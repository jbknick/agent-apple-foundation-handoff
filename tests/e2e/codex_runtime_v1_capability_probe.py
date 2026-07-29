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
APPROVED_CALL_ID = "call-runtime-v1"
DIRECT_TOOL_NAMES = (
    "exec_command",
    "multi_agent_v1",
    "request_user_input",
    "update_plan",
    "view_image",
    "write_stdin",
)
ROW_KEYS = (
    "id",
    "status",
    "reason",
    "bridgeKind",
    "commandExecutions",
    "hookInvocations",
    "bridgeStartObservations",
    "bridgeCompletionObservations",
    "bridgeProcessOutcome",
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
GENERATION_BLOCKER_REASONS = {
    "generation_assets_unavailable",
    "generation_unsupported_language_or_locale",
    "generation_rate_limited",
    "generation_concurrent_requests",
}
GENERATION_FAILURE_REASONS = {
    "generation_exceeded_context_window_size",
    "generation_guardrail_violation",
    "generation_unsupported_guide",
    "generation_decoding_failure",
    "generation_refusal",
    "generation_unknown_error",
}
APPLE_PREFLIGHT_BLOCKER_REASONS = {
    "apple_unavailable",
    "locale_unsupported",
    "context_budget_exceeded",
    "generation_preflight_unavailable",
}
BRIDGE_PROCESS_OUTCOMES = {
    "launch_unavailable",
    "timed_out",
    "nonzero_exit",
    "stderr_nonempty",
    "stdout_shape_invalid",
    "json_invalid",
    "result_shape_invalid",
    "result_observed",
}
BRIDGE_OBSERVATION_OUTCOMES = {
    "start_observation_missing",
    "completion_observation_missing",
    "observation_invalid",
}
BRIDGE_PROCESS_BLOCKERS = {"launch_unavailable", "timed_out"}
OBSERVATION_REASON_CODES = (
    APPLE_PREFLIGHT_BLOCKER_REASONS
    | GENERATION_BLOCKER_REASONS
    | GENERATION_FAILURE_REASONS
    | {"context_budget_exceeded", "contract_invariant_failed"}
)
BRIDGE_EXPECTED_ROW_IDS = {
    "direct_fake_applied",
    "composed_live_apple_applied",
    "bridge_malformed",
    "bridge_crash",
}
FIXTURE_ZERO_ATTEMPT_ROW_IDS = set(REQUIRED_ROW_IDS) - {
    "composed_live_apple_applied"
}
ROW_BRIDGE_KINDS = {
    "plugin_off_baseline": "valid",
    "direct_fake_applied": "valid",
    "composed_live_apple_applied": "apple",
    "decline_unapproved_stimulus": "valid",
    "bridge_malformed": "malformed",
    "bridge_crash": "crash",
    "adapter_crash": "valid",
    "hook_timeout": "valid",
}
ROW_PASS_PROCESS_OUTCOMES = {
    "plugin_off_baseline": None,
    "direct_fake_applied": "result_observed",
    "composed_live_apple_applied": "result_observed",
    "decline_unapproved_stimulus": None,
    "bridge_malformed": "result_shape_invalid",
    "bridge_crash": "nonzero_exit",
    "adapter_crash": None,
    "hook_timeout": None,
}
ROW_INVARIANT_FAILURES = {
    "replacement_invariant_failed",
    "untouched_original_invariant_failed",
    "bridge_process_invariant_failed",
}
ROW_INVARIANT_FAILURE_IDS = {
    "replacement_invariant_failed": {
        "direct_fake_applied",
        "composed_live_apple_applied",
    },
    "untouched_original_invariant_failed": set(REQUIRED_ROW_IDS)
    - {
        "direct_fake_applied",
        "composed_live_apple_applied",
    },
    "bridge_process_invariant_failed": BRIDGE_EXPECTED_ROW_IDS,
}
ALLOWED_BLOCKERS = {
    "historical_helpers_unavailable",
    "missing_binary_or_version_mismatch",
    "sdk_26_5_unavailable",
    "hook_trust_unavailable",
    "cleanup_incomplete",
} | (
    APPLE_PREFLIGHT_BLOCKER_REASONS
    | GENERATION_BLOCKER_REASONS
    | BRIDGE_PROCESS_BLOCKERS
)
TERMINAL_FAILURE_REASONS = {
    "app_server_early_exit",
    "app_server_json_invalid",
    "app_server_request_failed",
    "app_server_response_id_invalid",
    "app_server_result_invalid",
    "app_server_start_failed",
    "app_server_stderr",
    "app_server_timeout",
    "app_server_write_failed",
    "blocker_reason_invalid",
    "codex_process_nonzero",
    "codex_stderr_nonempty",
    "direct_tool_mode_unavailable",
    "duplicate_row",
    "evidence_digest_invalid",
    "evidence_safety_failed",
    "evidence_shape_invalid",
    "evidence_value_invalid",
    "fake_bridge_mode_invalid",
    "gate_phase_invalid",
    "generation_error_invariant_failed",
    "generation_reason_invalid",
    "host_resolution_or_version_drift",
    "hook_timeout_variant_invalid",
    "inspection_failed",
    "inspection_value_invalid",
    "marketplace_materialization_failed",
    "observation_invalid",
    "outer_gate_arguments_invalid",
    "plugin_command_failed",
    "provider_request_count_invalid",
    "provider_request_invalid",
    "row_id_invalid",
    "stimulus_grant_invalid",
    "stimulus_variant_invalid",
    "synthetic_plugin_drift",
} | GENERATION_FAILURE_REASONS
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
    "timeoutPluginSha256",
    "timeoutHookCurrentHash",
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


@dataclass(frozen=True)
class CapturedPython:
    locator: Path
    resolved: Path
    snapshot: tuple[int, ...]
    version: bytes

    def recheck(self) -> None:
        _recheck_runnable(self.locator, self.resolved, self.snapshot)
        if _python_version(self.resolved) != self.version:
            raise ProbeFailure("host_resolution_or_version_drift")


def _python_version(executable: Path) -> bytes:
    try:
        completed = subprocess.run(
            [str(executable), "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            shell=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return b""
    output = completed.stdout or completed.stderr
    if (
        completed.returncode != 0
        or bool(completed.stdout) == bool(completed.stderr)
        or re.fullmatch(rb"Python [0-9]+(?:\.[0-9]+)+\n", output)
        is None
    ):
        return b""
    return output


def capture_python(path: Path) -> CapturedPython:
    resolved, snapshot = _capture_runnable(path)
    version = _python_version(resolved)
    if not version:
        raise ProbeBlocked("missing_binary_or_version_mismatch")
    captured = CapturedPython(path, resolved, snapshot, version)
    captured.recheck()
    return captured


def run_with_python_bracket(captured: CapturedPython, operation):
    captured.recheck()
    try:
        return operation()
    finally:
        captured.recheck()


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


_COMPLETED_EXEC_ENVELOPE_HEADER = re.compile(
    rb"Chunk ID: [0-9a-f]+\n"
    rb"Wall time: (?:0|[1-9][0-9]*)\.[0-9]+ seconds\n"
    rb"Process exited with code 0\n"
    rb"Original token count: (?:0|[1-9][0-9]*)\n"
    rb"Output:\n"
)


def preserves_untouched_original(
    output: bytes,
    original: bytes,
) -> bool:
    header = _COMPLETED_EXEC_ENVELOPE_HEADER.match(output)
    return header is not None and output[header.end() :] == original


def generation_error_gate_result(reason: str) -> str:
    if reason in GENERATION_BLOCKER_REASONS:
        return "blocked"
    if (
        reason in GENERATION_FAILURE_REASONS
        or reason == "contract_invariant_failed"
    ):
        return "fail"
    raise ProbeFailure("generation_reason_invalid")


def observations_are_closed(
    observations: list[Mapping[str, object]],
    *,
    call_id: str,
) -> bool:
    event_keys = {
        "hook_invoked": {"event", "callID", "hookInvocations"},
        "original_observed": {
            "event",
            "callID",
            "originalSha256",
        },
        "bridge_process_started": {"event", "callID"},
        "bridge_process_completed": {
            "event",
            "callID",
            "bridgeProcessOutcome",
        },
        "consultation_completed": {
            "event",
            "callID",
            "appleAttempts",
            "appleValidResults",
            "reasonCode",
        },
        "replacement_emitted": {
            "event",
            "callID",
            "replacementSha256",
            "replacementBytes",
            "appleAttempts",
        },
    }
    seen: dict[str, Mapping[str, object]] = {}
    positions: dict[str, int] = {}
    for position, value in enumerate(observations):
        if type(value) is not dict:
            return False
        event = value.get("event")
        if (
            type(event) is not str
            or event not in event_keys
            or event in seen
            or set(value) != event_keys[event]
            or value.get("callID") != call_id
        ):
            return False
        seen[event] = value
        positions[event] = position
        if event == "hook_invoked" and (
            type(value["hookInvocations"]) is not int
            or value["hookInvocations"] != 1
        ):
            return False
        if event == "original_observed" and not _digest(
            value["originalSha256"]
        ):
            return False
        if event == "bridge_process_completed" and (
            type(value["bridgeProcessOutcome"]) is not str
            or value["bridgeProcessOutcome"]
            not in BRIDGE_PROCESS_OUTCOMES
        ):
            return False
        if event == "consultation_completed":
            attempts = value["appleAttempts"]
            valid = value["appleValidResults"]
            reason = value["reasonCode"]
            if (
                type(attempts) is not int
                or attempts not in {0, 1}
                or type(valid) is not int
                or valid not in {0, 1}
                or (
                    valid == 1
                    and (attempts != 1 or reason is not None)
                )
                or (
                    valid == 0
                    and (
                        type(reason) is not str
                        or reason not in OBSERVATION_REASON_CODES
                    )
                )
            ):
                return False
        if event == "replacement_emitted":
            if (
                not _digest(value["replacementSha256"])
                or type(value["replacementBytes"]) is not int
                or not 1 <= value["replacementBytes"] <= 4096
                or type(value["appleAttempts"]) is not int
                or value["appleAttempts"] not in {0, 1}
            ):
                return False
    if not observations:
        return True
    if "hook_invoked" not in seen:
        return False
    if (
        set(seen) - {"hook_invoked", "original_observed"}
        and "original_observed" not in seen
    ):
        return False
    ordered_pairs = (
        ("hook_invoked", "original_observed"),
        ("original_observed", "bridge_process_started"),
        ("bridge_process_started", "bridge_process_completed"),
        ("bridge_process_completed", "consultation_completed"),
        ("consultation_completed", "replacement_emitted"),
    )
    if any(
        later in seen
        and earlier in seen
        and positions[earlier] >= positions[later]
        for earlier, later in ordered_pairs
    ):
        return False
    consultation = seen.get("consultation_completed")
    completion = seen.get("bridge_process_completed")
    if consultation is not None and (
        completion is None
        or completion["bridgeProcessOutcome"] != "result_observed"
    ):
        return False
    if "replacement_emitted" in seen and (
        consultation is None
        or consultation["appleValidResults"] != 1
        or consultation["appleAttempts"]
        != seen["replacement_emitted"]["appleAttempts"]
    ):
        return False
    return True


def summarize_bridge_observations(
    observations: list[Mapping[str, object]],
    *,
    call_id: str,
    bridge_expected: bool,
) -> tuple[str | None, int, int]:
    process = [
        value
        for value in observations
        if value.get("event")
        in {"bridge_process_started", "bridge_process_completed"}
    ]
    starts = [
        value
        for value in process
        if value.get("event") == "bridge_process_started"
    ]
    completions = [
        value
        for value in process
        if value.get("event") == "bridge_process_completed"
    ]
    start_count = int(bool(starts))
    completion_count = int(bool(completions))
    if not bridge_expected:
        return (
            ("observation_invalid" if process else None),
            start_count,
            completion_count,
        )
    if not starts:
        return (
            "start_observation_missing",
            0,
            completion_count,
        )
    if len(starts) == 1 and not completions:
        return "completion_observation_missing", 1, 0
    if len(starts) != 1 or len(completions) != 1:
        return "observation_invalid", start_count, completion_count
    start = starts[0]
    completion = completions[0]
    if (
        set(start) != {"event", "callID"}
        or start["callID"] != call_id
        or set(completion)
        != {"event", "callID", "bridgeProcessOutcome"}
        or completion["callID"] != call_id
        or completion["bridgeProcessOutcome"]
        not in BRIDGE_PROCESS_OUTCOMES
    ):
        return "observation_invalid", 1, 1
    return completion["bridgeProcessOutcome"], 1, 1


def replacement_observation_matches(
    observations: list[Mapping[str, object]],
    *,
    next_output: bytes,
    bridge_process_outcome: str | None,
) -> bool:
    if not observations_are_closed(
        observations,
        call_id=APPROVED_CALL_ID,
    ):
        return False
    replacements = [
        value
        for value in observations
        if value["event"] == "replacement_emitted"
    ]
    consultations = [
        value
        for value in observations
        if value["event"] == "consultation_completed"
    ]
    applied = (
        bridge_process_outcome == "result_observed"
        and len(consultations) == 1
        and consultations[0]["appleValidResults"] == 1
    )
    if not applied:
        return not replacements
    if len(replacements) != 1:
        return False
    replacement = replacements[0]
    return (
        replacement["replacementBytes"] == len(next_output)
        and replacement["replacementSha256"]
        == hashlib.sha256(next_output).hexdigest()
        and replacement["appleAttempts"]
        == consultations[0]["appleAttempts"]
    )


def enforce_composed_terminal(
    reasons: list[object],
    row: dict[str, object],
) -> None:
    if not reasons:
        return
    if len(reasons) != 1 or type(reasons[0]) is not str:
        raise ProbeFailure("generation_reason_invalid")
    reason = reasons[0]
    expected_attempts = (
        0 if reason in APPLE_PREFLIGHT_BLOCKER_REASONS else 1
    )
    if (
        row.get("status") != "pass"
        or row.get("appleAttempts") != expected_attempts
        or row.get("appleValidResults") != 0
        or row.get("originalPreserved") is not True
        or row.get("replacementPresentInNextRequest") is not False
        or row.get("replacementBytes") != 0
        or row.get("spooled") is not False
        or row.get("commandExecutions") != 1
        or row.get("hookInvocations") != 1
        or row.get("providerRequests") != 2
        or row.get("additionalParentModelTurns") != 0
    ):
        raise ProbeFailure("generation_error_invariant_failed")
    if reason in APPLE_PREFLIGHT_BLOCKER_REASONS:
        row["status"] = "blocked"
        row["reason"] = reason
        return
    row["status"] = generation_error_gate_result(reason)
    row["reason"] = reason


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
    apple_attempts: int | None,
    apple_valid_results: int = 0,
    bridge_start_observations: int = 0,
    bridge_completion_observations: int = 0,
    bridge_process_outcome: str | None = None,
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
        original_preserved = preserves_untouched_original(
            next_output,
            stimulus,
        )
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
        "bridgeStartObservations": bridge_start_observations,
        "bridgeCompletionObservations": bridge_completion_observations,
        "bridgeProcessOutcome": bridge_process_outcome,
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


def row_observability_is_valid(row: Mapping[str, object]) -> bool:
    row_id = row.get("id")
    outcome = row.get("bridgeProcessOutcome")
    starts = row.get("bridgeStartObservations")
    completions = row.get("bridgeCompletionObservations")
    attempts = row.get("appleAttempts")
    valid_results = row.get("appleValidResults")
    if (
        type(row_id) is not str
        or row_id not in REQUIRED_ROW_IDS
        or (outcome is not None and type(outcome) is not str)
        or type(starts) is not int
        or starts not in {0, 1}
        or type(completions) is not int
        or completions not in {0, 1}
        or (
            attempts is not None
            and (type(attempts) is not int or attempts not in {0, 1})
        )
        or type(valid_results) is not int
        or valid_results not in {0, 1}
    ):
        return False
    if outcome is None:
        return (
            row_id not in BRIDGE_EXPECTED_ROW_IDS
            and starts == completions == 0
            and attempts == 0
            and valid_results == 0
        )
    if outcome == "result_observed":
        if starts != 1 or completions != 1 or attempts not in {0, 1}:
            return False
        if row_id == "composed_live_apple_applied":
            return (
                valid_results in {0, 1}
                if row.get("status") == "pass"
                else valid_results == 0
            )
        return (
            row_id in FIXTURE_ZERO_ATTEMPT_ROW_IDS
            and attempts == 0
            and valid_results == 0
            and row.get("status") == "pass"
        )
    if outcome in BRIDGE_PROCESS_OUTCOMES - {"result_observed"}:
        if starts != 1 or completions != 1 or valid_results != 0:
            return False
    elif outcome == "start_observation_missing":
        if starts != 0 or valid_results != 0:
            return False
    elif outcome == "completion_observation_missing":
        if starts != 1 or completions != 0 or valid_results != 0:
            return False
    elif outcome == "observation_invalid":
        if valid_results != 0:
            return False
    else:
        return False
    if outcome in BRIDGE_OBSERVATION_OUTCOMES:
        return attempts is None and row.get("status") == "fail"
    if row_id == "composed_live_apple_applied":
        expected_status = (
            "blocked" if outcome in BRIDGE_PROCESS_BLOCKERS else "fail"
        )
        return attempts is None and row.get("status") == expected_status
    return (
        row_id in FIXTURE_ZERO_ATTEMPT_ROW_IDS
        and attempts == 0
        and row.get("status") == "pass"
    )


def apply_live_process_outcome(row: dict[str, object]) -> None:
    outcome = row["bridgeProcessOutcome"]
    if outcome == "result_observed":
        return
    if (
        outcome is None
        or row["originalPreserved"] is not True
        or row["replacementPresentInNextRequest"] is not False
        or row["commandExecutions"] != 1
        or row["providerRequests"] != 2
        or row["additionalParentModelTurns"] != 0
    ):
        row["status"] = "fail"
        row["reason"] = "bridge_process_invariant_failed"
        return
    row["status"] = (
        "blocked" if outcome in BRIDGE_PROCESS_BLOCKERS else "fail"
    )
    row["reason"] = outcome


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
    if any(not row_observability_is_valid(row) for row in rows):
        return "fail", "bridge_observation_invariant_failed"
    composed = by_id.get("composed_live_apple_applied")
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
    for row in rows:
        if row["bridgeProcessOutcome"] in (
            BRIDGE_PROCESS_OUTCOMES - {"result_observed"}
        ) | BRIDGE_OBSERVATION_OUTCOMES and (
            row["originalAbsentFromNextRequest"] is not False
            or row["replacementPresentInNextRequest"] is not False
            or row["replacementSha256"] is not None
            or row["replacementBytes"] != 0
            or row["spooled"] is not False
        ):
            return "fail", "replacement_invariant_failed"
        if (
            row["bridgeProcessOutcome"]
            in (
                BRIDGE_PROCESS_OUTCOMES - {"result_observed"}
            )
            | BRIDGE_OBSERVATION_OUTCOMES
            and row["originalPreserved"] is not True
        ):
            return "fail", "untouched_original_invariant_failed"
    for row_id in (
        "direct_fake_applied",
        "composed_live_apple_applied",
    ):
        row = by_id.get(row_id)
        replacement_required = (
            row_id == "direct_fake_applied"
            or (
                row is not None
                and row["appleValidResults"] == 1
            )
        )
        if (
            row is not None
            and row["bridgeProcessOutcome"] == "result_observed"
            and replacement_required
            and (
            row["originalAbsentFromNextRequest"] is not True
            or row["replacementPresentInNextRequest"] is not True
            or row["spooled"] is not False
            or row["status"] == "fail"
            )
        ):
            return "fail", "replacement_invariant_failed"
    for row in rows:
        if (
            row["bridgeProcessOutcome"] is not None
            and row["status"] in {"blocked", "fail"}
        ):
            return row["status"], row["reason"]
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


def row_values_are_closed(
    row: Mapping[str, object],
    *,
    approved_stimulus_sha256: str,
) -> bool:
    row_id = row.get("id")
    status = row.get("status")
    if (
        row_id not in REQUIRED_ROW_IDS
        or row.get("bridgeKind") != ROW_BRIDGE_KINDS[row_id]
        or type(status) is not str
        or status not in {"pass", "fail", "blocked"}
        or type(row.get("reason")) is not str
        or type(row.get("commandExecutions")) is not int
        or row.get("commandExecutions") != 1
        or type(row.get("hookInvocations")) is not int
        or row.get("hookInvocations")
        != (0 if row_id == "plugin_off_baseline" else 1)
        or type(row.get("providerRequests")) is not int
        or row.get("providerRequests") != 2
        or type(row.get("additionalParentModelTurns")) is not int
        or row.get("additionalParentModelTurns") != 0
        or row.get("cleanupStatus") != "complete"
        or type(row.get("originalAbsentFromNextRequest")) is not bool
        or type(row.get("replacementPresentInNextRequest")) is not bool
        or type(row.get("originalPreserved")) is not bool
        or type(row.get("spooled")) is not bool
        or type(row.get("replacementBytes")) is not int
        or not _digest(row.get("originalSha256"))
        or not _digest(row.get("nextRequestOutputSha256"))
    ):
        return False
    original = row["originalSha256"]
    expected_grant = row_id != "decline_unapproved_stimulus"
    if (
        (original == approved_stimulus_sha256) is not expected_grant
        or row.get("hookInputSha256")
        != (None if row_id == "plugin_off_baseline" else original)
    ):
        return False
    replacement = row["replacementPresentInNextRequest"]
    if replacement:
        if (
            row_id
            not in {
                "direct_fake_applied",
                "composed_live_apple_applied",
            }
            or not _digest(row.get("replacementSha256"))
            or row["originalAbsentFromNextRequest"] is not True
            or row["originalPreserved"] is not False
            or not 1 <= row["replacementBytes"] <= 4096
            or row["spooled"] is not False
        ):
            return False
    elif (
        row.get("replacementSha256") is not None
        or row["originalAbsentFromNextRequest"] is not False
        or row["replacementBytes"] != 0
        or row["spooled"] is not False
    ):
        return False
    outcome = row["bridgeProcessOutcome"]
    status = row["status"]
    reason = row["reason"]
    if status == "pass":
        expected_replacement = row_id in {
            "direct_fake_applied",
            "composed_live_apple_applied",
        }
        return (
            reason
            == (
                "replacement_observed"
                if expected_replacement
                else "untouched_original_observed"
            )
            and outcome == ROW_PASS_PROCESS_OUTCOMES[row_id]
            and replacement is expected_replacement
            and row["originalPreserved"] is (not expected_replacement)
            and row["appleAttempts"]
            == (1 if row_id == "composed_live_apple_applied" else 0)
            and row["appleValidResults"]
            == (1 if row_id == "composed_live_apple_applied" else 0)
        )
    if outcome in BRIDGE_OBSERVATION_OUTCOMES:
        return (
            status == "fail"
            and reason == outcome
            and row["appleAttempts"] is None
            and row["appleValidResults"] == 0
            and row["originalPreserved"] is True
        )
    if outcome in BRIDGE_PROCESS_OUTCOMES - {"result_observed"}:
        return (
            row_id in BRIDGE_EXPECTED_ROW_IDS
            and status
            == (
                "blocked"
                if outcome in BRIDGE_PROCESS_BLOCKERS
                else "fail"
            )
            and reason == outcome
            and row["appleAttempts"] is None
            and row["appleValidResults"] == 0
            and row["originalPreserved"] is True
        )
    if (
        row_id == "composed_live_apple_applied"
        and outcome == "result_observed"
        and row["appleValidResults"] == 0
        and row["replacementPresentInNextRequest"] is False
        and row["originalPreserved"] is True
    ):
        zero_attempt = reason in APPLE_PREFLIGHT_BLOCKER_REASONS
        blocked = (
            zero_attempt
            or reason in GENERATION_BLOCKER_REASONS
        )
        return (
            reason
            in (
                APPLE_PREFLIGHT_BLOCKER_REASONS
                | GENERATION_BLOCKER_REASONS
                | GENERATION_FAILURE_REASONS
                | {"contract_invariant_failed"}
            )
            and status == ("blocked" if blocked else "fail")
            and row["appleAttempts"] == (0 if zero_attempt else 1)
        )
    if status != "fail" or reason not in ROW_INVARIANT_FAILURES:
        return False
    if row_id not in ROW_INVARIANT_FAILURE_IDS[reason]:
        return False
    if reason == "replacement_invariant_failed":
        return outcome == "result_observed"
    if reason == "bridge_process_invariant_failed":
        return outcome in (
            BRIDGE_PROCESS_OUTCOMES - {"result_observed"}
        ) | BRIDGE_OBSERVATION_OUTCOMES
    return outcome == ROW_PASS_PROCESS_OUTCOMES[row_id]


def validate_evidence(value: Mapping[str, object]) -> dict[str, object]:
    if type(value) is not dict or set(value) != set(EVIDENCE_KEYS):
        raise ProbeFailure("evidence_shape_invalid")
    rows = value["rows"]
    if (
        type(rows) is not list
        or type(value.get("status")) is not str
        or type(value.get("reason")) is not str
    ):
        raise ProbeFailure("evidence_shape_invalid")
    for row in rows:
        if type(row) is not dict or set(row) != set(ROW_KEYS):
            raise ProbeFailure("evidence_shape_invalid")
        if (
            not row_observability_is_valid(row)
            or not row_values_are_closed(
                row,
                approved_stimulus_sha256=value.get(
                    "approvedStimulusSha256"
                ),
            )
        ):
            raise ProbeFailure("evidence_value_invalid")
        if (
            row["id"] == "composed_live_apple_applied"
            and row["status"] == "pass"
            and (
                row["bridgeProcessOutcome"] != "result_observed"
                or row["appleAttempts"] != 1
                or row["appleValidResults"] != 1
            )
        ):
            raise ProbeFailure("evidence_value_invalid")
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
    terminal = not rows and value["status"] in {"fail", "blocked"}
    if rows:
        expected_status, expected_reason = derive_gate_status(
            rows,
            approved_stimulus_sha256=value.get(
                "approvedStimulusSha256"
            ),
            blocker_reason=None,
            unsafe_findings=value.get(
                "unsafeCommittedEvidenceFindings"
            ),
            cleanup_status=value.get("cleanupStatus"),
        )
        if (value.get("status"), value.get("reason")) != (
            expected_status,
            expected_reason,
        ):
            raise ProbeFailure("evidence_value_invalid")
    elif not (
        (
            value.get("status") == "blocked"
            and value.get("reason") in ALLOWED_BLOCKERS
        )
        or (
            value.get("status") == "fail"
            and value.get("reason") in TERMINAL_FAILURE_REASONS
        )
    ):
        raise ProbeFailure("evidence_value_invalid")
    if (
        type(value["schemaVersion"]) is not int
        or value["schemaVersion"] != 1
        or type(value["gate"]) is not str
        or value["gate"] != "runtime-v1-successor-capability"
        or value["status"] not in {"pass", "fail", "blocked"}
        or type(value["codexExecutable"]) is not str
        or value["codexExecutable"] != "<host-path>"
        or (
            terminal
            and (
                (
                    value["codexVersion"] is not None
                    and (
                        type(value["codexVersion"]) is not str
                        or value["codexVersion"] != "0.145.0"
                    )
                )
                or (
                    value["sdkVersion"] is not None
                    and (
                        type(value["sdkVersion"]) is not str
                        or value["sdkVersion"] != "26.5"
                    )
                )
                or (
                    value["swiftVersion"] is not None
                    and (
                        type(value["swiftVersion"]) is not str
                        or value["swiftVersion"] != "6.3.3"
                    )
                )
                or type(value["hookTrustStatus"]) is not str
                or value["hookTrustStatus"]
                not in {"blocked", "trusted"}
                or (
                    value["directToolMode"] is not None
                    and value["directToolMode"] is not True
                )
                or (
                    value["codeModeEnabled"] is not None
                    and value["codeModeEnabled"] is not False
                )
            )
        )
        or (
            not terminal
            and (
                type(value["codexVersion"]) is not str
                or value["codexVersion"] != "0.145.0"
                or type(value["sdkVersion"]) is not str
                or value["sdkVersion"] != "26.5"
                or type(value["swiftVersion"]) is not str
                or value["swiftVersion"] != "6.3.3"
                or type(value["hookTrustStatus"]) is not str
                or value["hookTrustStatus"] != "trusted"
                or value["directToolMode"] is not True
                or value["codeModeEnabled"] is not False
            )
        )
        or (
            value["pluginSha256"] is not None
            and not _digest(value["pluginSha256"])
        )
        or (
            value["hookCurrentHash"] is not None
            and not _digest(value["hookCurrentHash"], prefixed=True)
        )
        or (
            not terminal
            and (
                value["pluginSha256"] is None
                or value["hookCurrentHash"] is None
            )
        )
        or (
            value["timeoutPluginSha256"] is not None
            and not _digest(value["timeoutPluginSha256"])
        )
        or (
            value["timeoutHookCurrentHash"] is not None
            and not _digest(
                value["timeoutHookCurrentHash"],
                prefixed=True,
            )
        )
        or (
            (value["timeoutPluginSha256"] is None)
            != (value["timeoutHookCurrentHash"] is None)
        )
        or (
            len(rows) == len(REQUIRED_ROW_IDS)
            and value["timeoutPluginSha256"] is None
        )
        or (
            value["timeoutPluginSha256"] is not None
            and value["timeoutPluginSha256"] == value["pluginSha256"]
        )
        or (
            value["timeoutHookCurrentHash"] is not None
            and value["timeoutHookCurrentHash"] == value["hookCurrentHash"]
        )
        or (
            value["approvedStimulusSha256"] is not None
            and not _digest(value["approvedStimulusSha256"])
        )
        or (
            not terminal and value["approvedStimulusSha256"] is None
        )
        or type(value["contextClassification"]) is not str
        or value["contextClassification"] != "C0"
        or type(value["contextGrantStatus"]) is not str
        or value["contextGrantStatus"] not in {
            "approved_exact_synthetic_hash",
            "blocked",
        }
        or (
            not terminal
            and value["contextGrantStatus"]
            != "approved_exact_synthetic_hash"
        )
        or type(value["unsafeCommittedEvidenceFindings"]) is not int
        or value["unsafeCommittedEvidenceFindings"] < 0
        or type(value["cleanupStatus"]) is not str
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
    timeout_plugin_sha256: str | None,
    timeout_hook_current_hash: str | None,
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
        "timeoutPluginSha256": timeout_plugin_sha256,
        "timeoutHookCurrentHash": timeout_hook_current_hash,
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


def terminal_evidence(
    options,
    status: str,
    reason: str,
    cleanup_status: str = "complete",
) -> dict[str, object]:
    def digest_or_none(value, *, prefixed=False):
        return value if _digest(value, prefixed=prefixed) else None

    plugin_sha256 = digest_or_none(options.approved_plugin_sha256)
    hook_hash = digest_or_none(
        options.approved_hook_hash,
        prefixed=True,
    )
    timeout_plugin_sha256 = digest_or_none(
        options.approved_timeout_plugin_sha256
    )
    timeout_hook_hash = digest_or_none(
        options.approved_timeout_hook_hash,
        prefixed=True,
    )
    if (
        timeout_plugin_sha256 is None
        or timeout_hook_hash is None
        or timeout_plugin_sha256 == plugin_sha256
        or timeout_hook_hash == hook_hash
    ):
        timeout_plugin_sha256 = None
        timeout_hook_hash = None
    return validate_evidence(
        {
            "schemaVersion": 1,
            "gate": "runtime-v1-successor-capability",
            "status": status,
            "reason": reason,
            "codexVersion": None,
            "codexExecutable": "<host-path>",
            "sdkVersion": None,
            "swiftVersion": None,
            "pluginSha256": plugin_sha256,
            "hookCurrentHash": hook_hash,
            "timeoutPluginSha256": timeout_plugin_sha256,
            "timeoutHookCurrentHash": timeout_hook_hash,
            "hookTrustStatus": "blocked",
            "approvedStimulusSha256": digest_or_none(
                options.approved_stimulus_sha256
            ),
            "contextClassification": "C0",
            "contextGrantStatus": (
                "approved_exact_synthetic_hash"
                if _digest(options.approved_stimulus_sha256)
                else "blocked"
            ),
            "directToolMode": None,
            "codeModeEnabled": None,
            "rows": [],
            "unsafeCommittedEvidenceFindings": 0,
            "cleanupStatus": cleanup_status,
        }
    )


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
                "name": "exec_command",
                "arguments": json.dumps(
                    {"cmd": APPROVED_COMMAND},
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
    python = capture_python(python_executable)
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
            python.resolved,
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
        python.recheck()
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
        'web_search="disabled"',
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


def require_direct_exec_requests(
    requests: list[Mapping[str, Any]],
) -> None:
    if len(requests) != 2:
        raise ProbeFailure("provider_request_invalid")
    calls = []
    for request in requests:
        tools = request.get("tools")
        items = request.get("input")
        if (
            type(tools) is not list
            or len(tools) != len(DIRECT_TOOL_NAMES)
            or {
                tool.get("name")
                for tool in tools
                if type(tool) is dict
                and type(tool.get("name")) is str
            }
            != set(DIRECT_TOOL_NAMES)
            or type(items) is not list
        ):
            raise ProbeFailure("direct_tool_mode_unavailable")
        calls.extend(
            item
            for item in items
            if type(item) is dict
            and item.get("type") == "function_call"
        )
    if len(calls) != 1 or not {
        "type",
        "call_id",
        "name",
        "arguments",
    } <= set(calls[0]):
        raise ProbeFailure("direct_tool_mode_unavailable")
    try:
        arguments = json.loads(calls[0]["arguments"])
    except (TypeError, json.JSONDecodeError):
        raise ProbeFailure("direct_tool_mode_unavailable") from None
    if (
        calls[0]["call_id"] != "call-runtime-v1"
        or calls[0]["name"] != "exec_command"
        or arguments != {"cmd": APPROVED_COMMAND}
    ):
        raise ProbeFailure("direct_tool_mode_unavailable")
    _function_output(requests[1])


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

sys.stderr = sys.stdout

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


def validate_installed_row_result(
    returncode: int,
    stderr: bytes,
    provider_request_count: int,
) -> None:
    if returncode != 0:
        raise ProbeFailure("codex_process_nonzero")
    if stderr:
        raise ProbeFailure("codex_stderr_nonempty")
    if provider_request_count != 2:
        raise ProbeFailure("provider_request_count_invalid")


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
            master_fd, slave_fd = os.openpty()
            try:
                completed = subprocess.run(
                    [
                        str(codex.resolved),
                        *build_exec_arguments(
                            f"http://{host}:{port}",
                            workspace,
                        ),
                    ],
                    env=environment,
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
        validate_installed_row_result(
            completed.returncode,
            completed.stderr,
            len(server.requests),
        )
        require_direct_exec_requests(server.requests)
        next_output = _function_output(server.requests[1])
        if not counter.is_file() or counter.read_text() != "1":
            command_executions = -1
        else:
            command_executions = 1
        rows = []
        observation_parse_invalid = False
        if observations.is_file():
            try:
                observation_lines = observations.read_text(
                    encoding="utf-8"
                ).splitlines()
            except UnicodeDecodeError:
                observation_lines = []
                observation_parse_invalid = True
            for line in observation_lines:
                try:
                    value = json.loads(line)
                except json.JSONDecodeError:
                    observation_parse_invalid = True
                    continue
                if type(value) is not dict:
                    observation_parse_invalid = True
                    continue
                rows.append(value)
        if not observations_are_closed(
            rows,
            call_id=APPROVED_CALL_ID,
        ):
            observation_parse_invalid = True
        if observation_parse_invalid:
            raise ProbeFailure("observation_invalid")
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
        bridge_process_outcome, bridge_starts, bridge_completions = (
            summarize_bridge_observations(
                rows,
                call_id=APPROVED_CALL_ID,
                bridge_expected=phase in BRIDGE_EXPECTED_ROW_IDS,
            )
        )
        if (
            bridge_process_outcome == "result_observed"
        ) != (len(consultation_rows) == 1):
            bridge_process_outcome = "observation_invalid"
        if not replacement_observation_matches(
            rows,
            next_output=next_output,
            bridge_process_outcome=bridge_process_outcome,
        ):
            raise ProbeFailure("observation_invalid")
        reasons = [
            row.get("reasonCode")
            for row in consultation_rows
            if row.get("reasonCode") is not None
        ]
        if (
            bridge_process_outcome == "result_observed"
            and len(consultation_rows) == 1
            and type(consultation_rows[0].get("appleAttempts")) is int
            and consultation_rows[0]["appleAttempts"] in {0, 1}
        ):
            apple_attempts = consultation_rows[0]["appleAttempts"]
        elif bridge_process_outcome in BRIDGE_OBSERVATION_OUTCOMES:
            apple_attempts = None
        elif phase in FIXTURE_ZERO_ATTEMPT_ROW_IDS:
            apple_attempts = 0
        else:
            apple_attempts = None
        if phase == "direct_fake_applied":
            apple_attempts = 0
        apple_valid_results = sum(
            row.get("appleValidResults", 0)
            for row in consultation_rows
            if type(row.get("appleValidResults")) is int
        )
        if bridge_process_outcome != "result_observed":
            apple_valid_results = 0
        if phase == "direct_fake_applied":
            apple_valid_results = 0
        classified = classify_row(
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
            apple_valid_results=apple_valid_results,
            bridge_start_observations=bridge_starts,
            bridge_completion_observations=bridge_completions,
            bridge_process_outcome=bridge_process_outcome,
        )
        if bridge_process_outcome in BRIDGE_OBSERVATION_OUTCOMES:
            apply_live_process_outcome(classified)
        elif phase == "composed_live_apple_applied":
            if bridge_process_outcome == "result_observed":
                enforce_composed_terminal(reasons, classified)
            else:
                apply_live_process_outcome(classified)
        return classified


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
        or (
            options.approved_timeout_plugin_sha256
            == options.approved_plugin_sha256
        )
        or (
            options.approved_timeout_hook_hash
            == options.approved_hook_hash
        )
    ):
        raise ProbeFailure("outer_gate_arguments_invalid")


def execute_outer_gate(options) -> dict[str, object]:
    validate_outer_options(options)
    codex = capture_codex(options.codex_executable)
    python = capture_python(options.python_executable)
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
                python.resolved,
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
            return run_with_python_bracket(
                python,
                lambda: run_row(
                    codex=codex,
                    python=python.resolved,
                    plugin=selected_plugin,
                    approved_plugin_sha256=selected_plugin_sha256,
                    approved_hook_hash=selected_hook_hash,
                    approved_stimulus_sha256=(
                        options.approved_stimulus_sha256
                    ),
                    bridge_executable=bridges[
                        config["bridgeMode"]
                    ],
                    phase=row_id,
                    baseline_provider_requests=baseline,
                ),
            )

        try:
            collect_rows(options.through, runner, rows)
        except ProbeBlocked as error:
            if error.args[0] not in ALLOWED_BLOCKERS:
                raise
            blocker_reason = error.args[0]

        codex.recheck()
        python.recheck()
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
        timeout_plugin_sha256=(
            options.approved_timeout_plugin_sha256
        ),
        timeout_hook_current_hash=(
            options.approved_timeout_hook_hash
        ),
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
    except ProbeBlocked as error:
        value = terminal_evidence(options, "blocked", error.args[0])
        atomic_write_json(options.output, value)
        print(error.args[0], file=sys.stderr)
        return 2
    except ProbeFailure as error:
        value = terminal_evidence(options, "fail", error.args[0])
        atomic_write_json(options.output, value)
        print(error.args[0], file=sys.stderr)
        return 2
    except OSError:
        value = terminal_evidence(
            options,
            "blocked",
            "cleanup_incomplete",
            cleanup_status="incomplete",
        )
        atomic_write_json(options.output, value)
        print("cleanup_incomplete", file=sys.stderr)
        return 2
    except ValueError:
        value = terminal_evidence(options, "fail", "inspection_failed")
        atomic_write_json(options.output, value)
        print("inspection_failed", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
