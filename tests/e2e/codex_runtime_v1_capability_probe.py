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
REQUIRED_ROW_IDS = (
    "plugin_off_baseline",
    "direct_fake_applied",
    "composed_live_apple_applied",
    "decline_unapproved_stimulus",
    "bridge_malformed",
    "bridge_crash",
    "adapter_crash",
    "hook_timeout",
)
FALLBACK_ROW_IDS = REQUIRED_ROW_IDS[3:]
ALLOWED_BLOCKERS = {
    "missing_binary_or_version_mismatch",
    "sdk_26_5_unavailable",
    "apple_unavailable",
    "locale_unsupported",
    "hook_trust_unavailable",
    "cleanup_incomplete",
}
EVIDENCE_KEYS = (
    "schemaVersion",
    "gate",
    "status",
    "reason",
    "codexVersion",
    "codexExecutable",
    "sdkVersion",
    "swiftVersion",
    "pluginSha256",
    "hookCurrentHash",
    "hookTrustStatus",
    "approvedStimulusSha256",
    "contextClassification",
    "contextGrantStatus",
    "directToolMode",
    "codeModeEnabled",
    "rows",
    "unsafeCommittedEvidenceFindings",
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


def derive_gate_status(
    rows: list[dict[str, object]],
    *,
    approved_stimulus_sha256: str,
    blocker_reason: str | None,
    unsafe_findings: int,
    cleanup_status: str,
) -> tuple[str, str]:
    identities = [row["id"] for row in rows]
    if len(identities) != len(set(identities)):
        raise ProbeFailure("duplicate_row")
    by_id = {row["id"]: row for row in rows}
    if unsafe_findings != 0:
        return "fail", "evidence_safety_failed"
    if any(row["commandExecutions"] != 1 for row in rows):
        return "fail", "command_execution_invariant_failed"
    if any(row["additionalParentModelTurns"] != 0 for row in rows):
        return "fail", "parent_turn_invariant_failed"
    for row in rows:
        expected_hook_sha = (
            None
            if row["id"] == "plugin_off_baseline"
            else row["originalSha256"]
        )
        if row["hookInputSha256"] != expected_hook_sha:
            return "fail", "hook_input_invariant_failed"
        expected_grant_match = (
            row["id"] != "decline_unapproved_stimulus"
        )
        if (
            row["originalSha256"] == approved_stimulus_sha256
        ) is not expected_grant_match:
            return "fail", "context_grant_invariant_failed"
    for row_id in (
        "direct_fake_applied",
        "composed_live_apple_applied",
    ):
        row = by_id.get(row_id)
        if row is not None and (
            row["originalAbsentFromNextRequest"] is not True
            or row["replacementPresentInNextRequest"] is not True
            or row["spooled"] is not False
            or row["status"] == "fail"
        ):
            return "fail", "replacement_invariant_failed"
    composed = by_id.get("composed_live_apple_applied")
    if composed is not None and (
        composed["appleAttempts"] != 1
        or composed["appleValidResults"] != 1
    ):
        return "fail", "apple_attempt_invariant_failed"
    for row_id in FALLBACK_ROW_IDS:
        row = by_id.get(row_id)
        if row is not None and (
            row["originalPreserved"] is not True
            or row["replacementPresentInNextRequest"] is not False
            or row["status"] == "fail"
        ):
            return "fail", "untouched_original_invariant_failed"
    if cleanup_status != "complete":
        return "blocked", "cleanup_incomplete"
    if blocker_reason is not None:
        if blocker_reason not in ALLOWED_BLOCKERS:
            raise ProbeFailure("blocker_reason_invalid")
        return "blocked", blocker_reason
    if set(by_id) != set(REQUIRED_ROW_IDS):
        return "fail", "incomplete_gate"
    if any(row["status"] != "pass" for row in rows):
        return "fail", "row_failed"
    return "pass", "capability_proven"


def _digest(value: object, *, prefixed: bool = False) -> bool:
    pattern = (
        r"sha256:[0-9a-f]{64}" if prefixed else r"[0-9a-f]{64}"
    )
    return type(value) is str and re.fullmatch(pattern, value) is not None


def validate_evidence(value: Mapping[str, object]) -> dict[str, object]:
    if type(value) is not dict or set(value) != set(EVIDENCE_KEYS):
        raise ProbeFailure("evidence_shape_invalid")
    rows = value["rows"]
    if type(rows) is not list:
        raise ProbeFailure("evidence_shape_invalid")
    for row in rows:
        if type(row) is not dict or set(row) != set(ROW_KEYS):
            raise ProbeFailure("evidence_shape_invalid")
        if (
            not _digest(row["originalSha256"])
            or not _digest(row["nextRequestOutputSha256"])
            or (
                row["hookInputSha256"] is not None
                and not _digest(row["hookInputSha256"])
            )
            or (
                row["replacementSha256"] is not None
                and not _digest(row["replacementSha256"])
            )
        ):
            raise ProbeFailure("evidence_digest_invalid")
    if (
        value["schemaVersion"] != 1
        or value["gate"] != "runtime-v1-successor-capability"
        or value["status"] not in {"pass", "fail", "blocked"}
        or type(value["reason"]) is not str
        or value["codexVersion"] != "0.145.0"
        or value["codexExecutable"] != "<host-path>"
        or value["sdkVersion"] != "26.5"
        or value["swiftVersion"] != "6.3.3"
        or not _digest(value["pluginSha256"])
        or not _digest(value["hookCurrentHash"], prefixed=True)
        or value["hookTrustStatus"] != "trusted"
        or not _digest(value["approvedStimulusSha256"])
        or value["contextClassification"] != "C0"
        or value["contextGrantStatus"]
        != "approved_exact_synthetic_hash"
        or value["directToolMode"] is not True
        or value["codeModeEnabled"] is not False
        or type(value["unsafeCommittedEvidenceFindings"]) is not int
        or value["unsafeCommittedEvidenceFindings"] < 0
        or value["cleanupStatus"] not in {"complete", "incomplete"}
    ):
        raise ProbeFailure("evidence_value_invalid")
    encoded = json.dumps(value, ensure_ascii=True, sort_keys=True)
    if (
        "RUNTIME_V1_ORIGINAL_SENTINEL" in encoded
        or re.search(r"/(?:Users|home|private)/", encoded)
        or re.search(
            r"\b(?:Bearer|password|credential|api[_ -]?key)\b",
            encoded,
            re.IGNORECASE,
        )
    ):
        raise ProbeFailure("evidence_safety_failed")
    return dict(value)


def phases_for(through: str) -> tuple[str, ...]:
    counts = {"direct": 2, "composed": 3, "complete": 8}
    if through not in counts:
        raise ProbeFailure("gate_phase_invalid")
    return REQUIRED_ROW_IDS[: counts[through]]


def build_evidence(
    *,
    rows: list[dict[str, object]],
    approved_stimulus_sha256: str,
    plugin_sha256: str,
    hook_current_hash: str,
    blocker_reason: str | None,
    cleanup_status: str,
) -> dict[str, object]:
    status, reason = derive_gate_status(
        rows,
        approved_stimulus_sha256=approved_stimulus_sha256,
        blocker_reason=blocker_reason,
        unsafe_findings=0,
        cleanup_status=cleanup_status,
    )
    value = {
        "schemaVersion": 1,
        "gate": "runtime-v1-successor-capability",
        "status": status,
        "reason": reason,
        "codexVersion": "0.145.0",
        "codexExecutable": "<host-path>",
        "sdkVersion": "26.5",
        "swiftVersion": "6.3.3",
        "pluginSha256": plugin_sha256,
        "hookCurrentHash": hook_current_hash,
        "hookTrustStatus": "trusted",
        "approvedStimulusSha256": approved_stimulus_sha256,
        "contextClassification": "C0",
        "contextGrantStatus": "approved_exact_synthetic_hash",
        "directToolMode": True,
        "codeModeEnabled": False,
        "rows": rows,
        "unsafeCommittedEvidenceFindings": 0,
        "cleanupStatus": cleanup_status,
    }
    return validate_evidence(value)


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


def inspection_record(
    *,
    plugin_sha256: str,
    hook_current_hash: str,
    approved_stimulus_sha256: str,
    cleanup_status: str,
) -> dict[str, object]:
    if (
        not _digest(plugin_sha256)
        or not _digest(hook_current_hash, prefixed=True)
        or not _digest(approved_stimulus_sha256)
        or cleanup_status != "complete"
    ):
        raise ProbeFailure("inspection_value_invalid")
    return {
        "pluginSha256": plugin_sha256,
        "hookCurrentHash": hook_current_hash,
        "approvedStimulusSha256": approved_stimulus_sha256,
        "contextClassification": "C0",
        "contextGrantStatus": "approved_exact_synthetic_hash",
        "codexVersion": "0.145.0",
        "codexExecutable": "<host-path>",
        "cleanupStatus": cleanup_status,
    }


def _capture_runnable(path: Path) -> tuple[Path, tuple[int, ...]]:
    try:
        resolved = path.resolve(strict=True)
        metadata = resolved.stat()
    except OSError:
        raise ProbeBlocked("missing_binary_or_version_mismatch") from None
    if not stat.S_ISREG(metadata.st_mode) or not os.access(path, os.X_OK):
        raise ProbeBlocked("missing_binary_or_version_mismatch")
    return resolved, executable_snapshot(metadata)


def _recheck_runnable(
    path: Path,
    resolved: Path,
    snapshot: tuple[int, ...],
) -> None:
    try:
        current = path.resolve(strict=True)
        metadata = current.stat()
    except OSError:
        raise ProbeFailure(
            "host_resolution_or_version_drift"
        ) from None
    if (
        current != resolved
        or executable_snapshot(metadata) != snapshot
        or not stat.S_ISREG(metadata.st_mode)
        or not os.access(path, os.X_OK)
    ):
        raise ProbeFailure("host_resolution_or_version_drift")


def _timeout_variant(
    plugin: Path,
    destination: Path,
    timeout_seconds: int | None,
) -> Path:
    if timeout_seconds is None:
        return plugin
    if timeout_seconds != 1:
        raise ProbeFailure("hook_timeout_variant_invalid")
    try:
        shutil.copytree(plugin, destination, symlinks=False)
        hooks_path = destination / "hooks/codex/hooks.json"
        value = json.loads(hooks_path.read_text(encoding="utf-8"))
        handler = value["hooks"]["PostToolUse"][0]["hooks"][0]
        if handler["timeout"] != 60:
            raise ProbeFailure("hook_timeout_variant_invalid")
        handler["timeout"] = timeout_seconds
        _write_json(hooks_path, value)
    except ProbeFailure:
        raise
    except (OSError, KeyError, TypeError, json.JSONDecodeError):
        raise ProbeFailure("hook_timeout_variant_invalid") from None
    return destination


def inspect_trust(
    *,
    codex_executable: Path,
    python_executable: Path,
    plugin: Path,
    hook_timeout_seconds: int | None = None,
) -> dict[str, object]:
    codex = capture_codex(codex_executable)
    python, python_snapshot = _capture_runnable(python_executable)
    temporary_path = None
    with tempfile.TemporaryDirectory() as directory:
        temporary_path = Path(directory).resolve(strict=True)
        reviewed_plugin = _timeout_variant(
            plugin,
            temporary_path / "reviewed-plugin",
            hook_timeout_seconds,
        )
        plugin_sha256 = tree_sha256(reviewed_plugin)
        workspace = temporary_path / "workspace"
        workspace.mkdir()
        environment, installed = install_plugin(
            codex,
            reviewed_plugin,
            temporary_path,
            python,
        )
        if tree_sha256(installed) != plugin_sha256:
            raise ProbeFailure("synthetic_plugin_drift")
        with JsonRpcProcess(codex.resolved, environment) as rpc:
            hook = _hook_from_list(
                rpc.call("hooks/list", {"cwds": [str(workspace)]}),
                cwd=workspace,
                plugin_id=PLUGIN_ID,
            )
        codex.recheck()
        _recheck_runnable(
            python_executable,
            python,
            python_snapshot,
        )
        hook_current_hash = hook["currentHash"]
    if temporary_path is None or temporary_path.exists():
        raise ProbeBlocked("cleanup_incomplete")
    return inspection_record(
        plugin_sha256=plugin_sha256,
        hook_current_hash=hook_current_hash,
        approved_stimulus_sha256=hashlib.sha256(
            stimulus_bytes()
        ).hexdigest(),
        cleanup_status="complete",
    )


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


def stimulus_bytes(*, unapproved: bool = False) -> bytes:
    if type(unapproved) is not bool:
        raise ProbeFailure("stimulus_variant_invalid")
    filler = "b" if unapproved else "a"
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
        + (filler * 8200)
        + "\n"
    )
    return (
        diagnostic
        + "----------------------------------------------------------------------\n"
        + "Ran 1 test in 0.000s\n\n"
        + "OK\n"
    ).encode("utf-8")


def materialize_workspace(
    workspace: Path,
    *,
    unapproved: bool = False,
) -> None:
    if type(unapproved) is not bool:
        raise ProbeFailure("stimulus_variant_invalid")
    filler = "b" if unapproved else "a"
    source = f"""\
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
    + ({filler!r} * 8200)
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


def stimulus_for_row(row_id: str) -> bytes:
    return stimulus_bytes(
        unapproved=row_configuration(row_id)["unapprovedStimulus"]
    )


def materialize_fake_bridge(
    directory: Path,
    python: Path,
    mode: str,
) -> Path:
    if mode not in {"valid", "malformed", "crash"}:
        raise ProbeFailure("fake_bridge_mode_invalid")
    directory.mkdir()
    executable = directory / "bridge"
    if mode == "valid":
        output = {
            "status": "applied",
            "reasonCode": None,
            "appleAvailable": True,
            "localeSupported": True,
            "contextSize": 4096,
            "occupiedTokens": 2048,
            "appleAttempts": 1,
            "condensation": {
                "commandOutcome": "success",
                "summary": "synthetic unittest success",
                "summaryFacts": [
                    "command-class=test",
                    "outcome=success",
                    "exit-status=0",
                    "warning-count=0",
                ],
                "diagnostics": [],
                "warningCount": 0,
                "omittedWarningCount": 0,
                "nextAction": (
                    "continue after successful synthetic unittest"
                ),
                "completionFacts": [
                    "command-finished=true",
                    "task-complete=true",
                ],
            },
        }
        body = (
            "import sys\n"
            "sys.stdin.buffer.read()\n"
            f"sys.stdout.write({(json.dumps(output, separators=(',', ':')) + chr(10))!r})\n"
        )
    elif mode == "malformed":
        body = "import sys\nsys.stdin.buffer.read()\nsys.stdout.write('{}\\n')\n"
    else:
        body = "import sys\nsys.stdin.buffer.read()\nraise SystemExit(70)\n"
    executable.write_text(
        f"#!{python}\n{body}",
        encoding="utf-8",
        newline="\n",
    )
    executable.chmod(0o700)
    return executable


def compile_swift_bridge(
    *,
    xcrun: Path,
    swiftc: Path,
    source: Path,
    output: Path,
) -> Path:
    resolved_xcrun, xcrun_snapshot = _capture_runnable(xcrun)
    resolved_swiftc, swiftc_snapshot = _capture_runnable(swiftc)
    try:
        source_metadata = source.lstat()
    except OSError:
        raise ProbeBlocked("sdk_26_5_unavailable") from None
    if (
        stat.S_ISLNK(source_metadata.st_mode)
        or not stat.S_ISREG(source_metadata.st_mode)
        or not output.parent.is_dir()
    ):
        raise ProbeBlocked("sdk_26_5_unavailable")
    environment = {"PATH": os.environ.get("PATH", "")}
    sdk_version = subprocess.run(
        [str(resolved_xcrun), "--sdk", "macosx", "--show-sdk-version"],
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        shell=False,
        timeout=30,
    )
    sdk_path = subprocess.run(
        [str(resolved_xcrun), "--sdk", "macosx", "--show-sdk-path"],
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        shell=False,
        timeout=30,
    )
    swift_version = subprocess.run(
        [str(resolved_swiftc), "--version"],
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        shell=False,
        timeout=30,
    )
    if (
        sdk_version.returncode != 0
        or sdk_version.stderr
        or sdk_version.stdout != b"26.5\n"
        or sdk_path.returncode != 0
        or sdk_path.stderr
        or not sdk_path.stdout.endswith(b"\n")
        or b"\n" in sdk_path.stdout[:-1]
        or swift_version.returncode != 0
        or swift_version.stderr != b"swift-driver version: 1.148.6 "
        or re.fullmatch(
            rb"Apple Swift version 6\.3\.3 \([^)]+\)\n"
            rb"Target: arm64-apple-macosx26\.0\n",
            swift_version.stdout,
        )
        is None
    ):
        raise ProbeBlocked("sdk_26_5_unavailable")
    completed = subprocess.run(
        [
            str(resolved_swiftc),
            "-parse-as-library",
            "-target",
            "arm64-apple-macos26.4",
            "-sdk",
            sdk_path.stdout.decode("utf-8").strip(),
            str(source),
            "-o",
            str(output),
        ],
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        shell=False,
        timeout=60,
    )
    if completed.returncode != 0 or completed.stdout or completed.stderr:
        raise ProbeBlocked("sdk_26_5_unavailable")
    _recheck_runnable(xcrun, resolved_xcrun, xcrun_snapshot)
    _recheck_runnable(swiftc, resolved_swiftc, swiftc_snapshot)
    try:
        metadata = output.lstat()
    except OSError:
        raise ProbeBlocked("sdk_26_5_unavailable") from None
    if not stat.S_ISREG(metadata.st_mode) or not os.access(output, os.X_OK):
        raise ProbeBlocked("sdk_26_5_unavailable")
    return output


def row_configuration(row_id: str) -> dict[str, object]:
    values = {
        "plugin_off_baseline": (False, "valid", "none", False, False),
        "direct_fake_applied": (True, "valid", "none", False, False),
        "composed_live_apple_applied": (
            True,
            "apple",
            "none",
            False,
            False,
        ),
        "decline_unapproved_stimulus": (
            True,
            "valid",
            "none",
            True,
            False,
        ),
        "bridge_malformed": (
            True,
            "malformed",
            "none",
            False,
            False,
        ),
        "bridge_crash": (True, "crash", "none", False, False),
        "adapter_crash": (
            True,
            "valid",
            "adapter_crash",
            False,
            False,
        ),
        "hook_timeout": (
            True,
            "valid",
            "hook_timeout",
            False,
            True,
        ),
    }
    try:
        enabled, bridge, fault, unapproved, timeout = values[row_id]
    except KeyError:
        raise ProbeFailure("row_id_invalid") from None
    return {
        "pluginEnabled": enabled,
        "bridgeMode": bridge,
        "faultMode": fault,
        "unapprovedStimulus": unapproved,
        "timeoutPlugin": timeout,
    }


def collect_rows(
    through: str,
    runner,
    rows: list[dict[str, object]] | None = None,
) -> list[dict[str, object]]:
    rows = [] if rows is None else rows
    baseline_provider_requests = 2
    for row_id in phases_for(through):
        row = runner(row_id, baseline_provider_requests)
        rows.append(row)
        if row_id == "plugin_off_baseline":
            baseline_provider_requests = row["providerRequests"]
        if row["status"] != "pass":
            break
    return rows


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
    config = row_configuration(phase)
    plugin_enabled = config["pluginEnabled"]
    if plugin_enabled and tree_sha256(plugin) != approved_plugin_sha256:
        raise ProbeFailure("synthetic_plugin_drift")
    with tempfile.TemporaryDirectory() as directory:
        temporary_root = Path(directory).resolve(strict=True)
        workspace = temporary_root / "workspace"
        materialize_workspace(
            workspace,
            unapproved=config["unapprovedStimulus"],
        )
        counter = temporary_root / "command-counter"
        observations = temporary_root / "observations.jsonl"
        if plugin_enabled:
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
        else:
            codex_home = temporary_root / "codex-home"
            codex_home.mkdir()
            environment = {
                "CODEX_HOME": str(codex_home),
                "PATH": os.environ.get("PATH", ""),
                "RUNTIME_V1_PYTHON": str(python),
            }
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
        if config["faultMode"] != "none":
            environment["RUNTIME_V1_FAULT_MODE"] = config["faultMode"]
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
        original = stimulus_for_row(phase)
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
        if phase == "composed_live_apple_applied":
            reasons = [
                row.get("reasonCode")
                for row in consultation_rows
                if row.get("reasonCode") is not None
            ]
            if reasons == ["apple_unavailable"]:
                raise ProbeBlocked("apple_unavailable")
            if reasons == ["locale_unsupported"]:
                raise ProbeBlocked("locale_unsupported")
        apple_attempts = sum(
            row.get("appleAttempts", 0)
            for row in consultation_rows
        )
        if phase == "direct_fake_applied":
            apple_attempts = 0
        return classify_row(
            row_id=phase,
            bridge_kind=config["bridgeMode"],
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
            apple_attempts=apple_attempts,
            apple_valid_results=sum(
                row.get("appleValidResults", 0)
                for row in consultation_rows
            ),
        )


def validate_outer_options(options) -> None:
    if (
        options.xcrun_executable is None
        or options.swiftc_executable is None
        or options.through is None
        or not _digest(options.approved_plugin_sha256)
        or not _digest(options.approved_hook_hash, prefixed=True)
        or not _digest(options.approved_stimulus_sha256)
    ):
        raise ProbeFailure("outer_gate_arguments_invalid")
    if options.through == "complete" and (
        not _digest(options.approved_timeout_plugin_sha256)
        or not _digest(
            options.approved_timeout_hook_hash,
            prefixed=True,
        )
    ):
        raise ProbeFailure("outer_gate_arguments_invalid")


def execute_outer_gate(options) -> dict[str, object]:
    validate_outer_options(options)
    codex = capture_codex(options.codex_executable)
    python, python_snapshot = _capture_runnable(
        options.python_executable
    )
    xcrun, xcrun_snapshot = _capture_runnable(
        options.xcrun_executable
    )
    swiftc, swiftc_snapshot = _capture_runnable(
        options.swiftc_executable
    )
    plugin_sha256 = tree_sha256(options.plugin)
    if plugin_sha256 != options.approved_plugin_sha256:
        raise ProbeFailure("synthetic_plugin_drift")

    temporary_path = None
    rows: list[dict[str, object]] = []
    blocker_reason = None
    with tempfile.TemporaryDirectory() as directory:
        temporary_path = Path(directory).resolve(strict=True)
        bridges = {
            mode: materialize_fake_bridge(
                temporary_path / f"bridge-{mode}",
                python,
                mode,
            )
            for mode in ("valid", "malformed", "crash")
        }
        bridges["apple"] = compile_swift_bridge(
            xcrun=xcrun,
            swiftc=swiftc,
            source=(
                options.plugin / "runtime/DiagnosticCondenser.swift"
            ),
            output=temporary_path / "DiagnosticCondenser",
        )
        timeout_plugin = None
        if options.through == "complete":
            timeout_plugin = _timeout_variant(
                options.plugin,
                temporary_path / "timeout-plugin",
                1,
            )
            if (
                tree_sha256(timeout_plugin)
                != options.approved_timeout_plugin_sha256
            ):
                raise ProbeFailure("synthetic_plugin_drift")

        def runner(row_id: str, baseline: int) -> dict[str, object]:
            config = row_configuration(row_id)
            selected_plugin = (
                timeout_plugin
                if config["timeoutPlugin"]
                else options.plugin
            )
            selected_plugin_sha256 = (
                options.approved_timeout_plugin_sha256
                if config["timeoutPlugin"]
                else options.approved_plugin_sha256
            )
            selected_hook_hash = (
                options.approved_timeout_hook_hash
                if config["timeoutPlugin"]
                else options.approved_hook_hash
            )
            return run_row(
                codex=codex,
                python=python,
                plugin=selected_plugin,
                approved_plugin_sha256=selected_plugin_sha256,
                approved_hook_hash=selected_hook_hash,
                approved_stimulus_sha256=(
                    options.approved_stimulus_sha256
                ),
                bridge_executable=bridges[config["bridgeMode"]],
                phase=row_id,
                baseline_provider_requests=baseline,
            )

        try:
            collect_rows(options.through, runner, rows)
        except ProbeBlocked as error:
            if error.args[0] not in {
                "apple_unavailable",
                "locale_unsupported",
            }:
                raise
            blocker_reason = error.args[0]

        codex.recheck()
        _recheck_runnable(
            options.python_executable,
            python,
            python_snapshot,
        )
        _recheck_runnable(
            options.xcrun_executable,
            xcrun,
            xcrun_snapshot,
        )
        _recheck_runnable(
            options.swiftc_executable,
            swiftc,
            swiftc_snapshot,
        )
    if temporary_path is None or temporary_path.exists():
        raise ProbeBlocked("cleanup_incomplete")
    return build_evidence(
        rows=rows,
        approved_stimulus_sha256=options.approved_stimulus_sha256,
        plugin_sha256=plugin_sha256,
        hook_current_hash=options.approved_hook_hash,
        blocker_reason=blocker_reason,
        cleanup_status="complete",
    )


def _parse_arguments(arguments=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--inspect-trust", action="store_true")
    parser.add_argument("--hook-timeout-seconds", type=int)
    parser.add_argument("--codex-executable", type=Path, required=True)
    parser.add_argument("--python-executable", type=Path, required=True)
    parser.add_argument("--xcrun-executable", type=Path)
    parser.add_argument("--swiftc-executable", type=Path)
    parser.add_argument("--plugin", type=Path, required=True)
    parser.add_argument("--approved-plugin-sha256")
    parser.add_argument("--approved-hook-hash")
    parser.add_argument("--approved-stimulus-sha256")
    parser.add_argument("--approved-timeout-plugin-sha256")
    parser.add_argument("--approved-timeout-hook-hash")
    parser.add_argument(
        "--through",
        choices=("direct", "composed", "complete"),
    )
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(arguments)


def main(arguments=None) -> int:
    options = _parse_arguments(arguments)
    try:
        if options.inspect_trust:
            value = inspect_trust(
                codex_executable=options.codex_executable,
                python_executable=options.python_executable,
                plugin=options.plugin,
                hook_timeout_seconds=options.hook_timeout_seconds,
            )
        else:
            value = execute_outer_gate(options)
        atomic_write_json(options.output, value)
        if options.inspect_trust:
            return 0
        expected = phases_for(options.through)
        rows = value["rows"]
        return int(
            len(rows) != len(expected)
            or any(row["status"] != "pass" for row in rows)
        )
    except (ProbeBlocked, ProbeFailure) as error:
        print(error.args[0], file=sys.stderr)
        return 2
    except (OSError, ValueError):
        print("inspection_failed", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
