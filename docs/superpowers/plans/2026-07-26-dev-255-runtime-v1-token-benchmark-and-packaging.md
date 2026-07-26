# DEV-255 Runtime V1 Token Benchmark and Packaging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove the merged production Runtime V1 reduces actual parent-model usage by at least 10% median across 24 required pairs without correctness regressions, extra turns, reruns, unsafe evidence, or unsupported packaging.

**Architecture:** Keep DEV-142's historical two-host benchmark immutable and add one separate Codex-only `codex-runtime-v1-cost-v1` validator. An authorized outer harness runs identical plugin-off/plugin-on tasks through the merged production plugin, normalizes actual supported usage, scores correctness and operational invariants, and writes only closed normalized evidence.

**Tech Stack:** Python 3 standard library and `unittest`; merged DEV-254 Codex plugin; Codex CLI `0.145.0`; Swift 6.3.3; macOS SDK 26.5; actual Codex/provider usage; JSON and SHA-256.

**Linear issue:** [DEV-255](https://linear.app/devprentice/issue/DEV-255/v2-prove-runtime-v1-token-reduction-and-packaging-readiness)

**Spec source:** `docs/superpowers/specs/2026-07-26-runtime-v1-successor-linear-backlog-design.md`

**Blocked by:** DEV-254.

---

## Predecessor assumptions and mandatory refresh

Do not implement this plan until DEV-254 is merged, green, complete in Linear, and locally synchronized. Refresh this plan against the merged production manifest, hook path, adapter interface, Swift staging method, supported host, and usage-event schema. The intended benchmark assumes:

```text
one production Codex plugin
one direct Bash command per arm
pluginOff appleAttempts = 0
pluginOn appleAttempts <= 1
no command rerun
no additional parent-model turn
actual supported usage fields
closed normalized evidence only
```

If the merged production interface, Codex usage schema, or provider normalization differs, stop and request a Sol/High plan refresh. Missing telemetry is a blocker, not a reason to estimate.

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
- Read: `tests/e2e/codex_runtime_v1_production.py`
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

- [ ] **Step 3: Prove the actual usage boundary**

Run one plugin-off dry protocol row from an authorized outer Codex session and require the supported completed-turn event to contain nonnegative integer input, cached-input when exposed, output, reasoning-output when exposed, and total usage fields. If total parent usage cannot be mapped exactly to `openai-responses-usage-v1`, stop with `blocked:provider_usage_normalization_unavailable`.

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

Test closed objects, duplicate/extra/missing identities, mismatched pair coordinates, missing usage, zero plugin-off denominator, negative/non-integer usage, exactly 10%, below 10%, even-count median, correctness regression, extra parent turn, Apple attempts, command rerun, blocked pair, unsafe evidence, and the 24-pair success case.

- [ ] **Step 2: Run focused tests and verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_runtime_v1_benchmark -v
```

Expected: FAIL because the contract module does not exist.

- [ ] **Step 3: Implement the closed data model**

Use frozen dataclasses:

```python
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
    total_parent_tokens: int
    parent_turns: int
    apple_attempts: int
    command_executions: int
    correctness_passed: bool
    cleanup_complete: bool

@dataclass(frozen=True)
class RuntimeV1PairScore:
    fixture_id: str
    reduction_ppm: int
    status: str
    reason: str
```

Expose exactly these interfaces:

```text
validate_arm(value: object) -> RuntimeV1Arm
score_pair(off: object, on: object) -> RuntimeV1PairScore
release_gate(pairs: list[RuntimeV1PairScore]) -> dict[str, object]
validate_evidence(value: object) -> None
```

Reuse DEV-142's exact `normalize_usage` semantics by importing it read-only. Do not call or modify DEV-142's 48-pair `release_gate`; the successor release arithmetic is owned here.

- [ ] **Step 4: Implement the release gate**

The release gate returns `pass` only when:

```python
len(pairs) == 24
all(pair.status == "pass" for pair in pairs)
median_reduction_ppm >= 100_000
correctness_regressions == 0
additional_parent_turns == 0
real_apple_attempts >= 1
validated_applied_rows >= 1
original_command_reruns == 0
unsafe_committed_evidence_findings == 0
```

Sort the 24 integer reductions and define the median as the integer average of positions 11 and 12. Any missing required pair, blocked required pair, zero denominator, or unavailable normalization returns `blocked`; invariant and correctness violations return `fail`.

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

Test exact executable capture/recheck; immutable pair coordinates; deterministic fixture order; plugin-off isolation; plugin-on install/trust; one command; zero added turns; actual usage extraction; Apple-attempt counting; correctness scoring; monotonic latency; transient raw-data cleanup; atomic normalized writes; resume rejection; and fail-closed cancellation.

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
    "fixtureSha256": case_sha256,
    "parentModel": exact_parent_model,
    "reasoningEffort": exact_reasoning_effort,
    "provider": "openai-responses-usage-v1",
    "codexVersion": "0.145.0",
    "policyVersion": "diagnostic-condensation-v1",
    "commandClass": case["commandClass"],
    "taskPromptSha256": task_prompt_sha256,
}
```

Reject drift between arms before scoring.

- [ ] **Step 4: Implement one arm runner**

Each arm must:

1. Create a fresh isolated root.
2. Capture and recheck the exact Codex executable.
3. Install/trust the exact production plugin only for `pluginOn`.
4. Run the case's approved direct command once.
5. Capture actual completed-turn usage and counts transiently.
6. Score the parent outcome against DEV-142 and the paired baseline.
7. Record monotonic Apple, hook, and parent-turn latency with denominators.
8. Delete provider bodies, diagnostics, Apple output, transcripts, compiled binaries, and isolated configuration.
9. Return only the closed normalized arm.

No arm retries. Interruption or uncertain completion blocks its required pair.

- [ ] **Step 5: Implement atomic evidence output**

Reject private absolute paths, credential forms, prompt/result/transcript keys, original fixture text, and malformed hashes before calling the existing atomic JSON writer. A cleanup failure may write only `blocked:cleanup_incomplete`.

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

From an authorized outer Codex session, capture the exact Codex, Python, `xcrun`, and Swift compiler executables; verify authentication, plugin trust, SDK 26.5, Apple availability, locale, actual usage mapping, corpus hash, production plugin hash, and free temporary storage. Any missing prerequisite writes a normalized blocker and stops.

- [ ] **Step 2: Run all required arms**

Run the harness once with `--through complete`. Expected normalized denominators:

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
```

Expected: the evidence validates as exactly one `pass`, `blocked`, or `fail` verdict. Report the verdict truthfully.

- [ ] **Step 4: Write bounded interpretation and packaging result**

Record the evidence SHA-256, exact denominators, median reduction, correctness regressions, added turns, Apple attempts, applied rows, reruns, safety findings, latency denominators, cleanup, packaging/install result, proven claims, unproven claims, and stop/release decision. Quote no provider, tool, or Apple content.

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

Review all 24 identities and 48 arms; actual usage normalization; median arithmetic; correctness; turns; Apple attempts; reruns; latency denominators; evidence safety; cleanup; packaging/install proof; DEV-142 immutability; CI; and merge readiness. Resolve every actionable finding and rerun Step 1.

- [ ] **Step 3: Finish the issue**

Open one DEV-255 PR, wait for green CI, merge, verify remote containment and a clean synchronized worktree, then mark DEV-255 complete only when the normalized verdict satisfies the approved release gate. A `blocked` or `fail` verdict closes the run truthfully without a release claim.
