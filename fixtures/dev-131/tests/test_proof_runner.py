from __future__ import annotations

import copy
import hashlib
import importlib.util
import inspect
import json
import shutil
import tempfile
import unittest
from pathlib import Path


FIXTURES_ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = FIXTURES_ROOT / "proof_runner.py"

DOCUMENTED_CHECK_IDS = {
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


def load_runner():
    if not RUNNER_PATH.is_file():
        raise AssertionError(
            "proof_runner.py must exist before the executable contract can pass"
        )
    spec = importlib.util.spec_from_file_location("dev_131_proof_runner", RUNNER_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError("proof_runner.py must be importable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class OfflineEvaluationProofTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = load_runner()
        self.index = load_json(FIXTURES_ROOT / "index.json")

    def load_case(self, relative_path: str) -> dict:
        return load_json(FIXTURES_ROOT / relative_path)

    def test_case_results_use_only_documented_stable_check_ids(self) -> None:
        observed_ids: set[str] = set()
        for entry in self.index["cases"]:
            result = self.runner.evaluate_case(self.load_case(entry["path"]))
            observed_ids.update(check["id"] for check in result["checks"])
            observed_ids.update(result["violations"])
        self.assertTrue(observed_ids)
        self.assertLessEqual(observed_ids, DOCUMENTED_CHECK_IDS)

    def test_case_oracle_is_independent_and_exact(self) -> None:
        for entry in self.index["cases"]:
            with self.subTest(case=entry["id"]):
                case = self.load_case(entry["path"])
                self.assertFalse(
                    {"expected", "expectedStatus", "expectedViolations"} & case.keys()
                )
                result = self.runner.evaluate_case(case)
                self.assertEqual(entry["expectedStatus"], result["status"])
                self.assertEqual(
                    sorted(entry["expectedViolations"]), result["violations"]
                )

    def test_evaluate_case_accepts_only_the_case_input(self) -> None:
        signature = inspect.signature(self.runner.evaluate_case)
        self.assertEqual(["case"], list(signature.parameters))

    def test_valid_cases_cover_both_synthetic_workflow_identities(self) -> None:
        workflows = {
            self.load_case(entry["path"])["workflow"]
            for entry in self.index["cases"]
            if entry["expectedStatus"] == "pass"
        }
        self.assertEqual(
            {"minimal-route-owner", "recovery-aware-effect"}, workflows
        )

    def test_state_and_policy_versions_are_checked_independently(self) -> None:
        base = self.load_case("cases/valid/happy-path.json")
        stale_state = copy.deepcopy(base)
        stale_state["result"]["grant"]["stateVersion"] += 1
        stale_policy = copy.deepcopy(base)
        stale_policy["result"]["grant"]["policyVersion"] += 1

        self.assertEqual(
            ["D-GRANT-001"], self.runner.evaluate_case(stale_state)["violations"]
        )
        self.assertEqual(
            ["D-GRANT-001"], self.runner.evaluate_case(stale_policy)["violations"]
        )

    def test_phase_replay_and_reconciliation_invariants_are_enforced(self) -> None:
        valid_replay = self.load_case("cases/valid/replayed-effect.json")
        replay_command = copy.deepcopy(valid_replay)
        replay_command["result"]["executorCommands"].append(
            {
                "effectId": "effect-commit-1",
                "sourceObservation": "replay",
            }
        )

        self.assertEqual(
            "pass", self.runner.evaluate_case(valid_replay)["status"]
        )
        self.assertEqual(
            ["D-PHASE-001"],
            self.runner.evaluate_case(
                self.load_case("cases/invalid/invalid-phase.json")
            )["violations"],
        )
        self.assertEqual(
            ["D-EFFECT-002"],
            self.runner.evaluate_case(replay_command)["violations"],
        )
        self.assertEqual(
            ["D-EFFECT-002"],
            self.runner.evaluate_case(
                self.load_case("cases/invalid/retry-before-reconciliation.json")
            )["violations"],
        )

    def test_phase_rules_are_independent_and_recovery_order_is_binding(self) -> None:
        happy_path = self.load_case("cases/valid/happy-path.json")
        self_declared = copy.deepcopy(happy_path)
        self_declared["result"]["events"][0]["event"] = "execute"
        self_declared["policy"]["validPhaseEvents"]["stable"].append("execute")
        self.assertIn(
            "D-PHASE-001", self.runner.evaluate_case(self_declared)["violations"]
        )

        recovery = self.load_case("cases/valid/replayed-effect.json")
        erased_recovery = copy.deepcopy(recovery)
        erased_recovery["policy"]["allowedEdges"] = [
            ["stable", "proposed"],
            ["proposed", "executing"],
            ["executing", "complete"],
        ]
        erased_recovery["result"]["transitions"] = [
            {"from": "stable", "to": "proposed"},
            {"from": "proposed", "to": "executing"},
            {"from": "executing", "to": "complete"},
        ]
        erased_recovery["result"]["events"] = [
            {"phase": "stable", "event": "propose"},
            {"phase": "proposed", "event": "approve"},
            {"phase": "executing", "event": "execute"},
            {"phase": "complete", "event": "finalize"},
        ]
        self.assertIn(
            "D-PHASE-001",
            self.runner.evaluate_case(erased_recovery)["violations"],
        )

        missing_reconciliation = copy.deepcopy(recovery)
        del missing_reconciliation["result"]["events"][3]
        self.assertIn(
            "D-PHASE-001",
            self.runner.evaluate_case(missing_reconciliation)["violations"],
        )

        out_of_order = copy.deepcopy(recovery)
        out_of_order["result"]["events"][3], out_of_order["result"]["events"][4] = (
            out_of_order["result"]["events"][4],
            out_of_order["result"]["events"][3],
        )
        self.assertIn(
            "D-PHASE-001", self.runner.evaluate_case(out_of_order)["violations"]
        )

    def test_effect_proof_is_non_vacuous_unique_and_identity_based(self) -> None:
        replay = self.load_case("cases/valid/replayed-effect.json")
        self.assertEqual("pass", self.runner.evaluate_case(replay)["status"])

        empty = copy.deepcopy(replay)
        empty["result"]["effects"] = []
        empty["result"]["effectLedger"] = []
        empty["result"]["executorCommands"] = []
        empty_violations = self.runner.evaluate_case(empty)["violations"]
        self.assertIn("D-EFFECT-001", empty_violations)
        self.assertIn("D-EFFECT-002", empty_violations)

        duplicate_effect = copy.deepcopy(replay)
        duplicate_effect["result"]["effects"].append(
            copy.deepcopy(duplicate_effect["result"]["effects"][0])
        )
        self.assertIn(
            "D-EFFECT-001",
            self.runner.evaluate_case(duplicate_effect)["violations"],
        )

        duplicate_ledger = copy.deepcopy(replay)
        duplicate_ledger["result"]["effectLedger"].append(
            {"effectId": "effect-commit-1"}
        )
        self.assertIn(
            "D-EFFECT-001",
            self.runner.evaluate_case(duplicate_ledger)["violations"],
        )

        mismatched_observation = copy.deepcopy(replay)
        mismatched_observation["result"]["effects"][0]["observations"][1][
            "effectId"
        ] = "effect-other"
        self.assertIn(
            "D-EFFECT-001",
            self.runner.evaluate_case(mismatched_observation)["violations"],
        )

        replay_command = copy.deepcopy(replay)
        replay_command["result"]["executorCommands"].append(
            {"effectId": "effect-commit-1", "sourceObservation": "replay"}
        )
        self.assertIn(
            "D-EFFECT-002",
            self.runner.evaluate_case(replay_command)["violations"],
        )

    def test_malformed_normalized_shapes_return_only_schema_failure(self) -> None:
        happy_path = self.load_case("cases/valid/happy-path.json")
        mutations = []

        transitions_string = copy.deepcopy(happy_path)
        transitions_string["result"]["transitions"] = "not-a-list"
        mutations.append(transitions_string)

        missing_effect_ledger = copy.deepcopy(happy_path)
        del missing_effect_ledger["result"]["effectLedger"]
        mutations.append(missing_effect_ledger)

        invalid_context_items = copy.deepcopy(happy_path)
        invalid_context_items["policy"]["contextPolicy"]["required"] = "request"
        mutations.append(invalid_context_items)

        malformed_edge = copy.deepcopy(happy_path)
        malformed_edge["policy"]["allowedEdges"] = [["stable"]]
        mutations.append(malformed_edge)

        for case in mutations:
            with self.subTest(case=case.get("caseId")):
                result = self.runner.evaluate_case(case)
                self.assertEqual("fail", result["status"])
                self.assertEqual(["D-SCHEMA-001"], result["violations"])
                self.assertEqual(
                    [{"id": "D-SCHEMA-001", "status": "fail"}],
                    result["checks"],
                )

    def test_semantic_quality_is_gated_only_by_the_seven_dimension_rubric(self) -> None:
        response_path = (
            FIXTURES_ROOT
            / "example-evidence/rubric/architecture-response.synthetic.md"
        )
        valid = load_json(
            FIXTURES_ROOT / "example-evidence/rubric/assessment.json"
        )
        invalid = load_json(
            FIXTURES_ROOT / "example-evidence/rubric/assessment.invalid.json"
        )

        valid_result = self.runner.validate_rubric(response_path, valid)
        invalid_result = self.runner.validate_rubric(response_path, invalid)
        self.assertEqual(RUBRIC_DIMENSIONS, set(valid_result["scores"]))
        self.assertEqual("pass", valid_result["status"])
        self.assertEqual("fail", invalid_result["status"])
        self.assertEqual(["D-RUBRIC-001"], invalid_result["violations"])

        deterministic = self.runner.evaluate_case(
            self.load_case("cases/valid/happy-path.json")
        )
        self.assertNotIn("semanticScore", deterministic)
        self.assertNotIn("D-RUBRIC-001", [c["id"] for c in deterministic["checks"]])

    def test_valid_evidence_bundle_passes_allowlist_and_hash_checks(self) -> None:
        result = self.runner.validate_evidence_bundle(
            FIXTURES_ROOT / "example-evidence"
        )
        self.assertEqual("pass", result["status"])
        self.assertEqual([], result["violations"])
        self.assertGreater(result["verifiedFileCount"], 0)

    def test_unsafe_manifest_and_invalid_critical_rubric_score_are_rejected(self) -> None:
        unsafe_case = self.runner.evaluate_case(
            self.load_case("cases/invalid/unsafe-evidence-manifest.json")
        )
        self.assertEqual(["D-EVIDENCE-001"], unsafe_case["violations"])

        with tempfile.TemporaryDirectory() as temp_dir:
            bundle = Path(temp_dir) / "bundle"
            shutil.copytree(FIXTURES_ROOT / "example-evidence", bundle)
            manifest_path = bundle / "manifest.json"
            manifest = load_json(manifest_path)
            manifest["files"][0]["path"] = "raw-response.txt"
            manifest_path.write_text(
                json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
            )
            result = self.runner.validate_evidence_bundle(bundle)
        self.assertEqual("fail", result["status"])
        self.assertEqual(["D-EVIDENCE-001"], result["violations"])

        response_path = (
            FIXTURES_ROOT
            / "example-evidence/rubric/architecture-response.synthetic.md"
        )
        invalid = load_json(
            FIXTURES_ROOT / "example-evidence/rubric/assessment.invalid.json"
        )
        rubric_result = self.runner.validate_rubric(response_path, invalid)
        self.assertEqual(["D-RUBRIC-001"], rubric_result["violations"])

    def test_rehashed_prohibited_content_is_rejected_for_every_allowlisted_file(self) -> None:
        source = FIXTURES_ROOT / "example-evidence"
        manifest = load_json(source / "manifest.json")
        allowlisted_paths = [item["path"] for item in manifest["files"]]

        for relative_path in allowlisted_paths:
            with self.subTest(path=relative_path), tempfile.TemporaryDirectory() as temp_dir:
                bundle = Path(temp_dir) / "bundle"
                shutil.copytree(source, bundle)
                target = bundle / relative_path
                if target.suffix == ".md":
                    target.write_text(
                        target.read_text(encoding="utf-8")
                        + "\n-----BEGIN PRIVATE KEY-----\nsynthetic-prohibited\n",
                        encoding="utf-8",
                    )
                elif target.suffix == ".json":
                    data = load_json(target)
                    data["accessToken"] = "synthetic-prohibited"
                    target.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
                else:
                    target.write_text(
                        target.read_text(encoding="utf-8")
                        + '{"accessToken":"synthetic-prohibited"}\n',
                        encoding="utf-8",
                    )

                copied_manifest_path = bundle / "manifest.json"
                copied_manifest = load_json(copied_manifest_path)
                for item in copied_manifest["files"]:
                    if item["path"] == relative_path:
                        item["sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
                copied_manifest_path.write_text(
                    json.dumps(copied_manifest, indent=2) + "\n", encoding="utf-8"
                )

                result = self.runner.validate_evidence_bundle(bundle)
                self.assertEqual("fail", result["status"])
                self.assertEqual(["D-EVIDENCE-001"], result["violations"])

    def test_zero_denominator_metrics_are_not_applicable(self) -> None:
        result = self.runner.run(FIXTURES_ROOT)
        metric = result["metrics"]["optionalAppleEvaluationPassRate"]
        self.assertEqual(0, metric["denominator"])
        self.assertEqual("not_applicable", metric["status"])
        self.assertIsNone(metric["value"])
        self.assertNotEqual(0, metric["value"])

    def test_cli_shape_reports_exact_oracle_rubric_and_evidence_status(self) -> None:
        result = self.runner.run(FIXTURES_ROOT)
        self.assertEqual("pass", result["status"])
        self.assertTrue(all(case["oracleMatch"] for case in result["cases"]))
        self.assertEqual("pass", result["rubric"]["status"])
        self.assertEqual("pass", result["evidence"]["status"])


if __name__ == "__main__":
    unittest.main()
