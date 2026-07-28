# DEV-253 Runtime V1 Successor Capability Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the prepared repository-only gate and record one safe `pass`, `blocked`, or `fail` verdict for the installed Codex `0.145.0` direct-result boundary composed with one real local Apple Foundation Models response.

**Architecture:** Reuse the committed synthetic plugin, Swift condenser, installed-CLI harness, and frozen DEV-142 validator. An authorized outer Codex session approves the exact base and timeout trust identities, runs the direct and composed rows in order, runs the untouched-original failure matrix, and commits only closed normalized evidence.

**Tech Stack:** Python 3 standard library and `unittest`; Codex CLI `0.145.0`; app-server hook trust; loopback deterministic Responses protocol; Swift 6.3.3; macOS SDK 26.5 `FoundationModels`; JSON and SHA-256.

**Linear issue:** [DEV-253](https://linear.app/devprentice/issue/DEV-253/d6-prove-runtime-v1-direct-local-consultation-capability)

**Spec source:** `docs/superpowers/specs/2026-07-26-runtime-v1-successor-linear-backlog-design.md`

**Predecessor:** None. DEV-142 and DEV-246 remain immutable historical authorities.

---

## Current checkpoint

The following work is already committed and must not be recreated:

```text
a3a415e test: define Runtime V1 capability adapter
799f9e9 test: add local Apple condenser fixture
e856e19 test: add installed Codex boundary harness
07e185e test: prepare Runtime V1 live gate
```

The implementation starts with the two missing timeout trust fields. Existing fixture, adapter, bridge, harness, and deterministic tests are inputs, not new production code.

### Observed Codex `0.145.0` direct-tool interface refresh

After explicit owner approval of all five trust identities, the first authorized
direct row reached child exit `0`, empty stderr after the PTY correction, and
exactly two provider requests. Both requests advertised these exact six named
tools:
`exec_command`, `multi_agent_v1`, `request_user_input`, `update_plan`,
`view_image`, and `write_stdin`. A subsequent exact no-command structural probe
also found a seventh nameless
`{type: "web_search", external_web_access: true}` tool entry in both requests,
even though it was not invoked. `code_mode` and `code_mode_only` were
explicitly disabled. The reviewed normalized `exec_command` provider schema
requires only `cmd`, and the current Codex manual requires top-level
`web_search = "disabled"` to remove the web-search tool under
`danger-full-access`.

The row was correctly rejected before Apple because the prepared provider
fixture still emitted `shell_command` and the prepared direct-mode assertion
rejected `exec_command` and the advertised `write_stdin` companion. The
structural probe is also rejected because the enabled web-search surface
violates the binding no-network-fallback boundary. These are supported
installed-interface corrections, not trust, provider, topology, or
runtime-policy changes. Refresh the fixture to emit
`exec_command({"cmd": APPROVED_COMMAND})`; require `exec_command` to be present,
code-mode-only and web-search tools to be absent, and no `write_stdin` call or
event. Mere advertisement of `write_stdin` is not an invocation. No capability
row is accepted from either rejected observation.

After those interface corrections, `direct_fake_applied` passed with
`hookInputSha256 =
dfb7f1221f87b5450ae6135e980c558b8cd45bacffd77df834a17c673fe4b0c0`,
the approved raw stimulus SHA, an exact raw
replacement-only second-request output, one command, one hook, two provider
requests, and zero added parent turns. The plugin-off baseline was rejected
solely because the prepared parser expected the obsolete `Exit code...`
wrapper. Codex `0.145.0` now returns the supported completed
`exec_command` envelope:

```text
Chunk ID: <lower-hex>
Wall time: <decimal> seconds
Process exited with code 0
Original token count: <nonnegative integer>
Output:
<exact raw stimulus once>
```

This observation refreshes only fallback-envelope parsing. The dynamic chunk
ID, wall time, and token count are transport metadata; they are not trust
identities and do not enter committed evidence. The five approved identities
remain unchanged, and the passing applied path continues to require the exact
raw replacement SHA without this envelope. The isolated applied-row pass does
not satisfy Task 2, authorize Apple, or constitute capability acceptance while
the baseline remains rejected.

After Task 2 passed both rows, the first composed harness preflight made zero
Apple attempts and preserved the original. A separately bounded invocation
using the same approved C0 stimulus then proved
`SystemLanguageModel.default` available, locale supported, `contextSize =
4096`, exactly one Apple attempt, zero condensations, process exit `0`, empty
stderr, and `status = fail` with the opaque reason `generation_declined`. No
retry occurred. This is a truthful failed Apple attempt, not a valid structured
response or capability pass.

SDK 26.5 exposes these
`LanguageModelSession.GenerationError` cases. Replace the opaque catch result
with this closed application-owned classification:

| SDK case | Bridge status | Stable reason code | Gate result |
|---|---|---|---|
| `assetsUnavailable` | `declined` | `generation_assets_unavailable` | `blocked` |
| `unsupportedLanguageOrLocale` | `declined` | `generation_unsupported_language_or_locale` | `blocked` |
| `rateLimited` | `declined` | `generation_rate_limited` | `blocked` |
| `concurrentRequests` | `declined` | `generation_concurrent_requests` | `blocked` |
| `exceededContextWindowSize` after successful preflight | `fail` | `generation_exceeded_context_window_size` | `fail` |
| `guardrailViolation` | `fail` | `generation_guardrail_violation` | `fail` |
| `unsupportedGuide` | `fail` | `generation_unsupported_guide` | `fail` |
| `decodingFailure` | `fail` | `generation_decoding_failure` | `fail` |
| `refusal` | `fail` | `generation_refusal` | `fail` |
| any non-`GenerationError` or future unknown error | `fail` | `generation_unknown_error` | `fail` |

Pre-response model or service unavailability remains the existing
`apple_unavailable` blocker. Any throw while computing instruction, prompt, or
schema token counts or other pre-`respond` generation preparation maps only to
bridge status `declined`, stable reason
`generation_preflight_unavailable`, gate result `blocked`, and
`appleAttempts = 0`. Never serialize or inspect
`Context.debugDescription`, `LocalizedError` text, refusal transcript entries
or explanations, Apple output, or the raw error.

After the stream-order fixture correction formally passed, both direct rows
passed. The next `composed_live_apple_applied` row preserved the exact original
but recorded only `hook_invoked` and `original_observed`: it recorded no
`consultation_completed` and no replacement. The outer harness reported
`appleAttempts = 0`, but the missing bridge observation makes the real attempt
state unknown; zero is therefore unsupported. The row truthfully failed with
`replacement_invariant_failed`, two provider requests, zero added turns, no
retry, and complete cleanup.

Close this observability gap at the bridge-process boundary. For the live Apple
bridge or any unexpected process outcome, record only one application-owned
outcome class and bounded observation counters:

| Bridge-process outcome | Gate result | Apple attempts |
|---|---|---|
| `result_observed` with a closed valid bridge result | result-dependent | trusted structured `0` or `1` |
| `launch_unavailable` | `blocked` | `null` |
| `timed_out` | `blocked` | `null` |
| `nonzero_exit` | `fail` | `null` |
| `stderr_nonempty` | `fail` | `null` |
| `stdout_shape_invalid` | `fail` | `null` |
| `json_invalid` | `fail` | `null` |
| `result_shape_invalid` | `fail` | `null` |
| `start_observation_missing` | `fail` | `null` |
| `completion_observation_missing` | `fail` | `null` |
| `observation_invalid` | `fail` | `null` |

Use that precedence exactly: launch, timeout, nonzero, stderr, stdout shape,
JSON, result shape, valid result. Record `bridgeStartObservations` and
`bridgeCompletionObservations` as observation counters, each restricted to
`0` or `1`; they do not claim an unobserved process or Apple action did not
occur. Only a closed valid bridge result may supply an Apple-attempt count.
Every other process outcome serializes `appleAttempts = null`, never `0`, and
can never pass.

Observation integrity precedes terminal process classification: a missing
start, missing completion, duplicate, or contradictory observation uses its
closed observation outcome above. Only exactly one start plus one completion
may be classified by the launch-through-valid-result precedence.

The controlled non-Apple failure-matrix bridges and pre-bridge fault injections
are the sole exception: their reviewed fixture identity proves Apple is not
reachable, so they may record `appleAttempts = 0` and pass only their exact
fallback oracle. That fixture-only zero is not live Apple process evidence and
cannot satisfy the composed capability row.

### CI baseline refresh

GitHub Actions is enabled, but `origin/main` has no `.github` tree and the
repository has no authored workflow. The only visible dynamic Copilot workflow
is not repository CI. There is no branch protection or ruleset, and PR #17 at
head `810a360` has zero check runs. The existing requirement to wait for green
CI is therefore impossible under the plan's current path boundary.

Authorize exactly one repository workflow,
`.github/workflows/ci.yml`, solely to run the existing deterministic repository
contract on pull requests and pushes to `main`. This closes the CI gate; it
does not prove Apple availability, live capability, trust, or evidence
correctness beyond the commands it actually runs, and it does not replace the
separately required local SDK 26.5 proof.

## Constraints

- Direct tool mode only: `exec_command` is present, code-mode-only tools are
  absent, and `code_mode` plus `code_mode_only` remain explicitly disabled.
  `write_stdin` may be advertised as the installed direct-tool companion but
  must never be called or emitted for this completed-output row.
- Every run passes `-c 'web_search="disabled"'`; both provider requests must
  omit the `web_search` tool entry. Network fallback remains prohibited.
- Capture and recheck exact executables before and after every host phase.
- Use isolated marketplace registration and `plugin add`; never use `codex --plugin-dir` or a trust bypass.
- The approved command executes once per row. Neither hook nor bridge can execute or retry it.
- One plugin-on row permits at most one Apple attempt and no retry.
- Isolate token-count, schema, and other generation preflight work in its own
  catch. Any preflight throw emits only
  `declined/generation_preflight_unavailable`, is `blocked`, reports zero
  attempts and no condensation, and preserves the exact original without
  inspecting the error.
- Set `appleAttempts = 1` only after every preflight operation and the existing
  context-budget guard succeed, immediately before the single `respond`.
  Classified errors thrown by that `respond` retain exactly one attempt.
- Classify a thrown Apple generation error only by its SDK enum case into the
  closed stable reason-code table above. Missing assets, locale, service,
  rate, or concurrency prerequisites are `blocked`; post-preflight context
  overflow, guardrail, unsupported guide, decoding, refusal, and unknown
  errors are `fail`.
- Every classified Apple error emits no condensation and preserves the exact
  original through the supported `exec_command` envelope. No case permits a
  retry or a second Apple attempt.
- Emit one stable bridge-start observation before process launch and one
  stable terminal process-outcome observation on every closed launch, timeout,
  exit, stderr, stdout-shape, JSON, or result-shape branch. Record only the
  closed outcome enum and bounded observation counters.
- If the start or terminal observation is missing, or the child does not
  return a closed valid bridge result, Apple attempt state is unknown:
  serialize `appleAttempts = null`, preserve the exact original, never retry,
  and return the table's `blocked` or `fail` result. Never coerce silence to
  zero or pass.
- Never serialize bridge stderr/stdout, exception or error strings, exit
  values, Apple content, paths, prompts, transcripts, or hashes derived from
  any of them. Stable outcome classes and bounded counters are the complete
  process evidence.
- Never serialize Apple error descriptions, localized strings, refusal
  transcripts/explanations, Apple output, or raw errors into bridge output,
  observations, diagnostics, or committed evidence.
- Successful replacement must be inline, unspooled, present in the second provider request, and replace the original.
- Decline/failure emits no hook stdout. Parse the closed successful
  `exec_command` envelope, validate its success metadata, and require the
  remaining payload bytes to equal the untouched original exactly once.
- Chunk ID, wall time, and original token count remain transient transport
  metadata and never become trust identities or committed evidence fields.
- Raw provider bodies, hook input, diagnostic content, Apple prompts/output, transcripts, configuration, credentials, private paths, traces, and compiled binaries stay transient.
- Missing CLI, authentication, SDK, compiler, model, hardware, locale, trust, telemetry, or cleanup is `blocked`; an invariant violation is `fail`.
- Do not modify the production plugin, DEV-142, DEV-246, or any canceled issue.
- Only a final `pass` may unblock DEV-254 after its plan baseline refresh.
- CI is limited to `.github/workflows/ci.yml`, uses no secrets or write
  permissions, and cannot invoke Codex, Apple generation, a live host row,
  network inference, or release/publish behavior.

## File structure

- Create `.github/workflows/ci.yml` — minimal deterministic pull-request and
  `main` push regression gate.
- Modify `tests/e2e/codex_runtime_v1_capability_probe.py` — close timeout trust fields, run rows, and write normalized evidence.
- Modify `tests/test_codex_runtime_v1_capability_probe.py` — schema, trust, row, evidence, and safety checks.
- Modify `fixtures/runtime-v1-capability/README.md` — exact approved hashes and outer-session execution order.
- Create `docs/research/evidence/runtime-v1-capability-gate.json` — normalized gate verdict.
- Create `docs/research/runtime-v1-capability-gate.md` — bounded interpretation and stop/unblock decision.

### Task 1: Close and approve all five trust identities

**Files:**
- Modify: `tests/e2e/codex_runtime_v1_capability_probe.py`
- Modify: `tests/test_codex_runtime_v1_capability_probe.py`
- Modify: `fixtures/runtime-v1-capability/README.md`

- [ ] **Step 1: Write the failing timeout-field tests**

Add `timeoutPluginSha256` and `timeoutHookCurrentHash` to the exact top-level evidence key set. In the canonical test value, use:

```python
"pluginSha256": "e" * 64,
"hookCurrentHash": "sha256:" + ("f" * 64),
"timeoutPluginSha256": "a" * 64,
"timeoutHookCurrentHash": "sha256:" + ("b" * 64),
```

Add rejection cases for a missing field, unknown field, malformed raw SHA-256, malformed `sha256:` hook hash, and equality between the base and timeout plugin/hash identities.

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_codex_runtime_v1_capability_probe.GateNormalizerTests -v
```

Expected: FAIL because the two timeout fields are not in the closed schema.

- [ ] **Step 3: Implement the two fields**

Add the fields to the top-level key tuple and evidence builder:

```python
"timeoutPluginSha256",
"timeoutHookCurrentHash",
```

Validate:

```python
if (
    not _digest(value["timeoutPluginSha256"])
    or not _digest(value["timeoutHookCurrentHash"], prefixed=True)
    or value["timeoutPluginSha256"] == value["pluginSha256"]
    or value["timeoutHookCurrentHash"] == value["hookCurrentHash"]
):
    raise ProbeFailure("timeout_trust_identity_invalid")
```

Require the complete run to receive `--approved-timeout-plugin-sha256` and `--approved-timeout-hook-hash`; direct/composed partial runs may carry `null` internally but cannot write final repository evidence.

- [ ] **Step 4: Run focused GREEN**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_codex_runtime_v1_capability_probe.GateNormalizerTests \
  tests.test_codex_runtime_v1_capability_probe.TrustInspectionTests -v
```

Expected: PASS.

- [ ] **Step 5: Inspect the base identities**

From the authorized outer session, capture exact executables:

```bash
runtime_v1_codex_path="$(command -v codex)"
runtime_v1_python_path="$(command -v python3)"
runtime_v1_xcrun_path="$(command -v xcrun)"
runtime_v1_swiftc_path="$(command -v swiftc)"
test -x "$runtime_v1_codex_path"
test -x "$runtime_v1_python_path"
test -x "$runtime_v1_xcrun_path"
test -x "$runtime_v1_swiftc_path"

runtime_v1_tmp_dir="$(mktemp -d)"
test -d "$runtime_v1_tmp_dir"
runtime_v1_base_inspection="$runtime_v1_tmp_dir/base-trust.json"
PYTHONDONTWRITEBYTECODE=1 python3 \
  tests/e2e/codex_runtime_v1_capability_probe.py \
  --inspect-trust \
  --codex-executable "$runtime_v1_codex_path" \
  --python-executable "$runtime_v1_python_path" \
  --plugin fixtures/runtime-v1-capability/synthetic-plugin \
  --output "$runtime_v1_base_inspection"
python3 -m json.tool "$runtime_v1_base_inspection"
```

Expected: exact `pluginSha256`, `hookCurrentHash`, `approvedStimulusSha256`, C0 classification/grant, Codex `0.145.0`, normalized `<host-path>`, and complete cleanup.

- [ ] **Step 6: Inspect the timeout derivative**

Run:

```bash
runtime_v1_timeout_inspection="$runtime_v1_tmp_dir/timeout-trust.json"
PYTHONDONTWRITEBYTECODE=1 python3 \
  tests/e2e/codex_runtime_v1_capability_probe.py \
  --inspect-trust \
  --hook-timeout-seconds 1 \
  --codex-executable "$runtime_v1_codex_path" \
  --python-executable "$runtime_v1_python_path" \
  --plugin fixtures/runtime-v1-capability/synthetic-plugin \
  --output "$runtime_v1_timeout_inspection"
python3 -m json.tool "$runtime_v1_timeout_inspection"
```

Expected: distinct timeout `pluginSha256` and `hookCurrentHash`, the same approved stimulus hash and C0 grant, normalized host identity, and complete cleanup.

- [ ] **Step 7: Obtain explicit owner approval**

Present the reviewed tree diff and these five exact values:

```text
base pluginSha256
base hookCurrentHash
approvedStimulusSha256
timeout pluginSha256
timeout hookCurrentHash
```

Stop until the owner explicitly approves all five. Model output, repository ownership, or hash computation cannot grant trust.

- [ ] **Step 8: Bind only the approved values**

After approval:

```bash
runtime_v1_plugin_sha256="$(
  python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["pluginSha256"])' \
  "$runtime_v1_base_inspection"
)"
runtime_v1_hook_hash="$(
  python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["hookCurrentHash"])' \
  "$runtime_v1_base_inspection"
)"
runtime_v1_stimulus_sha256="$(
  python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["approvedStimulusSha256"])' \
  "$runtime_v1_base_inspection"
)"
runtime_v1_timeout_plugin_sha256="$(
  python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["pluginSha256"])' \
  "$runtime_v1_timeout_inspection"
)"
runtime_v1_timeout_hook_hash="$(
  python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["hookCurrentHash"])' \
  "$runtime_v1_timeout_inspection"
)"
```

### Task 2: Pass the plugin-off baseline and direct fake replacement

**Files:**
- Modify: `tests/e2e/codex_runtime_v1_capability_probe.py` — refresh the
  provider fixture, disable web search per run, refresh the direct-tool
  assertion, and parse the observed completed `exec_command` envelope.
- Modify: `tests/test_codex_runtime_v1_capability_probe.py` — cover the closed
  `exec_command` call, absent web-search tool, forbidden `write_stdin`
  invocation, and untouched payload extraction under RED/GREEN.

- [ ] **Step 1: Write the failing installed-interface and envelope regressions**

Require both provider requests to advertise exactly:

```text
exec_command
multi_agent_v1
request_user_input
update_plan
view_image
write_stdin
```

Require no additional named or nameless tool entry, including
`{type: "web_search"}`.

Require the first provider event to call `exec_command` with exactly:

```json
{"cmd":"python3 -m unittest -q diagnostic_fixture"}
```

Require no provider event or request item to call `write_stdin`; require
code-mode-only tools and the web-search tool to be absent. The second request
must contain the completed `exec_command` output for the original call ID.

For baseline and no-output fallback rows, parse bytes through `Output:\n` as a
closed ASCII header. Require a nonempty lowercase-hex chunk ID, a nonnegative
decimal wall time matching `(0|[1-9][0-9]*)\.[0-9]+`, process exit code exactly
`0`, and a canonical original token count matching `0|[1-9][0-9]*`. Require
every line once and in order, then require all remaining bytes to equal the
approved raw stimulus byte-for-byte. Reject
unknown, missing, reordered, duplicated, malformed, nonzero-exit, trailing, or
mutated content. Applied rows remain outside this parser and require the exact
raw replacement SHA.

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_codex_runtime_v1_capability_probe.HarnessTests -v
```

Expected: FAIL until the prepared interface fixture/checker is refreshed, web
search is explicitly disabled, and the obsolete `Exit code...` fallback parser
accepts only the observed completed `exec_command` envelope.

- [ ] **Step 3: Refresh only the direct provider fixture, assertion, and envelope parser**

Emit one `exec_command` function call with only
`cmd = APPROVED_COMMAND`. Add `-c 'web_search="disabled"'` to
`build_exec_arguments`. Accept the exact six named direct tools while rejecting
any additional named or nameless entry, including `web_search`; reject any
`write_stdin` call/event, any code-mode-only tool, any additional command call,
or any argument beyond `cmd`. Preserve the existing command counter,
two-request, zero-added-turn, and completed-output checks. Replace only the
obsolete fallback-wrapper parser with the closed header parse and exact
remaining-payload comparison above; do not normalize, hash, persist, or trust
the chunk ID, wall time, or token count.

- [ ] **Step 4: Run focused GREEN**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_codex_runtime_v1_capability_probe.HarnessTests -v
```

Expected: PASS.

- [ ] **Step 5: Run through the direct boundary**

Run from the authorized outer session:

```bash
runtime_v1_partial_output="$runtime_v1_tmp_dir/direct.json"
PYTHONDONTWRITEBYTECODE=1 python3 \
  tests/e2e/codex_runtime_v1_capability_probe.py \
  --codex-executable "$runtime_v1_codex_path" \
  --python-executable "$runtime_v1_python_path" \
  --xcrun-executable "$runtime_v1_xcrun_path" \
  --swiftc-executable "$runtime_v1_swiftc_path" \
  --plugin fixtures/runtime-v1-capability/synthetic-plugin \
  --approved-plugin-sha256 "$runtime_v1_plugin_sha256" \
  --approved-hook-hash "$runtime_v1_hook_hash" \
  --approved-stimulus-sha256 "$runtime_v1_stimulus_sha256" \
  --through direct \
  --output "$runtime_v1_partial_output"
```

- [ ] **Step 6: Verify both rows**

Require:

```text
plugin_off_baseline:
  commandExecutions = 1
  providerRequests = 2
  appleAttempts = 0
  additionalParentModelTurns = 0
  originalPreserved = true

direct_fake_applied:
  commandExecutions = 1
  hookInvocations = 1
  hookInputSha256 = originalSha256
  appleAttempts = 0
  providerRequests = 2
  additionalParentModelTurns = 0
  originalAbsentFromNextRequest = true
  replacementPresentInNextRequest = true
  replacementBytes <= 4096
  spooled = false
  cleanupStatus = complete
```

For both rows, both provider requests must pass the refreshed direct-tool
assertion: the exact observed advertised set, `exec_command` present,
code-mode-only and web-search tools absent, and zero `write_stdin` calls/events.
The run arguments must contain `-c 'web_search="disabled"'`. This refresh does
not widen the closed normalized evidence schema.

For `plugin_off_baseline`, `originalPreserved = true` means the closed
`exec_command` success header is valid and its remaining payload equals the
approved raw stimulus exactly once. For `direct_fake_applied`, the
second-request output SHA must equal the transient raw replacement SHA with no
transport envelope.

Any missing prerequisite is `blocked`; any mismatch is `fail`. Stop before Apple unless both rows pass.

### Task 3: Pass one real composed Apple row

**Files:**
- Modify: `fixtures/runtime-v1-capability/synthetic-plugin/runtime/DiagnosticCondenser.swift` — replace the opaque catch with the closed SDK 26.5 case classification.
- Modify: `fixtures/runtime-v1-capability/synthetic-plugin/hooks/codex/probe.py` — emit only closed bridge-process outcomes and observation counters.
- Modify: `tests/e2e/codex_runtime_v1_capability_probe.py` — normalize each stable generation/process reason and nullable attempt state truthfully.
- Modify: `tests/test_codex_runtime_v1_capability_probe.py` — deterministic generation mapping, every process branch, fallback, attempt-budget, evidence-safety, and SDK compile checks.
- Modify: `fixtures/runtime-v1-capability/README.md` — record only owner-approved refreshed plugin identities.

- [ ] **Step 1: Write the failing generation and bridge-process observation tests**

Exercise every row in the closed classification table without invoking
`SystemLanguageModel.default`. Require the exact bridge status and stable
reason code, `appleAttempts = 1`, no condensation, no retry, and untouched
original fallback. Require the harness to normalize the four prerequisite
`respond` classes as `blocked` and every invariant/refusal/unknown class as
`fail`.

Separately inject a failure into each token-count/schema preflight operation.
Every case must produce only
`declined/generation_preflight_unavailable`, zero Apple attempts, zero valid
results, no condensation, no retry, exact original fallback, and a normalized
`blocked` gate result. Add an ordering assertion that the attempt counter
changes from zero to one only after all preflight work and the context-budget
guard complete.

Add safety assertions that neither source nor structured output serializes or
reads `debugDescription`, `errorDescription`, `failureReason`,
`recoverySuggestion`, refusal transcripts or explanations, localized strings,
Apple output, or a raw error. Preserve the existing one-`respond` source check.

Deterministically exercise process launch failure, timeout, nonzero exit,
nonempty stderr, invalid stdout framing, invalid JSON, non-object/invalid
result shape, valid structured result, missing start observation, and missing
completion observation. Require the exact outcome, precedence, start/completion
observation counters, blocked/fail mapping, exact original fallback, and no
retry for every branch.

Allow `appleAttempts` to be `null` only for a non-passing row whose bridge
outcome is not `result_observed`. A valid structured result may report only
`0` or `1`; an applied pass requires `1`. A deterministic decline before any
bridge invocation may retain proven `0`. Missing or incomplete observations
must never normalize to zero or pass.

For every branch, assert the transient observations and closed committed row
schema exclude raw stderr/stdout, exception/error text, exit values, Apple
content, paths, prompts, transcripts, and derived hashes. Unknown keys and
unknown outcome classes fail validation.

- [ ] **Step 2: Run focused RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_codex_runtime_v1_capability_probe.SwiftBridgeTests \
  tests.test_codex_runtime_v1_capability_probe.HarnessTests -v
```

Expected: FAIL because one catch still conflates zero-attempt preflight errors
with one-attempt `respond` errors, `generation_declined` remains opaque, and the
harness does not yet classify the closed stable reason codes. The hook also
lets bridge-process exceptions disappear into its broad fallback, so process
outcome and Apple attempt state are unobservable.

- [ ] **Step 3: Implement the minimum typed catch and gate mapping**

Wrap all token-count, schema, and other generation preparation in a dedicated
preflight catch that returns only
`declined/generation_preflight_unavailable` with zero attempts. Do not inspect
or classify that error. After successful preflight and the existing
context-budget guard, set `appleAttempts = 1` immediately before the single
`respond`.

Wrap only `respond` in the typed classification catch. Catch
`LanguageModelSession.GenerationError`, switch only on its SDK enum case,
ignore every associated `Context` and `Refusal` value, and return only the
table's stable status/reason pair with one attempt. An `@unknown default` and a
separate untyped catch both return only `fail/generation_unknown_error` with
one attempt. Do not stringify, reflect, log, interpolate, or otherwise inspect
either error.

Update the outer harness's closed blocker mapping to include
`generation_preflight_unavailable` with zero attempts. A classified error after
`respond` must report exactly one Apple attempt and zero valid results, emit no
replacement, preserve the untouched original, and terminate without a retry.
Keep the case mapping in the smallest deterministic unit-testable helper; do
not add a logging, error-wrapper, or retry abstraction.

At the hook boundary, emit the stable start observation immediately before the
single process invocation. Convert each process result branch into exactly one
terminal outcome observation using the table's precedence. Return the valid
structured bridge result only for `result_observed`; every other outcome emits
no replacement and preserves the original. The outer harness validates exactly
one start and one terminal observation for an observed invocation and derives
the normalized process outcome without reading raw process material.

If no start observation exists after an eligible original, classify
`start_observation_missing` regardless of any stray terminal observation. If
one start exists without a terminal observation, classify
`completion_observation_missing`. Duplicate or otherwise contradictory
observations classify `observation_invalid`. All are `fail` with
`appleAttempts = null`. Use the nullable attempt value for every other
non-result process outcome. Do not use exception messages, raw streams, paths,
or Apple content to derive any class.

- [ ] **Step 4: Run deterministic GREEN and SDK compilation**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_codex_runtime_v1_capability_probe.SwiftBridgeTests \
  tests.test_codex_runtime_v1_capability_probe.HarnessTests -v
```

Require all preflight and `respond` mapping, every bridge-process branch and
precedence, observation counters, nullable-attempt semantics, evidence safety,
fallback, attempt ordering/budget, and SDK 26.5 typecheck/compile assertions to
pass without invoking Apple.

- [ ] **Step 5: Reinspect trust and obtain refreshed plugin and hook approvals**

After the Swift source, hook, harness, and tests are final, rerun Task 1 Steps
5 and 6 against the exact current base and timeout trees. Require:

```text
base pluginSha256 = freshly computed from the final base tree
timeout pluginSha256 = freshly computed from the final timeout tree
base hookCurrentHash = freshly inspected from the installed final base tree
timeout hookCurrentHash = freshly inspected from the installed final timeout tree
approvedStimulusSha256 = dfb7f1221f87b5450ae6135e980c558b8cd45bacffd77df834a17c673fe4b0c0
```

Stop on stimulus drift or any inspection/cleanup failure. Present the reviewed
Swift and hook diff plus all four freshly computed/inspected base and timeout
plugin/hook identities to the owner. Obtain explicit approval of those exact
four current values even if an inspected hook hash happens to equal its prior
value. Then rebind all four runtime trust variables. Prior approvals do not
authorize changed plugin or hook bytes. Do not invent, predict, or copy
placeholder hashes, and do not run Apple before approval.

- [ ] **Step 6: Run through the composed boundary**

Run:

```bash
runtime_v1_composed_output="$runtime_v1_tmp_dir/composed.json"
PYTHONDONTWRITEBYTECODE=1 python3 \
  tests/e2e/codex_runtime_v1_capability_probe.py \
  --codex-executable "$runtime_v1_codex_path" \
  --python-executable "$runtime_v1_python_path" \
  --xcrun-executable "$runtime_v1_xcrun_path" \
  --swiftc-executable "$runtime_v1_swiftc_path" \
  --plugin fixtures/runtime-v1-capability/synthetic-plugin \
  --approved-plugin-sha256 "$runtime_v1_plugin_sha256" \
  --approved-hook-hash "$runtime_v1_hook_hash" \
  --approved-stimulus-sha256 "$runtime_v1_stimulus_sha256" \
  --through composed \
  --output "$runtime_v1_composed_output"
```

- [ ] **Step 7: Verify the real row**

Require:

```text
commandExecutions = 1
hookInvocations = 1
hookInputSha256 = originalSha256
bridgeStartObservations = 1
bridgeCompletionObservations = 1
bridgeProcessOutcome = result_observed
appleAttempts = 1
appleValidResults = 1
providerRequests = 2
additionalParentModelTurns = 0
originalAbsentFromNextRequest = true
replacementPresentInNextRequest = true
replacementBytes <= 4096
spooled = false
cleanupStatus = complete
```

The second-request output SHA must equal the adapter's transient replacement
SHA. Missing model, hardware, SDK, service/assets, locale, rate, or concurrency
prerequisites are `blocked`; any thrown token-count/schema preflight emits
`generation_preflight_unavailable`, is also `blocked`, and reports zero
attempts. A post-preflight context-window failure, guardrail, unsupported
guide, decoding failure, refusal, unknown error, or attempted invalid Apple
result is `fail` with one attempt. Every classified non-applied result must
preserve the exact original with no retry. Stop on either terminal result; only
one schema-valid applied response passes Task 3.

A non-result process outcome uses the closed process table and
`appleAttempts = null`. Missing, duplicate, contradictory, or incomplete
observations are invariant failures, never evidence of zero attempts. A
blocked launch/timeout or any failed process/observation outcome preserves the
exact original, performs no retry, and stops the composed gate.

### Task 4: Pass the untouched-original failure matrix

**Files:**
- Modify: `tests/e2e/codex_runtime_v1_capability_probe.py` only for a reproduced invariant defect.
- Modify: `tests/test_codex_runtime_v1_capability_probe.py` with one RED regression per defect.

- [ ] **Step 1: Run the complete matrix**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 \
  tests/e2e/codex_runtime_v1_capability_probe.py \
  --codex-executable "$runtime_v1_codex_path" \
  --python-executable "$runtime_v1_python_path" \
  --xcrun-executable "$runtime_v1_xcrun_path" \
  --swiftc-executable "$runtime_v1_swiftc_path" \
  --plugin fixtures/runtime-v1-capability/synthetic-plugin \
  --approved-plugin-sha256 "$runtime_v1_plugin_sha256" \
  --approved-hook-hash "$runtime_v1_hook_hash" \
  --approved-stimulus-sha256 "$runtime_v1_stimulus_sha256" \
  --approved-timeout-plugin-sha256 "$runtime_v1_timeout_plugin_sha256" \
  --approved-timeout-hook-hash "$runtime_v1_timeout_hook_hash" \
  --through complete \
  --output docs/research/evidence/runtime-v1-capability-gate.json
```

- [ ] **Step 2: Verify every fallback row**

For `decline_unapproved_stimulus`, `bridge_malformed`, `bridge_crash`, `adapter_crash`, and `hook_timeout`, require:

```text
commandExecutions = 1
providerRequests = 2
additionalParentModelTurns = 0
hookInputSha256 = originalSha256
originalPreserved = true
replacementPresentInNextRequest = false
appleAttempts = 0
cleanupStatus = complete
```

For every fallback row, `originalPreserved = true` requires the same closed
successful `exec_command` header and an exact byte-for-byte comparison between
all remaining payload bytes and that row's raw original stimulus. Dynamic
chunk, timing, and token-count metadata are validated only as transport
metadata and are neither compared across rows nor promoted into trust or
committed evidence. The unapproved stimulus must decline before Apple. Any
mismatch is `fail:untouched_original_invariant_failed`.

These five rows use only reviewed non-Apple fake bridges or deterministic
pre-bridge faults, so `appleAttempts = 0` is proven by fixture identity rather
than inferred from missing observations. Record their expected closed
bridge-process outcome and observation counters, and pass the row only when
that expected fault plus the exact fallback oracle both match. Never reuse this
fixture-only zero for `composed_live_apple_applied`.

### Task 5: Publish only normalized evidence and finish DEV-253

**Files:**
- Create: `.github/workflows/ci.yml`
- Modify: `fixtures/runtime-v1-capability/README.md`
- Create: `docs/research/evidence/runtime-v1-capability-gate.json`
- Create: `docs/research/runtime-v1-capability-gate.md`
- Modify: `tests/e2e/codex_runtime_v1_capability_probe.py`
- Modify: `tests/test_codex_runtime_v1_capability_probe.py`

- [ ] **Step 1: Validate the final closed evidence**

Require exact top-level and row key sets, all five approved trust identities, SHA-256 forms, C0 classification/grant, normalized `<host-path>`, zero unsafe findings, and complete cleanup. Reject private paths, credentials, prompt/result/transcript keys, original sentinel text, raw provider bodies, hook input, diagnostics, and Apple output.

The closed row schema includes only the stable bridge-process outcome,
`bridgeStartObservations`, `bridgeCompletionObservations`, and nullable
`appleAttempts` in addition to the existing normalized fields. Enforce the
outcome/counter/nullability rules above. A final pass requires the composed row
to have `result_observed`, one start, one completion, and one observed Apple
attempt. Missing or invalid observations, or a non-result live process outcome,
can never serialize zero attempts or pass.

Reject raw stderr/stdout, exit values, exception/error/localized strings,
refusal data, Apple content, private paths, prompts, transcripts, and any hash
or diagnostic derived from them in both transient observation validation and
committed evidence. Require deterministic schema-safety rejection tests for
every forbidden key/value class.

- [ ] **Step 2: Write the bounded interpretation**

Record only the normalized verdict, evidence SHA-256, exact tested boundary, acceptance mapping, proven claims, unproven claims, and stop/unblock decision. Quote no provider, tool, or Apple content.

- [ ] **Step 3: Add the minimal repository CI workflow**

Create exactly:

```yaml
name: CI

on:
  pull_request:
  push:
    branches:
      - main

permissions:
  contents: read

jobs:
  test:
    runs-on: macos-26
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v6
        with:
          fetch-depth: 0
          persist-credentials: false
      - name: Fetch immutable evidence commits
        run: |
          git fetch --no-tags --depth=1 origin \
            5564ab3303afc79080e5f8bdbba934535e914322 \
            2a111d96329506276741a86028019fab8572b0e8 \
            75c9c8ca8d38bcfd05dc3d82264d1b8219253bc6 \
            cdaa9bd5ce771c41d68603efa7835003ff46ee8c \
            5d6046f87471d341ea93aad4689fb234b88d9cdd \
            c0644b860032f2cd460586f91b14885c91d476f7 \
            464dd11938acebbed055df1bdbf5032c0fadbdb6 \
            ec2094ad9827488539c77a704b97882c69a4ee9e \
            ba18d72e65b46939b1d494cf423f245cdd003231 \
            35ac482a8e2a954525a24d7e6047d6732df41fbe
      - uses: actions/setup-python@v6
        with:
          python-version: "3.13"
      - name: Select Swift 6.3.3 and SDK 26.5
        run: |
          sudo xcode-select --switch /Applications/Xcode_26.6.app/Contents/Developer
          test "$(xcrun --sdk macosx --show-sdk-version)" = "26.5"
      - name: Verify generated artifacts
        run: |
          python3 scripts/sync_generated_artifacts.py --write
          git diff --exit-code
          python3 scripts/sync_generated_artifacts.py --check
      - name: Run tests
        run: PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py' -v
      - name: Check diff formatting
        run: git diff --check
```

Use the currently supported pinned `macos-26` runner because this repository
contains macOS and Swift probes; use explicit Python `3.13` because the
repository has no dependency manifest or Python version file and otherwise the
runner default may drift. The job has one read-only permission, persists no
credential, installs no repository dependency, uses no secret, and is bounded
to 20 minutes.

The checkout fetches current-branch history, then explicitly fetches the exact
closed set of immutable evidence commits because several reviewed captures are
server-retained but no longer reachable from current remote refs. The workflow
selects Xcode 26.6 because the supported `macos-26` image binds it to Swift
6.3.3 while retaining macOS SDK 26.5, then verifies the exact SDK version
before running the repository contract's authored write, check, and full test
commands. `git diff --exit-code` after `--write` makes generated drift fail
instead of silently repairing it, and `git diff --check` preserves the
existing plan gate. The hosted runner does not replace the separately required
exact Codex `0.145.0`, local SDK 26.5, trusted-hook, real Apple, evidence, or
cleanup proof; any declared host skip remains a limitation, never capability
evidence.

- [ ] **Step 4: Run focused and full local gates**

Run:

```bash
python3 -m json.tool \
  docs/research/evidence/runtime-v1-capability-gate.json >/dev/null
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_codex_runtime_v1_capability_probe \
  tests.test_codex_result_replacement_probe \
  tests.test_dev_142_contract -v
python3 scripts/sync_generated_artifacts.py --check
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests -p 'test_*.py' -v
git diff --check
git status --short
```

Expected: JSON valid, focused/full tests PASS except declared pre-existing
skips, SDK 26.5 compile/typecheck PASS, every process branch and evidence-safety
test PASS, generator synchronized, no diff errors, and only DEV-253 paths
changed, including the one authorized workflow.

- [ ] **Step 5: Run Sol/High gate review**

Review all 13 approved capability assertions, all five trust identities,
executable rechecks, the observed `exec_command` direct interface, absence of
code-mode-only and web-search tools, explicit
`web_search = "disabled"`, absence of `write_stdin` calls/events, one command,
one Apple attempt, no retry, all SDK 26.5 generation-error mappings, blocked
versus fail precedence, zero-attempt
`generation_preflight_unavailable`, attempt-counter ordering before `respond`,
one-attempt `respond` errors, absence of Apple/raw/refusal error content,
every closed bridge-process branch and precedence, start/completion observation
integrity, nullable unknown attempts, fixture-only proven zeroes, refreshed
owner approval of all four current plugin/hook identities, unchanged stimulus
readback, DEV-142 validity, exact raw replacement SHA, closed `exec_command`
success-header parsing, exact untouched payload bytes, exclusion of dynamic
envelope metadata from trust/evidence, original absence/preservation, parent
turns, spooling, evidence safety, cleanup, no-network-fallback enforcement,
and truthful blocker/failure precedence. Also review the CI workflow's exact
path, two triggers, pinned runner/Python and action major versions, read-only
permission, full-history checkout, disabled credential persistence, the exact
closed immutable-evidence commit fetch set, explicit Xcode 26.6 selection for
Swift 6.3.3 plus SDK 26.5, timeout, generated-drift check, exact repository
commands, and explicit separation from live capability and local SDK proof.
Fix findings under RED/GREEN and rerun Step 4. After push, require a fresh
exact-head CI readback before merge.

- [ ] **Step 6: Commit planning-scope implementation output**

Run:

```bash
git add \
  .github/workflows/ci.yml \
  fixtures/runtime-v1-capability \
  tests/e2e/codex_runtime_v1_capability_probe.py \
  tests/test_codex_runtime_v1_capability_probe.py \
  docs/research/evidence/runtime-v1-capability-gate.json \
  docs/research/runtime-v1-capability-gate.md
git commit -m "test(DEV-253): record Runtime V1 capability gate"
```

- [ ] **Step 7: Require exact-head green CI, merge, and read back `main` CI**

Open one DEV-253 PR. Before merge, read back a completed successful `CI / test`
check run produced by `.github/workflows/ci.yml` for the PR's exact current
head SHA and `pull_request` event. A dynamic Copilot workflow, a check for an
older SHA, queued/in-progress state, or neutral/skipped/canceled/missing
conclusion is not green CI.

Because no branch protection or ruleset enforces the check, treat this readback
as an application-owned manual merge gate. Do not merge while it is absent or
non-successful. After merge, verify remote containment and require the
workflow's `push` run on the exact resulting `main` commit to complete
successfully. Then verify a clean synchronized worktree and update DEV-253 with
the PR, both exact SHAs, both successful workflow-run/check URLs, and the exact
normalized proof.

Mark DEV-253 complete for any truthful verdict only after both CI readbacks and
all existing gates pass. Only `pass:capability_proven` unblocks DEV-254
execution after the DEV-254 plan refresh.
