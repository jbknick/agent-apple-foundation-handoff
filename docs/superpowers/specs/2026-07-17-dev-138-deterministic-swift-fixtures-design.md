# DEV-138 Deterministic Swift Handoff Fixtures Design

Issue: [DEV-138](https://linear.app/devprentice/issue/DEV-138/i4parallel-implement-deterministic-swift-handoff-fixtures-and)

Decision date: `2026-07-17`

Branch/base: `codex/dev-138-deterministic-swift-fixtures` at
`27c7ce6b8d47541711184ceae06b2eecbdc4be8e`

## Authority and status

This design implements the durable DEV-138 decision in Linear comment
`4bf0b19c-1a3a-485b-ac2e-823e05cbee22`. That comment already completed the
mandatory brainstorming gate after loading DEV-128, DEV-130, DEV-131, DEV-132,
DEV-134, and DEV-135. A material change to fixture placement, shipping status,
Apple API ownership, the stable `D-*` catalog, or the host boundary must first
update DEV-138 and affected downstream issues.

The selected design adds a repository-only, Foundation-only Swift reducer and
deterministic scenario executable under `fixtures/dev-138/`. It is proof of
application/plugin architecture invariants. It is not an Apple framework
runtime, a reusable Swift package, a sample app, a live model simulation, or a
shipped plugin capability.

## Approaches considered

### Selected: standalone `swiftc` fixture plus repository oracle

Two Swift source files compile directly with `swiftc`: one owns the pure state,
policy, validation, and reducer types; one owns the synthetic scenario corpus
and executable entry point. The executable emits canonical JSON Lines. A
separate tracked JSONL file owns exact expected results and violation sets, and
Python repository tests compare stdout byte-for-byte on two independent runs.

This is the smallest design that keeps reducer logic, scenario construction,
and the outcome oracle reviewable while avoiding a package manifest or test
framework dependency.

### Rejected: Swift Package or Xcode project

A package or project would create a reusable/runtime-looking surface, add
metadata and build-system scope, and imply product architecture that DEV-132
explicitly rejected. Full Xcode is not required for Foundation-only proof.

### Rejected: extend the DEV-130 fixture in place

DEV-130 is an eight-scenario research proof with a text golden. DEV-138 needs the
complete approved state/security/recovery matrix, machine-readable stable
identities, and downstream oracle ownership. Mutating DEV-130 would blur issue
authority and make its reviewed evidence non-reproducible.

### Rejected: copy DEV-128 Apple API snippets

DEV-128 remains the sole owner of verified Apple signatures and compile
sources. DEV-138 invokes those files directly. Copying declarations would
create a second, drift-prone API authority.

## Scope and non-goals

DEV-138 owns:

- deterministic baton-pass and isolated-consultation application state;
- one active profile/provider, explicit final-response ownership, valid edges,
  finite budgets, independent `stateVersion` and `policyVersion`, and phase
  gating;
- C0-C3 context/provenance, exact grant bindings, tool-result provenance,
  effect identity/ledger/replay behavior, reconciliation, cancellation,
  transcript repair, fallback, and safe evidence;
- stable machine-readable output using the existing `D-*` catalog;
- direct compile/run reuse of authoritative DEV-128 SDK 26.5 fixtures;
- repository-only/package-exclusion proof; and
- normalized, synthetic, credential-free evidence.

DEV-138 does not add or modify production skills/references, plugin metadata,
generated artifacts, schemas, the generator, a Swift package, UI, persistence,
networking, credentials, PCC/custom-provider calls, live model generation,
Apple runtime Skills, Evaluations, Instruments, hooks, agents, commands, MCP
servers, release metadata, or publishing behavior.

## Exact artifact topology

| Path | Responsibility |
| --- | --- |
| `fixtures/dev-138/HandoffReducer.swift` | Foundation-only state, policies, typed events, validation checks, pure reducer, and normalized result types. |
| `fixtures/dev-138/DeterministicScenarios.swift` | Synthetic cases, `@main`, sorted execution, and canonical JSONL serialization. |
| `fixtures/dev-138/expected-results.jsonl` | Sole DEV-138 expected outcome oracle: sorted case IDs, statuses, exact sorted violation arrays, and normalized observables. |
| `fixtures/dev-138/README.md` | Truth boundary, case/check map, exact compile/run/SDK commands, and blocker semantics. |
| `tests/test_dev_138_fixtures.py` | Compile/run/golden/repeat tests, oracle-separation mutations, DEV-134 mapping, SDK 26.5 probes, environment records, and offline package-exclusion proof. |
| `tests/test_plugin_contract.py` | One narrow assertion that repository fixtures remain outside the effective plugin package; existing package oracle remains authoritative. |
| `docs/research/evidence/dev-138-command-transcript.md` | Normalized final commands, counts, hashes, environment, package proof, blockers, and nonclaims. |

No file below `plugins/apple-foundation-models-handoff/` is added or edited.
`scripts/sync_generated_artifacts.py` and all three generated outputs remain
unchanged.

## Reducer and validation contract

The framework-neutral state contains:

```text
schemaVersion = 1.0
pattern = baton_pass | isolated_consultation
stateVersion
policyVersion
phase = stable | transitioning | recoveryRequired | terminated
sourceProfile / sourceProvider
destinationProfile / destinationProvider
activeProfile / activeProvider
finalResponseOwner
allowedEdges
transitionCount / transitionBudget
toolCount / toolBudget
effectCount / effectBudget
contextEnvelope
boundaryGrant
pendingTransition
stableCheckpoint
effectLedger
repairFacts
auditEvents
fallback
```

Only typed trusted events enter the reducer. Prompt, model, repository,
retrieved, summary, and tool text remain untrusted data. Phase validation occurs
before budget or authority mutation: the event's required phase is checked
first, then the validator's shared state-phase coherence predicate rejects a
malformed same-phase snapshot without changing it. A valid proposal snapshots
the active profile/provider plus independent state and policy versions. Both
proposal and commit boundaries reject either version drifting before the baton
commits.
Transitioning-state validation also requires the exact pending baton marker,
current source, allowed edge, and an unvisited destination. A
committed baton-pass activates the destination and transfers final ownership; a
consultation returns to the parent and never transfers final ownership.

Known pre-effect failure or cancellation restores the checkpoint. Possible or
uncertain effect commit records one effect and remains `recoveryRequired` until
typed reconciliation establishes either confirmed-applied or
confirmed-not-applied external truth. Confirmed-applied effects cannot retry;
confirmed-not-applied effects authorize at most one retry. No-safe reconciliation
remains repair-blocked in `recoveryRequired`. Late/replayed events preserve
authority, phase, pending/checkpoint state, counts, ledger, and repair facts and
emit no command. Reconciliation attempts increase monotonically for the same
effect. Awaiting recovery records exactly zero attempts before a retry and one
after the sole retry. Stable reconciled facts record exactly one attempt before
and through retry result acceptance, then two only after post-retry
reconciliation. Malformed recovery state cannot use a reducer event to
self-heal. Confirmed-not-applied truth cannot restore retry authority after the
one retry was consumed. Ordinary budget termination is `stable`-only.

Context fields bind class, source, subject, purpose, destination, retention,
and redaction. C3 and unknown data never cross a model boundary. A disallowed
field rejects the whole envelope. A grant independently binds person, session,
source profile/provider, destination profile/provider, purpose, exact
classes/fields/tools, retention, expiry at the deterministic request time,
exceptional C2 permission,
`stateVersion`, and `policyVersion`. Accepted tool results bind call ID,
tool/version/provider, result type, the exact originating command state, and one
total unresolved ledger record for the effect; accepting a result consumes that
record once. A retried effect accepts only the retry command's call/result; a
late original result cannot close it. Every command maps to one ledger
effect/state/executor identity. Historical command/record version pairs remain
valid after a later state transition, but mismatched or future versions fail.
The ledger stays within its effect budget and admits only the committed
checkpoint and declared truth/reconciliation combinations. Stable resolved
ledger truth and repair facts must cross-bind one effect, command lifecycle,
truth, positive attempt count, and retry authority.

The effect guarantee is application-controlled at-most-once command emission
plus reconciliation. The fixture never claims exactly-once delivery or
external-effect rollback. A retry command preserves a typed
confirmed-not-applied
reconciliation basis, so renewed uncertainty and later reconciliation do not
erase valid lineage. A retry without that lineage remains a replay violation.
Initial and consultation commands must carry no retry basis.
Fallback may only use an already authorized
equal-or-lower provider/context/retention/tool/effect boundary; otherwise the
result is explicit unavailable/degraded.

Evidence extension and prohibited-content checks are case-insensitive, while
SHA-256 verification remains bound to the original, unmodified content bytes.

## Canonical executable output

Each line of `expected-results.jsonl` and executable stdout is one compact JSON
object with sorted keys and this closed shape:

```text
schemaVersion
caseId
status = pass | fail
violations[]
pattern
activeProfile
finalResponseOwner
phase
stateVersion
policyVersion
transitionCount
transitionBudget
executorCommandCount
effectCount
fallback
contextIncluded[]
contextExcluded[]
auditEvents[]
```

Cases execute in lexical `caseId` order. Arrays whose order is not semantic are
sorted before encoding. `JSONEncoder` uses `.sortedKeys` and
`.withoutEscapingSlashes`; the executable writes UTF-8 with exactly one newline
per record. It never reads `expected-results.jsonl`, and no scenario embeds an
expected status or expected violations. That oracle separation is tested.

## Stable check ownership

DEV-138 reuses, and does not rename or extend, the approved deterministic
catalog:

| Check | DEV-138 meaning |
| --- | --- |
| `D-SCHEMA-001` | Closed versioned state/result shape. |
| `D-ROUTE-001` | Expected and allowed destination/pattern route. |
| `D-OWNER-001` | Exactly one correct final owner for baton-pass or consultation. |
| `D-TRANSITION-001` | Valid edge, finite budget, and no revisited state. |
| `D-TOOL-001` | Authorized actor/tool, exact command binding, bound result provenance, and budget. |
| `D-CONTEXT-001` | Required minimized context is present. |
| `D-CONTEXT-002` | Forbidden, C3, unknown, or unredacted disallowed context is absent. |
| `D-GRANT-001` | Every grant binding, including independent versions, matches. |
| `D-PHASE-001` | Event phase, checkpoint, cancellation, coherent repair facts, and bound recovery persistence are valid. |
| `D-EFFECT-001` | Each command has one budgeted, non-future, exactly paired ledger identity. |
| `D-EFFECT-002` | Replay emits no command and retry carries confirmed-not-applied lineage. |
| `D-FALLBACK-001` | Fallback does not expand trust or authority. |
| `D-EVIDENCE-001` | Case-normalized path/content/type checks and original-content hash binding are safe. |
| `D-RUBRIC-001` | Remains owned and executed by the inherited DEV-131 rubric proof; Swift does not duplicate semantic scoring. |

`docs/research/evidence/dev-134-activation-prototype.json` remains the sole
15-case activation prototype. Repository tests assert that its six positive,
six negative, and three ambiguous identities reference only this catalog, with
exactly seven `direct_workflow` and eight `non_positive_router` metadata owners.
Those owner values are not emitted envelope fields.
DEV138 baton-pass, consultation, flawed-reducer, and recovery cases provide the
runtime-invariant mappings for `DEV134-POS-001`, `POS-002`, `POS-004`,
`POS-006`, and `AMB-003`; the other activation identities remain router/host
concerns and are not simulated as Apple behavior.

## Exact deterministic case matrix

An adversarial input that is correctly blocked is a passing case. A deliberately
invalid normalized outcome is a failing case and must emit exactly the sorted
violations below.

| Case ID | Expected violations | Required observation |
| --- | --- | --- |
| `DEV138-BATON-VALID` | `[]` | Destination becomes active/final owner with one committed transition. |
| `DEV138-CONSULTATION-VALID` | `[]` | Child transcript is isolated and parent remains active/final owner. |
| `DEV138-INJECTION-IGNORED` | `[]` | Forged instructions in untrusted text emit no command or typed event. |
| `DEV138-C3-BLOCKED` | `[]` | Whole envelope is blocked; sentinel is absent from request/audit. |
| `DEV138-C2-REDACTED` | `[]` | Only named/redacted exceptional C2 field crosses its bound destination. |
| `DEV138-PRECOMMIT-ROLLBACK` | `[]` | Known pre-effect failure restores source/checkpoint. |
| `DEV138-UNCERTAIN-RECOVERY` | `[]` | Possible commit enters persistent recovery with one ledger row. |
| `DEV138-RECONCILIATION-UNAVAILABLE` | `[]` | No safe reconciliation path returns repair-blocked/unavailable while phase remains `recoveryRequired`; authority, pending/checkpoint state, counts, ledger, and repair facts are byte-for-byte unchanged and no command is emitted. |
| `DEV138-REPLAY-SUPPRESSED` | `[]` | Same effect ID keeps one ledger row and emits no replay command. |
| `DEV138-RECONCILED-RETRY` | `[]` | Confirmed-not-applied reconciliation precedes the one authorized retry; confirmed-applied truth never authorizes retry. |
| `DEV138-CANCEL-PRECOMMIT` | `[]` | Cancellation restores checkpoint without ledger mutation. |
| `DEV138-CANCEL-UNCERTAIN` | `[]` | Uncertain cancellation preserves repair facts in recovery. |
| `DEV138-MODEL-UNAVAILABLE-SAFE` | `[]` | Equal/lower authorized fallback is selected. |
| `DEV138-MODEL-UNAVAILABLE-EXPLICIT` | `[]` | No safe route returns unavailable without authority expansion. |
| `DEV138-TRANSCRIPT-REPAIRED` | `[]` | Partial entries and call/output pairs are repaired before reuse. |
| `DEV138-SCHEMA-MISSING` | `["D-SCHEMA-001"]` | Required version/state field is absent. |
| `DEV138-ROUTE-DISALLOWED` | `["D-ROUTE-001"]` | Destination is not the declared/allowed route. |
| `DEV138-OWNER-BATON-SOURCE` | `["D-OWNER-001"]` | Source incorrectly retains baton-pass final ownership. |
| `DEV138-OWNER-CONSULT-CHILD` | `["D-OWNER-001"]` | Child incorrectly becomes consultation final owner. |
| `DEV138-EDGE-INVALID` | `["D-TRANSITION-001"]` | Transition uses an unapproved edge. |
| `DEV138-BUDGET-EXCEEDED` | `["D-TRANSITION-001"]` | Command occurs after finite transition budget. |
| `DEV138-LOOP` | `["D-TRANSITION-001"]` | State is revisited in one bounded flow. |
| `DEV138-TOOL-UNAUTHORIZED` | `["D-TOOL-001"]` | Actor/tool/budget is unauthorized. |
| `DEV138-RESULT-SPOOFED` | `["D-TOOL-001"]` | Call/tool/version/provider/type/state provenance mismatches. |
| `DEV138-CONTEXT-REQUIRED-MISSING` | `["D-CONTEXT-001"]` | A declared required field is absent. |
| `DEV138-C3-LEAK` | `["D-CONTEXT-002"]` | C3/unknown data appears in provider context. |
| `DEV138-C2-UNREDACTED` | `["D-CONTEXT-002"]` | Disallowed unredacted C2 data crosses the boundary. |
| `DEV138-GRANT-STATE-STALE` | `["D-GRANT-001"]` | Grant state revision is stale. |
| `DEV138-GRANT-POLICY-STALE` | `["D-GRANT-001"]` | Grant policy revision is stale. |
| `DEV138-GRANT-DESTINATION-MISMATCH` | `["D-GRANT-001"]` | Destination profile/provider mismatches. |
| `DEV138-GRANT-PURPOSE-MISMATCH` | `["D-GRANT-001"]` | Purpose mismatches. |
| `DEV138-GRANT-CLASS-MISMATCH` | `["D-GRANT-001"]` | Class is outside the exact allowance. |
| `DEV138-GRANT-FIELD-MISMATCH` | `["D-GRANT-001"]` | Field is outside the exact allowance. |
| `DEV138-GRANT-AUTH-EXPIRED` | `["D-GRANT-001"]` | The bound authorization expiry is no longer current. |
| `DEV138-PHASE-INVALID` | `["D-PHASE-001"]` | Event is accepted outside its authoritative phase. |
| `DEV138-RECOVERY-TERMINATED` | `["D-PHASE-001"]` | Unresolved recovery is incorrectly terminated. |
| `DEV138-TRANSCRIPT-UNBALANCED` | `["D-PHASE-001"]` | Reuse occurs with partial/unbalanced call-output entries. |
| `DEV138-EFFECT-DUPLICATE-LEDGER` | `["D-EFFECT-001"]` | One effect ID has multiple ledger entries. |
| `DEV138-EFFECT-REPLAY-COMMAND` | `["D-EFFECT-002"]` | Replayed effect emits a second command. |
| `DEV138-EFFECT-RETRY-BEFORE-RECONCILE` | `["D-EFFECT-002"]` | Retry precedes explicit reconciliation. |
| `DEV138-CANCEL-ERASES-RECOVERY` | `["D-EFFECT-001","D-PHASE-001"]` | Late cancellation clears recovery/ledger facts. |
| `DEV138-FALLBACK-EXPANDS-TRUST` | `["D-FALLBACK-001"]` | Fallback broadens provider/context/tool/effect authority. |
| `DEV138-EVIDENCE-LEAKAGE` | `["D-EVIDENCE-001"]` | Raw prompt/tool content, credential sentinel, absolute path, or `.trace` is present. |

Every approved grant binding also has an independent mutation test, even when
the compact executable matrix groups a binding under a broader explicit case.
Each mutation starts from the same valid grant, changes exactly one field, and
must return only `["D-GRANT-001"]`:

| Mutation identity | Sole changed binding |
| --- | --- |
| `grant_person_mismatch` | Person identity. |
| `grant_session_mismatch` | Session identity. |
| `grant_source_profile_mismatch` | Source profile. |
| `grant_source_provider_mismatch` | Source provider. |
| `grant_destination_profile_mismatch` | Destination profile. |
| `grant_destination_provider_mismatch` | Destination provider. |
| `grant_purpose_mismatch` | Purpose. |
| `grant_class_mismatch` | Exact allowed class set. |
| `grant_field_mismatch` | Exact allowed field set. |
| `grant_tool_mismatch` | Exact allowed tool set. |
| `grant_retention_mismatch` | Retention policy. |
| `grant_expired` | Expiry/authentication validity; mirrors explicit `DEV138-GRANT-AUTH-EXPIRED`. |
| `grant_exceptional_c2_missing` | Exceptional C2 permission. |
| `grant_state_version_stale` | `stateVersion`. |
| `grant_policy_version_stale` | `policyVersion`. |

The source and destination profile/provider mutations are separate tests; a
combined provider-boundary mutation cannot substitute for either. The expiry
mutation records only normalized fixture time/validity and never reads a live
credential or authentication session.

## Apple SDK 26.5 truth boundary

DEV-138 compiles the authoritative DEV-128 sources in place. Executed evidence
labels are exact machine values `compiled_sdk_26_5` and
`interface_verified_sdk_26_5`; the Foundation-free reducer itself is
`pseudocode_deterministic_mock` even though `swiftc` compiles it.

The SDK row captures Swift 6.3.3, `xcrun --sdk macosx --show-sdk-version`, and
target `arm64-apple-macos26.0` without committing the literal executable or SDK
path. Executable and SDK-directory device/inode/type/mode/size/time snapshots
are rechecked around invocations. Exact SDK 26.5 positive probes cover stable
surface, the Generable macro, availability, transcript round-trip, session
isolation, and the existing baton mock. The installed interface hash remains
`ff2285670b0966addb9827dc895a3ee3c9db6e186baae62c034fed012632aacc`.

OS 27 profile/session/tool-calling-mode and Evaluations probes pass only when
compilation fails with each capability-specific diagnostic. If a future
toolchain supports one, the row must be reclassified; the diagnostic may not be
weakened. Full Xcode, iPhone SDK, Instruments, Evaluations, Xcode/OS 27 runtime
features, PCC/custom providers, runtime Skills, and live model generation remain
separate blocked or not-run capabilities.

## Offline packaging and evidence boundary

The plugin package root remains `plugins/apple-foundation-models-handoff`.
`tests/test_plugin_contract.py` already scans it without following symlinks and
accepts only approved package entries. DEV-138 adds a focused assertion that
`fixtures/dev-138` exists only at repository root and that no `fixtures` entry
or DEV-138 path appears in a copied effective package. This proof uses only a
temporary local copy: no host, network, credential, cache, or installation is
required.

Tracked evidence is synthetic/normalized. It excludes raw/live prompts,
responses, reasoning, tool arguments/results, credentials, private
configuration, real user/third-party data, literal user/home/worktree or SDK
paths, raw `PATH`, raw diagnostics, `.trace`, and `.xcresult`. The transcript
records versions, target, stable diagnostic classes, exit codes, case counts,
and hashes only.

## Environment and blocker semantics

| Condition | Status | Required behavior |
| --- | --- | --- |
| Foundation-only `swiftc` compile/run succeeds | `pass` | Compare two byte-identical runs with the exact JSONL oracle. |
| `swiftc` missing/non-runnable | `blocked/missing_binary` | Emit normalized blocker; do not claim fixture pass. |
| `xcrun` or macOS SDK missing | `blocked/sdk_unavailable` | Reducer may still run, but no Apple compile label passes. |
| SDK is not exactly 26.5 | `blocked/sdk_version_mismatch` | Do not reuse 26.5 labels or diagnostics; re-evaluate the matrix. |
| Expected negative probe has wrong/generic diagnostic | `fail` | Preserve raw diagnostic transiently; commit only stable class/exit code. |
| Xcode/OS 27 beta prerequisite absent | `blocked` | Never convert documentation or an SDK 26.5 failure into runtime proof. |
| BATS 1.13.0 available | `pass` when `tests/plugin_skeleton.bats` runs 3/3 | It remains a required inherited gate. |
| Claude Code, `pre-commit`, or `markdownlint` | `blocked/deferred_by_owner` | Do not invoke or substitute; DEV-141 retains the release blocker. |
| Network/PCC/provider credential/live model | `not_applicable` | Fixture architecture intentionally has no such operation. |

## Completion and downstream contract

Implementation is complete only when every case appears exactly once, stdout
matches the sole oracle on two runs, mutation tests prove oracle independence,
the full D catalog remains stable, DEV-128 probes are truthfully classified,
DEV-130 and DEV-131 regressions pass, repository tests and BATS pass, package
exclusion is offline/credential-free, evidence is normalized and scanned, and
the worktree contains only DEV-138 paths.

DEV-136 and DEV-137 may cite case/check identities but never ship fixture code
or advertise it as capability. DEV-139 consumes the JSONL oracle and environment
semantics. DEV-141 reruns the offline/SDK/package matrix and preserves all beta
and owner-deferred blockers.
