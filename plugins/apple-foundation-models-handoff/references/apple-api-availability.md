# Apple API Availability and Version Boundary

## Scope and authority

This reference is the sole owner of exact Apple declarations, error payloads,
availability labels, provider/PCC facts, cache qualifications, and Apple-owned
Foundation Models Utilities source statements used by this package. It keeps
the installed SDK 26.5 surface separate from current OS and Xcode 27 beta
documentation. Application authorization, reducer, recovery, and rubric policy
remain in sibling references.

Installed evidence was refreshed on 2026-07-20. Installed declarations are
pinned to the local interface hash. Current beta declarations come from live official Apple
DocC and remain locally unverified because SDK 27 is absent.

## Evidence labels

| Label | Meaning |
| --- | --- |
| `compiled_sdk_26_5` | The complete block type-checks against the explicit installed SDK 26.5 and `arm64-apple-macos26.0`; no live generation is run |
| `interface_verified_sdk_26_5` | Exact declaration tokens are present in the pinned SDK 26.5 interface, without an execution claim |
| `official_os_xcode_27_beta_locally_unverified` | Current official Apple OS/Xcode 27 beta documentation publishes the declaration, but the installed SDK cannot compile it |
| `pseudocode_deterministic_mock` | Application-only deterministic contract, never a framework type |

An unlabelled Swift block is invalid. A changed SDK, interface hash, or official
beta declaration requires reclassification rather than preservation of an old
label.

## Normalized host and interface identity

```text
SDK: macOS 26.5
Xcode: 26.6 (17F113)
Swift: Apple Swift 6.3.3
Target: arm64-apple-macos26.0
Interface: <sdk>/System/Library/Frameworks/FoundationModels.framework/
           Versions/A/Modules/FoundationModels.swiftmodule/
           arm64e-apple-macos.swiftinterface
SHA-256: ff2285670b0966addb9827dc895a3ee3c9db6e186baae62c034fed012632aacc
Installed host verified: 2026-07-20
```

The durable locator is normalized. A literal host or user path is not evidence.

## Availability matrix

| Family | Exact boundary | Status and gate |
| --- | --- | --- |
| Sessions | `LanguageModelSession`, get-only transcript, `isResponding`, instructions/transcript initializers, prewarm, response, streaming | Stable SDK 26.5; response calls may type-check but are not run by default |
| On-device model | default model, availability, context size, locale support, token counting | Stable SDK 26.5; runtime availability is mutable host state |
| Static structured output | generable/guide declarations and schema | Compiled SDK 26.5 with the Xcode 26.6 macro plugin; uninvoked typecheck only |
| Runtime structured output | dynamic schema construction and schema response/stream overloads | Stable SDK 26.5; construction is compiled below |
| Tools | typed arguments/output, name/description/schema, async call | Stable core; model selection of a tool is probabilistic and not a default test |
| Transcript/rehydration | collection/Codable entries and transcript initializer | Stable SDK 26.5 mechanics; transfer authorization is application policy |
| Dynamic sessions/profiles | changing instructions, profile configuration, lifecycle modifiers, history transforms | Official OS/Xcode 27 beta, locally unverified |
| Generic model and providers | generic model protocol, executor, PCC, custom provider packages | Official OS/Xcode 27 beta; provider/network/entitlement gates are separate |
| Tool mode | required/allowed/disallowed static values | Official OS/Xcode 27 beta, locally unverified |
| Revised errors | split model/session/system/PCC taxonomy | Official OS/Xcode 27 beta; stable taxonomy remains separate |
| Runtime Skills/history helpers | Apple-owned utilities package | Pinned Apple source, OS 27 minimum, no plugin runtime dependency |
| Evaluations/Instruments | quality framework and runtime profiling | Xcode 27 beta; blocked because current full Xcode is 26.6, not Xcode 27 |

## Stable SDK 26.5 surface

The pinned interface establishes a stateful on-device session, a get-only
transcript, one response at a time, tools and instructions, transcript
rehydration, text and structured response overloads, streaming, prewarming,
availability, context size, and token counting.

Code status: `interface_verified_sdk_26_5`
```swift
final public class LanguageModelSession {
  final public var transcript: FoundationModels.Transcript {
    get
  }
  @objc deinit
}

extension FoundationModels.LanguageModelSession {
  final public var isResponding: Swift.Bool {
    get
  }
  convenience public init(
    model: FoundationModels.SystemLanguageModel = .default,
    tools: [any FoundationModels.Tool] = [],
    transcript: FoundationModels.Transcript
  )
}
```

The excerpt reproduces selected pinned declaration tokens; it makes no behavior
claim. The convenience initializer is line-wrapped without changing tokens.

Case names only for installed `SystemLanguageModel.Availability` are
`.available` and `.unavailable(reason)`. Case names only for the installed
unavailable reasons are `.deviceNotEligible`,
`.appleIntelligenceNotEnabled`, and `.modelNotReady`. Code must inspect the
current availability instead of treating a previously observed result as
portable.

## OS and Xcode 27 beta surface

Current official beta documentation introduces a generic model protocol,
server/PCC and custom-provider models, dynamic instructions and profiles,
profile modifiers, mutable/shared history, lifecycle callbacks, session
properties, transcript error policy, and a revised error taxonomy. These
symbols are absent from the installed SDK 26.5 interface.

The following current Apple initializers include documented defaults and are
not reduced signatures. Sources are
[`init(profile:history:)`](https://developer.apple.com/documentation/foundationmodels/languagemodelsession/init%28profile%3Ahistory%3A%29)
and
[`init(model:dynamicInstructions:history:)`](https://developer.apple.com/documentation/foundationmodels/languagemodelsession/init%28model%3Adynamicinstructions%3Ahistory%3A%29),
retrieved 2026-07-17.

Code status: `official_os_xcode_27_beta_locally_unverified`
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

A dynamic profile resolves to one active profile per request. Profile
configuration may select model, temperature, sampling/reasoning, response-token
limits, tool mode, transcript policy, history transform, and lifecycle
callbacks. Application state and authorization remain independent of those
framework mechanisms.

`GenerationOptions.ToolCallingMode` is a struct exposing static values
`.allowed`, `.required`, and `.disallowed`; these are static values, not enum
cases. Apple documents allowed mode as the default. Required mode needs an
application exit condition so the tool loop cannot continue without bound.

## Structured output and tools

Runtime dynamic schema construction is the stable, macro-independent compiled
example. It constructs a schema and a session but does not prompt a model,
invoke a tool, use PCC, or require credentials.

Code status: `compiled_sdk_26_5`
```swift
import FoundationModels

func makeSession() throws -> LanguageModelSession {
    let schema = DynamicGenerationSchema(
        name: "HandoffEnvelope",
        properties: [
            .init(name: "summary", schema: .init(type: String.self)),
            .init(name: "destination", schema: .init(type: String.self)),
        ]
    )
    _ = try GenerationSchema(root: schema, dependencies: [])
    return LanguageModelSession(instructions: "Return a concise result.")
}
```

The stable tool contract has typed arguments convertible from generated
content, output representable in a prompt, descriptive metadata, and an async
call. A deterministic direct tool call can be tested offline; whether a model
chooses the tool is probabilistic. Static structured-output macros `@Generable`
and `@Guide`, the static structured-response overload, and typed content access
now compile as `compiled_sdk_26_5` with Xcode 26.6 against SDK 26.5. The
repository-only DEV-128 matrix records six positive rows including that macro
fixture; typechecking is not live generation or runtime bridge proof.

## Transcripts and history

SDK 26.5 `Transcript` is a collection and Codable history of instructions,
prompts, tool calls, tool outputs, and responses. A new session can be
initialized from a transcript. That proves copying and rehydration mechanics,
not consent, provenance, minimum necessary disclosure, complete tool pairs, or
authority transfer.

In current OS/Xcode 27 beta documentation the session transcript can be
mutated while the session is not responding, shared history can be accessed
through session properties, and a profile may apply a request-local history
transform. `TranscriptErrorHandlingPolicy` offers rollback or preservation of
partial history. Preserved partial entries require application validation and
repair before reuse. Mutation while responding is a session error.

## Stable SDK 26.5 errors

The following are exact installed interface signatures. SDK 26.5
`LanguageModelSession.GenerationError` remains distinct from all beta error
types. In short: SDK 26.5 `LanguageModelSession.GenerationError` is the stable
owner on this host.

| Exact installed case signature | Boundary |
| --- | --- |
| `case exceededContextWindowSize(FoundationModels.LanguageModelSession.GenerationError.Context)` | Context window exceeded |
| `case assetsUnavailable(FoundationModels.LanguageModelSession.GenerationError.Context)` | Required assets unavailable |
| `case guardrailViolation(FoundationModels.LanguageModelSession.GenerationError.Context)` | Guardrail triggered |
| `case unsupportedGuide(FoundationModels.LanguageModelSession.GenerationError.Context)` | Guide unsupported |
| `case unsupportedLanguageOrLocale(FoundationModels.LanguageModelSession.GenerationError.Context)` | Language/locale unsupported |
| `case decodingFailure(FoundationModels.LanguageModelSession.GenerationError.Context)` | Requested decoding failed |
| `case rateLimited(FoundationModels.LanguageModelSession.GenerationError.Context)` | Stable session rate limited |
| `case concurrentRequests(FoundationModels.LanguageModelSession.GenerationError.Context)` | Concurrent requests rejected |
| `case refusal(FoundationModels.LanguageModelSession.GenerationError.Refusal, FoundationModels.LanguageModelSession.GenerationError.Context)` | Refusal plus context payloads |

Complete supporting payload/property/initializer signatures:

| Installed type | Exact signature |
| --- | --- |
| `LanguageModelSession.GenerationError.Context` | `public let debugDescription: Swift.String` |
| `LanguageModelSession.GenerationError.Context` | `public init(debugDescription: Swift.String)` |
| `LanguageModelSession.GenerationError.Refusal` | `public init(transcriptEntries: [FoundationModels.Transcript.Entry])` |
| `LanguageModelSession.GenerationError.Refusal` | `public var explanation: FoundationModels.LanguageModelSession.Response<Swift.String> { get async throws }` |
| `LanguageModelSession.GenerationError.Refusal` | `public var explanationStream: FoundationModels.LanguageModelSession.ResponseStream<Swift.String> { get }` |
| `LanguageModelSession.GenerationError` | `public var errorDescription: Swift.String? { get }` |
| `LanguageModelSession.GenerationError` | `public var recoverySuggestion: Swift.String? { get }` |
| `LanguageModelSession.GenerationError` | `public var failureReason: Swift.String? { get }` |
| `LanguageModelSession.ToolCallError` | `public var tool: any FoundationModels.Tool` |
| `LanguageModelSession.ToolCallError` | `public var underlyingError: any Swift.Error` |
| `LanguageModelSession.ToolCallError` | `public init(tool: any FoundationModels.Tool, underlyingError: any Swift.Error)` |
| `LanguageModelSession.ToolCallError` | `public var errorDescription: Swift.String? { get }` |

## OS and Xcode 27 beta errors

These tables reproduce complete current Apple DocC case signatures and public
payload data/initializers retrieved 2026-07-17. They are
`official_os_xcode_27_beta_locally_unverified`; similar stable names do not imply source
compatibility.

| Current type | Complete case signatures |
| --- | --- |
| `LanguageModelError` | `case contextSizeExceeded(LanguageModelError.ContextSizeExceeded)`<br>`case rateLimited(LanguageModelError.RateLimited)`<br>`case refusal(LanguageModelError.Refusal)`<br>`case timeout(LanguageModelError.Timeout)`<br>`case guardrailViolation(LanguageModelError.GuardrailViolation)`<br>`case unsupportedCapability(LanguageModelError.UnsupportedCapability)`<br>`case unsupportedTranscriptContent(LanguageModelError.UnsupportedTranscriptContent)`<br>`case unsupportedGenerationGuide(LanguageModelError.UnsupportedGenerationGuide)`<br>`case unsupportedLanguageOrLocale(LanguageModelError.UnsupportedLanguageOrLocale)` |
| `LanguageModelSession.Error` | `case concurrentRequests`<br>`case transcriptMutationWhileResponding` |
| `SystemLanguageModel.Error` | `case assetsUnavailable(SystemLanguageModel.Error.AssetsUnavailable)` |
| `PrivateCloudComputeLanguageModel.Error` | `case quotaLimitReached(PrivateCloudComputeLanguageModel.Error.QuotaLimitReached)`<br>`case networkFailure(PrivateCloudComputeLanguageModel.Error.NetworkFailure)`<br>`case serviceUnavailable(PrivateCloudComputeLanguageModel.Error.ServiceUnavailable)` |

Complete `LanguageModelError` payload surfaces:

| Payload | Exact initializer and public properties |
| --- | --- |
| `ContextSizeExceeded` | `init(contextSize: Int, tokenCount: Int, debugDescription: String, metadata: [String : any Sendable] = [:])`<br>`var contextSize: Int`<br>`var tokenCount: Int`<br>`var debugDescription: String`<br>`var metadata: [String : any Sendable]` |
| `RateLimited` | `init(resetDate: Date?, debugDescription: String, metadata: [String : any Sendable] = [:])`<br>`var resetDate: Date?`<br>`var debugDescription: String`<br>`var metadata: [String : any Sendable]` |
| `Refusal` | `init(explanation: String, debugDescription: String, metadata: [String : any Sendable] = [:])`<br>`nonisolated(nonsending) var explanation: LanguageModelSession.Response<String> { get async throws }`<br>`var explanationStream: LanguageModelSession.ResponseStream<String> { get }`<br>`var debugDescription: String`<br>`var metadata: [String : any Sendable]` |
| `Timeout` | `init(debugDescription: String, metadata: [String : any Sendable] = [:])`<br>`var debugDescription: String`<br>`var metadata: [String : any Sendable]` |
| `GuardrailViolation` | `init(debugDescription: String, metadata: [String : any Sendable] = [:])`<br>`var debugDescription: String`<br>`var metadata: [String : any Sendable]` |
| `UnsupportedCapability` | `init(capability: LanguageModelCapabilities.Capability, debugDescription: String, metadata: [String : any Sendable] = [:])`<br>`var capability: LanguageModelCapabilities.Capability`<br>`var debugDescription: String`<br>`var metadata: [String : any Sendable]` |
| `UnsupportedTranscriptContent` | `init(unsupportedContent: [Transcript.Entry], debugDescription: String, metadata: [String : any Sendable] = [:])`<br>`var unsupportedContent: [Transcript.Entry]`<br>`var debugDescription: String`<br>`var metadata: [String : any Sendable]` |
| `UnsupportedGenerationGuide` | `init(schemaName: String?, debugDescription: String, metadata: [String : any Sendable] = [:])`<br>`var schemaName: String?`<br>`var debugDescription: String`<br>`var metadata: [String : any Sendable]` |
| `UnsupportedLanguageOrLocale` | `init(languageCode: Locale.LanguageCode, debugDescription: String, metadata: [String : any Sendable] = [:])`<br>`var languageCode: Locale.LanguageCode`<br>`var debugDescription: String`<br>`var metadata: [String : any Sendable]` |

Complete model/provider payload surfaces:

| Payload | Exact initializer and public properties |
| --- | --- |
| `SystemLanguageModel.Error.AssetsUnavailable` | `init(debugDescription: String)`<br>`var debugDescription: String` |
| `PrivateCloudComputeLanguageModel.Error.QuotaLimitReached` | `init(limitIncreaseSuggestion: PrivateCloudComputeLanguageModel.QuotaUsage.LimitIncreaseSuggestion? = nil, resetDate: Date? = nil, debugDescription: String)`<br>`var limitIncreaseSuggestion: PrivateCloudComputeLanguageModel.QuotaUsage.LimitIncreaseSuggestion?`<br>`var resetDate: Date?`<br>`var debugDescription: String` |
| `PrivateCloudComputeLanguageModel.Error.NetworkFailure` | `init(debugDescription: String)`<br>`var debugDescription: String` |
| `PrivateCloudComputeLanguageModel.Error.ServiceUnavailable` | `init(debugDescription: String)`<br>`var debugDescription: String` |

Current DocC publishes `LanguageModelSession.ToolCallError` as a struct with
this complete data/initializer surface:

| Current type | Exact current declaration tokens |
| --- | --- |
| `LanguageModelSession.ToolCallError` | `init(tool: any Tool, underlyingError: any Error)` |
| `LanguageModelSession.ToolCallError` | `var tool: any Tool` |
| `LanguageModelSession.ToolCallError` | `var underlyingError: any Error` |
| `LanguageModelSession.ToolCallError` | `var errorDescription: String? { get }` |

## Provider and PCC boundary

Current beta `PrivateCloudComputeLanguageModel` is an Apple network-backed
model route. It requires a compatible SDK/OS, a managed PCC entitlement,
service eligibility, quota, network, and graceful fallback. PCC's published
stateless-computation, no-privileged-access, non-targetability, and verifiable-
transparency properties apply to PCC, not to an arbitrary custom provider.

A custom `LanguageModel` provider owns its authentication, transport, model
execution, logging, retention, server tools, configuration identity, and error
mapping. Provider selection must be visible to the person and separately
authorized. Default reference tests make no PCC or custom-provider request.

## Runtime Skills boundary

Apple's separately versioned Foundation Models Utilities package contains
runtime `Skills`, `Skill`, `SkillActivations`, and `SkillsBuilder` constructs
for procedural context within a model session. They are unrelated to coding-
agent skill discovery and do not perform baton-pass.

At immutable Apple-owned commit
`376ca60e61985369d5067bd3c575bdb6a13f0e1b`, `Skills` composes dynamic
instructions. `SkillActivations` conforms to `Observable`, exposes
`activeSkillNames` and `isActive(_:)`, and no longer conforms to
`RandomAccessCollection`. The conformance statement comes from the pinned
source file; the collection-removal statement also appears in that exact
commit's tagged beta3 message. This package is optional reference material and
not a runtime dependency of the plugin.

Pinned history helpers include rolling windows by entries or size, dropping
completed tool calls, and model-based summarization. Rolling/drop operations
can be tested deterministically. Summarization invokes a model and is lossy, so
it needs separate authorization and evaluation.

## Cache and performance qualifications

Appending compatible history can preserve more of a stable prefix, while
changing model/provider, configuration, instructions, tools, schema, or
history can reduce or invalidate reuse. Request-local transforms and dynamic
instruction changes may alter the effective prefix.

Provider behavior varies. Cache hit rate, cached tokens, time to first token,
and latency must be measured under a pinned model/provider/prefix/configuration,
OS/SDK, tool set, transcript shape, cold/warm state, and run count. No document
or compile test establishes a cache hit.

## Compile and blocker matrix

| Row | Current result | Required action |
| --- | --- | --- |
| SDK 26.5 runtime schema block | Compiled offline | Keep explicit SDK/target and rerun after toolchain change |
| Installed interface | Hash matches pinned value | Reclassify on any hash or SDK drift |
| Static macros | Compiled offline with Xcode 26.6 macro plugin against SDK 26.5 | Keep `compiled_sdk_26_5`; rerun after toolchain change |
| OS/Xcode 27 dynamic surfaces | Blocked: missing declarations in SDK 26.5 | Compile only with compatible SDK 27 |
| PCC/provider | Blocked by SDK plus network/entitlement/service prerequisites | Keep out of default gates |
| Evaluations | Blocked: module absent | Requires full compatible Xcode 27 |
| Instruments/trace capture | Blocked: full Xcode, compatible target, and tooling absent | Record a narrow blocker, never a documentation-only pass |

## Related references

- [Architecture and state](architecture-and-state.md)
- [Orchestration patterns](orchestration-patterns.md)
- [Security, context, and recovery](security-context-and-recovery.md)
- [Evaluation and observability](evaluation-and-observability.md)

## Source ledger

All web sources were retrieved on 2026-07-17.

| Claim family | Official source |
| --- | --- |
| Framework/session/model overview | [Foundation Models](https://developer.apple.com/documentation/foundationmodels), [LanguageModelSession](https://developer.apple.com/documentation/foundationmodels/languagemodelsession), [SystemLanguageModel](https://developer.apple.com/documentation/foundationmodels/systemlanguagemodel) |
| June 2026 beta changes | [Foundation Models updates](https://developer.apple.com/documentation/updates/foundationmodels) |
| Dynamic profiles/history/lifecycle | [Composing dynamic sessions](https://developer.apple.com/documentation/foundationmodels/composing-dynamic-sessions-with-instructions-and-profiles), [WWDC26 session 242](https://developer.apple.com/videos/play/wwdc2026/242/) |
| Stable tool declaration | [Tool](https://developer.apple.com/documentation/foundationmodels/tool), [Tool calling](https://developer.apple.com/documentation/foundationmodels/expanding-generation-with-tool-calling) |
| Transcript/context | [Transcript](https://developer.apple.com/documentation/foundationmodels/transcript), [Managing the context window](https://developer.apple.com/documentation/foundationmodels/managing-the-context-window) |
| Beta model errors | [LanguageModelError](https://developer.apple.com/documentation/foundationmodels/languagemodelerror), [session error](https://developer.apple.com/documentation/foundationmodels/languagemodelsession/error), [system-model error](https://developer.apple.com/documentation/foundationmodels/systemlanguagemodel/error), [PCC error](https://developer.apple.com/documentation/foundationmodels/privatecloudcomputelanguagemodel/error), [tool-call error](https://developer.apple.com/documentation/foundationmodels/languagemodelsession/toolcallerror) |
| PCC and provider | [WWDC26 PCC session 319](https://developer.apple.com/videos/play/wwdc2026/319/), [WWDC26 provider session 339](https://developer.apple.com/videos/play/wwdc2026/339/), [PCC Security Guide](https://security.apple.com/documentation/private-cloud-compute/) |
| Cache/performance | [Key-value caching](https://developer.apple.com/documentation/foundationmodels/optimizing-key-value-caching-in-language-model-sessions), [runtime performance](https://developer.apple.com/documentation/foundationmodels/analyzing-the-runtime-performance-of-your-foundation-models-app) |
| Runtime utilities | [Pinned Apple source](https://github.com/apple/foundation-models-utilities/tree/376ca60e61985369d5067bd3c575bdb6a13f0e1b), [pinned activation source](https://github.com/apple/foundation-models-utilities/blob/376ca60e61985369d5067bd3c575bdb6a13f0e1b/Sources/FoundationModelsUtilities/Skills/SkillActivations.swift) |
| Evaluations | [Evaluations](https://developer.apple.com/documentation/evaluations) |

## Limitations

This reference does not prove beta compilation, live generation, tool
selection, model availability, PCC eligibility, custom-provider behavior,
cache reuse, Evaluations, or Instruments. Official beta declarations may
change. Recheck live DocC and the installed interface whenever the OS, SDK,
Xcode, or pinned utilities revision changes. The historical Command Line Tools
macro-plugin blocker is not a current blocker under Xcode 26.6.
