# DEV-134 Apple Foundation Models Handoff Agent Skill Catalog Design

Issue: [DEV-134](https://linear.app/devprentice/issue/DEV-134/d3-design-the-agent-skill-and-reference-architecture)

Decision date: `2026-07-17`

Durable decision: Linear comment
`e90f2a39-d887-48b6-a8ce-17a2fa56e0a3`

Stack input: `ca767a0c50e1b527fed5c87e0922bf51cf655295`

## Purpose and authority

This specification is the authoritative DEV-134 catalog for the five Agent
Skills that help Apple-platform engineers design, implement, review, debug, and
validate Apple Foundation Models handoff architectures. It defines activation,
workflow ownership, result shapes, progressive-disclosure routes, synthetic
design-prototype cases, and downstream contracts. It does not create a
production skill or claim that either host can activate one yet.

The reviewed issue heads below are binding inputs:

| Issue | Reviewed head | Authority consumed here |
| --- | --- | --- |
| DEV-128 | `4f0b66ef7061d842f333e2749e74614f5331c915` | Installed SDK 26.5 interface and compiled-fixture boundary; official OS/Xcode 27 beta inventory; handoff-pattern and Apple runtime Skills distinctions. |
| DEV-129 | `3db33eb957326b4d22ebe482c21925dd23b03af0` | One physical provider-neutral capability corpus, narrow what-and-when skills, progressive disclosure, generated Codex ownership, and host-specific structural workflows. |
| DEV-130 | `5e27a1c81a4c45199c912a5cbb750a30a8c7bf17` | Deterministic reducer authority, C0-C3 context policy, grants, confirmation, provenance, effect ledger, recovery, fallback, and metadata-only live evidence. |
| DEV-131 | `3792e8c98a387b7f9c48bd210d25938b40cdd5fe` | Stable D/E identities, deterministic/rubric/host evidence separation, safe synthetic evidence, status meanings, and zero-denominator behavior. |
| DEV-132 | `ca767a0c50e1b527fed5c87e0922bf51cf655295` | Exact five-skill catalog, `architectureSchemaVersion: "1.0"`, common state/security/evidence contract, five concern-owned references, no-worker decision, and conditional package placement. |

The source reports are
[`dev-128-foundation-models-api-map.md`](../../research/dev-128-foundation-models-api-map.md),
[`dev-129-production-pattern-comparison.md`](../../research/dev-129-production-pattern-comparison.md),
[`dev-130-handoff-threat-model.md`](../../research/dev-130-handoff-threat-model.md),
[`dev-131-evaluation-strategy.md`](../../research/dev-131-evaluation-strategy.md),
and the
[`DEV-132 canonical architecture`](2026-07-17-dev-132-mvp-architecture-design.md).
The compact DEV-132
[`decision record`](../../architecture/apple-foundation-models-handoff-mvp-decision-record.md)
is a durable index, not a competing authority.

Apple API claims are controlled by current official Apple documentation,
installed SDK interfaces, WWDC material, and Apple-owned repositories. Duyet
`codex-claude-plugins`, Zeabur Agent Skills, upstream bstack, and OpenAI plugin
examples are structural production references only. Their domain prose is not
Apple API evidence. If this catalog and an Apple primary source disagree about
an Apple declaration, the Apple source plus a compatible compile check controls
and the catalog must be corrected.

## Resolved approaches

### Selected: five exact workflows behind one domain-first router

Keep the five exact DEV-132 skill names and route by handoff domain,
`requestedOperation`, `artifactState`, and `evidenceState`. Every entry owns one
workflow, consumes the same versioned architecture contract, and links directly
to the same concern-owned reference corpus. This preserves reviewable ownership
without duplicating volatile domain rules.

### Rejected: five duplicated workflow copies

Five names that each repeat the complete state, security, Apple API, and
evidence guidance would produce five mutable contracts. A correction to
recovery or an Apple version label could land in only some copies. Shared
references and a single common result contract are therefore mandatory.

### Rejected: collapsed or provider-specific catalogs

A catch-all entry or a collapsed design/implement/review/debug/validate skill
would make activation and edit authority ambiguous. Separate Claude and Codex
catalogs would fork provider-neutral behavior. Provider-specific wrappers,
generated skill mirrors, and a plugin-local worker are not approved.

## MVP scope and non-goals

DEV-134 produces these contracts:

1. this canonical design;
2. a compact, non-authoritative downstream skill contract derived from it; and
3. hash-bound `design_contract_prototype` evidence for exactly 15 synthetic
   activation cases with identical normalized Claude/Codex expectations.

The design owns exact skill names, activation and non-activation semantics,
common and workflow-specific result fields, direct reference routes, synthetic
case identities, and two complete walkthrough expectations. It preserves the
DEV-132 architecture; it does not reopen package placement, metadata ownership,
generation direction, or the root-package fallback trigger.

DEV-134 does not create or modify:

- production `SKILL.md` files or reference content;
- Claude/Codex manifests, marketplaces, schemas, guidance adapters, generators,
  validators, installation/cache workflows, or generated artifacts;
- Swift fixtures, application runtime orchestration, authentication,
  authorization, encryption, persistence, networking, UI, provider
  integration, or a reusable package/sample application;
- a plugin-local agent, hook, command, MCP server, app, dependency, runtime
  package, provider-specific skill copy, or generated skill mirror;
- PCC, custom-provider, live-model, credential, entitlement, paid-service,
  network, device, simulator, full-Xcode, Evaluations, or Instruments
  requirements in default proof;
- Apple Handoff, App Intents, coding-session handoff, generic Core ML/Swift or
  Foundation Models education, or Apple Foundation Models runtime Skills; or
- a release, publication, tag, merge, marketplace distribution, or capability
  claim based only on files, Markdown, validation, discovery, installation, a
  version string, or an enabled flag.

The plugin supplies guidance and reviewable proof contracts. It never becomes
the application's reducer, authorization boundary, effect executor, external
truth source, or runtime enforcement layer.

## Activation router

### Normalized router input

The router evaluates these fields in order:

```text
domain = foundation_models_handoff | out_of_domain | ambiguous
requestedOperation = design | implement | review | debug | validate | compound_review_fix | unspecified
artifactState = absent | proposal | approved_contract | implementation | evidence_bundle | unknown
evidenceState = not_requested | missing | available | failing | blocked | unknown
```

`domain=foundation_models_handoff` requires an application architecture that
coordinates Apple Foundation Models sessions/profiles/providers through
baton-pass, isolated consultation, deterministic routing, transcript transfer,
or a related state/context/tool/recovery boundary. A mere occurrence of the
words “Apple,” “model,” “agent,” “skill,” or “handoff” is insufficient.

### Decision procedure

1. **Classify the domain first.** `out_of_domain` returns `no_activation`.
   `ambiguous` asks one bounded domain question and does not select a skill.
2. **Normalize the requested operation.** Prefer the user's explicit action.
   Infer from the requested deliverable only when the action is unambiguous.
3. **Inspect artifact state.** Implementation requires an approved architecture
   or decision reference and an exact change boundary. Review/debug require an
   existing artifact or observed behavior respectively.
4. **Inspect evidence state.** Proof-only execution selects validate. A failing
   proof plus an unexplained observed divergence selects debug when root-cause
   analysis is requested; findings-only inspection remains review.
5. **Resolve compound authority.** “Review and fix” defaults to review first.
   The review may name a bounded follow-on implementation but must not invoke a
   second skill or edit the artifact.
6. **Select at most one result.** A request never activates two skills. Each
   selected skill loads its own direct references.

### Router table

| Domain and normalized state | Outcome |
| --- | --- |
| Handoff; new/revised topology, pattern, state, or boundary | `design-apple-foundation-models-handoff` |
| Handoff; code change; `artifactState=approved_contract` | `implement-apple-foundation-models-handoff` |
| Handoff; existing proposal/code/fixture/evidence; findings requested | `review-apple-foundation-models-handoff` |
| Handoff; observed unexplained routing/ownership/context/tool/recovery/availability divergence | `debug-apple-foundation-models-handoff` |
| Handoff; proof-only deterministic/compile/schema/generation/evidence/host matrix | `validate-apple-foundation-models-handoff` |
| Handoff; compound review and fix | `review-apple-foundation-models-handoff`, with a documented follow-on boundary only |
| Handoff; implementation requested without an approved contract/change boundary | `clarification_required` with one approved-contract question |
| Ambiguous “Apple handoff” domain | `clarification_required` with one domain question |
| Out-of-domain concept | `no_activation` |

One bounded clarification means exactly one concise question that names the
single missing discriminator. It must not gather implementation detail, start a
workflow, emit a positive result, or loop through multiple questions. If the
answer does not establish the domain or approved contract, the result stays
non-positive.

## Common result contracts

### Positive activation envelope

Every positive activation has this normalized outer shape:

```text
activationStatus = activated
selectedSkill
routerInput = { domain, requestedOperation, artifactState, evidenceState }
architectureResult
```

`architectureResult` always has `architectureSchemaVersion: "1.0"` and the
complete common machine-readable contract:

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

A positive handoff design selects `baton_pass` or
`isolated_consultation` unless it explicitly concludes that the request needs
deterministic routing or transcript transfer rather than a handoff. Review,
debug, and validation may use the full union to identify a mislabelled design.

The matching human rendering contains every common section below, even when a
section explicitly reports no applicable effect or a named blocker:

1. **Activation and Scope**
2. **Pattern and Ownership**
3. **Apple API Availability**
4. **State and Lifecycle**
5. **Trust and Model Boundaries**
6. **Context Policy**
7. **Tools Effects and Confirmation**
8. **Failure Recovery and Fallback**
9. **Verification and Evidence**
10. **Limitations**

Exact prose is not the acceptance contract. Versioned fields, stable IDs,
sections, state facts, and security outcomes are.

### State, security, and failure invariants

Every positive workflow preserves all of the following:

- independent monotonic `stateVersion` and separately changed `policyVersion`;
- phase `stable | transitioning | recoveryRequired | terminated`, one stable
  active profile/provider, an explicit `finalResponseOwner`, valid edges, and
  finite transition/tool/effect budgets;
- phase validation before budget mutation; a valid proposal checkpoints state,
  enters `transitioning`, and emits at most one executor command;
- application-created typed events as the only reducer authority; prompt,
  model, repository, summary, retrieved, and tool text remain untrusted data;
- field-level C0, C1, C2, or C3 classification plus source, subject, purpose,
  destination, retention, and redaction provenance; unknown or disallowed data
  rejects the whole envelope rather than being silently dropped;
- a provider grant scoped to a person/session that binds the person/session,
  source profile/provider, destination profile/provider, purpose, exact classes,
  exact fields, tools, retention, expiry, `stateVersion`, and `policyVersion`;
  any bound-field change invalidates the grant, which is not effect confirmation
  and cannot override C3 or unknown-data fail-closed behavior;
- immediate high-impact effect confirmation that binds the semantic action,
  normalized arguments, recipient/resource identity and version,
  provider/profile, `stateVersion`, `policyVersion`, authority, effect budget,
  and idempotency key;
- after confirmation and before execution, application revalidation of
  authentication/unlock state, permissions and tool allowlist, input schema,
  semantic argument constraints, recipient/resource identity and version,
  provider/profile, `stateVersion`, `policyVersion`, authority, effect budget,
  active state, and the grant; any mismatch rejects execution and requires
  fresh authority or confirmation as applicable;
- prompt, model, repository, summary, retrieved, and tool text remain untrusted
  and cannot create or broaden a grant, confirmation, authority, or typed
  reducer event;
- provenance-valid tool results bound to outstanding call ID, tool/version/
  provider, state, and result type;
- one stable identity and ledger entry for each logical effect,
  application-controlled at-most-once command emission, and reconciliation
  rather than an exactly-once external-delivery promise;
- preserved transcript/history is reused only after deterministic repair of
  partial responses and provenance-balanced tool-call/output pairs; a session
  transcript is never mutated while that session is responding, and a model
  summary cannot establish structure, authority, or effect truth;
- known pre-commit failure/cancellation restores the checkpoint; possible or
  uncertain external commit records repair facts and remains
  `recoveryRequired`;
- only explicit successful reconciliation establishes external truth and may
  produce a valid `stable` state; “no safe reconciliation path” remains
  `recoveryRequired` and returns repair-blocked/unavailable;
- late/replayed events while recovery is unresolved preserve phase, authority,
  pending/checkpoint state, counts, effect ledger, and repair facts exactly and
  emit no executor command;
- ordinary budget/no-safe-path termination only from `stable`; unresolved
  recovery is never relabelled `terminated`; and
- fallback only to an already authorized equal-or-lower context, retention,
  tool, effect, and provider boundary. Any expansion needs a new matching
  grant; otherwise return explicit unavailable/degraded state; and
- PCC and every custom provider remain separate trust boundaries; PCC
  properties never transfer to another provider, and absent local tool-call
  evidence from an opaque provider means `unknown`, not zero tool use.

### Apple availability labels

Executed Apple claims use exactly `compiled_sdk_26_5` or
`interface_verified_sdk_26_5`. The other distinct states are
`official_os_xcode_27_beta_locally_unverified`,
`pseudocode_deterministic_mock`, and `blocked`. “SDK 26.x” is a family boundary,
not an executed evidence label. Exact error tables must contain full case
signatures and associated-value payload types; a shorter inventory is labelled
name-only. Stable SDK 26.5 errors and current beta language/session/model/PCC
errors stay separately versioned.

Baton-pass and isolated consultation are Apple composition patterns, not
first-class `BatonPass` or `PhoneFriendTool` framework types. Transcript
Codable/rehydration proves mechanics only. Dynamic profiles, history mutation,
history transforms, tool-calling mode, transcript error policy, PCC/custom
providers, Evaluations, Instruments, and Foundation Models runtime Skills keep
their exact source/version/prerequisite boundary.

### Verification and evidence split

Allowed verification statuses are `pass`, `fail`, `blocked`, and
`not_applicable`. Zero denominator produces `not_applicable` with a null value.
One host cannot substitute for another.

The mandatory deterministic catalog is `D-SCHEMA-001`, `D-ROUTE-001`,
`D-OWNER-001`, `D-TRANSITION-001`, `D-TOOL-001`, `D-CONTEXT-001`,
`D-CONTEXT-002`, `D-GRANT-001`, `D-PHASE-001`, `D-EFFECT-001`,
`D-EFFECT-002`, `D-FALLBACK-001`, `D-EVIDENCE-001`, and `D-RUBRIC-001`.
The exact human rubric dimensions are pattern selection; Apple API grounding
and version labeling; security-policy completeness; context minimization;
failure and recovery behavior; testability and observability; and limitation
honesty. Scores are integers 1-4, mean is at least `3.0`, and security,
failure/recovery, and limitation honesty are each at least `3`. Deterministic
validation owns hash/anchor/arithmetic integrity; a human owns semantic scores.

Runtime and live-host telemetry contributes normalized metadata only. The
separate DEV-131 allowlist permits a hash-bound synthetic or approved-redacted
rubric stimulus, bounded assessment rationales, and a redacted summary after
path, content, structured-key, classification, and hash scanners pass. Raw/live
prompts, responses, reasoning, tool arguments/results, credentials, private
configuration, real user/third-party data, raw host/machine identity, literal
executable paths, raw `PATH`, raw blocker diagnostics, `.trace`, and `.xcresult`
are excluded from committed evidence.

### Non-positive activation results

An out-of-domain result is exactly a normalized rejection, not a partial
architecture:

```text
activationStatus = no_activation
reasonCode = out_of_domain
domain
requestedOperation
```

A clarification result is likewise bounded:

```text
activationStatus = clarification_required
clarificationKind = domain | approved_contract
missingInput
question
```

Neither non-positive shape contains `architectureResult`, workflow-specific
sections, loaded references, a fabricated Apple claim, or evidence that a host
activated a production skill.

## Exact skill catalog

### `design-apple-foundation-models-handoff`

**Purpose:** Choose and specify a new or revised Foundation Models handoff
architecture as an implementation-ready decision contract.

**Exact what-and-when activation description:** Design an Apple Foundation
Models handoff architecture, topology, pattern, state model, or trust boundary
when the user is creating or materially revising how sessions, profiles, or
providers transfer control or provide isolated consultation.

**Positive triggers:** new baton-pass or consultation flow; pattern comparison;
new route/owner/context/tool/recovery design; material revision to an existing
architecture; deciding that deterministic routing or transcript transfer means
no handoff is needed.

**Non-triggers:** application coding against an approved contract; findings-only
inspection; an observed unexplained failure; proof-only execution; generic
Foundation Models education; Apple Handoff; App Intents; runtime Skills;
coding-session handoff.

**Required inputs:** task scope; intended source and destination roles/providers;
ownership goal; available artifact/repository context; context and effect
classes; evidence/toolchain state. Missing noncritical detail becomes an
explicit assumption or limitation, not fabricated authority.

**Ordered workflow:**

1. confirm the Foundation Models handoff domain and normalize the router input;
2. inspect current architecture, repository, installed SDK, and cited Apple
   evidence without treating structural references as API authority;
3. compare baton-pass, isolated consultation, deterministic routing, and
   transcript transfer using topology, history, trigger/control, and final
   owner;
4. define reducer state, valid edges, budgets, ownership, context envelope,
   provider grant, tool/effect policy, recovery, and safe fallback;
5. label every Apple surface and every pseudocode boundary exactly;
6. produce the common result plus **Alternatives**, **Decision Rationale**,
   **Proposed Components**, and **Implementation and Test Plan**; and
7. bind deterministic checks, rubric inputs, host blockers, and limitations.

**Direct references:** always load `architecture-and-state.md` and
`orchestration-patterns.md`; load `apple-api-availability.md` for every Apple
surface; load `security-context-and-recovery.md` for every transfer/provider/
tool/effect boundary; load `evaluation-and-observability.md` to specify proof.

**Workflow-specific output:** alternatives, selected architecture and rationale,
proposed components/file changes, and a scoped implementation/test plan.

**Failure behavior:** return clarification for ambiguous domain; return an
explicit no-handoff decision when routing/transfer is sufficient; mark missing
SDK/host proof blocked; never invent Apple types, grants, or runtime behavior.

**Non-goals:** writing production changes, reviewing a finished artifact,
root-cause debugging, running the production host harness, or enforcing the
application policy it describes.

### `implement-apple-foundation-models-handoff`

**Purpose:** Translate an approved handoff contract into bounded application
changes and tests while retaining contract traceability.

**Exact what-and-when activation description:** Implement an Apple Foundation
Models handoff architecture when an approved architecture or decision reference
and an exact application change boundary already exist.

**Positive triggers:** add or change reducer/application code, Swift integration,
tests, or configuration that cites an approved contract and names affected
paths; apply an explicitly approved bounded correction after a separate review.

**Non-triggers:** implementation request without an approved contract; selecting
a new pattern; findings-only review; unexplained failure diagnosis; proof-only
validation; unrelated Swift feature work.

**Required inputs:** immutable approved-decision reference; exact change
boundary; repository state; target/toolchain; applicable API labels; expected
deterministic and compile/regression gates.

**Ordered workflow:**

1. normalize activation and verify the approved contract/change boundary;
2. inspect current code/tests and map every change to the contract;
3. preserve reducer authority, state/security/recovery/fallback invariants and
   version-labelled Apple boundaries;
4. use test-first changes and compile supported Swift examples on the pinned
   local SDK;
5. run deterministic, regression, evidence, generation/schema, and applicable
   host prerequisites without widening scope; and
6. emit the common result plus **Approved Decision**, **Change Boundary**,
   **Changed Paths**, and **Compilation and Regression Results**.

**Direct references:** load `architecture-and-state.md`; load
`orchestration-patterns.md` for the approved topology; load
`apple-api-availability.md` for compiled interfaces; load
`security-context-and-recovery.md` for context/tools/effects; load
`evaluation-and-observability.md` for required proof.

**Workflow-specific output:** approved decision reference, exact change
boundary, changed paths, and compile/regression results.

**Failure behavior:** missing approved contract or boundary returns the one
bounded contract clarification; an unsupported SDK/API is blocked, not replaced
with speculative code; a failing required gate remains fail.

**Non-goals:** redesigning the architecture, editing outside the approved
boundary, weakening tests, adding providers/dependencies, or claiming the skill
itself enforces runtime authorization.

### `review-apple-foundation-models-handoff`

**Purpose:** Inspect an existing proposal, implementation, fixture, or evidence
bundle and return finding-first contract/API/security feedback without editing.

**Exact what-and-when activation description:** Review an existing Apple
Foundation Models handoff artifact when the user wants severity-ranked findings
about architecture, Apple API grounding, state, security, recovery, or evidence
claims rather than changes.

**Positive triggers:** architecture review; code review; threat/evidence audit;
“review and fix” compound request; validation-result interpretation when the
requested output is findings rather than rerunning proof.

**Non-triggers:** style-only or unrelated Apple review; greenfield architecture;
authorized implementation-only work; unexplained live failure diagnosis;
proof-only command execution.

**Required inputs:** artifact and intended contract or reconstructable intent;
scope; available code/fixtures/evidence; claimed SDK/host boundaries. Missing
evidence is itself a bounded finding or blocker, not invented proof.

**Ordered workflow:**

1. normalize activation and freeze the review/edit boundary;
2. reconstruct intended pattern, owner, state, trust, context, effect, recovery,
   API, and evidence contracts;
3. inspect the artifact against exact common fields and stable D/E rules;
4. rank only evidence-backed findings by severity and stable check ID;
5. give impact and the smallest bounded correction for each finding; and
6. emit the common result plus **Findings**, without modifying the artifact or
   invoking implement.

**Direct references:** load `architecture-and-state.md`; load
`orchestration-patterns.md` for topology/ownership; load
`apple-api-availability.md` for claims; load
`security-context-and-recovery.md` for trust/effect findings; load
`evaluation-and-observability.md` for evidence integrity.

**Workflow-specific output:** severity-ranked findings, each with stable check
ID, exact evidence, impact, and bounded correction; state explicitly when no
finding is proven.

**Failure behavior:** unavailable artifact/evidence yields a blocker; ambiguous
intent is reconstructed from stated facts with limitations; no finding is
fabricated to satisfy a requested count. Compound work stops after review and
names a separate authorized change boundary.

**Non-goals:** editing code/prose, silently converting review into redesign,
rerunning every host gate, or treating compilation/file presence as capability.

### `debug-apple-foundation-models-handoff`

**Purpose:** Find the first divergence and root cause of an observed handoff
failure, then bound the correction and regression proof.

**Exact what-and-when activation description:** Debug an Apple Foundation Models
handoff when an observed routing, ownership, transition, context, tool, effect,
recovery, fallback, availability, or version-labelled behavior differs from its
expected contract and the cause is not yet established.

**Positive triggers:** transition/owner mismatch; context leak or rejection;
spoofed/missing tool result; uncertain effect timeout; replay; stuck recovery;
unsafe fallback; availability/error mismatch; host evidence divergence.

**Non-triggers:** generic crash with no handoff boundary; planned architecture;
approved implementation work with known change; findings-only review; proof-only
matrix execution with no diagnosis request.

**Required inputs:** observed and expected behavior; reproducible boundary or
evidence; relevant state/effect identities in normalized form; artifact and
toolchain context; allowed correction scope.

**Ordered workflow:**

1. normalize activation and reproduce or classify the observed divergence;
2. compare expected/observed state and find the first divergent event;
3. test state, policy, graph, context, grant, provenance, effect, recovery,
   fallback, and API-version hypotheses systematically;
4. identify one evidence-backed root cause without exposing raw sensitive data;
5. specify or, only when requested and authorized, apply the smallest root-cause
   correction; and
6. emit the common result plus **Observed and Expected State**,
   **First Divergence**, **Root Cause**, **Correction**, and
   **Regression Proof**.

**Direct references:** load `architecture-and-state.md`; load
`orchestration-patterns.md` for route/owner failures; load
`apple-api-availability.md` for availability/version failures; load
`security-context-and-recovery.md` for trust/effect/replay; load
`evaluation-and-observability.md` for reproducible safe proof.

**Workflow-specific output:** observed/expected state, first divergence, root
cause, bounded correction, and regression proof.

**Failure behavior:** unreproducible or unavailable evidence is blocked with a
named prerequisite; uncertain external truth stays `recoveryRequired`; no retry
or fallback broadens authority; broader changes are returned as a separate
design/implementation boundary.

**Non-goals:** generic debugging, speculative API replacement, broad refactor,
external-effect rollback claims, or converting raw prompts/traces into committed
evidence.

### `validate-apple-foundation-models-handoff`

**Purpose:** Execute and report the deterministic, compile, schema, generation,
evidence, rubric-integrity, and host acceptance matrix without editing the
subject to manufacture a pass.

**Exact what-and-when activation description:** Validate an Apple Foundation
Models handoff artifact when the user requests reproducible proof, a complete
pass/fail/blocked/not-applicable matrix, cross-host comparison, or release
implication rather than design, edits, findings-only review, or diagnosis.

**Positive triggers:** run offline cases; compile Swift examples; check schemas
or generated drift; scan evidence; verify rubric integrity; execute eligible
host E rows; produce final proof/release matrix.

**Non-triggers:** file-presence/Markdown-only success request; architecture or
code creation; findings-only review; unexplained failure diagnosis; claims from
binary discovery alone.

**Required inputs:** artifact/commit identity; required gate catalog; expected
oracle; repository/toolchain/host prerequisite state; evidence policy; release
decision boundary.

**Ordered workflow:**

1. normalize activation and pin the artifact, commands, oracles, and hosts;
2. run deterministic and schema/generation/evidence checks;
3. compile/run supported SDK 26.5 fixtures and classify exact blockers;
4. validate the seven-dimension rubric record without inventing human scores;
5. run eligible real-host rows separately and preserve per-host outcomes;
6. scan evidence and rerun affected gates after any authorized correction made
   outside this skill's proof-only boundary; and
7. emit the common result plus **Layer Matrix**, **Counts and Hashes**,
   **Rubric Result**, **Blockers and Skips**, and **Release Implication**.

**Direct references:** load `architecture-and-state.md` for schema/state facts;
load `orchestration-patterns.md` when route/owner cases are in scope; load
`apple-api-availability.md` for compile/blocker labels; load
`security-context-and-recovery.md` for adversarial assertions; load
`evaluation-and-observability.md` for all gate and evidence semantics.

**Workflow-specific output:** complete layer matrix, executed counts, hashes,
rubric integrity/result, blockers/skips, reviewer verdict when supplied, and
release implication.

**Failure behavior:** retain every failing gate; classify a missing named
prerequisite blocked; use `not_applicable` only for a valid non-applicable
calculation; never edit production code/prose, weaken an oracle, or extrapolate
one host's outcome.

**Non-goals:** fixing the subject, semantic rubric scoring without a human,
claiming blocked Apple/host rows passed, or treating structure as capability.

## Progressive-disclosure routing

The exact five filenames are fixed. Each has one concern owner; content is
authored once under `references/`, and every consumer edge is direct from the
selected skill. No reference invokes a skill and no skill invokes another.

| Reference | Sole concern ownership | Direct consumer rule |
| --- | --- | --- |
| `architecture-and-state.md` | `1.0` result schema; state/ownership/lifecycle; transition, termination, cancellation, retry, and repair | All five load it for common output/state facts. |
| `orchestration-patterns.md` | Baton-pass, isolated consultation, deterministic routing, transcript transfer, topology, history, trigger/control, and final-owner selection | Design always; implement/review/debug when topology or ownership is in scope; validate for route/owner cases. |
| `apple-api-availability.md` | Installed SDK 26.5 compiled/interface surfaces; separately labelled OS/Xcode 27 beta declarations; full error signatures; cache/provider/runtime Skills boundaries | Every skill that mentions or checks an Apple surface loads it directly. |
| `security-context-and-recovery.md` | Trust boundaries, C0-C3, provenance, grants, confirmation, result provenance, effects, recovery, fallback, trace safety, and residual risk | Every skill with a transfer, provider, tool, effect, recovery, fallback, or evidence-safety boundary loads it directly. |
| `evaluation-and-observability.md` | D/E IDs, corpus/oracle, rubric, safe evidence, host matrix, zero denominator, Evaluations, Instruments, and blocker policy | Design specifies proof; implement records it; review audits it; debug reproduces it; validate owns its execution matrix. |

Core activation descriptions stay concise. Volatile Apple declarations, exact
error payload signatures, detailed policy tables, and evidence-scanner rules
remain in their sole owning references. Production skills may summarize a rule
needed to execute their workflow, but they link to the owner and must not create
a second canonical table.

## Plugin-agent decision

No plugin-local worker or agent is justified. All five workflows use the host's
active agent, share the same domain contract, and differ by activation and
output/edit authority rather than by an isolated role, context, tool set, or
execution environment.

Optional per-skill `agents/openai.yaml` is presentation-only downstream
metadata. DEV-135 may add it only if native validation demonstrates a concrete
presentation need. It may contain UI/activation presentation, but it cannot own
domain/workflow content, execute as a worker, replace `SKILL.md`, fork Claude
and Codex semantics, or become an additional capability. DEV-134 creates no
such YAML.

## Design-prototype E2E suite

These 15 synthetic cases define normalized design expectations, not production
host capability. For every case,
`hostExpectations.claude == hostExpectations.codex == expectedActivation`.
Positive cases use the `1.0` result; negative and clarification cases use only
their non-positive shape.

### DEV134-POS-001: new baton-pass design

- Representative synthetic request: “Design a new Apple Foundation Models baton-pass architecture where a research profile transfers control and final-answer ownership to a review profile.”
- Input class: new architecture request.
- Router: `design`, `absent`, `missing`.
- Expected activation: `design-apple-foundation-models-handoff`.
- Direct references: all five concern owners.
- Full walkthrough: yes; detailed below.
- Resolution: select a research-to-review baton-pass with destination final
  ownership, target-necessary context, reducer authority, and bounded proof.

### DEV134-POS-002: flawed reducer review

- Representative synthetic request: “Review this existing Foundation Models handoff reducer for ambiguous ownership, unlimited transitions, and full-transcript transfer, and return findings without editing it.”
- Input class: existing implementation findings request.
- Router: `review`, `implementation`, `failing`.
- Expected activation: `review-apple-foundation-models-handoff`.
- Direct references: all five concern owners.
- Full walkthrough: yes; detailed below.
- Resolution: reject ambiguous owner, unbounded transitions, full transcript,
  and incomplete recovery using stable IDs and bounded corrections.

### DEV134-POS-003: approved contract implementation

- Representative synthetic request: “Implement only the transition-budget check defined by approved synthetic architecture decision ARCH-SYN-001 in the reducer and its tests.”
- Input class: bounded application change tied to an approved decision.
- Router: `implement`, `approved_contract`, `available`.
- Expected activation: `implement-apple-foundation-models-handoff`.
- References: architecture/state, approved pattern, Apple availability,
  security/recovery, and evaluation proof loaded directly.
- Resolution: implement only the named boundary and report changed paths plus
  compile/regression results.

### DEV134-POS-004: observed uncertain-effect failure

- Representative synthetic request: “Debug why a dispatched synthetic handoff effect timed out and the reducer attempted to replay the same effect before reconciliation.”
- Input class: dispatched effect timed out and replay was proposed.
- Router: `debug`, `implementation`, `failing`.
- Expected activation: `debug-apple-foundation-models-handoff`.
- References: architecture/state, security/recovery, and evaluation always;
  pattern/API references when the observed route or API is implicated.
- Resolution: identify the first divergence, keep `recoveryRequired`, reconcile
  the one effect identity, emit no replay command, and prove the regression.

### DEV134-POS-005: proof-only evidence matrix

- Representative synthetic request: “Validate the handoff's deterministic, SDK compile, evidence-safety, and Claude/Codex host matrix, report blockers, and do not edit anything to obtain a pass.”
- Input class: deterministic/compile/evidence/cross-host validation request.
- Router: `validate`, `evidence_bundle`, `available`.
- Expected activation: `validate-apple-foundation-models-handoff`.
- References: evaluation plus every owner exercised by the matrix.
- Resolution: report exact pass/fail/blocked/not_applicable rows, hashes,
  rubric integrity, blockers, and release implication without editing.

### DEV134-POS-006: isolated-consultation selection

- Representative synthetic request: “Design an Apple Foundation Models consultation where the parent session asks a narrow specialist question, keeps control, and writes the final answer.”
- Input class: parent asks a specialist a narrow question but retains control.
- Router: `design`, `absent`, `missing`.
- Expected activation: `design-apple-foundation-models-handoff`.
- References: all five concern owners.
- Resolution: choose an isolated child transcript and minimized envelope;
  parent remains final owner and child failure returns a typed result.

### DEV134-NEG-001: App Intents

- Representative synthetic request: “Show me how to expose an App Intent for a Shortcuts action.”
- Router domain: `out_of_domain`.
- Expected activation: `no_activation`.
- Resolution: `reject_out_of_domain`; no references or positive sections.

### DEV134-NEG-002: Apple Handoff

- Representative synthetic request: “Explain how to continue activity between my iPhone and Mac with Apple Handoff and NSUserActivity.”
- Router domain: `out_of_domain`.
- Expected activation: `no_activation`.
- Resolution: `reject_out_of_domain`; no references or positive sections.

### DEV134-NEG-003: generic Swift

- Representative synthetic request: “How do Swift actors isolate mutable state?”
- Router domain: `out_of_domain`.
- Expected activation: `no_activation`.
- Resolution: `reject_out_of_domain`; no references or positive sections.

### DEV134-NEG-004: generic Core ML or Foundation Models education

- Representative synthetic request: “Give me a beginner overview of Core ML model deployment.”
- Router domain: `out_of_domain`.
- Expected activation: `no_activation`.
- Resolution: `reject_out_of_domain`; no references or positive sections.

### DEV134-NEG-005: coding-session handoff

- Representative synthetic request: “How should I hand a coding session from Claude Code to Codex?”
- Router domain: `out_of_domain`.
- Expected activation: `no_activation`.
- Resolution: `reject_out_of_domain`; no references or positive sections.

### DEV134-NEG-006: Foundation Models runtime Skills alone

- Representative synthetic request: “Explain how Foundation Models runtime Skills activate tool calling inside one model session.”
- Router domain: `out_of_domain`.
- Expected activation: `no_activation`.
- Resolution: `reject_out_of_domain`; no references or positive sections.

### DEV134-AMB-001: ambiguous “Apple handoff”

- Representative synthetic request: “Help me design an Apple handoff.”
- Router: `ambiguous`, `unspecified`, `unknown`, `unknown`.
- Expected activation: `clarification_required`.
- Resolution: `bounded_domain_clarification` asking whether the request concerns
  Foundation Models session/profile/provider orchestration rather than Apple
  Handoff; no references or positive result before the answer.

### DEV134-AMB-002: implementation without an approved contract

- Representative synthetic request: “Implement the Apple Foundation Models handoff for my app.”
- Router: handoff, `implement`, `unknown`, `missing`.
- Expected activation: `clarification_required`.
- Resolution: `bounded_contract_clarification` asking for the approved
  architecture/decision reference and exact change boundary; no speculative
  design or code.

### DEV134-AMB-003: compound review and fix

- Representative synthetic request: “Review and fix this Apple Foundation Models handoff implementation.”
- Router: handoff, `compound_review_fix`, `implementation`, `failing`.
- Expected activation: `review-apple-foundation-models-handoff`.
- Resolution: `documented_default_review_first`; return findings and a bounded
  follow-on change boundary, with no edit and no second skill invocation.

### Full walkthrough A: `DEV134-POS-001`

Representative synthetic request: design a Foundation Models flow where a
research profile gathers evidence and a review profile takes over and answers.

| Required section | Expected content and guardrail |
| --- | --- |
| Activation and Scope | Router selects design only; Foundation Models handoff domain and exclusions are explicit. `D-SCHEMA-001`, `D-ROUTE-001`. |
| Pattern and Ownership | Compare all four patterns, select `baton_pass`, source `research`, destination `review`, destination final owner. `D-OWNER-001`, `D-TRANSITION-001`. |
| Apple API Availability | Stable transcript mechanics use exact SDK 26.5 labels; dynamic profiles remain OS/Xcode 27 beta locally unverified; no fictional `BatonPass` type. |
| State and Lifecycle | Independent versions, `stable -> transitioning -> stable`, valid edge, one active owner, finite budgets, checkpoint, and persistent recovery. `D-PHASE-001`. |
| Trust and Model Boundaries | Application reducer owns authority; on-device/PCC/custom providers remain distinct; model text is a proposal. |
| Context Policy | Target-necessary history, full provenance, atomic C0-C3 decision, C3 rejection. `D-CONTEXT-001`, `D-CONTEXT-002`. |
| Tools Effects and Confirmation | Bound grant, immediate confirmation, auth/permission/recipient recheck, typed result provenance, one effect identity. `D-TOOL-001`, `D-GRANT-001`, `D-EFFECT-001`. |
| Failure Recovery and Fallback | Pre-commit restore; uncertainty enters `recoveryRequired`; replay emits no command; reconciliation precedes retry; fallback never expands trust. `D-EFFECT-002`, `D-FALLBACK-001`. |
| Verification and Evidence | Mandatory D catalog, seven-dimension rubric input, metadata-only live evidence, safe synthetic allowance, and blocked host rows. `D-EVIDENCE-001`, `D-RUBRIC-001`. |
| Limitations | No runtime enforcement, live model, compatible beta host, external exactly-once guarantee, or activation claim. |
| Alternatives | Baton-pass versus isolated consultation, routing, and transcript transfer with topology/history/control/owner comparison. |
| Decision Rationale | Destination must continue and answer, so control/final ownership transfer is intentional. |
| Proposed Components | Framework-neutral reducer/state/context/grant/effect/evidence components and scoped file boundaries, not invented Apple types. |
| Implementation and Test Plan | Test-first reducer/security fixtures, SDK-supported compile checks, safe evidence gates, and separately blocked real-host/Apple rows. |

The expected guardrail set contains `D-ROUTE-001`, `D-OWNER-001`,
`D-TRANSITION-001`, `D-TOOL-001`, `D-CONTEXT-001`, `D-CONTEXT-002`,
`D-GRANT-001`, `D-PHASE-001`, `D-EFFECT-001`, `D-EFFECT-002`,
`D-FALLBACK-001`, `D-EVIDENCE-001`, and `D-RUBRIC-001`. The scenario passes
only when every common/design section is present and the destination alone owns
the final response.

### Full walkthrough B: `DEV134-POS-002`

Representative synthetic request: review a reducer that lets either profile
answer, has no transition limit, copies the full transcript, trusts a model
summary as approval, and terminates after an uncertain dispatch timeout.

| Required section | Expected content and finding |
| --- | --- |
| Activation and Scope | Router selects review only, freezes edits, and identifies the existing flawed artifact. `D-SCHEMA-001`, `D-ROUTE-001`. |
| Pattern and Ownership | Reconstruct intended baton-pass and report Important `D-OWNER-001` for ambiguous final owner plus `D-TRANSITION-001` for no finite budget. |
| Apple API Availability | Reject unlabelled beta profile/mutation claims; separate stable and beta errors and require exact evidence labels. |
| State and Lifecycle | Report phase/version/termination drift: uncertain external truth cannot become `terminated`; require persistent `recoveryRequired`. `D-PHASE-001`. |
| Trust and Model Boundaries | Report model summary as untrusted, not approval or reducer authority. |
| Context Policy | Report full transcript with no include/exclude/provenance policy using `D-CONTEXT-001` and `D-CONTEXT-002`; require atomic C3 rejection. |
| Tools Effects and Confirmation | Report missing bound grant/confirmation/result provenance with `D-TOOL-001`, `D-GRANT-001`, and `D-EFFECT-001`. |
| Failure Recovery and Fallback | Report timeout termination/retry as `D-EFFECT-002`; require one ledger identity, no replay command, explicit reconciliation, and `D-FALLBACK-001`. |
| Verification and Evidence | Reject file/compile presence as capability; require exact oracle, evidence scanner, rubric, and honest blockers. `D-EVIDENCE-001`, `D-RUBRIC-001`. |
| Limitations | State evidence gaps, beta-host blockers, no edits performed, and residual external uncertainty. |
| Findings | Severity-ranked finding for every proven violation, each with stable ID, exact synthetic evidence, impact, and smallest bounded correction. |

The expected guardrail set contains `D-OWNER-001`, `D-TRANSITION-001`,
`D-TOOL-001`, `D-CONTEXT-001`, `D-CONTEXT-002`, `D-GRANT-001`,
`D-PHASE-001`, `D-EFFECT-001`, `D-EFFECT-002`, `D-FALLBACK-001`,
`D-EVIDENCE-001`, and `D-RUBRIC-001`. The scenario passes only when the
deliberately flawed input is rejected with those applicable identities, every
common/review section is present, and the review performs no edit.

## Host capability boundary

This design and its 15-case oracle are `design_contract_prototype` evidence.
They prove that the written router and result expectations are internally
machine-checkable; they do not prove production loading, reference loading,
model-backed activation, output behavior, or cross-host equivalence.

Until DEV-135 creates a structurally valid candidate and DEV-136/DEV-137 create
the production skills/references, record:

```text
E-CLAUDE-ACTIVATE-001 blocked production_skill_not_implemented
E-CODEX-ACTIVATE-001 blocked production_skill_not_implemented
```

Claude Code `2.1.91` and Codex `0.144.5` version observations are executable
prerequisites only. They cannot turn these rows into passes. Real capability in
DEV-139 requires fresh tasks that observe correct activation, direct progressive
reference loading, complete versioned outputs, negative rejection, and paired
normalized semantics. Missing model/session/auth/automation remains blocked.

Each future host row captures one approved executable before operations, uses
it throughout, and rechecks resolution/version. Initial missing, non-runnable,
wrong-version, or invalid strict single-line version is `blocked`; post-capture
resolution/version drift is `fail` and invalidates the row. Committed identity
is normalized `<host-path>` with an exact strict version or `null`; literal
paths, raw `PATH`, malformed/multiline/path-bearing version output, and raw
diagnostics are never committed. Alternate-PATH Claude `2.1.140` remains
diagnostic only.

## Downstream handoff

| Issue | Inherited DEV-134 contract and scope boundary |
| --- | --- |
| DEV-135 | Scaffold exactly five names and optional presentation-only per-skill YAML only if proven necessary; preserve one corpus and generated ownership. Structural loading cannot claim activation. |
| DEV-136 | Author the five production workflows with these activation, ordered workflow, common result, workflow additions, failure, and non-goal contracts. Do not turn guidance into runtime enforcement. |
| DEV-137 | Author the five unchanged sole-owner references and direct links. Keep volatile Apple detail and exact error payload signatures in the Apple owner; do not copy fixture code into capability content. |
| DEV-138 | Map the stable D catalog and adversarial state/security/recovery cases to deterministic offline fixtures and exact repeated output, preserving oracle separation and safe synthetic evidence. |
| DEV-139 | Convert the 15 identities and both full walkthroughs into fresh Claude/Codex activation/reference/output/rejection evidence; preserve per-host blockers, payload isolation, executable integrity, and no structural-only pass. |
| DEV-140 | Document exact triggers, non-triggers, result sections, pattern/API distinctions, real blocker states, and proven package placement without advertising prototype or blocked behavior as shipped. |
| DEV-141 | Reject release readiness for catalog overlap, missing common/workflow fields, reference duplication, state/security/recovery drift, unsafe evidence, oracle drift, false host pass, or absent required real capability proof. |

These are contract handoffs, not implementation moved into DEV-134. A downstream
decision change must be recorded in its owning issue and propagated through the
durable Linear chain before work that depends on it starts.

## Completion criteria

DEV-134's design is complete only when:

- all five exact names have non-overlapping what-and-when activation,
  inputs/workflow/references/output/failure/non-goal contracts;
- the router is domain-first and deterministically resolves positive,
  no-activation, one-question clarification, and compound review-first cases;
- positive outputs retain the complete `architectureSchemaVersion: "1.0"`
  state, security, Apple availability, recovery, fallback, evidence, and
  limitation contract;
- negative and clarification outputs never fabricate a positive architecture;
- the five exact references each have one concern owner and every edge is
  direct;
- no plugin-local worker is introduced and optional YAML remains presentation
  metadata only;
- exactly six positive, six negative, and three ambiguous synthetic cases have
  identical normalized Claude/Codex expectations;
- the baton-pass design and flawed-reducer review traverse every required
  common/workflow section and applicable guardrail;
- the design-prototype oracle and safe-evidence checks pass reproducibly;
- real activation stays blocked under `E-CLAUDE-ACTIVATE-001` and
  `E-CODEX-ACTIVATE-001` until production capability proof exists;
- DEV-135 through DEV-141 inherit their issue-specific contracts without
  implementation scope leaking into this issue; and
- the issue diff contains only approved DEV-134 design/contract/prototype/plan
  artifacts, with no production skills or unrelated changes.
