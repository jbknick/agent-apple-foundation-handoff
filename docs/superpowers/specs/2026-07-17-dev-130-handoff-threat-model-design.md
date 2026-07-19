# DEV-130 Handoff Security, Privacy, and Failure Threat Model Design

Issue: [DEV-130](https://linear.app/devprentice/issue/DEV-130/r4parallel-define-the-handoff-security-privacy-and-failure-threat)

Primary-source collection range: `2026-07-16` through `2026-07-17`

Host-evidence refresh: `2026-07-19`

## Purpose

DEV-130 defines enforceable security, privacy, trust-boundary, and recovery
requirements for Apple Foundation Models handoff architectures before the
production skills and reference library are written. It covers baton-pass,
isolated consultation, provider changes, transcripts, tools, traces, and
generated guidance without implementing a production runtime or security
system.

The issue produces a source-grounded threat model and a minimal deterministic
adversarial fixture. The fixture is application-policy pseudocode expressed as
framework-neutral Swift. It is not a `FoundationModels` handoff API, a runtime
package, or a substitute for DEV-138's production-quality fixture suite.

## Evidence and approval boundary

Apple facts use current official Apple documentation, WWDC26 material, the
Private Cloud Compute Security Guide, and the installed SDK 26.5
`FoundationModels.swiftinterface`. The installed interface has SHA-256
`ff2285670b0966addb9827dc895a3ee3c9db6e186baae62c034fed012632aacc`.

The selected policy is the approved DEV-130 brainstorming record. It chooses:

- four data classes plus provenance attributes;
- session-scoped, destination-bound provider grants plus per-effect
  confirmation;
- a deterministic reducer as the only authority for transitions and effects;
- revert-to-checkpoint recovery while retaining an application-owned effect
  ledger; and
- deterministic offline adversarial proof with metadata-only evidence.

An independent verification refinement preserves a strict SDK boundary:
Apple's `.onToolCall`, `.historyTransform`, mutable session transcript, and
transcript error policies are official Xcode 27 beta guidance. The installed
SDK 26.5 session transcript is get-only. These beta surfaces may illustrate
controls but are not default-test prerequisites or locally verified APIs.

The refreshed host uses Xcode 26.6 (17F113), Swift 6.3.3, and the macOS and
iPhoneOS 26.5 SDKs. `xctrace` and `simctl` are available, while the legacy
`Instruments` binary, SDK 27 declarations, and the `Evaluations` module remain
blocked. The pinned Foundation Models interface hash is unchanged. Availability
of those host tools is structural evidence only; no live model or bridge call
was executed for DEV-130.

## Selected policy architecture

The policy layer distinguishes model proposals from application authority.
Prompts, retrieved content, tool output, model responses, summaries, and
repository text remain untrusted data. A typed event may be created only by a
trusted application boundary; the reducer never parses control events,
confirmations, policy changes, or authorization from untrusted text.

The state model has exactly one stable active profile and provider outside a
named transition. Each transition is checked against a valid graph edge,
monotonic state version, independently stable policy version, finite transition
budget, classified context envelope, and matching boundary grant. A proposal
binds its source state version and policy version separately; commit increments
only the state version. Effectful tools additionally require current
authorization, semantic argument checks, recipient/resource checks, immediate
confirmation when the effect is high-impact, an idempotency key, and an effect
ledger entry.

The design promises application-controlled at-most-once execution plus
reconciliation, not exactly-once delivery. Transcript rollback cannot undo an
external effect. A timeout, cancellation, or error after a possible commit
enters `recoveryRequired` until the ledger and external resource are reconciled.

### Diagnostic-result routing boundary

The July 18 host contract selects diagnostic tool results at `PostToolUse` and
uses the exact action `condense_diagnostic_output` for an Apple-first local
bridge. The host executes the original tool once, then constructs a request
only from fields with an allowlisted name and typed `trustedLocal` origin. An
approved name does not admit a remote or otherwise non-local value. The bridge
is not allowed to trigger the tool again.

The Apple response remains untrusted until its schema version, call ID, tool
name and version, source state version, action, original result type, and
response result type match the request. A valid response may replace the
visible result. A decline preserves the original result without an error;
invalid output, failure, timeout, or cancellation preserves the original,
returns a bounded normalized error, and never duplicates the original effect.
Audit evidence records metadata only. DEV-130 models this resolver as a pure
repository fixture; it does not install or invoke the production hook or bridge.

## Data and confirmation policy

Every context field has one class and provenance attributes for source,
subject, purpose, allowed destination, retention, and redaction status:

- `C0 Public`: intentionally public, non-secret content.
- `C1 Task-private`: non-sensitive private content needed for the approved task.
- `C2 Sensitive`: personal, regulated, high-impact, or confidential content.
- `C3 Never-transfer`: credentials, signing material, unrelated third-party
  private data, out-of-purpose content, and anything that cannot be classified
  safely.

Unknown or unclassified provider-bound data fails closed. `C3` never crosses a
model boundary. `C2` is minimized and normally blocked for isolated
consultation or custom providers; an exceptional crossing requires named
fields, destination, purpose, retention policy, and bound confirmation.

A provider grant binds session/person, source, named destination, purpose,
allowed classes and fields, tool set, expiry, and policy version. Provider,
class/field, purpose, authority, expiry, or policy-version changes require a new
grant. Destructive, financial, public/exfiltrating, shared-content,
irreversible, or hard-to-undo effects are confirmed immediately before
execution, followed by revalidation of authentication, arguments, recipient,
state version, and permissions.

## Handoff and provider boundaries

Baton-pass and isolated consultation remain different trust patterns.
Baton-pass selects and filters target-necessary history, changes the active
profile/provider, and transfers final-response ownership to the destination.
Consultation constructs a minimized child envelope, keeps an independent child
transcript, and returns control and final-response ownership to the parent.

On-device, PCC, and a custom provider are distinct trust boundaries. On-device
execution does not neutralize untrusted context, unsafe tools, over-sharing, or
trace disclosure. PCC-specific statelessness, transparency, routing, and
retention claims must not be attributed to a custom provider. A fallback cannot
silently expand provider trust, data exposure, tool authority, or effect
capability.

## Transcript, cancellation, and failure policy

The default application policy captures a stable checkpoint, including the
source state version, before a transition. A pre-commit error or cancellation
restores that checkpoint and leaves the previous stable profile/provider active.
A possible or confirmed external commit remains in the effect ledger and moves
to recovery rather than being represented as rolled back. Proposals are phase
gated before budget evaluation, and failure or cancellation events have
authority only while a transition is in flight. Late events in stable,
terminated, or recovery state cannot alter authority, phase, pending transition,
checkpoint, or effect ledger.

Preserved-transcript recovery is an advanced mode only. Further inference is
blocked until a deterministic validator removes or marks partial responses,
balances call/output pairs, checks provenance and active profile/tool
definitions, and produces one valid stable state. A model-generated summary
cannot repair transcript structure or establish authorization.

## Trace and evidence policy

Default logs and committed proof contain typed event names, synthetic stable
IDs, classifications, decisions, counts, hashes, and redactions only. They
exclude raw prompts, responses, reasoning, tool arguments/results, credentials,
real user content, and `.trace` files. Explicit raw Instruments capture is kept
outside the repository under separate retention and deletion controls.

Default proof uses synthetic sentinels and no network, PCC, provider
credential, paid service, model generation, hardware, or live Apple-runtime
requirement. Missing Xcode/SDK 27, the legacy `Instruments` binary,
`Evaluations`, or a compatible beta target is an explicit optional-host
blocker, never a security pass. Xcode 26.6, iPhoneOS 26.5, `xctrace`, and
`simctl` availability are reported as current structural passes, not runtime
security proof.

## Deterministic fixture boundary

The fixture is split into a reusable mock policy file and an executable
adversarial runner:

- `fixtures/dev-130/HandoffSecurityPolicy.swift` owns data classes, provider
  grants, transition/effect state, typed events, and the pure reducer.
- `fixtures/dev-130/AdversarialScenarios.swift` owns assertions and executable
  scenarios.
- `fixtures/dev-130/expected-output.txt` is the exact output contract.

The runner executes the five required scenarios and strengthens the two
partial-failure cases into pre-commit and uncertain-commit variants:

1. untrusted tool output contains forged transition/effect instructions but
   emits no executor command;
2. a custom-provider envelope containing `C3` content is blocked and the secret
   sentinel appears in neither provider serialization nor audit output;
3. a pre-commit tool failure restores the checkpoint, while an uncertain commit
   enters recovery without another execution;
4. three transitions are allowed and the fourth is terminated by the budget;
5. pre-commit cancellation restores the checkpoint, while cancellation after a
   possible effect enters recovery without duplication.
6. selected diagnostic results route only fields with an approved name and
   trusted-local origin through exact action `condense_diagnostic_output`; only
   a schema- and provenance-bound Apple response is accepted, while decline,
   failure, timeout, and cancellation preserve the once-executed original
   result without rerun.

The fixture validates application policy only. It does not invoke a model,
prove Apple framework callbacks, exercise a provider, or claim exactly-once
external effects.

## Artifacts and commit boundaries

The DEV-130 issue delta is based on current `origin/main` and contains exactly
these seven files:

- this design;
- `docs/superpowers/plans/2026-07-17-dev-130-handoff-threat-model.md`;
- `docs/research/dev-130-handoff-threat-model.md`;
- `docs/research/evidence/dev-130-command-transcript.md`;
- `fixtures/dev-130/HandoffSecurityPolicy.swift`;
- `fixtures/dev-130/AdversarialScenarios.swift`; and
- `fixtures/dev-130/expected-output.txt`.

Historical implementation commits remain reviewable. Integration uses exactly
three main-agent review/fix rounds; each round delegates named corrections to a
fresh worker and re-verifies the resulting diff. After zero actionable findings
and current gates, the reviewed head is force-pushed only with an exact lease,
squash-merged to `main` with head-SHA protection, and checked for reviewed-tree
identity plus a merged-result smoke run. Linear receives only completion-contract
evidence and status propagation required by the issue definition of done.
