from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import stat
import subprocess
from typing import Any, Iterable
import unittest
from unittest.mock import patch


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
TOOL_ITEM_TYPES = {
    "command_execution",
    "file_read",
    "function_call",
    "mcp_tool_call",
    "tool_call",
}
TOOL_INPUT_KEYS = {
    "arguments",
    "command",
    "cwd",
    "file_path",
    "input",
    "path",
    "workdir",
}
DISCOVERY_COMMANDS = {"fd", "find", "ls"}
CONTENT_COMMANDS = {
    "awk",
    "cat",
    "cut",
    "grep",
    "head",
    "less",
    "more",
    "perl",
    "python",
    "python3",
    "rg",
    "ruby",
    "sed",
    "tail",
    "wc",
}
BLOCKER_ERROR_CODES = {
    "authentication_required",
    "invalid_api_key",
    "model_not_found",
    "model_unavailable",
    "network_error",
    "not_authenticated",
    "rate_limit_exceeded",
    "request_timeout",
    "service_unavailable",
}
BLOCKER_DIAGNOSTIC_PATTERNS = (
    re.compile(r"\b401 Unauthorized\b", re.IGNORECASE),
    re.compile(r"\b403 Forbidden\b", re.IGNORECASE),
    re.compile(r"\b408 Request Timeout\b", re.IGNORECASE),
    re.compile(r"\b429 Too Many Requests\b", re.IGNORECASE),
    re.compile(r"\b502 Bad Gateway\b", re.IGNORECASE),
    re.compile(r"\b503 Service Unavailable\b", re.IGNORECASE),
    re.compile(r"\b504 Gateway Timeout\b", re.IGNORECASE),
    re.compile(r"\berror sending request for url\b", re.IGNORECASE),
    re.compile(r"\bnot logged in\b", re.IGNORECASE),
    re.compile(r"\brequest timed out\b", re.IGNORECASE),
    re.compile(
        r"\bmodel\s+['\"][^'\"]+['\"]\s+(?:does not exist|is not available)\b",
        re.IGNORECASE,
    ),
)
FICTIONAL_SIGNATURE_PATTERNS = (
    re.compile(r"\b(?:func|case)\s+transferBaton\s*\(", re.IGNORECASE),
    re.compile(r"\btransferBaton\s*\(\s*to\s*:", re.IGNORECASE),
    re.compile(
        r"\b(?:public\s+|private\s+|internal\s+|static\s+|class\s+)*"
        r"(?:func|struct|class|enum|protocol)\s+[A-Za-z_]\w*",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*(?:public\s+|private\s+|internal\s+|static\s+)*"
        r"case\s+[A-Za-z_]\w*\s*(?:\(|=)",
        re.IGNORECASE | re.MULTILINE,
    ),
)

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


def tool_input_signature(item: dict[str, Any]) -> str:
    inputs = {key: item[key] for key in TOOL_INPUT_KEYS if key in item}
    try:
        return json.dumps(inputs, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    except (TypeError, ValueError):
        raise ProbeFailure("invalid_tool_event") from None


def paired_successful_tool_items(
    events: list[dict[str, Any]], task_id: str
) -> list[dict[str, Any]]:
    started: dict[str, tuple[str, str]] = {}
    completed: list[dict[str, Any]] = []
    for event in events:
        item = event.get("item")
        if not isinstance(item, dict) or item.get("type") not in TOOL_ITEM_TYPES:
            continue
        event_type = event.get("type")
        if event_type not in {"item.started", "item.completed"}:
            continue
        identifier = item.get("id")
        item_type = item.get("type")
        if not isinstance(identifier, str) or not identifier:
            raise ProbeFailure("unpaired_command_event", task_id)
        signature = tool_input_signature(item)
        if event_type == "item.started":
            if identifier in started:
                raise ProbeFailure("unpaired_command_event", task_id)
            started[identifier] = (str(item_type), signature)
            continue

        start = started.pop(identifier, None)
        if start is None or start != (str(item_type), signature):
            raise ProbeFailure("unpaired_command_event", task_id)
        if item_type == "command_execution":
            if item.get("status") != "completed" or item.get("exit_code") != 0:
                raise ProbeFailure("command_execution_failed", task_id)
        elif item.get("status") not in {"completed", "success"}:
            raise ProbeFailure("tool_execution_failed", task_id)
        elif "exit_code" in item and item.get("exit_code") != 0:
            raise ProbeFailure("tool_execution_failed", task_id)
        completed.append(item)
    if started:
        raise ProbeFailure("unpaired_command_event", task_id)
    return completed


def shell_tokens(command: str, task_id: str) -> list[str]:
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|")
        lexer.whitespace_split = True
        lexer.commenters = ""
        tokens = list(lexer)
    except ValueError:
        raise ProbeFailure("unparseable_reference_command", task_id) from None
    if not tokens:
        return []
    executable = Path(tokens[0]).name
    if executable in {"bash", "sh", "zsh"}:
        command_options = tokens[1:-1]
        if any(option.startswith("-") and "c" in option for option in command_options):
            return shell_tokens(tokens[-1], task_id)
    return tokens


def shell_segments(tokens: list[str]) -> list[list[str]]:
    segments: list[list[str]] = []
    current: list[str] = []
    for token in tokens:
        if token in {"&&", "||", ";", "|"}:
            if current:
                segments.append(current)
                current = []
            continue
        current.append(token)
    if current:
        segments.append(current)
    return segments


def is_reference_path_token(token: str) -> bool:
    stripped = token.strip("\"'(){}<>,")
    if not stripped:
        return False
    return (
        REFERENCE_ROOT_RELATIVE in stripped
        or str(REFERENCE_ROOT) in stripped
        or Path(stripped).name in REFERENCE_NAMES
    )


def resolve_candidate_path(token: str, base: Path, task_id: str) -> Path:
    stripped = token.strip("\"'(){}<>,")
    if any(character in stripped for character in "*?["):
        raise ProbeFailure("bulk_reference_content_read", task_id)
    candidate = Path(stripped)
    try:
        return (candidate if candidate.is_absolute() else base / candidate).resolve(
            strict=False
        )
    except (OSError, RuntimeError, ValueError):
        raise ProbeFailure("reference_path_outside_package", task_id) from None


def validate_reference_candidate(
    token: str,
    base: Path,
    task_id: str,
    *,
    directory_discovery: bool,
    bulk_directory_read: bool = False,
) -> str | None:
    resolved = resolve_candidate_path(token, base, task_id)
    canonical_root = REFERENCE_ROOT.resolve(strict=True)
    if resolved == canonical_root:
        if directory_discovery:
            return None
        raise ProbeFailure(
            "bulk_reference_content_read"
            if bulk_directory_read
            else "reference_directory_read",
            task_id,
        )
    try:
        relative = resolved.relative_to(canonical_root)
    except ValueError:
        raise ProbeFailure("reference_path_outside_package", task_id) from None
    if len(relative.parts) != 1 or relative.name not in REFERENCE_NAMES:
        raise ProbeFailure("unrelated_reference_read", task_id)
    try:
        metadata = resolved.lstat()
    except OSError:
        raise ProbeFailure("reference_path_invalid", task_id) from None
    if not stat.S_ISREG(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
        raise ProbeFailure("reference_path_invalid", task_id)
    return relative.name if not directory_discovery else None


def command_reference_reads(command: str, task_id: str) -> set[str]:
    observed: set[str] = set()
    current_directory = ROOT.resolve(strict=True)
    for segment in shell_segments(shell_tokens(command, task_id)):
        if not segment:
            continue
        executable = Path(segment[0]).name
        arguments = segment[1:]
        if executable == "cd":
            if len(arguments) != 1:
                raise ProbeFailure("unparseable_reference_command", task_id)
            current_directory = resolve_candidate_path(
                arguments[0], current_directory, task_id
            )
            continue
        path_tokens = [token for token in arguments if is_reference_path_token(token)]
        if not path_tokens:
            continue
        is_rg_discovery = executable == "rg" and "--files" in arguments
        directory_discovery = executable in DISCOVERY_COMMANDS or is_rg_discovery
        if directory_discovery:
            if any(
                marker in arguments
                for marker in ("-exec", "-execdir", "-delete")
            ):
                raise ProbeFailure("bulk_reference_content_read", task_id)
        elif executable not in CONTENT_COMMANDS:
            raise ProbeFailure("ambiguous_reference_read", task_id)
        for token in path_tokens:
            name = validate_reference_candidate(
                token,
                current_directory,
                task_id,
                directory_discovery=directory_discovery,
                bulk_directory_read=executable in {"grep", "rg"},
            )
            if name is not None:
                observed.add(name)
    return observed


def mapping_reference_reads(
    value: object,
    base: Path,
    task_id: str,
) -> set[str]:
    observed: set[str] = set()
    if isinstance(value, str):
        stripped = value.lstrip()
        if stripped.startswith(("{", "[")):
            try:
                decoded = json.loads(
                    value,
                    object_pairs_hook=pairs_without_duplicates,
                )
            except (json.JSONDecodeError, DuplicateKeyError):
                if is_reference_path_token(value):
                    raise ProbeFailure("invalid_tool_event", task_id) from None
                return observed
            if isinstance(decoded, (dict, list)):
                observed.update(mapping_reference_reads(decoded, base, task_id))
            return observed
        if is_reference_path_token(value):
            if not any(character.isspace() for character in value) and not any(
                operator in value for operator in ("|", ";", "&", ">", "<")
            ):
                name = validate_reference_candidate(
                    value,
                    base,
                    task_id,
                    directory_discovery=False,
                )
                if name is not None:
                    observed.add(name)
            else:
                observed.update(command_reference_reads(value, task_id))
        return observed
    if isinstance(value, list):
        for nested in value:
            observed.update(mapping_reference_reads(nested, base, task_id))
        return observed
    if not isinstance(value, dict):
        return observed
    local_base = base
    for key in ("cwd", "workdir"):
        candidate = value.get(key)
        if isinstance(candidate, str):
            local_base = resolve_candidate_path(candidate, base, task_id)
    for key, nested in value.items():
        if key in {"cwd", "workdir"}:
            continue
        if key in {"path", "file_path"} and isinstance(nested, str):
            name = validate_reference_candidate(
                nested,
                local_base,
                task_id,
                directory_discovery=False,
            )
            if name is not None:
                observed.add(name)
        elif key == "command" and isinstance(nested, str):
            observed.update(command_reference_reads(nested, task_id))
        else:
            observed.update(mapping_reference_reads(nested, local_base, task_id))
    return observed


def observed_reference_reads(
    events: list[dict[str, Any]], task_id: str
) -> set[str]:
    observed: set[str] = set()
    for item in paired_successful_tool_items(events, task_id):
        if item.get("type") == "command_execution":
            command = item.get("command")
            if not isinstance(command, str):
                raise ProbeFailure("invalid_tool_event", task_id)
            observed.update(command_reference_reads(command, task_id))
        else:
            inputs = {key: item[key] for key in TOOL_INPUT_KEYS if key in item}
            observed.update(mapping_reference_reads(inputs, ROOT, task_id))
    return observed


def agent_messages(events: list[dict[str, Any]]) -> list[str]:
    messages: list[str] = []

    def visit(value: object) -> None:
        if isinstance(value, dict):
            if value.get("type") == "agent_message" and isinstance(
                value.get("text"), str
            ):
                messages.append(value["text"])
            for nested in value.values():
                visit(nested)
        elif isinstance(value, list):
            for nested in value:
                visit(nested)

    for event in events:
        visit(event)
    return messages


def parse_bounded_result(events: list[dict[str, Any]], task_id: str) -> tuple[str, str]:
    messages = agent_messages(events)
    if not messages:
        raise ProbeFailure("missing_bounded_result", task_id)
    if task_id == "fictional-transfer-baton-api":
        for message in messages:
            if any(pattern.search(message) for pattern in FICTIONAL_SIGNATURE_PATTERNS):
                raise ProbeFailure("invented_fictional_api_signature", task_id)
    response = messages[-1].strip()
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


def diagnostic_codes(value: object) -> set[str]:
    codes: set[str] = set()
    if isinstance(value, dict):
        for key, nested in value.items():
            if key == "code" and isinstance(nested, str):
                codes.add(nested.lower())
            else:
                codes.update(diagnostic_codes(nested))
    elif isinstance(value, list):
        for nested in value:
            codes.update(diagnostic_codes(nested))
    return codes


def execution_is_unavailable(stdout: bytes, stderr: bytes) -> bool:
    payload = stdout[-8192:] + b"\n" + stderr[-8192:]
    diagnostic = payload.decode("utf-8", errors="replace")
    codes: set[str] = set()
    for line in diagnostic.splitlines():
        try:
            parsed = json.loads(line, object_pairs_hook=pairs_without_duplicates)
        except (json.JSONDecodeError, ValueError):
            continue
        codes.update(diagnostic_codes(parsed))
    if codes & BLOCKER_ERROR_CODES:
        return True
    return any(pattern.search(diagnostic) for pattern in BLOCKER_DIAGNOSTIC_PATTERNS)


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
        raise ProbeFailure("task_execution_failed", task_id) from None
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
    terminal_status = 1
    terminal_payload: dict[str, Any]
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
        terminal_status = 2
        terminal_payload = blocked_payload(failure.reason, attempted)
    except ProbeFailure as failure:
        terminal_payload = failed_payload(failure)
    except Exception:
        terminal_payload = failed_payload(ProbeFailure("unexpected_probe_failure"))
    else:
        terminal_status = 0
        terminal_payload = {
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
    finally:
        try:
            require_unchanged_host(
                executable,
                locator,
                initial_resolution,
                environment,
            )
        except Exception:
            terminal_status = 1
            terminal_payload = failed_payload(
                ProbeFailure("host_resolution_or_version_drift")
            )
    emit_result(terminal_payload)
    return terminal_status


class DirectedReferenceProbeTests(unittest.TestCase):
    def command_events(
        self,
        command: str,
        *,
        identifier: str = "command-1",
        completion_status: str = "completed",
        exit_code: int = 0,
    ) -> list[dict[str, Any]]:
        return [
            {
                "type": "item.started",
                "item": {
                    "command": command,
                    "id": identifier,
                    "status": "in_progress",
                    "type": "command_execution",
                },
            },
            {
                "type": "item.completed",
                "item": {
                    "command": command,
                    "exit_code": exit_code,
                    "id": identifier,
                    "status": completion_status,
                    "type": "command_execution",
                },
            },
        ]

    def tool_events(
        self,
        item_type: str,
        inputs: dict[str, Any],
        *,
        identifier: str = "tool-1",
        completion_status: str = "completed",
    ) -> list[dict[str, Any]]:
        common = {"id": identifier, "type": item_type, **inputs}
        return [
            {
                "type": "item.started",
                "item": {**common, "status": "in_progress"},
            },
            {
                "type": "item.completed",
                "item": {**common, "status": completion_status},
            },
        ]

    def assert_probe_failure(
        self,
        events: list[dict[str, Any]],
        expected_reason: str,
    ) -> None:
        with self.assertRaises(ProbeFailure) as raised:
            observed_reference_reads(events, "synthetic-case")
        self.assertEqual(expected_reason, raised.exception.reason)

    def test_successful_paired_relative_owner_read_is_accepted(self):
        owner = f"{REFERENCE_ROOT_RELATIVE}/apple-api-availability.md"
        events = self.command_events(f"sed -n '1,40p' {owner}")
        self.assertEqual(
            {"apple-api-availability.md"},
            observed_reference_reads(events, "synthetic-case"),
        )

    def test_json_string_tool_arguments_resolve_one_exact_owner(self):
        arguments = json.dumps(
            {"path": f"{REFERENCE_ROOT_RELATIVE}/apple-api-availability.md"}
        )
        events = self.tool_events("mcp_tool_call", {"arguments": arguments})
        self.assertEqual(
            {"apple-api-availability.md"},
            observed_reference_reads(events, "synthetic-case"),
        )

    def test_failed_file_event_is_rejected(self):
        events = self.tool_events(
            "file_read",
            {"path": f"{REFERENCE_ROOT_RELATIVE}/apple-api-availability.md"},
            completion_status="failed",
        )
        self.assert_probe_failure(events, "tool_execution_failed")

    def test_started_without_completion_is_rejected(self):
        owner = f"{REFERENCE_ROOT_RELATIVE}/apple-api-availability.md"
        events = self.command_events(f"sed -n '1,40p' {owner}")[:1]
        self.assert_probe_failure(events, "unpaired_command_event")

    def test_completion_without_started_pair_is_rejected(self):
        owner = f"{REFERENCE_ROOT_RELATIVE}/apple-api-availability.md"
        events = self.command_events(f"sed -n '1,40p' {owner}")[1:]
        self.assert_probe_failure(events, "unpaired_command_event")

    def test_failed_command_cannot_be_counted_as_a_read(self):
        owner = f"{REFERENCE_ROOT_RELATIVE}/apple-api-availability.md"
        events = self.command_events(
            f"sed -n '1,40p' {owner}",
            completion_status="failed",
            exit_code=1,
        )
        self.assert_probe_failure(events, "command_execution_failed")

    def test_sibling_prefix_path_is_rejected(self):
        outside = f"{REFERENCE_ROOT_RELATIVE}-evil/apple-api-availability.md"
        self.assert_probe_failure(
            self.command_events(f"cat {outside}"),
            "reference_path_outside_package",
        )

    def test_same_basename_outside_root_is_not_paired_with_root_substring(self):
        command = (
            f"cd {REFERENCE_ROOT_RELATIVE} && "
            "cat /tmp/apple-api-availability.md"
        )
        self.assert_probe_failure(
            self.command_events(command),
            "reference_path_outside_package",
        )

    def test_parent_escape_is_rejected_after_path_resolution(self):
        escaped = (
            f"{REFERENCE_ROOT_RELATIVE}/../references-evil/"
            "apple-api-availability.md"
        )
        self.assert_probe_failure(
            self.command_events(f"cat {escaped}"),
            "reference_path_outside_package",
        )

    def test_reference_directory_content_read_is_rejected(self):
        self.assert_probe_failure(
            self.command_events(f"cat {REFERENCE_ROOT_RELATIVE}"),
            "reference_directory_read",
        )

    def test_reference_glob_is_rejected_as_bulk_read(self):
        self.assert_probe_failure(
            self.command_events(f"cat {REFERENCE_ROOT_RELATIVE}/*.md"),
            "bulk_reference_content_read",
        )

    def test_unrelated_reference_read_is_rejected(self):
        command = (
            f"cat {REFERENCE_ROOT_RELATIVE}/apple-api-availability.md "
            f"{REFERENCE_ROOT_RELATIVE}/architecture-and-state.md"
        )
        with self.assertRaises(ProbeFailure) as raised:
            observed = observed_reference_reads(
                self.command_events(command), "synthetic-case"
            )
            if observed != {"apple-api-availability.md"}:
                raise ProbeFailure("reference_selection_mismatch", "synthetic-case")
        self.assertEqual("reference_selection_mismatch", raised.exception.reason)

    def test_successful_directory_listing_is_discovery_not_content_read(self):
        events = self.command_events(f"ls {REFERENCE_ROOT_RELATIVE}")
        self.assertEqual(set(), observed_reference_reads(events, "synthetic-case"))

    def test_generic_model_word_does_not_create_a_blocker(self):
        self.assertFalse(
            execution_is_unavailable(b"model crashed for an unknown reason", b"")
        )

    def test_generic_connection_word_does_not_create_a_blocker(self):
        self.assertFalse(
            execution_is_unavailable(b"connection invariant failed internally", b"")
        )

    def test_generic_unavailable_word_does_not_create_a_blocker(self):
        self.assertFalse(
            execution_is_unavailable(b"local module unavailable after assertion", b"")
        )

    def test_closed_auth_and_model_codes_are_blockers(self):
        for diagnostic in (
            b'{"error":{"code":"authentication_required"}}',
            b'{"error":{"code":"model_not_found"}}',
            b"Error: 401 Unauthorized",
            b"Error: 403 Forbidden",
        ):
            with self.subTest(diagnostic=diagnostic):
                self.assertTrue(execution_is_unavailable(b"", diagnostic))

    def test_closed_transport_and_service_codes_are_blockers(self):
        for diagnostic in (
            b'{"error":{"code":"request_timeout"}}',
            b'{"error":{"code":"service_unavailable"}}',
            b"Error: 429 Too Many Requests",
            b"error sending request for url",
        ):
            with self.subTest(diagnostic=diagnostic):
                self.assertTrue(execution_is_unavailable(b"", diagnostic))

    def test_unknown_nonzero_diagnostic_is_task_execution_failure(self):
        completed = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout=b"model crashed for an unknown reason",
            stderr=b"",
        )
        with patch(f"{__name__}.subprocess.run", return_value=completed):
            with self.assertRaises(ProbeFailure) as raised:
                run_case("codex", {}, "pattern-final-owner", CASES["pattern-final-owner"])
        self.assertEqual("task_execution_failed", raised.exception.reason)

    def test_exact_nonzero_model_code_is_prerequisite_blocker(self):
        completed = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout=b"",
            stderr=b'{"error":{"code":"model_not_found"}}',
        )
        with patch(f"{__name__}.subprocess.run", return_value=completed):
            with self.assertRaises(ProbeBlocked) as raised:
                run_case("codex", {}, "pattern-final-owner", CASES["pattern-final-owner"])
        self.assertEqual(
            "model_auth_or_task_execution_unavailable", raised.exception.reason
        )

    def test_local_spawn_oserror_is_failure_not_prerequisite_blocker(self):
        with patch(f"{__name__}.subprocess.run", side_effect=OSError("synthetic")):
            with self.assertRaises(ProbeFailure) as raised:
                run_case("codex", {}, "pattern-final-owner", CASES["pattern-final-owner"])
        self.assertEqual("task_execution_failed", raised.exception.reason)

    def terminal_payload_with_drift(self, terminal: BaseException) -> tuple[int, dict[str, Any]]:
        output = io.StringIO()
        with (
            patch(
                f"{__name__}.capture_host",
                return_value=("codex", Path("codex"), Path("codex"), {}),
            ),
            patch(f"{__name__}.run_case", side_effect=terminal),
            patch(
                f"{__name__}.require_unchanged_host",
                side_effect=ProbeFailure("host_resolution_or_version_drift"),
            ),
            contextlib.redirect_stdout(output),
        ):
            status = main()
        return status, json.loads(output.getvalue())

    def test_drift_overrides_blocker_terminal_path(self):
        status, payload = self.terminal_payload_with_drift(
            ProbeBlocked("model_auth_or_task_execution_unavailable", 1)
        )
        self.assertEqual(1, status)
        self.assertEqual("fail", payload["status"])
        self.assertEqual("host_resolution_or_version_drift", payload["reason"])

    def test_drift_overrides_known_failure_terminal_path(self):
        status, payload = self.terminal_payload_with_drift(
            ProbeFailure("semantic_result_mismatch", "synthetic-case")
        )
        self.assertEqual(1, status)
        self.assertEqual("fail", payload["status"])
        self.assertEqual("host_resolution_or_version_drift", payload["reason"])

    def test_drift_overrides_unexpected_failure_terminal_path(self):
        status, payload = self.terminal_payload_with_drift(RuntimeError("synthetic"))
        self.assertEqual(1, status)
        self.assertEqual("fail", payload["status"])
        self.assertEqual("host_resolution_or_version_drift", payload["reason"])

    def test_invented_signature_in_nonfinal_agent_message_is_rejected(self):
        events = [
            {
                "type": "item.completed",
                "item": {
                    "type": "agent_message",
                    "text": "func transferBaton(to destination: Profile)",
                },
            },
            {
                "type": "item.completed",
                "item": {
                    "type": "agent_message",
                    "text": '{"result":"unsupported_no_verified_first_class_api"}',
                },
            },
        ]
        with self.assertRaises(ProbeFailure) as raised:
            parse_bounded_result(events, "fictional-transfer-baton-api")
        self.assertEqual(
            "invented_fictional_api_signature", raised.exception.reason
        )

    def test_qualified_invented_signature_in_any_agent_message_is_rejected(self):
        events = [
            {
                "type": "agent_message",
                "text": "LanguageModelSession.transferBaton(to:) -> Transcript",
            },
            {
                "type": "agent_message",
                "text": '{"result":"unsupported_no_verified_first_class_api"}',
            },
        ]
        with self.assertRaises(ProbeFailure) as raised:
            parse_bounded_result(events, "fictional-transfer-baton-api")
        self.assertEqual(
            "invented_fictional_api_signature", raised.exception.reason
        )

    def test_other_swift_signature_in_fictional_task_is_rejected(self):
        events = [
            {
                "type": "agent_message",
                "text": "public func handoffSession(to destination: Profile) async",
            },
            {
                "type": "agent_message",
                "text": '{"result":"unsupported_no_verified_first_class_api"}',
            },
        ]
        with self.assertRaises(ProbeFailure) as raised:
            parse_bounded_result(events, "fictional-transfer-baton-api")
        self.assertEqual(
            "invented_fictional_api_signature", raised.exception.reason
        )

    def test_ordinary_case_prose_is_not_mistaken_for_a_swift_declaration(self):
        events = [
            {
                "type": "agent_message",
                "text": "In this case unsupported is the bounded result.",
            },
            {
                "type": "agent_message",
                "text": '{"result":"unsupported_no_verified_first_class_api"}',
            },
        ]
        result, _ = parse_bounded_result(events, "fictional-transfer-baton-api")
        self.assertEqual("unsupported_no_verified_first_class_api", result)


if __name__ == "__main__":
    raise SystemExit(main())
