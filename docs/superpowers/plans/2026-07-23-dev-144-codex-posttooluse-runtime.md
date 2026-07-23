# DEV-144 Codex PostToolUse Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Install a trusted Codex-only `PostToolUse` runtime that routes eligible completed `Bash` results through the DEV-142 policy and DEV-143 local Apple bridge, then uses the exact passing DEV-246 host contract to expose only the validated compact result to the next parent-model request.

**Architecture:** Keep production adapter sources at repository root, generate their plugin-local cache payload through the existing artifact generator, and point the generated Codex manifest at `hooks/codex/hooks.json`. The adapter validates a closed host event, preserves the original result in memory, applies deterministic policy, invokes the mirrored Swift executable once, validates its terminal envelope, and either performs the frozen replacement or leaves the original host behavior untouched.

**Tech Stack:** Python 3 standard library, Codex CLI `0.144.5`, Codex plugin hooks, generated JSON metadata, Swift Package Manager, `unittest`.

## Global Constraints

- Prerequisites: DEV-246 is merged with `status = pass` and an exact field-level replacement contract; DEV-143 is merged with its deterministic and live Apple proof. Stop and return to Sol if either contract differs from this plan.
- Spec source: `docs/superpowers/specs/2026-07-23-codex-foundation-models-runtime-completion-design.md`.
- Consume DEV-142 policy values exactly; do not edit its frozen repository-only evidence contract.
- The production runtime is Codex-only. The shared Claude manifest must not register hooks, and the default `hooks/hooks.json` path must remain absent.
- Canonical authored inputs remain `CLAUDE.md`, root runtime sources, plugin-local canonical hook inputs, and plugin-local canonical metadata. `AGENTS.md` and `.codex-plugin/plugin.json` remain generated.
- The effective cached payload includes only production bridge sources/executable inputs and Codex hook files; exclude tests, fixtures, research, plans, private state, and repository docs.
- Invoke child processes with argument vectors, `shell=False`, bounded deadlines, controlled environment, explicit executable capture, and at-most-once semantics.
- A decline, failure, timeout, cancellation, malformed event, untrusted hook, unavailable Apple model, invalid compact result, or replacement failure preserves normal original-result behavior.
- Never send both original and compact results to the model. Never add an extra parent-model turn.
- No mobile app, Claude runtime adapter, external LLM, PCC, remote fallback, credentials, paid service, network inference, transcript mutation, MCP detour, chunking, or retry.

---

## File Structure

- Create `runtime/codex-adapter/policy.py` — production closed DEV-142 eligibility and result-validation policy.
- Create `runtime/codex-adapter/codex_diagnostic_condensation.py` — canonical hook adapter.
- Create `plugins/apple-foundation-models-handoff/hooks/codex/hooks.json` — canonical Codex-only hook registration.
- Modify `scripts/sync_generated_artifacts.py` — validate inputs; generate Codex manifest and production-only cache mirrors.
- Modify `CLAUDE.md` — replace the now-stale no-runtime/no-hook repository truth.
- Modify `plugins/apple-foundation-models-handoff/metadata/codex-interface.json` — declare the Codex runtime interface and exact DEV-246 contract version.
- Modify generated `AGENTS.md`, `.agents/plugins/marketplace.json`, and `plugins/apple-foundation-models-handoff/.codex-plugin/plugin.json` only through the generator.
- Generate `plugins/apple-foundation-models-handoff/hooks/codex/codex_diagnostic_condensation.py` and `policy.py` from root canonical sources.
- Generate `plugins/apple-foundation-models-handoff/runtime/apple-foundation-models-bridge/Package.swift` and `Sources/**` from DEV-143 production sources, excluding `Tests/**`.
- Create `tests/test_codex_runtime_adapter.py` — closed event, policy, process, privacy, and replacement tests.
- Modify `tests/test_plugin_contract.py` — Codex-only hook/runtime and cache-payload truth.
- Create `tests/e2e/codex_runtime_activation.py` — exact-host installed-plugin proof.
- Create `docs/research/evidence/dev-144-codex-runtime.json` — normalized activation evidence.

### Task 1: Promote the frozen policy into a production adapter module

**Files:**
- Create: `runtime/codex-adapter/policy.py`
- Create: `tests/test_codex_runtime_adapter.py`

**Interfaces:**
- Consumes: normalized completed-tool metadata and DEV-142 request/result fields.
- Produces: `SelectedRequest`, `Declined`, or `Failed` with the frozen reason vocabulary.

- [ ] **Step 1: Write failing parity and closed-schema tests**

```python
def test_policy_identity_matches_dev_142(self):
    self.assertEqual(adapter_policy.POLICY_VERSION, "diagnostic-condensation-v1")
    self.assertEqual(adapter_policy.MINIMUM_INPUT_BYTES, 8192)
    self.assertEqual(adapter_policy.MAXIMUM_INPUT_BYTES, 65536)
    self.assertEqual(adapter_policy.MAXIMUM_OUTPUT_BYTES, 4096)

def test_unknown_event_key_fails_closed(self):
    event = valid_event()
    event["unexpected"] = True
    self.assertEqual(adapter.normalize_event(event).reason, "contract_invariant_failed")
```

Cover all DEV-142 routing boundaries, C0/C1 `trustedLocal`, destination `apple_on_device`, retention `ephemeral`, 75-percent occupancy, 4,096-byte estimated/realized savings, duplicate keys, future versions, provenance drift, and identity drift.

- [ ] **Step 2: Run focused tests and confirm RED**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_codex_runtime_adapter -v
```

Expected: FAIL because production policy/adapter modules do not exist.

- [ ] **Step 3: Implement the smallest pure policy module**

Copy no fixture at runtime. Re-express the frozen constants and functions as a closed production module, then add test parity against `fixtures/dev-142/runtime_contract.py` across the hash-bound boundary corpus.

- [ ] **Step 4: Run focused tests and confirm GREEN**

Expected: PASS; no child process, Apple generation, or Codex host.

- [ ] **Step 5: Commit the production policy**

```bash
git add runtime/codex-adapter/policy.py tests/test_codex_runtime_adapter.py
git commit -m "feat: add Codex runtime policy boundary"
```

### Task 2: Implement the fail-closed hook adapter

**Files:**
- Create: `runtime/codex-adapter/codex_diagnostic_condensation.py`
- Modify: `tests/test_codex_runtime_adapter.py`

**Interfaces:**
- Consumes: one documented `PostToolUse` JSON event for canonical `Bash`.
- Produces: either the exact DEV-246 replacement response or no replacement, plus bounded normalized diagnostics.

- [ ] **Step 1: Add failing event and process tests**

Test selected success, non-`Bash`, success exit, interrupted command, disallowed classification, insufficient size/savings, malformed/duplicate JSON, bridge decline, bridge fail, timeout, cancellation, invalid bridge identity, oversize compact result, original/compact overlap, and second invocation.

- [ ] **Step 2: Run focused tests and confirm RED**

Expected: FAIL at the missing adapter entry point.

- [ ] **Step 3: Implement one bounded pipeline**

Implement:

```text
read one bounded event
-> validate frozen DEV-246 host fields
-> normalize completed Bash result
-> route with production policy
-> invoke captured plugin-local bridge once
-> validate one terminal envelope
-> encode exact DEV-246 replacement
-> write one hook response
```

The bridge command is resolved beneath `$PLUGIN_ROOT/runtime/apple-foundation-models-bridge`; reject traversal, symlinks escaping the root, extra stdout values, stderr leakage, and executable drift. Preserve the original only in process memory until replacement succeeds.

- [ ] **Step 4: Prove fallback and privacy**

Assert that every non-applied path produces no replacement field, never serializes the original result into feedback/evidence, and cannot trigger a second Apple attempt or parent turn.

- [ ] **Step 5: Run focused tests and confirm GREEN**

Expected: all adapter tests PASS offline with fake policy/bridge dependencies.

- [ ] **Step 6: Commit the adapter**

```bash
git add runtime/codex-adapter/codex_diagnostic_condensation.py \
  tests/test_codex_runtime_adapter.py
git commit -m "feat: implement Codex diagnostic condensation hook"
```

### Task 3: Generate a Codex-only plugin payload

**Files:**
- Create: `plugins/apple-foundation-models-handoff/hooks/codex/hooks.json`
- Modify: `plugins/apple-foundation-models-handoff/metadata/codex-interface.json`
- Modify: `scripts/sync_generated_artifacts.py`
- Modify: `CLAUDE.md`
- Modify: `tests/test_plugin_contract.py`
- Generate: `AGENTS.md`
- Generate: `.agents/plugins/marketplace.json`
- Generate: `plugins/apple-foundation-models-handoff/.codex-plugin/plugin.json`
- Generate: plugin-local adapter and Swift production mirror files

- [ ] **Step 1: Write failing generation/ownership tests**

Require:

```text
Codex manifest hooks == ./hooks/codex/hooks.json
Claude manifest has no hooks
default hooks/hooks.json absent
generated hook scripts byte-match canonical root adapter sources
generated Swift Package.swift and Sources byte-match DEV-143 production inputs
generated payload excludes Tests, fixtures, docs, plans, and research
five positive skills plus one router remain unchanged
```

- [ ] **Step 2: Run generator and plugin tests; confirm RED**

```bash
python3 scripts/sync_generated_artifacts.py --check
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_plugin_contract -v
```

Expected: FAIL on absent Codex hook/runtime surfaces and stale no-runtime assertions.

- [ ] **Step 3: Add canonical hook config and metadata**

Register only `PostToolUse` with matcher `Bash`. The command invokes the generated adapter under `$PLUGIN_ROOT`. Encode the passing DEV-246 contract version/hash in `codex-interface.json`; reject generation if DEV-246 evidence is absent or not passing.

- [ ] **Step 4: Extend the generator**

Make `--write` deterministically copy only production files and generate the Codex manifest hook field. Make `--check` fail on drift, unexpected payload entries, external symlinks, missing executable inputs, or a nonpassing DEV-246 contract.

- [ ] **Step 5: Update canonical guidance**

Edit `CLAUDE.md` to state precisely that Codex has one generated runtime hook/bridge payload while Claude execution remains owner-deferred and hook-free. Run the generator; never edit `AGENTS.md` directly.

- [ ] **Step 6: Run generation and plugin tests; confirm GREEN**

```bash
python3 scripts/sync_generated_artifacts.py --write
python3 scripts/sync_generated_artifacts.py --check
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_plugin_contract tests.test_codex_runtime_adapter -v
```

Expected: PASS; a second `--write` creates no diff.

- [ ] **Step 7: Commit generated integration**

```bash
git add CLAUDE.md AGENTS.md .agents/plugins/marketplace.json \
  scripts/sync_generated_artifacts.py tests/test_plugin_contract.py \
  plugins/apple-foundation-models-handoff
git commit -m "feat: package Codex-only Apple runtime"
```

### Task 4: Prove installed-plugin activation on exact Codex

**Files:**
- Create: `tests/e2e/codex_runtime_activation.py`
- Create: `docs/research/evidence/dev-144-codex-runtime.json`
- Modify: `tests/test_codex_runtime_adapter.py`

- [ ] **Step 1: Add fake-host activation tests**

Require captured executable/version before and after, isolated `CODEX_HOME`, marketplace registration, plugin install/add, explicit hook trust, fresh task, one selected row, decline rows, bridge failure rows, and cleanup.

- [ ] **Step 2: Run focused tests and confirm RED**

Expected: FAIL because the E2E harness does not exist.

- [ ] **Step 3: Implement the normalized harness**

Use synthetic/hash-bound stimuli only. Persist schema/version/hash/status, hook count, bridge count, replacement result, original-absence result, added-turn count, and stable reason. Exclude raw prompts, tool results, compact text, responses, paths, configuration, and traces.

- [ ] **Step 4: Run the exact-host row**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tests/e2e/codex_runtime_activation.py \
  --codex-executable "<captured-codex-path>" \
  --output docs/research/evidence/dev-144-codex-runtime.json
```

Expected: PASS only when the installed trusted plugin reproduces the DEV-246 boundary with the real DEV-143 bridge. Missing Apple/session prerequisites are BLOCKED, never mocked or passed.

- [ ] **Step 5: Run the complete issue gate**

```bash
python3 scripts/sync_generated_artifacts.py --write
python3 scripts/sync_generated_artifacts.py --check
swift test --package-path runtime/apple-foundation-models-bridge
swift build --package-path runtime/apple-foundation-models-bridge
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests -p 'test_*.py' -v
git diff --check
git status --short
```

Expected: deterministic gates PASS; exact-host/live activation PASS or truthful BLOCKED; status contains only DEV-144 paths.

- [ ] **Step 6: Sol review and dependency handoff**

Sol reviews the DEV-246 contract use, generator ownership, Claude exclusion, replacement/fallback semantics, privacy, and exact-host evidence. Merge only after green CI and passing required live evidence; then synchronize `main`, prove clean state, and unblock DEV-139.

