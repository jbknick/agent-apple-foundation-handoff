# DEV-138 deterministic Swift handoff fixtures

These repository-only fixtures exercise a pure Foundation reducer and a closed,
canonical JSONL oracle. They are test infrastructure, not plugin payload or a
production handoff runtime.

## Case map

The canonical oracle contains exactly these 43 cases:

- Core, route, owner, transition, and phase: `DEV138-BATON-VALID`,
  `DEV138-CONSULTATION-VALID`, `DEV138-SCHEMA-MISSING`,
  `DEV138-ROUTE-DISALLOWED`, `DEV138-OWNER-BATON-SOURCE`,
  `DEV138-OWNER-CONSULT-CHILD`, `DEV138-EDGE-INVALID`,
  `DEV138-BUDGET-EXCEEDED`, `DEV138-LOOP`, and `DEV138-PHASE-INVALID`.
- Context, grant, and tool policy: `DEV138-INJECTION-IGNORED`,
  `DEV138-C3-BLOCKED`, `DEV138-C3-LEAK`, `DEV138-C2-REDACTED`,
  `DEV138-C2-UNREDACTED`, `DEV138-CONTEXT-REQUIRED-MISSING`,
  `DEV138-TOOL-UNAUTHORIZED`, `DEV138-RESULT-SPOOFED`,
  `DEV138-GRANT-AUTH-EXPIRED`, `DEV138-GRANT-CLASS-MISMATCH`,
  `DEV138-GRANT-DESTINATION-MISMATCH`, `DEV138-GRANT-FIELD-MISMATCH`,
  `DEV138-GRANT-POLICY-STALE`, `DEV138-GRANT-PURPOSE-MISMATCH`, and
  `DEV138-GRANT-STATE-STALE`.
- Effect, recovery, replay, and cancellation: `DEV138-PRECOMMIT-ROLLBACK`,
  `DEV138-UNCERTAIN-RECOVERY`, `DEV138-RECONCILIATION-UNAVAILABLE`,
  `DEV138-REPLAY-SUPPRESSED`, `DEV138-RECONCILED-RETRY`,
  `DEV138-CANCEL-PRECOMMIT`, `DEV138-CANCEL-UNCERTAIN`,
  `DEV138-CANCEL-ERASES-RECOVERY`, `DEV138-RECOVERY-TERMINATED`,
  `DEV138-EFFECT-DUPLICATE-LEDGER`, `DEV138-EFFECT-REPLAY-COMMAND`, and
  `DEV138-EFFECT-RETRY-BEFORE-RECONCILE`.
- Availability, transcript, and evidence: `DEV138-MODEL-UNAVAILABLE-EXPLICIT`,
  `DEV138-MODEL-UNAVAILABLE-SAFE`, `DEV138-FALLBACK-EXPANDS-TRUST`,
  `DEV138-TRANSCRIPT-REPAIRED`, `DEV138-TRANSCRIPT-UNBALANCED`, and
  `DEV138-EVIDENCE-LEAKAGE`.

## Truth boundary

The DEV-138 reducer and the reused baton fixture are
`pseudocode_deterministic_mock`. Compiling them does not establish Apple API or
probabilistic model behavior.

The reused DEV-128 stable-surface, generable-macro, availability,
transcript-round-trip, and session-isolation rows are `compiled_sdk_26_5` only
after the environment gate confirms Swift 6.3.3, SDK 26.5, and target
`arm64-apple-macos26.0`. The installed
`arm64e-apple-macos.swiftinterface` row is
`interface_verified_sdk_26_5` only when its SHA-256 is exactly
`ff2285670b0966addb9827dc895a3ee3c9db6e186baae62c034fed012632aacc`.

These gates perform no live generation, model-selected tool call, network or
provider request, credential lookup, paid-service call, entitlement operation,
or hardware-dependent capability assertion. Availability output records mutable
host state and is not a generation result.

## Reducer invariants

Baton proposals bind the active profile/provider and independent state/policy
versions at proposal and commit; pending validation also binds the baton marker,
allowed edge, and unvisited destination. Effect lifecycle events require one
total ledger row for the effect. Validator checks bind every command to one
budgeted, non-future ledger identity with a declared checkpoint and truth state;
exact historical command/record pairs remain valid after state advances.
Resolved stable truth must cross-bind coherent repair facts with a positive,
monotonic reconciliation count. A retry records a typed confirmed-not-applied
basis, consumes retry authority, accepts only its own result, and remains valid
through renewed uncertainty and later reconciliation.

Evidence extensions and prohibited content are compared case-insensitively.
Fingerprint verification still hashes the original content exactly.

## Foundation-only deterministic commands

Run from the repository root:

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

## SDK 26.5 commands

The positive matrix reuses DEV-128 sources directly. The first five rows are
`compiled_sdk_26_5`; the baton row remains
`pseudocode_deterministic_mock`.

```bash
set -e
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT
SWIFT_VERSION="$(swiftc --version)"
SDK="$(xcrun --sdk macosx --show-sdk-path)"
SDK_VERSION="$(xcrun --sdk macosx --show-sdk-version)"
TARGET=arm64-apple-macos26.0
test "$SDK_VERSION" = 26.5

swiftc -typecheck -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/stable-surface.swift
swiftc -typecheck -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/generable-macro.swift
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

INTERFACE="$(find \
  "$SDK/System/Library/Frameworks/FoundationModels.framework/Modules/FoundationModels.swiftmodule" \
  -name 'arm64e-apple-macos.swiftinterface' -print -quit)"
test -n "$INTERFACE"
test "$(shasum -a 256 "$INTERFACE" | awk '{print $1}')" = \
  ff2285670b0966addb9827dc895a3ee3c9db6e186baae62c034fed012632aacc
```

## Expected-blocker commands

Each blocked source must fail compilation and match every capability-specific
diagnostic below. Generic nonzero compilation is `fail`; it is not an expected
blocker pass.

```bash
set -e
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT
SDK="$(xcrun --sdk macosx --show-sdk-path)"

set +e
swiftc -typecheck -target arm64-apple-macos27.0 -sdk "$SDK" \
  fixtures/dev-128/blocked/os-27-beta-surface.swift \
  >"$TMPDIR/beta.out" 2>&1
beta_rc=$?
set -e
test "$beta_rc" -ne 0
rg -q "DynamicProfile.*not a member type|has no member 'Profile'" \
  "$TMPDIR/beta.out"
rg -q "extra arguments at positions #1, #2 in call" \
  "$TMPDIR/beta.out"
rg -q "extra argument 'toolCallingMode' in call" \
  "$TMPDIR/beta.out"

set +e
swiftc -typecheck -target arm64-apple-macos27.0 -sdk "$SDK" \
  fixtures/dev-128/blocked/evaluations-import.swift \
  >"$TMPDIR/evaluations.out" 2>&1
evaluations_rc=$?
set -e
test "$evaluations_rc" -ne 0
rg -q "no such module 'Evaluations'" "$TMPDIR/evaluations.out"
```

## Release blockers

The SDK test captures `swiftc`, `xcrun`, and the SDK directory once, verifies
strict normalized version output, and brackets invocations with the same exact
device, inode, type, mode, size, modification-time, and change-time snapshots.
Missing tools produce `unittest.SkipTest` messages beginning
`blocked/missing_swiftc` or `blocked/missing_xcrun`; either skip is a release
blocker, never a pass. An SDK other than exactly 26.5 produces
`blocked/sdk_version_mismatch` and requires matrix reclassification.

A missing or mismatched installed interface, a positive probe failure, an
expected-blocker compile success, or a nonzero compile without the complete
capability-specific diagnostic set is `fail`. Newly supported SDK surfaces must
be reclassified instead of weakening a diagnostic.
