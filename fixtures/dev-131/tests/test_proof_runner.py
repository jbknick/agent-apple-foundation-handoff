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

    def test_embedded_oracle_fields_are_schema_failures(self) -> None:
        happy_path = self.load_case("cases/valid/happy-path.json")
        embedded_fields = {
            "expected": "pass",
            "expectedStatus": "pass",
            "expectedViolations": [],
        }
        for field, value in embedded_fields.items():
            with self.subTest(field=field):
                case = copy.deepcopy(happy_path)
                case[field] = value
                result = self.runner.evaluate_case(case)
                self.assertEqual(["D-SCHEMA-001"], result["violations"])
                self.assertEqual(
                    [{"id": "D-SCHEMA-001", "status": "fail"}],
                    result["checks"],
                )

    def test_runner_requires_complete_unique_readable_executed_corpus(self) -> None:
        source = FIXTURES_ROOT
        mutations = (
            "missing-index-entry",
            "duplicate-index-entry",
            "path-mismatch",
            "unreadable-case",
            "unexecuted-case",
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temp_dir:
                fixtures = Path(temp_dir) / "fixtures"
                shutil.copytree(source, fixtures)
                index_path = fixtures / "index.json"
                index = load_json(index_path)
                if mutation == "missing-index-entry":
                    index["cases"] = [
                        entry
                        for entry in index["cases"]
                        if entry["id"] != "invalid-phase"
                    ]
                elif mutation == "duplicate-index-entry":
                    index["cases"].append(copy.deepcopy(index["cases"][0]))
                elif mutation == "path-mismatch":
                    budget = next(
                        entry
                        for entry in index["cases"]
                        if entry["id"] == "transition-budget-exhausted"
                    )
                    budget["path"] = "cases/invalid/transition-loop.json"
                elif mutation == "unreadable-case":
                    (fixtures / "cases/invalid/invalid-phase.json").unlink()
                elif mutation == "unexecuted-case":
                    (fixtures / "cases/invalid/invalid-phase.json").write_text(
                        "{not-json}\n", encoding="utf-8"
                    )
                index_path.write_text(
                    json.dumps(index, indent=2) + "\n", encoding="utf-8"
                )

                result = self.runner.run(fixtures)
                self.assertEqual("fail", result["status"])
                self.assertEqual("fail", result["corpus"]["status"])

    def test_runner_has_no_second_expected_outcome_oracle(self) -> None:
        source = RUNNER_PATH.read_text(encoding="utf-8")
        self.assertNotIn("EXPECTED_REJECTIONS", source)

    def test_transition_budget_exhaustion_is_distinct_from_a_loop(self) -> None:
        budget_entries = [
            entry
            for entry in self.index["cases"]
            if entry["id"] == "transition-budget-exhausted"
        ]
        self.assertEqual(1, len(budget_entries))
        if not budget_entries:
            return
        entry = budget_entries[0]
        self.assertNotEqual("cases/invalid/transition-loop.json", entry["path"])
        case = self.load_case(entry["path"])
        self.assertEqual(
            len(case["result"]["transitions"]) - 1,
            case["policy"]["transitionBudget"],
        )
        self.assertEqual(
            ["D-TRANSITION-001"],
            self.runner.evaluate_case(case)["violations"],
        )
        checks = load_json(FIXTURES_ROOT / "example-evidence/checks.json")
        self.assertEqual(
            ["D-TRANSITION-001"],
            checks["exactRejections"]["transition-budget-exhausted"],
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

        undeclared_context = copy.deepcopy(base)
        undeclared_context["result"]["context"]["included"].append(
            "undeclared_private_notes"
        )
        self.assertEqual(
            ["D-CONTEXT-001"],
            self.runner.evaluate_case(undeclared_context)["violations"],
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
        for outcome in ("still_unknown", "confirmed_committed"):
            with self.subTest(reconciliation_outcome=outcome):
                unsafe_retry = copy.deepcopy(valid_replay)
                unsafe_retry["result"]["effects"][0]["observations"][2][
                    "outcome"
                ] = outcome
                self.assertEqual(
                    ["D-EFFECT-002"],
                    self.runner.evaluate_case(unsafe_retry)["violations"],
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

        nested_locations = (
            ("policy", "route"),
            ("policy", "contextPolicy"),
            ("result", "responses", 0),
            ("result", "transitions", 0),
            ("result", "toolCalls", 0),
            ("result", "context"),
            ("result", "grant"),
            ("result", "events", 0),
            ("result", "effects", 0),
            ("result", "effects", 0, "observations", 0),
            ("result", "effectLedger", 0),
            ("result", "executorCommands", 0),
            ("result", "evidence"),
        )
        for location in nested_locations:
            nested_extra = copy.deepcopy(happy_path)
            target = nested_extra
            for key in location:
                target = target[key]
            target["unexpectedField"] = "synthetic-extra"
            mutations.append(nested_extra)

        result_extra = copy.deepcopy(happy_path)
        result_extra["result"]["oracle"] = "synthetic-extra"
        mutations.append(result_extra)

        nested_raw = copy.deepcopy(happy_path)
        nested_raw["policy"]["route"]["rawResponse"] = "synthetic-extra"
        mutations.append(nested_raw)

        for case in mutations:
            with self.subTest(case=case.get("caseId")):
                result = self.runner.evaluate_case(case)
                self.assertEqual("fail", result["status"])
                self.assertEqual(["D-SCHEMA-001"], result["violations"])
                self.assertEqual(
                    [{"id": "D-SCHEMA-001", "status": "fail"}],
                    result["checks"],
                )

    def test_case_evidence_paths_are_non_empty_normalized_and_safe(self) -> None:
        happy_path = self.load_case("cases/valid/happy-path.json")
        mutations = {
            "empty": [],
            "traversal": ["safe/../../secret.txt"],
            "raw-prompt": ["raw-prompt.txt"],
            "safe-but-undeclared": ["safe-but-undeclared.json"],
        }
        for name, included_paths in mutations.items():
            with self.subTest(mutation=name):
                case = copy.deepcopy(happy_path)
                case["result"]["evidence"]["includedPaths"] = included_paths
                self.assertEqual(
                    ["D-EVIDENCE-001"],
                    self.runner.evaluate_case(case)["violations"],
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

    def test_boolean_rubric_score_is_rejected(self) -> None:
        response_path = (
            FIXTURES_ROOT
            / "example-evidence/rubric/architecture-response.synthetic.md"
        )
        valid = load_json(FIXTURES_ROOT / "example-evidence/rubric/assessment.json")

        boolean_score = copy.deepcopy(valid)
        boolean_score["dimensions"][0]["score"] = True
        boolean_score["meanScore"] = 3.29
        self.assertEqual(
            ["D-RUBRIC-001"],
            self.runner.validate_rubric(response_path, boolean_score)["violations"],
        )

    def test_malformed_rubric_thresholds_return_stable_failure(self) -> None:
        response_path = (
            FIXTURES_ROOT
            / "example-evidence/rubric/architecture-response.synthetic.md"
        )
        valid = load_json(FIXTURES_ROOT / "example-evidence/rubric/assessment.json")
        malformed_thresholds = copy.deepcopy(valid)
        malformed_thresholds["thresholds"] = "not-an-object"
        self.assertEqual(
            ["D-RUBRIC-001"],
            self.runner.validate_rubric(response_path, malformed_thresholds)[
                "violations"
            ],
        )

    def test_missing_rubric_stimulus_returns_stable_failure(self) -> None:
        response_path = (
            FIXTURES_ROOT
            / "example-evidence/rubric/architecture-response.synthetic.md"
        )
        valid = load_json(FIXTURES_ROOT / "example-evidence/rubric/assessment.json")
        missing_response = response_path.with_name("missing-stimulus.md")
        self.assertFalse(missing_response.exists())
        self.assertEqual(
            ["D-RUBRIC-001"],
            self.runner.validate_rubric(missing_response, valid)["violations"],
        )

    def test_duplicate_critical_rubric_dimension_is_rejected(self) -> None:
        response_path = (
            FIXTURES_ROOT
            / "example-evidence/rubric/architecture-response.synthetic.md"
        )
        assessment = load_json(
            FIXTURES_ROOT / "example-evidence/rubric/assessment.json"
        )
        assessment["thresholds"]["criticalDimensions"].append(
            "security_policy_completeness"
        )
        result = self.runner.validate_rubric(response_path, assessment)
        self.assertEqual(["D-RUBRIC-001"], result["violations"])

    def test_valid_evidence_bundle_passes_allowlist_and_hash_checks(self) -> None:
        source = FIXTURES_ROOT / "example-evidence"
        result = self.runner.validate_evidence_bundle(source)
        self.assertEqual("pass", result["status"])
        self.assertEqual([], result["violations"])
        self.assertGreater(result["verifiedFileCount"], 0)

        with tempfile.TemporaryDirectory() as temp_dir:
            bundle = Path(temp_dir) / "bundle"
            shutil.copytree(source, bundle)
            checks_path = bundle / "checks.json"
            checks = load_json(checks_path)
            checks["runtimeCostEvidence"]["releaseFloor"][
                "minimumMedianTotalParentModelTokenReduction"
            ] = 0.0
            checks_path.write_text(
                json.dumps(checks, indent=2) + "\n", encoding="utf-8"
            )
            manifest_path = bundle / "manifest.json"
            manifest = load_json(manifest_path)
            for item in manifest["files"]:
                if item["path"] == "checks.json":
                    item["sha256"] = hashlib.sha256(
                        checks_path.read_bytes()
                    ).hexdigest()
            manifest_path.write_text(
                json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
            )
            invalid = self.runner.validate_evidence_bundle(bundle)
        self.assertEqual(["D-EVIDENCE-001"], invalid["violations"])

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

    def test_manifest_run_and_commit_metadata_are_required(self) -> None:
        source = FIXTURES_ROOT / "example-evidence"

        with tempfile.TemporaryDirectory() as temp_dir:
            bundle = Path(temp_dir) / "bundle"
            shutil.copytree(source, bundle)
            manifest_path = bundle / "manifest.json"
            manifest = load_json(manifest_path)
            del manifest["runId"]
            del manifest["commit"]
            manifest_path.write_text(
                json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
            )
            result = self.runner.validate_evidence_bundle(bundle)
            self.assertEqual(["D-EVIDENCE-001"], result["violations"])

    def test_rehashed_undeclared_environment_field_is_rejected(self) -> None:
        source = FIXTURES_ROOT / "example-evidence"

        with tempfile.TemporaryDirectory() as temp_dir:
            bundle = Path(temp_dir) / "bundle"
            shutil.copytree(source, bundle)
            environment_path = bundle / "environment.json"
            environment = load_json(environment_path)
            environment["fullName"] = "Synthetic Person"
            environment_path.write_text(
                json.dumps(environment, indent=2) + "\n", encoding="utf-8"
            )
            manifest_path = bundle / "manifest.json"
            manifest = load_json(manifest_path)
            for item in manifest["files"]:
                if item["path"] == "environment.json":
                    item["sha256"] = hashlib.sha256(
                        environment_path.read_bytes()
                    ).hexdigest()
            manifest_path.write_text(
                json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
            )
            result = self.runner.validate_evidence_bundle(bundle)
            self.assertEqual(["D-EVIDENCE-001"], result["violations"])

    def test_zero_denominator_metrics_are_not_applicable(self) -> None:
        result = self.runner.run(FIXTURES_ROOT)
        metric = result["metrics"]["optionalAppleEvaluationPassRate"]
        self.assertEqual(0, metric["denominator"])
        self.assertEqual("not_applicable", metric["status"])
        self.assertIsNone(metric["value"])

    def test_cli_shape_reports_exact_oracle_rubric_and_evidence_status(self) -> None:
        result = self.runner.run(FIXTURES_ROOT)
        self.assertEqual("pass", result["status"])
        self.assertTrue(all(case["oracleMatch"] for case in result["cases"]))
        self.assertEqual("pass", result["rubric"]["status"])
        self.assertEqual("pass", result["evidence"]["status"])
        cost = result["metrics"]["runtimeCostEvidence"]
        self.assertEqual("blocked", cost["status"])
        self.assertEqual(0, cost["comparison"]["eligibleWorkflowCount"])
        self.assertIsNone(
            cost["comparison"]["medianTotalParentModelTokenReduction"]
        )
        self.assertEqual(
            {
                "minimumMedianTotalParentModelTokenReduction": 0.1,
                "maximumCorrectnessRegressions": 0,
                "maximumExtraParentModelTurns": 0,
            },
            cost["releaseFloor"],
        )
        self.assertTrue(all(value is None for value in cost["measurements"].values()))


if __name__ == "__main__":
    unittest.main()
