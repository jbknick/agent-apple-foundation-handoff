# DEV-128 Apple Foundation Models API and handoff map

Evidence collection range: `2026-07-16` through `2026-07-19`

## Scope, authority, and labels

This report defines the Apple API boundary that downstream handoff architecture,
implementation, review, debugging, and validation work may rely on. It maps the
installed Foundation Models SDK 26.5 surface separately from Apple's current OS
27 beta surface and from the Apple-owned Foundation Models Utilities package.
It does not choose the repository's plugin topology or add production code.

Authority is ordered as follows:

1. The installed macOS 26.5 SDK interface, pinned by SHA-256, plus checked-in
   fixtures that type-check or run against that SDK.
2. Current official Apple documentation and WWDC material for OS 27 beta APIs
   that are absent from the installed SDK.
3. Apple-owned `apple/foundation-models-utilities` source at immutable commit
   [`376ca60e61985369d5067bd3c575bdb6a13f0e1b`](https://github.com/apple/foundation-models-utilities/tree/376ca60e61985369d5067bd3c575bdb6a13f0e1b).

The reproducible commands, outputs, source ledger, and negative diagnostics are
in the [DEV-128 command transcript](evidence/dev-128-command-transcript.md).
Third-party plugin repositories are not Apple API authority for this issue.

Evidence labels used below are:

- **Compiled SDK 26.5**: a checked-in fixture type-checks or runs against the
  installed macOS SDK. An uninvoked function proves API shape, not behavior.
- **Interface-verified SDK 26.5**: a declaration is present in the pinned local
  interface but the stated behavior was not executed.
- **Official OS 27 beta, locally unverified**: Apple publishes the declaration,
  but SDK 26.5 cannot compile it on this host.
- **Pseudocode / deterministic mock**: application orchestration logic, not a
  shipped Apple framework type or probabilistic model result.
- **Blocked**: a specific SDK, module, macro plugin, entitlement, binary, or
  compatible target is unavailable. A narrow blocker is not a blanket failure.

Primary official references are
[`LanguageModelSession`](https://developer.apple.com/documentation/foundationmodels/languagemodelsession),
[`SystemLanguageModel`](https://developer.apple.com/documentation/foundationmodels/systemlanguagemodel),
[`Tool`](https://developer.apple.com/documentation/foundationmodels/tool),
[`Transcript`](https://developer.apple.com/documentation/foundationmodels/transcript),
[dynamic sessions](https://developer.apple.com/documentation/foundationmodels/composing-dynamic-sessions-with-instructions-and-profiles),
[tool calling](https://developer.apple.com/documentation/foundationmodels/expanding-generation-with-tool-calling),
[runtime performance](https://developer.apple.com/documentation/foundationmodels/analyzing-the-runtime-performance-of-your-foundation-models-app),
and [`Evaluations`](https://developer.apple.com/documentation/evaluations).

## Host and SDK baseline

| Item | Verified baseline |
| --- | --- |
| Host | Apple Silicon `arm64`, macOS 26.5.1 build 25F80 |
| Developer directory | `/Applications/Xcode.app/Contents/Developer` |
| Xcode | Xcode 26.6, build `17F113` |
| Swift | Apple Swift 6.3.3, default target `arm64-apple-macosx26.0` |
| macOS and iPhone SDKs | Xcode SDK 26.5 for both platforms |
| Foundation Models interface | `arm64e-apple-macos.swiftinterface`, SHA-256 `ff2285670b0966addb9827dc895a3ee3c9db6e186baae62c034fed012632aacc` |
| Positive fixture target | `arm64-apple-macos26.0` with an explicit SDK path |
| Observed on-device state | `availability=available`, `isAvailable=true`, `contextSize=4096`, current locale supported; these values are mutable host state |
| Current narrow blockers | SDK 27, `Evaluations`, the Foundation Models xctrace template, legacy `instruments`, and a supported OS 27 host or device for beta evidence |

Default gates perform no live generation, model-selected tool call, network
request, PCC request, adapter load, provider request, credential lookup, or paid
service operation. They prove stable API shape and deterministic state mechanics.
The availability probe reports host state without requiring the model to be
available on every machine.

## API availability matrix

| API family | Exact surface and boundary | Status | Local evidence and default-test rule |
| --- | --- | --- | --- |
| Sessions | `LanguageModelSession`, get-only `transcript`, `isResponding`, instructions/transcript initializers, `prewarm`, `respond`, and `streamResponse` | Stable SDK 26.5 | Compiled SDK 26.5. Response calls occur only in an uninvoked type-check function. |
| On-device model | `SystemLanguageModel.default`, `Availability`, `isAvailable`, `UseCase.general`, `UseCase.contentTagging`, guardrails, locale support | Stable SDK 26.5 | Construction and availability inspection run offline; generation readiness must still be gated at runtime. |
| Context and token APIs | `contextSize`; five `tokenCount(for:)` overloads for prompt, instructions, tools, schema, and transcript entries | `contextSize` is SDK 26.0 and back-deployed before 26.4; token counting is SDK 26.4 | `contextSize` runs; all five token-count calls type-check but are not invoked. |
| Adapter entitlement | `SystemLanguageModel.Adapter`, adapter compilation/loading, and model initialization with an adapter; entitlement `com.apple.developer.foundation-model-adapter` | Stable SDK 26 interface plus entitlement requirement | Interface-verified only. Adapter/entitlement behavior is excluded from default tests. |
| Generic model and PCC | `LanguageModel`; `PrivateCloudComputeLanguageModel`; sessions accepting `some LanguageModel` | Official OS 27 beta, locally unverified | PCC needs a compatible SDK, network, managed `com.apple.developer.private-cloud-compute` entitlement, eligibility, and quota; never a default gate. |
| Dynamic instructions | `DynamicInstructions`, its `body`, builder composition, and `init(model:dynamicInstructions:history:)` | Official OS 27 beta, locally unverified | Missing from SDK 26.5. |
| Dynamic profiles | `LanguageModelSession.DynamicProfile`, `Profile`, `init(profile:history:)`, model/configuration/history/lifecycle modifiers | Official OS 27 beta, locally unverified | The negative fixture matches missing profile and initializer diagnostics independently. |
| Tools | `Tool<Arguments, Output>`, schema/name/description properties, `includesSchemaInInstructions`, and async `call(arguments:)`; OS 27 adds session properties and tool-calling mode | Stable core plus beta additions | A deterministic `GeneratedContent`-arguments tool type-checks. Model-selected invocation remains probabilistic. |
| Static structured output | `@Generable`, `@Guide`, `Generable`, `GenerationSchema`, and `GeneratedContent` | Stable SDK 26 declarations | Compiled SDK 26.5 with Xcode 26.6, including an uninvoked static structured-response overload and typed content access. |
| Runtime schema | `DynamicGenerationSchema`, `GenerationSchema(root:dependencies:)`, schema response, and schema streaming overloads | Stable SDK 26.5; explicit-null additions are 26.4 | Runtime schema construction is Compiled SDK 26.5 independently of macro synthesis; schema-based response and streaming overloads are Interface-verified SDK 26.5 only. |
| Transcript | `Transcript` as a collection and `Codable`; instruction, prompt, tool-call, tool-output, and response entries; session rehydration | Stable SDK 26.5 | Offline Codable round-trip and destination-session rehydration run successfully. Mechanics do not establish authorization to transfer content. |
| History mutation | SDK 26 session transcript is get-only; OS 27 makes transcript mutable and adds `SessionPropertyValues.history`, history transforms, and lifecycle modifiers | Official OS 27 beta for mutation | Missing locally. Mutation while responding is a beta session error. |
| Streaming | `LanguageModelSession.ResponseStream<Content>` as `AsyncSequence`, snapshot `content`/`rawContent`, and `collect()` | Stable SDK 26.5 | Type-checked only; no live stream is consumed by default. |
| Stable errors | `LanguageModelSession.GenerationError` and `LanguageModelSession.ToolCallError` | Stable SDK 26.5 interface | Interface-verified and listed separately below. |
| Beta errors | `LanguageModelError`, `LanguageModelSession.Error`, `SystemLanguageModel.Error`, PCC-specific errors, and `ToolCallError`; `GenerationError` is deprecated | Official OS 27 beta, locally unverified | Exact beta names come from current Apple documentation, not local compilation. |
| Cancellation and transcript policy | Swift task/tool cancellation; `TranscriptErrorHandlingPolicy.revertTranscript` and `.preserveTranscript` | Cancellation is Swift behavior; policy is official OS 27 beta | Default rollback is documented; preserved partial history requires application repair. |
| Runtime Skills | `Skills`, `Skill`, `SkillActivations`, and `SkillsBuilder` from Apple Foundation Models Utilities | Apple-owned `1.0.0-beta3`, OS 27 minimum | Pinned-source inspected; package build is blocked against SDK 26.5. Distinct from Claude/Codex skills. |
| History utilities | `rollingWindow(entries:)`, `rollingWindow(size:)`, `droppingCompletedToolCalls()`, and `summarizeHistory(...)` | Apple-owned `1.0.0-beta3`, OS 27 minimum | Pinned-source inspected. Rolling/drop transforms can be deterministic; summarization invokes a model and is lossy. |
| Evaluations | Datasets, generations, metrics/evaluators, aggregation, model judges, tool-call and trajectory evaluation | Official Xcode 27 beta surface | `import Evaluations` fails with the expected missing-module diagnostic under SDK 26.5. |
| Instruments | Foundation Models Instruments template with request/session/profile/tool control flow and token/cache/latency measurements | Official Xcode 27 tooling surface | Xcode 26.6 provides `xctrace` but its template list has no Foundation Models template. Full Xcode 27 plus a compatible current OS target or device remains required. Trace content can be sensitive. |

## Stable SDK 26.5 surface

The installed interface establishes a stateful session over the on-device
`SystemLanguageModel`. The session retains a get-only transcript, permits one
response at a time, accepts tools and instructions, can be rehydrated from a
`Transcript`, and supports text, static-generable, and runtime-schema response
and streaming overloads. `Response` includes `content`, `rawContent`, and the
new transcript entries; `ResponseStream` emits snapshots and supports
`collect()`.

**Compiled SDK 26.5**

```swift
let model = SystemLanguageModel.default
let session = LanguageModelSession(
    model: model,
    tools: [EchoTool()],
    instructions: "Return concise JSON."
)
session.prewarm(promptPrefix: Prompt("prefix"))

let dynamic = DynamicGenerationSchema(
    name: "HandoffEnvelope",
    properties: [
        .init(name: "summary", schema: .init(type: String.self)),
        .init(name: "destination", schema: .init(type: String.self)),
    ]
)
let schema = try GenerationSchema(root: dynamic, dependencies: [])
```

This reduced excerpt is backed by
[`fixtures/dev-128/compiled/stable-surface.swift`](../../fixtures/dev-128/compiled/stable-surface.swift),
which also type-checks all five token-count overloads, text response/streaming
APIs, transcript copying, and generation options. The response function is not
run. Schema-based response and streaming overloads are present in the pinned
interface but are not exercised by the fixture.

The separate
[`fixtures/dev-128/compiled/generable-macro.swift`](../../fixtures/dev-128/compiled/generable-macro.swift)
type-checks `@Generable`, `@Guide`, the static
`respond(... generating: HandoffEnvelope.self)` overload, and typed access to
the returned `HandoffEnvelope`. Its async function is never called by the
default gate, so this is compile evidence only and performs no live generation.

`SystemLanguageModel.Availability` is `.available` or `.unavailable(reason)`;
the installed reasons are `.deviceNotEligible`,
`.appleIntelligenceNotEnabled`, and `.modelNotReady`. Runtime code must inspect
availability rather than treating the observed local result as portable.

Static `@Generable` and `@Guide` declarations are present in the interface and
compile with the active Xcode 26.6 macro plugin. The 2026-07-17 Command Line
Tools failure remains historical evidence in the transcript, but it is no
longer a current blocker. Runtime `DynamicGenerationSchema` remains a stable
alternative when schemas are assembled dynamically, not a semantic replacement
for every macro feature.

The stable `Tool` contract uses structured arguments conforming to
`ConvertibleFromGeneratedContent` and output conforming to
`PromptRepresentable`. A deterministic tool can be tested offline; whether the
model selects it cannot be made a deterministic default assertion.

### Stable production bridge contract

The durable SDK 26.5 production bridge chain is an application contract, not a
claim that this research PR ships or runs the bridge:

1. Start with `SystemLanguageModel.default`; gate its local `availability` and
   confirm that it supports the application's intended locale before creating
   generation work.
2. Enforce a conservative application payload/context bound below
   `contextSize`, retaining headroom for instructions, schema, tools,
   transcript, and response. Where the application uses the SDK 26.4
   token-count APIs, use the applicable `tokenCount(for:)` overloads as input
   to that bound rather than treating character or byte counts as tokens.
3. Construct a real `LanguageModelSession` and request a structured response,
   such as `respond(... generating: HandoffEnvelope.self)` for a static
   `@Generable` type or the stable runtime-schema overload where appropriate.
4. Treat all model output as untrusted. Do not authorize a handoff, tool,
   destination, or side effect until application validation of the typed
   fields, policy, provenance, and bounds succeeds.
5. Propagate cooperative cancellation through the surrounding Swift task and
   impose an application-owned deadline/timeout around generation on SDK 26.5.
   Do not invent a stable timeout error: map deadline expiry into an
   application error. Keep OS 27 beta `LanguageModelError.timeout` in the beta
   taxonomy only.
6. Handle stable `LanguageModelSession.GenerationError` cases, including
   `decodingFailure`, without substituting OS 27 names. Preserve cancellation
   separately from generation failures.
7. Require supported-host live proof downstream before describing the bridge
   or runtime as proven, including an actual availability-qualified structured
   response, application validation, cancellation/deadline behavior, and the
   intended error handling.

This PR provides compile/typecheck and deterministic mock evidence only. It
runs no live generation and therefore is not live runtime proof of this bridge.

## Official OS 27 beta surface

Apple's current beta documentation generalizes sessions to `some LanguageModel`
and adds dynamic instructions and profiles. A dynamic profile resolves to one
active `Profile` for each request. Profiles bind dynamic instructions and tools
to model, temperature, sampling, reasoning, response-token, tool-calling,
transcript-policy, history-transform, and lifecycle configuration.

The declarations below include Apple's documented defaults; they are not
reduced signatures.

**Official OS 27 beta, locally unverified**

```swift
convenience init(
    profile: sending some LanguageModelSession.DynamicProfile,
    history: some Collection<Transcript.Entry> = []
)

convenience init(
    model: some LanguageModel = SystemLanguageModel.default,
    dynamicInstructions: sending some DynamicInstructions,
    history: some Collection<Transcript.Entry> = []
)
```

Sources:
[`init(profile:history:)`](https://developer.apple.com/documentation/foundationmodels/languagemodelsession/init%28profile%3Ahistory%3A%29)
and
[`init(model:dynamicInstructions:history:)`](https://developer.apple.com/documentation/foundationmodels/languagemodelsession/init%28model%3Adynamicinstructions%3Ahistory%3A%29).
Both are absent from SDK 26.5.

`GenerationOptions.ToolCallingMode` is a struct that exposes the static values
`.allowed`, `.required`, and `.disallowed`; Apple documents `.allowed` as the
default behavior. Required mode needs an exit condition, such as state that
changes the active mode or a terminating tool path, or the model can continue
calling tools. The report does not recast those static values as enum cases.

The beta session's transcript is mutable when the session is not responding.
`historyTransform` changes the history presented for a profile invocation
without mutating global session history. `SessionPropertyValues.history` is
shared mutable history, so edits are lossy and visible across profiles.

`PrivateCloudComputeLanguageModel` is a network-backed Apple route through the
generic model boundary. It is optional and must never be required for offline
fixtures: use needs the managed PCC entitlement, service eligibility, quota,
and a compatible SDK and OS.

## Orchestration pattern comparison

| Pattern | Session topology | History visibility | Trigger and control | Final-answer owner | API status |
| --- | --- | --- | --- | --- | --- |
| **baton-pass** | One `LanguageModelSession` with two or more dynamic profiles, potentially selecting different models | Shared session transcript, unless a request-local profile transform narrows what one model sees | A tool or application event changes state so a different profile becomes active | Receiving/destination profile | Official WWDC26 composition pattern built from beta primitives; no first-class `BatonPass` framework type |
| **isolated consultation** (phone-a-friend) | Parent session plus a short-lived child `LanguageModelSession`, commonly created inside a parent tool | Parent and child transcripts are isolated; only deliberately returned tool output crosses the boundary | Parent model selects the consultation tool; tool code creates and prompts the child | Parent profile/session | Official WWDC26 composition pattern; no drop-in `PhoneFriendTool` framework type |
| **simple routing** | Application chooses one route, model, profile branch, or distinct session | Depends on the chosen topology; routing alone promises no shared context | Deterministic application policy such as availability, capability, UI state, or approved provider choice | Selected route | Application policy, not inherently a handoff or delegation API |
| **transcript transfer** | A distinct destination session initialized from all or selected source entries | Only explicitly copied or filtered entries; sessions remain distinct | Application serializes/selects entries and constructs the destination transcript/session | Destination session | Stable SDK 26 transcript/rehydration mechanics; not baton-pass |
| **runtime Skills** | One session whose dynamic instructions include Apple Utilities `Skills` | Prompt skills return one-shot tool output; instruction skills change active instructions while enabled | Generated activation/toggle tool call updates `SkillActivations` | Same active profile/session | Apple Utilities beta pattern; neither agent handoff nor Claude/Codex Agent Skills |

**Pseudocode / deterministic mock**

```swift
state.apply(.transfer(source: .research, destination: .review))
precondition(state.active == .review)
precondition(state.finalResponseOwner == .review)
```

The executable pure-Swift fixture
[`fixtures/dev-128/compiled/baton-pass-state.swift`](../../fixtures/dev-128/compiled/baton-pass-state.swift)
checks this state transition. It does not compile an OS 27 profile or invoke a
model. The separate session-isolation and transcript-round-trip fixtures prove
only their stable mechanics, not complete probabilistic consultation or policy
approval.

## Runtime Skills boundary

Apple's Foundation Models runtime `Skills` are dynamic-instruction utilities in
the separately versioned Apple-owned package. They make procedural context
available to a model session through generated activation/toggle tools. They do
not define Claude Code skill discovery, Codex plugin installation, coding-session
handoff, Apple Handoff, or App Intents.

At pinned commit `376ca60e61985369d5067bd3c575bdb6a13f0e1b`:

- `Skills` conforms to `DynamicInstructions` and composes `Skill` definitions.
- Prompt-based skills return one-shot content as tool output.
- Instruction-based skills remain active in session state, can contain tools,
  and may optionally support deactivation.
- `strictSchema` restricts activation/deactivation targets to currently valid
  names.
- `SkillActivations` exposes `activeSkillNames` and `isActive(_:)` and does not
  conform to `RandomAccessCollection` in the pinned source.

The `RandomAccessCollection` removal is attributed to the pinned source and the
tagged beta3 commit message, which explicitly records that change. It is not
presented as an Apple release-note claim. The package's checked-out beta3 commit
targets OS 27 and fails against SDK 26.5 for missing beta declarations; that
result does not predict its behavior under a compatible Xcode 27 toolchain.

Pinned history helpers include rolling windows by entries or size, dropping
completed tool calls, and model-based summarization. The first two families can
be tested with deterministic history inputs. Summarization creates another
model session and replaces history with a lossy summary, so it requires separate
model-dependent evaluation and authorization boundaries.

## Errors, cancellation, and transcript repair

The stable and beta taxonomies must remain separate. Catching a fictional union
of names across both versions would hide deployment and migration mistakes.

### Stable SDK 26.5 errors

`LanguageModelSession.GenerationError` in the pinned installed interface has
these complete case signatures, including associated-value types:

| Exact installed case signature | Stable meaning boundary |
| --- | --- |
| `case exceededContextWindowSize(FoundationModels.LanguageModelSession.GenerationError.Context)` | Session input exceeded the installed model context window |
| `case assetsUnavailable(FoundationModels.LanguageModelSession.GenerationError.Context)` | Required model assets are unavailable |
| `case guardrailViolation(FoundationModels.LanguageModelSession.GenerationError.Context)` | Input or output triggered guardrails |
| `case unsupportedGuide(FoundationModels.LanguageModelSession.GenerationError.Context)` | A generation guide is unsupported |
| `case unsupportedLanguageOrLocale(FoundationModels.LanguageModelSession.GenerationError.Context)` | Requested language or locale is unsupported |
| `case decodingFailure(FoundationModels.LanguageModelSession.GenerationError.Context)` | Generated content could not be decoded as requested |
| `case rateLimited(FoundationModels.LanguageModelSession.GenerationError.Context)` | Stable session request was rate limited |
| `case concurrentRequests(FoundationModels.LanguageModelSession.GenerationError.Context)` | More than one request used the session concurrently |
| `case refusal(FoundationModels.LanguageModelSession.GenerationError.Refusal, FoundationModels.LanguageModelSession.GenerationError.Context)` | The model refused, with distinct refusal and context payloads |

The same installed interface declares these complete supporting payload and
error-property signatures:

| Installed type | Exact installed property or initializer signature |
| --- | --- |
| `LanguageModelSession.GenerationError.Context` | `public let debugDescription: Swift.String` |
| `LanguageModelSession.GenerationError.Context` | `public init(debugDescription: Swift.String)` |
| `LanguageModelSession.GenerationError.Refusal` | `public init(transcriptEntries: [FoundationModels.Transcript.Entry])` |
| `LanguageModelSession.GenerationError.Refusal` | `public var explanation: FoundationModels.LanguageModelSession.Response<Swift.String> { get async throws }` |
| `LanguageModelSession.GenerationError.Refusal` | `public var explanationStream: FoundationModels.LanguageModelSession.ResponseStream<Swift.String> { get }` |
| `LanguageModelSession.GenerationError` | `public var errorDescription: Swift.String? { get }` |
| `LanguageModelSession.GenerationError` | `public var recoverySuggestion: Swift.String? { get }` |
| `LanguageModelSession.GenerationError` | `public var failureReason: Swift.String? { get }` |

`LanguageModelSession.ToolCallError` is not an enum. Its complete installed
public data/initializer surface is:

| Installed type | Exact installed property or initializer signature |
| --- | --- |
| `LanguageModelSession.ToolCallError` | `public var tool: any FoundationModels.Tool` |
| `LanguageModelSession.ToolCallError` | `public var underlyingError: any Swift.Error` |
| `LanguageModelSession.ToolCallError` | `public init(tool: any FoundationModels.Tool, underlyingError: any Swift.Error)` |
| `LanguageModelSession.ToolCallError` | `public var errorDescription: Swift.String? { get }` |

All signatures in these three tables are **Interface-verified SDK 26.5** from
the pinned installed interface; no OS 27 name is substituted into them.

### Official OS 27 beta errors

| Exact current type | Complete current Apple DocC case signatures |
| --- | --- |
| [`LanguageModelError`](https://developer.apple.com/documentation/foundationmodels/languagemodelerror) | `case contextSizeExceeded(LanguageModelError.ContextSizeExceeded)`<br>`case rateLimited(LanguageModelError.RateLimited)`<br>`case refusal(LanguageModelError.Refusal)`<br>`case timeout(LanguageModelError.Timeout)`<br>`case guardrailViolation(LanguageModelError.GuardrailViolation)`<br>`case unsupportedCapability(LanguageModelError.UnsupportedCapability)`<br>`case unsupportedTranscriptContent(LanguageModelError.UnsupportedTranscriptContent)`<br>`case unsupportedGenerationGuide(LanguageModelError.UnsupportedGenerationGuide)`<br>`case unsupportedLanguageOrLocale(LanguageModelError.UnsupportedLanguageOrLocale)` |
| [`LanguageModelSession.Error`](https://developer.apple.com/documentation/foundationmodels/languagemodelsession/error) | `case concurrentRequests`<br>`case transcriptMutationWhileResponding` |
| [`SystemLanguageModel.Error`](https://developer.apple.com/documentation/foundationmodels/systemlanguagemodel/error) | `case assetsUnavailable(SystemLanguageModel.Error.AssetsUnavailable)` |
| [`PrivateCloudComputeLanguageModel.Error`](https://developer.apple.com/documentation/foundationmodels/privatecloudcomputelanguagemodel/error) | `case quotaLimitReached(PrivateCloudComputeLanguageModel.Error.QuotaLimitReached)`<br>`case networkFailure(PrivateCloudComputeLanguageModel.Error.NetworkFailure)`<br>`case serviceUnavailable(PrivateCloudComputeLanguageModel.Error.ServiceUnavailable)` |

Current Apple DocC publishes
[`LanguageModelSession.ToolCallError`](https://developer.apple.com/documentation/foundationmodels/languagemodelsession/toolcallerror)
as a struct with this complete public data/initializer surface:

| Current Apple DocC type | Exact current Apple DocC declaration tokens |
| --- | --- |
| `LanguageModelSession.ToolCallError` | `var tool: any Tool` |
| `LanguageModelSession.ToolCallError` | `var underlyingError: any Error` |
| `LanguageModelSession.ToolCallError` | `init(tool: any Tool, underlyingError: any Error)` |
| `LanguageModelSession.ToolCallError` | `var errorDescription: String? { get }` |

These complete case and property signatures are **Official OS 27 beta, locally
unverified**. The unqualified `Error` and `Tool` spellings in the ToolCallError
table intentionally reproduce Apple's current DocC declaration tokens; they
are not rewritten from the SDK 26.5 interface. Current Apple docs deprecate
stable `GenerationError` in favor of the split taxonomy; local SDK 26.5
compilation cannot validate that migration.

Cancellation must be treated as a state transition, not merely a thrown value.
A Swift task or tool can be cancelled, and a tool may deliberately throw
`CancellationError` to terminate a required tool loop. With the OS 27 beta
default error policy, a failed or cancelled request reverts the transcript to
its pre-request state. `.preserveTranscript` keeps partial entries; the
application then owns validation, redaction, removal of incomplete tool-call
pairs, and repair before reuse. `.revertTranscript` selects rollback explicitly.
Never mutate the transcript while `isResponding` is true.

## Cache and performance guidance

Cache statements here are guidance to measure, not guarantees established by
the fixtures. Apple's
[key-value caching guidance](https://developer.apple.com/documentation/foundationmodels/optimizing-key-value-caching-in-language-model-sessions)
supports preserving stable prefixes: appending compatible history can preserve
more of a reusable prefix, while replacing history, instructions, tools, model
configuration, or other prefix content can reduce or invalidate reuse. Actual
behavior varies by model, provider, request, and OS release.

`prewarm(promptPrefix:)` requests eager resource loading and can ask the system
to cache a prompt prefix, but the stable fixture only type-checks the call.
Request-local `historyTransform` avoids mutating the global transcript; it can
still change the prefix presented to the selected model. In Apple Utilities,
prompt-based skills are designed to inject one-shot content as tool output,
whereas instruction-based skills change instructions and may affect prefix
reuse. None of these claims is a measured cache hit on this host.

Performance acceptance must capture the exact model/provider, OS and SDK,
profile, instructions, tools, transcript shape, cold/warm state, and run count.
Do not compare time-to-first-token or cache hit rates across materially different
prefixes as if only the handoff strategy changed.

## Evaluation and profiling surfaces

The official Xcode 27 beta `Evaluations` framework covers datasets, generations,
metrics/evaluators, aggregation, model judges, and tool-call/trajectory
evaluation. It can complement deterministic contract tests, but it is not
available in SDK 26.5. Model-judge or live-model evaluations must be optional and
must state provider, availability, and non-determinism; deterministic metrics
can run only after a compatible framework exists.

Apple's Xcode 27 Foundation Models Instruments surface can show session/request
control flow, active profiles and tools, prompts/responses, token use, cache
measurements, time to first token, response duration, and related latency.
Host-level proof requires full Xcode 27 plus a compatible current OS target or
device. This machine now has Xcode 26.6 and `xctrace`, but `xctrace list
templates` has no Foundation Models template and legacy `instruments` remains
absent. A trace is explicitly Blocked rather than passed by documentation.
Trace artifacts can contain sensitive prompts and responses and must be
redacted and handled as sensitive evidence.

Repository acceptance therefore has two independent layers:

1. deterministic, offline fixtures and structural assertions that run by
   default; and
2. optional rubric, Evaluations, live-model, or Instruments evidence when the
   exact host prerequisites exist.

## Fixture coverage and blockers

| Fixture | Label | Reproducible result | Proof boundary |
| --- | --- | --- | --- |
| `compiled/stable-surface.swift` | Compiled SDK 26.5 | Type-check exit `0` | Stable API shape only; response, streaming, prewarm, and token counts are not run |
| `compiled/generable-macro.swift` | Compiled SDK 26.5 | Type-check exit `0` for macros, static structured response, and typed content access | Uninvoked function; no generation, application validation, or runtime proof |
| `compiled/availability-probe.swift` | Compiled SDK 26.5 | Emits all four expected state fields | Host state only; no generation |
| `compiled/transcript-roundtrip.swift` | Compiled SDK 26.5 | `entries=3 codableRoundTrip=true rehydrated=true` | Stable transfer mechanics, not authorization or baton-pass |
| `compiled/session-isolation.swift` | Compiled SDK 26.5 | `parentEntries=1 childEntries=1 isolated=true` | Construction isolation, not a complete consultation |
| `compiled/baton-pass-state.swift` | Pseudocode / deterministic mock | Source-to-destination transition and final owner asserted | Pure application state; no beta profile or model |
| `blocked/os-27-beta-surface.swift` | Official OS 27 beta, locally unverified / Blocked | Nonzero compile plus independent profile, initializer, and tool-mode diagnostics | SDK 26.5 absence; not a beta API refutation |
| `blocked/evaluations-import.swift` | Official OS 27 beta, locally unverified / Blocked | Nonzero compile plus `no such module 'Evaluations'` | SDK 26.5 absence only |

The Apple Utilities build is a separate network-dependent research probe of a
pinned checkout, not a default repository test. It fails because an OS 27
package is compiled against SDK 26.5 and reports the expected missing beta
declarations.

Remaining narrow blockers are SDK 27, Evaluations, the Foundation Models
xctrace template, legacy `instruments`, and a compatible current OS target or
device for beta host evidence. Xcode, the iPhone SDK, `xctrace`, and the macro
plugin are now present. The 2026-07-17 failures remain historical evidence, but
the 2026-07-19 revalidation controls current classification. A changed
toolchain must trigger reclassification and fresh proof; expected diagnostics
must not be weakened merely to keep an old blocker green.

## Downstream requirements

Downstream issues must inherit these constraints:

1. Build the default architecture and fixtures on the locally compiled SDK 26.5
   core. Keep OS 27 APIs in a clearly volatile, beta-labeled reference layer
   until a compatible SDK compiles them.
2. Treat baton-pass and isolated consultation as distinct composition patterns.
   Do not invent a first-class `BatonPass` type or copy an illustrative
   `PhoneFriendTool` as a drop-in framework declaration.
3. Do not conflate baton-pass, simple routing, transcript transfer, Apple
   Utilities runtime Skills, Claude/Codex Agent Skills, Apple Handoff, or App
   Intents. Every example must name its session topology and final-answer owner.
4. Keep stable `LanguageModelSession.GenerationError`, beta
   `LanguageModelError`, beta `LanguageModelSession.Error`, and model/provider
   errors in separately versioned guidance and tests.
5. Follow the [Stable production bridge contract](#stable-production-bridge-contract);
   supported-host live proof remains required and is not claimed here.
6. Default tests must remain deterministic and offline: no PCC, external
   provider, credentials, entitlement, paid service, network, or live generation
   requirement. Unsupported host prerequisites must produce explicit blockers.
7. Label every Swift example as `Compiled SDK 26.5`, `Official OS 27 beta,
   locally unverified`, or `Pseudocode / deterministic mock`. Unsupported API
   shapes must not be represented as compiled code.
8. Preserve transcript provenance and authorization boundaries. Rehydration
   proves mechanics only; partial-history preservation requires explicit repair,
   and transcript mutation must not occur during a response.
9. Treat cache and performance claims as hypotheses until measured under a
   pinned host/model/profile/prefix configuration. Keep sensitive prompt and
   trace content out of default evidence.
10. Use deterministic fixtures as the mandatory gate and keep Evaluations,
   rubric judging, live-model behavior, and Instruments as separately reported
   optional evidence with explicit prerequisites.
11. Re-run the fixture matrix, expected-blocker diagnostics, source audit, and
    report semantic gates whenever the SDK, Xcode, OS, or pinned Apple Utilities
    revision changes.
