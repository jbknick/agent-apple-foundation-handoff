import json
import re
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests/fixtures/dev-136-codex-skill-cases.json"
EVIDENCE_PATH = ROOT / "docs/research/evidence/dev-136-codex-skill-tdd.json"

SKILLS = (
    "design-apple-foundation-models-handoff",
    "implement-apple-foundation-models-handoff",
    "review-apple-foundation-models-handoff",
    "debug-apple-foundation-models-handoff",
    "validate-apple-foundation-models-handoff",
)

ROUTER_ENUMS = {
    "domain": (
        "foundation_models_handoff",
        "out_of_domain",
        "ambiguous",
    ),
    "requestedOperation": (
        "design",
        "implement",
        "review",
        "debug",
        "validate",
        "compound_review_fix",
        "unspecified",
    ),
    "artifactState": (
        "absent",
        "proposal",
        "approved_contract",
        "implementation",
        "evidence_bundle",
        "unknown",
    ),
    "evidenceState": (
        "not_requested",
        "missing",
        "available",
        "failing",
        "blocked",
        "unknown",
    ),
}

COMMON_SECTIONS = (
    "Activation and Scope",
    "Pattern and Ownership",
    "Apple API Availability",
    "State and Lifecycle",
    "Trust and Model Boundaries",
    "Context Policy",
    "Tools Effects and Confirmation",
    "Failure Recovery and Fallback",
    "Verification and Evidence",
    "Limitations",
)

WORKFLOW_SECTIONS = {
    SKILLS[0]: (
        "Alternatives",
        "Decision Rationale",
        "Proposed Components",
        "Implementation and Test Plan",
    ),
    SKILLS[1]: (
        "Approved Decision",
        "Change Boundary",
        "Changed Paths",
        "Compilation and Regression Results",
    ),
    SKILLS[2]: ("Findings",),
    SKILLS[3]: (
        "Observed and Expected State",
        "First Divergence",
        "Root Cause",
        "Correction",
        "Regression Proof",
    ),
    SKILLS[4]: (
        "Layer Matrix",
        "Counts and Hashes",
        "Rubric Result",
        "Blockers and Skips",
        "Release Implication",
    ),
}

CASE_KEYS = {
    "id",
    "phase",
    "category",
    "skillUnderTest",
    "model",
    "sourcePrototypeIds",
    "prompt",
    "routerInput",
    "expectedActivation",
    "expectedClarificationKind",
    "expectedOutputContract",
    "adjacentDomains",
    "rubricContract",
}

POSITIVE_RUBRIC = (
    "result_envelope_complete",
    "selected_skill_named",
    "router_envelope_complete",
    "version_labels_complete",
    "common_sections_complete",
    "workflow_sections_complete",
    "evidence_vocabulary_complete",
)

NON_ACTIVATION_RUBRIC = (
    "no_activation_shape_complete",
    "architecture_result_absent",
)

CLARIFICATION_RUBRIC = (
    "one_clarification_only",
    "clarification_shape_complete",
    "architecture_result_absent",
)

FAILURE_CLASSES = {
    "missing_result_envelope",
    "missing_skill_selection",
    "missing_router_envelope",
    "missing_version_labels",
    "missing_common_sections",
    "missing_workflow_sections",
    "missing_evidence_status_vocabulary",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class SkillCaseFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = load_json(FIXTURE_PATH) if FIXTURE_PATH.is_file() else None

    def require_fixture(self) -> dict:
        if self.fixture is None:
            self.skipTest("fixture is created during the GREEN phase")
        return self.fixture

    def test_fixture_file_exists(self) -> None:
        self.assertTrue(
            FIXTURE_PATH.is_file(),
            "DEV-136 RED: the 25-case skill fixture does not exist yet",
        )

    def test_fixture_metadata_is_exact(self) -> None:
        fixture = self.require_fixture()
        self.assertEqual("1.0", fixture["schemaVersion"])
        self.assertEqual("DEV-136", fixture["sourceIssue"])
        self.assertEqual("approved_synthetic_skill_tdd_cases", fixture["evidenceKind"])
        self.assertEqual("gpt-5.6-sol", fixture["model"])
        self.assertEqual(25, fixture["caseCount"])
        self.assertEqual(
            {
                "prompts": "approved_synthetic",
                "expectedAnswersIncludedInPrompts": False,
                "liveHostResponses": "transient_not_committed",
                "offlineScorerOutputs": "approved_synthetic_or_redacted_only",
            },
            fixture["privacy"],
        )
        self.assertEqual(
            {key: list(values) for key, values in ROUTER_ENUMS.items()},
            fixture["routerEnums"],
        )
        self.assertEqual(list(COMMON_SECTIONS), fixture["commonOutputSections"])
        self.assertEqual(
            {key: list(values) for key, values in WORKFLOW_SECTIONS.items()},
            fixture["workflowSpecificSections"],
        )
        self.assertEqual(
            {
                "positive": list(POSITIVE_RUBRIC),
                "no_activation": list(NON_ACTIVATION_RUBRIC),
                "clarification": list(CLARIFICATION_RUBRIC),
            },
            fixture["rubricContracts"],
        )

    def test_fixture_has_exact_baseline_and_forward_coverage(self) -> None:
        cases = self.require_fixture()["cases"]
        self.assertEqual(25, len(cases))
        self.assertEqual(25, len({case["id"] for case in cases}))

        baselines = [case for case in cases if case["phase"] == "baseline"]
        forwards = [case for case in cases if case["phase"] == "forward"]
        self.assertEqual(5, len(baselines))
        self.assertEqual(20, len(forwards))
        self.assertEqual(set(SKILLS), {case["skillUnderTest"] for case in baselines})

        coverage = Counter(
            (case["skillUnderTest"], case["category"]) for case in forwards
        )
        self.assertEqual(
            Counter(
                (skill, category)
                for skill in SKILLS
                for category in ("positive", "negative", "ambiguous", "complete-output")
            ),
            coverage,
        )

    def test_every_case_has_exact_shape_and_normative_router_values(self) -> None:
        for case in self.require_fixture()["cases"]:
            with self.subTest(case=case["id"]):
                self.assertEqual(CASE_KEYS, set(case))
                self.assertRegex(case["id"], r"^DEV136-(BASE|FWD)-[A-Z]+-[0-9]{3}$")
                self.assertIn(case["phase"], {"baseline", "forward"})
                self.assertIn(
                    case["category"],
                    {"positive", "negative", "ambiguous", "complete-output"},
                )
                self.assertIn(case["skillUnderTest"], SKILLS)
                self.assertEqual("gpt-5.6-sol", case["model"])
                self.assertTrue(case["sourcePrototypeIds"])
                self.assertTrue(case["prompt"].strip())
                self.assertEqual(set(ROUTER_ENUMS), set(case["routerInput"]))
                for field, values in ROUTER_ENUMS.items():
                    self.assertIn(case["routerInput"][field], values)

    def test_prompts_do_not_leak_expected_answers_or_contract_tokens(self) -> None:
        hidden_tokens = (
            *SKILLS,
            "architectureSchemaVersion",
            "stateVersion",
            "policyVersion",
            "selectedSkill",
            "routerInput",
            *COMMON_SECTIONS,
        )
        for case in self.require_fixture()["cases"]:
            with self.subTest(case=case["id"]):
                prompt = case["prompt"]
                for token in hidden_tokens:
                    self.assertNotIn(token, prompt)
                self.assertNotRegex(prompt.lower(), r"expected[ _-]answer")

    def test_activation_output_and_rubric_expectations_match_category(self) -> None:
        for case in self.require_fixture()["cases"]:
            with self.subTest(case=case["id"]):
                category = case["category"]
                if case["phase"] == "baseline" or category in {
                    "positive",
                    "complete-output",
                }:
                    self.assertEqual(case["skillUnderTest"], case["expectedActivation"])
                    self.assertIsNone(case["expectedClarificationKind"])
                    self.assertEqual("common_plus_workflow", case["expectedOutputContract"])
                    self.assertEqual("positive", case["rubricContract"])
                elif category == "negative":
                    self.assertEqual("no_activation", case["expectedActivation"])
                    self.assertIsNone(case["expectedClarificationKind"])
                    self.assertEqual("none", case["expectedOutputContract"])
                    self.assertEqual("no_activation", case["rubricContract"])
                    self.assertEqual("out_of_domain", case["routerInput"]["domain"])
                else:
                    self.assertEqual("clarification_required", case["expectedActivation"])
                    self.assertIn(
                        case["expectedClarificationKind"], {"domain", "approved_contract"}
                    )
                    self.assertEqual("none", case["expectedOutputContract"])
                    self.assertEqual("clarification", case["rubricContract"])

    def test_negative_cases_cover_all_adjacent_domains(self) -> None:
        negative_cases = [
            case
            for case in self.require_fixture()["cases"]
            if case["phase"] == "forward" and case["category"] == "negative"
        ]
        covered = {
            adjacent
            for case in negative_cases
            for adjacent in case["adjacentDomains"]
        }
        self.assertEqual(
            {
                "app_intents",
                "apple_handoff_nsu_activity",
                "swift_actors",
                "generic_core_ml",
                "coding_session_handoff",
                "foundation_models_runtime_skills",
            },
            covered,
        )

    def test_review_and_fix_is_the_review_positive_ordering_case(self) -> None:
        matches = [
            case
            for case in self.require_fixture()["cases"]
            if case["phase"] == "forward"
            and case["skillUnderTest"] == "review-apple-foundation-models-handoff"
            and case["category"] == "positive"
        ]
        self.assertEqual(1, len(matches))
        case = matches[0]
        self.assertIn("DEV134-AMB-003", case["sourcePrototypeIds"])
        self.assertEqual("compound_review_fix", case["routerInput"]["requestedOperation"])
        self.assertEqual("review-apple-foundation-models-handoff", case["expectedActivation"])


class SkillBaselineEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.evidence = load_json(EVIDENCE_PATH) if EVIDENCE_PATH.is_file() else None
        cls.fixture = load_json(FIXTURE_PATH) if FIXTURE_PATH.is_file() else None

    def require_evidence(self) -> dict:
        if self.evidence is None:
            self.skipTest("baseline evidence is created after five fresh sessions")
        return self.evidence

    def test_evidence_file_exists(self) -> None:
        self.assertTrue(
            EVIDENCE_PATH.is_file(),
            "DEV-136 RED: normalized five-session baseline evidence does not exist yet",
        )

    def test_evidence_host_and_privacy_metadata_are_exact(self) -> None:
        evidence = self.require_evidence()
        self.assertEqual("1.0", evidence["schemaVersion"])
        self.assertEqual("DEV-136", evidence["sourceIssue"])
        self.assertEqual("codex_skill_red_baseline", evidence["evidenceKind"])
        self.assertEqual("complete", evidence["status"])
        self.assertEqual(
            {
                "name": "codex",
                "version": "0.144.5",
                "model": "gpt-5.6-sol",
                "modelSelection": "explicit_cli_argument",
                "sessionMode": "fresh_ephemeral_ignore_user_config",
                "productionPluginSkillsAvailable": False,
                "claudeInvoked": False,
            },
            evidence["host"],
        )
        self.assertEqual(
            {
                "rawPrompts": "transient",
                "rawResponses": "transient",
                "rawToolEvents": "transient",
                "committedHostEvidence": "normalized_metadata_and_sha256_only",
                "offlineScorerOutputs": "approved_synthetic_or_redacted_only",
            },
            evidence["privacy"],
        )
        self.assertEqual(
            [
                {
                    "attemptedModelId": "sol",
                    "status": "blocked",
                    "phase": "pre_response",
                    "reasonCode": "unsupported_chatgpt_account_model_alias",
                    "responseProduced": False,
                    "countedAsBaselineSession": False,
                    "capabilityEvidence": False,
                }
            ],
            evidence["preResponseBlockerObservations"],
        )

    def test_evidence_has_one_real_failing_baseline_per_skill(self) -> None:
        evidence = self.require_evidence()
        baselines = evidence["baselines"]
        self.assertEqual(5, evidence["summary"]["sessionCount"])
        self.assertEqual(5, evidence["summary"]["failedBaselineCount"])
        self.assertEqual(0, evidence["summary"]["passedBaselineCount"])
        self.assertEqual(5, len(baselines))
        self.assertEqual(set(SKILLS), {row["skillUnderTest"] for row in baselines})
        self.assertEqual(set(range(1, 6)), {row["sessionOrdinal"] for row in baselines})

        fixture_baselines = {
            case["id"]
            for case in self.fixture["cases"]
            if case["phase"] == "baseline"
        }
        self.assertEqual(fixture_baselines, {row["caseId"] for row in baselines})

        for row in baselines:
            with self.subTest(case=row["caseId"]):
                self.assertEqual(0, row["codexExitCode"])
                self.assertRegex(row["responseSha256"], r"^[0-9a-f]{64}$")
                self.assertGreater(row["responseBytes"], 0)
                self.assertGreaterEqual(row["toolEventCount"], 0)
                self.assertEqual("fail", row["rubricOutcome"]["verdict"])
                self.assertTrue(row["rubricOutcome"]["failedChecks"])
                self.assertTrue(row["observedFailureClasses"])
                self.assertLessEqual(
                    set(row["observedFailureClasses"]), FAILURE_CLASSES
                )

    def test_evidence_contains_no_raw_host_payload_fields_or_local_paths(self) -> None:
        evidence = self.require_evidence()
        forbidden_keys = {"prompt", "response", "transcript", "events", "command"}

        def walk(value):
            if isinstance(value, dict):
                for key, child in value.items():
                    self.assertNotIn(key, forbidden_keys)
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)

        walk(evidence)
        serialized = json.dumps(evidence, sort_keys=True)
        self.assertNotRegex(serialized, r"/Users/|/home/|[A-Za-z]:\\\\")
        self.assertNotRegex(serialized, r"sk-[A-Za-z0-9_-]{8,}")


if __name__ == "__main__":
    unittest.main()
