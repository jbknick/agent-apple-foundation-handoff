# DEV-133 Repository Guidance Plan

## Goal and architecture

Maintain one provider-neutral repository contract without inventing ownership.
`CLAUDE.md` is the only authored guide. Its bounded adapter section is the sole
source for the generated root `AGENTS.md`. The standard-library sync script is
the only writer for that output, and repository tests enforce generation,
placement, privacy, and safety.

DEV-133 is guidance-only. It describes five future positive workflows and one
bounded non-positive preselection router, but implements no plugin payload,
manifest, host loading, cost router, hook, Swift bridge, or runtime behavior.
Later issues own those artifacts.

## Binding review contract

- Linear DEV-133 comment `973b4feb-4832-4482-85de-228d17839ace` and the latest
  DEV-132 propagation comment `46fb2400-0512-4337-801d-f4a11104f460` govern;
  earlier DEV-133 corrections remain binding.
- The current review is based on merged `main` at
  `829d5f71ac5cb9609f96dde4a7ae73c32f42e3cd`.
- Acceptance requires exactly three main-agent review rounds with a fresh fix
  worker for each round and zero actionable findings after every round.
- Workers may commit locally but never push, edit PR metadata, merge, tag,
  publish, or release. Only the main agent may perform authorized publication.
- Generated `AGENTS.md` is never hand-edited. Regenerate it only through
  `scripts/sync_generated_artifacts.py`.

## Exact scope

The final DEV-133 delta contains exactly these six paths:

```text
AGENTS.md
CLAUDE.md
docs/research/evidence/dev-133-repository-guidance-e2e.md
docs/superpowers/plans/2026-07-17-dev-133-repository-guidance.md
scripts/sync_generated_artifacts.py
tests/test_repository_guidance.py
```

Ignored `.superpowers/sdd/**` files are local scratch state, not product scope.

## Implemented interfaces

`CLAUDE.md` owns one non-empty section between:

```text
<!-- BEGIN GENERATED AGENTS ADAPTER -->
<!-- END GENERATED AGENTS ADAPTER -->
```

`scripts/sync_generated_artifacts.py` exposes:

- `render_agents(canonical_text: str) -> str`, which validates exactly one
  ordered, non-empty adapter section and renders stable LF UTF-8 output;
- `synchronize(root: pathlib.Path, write: bool) -> bool`, which rejects unsafe
  canonical/generated paths and reports only normalized relative diagnostics;
- exact CLI modes `--write` and `--check`; and
- atomic write behavior that neither follows symlinks nor leaves temporary
  files after failure.

The generated adapter must be a regular root file, unique in the repository,
smaller than the canonical guide, at most 90 lines, and at most 6500 UTF-8
bytes. Before accepting read bytes, the synchronizer revalidates the opened
descriptor snapshot and current pathname identity, mode, size, modification
time, and change time. The 23 behavior-focused tests cover extraction,
check/write behavior, idempotence, drift, obstruction/symlink/path-swap and
post-read mutation failures, cleanup, bounds, placement, links, ownership,
routing, evidence, host lifecycle, and privacy.

## Guidance invariants

- The future positive surface is design, implement, review, debug, and validate.
  Positive preselection reveals one directly relevant reference. The bounded
  non-positive router only clarifies, declines, or hands off and is not a sixth
  positive skill or the later cost-routing runtime.
- Today only canonical `CLAUDE.md` and generated `AGENTS.md` exist for DEV-133.
  DEV-135 owns planned plugin metadata and manifest generation through the
  shared synchronization entry point. Skills and references belong to their
  own later issues.
- Preferred source `./` is conditional on isolated cache and real-host proof;
  the deterministic fallback changes placement only and uses no external
  symlink. Effective plugin payload excludes repository docs, research,
  fixtures, tests, and private state.
- Apple claims rely only on official Apple material and installed SDK
  interfaces. Executed labels are exact; unsupported prerequisites are
  `blocked`, never false passes.
- Each host row captures one executable, checks its strict approved version,
  invokes only that executable, and rechecks resolution/version. An unmet
  initial prerequisite is `blocked`; post-capture drift is `fail` and
  invalidates the row.
- Evidence contains normalized identity, version, diagnostics, exit, status,
  and approved hash-bound synthetic/redacted rubric material only. Raw host or
  model content, credentials, private paths/configuration, traces, and real
  user or third-party data remain excluded.
- Structural loading, discovery, installation, cache, enabled state, file
  presence, Markdown, and version output never prove capability. Capability
  requires reproducible fresh-host activation and complete valid/invalid
  outcomes.

## Deterministic acceptance

Run generation and all 23 repository-guidance tests:

```bash
set -euo pipefail
PYTHONDONTWRITEBYTECODE=1 python3 scripts/sync_generated_artifacts.py --write
PYTHONDONTWRITEBYTECODE=1 python3 scripts/sync_generated_artifacts.py --check
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests -p 'test_*.py' -v
test "$(find . -name AGENTS.md -type f | wc -l | tr -d ' ')" -eq 1
test ! -L AGENTS.md
test "$(wc -l < AGENTS.md | tr -d ' ')" -le 90
test "$(wc -c < AGENTS.md | tr -d ' ')" -le 6500
```

Run the inherited DEV-131 26-test and 11-case proof:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s fixtures/dev-131/tests -p 'test_*.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 fixtures/dev-131/proof_runner.py
```

Compile and run DEV-130 twice, requiring the exact 8/0 golden output and a
byte-identical repeat:

```bash
artifact_dir="$(mktemp -d)"
swiftc -warnings-as-errors -parse-as-library \
  fixtures/dev-130/HandoffSecurityPolicy.swift \
  fixtures/dev-130/AdversarialScenarios.swift \
  -o "$artifact_dir/dev130"
"$artifact_dir/dev130" > "$artifact_dir/first.out"
diff -u fixtures/dev-130/expected-output.txt "$artifact_dir/first.out"
rg -q '^SUMMARY passed=8 failed=0$' "$artifact_dir/first.out"
"$artifact_dir/dev130" > "$artifact_dir/second.out"
cmp "$artifact_dir/first.out" "$artifact_dir/second.out"
```

Verify identity, privacy, cache, scope, and diff hygiene:

```bash
shasum -a 256 CLAUDE.md AGENTS.md scripts/sync_generated_artifacts.py \
  tests/test_repository_guidance.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_repository_guidance.RepositoryGuidanceTests.test_guidance_contains_no_literal_private_paths_or_placeholders -v
test -z "$(find . -type d -name '__pycache__' -print -quit)"
test -z "$(find . -type f -name '*.pyc' -print -quit)"
git diff --check 829d5f71ac5cb9609f96dde4a7ae73c32f42e3cd..HEAD
git diff --name-only 829d5f71ac5cb9609f96dde4a7ae73c32f42e3cd...HEAD | sort
```

The last command must equal the six-path list above exactly. Evidence review
must also confirm that only normalized metadata was committed.

## Host evidence boundary

Claude Code `2.1.91` and Codex CLI `0.144.5` semantic rows dated 2026-07-17 are
historical evidence bound to their historical source. Do not rerun them in this
review or use them to validate corrected current guidance. Record only current
executable/version prerequisites. Claude Code `2.1.140` is diagnostic-only and
cannot substitute for the approved Claude baseline.

Missing authentication, semantic automation, `pre-commit`, `markdownlint`, SDK,
device, hardware, or other required prerequisites remain explicit `blocked` or
deferred rows. Do not install dependencies, switch models, retry, or relabel a
structural result as a semantic pass.

## Evidence, publication, and issue state

The evidence file binds the deterministic checks to the exact tested source
commit and source hashes, retains historical host rows as historical, records
current normalized prerequisites, and makes all runtime/capability nonclaims
explicit. A later evidence-only commit may cite that exact source commit.

Immediately before publication, the main agent rereads Linear and GitHub,
confirms the reviewed head and six-path scope, reruns the deterministic gates,
and requires zero actionable findings. It may then force-push only with the
captured lease and squash-merge only with head-SHA protection. Post only the
DoD-required normalized Linear evidence comment. Leave DEV-133 In Review while
current semantic E2E or required tool prerequisites remain incomplete; never
report deferred evidence as passed.
