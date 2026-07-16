# DEV-129 Production Plugin Pattern Comparison Implementation Plan

> Execute with `superpowers:subagent-driven-development`. Use a fresh
> implementer and reviewer for each task.

**Goal:** Verify pinned production Claude Code/Codex structures and publish an
evidence-backed adopt/adapt/reject decision matrix for this fork.

**Stack base:** `origin/codex/dev-128-apple-api-research`

**Design:**
`docs/superpowers/specs/2026-07-17-dev-129-production-patterns-design.md`

**Constraints:** References are structural evidence only. Do not create plugin
files, skills, agents, guidance adapters, generators, dependencies, or runtime
code. Do not claim capability E2E from validation/install/discovery. Use
isolated host configuration directories.

## Commit boundaries

1. `docs(DEV-129): design production pattern research`
2. `docs(DEV-129): plan production pattern research`
3. `docs(DEV-129): record production reference evidence`
4. `docs(DEV-129): compare cross-host production patterns`

Review corrections use narrow follow-up commits. Do not squash a branch that
has downstream dependents.

## Task 1: Record pinned reference and host-workflow evidence

**Files:**

- Create: `docs/research/evidence/dev-129-reference-command-transcript.md`

### Step 1: Prove the transcript is absent

```bash
test ! -e docs/research/evidence/dev-129-reference-command-transcript.md
```

Expected: exit `0`.

### Step 2: Create immutable reference checkouts

Use a new temporary root and check out these exact revisions:

```bash
refs_root="$(mktemp -d /tmp/dev129-refs.XXXXXX)"
git clone --filter=blob:none https://github.com/duyet/codex-claude-plugins.git "$refs_root/duyet"
git -C "$refs_root/duyet" checkout --detach 82de4021a311034a9596e891baf3a8266fb33bf7
git clone --filter=blob:none https://github.com/zeabur/agent-skills.git "$refs_root/zeabur"
git -C "$refs_root/zeabur" checkout --detach 30da8243ef23470be79e02bac50a7e1dee1af12e
git clone --filter=blob:none https://github.com/baleen37/bstack.git "$refs_root/bstack"
git -C "$refs_root/bstack" checkout --detach 34a04e16b8582d9ddc605563fea1f868732cca4e
git clone --filter=blob:none https://github.com/openai/plugins.git "$refs_root/openai-plugins"
git -C "$refs_root/openai-plugins" checkout --detach 11c74d6ba24d3a6d48f54a194cd00ef3beea18f9
git clone --filter=blob:none https://github.com/openai/codex.git "$refs_root/openai-codex"
git -C "$refs_root/openai-codex" checkout --detach 693b8c2ba4396772eeb82ce2982acad19dd960f5
```

Record the temporary root in scratch only. The transcript must normalize it as
`<reference-root>` and record all five `rev-parse HEAD` results.

### Step 3: Inspect exact structural paths

Record `test -e`, `find`, `git ls-tree`, and focused source excerpts that prove:

- root and nested `AGENTS.md`/`CLAUDE.md` strategies;
- Claude/Codex manifests and marketplaces;
- canonical/shared versus mirrored skill trees;
- generator, sync, drift, validator, and workflow paths;
- official Codex plugin `interface`, per-skill `agents/openai.yaml`
  UI/activation metadata, and the root reference-file observation;
- the distinction between documented entry-point requirements, optional rich
  fields, and the pinned official validator's stricter creation policy;
- plugin `interface` fields versus marketplace-only policy/category fields;
- per-skill `agents/openai.yaml` UI/activation metadata versus the unvalidated
  root reference file;
- full loader recognition order and root `.`/`./` marketplace source handling,
  without claiming when root support was introduced;
- precise Claude marketplace/local-path symlink handling; and
- concise skill descriptions plus progressive `references/`/`scripts/`.

Every conclusion in the final report must be traceable to one pinned path.

### Step 4: Run reference-native validation

Run and record:

```bash
bash "$refs_root/duyet/scripts/validate-plugins.sh"

git -C "$refs_root/zeabur" diff --quiet
node "$refs_root/zeabur/scripts/sync-codex-plugin.mjs"
git -C "$refs_root/zeabur" diff --exit-code -- plugins/zeabur .agents/plugins/marketplace.json

bash "$refs_root/bstack/scripts/check-codex-artifacts.sh"

python3 "$refs_root/openai-codex/codex-rs/skills/src/assets/samples/plugin-creator/scripts/validate_plugin.py" \
  "$refs_root/openai-plugins/plugins/build-ios-apps"

set +e
python3 "$refs_root/openai-codex/codex-rs/skills/src/assets/samples/plugin-creator/scripts/validate_plugin.py" \
  "$refs_root/bstack/plugins/me" >/tmp/dev129-openai-bstack-policy.out 2>&1
bstack_policy_rc=$?
python3 "$refs_root/openai-codex/codex-rs/skills/src/assets/samples/plugin-creator/scripts/validate_plugin.py" \
  "$refs_root/duyet/build-ios-apps" >/tmp/dev129-openai-duyet-policy.out 2>&1
duyet_policy_rc=$?
set -e
test "$bstack_policy_rc" -ne 0
test "$duyet_policy_rc" -ne 0
rg -q 'interface.*must be an object' /tmp/dev129-openai-bstack-policy.out
for diagnostic in \
  'field `agents` is not accepted' \
  'field `interface.links` is not accepted' \
  'field `interface.longDescription` must be a non-empty string' \
  'field `interface.defaultPrompt` or `interface.default_prompt` is required'; do
  rg -Fq "$diagnostic" /tmp/dev129-openai-duyet-policy.out
done
```

Expected: native validators and the official example validation exit `0`.
The pinned official validator exits nonzero for bstack and Duyet with the
exact current-policy diagnostics above. Record those expected policy gaps
separately from the references' native validator passes. If a command instead
needs an unavailable dependency, record the exact blocker; do not patch the
reference or weaken validation.

### Step 5: Verify installed host workflows

Record:

```bash
claude --version
claude --help
claude plugin --help
claude plugin validate "$refs_root/bstack/plugins/me"

codex --version
codex plugin --help
codex plugin marketplace --help
set +e
codex --plugin-dir /tmp --help >/tmp/dev129-codex-plugin-dir.out 2>&1
codex_plugin_dir_rc=$?
set -e
test "$codex_plugin_dir_rc" -ne 0
rg -q "unexpected argument.*--plugin-dir" /tmp/dev129-codex-plugin-dir.out
```

The transcript must record that installed Claude `2.1.91` supports session-only
`--plugin-dir`, Codex `0.144.5` rejects it, and relied host features are based
on installed behavior rather than possibly newer documentation.

### Step 6: Run isolated representative loading

Use disposable host homes and the pinned bstack reference:

```bash
claude_home="$(mktemp -d /tmp/dev129-claude.XXXXXX)"
codex_home="$(mktemp -d /tmp/dev129-codex.XXXXXX)"

CLAUDE_CONFIG_DIR="$claude_home" claude plugin marketplace add "$refs_root/bstack" --scope user
CLAUDE_CONFIG_DIR="$claude_home" claude plugin list --available --json | \
  jq -e '.available[] | select(.pluginId == "me@bstack")'
CLAUDE_CONFIG_DIR="$claude_home" claude plugin install me@bstack --scope user
CLAUDE_CONFIG_DIR="$claude_home" claude plugin list --json | \
  jq -e '.[] | select(.id == "me@bstack" and .enabled == true)'

CODEX_HOME="$codex_home" codex plugin marketplace add "$refs_root/bstack" --json | \
  jq -e 'select(.marketplaceName == "bstack")'
CODEX_HOME="$codex_home" codex plugin list --available --json | \
  jq -e '.available[] | select(.pluginId == "me@bstack")'
CODEX_HOME="$codex_home" codex plugin add me@bstack --json | \
  jq -e 'select(.pluginId == "me@bstack")'
CODEX_HOME="$codex_home" codex plugin list --json | \
  jq -e '.installed[] | select(.pluginId == "me@bstack" and .enabled == true)'
```

Expected: all structural load gates exit `0`. Explicitly state that no model
session activated a skill, loaded a reference, or proved output behavior.

### Step 7: Write and validate the transcript

Use `apply_patch` with exactly these top-level sections:

1. `Scope and classifications`
2. `Pinned revisions`
3. `Exact structural path evidence`
4. `Reference-native validation`
5. `Installed host workflow evidence`
6. `Isolated representative loading`
7. `Claims this evidence does not establish`

Run:

```bash
set -e
transcript=docs/research/evidence/dev-129-reference-command-transcript.md
test -s "$transcript"
headings=(
  'Scope and classifications'
  'Pinned revisions'
  'Exact structural path evidence'
  'Reference-native validation'
  'Installed host workflow evidence'
  'Isolated representative loading'
  'Claims this evidence does not establish'
)
for heading in "${headings[@]}"; do rg -q "^## ${heading}$" "$transcript"; done
test "$(rg '^## ' "$transcript" | wc -l | tr -d ' ')" -eq 7
for sha in \
  82de4021a311034a9596e891baf3a8266fb33bf7 \
  30da8243ef23470be79e02bac50a7e1dee1af12e \
  34a04e16b8582d9ddc605563fea1f868732cca4e \
  11c74d6ba24d3a6d48f54a194cd00ef3beea18f9 \
  693b8c2ba4396772eeb82ce2982acad19dd960f5; do
  rg -q "$sha" "$transcript"
done
rg -q '49 checks.*0 failed|49/49' "$transcript"
rg -q 'no drift|No drift' "$transcript"
rg -q 'unexpected argument.*--plugin-dir' "$transcript"
rg -q 'me@bstack' "$transcript"
rg -qi 'not.*capability E2E|does not establish.*capability' "$transcript"
rg -q 'api_marketplace.json' "$transcript"
rg -q 'interface.*must be an object' "$transcript"
rg -q 'interface.longDescription' "$transcript"
rg -qi 'symlink' "$transcript"
! rg -n 'TBD|TODO|FIXME|fill in details|implement later' "$transcript"
git diff --check
git add "$transcript"
git commit -m "docs(DEV-129): record production reference evidence"
```

Expected: one transcript-only commit.

## Task 2: Publish the adopt/adapt/reject comparison

**Files:**

- Create: `docs/research/dev-129-production-pattern-comparison.md`

### Step 1: Prove the report is absent

```bash
test ! -e docs/research/dev-129-production-pattern-comparison.md
```

Expected: exit `0`.

### Step 2: Write the report

Use `apply_patch` with exactly these top-level sections:

1. `Scope and authority`
2. `Pinned reference matrix`
3. `Repository guidance comparison`
4. `Canonical and generated metadata comparison`
5. `Skills and progressive disclosure comparison`
6. `Agents, wrappers, and optional surfaces`
7. `Host-local workflow comparison`
8. `Adopt, adapt, and reject matrix`
9. `Downstream decisions`
10. `Validation contract and non-claims`

The adopt/adapt/reject matrix must cover at least:

- one physical skill/reference tree;
- narrow workflow skills;
- progressive disclosure;
- Claude-canonical/generated-rich-Codex metadata;
- deterministic drift validation;
- provider-neutral guidance plus thin/generated `AGENTS.md`;
- host-specific local workflows;
- plugin-local agent default;
- manual dual catalogs;
- full skill-tree mirroring;
- `codex --plugin-dir`;
- unapproved hooks/MCP/commands/dependencies; and
- capability claims from discovery/install alone.

It must define the generator inputs precisely: Claude metadata owns shared
identity, while a separate Codex-only input owns plugin `interface` and
marketplace source/order/policy/category. Generated Codex outputs are not
hand-edited. It must distinguish the documented required entry point and
optional rich fields from the pinned validator's stricter creation policy,
keep marketplace-only fields out of `plugin.json`, apply the precise Claude
symlink rules, and leave repository-root versus `plugins/<name>` placement for
DEV-132.

Each row requires classification, exact pinned path(s), rationale, and
downstream issue impact. Link the transcript relatively. State that current
legacy loader compatibility does not replace explicit production Codex
artifacts.

### Step 3: Run report gates

```bash
set -e
report=docs/research/dev-129-production-pattern-comparison.md
test -s "$report"
headings=(
  'Scope and authority'
  'Pinned reference matrix'
  'Repository guidance comparison'
  'Canonical and generated metadata comparison'
  'Skills and progressive disclosure comparison'
  'Agents, wrappers, and optional surfaces'
  'Host-local workflow comparison'
  'Adopt, adapt, and reject matrix'
  'Downstream decisions'
  'Validation contract and non-claims'
)
for heading in "${headings[@]}"; do rg -q "^## ${heading}$" "$report"; done
test "$(rg '^## ' "$report" | wc -l | tr -d ' ')" -eq 10
rg -q 'evidence/dev-129-reference-command-transcript.md' "$report"
for term in Adopt Adapt Reject 'progressive disclosure' 'generated Codex' \
  'AGENTS.md' 'plugin-local agent' 'codex --plugin-dir' 'capability E2E'; do
  rg -qi "$term" "$report"
done
for issue in DEV-132 DEV-133 DEV-134 DEV-135 DEV-139; do rg -q "$issue" "$report"; done
! rg -n 'TBD|TODO|FIXME|fill in details|implement later' "$report"
git diff --check
git add "$report"
git commit -m "docs(DEV-129): compare cross-host production patterns"
```

Expected: one report-only commit.

## Final issue verification

After task reviews and corrections:

```bash
set -e
git diff --check origin/codex/dev-128-apple-api-research...HEAD
expected_paths="$(printf '%s\n' \
  'docs/research/dev-129-production-pattern-comparison.md' \
  'docs/research/evidence/dev-129-reference-command-transcript.md' \
  'docs/superpowers/plans/2026-07-17-dev-129-production-patterns.md' \
  'docs/superpowers/specs/2026-07-17-dev-129-production-patterns-design.md' | sort)"
actual_paths="$(git diff --name-only origin/codex/dev-128-apple-api-research...HEAD | sort)"
test "$actual_paths" = "$expected_paths"
test -z "$(git status --porcelain)"
```

Rerun reference-native validators, isolated host loading, transcript/report
semantics, source links, and a clean detached-worktree gate from the exact
final head. A missing binary, dependency, credential, or network requirement
must be an explicit blocker, never a false pass.

## Linear and stacked PR handoff

1. Attach report, transcript, exact commits, validation output, review verdict,
   and blockers to DEV-129.
2. Push `codex/dev-129-production-patterns`.
3. Open a ready PR targeting `codex/dev-128-apple-api-research` and link PR #2.
4. Move DEV-129 to `In Review`; do not merge the stack.
