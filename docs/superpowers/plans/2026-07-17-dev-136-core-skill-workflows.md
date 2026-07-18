# DEV-136 Core Skill Workflows Implementation Plan

> **Execution requirement:** Use `superpowers:subagent-driven-development` for this
> plan. Apply `superpowers:test-driven-development` to implementation changes,
> `superpowers:writing-skills` to every skill, and
> `superpowers:verification-before-completion` before a completion claim.

**Goal:** Implement and prove five Codex-active Apple Foundation Models handoff
workflow skills without adding another plugin capability surface.

**Architecture:** Five authored `SKILL.md` files implement DEV-134's deterministic
router and result contracts, link to DEV-137's fixed references, and are advertised
through authored metadata. DEV-135's generator remains the only writer of Codex
manifests and generated root guidance. Offline tests prove structure and contracts;
fresh Codex `gpt-5.6-sol` sessions prove activation and output behavior.

**Base:** `bdbfd335e32eba3efee32f2aac08bd3c2a100368`

**Branch:** `codex/dev-136-core-skill-workflows`

**Design:** `docs/superpowers/specs/2026-07-17-dev-136-core-skill-workflows-design.md`

## Execution controls

- Re-read DEV-136 and linked DEV-128/130/131/132/134/135/137 decisions before
  execution. Propagate any changed decision in Linear before changing implementation.
- Verify `git status --short` before every commit and preserve user changes.
- Use independent subagents only for read-only review or non-overlapping files.
  Shared contracts, generator edits, and generated artifacts are serialized.
- Use `apply_patch` for authored files and the generator for generated files.
- Add no commands, hooks, MCP servers, agents, dependencies, runtime packages,
  per-skill YAML, or sixth workflow.
- Do not invoke Claude. Record it as `blocked/owner-deferred`.
- Use Codex `0.144.5` and explicitly select `gpt-5.6-sol` for model-backed tests.

Use DEV-134's exact router enums everywhere in fixtures, skills, tests, and evidence:

| Field | Allowed values |
| --- | --- |
| `domain` | `foundation_models_handoff`, `out_of_domain`, `ambiguous` |
| `requestedOperation` | `design`, `implement`, `review`, `debug`, `validate`, `compound_review_fix`, `unspecified` |
| `artifactState` | `absent`, `proposal`, `approved_contract`, `implementation`, `evidence_bundle`, `unknown` |
| `evidenceState` | `not_requested`, `missing`, `available`, `failing`, `blocked`, `unknown` |

## Task 1: Freeze cases and capture five RED baselines

**Files:**

- Create: `tests/fixtures/dev-136-codex-skill-cases.json`
- Create: `docs/research/evidence/dev-136-codex-skill-tdd.json`
- Create: `tests/test_skill_cases.py`

### Step 1: Write fixture coverage tests

Require:

- exactly five baseline cases, one per exact skill identifier;
- exactly 20 forward cases, one `positive`, `negative`, `ambiguous`, and
  `complete-output` case per skill;
- stable unique IDs, `gpt-5.6-sol` as required model, and no expected answer in prompts;
- expected exact `requestedOperation`, `artifactState`, `evidenceState`, and rubric
  outside prompts, using only the normative enums above;
- DEV-134's review-and-fix prompt as the review-ordering case;
- negative coverage for App Intents, Apple Handoff, coding-session handoff,
  Foundation Models runtime Skills, generic Core ML, and Swift actors.

Run RED:

```bash
python3 -m unittest tests.test_skill_cases -v
```

Expected: FAIL because the fixture/evidence does not exist.

### Step 2: Add the minimal fixture

Base prompts on
`docs/research/evidence/dev-134-activation-prototype.json`, but give all cases stable
DEV-136 IDs and exactly one expected primary skill. Keep rubric data hidden from the
model-visible prompt.

Run GREEN:

```bash
python3 -m unittest tests.test_skill_cases -v
```

### Step 3: Capture baseline responses without the skills

Run five fresh Codex `gpt-5.6-sol` sessions with the plugin absent. Initially use fresh
subagent sessions under `superpowers:writing-skills`; Task 6 replaces this with the
repeatable host runner. Score only after response generation.

For each baseline commit only Codex version, model, base commit, prompt ID, response
SHA-256, normalized rubric result, and an observed failure/rationalization summary.
Raw live host responses remain transient and must not enter fixtures or repository
evidence. If the response passes, improve the discriminating prompt/rubric rather than
inventing a failure.

```bash
python3 -m json.tool docs/research/evidence/dev-136-codex-skill-tdd.json >/dev/null
python3 -m unittest tests.test_skill_cases -v
```

### Step 4: Commit cases and RED evidence

```bash
git add tests/fixtures/dev-136-codex-skill-cases.json \
  tests/test_skill_cases.py \
  docs/research/evidence/dev-136-codex-skill-tdd.json
git diff --cached --check
git commit -m "test(DEV-136): capture skill baselines and cases"
```

Commit boundary: fixtures, RED evidence, and coverage/schema test only.

## Task 2: Add RED skill-contract tests

**Files:**

- Create: `tests/test_skill_contract.py`
- Modify: `tests/test_plugin_contract.py`
- Modify: `tests/test_repository_guidance.py`

### Step 1: Specify the exact surface and semantics

Assert:

- exact five directories and one `SKILL.md` per directory, with no extra skill files;
- exact frontmatter keys `name` and `description`, names, and DEV-134 descriptions;
- four router inputs, one-clarification rule, review-first rule, and no skill calls;
- explicit adjacent-domain non-triggers;
- `architectureSchemaVersion: "1.0"` plus independent `stateVersion` and
  `policyVersion`;
- these exact ten common sections:
  1. `Activation and Scope`
  2. `Pattern and Ownership`
  3. `Apple API Availability`
  4. `State and Lifecycle`
  5. `Trust and Model Boundaries`
  6. `Context Policy`
  7. `Tools Effects and Confirmation`
  8. `Failure Recovery and Fallback`
  9. `Verification and Evidence`
  10. `Limitations`
- workflow-specific sections from DEV-134 in addition to those ten common sections;
- SDK/official evidence, compile-check, pseudocode, unsupported, and blocker rules;
- direct `../../references/<fixed-name>.md` links and no other reference names;
- package allowlist permits only five skills beyond DEV-135 files;
- no commands, hooks, MCP, agents, `openai.yaml`, or runtime package surface;
- canonical and generated guidance truthfully report five workflows.

Run RED:

```bash
python3 -m unittest \
  tests.test_skill_contract \
  tests.test_plugin_contract \
  tests.test_repository_guidance -v
```

Expected: FAIL because skills and truthful metadata/guidance are absent.

### Step 2: Commit RED tests

```bash
git add tests/test_skill_contract.py \
  tests/test_plugin_contract.py \
  tests/test_repository_guidance.py
git diff --cached --check
git commit -m "test(DEV-136): specify core workflow contracts"
```

Commit boundary: RED tests only. Do not weaken them in implementation commits.

## Task 3: Implement five minimal GREEN skills

**Files:**

- Create: `plugins/apple-foundation-models-handoff/skills/design-apple-foundation-models-handoff/SKILL.md`
- Create: `plugins/apple-foundation-models-handoff/skills/implement-apple-foundation-models-handoff/SKILL.md`
- Create: `plugins/apple-foundation-models-handoff/skills/review-apple-foundation-models-handoff/SKILL.md`
- Create: `plugins/apple-foundation-models-handoff/skills/debug-apple-foundation-models-handoff/SKILL.md`
- Create: `plugins/apple-foundation-models-handoff/skills/validate-apple-foundation-models-handoff/SKILL.md`

### Step 1: Implement one skill at a time

For each baseline, add the smallest instruction set that closes the observed failure
and implements:

1. exact frontmatter/activation boundary;
2. repository, artifact, and installed-SDK inspection;
3. four-input routing and single clarification;
4. ownership/state/trust/context/tool/effect/recovery protocol;
5. independent version labels and evidence/limitation labeling;
6. common and workflow-specific output sections;
7. relevant fixed DEV-137 links.

Use imperative steps and concise checklists. Do not copy volatile Apple declarations,
invent APIs, add marketing prose, or invoke another skill.

Run each focused test after its file, then the full slice:

```bash
python3 -m unittest tests.test_skill_contract tests.test_plugin_contract -v
```

Reference existence may be explicitly blocked before Task 7, but target-name and link
syntax checks must pass.

### Step 2: Fresh authoring probes

For each new skill, run its positive and complete-output prompts in fresh Codex `gpt-5.6-sol`
sessions. Record failures and changes. Refactor only in response to observed behavior.

### Step 3: Commit skills

```bash
git add plugins/apple-foundation-models-handoff/skills
git diff --cached --check
git commit -m "feat(DEV-136): add core handoff workflow skills"
```

Commit boundary: exactly five authored `SKILL.md` files.

## Task 4: Make metadata truthful and regenerate

**Files:**

- Modify: `plugins/apple-foundation-models-handoff/.claude-plugin/plugin.json`
- Modify: `plugins/apple-foundation-models-handoff/metadata/codex-interface.json`
- Modify if stale: `.claude-plugin/marketplace.json`
- Modify: `scripts/sync_generated_artifacts.py`
- Modify: `schemas/codex-interface-input.schema.json`
- Modify: `tests/test_generated_artifacts.py`
- Modify: `tests/test_plugin_contract.py`
- Generate: `plugins/apple-foundation-models-handoff/.codex-plugin/plugin.json`
- Generate: `.agents/plugins/marketplace.json`

### Step 1: Add RED metadata/generator assertions

Require this exact ordered capability list:

```json
[
  "design-apple-foundation-models-handoff",
  "implement-apple-foundation-models-handoff",
  "review-apple-foundation-models-handoff",
  "debug-apple-foundation-models-handoff",
  "validate-apple-foundation-models-handoff"
]
```

Require the canonical shared manifest to contain exactly
`"skills": "./skills/"`; the component root must discover exactly the five approved
skill directories. Require the generated Codex manifest to inherit the same `skills`
component path. Require truthful descriptions/starter prompts and one authored skill
per exact capability. Require JSON Schema and custom validation to reject a missing,
reordered, duplicated, or sixth capability.

```bash
python3 -m unittest tests.test_plugin_contract tests.test_generated_artifacts -v
```

Expected RED: scaffold metadata still has `capabilities == []`.

### Step 2: Update authored inputs and generator validation

Change only canonical data/schema/generator logic. Generate mechanical outputs:

```bash
python3 scripts/sync_generated_artifacts.py --check
python3 scripts/sync_generated_artifacts.py --write
python3 scripts/sync_generated_artifacts.py --check
```

The first check reports expected drift; the final check passes.

### Step 3: Validate metadata and generation

```bash
python3 -m unittest tests.test_plugin_contract tests.test_generated_artifacts -v
python3 -m json.tool \
  plugins/apple-foundation-models-handoff/.claude-plugin/plugin.json >/dev/null
python3 -m json.tool \
  plugins/apple-foundation-models-handoff/metadata/codex-interface.json >/dev/null
python3 -m json.tool \
  plugins/apple-foundation-models-handoff/.codex-plugin/plugin.json >/dev/null
```

### Step 4: Commit causal metadata change

```bash
git add plugins/apple-foundation-models-handoff/.claude-plugin/plugin.json \
  plugins/apple-foundation-models-handoff/metadata/codex-interface.json \
  scripts/sync_generated_artifacts.py \
  schemas/codex-interface-input.schema.json \
  tests/test_generated_artifacts.py \
  tests/test_plugin_contract.py \
  plugins/apple-foundation-models-handoff/.codex-plugin/plugin.json \
  .agents/plugins/marketplace.json
git add .claude-plugin/marketplace.json  # only if truthfulness required a change
git diff --cached --check
git commit -m "feat(DEV-136): advertise implemented workflows"
```

Commit boundary: canonical inputs, validator/schema/tests, and their generated outputs.

## Task 5: Correct guidance and regenerate the adapter

**Files:**

- Modify: `CLAUDE.md`
- Generate: `AGENTS.md`
- Modify: `tests/test_repository_guidance.py`

### Step 1: Replace only stale implementation status

Preserve DEV-133 guardrails, evidence labels, generated boundaries, and verification
commands. Replace scaffold-era “unimplemented” claims with the exact five workflows
and Codex-only evidence boundary. Do not duplicate DEV-137 references in root guidance.

```bash
python3 scripts/sync_generated_artifacts.py --write
python3 scripts/sync_generated_artifacts.py --check
python3 -m unittest tests.test_repository_guidance -v
```

### Step 2: Commit guidance and adapter

```bash
git add CLAUDE.md AGENTS.md tests/test_repository_guidance.py
git diff --cached --check
git commit -m "docs(DEV-136): document available handoff workflows"
```

Commit boundary: canonical guide, mechanical adapter, and parity/status test.

## Task 6: Build Codex forward-test evidence

**Files:**

- Create: `tests/e2e/codex_skill_forward_tests.py`
- Modify: `tests/fixtures/dev-136-codex-skill-cases.json`
- Modify: `docs/research/evidence/dev-136-codex-skill-tdd.json`
- Modify: `tests/test_skill_cases.py`
- Modify: `tests/e2e/codex_plugin_load.py`

### Step 1: Write RED runner tests

Using injected approved synthetic or redacted scorer outputs, require the runner to:

- start a fresh session per case and explicitly use `-m gpt-5.6-sol`;
- require Codex `0.144.5` or record an exact version blocker;
- never invoke Claude;
- score after generation without exposing expected answers;
- evaluate activation, routing, one clarification, review-first ordering, version
  labels, common sections, and workflow-specific sections;
- record `pass`, `fail`, `blocked`, or `not_applicable` per assertion;
- return nonzero on failure and a distinct blocked code for missing binary, auth,
  model, or plugin activation;
- hash live responses, discard their raw content after scoring, redact secrets, commit
  only normalized metadata/hash evidence, and never turn discovery into behavioral
  proof.

```bash
python3 -m unittest tests.test_skill_cases -v
```

Expected: FAIL because the runner is absent.

### Step 2: Implement offline and host modes

Offline unit mode uses only approved synthetic or redacted scorer outputs and
requires no network, credentials, or paid service. No raw live host response may be
promoted into an offline fixture. Host mode runs one
`codex exec --ephemeral -m gpt-5.6-sol`
session per prompt using the discoverable plugin and existing authenticated host
context without copying credentials.

Exact host command:

```bash
CODEX_BIN="$(command -v codex)" \
python3 tests/e2e/codex_skill_forward_tests.py \
  --mode host \
  --model gpt-5.6-sol \
  --codex-version 0.144.5 \
  --cases tests/fixtures/dev-136-codex-skill-cases.json \
  --evidence docs/research/evidence/dev-136-codex-skill-tdd.json
```

Stop blocked when `gpt-5.6-sol`, authentication, or plugin discovery is unavailable. Never
fall back to another model or directly inject skill text to bypass activation.

### Step 3: Update the plugin-load probe

Change `tests/e2e/codex_plugin_load.py` so the cache allowlist expects five skills plus
metadata, capabilities match the five names, and activation is not scaffold-blocked.
Keep discovery as structural evidence; the new runner owns behavior.

```bash
python3 -m unittest tests.test_skill_cases -v
python3 tests/e2e/codex_plugin_load.py --repo-root .
```

### Step 4: Run all forward cases

After Task 7's rebase, execute the host command and inspect every failure. For a real
skill failure, make the smallest skill correction, run a fresh affected case, then
rerun all 20. Never weaken expected behavior to obtain green.

```bash
python3 -m json.tool docs/research/evidence/dev-136-codex-skill-tdd.json >/dev/null
python3 -m unittest tests.test_skill_cases -v
```

### Step 5: Commit runner and evidence

```bash
git add tests/e2e/codex_skill_forward_tests.py \
  tests/e2e/codex_plugin_load.py \
  tests/fixtures/dev-136-codex-skill-cases.json \
  tests/test_skill_cases.py \
  docs/research/evidence/dev-136-codex-skill-tdd.json
git diff --cached --check
git commit -m "test(DEV-136): prove Codex skill workflows"
```

Commit boundary: behavioral runner, synthetic/redacted offline scorer cases, and
normalized host metadata/hash evidence. Commit focused skill fixes separately
immediately before this evidence commit so the TDD loop is reviewable.

## Task 7: Rebase above DEV-137 and prove references

**Files:**

- Do not author DEV-137 reference files in DEV-136
- Verify: `plugins/apple-foundation-models-handoff/references/*.md`

### Step 1: Rebase only DEV-136 commits

Get the reviewed final DEV-137 SHA, require a clean worktree, then run:

```bash
git status --short
git rebase --onto <DEV137_HEAD> \
  bdbfd335e32eba3efee32f2aac08bd3c2a100368 \
  codex/dev-136-core-skill-workflows
```

Preserve DEV-137 reference content and DEV-136 skill/metadata content in conflicts.
Do not squash DEV-137 into a DEV-136 commit.

### Step 2: Prove resolution and atomicity

```bash
python3 -m unittest tests.test_skill_contract -v
git diff --name-status <DEV137_HEAD>...HEAD
git log --oneline <DEV137_HEAD>..HEAD
```

Expected: all links resolve and the stacked diff contains only DEV-136 changes. A
changed DEV-137 filename requires a stop and durable decision propagation, not an
unreviewed local workaround.

### Step 3: Run the host suite

Execute Task 6's five baselines and 20 forward cases on the rebased stack. Only
evidence and evidence-driven skill-fix commits may follow.

## Task 7A: Normalize the pinned Codex 0.144.5 web-search JSONL defect

**Files:**

- Modify: `tests/test_skill_cases.py`
- Modify: `tests/e2e/codex_skill_forward_tests.py`

### Step 1: Write and commit the failing protocol tests

Add a focused test that manually constructs the exact Codex 0.144.5 JSONL shape
documented by official tag `rust-v0.144.5`: `item.started` and `item.completed`
`web_search` records whose immediate item object contains outer `id: item_0` and
flattened inner `id: search-1`. Require `_tool_events` to retain the first/outer
lifecycle ID.

Add negative cases proving that the compatibility parser still rejects:

- a duplicate `id` on any non-`web_search` item;
- three `id` entries on a `web_search` item;
- duplicate `type`, `query`, or `action` entries;
- a duplicate nested inside `action`;
- a non-`item_[0-9]+` outer ID; and
- the same duplicate web-search object through generic `_strict_json_loads`.

Run the exact new test and require it to fail for the missing compatibility rule:

```bash
python3 -m unittest \
  tests.test_skill_cases.CodexForwardRunnerContractTests.test_codex_01445_web_search_duplicate_id_is_narrowly_normalized \
  -v
```

Commit only `tests/test_skill_cases.py` as the RED boundary.

### Step 2: Implement the JSONL-only compatibility decoder

Add a Codex-record-specific object-pairs decoder used only by
`_codex_jsonl_events`. Keep `_strict_json_loads` unchanged for fixtures,
evidence, manifests, and all other JSON.

Permit exactly two immediate `item.id` entries only when the record is
`item.started` or `item.completed`, the unique item keys are exactly
`id,type,query,action`, `type` is exactly `web_search`, both IDs are non-empty
strings, and the first/outer ID matches `item_[0-9]+`. Preserve the first ID so
the existing lifecycle pairing remains authoritative. Reject every other
duplicate key, location, count, or type before normal schema validation.

Run the focused test plus existing strict JSON, JSONL schema, lifecycle, malformed
stream, and model-unavailable tests. Commit only
`tests/e2e/codex_skill_forward_tests.py` as the GREEN boundary.

### Step 3: Re-run the exact host matrix

Run the full 25-case Codex host command from Task 8 into a temporary evidence path
first. Do not replace the tracked baseline evidence unless all 25 rows are valid and
the evidence validator passes. Record the pinned upstream source, both repair SHAs,
and the fresh host result in DEV-136, DEV-139, and DEV-141.

## Task 7B: Release the completed case copy before the independent post-check

**Files:**

- Modify: `tests/test_skill_cases.py`
- Modify: `tests/e2e/codex_skill_forward_tests.py`

### Step 1: Write and commit the failing cleanup-order tests

Extend the host lifecycle tests with an instrumented bound-copy factory and post-case
prerequisite checker. Require the case's verified execution copy and private directory
to exist for the complete child-process call, but to be absent before the post-case
checker starts. Also prove that process failures, post-check failures, early returns,
and final cleanup do not leave the copy or directory behind.

Run the focused lifecycle tests and require the new ordering assertion to fail against
the current runner because it retains the execution copy through the post-check.
Commit only `tests/test_skill_cases.py` as the RED boundary.

### Step 2: Move cleanup to the closed-process boundary

In `run_host`, unlink the per-case bound executable and remove its private directory
immediately after `process_runner` returns or raises, before calling the independent
post-capture prerequisite checker. Keep the existing `finally` cleanup idempotent as
defense in depth. Do not alter snapshot identity, digest comparison, prerequisite
classification, evidence status derivation, or retry behavior.

Run the focused lifecycle tests, all `CodexForwardRunnerContractTests`, and the full
`tests.test_skill_cases` module. Commit only
`tests/e2e/codex_skill_forward_tests.py` as the GREEN boundary.

### Step 2A: Close the review-discovered failure-atomicity gaps

Independent review must inject and reproduce all of these faults without a model:

- output-temp descriptor close/allocation failure;
- bound-copy unlink/rmdir failure while output allocation fails; and
- raw-output unlink failure after private response bytes exist.

Commit test-only RED coverage proving that none of these paths may leak a descriptor,
bound executable, private directory, or raw response, and none may escape a traceback.

Then retain the secure `mkstemp` descriptor through the child lifetime and put output
allocation inside the same per-case cleanup envelope. Final cleanup must zeroize the
output inode before close/unlink, use a no-follow path fallback when descriptor
zeroization is unavailable, and retry idempotent bound cleanup on every exit. An
unresolved bound cleanup fault returns normalized
`fail/post_capture_prerequisite_drift`; an unresolved private-output cleanup fault
returns normalized fail. Preserve the Step 2 ordering and commit only the runner as a
follow-up GREEN boundary.

Repeat focused, forward-runner, full skill-case, synthetic fault, compile, and diff
checks, followed by a fresh independent review. The first Step 2 GREEN is not approved
evidence by itself.

### Step 2B: Make cleanup ownership-safe under descriptor and path replacement

Add test-only RED coverage for review-discovered adversarial cases:

- a close call that takes effect, reports an error, and is followed by immediate
  reuse of the same descriptor number must never cause a second close;
- after direct truncate failure, replacement of the output pathname by a hardlink to
  another inode must not truncate or unlink the replacement;
- direct truncate plus path-open failure must still zero the original private bytes
  through the owned output handle; and
- bound-copy construction failure combined with transient unlink or rmdir failure must
  leave neither the copy nor its directory.

Then transfer the `mkstemp` descriptor into a single owned unbuffered binary file
object, close that owner exactly once, and remove numeric close retry/probing. Capture
the original regular-file `(device, inode)` once and never replace it; every no-follow
path fallback must match that identity before touching the path. If truncate fails,
overwrite the original length with zero bytes through the owned handle, flush, and
fsync. Apply retried path cleanup inside `_bound_executable_copy` construction-failure
handling. Preserve all Step 2A status, ordering, privacy, sink, and no-retry semantics.

Commit RED tests and GREEN runner separately. Require another clean independent fault
review before Step 3; neither earlier GREEN is final evidence by itself.

### Step 3: Verify storage and retry the matrix

Remove only DEV-136-owned stale temporary artifacts, confirm enough space for one
248 MB verified executable copy, and rerun Task 8's exact 25-case host command into a
new temporary evidence path. A remaining `OSError 28` is an explicit host blocker;
do not delete unrelated user data or reinterpret it as pass.

## Task 8: Full verification before completion

Invoke `superpowers:verification-before-completion` and run fresh commands.

### Step 1: Generation and schemas

```bash
python3 scripts/sync_generated_artifacts.py --check
python3 scripts/sync_generated_artifacts.py --write
python3 scripts/sync_generated_artifacts.py --check
git diff --exit-code
python3 -m json.tool .claude-plugin/marketplace.json >/dev/null
python3 -m json.tool .agents/plugins/marketplace.json >/dev/null
python3 -m json.tool plugins/apple-foundation-models-handoff/.claude-plugin/plugin.json >/dev/null
python3 -m json.tool plugins/apple-foundation-models-handoff/.codex-plugin/plugin.json >/dev/null
python3 -m json.tool plugins/apple-foundation-models-handoff/metadata/codex-interface.json >/dev/null
```

### Step 2: Repository, fixture, and package

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
bats tests/plugin_skeleton.bats
python3 tests/e2e/codex_plugin_load.py --repo-root .
python3 -m json.tool docs/research/evidence/dev-136-codex-skill-tdd.json >/dev/null
```

### Step 3: Codex host

```bash
codex --version
CODEX_BIN="$(command -v codex)" \
python3 tests/e2e/codex_skill_forward_tests.py \
  --mode host \
  --model gpt-5.6-sol \
  --codex-version 0.144.5 \
  --cases tests/fixtures/dev-136-codex-skill-cases.json \
  --evidence docs/research/evidence/dev-136-codex-skill-tdd.json
```

Require exact version/model, five baselines, 20 forward cases, and no unresolved
rubric failure or blocker. A blocked host keeps DEV-136 incomplete despite green
offline tests.

### Step 4: Swift/API checks

```bash
rg -n 'import FoundationModels|LanguageModelSession|@Generable|@Guide|Tool|SystemLanguageModel' \
  plugins/apple-foundation-models-handoff/skills \
  docs/research/evidence/dev-136-codex-skill-tdd.json
rg -n 'pseudocode|unsupported|blocked|not_applicable|availability|SDK' \
  plugins/apple-foundation-models-handoff/skills \
  docs/research/evidence/dev-136-codex-skill-tdd.json
```

Compile each concrete Swift sample using DEV-128's platform/SDK command. If there is
no concrete sample, record `not_applicable`. If the SDK is missing, record `blocked`
with the exact prerequisite; never claim pass.

### Step 5: Diff, cleanliness, and independent review

```bash
git status --short
git diff --check <DEV137_HEAD>...HEAD
git diff --stat <DEV137_HEAD>...HEAD
git log --oneline <DEV137_HEAD>..HEAD
```

Request independent code/skill review, address evidence-backed findings, and rerun
the full matrix after the last change.

## Task 9: Linear evidence and stacked PR handoff

### Step 1: Attach durable evidence to DEV-136

Link:

- this design and plan;
- each DEV-136 commit SHA and atomic boundary;
- exact fresh verification commands/results;
- `docs/research/evidence/dev-136-codex-skill-tdd.json`;
- Codex version/model and all 25 verdicts;
- DEV-137 reference-resolution proof;
- Claude as `blocked/owner-deferred`;
- Swift compile pass, `not_applicable`, or exact blocker.

Propagate only genuinely changed decisions to DEV-138/139/140/141.

### Step 2: Create the atomic stacked PR

While DEV-137 is unmerged, target DEV-136 at the DEV-137 branch/head so its PR diff is
DEV-136-only. After DEV-137 merges, rebase/retarget and verify the same atomic diff.
Do not push, merge, publish, tag, or release without the authorized project step.

### Step 3: Completion gate

Complete DEV-136 only after all five workflows pass fresh Codex `gpt-5.6-sol` tests, all
repository/generation/schema/fixture/package/link checks pass, generated files are in
sync, the PR is independently reviewable, forbidden surfaces are absent, and evidence
is durable in Linear. File existence, lint, or discovery alone is insufficient.
