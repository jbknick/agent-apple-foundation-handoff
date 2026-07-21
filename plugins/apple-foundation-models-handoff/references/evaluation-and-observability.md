# Evaluation and Observability Contract

## Scope and authority

This reference solely owns stable deterministic/evidence IDs, corpus/oracle
separation, evidence states, the seven-dimension rubric, safe evidence, host
rows, zero-denominator handling, optional Apple Evaluations/Instruments
boundaries, and blocker policy. It does not authorize context, tools, effects,
providers, or fallback.

Architecture invariants are defined in
[architecture and state](architecture-and-state.md), topology in
[orchestration patterns](orchestration-patterns.md), exact Apple availability
in [Apple API availability](apple-api-availability.md), and adversarial policy
in [security, context, and recovery](security-context-and-recovery.md).

## Evidence layers and states

| Layer | Purpose | Default |
| --- | --- | --- |
| Deterministic contract | Exact schemas, transitions, routes, owners, grants, effects, fallback, and evidence safety | Mandatory, offline |
| Structural host | Installed package files, hashes, links, and direct routes | Mandatory when the host exists |
| Semantic rubric | Human-reviewed quality against a fixed corpus and seven dimensions | Mandatory for selected deliverables, separate from arithmetic validation |
| Live/model/tool host | Probabilistic activation, provider behavior, and model results | Optional and prerequisite-gated |
| Apple toolchain | Evaluations and Instruments evidence | Optional Xcode 27 evidence, not authorization and not default CI |

Every row uses exactly one state: `pass`, `fail`, `blocked`, or
`not_applicable`. A blocker names the unavailable prerequisite and does not
become a pass. Owner-deferred work remains blocked/deferred in the relevant
ledger.

## Stable ID catalog

| ID | Contract |
| --- | --- |
| `D-SCHEMA-001` | Versioned case/policy/result shape and oracle separation |
| `D-ROUTE-001` | Required and allowed destination |
| `D-OWNER-001` | Exactly one final response by the declared owner |
| `D-TRANSITION-001` | Valid, contiguous, acyclic, budgeted transitions |
| `D-TOOL-001` | Actor/tool allowlist and call budget |
| `D-CONTEXT-001` | Declared required-context inclusion |
| `D-CONTEXT-002` | Forbidden-context exclusion |
| `D-GRANT-001` | Bound provider grant and independent state/policy revision match |
| `D-PHASE-001` | Canonical phase/event order and recovery position |
| `D-EFFECT-001` | Unique effect identities and one matching ledger entry |
| `D-EFFECT-002` | One original command, no replay command, reconciliation before retry |
| `D-FALLBACK-001` | Only a declared safe fallback |
| `D-EVIDENCE-001` | Safe allowlisted evidence and exact hashes |
| `D-RUBRIC-001` | Complete, anchored, hash-bound rubric integrity and verdict |

D-GRANT-001 verifies the complete provider-grant binding owned by
[security, context, and recovery](security-context-and-recovery.md) without
redefining that owner's field list. Verification rejects any mismatch and
checks the independently advancing state and policy versions against the
approved policy and result.

Host/evidence identities are:

| ID | Boundary |
| --- | --- |
| `E-CLAUDE-LOAD-001` | Claude package load; owner-deferred and not invoked here |
| `E-CODEX-LOAD-001` | Codex installed source/cache byte identity; structural only |
| `E-CLAUDE-ACTIVATE-001` | Claude production workflow activation; owner-deferred |
| `E-CODEX-ACTIVATE-001` | Codex production workflow activation; requires integrated skills |
| `E-CROSSHOST-STRUCT-001` | Cross-host structural equivalence |
| `E-CROSSHOST-CAP-001` | Cross-host capability/semantic equivalence |
| `E-APPLE-HOST-001` | Normalized Apple SDK/interface/compile identity |
| `E-APPLE-EVAL-001` | Apple Evaluations run on a compatible toolchain |
| `E-APPLE-INSTR-001` | Instruments run with compatible target and safe evidence |

IDs never encode a result. The record beside an ID carries status, reason,
candidate commit/tree, version, counts, and hashes.

## Corpus and oracle separation

The corpus contains inputs and expected policy facts. The oracle independently
maps those facts to deterministic expected results. The implementation under
test cannot generate or rewrite its own expectations.

Each case has a stable ID, operation/domain, approved input identity, expected
result class, expected route/owner/state/effect facts, evidence sensitivity,
and applicability. Invalid cases are first-class: wrong versions, missing
grant fields, stale confirmation, duplicate/replayed events, unsafe fallback,
unknown API claims, and malformed rubric data must fail closed.

## Deterministic acceptance

- Validate closed schema and required fields before semantics.
- Check phase before versions, edge, budgets, grant, context, and effects.
- Require exact source/destination/final owner for each pattern.
- Reject overbroad context, C3 transfer, stale versions, and mismatched
  provenance/correlation.
- Assert at most one command for an accepted effect identity and none for
  replay/late events.
- Require reconciliation before retry and no trust expansion during fallback.
- Validate arithmetic and evidence shape mechanically; keep semantic judgment
  separate.
- Run the same deterministic corpus twice and require byte-identical normalized
  output.

## Canonical rubric

Scores are integers from 1 through 4. The seven exact dimensions are:

| Dimension | A score of 3 or better requires |
| --- | --- |
| Pattern selection | Correct topology/history/control/final-owner distinction and alternatives |
| Apple API grounding and version labeling | Exact source-supported surface, stable/beta separation, and honest blockers |
| Security-policy completeness | Context classes, provenance, grants, confirmation, tool/effect boundary, and provider limits |
| Context minimization | Necessary fields only, destination/purpose binding, and explicit exclusions |
| Failure and recovery behavior | Phase-correct rollback/recovery, reconciliation, replay handling, and fallback |
| Testability and observability | Deterministic IDs/oracles, safe host rows, reproducibility, and counts/hashes |
| Limitation honesty | No invented API, pass, guarantee, provider property, or hidden prerequisite |

The arithmetic mean is at least 3.0, and Security-policy completeness, Failure
and recovery behavior, and Limitation honesty each score at least 3. A mean
above threshold cannot compensate for a critical-dimension score below 3.
Human semantic scoring remains distinct from deterministic shape, integer,
range, threshold, and mean validation.

## Safe evidence

Committed evidence may contain only normalized metadata: stable IDs, candidate
commit/tree hashes, source/interface/prompt/result hashes, versions, statuses,
normalized reasons, expected/observed basenames, result classes, counts,
durations, and aggregate rubric scores. The approved content exception is a
scanned synthetic/redacted corpus and rubric rationale that contains no person,
credential, prompt injection payload from a real source, private path, or live
provider/tool body.

Live prompts, responses, reasoning, tool arguments/results, credentials,
provider bodies, private configuration, host identity, and sensitive trace or
result bundles remain outside committed evidence. Scan before commit and hash
the retained normalized record.

## Reference-disclosure proof

Reference-library validation has separate claims:

1. offline topology/ownership/link/source/label tests prove the five-file
   package contract;
2. installed payload proof establishes regular non-symlink files and
   byte-identical source/cache content;
3. an explicitly directed reference-selection probe is prerequisite evidence
   only; and
4. workflow-triggered progressive disclosure requires integrated production
   skills, fresh sessions, observed exact reference reads, minimal conditional
   loads, and fictional-API noninvention.

Structural or explicitly directed evidence cannot be relabelled as production
workflow activation.

## Host matrix

| Row | Prerequisite | Result rule |
| --- | --- | --- |
| Offline repository/reference tests | Python, Swift compiler for compiled blocks | Must pass on the candidate tree |
| Installed Apple host | SDK 26.5 identity and pinned interface | Pass only on exact version/hash and successful compilation |
| Codex package load | Approved CLI version and isolated install/cache | Structural pass only |
| Codex production activation | Integrated production skills and approved host runner | Blocked until integrated; every semantic mismatch fails |
| Claude load/activation | Owner-approved invocation | Owner-deferred; do not invoke in this work |
| Apple Evaluations | Compatible full Xcode 27/module/target | Optional or blocked, never default pass |
| Instruments | Full Xcode 27, compatible target/device, collection approval | Optional or blocked; sensitive evidence rules apply |
| DEV-142 runtime-cost gate | Paired normalized live telemetry, current policy, and live Apple prerequisites | At least 10% median total parent-model token reduction, zero correctness regressions, and zero additional parent-model turns; otherwise fail or block |

The DEV-142 repository-only proof semantically validates three schemas and
their closed custom vocabulary, a hash-bound synthetic corpus of 24 eligible
cases, all 96 arms and 48 required host/case pair identities, deterministic
routing boundaries, quality scoring, and the two versioned provider-
normalization formulas. Its sorted metadata-only artifact can pass only for
that offline contract. It records Apple and host invocation as
`not_applicable`; parent-token reduction remains
`blocked/provider_usage_not_executed` because no paired live provider usage
was executed. It contains no model output, raw diagnostics, paths, traces, or
runtime capability metadata.

## Apple Evaluations

Official Apple documentation describes datasets, generations, metrics,
evaluators, aggregation, and model-as-judge patterns for measuring intelligent
features. This is optional evidence on Xcode 27, not authorization, not a
replacement for deterministic invariants, and not default CI. A live/model
evaluation records model/provider, OS/SDK, dataset revision, run count, and
non-determinism.

## Instruments

Official Foundation Models Instruments guidance exposes request/session/profile
and tool control flow, prompts/model output, token use, cached tokens, time to
first token, response duration, and latency. Host proof requires full Xcode 27
and a compatible current target or device. Collected content can be sensitive;
only the safe normalized allowlist may be committed.

Instruments can explain performance and control flow. It cannot establish an
authorization grant, effect truth, rubric score, or universal cache guarantee.

## Zero-denominator rules

When a metric denominator is zero, do not emit zero, one, NaN, infinity, or a
fabricated percentage. Emit:

```text
value: null
status: not_applicable
reason: zero_denominator
```

Exclude that metric from aggregate arithmetic and preserve the numerator and
denominator counts in normalized evidence.

## Blockers

A blocked row includes stable ID, status `blocked`, normalized reason,
prerequisite, observed version/absence, command or probe identity, and candidate
commit/tree. Missing SDK 27, full Xcode, module, macro plugin, model/provider,
entitlement, device, network, approved binary, integrated skills, or owner
permission are narrow blockers. They do not invalidate independent offline
passes and never become inferred success.

## Related references

- [Architecture and state](architecture-and-state.md)
- [Orchestration patterns](orchestration-patterns.md)
- [Apple API availability](apple-api-availability.md)
- [Security, context, and recovery](security-context-and-recovery.md)

## Source ledger

All official sources were retrieved on 2026-07-17.

| Evidence family | Official source |
| --- | --- |
| Apple Evaluations | [Evaluations](https://developer.apple.com/documentation/evaluations), [WWDC26 session 298](https://developer.apple.com/videos/play/wwdc2026/298/), [WWDC26 session 299](https://developer.apple.com/videos/play/wwdc2026/299/) |
| Instruments, tokens, cache, and sensitive collection | [Runtime performance](https://developer.apple.com/documentation/foundationmodels/analyzing-the-runtime-performance-of-your-foundation-models-app), [WWDC26 session 243](https://developer.apple.com/videos/play/wwdc2026/243/) |
| Context limits | [Managing the context window](https://developer.apple.com/documentation/foundationmodels/managing-the-context-window) |

## Limitations

Deterministic passes do not prove probabilistic model quality or live host
activation. Rubric scores remain human judgment. Optional Apple tools depend on
beta toolchains and compatible targets. Cross-host equivalence, provider
behavior, cache performance, and sensitive trace review require separately
authorized evidence.
