# DEV-130 Handoff Security, Privacy, and Failure Threat Model Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish an Apple-source-grounded handoff threat model and execute a deterministic offline mock that proves DEV-130's five mandatory adversarial outcomes.

**Architecture:** Keep Apple API facts and version labels in research evidence, while expressing the selected security policy as a framework-neutral typed reducer. Split the reducer from its executable scenario runner so policy state and adversarial expectations are independently reviewable; capture exact commands, outputs, blockers, and non-claims in a separate evidence transcript.

**Tech Stack:** Markdown, Swift 6.3.2 standard library, macOS Command Line Tools SDK 26.5 inspection, POSIX shell validation, official Apple documentation and WWDC26 sources.

## Global Constraints

- Do not implement authentication, authorization, encryption, a production skill, or a production Swift runtime architecture.
- Do not claim on-device execution makes a workflow safe or that PCC guarantees apply to custom providers.
- Do not permit an automatic PCC/custom-provider transition without a matching explicit data-boundary policy.
- Treat prompts, retrieved content, tool output, summaries, model text, and repository text as untrusted data; only typed application events may affect authority.
- Use `C0 Public`, `C1 Task-private`, `C2 Sensitive`, and `C3 Never-transfer` plus provenance; unknown provider-bound data fails closed.
- Require bound provider grants, immediate confirmation for high-impact effects, one stable active state, valid versioned transitions, finite budgets, provenance-bound results, least-context envelopes, and no silent trust-expanding fallback.
- Promise application-controlled at-most-once execution plus reconciliation/recovery, never exactly-once or external-effect rollback.
- Keep default evidence metadata-only; raw prompts, responses, reasoning, tool arguments/results, credentials, real user content, and `.trace` files are excluded from committed artifacts.
- Default tests use no model generation, network service, PCC, provider credentials, paid service, full Xcode, or hardware requirement.
- Apple `.onToolCall`, `.historyTransform`, mutable session transcript, and transcript error policies are official Xcode 27 beta guidance; the installed SDK 26.5 session transcript is get-only.
- Missing SDK, binary, target, Instruments, Evaluations, or hardware support is an explicit blocker, never a pass.

**Stack base:** temporary local DEV-129 head `b4e12a6`; the parent will rebase this branch onto final DEV-129 before push or PR creation.

**Design:** `docs/superpowers/specs/2026-07-17-dev-130-handoff-threat-model-design.md`

## File map

- `fixtures/dev-130/HandoffSecurityPolicy.swift`: non-production data classes, grants, transition/effect state, typed events, decisions, and pure reducer.
- `fixtures/dev-130/AdversarialScenarios.swift`: executable assertions for mandatory adversarial scenarios.
- `fixtures/dev-130/expected-output.txt`: byte-for-byte output contract for repeatable E2E proof.
- `docs/research/dev-130-handoff-threat-model.md`: durable assets/actors/boundaries/threats/controls/invariants/residual-risks report.
- `docs/research/evidence/dev-130-command-transcript.md`: commands, exact outputs, environment labels, source checks, blockers, and non-claims.

## Commit boundaries

1. `docs(DEV-130): design handoff threat model`
2. `docs(DEV-130): plan handoff threat model research`
3. `test(DEV-130): add adversarial handoff policy fixture`
4. `docs(DEV-130): publish threat model evidence`

Review corrections use narrow follow-up commits. Do not squash, push, merge,
tag, or release from this task.

---

### Task 1: Build the deterministic adversarial reducer fixture

**Files:**

- Create: `fixtures/dev-130/AdversarialScenarios.swift`
- Create: `fixtures/dev-130/expected-output.txt`
- Create: `fixtures/dev-130/HandoffSecurityPolicy.swift`

**Interfaces:**

- Consumes: only Swift standard-library values and synthetic fixture data.
- Produces: `DataClass`, `Provider`, `ContextField`, `BoundaryGrant`, `TransitionEdge`, `TransitionProposal`, `EffectCommitStatus`, `Phase`, `HandoffState`, `SecurityEvent`, `ExecutorCommand`, `ReducerDecision`, and `HandoffSecurityPolicy.reduce(state:event:)`.
- Produces exact executable output used by Task 2's evidence transcript.

- [ ] **Step 1: Write the failing adversarial runner and golden output**

Create `AdversarialScenarios.swift` first. Its `@main` runner must construct
synthetic state, call `HandoffSecurityPolicy.reduce`, fail with `fatalError`
when an assertion is false, and emit exactly these lines:

```text
PASS indirect-injection unauthorizedCommands=0
PASS sensitive-provider-transfer blocked=true sentinelLeaked=false
PASS tool-failure-precommit phase=stable active=research
PASS tool-failure-uncertain phase=recoveryRequired effects=1 commands=1
PASS transition-budget count=3 fourthCommand=false terminal=transitionBudgetExceeded
PASS cancellation-precommit phase=stable pending=false
PASS cancellation-uncertain phase=recoveryRequired effects=1 commands=1
SUMMARY passed=7 failed=0
```

Write the same bytes to `expected-output.txt`. The runner must assert:

```swift
expect(injected.state.executorCommandCount == 0, "untrusted text emitted a command")
expect(blocked.providerRequest == nil, "C3 content crossed the provider boundary")
expect(!blocked.state.audit.joined().contains(secretSentinel), "sentinel leaked to audit")
expect(precommit.state.phase == .stable, "pre-commit failure did not restore stable state")
expect(uncertain.state.phase.isRecoveryRequired, "uncertain effect did not require recovery")
expect(budget.state.transitionCount == 3, "transition budget count changed")
expect(cancelled.state.pendingTransition == nil, "cancel left a pending transition")
```

- [ ] **Step 2: Run the RED compile and prove the missing policy causes failure**

Run:

```bash
set +e
swiftc -parse-as-library fixtures/dev-130/AdversarialScenarios.swift \
  -o /tmp/dev130-red >/tmp/dev130-red.out 2>&1
red_rc=$?
set -e
test "$red_rc" -ne 0
rg -q "cannot find.*HandoffState|cannot find.*HandoffSecurityPolicy" /tmp/dev130-red.out
```

Expected: compile exits nonzero only because the required mock policy types do
not exist yet.

- [ ] **Step 3: Implement the minimal policy reducer**

Create `HandoffSecurityPolicy.swift` with these exact type relationships:

```swift
enum DataClass: Int, Hashable { case c0Public, c1TaskPrivate, c2Sensitive, c3NeverTransfer }
enum Provider: Hashable { case onDevice, pcc, custom(String) }
struct ContextField: Equatable { let name: String; let value: String; let classification: DataClass; let source: String; let subject: String; let purpose: String; let retention: String; let redacted: Bool }
struct BoundaryGrant: Equatable { let destination: Provider; let purpose: String; let allowedClasses: Set<DataClass>; let allowedFieldNames: Set<String>; let policyVersion: Int }
struct TransitionEdge: Hashable { let sourceProfile: String; let destinationProfile: String }
struct TransitionProposal: Equatable { let destinationProfile: String; let destinationProvider: Provider; let purpose: String; let fields: [ContextField]; let grant: BoundaryGrant?; let sourceStateVersion: Int; let policyVersion: Int }
enum EffectCommitStatus: Equatable { case notCommitted; case uncertain(effectID: String) }
enum Phase: Equatable { case stable; case transitioning; case recoveryRequired; case terminated(String) }
struct ExecutorCommand: Equatable { let kind: String; let destination: Provider }
struct ReducerDecision: Equatable { var state: HandoffState; let command: ExecutorCommand?; let providerRequest: String? }
enum SecurityEvent: Equatable { case untrustedContext(source: String, text: String); case proposeTransition(TransitionProposal); case transitionCommitted; case transitionToolFailed(EffectCommitStatus); case cancel(EffectCommitStatus) }
struct HandoffSecurityPolicy { static func reduce(state: HandoffState, event: SecurityEvent) -> ReducerDecision }
```

`HandoffState` must carry `activeProfile`, `provider`, `stateVersion`, `policyVersion`,
`transitionCount`, `maxTransitions`, `phase`, `pendingTransition`,
`checkpoint`, `allowedEdges`, `executorCommandCount`, `effectLedger`, and
`audit`. Implement only the behavior required by the adversarial assertions:

- untrusted context appends metadata-only audit and never creates a command;
- transition proposals are phase gated before budget evaluation and fail closed
  for stale source state, policy-version mismatch, invalid edges,
  missing/mismatched grants, unapproved fields/classes, or any `C3` field;
- a valid proposal captures a checkpoint, increments the transition count and
  command count, and serializes only approved field values;
- commit selects the destination, increments only `stateVersion`, and clears the
  checkpoint/pending transition while leaving `policyVersion` stable;
- pre-commit failure/cancel restores the checkpoint without changing the effect
  ledger;
- uncertain failure/cancel records the synthetic effect ID once and enters
  recovery without another command; late failure/cancel events outside
  `transitioning` preserve authority, phase, pending state, checkpoint, and
  ledger; and
- a proposal after the transition budget is exhausted terminates with exact
  reason `transitionBudgetExceeded` and emits no command.

Audit strings contain types, decisions, classes, and synthetic IDs only. They
must never include `ContextField.value`.

- [ ] **Step 4: Run the GREEN compile and exact-output gate**

Run:

```bash
set -euo pipefail
swiftc -parse-as-library \
  fixtures/dev-130/HandoffSecurityPolicy.swift \
  fixtures/dev-130/AdversarialScenarios.swift \
  -o /tmp/dev130-adversarial
/tmp/dev130-adversarial | tee /tmp/dev130-adversarial.out
diff -u fixtures/dev-130/expected-output.txt /tmp/dev130-adversarial.out
/tmp/dev130-adversarial > /tmp/dev130-adversarial-second.out
cmp /tmp/dev130-adversarial.out /tmp/dev130-adversarial-second.out
! rg -q 'DEV130_SECRET_SENTINEL' /tmp/dev130-adversarial.out
```

Expected: compile and both runs exit `0`; output reports seven passes and is
byte-identical across runs; the secret sentinel is absent.

- [ ] **Step 5: Run fixture scope and hygiene gates**

Run:

```bash
set -e
test "$(find fixtures/dev-130 -maxdepth 1 -type f | wc -l | tr -d ' ')" -eq 3
! rg -n 'import FoundationModels|URLSession|PrivateCloudCompute|apiKey|token=' fixtures/dev-130
! find fixtures/dev-130 -type f \( -name '*.trace' -o -name '*.xcresult' \) | grep .
! rg -n 'TBD|TODO|FIXME|fill in details|implement later' fixtures/dev-130
git diff --check
```

Expected: three fixture files, no Apple runtime/network/credential dependency,
no trace artifact, no placeholder, and clean whitespace.

- [ ] **Step 6: Commit the fixture atomically**

```bash
git add fixtures/dev-130/HandoffSecurityPolicy.swift \
  fixtures/dev-130/AdversarialScenarios.swift \
  fixtures/dev-130/expected-output.txt
git commit -m "test(DEV-130): add adversarial handoff policy fixture"
```

Expected: one commit containing exactly three fixture files.

---

### Task 2: Publish the source-grounded threat model and evidence transcript

**Files:**

- Create: `docs/research/dev-130-handoff-threat-model.md`
- Create: `docs/research/evidence/dev-130-command-transcript.md`

**Interfaces:**

- Consumes: Task 1 exact output, the installed SDK interface/hash, official
  Apple source pages, and the approved DEV-130 Linear decisions.
- Produces: binding security invariants and downstream contracts for DEV-132,
  DEV-134, DEV-136, DEV-137, DEV-138, DEV-139, and DEV-141.

- [ ] **Step 1: Prove both report artifacts are absent**

```bash
test ! -e docs/research/dev-130-handoff-threat-model.md
test ! -e docs/research/evidence/dev-130-command-transcript.md
```

Expected: both commands exit `0`.

- [ ] **Step 2: Write the threat-model report**

Use `apply_patch`. The report must have exactly these top-level sections:

1. `Scope, authority, and evidence labels`
2. `Host and SDK baseline`
3. `Official Apple fact ledger`
4. `Assets and actors`
5. `Trust boundaries`
6. `Data classification and transfer policy`
7. `Confirmation and authorization boundaries`
8. `Deterministic state and effect model`
9. `Mandatory testable invariants`
10. `Recommended controls`
11. `Threat, mitigation, and residual-risk matrix`
12. `Transcript, failure, cancellation, and repair policy`
13. `Availability and fallback policy`
14. `Trace, logging, and evidence policy`
15. `Adversarial E2E matrix and executed proof`
16. `Downstream decision contract`

The report must cover every threat named in DEV-130: indirect injection, data
exfiltration, over-sharing, spoofed tool results, authorization confusion,
duplicate effects, transition loops, partial failure, cancellation,
inconsistent active state, sensitive logs, and unavailable-model fallback. It
must distinguish baton-pass from isolated consultation, PCC from custom
providers, mandatory invariants from recommendations, pre-commit rollback from
uncertain external effects, and Apple facts from plugin policy.

The adversarial matrix must specify initial state, ordered event, expected final
state, expected command/effect count, and redacted evidence for at least these
16 cases: injection, disallowed transfer, pre/post-effect tool failure,
transition budget, cancellation, duplicate retry, spoofed result, confirmation
replay, summary poisoning, unsafe fallback, stale concurrency, transcript
repair, auth expiry, opaque provider tools, trace leakage, and error/fallback
mapping. Link the executed Task 1 fixture and mark the remaining cases as
deterministic downstream requirements, not falsely executed proof.

Use retrieval date `2026-07-17` and direct official Apple links for WWDC26
sessions 242, 243, 319, 339, 347, and 8009; Foundation Models Tool/tool-calling,
session/tool error, transcript, and logging documentation; and PCC core
requirements, stateless computation, attack analysis, and restricted
observability.

- [ ] **Step 3: Write the evidence transcript**

Use `apply_patch`. The transcript must have exactly these top-level sections:

1. `Scope and non-claims`
2. `Environment and installed SDK evidence`
3. `Official primary-source checks`
4. `Fixture RED-GREEN cycle`
5. `Adversarial E2E execution`
6. `Semantic and evidence-safety gates`
7. `Host-assisted blockers`

Record exact commands, exit codes, relevant outputs, interface hash, Task 1 RED
diagnostic class, compiled fixture output, repeated-run comparison, source-link
checks, report semantic gates, existing DEV-128 regression results, and exact
full-Xcode/Instruments/Evaluations blockers. Do not include temporary absolute
paths, raw user/model data, or claim a source link check proves API behavior.

- [ ] **Step 4: Run report semantics and source gates**

```bash
set -euo pipefail
report=docs/research/dev-130-handoff-threat-model.md
transcript=docs/research/evidence/dev-130-command-transcript.md
test -s "$report"
test -s "$transcript"
test "$(rg '^## ' "$report" | wc -l | tr -d ' ')" -eq 16
test "$(rg '^## ' "$transcript" | wc -l | tr -d ' ')" -eq 7
for term in assets actors 'trust boundaries' 'C0 Public' 'C3 Never-transfer' \
  'indirect prompt injection' 'data exfiltration' over-sharing spoofing \
  'authorization confusion' 'duplicate effects' 'transition loops' \
  'partial failure' cancellation 'single-active' 'sensitive logs' \
  'unavailable-model fallback' 'baton-pass' 'isolated consultation' \
  'at-most-once' 'recoveryRequired' 'residual risk' 'metadata-only'; do
  rg -qi "$term" "$report"
done
for issue in DEV-132 DEV-134 DEV-136 DEV-137 DEV-138 DEV-139 DEV-141; do
  rg -q "$issue" "$report"
done
test "$(rg -o 'https://(developer|security)\.apple\.com/[^ )]+' "$report" | sort -u | wc -l | tr -d ' ')" -ge 14
! rg -n 'TBD|TODO|FIXME|fill in details|implement later' "$report" "$transcript"
! rg -n 'DEV130_SECRET_SENTINEL' "$report" "$transcript"
git diff --check
```

Expected: exact section counts, all issue threats and downstream contracts,
at least 14 distinct official Apple links, no placeholders/sentinel disclosure,
and clean whitespace.

- [ ] **Step 5: Rerun fixture and SDK regression gates**

```bash
set -euo pipefail
swiftc -parse-as-library \
  fixtures/dev-130/HandoffSecurityPolicy.swift \
  fixtures/dev-130/AdversarialScenarios.swift \
  -o /tmp/dev130-adversarial
/tmp/dev130-adversarial > /tmp/dev130-adversarial.out
diff -u fixtures/dev-130/expected-output.txt /tmp/dev130-adversarial.out

SDK=$(xcrun --sdk macosx --show-sdk-path)
TARGET=arm64-apple-macos26.0
swiftc -typecheck -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/stable-surface.swift
for fixture in availability-probe transcript-roundtrip session-isolation baton-pass-state; do
  swiftc -parse-as-library -target "$TARGET" -sdk "$SDK" \
    "fixtures/dev-128/compiled/$fixture.swift" -o "/tmp/dev130-$fixture"
  "/tmp/dev130-$fixture"
done
```

Expected: DEV-130 exact output passes, and all five prior stable/pseudocode
DEV-128 fixtures type-check or run with their documented outputs.

- [ ] **Step 6: Commit report and transcript atomically**

```bash
git add docs/research/dev-130-handoff-threat-model.md \
  docs/research/evidence/dev-130-command-transcript.md
git commit -m "docs(DEV-130): publish threat model evidence"
```

Expected: one commit containing exactly the two research artifacts.

## Final issue verification

After task reviews and corrections, invoke
`superpowers:verification-before-completion` and run from the exact final head:

```bash
set -euo pipefail
base=b4e12a6
expected_paths="$(printf '%s\n' \
  'docs/research/dev-130-handoff-threat-model.md' \
  'docs/research/evidence/dev-130-command-transcript.md' \
  'docs/superpowers/plans/2026-07-17-dev-130-handoff-threat-model.md' \
  'docs/superpowers/specs/2026-07-17-dev-130-handoff-threat-model-design.md' \
  'fixtures/dev-130/AdversarialScenarios.swift' \
  'fixtures/dev-130/HandoffSecurityPolicy.swift' \
  'fixtures/dev-130/expected-output.txt' | sort)"
actual_paths="$(git diff --name-only "$base"...HEAD | sort)"
test "$actual_paths" = "$expected_paths"

swiftc -parse-as-library \
  fixtures/dev-130/HandoffSecurityPolicy.swift \
  fixtures/dev-130/AdversarialScenarios.swift \
  -o /tmp/dev130-final
/tmp/dev130-final > /tmp/dev130-final.out
diff -u fixtures/dev-130/expected-output.txt /tmp/dev130-final.out
/tmp/dev130-final > /tmp/dev130-final-second.out
cmp /tmp/dev130-final.out /tmp/dev130-final-second.out

! git ls-files | rg '\.(trace|xcresult)$'
! rg -n 'DEV130_SECRET_SENTINEL' docs/research/dev-130-handoff-threat-model.md \
  docs/research/evidence/dev-130-command-transcript.md
git diff --check "$base"...HEAD
test -z "$(git status --porcelain)"
```

Then rerun all Task 2 semantic/source gates, the prior DEV-128 regression gates,
and the expected Xcode 27/Instruments/Evaluations blocker probes. Generate a
whole-branch review package from `b4e12a6` to the exact head and obtain a fresh
review with no open Critical or Important findings.

## Linear and parent handoff

1. Add a DEV-130 completion-evidence comment with exact commits, seven paths,
   fixture output, report/source gates, reviews, SDK regression results,
   blocker classification, and skipped checks.
2. Link repository paths/commit hashes as reproducible evidence.
3. Leave DEV-130 `In Progress` because the parent still must rebase onto final
   DEV-129, push, open the atomic stacked PR, and move the issue to `In Review`.
4. Report the local head and rebase base to the parent. Do not push or open a PR.
