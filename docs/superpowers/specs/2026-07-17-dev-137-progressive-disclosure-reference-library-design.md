# DEV-137 Progressive-Disclosure Reference Library Design

Issue: [DEV-137](https://linear.app/devprentice/issue/DEV-137)

Status: approved design; DEV-137 remains In Progress with blocker
`production_skills_not_integrated` until the combined-tip Codex gate passes

## Objective

Create one package-local, provider-neutral reference library that lets the five
Apple Foundation Models handoff skills load only the concern needed for the
current workflow. The library must preserve exact Apple source and SDK
boundaries, the application-owned architecture and security contracts, and the
DEV-131 evidence vocabulary without duplicating skill activation prose or
repository-only executable fixtures.

This design is documentation architecture. DEV-137 later authors the five
references and reference-specific tests. It does not create a Swift runtime,
copy DEV-138 fixtures into the plugin, implement the DEV-136 skills, or claim
full workflow activation before those skills exist.

## Authority and inherited decisions

The design inherits these binding records:

- DEV-128: installed SDK 26.5 versus official OS/Xcode 27 beta API boundary,
  exact error payloads, orchestration distinctions, cache qualifications, and
  Apple-owned utilities revision;
- DEV-130: Apple fact versus application-policy separation, independent state
  and policy versions, phase gating, C0-C3, bound grants and confirmations,
  effect-ledger reconciliation, persistent recovery, safe fallback, and trace
  safety;
- DEV-131: stable D/E identities, deterministic versus rubric/host layers, the
  exact seven-dimension rubric, zero-denominator handling, and safe evidence;
- DEV-132: one physical progressive-disclosure tree, the common architecture
  contract, repository-only fixtures, and honest blocker handling;
- DEV-134: the fixed five filenames, sole concern ownership, and direct
  skill-to-reference routes;
- DEV-135: conventional package root, regular-file/no-external-symlink payload,
  generated-file boundary, Codex 0.144.5 structural proof, and deferred host
  ledger; and
- the approved DEV-137 decision comment
  `fb9490c1-2352-4cb7-93fb-a7e43b32b0f3`, plus DEV-136/DEV-138 coordination
  comments, which fix filenames, ownership, stacking, and fixture boundaries.

## Approaches considered

### Selected: five concern-owned references

Use one file for each stable concern: architecture/state, orchestration,
Apple API availability, security/recovery, and evaluation/observability. This
matches the DEV-134 direct-routing contract, gives volatile declarations one
owner, and lets every workflow load a bounded subset.

### Rejected: lifecycle-owned references

Grouping design, implementation, review, debugging, and validation separately
would repeat state, API, security, and evidence material across five files. It
would also duplicate the workflow ownership already present in `SKILL.md`.

### Rejected: stable-versus-beta file split

Separate SDK 26.5 and OS/Xcode 27 files would force every Apple question to load
two documents and would separate migration comparisons from their exact source
context. Versioning stays inside the sole Apple API owner instead.

## Exact package topology

The installable package gains exactly these five reference files:

```text
plugins/apple-foundation-models-handoff/
└── references/
    ├── architecture-and-state.md
    ├── orchestration-patterns.md
    ├── apple-api-availability.md
    ├── security-context-and-recovery.md
    └── evaluation-and-observability.md
```

There is no generated reference copy, host-specific mirror, symlink, index
file, runtime dependency, hook, MCP server, command, plugin worker, or packaged
fixture. Repository tests and evidence stay outside the package. The package
oracle expands its exact regular-file allowlist to include these five paths;
unexpected files and all symlinks remain failures.

## Sole ownership contract

| Reference | Sole ownership | Explicit exclusions |
| --- | --- | --- |
| `architecture-and-state.md` | `architectureSchemaVersion: "1.0"`; result domains; source/destination/final ownership; framework-neutral state, phase, transition, termination, cancellation, retry, checkpoint, ledger, and repair contracts | Apple declaration/signature tables, workflow activation text, threat catalog, rubric details |
| `orchestration-patterns.md` | Baton-pass, isolated consultation, deterministic routing, transcript transfer; topology, history visibility, trigger/control, final owner, and selection tables | Exact Apple declarations/errors, state schema duplication, workflow triggers |
| `apple-api-availability.md` | Installed SDK 26.5 compiled/interface surfaces; OS/Xcode 27 beta declarations; complete exact error signatures and payloads; availability, provider/PCC, cache, structured output, runtime Skills, and API blockers | Application authorization policy, rubric, skill activation prose |
| `security-context-and-recovery.md` | Apple security facts separated from application policy; trust boundaries; C0-C3; provenance; grants; confirmation; tool-result provenance; effects; recovery; fallback; trace handling; residual risk | Duplicate Apple signature/error tables, executable reducer fixture code |
| `evaluation-and-observability.md` | Stable D/E IDs; corpus/oracle rules; seven-dimension rubric; evidence allowlist; host matrix; zero denominators; Evaluations and Instruments boundaries; blocker policy | Exact Apple API signatures, duplicated state/security tables, production host harness implementation |

If a subject touches another owner, the file states the local decision in one
sentence and links to the sibling owner. It does not reproduce the sibling
table. Apple declaration tokens, full error payloads, beta availability, and
cache/provider qualifications occur only in `apple-api-availability.md`.

## Reference contracts

### `architecture-and-state.md`

Required sections are scope and authority, common result schema, ownership and
state fields, lifecycle transition table, termination and fallback boundary,
recovery and replay checklist, limitations, related references, and source
context. The state contract preserves:

```text
stateVersion                monotonic state/concurrency revision
policyVersion               independently changed boundary-policy revision
phase                       stable | transitioning | recoveryRequired | terminated
activeProfile / provider
finalResponseOwner
allowedEdges
transition/tool/effect counts and budgets
classified context envelope / provider grant
pending transition / stable checkpoint
effect ledger
metadata-only audit events
```

Ordinary budget or no-safe-path termination begins only from `stable`.
Uncertain external truth remains `recoveryRequired`; unavailable reconciliation
preserves authority, pending/checkpoint state, counts, ledger, and repair facts.
Only explicit successful reconciliation may establish external truth and leave
recovery. Late and replayed events mutate nothing and emit no command.

### `orchestration-patterns.md`

Required sections are selection questions, a four-pattern comparison, baton-
pass, isolated consultation, deterministic routing, transcript transfer,
anti-conflation boundaries, context/cache implications, failure ownership,
related references, and official pattern sources.

The selection table must preserve these results:

| Pattern | Topology | History | Control and final owner |
| --- | --- | --- | --- |
| Baton-pass | One session with changing active profiles | Selected target-necessary shared history | Destination becomes active and owns the final response |
| Isolated consultation | Parent plus short-lived child session | Independent child transcript and minimized envelope | Parent receives a typed result and retains final ownership |
| Deterministic routing | Application selects one route | Defined by the chosen route; no ownership-transfer promise | Selected route owns its result; routing is not inherently a handoff |
| Transcript transfer | Distinct destination session from selected entries | Only explicitly copied entries | Destination session owns its result; mechanics do not grant transfer authority |

No first-class `BatonPass` type or drop-in `PhoneFriendTool` is claimed.
Foundation Models runtime Skills, Claude/Codex Agent Skills, Apple Handoff, App
Intents, and coding-session handoff remain distinct.

### `apple-api-availability.md`

Required sections are evidence labels, normalized host/interface identity,
availability matrix, stable SDK 26.5 surface, OS/Xcode 27 beta surface,
structured output and tools, transcripts and history, complete stable and beta
error tables, provider/PCC boundary, runtime Skills boundary, cache/performance
qualifications, compile/blocker matrix, source ledger, and nonclaims.

The installed interface authority is:

```text
SDK: macOS 26.5
Swift: Apple Swift 6.3.2
Interface: <sdk>/System/Library/Frameworks/FoundationModels.framework/
           Versions/A/Modules/FoundationModels.swiftmodule/
           arm64e-apple-macos.swiftinterface
SHA-256: ff2285670b0966addb9827dc895a3ee3c9db6e186baae62c034fed012632aacc
```

SDK 26.5 `LanguageModelSession.GenerationError` and `ToolCallError` stay
separate from current beta `LanguageModelError`, `LanguageModelSession.Error`,
`SystemLanguageModel.Error`, `PrivateCloudComputeLanguageModel.Error`, and
beta `ToolCallError`. A table called exact includes full associated-value,
property, and initializer signatures. A names-only table says `case names`.

The Apple-owned utilities source is pinned to
`apple/foundation-models-utilities` commit
`376ca60e61985369d5067bd3c575bdb6a13f0e1b`. Source and the tagged commit
message, not a release-note inference, own the `SkillActivations` conformance
statement. The package is optional reference material and does not become a
runtime dependency.

### `security-context-and-recovery.md`

Every subsection is visibly labelled **Official Apple fact**, **Mandatory
application policy**, or **Recommended control**. Required content covers
untrusted inputs, trust boundaries, C0-C3 and provenance, atomic boundary
envelopes, provider grants, immediate effect confirmation, reducer authority,
tool-result provenance, at-most-once command emission, effect reconciliation,
pre-commit versus uncertain failure/cancellation, transcript repair, provider
truth, safe fallback, trace policy, adversarial checklist, and residual risks.

The deterministic reducer, grants, effect ledger, transcript validator, and
repair policy are application architecture, not Foundation Models guarantees.
PCC properties never transfer to a custom provider. Trace claims stop at
Apple's statement that prompts/responses may be sensitive and need safe
handling; the reference makes no unsupported at-rest encryption claim.

### `evaluation-and-observability.md`

Required sections are evidence layers/states, stable ID catalog, corpus/oracle
separation, deterministic acceptance, canonical rubric, safe evidence,
reference-disclosure proof, host matrix, Apple Evaluations, Instruments,
zero-denominator rules, blockers, and limitations.

The canonical rubric contains exactly: pattern selection; Apple API grounding
and version labeling; security-policy completeness; context minimization;
failure and recovery behavior; testability and observability; limitation
honesty. Scores are integers 1-4, mean is at least 3.0, and security policy,
failure/recovery, and limitation honesty each score at least 3. Human semantic
judgment stays separate from deterministic shape/hash/arithmetic validation.

## Direct progressive-disclosure routes

DEV-136 owns the `SKILL.md` links. DEV-137 fixes the destinations and validates
that every reference has at least one direct consumer. No reference invokes a
skill, and no skill invokes another.

| Skill | Always/directly needed | Conditional direct loads |
| --- | --- | --- |
| Design | architecture/state; orchestration; Apple API; security/recovery; evaluation | none; design loads all five |
| Implement | architecture/state; Apple API; security/recovery; evaluation | orchestration for an approved topology |
| Review | architecture/state; evaluation | orchestration for topology/ownership claims; Apple API for API/availability/version claims; security/recovery for trust/effect/replay claims |
| Debug | architecture/state; security/recovery; evaluation | orchestration for route/owner questions; Apple API for API/availability/version questions |
| Validate | architecture/state; Apple API; security/recovery; evaluation | orchestration for route/owner cases |

The full flawed-reducer review case puts topology/ownership, Apple API, and
trust/effect/replay claims in scope and therefore loads all five. That case does
not make all five unconditional for every review. Likewise, validation does not
load orchestration unless route or ownership is in scope.

The exact direct-link assertions become active after DEV-136 rebases above
DEV-137. On the DEV-137-only branch, missing production skills is an honest
downstream prerequisite, not permission to add placeholder `SKILL.md` files.

## Source and citation matrix

All current web sources were rechecked on `2026-07-17`. Installed-interface
claims also carry SDK version, normalized locator, and SHA-256. Each reference
has a concise source ledger; every Apple claim is cited at the table row or
paragraph where it appears.

| Claim family | Owner | Permitted primary sources and retrieval context |
| --- | --- | --- |
| Stable session/model/tool/transcript/structured-output declarations and errors | Apple API | Installed SDK 26.5 interface at the pinned hash; [LanguageModelSession](https://developer.apple.com/documentation/foundationmodels/languagemodelsession), [SystemLanguageModel](https://developer.apple.com/documentation/foundationmodels/systemlanguagemodel), [Tool](https://developer.apple.com/documentation/foundationmodels/tool), and [Transcript](https://developer.apple.com/documentation/foundationmodels/transcript) |
| Current API changes, dynamic instructions/profiles, history, tool mode, revised errors | Apple API | [Foundation Models updates](https://developer.apple.com/documentation/updates/foundationmodels), [dynamic sessions](https://developer.apple.com/documentation/foundationmodels/composing-dynamic-sessions-with-instructions-and-profiles), and [tool calling](https://developer.apple.com/documentation/foundationmodels/expanding-generation-with-tool-calling), retrieved 2026-07-17 and labelled beta/unverified where absent from SDK 26.5 |
| Baton-pass and isolated consultation | Orchestration | [WWDC26 session 242](https://developer.apple.com/videos/play/wwdc2026/242/), retrieved 2026-07-17; declarations remain owned by the Apple API reference |
| Context size, cache, and runtime performance | Apple API | [Managing the context window](https://developer.apple.com/documentation/foundationmodels/managing-the-context-window), [key-value caching](https://developer.apple.com/documentation/foundationmodels/optimizing-key-value-caching-in-language-model-sessions), and [runtime performance](https://developer.apple.com/documentation/foundationmodels/analyzing-the-runtime-performance-of-your-foundation-models-app); claims stay qualified by model/provider/prefix/toolchain |
| Foundation Models runtime Skills and history utilities | Apple API | Apple-owned repository at immutable commit `376ca60e61985369d5067bd3c575bdb6a13f0e1b`, source-inspected with revision context; no third-party authority and no dependency |
| Prompt injection, tool interception, and history transforms | Security | [WWDC26 session 347](https://developer.apple.com/videos/play/wwdc2026/347/), retrieved 2026-07-17; lifecycle APIs labelled Xcode 27 beta/unverified locally |
| PCC and custom-provider boundaries | Apple API and Security | [WWDC26 PCC session 319](https://developer.apple.com/videos/play/wwdc2026/319/), [WWDC26 provider session 339](https://developer.apple.com/videos/play/wwdc2026/339/), and the [PCC Security Guide](https://security.apple.com/documentation/private-cloud-compute/); PCC guarantees are never generalized |
| Evaluations | Evaluation | [Evaluations documentation](https://developer.apple.com/documentation/evaluations), [WWDC26 session 298](https://developer.apple.com/videos/play/wwdc2026/298/), and [WWDC26 session 299](https://developer.apple.com/videos/play/wwdc2026/299/); Xcode 27 beta and blocked on this host |
| Instruments and sensitive trace handling | Evaluation and Security | [WWDC26 session 243](https://developer.apple.com/videos/play/wwdc2026/243/) and runtime-performance documentation; full Xcode 27 plus compatible current target required |
| Application state, reducer, security, evidence, and rubric policy | Architecture, Security, Evaluation | DEV-130/131/132/134 decision contracts, explicitly labelled project/application policy rather than Apple API fact |

Third-party plugin repositories may explain structural organization only. They
cannot appear in an Apple source ledger or support an API declaration,
availability, error, provider, cache, security, or evaluation claim.

## Swift labels and compile contract

Every Swift fence has one visible status line immediately before it:

```text
Code status: `compiled_sdk_26_5`
Code status: `interface_verified_sdk_26_5`
Code status: `official_beta_unverified`
Code status: `pseudocode`
```

No other Swift status is permitted. `compiled_sdk_26_5` blocks are small,
self-contained excerpts that type-check independently against the explicit
macOS 26.5 SDK and `arm64-apple-macos26.0` target. They do not invoke live
generation, PCC, a provider, credentials, entitlements, or a network service.
`interface_verified_sdk_26_5` blocks reproduce the pinned local declaration
shape but do not imply execution. `official_beta_unverified` blocks cite the
official source and remain blocked without SDK/Xcode 27. `pseudocode` blocks
are application contracts and never masquerade as framework types.

Reference snippets are not executable scenario fixtures. DEV-138 retains all
deterministic orchestration/adversarial executables under `fixtures/dev-138/`;
references name stable evidence IDs without copying fixture implementations.

## Validation design

### Offline reference contract

`tests/test_reference_library.py` uses Python standard library only and proves:

- the exact five regular, non-symlink files and no extra reference file;
- required headings and sole-owner term placement;
- every sibling/relative link resolves inside the package and no link escapes;
- every reference is a direct DEV-136 consumer after skills are present;
- every Swift fence has one allowed label and every compiled block type-checks;
- every Apple source ledger URL uses an approved Apple authority/revision;
- volatile declarations/error payloads occur only in the Apple owner;
- exact error tables include payload/property/initializer signatures;
- no placeholder, workflow-activation duplication, third-party API authority,
  raw trace/result artifact, private absolute path, or forbidden secret marker;
  and
- all five files are reachable and none is orphaned.

External HTTP resolution is a separate opt-in network gate. Offline tests
validate URL authority and shape; the active source audit resolves every unique
official URL and records an honest blocker if network/TLS/DNS is unavailable.

### Package and Codex structural proof

`tests/test_plugin_contract.py` expands the source payload oracle from three
files to the three metadata files plus five references. `tests/e2e/
codex_plugin_load.py` expands `EXPECTED_CACHE_FILES` identically and proves all
eight source/cache files are regular, non-symlinked, byte-identical, and inside
the isolated installed package. This remains `E-CODEX-LOAD-001` structural
evidence, not workflow activation.

### Optional structural direct-reference prerequisite

Codex 0.144.5 is active for DEV-137. A focused fresh-task probe asks the model
to use the package reference library, records JSONL file-read events, and
requires the expected minimal reference set for three normalized tasks:

1. pattern/final-owner question -> `orchestration-patterns.md`;
2. installed transcript/API-label question -> `apple-api-availability.md`;
3. fictional `LanguageModelSession.transferBaton(to:)` signature -> Apple API
   reference and an explicit unsupported/no-first-class-API result, never an
   invented declaration.

This probe is only an optional structural prerequisite showing that Codex can
select and ground in the authored corpus when explicitly directed to inspect
it. It is not workflow-triggered progressive disclosure, cannot satisfy
`E-CODEX-ACTIVATE-001`, and cannot complete DEV-137.

### Mandatory combined-stack workflow-triggered proof

After DEV-136 rebases above DEV-137, a host runner launches fresh Codex 0.144.5
`sol` sessions that naturally activate each of the five production workflows.
The task prompts describe the work only: they do not mention the reference
library, reference filenames, file inspection, or which workflow/skill to
activate. Observed file-read events must prove the exact DEV-134 route contract
and minimal conditional loads:

- design reads all five references;
- implement reads architecture/state, Apple API, security/recovery, and
  evaluation, plus orchestration for the approved-topology case;
- baseline review reads architecture/state and evaluation; conditional review
  cases add only the in-scope orchestration, Apple API, or security/recovery
  owner, while the full flawed-reducer review reads all five;
- baseline debug reads architecture/state, security/recovery, and evaluation;
  route/owner adds orchestration and API/availability/version adds Apple API;
  and
- baseline validation reads architecture/state, Apple API, security/recovery,
  and evaluation; route/owner adds orchestration.

The same gate includes a naturally phrased fictional-API task and requires an
unsupported/no-verified-first-class-API result without an invented signature.
The runner rejects missing expected reads and every unrelated reference-content
read. Committed evidence retains only normalized case IDs, prompt hashes,
expected/observed reference basenames, result classifications, Codex version,
integrated commit/tree hashes, counts, reasons, and status. Raw prompts,
responses, JSONL, reasoning, tool arguments/results, credentials, and host
paths are never committed.

Until this combined-tip gate passes, DEV-137 remains In Progress with the exact
blocker `production_skills_not_integrated`. DEV-139 may reuse the evidence for
broader paired and cross-host coverage, but that downstream ownership does not
waive DEV-137's combined-stack completion gate.

## Host and deferred-gate matrix

| Row | DEV-137 policy | Completion meaning |
| --- | --- | --- |
| Offline link/source/ownership/compile tests | Active | Must pass |
| BATS 1.13.0 regression | Active | Existing 3/3 gate must remain pass |
| `E-CODEX-LOAD-001` | Active | Rerun after payload expansion; structural only |
| Optional scoped direct-reference probe | Prerequisite only | May pass, fail, or report a normalized prerequisite blocker; never completes DEV-137 |
| `E-CODEX-ACTIVATE-001` / `DEV137-CODEX-PROGRESSIVE-001` | Mandatory on the combined tip after DEV-136 rebases above DEV-137 | Every workflow-triggered exact/minimal route and the fictional-API noninvention case must pass |
| DEV-137 issue state before the combined-tip pass | In Progress / `production_skills_not_integrated` | Missing production skills is a completion blocker, not a deferred success |
| Claude Code load/activation | `blocked/deferred_by_owner`; not invoked | Never represented as pass |
| `pre-commit` | `blocked/deferred_by_owner` | Never represented as pass |
| `markdownlint` | `blocked/deferred_by_owner` | Never represented as pass |
| Xcode 27/Evaluations/Instruments | Blocked on current SDK 26.5 Command Line Tools host | Missing full Xcode/module/tool/compatible target is an explicit blocker |

Committed host evidence contains normalized `<repo>`/`<host-path>`, strict
version/status/reason/exit-code metadata, and hashes/counts only. Raw prompts,
responses, reasoning, tool arguments/results, credentials, private config,
host identity, raw diagnostics, `.trace`, and `.xcresult` remain excluded.

## Atomic implementation and stack boundary

Implementation begins at DEV-135
`bdbfd335e32eba3efee32f2aac08bd3c2a100368`. Atomic green commits separate:

1. the complete five-file reference library plus its offline/package contract
   tests (partial packaged references are never committed);
2. Codex cache and optional direct-reference prerequisite proof plus normalized
   evidence;
3. the fail-closed workflow-triggered host runner plus the normalized
   `production_skills_not_integrated` DEV-137-only result;
4. review corrections only if independent verification finds a defect; and
5. after DEV-136 rebases above DEV-137, combined-tip workflow-triggered proof
   and an evidence-only commit containing normalized metadata/hashes.

No DEV-137 reference/content commit mixes DEV-136 skill workflow prose or
DEV-138 fixture implementation into DEV-137. After parallel implementation,
DEV-137 rebases above DEV-138 and below DEV-136. DEV-136 then supplies direct
production links without obscuring the reference-only review delta. The final
host run and normalized evidence occur only on that integrated tip; they do not
retroactively fold production skill content into the DEV-137 reference commits.

## Completion criteria

DEV-137 implementation is complete only when the five files are source-grounded,
sole-owned, non-orphaned, correctly linked, code-labelled, compile/audit
checked, and present byte-identically in the Codex cache; the full repository
and inherited regression suites pass; and the combined tip with DEV-136 passes
`DEV137-CODEX-PROGRESSIVE-001` in fresh Codex 0.144.5 `sol` sessions for every
workflow route, every minimal conditional-load case, and fictional-API
noninvention. Structural install evidence or the optional explicitly directed
reference probe cannot substitute for that gate. Until it passes, the issue
remains In Progress with `production_skills_not_integrated`. Claude remains
owner-deferred and is not invoked; pre-commit/markdownlint/Xcode blockers remain
explicit. Broader paired and cross-host proof can remain with DEV-139.
