# DEV-140 Codex Runtime Documentation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this documentation plan task-by-task.

**Goal:** Document the proven Codex-only Apple Foundation Models runtime, installation/trust workflow, local data boundary, verification commands, cost evidence, fallback behavior, and limitations without extending any evidence claim.

**Architecture:** Add one focused runtime guide and a short README entry point. Generate documentation assertions from the merged DEV-246, DEV-143, DEV-144, and DEV-139 evidence identities so commands, host versions, pair counts, and status claims cannot drift silently.

**Tech Stack:** Markdown, Python 3 `unittest`, repository generator/checks, local Codex CLI workflow.

## Global Constraints

- Prerequisite: DEV-139 is merged with complete, passing required evidence.
- Documentation sources are the merged issue plans/specs and normalized evidence JSON, not historical comments or model prose.
- Scope is Codex CLI `0.144.5` only, using Apple Foundation Models locally through the plugin system.
- State clearly that there is no mobile app, Claude runtime adapter, external LLM, PCC, remote fallback, credential, paid service, or network inference.
- Document explicit hook trust, plugin-cache behavior, supported completed `Bash` eligibility, original-result fallback, and exact blocker semantics.
- Do not claim marketplace publication, release, savings percentage, live Apple execution, supported SDK, or replacement capability beyond merged evidence.
- Preserve the historical DEV-142 48-pair/96-arm proof as historical contract evidence; describe the downstream Codex release matrix as 24 pairs/48 arms.
- Do not put private absolute paths, credentials, raw prompts/results/responses, traces, or environment dumps in examples.
- Do not modify runtime behavior from this issue.

---

## File Structure

- Create `docs/codex-runtime.md` — end-to-end user/contributor guide.
- Modify `README.md` — concise Codex runtime overview and link.
- Modify `fixtures/dev-142/README.md` — add only a scoped historical/downstream clarification link.
- Create `tests/test_codex_runtime_documentation.py` — evidence-bound command, link, scope, and forbidden-claim tests.

### Task 1: Bind documentation claims to merged evidence

**Files:**
- Create: `tests/test_codex_runtime_documentation.py`

- [ ] **Step 1: Write failing evidence-bound tests**

Require:

```text
Codex version 0.144.5
Apple Foundation Models only
explicit plugin hook trust
24 pairs / 48 arms
DEV-246 replacement evidence status and hash
DEV-143 live bridge evidence status and hash
DEV-144 activation evidence status and hash
DEV-139 release evidence status and hash
no mobile, Claude runtime, external LLM, PCC, or remote fallback claim
```

Also require every documented command to use repository-relative placeholders rather than private paths.

- [ ] **Step 2: Run the focused tests and confirm RED**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_codex_runtime_documentation -v
```

Expected: FAIL because the guide and README link do not exist.

- [ ] **Step 3: Add evidence loaders and forbidden-claim checks**

Tests must parse the normalized JSON evidence and compare exact version, status, count, and hash values used by the docs. Reject unsupported terms such as `Claude adapter enabled`, `TestFlight`, `remote model fallback`, and unqualified `released`.

- [ ] **Step 4: Re-run focused tests**

Expected: still RED only on missing documentation content.

- [ ] **Step 5: Commit the documentation contract**

```bash
git add tests/test_codex_runtime_documentation.py
git commit -m "test: bind Codex runtime docs to evidence"
```

### Task 2: Write the Codex runtime guide

**Files:**
- Create: `docs/codex-runtime.md`
- Modify: `README.md`
- Modify: `fixtures/dev-142/README.md`

- [ ] **Step 1: Write the guide from verified commands**

Use these sections:

```text
Scope
Prerequisites and exact versions
Marketplace registration and plugin installation
Explicit hook trust
Eligible completed Bash results
Local Apple data flow
Applied and original-result fallback behavior
Deterministic verification
Opt-in live Apple verification
24-pair/48-arm cost evidence
Privacy and retained metadata
Known blockers and limitations
Uninstall/disable behavior
```

Every command must be copied from the passing DEV-144/139 harness workflow and use placeholders such as `<repo>` and `<host-path>`.

- [ ] **Step 2: Add the README entry point**

Describe the plugin as five guidance workflows plus one router and one Codex-only diagnostic-condensation runtime. Link to `docs/codex-runtime.md`; do not imply the runtime is a sixth workflow.

- [ ] **Step 3: Clarify historical DEV-142 evidence**

Add a short note that DEV-142’s two-host 48-pair/96-arm bundle remains historical contract proof while the approved downstream release evidence is Codex-only 24-pair/48-arm DEV-139.

- [ ] **Step 4: Run focused tests and link checks**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_codex_runtime_documentation -v
python3 scripts/sync_generated_artifacts.py --check
```

Expected: PASS.

- [ ] **Step 5: Perform a clean-session walkthrough**

In a fresh isolated Codex home, follow the documented install, trust, deterministic check, live prerequisite check, and uninstall/disable instructions exactly. Record only pass/block status in the PR; do not add new runtime evidence in this issue.

- [ ] **Step 6: Run the complete issue gate**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests -p 'test_*.py' -v
python3 scripts/sync_generated_artifacts.py --check
git diff --check
git status --short
```

Expected: PASS; status contains only DEV-140 documentation/test paths.

- [ ] **Step 7: Sol review and handoff**

Sol compares each claim/command to merged evidence and checks scope language, privacy, and historical distinction. Merge after green CI, synchronize `main`, prove clean state, and unblock DEV-141.

