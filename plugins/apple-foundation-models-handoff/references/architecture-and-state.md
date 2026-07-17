# Architecture and State Contract

## Scope and authority

This reference is the sole owner of the provider-neutral handoff result schema,
state, ownership, lifecycle, transition, termination, cancellation, retry,
checkpoint, ledger, and repair contracts. These are mandatory application
architecture decisions, not guarantees supplied by Apple frameworks. Exact
framework declarations and availability remain in [Apple API availability](apple-api-availability.md).

The schema identifier is `architectureSchemaVersion: "1.0"`. A consumer must
reject a result with an unknown major schema version rather than guessing how
ownership or recovery works.

## Common result schema

Every positive result contains exactly one common domain plus the addition
owned by the operation:

| Result domain | Required purpose |
| --- | --- |
| `architectureResult` | Selected topology, state contract, ownership decision, alternatives, rationale, components, and proof plan |
| `implementationResult` | Approved-contract identity, bounded changes, tests, and observed results |
| `reviewResult` | Findings, evidence locations, residual risks, and no mutation claim |
| `debugResult` | Reproduction, root cause, affected invariant, correction boundary, and regression proof |
| `validationResult` | Deterministic gates, host rows, blockers, rubric result, and limitations |

All positive domains carry `architectureSchemaVersion`, `stateVersion`,
`policyVersion`, source and destination identities, final-response owner,
current phase, evidence status, blockers, assumptions, and limitations.
Workflow-specific additions are named here only; their activation and prose
belong to the production skill entrypoints.

Non-positive results are bounded to either `not_applicable` with the normalized
requested domain/operation or `clarification_required` with one missing input
and one question. They contain no fabricated architecture or Apple claim.

## Ownership and state fields

`stateVersion` and `policyVersion` change independently: the first is the
monotonic concurrency/state revision, while the second identifies the boundary
policy applied to a proposal. A policy change never masquerades as a state
transition.

| Field | Contract |
| --- | --- |
| `stateVersion` | Increment only after an accepted state transition; compare before every command or commit acknowledgement |
| `policyVersion` | Revalidate before execution and after confirmation; advance independently when authorization policy changes |
| `phase` | Exactly one of `stable`, `transitioning`, `recoveryRequired`, or `terminated` |
| `activeProfile` / `provider` | Current application-selected execution identity; never inferred from a model sentence |
| `source` / `destination` | Explicit identities for a proposed transfer or consultation |
| `finalResponseOwner` | The component permitted to return the user-facing result |
| `allowedEdges` | Policy-approved source/destination transitions |
| transition/tool/effect counts and budgets | Monotonic bounded counters checked only after phase and version checks |
| classified context envelope / provider grant | Authorized fields, purpose, tools, recipient, retention, expiry, person, and versions |
| pending transition / stable checkpoint | Complete repair input retained until success or known rollback |
| effect ledger | One application identity for each possible or confirmed external commit |
| metadata-only audit events | Normalized IDs, versions, states, hashes, counts, and reasons; no sensitive content |

The source owns authority until the transition commits. Baton-pass transfers
`finalResponseOwner` to the destination only on a committed activation.
Consultation, routing, and transcript mechanics use the ownership rules in
[orchestration patterns](orchestration-patterns.md).

## Lifecycle transition table

Phase validation precedes versions, edge, budgets, grant, context, tools, and
effect checks. Ordinary budget or no-safe-path termination is permitted only
from `stable`; this is the stable-only ordinary termination rule.

| Current phase | Trusted event | Required result |
| --- | --- | --- |
| `stable` | valid proposal | Validate phase first, versions, edge, budgets, grant, and context; checkpoint; enter `transitioning`; emit at most one command. |
| `transitioning` | commit before uncertainty | Activate destination; transfer final owner only for baton-pass; increment only `stateVersion`; return `stable`. |
| `transitioning` | known pre-commit failure/cancellation | Restore checkpoint and source authority; clear pending state; return `stable`. |
| `transitioning` | possible external commit/uncertain cancellation | Retain repair facts and one effect identity; enter `recoveryRequired`. |
| `recoveryRequired` | explicit successful reconciliation | Establish external truth, resolve the ledger, then produce one valid stable state. |
| `recoveryRequired` | late/replayed event or unavailable repair | Preserve authority, phase, pending/checkpoint state, counts, ledger, and repair facts; emit no command. |
| `stable` | budget exhaustion/no safe path | Terminate or return explicit unavailable/degraded output without expanding trust. |

Code status: `pseudocode`
```swift
switch (state.phase, event) {
case (.stable, .validProposal(let proposal)):
    return checkpointAndBegin(proposal)
case (.recoveryRequired, .replayed):
    return unchanged(command: nil)
case (.recoveryRequired, .reconciled(let truth)):
    return resolve(truth)
default:
    return unchanged(command: nil)
}
```

This reducer sketch is application pseudocode. It deliberately omits framework
types and executable scenario implementation.

## Termination and fallback boundary

The reducer checks phase before any budget rule. `transitioning` never becomes
`terminated` merely because a counter is exhausted: a known pre-commit outcome
rolls back, while uncertain external truth enters `recoveryRequired`.

From `stable`, a budget failure or missing safe route returns one of:

- a terminal result that preserves the last trusted authority and reason;
- a degraded, local-only route that satisfies the same policy; or
- an explicit unavailable result with no widened context, provider, tool, or
  effect permission.

Fallback is a new policy decision. It cannot silently change recipient,
provider, final owner, context class, or effect scope.

## Recovery and replay checklist

- Retain source/destination, final owner, both versions, pending proposal,
  stable checkpoint, counts, effect identity, and repair reason while truth is
  uncertain.
- Query an authoritative provider or effect system by the same application
  identity; do not infer commit from timeout, cancellation, or model text.
- Leave `recoveryRequired` only after explicit successful reconciliation
  establishes external truth.
- Apply a late or replayed event to the current versions and ledger. A stale
  event returns unchanged state and no command.
- Permit retry only after reconciliation proves the earlier effect did not
  commit or the existing committed result has been adopted.
- Emit metadata-only repair evidence and keep context/tool payloads outside the
  durable record.

The detailed trust, grant, effect, and fallback controls are owned by
[security, context, and recovery](security-context-and-recovery.md). Evidence
states and acceptance IDs are owned by
[evaluation and observability](evaluation-and-observability.md).

## Related references

- [Orchestration patterns](orchestration-patterns.md) selects topology,
  history visibility, control, and final owner.
- [Apple API availability](apple-api-availability.md) owns exact declarations,
  errors, availability, and SDK labels.
- [Security, context, and recovery](security-context-and-recovery.md) owns
  trust classes, grants, effects, recovery, and fallback policy.
- [Evaluation and observability](evaluation-and-observability.md) owns stable
  evidence IDs, rubric semantics, host states, and safe committed evidence.

## Source ledger

| Source | Retrieved | Boundary |
| --- | --- | --- |
| [LanguageModelSession](https://developer.apple.com/documentation/foundationmodels/languagemodelsession) | 2026-07-17 | Official session/transcript context only; it does not define this application reducer |
| [Build agentic app experiences](https://developer.apple.com/videos/play/wwdc2026/242/) | 2026-07-17 | Official pattern context; application authorization and recovery remain local policy |

## Limitations

This document does not claim a framework-owned reducer, authorization grant,
effect ledger, transition transaction, or repair protocol. It does not prove a
provider call or external side effect. Exact API and host evidence must be read
from their concern owners before implementation or validation.
