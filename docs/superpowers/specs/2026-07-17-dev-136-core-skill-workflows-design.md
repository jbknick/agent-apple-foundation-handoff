# DEV-136 Core Skill Workflows Design

**Issue:** DEV-136 — Implement the core handoff workflow skills

**Status:** Approved implementation design

**Base:** `bdbfd335e32eba3efee32f2aac08bd3c2a100368` (DEV-135)

**Host boundary:** Codex `0.144.5` with model `sol`; Claude execution is owner-deferred

## Purpose

DEV-136 turns the metadata-only plugin scaffold into five real, narrowly activated
Apple Foundation Models handoff workflows. The implementation preserves DEV-135's
canonical/generated boundary, inherits DEV-134's catalog and router contract, consumes
DEV-137's coordinated reference paths, and produces behavioral evidence rather than
treating file discovery or Markdown shape as proof.

This design does not change the approved Linear decision. It makes that decision
executable and resolves only implementation details that do not alter product scope.

## Inputs and inherited decisions

- DEV-128: ground Apple API claims in current official Apple sources or installed SDK
  interfaces. Label unsupported APIs and pseudocode.
- DEV-130: make state ownership, trust boundaries, context minimization, effect
  authority, failure handling, recovery, and version compatibility explicit.
- DEV-131: use layered evidence with `pass`, `fail`, `blocked`, or `not_applicable`;
  missing host support is never a pass.
- DEV-132: preserve the canonical Claude/shared to generated Codex artifact model and
  do not conflate the six adjacent meanings of handoff or skills.
- DEV-134: use the exact five-skill catalog, deterministic router, common result
  envelope, workflow sections, and activation prototype.
- DEV-135: five canonical inputs generate exactly three Codex artifacts. Never edit
  generated files directly.
- DEV-136 approved decision: add exactly five skill directories, each containing one
  `SKILL.md`; add no commands, hooks, MCP servers, agents, dependencies, runtime
  packages, or per-skill `agents/openai.yaml`.

## Production surface

Create exactly these authored workflow files:

```text
plugins/apple-foundation-models-handoff/skills/
├── design-apple-foundation-models-handoff/SKILL.md
├── implement-apple-foundation-models-handoff/SKILL.md
├── review-apple-foundation-models-handoff/SKILL.md
├── debug-apple-foundation-models-handoff/SKILL.md
└── validate-apple-foundation-models-handoff/SKILL.md
```

Each skill has YAML frontmatter with only `name` and `description`, followed by a
concise executable workflow. The canonical shared manifest explicitly exposes the
single component root with `"skills": "./skills/"`; discovery under that approved
root must yield exactly the five directories above and no others.

Update existing authored metadata and guidance only where the current metadata-only
language becomes false:

- `plugins/apple-foundation-models-handoff/.claude-plugin/plugin.json`
- `plugins/apple-foundation-models-handoff/metadata/codex-interface.json`
- `.claude-plugin/marketplace.json`, only if its description is stale
- `CLAUDE.md`

The generator remains the only writer of:

- `plugins/apple-foundation-models-handoff/.codex-plugin/plugin.json`
- `.agents/plugins/marketplace.json`
- `AGENTS.md`

## Skill activation contract

The frontmatter description is the primary activation boundary. Use the exact
DEV-134 wording:

| Skill | Activation description |
| --- | --- |
| `design-apple-foundation-models-handoff` | Design an Apple Foundation Models handoff architecture, topology, pattern, state model, or trust boundary when the user is creating or materially revising how sessions, profiles, or providers transfer control or provide isolated consultation. |
| `implement-apple-foundation-models-handoff` | Implement an Apple Foundation Models handoff architecture when an approved architecture or decision reference and an exact application change boundary already exist. |
| `review-apple-foundation-models-handoff` | Review an existing Apple Foundation Models handoff artifact when the user wants severity-ranked findings about architecture, Apple API grounding, state, security, recovery, or evidence claims rather than changes. |
| `debug-apple-foundation-models-handoff` | Debug an Apple Foundation Models handoff when an observed routing, ownership, transition, context, tool, effect, recovery, fallback, availability, or version-labelled behavior differs from its expected contract and the cause is not yet established. |
| `validate-apple-foundation-models-handoff` | Validate an Apple Foundation Models handoff artifact when the user requests reproducible proof, a complete pass/fail/blocked/not_applicable matrix, cross-host comparison, or release implication rather than design, edits, findings-only review, or diagnosis. |

The router evaluates four inputs:

1. `domain`: `foundation_models_handoff`, `out_of_domain`, or `ambiguous`.
2. `requestedOperation`: `design`, `implement`, `review`, `debug`, `validate`,
   `compound_review_fix`, or `unspecified`.
3. `artifactState`: `absent`, `proposal`, `approved_contract`, `implementation`,
   `evidence_bundle`, or `unknown`.
4. `evidenceState`: `not_requested`, `missing`, `available`, `failing`, `blocked`,
   or `unknown`.

Routing rules:

- Choose exactly one primary workflow when the inputs are sufficient.
- For “review and fix,” run review first. Only then may requested corrections proceed,
  and the findings remain independently visible.
- Ask exactly one targeted clarification when the domain or required authority is
  missing. Implementation authority means an approved decision reference and exact
  change boundary.
- Refuse or redirect Apple Handoff/`NSUserActivity`, App Intents, Swift actors,
  generic Core ML, coding-session handoff, Agent Skills generally, and Foundation
  Models runtime Skills.
- No workflow invokes another skill.

## Common workflow protocol

Every positive workflow:

1. Inspects the repository, relevant artifacts, and installed SDK interfaces before
   asserting implementation facts.
2. Resolves the router inputs and states the selected workflow.
3. Establishes current owner, next owner, trust boundary, and effect authority.
4. Separates control-plane state from model context and minimizes transferred data.
5. Distinguishes consultation from ownership transfer.
6. Uses version-labelled state, deterministic transitions, bounded retries,
   idempotency/reconciliation, and explicit recovery/fallback.
7. Grounds Apple claims through installed interfaces and DEV-137 references.
8. Compile-checks Swift examples where supported; otherwise labels pseudocode or an
   exact `blocked` prerequisite.
9. Emits the common result envelope plus workflow-specific sections.
10. Separates fact, inference, pseudocode, unsupported API, limitation, blocker, and
    `not_applicable` evidence.

Every positive result contains independent labels:

```yaml
architectureSchemaVersion: "1.0"
stateVersion: <independent state schema version>
policyVersion: <independent policy version>
```

It also contains DEV-134's ten common sections:

1. Activation and Scope
2. Pattern and Ownership
3. Apple API Availability
4. State and Lifecycle
5. Trust and Model Boundaries
6. Context Policy
7. Tools Effects and Confirmation
8. Failure Recovery and Fallback
9. Verification and Evidence
10. Limitations

Workflow-specific sections are:

| Workflow | Required sections |
| --- | --- |
| Design | Alternatives; Decision Rationale; Proposed Components; Implementation and Test Plan |
| Implement | Approved Decision; Change Boundary; Changed Paths; Compilation and Regression Results |
| Review | Findings, severity-ranked and evidence-linked |
| Debug | Observed and Expected State; First Divergence; Root Cause; Correction; Regression Proof |
| Validate | Layer Matrix; Counts and Hashes; Rubric Result; Blockers and Skips; Release Implication |

## Reference-library contract

Skills link directly from their directory to fixed DEV-137 paths:

- `../../references/architecture-and-state.md`
- `../../references/orchestration-patterns.md`
- `../../references/apple-api-availability.md`
- `../../references/security-context-and-recovery.md`
- `../../references/evaluation-and-observability.md`

Each link names the concern it supports. Skill prose carries stable workflow rules,
not volatile Apple signatures copied from references. Review and validation use all
five because their remit spans the entire contract; other skills link only the
concerns they use.

DEV-136 and DEV-137 may be developed in parallel from DEV-135. Missing reference
targets on the DEV-136-only branch are an explicit integration blocker, not permission
to create placeholders or weaken links. Rebase DEV-136 above final DEV-137 before
reference-resolution and host proof.

## Canonical metadata and generated artifacts

Once the skills exist:

- the canonical shared manifest contains exactly `"skills": "./skills/"`, and that
  component root resolves exactly the five approved skill names;
- descriptions advertise the five real workflows;
- Codex `capabilities` is exactly this ordered list:
  `design-apple-foundation-models-handoff`,
  `implement-apple-foundation-models-handoff`,
  `review-apple-foundation-models-handoff`,
  `debug-apple-foundation-models-handoff`, and
  `validate-apple-foundation-models-handoff`;
- Codex starter prompts exercise real workflows instead of metadata inspection;
- repository guidance no longer says workflows are unimplemented.

The shared-manifest validator changes from forbidding `skills` to requiring exactly
`"skills": "./skills/"`. The Codex interface schema and generator validator change
from `capabilities == []` to the exact ordered five-name invariant. The generated
Codex manifest inherits both. Tests fail for a directly edited generated file, a
missing/reordered/sixth capability, a changed skills component path, or a capability
without its authored skill.

## Skill TDD and forward tests

Apply RED/GREEN/REFACTOR separately to all five skills.

### RED: baseline without each skill

Run five fresh Codex `sol` sessions with the plugin unavailable and one representative
positive prompt per workflow. Score responses against DEV-134. Record an actual miss,
such as wrong routing, absent version labels, incomplete ownership/trust data,
unlabelled API claims, or a missing result section. If a baseline unexpectedly passes,
strengthen the discriminating prompt/rubric instead of inventing a failure.

### GREEN: minimal skill

Add the smallest workflow text that corrects the observed failure and satisfies the
normative contract. Repository tests first prove file shape, frontmatter, activation,
router, outputs, links, and canonical/generated metadata. Those checks are necessary,
not sufficient.

### REFACTOR: fresh forward tests

Run four fresh Codex `sol` cases for every skill, 20 total:

- positive activation and correct workflow selection;
- negative non-activation for an adjacent domain;
- ambiguous input producing exactly one targeted clarification;
- complete positive output containing every common and workflow-specific field.

Review-and-fix is the review case and must remain review-first. Each case begins with
no conversation history. The prompt does not reveal expected answers; deterministic
rubric code evaluates afterward.

Committed evidence records prompt ID, skill, category, model, Codex version, commit,
response hash, normalized rubric checks, verdict, and blocker details. Raw live host
responses remain transient. Offline scorer fixtures contain only approved synthetic or
redacted outputs. Never commit credentials, local tokens, raw live responses, or
unrelated user configuration.

## Codex-only host boundary

This wave actively tests Codex `0.144.5` with `-m sol`. Claude CLI execution and
cross-host comparison are `blocked/owner-deferred`; no Claude binary is invoked and no
inference is presented as Claude evidence.

Host tests use a controlled plugin context and a fresh session per case. Skills make
no provider/network calls. Model execution may use the host's existing authenticated
Codex context without copying credentials. If the binary, selected model,
authentication, or plugin activation is unavailable, host validation exits blocked;
offline tests do not upgrade that blocker to a pass.

## Validation matrix

| Layer | Proof | Required result |
| --- | --- | --- |
| Repository | Exact files, frontmatter, links, no extra capability surfaces | Pass |
| Schema | Canonical manifests and Codex interface validate | Pass |
| Generation | Check, sync, check; exactly three outputs; drift detection | Pass |
| Fixture | Five baselines and 20 forward cases have exact coverage | Pass |
| Skill contract | Router, versions, outputs, safety, and evidence rules | Pass |
| Swift examples | Compile/type-check where supported | Pass or explicit blocked/not_applicable |
| Codex host | Fresh `sol` sessions and deterministic rubric | Pass |
| References | All fixed DEV-137 links resolve after rebase | Pass |
| Claude host | No invocation in this wave | Blocked/owner-deferred |
| Full repository | Python, BATS, generation, schema, fixture, and host checks | Pass |

Discovery, Markdown lint, and generated manifest presence never prove capability by
themselves.

## Atomic integration and review

1. Develop from `bdbfd335...` while DEV-137 proceeds independently.
2. Commit only DEV-136 tests/evidence, skills, metadata/generator changes, and truthful
   guidance in small reviewable commits.
3. Rebase above final DEV-137 with
   `git rebase --onto <DEV137_HEAD> bdbfd335 codex/dev-136-core-skill-workflows`.
4. Target a stacked DEV-136 PR at DEV-137 until DEV-137 merges; then rebase/retarget
   without folding DEV-137 into DEV-136's issue diff.
5. Do not publish, tag, release, push, or merge outside separately authorized steps.

## Completion gate

DEV-136 completes only when all five skills exist, metadata is truthful, generated
artifacts are synchronized, deterministic checks pass, DEV-137 links resolve, all 25
fresh Codex `sol` sessions have durable rubric evidence, no forbidden capability
surface exists, and host limitations are explicit blockers rather than false passes.
Attach commands, results, evidence, and final commits in Linear before completion.
