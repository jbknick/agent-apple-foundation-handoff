---
name: validate-apple-foundation-models-handoff
description: Validate an Apple Foundation Models handoff artifact when the user requests reproducible proof, a complete pass/fail/blocked/not_applicable matrix, cross-host comparison, or release implication rather than design, edits, findings-only review, or diagnosis.
---

# Validate Apple Foundation Models Handoff

## Routing and Inspection

Normalize these router inputs in order:

domain = foundation_models_handoff | out_of_domain | ambiguous
requestedOperation = design | implement | review | debug | validate | compound_review_fix | unspecified
artifactState = absent | proposal | approved_contract | implementation | evidence_bundle | unknown
evidenceState = not_requested | missing | available | failing | blocked | unknown

Classify the domain before selecting work. Activate validation only for reproducible
proof, a complete evidence matrix, cross-host comparison, or release implication.
Keep design, editing, findings-only review, and diagnosis outside this proof boundary.

Choose exactly one primary workflow. Ask exactly one targeted clarification when the
domain is ambiguous. For compound review and fix, run review first and name a
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
selectedSkill = validate-apple-foundation-models-handoff
routerInput = { domain, requestedOperation, artifactState, evidenceState }
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
  limitations[]: <limitations and blockers>
```

### Activation and Scope

Use the complete positive contract for every activated validation, including a short
answer. Serialize `selectedSkill` as the literal assignment
`selectedSkill = validate-apple-foundation-models-handoff`. Serialize all four
populated `routerInput` values on exactly one physical line, with `architectureResult`
on the immediately following line. Emit exactly one response-level fenced `text`
block, reserve it for the result envelope, and emit no additional fenced `text`
blocks. After the envelope, render only the exact required headings, each exactly once
and in the listed order. Populate every nested field, including the architecture
result wrapper and verification; do not replace that shape with YAML, JSON, or prose
alone. Use only the four pattern enum values shown above. Render source and destination
as objects containing profile and provider. Report real independent state and policy
version labels; when a version cannot be established, report an explicit blocker
rather than a prose placeholder.

Pin the artifact or commit identity, required gate catalog, oracles, commands, hosts,
evidence policy, and release boundary. State every unavailable prerequisite.
Keep validation read-only and state explicitly that no subject edit was made. Set
`PYTHONDONTWRITEBYTECODE=1` for Python checks and verify the worktree before making
that statement.

### Pattern and Ownership

Read the claimed pattern, source, destination, trigger, current owner, next owner, and
final response owner as proof inputs. Do not redesign them during validation.

Maintain exactly one stable owner at every state; only that owner authorizes the next
transition, and model output, provider output, and tools never become the owner.

### Apple API Availability

Compile or inspect each in-scope Apple surface on the named local boundary. Separate
supported execution, interface-only evidence, local unavailability, and unsupported
claims.

versionLabel = compiled_sdk_26_5 | interface_verified_sdk_26_5 | official_os_xcode_27_beta_locally_unverified | pseudocode_deterministic_mock | blocked

Record stable SDK 26.5 compile and interface errors separately from locally
unverified OS/Xcode 27 beta errors.

### State and Lifecycle

Execute state-schema, transition, termination, cancellation, retry, idempotency,
reconciliation, repair, and independent version-compatibility checks.

For every allowed edge, define finite transition, tool-call, and external-effect
budgets. Validate the event, source phase, allowed edge, grant, stateVersion, and
policyVersion before mutating any budget. Persist the checkpoint before setting the
phase to transitioning; only then may the reducer emit at most one executor command.

Treat stateVersion and policyVersion as independent values, each with its own
compatibility and migration rule. Terminate only from a stable phase with no
unresolved pending command, pending effect, or recovery requirement.

### Trust and Model Boundaries

Execute assertions for provider, session, profile, process, external-service, grant,
and fail-closed transfer boundaries without widening test authority.

Classify every context field atomically as C0, C1, C2, or C3 before transfer; reject
the whole envelope when any field is unknown or disallowed.

Bind every grant to person, session, source profile, source provider, destination
profile, destination provider, purpose, exact context classes, exact fields, tools,
retention, expiry, C2 permission, stateVersion, and policyVersion. Invalidate and
revalidate the grant before use whenever any binding drifts.

### Context Policy

Validate classification, minimization, redaction, retention, provenance, destination
revalidation, and separation of control-plane state from model context.

### Tools Effects and Confirmation

Validate tool and result provenance, confirmation, stable effect identity,
at-most-once execution, reconciliation, and authority for external effects.

Accept a tool result only when its call ID, tool ID, tool version, provider, result
type, and current state match the pending invocation; otherwise reject it.

Require confirmation plus an application-controlled effect ID and application-owned
effect ledger; execute every external effect at most once and reconcile ledger state
with external truth before retry or replay.

### Failure Recovery and Fallback

Validate bounded retries, recovery states, reconciliation before replay, blocker
classification, and equal-or-lower-authority fallback.

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
Record one outcome and bounded evidence reference for every required row. Keep host
outcomes separate. For a zero denominator, emit status not_applicable and value null.

### Limitations

List missing tools, SDKs, binaries, hardware, credentials, host automation, human
scores, unsupported APIs, excluded raw evidence, and every unresolved blocker.

### Layer Matrix

Report deterministic, compilation, schema, generation, evidence, rubric-integrity,
and eligible host rows with their exact status and required prerequisite.

### Counts and Hashes

Report executed, passing, failing, blocked, and not-applicable counts plus approved
artifact, fixture, prompt, rubric, and evidence hashes where the contract requires.
If an identity or hash cannot be reproduced, name its prerequisite and mark it blocked
instead of omitting or inventing it.

### Rubric Result

Validate rubric structure, arithmetic, dimensions, thresholds, and human-reviewer
identity when supplied. Never invent semantic scores or a reviewer verdict.

### Blockers and Skips

Name every unavailable prerequisite and affected row. Preserve failures. Treat a
valid non-applicable calculation separately from a missing prerequisite.

### Release Implication

Derive the release result from the complete matrix and governing policy. One passing
layer or host never substitutes for a failing, blocked, or unexecuted required row.

## References

- [Architecture and state](../../references/architecture-and-state.md) — result schema, ownership, lifecycle, and deterministic state checks.
- [Orchestration patterns](../../references/orchestration-patterns.md) — route, topology, trigger, and owner checks.
- [Apple API availability](../../references/apple-api-availability.md) — compile boundaries, version labels, and blocker classification.
- [Security, context, and recovery](../../references/security-context-and-recovery.md) — adversarial trust, grant, effect, recovery, and fallback assertions.
- [Evaluation and observability](../../references/evaluation-and-observability.md) — gate catalog, hashes, rubric, host matrix, and safe evidence.

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

Non-positive results contain no architectureResult, workflow-specific sections,
references, fabricated Apple claims, or host activation evidence.
