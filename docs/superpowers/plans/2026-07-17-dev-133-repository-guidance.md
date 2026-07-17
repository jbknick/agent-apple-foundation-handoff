# DEV-133 Repository Guidance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:subagent-driven-development` to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish one canonical provider-neutral repository guide and a
deterministically generated, bounded root Codex adapter that both hosts can use
to answer local-development and generated-file questions without contradictory
instructions.

**Architecture:** `CLAUDE.md` is the only authored repository-guidance source.
One delimited section inside it is the canonical adapter input; the Python
standard-library sync entry point extracts that section and writes or checks
the root `AGENTS.md`. Unit tests own deterministic generation, drift, size,
privacy, placement, link, and command contracts. Fresh Claude Code and Codex
read-only sessions supply separately labelled host proof; their raw responses
remain transient.

**Tech Stack:** Markdown, Python 3 standard library, `unittest`, Claude Code
2.1.91, Codex CLI 0.144.5, Git.

## Global Constraints

- Start from reviewed DEV-132 head
  `ca767a0c50e1b527fed5c87e0922bf51cf655295` on
  `codex/dev-133-repository-guidance`.
- Linear decision source is DEV-133 comment
  `973b4feb-4832-4482-85de-228d17839ace`; inherited corrections in all prior
  DEV-133 comments remain binding.
- `CLAUDE.md` is authored canonical guidance. `AGENTS.md` is generated and must
  never be edited directly.
- Create exactly one root `AGENTS.md`; create no nested `AGENTS.md` and no
  symlinked guidance.
- Initialize only the approved shared entry point
  `scripts/sync_generated_artifacts.py`; DEV-135 will extend that same script
  for metadata generation.
- The script uses Python 3 standard library only and supports exact `--write`
  and `--check` modes.
- Keep the generated adapter at or below 100 lines and 8192 UTF-8 bytes, and
  smaller than the canonical guide. It must be self-contained for repository
  probes without duplicating the full guide.
- Preferred plugin source `./` remains conditional on DEV-135/139 cache and
  real-host proof. Approved fallback is
  `./plugins/apple-foundation-models-handoff`; no external symlink is allowed.
- Repository-only fixtures, tests, research, docs, and private state must be
  absent from effective cached plugin payload content and must not be exposed
  as plugin capabilities.
- Generated Codex manifest and marketplace paths are planned outputs only in
  DEV-133; do not create or edit them.
- Use exact executed Apple labels `compiled_sdk_26_5` and
  `interface_verified_sdk_26_5`; “SDK 26.x” is an architecture-family boundary,
  not an executed evidence label.
- Apple API truth comes only from current official Apple material, installed
  SDK interfaces, WWDC material, and Apple-owned repositories. Structural
  reference repositories are never Apple API authority.
- Do not add Apple tutorials, Swift examples, complete skill workflows,
  manifests, marketplaces, skill/reference content, hooks, MCP, commands,
  agents, apps, dependencies, runtime packages, release, publishing, tagging,
  merging, or unrelated repository conventions.
- Host rows capture one executable before operations, require Claude Code
  `2.1.91` or Codex `0.144.5`, use it throughout, and recheck resolution/version.
  Initial absence or mismatch is `blocked`; post-capture drift is `fail`.
- Never commit literal private absolute or executable paths, raw `PATH`, raw host
  diagnostics, raw prompts/responses/reasoning/tool content, credentials,
  private configuration, real user/third-party data, `.trace`, or `.xcresult`.
- Version output is prerequisite-only. Repository guidance answers and plugin
  discovery are structural evidence, not plugin capability proof.
- Missing pre-commit, Markdown, host, authentication, automation, SDK, or
  hardware prerequisites are explicit blockers, never false passes.
- Do not push, create/edit a PR, merge, tag, publish, release, or move DEV-133
  beyond In Progress. Root owns publication after independent review.

## Exact DEV-133 Path Set

The intended final diff contains only:

```text
AGENTS.md
CLAUDE.md
docs/research/evidence/dev-133-repository-guidance-e2e.md
docs/superpowers/plans/2026-07-17-dev-133-repository-guidance.md
scripts/sync_generated_artifacts.py
tests/test_repository_guidance.py
```

Ignored `.superpowers/sdd/**` briefs, reports, packages, and progress records
remain untracked scratch artifacts.

---

### Task 1: Plan the issue atomically

**Files:**

- Create: `docs/superpowers/plans/2026-07-17-dev-133-repository-guidance.md`

**Interfaces:**

- Consumes: DEV-133 decision comment
  `973b4feb-4832-4482-85de-228d17839ace` and DEV-132 canonical architecture.
- Produces: exact implementation, test, host-proof, and commit boundaries for
  Tasks 2 and 3.

- [ ] **Step 1: Verify the plan is complete and private**

Run:

```bash
set -e
plan=docs/superpowers/plans/2026-07-17-dev-133-repository-guidance.md
test -s "$plan"
test -z "$(rg -n -e 'T(BD)|TO(DO)|FIX(ME)|fill in detai(ls)|implement lat(er)' \
  "$plan" || true)"
private_path_re='/(Us[e]rs|ho[m]e)/'
test -z "$(rg -n -e "$private_path_re" "$plan" || true)"
git diff --check -- "$plan"
```

Expected: exit `0`; both searches print nothing.

- [ ] **Step 2: Commit the plan alone**

```bash
git add docs/superpowers/plans/2026-07-17-dev-133-repository-guidance.md
git diff --cached --check
test "$(git diff --cached --name-only)" = \
  docs/superpowers/plans/2026-07-17-dev-133-repository-guidance.md
git commit -m 'docs(DEV-133): plan repository guidance'
```

Expected: one commit containing the plan only.

### Task 2: Add canonical guidance and deterministic adapter generation with TDD

**Files:**

- Create: `tests/test_repository_guidance.py`
- Create: `CLAUDE.md`
- Create: `scripts/sync_generated_artifacts.py`
- Generate: `AGENTS.md`

**Interfaces:**

- Consumes: the adapter delimiters
  `<!-- BEGIN GENERATED AGENTS ADAPTER -->` and
  `<!-- END GENERATED AGENTS ADAPTER -->` in `CLAUDE.md`.
- Produces: `render_agents(canonical_text: str) -> str`,
  `synchronize(root: pathlib.Path, write: bool) -> bool`, and CLI modes
  `--write`/`--check`.
- `synchronize(..., write=False)` returns `True` only for an exact byte match.
  Check-mode mismatch prints one normalized relative-path diagnostic and exits
  `1`; write mode writes UTF-8 with stable LF newline and exits `0`.

- [ ] **Step 1: Write the failing guidance tests first**

Create `tests/test_repository_guidance.py` with `unittest` cases that:

```python
class RepositoryGuidanceTests(unittest.TestCase):
    def test_generated_agents_matches_canonical_adapter_exactly(self): ...
    def test_check_mode_passes_for_the_tracked_adapter(self): ...
    def test_write_mode_is_idempotent_in_an_isolated_root(self): ...
    def test_check_mode_rejects_isolated_generated_drift(self): ...
    def test_adapter_is_bounded_and_smaller_than_canonical(self): ...
    def test_only_one_root_agents_file_exists(self): ...
    def test_guidance_names_canonical_generated_and_non_editable_paths(self): ...
    def test_guidance_commands_and_markdown_links_resolve(self): ...
    def test_guidance_preserves_plugin_payload_and_host_boundaries(self): ...
    def test_guidance_contains_no_literal_private_paths_or_placeholders(self): ...
```

The isolated write/drift tests copy only `CLAUDE.md` into a
`tempfile.TemporaryDirectory`; they never mutate the tracked `AGENTS.md`.

- [ ] **Step 2: Run RED and prove the missing production interface is the cause**

Run:

```bash
set +e
PYTHONDONTWRITEBYTECODE=1 \
  python3 -m unittest discover -s tests -p 'test_*.py' -v \
  > "$(mktemp)" 2>&1
rc=$?
set -e
test "$rc" -ne 0
test ! -e scripts/sync_generated_artifacts.py
test ! -e CLAUDE.md
test ! -e AGENTS.md
printf 'DEV133_GUIDANCE_RED rc=%s reason=production_interface_missing\n' "$rc"
```

Expected: normalized `DEV133_GUIDANCE_RED` with nonzero status because the
canonical source/generator/generated output do not yet exist.

- [ ] **Step 3: Implement the minimal canonical guide and generator**

Create `CLAUDE.md` with:

- a canonical-authority statement;
- one delimited adapter section containing the concise repository contract;
- authored/generated path ownership and the no-direct-edit rule;
- exact current sync/check and `unittest` commands;
- the five skill names and direct progressive-disclosure rule without copying
  workflow bodies;
- Apple authority, SDK label, compile/blocker, and no-tutorial rules;
- root/fallback placement and effective-payload exclusion;
- captured-executable/version, normalized evidence, security, and privacy rules;
- release/non-action rules and links to the DEV-132 design/decision record; and
- a short Claude-only local-development note outside the adapter section.

Create `scripts/sync_generated_artifacts.py` with only Python standard-library
imports. It must require one occurrence of each delimiter, reject reversed or
empty sections, render a fixed generated header plus the exact adapter body,
resolve the repository root from the script location, support mutually
exclusive `--write`/`--check`, and expose the interfaces above.

- [ ] **Step 4: Generate `AGENTS.md`; never author it directly**

Run:

```bash
python3 scripts/sync_generated_artifacts.py --write
python3 scripts/sync_generated_artifacts.py --check
```

Expected: write reports `updated AGENTS.md`; check reports
`generated artifacts are synchronized` and both exit `0`.

- [ ] **Step 5: Run GREEN and all deterministic guidance gates**

Run:

```bash
set -e
PYTHONDONTWRITEBYTECODE=1 \
  python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/sync_generated_artifacts.py --check
git diff --check
test "$(find . -name AGENTS.md -type f | wc -l | tr -d ' ')" -eq 1
test -z "$(find . -type d -name '__pycache__' -print -quit)"
test -z "$(find . -type f -name '*.pyc' -print -quit)"
```

Expected: 10 guidance tests pass, generation is synchronized, one root adapter
exists, and no repository bytecode/cache artifact exists.

- [ ] **Step 6: Re-run inherited deterministic regressions**

Run:

```bash
set -e
PYTHONDONTWRITEBYTECODE=1 \
  python3 -m unittest discover -s fixtures/dev-131/tests -p 'test_*.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 fixtures/dev-131/proof_runner.py
artifact_dir="$(mktemp -d)"
swiftc -warnings-as-errors -parse-as-library \
  fixtures/dev-130/HandoffSecurityPolicy.swift \
  fixtures/dev-130/AdversarialScenarios.swift \
  -o "$artifact_dir/dev130-adversarial"
"$artifact_dir/dev130-adversarial" > "$artifact_dir/output"
diff -u fixtures/dev-130/expected-output.txt "$artifact_dir/output"
rg -q '^SUMMARY passed=7 failed=0$' "$artifact_dir/output"
```

Expected: DEV-131 reports 26 passing tests and 11/11 proof-runner oracle
matches; DEV-130 matches the golden file with 7/0 summary.

- [ ] **Step 7: Commit the reviewed green change atomically**

```bash
git add CLAUDE.md AGENTS.md scripts/sync_generated_artifacts.py \
  tests/test_repository_guidance.py
git diff --cached --check
git diff --cached --name-only | sort > "$(mktemp)"
git commit -m 'feat(DEV-133): add generated repository guidance'
```

Expected: only the four Task 2 paths are committed.

### Task 3: Run fresh-host repository E2E and record safe evidence

**Files:**

- Create: `docs/research/evidence/dev-133-repository-guidance-e2e.md`

**Interfaces:**

- Consumes: canonical `CLAUDE.md`, generated `AGENTS.md`, captured Claude Code
  2.1.91/Codex 0.144.5 executables, and a shared repository-probe contract.
- Produces: normalized host rows and assertions only. Raw prompts, responses,
  diagnostics, executable paths, configuration, and session data remain in
  untracked `mktemp` storage.

- [ ] **Step 1: Define one semantic repository probe without embedding answers**

Use a prompt that asks each fresh host to return machine-readable fields for:

```text
canonical guidance path
generated/non-editable paths
generation/check command
repository test command
planned plugin location and fallback
response to a request to edit a generated Codex manifest
whether structural guidance proves plugin capability
```

The prompt must not state the expected values. Validate the returned fields
against the tracked guidance after the session.

- [ ] **Step 2: Run the Claude row read-only from the repository root**

Capture `claude_bin="$(command -v claude)"`, validate the strict exact version,
then invoke only `"$claude_bin"`:

```bash
"$claude_bin" --print --no-session-persistence \
  --permission-mode plan --output-format json \
  --json-schema "$probe_schema" "$probe_prompt"
```

Keep output transient, validate the semantic fields, recheck executable
resolution/version, and emit only:

```text
probe=claude-repository-guidance version=2.1.91 status=pass assertions=7
```

If binary/version/auth/model/session/automation is unavailable before the
semantic probe, emit `blocked` with a stable reason. Post-capture drift is
`fail`. Never substitute the alternate Claude 2.1.140 binary.

- [ ] **Step 3: Run the Codex row read-only from the repository root**

Capture `codex_bin="$(command -v codex)"`, validate the strict exact version,
then invoke only `"$codex_bin"`:

```bash
"$codex_bin" exec --ephemeral --sandbox read-only --json \
  --output-last-message "$codex_result" "$probe_prompt"
```

Keep the event stream and last message transient, validate the same seven
semantic fields, recheck resolution/version, and emit only:

```text
probe=codex-repository-guidance version=0.144.5 status=pass assertions=7
```

Missing binary/version/auth/model/session/automation is `blocked`; post-capture
drift is `fail`. Repository answers remain structural evidence only.

- [ ] **Step 4: Probe repository validation prerequisites honestly**

Run and record normalized statuses for:

```bash
python3 scripts/sync_generated_artifacts.py --check
PYTHONDONTWRITEBYTECODE=1 \
  python3 -m unittest discover -s tests -p 'test_*.py' -v
command -v pre-commit
command -v markdownlint
```

The first two must pass. Missing `pre-commit` or `markdownlint` is `blocked`,
not a repository pass and not a reason to add a dependency in DEV-133.

- [ ] **Step 5: Write only normalized E2E evidence**

Create `docs/research/evidence/dev-133-repository-guidance-e2e.md` containing:

- exact issue, branch, base/head, date, and four source artifact hashes;
- the seven semantic assertions and per-host normalized status/count;
- captured normalized `<host-path>` identity plus exact strict version;
- generator/test/regression results and counts;
- pre-commit/Markdown prerequisite status;
- scope/privacy/cache/cleanliness results; and
- explicit nonclaims: no plugin metadata/loading/activation/reference/model
  capability, no Apple runtime/device/Xcode proof, and no release action.

Do not include raw host responses, prompt text, reasoning, paths, `PATH`, raw
diagnostics, session IDs, credentials, configuration, `.trace`, or `.xcresult`.

- [ ] **Step 6: Commit evidence alone**

```bash
git add docs/research/evidence/dev-133-repository-guidance-e2e.md
git diff --cached --check
test "$(git diff --cached --name-only)" = \
  docs/research/evidence/dev-133-repository-guidance-e2e.md
git commit -m 'test(DEV-133): record repository guidance E2E'
```

Expected: only the normalized evidence path is committed.

## Final Verification and Handoff

Invoke `superpowers:verification-before-completion`, then rerun from the exact
final head:

```bash
set -euo pipefail
base=ca767a0c50e1b527fed5c87e0922bf51cf655295
git merge-base --is-ancestor "$base" HEAD
git diff --check "$base"..HEAD
python3 scripts/sync_generated_artifacts.py --check
PYTHONDONTWRITEBYTECODE=1 \
  python3 -m unittest discover -s tests -p 'test_*.py' -v
PYTHONDONTWRITEBYTECODE=1 \
  python3 -m unittest discover -s fixtures/dev-131/tests -p 'test_*.py' -v
test "$(find . -name AGENTS.md -type f | wc -l | tr -d ' ')" -eq 1
test -z "$(find . -type d -name '__pycache__' -print -quit)"
test -z "$(find . -type f -name '*.pyc' -print -quit)"
test -z "$(git status --short)"
```

Also rerun the DEV-130 golden command, both fresh-host semantic probes, static
private-path/raw-evidence scans, the exact six-path allowlist, and a detached
exact-head verification. Obtain a fresh task spec/quality review and a fresh
whole-branch review with zero unresolved Critical, Important, or Minor
findings. If a gate fails, invoke `superpowers:systematic-debugging`, establish
root cause, make one narrow correction commit, rerun affected and full gates,
and obtain re-review.

After proof, attach one DEV-133 Linear evidence comment with decision and
propagation comment IDs, ordered commits, exact commands/counts, normalized
host results, blockers/nonclaims, hashes, review verdicts, exact scope, and
clean status. Leave DEV-133 In Progress. Do not push or create/edit a PR.
