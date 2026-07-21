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

Every positive result has exactly this normalized outer envelope:

```text
activationStatus = activated
selectedSkill
preselectionInput = { domain, requestedOperation, artifactState, evidenceState }
architectureResult
```

`architectureResult` contains the complete common contract:

```text
architectureSchemaVersion: "1.0"
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

The workflow-specific sections are additive inside `architectureResult`; they
never replace it or create another outer result domain:

| Workflow | Additive sections |
| --- | --- |
| Design | Alternatives; Decision Rationale; Proposed Components; Implementation and Test Plan |
| Implement | Approved Decision; Change Boundary; Changed Paths; Compilation and Regression Results |
| Review | Findings ranked by severity with stable check ID, exact evidence, impact, and bounded correction |
| Debug | Observed and Expected State; First Divergence; Root Cause; Correction; Regression Proof |
| Validate | Layer Matrix; Counts and Hashes; Rubric Result; Blockers and Skips; Release Implication |

All positive results carry `architectureSchemaVersion`, `stateVersion`,
`policyVersion`, source and destination identities, final-response owner,
current phase, evidence status, blockers, assumptions, and limitations.

Positive requests bypass the bounded non-positive router and select exactly one
of the five workflows directly. The router loads no reference, is not a sixth
workflow, and is distinct from the DEV-142 through DEV-145 cost router documented
by [orchestration patterns](orchestration-patterns.md).

Out-of-domain rejection contains exactly:

```text
activationStatus = no_activation
reasonCode = out_of_domain
domain
requestedOperation
```

Bounded clarification contains exactly:

```text
activationStatus = clarification_required
clarificationKind = domain | approved_contract
missingInput
question
```

Neither non-positive shape contains `architectureResult`, loaded references,
fabricated architecture or Apple claims, tools, effects, commands, agents,
hooks, MCP, apps, scripts, dependencies, runtime, or cost-routing work.

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
| classified context envelope / provider grant | Grant identity and validation status; the complete binding fields are owned only by [security, context, and recovery](security-context-and-recovery.md) |
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

Code status: `pseudocode_deterministic_mock`
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
- Permit retry only after reconciliation confirms the earlier effect is absent.
  A confirmed committed result is adopted and is never retried.
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
