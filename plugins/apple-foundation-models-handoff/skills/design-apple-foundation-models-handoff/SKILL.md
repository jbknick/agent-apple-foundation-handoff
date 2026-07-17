---
name: design-apple-foundation-models-handoff
description: Design an Apple Foundation Models handoff architecture, topology, pattern, state model, or trust boundary when the user is creating or materially revising how sessions, profiles, or providers transfer control or provide isolated consultation.
---

# Design Apple Foundation Models Handoff

## Routing and Inspection

Normalize these router inputs in order:

domain = foundation_models_handoff | out_of_domain | ambiguous
requestedOperation = design | implement | review | debug | validate | compound_review_fix | unspecified
artifactState = absent | proposal | approved_contract | implementation | evidence_bundle | unknown
evidenceState = not_requested | missing | available | failing | blocked | unknown

Classify the domain before selecting work. Activate design only for a new or
materially revised Foundation Models handoff architecture, topology, state model,
or trust boundary.

Choose exactly one primary workflow. Ask exactly one targeted clarification when
the domain is ambiguous. For compound review and fix, run review first and name a
separate authorized follow-on boundary. Do not invoke another skill.

Adjacent non-triggers: Apple Handoff; NSUserActivity; App Intents; Swift actors;
generic Core ML; coding-session handoff; Agent Skills;
Foundation Models runtime Skills.

### no_activation

```text
activationStatus = no_activation
reasonCode = out_of_domain
domain = out_of_domain
requestedOperation = design | implement | review | debug | validate | compound_review_fix | unspecified
```

### clarification_required

```text
activationStatus = clarification_required
clarificationKind = domain | approved_contract
missingInput = domain | approved_contract
question = <one bounded question>
```

## Common Workflow Protocol

1. Inspect the repository, relevant artifacts, and installed SDK interfaces before asserting implementation facts.
2. Resolve the router inputs and state the selected workflow.
3. Establish the current owner, next owner, trust boundary, and effect authority.
4. Separate control-plane state from model context and minimize transferred data.
5. Distinguish consultation from ownership transfer.
6. Use version-labelled state, deterministic transitions, bounded retries, idempotency and reconciliation, and explicit recovery and fallback.
7. Ground Apple claims through installed interfaces and the direct references.
8. Compile-check Swift examples where supported; otherwise label pseudocode or an exact blocked prerequisite.
9. Emit the common result envelope plus workflow-specific sections.
10. Separate fact, inference, pseudocode, unsupported API, limitation, blocker, and not_applicable evidence.

## Output Contract

```text
activationStatus = activated
selectedSkill
routerInput = { domain, requestedOperation, artifactState, evidenceState }
architectureResult
  architectureSchemaVersion: "1.0"
  stateVersion: <independent state schema version>
  policyVersion: <independent policy version>
  workflow
  scope
  pattern = baton_pass | isolated_consultation | deterministic_routing | transcript_transfer
  source = { profile, provider }
  destination = { profile, provider }
  finalResponseOwner
  apiAvailability[] = { surface, versionLabel, compileStatus, source }
  stateModel
  trustBoundaries[]
  contextPolicy
  toolAndEffectPolicy
  failurePolicy
  verification[] = { id, layer, status, evidence }
  limitations[]
```

### Activation and Scope

Begin every positive response with one fenced `text` result using the exact outer and
nested field names, nesting, and order shown above. Populate every field; do not
replace that shape with YAML or JSON. Then render every common and design-specific
heading below verbatim and in order; do not rename, merge, or omit a heading.

State the activation reason, design boundary, inspected artifacts, assumptions, and
unavailable prerequisites. Keep adjacent Apple concepts outside the scope.

### Pattern and Ownership

Compare baton pass, isolated consultation, deterministic routing, and transcript
transfer. Select one pattern or an explicit no-handoff outcome. Name source,
destination, trigger, current owner, next owner, and final response owner.

### Apple API Availability

List each Apple surface used by the proposal with its evidence source, version label,
and local compile or interface-inspection state. Keep unsupported surfaces labelled.

### State and Lifecycle

Define reducer authority, stable identities, valid transitions, termination,
cancellation, retry budgets, idempotency, reconciliation, and version migration.

### Trust and Model Boundaries

Identify each session, profile, provider, process, and external service boundary.
State the grant that permits each transfer and keep provider properties separate.

### Context Policy

Classify the minimum context needed by the destination. Separate control-plane state
from model context and define redaction, retention, provenance, and revalidation.

### Tools Effects and Confirmation

Define tool provenance, allowed effects, confirmation timing, stable effect identity,
result provenance, and the authority boundary for every requested side effect.

### Failure Recovery and Fallback

Define fail-closed transitions, bounded retry, external-effect reconciliation,
recovery prerequisites, and an equal-or-lower-authority fallback.

### Verification and Evidence

status = pass | fail | blocked | not_applicable

Bind deterministic checks, compile checks, host prerequisites, and human review to
specific claims. A zero denominator produces not_applicable with a null value.

### Limitations

List unverified assumptions, unsupported APIs, missing host or SDK proof, residual
risk, and decisions deferred to implementation.

### Alternatives

Compare viable patterns against topology, history, trigger, ownership, context,
effect, recovery, testability, and evidence requirements.

### Decision Rationale

Select one architecture and explain why it satisfies the stated ownership and trust
contract better than the alternatives.

### Proposed Components

Name the reducer, session or profile boundaries, policy objects, adapters, fixtures,
and evidence surfaces required by the design without inventing framework types.

### Implementation and Test Plan

Provide bounded change phases, exact validation layers, compile prerequisites,
deterministic cases, host blockers, and rollback or reconciliation gates.

## References

- [Architecture and state](../../references/architecture-and-state.md) — result schema, ownership, lifecycle, and transitions.
- [Orchestration patterns](../../references/orchestration-patterns.md) — topology, history, triggers, and final-owner selection.
- [Apple API availability](../../references/apple-api-availability.md) — installed interfaces, version labels, and unsupported boundaries.
- [Security, context, and recovery](../../references/security-context-and-recovery.md) — trust, grants, effects, recovery, and fallback.
- [Evaluation and observability](../../references/evaluation-and-observability.md) — deterministic checks, host evidence, and rubric semantics.

## Guardrails

Ground Apple claims in official Apple documentation, installed SDK interfaces, WWDC,
and Apple-owned repositories. Use compiled_sdk_26_5 and
interface_verified_sdk_26_5 only for their proven local evidence boundaries.
Compile-check Swift examples where supported; otherwise label pseudocode and
unsupported APIs. A missing SDK, host, toolchain, binary, hardware, or prerequisite
is blocked, never a pass. If a fixed reference target is absent, report the DEV-137
integration prerequisite as blocked; do not create a substitute.

Non-positive results contain no architectureResult, workflow-specific sections,
references, fabricated Apple claims, or host activation evidence.
