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
PINNED_PASSIVE_ITEM_KEYS = {
    "agent_message": {"id", "text", "type"},
    "reasoning": {"id", "text", "type"},
    "error": {"id", "message", "type"},
}
PINNED_ACTION_ITEM_TYPES = {
    "collab_tool_call",
    "file_change",
    "mcp_tool_call",
    "todo_list",
    "web_search",
}
PINNED_ITEM_TYPES = {
    "command_execution",
    *PINNED_PASSIVE_ITEM_KEYS,
    *PINNED_ACTION_ITEM_TYPES,
}
COMMAND_EVENT_KEYS = {"item", "type"}
COMMAND_ITEM_KEYS = {
    "aggregated_output",
    "command",
    "exit_code",
    "id",
    "status",
    "type",
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
SHELL_WRAPPERS = {"bash", "sh", "zsh"}
COMMAND_PREFIX_WRAPPERS = {"command", "env", "exec", "nohup", "sudo"}
SHELL_CONTROL_CHARACTERS = frozenset("();<>|&")
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
DIRECT_SEARCH_COMMANDS = {"grep", "rg"}
REFERENCE_DISCOVERY_ACCESS = "discovery"
REFERENCE_CONTENT_ACCESS = "content_read"
EXACT_REFERENCE_ACCESS_SEQUENCE = (
    REFERENCE_DISCOVERY_ACCESS,
    REFERENCE_CONTENT_ACCESS,
)
DIRECT_SEARCH_FLAG_OPTIONS = {
    "grep": {
        "--fixed-strings",
        "--line-number",
        "-F",
        "-n",
    },
    "rg": {
        "--fixed-strings",
        "--line-number",
        "-F",
        "-n",
    },
}
DIRECT_SEARCH_PATTERN_OPTIONS = {"--regexp", "-e"}
DIRECT_SEARCH_REJECTED_OPTIONS = {
    "--dereference-recursive",
    "--file",
    "--ignore-file",
    "--include",
    "--pre",
    "--pre-glob",
    "--recursive",
    "--search-zip",
    "-R",
    "-f",
    "-r",
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


def reject_json_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant: {value}")


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
        "workflow activation. Use exactly two separate tool invocations for "
        "reference access. In the first tool invocation, run exactly `rg --files "
        f"{REFERENCE_ROOT_RELATIVE}` with no content read and no second command. "
        "After that first invocation, from the task semantics and the listed "
        "basenames, independently select the needed canonical owner. In the "
        "second tool invocation, run exactly `cat <one-approved-owner-path>` with "
        "the selected canonical path substituted for the placeholder, with no "
        "directory listing or second command. Do not combine the directory "
        "listing and content read in one shell string or tool call. Do not use "
        "pipes, redirection, command chaining, command substitution, xargs, "
        "find -exec, globs, bulk reads, alternate commands, additional operands, "
        "or any additional reference-access invocation. Do not grep or search "
        "across the directory, and do not read unrelated reference content. Base "
        "the classification only on the independently selected owner. "
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
            event = json.loads(
                line,
                object_pairs_hook=pairs_without_duplicates,
                parse_constant=reject_json_constant,
            )
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


def parsed_shell_command(command: str, task_id: str) -> tuple[str, list[str]]:
    try:
        lexer = shlex.shlex(
            command,
            posix=True,
            punctuation_chars="".join(sorted(SHELL_CONTROL_CHARACTERS)),
        )
        lexer.whitespace_split = True
        lexer.commenters = ""
        tokens = list(lexer)
    except ValueError:
        raise ProbeFailure("unparseable_reference_command", task_id) from None
    if not tokens:
        return command, []
    return command, tokens


def shell_tokens(command: str, task_id: str) -> list[str]:
    return parsed_shell_command(command, task_id)[1]


def shell_syntax_flags(command: str) -> tuple[bool, bool]:
    single_quoted = False
    double_quoted = False
    escaped = False
    has_control = False
    has_command_substitution = False
    for index, character in enumerate(command):
        if escaped:
            escaped = False
            continue
        if character == "\\" and not single_quoted:
            escaped = True
            continue
        if character == "'" and not double_quoted:
            single_quoted = not single_quoted
            continue
        if character == '"' and not single_quoted:
            double_quoted = not double_quoted
            continue
        if single_quoted:
            continue
        if character == "`" or (
            character == "$" and command[index : index + 2] == "$("
        ):
            has_command_substitution = True
        if not double_quoted and character in SHELL_CONTROL_CHARACTERS:
            has_control = True
    return has_control, has_command_substitution


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


def declared_working_directory(
    value: dict[str, Any],
    base: Path,
    task_id: str,
) -> Path:
    declared: list[Path] = []
    for key in ("cwd", "workdir"):
        if key not in value:
            continue
        candidate = value[key]
        if not isinstance(candidate, str):
            raise ProbeFailure("invalid_tool_event", task_id)
        declared.append(resolve_candidate_path(candidate, base, task_id))
    if not declared:
        return base.resolve(strict=False)
    if any(candidate != declared[0] for candidate in declared[1:]):
        raise ProbeFailure("invalid_tool_event", task_id)
    return declared[0]


def is_reference_context(path: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(REFERENCE_ROOT.resolve(strict=True))
    except (OSError, RuntimeError, ValueError):
        return False
    return True


def direct_search_reference_read(
    executable: str,
    arguments: list[str],
    base: Path,
    task_id: str,
) -> str:
    patterns: list[str] = []
    positionals: list[str] = []
    parse_options = True
    index = 0
    while index < len(arguments):
        token = arguments[index]
        if parse_options and token == "--":
            parse_options = False
            index += 1
            continue
        if parse_options and token.startswith("--"):
            option, separator, attached = token.partition("=")
            if option in DIRECT_SEARCH_REJECTED_OPTIONS:
                raise ProbeFailure("bulk_reference_content_read", task_id)
            if option in DIRECT_SEARCH_FLAG_OPTIONS[executable]:
                if separator:
                    raise ProbeFailure("ambiguous_reference_read", task_id)
                index += 1
                continue
            if option in DIRECT_SEARCH_PATTERN_OPTIONS:
                if separator:
                    if not attached:
                        raise ProbeFailure("ambiguous_reference_read", task_id)
                    patterns.append(attached)
                    index += 1
                    continue
                index += 1
                if index >= len(arguments):
                    raise ProbeFailure("ambiguous_reference_read", task_id)
                patterns.append(arguments[index])
                index += 1
                continue
            raise ProbeFailure("ambiguous_reference_read", task_id)
        if parse_options and token.startswith("-") and token != "-":
            if token in DIRECT_SEARCH_REJECTED_OPTIONS:
                raise ProbeFailure("bulk_reference_content_read", task_id)
            if token in DIRECT_SEARCH_FLAG_OPTIONS[executable]:
                index += 1
                continue
            if token == "-e":
                index += 1
                if index >= len(arguments):
                    raise ProbeFailure("ambiguous_reference_read", task_id)
                patterns.append(arguments[index])
                index += 1
                continue
            if token.startswith("-e") and len(token) > 2:
                patterns.append(token[2:])
                index += 1
                continue
            raise ProbeFailure("ambiguous_reference_read", task_id)
        positionals.append(token)
        index += 1

    if not patterns:
        if len(positionals) < 2:
            raise ProbeFailure("ambiguous_reference_read", task_id)
        patterns.append(positionals.pop(0))
    if any(is_reference_path_token(pattern) for pattern in patterns):
        raise ProbeFailure("ambiguous_reference_read", task_id)
    if len(positionals) != 1 or positionals[0] == "-":
        raise ProbeFailure("bulk_reference_content_read", task_id)
    name = validate_reference_candidate(
        positionals[0],
        base,
        task_id,
        directory_discovery=False,
        bulk_directory_read=True,
    )
    if name is None:
        raise ProbeFailure("ambiguous_reference_read", task_id)
    return name


def validate_rg_files_discovery(
    arguments: list[str],
    base: Path,
    task_id: str,
) -> None:
    if any(
        token.partition("=")[0] in DIRECT_SEARCH_REJECTED_OPTIONS
        for token in arguments
    ):
        raise ProbeFailure("bulk_reference_content_read", task_id)
    if len(arguments) != 2 or arguments[0] != "--files":
        raise ProbeFailure("ambiguous_reference_read", task_id)
    candidate = Path(arguments[1])
    unresolved = candidate if candidate.is_absolute() else base / candidate
    try:
        metadata = unresolved.lstat()
        resolved = unresolved.resolve(strict=True)
        canonical_root = REFERENCE_ROOT.resolve(strict=True)
    except (OSError, RuntimeError, ValueError):
        raise ProbeFailure("ambiguous_reference_read", task_id) from None
    if (
        resolved != canonical_root
        or not stat.S_ISDIR(metadata.st_mode)
        or stat.S_ISLNK(metadata.st_mode)
    ):
        raise ProbeFailure("ambiguous_reference_read", task_id)


def command_reference_reads(
    command: str,
    task_id: str,
    base: Path = ROOT,
    access_sequence: list[str] | None = None,
) -> tuple[set[str], int]:
    observed: set[str] = set()
    read_count = 0
    effective_command, tokens = parsed_shell_command(command, task_id)
    if not tokens:
        return observed, 0
    executable = Path(tokens[0]).name
    reference_relevant = any(is_reference_path_token(token) for token in tokens)
    reference_context = is_reference_context(base)
    if executable in SHELL_WRAPPERS:
        if reference_relevant or reference_context:
            raise ProbeFailure("bulk_reference_content_read", task_id)
        return observed, 0
    if executable in COMMAND_PREFIX_WRAPPERS:
        raise ProbeFailure("ambiguous_reference_read", task_id)
    has_control, has_command_substitution = shell_syntax_flags(effective_command)
    has_xargs = executable == "xargs"
    if has_xargs:
        raise ProbeFailure("ambiguous_reference_read", task_id)
    if (
        executable in DIRECT_SEARCH_COMMANDS
        or reference_relevant
        or reference_context
    ) and (has_control or has_command_substitution):
        raise ProbeFailure("bulk_reference_content_read", task_id)
    if has_control or has_command_substitution:
        return observed, 0

    arguments = tokens[1:]
    path_tokens = [token for token in arguments if is_reference_path_token(token)]
    is_rg_discovery = executable == "rg" and "--files" in arguments
    if is_rg_discovery:
        validate_rg_files_discovery(
            arguments,
            base.resolve(strict=False),
            task_id,
        )
        if access_sequence is not None:
            access_sequence.append(REFERENCE_DISCOVERY_ACCESS)
        return observed, 0
    if executable in DIRECT_SEARCH_COMMANDS and not is_rg_discovery:
        observed.add(
            direct_search_reference_read(
                executable,
                arguments,
                base.resolve(strict=False),
                task_id,
            )
        )
        if access_sequence is not None:
            access_sequence.append(REFERENCE_CONTENT_ACCESS)
        return observed, 1
    if (
        reference_context
        and executable in DISCOVERY_COMMANDS | CONTENT_COMMANDS
        and not path_tokens
    ):
        raise ProbeFailure("bulk_reference_content_read", task_id)
    if not path_tokens:
        return observed, 0
    directory_discovery = executable in DISCOVERY_COMMANDS or is_rg_discovery
    if directory_discovery:
        if any(
            marker in arguments for marker in ("-exec", "-execdir", "-delete")
        ):
            raise ProbeFailure("bulk_reference_content_read", task_id)
    elif executable not in CONTENT_COMMANDS:
        raise ProbeFailure("ambiguous_reference_read", task_id)
    current_directory = base.resolve(strict=False)
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
            read_count += 1
    if access_sequence is not None:
        if directory_discovery and not observed:
            access_sequence.append(REFERENCE_DISCOVERY_ACCESS)
        elif observed:
            access_sequence.append(REFERENCE_CONTENT_ACCESS)
    return observed, read_count


def is_command_argv_array(value: list[object]) -> bool:
    if not value or not isinstance(value[0], str):
        return False
    executable = Path(value[0]).name
    return executable in (
        DISCOVERY_COMMANDS
        | CONTENT_COMMANDS
        | SHELL_WRAPPERS
        | COMMAND_PREFIX_WRAPPERS
        | {"xargs"}
    )


def has_direct_reference_path_owner(value: dict[str, Any]) -> bool:
    return any(
        isinstance(value.get(key), str)
        and is_reference_path_token(value[key])
        for key in ("path", "file_path")
    )


def reference_scalar_presence(value: object) -> tuple[bool, bool]:
    if isinstance(value, dict):
        if has_direct_reference_path_owner(value):
            return True, False
        nested_values = value.values()
    elif isinstance(value, list):
        nested_values = value
    else:
        is_reference = isinstance(value, str) and is_reference_path_token(value)
        return is_reference, not is_reference

    has_reference = False
    has_non_reference = False
    for nested in nested_values:
        nested_reference, nested_non_reference = reference_scalar_presence(nested)
        has_reference = has_reference or nested_reference
        has_non_reference = has_non_reference or nested_non_reference
    return has_reference, has_non_reference


def has_mixed_reference_scalars(value: list[object]) -> bool:
    has_reference, has_non_reference = reference_scalar_presence(value)
    return has_reference and has_non_reference


def structural_scalar_presence(value: object) -> tuple[bool, bool]:
    if isinstance(value, dict):
        if has_direct_reference_path_owner(value):
            return True, False
        if "paths" in value and reference_scalar_presence(value["paths"])[0]:
            return True, False
        nested_values = (
            nested
            for key, nested in value.items()
            if key not in {"cwd", "workdir"}
        )
    elif isinstance(value, list):
        nested_values = iter(value)
    else:
        is_reference = isinstance(value, str) and is_reference_path_token(value)
        return is_reference, not is_reference

    has_reference = False
    has_non_reference = False
    for nested in nested_values:
        nested_reference, nested_non_reference = structural_scalar_presence(nested)
        has_reference = has_reference or nested_reference
        has_non_reference = has_non_reference or nested_non_reference
    return has_reference, has_non_reference


def has_ambiguous_structural_siblings(value: dict[str, Any]) -> bool:
    presences = [
        structural_scalar_presence(nested)
        for key, nested in value.items()
        if key not in {"cwd", "workdir"}
    ]
    reference_children = {
        index for index, (has_reference, _) in enumerate(presences) if has_reference
    }
    non_reference_children = {
        index
        for index, (_, has_non_reference) in enumerate(presences)
        if has_non_reference
    }
    return any(
        reference_index != non_reference_index
        for reference_index in reference_children
        for non_reference_index in non_reference_children
    )


def contains_structured_command(value: object) -> bool:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in {"command", "argv"} or (
                key == "input" and not isinstance(nested, str)
            ):
                return True
            if contains_structured_command(nested):
                return True
    elif isinstance(value, list):
        return is_command_argv_array(value) or any(
            contains_structured_command(nested) for nested in value
        )
    return False


def validate_passive_path_metadata(value: object, task_id: str) -> None:
    if isinstance(value, dict):
        if set(value) & {
            "argv",
            "command",
            "file_path",
            "input",
            "path",
            "paths",
        }:
            raise ProbeFailure("invalid_tool_event", task_id)
        for nested in value.values():
            validate_passive_path_metadata(nested, task_id)
        return
    if isinstance(value, list):
        if is_command_argv_array(value):
            raise ProbeFailure("invalid_tool_event", task_id)
        for nested in value:
            validate_passive_path_metadata(nested, task_id)
        return
    if isinstance(value, str) and is_reference_path_token(value):
        raise ProbeFailure("invalid_tool_event", task_id)


def data_path_member_reads(
    value: object,
    base: Path,
    task_id: str,
    access_sequence: list[str] | None = None,
) -> tuple[set[str], int]:
    if isinstance(value, list):
        return data_path_collection_reads(
            value,
            base,
            task_id,
            access_sequence,
        )

    candidate: object
    metadata: dict[str, Any] = {}
    if isinstance(value, str):
        candidate = value
    elif isinstance(value, dict):
        owner_keys = [key for key in ("path", "file_path") if key in value]
        if len(owner_keys) != 1:
            raise ProbeFailure("invalid_tool_event", task_id)
        owner_key = owner_keys[0]
        candidate = value[owner_key]
        metadata = {key: nested for key, nested in value.items() if key != owner_key}
    else:
        raise ProbeFailure("invalid_tool_event", task_id)

    if (
        not isinstance(candidate, str)
        or candidate != candidate.strip()
        or candidate != candidate.strip("\"'(){}<>,")
        or any(character.isspace() for character in candidate)
        or any(operator in candidate for operator in ("|", ";", "&", ">", "<"))
        or not is_reference_path_token(candidate)
    ):
        raise ProbeFailure("invalid_tool_event", task_id)
    validate_passive_path_metadata(metadata, task_id)
    name = validate_reference_candidate(
        candidate,
        base,
        task_id,
        directory_discovery=False,
    )
    if name is None:
        raise ProbeFailure("invalid_tool_event", task_id)
    if access_sequence is not None:
        access_sequence.append(REFERENCE_CONTENT_ACCESS)
    return {name}, 1


def data_path_collection_reads(
    value: object,
    base: Path,
    task_id: str,
    access_sequence: list[str] | None = None,
) -> tuple[set[str], int]:
    if not isinstance(value, list):
        raise ProbeFailure("invalid_tool_event", task_id)
    observed: set[str] = set()
    read_count = 0
    for member in value:
        member_observed, member_count = data_path_member_reads(
            member,
            base,
            task_id,
            access_sequence,
        )
        observed.update(member_observed)
        read_count += member_count
    return observed, read_count


def direct_data_path_owner_reads(
    value: dict[str, Any],
    base: Path,
    task_id: str,
    access_sequence: list[str] | None = None,
) -> tuple[set[str], int] | None:
    record = {
        key: nested
        for key, nested in value.items()
        if key not in {"cwd", "workdir"}
    }
    if "path" in value or "file_path" in value:
        return data_path_member_reads(
            record,
            base,
            task_id,
            access_sequence,
        )
    if "paths" not in value:
        return None
    validate_passive_path_metadata(
        {key: nested for key, nested in record.items() if key != "paths"},
        task_id,
    )
    return data_path_collection_reads(
        value["paths"],
        base,
        task_id,
        access_sequence,
    )


def is_syntactic_command_input(value: str, task_id: str) -> bool:
    _, tokens = parsed_shell_command(value, task_id)
    if not tokens:
        return False
    executable = Path(tokens[0]).name
    return executable in (
        DISCOVERY_COMMANDS
        | CONTENT_COMMANDS
        | SHELL_WRAPPERS
        | COMMAND_PREFIX_WRAPPERS
        | {"xargs"}
    )


def mapping_reference_reads(
    value: object,
    base: Path,
    task_id: str,
    access_sequence: list[str] | None = None,
    *,
    allow_serialized_command: bool = False,
    allow_reference_value: bool = True,
) -> tuple[set[str], int]:
    observed: set[str] = set()
    read_count = 0
    if isinstance(value, str):
        stripped = value.lstrip()
        if stripped.startswith(("{", "[")):
            try:
                decoded = json.loads(
                    value,
                    object_pairs_hook=pairs_without_duplicates,
                    parse_constant=reject_json_constant,
                )
            except (json.JSONDecodeError, ValueError):
                raise ProbeFailure("invalid_tool_event", task_id) from None
            if isinstance(decoded, (dict, list)):
                if (
                    not allow_serialized_command
                    and contains_structured_command(decoded)
                ):
                    raise ProbeFailure("invalid_tool_event", task_id)
                nested_observed, nested_count = mapping_reference_reads(
                    decoded,
                    base,
                    task_id,
                    access_sequence,
                    allow_reference_value=allow_reference_value,
                )
                observed.update(nested_observed)
                read_count += nested_count
            return observed, read_count
        if is_reference_path_token(value):
            raise ProbeFailure("invalid_tool_event", task_id)
        return observed, read_count
    if isinstance(value, list):
        has_reference = reference_scalar_presence(value)[0]
        if has_reference:
            if not allow_reference_value:
                raise ProbeFailure("invalid_tool_event", task_id)
            return data_path_collection_reads(
                value,
                base,
                task_id,
                access_sequence,
            )
        if has_mixed_reference_scalars(value) or is_command_argv_array(value):
            raise ProbeFailure("invalid_tool_event", task_id)
        for nested in value:
            nested_observed, nested_count = mapping_reference_reads(
                nested,
                base,
                task_id,
                access_sequence,
                allow_reference_value=allow_reference_value,
            )
            observed.update(nested_observed)
            read_count += nested_count
        return observed, read_count
    if not isinstance(value, dict):
        return observed, read_count
    local_base = declared_working_directory(value, base, task_id)
    direct_owner_reads = direct_data_path_owner_reads(
        value,
        local_base,
        task_id,
        access_sequence,
    )
    if direct_owner_reads is not None:
        return direct_owner_reads
    if has_ambiguous_structural_siblings(value):
        raise ProbeFailure("invalid_tool_event", task_id)
    for key, nested in value.items():
        if key in {"cwd", "workdir"}:
            continue
        if key == "argv":
            raise ProbeFailure("invalid_tool_event", task_id)
        if key in {"path", "file_path"}:
            if not isinstance(nested, str):
                raise ProbeFailure("invalid_tool_event", task_id)
            name = validate_reference_candidate(
                nested,
                local_base,
                task_id,
                directory_discovery=False,
            )
            if name is not None:
                observed.add(name)
                read_count += 1
                if access_sequence is not None:
                    access_sequence.append(REFERENCE_CONTENT_ACCESS)
        elif key == "paths":
            nested_observed, nested_count = data_path_collection_reads(
                nested,
                local_base,
                task_id,
                access_sequence,
            )
            observed.update(nested_observed)
            read_count += nested_count
        elif key == "command":
            if not isinstance(nested, str):
                raise ProbeFailure("invalid_tool_event", task_id)
            nested_observed, nested_count = command_reference_reads(
                nested, task_id, local_base, access_sequence
            )
            observed.update(nested_observed)
            read_count += nested_count
        elif key == "input":
            if not isinstance(nested, str):
                raise ProbeFailure("invalid_tool_event", task_id)
            if is_syntactic_command_input(nested, task_id):
                nested_observed, nested_count = command_reference_reads(
                    nested, task_id, local_base, access_sequence
                )
            elif is_reference_path_token(nested):
                raise ProbeFailure("invalid_tool_event", task_id)
            else:
                nested_observed, nested_count = mapping_reference_reads(
                    nested, local_base, task_id, access_sequence
                )
            observed.update(nested_observed)
            read_count += nested_count
        else:
            nested_observed, nested_count = mapping_reference_reads(
                nested,
                local_base,
                task_id,
                access_sequence,
                allow_serialized_command=key == "arguments",
                allow_reference_value=False,
            )
            observed.update(nested_observed)
            read_count += nested_count
    return observed, read_count


def validate_pinned_passive_item(
    event: dict[str, Any], item: dict[str, Any], task_id: str
) -> None:
    item_type = item.get("type")
    expected_keys = PINNED_PASSIVE_ITEM_KEYS.get(str(item_type))
    payload_key = "message" if item_type == "error" else "text"
    if (
        expected_keys is None
        or set(event) != COMMAND_EVENT_KEYS
        or event.get("type") != "item.completed"
        or set(item) != expected_keys
        or not isinstance(item.get("id"), str)
        or not item.get("id")
        or not isinstance(item.get(payload_key), str)
    ):
        raise ProbeFailure("ambiguous_reference_read", task_id)


def exact_command_items(
    events: list[dict[str, Any]], task_id: str
) -> list[dict[str, Any]]:
    lifecycle: list[tuple[str, dict[str, Any]]] = []
    for event in events:
        event_type = event.get("type")
        if "item" not in event:
            if event_type in {"item.started", "item.updated", "item.completed"}:
                raise ProbeFailure("ambiguous_reference_read", task_id)
            continue
        item = event.get("item")
        if not isinstance(item, dict):
            raise ProbeFailure("ambiguous_reference_read", task_id)
        item_type = item.get("type")
        if item_type not in PINNED_ITEM_TYPES:
            raise ProbeFailure("ambiguous_reference_read", task_id)
        if item_type in PINNED_PASSIVE_ITEM_KEYS:
            validate_pinned_passive_item(event, item, task_id)
            continue
        if item_type != "command_execution":
            raise ProbeFailure("ambiguous_reference_read", task_id)
        if set(event) != COMMAND_EVENT_KEYS or set(item) != COMMAND_ITEM_KEYS:
            raise ProbeFailure("ambiguous_reference_read", task_id)
        lifecycle.append((str(event.get("type")), item))

    if len(lifecycle) != 4:
        reason = (
            "bulk_reference_content_read"
            if len(lifecycle) > 4
            else "ambiguous_reference_read"
        )
        raise ProbeFailure(reason, task_id)

    completed: list[dict[str, Any]] = []
    used_identifiers: set[str] = set()
    for index in range(0, len(lifecycle), 2):
        started_event_type, started = lifecycle[index]
        completed_event_type, finished = lifecycle[index + 1]
        if (
            started_event_type != "item.started"
            or completed_event_type != "item.completed"
        ):
            raise ProbeFailure("ambiguous_reference_read", task_id)

        identifier = started.get("id")
        command = started.get("command")
        if (
            not isinstance(identifier, str)
            or not identifier
            or identifier in used_identifiers
            or not isinstance(command, str)
            or not command
            or started.get("type") != "command_execution"
            or started.get("status") != "in_progress"
            or started.get("exit_code") is not None
            or started.get("aggregated_output") != ""
        ):
            raise ProbeFailure("ambiguous_reference_read", task_id)
        used_identifiers.add(identifier)

        if (
            finished.get("id") != identifier
            or finished.get("type") != "command_execution"
            or finished.get("command") != command
            or finished.get("status") != "completed"
            or type(finished.get("exit_code")) is not int
            or finished.get("exit_code") != 0
            or not isinstance(finished.get("aggregated_output"), str)
        ):
            if (
                finished.get("status") != "completed"
                or finished.get("exit_code") != 0
            ):
                raise ProbeFailure("command_execution_failed", task_id)
            raise ProbeFailure("ambiguous_reference_read", task_id)
        completed.append(finished)
    return completed


def exact_command_script(command: str, task_id: str) -> tuple[str, bool]:
    discovery = f"rg --files {REFERENCE_ROOT_RELATIVE}"
    if command == discovery:
        return command, True

    direct = True
    script = command
    try:
        outer_tokens = shlex.split(command, posix=True)
    except ValueError:
        raise ProbeFailure("ambiguous_reference_read", task_id) from None
    shell_token = Path(outer_tokens[0]) if outer_tokens else None
    if (
        len(outer_tokens) == 3
        and shell_token is not None
        and (
            outer_tokens[0] in SHELL_WRAPPERS
            or (
                shell_token.is_absolute()
                and shell_token.name in SHELL_WRAPPERS
            )
        )
        and outer_tokens[1] == "-lc"
    ):
        direct = False
        script = outer_tokens[2]

    try:
        tokens = shlex.split(script, posix=True)
    except ValueError:
        raise ProbeFailure("ambiguous_reference_read", task_id) from None
    if not direct and script == discovery:
        return discovery, True
    if tokens[:1] != ["cat"]:
        raise ProbeFailure("ambiguous_reference_read", task_id)
    if len(tokens) != 2:
        owners = [
            validate_reference_candidate(
                token,
                ROOT,
                task_id,
                directory_discovery=False,
            )
            for token in tokens[1:]
        ]
        if len({owner for owner in owners if owner is not None}) > 1:
            raise ProbeFailure("reference_selection_mismatch", task_id)
        raise ProbeFailure("bulk_reference_content_read", task_id)

    owner = validate_reference_candidate(
        tokens[1],
        ROOT,
        task_id,
        directory_discovery=False,
    )
    if owner is None:
        raise ProbeFailure("ambiguous_reference_read", task_id)
    exact_read = f"cat {REFERENCE_ROOT_RELATIVE}/{owner}"
    if (direct and command != exact_read) or (not direct and script != exact_read):
        raise ProbeFailure("ambiguous_reference_read", task_id)
    return owner, False


def exact_reference_reads(
    events: list[dict[str, Any]], task_id: str
) -> set[str]:
    commands = exact_command_items(events, task_id)
    first_value, first_is_discovery = exact_command_script(
        str(commands[0]["command"]), task_id
    )
    owner, second_is_discovery = exact_command_script(
        str(commands[1]["command"]), task_id
    )
    if not first_is_discovery or second_is_discovery:
        raise ProbeFailure("ambiguous_reference_read", task_id)
    if first_value != f"rg --files {REFERENCE_ROOT_RELATIVE}":
        raise ProbeFailure("ambiguous_reference_read", task_id)
    return {owner}


def observed_reference_reads(
    events: list[dict[str, Any]],
    task_id: str,
    *,
    require_exact_sequence: bool = False,
) -> set[str]:
    if require_exact_sequence:
        return exact_reference_reads(events, task_id)

    observed: set[str] = set()
    read_count = 0
    access_sequence: list[str] = []
    for item in paired_successful_tool_items(events, task_id):
        item_access_sequence: list[str] = []
        if item.get("type") == "command_execution":
            command = item.get("command")
            if not isinstance(command, str):
                raise ProbeFailure("invalid_tool_event", task_id)
            base = declared_working_directory(item, ROOT, task_id)
            item_observed, item_count = command_reference_reads(
                command, task_id, base, item_access_sequence
            )
        else:
            inputs = {key: item[key] for key in TOOL_INPUT_KEYS if key in item}
            item_observed, item_count = mapping_reference_reads(
                inputs, ROOT, task_id, item_access_sequence
            )
        if len(item_access_sequence) > 1:
            raise ProbeFailure("bulk_reference_content_read", task_id)
        access_sequence.extend(item_access_sequence)
        observed.update(item_observed)
        read_count += item_count
        if read_count > 1:
            raise ProbeFailure("bulk_reference_content_read", task_id)
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
        parsed = json.loads(
            response,
            object_pairs_hook=pairs_without_duplicates,
            parse_constant=reject_json_constant,
        )
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
            parsed = json.loads(
                line,
                object_pairs_hook=pairs_without_duplicates,
                parse_constant=reject_json_constant,
            )
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
    observed = observed_reference_reads(
        events, task_id, require_exact_sequence=True
    )
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
        cwd: str | None = None,
        aggregated_output: str = "synthetic command output",
    ) -> list[dict[str, Any]]:
        inputs: dict[str, Any] = {"command": command}
        if cwd is not None:
            inputs["cwd"] = cwd
        return [
            {
                "type": "item.started",
                "item": {
                    **inputs,
                    "aggregated_output": "",
                    "exit_code": None,
                    "id": identifier,
                    "status": "in_progress",
                    "type": "command_execution",
                },
            },
            {
                "type": "item.completed",
                "item": {
                    **inputs,
                    "aggregated_output": aggregated_output,
                    "exit_code": exit_code,
                    "id": identifier,
                    "status": completion_status,
                    "type": "command_execution",
                },
            },
        ]

    def exact_reference_access_events(
        self,
        owner: str = "apple-api-availability.md",
        *,
        shell: str | None = None,
    ) -> list[dict[str, Any]]:
        discovery = f"rg --files {REFERENCE_ROOT_RELATIVE}"
        read = f"cat {REFERENCE_ROOT_RELATIVE}/{owner}"
        if shell is not None:
            discovery = f"{shell} -lc {shlex.quote(discovery)}"
            read = f"{shell} -lc {shlex.quote(read)}"
        return self.command_events(
            discovery,
            identifier="discovery-1",
        ) + self.command_events(
            read,
            identifier="reader-1",
        )

    def strict_observed(
        self,
        events: list[dict[str, Any]],
    ) -> set[str]:
        return observed_reference_reads(
            events,
            "synthetic-case",
            require_exact_sequence=True,
        )

    def assert_strict_probe_failure(
        self,
        events: list[dict[str, Any]],
    ) -> None:
        with self.assertRaises(ProbeFailure):
            self.strict_observed(events)

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

    def assert_probe_failure_in(
        self,
        events: list[dict[str, Any]],
        expected_reasons: set[str],
    ) -> None:
        with self.assertRaises(ProbeFailure) as raised:
            observed_reference_reads(events, "synthetic-case")
        self.assertIn(raised.exception.reason, expected_reasons)

    def direct_reader_events(
        self,
        command: str,
        *,
        surface: str,
        cwd: Path,
        identifier: str = "reader-1",
    ) -> list[dict[str, Any]]:
        if surface == "command_event":
            return self.command_events(
                command,
                cwd=str(cwd),
                identifier=identifier,
            )
        nested = {"payload": {"command": command, "cwd": str(cwd)}}
        arguments: object = (
            nested if surface == "nested_mapping" else json.dumps(nested)
        )
        return self.tool_events(
            "mcp_tool_call",
            {"arguments": arguments},
            identifier=identifier,
        )

    def test_exact_direct_or_host_shell_lifecycle_selects_one_semantic_owner(self):
        for shell in (
            None,
            "sh",
            "bash",
            "zsh",
            "/bin/sh",
            "/bin/bash",
            "/bin/zsh",
            "/opt/homebrew/bin/zsh",
            "/configured/toolchain/bash",
        ):
            with self.subTest(shell=shell or "direct"):
                try:
                    observed = self.strict_observed(
                        self.exact_reference_access_events(shell=shell)
                    )
                except ProbeFailure as failure:
                    self.fail(
                        "approved direct or shell-enveloped lifecycle was "
                        f"rejected: {failure.reason}"
                    )
                self.assertEqual(
                    {"apple-api-availability.md"},
                    observed,
                )

    def test_shell_envelope_rejects_relative_slash_executable_tokens(self):
        for shell in (
            "./bash",
            "tools/zsh",
            "../bin/sh",
            "nested/toolchain/bash",
        ):
            with self.subTest(shell=shell):
                self.assert_strict_probe_failure(
                    self.exact_reference_access_events(shell=shell)
                )

    def test_command_items_require_the_exact_pinned_schema(self):
        expected_item_keys = {
            "aggregated_output",
            "command",
            "exit_code",
            "id",
            "status",
            "type",
        }
        canonical = self.exact_reference_access_events()
        for event in canonical:
            self.assertEqual(expected_item_keys, set(event["item"]))

        malformed: dict[str, list[dict[str, Any]]] = {}
        for event_index, phase in ((0, "started"), (1, "completed")):
            for key in sorted(expected_item_keys):
                events = json.loads(json.dumps(canonical))
                events[event_index]["item"].pop(key)
                malformed[f"{phase}_missing_{key}"] = events

        wrong_started_exit = json.loads(json.dumps(canonical))
        wrong_started_exit[0]["item"]["exit_code"] = 0
        malformed["started_exit_code_not_null"] = wrong_started_exit
        wrong_started_status = json.loads(json.dumps(canonical))
        wrong_started_status[0]["item"]["status"] = "completed"
        malformed["started_status_not_in_progress"] = wrong_started_status
        wrong_completed_output = json.loads(json.dumps(canonical))
        wrong_completed_output[1]["item"]["aggregated_output"] = ["not", "text"]
        malformed["completed_output_not_string"] = wrong_completed_output
        extra_item_key = json.loads(json.dumps(canonical))
        extra_item_key[0]["item"]["cwd"] = str(ROOT)
        extra_item_key[1]["item"]["cwd"] = str(ROOT)
        malformed["extra_item_key"] = extra_item_key
        extra_event_key = json.loads(json.dumps(canonical))
        extra_event_key[0]["unexpected"] = True
        malformed["extra_event_key"] = extra_event_key

        for name, events in malformed.items():
            with self.subTest(schema=name):
                self.assert_strict_probe_failure(events)

    def test_command_lifecycles_are_sequential_paired_and_globally_unique(self):
        canonical = self.exact_reference_access_events()

        interleaved = [canonical[0], canonical[2], canonical[1], canonical[3]]
        reversed_completions = [
            canonical[0],
            canonical[2],
            canonical[3],
            canonical[1],
        ]
        completion_before_start = [
            canonical[1],
            canonical[0],
            canonical[2],
            canonical[3],
        ]
        reused_identifier = json.loads(json.dumps(canonical))
        reused_identifier[2]["item"]["id"] = "discovery-1"
        reused_identifier[3]["item"]["id"] = "discovery-1"
        with_update = json.loads(json.dumps(canonical))
        update = json.loads(json.dumps(with_update[0]))
        update["type"] = "item.updated"
        with_update.insert(1, update)
        with_extra_command = canonical + self.command_events(
            "pwd",
            identifier="extra-1",
        )

        invalid = {
            "interleaved": interleaved,
            "reversed_completions": reversed_completions,
            "completion_before_start": completion_before_start,
            "sequential_id_reuse": reused_identifier,
            "command_update": with_update,
            "missing_discovery_completion": canonical[:1] + canonical[2:],
            "missing_read_start": canonical[:2] + canonical[3:],
            "extra_command": with_extra_command,
        }
        for name, events in invalid.items():
            with self.subTest(lifecycle=name):
                self.assert_strict_probe_failure(events)

    def test_every_non_command_tool_item_invalidates_exact_evidence(self):
        canonical = self.exact_reference_access_events()
        non_command_tool_types = (
            "file_read",
            "function_call",
            "mcp_tool_call",
            "tool_call",
            "file_change",
            "collab_tool_call",
            "web_search",
        )
        for item_type in non_command_tool_types:
            events = (
                canonical[:2]
                + self.tool_events(
                    item_type,
                    {},
                    identifier=f"extra-{item_type}",
                )
                + canonical[2:]
            )
            with self.subTest(item_type=item_type):
                self.assert_strict_probe_failure(events)

    def test_pinned_passive_items_do_not_invalidate_exact_evidence(self):
        canonical = self.exact_reference_access_events()
        passive_events = {
            "agent_message": {
                "type": "item.completed",
                "item": {
                    "id": "passive-agent-message",
                    "type": "agent_message",
                    "text": "synthetic response",
                },
            },
            "reasoning": {
                "type": "item.completed",
                "item": {
                    "id": "passive-reasoning",
                    "type": "reasoning",
                    "text": "synthetic summary",
                },
            },
            "error": {
                "type": "item.completed",
                "item": {
                    "id": "passive-error",
                    "type": "error",
                    "message": "synthetic non-fatal error item",
                },
            },
        }
        for item_type, event in passive_events.items():
            with self.subTest(item_type=item_type):
                self.assertEqual(
                    {"apple-api-availability.md"},
                    self.strict_observed(canonical[:2] + [event] + canonical[2:]),
                )

    def test_pinned_actions_tools_and_unknown_items_invalidate_exact_evidence(self):
        canonical = self.exact_reference_access_events()
        rejected_item_types = (
            "todo_list",
            "file_change",
            "mcp_tool_call",
            "collab_tool_call",
            "web_search",
            "file_read",
            "function_call",
            "tool_call",
            "future_tool_action",
        )
        for item_type in rejected_item_types:
            event = {
                "type": "item.completed",
                "item": {
                    "id": f"extra-{item_type}",
                    "type": item_type,
                },
            }
            with self.subTest(item_type=item_type):
                self.assert_strict_probe_failure(
                    canonical[:2] + [event] + canonical[2:]
                )

    def test_only_exact_discovery_and_cat_owner_tokens_are_accepted(self):
        owner = f"{REFERENCE_ROOT_RELATIVE}/apple-api-availability.md"
        discovery_alternatives = (
            f"ls {REFERENCE_ROOT_RELATIVE}",
            f"find {REFERENCE_ROOT_RELATIVE}",
            f"/usr/bin/rg --files {REFERENCE_ROOT_RELATIVE}",
            f"rg --files -- {REFERENCE_ROOT_RELATIVE}",
            f"rg --files {REFERENCE_ROOT_RELATIVE} {REFERENCE_ROOT_RELATIVE}",
            f"rg --files {REFERENCE_ROOT_RELATIVE}/*.md",
        )
        for command in discovery_alternatives:
            events = self.command_events(
                command,
                identifier="discovery-1",
            ) + self.command_events(
                f"cat {owner}",
                identifier="reader-1",
            )
            with self.subTest(stage="discovery", command=command):
                self.assert_strict_probe_failure(events)

        read_alternatives = (
            f"sed -n '1,40p' {owner}",
            f"head {owner}",
            f"rg -n needle {owner}",
            f"grep -n needle {owner}",
            f"/bin/cat {owner}",
            f"cat -- {owner}",
            f"cat {owner} {owner}",
            f"cat {owner} /tmp/unrelated",
            f"cat {REFERENCE_ROOT_RELATIVE}/*.md",
            f"cat {REFERENCE_ROOT_RELATIVE}",
            "bash -c " + shlex.quote(f"cat {owner}"),
            f"python3 -c 'print(1)' {owner}",
            f"printf %s {owner}",
        )
        for command in read_alternatives:
            events = self.command_events(
                f"rg --files {REFERENCE_ROOT_RELATIVE}",
                identifier="discovery-1",
            ) + self.command_events(command, identifier="reader-1")
            with self.subTest(stage="read", command=command):
                self.assert_strict_probe_failure(events)

    def test_host_shell_envelope_rejects_other_flags_and_modified_inner_scripts(self):
        owner = f"{REFERENCE_ROOT_RELATIVE}/apple-api-availability.md"
        exact_discovery = f"rg --files {REFERENCE_ROOT_RELATIVE}"
        exact_read = f"cat {owner}"
        malformed_discovery = (
            "/bin/fish -lc " + shlex.quote(exact_discovery),
            "/configured/toolchain/bash.exe -lc " + shlex.quote(exact_discovery),
            "/bin/bash -c " + shlex.quote(exact_discovery),
            "/bin/bash -l -c " + shlex.quote(exact_discovery),
            "/bin/bash -lc " + shlex.quote(exact_discovery) + " placeholder",
            "/bin/bash -lc " + shlex.quote(exact_discovery + " && true"),
            "/bin/zsh -lc " + shlex.quote(exact_discovery + "; pwd"),
            "/bin/zsh -lc " + shlex.quote(exact_discovery + " " + REFERENCE_ROOT_RELATIVE),
        )
        malformed_read = (
            "fish -lc " + shlex.quote(exact_read),
            "/configured/toolchain/zsh.exe -lc " + shlex.quote(exact_read),
            "/bin/zsh -c " + shlex.quote(exact_read),
            "/bin/zsh -lc " + shlex.quote(exact_read) + " placeholder",
            "/bin/zsh -lc " + shlex.quote(exact_read + " && true"),
            "/bin/bash -lc " + shlex.quote(exact_read + " | wc -l"),
            "/bin/bash -lc " + shlex.quote(f"cat -- {owner}"),
            "/bin/bash -lc " + shlex.quote(f"cat {owner} {owner}"),
            "/bin/bash -lc "
            + shlex.quote("/bin/bash -lc " + shlex.quote(exact_read)),
        )
        exact_read_event = self.command_events(
            "/bin/zsh -lc " + shlex.quote(exact_read),
            identifier="reader-1",
        )
        exact_discovery_event = self.command_events(
            "/bin/bash -lc " + shlex.quote(exact_discovery),
            identifier="discovery-1",
        )
        for command in malformed_discovery:
            with self.subTest(stage="discovery", command=command):
                self.assert_strict_probe_failure(
                    self.command_events(command, identifier="discovery-1")
                    + exact_read_event
                )
        for command in malformed_read:
            with self.subTest(stage="read", command=command):
                self.assert_strict_probe_failure(
                    exact_discovery_event
                    + self.command_events(command, identifier="reader-1")
                )

    def test_host_shell_envelope_rejects_nonliteral_inner_scripts(self):
        owner = f"{REFERENCE_ROOT_RELATIVE}/apple-api-availability.md"
        exact_discovery = f"rg --files {REFERENCE_ROOT_RELATIVE}"
        exact_read = f"cat {owner}"
        exact_discovery_event = self.command_events(
            "/bin/bash -lc " + shlex.quote(exact_discovery),
            identifier="discovery-1",
        )
        exact_read_event = self.command_events(
            "/bin/zsh -lc " + shlex.quote(exact_read),
            identifier="reader-1",
        )
        nonliteral_discovery_scripts = (
            f"rg  --files {REFERENCE_ROOT_RELATIVE}",
            f"'rg' --files {REFERENCE_ROOT_RELATIVE}",
            f"rg --files '{REFERENCE_ROOT_RELATIVE}'",
        )
        nonliteral_read_scripts = (
            f"cat  {owner}",
            f"'cat' {owner}",
            f"cat '{owner}'",
        )
        for script in nonliteral_discovery_scripts:
            command = "/bin/bash -lc " + shlex.quote(script)
            with self.subTest(stage="discovery", script=script):
                self.assert_strict_probe_failure(
                    self.command_events(command, identifier="discovery-1")
                    + exact_read_event
                )
        for script in nonliteral_read_scripts:
            command = "/bin/zsh -lc " + shlex.quote(script)
            with self.subTest(stage="read", script=script):
                self.assert_strict_probe_failure(
                    exact_discovery_event
                    + self.command_events(command, identifier="reader-1")
                )

    def test_nested_mappings_argv_and_sibling_inputs_are_never_command_evidence(self):
        owner = f"{REFERENCE_ROOT_RELATIVE}/apple-api-availability.md"
        discovery = self.command_events(
            f"rg --files {REFERENCE_ROOT_RELATIVE}",
            identifier="discovery-1",
        )
        indirect_items = {
            "nested_mapping": self.tool_events(
                "mcp_tool_call",
                {"arguments": {"payload": {"command": f"cat {owner}"}}},
                identifier="reader-1",
            ),
            "stringified_mapping": self.tool_events(
                "mcp_tool_call",
                {"arguments": json.dumps({"command": f"cat {owner}"})},
                identifier="reader-1",
            ),
            "structured_argv": self.tool_events(
                "mcp_tool_call",
                {"arguments": {"argv": ["cat", owner]}},
                identifier="reader-1",
            ),
            "sibling_inputs": self.tool_events(
                "mcp_tool_call",
                {
                    "arguments": {
                        "command": f"cat {owner}",
                        "path": owner,
                    }
                },
                identifier="reader-1",
            ),
        }
        direct_with_sibling = self.command_events(
            f"cat {owner}",
            identifier="reader-1",
        )
        for event in direct_with_sibling:
            event["item"]["argv"] = ["cat", owner]
        indirect_items["command_item_sibling_argv"] = direct_with_sibling

        for name, read_events in indirect_items.items():
            with self.subTest(surface=name):
                self.assert_strict_probe_failure(discovery + read_events)

    def test_jsonl_rejects_duplicate_keys_and_non_standard_constants(self):
        rejected = {
            "duplicate_event_key": b'{"type":"turn.started","type":"turn.completed"}\n',
            "duplicate_item_key": (
                b'{"type":"item.started","item":{"id":"one","id":"two"}}\n'
            ),
            "nan": b'{"type":"turn.completed","value":NaN}\n',
            "positive_infinity": b'{"type":"turn.completed","value":Infinity}\n',
            "negative_infinity": b'{"type":"turn.completed","value":-Infinity}\n',
        }
        for name, payload in rejected.items():
            with self.subTest(jsonl=name):
                with self.assertRaises(ProbeFailure) as raised:
                    decode_json_lines(payload, "synthetic-case")
                self.assertEqual("invalid_jsonl", raised.exception.reason)

    def test_direct_rg_grep_are_rejected_as_alternative_read_commands(self):
        relative_owner = (
            f"{REFERENCE_ROOT_RELATIVE}/apple-api-availability.md"
        )
        absolute_owner = str(
            REFERENCE_ROOT / "apple-api-availability.md"
        )
        commands = {
            "rg_relative_n": (f"rg -n needle {relative_owner}", ROOT),
            "rg_absolute_e": (
                f"rg -e {shlex.quote('[;|&<>]')} {absolute_owner}",
                ROOT,
            ),
            "rg_fixed_double_dash": (
                f"rg --fixed-strings -- {shlex.quote('needle;|&')} "
                f"{relative_owner}",
                ROOT,
            ),
            "grep_relative_e": (
                f"grep -n -e needle {relative_owner}",
                ROOT,
            ),
            "grep_absolute_fixed": (
                f"grep -F -- {shlex.quote('needle[;]')} {absolute_owner}",
                ROOT,
            ),
            "grep_basename_from_owner_directory": (
                "grep -n needle apple-api-availability.md",
                REFERENCE_ROOT,
            ),
        }
        for surface in (
            "command_event",
            "nested_mapping",
            "json_string_arguments",
        ):
            for name, (command, cwd) in commands.items():
                with self.subTest(surface=surface, form=name):
                    self.assert_strict_probe_failure(
                        self.command_events(
                            f"rg --files {REFERENCE_ROOT_RELATIVE}",
                            identifier="discovery-1",
                        )
                        + self.direct_reader_events(
                            command,
                            surface=surface,
                            cwd=cwd,
                            identifier="reader-1",
                        )
                    )

    def test_direct_rg_grep_reject_ambiguous_operands_options_and_dataflow(self):
        owner = f"{REFERENCE_ROOT_RELATIVE}/apple-api-availability.md"
        other = f"{REFERENCE_ROOT_RELATIVE}/architecture-and-state.md"
        absolute_owner = str(
            REFERENCE_ROOT / "apple-api-availability.md"
        )
        rejected = {
            "owner_plus_dot": (f"rg needle {owner} .", ROOT),
            "explicit_directory": (
                f"rg needle {REFERENCE_ROOT_RELATIVE}",
                ROOT,
            ),
            "implicit_dot": ("rg needle .", REFERENCE_ROOT),
            "stdin": ("grep needle -", REFERENCE_ROOT),
            "glob": (f"rg needle {REFERENCE_ROOT_RELATIVE}/*.md", ROOT),
            "recursive": (f"grep -r needle {absolute_owner}", ROOT),
            "multiple_files": (f"rg needle {owner} {other}", ROOT),
            "duplicate_file": (f"grep needle {owner} {owner}", ROOT),
            "basename_as_pattern": (
                "rg apple-api-availability.md .",
                REFERENCE_ROOT,
            ),
            "basename_as_option_value": (
                "grep -e apple-api-availability.md architecture-and-state.md",
                REFERENCE_ROOT,
            ),
            "rg_pattern_file_short": (f"rg -f {owner} {other}", ROOT),
            "rg_pattern_file_long": (
                f"rg --file {owner} {other}",
                ROOT,
            ),
            "grep_pattern_file_short": (
                f"grep -f {owner} {other}",
                ROOT,
            ),
            "grep_pattern_file_long": (
                f"grep --file={owner} {other}",
                ROOT,
            ),
            "ignore_file_split": (
                f"rg --ignore-file {owner} needle {owner}",
                ROOT,
            ),
            "ignore_file_equals": (
                f"rg --ignore-file={owner} needle {owner}",
                ROOT,
            ),
            "pre_reader": (f"rg --pre {owner} needle {owner}", ROOT),
            "pre_glob": (
                f"rg --pre-glob {owner} needle {owner}",
                ROOT,
            ),
            "search_zip": (f"rg --search-zip needle {owner}", ROOT),
            "unknown_long_split": (f"rg --mystery needle {owner}", ROOT),
            "unknown_long_equals": (
                f"rg --mystery=value needle {owner}",
                ROOT,
            ),
            "unknown_short": (f"grep -Q needle {owner}", ROOT),
            "shell_wrapper": (
                "bash -c " + shlex.quote(f"rg needle {owner}"),
                ROOT,
            ),
            "pipeline": (f"rg needle {owner} | cat", ROOT),
            "redirection": (f"grep needle {owner} > /tmp/reference", ROOT),
        }
        expected_reasons = {
            "ambiguous_reference_read",
            "bulk_reference_content_read",
            "reference_directory_read",
        }
        for surface in (
            "command_event",
            "nested_mapping",
            "json_string_arguments",
        ):
            for name, (command, cwd) in rejected.items():
                with self.subTest(surface=surface, form=name):
                    self.assert_probe_failure_in(
                        self.direct_reader_events(
                            command,
                            surface=surface,
                            cwd=cwd,
                        ),
                        expected_reasons,
                    )

    def test_rg_files_discovery_rejects_closed_grammar_bypasses(self):
        reference_root = REFERENCE_ROOT_RELATIVE
        rejected = {
            "unknown_long_split": (
                f"rg --files --mystery value {reference_root}"
            ),
            "unknown_long_equals": (
                f"rg --files --mystery=value {reference_root}"
            ),
            "ignore_file_split": (
                f"rg --files --ignore-file /tmp/ignore {reference_root}"
            ),
            "ignore_file_equals": (
                f"rg --files --ignore-file=/tmp/ignore {reference_root}"
            ),
            "pre_reader": (
                f"rg --files --pre /tmp/helper {reference_root}"
            ),
            "pre_glob": (
                f"rg --files --pre-glob '*.md' {reference_root}"
            ),
            "search_zip": f"rg --files --search-zip {reference_root}",
            "pattern_file_short": (
                f"rg --files -f /tmp/patterns {reference_root}"
            ),
            "pattern_file_long": (
                f"rg --files --file /tmp/patterns {reference_root}"
            ),
        }
        for surface in (
            "command_event",
            "nested_mapping",
            "json_string_arguments",
        ):
            with self.subTest(surface=surface, form="exact_discovery"):
                self.assert_strict_probe_failure(
                    self.direct_reader_events(
                        f"rg --files {reference_root}",
                        surface=surface,
                        cwd=ROOT,
                    )
                )
            for name, command in rejected.items():
                with self.subTest(surface=surface, form=name):
                    self.assert_strict_probe_failure(
                        self.direct_reader_events(
                            command,
                            surface=surface,
                            cwd=ROOT,
                        ),
                    )

    def test_direct_searches_cannot_hide_implicit_reference_scope(self):
        owner = f"{REFERENCE_ROOT_RELATIVE}/apple-api-availability.md"
        implicit_bulk = {
            "implicit_repository_root": ("rg Apple", ROOT),
            "explicit_repository_dot": ("rg Apple .", ROOT),
            "recursive_repository_dot": ("grep -r Apple .", ROOT),
            "package_relative_reference_directory": (
                "rg Apple references",
                REFERENCE_ROOT.parent,
            ),
            "owner_parent_from_reference_root": ("rg Apple ..", REFERENCE_ROOT),
        }
        expected_reasons = {
            "ambiguous_reference_read",
            "bulk_reference_content_read",
            "reference_directory_read",
            "reference_path_outside_package",
        }
        for surface in (
            "command_event",
            "nested_mapping",
            "json_string_arguments",
        ):
            for name, (command, cwd) in implicit_bulk.items():
                with self.subTest(surface=surface, form=name):
                    self.assert_probe_failure_in(
                        self.direct_reader_events(
                            command,
                            surface=surface,
                            cwd=cwd,
                        ),
                        expected_reasons,
                    )

            with self.subTest(surface=surface, form="hidden_before_owner"):
                events = self.direct_reader_events(
                    "rg Apple .",
                    surface=surface,
                    cwd=ROOT,
                    identifier="bulk-1",
                ) + self.direct_reader_events(
                    f"rg -n needle {owner}",
                    surface=surface,
                    cwd=ROOT,
                    identifier="reader-1",
                )
                self.assert_probe_failure_in(events, expected_reasons)

    def test_reference_access_sequence_is_exactly_discovery_then_one_read(self):
        owner = f"{REFERENCE_ROOT_RELATIVE}/apple-api-availability.md"
        discovery = self.command_events(
            f"rg --files {REFERENCE_ROOT_RELATIVE}",
            identifier="discovery-1",
        )
        second_discovery = self.command_events(
            f"rg --files {REFERENCE_ROOT_RELATIVE}",
            identifier="discovery-2",
        )
        read = self.command_events(
            f"cat {owner}",
            identifier="reader-1",
        )

        self.assertEqual(
            {"apple-api-availability.md"},
            self.strict_observed(discovery + read),
        )
        invalid_sequences = {
            "read_without_discovery": read,
            "discovery_without_read": discovery,
            "duplicate_discovery": discovery + second_discovery + read,
            "read_before_discovery": read + discovery,
            "extra_discovery_after_read": discovery + read + second_discovery,
        }
        for name, events in invalid_sequences.items():
            with self.subTest(sequence=name):
                with self.assertRaises(ProbeFailure) as raised:
                    self.strict_observed(events)
                self.assertIn(
                    raised.exception.reason,
                    {"ambiguous_reference_read", "bulk_reference_content_read"},
                )

    def test_strict_reference_access_rejects_item_boundary_and_hidden_context_bypasses(
        self,
    ):
        owner = f"{REFERENCE_ROOT_RELATIVE}/apple-api-availability.md"
        discovery = self.command_events(
            f"rg --files {REFERENCE_ROOT_RELATIVE}",
            identifier="discovery-1",
        )
        targeted_read = self.command_events(
            f"cat {owner}",
            identifier="reader-1",
        )
        rejected = {
            "one_tool_item_combines_discovery_and_read": self.tool_events(
                "mcp_tool_call",
                {
                    "arguments": {
                        "steps": [
                            {
                                "command": f"rg --files {REFERENCE_ROOT_RELATIVE}",
                                "cwd": str(ROOT),
                            },
                            {
                                "command": f"sed -n '1,40p' {owner}",
                                "cwd": str(ROOT),
                            },
                        ]
                    }
                },
            ),
            "env_hides_reference_context_search": (
                discovery
                + self.command_events(
                    "env rg Apple .",
                    cwd=str(REFERENCE_ROOT),
                    identifier="hidden-1",
                )
                + targeted_read
            ),
            "glob_hides_reference_context_read": (
                discovery
                + self.command_events(
                    "cat *.md",
                    cwd=str(REFERENCE_ROOT),
                    identifier="hidden-1",
                )
                + targeted_read
            ),
            "structured_command_argv_is_not_recursively_flattened": (
                discovery
                + self.tool_events(
                    "mcp_tool_call",
                    {
                        "arguments": {
                            "payload": {
                                "command": ["rg", "needle", owner, "."],
                                "cwd": str(ROOT),
                            }
                        }
                    },
                    identifier="reader-1",
                )
            ),
        }
        for name, events in rejected.items():
            with self.subTest(bypass=name):
                with self.assertRaises(ProbeFailure):
                    observed_reference_reads(
                        events,
                        "synthetic-case",
                        require_exact_sequence=True,
                    )

    def test_json_tool_arguments_normalize_parse_failures_to_probe_failure(self):
        owner = f"{REFERENCE_ROOT_RELATIVE}/apple-api-availability.md"
        rejected = {
            "malformed": f'{{"path":"{owner}"',
            "duplicate_key": (
                f'{{"path":"{owner}","path":"{owner}"}}'
            ),
            "nan": f'{{"command":"cat {owner}","value":NaN}}',
            "positive_infinity": (
                f'{{"command":"cat {owner}","value":Infinity}}'
            ),
            "negative_infinity": (
                f'{{"command":"cat {owner}","value":-Infinity}}'
            ),
        }
        discovery = self.command_events(
            f"rg --files {REFERENCE_ROOT_RELATIVE}",
            identifier="discovery-1",
        )
        for name, arguments in rejected.items():
            with self.subTest(arguments=name):
                try:
                    self.strict_observed(
                        discovery
                        + self.tool_events(
                            "mcp_tool_call",
                            {"arguments": arguments},
                            identifier="reader-1",
                        ),
                    )
                except Exception as failure:
                    self.assertIsInstance(failure, ProbeFailure)
                else:
                    self.fail("invalid JSON tool arguments were accepted")

    def test_run_case_requires_the_exact_reference_access_sequence(self):
        completed = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=b'{"type":"turn.completed"}\n',
            stderr=b"",
        )
        strict_arguments: list[bool] = []

        def sequence_spy(
            events: list[dict[str, Any]],
            task_id: str,
            *,
            require_exact_sequence: bool = False,
        ) -> set[str]:
            strict_arguments.append(require_exact_sequence)
            raise ProbeFailure("sequence_checked", task_id)

        with (
            patch(f"{__name__}.subprocess.run", return_value=completed),
            patch(
                f"{__name__}.observed_reference_reads",
                side_effect=sequence_spy,
            ),
        ):
            with self.assertRaises(ProbeFailure) as raised:
                run_case(
                    "codex",
                    {},
                    "pattern-final-owner",
                    CASES["pattern-final-owner"],
                )
        self.assertEqual("sequence_checked", raised.exception.reason)
        self.assertEqual([True], strict_arguments)

    def test_nested_input_commands_are_not_exact_command_evidence(self):
        valid = "rg -n needle apple-api-availability.md"
        implicit_bulk = "rg Apple ."
        discovery = self.command_events(
            f"rg --files {REFERENCE_ROOT_RELATIVE}",
            identifier="discovery-1",
        )
        for as_json in (False, True):
            arguments: object = {
                "input": valid,
                "cwd": str(REFERENCE_ROOT),
            }
            if as_json:
                arguments = json.dumps(arguments)
            with self.subTest(json_string=as_json, form="valid_owner"):
                self.assert_strict_probe_failure(
                    discovery
                    + self.tool_events(
                            "mcp_tool_call",
                            {"arguments": arguments},
                            identifier="reader-1",
                        ),
                )

            bulk_arguments: object = {
                "input": implicit_bulk,
                "cwd": str(REFERENCE_ROOT),
            }
            if as_json:
                bulk_arguments = json.dumps(bulk_arguments)
            with self.subTest(json_string=as_json, form="implicit_bulk"):
                self.assert_strict_probe_failure(
                    discovery
                    + self.tool_events(
                        "mcp_tool_call",
                        {"arguments": bulk_arguments},
                        identifier="reader-1",
                    ),
                )

    def test_duplicate_direct_reader_invocations_fail_instead_of_set_deduplication(self):
        owner = f"{REFERENCE_ROOT_RELATIVE}/apple-api-availability.md"
        command = f"rg -n needle {owner}"
        for surface in (
            "command_event",
            "nested_mapping",
            "json_string_arguments",
        ):
            with self.subTest(surface=surface):
                events = self.direct_reader_events(
                    command,
                    surface=surface,
                    cwd=ROOT,
                    identifier="reader-1",
                ) + self.direct_reader_events(
                    command,
                    surface=surface,
                    cwd=ROOT,
                    identifier="reader-2",
                )
                self.assert_probe_failure_in(
                    events,
                    {"ambiguous_reference_read", "bulk_reference_content_read"},
                )

    def test_syntactically_valid_wrong_direct_reader_owner_is_selection_mismatch(self):
        wrong_owner = (
            f"{REFERENCE_ROOT_RELATIVE}/architecture-and-state.md"
        )
        events = self.command_events(
            f"rg --files {REFERENCE_ROOT_RELATIVE}",
            identifier="discovery-1",
        ) + self.command_events(
            f"cat {wrong_owner}",
            identifier="reader-1",
        )
        with self.assertRaises(ProbeFailure) as raised:
            observed = self.strict_observed(events)
            if observed != {"apple-api-availability.md"}:
                raise ProbeFailure(
                    "reference_selection_mismatch",
                    "synthetic-case",
                )
        self.assertEqual("reference_selection_mismatch", raised.exception.reason)

    def test_prior_authoritative_direct_reader_result_remains_failed(self):
        evidence = (
            ROOT
            / "docs/research/evidence/dev-137-reference-library-e2e.md"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "The newest two-call-prompt final-code `DEV137-CODEX-REF-001` run "
            "failed closed",
            evidence,
        )
        self.assertIn(
            "That newest result is authoritative and is not converted to a "
            "prerequisite blocker or pass.",
            " ".join(evidence.split()),
        )
        self.assertRegex(
            evidence,
            r"\| `DEV137-CODEX-REF-001` \| fail / "
            r"`bulk_reference_content_read` at `pattern-final-owner`;",
        )

    def test_prompt_requires_exact_command_forms_without_owner_hint(self):
        exact_discovery = f"rg --files {REFERENCE_ROOT_RELATIVE}"
        exact_read_template = "cat <one-approved-owner-path>"
        required_phrases = (
            "exactly two separate tool invocations",
            "first tool invocation",
            exact_discovery,
            "with no content read",
            "from the task semantics",
            "second tool invocation",
            exact_read_template,
            "Do not combine the directory listing and content read in one shell "
            "string or tool call",
            "pipes",
            "redirection",
            "command chaining",
            "command substitution",
            "xargs",
            "find -exec",
        )
        for task_id, case in CASES.items():
            prompt = build_prompt(task_id, case)
            with self.subTest(task_id=task_id):
                for phrase in required_phrases:
                    self.assertIn(phrase, prompt)
                self.assertEqual(1, prompt.count(exact_discovery))
                self.assertEqual(1, prompt.count(exact_read_template))
                self.assertLess(
                    prompt.index("first tool invocation"),
                    prompt.index("second tool invocation"),
                )
                self.assertNotIn("for example", prompt)
                for reference_name in REFERENCE_NAMES:
                    self.assertNotIn(reference_name, prompt)

    def test_semantic_owner_result_is_preserved_for_exact_access(self):
        events = self.exact_reference_access_events()
        self.assertEqual(
            {"apple-api-availability.md"},
            self.strict_observed(events),
        )

    def test_find_xargs_bulk_read_cannot_be_hidden_by_later_owner_read(self):
        owner = f"{REFERENCE_ROOT_RELATIVE}/apple-api-availability.md"
        command = (
            f"find {REFERENCE_ROOT_RELATIVE} -type f -print0 | "
            f"xargs -0 cat ; sed -n '1,40p' {owner}"
        )
        self.assert_probe_failure_in(
            self.command_events(command),
            {"ambiguous_reference_read", "bulk_reference_content_read"},
        )

    def test_redirected_file_list_read_cannot_be_hidden_by_owner_read(self):
        owner = f"{REFERENCE_ROOT_RELATIVE}/apple-api-availability.md"
        command = (
            f"ls {REFERENCE_ROOT_RELATIVE} > /tmp/refs ; "
            f"xargs cat < /tmp/refs ; sed -n '1,40p' {owner}"
        )
        self.assert_probe_failure_in(
            self.command_events(command),
            {"ambiguous_reference_read", "bulk_reference_content_read"},
        )

    def test_nested_mapping_rejects_indirect_reference_dataflow(self):
        owner = f"{REFERENCE_ROOT_RELATIVE}/apple-api-availability.md"
        commands = (
            (
                f"find {REFERENCE_ROOT_RELATIVE} -type f -print0 | "
                f"xargs -0 cat ; sed -n '1,40p' {owner}"
            ),
            (
                f"ls {REFERENCE_ROOT_RELATIVE} > /tmp/refs ; "
                f"xargs cat < /tmp/refs ; sed -n '1,40p' {owner}"
            ),
        )
        for index, command in enumerate(commands):
            nested = {"payload": {"cwd": str(ROOT), "command": command}}
            arguments: object = nested if index == 0 else json.dumps(nested)
            with self.subTest(command=command):
                self.assert_probe_failure_in(
                    self.tool_events("mcp_tool_call", {"arguments": arguments}),
                    {"ambiguous_reference_read", "bulk_reference_content_read"},
                )

    def test_shell_dataflow_operators_and_indirect_readers_fail_closed(self):
        owner = f"{REFERENCE_ROOT_RELATIVE}/apple-api-availability.md"
        commands = {
            "pipe": f"cat {owner} | wc -l",
            "output_redirection": f"cat {owner} > /tmp/reference-copy",
            "input_redirection": f"cat < {owner}",
            "semicolon": f"cat {owner} ; true",
            "and_if": f"cat {owner} && true",
            "or_if": f"cat {owner} || true",
            "subshell": f"cat $(find {REFERENCE_ROOT_RELATIVE} -type f)",
            "backtick": f"cat `find {REFERENCE_ROOT_RELATIVE} -type f`",
            "xargs": f"xargs cat {owner}",
            "find_exec": (
                f"find {REFERENCE_ROOT_RELATIVE} -type f -exec cat {{}} +"
            ),
        }
        for name, command in commands.items():
            with self.subTest(name=name):
                self.assert_probe_failure_in(
                    self.command_events(command),
                    {"ambiguous_reference_read", "bulk_reference_content_read"},
                )

    def test_shell_wrappers_with_post_script_operands_fail_closed(self):
        owner = f"{REFERENCE_ROOT_RELATIVE}/apple-api-availability.md"
        commands = {
            "bash_find_xargs": (
                "bash -c "
                + shlex.quote(
                    f"find {REFERENCE_ROOT_RELATIVE} -type f -print0 | "
                    "xargs -0 cat"
                )
                + " placeholder"
            ),
            "sh_glob": (
                "sh -c "
                + shlex.quote(f"cat {REFERENCE_ROOT_RELATIVE}/*.md")
                + " placeholder"
            ),
            "zsh_owner": (
                "zsh -lc "
                + shlex.quote(f"cat {owner}")
                + " placeholder"
            ),
        }
        for name, command in commands.items():
            with self.subTest(name=name):
                self.assert_probe_failure_in(
                    self.command_events(command),
                    {"ambiguous_reference_read", "bulk_reference_content_read"},
                )

    def test_absolute_shell_wrappers_reject_reference_operands_in_any_layout(self):
        owner = f"{REFERENCE_ROOT_RELATIVE}/apple-api-availability.md"
        commands = {
            "bash_split_options": (
                "/bin/bash -l -c "
                + shlex.quote(f"cat {owner}")
                + " placeholder extra"
            ),
            "sh_c": (
                "/bin/sh -c "
                + shlex.quote(f"sed -n '1,40p' {owner}")
                + " placeholder extra"
            ),
            "zsh_lc": (
                "/bin/zsh -lc "
                + shlex.quote(f"cat {REFERENCE_ROOT_RELATIVE}/*.md")
                + " placeholder extra"
            ),
        }
        for name, command in commands.items():
            with self.subTest(name=name):
                self.assert_probe_failure_in(
                    self.command_events(command),
                    {"ambiguous_reference_read", "bulk_reference_content_read"},
                )

    def test_shell_wrapper_reference_reads_fail_in_nested_tool_payloads(self):
        commands = (
            "bash -c "
            + shlex.quote(
                f"find {REFERENCE_ROOT_RELATIVE} -type f -print0 | "
                "xargs -0 cat"
            )
            + " placeholder",
            "sh -c "
            + shlex.quote(f"cat {REFERENCE_ROOT_RELATIVE}/*.md")
            + " placeholder",
            "zsh -lc "
            + shlex.quote(
                f"cat {REFERENCE_ROOT_RELATIVE}/apple-api-availability.md"
            )
            + " placeholder",
        )
        for index, command in enumerate(commands):
            nested = {"payload": {"cwd": str(ROOT), "command": command}}
            arguments: object = nested if index % 2 == 0 else json.dumps(nested)
            with self.subTest(command=command):
                self.assert_probe_failure_in(
                    self.tool_events("mcp_tool_call", {"arguments": arguments}),
                    {"ambiguous_reference_read", "bulk_reference_content_read"},
                )

    def test_shell_wrapper_cannot_hide_reference_in_cwd_or_positional_argument(self):
        positional_owner = str(REFERENCE_ROOT / "apple-api-availability.md")
        commands = (
            (
                "bash -c 'cat apple-api-availability.md' placeholder",
                str(REFERENCE_ROOT),
            ),
            (
                "sh -c 'cat \"$1\"' placeholder "
                + shlex.quote(positional_owner),
                str(ROOT),
            ),
        )
        for command, cwd in commands:
            with self.subTest(command=command):
                self.assert_probe_failure_in(
                    self.command_events(command, cwd=cwd),
                    {"ambiguous_reference_read", "bulk_reference_content_read"},
                )

    def test_unrelated_shell_activity_invalidates_the_exact_sequence(self):
        commands = (
            "bash -c 'printf okay' placeholder",
            "/bin/sh -lc 'pwd >/tmp/probe-pwd' placeholder",
            "zsh -c 'printf %s \"$1\"' placeholder unrelated",
        )
        for command in commands:
            with self.subTest(command=command):
                self.assert_strict_probe_failure(
                    self.exact_reference_access_events()
                    + self.command_events(command, identifier="extra-1")
                )

    def test_quoted_direct_search_is_still_an_alternative_reader(self):
        owner = f"{REFERENCE_ROOT_RELATIVE}/apple-api-availability.md"
        discovery = self.command_events(
            f"rg --files {REFERENCE_ROOT_RELATIVE}",
            identifier="discovery-1",
        )
        for pattern in ("[;|&<>]", "|", "&&", ">", "<", ";"):
            command = f"rg -n {shlex.quote(pattern)} {owner}"
            with self.subTest(pattern=pattern):
                self.assert_strict_probe_failure(
                    discovery
                    + self.command_events(command, identifier="reader-1")
                )

    def test_command_item_cwd_is_rejected_as_an_extra_schema_key(self):
        events = self.command_events(
            f"rg --files {REFERENCE_ROOT_RELATIVE}",
            identifier="discovery-1",
        ) + self.command_events(
            "cat apple-api-availability.md",
            cwd=str(REFERENCE_ROOT),
            identifier="reader-1",
        )
        self.assert_strict_probe_failure(events)

    def test_exact_cat_owner_outside_root_preserves_path_rejection(self):
        events = self.command_events(
            f"rg --files {REFERENCE_ROOT_RELATIVE}",
            identifier="discovery-1",
        ) + self.command_events(
            "cat /tmp/apple-api-availability.md",
            identifier="reader-1",
        )
        with self.assertRaises(ProbeFailure) as raised:
            self.strict_observed(events)
        self.assertEqual("reference_path_outside_package", raised.exception.reason)

    def test_command_item_sibling_context_cannot_differ_between_pair(self):
        events = self.exact_reference_access_events()
        events[2]["item"]["cwd"] = str(REFERENCE_ROOT)
        events[3]["item"]["cwd"] = "/tmp"
        self.assert_strict_probe_failure(events)

    def test_nested_mapping_cwd_is_not_command_evidence(self):
        arguments = {
            "payload": {
                "cwd": str(REFERENCE_ROOT),
                "command": "sed -n '1,40p' apple-api-availability.md",
            }
        }
        events = self.tool_events("mcp_tool_call", {"arguments": arguments})
        self.assert_strict_probe_failure(
            self.command_events(
                f"rg --files {REFERENCE_ROOT_RELATIVE}",
                identifier="discovery-1",
            )
            + events
        )

    def test_nested_mapping_outside_cwd_rejects_relative_owner(self):
        arguments = {
            "payload": {
                "cwd": "/tmp",
                "command": "sed -n '1,40p' apple-api-availability.md",
            }
        }
        events = self.tool_events("mcp_tool_call", {"arguments": arguments})
        self.assert_strict_probe_failure(
            self.command_events(
                f"rg --files {REFERENCE_ROOT_RELATIVE}",
                identifier="discovery-1",
            )
            + events
        )

    def test_json_string_tool_arguments_are_not_command_evidence(self):
        arguments = json.dumps(
            {"path": f"{REFERENCE_ROOT_RELATIVE}/apple-api-availability.md"}
        )
        events = self.tool_events("mcp_tool_call", {"arguments": arguments})
        self.assert_strict_probe_failure(
            self.command_events(
                f"rg --files {REFERENCE_ROOT_RELATIVE}",
                identifier="discovery-1",
            )
            + events
        )

    def test_failed_file_event_is_rejected(self):
        events = (
            self.command_events(
                f"rg --files {REFERENCE_ROOT_RELATIVE}",
                identifier="discovery-1",
            )
            + self.tool_events(
                "file_read",
                {"path": f"{REFERENCE_ROOT_RELATIVE}/apple-api-availability.md"},
                identifier="reader-1",
                completion_status="failed",
            )
        )
        self.assert_strict_probe_failure(events)

    def test_started_without_completion_is_rejected(self):
        events = self.exact_reference_access_events()[:-1]
        self.assert_strict_probe_failure(events)

    def test_completion_without_started_pair_is_rejected(self):
        events = self.exact_reference_access_events()
        events.pop(2)
        self.assert_strict_probe_failure(events)

    def test_failed_command_cannot_be_counted_as_a_read(self):
        owner = f"{REFERENCE_ROOT_RELATIVE}/apple-api-availability.md"
        events = self.command_events(
            f"rg --files {REFERENCE_ROOT_RELATIVE}",
            identifier="discovery-1",
        ) + self.command_events(
            f"cat {owner}",
            identifier="reader-1",
            completion_status="failed",
            exit_code=1,
        )
        self.assert_strict_probe_failure(events)

    def test_sibling_prefix_path_is_rejected(self):
        outside = f"{REFERENCE_ROOT_RELATIVE}-evil/apple-api-availability.md"
        events = self.command_events(
            f"rg --files {REFERENCE_ROOT_RELATIVE}",
            identifier="discovery-1",
        ) + self.command_events(f"cat {outside}", identifier="reader-1")
        with self.assertRaises(ProbeFailure) as raised:
            self.strict_observed(events)
        self.assertEqual("reference_path_outside_package", raised.exception.reason)

    def test_same_basename_outside_root_is_not_paired_with_root_substring(self):
        command = (
            f"cd {REFERENCE_ROOT_RELATIVE} && "
            "cat /tmp/apple-api-availability.md"
        )
        self.assert_probe_failure_in(
            self.command_events(command),
            {"ambiguous_reference_read", "bulk_reference_content_read"},
        )

    def test_parent_escape_is_rejected_after_path_resolution(self):
        escaped = (
            f"{REFERENCE_ROOT_RELATIVE}/../references-evil/"
            "apple-api-availability.md"
        )
        events = self.command_events(
            f"rg --files {REFERENCE_ROOT_RELATIVE}",
            identifier="discovery-1",
        ) + self.command_events(f"cat {escaped}", identifier="reader-1")
        with self.assertRaises(ProbeFailure) as raised:
            self.strict_observed(events)
        self.assertEqual("reference_path_outside_package", raised.exception.reason)

    def test_reference_directory_content_read_is_rejected(self):
        events = self.command_events(
            f"rg --files {REFERENCE_ROOT_RELATIVE}",
            identifier="discovery-1",
        ) + self.command_events(
            f"cat {REFERENCE_ROOT_RELATIVE}",
            identifier="reader-1",
        )
        with self.assertRaises(ProbeFailure) as raised:
            self.strict_observed(events)
        self.assertEqual("reference_directory_read", raised.exception.reason)

    def test_reference_glob_is_rejected_as_bulk_read(self):
        events = self.command_events(
            f"rg --files {REFERENCE_ROOT_RELATIVE}",
            identifier="discovery-1",
        ) + self.command_events(
            f"cat {REFERENCE_ROOT_RELATIVE}/*.md",
            identifier="reader-1",
        )
        with self.assertRaises(ProbeFailure) as raised:
            self.strict_observed(events)
        self.assertEqual("bulk_reference_content_read", raised.exception.reason)

    def test_unrelated_reference_read_is_rejected(self):
        command = (
            f"cat {REFERENCE_ROOT_RELATIVE}/apple-api-availability.md "
            f"{REFERENCE_ROOT_RELATIVE}/architecture-and-state.md"
        )
        with self.assertRaises(ProbeFailure) as raised:
            observed = self.strict_observed(
                self.command_events(
                    f"rg --files {REFERENCE_ROOT_RELATIVE}",
                    identifier="discovery-1",
                )
                + self.command_events(command, identifier="reader-1")
            )
            if observed != {"apple-api-availability.md"}:
                raise ProbeFailure("reference_selection_mismatch", "synthetic-case")
        self.assertEqual("reference_selection_mismatch", raised.exception.reason)

    def test_ls_directory_listing_is_not_exact_discovery_evidence(self):
        owner = f"{REFERENCE_ROOT_RELATIVE}/apple-api-availability.md"
        events = self.command_events(
            f"ls {REFERENCE_ROOT_RELATIVE}",
            identifier="discovery-1",
        ) + self.command_events(f"cat {owner}", identifier="reader-1")
        self.assert_strict_probe_failure(events)

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
