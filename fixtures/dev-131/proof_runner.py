#!/usr/bin/env python3
"""Deterministic, standard-library-only research proof for DEV-131."""

from __future__ import annotations

import hashlib
import json
import math
import re
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
    "pattern_selection",
    "apple_api_grounding_version_labeling",
    "security_policy_completeness",
    "context_minimization",
    "failure_recovery_behavior",
    "testability_observability",
    "limitation_honesty",
}

CRITICAL_DIMENSIONS = {
    "security_policy_completeness",
    "failure_recovery_behavior",
    "limitation_honesty",
}

CANONICAL_PHASE_EVENTS = {
    "stable": ["propose"],
    "proposed": ["approve"],
    "executing": ["execute"],
    "recoveryRequired": ["reconcile"],
    "complete": ["finalize"],
}

EVIDENCE_PATH_CLASSIFICATIONS = {
    "summary.md": "redacted-summary",
    "checks.json": "derived-check",
    "commands.jsonl": "normalized",
    "environment.json": "capability-fact",
    "host-matrix.json": "capability-fact",
    "rubric/architecture-response.synthetic.md": "synthetic",
    "rubric/assessment.json": "synthetic",
    "rubric/assessment.invalid.json": "synthetic",
}
EVIDENCE_ALLOWLIST = set(EVIDENCE_PATH_CLASSIFICATIONS)

PROHIBITED_STRUCTURED_KEYS = {
    "api_key",
    "access_token",
    "password",
    "secret",
    "credential",
    "authorization",
    "raw_prompt",
    "raw_response",
    "hidden_reasoning",
    "chain_of_thought",
    "raw_trace",
    "instruments_trace",
    "trace_content",
    "trace_data",
    "hostname",
    "home_path",
    "username",
    "user_data",
    "real_user_data",
    "host_configuration",
    "private_host_configuration",
    "machine_configuration",
    "user_configuration",
    "authentication_state",
    "hardware_uuid",
    "serial_number",
    "provisioning_identifier",
}

PROHIBITED_TEXT_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----", re.IGNORECASE),
    re.compile(r"/(?:Users|home)/[^\s/]+", re.IGNORECASE),
    re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"),
    re.compile(
        r"^(?:#{1,6}\s*)?(?:raw prompt|raw response|hidden reasoning|"
        r"chain of thought|raw instruments trace|raw trace)\s*[:#]?\s*$",
        re.IGNORECASE | re.MULTILINE,
    ),
    re.compile(
        r"\b(?:api[_ -]?key|access[_ -]?token|password|secret|credential)\b"
        r"\s*[:=]\s*(?!<redacted>|\[redacted\]|null\b)[^\s,}]+",
        re.IGNORECASE,
    ),
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _check(check_id: str, passed: bool) -> dict:
    return {"id": check_id, "status": "pass" if passed else "fail"}


def _non_empty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _string_list(value: object) -> bool:
    return isinstance(value, list) and all(_non_empty_string(item) for item in value)


def _record_list(value: object, fields: dict[str, object]) -> bool:
    if not isinstance(value, list):
        return False
    for item in value:
        if not isinstance(item, dict):
            return False
        for field, validator in fields.items():
            if field not in item or not validator(item[field]):
                return False
    return True


def _valid_case_shape(case: object) -> bool:
    if not isinstance(case, dict):
        return False
    if (
        case.get("schemaVersion") != "1.0"
        or not _non_empty_string(case.get("caseId"))
        or not _non_empty_string(case.get("workflow"))
        or not isinstance(case.get("policy"), dict)
        or not isinstance(case.get("result"), dict)
    ):
        return False

    policy = case["policy"]
    result = case["result"]
    route = policy.get("route")
    context_policy = policy.get("contextPolicy")
    phase_policy = policy.get("validPhaseEvents")
    tool_allowlist = policy.get("toolAllowlist")
    if (
        not isinstance(route, dict)
        or not _non_empty_string(route.get("requiredDestination"))
        or not _string_list(route.get("allowedDestinations"))
        or not _non_empty_string(policy.get("finalOwner"))
        or not isinstance(policy.get("allowedEdges"), list)
        or not all(
            isinstance(edge, list)
            and len(edge) == 2
            and all(_non_empty_string(state) for state in edge)
            for edge in policy["allowedEdges"]
        )
        or not _integer(policy.get("transitionBudget"))
        or policy["transitionBudget"] < 0
        or not isinstance(tool_allowlist, dict)
        or not all(
            _non_empty_string(actor) and _string_list(tools)
            for actor, tools in tool_allowlist.items()
        )
        or not _integer(policy.get("toolBudget"))
        or policy["toolBudget"] < 0
        or not isinstance(context_policy, dict)
        or not isinstance(context_policy.get("declared"), bool)
        or not _string_list(context_policy.get("required"))
        or not _string_list(context_policy.get("forbidden"))
        or not _integer(policy.get("stateVersion"))
        or not _integer(policy.get("policyVersion"))
        or not isinstance(phase_policy, dict)
        or not all(
            _non_empty_string(phase) and _string_list(events)
            for phase, events in phase_policy.items()
        )
        or not _string_list(policy.get("allowedFallbacks"))
    ):
        return False

    responses_ok = _record_list(
        result.get("responses"),
        {"actor": _non_empty_string, "final": lambda value: isinstance(value, bool)},
    )
    transitions_ok = _record_list(
        result.get("transitions"),
        {"from": _non_empty_string, "to": _non_empty_string},
    )
    tool_calls_ok = _record_list(
        result.get("toolCalls"),
        {"actor": _non_empty_string, "tool": _non_empty_string},
    )
    events_ok = _record_list(
        result.get("events"),
        {"phase": _non_empty_string, "event": _non_empty_string},
    )
    ledger_ok = _record_list(
        result.get("effectLedger"), {"effectId": _non_empty_string}
    )
    commands_ok = _record_list(
        result.get("executorCommands"),
        {"effectId": _non_empty_string, "sourceObservation": _non_empty_string},
    )
    effects = result.get("effects")
    effects_ok = isinstance(effects, list) and all(
        isinstance(effect, dict)
        and _non_empty_string(effect.get("effectId"))
        and isinstance(effect.get("uncertainCommit"), bool)
        and isinstance(effect.get("retryAttempted"), bool)
        and _record_list(
            effect.get("observations"),
            {"kind": _non_empty_string, "effectId": _non_empty_string},
        )
        for effect in effects
    )
    context = result.get("context")
    grant = result.get("grant")
    evidence = result.get("evidence")
    return bool(
        _non_empty_string(result.get("destination"))
        and responses_ok
        and transitions_ok
        and tool_calls_ok
        and isinstance(context, dict)
        and _string_list(context.get("included"))
        and _string_list(context.get("excluded"))
        and isinstance(grant, dict)
        and _integer(grant.get("stateVersion"))
        and _integer(grant.get("policyVersion"))
        and events_ok
        and effects_ok
        and ledger_ok
        and commands_ok
        and _non_empty_string(result.get("fallback"))
        and isinstance(evidence, dict)
        and _string_list(evidence.get("includedPaths"))
        and isinstance(evidence.get("redacted"), bool)
        and isinstance(evidence.get("hashesVerified"), bool)
        and isinstance(evidence.get("containsRawTrace"), bool)
    )


def _case_result(case: object, checks: list[dict]) -> dict:
    violations = sorted(check["id"] for check in checks if check["status"] == "fail")
    return {
        "caseId": case.get("caseId") if isinstance(case, dict) else None,
        "workflow": case.get("workflow") if isinstance(case, dict) else None,
        "status": "pass" if not violations else "fail",
        "violations": violations,
        "checks": checks,
    }


def evaluate_case(case: dict) -> dict:
    """Evaluate one normalized fixture without reading its oracle."""

    schema_ok = _valid_case_shape(case)
    checks: list[dict] = [_check("D-SCHEMA-001", schema_ok)]
    if not schema_ok:
        return _case_result(case, checks)

    policy = case["policy"]
    result = case["result"]

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
    allowed_edges = {tuple(edge) for edge in policy["allowedEdges"]}
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

    events = result["events"]
    phase_ok = (
        bool(events)
        and bool(transitions)
        and policy["validPhaseEvents"] == CANONICAL_PHASE_EVENTS
        and all(
            event["event"] in CANONICAL_PHASE_EVENTS.get(event["phase"], [])
            for event in events
        )
    )
    if transition_ok:
        transition_path = (
            [transitions[0]["from"]] + [transition["to"] for transition in transitions]
            if transitions
            else []
        )
        phase_ok = phase_ok and len(events) == len(transition_path) and all(
            event["phase"] == transition_path[index]
            for index, event in enumerate(events)
        )

    recovery_required = any(effect["uncertainCommit"] for effect in result["effects"])
    if recovery_required:
        recovery_transition_indexes = [
            index
            for index, transition in enumerate(transitions)
            if transition["to"] == "recoveryRequired"
        ]
        recovery_event_indexes = [
            index
            for index, event in enumerate(events)
            if event == {"phase": "recoveryRequired", "event": "reconcile"}
        ]
        phase_ok = (
            phase_ok
            and len(recovery_transition_indexes) == 1
            and len(recovery_event_indexes) == 1
            and recovery_event_indexes[0] == recovery_transition_indexes[0] + 1
        )
    checks.append(_check("D-PHASE-001", phase_ok))

    effects = result["effects"]
    effect_ids = [effect["effectId"] for effect in effects]
    ledger_ids = [entry["effectId"] for entry in result["effectLedger"]]
    ledger_ok = (
        bool(effect_ids)
        and len(effect_ids) == len(set(effect_ids))
        and len(ledger_ids) == len(effect_ids)
        and set(ledger_ids) == set(effect_ids)
        and len(ledger_ids) == len(set(ledger_ids))
        and all(
            bool(effect["observations"])
            and all(
                observation["effectId"] == effect["effectId"]
                for observation in effect["observations"]
            )
            for effect in effects
        )
    )

    commands = result["executorCommands"]
    replay_and_recovery_ok = bool(effects)
    for effect in effects:
        effect_id = effect["effectId"]
        kinds = [observation["kind"] for observation in effect["observations"]]
        original_commands = [
            command
            for command in commands
            if command["effectId"] == effect_id
            and command["sourceObservation"] == "original"
        ]
        replay_commands = [
            command
            for command in commands
            if command["effectId"] == effect_id
            and command["sourceObservation"] == "replay"
        ]
        replay_and_recovery_ok = replay_and_recovery_ok and (
            kinds[0:1] == ["original"]
            and kinds[-1:] == ["replay"]
            and len(original_commands) == 1
            and not replay_commands
        )
        if effect["retryAttempted"]:
            replay_and_recovery_ok = replay_and_recovery_ok and (
                effect["uncertainCommit"]
                and kinds
                == [
                    "original",
                    "uncertain_commit",
                    "reconciliation",
                    "retry",
                    "replay",
                ]
            )
        elif effect["uncertainCommit"]:
            replay_and_recovery_ok = False
        else:
            replay_and_recovery_ok = replay_and_recovery_ok and kinds == [
                "original",
                "replay",
            ]

    replay_and_recovery_ok = replay_and_recovery_ok and all(
        command["effectId"] in set(effect_ids)
        and command["sourceObservation"] in {"original", "replay"}
        for command in commands
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

    return _case_result(case, checks)


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


def _normalized_key(key: str) -> str:
    camel_split = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", key)
    return re.sub(r"[^a-z0-9]+", "_", camel_split.lower()).strip("_")


def _text_is_safe(text: str) -> bool:
    return all(pattern.search(text) is None for pattern in PROHIBITED_TEXT_PATTERNS)


def _structured_content_is_safe(value: object) -> bool:
    if isinstance(value, dict):
        return all(
            _normalized_key(str(key)) not in PROHIBITED_STRUCTURED_KEYS
            and _structured_content_is_safe(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return all(_structured_content_is_safe(item) for item in value)
    if isinstance(value, str):
        return _text_is_safe(value)
    return value is None or isinstance(value, (bool, int, float))


def _evidence_content_is_safe(path: Path, relative: str) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    if not text.strip() or not _text_is_safe(text):
        return False

    if relative.endswith(".md"):
        return relative in {
            "summary.md",
            "rubric/architecture-response.synthetic.md",
        }
    if relative.endswith(".json"):
        try:
            value = json.loads(text)
        except json.JSONDecodeError:
            return False
        return isinstance(value, dict) and _structured_content_is_safe(value)
    if relative == "commands.jsonl":
        records = []
        try:
            records = [json.loads(line) for line in text.splitlines() if line.strip()]
        except json.JSONDecodeError:
            return False
        return bool(records) and all(
            isinstance(record, dict)
            and set(record) == {"command", "cwd", "exitCode", "outputClass"}
            and _non_empty_string(record["command"])
            and record["cwd"] == "<repo>"
            and _integer(record["exitCode"])
            and _non_empty_string(record["outputClass"])
            and _structured_content_is_safe(record)
            for record in records
        )
    return False


def validate_evidence_bundle(bundle_root: Path) -> dict:
    """Validate a safe, declared, hash-addressed evidence bundle."""

    bundle_root = Path(bundle_root)
    manifest_path = bundle_root / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        manifest = {}

    declared_files = manifest.get("files", [])
    files = declared_files if isinstance(declared_files, list) else []
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
        and _structured_content_is_safe(manifest)
        and isinstance(declared_files, list)
        and len(files) == len(EVIDENCE_ALLOWLIST)
        and declared_paths == EVIDENCE_ALLOWLIST
        and actual_paths == EVIDENCE_ALLOWLIST
    )

    for item in files:
        if not isinstance(item, dict):
            valid = False
            continue
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
        content_is_safe = path.is_file() and _evidence_content_is_safe(path, relative)
        hash_matches = content_is_safe and item.get("sha256") == _sha256(path)
        if (
            not path_is_safe
            or item.get("classification")
            != EVIDENCE_PATH_CLASSIFICATIONS.get(relative)
            or not path.is_file()
            or path.is_symlink()
            or not content_is_safe
            or not hash_matches
        ):
            valid = False

    # Scan the assembled allowlist a second time after hash validation. The
    # manifest hash can never turn prohibited content into safe evidence.
    if valid and not all(
        _evidence_content_is_safe(bundle_root / relative, relative)
        for relative in EVIDENCE_ALLOWLIST
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
