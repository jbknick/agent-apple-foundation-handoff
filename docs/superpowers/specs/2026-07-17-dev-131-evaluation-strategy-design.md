# DEV-131 Evaluation, Observability, and E2E Proof Design

Issue: [DEV-131](https://linear.app/devprentice/issue/DEV-131/r5parallel-define-evaluation-observability-and-e2e-proof-requirements)

Evidence dates: original capture `2026-07-17`; current-host refresh `2026-07-19`

## Purpose

DEV-131 defines how the project proves generated handoff architectures and the
eventual cross-host plugin are correct, safe, useful, observable, and
regression-resistant. It also supplies a small executable research proof that
accepts conforming synthetic results and rejects intentionally invalid ones.

This issue does not implement the production test harness, production plugin
metadata, production skills, Apple runtime architecture, or live-model CI.
DEV-139 owns the final cross-host harness after its content and fixture blockers
complete.

## Selected approach

The selected approach has three independent evidence layers:

1. **Deterministic offline contract gate.** Stable machine checks evaluate
   normalized policy, transition, tool, context, recovery, evidence, and rubric
   integrity fields without a model, network, credential, paid service,
   particular hardware, PCC, or full Xcode.
2. **Rubric quality gate.** A human reviewer scores a synthetic or reviewed
   redacted/normalized response using anchored dimensions. An optional model
   judge can supplement but not replace the human verdict or deterministic
   security checks.
3. **Real-host acceptance and optional Apple evidence.** Fresh Claude Code and
   Codex sessions prove activation, reference loading, and output behavior.
   Apple Evaluations and Instruments add optional Xcode 27 beta quality and
   profiling evidence when their exact prerequisites exist.
4. **Paired runtime-cost evidence.** Eligible plugin-off/plugin-on runs record
   provider usage fields and routing/correctness metrics without estimating
   missing data. Provider telemetry, normalization, or live Apple blockers
   keep the row `blocked`.

Documentation alone was rejected because it cannot execute the issue's
valid/invalid proof. A production harness was rejected because it would
pre-empt DEV-139 and depend on plugin decisions that are not complete.

## Deterministic contract

Each check has a stable ID and reports `pass`, `fail`, `blocked`, or
`not_applicable`. Zero denominators are `not_applicable`, never fabricated as a
perfect rate. A negative fixture succeeds only when the validator rejects it
with exactly the expected sorted violation set.

The proof runner covers these families:

- `D-SCHEMA-001`: required versioned policy and result shape;
- `D-ROUTE-001`: allowed and expected destination;
- `D-OWNER-001`: exactly one final response from the declared owner;
- `D-TRANSITION-001`: allowed edges, finite budget, and no revisited state;
- `D-TOOL-001`: actor/tool allowlist and tool-call budget;
- `D-CONTEXT-001` and `D-CONTEXT-002`: required inclusion and forbidden
  exclusion;
- `D-GRANT-001`: independent state and boundary-policy revision matching;
- `D-PHASE-001`: events occur only in valid phases and cannot erase recovery;
- `D-EFFECT-001` and `D-EFFECT-002`: one ledger record, no executor command on
  replay, and a `confirmed_absent` reconciliation before retry after an
  uncertain commit;
- `D-FALLBACK-001`: only declared safe fallback outcomes;
- `D-EVIDENCE-001`: allowlisted paths, classifications, redaction, and hashes;
  and
- `D-RUBRIC-001`: stimulus hash, dimension set, score bounds, rationales,
  anchors, arithmetic, critical thresholds, and verdict integrity.

These checks are framework-neutral application policy. They do not claim that
Foundation Models authorizes actions, provides exactly-once delivery, undoes
external effects through transcript rollback, enforces context minimization,
or selects the application's final-response owner.

DEV-130's binding correction is inherited: `stateVersion` is the monotonic
state/concurrency revision; `policyVersion` independently identifies the
approved boundary policy. A grant matches both. Invalid-phase events cannot
clear an in-flight transition or unresolved recovery. At-most-once proof
replays the same synthetic effect ID, expects one ledger entry, and expects no
executor command for the replay. An uncertain commit reconciles before retry.
The reconciliation outcome must be `confirmed_absent`; `still_unknown` and
`confirmed_committed` fail closed. Nested policy/result records use exact
schemas, context inclusion equals the declared minimum, and evidence paths are
a subset of the evidence allowlist.

## Rubric contract

The architecture rubric uses a four-level anchored scale:

- `1`: unsafe or unsupported;
- `2`: materially incomplete;
- `3`: correct with minor omissions; and
- `4`: complete and well-grounded.

The required dimensions are:

1. pattern selection;
2. Apple API grounding and version labeling;
3. security-policy completeness;
4. context minimization;
5. failure and recovery behavior;
6. testability and observability; and
7. limitation honesty.

A result passes when every dimension exists, the mean is at least `3.0`, and
security policy, failure recovery, and limitation honesty are each at least
`3`. Every score has a rationale and resolvable response anchor. Deterministic
validation proves only the assessment's structure and arithmetic; a human or
optional model judge supplies the semantic scores.

The committed stimulus is wholly synthetic and hashed. Raw real prompts,
responses, hidden reasoning, real user data, secrets, credentials, private
host configuration, and Instruments `.trace` files are excluded.

## Dataset and proof boundary

The minimum executable corpus contains two synthetic workflow identities—a
handoff-design result and a handoff-review result—without creating discoverable
production `SKILL.md` files. It includes:

- conforming happy-path and replayed-effect cases;
- transition loop and budget exhaustion;
- wrong final-response owner;
- missing context policy;
- unauthorized tool use;
- stale state/policy grant;
- invalid-phase state movement;
- retry before reconciliation;
- unsafe evidence manifest; and
- valid and invalid rubric assessments.

The research report additionally specifies downstream cases for ambiguous
routing, invalid edges, pre/post-commit failure, cancellation, unavailable
model, privacy-sensitive context, prompt injection, context pressure, duplicate
effects, spoofed results, unsafe fallback, and trace leakage.

The proof runner uses only the Python standard library. Expected outcomes live
in `index.json` and never enter individual validator functions. The runner emits
machine-readable JSON and exits nonzero if any actual violation set differs
from its expected set.

## Cross-host acceptance boundary

The MVP host matrix separates structural setup from capability:

- canonical/generated drift and schema checks run offline;
- Claude validation and isolated load, and Codex isolated marketplace/install,
  are structural prerequisites;
- explicit skill invocation and a complete versioned output contract require
  fresh real sessions in both hosts;
- progressive disclosure requires evidence that routed references were loaded;
- valid and invalid normalized runtime fixtures use the same check IDs; and
- unavailable required binary, model, or authentication support is `blocked`,
  never silently skipped or passed.

Plugin discovery, manifest validation, installation, cache contents, and an
enabled flag do not prove activation or task completion.

The runtime-cost row pairs identical eligible workflows under plugin-off and
plugin-on conditions. It preserves provider-reported input, cached-input,
output, and reasoning usage when exposed and records parent turns, Apple
attempts, replacement ratio, declines, fallback rate, latency, and
correctness. A versioned provider normalization defines total parent-model
tokens. Release requires at least 10% median reduction, zero correctness
regressions, and zero extra parent-model turns. Discovery, activation, byte
counts, compile checks, and DEV-138 mocks cannot satisfy this live row.

## Apple evaluation and profiling boundary

Apple's current primary sources establish that Evaluations is new in Xcode 27
and integrates datasets, `Metric`, `Evaluator`, aggregation, Swift Testing,
model judges, score dimensions, and tool-call trajectories. Trajectory
expectations can constrain tool names, arguments, ordering, and disallowed
calls. They do not establish app-owned authorization, idempotency, context
minimization, or final-response ownership.

The improved Foundation Models Instrument exposes request/session/inference,
instruction, prompt/response, profile, and tool control flow plus token usage,
Time to First Token, Tokens per Second, and Total Latency. Apple warns that
trace files contain prompt and response data and can be sensitive. Host proof
requires full Xcode 27 plus a compatible current OS target/device.

The 2026-07-19 host refresh observes macOS 26.5.1 (25F80), Xcode 26.6
(17F113) at `/Applications/Xcode.app/Contents/Developer`, Swift 6.3.3/driver
1.148.6, macOS and iPhoneOS SDK 26.5, xctrace 16.0, simctl, and two booted
simulators. `Evaluations` still fails to import, the legacy `Instruments`
lookup exits 72, and Xcode/SDK 27 is absent. These are narrow optional-host
blockers; available tools do not prove a runtime model or cost row. Claude Code
2.1.140 and Codex CLI 0.144.5 are binary prerequisites only and do not prove
plugin activation.

## Evidence-bundle contract

The committed example bundle is synthetic and safe to store. It contains:

- a redacted Markdown summary;
- machine-readable check results;
- normalized commands and exit codes;
- an allowlisted environment description;
- a cross-host status matrix;
- the synthetic rubric stimulus and assessment; and
- a manifest containing schema/issue/run/commit metadata plus SHA-256 and
  classification for every other included file.

The manifest does not hash itself. Its SHA-256 is published separately in
Linear. Commands normalize the repository path to `<repo>` and never dump the
complete environment. Environment data excludes usernames, home paths,
hostnames, serials, hardware UUIDs, provisioning identifiers, tokens,
authentication state, and user configuration.

Redaction is a failing gate: scan before hashing, assemble only allowlisted
paths and extensions, verify every declared hash, and scan the complete bundle
again. Raw event streams, real user content, secrets, and `.trace` files remain
outside committed evidence.

## Artifact topology

DEV-131 adds these bounded artifact families:

- `docs/superpowers/specs/2026-07-17-dev-131-evaluation-strategy-design.md`;
- `docs/superpowers/plans/2026-07-17-dev-131-evaluation-strategy.md`;
- `fixtures/dev-131/README.md`, `proof_runner.py`, `tests/`, `cases/`, and
  `example-evidence/`;
- `docs/research/evidence/dev-131-evaluation-command-transcript.md`; and
- `docs/research/dev-131-evaluation-strategy.md`.

The fixture tree is explicitly research proof, not the final DEV-139 harness.
No production plugin metadata, skill, agent, hook, command, MCP server,
dependency, generated Codex artifact, runtime package, or network-backed test is
introduced.

## Verification and commit boundary

The issue is maintained as one atomic 28-path delta against current `main`.
Verification includes the
test suite's observed red/green evidence, exact expected rejection IDs, rubric
and evidence-bundle checks, source links, installed-host blocker probes,
placeholder and sensitive-path scans, `git diff --check`, and fresh exact-head
validation. The sequential executor owns exactly three main-agent review/fix
rounds, exact-lease publication, a current Linear/GitHub reread, head-locked
squash merge, reviewed-tree equality, and a merged smoke gate; Round 1 does not
claim those later steps are complete.

Runtime-evidence propagation is explicit: DEV-142 owns provider usage capture
and normalization; DEV-143 owns paired runtime/routing measurements; DEV-144
owns correctness and eligibility; DEV-145 owns aggregation and the release
floor. None transfers production runtime ownership into DEV-131.
