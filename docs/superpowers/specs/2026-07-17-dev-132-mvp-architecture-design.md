# DEV-132 Apple Foundation Models Handoff MVP Architecture Design

Issue: [DEV-132](https://linear.app/devprentice/issue/DEV-132/d1-synthesize-research-into-the-mvp-architecture-and-decision-record)

Decision date: `2026-07-17`

Stack base: `3792e8c98a387b7f9c48bd210d25938b40cdd5fe`

## Purpose

This specification is the canonical MVP architecture for a cross-compatible
Claude Code and Codex plugin that helps Apple-platform engineers design,
implement, review, debug, and validate Apple Foundation Models handoff
architectures. It resolves the repository, Apple API, production-pattern,
security, and evaluation decisions established by DEV-127 through DEV-131.

The plugin produces coding guidance and reviewable proof contracts. It does not
run a handoff, implement application authorization, provide a reusable Swift
runtime, or make a probabilistic model authoritative for transitions or
effects.

## Source decisions and authority

The following reviewed issue heads are binding inputs:

| Issue | Reviewed head | Authority used here |
| --- | --- | --- |
| DEV-127 | `191e2da63b863b367341a614c1ea1d9b4a032cd7` | The authoritative fork started as a three-document repository with no inherited plugin/generation architecture. |
| DEV-128 | `4f0b66ef7061d842f333e2749e74614f5331c915` | SDK 26.5 compile-checked core, separately labelled OS/Xcode 27 beta surface, and distinct orchestration patterns. |
| DEV-129 | `3db33eb957326b4d22ebe482c21925dd23b03af0` | One physical skill tree, narrow workflows, explicit generated Codex artifacts, host-specific loading, and no custom worker by default. |
| DEV-130 | `5e27a1c81a4c45199c912a5cbb750a30a8c7bf17` | Fail-closed reducer, context/grant/effect boundaries, recovery, fallback, metadata-only runtime evidence, and safe synthetic proof. |
| DEV-131 | `3792e8c98a387b7f9c48bd210d25938b40cdd5fe` | Deterministic/rubric/real-host evidence separation, stable IDs, safe evidence, and explicit blocker semantics. |

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
the installed Claude Code `2.1.91` and Codex `0.144.5` hosts. The effective
cached payload must exclude repository-only fixtures, tests, research, and
private repository state; none may be exposed as plugin capabilities.

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

MVP does not provide:

- application runtime orchestration, authentication, authorization, encryption,
  persistence, networking, UI, or provider integration;
- a reusable Swift package or sample application;
- automatic PCC/custom-provider use, credentials, entitlements, or paid
  services;
- App Intents, Apple Handoff, generic Core ML/Apple Intelligence education, or
  coding-session handoff;
- a custom agent, hook, command, MCP server, app, or runtime dependency; or
- release, publishing, tagging, merging, or marketplace distribution.

## Skill catalog and activation ownership

The MVP contains exactly five entry skills:

| Skill directory | Activates for | Does not activate for | Primary output |
| --- | --- | --- | --- |
| `design-apple-foundation-models-handoff` | New or revised handoff architecture, topology, pattern, boundary, or state design | Generic Swift, general Foundation Models questions, App Intents, Apple Handoff | Complete architecture contract and implementation-ready decision record |
| `implement-apple-foundation-models-handoff` | Translating an approved handoff contract into application code/tests | Architecture work without an approved contract, unrelated feature coding | Scoped implementation plan/change set plus compile/test evidence |
| `review-apple-foundation-models-handoff` | Reviewing a proposal, code, fixture, or evidence bundle for contract/API/security violations | Style-only review or unrelated Apple code review | Severity-ranked findings with stable check IDs and proof |
| `debug-apple-foundation-models-handoff` | Diagnosing routing, ownership, transition, context, tool, recovery, or availability failure | Generic crash debugging without a handoff boundary | Root-cause statement, state/evidence trace, bounded fix and regression proof |
| `validate-apple-foundation-models-handoff` | Running deterministic, compile, schema, generation, evidence, or cross-host acceptance gates | File-presence or Markdown-only success claims | Per-layer pass/fail/blocked/not-applicable matrix and safe evidence bundle |

DEV-134 owns the final activation prose, positive/negative/ambiguous prompts,
and workflow-specific output details without changing these five names or their
non-overlapping responsibilities. A skill must not depend on another skill
being invoked; all five load common references directly.

No plugin-local worker is justified. The workflows use the host's active agent
and share the same domain contract. There is no distinct role, isolated context,
tool set, or responsibility that requires a custom worker. A per-skill
`agents/openai.yaml`, if required after host validation, is presentation and
activation metadata only.

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

## Apple API and model boundaries

Runnable guidance uses the compile-checked SDK 26.5 core: sessions, on-device
availability/context, tools, runtime dynamic schemas, transcript Codable and
rehydration, streaming shapes, prewarm, and the stable versioned error surface.
Static macros remain blocked under the installed Command Line Tools because
`FoundationModelsMacros` is missing; runtime dynamic schema is the locally
compiled structured-output path.

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

Runtime/live-host logs, traces, and derived capability telemetry may contribute
only normalized metadata to committed evidence; their raw/source content is
excluded. The canonical DEV-131 allowlist separately permits a hash-bound
synthetic or approved-redacted rubric stimulus, rubric assessments with only
the bounded rationales required for review, and a redacted summary. Those
artifacts must pass the DEV-131 path, content, structured-key, classification,
and hash scanners before commit.

Raw/live prompts, responses, reasoning, tool arguments/results, credentials,
private configuration, real user or third-party data, host identity, `.trace`,
and `.xcresult` remain excluded. Raw Instruments traces and any other authorized
live-host artifact remain outside the repository under separately approved
access, retention, redaction, and deletion policy.

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

Every scenario has one activation, one pattern/failure path, one owner result,
one safety result, and a reproducible validation boundary. There is no
unresolved alternative in the expected flow.

## Local development and host acceptance

Claude Code `2.1.91` supports structural validation and session-only
`--plugin-dir`; packaging/cache tests use an isolated `CLAUDE_CONFIG_DIR`, local
marketplace registration, install, and enabled-state inspection. Codex
`0.144.5` rejects `codex --plugin-dir`; it uses an isolated `CODEX_HOME`, local
marketplace registration, plugin add/install, enabled-state inspection, and a
fresh task.

DEV-135 owns structural generation/schema/install proof. DEV-139 owns fresh
real task activation/reference/output proof. Neither issue may report discovery
as capability. If automation, model access, or authentication needed for a real
host row is unavailable, that row is blocked with exact evidence.

## Commit and issue boundaries

DEV-132 may add only its approved design, plan, decision record, and normalized
design-scenario evidence. It does not create production manifests, skills,
references, schemas, generators, tests, or Swift fixtures. Those paths in the
proposed tree are contracts for downstream issues, not files created here.

The DEV-132 PR is stacked on DEV-131 and contains separately reviewable commits
for design, plan, decision/evidence artifacts, and narrow review corrections.
Before opening it, rebase onto the final reviewed DEV-131 head, verify issue
blobs and the exact allowed path set, rerun the existing SDK 26.5, security, and
evaluation regression gates, and obtain fresh whole-issue review.

## Completion criteria

DEV-132 is complete only when:

- this canonical spec and a durable decision log agree;
- every decision includes source, rationale, and downstream impact;
- the selected root placement and fallback trigger are unambiguous;
- the proposed file trees match the ownership model;
- all four scenario walkthroughs pass independent consistency review;
- DEV-133 through DEV-141 contain the decisions they inherit;
- existing DEV-128/130/131 regression gates still pass;
- unsupported host/toolchain capabilities remain explicit blockers; and
- the issue-scoped branch/PR contains no production implementation.
