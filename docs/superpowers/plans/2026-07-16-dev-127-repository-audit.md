# DEV-127 Repository Architecture Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a source-grounded current-fork architecture report and reproducible host-loading evidence without creating plugin implementation artifacts.

**Architecture:** The command transcript is the evidence layer; the architecture report consumes it and separates authoritative fork facts, pinned upstream reference observations, not-yet-established decisions, and explicit blockers. Upstream bstack is comparison material only.

**Tech Stack:** Git, Bash, GitHub CLI, rg, jq, Claude Code CLI 2.1.91,
Codex CLI 0.144.5, Apple Swift toolchain (`swiftc`), `xcodebuild` (host
availability/version check), Markdown.

## Global Constraints

- Treat the current fork as authoritative and do not import upstream behavior.
- Modify only DEV-127 design, plan, report, and evidence documentation.
- Do not create or modify guidance, plugin, manifest, marketplace, generator, schema, test, runtime, or release artifacts.
- Classify every claim as established, reference only, not established, or blocked.
- Do not claim a Claude-canonical/Codex-generated model exists in the current fork.
- Use temporary isolated host configuration directories; do not mutate user-level Claude Code or Codex configuration.
- Do not edit generated Codex artifacts.

---

## File map

- `docs/superpowers/specs/2026-07-16-dev-127-repository-audit-design.md`: approved audit design; already committed.
- `docs/superpowers/plans/2026-07-16-dev-127-repository-audit.md`: this execution plan.
- `docs/research/evidence/dev-127-command-transcript.md`: normalized command evidence with exit statuses and redacted temporary paths.
- `docs/research/dev-127-repository-architecture.md`: durable current-fork report and downstream constraint table.

### Task 1: Capture authoritative, upstream-reference, and cross-host evidence

**Files:**
- Create: `docs/research/evidence/dev-127-command-transcript.md`

**Interfaces:**
- Consumes: authoritative fork commit `7ec92734127236e29ab88d66c1b41f663149ce0e`.
- Produces: evidence for the report under the headings `Authoritative fork`, `Pinned upstream reference`, `Host tooling`, `Claude Code isolated loading`, and `Codex isolated loading`.

- [ ] **Step 1: Verify the evidence artifact does not pre-exist**

Run:

```bash
test ! -e docs/research/evidence/dev-127-command-transcript.md
```

Expected: exit 0.

- [ ] **Step 2: Capture the authoritative repository inventory**

Run:

```bash
git rev-parse HEAD
git remote -v
git ls-tree -r --name-only 7ec92734127236e29ab88d66c1b41f663149ce0e
git log --oneline --decorate -2
for path in AGENTS.md CLAUDE.md package.json .claude-plugin .codex-plugin .agents plugins schemas scripts tests .github/workflows; do
  if [ -e "$path" ]; then
    printf 'PRESENT %s\n' "$path"
  else
    printf 'ABSENT %s\n' "$path"
  fi
done
```

Expected: the tree contains exactly `COMMERCIAL-LICENSE.md`, `LICENSE`, and `README.md`; every probed architecture path prints `ABSENT`.

- [ ] **Step 3: Inspect the pinned upstream bstack revision without changing the fork**

Run:

```bash
upstream_dir="$(mktemp -d /tmp/dev127-bstack.XXXXXX)"
git clone --quiet https://github.com/baleen37/bstack.git "$upstream_dir"
git -C "$upstream_dir" checkout --quiet 34a04e16b8582d9ddc605563fea1f868732cca4e
git -C "$upstream_dir" rev-parse HEAD
git -C "$upstream_dir" ls-tree -d --name-only HEAD
git -C "$upstream_dir" ls-tree -r --name-only HEAD |
  rg '(^|/)(AGENTS\.md|CLAUDE\.md|plugin\.json|marketplace\.json|.*sync.*|.*test.*|.*schema.*|SKILL\.md)$'
bash "$upstream_dir/scripts/check-codex-artifacts.sh"
```

Expected: exact revision `34a04e16b8582d9ddc605563fea1f868732cca4e`; upstream contains Claude and generated Codex marketplace/manifests, shared `skills/`, schemas, scripts, and BATS tests. The drift check exits 0. Record upstream observations as `Reference only`.

- [ ] **Step 4: Capture installed host versions and the Xcode blocker (historical 2026-07-16/17)**

Run:

```bash
claude --version
codex --version
swift --version
printf 'import FoundationModels\n' | swiftc -typecheck -
xcodebuild -version
```

**Historical expected result (2026-07-16/17):** Claude Code `2.1.91`, Codex
`0.144.5`, and Apple Swift `6.3.2`; the bare `FoundationModels` import exits
0 using the installed Command Line Tools SDK. It does not establish
compilation of absent project examples. `xcodebuild` exits 1 because the active
developer directory is CommandLineTools rather than full Xcode.

The later 2026-07-19 host revalidation is recorded in the evidence and report.
It establishes Xcode host-tool availability and version only, not project
example compilation or behavior.

- [ ] **Step 5: Prove isolated Claude Code discovery and installation using the pinned upstream reference**

Run:

```bash
claude_home="$(mktemp -d /tmp/dev127-claude-home.XXXXXX)"
CLAUDE_CONFIG_DIR="$claude_home" claude plugin validate "$upstream_dir/plugins/me"
CLAUDE_CONFIG_DIR="$claude_home" claude plugin marketplace add "$upstream_dir" --scope user
CLAUDE_CONFIG_DIR="$claude_home" claude plugin list --available --json |
  jq -e '.available[] | select(.pluginId == "me@bstack")'
CLAUDE_CONFIG_DIR="$claude_home" claude plugin install me@bstack --scope user
CLAUDE_CONFIG_DIR="$claude_home" claude plugin list --json |
  jq -e '.[] | select(.id == "me@bstack" and .enabled == true)'
```

Expected: all commands exit 0; validation passes; `me@bstack` is discoverable and enabled inside the temporary configuration directory.

- [ ] **Step 6: Prove isolated Codex discovery and installation using the pinned upstream reference**

Run:

```bash
codex_home="$(mktemp -d /tmp/dev127-codex-home.XXXXXX)"
CODEX_HOME="$codex_home" codex plugin marketplace add "$upstream_dir" --json |
  jq -e 'select(.marketplaceName == "bstack")'
CODEX_HOME="$codex_home" codex plugin list --available --json |
  jq -e '.available[] | select(.pluginId == "me@bstack")'
CODEX_HOME="$codex_home" codex plugin add me@bstack --json |
  jq -e 'select(.pluginId == "me@bstack")'
CODEX_HOME="$codex_home" codex plugin list --json |
  jq -e '.installed[] | select(.pluginId == "me@bstack" and .enabled == true)'
```

Expected: all commands exit 0; `me@bstack` is discoverable and enabled inside the temporary Codex home.

- [ ] **Step 7: Write the normalized command transcript**

Use `apply_patch` to create the transcript with:

- evidence collection range `2026-07-16` through `2026-07-17`;
- every command above, exit status, and normalized result;
- temporary paths replaced with `<temporary-directory>`;
- no tokens, credentials, global configuration values, or raw home paths;
- explicit labels `Established`, `Reference only`, and `Blocked`;
- a note that cross-host loading proves the installed CLIs can load a representative upstream plugin, not that this fork already contains a plugin.

- [ ] **Step 8: Verify and commit the evidence**

Run:

```bash
test -s docs/research/evidence/dev-127-command-transcript.md
rg -q '^## Authoritative fork$' docs/research/evidence/dev-127-command-transcript.md
rg -q '^## Pinned upstream reference$' docs/research/evidence/dev-127-command-transcript.md
rg -q '^## Claude Code isolated loading$' docs/research/evidence/dev-127-command-transcript.md
rg -q '^## Codex isolated loading$' docs/research/evidence/dev-127-command-transcript.md
! rg -n 'gho_|github_pat_|sk-|/Users/[^/ ]+' docs/research/evidence/dev-127-command-transcript.md
git diff --check
git add docs/research/evidence/dev-127-command-transcript.md
git commit -m "docs(DEV-127): record repository audit evidence"
```

Expected: all checks exit 0 and the commit contains only the transcript.

### Task 2: Write and verify the architecture report

**Files:**
- Create: `docs/research/dev-127-repository-architecture.md`

**Interfaces:**
- Consumes: `docs/research/evidence/dev-127-command-transcript.md`.
- Produces: the repository constraints consumed by DEV-132, DEV-133, DEV-135, and DEV-139.

- [ ] **Step 1: Verify the report does not pre-exist**

Run:

```bash
test ! -e docs/research/dev-127-repository-architecture.md
```

Expected: exit 0.

- [ ] **Step 2: Write the report from the evidence**

Use `apply_patch` to create a report with exactly these top-level sections:

1. `Scope and authority`
2. `Executive finding`
3. `Authoritative tracked-file inventory`
4. `Canonical, generated, and adapter classification`
5. `Repository capabilities and gaps`
6. `Pinned upstream bstack comparison`
7. `Cross-host loading evidence`
8. `Downstream decisions still required`
9. `Files downstream must not edit directly`
10. `Validation contract for this revision`

The report must state that the three tracked root documents are canonical
repository documents; there are no generated or adapter artifacts; plugin
shape, runtimes, validation, loading, and generation are not established; the
upstream Claude-to-Codex generator is reference-only; and the current
`Files downstream must not edit directly` list is empty because no generated
files exist. Link the command transcript with a relative Markdown link.

- [ ] **Step 3: Verify semantic coverage**

Run:

```bash
report=docs/research/dev-127-repository-architecture.md
test -s "$report"
headings=(
  'Scope and authority'
  'Executive finding'
  'Authoritative tracked-file inventory'
  'Canonical, generated, and adapter classification'
  'Repository capabilities and gaps'
  'Pinned upstream bstack comparison'
  'Cross-host loading evidence'
  'Downstream decisions still required'
  'Files downstream must not edit directly'
  'Validation contract for this revision'
)
for heading in "${headings[@]}"; do
  rg -q "^## ${heading}$" "$report"
done
test "$(rg '^## ' "$report" | wc -l | tr -d ' ')" -eq 10
rg -q '7ec92734127236e29ab88d66c1b41f663149ce0e' "$report"
rg -q '34a04e16b8582d9ddc605563fea1f868732cca4e' "$report"
rg -q 'not established' "$report"
rg -q 'Reference only' "$report"
rg -q 'evidence/dev-127-command-transcript.md' "$report"
! rg -n 'TBD|TODO|implement later|fill in details' "$report"
git diff --check
```

Expected: every command exits 0.

- [ ] **Step 4: Prove the issue diff is scope-clean in a detached worktree**

Run:

```bash
proof_dir="$(mktemp -d /tmp/dev127-proof.XXXXXX)"
git worktree add --quiet --detach "$proof_dir" HEAD
git -C "$proof_dir" status --short
git -C "$proof_dir" diff --check
git worktree remove "$proof_dir"
git diff --name-only origin/main...HEAD
```

Expected before the report commit: the detached worktree is clean, and the branch diff contains only the design, plan, and evidence files. After the report commit, the final branch diff adds only `docs/research/dev-127-repository-architecture.md`.

- [ ] **Step 5: Commit the report**

Run:

```bash
git add docs/research/dev-127-repository-architecture.md
git commit -m "docs(DEV-127): document repository architecture"
```

Expected: one commit containing only the architecture report.

- [ ] **Step 6: Run the final issue gate**

Run:

```bash
git status --short --branch
git diff --check origin/main...HEAD
git diff --name-only origin/main...HEAD
expected_paths="$(printf '%s\n' \
  'docs/research/dev-127-repository-architecture.md' \
  'docs/research/evidence/dev-127-command-transcript.md' \
  'docs/superpowers/plans/2026-07-16-dev-127-repository-audit.md' \
  'docs/superpowers/specs/2026-07-16-dev-127-repository-audit-design.md' |
  sort)"
actual_paths="$(git diff --name-only origin/main...HEAD | sort)"
test "$actual_paths" = "$expected_paths"
```

Expected: clean branch; exactly four DEV-127 documentation files; no out-of-scope paths.

## Linear and PR handoff

After both tasks pass task review and whole-branch review:

1. Attach a Linear completion comment linking the report, transcript, exact
   commits, commands, results, review verdict, and PR.
2. Push `codex/dev-127-repository-audit`.
3. Open a ready-for-review PR targeting `main` with title
   `DEV-127: audit repository architecture and invariants`.
4. Move DEV-127 to `In Review`; do not merge it.
