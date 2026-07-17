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
    "post_capture_prerequisite_drift",
    "process_failed",
    "scoring_failed",
}
PRE_RESPONSE_REASONS = {
    "missing_binary",
    "nonregular_binary",
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


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _compact_sha256(value: Any) -> str:
    return _sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )


def _fixture_contract() -> dict[str, Any]:
    raw = CANONICAL_FIXTURE.read_bytes()
    if _sha256(raw) != OFFICIAL_FIXTURE_SHA256:
        raise ValueError("canonical fixture identity mismatch")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("canonical fixture must be an object")
    return value


def _validate_fixture(fixture: dict[str, Any], fixture_bytes: bytes) -> None:
    if type(fixture) is not dict or type(fixture_bytes) is not bytes:
        raise ValueError("fixture and exact fixture bytes are required")
    try:
        decoded = json.loads(fixture_bytes)
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


def _prerequisite_statuses(snapshot: dict[str, Any] | None, blocker: str | None) -> dict[str, str]:
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
        "pluginActivation": "pass" if snapshot.get("pluginAvailable") is True else "blocked",
        "discovery": snapshot.get("discovery", "blocked"),
        "installation": snapshot.get("installation", "blocked"),
    }
    if blocker == "nonregular_binary":
        values["binary"] = "blocked"
    if blocker == "model_unavailable":
        values["model"] = "blocked"
    return values


def _host_metadata(
    mode: str,
    snapshot: dict[str, Any] | None = None,
    blocker: str | None = None,
) -> dict[str, Any]:
    return {
        "name": "codex",
        "version": EXPECTED_CODEX_VERSION,
        "model": EXPECTED_MODEL,
        "modelSelection": "explicit_cli_argument",
        "sessionMode": "fresh_ephemeral" if mode == "host" else "not_applicable",
        "resolvedExecutableSha256": None if snapshot is None else snapshot.get("executableSha256"),
        "prerequisites": _prerequisite_statuses(snapshot, blocker),
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
    return {
        "schemaVersion": "1.0",
        "sourceIssue": "DEV-136",
        "evidenceKind": "codex_skill_forward_test",
        "mode": mode,
        "status": status,
        "model": EXPECTED_MODEL,
        "codexVersion": EXPECTED_CODEX_VERSION,
        "fixtureSha256": _sha256(fixture_bytes),
        "host": _host_metadata(mode, snapshot, blocker),
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
    if type(scorer_outputs) is not dict or set(scorer_outputs) != {
        case["id"] for case in fixture["cases"]
    }:
        raise ValueError("offline scorer output identities do not match fixture")
    rows = []
    for ordinal, case in enumerate(fixture["cases"], 1):
        observation = scorer_outputs[case["id"]]
        _validate_observation(observation)
        rows.append(_row(fixture, case, ordinal, observation))
    evidence = _evidence("offline", fixture, fixture_bytes, rows)
    return _exit_for(evidence), evidence


def _assert_no_symlink_components(path: Path) -> None:
    absolute = path.absolute()
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current = current / part
        if current.is_symlink():
            raise ValueError("path indirection is not allowed")


def capture_executable(executable: str) -> dict[str, str]:
    path = Path(executable)
    if path.is_symlink():
        raise ValueError("path indirection is not allowed")
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode):
        raise ValueError("executable must be a regular file")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or opened.st_mode & 0o111 == 0
            or (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino)
        ):
            raise ValueError("executable changed during capture")
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
            raise ValueError("executable changed during capture")
    finally:
        os.close(descriptor)
    return {
        "resolvedExecutable": str(path.resolve()),
        "executableSha256": digest.hexdigest(),
    }


def _precondition_blocker(snapshot: dict[str, Any]) -> str | None:
    if snapshot.get("captureError") == "nonregular_binary":
        return "nonregular_binary"
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


def _tool_events(stdout: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line in stdout.splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if (
            type(value) is dict
            and value.get("type") == "item.completed"
            and type(value.get("item")) is dict
            and str(value["item"].get("type", "")).endswith("tool_call")
        ):
            events.append(value)
    return events


def _is_model_unavailable(completed: subprocess.CompletedProcess[str]) -> bool:
    diagnostic = f"{completed.stdout}\n{completed.stderr}"
    patterns = (
        r"(?i)\bmodel\b.{0,120}\b(?:unavailable|not available|not found|unsupported)\b",
        r"(?i)\b(?:no|not)\s+access\b.{0,120}\bmodel\b",
        r"(?i)\bmodel\b.{0,120}\b(?:access denied|permission denied)\b",
    )
    return any(re.search(pattern, diagnostic) is not None for pattern in patterns)


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
        blocker = _precondition_blocker(pre)
        if blocker is not None:
            evidence = _evidence(
                "host", fixture, fixture_bytes, rows, snapshot=first_snapshot,
                blocker=blocker, forced_status="blocked",
            )
            return BLOCKED, evidence

        descriptor, output_name = tempfile.mkstemp(prefix="dev136-codex-", suffix=".txt")
        os.close(descriptor)
        output_path = Path(output_name)
        completed: subprocess.CompletedProcess[str] | None = None
        process_error = False
        try:
            command = [
                executable, "exec", "--ephemeral", "--json", "-m", EXPECTED_MODEL,
                "--output-last-message", str(output_path), "-",
            ]
            try:
                completed = process_runner(
                    command,
                    input=case["prompt"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
            except Exception:
                process_error = True

            try:
                post = prerequisite_checker(executable, EXPECTED_MODEL, EXPECTED_CODEX_VERSION)
            except Exception:
                post = {}
            if _snapshot_identity(pre) != _snapshot_identity(post):
                evidence = _evidence(
                    "host", fixture, fixture_bytes, rows, snapshot=first_snapshot,
                    blocker="post_capture_prerequisite_drift", forced_status="fail",
                )
                return FAIL, evidence
            if completed is not None and completed.returncode != 0 and _is_model_unavailable(completed):
                evidence = _evidence(
                    "host", fixture, fixture_bytes, rows, snapshot=first_snapshot,
                    blocker="model_unavailable", forced_status="blocked",
                )
                return BLOCKED, evidence
            if process_error or completed is None or completed.returncode != 0:
                evidence = _evidence(
                    "host", fixture, fixture_bytes, rows, snapshot=first_snapshot,
                    blocker="process_failed", forced_status="fail",
                )
                return FAIL, evidence
            response = output_path.read_bytes()
            events = _tool_events(completed.stdout)
            host_result = {
                "codexExitCode": completed.returncode,
                "responseSha256": _sha256(response),
                "responseBytes": len(response),
                "toolEventCount": len(events),
            }
            if host_results_sink is not None:
                host_results_sink.append(copy.deepcopy(host_result))
            try:
                observation = scorer(case, response, events)
                _validate_observation(observation)
            except Exception:
                evidence = _evidence(
                    "host", fixture, fixture_bytes, rows, snapshot=first_snapshot,
                    blocker="scoring_failed", forced_status="fail",
                )
                return FAIL, evidence
            if scorer_outputs_sink is not None:
                scorer_outputs_sink[case["id"]] = copy.deepcopy(observation)
            rows.append(_row(fixture, case, ordinal, observation, host_result))
        finally:
            try:
                output_path.unlink()
            except FileNotFoundError:
                pass

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
    elif evidence["status"] == "pass":
        raise ValueError("partial evidence cannot pass")
    _validate_private_evidence(evidence)


def _open_destination_parent(path: Path) -> int:
    if path.parent.is_symlink():
        raise ValueError("evidence parent indirection is not allowed")
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path.parent, flags)
    try:
        opened = os.fstat(descriptor)
        current = os.stat(path.parent, follow_symlinks=False)
        if not stat.S_ISDIR(opened.st_mode) or (opened.st_dev, opened.st_ino) != (
            current.st_dev, current.st_ino
        ):
            raise ValueError("evidence parent changed during binding")
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


def _probe(command: list[str]) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            command, capture_output=True, text=True, check=False, timeout=20
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def _plugin_is_installed_enabled_with_capabilities(stdout: str) -> bool:
    try:
        listing = json.loads(stdout)
    except json.JSONDecodeError:
        return False
    if type(listing) is not dict or type(listing.get("installed")) is not list:
        return False
    plugin_id = "apple-foundation-models-handoff@agent-apple-foundation-handoff"
    matches = [
        item for item in listing["installed"]
        if type(item) is dict and item.get("pluginId") == plugin_id
    ]
    if len(matches) != 1:
        return False
    plugin = matches[0]
    if not (
        plugin.get("name") == "apple-foundation-models-handoff"
        and plugin.get("installed") is True
        and plugin.get("enabled") is True
    ):
        return False
    source = plugin.get("source")
    if type(source) is not dict or source.get("source") != "local":
        return False
    source_path = source.get("path")
    if type(source_path) is not str:
        return False
    manifest_path = Path(source_path) / ".codex-plugin/plugin.json"
    try:
        if manifest_path.is_symlink() or not manifest_path.is_file():
            return False
        manifest = json.loads(manifest_path.read_bytes())
    except (OSError, json.JSONDecodeError):
        return False
    interface = manifest.get("interface") if type(manifest) is dict else None
    capabilities = interface.get("capabilities") if type(interface) is dict else None
    return (
        manifest.get("name") == "apple-foundation-models-handoff"
        and capabilities == list(WORKFLOW_SECTIONS)
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
    except (OSError, ValueError):
        return {
            "resolvedExecutable": None, "executableSha256": None, "version": None,
            "authenticated": False, "modelAvailable": False, "pluginAvailable": False,
            "discovery": "blocked", "installation": "blocked",
            "captureError": "nonregular_binary",
        }
    version_probe = _probe([executable, "--version"])
    expected_version_line = f"codex-cli {EXPECTED_CODEX_VERSION}"
    observed_version = None
    if (
        version_probe is not None
        and version_probe.returncode == 0
        and version_probe.stderr == ""
        and version_probe.stdout == f"{expected_version_line}\n"
    ):
        observed_version = EXPECTED_CODEX_VERSION
    login_probe = _probe([executable, "login", "status"])
    authenticated = login_probe is not None and login_probe.returncode == 0
    plugin_probe = _probe([executable, "plugin", "list", "--json"])
    plugin_available = (
        plugin_probe is not None
        and plugin_probe.returncode == 0
        and plugin_probe.stderr == ""
        and _plugin_is_installed_enabled_with_capabilities(plugin_probe.stdout)
    )
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
        match = re.fullmatch(r"\s{2}([A-Za-z][A-Za-z0-9]*(?:\[\])?)\s*:\s*(.+)", raw_line)
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
    normalized = value.strip().strip('"\'').lower()
    return bool(normalized) and normalized not in {
        "unknown", "n/a", "none", "null", "tbd", "placeholder"
    } and "<" not in normalized and ">" not in normalized


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
            tail = after[findings:].lower() if findings >= 0 else ""
            assertions["review_first_ordering"] = "pass" if (
                findings >= 0
                and "authorized" in tail
                and "separate" in tail
                and ("follow-on" in tail or "follow on" in tail)
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("offline", "host"), required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--codex-version", required=True)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--scorer-outputs", type=Path)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args(argv)

    fixture_bytes = args.cases.read_bytes()
    fixture = json.loads(fixture_bytes)
    _validate_fixture(fixture, fixture_bytes)
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
        scorer_outputs = json.loads(args.scorer_outputs.read_bytes())
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
