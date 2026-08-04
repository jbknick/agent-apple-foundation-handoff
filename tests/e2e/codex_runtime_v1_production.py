#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from typing import Mapping


ROOT = Path(__file__).resolve().parents[2]
PLUGIN = ROOT / "plugins/apple-foundation-models-handoff"
CAPABILITY_PROBE = ROOT / "tests/e2e/codex_runtime_v1_capability_probe.py"
MARKETPLACE_NAME = "agent-apple-foundation-handoff"
PLUGIN_NAME = "apple-foundation-models-handoff"
PLUGIN_ID = f"{PLUGIN_NAME}@{MARKETPLACE_NAME}"
VERSION = "0.1.0"
COMMAND = "python3 -m unittest -q diagnostic_fixture"
SENTINEL = "RUNTIME_V1_PRODUCTION_ORIGINAL_SENTINEL"
ADAPTER = PLUGIN / "hooks/codex/diagnostic_condensation.py"
CONTRACT = PLUGIN / "runtime/runtime_contract.py"
APPROVED_DIGEST = re.compile(r"^[0-9a-f]{64}$")
APPROVED_HOOK_HASH = re.compile(r"^sha256:[0-9a-f]{64}$")


def _load_helpers():
    spec = importlib.util.spec_from_file_location(
        "runtime_v1_production_proved_helpers",
        CAPABILITY_PROBE,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("proved_helpers_unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


helpers = _load_helpers()
ProbeBlocked = helpers.ProbeBlocked
ProbeFailure = helpers.ProbeFailure
JsonRpcProcess = helpers.JsonRpcProcess
atomic_write_json = helpers.atomic_write_json
build_exec_arguments = helpers.build_exec_arguments
capture_codex = helpers.capture_codex
capture_python = helpers.capture_python
function_output = helpers._function_output
preserves_untouched_original = helpers.preserves_untouched_original
require_direct_exec_requests = helpers.require_direct_exec_requests
responses_server = helpers.responses_server
run_json = helpers.run_json
tree_sha256 = helpers.tree_sha256
trust_hook = helpers.trust_hook
capture_runnable = helpers._capture_runnable
recheck_runnable = helpers._recheck_runnable


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ProbeFailure("runtime_module_unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


adapter = _load_module(ADAPTER, "runtime_v1_production_probe_adapter")
contract = _load_module(CONTRACT, "runtime_v1_production_probe_contract")


class VerifiedTerminal(Exception):
    def __init__(self, status: str, reason: str, cleanup_status: str):
        self.status = status
        self.reason = reason
        self.cleanup_status = cleanup_status
        super().__init__(reason)


def capture_sdk() -> tuple[Path, Path, tuple[int, ...]]:
    locator_value = shutil.which("xcrun")
    if locator_value is None:
        raise ProbeBlocked("sdk_26_5_unavailable")
    locator = Path(locator_value)
    resolved, snapshot = capture_runnable(locator)
    recheck_sdk(locator, resolved, snapshot)
    return locator, resolved, snapshot


def recheck_sdk(
    locator: Path,
    resolved: Path,
    snapshot: tuple[int, ...],
) -> None:
    recheck_runnable(locator, resolved, snapshot)
    try:
        completed = subprocess.run(
            [str(resolved), "--sdk", "macosx", "--show-sdk-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            shell=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        raise ProbeBlocked("sdk_26_5_unavailable") from None
    if (
        completed.returncode != 0
        or completed.stderr
        or completed.stdout != b"26.5\n"
    ):
        raise ProbeBlocked("sdk_26_5_unavailable")


def _record(classification: str) -> str:
    if classification not in {"C0", "C2"}:
        raise ProbeFailure("classification_invalid")
    prefix = (
        f"{SENTINEL}\n"
        "case-id: production-installed-01\n"
        "command-class: test\n"
        "command-form: python3 -m unittest\n"
        f"classification: {classification}\n"
        "exit-status: 0\n"
        "interrupted: false\n"
        "warning-count: 0\n"
        "command-outcome: success\n"
        "summary: installed synthetic unittest success\n"
        "summary-facts: command-class=test|"
        "command-form=python3 -m unittest|outcome=success|"
        "error-count=0|warning-count=0\n"
        "next-action: continue after installed synthetic unittest\n"
        "completion-facts: command-finished=true|task-complete=true\n"
    )
    return prefix + "synthetic-noise|" + ("a" * 7600) + "\n"


def stimulus_bytes(classification: str) -> bytes:
    return (
        _record(classification)
        + "----------------------------------------------------------------------\n"
        + "Ran 1 test in 0.000s\n\n"
        + "OK\n"
    ).encode("utf-8")


def materialize_workspace(
    workspace: Path,
    *,
    classification: str,
) -> None:
    source = f"""\
from pathlib import Path
import os
import sys
import unittest

sys.stderr = sys.stdout
counter = Path(os.environ["DEV254_PROBE_COMMAND_COUNTER"])
previous = int(counter.read_text() or "0") if counter.exists() else 0
counter.write_text(str(previous + 1))
unittest.runner.time.perf_counter = lambda: 0.0
DIAGNOSTIC = {_record(classification)!r}

class DiagnosticFixture(unittest.TestCase):
    def test_large_safe_output(self):
        sys.stdout.write(DIAGNOSTIC)
        sys.stdout.flush()
"""
    workspace.mkdir()
    (workspace / "diagnostic_fixture.py").write_text(
        source,
        encoding="utf-8",
        newline="\n",
    )


def compile_bridge(
    staged_plugin: Path,
    *,
    xcrun: Path,
) -> Path:
    source = staged_plugin / "runtime/DiagnosticCondenser.swift"
    executable = staged_plugin / "runtime/diagnostic-condenser"
    try:
        completed = subprocess.run(
            [
                str(xcrun),
                "--sdk",
                "macosx",
                "swiftc",
                "-parse-as-library",
                str(source),
                "-o",
                str(executable),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            shell=False,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired):
        raise ProbeBlocked("sdk_26_5_unavailable") from None
    if completed.returncode != 0 or completed.stdout or completed.stderr:
        raise ProbeBlocked("sdk_26_5_unavailable")
    executable.chmod(
        stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR
    )
    return executable


def materialize_marketplace(
    staged_plugin: Path,
    marketplace: Path,
) -> Path:
    destination = marketplace / "plugins" / PLUGIN_NAME
    destination.parent.mkdir(parents=True)
    shutil.copytree(staged_plugin, destination, symlinks=False)
    for relative in (
        Path(".claude-plugin/marketplace.json"),
        Path("metadata/codex-marketplace.json"),
    ):
        target = marketplace / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    if tree_sha256(destination) != tree_sha256(staged_plugin):
        raise ProbeFailure("staged_plugin_drift")
    return destination


def install_plugin(
    codex,
    staged_plugin: Path,
    temporary_root: Path,
    python: Path,
) -> tuple[dict[str, str], Path]:
    codex_home = temporary_root / "codex-home"
    marketplace = temporary_root / "marketplace"
    codex_home.mkdir()
    materialize_marketplace(staged_plugin, marketplace)
    environment = {
        "CODEX_HOME": str(codex_home),
        "PATH": os.environ.get("PATH", ""),
        "PYTHONDONTWRITEBYTECODE": "1",
        "RUNTIME_V1_PYTHON": str(python),
    }
    codex.recheck()
    run_json(
        codex.resolved,
        ["plugin", "marketplace", "add", str(marketplace), "--json"],
        environment,
    )
    run_json(
        codex.resolved,
        ["plugin", "add", PLUGIN_ID, "--json"],
        environment,
    )
    codex.recheck()
    installed = (
        codex_home
        / "plugins/cache"
        / MARKETPLACE_NAME
        / PLUGIN_NAME
        / VERSION
    )
    if not installed.is_dir():
        raise ProbeFailure("installed_plugin_unavailable")
    return environment, installed


def _hook_identity(
    rpc,
    *,
    workspace: Path,
) -> str:
    value = rpc.call("hooks/list", {"cwds": [str(workspace)]})
    rows = value.get("data")
    if type(rows) is not list or len(rows) != 1:
        raise ProbeBlocked("hook_trust_unavailable")
    hooks = rows[0].get("hooks")
    if type(hooks) is not list or len(hooks) != 1:
        raise ProbeBlocked("hook_trust_unavailable")
    hook = hooks[0]
    current_hash = hook.get("currentHash")
    if (
        hook.get("pluginId") != PLUGIN_ID
        or hook.get("matcher") != "Bash"
        or type(current_hash) is not str
        or not current_hash.startswith("sha256:")
    ):
        raise ProbeBlocked("hook_trust_unavailable")
    return current_hash


def _exec_arguments(server_url: str, workspace: Path) -> list[str]:
    arguments = build_exec_arguments(server_url, workspace)
    return [
        argument.replace(
            'env_key="RUNTIME_V1_LOCAL_PROVIDER_KEY"',
            'env_key="DEV254_PROBE_PROVIDER_KEY"',
        )
        for argument in arguments
    ]


def _validated_applied_output(output: bytes, original: bytes) -> str:
    try:
        decoded = output.decode("utf-8")
        result = json.loads(
            decoded,
            object_pairs_hook=adapter._pairs_without_duplicates,
        )
        original_text = original.decode("utf-8")
    except (UnicodeError, ValueError, json.JSONDecodeError):
        raise ProbeFailure("replacement_result_invalid") from None
    try:
        contract._validate_condensation(result)
        expected_facts = adapter.source_facts(original_text)
    except (TypeError, ValueError, contract.ContractError):
        raise ProbeFailure("replacement_result_invalid") from None
    if result != expected_facts:
        raise ProbeFailure("replacement_semantics_invalid")
    canonical = json.dumps(
        result,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    if canonical != output:
        raise ProbeFailure("replacement_bytes_invalid")
    return hashlib.sha256(canonical).hexdigest()


def _run_row(
    *,
    codex,
    environment: Mapping[str, str],
    installed: Path,
    temporary_root: Path,
    classification: str,
) -> dict[str, object]:
    row_id = "installed_real_apple_applied" if classification == "C0" else (
        "installed_c2_fallback"
    )
    workspace = temporary_root / f"workspace-{classification.lower()}"
    materialize_workspace(workspace, classification=classification)
    counter = temporary_root / f"command-counter-{classification.lower()}"
    row_environment = dict(environment)
    row_environment.update(
        {
            "NO_COLOR": "1",
            "PYTHON_COLORS": "0",
            "RUNTIME_V1_BRIDGE_EXECUTABLE": str(
                installed / "runtime/diagnostic-condenser"
            ),
            "DEV254_PROBE_COMMAND_COUNTER": str(counter),
            "DEV254_PROBE_PROVIDER_KEY": "local-production-probe",
            "RUNTIME_V1_REPO_ROOT": str(workspace),
        }
    )
    with responses_server() as server:
        host, port = server.server_address
        master_fd, slave_fd = os.openpty()
        try:
            completed = subprocess.run(
                [
                    str(codex.resolved),
                    *_exec_arguments(
                        f"http://{host}:{port}",
                        workspace,
                    ),
                ],
                env=row_environment,
                stdin=slave_fd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                shell=False,
                timeout=90,
            )
        finally:
            try:
                os.close(slave_fd)
            finally:
                os.close(master_fd)
    codex.recheck()
    if completed.returncode != 0 or completed.stderr:
        raise ProbeFailure("codex_process_failed")
    require_direct_exec_requests(server.requests)
    if len(server.requests) != 2:
        raise ProbeFailure("parent_request_count_invalid")
    if not counter.is_file() or counter.read_text() != "1":
        raise ProbeFailure("command_execution_count_invalid")
    output = function_output(server.requests[1])
    original = stimulus_bytes(classification)
    if classification == "C0":
        if original in output or SENTINEL.encode() in output:
            raise ProbeFailure("original_exclusion_invalid")
        replacement_sha256 = _validated_applied_output(output, original)
        return {
            "id": row_id,
            "status": "pass",
            "reason": None,
            "commandExecutions": 1,
            "appleAttempts": 1,
            "appleValidResults": 1,
            "providerRequests": 2,
            "additionalParentModelTurns": 0,
            "originalPreserved": False,
            "originalAbsentFromNextRequest": True,
            "replacementPresentInNextRequest": True,
            "replacementSha256": replacement_sha256,
        }
    if not preserves_untouched_original(output, original):
        raise ProbeFailure("untouched_original_invariant_failed")
    return {
        "id": row_id,
        "status": "pass",
        "reason": None,
        "commandExecutions": 1,
        "appleAttempts": 0,
        "appleValidResults": 0,
        "providerRequests": 2,
        "additionalParentModelTurns": 0,
        "originalPreserved": True,
        "originalAbsentFromNextRequest": False,
        "replacementPresentInNextRequest": False,
        "replacementSha256": None,
    }


def unsafe_evidence_findings(value: object) -> int:
    prohibited_keys = {
        "diagnosticText",
        "sourceFacts",
        "prompt",
        "response",
        "transcript",
        "toolInput",
        "toolOutput",
        "appleOutput",
    }
    private = re.compile(
        r"(?:/Users/|/home/|/private/|"
        r"\b(?:password|secret|credential|authorization)\s*[:=])",
        re.IGNORECASE,
    )
    findings = 0

    def visit(item: object) -> None:
        nonlocal findings
        if type(item) is dict:
            for key, child in item.items():
                if key in prohibited_keys:
                    findings += 1
                visit(key)
                visit(child)
        elif type(item) is list:
            for child in item:
                visit(child)
        elif type(item) is str and (
            SENTINEL in item or private.search(item) is not None
        ):
            findings += 1

    visit(value)
    return findings


def _finalize_evidence(value: dict[str, object]) -> dict[str, object]:
    findings = unsafe_evidence_findings(value)
    value["unsafeCommittedEvidenceFindings"] = findings
    if findings != 0:
        raise VerifiedTerminal("fail", "evidence_safety_failed", "complete")
    return value


def _execute_in_temporary(
    *,
    codex_executable: Path,
    python_executable: Path,
    approved_plugin_sha256: str | None,
    approved_hook_hash: str | None,
    inspect_only: bool,
    temporary_path: Path,
) -> dict[str, object]:
        codex = capture_codex(codex_executable)
        python = capture_python(python_executable)
        sdk_locator, sdk_resolved, sdk_snapshot = capture_sdk()
        staged = temporary_path / "staged-plugin"
        shutil.copytree(PLUGIN, staged, symlinks=False)
        compile_bridge(staged, xcrun=sdk_resolved)
        plugin_sha256 = tree_sha256(staged)
        if (
            not inspect_only
            and plugin_sha256 != approved_plugin_sha256
        ):
            raise ProbeBlocked("plugin_identity_unapproved")
        environment, installed = install_plugin(
            codex,
            staged,
            temporary_path,
            python.resolved,
        )
        if tree_sha256(installed) != plugin_sha256:
            raise ProbeFailure("installed_plugin_drift")
        trust_workspace = temporary_path / "trust-workspace"
        trust_workspace.mkdir()
        with JsonRpcProcess(codex.resolved, environment) as rpc:
            hook_hash = _hook_identity(rpc, workspace=trust_workspace)
            if not inspect_only:
                if hook_hash != approved_hook_hash:
                    raise ProbeBlocked("hook_identity_unapproved")
                trust_hook(
                    rpc,
                    cwd=trust_workspace,
                    plugin_id=PLUGIN_ID,
                    approved_hash=approved_hook_hash,
                )
        if inspect_only:
            codex.recheck()
            python.recheck()
            recheck_sdk(sdk_locator, sdk_resolved, sdk_snapshot)
            return {
                "schemaVersion": 1,
                "status": "inspection",
                "reason": None,
                "codexVersion": "0.145.0",
                "codexExecutable": "<host-path>",
                "sdkVersion": "26.5",
                "pluginSha256": plugin_sha256,
                "hookCurrentHash": hook_hash,
                "cleanupStatus": "pending",
            }
        rows = [
            _run_row(
                codex=codex,
                environment=environment,
                installed=installed,
                temporary_root=temporary_path,
                classification=classification,
            )
            for classification in ("C0", "C2")
        ]
        if tree_sha256(installed) != plugin_sha256:
            raise ProbeFailure("installed_plugin_drift")
        codex.recheck()
        python.recheck()
        recheck_sdk(sdk_locator, sdk_resolved, sdk_snapshot)
        return {
            "schemaVersion": 1,
            "status": "pass",
            "reason": None,
            "codexVersion": "0.145.0",
            "codexExecutable": "<host-path>",
            "sdkVersion": "26.5",
            "pluginSha256": plugin_sha256,
            "hookCurrentHash": hook_hash,
            "hookTrustStatus": "trusted",
            "hostInjectedPluginRoot": True,
            "explicitRuntimeVariables": [
                "RUNTIME_V1_PYTHON",
                "RUNTIME_V1_BRIDGE_EXECUTABLE",
                "RUNTIME_V1_REPO_ROOT",
            ],
            "probeOnlyVariables": [
                "DEV254_PROBE_COMMAND_COUNTER",
                "DEV254_PROBE_PROVIDER_KEY",
            ],
            "rows": rows,
            "cleanupStatus": "pending",
        }


def execute(
    *,
    codex_executable: Path,
    python_executable: Path,
    approved_plugin_sha256: str | None,
    approved_hook_hash: str | None,
    inspect_only: bool,
) -> dict[str, object]:
    temporary = tempfile.TemporaryDirectory()
    temporary_path = Path(temporary.name).resolve(strict=True)
    result: dict[str, object] | None = None
    terminal: tuple[str, str] | None = None
    try:
        result = _execute_in_temporary(
            codex_executable=codex_executable,
            python_executable=python_executable,
            approved_plugin_sha256=approved_plugin_sha256,
            approved_hook_hash=approved_hook_hash,
            inspect_only=inspect_only,
            temporary_path=temporary_path,
        )
    except ProbeBlocked as error:
        terminal = ("blocked", str(error))
    except (ProbeFailure, OSError, ValueError) as error:
        terminal = ("fail", str(error))
    cleanup_status = "complete"
    try:
        temporary.cleanup()
    except OSError:
        cleanup_status = "incomplete"
    if temporary_path.exists():
        cleanup_status = "incomplete"
    if cleanup_status != "complete":
        raise VerifiedTerminal("blocked", "cleanup_incomplete", cleanup_status)
    if terminal is not None:
        raise VerifiedTerminal(*terminal, cleanup_status)
    if result is None:
        raise VerifiedTerminal("fail", "result_unavailable", cleanup_status)
    result["cleanupStatus"] = cleanup_status
    return _finalize_evidence(result)


def _arguments(arguments=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--codex-executable", type=Path, required=True)
    parser.add_argument("--python-executable", type=Path, required=True)
    parser.add_argument("--inspect", action="store_true")
    parser.add_argument("--approved-plugin-sha256")
    parser.add_argument("--approved-hook-hash")
    parser.add_argument("--output", type=Path)
    options = parser.parse_args(arguments)
    if not options.inspect and (
        type(options.approved_plugin_sha256) is not str
        or APPROVED_DIGEST.fullmatch(options.approved_plugin_sha256) is None
        or type(options.approved_hook_hash) is not str
        or APPROVED_HOOK_HASH.fullmatch(options.approved_hook_hash) is None
    ):
        parser.error(
            "run mode requires exact approved plugin and hook hashes"
        )
    return options


def main(arguments=None) -> int:
    options = _arguments(arguments)
    try:
        result = execute(
            codex_executable=options.codex_executable,
            python_executable=options.python_executable,
            approved_plugin_sha256=options.approved_plugin_sha256,
            approved_hook_hash=options.approved_hook_hash,
            inspect_only=options.inspect,
        )
    except VerifiedTerminal as error:
        result = _finalize_evidence({
            "schemaVersion": 1,
            "status": error.status,
            "reason": error.reason,
            "codexVersion": None,
            "codexExecutable": "<host-path>",
            "cleanupStatus": error.cleanup_status,
        })
    if options.output is not None:
        atomic_write_json(options.output, result)
    print(json.dumps(result, separators=(",", ":"), sort_keys=True))
    return 0 if result["status"] in {"inspection", "pass"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
