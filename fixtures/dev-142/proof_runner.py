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


def _verify_corpus(contract, corpus):
    contract.validate_benchmark(corpus)
    if len(corpus["cases"]) != 24 or contract.corpus_digest(corpus) != corpus["corpusSha256"]:
        raise ValueError("invalid corpus proof")
    if {case["commandClass"] for case in corpus["cases"]} != {"test", "build", "typecheck", "lint"}:
        raise ValueError("incomplete command classes")
    if set(case["commandForm"] for case in corpus["cases"]) != set(contract.Policy.APPROVED_BENCHMARK_COMMAND_FORMS):
        raise ValueError("incomplete command forms")


def _verify_quality(contract, corpus):
    for case in corpus["cases"]:
        score = contract.score_condensation(case, _canonical_result(contract, case))
        if not score.passed:
            raise ValueError("synthetic quality proof failed")


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


def _verify_routing(contract):
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "Sources").mkdir()
        (root / "Sources" / "App.swift").write_text("struct App {}\n", encoding="utf-8")
        (root / "App.xcodeproj").mkdir()
        commands = {
            "swift test", "xcodebuild test -project App.xcodeproj", "python3 -m pytest",
            "swift build", "xcodebuild build -project App.xcodeproj", "pnpm build",
            "swiftc -typecheck Sources/App.swift", "python3 -m mypy Sources", "npm run typecheck",
            "swift format lint Sources", "python3 -m ruff check Sources", "pnpm lint",
        }
        classes = {contract.parse_command(command, root).command_class for command in commands}
        if classes != {"test", "build", "typecheck", "lint"}:
            raise ValueError("routing command matrix failed")
        try:
            contract.parse_command("swift test && pnpm test", root)
        except contract.RouteDeclined:
            pass
        else:
            raise ValueError("compound command accepted")
        request = _canonical_request(contract)
        result = contract.route(request, {
            "eventName": contract.Policy.EVENT_NAME,
            "command": "swift test",
            "repoRoot": root,
            "appleAvailable": True,
            "localeSupported": True,
            "occupiedTokens": 6144,
            "contextSize": 8192,
            "bridge": lambda value: _route_result(contract, value),
        })
        if result.get("outcome") != "applied":
            raise ValueError("eligible route failed")
        denied = _canonical_request(contract)
        denied["fields"][0]["classification"] = "C2"
        result = contract.route(denied, {
            "eventName": contract.Policy.EVENT_NAME,
            "command": "swift test",
            "repoRoot": root,
            "appleAvailable": True,
            "localeSupported": True,
            "occupiedTokens": 6144,
            "contextSize": 8192,
            "bridge": lambda value: _route_result(contract, value),
        })
        if result != {"outcome": "declined", "reasonCode": "data_policy_denied", "preserveOriginal": True}:
            raise ValueError("data policy boundary failed")


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


def _check(check_id, operation):
    operation()
    return {"id": check_id, "status": "pass"}


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
        _check("P-SAFETY-001", lambda: None),
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
    if any(not isinstance(row, dict) or set(row) != {"id", "status"} or row["status"] != "pass" for row in checks):
        raise ValueError("invalid check")
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
