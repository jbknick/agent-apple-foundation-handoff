# Runtime V1 Direct Local Diagnostic Consultation Design

Project:
[Agent Apple Foundation Handoff](https://linear.app/devprentice/project/agent-apple-foundation-handoff-8297ee383b88)

Decision date: `2026-07-25`

Status: conversational design approved with `lgtm`; this written specification
awaits user review. Implementation planning, runtime work, and Linear mutations
remain unauthorized.

## Executive decision

Runtime V1 will pursue one proof-first architecture:

```text
completed eligible direct-mode Codex Bash result
  -> trusted PostToolUse hook
  -> deterministic diagnostic-condensation-v1 gates
  -> one local Swift Foundation Models consultation
  -> deterministic result validation
  -> PostToolUse continue:false replacement for the next parent request
  -> Codex parent retains final-response ownership
```

This is an `isolated_consultation`, not a provider switch or a full session
handoff. Apple Foundation Models performs one bounded diagnostic-condensation
operation. Codex executes the original command exactly once and remains the
task and final-response owner.

The architecture is a candidate until an installed-host capability gate proves
the composed chain. Separate Codex source support and Apple SDK availability do
not establish that the chain works end to end.

Runtime V1 is limited to direct tool mode. Code mode, including a direct tool
invoked from inside code mode, is blocked because Codex `0.145.0` deliberately
retains the original typed result for the code-mode caller.

## Authority and bounded supersession

Freshly fetched `origin/main` was
`934285f38e67d0f956f0848d150d0afa33dbfb4e` when this design was written. The
following repository sources remain authoritative:

- [DEV-142 runtime and benchmark contract](2026-07-21-dev-142-runtime-cost-routing-and-benchmark-design.md)
- [Prior Codex-only runtime design](2026-07-23-codex-foundation-models-runtime-completion-design.md)
- [DEV-246 terminal result](../../research/dev-246-codex-result-replacement.md)
- [Apple API map](../../research/dev-128-foundation-models-api-map.md)
- [Evaluation strategy](../../research/dev-131-evaluation-strategy.md)
- [MVP decision record](../../architecture/apple-foundation-models-handoff-mvp-decision-record.md)

This design preserves DEV-142's exact policy identity, command and data
allowlists, request/result contracts, fixture hashes, correctness rules,
original-result fallback, at-most-one Apple attempt, and no-rerun invariant.
It does not rewrite DEV-246's historical evidence.

DEV-142's historical benchmark validator also remains immutable: it requires
two hosts, 48 pairs, and 96 arms. Runtime V1 therefore uses an independent
successor benchmark identity,
`benchmarkProfile = codex-runtime-v1-cost-v1`, for its Codex-only 24-pair
matrix. The runtime `policyVersion` remains `diagnostic-condensation-v1`.

It narrowly supersedes the prior conclusion that Codex CLI `0.145.0` has no
supported model-visible result-replacement boundary. DEV-246 remains correct
that `suppressOutput` is parsed but unsupported. Current official `0.145.0`
source separately implements and tests replacement through
`continue:false` plus `stopReason`; DEV-246 stopped before evaluating that
path.

The five positive workflow skills and bounded non-positive router remain
guidance capabilities. They are not this runtime's cost router, hook, bridge,
or execution owner.

## Current verified facts

### Repository and Linear

- The guidance/plugin surface contains five positive workflows plus one
  non-positive router.
- DEV-142 is Done and contract-only. It contains no production Swift bridge,
  runtime hook, live Apple response, or provider-usage claim.
- DEV-246 is Done with historical
  `blocked:host_replacement_unavailable` evidence for `suppressOutput`.
- DEV-143, DEV-144, DEV-139, DEV-140, DEV-141, and DEV-145 remain Canceled.
- The repository contains no production runtime code, hook, command, agent,
  MCP server, package dependency, or live cost result.

### Codex

- The captured installed executable reports `codex-cli 0.145.0`.
- [`rust-v0.145.0`](https://github.com/openai/codex/releases/tag/rust-v0.145.0)
  remains the latest official release as of the decision date.
- `suppressOutput` and `updatedMCPToolOutput` remain unsupported
  ([official parser](https://github.com/openai/codex/blob/rust-v0.145.0/codex-rs/hooks/src/engine/output_parser.rs#L386-L431)).
- In direct tool mode, an official integration test proves that a
  `PostToolUse` hook sees the raw shell result while the corresponding tool
  result in the next provider request equals `stopReason`, not the raw result
  ([official test](https://github.com/openai/codex/blob/rust-v0.145.0/codex-rs/core/tests/suite/hooks.rs#L4497-L4552)).
- Codex wraps the original result for local handling while exposing only the
  model-visible replacement in the next response item
  ([dispatch](https://github.com/openai/codex/blob/rust-v0.145.0/codex-rs/core/src/tools/registry.rs#L618-L674),
  [wrapper](https://github.com/openai/codex/blob/rust-v0.145.0/codex-rs/core/src/tools/registry.rs#L189-L209)).
- In code mode, `continue:false` deliberately returns the original typed
  result to JavaScript
  ([official test](https://github.com/openai/codex/blob/rust-v0.145.0/codex-rs/core/src/tools/registry_tests.rs#L323-L371)).
- Source proof is not installed-binary, plugin-trust, live Apple, or
  provider-usage proof.

### Apple Foundation Models

- The verified host has Xcode `26.6` (`17F113`), Swift `6.3.3`, SDK `26.5`,
  Apple Silicon, and the pinned Foundation Models interface SHA-256
  `ff2285670b0966addb9827dc895a3ee3c9db6e186baae62c034fed012632aacc`.
- Fresh `compiled_sdk_26_5` evidence covers `LanguageModelSession`,
  `@Generable`, `@Guide`, `GenerationSchema`, and structured response shape.
- Fresh prerequisite checks reported the default model available, the current
  locale supported, `contextSize = 4096`, and successful `tokenCount`.
- No live `respond` call occurred. Availability, compilation, and tokenization
  are prerequisites, not generation proof.
- Apple's [guided-generation API](https://developer.apple.com/documentation/foundationmodels/generating-swift-data-structures-with-guided-generation)
  can constrain shape but cannot prove semantic correctness.
- The Apple-owned [Python SDK](https://github.com/apple/python-apple-fm-sdk) is
  alpha and absent locally. The native `fm` CLI requires macOS 27 and is absent.
  Neither is selected.

## Current blockers

Runtime V1 has no pass until all of these blockers are cleared:

1. The installed Codex binary has not produced direct next-request evidence
   for the selected hook output.
2. No trusted installed plugin hook has invoked the proposed local bridge.
3. No real Apple `LanguageModelSession.respond` has produced a structured
   condensation.
4. No live Apple output has passed the frozen DEV-142 validator.
5. No composed failure has proved untouched-original fallback.
6. No paired run has supplied actual parent-model usage.
7. No token reduction, correctness, latency, or Apple-attempt release result
   exists.
8. Authentication, exact model, telemetry, hardware, SDK, or model
   availability missing from a required row remains `blocked`.

## Source-backed capability matrix

| Candidate boundary | Exact supported interface and source | Invocation | Original reaches parent model | Parent-model turn effect | Execution and final-response owner | Runtime V1 disposition |
| --- | --- | --- | --- | --- | --- | --- |
| Direct `PostToolUse` replacement | `continue:false` with `stopReason`; official [next-request test](https://github.com/openai/codex/blob/rust-v0.145.0/codex-rs/core/tests/suite/hooks.rs#L4497-L4552) | Automatic after a matching trusted direct tool | No on a successful replacement according to tagged source; installed host remains unproved | Normal post-tool continuation only; no additional completion | Codex executes once and answers; Apple only condenses | **Selected exact-original-V1 candidate** |
| `PreToolUse.updatedInput` wrapper | Supported rewrite before unified exec ([source](https://github.com/openai/codex/blob/rust-v0.145.0/codex-rs/core/src/tools/handlers/unified_exec/exec_command.rs#L408-L439)) | Automatic | No if the wrapper buffers the command output | Normal tool continuation | Wrapper owns command and Apple; Codex answers | Supported but rejected: more execution and fallback risk than the selected native boundary |
| Local STDIO MCP tool | Supported local [MCP server](https://developers.openai.com/codex/mcp/) returning `CallToolResult` | Model-selected or explicitly requested | No on success because MCP owns and buffers execution | Normal MCP tool continuation | MCP process executes and condenses; Codex answers | Closest supported V1 if automatic replacement fails; requires explicit product-scope change |
| Explicit local wrapper command | Ordinary direct shell command that owns execution and condensation | User- or model-invoked | No on success | Normal shell continuation when run during a task | Wrapper executes and condenses; Codex answers | Smallest executable scope-changed V1; not transparent |
| Code-mode `continue:false` | Original typed result is retained by design | Automatic after nested direct tool | Yes, to the code-mode caller | No savings guarantee | Code-mode script remains caller | **Blocked for Runtime V1** |
| `suppressOutput` / `updatedMCPToolOutput` | Parsed but unsupported | Hook output | Original is not replaced | Not applicable | Not applicable | **Unsupported** |
| `additionalContext` / `systemMessage` | Context or UI feedback beside the result | Automatic hook feedback | Yes | `additionalContext` can add use; neither field removes the original | Codex remains owner | **Does not satisfy replacement** |
| Skill, plugin discovery, or custom prompt alone | Guidance/user-message expansion only | User- or model-selected | Yes if it calls the ordinary tool | Same or greater use | Codex remains owner | **Structural prerequisite only** |
| Codex subagent | Separate Codex model task; official [subagent documentation](https://developers.openai.com/codex/subagents/) warns of greater token use | Model- or user-selected | Child may hide raw content from parent, but consumes another Codex model | Adds model work | Codex models own both tasks | **Excluded: Apple is not the delegated provider** |
| Swift `LanguageModelSession` | Installed SDK 26.5 structured local generation | Bridge-invoked | Only the bridge's validated result crosses back | No parent call by Apple | Swift bridge owns the Apple attempt | **Selected Apple surface; live generation blocked** |
| Apple Python SDK | Apple-owned alpha package, absent locally | Bridge-invoked | Boundary could be equivalent | No parent call by Apple | Python bridge | **Blocked and unnecessary** |
| Native `fm` CLI | Official macOS 27 surface, absent locally | Explicit process | Boundary could be equivalent | No parent call by Apple | `fm` process | **Blocked by host and privacy uncertainties** |

## Selected Runtime V1 architecture

### Pattern

The selected pattern is `isolated_consultation`:

- **Source:** the Codex parent session after one eligible direct-mode `Bash`
  result.
- **Destination:** one fresh local `LanguageModelSession` using
  `SystemLanguageModel.default`.
- **Trigger:** deterministic application policy after `PostToolUse`, never
  model choice.
- **Current and final owner:** the Codex parent for the entire task.
- **Apple role:** one typed diagnostic-condensation computation only.
- **History:** none. Apple receives no parent transcript or prior Apple
  transcript.

Baton pass is not selected because Apple never becomes the final-response
owner. Transcript transfer is unnecessary. Deterministic routing supplies
eligibility gates but does not itself transfer ownership.

### Successful data flow

1. Codex executes one allowed direct-mode `Bash` command.
2. Codex retains the original tool result and invokes the trusted
   `PostToolUse` hook once.
3. Host preflight pins code mode disabled. The adapter validates canonical tool
   identity, call identity, version bindings, command grammar, data
   classification, byte bounds, and estimated savings.
4. The adapter passes one request through standard input to a captured local
   Swift executable. Raw diagnostic content never appears in process arguments.
5. The Swift bridge checks model availability, locale, exact token counts, and
   the 75% context-occupancy ceiling.
6. Immediately before the sole `respond`, the bridge increments the Apple
   attempt counter.
7. Apple generates only the untrusted condensation content. Application code,
   not the model, supplies trusted request bindings and control fields.
8. The bridge validates the complete frozen DEV-142 result, semantic
   invariants, maximum 4,096 output bytes, minimum 4,096 realized savings
   bytes, and a rendered result below Codex's large-hook-output spooling
   boundary.
9. Only after validation, the adapter serializes the canonical
   `diagnostic_condensation` as `stopReason` and emits:

   ```json
   {"continue": false, "stopReason": "<validated diagnostic_condensation>"}
   ```

10. Codex sends the validated condensation, not the original result, in the
    next parent-provider request.
11. The Codex parent validates and uses the result and remains the sole
    final-response owner.

The first parent completion and original command are unchanged. Savings can
occur only in parent consumption after `PostToolUse`.

### Invocation-local state

`stateVersion = runtime-v1-direct-consultation-v1` is independent of
`policyVersion = diagnostic-condensation-v1`.

```text
observed
  -> declined
  -> eligible
      -> apple_attempting
          -> validated
              -> replacement_emitted
          -> fallback_original
      -> fallback_original
  -> complete
```

The Codex parent remains owner in every state. The adapter has zero original
command budget, zero external-effect budget, and one Apple-attempt budget. It
cannot execute, retry, or replay the original command. The Apple attempt has
zero retries.

The state is invocation-local and contains no recoverable external effect.
Cancellation, bridge failure, or uncertain Apple completion cannot authorize a
second attempt. The adapter returns control to Codex's retained original-result
path.

Codex's existing permission and confirmation boundary owns the original
command and any effects it produces. The hook emits no executor command and
adds no external effect, so it cannot widen or replay that authority.

## Ownership and trust boundaries

| Boundary | Receives | Authority | Retention |
| --- | --- | --- | --- |
| Codex parent provider | Validated condensation on `applied`; untouched original otherwise | Task planning and final response | Existing Codex policy |
| Codex host/core | Original command, original result, hook result | Command execution and tool-result lifecycle | Existing local host behavior |
| Trusted hook adapter | One original result plus trusted hook metadata | Eligibility, bridge invocation, validation, replacement decision | Process memory only |
| Swift bridge | Minimized DEV-142 request and selected diagnostics | One local Apple attempt and typed result construction | Process memory only |
| Apple `SystemLanguageModel.default` | Allowlisted C0/C1 diagnostic content, instructions, and schema | Generate one untrusted condensation | Fresh session only |
| Evidence extractor | Normalized counters, hashes, versions, statuses, and aggregates | Evidence normalization only | Committed safe metadata after scans |

Every field is classified atomically before Apple transfer:

- C0 public synthetic diagnostic content is allowed.
- C1 task-private trusted-local diagnostic content is allowed only under the
  exact purpose-bound runtime grant.
- C2, C3, unknown, mixed-provenance, remote, transcript-derived, credential,
  configuration, and injected content are declined.

The grant binds session, call ID, tool, command class, exact fields, source and
destination providers, purpose, retention, expiry, `stateVersion`, and
`policyVersion`. Binding drift declines before the Apple attempt.

Apple Foundation Models is the only added generation provider. The existing
Codex parent is not replaced. The runtime adds no PCC, external LLM, network
inference, credential, paid inference, or remote fallback.

## Context and privacy policy

The bridge uses one fresh, single-turn `LanguageModelSession` with no Apple
tools and no transcript rehydration. The context budget includes:

- instructions;
- generated schema;
- selected diagnostic fields;
- only semantic request fields required for condensation; control bindings
  remain outside model context; and
- reserved response tokens.

The bridge uses Apple's exact token-count APIs. Their sum must remain at or
below 3,072 tokens, DEV-142's 75% ceiling over the installed 4,096-token
context. Byte eligibility never substitutes for token eligibility.

Raw prompts, tool results, Apple output, parent responses, reasoning, hook
arguments, credentials, private configuration, private paths, transcripts,
traces, and `.xcresult` content are never committed. They remain transient in
process memory or an isolated evidence harness and are deleted after
normalization. The project makes no secure-memory-erasure claim.

The original may remain visible to the local Codex host, UI, and transient
tool telemetry. Runtime V1 promises only that the original is absent from the
next parent-provider request on an `applied` row.

## Minimal components and interfaces

Runtime V1 needs four responsibilities and no generic runtime framework:

1. **Existing DEV-142 contract authority**
   - Reuse the exact runtime policy, request/result schemas, 24-case corpus,
     semantic validators, correctness oracle, and provider-normalization
     rules.
   - Do not create a second runtime router or modify fixtures to fit output.
   - Preserve the historical two-host benchmark validator unchanged.

2. **Trusted Codex hook adapter**
   - Match only canonical `PostToolUse` plus `Bash`.
   - Accept only direct tool mode.
   - Preserve the host-retained original by default.
   - Invoke the bridge at most once.
   - Emit `continue:false` only for a validated `applied` result.

3. **Native Swift condenser**
   - Use the installed `FoundationModels` framework and
     `SystemLanguageModel.default`.
   - Read a bounded request from standard input.
   - Use one fresh session, one structured response, and no tools.
   - Return the frozen DEV-142 result shape without logging raw content.

4. **Normalized capability and benchmark evidence**
   - Observe provider-next-request replacement transiently.
   - Record actual provider usage, Apple attempts, correctness, and latency.
   - Add the separate `codex-runtime-v1-cost-v1` benchmark profile and its
     Codex-only matrix validator without relabeling DEV-142 evidence.
   - Commit only normalized, scanned metadata.

No MCP server, Python package, custom provider abstraction, transcript store,
Apple tool, subagent, telemetry SDK, retry coordinator, or persistent state
machine belongs in Runtime V1.

## Failure and untouched-original fallback

The adapter's default is no replacement. An ordinary decline or caught bridge
failure exits `0` with no output so Codex continues normal processing of the
original result. The adapter emits the replacement directive only after a
complete `applied` result.

The untouched original is required for:

- tool, command, mode, version, provenance, or data-policy decline;
- input byte or exact Apple context ineligibility;
- Apple unavailable or locale unsupported;
- bridge launch, stdin/stdout, deadline, cancellation, or decoding failure;
- guardrail, refusal, asset, rate-limit, concurrent-request, or generation
  failure;
- invalid schema, binding, diagnostic identity, warning accounting,
  correctness, output size, or realized savings;
- malformed hook output or host replacement failure; and
- any unknown state or reason code.

No failure prepends or appends a reason to the original. Normalized reason
metadata is separate. The command and Apple attempt are never retried.

`decision:block`, exit code `2`, `suppressOutput`, context addition, transcript
mutation, and a second parent request to perform condensation are prohibited
fallbacks.

The installed-host gate must prove ordinary no-output decline, caught bridge
failure, malformed bridge output, adapter crash, and hook timeout behavior.
If any branch does not preserve the original without rerun, Runtime V1 is
`fail`, not partially supported.

## Live benchmark design

### Evidence layers

The proof proceeds through independent gates:

1. **Direct-boundary gate:** captured Codex `0.145.0`, direct mode, trusted
   synthetic hook, and transient inspection of the next provider request.
2. **Live Apple gate:** one non-mocked `SystemLanguageModel.default` response
   through the same bridge interface.
3. **Composed capability gate:** one eligible synthetic diagnostic completes
   the full hook-to-Apple-to-next-provider path plus untouched-original
   fallback cases.
4. **Codex-only paired benchmark:** all 24 frozen DEV-142 eligible fixtures run
   `pluginOff` and `pluginOn`.

Passing an earlier gate never satisfies a later one.

### Required pair and arm denominators

The successor Runtime V1 product scope is Codex-only:

```text
benchmarkProfile = codex-runtime-v1-cost-v1
requiredFixtures = 24
requiredPairs = 24
armsPerPair = 2
requiredArms = 48
validRequiredPairs = 24
blockedRequiredPairs = 0
```

This narrows the successor Runtime V1 release matrix from DEV-142's historical
two-host 48-pair/96-arm contract. It does not alter or relabel DEV-142's
completed cross-host evidence or reuse its closed release validator as though
the required host count had changed.

Every pair contains otherwise identical `pluginOff` and `pluginOn` arms.
Identity binds fixture hash, parent model, reasoning configuration, provider,
provider normalization, Codex version, toolchain, policy version, command
class, task prompt hash, and relevant host prerequisites. Any mismatch blocks
the pair.

No row may be dropped, imputed, or converted to a zero. A zero or missing
plugin-off token denominator blocks that pair.

### Invocation denominators

The benchmark reports all of these counts separately:

```text
requiredPluginOnRows = 24
deterministicallyEligibleRows
appleContextEligibleRows
appleAttemptedRows
appleValidResultRows
appliedRows
declinedRows
fallbackRows
failedRows
```

Rates always name their denominator:

- Apple attempt rate =
  `appleAttemptedRows / appleContextEligibleRows`.
- Apple valid-result rate =
  `appleValidResultRows / appleAttemptedRows`.
- Application rate = `appliedRows / requiredPluginOnRows`.
- Fallback rate = `fallbackRows / requiredPluginOnRows`.

A zero denominator yields `null` and `not_applicable`, never a perfect score.
Runtime V1 release still requires at least one real Apple attempt and one
validated `applied` row; otherwise the live handoff claim fails.

### Parent-model usage

Each arm records actual provider- or Codex-reported:

- input tokens;
- cached-input tokens;
- cache-write input tokens when exposed;
- output tokens;
- reasoning-output tokens;
- total parent-model tokens;
- parent completions/turns; and
- the exact versioned normalization used.

The primary pair reduction remains:

```text
(pluginOff.totalParentModelTokens - pluginOn.totalParentModelTokens)
/ pluginOff.totalParentModelTokens
```

Cached and reasoning subsets are reported separately and are never added twice.
If current Codex telemetry cannot map exactly to the frozen
`openai-responses-usage-v1` semantics, the benchmark is blocked pending an
approved versioned normalization. Bytes, Apple tokens, local tokenizers,
estimated tokens, and inferred cache values cannot substitute.

Whole-turn actual usage is acceptable when it is the stable supported
telemetry boundary, but the report must state that unchanged first-completion
usage dilutes post-tool savings. Exact post-tool usage may be reported
separately only from a supported source.

### Correctness, latency, and attempts

Correctness compares each `pluginOn` parent outcome with both the fixed oracle
and its paired `pluginOff` outcome. It requires:

- unchanged command outcome;
- every fatal and error identity;
- failed test identities;
- warning accounting;
- an actionable next step;
- no invented fact; and
- correct task completion.

Latency uses monotonic clocks and records:

- Apple `respond` latency over attempted rows;
- complete hook latency;
- complete parent-turn latency; and
- median and p95 values with explicit denominators.

This design sets no arbitrary latency release threshold. Missing latency is
blocked, and exceeding the enforced hook deadline is a fallback/failure. The
observed latency distribution remains an explicit owner review item.

The Apple-attempt counter increments immediately before the sole real
`respond`. `pluginOff` attempts are exactly zero. Every `pluginOn` row has at
most one.

### Privacy and cleanup

Provider request capture, raw diagnostics, prompts, responses, and traces stay
outside the repository in an isolated temporary harness. The committed row
contains only:

- normalized executable and version identities;
- fixture and artifact hashes;
- boolean original-absent/replacement-present assertions;
- counts, timings, token fields, and status;
- stable reason and diagnostic classes; and
- cleanup status.

The harness performs path, content, structured-key, classification, and hash
scans before commit. Cleanup failure blocks the row.

## Acceptance criteria

### Successor capability gate

All conditions are conjunctive:

1. The captured executable resolves and rechecks as exact Codex CLI `0.145.0`.
2. Direct tool mode is explicitly active and code mode is disabled.
3. The exact candidate plugin is installed through an isolated `CODEX_HOME`
   marketplace workflow and its hook is explicitly trusted.
4. One approved diagnostic command executes exactly once.
5. The hook receives the original synthetic sentinel.
6. One real `SystemLanguageModel.default` `respond` occurs.
7. The result passes the frozen DEV-142 schema and semantic validator.
8. The next parent-provider request contains the validated
   `diagnostic_condensation`.
9. The original sentinel is absent from that next request.
10. The successful path adds zero parent-model turns relative to its paired
    baseline.
11. Each required decline/failure path returns the untouched original and
    executes no second command or Apple attempt.
12. The replacement is delivered inline; Codex does not spool it to a
    temporary file or substitute a head-and-tail preview.
13. Transient raw evidence is cleaned and only normalized safe evidence
    remains.

Any missing prerequisite is `blocked`. Any violated invariant is `fail`.
Neither state authorizes production runtime work.

### Runtime V1 release gate

All conditions are conjunctive:

```text
validRequiredPairs = 24
blockedRequiredPairs = 0
median(parent-token reduction across all required pairs) >= 0.10
correctnessRegressions = 0
additionalParentModelTurns = 0
realAppleAttempts >= 1
validatedAppliedRows >= 1
originalCommandReruns = 0
unsafeCommittedEvidenceFindings = 0
```

Compilation, model availability, plugin discovery, hook invocation, structural
tests, synthetic model output, output byte reduction, or one successful live
row cannot satisfy this release gate.

## Alternatives and unsupported ideas

### Closest supported V1: local STDIO MCP tool

An MCP tool could own the command, buffer its result, call Apple, and return
only the condensation. It is easier to reason about than command rewriting but
is model-selected or explicitly invoked rather than transparently automatic.
It changes execution ownership and therefore requires a new product decision.

### Smallest scope-changed V1: explicit wrapper command

An explicit wrapper could prove local Apple generation and parent savings with
the fewest runtime surfaces. It would not satisfy automatic diagnostic
condensation and therefore cannot silently replace the selected design.

### Supported but rejected: `PreToolUse` command rewriting

Rewriting the command to a wrapper could intercept output before Codex records
it, but makes the new component responsible for faithfully reproducing
stdout, stderr, exit status, cancellation, confirmation, and failure behavior.
That is more code and risk than the source-supported `PostToolUse` boundary.

### Impossible or unsupported for Runtime V1

- `suppressOutput` and `updatedMCPToolOutput`;
- code-mode `continue:false`;
- adding feedback or context beside the original;
- transcript mutation or compaction as result replacement;
- a second parent-model condensation turn;
- Codex subagents as an Apple provider;
- experimental dynamic tools;
- plugin discovery, compilation, mocks, or model prose as runtime proof;
- Apple Python SDK or `fm` without their missing prerequisites; and
- any token-savings claim inferred from output bytes.

## Repository and Linear treatment

No Linear mutation is authorized by this specification.

Recommended issue treatment after written-spec approval:

- **Keep DEV-142 Done.** Reuse its exact policy and corpus.
- **Keep DEV-246 Done.** Preserve its truthful `suppressOutput` blocker as
  historical evidence.
- **Keep DEV-143, DEV-144, DEV-139, DEV-140, DEV-141, and DEV-145 Canceled.**
  Their plans and assumptions predate this successor architecture.
- **Create one new successor capability-gate issue.** It owns only the
  installed direct-boundary, live Apple, composed fallback, and safe-evidence
  proof.
- **Only after that issue passes, create one production Runtime V1 issue.** It
  owns the minimal hook adapter and Swift condenser.
- **Only after production implementation passes deterministic gates, create one
  Codex-only benchmark and packaging issue.**

The chain is strictly sequential:

```text
successor capability gate
  -> production Runtime V1
  -> Codex-only benchmark and packaging
```

A blocked or failed predecessor prevents creation or activation of dependent
work. Old canceled issues are never reopened or repurposed.

## Product decisions captured by this design

The source request and approved discussion establish:

1. Observable replacement semantics, not the field name, define exact original
   V1.
2. Runtime V1 is Codex-only.
3. Direct tool mode is the only eligible Codex execution mode.
4. Code mode and nested code-mode execution are blocked.
5. Apple Foundation Models is the only added generation provider.
6. Codex remains command and final-response owner.
7. Apple receives one bounded condensation consultation with no tools.
8. No command or Apple retry is allowed.
9. Untouched-original fallback is mandatory.
10. The capability gate precedes production implementation.
11. The historical issues remain closed.

Written-spec approval additionally confirms:

- parent-provider suppression is the V1 claim; local UI suppression is not;
- the successor release matrix is Codex-only with 24 pairs and 48 arms;
- latency is measured and reviewed but has no invented hard threshold; and
- MCP or explicit-wrapper fallback requires a separate product-scope decision.

## Limitations and residual risks

- The composed handoff may fail even though both component interfaces are
  separately supported.
- `continue:false` uses stop/feedback lifecycle semantics; the installed host
  may expose unexpected UI or hook-status behavior.
- Apple context pressure may decline enough fixtures to prevent a 10% median
  reduction.
- Apple output may be structurally valid but semantically incomplete.
- Parent-model variability may obscure savings; the fixed paired matrix and
  blocker rules limit but do not eliminate that risk.
- The local host may retain raw tool content in UI, memory, or transient
  telemetry.
- Packaging a native Swift executable for supported hosts remains downstream
  work and cannot be inferred from local compilation.
- No release claim exists until every required live pair is valid.

## Source ledger

| Source | Retrieved or verified | Use |
| --- | --- | --- |
| [Codex hooks documentation](https://developers.openai.com/codex/hooks) | 2026-07-25 | Hook events, trust, `continue:false`, feedback, and unsupported fields |
| [Codex `0.145.0` release](https://github.com/openai/codex/releases/tag/rust-v0.145.0) | 2026-07-25 | Current release and tagged source identity |
| [Direct replacement integration test](https://github.com/openai/codex/blob/rust-v0.145.0/codex-rs/core/tests/suite/hooks.rs#L4497-L4552) | 2026-07-25 | Raw hook input and compact next-provider output |
| [Codex tool-result dispatch](https://github.com/openai/codex/blob/rust-v0.145.0/codex-rs/core/src/tools/registry.rs#L618-L674) | 2026-07-25 | Model-visible replacement path |
| [Code-mode behavior](https://github.com/openai/codex/blob/rust-v0.145.0/codex-rs/core/src/tools/registry_tests.rs#L323-L371) | 2026-07-25 | Direct-mode restriction |
| [Codex MCP documentation](https://developers.openai.com/codex/mcp/) | 2026-07-25 | Supported closest alternative |
| [Codex non-interactive mode](https://developers.openai.com/codex/noninteractive/) | 2026-07-25 | Actual task-usage telemetry boundary |
| [Apple guided generation](https://developer.apple.com/documentation/foundationmodels/generating-swift-data-structures-with-guided-generation) | 2026-07-25 | Structured result generation |
| [Apple context management](https://developer.apple.com/documentation/foundationmodels/managing-the-context-window) | 2026-07-25 | Context and token preflight |
| [Apple `SystemLanguageModel`](https://developer.apple.com/documentation/foundationmodels/systemlanguagemodel) | 2026-07-25 | Local default model availability and locale gates |
| Installed SDK 26.5 interface and fresh local probes | 2026-07-25 | `compiled_sdk_26_5` and `interface_verified_sdk_26_5` claims |
| Live Linear project and issue comments | 2026-07-25 | Current issue status and no-revival boundary |

## Post-approval boundary

This document is a design specification, not an implementation plan.

After user review:

1. If changes are requested, revise this file and repeat self-review.
2. If the written specification is approved, create an implementation plan
   only for the successor capability-gate issue.
3. Stop again before runtime implementation or Linear mutation unless
   separately authorized.
