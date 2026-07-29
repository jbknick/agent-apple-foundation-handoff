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

## 2026-07-29 Task 3 observation-boundary amendment

Formal review confirmed that the production adapter already derives closed
`consultation_completed` and `replacement_emitted` events, but its executable
path passes `observe=lambda _value: None`. The current Task 3 runner therefore
cannot truthfully derive `appleAttempts`, a replacement-prepared application
fact, or Apple/hook latency and correctly stops with
`blocked:apple_attempt_counter_unobservable`. Task 3 is incomplete until that
production observation prerequisite and the remaining outer-runner gaps below
are closed; no counter may be inferred from plugin installation, hook trust,
process completion, replacement text, or model output.

Standing DEV-255 approval authorizes Task 3 implementation changes only in
these four paths:

```text
plugins/apple-foundation-models-handoff/hooks/codex/diagnostic_condensation.py
tests/test_runtime_v1_production.py
tests/e2e/codex_runtime_v1_benchmark.py
tests/test_codex_runtime_v1_benchmark.py
```

It also authorizes mechanically refreshing the exact
`productionPluginSha256` and `pythonAdapterSha256` values bound in the runner
and tests after those reviewed bytes change. The Codex manifest, hook manifest,
Swift source, generated runtime contract, DEV-142 fixtures/contracts/evidence,
and every other production path remain unchanged. This approval does not
authorize a live Codex or Apple run, evidence publication, commit, push, merge,
tag, release, or a second Apple attempt.

The Sol/High decision for the remaining effect-proof boundary is to accept
rigorous non-body triangulation. A direct live second-request body hash is not
required and must not be captured: Codex `0.145.0` preserves the original
`PostToolUseFeedbackOutput` in JSONL and `log_preview`, applies the hook
replacement only through `to_response_item`, and intentionally excludes bodies
from the authorized OTel request counter. The model-authored last message is
also not effect authority. Instead, the outer runner may derive
`validated_applied = true` only from all of these independently owned facts:

```text
application observation status = replacement_emitted
application observation appleAttempts = 1
application observation appleValidResults = 1
current-candidate Codex 0.145.0 local-provider forwarding preflight = pass
live OTel normal parent requests = 2
live JSONL completed parent turns = 1
live JSONL command executions = 1
live final parent outcome DEV-142 score = pass
```

The current-candidate preflight must use the captured Codex `0.145.0`
executable and exact installed production bytes. With only synthetic transient
content, its local provider records that the current adapter's exact stdout
replacement SHA-256 is the only `function_call_output` in request two, the
original tool-result bytes are absent from the whole second request, and
exactly two `/responses` requests and one completed turn occur. It deletes both
request bodies before returning a closed
normalized pass/block result. Existing DEV-253 production-mechanism evidence is
a predecessor check, not a substitute for this current-byte proof. Any Codex
source, executable, candidate, plugin-tree, hook, adapter, or forwarding-preflight
identity drift blocks every applied row.

This is intentionally a composite application proof, not a claim that OTel
observed a provider body. For the configured benchmark path only, the adapter
must serialize the already validated closed hook response once, write all of
those exact bytes to stdout, flush successfully, and only then durably write
the terminal `replacement_emitted` receipt containing the same SHA-256 and byte
count. No fallible mutation or recheck may occur after that receipt. A receipt
failure cannot roll back the already emitted consultation and must not be
reported as a consultation decline or fallback; it blocks measurement and
evidence for the arm. A stdout, receipt, request-count, turn, cleanup, or
parent-outcome failure therefore prevents the outer arm from deriving
`validated_applied`.

## File structure

- Create `fixtures/runtime-v1-benchmark/README.md` — exact profile, denominators, privacy, blocker, and release rules.
- Create `fixtures/runtime-v1-benchmark/runtime_v1_benchmark.py` — closed Codex-only arm/pair/release validation and derivation.
- Create `tests/test_runtime_v1_benchmark.py` — schema, normalization, arithmetic, correctness, and safety tests.
- Modify `plugins/apple-foundation-models-handoff/hooks/codex/diagnostic_condensation.py` — optional production-safe normalized Task 3 observation sink; absent by default.
- Modify `tests/test_runtime_v1_production.py` — observation containment, schema, fallback, and single-attempt regression coverage.
- Create `tests/e2e/codex_runtime_v1_benchmark.py` — authorized outer 24-pair runner and normalized evidence writer.
- Create `tests/test_codex_runtime_v1_benchmark.py` — deterministic outer-runner and observation-consumer tests.
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
- Modify: `plugins/apple-foundation-models-handoff/hooks/codex/diagnostic_condensation.py`
- Modify: `tests/test_runtime_v1_production.py`
- Create: `tests/e2e/codex_runtime_v1_benchmark.py`
- Create: `tests/test_codex_runtime_v1_benchmark.py`

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
  tests.test_codex_runtime_v1_benchmark.RuntimeV1RunnerTests -v
```

Expected: FAIL because the runner does not exist.

- [ ] **Step 3: Add the optional normalized production observation boundary**

Keep the installed production default byte-for-byte equivalent in behavior:
when `RUNTIME_V1_BENCHMARK_OBSERVATION_PATH` is absent, select the existing
no-op observer, create no file, expose no new capability, and preserve every
current fallback. Only the authorized outer Task 3 runner may set the variable,
and only for `pluginOn`.

Use a regular file, not a FIFO: a FIFO can block the hook and weaken
original-result fallback. Before evaluation, require the value to be one
absolute path with the fixed basename `runtime-v1-observation.json` in an
already-created `.runtime-v1-observation` directory directly beneath the
captured `RUNTIME_V1_REPO_ROOT`. Capture that directory as a non-symlink
directory, require the leaf not to exist, and recheck the repository and
directory identities before open and after close. Open once with
`O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW | O_CLOEXEC` and mode `0o600`; require
a regular single-link file, write exactly one complete canonical UTF-8 JSON
line through the captured descriptor, `fsync`, close, and recheck. Reject
relative, outside-root, pre-existing, symlinked, multiply linked, changed-parent,
duplicate-write, partial-write, or identity-drift cases.

The one line is a closed tagged union with exactly these fields:

```text
schemaVersion = 1
event = "runtime_v1_observation"
status = "replacement_emitted" | "fallback" | "blocked"
reasonCode = null | "apple_attempt_count_uncertain" |
             "observation_invariant_failed"
appleAttempts = 0 | 1 | null
appleValidResults = 0 | 1
replacementEmitted = true | false
replacementSha256 = <64-lowercase-hex> | null
replacementBytes = <nonnegative int> | null
preReceiptHookLatencyNanoseconds = <nonnegative int>
appleLatencyNanoseconds = <nonnegative int> | null
appleLatencySamples = 0 | 1
```

Wrap the existing one-shot bridge call with `time.monotonic_ns()` and reduce
only the adapter-owned closed events into this record.
`replacement_emitted` requires `replacementEmitted = true`, one known Apple
attempt, one valid result, one Apple latency sample, and the exact replacement
hash/byte count successfully written and flushed to stdout before the receipt.
It does not claim provider receipt. A known untouched-original path is
`fallback` with `replacementEmitted = false` and
no replacement fields. A blocked record also has
`replacementEmitted = false`. If bridge completion or the attempt count is
uncertain, emit only the normalized `blocked` variant with null attempt and
Apple-latency values. Do not include or retain the observation path, prompt,
response, original output, replacement body, diagnostics, source facts,
provider data, Apple output, credentials, or reasoning.

Any configured observation capture, reduction, open, write, close, or recheck
failure before stdout must suppress the replacement and preserve the exact
original result. It must not call the bridge again, retry Apple generation, or
convert a fallback into an emitted result. For an applied benchmark response,
complete all identity rechecks first, serialize once, require a full stdout
write and successful flush, and then write the terminal receipt as the final
fallible operation. If that post-stdout receipt fails, emit no substitute
observation and let the outer runner block the arm; do not label the already
emitted response as fallback.
The outer runner treats a missing, malformed, blocked, inconsistent, or
duplicate observation as a blocked arm and deletes the observation file and
directory during mandatory cleanup.

`preReceiptHookLatencyNanoseconds` is the monotonic interval from immediately
before evaluation through the successful stdout flush and immediately before
the terminal receipt write. It deliberately excludes the receipt's own durable
write and process-exit time and must never be labelled total hook latency.

Add production RED/GREEN tests for: default-variable absence; exact
replacement-emitted, fallback, and blocked records; all tagged-union
invariants; monotonic
denominators; relative/outside/pre-existing/symlink/hard-link/parent-drift
rejection; `O_EXCL`/`O_NOFOLLOW`/mode `0o600`; short-write and recheck failure;
no sensitive or path-bearing content; exact original preservation on every
pre-stdout observation failure; stdout short-write/flush failure suppressing
the receipt; post-stdout receipt failure blocking measurement without a false
fallback; and proof that the bridge remains one-shot. Tests must also prove the runner
never accepts an observation-owned `validatedApplied` field and never derives
the arm's `validated_applied` from the observation alone.

- [ ] **Step 4: Implement fixed pair coordinates**

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

The hash-bound task prompt contains the approved direct command and the fixed
parent-outcome schema only. It must not contain the fixture ID, fixture hash,
expected facts, expected diagnostics, expected answer, oracle values, or
rendered-case hash. It instructs the parent to execute the command exactly once,
make no other tool call, and serialize only facts derived from the observed
tool result into this exact closed object:

```text
commandOutcome, summary, summaryFacts, diagnostics, warningCount,
omittedWarningCount, nextAction, completionFacts
```

Those are exactly DEV-142's condensation fields. The prompt must not ask the
parent to repeat a known answer or copy a fixture identifier.

- [ ] **Step 5: Implement one arm runner**

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
5. Count exactly two `/responses` provider requests through the authorized
   outer request counter used by the dry protocol, without retaining request
   bodies. Every `codex.api_request` record must contain exactly one closed
   `event.name` and one closed `endpoint`; count only
   `endpoint = "/responses"` and reject malformed, duplicated, or missing
   discriminator attributes. Other well-formed endpoints such as `/models`
   are not parent turns. Parse transient JSONL as one closed stream:
   `thread.started`, one
   `turn.started`, bounded item events, and exactly one terminal
   `turn.completed`; reject `turn.failed`, top-level error, trailing records,
   open items, or a second terminal. If the supported request counter is
   unavailable, block rather than infer the count. Require exactly one command
   execution, exactly two normal `/responses` parent requests, and one
   completed parent turn.
6. Validate the exact five-key terminal usage and map it through DEV-142.
7. For `pluginOff`, require zero Apple attempts and no loaded/trusted plugin.
   For `pluginOn`, require at most one Apple attempt, no retry, and exactly one
   replacement-emitted or untouched-original fallback observation. Apple-only
   generation is the only extra generation relative to `pluginOff`. Set the
   optional observation path only for `pluginOn`; validate its exact one-line
   closed union, cross-check it against the arm role, and then delete it. Never
   read `validated_applied` from this record.
8. Parse `--output-last-message` with duplicate-key rejection as exactly the
   eight-field parent-outcome object above. Require it to equal the text of the
   final completion-only `agent_message`, reject a wrapper, prose, Markdown,
   extra or missing keys, invalid DEV-142 field shape, non-JSON trailing
   content, or an output larger than DEV-142's bound. Accept semantically valid
   JSON regardless of member order or insignificant JSON whitespace; after the
   duplicate-safe parse, canonicalize the closed object application-side for
   hashing and scoring. While the exact input and canonical bytes remain
   transient, bind the canonical SHA-256 to the candidate commit, pair coordinate,
   `taskPromptSha256`, case `renderedSha256`, and immutable DEV-142 oracle;
   construct the fixed applied DEV-142 scoring envelope, call
   `validate_result` and `score_condensation`, and derive
   `correctness_passed` only from `QualityScore.passed` with no reason codes.
   No caller-provided correctness flag is accepted. Score both arms
   independently against the same case, then delete the final-message bytes.
9. Record monotonic Apple, pre-receipt hook, and parent-turn latency with
   explicit numerators and denominators. Never report the pre-receipt interval
   as full hook latency.
10. Recheck executable, plugin/tree identities, manifest/hook trust, and
    toolchain identity.
11. Delete provider bodies, JSONL, diagnostics, Apple output, transcripts,
    compiled binaries, isolated configuration, and credentials.
12. Return only the closed normalized arm after proving the isolated root no
    longer exists.

No arm retries. Interruption or uncertain completion blocks its required pair.

The JSONL parser must implement the exact supported Codex `0.145.0` lifecycle
from official commit `25af12f7`. Accept only exact closed top-level shapes:
`thread.started` first, then one `turn.started`, bounded item records, and one
final `turn.completed`. Within this benchmark, accept only
`command_execution`, nonempty `reasoning`, and `agent_message` items. Every
item ID must match `item_[0-9]+` and be unique on first introduction.

`command_execution` is the only matched lifecycle: require exactly one
`item.started` with the exact closed command item shape and
`status = "in_progress"`, followed by exactly one `item.completed` with the
same ID, type, and command, exact completed command fields, terminal status,
aggregated output, and exit code. Reject completion before start, a changed
ID/type/command, duplicate start or completion, reuse, or an open command.
Both records contain exactly
`id, type, command, aggregated_output, exit_code, status`; the start has empty
aggregated output and null exit code, and the completion has status
`completed | failed | declined` with an integer or null exit code consistent
with the emitted terminal shape.

`agent_message` and nonempty `reasoning` are completion-only. Accept each only
as an exact closed `item.completed` whose item contains exactly
`id, type, text`, with its own new synthetic ID and nonempty text; reject any
`item.started` for either type, empty reasoning, duplicate or reused IDs, or
extra item fields. Require at least one completed
`agent_message`; the final item before `turn.completed` must be the completed
agent message whose text exactly equals `--output-last-message`. Reject
`item.updated`, unsupported item types or events, extra keys at any depth,
out-of-order records, records after terminal, and multiple terminals. Add
positive tests for official completion-only agent/reasoning records and
negative tests for every rejected case above. A merely parseable or
count-equivalent stream is not closed proof.

- [ ] **Step 6: Implement atomic evidence output**

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

For `--through complete`, accept only the exact normalized output path
`docs/research/evidence/runtime-v1-benchmark.json`, require its existing
repository-contained parent identity, reject symlinks and pre-existing output,
and never create arbitrary parents. Candidate rechecks must allow exactly that
new path only after the final pre-write identity check; every other worktree
change remains `fail:candidate_identity_drift`. Dry-run and validation modes
allow no worktree change.

- [ ] **Step 7: Refresh identities, run deterministic GREEN, and commit**

After the production adapter and both Task 3 files are final, compute and bind
the exact current plugin-tree and adapter SHA-256 values under the standing
approval above. Recompute them from disk in tests, require every unchanged
manifest/Swift/corpus identity to equal its prior approved value, and prove the
installed plugin tree and trusted hook hash match the same captured bytes.
Placeholders, stale hashes, or self-attested command-line hashes block.

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_runtime_v1_production \
  tests.test_runtime_v1_benchmark \
  tests.test_codex_runtime_v1_benchmark -v
python3 scripts/sync_generated_artifacts.py --check
git diff --check
git add \
  plugins/apple-foundation-models-handoff/hooks/codex/diagnostic_condensation.py \
  tests/test_runtime_v1_production.py \
  tests/e2e/codex_runtime_v1_benchmark.py \
  tests/test_codex_runtime_v1_benchmark.py
git commit -m "test(DEV-255): add paired Runtime V1 benchmark runner"
```

Expected: deterministic production and runner tests PASS; all refreshed hashes
match current reviewed bytes; the runner no longer contains an unconditional
`apple_attempt_counter_unobservable` terminal; no live pair runs inside the
implementation session.

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

Before any provider-backed dry or live row, run the deterministic
current-candidate forwarding preflight described in the Sol/High amendment.
It must exercise the captured Codex `0.145.0` executable, exact installed
plugin/hook/adapter bytes, the stdout-precedes-receipt path, and a local
provider with synthetic content. While request bodies remain transient, prove
that the emitted replacement SHA-256 equals the only `function_call_output` in
request two, no function output exists in request one, the original tool-result
bytes are absent from the whole serialized second request, the `/responses`
request count is exactly two, the command count is exactly one, and the turn is
closed. Delete
the bodies and isolated root, then retain only a normalized result bound to the
candidate commit, executable version, Codex source commit `25af12f7`, plugin
tree, hook, and adapter hashes. A missing, stale, mismatched, or failed result
is `blocked:replacement_forwarding_unproven` and stops before an Apple attempt.

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
object, exactly two normal `/responses` parent requests, one completed parent turn, no
Apple attempt, no retry, and completed cleanup. The harness may print only a
normalized terminal record and must delete raw JSONL and the isolated root.
Any mismatch stops before the matrix with
`blocked:provider_usage_schema_or_semantic_drift`.

For every live `pluginOn` row, derive `validated_applied` only after rechecking
the bound forwarding-preflight result and combining it with that row's
post-stdout `replacement_emitted` application receipt, exact two-`/responses`
OTel count,
closed one-turn JSONL stream, one command execution, and correct closed parent
outcome. This per-row cross-check is the accepted production effect proof.
Neither OTel nor the observation is described as provider-body evidence, and
no provider body is retained.

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
