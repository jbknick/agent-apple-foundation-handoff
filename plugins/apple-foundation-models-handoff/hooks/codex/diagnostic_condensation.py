#!/usr/bin/env python3

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
from types import ModuleType
from typing import Callable, Mapping


HOOK_INPUT_KEYS = {
    "session_id",
    "transcript_path",
    "cwd",
    "hook_event_name",
    "model",
    "turn_id",
    "permission_mode",
    "tool_name",
    "tool_input",
    "tool_response",
    "tool_use_id",
}
BRIDGE_INPUT_KEYS = {"diagnosticText", "sourceFacts"}
BRIDGE_OUTPUT_KEYS = {
    "status",
    "reasonCode",
    "appleAvailable",
    "localeSupported",
    "contextSize",
    "occupiedTokens",
    "appleAttempts",
    "condensation",
}
BRIDGE_REASON_CODES = {
    "apple_unavailable",
    "locale_unsupported",
    "context_budget_exceeded",
    "generation_preflight_unavailable",
    "generation_assets_unavailable",
    "generation_unsupported_language_or_locale",
    "generation_rate_limited",
    "generation_concurrent_requests",
    "generation_exceeded_context_window_size",
    "generation_guardrail_violation",
    "generation_unsupported_guide",
    "generation_decoding_failure",
    "generation_refusal",
    "generation_unknown_error",
    "contract_invariant_failed",
}
STATE_VERSION = "runtime-v1-direct-consultation-v1"
TOOL_VERSION = "codex-cli-0.145.0"
APPLICATION_CLASSIFICATION = "C1"
RECORD_KEYS = {
    "case-id",
    "command-class",
    "command-form",
    "classification",
    "exit-status",
    "interrupted",
    "warning-count",
    "command-outcome",
    "summary",
    "summary-facts",
    "next-action",
    "completion-facts",
}
DIAGNOSTIC_KEYS = {
    "id",
    "severity",
    "code",
    "message",
    "file",
    "line",
    "column",
    "failedTestID",
}


def _snapshot(metadata: os.stat_result) -> tuple[int, ...]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        stat.S_IFMT(metadata.st_mode),
        stat.S_IMODE(metadata.st_mode),
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


@dataclass(frozen=True)
class BoundPath:
    path: Path
    snapshot: tuple[int, ...]
    directory: bool
    executable: bool

    @classmethod
    def capture(
        cls,
        path: Path,
        *,
        directory: bool = False,
        executable: bool = False,
    ) -> "BoundPath":
        if not isinstance(path, Path) or not path.is_absolute():
            raise ValueError("path unavailable")
        try:
            resolved = path.resolve(strict=True)
            metadata = path.lstat()
        except OSError:
            raise ValueError("path unavailable") from None
        expected = stat.S_ISDIR if directory else stat.S_ISREG
        if (
            resolved != path
            or not expected(metadata.st_mode)
            or (executable and not os.access(path, os.X_OK))
        ):
            raise ValueError("path unavailable")
        captured = cls(path, _snapshot(metadata), directory, executable)
        captured.recheck()
        return captured

    def recheck(self) -> None:
        try:
            resolved = self.path.resolve(strict=True)
            metadata = self.path.lstat()
        except OSError:
            raise ValueError("path identity drift") from None
        expected = stat.S_ISDIR if self.directory else stat.S_ISREG
        if (
            resolved != self.path
            or _snapshot(metadata) != self.snapshot
            or not expected(metadata.st_mode)
            or (self.executable and not os.access(self.path, os.X_OK))
        ):
            raise ValueError("path identity drift")


def _pairs_without_duplicates(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON key")
        value[key] = item
    return value


def _closed_diagnostic(value: object) -> dict[str, object]:
    if type(value) is not dict or set(value) != DIAGNOSTIC_KEYS:
        raise ValueError("invalid diagnostic")
    if (
        type(value["id"]) is not str
        or not value["id"]
        or value["severity"] not in {"fatal", "error", "warning"}
        or type(value["code"]) is not str
        or not value["code"]
        or type(value["message"]) is not str
        or not value["message"]
        or (
            value["file"] is not None
            and (type(value["file"]) is not str or not value["file"])
        )
        or (
            value["line"] is not None
            and (type(value["line"]) is not int or value["line"] < 1)
        )
        or (
            value["column"] is not None
            and (type(value["column"]) is not int or value["column"] < 1)
        )
        or (
            value["failedTestID"] is not None
            and (
                type(value["failedTestID"]) is not str
                or not value["failedTestID"]
            )
        )
    ):
        raise ValueError("invalid diagnostic")
    return value


def _parse_record(
    text: str,
) -> tuple[dict[str, object], str, int, bool, str]:
    if type(text) is not str:
        raise ValueError("invalid diagnostic text")
    metadata: dict[str, str] = {}
    diagnostics: list[dict[str, object]] = []
    failed_tests: list[str] = []
    for line in text.splitlines():
        key, separator, raw = line.partition(": ")
        if separator and key in RECORD_KEYS:
            if key in metadata or not raw:
                raise ValueError("invalid diagnostic record")
            metadata[key] = raw
        elif separator and key in {"diagnostic", "warning-representative"}:
            try:
                decoded = json.loads(
                    raw,
                    object_pairs_hook=_pairs_without_duplicates,
                )
            except (TypeError, ValueError, json.JSONDecodeError):
                raise ValueError("invalid diagnostic record") from None
            diagnostics.append(_closed_diagnostic(decoded))
        elif separator and key == "failed-test":
            if not raw or raw in failed_tests:
                raise ValueError("invalid diagnostic record")
            failed_tests.append(raw)
        elif line.startswith("synthetic-noise|") or not line:
            continue
    if set(metadata) != RECORD_KEYS:
        raise ValueError("invalid diagnostic record")
    if metadata["command-class"] not in {
        "test",
        "build",
        "typecheck",
        "lint",
    }:
        raise ValueError("invalid command class")
    classification = metadata["classification"]
    if classification not in {"C0", "C1"}:
        raise ValueError("invalid classification")
    try:
        exit_status = int(metadata["exit-status"])
        warning_count = int(metadata["warning-count"])
    except ValueError:
        raise ValueError("invalid diagnostic counters") from None
    if not 0 <= exit_status <= 255 or warning_count < 0:
        raise ValueError("invalid diagnostic counters")
    interrupted = metadata["interrupted"]
    if interrupted != "false":
        raise ValueError("invalid interruption")
    outcome = metadata["command-outcome"]
    expected_outcome = "success" if exit_status == 0 else "failure"
    if outcome != expected_outcome:
        raise ValueError("invalid command outcome")
    summary_facts = metadata["summary-facts"].split("|")
    completion_facts = metadata["completion-facts"].split("|")
    if (
        not summary_facts
        or any(not fact for fact in summary_facts)
        or len(set(summary_facts)) != len(summary_facts)
        or len(completion_facts) != 2
        or len(set(completion_facts)) != 2
        or f"command-class={metadata['command-class']}" not in summary_facts
        or f"outcome={outcome}" not in summary_facts
        or f"warning-count={warning_count}" not in summary_facts
        or "command-finished=true" not in completion_facts
        or (
            f"task-complete={'true' if exit_status == 0 else 'false'}"
            not in completion_facts
        )
    ):
        raise ValueError("invalid diagnostic facts")
    identities = [diagnostic["id"] for diagnostic in diagnostics]
    if len(set(identities)) != len(identities):
        raise ValueError("duplicate diagnostic")
    if any(
        diagnostic["failedTestID"] not in failed_tests
        for diagnostic in diagnostics
        if diagnostic["failedTestID"] is not None
    ):
        raise ValueError("unbound failed test")
    warning_representatives = sum(
        diagnostic["severity"] == "warning" for diagnostic in diagnostics
    )
    if warning_representatives > warning_count:
        raise ValueError("invalid warning accounting")
    facts = {
        "commandOutcome": outcome,
        "summary": metadata["summary"],
        "summaryFacts": summary_facts,
        "diagnostics": diagnostics,
        "warningCount": warning_count,
        "omittedWarningCount": warning_count - warning_representatives,
        "nextAction": metadata["next-action"],
        "completionFacts": completion_facts,
    }
    return (
        facts,
        classification,
        exit_status,
        False,
        metadata["command-form"],
    )


def source_facts(text: str) -> dict[str, object]:
    facts, _, _, _, _ = _parse_record(text)
    return facts


def _selection_command_form(
    contract: ModuleType,
    selection: object,
) -> str:
    tokens = selection.tokens
    for prefix, _, _ in contract._COMMAND_PREFIXES:
        if tuple(tokens[: len(prefix)]) == prefix:
            return " ".join(prefix)
    raise ValueError("command form unavailable")


def _validated_source_facts(
    contract: ModuleType,
    facts: dict[str, object],
) -> dict[str, object]:
    frozen = json.loads(
        json.dumps(
            facts,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ),
        object_pairs_hook=_pairs_without_duplicates,
    )
    contract._validate_source_facts(frozen)
    if not contract._value_is_safe(frozen):
        raise ValueError("source facts denied")
    return frozen


def _bridge_result_is_closed(value: object) -> bool:
    if type(value) is not dict or set(value) != BRIDGE_OUTPUT_KEYS:
        return False
    if (
        value["status"] not in {"applied", "declined", "fail"}
        or type(value["appleAvailable"]) is not bool
        or type(value["localeSupported"]) is not bool
        or type(value["contextSize"]) is not int
        or value["contextSize"] < 1
        or type(value["occupiedTokens"]) is not int
        or value["occupiedTokens"] < 0
        or type(value["appleAttempts"]) is not int
        or value["appleAttempts"] not in {0, 1}
    ):
        return False
    if value["status"] == "applied":
        return (
            value["reasonCode"] is None
            and value["appleAvailable"] is True
            and value["localeSupported"] is True
            and value["appleAttempts"] == 1
            and type(value["condensation"]) is dict
        )
    return (
        type(value["reasonCode"]) is str
        and value["reasonCode"] in BRIDGE_REASON_CODES
        and value["condensation"] is None
    )


def _complete_result(
    request: Mapping[str, object],
    consultation: Mapping[str, object],
) -> dict[str, object]:
    bindings = {
        key: request[key]
        for key in (
            "schemaVersion",
            "policyVersion",
            "callID",
            "toolName",
            "toolVersion",
            "stateVersion",
            "action",
            "commandClass",
            "originalResultType",
            "originalResultDigest",
            "exitStatus",
            "interrupted",
        )
    }
    if consultation["status"] == "applied":
        return {
            **bindings,
            "outcome": "applied",
            "resultType": "diagnostic_condensation",
            "condensation": consultation["condensation"],
        }
    return {
        **bindings,
        "outcome": consultation["status"],
        "reasonCode": consultation["reasonCode"],
    }


def evaluate(
    payload: dict[str, object],
    *,
    contract: ModuleType,
    consult: Callable[[dict[str, object]], Mapping[str, object]],
    repo_root: Path,
    observe: Callable[[Mapping[str, object]], None],
) -> dict[str, object] | None:
    try:
        if type(payload) is not dict or set(payload) != HOOK_INPUT_KEYS:
            return None
        if (
            payload["hook_event_name"] != "PostToolUse"
            or payload["tool_name"] != "Bash"
            or type(payload["tool_input"]) is not dict
            or set(payload["tool_input"]) != {"command"}
            or type(payload["tool_input"]["command"]) is not str
            or type(payload["tool_response"]) is not str
            or type(payload["tool_use_id"]) is not str
            or not payload["tool_use_id"]
            or payload["cwd"] != str(repo_root)
        ):
            return None
        command = payload["tool_input"]["command"]
        selection = contract.parse_command(command, repo_root)
        facts, _, exit_status, interrupted, command_form = _parse_record(
            payload["tool_response"]
        )
        if (
            command_form != _selection_command_form(contract, selection)
            or f"command-class={selection.command_class}"
            not in facts["summaryFacts"]
        ):
            return None
        facts = _validated_source_facts(contract, facts)
        original_bytes = payload["tool_response"].encode("utf-8")
        digest = hashlib.sha256(original_bytes).hexdigest()
        fields = [
            {
                "name": "message",
                "value": payload["tool_response"],
                "origin": "trustedLocal",
                "classification": APPLICATION_CLASSIFICATION,
                "purpose": "diagnostic_condensation",
                "destination": "apple_on_device",
                "retention": "ephemeral",
                "redacted": False,
            }
        ]
        input_bytes = len(contract.canonical_field_bytes(fields))
        request = {
            "schemaVersion": 1,
            "policyVersion": "diagnostic-condensation-v1",
            "callID": payload["tool_use_id"],
            "toolName": "Bash",
            "toolVersion": TOOL_VERSION,
            "stateVersion": STATE_VERSION,
            "action": "condense_diagnostic_output",
            "commandClass": selection.command_class,
            "originalResultType": "string",
            "originalResultDigest": digest,
            "exitStatus": exit_status,
            "interrupted": interrupted,
            "inputBytes": input_bytes,
            "estimatedSavingsBytes": contract.estimate_savings(input_bytes),
            "fields": fields,
        }
        contract.validate_request(request)
        bridge_input = {
            "diagnosticText": payload["tool_response"],
            "sourceFacts": json.loads(
                json.dumps(
                    facts,
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                ),
                object_pairs_hook=_pairs_without_duplicates,
            ),
        }
        if set(bridge_input) != BRIDGE_INPUT_KEYS:
            return None
        consultation = dict(consult(bridge_input))
        if not _bridge_result_is_closed(consultation):
            return None
        frozen_result = _complete_result(request, consultation)
        routed = contract.route(
            request,
            {
                "eventName": "PostToolUse",
                "command": command,
                "repoRoot": repo_root,
                "appleAvailable": consultation["appleAvailable"],
                "localeSupported": consultation["localeSupported"],
                "occupiedTokens": consultation["occupiedTokens"],
                "contextSize": consultation["contextSize"],
                "sourceFacts": facts,
                "bridge": lambda _request: json.loads(
                    json.dumps(frozen_result)
                ),
            },
        )
        if routed.get("outcome") != "applied":
            observe(
                {
                    "event": "consultation_completed",
                    "appleAttempts": consultation["appleAttempts"],
                    "appleValidResults": 0,
                }
            )
            return None
        contract.validate_result(routed)
        stop_reason = json.dumps(
            routed,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        replacement_bytes = len(stop_reason.encode("utf-8"))
        if (
            replacement_bytes > contract.Policy.MAXIMUM_CONDENSED_BYTES
            or input_bytes - replacement_bytes
            < contract.Policy.MINIMUM_REALIZED_SAVINGS_BYTES
        ):
            return None
        observe(
            {
                "event": "consultation_completed",
                "appleAttempts": consultation["appleAttempts"],
                "appleValidResults": 1,
            }
        )
        observe(
            {
                "event": "replacement_emitted",
                "replacementSha256": hashlib.sha256(
                    stop_reason.encode("utf-8")
                ).hexdigest(),
                "replacementBytes": replacement_bytes,
                "appleAttempts": consultation["appleAttempts"],
            }
        )
        return {"continue": False, "stopReason": stop_reason}
    except Exception:
        return None


def run_bridge_process(
    request: dict[str, object],
    *,
    executable: Path,
    timeout_seconds: float,
) -> dict[str, object]:
    if (
        type(request) is not dict
        or set(request) != BRIDGE_INPUT_KEYS
        or type(timeout_seconds) not in {int, float}
        or timeout_seconds <= 0
    ):
        raise ValueError("invalid bridge request")
    captured = BoundPath.capture(executable, executable=True)
    encoded = json.dumps(
        request,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    captured.recheck()
    try:
        completed = subprocess.run(
            [str(captured.path)],
            input=encoded,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            shell=False,
            timeout=timeout_seconds,
        )
    except (OSError, subprocess.TimeoutExpired):
        raise ValueError("bridge unavailable") from None
    finally:
        captured.recheck()
    if (
        completed.returncode != 0
        or completed.stderr
        or not completed.stdout.endswith(b"\n")
        or completed.stdout.count(b"\n") != 1
    ):
        raise ValueError("bridge failed")
    try:
        value = json.loads(
            completed.stdout,
            object_pairs_hook=_pairs_without_duplicates,
        )
    except (UnicodeError, ValueError, json.JSONDecodeError):
        raise ValueError("bridge failed") from None
    if not _bridge_result_is_closed(value):
        raise ValueError("bridge failed")
    return value


def _load_contract(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "runtime_v1_production_contract",
        path,
    )
    if spec is None or spec.loader is None:
        raise ValueError("contract unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    try:
        plugin_root = BoundPath.capture(
            Path(os.environ["PLUGIN_ROOT"]),
            directory=True,
        )
        repo_root = BoundPath.capture(
            Path(os.environ["RUNTIME_V1_REPO_ROOT"]),
            directory=True,
        )
        bridge = BoundPath.capture(
            Path(os.environ["RUNTIME_V1_BRIDGE_EXECUTABLE"]),
            executable=True,
        )
        if Path(__file__).resolve().parents[2] != plugin_root.path:
            return 0
        contract_path = plugin_root.path / "runtime/runtime_contract.py"
        contract_file = BoundPath.capture(contract_path)
        payload = json.load(
            sys.stdin,
            object_pairs_hook=_pairs_without_duplicates,
        )
        response = evaluate(
            payload,
            contract=_load_contract(contract_file.path),
            consult=lambda request: run_bridge_process(
                request,
                executable=bridge.path,
                timeout_seconds=30,
            ),
            repo_root=repo_root.path,
            observe=lambda _value: None,
        )
        plugin_root.recheck()
        repo_root.recheck()
        bridge.recheck()
        contract_file.recheck()
        if response is not None:
            json.dump(
                response,
                sys.stdout,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
            sys.stdout.write("\n")
        return 0
    except Exception:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
