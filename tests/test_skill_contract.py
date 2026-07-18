from __future__ import annotations

from dataclasses import dataclass
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

ARCHITECTURE_RESULT_FIELDS = (
    "architectureSchemaVersion",
    "stateVersion",
    "policyVersion",
    "workflow",
    "scope",
    "pattern",
    "source",
    "destination",
    "finalResponseOwner",
    "apiAvailability[]",
    "stateModel",
    "trustBoundaries[]",
    "contextPolicy",
    "toolAndEffectPolicy",
    "failurePolicy",
    "verification[]",
    "limitations[]",
)

POSITIVE_RESULT_LINES = (
    "activationStatus = activated",
    "selectedSkill = {skill}",
    "routerInput = { domain = <domain>, requestedOperation = <requestedOperation>, "
    "artifactState = <artifactState>, evidenceState = <evidenceState> }",
    "architectureResult",
    '  architectureSchemaVersion: "1.0"',
    "  stateVersion: <independent state schema version>",
    "  policyVersion: <independent policy version>",
    "  workflow: <selected workflow>",
    "  scope: <bounded artifact and operation scope>",
    "  pattern = baton_pass | isolated_consultation | deterministic_routing | "
    "transcript_transfer",
    "  source = { profile, provider }",
    "  destination = { profile, provider }",
    "  finalResponseOwner: <stable final-response owner>",
    "  apiAvailability[] = { surface, versionLabel, compileStatus, source }",
    "  stateModel: <versioned reducer state and lifecycle>",
    "  trustBoundaries[]: <classified trust boundaries>",
    "  contextPolicy: <minimum-context transfer policy>",
    "  toolAndEffectPolicy: <tool, confirmation, and effect authority policy>",
    "  failurePolicy: <fail-closed recovery and fallback policy>",
    "  verification[] = { id, layer, status, evidence }",
    "  limitations[]: <one-line limitations and blockers summary; close the fence "
    "immediately after this line>",
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

PROTOCOL_STEPS = (
    "Inspect the repository, relevant artifacts, and installed SDK interfaces before "
    "asserting implementation facts.",
    "Resolve the router inputs and state the selected workflow.",
    "Establish the current owner, next owner, trust boundary, and effect authority.",
    "Separate control-plane state from model context and minimize transferred data.",
    "Distinguish consultation from ownership transfer.",
    "Use version-labelled state, deterministic transitions, bounded retries, "
    "idempotency and reconciliation, and explicit recovery and fallback.",
    "Ground Apple claims through installed interfaces and the direct references.",
    "Compile-check Swift examples where supported; otherwise label pseudocode or an "
    "exact blocked prerequisite.",
    "Emit the common result envelope plus workflow-specific sections.",
    "Separate fact, inference, pseudocode, unsupported API, limitation, blocker, and "
    "not_applicable evidence.",
)

PROTOCOL_STEP_PATTERNS = (
    (r"inspect", r"repositor", r"artifact", r"installed SDK interface", r"implementation fact"),
    (r"router input", r"selected workflow"),
    (r"current owner", r"next owner", r"trust boundar", r"effect authorit"),
    (r"control-plane state", r"model context", r"minimiz", r"transferred data"),
    (r"consultation", r"ownership transfer"),
    (
        r"version-label",
        r"deterministic transition",
        r"bounded retr",
        r"idempotenc",
        r"reconcil",
        r"recovery",
        r"fallback",
    ),
    (r"Apple claim", r"installed interface", r"reference"),
    (r"compile-check", r"Swift", r"supported", r"pseudocode", r"blocked prerequisite"),
    (r"common result envelope", r"workflow-specific section"),
    (
        r"fact",
        r"inference",
        r"pseudocode",
        r"unsupported API",
        r"limitation",
        r"blocker",
        r"not_applicable",
    ),
)

NO_ACTIVATION_FIELDS = (
    "activationStatus",
    "reasonCode",
    "domain",
    "requestedOperation",
)
CLARIFICATION_FIELDS = (
    "activationStatus",
    "clarificationKind",
    "missingInput",
    "question",
)
VERIFICATION_STATUSES = ("pass", "fail", "blocked", "not_applicable")
NO_ACTIVATION_VALUES = {
    "activationStatus": "no_activation",
    "reasonCode": "out_of_domain",
    "domain": "out_of_domain",
    "requestedOperation": " | ".join(ROUTER_ENUMS["requestedOperation"]),
}
CLARIFICATION_VALUES = {
    "activationStatus": "clarification_required",
    "clarificationKind": "domain | approved_contract",
    "missingInput": "domain | approved_contract",
    "question": "<one bounded question>",
}

CORE_SEMANTIC_SECTION_TITLES = (
    "Routing and Inspection",
    "Common Workflow Protocol",
    "Output Contract",
    "References",
    "Guardrails",
)

CONTROLLED_AVAILABILITY_LABELS = (
    "compiled_sdk_26_5",
    "interface_verified_sdk_26_5",
    "official_os_xcode_27_beta_locally_unverified",
    "pseudocode_deterministic_mock",
    "blocked",
)

STABLE_INVARIANT_SENTENCES = {
    "Pattern and Ownership": (
        "Maintain exactly one stable owner at every state; only that owner authorizes "
        "the next transition, and model output, provider output, and tools never "
        "become the owner.",
    ),
    "State and Lifecycle": (
        "For every allowed edge, define finite transition, tool-call, and "
        "external-effect budgets.",
        "Validate the event, source phase, allowed edge, grant, stateVersion, and "
        "policyVersion before mutating any budget.",
        "Persist the checkpoint before setting the phase to transitioning; only then "
        "may the reducer emit at most one executor command.",
        "Treat stateVersion and policyVersion as independent values, each with its "
        "own compatibility and migration rule.",
        "Terminate only from a stable phase with no unresolved pending command, "
        "pending effect, or recovery requirement.",
    ),
    "Trust and Model Boundaries": (
        "Classify every context field atomically as C0, C1, C2, or C3 before "
        "transfer; reject the whole envelope when any field is unknown or "
        "disallowed.",
        "Bind every grant to person, session, source profile, source provider, "
        "destination profile, destination provider, purpose, exact context classes, "
        "exact fields, tools, retention, expiry, C2 permission, stateVersion, and "
        "policyVersion. Invalidate and revalidate the grant before use whenever any "
        "binding drifts.",
    ),
    "Tools Effects and Confirmation": (
        "Accept a tool result only when its call ID, tool ID, tool version, provider, "
        "result type, and current state match the pending invocation; otherwise "
        "reject it.",
        "Require confirmation plus an application-controlled effect ID and "
        "application-owned effect ledger; execute every external effect at most once "
        "and reconcile ledger state with external truth before retry or replay.",
    ),
    "Failure Recovery and Fallback": (
        "When external truth is uncertain, set recoveryRequired and remain in "
        "recovery until reconciliation proves the outcome.",
        "While recoveryRequired, late results, replay events, and cancellation "
        "preserve authority, pending command and effect, checkpoint, "
        "transition/tool/effect counts, effect ledger, and repair facts "
        "byte-identically and emit no executor command.",
        "Fallback never expands trust: it cannot widen context, provider, tool, "
        "effect, retention, grant, or authority boundaries.",
    ),
}

AVAILABILITY_ERROR_BOUNDARY_SENTENCE = (
    "Record stable SDK 26.5 compile and interface errors separately from locally "
    "unverified OS/Xcode 27 beta errors."
)
DESIGN_READ_ONLY_SENTENCE = "Design is read-only: make no production edits."
INTEGRATION_BLOCKER_REASON = "production_skills_not_integrated"
INTEGRATION_BLOCKER_SENTENCE = (
    "A missing fixed reference is reported as blocked with reason "
    f"`{INTEGRATION_BLOCKER_REASON}`."
)

OUTPUT_SERIALIZATION_SENTENCES = (
    (
        "literal 21-line result envelope",
        "Every activated response emits exactly the 21 shown nonblank "
        "result-envelope lines in order with placeholders replaced inline and no "
        "added lines.",
    ),
    (
        "line-21 fence terminator",
        "Close the result-envelope fence immediately after that 21st line, and put "
        "every explanation, bullet, subfield, example, and detail only under the "
        "required headings after the fence.",
    ),
    (
        "single-line result envelope serialization",
        "Never wrap, pretty-print, or expand `routerInput` or any "
        "`architectureResult` child across physical lines, keeping each on its "
        "single template line.",
    ),
    (
        "selected skill assignment",
        "Serialize `selectedSkill` as the literal assignment "
        "`selectedSkill = {skill}`.",
    ),
    (
        "router and architecture line adjacency",
        "Serialize all four populated `routerInput` values on exactly one physical "
        "line, with `architectureResult` on the immediately following line.",
    ),
    (
        "single response envelope fence",
        "Emit exactly one response-level fenced `text` block, reserve it for the "
        "result envelope, and emit no additional fenced `text` blocks.",
    ),
    (
        "exact response headings",
        "After the envelope, render only the exact required headings, each exactly "
        "once and in the listed order.",
    ),
)

OUTER_HARNESS_GUARDRAIL_SENTENCES = (
    (
        "recursive host invocation prohibition",
        "Never invoke `codex exec`, `tests/e2e/codex_skill_forward_tests.py`, or a "
        "Claude/Codex host matrix from inside this skill.",
    ),
    (
        "missing outer evidence blocker",
        "Existing normalized host evidence may be inspected, but missing "
        "outer-harness evidence is `blocked`.",
    ),
)


@dataclass(frozen=True)
class MarkdownSection:
    level: int
    title: str
    heading_start: int
    content_start: int
    end: int
    direct_body: str
    body: str


def parse_markdown_sections(text: str) -> tuple[MarkdownSection, ...]:
    headings: list[tuple[int, str, int, int]] = []
    offset = 0
    fence: str | None = None
    for line in text.splitlines(keepends=True):
        fence_match = re.match(r"^\s*(```+|~~~+)", line)
        if fence_match:
            marker = fence_match.group(1)[:3]
            fence = None if fence == marker else marker
        elif fence is None:
            heading = re.match(r"^(#{2,6})[ \t]+(.+?)\s*(?:\n)?$", line)
            if heading:
                headings.append(
                    (len(heading.group(1)), heading.group(2), offset, offset + len(line))
                )
        offset += len(line)

    sections: list[MarkdownSection] = []
    for index, (level, title, heading_start, content_start) in enumerate(headings):
        end = len(text)
        for next_level, _, next_start, _ in headings[index + 1 :]:
            if next_level <= level:
                end = next_start
                break
        direct_end = headings[index + 1][2] if index + 1 < len(headings) else end
        direct_end = min(direct_end, end)
        sections.append(
            MarkdownSection(
                level=level,
                title=title,
                heading_start=heading_start,
                content_start=content_start,
                end=end,
                direct_body=text[content_start:direct_end].strip(),
                body=text[content_start:end].strip(),
            )
        )
    return tuple(sections)


def normalize_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


def semantic_section(
    test_case: unittest.TestCase,
    sections: tuple[MarkdownSection, ...],
    *keywords: str,
) -> MarkdownSection:
    candidates = [
        section
        for section in sections
        if section.level == 2
        and all(keyword in normalize_title(section.title) for keyword in keywords)
    ]
    test_case.assertEqual(
        1,
        len(candidates),
        f"expected one level-two section matching {keywords}",
    )
    return candidates[0]


def direct_children(
    sections: tuple[MarkdownSection, ...], parent: MarkdownSection
) -> tuple[MarkdownSection, ...]:
    return tuple(
        section
        for section in sections
        if section.level == parent.level + 1
        and parent.content_start <= section.heading_start < parent.end
    )


def child_named(
    test_case: unittest.TestCase,
    sections: tuple[MarkdownSection, ...],
    parent: MarkdownSection,
    title: str,
) -> MarkdownSection:
    expected = normalize_title(title)
    matches = [
        child
        for child in direct_children(sections, parent)
        if normalize_title(child.title) == expected
    ]
    test_case.assertEqual(1, len(matches), f"missing structured subsection: {title}")
    return matches[0]


def assigned_fields(body: str) -> list[tuple[str, str]]:
    return re.findall(
        r"(?m)^\s*(?:[-*]\s*)?`?([A-Za-z][A-Za-z0-9]*)`?\s*[:=]\s*(.+?)\s*$",
        body,
    )


def assert_exact_shape(
    test_case: unittest.TestCase,
    section: MarkdownSection,
    expected_fields: tuple[str, ...],
    expected_values: dict[str, str],
) -> None:
    fenced = re.fullmatch(
        r"```text\n(?P<body>.*?)\n```",
        section.body.strip(),
        flags=re.DOTALL,
    )
    if fenced is None:
        test_case.fail(
            f"{section.title} must contain exactly one fenced normalized text block"
        )
    block = fenced.group("body")
    lines = [line for line in block.splitlines() if line.strip()]
    fields = assigned_fields(block)
    test_case.assertEqual(
        len(lines),
        len(fields),
        f"{section.title} block may contain only normalized field assignments",
    )
    test_case.assertEqual(expected_fields, tuple(name for name, _ in fields))
    values = {name: value.strip().strip("`") for name, value in fields}
    test_case.assertEqual(expected_values, values)


def positive_result_lines(skill: str) -> tuple[str, ...]:
    return tuple(line.replace("{skill}", skill) for line in POSITIVE_RESULT_LINES)


def assert_exact_positive_result_shape(
    test_case: unittest.TestCase, section: MarkdownSection, skill: str
) -> None:
    fenced = re.fullmatch(
        r"```text\n(?P<body>.*?)\n```",
        section.direct_body,
        flags=re.DOTALL,
    )
    if fenced is None:
        test_case.fail(
            "positive result must contain exactly one fenced normalized text block"
        )
    test_case.assertEqual("\n".join(positive_result_lines(skill)), fenced.group("body"))


def assert_non_positive_exclusions(
    test_case: unittest.TestCase, section: MarkdownSection
) -> None:
    forbidden_sections = {
        *COMMON_SECTIONS,
        *(title for titles in WORKFLOW_SECTIONS.values() for title in titles),
    }
    test_case.assertNotIn("architectureResult", section.body)
    test_case.assertNotIn("../../references/", section.body)
    for title in forbidden_sections:
        test_case.assertNotRegex(
            section.body,
            rf"(?mi)^\s*#{{2,6}}\s+{re.escape(title)}\s*$",
        )
    test_case.assertNotRegex(
        section.body,
        re.compile(
            r"compiled_sdk_|interface_verified_sdk_|official Apple documentation|"
            r"Apple API Availability|\bhost\b.{0,80}(?:activat|evidence)",
            re.IGNORECASE | re.DOTALL,
        ),
    )


def enum_values(body: str, field: str) -> tuple[str, ...]:
    match = re.search(
        rf"(?mi)^\s*(?:[-*]\s*)?`?{re.escape(field)}`?\s*[:=]\s*(.+?)\s*$",
        body,
    )
    if match is None:
        return ()
    return tuple(re.findall(r"\b[a-z][A-Za-z0-9_]*\b", match.group(1)))


def numbered_items(body: str) -> tuple[tuple[int, str], ...]:
    markers = list(re.finditer(r"(?m)^\s*(\d+)\.\s+", body))
    items = []
    for index, marker in enumerate(markers):
        end = markers[index + 1].start() if index + 1 < len(markers) else len(body)
        items.append((int(marker.group(1)), body[marker.end() : end].strip()))
    return tuple(items)


def section_owns(section: MarkdownSection, position: int) -> bool:
    return section.heading_start <= position < section.end


def flexible_phrase_pattern(phrase: str) -> re.Pattern[str]:
    return re.compile(
        r"\s+".join(re.escape(token) for token in phrase.split()),
        re.IGNORECASE,
    )


def assert_single_owned_phrase(
    test_case: unittest.TestCase,
    text: str,
    owner: MarkdownSection,
    phrase: str,
    label: str,
) -> None:
    matches = tuple(flexible_phrase_pattern(phrase).finditer(text))
    test_case.assertEqual(1, len(matches), f"missing stable invariant: {label}")
    match = matches[0]
    test_case.assertTrue(
        owner.content_start <= match.start() and match.end() <= owner.end,
        f"{label} must occur only under {owner.title}",
    )


def output_serialization_sentences(skill: str) -> tuple[tuple[str, str], ...]:
    return tuple(
        (label, sentence.replace("{skill}", skill))
        for label, sentence in OUTPUT_SERIALIZATION_SENTENCES
    )


def assert_output_serialization_contract(
    test_case: unittest.TestCase,
    text: str,
    output: MarkdownSection,
    skill: str,
) -> None:
    selected_assignment = f"selectedSkill = {skill}"
    selected_matches = tuple(
        re.finditer(rf"(?m)^{re.escape(selected_assignment)}$", text)
    )
    test_case.assertEqual(
        1,
        len(selected_matches),
        f"{skill}: positive envelope must contain its literal selectedSkill assignment",
    )
    selected_match = selected_matches[0]
    test_case.assertTrue(
        output.content_start <= selected_match.start()
        and selected_match.end() <= output.end,
        "literal selectedSkill assignment must be owned by Output Contract",
    )
    for label, sentence in output_serialization_sentences(skill):
        assert_single_owned_phrase(test_case, text, output, sentence, label)


def assert_outer_harness_guardrails(
    test_case: unittest.TestCase,
    text: str,
    guardrails: MarkdownSection,
) -> None:
    for label, sentence in OUTER_HARNESS_GUARDRAIL_SENTENCES:
        assert_single_owned_phrase(test_case, text, guardrails, sentence, label)


def assert_pattern_owned(
    test_case: unittest.TestCase,
    text: str,
    pattern: re.Pattern[str],
    owner: MarkdownSection,
    label: str,
) -> None:
    matches = tuple(pattern.finditer(text))
    test_case.assertTrue(matches, f"missing owned contract content: {label}")
    for match in matches:
        test_case.assertTrue(
            section_owns(owner, match.start()),
            f"{label} must occur only under {owner.title}",
        )


def assert_stable_handoff_invariants(
    test_case: unittest.TestCase,
    text: str,
    sections: tuple[MarkdownSection, ...],
    output: MarkdownSection,
    guardrails: MarkdownSection,
    skill: str,
) -> None:
    for title, phrases in STABLE_INVARIANT_SENTENCES.items():
        owner = child_named(test_case, sections, output, title)
        for index, phrase in enumerate(phrases, start=1):
            assert_single_owned_phrase(
                test_case,
                text,
                owner,
                phrase,
                f"{title} invariant {index}",
            )

    availability = child_named(
        test_case, sections, output, "Apple API Availability"
    )
    assignment_pattern = re.compile(
        r"(?mi)^\s*(?:[-*]\s*)?`?versionLabel`?\s*[:=]\s*(.+?)\s*$"
    )
    assignments = tuple(assignment_pattern.finditer(text))
    test_case.assertEqual(
        1,
        len(assignments),
        "versionLabel must have exactly one controlled-vocabulary assignment",
    )
    assignment = assignments[0]
    test_case.assertTrue(
        availability.content_start <= assignment.start()
        and assignment.end() <= availability.end,
        "versionLabel vocabulary must be owned by Apple API Availability",
    )
    test_case.assertEqual(
        CONTROLLED_AVAILABILITY_LABELS,
        tuple(re.findall(r"\b[a-z][a-z0-9_]*\b", assignment.group(1))),
        "versionLabel vocabulary must be exact and closed",
    )
    assert_single_owned_phrase(
        test_case,
        text,
        availability,
        AVAILABILITY_ERROR_BOUNDARY_SENTENCE,
        "stable SDK versus OS/Xcode 27 beta error boundary",
    )

    if skill == "design-apple-foundation-models-handoff":
        activation = child_named(test_case, sections, output, "Activation and Scope")
        assert_single_owned_phrase(
            test_case,
            text,
            activation,
            DESIGN_READ_ONLY_SENTENCE,
            "design no-production-edit boundary",
        )
        blocker_relationship = re.compile(
            r"(?:If\s+a\s+fixed\s+reference\s+target\s+is\s+absent|"
            r"A\s+missing\s+fixed\s+reference)"
            r"[^.]{0,160}?"
            r"(?:is\s+reported|report(?:s|ed)?)"
            r"[^.]{0,160}?"
            r"as\s+blocked\s+with\s+reason\s+`"
            + re.escape(INTEGRATION_BLOCKER_REASON)
            + r"`",
            re.IGNORECASE,
        )
        blocker_matches = tuple(blocker_relationship.finditer(text))
        test_case.assertEqual(
            1,
            len(blocker_matches),
            "design must bind a missing fixed reference to blocked with the exact "
            "integration reason",
        )
        blocker_match = blocker_matches[0]
        test_case.assertTrue(
            guardrails.content_start <= blocker_match.start()
            and blocker_match.end() <= guardrails.end,
            "design missing-reference blocker relationship belongs only to Guardrails",
        )


def numbered_item_spans(text: str) -> tuple[tuple[int, str], ...]:
    markers = list(re.finditer(r"(?m)^\s*\d+\.\s+", text))
    headings = list(re.finditer(r"(?m)^#{2,6}[ \t]+", text))
    items = []
    for index, marker in enumerate(markers):
        boundaries = [
            candidate.start()
            for candidate in (*markers[index + 1 :], *headings)
            if candidate.start() > marker.start()
        ]
        end = min(boundaries, default=len(text))
        items.append((marker.start(), text[marker.end() : end].strip()))
    return tuple(items)


def assert_exclusive_section_ownership(
    test_case: unittest.TestCase,
    text: str,
    sections: tuple[MarkdownSection, ...],
    routing: MarkdownSection,
    protocol: MarkdownSection,
    output: MarkdownSection,
    references: MarkdownSection,
    guardrails: MarkdownSection,
    skill: str,
) -> None:
    core_owners = dict(
        zip(
            CORE_SEMANTIC_SECTION_TITLES,
            (routing, protocol, output, references, guardrails),
            strict=True,
        )
    )
    for title, owner in core_owners.items():
        matches = [
            section
            for section in sections
            if normalize_title(section.title) == normalize_title(title)
        ]
        test_case.assertEqual(
            [owner],
            matches,
            f"{title} must appear exactly once as its level-two owner",
        )

    assignment_pattern = re.compile(
        r"(?m)^\s*(?:[-*]\s*)?`?([A-Za-z][A-Za-z0-9]*)`?\s*[:=]"
    )
    router_fields = {
        *ROUTER_ENUMS,
        "reasonCode",
        "clarificationKind",
        "missingInput",
        "question",
    }
    for assignment in assignment_pattern.finditer(text):
        field = assignment.group(1)
        if field in RESULT_FIELDS:
            allowed = section_owns(output, assignment.start()) or (
                field == "activationStatus"
                and section_owns(routing, assignment.start())
            )
            test_case.assertTrue(
                allowed,
                f"machine output field {field} must be owned by Output Contract",
            )
        if field in router_fields:
            test_case.assertTrue(
                section_owns(routing, assignment.start()),
                f"router field {field} must be owned by Routing and Inspection",
            )

    distinctive_output_fields = tuple(
        field
        for field in RESULT_FIELDS
        if any(character.isupper() for character in field)
        and field != "activationStatus"
    )
    for field in distinctive_output_fields:
        for occurrence in re.finditer(
            rf"(?<![A-Za-z0-9_]){re.escape(field)}(?![A-Za-z0-9_])", text
        ):
            allowed = section_owns(output, occurrence.start()) or (
                field == "architectureResult"
                and section_owns(guardrails, occurrence.start())
            )
            test_case.assertTrue(
                allowed,
                f"output identifier {field} must be owned by Output Contract",
            )

    expected_output_titles = {
        normalize_title(title)
        for title in (*COMMON_SECTIONS, *WORKFLOW_SECTIONS[skill])
    }
    for title in expected_output_titles:
        matches = [
            section
            for section in sections
            if normalize_title(section.title) == title
        ]
        test_case.assertEqual(1, len(matches), f"duplicate output heading: {title}")
        test_case.assertTrue(
            section_owns(output, matches[0].heading_start),
            f"output heading {title} must be owned by Output Contract",
        )

    availability = child_named(
        test_case, sections, output, "Apple API Availability"
    )
    evidence_label_pair = re.compile(
        r"compiled_sdk_26_5.{0,60}interface_verified_sdk_26_5",
        re.IGNORECASE | re.DOTALL,
    )
    for match in evidence_label_pair.finditer(text):
        test_case.assertTrue(
            section_owns(availability, match.start())
            or section_owns(guardrails, match.start()),
            "controlled evidence labels belong only to Apple API Availability or Guardrails",
        )

    expected_targets = tuple(f"../../references/{name}" for name in REFERENCE_NAMES)
    for target in expected_targets:
        matches = tuple(re.finditer(re.escape(target), text))
        test_case.assertEqual(1, len(matches), f"duplicate or missing reference: {target}")
        test_case.assertTrue(
            section_owns(references, matches[0].start()),
            f"reference {target} must be owned by References",
        )

    guardrail_patterns = (
        re.compile(
            r"Use(?: exact)?\s+compiled_sdk_26_5.{0,60}"
            r"interface_verified_sdk_26_5.{0,60}(?:only|labels)",
            re.IGNORECASE | re.DOTALL,
        ),
        re.compile(
            r"ground\s+(?:Apple\s+)?claims.{0,80}official Apple documentation.{0,80}"
            r"installed SDK interfaces.{0,80}WWDC.{0,80}Apple-owned repositories",
            re.IGNORECASE | re.DOTALL,
        ),
        re.compile(
            r"compile-check.{0,80}Swift.{0,80}supported.{0,80}label.{0,40}"
            r"pseudocode.{0,80}unsupported",
            re.IGNORECASE | re.DOTALL,
        ),
        re.compile(
            r"missing (?:SDK|host|toolchain|binary|hardware|prerequisite).{0,140}"
            r"blocked",
            re.IGNORECASE | re.DOTALL,
        ),
        re.compile(
            r"non-positive results.{0,80}(?:contain|emit|include|load) no.{0,80}"
            r"architectureResult.{0,80}workflow-specific sections.{0,80}references"
            r".{0,80}fabricated Apple claims.{0,80}host activation evidence",
            re.IGNORECASE | re.DOTALL,
        ),
    )
    for index, pattern in enumerate(guardrail_patterns, start=1):
        assert_pattern_owned(
            test_case,
            text,
            pattern,
            guardrails,
            f"guardrail rule {index}",
        )

    routing_phrases = (
        "Choose exactly one primary workflow",
        "Ask exactly one targeted clarification",
        "review first",
        "separate authorized follow-on boundary",
        "Do not invoke another skill",
        "Adjacent non-triggers",
    )
    for phrase in routing_phrases:
        assert_pattern_owned(
            test_case,
            text,
            re.compile(re.escape(phrase), re.IGNORECASE),
            routing,
            phrase,
        )

    for shape_title in ("no_activation", "clarification_required"):
        normalized = normalize_title(shape_title)
        matches = [
            section
            for section in sections
            if normalize_title(section.title) == normalized
        ]
        test_case.assertEqual(1, len(matches), f"duplicate routing shape: {shape_title}")
        test_case.assertTrue(
            section_owns(routing, matches[0].heading_start),
            f"{shape_title} must be owned by Routing and Inspection",
        )

    for position, item in numbered_item_spans(text):
        if section_owns(protocol, position):
            continue
        for patterns in PROTOCOL_STEP_PATTERNS:
            if all(re.search(pattern, item, re.IGNORECASE) for pattern in patterns):
                test_case.fail(
                    "common protocol steps must occur only under Common Workflow Protocol"
                )


def assert_structured_skill_contract(
    test_case: unittest.TestCase, text: str, skill: str
) -> None:
    sections = parse_markdown_sections(text)
    routing = semantic_section(test_case, sections, "routing", "inspection")
    protocol = semantic_section(test_case, sections, "workflow", "protocol")
    output = semantic_section(test_case, sections, "output", "contract")
    references = semantic_section(test_case, sections, "reference")
    guardrails = semantic_section(test_case, sections, "guardrail")
    ordered = (routing, protocol, output, references, guardrails)
    test_case.assertEqual(
        sorted(section.heading_start for section in ordered),
        [section.heading_start for section in ordered],
        "routing, protocol, output, references, and guardrails must be ordered",
    )

    for field, expected in ROUTER_ENUMS.items():
        test_case.assertEqual(expected, enum_values(routing.direct_body, field), field)
    routing_rules = (
        "Choose exactly one primary workflow",
        "Ask exactly one targeted clarification",
        "review first",
        "separate authorized follow-on boundary",
        "Do not invoke another skill",
        *ADJACENT_NON_TRIGGERS,
    )
    for rule in routing_rules:
        test_case.assertIn(rule, routing.direct_body)

    no_activation = child_named(test_case, sections, routing, "no_activation")
    assert_exact_shape(
        test_case,
        no_activation,
        NO_ACTIVATION_FIELDS,
        NO_ACTIVATION_VALUES,
    )
    assert_non_positive_exclusions(test_case, no_activation)
    clarification = child_named(
        test_case, sections, routing, "clarification_required"
    )
    assert_exact_shape(
        test_case,
        clarification,
        CLARIFICATION_FIELDS,
        CLARIFICATION_VALUES,
    )
    assert_non_positive_exclusions(test_case, clarification)

    steps = numbered_items(protocol.body)
    test_case.assertEqual(tuple(range(1, 11)), tuple(number for number, _ in steps))
    for number, ((_, step), patterns) in enumerate(
        zip(steps, PROTOCOL_STEP_PATTERNS, strict=True), start=1
    ):
        for pattern in patterns:
            test_case.assertRegex(
                step,
                re.compile(pattern, re.IGNORECASE),
                f"common protocol step {number} lacks {pattern}",
            )

    assert_exact_positive_result_shape(test_case, output, skill)
    assert_output_serialization_contract(test_case, text, output, skill)

    expected_output_sections = (*COMMON_SECTIONS, *WORKFLOW_SECTIONS[skill])
    observed_output_sections = tuple(
        child.title.strip().strip("*`") for child in direct_children(sections, output)
    )
    test_case.assertEqual(expected_output_sections, observed_output_sections)
    assert_stable_handoff_invariants(
        test_case,
        text,
        sections,
        output,
        guardrails,
        skill,
    )

    verification = child_named(
        test_case, sections, output, "Verification and Evidence"
    )
    status_line = re.search(
        r"(?mi)^\s*(?:[-*]\s*)?`?status`?\s*[:=]\s*(.+?)\s*$",
        verification.body,
    )
    test_case.assertIsNotNone(status_line, "verification status vocabulary is missing")
    observed_statuses = tuple(
        re.findall(r"\b[a-z][a-z0-9_]*\b", status_line.group(1))
    )
    test_case.assertEqual(VERIFICATION_STATUSES, observed_statuses)
    test_case.assertRegex(
        re.sub(r"\s+", " ", verification.body),
        re.compile(
            r"zero denominator.{0,100}not_applicable.{0,80}(?:null value|value.{0,20}null)",
            re.IGNORECASE,
        ),
    )
    assert_exclusive_section_ownership(
        test_case,
        text,
        sections,
        routing,
        protocol,
        output,
        references,
        guardrails,
        skill,
    )
    assert_outer_harness_guardrails(test_case, text, guardrails)

    expected_targets = tuple(f"../../references/{name}" for name in REFERENCE_NAMES)
    reference_pattern = r"\[[^]]+\]\(([^)]+references/[^)]+)\)"
    scoped_targets = tuple(re.findall(reference_pattern, references.body))
    all_targets = tuple(re.findall(reference_pattern, text))
    test_case.assertEqual(expected_targets, scoped_targets)
    test_case.assertEqual(scoped_targets, all_targets, "references must be scoped")

    guardrail_rules = (
        "compiled_sdk_26_5",
        "interface_verified_sdk_26_5",
    )
    normalized_guardrails = guardrails.body.lower()
    for rule in guardrail_rules:
        test_case.assertIn(rule.lower(), normalized_guardrails)
    test_case.assertRegex(
        re.sub(r"\s+", " ", guardrails.body),
        re.compile(
            r"ground (?:Apple )?claims.{0,80}official Apple documentation.{0,80}"
            r"installed SDK interfaces.{0,80}WWDC.{0,80}Apple-owned repositories",
            re.IGNORECASE,
        ),
    )
    test_case.assertRegex(
        re.sub(r"\s+", " ", guardrails.body),
        re.compile(
            r"compile-check.{0,80}Swift.{0,80}supported.{0,80}label.{0,40}"
            r"pseudocode.{0,80}unsupported",
            re.IGNORECASE,
        ),
    )
    test_case.assertRegex(
        re.sub(r"\s+", " ", guardrails.body),
        re.compile(
            r"missing (?:SDK|host|toolchain|binary|hardware|prerequisite).{0,140}blocked",
            re.IGNORECASE,
        ),
    )
    test_case.assertRegex(
        re.sub(r"\s+", " ", guardrails.body),
        re.compile(
            r"non-positive results.{0,80}(?:contain|emit|include|load) no.{0,80}"
            r"architectureResult.{0,80}workflow-specific sections.{0,80}references"
            r".{0,80}fabricated Apple claims.{0,80}host activation evidence",
            re.IGNORECASE,
        ),
    )


def build_valid_skill_fixture(skill: str) -> str:
    description = SKILL_DESCRIPTIONS[skill]
    router_lines = [
        f"{field} = {' | '.join(values)}" for field, values in ROUTER_ENUMS.items()
    ]
    output_fields = "\n".join(("```text", *positive_result_lines(skill), "```"))
    rendered_sections = []
    for section in (*COMMON_SECTIONS, *WORKFLOW_SECTIONS[skill]):
        invariant_sentences = list(STABLE_INVARIANT_SENTENCES.get(section, ()))
        if section == "Activation and Scope":
            invariant_sentences.extend(
                sentence for _, sentence in output_serialization_sentences(skill)
            )
        if section == "Apple API Availability":
            invariant_sentences.extend(
                (
                    "versionLabel = " + " | ".join(CONTROLLED_AVAILABILITY_LABELS),
                    AVAILABILITY_ERROR_BOUNDARY_SENTENCE,
                )
            )
        if (
            skill == "design-apple-foundation-models-handoff"
            and section == "Activation and Scope"
        ):
            invariant_sentences.append(DESIGN_READ_ONLY_SENTENCE)
        if section == "Verification and Evidence":
            body = (
                "status = pass | fail | blocked | not_applicable\n"
                "A zero denominator produces not_applicable with a null value."
            )
        elif invariant_sentences:
            body = "\n".join(invariant_sentences)
        else:
            body = f"Required structured output for {section}."
        rendered_sections.append(f"### {section}\n{body}")
    reference_lines = "\n".join(
        f"- [{name}](../../references/{name})" for name in REFERENCE_NAMES
    )
    protocol_lines = "\n".join(
        f"{number}. {step}" for number, step in enumerate(PROTOCOL_STEPS, start=1)
    )
    return (
        f"---\nname: {skill}\ndescription: {description}\n---\n\n"
        "## Routing and Inspection\n"
        + "\n".join(router_lines)
        + "\nChoose exactly one primary workflow. Ask exactly one targeted clarification. "
        "For compound review and fix, run review first and name a separate authorized "
        "follow-on boundary. Do not invoke another skill.\n"
        "Adjacent non-triggers: "
        + "; ".join(ADJACENT_NON_TRIGGERS)
        + ".\n\n"
        "### no_activation\n"
        "```text\nactivationStatus = no_activation\nreasonCode = out_of_domain\n"
        "domain = out_of_domain\n"
        f"requestedOperation = {NO_ACTIVATION_VALUES['requestedOperation']}\n```\n\n"
        "### clarification_required\n"
        "```text\nactivationStatus = clarification_required\n"
        "clarificationKind = domain | approved_contract\n"
        "missingInput = domain | approved_contract\n"
        "question = <one bounded question>\n```\n\n"
        "## Common Workflow Protocol\n"
        f"{protocol_lines}\n\n"
        "## Output Contract\n"
        f"{output_fields}\n\n"
        + "\n\n".join(rendered_sections)
        + "\n\n## References\n"
        f"{reference_lines}\n\n"
        "## Guardrails\n"
        "Ground claims in official Apple documentation, installed SDK interfaces, "
        "WWDC, and Apple-owned repositories. Use exact compiled_sdk_26_5 and "
        "interface_verified_sdk_26_5 labels. Compile-check Swift examples where "
        "supported; label pseudocode and unsupported APIs. Missing SDK, host, "
        "toolchain, binary, hardware, or prerequisite support is blocked.\n"
        + (
            f"{INTEGRATION_BLOCKER_SENTENCE}\n"
            if skill == "design-apple-foundation-models-handoff"
            else ""
        )
        + "\n".join(
            sentence for _, sentence in OUTER_HARNESS_GUARDRAIL_SENTENCES
        )
        + "\nNon-positive results contain no architectureResult, workflow-specific sections, "
        "references, fabricated Apple claims, or host activation evidence.\n"
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
                self.assertEqual(
                    ["SKILL.md"], sorted(path.name for path in directory.iterdir())
                )

    def test_frontmatter_is_exact_and_activation_descriptions_match_dev_134(self) -> None:
        for skill, description in SKILL_DESCRIPTIONS.items():
            with self.subTest(skill=skill):
                text = self.require_skill_text(skill)
                expected = f"---\nname: {skill}\ndescription: {description}\n---\n"
                self.assertTrue(
                    text.startswith(expected),
                    f"{skill}: frontmatter must contain only exact name and description",
                )
                self.assertTrue(text.removeprefix(expected).strip())

    def test_each_skill_has_the_ordered_scoped_executable_contract(self) -> None:
        for skill in SKILLS:
            with self.subTest(skill=skill):
                assert_structured_skill_contract(
                    self, self.require_skill_text(skill), skill
                )

    def test_positive_result_template_is_parseable(self) -> None:
        assignment = re.compile(
            r"\s{2}([A-Za-z][A-Za-z0-9]*(?:\[\])?)\s*(?:=|:)\s*(.+)"
        )
        for skill in SKILLS:
            with self.subTest(skill=skill):
                text = self.require_skill_text(skill)
                sections = parse_markdown_sections(text)
                output = semantic_section(self, sections, "output", "contract")
                templates = re.findall(
                    r"```text\n(.*?)\n```",
                    output.direct_body,
                    flags=re.DOTALL,
                )
                self.assertEqual(
                    1,
                    len(templates),
                    f"{skill}: expected one fenced positive result template",
                )

                lines = templates[0].splitlines()
                preamble = positive_result_lines(skill)[:4]
                self.assertEqual(preamble, tuple(lines[:4]))
                children = lines[4:]
                self.assertEqual(len(ARCHITECTURE_RESULT_FIELDS), len(children))

                parsed: list[tuple[str, str]] = []
                incomplete: list[str] = []
                for raw_line in children:
                    match = assignment.fullmatch(raw_line)
                    if match is None or not match.group(2).strip():
                        incomplete.append(raw_line.strip())
                        continue
                    parsed.append((match.group(1), match.group(2).strip()))
                self.assertEqual(
                    [],
                    incomplete,
                    f"{skill}: architectureResult children must be indented "
                    "nonempty assignments",
                )
                self.assertEqual(
                    ARCHITECTURE_RESULT_FIELDS,
                    tuple(name for name, _ in parsed),
                )

    def test_each_skill_owns_deterministic_response_serialization(self) -> None:
        for skill in SKILLS:
            text = self.require_skill_text(skill)
            sections = parse_markdown_sections(text)
            output = semantic_section(self, sections, "output", "contract")
            selected_assignment = f"selectedSkill = {skill}"
            with self.subTest(skill=skill, requirement="literal selectedSkill"):
                matches = tuple(
                    re.finditer(
                        rf"(?m)^{re.escape(selected_assignment)}$",
                        text,
                    )
                )
                self.assertEqual(
                    1,
                    len(matches),
                    f"{skill}: positive envelope must contain its literal "
                    "selectedSkill assignment",
                )
                self.assertTrue(
                    output.content_start <= matches[0].start()
                    and matches[0].end() <= output.end,
                    "literal selectedSkill assignment must be owned by Output "
                    "Contract",
                )
            for label, sentence in output_serialization_sentences(skill):
                with self.subTest(skill=skill, requirement=label):
                    assert_single_owned_phrase(self, text, output, sentence, label)

    def test_each_skill_owns_non_recursive_outer_harness_guardrails(self) -> None:
        for skill in SKILLS:
            text = self.require_skill_text(skill)
            sections = parse_markdown_sections(text)
            guardrails = semantic_section(self, sections, "guardrail")
            for label, sentence in OUTER_HARNESS_GUARDRAIL_SENTENCES:
                with self.subTest(skill=skill, requirement=label):
                    assert_single_owned_phrase(
                        self,
                        text,
                        guardrails,
                        sentence,
                        label,
                    )


class SkillContractMutationTests(unittest.TestCase):
    skill = SKILLS[0]

    def assert_rejected(self, text: str) -> None:
        with self.assertRaises(AssertionError):
            assert_structured_skill_contract(self, text, self.skill)

    def assert_skill_rejected(self, text: str, skill: str) -> None:
        with self.assertRaises(AssertionError):
            assert_structured_skill_contract(self, text, skill)

    def test_reference_fixture_satisfies_the_structured_oracle(self) -> None:
        assert_structured_skill_contract(
            self, build_valid_skill_fixture(self.skill), self.skill
        )

    def test_deterministic_output_and_outer_harness_mutations_are_rejected(
        self,
    ) -> None:
        for skill in SKILLS:
            fixture = build_valid_skill_fixture(skill)
            selected_assignment = f"selectedSkill = {skill}"
            mutations = {
                "wrong literal selectedSkill": fixture.replace(
                    selected_assignment,
                    "selectedSkill = wrong-skill",
                    1,
                ),
            }
            for label, sentence in output_serialization_sentences(skill):
                mutations[f"missing output rule: {label}"] = fixture.replace(
                    sentence,
                    "",
                    1,
                )
                mutations[f"misplaced output rule: {label}"] = fixture.replace(
                    sentence,
                    "",
                    1,
                ).replace(
                    "## Guardrails\n",
                    f"## Guardrails\n{sentence}\n",
                    1,
                )
            for label, sentence in OUTER_HARNESS_GUARDRAIL_SENTENCES:
                mutations[f"missing guardrail: {label}"] = fixture.replace(
                    sentence,
                    "",
                    1,
                )
                mutations[f"misplaced guardrail: {label}"] = fixture.replace(
                    sentence,
                    "",
                    1,
                ).replace(
                    "## Output Contract\n",
                    f"## Output Contract\n{sentence}\n",
                    1,
                )

            for mutation, candidate in mutations.items():
                with self.subTest(skill=skill, mutation=mutation):
                    self.assert_skill_rejected(candidate, skill)

    def test_flat_token_dump_is_rejected(self) -> None:
        fixture = build_valid_skill_fixture(self.skill)
        flat_dump = re.sub(r"(?m)^#{2,6}\s+", "", fixture)

        self.assert_rejected(flat_dump)

    def test_stable_invariant_removal_misplacement_and_token_dumps_are_rejected(
        self,
    ) -> None:
        for skill in SKILLS:
            fixture = build_valid_skill_fixture(skill)
            cases = [
                (title, phrase)
                for title, phrases in STABLE_INVARIANT_SENTENCES.items()
                for phrase in phrases
            ]
            cases.append(
                ("Apple API Availability", AVAILABILITY_ERROR_BOUNDARY_SENTENCE)
            )
            if skill == "design-apple-foundation-models-handoff":
                cases.append(("Activation and Scope", DESIGN_READ_ONLY_SENTENCE))

            for owner_title, phrase in cases:
                removed = fixture.replace(phrase, "", 1)
                misplaced = removed.replace(
                    "## Guardrails\n",
                    f"## Guardrails\n{phrase}\n",
                    1,
                )
                tokens = sorted(
                    set(re.findall(r"[A-Za-z][A-Za-z0-9_-]*", phrase.lower()))
                )
                token_dump = fixture.replace(
                    phrase,
                    "Invariant tokens: " + " | ".join(tokens) + ".",
                    1,
                )
                for mutation, candidate in (
                    ("removed", removed),
                    ("misplaced", misplaced),
                    ("token dump", token_dump),
                ):
                    with self.subTest(
                        skill=skill,
                        owner=owner_title,
                        invariant=phrase,
                        mutation=mutation,
                    ):
                        self.assert_skill_rejected(candidate, skill)

    def test_availability_vocabulary_mutations_are_rejected_for_every_skill(
        self,
    ) -> None:
        assignment = "versionLabel = " + " | ".join(
            CONTROLLED_AVAILABILITY_LABELS
        )
        for skill in SKILLS:
            fixture = build_valid_skill_fixture(skill)
            removed = fixture.replace(assignment, "", 1)
            misplaced = removed.replace(
                "## Guardrails\n",
                f"## Guardrails\n{assignment}\n",
                1,
            )
            token_dump = fixture.replace(
                assignment,
                "Availability tokens: " + " | ".join(CONTROLLED_AVAILABILITY_LABELS),
                1,
            )
            extra = fixture.replace(
                assignment,
                assignment + " | invented_label",
                1,
            )
            for mutation, candidate in (
                ("removed", removed),
                ("misplaced", misplaced),
                ("token dump", token_dump),
                ("extra label", extra),
            ):
                with self.subTest(skill=skill, mutation=mutation):
                    self.assert_skill_rejected(candidate, skill)

    def test_design_read_only_and_integration_reason_are_owned_and_required(
        self,
    ) -> None:
        skill = "design-apple-foundation-models-handoff"
        fixture = build_valid_skill_fixture(skill)
        bounded_reason = INTEGRATION_BLOCKER_SENTENCE
        mutations = {
            "read-only removed": fixture.replace(DESIGN_READ_ONLY_SENTENCE, "", 1),
            "read-only misplaced": fixture.replace(
                DESIGN_READ_ONLY_SENTENCE, "", 1
            ).replace(
                "## Guardrails\n",
                f"## Guardrails\n{DESIGN_READ_ONLY_SENTENCE}\n",
                1,
            ),
            "reason removed": fixture.replace(INTEGRATION_BLOCKER_REASON, "", 1),
            "reason token dump": fixture.replace(
                bounded_reason,
                f"Blocker token dump: {INTEGRATION_BLOCKER_REASON}.",
                1,
            ),
            "reason unrelated": fixture.replace(
                bounded_reason,
                "A missing fixed reference is noted. An unrelated prerequisite is "
                f"blocked with reason `{INTEGRATION_BLOCKER_REASON}`.",
                1,
            ),
            "reason reversed": fixture.replace(
                bounded_reason,
                f"Reason `{INTEGRATION_BLOCKER_REASON}` blocks an unrelated "
                "prerequisite; a fixed reference is missing.",
                1,
            ),
            "reason misplaced": fixture.replace(
                INTEGRATION_BLOCKER_REASON, "", 1
            ).replace(
                "## Routing and Inspection\n",
                f"## Routing and Inspection\n{INTEGRATION_BLOCKER_REASON}\n",
                1,
            ),
        }
        for mutation, candidate in mutations.items():
            with self.subTest(mutation=mutation):
                self.assert_skill_rejected(candidate, skill)

    def test_removed_and_reordered_protocol_steps_are_rejected(self) -> None:
        fixture = build_valid_skill_fixture(self.skill)
        removed = re.sub(r"(?m)^5\..*\n", "", fixture, count=1)
        step_four = f"4. {PROTOCOL_STEPS[3]}"
        step_five = f"5. {PROTOCOL_STEPS[4]}"
        reordered = fixture.replace(
            f"{step_four}\n{step_five}", f"{step_five}\n{step_four}", 1
        )

        for name, candidate in (("removed", removed), ("reordered", reordered)):
            with self.subTest(mutation=name):
                self.assert_rejected(candidate)

    def test_non_positive_shape_omissions_and_malformed_fields_are_rejected(self) -> None:
        fixture = build_valid_skill_fixture(self.skill)
        requested_operation = (
            f"requestedOperation = {NO_ACTIVATION_VALUES['requestedOperation']}\n"
        )
        mutations = {
            "missing requested operation": fixture.replace(
                requested_operation, "", 1
            ),
            "extra positive field": fixture.replace(
                requested_operation,
                f"{requested_operation}architectureResult = <forbidden>\n",
                1,
            ),
            "malformed clarification kind": fixture.replace(
                "clarificationKind = domain | approved_contract",
                "clarificationKind = domain | approved_contract | implementation_detail",
                1,
            ),
            "invalid no activation domain": fixture.replace(
                "domain = out_of_domain",
                "domain = ambiguous",
                1,
            ),
            "invalid requested operation": fixture.replace(
                requested_operation,
                f"{requested_operation.rstrip()} | unknown_action\n",
                1,
            ),
            "invalid missing input": fixture.replace(
                "missingInput = domain | approved_contract",
                "missingInput = implementation_detail",
                1,
            ),
            "fabricated host activation evidence": fixture.replace(
                f"{requested_operation}```",
                f"{requested_operation}```\n"
                "Host activation evidence claims a pass.",
                1,
            ),
        }

        for name, candidate in mutations.items():
            with self.subTest(mutation=name):
                self.assert_rejected(candidate)

    def test_non_positive_shapes_reject_arbitrary_prose_outside_the_exact_block(
        self,
    ) -> None:
        fixture = build_valid_skill_fixture(self.skill)
        requested_operation = (
            f"requestedOperation = {NO_ACTIVATION_VALUES['requestedOperation']}\n"
        )
        mutations = {
            "no activation prose": fixture.replace(
                f"{requested_operation}```",
                f"{requested_operation}```\n"
                "Arbitrary prose is forbidden here.",
                1,
            ),
            "clarification prose": fixture.replace(
                "question = <one bounded question>\n```",
                "question = <one bounded question>\n```\n"
                "Arbitrary prose is forbidden here.",
                1,
            ),
            "prose inside normalized block": fixture.replace(
                f"{requested_operation}```",
                f"{requested_operation}Arbitrary prose is forbidden here.\n```",
                1,
            ),
        }

        for name, candidate in mutations.items():
            with self.subTest(mutation=name):
                self.assert_rejected(candidate)

    def test_evidence_status_omissions_extras_and_nonnull_na_are_rejected(self) -> None:
        fixture = build_valid_skill_fixture(self.skill)
        mutations = {
            "missing fail": fixture.replace(
                "status = pass | fail | blocked | not_applicable",
                "status = pass | blocked | not_applicable",
                1,
            ),
            "extra status": fixture.replace(
                "status = pass | fail | blocked | not_applicable",
                "status = pass | fail | blocked | not_applicable | skipped",
                1,
            ),
            "nonnull zero denominator": fixture.replace(
                "not_applicable with a null value",
                "not_applicable with a zero value",
                1,
            ),
        }

        for name, candidate in mutations.items():
            with self.subTest(mutation=name):
                self.assert_rejected(candidate)

    def test_positive_result_requires_the_exact_normalized_machine_envelope(
        self,
    ) -> None:
        fixture = build_valid_skill_fixture(self.skill)
        output_start = fixture.index("## Output Contract\n") + len(
            "## Output Contract\n"
        )
        output_end = fixture.index("\n\n### Activation and Scope", output_start)
        prose_only = (
            "Reviewer prose mentions every expected token: "
            + " ".join(RESULT_FIELDS)
            + ' architectureSchemaVersion: "1.0"; '
            + "stateVersion is independent; policyVersion is independent."
        )
        mutation = fixture[:output_start] + prose_only + fixture[output_end:]

        self.assert_rejected(mutation)

    def test_positive_result_rejects_every_exact_shape_mutation(self) -> None:
        fixture = build_valid_skill_fixture(self.skill)
        selected = f"selectedSkill = {self.skill}\n"
        router = (
            "routerInput = { domain = <domain>, requestedOperation = "
            "<requestedOperation>, artifactState = <artifactState>, evidenceState = "
            "<evidenceState> }\n"
        )
        schema = '  architectureSchemaVersion: "1.0"\n'
        state_version = "  stateVersion: <independent state schema version>\n"
        limitations = f"{POSITIVE_RESULT_LINES[-1]}\n"
        mutations = {
            "wrong fence language": fixture.replace(
                "## Output Contract\n```text\n",
                "## Output Contract\n```yaml\n",
                1,
            ),
            "extra line": fixture.replace(
                f"{limitations}```",
                f"{limitations}  extraField\n```",
                1,
            ),
            "outer reorder": fixture.replace(
                selected + router,
                router + selected,
                1,
            ),
            "outer duplicate": fixture.replace(
                selected,
                selected + selected,
                1,
            ),
            "outer omission": fixture.replace("architectureResult\n", "", 1),
            "router shape": fixture.replace(
                router,
                "routerInput = { domain = <domain>, requestedOperation = "
                "<requestedOperation>, evidenceState = <evidenceState> }\n",
                1,
            ),
            "schema version": fixture.replace(
                schema,
                '  architectureSchemaVersion: "2.0"\n',
                1,
            ),
            "nested reorder": fixture.replace(
                schema + state_version,
                state_version + schema,
                1,
            ),
            "nested duplicate": fixture.replace(
                state_version,
                state_version + state_version,
                1,
            ),
            "nested omission": fixture.replace(limitations, "", 1),
        }

        for name, candidate in mutations.items():
            with self.subTest(mutation=name):
                self.assert_rejected(candidate)

    def test_output_omission_and_misplaced_guardrail_or_reference_are_rejected(self) -> None:
        fixture = build_valid_skill_fixture(self.skill)
        missing_output = fixture.replace(
            "### Context Policy\nRequired structured output for Context Policy.\n\n",
            "",
            1,
        )
        guardrail = (
            "Missing SDK, host, toolchain, binary, hardware, or prerequisite support "
            "is blocked."
        )
        misplaced_guardrail = fixture.replace(guardrail, "", 1).replace(
            "## Routing and Inspection\n",
            f"## Routing and Inspection\n{guardrail}\n",
            1,
        )
        links = "\n".join(
            f"- [{name}](../../references/{name})" for name in REFERENCE_NAMES
        )
        misplaced_references = fixture.replace(links, "", 1).replace(
            "## Guardrails\n", f"## Guardrails\n{links}\n", 1
        )

        mutations = {
            "missing output": missing_output,
            "misplaced guardrail": misplaced_guardrail,
            "misplaced references": misplaced_references,
        }
        for name, candidate in mutations.items():
            with self.subTest(mutation=name):
                self.assert_rejected(candidate)

    def test_copy_without_remove_duplicates_violate_exclusive_section_ownership(
        self,
    ) -> None:
        fixture = build_valid_skill_fixture(self.skill)
        missing_guardrail = (
            "Missing SDK, host, toolchain, binary, hardware, or prerequisite support "
            "is blocked."
        )
        clarification_block = (
            "### clarification_required\n"
            "```text\nactivationStatus = clarification_required\n"
            "clarificationKind = domain | approved_contract\n"
            "missingInput = domain | approved_contract\n"
            "question = <one bounded question>\n```\n"
        )
        reference_link = (
            f"[{REFERENCE_NAMES[0]}](../../references/{REFERENCE_NAMES[0]})"
        )
        router_domain = f"domain = {' | '.join(ROUTER_ENUMS['domain'])}"
        mutations = {
            "architecture result in routing": fixture.replace(
                "## Routing and Inspection\n",
                "## Routing and Inspection\narchitectureResult = <duplicate>\n",
                1,
            ),
            "common output heading under references": fixture.replace(
                "## References\n",
                "## References\n### Context Policy\nDuplicate output content.\n",
                1,
            ),
            "guardrail in routing": fixture.replace(
                "## Routing and Inspection\n",
                f"## Routing and Inspection\n{missing_guardrail}\n",
                1,
            ),
            "evidence-label guardrail in routing": fixture.replace(
                "## Routing and Inspection\n",
                "## Routing and Inspection\ncompiled_sdk_26_5 and "
                "interface_verified_sdk_26_5\n",
                1,
            ),
            "clarification block under guardrails": fixture.replace(
                "## Guardrails\n",
                f"## Guardrails\n{clarification_block}",
                1,
            ),
            "reference link in routing": fixture.replace(
                "## Routing and Inspection\n",
                f"## Routing and Inspection\n{reference_link}\n",
                1,
            ),
            "protocol step under guardrails": fixture.replace(
                "## Guardrails\n",
                f"## Guardrails\n1. {PROTOCOL_STEPS[0]}\n",
                1,
            ),
            "output field in routing": fixture.replace(
                "## Routing and Inspection\n",
                "## Routing and Inspection\nscope = <duplicate>\n",
                1,
            ),
            "router input under guardrails": fixture.replace(
                "## Guardrails\n",
                f"## Guardrails\n{router_domain}\n",
                1,
            ),
        }

        for name, candidate in mutations.items():
            with self.subTest(mutation=name):
                self.assert_rejected(candidate)

    def test_core_semantic_headings_reject_wrong_level_copies(self) -> None:
        fixture = build_valid_skill_fixture(self.skill)
        mutations = {
            f"level {level} {title}": fixture.replace(
                "## References\n",
                f"## References\n{'#' * level} {title}\nCopied contract content.\n",
                1,
            )
            for level in (3, 4)
            for title in CORE_SEMANTIC_SECTION_TITLES
        }

        for name, candidate in mutations.items():
            with self.subTest(mutation=name):
                self.assert_rejected(candidate)


if __name__ == "__main__":
    unittest.main()
