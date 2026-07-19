# DEV-138 Deterministic Swift Handoff Fixtures Verification and Merge Plan

**Goal:** Verify and merge the completed DEV-138 repository-only Swift fixture
system without widening it into production runtime code or overstating its
evidence.

**Architecture:** `fixtures/dev-138/HandoffReducer.swift` is a pure,
Foundation-only reducer. `DeterministicScenarios.swift` evaluates the fixed case
corpus, while `expected-results.jsonl` is the sole closed outcome oracle. Python
tests compile and run the fixtures, exercise adversarial mutations, reuse the
authoritative DEV-128 SDK probes in place, and prove the fixtures never enter the
metadata-only plugin package.

**Canonical detail:** The approved design owns invariant and mapping detail,
`fixtures/dev-138/README.md` owns the case list and direct commands, and
`docs/research/evidence/dev-138-command-transcript.md` owns executed evidence.
This file is the present-state review, verification, and publication runbook; it
does not reconstruct implementation history.

## Authority and boundaries

- DEV-138 and its complete chronological Linear record are authoritative. The
  durable decision is comment `4bf0b19c-1a3a-485b-ac2e-823e05cbee22`; the July
  19 amendment is comment `a802f758-ea3f-429e-8f81-04ca8b2f00b7`. Re-read the
  issue, relations, attachments, and comments immediately before publication
  and merge. A newer amendment stops the sequence.
- The issue base is
  `27c7ce6b8d47541711184ceae06b2eecbdc4be8e`. DEV-138 remains deterministic,
  offline, and repository-only.
- Add no production bridge, workflow router, cost router, hook, skill,
  reference, agent, command, MCP server, package capability, dependency, live
  model call, provider/PCC call, credential access, hardware gate, release, or
  publication behavior.
- The reducer and baton fixture are `pseudocode_deterministic_mock`. Compilation
  does not prove Apple runtime behavior, model behavior, or capability
  activation.
- Do not invoke or substitute Claude Code `2.1.91`, `pre-commit`, or
  `markdownlint`; retain `blocked/deferred_by_owner`. Claude Code `2.1.140`
  remains diagnostic-only and cannot substitute. Full Xcode, Xcode/OS 27
  runtime behavior, Evaluations, Instruments, device, entitlement, and other
  unavailable host prerequisites remain explicit blockers, never passes.

## Exact issue scope

The complete delta is exactly nine regular files. The first two are planning
paths; the remaining seven are implementation/evidence paths.

1. `docs/superpowers/plans/2026-07-17-dev-138-deterministic-swift-fixtures.md`
2. `docs/superpowers/specs/2026-07-17-dev-138-deterministic-swift-fixtures-design.md`
3. `fixtures/dev-138/HandoffReducer.swift`
4. `fixtures/dev-138/DeterministicScenarios.swift`
5. `fixtures/dev-138/expected-results.jsonl`
6. `fixtures/dev-138/README.md`
7. `tests/test_dev_138_fixtures.py`
8. `tests/test_plugin_contract.py`
9. `docs/research/evidence/dev-138-command-transcript.md`

No package metadata, generator, generated file, or effective plugin payload may
change. The package must continue to expose zero capabilities and exclude all
repository fixtures, tests, docs, research, caches, private state, and runtime
artifacts.

## Contract that every review preserves

- Keep all 43 stable `DEV138-*` case IDs enumerated in the README. The executable
  emits one canonical, lexically ordered JSONL row per case; violations are
  sorted; the executable never reads or duplicates the expected oracle.
- Preserve typed, fail-closed ownership of transitions, minimized context,
  complete grants, tool-result provenance and consumption, stable effects,
  reconciliation truth, one authorized retry, cancellation, recovery,
  availability fallback, transcript repair, and metadata-only evidence.
- Preserve independent state and policy versions, exact destination/purpose/
  retention/class/field/tool bindings, C0-C3 policy, stable effect-ledger
  identities, no-rerun behavior, original-result ownership, and recovery until
  reconciliation.
- DEV-131 alone owns rubric scoring. DEV-138 may exercise `D-RUBRIC-001` as an
  inherited contract but must not add a second semantic scorer.
- Where the DEV-134 mapping is read, preserve five positive workflows—design,
  implement, review, debug, and validate—and one bounded non-positive router.
  The prototype remains 6 positive, 6 negative, and 3 ambiguous identities.
  Its 7 `direct_workflow` and 8 `non_positive_router` values are ownership
  metadata, not fields in any exact emitted envelope.
- The approved SDK row is Swift `6.3.3`, default target
  `arm64-apple-macosx26.0`, explicit target `arm64-apple-macos26.0`, and macOS
  SDK `26.5`. The installed arm64e Foundation Models interface SHA-256 is exactly
  `ff2285670b0966addb9827dc895a3ee3c9db6e186baae62c034fed012632aacc`.
- The DEV-128 matrix has six positive rows (five
  `compiled_sdk_26_5` rows plus the pseudocode baton row), one
  `interface_verified_sdk_26_5` row, and two strict expected blockers. Generic
  nonzero compilation is a failure; newly supported surfaces require honest
  reclassification.
- No gate establishes live Apple/model behavior, a production workflow/router,
  runtime cost or latency, host activation, or future capability. Missing
  evidence is `blocked`, not inferred or fabricated.

## Exactly three review/fix rounds

The main agent performs all three rounds in order against the whole PR and
records severity, exact evidence, impact, and the smallest bounded correction.
Each round uses a fresh fix worker that owns only named paths, preserves all
other work, commits locally, and never pushes, merges, or changes GitHub/Linear
state. Behavioral corrections require an observed focused RED and the smallest
GREEN fix. The main agent inspects every resulting diff and reruns the focused
gate. A clean round changes nothing and creates no no-op commit.

1. **Correctness and scope:** current Linear/GitHub compliance, state and
   security invariants, exclusions, SDK provenance, package boundaries, and
   existing unresolved feedback.
2. **Simplicity:** readable and concise control flow, single ownership of
   policy/oracles, DRY behavior tests, no dead scaffolding, and no speculative
   runtime surface.
3. **Adversarial acceptance:** replay, cancellation, recovery, reconciliation,
   stale versions/hashes/SHAs, duplicated identities, unavailable prerequisites,
   evidence honesty, and whole-PR readiness.

All findings in a round must be closed before advancing. Immediately before
merge, re-read Linear and GitHub and require zero actionable findings.

## Verification ladder

Run from the repository root at the exact reviewed head. Use a fresh temporary
directory and keep Python bytecode outside the repository.

### DEV-138 deterministic, mutation, mapping, package, and SDK gates

```bash
set -eu
dev138_artifacts="$(mktemp -d)"
trap 'rm -rf "$dev138_artifacts"' EXIT

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_dev_138_fixtures -v

swiftc -warnings-as-errors -parse-as-library \
  fixtures/dev-138/HandoffReducer.swift \
  fixtures/dev-138/DeterministicScenarios.swift \
  -o "$dev138_artifacts/dev138"
"$dev138_artifacts/dev138" >"$dev138_artifacts/first.jsonl"
"$dev138_artifacts/dev138" >"$dev138_artifacts/second.jsonl"
cmp "$dev138_artifacts/first.jsonl" "$dev138_artifacts/second.jsonl"
diff -u fixtures/dev-138/expected-results.jsonl \
  "$dev138_artifacts/first.jsonl"
test "$(wc -l < fixtures/dev-138/expected-results.jsonl | tr -d ' ')" = 43

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_dev_138_fixtures.Dev138ContractTests \
  tests.test_plugin_contract.PluginContractTests.test_dev_138_fixtures_are_repository_only \
  -v

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_dev_138_fixtures.Dev138SDKTests -v
```

Required result: DEV-138 passes exactly `36/36` with no skip; all 43 oracle
rows are exact and byte-identical across two runs; the mapping/package subset
passes `3/3`; and the SDK class confirms Swift 6.3.3, SDK 26.5, six positives,
the exact interface hash, and both capability-specific blockers. Any SDK skip
is a merge blocker. The README contains the authoritative direct positive and
negative command bodies; do not duplicate or weaken them here.

### Inherited deterministic and repository gates

```bash
set -eu
dev138_artifacts="$(mktemp -d)"
trap 'rm -rf "$dev138_artifacts"' EXIT

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests -p 'test_*.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s fixtures/dev-131/tests -p 'test_*.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 fixtures/dev-131/proof_runner.py \
  >"$dev138_artifacts/dev131.json"
PYTHONPYCACHEPREFIX="$dev138_artifacts/pycache" \
  python3 -m compileall -q fixtures/dev-131

swiftc -warnings-as-errors -parse-as-library \
  fixtures/dev-130/HandoffSecurityPolicy.swift \
  fixtures/dev-130/AdversarialScenarios.swift \
  -o "$dev138_artifacts/dev130"
"$dev138_artifacts/dev130" >"$dev138_artifacts/dev130-first.out"
"$dev138_artifacts/dev130" >"$dev138_artifacts/dev130-second.out"
diff -u fixtures/dev-130/expected-output.txt \
  "$dev138_artifacts/dev130-first.out"
cmp "$dev138_artifacts/dev130-first.out" \
  "$dev138_artifacts/dev130-second.out"
rg -q '^SUMMARY passed=8 failed=0$' \
  "$dev138_artifacts/dev130-first.out"

PYTHONDONTWRITEBYTECODE=1 python3 scripts/sync_generated_artifacts.py --check
git diff --exit-code -- AGENTS.md .agents/plugins/marketplace.json \
  plugins/apple-foundation-models-handoff/.codex-plugin/plugin.json

test "$(bats --version)" = 'Bats 1.13.0'
bats tests/plugin_skeleton.bats
```

Required result: repository `93/93`, DEV-131 `26/26` and `11/11`, DEV-130
`8/8` with exact golden and byte-identical repeat, synchronized generation, no
generated diff, and Bats `3/3`.

### Official validator and two exact Codex structural probes

```bash
set -eu
dev138_codex_root="${CODEX_HOME:-${HOME}/.codex}"
PYTHONDONTWRITEBYTECODE=1 python3 \
  "$dev138_codex_root/skills/.system/plugin-creator/scripts/validate_plugin.py" \
  plugins/apple-foundation-models-handoff

dev138_first_probe="$(PYTHONDONTWRITEBYTECODE=1 \
  python3 tests/e2e/codex_plugin_load.py)"
dev138_second_probe="$(PYTHONDONTWRITEBYTECODE=1 \
  python3 tests/e2e/codex_plugin_load.py)"
test "$dev138_first_probe" = "$dev138_second_probe"
printf '%s\n' "$dev138_first_probe" | jq -e '
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

Required result: the current official validator accepts the metadata-only
package. Both fresh isolated Codex `0.144.5` probes exit zero and emit identical
normalized JSON with an exact three-file cache. This is structural discovery,
installation, enabled-state, and cache-integrity evidence only.

### Exact scope, modes, privacy, cache, and diff gates

```bash
set -eu
dev138_base=27c7ce6b8d47541711184ceae06b2eecbdc4be8e
dev138_paths=(
  docs/research/evidence/dev-138-command-transcript.md
  docs/superpowers/plans/2026-07-17-dev-138-deterministic-swift-fixtures.md
  docs/superpowers/specs/2026-07-17-dev-138-deterministic-swift-fixtures-design.md
  fixtures/dev-138/DeterministicScenarios.swift
  fixtures/dev-138/HandoffReducer.swift
  fixtures/dev-138/README.md
  fixtures/dev-138/expected-results.jsonl
  tests/test_dev_138_fixtures.py
  tests/test_plugin_contract.py
)
test "${#dev138_paths[@]}" = 9
diff -u \
  <(printf '%s\n' "${dev138_paths[@]}" | LC_ALL=C sort) \
  <(git diff --name-only "$dev138_base"..HEAD | LC_ALL=C sort)
for dev138_file in "${dev138_paths[@]}"; do
  test "$(git ls-tree HEAD -- "$dev138_file" | awk '{print $1}')" = 100644
done

PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
from pathlib import Path

files = [
    Path("fixtures/dev-138/expected-results.jsonl"),
    Path("fixtures/dev-138/README.md"),
    Path("docs/research/evidence/dev-138-command-transcript.md"),
]
files.extend(
    entry
    for entry in Path("plugins/apple-foundation-models-handoff").rglob("*")
    if entry.is_file()
)
markers = (
    "/" + "Users" + "/",
    "/" + "home" + "/",
    "DEV138_" + "SECRET_SENTINEL",
    "BEGIN " + "RSA" + " PRIVATE KEY",
    "BEGIN " + "OPENSSH" + " PRIVATE KEY",
    "BEGIN " + "EC" + " PRIVATE KEY",
)
for entry in files:
    payload = entry.read_text(encoding="utf-8")
    for marker in markers:
        if marker in payload:
            raise SystemExit(f"unsafe evidence in {entry}")
PY

test -z "$(find . -type d -name '__pycache__' -print -quit)"
test -z "$(find . -type f -name '*.pyc' -print -quit)"
test -z "$(find . -type f \( -name '*.trace' -o -name '*.xcresult' \) \
  -print -quit)"
git diff --check "$dev138_base"..HEAD
git diff --check
test -z "$(git status --porcelain)"
```

Required result: exactly nine paths, all mode `100644`; no prohibited evidence,
cache, trace, result bundle, whitespace error, generated drift, or worktree
change.

## Evidence truth and merge gate

The transcript records only normalized versions, targets, stable diagnostic
classes, exit codes, counts, hashes, branch/base, exact tested source commit and
tree, and the nine-path scope. It excludes executable/SDK/private paths, raw
environment search values, diagnostics, prompts, responses, reasoning, tool
payloads, credentials, private configuration, real data, `.trace`, and
`.xcresult`.

Any change to reducer/scenario/oracle/README/test behavior requires the affected
gate ladder to run again and the evidence to bind the new tested source commit
and tree. A planning-only edit does not rebind source evidence when those seven
implementation/evidence responsibilities and all recorded results remain
unchanged. Never reconstruct a missing RED, stale hash, result, or prerequisite.

Publication and merge are main-agent-only. After all three rounds, all gates,
the final Linear/GitHub reread, and zero actionable findings:

```bash
set -eu
dev138_reviewed_head="$(git rev-parse HEAD^{commit})"
dev138_reviewed_tree="$(git rev-parse HEAD^{tree})"
dev138_remote_before="$(git rev-parse refs/remotes/origin/codex/dev-138-deterministic-swift-fixtures)"

git push origin \
  HEAD:refs/heads/codex/dev-138-deterministic-swift-fixtures \
  --force-with-lease=refs/heads/codex/dev-138-deterministic-swift-fixtures:"$dev138_remote_before"
test "$(git ls-remote origin refs/heads/codex/dev-138-deterministic-swift-fixtures | awk '{print $1}')" = \
  "$dev138_reviewed_head"
gh pr edit 10 --base main
gh pr ready 10
gh pr merge 10 --squash --match-head-commit "$dev138_reviewed_head"

git fetch origin main
test "$(git rev-parse origin/main^{tree})" = "$dev138_reviewed_tree"
```

Stop instead of overwriting if the remote lease, PR head, Linear contract, or
required prerequisite changed. Retain the remote branch and existing worktree.
Fast-forward the existing `main` worktree to `origin/main`, repeat the focused
merged-result smoke gate there, and stop if its tree or result differs.
Post only DoD-required normalized Linear evidence; change issue status only when
its current issue-level completion contract is satisfied.
