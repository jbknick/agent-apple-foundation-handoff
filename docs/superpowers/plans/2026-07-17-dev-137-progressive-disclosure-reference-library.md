# DEV-137 progressive-disclosure reference library verification and merge runbook

**Status:** implementation complete for the DEV-137 reference-only branch; final
completion remains blocked on the combined DEV-136 gate.

**Purpose:** verify the present 16-path DEV-137 delta, preserve the reference-only
boundary, bind deterministic evidence to an exact source commit/tree, and hand
that immutable source tip to DEV-136. This is a verification and merge runbook,
not an implementation history.

## Non-negotiable outcome

The packaged plugin remains documentation-only:

- exactly five regular Markdown references under
  `plugins/apple-foundation-models-handoff/references/`;
- exactly eight packaged files total: the five references plus the Claude
  manifest, generated Codex manifest, and Codex interface metadata;
- zero skills, hooks, commands, agents, MCP servers, scripts, dependencies,
  Swift runtime, executable fixtures, or other runtime capability;
- production activation is not claimed by file presence, installation, cache
  identity, an explicitly directed prompt, or a model response.

The five concern owners are:

1. `architecture-and-state.md` — result schema, state, ownership lifecycle,
   transitions, and recovery.
2. `orchestration-patterns.md` — pattern topology, history visibility, control,
   final-response owner, selection, and the documentation-only DEV-142 through
   DEV-145 diagnostic chain.
3. `apple-api-availability.md` — Apple API declarations, availability,
   interface evidence, errors, and blockers.
4. `security-context-and-recovery.md` — C0-C3 policy, grants, effects,
   reconciliation, recovery, and provider-field ownership.
5. `evaluation-and-observability.md` — stable checks/evidence IDs, rubric,
   observability, runtime-cost release gate, and blocker ownership.

## Present 16-path delta

The merge review is limited to these paths:

| Path | Present role |
| --- | --- |
| `CLAUDE.md` | authored repository contract |
| `AGENTS.md` | generated mirror; never edit directly |
| `docs/research/evidence/dev-137-reference-library-e2e.md` | normalized evidence ledger |
| `docs/superpowers/plans/2026-07-17-dev-137-progressive-disclosure-reference-library.md` | this runbook |
| `docs/superpowers/specs/2026-07-17-dev-137-progressive-disclosure-reference-library-design.md` | canonical DEV-137 design |
| `plugins/apple-foundation-models-handoff/references/apple-api-availability.md` | Apple owner |
| `plugins/apple-foundation-models-handoff/references/architecture-and-state.md` | architecture owner |
| `plugins/apple-foundation-models-handoff/references/evaluation-and-observability.md` | evaluation owner |
| `plugins/apple-foundation-models-handoff/references/orchestration-patterns.md` | orchestration owner |
| `plugins/apple-foundation-models-handoff/references/security-context-and-recovery.md` | security owner |
| `tests/e2e/codex_plugin_load.py` | structural install/cache probe |
| `tests/e2e/codex_reference_disclosure.py` | optional directed disclosure probe |
| `tests/test_codex_reference_disclosure.py` | closed parser and host tests |
| `tests/test_plugin_contract.py` | package/host contract tests |
| `tests/test_reference_library.py` | reference topology/content/source/compile tests |
| `tests/test_repository_guidance.py` | canonical/generated guidance tests |

Canonical authored inputs remain `CLAUDE.md`,
`.claude-plugin/marketplace.json`, `metadata/codex-marketplace.json`,
`plugins/apple-foundation-models-handoff/.claude-plugin/plugin.json`, and
`plugins/apple-foundation-models-handoff/metadata/codex-interface.json`.
`AGENTS.md`, `.agents/plugins/marketplace.json`, and
`plugins/apple-foundation-models-handoff/.codex-plugin/plugin.json` are
generated only by `scripts/sync_generated_artifacts.py`.

## Current Apple/toolchain truth

The installed deterministic baseline is:

- Xcode 26.6 (17F113);
- Apple Swift 6.3.3;
- macOS SDK 26.5;
- installed FoundationModels interface SHA-256
  `ff2285670b0966addb9827dc895a3ee3c9db6e186baae62c034fed012632aacc`.

Executed labels are only `compiled_sdk_26_5` and
`interface_verified_sdk_26_5`. OS/Xcode 27-only surfaces retain
`official_os_xcode_27_beta_locally_unverified`; deterministic mock material
retains `pseudocode_deterministic_mock`. Missing SDK 27, full Xcode 27,
Evaluations, Instruments, compatible targets, model, network, credentials, or
hardware is a blocker, never a pass. “SDK 26.x” is an architecture-family
description, not an executed evidence label.

## Parser and host contracts

`parse_disclosure_events` is the single disclosure parser used by `run_case`.
It accepts only:

1. one complete successful `command_execution` lifecycle for the exact
   five-path discovery command;
2. one complete successful lifecycle for `cat` of exactly one canonical,
   root-contained regular reference;
3. one top-level schema-pinned final agent message containing only the bounded
   JSON result.

One bare or absolute `sh`, `bash`, or `zsh` transport envelope with sole
flag `-lc` is grammar-only. IDs are globally unique; lifecycles are paired and
ordered; discovery output and source output bytes are exact. Nested,
lookalike, pre-read, replayed, failed, interleaved, extra, or unknown actions
fail closed. Fictional Swift signatures fail whether present in reasoning or
the final message. JSONL rejects invalid UTF-8, duplicate keys, non-standard
constants, scalars, and empty input.

Codex host baseline is exactly `codex-cli 0.144.5`. Capture one resolved
executable and its device, inode, file type, permission mode, size, mtime ns,
and ctime ns. Recheck that snapshot before and after version calls, install,
every case, source/cache validation, and temporary-home teardown. A missing,
non-runnable, malformed, or version-mismatched initial host is normalized
`blocked/missing_binary_or_version_mismatch`; post-capture identity/version
drift is `fail/host_resolution_or_version_drift`. No model output can prove
an effect or grant authority.

## Exact three-round fresh-worker review

Each round uses a different fresh worker at the exact current source tip. A
worker must inspect the actual diff and run its own gates; it must not inherit a
prior worker's conclusion.

1. **Round 1 — contract correctness.** Review all 16 paths against the canonical
   design and repository contract. Verify the five-owner partition, eight-file
   payload, zero runtime, Apple labels/facts, security/evidence boundaries,
   parser closure, host race handling, and all deterministic gates. Correct
   proven defects, then bind an evidence-only commit to the corrected source
   SHA/tree.
2. **Round 2 — simplicity without behavior loss.** Verify one parser truth,
   no embedded executable-helper test class, no dead generic/recursive parser,
   concise parameterized external coverage, and a present-state runbook. Repeat
   all deterministic gates and update only evidence after the new source
   commit exists.
3. **Round 3 — final merge audit.** From a clean worktree, independently review
   the complete current 16-path delta, confirm generated synchronization,
   source/cache and evidence hashes, exact source/evidence commit separation,
   historical-row attribution, and every deterministic result. No new source
   change is acceptable without restarting the evidence binding for that tip.

A round is not complete on a review comment alone. Its accepted state is a
clean exact source tip, passing bounded deterministic proof, and an evidence
commit whose recorded source SHA/tree matches that tip.

## Deterministic verification

Run Python groups separately and with `PYTHONDONTWRITEBYTECODE=1`. Do not run
`codex exec`, a live model, Claude, network source resolution, or the combined
DEV-136 runner in this branch review.

### Focused parser, host, reference, and plugin groups

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v \
  tests.test_codex_reference_disclosure.ClosedDisclosureParserTests \
  tests.test_codex_reference_disclosure.ProbeBoundaryTests \
  tests.test_codex_reference_disclosure.HostIdentityTests
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v \
  tests.test_reference_library
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v \
  tests.test_plugin_contract tests.test_repository_guidance
```

### Full unit, compile, sync, and Bats gates

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests -p 'test_*.py' -v
PYTHONPYCACHEPREFIX=/tmp/dev137-pycache PYTHONDONTWRITEBYTECODE=1 \
  python3 -m py_compile \
  tests/e2e/codex_plugin_load.py tests/e2e/codex_reference_disclosure.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/sync_generated_artifacts.py --check
bats tests/plugin_skeleton.bats
```

### Direct blocked-PATH proof

Use a fresh empty temporary directory as `PATH`, invoke each script through
the already resolved Python executable, and require exit `2` plus exactly one
normalized JSON dictionary:

```text
{"evidenceId":"E-CODEX-LOAD-001","reason":"missing_binary_or_version_mismatch","status":"blocked"}
{"attemptedCaseCount":0,"claimBoundary":"optional_explicitly_directed_reference_selection_only","completionGate":"blocked/production_skills_not_integrated","evidenceId":"DEV137-CODEX-REF-001","host":"codex","hostPath":"<host-path>","hostVersion":null,"model":"gpt-5.6-sol","reason":"missing_binary_or_version_mismatch","status":"blocked","workflowActivation":"not_claimed"}
```

This proof must not resolve or execute a real Codex binary.

### Inherited deterministic gates

DEV-128: confirm SDK 26.5, type-check all six `fixtures/dev-128/compiled/*.swift`
fixtures with their documented targets, and require the two documented blocked
fixtures to fail with their exact expected diagnostics. Recheck the installed
interface hash above.

DEV-130:

```bash
swiftc -warnings-as-errors -parse-as-library \
  fixtures/dev-130/HandoffSecurityPolicy.swift \
  fixtures/dev-130/AdversarialScenarios.swift -o /tmp/dev-130-adversarial
/tmp/dev-130-adversarial > /tmp/dev-130-output
diff -u fixtures/dev-130/expected-output.txt /tmp/dev-130-output
```

DEV-131:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s fixtures/dev-131/tests -p 'test_*.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 fixtures/dev-131/proof_runner.py
```

DEV-138:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v tests.test_dev_138_fixtures
swiftc -warnings-as-errors -parse-as-library \
  fixtures/dev-138/HandoffReducer.swift fixtures/dev-138/DeterministicScenarios.swift \
  -o /tmp/dev-138-scenarios
/tmp/dev-138-scenarios > /tmp/dev-138-results.jsonl
diff -u fixtures/dev-138/expected-results.jsonl /tmp/dev-138-results.jsonl
```

### Scope and hygiene

```bash
git diff --check
git diff --name-status origin/main...HEAD
git status --short
find . -type d -name __pycache__ -o -name '*.pyc'
git ls-files --others --exclude-standard
```

Require exactly the 16 paths above in the branch delta, no repository Python
cache, no untracked files, and a clean worktree before and after each commit.

## Evidence-only binding and merge handoff

First create a source commit containing only the intended source/test/runbook
paths. Record its full SHA and tree. Only after that source commit exists and
the worktree is clean may the evidence ledger change in a separate evidence-only
commit. The ledger must record the exact source SHA/tree, actual line/test/count
reductions, command results, normalized hashes, and unchanged historical rows.

Historical structural or directed-reference host results stay bound to their
older candidate SHA/tree. They must not be relabelled as current evidence.
No live host/model rerun is authorized here, and no historical row, optional
directed probe, Markdown presence, install/cache proof, or model response can
substitute for the mandatory combined-tip gate.

Hand the immutable DEV-137 source tip to DEV-136. DEV-136 must rebase above that
exact tip and run the fresh 25-case workflow-triggered matrix: five workflows
times direct, ambiguous, injected/malicious, invalid-artifact, and unsafe-
execution variants. Every valid/invalid route, minimal exact reference load,
fictional-API noninvention rule, and normalized host boundary must pass on the
combined tip. Until that evidence-only combined result passes, retain:

```text
blocked/production_skills_not_integrated
```

DEV-137 remains In Progress. Push, merge, tag, publish, or release requires
separate authorization.
