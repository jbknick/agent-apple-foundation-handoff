# Apple Foundation Models Handoff MVP Decision Record

Decision date: `2026-07-17`

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

The durable host-verification correction source is DEV-132 comment
`98e25ecf-0c4c-4fa6-b877-d255fb24107b`. It narrows executable identity and
evidence handling without changing the plugin, skill, package, state, or
evaluation decisions below.

| Source | Reviewed head | Decision and rationale | Impact |
| --- | --- | --- | --- |
| [DEV-127](../research/dev-127-repository-architecture.md) | `191e2da63b863b367341a614c1ea1d9b4a032cd7` | The authoritative fork began with three documents and no inherited plugin/generation model; upstream is reference only. | Choose every ownership, path, runtime, and proof boundary explicitly. |
| [DEV-128](../research/dev-128-foundation-models-api-map.md) | `4f0b66ef7061d842f333e2749e74614f5331c915` | Pin checked claims to SDK 26.5; keep OS/Xcode 27 beta and orchestration patterns separate. | Compile supported local examples and label unsupported surfaces narrowly. |
| [DEV-129](../research/dev-129-production-pattern-comparison.md) | `3db33eb957326b4d22ebe482c21925dd23b03af0` | One physical capability corpus plus generated Codex metadata avoids provider drift. | Use narrow skills, progressive disclosure, host-specific loading, and no worker by default. |
| [DEV-130](../research/dev-130-handoff-threat-model.md) | `5e27a1c81a4c45199c912a5cbb750a30a8c7bf17` | Model output cannot own authority or external-effect truth. | Make reducer, context/grant/effect, recovery, fallback, and safe-evidence rules binding. |
| [DEV-131](../research/dev-131-evaluation-strategy.md) | `3792e8c98a387b7f9c48bd210d25938b40cdd5fe` | Deterministic, rubric, real-host, and optional Apple evidence answer different questions. | Preserve stable IDs, oracle separation, blocker honesty, and evidence scanners. |

The plugin provides coding guidance and reviewable proof contracts. It does not
run a handoff, enforce application policy, or make a probabilistic model an
authority.

## Users and workflows

Plugin ID: `apple-foundation-models-handoff`. Display name:
**Apple Foundation Models Handoff**. Users are Apple-platform engineers,
architects, reviewers, and maintainers working in Claude Code or Codex.

The five non-overlapping workflow entries are fixed:

| Exact skill directory | Owns |
| --- | --- |
| `design-apple-foundation-models-handoff` | New or revised architecture, topology, pattern, state, and boundary decisions |
| `implement-apple-foundation-models-handoff` | Application changes and tests tied to an approved architecture |
| `review-apple-foundation-models-handoff` | Evidence-backed contract/API/security findings with stable IDs |
| `debug-apple-foundation-models-handoff` | First divergence, root cause, bounded correction, and regression proof |
| `validate-apple-foundation-models-handoff` | Deterministic, compile, schema, generation, evidence, and host matrices |

MVP explicitly excludes:

- application runtime orchestration, authentication, authorization,
  encryption, persistence, networking, UI, and provider integration;
- automatic PCC/custom-provider use, credentials, entitlements, and paid
  services;
- a reusable Swift package/sample app, App Intents, Apple Handoff, generic
  Core ML/Apple Intelligence education, and coding-session handoff;
- a custom agent, hook, command, MCP server, app, or runtime dependency; and
- release, publishing, tagging, merging, and marketplace distribution.

## Skill and reference architecture

Both hosts use one provider-neutral physical `skills/` corpus and one shared
`references/` corpus. Skills load common references directly and do not require
another skill invocation. No plugin-local worker is justified; per-skill
`agents/openai.yaml`, if host proof requires it, is presentation/activation
metadata only.

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
on the primary controlled-shell Claude Code `2.1.91` and Codex `0.144.5`
baseline. Each row pins one executable before operations and invalidates on
resolution drift. Repository-only fixtures, tests, research, and private
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

The primary acceptance baseline remains Claude Code `2.1.91` and Codex
`0.144.5` from the controlled shell. Alternate-PATH Claude Code `2.1.140` is a
diagnostic observation only, not substitute evidence for the selected Claude
row and not an additional acceptance row. Version output proves only that the
captured executable prerequisite is present; it does not prove loading,
activation, reference use, or capability.

## Handoff patterns and Apple API boundary

| Pattern | Context/topology | Control and final owner |
| --- | --- | --- |
| `baton_pass` | One session; target-necessary selected history across active profiles | Destination becomes active and owns the final response |
| `isolated_consultation` | Parent plus short-lived child; minimized envelope; independent child transcript | Parent receives a typed result and retains control/final ownership |

Deterministic routing chooses before a session; transcript transfer constructs a
distinct session from selected entries. Neither is renamed baton-pass. Runtime
Foundation Models Skills, Claude/Codex Agent Skills, coding-session handoff,
Apple Handoff, and App Intents remain separate concepts.

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
Expected outcomes exist only in the corpus index.

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
executable paths, raw `PATH`, `.trace`, and `.xcresult` are excluded. Normalized
`<host-path>` executable identity plus exact version is the only committed path
identity exception. Authorized raw host artifacts remain outside the repository
under separate access, retention, redaction, and deletion policy.

## Deferred work

Rejected: a catch-all skill; provider-specific corpus copies; hand-maintained
dual manifests/catalogs; generated skill mirroring; a custom worker; or
unapproved agent, hook, command, MCP, app, dependency, and runtime surfaces.

DEV-133 through DEV-140 implement approved guidance, metadata, schemas,
generation, skills, references, fixtures, E2E, and documentation. DEV-141 owns
final acceptance. OS/Xcode 27 beta integrations, live PCC/custom providers,
model-dependent evaluation, Instruments, and raw trace workflows remain
optional and separately gated. No deferred item is a present capability.

## Decision propagation

| Issue | Source | Rationale | Inherited decision | Impact |
| --- | --- | --- | --- | --- |
| DEV-133 | DEV-127/129/132 | One guide avoids drift and normalized host identity avoids local-path leakage. | Canonical `CLAUDE.md`; generated bounded `AGENTS.md`; this record is non-authoritative; host evidence uses `<host-path>` plus exact observed version or `null`, prerequisite `blocked`, and post-capture drift `fail`. | Define guidance generation and fresh repository probes for selected/fallback placement without literal executable paths or raw `PATH`. |
| DEV-134 | DEV-129/130/131/132 | Narrow activation and one concern owner keep behavior reviewable. | Exactly five skills; one corpus; no worker; common output/security/evidence contracts. | May refine reference filenames only with sole concern ownership and deterministic direct links. |
| DEV-135 | DEV-127/129/132 | Deterministic ownership, payload isolation, and executable pinning prevent drift/leakage. | Generated adapters/Codex metadata; root gate requires repository-only content absent from effective payload; each structural row emits normalized prerequisite blockers, captures one approved executable, and fails post-capture resolution/version drift; exact fallback triggers. | Implement schemas, sync/check, validators, isolated host structure, payload and executable-identity inspection, and fallback. |
| DEV-136 | DEV-128/130/132 | Guidance must not claim runtime enforcement. | Two handoff patterns; SDK 26.5 labels; reducer/grant/effect/fallback contract; stable-only ordinary termination; persistent recovery. | Author workflows that leave authority, reconciliation, and limitations with the application. |
| DEV-137 | DEV-128/130/131/132 | Complex facts need one source-grounded owner. | Five concern owners, exact labels, state/recovery rules, D/E/rubric contracts, metadata-only live telemetry, and safe synthetic allowance. | Write direct references without copying fixture code or weakening scanners/raw exclusions. |
| DEV-138 | DEV-128/130/131/132 | Offline semantics must not depend on model luck. | Stable D IDs/oracle separation; independent versions; recovery persists through no safe reconciliation; synthetic evidence passes every DEV-131 scanner. | Expand deterministic Swift/adversarial proof with exact/repeated output and honest blockers. |
| DEV-139 | DEV-129/130/131/132 | Loading is not capability, cached content is a security boundary, and executable drift invalidates comparison. | Exact E rows emit normalized `blocked` for missing/non-runnable/wrong-version prerequisites; fresh tasks then use one approved captured executable; resolution/version drift is `fail`; payload isolation, metadata-only live telemetry, and fallback remain. | Prove activation/reference/output/rejection on selected 2.1.91/0.144.5 or record blockers/use fallback; 2.1.140 is diagnostic only. |
| DEV-140 | DEV-132 | Documentation must not advertise conditional, path-local, or blocked behavior as shipped. | Exact identity/workflows, proven placement, pattern/API distinctions, prerequisite `blocked` versus drift `fail`, recovery persistence, normalized host identity, and exclusions. | Document installation, development, usage, normalized host outcomes, selected executable/version contract, actual fallback, and limitations without local paths/raw `PATH`. |
| DEV-141 | DEV-127 through DEV-132 | Acceptance must integrate all proof layers without collapsing them or accepting host-resolution drift. | Ownership/path, five skills, state/security/recovery, exact D/E/rubric gates, payload isolation, safe evidence exception, normalized `<host-path>` plus exact version/null, prerequisite blockers, drift failures, and blocker truth. | Reject unsafe evidence, unresolved recovery, literal paths/raw `PATH`, alternate substitution, misclassified prerequisite/drift outcomes, false execution/pass claims, or unproven placement. |

The host-identity correction is already durable downstream in DEV-133 comment
`2efe4e95-30f7-453d-be6f-06cd87c93a2b`, DEV-135 comment
`e2932c4f-93b5-4432-b0f8-77acf14ecfc8`, DEV-139 comment
`051492e4-bec7-47e4-9e4b-9b8830d81710`, DEV-140 comment
`7041ac79-801b-43d6-854b-9a2e9411b07c`, and DEV-141 comment
`e061d603-13c0-4259-8e34-a238de29d7e1`.
