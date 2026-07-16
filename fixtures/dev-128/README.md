# DEV-128 Apple API verification fixtures

These fixtures separate locally verified Foundation Models APIs from expected
toolchain blockers. Here, **compiled** means compile-checked against the
recorded macOS 26.5 SDK. It does not mean that live model generation ran or
that probabilistic model behavior was validated.

## Fixture inventory

| Fixture | Evidence label | What it proves | What it does not prove |
| --- | --- | --- | --- |
| `compiled/stable-surface.swift` | Compiled SDK 26.5 | The installed SDK type-checks stable model/session construction, availability and context access, all five token-count overloads, deterministic `Tool` conformance, generation options, prewarming, text response and streaming APIs, transcript copy/rehydration, and runtime dynamic schema. | The unexecuted response, streaming, prewarm, and token-count calls do not establish model availability, generated output quality, runtime latency, cache behavior, or a handoff architecture. |
| `compiled/availability-probe.swift` | Compiled SDK 26.5 | The host can inspect `availability`, `isAvailable`, `contextSize`, and current-locale support without generation. | A result of `available` does not validate a generated response, future host state, or other hardware/locales. |
| `compiled/transcript-roundtrip.swift` | Compiled SDK 26.5 | A three-entry `Transcript` survives an offline Codable round-trip and can initialize a distinct destination session. | Rehydration is not baton-pass, delegation, model generation, or proof that copied content is safe to transfer. |
| `compiled/session-isolation.swift` | Compiled SDK 26.5 | Parent and child sessions can be constructed offline with separate transcripts. | Construction alone is not a complete phone-a-friend tool call and does not validate model-selected consultation. |
| `compiled/baton-pass-state.swift` | Pseudocode / deterministic mock | A pure Swift reducer begins on the source profile, applies one explicit transfer, activates the destination, and gives it final-response ownership. | This is not a shipped Apple `BatonPass` API, an OS 27 `DynamicProfile`, a model-generated handoff, or shared-transcript behavior. |
| `blocked/generable-macro.swift` | Blocked | Compilation fails with a missing `FoundationModelsMacros` implementation diagnostic under the active Command Line Tools. | The failure does not mean that `@Generable` or `@Guide` is absent from compatible full-Xcode toolchains. |
| `blocked/os-27-beta-surface.swift` | Official OS 27 beta, locally unverified / Blocked | Compilation fails because the installed SDK lacks dynamic-profile, profile-session, and tool-calling-mode declarations. | The failure does not disprove the official OS 27 beta APIs; it proves only that this SDK cannot compile them. |
| `blocked/evaluations-import.swift` | Official OS 27 beta, locally unverified / Blocked | Compilation fails because the installed SDK has no `Evaluations` module. | The failure does not evaluate prompts, tools, trajectories, or model quality and does not describe Xcode 27 behavior. |

## Positive gates

Run from the repository root:

```bash
set -e
SDK="$(xcrun --sdk macosx --show-sdk-path)"
TARGET=arm64-apple-macos26.0

swiftc -typecheck -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/stable-surface.swift

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

## Expected-blocker gates

An expected blocker passes only when compilation fails and the output contains
the capability-specific diagnostic. A generic nonzero exit is not sufficient.

```bash
set -e
SDK="$(xcrun --sdk macosx --show-sdk-path)"

set +e
swiftc -typecheck -target arm64-apple-macos26.0 -sdk "$SDK" \
  fixtures/dev-128/blocked/generable-macro.swift \
  >/tmp/dev-128-generable.out 2>&1
macro_rc=$?
set -e
test "$macro_rc" -ne 0
rg -q 'FoundationModelsMacros|macro implementation.*could not be found' \
  /tmp/dev-128-generable.out

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

## Default-test constraints

The positive gates perform no live generation, tool selection, network call,
PCC request, provider request, credential lookup, paid-service call, adapter
load, or entitlement-dependent operation. They require only the recorded host's
Swift compiler and macOS SDK. The availability probe records state and does not
fail merely because model assets are unavailable.

The blocked gates deliberately require no missing toolchain to be installed;
they preserve narrow evidence for the missing macro plugin, SDK 27 symbols, and
Evaluations module. A compatible toolchain changing one of these results must
trigger reclassification rather than weakening the expected diagnostic.
