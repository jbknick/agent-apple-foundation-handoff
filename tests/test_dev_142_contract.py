import importlib.util
import json
import math
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "fixtures" / "dev-142" / "runtime_contract.py"
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


if __name__ == "__main__":
    unittest.main()
