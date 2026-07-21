#!/usr/bin/env python3
"""Emit deterministic, metadata-only verification evidence for DEV-142."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import tempfile


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "fixtures" / "dev-142" / "runtime_contract.py"
CORPUS_PATH = ROOT / "fixtures" / "dev-142" / "benchmark-corpus.json"
SCHEMA_PATHS = tuple(sorted((ROOT / "schemas").glob("dev-142-*.schema.json")))
CHECK_IDS = (
    "P-BOUNDARY-001",
    "P-CORPUS-001",
    "P-NORMALIZATION-001",
    "P-QUALITY-001",
    "P-RELEASE-001",
    "P-ROUTING-001",
    "P-SAFETY-001",
    "P-SCHEMA-001",
)
ROUTING_BOUNDARIES = (
    "R-ACCEPT-TEST-001", "R-ACCEPT-TEST-002", "R-ACCEPT-TEST-003",
    "R-ACCEPT-BUILD-001", "R-ACCEPT-BUILD-002", "R-ACCEPT-BUILD-003",
    "R-ACCEPT-TYPECHECK-001", "R-ACCEPT-TYPECHECK-002", "R-ACCEPT-TYPECHECK-003",
    "R-ACCEPT-LINT-001", "R-ACCEPT-LINT-002", "R-ACCEPT-LINT-003",
    "R-EVENT-001", "R-TOOL-001", "R-ACTION-001", "R-POLICY-001",
    "R-COMMAND-001", "R-COMPOUND-001", "R-INPUT-8191", "R-INPUT-8192",
    "R-INPUT-65536", "R-INPUT-65537", "R-ESTIMATED-4095", "R-ESTIMATED-4096",
    "R-REALIZED-4095", "R-REALIZED-4096", "R-OCCUPANCY-75-PASS",
    "R-OCCUPANCY-75-FAIL", "R-CLASS-C2", "R-CLASS-C3", "R-CLASS-UNKNOWN",
    "R-CLASS-UNCLASSIFIED", "R-PROVENANCE-MIXED", "R-FILE-INVALID",
    "R-FILE-MISSING", "R-FILE-NONCONTAINED", "R-APPLE-UNAVAILABLE",
    "R-LOCALE-UNSUPPORTED", "R-MALFORMED-RESPONSE", "R-BRIDGE-DECLINE",
    "R-BRIDGE-FAIL", "R-BRIDGE-EXCEPTION", "R-APPLIED-001",
)
SAFETY_BOUNDARIES = (
    "S-PRIVATE-KEY-001", "S-PRIVATE-PATH-001", "S-RAW-PROMPT-001",
    "S-RAW-RESULT-001", "S-RAW-RESPONSE-001", "S-CREDENTIAL-001",
    "S-TRACE-001", "S-XCRESULT-001", "S-SELF-ATTEST-001",
    "S-EXTRA-KEY-001", "S-STATUS-001", "S-LIVE-CLAIM-001",
)
LIVE_CLAIMS = {
    "appleInvocation": "not_applicable",
    "codexHook": "not_applicable",
    "claudeHook": "not_applicable",
    "parentTokenReduction": "blocked/provider_usage_not_executed",
}
EVIDENCE_KEYS = {
    "schemaVersion", "issue", "status", "policyVersion", "action", "schemaCount",
    "eligibleCaseCount", "requiredPairCount", "corpusSha256", "checks", "liveClaims",
}
FORBIDDEN_METADATA = (
    "api_key", "credential", "password", "secret", "rawprompt", "rawresult",
    "rawresponse", "trace", "xcresult", "modelcorrectness", "selfattested",
)


def _contract():
    spec = importlib.util.spec_from_file_location("dev142_runtime_contract", CONTRACT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _canonical_result(contract, case):
    expected = case["expected"]
    diagnostics = [
        contract._diagnostic_for_case(case, diagnostic_id)
        for diagnostic_id in expected["requiredDiagnosticIDs"]
    ]
    return {
        "schemaVersion": contract.Policy.SCHEMA_VERSION,
        "policyVersion": contract.Policy.POLICY_VERSION,
        "callID": "proof-call",
        "toolName": contract.Policy.TOOL_NAME,
        "toolVersion": "0.144.5",
        "stateVersion": "proof-state-v1",
        "action": contract.Policy.ACTION,
        "commandClass": case["commandClass"],
        "originalResultType": "text",
        "originalResultDigest": case["renderedSha256"],
        "outcome": "applied",
        "exitStatus": expected["exitStatus"],
        "interrupted": expected["interrupted"],
        "resultType": contract.Policy.RESULT_TYPE,
        "condensation": {
            "summary": contract._case_summary(case),
            "diagnostics": diagnostics,
            "warningCount": expected["warningCount"],
            "omittedWarningCount": 0,
        },
    }


def _canonical_request(contract, command_class="test"):
    return {
        "schemaVersion": contract.Policy.SCHEMA_VERSION,
        "policyVersion": contract.Policy.POLICY_VERSION,
        "callID": "proof-route-call",
        "toolName": contract.Policy.TOOL_NAME,
        "toolVersion": "0.144.5",
        "stateVersion": "proof-state-v1",
        "action": contract.Policy.ACTION,
        "commandClass": command_class,
        "originalResultType": "text",
        "originalResultDigest": "a" * 64,
        "exitStatus": 1,
        "interrupted": False,
        "inputBytes": contract.Policy.MINIMUM_INPUT_BYTES,
        "estimatedSavingsBytes": contract.Policy.MINIMUM_ESTIMATED_SAVINGS_BYTES,
        "fields": [{
            "name": "message",
            "value": "synthetic diagnostic",
            "origin": "trustedLocal",
            "classification": "C1",
            "purpose": "diagnostic_condensation",
            "destination": "apple_on_device",
            "retention": "ephemeral",
            "redacted": False,
        }],
    }


def _route_result(contract, request):
    return {
        "schemaVersion": request["schemaVersion"],
        "policyVersion": request["policyVersion"],
        "callID": request["callID"],
        "toolName": request["toolName"],
        "toolVersion": request["toolVersion"],
        "stateVersion": request["stateVersion"],
        "action": request["action"],
        "commandClass": request["commandClass"],
        "originalResultType": request["originalResultType"],
        "originalResultDigest": request["originalResultDigest"],
        "outcome": "applied",
        "exitStatus": request["exitStatus"],
        "interrupted": request["interrupted"],
        "resultType": contract.Policy.RESULT_TYPE,
        "condensation": {
            "summary": "synthetic route proof",
            "diagnostics": [],
            "warningCount": 0,
            "omittedWarningCount": 0,
        },
    }


def _verify_schemas(contract):
    if len(SCHEMA_PATHS) != 3:
        raise ValueError("unexpected schema count")
    for path in SCHEMA_PATHS:
        contract.load_closed_json(path)
    return ("D-SCHEMA-001",)


def _verify_corpus(contract, corpus):
    contract.validate_benchmark(corpus)
    if len(corpus["cases"]) != 24 or contract.corpus_digest(corpus) != corpus["corpusSha256"]:
        raise ValueError("invalid corpus proof")
    if {case["commandClass"] for case in corpus["cases"]} != {"test", "build", "typecheck", "lint"}:
        raise ValueError("incomplete command classes")
    if set(case["commandForm"] for case in corpus["cases"]) != set(contract.Policy.APPROVED_BENCHMARK_COMMAND_FORMS):
        raise ValueError("incomplete command forms")
    return ("D-CORPUS-001",)


def _verify_quality(contract, corpus):
    for case in corpus["cases"]:
        score = contract.score_condensation(case, _canonical_result(contract, case))
        if not score.passed:
            raise ValueError("synthetic quality proof failed")
    return ("D-QUALITY-001",)


def _verify_boundaries(contract):
    rows = {row["id"]: row for row in contract.benchmark_boundaries()}
    if contract.estimate_savings(rows["minimum-input"]["inputBytes"]) != 4096:
        raise ValueError("minimum input boundary failed")
    if contract.estimate_savings(rows["maximum-input"]["inputBytes"]) != 61440:
        raise ValueError("maximum input boundary failed")
    for row_id in ("below-input-minimum", "above-input-maximum"):
        try:
            contract.estimate_savings(rows[row_id]["inputBytes"])
        except contract.RouteDeclined:
            continue
        raise ValueError("rejected input boundary accepted")
    if not contract.fits_apple_budget(6144, 8192) or contract.fits_apple_budget(6145, 8192):
        raise ValueError("context boundary failed")
    return ("D-INPUT-001", "D-OCCUPANCY-001")


def _route_result_with_size(contract, request, output_bytes):
    result = _route_result(contract, request)
    baseline = contract._response_bytes(result)
    if output_bytes < baseline:
        raise ValueError("invalid proof response size")
    result["condensation"]["summary"] = "x" * (
        len(result["condensation"]["summary"]) + output_bytes - baseline
    )
    if contract._response_bytes(result) != output_bytes:
        raise ValueError("unstable proof response size")
    return result


def _non_applied_result(contract, request, outcome):
    result = _route_result(contract, request)
    result.pop("resultType")
    result.pop("condensation")
    result["outcome"] = outcome
    result["reasonCode"] = "generation_declined"
    return result


def _verify_routing(contract):
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "Sources").mkdir()
        (root / "Sources" / "App.swift").write_text("struct App {}\n", encoding="utf-8")
        (root / "App.xcodeproj").mkdir()
        accepted = (
            ("R-ACCEPT-TEST-001", "swift test", "test"),
            ("R-ACCEPT-TEST-002", "xcodebuild test -project App.xcodeproj", "test"),
            ("R-ACCEPT-TEST-003", "python3 -m pytest", "test"),
            ("R-ACCEPT-BUILD-001", "swift build", "build"),
            ("R-ACCEPT-BUILD-002", "xcodebuild build -project App.xcodeproj", "build"),
            ("R-ACCEPT-BUILD-003", "pnpm build", "build"),
            ("R-ACCEPT-TYPECHECK-001", "swiftc -typecheck Sources/App.swift", "typecheck"),
            ("R-ACCEPT-TYPECHECK-002", "python3 -m mypy Sources", "typecheck"),
            ("R-ACCEPT-TYPECHECK-003", "npm run typecheck", "typecheck"),
            ("R-ACCEPT-LINT-001", "swift format lint Sources", "lint"),
            ("R-ACCEPT-LINT-002", "python3 -m ruff check Sources", "lint"),
            ("R-ACCEPT-LINT-003", "pnpm lint", "lint"),
        )
        for boundary_id, command, command_class in accepted:
            if contract.parse_command(command, root).command_class != command_class:
                raise ValueError(f"failed {boundary_id}")

        def route_case(boundary_id, request_change, context_change, bridge_factory, expected, expected_calls):
            request = _canonical_request(contract)
            request_change(request)
            calls = []

            def bridge(value):
                calls.append(value)
                return bridge_factory(value)

            context = {
                "eventName": contract.Policy.EVENT_NAME,
                "command": "swift test",
                "repoRoot": root,
                "appleAvailable": True,
                "localeSupported": True,
                "occupiedTokens": 6144,
                "contextSize": 8192,
                "bridge": bridge,
            }
            context_change(context)
            result = contract.route(request, context)
            if result != expected(request) or len(calls) != expected_calls:
                raise ValueError(f"failed {boundary_id}")

        applied = lambda request: _route_result(contract, request)
        fallback = lambda outcome, reason: lambda _request: {
            "outcome": outcome, "reasonCode": reason, "preserveOriginal": True,
        }
        no_request_change = lambda _request: None
        no_context_change = lambda _context: None
        preflight_rows = (
            ("R-EVENT-001", no_request_change, lambda context: context.update(eventName="PreToolUse"), fallback("declined", "tool_not_allowed")),
            ("R-TOOL-001", lambda request: request.update(toolName="Read"), no_context_change, fallback("declined", "tool_not_allowed")),
            ("R-ACTION-001", lambda request: request.update(action="other"), no_context_change, fallback("fail", "contract_invariant_failed")),
            ("R-POLICY-001", lambda request: request.update(policyVersion="diagnostic-condensation-v2"), no_context_change, fallback("fail", "contract_invariant_failed")),
            ("R-COMMAND-001", no_request_change, lambda context: context.update(command="echo rejected"), fallback("declined", "command_not_allowed")),
            ("R-COMPOUND-001", no_request_change, lambda context: context.update(command="swift test && pnpm test"), fallback("declined", "compound_command")),
            ("R-INPUT-8191", lambda request: request.update(inputBytes=8191, estimatedSavingsBytes=4095), no_context_change, fallback("declined", "input_below_minimum")),
            ("R-INPUT-65537", lambda request: request.update(inputBytes=65537, estimatedSavingsBytes=61441), no_context_change, fallback("declined", "input_above_maximum")),
            ("R-ESTIMATED-4095", lambda request: request.update(estimatedSavingsBytes=4095), no_context_change, fallback("fail", "contract_invariant_failed")),
            ("R-OCCUPANCY-75-FAIL", no_request_change, lambda context: context.update(occupiedTokens=6145), fallback("declined", "context_budget_exceeded")),
            ("R-CLASS-C2", lambda request: request["fields"][0].update(classification="C2"), no_context_change, fallback("declined", "data_policy_denied")),
            ("R-CLASS-C3", lambda request: request["fields"][0].update(classification="C3"), no_context_change, fallback("declined", "data_policy_denied")),
            ("R-CLASS-UNKNOWN", lambda request: request["fields"][0].update(classification="C9"), no_context_change, fallback("declined", "data_policy_denied")),
            ("R-CLASS-UNCLASSIFIED", lambda request: request["fields"][0].pop("classification"), no_context_change, fallback("declined", "data_policy_denied")),
            ("R-PROVENANCE-MIXED", lambda request: request["fields"][0].update(origin="remote"), no_context_change, fallback("declined", "data_policy_denied")),
            ("R-FILE-INVALID", lambda request: request.update(fields=[{**request["fields"][0], "name": "file", "value": "Sources\\App.swift"}]), no_context_change, fallback("declined", "data_policy_denied")),
            ("R-FILE-MISSING", lambda request: request.update(fields=[{**request["fields"][0], "name": "file", "value": "Missing.swift"}]), no_context_change, fallback("declined", "data_policy_denied")),
            ("R-FILE-NONCONTAINED", lambda request: request.update(fields=[{**request["fields"][0], "name": "file", "value": "../outside.swift"}]), no_context_change, fallback("declined", "data_policy_denied")),
            ("R-APPLE-UNAVAILABLE", no_request_change, lambda context: context.update(appleAvailable=False), fallback("declined", "apple_unavailable")),
            ("R-LOCALE-UNSUPPORTED", no_request_change, lambda context: context.update(localeSupported=False), fallback("declined", "locale_unsupported")),
        )
        for boundary_id, request_change, context_change, expected in preflight_rows:
            route_case(boundary_id, request_change, context_change, applied, expected, 0)

        postflight_rows = (
            ("R-INPUT-8192", lambda request: request.update(inputBytes=8192, estimatedSavingsBytes=4096), no_context_change, applied, applied),
            ("R-INPUT-65536", lambda request: request.update(inputBytes=65536, estimatedSavingsBytes=61440), no_context_change, applied, applied),
            ("R-ESTIMATED-4096", lambda request: request.update(estimatedSavingsBytes=4096), no_context_change, applied, applied),
            ("R-OCCUPANCY-75-PASS", no_request_change, no_context_change, applied, applied),
            ("R-REALIZED-4095", no_request_change, no_context_change, lambda request: _route_result_with_size(contract, request, 4097), fallback("declined", "insufficient_realized_savings")),
            ("R-REALIZED-4096", no_request_change, no_context_change, lambda request: _route_result_with_size(contract, request, 4096), lambda request: _route_result_with_size(contract, request, 4096)),
            ("R-MALFORMED-RESPONSE", no_request_change, no_context_change, lambda _request: {"outcome": "applied"}, fallback("fail", "invalid_response")),
            ("R-BRIDGE-DECLINE", no_request_change, no_context_change, lambda _request: (_ for _ in ()).throw(contract.RouteDeclined("generation_declined")), fallback("declined", "generation_declined")),
            ("R-BRIDGE-FAIL", no_request_change, no_context_change, lambda request: _non_applied_result(contract, request, "fail"), fallback("fail", "generation_declined")),
            ("R-BRIDGE-EXCEPTION", no_request_change, no_context_change, lambda _request: (_ for _ in ()).throw(RuntimeError("synthetic")), fallback("fail", "contract_invariant_failed")),
            ("R-APPLIED-001", no_request_change, no_context_change, applied, applied),
        )
        for boundary_id, request_change, context_change, bridge_factory, expected in postflight_rows:
            route_case(boundary_id, request_change, context_change, bridge_factory, expected, 1)
    return tuple(sorted(ROUTING_BOUNDARIES))


def _arm(contract, host, case_id, arm, input_tokens, output_tokens):
    usage = contract.normalize_usage("openai-responses-usage-v1", {
        "input_tokens": input_tokens,
        "cached_tokens": 0,
        "output_tokens": output_tokens,
        "reasoning_tokens": 0,
    })
    return {
        "host": host,
        "caseID": case_id,
        "workflow": "diagnostic-condensation",
        "parentModel": "proof-parent-model-v1",
        "provider": usage.provider,
        "normalizationVersion": usage.provider,
        "toolchain": "offline-contract-v1",
        "policyVersion": contract.Policy.POLICY_VERSION,
        "commandClass": "test",
        "arm": arm,
        "usage": usage,
        "parentTurns": 1,
        "quality": contract.QualityScore(True, ()),
    }


def _verify_normalization_and_release(contract):
    openai = contract.normalize_usage("openai-responses-usage-v1", {
        "input_tokens": 900, "cached_tokens": 200, "output_tokens": 100, "reasoning_tokens": 50,
    })
    anthropic = contract.normalize_usage("anthropic-messages-usage-v1", {
        "input_tokens": 700, "cache_read_input_tokens": 200,
        "cache_creation_input_tokens": 100, "output_tokens": 100,
    })
    if (openai.total_parent_model_tokens, anthropic.total_parent_model_tokens, anthropic.reasoning_tokens) != (1000, 1100, None):
        raise ValueError("provider normalization failed")
    pairs = []
    for host, case_id in contract.REQUIRED_PAIR_IDENTITIES:
        off = _arm(contract, host, case_id, "pluginOff", 900, 100)
        on = _arm(contract, host, case_id, "pluginOn", 810, 90)
        pairs.append(contract.score_pair(off, on))
    release = contract.release_gate(pairs)
    if (release.status, release.valid_required_pairs, release.blocked_required_pairs,
            release.median_reduction_ppm, release.correctness_regressions,
            release.additional_parent_model_turns) != ("pass", 48, 0, 100000, 0, 0):
        raise ValueError("release gate failed")
    return ("D-NORMALIZATION-001", "D-RELEASE-001")


def _check(check_id, operation):
    boundaries = operation()
    if type(boundaries) is not tuple or not boundaries:
        raise ValueError("missing proof boundaries")
    return {"id": check_id, "status": "pass", "boundaries": sorted(boundaries)}


def _evidence_copy(evidence):
    return json.loads(json.dumps(evidence, ensure_ascii=False))


def _verify_safety(evidence):
    mutations = (
        ("S-PRIVATE-KEY-001", lambda value: value.update(privateKey="redacted")),
        ("S-PRIVATE-PATH-001", lambda value: value.update(privatePath="/Users/example/private")),
        ("S-RAW-PROMPT-001", lambda value: value.update(rawPrompt="synthetic")),
        ("S-RAW-RESULT-001", lambda value: value.update(rawResult="synthetic")),
        ("S-RAW-RESPONSE-001", lambda value: value.update(rawResponse="synthetic")),
        ("S-CREDENTIAL-001", lambda value: value.update(credential="redacted")),
        ("S-TRACE-001", lambda value: value.update(trace="output.trace")),
        ("S-XCRESULT-001", lambda value: value.update(xcresult="output.xcresult")),
        ("S-SELF-ATTEST-001", lambda value: value.update(modelCorrectness="self-attested")),
        ("S-EXTRA-KEY-001", lambda value: value.update(extra=True)),
        ("S-STATUS-001", lambda value: value.update(status="blocked")),
        ("S-LIVE-CLAIM-001", lambda value: value["liveClaims"].update(parentTokenReduction="pass")),
    )
    observed = []
    for boundary_id, mutate in mutations:
        candidate = _evidence_copy(evidence)
        mutate(candidate)
        try:
            validate_evidence(candidate)
        except ValueError:
            observed.append(boundary_id)
            continue
        raise ValueError(f"unsafe evidence accepted: {boundary_id}")
    if tuple(sorted(observed)) != tuple(sorted(SAFETY_BOUNDARIES)):
        raise ValueError("incomplete safety proof")
    return tuple(sorted(observed))


def build_evidence():
    contract = _contract()
    corpus = contract.load_closed_json(CORPUS_PATH)
    checks = [
        _check("P-SCHEMA-001", lambda: _verify_schemas(contract)),
        _check("P-CORPUS-001", lambda: _verify_corpus(contract, corpus)),
        _check("P-QUALITY-001", lambda: _verify_quality(contract, corpus)),
        _check("P-BOUNDARY-001", lambda: _verify_boundaries(contract)),
        _check("P-ROUTING-001", lambda: _verify_routing(contract)),
        _check("P-NORMALIZATION-001", lambda: _verify_normalization_and_release(contract)),
        _check("P-RELEASE-001", lambda: _verify_normalization_and_release(contract)),
        {"id": "P-SAFETY-001", "status": "pass", "boundaries": sorted(SAFETY_BOUNDARIES)},
    ]
    evidence = {
        "schemaVersion": 1,
        "issue": "DEV-142",
        "status": "pass",
        "policyVersion": contract.Policy.POLICY_VERSION,
        "action": contract.Policy.ACTION,
        "schemaCount": len(SCHEMA_PATHS),
        "eligibleCaseCount": len(corpus["cases"]),
        "requiredPairCount": len(contract.REQUIRED_PAIR_IDENTITIES),
        "corpusSha256": contract.corpus_digest(corpus),
        "checks": sorted(checks, key=lambda row: row["id"]),
        "liveClaims": dict(LIVE_CLAIMS),
    }
    _verify_safety(evidence)
    validate_evidence(evidence)
    return evidence


def _safe_metadata(value):
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = "".join(character for character in key.lower() if character.isalnum())
            if any(term in normalized for term in FORBIDDEN_METADATA):
                return False
            if not _safe_metadata(item):
                return False
    elif isinstance(value, list):
        return all(_safe_metadata(item) for item in value)
    elif isinstance(value, str):
        lowered = value.lower()
        if "/users/" in lowered or "/home/" in lowered or ".trace" in lowered or ".xcresult" in lowered:
            return False
    return True


def validate_evidence(evidence):
    contract = _contract()
    corpus = contract.load_closed_json(CORPUS_PATH)
    if not isinstance(evidence, dict) or set(evidence) != EVIDENCE_KEYS or not _safe_metadata(evidence):
        raise ValueError("unsafe evidence")
    expected = {
        "schemaVersion": 1,
        "issue": "DEV-142",
        "status": "pass",
        "policyVersion": contract.Policy.POLICY_VERSION,
        "action": contract.Policy.ACTION,
        "schemaCount": 3,
        "eligibleCaseCount": 24,
        "requiredPairCount": 48,
        "corpusSha256": contract.corpus_digest(corpus),
        "liveClaims": LIVE_CLAIMS,
    }
    if any(evidence.get(key) != value for key, value in expected.items()):
        raise ValueError("invalid evidence metadata")
    checks = evidence.get("checks")
    if not isinstance(checks, list) or checks != sorted(checks, key=lambda row: row.get("id", "")):
        raise ValueError("unordered checks")
    if {row.get("id") for row in checks if isinstance(row, dict)} != set(CHECK_IDS):
        raise ValueError("unexpected checks")
    if any(
        not isinstance(row, dict)
        or set(row) != {"id", "status", "boundaries"}
        or row["status"] != "pass"
        or type(row["boundaries"]) is not list
        or not row["boundaries"]
        or row["boundaries"] != sorted(row["boundaries"])
        or any(type(boundary) is not str or not boundary for boundary in row["boundaries"])
        for row in checks
    ):
        raise ValueError("invalid check")
    rows = {row["id"]: row for row in checks}
    if tuple(rows["P-ROUTING-001"]["boundaries"]) != tuple(sorted(ROUTING_BOUNDARIES)):
        raise ValueError("incomplete routing proof")
    if tuple(rows["P-SAFETY-001"]["boundaries"]) != tuple(sorted(SAFETY_BOUNDARIES)):
        raise ValueError("incomplete safety proof")
    return evidence


def _encode(evidence):
    return (json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def write_evidence(path, evidence):
    target = Path(path)
    data = _encode(evidence)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args(argv)
    evidence = build_evidence()
    if arguments.output is None:
        print(_encode(evidence).decode("utf-8"), end="")
    else:
        write_evidence(arguments.output, evidence)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
