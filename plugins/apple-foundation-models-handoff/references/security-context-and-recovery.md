# Security, Context, and Recovery Policy

## Scope and authority

This reference owns the separation of Apple security facts from mandatory
application policy and recommended controls. It defines trust boundaries,
context classes, provenance, grants, confirmations, tool-result provenance,
effects, recovery, safe fallback, trace handling, and residual risk. Exact API
declarations and availability are owned by
[Apple API availability](apple-api-availability.md); framework mechanisms never
replace the application reducer in [architecture and state](architecture-and-state.md).

Every substantive rule is labelled as one of:

- **Official Apple fact** — directly supported by an official source;
- **Mandatory application policy** — required by this handoff architecture,
  not an Apple framework guarantee; or
- **Recommended control** — defense in depth that does not replace mandatory
  checks.

## Untrusted inputs and trust boundaries

**Official Apple fact:** WWDC26 session 347 identifies indirect prompt
injection in external context and tool results, plus unintended action and data
exfiltration risks when agents can perform side effects. Apple recommends
deterministic mitigations as an auditable baseline, minimizing/redacting
sensitive context, confirming risky actions, and applying authentication where
appropriate.

**Mandatory application policy:** treat user-supplied text, copied transcript
entries, files, web/provider responses, calendar/contact/feed data, model text,
and tool outputs as untrusted until classified and validated. Model output is a
proposal, never authorization or proof of external truth.

| Boundary | Threat | Mandatory response |
| --- | --- | --- |
| Person/application -> model | Overbroad or poisoned context | Classify provenance, minimize fields, label untrusted content, and bind purpose |
| Model -> tool/executor | Action/data poisoning | Validate typed arguments, grant, confirmation, versions, recipient, and effect policy before execution |
| Provider change | Privacy/retention/auth differences | Require provider-specific grant and disclose the selected provider |
| Tool/provider -> transcript | Forged or replayed result | Validate typed tool-result provenance and correlation before state change |
| External effect system | Timeout or uncertain commit | Preserve one effect identity and enter recovery until reconciled |

## Context classes and provenance

**Mandatory application policy:** every field carries source identity,
acquisition time, classification, purpose, integrity/validation state,
retention, and allowed destination/provider.

| Class | Examples | Transfer rule |
| --- | --- | --- |
| `C0` | Public or purpose-created nonsensitive facts | Transfer only the necessary fields with provenance |
| `C1` | Person-provided task context with limited sensitivity | Require destination/purpose binding and bounded retention |
| `C2` | Sensitive personal, account, or private workspace data | Require explicit policy, minimization, provider eligibility, and confirmation where effects or disclosure warrant it |
| `C3` | Secrets, credentials, authentication material, private keys, or policy-prohibited content | C3 is never transferable to a model, provider, transcript handoff, tool result, trace, or committed evidence |

**Recommended control:** transform source values into typed, allowlisted fields
before the boundary rather than attempting to remove unsafe data afterward.

## Atomic boundary envelopes

**Mandatory application policy:** a transfer envelope is atomic and fail-
closed. Missing or invalid fields reject the whole envelope; no partial subset
is silently accepted.

Required envelope members are source, destination, purpose, allowlisted fields,
tools, context classifications, provenance, retention, expiry, person identity,
`stateVersion`, `policyVersion`, grant identity, confirmation identity when
needed, and correlation/effect identities. Hashes cover the canonical envelope
and the versions used for authorization.

The recipient verifies the same envelope before use. A field not named by the
grant is absent, not merely hidden by instructions.

## Provider grants

**Mandatory application policy:** every provider grant is bound to destination,
purpose, fields, tools, retention, expiry, person, `stateVersion`, and
`policyVersion`. It is nontransferable to another provider, model, child
session, purpose, or effect. Revocation or version drift invalidates it.

**Official Apple fact:** published PCC privacy/security properties describe
PCC. They do not transfer to a custom provider. Provider packages can own
authentication, transport, server tools, logging, retention, and error mapping.

**Recommended control:** use secure credential storage and device attestation
for server providers, while keeping credential material outside model context,
logs, evidence, and tool arguments.

## Immediate effect confirmation

**Mandatory application policy:** the person confirms the exact effect
immediately before execution after seeing the resolved tool, recipient,
parameters, scope, and consequences. Confirmation is bound to the canonical
arguments, person, grant, state, and policy versions; a changed value requires
new confirmation. This immediate effect confirmation is never reusable.

After confirmation and before the executor command, revalidate authentication,
permission, recipient, availability, `stateVersion`, `policyVersion`, expiry,
and effect identity. A previously confirmed proposal is not a standing grant.

**Official Apple fact:** current beta lifecycle documentation says
`.onToolCall` runs before tool execution and a thrown error prevents the tool
from executing. The declaration and Xcode 27 `official_beta_unverified` label
are owned by [Apple API availability](apple-api-availability.md).

## Reducer authority

**Mandatory application policy:** the deterministic reducer is authoritative
for phase, versions, ownership, budgets, grants, confirmations, command
emission, effect ledger, fallback, and repair. A model, profile, transcript,
lifecycle callback, provider, or tool response cannot directly mutate these
facts.

The reducer validates phase before budgets. Ordinary termination starts only
from `stable`. Uncertain external truth remains `recoveryRequired` with the
checkpoint, pending transition, counts, ledger, and repair facts intact.

## Tool-result provenance

**Mandatory application policy:** typed tool-result provenance includes tool
identity/version, provider/executor identity, request/correlation/effect IDs,
canonical argument hash, source and completion time, result schema/version,
integrity state, classification, and a normalized outcome. Reject an unknown
tool, mismatched correlation, stale versions, malformed schema, duplicate
completion, or model-authored claim that an effect succeeded.

**Recommended control:** render untrusted result content as data with explicit
delimiters and minimize it before the next inference. Do not rely on
spotlighting alone; Apple describes it as probabilistic.

## Command emission and effect reconciliation

**Mandatory application policy:** an accepted transition emits at most one
executor command for one effect identity. The ledger prevents duplicate
command emission, but the system must never promise exactly-once delivery or
external execution.

```text
known pre-commit failure -> checkpoint restore -> stable -> no effect ledger entry
possible/confirmed commit -> one ledger identity -> recoveryRequired
replay/late event -> unchanged state and no executor command
retry -> only after explicit reconciliation establishes external truth
```

Reconciliation queries the authoritative effect system using the same effect
identity. It records confirmed absent, confirmed committed with normalized
result, or still unknown. Only the first two states can resolve recovery; retry
is allowed only after confirmed absence, while confirmed commit is adopted.

## Failure, cancellation, and transcript repair

**Mandatory application policy:** known pre-commit failure or cancellation
restores the stable checkpoint and source authority. Possible commit or
uncertain cancellation preserves repair input and enters `recoveryRequired`.
Cancellation is a transition event, not proof that a tool or provider did
nothing.

**Official Apple fact:** current beta documentation exposes request-local
`.historyTransform`, mutable transcript/history behavior, and transcript error
policy. Their exact Xcode 27 `official_beta_unverified` declarations are linked
through [Apple API availability](apple-api-availability.md). A request-local
transform does not mutate global history; preserved partial history needs
application repair.

**Mandatory application policy:** transcript repair removes or rejects
incomplete tool-call/output pairs, verifies provenance and classification,
redacts fields no longer permitted, preserves source ordering, and records a
new repair hash before reuse. Framework rollback does not reconcile an external
effect.

## Provider truth and safe fallback

**Mandatory application policy:** provider timeout, network failure, stream
end, cancellation, or model text never proves commit/absence. Use an
authoritative provider/effect status endpoint or remain in recovery.

Safe fallback is an explicit policy decision that preserves or narrows trust.
It must not widen context class, destination, provider, tools, effect scope,
retention, or final-response authority. If no authorized fallback exists,
return a bounded unavailable/degraded result.

## Trace policy

**Official Apple fact:** Apple says Foundation Models Instruments can expose
prompts, model output, tools, token use, and timing, and that captured data can
be sensitive and must be handled accordingly.

**Mandatory application policy:** committed evidence contains metadata-only
IDs, versions, counts, statuses, reasons, and hashes. Prompt/response content,
tool payloads, credentials, personal data, provider bodies, and host identity
stay out. Trace and result bundles remain uncommitted sensitive artifacts with
access control, short retention, and a documented deletion path.

**Recommended control:** scan evidence before commit, use synthetic/redacted
corpora, and separate security review from performance collection. This
reference makes no unsupported claim about trace storage encryption.

## Adversarial checklist

- Poisoned external context cannot add a field, tool, destination, or effect.
- Model output cannot mint a grant, confirmation, or successful effect result.
- A stale confirmation fails after any argument, recipient, version, or policy
  change.
- Child/provider/tool results require typed provenance and correlation.
- Duplicate, late, and replayed events mutate nothing and emit no command.
- Known pre-commit failure restores; uncertain commit enters recovery.
- Reconciliation precedes retry and adopts a confirmed existing commit.
- C3 data never enters model context, provider requests, traces, or evidence.
- Provider fallback never inherits PCC properties or prior provider grants.
- Missing safe route returns unavailable/degraded without widening trust.

## Residual risks

Prompt injection and model behavior remain probabilistic; deterministic
boundaries reduce but do not eliminate risk. A compromised application,
provider, device, effect system, or policy authority can still violate its
trust boundary. Reconciliation may remain unavailable, leaving the state in
recovery. Confirmation fatigue, incorrect classification, and poor provenance
can weaken otherwise correct enforcement.

## Related references

- [Architecture and state](architecture-and-state.md)
- [Orchestration patterns](orchestration-patterns.md)
- [Apple API availability](apple-api-availability.md)
- [Evaluation and observability](evaluation-and-observability.md)

## Source ledger

All official sources were retrieved on 2026-07-17.

| Fact family | Official source |
| --- | --- |
| Indirect prompt injection, context/tool threats, confirmation, authentication, lifecycle checkpoints | [WWDC26 session 347](https://developer.apple.com/videos/play/wwdc2026/347/) |
| Dynamic history and lifecycle context | [Composing dynamic sessions](https://developer.apple.com/documentation/foundationmodels/composing-dynamic-sessions-with-instructions-and-profiles) |
| Tool boundary | [Expanding generation with tool calling](https://developer.apple.com/documentation/foundationmodels/expanding-generation-with-tool-calling) |
| PCC properties and limits | [PCC Security Guide](https://security.apple.com/documentation/private-cloud-compute/), [core requirements](https://security.apple.com/documentation/private-cloud-compute/corerequirements) |
| Custom-provider authentication/privacy boundary | [WWDC26 session 339](https://developer.apple.com/videos/play/wwdc2026/339/) |
| Sensitive profiling content | [Runtime performance](https://developer.apple.com/documentation/foundationmodels/analyzing-the-runtime-performance-of-your-foundation-models-app) |

## Limitations

These application controls require correct integration and independent tests;
the framework does not enforce the complete policy. This reference does not
claim immunity from prompt injection, guaranteed provider truth, lossless
repair, external execution semantics, or a safe fallback for every task.
