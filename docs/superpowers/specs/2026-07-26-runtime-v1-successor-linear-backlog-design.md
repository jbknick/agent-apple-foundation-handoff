# Runtime V1 Successor Linear Backlog Design

Project:
[Agent Apple Foundation Handoff](https://linear.app/devprentice/project/agent-apple-foundation-handoff-8297ee383b88)

Decision date: `2026-07-26`

Status: written specification approved on `2026-07-26`; Linear shell creation
and issue-keyed planning are authorized. Runtime implementation remains
unauthorized.

## Summary

Create three new Runtime V1 planning shells now and order them strictly:

```text
[D6] successor capability gate
  -> [I10] production Runtime V1
      -> [V2] benchmark and packaging readiness
```

The seven source steps are requirements, not seven issue boundaries. Steps
1–5 belong to the capability gate, step 6 belongs to production
implementation, and step 7 belongs to benchmark and packaging readiness.

All three issues start in `Backlog`, remain unassigned, and use Linear
`blockedBy` relations. Downstream shells may exist for visibility, but they
are not implementation-ready and must not start until their predecessor is
merged, verified, complete in Linear, and followed by a plan-baseline refresh.

## Verified baseline

- Fresh `origin/main` is
  `934285f38e67d0f956f0848d150d0afa33dbfb4e`.
- The clean planning branch is
  `codex/runtime-v1-supported-handoff-design` at
  `bcb6c302ea6acdcd15e0b77eb455c4efa43bd97d`, seven commits ahead of
  `origin/main`.
- The approved architecture is
  [Runtime V1 Direct Local Diagnostic Consultation](2026-07-25-runtime-v1-direct-local-diagnostic-consultation-design.md).
- The prepared capability work is described by
  [DEV-253 Runtime V1 Successor Capability Gate Implementation Plan](../plans/2026-07-26-dev-253-runtime-v1-successor-capability-gate.md).
- Live Linear on `2026-07-26` contains 20 project issues and no Runtime V1
  successor issue.
- DEV-142 is Done and remains the immutable
  `diagnostic-condensation-v1` contract.
- DEV-246 is Done as capability discovery with terminal historical result
  `blocked:host_replacement_unavailable`.
- DEV-143, DEV-144, DEV-139, DEV-140, DEV-141, and DEV-145 remain Canceled.
- No real Apple response, installed-host model-visible replacement, live
  untouched-original matrix, production runtime, or parent-token reduction
  is currently proven.

## Shared product and execution boundaries

- Apple Foundation Models is the only added generation provider.
- Runtime V1 is Codex-only and direct-tool-mode-only.
- Codex executes the original command exactly once and owns the final response.
- Apple performs one bounded diagnostic-condensation consultation with no
  tools and at most one `respond`.
- Declines and failures preserve the untouched original result.
- No PCC, external LLM, remote fallback, credentials, paid inference, network
  inference, transcript mutation, MCP fallback, wrapper fallback, retry, or
  added parent-model turn is allowed.
- Raw prompts, responses, reasoning, tool content, Apple output, credentials,
  configuration, transcripts, and private paths remain outside committed
  evidence.
- Missing host, SDK, model, hardware, locale, authentication, trust,
  telemetry, or cleanup prerequisites are `blocked`, never passes.
- DEV-142 and DEV-246 remain historical authorities; canceled issues are not
  reopened, renamed, or repurposed.

## Issue 1 — [D6] Prove Runtime V1 direct local consultation capability

### Linear metadata

- State: `Backlog`
- Priority: `Urgent`
- Assignee: unassigned
- Labels: `Decision`, `Security`, `E2E Verifiable`
- New blocker: none

### Goal

Produce one safe `pass`, `blocked`, or `fail` verdict for the installed Codex
`0.145.0` direct-result boundary composed with one real local Apple Foundation
Models response.

### Scope

1. Add `timeoutPluginSha256` and `timeoutHookCurrentHash` to the closed evidence
   schema and its deterministic tests.
2. Reproduce the base plugin, base hook, approved C0 stimulus, timeout plugin,
   and timeout hook identities from the committed tree.
3. Obtain explicit owner approval for those exact identities before live rows.
4. Run the plugin-off baseline and deterministic direct fake-replacement row
   from an authorized outer Codex session.
5. Run one real `SystemLanguageModel.default` structured response through the
   same installed hook and bridge boundary.
6. Run the untouched-original matrix for unapproved stimulus, malformed
   bridge output, bridge crash, adapter crash, and hook timeout.
7. Commit only the normalized capability evidence and bounded interpretation
   after cleanup and evidence-safety checks.

### Boundaries

- This issue proves capability; it does not create the production runtime.
- It does not run the 24-pair product benchmark or claim token savings.
- It does not modify DEV-142 or DEV-246 evidence.
- Its implementation workflow must not invoke nested `codex exec`; live rows
  require an authorized outer session.

### Acceptance criteria

All conditions are conjunctive:

1. Exact Codex CLI `0.145.0` is captured and rechecked.
2. Direct tool mode is active and code mode is disabled.
3. The exact isolated plugin and hook are installed and explicitly trusted.
4. The approved command executes exactly once.
5. The hook receives the original synthetic result.
6. One real Apple `respond` returns one schema-valid result.
7. The DEV-142 semantic validator accepts the complete condensation.
8. The next parent request contains the inline replacement.
9. The original result is absent from that successful next request.
10. No parent-model turn is added relative to the baseline.
11. Every decline and failure row preserves the exact original without rerun.
12. Transient raw data is removed and committed evidence passes safety scans.

Any missing prerequisite is `blocked`. Any invariant violation is `fail`.
Only `pass` unblocks Issue 2.

### Verification

- Focused Runtime V1, DEV-142, and DEV-246 unit suites.
- Generated-artifact synchronization and `git diff --check`.
- SDK 26.5 Swift compilation.
- Base and timeout trust inspections bound to approved hashes.
- Installed-host direct, composed, fallback, evidence-safety, and cleanup rows.
- Full repository regression suite.

## Issue 2 — [I10] Implement production Runtime V1 direct diagnostic consultation

### Linear metadata

- State: `Backlog`
- Priority: `Urgent`
- Assignee: unassigned
- Labels: `Feature`, `Security`, `E2E Verifiable`
- Blocked by: Issue 1

### Goal

Turn the exact passing capability boundary into the smallest supported
production Runtime V1 for selected `diagnostic-condensation-v1` work.

### Scope

1. Promote only the proven hook adapter and native Swift condenser
   responsibilities into the production plugin boundary.
2. Preserve the exact DEV-142 policy, request/result schemas, routing,
   semantic validator, context ceiling, and at-most-one Apple attempt.
3. Package the local executable and hook declarations using the installed-host
   trust and installation behavior proven by Issue 1.
4. Preserve command-once execution, no-output fallback, direct-mode
   enforcement, normalized observations, and bounded cleanup.
5. Add focused deterministic, compilation, installation, trust, success, and
   fallback tests.

### Boundaries

- Do not add a generic runtime framework, MCP server, custom provider
  abstraction, transcript store, telemetry SDK, retry coordinator, or
  persistent state machine.
- Do not add alternate providers or remote fallback.
- Do not claim savings or release readiness.
- Do not begin until Issue 1 is `pass`, merged, complete, and its observed
  interfaces are reconciled into this issue's implementation plan.

### Acceptance criteria

1. Production code uses only the exact boundary proven by Issue 1.
2. The command and final response remain Codex-owned.
3. Apple receives only approved minimized context and no tools.
4. One invocation permits at most one Apple response attempt and no retry.
5. Every decline and failure preserves the untouched original result.
6. Production installation and explicit hook trust are reproducible.
7. Swift compilation and deterministic contract suites pass.
8. No dependency, packaging, security, or evidence boundary is widened.
9. Required review, CI, merge, Linear completion, and clean-state proof pass.

### Verification

- Issue-scoped RED/GREEN tests for the production adapter and bridge.
- SDK 26.5 compile and interface checks.
- Isolated plugin installation and trust checks.
- Direct success and all approved fallback cases.
- Evidence-safety, generated-artifact, focused, and full regression gates.
- Sol/High risk and architecture review before merge.

## Issue 3 — [V2] Prove Runtime V1 token reduction and packaging readiness

### Linear metadata

- State: `Backlog`
- Priority: `Urgent`
- Assignee: unassigned
- Labels: `Quality`, `DevOps`, `E2E Verifiable`
- Blocked by: Issue 2

### Goal

Prove that the production Runtime V1 materially reduces actual parent-model
usage without correctness regressions, extra turns, unsafe evidence, or
unshippable packaging.

### Scope

1. Implement the independent
   `benchmarkProfile = codex-runtime-v1-cost-v1` validator without changing
   DEV-142's historical two-host validator.
2. Run all 24 required Codex-only pairs and 48 arms with identical normalized
   identities across `pluginOff` and `pluginOn`.
3. Capture actual supported parent-model usage, correctness, parent turns,
   Apple attempts, Apple/hook/turn latency, and cleanup state.
4. Validate installation and packaging on the approved supported host
   boundary.
5. Commit only normalized evidence, release arithmetic, and bounded
   operational documentation.

### Boundaries

- Output bytes, Apple tokens, local tokenizers, estimates, or inferred cache
  values cannot substitute for actual parent usage.
- Rows cannot be dropped, imputed, or converted to zero.
- Missing telemetry or a zero plugin-off denominator blocks the affected pair.
- This issue cannot weaken correctness, privacy, cleanup, or blocker rules to
  reach a release verdict.

### Acceptance criteria

```text
requiredPairs = 24
requiredArms = 48
validRequiredPairs = 24
blockedRequiredPairs = 0
medianParentTokenReduction >= 0.10
correctnessRegressions = 0
additionalParentModelTurns = 0
realAppleAttempts >= 1
validatedAppliedRows >= 1
originalCommandReruns = 0
unsafeCommittedEvidenceFindings = 0
```

Latency is measured with explicit denominators and owner-reviewed; no invented
hard latency threshold is added.

### Verification

- Closed benchmark-schema and arithmetic tests.
- Full 24-pair/48-arm live run using actual supported provider usage.
- Correctness-oracle comparison and paired baseline comparison.
- Apple attempt, parent-turn, fallback, latency, evidence-safety, and cleanup
  validation.
- Packaging/install proof, focused and full regression suites, Sol/High
  release review, green CI, merged PR, and clean-state verification.

## Dependency and plan policy

The Linear chain is:

```text
[D6] capability gate
  blocks [I10] production Runtime V1
    blocks [V2] benchmark and packaging readiness
```

Creating all three shells does not authorize downstream execution. Every issue
must contain its own completed, issue-keyed Sol/High
`superpowers:writing-plans` plan before it is implementation-ready.

The Issue 1 plan must reconcile the already prepared capability plan with its
real Linear identifier. Issue 2 and Issue 3 plans may describe approved
intended interfaces, but each records a mandatory baseline refresh after its
predecessor merges. A predecessor `blocked` or `fail` keeps every successor in
Backlog and prohibits implementation.

Execution defaults to `gpt-5.6-sol` with medium reasoning. Architecture,
fallback, security, plan, and formal review decisions remain owned by
`gpt-5.6-sol` with high reasoning.

## Assumptions and defaults

- The existing Linear project remains the owner.
- All three issues are created now for visibility.
- All remain unassigned unless the user later changes assignment.
- No due date or cycle is added.
- The existing project status remains unchanged.
- Existing issue statuses, descriptions, comments, and relations are not
  modified.
- Linear creation happens only after the user approves this written spec.
- Planning artifacts may be committed; implementation remains separately
  gated by the issue chain.
