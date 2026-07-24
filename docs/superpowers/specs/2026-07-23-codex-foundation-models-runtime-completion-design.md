# Codex-Only Apple Foundation Models Runtime Completion Design

Project:
[Agent Apple Foundation Handoff](https://linear.app/devprentice/project/agent-apple-foundation-handoff-8297ee383b88)

Decision date: `2026-07-23`

Approved direction: the user confirmed that this project uses Apple Foundation
Models only during Codex runs through the Codex plugin system. The previously
suggested mobile/TestFlight scope belonged to another project and is excluded.
The user approved the corrected issue breakdown with `lgtm`.

Baseline amendment: on `2026-07-24`, the user replaced the active and future
Codex execution baseline with exact Codex CLI `0.145.0`. Historical evidence
captured on `0.144.5` remains immutable and may not satisfy a current host row.

## Summary and baseline

The repository baseline is `main` at `b6b2289`, matching `origin/main` after a
fresh fetch. DEV-142 is complete and supplies the frozen
`diagnostic-condensation-v1` request, policy, result, privacy, fallback, and
benchmark corpus contracts. The repository does not yet contain a production
Apple bridge or Codex runtime hook.

The remaining runtime outcome is deliberately narrow:

```text
completed eligible Codex Bash result
  -> trusted Codex plugin PostToolUse boundary
  -> DEV-142 deterministic cost router
  -> DEV-246 exact-host result-replacement capability gate
  -> DEV-143 local Apple Foundation Models bridge
  -> DEV-144 validated Codex continuation
```

Apple Foundation Models is the only generation provider in this path. The
runtime has no mobile application, Claude Code adapter, external model, PCC,
remote fallback, credential, paid service, or network inference.

The five positive workflow skills and the non-positive preselection router
remain separate guidance capabilities. This decision narrows only the
diagnostic-condensation runtime and its release evidence; it does not silently
remove existing shared metadata or rewrite completed workflow evidence.

## Authority and bounded supersession

The following sources remain authoritative unless this design expressly narrows
their downstream runtime scope:

- `docs/superpowers/specs/2026-07-21-dev-142-runtime-cost-routing-and-benchmark-design.md`
- `docs/architecture/apple-foundation-models-handoff-mvp-decision-record.md`
- current official Codex plugin and hook documentation
- the installed SDK interfaces and executed evidence required by `AGENTS.md`

The baseline amendment specifically supersedes the `0.144.5` prerequisite in
the 2026-07-21 DEV-143 design. Its remaining bridge contract stays
authoritative. DEV-143 now requires a passing exact `0.145.0` DEV-246 result.

DEV-142's versioned request, routing, validation, privacy, fallback, and
correctness contracts remain unchanged. Its former two-host runtime ownership
and release matrix are narrowed as follows:

- DEV-144 is the only host runtime adapter.
- DEV-145's Claude Code runtime adapter is canceled as out of scope.
- The retained corpus is 24 hash-bound cases for Codex CLI `0.145.0`.
- The required paired runtime matrix is therefore 24 plugin-off/plugin-on pairs,
  or 48 arms.
- Historical 48-pair/96-arm cross-host deterministic evidence remains truthful
  for DEV-142's completed contract work, but it is not the downstream release
  requirement.

This is a product-scope amendment, not permission to weaken the DEV-142 cost
floor, correctness requirements, privacy policy, original-result preservation,
or blocker rules.

## Codex capability gate

Current official Codex documentation establishes that:

- a plugin can bundle lifecycle hooks at `hooks/hooks.json` or through the
  `.codex-plugin/plugin.json` `hooks` entry;
- plugin hook paths are relative to and contained by the installed plugin root;
- installed or enabled plugin hooks require explicit trust before execution;
- `PostToolUse` can observe shell and unified-exec completion as canonical
  `Bash`; and
- `PostToolUse` output is documented as feedback and control fields, not as a
  byte-for-byte replacement or suppression contract for the original tool
  result.

DEV-246 therefore owns an exact-host capability probe before any production
implementation begins. The probe must use the captured Codex CLI `0.145.0`
executable and prove whether the plugin hook can prevent the original eligible
tool result from entering the next parent-model request while supplying the
validated compact result.

If the captured host cannot do this, DEV-246 records `blocked` with normalized
evidence and DEV-143 and every downstream issue remain blocked. Feedback-only
output, an additional parent turn, transcript mutation, an MCP/model-selected
detour, or sending both the original and condensed result does not satisfy the
product outcome and must not be adopted as a fallback. Any alternative
interface or task-boundary change returns to Sol and the user for a new
architecture decision.

For exact Codex CLI `0.145.0`, an official-manual statement that `PostToolUse`
`suppressOutput` is parsed but not implemented or supported is sufficient to
record `blocked:host_replacement_unavailable` before authentication or live
execution. The project must not copy a credential or run an unsupported effect
merely to reproduce the documented limitation.

The DEV-246 executable is intentionally exact-version. If the frozen
`0.145.0` manual no longer contains both unsupported-effect statements, the
row fails as `official_manual_contract_drift` and returns to Sol/user. It does
not infer or exercise a new trust, task, or boundary interface without a
refreshed architecture.

The manual-only blocker is valid only for pinned official-manual SHA-256
`6cff0c5701d5a8b10ae497b5dda6ee70f478518d4fa029558168ee2bcc18918b`.
Caller-supplied bytes with another digest fail as
`official_manual_hash_mismatch`.

## Terminal capability decision — 2026-07-24

DEV-246 verified the pinned manual and recorded
`blocked:host_replacement_unavailable`. Codex CLI `0.145.0` parses
`PostToolUse.suppressOutput` but does not implement or support that effect.
The probe therefore stopped before authentication, installation, trust, or a
model task.

DEV-143, DEV-144, DEV-139, DEV-140, and DEV-141 are canceled rather than
advertised as implementation-ready. Their conditional plans are intentionally
not published. Resumption requires a later owner-approved Codex baseline whose
official contract supports model-visible replacement, followed by a new
brainstorming decision, refreshed spec, and Sol-authored plans.

## Responsibility boundaries

### DEV-246: Codex capability discovery boundary

DEV-246 owns only the synthetic, exact-host experiment that determines whether
Codex CLI `0.145.0` exposes a trusted `PostToolUse` contract capable of replacing
or suppressing the original tool result before the next parent-model request.
It freezes the observed input/output schema, captures normalized evidence, and
returns `pass`, `blocked`, or `fail`.

It does not add production runtime code, invoke Apple Foundation Models, mutate
real transcripts, claim capability from model prose, or choose an alternative
architecture.

### DEV-143: local Apple provider boundary

DEV-143 owns one standalone Swift package at
`runtime/apple-foundation-models-bridge`. It accepts one versioned request on
standard input, repeats every deterministic eligibility and policy gate, makes
at most one local Foundation Models attempt, validates the generated result,
and emits one terminal `applied`, `declined`, or `fail` envelope.

It does not own Codex hook discovery, host result replacement, plugin trust,
parent continuation, provider telemetry, benchmark arithmetic, or original
tool execution.

### DEV-144: Codex plugin runtime boundary

DEV-144 owns the Codex plugin lifecycle hook, hook input normalization, immutable
original-result preservation, deterministic router invocation, one bridge
attempt, bridge-result validation, safe continuation, and Codex-specific
benchmark capture.

It may add canonical hook inputs and generated Codex metadata only through the
repository's existing generation ownership model. It does not modify the five
workflow skills, the non-positive preselection router, DEV-142 policy values, or
DEV-143 provider behavior.

### DEV-139: integrated evidence boundary

DEV-139 owns a reproducible Codex-only evidence harness covering installed
plugin identity, trust and hook loading, exact-host activation, selected and
nonselected routing, local Apple application or normalized blocker, fallback,
at-most-once behavior, result visibility, provider usage, correctness, latency,
and cost arithmetic.

Structural discovery, file presence, compile-only evidence, or a fake bridge
cannot prove the runtime capability or savings claim.

### DEV-140: documentation boundary

DEV-140 owns contributor and user documentation for Codex installation,
explicit hook trust, supported command classes, Apple availability, local-only
data handling, deterministic and live verification, cost evidence, fallback,
and limitations.

It documents only commands and outcomes proven by prior issues. It does not
claim a release, marketplace availability, savings, or live Apple execution
without evidence.

### DEV-141: final acceptance boundary

DEV-141 owns the independent Codex-only regression, privacy, evidence, and
release-readiness decision. It does not implement or repair the runtime. Missing
required host, Apple, or provider-usage evidence remains `blocked`.

### DEV-133: separate deferred validation debt

DEV-133 remains `In Review` outside the runtime blocker chain. Its repository
guidance implementation is already merged and has an existing issue plan at
`docs/superpowers/plans/2026-07-17-dev-133-repository-guidance.md`.
Its deferred Claude semantic and missing-tool validation debt remains truthful;
this Codex runtime amendment neither completes nor expands it.

## Ordered Linear issue chain

The approved sequential chain is:

```text
DEV-142 Done
  -> DEV-246 Codex result-replacement capability discovery
  -> DEV-143 local Apple bridge
  -> DEV-144 Codex plugin runtime
  -> DEV-139 Codex runtime and cost evidence
  -> DEV-140 Codex documentation
  -> DEV-141 Codex final acceptance
```

The Linear planning update will:

1. create DEV-246 in `Backlog` as the sole prerequisite for DEV-143;
2. reset DEV-143 to `Backlog` until its completed plan is linked;
3. retain DEV-144 in `Backlog`;
4. cancel DEV-145, remove it from the active blocker chain, and record the
   Codex-only decision;
5. narrow DEV-139, DEV-140, and DEV-141 to the responsibilities above and set
   them to `Backlog` until their plans are linked;
6. encode each active issue as blocked only by the immediately preceding issue;
7. leave DEV-133 `In Review` and outside this chain; and
8. add a bounded scope-propagation record to DEV-142 without reopening its
   completed implementation.

Each active implementation issue receives one Sol-authored plan and one
issue-scoped PR. No dependent issue starts until its predecessor has local
verification, required Sol review, green CI, merged-PR evidence when code
changed, Linear completion proof, synchronized `main`, and clean local state.

## Public interfaces and data flow

### Bridge process interface

DEV-143 consumes and returns the exact DEV-142 schema identities:

```text
schemaVersion = 1
policyVersion = diagnostic-condensation-v1
action = condense_diagnostic_output
resultType = diagnostic_condensation
```

The process accepts exactly one UTF-8 JSON request and emits exactly one UTF-8
JSON terminal envelope. The Codex adapter invokes it through an argument vector,
never a shell. Unknown keys, duplicate values, future versions, identity drift,
invalid provenance, disallowed data, or invalid bounds fail closed.

### Codex plugin interface

The plugin bundles a trusted lifecycle hook within the installed plugin root.
The adapter accepts only a `PostToolUse` event whose canonical tool name is
`Bash`, uses documented hook fields, and does not depend on the unstable
transcript format.

The immutable original result stays host-owned for fallback. Only a
schema-valid, provenance-bound, size-valid `applied` response is eligible for
model-visible use. Every decline or failure preserves the untouched original
result and never reruns the command.

### Evidence interface

Committed evidence is normalized and metadata-only. It may include stable
status and reason codes, counts, hashes, versions, exit codes, timings, provider
usage totals, and bounded correctness verdicts. It excludes raw prompts,
responses, reasoning, tool inputs/results, Apple output, credentials, private
configuration, literal host paths, transcripts, `.trace`, and `.xcresult`.

## Project acceptance criteria

The remaining project is complete only when:

- a fresh installed and trusted Codex plugin loads the approved hook from its
  cached package;
- exact-host evidence proves that an eligible completed `Bash` result invokes
  the local Apple bridge at most once and that only the validated compact result
  reaches the next parent-model request;
- nonselected, undersized, oversized, disallowed, unavailable, malformed,
  timed-out, canceled, and invalid-result rows preserve the original result and
  never rerun the underlying command;
- a supported Apple environment produces a live schema-valid local result, or
  the required live row remains explicitly `blocked`;
- the 24-case/48-arm Codex paired matrix records provider-reported usage,
  correctness, parent turns, latency, replacement ratio, and fallback rate;
- release arithmetic shows at least 10% median total parent-token reduction,
  zero correctness regressions, zero added parent turns, and zero blocked
  required pairs;
- default validation remains deterministic, offline, credential-free,
  Apple-generation-free, and network-free;
- documentation matches the verified install, trust, runtime, fallback, and
  limitation evidence;
- independent final review finds no unresolved contract, privacy, evidence, or
  release-readiness issue; and
- the final repository and Linear state are synchronized, reviewed, and clean.

## Verification plan

Every implementation plan must include focused RED/GREEN tests plus the
repository gates that apply to its merged tree. The common deterministic gates
are:

```bash
python3 scripts/sync_generated_artifacts.py --write
python3 scripts/sync_generated_artifacts.py --check
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Issue-specific verification additionally requires:

- DEV-246: exact Codex `0.145.0` executable capture, pinned official-manual
  provenance, hash-bound synthetic plugin identity, and normalized `pass`,
  `blocked`, or `fail` output. When the pinned manual records unsupported
  `PostToolUse` suppression, the terminal manual-only blocker stops before
  authentication, installation, trust, or a model task. Installation, trust,
  sentinel execution, and direct model-boundary evidence are required only
  under a refreshed plan after the manual contract permits live discovery;
- DEV-143: `swift test`, `swift build`, protocol-process tests, SDK interface
  verification, and opt-in live `LanguageModelSession` proof;
- DEV-144: the frozen passing DEV-246 contract, hook-schema tests, plugin
  generation and cache tests, selected/declined/failure/fallback tests, and a
  fresh installed-plugin run;
- DEV-139: the full 24-case/48-arm paired Codex harness, provider usage and
  correctness calculation, privacy scans, and deterministic cleanup;
- DEV-140: command/link verification and clean-session documentation
  walkthroughs using only already-proven behavior; and
- DEV-141: full merged-tree regression, exact evidence hashes, independent Sol
  review, blocker audit, release arithmetic, and clean-state verification.

Missing prerequisites are blockers, never passes. Compile-only, mock-only,
structural, version, or file-presence evidence cannot substitute for live
runtime or model-visible replacement proof.

## Assumptions and defaults

- Work proceeds sequentially through the active blocker chain.
- `gpt-5.6-sol` with `reasoning_effort: medium` executes implementation, tests,
  debugging, proof capture, and routine Linear/PR operations from linked plans.
- Sol owns every implementation plan, architecture or fallback change, formal
  non-trivial diff review, re-review, and merge-readiness judgment.
- One issue produces at most one implementation PR; planning-only changes do
  not authorize implementation.
- The repository's captured Codex CLI `0.145.0` and installed SDK requirements
  remain the executed baselines until separately amended.
- Final push, merge, tag, marketplace publication, or release requires the
  authority and gates stated by the repository workflow.
