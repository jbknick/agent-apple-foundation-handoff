# DEV-130 Handoff Security, Privacy, and Failure Threat Model

Evidence retrieval date: `2026-07-17`

## Scope, authority, and evidence labels

This report defines the binding security invariants and downstream contracts for
Foundation Models handoff architectures in DEV-130. It covers baton-pass,
isolated consultation, provider changes, transcripts, tools, traces, fallback,
and recovery. It does not implement a production runtime, provider, skill, or
security system.

The following labels are intentionally non-interchangeable:

- **Installed SDK 26.5 interface** means a declaration was found in the pinned
  local `FoundationModels.swiftinterface`. Interface inspection establishes API
  shape, not runtime behavior.
- **Compiled SDK 26.5** means a repository fixture type-checked or ran against
  the installed macOS 26.5 SDK.
- **Official Apple fact** means a claim is directly supported by current Apple
  documentation, an Apple WWDC session, or the Apple Private Cloud Compute
  Security Guide retrieved on `2026-07-17`.
- **Official Xcode 27 beta guidance, locally unverified** means Apple documents
  the surface for its current beta, but the installed SDK 26.5 does not expose
  it. This label applies to dynamic profiles, `.onToolCall`,
  `.historyTransform`, tool-calling mode, mutable session transcript, and
  transcript error-handling policy.
- **Mandatory plugin/application policy** means DEV-130 chooses an enforceable
  host-side rule. It is not an Apple framework guarantee.
- **Recommended control** is defense in depth and is not a release gate unless a
  downstream issue adopts it.
- **Executed deterministic proof** means the checked-in framework-neutral Swift
  fixture ran offline with exact output. **Deterministic downstream
  requirement** means the scenario is specified here but was not executed by
  Task 1.

Prompts, retrieved content, tool output, model responses, summaries, repository
text, generated code, and provider metadata remain untrusted data. Only a typed
event created at a trusted application boundary may reach the authoritative
reducer. Nothing in this report treats model text as authorization,
confirmation, tool-result provenance, policy state, or proof of an external
effect.

## Host and SDK baseline

The verified host baseline is:

| Item | Observed value | Evidence boundary |
| --- | --- | --- |
| Host | arm64, macOS 26.5.1 (25F80) | Local command output |
| Developer directory | `/Library/Developer/CommandLineTools` | Command Line Tools, not full Xcode |
| Swift | Apple Swift 6.3.2 | Local compiler identity |
| macOS SDK | 26.5 | Local `xcrun` result |
| Installed interface SHA-256 | `ff2285670b0966addb9827dc895a3ee3c9db6e186baae62c034fed012632aacc` | Pins the installed Apple interface |
| `LanguageModelSession.transcript` | get-only | Installed SDK 26.5 interface |
| Stable session errors | `LanguageModelSession.GenerationError` and `LanguageModelSession.ToolCallError` | Installed SDK 26.5 interface |
| Dynamic profiles, `.onToolCall`, `.historyTransform`, mutable transcript, transcript error policy | absent | Installed SDK 26.5 interface; present only in official Xcode 27 beta guidance reviewed below |
| Full Xcode, iPhone SDK, `xctrace`, Instruments, Evaluations | unavailable on this host | Explicit blockers, not security passes |

The installed interface contains the stable transcript, tool, session, and error
shapes needed by the DEV-128 regression fixtures. It does not validate Apple’s
Xcode 27 beta callbacks or mutable-history behavior. The production design must
therefore keep its deterministic policy independent of those beta APIs and use
them only as version-labelled integration points after compatible-host proof.

## Official Apple fact ledger

All links below are direct Apple primary sources retrieved on `2026-07-17`.
Apple facts stop at the statements in this ledger; the policy conclusions that
follow are DEV-130 application policy.

| Label | Official Apple fact | Primary source |
| --- | --- | --- |
| Current official documentation | A `Tool` can gather runtime information or perform side effects. Tool definitions enter model context, the model decides when and how often to call, and tool output returns to the model. | [`Tool`](https://developer.apple.com/documentation/foundationmodels/tool), [tool calling](https://developer.apple.com/documentation/foundationmodels/expanding-generation-with-tool-calling) |
| Current official documentation | A thrown tool failure surfaces through `LanguageModelSession.ToolCallError`, including the tool and underlying error. The installed interface independently exposes that structure. | [`ToolCallError`](https://developer.apple.com/documentation/foundationmodels/languagemodelsession/toolcallerror), [`LanguageModelSession`](https://developer.apple.com/documentation/foundationmodels/languagemodelsession) |
| Current official documentation | A transcript is a linear history that can contain instructions, prompts, reasoning, tool calls, tool outputs, and responses; a new session can be rehydrated from selected entries. Rehydration is mechanics, not authorization to transfer. | [`Transcript`](https://developer.apple.com/documentation/foundationmodels/transcript) |
| Official Apple security guidance | Indirect prompt injection is malicious instruction embedded in extra context, including initial context and tool results. Apple identifies data exfiltration and unintended actions as risks, calls prompt injection an active research area, and recommends deterministic mitigations as the auditable baseline. | [WWDC26 session 347](https://developer.apple.com/videos/play/wwdc2026/347/) |
| Official Xcode 27 beta guidance, locally unverified | `.onToolCall` runs after a model proposes a tool call and before the executor; throwing blocks execution. `.historyTransform` runs before inference for the initial request and loop iterations. These declarations are absent from the installed SDK 26.5 interface. | [WWDC26 session 347](https://developer.apple.com/videos/play/wwdc2026/347/) |
| Official Xcode 27 beta guidance, locally unverified | Baton-pass shares the session transcript and gives final-response ownership to the receiving profile. Phone-a-friend creates a short-lived child with an independent transcript and returns control and final-response ownership to the parent. Required tool mode behaves as a loop that needs an exit condition. | [WWDC26 session 242](https://developer.apple.com/videos/play/wwdc2026/242/) |
| Official Xcode 27 beta guidance, locally unverified | A thrown tool error or cancelled response defaults to transcript reversion. Preserve mode makes the application responsible for repair; session transcript mutation is allowed only when the session is not responding, and history rewrites can confuse the model. | [WWDC26 session 242](https://developer.apple.com/videos/play/wwdc2026/242/) |
| Official Xcode 27 beta guidance, locally unverified | The Foundation Models Instrument captures prompts and responses that can be sensitive; logging is enabled for the trace duration, so trace files require safe handling. | [WWDC26 session 243](https://developer.apple.com/videos/play/wwdc2026/243/), [runtime performance documentation](https://developer.apple.com/documentation/foundationmodels/analyzing-the-runtime-performance-of-your-foundation-models-app) |
| Official Xcode 27 beta guidance, locally unverified | The PCC model needs network access, has availability and quota behavior, and can include reasoning text in the session transcript. Apple recommends availability checks and graceful, persistent, actionable fallback UI. | [WWDC26 session 319](https://developer.apple.com/videos/play/wwdc2026/319/) |
| Official Xcode 27 beta guidance, locally unverified | A custom `LanguageModel` provider can expose server-side tools at different visibility levels: only final text, metadata, or typed custom segments. Absence of a local tool-call entry therefore cannot prove that no server-side tool ran. | [WWDC26 session 339](https://developer.apple.com/videos/play/wwdc2026/339/) |
| Official Apple privacy guidance | PCC’s no-retention, no-access, and verifiability guarantees apply only to Apple’s PCC path. A third-party provider’s own data handling governs data sent through the protocol and must be disclosed. | [WWDC26 session 8009](https://developer.apple.com/videos/play/wwdc2026/8009/) |
| PCC fact | PCC’s core requirements are stateless computation on personal user data, enforceable guarantees, no privileged runtime access, non-targetability, and verifiable transparency. | [PCC Security Guide](https://security.apple.com/documentation/private-cloud-compute/), [core requirements](https://security.apple.com/documentation/private-cloud-compute/corerequirements) |
| PCC fact | PCC is designed to use request data only to fulfill the request, encrypt it to validated nodes, and not retain decrypted user data after the response. These are PCC properties, not generic cloud-provider properties. | [Stateless computation and enforceable guarantees](https://security.apple.com/documentation/private-cloud-compute/statelessandenforcable) |
| PCC fact | PCC calls outside its trust boundary necessarily carry query-derived data. PCC limits routing metadata and records outbound calls in its request execution log and Apple Intelligence Report. Those controls cannot be attributed to arbitrary provider tools. | [PCC attack analysis](https://security.apple.com/documentation/private-cloud-compute/attacks) |
| PCC fact | PCC excludes general-purpose logging and permits only pre-specified, structured, audited logs and metrics to leave a node. This is a design principle for this plugin, not a guarantee the plugin inherits. | [Restricted observability](https://security.apple.com/documentation/private-cloud-compute/noprivilegedaccess) |
| Apple logging fact | Apple logging supports privacy redaction; Apple recommends limiting logs to static values where possible and explicitly protecting sensitive dynamic values. | [Generating log messages](https://developer.apple.com/documentation/os/generating-log-messages-from-your-code), [`OSLogPrivacy`](https://developer.apple.com/documentation/os/oslogprivacy) |

Structured generation constrains shape; none of these sources says a
well-formed model proposal is authorized or semantically safe. On-device
execution also does not neutralize untrusted context, tool authority,
over-sharing, or trace disclosure.

## Assets and actors

### Assets

- User intent, current authentication state, confirmations, boundary grants,
  provider disclosures, and revocations.
- Full transcripts, selected entries, summaries, reasoning, attachments, tool
  arguments/results, and session properties.
- Credentials, signing material, identity data, personal data, health and
  financial data, contacts, messages, calendar, photos, precise location, and
  confidential source code.
- Active profile/provider, transition graph, transition budget, stable
  checkpoint, independent `stateVersion` and `policyVersion`, pending
  transition, and terminal/recovery phase.
- Tool allowlists, effect ledger, idempotency keys, external-resource state,
  outstanding call IDs, and tool-result provenance.
- Logs, traces, screenshots, fixtures, CI artifacts, generated guidance, and
  review evidence.

### Actors

- The person initiating the task, approving a transfer, or confirming an
  effect.
- The host application and its trusted deterministic policy/reducer boundary.
- Apple’s on-device model, Apple’s PCC model, and each named custom provider.
- Local tools, PCC tools, opaque provider-side tools, and external services.
- Authors of untrusted pages, documents, feeds, events, tool results,
  repository content, and summaries.
- Developers, reviewers, CI operators, support staff, and anyone able to read a
  durable artifact.
- Faults, retries, races, cancellation, stale state, auth expiry, and partial
  failures as non-human adversaries.

## Trust boundaries

1. **Person/UI to orchestrator:** natural-language intent is input, not an
   authorization token. Confirmation is a typed, scoped application event.
2. **Developer control plane to model context:** static/dynamic instructions
   and authoritative policy state stay separate from prompts, retrieved data,
   model text, summaries, and tool output.
3. **Model proposal to transition/tool executor:** every proposal crosses state,
   policy, graph, provenance, semantic argument, recipient/resource,
   confirmation, authentication, and budget checks.
4. **Profile to profile in baton-pass:** the selected history and tool set may
   change, the active profile/provider changes, and final-response ownership
   moves to the destination. Apple’s example can share full history; DEV-130
   policy still filters it to target-necessary fields.
5. **Parent to isolated consultation:** the child receives only a classified,
   minimized consultation envelope, has an independent transcript and tool
   authority, and returns a typed result. The parent retains final-response
   ownership.
6. **Device to PCC:** an off-device boundary with PCC-specific statelessness,
   transparency, availability, quota, and possible outbound-tool properties.
7. **Device or PCC to custom provider:** a separate provider, credential,
   retention, training, location, and server-tool boundary. PCC properties must
   never be inherited or implied.
8. **Executor to external effect:** current permissions, authentication,
   recipient, resource version, idempotency, and commit outcome are rechecked
   outside model control.
9. **Live session to transcript/history/summary:** provenance and balanced
   call/output structure can be lost through preservation, mutation, or
   compaction. A model summary is not authority.
10. **Runtime to logs/traces/repository/CI:** durable artifacts have broader
    readership and retention than ephemeral inference.
11. **Generated guidance to execution:** generated Swift, shell, or configuration
    is untrusted until version-labelled, reviewed, compiled, tested, and
    explicitly executed.

## Data classification and transfer policy

Every context field has exactly one class plus provenance attributes: `source`,
`subject`, `purpose`, `allowed destination`, `retention`, and `redaction status`.
Unknown or unclassified fields fail closed at a model, provider, profile, tool,
trace, or repository boundary.

| Class | Definition | Transfer rule |
| --- | --- | --- |
| **C0 Public** | Intentionally public, non-secret content | May cross only for the named task, destination, and retention policy; public does not mean universally relevant. |
| **C1 Task-private** | Non-sensitive private content required for the approved task | Minimize to named fields; requires a current destination/purpose grant for a provider or profile boundary. |
| **C2 Sensitive** | Personal, regulated, high-impact, or confidential content | Normally blocked for isolated consultation and custom providers. An exception requires named fields, destination, purpose, retention, minimization, current policy version, and bound confirmation. |
| **C3 Never-transfer** | Credentials, tokens, keys, signing material, recovery codes, unrelated third-party private data, out-of-purpose content, and anything unsafe to classify | Never crosses a model/provider/profile/tool-output/log/trace/repository boundary. A grant cannot override this class. |

Transfer policy is atomic: a disallowed field blocks the whole envelope rather
than being silently dropped. A deterministic redactor may create a new,
separately classified field only when its transformation is exact and auditable.

### Pattern-specific policy

- **Baton-pass:** select target-necessary history, preserve provenance, bind the
  destination profile/provider, update the single active owner only on commit,
  and transfer final-response ownership.
- **Isolated consultation:** construct a minimized child envelope, never copy the
  parent transcript by default, assign an independent child transcript and
  narrow tool set, validate the typed return, then let the parent finish.
- **PCC:** apply the PCC boundary grant and disclose off-device processing. PCC
  facts do not waive data minimization, tool gating, or trace safety.
- **Custom provider:** require named-provider disclosure, retention/training and
  server-tool policy, explicit allowed fields/classes, and a separate grant. Do
  not claim PCC equivalence.
- **Fallback:** no fallback may increase data class, field set, provider trust,
  retention, tool authority, or effect capability without a new matching grant.

## Confirmation and authorization boundaries

A provider grant is session/person scoped and binds all of:

- source profile/provider and named destination profile/provider;
- purpose, allowed classes, exact field names, tool set, and retention policy;
- session/person identifier, expiry, and independent `policyVersion`;
- applicable disclosure and whether an exceptional C2 transfer is permitted.

A provider, purpose, class, field, retention, tool-set, expiry, person/session,
or policy-version change invalidates the grant. A grant is not an effect
confirmation.

Effect confirmation is required immediately before destructive, financial,
public or exfiltrating, shared-content, irreversible, or hard-to-undo actions.
It binds the semantic action, normalized arguments, recipient/resource,
provider/profile, `stateVersion`, `policyVersion`, effect budget, and
idempotency key. After confirmation and before execution the application
revalidates authentication/unlock state, permissions, semantic argument
constraints, recipient/resource identity and version, active state, and grant.
Auth expiry or any bound-field change rejects the call and requires a new
confirmation.

Model text, prompt text, a summary, tool output, a previous confirmation, or a
structurally valid generated object cannot create or broaden authority. A
matching typed application event is the only confirmation input to the reducer.

## Deterministic state and effect model

The reducer is the only transition/effect authority. It accepts typed events and
returns a new state plus zero-or-one executor command; it never parses control
events from text.

The stable state owns one `activeProfile`, one `provider`, independent monotonic
`stateVersion` and stable `policyVersion`, transition count/budget, valid graph
edges, phase, optional pending transition/checkpoint, executor command count,
effect ledger, and metadata-only audit records.

The corrected authority contract is binding:

1. A proposal separately binds `sourceStateVersion` and `policyVersion`.
2. Proposal phase is checked before transition budget or any other mutation.
   Only `stable` may start a transition.
3. Graph edge, destination, purpose, field/class policy, grant policy version,
   state version, and policy version must all match.
4. A valid proposal creates a checkpoint and enters `transitioning`; only then
   may it increment transition/command counts and emit one command.
5. Commit changes active profile/provider and increments only `stateVersion`.
   `policyVersion` changes only through a separate trusted policy operation.
6. Pre-commit failure or cancellation restores checkpoint identity and
   `stateVersion`, clears pending/checkpoint state, and returns to `stable`.
7. A possible or confirmed external effect is never represented as rolled back.
   Its synthetic effect ID stays in the application-owned ledger and phase
   becomes `recoveryRequired` until reconciliation.
8. Failure/cancellation events have authority only during `transitioning`.
   Late or replayed events in `stable`, `terminated`, or `recoveryRequired`
   cannot change authority, phase, pending state, checkpoint, count, or ledger.

The guarantee is application-controlled **at-most-once** execution plus
reconciliation, not exactly-once delivery. An external service can fail after
commit or lack idempotency; transcript rollback cannot undo that effect.

## Mandatory testable invariants

These are mandatory plugin/application policy, not Apple API guarantees:

1. **Untrusted-data:** prompts, retrieved content, tool output, summaries, model
   responses, and repository text never become control events, grants,
   confirmations, policy updates, or tool-result evidence.
2. **Proposal/authority:** a model may propose; only the reducer may authorize,
   command, commit, terminate, or enter recovery.
3. **Single-active:** exactly one stable profile/provider is active outside a
   named transition; every committed state change uses a valid graph edge.
4. **Independent versions:** proposal `sourceStateVersion`, state
   `stateVersion`, proposal/grant/state `policyVersion`, and their update rules
   remain separate. Commit increments only `stateVersion`.
5. **Phase-before-budget:** an in-flight, recovery, terminated, or late proposal
   is ignored before it can consume budget, clear pending state, or mutate a
   checkpoint.
6. **Finite execution:** model turns, tool calls, effects, and transitions have
   explicit budgets. Exhaustion terminates without another command.
7. **Boundary envelope:** every crossing has named destination, purpose,
   classified fields, provenance, retention, redactions, versions, and current
   grant. Unknown data blocks.
8. **Provider truth:** PCC guarantees are never attributed to a custom provider;
   opaque provider tools are labelled unknown rather than absent.
9. **Least context:** isolated consultation never receives the parent transcript
   by default; baton-pass receives only target-necessary selected history.
10. **Tool gate:** every effectful call is checked immediately before execution
    for allowlist, schema and semantic arguments, recipient/resource, versions,
    authority, current auth/permissions, confirmation, and effect budget.
11. **Tool-result provenance:** accepted results bind outstanding call ID,
    expected tool/version/provider, current state, and result type. Model text or
    mismatched output cannot close a call.
12. **At-most-once effect:** each logical effect has a stable idempotency key and
    ledger entry. Retry reconciles the recorded result and emits no second
    executor command.
13. **Truthful recovery:** pre-commit rollback and uncertain external effect are
    separate. Any possible commit enters `recoveryRequired` until reconciled.
14. **Cancellation:** pre-commit cancellation restores the checkpoint; uncertain
    cancellation records the effect and requires recovery without duplication.
15. **Concurrency:** one response/transition mutates a session at a time;
    stale-version events, duplicate commits, and transcript mutation during a
    response fail closed.
16. **Transcript validity:** resumed history has balanced provenance-valid
    call/output pairs, no partial response treated as final, and instructions and
    tools consistent with the active profile. A summary cannot repair it.
17. **Fallback:** unavailable-model fallback cannot silently expand data,
    provider trust, tools, or effects. Otherwise return explicit unavailable or
    degraded state.
18. **Trace safety and evidence integrity:** default proof is metadata-only,
    synthetic, offline, deterministic, credential-free, and contains no raw
    prompt/response/reasoning/tool data or committed `.trace`/`.xcresult` file.
    Missing host capability is a blocker, never a pass.

## Recommended controls

These controls are recommended defense in depth and are not substitutes for the
mandatory invariants:

- Show the active model/provider, pattern (baton-pass or isolated
  consultation), selected data classes, final-response owner, and degraded or
  recovery status in reviewable UI.
- Prefer tool mode `.disallowed` when a phase needs no tools, once a compatible
  Xcode 27 integration is available.
- Prefer short-lived grants, simple revocation, reversible effects, and staged
  preview/commit APIs.
- Use Apple’s beta `.onToolCall` and `.historyTransform` hooks as additional
  enforcement points only after compatible-host compilation; keep the reducer
  authoritative if callbacks change.
- Spotlight untrusted content and evaluate prompt defenses, while treating
  those probabilistic measures as bypassable.
- Expose a redacted human-readable audit of boundary decisions and effect
  reconciliation.
- Measure provider/model/profile changes against the same adversarial suite and
  a pinned model/toolchain. Do not infer security from quality evaluation.
- Keep explicitly requested raw traces outside the repository under separate
  access, retention, and deletion controls.

## Threat, mitigation, and residual-risk matrix

| Threat | Assets/boundary | Mandatory mitigation | Residual risk |
| --- | --- | --- | --- |
| Indirect prompt injection | Untrusted context to model and executor | Keep context as data; typed events only; deterministic reducer; tool and transition checks | Model behavior may still be influenced; prompt-level defenses are probabilistic. |
| Data exfiltration | Private data plus outward tool/provider | C3 block, C2 default block, field-level envelopes, recipient/resource validation, effect confirmation | Classification/redaction can miss novel sensitive data. |
| Over-sharing | Baton-pass, consultation, provider boundary | Target-necessary selection; isolated child envelope; atomic fail-closed transfer | Necessary context is task-specific and may be misclassified. |
| Spoofed tool results / spoofing | Model/provider output to evidence state | Bind call ID, tool/version/provider, type, and current state; label opaque provider tools unknown | A compromised expected provider/tool can still lie within its authority. |
| Authorization confusion | Prompt/summary/old approval to executor | Separate grants and effect confirmations; bind purpose, versions, recipient, expiry, and auth | Confirmation fatigue or deceptive UI can weaken human review. |
| Duplicate effects | Retry across executor/external service | Stable idempotency key, application ledger, at-most-once command emission, reconciliation | External service may lack durable idempotency; exactly-once is not promised. |
| Transition loops | Profile graph and tool loop | Valid graph, transition/turn/tool budgets, phase gate before budget, explicit termination | An allowed but poor transition can consume the finite budget. |
| Partial failure | Transcript/state versus external effect | Separate not-committed from uncertain; checkpoint rollback only before commit; recovery ledger afterward | External truth may remain unavailable and require human repair. |
| Cancellation | In-flight transition/effect | Restore pre-commit checkpoint; uncertain commit enters recovery; late cancellation ignored | User may see a cancelled response while the external effect exists. |
| Inconsistent active state | Concurrent/stale proposals | Single-active invariant, monotonic `stateVersion`, independent policy version, serial mutation | Distributed UI caches may temporarily display stale state. |
| Sensitive logs | Runtime to logs/traces/repository/CI | Metadata-only defaults, privacy redaction, synthetic IDs/hashes, artifact scans | Explicit raw traces remain sensitive even outside the repository. |
| Unavailable-model fallback | Availability/error to provider selection | Equal-or-lower authority fallback only; new provider grant otherwise; explicit unavailable state | Safe fallback may provide less capability or no answer. |
| Summary/transcript poisoning | History rewrite to later inference | Treat summary as untrusted; deterministic validator/repair; balanced provenance | Deterministically valid history may still mislead the probabilistic model. |
| Provider confusion and opaque tools | PCC/custom boundary | Separate disclosures/grants; never infer no tool use from absent local trace | Provider-side behavior may not be independently observable. |
| Generated-code execution | Guidance to host/runtime | Version labels, review, compile/test, explicit execution | Review can miss insecure semantics or environment-specific behavior. |

## Transcript, failure, cancellation, and repair policy

Default application policy captures a stable checkpoint before transition. If a
tool/session error or cancellation is known to occur before any external
commit, restore the checkpoint, clear pending transition state, and leave the
previous profile/provider solely active. This application policy is compatible
with Apple’s Xcode 27 beta default transcript-reversion guidance but does not
claim the installed SDK 26.5 executed that behavior.

If a commit is possible, acknowledged, timed out after dispatch, or otherwise
uncertain, never claim transcript rollback reversed it. Retain one ledger entry,
enter `recoveryRequired`, block further effectful inference, query the external
resource by idempotency key where supported, and resolve to one truthful stable
state. Replayed or late failure/cancellation events outside `transitioning` have
no authority.

Preserved-transcript recovery is an advanced mode only. Before reuse, a
deterministic validator must:

1. freeze inference and effect execution;
2. remove or explicitly mark partial responses;
3. balance each tool call with a provenance-valid typed output or typed failure;
4. reject spoofed call IDs, tools, providers, versions, and result types;
5. confirm instructions, tools, active profile/provider, `stateVersion`, and
   `policyVersion` agree;
6. retain uncertain external effects in the ledger; and
7. produce exactly one valid stable or `recoveryRequired` state.

A model-generated summary may be stored as untrusted context, but it cannot
repair transcript structure, establish tool-result provenance, change state,
grant a provider, confirm an effect, or erase the effect ledger.

## Availability and fallback policy

The installed SDK 26.5 exposes on-device availability and stable
`LanguageModelSession.GenerationError` cases for context exhaustion, unavailable
assets, guardrail violation, unsupported guide/language, decoding failure, rate
limiting, concurrent requests, and refusal, plus `ToolCallError`. Apple’s current
Xcode 27 beta documentation uses a revised error taxonomy and adds provider/PCC
conditions; those beta names remain locally unverified.

| Condition | Required application result | Effect/fallback rule |
| --- | --- | --- |
| Ineligible device, intelligence disabled, assets/model not ready | Stable explicit unavailable state with actionable UI | No silent provider change |
| Context exceeded | Stable blocked/degraded state; deterministically minimize or start an authorized new context | No automatic effect retry |
| Guardrail/refusal/unsupported language | Stable explicit non-result | Never reinterpret as permission to switch provider |
| Decoding failure | Stable typed failure; validate no external effect was dispatched | Retry generation only within budget and without effects |
| Rate/quota limit or PCC network/service failure | Prefer an already authorized on-device path only when it meets the task with equal/lower data and tool authority | A custom/off-device provider requires a new matching grant |
| Concurrent request | Reject stale request and keep one active authority state | No duplicate model/effect invocation |
| Tool error before commit | Restore checkpoint | Command/effect count unchanged after failure |
| Tool timeout/error after possible commit | `recoveryRequired` | Reconcile idempotency key; no second execution |
| Cancellation | Apply the same pre-commit versus uncertain split | Never use cancellation as evidence of rollback |

Fallback selection is a trusted application event, not model text or
configuration prose. If no equal-or-lower-authority path exists, return an
explicit unavailable/degraded result. Availability loss is not permission to
broaden context, tool set, provider trust, retention, or effect capability.

## Trace, logging, and evidence policy

Default application logs and committed evidence are **metadata-only**. Allowed
fields are typed event/decision names, synthetic stable IDs, data classes,
redaction decisions, counts, versions, bounded hashes, blocker classifications,
and pass/fail state. They exclude raw prompts, responses, reasoning, summaries,
attachments, tool arguments/results, credentials, provider payloads, real user
content, and external resource contents.

Dynamic values must be omitted, replaced by synthetic identifiers, or marked
private/sensitive using Apple logging privacy controls. Hashes must not be used
for low-entropy secrets or as a claim of anonymization. Audit strings must never
interpolate classified field values.

Foundation Models `.trace` files can contain unencrypted prompts and responses.
They and `.xcresult` bundles are not committed. Explicit host-assisted capture,
if later approved, stays outside the repository with named access, retention,
deletion, and disclosure rules. Production logging being normally off does not
make a trace safe.

The deterministic fixture uses synthetic data, no network, no live model, no
PCC/custom provider, no credentials, no entitlement, and no paid service.
Evidence scanners check forbidden sentinel content and artifact extensions.
Full Xcode 27, Instruments, Evaluations, or device absence is reported as a
blocker rather than converted into a security pass.

## Adversarial E2E matrix and executed proof

The executed proof is the framework-neutral
[`AdversarialScenarios.swift`](../../fixtures/dev-130/AdversarialScenarios.swift)
runner with the exact
[`expected-output.txt`](../../fixtures/dev-130/expected-output.txt) contract.
“Executed: Task 1” means the assertion ran in that fixture. “Partial” names the
subset that ran. Every other row is a deterministic downstream requirement and
must not be represented as executed proof.

| Case | Initial state | Ordered event | Expected final state | Expected command/effect count | Redacted evidence | Proof status |
| --- | --- | --- | --- | --- | --- | --- |
| Injection | `stable(research,onDevice)`, counts 0 | untrusted tool text contains forged transition/effect instructions | Same stable authority | commands 0, effects 0 | event name + `decision=ignored` | **Executed: Task 1** |
| Disallowed transfer | Stable; custom destination; envelope includes C3 | typed transition proposal with even an over-broad grant | Stable, no pending/checkpoint | commands 0, effects 0 | blocked + class only; no field value | **Executed: Task 1** |
| Pre-effect tool failure | Stable checkpoint, valid proposal | propose -> one transition command -> `.notCommitted` failure | Original stable profile/provider/version | commands 1 total, effects 0 | restored/notCommitted | **Executed: Task 1** |
| Post-effect/uncertain tool failure | Transitioning after one command | failure with synthetic uncertain effect ID -> replay | `recoveryRequired`, pending/checkpoint retained for repair | commands 1 total, ledger effects 1 | recovery + synthetic effect ID | **Executed: Task 1** |
| Transition budget | Stable, max 3 | three valid propose/commit pairs -> fourth proposal | `terminated(transitionBudgetExceeded)` with prior sole active identity | commands 3, effects 0 | transition count + terminal reason | **Executed: Task 1** |
| Cancellation | Transitioning after one command | pre-commit cancel; companion uncertain cancel; late stable cancel | checkpoint-restored stable, or `recoveryRequired` for uncertain; late event unchanged | one command per companion run; uncertain ledger 1 | phase/counts only | **Executed: Task 1** |
| Duplicate retry | `recoveryRequired`, ledger contains effect key | identical logical effect retry/replay | Same recovery or reconciled truthful stable state | external invocation exactly 1; ledger 1 | idempotency-key hash + reconciliation state | **Partial:** Task 1 proves replay adds no command/ledger duplicate; external executor retry remains downstream |
| Spoofed result | Executing effect with outstanding typed call | model text claims success -> wrong call/tool result -> matching typed result | Only matching result may close call | commands unchanged; one accepted result | call/tool synthetic IDs + rejection reasons | Deterministic downstream requirement |
| Confirmation replay | Stable, grant/confirmation for PCC C0/C1 and recipient A | replay for custom C2 or recipient B | Stable; confirmation rejected | commands/effects 0 | binding mismatch names only | Deterministic downstream requirement |
| Summary poisoning | Stable, no grant/effect | summary claims user approved custom provider/delete | Same grants, ledger, active state | commands/effects 0 | `source=summary decision=untrusted` | Deterministic downstream requirement |
| Unsafe fallback | PCC unavailable/quota; custom configured | provider-unavailable event -> attempt custom fallback without grant | Explicit unavailable, or authorized on-device degraded state | provider/effect commands 0 unless equal/lower authorized on-device | availability class + selected safe outcome | Deterministic downstream requirement |
| Stale concurrency | Stable version N; two proposals from N | accept first/in-flight -> second proposal; companion stale proposal | At most one transition; no dual active state | commands at most 1, effects 0 | phase/version mismatch only | **Executed: Task 1** for stale and in-flight proposal rejection |
| Transcript repair | Preserved history with partial response/unmatched call | resume request -> validator repair/drop -> validate | Inference blocked until one valid stable/recovery state | effect commands 0 during repair | entry types/counts/provenance decisions | Deterministic downstream requirement |
| Auth expiry | Confirmed while unlocked | auth expires -> immediate pre-execution revalidation | Stable blocked/awaiting fresh confirmation | effect commands 0 | auth-state class, no credential | Deterministic downstream requirement |
| Opaque provider tools | Custom provider returns final text without typed tool trace | accept provider response metadata -> render disclosure | Response may continue, but tool activity is `unknown` | local tool count unknown, never asserted zero | provider ID + `toolVisibility=opaque` | Deterministic downstream requirement |
| Trace leakage | Synthetic classified fields and reasoning markers | run default audit -> scan repository/log output | Stable; evidence contains metadata only | effects unchanged; leaked values 0 | classes, hashes, counts | Partial: Task 1 proves C3 field value absent from provider/audit; full trace scanner downstream |
| Error/fallback mapping | Table-driven stable state for each installed/beta-labelled error class | context/refusal/decoding/rate/concurrent/tool/timeout/cancel event | Explicit stable, terminated, unavailable, or `recoveryRequired` mapping | no silent retry; effect count at most prior ledger | error class + mapped phase only | Deterministic downstream requirement |

The executed output contains seven PASS scenario lines and
`SUMMARY passed=7 failed=0`; repeated runs are byte-identical. The fixture also
asserts separate state/policy versions, grant mismatch cases, proposal phase
gating, late-event immunity, and uncertain replay. It does not invoke a model,
Apple callbacks, a provider, Instruments, Evaluations, or an external effect.

## Downstream decision contract

These requirements bind the named follow-on issues:

| Issue | Binding DEV-130 contract |
| --- | --- |
| DEV-132 | Architecture must keep the deterministic reducer authoritative, model proposals untrusted, baton-pass distinct from isolated consultation, and one stable active profile/provider. |
| DEV-134 | Context transfer must implement C0–C3 classification, provenance attributes, atomic fail-closed envelopes, target-necessary history, destination grants, and PCC/custom-provider truth. |
| DEV-136 | Tooling must enforce semantic argument/recipient/resource checks, immediate bound confirmation, auth revalidation, provenance-valid results, idempotency, and application-controlled at-most-once execution. |
| DEV-137 | State orchestration must keep `stateVersion` and `policyVersion` independent, phase-gate before budget mutation, serialize authority changes, enforce finite budgets, and ignore late failure/cancellation outside transition. |
| DEV-138 | The fixture suite must execute all deterministic downstream rows above, retain exact output contracts, remain offline/synthetic, and never treat optional host blockers as passes. |
| DEV-139 | Transcript handling must default to checkpoint recovery, separate pre-commit rollback from uncertain effects, block inference during repair, validate balanced provenance, and treat summaries as untrusted. |
| DEV-141 | Observability/evidence must be metadata-only by default, scan for leaks and forbidden artifacts, keep raw traces outside the repository, and label Apple facts, Xcode 27 beta guidance, and plugin policy separately. |

All downstream code and guidance must preserve the installed SDK 26.5 versus
official Xcode 27 beta boundary. A changed SDK, Xcode, OS, provider, tool set, or
policy version requires re-running interface/source checks, deterministic
fixtures, blocker classification, and the complete adversarial suite.
