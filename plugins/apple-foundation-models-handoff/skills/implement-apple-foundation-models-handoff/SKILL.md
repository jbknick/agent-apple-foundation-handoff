---
name: implement-apple-foundation-models-handoff
description: Implement an Apple Foundation Models handoff architecture when an approved architecture or decision reference and an exact application change boundary already exist.
---

# Implement Apple Foundation Models Handoff

## Routing and Inspection

Normalize these router inputs in order:

domain = foundation_models_handoff | out_of_domain | ambiguous
requestedOperation = design | implement | review | debug | validate | compound_review_fix | unspecified
artifactState = absent | proposal | approved_contract | implementation | evidence_bundle | unknown
evidenceState = not_requested | missing | available | failing | blocked | unknown

Classify the domain before selecting work. Activate implementation only when an
approved architecture or decision reference and an exact application change boundary
already exist.

Choose exactly one primary workflow. Ask exactly one targeted clarification when the
domain or approved contract is missing. For compound review and fix, run review first
and name a separate authorized follow-on boundary. Do not invoke another skill.

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
replace that shape with YAML or JSON. Then render every common and
implementation-specific heading below verbatim and in order; do not rename, merge, or
omit a heading. Use only the four pattern enum values shown above. Render source and
destination as objects containing profile and provider. Report real independent state
and policy version labels; when either is unavailable, record the blocker rather than
a placeholder value.

State the approved authority, exact application boundary, inspected repository state,
target toolchain, and excluded changes. Stop for one bounded clarification if either
authority input is missing.

For report-only work, keep inspection read-only, set `PYTHONDONTWRITEBYTECODE=1` for
Python checks, and verify the worktree before claiming no edits.

### Pattern and Ownership

Preserve the approved topology, source, destination, trigger, current owner, next
owner, and final response owner. Map every code change back to that contract.

### Apple API Availability

Verify each used Apple surface against installed interfaces before coding. Record its
source, version label, local compilation state, and any unsupported boundary.

### State and Lifecycle

Implement only approved state fields, transitions, budgets, termination,
cancellation, retry, idempotency, reconciliation, and migration behavior.

### Trust and Model Boundaries

Preserve each provider, session, profile, process, and external-service boundary.
Require the approved grant before transferring control, context, tools, or effects.

### Context Policy

Transfer only the approved minimum context. Keep control-plane state separate and
retain required redaction, provenance, retention, and destination revalidation.

### Tools Effects and Confirmation

Preserve tool provenance, confirmation timing, stable effect identity, result
provenance, and at-most-once effect authority in code and tests.

### Failure Recovery and Fallback

Implement fail-closed transitions, bounded retries, reconciliation before replay, and
only the approved equal-or-lower-authority fallback.

### Verification and Evidence

status = pass | fail | blocked | not_applicable

Run the contract's deterministic, compile, regression, schema, generation, evidence,
and applicable host gates. A zero denominator produces not_applicable with a null
value.

### Limitations

List unsupported APIs, uncompiled paths, missing prerequisites, failing gates,
residual risk, and every requested change left outside the approved boundary.

### Approved Decision

Identify the immutable decision reference and map its selected pattern, state,
security, recovery, and proof requirements to the implementation.

### Change Boundary

State the exact allowed paths and behaviors. Reject redesign, broad refactoring,
dependency additions, or unrelated cleanup that lacks separate authority.

### Changed Paths

List each changed application or test path and the approved contract requirement it
implements. Include no path that cannot be traced to the boundary.

### Compilation and Regression Results

Report exact executed checks and outcomes. Preserve failures and blockers; never
weaken a test, oracle, or expected behavior to obtain a pass.

## References

- [Architecture and state](../../references/architecture-and-state.md) — result schema, ownership, lifecycle, and transitions.
- [Orchestration patterns](../../references/orchestration-patterns.md) — approved topology, history, triggers, and final-owner selection.
- [Apple API availability](../../references/apple-api-availability.md) — installed interfaces, version labels, and unsupported boundaries.
- [Security, context, and recovery](../../references/security-context-and-recovery.md) — trust, grants, effects, recovery, and fallback.
- [Evaluation and observability](../../references/evaluation-and-observability.md) — deterministic, compile, regression, and host evidence.

## Guardrails

Ground Apple claims in official Apple documentation, installed SDK interfaces, WWDC,
and Apple-owned repositories. Use compiled_sdk_26_5 and
interface_verified_sdk_26_5 only for their proven local evidence boundaries.
Compile-check Swift examples where supported; otherwise label pseudocode and
unsupported APIs. A missing SDK, host, toolchain, binary, hardware, or prerequisite
is blocked, never a pass. If a fixed reference target is absent, report
`production_skills_not_integrated` as the blocked DEV-137 integration reason; do not
create a substitute.

Non-positive results contain no architectureResult, workflow-specific sections,
references, fabricated Apple claims, or host activation evidence.
