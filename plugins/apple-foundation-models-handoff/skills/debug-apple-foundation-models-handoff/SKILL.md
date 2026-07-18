---
name: debug-apple-foundation-models-handoff
description: Debug an Apple Foundation Models handoff when an observed routing, ownership, transition, context, tool, effect, recovery, fallback, availability, or version-labelled behavior differs from its expected contract and the cause is not yet established.
---

# Debug Apple Foundation Models Handoff

## Routing and Inspection

Normalize these router inputs in order:

domain = foundation_models_handoff | out_of_domain | ambiguous
requestedOperation = design | implement | review | debug | validate | compound_review_fix | unspecified
artifactState = absent | proposal | approved_contract | implementation | evidence_bundle | unknown
evidenceState = not_requested | missing | available | failing | blocked | unknown

Activate debug only for an observed
Foundation Models handoff divergence whose cause is not established. Require an
expected contract and reproducible boundary or classify the missing evidence.

Choose exactly one primary workflow. For compound review and fix, run review first
and name a separate authorized follow-on boundary. Do not invoke another skill.

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
selectedSkill = debug-apple-foundation-models-handoff
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

Use the complete positive contract for every activated diagnosis, including a short
answer. Serialize `selectedSkill` as the literal assignment
`selectedSkill = debug-apple-foundation-models-handoff`. Serialize all four populated
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
placeholder in the shown shape; do not replace that shape with YAML, JSON, or prose
alone. Use only the four pattern enum values shown above. Render source and destination
as objects containing profile and provider. Report real independent state and policy
version labels; use an explicit unknown with evidence when a version cannot be
established, never a prose placeholder.

State the observed divergence, expected contract, reproducible boundary, inspected
artifact, available evidence, allowed correction scope, and unavailable prerequisites.
Keep diagnosis read-only unless correction is explicitly authorized. State whether
any edit occurred, set `PYTHONDONTWRITEBYTECODE=1` for Python checks, and verify the
worktree before claiming no edits.

### Pattern and Ownership

Reconstruct the selected pattern, route, trigger, source, destination, current owner,
next owner, and final response owner at the divergence boundary.

Maintain exactly one stable owner at every state; only that owner authorizes the next
transition, and model output, provider output, and tools never become the owner.

### Apple API Availability

Compare claimed and installed Apple surfaces, version labels, compilation state, and
error boundaries. Keep unsupported or locally unverified claims distinct.

versionLabel = compiled_sdk_26_5 | interface_verified_sdk_26_5 | official_os_xcode_27_beta_locally_unverified | pseudocode_deterministic_mock | blocked

Record stable SDK 26.5 compile and interface errors separately from locally
unverified OS/Xcode 27 beta errors.

### State and Lifecycle

Trace versioned reducer state and events to the first invalid edge. Check budgets,
termination, cancellation, replay, idempotency, reconciliation, and repair facts.

For every allowed edge, define finite transition, tool-call, and external-effect
budgets. Validate the event, source phase, allowed edge, grant, stateVersion, and
policyVersion before mutating any budget. Persist the checkpoint before setting the
phase to transitioning; only then may the reducer emit at most one executor command.

Treat stateVersion and policyVersion as independent values, each with its own
compatibility and migration rule. Terminate only from a stable phase with no
unresolved pending command, pending effect, or recovery requirement.

### Trust and Model Boundaries

Test provider, session, profile, process, and external-service hypotheses without
allowing authority or trust properties to cross an unproven boundary.

Classify every context field atomically as C0, C1, C2, or C3 before transfer; reject
the whole envelope when any field is unknown or disallowed.

Bind every grant to person, session, source profile, source provider, destination
profile, destination provider, purpose, exact context classes, exact fields, tools,
retention, expiry, C2 permission, stateVersion, and policyVersion. Invalidate and
revalidate the grant before use whenever any binding drifts.

### Context Policy

Compare expected and observed classification, minimization, redaction, retention,
provenance, destination revalidation, and control-plane separation.

### Tools Effects and Confirmation

Trace tool and result provenance, confirmation, stable effect identity, external
truth, at-most-once behavior, and authority at the first divergent event.

Accept a tool result only when its call ID, tool ID, tool version, provider, result
type, and current state match the pending invocation; otherwise reject it.

Require confirmation plus an application-controlled effect ID and application-owned
effect ledger; execute every external effect at most once and reconcile ledger state
with external truth before retry or replay.

### Failure Recovery and Fallback

Keep uncertain external truth in recovery until reconciled. Do not retry or fall back
through a broader context, provider, tool, effect, or retention boundary.

When external truth is uncertain, set recoveryRequired and remain in recovery until
reconciliation proves the outcome. While recoveryRequired, late results, replay
events, and cancellation preserve authority, pending command and effect, checkpoint,
transition/tool/effect counts, effect ledger, and repair facts byte-identically and
emit no executor command.

Fallback never expands trust: it cannot widen context, provider, tool, effect,
retention, grant, or authority boundaries.

### Verification and Evidence

status = pass | fail | blocked | not_applicable

State this complete allowed status vocabulary exactly, even when a status has no row.
Bind each hypothesis to a reproducible check and record the first discriminating
result. A zero denominator produces not_applicable with a null value.

### Limitations

List unreproduced paths, unavailable evidence, unverified APIs, sensitive data kept
out of diagnostics, residual hypotheses, blockers, and host-specific limits.

### Observed and Expected State

Normalize the expected state and the observed state at the same event boundary,
including owner, phase, pending effect, budgets, versions, and evidence identity.

### First Divergence

Name the earliest event where observed state, authority, context, effect, recovery,
fallback, or API behavior stops satisfying the expected contract.

### Root Cause

Select one evidence-backed causal mechanism. Keep correlation, inference, unknowns,
and downstream symptoms separate from the proven cause.

### Correction

Specify the smallest root-cause correction. Apply it only when explicitly requested
and authorized; return broader work as a separate design or implementation boundary.

### Regression Proof

Define the failing reproduction, corrected expectation, deterministic regression,
compile boundary, and any blocked host proof needed to prevent recurrence.

## References

- [Architecture and state](../../references/architecture-and-state.md) — result schema, event state, ownership, lifecycle, and repair.
- [Orchestration patterns](../../references/orchestration-patterns.md) — route, topology, history, triggers, and owner failures.
- [Apple API availability](../../references/apple-api-availability.md) — installed interfaces, version labels, and availability failures.
- [Security, context, and recovery](../../references/security-context-and-recovery.md) — trust, grants, effects, replay, recovery, and fallback.
- [Evaluation and observability](../../references/evaluation-and-observability.md) — safe reproduction, check identities, and host evidence.

## Guardrails

Ground Apple claims in official Apple documentation, installed SDK interfaces, WWDC,
and Apple-owned repositories. Use compiled_sdk_26_5 and
interface_verified_sdk_26_5 only for their proven local evidence boundaries.
Compile-check Swift examples where supported; otherwise label pseudocode and
unsupported APIs. A missing SDK, host, toolchain, binary, hardware, or prerequisite
is blocked, never a pass. If a fixed reference target is absent, report
`production_skills_not_integrated` as the blocked DEV-137 integration reason; do not
create a substitute.

Never invoke `codex exec`, `tests/e2e/codex_skill_forward_tests.py`, or a Claude/Codex
host matrix from inside this skill. Existing normalized host evidence may be
inspected, but missing outer-harness evidence is `blocked`.
