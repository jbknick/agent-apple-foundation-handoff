# DEV-138 Deterministic Swift Handoff Fixtures Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a repository-only Foundation Swift reducer and exact adversarial oracle that prove the approved handoff state, security, recovery, Apple SDK, packaging, and evidence contracts offline.

**Architecture:** Two direct-`swiftc` sources implement a pure framework-neutral reducer and a sorted synthetic scenario executable. The executable emits canonical JSONL; a separate tracked JSONL file is the sole expected-outcome oracle. A Python `unittest` module compiles/runs twice, performs exact/mutation checks, reuses DEV-128 sources directly, records normalized environment states, maps DEV-134 identities, and proves fixtures stay outside the plugin package.

**Tech Stack:** Swift 6 / Foundation, `swiftc`, Python 3 standard library and `unittest`, JSON Lines, macOS SDK 26.5 Command Line Tools, `xcrun`, BATS 1.13.0, and existing DEV-128/130/131 fixtures.

## Global constraints

- Work only on `codex/dev-138-deterministic-swift-fixtures` from
  `bdbfd335e32eba3efee32f2aac08bd3c2a100368`.
- Follow DEV-138 Linear decision comment
  `4bf0b19c-1a3a-485b-ac2e-823e05cbee22`; do not change it implicitly.
- Add no Swift package/project, production runtime, sample app, skill,
  reference, plugin metadata, schema, generated artifact, generator behavior,
  dependency, network call, credential, PCC/provider call, model call, hardware
  gate, hook, agent, command, MCP server, release, or publication.
- `fixtures/dev-138/` is repository-only and absent from the effective package
  and advertised capabilities.
- Treat reducer output as `pseudocode_deterministic_mock`, not Apple behavior.
  Reuse DEV-128 sources instead of copying Apple signatures.
- Keep exact check IDs and sorted expected violations from the design. Expected
  outcomes exist only in `expected-results.jsonl`, never in Swift cases.
- Use TDD: observe each focused RED failure before the smallest GREEN change;
  do not weaken an oracle to turn RED green.
- Default proof is offline and credential-free. Normalize blockers and never
  commit raw diagnostics or literal local paths.
- Do not invoke Claude Code. Claude Code, `pre-commit`, and `markdownlint`
  remain `blocked/deferred_by_owner`; BATS remains required.

## File responsibility map

| Path | Action | Responsibility |
| --- | --- | --- |
| `fixtures/dev-138/HandoffReducer.swift` | Create | State/policy/event types, reducer, invariant validator, normalized result. |
| `fixtures/dev-138/DeterministicScenarios.swift` | Create | Exact scenario corpus and canonical JSONL executable. |
| `fixtures/dev-138/expected-results.jsonl` | Create | Sole sorted expected status/violation/observable oracle. |
| `fixtures/dev-138/README.md` | Create | Case map, truth boundary, exact commands and blockers. |
| `tests/test_dev_138_fixtures.py` | Create | TDD harness, mutation tests, SDK probes, environment, DEV-134 map, package proof. |
| `tests/test_plugin_contract.py` | Modify | Assert DEV-138 repository fixture never enters copied package payload. |
| `docs/research/evidence/dev-138-command-transcript.md` | Create | Final normalized evidence matrix and hashes. |

---

### Task 1: Define the executable/oracle contract test-first

**Files:**
- Create: `tests/test_dev_138_fixtures.py`
- Create: `fixtures/dev-138/expected-results.jsonl`

**Interfaces:**
- `compile_fixture() -> Path`
- `run_fixture(executable: Path) -> bytes`
- `parse_jsonl(payload: bytes) -> list[dict[str, object]]`
- `load_oracle() -> list[dict[str, object]]`
- `environment_row() -> dict[str, object]`

- [ ] **Step 1: Write the failing fixture-presence and closed-output tests**

Create `tests/test_dev_138_fixtures.py` using only the Python standard library.
Define exact source/oracle paths and assert:

```python
ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "fixtures" / "dev-138"
SOURCES = (
    FIXTURE_ROOT / "HandoffReducer.swift",
    FIXTURE_ROOT / "DeterministicScenarios.swift",
)
ORACLE = FIXTURE_ROOT / "expected-results.jsonl"
CHECK_IDS = {
    "D-SCHEMA-001", "D-ROUTE-001", "D-OWNER-001",
    "D-TRANSITION-001", "D-TOOL-001", "D-CONTEXT-001",
    "D-CONTEXT-002", "D-GRANT-001", "D-PHASE-001",
    "D-EFFECT-001", "D-EFFECT-002", "D-FALLBACK-001",
    "D-EVIDENCE-001", "D-RUBRIC-001",
}
RESULT_KEYS = {
    "schemaVersion", "caseId", "status", "violations", "pattern",
    "activeProfile", "finalResponseOwner", "phase", "stateVersion",
    "policyVersion", "transitionCount", "transitionBudget",
    "executorCommandCount", "effectCount", "fallback",
    "contextIncluded", "contextExcluded", "auditEvents",
}
```

The first tests require both sources, validate every JSONL line is a closed
object with sorted unique case IDs and sorted unique `violations`, require
violations to be a subset of `CHECK_IDS`, and require exact byte equality
between executable output and the oracle.

- [ ] **Step 2: Verify RED for missing Swift sources**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_dev_138_fixtures.Dev138FixtureTests.test_output_matches_exact_oracle -v
```

Expected: nonzero assertion naming missing
`fixtures/dev-138/HandoffReducer.swift`; no skip and no generic compiler error.

- [ ] **Step 3: Add the complete oracle rows before implementation**

Write `expected-results.jsonl` from the design matrix. Use one compact
sorted-key object per case, lexical `caseId` order, the exact violation sets,
and normalized observables. Passing blocked-adversary cases have `status:
"pass"` and `violations: []`; deliberately invalid outcomes have `status:
"fail"` and the exact listed set.

The test must reject an omitted, duplicate, extra, reordered, malformed, or
unknown-ID oracle row.

- [ ] **Step 4: Keep RED at the implementation boundary**

Run the focused test again. Expected: source-presence/compile RED remains; the
oracle shape itself passes.

Do not commit a red state. Task 1 becomes green in Task 2 and is included in
that atomic commit.

---

### Task 2: Implement the smallest Foundation-only reducer and happy paths

**Files:**
- Create: `fixtures/dev-138/HandoffReducer.swift`
- Create: `fixtures/dev-138/DeterministicScenarios.swift`
- Modify: `tests/test_dev_138_fixtures.py`

**Core Swift interfaces:**

```swift
enum Pattern: String, Codable { case batonPass, isolatedConsultation }
enum Phase: String, Codable { case stable, transitioning, recoveryRequired, terminated }
enum DataClass: Int, Codable { case c0Public, c1TaskPrivate, c2Sensitive, c3NeverTransfer }
struct ContextField: Equatable { /* class plus complete provenance */ }
struct BoundaryGrant: Equatable { /* all bound fields plus both versions */ }
struct EffectRecord: Equatable { /* effectID, truth, reconciled */ }
struct HandoffState: Equatable { /* exact design state */ }
enum TrustedEvent: Equatable { /* propose, commit, fail, cancel, reconcile, replay */ }
struct ReducerDecision: Equatable { let state: HandoffState; let command: ExecutorCommand? }
struct CaseResult: Codable { /* exact closed JSONL shape */ }
enum HandoffReducer {
    static func reduce(state: HandoffState, event: TrustedEvent) -> ReducerDecision
    static func validate(_ observation: ScenarioObservation) -> [String]
}
```

- [ ] **Step 1: Implement value types and fail-closed validation**

Use `Foundation` only. Preserve independent versions, phase-before-budget
validation, atomic context rejection, exact grant bindings, provenance checks,
one effect identity, and sorted metadata-only audit labels. Never parse a
trusted event from untrusted text.

- [ ] **Step 2: Implement valid baton-pass and consultation reducers**

Add `DEV138-BATON-VALID` and `DEV138-CONSULTATION-VALID`. Baton-pass commits
destination active/final ownership. Consultation keeps the parent active/final
owner and uses an isolated child transcript identity.

- [ ] **Step 3: Add canonical encoding and executable ordering**

`DeterministicScenarios.swift` builds scenarios without expected outcomes,
sorts by `caseId`, evaluates them, and encodes with:

```swift
let encoder = JSONEncoder()
encoder.outputFormatting = [.sortedKeys, .withoutEscapingSlashes]
```

Write exactly one encoded object plus `\n` per case. The executable must never
open `expected-results.jsonl`.

- [ ] **Step 4: Verify the focused test is still RED for missing cases**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_dev_138_fixtures.Dev138FixtureTests.test_output_matches_exact_oracle -v
```

Expected: compile succeeds, but byte comparison fails because the executable
has only the two initial rows.

- [ ] **Step 5: Add schema/route/owner/transition baseline cases**

Implement through `DEV138-LOOP`, including schema, route, both owner errors,
invalid edge, budget exhaustion, and loop detection. Return sorted violations
from computed checks only.

- [ ] **Step 6: Verify the implemented core and deterministic repeat**

Add a separate core-family test that evaluates the implemented cases without
changing, filtering, or weakening the full-oracle test. Add a repeat test:

```python
self.assertEqual(run_fixture(executable), run_fixture(executable))
```

Expected: the core-family test is green and byte-identical; the full-oracle test
remains intentionally RED for the still-missing adversarial cases. Do not commit
this intermediate red work. Continue directly to Task 3 and commit only after
the complete repository suite is green.

---

### Task 3: Add context, grant, tool, effect, recovery, and fallback cases

**Files:**
- Modify: `fixtures/dev-138/HandoffReducer.swift`
- Modify: `fixtures/dev-138/DeterministicScenarios.swift`
- Modify: `fixtures/dev-138/expected-results.jsonl`
- Modify: `tests/test_dev_138_fixtures.py`

- [ ] **Step 1: Write RED mutation tests for each check family**

Add tests that mutate a valid in-memory scenario independently and assert the
exact computed set for:

```text
D-TOOL-001
D-CONTEXT-001
D-CONTEXT-002
D-GRANT-001
D-PHASE-001
D-EFFECT-001
D-EFFECT-002
D-FALLBACK-001
D-EVIDENCE-001
```

For every mutation, assert no unrelated check appears. Run the focused test and
observe RED because validators/cases do not exist.

- [ ] **Step 2: Implement untrusted-input and context policy cases**

Add `DEV138-INJECTION-IGNORED`, `DEV138-C3-BLOCKED`,
`DEV138-C2-REDACTED`, `DEV138-TOOL-UNAUTHORIZED`,
`DEV138-RESULT-SPOOFED`, `DEV138-CONTEXT-REQUIRED-MISSING`,
`DEV138-C3-LEAK`, and `DEV138-C2-UNREDACTED`.

The blocked C3 case must use a synthetic sentinel and assert it appears in
neither provider serialization nor audit output. The evidence-leak case later
uses only synthetic sentinel values.

- [ ] **Step 3: Implement and mutate every exact grant binding independently**

Add explicit state-version, policy-version, destination, purpose, class, field,
and `DEV138-GRANT-AUTH-EXPIRED` cases. Each must produce only
`["D-GRANT-001"]`.

From one valid grant, create one mutation test per binding below. Each test
changes exactly the named value and expects only `["D-GRANT-001"]`:

```text
grant_person_mismatch                 person identity
grant_session_mismatch                session identity
grant_source_profile_mismatch         source profile
grant_source_provider_mismatch        source provider
grant_destination_profile_mismatch    destination profile
grant_destination_provider_mismatch   destination provider
grant_purpose_mismatch                purpose
grant_class_mismatch                  exact allowed classes
grant_field_mismatch                  exact allowed fields
grant_tool_mismatch                   exact allowed tools
grant_retention_mismatch              retention
grant_expired                         expiry/authentication validity
grant_exceptional_c2_missing          exceptional C2 permission
grant_state_version_stale             stateVersion
grant_policy_version_stale            policyVersion
```

Do not combine source profile/provider or destination profile/provider into one
mutation. Use deterministic fixture time for expiry; do not inspect credentials
or live authentication state.

- [ ] **Step 4: Implement failure, recovery, replay, and cancellation**

Add precommit rollback, uncertain recovery, valid
`DEV138-RECONCILIATION-UNAVAILABLE`, replay suppression, reconciled retry,
precommit cancellation, uncertain cancellation, invalid phase,
recovery-termination, duplicate ledger, replay-command, retry-before-reconcile,
and cancellation-erases-recovery cases.

For replay, assert one ledger entry and `command == nil`. For no-safe
reconciliation, snapshot authority, pending transition, stable checkpoint,
transition/tool/effect counts, effect ledger, and repair facts before the event;
assert every snapshot value remains equal, phase remains `recoveryRequired`,
the normalized outcome is repair-blocked/unavailable, and `command == nil`.
For the combined late cancellation mutation, emit exactly
`["D-EFFECT-001","D-PHASE-001"]` in lexical order.

- [ ] **Step 5: Implement availability fallback and transcript repair**

Add both valid unavailable-model outcomes, unsafe trust-expanding fallback,
valid transcript repair, and unbalanced transcript reuse. The mock never calls
`SystemLanguageModel`; availability is a typed synthetic application event.

- [ ] **Step 6: Implement metadata-only evidence validation**

Add `DEV138-EVIDENCE-LEAKAGE` with one synthetic record containing prohibited
raw-content classification, credential sentinel, absolute-path marker, and
`.trace` extension. It emits only `["D-EVIDENCE-001"]`; raw values never enter
stdout/audit.

- [ ] **Step 7: Verify exact full-corpus GREEN**

```bash
set -e
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_dev_138_fixtures -v
```

Expected: every design case appears once; exact golden and byte-identical repeat
pass; every mutation emits exactly its expected sorted set.

- [ ] **Step 8: Commit the adversarial matrix**

```bash
git add fixtures/dev-138 tests/test_dev_138_fixtures.py
git diff --cached --check
git commit -m "test(DEV-138): cover adversarial handoff recovery"
```

---

### Task 4: Reuse DEV-128 SDK 26.5 probes and record environment truth

**Files:**
- Modify: `tests/test_dev_138_fixtures.py`
- Create: `fixtures/dev-138/README.md`

- [ ] **Step 1: Write the RED environment/SDK matrix test**

The test captures `swiftc` and `xcrun` with `shutil.which`, validates strict
version output, and emits only normalized values. Missing tools create a
`unittest.SkipTest` message beginning with `blocked/`; release validation treats
that skip as a blocker, never a pass.

Assert SDK version is exactly `26.5` before assigning SDK 26.5 labels. A
different SDK yields `blocked/sdk_version_mismatch` and requires matrix
reclassification.

- [ ] **Step 2: Add exact Foundation-only fixture commands to README**

```bash
set -e
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT
swiftc -warnings-as-errors -parse-as-library \
  fixtures/dev-138/HandoffReducer.swift \
  fixtures/dev-138/DeterministicScenarios.swift \
  -o "$TMPDIR/dev-138-fixtures"
"$TMPDIR/dev-138-fixtures" >"$TMPDIR/first.jsonl"
"$TMPDIR/dev-138-fixtures" >"$TMPDIR/second.jsonl"
cmp "$TMPDIR/first.jsonl" "$TMPDIR/second.jsonl"
diff -u fixtures/dev-138/expected-results.jsonl "$TMPDIR/first.jsonl"
```

- [ ] **Step 3: Add exact SDK and target probes**

```bash
set -e
SWIFT_VERSION="$(swiftc --version)"
SDK="$(xcrun --sdk macosx --show-sdk-path)"
SDK_VERSION="$(xcrun --sdk macosx --show-sdk-version)"
TARGET=arm64-apple-macos26.0
test "$SDK_VERSION" = 26.5

swiftc -typecheck -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/stable-surface.swift
swiftc -parse-as-library -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/availability-probe.swift \
  -o "$TMPDIR/availability"
"$TMPDIR/availability" >"$TMPDIR/availability.out"
rg -q '^availability=' "$TMPDIR/availability.out"
rg -q '^isAvailable=' "$TMPDIR/availability.out"
rg -q '^contextSize=[0-9]+$' "$TMPDIR/availability.out"
rg -q '^supportsCurrentLocale=' "$TMPDIR/availability.out"

swiftc -parse-as-library -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/transcript-roundtrip.swift \
  -o "$TMPDIR/transcript"
test "$("$TMPDIR/transcript")" = \
  'entries=3 codableRoundTrip=true rehydrated=true'

swiftc -parse-as-library -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/session-isolation.swift \
  -o "$TMPDIR/isolation"
test "$("$TMPDIR/isolation")" = \
  'parentEntries=1 childEntries=1 isolated=true'

swiftc -parse-as-library -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/baton-pass-state.swift \
  -o "$TMPDIR/baton"
test "$("$TMPDIR/baton")" = \
  'source=research destination=review active=review finalOwner=review transferred=true'
```

The first four supported Foundation Models rows are
`compiled_sdk_26_5`; the baton mock is
`pseudocode_deterministic_mock` despite compiling.

- [ ] **Step 4: Verify the installed interface identity**

```bash
INTERFACE="$(find \
  "$SDK/System/Library/Frameworks/FoundationModels.framework/Modules/FoundationModels.swiftmodule" \
  -name 'arm64e-apple-macos.swiftinterface' -print -quit)"
test -n "$INTERFACE"
test "$(shasum -a 256 "$INTERFACE" | awk '{print $1}')" = \
  ff2285670b0966addb9827dc895a3ee3c9db6e186baae62c034fed012632aacc
```

This row is `interface_verified_sdk_26_5`. The literal interface/SDK path is
transient and never copied into tracked evidence.

- [ ] **Step 5: Re-run the authoritative expected blockers**

Use the exact commands and three independent diagnostic checks from
`fixtures/dev-128/README.md` for:

- `blocked/generable-macro.swift` -> missing `FoundationModelsMacros`;
- `blocked/os-27-beta-surface.swift` -> dynamic profile/profile,
  profile-session initializer, and `toolCallingMode` diagnostics; and
- `blocked/evaluations-import.swift` -> no `Evaluations` module.

Each compile must be nonzero and match its capability-specific diagnostic.
Generic nonzero is `fail`. A future supported surface requires reclassification,
not a weaker regex.

- [ ] **Step 6: Verify SDK tests GREEN**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_dev_138_fixtures.Dev138SDKTests -v
```

Expected on the approved host: Swift 6.3.2, target
`arm64-apple-macos26.0`, SDK 26.5, positive DEV-128 matrix pass, and exact
expected blockers. Record normalized versions only.

- [ ] **Step 7: Commit SDK integration and README**

```bash
git add fixtures/dev-138/README.md tests/test_dev_138_fixtures.py
git diff --cached --check
git commit -m "test(DEV-138): verify SDK 26.5 fixture boundary"
```

---

### Task 5: Prove router mapping and offline package exclusion

**Files:**
- Modify: `tests/test_dev_138_fixtures.py`
- Modify: `tests/test_plugin_contract.py`

- [ ] **Step 1: Write RED DEV-134 mapping assertions**

Load `docs/research/evidence/dev-134-activation-prototype.json` and assert exact
counts `6/6/3`, unique identities, and that every applicable/not-applicable
guardrail is in `CHECK_IDS`. Map baton, consultation, flawed reducer, recovery,
and review-first identities to their named DEV-138 cases. Do not run either
host or pretend prototype activation is runtime proof.

- [ ] **Step 2: Write RED package-exclusion assertion**

In `tests/test_plugin_contract.py`, extend the existing package test with a
temporary copy and assert:

```python
self.assertTrue((ROOT / "fixtures/dev-138").is_dir())
self.assertFalse((plugin_root / "fixtures").exists())
assert_plugin_package_contract(self, copied_plugin_root)
```

Scan copied relative payload names and require no `fixtures`, `dev-138`,
`tests`, `docs`, `research`, `.trace`, `.xcresult`, credential sentinel, or
literal private path. Use no network, credential, Codex home, or host install.

- [ ] **Step 3: Observe and then fix RED**

Run the two focused tests before their mapping/assertion implementation;
expected RED names the missing mapping/package assertion. Add only the mapping
table and package-copy checks, then rerun:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_dev_138_fixtures.Dev138ContractTests \
  tests.test_plugin_contract.PluginContractTests.test_dev_138_fixtures_are_repository_only -v
```

Expected: pass with a local temporary package copy and no external state.

- [ ] **Step 4: Run generator and BATS regressions without changing them**

```bash
set -e
PYTHONDONTWRITEBYTECODE=1 python3 scripts/sync_generated_artifacts.py --check
bats tests/plugin_skeleton.bats
git diff --exit-code -- AGENTS.md .agents/plugins/marketplace.json \
  plugins/apple-foundation-models-handoff/.codex-plugin/plugin.json
```

Expected: generator synchronized; BATS `3/3`; no generated diff.

- [ ] **Step 5: Commit the repository/package boundary**

```bash
git add tests/test_dev_138_fixtures.py tests/test_plugin_contract.py
git diff --cached --check
git commit -m "test(DEV-138): prove repository-only fixture packaging"
```

---

### Task 6: Capture normalized evidence and run the full validation matrix

**Files:**
- Create: `docs/research/evidence/dev-138-command-transcript.md`
- Modify: `fixtures/dev-138/README.md` only if final commands/counts need correction

- [ ] **Step 1: Run focused and inherited suites**

```bash
set -e
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_dev_138_fixtures -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests -p 'test_*.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s fixtures/dev-131/tests -p 'test_*.py' -v
python3 fixtures/dev-131/proof_runner.py >"$TMPDIR/dev131.json"
python3 -m compileall -q fixtures/dev-131

swiftc -warnings-as-errors -parse-as-library \
  fixtures/dev-130/HandoffSecurityPolicy.swift \
  fixtures/dev-130/AdversarialScenarios.swift \
  -o "$TMPDIR/dev130"
"$TMPDIR/dev130" >"$TMPDIR/dev130.out"
diff -u fixtures/dev-130/expected-output.txt "$TMPDIR/dev130.out"

bats tests/plugin_skeleton.bats
PYTHONDONTWRITEBYTECODE=1 python3 scripts/sync_generated_artifacts.py --check
git diff --check
```

Expected: DEV-138 exact/repeat/mutation matrix passes; repository suite passes;
DEV-131 remains 26/26 with 11/11 oracle; DEV-130 remains 7/7 exact; BATS remains
3/3; generation is synchronized.

- [ ] **Step 2: Run the SDK matrix from Task 4**

Execute all positive, interface, and expected-blocker commands exactly. Record
only normalized compiler version, target, SDK version, evidence label,
diagnostic class, exit code, and status. Do not record the SDK path or raw
diagnostic text.

- [ ] **Step 3: Prove JSONL identity and publish hashes**

```bash
"$TMPDIR/dev-138-fixtures" >"$TMPDIR/dev138-first.jsonl"
"$TMPDIR/dev-138-fixtures" >"$TMPDIR/dev138-second.jsonl"
cmp "$TMPDIR/dev138-first.jsonl" "$TMPDIR/dev138-second.jsonl"
diff -u fixtures/dev-138/expected-results.jsonl "$TMPDIR/dev138-first.jsonl"
shasum -a 256 fixtures/dev-138/expected-results.jsonl \
  "$TMPDIR/dev138-first.jsonl" "$TMPDIR/dev138-second.jsonl"
```

Expected: all three SHA-256 values are identical.

- [ ] **Step 4: Write the normalized evidence transcript**

`docs/research/evidence/dev-138-command-transcript.md` must contain:

- exact commit/base and tracked DEV-138 path list;
- exact commands and exit codes;
- case counts, pass/fail-fixture counts, exact-violation result, repeat result,
  and JSONL SHA-256;
- normalized Swift/compiler/target/SDK/interface identity;
- DEV-128 positive and expected-blocker rows with exact evidence labels;
- DEV-130, DEV-131, repository, BATS, generation, package, scope, privacy, and
  whitespace results;
- `blocked/deferred_by_owner` rows for Claude Code, `pre-commit`, and
  `markdownlint` without invoking them;
- blocked OS/Xcode 27 capabilities and all no-network/no-credential nonclaims;
  and
- no literal local path, raw `PATH`, raw diagnostics, raw prompt/response/tool
  content, credential, `.trace`, or `.xcresult`.

- [ ] **Step 5: Run privacy/scope/final-diff gates**

```bash
set -e
test -z "$(find . -name '__pycache__' -o -name '*.pyc')"
! rg -n '/Users/|/home/|BEGIN (RSA|OPENSSH|EC) PRIVATE KEY|DEV138_SECRET_SENTINEL' \
  fixtures/dev-138/expected-results.jsonl fixtures/dev-138/README.md \
  docs/research/evidence/dev-138-command-transcript.md
! find . -name '*.trace' -o -name '*.xcresult' | rg .
git diff --check
git status --short
```

Review the complete issue delta against `bdbfd335e32eba3efee32f2aac08bd3c2a100368`
and require only the seven planned implementation paths.

- [ ] **Step 6: Commit final evidence**

```bash
git add fixtures/dev-138/README.md \
  docs/research/evidence/dev-138-command-transcript.md
git diff --cached --check
git commit -m "docs(DEV-138): record deterministic fixture evidence"
```

## Atomic implementation commit boundaries

| Commit | Scope | Must be green before commit |
| --- | --- | --- |
| `test(DEV-138): cover deterministic handoff recovery` | Closed oracle, reducer, canonical output, and complete state/context/grant/tool/effect/recovery/cancellation/fallback/transcript/evidence matrix. | Full exact case/violation/mutation suite; no intermediate red commit. |
| `test(DEV-138): verify SDK 26.5 fixture boundary` | DEV-128 reuse, normalized environment, README commands. | Exact positive/interface/blocker matrix. |
| `test(DEV-138): prove repository-only fixture packaging` | DEV-134 map and offline package/generator/BATS boundary. | Focused contract plus inherited package/generator/BATS tests. |
| `docs(DEV-138): record deterministic fixture evidence` | Final normalized transcript and any command-only README correction. | Entire validation matrix, privacy, scope, clean diff. |

Each commit is independently reviewable, contains no production/plugin payload
change, and is made only after its RED test has been observed and its complete
GREEN gate has passed.

## Final validation matrix

| Layer | Command/owner | Passing result |
| --- | --- | --- |
| DEV-138 deterministic | `tests.test_dev_138_fixtures` | Every case once; exact sorted violations; two byte-identical runs; oracle hash match. |
| DEV-138 mutation | Same module | Each independent mutation returns only its intended `D-*` set. |
| Apple SDK 26.5 | Direct DEV-128 sources | Supported rows compile/run; interface hash matches; blockers have exact diagnostics. |
| DEV-130 | Direct Swift compile/golden | `7/7`, exact output. |
| DEV-131 | Unit suite and proof runner | `26/26`, `11/11`, rubric/evidence gates unchanged. |
| Repository | `unittest discover -s tests` | All tests pass, including package exclusion. |
| Generation | `sync_generated_artifacts.py --check` | Synchronized; no generated diff. |
| BATS | `bats tests/plugin_skeleton.bats` | `3/3`. |
| Packaging | Local temporary package copy | No fixture/test/doc/research/private path or symlink. |
| Evidence/privacy | Scans plus manual transcript review | Only normalized synthetic metadata; no prohibited content/path. |
| Deferred host/tool rows | Owner decision | Claude, pre-commit, markdownlint stay explicit blockers, never passes. |
| Scope | Git diff from base | Only the seven DEV-138 implementation paths; no package/generator/generated change. |

## Completion handoff

Before claiming completion, invoke `superpowers:verification-before-completion`
and run the matrix from a clean exact-head checkout. Update DEV-138 with final
SHA, commands, counts, hashes, package proof, reviewer verdict, and blockers.
Propagate only stable case/check identities and environment semantics to
DEV-136, DEV-137, DEV-139, and DEV-141. Do not merge, tag, publish, or release.
