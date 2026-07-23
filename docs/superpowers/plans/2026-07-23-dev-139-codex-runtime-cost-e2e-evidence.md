# DEV-139 Codex Runtime and Cost E2E Evidence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to execute this evidence plan task-by-task.

**Goal:** Produce the reproducible Codex-only 24-case/48-arm runtime, correctness, provider-usage, latency, and cost evidence bundle required by the corrected product scope.

**Architecture:** Add a Codex-specific scorer around the frozen DEV-142 corpus without rewriting its historical two-host proof. Execute each case once plugin-off and once plugin-on through the merged installed-plugin path, bind paired arms by corpus and environment identity, and serialize hashes and aggregate arithmetic only.

**Tech Stack:** Python 3 standard library, Codex CLI `0.144.5`, DEV-142 corpus/contracts, DEV-144 installed plugin, `unittest`, SHA-256.

## Global Constraints

- Prerequisite: DEV-144 is merged with passing exact-host and live Apple activation evidence.
- Do not modify `fixtures/dev-142/runtime_contract.py`, `proof_runner.py`, `benchmark-corpus.json`, or their historical 48-pair/96-arm claims.
- Required downstream matrix: 24 corpus cases × 2 modes = 48 arms and 24 valid pairs, all on `codex-cli-0.144.5`.
- Plugin-off and plugin-on arms must share command hash, corpus hash, machine/SDK identity, working-tree head, locale, and environment class.
- Provider usage must be application-owned evidence that Apple was attempted exactly once on selected applied rows and never on ineligible/fallback rows. Model prose is not evidence.
- Passing release arithmetic requires zero correctness failures, zero privacy failures, zero added parent turns, complete pairs, and the unchanged DEV-142 cost/savings floor.
- Commit no raw prompts, commands, tool results, compact summaries, model responses, reasoning, private paths, credentials, environment dumps, traces, transcripts, or `.xcresult`.
- Missing exact host, trust, Apple availability, provider usage, or direct result-visibility evidence is `blocked`.

---

## File Structure

- Create `fixtures/dev-139/README.md` — execution, pairing, cleanup, and privacy rules.
- Create `fixtures/dev-139/proof_runner.py` — Codex-only paired runner and serializer.
- Create `tests/e2e/codex_runtime_cost.py` — exact-host orchestration.
- Create `tests/test_dev_139_codex_runtime_cost.py` — scorer, pairing, blocker, and privacy tests.
- Create `docs/research/evidence/dev-139-codex-runtime.json` — normalized 48-arm/24-pair evidence.
- Create `docs/research/dev-139-codex-runtime.md` — arithmetic and limitations.

### Task 1: Define Codex-only pair and release arithmetic

**Files:**
- Create: `fixtures/dev-139/proof_runner.py`
- Create: `tests/test_dev_139_codex_runtime_cost.py`

- [ ] **Step 1: Write failing arithmetic tests**

Cover exactly 48 arms/24 pairs, duplicate/missing modes, identity mismatch, corpus drift, correctness failure, provider over/under-use, added parent turn, privacy failure, cost-floor miss, and all-pass serialization.

```python
def test_release_requires_24_complete_codex_pairs(self):
    release = proof.score_release(valid_48_arms())
    self.assertEqual(release.required_pairs, 24)
    self.assertEqual(release.valid_pairs, 24)
    self.assertEqual(release.status, "pass")
```

- [ ] **Step 2: Run focused tests and confirm RED**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_dev_139_codex_runtime_cost -v
```

Expected: FAIL because the scorer does not exist.

- [ ] **Step 3: Implement the closed scorer**

Import stable DEV-142 validation/formula helpers where possible, but own Codex-only host counts locally. Serialize arm/pair IDs and SHA-256s, byte/token/cost/latency integers, booleans, stable reasons, and aggregate totals only.

- [ ] **Step 4: Cross-check historical arithmetic**

Add a test proving that applying the new pair formula to the Codex half of the frozen DEV-142 synthetic corpus yields the same per-pair arithmetic while requiring 24 rather than 48 pairs.

- [ ] **Step 5: Run focused tests and confirm GREEN**

Expected: PASS offline.

- [ ] **Step 6: Commit the scorer**

```bash
git add fixtures/dev-139/proof_runner.py tests/test_dev_139_codex_runtime_cost.py
git commit -m "test: define Codex runtime cost evidence"
```

### Task 2: Build exact-host paired orchestration

**Files:**
- Create: `tests/e2e/codex_runtime_cost.py`
- Modify: `tests/test_dev_139_codex_runtime_cost.py`

- [ ] **Step 1: Add failing fake-host tests**

Require strict Codex `0.144.5` capture/recheck, isolated installed plugin, explicit trust, deterministic 24-case order, plugin-off before plugin-on for each case, no retries, deadline handling, cleanup, and drift detection.

- [ ] **Step 2: Run focused tests and confirm RED**

Expected: FAIL on missing orchestrator.

- [ ] **Step 3: Implement the bounded runner**

Use argument vectors and controlled environment. Each arm captures normalized application-owned metrics from the merged DEV-144 runtime and the direct model-boundary proof established by DEV-246. Abort and mark the bundle blocked/fail on drift; never fill a missing arm with synthetic success.

- [ ] **Step 4: Run focused tests and confirm GREEN**

Expected: PASS with fake host; no live generation.

- [ ] **Step 5: Commit orchestration**

```bash
git add tests/e2e/codex_runtime_cost.py \
  tests/test_dev_139_codex_runtime_cost.py
git commit -m "test: orchestrate Codex paired runtime proof"
```

### Task 3: Execute and verify the 48-arm evidence bundle

**Files:**
- Create: `fixtures/dev-139/README.md`
- Create: `docs/research/evidence/dev-139-codex-runtime.json`
- Create: `docs/research/dev-139-codex-runtime.md`

- [ ] **Step 1: Run the captured exact-host matrix**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tests/e2e/codex_runtime_cost.py \
  --codex-executable "<captured-codex-path>" \
  --corpus fixtures/dev-142/benchmark-corpus.json \
  --output docs/research/evidence/dev-139-codex-runtime.json
```

Expected: 48 arms, 24 pairs, and one `pass`, `blocked`, or `fail` release record. A required unavailable prerequisite keeps the issue blocked.

- [ ] **Step 2: Validate evidence and privacy**

```bash
python3 -m json.tool docs/research/evidence/dev-139-codex-runtime.json >/dev/null
PYTHONDONTWRITEBYTECODE=1 python3 fixtures/dev-139/proof_runner.py \
  --verify docs/research/evidence/dev-139-codex-runtime.json
rg -n '/Users/|/home/|authorization|rawPrompt|rawResult|responseText|reasoning|transcript' \
  docs/research/evidence/dev-139-codex-runtime.json
```

Expected: JSON and arithmetic PASS; privacy scan finds no unsafe value.

- [ ] **Step 3: Write the evidence interpretation**

State exact pair counts, correctness, provider use, visibility, added turns, latency, cost/savings arithmetic, blocker status, and limitations. Keep DEV-142 historical claims intact.

- [ ] **Step 4: Run repository gates**

```bash
python3 scripts/sync_generated_artifacts.py --check
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests -p 'test_*.py' -v
git diff --check
git status --short
```

Expected: PASS; status contains only DEV-139 paths.

- [ ] **Step 5: Sol review and handoff**

Sol verifies pair binding, arithmetic, provider-use authority, privacy, host identity, and the release verdict. Merge only with complete passing required evidence; then synchronize `main`, prove clean state, and unblock DEV-140.

