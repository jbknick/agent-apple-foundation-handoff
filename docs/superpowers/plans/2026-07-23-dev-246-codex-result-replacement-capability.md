# DEV-246 Codex Result-Replacement Capability Discovery Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to execute this discovery plan task-by-task. Do not implement production runtime code from this issue.

**Goal:** Prove or block, on the captured Codex CLI `0.144.5`, the exact trusted `PostToolUse` contract required to replace or suppress an original tool result before the next parent-model request.

**Architecture:** Build a repository-only synthetic plugin and a deterministic probe harness. The harness freezes official-manual and plugin hashes, installs the plugin into an isolated `CODEX_HOME`, enables trust, emits unique synthetic sentinels, and inspects only an approved direct model-boundary representation. It serializes one closed `pass`, `blocked`, or `fail` verdict; model prose is never evidence.

**Tech Stack:** Python 3 standard library, Codex CLI `0.144.5`, Codex plugin manifest and lifecycle hooks, `unittest`, SHA-256.

## Global Constraints

- Spec source: `docs/superpowers/specs/2026-07-23-codex-foundation-models-runtime-completion-design.md`.
- DEV-142 is Done. DEV-246 blocks DEV-143 and every downstream runtime issue.
- Capture one explicit Codex executable before the host row, require strict single-line version `0.144.5`, and recheck resolution/version afterward.
- Use an isolated temporary `CODEX_HOME`, marketplace registration, plugin install/add, explicit hook trust, and a fresh task. `codex --plugin-dir` is prohibited.
- The stimulus is synthetic and hash-bound. Do not use real user data, repository secrets, raw prompts, raw model responses, reasoning, private configuration, or live tool output.
- A passing verdict requires direct evidence of the exact next parent-model request boundary: compact sentinel present exactly once, original sentinel absent, and zero additional parent-model turns.
- Hook stdout, `systemMessage`, `continue`, `stopReason`, transcript files, or model acknowledgement alone cannot prove replacement.
- If no approved host interface exposes the model-boundary representation, return `blocked` with reason `model_boundary_not_observable`.
- If the exact host exposes feedback/control but not replacement/suppression, return `blocked` with reason `host_replacement_unavailable`.
- Schema drift, executable drift, version drift, malformed output, sentinel leakage, or invariant failure is `fail`.
- No production plugin, Swift bridge, workflow skill, reference, canonical manifest, generator, or DEV-142 contract is modified.

---

## File Structure

- Create `fixtures/dev-246/README.md` — safe execution, trust, cleanup, and verdict rules.
- Create `fixtures/dev-246/synthetic-plugin/.codex-plugin/plugin.json` — repository-only probe manifest.
- Create `fixtures/dev-246/synthetic-plugin/hooks/codex/hooks.json` — exact `PostToolUse` probe registration.
- Create `fixtures/dev-246/synthetic-plugin/hooks/codex/probe.py` — closed hook-input validator and candidate replacement emitter.
- Create `tests/e2e/codex_result_replacement_probe.py` — exact-host installer, runner, boundary inspector, and serializer.
- Create `tests/test_codex_result_replacement_probe.py` — deterministic unit and fake-host tests.
- Create `docs/research/evidence/dev-246-codex-result-replacement.json` — normalized discovery result.
- Create `docs/research/dev-246-codex-result-replacement.md` — interpretation and downstream contract.

### Task 1: Freeze the verdict schema and synthetic fixture

**Files:**
- Create: `fixtures/dev-246/synthetic-plugin/.codex-plugin/plugin.json`
- Create: `fixtures/dev-246/synthetic-plugin/hooks/codex/hooks.json`
- Create: `fixtures/dev-246/synthetic-plugin/hooks/codex/probe.py`
- Test: `tests/test_codex_result_replacement_probe.py`

**Interfaces:**
- Consumes: documented `PostToolUse` input and the exact candidate output contract under test.
- Produces: a synthetic original sentinel, compact sentinel, and bounded hook response.

- [ ] **Step 1: Write the failing schema tests**

```python
def test_verdict_requires_closed_model_boundary_fields(self):
    verdict = probe.normalize_verdict(self.passing_observation())
    self.assertEqual(verdict["status"], "pass")
    self.assertTrue(verdict["originalAbsentFromNextRequest"])
    self.assertTrue(verdict["compactPresentInNextRequest"])
    self.assertEqual(verdict["additionalParentModelTurns"], 0)

def test_feedback_only_is_blocked(self):
    observation = self.passing_observation()
    observation["boundarySource"] = "hook_stdout"
    self.assertEqual(
        probe.normalize_verdict(observation)["reason"],
        "model_boundary_not_observable",
    )
```

- [ ] **Step 2: Run the focused tests and confirm RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_codex_result_replacement_probe -v
```

Expected: FAIL because the fixture and probe module do not exist.

- [ ] **Step 3: Add the closed synthetic plugin**

Use a manifest with no skills, references, MCP servers, apps, commands, or agents. Register one `PostToolUse` matcher for canonical `Bash`, pointing to:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$PLUGIN_ROOT/hooks/codex/probe.py\""
          }
        ]
      }
    ]
  }
}
```

`probe.py` must reject unknown top-level keys, verify the synthetic marker and digest, and emit only the candidate host response being tested. Never copy the original sentinel into diagnostics, feedback, or evidence.

- [ ] **Step 4: Implement the closed verdict normalizer**

The normalized evidence keys, in order, are:

```text
schemaVersion, issue, status, reason, codexVersion, codexExecutable,
manualSha256, pluginSha256, originalSha256, compactSha256,
boundarySource, originalAbsentFromNextRequest,
compactPresentInNextRequest, additionalParentModelTurns,
hookInvocations, trustConfirmed, cleanupStatus
```

Allow `status` only from `pass`, `blocked`, `fail`; normalize executable identity to `<host-path>` and unavailable observations to `null`.

- [ ] **Step 5: Run the focused tests and confirm GREEN**

Run the Task 1 test command again.

Expected: PASS with no network or Codex process.

- [ ] **Step 6: Commit the fixture/schema checkpoint**

```bash
git add fixtures/dev-246 tests/test_codex_result_replacement_probe.py
git commit -m "test: define Codex replacement capability probe"
```

### Task 2: Implement exact-host capture and isolated installation

**Files:**
- Create: `tests/e2e/codex_result_replacement_probe.py`
- Modify: `tests/test_codex_result_replacement_probe.py`

**Interfaces:**
- Consumes: explicit `--codex-executable`, manual path, synthetic plugin path, and output path.
- Produces: preflight metadata or a normalized blocked/fail verdict before host execution.

- [ ] **Step 1: Add failing preflight tests**

Cover missing executable, non-runnable file, multiline version, path-bearing version, non-`0.144.5` version, manual missing/hash failure, and post-run resolution/version drift.

- [ ] **Step 2: Run the focused tests and confirm RED**

Expected: FAIL on the first missing preflight implementation.

- [ ] **Step 3: Implement capture and isolated lifecycle helpers**

Use `subprocess.run` with argument vectors, `shell=False`, bounded timeouts, a temporary `CODEX_HOME`, and a controlled `PATH`. Commands must follow the repository-approved Codex lifecycle: marketplace registration, plugin install/add, explicit trust, then a fresh task. Persist only normalized exit/status metadata.

- [ ] **Step 4: Add fake-host lifecycle tests**

The fake executable must prove command ordering, isolated home use, one strict version before and after, trust confirmation, and unconditional temporary-directory cleanup on pass, blocked, fail, timeout, and interruption.

- [ ] **Step 5: Run the focused tests and confirm GREEN**

Expected: PASS; no real Codex invocation.

- [ ] **Step 6: Commit exact-host harness**

```bash
git add tests/e2e/codex_result_replacement_probe.py \
  tests/test_codex_result_replacement_probe.py
git commit -m "test: add exact Codex capability harness"
```

### Task 3: Prove the model-boundary invariant or block

**Files:**
- Modify: `tests/e2e/codex_result_replacement_probe.py`
- Modify: `tests/test_codex_result_replacement_probe.py`

**Interfaces:**
- Consumes: one approved direct model-boundary observation from the captured host.
- Produces: a verdict that downstream plans may consume only when `status == "pass"`.

- [ ] **Step 1: Add failing boundary-source tests**

Test these exact outcomes:

```text
direct next-request, original absent, compact present, zero extra turns -> pass
no direct boundary interface -> blocked:model_boundary_not_observable
direct boundary includes original -> blocked:host_replacement_unavailable
direct boundary omits compact -> blocked:host_replacement_unavailable
feedback-only or transcript-only source -> blocked:model_boundary_not_observable
more than one hook or added parent turn -> fail:execution_invariant_failed
```

- [ ] **Step 2: Run the focused tests and confirm RED**

Expected: FAIL because boundary classification is incomplete.

- [ ] **Step 3: Implement boundary classification**

Read only a documented/approved representation tied to the exact provider request. Compare SHA-256 values; never serialize raw content. Do not infer success from the next model response.

- [ ] **Step 4: Run the focused tests and full deterministic suite**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_codex_result_replacement_probe -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests -p 'test_*.py' -v
```

Expected: PASS without a live host.

- [ ] **Step 5: Commit boundary classification**

```bash
git add tests/e2e/codex_result_replacement_probe.py \
  tests/test_codex_result_replacement_probe.py
git commit -m "test: classify Codex replacement evidence"
```

### Task 4: Execute the bounded discovery and publish normalized evidence

**Files:**
- Create: `fixtures/dev-246/README.md`
- Create: `docs/research/evidence/dev-246-codex-result-replacement.json`
- Create: `docs/research/dev-246-codex-result-replacement.md`

- [ ] **Step 1: Capture the approved manual and explicit host**

Resolve the current official Codex manual through the `openai-docs` workflow. Record only its SHA-256. Resolve the intended executable once, verify `0.144.5`, and pass its explicit path to the harness.

- [ ] **Step 2: Run the real isolated probe**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 \
  tests/e2e/codex_result_replacement_probe.py \
  --codex-executable "<captured-codex-path>" \
  --manual "<captured-official-manual-path>" \
  --plugin fixtures/dev-246/synthetic-plugin \
  --output docs/research/evidence/dev-246-codex-result-replacement.json
```

Expected: one normalized `pass`, `blocked`, or `fail` result. `blocked` is the expected safe result when direct next-request visibility or replacement is unavailable; do not turn it into a pass.

- [ ] **Step 3: Run privacy and structure scans**

```bash
python3 -m json.tool \
  docs/research/evidence/dev-246-codex-result-replacement.json >/dev/null
rg -n '/Users/|/home/|BEGIN .*PRIVATE|token=|authorization|rawPrompt|rawResult|responseText' \
  fixtures/dev-246 docs/research/evidence/dev-246-codex-result-replacement.json \
  docs/research/dev-246-codex-result-replacement.md
```

Expected: JSON valid; privacy scan returns no unsafe committed value. Document literal scan examples as code only in the README, not evidence.

- [ ] **Step 4: Write the result interpretation**

Record the exact verdict, reason, hashes, limitations, and downstream action. A `pass` section must freeze the exact observed host input/output field names that DEV-144 may implement. A `blocked` or `fail` section must state that DEV-143 and later issues remain blocked and that architecture returns to Sol/user.

- [ ] **Step 5: Run repository gates**

```bash
python3 scripts/sync_generated_artifacts.py --check
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests -p 'test_*.py' -v
git diff --check
git status --short
```

Expected: generation check and tests PASS; diff check clean; status contains only DEV-246 paths.

- [ ] **Step 6: Request Sol review and close conditionally**

Sol verifies host identity, direct-boundary provenance, hashes, privacy, and verdict arithmetic. If `pass`, link the frozen contract and unblock DEV-143. If `blocked` or `fail`, keep DEV-143 blocked, record the truthful reason in Linear, and stop the runtime chain.

