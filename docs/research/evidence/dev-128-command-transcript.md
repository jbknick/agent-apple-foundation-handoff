# DEV-128 Apple Foundation Models verification transcript

Evidence collection range: `2026-07-16` through `2026-07-17`

The commands below were rerun from the DEV-128 worktree on `2026-07-17` in
Asia/Jerusalem. Output is normalized only to omit verbose compiler invocations
and repeated source excerpts; exit statuses and capability-specific diagnostics
are retained.

## Scope and evidence labels

This transcript records the installed Apple toolchain, locally compile-checked
Foundation Models fixtures, deliberately failing blocker fixtures, narrow host
tooling blockers, and a build probe of an immutable Apple-owned utilities
revision. It uses these labels:

- **Compiled SDK 26.5**: a checked-in fixture type-checked or executed against the
  installed macOS 26.5 SDK.
- **Interface-verified SDK 26.5**: a declaration or identity was inspected in
  the installed SDK interface without claiming the behavior ran.
- **Official OS 27 beta, locally unverified**: an Apple-published surface is
  outside this host's installed SDK and is not represented as locally compiled.
- **Pseudocode / deterministic mock**: a fixture demonstrates an application
  orchestration invariant, not a shipped Apple API.
- **Blocked**: a command failed for a recorded missing SDK, tool, macro plugin,
  module, or beta declaration. The blocker is kept narrower than the passing
  macOS 26.5 evidence.

Before this file was created:

```console
$ test ! -e docs/research/evidence/dev-128-command-transcript.md
# exit 0
```

No default fixture invoked model generation, PCC, an external provider, a
network request, a credential, a paid service, or an entitlement-dependent
operation. The Apple utilities build was a separate research probe of a local
clone, not a default repository gate.

## Host and SDK inventory

```console
$ date '+%Y-%m-%dT%H:%M:%S%z %Z'
2026-07-17T00:49:19+0300 IDT
# exit 0

$ uname -m
arm64
# exit 0

$ sw_vers
ProductName:            macOS
ProductVersion:         26.5.1
BuildVersion:           25F80
# exit 0

$ xcode-select -p
/Library/Developer/CommandLineTools
# exit 0

$ pkgutil --pkg-info=com.apple.pkg.CLTools_Executables
package-id: com.apple.pkg.CLTools_Executables
version: 26.5.0.0.1777544298
volume: /
location: /
install-time: 1781298398
# exit 0

$ swift --version
swift-driver version: 1.148.6 Apple Swift version 6.3.2 (swiftlang-6.3.2.1.108 clang-2100.1.1.101)
Target: arm64-apple-macosx26.0
# exit 0

$ xcrun --sdk macosx --show-sdk-path
/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk
# exit 0

$ xcrun --sdk macosx --show-sdk-version
26.5
# exit 0
```

The active developer directory is Command Line Tools, not full Xcode. That
distinction explains the narrow blockers below without invalidating the passing
macOS SDK fixture matrix.

## Installed interface identity

```console
$ shasum -a 256 /Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/System/Library/Frameworks/FoundationModels.framework/Versions/A/Modules/FoundationModels.swiftmodule/arm64e-apple-macos.swiftinterface
ff2285670b0966addb9827dc895a3ee3c9db6e186baae62c034fed012632aacc  /Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/System/Library/Frameworks/FoundationModels.framework/Versions/A/Modules/FoundationModels.swiftmodule/arm64e-apple-macos.swiftinterface
# exit 0
```

This hash pins the exact installed `arm64e-apple-macos.swiftinterface` used as
the Interface-verified SDK 26.5 authority. It is not a hash of an Xcode 27 beta
interface and does not establish any OS 27 declaration.

## Positive fixture evidence

The full positive matrix was rerun with an explicit SDK and deployment target:

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

Normalized result:

```text
stable_surface_typecheck_rc=0
availability_compile_rc=0
availability=available
isAvailable=true
contextSize=4096
supportsCurrentLocale=true
availability_run_rc=0
availability_shape_assertions_rc=0
transcript_compile_rc=0
entries=3 codableRoundTrip=true rehydrated=true
transcript_run_and_assert_rc=0
session_isolation_compile_rc=0
parentEntries=1 childEntries=1 isolated=true
session_isolation_run_and_assert_rc=0
baton_pass_mock_compile_rc=0
source=research destination=review active=review finalOwner=review transferred=true
baton_pass_mock_run_and_assert_rc=0
positive_fixture_matrix=PASS
```

All commands exited `0`. The stable fixture only type-checks response,
streaming, prewarm, token-count, tool, transcript, and runtime-schema calls;
its generation function is never invoked. Availability is mutable host state,
so the gate proves four fields are emitted rather than requiring these observed
values on every host. The transcript probes are deterministic and offline.
The baton-pass fixture is explicitly a pseudocode / deterministic mock, not an
Apple `BatonPass` type, dynamic-profile compilation, or live handoff.

## Expected blocker evidence

The negative fixtures pass only when compilation is nonzero and every planned
versioned diagnostic matches. In particular, the OS 27 fixture independently
checks the dynamic-profile declaration, the profile-based initializer, and the
tool-calling-mode argument; one matching error cannot satisfy all three gates.

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

Normalized result:

```text
macro_compile_rc=1
macro_diagnostic_match_rc=0
error: external macro implementation type 'FoundationModelsMacros.GenerableMacro' could not be found; plugin for module 'FoundationModelsMacros' not found
error: external macro implementation type 'FoundationModelsMacros.GuideMacro' could not be found; plugin for module 'FoundationModelsMacros' not found

os27_compile_rc=1
dynamic_profile_diagnostic_match_rc=0
profile_init_diagnostic_match_rc=0
tool_calling_mode_diagnostic_match_rc=0
error: 'DynamicProfile' is not a member type of class 'FoundationModels.LanguageModelSession'
error: type 'LanguageModelSession' has no member 'Profile'
error: extra arguments at positions #1, #2 in call
error: extra argument 'toolCallingMode' in call

evaluations_compile_rc=1
evaluations_diagnostic_match_rc=0
error: no such module 'Evaluations'
strict_expected_blocker_matrix=PASS
```

The macro blocker says only that this active Command Line Tools installation
lacks the implementation plugin. The OS 27 and Evaluations blockers say only
that SDK 26.5 lacks the official OS 27 beta surface. The `toolCallingMode`
diagnostic does not establish the beta static values or default. Stable SDK 26.x errors and official OS 27 beta errors remain separately versioned; these
compile failures do not define a fictional cross-version error taxonomy.

Narrow host-tool probes:

```console
$ xcodebuild -version
xcode-select: error: tool 'xcodebuild' requires Xcode, but active developer directory '/Library/Developer/CommandLineTools' is a command line tools instance
# exit 1

$ xcrun --sdk iphoneos --show-sdk-path
xcrun: error: SDK "iphoneos" cannot be located
xcrun: error: SDK "iphoneos" cannot be located
xcrun: error: unable to lookup item 'Path' in SDK 'iphoneos'
# exit 1

$ xcrun --find xctrace
xcrun: error: unable to find utility "xctrace", not a developer tool or in PATH
# exit 72

$ xcrun --find instruments
xcrun: error: unable to find utility "instruments", not a developer tool or in PATH
# exit 72
```

These results establish that the active host lacks full Xcode, an iPhone SDK,
`xctrace`, and the Instruments command. Recording a Foundation Models
Instrument trace for the official OS 27 beta surface additionally requires
full Xcode 27 and a compatible current OS target or device. It is therefore
Blocked on this host; the blocker is not evidence that the installed macOS
Foundation Models framework is unusable.

## Apple utilities evidence

The existing local evidence clone was already at the immutable revision, so no
network clone was required during this rerun:

```console
$ test "$(git -C /tmp/apple-foundation-models-utilities rev-parse HEAD)" = \
    376ca60e61985369d5067bd3c575bdb6a13f0e1b
# exit 0

$ git -C /tmp/apple-foundation-models-utilities describe --tags --exact-match HEAD
1.0.0-beta3
# exit 0

$ git -C /tmp/apple-foundation-models-utilities log -1 --format='%H%n%aI' HEAD
376ca60e61985369d5067bd3c575bdb6a13f0e1b
2026-07-10T17:10:52-04:00
# exit 0
```

The commit message begins `Updates to accompany Xcode 27 beta 3`. That is the
Apple repository's wording; this transcript does not rename the commit or
infer a broader stable release from it.

```console
$ swift build -v --package-path /tmp/apple-foundation-models-utilities
# normalized compiler identity
-target arm64-apple-macosx27.0
-sdk /Library/Developer/CommandLineTools/SDKs/MacOSX.sdk
-target-sdk-version 26.5
-target-sdk-name macosx26.5

error: cannot find type 'AnyDynamicInstructions' in scope
error: cannot find type 'DynamicInstructions' in scope
error: unknown attribute 'DynamicInstructionsBuilder'
error: type 'GeneratedContent' has no member 'ParsingError'
error: 'DynamicProfile' is not a member type of class 'FoundationModels.LanguageModelSession'
error: unknown attribute 'SessionProperty'
error: 'DynamicProfileModifier' is not a member type of class 'FoundationModels.LanguageModelSession'
error: cannot find type 'LanguageModel' in scope
# exit 1
```

The immutable Apple utilities beta3 revision is therefore Blocked against the
installed SDK 26.5 because it targets macOS 27 and consumes missing OS 27 beta
Foundation Models declarations. This is source-compatibility evidence, not a
claim that the package fails under Xcode 27.

## Official source ledger

All source retrieval and review occurred during `2026-07-16` through
`2026-07-17`. Only official Apple documentation, Apple WWDC material, and the
immutable Apple-owned repository revision are used for Apple API claims.

Apple documentation:

- [Foundation Models](https://developer.apple.com/documentation/foundationmodels/)
- [Foundation Models updates](https://developer.apple.com/documentation/updates/foundationmodels)
- [`LanguageModelSession`](https://developer.apple.com/documentation/foundationmodels/languagemodelsession)
- [`SystemLanguageModel`](https://developer.apple.com/documentation/foundationmodels/systemlanguagemodel)
- [`Tool`](https://developer.apple.com/documentation/foundationmodels/tool)
- [`Transcript`](https://developer.apple.com/documentation/foundationmodels/transcript)
- [Managing the context window](https://developer.apple.com/documentation/foundationmodels/managing-the-context-window)
- [Expanding generation with tool calling](https://developer.apple.com/documentation/foundationmodels/expanding-generation-with-tool-calling)
- [Composing dynamic sessions with instructions and profiles](https://developer.apple.com/documentation/foundationmodels/composing-dynamic-sessions-with-instructions-and-profiles)
- [Analyzing runtime performance](https://developer.apple.com/documentation/foundationmodels/analyzing-the-runtime-performance-of-your-foundation-models-app)
- [Evaluations](https://developer.apple.com/documentation/evaluations)

Apple WWDC sessions:

- [WWDC25: Meet the Foundation Models framework](https://developer.apple.com/videos/play/wwdc2025/286/)
- [WWDC25: Deep dive into the Foundation Models framework](https://developer.apple.com/videos/play/wwdc2025/301/)
- [WWDC26: What's new in the Foundation Models framework](https://developer.apple.com/videos/play/wwdc2026/241/)
- [WWDC26: Build agentic app experiences with Foundation Models](https://developer.apple.com/videos/play/wwdc2026/242/)
- [WWDC26: Debug and profile your agentic app with Foundation Models](https://developer.apple.com/videos/play/wwdc2026/243/)
- [WWDC26: Meet Evaluations](https://developer.apple.com/videos/play/wwdc2026/298/)

Apple-owned source:

- [`apple/foundation-models-utilities` at `376ca60e61985369d5067bd3c575bdb6a13f0e1b`](https://github.com/apple/foundation-models-utilities/tree/376ca60e61985369d5067bd3c575bdb6a13f0e1b)
- [Pinned package manifest](https://github.com/apple/foundation-models-utilities/blob/376ca60e61985369d5067bd3c575bdb6a13f0e1b/Package.swift)

## Claims this evidence does not establish

- It does not establish a first-class Apple `BatonPass` API or a drop-in
  phone-a-friend framework type.
- It does not establish live model generation, response quality, model-selected
  tools, probabilistic handoff behavior, performance, or cache behavior.
- It does not establish that transcript content is safe or authorized to move
  between sessions; the fixtures prove mechanics, not policy.
- It does not establish that parent/child session construction is a complete
  consultation flow, or that transcript rehydration is baton-pass.
- It does not locally verify official OS 27 beta signatures, initializer
  defaults, `ToolCallingMode` static values, mutable transcript behavior,
  dynamic profiles, Evaluations, PCC, runtime Skills, or the OS 27 error
  taxonomy.
- It does not establish iOS behavior, device behavior, adapter entitlement
  behavior, Instruments traces, or compatibility with Xcode 27.
- It does not turn missing full Xcode, SDK 27, macro plugins, iPhone SDK,
  `xctrace`, or Instruments into a blanket Foundation Models failure.
- It does not make the network-dependent Apple utilities research build a
  default test, nor does its SDK 26.5 failure predict its Xcode 27 result.
