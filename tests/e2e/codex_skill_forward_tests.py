#!/usr/bin/env python3
"""Closed, privacy-preserving DEV-136 Codex forward-test runner."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import secrets
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable


PASS = 0
FAIL = 1
BLOCKED = 2
EXPECTED_MODEL = "gpt-5.6-sol"
EXPECTED_CODEX_VERSION = "0.144.5"

ROOT = Path(__file__).resolve().parents[2]
CANONICAL_FIXTURE = ROOT / "tests/fixtures/dev-136-codex-skill-cases.json"
OFFICIAL_FIXTURE_SHA256 = (
    "6c5bd8dafb1b75990e88ec288de18282c00b99151f33a7566253395c4ef93dcb"
)

ASSERTIONS = (
    "activation",
    "routing",
    "one_clarification",
    "review_first_ordering",
    "independent_version_labels",
    "common_sections",
    "workflow_sections",
)
STATUSES = {"pass", "fail", "blocked", "not_applicable"}
EARLY_STOP_REASONS = {
    "event_stream_invalid",
    "post_capture_prerequisite_drift",
    "process_failed",
    "scoring_failed",
}
PRE_RESPONSE_REASONS = {
    "fixture_contract_invalid",
    "missing_binary",
    "nonregular_binary",
    "nonexecutable_binary",
    "version_mismatch",
    "authentication_unavailable",
    "model_unavailable",
    "plugin_activation_unavailable",
    "model_mismatch",
}
EVIDENCE_KEYS = {
    "schemaVersion", "sourceIssue", "evidenceKind", "mode", "status",
    "model", "codexVersion", "fixtureSha256", "host", "privacy",
    "summary", "cases",
}
HOST_KEYS = {
    "name", "version", "model", "modelSelection", "sessionMode",
    "resolvedExecutableSha256", "prerequisites", "blockerReason",
    "claudeInvoked",
}
PREREQUISITE_KEYS = {
    "binary", "version", "authentication", "model", "pluginActivation",
    "discovery", "installation",
}
SUMMARY_KEYS = {
    "fixtureCaseCount", "attemptedCount", "passedCount", "failedCount",
    "blockedCount", "notApplicableCount",
}
ROW_KEYS = {
    "caseId", "skillUnderTest", "sessionOrdinal", "promptSha256",
    "rubricContractSha256", "codexExitCode", "responseSha256",
    "responseBytes", "toolEventCount", "verdict", "assertions",
}
OBSERVATION_KEYS = {
    "provenance", "responseSha256", "responseBytes", "toolEventCount",
    "assertions",
}
HOST_RESULT_KEYS = {
    "codexExitCode", "responseSha256", "responseBytes", "toolEventCount",
}
PRIVACY = {
    "rawPrompts": "transient_not_committed",
    "rawResponses": "transient_not_committed",
    "rawToolEvents": "transient_not_committed",
    "committedEvidence": "normalized_metadata_and_sha256_only",
    "offlineScorerOutputs": "approved_synthetic_or_redacted_only",
    "expectedAnswersIncludedInPrompts": False,
}
FORBIDDEN_KEYS = {
    "command", "events", "outputPath", "prompt", "rawPrompt", "rawReasoning",
    "rawResponse", "resolvedExecutable", "response",
    "transcript",
}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ABSOLUTE_PATH_RE = re.compile(
    r"(?<![A-Za-z0-9_.-])/(?:[A-Za-z0-9._-]+/)*[A-Za-z0-9._-]+"
)
PRIVATE_VALUE_RES = (
    ABSOLUTE_PATH_RE,
    re.compile(r"[A-Za-z]:\\"),
    re.compile(r"(?i)\bbearer\s+[a-z0-9._~+/-]{8,}"),
    re.compile(r"\b(?:sk|pk)-[A-Za-z0-9_-]{8,}"),
)

COMMON_SECTIONS = (
    "Activation and Scope", "Pattern and Ownership", "Apple API Availability",
    "State and Lifecycle", "Trust and Model Boundaries", "Context Policy",
    "Tools Effects and Confirmation", "Failure Recovery and Fallback",
    "Verification and Evidence", "Limitations",
)
WORKFLOW_SECTIONS = {
    "design-apple-foundation-models-handoff": (
        "Alternatives", "Decision Rationale", "Proposed Components",
        "Implementation and Test Plan",
    ),
    "implement-apple-foundation-models-handoff": (
        "Approved Decision", "Change Boundary", "Changed Paths",
        "Compilation and Regression Results",
    ),
    "review-apple-foundation-models-handoff": ("Findings",),
    "debug-apple-foundation-models-handoff": (
        "Observed and Expected State", "First Divergence", "Root Cause",
        "Correction", "Regression Proof",
    ),
    "validate-apple-foundation-models-handoff": (
        "Layer Matrix", "Counts and Hashes", "Rubric Result",
        "Blockers and Skips", "Release Implication",
    ),
}
PLUGIN_ID = "apple-foundation-models-handoff"
MARKETPLACE_NAME = "agent-apple-foundation-handoff"
PLUGIN_SELECTOR = f"{PLUGIN_ID}@{MARKETPLACE_NAME}"
PLUGIN_ENTRY_KEYS = {
    "pluginId", "name", "marketplaceName", "version", "installed",
    "enabled", "source", "marketplaceSource", "installPolicy", "authPolicy",
}
SKILL_PAYLOAD_SHA256 = {
    "design-apple-foundation-models-handoff": (
        "825a25382785d50e512eab5bda8bd314804289c808111f30df2fba07dd668e39"
    ),
    "implement-apple-foundation-models-handoff": (
        "59bba3f47bc954f2c623709cfc6f11cb358f10fff83ac497d2ce61f845c577e9"
    ),
    "review-apple-foundation-models-handoff": (
        "15c7e81f59f7010f6b80462aa082c1e3895e4d037914eff068cd339550d06a37"
    ),
    "debug-apple-foundation-models-handoff": (
        "ea437fcb5ba8a3d88da6008ed86f802385298648dc81a4e5db4d8c7047353024"
    ),
    "validate-apple-foundation-models-handoff": (
        "bef0e5d0bf38ecccda8fce26d3eddf1230765d0bb7e19286b0ec9fd0bebfe36c"
    ),
}
CODEX_JSONL_EVENT_TYPES = {
    "thread.started", "turn.started", "turn.completed", "turn.failed",
    "item.started", "item.updated", "item.completed", "error",
}
CODEX_JSONL_ITEM_TYPES = {
    "agent_message", "reasoning", "command_execution", "file_change",
    "mcp_tool_call", "collab_tool_call", "web_search", "todo_list", "error",
}
CODEX_JSONL_TOOL_ITEM_TYPES = {
    "command_execution", "file_change", "mcp_tool_call", "collab_tool_call",
    "web_search",
}
CODEX_JSONL_ITEM_EVENT_TYPES = {
    "agent_message": {"item.completed"},
    "reasoning": {"item.completed"},
    "command_execution": {"item.started", "item.completed"},
    "file_change": {"item.completed"},
    "mcp_tool_call": {"item.started", "item.completed"},
    "collab_tool_call": {"item.started", "item.completed"},
    "web_search": {"item.started", "item.completed"},
    "todo_list": {"item.started", "item.updated", "item.completed"},
    "error": {"item.completed"},
}
CODEX_JSONL_PAIRED_ITEM_TYPES = {
    "command_execution", "mcp_tool_call", "collab_tool_call", "web_search",
    "todo_list",
}
CODEX_JSONL_IMMUTABLE_IDENTITY_FIELDS = {
    "command_execution": ("command",),
    "mcp_tool_call": ("server", "tool", "arguments"),
    "collab_tool_call": (
        "tool", "sender_thread_id", "receiver_thread_ids", "prompt",
    ),
}
CODEX_JSONL_WEB_SEARCH_INNER_ID = "_codex_web_search_inner_id"

TRUSTED_SYSTEM_PATH_ALIASES = {
    Path("/var"): Path("/private/var"),
    Path("/tmp"): Path("/private/tmp"),
}


class ExecutableCaptureError(ValueError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _compact_sha256(value: Any) -> str:
    return _sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )


def _json_type_exact_equal(left: Any, right: Any) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(
            _json_type_exact_equal(left[key], right[key]) for key in left
        )
    if isinstance(left, list):
        return len(left) == len(right) and all(
            _json_type_exact_equal(left_value, right_value)
            for left_value, right_value in zip(left, right)
        )
    return left == right


def _fixture_contract() -> dict[str, Any]:
    raw = CANONICAL_FIXTURE.read_bytes()
    if _sha256(raw) != OFFICIAL_FIXTURE_SHA256:
        raise ValueError("canonical fixture identity mismatch")
    value = _strict_json_loads(raw)
    if not isinstance(value, dict):
        raise ValueError("canonical fixture must be an object")
    return value


def _validate_fixture(fixture: dict[str, Any], fixture_bytes: bytes) -> None:
    if type(fixture) is not dict or type(fixture_bytes) is not bytes:
        raise ValueError("fixture and exact fixture bytes are required")
    try:
        decoded = _strict_json_loads(fixture_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("fixture bytes are not valid JSON") from error
    if decoded != fixture:
        raise ValueError("fixture bytes do not encode the supplied fixture")

    official = _fixture_contract()
    if set(fixture) != set(official):
        raise ValueError("fixture schema is not closed")
    for key, expected in official.items():
        if key not in {"cases", "caseCount"} and fixture[key] != expected:
            raise ValueError(f"fixture metadata drift: {key}")
    cases = fixture["cases"]
    if type(cases) is not list or type(fixture["caseCount"]) is not int:
        raise ValueError("fixture case collection is malformed")
    if fixture["caseCount"] != len(cases):
        raise ValueError("fixture case count mismatch")
    official_cases = official["cases"]
    official_by_id = {case["id"]: case for case in official_cases}
    official_positions = {case["id"]: index for index, case in enumerate(official_cases)}
    positions: list[int] = []
    for case in cases:
        if type(case) is not dict or type(case.get("id")) is not str:
            raise ValueError("fixture case identity is malformed")
        case_id = case["id"]
        if case_id not in official_by_id or case != official_by_id[case_id]:
            raise ValueError(f"unapproved fixture case: {case_id}")
        positions.append(official_positions[case_id])
    if positions != sorted(set(positions)):
        raise ValueError("fixture cases are duplicated or out of approved order")


def _validate_nonnegative_int(value: Any, label: str) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{label} must be a nonnegative integer")


def _validate_hash(value: Any, label: str, *, nullable: bool = False) -> None:
    if nullable and value is None:
        return
    if type(value) is not str or SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{label} must be a lowercase SHA-256")


def _validate_observation(observation: dict[str, Any]) -> None:
    if type(observation) is not dict or set(observation) != OBSERVATION_KEYS:
        raise ValueError("scorer observation schema is not closed")
    if observation["provenance"] not in {"approved_synthetic", "approved_redacted"}:
        raise ValueError("scorer observation provenance is not approved")
    _validate_hash(observation["responseSha256"], "responseSha256")
    _validate_nonnegative_int(observation["responseBytes"], "responseBytes")
    _validate_nonnegative_int(observation["toolEventCount"], "toolEventCount")
    assertions = observation["assertions"]
    if type(assertions) is not dict or set(assertions) != set(ASSERTIONS):
        raise ValueError("scorer assertions schema is not closed")
    if any(type(value) is not str or value not in STATUSES for value in assertions.values()):
        raise ValueError("scorer assertion status is invalid")


def _derived_status(statuses: list[str]) -> str:
    for status in ("fail", "blocked", "pass"):
        if status in statuses:
            return status
    return "not_applicable"


def score_case(case: dict[str, Any], observation: dict[str, Any]) -> dict[str, Any]:
    if type(case) is not dict:
        raise ValueError("case must be an object")
    _validate_observation(observation)
    assertions = copy.deepcopy(observation["assertions"])
    return {"assertions": assertions, "verdict": _derived_status(list(assertions.values()))}


def _rubric_hash(fixture: dict[str, Any], case: dict[str, Any]) -> str:
    name = case["rubricContract"]
    return _compact_sha256({"name": name, "checks": fixture["rubricContracts"][name]})


def _prerequisite_statuses(
    snapshot: dict[str, Any] | None,
    blocker: str | None,
    *,
    activation_proven: bool = False,
) -> dict[str, str]:
    if snapshot is None:
        values = {key: "not_applicable" for key in PREREQUISITE_KEYS}
        if blocker == "model_mismatch":
            values["model"] = "blocked"
        elif blocker == "version_mismatch":
            values["version"] = "blocked"
        return values
    values = {
        "binary": "pass" if snapshot.get("resolvedExecutable") and snapshot.get("executableSha256") else "blocked",
        "version": "pass" if snapshot.get("version") == EXPECTED_CODEX_VERSION else "blocked",
        "authentication": "pass" if snapshot.get("authenticated") is True else "blocked",
        "model": (
            "pass" if snapshot.get("modelAvailable") is True
            else "blocked" if snapshot.get("modelAvailable") is False
            else "not_applicable"
        ),
        "pluginActivation": (
            "pass" if snapshot.get("pluginAvailable") is True and activation_proven
            else "not_applicable" if snapshot.get("pluginAvailable") is True
            else "blocked"
        ),
        "discovery": snapshot.get("discovery", "blocked"),
        "installation": snapshot.get("installation", "blocked"),
    }
    if blocker in {"nonregular_binary", "nonexecutable_binary"}:
        values["binary"] = "blocked"
    if blocker == "model_unavailable":
        values["model"] = "blocked"
    return values


def _evidence_prerequisite_statuses(
    mode: str,
    blocker: str | None,
    executable_sha256: str | None,
    *,
    activation_proven: bool,
) -> dict[str, str]:
    """Derive committed prerequisite facts only from committed evidence facts."""
    values = {key: "not_applicable" for key in PREREQUISITE_KEYS}
    if blocker == "fixture_contract_invalid":
        return values
    if mode == "offline":
        if blocker == "model_mismatch":
            values["model"] = "blocked"
        elif blocker == "version_mismatch":
            values["version"] = "blocked"
        return values

    has_identity = executable_sha256 is not None
    if blocker in {"missing_binary", "nonregular_binary", "nonexecutable_binary"}:
        values["binary"] = "blocked"
        return values
    if blocker == "model_mismatch":
        values["model"] = "blocked"
        return values
    if blocker == "version_mismatch":
        values["binary"] = "pass" if has_identity else "not_applicable"
        values["version"] = "blocked"
        return values

    values["binary"] = "pass" if has_identity else "blocked"
    values["version"] = "pass"
    if blocker == "authentication_unavailable":
        values["authentication"] = "blocked"
        return values

    values["authentication"] = "pass"
    if blocker == "plugin_activation_unavailable":
        values["pluginActivation"] = "blocked"
        values["discovery"] = "blocked"
        values["installation"] = "blocked"
        return values

    values["discovery"] = "pass"
    values["installation"] = "pass"
    if blocker == "model_unavailable":
        values["model"] = "blocked"
        return values
    if blocker in {"event_stream_invalid", "scoring_failed"} or blocker is None:
        values["model"] = "pass"
    if blocker is None and activation_proven:
        values["pluginActivation"] = "pass"
    return values


def _host_metadata(
    mode: str,
    snapshot: dict[str, Any] | None = None,
    blocker: str | None = None,
    *,
    activation_proven: bool = False,
) -> dict[str, Any]:
    executable_sha256 = None if snapshot is None else snapshot.get("executableSha256")
    return {
        "name": "codex",
        "version": EXPECTED_CODEX_VERSION,
        "model": EXPECTED_MODEL,
        "modelSelection": "explicit_cli_argument",
        "sessionMode": "fresh_ephemeral" if mode == "host" else "not_applicable",
        "resolvedExecutableSha256": executable_sha256,
        "prerequisites": _evidence_prerequisite_statuses(
            mode,
            blocker,
            executable_sha256,
            activation_proven=activation_proven,
        ),
        "blockerReason": blocker,
        "claudeInvoked": False,
    }


def _summary(fixture: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, int]:
    verdicts = [row["verdict"] for row in rows]
    return {
        "fixtureCaseCount": len(fixture["cases"]),
        "attemptedCount": len(rows),
        "passedCount": verdicts.count("pass"),
        "failedCount": verdicts.count("fail"),
        "blockedCount": verdicts.count("blocked"),
        "notApplicableCount": verdicts.count("not_applicable"),
    }


def _evidence(
    mode: str,
    fixture: dict[str, Any],
    fixture_bytes: bytes,
    rows: list[dict[str, Any]],
    *,
    snapshot: dict[str, Any] | None = None,
    blocker: str | None = None,
    forced_status: str | None = None,
) -> dict[str, Any]:
    status = forced_status or _derived_status([row["verdict"] for row in rows])
    activation_proven = (
        mode == "host"
        and blocker is None
        and bool(rows)
        and len(rows) == len(fixture["cases"])
        and all(row["assertions"]["activation"] == "pass" for row in rows)
    )
    return {
        "schemaVersion": "1.0",
        "sourceIssue": "DEV-136",
        "evidenceKind": "codex_skill_forward_test",
        "mode": mode,
        "status": status,
        "model": EXPECTED_MODEL,
        "codexVersion": EXPECTED_CODEX_VERSION,
        "fixtureSha256": _sha256(fixture_bytes),
        "host": _host_metadata(
            mode, snapshot, blocker, activation_proven=activation_proven
        ),
        "privacy": copy.deepcopy(PRIVACY),
        "summary": _summary(fixture, rows),
        "cases": rows,
    }


def _row(
    fixture: dict[str, Any],
    case: dict[str, Any],
    ordinal: int,
    observation: dict[str, Any],
    host_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    scored = score_case(case, observation)
    source = observation if host_result is None else host_result
    return {
        "caseId": case["id"],
        "skillUnderTest": case["skillUnderTest"],
        "sessionOrdinal": ordinal,
        "promptSha256": _sha256(case["prompt"].encode("utf-8")),
        "rubricContractSha256": _rubric_hash(fixture, case),
        "codexExitCode": None if host_result is None else host_result["codexExitCode"],
        "responseSha256": source["responseSha256"],
        "responseBytes": source["responseBytes"],
        "toolEventCount": source["toolEventCount"],
        "verdict": scored["verdict"],
        "assertions": scored["assertions"],
    }


def _exit_for(evidence: dict[str, Any]) -> int:
    return {"fail": FAIL, "blocked": BLOCKED}.get(evidence["status"], PASS)


def run_offline(
    fixture: dict[str, Any],
    scorer_outputs: dict[str, dict[str, Any]],
    *,
    fixture_bytes: bytes,
) -> tuple[int, dict[str, Any]]:
    try:
        _validate_fixture(fixture, fixture_bytes)
    except ValueError:
        return FAIL, {"status": "fail", "reason": "fixture_contract_invalid"}
    _validate_scorer_outputs(fixture, scorer_outputs)
    rows = []
    for ordinal, case in enumerate(fixture["cases"], 1):
        observation = scorer_outputs[case["id"]]
        _validate_observation(observation)
        rows.append(_row(fixture, case, ordinal, observation))
    evidence = _evidence("offline", fixture, fixture_bytes, rows)
    return _exit_for(evidence), evidence


def _validate_scorer_outputs(
    fixture: dict[str, Any], scorer_outputs: dict[str, dict[str, Any]]
) -> None:
    if type(scorer_outputs) is not dict or set(scorer_outputs) != {
        case["id"] for case in fixture["cases"]
    }:
        raise ValueError("offline scorer output identities do not match fixture")
    for case in fixture["cases"]:
        _validate_observation(scorer_outputs[case["id"]])


def _absolute_lexical_path(path: Path | str) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


def _component_walk_path(path: Path | str) -> Path:
    absolute = _absolute_lexical_path(path)
    for alias, expected_target in TRUSTED_SYSTEM_PATH_ALIASES.items():
        if absolute != alias and alias not in absolute.parents:
            continue
        try:
            target = _absolute_lexical_path(alias.parent / os.readlink(alias))
            target_metadata = target.lstat()
        except OSError:
            continue
        if (
            alias.is_symlink()
            and target == expected_target
            and stat.S_ISDIR(target_metadata.st_mode)
            and not stat.S_ISLNK(target_metadata.st_mode)
        ):
            return target / absolute.relative_to(alias)
    return absolute


def _open_directory_no_symlinks(path: Path | str) -> int:
    absolute = _component_walk_path(path)
    flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    descriptor = os.open(absolute.anchor, flags)
    try:
        for part in absolute.parts[1:]:
            next_descriptor = os.open(part, flags, dir_fd=descriptor)
            try:
                if not stat.S_ISDIR(os.fstat(next_descriptor).st_mode):
                    raise ValueError("path component must be a directory")
            except Exception:
                os.close(next_descriptor)
                raise
            os.close(descriptor)
            descriptor = next_descriptor
        return descriptor
    except Exception:
        os.close(descriptor)
        raise


def _read_regular_file_no_symlinks(path: Path | str) -> bytes:
    absolute = _absolute_lexical_path(path)
    parent_descriptor = _open_directory_no_symlinks(absolute.parent)
    descriptor = -1
    try:
        before = os.stat(
            absolute.name, dir_fd=parent_descriptor, follow_symlinks=False
        )
        if not stat.S_ISREG(before.st_mode):
            raise ValueError("payload must be a regular file")
        flags = (
            os.O_RDONLY
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_CLOEXEC", 0)
        )
        descriptor = os.open(absolute.name, flags, dir_fd=parent_descriptor)
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino)
        ):
            raise ValueError("payload changed during binding")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(descriptor)
        if (opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns) != (
            after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns
        ):
            raise ValueError("payload changed during binding")
        return b"".join(chunks)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        os.close(parent_descriptor)


def _open_verified_executable(executable: str) -> tuple[Path, int, str]:
    path = _absolute_lexical_path(executable)
    parent_descriptor = _open_directory_no_symlinks(path.parent)
    descriptor = -1
    try:
        before = os.stat(path.name, dir_fd=parent_descriptor, follow_symlinks=False)
        if not stat.S_ISREG(before.st_mode):
            raise ExecutableCaptureError("nonregular_binary")
        if before.st_mode & 0o111 == 0:
            raise ExecutableCaptureError("nonexecutable_binary")
        flags = (
            os.O_RDONLY
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_CLOEXEC", 0)
        )
        descriptor = os.open(path.name, flags, dir_fd=parent_descriptor)
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise ExecutableCaptureError("nonregular_binary")
        if opened.st_mode & 0o111 == 0:
            raise ExecutableCaptureError("nonexecutable_binary")
        if (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino):
            raise ExecutableCaptureError("nonregular_binary")
        digest = hashlib.sha256()
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
        after = os.fstat(descriptor)
        if (opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns) != (
            after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns
        ):
            raise ExecutableCaptureError("nonregular_binary")
        os.lseek(descriptor, 0, os.SEEK_SET)
        return path, descriptor, digest.hexdigest()
    except Exception:
        if descriptor >= 0:
            os.close(descriptor)
        raise
    finally:
        os.close(parent_descriptor)


def capture_executable(executable: str) -> dict[str, str]:
    path, descriptor, digest = _open_verified_executable(executable)
    os.close(descriptor)
    return {
        "resolvedExecutable": str(path),
        "executableSha256": digest,
    }


def _precondition_blocker(snapshot: dict[str, Any]) -> str | None:
    if snapshot.get("captureError") in {
        "nonregular_binary", "nonexecutable_binary",
    }:
        return snapshot["captureError"]
    if not snapshot.get("resolvedExecutable") or not snapshot.get("executableSha256"):
        return "missing_binary"
    if snapshot.get("version") != EXPECTED_CODEX_VERSION:
        return "version_mismatch"
    if snapshot.get("authenticated") is not True:
        return "authentication_unavailable"
    if snapshot.get("modelAvailable") is False:
        return "model_unavailable"
    if snapshot.get("pluginAvailable") is not True:
        return "plugin_activation_unavailable"
    return None


def _snapshot_identity(snapshot: dict[str, Any]) -> tuple[Any, ...]:
    return tuple(
        snapshot.get(key)
        for key in (
            "resolvedExecutable", "executableSha256", "version", "authenticated",
            "modelAvailable", "pluginAvailable", "discovery", "installation",
        )
    )


def _snapshot_executable_identity(snapshot: dict[str, Any]) -> tuple[str, str]:
    expected_path = snapshot.get("resolvedExecutable")
    expected_digest = snapshot.get("executableSha256")
    if type(expected_path) is not str or type(expected_digest) is not str:
        raise ValueError("captured executable identity is incomplete")
    return expected_path, expected_digest


def _capture_matches_snapshot(snapshot: dict[str, Any]) -> bool:
    expected_path, expected_digest = _snapshot_executable_identity(snapshot)
    captured = capture_executable(expected_path)
    return (
        captured["resolvedExecutable"] == expected_path
        and captured["executableSha256"] == expected_digest
    )


def _bound_executable_copy(snapshot: dict[str, Any]) -> tuple[str, Path, Path]:
    expected_path, expected_digest = _snapshot_executable_identity(snapshot)
    source_path, source_descriptor, source_digest = _open_verified_executable(
        expected_path
    )
    bound_root: Path | None = None
    bound_path: Path | None = None
    bound_descriptor = -1
    root_descriptor = -1
    try:
        if str(source_path) != expected_path or source_digest != expected_digest:
            raise ValueError("captured executable identity drifted")
        bound_root = Path(tempfile.mkdtemp(prefix="dev136-codex-bound-"))
        bound_path = bound_root / "codex"
        root_descriptor = _open_directory_no_symlinks(bound_root)
        bound_descriptor = os.open(
            bound_path.name,
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_CLOEXEC", 0),
            0o700,
            dir_fd=root_descriptor,
        )
        while True:
            chunk = os.read(source_descriptor, 1024 * 1024)
            if not chunk:
                break
            remaining = memoryview(chunk)
            while remaining:
                written = os.write(bound_descriptor, remaining)
                if written <= 0:
                    raise OSError("bound executable copy did not make progress")
                remaining = remaining[written:]
        os.fsync(bound_descriptor)
        descriptor_to_close = bound_descriptor
        bound_descriptor = -1
        os.close(descriptor_to_close)
        captured_copy = capture_executable(str(bound_path))
        if captured_copy["executableSha256"] != expected_digest:
            raise ValueError("bound executable copy digest mismatch")
        return expected_path, bound_path, bound_root
    except Exception:
        if bound_path is not None and bound_root is not None:
            _retry_bound_executable_cleanup(bound_path, bound_root)
        raise
    finally:
        if bound_descriptor >= 0:
            os.close(bound_descriptor)
        if root_descriptor >= 0:
            os.close(root_descriptor)
        os.close(source_descriptor)


def _remove_bound_executable_copy(bound_path: Path, bound_root: Path) -> bool:
    removed = True
    try:
        bound_path.unlink()
    except FileNotFoundError:
        pass
    except OSError:
        removed = False
    try:
        bound_root.rmdir()
    except FileNotFoundError:
        pass
    except OSError:
        removed = False
    return removed


def _retry_bound_executable_cleanup(bound_path: Path, bound_root: Path) -> bool:
    for _attempt in range(2):
        try:
            if _remove_bound_executable_copy(bound_path, bound_root):
                return True
        except Exception:
            pass
    return False


def _close_descriptor(descriptor: int) -> bool:
    try:
        os.close(descriptor)
        return True
    except OSError:
        return False


def _zeroize_output_path_no_symlinks(
    output_path: Path,
    expected_identity: tuple[int, int],
) -> bool:
    parent_descriptor = -1
    descriptor = -1
    zeroized = False
    try:
        parent_descriptor = _open_directory_no_symlinks(output_path.parent)
        before = os.stat(
            output_path.name,
            dir_fd=parent_descriptor,
            follow_symlinks=False,
        )
        if (
            not stat.S_ISREG(before.st_mode)
            or (before.st_dev, before.st_ino) != expected_identity
        ):
            return False
        descriptor = os.open(
            output_path.name,
            os.O_WRONLY
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_CLOEXEC", 0),
            dir_fd=parent_descriptor,
        )
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or (opened.st_dev, opened.st_ino) != expected_identity
        ):
            return False
        os.ftruncate(descriptor, 0)
        os.fsync(descriptor)
        zeroized = True
    except (OSError, ValueError):
        pass
    finally:
        if descriptor >= 0 and not _close_descriptor(descriptor):
            zeroized = False
        if parent_descriptor >= 0 and not _close_descriptor(parent_descriptor):
            zeroized = False
    return zeroized


def _zeroize_owned_output(
    owner: Any,
    expected_identity: tuple[int, int],
) -> bool:
    try:
        descriptor = owner.fileno()
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or (opened.st_dev, opened.st_ino) != expected_identity
        ):
            return False
        original_size = opened.st_size
        truncated = True
        try:
            owner.truncate(0)
        except (OSError, ValueError):
            truncated = False
            owner.seek(0)
            remaining = original_size
            zeroes = bytes(1024 * 1024)
            while remaining:
                written = owner.write(zeroes[: min(remaining, len(zeroes))])
                if type(written) is not int or written <= 0:
                    return False
                remaining -= written
        owner.flush()
        os.fsync(descriptor)
        after = os.fstat(descriptor)
        sanitized = (
            stat.S_ISREG(after.st_mode)
            and (after.st_dev, after.st_ino) == expected_identity
        )
        return sanitized and truncated
    except (OSError, ValueError):
        return False


def _cleanup_private_output(
    owner: Any | None,
    output_path: Path | None,
    expected_identity: tuple[int, int] | None,
) -> bool:
    if owner is None and output_path is None:
        return True

    truncated = False
    if owner is not None and expected_identity is not None:
        truncated = _zeroize_owned_output(owner, expected_identity)

    path_zeroized = False
    if (
        not truncated
        and output_path is not None
        and expected_identity is not None
    ):
        path_zeroized = _zeroize_output_path_no_symlinks(
            output_path, expected_identity
        )
    zeroized = truncated or path_zeroized

    unlinked = output_path is None
    parent_descriptor = -1
    if output_path is not None:
        try:
            parent_descriptor = _open_directory_no_symlinks(output_path.parent)
            before = os.stat(
                output_path.name,
                dir_fd=parent_descriptor,
                follow_symlinks=False,
            )
            path_matches = (
                expected_identity is not None
                and stat.S_ISREG(before.st_mode)
                and expected_identity == (before.st_dev, before.st_ino)
            )
            if path_matches:
                os.unlink(output_path.name, dir_fd=parent_descriptor)
                unlinked = True
        except FileNotFoundError:
            unlinked = True
        except (OSError, ValueError):
            pass

    closed = True
    if owner is not None:
        try:
            owner.close()
        except (OSError, ValueError):
            closed = False
    if output_path is not None and unlinked:
        try:
            os.stat(
                output_path.name,
                dir_fd=parent_descriptor,
                follow_symlinks=False,
            )
        except FileNotFoundError:
            pass
        except (OSError, ValueError):
            unlinked = False
        else:
            unlinked = False
    if parent_descriptor >= 0 and not _close_descriptor(parent_descriptor):
        unlinked = False
    return zeroized and closed and unlinked


def _read_output_owner(
    owner: Any,
    expected_identity: tuple[int, int],
) -> bytes:
    descriptor = owner.fileno()
    opened = os.fstat(descriptor)
    if (
        not stat.S_ISREG(opened.st_mode)
        or (opened.st_dev, opened.st_ino) != expected_identity
    ):
        raise ValueError("private output must be a regular file")
    owner.seek(0)
    chunks: list[bytes] = []
    while True:
        chunk = owner.read(1024 * 1024)
        if not chunk:
            break
        chunks.append(chunk)
    after = os.fstat(descriptor)
    if (opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns) != (
        after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns
    ):
        raise ValueError("private output changed while being read")
    return b"".join(chunks)


def _json_object_without_duplicates(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, child in pairs:
        if key in value:
            raise ValueError("duplicate JSON key")
        value[key] = child
    return value


def _reject_json_constant(_constant: str) -> None:
    raise ValueError("non-standard JSON constant")


def _strict_json_loads(value: str | bytes | bytearray) -> Any:
    return json.loads(
        value,
        object_pairs_hook=_json_object_without_duplicates,
        parse_constant=_reject_json_constant,
    )


class _CodexJsonObjectPairs(list[tuple[str, Any]]):
    pass


def _codex_json_value_without_duplicates(value: Any) -> Any:
    if type(value) is _CodexJsonObjectPairs:
        decoded: dict[str, Any] = {}
        for key, child in value:
            if key in decoded:
                raise ValueError("duplicate Codex JSONL key")
            decoded[key] = _codex_json_value_without_duplicates(child)
        return decoded
    if type(value) is list:
        return [_codex_json_value_without_duplicates(child) for child in value]
    return value


def _codex_jsonl_item(value: Any, event_type: Any) -> Any:
    if type(value) is not _CodexJsonObjectPairs:
        return _codex_json_value_without_duplicates(value)
    keys = [key for key, _child in value]
    duplicate_keys = {key for key in keys if keys.count(key) > 1}
    if not duplicate_keys:
        decoded = _codex_json_value_without_duplicates(value)
        if type(decoded) is dict and decoded.get("type") == "web_search":
            if CODEX_JSONL_WEB_SEARCH_INNER_ID in decoded:
                raise ValueError("unsupported Codex JSONL web search metadata")
            decoded = {
                **decoded,
                CODEX_JSONL_WEB_SEARCH_INNER_ID: decoded.get("id"),
            }
        return decoded
    if (
        event_type not in {"item.started", "item.completed"}
        or duplicate_keys != {"id"}
        or keys.count("id") != 2
        or set(keys) != {"id", "type", "query", "action"}
    ):
        raise ValueError("unsupported Codex JSONL duplicate key")
    fields: dict[str, list[Any]] = {}
    for key, child in value:
        fields.setdefault(key, []).append(child)
    first_id, second_id = fields["id"]
    if (
        fields["type"] != ["web_search"]
        or type(first_id) is not str
        or re.fullmatch(r"item_[0-9]+", first_id) is None
        or type(second_id) is not str
        or not second_id
    ):
        raise ValueError("unsupported Codex JSONL duplicate id")
    return {
        "id": first_id,
        "type": "web_search",
        "query": _codex_json_value_without_duplicates(fields["query"][0]),
        "action": _codex_json_value_without_duplicates(fields["action"][0]),
        CODEX_JSONL_WEB_SEARCH_INNER_ID: second_id,
    }


def _codex_jsonl_record_loads(value: str) -> Any:
    decoded = json.loads(
        value,
        object_pairs_hook=_CodexJsonObjectPairs,
        parse_constant=_reject_json_constant,
    )
    if type(decoded) is not _CodexJsonObjectPairs:
        return _codex_json_value_without_duplicates(decoded)
    keys = [key for key, _child in decoded]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate Codex JSONL record key")
    fields = dict(decoded)
    event_type = fields.get("type")
    return {
        key: (
            _codex_jsonl_item(child, event_type)
            if key == "item"
            else _codex_json_value_without_duplicates(child)
        )
        for key, child in decoded
    }


def _require_closed_object(
    value: Any, keys: set[str], label: str
) -> dict[str, Any]:
    if type(value) is not dict or set(value) != keys:
        raise ValueError(f"{label} schema is not closed")
    return value


def _require_string(value: Any, label: str, *, nonempty: bool = True) -> str:
    if type(value) is not str or (nonempty and not value):
        raise ValueError(f"{label} must be a string")
    return value


def _validate_web_search_action(action: Any) -> None:
    if type(action) is not dict or type(action.get("type")) is not str:
        raise ValueError("web search action is malformed")
    action_type = action["type"]
    allowed = {
        "search": {"type", "query", "queries"},
        "open_page": {"type", "url"},
        "find_in_page": {"type", "url", "pattern"},
        "other": {"type"},
    }
    if action_type not in allowed or not set(action).issubset(allowed[action_type]):
        raise ValueError("web search action schema is not closed")
    if action_type == "search":
        if "query" in action and type(action["query"]) is not str:
            raise ValueError("web search query is malformed")
        if "queries" in action and (
            type(action["queries"]) is not list
            or any(type(query) is not str for query in action["queries"])
        ):
            raise ValueError("web search queries are malformed")
    else:
        for key in set(action) - {"type"}:
            if type(action[key]) is not str:
                raise ValueError("web search action value is malformed")


def _validate_codex_item(item: Any, event_type: str) -> dict[str, Any]:
    if type(item) is not dict:
        raise ValueError("Codex JSONL item must be an object")
    item_type = item.get("type")
    if type(item_type) is not str or item_type not in CODEX_JSONL_ITEM_TYPES:
        raise ValueError("Codex JSONL item type is unknown")
    if event_type not in CODEX_JSONL_ITEM_EVENT_TYPES[item_type]:
        raise ValueError("Codex JSONL item lifecycle is invalid")
    _require_string(item.get("id"), "item id")

    if item_type in {"agent_message", "reasoning"}:
        _require_closed_object(item, {"id", "type", "text"}, item_type)
        _require_string(item["text"], f"{item_type} text", nonempty=False)
    elif item_type == "error":
        _require_closed_object(item, {"id", "type", "message"}, "error item")
        _require_string(item["message"], "error item message", nonempty=False)
    elif item_type == "command_execution":
        _require_closed_object(
            item,
            {"id", "type", "command", "aggregated_output", "exit_code", "status"},
            "command item",
        )
        _require_string(item["command"], "command", nonempty=False)
        _require_string(item["aggregated_output"], "aggregated output", nonempty=False)
        if item["exit_code"] is not None and type(item["exit_code"]) is not int:
            raise ValueError("command exit code is malformed")
        if item["status"] not in {"in_progress", "completed", "failed", "declined"}:
            raise ValueError("command status is malformed")
        if event_type == "item.started" and (
            item["status"] != "in_progress"
            or item["aggregated_output"] != ""
            or item["exit_code"] is not None
        ):
            raise ValueError("command start state is malformed")
        if event_type == "item.updated":
            raise ValueError("command items do not emit updates")
        if event_type == "item.completed":
            status = item["status"]
            exit_code = item["exit_code"]
            valid_terminal = (
                (status == "completed" and exit_code == 0)
                or (
                    status == "failed"
                    and type(exit_code) is int
                    and exit_code != 0
                )
                or (status == "declined" and exit_code == -1)
            )
            if not valid_terminal:
                raise ValueError("command completion state is malformed")
    elif item_type == "file_change":
        _require_closed_object(item, {"id", "type", "changes", "status"}, "file change")
        if item["status"] not in {"completed", "failed"}:
            raise ValueError("file change status is malformed")
        if type(item["changes"]) is not list:
            raise ValueError("file changes are malformed")
        for change in item["changes"]:
            _require_closed_object(change, {"path", "kind"}, "file update")
            _require_string(change["path"], "file update path", nonempty=False)
            if change["kind"] not in {"add", "delete", "update"}:
                raise ValueError("file update kind is malformed")
    elif item_type == "mcp_tool_call":
        _require_closed_object(
            item,
            {"id", "type", "server", "tool", "arguments", "result", "error", "status"},
            "MCP tool call",
        )
        _require_string(item["server"], "MCP server", nonempty=False)
        _require_string(item["tool"], "MCP tool", nonempty=False)
        if item["status"] not in {"in_progress", "completed", "failed"}:
            raise ValueError("MCP status is malformed")
        if event_type == "item.started" and item["status"] != "in_progress":
            raise ValueError("MCP start state is malformed")
        if event_type == "item.completed" and item["status"] == "in_progress":
            raise ValueError("MCP completion state is malformed")
        if item["result"] is not None:
            result = item["result"]
            if type(result) is not dict or set(result) not in (
                {"content", "structured_content"},
                {"content", "_meta", "structured_content"},
            ):
                raise ValueError("MCP result schema is not closed")
            if type(result["content"]) is not list:
                raise ValueError("MCP result content is malformed")
        if item["error"] is not None:
            error = _require_closed_object(item["error"], {"message"}, "MCP error")
            _require_string(error["message"], "MCP error message", nonempty=False)
    elif item_type == "collab_tool_call":
        _require_closed_object(
            item,
            {
                "id", "type", "tool", "sender_thread_id", "receiver_thread_ids",
                "prompt", "agents_states", "status",
            },
            "collab tool call",
        )
        if item["tool"] not in {"spawn_agent", "send_input", "wait", "close_agent"}:
            raise ValueError("collab tool is malformed")
        _require_string(item["sender_thread_id"], "collab sender")
        if type(item["receiver_thread_ids"]) is not list or any(
            type(thread_id) is not str for thread_id in item["receiver_thread_ids"]
        ):
            raise ValueError("collab receivers are malformed")
        if item["prompt"] is not None and type(item["prompt"]) is not str:
            raise ValueError("collab prompt is malformed")
        if type(item["agents_states"]) is not dict:
            raise ValueError("collab agent states are malformed")
        for state in item["agents_states"].values():
            _require_closed_object(state, {"status", "message"}, "collab agent state")
            if state["status"] not in {
                "pending_init", "running", "interrupted", "completed", "errored",
                "shutdown", "not_found",
            }:
                raise ValueError("collab agent status is malformed")
            if state["message"] is not None and type(state["message"]) is not str:
                raise ValueError("collab agent message is malformed")
        if item["status"] not in {"in_progress", "completed", "failed"}:
            raise ValueError("collab tool status is malformed")
        if event_type == "item.started" and item["status"] != "in_progress":
            raise ValueError("collab tool start state is malformed")
        if event_type == "item.completed" and item["status"] == "in_progress":
            raise ValueError("collab tool completion state is malformed")
        if item["tool"] == "spawn_agent":
            receivers = item["receiver_thread_ids"]
            agent_states = item["agents_states"]
            if event_type == "item.started" and (receivers or agent_states):
                raise ValueError("collab spawn start state is malformed")
            if event_type == "item.completed":
                if item["status"] == "completed":
                    receiver_set = set(receivers)
                    if (
                        not receivers
                        or len(receiver_set) != len(receivers)
                        or receiver_set != set(agent_states)
                    ):
                        raise ValueError(
                            "collab spawn completion state is malformed"
                        )
                elif receivers or agent_states:
                    raise ValueError("failed collab spawn state is malformed")
    elif item_type == "web_search":
        _require_closed_object(
            item,
            {
                "id", "type", "query", "action",
                CODEX_JSONL_WEB_SEARCH_INNER_ID,
            },
            "web search",
        )
        _require_string(
            item[CODEX_JSONL_WEB_SEARCH_INNER_ID],
            "web search inner id",
        )
        _require_string(item["query"], "web search query", nonempty=False)
        _validate_web_search_action(item["action"])
        if event_type == "item.started" and (
            item["query"] != "" or item["action"] != {"type": "other"}
        ):
            raise ValueError("web search start state is malformed")
    elif item_type == "todo_list":
        _require_closed_object(item, {"id", "type", "items"}, "todo list")
        if type(item["items"]) is not list:
            raise ValueError("todo items are malformed")
        for todo in item["items"]:
            _require_closed_object(todo, {"text", "completed"}, "todo item")
            _require_string(todo["text"], "todo text", nonempty=False)
            if type(todo["completed"]) is not bool:
                raise ValueError("todo completion is malformed")
    return item


def _codex_jsonl_events(stdout: str) -> list[dict[str, Any]]:
    parsed: list[dict[str, Any]] = []
    terminal_seen = False
    open_items: dict[str, dict[str, Any]] = {}
    open_web_search_inner_ids: dict[str, str] = {}
    top_level_error_seen = False
    lines = stdout.splitlines()
    if not lines:
        raise ValueError("Codex JSONL stream is empty")
    for line in lines:
        if not line:
            raise ValueError("Codex JSONL stream contains a blank record")
        try:
            value = _codex_jsonl_record_loads(line)
        except (json.JSONDecodeError, ValueError) as error:
            raise ValueError("Codex JSONL record is invalid") from error
        if type(value) is not dict:
            raise ValueError("Codex JSONL record must be an object")
        event_type = value.get("type")
        if type(event_type) is not str or event_type not in CODEX_JSONL_EVENT_TYPES:
            raise ValueError("Codex JSONL event type is unknown")
        if terminal_seen:
            raise ValueError("Codex JSONL stream continues after its terminal event")
        if not parsed:
            if event_type != "thread.started":
                raise ValueError("Codex JSONL stream must start with thread.started")
        elif len(parsed) == 1:
            if event_type != "turn.started":
                raise ValueError("Codex JSONL turn must start after its thread")
        elif event_type in {"thread.started", "turn.started"}:
            raise ValueError("Codex JSONL start event is out of order")

        if event_type == "thread.started":
            _require_closed_object(value, {"type", "thread_id"}, "thread.started")
            _require_string(value["thread_id"], "thread id")
        elif event_type == "turn.started":
            _require_closed_object(value, {"type"}, "turn.started")
        elif event_type == "turn.completed":
            _require_closed_object(value, {"type", "usage"}, "turn.completed")
            usage = _require_closed_object(
                value["usage"],
                {
                    "input_tokens", "cached_input_tokens", "output_tokens",
                    "reasoning_output_tokens",
                },
                "turn usage",
            )
            if any(type(count) is not int or count < 0 for count in usage.values()):
                raise ValueError("turn usage is malformed")
            if top_level_error_seen:
                raise ValueError("successful stream contains a top-level error")
        elif event_type == "turn.failed":
            _require_closed_object(value, {"type", "error"}, "turn.failed")
            error = _require_closed_object(value["error"], {"message"}, "turn error")
            _require_string(error["message"], "turn error message", nonempty=False)
        elif event_type == "error":
            _require_closed_object(value, {"type", "message"}, "stream error")
            _require_string(value["message"], "stream error message", nonempty=False)
            if top_level_error_seen:
                raise ValueError("Codex JSONL stream has duplicate top-level errors")
            top_level_error_seen = True
        elif event_type.startswith("item."):
            _require_closed_object(value, {"type", "item"}, event_type)
            item = _validate_codex_item(value["item"], event_type)
            item_id = item["id"]
            if event_type == "item.started":
                if item_id in open_items:
                    raise ValueError("Codex JSONL item started more than once")
                if item["type"] == "web_search":
                    inner_id = item[CODEX_JSONL_WEB_SEARCH_INNER_ID]
                    inner_owner = open_web_search_inner_ids.get(inner_id)
                    if inner_owner is not None and inner_owner != item_id:
                        raise ValueError(
                            "Codex JSONL web search identity is reused"
                        )
                    open_web_search_inner_ids[inner_id] = item_id
                open_items[item_id] = copy.deepcopy(item)
            elif event_type == "item.updated":
                opened = open_items.get(item_id)
                if opened is None or opened["type"] != item["type"]:
                    raise ValueError("Codex JSONL item update is unpaired")
                if item["type"] != "todo_list":
                    raise ValueError("Codex JSONL item type does not emit updates")
            else:
                opened = open_items.get(item_id)
                if item["type"] in CODEX_JSONL_PAIRED_ITEM_TYPES and (
                    opened is None or opened["type"] != item["type"]
                ):
                    raise ValueError("Codex JSONL item completion is unpaired")
                if item["type"] == "web_search":
                    opened_inner_id = opened[CODEX_JSONL_WEB_SEARCH_INNER_ID]
                    completed_inner_id = item[CODEX_JSONL_WEB_SEARCH_INNER_ID]
                    if (
                        completed_inner_id != opened_inner_id
                        or open_web_search_inner_ids.get(completed_inner_id)
                        != item_id
                    ):
                        raise ValueError(
                            "Codex JSONL web search identity is mismatched"
                        )
                immutable_fields = CODEX_JSONL_IMMUTABLE_IDENTITY_FIELDS.get(
                    item["type"], ()
                )
                if (
                    item["type"] == "collab_tool_call"
                    and item["tool"] == "spawn_agent"
                ):
                    immutable_fields = tuple(
                        field
                        for field in immutable_fields
                        if field != "receiver_thread_ids"
                    )
                if any(
                    not _json_type_exact_equal(opened[field], item[field])
                    for field in immutable_fields
                ):
                    raise ValueError("Codex JSONL item identity is mismatched")
                if opened is not None:
                    if opened["type"] != item["type"]:
                        raise ValueError("Codex JSONL item type changed")
                    del open_items[item_id]
                    if item["type"] == "web_search":
                        del open_web_search_inner_ids[
                            item[CODEX_JSONL_WEB_SEARCH_INNER_ID]
                        ]
        if event_type in {"turn.completed", "turn.failed"}:
            if open_items:
                raise ValueError("Codex JSONL stream has unterminated items")
            if top_level_error_seen and event_type != "turn.failed":
                raise ValueError("top-level error requires a failed turn")
            terminal_seen = True
        parsed.append(value)
    if not terminal_seen:
        raise ValueError("Codex JSONL stream is unterminated")
    return parsed


def _tool_events(stdout: str) -> list[dict[str, Any]]:
    parsed = _codex_jsonl_events(stdout)
    if parsed[-1]["type"] != "turn.completed":
        raise ValueError("successful Codex JSONL stream did not complete")
    tool_events: list[dict[str, Any]] = []
    for event in parsed:
        if (
            event["type"] != "item.completed"
            or event["item"]["type"] not in CODEX_JSONL_TOOL_ITEM_TYPES
        ):
            continue
        scorer_event = copy.deepcopy(event)
        if scorer_event["item"]["type"] == "web_search":
            del scorer_event["item"][CODEX_JSONL_WEB_SEARCH_INNER_ID]
        tool_events.append(scorer_event)
    return tool_events


def _is_model_unavailable(completed: subprocess.CompletedProcess[str]) -> bool:
    if completed.returncode == 0:
        return False
    model = re.escape(EXPECTED_MODEL)
    message_pattern = re.compile(
        rf"(?:model {model} (?:is |was )?"
        rf"(?:unavailable|not available|not found|unsupported|access denied|permission denied)"
        rf"|(?:no|not) access to model {model})",
        re.IGNORECASE,
    )

    def exact_message(value: Any) -> bool:
        return type(value) is str and message_pattern.fullmatch(value.strip()) is not None

    if re.fullmatch(
        rf"Error: {message_pattern.pattern}",
        completed.stderr.strip(),
        re.IGNORECASE,
    ) is not None:
        return True
    for line in completed.stdout.splitlines():
        try:
            value = _strict_json_loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        if type(value) is not dict:
            continue
        if set(value) == {"type", "message"} and value.get("type") == "error":
            if exact_message(value["message"]):
                return True
        elif set(value) == {"type", "error"} and value.get("type") == "turn.failed":
            error = value["error"]
            if (
                type(error) is dict
                and set(error) == {"message"}
                and exact_message(error["message"])
            ):
                return True
    return False


def run_host(
    fixture: dict[str, Any],
    executable: str,
    process_runner: Callable[..., subprocess.CompletedProcess[str]],
    prerequisite_checker: Callable[[str, str, str], dict[str, Any]],
    scorer: Callable[[dict[str, Any], bytes, list[dict[str, Any]]], dict[str, Any]],
    *,
    fixture_bytes: bytes,
    host_results_sink: list[dict[str, Any]] | None = None,
    scorer_outputs_sink: dict[str, dict[str, Any]] | None = None,
) -> tuple[int, dict[str, Any]]:
    try:
        _validate_fixture(fixture, fixture_bytes)
    except ValueError:
        return FAIL, {"status": "fail", "reason": "fixture_contract_invalid"}
    rows: list[dict[str, Any]] = []
    first_snapshot: dict[str, Any] | None = None
    for ordinal, case in enumerate(fixture["cases"], 1):
        pre = prerequisite_checker(executable, EXPECTED_MODEL, EXPECTED_CODEX_VERSION)
        if type(pre) is not dict:
            raise ValueError("prerequisite checker returned invalid snapshot")
        if first_snapshot is None:
            first_snapshot = copy.deepcopy(pre)
        elif _snapshot_identity(pre) != _snapshot_identity(first_snapshot):
            evidence = _evidence(
                "host", fixture, fixture_bytes, rows, snapshot=first_snapshot,
                blocker="post_capture_prerequisite_drift", forced_status="fail",
            )
            return FAIL, evidence
        blocker = _precondition_blocker(pre)
        if blocker is not None:
            evidence = _evidence(
                "host", fixture, fixture_bytes, rows, snapshot=first_snapshot,
                blocker=blocker, forced_status="blocked",
            )
            return BLOCKED, evidence

        try:
            execution_path, bound_path, bound_root = _bound_executable_copy(pre)
        except (OSError, ValueError):
            evidence = _evidence(
                "host", fixture, fixture_bytes, rows, snapshot=first_snapshot,
                blocker="post_capture_prerequisite_drift", forced_status="fail",
            )
            return FAIL, evidence

        output_descriptor = -1
        output_owner: Any | None = None
        output_identity: tuple[int, int] | None = None
        allocation_descriptor_closed = True
        output_path: Path | None = None
        completed: subprocess.CompletedProcess[str] | None = None
        process_error = False
        case_code: int | None = None
        case_blocker: str | None = None
        case_status: str | None = None
        pending_host_result: dict[str, Any] | None = None
        pending_observation: dict[str, Any] | None = None
        bound_boundary_clean = True
        try:
            try:
                output_descriptor, output_name = tempfile.mkstemp(
                    prefix="dev136-codex-", suffix=".txt"
                )
                output_path = Path(output_name)
                opened = os.fstat(output_descriptor)
                if not stat.S_ISREG(opened.st_mode):
                    raise ValueError("private output must be a regular file")
                output_identity = (opened.st_dev, opened.st_ino)
                descriptor_to_transfer = output_descriptor
                output_descriptor = -1
                output_owner = os.fdopen(
                    descriptor_to_transfer, "r+b", buffering=0
                )
            except (OSError, ValueError):
                if output_descriptor >= 0:
                    allocation_descriptor_closed = _close_descriptor(
                        output_descriptor
                    )
                    output_descriptor = -1
                case_code = FAIL
                case_blocker = "process_failed"
                case_status = "fail"
            else:
                command = [
                    execution_path, "exec", "--ephemeral", "--json", "-m",
                    EXPECTED_MODEL, "--output-last-message", str(output_path), "-",
                ]
                try:
                    completed = process_runner(
                        command,
                        input=case["prompt"],
                        capture_output=True,
                        text=True,
                        check=False,
                        executable=str(bound_path),
                    )
                except Exception:
                    process_error = True

                bound_boundary_clean = _retry_bound_executable_cleanup(
                    bound_path, bound_root
                )
                if not bound_boundary_clean:
                    case_code = FAIL
                    case_blocker = "post_capture_prerequisite_drift"
                    case_status = "fail"
                else:
                    try:
                        post = prerequisite_checker(
                            execution_path, EXPECTED_MODEL, EXPECTED_CODEX_VERSION
                        )
                    except Exception:
                        post = {}
                    try:
                        identity_stable = _capture_matches_snapshot(first_snapshot)
                    except (OSError, ValueError):
                        identity_stable = False
                    if (
                        not identity_stable
                        or _snapshot_identity(pre) != _snapshot_identity(first_snapshot)
                        or _snapshot_identity(post)
                        != _snapshot_identity(first_snapshot)
                    ):
                        case_code = FAIL
                        case_blocker = "post_capture_prerequisite_drift"
                        case_status = "fail"
                    elif (
                        completed is not None
                        and completed.returncode != 0
                        and _is_model_unavailable(completed)
                    ):
                        case_code = BLOCKED
                        case_blocker = "model_unavailable"
                        case_status = "blocked"
                    elif (
                        process_error
                        or completed is None
                        or completed.returncode != 0
                    ):
                        case_code = FAIL
                        case_blocker = "process_failed"
                        case_status = "fail"
                    else:
                        try:
                            if output_owner is None or output_identity is None:
                                raise ValueError("private output owner is unavailable")
                            response = _read_output_owner(
                                output_owner, output_identity
                            )
                            events = _tool_events(completed.stdout)
                        except (OSError, ValueError):
                            case_code = FAIL
                            case_blocker = "event_stream_invalid"
                            case_status = "fail"
                        else:
                            pending_host_result = {
                                "codexExitCode": completed.returncode,
                                "responseSha256": _sha256(response),
                                "responseBytes": len(response),
                                "toolEventCount": len(events),
                            }
                            try:
                                pending_observation = scorer(case, response, events)
                                _validate_observation(pending_observation)
                            except Exception:
                                pending_observation = None
                                case_code = FAIL
                                case_blocker = "scoring_failed"
                                case_status = "fail"
        finally:
            output_clean = _cleanup_private_output(
                output_owner, output_path, output_identity
            )
            output_clean = output_clean and allocation_descriptor_closed
            bound_final_clean = _retry_bound_executable_cleanup(
                bound_path, bound_root
            )

        if not bound_boundary_clean or not bound_final_clean:
            case_code = FAIL
            case_blocker = "post_capture_prerequisite_drift"
            case_status = "fail"
        elif case_blocker != "post_capture_prerequisite_drift" and not output_clean:
            case_code = FAIL
            case_blocker = "process_failed"
            case_status = "fail"

        if case_code is not None:
            evidence = _evidence(
                "host", fixture, fixture_bytes, rows, snapshot=first_snapshot,
                blocker=case_blocker, forced_status=case_status,
            )
            return case_code, evidence

        if pending_host_result is None or pending_observation is None:
            evidence = _evidence(
                "host", fixture, fixture_bytes, rows, snapshot=first_snapshot,
                blocker="process_failed", forced_status="fail",
            )
            return FAIL, evidence
        if host_results_sink is not None:
            host_results_sink.append(copy.deepcopy(pending_host_result))
        if scorer_outputs_sink is not None:
            scorer_outputs_sink[case["id"]] = copy.deepcopy(pending_observation)
        rows.append(
            _row(
                fixture, case, ordinal, pending_observation, pending_host_result
            )
        )

    evidence = _evidence("host", fixture, fixture_bytes, rows, snapshot=first_snapshot)
    return _exit_for(evidence), evidence


def _validate_private_evidence(value: Any) -> None:
    if type(value) is dict:
        for key, child in value.items():
            if key in FORBIDDEN_KEYS:
                raise ValueError(f"private evidence key: {key}")
            _validate_private_evidence(child)
    elif type(value) is list:
        for child in value:
            _validate_private_evidence(child)
    elif type(value) is str:
        if any(pattern.search(value) for pattern in PRIVATE_VALUE_RES):
            raise ValueError("private evidence value")


def _validate_host_result(result: dict[str, Any]) -> None:
    if type(result) is not dict or set(result) != HOST_RESULT_KEYS:
        raise ValueError("host result schema is not closed")
    _validate_nonnegative_int(result["codexExitCode"], "codexExitCode")
    _validate_hash(result["responseSha256"], "responseSha256")
    _validate_nonnegative_int(result["responseBytes"], "responseBytes")
    _validate_nonnegative_int(result["toolEventCount"], "toolEventCount")


def _validate_evidence(
    evidence: dict[str, Any],
    fixture: dict[str, Any],
    fixture_bytes: bytes,
    scorer_outputs: dict[str, dict[str, Any]],
    host_results: list[dict[str, Any]] | None,
    executable_sha256: str | None,
) -> None:
    _validate_fixture(fixture, fixture_bytes)
    if type(evidence) is not dict or set(evidence) != EVIDENCE_KEYS:
        raise ValueError("evidence schema is not closed")
    expected_scalars = {
        "schemaVersion": "1.0", "sourceIssue": "DEV-136",
        "evidenceKind": "codex_skill_forward_test", "model": EXPECTED_MODEL,
        "codexVersion": EXPECTED_CODEX_VERSION, "fixtureSha256": _sha256(fixture_bytes),
        "privacy": PRIVACY,
    }
    for key, expected in expected_scalars.items():
        if evidence[key] != expected:
            raise ValueError(f"evidence binding mismatch: {key}")
    if evidence["mode"] not in {"offline", "host"} or evidence["status"] not in STATUSES:
        raise ValueError("evidence mode or status is invalid")
    host = evidence["host"]
    if type(host) is not dict or set(host) != HOST_KEYS:
        raise ValueError("host schema is not closed")
    if host["name"] != "codex" or host["version"] != EXPECTED_CODEX_VERSION:
        raise ValueError("host identity mismatch")
    if host["model"] != EXPECTED_MODEL or host["modelSelection"] != "explicit_cli_argument":
        raise ValueError("host model binding mismatch")
    if host["sessionMode"] != ("fresh_ephemeral" if evidence["mode"] == "host" else "not_applicable"):
        raise ValueError("host session mode mismatch")
    if host["resolvedExecutableSha256"] != executable_sha256:
        raise ValueError("host executable binding mismatch")
    _validate_hash(executable_sha256, "resolvedExecutableSha256", nullable=True)
    if host["claudeInvoked"] is not False:
        raise ValueError("Claude invocation is forbidden")
    if host["blockerReason"] is not None and host["blockerReason"] not in EARLY_STOP_REASONS | PRE_RESPONSE_REASONS:
        raise ValueError("unknown blocker reason")
    prerequisites = host["prerequisites"]
    if type(prerequisites) is not dict or set(prerequisites) != PREREQUISITE_KEYS:
        raise ValueError("prerequisite schema is not closed")
    if any(type(value) is not str or value not in STATUSES for value in prerequisites.values()):
        raise ValueError("prerequisite status is invalid")

    rows = evidence["cases"]
    if type(rows) is not list or len(rows) > len(fixture["cases"]):
        raise ValueError("evidence rows are invalid")
    blocker = host["blockerReason"]
    activation_proven = (
        evidence["mode"] == "host"
        and blocker is None
        and bool(rows)
        and len(rows) == len(fixture["cases"])
        and all(
            type(row) is dict
            and type(row.get("assertions")) is dict
            and row["assertions"].get("activation") == "pass"
            for row in rows
        )
    )
    expected_prerequisites = _evidence_prerequisite_statuses(
        evidence["mode"],
        blocker,
        executable_sha256,
        activation_proven=activation_proven,
    )
    if prerequisites != expected_prerequisites:
        raise ValueError("prerequisite derivation mismatch")
    if blocker is None and len(rows) != len(fixture["cases"]):
        raise ValueError("complete evidence must cover every fixture case")
    if len(rows) < len(fixture["cases"]):
        if blocker is None or evidence["status"] not in {"fail", "blocked"}:
            raise ValueError("partial evidence requires an explicit stop")
    if host_results is not None:
        if type(host_results) is not list or len(host_results) < len(rows):
            raise ValueError("host results do not cover evidence rows")
        for result in host_results:
            _validate_host_result(result)
    elif evidence["mode"] == "host" and rows:
        raise ValueError("host evidence requires normalized host results")

    expected_rows: list[dict[str, Any]] = []
    for index, case in enumerate(fixture["cases"][:len(rows)]):
        try:
            observation = scorer_outputs[case["id"]]
        except (KeyError, TypeError) as error:
            raise ValueError("missing scorer output binding") from error
        _validate_observation(observation)
        host_result = None if host_results is None else host_results[index]
        expected_rows.append(_row(fixture, case, index + 1, observation, host_result))
    if rows != expected_rows:
        raise ValueError("evidence row derivation mismatch")
    expected_summary = _summary(fixture, expected_rows)
    if type(evidence["summary"]) is not dict or set(evidence["summary"]) != SUMMARY_KEYS:
        raise ValueError("summary schema is not closed")
    if evidence["summary"] != expected_summary:
        raise ValueError("summary derivation mismatch")
    derived = _derived_status([row["verdict"] for row in expected_rows])
    if len(rows) == len(fixture["cases"]):
        if evidence["status"] != derived or blocker is not None:
            raise ValueError("complete status derivation mismatch")
    else:
        expected_stop_status = (
            "blocked" if blocker in PRE_RESPONSE_REASONS else "fail"
        )
        if evidence["status"] != expected_stop_status:
            raise ValueError("partial stop status derivation mismatch")
    _validate_private_evidence(evidence)


def _open_destination_parent(path: Path) -> int:
    descriptor = _open_directory_no_symlinks(path.parent)
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISDIR(opened.st_mode):
            raise ValueError("evidence parent must be a directory")
        try:
            destination = os.stat(path.name, dir_fd=descriptor, follow_symlinks=False)
        except FileNotFoundError:
            destination = None
        if destination is not None and not stat.S_ISREG(destination.st_mode):
            raise ValueError("evidence destination must be a regular file")
        return descriptor
    except Exception:
        os.close(descriptor)
        raise


def _atomic_write_evidence(
    path: Path | str,
    evidence: dict[str, Any],
    *,
    fault_hook: Callable[[str], None] | None = None,
) -> None:
    destination = Path(path)
    if not destination.is_absolute():
        destination = destination.absolute()
    data = (json.dumps(evidence, indent=2, sort_keys=True) + "\n").encode("utf-8")
    parent_descriptor = _open_destination_parent(destination)
    temporary_name = f".{destination.name}.{secrets.token_hex(16)}.tmp"
    descriptor = -1
    try:
        descriptor = os.open(
            temporary_name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
            0o600,
            dir_fd=parent_descriptor,
        )
        if fault_hook is not None:
            fault_hook("stage")
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = -1
            stream.write(data)
            stream.flush()
            if fault_hook is not None:
                fault_hook("fsync")
            os.fsync(stream.fileno())
        if fault_hook is not None:
            fault_hook("replace")
        os.replace(
            temporary_name,
            destination.name,
            src_dir_fd=parent_descriptor,
            dst_dir_fd=parent_descriptor,
        )
        os.fsync(parent_descriptor)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            os.unlink(temporary_name, dir_fd=parent_descriptor)
        except FileNotFoundError:
            pass
        os.close(parent_descriptor)


def write_evidence(
    path: Path | str,
    evidence: dict[str, Any],
    *,
    fixture: dict[str, Any],
    fixture_bytes: bytes,
    scorer_outputs: dict[str, dict[str, Any]],
    host_results: list[dict[str, Any]] | None = None,
    executable_sha256: str | None = None,
    fault_hook: Callable[[str], None] | None = None,
) -> None:
    _validate_evidence(
        evidence, fixture, fixture_bytes, scorer_outputs, host_results,
        executable_sha256,
    )
    _atomic_write_evidence(path, evidence, fault_hook=fault_hook)


def _probe(
    command: list[str],
    *,
    executable_override: str | None = None,
) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
            **(
                {"executable": executable_override}
                if executable_override is not None
                else {}
            ),
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def _plugin_skill_payloads_are_exact(plugin_root: Path) -> bool:
    skills_root = plugin_root / "skills"
    skills_descriptor = -1
    try:
        skills_descriptor = _open_directory_no_symlinks(skills_root)
        names = os.listdir(skills_descriptor)
        if set(names) != set(SKILL_PAYLOAD_SHA256) or len(names) != len(
            SKILL_PAYLOAD_SHA256
        ):
            return False
        for skill, expected_digest in SKILL_PAYLOAD_SHA256.items():
            metadata = os.stat(
                skill, dir_fd=skills_descriptor, follow_symlinks=False
            )
            if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
                return False
            skill_descriptor = os.open(
                skill,
                os.O_RDONLY
                | getattr(os, "O_DIRECTORY", 0)
                | getattr(os, "O_NOFOLLOW", 0)
                | getattr(os, "O_CLOEXEC", 0),
                dir_fd=skills_descriptor,
            )
            try:
                if os.listdir(skill_descriptor) != ["SKILL.md"]:
                    return False
                payload_metadata = os.stat(
                    "SKILL.md", dir_fd=skill_descriptor, follow_symlinks=False
                )
                if (
                    not stat.S_ISREG(payload_metadata.st_mode)
                    or stat.S_ISLNK(payload_metadata.st_mode)
                ):
                    return False
            finally:
                os.close(skill_descriptor)
            payload = _read_regular_file_no_symlinks(
                skills_root / skill / "SKILL.md"
            )
            if _sha256(payload) != expected_digest:
                return False
        return True
    except (OSError, ValueError):
        return False
    finally:
        if skills_descriptor >= 0:
            os.close(skills_descriptor)


def _plugin_is_installed_enabled_with_capabilities(stdout: str) -> bool:
    try:
        listing = _strict_json_loads(stdout)
    except (json.JSONDecodeError, ValueError):
        return False
    if (
        type(listing) is not dict
        or set(listing) != {"installed", "available"}
        or type(listing.get("installed")) is not list
        or type(listing.get("available")) is not list
    ):
        return False
    plugin_root = _absolute_lexical_path(ROOT / "plugins" / PLUGIN_ID)
    expected_fields = {
        "pluginId": PLUGIN_SELECTOR,
        "name": PLUGIN_ID,
        "marketplaceName": MARKETPLACE_NAME,
        "version": "0.1.0",
        "installed": True,
        "enabled": True,
        "source": {"source": "local", "path": str(plugin_root)},
        "marketplaceSource": {
            "sourceType": "local",
            "source": str(_absolute_lexical_path(ROOT)),
        },
        "installPolicy": "AVAILABLE",
        "authPolicy": "ON_INSTALL",
    }
    def is_target_related(plugin: Any) -> bool:
        return type(plugin) is dict and (
            plugin.get("pluginId") == PLUGIN_SELECTOR
            or (
                plugin.get("name") == PLUGIN_ID
                and plugin.get("marketplaceName") == MARKETPLACE_NAME
            )
        )

    installed_targets = [
        plugin for plugin in listing["installed"] if is_target_related(plugin)
    ]
    available_targets = [
        plugin for plugin in listing["available"] if is_target_related(plugin)
    ]
    if (
        len(installed_targets) != 1
        or available_targets
        or set(installed_targets[0]) != PLUGIN_ENTRY_KEYS
        or installed_targets[0] != expected_fields
    ):
        return False
    manifest_path = plugin_root / ".codex-plugin/plugin.json"
    try:
        manifest = _strict_json_loads(
            _read_regular_file_no_symlinks(manifest_path)
        )
    except (OSError, ValueError, json.JSONDecodeError):
        return False
    interface = manifest.get("interface") if type(manifest) is dict else None
    capabilities = interface.get("capabilities") if type(interface) is dict else None
    return (
        manifest.get("name") == PLUGIN_ID
        and capabilities == list(WORKFLOW_SECTIONS)
        and _plugin_skill_payloads_are_exact(plugin_root)
    )


def default_prerequisite_checker(executable: str, model: str, version: str) -> dict[str, Any]:
    try:
        captured = capture_executable(executable)
    except FileNotFoundError:
        return {
            "resolvedExecutable": None, "executableSha256": None, "version": None,
            "authenticated": False, "modelAvailable": False, "pluginAvailable": False,
            "discovery": "blocked", "installation": "blocked",
        }
    except ExecutableCaptureError as error:
        return {
            "resolvedExecutable": None, "executableSha256": None, "version": None,
            "authenticated": False, "modelAvailable": False, "pluginAvailable": False,
            "discovery": "blocked", "installation": "blocked",
            "captureError": error.reason,
        }
    except (OSError, ValueError):
        return {
            "resolvedExecutable": None, "executableSha256": None, "version": None,
            "authenticated": False, "modelAvailable": False, "pluginAvailable": False,
            "discovery": "blocked", "installation": "blocked",
            "captureError": "nonregular_binary",
        }
    captured_executable = captured["resolvedExecutable"]
    try:
        execution_path, bound_path, bound_root = _bound_executable_copy(captured)
    except (OSError, ValueError):
        return {
            **captured,
            "version": None,
            "authenticated": False,
            "modelAvailable": False,
            "pluginAvailable": False,
            "discovery": "blocked",
            "installation": "blocked",
            "captureError": "nonregular_binary",
        }
    try:
        override = str(bound_path)
        version_probe = _probe(
            [execution_path, "--version"], executable_override=override
        )
        expected_version_line = f"codex-cli {EXPECTED_CODEX_VERSION}"
        observed_version = None
        if (
            version_probe is not None
            and version_probe.returncode == 0
            and version_probe.stderr == ""
            and version_probe.stdout == f"{expected_version_line}\n"
        ):
            observed_version = EXPECTED_CODEX_VERSION
        login_probe = _probe(
            [execution_path, "login", "status"], executable_override=override
        )
        authenticated = (
            login_probe is not None
            and login_probe.returncode == 0
            and login_probe.stdout == ""
            and login_probe.stderr == "Logged in using ChatGPT\n"
        )
        plugin_probe = _probe(
            [execution_path, "plugin", "list", "--json"],
            executable_override=override,
        )
        plugin_available = (
            plugin_probe is not None
            and plugin_probe.returncode == 0
            and plugin_probe.stderr == ""
            and _plugin_is_installed_enabled_with_capabilities(plugin_probe.stdout)
        )
    finally:
        try:
            bound_path.unlink()
        except FileNotFoundError:
            pass
        try:
            bound_root.rmdir()
        except FileNotFoundError:
            pass
    return {
        **captured,
        "version": observed_version,
        "authenticated": authenticated,
        # Codex 0.144.5 exposes no model-list preflight. Exact model access is
        # therefore attemptable here and classified from the actual exec result.
        "modelAvailable": None,
        "pluginAvailable": plugin_available,
        "discovery": "pass" if plugin_available else "blocked",
        "installation": "pass" if plugin_available else "blocked",
    }


def _text_fence(text: str) -> tuple[str, str, str] | None:
    matches = list(re.finditer(r"```text\s*\n(.*?)\n```", text, re.DOTALL))
    if len(matches) != 1:
        return None
    match = matches[0]
    return text[:match.start()], match.group(1), text[match.end():]


def _assignments(block: str) -> tuple[list[str], dict[str, str]] | None:
    names: list[str] = []
    values: dict[str, str] = {}
    for raw_line in block.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = re.fullmatch(r"([A-Za-z][A-Za-z0-9]*)\s*=\s*(.+)", line)
        if match is None or match.group(1) in values:
            return None
        names.append(match.group(1))
        values[match.group(1)] = match.group(2).strip()
    return names, values


def _router_mapping(value: str) -> dict[str, str] | None:
    if not (value.startswith("{") and value.endswith("}")):
        return None
    fields: dict[str, str] = {}
    for part in value[1:-1].split(","):
        match = re.fullmatch(
            r"\s*([A-Za-z][A-Za-z0-9]*)\s*(?:=|:)\s*([^,{}]+?)\s*", part
        )
        if match is None or match.group(1) in fields:
            return None
        fields[match.group(1)] = match.group(2).strip().strip('"\'')
    return fields


def _positive_envelope(
    block: str, expected_skill: str, expected_router: dict[str, str]
) -> tuple[bool, bool, dict[str, str]]:
    lines = [line for line in block.splitlines() if line.strip()]
    if len(lines) < 21:
        return False, False, {}
    activation = re.fullmatch(r"activationStatus\s*=\s*activated", lines[0].strip()) is not None
    selected = re.fullmatch(
        rf"selectedSkill\s*=\s*{re.escape(expected_skill)}", lines[1].strip()
    ) is not None
    router_match = re.fullmatch(r"routerInput\s*=\s*(\{.*\})", lines[2].strip())
    router = None if router_match is None else _router_mapping(router_match.group(1))
    routing = router == expected_router
    if lines[3].strip() != "architectureResult":
        return False, routing, {}
    expected_fields = [
        "architectureSchemaVersion", "stateVersion", "policyVersion", "workflow",
        "scope", "pattern", "source", "destination", "finalResponseOwner",
        "apiAvailability[]", "stateModel", "trustBoundaries[]", "contextPolicy",
        "toolAndEffectPolicy", "failurePolicy", "verification[]", "limitations[]",
    ]
    names: list[str] = []
    values: dict[str, str] = {}
    for raw_line in lines[4:]:
        if not raw_line.startswith("  "):
            return False, routing, values
        match = re.fullmatch(
            r"\s{2}([A-Za-z][A-Za-z0-9]*(?:\[\])?)\s*(?:=|:)\s*(.+)",
            raw_line,
        )
        if match is None or match.group(1) in values:
            return False, routing, values
        names.append(match.group(1))
        values[match.group(1)] = match.group(2).strip()
    schema = values.get("architectureSchemaVersion", "").strip('"\'') == "1.0"
    envelope = activation and selected and names == expected_fields and schema
    return envelope, routing, values


def _usable_version(value: str | None) -> bool:
    if value is None:
        return False
    normalized = re.sub(r'^[\s"\'‘’“”]+|[\s"\'‘’“”]+$', "", value).lower()
    normalized = re.sub(r"[-_\s]+", "_", normalized)
    return bool(normalized) and normalized not in {
        "unknown", "n/a", "none", "null", "tbd", "placeholder",
        "not_specified", "unchanged_existing_version",
    } and "<" not in normalized and ">" not in normalized


def _has_authorized_follow_on_boundary(text: str) -> bool:
    normalized = text.lower()
    normalized = re.sub(
        r"\b[a-z]+n['’]t\b|\bcannot\b",
        " not ",
        normalized,
    )
    normalized = re.sub(r"\s+", " ", normalized)
    boundary = re.search(
        r"\bseparate(?:ly)?\b.{0,80}\bauthoriz(?:ed|ation)\b.{0,80}"
        r"\bfollow(?:-| )on\b"
        r"|\bauthoriz(?:ed|ation)\b.{0,80}\bseparate(?:ly)?\b.{0,80}"
        r"\bfollow(?:-| )on\b"
        r"|\bseparate(?:ly)?\b.{0,80}\bfollow(?:-| )on\b.{0,80}"
        r"\bauthoriz(?:ed|ation)\b",
        normalized,
    )
    if boundary is None:
        return False
    clause_start = max(
        normalized.rfind(".", 0, boundary.start()),
        normalized.rfind("!", 0, boundary.start()),
        normalized.rfind("?", 0, boundary.start()),
        normalized.rfind(";", 0, boundary.start()),
    ) + 1
    clause_ends = [
        position
        for token in (".", "!", "?", ";")
        if (position := normalized.find(token, boundary.end())) >= 0
    ]
    clause_end = min(clause_ends) if clause_ends else len(normalized)
    clause = normalized[clause_start:clause_end]
    return re.search(r"\b(?:no|not|never|without)\b", clause) is None


def live_score(
    case: dict[str, Any], response: bytes, tool_events: list[dict[str, Any]]
) -> dict[str, Any]:
    text = response.decode("utf-8", errors="replace")
    assertions = {name: "not_applicable" for name in ASSERTIONS}
    expected_activation = case["expectedActivation"]
    selected_skill = case["skillUnderTest"]
    fenced = _text_fence(text)
    if expected_activation in {"no_activation", "clarification_required"}:
        before, block, after = fenced if fenced is not None else ("x", "", "x")
        parsed = _assignments(block)
        names, fields = parsed if parsed is not None else ([], {})
        excluded = (
            before.strip() != ""
            or after.strip() != ""
            or re.search(r"(?i)architectureResult", text) is not None
            or re.search(r"(?m)^#{1,6}\s+", text) is not None
        )
        if expected_activation == "no_activation":
            expected_fields = [
                "activationStatus", "reasonCode", "domain", "requestedOperation"
            ]
            valid = (
                not excluded
                and names == expected_fields
                and fields.get("activationStatus") == "no_activation"
                and fields.get("reasonCode") == "out_of_domain"
                and fields.get("domain") == case["routerInput"]["domain"]
                and fields.get("requestedOperation")
                == case["routerInput"]["requestedOperation"]
            )
            assertions["activation"] = "pass" if valid else "fail"
            assertions["routing"] = "pass" if valid else "fail"
        else:
            expected_fields = [
                "activationStatus", "clarificationKind", "missingInput", "question"
            ]
            shape = (
                not excluded
                and names == expected_fields
                and fields.get("activationStatus") == "clarification_required"
                and fields.get("clarificationKind") == case["expectedClarificationKind"]
                and fields.get("missingInput") == case["expectedClarificationKind"]
            )
            question = fields.get("question", "")
            one_question = shape and question.count("?") == 1 and question.rstrip().endswith("?")
            assertions["activation"] = "pass" if shape else "fail"
            assertions["routing"] = "pass" if shape else "fail"
            assertions["one_clarification"] = "pass" if one_question else "fail"
    else:
        before, block, after = fenced if fenced is not None else ("x", "", "")
        envelope, routing, values = _positive_envelope(
            block, selected_skill, case["routerInput"]
        )
        assertions["activation"] = "pass" if before.strip() == "" and envelope else "fail"
        assertions["routing"] = "pass" if routing else "fail"
        headings = re.findall(r"(?m)^#{1,6}\s+(.+?)\s*$", after)
        common = list(COMMON_SECTIONS)
        workflow = list(WORKFLOW_SECTIONS[selected_skill])
        assertions["common_sections"] = "pass" if headings[:len(common)] == common else "fail"
        assertions["workflow_sections"] = "pass" if headings[len(common):] == workflow else "fail"
        assertions["independent_version_labels"] = "pass" if (
            _usable_version(values.get("stateVersion"))
            and _usable_version(values.get("policyVersion"))
        ) else "fail"
        if case["routerInput"]["requestedOperation"] == "compound_review_fix":
            findings = after.find("Findings")
            assertions["review_first_ordering"] = "pass" if (
                findings >= 0
                and _has_authorized_follow_on_boundary(after[findings:])
            ) else "fail"
    observation = {
        "provenance": "approved_redacted",
        "responseSha256": _sha256(response),
        "responseBytes": len(response),
        "toolEventCount": len(tool_events),
        "assertions": assertions,
    }
    _validate_observation(observation)
    return observation


def _blocked_cli_evidence(
    mode: str,
    fixture: dict[str, Any],
    fixture_bytes: bytes,
    reason: str,
    snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _evidence(
        mode, fixture, fixture_bytes, [], snapshot=snapshot, blocker=reason,
        forced_status="blocked",
    )


def _invalid_fixture_evidence(mode: str, fixture_bytes: bytes) -> dict[str, Any]:
    return {
        "schemaVersion": "1.0",
        "sourceIssue": "DEV-136",
        "evidenceKind": "codex_skill_forward_test",
        "mode": mode,
        "status": "fail",
        "model": EXPECTED_MODEL,
        "codexVersion": EXPECTED_CODEX_VERSION,
        "fixtureSha256": _sha256(fixture_bytes),
        "host": _host_metadata(mode, blocker="fixture_contract_invalid"),
        "privacy": copy.deepcopy(PRIVACY),
        "summary": {
            "fixtureCaseCount": 0,
            "attemptedCount": 0,
            "passedCount": 0,
            "failedCount": 0,
            "blockedCount": 0,
            "notApplicableCount": 0,
        },
        "cases": [],
    }


def _existing_evidence_is_stale_success(path: Path) -> bool:
    try:
        value = _strict_json_loads(_read_regular_file_no_symlinks(path))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return False
    return (
        type(value) is dict
        and set(value) == EVIDENCE_KEYS
        and value.get("schemaVersion") == "1.0"
        and value.get("sourceIssue") == "DEV-136"
        and value.get("evidenceKind") == "codex_skill_forward_test"
        and value.get("status") == "pass"
    )


def _write_invalid_fixture_evidence_if_safe(
    path: Path, mode: str, fixture_bytes: bytes
) -> None:
    destination = path if path.is_absolute() else path.absolute()
    try:
        destination.lstat()
    except FileNotFoundError:
        should_write = True
    else:
        should_write = _existing_evidence_is_stale_success(destination)
    if should_write:
        evidence = _invalid_fixture_evidence(mode, fixture_bytes)
        _validate_private_evidence(evidence)
        _atomic_write_evidence(destination, evidence)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("offline", "host"), required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--codex-version", required=True)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--scorer-outputs", type=Path)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args(argv)

    fixture_bytes = b""
    try:
        fixture_bytes = args.cases.read_bytes()
        fixture = _strict_json_loads(fixture_bytes)
        _validate_fixture(fixture, fixture_bytes)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        try:
            _write_invalid_fixture_evidence_if_safe(
                args.evidence, args.mode, fixture_bytes
            )
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
            pass
        sys.stderr.write("fixture_contract_invalid\n")
        return FAIL
    if args.model != EXPECTED_MODEL or args.codex_version != EXPECTED_CODEX_VERSION:
        reason = "model_mismatch" if args.model != EXPECTED_MODEL else "version_mismatch"
        evidence = _blocked_cli_evidence(args.mode, fixture, fixture_bytes, reason)
        write_evidence(
            args.evidence, evidence, fixture=fixture, fixture_bytes=fixture_bytes,
            scorer_outputs={}, executable_sha256=None,
        )
        return BLOCKED

    if args.mode == "offline":
        if args.scorer_outputs is None:
            parser.error("--scorer-outputs is required in offline mode")
        try:
            scorer_outputs = _strict_json_loads(args.scorer_outputs.read_bytes())
            _validate_scorer_outputs(fixture, scorer_outputs)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
            evidence = _evidence(
                "offline", fixture, fixture_bytes, [], blocker="scoring_failed",
                forced_status="fail",
            )
            try:
                write_evidence(
                    args.evidence, evidence, fixture=fixture,
                    fixture_bytes=fixture_bytes, scorer_outputs={},
                )
            except (OSError, ValueError):
                pass
            sys.stderr.write("scorer_outputs_invalid\n")
            return FAIL
        code, evidence = run_offline(fixture, scorer_outputs, fixture_bytes=fixture_bytes)
        write_evidence(
            args.evidence, evidence, fixture=fixture, fixture_bytes=fixture_bytes,
            scorer_outputs=scorer_outputs,
        )
        return code

    executable = os.environ.get("CODEX_BIN", "codex")
    initial = default_prerequisite_checker(executable, EXPECTED_MODEL, EXPECTED_CODEX_VERSION)
    blocker = _precondition_blocker(initial)
    if blocker is not None:
        evidence = _blocked_cli_evidence("host", fixture, fixture_bytes, blocker, initial)
        write_evidence(
            args.evidence, evidence, fixture=fixture, fixture_bytes=fixture_bytes,
            scorer_outputs={}, executable_sha256=initial.get("executableSha256"),
        )
        return BLOCKED
    snapshots = [initial]

    def checker(binary: str, model: str, version: str) -> dict[str, Any]:
        if snapshots:
            return snapshots.pop(0)
        return default_prerequisite_checker(binary, model, version)

    host_results: list[dict[str, Any]] = []
    scorer_outputs: dict[str, dict[str, Any]] = {}
    code, evidence = run_host(
        fixture, executable, subprocess.run, checker, live_score,
        fixture_bytes=fixture_bytes, host_results_sink=host_results,
        scorer_outputs_sink=scorer_outputs,
    )
    write_evidence(
        args.evidence, evidence, fixture=fixture, fixture_bytes=fixture_bytes,
        scorer_outputs=scorer_outputs, host_results=host_results,
        executable_sha256=initial["executableSha256"],
    )
    return code


if __name__ == "__main__":
    raise SystemExit(main())
