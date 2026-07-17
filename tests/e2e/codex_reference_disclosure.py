from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
REFERENCE_ROOT = (
    ROOT / "plugins" / "apple-foundation-models-handoff" / "references"
)
REFERENCE_ROOT_RELATIVE = REFERENCE_ROOT.relative_to(ROOT).as_posix()
REFERENCE_NAMES = {
    "architecture-and-state.md",
    "orchestration-patterns.md",
    "apple-api-availability.md",
    "security-context-and-recovery.md",
    "evaluation-and-observability.md",
}
VERSION_OUTPUT = "codex-cli 0.144.5"
MODEL = "gpt-5.6-sol"
EVIDENCE_ID = "DEV137-CODEX-REF-001"
CLAIM_BOUNDARY = "optional_explicitly_directed_reference_selection_only"
BLOCKED_COMPLETION = "blocked/production_skills_not_integrated"

CASES = {
    "pattern-final-owner": {
        "expectedReferences": ["orchestration-patterns.md"],
        "expectedResult": "baton_destination_consultation_parent",
        "question": (
            "Classify who owns the final user-facing response in baton-pass "
            "versus isolated consultation."
        ),
        "allowedResults": (
            "baton_destination_consultation_parent",
            "unsupported_or_unclear",
        ),
    },
    "sdk-26-5-transcript": {
        "expectedReferences": ["apple-api-availability.md"],
        "expectedResult": "get_only_interface_verified_sdk_26_5",
        "question": (
            "Classify the installed SDK 26.5 LanguageModelSession transcript "
            "property and its evidence label."
        ),
        "allowedResults": (
            "get_only_interface_verified_sdk_26_5",
            "mutable_or_unverified",
        ),
    },
    "fictional-transfer-baton-api": {
        "expectedReferences": ["apple-api-availability.md"],
        "expectedResult": "unsupported_no_verified_first_class_api",
        "question": (
            "Determine whether transferBaton(to:) is a verified first-class "
            "Apple Foundation Models API. Do not invent or reproduce a signature."
        ),
        "allowedResults": (
            "unsupported_no_verified_first_class_api",
            "verified_first_class_api",
        ),
    },
}


class ProbeFailure(Exception):
    def __init__(self, reason: str, task_id: str | None = None) -> None:
        super().__init__(reason)
        self.reason = reason
        self.task_id = task_id


class ProbeBlocked(Exception):
    def __init__(self, reason: str, attempted_case_count: int = 0) -> None:
        super().__init__(reason)
        self.reason = reason
        self.attempted_case_count = attempted_case_count


def pairs_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def emit_result(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def strict_version(executable: str, environment: dict[str, str]) -> bool:
    try:
        result = subprocess.run(
            [executable, "--version"],
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    if result.returncode != 0 or result.stderr:
        return False
    try:
        output = result.stdout.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return False
    return output == f"{VERSION_OUTPUT}\n" or output == VERSION_OUTPUT


def blocked_payload(reason: str, attempted_case_count: int = 0) -> dict[str, Any]:
    return {
        "attemptedCaseCount": attempted_case_count,
        "claimBoundary": CLAIM_BOUNDARY,
        "completionGate": BLOCKED_COMPLETION,
        "evidenceId": EVIDENCE_ID,
        "host": "codex",
        "hostPath": "<host-path>",
        "hostVersion": "0.144.5" if attempted_case_count else None,
        "model": MODEL,
        "reason": reason,
        "status": "blocked",
        "workflowActivation": "not_claimed",
    }


def failed_payload(failure: ProbeFailure) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "claimBoundary": CLAIM_BOUNDARY,
        "completionGate": BLOCKED_COMPLETION,
        "evidenceId": EVIDENCE_ID,
        "host": "codex",
        "hostPath": "<host-path>",
        "hostVersion": "0.144.5",
        "model": MODEL,
        "reason": failure.reason,
        "status": "fail",
        "workflowActivation": "not_claimed",
    }
    if failure.task_id is not None:
        payload["failedTaskId"] = failure.task_id
    return payload


def build_prompt(task_id: str, case: dict[str, Any]) -> str:
    allowed = ", ".join(case["allowedResults"])
    return (
        "This is an explicitly directed reference-selection prerequisite, not "
        "workflow activation. Inspect the five-file reference library at "
        f"{REFERENCE_ROOT_RELATIVE}/. You may list that directory, then read "
        "exactly the single canonical owner file needed for the question. Do not "
        "grep or search across the directory, and do not read unrelated reference "
        "content. Base the classification only on that owner. "
        f"Task {task_id}: {case['question']} Return exactly one JSON object with "
        f"one key named result and one of these values: {allowed}. Return no prose."
    )


def decode_json_lines(payload: bytes, task_id: str) -> list[dict[str, Any]]:
    try:
        text = payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        raise ProbeFailure("invalid_jsonl", task_id) from None
    events: list[dict[str, Any]] = []
    for line in text.splitlines():
        if not line:
            continue
        try:
            event = json.loads(line, object_pairs_hook=pairs_without_duplicates)
        except (json.JSONDecodeError, ValueError):
            raise ProbeFailure("invalid_jsonl", task_id) from None
        if not isinstance(event, dict):
            raise ProbeFailure("invalid_jsonl", task_id)
        events.append(event)
    if not events:
        raise ProbeFailure("missing_jsonl_events", task_id)
    return events


def nested_strings(value: object) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for nested in value.values():
            yield from nested_strings(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from nested_strings(nested)


def tool_input_strings(event: dict[str, Any]) -> list[str]:
    values: list[object] = []
    item = event.get("item")
    if isinstance(item, dict) and item.get("type") in {
        "command_execution",
        "file_read",
        "function_call",
        "mcp_tool_call",
        "tool_call",
    }:
        for key in (
            "arguments",
            "command",
            "cwd",
            "file_path",
            "input",
            "path",
            "workdir",
        ):
            if key in item:
                values.append(item[key])
    event_type = event.get("type")
    if isinstance(event_type, str) and any(
        marker in event_type for marker in ("command", "file", "function", "tool")
    ):
        for key in (
            "arguments",
            "command",
            "cwd",
            "file_path",
            "input",
            "path",
            "workdir",
        ):
            if key in event:
                values.append(event[key])
    return [text for value in values for text in nested_strings(value)]


def is_directory_discovery(value: str) -> bool:
    lower = value.lower()
    if "*.md" in lower or "-exec" in lower or "xargs" in lower:
        return False
    if re.search(r"\b(?:cat|sed|awk|head|tail|less|more|grep|perl|python|ruby)\b", lower):
        return False
    if re.search(r"\brg\b", lower) and "--files" not in lower:
        return False
    return bool(re.search(r"\b(?:ls|find|fd|rg\s+--files)\b", lower))


def observed_reference_reads(
    events: list[dict[str, Any]], task_id: str
) -> set[str]:
    observed: set[str] = set()
    absolute_root = str(REFERENCE_ROOT)
    for event in events:
        inputs = tool_input_strings(event)
        if not inputs:
            continue
        combined = "\n".join(inputs)
        mentions_root = (
            REFERENCE_ROOT_RELATIVE in combined or absolute_root in combined
        )
        mentioned_names = {
            name for name in REFERENCE_NAMES if name in combined
        }
        if mentioned_names and not mentions_root:
            raise ProbeFailure("reference_path_outside_package", task_id)
        if mentions_root and not mentioned_names and not is_directory_discovery(combined):
            raise ProbeFailure("bulk_reference_content_read", task_id)
        observed.update(mentioned_names)
    return observed


def agent_messages(events: list[dict[str, Any]]) -> list[str]:
    messages: list[str] = []
    for event in events:
        item = event.get("item")
        if (
            isinstance(item, dict)
            and item.get("type") == "agent_message"
            and isinstance(item.get("text"), str)
        ):
            messages.append(item["text"])
        if (
            event.get("type") == "agent_message"
            and isinstance(event.get("text"), str)
        ):
            messages.append(event["text"])
    return messages


def parse_bounded_result(events: list[dict[str, Any]], task_id: str) -> tuple[str, str]:
    messages = agent_messages(events)
    if not messages:
        raise ProbeFailure("missing_bounded_result", task_id)
    response = messages[-1].strip()
    if task_id == "fictional-transfer-baton-api" and re.search(
        r"\b(?:func\s+)?transferBaton\s*\(", response
    ):
        raise ProbeFailure("invented_fictional_api_signature", task_id)
    if response.startswith("```json\n") and response.endswith("\n```"):
        response = response[8:-4].strip()
    try:
        parsed = json.loads(response, object_pairs_hook=pairs_without_duplicates)
    except (json.JSONDecodeError, ValueError):
        raise ProbeFailure("malformed_bounded_result", task_id) from None
    if not isinstance(parsed, dict) or set(parsed) != {"result"}:
        raise ProbeFailure("malformed_bounded_result", task_id)
    result = parsed.get("result")
    if not isinstance(result, str):
        raise ProbeFailure("malformed_bounded_result", task_id)
    return result, response


def execution_is_unavailable(stdout: bytes, stderr: bytes) -> bool:
    diagnostic = (stdout[-8192:] + stderr[-8192:]).decode(
        "utf-8", errors="replace"
    ).lower()
    return any(
        marker in diagnostic
        for marker in (
            "authentication",
            "authorization",
            "connection",
            "credentials",
            "forbidden",
            "login",
            "model",
            "network",
            "quota",
            "rate limit",
            "timed out",
            "unauthorized",
            "unavailable",
        )
    )


def run_case(
    executable: str,
    environment: dict[str, str],
    task_id: str,
    case: dict[str, Any],
) -> dict[str, Any]:
    prompt = build_prompt(task_id, case)
    try:
        completed = subprocess.run(
            [
                executable,
                "exec",
                "--ephemeral",
                "--json",
                "-C",
                str(ROOT),
                "-m",
                MODEL,
                "-s",
                "read-only",
                prompt,
            ],
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=240,
        )
    except subprocess.TimeoutExpired:
        raise ProbeBlocked("model_auth_or_task_execution_unavailable", 1) from None
    except OSError:
        raise ProbeBlocked("model_auth_or_task_execution_unavailable", 1) from None
    if completed.returncode != 0:
        if execution_is_unavailable(completed.stdout, completed.stderr):
            raise ProbeBlocked("model_auth_or_task_execution_unavailable", 1)
        raise ProbeFailure("task_execution_failed", task_id)

    events = decode_json_lines(completed.stdout, task_id)
    observed = observed_reference_reads(events, task_id)
    expected = set(case["expectedReferences"])
    if observed != expected:
        raise ProbeFailure("reference_selection_mismatch", task_id)

    result, bounded_response = parse_bounded_result(events, task_id)
    if result != case["expectedResult"]:
        raise ProbeFailure("semantic_result_mismatch", task_id)
    return {
        "expectedReferences": sorted(expected),
        "observedReferences": sorted(observed),
        "resultClassification": result,
        "resultSha256": sha256_text(bounded_response),
        "taskId": task_id,
        "taskSha256": sha256_text(prompt),
    }


def capture_host() -> tuple[str, Path, Path, dict[str, str]]:
    host = shutil.which("codex")
    if host is None:
        raise ProbeBlocked("missing_binary_or_version_mismatch")
    locator = Path(host)
    try:
        initial_resolution = locator.resolve(strict=True)
        metadata = initial_resolution.stat()
    except OSError:
        raise ProbeBlocked("missing_binary_or_version_mismatch") from None
    if not stat.S_ISREG(metadata.st_mode) or not os.access(locator, os.X_OK):
        raise ProbeBlocked("missing_binary_or_version_mismatch")
    environment = os.environ.copy()
    executable = str(initial_resolution)
    if not strict_version(executable, environment):
        raise ProbeBlocked("missing_binary_or_version_mismatch")
    return executable, locator, initial_resolution, environment


def require_unchanged_host(
    executable: str,
    locator: Path,
    initial_resolution: Path,
    environment: dict[str, str],
) -> None:
    try:
        final_resolution = locator.resolve(strict=True)
        metadata = final_resolution.stat()
    except OSError:
        raise ProbeFailure("host_resolution_or_version_drift") from None
    if (
        final_resolution != initial_resolution
        or not stat.S_ISREG(metadata.st_mode)
        or not os.access(locator, os.X_OK)
        or not strict_version(executable, environment)
    ):
        raise ProbeFailure("host_resolution_or_version_drift")


def main() -> int:
    try:
        executable, locator, initial_resolution, environment = capture_host()
    except ProbeBlocked as failure:
        emit_result(blocked_payload(failure.reason, failure.attempted_case_count))
        return 2

    case_results: list[dict[str, Any]] = []
    try:
        for task_id, case in CASES.items():
            case_results.append(run_case(executable, environment, task_id, case))
            require_unchanged_host(
                executable,
                locator,
                initial_resolution,
                environment,
            )
    except ProbeBlocked as failure:
        attempted = len(case_results) + failure.attempted_case_count
        emit_result(blocked_payload(failure.reason, attempted))
        return 2
    except ProbeFailure as failure:
        emit_result(failed_payload(failure))
        return 1
    except Exception:
        emit_result(failed_payload(ProbeFailure("unexpected_probe_failure")))
        return 1

    emit_result(
        {
            "caseCount": len(CASES),
            "cases": case_results,
            "claimBoundary": CLAIM_BOUNDARY,
            "completionGate": BLOCKED_COMPLETION,
            "evidenceId": EVIDENCE_ID,
            "host": "codex",
            "hostPath": "<host-path>",
            "hostVersion": "0.144.5",
            "model": MODEL,
            "passedCaseCount": len(case_results),
            "referenceReadCount": sum(
                len(case["observedReferences"]) for case in case_results
            ),
            "status": "pass",
            "workflowActivation": "not_claimed",
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
