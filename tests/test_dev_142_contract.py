import importlib.util
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from dataclasses import replace
from copy import deepcopy


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "fixtures" / "dev-142" / "runtime_contract.py"
CORPUS = ROOT / "fixtures" / "dev-142" / "benchmark-corpus.json"
PROOF_RUNNER = ROOT / "fixtures" / "dev-142" / "proof_runner.py"
PROOF_EVIDENCE = ROOT / "docs" / "research" / "evidence" / "dev-142-contract-verification.json"
SCHEMAS = ROOT / "schemas"
SPEC = importlib.util.spec_from_file_location("dev142_runtime_contract", CONTRACT_PATH)
contract = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(contract)


FIELD_ORDER = ("severity", "code", "message", "file", "line", "column")


def canonical_field_bytes(fields):
    content = [
        {"name": field["name"], "value": field["value"]}
        for field in sorted(fields, key=lambda field: FIELD_ORDER.index(field["name"]))
    ]
    return json.dumps(
        content, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def bind_request_fields(request, fields, *, target_bytes=None):
    request = deepcopy(request)
    request["fields"] = deepcopy(fields)
    if target_bytes is not None:
        messages = [field for field in request["fields"] if field["name"] == "message"]
        if len(messages) != 1 or type(messages[0]["value"]) is not str:
            raise AssertionError("one string message field is required for padding")
        messages[0]["value"] = ""
        padding = target_bytes - len(canonical_field_bytes(request["fields"]))
        if padding < 1:
            raise AssertionError("target cannot hold canonical fields")
        messages[0]["value"] = "x" * padding
    request["inputBytes"] = len(canonical_field_bytes(request["fields"]))
    request["estimatedSavingsBytes"] = request["inputBytes"] - 4096
    return request


def canonical_request(input_bytes=8192):
    request = {
        "schemaVersion": 1,
        "policyVersion": "diagnostic-condensation-v1",
        "callID": "call-0001",
        "toolName": "Bash",
        "toolVersion": "0.144.5",
        "stateVersion": "state-v1",
        "action": "condense_diagnostic_output",
        "commandClass": "test",
        "originalResultType": "text",
        "originalResultDigest": "a" * 64,
        "exitStatus": 1,
        "interrupted": False,
        "inputBytes": input_bytes,
        "estimatedSavingsBytes": input_bytes - 4096,
        "fields": [
            {
                "name": "message",
                "value": "x",
                "origin": "trustedLocal",
                "classification": "C1",
                "purpose": "diagnostic_condensation",
                "destination": "apple_on_device",
                "retention": "ephemeral",
                "redacted": False,
            }
        ],
    }
    return bind_request_fields(request, request["fields"], target_bytes=input_bytes)


def canonical_result(outcome="applied"):
    result = {
        "schemaVersion": 1,
        "policyVersion": "diagnostic-condensation-v1",
        "callID": "call-0001",
        "toolName": "Bash",
        "toolVersion": "0.144.5",
        "stateVersion": "state-v1",
        "action": "condense_diagnostic_output",
        "commandClass": "test",
        "originalResultType": "text",
        "originalResultDigest": "a" * 64,
        "outcome": outcome,
        "exitStatus": 1,
        "interrupted": False,
    }
    if outcome == "applied":
        result["resultType"] = "diagnostic_condensation"
        result["condensation"] = {
            "commandOutcome": "failure",
            "summary": "1 test failed",
            "summaryFacts": ["failed-test-count=1"],
            "diagnostics": [],
            "warningCount": 0,
            "omittedWarningCount": 0,
            "nextAction": "inspect the synthetic failure",
            "completionFacts": ["command-finished=true", "task-complete=false"],
        }
    else:
        result["reasonCode"] = "generation_declined"
    return result


def canonical_source_facts(result=None):
    result = canonical_result() if result is None else result
    return deepcopy(result["condensation"])


def canonical_benchmark():
    return contract.load_closed_json(CORPUS)


def canonical_serialized_cost_evidence():
    corpus = canonical_benchmark()
    cases = {case["id"]: case for case in corpus["cases"]}
    arms = []
    pairs = []
    for host, case_id in contract.REQUIRED_PAIR_IDENTITIES:
        case = cases[case_id]
        pair_id = f"{host}:{case_id}"
        for role, input_tokens, output_tokens, attempts, replacements in (
            ("pluginOff", 900, 100, 0, 0),
            ("pluginOn", 810, 90, 1, 1),
        ):
            arms.append({
                "id": f"{pair_id}:{role}",
                "pairID": pair_id,
                "arm": role,
                "host": host,
                "caseID": case_id,
                "caseRenderedSha256": case["renderedSha256"],
                "commandClass": case["commandClass"],
                "workflow": "diagnostic-condensation",
                "parentModel": "synthetic-parent-v1",
                "provider": "openai-responses-usage-v1",
                "normalizationVersion": "openai-responses-usage-v1",
                "toolchain": "synthetic-toolchain-v1",
                "policyVersion": contract.Policy.POLICY_VERSION,
                "providerUsage": {
                    "input_tokens": input_tokens,
                    "cached_tokens": 0,
                    "output_tokens": output_tokens,
                    "reasoning_tokens": 0,
                },
                "parentTurns": 1,
                "appleAttempts": attempts,
                "replacements": replacements,
                "declines": 0,
                "fallbacks": 0,
                "latencyMilliseconds": 1,
                "qualityPassed": True,
                "qualityReasonCodes": [],
            })
        pairs.append({
            "id": pair_id,
            "host": host,
            "caseID": case_id,
            "status": "pass",
            "reductionPPM": 100000,
            "correctnessRegressions": 0,
            "additionalParentModelTurns": 0,
            "reasonCodes": [],
        })
    return {
        "schemaVersion": 1,
        "policyVersion": contract.Policy.POLICY_VERSION,
        "kind": "evidence",
        "corpusSha256": corpus["corpusSha256"],
        "arms": arms,
        "pairs": pairs,
        "release": {
            "status": "pass",
            "validRequiredPairs": 48,
            "blockedRequiredPairs": 0,
            "medianReductionPPM": 100000,
            "correctnessRegressions": 0,
            "additionalParentModelTurns": 0,
            "exploratoryPairs": 0,
            "reasonCodes": [],
        },
    }


def schema_accepts(schema, value):
    """Evaluate only the repository-local Draft 2020-12 keywords we use."""
    def json_equal(left, right):
        if type(left) is not type(right):
            return False
        if type(left) is dict:
            return set(left) == set(right) and all(json_equal(left[key], right[key]) for key in left)
        if type(left) is list:
            return len(left) == len(right) and all(json_equal(a, b) for a, b in zip(left, right))
        return left == right

    def resolve(node):
        if "$ref" not in node:
            return node
        target = schema
        for part in node["$ref"].removeprefix("#/").split("/"):
            target = target[part]
        return target

    def type_matches(candidate, expected):
        if expected == "null":
            return candidate is None
        if expected == "object":
            return type(candidate) is dict
        if expected == "array":
            return type(candidate) is list
        if expected == "string":
            return type(candidate) is str
        if expected == "boolean":
            return type(candidate) is bool
        if expected == "integer":
            return type(candidate) is int
        if expected == "number":
            return type(candidate) in (int, float) and math.isfinite(candidate)
        raise AssertionError(f"unsupported schema type: {expected}")

    def pointer(candidate, path):
        current = candidate
        for part in path.removeprefix("/").split("/"):
            if type(current) is not dict or part not in current:
                return None
            current = current[part]
        return current

    def closed_vocabulary_matches(vocabulary, candidate):
        for rule in vocabulary.get("uniqueBy", []):
            values = pointer(candidate, rule["array"])
            if values is None:
                continue
            if type(values) is not list:
                return False
            identities = set()
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
                if all(json_equal(item.get(key), expected) for key, expected in rule["when"].items()):
                    path = item.get(rule["field"])
                    if path is None and rule.get("nullable"):
                        continue
                    if type(path) is not str or not path or path.startswith("/") or "\\" in path or "\x00" in path:
                        return False
                    if any(part in ("", ".", "..") for part in path.split("/")):
                        return False
        for rule in vocabulary.get("derivedInteger", []):
            source = pointer(candidate, rule["source"])
            target = pointer(candidate, rule["target"])
            if source is None or target is None:
                continue
            if type(source) is not int or type(target) is not int or target != source - rule["subtract"]:
                return False
        for rule in vocabulary.get("lessThanOrEqual", []):
            left = pointer(candidate, rule["left"])
            right = pointer(candidate, rule["right"])
            if left is None or right is None:
                continue
            if type(left) is not int or type(right) is not int or left > right:
                return False
        for rule in vocabulary.get("warningAccounting", []):
            diagnostics = pointer(candidate, rule["array"])
            omitted = pointer(candidate, rule["omitted"])
            total = pointer(candidate, rule["total"])
            if diagnostics is None and omitted is None and total is None:
                continue
            if (
                type(diagnostics) is not list
                or type(omitted) is not int
                or type(total) is not int
                or any(type(item) is not dict for item in diagnostics)
            ):
                return False
            warning_count = sum(
                item.get(rule["severityField"]) == rule["warningValue"]
                for item in diagnostics
            )
            if warning_count + omitted != total:
                return False
        for rule in vocabulary.get("canonicalUtf8Bytes", []):
            fields = pointer(candidate, rule["array"])
            declared = pointer(candidate, rule["target"])
            if fields is None or declared is None:
                continue
            try:
                actual = canonical_field_bytes(fields)
            except (KeyError, TypeError, ValueError, UnicodeError):
                return False
            if type(declared) is not int or declared != len(actual):
                return False
        if vocabulary.get("benchmarkCostModel") is True and type(candidate) is dict and candidate.get("kind") == "evidence":
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
        if "const" in node and not json_equal(candidate, node["const"]):
            return False
        if "enum" in node and not any(json_equal(candidate, item) for item in node["enum"]):
            return False
        expected = node.get("type")
        if expected is not None:
            expected = expected if type(expected) is list else [expected]
            if not any(type_matches(candidate, item) for item in expected):
                return False
        if type(candidate) is dict:
            required = node.get("required", [])
            if any(key not in candidate for key in required):
                return False
            properties = node.get("properties", {})
            if node.get("additionalProperties") is False and any(key not in properties for key in candidate):
                return False
            if any(key in candidate and not matches(child, candidate[key]) for key, child in properties.items()):
                return False
        if type(candidate) is list:
            if len(candidate) < node.get("minItems", 0):
                return False
            if "maxItems" in node and len(candidate) > node["maxItems"]:
                return False
            if not all(matches(node.get("items", {}), item) for item in candidate):
                return False
            if node.get("uniqueItems") and any(json_equal(left, right) for index, left in enumerate(candidate) for right in candidate[index + 1:]):
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
        return closed_vocabulary_matches(node.get("x-dev142-constraints", {}), candidate)

    return matches(schema, value)


class Dev142PolicySchemaTests(unittest.TestCase):
    def test_policy_identity_and_closed_request_are_exact(self):
        self.assertEqual(contract.Policy.SCHEMA_VERSION, 1)
        self.assertEqual(contract.Policy.POLICY_VERSION, "diagnostic-condensation-v1")
        self.assertEqual(contract.Policy.ACTION, "condense_diagnostic_output")
        self.assertEqual(contract.Policy.RESULT_TYPE, "diagnostic_condensation")
        request = canonical_request()
        self.assertEqual(contract.validate_request(request), request)
        for key in tuple(request):
            mutated = dict(request)
            mutated.pop(key)
            with self.subTest(key=key), self.assertRaises(contract.ContractError):
                contract.validate_request(mutated)
        with self.assertRaises(contract.ContractError):
            contract.validate_request({**request, "unexpected": True})

    def test_policy_constants_are_frozen(self):
        with self.assertRaises((AttributeError, TypeError)):
            contract.Policy.ACTION = "other"

    def test_request_rejects_one_independent_mutation_per_required_field(self):
        mutations = {
            "schemaVersion": 2,
            "policyVersion": "diagnostic-condensation-v2",
            "callID": "",
            "toolName": "bash",
            "toolVersion": "",
            "stateVersion": "",
            "action": "other",
            "commandClass": "shell",
            "originalResultType": "",
            "originalResultDigest": "not-a-digest",
            "exitStatus": True,
            "interrupted": 0,
            "inputBytes": True,
            "estimatedSavingsBytes": 4095,
            "fields": [],
        }
        for key, value in mutations.items():
            mutated = canonical_request()
            mutated[key] = value
            with self.subTest(key=key), self.assertRaises(contract.ContractError):
                contract.validate_request(mutated)

    def test_request_rejects_invalid_field_grants_and_status_inconsistency(self):
        request = canonical_request()
        invalid_field = dict(request["fields"][0], origin="remote")
        with self.assertRaises(contract.ContractError):
            contract.validate_request({**request, "fields": [invalid_field]})
        with self.assertRaises(contract.ContractError):
            contract.validate_request({**request, "exitStatus": None, "interrupted": False})
        self.assertEqual(
            contract.validate_request({**request, "exitStatus": None, "interrupted": True}),
            {**request, "exitStatus": None, "interrupted": True},
        )

    def test_closed_json_rejects_duplicate_keys_and_non_finite_numbers(self):
        with tempfile.TemporaryDirectory() as directory:
            duplicate_path = Path(directory) / "duplicate.json"
            duplicate_path.write_text('{"schemaVersion": 1, "schemaVersion": 1}')
            with self.assertRaises(contract.ContractError):
                contract.load_closed_json(duplicate_path)
            non_finite_path = Path(directory) / "non-finite.json"
            non_finite_path.write_text('{"value": NaN}')
            with self.assertRaises(contract.ContractError):
                contract.load_closed_json(non_finite_path)

    def test_result_is_a_closed_tagged_union(self):
        for outcome in ("applied", "declined", "fail"):
            result = canonical_result(outcome)
            self.assertEqual(contract.validate_result(result), result)
            for key in tuple(result):
                mutated = dict(result)
                mutated.pop(key)
                with self.subTest(outcome=outcome, key=key), self.assertRaises(contract.ContractError):
                    contract.validate_result(mutated)
        declined = canonical_result("declined")
        with self.assertRaises(contract.ContractError):
            contract.validate_result({**declined, "condensation": {}})
        with self.assertRaises(contract.ContractError):
            contract.validate_result({**canonical_result(), "reasonCode": "generation_declined"})
        with self.assertRaises(contract.ContractError):
            contract.validate_result({**declined, "reasonCode": "unknown_reason"})

    def test_benchmark_is_closed_and_rejects_non_finite_values(self):
        benchmark = canonical_benchmark()
        self.assertEqual(contract.validate_benchmark(benchmark), benchmark)
        for key in tuple(benchmark):
            mutated = dict(benchmark)
            mutated.pop(key)
            with self.subTest(key=key), self.assertRaises(contract.ContractError):
                contract.validate_benchmark(mutated)
        with self.assertRaises(contract.ContractError):
            contract.validate_benchmark({**benchmark, "rawResult": "forbidden"})
        evidence = canonical_serialized_cost_evidence()
        self.assertEqual(contract.validate_benchmark(evidence), evidence)
        evidence["pairs"][0]["reductionPPM"] = math.nan
        with self.assertRaises(contract.ContractError):
            contract.validate_benchmark(evidence)

    def test_all_enum_boundaries_reject_unhashable_values_as_contract_errors(self):
        diagnostic = {
            "id": "diagnostic-1", "severity": [], "code": "E1", "message": "failure",
            "file": None, "line": None, "column": None, "failedTestID": None,
        }
        cases = (
            (contract.validate_request, {**canonical_request(), "commandClass": []}),
            (contract.validate_request, {**canonical_request(), "fields": [dict(canonical_request()["fields"][0], classification={})]}),
            (contract.validate_result, {**canonical_result(), "condensation": {**canonical_result()["condensation"], "diagnostics": [diagnostic]}}),
            (contract.validate_result, {**canonical_result("declined"), "reasonCode": {}}),
            (contract.validate_benchmark, {**canonical_benchmark(), "kind": []}),
            (contract.validate_benchmark, {**canonical_benchmark(), "cases": [dict(canonical_benchmark()["cases"][0], commandClass=[])]}),
        )
        for validator, value in cases:
            with self.subTest(validator=validator.__name__, value=value), self.assertRaises(contract.ContractError):
                validator(value)

        evidence = {
            "schemaVersion": 1, "policyVersion": contract.Policy.POLICY_VERSION, "kind": "evidence",
            "arms": [], "pairs": [],
            "release": {"status": {}, "validRequiredPairs": 0, "blockedRequiredPairs": 0, "medianReduction": None, "correctnessRegressions": 0, "additionalParentModelTurns": 0},
        }
        with self.assertRaises(contract.ContractError):
            contract.validate_benchmark(evidence)


class Dev142CorpusTests(unittest.TestCase):
    def _result_for(self, case):
        diagnostics = []
        diagnostic_ids = (
            case["expected"]["requiredDiagnosticIDs"]
            + case["expected"]["warningRepresentativeIDs"]
        )
        for diagnostic_id in diagnostic_ids:
            severity, ordinal = diagnostic_id.split("-", 1)
            index = int(ordinal)
            diagnostics.append({
                "id": diagnostic_id,
                "severity": severity,
                "code": f"{case['commandClass'].upper()}-{index:03d}",
                "message": f"synthetic {case['commandForm']} {severity} diagnostic",
                "file": f"Sources/{case['commandClass'].title()}Case{index}.swift",
                "line": 100 + index,
                "column": 1 + index,
                "failedTestID": case["expected"]["failedTestIDs"][0] if case["expected"]["failedTestIDs"] else None,
            })
        result = canonical_result()
        result["commandClass"] = case["commandClass"]
        result["exitStatus"] = case["expected"]["exitStatus"]
        result["interrupted"] = case["expected"]["interrupted"]
        result["condensation"] = {
            "commandOutcome": case["expected"]["commandOutcome"],
            "summary": case["expected"]["summary"],
            "summaryFacts": list(case["expected"]["summaryFacts"]),
            "diagnostics": diagnostics,
            "warningCount": case["expected"]["warningCount"],
            "omittedWarningCount": (
                case["expected"]["warningCount"]
                - len(case["expected"]["warningRepresentativeIDs"])
            ),
            "nextAction": case["expected"]["nextAction"],
            "completionFacts": list(case["expected"]["completionFacts"]),
        }
        return result

    def test_corpus_is_exact_hash_bound_and_balanced(self):
        self.assertTrue(CORPUS.exists())
        corpus = contract.load_closed_json(CORPUS)
        contract.validate_benchmark(corpus)
        self.assertEqual(len(corpus["cases"]), 24)
        self.assertEqual(Counter(row["commandClass"] for row in corpus["cases"]), {
            "test": 6, "build": 6, "typecheck": 6, "lint": 6,
        })
        self.assertEqual(len({row["id"] for row in corpus["cases"]}), 24)
        self.assertEqual(contract.corpus_digest(corpus), corpus["corpusSha256"])
        for row in corpus["cases"]:
            rendered = contract.render_case(row)
            self.assertEqual(hashlib.sha256(rendered).hexdigest(), row["renderedSha256"])
            self.assertGreaterEqual(len(rendered), 8192)
            self.assertLessEqual(len(rendered), 65536)
            self.assertTrue(rendered.endswith(b"\n"))

    def test_corpus_covers_twelve_forms_success_failure_and_synthetic_unicode(self):
        corpus = contract.load_closed_json(CORPUS)
        grouped = {}
        for row in corpus["cases"]:
            grouped.setdefault(row["commandForm"], []).append(row)
            self.assertIn(row["classification"], ("C0", "C1"))
            self.assertNotIn(b"/Users/", contract.render_case(row))
            self.assertNotIn(b"BEGIN PRIVATE", contract.render_case(row))
        self.assertEqual(len(grouped), 12)
        for command_form, rows in grouped.items():
            with self.subTest(command_form=command_form):
                self.assertEqual(len(rows), 2)
                self.assertEqual({row["expected"]["exitStatus"] == 0 for row in rows}, {False, True})
                failure = next(row for row in rows if row["expected"]["commandOutcome"] == "failure")
                self.assertIs(type(failure["expected"]["exitStatus"]), int)
                self.assertGreater(failure["expected"]["exitStatus"], 0)
                self.assertFalse(failure["expected"]["interrupted"])
        self.assertEqual(
            frozenset(grouped),
            contract.Policy.APPROVED_BENCHMARK_COMMAND_FORMS,
        )
        unicode_case = next(row for row in corpus["cases"] if "unicode" in row["id"])
        rendered = contract.render_case(unicode_case)
        self.assertGreater(len(rendered), len(rendered.decode("utf-8").encode("ascii", "ignore")))
        self.assertNotEqual(len(rendered), len(rendered.decode("utf-8").split()))

    def test_boundary_fixtures_are_outside_the_eligible_corpus(self):
        corpus = contract.load_closed_json(CORPUS)
        boundaries = contract.benchmark_boundaries()
        self.assertEqual({row["id"] for row in boundaries} & {row["id"] for row in corpus["cases"]}, set())
        self.assertEqual(
            {row["inputBytes"] for row in boundaries},
            {8191, 8192, 65536, 65537},
        )
        self.assertEqual(
            {row["outputBytes"] for row in boundaries}, {4096, 4097}
        )
        self.assertTrue(
            {4095, 4096}.issubset(
                {row["realizedSavingsBytes"] for row in boundaries}
            )
        )
        for row in boundaries:
            with self.subTest(row=row["id"]):
                self.assertEqual(
                    row["realizedSavingsBytes"],
                    row["inputBytes"] - row["outputBytes"],
                )
        self.assertTrue(any(row["occupiedTokens"] == 6144 and row["contextSize"] == 8192 for row in boundaries))
        self.assertTrue(any(row["occupiedTokens"] == 6145 and row["contextSize"] == 8192 for row in boundaries))
        interrupted = next(row for row in boundaries if row["id"] == "interrupted-command")
        self.assertIsNone(interrupted["exitStatus"])
        self.assertTrue(interrupted["interrupted"])

    def test_quality_oracle_is_hash_bound_and_scores_omission_and_invention_independently(self):
        corpus = contract.load_closed_json(CORPUS)
        for case in corpus["cases"]:
            expected = case["expected"]
            self.assertEqual(
                set(expected),
                {
                    "exitStatus", "interrupted", "commandOutcome", "warningCount",
                    "warningRepresentativeIDs", "requiredDiagnosticIDs", "failedTestIDs",
                    "summary", "summaryFacts", "nextAction", "completionFacts",
                },
            )
            self.assertTrue(expected["summaryFacts"])
            self.assertTrue(expected["completionFacts"])
            self.assertTrue(expected["nextAction"])
            self.assertLessEqual(
                len(expected["warningRepresentativeIDs"]), expected["warningCount"]
            )

        failure = next(
            case for case in corpus["cases"]
            if case["expected"]["requiredDiagnosticIDs"]
            and case["expected"]["warningRepresentativeIDs"]
        )
        passing = self._result_for(failure)
        self.assertTrue(contract.score_condensation(failure, passing).passed)
        mutations = {
            "diagnostic_omission": lambda value: value["condensation"]["diagnostics"].pop(0),
            "diagnostic_invention": lambda value: value["condensation"]["diagnostics"].append({
                "id": "error-999", "severity": "error", "code": "INVENTED",
                "message": "invented", "file": None, "line": None,
                "column": None, "failedTestID": None,
            }),
            "warning_omission": lambda value: value["condensation"]["diagnostics"].pop(),
            "warning_invention": lambda value: value["condensation"]["diagnostics"].append({
                "id": "warning-999", "severity": "warning", "code": "INVENTED",
                "message": "invented", "file": None, "line": None,
                "column": None, "failedTestID": None,
            }),
            "summary_fact_omission": lambda value: value["condensation"]["summaryFacts"].pop(),
            "summary_fact_invention": lambda value: value["condensation"]["summaryFacts"].append("invented=true"),
            "completion_fact_omission": lambda value: value["condensation"]["completionFacts"].pop(),
            "completion_fact_invention": lambda value: value["condensation"]["completionFacts"].append("invented=true"),
        }
        for reason, mutate in mutations.items():
            candidate = deepcopy(passing)
            mutate(candidate)
            with self.subTest(reason=reason):
                score = contract.score_condensation(failure, candidate)
                self.assertFalse(score.passed)
                self.assertIn(reason, score.reason_codes)

    def test_score_condensation_rejects_every_required_mutation(self):
        corpus = contract.load_closed_json(CORPUS)
        failure = next(row for row in corpus["cases"] if row["commandClass"] == "test" and row["expected"]["exitStatus"] not in (0, None))
        result = self._result_for(failure)
        self.assertEqual(contract.score_condensation(failure, result), contract.QualityScore(True, ()))

        mutations = {
            "removed_fatal": lambda value: value["condensation"]["diagnostics"].pop(),
            "invented_fatal": lambda value: value["condensation"]["diagnostics"].append(dict(value["condensation"]["diagnostics"][0], id="fatal-999")),
            "exit": lambda value: value.__setitem__("exitStatus", 0),
            "interruption": lambda value: value.__setitem__("interrupted", True),
            "path": lambda value: value["condensation"]["diagnostics"][0].__setitem__("file", "Sources/Elsewhere.swift"),
            "line": lambda value: value["condensation"]["diagnostics"][0].__setitem__("line", 999),
            "code": lambda value: value["condensation"]["diagnostics"][0].__setitem__("code", "TEST-999"),
            "test_id": lambda value: value["condensation"]["diagnostics"][0].__setitem__("failedTestID", "Tests.Other/test_other"),
            "warnings": lambda value: value["condensation"].__setitem__("warningCount", value["condensation"]["warningCount"] + 1),
            "oversize": lambda value: value["condensation"].__setitem__("summary", "x" * 4097),
        }
        for name, mutate in mutations.items():
            candidate = json.loads(json.dumps(result))
            mutate(candidate)
            with self.subTest(name=name):
                score = contract.score_condensation(failure, candidate)
                self.assertFalse(score.passed)
                self.assertEqual(score.reason_codes, tuple(sorted(score.reason_codes)))

    def test_score_requires_a_closed_applied_result_and_matching_command_outcome(self):
        corpus = contract.load_closed_json(CORPUS)
        failure = next(row for row in corpus["cases"] if row["commandClass"] == "test" and row["expected"]["exitStatus"] == 1)
        result = self._result_for(failure)
        for name, mutate in {
            "top_level_key": lambda value: value.__setitem__("invented", True),
            "condensation_key": lambda value: value["condensation"].__setitem__("invented", True),
            "command_class": lambda value: value.__setitem__("commandClass", "build"),
            "success_for_failure": lambda value: value.__setitem__("exitStatus", 0),
        }.items():
            candidate = json.loads(json.dumps(result))
            mutate(candidate)
            with self.subTest(name=name):
                score = contract.score_condensation(failure, candidate)
                self.assertFalse(score.passed)
                self.assertIn("invalid_result" if "key" in name else "command_outcome_regression", score.reason_codes)

        for outcome in ("declined", "fail"):
            candidate = canonical_result(outcome)
            candidate["commandClass"] = failure["commandClass"]
            candidate["exitStatus"] = failure["expected"]["exitStatus"]
            candidate["interrupted"] = failure["expected"]["interrupted"]
            with self.subTest(outcome=outcome):
                score = contract.score_condensation(failure, candidate)
                self.assertFalse(score.passed)
                self.assertIn("command_outcome_regression", score.reason_codes)

    def test_score_condensation_fails_closed_for_malformed_untrusted_shapes(self):
        case = next(
            row for row in canonical_benchmark()["cases"]
            if row["expected"]["commandOutcome"] == "failure"
        )
        result = self._result_for(case)
        malformed = (
            {**result, "condensation": []},
            {**result, "condensation": None},
            {
                **result,
                "condensation": {
                    **result["condensation"],
                    "summaryFacts": [{}],
                },
            },
            {
                **result,
                "condensation": {
                    **result["condensation"],
                    "completionFacts": [{}],
                },
            },
        )
        for candidate in malformed:
            with self.subTest(condensation=candidate["condensation"]):
                score = contract.score_condensation(case, candidate)
                self.assertFalse(score.passed)
                self.assertIn("invalid_result", score.reason_codes)

    def test_score_condensation_rejects_a_stale_oracle_hash(self):
        case = deepcopy(canonical_benchmark()["cases"][0])
        case["expected"]["summary"] = "synthetic tampered summary"
        result = self._result_for(case)
        with self.assertRaises(contract.ContractError):
            contract.score_condensation(case, result)

    def test_validate_benchmark_enforces_the_complete_hash_bound_corpus(self):
        corpus = contract.load_closed_json(CORPUS)
        self.assertEqual(contract.validate_benchmark(corpus), corpus)
        mutations = {
            "missing_case": lambda value: value["cases"].pop(),
            "unapproved_form": lambda value: value["cases"][0].__setitem__("commandForm", "echo synthetic"),
            "unbalanced_form": lambda value: value["cases"][0].__setitem__("commandForm", value["cases"][2]["commandForm"]),
            "rendered_hash": lambda value: value["cases"][0].__setitem__("renderedSha256", "0" * 64),
            "corpus_hash": lambda value: value.__setitem__("corpusSha256", "0" * 64),
        }
        for name, mutate in mutations.items():
            candidate = json.loads(json.dumps(corpus))
            mutate(candidate)
            with self.subTest(name=name), self.assertRaises(contract.ContractError):
                contract.validate_benchmark(candidate)


class Dev142CostTests(unittest.TestCase):
    def _usage_for_total(self, total):
        output_tokens = min(total, 200)
        return contract.normalize_usage("openai-responses-usage-v1", {
            "input_tokens": total - output_tokens,
            "cached_tokens": 0,
            "output_tokens": output_tokens,
            "reasoning_tokens": 0,
        })

    def _arm(self, host, case_id, role, total, *, parent_turns=1, quality=None):
        return {
            "host": host,
            "caseID": case_id,
            "workflow": "diagnostic-condensation",
            "parentModel": "synthetic-parent-v1",
            "provider": "openai-responses-usage-v1",
            "normalizationVersion": "openai-responses-usage-v1",
            "toolchain": "synthetic-toolchain-v1",
            "policyVersion": contract.Policy.POLICY_VERSION,
            "commandClass": "test",
            "arm": role,
            "usage": self._usage_for_total(total),
            "parentTurns": parent_turns,
            "appleAttempts": 0 if role == "pluginOff" else 1,
            "replacements": 0 if role == "pluginOff" else 1,
            "declines": 0,
            "fallbacks": 0,
            "quality": contract.QualityScore(True, ()) if quality is None else quality,
        }

    def _pair(self, host, case_id, *, off_total=1000, on_total=900, **changes):
        off_changes = changes.pop("off", {})
        on_changes = changes.pop("on", {})
        off = self._arm(host, case_id, "pluginOff", off_total)
        on = self._arm(host, case_id, "pluginOn", on_total)
        off.update(off_changes)
        on.update(on_changes)
        for key, value in changes.items():
            on[key] = value
        return contract.score_pair(off, on)

    def _48_pairs(self, *, off_total=1000, on_total=900):
        return [
            self._pair(host, case_id, off_total=off_total, on_total=on_total)
            for host, case_id in contract.REQUIRED_PAIR_IDENTITIES
        ]

    def test_openai_subsets_are_not_double_counted(self):
        usage = contract.normalize_usage("openai-responses-usage-v1", {
            "input_tokens": 1000,
            "cached_tokens": 600,
            "output_tokens": 200,
            "reasoning_tokens": 150,
        })
        self.assertEqual(usage.input_tokens, 1000)
        self.assertEqual(usage.cached_input_tokens, 600)
        self.assertEqual(usage.output_tokens, 200)
        self.assertEqual(usage.reasoning_tokens, 150)
        self.assertEqual(usage.total_parent_model_tokens, 1200)

    def test_anthropic_cache_categories_are_additive_and_reasoning_is_null(self):
        usage = contract.normalize_usage("anthropic-messages-usage-v1", {
            "input_tokens": 1000,
            "cache_read_input_tokens": 600,
            "cache_creation_input_tokens": 150,
            "output_tokens": 200,
        })
        self.assertEqual(usage.cached_input_tokens, 750)
        self.assertIsNone(usage.reasoning_tokens)
        self.assertEqual(usage.total_parent_model_tokens, 1950)

    def test_normalization_blocks_missing_invalid_subset_and_unknown_usage_fields(self):
        invalid = (
            ("openai-responses-usage-v1", {"input_tokens": 1, "cached_tokens": 0, "output_tokens": 1}),
            ("openai-responses-usage-v1", {"input_tokens": 1, "cached_tokens": 2, "output_tokens": 1, "reasoning_tokens": 0}),
            ("openai-responses-usage-v1", {"input_tokens": True, "cached_tokens": 0, "output_tokens": 1, "reasoning_tokens": 0}),
            ("anthropic-messages-usage-v1", {"input_tokens": 1, "cache_read_input_tokens": 0, "cache_creation_input_tokens": -1, "output_tokens": 1}),
            ("unknown-provider", {}),
        )
        for provider, usage in invalid:
            with self.subTest(provider=provider, usage=usage), self.assertRaises(contract.BlockedEvidence):
                contract.normalize_usage(provider, usage)

    def test_normalization_blocks_unsigned_overflow(self):
        with self.assertRaises(contract.BlockedEvidence) as caught:
            contract.normalize_usage("anthropic-messages-usage-v1", {
                "input_tokens": (1 << 64) - 1,
                "cache_read_input_tokens": 1,
                "cache_creation_input_tokens": 0,
                "output_tokens": 0,
            })
        self.assertEqual(caught.exception.reason, "usage_overflow")

    def test_score_pair_blocks_zero_denominator_and_mismatched_identity(self):
        host, case_id = contract.REQUIRED_PAIR_IDENTITIES[0]
        zero = self._pair(host, case_id, off_total=0, on_total=0)
        self.assertEqual(zero.status, "blocked")
        self.assertIn("invalid_plugin_off_denominator", zero.reason_codes)
        mismatch = self._pair(host, case_id, on={"workflow": "other-workflow"})
        self.assertEqual(mismatch.status, "blocked")
        self.assertIn("pair_identity_mismatch", mismatch.reason_codes)

    def test_score_pair_emits_pass_for_a_conforming_pair(self):
        pair = self._pair(*contract.REQUIRED_PAIR_IDENTITIES[0])
        self.assertEqual(pair.status, "pass")
        self.assertEqual(pair.reduction_ppm, 100000)

    def test_release_uses_integer_even_median_and_exact_ten_percent_boundary(self):
        pairs = self._48_pairs()
        for index, pair in enumerate(pairs):
            if index < 24:
                pairs[index] = self._pair(pair.host, pair.case_id, on_total=1000)
            else:
                pairs[index] = self._pair(pair.host, pair.case_id, on_total=800)
        score = contract.release_gate(pairs)
        self.assertEqual(score.status, "pass")
        self.assertEqual(score.median_reduction_ppm, 100000)
        below = self._48_pairs(on_total=901)
        self.assertEqual(contract.release_gate(below).status, "fail")

    def test_release_rejects_correctness_regression_and_extra_parent_turn(self):
        pairs = self._48_pairs()
        host, case_id = contract.REQUIRED_PAIR_IDENTITIES[0]
        pairs[0] = self._pair(host, case_id, on={"quality": contract.QualityScore(False, ("regression",))})
        pairs[1] = self._pair(*contract.REQUIRED_PAIR_IDENTITIES[1], on={"parentTurns": 2})
        score = contract.release_gate(pairs)
        self.assertEqual(score.status, "fail")
        self.assertEqual(score.correctness_regressions, 1)
        self.assertEqual(score.additional_parent_model_turns, 1)

    def test_release_blocks_missing_and_blocked_required_pairs(self):
        pairs = self._48_pairs()
        missing = contract.release_gate(pairs[1:])
        self.assertEqual(missing.status, "blocked")
        self.assertEqual(missing.blocked_required_pairs, 1)
        pairs[0] = replace(pairs[0], status="blocked", reduction_ppm=None, reason_codes=("provider_missing",))
        blocked = contract.release_gate(pairs)
        self.assertEqual(blocked.status, "blocked")
        self.assertEqual(blocked.blocked_required_pairs, 1)

    def test_release_rejects_duplicate_required_pair_and_excludes_exploratory_pair_from_median(self):
        pairs = self._48_pairs()
        duplicate = contract.release_gate([*pairs, pairs[0]])
        self.assertEqual(duplicate.status, "fail")
        exploratory = replace(pairs[0], host="exploratory-host", case_id="exploratory-case", reduction_ppm=-900000)
        score = contract.release_gate([*pairs, exploratory])
        self.assertEqual(score.status, "pass")
        self.assertEqual(score.exploratory_pairs, 1)
        self.assertEqual(score.median_reduction_ppm, 100000)

    def test_release_requires_complete_10_0_0_matrix(self):
        pairs = self._48_pairs(off_total=1000, on_total=900)
        score = contract.release_gate(pairs)
        self.assertEqual(score.status, "pass")
        self.assertEqual(score.valid_required_pairs, 48)
        self.assertEqual(score.blocked_required_pairs, 0)
        self.assertEqual(score.median_reduction_ppm, 100000)
        self.assertEqual(score.correctness_regressions, 0)
        self.assertEqual(score.additional_parent_model_turns, 0)

    def test_release_closed_validates_forged_pair_scores_before_aggregation(self):
        pairs = self._48_pairs()
        malformed = (
            replace(pairs[0], status="valid"),
            replace(pairs[0], status="pass", reduction_ppm=None),
            replace(pairs[0], status="blocked", reduction_ppm=0, reason_codes=("blocked",)),
            replace(pairs[0], reduction_ppm=1000001),
            replace(pairs[0], correctness_regressions=True),
            replace(pairs[0], additional_parent_model_turns=-1),
            replace(pairs[0], reason_codes=("unexpected",)),
        )
        for forged in malformed:
            with self.subTest(forged=forged), self.assertRaises(contract.ContractError):
                contract.release_gate([forged, *pairs[1:]])

        cancelled = list(pairs)
        cancelled[0] = replace(cancelled[0], correctness_regressions=1)
        cancelled[1] = replace(cancelled[1], correctness_regressions=-1)
        with self.assertRaises(contract.ContractError):
            contract.release_gate(cancelled)

    def test_serialized_cost_model_round_trips_exact_96_arms_and_48_derived_pairs(self):
        evidence = canonical_serialized_cost_evidence()
        self.assertEqual(len(evidence["arms"]), 96)
        self.assertEqual(len(evidence["pairs"]), 48)
        self.assertEqual(Counter(arm["arm"] for arm in evidence["arms"]), {
            "pluginOff": 48, "pluginOn": 48,
        })
        self.assertEqual(contract.validate_benchmark(evidence), evidence)
        self.assertEqual(contract.derive_benchmark(evidence), evidence)

        corpus = {case["id"]: case for case in canonical_benchmark()["cases"]}
        for arm in evidence["arms"]:
            case = corpus[arm["caseID"]]
            self.assertEqual(arm["caseRenderedSha256"], case["renderedSha256"])
            self.assertEqual(arm["commandClass"], case["commandClass"])
            self.assertEqual(arm["normalizationVersion"], arm["provider"])
            if arm["arm"] == "pluginOff":
                self.assertEqual((arm["appleAttempts"], arm["replacements"]), (0, 0))

    def test_serialized_cost_model_rejects_unlinked_roles_hashes_classes_and_trusted_aggregates(self):
        mutations = {
            "missing_arm": lambda value: value["arms"].pop(),
            "duplicate_role": lambda value: value["arms"][1].__setitem__("arm", "pluginOff"),
            "case_hash": lambda value: value["arms"][0].__setitem__("caseRenderedSha256", "0" * 64),
            "command_class": lambda value: value["arms"][0].__setitem__("commandClass", "lint"),
            "normalization": lambda value: value["arms"][0].__setitem__("normalizationVersion", "anthropic-messages-usage-v1"),
            "plugin_off_attempt": lambda value: value["arms"][0].__setitem__("appleAttempts", 1),
            "pair_reduction": lambda value: value["pairs"][0].__setitem__("reductionPPM", 999999),
            "release_status": lambda value: value["release"].__setitem__("status", "blocked"),
            "release_median": lambda value: value["release"].__setitem__("medianReductionPPM", 0),
        }
        for name, mutate in mutations.items():
            candidate = canonical_serialized_cost_evidence()
            mutate(candidate)
            with self.subTest(name=name), self.assertRaises(contract.ContractError):
                contract.validate_benchmark(candidate)

    def test_serialized_cost_model_rejects_incoherent_route_counters(self):
        mutations = {
            "plugin_off_decline": lambda value: value["arms"][0].__setitem__("declines", 1),
            "plugin_off_fallback": lambda value: value["arms"][0].__setitem__("fallbacks", 1),
            "plugin_on_replacement_and_decline": lambda value: value["arms"][1].update(declines=1, fallbacks=1),
            "plugin_on_no_terminal_outcome": lambda value: value["arms"][1].update(replacements=0, fallbacks=0),
            "plugin_on_decline_without_fallback": lambda value: value["arms"][1].update(replacements=0, declines=1, fallbacks=0),
            "decline_count_above_one": lambda value: value["arms"][1].__setitem__("declines", 2),
            "fallback_count_above_one": lambda value: value["arms"][1].__setitem__("fallbacks", 2),
        }
        for name, mutate in mutations.items():
            candidate = canonical_serialized_cost_evidence()
            mutate(candidate)
            with self.subTest(name=name), self.assertRaises(contract.ContractError):
                contract.validate_benchmark(candidate)

        fallback = canonical_serialized_cost_evidence()
        fallback["arms"][1].update(replacements=0, declines=1, fallbacks=1)
        derived = contract.derive_benchmark(fallback)
        self.assertEqual(derived["pairs"][0]["status"], "pass")
        self.assertEqual(contract.validate_benchmark(derived), derived)

    def test_missing_provider_usage_and_counters_derive_blocked_not_zero_or_pass(self):
        for key in (
            "providerUsage", "appleAttempts", "replacements", "declines",
            "fallbacks",
        ):
            candidate = canonical_serialized_cost_evidence()
            candidate["arms"][1][key] = None
            derived = contract.derive_benchmark(candidate)
            with self.subTest(key=key):
                self.assertEqual(derived["pairs"][0]["status"], "blocked")
                self.assertIsNone(derived["pairs"][0]["reductionPPM"])
                self.assertEqual(derived["release"]["status"], "blocked")
                self.assertEqual(derived["release"]["blockedRequiredPairs"], 1)
                self.assertEqual(contract.validate_benchmark(derived), derived)

    def test_serialized_provider_components_are_exact_and_totals_are_never_trusted(self):
        candidate = canonical_serialized_cost_evidence()
        usage = candidate["arms"][0]["providerUsage"]
        usage["total_tokens"] = 1
        with self.assertRaises(contract.ContractError):
            contract.validate_benchmark(candidate)

        candidate = canonical_serialized_cost_evidence()
        candidate["arms"][0]["provider"] = "anthropic-messages-usage-v1"
        candidate["arms"][0]["normalizationVersion"] = "anthropic-messages-usage-v1"
        candidate["arms"][0]["providerUsage"] = {
            "input_tokens": 700,
            "cache_read_input_tokens": 100,
            "cache_creation_input_tokens": 100,
            "output_tokens": 100,
        }
        derived = contract.derive_benchmark(candidate)
        self.assertNotEqual(derived["pairs"][0]["status"], "pass")


class Dev142SchemaParityTests(unittest.TestCase):
    def _schema(self, name):
        return json.loads((SCHEMAS / name).read_text())

    def test_request_schema_matches_field_value_and_status_contract(self):
        schema = self._schema("dev-142-request.schema.json")
        accepted = canonical_request()
        line = dict(accepted["fields"][0], name="line", value=1)
        accepted = bind_request_fields(
            accepted, [accepted["fields"][0], line], target_bytes=8192
        )
        self.assertEqual(contract.validate_request(accepted), accepted)
        self.assertTrue(schema_accepts(schema, accepted))
        rejected = deepcopy(accepted)
        rejected["fields"][1]["value"] = "1"
        with self.assertRaises(contract.ContractError):
            contract.validate_request(rejected)
        self.assertFalse(schema_accepts(schema, rejected))
        rejected = dict(accepted, exitStatus=None, interrupted=False)
        with self.assertRaises(contract.ContractError):
            contract.validate_request(rejected)
        self.assertFalse(schema_accepts(schema, rejected))

    def test_result_schema_matches_tagged_union_and_status_contract(self):
        schema = self._schema("dev-142-result.schema.json")
        for outcome in ("applied", "declined", "fail"):
            accepted = canonical_result(outcome)
            self.assertEqual(contract.validate_result(accepted), accepted)
            self.assertTrue(schema_accepts(schema, accepted))
        rejected = dict(canonical_result("declined"), exitStatus=None, interrupted=False)
        with self.assertRaises(contract.ContractError):
            contract.validate_result(rejected)
        self.assertFalse(schema_accepts(schema, rejected))
        rejected = {**canonical_result("declined"), "condensation": {}}
        with self.assertRaises(contract.ContractError):
            contract.validate_result(rejected)
        self.assertFalse(schema_accepts(schema, rejected))

    def test_benchmark_schema_matches_blocked_and_plugin_off_contract(self):
        schema = self._schema("dev-142-benchmark.schema.json")
        evidence = canonical_serialized_cost_evidence()
        self.assertEqual(contract.validate_benchmark(evidence), evidence)
        self.assertTrue(schema_accepts(schema, evidence))
        blocked_reduction = deepcopy(evidence)
        blocked_reduction["pairs"][0]["status"] = "blocked"
        blocked_reduction["pairs"][0]["reductionPPM"] = 100000
        with self.assertRaises(contract.ContractError):
            contract.validate_benchmark(blocked_reduction)
        self.assertFalse(schema_accepts(schema, blocked_reduction))
        plugin_off_attempt = deepcopy(evidence)
        plugin_off_attempt["arms"][0]["appleAttempts"] = 1
        with self.assertRaises(contract.ContractError):
            contract.validate_benchmark(plugin_off_attempt)
        self.assertFalse(schema_accepts(schema, plugin_off_attempt))

    def test_closed_vocabulary_enforces_cross_value_request_result_and_corpus_invariants(self):
        request_schema = self._schema("dev-142-request.schema.json")
        duplicate_name = canonical_request()
        duplicate_name["fields"].append(dict(duplicate_name["fields"][0], value="second message"))
        absolute_file = canonical_request()
        absolute_file["fields"] = [dict(absolute_file["fields"][0], name="file", value="/private/path")]
        traversal_file = canonical_request()
        traversal_file["fields"] = [dict(traversal_file["fields"][0], name="file", value="../private/path")]
        incorrect_estimate = dict(canonical_request(), estimatedSavingsBytes=4097)
        for rejected in (duplicate_name, absolute_file, traversal_file, incorrect_estimate):
            with self.subTest(request=rejected), self.assertRaises(contract.ContractError):
                contract.validate_request(rejected)
            self.assertFalse(schema_accepts(request_schema, rejected))

        result_schema = self._schema("dev-142-result.schema.json")
        result = canonical_result()
        identity = {
            "id": "diagnostic-1", "severity": "error", "code": "E1", "message": "failure",
            "file": "Sources/App.swift", "line": 1, "column": 1, "failedTestID": None,
        }
        duplicate_identity = dict(identity, id="diagnostic-2")
        duplicate_result = {**result, "condensation": {**result["condensation"], "diagnostics": [identity, duplicate_identity]}}
        warning_result = {**result, "condensation": {**result["condensation"], "warningCount": 1, "omittedWarningCount": 2}}
        exact_warning_mismatch = {
            **result,
            "condensation": {
                **result["condensation"],
                "warningCount": 2,
                "omittedWarningCount": 1,
            },
        }
        for rejected in (duplicate_result, warning_result, exact_warning_mismatch):
            with self.subTest(result=rejected), self.assertRaises(contract.ContractError):
                contract.validate_result(rejected)
            self.assertFalse(schema_accepts(result_schema, rejected))

        benchmark_schema = self._schema("dev-142-benchmark.schema.json")
        duplicate_case = canonical_benchmark()
        duplicate_case["cases"].append(dict(duplicate_case["cases"][0], commandForm="pnpm test"))
        with self.assertRaises(contract.ContractError):
            contract.validate_benchmark(duplicate_case)
        self.assertFalse(schema_accepts(benchmark_schema, duplicate_case))

    def test_local_schema_equality_distinguishes_boolean_and_integer_json_values(self):
        self.assertFalse(schema_accepts({"const": 1}, True))
        self.assertFalse(schema_accepts({"enum": [1]}, True))
        self.assertTrue(schema_accepts({"type": "array", "uniqueItems": True}, [True, 1]))

    def test_closed_vocabulary_covers_diagnostic_paths_and_evidence_ids(self):
        result_schema = self._schema("dev-142-result.schema.json")
        result = canonical_result()
        diagnostic = {
            "id": "diagnostic-1", "severity": "error", "code": "E1", "message": "failure",
            "file": "/private/path", "line": 1, "column": 1, "failedTestID": None,
        }
        for path in ("/private/path", "../private/path"):
            rejected = {**result, "condensation": {**result["condensation"], "diagnostics": [dict(diagnostic, file=path)]}}
            with self.subTest(path=path), self.assertRaises(contract.ContractError):
                contract.validate_result(rejected)
            self.assertFalse(schema_accepts(result_schema, rejected))

        benchmark_schema = self._schema("dev-142-benchmark.schema.json")
        evidence = canonical_serialized_cost_evidence()
        duplicate_arm = deepcopy(evidence)
        duplicate_arm["arms"][1]["id"] = duplicate_arm["arms"][0]["id"]
        duplicate_pair = deepcopy(evidence)
        duplicate_pair["pairs"][1]["id"] = duplicate_pair["pairs"][0]["id"]
        for rejected in (duplicate_arm, duplicate_pair):
            with self.subTest(evidence=rejected), self.assertRaises(contract.ContractError):
                contract.validate_benchmark(rejected)
            self.assertFalse(schema_accepts(benchmark_schema, rejected))


class Dev142CommandParserTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        (self.root / "Sources").mkdir()
        (self.root / "Tests").mkdir()
        (self.root / "Scratch").mkdir()
        (self.root / "Sources" / "App.swift").write_text("struct App {}\n")
        (self.root / "Tests" / "test_app.py").write_text("def test_app(): pass\n")
        (self.root / "App.xcodeproj").mkdir()
        (self.root / "App.xcworkspace").mkdir()

    def tearDown(self):
        self.directory.cleanup()

    def test_every_exact_prefix_selects_its_only_command_class(self):
        accepted = {
            "test": (
                "swift test", "xcodebuild test -project App.xcodeproj", "npm test", "npm run test",
                "pnpm test", "pnpm run test", "python3 -m unittest", "python3 -m pytest",
            ),
            "build": (
                "swift build", "xcodebuild build -workspace App.xcworkspace", "npm run build", "pnpm build",
                "pnpm run build", "python3 -m build",
            ),
            "typecheck": (
                "swiftc -typecheck Sources/App.swift", "npm run typecheck", "pnpm typecheck",
                "pnpm run typecheck", "python3 -m mypy Sources",
            ),
            "lint": (
                "swift format lint Sources", "npm run lint", "pnpm lint", "pnpm run lint",
                "python3 -m ruff check Sources",
            ),
        }
        for expected_class, commands in accepted.items():
            for command in commands:
                with self.subTest(command=command):
                    selection = contract.parse_command(command, self.root)
                    self.assertEqual(selection.command_class, expected_class)
                    self.assertEqual(selection.tokens, tuple(command.split()))

    def test_suffix_terminals_are_closed(self):
        accepted = (
            "swift test --configuration debug --package-path Scratch --scratch-path Scratch --filter AppTests/test_one",
            "swift build --configuration release --package-path Scratch --scratch-path Scratch",
            "swiftc -typecheck Sources/App.swift",
            "swift format lint --recursive --strict Sources",
            "xcodebuild test -project App.xcodeproj -scheme App -configuration Debug -sdk iphonesimulator -destination platform=iOS -derivedDataPath Scratch -quiet",
            "python3 -m unittest -v discover -s Tests -p test_*.py -t Tests",
            "python3 -m unittest Tests.test_app",
            "python3 -m pytest -q -v -x --maxfail=1 -k test_app -m unit Tests/test_app.py::test_app",
            'python3 -m pytest -k "test_app and (test_other)" Tests/test_app.py',
            "python3 -m build --sdist --wheel",
            "python3 -m mypy --strict --no-incremental Sources",
            "python3 -m ruff check --no-fix --output-format concise Sources",
        )
        for command in accepted:
            with self.subTest(command=command):
                self.assertIsNotNone(contract.parse_command(command, self.root))

        for option_like_path in (
            "--recursive", "--strict", "--no-incremental", "--no-fix",
            "--fix", "--unsafe-fixes",
        ):
            (self.root / option_like_path).write_text("synthetic option-like path\n")
        rejected = (
            "swift test --configuration debug --configuration release",
            "swift build --filter target",
            "swiftc -typecheck --help Sources/App.swift",
            "swift format lint --recursive --recursive Sources",
            "xcodebuild test -project App.xcodeproj -workspace App.xcworkspace",
            "python3 -m unittest discover -s Tests -s .",
            "python3 -m pytest --maxfail=0",
            "python3 -m build --sdist --sdist",
            "python3 -m mypy Sources --strict",
            "python3 -m mypy --no-incremental --strict Sources",
            "swift format lint --strict --recursive Sources",
            "python3 -m ruff check --output-format concise --no-fix Sources",
            "python3 -m ruff check --fix Sources",
            "npm test -- --watch",
        )
        for command in rejected:
            with self.subTest(command=command), self.assertRaises(contract.RouteDeclined):
                contract.parse_command(command, self.root)

    def test_parser_rejects_non_single_invocation_and_unsafe_paths(self):
        rejected = (
            "/usr/bin/swift test", "./swift test", "env X=1 swift test", "FOO=bar swift test",
            "sudo swift test", "swift test\necho unsafe", "swift test && npm test", "swift test | cat",
            "swift test > output", "swift test $(whoami)", "swift test $HOME", "swift test; npm test",
            "swiftc -typecheck ../outside.swift", "python3 -m pytest /tmp/test.py",
        )
        for command in rejected:
            with self.subTest(command=command), self.assertRaises(contract.RouteDeclined):
                contract.parse_command(command, self.root)

        (self.root / "outside.swift").write_text("struct Outside {}\n")
        (self.root / "Linked.swift").symlink_to(self.root / "outside.swift")
        with self.assertRaises(contract.RouteDeclined):
            contract.parse_command("swiftc -typecheck Linked.swift", self.root)

        (self.root / "LinkedSources").symlink_to(self.root / "Sources", target_is_directory=True)
        with self.assertRaises(contract.RouteDeclined) as caught:
            contract.parse_command("swiftc -typecheck LinkedSources/App.swift", self.root)
        self.assertEqual(caught.exception.reason, "command_not_allowed")

    def test_parser_rejects_filesystem_identity_drift(self):
        target = (self.root / "Sources" / "App.swift").resolve()
        original_lstat = contract._lstat
        calls = 0

        def drift(path):
            nonlocal calls
            stat = original_lstat(path)
            if Path(path) == target:
                calls += 1
                if calls > 1:
                    return os.stat_result((
                        stat.st_mode, stat.st_ino + 1, stat.st_dev, stat.st_nlink,
                        stat.st_uid, stat.st_gid, stat.st_size, stat.st_atime,
                        stat.st_mtime, stat.st_ctime,
                    ))
            return stat

        contract._lstat = drift
        try:
            with self.assertRaises(contract.RouteDeclined) as caught:
                contract.parse_command("swiftc -typecheck Sources/App.swift", self.root)
            self.assertEqual(caught.exception.reason, "command_not_allowed")
        finally:
            contract._lstat = original_lstat

    def test_parser_captures_root_ancestors_target_and_nearest_existing_parent(self):
        original_lstat = contract._lstat
        observed = Counter()

        def recording_lstat(path):
            observed[Path(path).resolve(strict=False)] += 1
            return original_lstat(path)

        contract._lstat = recording_lstat
        try:
            contract.parse_command("swiftc -typecheck Sources/App.swift", self.root)
            contract.parse_command("swift test --scratch-path Scratch/New/Derived", self.root)
        finally:
            contract._lstat = original_lstat

        resolved_root = self.root.resolve()
        root_chain = (resolved_root, *resolved_root.parents)
        for path in root_chain:
            with self.subTest(path=path):
                self.assertGreaterEqual(observed[path], 2)
        self.assertGreaterEqual(observed[(self.root / "Sources" / "App.swift").resolve()], 2)
        self.assertGreaterEqual(observed[(self.root / "Scratch").resolve()], 2)

    def test_every_filesystem_failure_and_recheck_drift_normalizes_to_route_decline(self):
        original_lstat = contract._lstat
        target = (self.root / "Sources" / "App.swift").resolve()

        def run_with(replacement):
            contract._lstat = replacement
            try:
                with self.assertRaises(contract.RouteDeclined) as caught:
                    contract.parse_command("swiftc -typecheck Sources/App.swift", self.root)
                self.assertEqual(caught.exception.reason, "command_not_allowed")
            finally:
                contract._lstat = original_lstat

        def permission_error(path):
            if Path(path).resolve(strict=False) == target:
                raise PermissionError("synthetic private diagnostic")
            return original_lstat(path)

        run_with(permission_error)

        calls = 0

        def disappears(path):
            nonlocal calls
            if Path(path).resolve(strict=False) == target:
                calls += 1
                if calls > 1:
                    raise FileNotFoundError("synthetic disappearance")
            return original_lstat(path)

        run_with(disappears)

        new_parent = self.root / "New"
        new_parent.mkdir()
        appeared_target = new_parent / "Derived"
        parent_calls = 0

        def appears_after_absence_capture(path):
            nonlocal parent_calls
            if Path(path).resolve(strict=False) == new_parent.resolve():
                parent_calls += 1
                if parent_calls == 2:
                    appeared_target.mkdir()
            return original_lstat(path)

        contract._lstat = appears_after_absence_capture
        try:
            with self.assertRaises(contract.RouteDeclined) as caught:
                contract.parse_command(
                    "swift test --scratch-path New/Derived", self.root
                )
            self.assertEqual(caught.exception.reason, "command_not_allowed")
        finally:
            contract._lstat = original_lstat

        original_abspath = contract.os.path.abspath

        def unavailable_working_directory(_path):
            raise FileNotFoundError("synthetic unavailable working directory")

        contract.os.path.abspath = unavailable_working_directory
        try:
            with self.assertRaises(contract.RouteDeclined) as caught:
                contract._repository_root(".")
            self.assertEqual(caught.exception.reason, "command_not_allowed")
        finally:
            contract.os.path.abspath = original_abspath


class Dev142RoutingTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        (self.root / "Sources").mkdir()
        (self.root / "Sources" / "App.swift").write_text("struct App {}\n")

    def tearDown(self):
        self.directory.cleanup()

    def _context(self, **changes):
        context = {
            "eventName": "PostToolUse",
            "command": "swift test",
            "repoRoot": self.root,
            "appleAvailable": True,
            "localeSupported": True,
            "occupiedTokens": 6144,
            "contextSize": 8192,
            "sourceFacts": canonical_source_facts(),
            "bridge": self._bridge,
        }
        context.update(changes)
        return context

    def _bridge(self, request):
        result = canonical_result()
        result["commandClass"] = request["commandClass"]
        result["condensation"]["commandOutcome"] = (
            "success" if request["exitStatus"] == 0 else "failure"
        )
        return result

    def test_exact_size_and_budget_boundaries(self):
        self.assertEqual(contract.estimate_savings(8192), 4096)
        self.assertEqual(contract.estimate_savings(65536), 61440)
        with self.assertRaises(contract.RouteDeclined) as caught:
            contract.estimate_savings(8191)
        self.assertEqual(caught.exception.reason, "input_below_minimum")
        with self.assertRaises(contract.RouteDeclined) as caught:
            contract.estimate_savings(65537)
        self.assertEqual(caught.exception.reason, "input_above_maximum")
        self.assertTrue(contract.fits_apple_budget(6144, 8192))
        self.assertFalse(contract.fits_apple_budget(6145, 8192))

    def test_routes_selected_commands_and_declines_every_preflight_gate_without_a_bridge_attempt(self):
        for command, command_class in (
            ("swift test", "test"), ("swift build", "build"),
            ("swiftc -typecheck Sources/App.swift", "typecheck"), ("swift format lint Sources", "lint"),
        ):
            request = canonical_request()
            request["commandClass"] = command_class
            result = contract.route(request, self._context(command=command))
            self.assertEqual(result["outcome"], "applied")

        missing_occupied_tokens = self._context()
        missing_occupied_tokens.pop("occupiedTokens")
        missing_context_size = self._context()
        missing_context_size.pop("contextSize")
        declined = (
            (canonical_request(), self._context(eventName="PreToolUse"), "tool_not_allowed"),
            (canonical_request(), self._context(command="echo nope"), "command_not_allowed"),
            ({**canonical_request(), "toolName": "Read"}, self._context(), "tool_not_allowed"),
            (canonical_request(8191), self._context(), "input_below_minimum"),
            ({**canonical_request(), "fields": [dict(canonical_request()["fields"][0], classification="C2")]}, self._context(), "data_policy_denied"),
            ({**canonical_request(), "fields": [dict(canonical_request()["fields"][0], classification="C3")]}, self._context(), "data_policy_denied"),
            (canonical_request(), self._context(appleAvailable=False), "apple_unavailable"),
            (canonical_request(), self._context(localeSupported=False), "locale_unsupported"),
            (canonical_request(), self._context(occupiedTokens=6145), "context_budget_exceeded"),
            (canonical_request(), missing_occupied_tokens, "context_budget_exceeded"),
            (canonical_request(), missing_context_size, "context_budget_exceeded"),
        )
        for request, context, reason in declined:
            calls = []
            context["bridge"] = lambda value: calls.append(value)
            with self.subTest(reason=reason):
                result = contract.route(request, context)
                self.assertEqual(result, {"outcome": "declined", "reasonCode": reason, "preserveOriginal": True})
                self.assertEqual(calls, [])

    def test_calls_bridge_once_only_for_an_eligible_request_and_validates_the_response(self):
        calls = []

        def bridge(request):
            calls.append(request)
            return canonical_result()

        result = contract.route(canonical_request(), self._context(bridge=bridge))
        self.assertEqual(result["outcome"], "applied")
        self.assertEqual(calls, [canonical_request()])

        invalid_response = contract.route(canonical_request(), self._context(bridge=lambda request: {"outcome": "applied"}))
        self.assertEqual(invalid_response, {"outcome": "fail", "reasonCode": "invalid_response", "preserveOriginal": True})

    def test_file_fields_require_a_contained_non_symlink_repository_path_before_the_bridge(self):
        (self.root / "LinkedSources").symlink_to(self.root / "Sources", target_is_directory=True)
        for file_value in ("LinkedSources/App.swift", "Missing.swift", "/private/path", "Sources\\App.swift"):
            request = canonical_request()
            fields = [
                request["fields"][0],
                dict(request["fields"][0], name="file", value=file_value),
            ]
            request = bind_request_fields(request, fields, target_bytes=8192)
            calls = []
            result = contract.route(request, self._context(bridge=lambda value: calls.append(value)))
            with self.subTest(file_value=file_value):
                self.assertEqual(result, {"outcome": "declined", "reasonCode": "data_policy_denied", "preserveOriginal": True})
                self.assertEqual(calls, [])

    def test_untrusted_response_serialization_failure_fails_closed_after_one_attempt(self):
        calls = []

        def bridge(request):
            calls.append(request)
            response = canonical_result()
            response["condensation"]["summary"] = "\ud800"
            return response

        self.assertEqual(
            contract.route(canonical_request(), self._context(bridge=bridge)),
            {"outcome": "fail", "reasonCode": "invalid_response", "preserveOriginal": True},
        )
        self.assertEqual(calls, [canonical_request()])

    def test_schema_valid_bridge_fail_and_decline_preserve_their_distinct_invocation_statuses(self):
        for outcome, expected_status in (("fail", "fail"), ("declined", "declined")):
            calls = []

            def bridge(request, outcome=outcome):
                calls.append(request)
                return canonical_result(outcome)

            with self.subTest(outcome=outcome):
                self.assertEqual(
                    contract.route(canonical_request(), self._context(bridge=bridge)),
                    {"outcome": expected_status, "reasonCode": "generation_declined", "preserveOriginal": True},
                )
                self.assertEqual(calls, [canonical_request()])

    def test_preflight_recursively_rejects_sensitive_values_and_recomputes_canonical_bytes(self):
        sensitive_values = (
            "Bearer synthetic-private-token-12345678",
            "password=synthetic-private-value",
            "token=ghp_abcdefghijklmnopqrstuvwxyz0123456789",
            "ghp_abcdefghijklmnopqrstuvwxyz0123456789",
            "-----BEGIN PRIVATE KEY-----",
            "/Users/synthetic/private.txt",
            "/private/synthetic/private.txt",
            "/etc/passwd",
            r"C:\\Users\\synthetic\\private.txt",
            r"C:\\Temp\\customer-secret.txt",
            r"\\\\synthetic-server\\private-share",
        )
        for sensitive in sensitive_values:
            request = canonical_request()
            message = request["fields"][0]
            message["value"] = sensitive + "x" * 8200
            request = bind_request_fields(request, [message])
            calls = []
            with self.subTest(sensitive=sensitive):
                self.assertEqual(
                    contract.route(request, self._context(bridge=lambda value: calls.append(value))),
                    {"outcome": "declined", "reasonCode": "data_policy_denied", "preserveOriginal": True},
                )
                self.assertEqual(calls, [])

        request = canonical_request()
        nested = dict(request["fields"][0], value={"safe": ["nested", {"value": "secret=synthetic"}]})
        request["fields"] = [nested]
        request["inputBytes"] = 8192
        request["estimatedSavingsBytes"] = 4096
        calls = []
        self.assertEqual(
            contract.route(request, self._context(bridge=lambda value: calls.append(value))),
            {"outcome": "declined", "reasonCode": "data_policy_denied", "preserveOriginal": True},
        )
        self.assertEqual(calls, [])

        exact = canonical_request()
        self.assertEqual(len(canonical_field_bytes(exact["fields"])), exact["inputBytes"])
        self.assertEqual(contract.route(exact, self._context())["outcome"], "applied")
        for mutation in (
            {**exact, "inputBytes": exact["inputBytes"] + 1, "estimatedSavingsBytes": exact["estimatedSavingsBytes"] + 1},
            {**exact, "estimatedSavingsBytes": exact["estimatedSavingsBytes"] + 1},
        ):
            calls = []
            with self.subTest(mutation=mutation):
                result = contract.route(mutation, self._context(bridge=lambda value: calls.append(value)))
                self.assertEqual(result["outcome"], "declined")
                self.assertTrue(result["preserveOriginal"])
                self.assertEqual(calls, [])

    def test_bridge_receives_an_isolated_request_and_cannot_mutate_frozen_bindings_or_source_facts(self):
        request = canonical_request()
        original = deepcopy(request)
        context = self._context()
        frozen_source = deepcopy(context["sourceFacts"])
        observed = []

        def bridge(candidate):
            observed.append(candidate)
            candidate["callID"] = "invented-call"
            context["sourceFacts"]["summary"] = "invented summary"
            result = canonical_result()
            result["callID"] = candidate["callID"]
            result["condensation"]["summary"] = context["sourceFacts"]["summary"]
            return result

        result = contract.route(request, {**context, "bridge": bridge})
        self.assertEqual(
            result,
            {"outcome": "fail", "reasonCode": "invalid_response", "preserveOriginal": True},
        )
        self.assertEqual(request, original)
        self.assertIsNot(observed[0], request)
        self.assertEqual(frozen_source["summary"], "1 test failed")

    def test_all_response_outcomes_bind_to_the_frozen_request(self):
        for outcome in ("applied", "declined", "fail"):
            response = canonical_result(outcome)
            response["callID"] = "invented-call"
            with self.subTest(outcome=outcome):
                self.assertEqual(
                    contract.route(canonical_request(), self._context(bridge=lambda _request, response=response: response)),
                    {"outcome": "fail", "reasonCode": "invalid_response", "preserveOriginal": True},
                )

    def test_applied_response_semantics_are_application_validated_before_replacement(self):
        error = {
            "id": "error-001", "severity": "error", "code": "E001",
            "message": "synthetic failure", "file": "Sources/App.swift",
            "line": 1, "column": 1, "failedTestID": "Tests.App/test_failure",
        }
        warning = {
            "id": "warning-001", "severity": "warning", "code": "W001",
            "message": "synthetic warning", "file": "Sources/App.swift",
            "line": 2, "column": 1, "failedTestID": None,
        }
        valid = canonical_result()
        valid["condensation"] = {
            "commandOutcome": "failure",
            "summary": "one synthetic test failed",
            "summaryFacts": ["failed-test-count=1", "error-count=1"],
            "diagnostics": [error, warning],
            "warningCount": 1,
            "omittedWarningCount": 0,
            "nextAction": "inspect Sources/App.swift",
            "completionFacts": ["command-finished=true", "task-complete=false"],
        }
        context = self._context(sourceFacts=canonical_source_facts(valid))
        self.assertEqual(
            contract.route(canonical_request(), {**context, "bridge": lambda _request: deepcopy(valid)}),
            valid,
        )
        mutations = {
            "commandOutcome": lambda value: value["condensation"].__setitem__("commandOutcome", "success"),
            "summary": lambda value: value["condensation"].__setitem__("summary", "invented summary"),
            "summaryFacts": lambda value: value["condensation"]["summaryFacts"].append("invented=true"),
            "diagnosticOmission": lambda value: value["condensation"]["diagnostics"].pop(0),
            "diagnosticInvention": lambda value: value["condensation"]["diagnostics"].append(dict(error, id="error-999")),
            "warningCount": lambda value: value["condensation"].__setitem__("warningCount", 2),
            "nextAction": lambda value: value["condensation"].__setitem__("nextAction", "delete everything"),
            "completionFacts": lambda value: value["condensation"]["completionFacts"].append("task-complete=true"),
            "path": lambda value: value["condensation"]["diagnostics"][0].__setitem__("file", "../outside.swift"),
        }
        for name, mutate in mutations.items():
            candidate = deepcopy(valid)
            mutate(candidate)
            with self.subTest(name=name):
                result = contract.route(
                    canonical_request(),
                    {**context, "bridge": lambda _request, candidate=candidate: candidate},
                )
                self.assertEqual(
                    result,
                    {"outcome": "fail", "reasonCode": "invalid_response", "preserveOriginal": True},
                )

    def test_route_normalizes_post_capture_filesystem_exceptions_to_original_preserving_envelopes(self):
        original_lstat = contract._lstat
        root_calls = 0
        resolved_root = self.root.resolve()

        def fails_on_recheck(path):
            nonlocal root_calls
            if Path(path).resolve(strict=False) == resolved_root:
                root_calls += 1
                if root_calls > 1:
                    raise PermissionError("synthetic private host path")
            return original_lstat(path)

        contract._lstat = fails_on_recheck
        try:
            result = contract.route(canonical_request(), self._context())
        finally:
            contract._lstat = original_lstat
        self.assertIn(result["outcome"], ("declined", "fail"))
        self.assertTrue(result["preserveOriginal"])
        self.assertIn(result["reasonCode"], ("command_not_allowed", "contract_invariant_failed", "invalid_response"))

    def test_route_rejects_repository_replacement_during_bridge(self):
        displaced_root = self.root.with_name(f"{self.root.name}-displaced")

        def replacing_bridge(request):
            self.root.rename(displaced_root)
            self.root.mkdir()
            (self.root / "Sources").mkdir()
            (self.root / "Sources" / "App.swift").write_text(
                "struct Replacement {}\n"
            )
            return self._bridge(request)

        try:
            result = contract.route(
                canonical_request(), self._context(bridge=replacing_bridge)
            )
        finally:
            if self.root.exists():
                shutil.rmtree(self.root)
            displaced_root.rename(self.root)

        self.assertEqual(
            result,
            {
                "outcome": "fail",
                "reasonCode": "invalid_response",
                "preserveOriginal": True,
            },
        )

    def test_route_rechecks_command_operand_identity_after_bridge(self):
        source = self.root / "Sources" / "App.swift"
        displaced = self.root / "Sources" / "App.displaced.swift"
        request = canonical_request()
        request["commandClass"] = "typecheck"

        def replacing_bridge(candidate):
            source.rename(displaced)
            source.write_text("struct Replacement {}\n")
            return self._bridge(candidate)

        try:
            result = contract.route(
                request,
                self._context(
                    command="swiftc -typecheck Sources/App.swift",
                    bridge=replacing_bridge,
                ),
            )
        finally:
            if source.exists():
                source.unlink()
            displaced.rename(source)

        self.assertEqual(
            result,
            {
                "outcome": "fail",
                "reasonCode": "invalid_response",
                "preserveOriginal": True,
            },
        )


class Dev142ProofTests(unittest.TestCase):
    """The repository-only proof is deterministic metadata, never runtime proof."""

    ROUTING_BOUNDARIES = {
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
    }
    SAFETY_BOUNDARIES = {
        "S-PRIVATE-KEY-001", "S-PRIVATE-PATH-001", "S-RAW-PROMPT-001",
        "S-RAW-RESULT-001", "S-RAW-RESPONSE-001", "S-CREDENTIAL-001",
        "S-TRACE-001", "S-XCRESULT-001", "S-SELF-ATTEST-001",
        "S-EXTRA-KEY-001", "S-STATUS-001", "S-LIVE-CLAIM-001",
        "S-PRIVATE-POSIX-001", "S-WINDOWS-PATH-001", "S-UNC-PATH-001",
        "S-CREDENTIAL-VALUE-001", "S-NESTED-KEY-001",
    }
    EXPECTED_BOUNDARIES = {
        "P-BOUNDARY-001": {"D-INPUT-001", "D-OCCUPANCY-001", "D-INTERRUPTION-001"},
        "P-CORPUS-001": {"D-CORPUS-001"},
        "P-NORMALIZATION-001": {"D-NORMALIZATION-OPENAI-001", "D-NORMALIZATION-ANTHROPIC-001"},
        "P-QUALITY-001": {"D-QUALITY-001"},
        "P-RELEASE-001": {"D-RELEASE-MATRIX-001"},
        "P-SCHEMA-001": {
            "D-SCHEMA-REQUEST-001", "D-SCHEMA-RESULT-001",
            "D-SCHEMA-BENCHMARK-001", "D-SCHEMA-VOCABULARY-001",
        },
    }

    def _runner(self):
        spec = importlib.util.spec_from_file_location("dev142_proof_runner", PROOF_RUNNER)
        runner = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(runner)
        return runner

    def _run_proof(self, output):
        completed = subprocess.run(
            [sys.executable, str(PROOF_RUNNER), "--output", str(output)],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.stdout, "")
        self.assertEqual(completed.stderr, "")
        return json.loads(output.read_text(encoding="utf-8"))

    def test_proof_is_closed_deterministic_and_covers_the_offline_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.json"
            second = Path(directory) / "second.json"
            proof = self._run_proof(first)
            self._run_proof(second)
            self.assertEqual(first.read_bytes(), second.read_bytes())

        self.assertEqual(set(proof), {
            "schemaVersion", "issue", "status", "policyVersion", "action",
            "schemaCount", "eligibleCaseCount", "requiredArmCount", "requiredPairCount", "corpusSha256",
            "checks", "liveClaims",
        })
        self.assertEqual(proof["schemaVersion"], 1)
        self.assertEqual(proof["issue"], "DEV-142")
        self.assertEqual(proof["status"], "pass")
        self.assertEqual(proof["policyVersion"], contract.Policy.POLICY_VERSION)
        self.assertEqual(proof["action"], contract.Policy.ACTION)
        self.assertEqual(proof["schemaCount"], 3)
        self.assertEqual(proof["eligibleCaseCount"], 24)
        self.assertEqual(proof["requiredArmCount"], 96)
        self.assertEqual(proof["requiredPairCount"], 48)
        self.assertEqual(proof["corpusSha256"], contract.corpus_digest(canonical_benchmark()))
        self.assertEqual(proof["checks"], sorted(proof["checks"], key=lambda row: row["id"]))
        self.assertEqual(
            {row["id"] for row in proof["checks"]},
            {
                "P-BOUNDARY-001", "P-CORPUS-001", "P-NORMALIZATION-001",
                "P-QUALITY-001", "P-RELEASE-001", "P-ROUTING-001",
                "P-SCHEMA-001", "P-SAFETY-001",
            },
        )
        self.assertTrue(all(set(row) == {"id", "status", "boundaries"} and row["status"] == "pass" for row in proof["checks"]))
        self.assertEqual(proof["liveClaims"], {
            "appleInvocation": "not_applicable",
            "codexHook": "not_applicable",
            "claudeHook": "not_applicable",
            "parentTokenReduction": "blocked/provider_usage_not_executed",
        })

    def test_routing_and_safety_rows_bind_each_executed_boundary(self):
        with tempfile.TemporaryDirectory() as directory:
            proof = self._run_proof(Path(directory) / "proof.json")
        runner = self._runner()
        rows = {row["id"]: row for row in proof["checks"]}
        self.assertEqual(set(rows["P-ROUTING-001"]["boundaries"]), self.ROUTING_BOUNDARIES)
        self.assertEqual(set(rows["P-SAFETY-001"]["boundaries"]), self.SAFETY_BOUNDARIES)
        for check_id, boundaries in self.EXPECTED_BOUNDARIES.items():
            with self.subTest(check_id=check_id):
                self.assertEqual(set(rows[check_id]["boundaries"]), boundaries)
        self.assertEqual(runner._verify_routing(runner._contract()), tuple(sorted(self.ROUTING_BOUNDARIES)))
        self.assertEqual(runner._verify_safety(proof), tuple(sorted(self.SAFETY_BOUNDARIES)))

    def test_proof_validator_rejects_unsafe_or_self_attested_content(self):
        with tempfile.TemporaryDirectory() as directory:
            proof = self._run_proof(Path(directory) / "proof.json")
        runner = self._runner()
        mutations = (
            {**proof, "privatePath": "/Users/example/private"},
            {**proof, "rawPrompt": "synthetic prompt"},
            {**proof, "rawResult": "synthetic result"},
            {**proof, "rawResponse": "synthetic response"},
            {**proof, "credential": "not-a-credential"},
            {**proof, "trace": "output.trace"},
            {**proof, "xcresult": "output.xcresult"},
            {**proof, "modelCorrectness": "self-attested"},
            {**proof, "extra": True},
            {**proof, "checks": [*proof["checks"], {"id": "P-EXTRA-001", "status": "pass", "detail": "extra"}]},
        )
        for mutated in mutations:
            with self.subTest(mutated=next(key for key in mutated if key not in proof or mutated[key] != proof.get(key))):
                with self.assertRaises(ValueError):
                    runner.validate_evidence(mutated)

        unsafe_values = (
            "/private/synthetic/path",
            "/etc/passwd",
            r"C:\\Users\\synthetic\\path",
            r"D:\\build\\result.log",
            r"\\\\synthetic-server\\private-share",
            "api_key=synthetic-private-value",
            "token=ghp_abcdefghijklmnopqrstuvwxyz0123456789",
            "ghp_abcdefghijklmnopqrstuvwxyz0123456789",
            "Bearer synthetic-private-token-12345678",
            "-----BEGIN PRIVATE KEY-----",
            "self-attested model correctness",
            "synthetic.trace",
        )
        for unsafe in unsafe_values:
            with self.subTest(unsafe=unsafe):
                self.assertFalse(runner._safe_metadata({"safe": [{"value": unsafe}]}))
        self.assertFalse(runner._safe_metadata({"safe": {"rawPrompt": "nested"}}))

    def test_safety_proof_requires_the_recursive_content_scanner(self):
        with tempfile.TemporaryDirectory() as directory:
            proof = self._run_proof(Path(directory) / "proof.json")
        runner = self._runner()
        original = runner._safe_metadata
        runner._safe_metadata = lambda _value: True
        try:
            with self.assertRaises(ValueError):
                runner._verify_safety(proof)
        finally:
            runner._safe_metadata = original

    def test_evidence_validator_exact_enums_every_check_and_boundary(self):
        with tempfile.TemporaryDirectory() as directory:
            proof = self._run_proof(Path(directory) / "proof.json")
        runner = self._runner()
        for row_index, row in enumerate(proof["checks"]):
            mutated = deepcopy(proof)
            mutated["checks"][row_index]["boundaries"][0] = "D-INVENTED-001"
            with self.subTest(check=row["id"]), self.assertRaises(ValueError):
                runner.validate_evidence(mutated)

    def test_committed_evidence_matches_the_runner_and_documentation_keeps_the_boundaries(self):
        with tempfile.TemporaryDirectory() as directory:
            generated = Path(directory) / "proof.json"
            self._run_proof(generated)
            self.assertEqual(PROOF_EVIDENCE.read_bytes(), generated.read_bytes())

        required_text = {
            ROOT / "fixtures" / "dev-142" / "README.md": (
                "python3 fixtures/dev-142/proof_runner.py --output",
                "does not invoke Apple", "does not activate a host hook",
                "provider_usage_not_executed", "semantically validates", "96 arms",
            ),
            ROOT / "docs" / "architecture" / "apple-foundation-models-handoff-mvp-decision-record.md": (
                "diagnostic-condensation-v1", "48", "96 arms", "provider_usage_not_executed",
            ),
            ROOT / "plugins" / "apple-foundation-models-handoff" / "references" / "orchestration-patterns.md": (
                "PostToolUse", "condense_diagnostic_output", "at most one bridge attempt",
            ),
            ROOT / "plugins" / "apple-foundation-models-handoff" / "references" / "security-context-and-recovery.md": (
                "C0", "C1", "preserve the original result",
            ),
            ROOT / "plugins" / "apple-foundation-models-handoff" / "references" / "evaluation-and-observability.md": (
                "24", "48", "96 arms", "provider_usage_not_executed",
            ),
        }
        for path, fragments in required_text.items():
            text = path.read_text(encoding="utf-8")
            for fragment in fragments:
                with self.subTest(path=path, fragment=fragment):
                    self.assertIn(fragment, text)


if __name__ == "__main__":
    unittest.main()
