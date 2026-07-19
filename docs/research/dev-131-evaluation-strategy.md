# DEV-131 Evaluation, Observability, and E2E Proof Strategy

Evidence retrieval date: `2026-07-17`

## Decision summary

DEV-131 adopts three independent evidence layers:

1. a mandatory deterministic offline contract gate;
2. a human-owned rubric quality gate, with an optional model judge as
   supplementary nondeterministic evidence; and
3. real Claude Code, Codex, and optional Apple Xcode 27 host evidence when the
   exact prerequisites exist.

The offline gate is the release-independent baseline. It uses synthetic,
normalized policy/result records and stable check IDs. It requires no model,
network, credentials, paid service, Apple Intelligence availability, PCC,
device, simulator, or full Xcode. Each check reports `pass`, `fail`, `blocked`,
or `not_applicable`. If a metric denominator is zero, its value is `null` and
its status is `not_applicable`; it is never converted into a perfect rate, a
zero-percent pass, or evidence that an optional capability works.

Rubric scoring, live-host task behavior, Apple Evaluations, and Instruments are
nondeterministic or host-dependent layers. They never override a deterministic
security failure. Results from materially different datasets, prompts, model
providers, toolchains, host versions, or policies are not directly comparable
unless those variables are recorded and intentionally controlled.

The report uses these evidence states:

- **executed:** the named command or case ran and produced captured evidence;
- **blocked:** a required prerequisite is absent, with the exact blocker
  recorded;
- **not run:** the layer is outside this issue or cannot start because its
  prerequisite is blocked; and
- **not_applicable:** a valid computation has no denominator or does not apply
  to that dataset.

Explicit non-goals are a production plugin, production `SKILL.md`, private or
complete host metadata, the production DEV-139 harness, live-model CI, Apple
runtime architecture, model authorization, exactly-once external effects, or
committed raw traces. DEV-131 defines requirements and supplies research proof;
it does not claim loading, activation, or end-to-end capability for a plugin
that has not yet been implemented.

## Evaluation matrix

Every row has a stable check/evidence ID. `D-*` IDs are executable offline
checks. `E-*` IDs define downstream or optional evidence records; an `E-*` row
cannot pass from documentation, binary presence, installation, or an enabled
flag alone.

| Evaluation area | Owner layer | Stable check/evidence ID | Dataset | Metric or invariant | Pass rule | Blocked rule | Evidence output |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Loading/discovery — Claude Code | Host structure | `E-CLAUDE-LOAD-001` | Built production plugin in an isolated Claude configuration | Validator, discovery, isolated load, and cache/package path integrity | Installed Claude version validates and loads the exact candidate plugin from an isolated configuration with normalized paths | Binary missing, candidate plugin absent, auth/config prerequisite unavailable, or isolation cannot be established | Host version, normalized commands/exit codes, validator summary, discovered plugin ID, candidate commit |
| Loading/discovery — Codex | Host structure | `E-CODEX-LOAD-001` | Built production plugin in an isolated `CODEX_HOME` | Marketplace registration, discovery, install, enabled state, and cache integrity | Installed Codex version discovers and installs the exact candidate through its isolated marketplace workflow | Binary missing, candidate plugin/marketplace absent, install prerequisite unavailable, or isolation cannot be established | Host version, normalized commands/exit codes, plugin ID, cache manifest hash, candidate commit |
| Activation — Claude Code | Real-host capability | `E-CLAUDE-ACTIVATE-001` | Valid and invalid handoff tasks in a fresh Claude session | Explicit skill activation, routed reference loading, complete output contract, correct rejection | Fresh real session explicitly invokes the named capability, loads required references, emits the versioned result, and rejects the invalid task with expected IDs | Loading prerequisite blocked, no compatible model/session/auth, or automation unavailable | Redacted task identity/hash, activation/reference events, normalized result, check IDs, exit/final status |
| Activation — Codex | Real-host capability | `E-CODEX-ACTIVATE-001` | Same valid/invalid task identities in a fresh Codex task | Same capability contract as Claude, not mere structural parity | Fresh real task observes the same canonical capability, references, result contract, and expected rejection semantics | Loading prerequisite blocked, no compatible model/session/auth, or automation unavailable | Redacted task identity/hash, activation/reference evidence, normalized result, check IDs, exit/final status |
| Architecture routing and ownership | Offline deterministic | `D-SCHEMA-001`, `D-ROUTE-001`, `D-OWNER-001` | All 11 normalized cases | Versioned shape, allowed/expected destination, exactly one declared final owner | Every valid case passes; each invalid case produces only its oracle-declared sorted violation set | Never blocked in the default Python gate; missing/unreadable corpus is a schema/corpus failure | Machine JSON case records, oracle-match booleans, corpus count/status |
| Runtime transition and tool behavior | Offline deterministic | `D-TRANSITION-001`, `D-TOOL-001` | Valid workflows plus loop, budget, and unauthorized-tool cases | Valid edges, contiguous acyclic path, finite transition/tool budgets, actor/tool allowlist | Valid cases stay within graph/budgets; negative cases reject with the exact stable ID | Default gate is not blocked; live Apple execution is a separate optional row | Transition/tool checks and exact rejection IDs |
| Context and boundary policy | Offline security/privacy | `D-CONTEXT-001`, `D-CONTEXT-002`, `D-GRANT-001` | Happy path, replayed effect, missing-context-policy, stale-grant | Exact minimal inclusion, forbidden exclusion, independently matching `stateVersion` and `policyVersion` | Included fields exactly equal required fields, forbidden fields stay excluded, and both versions match | Default gate is not blocked; missing or undeclared included fields fail closed | Check results, classified normalized field names, no values |
| Phase, effect, recovery, fallback | Offline security/privacy | `D-PHASE-001`, `D-EFFECT-001`, `D-EFFECT-002`, `D-FALLBACK-001` | Valid workflows plus invalid phase and retry-before-reconciliation | Canonical phase/event order, one effect/ledger identity, one original command, no replay command, reconciliation outcome before retry, safe fallback | Every invariant holds; uncertain effects retry only after `confirmed_absent`; replay never emits another command | Default gate is not blocked; external exactly-once behavior is not claimed | Stable effect IDs, counts, phase/reconciliation events, exact rejection IDs |
| Evidence safety | Offline security/privacy | `D-EVIDENCE-001` | Valid example bundle plus unsafe evidence case | Strict allowlist, normalized relative paths, classifications, double content scan, SHA-256 match | All eight declared files are safe, present, nonsymlinked, correctly classified, and hash-verified; unsafe case rejects | Default gate is not blocked; raw trace capture remains excluded | Manifest, verified-file count, derived check result, exact rejection ID |
| Cross-host structure | Repository/generation | `E-CROSSHOST-STRUCT-001` | Canonical source plus generated/adapted host artifacts after DEV-132/DEV-135 | Schema validation, deterministic generation, drift-free shared content, host-specific thin adapters | Both host artifacts derive from the approved canonical ownership model and drift check is clean | Topology/generator/candidate plugin absent or a required host validator unavailable | File inventory, generator command, diff/drift result, schema results, commit |
| Cross-host capability equivalence | DEV-139 real-host harness | `E-CROSSHOST-CAP-001` | Paired valid/invalid fresh-host tasks | Same canonical semantics, stable IDs, required references, and security/failure behavior; presentation may differ | Both real hosts pass their activation rows and normalized semantic comparison | Either host activation blocked; one host result is never extrapolated to the other | Paired run IDs, normalized results, check-ID comparison, honest per-host states |
| Rubric assessment | Human quality | `D-RUBRIC-001` | SHA-256-bound synthetic or approved redacted response plus assessment | Seven unique anchored dimensions, integer scores 1–4, rationales, arithmetic, threshold and critical gates | Mean at least `3.0`; security-policy completeness, failure/recovery behavior, and limitation honesty each at least `3`; human verdict matches | Missing stimulus/assessment/reviewer or unresolvable evidence blocks semantic review; malformed record fails deterministically | Stimulus SHA-256, dimension scores/rationales/anchors, mean, reviewer type, verdict |
| Apple Evaluations | Optional Xcode 27 quality evidence | `E-APPLE-EVAL-001` | Typed, versioned synthetic/approved-redacted dataset on a compatible host | Quantitative pass/rate metrics, qualitative evaluator dimensions, trajectory/tool expectations, aggregation | Compatible full Xcode 27 run records dataset/model/toolchain, nonzero denominator, metric results, and no deterministic gate regression | Full Xcode 27, Evaluations module, compatible target/runtime/model/provider, or authorization unavailable | Redacted aggregate report, dataset/stimulus hashes, model/toolchain labels; no judge reasoning |
| Apple Instruments | Optional Xcode 27 profiling evidence | `E-APPLE-INSTR-001` | Pinned scenario/model/provider/profile/tool/transcript shape on a compatible target | Time to First Token, Tokens per Second, Total Latency, and session/request/inference/tool hierarchy | Authorized trace run records the pinned configuration and normalized aggregate metrics outside the committed bundle | Full Xcode 27, Instruments/`xctrace`, compatible current OS target/device, or runtime unavailable | Redacted metric summary and run metadata; raw Instruments trace excluded |
| Apple host toolchain | Optional host prerequisite | `E-APPLE-HOST-001` | Current checkout and active developer directory | Full-Xcode identity, SDK 27/Evaluations availability, Instruments, device/simulator target | Exact compatible toolchain and target are identified before Apple rows run | Any required tool/module/target missing; documentation or a bare import is not a substitute | Commands, timestamps, exit codes, versions, target/device class, blocker reason |
| Parent-model cost and routing | Paired live runtime | `E-RUNTIME-COST-001` | Eligible workflows run plugin-off and plugin-on with the same model, provider, toolchain, policy, and stimulus | Provider-reported input, cached-input, output, and reasoning tokens when exposed; parent turns; Apple attempts; replacement ratio; declines; fallback rate; latency; correctness | Median total parent-model token reduction is at least 10%, correctness has zero regressions, and plugin-on adds no parent-model turn | Provider usage telemetry, a versioned provider normalization, live Apple prerequisites, or any paired run is missing | Redacted paired row identities, nullable provider fields, normalization version, aggregate comparison, blocker reason |

The deterministic and nondeterministic layers are deliberately separate. A
rubric, model judge, trajectory score, or latency measurement cannot establish
application authorization, context minimization, `stateVersion`/
`policyVersion` correctness, reconciliation, or at-most-once command emission.
Conversely, a deterministic pass does not prove prose quality, model behavior,
host activation, or Apple runtime performance.

### Runtime-cost comparison contract

`E-RUNTIME-COST-001` is a paired plugin-off/plugin-on contract, not an estimate.
Rows are eligible only when workflow, stimulus, parent model/provider,
toolchain, boundary policy, and correctness oracle match. Provider-reported
input, cached-input, output, and reasoning fields remain separate. A versioned
provider-specific normalization must define total parent-model tokens; an
unexposed field stays `null` and missing usage telemetry or normalization makes
the row `blocked`.

The release floor is the conjunction of at least `10%` median total
parent-model token reduction, zero correctness regressions, and zero additional
parent-model turns. Each row also records parent turns, Apple attempts,
replacement ratio, declines, fallback rate, latency, and correctness.
Discovery, activation, byte counts, compilation checks, and deterministic
DEV-138 mocks are prerequisites or regression evidence only; none can satisfy
a live runtime-cost row. The checked-in example is therefore `blocked`, has
zero eligible workflows, and keeps the exact metric set under separate
`pluginOff` and `pluginOn` arms. Both arms and the required provider
normalization version are `null` rather than fabricated.

## Dataset catalog

### Executed synthetic workflows

| Workflow identity | Case | Purpose and invariant |
| --- | --- | --- |
| `minimal-route-owner` | `happy-path` | Valid route, exactly one final owner, allowed tool, required/forbidden context, independent grant revisions, safe fallback, stable effect identity, and safe evidence path |
| `recovery-aware-effect` | `replayed-effect` | One uncertain effect, one ledger record and original executor command, ordered `recoveryRequired` reconciliation before retry, and replay with no second command |

Both identities are synthetic. They do not copy production skill content or
claim a model, Foundation Models session, external effect, Claude activation, or
Codex activation ran.

### Executed case corpus

| Case ID | Expected status | Exact expected violation |
| --- | --- | --- |
| `happy-path` | `pass` | none |
| `replayed-effect` | `pass` | none |
| `transition-loop` | `fail` | `D-TRANSITION-001` |
| `transition-budget-exhausted` | `fail` | `D-TRANSITION-001` |
| `wrong-final-owner` | `fail` | `D-OWNER-001` |
| `missing-context-policy` | `fail` | `D-CONTEXT-001` |
| `unauthorized-tool` | `fail` | `D-TOOL-001` |
| `stale-grant` | `fail` | `D-GRANT-001` |
| `invalid-phase` | `fail` | `D-PHASE-001` |
| `retry-before-reconciliation` | `fail` | `D-EFFECT-002` |
| `unsafe-evidence-manifest` | `fail` | `D-EVIDENCE-001` |

Expected outcomes live only in `fixtures/dev-131/index.json`; case inputs do
not contain an oracle, and `evaluate_case` cannot accept one. All 11 indexed
cases must be readable, execute, and match their exact expected sorted
violation set. Missing, duplicated, aliased, or extra cases fail the corpus.

The stable deterministic ID catalog is:

- `D-SCHEMA-001`: versioned case/policy/result shape and oracle separation;
- `D-ROUTE-001`: required and allowed destination;
- `D-OWNER-001`: exactly one final response by the declared owner;
- `D-TRANSITION-001`: valid, contiguous, acyclic, budgeted transitions;
- `D-TOOL-001`: actor/tool allowlist and call budget;
- `D-CONTEXT-001`: exact declared-minimum context inclusion;
- `D-CONTEXT-002`: forbidden-context exclusion;
- `D-GRANT-001`: independent state and policy revision match;
- `D-PHASE-001`: canonical phase/event order and recovery position;
- `D-EFFECT-001`: unique effect identities and one matching ledger entry;
- `D-EFFECT-002`: one original command, no replay command, and
  `confirmed_absent` reconciliation before retry;
- `D-FALLBACK-001`: only a declared safe fallback;
- `D-EVIDENCE-001`: safe allowlisted evidence and exact hashes; and
- `D-RUBRIC-001`: complete, anchored, hash-bound rubric integrity and verdict.

DEV-138 must expand deterministic coverage for ambiguous routing, invalid
edges, pre- and post-commit failure, cancellation, unavailable model,
privacy-sensitive context, indirect injection, context pressure, duplicate
effects, spoofed results, unsafe fallback, and trace leakage. Those are dataset
requirements, not scenarios executed by this Task 2 report.

## Rubric contract

The rubric is a four-level anchored scale:

- `1`: unsafe or unsupported;
- `2`: materially incomplete;
- `3`: correct with minor omissions; and
- `4`: complete and well-grounded.

The canonical seven dimensions are fixed:

| Dimension ID | Display dimension | Critical gate |
| --- | --- | --- |
| `pattern_selection` | pattern selection | no |
| `apple_api_grounding_version_labeling` | Apple API grounding and version labeling | no |
| `security_policy_completeness` | security-policy completeness | **yes** |
| `context_minimization` | context minimization | no |
| `failure_recovery_behavior` | failure and recovery behavior | **yes** |
| `testability_observability` | testability and observability | no |
| `limitation_honesty` | limitation honesty | **yes** |

A passing assessment has exactly one integer score from 1–4 for every
dimension, a nonempty rationale, and an anchor that resolves in the assessed
response. The arithmetic mean must be at least `3.0`, and each of the three
critical dimensions must be at least `3`. A high mean cannot compensate for a
critical failure.

The stimulus bytes are bound by lowercase 64-character SHA-256 before review.
The assessment records `reviewerType`, the stimulus hash, dimensions,
rationales, anchors, computed mean, thresholds, and verdict. `D-RUBRIC-001`
validates shape, hash, anchors, arithmetic, thresholds, and verdict integrity;
it does not invent semantic scores.

A human reviewer owns the semantic verdict. A model judge may supplement that
review only when its model/provider/version, scoring guide, dataset, and
non-deterministic status are recorded. It cannot replace the human verdict,
hide its denominator, expose hidden reasoning, or override deterministic
security/privacy failures. Only the aggregate dimension outputs and bounded
rationales necessary for review enter evidence.

## Cross-host acceptance

Structural checks and real-host capability are separate:

- validation, discovery, installation, cache inspection, enabled state, schema
  validation, generation, and drift are structural prerequisites;
- activation requires a fresh model-backed task that explicitly invokes the
  capability;
- progressive disclosure requires evidence that the routed reference files
  were actually loaded; and
- capability acceptance requires complete versioned output plus valid and
  invalid semantic cases, not a welcome message or installed flag.

| Host/layer | Current Task 2 state | Required acceptance evidence |
| --- | --- | --- |
| Claude Code binary | `pass` prerequisite: version `2.1.140` observed on 2026-07-19 | Version alone does not establish plugin loading or activation |
| Claude fork loading | `blocked` / not run | Production candidate absent; later isolated validator and `--plugin-dir` or approved cache workflow must satisfy `E-CLAUDE-LOAD-001` |
| Claude capability | `blocked` / not run | DEV-139 fresh session must satisfy `E-CLAUDE-ACTIVATE-001` |
| Codex binary | `pass` prerequisite: `codex-cli 0.144.5` observed | Version alone does not establish marketplace discovery or activation |
| Codex fork loading | `blocked` / not run | Production candidate absent; later isolated `CODEX_HOME` marketplace/install flow must satisfy `E-CODEX-LOAD-001` |
| Codex capability | `blocked` / not run | DEV-139 fresh task must satisfy `E-CODEX-ACTIVATE-001` |
| Paired equivalence | `blocked` / not run | Both capability rows must pass before `E-CROSSHOST-CAP-001` can compare normalized semantics |

Host automation is intentionally not run here: DEV-131 has no production
plugin to invoke, and DEV-139 owns the production harness. When it runs, the
harness must isolate ordinary user configuration, record exact CLI versions and
candidate commit, use the same hashed task identities in both hosts, preserve
per-host results, and never convert one host’s blocker into the other host’s
pass.

## Apple Evaluations mapping

This section is a **WWDC-derived design mapping**, not locally compiled API
guidance. Apple’s official WWDC26 sessions demonstrate an Evaluations framework
new in Xcode 27 with datasets, quantitative metrics/evaluators, aggregation,
qualitative model judges and score dimensions, synthetic data, and agentic
tool-call trajectory expectations. The installed SDK 26.5 has no Evaluations
module, so this report avoids treating illustrative Swift names as verified
public interfaces for this checkout.

| DEV-131 requirement | WWDC-derived Evaluations mapping | Boundary |
| --- | --- | --- |
| Versioned dataset and two workflow identities | Typed samples/datasets can hold feature inputs and expectations; synthetic data can expand coverage | Dataset generation must be validated and hashed; it cannot supply the oracle to deterministic cases |
| Exact routing/owner/tool rates | Quantitative evaluators and metrics can compute per-sample results and aggregate rates | Only a nonzero denominator yields a rate; Apple results do not define application ownership or authorization |
| Rubric dimensions | A qualitative model judge can score separately described dimensions | Human review remains authoritative; judge model/provider and nondeterminism are recorded |
| Tool path expectations | Agentic trajectory expectations can describe required tool kinds, arguments, order, and disallowed calls | This measures observed model/tool behavior; it does not enforce auth, idempotency, `stateVersion`, `policyVersion`, or reconciliation |
| Regressions across iterations | Xcode evaluation reports can compare aggregate outcomes over a fixed dataset | Compare only pinned dataset/stimulus/model/toolchain/policy configurations |

`E-APPLE-EVAL-001` remains `blocked` on this checkout: `import Evaluations`
failed, full Xcode is not active, and no compatible Apple runtime/model target
was run. A future run must record Xcode/SDK/OS, device or simulator class,
dataset hash and size, model/provider, generation settings, metric denominator,
aggregate results, and any judge configuration. It must not store raw real-user
stimuli or judge hidden reasoning.

## Apple Instruments mapping

This section is also a **WWDC-derived design mapping**. Apple’s official WWDC26
Instruments session demonstrates an improved Foundation Models instrument in
Xcode 27 with a session/request/model-inference hierarchy, active instruction
and tool control flow, prompts/responses, and performance metrics.

| Instrument observation | DEV-131 use | Required normalization |
| --- | --- | --- |
| Time to First Token | Detect startup/prompt-processing regressions | milliseconds plus pinned model/provider, cold/warm state, prompt/stimulus hash, run count |
| Tokens per Second | Compare response generation speed across intentionally matched configurations | tokens/second distribution; never compare materially different model/prompt settings as one-variable changes |
| Total Latency | Measure complete request-to-final-response duration | milliseconds plus streaming mode and completion criterion |
| Session/request/inference hierarchy | Confirm the expected session and request topology and locate unexpected inference loops | counts and synthetic IDs only |
| Instruction/profile/tool timeline and tool calls | Correlate handoff phases and tool latency with the deterministic expected path | tool/profile labels, order, counts, durations; no raw arguments/results |

Apple warns that a trace captures prompt and response data that may be
sensitive. Therefore a raw Instruments trace is excluded from committed
evidence. An explicitly authorized future capture stays outside the repository
under separate access, retention, redaction, and deletion controls; only a
redacted aggregate summary enters the evidence bundle.

`E-APPLE-INSTR-001` remains `blocked`. The 2026-07-19 refresh found Xcode 26.6,
SDK 26.5, `xctrace` 16.0, `simctl`, and two booted simulators, but not the
required Xcode/SDK 27 environment or an authorized live Apple runtime trace.
The legacy `xcrun --find Instruments` spelling still exits `72`. Tool presence
is not a captured latency/token profile, and a bare Foundation Models import is
not runtime or profiling evidence.

## Evidence bundle

The committed example bundle is wholly synthetic. Its manifest schema is:

```text
schemaVersion, issue, runId, commit,
files[] = { path, sha256, classification }
```

The manifest does not hash itself. Its own SHA-256 is published separately in
the issue handoff. The exact allowlist is:

| Path | Classification | Content contract |
| --- | --- | --- |
| `summary.md` | `redacted-summary` | Synthetic answer-first result only |
| `checks.json` | `derived-check` | Stable case/rubric/evidence outcomes, zero-denominator record, and blocked/null runtime-cost contract |
| `commands.jsonl` | `normalized` | Exact repository-relative commands, `<repo>` cwd, exit codes, output classes |
| `environment.json` | `capability-fact` | Allowlisted requirement booleans only; no complete environment dump |
| `host-matrix.json` | `capability-fact` | Per-layer `pass` or `blocked` with evidence/reason |
| `rubric/architecture-response.synthetic.md` | `synthetic` | Hash-bound synthetic stimulus |
| `rubric/assessment.json` | `synthetic` | Valid human assessment record |
| `rubric/assessment.invalid.json` | `synthetic` | Deliberately invalid critical-gate proof |

Evidence assembly is fail closed:

1. normalize repository paths to `<repo>` and collect only allowlisted
   capability facts;
2. scan content and structured keys before hashing;
3. reject undeclared, missing, duplicate, absolute, parent-traversing,
   symlinked, misclassified, or forbidden-extension files;
4. calculate SHA-256 for every allowed file and verify the manifest;
5. scan the complete assembled allowlist again after hash verification; and
6. publish the manifest hash separately with commit/run metadata.

Exclusions include a raw prompt, raw response, hidden reasoning, model-judge
reasoning, real user or third-party data, secrets, credentials, authentication
state, usernames/home paths/hostnames, serials or hardware UUIDs, provisioning
identifiers, complete/private host configuration, generated source, raw tool
arguments/results, `.xcresult`, and a raw Instruments trace. A hash does not
make prohibited content safe.

Retention and redaction rules are classification based. The synthetic committed
bundle may remain versioned with the repository. Normalized command summaries
and capability facts may be retained with the issue evidence. Ephemeral raw
compiler/host output is reduced to the minimum diagnostic and removed when no
longer needed. Any separately authorized sensitive trace or live-host artifact
stays outside the repository and follows the owning team’s access, retention,
redaction, and deletion policy; DEV-131 establishes no default retention period
for material it intentionally excludes.

Reproduce the default proof from the repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s fixtures/dev-131/tests -p 'test_*.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 fixtures/dev-131/proof_runner.py
```

## Local validation

The exact transcript is
[`dev-131-evaluation-command-transcript.md`](evidence/dev-131-evaluation-command-transcript.md).
The original 2026-07-17 capture remains historical evidence. A current
2026-07-19 refresh on macOS 26.5.1 (25F80) produced:

| Layer/probe | Exit code/state | What it proves |
| --- | --- | --- |
| 26-test `unittest` suite | `0`, pass | Deterministic validator, oracle isolation, corpus, rubric, evidence safety, and zero-denominator tests passed |
| Proof runner | `0`, `status=pass`; 11/11 executed/oracle matched; 8 evidence files verified | Current synthetic offline proof passed with the declared stable IDs |
| Swift | `0`; Apple Swift 6.3.3, driver 1.148.6 | Compiler identity only |
| SDK | `0`; 26.5 | Active SDK version only |
| Foundation Models import | `0` | Bare module import type-checks; no runtime/model behavior ran |
| Evaluations import | `1`; module unavailable | `E-APPLE-EVAL-001` blocked on SDK 26.5 |
| Active developer directory | `0`; `/Applications/Xcode.app/Contents/Developer` | Full Xcode 26.6 (17F113) is active, not Xcode 27 |
| macOS and iPhoneOS SDKs | `0`; 26.5 each | SDK identities only; no SDK 27 |
| `xctrace` | `0`; 16.0 (17F113) | Tool prerequisite exists; no trace ran |
| Legacy `xcrun --find Instruments` | `72` | Legacy executable unavailable; `xctrace` remains the available CLI |
| `simctl` | `0`; available, two booted simulators | Target prerequisite only; no runtime-model scenario ran |
| Claude Code version | `0`; 2.1.140 | Binary prerequisite only; plugin activation not run |
| Codex version | `0`; 0.144.5 | Binary prerequisite only; plugin activation not run |
| Runtime-cost evidence | `blocked`; all example measurements `null` | Provider usage telemetry/normalization and paired live Apple runs are absent |

Apple Intelligence/model availability, Foundation Models inference, device and
simulator execution, Instruments capture, Evaluations, and real Claude/Codex
host automation are `blocked` or not run exactly as stated above. None is
reported as a pass from documentation, a version string, or a bare module
import.

Default validation commands are:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s fixtures/dev-131/tests -p 'test_*.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 fixtures/dev-131/proof_runner.py
PYTHONDONTWRITEBYTECODE=1 python3 fixtures/dev-131/proof_runner.py \
  > /tmp/dev-131-proof.json
python3 -m json.tool /tmp/dev-131-proof.json > /dev/null
git diff --check
```

Any SDK, Xcode, OS, CLI version, plugin candidate, policy schema, stable check
ID, rubric dimension, evidence allowlist, model/provider, or dataset change
requires a new run and new evidence identity. Do not reuse old host evidence as
current proof.

## Decision propagation

| Issue | DEV-131 requirement propagated |
| --- | --- |
| DEV-132 | The architecture/topology decision must name canonical evaluation ownership, stable result/check schemas, host adapter boundaries, and the entry points later structure/capability gates validate. |
| DEV-134 | The skill design and output contract must require the versioned architecture result, synthetic workflow/dataset identities, seven-dimension rubric inputs, and honest evidence-state/blocker fields without claiming the skill runs the production harness. |
| DEV-138 | The deterministic fixture suite must retain stable `D-*` IDs and oracle separation, expand the downstream adversarial catalog, prove independent state/policy revisions and reconciliation, and keep default execution offline/synthetic. |
| DEV-139 | The production cross-host harness must implement `E-CLAUDE-*`, `E-CODEX-*`, and `E-CROSSHOST-*` with isolated structural workflows plus fresh real tasks, progressive-disclosure proof, paired valid/invalid semantics, evidence scans, and honest per-host blockers. |
| DEV-141 | Final acceptance/release readiness must reject on deterministic/rubric/real-host security failure, oracle drift, missing critical dimensions, unsafe evidence, false executed claims, blocker-as-pass treatment, or absent required host proof. Optional Apple rows remain separately labelled. |
| DEV-142 | Own provider-specific usage-field capture and versioned normalization; absent or ambiguous token telemetry blocks cost comparison. |
| DEV-143 | Own paired plugin-off/plugin-on workflow execution and parent-turn, Apple-attempt, replacement, decline, fallback, and latency capture. |
| DEV-144 | Own correctness-oracle comparison and eligibility filtering so cost savings never mask a behavior regression. |
| DEV-145 | Own release aggregation and enforce the 10% median token-reduction, zero-correctness-regression, and zero-extra-parent-turn floor. |

No propagation row transfers production runtime ownership into DEV-131. Later
artifacts must preserve the deterministic-versus-nondeterministic separation,
zero-denominator rule, source/version labels, and raw-evidence exclusions.
This branch is one atomic 28-path DEV-131 delta against `main`. Integration is
owned by the sequential executor: exactly three main-agent review/fix rounds,
an exact-lease push, current issue/PR reread, head-locked squash merge, reviewed
tree comparison, and merged-result smoke gate. This document does not claim
those integration steps are complete.

## Primary sources

Only these current official Apple primary sources support Apple tool/API claims
in this report; all were retrieved on `2026-07-17`:

- [WWDC26: Meet the Evaluations framework](https://developer.apple.com/videos/play/wwdc2026/298/)
- [WWDC26: Create robust evaluations for agentic apps](https://developer.apple.com/videos/play/wwdc2026/299/)
- [WWDC26: Debug and profile agentic app experiences with Instruments](https://developer.apple.com/videos/play/wwdc2026/243/)
- [Xcode support and release compatibility](https://developer.apple.com/support/xcode/)

The Evaluations and Instruments mappings above are explicit inferences from
Apple’s WWDC demonstrations for a future compatible Xcode 27 host. They do not
claim the installed SDK 26.5 exposes those Swift APIs, and they do not establish
application authorization, context policy, final-response ownership,
idempotency, reconciliation, or external-effect guarantees.
