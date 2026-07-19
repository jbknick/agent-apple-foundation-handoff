# DEV-128 Apple Foundation Models API Surface Implementation Plan

> Execute this plan with `superpowers:subagent-driven-development`. Each task
> receives a fresh implementer, task review, corrections, and re-review before
> the next task begins.

**Goal:** Produce a source-grounded, locally verified Apple Foundation Models
API map, compile/run fixture corpus, and reproducible evidence transcript for
handoff architectures.

**Scope base:** `origin/main`

**Design:**
`docs/superpowers/specs/2026-07-17-dev-128-apple-api-surface-design.md`

**Primary evidence input:** `/tmp/dev-128-evidence.md`, official Apple sources,
the installed SDK interface, and Apple-owned
`foundation-models-utilities@376ca60e61985369d5067bd3c575bdb6a13f0e1b`.
Scratch evidence is an input, not a substitute for rerunning the planned
commands.

**Binding amendment:** The 2026-07-18 Linear amendment requires the durable
stable production bridge chain documented in the design and API map. The
2026-07-19 Xcode 26.6 revalidation reclassifies the macro fixture from blocked
to compiled while preserving the 2026-07-17 Command Line Tools failure as
historical transcript evidence.

**Constraints:** Do not add a package manifest, dependency, production plugin,
skill, generator, runtime, or host metadata. Do not require live generation,
PCC, credentials, paid services, or network in default gates. Negative fixtures
must fail for the expected missing capability. Never edit DEV-127 artifacts.

## Commit boundaries

1. Design: `docs(DEV-128): design Apple API surface research`
2. Plan: `docs(DEV-128): plan Apple API surface research`
3. Task 1: `test(DEV-128): add Apple API compile fixtures`
4. Task 2: `docs(DEV-128): record Apple API verification evidence`
5. Task 3: `docs(DEV-128): map Apple handoff API surface`

Corrections discovered by review use narrow follow-up commits. Do not rewrite
or squash the stack while downstream branches depend on it.

## Task 1: Add compile, run, and expected-blocker fixtures

**Files:**

- Create: `fixtures/dev-128/README.md`
- Create: `fixtures/dev-128/compiled/stable-surface.swift`
- Create: `fixtures/dev-128/compiled/availability-probe.swift`
- Create: `fixtures/dev-128/compiled/transcript-roundtrip.swift`
- Create: `fixtures/dev-128/compiled/session-isolation.swift`
- Create: `fixtures/dev-128/compiled/baton-pass-state.swift`
- Create: `fixtures/dev-128/compiled/generable-macro.swift`
- Create: `fixtures/dev-128/blocked/os-27-beta-surface.swift`
- Create: `fixtures/dev-128/blocked/evaluations-import.swift`

### Step 1: Prove the fixture corpus is absent

Run:

```bash
test ! -e fixtures/dev-128
```

Expected: exit `0` before implementation.

### Step 2: Create positive fixtures

Use `apply_patch` to create:

- a stable surface type-check fixture covering model/session construction,
  availability/context, all five token-count overloads, deterministic tool
  conformance, generation options, prewarm, text response, streaming,
  transcript copy/rehydration, and runtime dynamic schema;
- an availability probe that performs no generation and reports availability,
  `isAvailable`, context size, and locale support;
- an offline transcript Codable round-trip and destination-session rehydration
  probe;
- an offline parent/child session transcript-isolation probe; and
- a pure Swift deterministic baton-pass state mock that starts with the source
  profile, applies one explicit transfer event, ends with the destination
  profile, and asserts destination final-response ownership.
- a static `@Generable`/`@Guide` fixture whose uninvoked async function
  type-checks `respond(... generating: HandoffEnvelope.self)` and typed content
  access without running generation.

The baton-pass file must say in a source comment that it is a deterministic
composition mock, not a shipped Apple `BatonPass` API or an OS 27 dynamic
profile fixture.

### Step 3: Create expected-blocker fixtures

Use `apply_patch` to create minimal probes for:

- OS 27 dynamic profile and tool-calling mode symbols, expected to fail because
  SDK 26.5 lacks them; and
- `import Evaluations`, expected to fail because the module is absent.

Each file must begin with a comment that it is intentionally non-compiling on
the recorded host and name the missing prerequisite.

### Step 4: Write the fixture README

Document every fixture, its evidence label, what it proves, what it does not
prove, exact commands below, and the default-test constraints. Explicitly state
that `compiled` means compile-checked on the recorded SDK, not live generation.

### Step 5: Run positive type-check and deterministic execution gates

Run:

```bash
set -e
SDK="$(xcrun --sdk macosx --show-sdk-path)"
TARGET=arm64-apple-macos26.0

swiftc -typecheck -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/stable-surface.swift

swiftc -typecheck -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/generable-macro.swift

swiftc -parse-as-library -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/availability-probe.swift \
  -o /tmp/dev-128-availability-probe
/tmp/dev-128-availability-probe | tee /tmp/dev-128-availability.out
rg -q '^availability=' /tmp/dev-128-availability.out
rg -q '^isAvailable=' /tmp/dev-128-availability.out
rg -q '^contextSize=[0-9]+$' /tmp/dev-128-availability.out
rg -q '^supportsCurrentLocale=' /tmp/dev-128-availability.out

swiftc -parse-as-library -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/transcript-roundtrip.swift \
  -o /tmp/dev-128-transcript-roundtrip
test "$(/tmp/dev-128-transcript-roundtrip)" = \
  'entries=3 codableRoundTrip=true rehydrated=true'

swiftc -parse-as-library -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/session-isolation.swift \
  -o /tmp/dev-128-session-isolation
test "$(/tmp/dev-128-session-isolation)" = \
  'parentEntries=1 childEntries=1 isolated=true'

swiftc -parse-as-library -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/baton-pass-state.swift \
  -o /tmp/dev-128-baton-pass-state
test "$(/tmp/dev-128-baton-pass-state)" = \
  'source=research destination=review active=review finalOwner=review transferred=true'
```

Expected: all commands exit `0`. Availability values may vary, but all four
fields must exist. No fixture invokes model generation.

### Step 6: Run expected-blocker diagnostic gates

Run:

```bash
set -e
SDK="$(xcrun --sdk macosx --show-sdk-path)"

set +e
swiftc -typecheck -target arm64-apple-macos27.0 -sdk "$SDK" \
  fixtures/dev-128/blocked/os-27-beta-surface.swift \
  >/tmp/dev-128-beta.out 2>&1
beta_rc=$?
set -e
test "$beta_rc" -ne 0
rg -q "DynamicProfile.*not a member type|has no member 'Profile'" \
  /tmp/dev-128-beta.out
rg -q "extra arguments at positions #1, #2 in call" \
  /tmp/dev-128-beta.out
rg -q "extra argument 'toolCallingMode' in call" \
  /tmp/dev-128-beta.out

set +e
swiftc -typecheck -target arm64-apple-macos27.0 -sdk "$SDK" \
  fixtures/dev-128/blocked/evaluations-import.swift \
  >/tmp/dev-128-evaluations.out 2>&1
evaluations_rc=$?
set -e
test "$evaluations_rc" -ne 0
rg -q "no such module 'Evaluations'" /tmp/dev-128-evaluations.out
```

Expected: both compiles exit nonzero and all four exact diagnostic matches exit
`0`. Do not weaken the OS 27 or Evaluations diagnostics.

### Step 7: Commit Task 1

Run:

```bash
git add fixtures/dev-128
git diff --cached --check
git commit -m "test(DEV-128): add Apple API compile fixtures"
```

Expected: one commit containing exactly the nine fixture files.

## Task 2: Record normalized verification evidence

**Files:**

- Create: `docs/research/evidence/dev-128-command-transcript.md`

### Step 1: Prove the transcript is absent

Run:

```bash
test ! -e docs/research/evidence/dev-128-command-transcript.md
```

Expected: exit `0`.

### Step 2: Re-run and record host and SDK identity

Record exact commands and normalized output for:

```bash
date '+%Y-%m-%dT%H:%M:%S%z %Z'
uname -m
sw_vers
xcode-select -p
xcodebuild -version
swift --version
xcrun --sdk macosx --show-sdk-path
xcrun --sdk macosx --show-sdk-version
xcrun --sdk iphoneos --show-sdk-path
xcrun --sdk iphoneos --show-sdk-version
SDK="$(xcrun --sdk macosx --show-sdk-path)"
shasum -a 256 "$SDK/System/Library/Frameworks/FoundationModels.framework/Versions/A/Modules/FoundationModels.swiftmodule/arm64e-apple-macos.swiftinterface"
```

Also run the Task 1 positive and expected-blocker gates from the committed
fixtures and record their final outputs and exit statuses.

### Step 3: Record current host tools and narrow blockers

Run and record the expected failures without converting them into blanket SDK
failures:

```bash
xcodebuild -version
xcrun --sdk iphoneos --show-sdk-path
xcrun --find xctrace
xcrun xctrace list templates
xcrun simctl list runtimes
xcrun --find instruments
xcrun --sdk macosx27.0 --show-sdk-path
```

Expected on the 2026-07-19 host: Xcode 26.6, iPhone SDK 26.5, `xctrace`, and
`simctl` are present. The Xcode 26.6 template list has no Foundation Models
template. Legacy `instruments` remains absent with exit `72`, and SDK 27 remains
absent. The transcript must preserve the 2026-07-17 Command Line Tools failures
as historical evidence and append, rather than overwrite them with, this dated
revalidation.

### Step 4: Record Apple-owned utilities evidence

Confirm the local evidence clone is the immutable commit:

```bash
test "$(git -C /tmp/apple-foundation-models-utilities rev-parse HEAD)" = \
  376ca60e61985369d5067bd3c575bdb6a13f0e1b
```

If that exact checkout is unavailable, create a new temporary clone, check out
the immutable commit, and record the command. Run `swift build -v` against the
package with the installed SDK, record the nonzero result, and match missing OS
27/Foundation Models beta declarations. This network-dependent research probe
is evidence collection, not a default repository gate.

### Step 5: Write the transcript

Use `apply_patch` and these exact top-level sections:

1. `Scope and evidence labels`
2. `Host and SDK inventory`
3. `Installed interface identity`
4. `Positive fixture evidence`
5. `Expected blocker evidence`
6. `Apple utilities evidence`
7. `Official source ledger`
8. `Claims this evidence does not establish`

The source ledger must link current official Apple documentation, WWDC25/26
sessions, and the immutable Apple repository commit. Record retrieval dates or
the evidence collection range. Do not copy unsupported beta signatures from
the scratch report without a primary Apple link.

### Step 6: Validate and commit Task 2

Run:

```bash
set -e
transcript=docs/research/evidence/dev-128-command-transcript.md
test -s "$transcript"
for heading in \
  'Scope and evidence labels' \
  'Host and SDK inventory' \
  'Installed interface identity' \
  'Positive fixture evidence' \
  'Expected blocker evidence' \
  'Apple utilities evidence' \
  'Official source ledger' \
  'Claims this evidence does not establish'; do
  rg -q "^## ${heading}$" "$transcript"
done
rg -q 'ff2285670b0966addb9827dc895a3ee3c9db6e186baae62c034fed012632aacc' "$transcript"
rg -q '376ca60e61985369d5067bd3c575bdb6a13f0e1b' "$transcript"
rg -q 'compiled SDK 26.5|Compiled SDK 26.5' "$transcript"
rg -q 'official OS 27 beta|Official OS 27 beta' "$transcript"
rg -q 'pseudocode|deterministic mock' "$transcript"
rg -q 'Blocked' "$transcript"
rg -q '2026-07-19' "$transcript"
rg -q 'Xcode 26.6' "$transcript"
rg -q 'macro_typecheck_rc=0' "$transcript"
! rg -n 'TBD|TODO|fill in details|implement later' "$transcript"
git diff --check
git add "$transcript"
git commit -m "docs(DEV-128): record Apple API verification evidence"
```

Expected: all gates exit `0`; one transcript-only commit.

## Task 3: Publish the API matrix and orchestration comparison

**Files:**

- Create: `docs/research/dev-128-foundation-models-api-map.md`

### Step 1: Prove the report is absent

Run:

```bash
test ! -e docs/research/dev-128-foundation-models-api-map.md
```

Expected: exit `0`.

### Step 2: Write the report

Use `apply_patch` and these exact top-level sections:

1. `Scope, authority, and labels`
2. `Host and SDK baseline`
3. `API availability matrix`
4. `Stable SDK 26.5 surface`
5. `Official OS 27 beta surface`
6. `Orchestration pattern comparison`
7. `Runtime Skills boundary`
8. `Errors, cancellation, and transcript repair`
9. `Cache and performance guidance`
10. `Evaluation and profiling surfaces`
11. `Fixture coverage and blockers`
12. `Downstream requirements`

The API matrix must cover sessions, on-device model, context/token APIs,
adapter entitlement, generic model/PCC, dynamic instructions, dynamic
profiles, tools, static structured output, runtime schema, transcript,
history mutation, streaming, stable/beta errors, cancellation/transcript
policy, runtime Skills, history utilities, Evaluations, and Instruments.

The pattern table must compare baton-pass, isolated consultation, simple
routing, transcript transfer, and runtime Skills across session topology,
history visibility, trigger/control, final-answer owner, and API status.

Link the transcript relatively. Label every Swift block as `Compiled SDK 26.5`,
`Official OS 27 beta, locally unverified`, or `Pseudocode / deterministic
mock`. Keep stable and beta error taxonomies separate. Clearly state that there
is no first-class `BatonPass` or drop-in `PhoneFriendTool` framework type.

### Step 3: Run report semantic gates

Run:

```bash
set -e
report=docs/research/dev-128-foundation-models-api-map.md
test -s "$report"
headings=(
  'Scope, authority, and labels'
  'Host and SDK baseline'
  'API availability matrix'
  'Stable SDK 26.5 surface'
  'Official OS 27 beta surface'
  'Orchestration pattern comparison'
  'Runtime Skills boundary'
  'Errors, cancellation, and transcript repair'
  'Cache and performance guidance'
  'Evaluation and profiling surfaces'
  'Fixture coverage and blockers'
  'Downstream requirements'
)
for heading in "${headings[@]}"; do
  rg -q "^## ${heading}$" "$report"
done
test "$(rg '^## ' "$report" | wc -l | tr -d ' ')" -eq 12
for term in \
  'LanguageModelSession' \
  'SystemLanguageModel' \
  'DynamicGenerationSchema' \
  'DynamicProfile' \
  'TranscriptErrorHandlingPolicy' \
  'Evaluations' \
  'Instruments' \
  'baton-pass' \
  'isolated consultation' \
  'transcript transfer' \
  'runtime Skills'; do
  rg -qi "$term" "$report"
done
rg -q 'evidence/dev-128-command-transcript.md' "$report"
rg -q 'Compiled SDK 26.5' "$report"
rg -q 'Official OS 27 beta, locally unverified' "$report"
rg -q 'Pseudocode / deterministic mock' "$report"
rg -q 'no first-class.*BatonPass|No first-class.*BatonPass' "$report"
rg -q 'SystemLanguageModel.default' "$report"
rg -q 'conservative application payload/context bound' "$report"
rg -q 'structured response' "$report"
rg -q 'Treat all model output as untrusted' "$report"
rg -q 'application-owned deadline/timeout' "$report"
rg -q 'decodingFailure' "$report"
rg -q 'supported-host live proof' "$report"
rg -q 'not live runtime proof' "$report"
! rg -n 'TBD|TODO|fill in details|implement later' "$report"
git diff --check
```

Expected: every command exits `0`.

### Step 4: Commit Task 3

Run:

```bash
git add docs/research/dev-128-foundation-models-api-map.md
git commit -m "docs(DEV-128): map Apple handoff API surface"
```

Expected: one report-only commit.

## Final issue verification

After all task reviews and corrections, run from the exact final head:

```bash
set -e
git status --short --branch
git diff --check origin/main...HEAD

expected_paths="$(printf '%s\n' \
  'docs/research/dev-128-foundation-models-api-map.md' \
  'docs/research/evidence/dev-128-command-transcript.md' \
  'docs/superpowers/plans/2026-07-17-dev-128-apple-api-surface.md' \
  'docs/superpowers/specs/2026-07-17-dev-128-apple-api-surface-design.md' \
  'fixtures/dev-128/README.md' \
  'fixtures/dev-128/blocked/evaluations-import.swift' \
  'fixtures/dev-128/blocked/os-27-beta-surface.swift' \
  'fixtures/dev-128/compiled/availability-probe.swift' \
  'fixtures/dev-128/compiled/baton-pass-state.swift' \
  'fixtures/dev-128/compiled/generable-macro.swift' \
  'fixtures/dev-128/compiled/session-isolation.swift' \
  'fixtures/dev-128/compiled/stable-surface.swift' \
  'fixtures/dev-128/compiled/transcript-roundtrip.swift' | sort)"
actual_paths="$(git diff --name-only \
  origin/main...HEAD | sort)"
test "$actual_paths" = "$expected_paths"
test "$(printf '%s\n' "$actual_paths" | wc -l | tr -d ' ')" -eq 13
```

Then rerun Task 1 positive and expected-blocker gates, Task 2 transcript gates,
and Task 3 report gates. Create a clean detached worktree at `HEAD`, rerun
`git diff --check`, positive compile/run fixtures, and report/link semantics.
SDK 27, Evaluations, the Foundation Models xctrace template, legacy
`instruments`, and supported OS 27 host evidence remain explicit blockers.
Xcode 26.6, iPhone SDK 26.5, `xctrace`, `simctl`, and macro compilation are
current positive evidence and must not be reported as blockers.

## Sequential main integration handoff

After the branch is rebased onto current `origin/main`:

1. Confirm the atomic DEV-128 PR targets `main` and its diff is exactly the
   13-path allowlist above.
2. Complete exactly three main-agent review/fix rounds. Each round reviews the
   current whole PR head; any correction gets a narrow local commit and the
   round's gates are rerun before the next review.
3. After Round 3, record the exact reviewed PR-head SHA and rerun the complete
   positive fixtures, strict blocker diagnostics, transcript/report semantics,
   13-path scope, `git diff --check`, and clean-worktree gates.
4. Push only the verified correction commits, then re-read the remote PR head.
   Squash-merge into `main` only when that remote SHA exactly matches the final
   reviewed and verified SHA and all required checks are current. Any head drift
   invalidates the lock and requires review and final gates on the new head.
5. After the squash merge, add final Linear evidence with the API map,
   transcript, fixture paths, reviewed PR-head SHA, squash-merge commit,
   commands/results, remaining blockers, and all three reviewer verdicts; then
   update the issue to its completed state.
