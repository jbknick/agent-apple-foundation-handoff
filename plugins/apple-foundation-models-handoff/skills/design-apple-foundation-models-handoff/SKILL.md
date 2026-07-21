---
name: design-apple-foundation-models-handoff
description: Design an Apple Foundation Models handoff architecture, topology, pattern, state model, or trust boundary when the user is creating or materially revising how sessions, profiles, or providers transfer control or provide isolated consultation.
---

# Design Apple Foundation Models Handoff

## Final Response Gate

Before drafting, freeze normalized `domain`, `requestedOperation`, `artifactState`,
and `evidenceState`, then copy that same tuple unchanged into `routerInput`; use no
synonyms and do not reclassify later.
On positive activation, `routerInput` is an immutable pre-selection record, not a
workflow finding. Serialize the exact four normalized values from the source
request in the shown field order; never use inspection, execution, evidence
results, or drafted output to infer or revise a value. This serialization neither
invokes nor emulates the router and has no branch or ownership effect.
For an explicit Apple Foundation Models design request with no user-supplied or
user-described artifact or evidence, freeze the exact tuple
`foundation_models_handoff/design/absent/missing`: `domain =
foundation_models_handoff`, `requestedOperation = design`, `artifactState = absent`,
and `evidenceState = missing` before inspection or non-skill tool use.
Once this positive workflow activates, it remains the only workflow owner; never
select, invoke, or switch to another skill.
Make the first character of the final response the opening backtick of the exact
21-line result-envelope `text` fence under Output Contract; emit no prose before it.
Close that fence immediately after its 21st line, then emit only the exact required
headings, each once and in their listed order.
The response is incomplete until the fence is followed by exactly 14 level-three
headings: all ten common headings followed by the workflow-specific headings in
their listed order; do not stop after the fence or omit an empty-but-required heading.

## Routing and Inspection

Normalize these router inputs in order:

domain = foundation_models_handoff | out_of_domain | ambiguous
requestedOperation = design | implement | review | debug | validate | compound_review_fix | unspecified
artifactState = absent | proposal | approved_contract | implementation | evidence_bundle | unknown
evidenceState = not_requested | missing | available | failing | blocked | unknown

Activate design only for a new or
materially revised Foundation Models handoff architecture, topology, state model,
or trust boundary.

Choose exactly one primary workflow. For compound review and fix, run review first
and name a separate authorized follow-on boundary. Do not invoke another skill.

## Common Workflow Protocol

1. Freeze the source-request router inputs and state the selected workflow before inspection or non-skill tool use.
2. Only after pre-selection, inspect the repository, relevant artifacts, and installed SDK interfaces for workflow facts.
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
selectedSkill = design-apple-foundation-models-handoff
routerInput = { domain = <domain>, requestedOperation = <requestedOperation>, artifactState = <artifactState>, evidenceState = <evidenceState> }
architectureResult
  architectureSchemaVersion: "1.0"
  stateVersion: <independent state schema version>
  policyVersion: <independent policy version>
  workflow: <selected workflow>
  scope: <bounded artifact and operation scope>
  pattern = baton_pass | isolated_consultation | deterministic_routing | transcript_transfer
  source = { profile, provider }
  destination = { profile, provider }
  finalResponseOwner: <stable final-response owner>
  apiAvailability[] = { surface, versionLabel, compileStatus, source }
  stateModel: <versioned reducer state and lifecycle>
  trustBoundaries[]: <classified trust boundaries>
  contextPolicy: <minimum-context transfer policy>
  toolAndEffectPolicy: <tool, confirmation, and effect authority policy>
  failurePolicy: <fail-closed recovery and fallback policy>
  verification[] = { id, layer, status, evidence }
  limitations[]: <one-line limitations and blockers summary; close the fence immediately after this line>
```

### Activation and Scope

Serialize `selectedSkill` as the literal assignment
`selectedSkill = design-apple-foundation-models-handoff`. Serialize all four populated
`routerInput` values on exactly one physical line, with `architectureResult` on the
immediately following line. Emit exactly one response-level fenced `text` block,
reserve it for the result envelope, and emit no additional fenced `text` blocks.
Every activated response emits exactly the 21 shown nonblank result-envelope lines in
order with placeholders replaced inline and no added lines. Close the result-envelope
fence immediately after that 21st line, and put every explanation, bullet, subfield,
example, and detail only under the required headings after the fence.
Never wrap, pretty-print,
or expand `routerInput` or any `architectureResult` child across physical lines,
keeping each on its single template line. After the envelope, render only the exact
required headings, each exactly once and in the listed order. Replace every inline
placeholder in the shown shape; do not replace that shape with YAML or JSON.

State the activation reason, design boundary, inspected artifacts, assumptions, and
unavailable prerequisites. Keep adjacent Apple concepts outside the scope.
Design is read-only: make no production edits.

### Pattern and Ownership

Compare baton pass, isolated consultation, deterministic routing, and transcript
transfer. Select one pattern or an explicit no-handoff outcome. Name source,
destination, trigger, current owner, next owner, and final response owner.

Maintain exactly one stable owner at every state; only that owner authorizes the next
transition, and model output, provider output, and tools never become the owner.

### Apple API Availability

List each Apple surface used by the proposal with its evidence source, version label,
and local compile or interface-inspection state. Keep unsupported surfaces labelled.

versionLabel = compiled_sdk_26_5 | interface_verified_sdk_26_5 | official_os_xcode_27_beta_locally_unverified | pseudocode_deterministic_mock | blocked

Record stable SDK 26.5 compile and interface errors separately from locally
unverified OS/Xcode 27 beta errors.

### State and Lifecycle

Define reducer authority, stable identities, valid transitions, termination,
cancellation, retry budgets, idempotency, reconciliation, and version migration.

For every allowed edge, define finite transition, tool-call, and external-effect
budgets. Validate the event, source phase, allowed edge, grant, stateVersion, and
policyVersion before mutating any budget. Persist the checkpoint before setting the
phase to transitioning; only then may the reducer emit at most one executor command.

Treat stateVersion and policyVersion as independent values, each with its own
compatibility and migration rule. Terminate only from a stable phase with no
unresolved pending command, pending effect, or recovery requirement.

### Trust and Model Boundaries

Identify each session, profile, provider, process, and external service boundary.
State the grant that permits each transfer and keep provider properties separate.

Classify every context field atomically as C0, C1, C2, or C3 before transfer; reject
the whole envelope when any field is unknown or disallowed.

Bind every grant to person, session, source profile, source provider, destination
profile, destination provider, purpose, exact context classes, exact fields, tools,
retention, expiry, C2 permission, stateVersion, and policyVersion. Invalidate and
revalidate the grant before use whenever any binding drifts.

### Context Policy

Classify the minimum context needed by the destination. Separate control-plane state
from model context and define redaction, retention, provenance, and revalidation.

### Tools Effects and Confirmation

Define tool provenance, allowed effects, confirmation timing, stable effect identity,
result provenance, and the authority boundary for every requested side effect.

Accept a tool result only when its call ID, tool ID, tool version, provider, result
type, and current state match the pending invocation; otherwise reject it.

Require confirmation plus an application-controlled effect ID and application-owned
effect ledger; execute every external effect at most once and reconcile ledger state
with external truth before retry or replay.

### Failure Recovery and Fallback

Define fail-closed transitions, bounded retry, external-effect reconciliation,
recovery prerequisites, and an equal-or-lower-authority fallback.

When external truth is uncertain, set recoveryRequired and remain in recovery until
reconciliation proves the outcome. While recoveryRequired, late results, replay
events, and cancellation preserve authority, pending command and effect, checkpoint,
transition/tool/effect counts, effect ledger, and repair facts byte-identically and
emit no executor command.

Fallback never expands trust: it cannot widen context, provider, tool, effect,
retention, grant, or authority boundaries.

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
integration prerequisite as blocked with reason `production_skills_not_integrated`;
do not create a substitute.

Never invoke `codex exec`, `tests/e2e/codex_skill_forward_tests.py`, or a Claude/Codex
host matrix from inside this skill. Existing normalized host evidence may be
inspected, but missing outer-harness evidence is `blocked`.
