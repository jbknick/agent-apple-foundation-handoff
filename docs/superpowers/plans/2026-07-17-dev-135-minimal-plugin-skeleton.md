# DEV-135 Minimal Plugin Skeleton Verification Runbook

This is a present-state verification runbook, not an implementation transcript.
DEV-135 is already implemented. Use these commands to verify the candidate without
recreating files, replaying historical RED steps, or adding behavior.

## DEV-136 option-2 supersession

> **Bounded supersession (DEV-136):** The approved DEV-136 option-2 decision
> amends the production capability topology to **five workflows plus one non-positive router**,
> `route-apple-foundation-models-handoff`. The five workflows retain
> **positive-only workflow ownership**; the **router-owned non-positive branches**
> are `no_activation`, domain `clarification_required`, and missing-approved-contract
> `clarification_required`. Historical evidence remains truthful: **fixture prompts/outcomes are unchanged**,
> and the DEV-134 prototype still does not prove host capability. **Codex-only current proof**
> remains in scope, while Claude proof is owner-deferred. The binding design amendment path is
> [`docs/superpowers/specs/2026-07-18-dev-136-preselection-router-design.md`](../specs/2026-07-18-dev-136-preselection-router-design.md).
> Statements below that describe exactly five production capabilities or a
> conceptual-only router remain historical except where this bounded note
> supersedes them.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

## Fixed contract

- Candidate branch: `codex/dev-135-minimal-plugin-skeleton`.
- Main base: `c749d14129888c643b66646158735bf58e6fc603`.
- Plugin ID/version: `apple-foundation-models-handoff` / `0.1.0`.
- Marketplace/source: `agent-apple-foundation-handoff` /
  `./plugins/apple-foundation-models-handoff`.
- Both category fields are `Developer Tools`; policy is installation `AVAILABLE`
  and authentication `ON_INSTALL`, with no products override.
- Python implementation and default checks use the standard library and require no
  network, credentials, PCC, paid provider, model generation, or hardware entitlement.

### Exact issue-owned paths

The diff from the fixed main base contains exactly these 19 paths:

```text
.agents/plugins/marketplace.json
.claude-plugin/marketplace.json
AGENTS.md
CLAUDE.md
docs/research/evidence/dev-135-plugin-skeleton-e2e.md
docs/superpowers/plans/2026-07-17-dev-135-minimal-plugin-skeleton.md
docs/superpowers/specs/2026-07-17-dev-135-minimal-plugin-skeleton-design.md
metadata/codex-marketplace.json
plugins/apple-foundation-models-handoff/.claude-plugin/plugin.json
plugins/apple-foundation-models-handoff/.codex-plugin/plugin.json
plugins/apple-foundation-models-handoff/metadata/codex-interface.json
schemas/codex-interface-input.schema.json
schemas/codex-marketplace-input.schema.json
scripts/sync_generated_artifacts.py
tests/e2e/codex_plugin_load.py
tests/plugin_skeleton.bats
tests/test_generated_artifacts.py
tests/test_plugin_contract.py
tests/test_repository_guidance.py
```

### Canonical and generated ownership

The five authored canonical inputs are:

1. `CLAUDE.md`
2. `.claude-plugin/marketplace.json`
3. `metadata/codex-marketplace.json`
4. `plugins/apple-foundation-models-handoff/.claude-plugin/plugin.json`
5. `plugins/apple-foundation-models-handoff/metadata/codex-interface.json`

The synchronization entry point owns exactly three generated outputs; never edit
them directly:

1. `AGENTS.md`
2. `.agents/plugins/marketplace.json`
3. `plugins/apple-foundation-models-handoff/.codex-plugin/plugin.json`

This is the approved Claude-authored/generated-Codex boundary: shared identity and
Claude metadata remain canonical, while Codex marketplace and manifest outputs are
deterministically rendered from canonical shared and Codex-only inputs.

### Honest package boundary

The installed package contains exactly three regular, non-symlink payload files:

```text
.claude-plugin/plugin.json
.codex-plugin/plugin.json
metadata/codex-interface.json
```

`capabilities` is exactly `[]`, and `skills` is absent. There are no skills,
references, preselection router, hooks, agents, MCP servers, commands, plugin-local
scripts, dependencies, runtime, assets, or plugin-local README. DEV-135 therefore
proves metadata packaging and structural installation only.

The five future direct positive workflows are design, implement, review, debug, and
validate. The bounded non-positive preselection router may only clarify, decline, or
hand off; it is not a sixth positive workflow. None is implemented here. That router
is also separate from the DEV-142 through DEV-145 cost router, `PostToolUse` hook,
and Swift bridge chain.

### Fail-closed generation boundary

`scripts/sync_generated_artifacts.py` is the only synchronization entry point.
Both modes must validate all canonical inputs and rendered outputs before mutation.
Canonical inputs must remain stable regular files across pre-read, open, read, and
post-read identity checks; malformed JSON, duplicate keys, unknown fields, ownership
drift, non-empty capabilities, symlinks, and non-regular inputs fail closed.

Only the three generated paths are allowed. Check and write modes reject unexpected
files or directories, including empty directories, in reserved generated namespaces;
nested-parent symlinks; generated-file symlinks or non-regular obstructions; staging
name collisions; and post-read or temporary-path identity swaps. Write mode preflights
the whole set before replacement, uses descriptor-relative exclusive temporary files
and atomic replacement, verifies the replaced inode/type, and cleans temporary files
on failure. A partial batch is drift, never synchronization. The repository tests are
the executable oracle for these rules; do not weaken them.

## Verification

Run every command from the repository root. A missing prerequisite is `blocked`; an
executed contradiction is `fail`. Do not install, vendor, substitute, or relax a gate
to obtain a pass.

### Repository, synchronization, Bats, and official validator

```bash
set -e
PYTHONDONTWRITEBYTECODE=1 python3 scripts/sync_generated_artifacts.py --write
git diff --exit-code -- AGENTS.md .agents/plugins/marketplace.json \
  plugins/apple-foundation-models-handoff/.codex-plugin/plugin.json
PYTHONDONTWRITEBYTECODE=1 python3 scripts/sync_generated_artifacts.py --check
PYTHONDONTWRITEBYTECODE=1 \
  python3 -m unittest discover -s tests -p 'test_*.py' -v

if ! command -v bats >/dev/null 2>&1; then
  printf '%s\n' 'BATS status=blocked reason=missing_binary'
  exit 2
fi
test "$(bats --version)" = 'Bats 1.13.0'
bats tests/plugin_skeleton.bats

codex_home="${CODEX_HOME:-${HOME}/.codex}"
python3 "$codex_home/skills/.system/plugin-creator/scripts/validate_plugin.py" \
  plugins/apple-foundation-models-handoff
```

Required result: generated bytes remain unchanged; synchronization passes; the full
repository suite passes; Bats `1.13.0` passes exactly 3 of 3 tracked tests; and the
official current plugin validator accepts the metadata-only package.

### Two exact Codex structural probes

Codex CLI `0.144.5` is the pinned active host. The probe captures one executable,
requires the strict single-line version, uses a fresh isolated `CODEX_HOME`, performs
only the approved local marketplace/list/install/list flow, validates the exact
three-file cache and source/cache SHA-256 equality, then rechecks executable identity
and version. Run it twice:

```bash
set -e
first="$(PYTHONDONTWRITEBYTECODE=1 python3 tests/e2e/codex_plugin_load.py)"
second="$(PYTHONDONTWRITEBYTECODE=1 python3 tests/e2e/codex_plugin_load.py)"
test "$first" = "$second"
printf '%s\n' "$first" | jq -e '
  select(
    .status == "pass" and
    .hostVersion == "0.144.5" and
    .pluginVersion == "0.1.0" and
    .enabled == true and
    .capabilities == [] and
    .capabilityActivation == "blocked/production_skill_not_implemented" and
    (.cacheFiles | length) == 3
  )'
```

Both invocations must exit 0 and emit byte-identical normalized JSON. Exit 2 is the
normalized missing/wrong-host blocker; exit 1 is a structural failure. Discovery,
installation, enabled state, and cache integrity do not prove capability activation.

### DEV-131 deterministic evaluation

```bash
set -e
PYTHONDONTWRITEBYTECODE=1 \
  python3 -m unittest discover -s fixtures/dev-131/tests -p 'test_*.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 fixtures/dev-131/proof_runner.py
pycache_root="$(mktemp -d)"
PYTHONPYCACHEPREFIX="$pycache_root" python3 -m compileall -q fixtures/dev-131
test -z "$(find . -type d -name '__pycache__' -print -quit)"
test -z "$(find . -type f -name '*.pyc' -print -quit)"
```

Required result: 26 tests pass, 11 of 11 oracle cases match, evidence and rubric
checks pass, and the zero denominator remains `not_applicable`.

### DEV-130 security golden

```bash
set -e
artifact_dir="$(mktemp -d)"
swiftc -warnings-as-errors -parse-as-library \
  fixtures/dev-130/HandoffSecurityPolicy.swift \
  fixtures/dev-130/AdversarialScenarios.swift \
  -o "$artifact_dir/dev130-adversarial"
"$artifact_dir/dev130-adversarial" > "$artifact_dir/first.out"
diff -u fixtures/dev-130/expected-output.txt "$artifact_dir/first.out"
"$artifact_dir/dev130-adversarial" > "$artifact_dir/second.out"
cmp "$artifact_dir/first.out" "$artifact_dir/second.out"
rg -q '^SUMMARY passed=8 failed=0$' "$artifact_dir/first.out"
```

Required result: exact golden output reports 8 passed and 0 failed, and the repeat
is byte-identical.

### DEV-128 SDK 26.5 matrix

```bash
set -e
artifact_dir="$(mktemp -d)"
SDK="$(xcrun --sdk macosx --show-sdk-path)"
TARGET=arm64-apple-macos26.0
swiftc -warnings-as-errors -typecheck -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/stable-surface.swift
swiftc -warnings-as-errors -typecheck -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/generable-macro.swift
swiftc -warnings-as-errors -parse-as-library -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/availability-probe.swift -o "$artifact_dir/availability"
"$artifact_dir/availability" > "$artifact_dir/availability.out"
rg -q '^availability=' "$artifact_dir/availability.out"
rg -q '^isAvailable=' "$artifact_dir/availability.out"
rg -q '^contextSize=[0-9]+$' "$artifact_dir/availability.out"
rg -q '^supportsCurrentLocale=' "$artifact_dir/availability.out"
swiftc -warnings-as-errors -parse-as-library -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/transcript-roundtrip.swift -o "$artifact_dir/transcript"
test "$("$artifact_dir/transcript")" = \
  'entries=3 codableRoundTrip=true rehydrated=true'
swiftc -warnings-as-errors -parse-as-library -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/session-isolation.swift -o "$artifact_dir/isolation"
test "$("$artifact_dir/isolation")" = \
  'parentEntries=1 childEntries=1 isolated=true'
swiftc -warnings-as-errors -parse-as-library -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/baton-pass-state.swift -o "$artifact_dir/baton"
test "$("$artifact_dir/baton")" = \
  'source=research destination=review active=review finalOwner=review transferred=true'
set +e
swiftc -warnings-as-errors -typecheck -target arm64-apple-macos27.0 -sdk "$SDK" \
  fixtures/dev-128/blocked/os-27-beta-surface.swift \
  > "$artifact_dir/beta.out" 2>&1
beta_rc=$?
set -e
test "$beta_rc" -ne 0
rg -q "DynamicProfile.*not a member type|has no member 'Profile'" \
  "$artifact_dir/beta.out"
rg -q "extra arguments at positions #1, #2 in call" "$artifact_dir/beta.out"
rg -q "extra argument 'toolCallingMode' in call" "$artifact_dir/beta.out"
set +e
swiftc -warnings-as-errors -typecheck -target arm64-apple-macos27.0 -sdk "$SDK" \
  fixtures/dev-128/blocked/evaluations-import.swift \
  > "$artifact_dir/evaluations.out" 2>&1
evaluations_rc=$?
set -e
test "$evaluations_rc" -ne 0
rg -q "no such module 'Evaluations'" "$artifact_dir/evaluations.out"
```

Required result: all six positive gates pass against installed SDK 26.5, and both
strict expected blockers fail with the listed capability-specific diagnostics.
These are the only executed SDK labels; `SDK 26.x` remains an architecture-family
boundary, not an execution claim.

### Exact scope and hygiene

```bash
set -e
base=c749d14129888c643b66646158735bf58e6fc603
test "$(git merge-base HEAD origin/main)" = "$base"
diff -u \
  <(printf '%s\n' \
    .agents/plugins/marketplace.json \
    .claude-plugin/marketplace.json \
    AGENTS.md \
    CLAUDE.md \
    docs/research/evidence/dev-135-plugin-skeleton-e2e.md \
    docs/superpowers/plans/2026-07-17-dev-135-minimal-plugin-skeleton.md \
    docs/superpowers/specs/2026-07-17-dev-135-minimal-plugin-skeleton-design.md \
    metadata/codex-marketplace.json \
    plugins/apple-foundation-models-handoff/.claude-plugin/plugin.json \
    plugins/apple-foundation-models-handoff/.codex-plugin/plugin.json \
    plugins/apple-foundation-models-handoff/metadata/codex-interface.json \
    schemas/codex-interface-input.schema.json \
    schemas/codex-marketplace-input.schema.json \
    scripts/sync_generated_artifacts.py \
    tests/e2e/codex_plugin_load.py \
    tests/plugin_skeleton.bats \
    tests/test_generated_artifacts.py \
    tests/test_plugin_contract.py \
    tests/test_repository_guidance.py | LC_ALL=C sort) \
  <(git diff --name-only "$base"..HEAD | LC_ALL=C sort)
git diff --check "$base"..HEAD
test -z "$(find . -type d -name '__pycache__' -print -quit)"
test -z "$(find . -type f -name '*.pyc' -print -quit)"
test -z "$(find . -type f \( -name '*.trace' -o -name '*.xcresult' \) \
  -print -quit)"
for surface in skills references agents hooks mcp commands scripts assets; do
  test ! -e "plugins/apple-foundation-models-handoff/$surface"
done
test -z "$(git status --porcelain)"
```

Required result: the base and 19-path list match exactly; no whitespace, cache,
trace, result-bundle, symlinked package, or unapproved package-surface finding exists;
and the final committed worktree is clean.

## Evidence classifications and publication boundary

Record only fresh, normalized evidence in
`docs/research/evidence/dev-135-plugin-skeleton-e2e.md`, bound to the tested commit
and source tree. Preserve exact counts, normalized host identity/version, the exact
three cache paths, hashes, and pass/fail/blocked reasons. Structural presence,
discovery, installation, cache, and enabled state are prerequisites, not capability
proof.

The truthful status rows are:

- `E-CODEX-LOAD-001`: pass only after both exact structural probes pass.
- `E-CODEX-ACTIVATE-001`: `blocked/production_skill_not_implemented`.
- `E-CLAUDE-LOAD-001`: `blocked/deferred_by_owner`; do not invoke Claude here.
- `BATS`: pass only for Bats `1.13.0` with exactly 3 of 3 tracked tests.
- `pre-commit`: `blocked/deferred_by_owner`.
- `markdownlint`: `blocked/deferred_by_owner`.

Never commit raw prompts, responses, reasoning, tool arguments/results, credentials,
private configuration, real user or third-party data, raw diagnostics, private absolute
paths, `.trace`, or `.xcresult`. Only hash-bound synthetic or approved-redacted rubric
material may be committed, and only after the DEV-131 path, content, structured-key,
classification, and hash scans pass.

Push, PR mutation, Linear mutation, merge, tag, publish, and release all require
separate authorization. Any later authorized report must state the exact commit/tree,
main base, 19-path scope, gate counts, blocked/deferred rows, three-file payload,
`capabilities: []`, and structural-not-activation boundary. Never convert a missing
prerequisite or deferred Claude/capability row into a pass.
