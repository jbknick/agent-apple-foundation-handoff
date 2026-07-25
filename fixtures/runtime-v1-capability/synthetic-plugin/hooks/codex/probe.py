#!/usr/bin/env python3

import copy
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Mapping


HOOK_INPUT_KEYS = (
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
)
CONSULTATION_KEYS = (
    "status",
    "reasonCode",
    "appleAvailable",
    "localeSupported",
    "contextSize",
    "occupiedTokens",
    "appleAttempts",
    "condensation",
)
STATE_VERSION = "runtime-v1-direct-consultation-v1"
TOOL_VERSION = "codex-cli-0.145.0"
APPROVED_COMMAND = "python3 -m unittest -q diagnostic_fixture"
APPROVED_CALL_ID = "call-runtime-v1"


def source_facts(exit_status: int) -> dict[str, Any]:
    outcome = "success" if exit_status == 0 else "failure"
    return {
        "commandOutcome": outcome,
        "summary": f"synthetic unittest {outcome}",
        "summaryFacts": [
            "command-class=test",
            f"outcome={outcome}",
            f"exit-status={exit_status}",
            "warning-count=0",
        ],
        "diagnostics": [],
        "warningCount": 0,
        "omittedWarningCount": 0,
        "nextAction": (
            "continue after successful synthetic unittest"
            if exit_status == 0
            else "inspect the synthetic unittest failure"
        ),
        "completionFacts": [
            "command-finished=true",
            f"task-complete={'true' if exit_status == 0 else 'false'}",
        ],
    }


def complete_result(
    request: Mapping[str, Any],
    consultation: Mapping[str, Any],
) -> dict[str, Any]:
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
    payload: Mapping[str, Any],
    *,
    contract: ModuleType,
    consult: Callable[[dict[str, Any]], Mapping[str, Any]],
    repo_root: Path,
    approved_stimulus_sha256: str,
    observe: Callable[[Mapping[str, Any]], None],
) -> dict[str, Any] | None:
    try:
        if type(payload) is not dict or set(payload) != set(HOOK_INPUT_KEYS):
            return None
        if (
            payload["hook_event_name"] != "PostToolUse"
            or payload["tool_name"] != "Bash"
            or type(payload["tool_response"]) is not str
            or type(payload["tool_input"]) is not dict
            or set(payload["tool_input"]) != {"command"}
            or type(payload["tool_input"]["command"]) is not str
            or payload["tool_input"]["command"] != APPROVED_COMMAND
            or payload["tool_use_id"] != APPROVED_CALL_ID
            or payload["cwd"] != str(repo_root)
        ):
            return None

        observe(
            {
                "event": "hook_invoked",
                "callID": payload["tool_use_id"],
                "hookInvocations": 1,
            }
        )
        exit_status = 0
        original_bytes = payload["tool_response"].encode("utf-8")
        original_sha256 = hashlib.sha256(original_bytes).hexdigest()
        observe(
            {
                "event": "original_observed",
                "callID": payload["tool_use_id"],
                "originalSha256": original_sha256,
            }
        )
        if (
            not re.fullmatch(r"[0-9a-f]{64}", approved_stimulus_sha256)
            or original_sha256 != approved_stimulus_sha256
        ):
            return None

        fields = [
            {
                "name": "message",
                "value": payload["tool_response"],
                "origin": "trustedLocal",
                "classification": "C0",
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
            "commandClass": "test",
            "originalResultType": "string",
            "originalResultDigest": original_sha256,
            "exitStatus": exit_status,
            "interrupted": False,
            "inputBytes": input_bytes,
            "estimatedSavingsBytes": contract.estimate_savings(input_bytes),
            "fields": fields,
        }
        contract.validate_request(request)
        contract.parse_command(payload["tool_input"]["command"], repo_root)

        expected = source_facts(exit_status)
        consultation = dict(consult(copy.deepcopy(request)))
        if set(consultation) != set(CONSULTATION_KEYS):
            return None
        if (
            consultation["status"] not in {"applied", "declined", "fail"}
            or type(consultation["appleAvailable"]) is not bool
            or type(consultation["localeSupported"]) is not bool
            or type(consultation["contextSize"]) is not int
            or consultation["contextSize"] < 1
            or type(consultation["occupiedTokens"]) is not int
            or consultation["occupiedTokens"] < 0
            or consultation["appleAttempts"] not in {0, 1}
        ):
            return None
        if consultation["status"] == "applied":
            if (
                consultation["reasonCode"] is not None
                or consultation["appleAvailable"] is not True
                or consultation["localeSupported"] is not True
                or consultation["appleAttempts"] != 1
            ):
                return None
        elif type(consultation["reasonCode"]) is not str:
            return None
        observe(
            {
                "event": "consultation_completed",
                "callID": payload["tool_use_id"],
                "appleAttempts": consultation["appleAttempts"],
                "appleValidResults": int(
                    consultation["status"] == "applied"
                ),
            }
        )

        frozen_result = complete_result(request, consultation)
        routed = contract.route(
            request,
            {
                "eventName": "PostToolUse",
                "command": payload["tool_input"]["command"],
                "repoRoot": repo_root,
                "appleAvailable": consultation["appleAvailable"],
                "localeSupported": consultation["localeSupported"],
                "occupiedTokens": consultation["occupiedTokens"],
                "contextSize": consultation["contextSize"],
                "sourceFacts": expected,
                "bridge": lambda _: copy.deepcopy(frozen_result),
            },
        )
        if routed.get("outcome") != "applied":
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
                "event": "replacement_emitted",
                "callID": payload["tool_use_id"],
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
    request: Mapping[str, Any],
    *,
    executable: Path,
    timeout_seconds: float,
) -> Mapping[str, Any]:
    encoded = json.dumps(
        {"diagnosticText": request["fields"][0]["value"]},
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    completed = subprocess.run(
        [str(executable)],
        input=encoded,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        shell=False,
        timeout=timeout_seconds,
    )
    if (
        completed.returncode != 0
        or completed.stderr != b""
        or not completed.stdout.endswith(b"\n")
        or completed.stdout.count(b"\n") != 1
    ):
        raise OSError("bridge_process_failed")
    decoded = json.loads(completed.stdout)
    if type(decoded) is not dict:
        raise ValueError("bridge_output_invalid")
    return decoded


def load_contract(repo_root: Path) -> ModuleType:
    path = repo_root / "fixtures/dev-142/runtime_contract.py"
    spec = importlib.util.spec_from_file_location(
        "runtime_v1_dev142_contract",
        path,
    )
    if spec is None or spec.loader is None:
        raise OSError("contract_unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def append_observation(path: Path, value: Mapping[str, Any]) -> None:
    encoded = (
        json.dumps(value, ensure_ascii=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    descriptor = os.open(
        path,
        os.O_APPEND | os.O_CREAT | os.O_WRONLY,
        0o600,
    )
    try:
        os.write(descriptor, encoded)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        if type(payload) is not dict:
            return 0
        repository_root = Path(os.environ["RUNTIME_V1_REPO_ROOT"])
        approved_workspace = Path(
            os.environ["RUNTIME_V1_APPROVED_WORKSPACE"]
        )
        approved_stimulus_sha256 = os.environ[
            "RUNTIME_V1_APPROVED_STIMULUS_SHA256"
        ]
        observation_path = Path(
            os.environ["RUNTIME_V1_OBSERVATION_PATH"]
        )
        bridge_executable = Path(
            os.environ["RUNTIME_V1_BRIDGE_EXECUTABLE"]
        )
        fault_mode = os.environ.get("RUNTIME_V1_FAULT_MODE", "none")
        if fault_mode not in {"none", "adapter_crash", "hook_timeout"}:
            return 0

        def observe(value: Mapping[str, Any]) -> None:
            append_observation(observation_path, value)
            if value["event"] != "original_observed":
                return
            if fault_mode == "adapter_crash":
                os._exit(70)
            if fault_mode == "hook_timeout":
                time.sleep(61)

        contract = load_contract(repository_root)
        response = evaluate(
            payload,
            contract=contract,
            consult=lambda request: run_bridge_process(
                request,
                executable=bridge_executable,
                timeout_seconds=30,
            ),
            repo_root=approved_workspace,
            approved_stimulus_sha256=approved_stimulus_sha256,
            observe=observe,
        )
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
