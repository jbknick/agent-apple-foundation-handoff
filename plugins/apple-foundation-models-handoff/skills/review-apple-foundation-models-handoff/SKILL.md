---
name: review-apple-foundation-models-handoff
description: Review an existing Apple Foundation Models handoff artifact when the user wants severity-ranked findings about architecture, Apple API grounding, state, security, recovery, or evidence claims rather than changes.
---

# Review Apple Foundation Models Handoff

## Routing and Inspection

Normalize these router inputs in order:

domain = foundation_models_handoff | out_of_domain | ambiguous
requestedOperation = design | implement | review | debug | validate | compound_review_fix | unspecified
artifactState = absent | proposal | approved_contract | implementation | evidence_bundle | unknown
evidenceState = not_requested | missing | available | failing | blocked | unknown

Activate review for an existing proposal,
implementation, fixture, or evidence bundle when the requested result is findings
rather than changes, diagnosis, or proof execution.

Classify supplied or described reducer code and reducer behavior as an implementation,
not a proposal.

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
selectedSkill = review-apple-foundation-models-handoff
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
`selectedSkill = review-apple-foundation-models-handoff`. Serialize all four populated
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
placeholder in the shown shape; do not replace that shape with YAML or JSON. Use only
the four pattern enum values shown above. Render source and destination as objects
containing profile and provider. Report real independent state and policy version
labels; when either is unavailable, record the blocker rather than a placeholder
value.

Freeze the artifact and review boundary. State reconstructable intent, inspected
paths, available evidence, claimed toolchain or host boundaries, and exclusions.
Keep inspection read-only, set `PYTHONDONTWRITEBYTECODE=1` for Python checks, and
verify the worktree before claiming no edits.

### Pattern and Ownership

Reconstruct the claimed pattern, source, destination, trigger, current owner, next
owner, and final response owner. Compare the artifact with that ownership contract.

Maintain exactly one stable owner at every state; only that owner authorizes the next
transition, and model output, provider output, and tools never become the owner.

### Apple API Availability

Check every Apple API claim against installed interfaces and authoritative sources.
Separate locally verified facts, unverified declarations, pseudocode, and unsupported
surfaces.

versionLabel = compiled_sdk_26_5 | interface_verified_sdk_26_5 | official_os_xcode_27_beta_locally_unverified | pseudocode_deterministic_mock | blocked

Record stable SDK 26.5 compile and interface errors separately from locally
unverified OS/Xcode 27 beta errors.

### State and Lifecycle

Inspect reducer authority, valid transitions, version compatibility, termination,
cancellation, retry budgets, idempotency, reconciliation, and repair behavior.

For every allowed edge, define finite transition, tool-call, and external-effect
budgets. Validate the event, source phase, allowed edge, grant, stateVersion, and
policyVersion before mutating any budget. Persist the checkpoint before setting the
phase to transitioning; only then may the reducer emit at most one executor command.

Treat stateVersion and policyVersion as independent values, each with its own
compatibility and migration rule. Terminate only from a stable phase with no
unresolved pending command, pending effect, or recovery requirement.

### Trust and Model Boundaries

Inspect provider, session, profile, process, and external-service boundaries. Verify
grants do not inherit authority or trust properties across those boundaries.

Classify every context field atomically as C0, C1, C2, or C3 before transfer; reject
the whole envelope when any field is unknown or disallowed.

Bind every grant to person, session, source profile, source provider, destination
profile, destination provider, purpose, exact context classes, exact fields, tools,
retention, expiry, C2 permission, stateVersion, and policyVersion. Invalidate and
revalidate the grant before use whenever any binding drifts.

### Context Policy

Check classification, minimization, redaction, retention, provenance, destination
revalidation, and separation of control-plane state from model context.

### Tools Effects and Confirmation

Check tool provenance, confirmation, stable effect identity, result provenance,
at-most-once execution, and authority for each possible external effect.

Accept a tool result only when its call ID, tool ID, tool version, provider, result
type, and current state match the pending invocation; otherwise reject it.

Require confirmation plus an application-controlled effect ID and application-owned
effect ledger; execute every external effect at most once and reconcile ledger state
with external truth before retry or replay.

### Failure Recovery and Fallback

Check fail-closed behavior, bounded retries, reconciliation before replay, recovery
states, and equal-or-lower-authority fallback.

When external truth is uncertain, set recoveryRequired and remain in recovery until
reconciliation proves the outcome. While recoveryRequired, late results, replay
events, and cancellation preserve authority, pending command and effect, checkpoint,
transition/tool/effect counts, effect ledger, and repair facts byte-identically and
emit no executor command.

Fallback never expands trust: it cannot widen context, provider, tool, effect,
retention, grant, or authority boundaries.

### Verification and Evidence

status = pass | fail | blocked | not_applicable

Link each finding to exact artifact evidence and a stable check identifier. A zero
denominator produces not_applicable with a null value.

### Limitations

List unavailable artifacts, incomplete intent, unverified APIs, absent host proof,
evidence gaps, residual risks, and every conclusion constrained by missing facts.

### Findings

Return findings first, ordered by severity. For each proven finding include a stable
check ID, exact evidence location, violated contract, impact, and smallest bounded
correction. State explicitly when no finding is proven. Do not edit the artifact.

## References

- [Architecture and state](../../references/architecture-and-state.md) — result schema, ownership, lifecycle, and transitions.
- [Orchestration patterns](../../references/orchestration-patterns.md) — topology, history, triggers, and final-owner selection.
- [Apple API availability](../../references/apple-api-availability.md) — installed interfaces, version labels, and claim boundaries.
- [Security, context, and recovery](../../references/security-context-and-recovery.md) — trust, grants, effects, recovery, and fallback findings.
- [Evaluation and observability](../../references/evaluation-and-observability.md) — check identities, safe evidence, and host semantics.

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
