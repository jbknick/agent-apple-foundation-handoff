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

## Constraints

- Direct tool mode only; code mode remains disabled.
- Capture and recheck exact executables before and after every host phase.
- Use isolated marketplace registration and `plugin add`; never use `codex --plugin-dir` or a trust bypass.
- The approved command executes once per row. Neither hook nor bridge can execute or retry it.
- One plugin-on row permits at most one Apple attempt and no retry.
- Successful replacement must be inline, unspooled, present in the second provider request, and replace the original.
- Decline/failure emits no hook stdout and preserves Codex's untouched original.
- Raw provider bodies, hook input, diagnostic content, Apple prompts/output, transcripts, configuration, credentials, private paths, traces, and compiled binaries stay transient.
- Missing CLI, authentication, SDK, compiler, model, hardware, locale, trust, telemetry, or cleanup is `blocked`; an invariant violation is `fail`.
- Do not modify the production plugin, DEV-142, DEV-246, or any canceled issue.
- Only a final `pass` may unblock DEV-254 after its plan baseline refresh.

## File structure

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
- Modify: `tests/e2e/codex_runtime_v1_capability_probe.py` only if a deterministic harness defect is reproduced under RED/GREEN.

- [ ] **Step 1: Run through the direct boundary**

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

- [ ] **Step 2: Verify both rows**

Require:

```text
plugin_off_baseline:
  commandExecutions = 1
  providerRequests = 2
  appleAttempts = 0
  additionalParentModelTurns = 0

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

Any missing prerequisite is `blocked`; any mismatch is `fail`. Stop before Apple unless both rows pass.

### Task 3: Pass one real composed Apple row

**Files:**
- Modify: `tests/e2e/codex_runtime_v1_capability_probe.py` only for a reproduced harness defect.
- Modify: `fixtures/runtime-v1-capability/synthetic-plugin/runtime/DiagnosticCondenser.swift` only for a reproduced contract defect reviewed against installed SDK 26.5.

- [ ] **Step 1: Run through the composed boundary**

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

- [ ] **Step 2: Verify the real row**

Require:

```text
commandExecutions = 1
hookInvocations = 1
hookInputSha256 = originalSha256
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

The second-request output SHA must equal the adapter's transient replacement SHA. Missing model, hardware, SDK, or locale is `blocked`; an attempted invalid Apple result is `fail`.

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
appleAttempts <= 1
cleanupStatus = complete
```

The unapproved stimulus must decline before Apple. Any mismatch is `fail:untouched_original_invariant_failed`.

### Task 5: Publish only normalized evidence and finish DEV-253

**Files:**
- Modify: `fixtures/runtime-v1-capability/README.md`
- Create: `docs/research/evidence/runtime-v1-capability-gate.json`
- Create: `docs/research/runtime-v1-capability-gate.md`
- Modify: `tests/e2e/codex_runtime_v1_capability_probe.py`
- Modify: `tests/test_codex_runtime_v1_capability_probe.py`

- [ ] **Step 1: Validate the final closed evidence**

Require exact top-level and row key sets, all five approved trust identities, SHA-256 forms, C0 classification/grant, normalized `<host-path>`, zero unsafe findings, and complete cleanup. Reject private paths, credentials, prompt/result/transcript keys, original sentinel text, raw provider bodies, hook input, diagnostics, and Apple output.

- [ ] **Step 2: Write the bounded interpretation**

Record only the normalized verdict, evidence SHA-256, exact tested boundary, acceptance mapping, proven claims, unproven claims, and stop/unblock decision. Quote no provider, tool, or Apple content.

- [ ] **Step 3: Run focused and full gates**

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

Expected: JSON valid, focused/full tests PASS except declared pre-existing skips, generator synchronized, no diff errors, and only DEV-253 paths changed.

- [ ] **Step 4: Run Sol/High gate review**

Review all 13 approved capability assertions, all five trust identities, executable rechecks, direct/code mode, one command, one Apple attempt, DEV-142 validity, replacement SHA equality, original absence/preservation, parent turns, spooling, evidence safety, cleanup, and truthful blocker/failure precedence. Fix findings under RED/GREEN and rerun Step 3.

- [ ] **Step 5: Commit planning-scope implementation output**

Run:

```bash
git add \
  fixtures/runtime-v1-capability \
  tests/e2e/codex_runtime_v1_capability_probe.py \
  tests/test_codex_runtime_v1_capability_probe.py \
  docs/research/evidence/runtime-v1-capability-gate.json \
  docs/research/runtime-v1-capability-gate.md
git commit -m "test(DEV-253): record Runtime V1 capability gate"
```

- [ ] **Step 6: Finish the issue truthfully**

Open one DEV-253 PR, wait for green CI, merge, verify remote containment and a clean synchronized worktree, then update DEV-253 with exact normalized proof. Mark it complete for any truthful verdict; only `pass:capability_proven` unblocks DEV-254 execution after the DEV-254 plan refresh.
