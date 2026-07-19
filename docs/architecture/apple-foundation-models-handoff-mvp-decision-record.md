# Apple Foundation Models Handoff MVP Decision Record

Decision date: `2026-07-17`; July 18 amendment integrated on `2026-07-19`

Issue: [DEV-132](https://linear.app/devprentice/issue/DEV-132/d1-synthesize-research-into-the-mvp-architecture-and-decision-record)

## Decision status and scope

Status: **approved, with evidence-gated package placement**.

This is a compact, non-authoritative durable index of sources, decisions,
rationales, and downstream impacts. The canonical design and source reports
control exact detailed contracts and win if this index shorthand differs. See
the
[canonical design](../superpowers/specs/2026-07-17-dev-132-mvp-architecture-design.md).
A decision change updates DEV-132, its canonical design, this index, and
affected downstream Linear issues before implementation.

The source artifacts on current `main` are binding. Earlier reviewed heads and
host observations remain historical provenance only.

| Source | Decision and rationale | Impact |
| --- | --- | --- |
| [DEV-127](../research/dev-127-repository-architecture.md) | The authoritative fork began with three documents and no inherited plugin/generation model; upstream is reference only. | Choose every ownership, path, runtime, and proof boundary explicitly. |
| [DEV-128](../research/dev-128-foundation-models-api-map.md) | Six SDK 26.5 positives and two strict blockers separate compile/interface evidence from live runtime proof. | Treat current Xcode 26.6 / Swift 6.3.3 / SDK 26.5 observations as bounded evidence only. |
| [DEV-129](../research/dev-129-production-pattern-comparison.md) | One physical capability corpus plus generated Codex metadata avoids provider drift. Its original no-router/no-worker choice is scoped to guidance work. | Preserve five positive workflows while permitting the later approved bounded routers and runtime chain. |
| [DEV-130](../research/dev-130-handoff-threat-model.md) | Eight deterministic cases prove fail-closed state/security behavior and diagnostic-result routing without shipping a runtime. | Preserve provenance, original-result fallback, recovery, and no original-tool rerun. |
| [DEV-131](../research/dev-131-evaluation-strategy.md) | Twenty-six tests and eleven cases separate deterministic, rubric, real-host, Apple, and paired cost evidence. | Preserve null-capable `pluginOff`/`pluginOn` arms, `providerNormalizationVersion`, blocker honesty, and the 10%/0/0 floor. |

DEV-132 provides architecture guidance and proof contracts only. Production
routers, host adapters, and the Swift bridge are downstream-owned. A
probabilistic model never owns routing, application policy, or effects.

## Users and workflows

Plugin ID: `apple-foundation-models-handoff`. Display name:
**Apple Foundation Models Handoff**. Users are Apple-platform engineers,
architects, reviewers, and maintainers working in Claude Code or Codex.

The five non-overlapping positive workflow entries are fixed:

| Exact skill directory | Owns |
| --- | --- |
| `design-apple-foundation-models-handoff` | New or revised architecture, topology, pattern, state, and boundary decisions |
| `implement-apple-foundation-models-handoff` | Application changes and tests tied to an approved architecture |
| `review-apple-foundation-models-handoff` | Evidence-backed contract/API/security findings with stable IDs |
| `debug-apple-foundation-models-handoff` | First divergence, root cause, bounded correction, and regression proof |
| `validate-apple-foundation-models-handoff` | Deterministic, compile, schema, generation, evidence, and host matrices |

This DEV-132 change explicitly excludes:

- application runtime orchestration, authentication, authorization,
  encryption, persistence, networking, and UI;
- automatic PCC/custom-provider use, credentials, entitlements, and paid
  services;
- a reusable Swift package/sample app, App Intents, Apple Handoff, generic
  Core ML/Apple Intelligence education, and coding-session handoff;
- production source for the approved routers, host hooks/adapters, or local
  Swift bridge; and
- release, publishing, tagging, merging, and marketplace distribution.

## Skill and reference architecture

Both hosts use one provider-neutral physical `skills/` corpus and one shared
`references/` corpus. Skills load common references directly and do not require
another skill invocation. DEV-129's no-worker decision remains scoped to these
guidance workflows; per-skill `agents/openai.yaml`, if host proof requires it,
is presentation/activation metadata only.

Exactly one bounded non-positive preselection router runs only when no positive
workflow matches. Its only outcomes are `no_activation` for out-of-domain input
and `clarification_required` for bounded domain/approved-contract ambiguity.
Positive prompts bypass it and activate exactly one of the five workflows. The
router may not invoke a workflow, load references, emit `architectureResult`,
use tools/effects, make Apple claims, or introduce commands, agents, hooks, or
broader routing.

| Proposed reference | Sole concern owner |
| --- | --- |
| `references/architecture-and-state.md` | Result schema, state, ownership, lifecycle, retry, and repair |
| `references/orchestration-patterns.md` | Baton-pass, consultation, routing, transcript transfer, and selection |
| `references/apple-api-availability.md` | SDK 26.5, OS/Xcode 27 beta, errors, availability, providers, and runtime Skills |
| `references/security-context-and-recovery.md` | Trust, C0-C3, grants, confirmation, provenance, effects, recovery, fallback, and traces |
| `references/evaluation-and-observability.md` | D/E IDs, datasets, rubric, evidence, hosts, Evaluations, Instruments, and blockers |

DEV-134 may refine these filenames only if every concern retains one owner and
every skill-to-reference link remains deterministic and direct. DEV-137 owns
reference content. Repository fixtures remain test evidence, not capability
content.

## Canonical and generated ownership

| Artifact/domain | Ownership | Edit rule |
| --- | --- | --- |
| `CLAUDE.md` | Provider-neutral repository/plugin guidance | Authored canonical input |
| Effective `.claude-plugin/plugin.json` | Shared identity | Authored canonical input |
| `.claude-plugin/marketplace.json` | Claude marketplace and selected source | Authored canonical input |
| Effective `metadata/codex-interface.json` | Codex `interface`, including presentation `category` | Authored canonical input |
| `metadata/codex-marketplace.json` | Codex source/order and marketplace-only `plugins[].category`/`plugins[].policy` | Authored canonical input |
| `skills/**`, `references/**` | Only provider-neutral capability corpus | Authored; never mirrored into generated host trees |
| `AGENTS.md` | Bounded adapter derived from `CLAUDE.md` | Generated; never edit directly |
| Effective `.codex-plugin/plugin.json` | Shared identity plus Codex interface input | Generated; never edit directly |
| `.agents/plugins/marketplace.json` | Shared identity plus Codex marketplace input | Generated; never edit directly |

`plugin.json.interface.category`, marketplace `plugins[].category`, and
marketplace `plugins[].policy` stay in their distinct schema layers. One Python
3 standard-library sync command owns deterministic write/check modes, validates
inputs/outputs, and fails on drift or untracked generated paths. Native host
validators and the pinned stricter OpenAI validator remain separate gates.

## Selected package placement and fallback

The selected candidate uses marketplace source `./` only after DEV-135 and
DEV-139 prove cached-install integrity and fresh activation/reference loading
on their current issue-approved host matrix. Each row pins one executable
before operations and invalidates on resolution drift. Earlier host versions
recorded in DEV-132 are historical evidence only. Repository-only fixtures,
tests, research, and private
repository state must be absent from effective cached payload content and must
not appear as plugin capabilities.

Complete root candidate:

```text
.
├── CLAUDE.md
├── AGENTS.md                                      # generated
├── .claude-plugin/
│   ├── plugin.json                                # canonical shared identity
│   └── marketplace.json                           # source ./
├── .codex-plugin/plugin.json                      # generated
├── .agents/plugins/marketplace.json               # generated
├── metadata/
│   ├── codex-interface.json                       # canonical
│   └── codex-marketplace.json                     # canonical
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
├── scripts/sync_generated_artifacts.py
├── tests/
│   ├── test_generated_artifacts.py
│   ├── test_plugin_contract.py
│   └── e2e/
├── fixtures/                                      # repository-only
└── docs/
```

Fallback is mandatory if a host rejects root placement, required content is
omitted or resolves outside the cached package, repository-only material is
included in the effective cached payload, or real activation/reference loading
fails. The fallback source is
`./plugins/apple-foundation-models-handoff`; it changes placement only and has
no symlink outside its package.

Complete conventional fallback:

```text
.
├── CLAUDE.md
├── AGENTS.md                                      # generated repository adapter
├── .claude-plugin/marketplace.json                # fallback source
├── .agents/plugins/marketplace.json               # generated
├── metadata/codex-marketplace.json                # canonical
├── plugins/apple-foundation-models-handoff/
│   ├── .claude-plugin/plugin.json                 # canonical shared identity
│   ├── .codex-plugin/plugin.json                  # generated
│   ├── metadata/codex-interface.json              # canonical
│   ├── skills/                                    # same five skills
│   └── references/                                # same concern owners
├── schemas/
├── scripts/sync_generated_artifacts.py
├── tests/
├── fixtures/                                      # outside plugin package
└── docs/
```

### Host executable identity

Each Claude/Codex host row selects an explicit executable or records the first
executable resolved from its controlled `PATH` before any operation. The row
invokes only that captured executable and rechecks resolution before it
finishes. Before operations, a missing or non-runnable executable, unavailable
version, or approved-baseline version mismatch is a normalized `blocked` row;
the alternate installed version cannot substitute. After a successful capture,
resolution or version drift is `fail` and invalid evidence. Committed evidence
records normalized executable identity `<host-path>` plus exact observed
version or `null`. It never records a literal executable path or raw `PATH`.
Only strict single-line Claude/Codex version formats may enter committed
evidence; malformed, multiline, or path-bearing output normalizes to `null`
with a stable reason and is never echoed. Raw blocker diagnostics stay
transient. A committed blocker row contains only probe identity, exit code,
normalized status, and verified stable `diagnosticClass`.

Each downstream host issue owns its current approved executable/model matrix.
Version output proves only that a captured executable prerequisite is present;
historical or alternate host observations never prove loading, activation,
reference use, capability, or runtime savings.

## Handoff patterns and Apple API boundary

| Pattern | Context/topology | Control and final owner |
| --- | --- | --- |
| `baton_pass` | One session; target-necessary selected history across active profiles | Destination becomes active and owns the final response |
| `isolated_consultation` | Parent plus short-lived child; minimized envelope; independent child transcript | Parent receives a typed result and retains control/final ownership |

Deterministic routing chooses before a session; transcript transfer constructs a
distinct session from selected entries. Neither is renamed baton-pass. Runtime
Foundation Models Skills, Claude/Codex Agent Skills, coding-session handoff,
Apple Handoff, and App Intents remain separate concepts.

The non-positive preselection router is not a sixth workflow. A separate
runtime cost router runs only after a selected host tool result exists.

### Diagnostic cost-routing chain

The approved downstream chain is:

`host PostToolUse adapter -> deterministic cost router -> one local Swift Apple Foundation Models bridge -> host-visible result`

| Owner | Interface responsibility |
| --- | --- |
| DEV-142 | Versioned exact action/tool allowlists and selected command classes; minimum estimated-savings threshold; conservative maximum Apple payload; paired cost/correctness contract and release calculation. Unknown or unset inputs fail closed. |
| DEV-143 | The sole production local Swift Apple bridge: availability/data-policy/payload gating, structured local generation, validation, cancellation/deadline handling, and normalized failure. |
| DEV-144 | Codex `PostToolUse` adapter, provenance binding, original-result preservation, at-most-one route attempt, and rendering. |
| DEV-145 | Claude adapter with the same trigger, provenance, fallback, and no-rerun contract. |
| DEV-139/140/141 | Integrate and accept the proven components without changing their semantics. |

The exact action is `condense_diagnostic_output`. Eligibility is limited to
selected test/build/typecheck/lint result envelopes and requires the current
DEV-142 versioned action, tool, and command-class allowlists, sufficient
estimated savings under its threshold, payload within its conservative Apple
bound, explicit application data-policy permission, trusted-local field
provenance, and current Apple runtime availability. DEV-132 invents no tool
names, concrete commands, numeric policy bounds, or runtime filesystem paths.

Ineligible, unavailable, unknown-policy, and decline paths return the original
result unchanged. Failure, timeout, cancellation, or invalid Apple output
returns a bounded normalized error plus the original result. No branch reruns
the original tool. Only a provenance-bound valid response may replace the
host-visible result; the bridge never owns the task or final response.

Apple Foundation Models is the sole MVP local provider. Generic provider
interfaces, GLM, Kimi, local OpenAI-compatible servers, external providers,
PCC, credentials, paid services, and network surfaces are deferred. Because
the route begins at `PostToolUse`, it makes no first-parent-turn savings claim;
it targets lower subsequent parent-model consumption.

SDK 26.x is only the architecture-family boundary. Checked claims use the exact
labels below:

| Evidence label | Boundary |
| --- | --- |
| **Compiled SDK 26.5** | Checked fixture compiles/runs; an uninvoked function proves shape only |
| **Interface-verified SDK 26.5** | Pinned declaration exists; behavior did not run |
| **Official OS 27 beta, locally unverified** | Apple publishes it; SDK 26.5 cannot prove it locally |
| **Pseudocode / deterministic mock** | Application orchestration, not an Apple type or model result |
| **Blocked** | Named SDK/module/macro/entitlement/binary/target is unavailable |

The SDK 26.5 runnable core and OS/Xcode 27 beta API inventory are owned by
DEV-128. Beta tool-calling mode exposes static values: `.allowed` is the
documented default and `.required` needs an exit path. Failed/cancelled requests
default to transcript reversion; `.preserveTranscript` makes the application
own validation, redaction, incomplete call/output repair, and reuse safety.
Never mutate a transcript while its session is responding. Default tests need
no live model, PCC/provider, credentials, network, paid service, hardware, or
full Xcode; missing prerequisites are narrow blockers.

Current Xcode 26.6 / Swift 6.3.3 / SDK 26.5 evidence includes six positive
fixtures, including static macro expansion, plus two strict expected blockers.
The prior Command Line Tools macro failure is historical only. None of these
fixtures proves a live Apple response or the production bridge.

## State, trust, effects, and recovery

The authoritative design owns exact types. Required state includes independent
`stateVersion`/`policyVersion`; phase
`stable|transitioning|recoveryRequired|terminated`; one stable active
profile/provider and final owner; valid edges and finite transition/tool/effect
budgets; classified context and bound grant; pending transition/checkpoint;
effect ledger; and metadata-only audit events.

| Phase | Trusted event | Required result |
| --- | --- | --- |
| `stable` | Valid proposal | Validate phase first, versions, edge, budgets, grant, and context; checkpoint; enter `transitioning`; emit at most one command |
| `stable` | Invalid proposal/untrusted text | Preserve state/authority; emit no command |
| `transitioning` | Commit before uncertainty | Activate destination; transfer owner only for baton-pass; increment `stateVersion`; return `stable` |
| `transitioning` | Known pre-commit failure/cancellation | Restore checkpoint/source identity and return `stable` |
| `transitioning` | Possible/confirmed external commit or uncertain cancellation | Record one effect/repair facts and enter `recoveryRequired` |
| `recoveryRequired` | Explicit successful reconciliation | Establish external truth, resolve ledger truth, produce one valid stable state, then consider retry |
| `recoveryRequired` | Late/replayed event | Preserve authority, phase, pending/checkpoint, counts, ledger, and repair facts; emit no command |
| `recoveryRequired` | No safe reconciliation path currently available | Remain `recoveryRequired`; return repair-blocked/unavailable until explicit successful reconciliation |
| `stable` | Budget exhaustion or no safe available path | Enter `terminated` or return unavailable/degraded without expanding trust |

`policyVersion` changes only through a separate trusted policy operation; a
handoff commit increments `stateVersion`, not `policyVersion`.

Ordinary budget/no-safe-path termination applies only from `stable`. Unresolved
recovery is never relabelled `terminated`. A no-safe-reconciliation outcome
changes no recovery fact. Failure/cancellation authority exists only in
`transitioning`.

All model/context/tool text is untrusted. The application reducer alone consumes
typed trusted events. Every field has provenance and class C0 public, C1
task-private, C2 sensitive, or C3 never-transfer; unknown/disallowed data rejects
the entire envelope. A grant binds person/session, source/destination, purpose,
fields/classes, tools, retention, expiry, and both versions. Immediate
confirmation for high-impact effects binds action/arguments/resource/authority/
budget/idempotency and is followed by authentication and permission rechecks.

Accepted tool results bind call ID, tool/version/provider, type, and state. Each
logical effect has one ID/key and ledger record; replay emits no executor
command. The guarantee is application-controlled at-most-once command emission
plus reconciliation, never exactly-once delivery or external-effect rollback.
Fallback is trusted and may use only an already authorized equal-or-lower
context, retention, tool, effect, and provider boundary. Any expansion requires
a new matching grant; without one, return unavailable/degraded.

## Output and evidence contracts

Every positive result uses `architectureSchemaVersion: "1.0"` with:

```text
workflow, scope, pattern
source = { profile, provider }
destination = { profile, provider }
finalResponseOwner
apiAvailability[] = { surface, versionLabel, compileStatus, source }
stateModel, trustBoundaries[], contextPolicy
toolAndEffectPolicy, failurePolicy
verification[] = { id, layer, status, evidence }
limitations[]
```

The pattern union is `baton_pass|isolated_consultation|deterministic_routing|
transcript_transfer`; positive handoff design selects the first two unless it
concludes no handoff is needed. Design adds alternatives/rationale/plan;
implement adds approved-decision/change/compile results; review adds
severity/ID/evidence/impact/correction; debug adds expected/observed divergence,
cause, fix, and regression; validate adds layer counts/hashes/verdict/blockers/
skips/release implication.

Evidence layers remain independent: mandatory deterministic D checks; the human
seven-dimension rubric; real-host E rows; and optional Apple
Evaluations/Instruments. The D catalog is `D-SCHEMA-001`, `D-ROUTE-001`,
`D-OWNER-001`, `D-TRANSITION-001`, `D-TOOL-001`, `D-CONTEXT-001`,
`D-CONTEXT-002`, `D-GRANT-001`, `D-PHASE-001`, `D-EFFECT-001`,
`D-EFFECT-002`, `D-FALLBACK-001`, `D-EVIDENCE-001`, and `D-RUBRIC-001`.
Per-case expected outcomes are in the corpus index. Stable IDs and the
evaluator, rubric, and invariant contracts are owned by the runner, tests, and
evaluation documentation.

Stable E ownership and boundaries:

- `E-CLAUDE-LOAD-001` / `E-CODEX-LOAD-001` — host structure passes only for a
  captured, resolution-stable executable with normalized `<host-path>` identity
  and exact version plus isolated exact-candidate loading/cache integrity;
  missing/non-runnable executable, unavailable/wrong approved version, missing
  candidate/prerequisite, or unavailable isolation blocks before operations;
  resolution/version drift after successful capture fails and invalidates.
- `E-CLAUDE-ACTIVATE-001` / `E-CODEX-ACTIVATE-001` — DEV-139 capability passes
  only for fresh activation, routed references, versioned output, and invalid
  rejection; blocked loading/model/session/auth/automation blocks.
- `E-CROSSHOST-STRUCT-001` — generation passes only when both host artifacts
  derive from canonical inputs and validate without drift; missing topology,
  generator, candidate, or validator blocks.
- `E-CROSSHOST-CAP-001` — paired capability passes only when both activation
  rows and normalized semantics agree; either host blocker blocks equivalence.
- `E-APPLE-EVAL-001`, `E-APPLE-INSTR-001`, and `E-APPLE-HOST-001` — optional
  Apple evidence requires compatible authorized Xcode 27 modules/tooling and a
  target; any missing prerequisite blocks and documentation is not a substitute.

Rubric dimensions are exactly: pattern selection; Apple API grounding and
version labeling; security-policy completeness; context minimization; failure
and recovery behavior; testability and observability; and limitation honesty.
Scores are integers 1-4, mean is at least `3.0`, and security, failure/recovery,
and limitation honesty are each at least `3`. A human owns the semantic verdict;
deterministic validation owns exact dimensions, stimulus hash, anchors,
arithmetic, and thresholds. A model judge cannot override deterministic failure.

`E-RUNTIME-COST-001` requires paired live `pluginOff` and `pluginOn` arms with
nullable provider input/cached-input/output/reasoning fields and a versioned
`providerNormalizationVersion`. Missing telemetry, normalization, pairing,
policy, or live Apple prerequisites is `blocked`, never estimated. DEV-142
acceptance is the conjunction of at least 10% median total parent-model token
reduction across eligible workflows, zero correctness regressions, and zero
additional parent-model turns. DEV-138 fixtures are repository-only
deterministic evidence, not runtime or savings proof.

Statuses are only `pass`, `fail`, `blocked`, and `not_applicable`: `pass` means
the gate ran and met its contract; `fail` means it ran and violated the
contract; `blocked` means a named prerequisite is absent; and `not_applicable`
means a valid computation does not apply. A zero denominator has a null value
and `not_applicable`. Structure/discovery never proves capability, and one host
never supplies another host's pass.

Runtime/live-host logs, traces, and derived capability telemetry are
metadata-only. The canonical DEV-131 allowlist separately permits a hash-bound
synthetic or approved-redacted rubric stimulus, assessments containing only the
bounded rationales required for review, and a redacted summary after all path,
content, structured-key, classification, and hash scanners pass. Raw/live
prompts, responses, reasoning, tool arguments/results, credentials, private
configuration, real user/third-party data, raw host/machine identity, literal
executable paths, raw `PATH`, raw blocker diagnostics, `.trace`, and `.xcresult`
are excluded. Normalized `<host-path>` executable identity plus a strict exact
version or `null` is the only committed path-identity exception. Authorized raw
host artifacts remain outside the repository under separate access, retention,
redaction, and deletion policy.

## Deferred work

Rejected: a catch-all skill; provider-specific corpus copies; hand-maintained
dual manifests/catalogs; generated skill mirroring; a guidance-workflow custom
worker; or any runtime surface outside the explicit issue-owned chain above.

DEV-133 through DEV-141 retain their approved guidance, metadata, fixture, and
acceptance ownership. DEV-142 owns the runtime-cost policy/benchmark, DEV-143
the single local Swift bridge, DEV-144 the Codex adapter, and DEV-145 the Claude
adapter; DEV-139/140/141 integration follows those contracts. Generic provider
interfaces, non-Apple providers, PCC, network/credential/paid surfaces,
model-dependent optional evaluation, Instruments, and raw trace workflows
remain deferred and separately gated. No deferred item is a present capability.

## Decision propagation

| Issue | Source | Rationale | Inherited decision | Impact |
| --- | --- | --- | --- | --- |
| DEV-133 | DEV-127/129/132 | One guide avoids drift and normalized host identity avoids local-path leakage. | Canonical `CLAUDE.md`; generated bounded `AGENTS.md`; this record is non-authoritative; host evidence uses `<host-path>` plus a strict single-line version or `null`, prerequisite `blocked`, post-capture drift `fail`, and stable diagnostic classes. | Define guidance generation and fresh repository probes for selected/fallback placement without literal paths, raw `PATH`, malformed versions, or raw diagnostics. |
| DEV-134 | DEV-129/130/131/132 | Narrow activation and one concern owner keep behavior reviewable. | Five positive skills plus exactly one bounded non-positive router; one corpus; no guidance worker; common output/security/evidence contracts. | Positive prompts bypass the router; non-positive output is exactly `no_activation` or `clarification_required`; reference ownership stays deterministic. |
| DEV-135 | DEV-127/129/132 | Deterministic ownership, payload isolation, and executable pinning prevent drift/leakage. | Generated adapters/Codex metadata; root gate requires repository-only content absent from effective payload; each structural row accepts only strict single-line versions, emits `null` for invalid output and stable blocker classes/exit codes, captures one approved executable, and fails post-capture resolution/version drift; exact fallback triggers. | Implement schemas, sync/check, validators, isolated host structure, safe payload/executable-evidence inspection, and fallback without raw diagnostics. |
| DEV-136 | DEV-128/130/132 | Guidance must distinguish its five owners from bounded routing and later runtime enforcement. | Five positive workflows, bounded non-positive router, two handoff patterns, SDK labels, and diagnostic-route fallback/no-rerun rules. | Author guidance that leaves routing authority, provenance, reconciliation, and limitations with the application. |
| DEV-137 | DEV-128/130/131/132 | Complex facts need one source-grounded owner. | Five concern owners, generated-artifact ownership, exact labels, state/recovery rules, diagnostic routing, cost evidence, and safe synthetic allowance. | Write direct references without copying fixture/runtime code or weakening scanners and raw exclusions. |
| DEV-138 | DEV-128/130/131/132 | Offline semantics must not depend on model luck. | Stable D IDs, independent versions, persistent recovery, diagnostic route/fallback/no-rerun behavior, and repository-only synthetic evidence. | Expand deterministic Swift/adversarial proof; never label fixtures as production or live Apple proof. |
| DEV-139 | DEV-129/130/131/132 | Loading is not capability and integrations must consume proven runtime contracts. | Current issue-owned host matrix, strict normalized evidence, payload isolation, and the DEV-142 through DEV-145 route/bridge contracts. | Integrate only after prerequisite component evidence; do not substitute historical host versions or fixtures for capability. |
| DEV-140 | DEV-132 | Documentation must not advertise conditional, path-local, blocked, or architecture-only behavior as shipped. | Exact identity/workflows, bounded router, Apple-only runtime chain, cost target, blocker truth, and raw-evidence exclusions. | Document only proven installation, routing, bridge, cost, fallback, and limitations. |
| DEV-141 | DEV-127 through DEV-132 | Acceptance must integrate all proof layers without collapsing them. | Ownership/path, five workflows, bounded router, state/security/recovery, runtime chain, exact D/E/cost gates, safe evidence, and blocker truth. | Reject false runtime/cost proof, extra parent turns, correctness regression, original-tool rerun, unsafe evidence, or unproven placement. |
| DEV-142 | DEV-128/130/131/132 | Cost routing must be deterministic before runtime implementation. | Own exact versioned action/tool allowlists, selected command classes, savings/payload bounds, paired normalization, and the 10%/0/0 gate. | Unknown policy or telemetry blocks; no invented tool, command, or numeric bound enters DEV-132. |
| DEV-143 | DEV-128/130/132/142 | The Apple bridge is one narrow local provider boundary. | Own the production Swift bridge, availability/data-policy/payload gates, typed result validation, cancellation/deadline, and normalized failure. | Ship no generic provider abstraction or network/PCC/credential surface. |
| DEV-144 | DEV-130/132/142/143 | Codex needs an explicit post-result adapter boundary. | Own Codex `PostToolUse`, provenance binding, original-result preservation, at-most-one bridge attempt, and no original-tool rerun. | Prove success, decline, ineligible, unavailable, invalid, failed, timed-out, and cancelled paths. |
| DEV-145 | DEV-130/132/142/143 | Claude must preserve the same route semantics without a second source of truth. | Own the Claude adapter and consume the same action, policy, bridge, fallback, provenance, and cost contracts. | Prove parity without duplicating policy ownership. |

The earlier host-identity correction is historical propagation evidence in DEV-133 comment
`2efe4e95-30f7-453d-be6f-06cd87c93a2b`, DEV-135 comment
`e2932c4f-93b5-4432-b0f8-77acf14ecfc8`, DEV-139 comment
`051492e4-bec7-47e4-9e4b-9b8830d81710`, DEV-140 comment
`7041ac79-801b-43d6-854b-9a2e9411b07c`, and DEV-141 comment
`e061d603-13c0-4259-8e34-a238de29d7e1`. Current issue text and later comments
govern whenever they amend that evidence.
