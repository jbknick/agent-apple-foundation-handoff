import copy
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests/fixtures/dev-136-codex-skill-cases.json"
EVIDENCE_PATH = ROOT / "docs/research/evidence/dev-136-codex-skill-tdd.json"
PROTOTYPE_PATH = ROOT / "docs/research/evidence/dev-134-activation-prototype.json"
RUNNER_PATH = ROOT / "tests/e2e/codex_skill_forward_tests.py"

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

FAILURE_CLASS_BY_CHECK = {
    "result_envelope_complete": "missing_result_envelope",
    "selected_skill_named": "missing_skill_selection",
    "router_envelope_complete": "missing_router_envelope",
    "version_labels_complete": "missing_version_labels",
    "common_sections_complete": "missing_common_sections",
    "workflow_sections_complete": "missing_workflow_sections",
    "evidence_vocabulary_complete": "missing_evidence_status_vocabulary",
}

FAILURE_CLASSES = set(FAILURE_CLASS_BY_CHECK.values())

EXPECTED_CASES = (
    ("DEV136-BASE-DESIGN-001", SKILLS[0], "baseline", "positive", ("DEV134-POS-001",)),
    ("DEV136-BASE-IMPLEMENT-001", SKILLS[1], "baseline", "positive", ("DEV134-POS-003",)),
    ("DEV136-BASE-REVIEW-001", SKILLS[2], "baseline", "positive", ("DEV134-POS-002",)),
    ("DEV136-BASE-DEBUG-001", SKILLS[3], "baseline", "positive", ("DEV134-POS-004",)),
    ("DEV136-BASE-VALIDATE-001", SKILLS[4], "baseline", "positive", ("DEV134-POS-005",)),
    ("DEV136-FWD-DESIGN-001", SKILLS[0], "forward", "positive", ("DEV134-POS-006",)),
    ("DEV136-FWD-DESIGN-002", SKILLS[0], "forward", "negative", ("DEV134-NEG-001",)),
    ("DEV136-FWD-DESIGN-003", SKILLS[0], "forward", "ambiguous", ("DEV134-AMB-001",)),
    ("DEV136-FWD-DESIGN-004", SKILLS[0], "forward", "complete-output", ("DEV134-POS-001",)),
    ("DEV136-FWD-IMPLEMENT-001", SKILLS[1], "forward", "positive", ("DEV134-POS-003",)),
    ("DEV136-FWD-IMPLEMENT-002", SKILLS[1], "forward", "negative", ("DEV134-NEG-003",)),
    ("DEV136-FWD-IMPLEMENT-003", SKILLS[1], "forward", "ambiguous", ("DEV134-AMB-002",)),
    ("DEV136-FWD-IMPLEMENT-004", SKILLS[1], "forward", "complete-output", ("DEV134-POS-003",)),
    ("DEV136-FWD-REVIEW-001", SKILLS[2], "forward", "positive", ("DEV134-AMB-003", "DEV134-POS-002")),
    ("DEV136-FWD-REVIEW-002", SKILLS[2], "forward", "negative", ("DEV134-NEG-002",)),
    ("DEV136-FWD-REVIEW-003", SKILLS[2], "forward", "ambiguous", ("DEV134-AMB-001",)),
    ("DEV136-FWD-REVIEW-004", SKILLS[2], "forward", "complete-output", ("DEV134-POS-002",)),
    ("DEV136-FWD-DEBUG-001", SKILLS[3], "forward", "positive", ("DEV134-POS-004",)),
    ("DEV136-FWD-DEBUG-002", SKILLS[3], "forward", "negative", ("DEV134-NEG-005",)),
    ("DEV136-FWD-DEBUG-003", SKILLS[3], "forward", "ambiguous", ("DEV134-AMB-001",)),
    ("DEV136-FWD-DEBUG-004", SKILLS[3], "forward", "complete-output", ("DEV134-POS-004",)),
    ("DEV136-FWD-VALIDATE-001", SKILLS[4], "forward", "positive", ("DEV134-POS-005",)),
    ("DEV136-FWD-VALIDATE-002", SKILLS[4], "forward", "negative", ("DEV134-NEG-004", "DEV134-NEG-006")),
    ("DEV136-FWD-VALIDATE-003", SKILLS[4], "forward", "ambiguous", ("DEV134-AMB-001",)),
    ("DEV136-FWD-VALIDATE-004", SKILLS[4], "forward", "complete-output", ("DEV134-POS-005",)),
)

FIXTURE_KEYS = {
    "schemaVersion",
    "sourceIssue",
    "evidenceKind",
    "model",
    "caseCount",
    "privacy",
    "routerEnums",
    "commonOutputSections",
    "workflowSpecificSections",
    "rubricContracts",
    "cases",
}

EVIDENCE_KEYS = {
    "schemaVersion",
    "sourceIssue",
    "evidenceKind",
    "status",
    "initialRepositoryHeadAtCapture",
    "caseContract",
    "fixtureSha256",
    "host",
    "privacy",
    "preResponseBlockerObservations",
    "summary",
    "baselines",
    "limitations",
}

BASELINE_ROW_KEYS = {
    "caseId",
    "skillUnderTest",
    "sessionOrdinal",
    "repositoryHeadAtCapture",
    "promptSha256",
    "rubricContractSha256",
    "codexExitCode",
    "responseSha256",
    "responseBytes",
    "toolEventCount",
    "rubricOutcome",
    "observedFailureClasses",
}

INITIAL_CAPTURE_HEAD = "fbe50c1852778f72ec30ffe4c60614d2b4a9c206"
REVIEW_RECAPTURE_HEAD = "9b2c3990af8d56dfb57775fc6e7f7994f581a04f"

APPROVED_LIMITATIONS = (
    "The five responses were scored only as no-skill RED controls and are not capability evidence.",
    "Raw prompts, responses, and tool events were deleted after normalization.",
    "Claude was not invoked in this wave.",
)

APPROVED_PROMPT_SHA256_BY_CASE = {
    "DEV136-BASE-DESIGN-001": "cdc8b25f1db7d95f85e37ba6a916f5ccb2b4312726c1f032d55423747e268833",
    "DEV136-BASE-IMPLEMENT-001": "0f602d0a9eb90d619728be4a99d8590c1583020b3a7d56206e34d423bd7914a1",
    "DEV136-BASE-REVIEW-001": "53c421f4ef049225ca052c393f85c4f5196d35376ce49f92bb4781ce3c7c55fa",
    "DEV136-BASE-DEBUG-001": "5aa0f73c4d9528249022718abd6237840d8023d40ec2869029f188d1a0544de4",
    "DEV136-BASE-VALIDATE-001": "19f364ecf794839bdcebd4e5b2de5f573126080106361b8ed8b9e21584a43faf",
    "DEV136-FWD-DESIGN-001": "6a97d3b4c474d08314907fe17a6a7ee95377b4d6cdad563bbe540467654ad72a",
    "DEV136-FWD-DESIGN-002": "7258d92acab4ce7ccf4cbb019f9bf59afa68123556887091b9c71da4b7837ad3",
    "DEV136-FWD-DESIGN-003": "d8d239e830b12c9883fb7596024fd2c5d932dee325d3d0383846ed6e86846adb",
    "DEV136-FWD-DESIGN-004": "1f3673bb927808ccb7967e074883352d1bc37f115909e769d9ce45e38fe2573d",
    "DEV136-FWD-IMPLEMENT-001": "bc03f6ad9d9332ef02f769b34cb58f92a19cc30774e7b554f54280cd31a3ee56",
    "DEV136-FWD-IMPLEMENT-002": "bbba3d3c685681496317c80fd646afc74b0b62cdd1f214b3626cfb9b95c99f7c",
    "DEV136-FWD-IMPLEMENT-003": "6b09de346ca348ca6734d6d4cbac8db46d2bef52b699d03748d4b75d18e661ab",
    "DEV136-FWD-IMPLEMENT-004": "5613b02a220966212ed05d4fcbc98825d6eb658c3072bb88ab9aa2f6f00d1336",
    "DEV136-FWD-REVIEW-001": "128ad2bb3a23ee3017098bee1d50b395f5cd3f086618f4b02ff2966d610863a1",
    "DEV136-FWD-REVIEW-002": "5dd735c54afec3e6f32dd7843e1d92409ac0414f403eb26f8b3a693e1a86e6d0",
    "DEV136-FWD-REVIEW-003": "ed476f4c874372904783c3e3143c1717224ee601080757b3414888e385fba8e0",
    "DEV136-FWD-REVIEW-004": "5205bca70575277a56b080b4cd5e6588dbe7e6a8a75f733c50ae54e2dbb19eee",
    "DEV136-FWD-DEBUG-001": "27d89e2bfccf51b9c4b62cbf901caadba443546c6b98e80309658c253ec2e9d7",
    "DEV136-FWD-DEBUG-002": "f0c0363ee8376343a9432f71d683c72b63c5b77b36f1021f0c6d0e2e188d18ad",
    "DEV136-FWD-DEBUG-003": "e3d58d1dd7dfaebdb324066871e8240b5931e78a0b2d24ecd0014155ca36ac5e",
    "DEV136-FWD-DEBUG-004": "f4a1b570c2605ebb919159dbf901bb0c9490d043efe8d39c91e0bfbe35edd154",
    "DEV136-FWD-VALIDATE-001": "3c53a023eecc7572a302836b9d54a747520cf44c0932d085b5cc97985c8592d4",
    "DEV136-FWD-VALIDATE-002": "6026011bc55e5d4ab242e45aaaeb642cd5da469aecbee9656655a801da0e740c",
    "DEV136-FWD-VALIDATE-003": "77b647196bd891d2337646056c8eea5ab02293f6031a47423634f554feda7778",
    "DEV136-FWD-VALIDATE-004": "0d07a828298e3776af2887b250de273c3d3f72a59aad309dcd4509d96d86f14e",
}

DISTINCTIVE_INTERNAL_TOKENS = (
    "activationStatus",
    "reasonCode",
    "clarificationKind",
    "missingInput",
    "selectedSkill",
    "routerInput",
    "architectureResult",
    "architectureSchemaVersion",
    "stateVersion",
    "policyVersion",
    "finalResponseOwner",
    "apiAvailability",
    "stateModel",
    "trustBoundaries",
    "contextPolicy",
    "toolAndEffectPolicy",
    "failurePolicy",
    "requestedOperation",
    "artifactState",
    "evidenceState",
)

CONTEXTUAL_INTERNAL_FIELDS = (
    "domain",
    "workflow",
    "scope",
    "pattern",
    "source",
    "destination",
    "verification",
    "limitations",
)

PROMPT_PRIVACY_PATTERNS = {
    "absolute_unix_path": r"(?<![A-Za-z0-9_.-])/(?:[A-Za-z0-9._-]+/)*[A-Za-z0-9._-]+",
    "windows_path": r"[A-Za-z]:\\",
    "bearer_credential": r"(?i)\bbearer\s+[a-z0-9._~+/-]{8,}",
    "api_key": r"\b(?:sk|pk)-[A-Za-z0-9_-]{8,}",
    "host_identity": r"(?i)\b(?:host(?:name| identity)|machine name|computer name)\s*[:=]",
    "raw_user_material": r"(?i)\b(?:raw user (?:material|prompt|transcript)|verbatim user material)\s*[:=]",
}

FORWARD_ASSERTIONS = (
    "activation",
    "routing",
    "one_clarification",
    "review_first_ordering",
    "independent_version_labels",
    "common_sections",
    "workflow_sections",
)

FORWARD_STATUSES = {"pass", "fail", "blocked", "not_applicable"}
FORWARD_EVIDENCE_KEYS = {
    "schemaVersion",
    "sourceIssue",
    "evidenceKind",
    "mode",
    "status",
    "model",
    "codexVersion",
    "fixtureSha256",
    "host",
    "privacy",
    "summary",
    "cases",
}
FORWARD_HOST_KEYS = {
    "name",
    "version",
    "model",
    "modelSelection",
    "sessionMode",
    "resolvedExecutableSha256",
    "prerequisites",
    "blockerReason",
    "claudeInvoked",
}
FORWARD_PREREQUISITE_KEYS = {
    "binary",
    "version",
    "authentication",
    "model",
    "pluginActivation",
    "discovery",
    "installation",
}
FORWARD_SUMMARY_KEYS = {
    "fixtureCaseCount",
    "attemptedCount",
    "passedCount",
    "failedCount",
    "blockedCount",
    "notApplicableCount",
}
FORWARD_CASE_KEYS = {
    "caseId",
    "skillUnderTest",
    "sessionOrdinal",
    "promptSha256",
    "rubricContractSha256",
    "codexExitCode",
    "responseSha256",
    "responseBytes",
    "toolEventCount",
    "verdict",
    "assertions",
}
FORWARD_PRIVACY = {
    "rawPrompts": "transient_not_committed",
    "rawResponses": "transient_not_committed",
    "rawToolEvents": "transient_not_committed",
    "committedEvidence": "normalized_metadata_and_sha256_only",
    "offlineScorerOutputs": "approved_synthetic_or_redacted_only",
    "expectedAnswersIncludedInPrompts": False,
}
FORBIDDEN_FORWARD_EVIDENCE_KEYS = {
    "command",
    "events",
    "outputPath",
    "prompt",
    "rawPrompt",
    "rawReasoning",
    "rawResponse",
    "rawToolEvents",
    "resolvedExecutable",
    "response",
    "transcript",
}
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_forward_runner():
    if not RUNNER_PATH.is_file():
        raise AssertionError(
            "DEV-136 RED: tests/e2e/codex_skill_forward_tests.py is absent"
        )
    spec = importlib.util.spec_from_file_location(
        "codex_skill_forward_tests_contract", RUNNER_PATH
    )
    if spec is None or spec.loader is None:
        raise AssertionError("DEV-136 RED: forward runner cannot be imported")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_payload_sha256(value) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256_bytes(payload)


def fixture_payload_sha256(fixture: dict) -> str:
    return canonical_payload_sha256(fixture)


def captured_executable_sha256() -> str:
    return sha256_bytes(b"approved-synthetic-codex-executable-identity")


def prompt_sha256(case: dict) -> str:
    return sha256_bytes(case["prompt"].encode("utf-8"))


def rubric_contract_sha256(fixture: dict, case: dict) -> str:
    payload = {
        "name": case["rubricContract"],
        "checks": fixture["rubricContracts"][case["rubricContract"]],
    }
    return canonical_payload_sha256(payload)


def token_is_present(text: str, token: str) -> bool:
    pattern = rf"(?<![a-z0-9_]){re.escape(token.lower())}(?![a-z0-9_])"
    return re.search(pattern, text.lower()) is not None


def internal_field_context_is_present(text: str, field: str) -> bool:
    escaped = re.escape(field)
    pattern = rf"""(?ix)
        (?:[\"'`]{escaped}[\"'`]\s*[:=])
        |(?:\b{escaped}\s*=)
        |(?:(?:\{{|,)\s*{escaped}\s*:)
    """
    return re.search(pattern, text) is not None


def output_heading_is_present(text: str, heading: str) -> bool:
    escaped = re.escape(heading)
    article = r"(?:(?:an?|the)\s+)?"
    meta_noun = r"(?:result|output|response|answer)"
    modal = r"(?:(?:must|should|shall|will|can|may)\s+)?"
    request_verb = (
        r"(?:includ(?:e|es|ed|ing)|contain(?:s|ed|ing)?|"
        r"list(?:s|ed|ing)?|show(?:s|ed|ing)?|request(?:s|ed|ing)?)"
    )
    structural_verb = (
        rf"(?:{request_verb}|add(?:s|ed|ing)?|provid(?:e|es|ed|ing)|"
        r"return(?:s|ed|ing)?|emit(?:s|ted|ting)?|use(?:s|d|ing)?)"
    )
    bare_imperative = r"(?:return|emit|provide|include|contain|list|show|request)"
    heading_terminal = rf"{escaped}(?=\s*(?:[,.;:!?)]+|$))"
    meta_location = rf"(?:in|within|on|under|to)\s+{article}{meta_noun}\b"
    appear_verb = r"appear(?:s|ed|ing)?"
    passive_auxiliary = (
        r"(?:(?:is|are|was|were)|(?:has|have|had)\s+been|"
        r"(?:must|should|shall|will|can|may)\s+be)"
    )
    output_participle = (
        r"(?:included|contained|listed|shown|requested|provided|returned|emitted)"
    )
    patterns = (
        rf"(?im)^[ \t]*(?:#{{1,6}}[ \t]+)?{escaped}[ \t]*:?[ \t]*$",
        rf"(?i)\b{structural_verb}\s+{article}{escaped}\s+"
        rf"(?:section|heading)\b",
        rf"(?i)[\"'`]{escaped}[\"'`]\s*[:=]",
        rf"(?i)\b(?:key|field)\s+(?:named|called)\s+{escaped}\b",
        rf"(?i)\b{article}{meta_noun}\s+{modal}{request_verb}\s+"
        rf"{article}{heading_terminal}",
        rf"(?i)\b{bare_imperative}\s+{article}{heading_terminal}",
        rf"(?i)\b{bare_imperative}\s+{article}{escaped}\s+{meta_location}",
        rf"(?i)\b{escaped}\s+{modal}{appear_verb}\s+{meta_location}",
        rf"(?i)\b{escaped}\s+{passive_auxiliary}\s+{output_participle}\s+"
        rf"{meta_location}",
    )
    return any(re.search(pattern, text) is not None for pattern in patterns)


def prompt_privacy_pattern_is_present(text: str, name: str, pattern: str) -> bool:
    candidate = text
    if name == "absolute_unix_path":
        candidate = re.sub(r"(?i)\bhttps://[^\s<>\"']+", "", candidate)
    return re.search(pattern, candidate) is not None


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
        self.assertEqual(FIXTURE_KEYS, set(fixture))
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
        self.assertEqual(
            [expected[:4] for expected in EXPECTED_CASES],
            [
                (
                    case["id"],
                    case["skillUnderTest"],
                    case["phase"],
                    case["category"],
                )
                for case in cases
            ],
        )
        self.assertEqual(25, len(cases))
        self.assertEqual(25, len({case["id"] for case in cases}))

        baselines = [case for case in cases if case["phase"] == "baseline"]
        forwards = [case for case in cases if case["phase"] == "forward"]
        self.assertEqual(5, len(baselines))
        self.assertEqual(20, len(forwards))
        self.assertTrue(all(case["category"] == "positive" for case in baselines))
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
        output_headings = (
            *COMMON_SECTIONS,
            *(section for sections in WORKFLOW_SECTIONS.values() for section in sections),
        )
        for case in self.require_fixture()["cases"]:
            with self.subTest(case=case["id"]):
                prompt = case["prompt"]
                for token in (*SKILLS, *DISTINCTIVE_INTERNAL_TOKENS):
                    self.assertFalse(
                        token_is_present(prompt, token),
                        f"prompt leaks hidden contract token {token!r}",
                    )
                for field in CONTEXTUAL_INTERNAL_FIELDS:
                    self.assertFalse(
                        internal_field_context_is_present(prompt, field),
                        f"prompt leaks internal field context {field!r}",
                    )
                for heading in output_headings:
                    self.assertFalse(
                        output_heading_is_present(prompt, heading),
                        f"prompt leaks expected output heading {heading!r}",
                    )
                self.assertNotRegex(prompt.lower(), r"expected[ _-]answer")

    def test_approved_synthetic_prompts_match_reviewed_hashes(self) -> None:
        cases = self.require_fixture()["cases"]
        self.assertEqual(
            set(APPROVED_PROMPT_SHA256_BY_CASE),
            {case["id"] for case in cases},
        )
        for case in cases:
            with self.subTest(case=case["id"]):
                self.assertEqual(
                    APPROVED_PROMPT_SHA256_BY_CASE[case["id"]],
                    prompt_sha256(case),
                )

    def test_approved_synthetic_prompts_contain_no_private_material(self) -> None:
        for case in self.require_fixture()["cases"]:
            for name, pattern in PROMPT_PRIVACY_PATTERNS.items():
                with self.subTest(case=case["id"], privacy_pattern=name):
                    self.assertFalse(
                        prompt_privacy_pattern_is_present(
                            case["prompt"],
                            name,
                            pattern,
                        )
                    )

    def test_natural_prose_may_use_ordinary_contract_words(self) -> None:
        accepted_prompts = (
            "Describe a workflow whose scope uses a pattern with a source and "
            "destination, then discuss verification and limitations in natural prose.",
            "Summarize the findings in prose, then explain activation and scope as "
            "architecture concepts.",
            "The result can describe why activation and scope matter without "
            "prescribing output sections.",
            "The findings from an audit explain the first divergence.",
            "Describe the activation and scope behavior of the coordinator.",
            "Discuss the limitations of an API before implementation.",
            "Use normal workflow prose to explain sequencing.",
            "The result contains findings from an audit, not prescribed output fields.",
            "The answer explains findings from an audit.",
        )
        for prompt in accepted_prompts:
            with self.subTest(prompt=prompt):
                fixture = copy.deepcopy(self.require_fixture())
                fixture["cases"][0]["prompt"] = prompt
                validator = SkillCaseFixtureTests()
                validator.fixture = fixture
                validator.test_prompts_do_not_leak_expected_answers_or_contract_tokens()

    def test_prototype_sources_resolve_with_exact_category_and_activation(self) -> None:
        prototype_cases = {
            case["id"]: case for case in load_json(PROTOTYPE_PATH)["cases"]
        }
        fixture_cases = self.require_fixture()["cases"]
        for case, expected in zip(fixture_cases, EXPECTED_CASES, strict=True):
            expected_sources = expected[4]
            with self.subTest(case=case["id"]):
                self.assertEqual(list(expected_sources), case["sourcePrototypeIds"])
                sources = [prototype_cases[source_id] for source_id in expected_sources]
                self.assertTrue(
                    all(
                        source["expectedActivation"] == case["expectedActivation"]
                        for source in sources
                    )
                )
                if case["phase"] == "baseline" or case["category"] == "complete-output":
                    self.assertTrue(all(source["category"] == "positive" for source in sources))
                elif case["category"] == "negative":
                    self.assertTrue(all(source["category"] == "negative" for source in sources))
                elif case["category"] == "ambiguous":
                    self.assertTrue(all(source["category"] == "ambiguous" for source in sources))
                elif case["skillUnderTest"] == SKILLS[2]:
                    self.assertEqual(
                        ["ambiguous", "positive"],
                        [source["category"] for source in sources],
                    )
                else:
                    self.assertTrue(all(source["category"] == "positive" for source in sources))

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

    def test_evidence_schema_binding_and_derivations_are_exact(self) -> None:
        evidence = self.require_evidence()
        fixture = self.fixture
        self.assertEqual(EVIDENCE_KEYS, set(evidence))
        self.assertEqual(INITIAL_CAPTURE_HEAD, evidence["initialRepositoryHeadAtCapture"])
        self.assertEqual(
            "tests/fixtures/dev-136-codex-skill-cases.json",
            evidence["caseContract"],
        )
        self.assertEqual(
            sha256_bytes(FIXTURE_PATH.read_bytes()),
            evidence["fixtureSha256"],
        )
        self.assertEqual(list(APPROVED_LIMITATIONS), evidence["limitations"])
        self.assertEqual(
            {"sessionCount", "failedBaselineCount", "passedBaselineCount"},
            set(evidence["summary"]),
        )

        fixture_by_id = {case["id"]: case for case in fixture["cases"]}
        baselines = evidence["baselines"]
        expected_baselines = EXPECTED_CASES[:5]
        self.assertEqual(len(expected_baselines), len(baselines))

        for ordinal, (row, expected) in enumerate(
            zip(baselines, expected_baselines, strict=True), 1
        ):
            case_id, skill, phase, category, _ = expected
            case = fixture_by_id[case_id]
            with self.subTest(case=case_id):
                self.assertEqual(BASELINE_ROW_KEYS, set(row))
                self.assertEqual("baseline", phase)
                self.assertEqual("positive", category)
                self.assertEqual(case_id, row["caseId"])
                self.assertEqual(skill, row["skillUnderTest"])
                self.assertEqual(ordinal, row["sessionOrdinal"])
                expected_head = (
                    REVIEW_RECAPTURE_HEAD
                    if case_id == "DEV136-BASE-REVIEW-001"
                    else INITIAL_CAPTURE_HEAD
                )
                self.assertEqual(expected_head, row["repositoryHeadAtCapture"])
                self.assertEqual(prompt_sha256(case), row["promptSha256"])
                self.assertEqual(
                    rubric_contract_sha256(fixture, case),
                    row["rubricContractSha256"],
                )
                self.assertEqual(0, row["codexExitCode"])
                self.assertRegex(row["responseSha256"], r"^[0-9a-f]{64}$")
                self.assertIs(type(row["responseBytes"]), int)
                self.assertGreater(row["responseBytes"], 0)
                self.assertIs(type(row["toolEventCount"]), int)
                self.assertGreaterEqual(row["toolEventCount"], 0)

                outcome = row["rubricOutcome"]
                self.assertEqual({"checks", "failedChecks", "verdict"}, set(outcome))
                self.assertEqual(list(POSITIVE_RUBRIC), list(outcome["checks"]))
                self.assertTrue(
                    all(type(value) is bool for value in outcome["checks"].values())
                )
                false_checks = [
                    check for check, passed in outcome["checks"].items() if not passed
                ]
                self.assertEqual(false_checks, outcome["failedChecks"])
                self.assertEqual("fail" if false_checks else "pass", outcome["verdict"])
                self.assertEqual(
                    [FAILURE_CLASS_BY_CHECK[check] for check in false_checks],
                    row["observedFailureClasses"],
                )

        failed_count = sum(
            row["rubricOutcome"]["verdict"] == "fail" for row in baselines
        )
        self.assertEqual(
            {
                "sessionCount": len(baselines),
                "failedBaselineCount": failed_count,
                "passedBaselineCount": len(baselines) - failed_count,
            },
            evidence["summary"],
        )

    def test_capture_heads_resolve_and_follow_task_1_ancestry(self) -> None:
        evidence = self.require_evidence()
        current_head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        expected_by_case = {
            case_id: (
                REVIEW_RECAPTURE_HEAD
                if case_id == "DEV136-BASE-REVIEW-001"
                else INITIAL_CAPTURE_HEAD
            )
            for case_id, *_ in EXPECTED_CASES[:5]
        }

        for row in evidence["baselines"]:
            capture_head = row["repositoryHeadAtCapture"]
            with self.subTest(case=row["caseId"]):
                self.assertRegex(capture_head, r"^[0-9a-f]{40}$")
                resolved = subprocess.run(
                    ["git", "rev-parse", "--verify", f"{capture_head}^{{commit}}"],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(0, resolved.returncode, resolved.stderr)
                self.assertEqual(capture_head, resolved.stdout.strip())
                self.assertEqual(expected_by_case[row["caseId"]], capture_head)
                for ancestor, descendant in (
                    (INITIAL_CAPTURE_HEAD, capture_head),
                    (capture_head, current_head),
                ):
                    ancestry = subprocess.run(
                        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
                        cwd=ROOT,
                        capture_output=True,
                        text=True,
                    )
                    self.assertEqual(0, ancestry.returncode, ancestry.stderr)

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
        self.assertNotRegex(
            serialized,
            r"(?<![A-Za-z0-9_.-])/(?:[A-Za-z0-9._-]+/)*[A-Za-z0-9._-]+",
        )
        self.assertNotRegex(serialized, r"[A-Za-z]:\\\\")
        self.assertNotRegex(serialized, r"sk-[A-Za-z0-9_-]{8,}")
        self.assertNotRegex(serialized.lower(), r"\bbearer\s+[a-z0-9._~+/-]{8,}")


class ContractMutationReproductionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = load_json(FIXTURE_PATH)
        cls.evidence = load_json(EVIDENCE_PATH)

    def assert_fixture_mutation_rejected(self, fixture: dict) -> None:
        validator = SkillCaseFixtureTests()
        validator.fixture = fixture
        with self.assertRaises(AssertionError):
            validator.test_fixture_metadata_is_exact()
            validator.test_fixture_has_exact_baseline_and_forward_coverage()
            validator.test_every_case_has_exact_shape_and_normative_router_values()
            validator.test_prompts_do_not_leak_expected_answers_or_contract_tokens()
            validator.test_approved_synthetic_prompts_match_reviewed_hashes()
            validator.test_approved_synthetic_prompts_contain_no_private_material()
            validator.test_prototype_sources_resolve_with_exact_category_and_activation()
            validator.test_activation_output_and_rubric_expectations_match_category()
            validator.test_negative_cases_cover_all_adjacent_domains()
            validator.test_review_and_fix_is_the_review_positive_ordering_case()

    def assert_evidence_mutation_rejected(self, evidence: dict) -> None:
        validator = SkillBaselineEvidenceTests()
        validator.evidence = evidence
        validator.fixture = self.fixture
        with self.assertRaises(AssertionError):
            validator.test_evidence_host_and_privacy_metadata_are_exact()
            validator.test_evidence_has_one_real_failing_baseline_per_skill()
            validator.test_evidence_schema_binding_and_derivations_are_exact()
            validator.test_capture_heads_resolve_and_follow_task_1_ancestry()
            validator.test_evidence_contains_no_raw_host_payload_fields_or_local_paths()

    def test_rejects_closed_schema_and_private_value_mutations(self) -> None:
        mutations = {
            "raw_reasoning": lambda value: value["baselines"][0].update(
                {"rawReasoning": "transient reasoning"}
            ),
            "tool_arguments": lambda value: value["baselines"][0][
                "rubricOutcome"
            ].update({"toolArguments": {"path": "synthetic"}}),
            "host_identity": lambda value: value.update(
                {"hostIdentity": "unapproved-host"}
            ),
            "unix_path": lambda value: value["limitations"].append(
                "/tmp/private-host-output"
            ),
            "bearer_value": lambda value: value["limitations"].append(
                "Bearer synthetic-secret-value"
            ),
        }
        for name, mutate in mutations.items():
            with self.subTest(mutation=name):
                mutant = copy.deepcopy(self.evidence)
                mutate(mutant)
                self.assert_evidence_mutation_rejected(mutant)

    def test_evidence_declares_fixture_prompt_and_rubric_hashes(self) -> None:
        self.assertIn("fixtureSha256", self.evidence)
        for row in self.evidence["baselines"]:
            with self.subTest(case=row["caseId"]):
                self.assertIn("promptSha256", row)
                self.assertIn("rubricContractSha256", row)

    def test_rejects_evidence_mapping_and_derivation_mutations(self) -> None:
        mutations = {
            "row_order": lambda value: value["baselines"].__setitem__(
                slice(0, 2), list(reversed(value["baselines"][:2]))
            ),
            "skill_swap": lambda value: (
                value["baselines"][0].update(
                    {"skillUnderTest": SKILLS[1]}
                ),
                value["baselines"][1].update(
                    {"skillUnderTest": SKILLS[0]}
                ),
            ),
            "arbitrary_check": lambda value: value["baselines"][0][
                "rubricOutcome"
            ]["checks"].update({"arbitrary_check": False}),
            "failed_check_drift": lambda value: value["baselines"][0][
                "rubricOutcome"
            ]["failedChecks"].pop(),
            "failure_class_drift": lambda value: value["baselines"][0][
                "observedFailureClasses"
            ].__setitem__(0, "missing_skill_selection"),
        }
        for name, mutate in mutations.items():
            with self.subTest(mutation=name):
                mutant = copy.deepcopy(self.evidence)
                mutate(mutant)
                self.assert_evidence_mutation_rejected(mutant)

    def test_rejects_fixture_identity_prototype_and_leakage_mutations(self) -> None:
        mutations = {
            "case_order": lambda value: value["cases"].__setitem__(
                slice(0, 2), list(reversed(value["cases"][:2]))
            ),
            "baseline_category": lambda value: value["cases"][0].update(
                {"category": "complete-output"}
            ),
            "prototype_activation": lambda value: value["cases"][0].update(
                {"sourcePrototypeIds": ["DEV134-NEG-001"]}
            ),
            "case_insensitive_skill": lambda value: value["cases"][0].update(
                {
                    "prompt": value["cases"][0]["prompt"]
                    + " DESIGN-APPLE-FOUNDATION-MODELS-HANDOFF"
                }
            ),
            "workflow_heading": lambda value: value["cases"][0].update(
                {"prompt": value["cases"][0]["prompt"] + "\n## FINDINGS"}
            ),
            "internal_result_token": lambda value: value["cases"][0].update(
                {"prompt": value["cases"][0]["prompt"] + " ARCHITECTURERESULT"}
            ),
            "common_heading": lambda value: value["cases"][0].update(
                {"prompt": value["cases"][0]["prompt"] + "\nLIMITATIONS:"}
            ),
            "contextual_internal_field": lambda value: value["cases"][0].update(
                {"prompt": value["cases"][0]["prompt"] + '\n{"SCOPE": "handoff"}'}
            ),
        }
        for name, mutate in mutations.items():
            with self.subTest(mutation=name):
                mutant = copy.deepcopy(self.fixture)
                mutate(mutant)
                self.assert_fixture_mutation_rejected(mutant)

    def test_rejects_private_prompt_drift(self) -> None:
        prompt_suffixes = {
            "credential": " Credential: Bearer synthetic-secret-value",
            "private_path": " Private path: /Users/private/customer.txt",
            "windows_private_path": r" Private path: C:\Users\private\customer.txt",
            "host_identity": " Host identity: joes-macbook-pro",
            "raw_user_material": " Raw user material: customer-alpha text",
        }
        for name, suffix in prompt_suffixes.items():
            with self.subTest(mutation=name):
                mutant = copy.deepcopy(self.fixture)
                mutant["cases"][5]["prompt"] += suffix
                validator = SkillCaseFixtureTests()
                validator.fixture = mutant
                with self.assertRaises(AssertionError):
                    validator.test_approved_synthetic_prompts_match_reviewed_hashes()
                with self.assertRaises(AssertionError):
                    validator.test_approved_synthetic_prompts_contain_no_private_material()

    def test_rejects_inline_output_heading_contexts_case_insensitively(self) -> None:
        prompt_suffixes = {
            "workflow_section": " Include a FINDINGS section.",
            "common_result": " Include ACTIVATION AND SCOPE in the result.",
            "common_key": ' Add "ACTIVATION AND SCOPE": as an output key.',
            "review_output_includes": " The output includes Findings.",
            "review_result_contains": " The result contains Findings.",
            "review_return": " Return Findings.",
            "review_heading_appears": " Findings should appear in the output.",
            "case_variant": " tHE aNSWER sHOWS fINDINGS.",
            "emit_imperative": " Emit Findings.",
            "provide_imperative": " Provide Findings.",
            "include_imperative": " Include Findings.",
            "list_inflection": " The response lists Findings.",
            "show_inflection": " The output showed Findings.",
            "request_inflection": " The answer requests Findings.",
            "heading_requested": " Findings are requested in the answer.",
            "heading_appear_inflection": " Findings appear in the response.",
        }
        for name, suffix in prompt_suffixes.items():
            with self.subTest(mutation=name):
                mutant = copy.deepcopy(self.fixture)
                mutant["cases"][5]["prompt"] += suffix
                validator = SkillCaseFixtureTests()
                validator.fixture = mutant
                with self.assertRaises(AssertionError):
                    validator.test_prompts_do_not_leak_expected_answers_or_contract_tokens()

    def test_path_privacy_accepts_https_and_rejects_file_or_absolute_paths(self) -> None:
        accepted = copy.deepcopy(self.fixture)
        accepted["cases"][5]["prompt"] += (
            " Consult https://developer.apple.com/documentation/foundationmodels."
        )
        validator = SkillCaseFixtureTests()
        validator.fixture = accepted
        validator.test_approved_synthetic_prompts_contain_no_private_material()

        rejected_suffixes = {
            "absolute_path": " Read /Users/private/customer.txt.",
            "file_uri": " Read file:///Users/private/customer.txt.",
        }
        for name, suffix in rejected_suffixes.items():
            with self.subTest(mutation=name):
                mutant = copy.deepcopy(self.fixture)
                mutant["cases"][5]["prompt"] += suffix
                validator.fixture = mutant
                with self.assertRaises(AssertionError):
                    validator.test_approved_synthetic_prompts_contain_no_private_material()

    def test_rejects_nonexistent_and_wrong_resolving_capture_heads(self) -> None:
        capture_heads = {
            "nonexistent": "9b2c399fda3790d36ac200c3770f733c0ab55b33",
            "wrong_resolving": INITIAL_CAPTURE_HEAD,
        }
        for name, capture_head in capture_heads.items():
            with self.subTest(mutation=name):
                mutant = copy.deepcopy(self.evidence)
                mutant["baselines"][2]["repositoryHeadAtCapture"] = capture_head
                validator = SkillBaselineEvidenceTests()
                validator.evidence = mutant
                validator.fixture = self.fixture
                with self.assertRaises(AssertionError):
                    validator.test_capture_heads_resolve_and_follow_task_1_ancestry()


def _forward_fixture(*case_ids: str) -> dict:
    fixture = copy.deepcopy(load_json(FIXTURE_PATH))
    selected = [case for case in fixture["cases"] if case["id"] in case_ids]
    fixture["cases"] = selected
    fixture["caseCount"] = len(selected)
    return fixture


def _forward_assertions(**overrides: str) -> dict[str, str]:
    assertions = {name: "pass" for name in FORWARD_ASSERTIONS}
    assertions.update(overrides)
    return assertions


def _forward_observation(case: dict, **assertion_overrides: str) -> dict:
    response = f"approved-redacted:{case['id']}".encode()
    return {
        "provenance": "approved_redacted",
        "responseSha256": sha256_bytes(response),
        "responseBytes": len(response),
        "toolEventCount": 0,
        "assertions": _forward_assertions(**assertion_overrides),
    }


def _forward_outputs(fixture: dict, **overrides: str) -> dict[str, dict]:
    return {
        case["id"]: _forward_observation(case, **overrides)
        for case in fixture["cases"]
    }


def _passing_prerequisites(executable: str = "/opt/codex") -> dict:
    return {
        "resolvedExecutable": executable,
        "executableSha256": captured_executable_sha256(),
        "version": "0.144.5",
        "authenticated": True,
        "modelAvailable": True,
        "pluginAvailable": True,
        "discovery": "pass",
        "installation": "pass",
    }


def _assert_forward_evidence_schema(
    test: unittest.TestCase,
    evidence: dict,
) -> None:
    test.assertEqual(FORWARD_EVIDENCE_KEYS, set(evidence))
    test.assertEqual("1.0", evidence["schemaVersion"])
    test.assertEqual("DEV-136", evidence["sourceIssue"])
    test.assertEqual("codex_skill_forward_test", evidence["evidenceKind"])
    test.assertIn(evidence["mode"], {"offline", "host"})
    test.assertIn(evidence["status"], FORWARD_STATUSES)
    test.assertEqual("gpt-5.6-sol", evidence["model"])
    test.assertEqual("0.144.5", evidence["codexVersion"])
    test.assertRegex(evidence["fixtureSha256"], SHA256_PATTERN)

    host = evidence["host"]
    test.assertEqual(FORWARD_HOST_KEYS, set(host))
    test.assertEqual("codex", host["name"])
    test.assertEqual("0.144.5", host["version"])
    test.assertEqual("gpt-5.6-sol", host["model"])
    test.assertEqual("explicit_cli_argument", host["modelSelection"])
    test.assertIn(host["sessionMode"], {"not_applicable", "fresh_ephemeral"})
    if host["resolvedExecutableSha256"] is not None:
        test.assertRegex(host["resolvedExecutableSha256"], SHA256_PATTERN)
    test.assertIsInstance(host["claudeInvoked"], bool)
    test.assertFalse(host["claudeInvoked"])
    test.assertTrue(host["blockerReason"] is None or isinstance(host["blockerReason"], str))
    test.assertEqual(FORWARD_PREREQUISITE_KEYS, set(host["prerequisites"]))
    for status in host["prerequisites"].values():
        test.assertIn(status, FORWARD_STATUSES)

    test.assertEqual(FORWARD_PRIVACY, evidence["privacy"])
    summary = evidence["summary"]
    test.assertEqual(FORWARD_SUMMARY_KEYS, set(summary))
    for key, count in summary.items():
        test.assertIs(type(count), int, key)
        test.assertGreaterEqual(count, 0, key)
    test.assertEqual(len(evidence["cases"]), summary["attemptedCount"])
    test.assertLessEqual(summary["attemptedCount"], summary["fixtureCaseCount"])
    test.assertEqual(
        summary["attemptedCount"],
        sum(
            summary[key]
            for key in (
                "passedCount",
                "failedCount",
                "blockedCount",
                "notApplicableCount",
            )
        ),
    )

    for ordinal, row in enumerate(evidence["cases"], 1):
        test.assertEqual(FORWARD_CASE_KEYS, set(row))
        test.assertRegex(row["caseId"], r"^DEV136-(BASE|FWD)-[A-Z]+-[0-9]{3}$")
        test.assertIn(row["skillUnderTest"], SKILLS)
        test.assertEqual(ordinal, row["sessionOrdinal"])
        test.assertRegex(row["promptSha256"], SHA256_PATTERN)
        test.assertRegex(row["rubricContractSha256"], SHA256_PATTERN)
        if row["codexExitCode"] is not None:
            test.assertIs(type(row["codexExitCode"]), int)
            test.assertGreaterEqual(row["codexExitCode"], 0)
        if row["responseSha256"] is not None:
            test.assertRegex(row["responseSha256"], SHA256_PATTERN)
        for key in ("responseBytes", "toolEventCount"):
            test.assertIs(type(row[key]), int)
            test.assertGreaterEqual(row[key], 0)
        test.assertIn(row["verdict"], FORWARD_STATUSES)
        test.assertEqual(set(FORWARD_ASSERTIONS), set(row["assertions"]))
        for status in row["assertions"].values():
            test.assertIn(status, FORWARD_STATUSES)

    def assert_private_values_absent(value) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                test.assertNotIn(key, FORBIDDEN_FORWARD_EVIDENCE_KEYS)
                assert_private_values_absent(child)
        elif isinstance(value, list):
            for child in value:
                assert_private_values_absent(child)
        elif isinstance(value, str):
            test.assertIsNone(
                re.search(
                    r"(?<![A-Za-z0-9_.-])/(?:[A-Za-z0-9._-]+/)*[A-Za-z0-9._-]+",
                    value,
                )
            )
            test.assertIsNone(re.search(r"[A-Za-z]:\\", value))
            test.assertIsNone(re.search(r"(?i)\bbearer\s+[a-z0-9._~+/-]{8,}", value))
            test.assertIsNone(re.search(r"\b(?:sk|pk)-[A-Za-z0-9_-]{8,}", value))

    assert_private_values_absent(evidence)


def _derived_status(verdicts: list[str]) -> str:
    for status in ("fail", "blocked", "pass"):
        if status in verdicts:
            return status
    return "not_applicable"


def _assert_forward_evidence_derivations(
    test: unittest.TestCase,
    runner,
    fixture: dict,
    scorer_outputs: dict[str, dict],
    evidence: dict,
    *,
    host_results: list[dict] | None = None,
    executable_sha256: str | None = None,
) -> None:
    _assert_forward_evidence_schema(test, evidence)
    test.assertEqual(fixture_payload_sha256(fixture), evidence["fixtureSha256"])
    rows = evidence["cases"]
    test.assertLessEqual(len(rows), len(fixture["cases"]))
    for index, (case, row) in enumerate(
        zip(fixture["cases"], rows, strict=False)
    ):
        scored = runner.score_case(case, scorer_outputs[case["id"]])
        test.assertEqual(case["id"], row["caseId"])
        test.assertEqual(case["skillUnderTest"], row["skillUnderTest"])
        test.assertEqual(prompt_sha256(case), row["promptSha256"])
        test.assertEqual(
            rubric_contract_sha256(fixture, case),
            row["rubricContractSha256"],
        )
        test.assertEqual(scored["assertions"], row["assertions"])
        test.assertEqual(scored["verdict"], row["verdict"])
        if host_results is None:
            observation = scorer_outputs[case["id"]]
            test.assertIsNone(row["codexExitCode"])
            test.assertEqual(observation["responseSha256"], row["responseSha256"])
            test.assertEqual(observation["responseBytes"], row["responseBytes"])
            test.assertEqual(observation["toolEventCount"], row["toolEventCount"])
        else:
            result = host_results[index]
            test.assertEqual(result["codexExitCode"], row["codexExitCode"])
            test.assertEqual(result["responseSha256"], row["responseSha256"])
            test.assertEqual(result["responseBytes"], row["responseBytes"])
            test.assertEqual(result["toolEventCount"], row["toolEventCount"])

    verdicts = [row["verdict"] for row in rows]
    expected_summary = {
        "fixtureCaseCount": len(fixture["cases"]),
        "attemptedCount": len(rows),
        "passedCount": verdicts.count("pass"),
        "failedCount": verdicts.count("fail"),
        "blockedCount": verdicts.count("blocked"),
        "notApplicableCount": verdicts.count("not_applicable"),
    }
    test.assertEqual(expected_summary, evidence["summary"])
    test.assertEqual(_derived_status(verdicts), evidence["status"])
    test.assertEqual(
        executable_sha256,
        evidence["host"]["resolvedExecutableSha256"],
    )


def _write_bound_evidence(
    runner,
    path: Path,
    evidence: dict,
    fixture: dict,
    scorer_outputs: dict[str, dict],
    *,
    executable_sha256: str | None = None,
    fault_hook=None,
) -> None:
    runner.write_evidence(
        path,
        evidence,
        fixture=fixture,
        scorer_outputs=scorer_outputs,
        executable_sha256=executable_sha256,
        fault_hook=fault_hook,
    )


class _FakePrerequisiteChecker:
    def __init__(self, *snapshots: dict) -> None:
        self.snapshots = [copy.deepcopy(value) for value in snapshots]
        self.calls: list[tuple[str, str, str]] = []

    def __call__(self, executable: str, model: str, version: str) -> dict:
        self.calls.append((executable, model, version))
        index = min(len(self.calls) - 1, len(self.snapshots) - 1)
        return copy.deepcopy(self.snapshots[index])


class _FakeHostProcess:
    def __init__(
        self,
        *,
        responses: list[bytes] | None = None,
        returncodes: list[int] | None = None,
        timeline: list[str] | None = None,
    ) -> None:
        self.responses = responses or [b"approved synthetic response"]
        self.returncodes = returncodes or [0]
        self.commands: list[list[str]] = []
        self.inputs: list[str] = []
        self.output_paths: list[Path] = []
        self.results: list[dict] = []
        self.timeline = timeline if timeline is not None else []

    def __call__(self, command: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
        index = len(self.commands)
        self.commands.append(list(command))
        self.inputs.append(kwargs["input"])
        self.timeline.append("execute")
        output_index = command.index("--output-last-message") + 1
        output_path = Path(command[output_index])
        self.output_paths.append(output_path)
        response = self.responses[min(index, len(self.responses) - 1)]
        output_path.write_bytes(response)
        returncode = self.returncodes[min(index, len(self.returncodes) - 1)]
        jsonl = "\n".join(
            (
                '{"type":"item.completed","item":{"type":"mcp_tool_call"}}',
                '{"type":"turn.completed"}',
            )
        )
        self.results.append(
            {
                "codexExitCode": returncode,
                "responseSha256": sha256_bytes(response),
                "responseBytes": len(response),
                "toolEventCount": 1,
            }
        )
        return subprocess.CompletedProcess(command, returncode, jsonl, "")


class _FakeScorer:
    def __init__(
        self,
        observations: dict[str, dict],
        timeline: list[str] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.observations = observations
        self.calls: list[str] = []
        self.timeline = timeline if timeline is not None else []
        self.error = error

    def __call__(self, case: dict, response: bytes, tool_events: list[dict]) -> dict:
        self.calls.append(case["id"])
        self.timeline.append("score")
        if self.error is not None:
            raise self.error
        return copy.deepcopy(self.observations[case["id"]])


class _ExplodingScorerOutputs(dict):
    def __len__(self):
        raise AssertionError("scorer outputs were read before fixture validation")

    def __getitem__(self, key):
        raise AssertionError("scorer outputs were read before fixture validation")

    def __iter__(self):
        raise AssertionError("scorer outputs were read before fixture validation")

    def __contains__(self, key):
        raise AssertionError("scorer outputs were read before fixture validation")

    def get(self, key, default=None):
        raise AssertionError("scorer outputs were read before fixture validation")

    def items(self):
        raise AssertionError("scorer outputs were read before fixture validation")

    def keys(self):
        raise AssertionError("scorer outputs were read before fixture validation")

    def values(self):
        raise AssertionError("scorer outputs were read before fixture validation")


class _AtomicFault:
    def __init__(self, phase: str) -> None:
        self.phase = phase

    def __call__(self, phase: str) -> None:
        if phase == self.phase:
            raise OSError(f"injected {phase} failure")


class CodexForwardRunnerContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = load_forward_runner()
        cls.fixture = load_json(FIXTURE_PATH)

    def test_constants_and_host_command_semantics_are_exact(self) -> None:
        self.assertEqual(
            (0, 1, 2),
            (self.runner.PASS, self.runner.FAIL, self.runner.BLOCKED),
        )
        self.assertEqual("gpt-5.6-sol", self.runner.EXPECTED_MODEL)
        self.assertEqual("0.144.5", self.runner.EXPECTED_CODEX_VERSION)

        fixture = _forward_fixture("DEV136-FWD-DESIGN-001")
        timeline: list[str] = []
        process = _FakeHostProcess(timeline=timeline)
        outputs = _forward_outputs(fixture)
        scorer = _FakeScorer(outputs, timeline)
        checker = _FakePrerequisiteChecker(_passing_prerequisites("/captured/codex"))
        code, evidence = self.runner.run_host(
            fixture,
            "/captured/codex",
            process,
            checker,
            scorer,
        )

        self.assertEqual(self.runner.PASS, code)
        self.assertEqual(["execute", "score"], timeline)
        self.assertEqual([fixture["cases"][0]["prompt"]], process.inputs)
        command = process.commands[0]
        self.assertEqual(["/captured/codex", "exec"], command[:2])
        self.assertIn("--ephemeral", command)
        self.assertIn("--json", command)
        self.assertEqual(1, command.count("-m"))
        self.assertEqual("gpt-5.6-sol", command[command.index("-m") + 1])
        output_path = command[command.index("--output-last-message") + 1]
        self.assertTrue(Path(output_path).is_absolute())
        self.assertFalse(Path(output_path).is_relative_to(ROOT))
        self.assertEqual(1, command.count("-"))
        self.assertNotIn(fixture["cases"][0]["prompt"], command)
        self.assertNotIn("claude", " ".join(command).lower())
        self.assertNotIn("--model", command)
        self.assertEqual(1, evidence["cases"][0]["toolEventCount"])
        self.assertFalse(Path(output_path).exists())
        _assert_forward_evidence_derivations(
            self,
            self.runner,
            fixture,
            outputs,
            evidence,
            host_results=process.results,
            executable_sha256=captured_executable_sha256(),
        )

    def test_scoring_schema_is_closed_and_status_precedence_is_stable(self) -> None:
        case = self.fixture["cases"][0]
        scenarios = (
            ({}, "pass"),
            ({"activation": "not_applicable"}, "pass"),
            ({"activation": "blocked"}, "blocked"),
            ({"activation": "fail", "routing": "blocked"}, "fail"),
            ({name: "not_applicable" for name in FORWARD_ASSERTIONS}, "not_applicable"),
        )
        for overrides, expected in scenarios:
            with self.subTest(overrides=overrides):
                result = self.runner.score_case(
                    case,
                    _forward_observation(case, **overrides),
                )
                self.assertEqual(expected, result["verdict"])
                self.assertEqual(set(FORWARD_ASSERTIONS), set(result["assertions"]))

        invalid = []
        for mutation in (
            lambda value: value["assertions"].update({"unexpected": "pass"}),
            lambda value: value["assertions"].pop("routing"),
            lambda value: value["assertions"].update({"routing": "unknown"}),
            lambda value: value.update({"provenance": "raw_live"}),
            lambda value: value.update({"responseSha256": "not-a-hash"}),
            lambda value: value.update({"responseBytes": -1}),
            lambda value: value.update({"toolEventCount": True}),
            lambda value: value.update(
                {"rawResponse": "Bearer synthetic-private-secret"}
            ),
            lambda value: value.pop("provenance"),
        ):
            observation = _forward_observation(case)
            mutation(observation)
            invalid.append(observation)
        for observation in invalid:
            with self.assertRaises(ValueError):
                self.runner.score_case(case, observation)

    def test_offline_mode_derives_pass_fail_and_blocked_exit_codes(self) -> None:
        fixture = _forward_fixture("DEV136-FWD-DESIGN-001")
        case = fixture["cases"][0]
        for assertion_status, expected_code in (
            ("pass", self.runner.PASS),
            ("fail", self.runner.FAIL),
            ("blocked", self.runner.BLOCKED),
            ("not_applicable", self.runner.PASS),
        ):
            with self.subTest(status=assertion_status):
                overrides = (
                    {name: "not_applicable" for name in FORWARD_ASSERTIONS}
                    if assertion_status == "not_applicable"
                    else {"activation": assertion_status}
                )
                outputs = {case["id"]: _forward_observation(case, **overrides)}
                code, evidence = self.runner.run_offline(fixture, outputs)
                self.assertEqual(expected_code, code)
                self.assertEqual("offline", evidence["mode"])
                self.assertEqual(assertion_status, evidence["status"])
                _assert_forward_evidence_derivations(
                    self,
                    self.runner,
                    fixture,
                    outputs,
                    evidence,
                )

        aggregate = _forward_fixture(
            "DEV136-FWD-DESIGN-001",
            "DEV136-FWD-REVIEW-001",
        )
        outputs = _forward_outputs(aggregate, activation="blocked")
        outputs[aggregate["cases"][1]["id"]] = _forward_observation(
            aggregate["cases"][1],
            activation="fail",
        )
        code, evidence = self.runner.run_offline(aggregate, outputs)
        self.assertEqual(self.runner.FAIL, code)
        self.assertEqual("fail", evidence["status"])
        _assert_forward_evidence_derivations(
            self,
            self.runner,
            aggregate,
            outputs,
            evidence,
        )

    def test_host_uses_fresh_processes_and_pre_post_checks_per_case(self) -> None:
        fixture = _forward_fixture(
            "DEV136-FWD-DESIGN-001", "DEV136-FWD-REVIEW-001"
        )
        timeline: list[str] = []
        process = _FakeHostProcess(timeline=timeline)
        outputs = _forward_outputs(fixture)
        scorer = _FakeScorer(outputs, timeline)
        checker = _FakePrerequisiteChecker(_passing_prerequisites())

        code, evidence = self.runner.run_host(
            fixture,
            "/opt/codex",
            process,
            checker,
            scorer,
        )

        self.assertEqual(self.runner.PASS, code)
        self.assertEqual(["execute", "score"] * 2, timeline)
        self.assertEqual(2, len(process.commands))
        self.assertEqual(
            [case["prompt"] for case in fixture["cases"]],
            process.inputs,
        )
        self.assertEqual(
            [case["id"] for case in fixture["cases"]],
            scorer.calls,
        )
        self.assertEqual(
            [("/opt/codex", "gpt-5.6-sol", "0.144.5")] * 4,
            checker.calls,
        )
        self.assertEqual([1, 2], [row["sessionOrdinal"] for row in evidence["cases"]])
        self.assertTrue(all(not path.exists() for path in process.output_paths))
        _assert_forward_evidence_derivations(
            self,
            self.runner,
            fixture,
            outputs,
            evidence,
            host_results=process.results,
            executable_sha256=captured_executable_sha256(),
        )

    def test_host_blocks_exact_prerequisites_without_fallback(self) -> None:
        fixture = _forward_fixture("DEV136-FWD-DESIGN-001")
        blockers = {
            "missing_binary": {
                "resolvedExecutable": None,
                "executableSha256": None,
            },
            "version_mismatch": {"version": "0.144.4"},
            "authentication_unavailable": {"authenticated": False},
            "model_unavailable": {"modelAvailable": False},
            "plugin_activation_unavailable": {"pluginAvailable": False},
        }
        for reason, mutation in blockers.items():
            with self.subTest(reason=reason):
                snapshot = _passing_prerequisites()
                snapshot.update(mutation)
                process = _FakeHostProcess()
                scorer = _FakeScorer(_forward_outputs(fixture))
                checker = _FakePrerequisiteChecker(snapshot)
                code, evidence = self.runner.run_host(
                    fixture,
                    "/opt/codex",
                    process,
                    checker,
                    scorer,
                )
                self.assertEqual(self.runner.BLOCKED, code)
                self.assertEqual([], process.commands)
                self.assertEqual([], scorer.calls)
                self.assertEqual(1, len(checker.calls))
                self.assertEqual(reason, evidence["host"]["blockerReason"])
                self.assertEqual(
                    None if reason == "missing_binary" else captured_executable_sha256(),
                    evidence["host"]["resolvedExecutableSha256"],
                )
                _assert_forward_evidence_schema(self, evidence)

    def test_post_capture_prerequisite_drift_fails_and_stops_without_retry(self) -> None:
        fixture = _forward_fixture(
            "DEV136-FWD-DESIGN-001", "DEV136-FWD-REVIEW-001"
        )
        post_mutations = {
            "resolved_path": {"resolvedExecutable": "/opt/replaced-codex"},
            "executable_bytes": {"executableSha256": "f" * 64},
            "version": {"version": "0.144.6"},
            "authentication": {"authenticated": False},
            "model": {"modelAvailable": False},
            "plugin": {"pluginAvailable": False},
        }
        for name, mutation in post_mutations.items():
            with self.subTest(field=name):
                post = _passing_prerequisites()
                post.update(mutation)
                process = _FakeHostProcess()
                scorer = _FakeScorer(_forward_outputs(fixture))
                checker = _FakePrerequisiteChecker(_passing_prerequisites(), post)
                code, evidence = self.runner.run_host(
                    fixture,
                    "/opt/codex",
                    process,
                    checker,
                    scorer,
                )
                self.assertEqual(self.runner.FAIL, code)
                self.assertEqual(1, len(process.commands))
                self.assertEqual([], scorer.calls)
                self.assertEqual(2, len(checker.calls))
                self.assertTrue(
                    all(not path.exists() for path in process.output_paths)
                )
                self.assertEqual(
                    "post_capture_prerequisite_drift",
                    evidence["host"]["blockerReason"],
                )

        second_post = _passing_prerequisites()
        second_post.update({"pluginAvailable": False})
        process = _FakeHostProcess()
        scorer = _FakeScorer(_forward_outputs(fixture))
        checker = _FakePrerequisiteChecker(
            _passing_prerequisites(),
            _passing_prerequisites(),
            _passing_prerequisites(),
            second_post,
        )
        code, _ = self.runner.run_host(
            fixture,
            "/opt/codex",
            process,
            checker,
            scorer,
        )
        self.assertEqual(self.runner.FAIL, code)
        self.assertEqual(2, len(process.commands))
        self.assertEqual(4, len(checker.calls))
        self.assertEqual([fixture["cases"][0]["id"]], scorer.calls)
        self.assertTrue(all(not path.exists() for path in process.output_paths))

        fixture = _forward_fixture("DEV136-FWD-DESIGN-001")
        process = _FakeHostProcess(returncodes=[7])
        scorer = _FakeScorer(_forward_outputs(fixture))
        checker = _FakePrerequisiteChecker(_passing_prerequisites())
        code, evidence = self.runner.run_host(
            fixture,
            "/opt/codex",
            process,
            checker,
            scorer,
        )
        self.assertEqual(self.runner.FAIL, code)
        self.assertEqual(1, len(process.commands))
        self.assertEqual([], scorer.calls)
        self.assertEqual(2, len(checker.calls))
        self.assertEqual("process_failed", evidence["host"]["blockerReason"])
        self.assertTrue(all(not path.exists() for path in process.output_paths))

    def test_scorer_failure_cleans_raw_response_and_returns_stable_failure(self) -> None:
        fixture = _forward_fixture("DEV136-FWD-DESIGN-001")
        process = _FakeHostProcess()
        scorer = _FakeScorer(
            _forward_outputs(fixture),
            error=RuntimeError("injected scorer failure"),
        )
        checker = _FakePrerequisiteChecker(_passing_prerequisites())
        code, evidence = self.runner.run_host(
            fixture,
            "/opt/codex",
            process,
            checker,
            scorer,
        )
        self.assertEqual(self.runner.FAIL, code)
        self.assertEqual([fixture["cases"][0]["id"]], scorer.calls)
        self.assertEqual(2, len(checker.calls))
        self.assertEqual("scoring_failed", evidence["host"]["blockerReason"])
        self.assertNotIn("injected scorer failure", json.dumps(evidence))
        self.assertTrue(all(not path.exists() for path in process.output_paths))

    def test_host_hashes_and_discards_raw_private_response_content(self) -> None:
        fixture = _forward_fixture("DEV136-FWD-DESIGN-001")
        case = fixture["cases"][0]
        raw = b"Bearer synthetic-private-secret from /Users/private/customer.txt"
        process = _FakeHostProcess(responses=[raw])
        outputs = _forward_outputs(fixture)
        scorer = _FakeScorer(outputs)
        code, evidence = self.runner.run_host(
            fixture,
            "/opt/codex",
            process,
            _FakePrerequisiteChecker(
                _passing_prerequisites(), _passing_prerequisites()
            ),
            scorer,
        )
        serialized = json.dumps(evidence, sort_keys=True)
        self.assertEqual(self.runner.PASS, code)
        self.assertEqual(sha256_bytes(raw), evidence["cases"][0]["responseSha256"])
        self.assertEqual(len(raw), evidence["cases"][0]["responseBytes"])
        self.assertEqual(1, evidence["cases"][0]["toolEventCount"])
        self.assertNotIn("synthetic-private-secret", serialized)
        self.assertNotIn("/Users/", serialized)
        self.assertNotIn(case["prompt"], serialized)
        self.assertFalse(process.output_paths[0].exists())
        _assert_forward_evidence_derivations(
            self,
            self.runner,
            fixture,
            outputs,
            evidence,
            host_results=process.results,
            executable_sha256=captured_executable_sha256(),
        )

    def assert_invalid_fixture_rejected_before_use(self, fixture: dict) -> None:
        offline_code, _ = self.runner.run_offline(
            fixture,
            _ExplodingScorerOutputs(),
        )
        self.assertEqual(self.runner.FAIL, offline_code)

        process = _FakeHostProcess()
        scorer = _FakeScorer({})
        host_code, _ = self.runner.run_host(
            fixture,
            "/opt/codex",
            process,
            _FakePrerequisiteChecker(_passing_prerequisites()),
            scorer,
        )
        self.assertEqual(self.runner.FAIL, host_code)
        self.assertEqual([], process.commands)
        self.assertEqual([], scorer.calls)

    def test_fixture_identity_and_every_reviewed_prompt_hash_are_preconditions(self) -> None:
        for index, case in enumerate(self.fixture["cases"]):
            with self.subTest(case=case["id"]):
                mutant = copy.deepcopy(self.fixture)
                mutant["cases"][index]["prompt"] += " Harmless identity drift."
                self.assert_invalid_fixture_rejected_before_use(mutant)

        for name, mutate in {
            "case_order": lambda value: value["cases"].__setitem__(
                slice(0, 2), list(reversed(value["cases"][:2]))
            ),
            "case_count": lambda value: value.update({"caseCount": 24}),
            "case_id": lambda value: value["cases"][0].update({"id": "DEV136-FWD-X-999"}),
        }.items():
            with self.subTest(identity=name):
                mutant = copy.deepcopy(self.fixture)
                mutate(mutant)
                self.assert_invalid_fixture_rejected_before_use(mutant)

    def test_all_prompt_leakage_families_fail_before_execution_or_scoring(self) -> None:
        suffixes = {
            "expected_answer": " Expected answer: selectedSkill.",
            "skill_name": f" {SKILLS[0]}",
            "internal_token": " architectureResult",
            "router_field": ' {"requestedOperation": "design"}',
            "rubric_token": " result_envelope_complete",
            "contextual_internal_field": ' {"scope": "handoff"}',
            "common_heading": " Include an Activation and Scope section.",
            "workflow_heading": " Include a Findings section.",
            "private_path": " Read /Users/private/customer.txt.",
            "windows_path": r" Read C:\Users\private\customer.txt.",
            "bearer_secret": " Credential: Bearer synthetic-secret-value",
            "api_key": " Credential: sk-synthetic-secret-value",
            "host_identity": " Host identity: joes-macbook-pro",
            "raw_material": " Raw user material: customer-alpha text",
        }
        for name, suffix in suffixes.items():
            with self.subTest(family=name):
                mutant = copy.deepcopy(self.fixture)
                mutant["cases"][5]["prompt"] += suffix
                self.assert_invalid_fixture_rejected_before_use(mutant)

    def test_structural_passes_never_substitute_for_behavioral_failure(self) -> None:
        fixture = _forward_fixture("DEV136-FWD-DESIGN-001")
        process = _FakeHostProcess()
        outputs = _forward_outputs(fixture, activation="fail")
        scorer = _FakeScorer(outputs)
        code, evidence = self.runner.run_host(
            fixture,
            "/opt/codex",
            process,
            _FakePrerequisiteChecker(
                _passing_prerequisites(), _passing_prerequisites()
            ),
            scorer,
        )
        self.assertEqual("pass", evidence["host"]["prerequisites"]["discovery"])
        self.assertEqual("pass", evidence["host"]["prerequisites"]["installation"])
        self.assertEqual(self.runner.FAIL, code)
        self.assertEqual("fail", evidence["status"])
        _assert_forward_evidence_derivations(
            self,
            self.runner,
            fixture,
            outputs,
            evidence,
            host_results=process.results,
            executable_sha256=captured_executable_sha256(),
        )

    def test_cli_writes_evidence_and_returns_real_pass_fail_blocked_exits(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for expected_code, assertion_status in (
                (0, "pass"),
                (1, "fail"),
            ):
                with self.subTest(mode="offline", status=assertion_status):
                    outputs = _forward_outputs(self.fixture)
                    if assertion_status == "fail":
                        first = self.fixture["cases"][0]["id"]
                        outputs[first] = _forward_observation(
                            self.fixture["cases"][0],
                            activation="fail",
                        )
                    scorer_path = root / f"{assertion_status}-scorer.json"
                    scorer_path.write_text(
                        json.dumps(outputs, sort_keys=True),
                        encoding="utf-8",
                    )
                    evidence_path = root / f"{assertion_status}-evidence.json"
                    command = [
                        sys.executable,
                        str(RUNNER_PATH),
                        "--mode",
                        "offline",
                        "--model",
                        "gpt-5.6-sol",
                        "--codex-version",
                        "0.144.5",
                        "--cases",
                        str(FIXTURE_PATH),
                        "--evidence",
                        str(evidence_path),
                        "--scorer-outputs",
                        str(scorer_path),
                    ]
                    completed = subprocess.run(
                        command,
                        cwd=ROOT,
                        capture_output=True,
                        text=True,
                    )
                    self.assertEqual(
                        expected_code,
                        completed.returncode,
                        completed.stderr,
                    )
                    self.assertTrue(evidence_path.is_file())
                    evidence = load_json(evidence_path)
                    self.assertEqual(assertion_status, evidence["status"])
                    _assert_forward_evidence_derivations(
                        self,
                        self.runner,
                        self.fixture,
                        outputs,
                        evidence,
                    )

            for flag, wrong_value, blocker_reason in (
                ("--model", "fallback-model", "model_mismatch"),
                ("--codex-version", "0.144.4", "version_mismatch"),
            ):
                with self.subTest(mode="offline", mismatch=flag):
                    mismatch_evidence = root / f"{flag[2:]}-mismatch-evidence.json"
                    command = [
                        sys.executable,
                        str(RUNNER_PATH),
                        "--mode",
                        "offline",
                        "--model",
                        "gpt-5.6-sol",
                        "--codex-version",
                        "0.144.5",
                        "--cases",
                        str(FIXTURE_PATH),
                        "--evidence",
                        str(mismatch_evidence),
                        "--scorer-outputs",
                        str(root / "pass-scorer.json"),
                    ]
                    command[command.index(flag) + 1] = wrong_value
                    completed = subprocess.run(
                        command,
                        cwd=ROOT,
                        capture_output=True,
                        text=True,
                    )
                    self.assertEqual(2, completed.returncode, completed.stderr)
                    blocked = load_json(mismatch_evidence)
                    self.assertEqual("blocked", blocked["status"])
                    self.assertEqual(0, blocked["summary"]["attemptedCount"])
                    self.assertEqual(
                        blocker_reason,
                        blocked["host"]["blockerReason"],
                    )
                    _assert_forward_evidence_schema(self, blocked)

            host_evidence = root / "blocked-host-evidence.json"
            host_command = [
                sys.executable,
                str(RUNNER_PATH),
                "--mode",
                "host",
                "--model",
                "gpt-5.6-sol",
                "--codex-version",
                "0.144.5",
                "--cases",
                str(FIXTURE_PATH),
                "--evidence",
                str(host_evidence),
            ]
            environment = os.environ.copy()
            environment["CODEX_BIN"] = str(root / "missing-codex")
            completed = subprocess.run(
                host_command,
                cwd=ROOT,
                capture_output=True,
                text=True,
                env=environment,
            )
            self.assertEqual(2, completed.returncode, completed.stderr)
            self.assertTrue(host_evidence.is_file())
            blocked = load_json(host_evidence)
            self.assertEqual("blocked", blocked["status"])
            self.assertEqual("missing_binary", blocked["host"]["blockerReason"])
            _assert_forward_evidence_schema(self, blocked)

    def test_evidence_writer_rejects_recursive_schema_and_privacy_mutations(self) -> None:
        fixture = _forward_fixture(
            "DEV136-FWD-DESIGN-001",
            "DEV136-FWD-REVIEW-001",
        )
        outputs = _forward_outputs(fixture)
        _, evidence = self.runner.run_offline(fixture, outputs)

        def falsify_score(value: dict) -> None:
            value["cases"][0]["assertions"]["activation"] = "fail"
            value["cases"][0]["verdict"] = "fail"
            value["status"] = "fail"
            value["summary"].update({"passedCount": 1, "failedCount": 1})

        mutations = {
            "top_extra": lambda value: value.update({"unexpected": True}),
            "host_missing": lambda value: value["host"].pop("sessionMode"),
            "host_extra": lambda value: value["host"].update({"hostname": "private"}),
            "privacy_drift": lambda value: value["privacy"].update(
                {"rawResponses": "committed"}
            ),
            "summary_bool": lambda value: value["summary"].update(
                {"attemptedCount": True}
            ),
            "summary_negative": lambda value: value["summary"].update(
                {"failedCount": -1}
            ),
            "case_missing": lambda value: value["cases"][0].pop("promptSha256"),
            "case_extra": lambda value: value["cases"][0].update(
                {"rawResponse": "private"}
            ),
            "row_order": lambda value: value["cases"].__setitem__(
                slice(0, 2), list(reversed(value["cases"][:2]))
            ),
            "case_id_drift": lambda value: value["cases"][0].update(
                {"caseId": value["cases"][1]["caseId"]}
            ),
            "skill_drift": lambda value: value["cases"][0].update(
                {"skillUnderTest": SKILLS[1]}
            ),
            "bad_hash": lambda value: value["cases"][0].update(
                {"responseSha256": "not-a-hash"}
            ),
            "arbitrary_response_hash": lambda value: value["cases"][0].update(
                {"responseSha256": "b" * 64}
            ),
            "arbitrary_fixture_hash": lambda value: value.update(
                {"fixtureSha256": "a" * 64}
            ),
            "arbitrary_prompt_hash": lambda value: value["cases"][0].update(
                {"promptSha256": "a" * 64}
            ),
            "arbitrary_rubric_hash": lambda value: value["cases"][0].update(
                {"rubricContractSha256": "a" * 64}
            ),
            "arbitrary_executable_hash": lambda value: value["host"].update(
                {"resolvedExecutableSha256": "a" * 64}
            ),
            "negative_count": lambda value: value["cases"][0].update(
                {"responseBytes": -1}
            ),
            "response_count_drift": lambda value: value["cases"][0].update(
                {"responseBytes": value["cases"][0]["responseBytes"] + 1}
            ),
            "tool_count_drift": lambda value: value["cases"][0].update(
                {"toolEventCount": value["cases"][0]["toolEventCount"] + 1}
            ),
            "codex_exit_drift": lambda value: value["cases"][0].update(
                {"codexExitCode": 0}
            ),
            "unknown_verdict": lambda value: value["cases"][0].update(
                {"verdict": "unknown"}
            ),
            "missing_assertion": lambda value: value["cases"][0][
                "assertions"
            ].pop("routing"),
            "unknown_assertion": lambda value: value["cases"][0][
                "assertions"
            ].update({"routing": "unknown"}),
            "private_value": lambda value: value["host"].update(
                {"blockerReason": "/Users/private/customer.txt"}
            ),
            "changed_assertions_and_verdict": falsify_score,
            "all_pass_under_failed_summary": lambda value: (
                value.update({"status": "fail"}),
                value["summary"].update({"passedCount": 1, "failedCount": 1}),
            ),
            "bucket_swap": lambda value: value["summary"].update(
                {"passedCount": 1, "blockedCount": 1}
            ),
            "attempted_count_drift": lambda value: value["summary"].update(
                {"attemptedCount": 3}
            ),
            "fixture_count_drift": lambda value: value["summary"].update(
                {"fixtureCaseCount": 3}
            ),
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.json"
            path.write_text("old-evidence", encoding="utf-8")
            for name, mutate in mutations.items():
                with self.subTest(mutation=name):
                    mutant = copy.deepcopy(evidence)
                    mutate(mutant)
                    with self.assertRaises(ValueError):
                        _write_bound_evidence(
                            self.runner,
                            path,
                            mutant,
                            fixture,
                            outputs,
                        )
                    self.assertEqual(
                        "old-evidence",
                        path.read_text(encoding="utf-8"),
                    )

    def test_evidence_writer_is_closed_atomic_and_failure_safe(self) -> None:
        fixture = _forward_fixture("DEV136-FWD-DESIGN-001")
        outputs = _forward_outputs(fixture)
        _, evidence = self.runner.run_offline(fixture, outputs)
        _assert_forward_evidence_derivations(
            self,
            self.runner,
            fixture,
            outputs,
            evidence,
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "evidence.json"
            path.write_text("stale", encoding="utf-8")
            _write_bound_evidence(
                self.runner,
                path,
                evidence,
                fixture,
                outputs,
            )
            self.assertEqual(evidence, load_json(path))
            self.assertEqual([path], list(root.iterdir()))

            mutant = {**evidence, "rawResponse": "private"}
            with self.assertRaises(ValueError):
                _write_bound_evidence(
                    self.runner,
                    path,
                    mutant,
                    fixture,
                    outputs,
                )

            for operation in ("stage", "fsync", "replace"):
                with self.subTest(operation=operation):
                    failure_root = root / operation
                    failure_root.mkdir()
                    destination = failure_root / "evidence.json"
                    destination.write_text("old-evidence", encoding="utf-8")
                    with self.assertRaises(OSError):
                        _write_bound_evidence(
                            self.runner,
                            destination,
                            evidence,
                            fixture,
                            outputs,
                            fault_hook=_AtomicFault(operation),
                        )
                    self.assertEqual(
                        "old-evidence",
                        destination.read_text(encoding="utf-8"),
                    )
                    self.assertEqual([destination], list(failure_root.iterdir()))

            target = root / "private-target"
            target.write_text("private", encoding="utf-8")
            symlink = root / "symlink-evidence.json"
            symlink.symlink_to(target)
            with self.assertRaises((OSError, ValueError)):
                _write_bound_evidence(
                    self.runner,
                    symlink,
                    evidence,
                    fixture,
                    outputs,
                )
            self.assertEqual("private", target.read_text(encoding="utf-8"))

            directory_target = root / "directory-target"
            directory_target.mkdir()
            with self.assertRaises((OSError, ValueError)):
                _write_bound_evidence(
                    self.runner,
                    directory_target,
                    evidence,
                    fixture,
                    outputs,
                )

            real_parent = root / "real-parent"
            real_parent.mkdir()
            linked_parent = root / "linked-parent"
            linked_parent.symlink_to(real_parent, target_is_directory=True)
            with self.assertRaises((OSError, ValueError)):
                _write_bound_evidence(
                    self.runner,
                    linked_parent / "evidence.json",
                    evidence,
                    fixture,
                    outputs,
                )
            self.assertEqual([], list(real_parent.iterdir()))

            nonregular_parent = root / "nonregular-parent"
            nonregular_parent.write_text("not a directory", encoding="utf-8")
            with self.assertRaises((OSError, ValueError, NotADirectoryError)):
                _write_bound_evidence(
                    self.runner,
                    nonregular_parent / "evidence.json",
                    evidence,
                    fixture,
                    outputs,
                )


if __name__ == "__main__":
    unittest.main()
