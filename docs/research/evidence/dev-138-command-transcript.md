# DEV-138 deterministic Swift fixture command transcript

Evidence date: `2026-07-20`

This transcript records the final offline validation matrix for DEV-138. All
results are normalized to compiler version, target, SDK version, interface
hash, evidence label, stable diagnostic class, exit code, count, and status.
It contains no executable location, SDK location, environment search value,
raw compiler diagnostic, model content, prompt, response, tool payload,
credential, or private configuration.

## Identity and scope

- Issue base: `27c7ce6b8d47541711184ceae06b2eecbdc4be8e`
- Exact tested source commit:
  `93cc77dcfac03528644f781eddcae6f62d6e1331`
- Exact tested source tree:
  `5ffa60fc33d8185a91cc6fc01035ebb0ec8d8fb9`
- Branch: `codex/dev-138-deterministic-swift-fixtures`
- The follow-up evidence commit changes only this transcript; it does not change
  the tested source tree above.

The issue delta contains two approved planning paths, which are not counted as
implementation:

1. `docs/superpowers/plans/2026-07-17-dev-138-deterministic-swift-fixtures.md`
2. `docs/superpowers/specs/2026-07-17-dev-138-deterministic-swift-fixtures-design.md`

The implementation scope is exactly these seven paths:

1. `fixtures/dev-138/HandoffReducer.swift`
2. `fixtures/dev-138/DeterministicScenarios.swift`
3. `fixtures/dev-138/expected-results.jsonl`
4. `fixtures/dev-138/README.md`
5. `tests/test_dev_138_fixtures.py`
6. `tests/test_plugin_contract.py`
7. `docs/research/evidence/dev-138-command-transcript.md`

The complete issue delta is exactly nine paths: the two planning paths and the
seven implementation/evidence paths above. No package metadata, generator,
generated artifact, production skill, reference, hook, agent, command, MCP
server, dependency, or runtime was added or modified by DEV-138.

## TDD provenance

The original Task 2 and Task 3 intermediate RED steps are
`unproven/not_captured`. No missing historical output is reconstructed or
claimed as evidence.

The later review-defect REDs are valid implementation records:

| Defect RED | Status | Resolution |
| --- | --- | --- |
| Adversarial outcomes were not sufficiently reducer-derived and command suppression was not proven through the reducer | `valid/observed_before_fix` | `96b714e19314904c7b1678eed0be83e9181d42d2` |
| Fallback, typed proposal, transcript repair, evidence hashing, grant binding, and recovery semantics were incomplete | `valid/observed_before_fix` | `e90d3586203e179fa321f22e6af1c63c6bafd469` |

Task 5 has a separate captured contract RED. The focused command ran three
tests and exited `1` with two failures: the DEV-134 mapping table and the
repository-only package assertion were absent. After the smallest additions,
the same three tests passed. This contract RED does not retroactively prove the
uncaptured Task 2 or Task 3 intermediate RED steps.

The July 19 review round captured the current defects before correction:

| Focused RED | Observed result before fix |
| --- | --- |
| Consultation/effect replay, result consumption/provenance, duplicate context/call validation, and private-root evidence | Five tests exited `1`: four assertion failures and one duplicate-key serialization trap |
| Deterministic request expiry and typed applied/not-applied reconciliation | Two tests exited `1` with missing-type/member compile failures |
| Unique unresolved ledger/command binding | One test emitted `false` and exited `1` |
| Ambiguous call identity and missing originating command | Two focused tests emitted their final `false` values and exited `1` |
| Forged retry authority without reconciled ledger/command provenance | One focused test emitted `false|false|false|true` and exited `1`; the valid fourth path already worked |

The adversarial acceptance round then captured these additional REDs against
the immediately preceding source:

| Focused RED | Observed result before fix |
| --- | --- |
| Proposal state/policy provenance | The proposal probe failed compilation with extra initializer arguments and missing `stateVersion` / `policyVersion` members. |
| Case-insensitive evidence rejection | The six new uppercase/lowercase extension, private-root, trace, and raw-payload assertions all emitted `false`; the focused test exited `1`. |
| Total ledger cardinality at result/recovery/reconciliation/retry boundaries | The result probe ended in `false`; mixed-row recovery and retry probes emitted their new `false` values and exited `1`. |
| Validator command/ledger, truth/checkpoint, budget, and recovery coherence | The three baseline assertions emitted `true`; all twelve new adversarial expectations emitted `false`, and the focused test exited `1`. |
| Retry lineage across renewed uncertainty | Mixed reconciliation/retry, renewed uncertainty, later reconciliation, and forged lineage emitted `false` in the lifecycle probe; a subsequent lone-retry RED emitted only its new ninth value as `false`. |

The final main-inspection follow-up captured these REDs against the prior
reviewed head:

| Focused RED | Observed result before fix |
| --- | --- |
| Historical ledger and pending-proposal coherence | In the validator probe, historical consultation followed by baton commit, orphan/mismatched/reverse-orphan repair facts, and independently stale or disallowed pending proposal fields emitted their new `false` values. |
| Retry completion and monotonic recovery | In the 17-value lifecycle probe, accepted retry completion, late-original refusal, preserved/incremented attempt counts, second confirmed-not-applied authority denial, and forged-basis repair coherence emitted `false`. |
| Typed retry basis | The focused probe failed compilation because `retryBasis` was `String?` and had no typed `confirmedNotApplied` member. |
| Stable repair command binding | After the preceding corrections, the commandless reconciled-repair mutation was the sole `false` value in its updated validator position. |
| Non-retry provenance | In the 29-value validator probe, initial and consultation commands carrying a typed confirmed-not-applied retry basis were the two `false` values. |
| Renewed uncertainty from incoherent retry state | In the 19-value lifecycle probe, a forged retry with erased repair lineage was normalized into recovery instead of being refused; its new expectation was `false`. |
| Malformed recovery self-healing | In the same lifecycle probe, forged transition/checkpoint/truth facts and a negative attempt count were accepted by reconciliation instead of preserving/refusing the snapshot; its new expectation was `false`. |
| Exact reconciliation counts | In the 30-value validator probe, the inflated no-retry count was the sole new `false`; in the 25-value lifecycle probe, all six new pre-retry, post-retry, retry-issued, result-accepted, and resolved count mutations were `false`. |

The first full post-fix run then exposed one oracle-isolation regression: the
synthetic retry-before-reconciliation case also emitted `D-PHASE-001`. Its
awaiting-recovery counter was made phase-coherent so the case continued to
isolate only its intended `D-EFFECT-002` retry-lineage defect. The canonical
oracle was not edited.

The corresponding focused GREEN set passed before the full matrix. The source
commit above contains the tests and smallest reducer correction; no historical
RED output was reconstructed.

## Deterministic DEV-138 oracle

Commands:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_dev_138_fixtures -v

TMPDIR="$(mktemp -d)"
swiftc -warnings-as-errors -parse-as-library \
  fixtures/dev-138/HandoffReducer.swift \
  fixtures/dev-138/DeterministicScenarios.swift \
  -o "$TMPDIR/dev-138-fixtures"
"$TMPDIR/dev-138-fixtures" >"$TMPDIR/dev138-first.jsonl"
"$TMPDIR/dev-138-fixtures" >"$TMPDIR/dev138-second.jsonl"
cmp "$TMPDIR/dev138-first.jsonl" "$TMPDIR/dev138-second.jsonl"
diff -u fixtures/dev-138/expected-results.jsonl \
  "$TMPDIR/dev138-first.jsonl"
shasum -a 256 fixtures/dev-138/expected-results.jsonl \
  "$TMPDIR/dev138-first.jsonl" "$TMPDIR/dev138-second.jsonl"
```

Normalized result:

| Gate | Exit | Result |
| --- | ---: | --- |
| DEV-138 unit module | `0` | `36/36` tests passed; no skip |
| Fixture compile | `0` | `pseudocode_deterministic_mock` |
| Canonical cases | `0` | `43` unique sorted cases |
| Passing fixtures | `0` | `15` |
| Deliberately failing fixtures | `0` | `28` with exact sorted violations |
| First/second run comparison | `0` | byte-identical |
| Oracle/run comparison | `0` | byte-identical |

All three JSONL artifacts have SHA-256:

```text
f665a7e3556e25c82254a480b0d0fb3cc473971e6fa52044daae729c9593fd5d
```

The Swift scenarios do not contain a second expected-outcome oracle, do not
self-attest policy verdicts, and do not implement DEV-131 rubric scoring.

## Apple SDK 26.5 matrix

The exact positive and expected-blocker command blocks are also retained in
`fixtures/dev-138/README.md`. They were rerun with captured compiler, `xcrun`,
and SDK-directory identities. Exact device/inode/type/mode/size/time snapshots
were checked around invocations; a same-path replacement regression also
passed. No skipped SDK test is counted as a pass.

Normalized environment:

| Field | Value | Status |
| --- | --- | --- |
| Apple Swift compiler | `6.3.3` | `pass` |
| Default compiler target | `arm64-apple-macosx26.0` | `pass` |
| Explicit fixture target | `arm64-apple-macos26.0` | `pass` |
| macOS SDK | `26.5` | `pass` |
| Foundation Models arm64e interface SHA-256 | `ff2285670b0966addb9827dc895a3ee3c9db6e186baae62c034fed012632aacc` | `pass` |

Positive commands:

```bash
SDK="$(xcrun --sdk macosx --show-sdk-path)"
TARGET=arm64-apple-macos26.0

swiftc -typecheck -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/stable-surface.swift
swiftc -typecheck -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/generable-macro.swift
swiftc -parse-as-library -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/availability-probe.swift -o "$TMPDIR/availability"
"$TMPDIR/availability" >"$TMPDIR/availability.out"
rg -q '^availability=' "$TMPDIR/availability.out"
rg -q '^isAvailable=' "$TMPDIR/availability.out"
rg -q '^contextSize=[0-9]+$' "$TMPDIR/availability.out"
rg -q '^supportsCurrentLocale=' "$TMPDIR/availability.out"
swiftc -parse-as-library -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/transcript-roundtrip.swift -o "$TMPDIR/transcript"
swiftc -parse-as-library -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/session-isolation.swift -o "$TMPDIR/isolation"
swiftc -parse-as-library -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/baton-pass-state.swift -o "$TMPDIR/baton"
```

| Row | Evidence | Exit | Status |
| --- | --- | ---: | --- |
| Stable surface | `compiled_sdk_26_5` | `0` | `pass` |
| Generable macro | `compiled_sdk_26_5` | `0` | `pass` |
| Availability shape | `compiled_sdk_26_5` | `0` | `pass` |
| Transcript round trip | `compiled_sdk_26_5` | `0` | `pass` |
| Session isolation | `compiled_sdk_26_5` | `0` | `pass` |
| Baton state | `pseudocode_deterministic_mock` | `0` | `pass` |
| Installed interface identity | `interface_verified_sdk_26_5` | `0` | `pass` |

Expected-blocker commands:

```bash
swiftc -typecheck -target arm64-apple-macos27.0 -sdk "$SDK" \
  fixtures/dev-128/blocked/os-27-beta-surface.swift
swiftc -typecheck -target arm64-apple-macos27.0 -sdk "$SDK" \
  fixtures/dev-128/blocked/evaluations-import.swift
```

Raw diagnostics were transient and are not reproduced here. Every blocked row
required nonzero compilation plus its complete stable diagnostic-class match.

| Row | Diagnostic class | Exit | Status |
| --- | --- | ---: | --- |
| OS 27 beta surface | `dynamic_profile_profile_initializer_tool_calling_mode_unavailable` | `1` | `blocked` |
| Evaluations import | `evaluations_module_unavailable` | `1` | `blocked` |
| OS 27 runtime behavior | `installed_sdk_26_5_only` | not run | `blocked` |
| Xcode 27 capability | `installed_sdk_26_5_only` | not run | `blocked` |

These blocker matches establish only that the pinned SDK lacks the named
capabilities. They are not Apple runtime, beta SDK, router, or host proof.

## Inherited validation

Commands:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests -p 'test_*.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s fixtures/dev-131/tests -p 'test_*.py' -v
python3 fixtures/dev-131/proof_runner.py >"$TMPDIR/dev131.json"
PYTHONPYCACHEPREFIX="$TMPDIR/pycache" \
  python3 -m compileall -q fixtures/dev-131

swiftc -warnings-as-errors -parse-as-library \
  fixtures/dev-130/HandoffSecurityPolicy.swift \
  fixtures/dev-130/AdversarialScenarios.swift \
  -o "$TMPDIR/dev130"
"$TMPDIR/dev130" >"$TMPDIR/dev130.out"
diff -u fixtures/dev-130/expected-output.txt "$TMPDIR/dev130.out"

bats tests/plugin_skeleton.bats
PYTHONDONTWRITEBYTECODE=1 \
  python3 scripts/sync_generated_artifacts.py --check
git diff --exit-code -- AGENTS.md .agents/plugins/marketplace.json \
  plugins/apple-foundation-models-handoff/.codex-plugin/plugin.json
```

| Gate | Exit | Result |
| --- | ---: | --- |
| Repository discovery | `0` | `93/93` tests passed |
| DEV-131 unit suite | `0` | `26/26` tests passed |
| DEV-131 proof runner | `0` | `11/11` executed cases matched the oracle; top-level status `pass` |
| DEV-131 compileall | `0` | `pass` |
| DEV-130 Swift compile/golden | `0` | `8/8` scenarios passed; exact golden and byte-identical repeat |
| BATS skeleton | `0` | `3/3` passed |
| Generator check | `0` | synchronized |
| Generated-file diff | `0` | no generated change |

## Mapping and package boundary

Command:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_dev_138_fixtures.Dev138ContractTests \
  tests.test_plugin_contract.PluginContractTests.test_dev_138_fixtures_are_repository_only \
  -v
```

Result: exit `0`; `3/3` tests passed.

- The DEV-134 prototype remains exactly `6` positive, `6` negative, and `3`
  ambiguous identities with stable guardrails, `7` `direct_workflow` owners,
  and `8` `non_positive_router` owners. Tests read both canonical contract
  documents and match all six positive/rejection/clarification text blocks
  exactly; owner metadata is absent from every emitted envelope block.
- The exact baton, consultation, flawed-reducer, recovery, and review-first
  mappings resolve only to deterministic DEV-138 invariant cases.
- The mapping does not prove router activation, review-first/no-edit behavior,
  host capability, or Apple runtime behavior. DEV-131 retains rubric ownership.
- A temporary local copy of the effective plugin preserves the canonical
  package contract and contains no repository fixture, DEV-138, test, docs,
  research, private-state, credential-sentinel, or prohibited runtime artifact.
- The package-exclusion proof uses no network, credential, host install, or
  external state.

## Structural package and Codex checks

The current official plugin validator accepted the metadata-only package.
Bats 1.13.0 passed 3/3, generation was synchronized, and the three generated
outputs had no diff. Two fresh isolated Codex runs used the captured `0.144.5`
executable, produced byte-identical normalized JSON, and verified regular-file
mode/type, exact three-file source/cache membership, source/cache hash equality,
enabled state, and zero capabilities.

| Structural field | Normalized result |
| --- | --- |
| Host/version | `codex` / `0.144.5` |
| Plugin/version | `apple-foundation-models-handoff` / `0.1.0` |
| Cache file count | `3` |
| Canonical manifest SHA-256 | `2ef1c67b4c5d4788b5316dd645aa9e580fea18b6ec5cbfb8759b355af31ae618` |
| Generated manifest SHA-256 | `2cf94a87d9e25e687435e423d3e1f11bf848e5fac3b1ae1399e83c70085047b8` |
| Enabled/capabilities | `true` / `[]` |
| Capability activation | `blocked/production_skill_not_implemented` |

This is local structural discovery, installation, and cache-integrity evidence.
It is not workflow activation, router execution, Apple runtime behavior, or
capability proof.

## Deferred rows and nonclaims

The following owner-deferred tools were not invoked or substituted:

| Row | Exit | Status |
| --- | --- | --- |
| Claude Code | not run | `blocked/deferred_by_owner` |
| pre-commit | not run | `blocked/deferred_by_owner` |
| markdownlint | not run | `blocked/deferred_by_owner` |

DEV-138 is an offline, deterministic, repository-only proof. It performs no
network call, PCC call, provider request, credential lookup, paid-service call,
live model generation, model-selected tool call, entitlement operation, device
hardware gate, capability activation, or release operation. The local Codex
row proves only structural discovery/install/cache integrity; it does not prove
future workflow activation, production routing, or Foundation Models runtime
behavior.

## Final gates

The final evidence commit is gated by:

```bash
test -z "$(find . -name '__pycache__' -o -name '*.pyc')"
git diff --check
git diff --cached --check
git diff --exit-code -- AGENTS.md .agents/plugins/marketplace.json \
  plugins/apple-foundation-models-handoff/.codex-plugin/plugin.json
git status --short
```

A content scanner also constructs prohibited private-root, credential, key,
and runtime-artifact markers from separate string fragments and scans the
oracle, fixture README, transcript, and copied plugin payload. This avoids
placing a prohibited literal into the evidence file merely to describe its
absence. The source commit had a clean worktree, exactly nine issue paths and
seven implementation/evidence paths, no package/generator/generated delta, and
no cache or runtime artifact. The final committed-head result is recorded in
the DEV-138 handoff; no push, merge, tag, publication, release, or downstream
issue mutation is part of this task.
