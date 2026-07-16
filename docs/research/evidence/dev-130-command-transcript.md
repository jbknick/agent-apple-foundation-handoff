# DEV-130 Handoff Threat Model Evidence Transcript

Evidence date: `2026-07-17` (Asia/Jerusalem)

## Scope and non-claims

This transcript records the installed SDK/interface checks, current official
Apple primary-source review, the reviewed Task 1 RED diagnostic class, a fresh
deterministic GREEN run, repeated-run comparison, DEV-128 regressions, report
semantic/source gates, and narrow host blockers for DEV-130.

Evidence labels match the threat model:

- **Installed SDK 26.5 interface**: declaration inspection only.
- **Compiled SDK 26.5**: a repository fixture type-checked or ran locally.
- **Official Xcode 27 beta guidance, locally unverified**: current Apple beta
  material reviewed, but unavailable in the installed interface.
- **Executed deterministic proof**: the framework-neutral fixture ran offline
  with exact expected output.
- **Blocked**: a missing host tool, SDK, module, or beta declaration produced an
  expected nonzero result. A blocker is not a security pass.

No command in the default proof invoked live model generation, PCC, a custom
provider, a network model request, credentials, entitlements, a paid service,
or an external effect. No raw prompt, response, reasoning, tool argument/result,
user data, or temporary absolute artifact path is recorded here. Commands use
`$artifact_dir` for ephemeral compiler output.

Source reachability checks establish that a URL was reachable during the
retrieval window; they do not prove API behavior. Official source content was
reviewed independently, and installed API claims were checked against the
pinned local interface.

## Environment and installed SDK evidence

Command:

```bash
set -euo pipefail
date '+%Y-%m-%dT%H:%M:%S%z %Z'
uname -m
sw_vers
xcode-select -p
pkgutil --pkg-info=com.apple.pkg.CLTools_Executables
swift --version
xcrun --sdk macosx --show-sdk-path
xcrun --sdk macosx --show-sdk-version

SDK="$(xcrun --sdk macosx --show-sdk-path)"
INTERFACE="$SDK/System/Library/Frameworks/FoundationModels.framework/Versions/A/Modules/FoundationModels.swiftmodule/arm64e-apple-macos.swiftinterface"
shasum -a 256 "$INTERFACE"
sed -n '316,329p' "$INTERFACE"
sed -n '400,458p' "$INTERFACE"
if rg -q 'public var transcript:.*\{ get set \}' "$INTERFACE"; then
  echo transcript_mutability=get-set
else
  echo transcript_mutability=get-only
fi
if rg -q 'onToolCall|historyTransform|TranscriptErrorHandlingPolicy|DynamicProfile' "$INTERFACE"; then
  echo beta_dynamic_surface=present
else
  echo beta_dynamic_surface=absent
fi
```

Relevant output; exit `0`:

```text
2026-07-17T02:31:16+0300 IDT
arm64
ProductName: macOS
ProductVersion: 26.5.1
BuildVersion: 25F80
/Library/Developer/CommandLineTools
version: 26.5.0.0.1777544298
swift-driver version: 1.148.6 Apple Swift version 6.3.2 (swiftlang-6.3.2.1.108 clang-2100.1.1.101)
Target: arm64-apple-macosx26.0
SDK version: 26.5
ff2285670b0966addb9827dc895a3ee3c9db6e186baae62c034fed012632aacc
final public var transcript: FoundationModels.Transcript {
  get
}
public enum GenerationError : Swift.Error, Foundation.LocalizedError
public struct ToolCallError : Swift.Error, Foundation.LocalizedError
transcript_mutability=get-only
beta_dynamic_surface=absent
```

The installed `GenerationError` cases inspected were context-window exceeded,
assets unavailable, guardrail violation, unsupported guide,
unsupported language/locale, decoding failure, rate limiting, concurrent
requests, and refusal. The installed `ToolCallError` exposes the tool,
underlying error, initializer, and error description. This is interface shape,
not an executed error scenario.

## Official primary-source checks

The threat-model source ledger contains only direct `developer.apple.com` and
`security.apple.com` links. It includes WWDC26 sessions 242, 243, 319, 339, 347,
and 8009; Foundation Models Tool, tool calling, session, tool error, transcript,
and runtime-performance documentation; OS logging/privacy documentation; and
PCC guide, core-requirement, stateless-computation, attack-analysis, and
restricted-observability pages.

Exact reachability command:

```bash
set -euo pipefail
report=docs/research/dev-130-handoff-threat-model.md
count=0
while IFS= read -r url; do
  test -n "$url"
  code=$(curl --silent --show-error --location --output /dev/null \
    --write-out '%{http_code}' "$url")
  test "$code" = 200
  count=$((count + 1))
done < <(rg -o 'https://(developer|security)\.apple\.com/[^ )]+' "$report" | sort -u)
printf 'official_links_checked=%s failures=0\n' "$count"
```

Output; exit `0`:

```text
official_links_checked=19 failures=0
```

High-risk claims were cross-checked as follows:

- Apple’s Tool and tool-calling documentation says tools may perform side
  effects, the model decides when/how often to call, and output returns to the
  model. This does not establish authorization.
- WWDC26 session 347 defines indirect prompt injection, recommends deterministic
  mitigations as a baseline, and describes `.onToolCall` before executor
  execution plus per-inference `.historyTransform`. Those callback declarations
  are official Xcode 27 beta guidance and absent from the installed interface.
- WWDC26 session 242 distinguishes shared-history/final-owner baton-pass from an
  independent-child-transcript consultation, and describes beta transcript
  revert/preserve behavior and mutable transcript. The installed transcript is
  get-only.
- WWDC26 sessions 319, 339, and 8009 plus the PCC Security Guide distinguish
  PCC guarantees from custom-provider data policy and show that a provider may
  keep server-side tool work opaque to the local transcript.
- WWDC26 session 243 and Apple runtime/logging documentation state that traces
  can contain sensitive prompt/response data and must be handled accordingly.

These checks support the labelled fact ledger. They do not turn Apple examples
into plugin policy or prove a callback, model, provider, trace, or error path ran.

## Fixture RED-GREEN cycle

### Reviewed Task 1 RED record

Task 1 changed the runner before adding the policy implementation. The reviewed
RED command was:

```bash
set +e
artifact_dir="$(getconf DARWIN_USER_TEMP_DIR)"
swiftc -parse-as-library fixtures/dev-130/AdversarialScenarios.swift \
  -o "${artifact_dir}dev130-red" \
  >"${artifact_dir}dev130-red.out" 2>&1
red_rc=$?
set -e
test "$red_rc" -ne 0
rg -q "cannot find.*HandoffState|cannot find.*HandoffSecurityPolicy" \
  "${artifact_dir}dev130-red.out"
```

Recorded diagnostic class:

```text
red_rc=1
error: cannot find type 'HandoffState' in scope
```

Task 2 did not recreate that historical state after the policy file existed.
The RED evidence is the reviewed Task 1 record, not a fresh Task 2 execution.

### Fresh GREEN and repeatability

Command:

```bash
set -euo pipefail
artifact_dir="$(getconf DARWIN_USER_TEMP_DIR)"
swiftc -parse-as-library \
  fixtures/dev-130/HandoffSecurityPolicy.swift \
  fixtures/dev-130/AdversarialScenarios.swift \
  -o "${artifact_dir}dev130-adversarial"
"${artifact_dir}dev130-adversarial" \
  | tee "${artifact_dir}dev130-adversarial.out"
diff -u fixtures/dev-130/expected-output.txt \
  "${artifact_dir}dev130-adversarial.out"
"${artifact_dir}dev130-adversarial" \
  > "${artifact_dir}dev130-adversarial-second.out"
cmp "${artifact_dir}dev130-adversarial.out" \
  "${artifact_dir}dev130-adversarial-second.out"
```

Output; compile, run, golden diff, and repeated-run comparison all exited `0`:

```text
PASS indirect-injection unauthorizedCommands=0
PASS sensitive-provider-transfer blocked=true sentinelLeaked=false
PASS tool-failure-precommit phase=stable active=research
PASS tool-failure-uncertain phase=recoveryRequired effects=1 commands=1
PASS transition-budget count=3 fourthCommand=false terminal=transitionBudgetExceeded
PASS cancellation-precommit phase=stable pending=false
PASS cancellation-uncertain phase=recoveryRequired effects=1 commands=1
SUMMARY passed=7 failed=0
```

The diff and byte comparison produced no output. The assertions additionally
cover independent `stateVersion`/`policyVersion`, stale source state, destination,
purpose, class, field, proposal-policy and grant-policy mismatches, proposal
phase gating before budget, uncertain replay, and late-event immunity.

## Adversarial E2E execution

Executed deterministic proof covers:

- injection text producing zero unauthorized commands;
- C3 transfer blocked without provider serialization or audit leakage;
- pre-commit tool failure restoring checkpoint state;
- uncertain post-dispatch failure retaining one ledger effect and one command;
- three allowed transitions and deterministic fourth-proposal termination;
- pre-commit and uncertain cancellation; and
- assertion-only stale/mismatched proposal, in-flight replay, and late-event
  cases.

The report’s remaining cases are explicitly marked deterministic downstream
requirements: a complete external duplicate-retry/idempotency executor,
spoofed-result acceptance, confirmation replay, summary poisoning, unsafe
fallback, deterministic transcript repair, auth expiry, opaque provider-tool
disclosure, full trace leakage scanning, and table-driven error/fallback
mapping. Task 1 provides partial ledger-replay and audit-leakage proof only.

The fixture validates mandatory application policy. It does not execute Apple
Foundation Models callbacks, dynamic profiles, transcript error policy, a model,
PCC, a custom provider, a real tool, an external effect, Instruments, or
Evaluations. It does not prove exactly-once external delivery.

## Semantic and evidence-safety gates

Report/transcript command:

```bash
set -euo pipefail
report=docs/research/dev-130-handoff-threat-model.md
transcript=docs/research/evidence/dev-130-command-transcript.md
test -s "$report"
test -s "$transcript"
test "$(rg '^## ' "$report" | wc -l | tr -d ' ')" -eq 16
test "$(rg '^## ' "$transcript" | wc -l | tr -d ' ')" -eq 7
for term in assets actors 'trust boundaries' 'C0 Public' 'C3 Never-transfer' \
  'indirect prompt injection' 'data exfiltration' over-sharing spoofing \
  'authorization confusion' 'duplicate effects' 'transition loops' \
  'partial failure' cancellation 'single-active' 'sensitive logs' \
  'unavailable-model fallback' 'baton-pass' 'isolated consultation' \
  'at-most-once' 'recoveryRequired' 'residual risk' 'metadata-only'; do
  rg -qi "$term" "$report"
done
for issue in DEV-132 DEV-134 DEV-136 DEV-137 DEV-138 DEV-139 DEV-141; do
  rg -q "$issue" "$report"
done
test "$(rg -o 'https://(developer|security)\.apple\.com/[^ )]+' "$report" \
  | sort -u | wc -l | tr -d ' ')" -ge 14
placeholder_pattern="$(printf '%s%s|%s%s|%s%s|fill in %s|implement %s' \
  T BD TO DO FIX ME details later)"
! rg -n "$placeholder_pattern" "$report" "$transcript"
forbidden_pattern="$(printf 'DEV130_%s_%s' SECRET SENTINEL)"
! rg -n "$forbidden_pattern" "$report" "$transcript"
git diff --check
```

Result after both documents were written:

```text
report_sections=16
transcript_sections=7
official_apple_links=19
placeholders=0
forbidden_sentinel_occurrences=0
semantic_source_gate=PASS
```

Existing DEV-128 regression command:

```bash
set -euo pipefail
artifact_dir="$(getconf DARWIN_USER_TEMP_DIR)"
SDK=$(xcrun --sdk macosx --show-sdk-path)
TARGET=arm64-apple-macos26.0
swiftc -typecheck -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/stable-surface.swift
for fixture in availability-probe transcript-roundtrip session-isolation baton-pass-state; do
  swiftc -parse-as-library -target "$TARGET" -sdk "$SDK" \
    "fixtures/dev-128/compiled/$fixture.swift" \
    -o "${artifact_dir}dev130-$fixture"
  "${artifact_dir}dev130-$fixture"
done
```

Relevant output; every compile/run exited `0`:

```text
stable-surface=PASS
availability=available
isAvailable=true
contextSize=4096
supportsCurrentLocale=true
entries=3 codableRoundTrip=true rehydrated=true
parentEntries=1 childEntries=1 isolated=true
source=research destination=review active=review finalOwner=review transferred=true
dev128-regression=PASS
```

Availability values are mutable host state. The gate requires the documented
shape, not these exact values on every machine. `stable-surface.swift` only
type-checks; its generation helper was not invoked. Transcript rehydration proves
mechanics, not transfer authorization, and `baton-pass-state.swift` is a
framework-neutral deterministic mock.

Repository evidence-safety checks also require no tracked `.trace` or
`.xcresult`, no forbidden fixture sentinel in either report, clean whitespace,
and exactly the seven DEV-130 branch paths at final issue verification.

## Host-assisted blockers

Narrow host-tool command:

```bash
set -u
artifact_dir="$(getconf DARWIN_USER_TEMP_DIR)"
set +e
xcodebuild -version >"${artifact_dir}dev130-xcodebuild.out" 2>&1
xcodebuild_rc=$?
xcrun --sdk iphoneos --show-sdk-path \
  >"${artifact_dir}dev130-iphoneos.out" 2>&1
iphoneos_rc=$?
xcrun --find xctrace >"${artifact_dir}dev130-xctrace.out" 2>&1
xctrace_rc=$?
xcrun --find instruments >"${artifact_dir}dev130-instruments.out" 2>&1
instruments_rc=$?
set -e
```

Relevant results:

```text
xcodebuild_rc=1
xcode-select: error: tool 'xcodebuild' requires Xcode, but the active developer directory is a command line tools instance
iphoneos_rc=1
xcrun: error: SDK "iphoneos" cannot be located
xctrace_rc=72
xcrun: error: unable to find utility "xctrace"
instruments_rc=72
xcrun: error: unable to find utility "instruments"
```

Exact Xcode 27 beta/Evaluations blocker command:

```bash
set -euo pipefail
artifact_dir="$(getconf DARWIN_USER_TEMP_DIR)"
SDK="$(xcrun --sdk macosx --show-sdk-path)"
set +e
swiftc -typecheck -target arm64-apple-macos27.0 -sdk "$SDK" \
  fixtures/dev-128/blocked/os-27-beta-surface.swift \
  >"${artifact_dir}dev130-beta.out" 2>&1
beta_rc=$?
swiftc -typecheck -target arm64-apple-macos27.0 -sdk "$SDK" \
  fixtures/dev-128/blocked/evaluations-import.swift \
  >"${artifact_dir}dev130-evaluations.out" 2>&1
evaluations_rc=$?
set -e
test "$beta_rc" -ne 0
rg -q "DynamicProfile.*not a member type|has no member 'Profile'" \
  "${artifact_dir}dev130-beta.out"
rg -q "extra arguments at positions #1, #2 in call" \
  "${artifact_dir}dev130-beta.out"
rg -q "extra argument 'toolCallingMode' in call" \
  "${artifact_dir}dev130-beta.out"
test "$evaluations_rc" -ne 0
rg -q "no such module 'Evaluations'" \
  "${artifact_dir}dev130-evaluations.out"
```

Relevant results; the blocker assertions exited `0`:

```text
beta_rc=1
error: 'DynamicProfile' is not a member type of class 'FoundationModels.LanguageModelSession'
error: type 'LanguageModelSession' has no member 'Profile'
error: extra arguments at positions #1, #2 in call
error: extra argument 'toolCallingMode' in call
evaluations_rc=1
error: no such module 'Evaluations'
blocker_probe_assertions=PASS
```

The active host therefore cannot compile the official Xcode 27 beta surface,
import Evaluations, record or inspect a Foundation Models Instruments trace, or
run an iPhone target. WWDC26 session 243 additionally requires Xcode 27 and a
compatible current OS target/device for the improved instrument. Evaluations
execution likewise requires full Xcode/SDK 27 and the module. These are exact
optional-host blockers; they do not invalidate the passing SDK 26.5 or
deterministic evidence, and they are not claims that the beta APIs fail on a
compatible host.
