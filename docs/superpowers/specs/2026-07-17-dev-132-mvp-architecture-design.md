# DEV-132 Apple Foundation Models Handoff MVP Architecture Design

Issue: [DEV-132](https://linear.app/devprentice/issue/DEV-132/d1-synthesize-research-into-the-mvp-architecture-and-decision-record)

Decision date: `2026-07-17`; July 18 amendment integrated on `2026-07-19`

Integration boundary: one atomic DEV-132 documentation change against current
`main`. Commit identifiers from earlier reviews are historical provenance, not
current acceptance bindings.

## DEV-136 option-2 supersession

> **Bounded supersession (DEV-136):** The approved DEV-136 option-2 decision
> amends the production capability topology to **five workflows plus one non-positive router**,
> `route-apple-foundation-models-handoff`. The five workflows retain
> **positive-only workflow ownership**; the **router-owned non-positive branches**
> are `no_activation`, domain `clarification_required`, and missing-approved-contract
> `clarification_required`. Historical evidence remains truthful: **fixture prompts/outcomes are unchanged**,
> and the DEV-134 prototype still does not prove host capability. **Codex-only current proof**
> remains in scope, while Claude proof is owner-deferred. The binding design amendment path is
> [`docs/superpowers/specs/2026-07-18-dev-136-preselection-router-design.md`](2026-07-18-dev-136-preselection-router-design.md).
> Statements below that describe exactly five production capabilities or a
> conceptual-only router remain historical except where this bounded note
> supersedes them.

## Purpose

This specification is the canonical MVP architecture for a cross-compatible
Claude Code and Codex plugin that helps Apple-platform engineers design,
implement, review, debug, and validate Apple Foundation Models handoff
architectures. It resolves the repository, Apple API, production-pattern,
security, and evaluation decisions established by DEV-127 through DEV-131.

DEV-132 produces architecture guidance and reviewable proof contracts only. It
does not install or run the approved host adapters, cost router, or Swift
bridge. Those production components are owned by downstream issues; a
probabilistic model never becomes authoritative for routing, transitions, or
effects.

## Source decisions and authority

The source artifacts on current `main` are binding inputs. Their earlier review
SHAs remain available in Git history but do not override later amendments.

| Issue | Authority used here |
| --- | --- |
| DEV-127 | The authoritative fork started as a three-document repository with no inherited plugin/generation architecture. |
| DEV-128 | SDK 26.5 has six positive fixtures and two strict expected blockers; Xcode 26.6, Swift 6.3.3, and SDK 26.5 observations are compile/interface evidence, never live bridge proof. |
| DEV-129 | One physical skill tree, five narrow positive workflows, explicit generated Codex artifacts, and host-specific loading. Its original no-router/no-worker conclusion applies to that guidance design, not later approved runtime work. |
| DEV-130 | Eight-case fail-closed proof, including diagnostic-result routing, original-result preservation, no rerun, provenance, recovery, fallback, and safe synthetic evidence. |
| DEV-131 | Twenty-six tests and eleven offline cases; deterministic/rubric/live evidence separation; paired null-capable `pluginOff`/`pluginOn` cost arms; `providerNormalizationVersion`; and the 10%/0/0 live release floor. |

Apple API claims remain subordinate to current official Apple documentation,
installed SDK interfaces, WWDC material, and Apple-owned repositories. Duyet,
Zeabur, upstream bstack, and OpenAI plugin examples are structural references,
not Apple API authority.

## Approaches considered

### Selected: evidence-gated root package with narrow skills

Treat the single-plugin repository root as the plugin source (`./`), keep one
physical `skills/` and `references/` tree, generate explicit Codex metadata,
and expose five bounded workflow entry skills. This is the least indirect
shape for a repository devoted to one plugin.

Root placement is conditional rather than assumed. DEV-135 and DEV-139 must
prove cached-install integrity and fresh real invocation/reference loading on
their current issue-approved host matrix. Each row pins its executable before
any operation and invalidates the result if resolution changes mid-run. An
earlier host version recorded in DEV-132 is historical evidence only. The
effective cached payload must
exclude repository-only fixtures, tests, research, and private repository
state; none may be exposed as plugin capabilities.

### Approved fallback: conventional plugin subdirectory

If either host rejects root placement, required content is omitted or resolves
outside the cached package, repository-only test material cannot stay outside
the effective plugin payload, or real activation/reference loading fails, use
`plugins/apple-foundation-models-handoff/` and marketplace source
`./plugins/apple-foundation-models-handoff`.

The fallback preserves identity, skills, references, metadata ownership,
generation, and behavior. It changes only physical placement. No symlink may
reach outside the fallback package. The fallback trigger is deterministic and
already approved; it is not a new product decision.

### Rejected: one catch-all or manually duplicated host catalogs

A single skill would combine incompatible activation and output ownership for
design, implementation, review, debugging, and validation. Provider-specific
copies would create semantic drift. Manually authored Claude and Codex
manifests/catalogs would leave two mutable sources. These shapes are rejected.

## MVP users, workflows, and boundaries

The plugin ID is `apple-foundation-models-handoff`. Its display name is
**Apple Foundation Models Handoff**.

The intended users are Apple-platform engineers, architects, reviewers, and
maintainers working in Claude Code or Codex. The supported user goals are:

1. design a new Foundation Models handoff architecture;
2. implement an approved architecture in an application repository;
3. review an existing handoff implementation or proposal;
4. debug routing, ownership, context, tool, recovery, or availability failures;
5. validate architecture, Swift examples, security invariants, and evidence.

This DEV-132 documentation change does not provide:

- application runtime orchestration, authentication, authorization, encryption,
  persistence, networking, or UI;
- a reusable Swift package or sample application;
- automatic PCC/custom-provider use, credentials, entitlements, or paid
  services;
- App Intents, Apple Handoff, generic Core ML/Apple Intelligence education, or
  coding-session handoff;
- production source for the approved non-positive router, `PostToolUse`
  adapters, cost router, or local Swift bridge; or
- release, publishing, tagging, merging, or marketplace distribution.

## Skill catalog and activation ownership

The MVP contains exactly five positive workflow skills:

| Skill directory | Activates for | Does not activate for | Primary output |
| --- | --- | --- | --- |
| `design-apple-foundation-models-handoff` | New or revised handoff architecture, topology, pattern, boundary, or state design | Generic Swift, general Foundation Models questions, App Intents, Apple Handoff | Complete architecture contract and implementation-ready decision record |
| `implement-apple-foundation-models-handoff` | Translating an approved handoff contract into application code/tests | Architecture work without an approved contract, unrelated feature coding | Scoped implementation plan/change set plus compile/test evidence |
| `review-apple-foundation-models-handoff` | Reviewing a proposal, code, fixture, or evidence bundle for contract/API/security violations | Style-only review or unrelated Apple code review | Severity-ranked findings with stable check IDs and proof |
| `debug-apple-foundation-models-handoff` | Diagnosing routing, ownership, transition, context, tool, recovery, or availability failure | Generic crash debugging without a handoff boundary | Root-cause statement, state/evidence trace, bounded fix and regression proof |
| `validate-apple-foundation-models-handoff` | Running deterministic, compile, schema, generation, evidence, or cross-host acceptance gates | File-presence or Markdown-only success claims | Per-layer pass/fail/blocked/not-applicable matrix and safe evidence bundle |

DEV-134 owns the final activation prose and workflow-specific output details
without changing these names or their non-overlapping responsibilities. A
positive prompt bypasses non-positive preselection and activates exactly one
workflow. A skill never depends on another skill invocation; all five load
common references directly.

### Bounded non-positive preselection

Exactly one preselection router handles only requests that have no positive
workflow match. It emits `no_activation` for out-of-domain input or
`clarification_required` for bounded domain/approved-contract ambiguity. It
cannot invoke a workflow, load a reference, emit `architectureResult`, use a
tool or effect, make an Apple capability claim, or introduce commands, agents,
hooks, or broader routing. `clarification_required` asks one bounded question;
the host must classify the answer afresh.

The original DEV-129 no-worker conclusion remains binding for the five guidance
workflows. It does not prohibit the separately approved, deterministic runtime
chain below. Per-skill `agents/openai.yaml`, if host validation requires it,
remains presentation and activation metadata only.

## Progressive-disclosure reference topology

The proposed shared reference library is concern-owned:

| Reference | Owns |
| --- | --- |
| `references/architecture-and-state.md` | Common output schema, state model, ownership, transitions, termination, cancellation, retry, and repair |
| `references/orchestration-patterns.md` | Baton-pass, isolated consultation, routing, transcript transfer, and pattern-selection tables |
| `references/apple-api-availability.md` | SDK 26.5 compiled surface, OS/Xcode 27 beta layer, errors, availability, cache caveats, PCC/providers, and runtime Skills disambiguation |
| `references/security-context-and-recovery.md` | Trust boundaries, C0-C3 classification, grants, confirmation, tool provenance, effect ledger, fallback, traces, and residual risks |
| `references/evaluation-and-observability.md` | Stable D/E IDs, datasets, rubric, evidence bundle, host matrix, Evaluations, Instruments, and blocker policy |

DEV-134 may refine filenames only if each concern retains one owner and every
skill link remains deterministic. DEV-137 writes the reference content. Swift
compile/adversarial fixtures stay under repository `fixtures/`; reference files
link to their evidence but do not embed or ship fixture code as a capability.

## Canonical, generated, and adapter ownership

### Authored canonical inputs

| Path/domain | Ownership |
| --- | --- |
| `CLAUDE.md` | Provider-neutral repository and plugin authoring guidance |
| `.claude-plugin/plugin.json` or fallback plugin-local equivalent | Shared plugin identity: name, version, description, author, project links, license, keywords |
| `.claude-plugin/marketplace.json` | Canonical Claude marketplace entry and selected source path |
| `metadata/codex-interface.json` or fallback plugin-local equivalent | Codex plugin `interface`, including `longDescription`, `category`, `capabilities`, and `defaultPrompt` |
| `metadata/codex-marketplace.json` | Codex marketplace source/order plus marketplace-only `plugins[].category` and `plugins[].policy` |
| `skills/**`, `references/**` | One physical provider-neutral capability corpus |

The two category fields are distinct: `plugin.json.interface.category` is a
plugin-presentation field, while `plugins[].category` is a marketplace-entry
field. `plugins[].policy` is marketplace-only. A generator or schema must not
move or collapse them.

### Generated outputs

| Path | Generated from | Edit rule |
| --- | --- | --- |
| `AGENTS.md` | Provider-neutral `CLAUDE.md` plus adapter template/rules | Never edit directly |
| `.codex-plugin/plugin.json` or fallback plugin-local equivalent | Claude shared identity plus `metadata/codex-interface.json` | Never edit directly |
| `.agents/plugins/marketplace.json` | Claude/shared identity and `metadata/codex-marketplace.json` | Never edit directly |

Generation uses Python 3 standard library only. One sync entry point supports
write and check modes; it produces stable key ordering/newlines, validates
inputs/outputs, detects untracked generated paths, and exits nonzero on drift.
Native Claude/Codex validators and the pinned stricter OpenAI validator remain
separate named gates because they implement different contracts.

The first generated `AGENTS.md` should be thin: it names the canonical guide,
non-editable outputs, selected plugin location, generator/check command,
Apple-source/version policy, and validation entry points. If a fresh Codex
repository probe cannot answer those questions, generation may emit a bounded
self-contained adapter derived from the same source. It never becomes an
independent full guide.

## Proposed production and repository file trees

### Root-package candidate

```text
.
├── CLAUDE.md                                      # canonical guidance
├── AGENTS.md                                      # generated adapter
├── .claude-plugin/
│   ├── plugin.json                                # canonical shared identity
│   └── marketplace.json                           # canonical Claude marketplace, source ./
├── .codex-plugin/
│   └── plugin.json                                # generated Codex manifest
├── .agents/plugins/
│   └── marketplace.json                           # generated Codex marketplace
├── metadata/
│   ├── codex-interface.json                       # canonical Codex interface input
│   └── codex-marketplace.json                     # canonical Codex marketplace input
├── skills/
│   ├── design-apple-foundation-models-handoff/SKILL.md
│   ├── implement-apple-foundation-models-handoff/SKILL.md
│   ├── review-apple-foundation-models-handoff/SKILL.md
│   ├── debug-apple-foundation-models-handoff/SKILL.md
│   └── validate-apple-foundation-models-handoff/SKILL.md
├── references/
│   ├── architecture-and-state.md
│   ├── orchestration-patterns.md
│   ├── apple-api-availability.md
│   ├── security-context-and-recovery.md
│   └── evaluation-and-observability.md
├── schemas/
│   ├── codex-interface-input.schema.json
│   ├── codex-marketplace-input.schema.json
│   └── architecture-result.schema.json
├── scripts/
│   └── sync_generated_artifacts.py                # write/check modes
├── tests/
│   ├── test_generated_artifacts.py
│   ├── test_plugin_contract.py
│   └── e2e/                                       # DEV-139 host harness
├── fixtures/                                      # repository-only, not plugin capability
└── docs/
```

Root packaging passes only if cached payload inspection and real activation
show that repository-only `fixtures/`, tests, research, and private repository
state are absent from effective cached payload content and are not exposed as
plugin capabilities.

### Approved conventional fallback

```text
.
├── CLAUDE.md                                      # canonical repository guidance
├── AGENTS.md                                      # generated repository adapter
├── .claude-plugin/marketplace.json                # source ./plugins/apple-foundation-models-handoff
├── .agents/plugins/marketplace.json               # generated marketplace
├── metadata/codex-marketplace.json                # canonical marketplace input
├── plugins/apple-foundation-models-handoff/
│   ├── .claude-plugin/plugin.json                 # canonical shared identity
│   ├── .codex-plugin/plugin.json                  # generated Codex manifest
│   ├── metadata/codex-interface.json              # canonical interface input
│   ├── skills/                                    # same five skills
│   └── references/                                # same five references
├── schemas/
├── scripts/sync_generated_artifacts.py
├── tests/
├── fixtures/                                      # remains outside plugin package
└── docs/
```

The fallback contains no symlink to root guidance, fixtures, tests, or scripts.
Repository guidance may describe and validate the plugin without being copied
into the installed capability corpus.

## Handoff pattern selection

The plugin guides two first-class composition patterns and names their owner:

| Criterion | Baton-pass | Isolated consultation |
| --- | --- | --- |
| Session topology | One session with changing active profiles | Parent session plus short-lived child session |
| Context | Selected target-necessary shared history | Minimized explicit consultation envelope; no parent transcript by default |
| Control transfer | Destination becomes active | Parent waits for a typed child result |
| Final-response owner | Destination profile | Parent profile/session |
| Best fit | The destination must finish the user-facing task and continue the workflow | The parent needs bounded expertise but retains task responsibility |
| Failure boundary | Transition state/checkpoint and shared-history validity | Child failure returns a typed failure without transferring ownership |

Use deterministic routing instead when the application selects one route before
starting a session and no ownership transfer occurs. Use transcript transfer
only when constructing a distinct session from explicit entries. Neither is
renamed baton-pass. Apple Foundation Models runtime Skills, Claude/Codex Agent
Skills, coding-session handoff, Apple Handoff, and App Intents remain separate.

The bounded non-positive preselection router is not a sixth workflow and is not
the runtime cost router. Positive workflow activation bypasses it. The cost
router runs only after an eligible host tool has already produced a result.

## Apple-first diagnostic cost route

The MVP runtime direction is one deterministic chain:

`host PostToolUse adapter -> deterministic cost router -> one local Swift Apple Foundation Models bridge -> host-visible result`

DEV-132 defines interfaces and ownership, not filesystem paths or production
code:

| Component | Exact boundary | Owner |
| --- | --- | --- |
| Runtime-cost benchmark and policy contract | Defines the versioned exact action/tool allowlists, selected command classes, minimum estimated-savings threshold, conservative maximum Apple payload, pairing rules, telemetry normalization, and release calculation. Unknown or unset policy data fails closed. | DEV-142 |
| Local Swift bridge | Accepts only a validated `condense_diagnostic_output` request, gates Apple availability and application data-policy permission, applies the policy-owned payload bound, requests a structured local result, and returns a validated result or normalized failure. | DEV-143 |
| Codex host adapter | Observes selected test/build/typecheck/lint result envelopes at `PostToolUse`, preserves the original result, invokes the deterministic router at most once, and renders the routed outcome. | DEV-144 |
| Claude host adapter | Applies the same `PostToolUse`, original-result, provenance, and no-rerun contract for Claude. | DEV-145 |
| Workflow integrations | Consume the proven chain without changing its route, bridge, or acceptance semantics. | DEV-139, DEV-140, DEV-141 |

The cost router requires all of the following before one bridge attempt: exact
action `condense_diagnostic_output`; membership in DEV-142's versioned action,
tool, and command-class allowlists; a selected test/build/typecheck/lint result
envelope; sufficient estimated savings under DEV-142's threshold; payload at or
below DEV-142's conservative Apple bound; explicit application data-policy
permission; trusted-local allowed fields with provenance; and current Apple
runtime availability. DEV-132 does not invent tool names, concrete commands,
or numeric policy bounds.

Ineligible, unavailable, unknown-policy, and router-decline paths return the
original result unchanged. Apple failure, timeout, cancellation, or invalid
output returns a bounded normalized error together with the original result.
No path reruns the original tool. Only a provenance-bound, schema-valid bridge
response may replace the host-visible diagnostic result. The bridge is never
the task or final-response owner.

Apple Foundation Models is the sole MVP local provider. Generic provider
interfaces, GLM, Kimi, local OpenAI-compatible servers, external providers,
PCC, credentials, paid services, and network surfaces are deferred. The route
cannot reduce the parent model's first turn because `PostToolUse` occurs after
the original tool result; it targets lower parent-model consumption on later
turns.

## Apple API and model boundaries

Runnable guidance uses the compile-checked SDK 26.5 core: sessions, on-device
availability/context, tools, runtime dynamic schemas, transcript Codable and
rehydration, streaming shapes, prewarm, and the stable versioned error surface.
Static `@Generable` and `@Guide` macros compile with the currently recorded
Xcode 26.6 / Swift 6.3.3 toolchain against SDK 26.5. The earlier Command Line
Tools macro failure is historical evidence only. Typechecking and offline
fixtures do not establish a live model or production bridge.

Dynamic instructions/profiles, generic models, PCC/custom providers, tool
calling mode, mutable transcript, history transforms, `.onToolCall`, transcript
error policy, Evaluations, Instruments, and Foundation Models runtime Skills
remain official OS/Xcode 27 beta references until a compatible host compiles or
runs them. Exact initializer snippets include official defaults or say they are
reduced. Stable and beta error taxonomies stay in separate tables; an exact
table includes associated-value payload signatures.

Default tests never require live model generation, Apple Intelligence
availability, PCC, a custom provider, credentials, entitlements, a paid
service, network access, device hardware, or full Xcode. A missing supported
prerequisite is an explicit blocker rather than a pass or blanket framework
failure.

## Canonical architecture output contract

Every positive workflow emits or updates a result with
`architectureSchemaVersion: "1.0"`. A human-readable rendering and normalized
machine-readable form share these required domains:

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

The `pattern` union includes routing and transcript transfer so review/debug
work can identify a mislabelled design, but a handoff design accepts only
`baton_pass` or `isolated_consultation` unless it explicitly concludes that the
request does not need a handoff.

Workflow-specific additions are:

- design: alternatives, decision rationale, proposed components/file changes,
  and implementation/test plan;
- implement: approved decision reference, exact change boundaries, compilation
  and regression results;
- review: severity, stable check ID, evidence, impact, and bounded correction
  for every finding;
- debug: observed/expected state, first divergence, root cause, correction, and
  regression proof; and
- validate: full layer matrix, counts, hashes, reviewer verdict, blockers,
  skips, and release implication.

Exact prose is not an acceptance contract. Schemas, stable IDs, required
sections, state facts, and security outcomes are.

## State, ownership, and lifecycle contract

Framework-neutral application state includes:

```text
stateVersion                monotonic concurrency/state revision
policyVersion               independent boundary-policy revision
phase                       stable | transitioning | recoveryRequired | terminated
activeProfile
provider
finalResponseOwner
allowedEdges
transitionCount / transitionBudget
toolCount / toolBudget
effectCount / effectBudget
contextEnvelope
providerGrant
pendingTransition
stableCheckpoint
effectLedger
auditEvents                 metadata only
```

Only a deterministic reducer consumes typed trusted events. Model output,
prompt text, retrieved context, repository text, summaries, and tool output are
untrusted proposals/data.

| Current phase | Trusted event | Required result |
| --- | --- | --- |
| `stable` | valid proposal | Validate phase first, versions, edge, budgets, grant, context; save checkpoint; enter `transitioning`; emit at most one command |
| `stable` | invalid proposal or untrusted text | No authority/state change and no executor command |
| `transitioning` | commit before external uncertainty | Activate destination, transfer owner only for baton-pass, increment `stateVersion`, return `stable` |
| `transitioning` | known pre-commit failure/cancellation | Restore checkpoint, clear pending state, return source identity to `stable` |
| `transitioning` | possible/confirmed external commit or uncertain cancellation | Record one effect identity, retain repair facts, enter `recoveryRequired` |
| `recoveryRequired` | explicit successful reconciliation | Establish external truth, resolve ledger truth, produce one valid stable state, then allow retry if policy/budget permit |
| `recoveryRequired` | replayed or late event | Preserve phase, authority, pending/checkpoint state, counts, effect ledger, and repair facts exactly; emit no command |
| `recoveryRequired` | no safe reconciliation path is currently available | Remain `recoveryRequired`, preserve the ledger and repair facts, and return an explicit repair-blocked/unavailable result until explicit reconciliation establishes external truth |
| `stable` | budget exhaustion or no safe available path | Enter `terminated` or return an explicit unavailable/degraded terminal result without expanding trust |

`policyVersion` changes only through a separate trusted policy operation.
Commit increments `stateVersion`, not `policyVersion`. Late or replayed events
cannot change authority, phase, pending state, checkpoint, counts, or ledger.
Unresolved recovery cannot be relabelled `terminated`; only explicit successful
reconciliation may establish external truth and leave `recoveryRequired`.
Transcript rollback never claims to undo an external effect. The guarantee is
application-controlled at-most-once command emission plus reconciliation,
never exactly-once external delivery.

## Trust, context, tools, and confirmation

Every field in a boundary envelope has a class and provenance:

- `C0 Public`: intentionally public but still purpose/destination limited;
- `C1 Task-private`: non-sensitive private task context, minimized to named
  fields;
- `C2 Sensitive`: personal, regulated, high-impact, or confidential; normally
  blocked for consultation/custom providers without a field-specific exception;
- `C3 Never-transfer`: credentials, signing material, unrelated private data,
  out-of-purpose content, or unsafe-to-classify values; never transferable.

A field records source, subject, purpose, destination, retention, and redaction.
Unknown data fails closed. A disallowed field rejects the complete envelope;
silent dropping is not authorization.

A provider grant binds person/session, source, destination, purpose, exact
classes/fields, tools, retention, expiry, `stateVersion`, and `policyVersion`.
Any binding change invalidates it. High-impact destructive, financial, public,
shared-content, irreversible, exfiltrating, or hard-to-undo effects require
immediate confirmation binding normalized action, arguments,
recipient/resource, versions, authority, effect budget, and idempotency key.
Authentication, permission, recipient/resource version, arguments, active
state, and grant are revalidated after confirmation and before execution.

Accepted tool results bind outstanding call ID, tool/version/provider, result
type, and current state. Model text and mismatched outputs cannot close a call.
Each logical effect has one stable ID/idempotency key and one ledger record.
Replay returns the recorded/reconciled outcome and emits no executor command.

## Availability, fallback, and provider truth

On-device, PCC, and every custom provider are separate boundaries. PCC
properties do not transfer to a custom provider. Absence of local tool-call
evidence from an opaque provider means `unknown`, not zero tool use.

Fallback is a trusted application decision. An already authorized on-device
path may be used only if it has equal-or-lower context, retention, tool, effect,
and provider authority. A new PCC/custom provider, broader context, additional
tools, or stronger effect capability requires a new matching grant. When no
safe route exists, return an explicit unavailable/degraded result.

## Evaluation and evidence contract

The evidence layers are independent:

1. mandatory deterministic offline checks with stable `D-*` IDs;
2. the exact human-owned seven-dimension rubric;
3. real-host Claude/Codex capability rows with `E-*` IDs; and
4. optional Xcode 27 Apple Evaluations/Instruments evidence.

The seven rubric dimensions are exactly:

1. pattern selection;
2. Apple API grounding and version labeling;
3. security-policy completeness;
4. context minimization;
5. failure and recovery behavior;
6. testability and observability; and
7. limitation honesty.

Scores are integers 1-4. Mean must be at least `3.0`; security-policy
completeness, failure/recovery behavior, and limitation honesty must each be at
least `3`. A human owns the semantic verdict. Deterministic validation owns
dimension set, hashes, anchors, arithmetic, and thresholds. A model judge is
optional supplementary evidence and cannot override a deterministic failure.

Plugin validation, discovery, installation, cache contents, enabled state, and
file presence are structural prerequisites only. Capability acceptance requires
fresh real tasks that observe correct skill activation, progressive reference
loading, complete output contracts, and valid/invalid outcomes in each host.

Every result status is `pass`, `fail`, `blocked`, or `not_applicable`. A zero
denominator yields `not_applicable` with null value. One host's pass does not
replace another host's blocker.

`E-RUNTIME-COST-001` is a paired live-runtime contract. Eligible rows preserve
separate null-capable `pluginOff` and `pluginOn` arms and a versioned
`providerNormalizationVersion`; missing or ambiguous telemetry, normalization,
pairing, policy, or live Apple evidence is `blocked`, never estimated. DEV-142
must prove the conjunction of at least 10% median total parent-model token
reduction across eligible workflows, zero correctness regressions, and zero
additional parent-model turns. DEV-138's deterministic Swift fixtures are
repository-only regression evidence and cannot satisfy this live gate.

Runtime/live-host logs, traces, and derived capability telemetry may contribute
only normalized metadata to committed evidence; their raw/source content is
excluded. The canonical DEV-131 allowlist separately permits a hash-bound
synthetic or approved-redacted rubric stimulus, rubric assessments with only
the bounded rationales required for review, and a redacted summary. Those
artifacts must pass the DEV-131 path, content, structured-key, classification,
and hash scanners before commit.

Raw/live prompts, responses, reasoning, tool arguments/results, credentials,
private configuration, real user or third-party data, raw host/machine identity,
literal executable paths, raw `PATH`, raw blocker diagnostics, `.trace`, and
`.xcresult` remain excluded.
Normalized `<host-path>` executable identity plus a strict exact version or
`null` is the only committed path-identity exception. Raw Instruments traces
and any other
authorized live-host artifact remain outside the repository under separately
approved access, retention, redaction, and deletion policy.

## Design-level E2E scenario suite

### Scenario 1: new baton-pass design

**Representative request:** “Design a Foundation Models flow where a research
profile gathers evidence and a review profile takes over and answers the user.”

1. Activation selects `design-apple-foundation-models-handoff` because the
   request asks for a new handoff architecture.
2. The workflow inspects repository and SDK evidence, labels SDK 26.5 compiled
   primitives separately from OS/Xcode 27 dynamic-profile guidance, and does
   not invent a `BatonPass` type.
3. Pattern selection chooses `baton_pass`: one session, selected shared
   history, source `research`, destination `review`, final owner `review`.
4. The result defines the reducer state, valid `research -> review` edge,
   independent versions, finite transition/tool budgets, target-necessary
   context, grants/confirmation, availability fallback, and recovery.
5. Safety checks require no C3 crossing, no model-created authority, and no
   effect without typed confirmation/provenance.
6. Verification expects `D-ROUTE-001`, `D-OWNER-001`, `D-TRANSITION-001`,
   `D-CONTEXT-*`, `D-GRANT-001`, and safe-evidence checks to pass. Destination
   final ownership is unambiguous.

### Scenario 2: existing implementation review

**Representative request:** “Review this handoff reducer; it lets either profile
answer, has no transition limit, and copies the full transcript.”

1. Activation selects `review-apple-foundation-models-handoff` because an
   existing implementation is being evaluated.
2. The workflow reconstructs the intended pattern and normalized state rather
   than beginning a redesign.
3. It emits at least three evidence-backed findings:
   `D-OWNER-001` for ambiguous/wrong final owner,
   `D-TRANSITION-001` for no finite transition budget, and
   `D-CONTEXT-001`/`D-CONTEXT-002` for missing inclusion/exclusion policy.
4. It also checks independent versions, phase gating, tool/effect policy,
   recovery, fallback, API labels, and fixture/evidence claims.
5. Output contains severity, exact evidence, impact, and bounded correction;
   it does not claim success from compilation or file presence.
6. Verification passes only when the deliberately flawed input is rejected
   with the intended IDs and the review retains limitation/blocker honesty.

### Scenario 3: baton-pass versus isolated consultation

**Representative request:** “My main session should ask a specialist a narrow
question, then keep control and write the final answer. Should this be a
handoff?”

1. Activation selects `design-apple-foundation-models-handoff` because the
   user asks for a pattern decision in a new architecture.
2. The selection table rejects baton-pass: the destination must not become the
   final owner and full/shared session history is unnecessary.
3. It chooses `isolated_consultation`: short-lived child session, minimized
   consultation envelope, independent child transcript, typed result, parent
   control and final ownership.
4. It distinguishes consultation from deterministic routing, transcript
   transfer, runtime Skills, and coding-agent handoff.
5. Failure returns a typed child failure to the parent without changing the
   active/final owner or silently escalating provider trust.
6. Verification asserts parent final ownership, context minimization, child
   transcript isolation, and no unauthorized child tool/effect.

### Scenario 4: failed transition and security boundary

**Representative request:** “The model wants to send a credential-bearing
summary to a custom provider; after dispatch timed out, it proposes retrying.”

1. Activation selects `debug-apple-foundation-models-handoff` for the observed
   failure; `validate` may then run the regression matrix.
2. The C3 credential field rejects the complete provider envelope. No grant can
   authorize C3 and no executor command is emitted.
3. If a separate allowed effect had already been dispatched before the timeout,
   the state records one effect ID and enters `recoveryRequired`; it does not
   claim rollback.
4. A replay of the same effect ID emits no second command. Explicit
   reconciliation must establish external truth before retry or stable repair.
5. Custom-provider fallback is rejected without a matching destination/purpose/
   field/tool/retention/version grant. Equal-or-lower authorized on-device
   degradation is allowed; otherwise the result is unavailable.
6. Evidence contains classes, synthetic IDs, counts, decisions, and blocker
   states only. The credential, raw prompt, provider payload, and trace do not
   enter committed evidence.

### Scenario 5: out-of-domain non-activation

An out-of-domain request reaches the bounded preselection router only after no
positive workflow matches. It returns exactly `no_activation`, invokes no
workflow, loads no reference, emits no `architectureResult`, and performs no
tool, effect, command, hook, agent, or Apple operation.

### Scenario 6: bounded clarification

A request whose domain or approved implementation contract is ambiguous reaches
the same non-positive router and returns exactly `clarification_required` with
one bounded question. It performs none of the prohibited Scenario 5 actions;
the answer is classified as a new input rather than resuming hidden state.

### Scenario 7: Apple diagnostic route and fallback

A synthetic selected diagnostic result arrives after one original test/build/
typecheck/lint tool execution. The `PostToolUse` adapter checks exact action
`condense_diagnostic_output` and every versioned DEV-142 policy gate before at
most one local bridge request. A validated bridge response may replace the
visible result. Decline, ineligibility, unavailability, or unknown policy keeps
the original unchanged; failure returns a normalized error plus the original.
Every branch records zero original-tool reruns and makes no first-parent-turn
savings claim.

Every scenario has one deterministic route or activation decision, one
pattern/failure path, one owner result, one safety result, and a reproducible
validation boundary. There is no unresolved alternative in the expected flow.

## Local development and host acceptance

A host row selects one explicit executable or records the first executable
resolved from its controlled `PATH` before validation starts. Every operation
in that row invokes the captured executable. Resolution is checked again before
the row finishes. Before operations, a missing or non-runnable executable,
unavailable version, or exact approved-baseline version mismatch produces a
normalized `blocked` row; the alternate installed version cannot substitute.
After a successful capture, resolution or version drift is `fail`, invalidates
the evidence, and requires a fresh run. Committed evidence identifies the
captured executable as normalized `<host-path>` plus its exact observed version
or `null`. Literal local executable paths and the raw `PATH` are never committed.
Only strict single-line Claude/Codex version formats may enter evidence;
malformed, multiline, or path-bearing output normalizes to `null` with a stable
reason and is never echoed. Raw blocker diagnostics stay transient. Committed
blocker evidence contains only probe identity, exit code, normalized status,
and a stable `diagnosticClass` after the expected error class is verified.

Each downstream host issue owns its current approved executable/model matrix.
Historical DEV-132 host observations establish provenance only. Version output
establishes an executable prerequisite, never plugin loading, activation,
capability, or runtime-cost proof.

DEV-135 owns structural generation/schema/install proof. DEV-139 owns fresh
real task activation/reference/output proof. Neither issue may report discovery
as capability. If automation, model access, or authentication needed for a real
host row is unavailable, that row is blocked with exact evidence.

## Commit and issue boundaries

DEV-132 may add only its approved design, plan, decision record, and normalized
design-scenario evidence. It does not create production manifests, skills,
references, schemas, generators, tests, or Swift fixtures. Those paths in the
proposed tree are contracts for downstream issues, not files created here.

The DEV-132 change integrates atomically against current `main`. Verify the
exact allowed path set, rerun the current DEV-128 SDK matrix, DEV-130 security
oracle, and DEV-131 evaluation suite, then obtain fresh whole-issue review.

## Completion criteria

DEV-132 is complete only when:

- this canonical spec and a durable decision log agree;
- every decision includes source, rationale, and downstream impact;
- the selected root placement and fallback trigger are unambiguous;
- the proposed file trees match the ownership model;
- all seven scenario walkthroughs pass independent consistency review;
- DEV-133 through DEV-145 contain the decisions they inherit; in particular,
  DEV-136/137 and DEV-139 through DEV-145 carry the amended routing/runtime
  contracts while generated artifacts retain their canonical ownership rules;
- existing DEV-128/130/131 regression gates still pass;
- each host row records normalized `<host-path>` identity and exact version,
  emits prerequisite blockers before exit, uses one captured executable
  throughout, and fails/invalidates resolution or version drift;
- unsupported host/toolchain capabilities remain explicit blockers; and
- the issue-scoped branch/PR contains no production implementation.
