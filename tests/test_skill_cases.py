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
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests/fixtures/dev-136-codex-skill-cases.json"
EVIDENCE_PATH = ROOT / "docs/research/evidence/dev-136-codex-skill-tdd.json"
PROTOTYPE_PATH = ROOT / "docs/research/evidence/dev-134-activation-prototype.json"
RUNNER_PATH = ROOT / "tests/e2e/codex_skill_forward_tests.py"
PLUGIN_LOAD_PATH = ROOT / "tests/e2e/codex_plugin_load.py"
TEST_EXECUTABLE_PATH = Path(sys.executable).resolve()

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

INITIAL_CAPTURE_HEAD = "e2a0fb7edfc649be1c95aef2ebfd9fedd38dc87f"
REVIEW_RECAPTURE_HEAD = "fbbec6fa30c02ffba2e604e5e21cacf71de73b4e"

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
FORWARD_EARLY_STOP_REASONS = {
    "event_stream_invalid",
    "post_capture_prerequisite_drift",
    "process_failed",
    "scoring_failed",
}
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
    "resolvedExecutable",
    "response",
    "transcript",
}
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
OFFICIAL_FIXTURE_SHA256 = (
    "6c5bd8dafb1b75990e88ec288de18282c00b99151f33a7566253395c4ef93dcb"
)


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


def load_plugin_load_probe():
    if not PLUGIN_LOAD_PATH.is_file():
        raise AssertionError(
            "DEV-136 RED: tests/e2e/codex_plugin_load.py is absent"
        )
    spec = importlib.util.spec_from_file_location(
        "codex_plugin_load_contract", PLUGIN_LOAD_PATH
    )
    if spec is None or spec.loader is None:
        raise AssertionError("DEV-136 RED: plugin-load probe cannot be imported")
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


def fixture_bytes_sha256(fixture_bytes: bytes) -> str:
    return sha256_bytes(fixture_bytes)


def deterministic_fixture_bytes(fixture: dict) -> bytes:
    return (
        json.dumps(fixture, ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")


def executable_bytes_sha256(path: Path = TEST_EXECUTABLE_PATH) -> str:
    return sha256_bytes(path.read_bytes())


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


def _run_offline(
    runner,
    fixture: dict,
    scorer_outputs: dict[str, dict],
    fixture_bytes: bytes | None = None,
):
    return runner.run_offline(
        fixture,
        scorer_outputs,
        fixture_bytes=(
            deterministic_fixture_bytes(fixture)
            if fixture_bytes is None
            else fixture_bytes
        ),
    )


def _run_host(
    runner,
    fixture: dict,
    executable: str,
    process_runner,
    prerequisite_checker,
    scorer,
    fixture_bytes: bytes | None = None,
):
    return runner.run_host(
        fixture,
        executable,
        process_runner,
        prerequisite_checker,
        scorer,
        fixture_bytes=(
            deterministic_fixture_bytes(fixture)
            if fixture_bytes is None
            else fixture_bytes
        ),
    )


def _passing_prerequisites(executable: str | None = None) -> dict:
    path = Path(executable) if executable is not None else TEST_EXECUTABLE_PATH
    return {
        "resolvedExecutable": str(path),
        "executableSha256": executable_bytes_sha256(path),
        "version": "0.144.5",
        "authenticated": True,
        "modelAvailable": True,
        "pluginAvailable": True,
        "discovery": "pass",
        "installation": "pass",
    }


def _codex_usage() -> dict[str, int]:
    return {
        "input_tokens": 11,
        "cached_input_tokens": 2,
        "output_tokens": 7,
        "reasoning_output_tokens": 3,
    }


def _codex_command_item(
    *,
    item_id: str = "item_0",
    command: str = "synthetic-command",
    aggregated_output: str = "",
    exit_code: int | None = None,
    status: str = "in_progress",
) -> dict:
    return {
        "id": item_id,
        "type": "command_execution",
        "command": command,
        "aggregated_output": aggregated_output,
        "exit_code": exit_code,
        "status": status,
    }


def _canonical_codex_jsonl() -> str:
    events = (
        {"type": "thread.started", "thread_id": "thread_synthetic"},
        {"type": "turn.started"},
        {"type": "item.started", "item": _codex_command_item()},
        {
            "type": "item.completed",
            "item": _codex_command_item(
                aggregated_output="synthetic output",
                exit_code=0,
                status="completed",
            ),
        },
        {"type": "turn.completed", "usage": _codex_usage()},
    )
    return "\n".join(json.dumps(event, sort_keys=True) for event in events)


def _build_forward_plugin_tree(repo_root: Path) -> tuple[Path, dict]:
    plugin_root = repo_root / "plugins/apple-foundation-models-handoff"
    manifest_path = plugin_root / ".codex-plugin/plugin.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(
        json.dumps(
            {
                "name": "apple-foundation-models-handoff",
                "interface": {"capabilities": list(WORKFLOW_SECTIONS)},
            }
        ),
        encoding="utf-8",
    )
    for skill in SKILLS:
        target = plugin_root / "skills" / skill / "SKILL.md"
        target.parent.mkdir(parents=True)
        target.write_bytes(
            (
                ROOT
                / "plugins/apple-foundation-models-handoff/skills"
                / skill
                / "SKILL.md"
            ).read_bytes()
        )
    entry = {
        "pluginId": (
            "apple-foundation-models-handoff@"
            "agent-apple-foundation-handoff"
        ),
        "name": "apple-foundation-models-handoff",
        "marketplaceName": "agent-apple-foundation-handoff",
        "version": "0.1.0",
        "installed": True,
        "enabled": True,
        "source": {"source": "local", "path": str(plugin_root)},
        "marketplaceSource": {
            "sourceType": "local",
            "source": str(repo_root),
        },
        "installPolicy": "AVAILABLE",
        "authPolicy": "ON_INSTALL",
    }
    return plugin_root, {"installed": [entry], "available": []}


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
    fixture_bytes: bytes | None = None,
    host_results: list[dict] | None = None,
    executable_sha256: str | None = None,
) -> None:
    _assert_forward_evidence_schema(test, evidence)
    if fixture_bytes is None:
        fixture_bytes = deterministic_fixture_bytes(fixture)
    test.assertEqual(fixture_bytes_sha256(fixture_bytes), evidence["fixtureSha256"])
    rows = evidence["cases"]
    blocker_reason = evidence["host"]["blockerReason"]
    if evidence["mode"] == "offline" or blocker_reason is None:
        test.assertEqual(len(fixture["cases"]), len(rows))
    elif len(rows) < len(fixture["cases"]):
        test.assertNotEqual("pass", evidence["status"])
        test.assertIn(blocker_reason, FORWARD_EARLY_STOP_REASONS)
    else:
        test.assertEqual(len(fixture["cases"]), len(rows))
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
    if len(rows) < len(fixture["cases"]):
        test.assertIn(evidence["status"], {"fail", "blocked"})
        test.assertIn(blocker_reason, FORWARD_EARLY_STOP_REASONS)
    else:
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
    fixture_bytes: bytes | None = None,
    host_results: list[dict] | None = None,
    executable_sha256: str | None = None,
    fault_hook=None,
) -> None:
    if fixture_bytes is None:
        fixture_bytes = deterministic_fixture_bytes(fixture)
    runner.write_evidence(
        path,
        evidence,
        fixture=fixture,
        fixture_bytes=fixture_bytes,
        scorer_outputs=scorer_outputs,
        host_results=host_results,
        executable_sha256=executable_sha256,
        fault_hook=fault_hook,
    )


class CodexPluginLoadContractTests(unittest.TestCase):
    EXPECTED_FILES = {
        ".claude-plugin/plugin.json",
        ".codex-plugin/plugin.json",
        "metadata/codex-interface.json",
        "references/apple-api-availability.md",
        "references/architecture-and-state.md",
        "references/evaluation-and-observability.md",
        "references/orchestration-patterns.md",
        "references/security-context-and-recovery.md",
        "skills/design-apple-foundation-models-handoff/SKILL.md",
        "skills/implement-apple-foundation-models-handoff/SKILL.md",
        "skills/review-apple-foundation-models-handoff/SKILL.md",
        "skills/debug-apple-foundation-models-handoff/SKILL.md",
        "skills/validate-apple-foundation-models-handoff/SKILL.md",
    }
    EXPECTED_DIRECTORIES = {
        ".claude-plugin",
        ".codex-plugin",
        "metadata",
        "references",
        "skills",
        "skills/design-apple-foundation-models-handoff",
        "skills/implement-apple-foundation-models-handoff",
        "skills/review-apple-foundation-models-handoff",
        "skills/debug-apple-foundation-models-handoff",
        "skills/validate-apple-foundation-models-handoff",
    }

    @classmethod
    def setUpClass(cls) -> None:
        cls.probe_module = load_plugin_load_probe()

    def _write_payload(
        self,
        root: Path,
        files: set[str],
        capabilities: list[str] | None = None,
    ) -> None:
        for relative_path in files:
            target = root / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            if relative_path == ".codex-plugin/plugin.json":
                target.write_text(
                    json.dumps(
                        {
                            "name": "apple-foundation-models-handoff",
                            "interface": {
                                "capabilities": capabilities or [],
                            },
                        }
                    ),
                    encoding="utf-8",
                )
            else:
                target.write_bytes((relative_path + "\n").encode("utf-8"))

    def _run_probe_without_host_io(self) -> dict:
        module = self.probe_module
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository = root / "repository"
            source = repository / "plugins/apple-foundation-models-handoff"
            codex_home = root / "codex-home"
            installed = codex_home / "cache/apple-foundation-models-handoff"
            codex_home.mkdir()
            declared_files = set(module.EXPECTED_CACHE_FILES)
            declared_capabilities = list(SKILLS)
            self._write_payload(source, declared_files, declared_capabilities)
            self._write_payload(installed, declared_files, declared_capabilities)

            def entry(*, installed_state: bool, enabled: bool) -> dict:
                return {
                    "pluginId": module.SELECTOR,
                    "name": module.PLUGIN_ID,
                    "marketplaceName": module.MARKETPLACE,
                    "version": module.PLUGIN_VERSION,
                    "installed": installed_state,
                    "enabled": enabled,
                    "source": {"source": "local", "path": str(source)},
                    "marketplaceSource": {
                        "sourceType": "local",
                        "source": str(repository),
                    },
                    "installPolicy": "AVAILABLE",
                    "authPolicy": "ON_INSTALL",
                }

            responses = iter(
                (
                    {
                        "marketplaceName": module.MARKETPLACE,
                        "installedRoot": str(repository),
                        "alreadyAdded": False,
                    },
                    {
                        "installed": [],
                        "available": [
                            entry(installed_state=False, enabled=False)
                        ],
                    },
                    {
                        "pluginId": module.SELECTOR,
                        "name": module.PLUGIN_ID,
                        "marketplaceName": module.MARKETPLACE,
                        "version": module.PLUGIN_VERSION,
                        "authPolicy": "ON_INSTALL",
                        "installedPath": str(installed),
                    },
                    {
                        "installed": [
                            entry(installed_state=True, enabled=True)
                        ],
                        "available": [],
                    },
                )
            )
            temporary_home = mock.MagicMock()
            temporary_home.__enter__.return_value = str(codex_home)
            temporary_home.__exit__.return_value = False
            executable = Path(sys.executable).resolve(strict=True)
            production_require = module.require

            def require_except_superseded_capability_check(
                condition: bool, reason: str
            ) -> None:
                if reason != "capabilities_not_empty":
                    production_require(condition, reason)

            with (
                mock.patch.object(module, "ROOT", repository),
                mock.patch.object(module, "PLUGIN_ROOT", source),
                mock.patch.object(
                    module.tempfile,
                    "TemporaryDirectory",
                    return_value=temporary_home,
                ),
                mock.patch.object(module, "run_json", side_effect=responses),
                mock.patch.object(module, "exact_version", return_value=True),
                mock.patch.object(
                    module,
                    "require",
                    side_effect=require_except_superseded_capability_check,
                ),
            ):
                return module.probe(str(executable), executable, executable)

    def test_plugin_load_accepts_exact_combined_approved_package_closure(
        self,
    ) -> None:
        module = self.probe_module
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write_payload(root, self.EXPECTED_FILES, list(SKILLS))
            self.assertEqual(
                self.EXPECTED_DIRECTORIES,
                {
                    path.relative_to(root).as_posix()
                    for path in root.rglob("*")
                    if path.is_dir()
                },
            )
            try:
                observed = module.scan_payload(
                    root, "approved_payload_contract_mismatch"
                )
            except module.ProbeFailure as failure:
                self.fail(f"exact approved payload rejected: {failure.reason}")
            self.assertEqual(self.EXPECTED_FILES, observed)

    def test_plugin_load_rejects_unapproved_or_nonregular_topology(self) -> None:
        module = self.probe_module
        for mutation in ("extra_file", "extra_directory", "symlink"):
            with self.subTest(mutation=mutation):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    self._write_payload(root, self.EXPECTED_FILES, list(SKILLS))
                    if mutation == "extra_file":
                        (root / "EXTRA.md").write_text(
                            "unapproved\n", encoding="utf-8"
                        )
                    elif mutation == "extra_directory":
                        (root / "unapproved-empty-directory").mkdir()
                    else:
                        target = root / (
                            "skills/design-apple-foundation-models-handoff/"
                            "SKILL.md"
                        )
                        target.unlink()
                        target.symlink_to(root / ".codex-plugin/plugin.json")
                    with self.assertRaises(module.ProbeFailure):
                        module.scan_payload(
                            root, "approved_payload_contract_mismatch"
                        )

    def test_plugin_load_reports_exact_ordered_capabilities(self) -> None:
        result = self._run_probe_without_host_io()
        self.assertEqual(list(SKILLS), result["capabilities"])

    def test_plugin_load_reports_forward_runner_activation_ownership(self) -> None:
        result = self._run_probe_without_host_io()
        self.assertEqual(
            "not_applicable/behavior_owned_by_forward_runner",
            result["capabilityActivation"],
        )

    def test_plugin_load_json_accepts_valid_and_rejects_duplicate_keys(self) -> None:
        module = self.probe_module
        self.assertEqual(
            {"finite": [0, 1.5, -2]},
            module.parse_json_object(
                b'{"finite":[0,1.5,-2]}', "strict_json_required"
            ),
        )
        with self.assertRaises(module.ProbeFailure):
            module.parse_json_object(
                b'{"duplicate":0,"duplicate":1}',
                "strict_json_required",
            )

    def test_plugin_load_json_rejects_nonfinite_constants(self) -> None:
        module = self.probe_module
        for constant in (b"NaN", b"Infinity", b"-Infinity"):
            with self.subTest(constant=constant.decode("ascii")):
                with self.assertRaises(module.ProbeFailure):
                    module.parse_json_object(
                        b'{"nonfinite":' + constant + b"}",
                        "strict_json_required",
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
        jsonl = _canonical_codex_jsonl()
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


def _canonical_live_response(
    case: dict,
    *,
    state_version: str = "state-v1",
    policy_version: str = "policy-v1",
    review_boundary: str = "A separate authorized follow-on boundary is required.",
) -> bytes:
    router = case["routerInput"]
    machine = [
        "activationStatus = activated",
        f"selectedSkill = {case['skillUnderTest']}",
        (
            "routerInput = { "
            f"domain = {router['domain']}, "
            f"requestedOperation: {router['requestedOperation']}, "
            f"artifactState = {router['artifactState']}, "
            f"evidenceState: {router['evidenceState']} "
            "}"
        ),
        "architectureResult",
        '  architectureSchemaVersion: "1.0"',
        f'  stateVersion: "{state_version}"',
        f'  policyVersion: "{policy_version}"',
        "  workflow: review",
        "  scope: synthetic implementation",
        "  pattern = baton_pass",
        "  source = { profile: source, provider: apple_on_device }",
        "  destination = { profile: review, provider: apple_on_device }",
        "  finalResponseOwner: review",
        "  apiAvailability[] = []",
        "  stateModel: deterministic",
        "  trustBoundaries[]: [model_to_application]",
        "  contextPolicy: minimized",
        "  toolAndEffectPolicy: application_owned",
        "  failurePolicy: fail_closed",
        "  verification[] = [pass]",
        "  limitations[]: []",
    ]
    sections = [
        *(f"## {heading}\nBounded result." for heading in COMMON_SECTIONS),
        "## Findings\n" + review_boundary,
    ]
    return (
        "```text\n"
        + "\n".join(machine)
        + "\n```\n\n"
        + "\n\n".join(sections)
        + "\n"
    ).encode("utf-8")


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
        checker = _FakePrerequisiteChecker(_passing_prerequisites())
        code, evidence = _run_host(
            self.runner,
            fixture,
            str(TEST_EXECUTABLE_PATH),
            process,
            checker,
            scorer,
        )

        self.assertEqual(self.runner.PASS, code)
        self.assertEqual(["execute", "score"], timeline)
        self.assertEqual([fixture["cases"][0]["prompt"]], process.inputs)
        command = process.commands[0]
        self.assertEqual([str(TEST_EXECUTABLE_PATH), "exec"], command[:2])
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
            executable_sha256=executable_bytes_sha256(),
        )

    def test_executable_capture_hashes_real_regular_bytes_and_rejects_indirection(self) -> None:
        self.assertTrue(TEST_EXECUTABLE_PATH.is_file())
        self.assertFalse(TEST_EXECUTABLE_PATH.is_symlink())
        captured = self.runner.capture_executable(str(TEST_EXECUTABLE_PATH))
        self.assertEqual(str(TEST_EXECUTABLE_PATH), captured["resolvedExecutable"])
        self.assertEqual(
            executable_bytes_sha256(),
            captured["executableSha256"],
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            linked = root / "linked-executable"
            linked.symlink_to(TEST_EXECUTABLE_PATH)
            with self.assertRaises((OSError, ValueError)):
                self.runner.capture_executable(str(linked))

            nonregular = root / "directory-executable"
            nonregular.mkdir()
            with self.assertRaises((OSError, ValueError)):
                self.runner.capture_executable(str(nonregular))

            replaced = root / "replaceable-executable"
            replaced.write_bytes(TEST_EXECUTABLE_PATH.read_bytes())
            replaced.chmod(0o700)
            before = self.runner.capture_executable(str(replaced))
            replaced.write_bytes(replaced.read_bytes() + b"replaced")
            replaced.chmod(0o700)
            after = self.runner.capture_executable(str(replaced))
            self.assertEqual(executable_bytes_sha256(replaced), after["executableSha256"])
            self.assertNotEqual(
                before["executableSha256"],
                after["executableSha256"],
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
                code, evidence = _run_offline(self.runner, fixture, outputs)
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
        code, evidence = _run_offline(self.runner, aggregate, outputs)
        self.assertEqual(self.runner.FAIL, code)
        self.assertEqual("fail", evidence["status"])
        _assert_forward_evidence_derivations(
            self,
            self.runner,
            aggregate,
            outputs,
            evidence,
        )

    def test_dict_mode_hashes_exact_supplied_fixture_bytes_not_reserialization(self) -> None:
        self.assertEqual(
            OFFICIAL_FIXTURE_SHA256,
            fixture_bytes_sha256(FIXTURE_PATH.read_bytes()),
        )
        fixture = _forward_fixture("DEV136-FWD-DESIGN-001")
        outputs = _forward_outputs(fixture)
        pretty_bytes = deterministic_fixture_bytes(fixture)
        compact_bytes = (
            json.dumps(
                fixture,
                ensure_ascii=False,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("utf-8")
        self.assertEqual(json.loads(pretty_bytes), json.loads(compact_bytes))
        self.assertNotEqual(
            fixture_bytes_sha256(pretty_bytes),
            fixture_bytes_sha256(compact_bytes),
        )
        for fixture_bytes in (pretty_bytes, compact_bytes):
            with self.subTest(bytes_sha256=fixture_bytes_sha256(fixture_bytes)):
                code, evidence = _run_offline(
                    self.runner,
                    fixture,
                    outputs,
                    fixture_bytes,
                )
                self.assertEqual(self.runner.PASS, code)
                self.assertEqual(
                    fixture_bytes_sha256(fixture_bytes),
                    evidence["fixtureSha256"],
                )

        mismatched = copy.deepcopy(fixture)
        mismatched["cases"][0]["prompt"] += " mismatched bytes"
        code, _ = _run_offline(
            self.runner,
            fixture,
            outputs,
            deterministic_fixture_bytes(mismatched),
        )
        self.assertEqual(self.runner.FAIL, code)

    def test_host_uses_fresh_processes_and_pre_post_checks_per_case(self) -> None:
        fixture = _forward_fixture(
            "DEV136-FWD-DESIGN-001", "DEV136-FWD-REVIEW-001"
        )
        timeline: list[str] = []
        process = _FakeHostProcess(timeline=timeline)
        outputs = _forward_outputs(fixture)
        scorer = _FakeScorer(outputs, timeline)
        checker = _FakePrerequisiteChecker(_passing_prerequisites())

        code, evidence = _run_host(
            self.runner,
            fixture,
            str(TEST_EXECUTABLE_PATH),
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
            [(str(TEST_EXECUTABLE_PATH), "gpt-5.6-sol", "0.144.5")] * 4,
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
            executable_sha256=executable_bytes_sha256(),
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
                code, evidence = _run_host(
                    self.runner,
                    fixture,
                    str(TEST_EXECUTABLE_PATH),
                    process,
                    checker,
                    scorer,
                )
                self.assertEqual(self.runner.BLOCKED, code)
                self.assertEqual([], process.commands)
                self.assertEqual([], scorer.calls)
                self.assertEqual(1, len(checker.calls))
                self.assertEqual([], evidence["cases"])
                self.assertEqual(0, evidence["summary"]["attemptedCount"])
                self.assertEqual("blocked", evidence["status"])
                self.assertEqual(reason, evidence["host"]["blockerReason"])
                self.assertEqual(
                    None if reason == "missing_binary" else executable_bytes_sha256(),
                    evidence["host"]["resolvedExecutableSha256"],
                )
                _assert_forward_evidence_schema(self, evidence)

    def test_post_capture_prerequisite_drift_fails_and_stops_without_retry(self) -> None:
        fixture = _forward_fixture(
            "DEV136-FWD-DESIGN-001", "DEV136-FWD-REVIEW-001"
        )
        post_mutations = {
            "resolved_path": {
                "resolvedExecutable": str(
                    TEST_EXECUTABLE_PATH.with_name("replaced-codex")
                )
            },
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
                outputs = _forward_outputs(fixture)
                scorer = _FakeScorer(outputs)
                checker = _FakePrerequisiteChecker(_passing_prerequisites(), post)
                code, evidence = _run_host(
                    self.runner,
                    fixture,
                    str(TEST_EXECUTABLE_PATH),
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
                self.assertEqual([], evidence["cases"])
                _assert_forward_evidence_derivations(
                    self,
                    self.runner,
                    fixture,
                    outputs,
                    evidence,
                    host_results=process.results,
                    executable_sha256=executable_bytes_sha256(),
                )

        second_post = _passing_prerequisites()
        second_post.update({"pluginAvailable": False})
        process = _FakeHostProcess()
        outputs = _forward_outputs(fixture)
        scorer = _FakeScorer(outputs)
        checker = _FakePrerequisiteChecker(
            _passing_prerequisites(),
            _passing_prerequisites(),
            _passing_prerequisites(),
            second_post,
        )
        code, evidence = _run_host(
            self.runner,
            fixture,
            str(TEST_EXECUTABLE_PATH),
            process,
            checker,
            scorer,
        )
        self.assertEqual(self.runner.FAIL, code)
        self.assertEqual(2, len(process.commands))
        self.assertEqual(4, len(checker.calls))
        self.assertEqual([fixture["cases"][0]["id"]], scorer.calls)
        self.assertTrue(all(not path.exists() for path in process.output_paths))
        self.assertEqual(
            [fixture["cases"][0]["id"]],
            [row["caseId"] for row in evidence["cases"]],
        )
        _assert_forward_evidence_derivations(
            self,
            self.runner,
            fixture,
            outputs,
            evidence,
            host_results=process.results,
            executable_sha256=executable_bytes_sha256(),
        )

        fixture = _forward_fixture("DEV136-FWD-DESIGN-001")
        process = _FakeHostProcess(returncodes=[7])
        outputs = _forward_outputs(fixture)
        scorer = _FakeScorer(outputs)
        checker = _FakePrerequisiteChecker(_passing_prerequisites())
        code, evidence = _run_host(
            self.runner,
            fixture,
            str(TEST_EXECUTABLE_PATH),
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
        self.assertEqual([], evidence["cases"])
        _assert_forward_evidence_derivations(
            self,
            self.runner,
            fixture,
            outputs,
            evidence,
            host_results=process.results,
            executable_sha256=executable_bytes_sha256(),
        )

    def test_scorer_failure_cleans_raw_response_and_returns_stable_failure(self) -> None:
        fixture = _forward_fixture("DEV136-FWD-DESIGN-001")
        process = _FakeHostProcess()
        outputs = _forward_outputs(fixture)
        scorer = _FakeScorer(
            outputs,
            error=RuntimeError("injected scorer failure"),
        )
        checker = _FakePrerequisiteChecker(_passing_prerequisites())
        code, evidence = _run_host(
            self.runner,
            fixture,
            str(TEST_EXECUTABLE_PATH),
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
        self.assertEqual([], evidence["cases"])
        _assert_forward_evidence_derivations(
            self,
            self.runner,
            fixture,
            outputs,
            evidence,
            host_results=process.results,
            executable_sha256=executable_bytes_sha256(),
        )

    def test_host_hashes_and_discards_raw_private_response_content(self) -> None:
        fixture = _forward_fixture("DEV136-FWD-DESIGN-001")
        case = fixture["cases"][0]
        raw = b"Bearer synthetic-private-secret from /Users/private/customer.txt"
        process = _FakeHostProcess(responses=[raw])
        outputs = _forward_outputs(fixture)
        scorer = _FakeScorer(outputs)
        code, evidence = _run_host(
            self.runner,
            fixture,
            str(TEST_EXECUTABLE_PATH),
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
            executable_sha256=executable_bytes_sha256(),
        )

    def assert_invalid_fixture_rejected_before_use(self, fixture: dict) -> None:
        offline_code, _ = _run_offline(
            self.runner,
            fixture,
            _ExplodingScorerOutputs(),
        )
        self.assertEqual(self.runner.FAIL, offline_code)

        process = _FakeHostProcess()
        scorer = _FakeScorer({})
        host_code, _ = _run_host(
            self.runner,
            fixture,
            str(TEST_EXECUTABLE_PATH),
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
        code, evidence = _run_host(
            self.runner,
            fixture,
            str(TEST_EXECUTABLE_PATH),
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
            executable_sha256=executable_bytes_sha256(),
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
                    self.assertEqual(
                        OFFICIAL_FIXTURE_SHA256,
                        evidence["fixtureSha256"],
                    )
                    _assert_forward_evidence_derivations(
                        self,
                        self.runner,
                        self.fixture,
                        outputs,
                        evidence,
                        fixture_bytes=FIXTURE_PATH.read_bytes(),
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

            linked_codex = root / "linked-codex"
            linked_codex.symlink_to(TEST_EXECUTABLE_PATH)
            linked_evidence = root / "linked-host-evidence.json"
            linked_command = list(host_command)
            linked_command[linked_command.index("--evidence") + 1] = str(
                linked_evidence
            )
            environment["CODEX_BIN"] = str(linked_codex)
            completed = subprocess.run(
                linked_command,
                cwd=ROOT,
                capture_output=True,
                text=True,
                env=environment,
            )
            self.assertEqual(2, completed.returncode, completed.stderr)
            linked_blocked = load_json(linked_evidence)
            self.assertEqual("blocked", linked_blocked["status"])
            self.assertEqual(
                "nonregular_binary",
                linked_blocked["host"]["blockerReason"],
            )
            self.assertIsNone(
                linked_blocked["host"]["resolvedExecutableSha256"]
            )

    def test_host_writer_binds_normalized_process_measurements_without_raw_payloads(self) -> None:
        fixture = _forward_fixture(
            "DEV136-FWD-DESIGN-001",
            "DEV136-FWD-REVIEW-001",
        )
        fixture_bytes = deterministic_fixture_bytes(fixture)
        outputs = _forward_outputs(fixture)
        process = _FakeHostProcess(
            responses=[b"approved response one", b"approved response two"]
        )
        evidence_code, evidence = _run_host(
            self.runner,
            fixture,
            str(TEST_EXECUTABLE_PATH),
            process,
            _FakePrerequisiteChecker(_passing_prerequisites()),
            _FakeScorer(outputs),
            fixture_bytes,
        )
        self.assertEqual(self.runner.PASS, evidence_code)
        _assert_forward_evidence_derivations(
            self,
            self.runner,
            fixture,
            outputs,
            evidence,
            fixture_bytes=fixture_bytes,
            host_results=process.results,
            executable_sha256=executable_bytes_sha256(),
        )
        self.assertTrue(
            all(
                set(result)
                == {
                    "codexExitCode",
                    "responseSha256",
                    "responseBytes",
                    "toolEventCount",
                }
                for result in process.results
            )
        )

        mutations = {
            "codex_exit": lambda value: value["cases"][0].update(
                {"codexExitCode": 9}
            ),
            "response_hash": lambda value: value["cases"][0].update(
                {"responseSha256": "c" * 64}
            ),
            "response_bytes": lambda value: value["cases"][0].update(
                {"responseBytes": value["cases"][0]["responseBytes"] + 1}
            ),
            "tool_events": lambda value: value["cases"][0].update(
                {"toolEventCount": value["cases"][0]["toolEventCount"] + 1}
            ),
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "host-evidence.json"
            path.write_text("old-host-evidence", encoding="utf-8")
            _write_bound_evidence(
                self.runner,
                path,
                evidence,
                fixture,
                outputs,
                fixture_bytes=fixture_bytes,
                host_results=process.results,
                executable_sha256=executable_bytes_sha256(),
            )
            self.assertEqual(evidence, load_json(path))

            for name, mutate in mutations.items():
                with self.subTest(mutation=name):
                    path.write_text("old-host-evidence", encoding="utf-8")
                    mutant = copy.deepcopy(evidence)
                    mutate(mutant)
                    with self.assertRaises(ValueError):
                        _write_bound_evidence(
                            self.runner,
                            path,
                            mutant,
                            fixture,
                            outputs,
                            fixture_bytes=fixture_bytes,
                            host_results=process.results,
                            executable_sha256=executable_bytes_sha256(),
                        )
                    self.assertEqual(
                        "old-host-evidence",
                        path.read_text(encoding="utf-8"),
                    )

    def test_evidence_writer_rejects_recursive_schema_and_privacy_mutations(self) -> None:
        fixture = _forward_fixture(
            "DEV136-FWD-DESIGN-001",
            "DEV136-FWD-REVIEW-001",
        )
        outputs = _forward_outputs(fixture)
        _, evidence = _run_offline(self.runner, fixture, outputs)

        def falsify_score(value: dict) -> None:
            value["cases"][0]["assertions"]["activation"] = "fail"
            value["cases"][0]["verdict"] = "fail"
            value["status"] = "fail"
            value["summary"].update({"passedCount": 1, "failedCount": 1})

        def drop_trailing_pass_row(value: dict) -> None:
            value["cases"].pop()
            value["summary"].update(
                {
                    "attemptedCount": 1,
                    "passedCount": 1,
                }
            )

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
            "incomplete_pass_bundle": drop_trailing_pass_row,
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
        _, evidence = _run_offline(self.runner, fixture, outputs)
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
            old_inode = path.stat().st_ino
            _write_bound_evidence(
                self.runner,
                path,
                evidence,
                fixture,
                outputs,
            )
            new_inode = path.stat().st_ino
            if old_inode == 0 or new_inode == 0:
                self.skipTest("filesystem does not expose stable inode identity")
            self.assertNotEqual(old_inode, new_inode)
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

    def test_live_score_accepts_mixed_delimiters_and_rejects_placeholders_or_negated_review_boundary(self) -> None:
        case = _forward_fixture("DEV136-FWD-REVIEW-001")["cases"][0]
        expected_positive = _forward_assertions(one_clarification="not_applicable")

        with self.subTest(boundary="canonical_mixed_delimiters"):
            observation = self.runner.live_score(
                case,
                _canonical_live_response(case),
                [],
            )
            self.assertEqual(expected_positive, observation["assertions"])

        for placeholder in ("not_specified", "unchanged_existing_version"):
            with self.subTest(boundary="version_placeholder", value=placeholder):
                observation = self.runner.live_score(
                    case,
                    _canonical_live_response(
                        case,
                        state_version=placeholder,
                        policy_version=placeholder,
                    ),
                    [],
                )
                self.assertEqual(
                    "fail",
                    observation["assertions"]["independent_version_labels"],
                )

        with self.subTest(boundary="negated_follow_on_authority"):
            observation = self.runner.live_score(
                case,
                _canonical_live_response(
                    case,
                    review_boundary=(
                        "There is no separate authorized follow-on boundary."
                    ),
                ),
                [],
            )
            self.assertEqual(
                "fail",
                observation["assertions"]["review_first_ordering"],
            )

    def test_paths_reject_ancestor_symlinks_and_execution_is_bound_to_captured_identity(self) -> None:
        fixture = _forward_fixture("DEV136-FWD-DESIGN-001")
        outputs = _forward_outputs(fixture)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            with self.subTest(boundary="executable_ancestor_symlink"):
                real_parent = root / "real-executable-parent"
                real_parent.mkdir()
                executable = real_parent / "codex"
                executable.write_bytes(b"#!/bin/sh\nexit 0\n")
                executable.chmod(0o700)
                linked_parent = root / "linked-executable-parent"
                linked_parent.symlink_to(real_parent, target_is_directory=True)
                with self.assertRaises((OSError, ValueError)):
                    self.runner.capture_executable(
                        str(linked_parent / executable.name)
                    )

            with self.subTest(boundary="evidence_ancestor_symlink"):
                _, evidence = _run_offline(self.runner, fixture, outputs)
                real_parent = root / "real-evidence-parent"
                nested = real_parent / "nested"
                nested.mkdir(parents=True)
                linked_parent = root / "linked-evidence-parent"
                linked_parent.symlink_to(real_parent, target_is_directory=True)
                destination = linked_parent / "nested/evidence.json"
                with self.assertRaises((OSError, ValueError)):
                    _write_bound_evidence(
                        self.runner,
                        destination,
                        evidence,
                        fixture,
                        outputs,
                    )
                self.assertFalse((nested / "evidence.json").exists())

            with self.subTest(boundary="captured_execution_path"):
                captured = root / "captured-codex"
                requested = root / "uncaptured-codex"
                for path in (captured, requested):
                    path.write_bytes(b"#!/bin/sh\nexit 0\n")
                    path.chmod(0o700)
                process = _FakeHostProcess()
                code, _ = _run_host(
                    self.runner,
                    fixture,
                    str(requested),
                    process,
                    _FakePrerequisiteChecker(
                        _passing_prerequisites(str(captured))
                    ),
                    _FakeScorer(outputs),
                )
                safely_bound = (
                    code == self.runner.FAIL and not process.commands
                ) or process.commands[0][0] == str(captured)
                self.assertTrue(safely_bound)

            with self.subTest(boundary="transient_executable_swap"):
                executable = root / "swappable-codex"
                replacement = root / "replacement-codex"
                executable.write_bytes(b"#!/bin/sh\n# captured\nexit 0\n")
                executable.chmod(0o700)
                replacement.write_bytes(b"#!/bin/sh\n# replacement\nexit 0\n")
                replacement.chmod(0o700)
                captured_digest = executable_bytes_sha256(executable)

                class SwappingChecker:
                    def __init__(self) -> None:
                        self.calls = 0

                    def __call__(
                        self,
                        binary: str,
                        model: str,
                        version: str,
                    ) -> dict:
                        self.calls += 1
                        snapshot = _passing_prerequisites(binary)
                        if self.calls == 1:
                            os.replace(replacement, executable)
                        return snapshot

                class InspectingProcess(_FakeHostProcess):
                    def __init__(self) -> None:
                        super().__init__()
                        self.executed_hashes: list[str] = []

                    def __call__(self, command: list[str], **kwargs):
                        self.executed_hashes.append(
                            executable_bytes_sha256(Path(command[0]))
                        )
                        return super().__call__(command, **kwargs)

                process = InspectingProcess()
                code, _ = _run_host(
                    self.runner,
                    fixture,
                    str(executable),
                    process,
                    SwappingChecker(),
                    _FakeScorer(outputs),
                )
                self.assertEqual(self.runner.FAIL, code)
                self.assertTrue(
                    not process.commands
                    or process.executed_hashes == [captured_digest]
                )

            with self.subTest(boundary="nonexecutable_binary_taxonomy"):
                nonexecutable = root / "nonexecutable-codex"
                nonexecutable.write_bytes(b"regular but not executable")
                nonexecutable.chmod(0o600)
                snapshot = self.runner.default_prerequisite_checker(
                    str(nonexecutable),
                    "gpt-5.6-sol",
                    "0.144.5",
                )
                self.assertEqual(
                    "nonexecutable_binary",
                    snapshot.get("captureError"),
                )
                self.assertEqual(
                    "nonexecutable_binary",
                    self.runner._precondition_blocker(snapshot),
                )

    def test_process_execution_is_bound_to_verified_open_executable_bytes(self) -> None:
        fixture = _forward_fixture("DEV136-FWD-DESIGN-001")
        outputs = _forward_outputs(fixture)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = root / "captured-codex"
            replacement = root / "replacement-codex"
            executable.write_bytes(b"#!/bin/sh\n# captured bytes\nexit 0\n")
            executable.chmod(0o700)
            replacement.write_bytes(b"#!/bin/sh\n# replacement bytes\nexit 0\n")
            replacement.chmod(0o700)
            captured_digest = executable_bytes_sha256(executable)
            observed: dict[str, object] = {}

            class BindingProcess(_FakeHostProcess):
                def __call__(self, command: list[str], **kwargs):
                    os.replace(replacement, executable)
                    override = kwargs.get("executable")
                    observed["argv0"] = command[0]
                    observed["override"] = override
                    observed["pass_fds"] = kwargs.get("pass_fds", ())
                    observed["bound_digest"] = (
                        executable_bytes_sha256(Path(override))
                        if isinstance(override, str)
                        else None
                    )
                    return super().__call__(command, **kwargs)

            process = BindingProcess()
            code, _ = _run_host(
                self.runner,
                fixture,
                str(executable),
                process,
                _FakePrerequisiteChecker(
                    _passing_prerequisites(str(executable))
                ),
                _FakeScorer(outputs),
            )

            self.assertEqual(self.runner.FAIL, code)
            self.assertEqual(str(executable), observed["argv0"])
            self.assertIsInstance(observed["override"], str)
            self.assertNotEqual(str(executable), observed["override"])
            self.assertEqual(captured_digest, observed["bound_digest"])
            if str(observed["override"]).startswith("/dev/fd/"):
                descriptor = int(str(observed["override"]).rsplit("/", 1)[1])
                self.assertIn(descriptor, observed["pass_fds"])

    def test_prerequisites_require_exact_auth_plugin_entry_and_regular_skill_payloads(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline_root = root / "baseline"
            _, listing = _build_forward_plugin_tree(baseline_root)
            with mock.patch.object(self.runner, "ROOT", baseline_root):
                self.assertTrue(
                    self.runner._plugin_is_installed_enabled_with_capabilities(
                        json.dumps(listing)
                    )
                )

            version_probe = subprocess.CompletedProcess(
                ["codex", "--version"],
                0,
                "codex-cli 0.144.5\n",
                "",
            )
            exact_auth_probe = subprocess.CompletedProcess(
                ["codex", "login", "status"],
                0,
                "",
                "Logged in using ChatGPT\n",
            )
            plugin_probe = subprocess.CompletedProcess(
                ["codex", "plugin", "list", "--json"],
                0,
                json.dumps(listing),
                "",
            )
            with mock.patch.object(self.runner, "ROOT", baseline_root), mock.patch.object(
                self.runner,
                "_probe",
                side_effect=(version_probe, exact_auth_probe, plugin_probe),
            ):
                snapshot = self.runner.default_prerequisite_checker(
                    str(TEST_EXECUTABLE_PATH),
                    "gpt-5.6-sol",
                    "0.144.5",
                )
            self.assertTrue(snapshot["authenticated"])
            self.assertTrue(snapshot["pluginAvailable"])

            invalid_auth_results = (
                subprocess.CompletedProcess(
                    ["codex", "login", "status"],
                    0,
                    "Logged in using ChatGPT\n",
                    "",
                ),
                subprocess.CompletedProcess(
                    ["codex", "login", "status"],
                    0,
                    "",
                    "",
                ),
                subprocess.CompletedProcess(
                    ["codex", "login", "status"],
                    0,
                    "",
                    "Logged in using ChatGPT\nextra\n",
                ),
            )
            for auth_probe in invalid_auth_results:
                with self.subTest(auth=(auth_probe.stdout, auth_probe.stderr)), mock.patch.object(
                    self.runner, "ROOT", baseline_root
                ), mock.patch.object(
                    self.runner,
                    "_probe",
                    side_effect=(version_probe, auth_probe, plugin_probe),
                ):
                    snapshot = self.runner.default_prerequisite_checker(
                        str(TEST_EXECUTABLE_PATH),
                        "gpt-5.6-sol",
                        "0.144.5",
                    )
                    self.assertFalse(snapshot["authenticated"])

            for mutation in (
                "entry_extra_key",
                "available_not_empty",
                "skill_missing",
                "skill_symlink",
                "skill_payload_invalid",
            ):
                with self.subTest(plugin_contract=mutation):
                    repo_root = root / mutation
                    plugin_root, mutated = _build_forward_plugin_tree(repo_root)
                    entry = mutated["installed"][0]
                    if mutation == "entry_extra_key":
                        entry["unexpected"] = True
                    elif mutation == "available_not_empty":
                        mutated["available"] = [copy.deepcopy(entry)]
                    else:
                        skill_path = (
                            plugin_root
                            / "skills"
                            / SKILLS[0]
                            / "SKILL.md"
                        )
                        if mutation == "skill_missing":
                            skill_path.unlink()
                        elif mutation == "skill_symlink":
                            skill_path.unlink()
                            skill_path.symlink_to(
                                plugin_root
                                / "skills"
                                / SKILLS[1]
                                / "SKILL.md"
                            )
                        else:
                            skill_path.write_text(
                                "---\nname: wrong-skill\n---\n",
                                encoding="utf-8",
                            )
                    with mock.patch.object(self.runner, "ROOT", repo_root):
                        self.assertFalse(
                            self.runner._plugin_is_installed_enabled_with_capabilities(
                                json.dumps(mutated)
                            )
                        )

    def test_cli_normalizes_invalid_fixture_and_scorer_inputs_without_tracebacks(self) -> None:
        def command(
            cases: Path,
            scorer: Path,
            evidence: Path,
        ) -> list[str]:
            return [
                sys.executable,
                str(RUNNER_PATH),
                "--mode",
                "offline",
                "--model",
                "gpt-5.6-sol",
                "--codex-version",
                "0.144.5",
                "--cases",
                str(cases),
                "--evidence",
                str(evidence),
                "--scorer-outputs",
                str(scorer),
            ]

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            valid_scorer = root / "valid-scorer.json"
            valid_scorer.write_text(
                json.dumps(_forward_outputs(self.fixture)),
                encoding="utf-8",
            )
            fixture_inputs = {
                "contract": json.dumps(
                    {
                        "private": (
                            "Bearer synthetic-private-secret from "
                            "/Users/private/customer.txt"
                        )
                    }
                ),
                "malformed_json": (
                    '{"private":"Bearer synthetic-private-secret '
                    'from /Users/private/customer.txt"'
                ),
            }
            for name, payload in fixture_inputs.items():
                with self.subTest(input="fixture", mutation=name):
                    cases = root / f"{name}-fixture.json"
                    cases.write_text(payload, encoding="utf-8")
                    evidence = root / f"{name}-fixture-evidence.json"
                    evidence.write_text("preserve-existing-evidence", encoding="utf-8")
                    completed = subprocess.run(
                        command(cases, valid_scorer, evidence),
                        cwd=ROOT,
                        capture_output=True,
                        text=True,
                    )
                    self.assertEqual(1, completed.returncode)
                    self.assertEqual("", completed.stdout)
                    self.assertEqual(
                        ["fixture_contract_invalid"],
                        completed.stderr.strip().splitlines(),
                    )
                    self.assertNotIn("Traceback", completed.stderr)
                    self.assertNotIn("synthetic-private-secret", completed.stderr)
                    self.assertNotIn("/Users/", completed.stderr)
                    self.assertEqual(
                        "preserve-existing-evidence",
                        evidence.read_text(encoding="utf-8"),
                    )

            scorer_inputs = {
                "contract": json.dumps(
                    {
                        "rawResponse": (
                            "Bearer synthetic-private-secret from "
                            "/Users/private/customer.txt"
                        )
                    }
                ),
                "malformed_json": (
                    '{"rawResponse":"Bearer synthetic-private-secret '
                    'from /Users/private/customer.txt"'
                ),
            }
            for name, payload in scorer_inputs.items():
                with self.subTest(input="scorer", mutation=name):
                    scorer = root / f"{name}-scorer.json"
                    scorer.write_text(payload, encoding="utf-8")
                    evidence = root / f"{name}-scorer-evidence.json"
                    completed = subprocess.run(
                        command(FIXTURE_PATH, scorer, evidence),
                        cwd=ROOT,
                        capture_output=True,
                        text=True,
                    )
                    self.assertEqual(1, completed.returncode)
                    self.assertEqual("", completed.stdout)
                    self.assertEqual(
                        ["scorer_outputs_invalid"],
                        completed.stderr.strip().splitlines(),
                    )
                    self.assertNotIn("Traceback", completed.stderr)
                    self.assertNotIn("synthetic-private-secret", completed.stderr)
                    self.assertNotIn("/Users/", completed.stderr)
                    normalized = load_json(evidence)
                    self.assertEqual("fail", normalized["status"])
                    self.assertEqual(
                        "scoring_failed",
                        normalized["host"]["blockerReason"],
                    )
                    self.assertEqual(0, normalized["summary"]["attemptedCount"])
                    self.assertNotIn(
                        "synthetic-private-secret",
                        json.dumps(normalized),
                    )

    def test_codex_01445_tool_events_are_exact_and_malformed_jsonl_fails_closed(self) -> None:
        with self.subTest(jsonl="pinned_event_taxonomy"):
            self.assertEqual(
                {
                    "agent_message",
                    "reasoning",
                    "command_execution",
                    "file_change",
                    "mcp_tool_call",
                    "collab_tool_call",
                    "web_search",
                    "todo_list",
                    "error",
                },
                self.runner.CODEX_JSONL_ITEM_TYPES,
            )
            self.assertEqual(
                {
                    "command_execution",
                    "file_change",
                    "mcp_tool_call",
                    "collab_tool_call",
                    "web_search",
                },
                self.runner.CODEX_JSONL_TOOL_ITEM_TYPES,
            )
            events = self.runner._tool_events(_canonical_codex_jsonl())
            self.assertEqual(
                ["command_execution"],
                [event["item"]["type"] for event in events],
            )

        suffix_spoof = "\n".join(
            (
                json.dumps(
                    {
                        "type": "item.completed",
                        "item": {"type": "not_a_tool_call"},
                    }
                ),
                json.dumps({"type": "turn.completed", "usage": {}}),
            )
        )
        with self.subTest(jsonl="suffix_spoof"):
            with self.assertRaises(ValueError):
                self.runner._tool_events(suffix_spoof)

        malformed_streams = {
            "invalid_json": "not-json",
            "non_object": "[]",
            "unknown_top_level": json.dumps({"type": "unknown"}),
            "unknown_completed_item": json.dumps(
                {
                    "type": "item.completed",
                    "item": {"type": "unknown"},
                }
            ),
            "missing_terminal": json.dumps(
                {
                    "type": "item.completed",
                    "item": {"type": "command_execution"},
                }
            ),
        }
        for name, payload in malformed_streams.items():
            with self.subTest(jsonl=name):
                with self.assertRaises(ValueError):
                    self.runner._tool_events(payload)

        fixture = _forward_fixture("DEV136-FWD-DESIGN-001")
        outputs = _forward_outputs(fixture)

        class MalformedProcess(_FakeHostProcess):
            def __call__(self, command: list[str], **kwargs):
                completed = super().__call__(command, **kwargs)
                return subprocess.CompletedProcess(
                    command,
                    0,
                    "not-json\n",
                    completed.stderr,
                )

        with self.subTest(jsonl="runner_normalization"):
            process = MalformedProcess()
            scorer = _FakeScorer(outputs)
            try:
                code, evidence = _run_host(
                    self.runner,
                    fixture,
                    str(TEST_EXECUTABLE_PATH),
                    process,
                    _FakePrerequisiteChecker(_passing_prerequisites()),
                    scorer,
                )
            except (ValueError, json.JSONDecodeError) as error:
                self.fail(
                    "malformed JSONL escaped instead of returning normalized fail: "
                    f"{type(error).__name__}"
                )
            self.assertEqual(self.runner.FAIL, code)
            self.assertEqual(
                "event_stream_invalid",
                evidence["host"]["blockerReason"],
            )
            self.assertEqual([], scorer.calls)

    def test_successful_tool_event_stream_requires_turn_completed(self) -> None:
        failed_terminal = "\n".join(
            (
                json.dumps(
                    {
                        "type": "item.completed",
                        "item": {"type": "command_execution"},
                    }
                ),
                json.dumps(
                    {
                        "type": "turn.failed",
                        "error": {"message": "synthetic failure"},
                    }
                ),
            )
        )
        with self.assertRaises(ValueError):
            self.runner._tool_events(failed_terminal)

    def test_model_unavailable_requires_cli_or_structured_error_not_agent_prose(self) -> None:
        agent_prose = "\n".join(
            (
                json.dumps(
                    {
                        "type": "item.completed",
                        "item": {
                            "type": "agent_message",
                            "text": "The model is unavailable in this scenario.",
                        },
                    }
                ),
                json.dumps({"type": "turn.completed", "usage": {}}),
            )
        )
        agent_failure = subprocess.CompletedProcess(
            ["codex", "exec"],
            1,
            agent_prose,
            "",
        )
        cli_failure = subprocess.CompletedProcess(
            ["codex", "exec"],
            1,
            "",
            "Error: model gpt-5.6-sol is unavailable\n",
        )
        structured_failure = subprocess.CompletedProcess(
            ["codex", "exec"],
            1,
            json.dumps(
                {
                    "type": "error",
                    "message": "model gpt-5.6-sol is unavailable",
                }
            )
            + "\n",
            "",
        )
        with self.subTest(diagnostic="agent_message_prose"):
            self.assertFalse(self.runner._is_model_unavailable(agent_failure))
        with self.subTest(diagnostic="bounded_cli"):
            self.assertTrue(self.runner._is_model_unavailable(cli_failure))
        with self.subTest(diagnostic="structured_error"):
            self.assertTrue(
                self.runner._is_model_unavailable(structured_failure)
            )

        fixture = _forward_fixture("DEV136-FWD-DESIGN-001")
        outputs = _forward_outputs(fixture)

        class AgentProseFailureProcess(_FakeHostProcess):
            def __init__(self) -> None:
                super().__init__(returncodes=[1])

            def __call__(self, command: list[str], **kwargs):
                completed = super().__call__(command, **kwargs)
                return subprocess.CompletedProcess(
                    command,
                    1,
                    agent_prose,
                    completed.stderr,
                )

        with self.subTest(diagnostic="runner_agent_message_prose"):
            process = AgentProseFailureProcess()
            code, evidence = _run_host(
                self.runner,
                fixture,
                str(TEST_EXECUTABLE_PATH),
                process,
                _FakePrerequisiteChecker(_passing_prerequisites()),
                _FakeScorer(outputs),
            )
            self.assertEqual(self.runner.FAIL, code)
            self.assertEqual(
                "process_failed",
                evidence["host"]["blockerReason"],
            )

    def test_model_unavailable_ignores_nested_item_error_text(self) -> None:
        nested_item_failure = subprocess.CompletedProcess(
            ["codex", "exec"],
            1,
            json.dumps(
                {
                    "type": "item.completed",
                    "item": {
                        "type": "error",
                        "message": "model gpt-5.6-sol is unavailable",
                    },
                }
            )
            + "\n",
            "",
        )
        self.assertFalse(
            self.runner._is_model_unavailable(nested_item_failure)
        )

    def test_prerequisite_probes_and_all_cases_share_first_bound_executable_identity(self) -> None:
        probes: list[tuple[list[str], str | None, str | None, int | None]] = []

        def probe_process(command: list[str], **kwargs):
            override = kwargs.get("executable")
            bound = Path(override) if isinstance(override, str) else None
            probes.append(
                (
                    list(command),
                    override,
                    executable_bytes_sha256(bound)
                    if bound is not None and bound.is_file()
                    else None,
                    bound.stat().st_mode & 0o777
                    if bound is not None and bound.is_file()
                    else None,
                )
            )
            if command[1:] == ["--version"]:
                return subprocess.CompletedProcess(command, 0, "codex-cli 0.144.5\n", "")
            if command[1:] == ["login", "status"]:
                return subprocess.CompletedProcess(command, 0, "", "Logged in using ChatGPT\n")
            return subprocess.CompletedProcess(command, 0, "{}", "")

        original = str(TEST_EXECUTABLE_PATH)
        digest = executable_bytes_sha256()
        with mock.patch.object(
            self.runner.subprocess, "run", side_effect=probe_process
        ), mock.patch.object(
            self.runner, "_plugin_is_installed_enabled_with_capabilities", return_value=True
        ):
            snapshot = self.runner.default_prerequisite_checker(
                original, "gpt-5.6-sol", "0.144.5"
            )
        with self.subTest(bound_probe="version_auth_plugin"):
            overrides = [probe[1] for probe in probes]
            self.assertEqual(
                (
                    3,
                    {original},
                    1,
                    [digest] * 3,
                    [0o700] * 3,
                    digest,
                ),
                (
                    len(probes),
                    {probe[0][0] for probe in probes},
                    len(set(overrides)) if all(isinstance(value, str) for value in overrides) else 0,
                    [probe[2] for probe in probes],
                    [probe[3] for probe in probes],
                    snapshot["executableSha256"],
                ),
            )
        for override in {value for value in overrides if isinstance(value, str)}:
            self.assertFalse(Path(override).exists())

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first-codex"
            second = root / "second-codex"
            first.write_bytes(b"#!/bin/sh\n# first executable\nexit 0\n")
            second.write_bytes(b"#!/bin/sh\n# second executable\nexit 0\n")
            first.chmod(0o700)
            second.chmod(0o700)
            first_snapshot = _passing_prerequisites(str(first))
            second_snapshot = _passing_prerequisites(str(second))
            fixture = _forward_fixture(
                "DEV136-FWD-DESIGN-001", "DEV136-FWD-REVIEW-001"
            )
            process = _FakeHostProcess()
            scorer = _FakeScorer(_forward_outputs(fixture))
            checker = _FakePrerequisiteChecker(
                first_snapshot,
                first_snapshot,
                second_snapshot,
                second_snapshot,
            )
            code, evidence = _run_host(
                self.runner,
                fixture,
                str(first),
                process,
                checker,
                scorer,
            )
            with self.subTest(bound_probe="cross_case_identity"):
                self.assertEqual(
                    (
                        self.runner.FAIL,
                        1,
                        [fixture["cases"][0]["id"]],
                        "post_capture_prerequisite_drift",
                        first_snapshot["executableSha256"],
                    ),
                    (
                        code,
                        len(process.commands),
                        scorer.calls,
                        evidence["host"]["blockerReason"],
                        evidence["host"]["resolvedExecutableSha256"],
                    ),
                )

    def test_codex_01445_jsonl_schemas_and_command_lifecycle_are_exact(self) -> None:
        canonical = [
            json.loads(line) for line in _canonical_codex_jsonl().splitlines()
        ]
        self.assertEqual(
            "item_0",
            self.runner._tool_events(_canonical_codex_jsonl())[0]["item"]["id"],
        )
        for status, exit_code in (
            ("completed", 0),
            ("failed", 7),
            ("declined", -1),
        ):
            value = copy.deepcopy(canonical)
            value[3]["item"].update(
                {"status": status, "exit_code": exit_code}
            )
            with self.subTest(jsonl=f"valid_command_{status}"):
                self.assertEqual(
                    status,
                    self.runner._tool_events(
                        "\n".join(
                            json.dumps(event, sort_keys=True) for event in value
                        )
                    )[0]["item"]["status"],
                )

        failure = (
            {"type": "thread.started", "thread_id": "thread_synthetic"},
            {"type": "turn.started"},
            {"type": "error", "message": "model gpt-5.6-sol is unavailable"},
            {
                "type": "turn.failed",
                "error": {"message": "model gpt-5.6-sol is unavailable"},
            },
        )
        try:
            parsed_failure = self.runner._codex_jsonl_events(
                "\n".join(json.dumps(event) for event in failure)
            )
            parsed_failure_types = [event["type"] for event in parsed_failure]
        except ValueError:
            parsed_failure_types = None
        with self.subTest(jsonl="exact_top_level_error_and_failed_turn"):
            self.assertEqual(
                ["thread.started", "turn.started", "error", "turn.failed"],
                parsed_failure_types,
            )

        def stream(events: list[dict]) -> str:
            return "\n".join(json.dumps(event, sort_keys=True) for event in events)

        def mutated(change) -> list[dict]:
            value = copy.deepcopy(canonical)
            change(value)
            return value

        malformed = {
            "missing_thread_started": canonical[1:],
            "thread_schema": mutated(lambda value: value[0].pop("thread_id")),
            "turn_order": mutated(lambda value: value.pop(1)),
            "usage_schema": mutated(
                lambda value: value[-1].__setitem__("usage", {"input_tokens": 1})
            ),
            "command_schema": mutated(
                lambda value: value[2]["item"].pop("status")
            ),
            "command_schema_extra": mutated(
                lambda value: value[2]["item"].__setitem__("unexpected", True)
            ),
            "command_start_state": mutated(
                lambda value: value[2]["item"].update(
                    {"aggregated_output": "premature", "exit_code": 0}
                )
            ),
            "command_completion_state": mutated(
                lambda value: value[3]["item"].update(
                    {"status": "completed", "exit_code": 7}
                )
            ),
            "command_pair_mismatch": mutated(
                lambda value: value[3]["item"].update(
                    {"id": "item_other", "command": "different-command"}
                )
            ),
            "completion_without_start": mutated(lambda value: value.pop(2)),
            "duplicate_start": mutated(
                lambda value: value.insert(3, copy.deepcopy(value[2]))
            ),
            "open_item": mutated(lambda value: value.pop(3)),
            "command_item_updated": mutated(
                lambda value: value[2].__setitem__("type", "item.updated")
            ),
            "error_in_success_stream": mutated(
                lambda value: value.insert(
                    -1, {"type": "error", "message": "synthetic stream error"}
                )
            ),
        }

        for name, events in malformed.items():
            with self.subTest(jsonl=name):
                with self.assertRaises(ValueError):
                    self.runner._tool_events(stream(events))

        fixture = _forward_fixture("DEV136-FWD-DESIGN-001")
        outputs = _forward_outputs(fixture)

        class MissingThreadProcess(_FakeHostProcess):
            def __call__(self, command: list[str], **kwargs):
                completed = super().__call__(command, **kwargs)
                lines = completed.stdout.splitlines()
                return subprocess.CompletedProcess(
                    command, 0, "\n".join(lines[1:]), completed.stderr
                )

        process = MissingThreadProcess()
        scorer = _FakeScorer(outputs)
        code, evidence = _run_host(
            self.runner,
            fixture,
            str(TEST_EXECUTABLE_PATH),
            process,
            _FakePrerequisiteChecker(_passing_prerequisites()),
            scorer,
        )
        with self.subTest(jsonl="runner_event_stream_normalization"):
            self.assertEqual(
                (self.runner.FAIL, "event_stream_invalid", []),
                (code, evidence["host"]["blockerReason"], scorer.calls),
            )

    def test_codex_01445_noncommand_item_lifecycles_and_statuses_are_exact(self) -> None:
        def item_event(event_type: str, item: dict) -> dict:
            return {"type": event_type, "item": copy.deepcopy(item)}

        def stream(events: list[dict]) -> str:
            records = [
                {"type": "thread.started", "thread_id": "thread_synthetic"},
                {"type": "turn.started"},
                *events,
                {"type": "turn.completed", "usage": _codex_usage()},
            ]
            return "\n".join(
                json.dumps(record, sort_keys=True) for record in records
            )

        items = {
            "agent_message": {
                "id": "agent_0", "type": "agent_message", "text": "synthetic",
            },
            "reasoning": {
                "id": "reasoning_0", "type": "reasoning", "text": "synthetic",
            },
            "file_change": {
                "id": "file_0",
                "type": "file_change",
                "changes": [{"path": "synthetic.txt", "kind": "update"}],
                "status": "completed",
            },
            "mcp_tool_call": {
                "id": "mcp_0",
                "type": "mcp_tool_call",
                "server": "synthetic",
                "tool": "lookup",
                "arguments": {},
                "result": None,
                "error": None,
                "status": "in_progress",
            },
            "collab_tool_call": {
                "id": "collab_0",
                "type": "collab_tool_call",
                "tool": "wait",
                "sender_thread_id": "thread_synthetic",
                "receiver_thread_ids": [],
                "prompt": None,
                "agents_states": {},
                "status": "in_progress",
            },
            "web_search": {
                "id": "web_0",
                "type": "web_search",
                "query": "synthetic",
                "action": {"type": "other"},
            },
            "todo_list": {
                "id": "todo_0",
                "type": "todo_list",
                "items": [{"text": "synthetic", "completed": False}],
            },
            "error": {
                "id": "error_0", "type": "error", "message": "synthetic",
            },
        }

        def status_item(item_type: str, status: str) -> dict:
            value = copy.deepcopy(items[item_type])
            value["status"] = status
            return value

        valid_streams = {
            "completion_only_agent_message": [
                item_event("item.completed", items["agent_message"]),
            ],
            "completion_only_reasoning": [
                item_event("item.completed", items["reasoning"]),
            ],
            "completion_only_file_change_completed": [
                item_event("item.completed", items["file_change"]),
            ],
            "completion_only_file_change_failed": [
                item_event(
                    "item.completed", status_item("file_change", "failed")
                ),
            ],
            "completion_only_error": [
                item_event("item.completed", items["error"]),
            ],
            "paired_mcp_completed": [
                item_event("item.started", items["mcp_tool_call"]),
                item_event(
                    "item.completed", status_item("mcp_tool_call", "completed")
                ),
            ],
            "paired_mcp_failed": [
                item_event("item.started", items["mcp_tool_call"]),
                item_event(
                    "item.completed", status_item("mcp_tool_call", "failed")
                ),
            ],
            "paired_collab_completed": [
                item_event("item.started", items["collab_tool_call"]),
                item_event(
                    "item.completed",
                    status_item("collab_tool_call", "completed"),
                ),
            ],
            "paired_collab_failed": [
                item_event("item.started", items["collab_tool_call"]),
                item_event(
                    "item.completed", status_item("collab_tool_call", "failed")
                ),
            ],
            "paired_web_search": [
                item_event("item.started", items["web_search"]),
                item_event("item.completed", items["web_search"]),
            ],
            "paired_todo_with_update": [
                item_event("item.started", items["todo_list"]),
                item_event("item.updated", items["todo_list"]),
                item_event("item.completed", items["todo_list"]),
            ],
        }
        for name, events in valid_streams.items():
            with self.subTest(valid_control=name):
                parsed = self.runner._codex_jsonl_events(stream(events))
                self.assertEqual("turn.completed", parsed[-1]["type"])

        invalid_streams = {
            "agent_message_cannot_start": [
                item_event("item.started", items["agent_message"]),
                item_event("item.completed", items["agent_message"]),
            ],
            "reasoning_cannot_start": [
                item_event("item.started", items["reasoning"]),
                item_event("item.completed", items["reasoning"]),
            ],
            "file_change_cannot_start": [
                item_event(
                    "item.started", status_item("file_change", "in_progress")
                ),
                item_event("item.completed", items["file_change"]),
            ],
            "file_change_completion_cannot_be_in_progress": [
                item_event(
                    "item.completed", status_item("file_change", "in_progress")
                ),
            ],
            "mcp_completion_requires_start": [
                item_event(
                    "item.completed", status_item("mcp_tool_call", "completed")
                ),
            ],
            "mcp_start_requires_in_progress": [
                item_event(
                    "item.started", status_item("mcp_tool_call", "completed")
                ),
                item_event(
                    "item.completed", status_item("mcp_tool_call", "completed")
                ),
            ],
            "mcp_completion_requires_terminal_status": [
                item_event("item.started", items["mcp_tool_call"]),
                item_event("item.completed", items["mcp_tool_call"]),
            ],
            "collab_completion_requires_start": [
                item_event(
                    "item.completed",
                    status_item("collab_tool_call", "completed"),
                ),
            ],
            "collab_start_requires_in_progress": [
                item_event(
                    "item.started",
                    status_item("collab_tool_call", "completed"),
                ),
                item_event(
                    "item.completed",
                    status_item("collab_tool_call", "completed"),
                ),
            ],
            "collab_completion_requires_terminal_status": [
                item_event("item.started", items["collab_tool_call"]),
                item_event("item.completed", items["collab_tool_call"]),
            ],
            "web_search_completion_requires_start": [
                item_event("item.completed", items["web_search"]),
            ],
            "todo_completion_requires_start": [
                item_event("item.completed", items["todo_list"]),
            ],
            "error_cannot_start": [
                item_event("item.started", items["error"]),
                item_event("item.completed", items["error"]),
            ],
        }
        for name, events in invalid_streams.items():
            with self.subTest(invalid_lifecycle=name):
                with self.assertRaises(ValueError):
                    self.runner._codex_jsonl_events(stream(events))

    def test_paired_noncommand_items_preserve_immutable_identity_fields(self) -> None:
        def item_event(event_type: str, item: dict) -> dict:
            return {"type": event_type, "item": copy.deepcopy(item)}

        def stream(events: list[dict]) -> str:
            records = [
                {"type": "thread.started", "thread_id": "thread_synthetic"},
                {"type": "turn.started"},
                *events,
                {"type": "turn.completed", "usage": _codex_usage()},
            ]
            return "\n".join(
                json.dumps(record, sort_keys=True) for record in records
            )

        items = {
            "mcp_tool_call": {
                "id": "mcp_0",
                "type": "mcp_tool_call",
                "server": "synthetic",
                "tool": "lookup",
                "arguments": {},
                "result": None,
                "error": None,
                "status": "in_progress",
            },
            "collab_tool_call": {
                "id": "collab_0",
                "type": "collab_tool_call",
                "tool": "wait",
                "sender_thread_id": "thread_synthetic",
                "receiver_thread_ids": [],
                "prompt": None,
                "agents_states": {},
                "status": "in_progress",
            },
            "web_search": {
                "id": "web_0",
                "type": "web_search",
                "query": "synthetic",
                "action": {"type": "other"},
            },
            "todo_list": {
                "id": "todo_0",
                "type": "todo_list",
                "items": [{"text": "synthetic", "completed": False}],
            },
        }

        mcp_completed = copy.deepcopy(items["mcp_tool_call"])
        mcp_completed.update(
            {
                "result": {
                    "content": [
                        {"type": "text", "text": "synthetic result"}
                    ],
                    "structured_content": None,
                },
                "status": "completed",
            }
        )
        mcp_failed = copy.deepcopy(items["mcp_tool_call"])
        mcp_failed.update(
            {
                "error": {"message": "synthetic failure"},
                "status": "failed",
            }
        )
        collab_completed = copy.deepcopy(items["collab_tool_call"])
        collab_completed.update(
            {
                "agents_states": {
                    "thread_worker": {
                        "status": "completed",
                        "message": "synthetic completion",
                    }
                },
                "status": "completed",
            }
        )
        todo_updated = copy.deepcopy(items["todo_list"])
        todo_updated["items"][0]["completed"] = True
        todo_completed = copy.deepcopy(todo_updated)
        todo_completed["items"].append(
            {"text": "synthetic follow-on", "completed": True}
        )

        valid_controls = {
            "mcp_status_and_result_change": [
                item_event("item.started", items["mcp_tool_call"]),
                item_event("item.completed", mcp_completed),
            ],
            "mcp_status_and_error_change": [
                item_event("item.started", items["mcp_tool_call"]),
                item_event("item.completed", mcp_failed),
            ],
            "collab_status_and_agents_states_change": [
                item_event("item.started", items["collab_tool_call"]),
                item_event("item.completed", collab_completed),
            ],
            "todo_items_change_through_lifecycle": [
                item_event("item.started", items["todo_list"]),
                item_event("item.updated", todo_updated),
                item_event("item.completed", todo_completed),
            ],
        }
        for name, events in valid_controls.items():
            with self.subTest(mutable_control=name):
                parsed = self.runner._codex_jsonl_events(stream(events))
                self.assertEqual("turn.completed", parsed[-1]["type"])

        immutable_mutations = {
            "mcp_server": ("mcp_tool_call", {"server": "mutated"}),
            "mcp_tool": ("mcp_tool_call", {"tool": "fetch"}),
            "mcp_arguments": (
                "mcp_tool_call",
                {"arguments": {"mutated": True}},
            ),
            "collab_tool": ("collab_tool_call", {"tool": "send_input"}),
            "collab_sender_thread_id": (
                "collab_tool_call",
                {"sender_thread_id": "thread_mutated"},
            ),
            "collab_receiver_thread_ids": (
                "collab_tool_call",
                {"receiver_thread_ids": ["thread_mutated"]},
            ),
            "collab_prompt": (
                "collab_tool_call",
                {"prompt": "mutated prompt"},
            ),
            "web_search_query": ("web_search", {"query": "mutated"}),
            "web_search_action": (
                "web_search",
                {"action": {"type": "search", "query": "mutated"}},
            ),
        }
        for name, (item_type, mutation) in immutable_mutations.items():
            started = items[item_type]
            completed = copy.deepcopy(started)
            completed.update(mutation)
            if item_type in {"mcp_tool_call", "collab_tool_call"}:
                completed["status"] = "completed"
            with self.subTest(immutable_identity=name):
                with self.assertRaises(ValueError):
                    self.runner._codex_jsonl_events(
                        stream(
                            [
                                item_event("item.started", started),
                                item_event("item.completed", completed),
                            ]
                        )
                    )

    def test_paired_mcp_arguments_require_recursively_type_exact_identity(self) -> None:
        def item(arguments: dict, status: str) -> dict:
            return {
                "id": "mcp_0",
                "type": "mcp_tool_call",
                "server": "synthetic",
                "tool": "lookup",
                "arguments": arguments,
                "result": None,
                "error": None,
                "status": status,
            }

        def stream(started_arguments: dict, completed_arguments: dict) -> str:
            records = (
                {"type": "thread.started", "thread_id": "thread_synthetic"},
                {"type": "turn.started"},
                {
                    "type": "item.started",
                    "item": item(started_arguments, "in_progress"),
                },
                {
                    "type": "item.completed",
                    "item": item(completed_arguments, "completed"),
                },
                {"type": "turn.completed", "usage": _codex_usage()},
            )
            return "\n".join(json.dumps(record) for record in records)

        exact_nested = {
            "object": {"boolean": True, "integer": 1, "float": 1.0},
            "list": [False, 0, 0.0, {"null": None}],
        }
        controls = {
            "exact_nested_type_and_value": (
                exact_nested,
                copy.deepcopy(exact_nested),
            ),
            "dictionary_insertion_order": (
                {
                    "object": {"boolean": True, "integer": 1, "float": 1.0},
                    "list": [False, 0, 0.0],
                },
                {
                    "list": [False, 0, 0.0],
                    "object": {"float": 1.0, "integer": 1, "boolean": True},
                },
            ),
        }
        for name, (started_arguments, completed_arguments) in controls.items():
            with self.subTest(type_exact_control=name):
                parsed = self.runner._codex_jsonl_events(
                    stream(started_arguments, completed_arguments)
                )
                self.assertEqual("turn.completed", parsed[-1]["type"])

        type_mismatches = {
            "top_level_true_vs_integer": ({"value": True}, {"value": 1}),
            "top_level_false_vs_integer": ({"value": False}, {"value": 0}),
            "top_level_integer_vs_float": ({"value": 1}, {"value": 1.0}),
            "nested_true_vs_integer": (
                {"outer": [{"value": True}]},
                {"outer": [{"value": 1}]},
            ),
            "nested_false_vs_integer": (
                {"outer": [{"value": False}]},
                {"outer": [{"value": 0}]},
            ),
            "nested_integer_vs_float": (
                {"outer": [{"value": 1}]},
                {"outer": [{"value": 1.0}]},
            ),
        }
        for name, (started_arguments, completed_arguments) in type_mismatches.items():
            with self.subTest(type_identity_mismatch=name):
                with self.assertRaises(ValueError):
                    self.runner._codex_jsonl_events(
                        stream(started_arguments, completed_arguments)
                    )

    def test_nonstandard_json_constants_fail_closed_in_jsonl_and_parser_inputs(self) -> None:
        constants = {
            "NaN": float("nan"),
            "Infinity": float("inf"),
            "-Infinity": float("-inf"),
        }

        def mcp_stream(arguments) -> str:
            def item(status: str) -> dict:
                return {
                    "id": "mcp_0",
                    "type": "mcp_tool_call",
                    "server": "synthetic",
                    "tool": "lookup",
                    "arguments": arguments,
                    "result": None,
                    "error": None,
                    "status": status,
                }

            records = (
                {"type": "thread.started", "thread_id": "thread_synthetic"},
                {"type": "turn.started"},
                {"type": "item.started", "item": item("in_progress")},
                {"type": "item.completed", "item": item("completed")},
                {"type": "turn.completed", "usage": _codex_usage()},
            )
            return "\n".join(
                json.dumps(record, sort_keys=True) for record in records
            )

        for name, value in constants.items():
            with self.subTest(jsonl_constant=name):
                with self.assertRaises(ValueError):
                    self.runner._codex_jsonl_events(mcp_stream(value))

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plugin_root, listing = _build_forward_plugin_tree(root / "plugin-json")
            with mock.patch.object(self.runner, "ROOT", root / "plugin-json"):
                for name in constants:
                    manifest = (
                        '{"name":"apple-foundation-models-handoff",'
                        '"interface":{"capabilities":'
                        + json.dumps(list(WORKFLOW_SECTIONS))
                        + f'}},"nonStandard":{name}}}'
                    )
                    (plugin_root / ".codex-plugin/plugin.json").write_text(
                        manifest, encoding="utf-8"
                    )
                    with self.subTest(plugin_manifest_constant=name):
                        self.assertFalse(
                            self.runner._plugin_is_installed_enabled_with_capabilities(
                                json.dumps(listing)
                            )
                        )

            for name, value in constants.items():
                stale = {key: None for key in FORWARD_EVIDENCE_KEYS}
                stale.update(
                    {
                        "schemaVersion": "1.0",
                        "sourceIssue": "DEV-136",
                        "evidenceKind": "codex_skill_forward_test",
                        "status": "pass",
                        "cases": value,
                    }
                )
                path = root / f"stale-{name}.json"
                path.write_text(json.dumps(stale), encoding="utf-8")
                with self.subTest(stale_evidence_constant=name):
                    self.assertFalse(
                        self.runner._existing_evidence_is_stale_success(path)
                    )

    def test_evidence_prerequisites_are_derived_from_mode_blocker_and_rows(self) -> None:
        fixture = _forward_fixture("DEV136-FWD-DESIGN-001")
        fixture_bytes = deterministic_fixture_bytes(fixture)
        outputs = _forward_outputs(fixture)
        _, offline = _run_offline(
            self.runner, fixture, outputs, fixture_bytes
        )
        self.assertEqual(
            {key: "not_applicable" for key in FORWARD_PREREQUISITE_KEYS},
            offline["host"]["prerequisites"],
        )

        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "evidence.json"

            def reject(mutant: dict, scorer_outputs: dict, **bindings) -> None:
                with self.assertRaises(ValueError):
                    _write_bound_evidence(
                        self.runner, destination, mutant, fixture, scorer_outputs,
                        fixture_bytes=fixture_bytes, **bindings,
                    )

            for fact in ("authentication", "pluginActivation"):
                with self.subTest(mode="offline", impossible_fact=fact):
                    mutant = copy.deepcopy(offline)
                    mutant["host"]["prerequisites"][fact] = "pass"
                    reject(mutant, outputs)

            process = _FakeHostProcess()
            code, host_pass = _run_host(
                self.runner,
                fixture,
                str(TEST_EXECUTABLE_PATH),
                process,
                _FakePrerequisiteChecker(_passing_prerequisites()),
                _FakeScorer(outputs),
                fixture_bytes,
            )
            self.assertEqual(self.runner.PASS, code)
            self.assertEqual(
                "pass",
                host_pass["host"]["prerequisites"]["pluginActivation"],
            )
            with self.subTest(mode="host", impossible_fact="completed_activation_nonpass"):
                mutant = copy.deepcopy(host_pass)
                mutant["host"]["prerequisites"]["pluginActivation"] = (
                    "not_applicable"
                )
                reject(
                    mutant, outputs, host_results=process.results,
                    executable_sha256=executable_bytes_sha256(),
                )

            blocker_mutations = (
                ("authentication_unavailable", {"authenticated": False}, "authentication"),
                (
                    "plugin_activation_unavailable",
                    {
                        "pluginAvailable": False,
                        "discovery": "blocked",
                        "installation": "blocked",
                    },
                    "pluginActivation",
                ),
            )
            for reason, snapshot_mutation, impossible_fact in blocker_mutations:
                snapshot = _passing_prerequisites()
                snapshot.update(snapshot_mutation)
                code, blocked = _run_host(
                    self.runner,
                    fixture,
                    str(TEST_EXECUTABLE_PATH),
                    _FakeHostProcess(),
                    _FakePrerequisiteChecker(snapshot),
                    _FakeScorer(outputs),
                    fixture_bytes,
                )
                self.assertEqual(
                    (self.runner.BLOCKED, reason),
                    (code, blocked["host"]["blockerReason"]),
                )
                with self.subTest(blocker=reason, impossible_fact=impossible_fact):
                    mutant = copy.deepcopy(blocked)
                    mutant["host"]["prerequisites"][impossible_fact] = "pass"
                    reject(
                        mutant, {}, executable_sha256=executable_bytes_sha256()
                    )

    def test_live_score_rejects_spaced_hyphenated_placeholders_and_postposed_negation(self) -> None:
        case = _forward_fixture("DEV136-FWD-REVIEW-001")["cases"][0]
        for placeholder in (
            "not specified",
            "not-specified",
            " not specified ",
            " not_specified ",
            "unchanged existing version",
            "unchanged-existing-version",
            " unchanged-existing-version ",
            " unchanged_existing_version ",
        ):
            with self.subTest(version_placeholder=placeholder):
                observation = self.runner.live_score(
                    case,
                    _canonical_live_response(
                        case,
                        state_version=placeholder,
                        policy_version=placeholder,
                    ),
                    [],
                )
                self.assertEqual(
                    "fail",
                    observation["assertions"]["independent_version_labels"],
                )

        with self.subTest(review_boundary="postposed_negation"):
            observation = self.runner.live_score(
                case,
                _canonical_live_response(
                    case,
                    review_boundary=(
                        "A separate authorized follow-on boundary does not exist."
                    ),
                ),
                [],
            )
            self.assertEqual(
                "fail",
                observation["assertions"]["review_first_ordering"],
            )

    def test_live_score_rejects_contracted_full_clause_negations(self) -> None:
        case = _forward_fixture("DEV136-FWD-REVIEW-001")["cases"][0]
        negated_boundaries = {
            "isn't": "A separate authorized follow-on boundary isn't required.",
            "aren't": "Separate authorized follow-on changes aren't required.",
            "wasn't": "A separate authorized follow-on boundary wasn't established.",
            "weren't": "Separate authorized follow-on changes weren't established.",
            "doesn't": "A separate authorized follow-on boundary doesn't exist.",
            "don't": "Separate follow-on changes don't require authorization.",
            "can't": "A separate follow-on change can't be authorized.",
            "cannot": "A separate authorized follow-on boundary cannot exist.",
        }
        for contraction, review_boundary in negated_boundaries.items():
            with self.subTest(contracted_negation=contraction):
                observation = self.runner.live_score(
                    case,
                    _canonical_live_response(
                        case, review_boundary=review_boundary
                    ),
                    [],
                )
                self.assertEqual(
                    "fail",
                    observation["assertions"]["review_first_ordering"],
                )

    def test_live_score_rejects_generic_straight_and_curly_contracted_negations(self) -> None:
        case = _forward_fixture("DEV136-FWD-REVIEW-001")["cases"][0]
        with self.subTest(control="authorized_follow_on"):
            observation = self.runner.live_score(
                case,
                _canonical_live_response(case),
                [],
            )
            self.assertEqual(
                "pass",
                observation["assertions"]["review_first_ordering"],
            )

        negated_boundaries = {
            "straight_shouldnt": (
                "A separate authorized follow-on boundary shouldn't exist."
            ),
            "straight_hasnt": (
                "A separate authorized follow-on boundary hasn't been established."
            ),
            "straight_wont": (
                "A separate authorized follow-on boundary won't be required."
            ),
            "straight_wouldnt": (
                "A separate authorized follow-on boundary wouldn't be required."
            ),
            "straight_neednt": (
                "A separate authorized follow-on boundary needn't be repeated."
            ),
            "curly_shouldnt": (
                "A separate authorized follow-on boundary shouldn’t exist."
            ),
            "curly_hasnt": (
                "A separate authorized follow-on boundary hasn’t been established."
            ),
            "curly_wont": (
                "A separate authorized follow-on boundary won’t be required."
            ),
            "curly_wouldnt": (
                "A separate authorized follow-on boundary wouldn’t be required."
            ),
            "curly_neednt": (
                "A separate authorized follow-on boundary needn’t be repeated."
            ),
        }
        for contraction, review_boundary in negated_boundaries.items():
            with self.subTest(contracted_negation=contraction):
                observation = self.runner.live_score(
                    case,
                    _canonical_live_response(
                        case, review_boundary=review_boundary
                    ),
                    [],
                )
                self.assertEqual(
                    "fail",
                    observation["assertions"]["review_first_ordering"],
                )

    def test_live_score_rejects_quoted_padded_version_placeholders(self) -> None:
        case = _forward_fixture("DEV136-FWD-REVIEW-001")["cases"][0]

        def response_with_versions(
            state_version: str,
            policy_version: str,
        ) -> bytes:
            response = _canonical_live_response(case).decode("utf-8")
            response = response.replace(
                'stateVersion: "state-v1"',
                f"stateVersion: {state_version}",
            )
            response = response.replace(
                'policyVersion: "policy-v1"',
                f"policyVersion: {policy_version}",
            )
            return response.encode("utf-8")

        quote_pairs = {
            "ascii_single": ("'", "'"),
            "ascii_double": ('"', '"'),
            "typographic_single": ("‘", "’"),
            "typographic_double": ("“", "”"),
        }
        for quote_name, (opening, closing) in quote_pairs.items():
            with self.subTest(quoted_version_control=quote_name):
                observation = self.runner.live_score(
                    case,
                    response_with_versions(
                        f"{opening}state-v2{closing}",
                        f"{opening}policy-v3{closing}",
                    ),
                    [],
                )
                self.assertEqual(
                    "pass",
                    observation["assertions"]["independent_version_labels"],
                )

            for placeholder in (
                "not specified",
                "unchanged existing version",
            ):
                quoted_placeholder = (
                    f"{opening} {placeholder} {closing}"
                )
                with self.subTest(
                    quote=quote_name,
                    version_placeholder=placeholder,
                ):
                    observation = self.runner.live_score(
                        case,
                        response_with_versions(
                            quoted_placeholder,
                            quoted_placeholder,
                        ),
                        [],
                    )
                    self.assertEqual(
                        "fail",
                        observation["assertions"][
                            "independent_version_labels"
                        ],
                    )

    def test_live_score_normalizes_nested_mixed_padded_version_boundaries(self) -> None:
        case = _forward_fixture("DEV136-FWD-REVIEW-001")["cases"][0]

        def response_with_versions(
            state_version: str,
            policy_version: str,
        ) -> bytes:
            response = _canonical_live_response(case).decode("utf-8")
            response = response.replace(
                'stateVersion: "state-v1"',
                f"stateVersion: {state_version}",
            )
            response = response.replace(
                'policyVersion: "policy-v1"',
                f"policyVersion: {policy_version}",
            )
            return response.encode("utf-8")

        boundary_layers = {
            "reviewer_ascii_double_single": ("\" ' ", " ' \""),
            "reviewer_typographic_double_single": ("“ ‘ ", " ’ ”"),
            "ascii_double_typographic_single": ("\" ‘ ", " ’ \""),
            "typographic_double_ascii_single": ("“ ' ", " ' ”"),
            "ascii_single_typographic_double": ("' “ ", " ” '"),
            "typographic_single_ascii_double": ("‘ \" ", " \" ’"),
            "three_layer_mixed": ("“ ' ‘ ", " ’ ' ”"),
        }
        for name, (prefix, suffix) in boundary_layers.items():
            with self.subTest(nested_boundary_control=name):
                observation = self.runner.live_score(
                    case,
                    response_with_versions(
                        f"{prefix}state-v2{suffix}",
                        f"{prefix}policy-v3{suffix}",
                    ),
                    [],
                )
                self.assertEqual(
                    "pass",
                    observation["assertions"]["independent_version_labels"],
                )

            for placeholder in (
                "not specified",
                "unchanged existing version",
            ):
                with self.subTest(
                    nested_boundary=name,
                    version_placeholder=placeholder,
                ):
                    observation = self.runner.live_score(
                        case,
                        response_with_versions(
                            f"{prefix}{placeholder}{suffix}",
                            f"{prefix}{placeholder}{suffix}",
                        ),
                        [],
                    )
                    self.assertEqual(
                        "fail",
                        observation["assertions"][
                            "independent_version_labels"
                        ],
                    )

    def test_model_unavailable_is_bound_to_exact_model_and_diagnostic_grammar(self) -> None:
        def completed(*, stderr: str = "", stdout: str = ""):
            return subprocess.CompletedProcess(
                ["codex", "exec", "-m", "gpt-5.6-sol"],
                1,
                stdout,
                stderr,
            )

        accepted = (
            completed(stderr="Error: model gpt-5.6-sol is unavailable\n"),
            completed(
                stdout=json.dumps(
                    {
                        "type": "error",
                        "message": "model gpt-5.6-sol is unavailable",
                    }
                )
                + "\n"
            ),
            completed(
                stdout=json.dumps(
                    {
                        "type": "turn.failed",
                        "error": {
                            "message": "model gpt-5.6-sol is unavailable"
                        },
                    }
                )
                + "\n"
            ),
        )
        for index, result in enumerate(accepted):
            with self.subTest(diagnostic="accepted", index=index):
                self.assertTrue(self.runner._is_model_unavailable(result))

        rejected = {
            "unrelated_model": completed(
                stderr="Error: model gpt-5.5 is unavailable\n"
            ),
            "example_prose": completed(
                stderr=(
                    "Example only: Error: model gpt-5.6-sol is unavailable\n"
                )
            ),
            "structured_unrelated_model": completed(
                stdout=json.dumps(
                    {"type": "error", "message": "model gpt-5.5 is unavailable"}
                )
                + "\n"
            ),
            "structured_extra_key": completed(
                stdout=json.dumps(
                    {
                        "type": "error",
                        "message": "model gpt-5.6-sol is unavailable",
                        "example": True,
                    }
                )
                + "\n"
            ),
            "turn_failed_extra_key": completed(
                stdout=json.dumps(
                    {
                        "type": "turn.failed",
                        "error": {
                            "message": "model gpt-5.6-sol is unavailable"
                        },
                        "example": True,
                    }
                )
                + "\n"
            ),
        }
        for name, result in rejected.items():
            with self.subTest(diagnostic=name):
                self.assertFalse(self.runner._is_model_unavailable(result))

    def test_duplicate_json_inputs_fail_closed_and_replace_stale_fixture_evidence(self) -> None:
        def command(cases: Path, scorer: Path, evidence: Path) -> list[str]:
            return [
                sys.executable, str(RUNNER_PATH), "--mode", "offline",
                "--model", "gpt-5.6-sol", "--codex-version", "0.144.5",
                "--cases", str(cases), "--evidence", str(evidence),
                "--scorer-outputs", str(scorer),
            ]

        outputs = _forward_outputs(self.fixture)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            valid_scorer = root / "valid-scorer.json"
            valid_scorer.write_text(json.dumps(outputs), encoding="utf-8")
            duplicate_fixture = root / "duplicate-fixture.json"
            duplicate_fixture.write_text(
                FIXTURE_PATH.read_text(encoding="utf-8").replace(
                    '"schemaVersion": "1.0",',
                    (
                        '"schemaVersion": "Bearer synthetic-private-secret '
                        'from /Users/private/customer.txt",\n'
                        '  "schemaVersion": "1.0",'
                    ),
                    1,
                ),
                encoding="utf-8",
            )
            duplicate_scorer = root / "duplicate-scorer.json"
            scorer_text = json.dumps(outputs, separators=(",", ":"))
            first_case = self.fixture["cases"][0]["id"]
            duplicate_scorer.write_text(
                scorer_text.replace(
                    f'"{first_case}":',
                    f'"{first_case}":null,"{first_case}":',
                    1,
                ),
                encoding="utf-8",
            )
            duplicate_inputs = (
                ("fixture", duplicate_fixture, valid_scorer, "fixture_contract_invalid"),
                ("scorer", FIXTURE_PATH, duplicate_scorer, "scorer_outputs_invalid"),
            )
            for name, cases, scorer, diagnostic in duplicate_inputs:
                result = subprocess.run(
                    command(cases, scorer, root / f"{name}-evidence.json"),
                    cwd=ROOT, capture_output=True, text=True,
                )
                with self.subTest(duplicate_json=name):
                    self.assertEqual(
                        (1, [diagnostic]),
                        (result.returncode, result.stderr.strip().splitlines()),
                    )

            evidence_path = root / "stale-pass-evidence.json"
            result = subprocess.run(
                command(FIXTURE_PATH, valid_scorer, evidence_path),
                cwd=ROOT, capture_output=True, text=True,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            stale_inode = evidence_path.stat().st_ino
            malformed = root / "malformed-fixture.json"
            malformed_bytes = (
                b'{"private":"Bearer synthetic-private-secret from '
                b'/Users/private/customer.txt"'
            )
            malformed.write_bytes(malformed_bytes)
            result = subprocess.run(
                command(malformed, valid_scorer, evidence_path),
                cwd=ROOT, capture_output=True, text=True,
            )
            evidence = load_json(evidence_path)
            serialized = json.dumps(evidence, sort_keys=True)
            zero_summary = {
                "fixtureCaseCount": 0, "attemptedCount": 0, "passedCount": 0,
                "failedCount": 0, "blockedCount": 0, "notApplicableCount": 0,
            }
            expected_prerequisites = {
                key: "not_applicable" for key in FORWARD_PREREQUISITE_KEYS
            }
            with self.subTest(invalid_fixture="atomic_failure_envelope"):
                self.assertEqual(
                    (
                        1, True, FORWARD_EVIDENCE_KEYS, "fail", "offline",
                        sha256_bytes(malformed_bytes), "fixture_contract_invalid",
                        expected_prerequisites, zero_summary, [], False,
                    ),
                    (
                        result.returncode, stale_inode != evidence_path.stat().st_ino,
                        set(evidence), evidence["status"], evidence["mode"],
                        evidence["fixtureSha256"], evidence["host"]["blockerReason"],
                        evidence["host"]["prerequisites"], evidence["summary"],
                        evidence["cases"],
                        "synthetic-private-secret" in serialized or "/Users/" in serialized,
                    ),
                )
                self.assertNotIn("synthetic-private-secret", result.stderr)
                self.assertNotIn("/Users/", result.stderr)

            plugin_root, listing = _build_forward_plugin_tree(root / "plugin-json")
            duplicate_listing = json.dumps(listing).replace(
                '"enabled": true', '"enabled": false, "enabled": true', 1
            )
            with mock.patch.object(self.runner, "ROOT", root / "plugin-json"):
                with self.subTest(duplicate_json="plugin_listing"):
                    self.assertFalse(
                        self.runner._plugin_is_installed_enabled_with_capabilities(duplicate_listing)
                    )

            duplicate_manifest = (
                '{"name":"wrong-plugin",'
                '"name":"apple-foundation-models-handoff",'
                '"interface":{"capabilities":'
                + json.dumps(list(WORKFLOW_SECTIONS))
                + "}}"
            )
            (plugin_root / ".codex-plugin/plugin.json").write_text(
                duplicate_manifest, encoding="utf-8"
            )
            with mock.patch.object(self.runner, "ROOT", root / "plugin-json"):
                with self.subTest(duplicate_json="plugin_manifest"):
                    self.assertFalse(
                        self.runner._plugin_is_installed_enabled_with_capabilities(json.dumps(listing))
                    )

    def test_plugin_topology_is_exactly_five_one_file_skill_directories(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for mutation in ("sixth_skill", "extra_skill_file"):
                repo_root = root / mutation
                plugin_root, listing = _build_forward_plugin_tree(repo_root)
                if mutation == "sixth_skill":
                    extra = plugin_root / "skills/unapproved-sixth-skill/SKILL.md"
                    extra.parent.mkdir(parents=True)
                    extra.write_text(
                        "---\nname: unapproved-sixth-skill\n---\n",
                        encoding="utf-8",
                    )
                elif mutation == "extra_skill_file":
                    (plugin_root / "skills" / SKILLS[0] / "EXTRA.md").write_text(
                        "unapproved extra payload\n", encoding="utf-8"
                    )
                with mock.patch.object(self.runner, "ROOT", repo_root):
                    with self.subTest(plugin_topology=mutation):
                        self.assertFalse(
                            self.runner._plugin_is_installed_enabled_with_capabilities(
                                json.dumps(listing)
                            )
                        )

    def test_plugin_activation_is_nonpass_until_fresh_host_cases_prove_it(self) -> None:
        snapshot = _passing_prerequisites()
        with self.subTest(evidence="structural_only"):
            structural = self.runner._prerequisite_statuses(snapshot, None)
            self.assertEqual("pass", structural["discovery"])
            self.assertEqual("pass", structural["installation"])
            self.assertNotEqual("pass", structural["pluginActivation"])

        fixture = _forward_fixture("DEV136-FWD-DESIGN-001")
        outputs = _forward_outputs(fixture)
        with self.subTest(evidence="fresh_host_cases"):
            code, evidence = _run_host(
                self.runner,
                fixture,
                str(TEST_EXECUTABLE_PATH),
                _FakeHostProcess(),
                _FakePrerequisiteChecker(snapshot),
                _FakeScorer(outputs),
            )
            self.assertEqual(self.runner.PASS, code)
            self.assertEqual(
                "pass",
                evidence["host"]["prerequisites"]["pluginActivation"],
            )


if __name__ == "__main__":
    unittest.main()
