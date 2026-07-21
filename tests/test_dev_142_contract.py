import importlib.util
import json
import math
import os
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
            "python3 -m build --sdist --wheel",
            "python3 -m mypy --strict --no-incremental Sources",
            "python3 -m ruff check --no-fix --output-format concise Sources",
        )
        for command in accepted:
            with self.subTest(command=command):
                self.assertIsNotNone(contract.parse_command(command, self.root))

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
            "bridge": self._bridge,
        }
        context.update(changes)
        return context

    def _bridge(self, request):
        result = canonical_result()
        result["commandClass"] = request["commandClass"]
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

        declined = (
            (canonical_request(), self._context(eventName="PreToolUse"), "tool_not_allowed"),
            (canonical_request(), self._context(command="echo nope"), "command_not_allowed"),
            ({**canonical_request(), "toolName": "Read"}, self._context(), "tool_not_allowed"),
            ({**canonical_request(), "inputBytes": 8191, "estimatedSavingsBytes": 4095}, self._context(), "input_below_minimum"),
            ({**canonical_request(), "fields": [dict(canonical_request()["fields"][0], classification="C2")]}, self._context(), "data_policy_denied"),
            ({**canonical_request(), "fields": [dict(canonical_request()["fields"][0], classification="C3")]}, self._context(), "data_policy_denied"),
            (canonical_request(), self._context(appleAvailable=False), "apple_unavailable"),
            (canonical_request(), self._context(localeSupported=False), "locale_unsupported"),
            (canonical_request(), self._context(occupiedTokens=6145), "context_budget_exceeded"),
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


if __name__ == "__main__":
    unittest.main()
