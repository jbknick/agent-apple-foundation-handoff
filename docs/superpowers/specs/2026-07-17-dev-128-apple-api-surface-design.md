# DEV-128 Apple Foundation Models API Surface Design

Issue: [DEV-128](https://linear.app/devprentice/issue/DEV-128/r2parallel-verify-the-current-apple-foundation-models-handoff-api)

Evidence collection range: `2026-07-16` through `2026-07-17`

## Purpose

DEV-128 establishes the Apple API truth that later architecture, skill,
reference, fixture, and E2E issues may use. It does not select the repository
plugin topology or create production plugin content.

The approved approach is a stable, locally compile-checked OS 26 core plus a
separately labeled OS 27 beta reference. This preserves useful current Apple
guidance without representing unavailable beta symbols as locally compiled.

## Authority and evidence tiers

Apple API claims use these tiers, in order:

1. The installed macOS 26.5 SDK interface, coupled with local Swift type-check
   or execution evidence.
2. Current official Apple documentation and WWDC material for OS 27 beta APIs
   that are absent from the installed SDK.
3. Apple-owned `apple/foundation-models-utilities` source at immutable commit
   `376ca60e61985369d5067bd3c575bdb6a13f0e1b`.

Third-party plugin repositories may inform structure in other issues, but they
are not Apple API authority here. Memory, generated answers, and unsupported
inference are not evidence tiers.

Every surfaced API statement must be labeled as one of:

- **Compiled SDK 26.5**: the checked-in Swift fixture type-checks or runs with
  the installed SDK.
- **Interface-verified SDK 26.5**: the declaration is present in the installed
  interface but the specific behavior is not executed.
- **Official OS 27 beta, locally unverified**: Apple publishes the symbol, but
  it is absent from this host's SDK.
- **Pseudocode or deterministic mock**: demonstrates an orchestration contract,
  not a shipped Apple API.
- **Blocked**: the required SDK, binary, macro plugin, module, or hardware is
  unavailable, with a reproducible failing command.

## Stable core and beta boundary

The locally compilable core covers `LanguageModelSession`,
`SystemLanguageModel`, availability and context inspection, stable tools,
runtime `DynamicGenerationSchema`, text response and streaming overloads,
prewarming, transcript construction/Codable/rehydration, and the installed
26.x error surface.

Static `@Generable` and `@Guide` declarations exist in the installed interface,
but the Command Line Tools installation lacks the `FoundationModelsMacros`
plugin. The checked-in negative fixture records that blocker. Runtime dynamic
schema is the locally compiled structured-output alternative.

Dynamic instructions, dynamic profiles, generic `LanguageModel`, PCC/custom
providers, tool-calling modes, mutable transcript/session properties, history
modifiers, transcript error policy, the OS 27 error taxonomy, Evaluations, and
Foundation Models runtime Skills are kept in a volatile OS 27 beta section.
They must not appear as locally compiled examples until a compatible SDK is
available.

## Orchestration definitions

The report distinguishes five concepts:

1. **Baton-pass** uses one session and changes the active dynamic profile,
   commonly after a tool updates application state. History is shared unless a
   profile applies a transform. The receiving profile owns the final answer.
   Apple documents this as a composition pattern; no first-class `BatonPass`
   type is claimed.
2. **Phone-a-friend / isolated consultation** creates a short-lived child
   session inside a parent tool. Parent and child transcripts remain isolated,
   and the parent owns the final answer. Illustrative WWDC sample types are not
   treated as framework declarations.
3. **Simple routing** is application policy for choosing a model or route. It
   is not inherently a handoff.
4. **Transcript transfer / rehydration** creates a distinct session from
   explicitly selected transcript entries. It is not baton-pass.
5. **Foundation Models runtime Skills** are dynamic-instruction utilities for
   a model session. They are distinct from Claude Code or Codex Agent Skills.

Because the installed SDK lacks dynamic profiles, the corpus includes a pure
Swift deterministic baton-pass state mock and labels it as a mock. It also
includes an executable stable transcript-isolation probe for parent and child
session construction. Neither fixture claims a live model-generated handoff.

## Artifact layout

The issue adds only research artifacts and fixtures:

- `docs/research/dev-128-foundation-models-api-map.md`: source-grounded
  availability matrix, exact stable/beta boundaries, pattern comparison, and
  downstream constraints.
- `docs/research/evidence/dev-128-command-transcript.md`: normalized commands,
  host inventory, pass/fail output, blockers, and immutable source identities.
- `fixtures/dev-128/README.md`: fixture classifications and exact commands.
- `fixtures/dev-128/compiled/*.swift`: stable compile/run probes plus the
  explicitly labeled deterministic baton-pass mock.
- `fixtures/dev-128/blocked/*.swift`: intentionally non-compiling probes for
  unavailable macro, OS 27, and Evaluations surfaces.

No package manifest, repository runtime, generator, host plugin metadata, or
production skill is introduced. DEV-128 does not pre-empt DEV-132's topology
decision.

## Fixture contract

Positive fixtures must compile with an explicit SDK and target. Deterministic
run fixtures must avoid model generation, network, PCC, credentials, and paid
services. The availability probe may report an unavailable model without
failing; it records host state rather than imposing a hardware gate.

Negative fixtures pass only when their compile command fails for the expected
missing capability. A generic nonzero exit is insufficient: validation must
match the relevant missing macro, missing OS 27 symbol, or missing module
diagnostic.

The stable-surface fixture may type-check calls to probabilistic response and
streaming APIs inside an unexecuted function. It must not invoke generation in
the default run gate.

## Cache, errors, and safety boundaries

Cache guidance remains conditional: appending history generally preserves a
prefix, while changing instructions, tools, or history can invalidate it.
Provider behavior varies and must be measured. Instruments metrics are
optional host evidence when supported, never a default pass requirement.

The stable 26.x and beta 27 error taxonomies remain separate. Exact names must
not be collapsed into a fictional cross-version enum.

Default validation requires no PCC, external provider, entitlement, network,
credential, paid service, or live generation. Missing full Xcode, iPhone SDK,
Evaluations, Instruments, `xctrace`, SDK 27, or macro plugins is recorded as a
narrow blocker, not generalized into failure of the available SDK surface.

## Validation and review boundary

Completion requires:

- positive fixture type-checks and deterministic runs;
- expected negative fixture diagnostics;
- a pinned installed-interface hash and Apple-utilities commit;
- a complete API-family availability matrix;
- explicit source URLs and retrieval dates;
- a clean issue diff relative to the DEV-127 stack base;
- task-level reviews and a fresh whole-branch review;
- final verification from the exact pushed head.

This issue can move to `In Review` only after its atomic PR targets the DEV-127
branch. It must not be merged by this workflow.
