# Apple Foundation Models Handoff Skill Contract

## Contract authority

This is a compact, non-authoritative downstream index. The
[canonical DEV-134 design](../superpowers/specs/2026-07-17-dev-134-agent-skill-catalog-design.md)
controls detailed semantics and rationale. DEV-134 comments
`3213d6cd-2fae-4168-aeeb-5a124f9af937` and
`5d3d7021-a125-4e08-9d58-d8797b36af09` govern the amended preselection
contract; `ceceacdc-ad41-4f11-94a2-beca1026e369` keeps cost routing separate.
The original decision `e90f2a39-d887-48b6-a8ce-17a2fa56e0a3` remains
historical context. A conflict must be resolved in those authorities and
propagated before this index changes.

The plugin supplies guidance and proof contracts. The application remains the
authority for reducer state, authorization, tool/effect execution, external
truth, recovery, and fallback.

Canonical shared metadata remains authored from Claude-side inputs. Any Codex
artifacts are generated or regenerated from those inputs and are never
hand-edited. DEV-134 creates neither the metadata inputs nor generated
artifacts.

## Positive preselection and bounded non-positive router

Normalize these preselection fields:

```text
domain = foundation_models_handoff | out_of_domain | ambiguous
requestedOperation = design | implement | review | debug | validate | compound_review_fix | unspecified
artifactState = absent | proposal | approved_contract | implementation | evidence_bundle | unknown
evidenceState = not_requested | missing | available | failing | blocked | unknown
```

An in-domain positive request bypasses the non-positive router and directly
activates exactly one workflow from the explicit operation, artifact state, and
evidence state. Compound review-and-fix activates review first. Implementation
requires an approved contract and exact change boundary; without them the
request is not positive.

The bounded non-positive router owns only out-of-domain rejection, ambiguous
domain clarification, and missing-approved-contract clarification. It returns
only `no_activation` or `clarification_required`. It is not a sixth workflow
and may not select or invoke a workflow, load a reference, emit
`architectureResult`, or use tools, effects, commands, agents, hooks, MCP,
apps, scripts, dependencies, or runtime. It makes no Apple or host-capability
claim. The DEV-142 through DEV-145 cost router, `PostToolUse` hook, and Swift
bridge chain are separate later runtime and are not implemented here.

## Exact catalog

| Exact skill | Sole workflow ownership |
| --- | --- |
| `design-apple-foundation-models-handoff` | New or materially revised architecture, topology, pattern, state, or trust-boundary decision |
| `implement-apple-foundation-models-handoff` | Bounded application changes and tests tied to an approved architecture |
| `review-apple-foundation-models-handoff` | Findings-only contract, Apple API, state, security, recovery, and evidence inspection |
| `debug-apple-foundation-models-handoff` | First divergence, root cause, bounded correction, and regression proof for observed behavior |
| `validate-apple-foundation-models-handoff` | Deterministic, compile, schema, generation, evidence, rubric-integrity, and host matrices |

No skill invokes another skill. Compound review-and-fix stops after review and
records a separate authorized follow-on boundary.

## Common positive result

Every positive activation has exactly this outer envelope:

```text
activationStatus = activated
selectedSkill
preselectionInput = { domain, requestedOperation, artifactState, evidenceState }
architectureResult
```

Case-level `activationOwner = direct_workflow` and
`activationOwner = non_positive_router` values are prototype evidence metadata
used to prove preselection ownership. They are not emitted envelope fields.

`architectureResult` contains `architectureSchemaVersion: "1.0"` and all of:

```text
architectureSchemaVersion
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

Its human rendering contains Activation and Scope; Pattern and Ownership; Apple
API Availability; State and Lifecycle; Trust and Model Boundaries; Context
Policy; Tools Effects and Confirmation; Failure Recovery and Fallback;
Verification and Evidence; and Limitations. Status is exactly `pass`, `fail`,
`blocked`, or `not_applicable`; zero denominator is `not_applicable` with a
null value. Executed Apple claims use only `compiled_sdk_26_5` or
`interface_verified_sdk_26_5`; distinct non-executed states are
`official_os_xcode_27_beta_locally_unverified`,
`pseudocode_deterministic_mock`, and `blocked`.

## Non-positive activation result

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

Neither shape contains `architectureResult`, workflow-specific sections,
loaded references, fabricated Apple claims, or production-host activation
evidence. The router performs no tools, effects, commands, agents, hooks, MCP,
apps, scripts, dependency, runtime, or cost-routing work.

## Skill contracts

Reference routes below use the concern aliases defined once in Reference
routing.

| Skill | Input gate | Direct concern routes | Output additions | Failure boundary |
| --- | --- | --- | --- | --- |
| `design-apple-foundation-models-handoff` | Confirmed handoff domain; scope, source/destination roles and providers, ownership goal, repository context, context/effect classes, and evidence/toolchain state | `state`, `patterns`, `apple-availability`, `security-recovery`, `evaluation` | Alternatives; Decision Rationale; Proposed Components; Implementation and Test Plan | Clarify ambiguous domain; make missing proof blocked; never invent Apple types, grants, or runtime behavior; an explicit no-handoff decision may select routing or transcript transfer |
| `implement-apple-foundation-models-handoff` | Immutable approved-decision reference, exact change boundary, repository state, target/toolchain, API labels, and required gates | `state`; `patterns` for approved topology; `apple-availability` for compiled interfaces; `security-recovery`; `evaluation` | Approved Decision; Change Boundary; Changed Paths; Compilation and Regression Results | Missing approval/boundary asks one approved-contract question; unsupported SDK/API is blocked; required failures remain fail; no redesign or scope widening |
| `review-apple-foundation-models-handoff` | Existing artifact plus intended or reconstructable contract, frozen review scope, available code/fixtures/evidence, and claimed SDK/host boundaries | `state`; `patterns` for topology/ownership; `apple-availability` for claims; `security-recovery`; `evaluation` | Findings ranked by severity with stable check ID, exact evidence, impact, and bounded correction | Missing artifact/evidence is blocked; do not fabricate findings; do not edit; compound work names a separate follow-on boundary |
| `debug-apple-foundation-models-handoff` | Observed and expected behavior, reproducible boundary/evidence, normalized state/effect identities, artifact/toolchain context, and allowed correction scope | Always `state`, `security-recovery`, `evaluation`; `patterns` when route/owner is implicated; `apple-availability` when API/version is implicated | Observed and Expected State; First Divergence; Root Cause; Correction; Regression Proof | Missing reproduction/evidence is blocked; uncertain external truth stays `recoveryRequired`; no retry/fallback broadens authority; broader work becomes a separate boundary |
| `validate-apple-foundation-models-handoff` | Pinned artifact/commit, gate catalog, oracle, repository/toolchain/host prerequisites, evidence policy, and release-decision boundary | `state`; `patterns` for route/owner cases; `apple-availability`; `security-recovery`; `evaluation` | Layer Matrix; Counts and Hashes; Rubric Result; Blockers and Skips; Release Implication | Preserve failures and named blockers; use `not_applicable` only when valid; do not edit the subject, weaken an oracle, invent rubric scores, or substitute one host for another |

## Reference routing

Each alias has one physical owner. Consumer edges are direct from the selected
skill; a reference never invokes a skill.

| Concern alias | Sole physical owner | Sole concern | Direct consumer skills |
| --- | --- | --- | --- |
| `state` | `architecture-and-state.md` | `1.0` result schema; state, ownership, lifecycle, transition, termination, cancellation, retry, and repair | All five skills |
| `patterns` | `orchestration-patterns.md` | Baton-pass, isolated consultation, deterministic routing, transcript transfer, topology, history, trigger/control, and final-owner selection | Design always; implement/review/debug when topology or ownership applies; validate for route/owner cases |
| `apple-availability` | `apple-api-availability.md` | Installed SDK 26.5 compiled/interface surfaces; separately labelled OS/Xcode 27 beta declarations; full error signatures; cache, provider, and runtime Skills boundaries | Every skill that mentions or checks an Apple surface |
| `security-recovery` | `security-context-and-recovery.md` | Trust boundaries, C0-C3, provenance, grants, confirmation, result provenance, effects, recovery, fallback, trace safety, and residual risk | Every skill with a transfer, provider, tool, effect, recovery, fallback, or evidence-safety boundary |
| `evaluation` | `evaluation-and-observability.md` | D/E IDs, corpus/oracle, rubric, safe evidence, host matrix, zero denominator, Evaluations, Instruments, and blocker policy | Design specifies proof; implement records it; review audits it; debug reproduces it; validate owns the execution matrix |

## Activation prototype IDs

| Case IDs | Activation owner | Expected activation |
| --- | --- | --- |
| `DEV134-POS-001` | `direct_workflow` | `design-apple-foundation-models-handoff` |
| `DEV134-POS-002` | `direct_workflow` | `review-apple-foundation-models-handoff` |
| `DEV134-POS-003` | `direct_workflow` | `implement-apple-foundation-models-handoff` |
| `DEV134-POS-004` | `direct_workflow` | `debug-apple-foundation-models-handoff` |
| `DEV134-POS-005` | `direct_workflow` | `validate-apple-foundation-models-handoff` |
| `DEV134-POS-006` | `direct_workflow` | `design-apple-foundation-models-handoff` |
| `DEV134-NEG-001` | `non_positive_router` | `no_activation` |
| `DEV134-NEG-002` | `non_positive_router` | `no_activation` |
| `DEV134-NEG-003` | `non_positive_router` | `no_activation` |
| `DEV134-NEG-004` | `non_positive_router` | `no_activation` |
| `DEV134-NEG-005` | `non_positive_router` | `no_activation` |
| `DEV134-NEG-006` | `non_positive_router` | `no_activation` |
| `DEV134-AMB-001` | `non_positive_router` | `clarification_required` |
| `DEV134-AMB-002` | `non_positive_router` | `clarification_required` |
| `DEV134-AMB-003` | `direct_workflow` | `review-apple-foundation-models-handoff` |

These are `design_contract_prototype` consistency cases with identical
normalized Claude and Codex expectations. They do not establish a production
capability.

### Real-host blockers and nonclaims

| Host | Evidence ID | Status | Reason |
| --- | --- | --- | --- |
| Claude | `E-CLAUDE-ACTIVATE-001` | `blocked` | `production_skill_not_implemented` |
| Codex | `E-CODEX-ACTIVATE-001` | `blocked` | `production_skill_not_implemented` |

The `design_contract_prototype` consistency does not prove production activation,
skill loading, progressive reference loading, or host capability.
File existence, Markdown checks, schema validation, generation, plugin
discovery, installation, version output, and enabled state remain structural prerequisites only
and cannot turn either row into pass.

No claim is made for real Claude/Codex activation, production skill/reference
loading, Apple runtime enforcement, live model, PCC, provider execution, or
release readiness. A later host row must capture one approved executable,
classify an initial missing/non-runnable/wrong-version/invalid strict version as
`blocked`, classify post-capture resolution/version drift as `fail`, and commit
only normalized `<host-path>` identity, a strict exact version or `null`, stable
reason/status/exit-code fields, and no literal path, raw `PATH`, invalid version
output, or raw blocker diagnostic. Alternate executable observations are
diagnostic only and cannot substitute for the selected host row.

## Downstream handoff

| Issue | Required inheritance and owned work |
| --- | --- |
| DEV-135 | Scaffold exactly five positive names plus the bounded non-positive router, one corpus, and generated ownership; the router is not a sixth workflow; optional per-skill YAML is presentation-only and requires a demonstrated need; structural loading is not activation |
| DEV-136 | Author the five direct positive workflows and bounded non-positive router with these activation, ordered-workflow, common-result, output-addition, failure, and non-goal contracts; guidance is not runtime enforcement |
| DEV-137 | Author the five unchanged sole-owner references and direct routes; volatile Apple detail and exact error payload signatures stay with the Apple owner; fixture code is not capability content |
| DEV-138 | Map stable D identities plus adversarial state/security/recovery cases to deterministic offline fixtures and exact repeated output; preserve oracle separation and safe synthetic evidence |
| DEV-139 | Turn all 15 identities and the two canonical walkthroughs into fresh per-host activation/reference/output/rejection evidence; preserve payload isolation, executable integrity, blockers, and the no-structural-only-pass rule |
| DEV-140 | Document exact triggers, non-triggers, result sections, pattern/API distinctions, proven placement, and actual blockers without advertising prototype or blocked behavior as shipped |
| DEV-141 | Reject acceptance for catalog overlap, missing fields, reference duplication, state/security/recovery drift, unsafe evidence, oracle drift, false host pass, or missing required real-capability proof |

Dependent non-positive and ambiguous completion cannot pass until DEV-136
publishes reviewed affected-subset evidence and the full 25-case Codex `0.144.5`
matrix on the combined tip. Claude execution remains deferred. That downstream
completion gate did not run here and does not block DEV-134's design-prototype
verification.

Detailed examples, walkthroughs, alternatives analysis, option comparison, and
design rationale remain only in the canonical design.
