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

### Step 2C: Order ownership transfer and pathname removal safely

Add test-only RED coverage for the final review findings:

- an output-owner constructor that consumes/closes the descriptor, reuses its number,
  and then raises must not let the caller close the replacement descriptor;
- a replacement pathname installed during the owner's single close must remain present
  and unmodified, and the case must normalize to fail; and
- a bound-copy close that takes effect, reuses its number, and raises must not be
  followed by a second close in final cleanup.

Then move each numeric descriptor to its unowned sentinel before calling `os.fdopen`
or the explicit bound-copy `os.close`. Zeroize and identity-check the original output,
unlink that verified original path while the owner is still open, close the owner once,
and afterward only verify pathname absence. Never unlink a post-close replacement.
Preserve every prior cleanup, identity, blocker, sink, and no-retry rule.

Commit RED tests and GREEN runner separately, run all prior focused cases and full
suites, and obtain clean independent approval before Step 3.

### Step 3: Verify storage and retry the matrix

Remove only DEV-136-owned stale temporary artifacts, confirm enough space for one
248 MB verified executable copy, and rerun Task 8's exact 25-case host command into a
new temporary evidence path. A remaining `OSError 28` is an explicit host blocker;
do not delete unrelated user data or reinterpret it as pass.

## Task 7D: Repair the pinned web-search lifecycle boundary

**Files:**

- Modify: `tests/test_skill_cases.py`
- Modify: `tests/e2e/codex_skill_forward_tests.py`
- Verify only: pinned OpenAI `rust-v0.144.5` source at commit
  `87db9bc18ba5bc82c1cb4e4381b44f693ee35623`

### Step 1: Capture the official lifecycle as RED

The post-cleanup host retry reached Codex case 1, then failed closed as
`event_stream_invalid`. Pinned official test
`web_search_start_and_completion_reuse_item_id` proves that Codex 0.144.5 emits a
web-search start with an empty query and `other` action, then reuses the outer item
ID while filling the real query/action on completion. Add a regression with that
exact start/completion transition and negative controls for:

- nonempty start query;
- any start action other than the closed `{\"type\": \"other\"}` object;
- mismatched outer IDs;
- unpaired completion;
- duplicate keys other than the already approved two `id` fields;
- malformed or open completion actions.

Run the exact selector and prove it fails only because query/action are currently
classified as immutable. Commit the RED tests separately.

### Step 2: Implement the narrow lifecycle rule

Remove query/action from cross-event immutable identity checks for web searches.
Instead, require the exact official placeholder state on `item.started`, validate
both records with the existing closed schema/type checks, and retain outer-ID pairing
through completion. Do not change the generic strict JSON loader, the narrow duplicate
`id` decoder, any other item lifecycle, or scoring behavior.

Run:

```bash
python3 -m unittest \
  tests.test_skill_cases.CodexForwardRunnerContractTests.test_codex_01445_web_search_lifecycle_matches_official_output \
  tests.test_skill_cases.CodexForwardRunnerContractTests.test_codex_01445_jsonl_schemas_and_command_lifecycle_are_exact \
  tests.test_skill_cases.CodexForwardRunnerContractTests.test_codex_01445_noncommand_item_lifecycles_and_statuses_are_exact \
  tests.test_skill_cases.CodexForwardRunnerContractTests.test_codex_01445_web_search_duplicate_id_is_narrowly_normalized \
  -v
python3 -m unittest tests.test_skill_cases -v
python3 -m unittest discover -s tests -p 'test_*.py' -v
bats tests/plugin_skeleton.bats
python3 scripts/sync_generated_artifacts.py --check
git diff --check
```

Commit the GREEN runner separately and obtain independent parser review before any
new authenticated host run.

### Step 3: Retry normalized host evidence

Rerun the exact 25-case command into a new temporary evidence path. Inspect only the
normalized result, keep the tracked RED baseline unchanged unless all 25 cases pass,
and record any new fail-closed boundary in DEV-136 plus DEV-139/DEV-141 before further
changes. Raw prompts, responses, and tool events remain transient and uncommitted.

### Step 4: Close the reviewed inner-identity gap

Independent review of the first GREEN found that the duplicate raw/inner web-search
ID was validated and discarded. Add RED regressions proving rejection of:

- start `item_0/search-1` followed by completion `item_0/search-2`;
- two simultaneously open outer IDs that both claim `search-1`;
- any scorer-visible normalized tool event that exposes parser bookkeeping.

Retain the inner ID only as private parser metadata. Require the same outer-to-inner
association across the pair and a unique open owner for every inner ID. Strip the
private metadata from copied completed tool events before returning them to scoring;
never mutate the validated lifecycle state in place. Single-ID synthetic controls must
receive deterministic internal identity without changing their public shape. Preserve
the exact duplicate-key allowlist, official mutable query/action transition, start
placeholder validation, and every other item lifecycle.

Commit the new RED tests and GREEN parser separately. Rerun all Task 7D selectors,
`tests.test_skill_cases`, the full repository suite, Bats, generation sync, compile,
and diff checks, then obtain a new independent approval before Step 3's next host run.

### Step 5: Remove vacuous immutable-field controls

The identity review found two legacy web-search query/action mutation negatives that
now pass only because their started item violates the exact empty-query/`other`
placeholder rule. Replace them with positive assertions that begin from the valid
placeholder and complete with populated query/action. Keep the inner-ID and other
immutable-field negatives unchanged. Commit this as a tests-only repair, run the full
Task 7D and repository validation commands, and obtain final independent approval.

## Task 7E: Harden host output determinism and collab spawn lifecycle

**Files:**

- Modify: `tests/test_skill_contract.py`
- Modify: `tests/test_skill_cases.py`
- Modify: `tests/e2e/codex_skill_forward_tests.py`
- Modify: `plugins/apple-foundation-models-handoff/skills/design-apple-foundation-models-handoff/SKILL.md`
- Modify: `plugins/apple-foundation-models-handoff/skills/implement-apple-foundation-models-handoff/SKILL.md`
- Modify: `plugins/apple-foundation-models-handoff/skills/review-apple-foundation-models-handoff/SKILL.md`
- Modify: `plugins/apple-foundation-models-handoff/skills/debug-apple-foundation-models-handoff/SKILL.md`
- Modify: `plugins/apple-foundation-models-handoff/skills/validate-apple-foundation-models-handoff/SKILL.md`

### Step 1: Capture deterministic-output and recursion requirements as RED

Add skill-contract tests requiring every canonical skill to say, unambiguously:

- serialize `selectedSkill` as an exact assignment to that skill's canonical name;
- serialize the four populated `routerInput` values on one physical line;
- put `architectureResult` on the immediately following line;
- emit exactly one fenced `text` block in the whole response and reserve it for the
  result envelope;
- render only the exact required headings, once and in order;
- never invoke `codex exec`, `tests/e2e/codex_skill_forward_tests.py`, or a
  Claude/Codex host matrix from inside the skill; existing normalized host evidence
  may be inspected, but missing outer-harness evidence is `blocked`.

Prove the tests fail against all five current skills, then commit tests only.

### Step 2: Harden the canonical skill text

Add the smallest shared serialization and outer-harness language under the existing
Output Contract and Guardrails owners. Do not duplicate the machine schema, headings,
references, router enums, or workflow prose. Do not change fixtures, scorer logic,
generated Codex metadata, Apple claims, or capability scope.

Run:

```bash
python3 -m unittest tests.test_skill_contract -v
python3 -m unittest tests.test_skill_cases -v
python3 -m unittest discover -s tests -p 'test_*.py' -v
bats tests/plugin_skeleton.bats
python3 scripts/sync_generated_artifacts.py --check
git diff --check
```

Commit the five canonical skills separately from the RED tests and request an
independent skill-contract review.

### Step 3: Capture and implement the pinned collab-spawn lifecycle

Add an exact synthetic stream from official Codex 0.144.5
`collab_spawn_begin_and_end_emit_item_events`: `spawn_agent` starts with empty receiver
IDs and agent states, then completes with assigned receiver IDs and matching agent
state keys. Prove the current parser rejects this supported transition. Add negatives
for nonempty start receivers/states, completed receiver/state mismatch, and receiver
mutation on non-spawn collab tools.

In GREEN, permit receiver population only for `spawn_agent`; require the exact empty
start placeholder and a closed completed receiver/state association. Preserve receiver
identity for other collab tools and retain tool, sender, prompt, outer-ID, schema,
status, pairing, and metadata rules. Commit RED and GREEN separately and obtain an
independent parser review.

### Step 4: Rerun affected host boundaries before the matrix

Use the reviewed exact host path to rerun baseline review, baseline debug, baseline
validate, forward design 001, and the no-activation case that exposed collab parsing.
Capture only normalized structural/hash evidence; do not retain raw responses or tool
events. A remaining failure returns to RED/GREEN diagnosis. Only after all affected
boundaries pass, rerun all 25 cases into a new temporary evidence path.

### Step 5: Reject empty completed spawn identities

Independent review of the combined GREEN found that the completed `spawn_agent`
association accepts `receiver_thread_ids=[""]` with an identically keyed
`agents_states` map. Add a tests-only negative mutation proving empty receiver IDs
and empty state-map keys fail closed while a nonblank official lifecycle still
passes. Include spaces-only and tab-only receiver/state identity mutations. Then
require every completed receiver identity and every associated state key to be a
string whose trimmed value is nonempty before checking uniqueness and exact raw
key-set association.

Commit the RED test and GREEN parser separately. Rerun the supported lifecycle,
every collab transition negative, the complete skill-case suite, repository suite,
Bats, generation sync, compile, and diff checks. The partial host run from the
pre-repair head is non-evidence and must be discarded; restart affected host
boundaries and the full 25-case matrix only from the corrected, independently
approved head.

## Task 7F: Accept the pinned Codex file-change lifecycle

**Files:**

- Modify: `tests/test_skill_cases.py`
- Modify: `tests/e2e/codex_skill_forward_tests.py`

Official Codex `rust-v0.144.5` maps all non-message/non-reasoning items through
the started/completed identity table. The exact host replay emitted four
`file_change` pairs and the current runner rejected every start record.

### Step 1: Add exact lifecycle RED

Add an official-shape positive stream with one `item.started/file_change`
(`status=in_progress`) and one `item.completed/file_change`
(`status=completed`) sharing one nonblank outer ID and the same closed `changes`
list. Add negatives for completion without start, duplicate start, mismatched
outer ID, changed `changes`, a terminal start status, an in-progress completion,
unknown status, and extra item/change fields. Keep completion `failed` supported
only as the terminal failure state.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v \
  tests.test_skill_cases.CodexForwardRunnerContractTests.test_codex_01445_file_change_lifecycle_matches_official_output
git diff --check
```

Expected RED: only the official supported pair is rejected as
`Codex JSONL item lifecycle is invalid`; the exact negative mutations remain
rejected. Commit only the test file as
`test(DEV-136): capture file change lifecycle`.

### Step 2: Implement the narrow paired rule

Permit `file_change` on start and completion, add it to the paired item types,
require `in_progress` at start, require `completed` or `failed` at completion,
and compare the closed `changes` list as immutable pair identity. Preserve the
existing item ID, schema, change kind, path, duplicate, pairing, turn, and event
rules. Do not make any other lifecycle optional.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v \
  tests.test_skill_cases.CodexForwardRunnerContractTests.test_codex_01445_file_change_lifecycle_matches_official_output \
  tests.test_skill_cases.CodexForwardRunnerContractTests.test_codex_01445_noncommand_item_lifecycles_and_statuses_are_exact \
  tests.test_skill_cases.CodexForwardRunnerContractTests.test_codex_01445_jsonl_schemas_and_command_lifecycle_are_exact
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_skill_cases -v
python3 -m py_compile tests/e2e/codex_skill_forward_tests.py
git diff --check
```

Commit only the runner as `fix(DEV-136): parse file change lifecycle`, then
obtain independent parser review before another host matrix.

### Step 3: Close reviewed outer-item identity gaps

Independent review must add tests-only negatives for empty, spaces-only,
tabs-only, and representative Unicode-whitespace item IDs, plus sequential
reuse of one outer ID after its first terminal item. Exercise a paired
`file_change`, another paired tool item, and a completion-only message/error
control so uniqueness is parser-wide. Keep a valid exact raw start/completion
identity positive.

Require `item.id` to be a string whose `strip()` value is nonempty, but never
trim or normalize it for pairing. Track stream-private seen outer IDs: a start
claims an unseen ID, its matching completion may use that exact open ID once,
and every completion-only item claims an unseen ID. After terminal completion,
the ID remains spent for the rest of the stream. Preserve all inner web-search,
collab, status, schema, immutable-field, turn, and cleanup rules.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v \
  tests.test_skill_cases.CodexForwardRunnerContractTests.test_codex_item_ids_are_nonblank_and_stream_unique
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_skill_cases -v
python3 -m py_compile tests/e2e/codex_skill_forward_tests.py
git diff --check
```

Commit RED only as `test(DEV-136): reject invalid outer item identities`, then
GREEN runner only as `fix(DEV-136): enforce outer item identity`. Obtain a new
independent review before any host retry.

## Task 7G: Make every result-envelope field syntactically complete

**Files:**

- Modify: `tests/test_skill_contract.py`
- Modify: the five canonical
  `plugins/apple-foundation-models-handoff/skills/*/SKILL.md` files

The live scorer requires every `architectureResult` child to be an indented
assignment with a nonempty value, but the canonical templates and their tests
currently encode several required fields as bare names. Preserve the exact
field names, order, schema version, pattern enum, and semantics.

### Step 1: Add parser-backed template RED

Add a structural test that extracts the one fenced positive template, requires
the four preamble lines, and parses every indented result line with the same
closed name/assignment grammar as the live scorer. Require exactly these fields
in order: `architectureSchemaVersion`, `stateVersion`, `policyVersion`,
`workflow`, `scope`, `pattern`, `source`, `destination`, `finalResponseOwner`,
`apiAvailability[]`, `stateModel`, `trustBoundaries[]`, `contextPolicy`,
`toolAndEffectPolicy`, `failurePolicy`, `verification[]`, and `limitations[]`.
Every value slot must be nonempty.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v \
  tests.test_skill_contract.SkillContractTests.test_positive_result_template_is_parseable
git diff --check
```

Expected RED: all five skills fail only on the current bare fields. Commit only
the test as `test(DEV-136): require parseable result templates`.

### Step 2: Correct only the canonical templates

Give every bare required field a descriptive nonempty value slot using `:` or
`=`. Do not add fields, headings, prose sections, APIs, capabilities, or response
formats. Update the shared expected template in the test only in the RED commit;
the GREEN commit changes canonical skills only.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_skill_contract -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_skill_cases -v
python3 scripts/sync_generated_artifacts.py --check
git diff --check
```

Commit only the five canonical skills as
`fix(DEV-136): complete result template assignments` and request independent
contract review.

### Step 3: Refresh the five cryptographic payload bindings

The canonical edit must make the existing five `SKILL_PAYLOAD_SHA256` values
fail. Treat those exact prerequisite failures as RED; do not weaken or remove
payload binding. From the committed canonical `SKILL.md` bytes, recompute each
SHA-256 and update only the five constants in
`tests/e2e/codex_skill_forward_tests.py`. Verify every constant against a fresh
hash calculation and keep the runner commit separate from the skill commit.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_skill_contract -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_skill_cases -v
python3 scripts/sync_generated_artifacts.py --check
python3 -m py_compile tests/e2e/codex_skill_forward_tests.py
git diff --check
```

Expected: contract 21/21 and skill cases 96/96 pass; generation and compile are
clean. Commit only the runner as
`fix(DEV-136): refresh bound skill payloads`.

## Task 7H: Isolate every mutating Codex host case

**Files:**

- Modify: `tests/test_skill_cases.py`
- Modify: `tests/e2e/codex_skill_forward_tests.py`

The host matrix created Swift source/test files in the authoritative DEV-136
worktree. The runner must preserve full repository context without allowing a
model-generated change to reach the issue checkout.

### Step 1: Add isolation and cleanup RED

Add synthetic host-runner tests requiring every process invocation to receive a
fresh detached disposable Git worktree as `cwd`. Prove successful, nonzero,
exception, scoring-failure, and early-stop paths force-remove that worktree and
leave the authoritative status snapshot byte-identical. Inject cleanup failure
and authoritative state drift; both must produce a stable explicit hard-failure
reason without exposing an absolute path or raw diff in evidence. Prove one
case's created file is absent from the next case and from `ROOT`.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v \
  tests.test_skill_cases.CodexForwardRunnerContractTests.test_host_cases_use_disposable_worktrees \
  tests.test_skill_cases.CodexForwardRunnerContractTests.test_host_worktree_cleanup_failures_fail_closed
git diff --check
```

Expected RED: the current process runner has no `cwd` isolation and writes into
the caller checkout. Commit tests only as
`test(DEV-136): require isolated host cases`.

### Step 2: Implement disposable worktree ownership

Create a fresh detached worktree at the captured repository HEAD per case using
argument-vector subprocess calls. Pass only that path as the Codex process cwd.
In `finally`, force-remove the worktree, prune its private metadata, and verify
both path removal and the authoritative status snapshot. Treat construction,
cleanup, or source-state drift as a named hard failure; never clean or rewrite
the authoritative checkout. Keep disposable paths, status bytes, and generated
content out of normalized evidence. Preserve bound-binary and private-response
cleanup precedence.

Use exact normalized hard-failure reasons: `host_case_setup_failed` for
construction or verification failure before execution,
`host_case_cleanup_failed` for force-removal, prune, path-removal, or
registration-verification failure, and `source_worktree_drift` when the
authoritative status snapshot changes. These are failures, never prerequisite
blockers or skips. Never retain temp paths, status bytes, generated content, or
raw diffs, and never clean or revert the authoritative checkout.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v \
  tests.test_skill_cases.CodexForwardRunnerContractTests.test_host_cases_use_disposable_worktrees \
  tests.test_skill_cases.CodexForwardRunnerContractTests.test_host_worktree_cleanup_failures_fail_closed
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_skill_cases -v
python3 -m py_compile tests/e2e/codex_skill_forward_tests.py
git diff --check
```

Commit only the runner as `fix(DEV-136): isolate host case worktrees`. Obtain
independent cleanup/security review before running any authenticated case.

## Task 7I: Retry the affected rows and full Codex-only matrix

After independent approval of Tasks 7F through 7H, rerun the five prior failing
baseline/forward boundaries plus `DEV136-FWD-IMPLEMENT-001` into a new temporary
normalized evidence path. Inspect only counts, statuses, hashes, and assertion
names. If all affected rows pass, run the exact 25-case Codex 0.144.5
`gpt-5.6-sol` matrix. Verify the authoritative DEV-136 worktree remains clean
after every run and that no disposable worktree remains registered. Do not run
Claude Code. Any new mismatch returns to recorded RED/GREEN diagnosis; it is
not repaired by weakening a rubric.

## Task 7J: Close partial-setup and bound-cleanup precedence gaps

**Files:**

- Modify: `tests/test_skill_cases.py`
- Modify: `tests/e2e/codex_skill_forward_tests.py`

Independent cleanup/security review of Task 7H reproduced two P1 gaps. A
post-`worktree add` verification failure can swallow remove/prune failures and
leave a stale registration, while persistent bound-executable cleanup failure
during worktree setup is currently masked as `host_case_setup_failed`.

### Step 1: Add cleanup-precedence RED

Add focused synthetic tests that:

- make `worktree add` succeed, fail post-add verification, then fail force
  removal and prune; require `host_case_cleanup_failed`, prove the stale
  registration is observable before test cleanup, and exclude paths,
  registrations, status bytes, and exception details from evidence;
- make worktree setup fail while `_remove_bound_executable_copy` persistently
  refuses both cleanup attempts; require `post_capture_prerequisite_drift` to
  override `host_case_setup_failed`, prove exactly two attempts against the
  captured bound path/root, and prove no process, scorer, or later case runs;
- retain positive controls where partial setup cleanup is fully verified and
  therefore remains `host_case_setup_failed`, and where transient bound cleanup
  succeeds on retry without residue.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v \
  tests.test_skill_cases.CodexForwardRunnerContractTests.test_host_partial_setup_cleanup_failures_take_precedence \
  tests.test_skill_cases.CodexForwardRunnerContractTests.test_host_setup_failure_preserves_bound_cleanup_precedence
git diff --check
```

Expected RED: only the new precedence/residue assertions fail. Commit only the
test file as `test(DEV-136): expose setup cleanup precedence gaps`.

### Step 2: Implement verified partial-setup cleanup

Replace post-add best-effort cleanup with a closed, verified setup-owner path.
After any setup exception, inspect path and worktree registration state. When
partial ownership exists, force-remove, prune, verify path and registration
absence, and compare the authoritative status snapshot. Return only normalized
reasons. Use precedence `host_case_cleanup_failed`, then bound-copy
`post_capture_prerequisite_drift`, then `source_worktree_drift`, then
`host_case_setup_failed`. Do not clean or revert authoritative drift.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v \
  tests.test_skill_cases.CodexForwardRunnerContractTests.test_host_partial_setup_cleanup_failures_take_precedence \
  tests.test_skill_cases.CodexForwardRunnerContractTests.test_host_setup_failure_preserves_bound_cleanup_precedence \
  tests.test_skill_cases.CodexForwardRunnerContractTests.test_host_cases_use_disposable_worktrees \
  tests.test_skill_cases.CodexForwardRunnerContractTests.test_host_worktree_cleanup_failures_fail_closed
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_skill_cases -v
python3 -m py_compile tests/e2e/codex_skill_forward_tests.py
git diff --check
```

Commit only the runner as `fix(DEV-136): close setup cleanup precedence gaps`.
Obtain a fresh independent cleanup/security review before any authenticated
Codex case. A persistent injected cleanup refusal is proven by attempts and
fail-closed normalization; the test owns removal of its deliberately retained
artifacts.

## Task 7K: Bind activated output to the literal 21-line serializer

**Files:**

- Modify: `tests/test_skill_contract.py`
- Modify: `plugins/apple-foundation-models-handoff/skills/design-apple-foundation-models-handoff/SKILL.md`
- Modify: `plugins/apple-foundation-models-handoff/skills/implement-apple-foundation-models-handoff/SKILL.md`
- Modify: `plugins/apple-foundation-models-handoff/skills/review-apple-foundation-models-handoff/SKILL.md`
- Modify: `plugins/apple-foundation-models-handoff/skills/debug-apple-foundation-models-handoff/SKILL.md`
- Modify: `plugins/apple-foundation-models-handoff/skills/validate-apple-foundation-models-handoff/SKILL.md`
- Modify: `tests/e2e/codex_skill_forward_tests.py`

A normalized, non-acceptance Codex diagnostic rejected the preface hypothesis:
the response began with exactly one `text` fence, named the expected skill, and
rendered all required headings in order. It instead pretty-printed the activated
envelope into 52 nonblank lines. `routerInput` expanded across lines and moved
`architectureResult` out of its required fourth position; nested result fields
also expanded. The current template names router fields without showing their
required populated key/value serialization, while “populate every nested field”
permits line expansion despite the adjacent one-line router rule.

### Step 1: Add the literal-serializer RED

In `POSITIVE_RESULT_LINES`, change the router template to this single physical
line:

```text
routerInput = { domain = <domain>, requestedOperation = <requestedOperation>, artifactState = <artifactState>, evidenceState = <evidenceState> }
```

Add two exact `OUTPUT_SERIALIZATION_SENTENCES` requirements owned by `Output
Contract`: every activated response uses exactly the 21 shown nonblank envelope
lines in order with placeholders replaced inline and no added lines; neither
`routerInput` nor any `architectureResult` child may be wrapped, pretty-printed,
or expanded across physical lines. Reuse the existing exact-template,
ownership, and mutation oracles. Do not change the approved DEV-136 fixture,
production scorer, router values, headings, evidence schema, or rubric.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v \
  tests.test_skill_contract.SkillContractTests.test_positive_result_template_is_parseable \
  tests.test_skill_contract.SkillContractTests.test_each_skill_owns_deterministic_response_serialization \
  tests.test_skill_contract.SkillContractMutationTests.test_deterministic_output_and_outer_harness_mutations_are_rejected \
  tests.test_skill_contract.SkillContractMutationTests.test_positive_result_rejects_every_exact_shape_mutation
git diff --check
```

Expected RED: production skills fail only because their router template and two
literal-serializer rules are stale; the synthetic fixture and mutation oracle
remain self-consistent. Commit only `tests/test_skill_contract.py` as
`test(DEV-136): expose expanded result envelopes`.

### Step 2: Correct the five canonical skill contracts

Update each canonical positive template to the exact populated one-line
`routerInput`. Add the two literal-serializer sentences once under its `Output
Contract`, adjacent to the single-fence rule. Replace the ambiguous instruction
to populate nested fields with inline-placeholder language, preserving the rule
that the shape is not replaced with YAML, JSON, or prose. Do not add the
disproved preface-only rule and do not edit generated Codex artifacts directly.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v \
  tests.test_skill_contract.SkillContractTests.test_positive_result_template_is_parseable \
  tests.test_skill_contract.SkillContractTests.test_each_skill_owns_deterministic_response_serialization \
  tests.test_skill_contract.SkillContractMutationTests.test_deterministic_output_and_outer_harness_mutations_are_rejected \
  tests.test_skill_contract.SkillContractMutationTests.test_positive_result_rejects_every_exact_shape_mutation
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_skill_contract -v
git diff --check
```

Commit only the five canonical `SKILL.md` files as
`fix(DEV-136): keep result envelopes on template lines`.

### Step 3: Refresh exact installed-payload identities

Compute SHA-256 for each corrected canonical `SKILL.md` and update only its five
`SKILL_PAYLOAD_SHA256` values in the host runner. This binds discovery to the
corrected bytes and continues to reject stale installed caches.

```bash
shasum -a 256 plugins/apple-foundation-models-handoff/skills/*/SKILL.md
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_skill_cases -v
python3 -m py_compile tests/e2e/codex_skill_forward_tests.py
python3 scripts/sync_generated_artifacts.py --check
git diff --check
```

Commit only `tests/e2e/codex_skill_forward_tests.py` as
`test(DEV-136): bind literal envelope payloads`.

### Step 4: Review the correction before host execution

Use the subagent-driven workflow for an independent specification and contract
review. Require exact tests-only RED provenance, no scorer/fixture/rubric
weakening, no generated-file edits, no new Apple claims, exact five-skill
symmetry, and payload digests matching canonical bytes. Correct findings in
focused commits and rerun all affected offline gates.

### Step 5: Retry affected rows, then the full matrix

From the clean reviewed head, rebuild the approved six-case ordered subset and
run the exact Codex 0.144.5 / `gpt-5.6-sol` host boundary. Retain only normalized
evidence and verify source checkout, captured executable, private output, bound
copy, and disposable worktree cleanup after every case. Require all six rows to
pass before starting the full 25-case matrix. Any new mismatch returns to a
recorded RED/GREEN diagnosis; never weaken the contract or cherry-pick a pass.

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
