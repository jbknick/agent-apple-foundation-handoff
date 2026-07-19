# DEV-130 Handoff Threat Model Evidence Transcript

Primary-source and original structural evidence date: `2026-07-17`

Host and diagnostic-route evidence refresh: `2026-07-19` (Asia/Jerusalem)

## Scope and non-claims

This transcript records the installed SDK/interface checks, current official
Apple primary-source review, the original fixture RED diagnostic class, the
initial diagnostic-route RED, the locality review-correction RED, the final
deterministic GREEN and repeated-run comparison, the complete DEV-128 matrix,
report semantic/source gates, current structural host passes, and narrow host
blockers for DEV-130.

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
xcodebuild -version
xcode-select -p
swift --version
printf 'macos_sdk=%s\n' "$(xcrun --sdk macosx --show-sdk-version)"
printf 'iphoneos_sdk=%s\n' "$(xcrun --sdk iphoneos --show-sdk-version)"
xcrun xctrace version
xcrun --find xctrace
xcrun simctl list devices available | rg 'Booted' \
  | sed -E 's/ \([0-9A-F-]+\) \(Booted\)/ (Booted)/'

SDK="$(xcrun --sdk macosx --show-sdk-path)"
INTERFACE="$SDK/System/Library/Frameworks/FoundationModels.framework/Versions/A/Modules/FoundationModels.swiftmodule/arm64e-apple-macos.swiftinterface"
shasum -a 256 "$INTERFACE"
sed -n '316,329p' "$INTERFACE" | rg 'transcript| get| set'
sed -n '400,458p' "$INTERFACE" | rg 'GenerationError|ToolCallError'
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
2026-07-19T16:54:33+0300 IDT
arm64
ProductName: macOS
ProductVersion: 26.5.1
BuildVersion: 25F80
Xcode 26.6
Build version 17F113
/Applications/Xcode.app/Contents/Developer
swift-driver version: 1.148.6 Apple Swift version 6.3.3 (swiftlang-6.3.3.1.3 clang-2100.1.1.101)
Target: arm64-apple-macosx26.0
macos_sdk=26.5
iphoneos_sdk=26.5
xctrace version 16.0 (17F113)
/Applications/Xcode.app/Contents/Developer/usr/bin/xctrace
iPhone 17 Pro (Booted)
iPad Air 13-inch (M4) (Booted)
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
not an executed error scenario. The original `2026-07-17` collection used the
Command Line Tools developer directory and Swift 6.3.2. The `2026-07-19`
refresh supersedes those host facts; the Foundation Models interface hash and
SDK 26.5 stable/beta declaration boundary remain unchanged. Xcode, iPhoneOS,
`xctrace`, and simulator availability do not prove live Foundation Models,
production bridge, trace capture, or device behavior.

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

### Original transition-policy RED record

The original implementation changed the runner before adding the transition
policy. Its reviewed RED command was:

```bash
set +e
artifact_dir="$(mktemp -d)"
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

That historical state was not recreated after the policy file existed. This is
a reviewed historical RED record, distinct from the fresh route-specific RED
below.

### July 19 diagnostic-route RED record

The diagnostic-result assertions were added before their policy types. Fresh
command:

```bash
set +e
artifact_dir="$(mktemp -d)"
swiftc -warnings-as-errors -parse-as-library \
  fixtures/dev-130/HandoffSecurityPolicy.swift \
  fixtures/dev-130/AdversarialScenarios.swift \
  -o "$artifact_dir/dev130-red" > "$artifact_dir/red.out" 2>&1
red_rc=$?
set -e
test "$red_rc" -ne 0
rg -q "cannot find type 'DiagnosticRoutingDecision' in scope|cannot find 'DiagnosticToolResult' in scope" \
  "$artifact_dir/red.out"
```

Relevant output; compile exited `1`, and the diagnostic-class assertion exited
`0`:

```text
red_rc=1
error: cannot find type 'DiagnosticRoutingDecision' in scope
error: cannot find 'DiagnosticToolResult' in scope
```

No production hook, bridge, model, or tool execution was involved. The RED
proved only that the new pure policy contract did not yet exist.

### Locality review-correction RED

Review found that the first request filter checked only an approved field name.
The runner was changed first to give an approved-name `message` field a typed
non-local origin. Fresh command:

```bash
set +e
artifact_dir="$(mktemp -d)"
swiftc -warnings-as-errors -parse-as-library \
  fixtures/dev-130/HandoffSecurityPolicy.swift \
  fixtures/dev-130/AdversarialScenarios.swift \
  -o "$artifact_dir/dev130-red" > "$artifact_dir/red.out" 2>&1
red_rc=$?
set -e
test "$red_rc" -ne 0
rg -q "extra argument 'origin' in call|cannot infer contextual base in reference to member 'trustedLocal'" \
  "$artifact_dir/red.out"
```

Relevant output; compile exited `1`, and the diagnostic-class assertion exited
`0`:

```text
red_rc=1
error: extra argument 'origin' in call
error: cannot infer contextual base in reference to member 'trustedLocal'
```

GREEN added only `DiagnosticFieldOrigin` and required both `.trustedLocal` and
the approved name when filtering the request. The approved-name non-local
mutation and the unapproved-name local mutation are both absent from the bridge
request and metadata-only evidence.

### Fresh GREEN and repeatability

Command:

```bash
set -euo pipefail
artifact_dir="$(mktemp -d)"
swiftc -warnings-as-errors -parse-as-library \
  fixtures/dev-130/HandoffSecurityPolicy.swift \
  fixtures/dev-130/AdversarialScenarios.swift \
  -o "$artifact_dir/dev130-adversarial"
"$artifact_dir/dev130-adversarial" \
  | tee "$artifact_dir/dev130-adversarial.out"
diff -u fixtures/dev-130/expected-output.txt \
  "$artifact_dir/dev130-adversarial.out"
"$artifact_dir/dev130-adversarial" \
  > "$artifact_dir/dev130-adversarial-second.out"
cmp "$artifact_dir/dev130-adversarial.out" \
  "$artifact_dir/dev130-adversarial-second.out"
```

Output; compile, run, golden diff, and repeated-run comparison all exited `0`:

```text
PASS indirect-injection unauthorizedCommands=0
PASS sensitive-provider-transfer blocked=true sentinelLeaked=false
PASS diagnostic-result-routing action=condense_diagnostic_output fields=3 executions=1 rerun=false
PASS tool-failure-precommit phase=stable active=research
PASS tool-failure-uncertain phase=recoveryRequired effects=1 commands=1
PASS transition-budget count=3 fourthCommand=false terminal=transitionBudgetExceeded
PASS cancellation-precommit phase=stable pending=false
PASS cancellation-uncertain phase=recoveryRequired effects=1 commands=1
SUMMARY passed=8 failed=0
```

The diff and byte comparison produced no output. The assertions additionally
cover independent `stateVersion`/`policyVersion`, stale source state,
destination, purpose, class, field, proposal-policy and grant-policy mismatches,
proposal phase gating before budget, uncertain replay, late-event immunity,
approved diagnostic-name plus trusted-local-origin filtering,
response schema and result-type mismatches; independent `callID`, `toolName`,
`toolVersion`, `stateVersion`, `action`, and `originalResultType` binding
mismatches; accepted-response and cancellation replay; original result
preservation; normalized interruption errors; and no original-tool rerun.

## Adversarial E2E execution

Executed deterministic proof covers:

- injection text producing zero unauthorized commands;
- C3 transfer blocked without provider serialization or audit leakage;
- diagnostic `PostToolUse` routing with exact action, approved local fields,
  strict response schema/provenance, once-executed original-result fallback,
  normalized failure/timeout/cancellation errors, and no rerun;
- pre-commit tool failure restoring checkpoint state;
- uncertain post-dispatch failure retaining one ledger effect and one command;
- three allowed transitions and deterministic fourth-proposal termination;
- pre-commit and uncertain cancellation; and
- assertion-only stale/mismatched proposal, in-flight replay, and late-event
  cases.

The report’s remaining cases are explicitly marked deterministic downstream
requirements: a complete external duplicate-retry/idempotency executor,
general executor spoofed-result acceptance beyond the diagnostic resolver,
confirmation replay, summary poisoning, unsafe
fallback, deterministic transcript repair, auth expiry, opaque provider-tool
disclosure, full trace leakage scanning, and table-driven error/fallback
mapping. The fixture provides partial ledger-replay and audit-leakage proof; it
does not promote those remaining rows to executed status.

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
expected_paths="$(printf '%s\n' \
  'docs/research/dev-130-handoff-threat-model.md' \
  'docs/research/evidence/dev-130-command-transcript.md' \
  'docs/superpowers/plans/2026-07-17-dev-130-handoff-threat-model.md' \
  'docs/superpowers/specs/2026-07-17-dev-130-handoff-threat-model-design.md' \
  'fixtures/dev-130/AdversarialScenarios.swift' \
  'fixtures/dev-130/HandoffSecurityPolicy.swift' \
  'fixtures/dev-130/expected-output.txt' | sort)"
test "$(git diff --name-only origin/main...HEAD | sort)" = "$expected_paths"
placeholder_pattern="$(printf '%s%s|%s%s|%s%s|fill in %s|implement %s' \
  T BD TO DO FIX ME details later)"
! rg -n "$placeholder_pattern" "$report" "$transcript"
forbidden_pattern="$(printf 'DEV130_%s_%s|DEV130_%s_%s_%s|DEV130_%s_%s_%s' \
  SECRET SENTINEL DIAGNOSTIC RAW SENTINEL DIAGNOSTIC REMOTE SENTINEL)"
! rg -n "$forbidden_pattern" "$report" "$transcript"
git diff --check
```

Result after both documents were written:

```text
report_sections=16
transcript_sections=7
official_apple_links=19
issue_paths=7
placeholders=0
forbidden_sentinel_occurrences=0
semantic_source_gate=PASS
```

Current DEV-128 positive matrix:

```bash
set -euo pipefail
artifact_dir="$(mktemp -d)"
SDK="$(xcrun --sdk macosx --show-sdk-path)"
TARGET=arm64-apple-macos26.0
swiftc -typecheck -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/stable-surface.swift
swiftc -typecheck -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/generable-macro.swift
swiftc -parse-as-library -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/availability-probe.swift \
  -o "$artifact_dir/availability"
"$artifact_dir/availability" | tee "$artifact_dir/availability.out"
rg -q '^availability=' "$artifact_dir/availability.out"
rg -q '^isAvailable=' "$artifact_dir/availability.out"
rg -q '^contextSize=[0-9]+$' "$artifact_dir/availability.out"
rg -q '^supportsCurrentLocale=' "$artifact_dir/availability.out"
swiftc -parse-as-library -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/transcript-roundtrip.swift \
  -o "$artifact_dir/transcript"
test "$("$artifact_dir/transcript")" = \
  'entries=3 codableRoundTrip=true rehydrated=true'
swiftc -parse-as-library -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/session-isolation.swift \
  -o "$artifact_dir/isolation"
test "$("$artifact_dir/isolation")" = \
  'parentEntries=1 childEntries=1 isolated=true'
swiftc -parse-as-library -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/baton-pass-state.swift \
  -o "$artifact_dir/baton"
test "$("$artifact_dir/baton")" = \
  'source=research destination=review active=review finalOwner=review transferred=true'
```

Relevant output; every compile/run exited `0`:

```text
stable-surface=PASS
generable-macro=PASS
availability=available
isAvailable=true
contextSize=4096
supportsCurrentLocale=true
entries=3 codableRoundTrip=true rehydrated=true
parentEntries=1 childEntries=1 isolated=true
source=research destination=review active=review finalOwner=review transferred=true
dev128-positive=PASS
```

Availability values are mutable host state. The gate requires the documented
shape, not these exact values on every machine. The stable-surface and
generable-macro fixtures only type-check; no generation helper ran. Transcript
rehydration proves mechanics, not transfer authorization, and
`baton-pass-state.swift` is a framework-neutral deterministic mock.

Repository evidence-safety checks also require no tracked `.trace` or
`.xcresult`, no forbidden fixture sentinel in either report, clean whitespace,
and exactly the seven DEV-130 branch paths at final issue verification.

## Host-assisted blockers

Current host-tool classification command:

```bash
set -euo pipefail
xcodebuild -version
printf 'iphoneos_sdk=%s\n' "$(xcrun --sdk iphoneos --show-sdk-version)"
xcrun xctrace version
xcrun --find xctrace >/dev/null
printf 'simctl_booted=%s\n' \
  "$(xcrun simctl list devices available | rg -c 'Booted')"
set +e
xcrun --find Instruments > /dev/null 2>&1
instruments_rc=$?
set -e
test "$instruments_rc" -eq 72
printf 'legacy_instruments_rc=%s\n' "$instruments_rc"
```

Relevant results:

```text
Xcode 26.6
Build version 17F113
iphoneos_sdk=26.5
xctrace version 16.0 (17F113)
simctl_booted=2
legacy_instruments_rc=72
```

Exact Xcode 27 beta/Evaluations blocker command:

```bash
set -euo pipefail
artifact_dir="$(getconf DARWIN_USER_TEMP_DIR)"
SDK="$(xcrun --sdk macosx --show-sdk-path)"
set +e
swiftc -typecheck -target arm64-apple-macos27.0 -sdk "$SDK" \
  fixtures/dev-128/blocked/os-27-beta-surface.swift \
  >"$artifact_dir/dev130-beta.out" 2>&1
beta_rc=$?
swiftc -typecheck -target arm64-apple-macos27.0 -sdk "$SDK" \
  fixtures/dev-128/blocked/evaluations-import.swift \
  >"$artifact_dir/dev130-evaluations.out" 2>&1
evaluations_rc=$?
set -e
test "$beta_rc" -ne 0
rg -q "DynamicProfile.*not a member type|has no member 'Profile'" \
  "$artifact_dir/dev130-beta.out"
rg -q "extra arguments at positions #1, #2 in call" \
  "$artifact_dir/dev130-beta.out"
rg -q "extra argument 'toolCallingMode' in call" \
  "$artifact_dir/dev130-beta.out"
test "$evaluations_rc" -ne 0
rg -q "no such module 'Evaluations'" \
  "$artifact_dir/dev130-evaluations.out"
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

The active host therefore cannot compile the official Xcode 27 beta surface or
import `Evaluations`; the legacy `Instruments` executable is also absent.
Xcode 26.6, the iPhoneOS 26.5 SDK, `xctrace`, and `simctl` are now available and
are no longer reported as blockers. WWDC26 session 243's improved Foundation
Models instrument still requires Xcode 27 and a compatible target, so no live
trace proof is claimed. These exact blockers do not invalidate the passing SDK
26.5 or deterministic evidence, and they do not claim the beta APIs fail on a
compatible host.
