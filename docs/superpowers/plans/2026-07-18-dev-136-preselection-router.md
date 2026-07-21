# DEV-136 Non-Positive Pre-Selection Router Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:subagent-driven-development` to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking. Apply
> `superpowers:test-driven-development` to every behavior or validation change,
> `superpowers:writing-skills` and `skill-creator` to the new skill and the five
> edited skills, and `superpowers:verification-before-completion` before every
> completion claim.

**Goal:** Add one production-capable, cross-host pre-selection router that emits
the already approved exact `no_activation` and `clarification_required`
envelopes, while preserving the five positive Apple Foundation Models handoff
workflows and proving the result in Codex with `gpt-5.6-sol`.

**Architecture:** Keep the existing five workflow skills as the only positive
workflow owners. Append one instruction-only
`route-apple-foundation-models-handoff` skill that owns only rejection and the
two currently approved clarification branches. Canonical Claude metadata and
Codex interface metadata remain authored inputs; the generator remains the only
writer of `AGENTS.md` and Codex manifests. Add contractual fixture ownership,
bind all six payloads, and prove the differential with truthful pre-router
mixed evidence, a 15-case affected Codex gate, and the complete 25-case Codex
matrix.

**Tech Stack:** Python 3 standard-library `unittest`, JSON/JSON Schema, Bats
`1.13.0`, shell-based repository gates, Codex CLI `0.144.5`, Agent Skills
Markdown, and the repository's Python artifact generator.

**Base at plan creation:** `00c50560c7496e9626d9c19cf1e589ecbc8f46ee`

**Branch:** `codex/dev-136-core-skill-workflows`

**Design:**
`docs/superpowers/specs/2026-07-18-dev-136-preselection-router-design.md`

---

## Global constraints

- The user approved option 2 in DEV-136. The durable approval is Linear comment
  `7edff944-75b6-4f4e-90d8-8d41d5854daa`; the propagated comments in DEV-132,
  DEV-134, DEV-135, and DEV-137 through DEV-141 are binding.
- The Task 2 evidence amendment is approved in DEV-136 Linear comment
  `799a3023-8d37-4962-ad33-b1b2a042a3ab`. Preserve the exact three canonical
  rows as two differential RED failures plus one already-green domain
  non-regression pass. Do not rerun to seek a different verdict or substitute
  an unapproved row.
- The exact ordered capability list is the existing five workflows followed by
  `route-apple-foundation-models-handoff`. The router is not a sixth workflow.
- Preserve every existing workflow frontmatter description byte-for-byte. Use
  the router name and description from the approved design verbatim.
- The router owns only out-of-domain rejection, ambiguous-domain
  clarification, and implementation clarification for a missing approved
  contract or exact change boundary. Domain ambiguity takes precedence.
- The router emits exactly one `text` fence and the exact four ordered fields
  for the selected non-positive shape. It emits no prose, heading,
  `selectedSkill`, `routerInput`, `architectureResult`, workflow section,
  version, reference, Apple claim, tool/effect result, or inter-skill handoff.
- Positive prompts select one of the five workflows directly. The five
  workflow bodies become positive-only and retain all positive serialization,
  Apple-source, safety, reference, and evidence responsibilities.
- Keep the 25 fixture IDs, prompts, prompt hashes, router values, activation
  outcomes, clarification kinds, and rubrics unchanged. Add only
  `expectedSkillOwner`; keep `skillUnderTest` as the five-workflow coverage
  family.
- Codex exposes no selected-skill lifecycle telemetry. Treat
  `expectedSkillOwner` as a contractual owner, never as observed host telemetry.
- Add no plugin command, agent, hook, MCP server, app, new script, dependency,
  runtime package, network requirement, credential requirement, or
  `agents/openai.yaml`. The existing test runner may gain bounded case
  selection, but that is test infrastructure and not plugin surface.
- Keep version `0.1.0`. Do not use a semantic-version cachebuster. Do not change
  the repo-scoped Codex marketplace source, policy, authentication, or category.
- Use official Apple sources and installed SDK interfaces for Apple claims.
  This amendment adds no Apple API claim or Swift sample. Existing inherited
  Swift/SDK gates still run; router-specific compilation is `not_applicable`.
- Test only Codex in this wave. Record Claude as `owner_deferred`; do not invoke
  Claude or infer Claude acceptance.
- Use exact Codex CLI `0.144.5` and exact model `gpt-5.6-sol`. A missing binary,
  auth, model, plugin load, host automation, or cleanup prerequisite is an
  explicit blocker, never a pass.
- Use `apply_patch` for authored repository edits. Run
  `scripts/sync_generated_artifacts.py --write` for generated artifacts; never
  edit `AGENTS.md`, `.agents/plugins/marketplace.json`, or the plugin-local
  `.codex-plugin/plugin.json` directly.
- Keep commits atomic. Tests-only RED commits must remain tests-only. Generated
  files travel with the canonical change that produces them. Do not push until
  all task reviews and final verification are green.
- Execute implementation tasks serially with a fresh implementer and a fresh
  reviewer. Parallel subagents are allowed only for independent read-only
  review. Record reviewed task ranges in `.superpowers/sdd/progress.md`.

## Exact contracts

### Capabilities

```text
design-apple-foundation-models-handoff
implement-apple-foundation-models-handoff
review-apple-foundation-models-handoff
debug-apple-foundation-models-handoff
validate-apple-foundation-models-handoff
route-apple-foundation-models-handoff
```

Use these separate constants wherever topology is enforced:

```python
WORKFLOW_SKILLS = (
    "design-apple-foundation-models-handoff",
    "implement-apple-foundation-models-handoff",
    "review-apple-foundation-models-handoff",
    "debug-apple-foundation-models-handoff",
    "validate-apple-foundation-models-handoff",
)
ROUTER_SKILL = "route-apple-foundation-models-handoff"
ALL_CAPABILITIES = (*WORKFLOW_SKILLS, ROUTER_SKILL)
```

`WORKFLOW_SECTIONS` remains keyed only by `WORKFLOW_SKILLS`.

### Non-positive envelopes

```text
activationStatus = no_activation
reasonCode = out_of_domain
domain = out_of_domain
requestedOperation = unspecified
```

```text
activationStatus = clarification_required
clarificationKind = domain
missingInput = domain
question = <one concise question ending in exactly one question mark>
```

```text
activationStatus = clarification_required
clarificationKind = approved_contract
missingInput = approved_contract
question = <one concise question ending in exactly one question mark>
```

### Affected host cases

Affected rows in canonical fixture order (`-001` is positive anti-steal;
`-002` and `-003` are router-owned):

```text
DEV136-FWD-DESIGN-001
DEV136-FWD-DESIGN-002
DEV136-FWD-DESIGN-003
DEV136-FWD-IMPLEMENT-001
DEV136-FWD-IMPLEMENT-002
DEV136-FWD-IMPLEMENT-003
DEV136-FWD-REVIEW-001
DEV136-FWD-REVIEW-002
DEV136-FWD-REVIEW-003
DEV136-FWD-DEBUG-001
DEV136-FWD-DEBUG-002
DEV136-FWD-DEBUG-003
DEV136-FWD-VALIDATE-001
DEV136-FWD-VALIDATE-002
DEV136-FWD-VALIDATE-003
```

### Task 1: Propagate the approved repository contract

**Files:**

- Modify:
  `docs/superpowers/specs/2026-07-17-dev-132-mvp-architecture-design.md`
- Modify:
  `docs/architecture/apple-foundation-models-handoff-mvp-decision-record.md`
- Modify:
  `docs/superpowers/specs/2026-07-17-dev-134-agent-skill-catalog-design.md`
- Modify:
  `docs/architecture/apple-foundation-models-handoff-skill-contract.md`
- Modify: `docs/research/evidence/dev-134-activation-prototype.json`
- Modify:
  `docs/superpowers/specs/2026-07-17-dev-135-minimal-plugin-skeleton-design.md`
- Modify:
  `docs/superpowers/plans/2026-07-17-dev-135-minimal-plugin-skeleton.md`
- Modify:
  `docs/superpowers/specs/2026-07-17-dev-136-core-skill-workflows-design.md`
- Modify:
  `docs/superpowers/plans/2026-07-17-dev-136-core-skill-workflows.md`

**Interfaces:**

- Consumes: the approved router design and durable DEV-136 option-2 decision.
- Produces: repository contracts that define `WORKFLOW_SKILLS`, `ROUTER_SKILL`,
  `ALL_CAPABILITIES`, and the non-positive ownership boundary used by Tasks 2-6.

- [ ] **Step 1: Correct exact-five and conceptual-router assumptions**

Add bounded supersession notes rather than erasing historical decisions. Every
note must name DEV-136, the approved option-2 decision, the five-workflow-plus-
one-router topology, positive-only workflow ownership, router-owned
non-positive branches, unchanged fixture prompts/outcomes, Codex-only current
proof, and the design amendment path.

Update the DEV-134 prototype document only to distinguish conceptual routing
from the new production owner. Do not relabel old prototype observations as
host capability evidence and do not change its historical hashes or outcomes.

- [ ] **Step 2: Validate the corrected documents**

```bash
python3 -m json.tool docs/research/evidence/dev-134-activation-prototype.json >/dev/null
rg -n "five workflows plus one non-positive router|route-apple-foundation-models-handoff|DEV-136" \
  docs/superpowers/specs/2026-07-17-dev-132-mvp-architecture-design.md \
  docs/architecture/apple-foundation-models-handoff-mvp-decision-record.md \
  docs/superpowers/specs/2026-07-17-dev-134-agent-skill-catalog-design.md \
  docs/architecture/apple-foundation-models-handoff-skill-contract.md \
  docs/superpowers/specs/2026-07-17-dev-135-minimal-plugin-skeleton-design.md \
  docs/superpowers/plans/2026-07-17-dev-135-minimal-plugin-skeleton.md \
  docs/superpowers/specs/2026-07-17-dev-136-core-skill-workflows-design.md \
  docs/superpowers/plans/2026-07-17-dev-136-core-skill-workflows.md
git diff --check
```

- [ ] **Step 3: Commit the propagated contracts**

```bash
git add docs/architecture \
  docs/superpowers/specs/2026-07-17-dev-132-mvp-architecture-design.md \
  docs/superpowers/specs/2026-07-17-dev-134-agent-skill-catalog-design.md \
  docs/superpowers/specs/2026-07-17-dev-135-minimal-plugin-skeleton-design.md \
  docs/superpowers/specs/2026-07-17-dev-136-core-skill-workflows-design.md \
  docs/superpowers/plans/2026-07-17-dev-135-minimal-plugin-skeleton.md \
  docs/superpowers/plans/2026-07-17-dev-136-core-skill-workflows.md \
  docs/research/evidence/dev-134-activation-prototype.json
git diff --cached --check
git commit -m "docs(DEV-136): propagate router ownership contract"
```

Commit boundary: decision corrections and supersession notes only. No tests,
skill payload, metadata, fixture, runner, or generated output.

### Task 2: Capture representative pre-router mixed behavior

**Files:**

- Modify: `tests/test_skill_cases.py`
- Create:
  `docs/research/evidence/dev-136-non-positive-router-red-baseline.json`

**Interfaces:**

- Consumes: the unchanged canonical 25-case fixture and current five-skill
  payload at the Task 1 reviewed head.
- Produces: `NonPositiveRouterRedBaselineTests` plus one closed-schema,
  normalized three-branch pre-router mixed evidence document. The historical
  class and file identifiers remain stable because the tests-only RED
  checkpoint was already committed before the live result was known.

- [ ] **Step 1: Add the RED evidence contract**

Add a closed-schema test class that requires exactly these representative rows:

- `DEV136-FWD-DESIGN-002` for `no_activation`;
- `DEV136-FWD-DESIGN-003` for `clarificationKind = domain`;
- `DEV136-FWD-IMPLEMENT-003` for
  `clarificationKind = approved_contract`.

Require exact model/version, capture commit, prompt and rubric hashes, response
hash/byte count, tool-event count, verdict, failed checks, failure classes,
five-workflow payload digests, `productionRouterAvailable = false`, normalized
privacy metadata, and `claudeInvoked = false`. Require exact verdict order
`fail`, `pass`, `fail`; the passing domain row has empty failed checks and
failure classes, while both failing rows retain their exact failures. Require
top-level `status = "mixed"` and
`evidenceKind = "non_positive_router_pre_router_mixed_baseline"`. Forbid raw
prompt, response, reasoning, event, command, credential, and local-path fields.

Add these exact test constants and derive row checks from them:

```python
ROUTER_RED_CASE_IDS = (
    "DEV136-FWD-DESIGN-002",
    "DEV136-FWD-DESIGN-003",
    "DEV136-FWD-IMPLEMENT-003",
)
ROUTER_RED_BRANCHES = (
    ("no_activation", None),
    ("clarification_required", "domain"),
    ("clarification_required", "approved_contract"),
)
ROUTER_RED_EXPECTED_VERDICTS = (
    "fail",
    "pass",
    "fail",
)
ROUTER_RED_EVIDENCE_PATH = (
    ROOT / "docs/research/evidence/dev-136-non-positive-router-red-baseline.json"
)
```

- [ ] **Step 2: Run the evidence-contract test and observe RED**

Run RED and prove only the new evidence contract fails:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_skill_cases.NonPositiveRouterRedBaselineTests -v
```

Expected: FAIL because the evidence file does not exist.

- [ ] **Step 3: Commit the tests-only RED contract**

Commit the test-only RED:

```bash
git add tests/test_skill_cases.py
git diff --cached --check
git commit -m "test(DEV-136): require router RED baselines"
```

This historical checkpoint is commit `d3f1ad5`. After the approved live
capture returned a mixed result, add the exact verdict-order and mixed-status
assertions in a new tests-only correction commit. Rerun the same focused test;
it remains RED only because the normalized evidence file is absent.

```bash
git add tests/test_skill_cases.py
git diff --cached --check
git commit -m "test(DEV-136): accept truthful mixed router baseline"
```

- [ ] **Step 4: Run the three current-payload Codex probes**

Use the existing runner with an approved-order temporary subset derived from
the canonical fixture. The temporary subset and raw evidence remain under
`/tmp`, outside the repository, and are deleted after normalization. Generate
the test-only subset mechanically with `jq`; it is not an authored repository
edit. Run exact Codex `0.144.5` and `gpt-5.6-sol`; do not inject skill text and
do not invoke Claude.

The initial approved run is complete: `DEV136-FWD-DESIGN-002` and
`DEV136-FWD-IMPLEMENT-003` failed, while `DEV136-FWD-DESIGN-003` passed. The
approved fallback `DEV136-FWD-REVIEW-003` also passed and remains in the
execution record rather than replacing a canonical row. Controller resolution
approved the mixed evidence contract. Never alter a prompt, rubric, scorer, or
verdict to manufacture RED, and do not rerun merely to seek a different result.

```bash
codex --version
jq '(.cases |= map(select(.id == "DEV136-FWD-DESIGN-002" or .id == "DEV136-FWD-DESIGN-003" or .id == "DEV136-FWD-IMPLEMENT-003"))) | .caseCount = (.cases | length)' \
  tests/fixtures/dev-136-codex-skill-cases.json \
  > /tmp/dev-136-router-red-cases.json
CODEX_BIN="$(command -v codex)" python3 \
  tests/e2e/codex_skill_forward_tests.py \
  --mode host \
  --model gpt-5.6-sol \
  --codex-version 0.144.5 \
  --cases /tmp/dev-136-router-red-cases.json \
  --evidence /tmp/dev-136-router-red-run.json
```

The original runner exited nonzero because two representative rows failed; its
normalized mixed evidence must still be complete, closed-schema, and clean.

Normalize only approved hashes, counts, failure classes, capture SHA, and
privacy/host metadata into the repository evidence file using `apply_patch`.
Delete the temporary subset and raw runner evidence. Prove source and worktree
cleanliness after cleanup.

```bash
rm -f /tmp/dev-136-router-red-cases.json /tmp/dev-136-router-red-run.json
git status --short
```

- [ ] **Step 5: Validate the normalized mixed evidence**

```bash
python3 -m json.tool \
  docs/research/evidence/dev-136-non-positive-router-red-baseline.json >/dev/null
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_skill_cases.NonPositiveRouterRedBaselineTests -v
git diff --check
git status --short
```

- [ ] **Step 6: Commit normalized mixed evidence**

```bash
git add docs/research/evidence/dev-136-non-positive-router-red-baseline.json
git diff --cached --check
git commit -m "test(DEV-136): capture mixed router baselines"
```

Commit boundary: normalized pre-router evidence only. Both the historical RED
contract and its approved mixed-result correction remain in earlier tests-only
commits.

### Task 3: Transfer non-positive ownership to the router skill

**Files:**

- Modify: `tests/test_skill_contract.py`
- Create:
  `plugins/apple-foundation-models-handoff/skills/route-apple-foundation-models-handoff/SKILL.md`
- Modify: each of the five existing
  `plugins/apple-foundation-models-handoff/skills/*/SKILL.md` workflow files

**Interfaces:**

- Consumes: exact router description, exact non-positive envelopes, and the
  five existing positive skill contracts.
- Produces: `WORKFLOW_SKILLS: tuple[str, ...]`, `ROUTER_SKILL: str`,
  `ALL_CAPABILITIES: tuple[str, ...]`, one router payload, and five
  positive-only workflow payloads.

- [ ] **Step 1: Add tests-only RED skill contracts**

Split topology from workflow semantics:

- `WORKFLOW_SKILLS` is the exact existing five;
- `ROUTER_SKILL` is the exact router;
- `ALL_CAPABILITIES` is the ordered six;
- each directory contains exactly one regular authored `SKILL.md`;
- no skill contains `agents/openai.yaml`, nested references, scripts, assets,
  or other files.

Require the router's exact frontmatter and exact non-positive branches. Require
the exact one-fence shapes, field order, question cardinality, domain
precedence, and all router prohibitions from the approved design. Require zero
reference links and zero Apple API/source assertions in the router.

Use this exact router metadata in the test and production file:

```yaml
---
name: route-apple-foundation-models-handoff
description: Route a non-positive Apple Foundation Models handoff request before workflow selection: reject App Intents or Shortcuts, Apple Handoff or NSUserActivity, generic Swift or actors, generic Core ML, coding-session handoff, Agent Skills, and Foundation Models runtime Skills; ask one clarification for ambiguous Apple handoff wording or implementation without an approved architecture and exact change boundary. Return only no_activation or clarification_required; never use for a confirmed request that can select design, implement, review, debug, or validate.
---
```

For each workflow, retain the existing frontmatter and all positive contracts,
but reject duplicated non-positive templates, clarification ownership, and
non-trigger serialization. Keep positive result parsing and workflow section
oracles unchanged.

Update mutation tests to reject a seventh or unapproved skill, a second
non-positive owner, a router positive envelope, router references, extra prose,
wrong field order, wrong question count, and missing positive workflow content.

- [ ] **Step 2: Run the skill-contract tests and observe RED**

Run RED:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_skill_contract.SkillContractTests \
  tests.test_skill_contract.SkillContractMutationTests -v
```

Expected: FAIL because only five skills exist and those five still own the
non-positive templates.

- [ ] **Step 3: Commit the tests-only RED contract**

Commit the tests-only RED:

```bash
git add tests/test_skill_contract.py
git diff --cached --check
git commit -m "test(DEV-136): specify non-positive router contract"
```

- [ ] **Step 4: Initialize a disposable scaffold, then author the router**

After RED is observed, use the skill-creator initializer in a temporary
directory to validate the standard skeleton without adding its optional UI
metadata to the plugin package:

```bash
python3 /Users/josephknickerbocker/.codex/skills/.system/skill-creator/scripts/init_skill.py \
  route-apple-foundation-models-handoff \
  --path /tmp/dev-136-router-scaffold \
  --interface display_name="Route Apple Foundation Models Handoff" \
  --interface short_description="Route non-positive handoff requests" \
  --interface default_prompt="Route this non-positive Apple Foundation Models handoff request."
```

Inspect the scaffold, then delete the temporary directory. Author only the
approved `SKILL.md` path in the repository with `apply_patch`; the user-approved
frontmatter description overrides generic authoring-style preferences and must
remain verbatim. The body is a concise low-freedom decision procedure whose
positive recipe is the exact output shape.

After inspecting the generated scaffold, remove it:

```bash
rm -rf /tmp/dev-136-router-scaffold
```

Edit all five workflow bodies to remove non-positive serialization and
pre-selection ambiguity ownership while preserving every positive output,
source, reference, safety, and evidence contract.

- [ ] **Step 5: Validate GREEN**

```bash
python3 /Users/josephknickerbocker/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  plugins/apple-foundation-models-handoff/skills/route-apple-foundation-models-handoff
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_skill_contract.SkillContractTests \
  tests.test_skill_contract.SkillContractMutationTests -v
rg -n "no_activation|clarification_required|clarificationKind|missingInput" \
  plugins/apple-foundation-models-handoff/skills
git diff --check
```

The `rg` result must point only to the router. Confirm the original five
frontmatter descriptions are byte-for-byte unchanged.

- [ ] **Step 6: Commit production skill ownership**

```bash
git add plugins/apple-foundation-models-handoff/skills
git diff --cached --check
git commit -m "feat(DEV-136): add non-positive router ownership"
```

Commit boundary: the new router plus the five positive-only workflow payloads.
No metadata, fixture, runner, generated output, or evidence.

#### Task 3, phase B: Advertise and generate the six-capability package

**Files:**

- Modify: `tests/test_plugin_contract.py`
- Modify: `tests/test_generated_artifacts.py`
- Modify: `tests/test_repository_guidance.py`
- Modify: `tests/e2e/codex_plugin_load.py`
- Modify if exact topology is asserted: `tests/plugin_skeleton.bats`
- Modify:
  `plugins/apple-foundation-models-handoff/metadata/codex-interface.json`
- Modify only if prose is stale:
  `plugins/apple-foundation-models-handoff/.claude-plugin/plugin.json`
- Modify: `schemas/codex-interface-input.schema.json`
- Modify: `scripts/sync_generated_artifacts.py`
- Modify: `CLAUDE.md`
- Generate: `AGENTS.md`
- Generate:
  `plugins/apple-foundation-models-handoff/.codex-plugin/plugin.json`
- Generate only if canonical bytes require it:
  `.agents/plugins/marketplace.json`

**Phase B interfaces:**

- Consumes: the reviewed six skill directories from Task 3.
- Produces: a six-entry `interface.capabilities` array, six-skill component
  validation, exact generated `AGENTS.md`/Codex manifest bytes, and a structural
  load probe bound to those bytes.

- [ ] **Step 7: Add tests-only RED package contracts**

Require:

- exact ordered `ALL_CAPABILITIES` in Codex interface and generated manifest;
- exactly five workflow payloads plus the router payload under `./skills/`;
- an unapproved seventh capability/skill is rejected;
- missing, duplicate, reordered, or substituted router identity is rejected;
- schema exact-list `const` and custom validation agree;
- the package closure allows the sixth skill and no extra files/surfaces;
- canonical and generated guidance say “five workflows plus one non-positive
  router” and do not call the router a workflow;
- the installed-package probe binds the exact sixth directory and file;
- marketplace source/policy/auth/category and version remain unchanged.

Use the exact list from `ALL_CAPABILITIES` as the JSON Schema `const` and
custom-validator order, preserving the repository's current schema style. The
schema shape is:

```json
{
  "const": [
    "design-apple-foundation-models-handoff",
    "implement-apple-foundation-models-handoff",
    "review-apple-foundation-models-handoff",
    "debug-apple-foundation-models-handoff",
    "validate-apple-foundation-models-handoff",
    "route-apple-foundation-models-handoff"
  ]
}
```

- [ ] **Step 8: Run the package contracts and observe RED**

Run RED:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_plugin_contract \
  tests.test_generated_artifacts \
  tests.test_repository_guidance -v
bats tests/plugin_skeleton.bats
```

Expected: the six-capability assertions fail against five-capability canonical
metadata/generation. Existing unrelated tests remain green.

- [ ] **Step 9: Commit the tests-only RED package contract**

Commit the tests-only RED:

```bash
git add tests/test_plugin_contract.py \
  tests/test_generated_artifacts.py \
  tests/test_repository_guidance.py \
  tests/e2e/codex_plugin_load.py \
  tests/plugin_skeleton.bats
git diff --cached --check
git commit -m "test(DEV-136): require six-capability packaging"
```

- [ ] **Step 10: Update canonical metadata, schema, generator, and guidance**

Change only authored inputs. Preserve the shared plugin description and Claude
marketplace bytes when they remain truthful; do not churn them merely to name
the router. Update Codex interface prose only where the exact capability
contract requires it. Use separate workflow/router/all constants in the
generator and its topology validation.

The first generation check must report expected drift. Then generate and prove
idempotence:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/sync_generated_artifacts.py --check
PYTHONDONTWRITEBYTECODE=1 python3 scripts/sync_generated_artifacts.py --write
PYTHONDONTWRITEBYTECODE=1 python3 scripts/sync_generated_artifacts.py --check
```

- [ ] **Step 11: Validate the complete Task 3 GREEN package**

```bash
python3 -m json.tool \
  plugins/apple-foundation-models-handoff/metadata/codex-interface.json >/dev/null
python3 -m json.tool \
  plugins/apple-foundation-models-handoff/.codex-plugin/plugin.json >/dev/null
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_plugin_contract \
  tests.test_generated_artifacts \
  tests.test_repository_guidance -v
bats tests/plugin_skeleton.bats
python3 /Users/josephknickerbocker/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py \
  plugins/apple-foundation-models-handoff
git diff --check
```

Use `git diff -- .agents/plugins/marketplace.json` to prove it remained
byte-identical unless a canonical source byte actually required regeneration.

- [ ] **Step 12: Commit canonical and generated package changes**

```bash
git add CLAUDE.md AGENTS.md \
  plugins/apple-foundation-models-handoff/metadata/codex-interface.json \
  plugins/apple-foundation-models-handoff/.claude-plugin/plugin.json \
  plugins/apple-foundation-models-handoff/.codex-plugin/plugin.json \
  schemas/codex-interface-input.schema.json \
  scripts/sync_generated_artifacts.py
git add .agents/plugins/marketplace.json
git diff --cached --check
git commit -m "feat(DEV-136): advertise and generate router capability"
```

Before committing, unstage any listed canonical or generated path whose bytes
did not change. Commit boundary: authored metadata/schema/guidance/generator and
their exact generated outputs only.

### Task 4: Specify and bind contractual fixture ownership

**Files:**

- Modify: `tests/test_skill_cases.py`

**Interfaces:**

- Consumes: `WORKFLOW_SKILLS`, `ROUTER_SKILL`, and `ALL_CAPABILITIES` from the
  reviewed package contract.
- Produces: the `expectedSkillOwner: str` fixture/evidence contract and a
  repeatable `--case-id CASE_ID` runner interface that returns canonical-order
  selected cases.

- [ ] **Step 1: Add tests-only RED fixture/runner contracts**

Require each canonical case to contain one additional closed-schema string
field, `expectedSkillOwner`:

- baseline, positive, and complete-output rows: existing workflow owner;
- all five negative and all five ambiguous rows: router owner.

Require evidence rows emitted by the runner to carry both `skillUnderTest` and
`expectedSkillOwner`. Prove owner is contractual metadata and is never inferred
from absent Codex telemetry. Positive scoring must use the owner; non-positive
scoring must keep the existing exact-shape assertions byte-for-byte equivalent.

Require runner constants for `WORKFLOW_SKILLS`, `ROUTER_SKILL`, and
`ALL_CAPABILITIES`, all six payload SHA-256 values, and a refreshed canonical
fixture SHA-256. Require `WORKFLOW_SECTIONS` to remain five-only and prove
router-owned rows never index it.

Add a repeatable `--case-id` host/offline selector contract so affected gates
can consume the canonical 25-case file without authoring a second fixture.
Selection must reject unknown/duplicate IDs, preserve canonical order, bind the
selected exact cases in evidence, and leave the no-selector path as the full
canonical matrix.

Use this exact owner derivation in tests; fixture rows store the derived literal
value rather than computing it at runtime:

```python
def expected_skill_owner(case: dict[str, object]) -> str:
    if case["expectedActivation"] in {"no_activation", "clarification_required"}:
        return ROUTER_SKILL
    return str(case["skillUnderTest"])
```

The runner interface is a repeatable argparse option:

```python
parser.add_argument("--case-id", action="append", default=[])
```

Update mutation tests from “sixth skill” to “seventh/unapproved skill” and add
owner omission, substitution, overlap, prompt drift, scorer relaxation, stale
digest, and selector-order mutations.

- [ ] **Step 2: Run the fixture/runner contracts and observe RED**

Run RED:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_skill_cases.SkillCaseFixtureTests \
  tests.test_skill_cases.ContractMutationReproductionTests \
  tests.test_skill_cases.CodexForwardRunnerContractTests -v
```

Expected: FAIL because the fixture lacks owners and the runner remains bound to
five payloads/full-file-only selection.

- [ ] **Step 3: Commit the tests-only RED fixture/runner contract**

Commit tests-only RED:

```bash
git add tests/test_skill_cases.py
git diff --cached --check
git commit -m "test(DEV-136): specify router-owned fixture cases"
```

Commit boundary: tests only. Do not change the fixture, runner, or evidence.

#### Task 4, phase B: Bind the fixture, runner, payloads, and historical evidence

**Files:**

- Modify: `tests/fixtures/dev-136-codex-skill-cases.json`
- Modify: `tests/e2e/codex_skill_forward_tests.py`
- Modify: `docs/research/evidence/dev-136-codex-skill-tdd.json`

**Phase B interfaces:**

- Consumes: the Task 4 RED contracts, exact six payload bytes, and unchanged
  case prompts/rubrics/outcomes.
- Produces: amended 25-case fixture bytes, runner payload/fixture digests,
  `select_cases(fixture: dict[str, Any], case_ids: list[str]) -> dict[str, Any]`,
  and explicit historical-evidence supersession metadata.

- [ ] **Step 4: Add exact fixture ownership**

Use `apply_patch` to add only `expectedSkillOwner` to each of the 25 rows. Do
not reformat or change any other fixture value. Recompute and compare the 25
prompt hashes to the approved `APPROVED_PROMPT_SHA256` mapping before accepting
the diff.

- [ ] **Step 5: Preserve baseline evidence truthfully**

Do not rewrite the historical baseline capture as if it used the amended
fixture bytes. Keep its original `fixtureSha256`, host observations, hashes,
and outcomes. Add closed-schema supersession metadata stating that the original
fixture is superseded only by the `expectedSkillOwner` field amendment and that
the new Codex host evidence path is the capability proof. Update tests to bind
both the immutable historical digest and the new canonical digest.

- [ ] **Step 6: Update the runner minimally**

Add `expectedSkillOwner` to fixture and evidence closed schemas. Use the exact
six-capability topology and payload digests. Refresh all five workflow digests
because their bodies changed and add the router digest. Keep the positive and
non-positive scorers semantically unchanged except that positive selected-skill
matching reads `expectedSkillOwner`.

Implement the tested repeatable `--case-id` selector against the already loaded
canonical fixture. Do not accept arbitrary fixture content, alter case order,
or weaken fixture identity. Ensure cleanup/source/bound-copy checks still cover
every selected row.

Implement and unit-test this exact interface, raising `ValueError` for unknown
or duplicate requested IDs:

```python
def select_cases(
    fixture: dict[str, Any], case_ids: list[str]
) -> dict[str, Any]:
    """Return the full fixture or a canonical-order approved subset."""
```

- [ ] **Step 7: Validate GREEN**

```bash
python3 -m json.tool tests/fixtures/dev-136-codex-skill-cases.json >/dev/null
python3 -m json.tool docs/research/evidence/dev-136-codex-skill-tdd.json >/dev/null
python3 -m py_compile tests/e2e/codex_skill_forward_tests.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_skill_cases -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_skill_contract \
  tests.test_plugin_contract \
  tests.test_generated_artifacts \
  tests.test_repository_guidance -v
git diff --check
```

Inspect `git diff --word-diff` for the fixture and prove each row gained exactly
one owner field and no prompt/rubric/outcome drift.

- [ ] **Step 8: Commit fixture and runner bindings**

```bash
git add tests/fixtures/dev-136-codex-skill-cases.json \
  tests/e2e/codex_skill_forward_tests.py \
  docs/research/evidence/dev-136-codex-skill-tdd.json
git diff --cached --check
git commit -m "test(DEV-136): bind router fixture and payloads"
```

Commit boundary: canonical fixture ownership, runner implementation/digests,
and truthful historical-evidence supersession only.

### Task 5: Prove affected behavior and the complete Codex matrix

**Files:**

- Create: `docs/research/evidence/dev-136-codex-router-affected.json`
- Create: `docs/research/evidence/dev-136-codex-skill-host.json`
- Modify: `tests/test_skill_cases.py`

**Interfaces:**

- Consumes: the canonical fixture, `--case-id` selector, six bound payloads,
  and exact installed plugin source from Tasks 3-4.
- Produces: `CodexRouterHostEvidenceTests`, one 15-case affected evidence file,
  and one complete 25-case evidence file.

- [ ] **Step 1: Add RED final-evidence contracts**

Require the affected evidence to contain exactly the 15 affected rows in
canonical fixture order, including ten router-owned rows and five positive
anti-steal rows. Under the user's 2026-07-19 bounded affected-gate decision,
require all 15 rows to be attempted, at least 13 passes, at most two visible
failures, no blocked or not-applicable row, and Codex process exit code `0` for
every row. This supersedes only the prior exact-15 affected acceptance rule and
authorizes no retries. Keep the evidence status truthful: `pass` only for 15/15
and `fail` for one or two failures. Require passing rows to satisfy every
applicable assertion, each failing row to contain at least one failed applicable
assertion, and every non-applicable assertion to remain exactly
`not_applicable`. Every prerequisite remains `pass` except `pluginActivation`,
which is `pass` only when all activation assertions pass and otherwise is
`not_applicable`. Require the full evidence to contain all 25 canonical rows in
order, with 25 passes and no fail/blocked/not-applicable row.

Bind exact source commit, exact model/version/binary digest, canonical fixture
digest, six payload digests, plugin selector/source/bound-copy digests, case
owners, response hashes/counts, assertion outcomes, and cleanup results. Forbid
raw/private fields. Require both files to declare Claude `owner_deferred` and
not invoked.

Use exact evidence paths and expected counts:

```python
ROUTER_AFFECTED_EVIDENCE_PATH = (
    ROOT / "docs/research/evidence/dev-136-codex-router-affected.json"
)
FULL_HOST_EVIDENCE_PATH = (
    ROOT / "docs/research/evidence/dev-136-codex-skill-host.json"
)
ROUTER_AFFECTED_CASE_COUNT = 15
ROUTER_AFFECTED_MINIMUM_PASS_COUNT = 13
ROUTER_AFFECTED_MAXIMUM_FAIL_COUNT = 2
FULL_HOST_CASE_COUNT = 25
```

- [ ] **Step 2: Run the final-evidence contract and observe RED**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_skill_cases.CodexRouterHostEvidenceTests -v
```

Expected: FAIL because final host evidence files do not exist.

- [ ] **Step 3: Commit the tests-only RED final-evidence contract**

Commit the tests only:

```bash
git add tests/test_skill_cases.py
git diff --cached --check
git commit -m "test(DEV-136): require router host evidence"
```

- [ ] **Step 4: Run the 15-case affected gate**

First prove structural loading with the exact installed package:

```bash
codex --version
python3 tests/e2e/codex_plugin_load.py --repo-root .
```

Then run the canonical fixture with the 15 approved `--case-id` values from the
“Affected host cases” section. Use exact `CODEX_BIN`, model, and version:

```bash
CODEX_BIN="$(command -v codex)" python3 \
  tests/e2e/codex_skill_forward_tests.py \
  --mode host \
  --model gpt-5.6-sol \
  --codex-version 0.144.5 \
  --cases tests/fixtures/dev-136-codex-skill-cases.json \
  --case-id DEV136-FWD-DESIGN-001 \
  --case-id DEV136-FWD-DESIGN-002 \
  --case-id DEV136-FWD-DESIGN-003 \
  --case-id DEV136-FWD-IMPLEMENT-001 \
  --case-id DEV136-FWD-IMPLEMENT-002 \
  --case-id DEV136-FWD-IMPLEMENT-003 \
  --case-id DEV136-FWD-REVIEW-001 \
  --case-id DEV136-FWD-REVIEW-002 \
  --case-id DEV136-FWD-REVIEW-003 \
  --case-id DEV136-FWD-DEBUG-001 \
  --case-id DEV136-FWD-DEBUG-002 \
  --case-id DEV136-FWD-DEBUG-003 \
  --case-id DEV136-FWD-VALIDATE-001 \
  --case-id DEV136-FWD-VALIDATE-002 \
  --case-id DEV136-FWD-VALIDATE-003 \
  --evidence docs/research/evidence/dev-136-codex-router-affected.json
```

The host runner may exit `1` because one or two row failures truthfully produce
evidence status `fail`; that result still satisfies the higher-level affected
acceptance contract when all bounded conditions above hold. Preserve those
failures without retrying. If three or more rows fail, any row is blocked or
not applicable, any Codex process exits nonzero, or any other affected contract
condition fails, invoke `superpowers:systematic-debugging` and make the smallest
test-first correction in a dedicated fix commit. Do not weaken the fixture,
scorer, expected behavior, or privacy contract.

- [ ] **Step 5: Run the complete 25-case matrix**

Only after the 15-case evidence satisfies the bounded affected acceptance
contract:

```bash
CODEX_BIN="$(command -v codex)" python3 \
  tests/e2e/codex_skill_forward_tests.py \
  --mode host \
  --model gpt-5.6-sol \
  --codex-version 0.144.5 \
  --cases tests/fixtures/dev-136-codex-skill-cases.json \
  --evidence docs/research/evidence/dev-136-codex-skill-host.json
```

Any missing prerequisite is an explicit blocker and keeps DEV-136 open. Any
post-capture source, binary, bound-copy, or cleanup drift is `fail`, not
`blocked`.

- [ ] **Step 6: Validate host evidence**

```bash
python3 -m json.tool \
  docs/research/evidence/dev-136-codex-router-affected.json >/dev/null
python3 -m json.tool \
  docs/research/evidence/dev-136-codex-skill-host.json >/dev/null
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_skill_cases.CodexRouterHostEvidenceTests -v
git diff --check
```

- [ ] **Step 7: Commit normalized Codex host evidence**

```bash
git add docs/research/evidence/dev-136-codex-router-affected.json \
  docs/research/evidence/dev-136-codex-skill-host.json
git diff --cached --check
git commit -m "test(DEV-136): prove router and workflow activation"
```

Commit boundary: normalized Codex evidence only. Raw prompts, responses,
reasoning, events, commands, local paths, and credentials remain transient.

### Task 6: Verify, review, attach evidence, and open the stacked PR

**Files:** no production changes expected. Any review fix receives its own
test-first commit and repeats affected host evidence when it changes a skill,
fixture, scorer, runner, generator, or canonical metadata byte.

**Interfaces:**

- Consumes: all reviewed task commits and both normalized Codex GREEN evidence
  files.
- Produces: one clean final review verdict, a pushed stacked branch, one draft
  DEV-136 PR based on the DEV-137 branch, and a durable Linear evidence record.

- [ ] **Step 1: Run all offline and repository gates**

```bash
git diff --check
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py' -v
bats tests/plugin_skeleton.bats
PYTHONDONTWRITEBYTECODE=1 python3 scripts/sync_generated_artifacts.py --check
python3 /Users/josephknickerbocker/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py \
  plugins/apple-foundation-models-handoff
python3 /Users/josephknickerbocker/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  plugins/apple-foundation-models-handoff/skills/route-apple-foundation-models-handoff
python3 tests/e2e/codex_plugin_load.py --repo-root .
```

- [ ] **Step 2: Validate JSON, package, privacy, and generated ownership**

```bash
python3 -m json.tool .claude-plugin/marketplace.json >/dev/null
python3 -m json.tool .agents/plugins/marketplace.json >/dev/null
python3 -m json.tool \
  plugins/apple-foundation-models-handoff/.claude-plugin/plugin.json >/dev/null
python3 -m json.tool \
  plugins/apple-foundation-models-handoff/.codex-plugin/plugin.json >/dev/null
python3 -m json.tool \
  plugins/apple-foundation-models-handoff/metadata/codex-interface.json >/dev/null
python3 -m json.tool tests/fixtures/dev-136-codex-skill-cases.json >/dev/null
python3 -m json.tool \
  docs/research/evidence/dev-136-non-positive-router-red-baseline.json >/dev/null
python3 -m json.tool \
  docs/research/evidence/dev-136-codex-router-affected.json >/dev/null
python3 -m json.tool \
  docs/research/evidence/dev-136-codex-skill-host.json >/dev/null
rg -n '/Users/|/home/|file://|rawPrompt|rawResponse|rawReasoning|transcript|credential|Authorization' \
  docs/research/evidence/dev-136-*.json \
  tests/fixtures/dev-136-codex-skill-cases.json
```

The privacy `rg` must produce no prohibited live/private payload. Approved
synthetic prompt text in the canonical fixture is allowed; raw host material is
not.

- [ ] **Step 3: Run inherited Swift/SDK and source gates**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_dev_138_fixtures -v
rg -n 'import FoundationModels|LanguageModelSession|@Generable|@Guide|SystemLanguageModel' \
  plugins/apple-foundation-models-handoff/skills/route-apple-foundation-models-handoff \
  docs/research/evidence/dev-136-*.json
rg -n 'pseudocode|unsupported|blocked|not_applicable|availability|SDK' \
  plugins/apple-foundation-models-handoff/skills \
  docs/research/evidence/dev-136-*.json
```

Record router-specific Swift compilation as `not_applicable` because it contains
no Swift or Apple API claim. Do not convert an inherited SDK skip into a pass.

- [ ] **Step 4: Obtain the broad final review**

Generate one whole-branch review package from the DEV-136 merge base to `HEAD`
using the `superpowers:requesting-code-review` template. Dispatch a fresh
reviewer on the selected Sol model. The reviewer must assess the approved
design, this plan, the complete branch diff, all task reports, and the evidence
contracts.

Resolve every Critical or Important finding with one fix subagent, covering
tests, and a re-review. Record Minor findings in the SDD ledger and explicitly
triage them before PR creation.

- [ ] **Step 5: Push and create the stacked review boundary**

Verify the branch is stacked directly on the current DEV-137 head and rebase on
that head if the base moved. Re-run all offline gates after any rebase. Do not
merge, tag, release, or publish.

```bash
git status --short
git log --oneline --decorate --graph -40
git push -u origin codex/dev-136-core-skill-workflows
```

Create one draft DEV-136 PR with base branch
`codex/dev-137-progressive-reference-library`. The PR body must include:

- DEV-136 and the approved option-2 decision;
- dependency/base PR #11;
- atomic commit map;
- exact offline test counts and commands;
- Bats, generator, plugin, schema, fixture, SDK, privacy, load-probe, affected
  15-case, and full 25-case results;
- exact Codex version/model and evidence file hashes;
- explicit Claude deferral;
- no merge/release authorization.

- [ ] **Step 6: Attach evidence and complete Linear only if proven**

Add a DEV-136 Linear completion comment with the design/plan paths, commit range,
draft PR URL, commands, exact counts, evidence SHA-256 values, Codex
version/model, router-specific Swift `not_applicable`, inherited SDK status,
Claude deferral, and independent review verdict. Attach or link the normalized
evidence files and PR.

Re-read the complete DEV-136 Definition of Done. Mark it Done only when every
required item is proven and the stacked PR is reviewable. If any required host
gate is blocked, leave it In Progress and record the exact prerequisite; do not
claim completion.

## Atomic commit map

Expected boundaries, with review/fix commits inserted only when necessary:

1. `docs(DEV-136): approve explicit non-positive router` — already committed
   as `00c5056`.
2. `docs(DEV-136): propagate router ownership contract`.
3. `test(DEV-136): require router RED baselines`.
4. `docs(DEV-136): accept mixed pre-router evidence`.
5. `test(DEV-136): accept truthful mixed router baseline`.
6. `test(DEV-136): capture mixed router baselines`.
7. `test(DEV-136): specify non-positive router contract`.
8. `feat(DEV-136): add non-positive router ownership`.
9. `test(DEV-136): require six-capability packaging`.
10. `feat(DEV-136): advertise and generate router capability`.
11. `test(DEV-136): specify router-owned fixture cases`.
12. `test(DEV-136): bind router fixture and payloads`.
13. `test(DEV-136): require router host evidence`.
14. `test(DEV-136): prove router and workflow activation`.

Every task stops at its own independent review gate. A task is not complete
until both spec compliance and code quality are approved.
