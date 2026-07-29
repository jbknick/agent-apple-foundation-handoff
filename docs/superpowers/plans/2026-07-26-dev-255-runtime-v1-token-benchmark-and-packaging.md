# DEV-255 Runtime V1 Token Benchmark and Packaging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove the merged production Runtime V1 reduces actual parent-model usage by at least 10% median across 24 required pairs without correctness regressions, extra turns, reruns, unsafe evidence, or unsupported packaging.

**Architecture:** Keep DEV-142's historical two-host benchmark immutable and add one separate Codex-only `codex-runtime-v1-cost-v1` validator. An authorized outer harness runs identical plugin-off/plugin-on tasks through the merged production plugin, validates the exact Codex `turn.completed.usage` contract, maps it into DEV-142's existing `openai-responses-usage-v1` oracle without double counting subsets, scores correctness and operational invariants, and writes only closed normalized evidence.

**Tech Stack:** Python 3 standard library and `unittest`; merged DEV-254 Codex plugin; Codex CLI `0.145.0`; Swift 6.3.3; macOS SDK 26.5; actual Codex/provider usage; JSON and SHA-256.

**Linear issue:** [DEV-255](https://linear.app/devprentice/issue/DEV-255/v2-prove-runtime-v1-token-reduction-and-packaging-readiness)

**Spec source:** `docs/superpowers/specs/2026-07-26-runtime-v1-successor-linear-backlog-design.md`

**Blocked by:** DEV-254.

---

## Predecessor assumptions and mandatory refresh

DEV-254 is merged at `6d336044b0c21dfeca485b6676a18d50bf085487` and this plan was refreshed against that production manifest, hook, Python adapter, Swift bridge, production harness, DEV-142 corpus, and DEV-142 usage normalization. Before implementation, recheck that this commit remains an ancestor of `HEAD`, DEV-254 is complete in Linear, and the paths below remain unchanged. The benchmark contract is:

```text
one production Codex plugin
one direct Bash command per arm
pluginOff appleAttempts = 0
pluginOn appleAttempts <= 1
no command rerun
exactly two normal parent requests and one completed parent turn per arm
gpt-5.6-sol with medium reasoning
exact Codex 0.145.0 turn.completed.usage fields
closed normalized evidence only
```

The verified Codex `0.145.0` plugin-off dry row used an isolated `CODEX_HOME`,
`gpt-5.6-sol`, medium reasoning, one completed turn, and completed cleanup. Its
terminal event is exactly:

```json
{
  "type": "turn.completed",
  "usage": {
    "input_tokens": 0,
    "cached_input_tokens": 0,
    "cache_write_input_tokens": 0,
    "output_tokens": 0,
    "reasoning_output_tokens": 0
  }
}
```

The zeroes above show types only; live values must be provider-reported
nonnegative integers. Official `rust-v0.145.0` source establishes that
`input_tokens` is the provider input total, cached-input and cache-write input
are subsets of that input total, reasoning output is a subset of output, and
total parent usage is `input_tokens + output_tokens`.

Map the five Codex fields into DEV-142 without changing DEV-142:

```python
dev142_usage = normalize_usage("openai-responses-usage-v1", {
    "input_tokens": usage["input_tokens"],
    "cached_tokens": usage["cached_input_tokens"],
    "output_tokens": usage["output_tokens"],
    "reasoning_tokens": usage["reasoning_output_tokens"],
})
cache_write_input_tokens = usage["cache_write_input_tokens"]
```

Require the exact five usage keys, exact `int` values (not `bool`) in
`0..2**64-1`, `cached_input_tokens <= input_tokens`,
`cache_write_input_tokens <= input_tokens`, and
`reasoning_output_tokens <= output_tokens`. Cache-read and cache-write are each
validated as subsets; do not assume they are disjoint and do not add either to
the provider input total. Do not add reasoning output to output. Record
cache-write separately in normalized arm evidence and require DEV-142's
`total_parent_model_tokens == input_tokens + output_tokens`.

Missing or extra keys, a non-integer/negative/overflowing value, a violated
subset, a mapping mismatch, multiple/missing terminal events, or a changed
event shape stops preflight with
`blocked:provider_usage_schema_or_semantic_drift`. Missing telemetry is a
blocker, never estimated. Any later merged production, Codex schema, or
normalization drift requires another Sol/High plan refresh.

## File structure

- Create `fixtures/runtime-v1-benchmark/README.md` — exact profile, denominators, privacy, blocker, and release rules.
- Create `fixtures/runtime-v1-benchmark/runtime_v1_benchmark.py` — closed Codex-only arm/pair/release validation and derivation.
- Create `tests/test_runtime_v1_benchmark.py` — schema, normalization, arithmetic, correctness, and safety tests.
- Create `tests/e2e/codex_runtime_v1_benchmark.py` — authorized outer 24-pair runner and normalized evidence writer.
- Create `docs/research/evidence/runtime-v1-benchmark.json` — normalized 24-pair/48-arm evidence.
- Create `docs/research/runtime-v1-benchmark.md` — bounded verdict and limitations.
- Modify `docs/runtime-v1-installation.md` — packaging-readiness result only after the live matrix finishes.

The existing `fixtures/dev-142/runtime_contract.py`, corpus, evidence, and two-host validator remain byte-for-byte unchanged.

### Task 1: Refresh the merged production and usage boundaries

**Files:**
- Read: `plugins/apple-foundation-models-handoff/.codex-plugin/plugin.json`
- Read: `plugins/apple-foundation-models-handoff/hooks/codex/hooks.json`
- Read: `plugins/apple-foundation-models-handoff/hooks/codex/diagnostic_condensation.py`
- Read: `plugins/apple-foundation-models-handoff/runtime/DiagnosticCondenser.swift`
- Read: `tests/e2e/codex_runtime_v1_production.py`
- Read: `fixtures/dev-142/runtime_contract.py`
- Read: `fixtures/dev-142/benchmark-corpus.json`
- Modify only if a verified interface changed: `docs/superpowers/plans/2026-07-26-dev-255-runtime-v1-token-benchmark-and-packaging.md`

- [ ] **Step 1: Verify predecessor ancestry and state**

Run:

```bash
git status --short --branch
git merge-base --is-ancestor origin/main HEAD
python3 scripts/sync_generated_artifacts.py --check
```

Expected: clean DEV-255 branch from the merged DEV-254 baseline.

- [ ] **Step 2: Freeze the production and corpus identities**

Run:

```bash
shasum -a 256 \
  plugins/apple-foundation-models-handoff/.codex-plugin/plugin.json \
  plugins/apple-foundation-models-handoff/hooks/codex/hooks.json \
  plugins/apple-foundation-models-handoff/hooks/codex/diagnostic_condensation.py \
  plugins/apple-foundation-models-handoff/runtime/DiagnosticCondenser.swift \
  fixtures/dev-142/benchmark-corpus.json
```

Expected: five lowercase SHA-256 identities recorded in the transient run configuration and normalized evidence.

- [ ] **Step 3: Freeze the reviewed usage boundary**

Confirm the reviewed dry-row facts and official `rust-v0.145.0` semantics
match the frozen five-key contract and four-key DEV-142 mapping above. Do not
run Apple or a benchmark arm during this plan-refresh task. Task 4 repeats the
dry row through the tested benchmark parser before any matrix arm.

Expected: no optional usage field, inferred provider total, or double-counted
subset remains in the plan.

### Task 2: Add the independent Codex-only benchmark contract

**Files:**
- Create: `fixtures/runtime-v1-benchmark/README.md`
- Create: `fixtures/runtime-v1-benchmark/runtime_v1_benchmark.py`
- Create: `tests/test_runtime_v1_benchmark.py`

- [ ] **Step 1: Write the failing contract tests**

Define exact constants:

```python
PROFILE = "codex-runtime-v1-cost-v1"
REQUIRED_PAIRS = 24
REQUIRED_ARMS = 48
MINIMUM_MEDIAN_REDUCTION_PPM = 100_000
```

Test closed objects; duplicate/extra/missing identities; mismatched pair
coordinates; every missing and extra Codex usage key; `bool`, float, string,
negative, and unsigned-64 overflow values; cached-input, cache-write, and
reasoning subset violations; DEV-142 mapping and total mismatch; proof that
cache-write is recorded but not added; missing/multiple terminal events;
missing usage; zero plugin-off denominator; exactly 10%; below 10%;
even-count median; correctness regression; anything other than two parent
requests and one completed turn; Apple attempts; command rerun; blocked pair;
unsafe evidence; cleanup failure; and the 24-pair success case.

Add explicit RED cases proving that 24 arbitrary unique fixture IDs cannot
pass; a real fixture with the wrong rendered SHA-256, command class, or command
form blocks; a missing, extra, duplicate, or substituted DEV-142 corpus
identity blocks; and caller-forged `RuntimeV1PairScore` summaries cannot bypass
arm validation, pair scoring, or release derivation.

- [ ] **Step 2: Run focused tests and verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_runtime_v1_benchmark -v
```

Expected: FAIL because the contract module does not exist.

- [ ] **Step 3: Implement the closed data model**

Import only DEV-142's `normalize_usage`, `BlockedEvidence`, and
`load_closed_json`; do not copy its normalization or change that module. Load
`fixtures/dev-142/benchmark-corpus.json`, require its frozen corpus SHA-256 and
exact 24 IDs, and derive one immutable map:

```text
fixture_id -> { rendered_sha256, command_class, command_form }
```

`validate_arm` requires every fixture ID to exist in that map and requires its
`fixture_sha256`, `command_class`, and `command_form` to equal the mapped
values. Use frozen dataclasses:

```python
@dataclass(frozen=True)
class RuntimeV1Usage:
    input_tokens: int
    cached_input_tokens: int
    cache_write_input_tokens: int
    output_tokens: int
    reasoning_output_tokens: int
    total_parent_tokens: int

@dataclass(frozen=True)
class RuntimeV1Arm:
    fixture_id: str
    fixture_sha256: str
    arm: str
    codex_version: str
    parent_model: str
    reasoning_effort: str
    provider: str
    provider_normalization: str
    policy_version: str
    command_class: str
    command_form: str
    task_prompt_sha256: str
    usage: RuntimeV1Usage
    parent_requests: int
    completed_parent_turns: int
    apple_attempts: int
    validated_applied: bool
    command_executions: int
    correctness_passed: bool
    cleanup_complete: bool

@dataclass(frozen=True)
class RuntimeV1ArmPair:
    plugin_off: RuntimeV1Arm
    plugin_on: RuntimeV1Arm

@dataclass(frozen=True)
class RuntimeV1PairScore:
    fixture_id: str
    reduction_ppm: int | None
    status: str
    reason_codes: tuple[str, ...]
    correctness_regressions: int
    additional_parent_requests: int
    additional_parent_turns: int
    apple_attempts: int
    validated_applied_rows: int
    command_reruns: int
    cleanup_failures: int
```

Expose exactly these interfaces:

```text
normalize_codex_usage(value: object) -> RuntimeV1Usage
validate_arm(value: object) -> RuntimeV1Arm
validate_arm_pair(value: object) -> RuntimeV1ArmPair
score_pair(off: object, on: object) -> RuntimeV1PairScore
release_gate(
    arm_pairs: list[object],
    *,
    unsafe_committed_evidence_findings: int,
) -> dict[str, object]
validate_evidence(value: object) -> None
```

The raw arm-pair input is a closed object with exactly
`plugin_off` and `plugin_on`; `validate_arm_pair` validates both nested raw arm
objects, exact roles, identical coordinates, and the wrapper's one immutable
DEV-142 corpus identity. `RuntimeV1PairScore` is derived output only and is
never accepted as release authority.

`normalize_codex_usage` first validates the exact five-key Codex object, then
calls DEV-142's `normalize_usage` with the exact four-key mapping above and
checks the returned fields and total. Do not call or modify DEV-142's 48-pair
`release_gate`; the successor release arithmetic is owned here.

- [ ] **Step 4: Implement the release gate**

`release_gate` first requires exactly one validated arm pair for every exact
DEV-142 corpus ID and no other identity. It calls `score_pair` itself for all
24 pairs and aggregates only those freshly derived scores; it rejects
`RuntimeV1PairScore` inputs and never trusts a caller-provided reduction,
counter, status, or reason. The release gate returns `pass` only when:

```python
len(derived_pairs) == 24
set(pair.fixture_id for pair in derived_pairs) == set(EXACT_DEV142_FIXTURE_IDS)
all(pair.status == "pass" for pair in derived_pairs)
median_reduction_ppm >= 100_000
correctness_regressions == 0
additional_parent_requests == 0
additional_parent_turns == 0
real_apple_attempts >= 1
validated_applied_rows >= 1
original_command_reruns == 0
cleanup_failures == 0
unsafe_committed_evidence_findings == 0
```

Each valid arm has `parent_requests == 2`,
`completed_parent_turns == 1`, and `command_executions == 1`. Sort the 24
integer reductions and define the median as the integer floor-average of
zero-based positions 11 and 12. Any missing required pair, blocked required
pair, zero denominator, unavailable normalization, schema/semantic drift, or
incomplete cleanup returns `blocked`; invariant and correctness violations
return `fail`.

`validate_evidence` validates the closed evidence shape, groups its 48 raw
arms into the same 24 closed arm-pair inputs, calls `release_gate`, and requires
the stored pair summaries, release object, counts, status, and reason codes to
equal the freshly derived values exactly. Evidence validation cannot accept a
stored pair or release summary as proof of its own derivation.

- [ ] **Step 5: Run GREEN and commit**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_runtime_v1_benchmark \
  tests.test_dev_142_contract -v
git diff --check
git add fixtures/runtime-v1-benchmark tests/test_runtime_v1_benchmark.py
git commit -m "test(DEV-255): define Runtime V1 benchmark contract"
```

Expected: focused tests PASS and DEV-142 remains unchanged.

### Task 3: Build the authorized outer paired runner

**Files:**
- Create: `tests/e2e/codex_runtime_v1_benchmark.py`

- [ ] **Step 1: Write failing runner tests**

Test exact executable capture/recheck; clean candidate-commit capture/recheck;
production-commit ancestry; immutable pair coordinates; deterministic fixture
order; plugin-off isolation; plugin-on install/trust; one command; zero added
turns; actual usage extraction; Apple-attempt counting; correctness scoring;
monotonic latency; transient raw-data cleanup; atomic normalized writes;
resume rejection; and fail-closed cancellation.

- [ ] **Step 2: Run runner tests and verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_runtime_v1_benchmark.RuntimeV1RunnerTests -v
```

Expected: FAIL because the runner does not exist.

- [ ] **Step 3: Implement fixed pair coordinates**

For each DEV-142 corpus case, bind:

```python
{
    "benchmarkProfile": "codex-runtime-v1-cost-v1",
    "fixtureID": case["id"],
    "fixtureSha256": case["renderedSha256"],
    "parentModel": exact_parent_model,
    "reasoningEffort": exact_reasoning_effort,
    "provider": "openai-responses-usage-v1",
    "codexVersion": "0.145.0",
    "policyVersion": "diagnostic-condensation-v1",
    "commandClass": case["commandClass"],
    "commandForm": case["commandForm"],
    "taskPromptSha256": task_prompt_sha256,
}
```

Also bind the candidate commit, production plugin tree SHA-256, generated
Codex manifest SHA-256, hooks manifest SHA-256, Python adapter SHA-256, Swift
source SHA-256, corpus SHA-256, and exact captured executable identity to the
run. Pair coordinates are the fields in the object above and must be identical
between arms; arm role and plugin installation state are the only intentional
differences. Reject drift before scoring.

- [ ] **Step 4: Implement one arm runner**

Each arm must:

1. Create a fresh isolated root.
2. Capture and recheck the exact Codex executable.
3. Give both roles identical CLI/model/reasoning/config/task coordinates.
   Leave `pluginOff` in a fresh plugin-empty `CODEX_HOME`; install and trust the
   exact production plugin only for `pluginOn`.
4. Invoke the captured executable once with an argument list equivalent to:

   ```text
   <host-path> exec --ephemeral --json --strict-config
     --skip-git-repo-check --enable hooks
     --disable code_mode --disable code_mode_only
     -c web_search="disabled" -c approval_policy="never"
     -c model_reasoning_effort="medium"
     -m gpt-5.6-sol -s danger-full-access
     --output-last-message <transient-output>
     -C <isolated-workspace> <approved-hash-bound-task>
   ```

   Construct this as a subprocess argument list, never a shell string. The
   task instructs Codex to run the case's approved direct Bash command exactly
   once and to make no other tool call.
5. Count exactly two provider requests through the authorized outer request
   counter used by the dry protocol, without retaining request bodies. Parse
   transient JSONL as one closed stream: `thread.started`, one
   `turn.started`, bounded item events, and exactly one terminal
   `turn.completed`; reject `turn.failed`, top-level error, trailing records,
   open items, or a second terminal. If the supported request counter is
   unavailable, block rather than infer the count. Require exactly one command
   execution, exactly two normal parent requests, and one completed parent
   turn.
6. Validate the exact five-key terminal usage and map it through DEV-142.
7. For `pluginOff`, require zero Apple attempts and no loaded/trusted plugin.
   For `pluginOn`, require at most one Apple attempt, no retry, and exactly one
   terminal applied or untouched-original fallback outcome. Apple-only
   generation is the only extra generation relative to `pluginOff`.
8. Score the parent outcome against the immutable DEV-142 oracle and its
   paired baseline.
9. Record monotonic Apple, hook, and parent-turn latency with explicit
   numerators and denominators.
10. Recheck executable, plugin/tree identities, manifest/hook trust, and
    toolchain identity.
11. Delete provider bodies, JSONL, diagnostics, Apple output, transcripts,
    compiled binaries, isolated configuration, and credentials.
12. Return only the closed normalized arm after proving the isolated root no
    longer exists.

No arm retries. Interruption or uncertain completion blocks its required pair.

- [ ] **Step 5: Implement atomic evidence output**

Write exactly one closed top-level object:

```text
schemaVersion, benchmarkProfile, status, reasonCodes,
candidateCommit, productionIdentities, host,
usageContract, requiredPairs, requiredArms,
observedPairs, observedArms, arms, pairs, release
```

`usageContract` contains exact Codex version/model/reasoning, event name, the
five raw key names, the four-key DEV-142 mapping, subset semantics, and
`totalFormula = input_tokens + output_tokens`. Each arm contains only the
closed `RuntimeV1Arm` fields above plus normalized latency counts. `release`
contains exact denominators, median reduction PPM, correctness regressions,
additional parent requests, additional parent turns, real Apple attempts,
validated applied rows, command reruns, unsafe findings, cleanup failures,
status, and reason codes.

Reject private absolute paths, credential forms, prompt/result/transcript
keys, original fixture text, raw JSONL/events, provider or Apple bodies,
reasoning, and malformed hashes before calling the existing atomic JSON
writer. A cleanup failure may write only a minimal normalized
`blocked:cleanup_incomplete` terminal record.

- [ ] **Step 6: Run deterministic GREEN and commit**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_runtime_v1_benchmark -v
git diff --check
git add tests/e2e/codex_runtime_v1_benchmark.py
git commit -m "test(DEV-255): add paired Runtime V1 benchmark runner"
```

Expected: deterministic runner tests PASS; no live pair runs inside the implementation session.

### Task 4: Execute 24 pairs and publish normalized evidence

**Files:**
- Create: `docs/research/evidence/runtime-v1-benchmark.json`
- Create: `docs/research/runtime-v1-benchmark.md`
- Modify: `docs/runtime-v1-installation.md`

- [ ] **Step 1: Preflight the complete run**

From an authorized outer Codex session, capture the exact Codex, Python,
`xcrun`, and Swift compiler executables; require Codex `0.145.0`,
`gpt-5.6-sol`, medium reasoning, authentication, plugin trust, SDK 26.5, Apple
availability, locale, the dry-row usage mapping, corpus and production
identities, and free temporary storage. Any missing prerequisite writes a
normalized blocker and stops before an Apple attempt or benchmark arm.

After Task 3 is committed, require a clean worktree and capture its exact
40-character lowercase `HEAD` as `approved_candidate_commit`. Prove
`6d336044b0c21dfeca485b6676a18d50bf085487` is an ancestor of that candidate,
pass both identities separately, and recheck `HEAD` equality before and after
every dry or live row. The dry row must finish clean. The complete run may
create only its authorized normalized output path; any other worktree change
is drift. The production commit identifies merged Runtime V1; the candidate
commit identifies the exact harness and contract under test. Missing ancestry
is `blocked:production_commit_not_contained`; candidate or unexpected worktree
drift is `fail:candidate_identity_drift`.

Run the tested harness once through the plugin-off usage preflight:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 \
  tests/e2e/codex_runtime_v1_benchmark.py \
  --codex-executable <host-path> \
  --python-executable <host-path> \
  --approved-production-commit 6d336044b0c21dfeca485b6676a18d50bf085487 \
  --approved-candidate-commit <current-clean-task3-head> \
  --approved-plugin-sha256 <64-lowercase-hex> \
  --approved-hook-hash sha256:<64-lowercase-hex> \
  --through usage-dry-run
```

Require exactly one `turn.completed` event with the exact five-key usage
object, exactly two normal parent requests, one completed parent turn, no
Apple attempt, no retry, and completed cleanup. The harness may print only a
normalized terminal record and must delete raw JSONL and the isolated root.
Any mismatch stops before the matrix with
`blocked:provider_usage_schema_or_semantic_drift`.

- [ ] **Step 2: Run all required arms**

After the dry row passes, run the harness once with the exact captured
executables and approved hashes:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 \
  tests/e2e/codex_runtime_v1_benchmark.py \
  --codex-executable <host-path> \
  --python-executable <host-path> \
  --approved-production-commit 6d336044b0c21dfeca485b6676a18d50bf085487 \
  --approved-candidate-commit <current-clean-task3-head> \
  --approved-plugin-sha256 <64-lowercase-hex> \
  --approved-hook-hash sha256:<64-lowercase-hex> \
  --through complete \
  --output docs/research/evidence/runtime-v1-benchmark.json
```

The runner must reject placeholders; they identify values captured and
approved immediately before execution. Expected normalized denominators:

```text
requiredPairs = 24
requiredArms = 48
observedPairs = 24
observedArms = 48
```

Do not drop, repeat, replace, impute, or zero a row.

- [ ] **Step 3: Validate the release arithmetic**

Run:

```bash
python3 -m json.tool \
  docs/research/evidence/runtime-v1-benchmark.json >/dev/null
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_runtime_v1_benchmark -v
PYTHONDONTWRITEBYTECODE=1 python3 \
  tests/e2e/codex_runtime_v1_benchmark.py \
  --validate-evidence docs/research/evidence/runtime-v1-benchmark.json
```

Expected: the evidence validates as exactly one `pass`, `blocked`, or `fail` verdict. Report the verdict truthfully.

- [ ] **Step 4: Write bounded interpretation and packaging result**

Record the evidence SHA-256, exact five-key usage contract and DEV-142
mapping, cache-write non-double-count rule, exact denominators, median
reduction, correctness regressions, added requests/turns, Apple attempts,
applied rows, reruns, safety findings, latency denominators, cleanup,
packaging/install result, proven claims, unproven claims, and stop/release
decision. Quote no provider, tool, or Apple content.

- [ ] **Step 5: Commit evidence**

Run:

```bash
git add \
  docs/research/evidence/runtime-v1-benchmark.json \
  docs/research/runtime-v1-benchmark.md \
  docs/runtime-v1-installation.md
git commit -m "test(DEV-255): record Runtime V1 benchmark verdict"
```

### Task 5: Run final regression and release review

**Files:**
- Verify all DEV-255 paths above.

- [ ] **Step 1: Run repository gates**

Run:

```bash
python3 scripts/sync_generated_artifacts.py --check
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests -p 'test_*.py' -v
git diff --check
git status --short
```

Expected: generator synchronized, full suite PASS except declared pre-existing skips, no diff errors, and only DEV-255 paths changed.

- [ ] **Step 2: Run Sol/High release review**

Review all 24 identities and 48 arms; exact five-key usage validation;
four-key DEV-142 mapping; independent cache-read, cache-write, and reasoning
subset checks; no subset double counting; total and median arithmetic;
correctness; exactly two requests and one completed turn per arm; Apple
attempts and no retry; reruns; latency denominators; evidence safety; cleanup;
production identity and packaging/install proof; DEV-142 byte immutability;
CI; and merge readiness. Resolve every actionable finding and rerun Step 1.

- [ ] **Step 3: Finish the issue**

Open one DEV-255 PR, wait for green CI, merge, verify remote containment and a clean synchronized worktree, then mark DEV-255 complete only when the normalized verdict satisfies the approved release gate. A `blocked` or `fail` verdict closes the run truthfully without a release claim.
