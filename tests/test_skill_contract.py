from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT / "plugins/apple-foundation-models-handoff/skills"

SKILL_DESCRIPTIONS = {
    "design-apple-foundation-models-handoff": (
        "Design an Apple Foundation Models handoff architecture, topology, pattern, "
        "state model, or trust boundary when the user is creating or materially "
        "revising how sessions, profiles, or providers transfer control or provide "
        "isolated consultation."
    ),
    "implement-apple-foundation-models-handoff": (
        "Implement an Apple Foundation Models handoff architecture when an approved "
        "architecture or decision reference and an exact application change boundary "
        "already exist."
    ),
    "review-apple-foundation-models-handoff": (
        "Review an existing Apple Foundation Models handoff artifact when the user "
        "wants severity-ranked findings about architecture, Apple API grounding, "
        "state, security, recovery, or evidence claims rather than changes."
    ),
    "debug-apple-foundation-models-handoff": (
        "Debug an Apple Foundation Models handoff when an observed routing, ownership, "
        "transition, context, tool, effect, recovery, fallback, availability, or "
        "version-labelled behavior differs from its expected contract and the cause "
        "is not yet established."
    ),
    "validate-apple-foundation-models-handoff": (
        "Validate an Apple Foundation Models handoff artifact when the user requests "
        "reproducible proof, a complete pass/fail/blocked/not_applicable matrix, "
        "cross-host comparison, or release implication rather than design, edits, "
        "findings-only review, or diagnosis."
    ),
}

SKILLS = tuple(SKILL_DESCRIPTIONS)

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

ADJACENT_NON_TRIGGERS = (
    "Apple Handoff",
    "NSUserActivity",
    "App Intents",
    "Swift actors",
    "generic Core ML",
    "coding-session handoff",
    "Agent Skills",
    "Foundation Models runtime Skills",
)

RESULT_FIELDS = (
    "activationStatus",
    "selectedSkill",
    "routerInput",
    "architectureResult",
    "architectureSchemaVersion",
    "stateVersion",
    "policyVersion",
    "workflow",
    "scope",
    "pattern",
    "source",
    "destination",
    "finalResponseOwner",
    "apiAvailability",
    "stateModel",
    "trustBoundaries",
    "contextPolicy",
    "toolAndEffectPolicy",
    "failurePolicy",
    "verification",
    "limitations",
)

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

REFERENCE_NAMES = (
    "architecture-and-state.md",
    "orchestration-patterns.md",
    "apple-api-availability.md",
    "security-context-and-recovery.md",
    "evaluation-and-observability.md",
)


class SkillContractTests(unittest.TestCase):
    def require_skill_text(self, skill: str) -> str:
        path = SKILLS_ROOT / skill / "SKILL.md"
        self.assertTrue(path.is_file(), f"{path}: required production skill is missing")
        self.assertFalse(path.is_symlink(), f"{path}: skill must be an authored file")
        return path.read_text(encoding="utf-8")

    def test_exact_five_skill_surface_has_one_authored_file_each(self) -> None:
        self.assertTrue(
            SKILLS_ROOT.is_dir(),
            f"{SKILLS_ROOT}: required production skill root is missing",
        )
        observed = sorted(path.name for path in SKILLS_ROOT.iterdir())
        self.assertEqual(sorted(SKILLS), observed)

        for skill in SKILLS:
            with self.subTest(skill=skill):
                directory = SKILLS_ROOT / skill
                self.assertTrue(directory.is_dir())
                self.assertFalse(directory.is_symlink())
                self.assertEqual(["SKILL.md"], sorted(path.name for path in directory.iterdir()))

    def test_frontmatter_is_exact_and_activation_descriptions_match_dev_134(self) -> None:
        for skill, description in SKILL_DESCRIPTIONS.items():
            with self.subTest(skill=skill):
                text = self.require_skill_text(skill)
                expected = (
                    f"---\nname: {skill}\ndescription: {description}\n---\n"
                )
                self.assertTrue(
                    text.startswith(expected),
                    f"{skill}: frontmatter must contain only exact name and description",
                )
                self.assertTrue(text.removeprefix(expected).strip())

    def test_router_clarification_review_first_and_non_activation_rules_are_explicit(
        self,
    ) -> None:
        required_semantics = (
            "Choose exactly one primary workflow",
            "Ask exactly one targeted clarification",
            "review first",
            "separate authorized follow-on boundary",
            "Do not invoke another skill",
            "no_activation",
            "clarification_required",
            "out_of_domain",
            "approved_contract",
            "missingInput",
            "question",
            "Do not emit `architectureResult` for `no_activation` or "
            "`clarification_required`",
        )
        for skill in SKILLS:
            with self.subTest(skill=skill):
                text = self.require_skill_text(skill)
                for field, values in ROUTER_ENUMS.items():
                    self.assertIn(field, text)
                    for value in values:
                        self.assertRegex(text, rf"(?<![A-Za-z0-9_]){re.escape(value)}(?![A-Za-z0-9_])")
                for requirement in required_semantics:
                    self.assertIn(requirement, text)
                for non_trigger in ADJACENT_NON_TRIGGERS:
                    self.assertIn(non_trigger, text)

    def test_positive_result_schema_versions_and_sections_are_complete(self) -> None:
        for skill in SKILLS:
            with self.subTest(skill=skill):
                text = self.require_skill_text(skill)
                self.assertIn('architectureSchemaVersion: "1.0"', text)
                for field in RESULT_FIELDS:
                    self.assertRegex(
                        text,
                        rf"(?<![A-Za-z0-9_]){re.escape(field)}(?![A-Za-z0-9_])",
                    )
                normalized = re.sub(r"\s+", " ", text)
                self.assertRegex(
                    normalized,
                    r"(?i)(?:independent.{0,80}stateVersion|stateVersion.{0,80}independent)",
                )
                self.assertRegex(
                    normalized,
                    r"(?i)(?:independent.{0,80}policyVersion|policyVersion.{0,80}independent)",
                )
                for section in (*COMMON_SECTIONS, *WORKFLOW_SECTIONS[skill]):
                    self.assertIn(section, text)

    def test_apple_claim_compile_pseudocode_unsupported_and_blocker_rules_are_explicit(
        self,
    ) -> None:
        required_evidence = (
            "official Apple documentation",
            "installed SDK interfaces",
            "WWDC",
            "Apple-owned repositories",
            "compile-check",
            "pseudocode",
            "unsupported",
            "blocked",
            "not_applicable",
            "compiled_sdk_26_5",
            "interface_verified_sdk_26_5",
        )
        for skill in SKILLS:
            with self.subTest(skill=skill):
                text = self.require_skill_text(skill)
                for requirement in required_evidence:
                    self.assertIn(requirement, text)
                self.assertRegex(
                    re.sub(r"\s+", " ", text),
                    r"(?i)missing (?:SDK|host|toolchain|binary|hardware|prerequisite).{0,100}blocked",
                )

    def test_each_skill_uses_only_exact_direct_fixed_reference_links(self) -> None:
        expected = {f"../../references/{name}" for name in REFERENCE_NAMES}
        for skill in SKILLS:
            with self.subTest(skill=skill):
                text = self.require_skill_text(skill)
                targets = re.findall(r"\[[^]]+\]\(([^)]+references/[^)]+)\)", text)
                self.assertEqual(len(expected), len(targets))
                self.assertEqual(expected, set(targets))
                self.assertNotRegex(text, r"\]\((?!\.\./\.\./references/)[^)]+references/")


if __name__ == "__main__":
    unittest.main()
