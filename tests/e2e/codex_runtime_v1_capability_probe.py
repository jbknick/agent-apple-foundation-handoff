#!/usr/bin/env python3

import argparse
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
import os
from pathlib import Path
import re
import selectors
import shutil
import stat
import subprocess
import sys
import tempfile
import threading
import time
from typing import Any, Iterator, Mapping


ROOT = Path(__file__).resolve().parents[2]
DEV246_PATH = ROOT / "tests/e2e/codex_result_replacement_probe.py"
MARKETPLACE_NAME = "runtime-v1-capability"
PLUGIN_NAME = "runtime-v1-capability-probe"
PLUGIN_ID = f"{PLUGIN_NAME}@{MARKETPLACE_NAME}"
VERSION_LINE = b"codex-cli 0.145.0\n"
APPROVED_COMMAND = "python3 -m unittest -q diagnostic_fixture"
ROW_KEYS = (
    "id",
    "status",
    "reason",
    "bridgeKind",
    "commandExecutions",
    "hookInvocations",
    "appleAttempts",
    "appleValidResults",
    "providerRequests",
    "additionalParentModelTurns",
    "originalSha256",
    "hookInputSha256",
    "replacementSha256",
    "nextRequestOutputSha256",
    "originalAbsentFromNextRequest",
    "replacementPresentInNextRequest",
    "originalPreserved",
    "replacementBytes",
    "spooled",
    "cleanupStatus",
)


class ProbeBlocked(Exception):
    pass


class ProbeFailure(Exception):
    pass


def _load_dev246():
    spec = importlib.util.spec_from_file_location(
        "runtime_v1_dev246_helpers",
        DEV246_PATH,
    )
    if spec is None or spec.loader is None:
        raise ProbeBlocked("historical_helpers_unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_dev246 = _load_dev246()
tree_sha256 = _dev246._tree_sha256
atomic_write_json = _dev246._atomic_write_json


def executable_snapshot(metadata: os.stat_result) -> tuple[int, ...]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        stat.S_IFMT(metadata.st_mode),
        stat.S_IMODE(metadata.st_mode),
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def _version(executable: Path) -> bytes:
    try:
        completed = subprocess.run(
            [str(executable), "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            shell=False,
            timeout=30,
            env={"PATH": os.environ.get("PATH", "")},
        )
    except (OSError, subprocess.TimeoutExpired):
        return b""
    if completed.returncode != 0 or completed.stderr:
        return b""
    return completed.stdout


@dataclass(frozen=True)
class CapturedExecutable:
    locator: Path
    resolved: Path
    snapshot: tuple[int, ...]
    version: str

    def recheck(self) -> None:
        try:
            resolved = self.locator.resolve(strict=True)
            metadata = resolved.stat()
        except OSError:
            raise ProbeFailure(
                "host_resolution_or_version_drift"
            ) from None
        if (
            resolved != self.resolved
            or executable_snapshot(metadata) != self.snapshot
            or not stat.S_ISREG(metadata.st_mode)
            or not os.access(self.locator, os.X_OK)
            or _version(self.resolved) != VERSION_LINE
        ):
            raise ProbeFailure("host_resolution_or_version_drift")


def capture_codex(path: Path) -> CapturedExecutable:
    try:
        resolved = path.resolve(strict=True)
        metadata = resolved.stat()
    except OSError:
        raise ProbeBlocked(
            "missing_binary_or_version_mismatch"
        ) from None
    if (
        not stat.S_ISREG(metadata.st_mode)
        or not os.access(path, os.X_OK)
        or _version(resolved) != VERSION_LINE
    ):
        raise ProbeBlocked("missing_binary_or_version_mismatch")
    captured = CapturedExecutable(
        locator=path,
        resolved=resolved,
        snapshot=executable_snapshot(metadata),
        version="0.145.0",
    )
    captured.recheck()
    return captured


def _hook_from_list(
    value: Mapping[str, Any],
    *,
    cwd: Path,
    plugin_id: str,
) -> dict[str, Any]:
    if type(value) is not dict or set(value) != {"data"}:
        raise ProbeBlocked("hook_trust_unavailable")
    rows = value["data"]
    if type(rows) is not list or len(rows) != 1:
        raise ProbeBlocked("hook_trust_unavailable")
    row = rows[0]
    if (
        type(row) is not dict
        or row.get("cwd") != str(cwd)
        or row.get("warnings") != []
        or row.get("errors") != []
    ):
        raise ProbeBlocked("hook_trust_unavailable")
    hooks = row.get("hooks")
    if type(hooks) is not list or len(hooks) != 1:
        raise ProbeBlocked("hook_trust_unavailable")
    hook = hooks[0]
    if (
        type(hook) is not dict
        or hook.get("matcher") != "Bash"
        or hook.get("handlerType") != "command"
        or hook.get("source") != "plugin"
        or hook.get("pluginId") != plugin_id
        or hook.get("enabled") is not True
        or hook.get("isManaged") is not False
        or type(hook.get("key")) is not str
        or not hook["key"]
        or type(hook.get("currentHash")) is not str
        or not hook["currentHash"]
    ):
        raise ProbeBlocked("hook_trust_unavailable")
    return hook


def trust_hook(
    rpc,
    *,
    cwd: Path,
    plugin_id: str,
    approved_hash: str,
) -> bool:
    first = _hook_from_list(
        rpc.call("hooks/list", {"cwds": [str(cwd)]}),
        cwd=cwd,
        plugin_id=plugin_id,
    )
    if first["currentHash"] != approved_hash:
        raise ProbeBlocked("hook_trust_unavailable")
    rpc.call(
        "config/batchWrite",
        {
            "edits": [
                {
                    "keyPath": "hooks.state",
                    "value": {
                        first["key"]: {
                            "trusted_hash": first["currentHash"],
                        }
                    },
                    "mergeStrategy": "upsert",
                }
            ],
            "reloadUserConfig": True,
        },
    )
    second = _hook_from_list(
        rpc.call("hooks/list", {"cwds": [str(cwd)]}),
        cwd=cwd,
        plugin_id=plugin_id,
    )
    if (
        second["key"] != first["key"]
        or second["currentHash"] != first["currentHash"]
        or second.get("trustStatus") != "trusted"
    ):
        raise ProbeBlocked("hook_trust_unavailable")
    return True


def classify_row(
    *,
    row_id: str,
    bridge_kind: str,
    stimulus: bytes,
    approved_stimulus_sha256: str,
    hook_input_sha256: str | None,
    replacement_sha256: str | None,
    next_output: bytes,
    baseline_provider_requests: int,
    provider_requests: int,
    command_executions: int,
    hook_invocations: int,
    apple_attempts: int,
    apple_valid_results: int = 0,
    cleanup_status: str = "complete",
) -> dict[str, object]:
    if (
        not stimulus
        or not re.fullmatch(
            r"[0-9a-f]{64}",
            approved_stimulus_sha256,
        )
    ):
        raise ProbeFailure("stimulus_grant_invalid")
    original_sha256 = hashlib.sha256(stimulus).hexdigest()
    expected_grant_match = row_id != "decline_unapproved_stimulus"
    grant_matches = original_sha256 == approved_stimulus_sha256
    expected_hook_invocations = (
        0 if row_id == "plugin_off_baseline" else 1
    )
    hook_input_matches = (
        hook_input_sha256 is None
        if expected_hook_invocations == 0
        else hook_input_sha256 == original_sha256
    )
    next_sha256 = hashlib.sha256(next_output).hexdigest()
    added_turns = max(
        provider_requests - baseline_provider_requests,
        0,
    )
    if replacement_sha256 is not None:
        original_absent = (
            stimulus not in next_output
            and b"RUNTIME_V1_ORIGINAL_SENTINEL" not in next_output
        )
        replacement_present = next_sha256 == replacement_sha256
        original_preserved = False
        replacement_bytes = len(next_output)
        spooled = not replacement_present
        core_passed = (
            command_executions == 1
            and hook_invocations == expected_hook_invocations == 1
            and hook_input_matches
            and grant_matches is True
            and provider_requests == baseline_provider_requests == 2
            and added_turns == 0
            and original_absent is True
            and replacement_present is True
            and replacement_bytes <= 4096
            and spooled is False
        )
        if not core_passed:
            status, reason = "fail", "replacement_invariant_failed"
        elif cleanup_status != "complete":
            status, reason = "blocked", "cleanup_incomplete"
        else:
            status, reason = "pass", "replacement_observed"
    else:
        original_absent = False
        replacement_present = False
        envelope = re.fullmatch(
            rb"Exit code: 0\n"
            rb"Wall time: (?:0|[1-9][0-9]*)(?:\.[0-9]+)? seconds\n"
            rb"Output:\n"
            + re.escape(stimulus),
            next_output,
        )
        original_preserved = envelope is not None
        replacement_bytes = 0
        spooled = False
        core_passed = (
            command_executions == 1
            and hook_invocations == expected_hook_invocations
            and hook_input_matches
            and grant_matches is expected_grant_match
            and provider_requests == baseline_provider_requests == 2
            and added_turns == 0
            and original_preserved
        )
        if not core_passed:
            status, reason = "fail", "untouched_original_invariant_failed"
        elif cleanup_status != "complete":
            status, reason = "blocked", "cleanup_incomplete"
        else:
            status, reason = "pass", "untouched_original_observed"
    values = {
        "id": row_id,
        "status": status,
        "reason": reason,
        "bridgeKind": bridge_kind,
        "commandExecutions": command_executions,
        "hookInvocations": hook_invocations,
        "appleAttempts": apple_attempts,
        "appleValidResults": apple_valid_results,
        "providerRequests": provider_requests,
        "additionalParentModelTurns": added_turns,
        "originalSha256": original_sha256,
        "hookInputSha256": hook_input_sha256,
        "replacementSha256": replacement_sha256,
        "nextRequestOutputSha256": next_sha256,
        "originalAbsentFromNextRequest": original_absent,
        "replacementPresentInNextRequest": replacement_present,
        "originalPreserved": original_preserved,
        "replacementBytes": replacement_bytes,
        "spooled": spooled,
        "cleanupStatus": cleanup_status,
    }
    return {key: values[key] for key in ROW_KEYS}


def sse(events: list[dict[str, object]]) -> bytes:
    return "".join(
        f"event: {event['type']}\n"
        f"data: {json.dumps(event, separators=(',', ':'))}\n\n"
        for event in events
    ).encode("utf-8")


def _completed(response_id: str) -> dict[str, object]:
    return {
        "type": "response.completed",
        "response": {
            "id": response_id,
            "usage": {
                "input_tokens": 0,
                "input_tokens_details": None,
                "output_tokens": 0,
                "output_tokens_details": None,
                "total_tokens": 0,
            },
        },
    }


def _provider_events(index: int) -> list[dict[str, object]]:
    response_id = f"resp-{index}"
    created = {
        "type": "response.created",
        "response": {"id": response_id},
    }
    if index == 1:
        item = {
            "type": "response.output_item.done",
            "item": {
                "type": "function_call",
                "call_id": "call-runtime-v1",
                "name": "shell_command",
                "arguments": json.dumps(
                    {
                        "command": APPROVED_COMMAND,
                        "timeout_ms": 30_000,
                    },
                    separators=(",", ":"),
                ),
            },
        }
    else:
        item = {
            "type": "response.output_item.done",
            "item": {
                "id": "message-2",
                "type": "message",
                "role": "assistant",
                "content": [
                    {
                        "type": "output_text",
                        "text": "done",
                        "annotations": [],
                    }
                ],
            },
        }
    return [created, item, _completed(response_id)]


class _ResponsesServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self):
        self.requests: list[dict[str, object]] = []
        super().__init__(("127.0.0.1", 0), _ResponsesHandler)


class _ResponsesHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_POST(self):
        server = self.server
        if self.path != "/v1/responses" or not isinstance(
            server,
            _ResponsesServer,
        ):
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", ""))
            body = self.rfile.read(length)
            value = json.loads(body)
        except (ValueError, json.JSONDecodeError):
            self.send_error(400)
            return
        if type(value) is not dict or len(server.requests) >= 2:
            self.send_error(409)
            return
        server.requests.append(value)
        encoded = sse(_provider_events(len(server.requests)))
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, _format, *_arguments):
        return


@contextmanager
def responses_server() -> Iterator[_ResponsesServer]:
    server = _ResponsesServer()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


class JsonRpcProcess:
    def __init__(
        self,
        executable: Path,
        environment: Mapping[str, str],
    ):
        try:
            self.process = subprocess.Popen(
                [
                    str(executable),
                    "app-server",
                    "--stdio",
                    "--enable",
                    "hooks",
                ],
                env=dict(environment),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
            )
        except OSError:
            raise ProbeFailure("app_server_start_failed") from None
        if (
            self.process.stdin is None
            or self.process.stdout is None
            or self.process.stderr is None
        ):
            raise ProbeFailure("app_server_start_failed")
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.process.stdout, selectors.EVENT_READ)
        self.selector.register(self.process.stderr, selectors.EVENT_READ)
        self.next_id = 1
        self.seen_ids: set[int] = set()
        self.buffer = bytearray()
        self.call(
            "initialize",
            {
                "clientInfo": {
                    "name": "runtime_v1_capability_probe",
                    "title": "Runtime V1 Capability Probe",
                    "version": "0.0.1",
                }
            },
        )
        self.notify("initialized", {})

    def _write(self, value: Mapping[str, object]) -> None:
        encoded = (
            json.dumps(value, separators=(",", ":")) + "\n"
        ).encode("utf-8")
        try:
            self.process.stdin.write(encoded)
            self.process.stdin.flush()
        except (BrokenPipeError, OSError):
            raise ProbeFailure("app_server_write_failed") from None

    def notify(self, method: str, params: Mapping[str, object]) -> None:
        self._write({"method": method, "params": dict(params)})

    def call(
        self,
        method: str,
        params: Mapping[str, object],
    ) -> dict[str, object]:
        request_id = self.next_id
        self.next_id += 1
        self._write(
            {
                "id": request_id,
                "method": method,
                "params": dict(params),
            }
        )
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                raise ProbeFailure("app_server_early_exit")
            for key, _ in self.selector.select(
                max(0.0, deadline - time.monotonic())
            ):
                chunk = os.read(key.fileobj.fileno(), 65536)
                if key.fileobj is self.process.stderr:
                    if chunk:
                        raise ProbeFailure("app_server_stderr")
                    continue
                if not chunk:
                    raise ProbeFailure("app_server_early_exit")
                self.buffer.extend(chunk)
                while b"\n" in self.buffer:
                    raw, _, remainder = self.buffer.partition(b"\n")
                    self.buffer = bytearray(remainder)
                    try:
                        value = json.loads(raw)
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        raise ProbeFailure("app_server_json_invalid") from None
                    if type(value) is not dict or "id" not in value:
                        continue
                    response_id = value["id"]
                    if (
                        type(response_id) is not int
                        or response_id in self.seen_ids
                        or response_id != request_id
                    ):
                        raise ProbeFailure(
                            "app_server_response_id_invalid"
                        )
                    self.seen_ids.add(response_id)
                    if "error" in value or set(value) != {
                        "id",
                        "result",
                    }:
                        raise ProbeFailure("app_server_request_failed")
                    result = value["result"]
                    if type(result) is not dict:
                        raise ProbeFailure("app_server_result_invalid")
                    return result
        raise ProbeFailure("app_server_timeout")

    def close(self) -> None:
        self.selector.close()
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)
        stderr = self.process.stderr.read()
        if stderr:
            raise ProbeFailure("app_server_stderr")

    def __enter__(self):
        return self

    def __exit__(self, _type, _value, _traceback):
        self.close()


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


def materialize_marketplace(plugin: Path, marketplace: Path) -> Path:
    destination = marketplace / "plugins" / PLUGIN_NAME
    destination.parent.mkdir(parents=True)
    try:
        shutil.copytree(plugin, destination, symlinks=False)
    except OSError:
        raise ProbeFailure(
            "marketplace_materialization_failed"
        ) from None
    _write_json(
        marketplace / ".claude-plugin/marketplace.json",
        {
            "name": MARKETPLACE_NAME,
            "owner": {"name": "Runtime V1 capability probe"},
            "plugins": [
                {
                    "description": (
                        "Repository-only Runtime V1 capability probe."
                    ),
                    "name": PLUGIN_NAME,
                    "source": f"./plugins/{PLUGIN_NAME}",
                    "version": "0.0.1",
                }
            ],
        },
    )
    _write_json(
        marketplace / "metadata/codex-marketplace.json",
        {
            "interface": {
                "displayName": "Runtime V1 capability marketplace"
            },
            "name": MARKETPLACE_NAME,
            "plugins": [
                {
                    "category": "Developer Tools",
                    "name": PLUGIN_NAME,
                    "policy": {
                        "authentication": "ON_INSTALL",
                        "installation": "AVAILABLE",
                    },
                    "source": {
                        "path": f"./plugins/{PLUGIN_NAME}",
                        "source": "local",
                    },
                }
            ],
        },
    )
    return destination


def run_json(
    executable: Path,
    arguments: list[str],
    environment: Mapping[str, str],
) -> dict[str, object]:
    try:
        completed = subprocess.run(
            [str(executable), *arguments],
            env=dict(environment),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            shell=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        raise ProbeFailure("plugin_command_failed") from None
    if completed.returncode != 0 or completed.stderr:
        raise ProbeFailure("plugin_command_failed")
    try:
        value = json.loads(completed.stdout)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ProbeFailure("plugin_command_failed") from None
    if type(value) is not dict:
        raise ProbeFailure("plugin_command_failed")
    return value


def install_plugin(
    codex: CapturedExecutable,
    plugin: Path,
    temporary_root: Path,
    python: Path,
) -> tuple[dict[str, str], Path]:
    codex_home = temporary_root / "codex-home"
    marketplace = temporary_root / "marketplace"
    codex_home.mkdir()
    destination = materialize_marketplace(plugin, marketplace)
    if tree_sha256(destination) != tree_sha256(plugin):
        raise ProbeFailure("synthetic_plugin_drift")
    environment = {
        "CODEX_HOME": str(codex_home),
        "PATH": os.environ.get("PATH", ""),
        "RUNTIME_V1_PYTHON": str(python),
    }
    codex.recheck()
    run_json(
        codex.resolved,
        [
            "plugin",
            "marketplace",
            "add",
            str(marketplace),
            "--json",
        ],
        environment,
    )
    run_json(
        codex.resolved,
        ["plugin", "add", PLUGIN_ID, "--json"],
        environment,
    )
    codex.recheck()
    return environment, destination


def build_exec_arguments(
    server_url: str,
    workspace: Path,
) -> list[str]:
    provider = (
        "model_providers.runtime-v1-local={"
        'name="runtime-v1-local",'
        f'base_url="{server_url}/v1",'
        'env_key="RUNTIME_V1_LOCAL_PROVIDER_KEY",'
        'wire_api="responses",requires_openai_auth=false,'
        "supports_websockets=false}"
    )
    return [
        "exec",
        "--ephemeral",
        "--json",
        "--strict-config",
        "--skip-git-repo-check",
        "--enable",
        "hooks",
        "--disable",
        "code_mode",
        "--disable",
        "code_mode_only",
        "-c",
        provider,
        "-c",
        'model_provider="runtime-v1-local"',
        "-c",
        'approval_policy="never"',
        "-m",
        "gpt-5.1-codex",
        "-s",
        "danger-full-access",
        "-C",
        str(workspace),
        "Run the one approved synthetic unittest command exactly once.",
    ]


def _function_output(request: Mapping[str, Any]) -> bytes:
    items = request.get("input")
    if type(items) is not list:
        raise ProbeFailure("provider_request_invalid")
    matching = [
        item
        for item in items
        if type(item) is dict
        and item.get("type") == "function_call_output"
        and item.get("call_id") == "call-runtime-v1"
    ]
    if len(matching) != 1 or type(matching[0].get("output")) is not str:
        raise ProbeFailure("provider_request_invalid")
    return matching[0]["output"].encode("utf-8")


def _require_direct_shell(request: Mapping[str, Any]) -> None:
    tools = request.get("tools")
    if type(tools) is not list:
        raise ProbeFailure("direct_tool_mode_unavailable")
    names = {
        tool.get("name")
        for tool in tools
        if type(tool) is dict and type(tool.get("name")) is str
    }
    if "shell_command" not in names or any(
        name in names for name in ("exec", "write_stdin")
    ):
        raise ProbeFailure("direct_tool_mode_unavailable")


def stimulus_bytes() -> bytes:
    diagnostic = (
        "RUNTIME_V1_ORIGINAL_SENTINEL\n"
        "suite=synthetic unittest\n"
        "command-class=test\n"
        "outcome=success\n"
        "exit-status=0\n"
        "warning-count=0\n"
        "command-finished=true\n"
        "task-complete=true\n"
        "next-action=continue after successful synthetic unittest\n"
        "filler="
        + ("a" * 8200)
        + "\n"
    )
    return (
        diagnostic
        + "----------------------------------------------------------------------\n"
        + "Ran 1 test in 0.000s\n\n"
        + "OK\n"
    ).encode("utf-8")


def materialize_workspace(workspace: Path) -> None:
    source = """\
from pathlib import Path
import os
import sys
import unittest

counter = Path(os.environ["RUNTIME_V1_COMMAND_COUNTER"])
previous = int(counter.read_text() or "0") if counter.exists() else 0
counter.write_text(str(previous + 1))

unittest.runner.time.perf_counter = lambda: 0.0

DIAGNOSTIC = (
    "RUNTIME_V1_ORIGINAL_SENTINEL\\n"
    "suite=synthetic unittest\\n"
    "command-class=test\\n"
    "outcome=success\\n"
    "exit-status=0\\n"
    "warning-count=0\\n"
    "command-finished=true\\n"
    "task-complete=true\\n"
    "next-action=continue after successful synthetic unittest\\n"
    "filler="
    + ("a" * 8200)
    + "\\n"
)

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


def run_row(
    *,
    codex: CapturedExecutable,
    python: Path,
    plugin: Path,
    approved_plugin_sha256: str,
    approved_hook_hash: str,
    approved_stimulus_sha256: str,
    bridge_executable: Path,
    phase: str,
    baseline_provider_requests: int,
) -> dict[str, object]:
    if tree_sha256(plugin) != approved_plugin_sha256:
        raise ProbeFailure("synthetic_plugin_drift")
    with tempfile.TemporaryDirectory() as directory:
        temporary_root = Path(directory).resolve(strict=True)
        workspace = temporary_root / "workspace"
        materialize_workspace(workspace)
        counter = temporary_root / "command-counter"
        observations = temporary_root / "observations.jsonl"
        environment, _ = install_plugin(
            codex,
            plugin,
            temporary_root,
            python,
        )
        with JsonRpcProcess(codex.resolved, environment) as rpc:
            trust_hook(
                rpc,
                cwd=workspace,
                plugin_id=PLUGIN_ID,
                approved_hash=approved_hook_hash,
            )
        environment.update(
            {
                "NO_COLOR": "1",
                "PYTHON_COLORS": "0",
                "RUNTIME_V1_APPROVED_STIMULUS_SHA256": (
                    approved_stimulus_sha256
                ),
                "RUNTIME_V1_APPROVED_WORKSPACE": str(workspace),
                "RUNTIME_V1_BRIDGE_EXECUTABLE": str(bridge_executable),
                "RUNTIME_V1_COMMAND_COUNTER": str(counter),
                "RUNTIME_V1_LOCAL_PROVIDER_KEY": "local-probe",
                "RUNTIME_V1_OBSERVATION_PATH": str(observations),
                "RUNTIME_V1_REPO_ROOT": str(ROOT),
            }
        )
        with responses_server() as server:
            host, port = server.server_address
            completed = subprocess.run(
                [
                    str(codex.resolved),
                    *build_exec_arguments(
                        f"http://{host}:{port}",
                        workspace,
                    ),
                ],
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                shell=False,
                timeout=90,
            )
        codex.recheck()
        if (
            completed.returncode != 0
            or completed.stderr
            or len(server.requests) != 2
        ):
            raise ProbeFailure("installed_row_failed")
        _require_direct_shell(server.requests[0])
        next_output = _function_output(server.requests[1])
        if not counter.is_file() or counter.read_text() != "1":
            command_executions = -1
        else:
            command_executions = 1
        rows = []
        if observations.is_file():
            for line in observations.read_text(encoding="utf-8").splitlines():
                value = json.loads(line)
                if type(value) is not dict:
                    raise ProbeFailure("observation_invalid")
                rows.append(value)
        original = stimulus_bytes()
        original_sha = hashlib.sha256(original).hexdigest()
        hook_rows = [
            row for row in rows if row.get("event") == "original_observed"
        ]
        replacement_rows = [
            row for row in rows if row.get("event") == "replacement_emitted"
        ]
        consultation_rows = [
            row
            for row in rows
            if row.get("event") == "consultation_completed"
        ]
        return classify_row(
            row_id=phase,
            bridge_kind=bridge_executable.name,
            stimulus=original,
            approved_stimulus_sha256=approved_stimulus_sha256,
            hook_input_sha256=(
                hook_rows[0].get("originalSha256")
                if len(hook_rows) == 1
                else None
            ),
            replacement_sha256=(
                replacement_rows[0].get("replacementSha256")
                if len(replacement_rows) == 1
                else None
            ),
            next_output=next_output,
            baseline_provider_requests=baseline_provider_requests,
            provider_requests=len(server.requests),
            command_executions=command_executions,
            hook_invocations=len(
                [
                    row
                    for row in rows
                    if row.get("event") == "hook_invoked"
                ]
            ),
            apple_attempts=sum(
                row.get("appleAttempts", 0)
                for row in consultation_rows
            ),
            apple_valid_results=sum(
                row.get("appleValidResults", 0)
                for row in consultation_rows
            ),
        )


def _parse_arguments(arguments=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--codex-executable", type=Path, required=True)
    parser.add_argument("--python-executable", type=Path, required=True)
    parser.add_argument("--plugin", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(arguments)


def main(arguments=None) -> int:
    _parse_arguments(arguments)
    raise ProbeBlocked("live_mode_not_selected")


if __name__ == "__main__":
    raise SystemExit(main())
