#!/usr/bin/env python3
"""Emit deterministic, metadata-only verification evidence for DEV-142."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
from pathlib import Path
import re
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
    "R-SECRET-001", "R-CANONICAL-BYTES-001", "R-ISOLATED-REQUEST-001",
    "R-RESPONSE-BINDINGS-001", "R-RESPONSE-SEMANTICS-001",
    "R-PATH-RECHECK-001", "R-QUOTED-PYTEST-001", "R-FLAG-ORDER-001",
)
SAFETY_BOUNDARIES = (
    "S-PRIVATE-KEY-001", "S-PRIVATE-PATH-001", "S-RAW-PROMPT-001",
    "S-RAW-RESULT-001", "S-RAW-RESPONSE-001", "S-CREDENTIAL-001",
    "S-TRACE-001", "S-XCRESULT-001", "S-SELF-ATTEST-001",
    "S-EXTRA-KEY-001", "S-STATUS-001", "S-LIVE-CLAIM-001",
    "S-PRIVATE-POSIX-001", "S-WINDOWS-PATH-001", "S-UNC-PATH-001",
    "S-CREDENTIAL-VALUE-001", "S-NESTED-KEY-001",
)
EXPECTED_BOUNDARIES = {
    "P-BOUNDARY-001": ("D-INPUT-001", "D-INTERRUPTION-001", "D-OCCUPANCY-001"),
    "P-CORPUS-001": ("D-CORPUS-001",),
    "P-NORMALIZATION-001": ("D-NORMALIZATION-ANTHROPIC-001", "D-NORMALIZATION-OPENAI-001"),
    "P-QUALITY-001": ("D-QUALITY-001",),
    "P-RELEASE-001": ("D-RELEASE-MATRIX-001",),
    "P-ROUTING-001": tuple(sorted(ROUTING_BOUNDARIES)),
    "P-SAFETY-001": tuple(sorted(SAFETY_BOUNDARIES)),
    "P-SCHEMA-001": (
        "D-SCHEMA-BENCHMARK-001", "D-SCHEMA-REQUEST-001",
        "D-SCHEMA-RESULT-001", "D-SCHEMA-VOCABULARY-001",
    ),
}
LIVE_CLAIMS = {
    "appleInvocation": "not_applicable",
    "codexHook": "not_applicable",
    "claudeHook": "not_applicable",
    "parentTokenReduction": "blocked/provider_usage_not_executed",
}
EVIDENCE_KEYS = {
    "schemaVersion", "issue", "status", "policyVersion", "action", "schemaCount",
    "eligibleCaseCount", "requiredArmCount", "requiredPairCount", "corpusSha256", "checks", "liveClaims",
}
FORBIDDEN_METADATA_KEYS = {
    "api_key", "access_token", "password", "secret", "credential", "authorization",
    "private_key", "private_path", "raw_prompt", "raw_result", "raw_response",
    "raw_reasoning", "hidden_reasoning", "chain_of_thought", "trace", "raw_trace",
    "xcresult", "model_correctness", "self_attested", "self_attestation",
}
FORBIDDEN_METADATA_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----", re.IGNORECASE),
    re.compile(r"/(?:Users|home|private)/[^\s]+", re.IGNORECASE),
    re.compile(r"\b[A-Za-z]:[\\/](?:Users|home|private)[\\/]", re.IGNORECASE),
    re.compile(r"(?:\\\\|//)[A-Za-z0-9_.-]+[\\/][^\s]+"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/-]{8,}", re.IGNORECASE),
    re.compile(r"\b(?:api[_ -]?key|access[_ -]?token|password|secret|credential)\b\s*[:=]\s*[^\s,}]+", re.IGNORECASE),
    re.compile(r"\bself[-_ ](?:attested|attestation)\b", re.IGNORECASE),
    re.compile(r"\.(?:trace|xcresult)(?:\b|$)", re.IGNORECASE),
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
        for diagnostic_id in (
            expected["requiredDiagnosticIDs"] + expected["warningRepresentativeIDs"]
        )
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
            "commandOutcome": expected["commandOutcome"],
            "summary": expected["summary"],
            "summaryFacts": list(expected["summaryFacts"]),
            "diagnostics": diagnostics,
            "warningCount": expected["warningCount"],
            "omittedWarningCount": expected["warningCount"] - len(expected["warningRepresentativeIDs"]),
            "nextAction": expected["nextAction"],
            "completionFacts": list(expected["completionFacts"]),
        },
    }


def _canonical_request(contract, command_class="test"):
    request = {
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
            "value": "x",
            "origin": "trustedLocal",
            "classification": "C1",
            "purpose": "diagnostic_condensation",
            "destination": "apple_on_device",
            "retention": "ephemeral",
            "redacted": False,
        }],
    }
    base = len(contract.canonical_field_bytes(request["fields"]))
    request["fields"][0]["value"] = "x" * (contract.Policy.MINIMUM_INPUT_BYTES - base + 1)
    if len(contract.canonical_field_bytes(request["fields"])) != contract.Policy.MINIMUM_INPUT_BYTES:
        raise ValueError("unstable canonical request bytes")
    return request


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
            "commandOutcome": "failure",
            "summary": "synthetic route proof",
            "summaryFacts": ["error-count=0"],
            "diagnostics": [],
            "warningCount": 0,
            "omittedWarningCount": 0,
            "nextAction": "inspect the synthetic route proof",
            "completionFacts": ["command-finished=true", "task-complete=false"],
        },
    }


def _schema_accepts(contract, schema, value):
    def equal(left, right):
        if type(left) is not type(right):
            return False
        if type(left) is dict:
            return set(left) == set(right) and all(equal(left[key], right[key]) for key in left)
        if type(left) is list:
            return len(left) == len(right) and all(equal(a, b) for a, b in zip(left, right))
        return left == right

    def resolve(node):
        if "$ref" not in node:
            return node
        target = schema
        for part in node["$ref"].removeprefix("#/").split("/"):
            target = target[part]
        return target

    def type_matches(candidate, expected):
        return {
            "null": candidate is None,
            "object": type(candidate) is dict,
            "array": type(candidate) is list,
            "string": type(candidate) is str,
            "boolean": type(candidate) is bool,
            "integer": type(candidate) is int,
            "number": type(candidate) in (int, float) and not isinstance(candidate, bool) and math.isfinite(candidate),
        }[expected]

    def pointer(candidate, path):
        current = candidate
        for part in path.removeprefix("/").split("/"):
            if type(current) is not dict or part not in current:
                return None
            current = current[part]
        return current

    def vocabulary_matches(vocabulary, candidate):
        for rule in vocabulary.get("uniqueBy", []):
            values = pointer(candidate, rule["array"])
            if values is None:
                continue
            identities = set()
            if type(values) is not list:
                return False
            for item in values:
                if type(item) is not dict or any(key not in item for key in rule["keys"]):
                    return False
                identity = tuple(json.dumps(item[key], sort_keys=True, separators=(",", ":")) for key in rule["keys"])
                if identity in identities:
                    return False
                identities.add(identity)
        for rule in vocabulary.get("repoRelativePath", []):
            values = pointer(candidate, rule["array"])
            if values is None:
                continue
            if type(values) is not list:
                return False
            for item in values:
                if type(item) is not dict:
                    return False
                if all(equal(item.get(key), expected) for key, expected in rule["when"].items()):
                    path = item.get(rule["field"])
                    if path is None and rule.get("nullable"):
                        continue
                    if type(path) is not str or not path or path.startswith("/") or "\x00" in path:
                        return False
                    if any(part in ("", ".", "..") for part in path.split("/")):
                        return False
        for rule in vocabulary.get("derivedInteger", []):
            source, target = pointer(candidate, rule["source"]), pointer(candidate, rule["target"])
            if source is not None and target is not None and (
                type(source) is not int or type(target) is not int or target != source - rule["subtract"]
            ):
                return False
        for rule in vocabulary.get("lessThanOrEqual", []):
            left, right = pointer(candidate, rule["left"]), pointer(candidate, rule["right"])
            if left is not None and right is not None and (
                type(left) is not int or type(right) is not int or left > right
            ):
                return False
        for rule in vocabulary.get("canonicalUtf8Bytes", []):
            fields, declared = pointer(candidate, rule["array"]), pointer(candidate, rule["target"])
            if fields is not None and declared is not None:
                try:
                    actual = len(contract.canonical_field_bytes(fields))
                except contract.ContractError:
                    return False
                if type(declared) is not int or declared != actual:
                    return False
        if vocabulary.get("benchmarkCostModel") is True and type(candidate) is dict and candidate.get("kind") in ("corpus", "evidence"):
            try:
                contract.validate_benchmark(candidate)
            except contract.ContractError:
                return False
        return True

    def matches(node, candidate):
        node = resolve(node)
        if "oneOf" in node and sum(matches(branch, candidate) for branch in node["oneOf"]) != 1:
            return False
        if "allOf" in node and not all(matches(branch, candidate) for branch in node["allOf"]):
            return False
        if "if" in node and matches(node["if"], candidate) and "then" in node and not matches(node["then"], candidate):
            return False
        if "const" in node and not equal(candidate, node["const"]):
            return False
        if "enum" in node and not any(equal(candidate, item) for item in node["enum"]):
            return False
        expected = node.get("type")
        if expected is not None:
            expected = expected if type(expected) is list else [expected]
            if not any(type_matches(candidate, item) for item in expected):
                return False
        if type(candidate) is dict:
            if any(key not in candidate for key in node.get("required", [])):
                return False
            properties = node.get("properties", {})
            if node.get("additionalProperties") is False and any(key not in properties for key in candidate):
                return False
            if any(key in candidate and not matches(child, candidate[key]) for key, child in properties.items()):
                return False
        if type(candidate) is list:
            if len(candidate) < node.get("minItems", 0) or len(candidate) > node.get("maxItems", len(candidate)):
                return False
            if not all(matches(node.get("items", {}), item) for item in candidate):
                return False
            if node.get("uniqueItems") and any(equal(left, right) for index, left in enumerate(candidate) for right in candidate[index + 1:]):
                return False
        if type(candidate) is str:
            if len(candidate) < node.get("minLength", 0):
                return False
            if "pattern" in node and re.search(node["pattern"], candidate) is None:
                return False
        if type(candidate) in (int, float) and type(candidate) is not bool:
            if "minimum" in node and candidate < node["minimum"]:
                return False
            if "maximum" in node and candidate > node["maximum"]:
                return False
        return vocabulary_matches(node.get("x-dev142-constraints", {}), candidate)

    return matches(schema, value)


def _verify_schemas(contract, corpus):
    if len(SCHEMA_PATHS) != 3:
        raise ValueError("unexpected schema count")
    schemas = {path.name: contract.load_closed_json(path) for path in SCHEMA_PATHS}
    for name, schema in schemas.items():
        if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema" or schema.get("$id") != name:
            raise ValueError("invalid schema identity")
    request = _canonical_request(contract)
    result = _route_result(contract, request)
    benchmark = _serialized_evidence(contract, corpus)
    valid = {
        "dev-142-request.schema.json": request,
        "dev-142-result.schema.json": result,
        "dev-142-benchmark.schema.json": benchmark,
    }
    if any(not _schema_accepts(contract, schemas[name], value) for name, value in valid.items()):
        raise ValueError("valid semantic schema value rejected")
    invalid_request = dict(request, inputBytes=request["inputBytes"] + 1, estimatedSavingsBytes=request["estimatedSavingsBytes"] + 1)
    invalid_result = json.loads(json.dumps(result))
    invalid_result["condensation"]["omittedWarningCount"] = (
        invalid_result["condensation"]["warningCount"] + 1
    )
    invalid_benchmark = json.loads(json.dumps(benchmark))
    invalid_benchmark["pairs"][0]["reductionPPM"] += 1
    invalid = {
        "dev-142-request.schema.json": invalid_request,
        "dev-142-result.schema.json": invalid_result,
        "dev-142-benchmark.schema.json": invalid_benchmark,
    }
    if any(_schema_accepts(contract, schemas[name], value) for name, value in invalid.items()):
        raise ValueError("invalid semantic schema value accepted")
    expected_vocabularies = {
        "dev-142-request.schema.json": {"uniqueBy", "repoRelativePath", "derivedInteger", "canonicalUtf8Bytes"},
        "dev-142-result.schema.json": {"uniqueBy", "repoRelativePath", "lessThanOrEqual"},
        "dev-142-benchmark.schema.json": {"uniqueBy", "benchmarkCostModel"},
    }
    if any(set(schemas[name].get("x-dev142-constraints", {})) != expected for name, expected in expected_vocabularies.items()):
        raise ValueError("invalid closed schema vocabulary")
    return (
        "D-SCHEMA-BENCHMARK-001", "D-SCHEMA-REQUEST-001",
        "D-SCHEMA-RESULT-001", "D-SCHEMA-VOCABULARY-001",
    )


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
    interrupted = rows.get("interrupted-command")
    if interrupted is None or interrupted["exitStatus"] is not None or interrupted["interrupted"] is not True:
        raise ValueError("interruption boundary failed")
    return ("D-INPUT-001", "D-INTERRUPTION-001", "D-OCCUPANCY-001")


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


def _resize_request(contract, request, size):
    field = request["fields"][0]
    current = len(contract.canonical_field_bytes(request["fields"]))
    field["value"] += "x" * (size - current)
    if size < current:
        field["value"] = field["value"][: size - current]
    request["inputBytes"] = len(contract.canonical_field_bytes(request["fields"]))
    request["estimatedSavingsBytes"] = request["inputBytes"] - contract.Policy.MAXIMUM_CONDENSED_BYTES


def _set_file_field(contract, request, value):
    message = request["fields"][0]
    file_field = dict(message, name="file", value=value)
    request["fields"] = [message, file_field]
    content = [
        {"name": field["name"], "value": field["value"]}
        for field in sorted(request["fields"], key=lambda field: ("severity", "code", "message", "file", "line", "column").index(field["name"]))
    ]
    request["inputBytes"] = len(json.dumps(content, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    request["estimatedSavingsBytes"] = request["inputBytes"] - contract.Policy.MAXIMUM_CONDENSED_BYTES


def _verify_routing(contract):
    with tempfile.TemporaryDirectory() as directory:
        observed = set()
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
            observed.add(boundary_id)
        if contract.parse_command('python3 -m pytest -k "one and (two)"', root).command_class != "test":
            raise ValueError("failed R-QUOTED-PYTEST-001")
        observed.add("R-QUOTED-PYTEST-001")
        for command in (
            "swift format lint --strict --recursive Sources",
            "python3 -m mypy --no-incremental --strict Sources",
            "python3 -m ruff check --output-format concise --no-fix Sources",
        ):
            try:
                contract.parse_command(command, root)
            except contract.RouteDeclined:
                continue
            raise ValueError("failed R-FLAG-ORDER-001")
        observed.add("R-FLAG-ORDER-001")

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
                "sourceFacts": _route_result(contract, request)["condensation"],
                "bridge": bridge,
            }
            context_change(context)
            if boundary_id in ("R-REALIZED-4095", "R-REALIZED-4096"):
                output_bytes = 4097 if boundary_id.endswith("4095") else 4096
                context["sourceFacts"] = _route_result_with_size(
                    contract, request, output_bytes
                )["condensation"]
            result = contract.route(request, context)
            if result != expected(request) or len(calls) != expected_calls:
                raise ValueError(f"failed {boundary_id}")
            observed.add(boundary_id)

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
            ("R-INPUT-8191", lambda request: _resize_request(contract, request, 8191), no_context_change, fallback("declined", "input_below_minimum")),
            ("R-INPUT-65537", lambda request: _resize_request(contract, request, 65537), no_context_change, fallback("declined", "input_above_maximum")),
            ("R-ESTIMATED-4095", lambda request: request.update(estimatedSavingsBytes=4095), no_context_change, fallback("declined", "contract_invariant_failed")),
            ("R-CANONICAL-BYTES-001", lambda request: request.update(inputBytes=8193, estimatedSavingsBytes=4097), no_context_change, fallback("declined", "contract_invariant_failed")),
            ("R-SECRET-001", lambda request: request["fields"][0].update(value="Bearer synthetic-private-token-12345678" + "x" * 8192), no_context_change, fallback("declined", "data_policy_denied")),
            ("R-OCCUPANCY-75-FAIL", no_request_change, lambda context: context.update(occupiedTokens=6145), fallback("declined", "context_budget_exceeded")),
            ("R-CLASS-C2", lambda request: request["fields"][0].update(classification="C2"), no_context_change, fallback("declined", "data_policy_denied")),
            ("R-CLASS-C3", lambda request: request["fields"][0].update(classification="C3"), no_context_change, fallback("declined", "data_policy_denied")),
            ("R-CLASS-UNKNOWN", lambda request: request["fields"][0].update(classification="C9"), no_context_change, fallback("declined", "data_policy_denied")),
            ("R-CLASS-UNCLASSIFIED", lambda request: request["fields"][0].pop("classification"), no_context_change, fallback("declined", "data_policy_denied")),
            ("R-PROVENANCE-MIXED", lambda request: request["fields"][0].update(origin="remote"), no_context_change, fallback("declined", "data_policy_denied")),
            ("R-FILE-INVALID", lambda request: _set_file_field(contract, request, "Sources\\App.swift"), no_context_change, fallback("declined", "data_policy_denied")),
            ("R-FILE-MISSING", lambda request: _set_file_field(contract, request, "Missing.swift"), no_context_change, fallback("declined", "data_policy_denied")),
            ("R-FILE-NONCONTAINED", lambda request: _set_file_field(contract, request, "../outside.swift"), no_context_change, fallback("declined", "data_policy_denied")),
            ("R-APPLE-UNAVAILABLE", no_request_change, lambda context: context.update(appleAvailable=False), fallback("declined", "apple_unavailable")),
            ("R-LOCALE-UNSUPPORTED", no_request_change, lambda context: context.update(localeSupported=False), fallback("declined", "locale_unsupported")),
        )
        for boundary_id, request_change, context_change, expected in preflight_rows:
            route_case(boundary_id, request_change, context_change, applied, expected, 0)

        postflight_rows = (
            ("R-INPUT-8192", lambda request: _resize_request(contract, request, 8192), no_context_change, applied, applied),
            ("R-INPUT-65536", lambda request: _resize_request(contract, request, 65536), no_context_change, applied, applied),
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

        request = _canonical_request(contract)
        original = json.loads(json.dumps(request))

        def mutating_bridge(candidate):
            candidate["callID"] = "invented"
            response = _route_result(contract, candidate)
            return response

        isolated = contract.route(request, {
            "eventName": contract.Policy.EVENT_NAME, "command": "swift test",
            "repoRoot": root, "appleAvailable": True, "localeSupported": True,
            "occupiedTokens": 6144, "contextSize": 8192,
            "sourceFacts": _route_result(contract, request)["condensation"],
            "bridge": mutating_bridge,
        })
        if isolated != fallback("fail", "invalid_response")(request) or request != original:
            raise ValueError("failed R-ISOLATED-REQUEST-001")
        observed.add("R-ISOLATED-REQUEST-001")

        for boundary_id, response_change in (
            ("R-RESPONSE-BINDINGS-001", lambda response: response.update(callID="invented")),
            ("R-RESPONSE-SEMANTICS-001", lambda response: response["condensation"].update(summary="invented")),
        ):
            response = _route_result(contract, request)
            response_change(response)
            result = contract.route(request, {
                "eventName": contract.Policy.EVENT_NAME, "command": "swift test",
                "repoRoot": root, "appleAvailable": True, "localeSupported": True,
                "occupiedTokens": 6144, "contextSize": 8192,
                "sourceFacts": _route_result(contract, request)["condensation"],
                "bridge": lambda _request, response=response: response,
            })
            if result != fallback("fail", "invalid_response")(request):
                raise ValueError(f"failed {boundary_id}")
            observed.add(boundary_id)

        original_lstat = contract._lstat
        root_calls = 0

        def disappearing_root(path):
            nonlocal root_calls
            if Path(path).resolve(strict=False) == root.resolve():
                root_calls += 1
                if root_calls > 1:
                    raise FileNotFoundError("synthetic disappearance")
            return original_lstat(path)

        contract._lstat = disappearing_root
        try:
            result = contract.route(request, {
                "eventName": contract.Policy.EVENT_NAME, "command": "swift test",
                "repoRoot": root, "appleAvailable": True, "localeSupported": True,
                "occupiedTokens": 6144, "contextSize": 8192,
                "sourceFacts": _route_result(contract, request)["condensation"],
                "bridge": lambda value: _route_result(contract, value),
            })
        finally:
            contract._lstat = original_lstat
        if result.get("preserveOriginal") is not True or result.get("outcome") not in ("declined", "fail"):
            raise ValueError("failed R-PATH-RECHECK-001")
        observed.add("R-PATH-RECHECK-001")
    if observed != set(ROUTING_BOUNDARIES):
        raise ValueError("incomplete routing proof")
    return tuple(sorted(observed))


def _arm(contract, host, case, arm, input_tokens, output_tokens, quality):
    usage = contract.normalize_usage("openai-responses-usage-v1", {
        "input_tokens": input_tokens,
        "cached_tokens": 0,
        "output_tokens": output_tokens,
        "reasoning_tokens": 0,
    })
    return {
        "host": host,
        "caseID": case["id"],
        "workflow": "diagnostic-condensation",
        "parentModel": "proof-parent-model-v1",
        "provider": usage.provider,
        "normalizationVersion": usage.provider,
        "toolchain": "offline-contract-v1",
        "policyVersion": contract.Policy.POLICY_VERSION,
        "commandClass": case["commandClass"],
        "arm": arm,
        "usage": usage,
        "parentTurns": 1,
        "appleAttempts": 0 if arm == "pluginOff" else 1,
        "replacements": 0 if arm == "pluginOff" else 1,
        "quality": quality,
    }


def _serialized_evidence(contract, corpus):
    cases = {case["id"]: case for case in corpus["cases"]}
    arms = []
    for host, case_id in contract.REQUIRED_PAIR_IDENTITIES:
        case = cases[case_id]
        quality = contract.score_condensation(case, _canonical_result(contract, case))
        if not quality.passed:
            raise ValueError("non-oracle proof quality")
        pair_id = f"{host}:{case_id}"
        for role, input_tokens, output_tokens, attempts, replacements in (
            ("pluginOff", 900, 100, 0, 0),
            ("pluginOn", 810, 90, 1, 1),
        ):
            arms.append({
                "id": f"{pair_id}:{role}", "pairID": pair_id, "arm": role,
                "host": host, "caseID": case_id,
                "caseRenderedSha256": case["renderedSha256"],
                "commandClass": case["commandClass"],
                "workflow": "diagnostic-condensation",
                "parentModel": "proof-parent-model-v1",
                "provider": "openai-responses-usage-v1",
                "normalizationVersion": "openai-responses-usage-v1",
                "toolchain": "offline-contract-v1",
                "policyVersion": contract.Policy.POLICY_VERSION,
                "providerUsage": {
                    "input_tokens": input_tokens, "cached_tokens": 0,
                    "output_tokens": output_tokens, "reasoning_tokens": 0,
                },
                "parentTurns": 1, "appleAttempts": attempts,
                "replacements": replacements, "declines": 0, "fallbacks": 0,
                "latencyMilliseconds": 1, "qualityPassed": quality.passed,
                "qualityReasonCodes": list(quality.reason_codes),
            })
    seed = {
        "schemaVersion": contract.Policy.SCHEMA_VERSION,
        "policyVersion": contract.Policy.POLICY_VERSION,
        "kind": "evidence", "corpusSha256": corpus["corpusSha256"],
        "arms": arms, "pairs": [], "release": {},
    }
    derived = contract.derive_benchmark(seed)
    contract.validate_benchmark(derived)
    return derived


def _verify_normalization(contract):
    openai = contract.normalize_usage("openai-responses-usage-v1", {
        "input_tokens": 900, "cached_tokens": 200, "output_tokens": 100, "reasoning_tokens": 50,
    })
    anthropic = contract.normalize_usage("anthropic-messages-usage-v1", {
        "input_tokens": 700, "cache_read_input_tokens": 200,
        "cache_creation_input_tokens": 100, "output_tokens": 100,
    })
    if (openai.total_parent_model_tokens, anthropic.total_parent_model_tokens, anthropic.reasoning_tokens) != (1000, 1100, None):
        raise ValueError("provider normalization failed")
    return ("D-NORMALIZATION-ANTHROPIC-001", "D-NORMALIZATION-OPENAI-001")


def _verify_release(contract, corpus):
    cases = {case["id"]: case for case in corpus["cases"]}
    pairs = []
    for host, case_id in contract.REQUIRED_PAIR_IDENTITIES:
        case = cases[case_id]
        quality = contract.score_condensation(case, _canonical_result(contract, case))
        off = _arm(contract, host, case, "pluginOff", 900, 100, quality)
        on = _arm(contract, host, case, "pluginOn", 810, 90, quality)
        pairs.append(contract.score_pair(off, on))
    release = contract.release_gate(pairs)
    if (release.status, release.valid_required_pairs, release.blocked_required_pairs,
            release.median_reduction_ppm, release.correctness_regressions,
            release.additional_parent_model_turns) != ("pass", 48, 0, 100000, 0, 0):
        raise ValueError("release gate failed")
    serialized = _serialized_evidence(contract, corpus)
    if len(serialized["arms"]) != 96 or len(serialized["pairs"]) != 48 or serialized["release"]["status"] != "pass":
        raise ValueError("serialized release matrix failed")
    return ("D-RELEASE-MATRIX-001",)


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
        ("S-PRIVATE-POSIX-001", lambda value: value.update(issue="/private/synthetic/path")),
        ("S-WINDOWS-PATH-001", lambda value: value.update(issue=r"C:\Users\synthetic\path")),
        ("S-UNC-PATH-001", lambda value: value.update(issue=r"\\synthetic-server\private-share")),
        ("S-CREDENTIAL-VALUE-001", lambda value: value.update(issue="Bearer synthetic-private-token-12345678")),
        ("S-NESTED-KEY-001", lambda value: value["liveClaims"].update(rawPrompt="nested")),
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
        _check("P-SCHEMA-001", lambda: _verify_schemas(contract, corpus)),
        _check("P-CORPUS-001", lambda: _verify_corpus(contract, corpus)),
        _check("P-QUALITY-001", lambda: _verify_quality(contract, corpus)),
        _check("P-BOUNDARY-001", lambda: _verify_boundaries(contract)),
        _check("P-ROUTING-001", lambda: _verify_routing(contract)),
        _check("P-NORMALIZATION-001", lambda: _verify_normalization(contract)),
        _check("P-RELEASE-001", lambda: _verify_release(contract, corpus)),
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
        "requiredArmCount": len(contract.REQUIRED_PAIR_IDENTITIES) * 2,
        "requiredPairCount": len(contract.REQUIRED_PAIR_IDENTITIES),
        "corpusSha256": contract.corpus_digest(corpus),
        "checks": sorted(checks, key=lambda row: row["id"]),
        "liveClaims": dict(LIVE_CLAIMS),
    }
    _verify_safety(evidence)
    validate_evidence(evidence)
    return evidence


def _normalized_key(key):
    camel_split = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", key)
    return re.sub(r"[^a-z0-9]+", "_", camel_split.lower()).strip("_")


def _safe_metadata(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if _normalized_key(str(key)) in FORBIDDEN_METADATA_KEYS:
                return False
            if not _safe_metadata(item):
                return False
    elif isinstance(value, list):
        return all(_safe_metadata(item) for item in value)
    elif isinstance(value, str):
        return all(pattern.search(value) is None for pattern in FORBIDDEN_METADATA_PATTERNS)
    elif value is None or type(value) in (bool, int):
        return True
    else:
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
        "requiredArmCount": 96,
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
    for check_id, boundaries in EXPECTED_BOUNDARIES.items():
        if tuple(rows[check_id]["boundaries"]) != tuple(sorted(boundaries)):
            raise ValueError("incomplete proof boundary")
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
