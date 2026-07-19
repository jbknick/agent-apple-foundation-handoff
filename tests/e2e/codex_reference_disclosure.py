from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import stat
import subprocess
import tempfile
from typing import Any, Iterator

try:
    from tests.e2e import codex_plugin_load as plugin_probe
except ModuleNotFoundError as import_failure:
    if import_failure.name not in {"tests", "tests.e2e"}:
        raise
    import codex_plugin_load as plugin_probe


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
REFERENCE_PATHS = {
    f"{REFERENCE_ROOT_RELATIVE}/{name}" for name in REFERENCE_NAMES
}
MODEL = "gpt-5.6-sol"
EVIDENCE_ID = "DEV137-CODEX-REF-001"
CLAIM_BOUNDARY = "optional_explicitly_directed_reference_selection_only"
BLOCKED_COMPLETION = "blocked/production_skills_not_integrated"
PINNED_PASSIVE_ITEM_KEYS = {
    "agent_message": {"id", "text", "type"},
    "reasoning": {"id", "text", "type"},
    "error": {"id", "message", "type"},
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
SHELL_WRAPPERS = {"bash", "sh", "zsh"}
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

metadata_snapshot = plugin_probe.metadata_snapshot
require_unchanged_host = plugin_probe.require_stable_host


@dataclass(frozen=True)
class ParsedDisclosure:
    reference_name: str
    reference_sha256: str
    result: str
    result_sha256: str

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


def _reference_owner(candidate: str, task_id: str) -> str:
    prefix = f"{REFERENCE_ROOT_RELATIVE}/"
    if not candidate.startswith(prefix):
        raise ProbeFailure("ambiguous_reference_read", task_id)
    owner = candidate.removeprefix(prefix)
    if owner not in REFERENCE_NAMES or "/" in owner:
        raise ProbeFailure("ambiguous_reference_read", task_id)
    try:
        resolved_root = REFERENCE_ROOT.resolve(strict=True)
        resolved_candidate = (ROOT / candidate).resolve(strict=True)
    except OSError:
        raise ProbeFailure("ambiguous_reference_read", task_id) from None
    if resolved_candidate.parent != resolved_root or resolved_candidate.name != owner:
        raise ProbeFailure("ambiguous_reference_read", task_id)
    return owner



def _disclosure_command(
    command: str,
    *,
    expect_discovery: bool,
    task_id: str,
) -> str | None:
    direct = command
    try:
        outer = shlex.split(command, posix=True)
    except ValueError:
        raise ProbeFailure("ambiguous_reference_read", task_id) from None
    if len(outer) == 3 and outer[1] == "-lc":
        shell = Path(outer[0])
        is_bare = len(shell.parts) == 1 and outer[0] in SHELL_WRAPPERS
        is_absolute = shell.is_absolute() and shell.name in SHELL_WRAPPERS
        if not (is_bare or is_absolute):
            raise ProbeFailure("ambiguous_reference_read", task_id)
        direct = outer[2]
        try:
            nested = shlex.split(direct, posix=True)
        except ValueError:
            raise ProbeFailure("ambiguous_reference_read", task_id) from None
        if len(nested) == 3 and nested[1] == "-lc":
            raise ProbeFailure("ambiguous_reference_read", task_id)

    discovery = f"rg --files {REFERENCE_ROOT_RELATIVE}"
    if expect_discovery:
        if direct != discovery:
            raise ProbeFailure("ambiguous_reference_read", task_id)
        return None

    try:
        tokens = shlex.split(direct, posix=True)
    except ValueError:
        raise ProbeFailure("ambiguous_reference_read", task_id) from None
    if len(tokens) != 2 or tokens[0] != "cat":
        raise ProbeFailure("ambiguous_reference_read", task_id)
    owner = _reference_owner(tokens[1], task_id)
    if direct != f"cat {REFERENCE_ROOT_RELATIVE}/{owner}":
        raise ProbeFailure("ambiguous_reference_read", task_id)
    return owner


def _validate_discovery_output(output: str, task_id: str) -> None:
    if not output or "\r" in output:
        raise ProbeFailure("invalid_reference_discovery_output", task_id)
    lines = output.split("\n")
    if lines[-1] == "":
        lines.pop()
    if (
        len(lines) != len(REFERENCE_PATHS)
        or any(not line for line in lines)
        or len(set(lines)) != len(lines)
        or set(lines) != REFERENCE_PATHS
    ):
        raise ProbeFailure("invalid_reference_discovery_output", task_id)


def _parse_result_text(text: str, task_id: str) -> str:
    try:
        parsed = json.loads(
            text,
            object_pairs_hook=pairs_without_duplicates,
            parse_constant=reject_json_constant,
        )
    except (json.JSONDecodeError, ValueError):
        raise ProbeFailure("malformed_bounded_result", task_id) from None
    if not isinstance(parsed, dict) or set(parsed) != {"result"}:
        raise ProbeFailure("malformed_bounded_result", task_id)
    result = parsed.get("result")
    if not isinstance(result, str) or not result:
        raise ProbeFailure("malformed_bounded_result", task_id)
    return result


def parse_disclosure_events(
    events: list[dict[str, Any]], task_id: str
) -> ParsedDisclosure:
    """Parse the one closed Codex disclosure action sequence.

    Non-action thread/turn envelopes and schema-pinned reasoning may surround the
    sequence, but the only actions are discovery, one source read, and one final
    top-level agent message in that order.
    """

    logical_ids: set[str] = set()
    pending: tuple[str, str, bool] | None = None
    command_count = 0
    owner: str | None = None
    reference_sha256: str | None = None
    message_text: str | None = None
    inspected_text: list[str] = []
    seen_thread_started = False
    seen_turn_started = False
    seen_turn_completed = False

    for event in events:
        if not isinstance(event, dict):
            raise ProbeFailure("ambiguous_reference_read", task_id)
        event_type = event.get("type")
        if "item" not in event:
            if event_type == "thread.started":
                if (
                    seen_thread_started
                    or seen_turn_started
                    or command_count
                    or set(event) != {"thread_id", "type"}
                    or not isinstance(event.get("thread_id"), str)
                    or not event.get("thread_id")
                ):
                    raise ProbeFailure("ambiguous_reference_read", task_id)
                seen_thread_started = True
                continue
            if event_type == "turn.started":
                if seen_turn_started or command_count or set(event) != {"type"}:
                    raise ProbeFailure("ambiguous_reference_read", task_id)
                seen_turn_started = True
                continue
            if event_type == "turn.completed":
                if (
                    seen_turn_completed
                    or message_text is None
                    or set(event) not in ({"type"}, {"type", "usage"})
                    or (
                        "usage" in event
                        and not isinstance(event.get("usage"), dict)
                    )
                ):
                    raise ProbeFailure("terminal_event_failed", task_id)
                seen_turn_completed = True
                continue
            raise ProbeFailure(
                "terminal_event_failed"
                if event_type in {"error", "turn.failed"}
                else "ambiguous_reference_read",
                task_id,
            )

        if set(event) != COMMAND_EVENT_KEYS or event_type not in {
            "item.started",
            "item.completed",
        }:
            raise ProbeFailure("ambiguous_reference_read", task_id)
        item = event.get("item")
        if not isinstance(item, dict):
            raise ProbeFailure("ambiguous_reference_read", task_id)
        item_type = item.get("type")

        if item_type == "reasoning":
            if (
                event_type != "item.completed"
                or set(item) != PINNED_PASSIVE_ITEM_KEYS["reasoning"]
                or pending is not None
                or message_text is not None
                or not isinstance(item.get("id"), str)
                or not item.get("id")
                or item["id"] in logical_ids
                or not isinstance(item.get("text"), str)
            ):
                raise ProbeFailure("ambiguous_reference_read", task_id)
            logical_ids.add(item["id"])
            inspected_text.append(item["text"])
            continue

        if item_type == "error":
            raise ProbeFailure("passive_error_event", task_id)
        if item_type == "agent_message":
            if (
                event_type != "item.completed"
                or set(item) != PINNED_PASSIVE_ITEM_KEYS["agent_message"]
                or command_count != 2
                or pending is not None
                or message_text is not None
                or not isinstance(item.get("id"), str)
                or not item.get("id")
                or item["id"] in logical_ids
                or not isinstance(item.get("text"), str)
            ):
                raise ProbeFailure("malformed_bounded_result", task_id)
            logical_ids.add(item["id"])
            message_text = item["text"]
            inspected_text.append(message_text)
            continue
        if item_type != "command_execution":
            raise ProbeFailure("unexpected_action_event", task_id)
        if message_text is not None or seen_turn_completed or set(item) != COMMAND_ITEM_KEYS:
            raise ProbeFailure("unexpected_action_event", task_id)

        identifier = item.get("id")
        command = item.get("command")
        if not isinstance(identifier, str) or not identifier or not isinstance(command, str):
            raise ProbeFailure("ambiguous_reference_read", task_id)

        if event_type == "item.started":
            if (
                pending is not None
                or command_count >= 2
                or identifier in logical_ids
                or not command
                or item.get("status") != "in_progress"
                or item.get("exit_code") is not None
                or item.get("aggregated_output") != ""
            ):
                raise ProbeFailure("ambiguous_reference_read", task_id)
            is_discovery = command_count == 0
            _disclosure_command(
                command,
                expect_discovery=is_discovery,
                task_id=task_id,
            )
            logical_ids.add(identifier)
            pending = (identifier, command, is_discovery)
            continue

        if (
            pending is None
            or pending[:2] != (identifier, command)
            or item.get("status") != "completed"
            or type(item.get("exit_code")) is not int
            or item.get("exit_code") != 0
            or not isinstance(item.get("aggregated_output"), str)
        ):
            raise ProbeFailure(
                "command_execution_failed"
                if item.get("status") != "completed" or item.get("exit_code") != 0
                else "ambiguous_reference_read",
                task_id,
            )

        is_discovery = pending[2]
        output = item["aggregated_output"]
        parsed_owner = _disclosure_command(
            command,
            expect_discovery=is_discovery,
            task_id=task_id,
        )
        if is_discovery:
            _validate_discovery_output(output, task_id)
        else:
            if not output or parsed_owner is None:
                raise ProbeFailure("invalid_reference_read_output", task_id)
            try:
                source_bytes = plugin_probe.read_regular_file(
                    REFERENCE_ROOT / parsed_owner,
                    "reference_source_changed",
                )
            except plugin_probe.ProbeFailure as failure:
                raise ProbeFailure(failure.reason, task_id) from None
            try:
                output_bytes = output.encode("utf-8", errors="strict")
            except UnicodeEncodeError:
                raise ProbeFailure("invalid_reference_read_output", task_id) from None
            if output_bytes != source_bytes:
                raise ProbeFailure("invalid_reference_read_output", task_id)
            owner = parsed_owner
            reference_sha256 = hashlib.sha256(source_bytes).hexdigest()
        command_count += 1
        pending = None

    if pending is not None or command_count != 2 or owner is None or message_text is None:
        raise ProbeFailure("missing_bounded_result", task_id)
    if task_id == "fictional-transfer-baton-api" and any(
        pattern.search(text)
        for text in inspected_text
        for pattern in FICTIONAL_SIGNATURE_PATTERNS
    ):
        raise ProbeFailure("invented_fictional_api_signature", task_id)
    result = _parse_result_text(message_text, task_id)
    assert reference_sha256 is not None
    return ParsedDisclosure(
        reference_name=owner,
        reference_sha256=reference_sha256,
        result=result,
        result_sha256=sha256_text(message_text),
    )


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
    parsed = parse_disclosure_events(events, task_id)
    observed = {parsed.reference_name}
    expected = set(case["expectedReferences"])
    if observed != expected:
        raise ProbeFailure("reference_selection_mismatch", task_id)

    if parsed.result != case["expectedResult"]:
        raise ProbeFailure("semantic_result_mismatch", task_id)
    return {
        "expectedReferences": sorted(expected),
        "observedReferences": sorted(observed),
        "referenceSha256": parsed.reference_sha256,
        "resultClassification": parsed.result,
        "resultSha256": parsed.result_sha256,
        "taskId": task_id,
        "taskSha256": sha256_text(prompt),
    }


def capture_host() -> tuple[
    str,
    Path,
    Path,
    plugin_probe.HostSnapshot,
    dict[str, str],
]:
    search_path = os.environ.get("PATH")
    if search_path is None:
        raise ProbeBlocked("missing_binary_or_version_mismatch")
    environment = {"PATH": search_path}
    host = shutil.which("codex", path=search_path)
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
    executable = str(initial_resolution)
    snapshot = metadata_snapshot(metadata)
    try:
        version_matches = plugin_probe.stable_host_version_matches(
            executable,
            locator,
            initial_resolution,
            snapshot,
            environment,
        )
    except plugin_probe.ProbeFailure as failure:
        raise ProbeFailure(failure.reason) from None
    if not version_matches:
        raise ProbeBlocked("missing_binary_or_version_mismatch")
    return executable, locator, initial_resolution, snapshot, environment


@contextmanager
def prepare_isolated_plugin(
    executable: str,
    locator: Path,
    initial_resolution: Path,
    initial_snapshot: plugin_probe.HostSnapshot,
    base_environment: dict[str, str],
) -> Iterator[dict[str, str]]:
    with tempfile.TemporaryDirectory() as directory:
        codex_home = Path(directory).resolve(strict=True)
        environment = dict(base_environment)
        environment["CODEX_HOME"] = str(codex_home)
        installed_path: Path | None = None
        try:
            require_unchanged_host(
                executable,
                locator,
                initial_resolution,
                initial_snapshot,
                environment,
            )
            installed_path = plugin_probe.install_isolated_plugin(
                executable,
                environment,
                codex_home,
            )
            require_unchanged_host(
                executable,
                locator,
                initial_resolution,
                initial_snapshot,
                environment,
            )
            plugin_probe.require_source_cache_identity(installed_path)
            yield environment
        except plugin_probe.ProbeFailure as failure:
            raise ProbeFailure(failure.reason) from None
        finally:
            try:
                if installed_path is not None:
                    plugin_probe.require_source_cache_identity(installed_path)
                require_unchanged_host(
                    executable,
                    locator,
                    initial_resolution,
                    initial_snapshot,
                    environment,
                )
            except plugin_probe.ProbeFailure as failure:
                raise ProbeFailure(failure.reason) from None


def main() -> int:
    try:
        (
            executable,
            locator,
            initial_resolution,
            initial_snapshot,
            environment,
        ) = capture_host()
    except ProbeBlocked as failure:
        emit_result(blocked_payload(failure.reason, failure.attempted_case_count))
        return 2
    except ProbeFailure as failure:
        emit_result(failed_payload(failure))
        return 1

    case_results: list[dict[str, Any]] = []
    terminal_status = 1
    terminal_payload: dict[str, Any]
    try:
        with prepare_isolated_plugin(
            executable,
            locator,
            initial_resolution,
            initial_snapshot,
            environment,
        ) as isolated_environment:
            for task_id, case in CASES.items():
                require_unchanged_host(
                    executable,
                    locator,
                    initial_resolution,
                    initial_snapshot,
                    isolated_environment,
                )
                try:
                    case_results.append(
                        run_case(
                            executable,
                            isolated_environment,
                            task_id,
                            case,
                        )
                    )
                finally:
                    require_unchanged_host(
                        executable,
                        locator,
                        initial_resolution,
                        initial_snapshot,
                        isolated_environment,
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
                initial_snapshot,
                environment,
            )
        except Exception:
            terminal_status = 1
            terminal_payload = failed_payload(
                ProbeFailure("host_resolution_or_version_drift")
            )
    emit_result(terminal_payload)
    return terminal_status




if __name__ == "__main__":
    raise SystemExit(main())
