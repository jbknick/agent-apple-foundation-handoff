#!/usr/bin/env python3
"""Deterministic, standard-library-only research proof for DEV-131."""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path, PurePosixPath


CHECK_IDS = {
    "D-SCHEMA-001",
    "D-ROUTE-001",
    "D-OWNER-001",
    "D-TRANSITION-001",
    "D-TOOL-001",
    "D-CONTEXT-001",
    "D-CONTEXT-002",
    "D-GRANT-001",
    "D-PHASE-001",
    "D-EFFECT-001",
    "D-EFFECT-002",
    "D-FALLBACK-001",
    "D-EVIDENCE-001",
    "D-RUBRIC-001",
}

RUBRIC_DIMENSIONS = {
    "handoff_architecture_fit",
    "context_preservation",
    "tool_authority_correctness",
    "failure_recovery_behavior",
    "security_privacy_discipline",
    "evidence_quality",
    "limitations_host_boundary_honesty",
}

CRITICAL_DIMENSIONS = {
    "tool_authority_correctness",
    "failure_recovery_behavior",
    "security_privacy_discipline",
    "limitations_host_boundary_honesty",
}

EVIDENCE_ALLOWLIST = {
    "summary.md",
    "checks.json",
    "commands.jsonl",
    "environment.json",
    "host-matrix.json",
    "rubric/architecture-response.synthetic.md",
    "rubric/assessment.json",
    "rubric/assessment.invalid.json",
}

EVIDENCE_CLASSIFICATIONS = {
    "synthetic",
    "normalized",
    "redacted-summary",
    "capability-fact",
    "derived-check",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _check(check_id: str, passed: bool) -> dict:
    return {"id": check_id, "status": "pass" if passed else "fail"}


def evaluate_case(case: dict) -> dict:
    """Evaluate one normalized fixture without reading its oracle."""

    checks: list[dict] = []
    schema_ok = (
        isinstance(case, dict)
        and case.get("schemaVersion") == "1.0"
        and isinstance(case.get("caseId"), str)
        and isinstance(case.get("workflow"), str)
        and isinstance(case.get("policy"), dict)
        and isinstance(case.get("result"), dict)
    )
    checks.append(_check("D-SCHEMA-001", schema_ok))

    policy = case.get("policy", {}) if isinstance(case, dict) else {}
    result = case.get("result", {}) if isinstance(case, dict) else {}

    route = policy.get("route", {})
    destination = result.get("destination")
    route_ok = (
        destination == route.get("requiredDestination")
        and destination in route.get("allowedDestinations", [])
    )
    checks.append(_check("D-ROUTE-001", route_ok))

    final_responses = [
        response
        for response in result.get("responses", [])
        if response.get("final") is True
    ]
    owner_ok = (
        len(final_responses) == 1
        and final_responses[0].get("actor") == policy.get("finalOwner")
    )
    checks.append(_check("D-OWNER-001", owner_ok))

    transitions = result.get("transitions", [])
    allowed_edges = {
        tuple(edge) for edge in policy.get("allowedEdges", []) if len(edge) == 2
    }
    transition_ok = len(transitions) <= policy.get("transitionBudget", -1)
    visited: set[str] = set()
    previous_to = None
    for transition in transitions:
        source = transition.get("from")
        destination_state = transition.get("to")
        if not visited:
            visited.add(source)
        if previous_to is not None and source != previous_to:
            transition_ok = False
        if (source, destination_state) not in allowed_edges:
            transition_ok = False
        if destination_state in visited:
            transition_ok = False
        visited.add(destination_state)
        previous_to = destination_state
    checks.append(_check("D-TRANSITION-001", transition_ok))

    tool_calls = result.get("toolCalls", [])
    tool_ok = len(tool_calls) <= policy.get("toolBudget", -1)
    tool_allowlist = policy.get("toolAllowlist", {})
    for call in tool_calls:
        if call.get("tool") not in tool_allowlist.get(call.get("actor"), []):
            tool_ok = False
    checks.append(_check("D-TOOL-001", tool_ok))

    context_policy = policy.get("contextPolicy", {})
    context_result = result.get("context", {})
    included = set(context_result.get("included", []))
    excluded = set(context_result.get("excluded", []))
    required = set(context_policy.get("required", []))
    forbidden = set(context_policy.get("forbidden", []))
    inclusion_ok = context_policy.get("declared") is True and required <= included
    exclusion_ok = not (forbidden & included) and forbidden <= excluded
    checks.append(_check("D-CONTEXT-001", inclusion_ok))
    checks.append(_check("D-CONTEXT-002", exclusion_ok))

    grant = result.get("grant", {})
    grant_ok = (
        grant.get("stateVersion") == policy.get("stateVersion")
        and grant.get("policyVersion") == policy.get("policyVersion")
    )
    checks.append(_check("D-GRANT-001", grant_ok))

    allowed_events = policy.get("validPhaseEvents", {})
    phase_ok = all(
        event.get("event") in allowed_events.get(event.get("phase"), [])
        for event in result.get("events", [])
    )
    checks.append(_check("D-PHASE-001", phase_ok))

    effects = result.get("effects", [])
    ledger_ok = all(effect.get("ledgerEntryCount") == 1 for effect in effects)
    replay_and_recovery_ok = all(
        effect.get("replayExecutorCommandCount") == 0
        and not (
            effect.get("uncertainCommit") is True
            and effect.get("retryAttempted") is True
            and effect.get("reconciledBeforeRetry") is not True
        )
        for effect in effects
    )
    checks.append(_check("D-EFFECT-001", ledger_ok))
    checks.append(_check("D-EFFECT-002", replay_and_recovery_ok))

    fallback_ok = result.get("fallback") in policy.get("allowedFallbacks", [])
    checks.append(_check("D-FALLBACK-001", fallback_ok))

    evidence = result.get("evidence", {})
    included_paths = evidence.get("includedPaths", [])
    safe_paths = all(
        isinstance(path, str)
        and not path.startswith(("/", "../"))
        and "raw-response" not in path.lower()
        and not path.lower().endswith(".trace")
        for path in included_paths
    )
    evidence_ok = (
        safe_paths
        and evidence.get("redacted") is True
        and evidence.get("hashesVerified") is True
        and evidence.get("containsRawTrace") is False
    )
    checks.append(_check("D-EVIDENCE-001", evidence_ok))

    violations = sorted(check["id"] for check in checks if check["status"] == "fail")
    return {
        "caseId": case.get("caseId"),
        "workflow": case.get("workflow"),
        "status": "pass" if not violations else "fail",
        "violations": violations,
        "checks": checks,
    }


def validate_rubric(response_path: Path, assessment: dict) -> dict:
    """Validate rubric integrity, not the reviewer's semantic judgment."""

    response_path = Path(response_path)
    response = response_path.read_text(encoding="utf-8") if response_path.is_file() else ""
    dimensions = assessment.get("dimensions", [])
    scores = {
        item.get("id"): item.get("score")
        for item in dimensions
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    ids_ok = set(scores) == RUBRIC_DIMENSIONS and len(dimensions) == 7
    entries_ok = ids_ok and all(
        isinstance(item.get("score"), int)
        and 1 <= item["score"] <= 4
        and isinstance(item.get("rationale"), str)
        and bool(item["rationale"].strip())
        and isinstance(item.get("anchor"), str)
        and bool(item["anchor"].strip())
        and item["anchor"] in response
        for item in dimensions
    )
    calculated_mean = sum(scores.values()) / 7 if ids_ok else 0.0
    thresholds = assessment.get("thresholds", {})
    declared_critical = set(thresholds.get("criticalDimensions", []))
    thresholds_ok = (
        thresholds.get("meanMinimum") == 3.0
        and thresholds.get("criticalMinimum") == 3
        and declared_critical == CRITICAL_DIMENSIONS
    )
    mean_ok = (
        isinstance(assessment.get("meanScore"), (int, float))
        and math.isclose(assessment["meanScore"], calculated_mean, abs_tol=0.005)
    )
    critical_ok = ids_ok and all(scores[dimension] >= 3 for dimension in CRITICAL_DIMENSIONS)
    computed_verdict = (
        "pass"
        if entries_ok and calculated_mean >= 3.0 and critical_ok
        else "fail"
    )
    integrity_ok = (
        assessment.get("schemaVersion") == "1.0"
        and assessment.get("reviewerType") == "human"
        and assessment.get("stimulusSha256") == _sha256(response_path)
        and thresholds_ok
        and entries_ok
        and mean_ok
        and assessment.get("verdict") == computed_verdict
        and computed_verdict == "pass"
    )
    violations = [] if integrity_ok else ["D-RUBRIC-001"]
    return {
        "status": "pass" if integrity_ok else "fail",
        "violations": violations,
        "check": _check("D-RUBRIC-001", integrity_ok),
        "scores": scores,
        "meanScore": round(calculated_mean, 2) if ids_ok else None,
        "semanticReviewer": assessment.get("reviewerType"),
    }


def validate_evidence_bundle(bundle_root: Path) -> dict:
    """Validate a safe, declared, hash-addressed evidence bundle."""

    bundle_root = Path(bundle_root)
    manifest_path = bundle_root / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        manifest = {}

    files = manifest.get("files", [])
    declared_paths = {
        item.get("path") for item in files if isinstance(item, dict)
    }
    actual_paths = {
        path.relative_to(bundle_root).as_posix()
        for path in bundle_root.rglob("*")
        if path.is_file() and path != manifest_path
    }
    valid = (
        manifest.get("schemaVersion") == "1.0"
        and manifest.get("issue") == "DEV-131"
        and len(files) == len(EVIDENCE_ALLOWLIST)
        and declared_paths == EVIDENCE_ALLOWLIST
        and actual_paths == EVIDENCE_ALLOWLIST
    )

    for item in files:
        relative = item.get("path")
        if not isinstance(relative, str):
            valid = False
            continue
        pure = PurePosixPath(relative)
        path = bundle_root / relative
        path_is_safe = (
            not pure.is_absolute()
            and ".." not in pure.parts
            and relative in EVIDENCE_ALLOWLIST
            and "raw-response" not in relative.lower()
            and "raw-prompt" not in relative.lower()
            and not relative.lower().endswith(".trace")
        )
        if (
            not path_is_safe
            or item.get("classification") not in EVIDENCE_CLASSIFICATIONS
            or not path.is_file()
            or path.is_symlink()
            or item.get("sha256") != _sha256(path)
        ):
            valid = False

    violations = [] if valid else ["D-EVIDENCE-001"]
    return {
        "status": "pass" if valid else "fail",
        "violations": violations,
        "check": _check("D-EVIDENCE-001", valid),
        "verifiedFileCount": len(files) if valid else 0,
    }


def _rate_metric(numerator: int, denominator: int) -> dict:
    if denominator == 0:
        return {
            "numerator": numerator,
            "denominator": denominator,
            "status": "not_applicable",
            "value": None,
        }
    return {
        "numerator": numerator,
        "denominator": denominator,
        "status": "pass",
        "value": numerator / denominator,
    }


def run(fixtures_root: Path) -> dict:
    fixtures_root = Path(fixtures_root)
    index = json.loads((fixtures_root / "index.json").read_text(encoding="utf-8"))
    case_results = []
    for oracle in index["cases"]:
        case = json.loads(
            (fixtures_root / oracle["path"]).read_text(encoding="utf-8")
        )
        observed = evaluate_case(case)
        oracle_match = (
            observed["status"] == oracle["expectedStatus"]
            and observed["violations"] == sorted(oracle["expectedViolations"])
        )
        case_results.append(
            {
                "id": oracle["id"],
                "status": observed["status"],
                "violations": observed["violations"],
                "oracleMatch": oracle_match,
            }
        )

    rubric_root = fixtures_root / "example-evidence/rubric"
    response_path = rubric_root / "architecture-response.synthetic.md"
    valid_rubric = validate_rubric(
        response_path,
        json.loads((rubric_root / "assessment.json").read_text(encoding="utf-8")),
    )
    invalid_rubric = validate_rubric(
        response_path,
        json.loads(
            (rubric_root / "assessment.invalid.json").read_text(encoding="utf-8")
        ),
    )
    rubric_gate_ok = (
        valid_rubric["status"] == "pass"
        and invalid_rubric["status"] == "fail"
        and invalid_rubric["violations"] == ["D-RUBRIC-001"]
    )
    evidence = validate_evidence_bundle(fixtures_root / "example-evidence")
    overall_ok = (
        all(case["oracleMatch"] for case in case_results)
        and rubric_gate_ok
        and evidence["status"] == "pass"
    )
    return {
        "schemaVersion": "1.0",
        "status": "pass" if overall_ok else "fail",
        "cases": case_results,
        "rubric": {
            "status": "pass" if rubric_gate_ok else "fail",
            "validAssessment": valid_rubric,
            "invalidAssessment": invalid_rubric,
        },
        "evidence": evidence,
        "metrics": {
            "optionalAppleEvaluationPassRate": _rate_metric(0, 0)
        },
    }


def main() -> int:
    result = run(Path(__file__).resolve().parent)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
