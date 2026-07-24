# DEV-141 Codex Final Acceptance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to execute this acceptance plan task-by-task. Do not repair production behavior in this issue.

**Goal:** Produce an independent Codex-only regression, privacy, evidence-integrity, and release-readiness verdict for the completed Apple Foundation Models runtime.

**Architecture:** Add a read-only acceptance harness that verifies merged-tree hashes, runs deterministic gates, validates required live evidence and release arithmetic, audits blockers/Linear state, and emits one normalized `pass`, `blocked`, or `fail` record. Any product defect returns to its owning issue; this issue does not patch it.

**Tech Stack:** Python 3 standard library, Swift Package Manager, Codex CLI `0.145.0`, repository generator, Git, normalized JSON evidence.

## Global Constraints

- Prerequisite: DEV-140 is merged and `main` is synchronized and clean.
- Acceptance scope is Codex plugin runs with local Apple Foundation Models only.
- Required predecessors are DEV-246, DEV-143, DEV-144, DEV-139, and DEV-140. DEV-145 is canceled. DEV-133 remains separate owner-deferred debt and is reported but does not silently become runtime evidence.
- The harness is read-only with respect to production code, plugin metadata, runtime artifacts, and predecessor evidence.
- A missing/mismatched hash, host/version drift, nonpassing required live row, incomplete 24-pair/48-arm matrix, provider-usage gap, correctness/privacy failure, extra parent turn, unresolved in-chain blocker, dirty tree, or stale generated artifact prevents `pass`.
- `blocked` is reserved for a missing approved prerequisite/environment; deterministic invariant failures are `fail`.
- Do not claim release, marketplace publication, tag, push, or merge from this issue. Those actions require separate authority.
- Persist no raw prompts, commands, results, model responses, reasoning, credentials, private paths, traces, transcripts, `.xcresult`, or environment dumps.

---

## File Structure

- Create `fixtures/dev-141/final_acceptance.py` — closed evidence loader, hash verifier, arithmetic checker, and verdict serializer.
- Create `tests/test_dev_141_acceptance.py` — deterministic verdict and tamper tests.
- Create `docs/research/evidence/dev-141-final-acceptance.json` — normalized final verdict.
- Create `docs/research/dev-141-final-acceptance.md` — scope, evidence table, blockers, and release-readiness interpretation.

### Task 1: Define the closed acceptance manifest

**Files:**
- Create: `fixtures/dev-141/final_acceptance.py`
- Create: `tests/test_dev_141_acceptance.py`

- [ ] **Step 1: Write failing manifest and verdict tests**

Require exact predecessor evidence paths and SHA-256s, Codex version, SDK labels, plugin identity, 24/48 counts, zero correctness/privacy failures, zero extra turns, provider-use result, documentation test result, generated-state result, clean-tree result, and Linear blocker audit.

```python
def test_all_required_evidence_produces_pass(self):
    verdict = acceptance.evaluate(valid_manifest())
    self.assertEqual(verdict["status"], "pass")
    self.assertEqual(verdict["requiredPairCount"], 24)
    self.assertEqual(verdict["requiredArmCount"], 48)
```

Add one test per blocker/failure plus unknown-key, duplicate-key, evidence tamper, stale head, and canceled DEV-145 accidentally reintroduced.

- [ ] **Step 2: Run focused tests and confirm RED**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_dev_141_acceptance -v
```

Expected: FAIL because the acceptance module does not exist.

- [ ] **Step 3: Implement strict evidence loading and verdict precedence**

Use precedence:

```text
schema/hash/invariant/privacy/correctness failure -> fail
missing host/SDK/Apple/direct-boundary prerequisite -> blocked
all required evidence and repository/Linear gates pass -> pass
```

Reject unexpected files, status values, issue identities, counts, or hashes.

- [ ] **Step 4: Run focused tests and confirm GREEN**

Expected: PASS offline.

- [ ] **Step 5: Commit the acceptance harness**

```bash
git add fixtures/dev-141/final_acceptance.py tests/test_dev_141_acceptance.py
git commit -m "test: define Codex final acceptance gate"
```

### Task 2: Execute merged-tree regression and evidence audit

**Files:**
- Create: `docs/research/evidence/dev-141-final-acceptance.json`

- [ ] **Step 1: Confirm exact baseline**

```bash
git fetch origin
git status --short
git rev-parse HEAD
git rev-parse origin/main
git merge-base --is-ancestor HEAD origin/main
```

Expected: clean tree and the intended synchronized merged baseline. Record only normalized commit hashes.

- [ ] **Step 2: Run deterministic repository gates**

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

Expected: all PASS and no generated drift or dirty state.

- [ ] **Step 3: Validate predecessor evidence**

Run each predecessor verifier in read-only mode, then:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 fixtures/dev-141/final_acceptance.py \
  --verify-predecessors \
  --output docs/research/evidence/dev-141-final-acceptance.json
```

Expected: exact hashes/statuses accepted; any missing/tampered/nonpassing required evidence returns blocked/fail.

- [ ] **Step 4: Audit live Linear state**

Read back DEV-246, DEV-143, DEV-144, DEV-139, DEV-140, DEV-141, DEV-145, and DEV-133. Verify the active chain is completed through DEV-140, DEV-145 is canceled/outside the chain, DEV-133 is separately described, and every merged code issue has a PR/commit/evidence link. Do not mutate Linear during the audit.

- [ ] **Step 5: Run privacy and evidence scans**

```bash
rg -n '/Users/|/home/|authorization|rawPrompt|rawResult|responseText|reasoning|transcript|\\.trace|\\.xcresult' \
  docs/research/evidence/dev-246-codex-result-replacement.json \
  docs/research/evidence/dev-143-bridge.json \
  docs/research/evidence/dev-144-codex-runtime.json \
  docs/research/evidence/dev-139-codex-runtime.json \
  docs/research/evidence/dev-141-final-acceptance.json
```

Expected: no unsafe committed value.

### Task 3: Record the independent release-readiness decision

**Files:**
- Create: `docs/research/dev-141-final-acceptance.md`
- Modify: `docs/research/evidence/dev-141-final-acceptance.json`

- [ ] **Step 1: Write the evidence table**

For each predecessor list issue, artifact path, SHA-256, required status, observed status, host/SDK label, and acceptance result. Include DEV-133 as separate owner-deferred debt, never as a passing runtime prerequisite.

- [ ] **Step 2: Serialize the final verdict**

Run the harness again after the narrative is complete. `pass` requires every deterministic and live gate above; otherwise preserve the exact `blocked` or `fail` reason.

- [ ] **Step 3: Request independent Sol review**

Sol rechecks architecture conformance, exact-host evidence, Apple-only routing, fallback correctness, privacy, arithmetic, documentation claims, blocker graph, and clean state. Any required fix returns to its owning predecessor and triggers re-review; DEV-141 does not patch it.

- [ ] **Step 4: Run final clean-state proof**

```bash
python3 scripts/sync_generated_artifacts.py --check
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests -p 'test_*.py' -v
git diff --check
git status --short
```

Expected: PASS; status contains only DEV-141 evidence/narrative paths before commit and is clean after commit.

- [ ] **Step 5: Close without unauthorized release actions**

Attach the normalized verdict, merged PR links, commit hashes, and required evidence to Linear. Mark DEV-141 Done only on `pass`. On `blocked` or `fail`, keep it open with the exact owner/action. Do not push, merge, tag, publish, or release unless separately authorized.
