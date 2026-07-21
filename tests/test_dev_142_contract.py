import importlib.util
import json
import math
from pathlib import Path
import re
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "fixtures" / "dev-142" / "runtime_contract.py"
SCHEMAS = ROOT / "schemas"
SPEC = importlib.util.spec_from_file_location("dev142_runtime_contract", CONTRACT_PATH)
contract = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(contract)


def canonical_request():
    return {
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
        "inputBytes": 8192,
        "estimatedSavingsBytes": 4096,
        "fields": [
            {
                "name": "message",
                "value": "synthetic test failure",
                "origin": "trustedLocal",
                "classification": "C1",
                "purpose": "diagnostic_condensation",
                "destination": "apple_on_device",
                "retention": "ephemeral",
                "redacted": False,
            }
        ],
    }


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
            "summary": "1 test failed",
            "diagnostics": [],
            "warningCount": 0,
            "omittedWarningCount": 0,
        }
    else:
        result["reasonCode"] = "generation_declined"
    return result


def canonical_benchmark():
    return {
        "schemaVersion": 1,
        "policyVersion": "diagnostic-condensation-v1",
        "kind": "corpus",
        "corpusVersion": "dev-142-v1",
        "corpusSha256": "b" * 64,
        "cases": [
            {
                "id": "test-success-01",
                "commandClass": "test",
                "commandForm": "swift test",
                "classification": "C0",
                "renderedSha256": "c" * 64,
                "expected": {
                    "exitStatus": 0,
                    "interrupted": False,
                    "warningCount": 0,
                    "requiredDiagnosticIDs": [],
                    "failedTestIDs": [],
                },
            }
        ],
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
                    if type(path) is not str or not path or path.startswith("/") or "\x00" in path:
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
        evidence = {
            "schemaVersion": 1,
            "policyVersion": "diagnostic-condensation-v1",
            "kind": "evidence",
            "arms": [
                {
                    "id": "arm-1",
                    "pairID": "pair-1",
                    "arm": "pluginOff",
                    "provider": "openai-responses-usage-v1",
                    "inputTokens": 10,
                    "cachedInputTokens": 0,
                    "outputTokens": 5,
                    "reasoningTokens": 0,
                    "totalParentModelTokens": 15,
                    "parentTurns": 1,
                    "appleAttempts": 0,
                    "replacements": 0,
                    "declines": 0,
                    "fallbacks": 0,
                    "latencyMilliseconds": 1,
                    "correct": True,
                }
            ],
            "pairs": [{"id": "pair-1", "status": "valid", "reduction": 0.1}],
            "release": {
                "status": "blocked",
                "validRequiredPairs": 0,
                "blockedRequiredPairs": 48,
                "medianReduction": None,
                "correctnessRegressions": 0,
                "additionalParentModelTurns": 0,
            },
        }
        self.assertEqual(contract.validate_benchmark(evidence), evidence)
        evidence["pairs"][0]["reduction"] = math.nan
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


class Dev142SchemaParityTests(unittest.TestCase):
    def _schema(self, name):
        return json.loads((SCHEMAS / name).read_text())

    def test_request_schema_matches_field_value_and_status_contract(self):
        schema = self._schema("dev-142-request.schema.json")
        accepted = canonical_request()
        line = dict(accepted["fields"][0], name="line", value=1)
        accepted["fields"] = [line]
        self.assertEqual(contract.validate_request(accepted), accepted)
        self.assertTrue(schema_accepts(schema, accepted))
        rejected = dict(accepted, fields=[dict(line, value="1")])
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
        evidence = {
            "schemaVersion": 1, "policyVersion": contract.Policy.POLICY_VERSION, "kind": "evidence",
            "arms": [{
                "id": "arm-1", "pairID": "pair-1", "arm": "pluginOff", "provider": "openai-responses-usage-v1",
                "inputTokens": 1, "cachedInputTokens": 0, "outputTokens": 1, "reasoningTokens": 0,
                "totalParentModelTokens": 2, "parentTurns": 1, "appleAttempts": 0, "replacements": 0,
                "declines": 0, "fallbacks": 0, "latencyMilliseconds": 1, "correct": True,
            }],
            "pairs": [{"id": "pair-1", "status": "blocked", "reduction": None}],
            "release": {"status": "blocked", "validRequiredPairs": 0, "blockedRequiredPairs": 1, "medianReduction": None, "correctnessRegressions": 0, "additionalParentModelTurns": 0},
        }
        self.assertEqual(contract.validate_benchmark(evidence), evidence)
        self.assertTrue(schema_accepts(schema, evidence))
        blocked_reduction = {**evidence, "pairs": [{"id": "pair-1", "status": "blocked", "reduction": 0.0}]}
        with self.assertRaises(contract.ContractError):
            contract.validate_benchmark(blocked_reduction)
        self.assertFalse(schema_accepts(schema, blocked_reduction))
        plugin_off_attempt = {**evidence, "arms": [dict(evidence["arms"][0], appleAttempts=1)]}
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
        for rejected in (duplicate_result, warning_result):
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
        arm = {
            "id": "arm-1", "pairID": "pair-1", "arm": "pluginOff", "provider": "openai-responses-usage-v1",
            "inputTokens": 1, "cachedInputTokens": 0, "outputTokens": 1, "reasoningTokens": 0,
            "totalParentModelTokens": 2, "parentTurns": 1, "appleAttempts": 0, "replacements": 0,
            "declines": 0, "fallbacks": 0, "latencyMilliseconds": 1, "correct": True,
        }
        evidence = {
            "schemaVersion": 1, "policyVersion": contract.Policy.POLICY_VERSION, "kind": "evidence",
            "arms": [arm], "pairs": [{"id": "pair-1", "status": "blocked", "reduction": None}],
            "release": {"status": "blocked", "validRequiredPairs": 0, "blockedRequiredPairs": 1, "medianReduction": None, "correctnessRegressions": 0, "additionalParentModelTurns": 0},
        }
        duplicate_arm = {**evidence, "arms": [arm, dict(arm, pairID="pair-2")]}
        duplicate_pair = {**evidence, "pairs": [evidence["pairs"][0], {"id": "pair-1", "status": "valid", "reduction": None}]}
        for rejected in (duplicate_arm, duplicate_pair):
            with self.subTest(evidence=rejected), self.assertRaises(contract.ContractError):
                contract.validate_benchmark(rejected)
            self.assertFalse(schema_accepts(benchmark_schema, rejected))


if __name__ == "__main__":
    unittest.main()
