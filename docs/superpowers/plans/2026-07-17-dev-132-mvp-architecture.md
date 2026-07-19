# DEV-132 Apple Foundation Models Handoff MVP Architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:subagent-driven-development` to execute this plan task by task.

**Goal:** Publish a durable, internally consistent MVP architecture decision
record and machine-checkable proof for seven representative design scenarios,
without creating any production plugin artifact.

**Architecture:** The canonical design spec fixes the product and repository
contract. A concise decision record will restate every binding choice with its
source, rationale, and downstream impact. A normalized JSON evidence file will
retain the original four scenarios and add three amendment cases against one
small design-proof schema so
deterministic checks can validate activation, pattern, ownership, safety,
version labels, and expected verification IDs. Existing DEV-128, DEV-130, and
DEV-131 fixtures remain the executable regression authorities.

**Tech Stack:** Markdown, JSON, Python 3 standard library, Swift 6.3.3,
Xcode 26.6, macOS SDK 26.5, Git, and Linear. These toolchain observations are
compile/regression evidence only, not live runtime proof.

## Global constraints

- Work from the repository root, recorded as `<repo>`, on
  `codex/dev-132-mvp-architecture`.
- Integrate the unique four-path DEV-132 delta atomically against current
  `main`. Historical stack bases, commit IDs, and host versions are provenance,
  not acceptance bindings.
- Do not push, merge, tag, publish, or release unless the active issue separately
  authorizes that action. Opening the issue-scoped PR is permitted only after
  final verification and review.
- Do not create production manifests, marketplaces, skills, references,
  schemas, generators, tests, Swift fixtures, routers, hooks, bridges, agents,
  commands, MCP servers, apps, dependencies, or runtime packages in DEV-132.
- Do not edit any generated artifact. The proposed generated paths in the
  design are downstream contracts, not DEV-132 deliverables.
- Use Apple-owned material and the installed SDK for Apple API truth. Structural
  reference repositories never establish Apple API behavior.
- Never turn missing Xcode, SDK, device, simulator, Instruments, Evaluations,
  host automation, authentication, or model access into a pass.
- For every Claude/Codex host row, select an explicit executable or capture the
  first executable from the controlled `PATH` before any operation. Invoke only
  that captured executable, recheck resolution before completion, and invalidate
  the row on drift. Commit only normalized `<host-path>` identity and exact
  version; never commit a literal executable path or raw `PATH`.
- Each downstream issue owns its current host/model matrix. Version output
  proves a binary prerequisite only and no historical version may substitute.
- Default validation remains offline and requires no live model generation,
  PCC, custom provider, credential, network service, entitlement, or hardware.
- Apply changes with `apply_patch`. Keep each commit single-purpose.

## Exact allowed path set

The final DEV-132 diff may contain exactly these four paths:

```text
docs/superpowers/specs/2026-07-17-dev-132-mvp-architecture-design.md
docs/superpowers/plans/2026-07-17-dev-132-mvp-architecture.md
docs/architecture/apple-foundation-models-handoff-mvp-decision-record.md
docs/research/evidence/dev-132-architecture-scenarios.json
```

Ignored `.superpowers/sdd/**` worker briefs may exist locally but must not enter
the commit or PR. Any correction must modify one of the four allowed files.

## Binding contract to preserve

- Identity: `apple-foundation-models-handoff`; display name
  `Apple Foundation Models Handoff`.
- Exactly five positive workflow skills: design, implement, review, debug, and
  validate, using the exact directory names in the design spec. Positive
  prompts bypass one bounded non-positive router; its only outputs are
  `no_activation` and `clarification_required`, with no workflow/reference/
  architectureResult/tool/effect/Apple/command/agent/hook behavior.
- One physical provider-neutral skills tree and one shared references tree.
- Canonical `CLAUDE.md`; generated `AGENTS.md` adapter; canonical Claude shared
  identity; authored Codex interface/marketplace inputs; generated Codex
  outputs; Python 3 standard-library deterministic sync/check.
- Selected root source `./` only after cached-install integrity and fresh real
  activation/reference proof on both pinned hosts. Deterministic fallback is
  `./plugins/apple-foundation-models-handoff` with no external symlink.
- Repository-only fixtures, tests, research, and private repository state remain
  outside both plugin capabilities and the effective cached payload.
- Baton-pass and isolated consultation are distinct first-class patterns;
  routing, transcript transfer, Apple Handoff, App Intents, runtime Skills,
  Agent Skills, and coding-session handoff are not aliases.
- SDK 26.5 compiled claims are separate from the broader SDK 26.x family
  boundary and from OS/Xcode 27 beta guidance.
- Deterministic reducer, independent `stateVersion` and `policyVersion`, phases
  `stable|transitioning|recoveryRequired|terminated`, one stable active
  profile/provider, finite budgets, C0-C3 classification, bound grant,
  confirmation, provenance, effect ledger, fail-closed transfer, reconciliation
  before retry, and no exactly-once/rollback claim. Ordinary budget/no-safe-path
  termination applies only from `stable`; unresolved recovery preserves its
  phase, authority, pending/checkpoint state, counts, ledger, and repair facts
  and returns repair-blocked/unavailable until explicit reconciliation.
- Evidence layers remain separate: deterministic `D-*`, exact seven-dimension
  human rubric, real-host `E-*`, and optional Apple evidence. Statuses are
  `pass|fail|blocked|not_applicable`; zero denominator is not applicable.
  Runtime/live-host logs, traces, and derived capability telemetry are
  metadata-only. The DEV-131 allowlist may contain a hash-bound synthetic or
  approved-redacted rubric stimulus, assessments with bounded rationales, and
  a redacted summary after all path/content/key/classification/hash scanners.
- A separate `PostToolUse` cost route uses exact action
  `condense_diagnostic_output` for selected test/build/typecheck/lint result
  envelopes. DEV-142 owns versioned exact allowlists, command classes, savings
  and payload bounds, paired cost normalization, and the 10%/0/0 gate; DEV-143
  owns the sole local Swift Apple bridge; DEV-144 and DEV-145 own Codex and
  Claude adapters. Unknown policy fails closed. Decline/unavailable preserves
  the original; failure adds only a normalized error; no path reruns the tool.
- Apple is the sole MVP local provider. Generic provider interfaces, GLM, Kimi,
  local OpenAI-compatible servers, external providers, PCC, credentials, paid,
  and network surfaces are deferred.

## Task 1: Publish the durable decision record

**Files:**

- Create:
  `docs/architecture/apple-foundation-models-handoff-mvp-decision-record.md`
- Read:
  `docs/superpowers/specs/2026-07-17-dev-132-mvp-architecture-design.md`
- Read:
  `docs/research/dev-128-foundation-models-api-map.md`
- Read:
  `docs/research/dev-129-production-pattern-comparison.md`
- Read:
  `docs/research/dev-130-handoff-threat-model.md`
- Read:
  `docs/research/dev-131-evaluation-strategy.md`

### Step 1: Assign a fresh SDD implementer

Give the implementer Task 1 only. Require it to read the five source documents
and the DEV-132 design spec before editing. Tell it that the output is a
decision record, not a second speculative design, and that it may change only
the decision-record path.

### Step 2: Prove the artifact and semantic contract are initially RED

Run:

```bash
set +e
record=docs/architecture/apple-foundation-models-handoff-mvp-decision-record.md
test -s "$record"
red_rc=$?
set -e
test "$red_rc" -ne 0
```

Expected: the file check exits nonzero before the record exists.

Then save the following semantic gate in the worker notes and run it. It must
also fail before implementation:

```bash
set +e
record=docs/architecture/apple-foundation-models-handoff-mvp-decision-record.md
(
  for section in \
    'Decision status and scope' \
    'Users and workflows' \
    'Skill and reference architecture' \
    'Canonical and generated ownership' \
    'Selected package placement and fallback' \
    'Handoff patterns and Apple API boundary' \
    'State, trust, effects, and recovery' \
    'Output and evidence contracts' \
    'Deferred work' \
    'Decision propagation'; do
    rg -q -F "## $section" "$record" || exit 1
  done
)
red_semantic_rc=$?
set -e
test "$red_semantic_rc" -ne 0
```

### Step 3: Create the decision record

Use `apply_patch` to create the file. It must:

1. identify the current DEV-127 through DEV-131 artifacts as source authority
   and label earlier reviewed heads as historical provenance;
2. state the plugin identity, users, five positive workflows, bounded
   non-positive router, exact skill names, and explicit DEV-132 exclusions;
3. state one physical skill/reference corpus and the five concern-owned
   references;
4. distinguish canonical inputs, generated outputs, and edit rules;
5. include the complete root candidate tree and complete conventional fallback
   tree, the precise fallback triggers, marketplace source for each, and the
   exclusion of repository-only material from capabilities and effective cached
   payload content;
6. state that root placement is conditional evidence, not a present success,
   and require captured, normalized, versioned, resolution-stable host identity;
7. define baton-pass and isolated consultation ownership/context differences
   and name the concepts that remain separate;
8. separate compiled SDK 26.5, interface-only SDK 26.5, beta, pseudocode, and
   blocked claims;
9. summarize the common output schema and workflow-specific additions;
10. preserve state, trust, context, grant, confirmation, effect, replay,
    recovery, and fallback invariants, including stable-only termination and
    `recoveryRequired` until explicit reconciliation establishes external truth;
11. preserve all four evaluation layers, exact rubric dimensions/thresholds,
    status meanings, metadata-only runtime/live-host telemetry, the allowlisted
    synthetic/approved-redacted rubric and summary exception, and all raw/live
    evidence exclusions;
12. record the Apple-first `PostToolUse` cost chain, fallback/no-rerun behavior,
    DEV-142 through DEV-145 ownership, 10%/0/0 floor, rejected alternatives,
    and deferred provider/runtime surfaces; and
13. provide a decision-propagation table for DEV-133 through DEV-145 with
    source, rationale, inherited decision, and impact.

Do not copy long research prose. Prefer compact tables with explicit ownership
and downstream impact.

### Step 4: Run GREEN semantic and consistency gates

Run the section gate from Step 2 and:

```bash
set -e
record=docs/architecture/apple-foundation-models-handoff-mvp-decision-record.md
test -s "$record"
placeholder_re='T(BD)|TO(DO)|FIX(ME)|fill in detai(ls)|implement lat(er)'
! rg -n -e "$placeholder_re" "$record"
for token in \
  'apple-foundation-models-handoff' \
  'design-apple-foundation-models-handoff' \
  'implement-apple-foundation-models-handoff' \
  'review-apple-foundation-models-handoff' \
  'debug-apple-foundation-models-handoff' \
  'validate-apple-foundation-models-handoff' \
  'plugins/apple-foundation-models-handoff' \
  'stateVersion' 'policyVersion' 'recoveryRequired' \
  'no safe reconciliation' 'metadata-only' 'rubric stimulus' \
  '<host-path>' 'no_activation' 'clarification_required' \
  'condense_diagnostic_output' 'providerNormalizationVersion' \
  'D-OWNER-001' 'not_applicable' 'DEV-141' 'DEV-145'; do
  rg -q -F "$token" "$record"
done
git diff --check -- "$record"
```

Expected: every assertion exits `0`; the placeholder search prints nothing.

### Step 5: Review Task 1 before commit

Assign a fresh spec-compliance reviewer. It must compare the record against all
five blocker reports and the design spec, list omissions/contradictions with
line evidence, and make no edits. The implementer fixes only confirmed issues;
rerun the semantic gate after each fix. Then assign a fresh quality reviewer to
check readability, duplicated authority, ambiguous ownership, and unsupported
Apple claims. Resolve verified findings before committing.

### Step 6: Commit Task 1 atomically

```bash
git add docs/architecture/apple-foundation-models-handoff-mvp-decision-record.md
git diff --cached --check
git diff --cached --name-only
git commit -m 'docs(DEV-132): publish MVP decision record'
```

Expected staged path: the decision record only.

## Task 2: Amend the machine-checkable seven-scenario architecture proof

**Files:**

- Create:
  `docs/research/evidence/dev-132-architecture-scenarios.json`
- Read:
  `docs/superpowers/specs/2026-07-17-dev-132-mvp-architecture-design.md`
- Read:
  `docs/architecture/apple-foundation-models-handoff-mvp-decision-record.md`
- Read:
  `fixtures/dev-131/index.json`
- Read:
  `fixtures/dev-131/proof_runner.py`

### Step 1: Assign a fresh SDD implementer

Give the implementer Task 2 only. It may change only the scenario JSON. Require
normalized synthetic data, no raw prompt/response/reasoning/tool content, no
real user data, no credentials, and no claim that a design-level case ran a
real host, model, provider, or Apple runtime. Synthetic scenario evidence must
still satisfy the DEV-131 path, content, structured-key, classification, and
hash boundaries; this file does not authorize raw/live evidence.

### Step 2: Establish the amended JSON contract RED

Run before editing the existing four-scenario file:

```bash
set +e
python3 - <<'PY'
import json
from pathlib import Path

path = Path('docs/research/evidence/dev-132-architecture-scenarios.json')
data = json.loads(path.read_text())
assert [s['id'] for s in data['scenarios']] == [
    f'DEV132-SCENARIO-{n:03d}' for n in range(1, 8)
]
text = path.read_text()
for required in (
    'no_activation', 'clarification_required',
    'condense_diagnostic_output',
):
    assert required in text
PY
red_rc=$?
set -e
test "$red_rc" -ne 0
```

Expected: nonzero because the stale evidence has only scenarios 001-004 and no
July 18 routing/cost contract.

### Step 3: Create the normalized JSON evidence

Use `apply_patch`. Top-level fields must be:

```text
schemaVersion
evidenceKind = design_scenario
sourceIssue = DEV-132
designArtifact
designArtifactSha256
workflowRoutingContract
costRoutingContract
status
limitations[]
scenarios[]
```

Each scenario must have:

```text
id
title
workflowSkill
inputClass
expectedPattern
sourceProfile
destinationProfile
finalResponseOwner
contextPolicy = { included[], excluded[], classificationOutcome }
stateOutcome = { phase, commandCount, effectCount, reconciliationRequired }
safetyOutcomes[] = { id, expected }
verification = { requiredIds[], expectedResult }
apiClaims[] = { surface, versionLabel, localStatus }
limitations[]
```

Retain and amend exactly these cases:

- `DEV132-SCENARIO-001`: new baton-pass design; design skill; source research,
  destination/final owner review; valid selected context; no invented Apple
  baton API; expected pass.
- `DEV132-SCENARIO-002`: flawed reducer review; review skill; wrong/ambiguous
  final owner, unlimited transitions, and whole-transcript copy; expected fail
  with exact IDs `D-OWNER-001`, `D-TRANSITION-001`, `D-CONTEXT-001`, and
  `D-CONTEXT-002`.
- `DEV132-SCENARIO-003`: isolated consultation; design skill; parent retains
  final ownership, child transcript is isolated, context minimized; expected
  pass.
- `DEV132-SCENARIO-004`: debug a C3 custom-provider transfer plus a separate
  uncertain allowed effect; debug skill; attempted pattern is `baton_pass`; C3
  envelope emits zero commands; uncertain effect retains exactly one
  command/effect and enters `recoveryRequired`; replay emits no second command;
  reconciliation required. A late/replayed event changes no authority, phase,
  pending/checkpoint state, counts, or ledger. If no safe reconciliation path is
  currently available, the result is repair-blocked/unavailable while the
  phase, ledger, and repair facts remain unchanged.
- `DEV132-SCENARIO-005`: an out-of-domain request returns exact
  `no_activation` with every non-positive-router side effect prohibited.
- `DEV132-SCENARIO-006`: bounded domain/approved-contract ambiguity returns
  exact `clarification_required`, asks one bounded question, and reclassifies
  the answer afresh without hidden state.
- `DEV132-SCENARIO-007`: a selected diagnostic result enters the separate
  Apple-first `PostToolUse` cost route; exact DEV-142 policy gates precede one
  bridge attempt; decline/unavailable preserves the original, failure returns
  a normalized error plus the original, and every path has zero original-tool
  reruns and no first-parent-turn savings claim.

Keep the two branches in Scenario 4 explicit so the blocked C3 envelope is not
misrepresented as having been dispatched.

### Step 4: Run the semantic oracle

Run exactly:

```bash
python3 - <<'PY'
import json
import hashlib
from pathlib import Path

p = Path('docs/research/evidence/dev-132-architecture-scenarios.json')
d = json.loads(p.read_text())
assert d['schemaVersion'] == '1.0'
assert d['evidenceKind'] == 'design_scenario'
assert d['sourceIssue'] == 'DEV-132'
design_path = Path(
    'docs/superpowers/specs/2026-07-17-dev-132-mvp-architecture-design.md'
)
assert d['designArtifact'] == design_path.as_posix()
assert d['designArtifactSha256'] == hashlib.sha256(
    design_path.read_bytes()
).hexdigest()
workflow_route = d['workflowRoutingContract']
assert workflow_route['positiveWorkflowCount'] == 5
assert workflow_route['positivePromptBehavior'] == (
    'bypass_non_positive_router_and_activate_exactly_one_workflow'
)
assert workflow_route['nonPositiveRouterCount'] == 1
assert workflow_route['outcomes'] == [
    'no_activation', 'clarification_required'
]
cost_route = d['costRoutingContract']
assert cost_route['trigger'] == 'host_PostToolUse'
assert cost_route['action'] == 'condense_diagnostic_output'
assert cost_route['eligibleResultClasses'] == [
    'test', 'build', 'typecheck', 'lint'
]
assert cost_route['policyOwner'] == 'DEV-142'
assert cost_route['provider'] == 'local_Apple_Foundation_Models_only'
assert cost_route['unknownPolicyBehavior'] == (
    'fail_closed_preserve_original'
)
assert cost_route['acceptance'] == {
    'minimumMedianTotalParentModelTokenReduction': 0.1,
    'maximumCorrectnessRegressions': 0,
    'maximumExtraParentModelTurns': 0,
    'evidenceShape': (
        'paired_null_capable_pluginOff_pluginOn_with_'
        'providerNormalizationVersion'
    ),
}
assert cost_route['liveRuntimeCostEvidence'] == {
    'id': 'E-RUNTIME-COST-001',
    'status': 'blocked',
    'reasonCodes': [
        'DEV142_benchmark_and_DEV143_145_runtime_chain_unavailable',
        'paired_provider_usage_and_normalization_evidence_unavailable',
    ],
    'nonEvidence': [
        'DEV132_architecture_scenarios',
        'DEV128_compiled_fixtures',
        'DEV130_deterministic_fixture',
        'DEV138_repository_fixtures',
    ],
}
assert d['status'] == 'pass'
assert isinstance(d['limitations'], list) and d['limitations']

scenarios = d['scenarios']
assert [s['id'] for s in scenarios] == [
    'DEV132-SCENARIO-001',
    'DEV132-SCENARIO-002',
    'DEV132-SCENARIO-003',
    'DEV132-SCENARIO-004',
    'DEV132-SCENARIO-005',
    'DEV132-SCENARIO-006',
    'DEV132-SCENARIO-007',
]
required = {
    'id', 'title', 'workflowSkill', 'inputClass', 'expectedPattern',
    'sourceProfile', 'destinationProfile', 'finalResponseOwner',
    'contextPolicy', 'stateOutcome', 'safetyOutcomes', 'verification',
    'apiClaims', 'limitations',
}
assert all(set(s) == required for s in scenarios)
assert all(set(s['contextPolicy']) == {
    'included', 'excluded', 'classificationOutcome'
} for s in scenarios)
assert all(set(s['stateOutcome']) == {
    'phase', 'commandCount', 'effectCount', 'reconciliationRequired'
} for s in scenarios)
assert all(s['safetyOutcomes'] for s in scenarios)
assert all(s['verification']['requiredIds'] for s in scenarios)
assert all(s['apiClaims'] for s in scenarios)
assert all(s['limitations'] for s in scenarios)

s1, s2, s3, s4, s5, s6, s7 = scenarios
assert s1['workflowSkill'] == 'design-apple-foundation-models-handoff'
assert s1['expectedPattern'] == 'baton_pass'
assert s1['destinationProfile'] == s1['finalResponseOwner'] == 'review'
assert s1['verification']['expectedResult'] == 'pass'

assert s2['workflowSkill'] == 'review-apple-foundation-models-handoff'
assert s2['verification']['expectedResult'] == 'fail'
assert set(s2['verification']['requiredIds']) == {
    'D-OWNER-001', 'D-TRANSITION-001',
    'D-CONTEXT-001', 'D-CONTEXT-002',
}

assert s3['expectedPattern'] == 'isolated_consultation'
assert s3['sourceProfile'] == s3['finalResponseOwner'] == 'parent'
assert s3['destinationProfile'] == 'specialist_child'
assert s3['stateOutcome']['phase'] == 'stable'

assert s4['workflowSkill'] == 'debug-apple-foundation-models-handoff'
assert s4['expectedPattern'] == 'baton_pass'
assert s4['stateOutcome'] == {
    'phase': 'recoveryRequired',
    'commandCount': 1,
    'effectCount': 1,
    'reconciliationRequired': True,
}
outcomes = {o['id']: o['expected'] for o in s4['safetyOutcomes']}
assert outcomes['C3_PROVIDER_ENVELOPE'] == 'blocked_zero_commands'
assert outcomes['UNCERTAIN_ALLOWED_EFFECT'] == 'one_effect_one_command'
assert outcomes['REPLAY'] == 'zero_additional_commands'
assert outcomes['RETRY'] == 'blocked_until_reconciled'
assert outcomes['LATE_OR_REPLAYED_EVENT'] == 'no_state_or_authority_mutation'
assert outcomes['NO_SAFE_RECONCILIATION'] == (
    'repair_blocked_remain_recovery_required'
)

for scenario, outcome in (
    (s5, 'no_activation'),
    (s6, 'clarification_required'),
):
    assert scenario['workflowSkill'] == 'none'
    assert scenario['expectedPattern'] == 'deterministic_routing'
    assert scenario['stateOutcome']['commandCount'] == 0
    assert scenario['stateOutcome']['effectCount'] == 0
    route_outcomes = {
        o['id']: o['expected'] for o in scenario['safetyOutcomes']
    }
    assert route_outcomes['NON_POSITIVE_OUTCOME'] == outcome
    assert route_outcomes['NON_POSITIVE_SIDE_EFFECTS'] == (
        'no_workflow_reference_architectureResult_tool_effect_command_'
        'agent_hook_or_Apple_claim'
    )

assert s7['workflowSkill'] == 'none'
assert s7['expectedPattern'] == 'deterministic_routing'
assert s7['finalResponseOwner'] == 'host_parent'
cost_outcomes = {o['id']: o['expected'] for o in s7['safetyOutcomes']}
assert cost_outcomes['DIAGNOSTIC_ACTION'] == 'condense_diagnostic_output'
assert cost_outcomes['ORIGINAL_TOOL_EXECUTION'] == 'one_before_PostToolUse'
assert cost_outcomes['ORIGINAL_TOOL_RERUN'] == 'zero_for_every_route_outcome'
assert cost_outcomes['DECLINE_OR_UNAVAILABLE'] == 'original_result_unchanged'
assert cost_outcomes['APPLE_FAILURE'] == (
    'normalized_error_plus_original_result'
)
assert cost_outcomes['PARENT_USAGE_BOUNDARY'] == (
    'no_first_turn_savings_claim_lower_subsequent_consumption_target'
)
assert cost_outcomes['LIVE_ACCEPTANCE'].startswith('blocked_pending_')
assert all(
    'E-RUNTIME-COST-001' not in s['verification']['requiredIds']
    for s in scenarios if s['verification']['expectedResult'] == 'pass'
)
assert s7['apiClaims'][0]['surface'] == (
    'DEV128_SDK_26_5_fixture_regression_boundary'
)

allowed_labels = {
    'compiled_sdk_26_5', 'interface_verified_sdk_26_5',
    'official_os_xcode_27_beta_locally_unverified',
    'pseudocode_deterministic_mock', 'blocked',
}
assert all(c['versionLabel'] in allowed_labels
           for s in scenarios for c in s['apiClaims'])
print('DEV132_SCENARIOS_PASS count=7 semantic_contract=pass')
PY
```

Expected output:
`DEV132_SCENARIOS_PASS count=7 semantic_contract=pass`.

This check validates scenario semantics and cross-field invariants. File
existence or JSON syntax alone is not acceptance.

### Step 5: Perform independent consistency and risk reviews

Run two read-only reviewers in parallel because they share no mutable state:

1. **Architecture consistency reviewer:** compare every scenario field against
   the design spec, decision record, DEV-128 pattern/API map, and DEV-131 stable
   IDs. It must report any wrong activation, pattern, owner, version label, or
   oracle set with exact file/line or JSON-pointer evidence.
2. **Security and recovery risk reviewer:** compare Scenarios 2 and 4 against
   DEV-130. It must actively look for C3 serialization, conflated blocked and
   dispatched paths, unauthorized trust expansion, replay, exactly-once or
   rollback overclaim, missing reconciliation, termination before
   reconciliation, late/replayed mutation of authority/phase/pending/checkpoint/
   counts/ledger, sensitive evidence, or `stateVersion`/`policyVersion` drift.

Reviewers do not edit. The Task 2 implementer resolves only confirmed findings;
rerun the complete semantic oracle after each change.

### Step 6: Commit Task 2 atomically

```bash
git add docs/research/evidence/dev-132-architecture-scenarios.json
git diff --cached --check
git diff --cached --name-only
git commit -m 'docs(DEV-132): record architecture scenario proof'
```

Expected staged path: the scenario JSON only.

## Task 3: Run complete issue verification

Do not edit while collecting the first verification result. If a gate fails,
invoke `superpowers:systematic-debugging`, establish root cause, assign the
narrow correction to the prior task implementer or a fresh worker, and commit
the correction separately.

### Step 1: Verify scope, history, and allowed paths

```bash
set -e
# Reviewed main base captured for this PR.
base=6992d57cc4b6882f7c644141852cddad23e77d2a
git merge-base --is-ancestor "$base" HEAD
git diff --check "$base"..HEAD
actual_paths_file="$(mktemp)"
expected_paths_file="$(mktemp)"
git diff --name-only "$base"..HEAD | sort > "$actual_paths_file"
printf '%s\n' \
  docs/architecture/apple-foundation-models-handoff-mvp-decision-record.md \
  docs/research/evidence/dev-132-architecture-scenarios.json \
  docs/superpowers/plans/2026-07-17-dev-132-mvp-architecture.md \
  docs/superpowers/specs/2026-07-17-dev-132-mvp-architecture-design.md \
  | sort > "$expected_paths_file"
diff -u "$expected_paths_file" "$actual_paths_file"
git status --short
```

Expected: no diff, no worktree status, and only atomic DEV-132 commits after the
base.

### Step 2: Re-run DEV-132 document and JSON semantic gates

Run Task 1 Step 4, Task 2 Step 4, and:

```bash
set -e
spec=docs/superpowers/specs/2026-07-17-dev-132-mvp-architecture-design.md
plan=docs/superpowers/plans/2026-07-17-dev-132-mvp-architecture.md
record=docs/architecture/apple-foundation-models-handoff-mvp-decision-record.md
json=docs/research/evidence/dev-132-architecture-scenarios.json
for path in "$spec" "$plan" "$record" "$json"; do test -s "$path"; done
placeholder_re='T(BD)|TO(DO)|FIX(ME)|fill in detai(ls)|implement lat(er)'
! rg -n -e "$placeholder_re" \
  "$spec" "$plan" "$record" "$json"
test "$(rg -c '^### Scenario [1-7]:' "$spec")" -eq 7
git diff --check origin/main...HEAD
```

### Step 3: Re-run DEV-131 deterministic evaluation proof

```bash
set -e
PYTHONDONTWRITEBYTECODE=1 \
  python3 -m unittest discover -s fixtures/dev-131/tests -p 'test_*.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 fixtures/dev-131/proof_runner.py
pycache_root="$(mktemp -d)"
PYTHONPYCACHEPREFIX="$pycache_root" \
  python3 -m compileall -q fixtures/dev-131
test -z "$(find . -type d -name '__pycache__' -print -quit)"
test -z "$(find . -type f -name '*.pyc' -print -quit)"
```

Expected: 26 tests pass; proof runner reports `schemaVersion=1.0`, top-level
`status=pass`, 11/11 executed oracle matches, safe evidence pass, valid rubric
pass, invalid critical rubric fail, and zero-denominator `not_applicable`.

### Step 4: Re-run DEV-130 deterministic security proof

```bash
set -e
artifact_dir="$(mktemp -d)"
swiftc -warnings-as-errors -parse-as-library \
  fixtures/dev-130/HandoffSecurityPolicy.swift \
  fixtures/dev-130/AdversarialScenarios.swift \
  -o "$artifact_dir/dev130-adversarial"
"$artifact_dir/dev130-adversarial" > "$artifact_dir/first.out"
diff -u fixtures/dev-130/expected-output.txt "$artifact_dir/first.out"
"$artifact_dir/dev130-adversarial" > "$artifact_dir/second.out"
cmp "$artifact_dir/first.out" "$artifact_dir/second.out"
rg -q '^SUMMARY passed=8 failed=0$' "$artifact_dir/first.out"
```

Expected: warnings-as-errors compile succeeds, exact golden matches, summary is
8 pass/0 fail, including diagnostic-result routing, and the repeat is
byte-identical.

### Step 5: Re-run the DEV-128 six-positive/two-blocker matrix

```bash
set -e
artifact_dir="$(mktemp -d)"
SDK="$(xcrun --sdk macosx --show-sdk-path)"
TARGET=arm64-apple-macos26.0
swiftc -warnings-as-errors -typecheck -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/stable-surface.swift
swiftc -warnings-as-errors -typecheck -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/generable-macro.swift
swiftc -warnings-as-errors -parse-as-library -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/availability-probe.swift \
  -o "$artifact_dir/availability"
"$artifact_dir/availability" > "$artifact_dir/availability.out"
rg -q '^availability=' "$artifact_dir/availability.out"
rg -q '^isAvailable=' "$artifact_dir/availability.out"
rg -q '^contextSize=[0-9]+$' "$artifact_dir/availability.out"
rg -q '^supportsCurrentLocale=' "$artifact_dir/availability.out"
swiftc -warnings-as-errors -parse-as-library -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/transcript-roundtrip.swift \
  -o "$artifact_dir/transcript"
test "$("$artifact_dir/transcript")" = \
  'entries=3 codableRoundTrip=true rehydrated=true'
swiftc -warnings-as-errors -parse-as-library -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/session-isolation.swift \
  -o "$artifact_dir/isolation"
test "$("$artifact_dir/isolation")" = \
  'parentEntries=1 childEntries=1 isolated=true'
swiftc -warnings-as-errors -parse-as-library -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/baton-pass-state.swift \
  -o "$artifact_dir/baton"
test "$("$artifact_dir/baton")" = \
  'source=research destination=review active=review finalOwner=review transferred=true'

set +e
swiftc -warnings-as-errors -typecheck -target arm64-apple-macos27.0 \
  -sdk "$SDK" fixtures/dev-128/blocked/os-27-beta-surface.swift \
  >"$artifact_dir/beta.out" 2>&1
beta_rc=$?
swiftc -warnings-as-errors -typecheck -target arm64-apple-macos27.0 \
  -sdk "$SDK" fixtures/dev-128/blocked/evaluations-import.swift \
  >"$artifact_dir/evaluations.out" 2>&1
evaluations_rc=$?
set -e
test "$beta_rc" -ne 0
test "$evaluations_rc" -ne 0
rg -q "DynamicProfile.*not a member type|has no member 'Profile'" \
  "$artifact_dir/beta.out"
rg -q "extra arguments at positions #1, #2 in call" "$artifact_dir/beta.out"
rg -q "extra argument 'toolCallingMode' in call" "$artifact_dir/beta.out"
rg -q "no such module 'Evaluations'" "$artifact_dir/evaluations.out"
```

Expected: six positive fixtures pass and both strict expected blockers match
their capability-specific diagnostics. Static macros are now positive under
Xcode 26.6; the old Command Line Tools blocker is historical. The availability
values themselves
remain host-state observations; their four output shapes are the gate.
Unique `mktemp` artifacts remain outside the repository because destructive
cleanup commands are not permitted in this execution environment.

### Step 6: Preserve historical host evidence without false passes

The following July 17 probe is retained only as historical provenance. Do not
run it as a current acceptance gate or repeat its Command Line Tools blockers:
the current bounded observation is Xcode 26.6, Swift 6.3.3, and SDK 26.5, with
the six-positive/two-strict-blocker DEV-128 matrix in Step 5. Current downstream
host/model issues own their own matrices; missing live Apple, paired telemetry,
or runtime prerequisites remain `blocked` rather than inheriting this output.

```bash
set -e

normalize_host_version() {
  python3 -c '
import re
import sys

patterns = {
    "claude": r"[0-9]+\.[0-9]+\.[0-9]+ \(Claude Code\)",
    "codex": r"codex-cli [0-9]+\.[0-9]+\.[0-9]+",
}
value = sys.stdin.read()
print(value if re.fullmatch(patterns[sys.argv[1]], value) else "null")
' "$1"
}

set +e
claude_bin="$(command -v claude 2>/dev/null)"
claude_lookup_rc=$?
codex_bin="$(command -v codex 2>/dev/null)"
codex_lookup_rc=$?
set -e

claude_version_output=null
claude_version_rc=1
claude_row_state=blocked
claude_row_reason=executable_missing
if test "$claude_lookup_rc" -eq 0 && test -n "$claude_bin"; then
  if test ! -x "$claude_bin"; then
    claude_row_reason=executable_not_runnable
  else
    set +e
    claude_version_raw="$("$claude_bin" --version 2>/dev/null)"
    claude_version_rc=$?
    set -e
    claude_version_output="$(printf '%s' "$claude_version_raw" | \
      normalize_host_version claude)"
    if test "$claude_version_rc" -ne 0 || test -z "$claude_version_raw"; then
      claude_version_output=null
      claude_row_reason=version_unavailable
    elif test "$claude_version_output" = null; then
      claude_row_reason=version_output_invalid
    elif test "$claude_version_output" = '2.1.91 (Claude Code)'; then
      claude_row_state=pass
      claude_row_reason=approved_baseline
    else
      claude_row_reason=version_mismatch
    fi
  fi
fi

codex_version_output=null
codex_version_rc=1
codex_row_state=blocked
codex_row_reason=executable_missing
if test "$codex_lookup_rc" -eq 0 && test -n "$codex_bin"; then
  if test ! -x "$codex_bin"; then
    codex_row_reason=executable_not_runnable
  else
    set +e
    codex_version_raw="$("$codex_bin" --version 2>/dev/null)"
    codex_version_rc=$?
    set -e
    codex_version_output="$(printf '%s' "$codex_version_raw" | \
      normalize_host_version codex)"
    if test "$codex_version_rc" -ne 0 || test -z "$codex_version_raw"; then
      codex_version_output=null
      codex_row_reason=version_unavailable
    elif test "$codex_version_output" = null; then
      codex_row_reason=version_output_invalid
    elif test "$codex_version_output" = 'codex-cli 0.144.5'; then
      codex_row_state=pass
      codex_row_reason=approved_baseline
    else
      codex_row_reason=version_mismatch
    fi
  fi
fi

printf 'host=claude phase=prerequisite executable=<host-path> version=%s status=%s reason=%s\n' \
  "$claude_version_output" "$claude_row_state" "$claude_row_reason"
printf 'host=codex phase=prerequisite executable=<host-path> version=%s status=%s reason=%s\n' \
  "$codex_version_output" "$codex_row_state" "$codex_row_reason"
if test "$claude_row_state" != pass || test "$codex_row_state" != pass; then
  exit 1
fi

developer_dir="$(xcode-select -p)"
set +e
xcodebuild_output="$(xcodebuild -version 2>&1)"
xcodebuild_rc=$?
instruments_output="$(xcrun --find instruments 2>&1)"
instruments_rc=$?
xctrace_output="$(xcrun --find xctrace 2>&1)"
xctrace_rc=$?
iphoneos_output="$(xcrun --sdk iphoneos --show-sdk-path 2>&1)"
iphoneos_rc=$?
simctl_output="$(xcrun --find simctl 2>&1)"
simctl_rc=$?
evaluations_dir="$(mktemp -d)"
evaluations_source="$evaluations_dir/evaluations.swift"
printf 'import Evaluations\n' > "$evaluations_source"
evaluations_output="$(xcrun swiftc -typecheck "$evaluations_source" 2>&1)"
evaluations_rc=$?
set -e
test -n "$developer_dir"
printf 'developerDirectory=<developer-dir>\n'
classify_blocker_probe() {
  probe_name="$1"
  probe_rc="$2"
  probe_raw_output="$3"
  probe_state=fail
  probe_diagnostic_class=unexpected_diagnostic
  case "$probe_name" in
    xcodebuild)
      expected_fragment='requires Xcode'
      expected_class=full_xcode_unavailable
      ;;
    instruments|xctrace|simctl)
      expected_fragment='unable to find utility'
      expected_class=utility_not_found
      ;;
    iphoneos)
      expected_fragment='SDK "iphoneos" cannot be located'
      expected_class=sdk_not_found
      ;;
    evaluations)
      expected_fragment="no such module 'Evaluations'"
      expected_class=module_not_found
      ;;
    *)
      expected_fragment=''
      expected_class=unknown_probe
      ;;
  esac
  if test "$probe_rc" -ne 0 && \
     test -n "$expected_fragment" && \
     [[ "$probe_raw_output" == *"$expected_fragment"* ]]; then
    probe_state=blocked
    probe_diagnostic_class="$expected_class"
  fi
  printf 'probe=%s rc=%s status=%s diagnosticClass=%s\n' \
    "$probe_name" "$probe_rc" "$probe_state" "$probe_diagnostic_class"
  test "$probe_state" = blocked
}
classify_blocker_probe xcodebuild "$xcodebuild_rc" "$xcodebuild_output"
classify_blocker_probe instruments "$instruments_rc" "$instruments_output"
classify_blocker_probe xctrace "$xctrace_rc" "$xctrace_output"
classify_blocker_probe iphoneos "$iphoneos_rc" "$iphoneos_output"
classify_blocker_probe simctl "$simctl_rc" "$simctl_output"
classify_blocker_probe evaluations "$evaluations_rc" "$evaluations_output"

set +e
claude_bin_after="$(command -v claude 2>/dev/null)"
claude_lookup_after_rc=$?
codex_bin_after="$(command -v codex 2>/dev/null)"
codex_lookup_after_rc=$?
claude_version_after_raw="$("$claude_bin" --version 2>/dev/null)"
claude_version_after_rc=$?
codex_version_after_raw="$("$codex_bin" --version 2>/dev/null)"
codex_version_after_rc=$?
set -e
claude_version_after="$(printf '%s' "$claude_version_after_raw" | \
  normalize_host_version claude)"
codex_version_after="$(printf '%s' "$codex_version_after_raw" | \
  normalize_host_version codex)"

claude_integrity_state=pass
claude_integrity_reason=stable_resolution_and_version
if test "$claude_lookup_after_rc" -ne 0 || \
   test "$claude_bin_after" != "$claude_bin" || \
   test "$claude_version_after_rc" -ne 0 || \
   test "$claude_version_after" = null || \
   test "$claude_version_after" != "$claude_version_output"; then
  claude_integrity_state=fail
  claude_integrity_reason=resolution_or_version_drift
  if test "$claude_version_after_rc" -ne 0 || \
     test -z "$claude_version_after_raw" || \
     test "$claude_version_after" = null; then
    claude_version_after=null
  fi
fi

codex_integrity_state=pass
codex_integrity_reason=stable_resolution_and_version
if test "$codex_lookup_after_rc" -ne 0 || \
   test "$codex_bin_after" != "$codex_bin" || \
   test "$codex_version_after_rc" -ne 0 || \
   test "$codex_version_after" = null || \
   test "$codex_version_after" != "$codex_version_output"; then
  codex_integrity_state=fail
  codex_integrity_reason=resolution_or_version_drift
  if test "$codex_version_after_rc" -ne 0 || \
     test -z "$codex_version_after_raw" || \
     test "$codex_version_after" = null; then
    codex_version_after=null
  fi
fi

printf 'host=claude phase=integrity executable=<host-path> version=%s status=%s reason=%s\n' \
  "$claude_version_after" "$claude_integrity_state" "$claude_integrity_reason"
printf 'host=codex phase=integrity executable=<host-path> version=%s status=%s reason=%s\n' \
  "$codex_version_after" "$codex_integrity_state" "$codex_integrity_reason"
if test "$claude_integrity_state" != pass || \
   test "$codex_integrity_state" != pass; then
  exit 1
fi
```

Historical July 17 result only: Command Line Tools was selected and the listed
Xcode/device tooling was blocked. Before operations, a missing/non-runnable executable, unavailable
version, or version other than the approved baseline produces a normalized
`blocked` row with `<host-path>` and observed exact version or `null`; only then
does the command exit. Claude 2.1.91 and Codex 0.144.5 produce prerequisite
`pass`, but version output proves binary prerequisites only. All later
Claude/Codex operations use `"$claude_bin"` and `"$codex_bin"`. After successful
capture, resolution or version drift emits normalized `fail`, invalidates the
row, and then exits. Alternate-PATH Claude Code 2.1.140 is neither a substitute
nor an extra acceptance row. DEV-132 does not claim plugin discovery,
activation, reference loading, model execution, device execution, or Xcode 27
evidence. Only strict single-line Claude/Codex version formats may enter the
row; malformed, multiline, or path-bearing output becomes `null` and is never
echoed. Raw blocker diagnostics stay transient. Committed blocker evidence is
limited to the probe name, exit code, normalized status, and stable
`diagnosticClass` after the expected error class is verified.

### Step 7: Verify downstream Linear propagation

Read DEV-133 through DEV-145 from Linear, including DEV-136/137 and DEV-139
through DEV-145. Confirm each affected issue contains the
DEV-132 propagation comment with decision, rationale, source issue, and impact,
and that no stale assumption contradicts the approved root/fallback, five
positive workflows, bounded non-positive router, generated-artifact ownership,
Apple-first runtime chain, security, or cost/evidence contracts. If a durable decision changed,
update DEV-132 first, then every affected downstream issue before proceeding.

## Task 4: Obtain final whole-issue review and attach evidence

### Step 1: Assign a fresh whole-issue reviewer

The reviewer must not be a Task 1/2 implementer or prior focused reviewer. Give
it the full DEV-132 issue, blocker documents, design spec, implementation plan,
decision record, scenario JSON, commit history, and fresh verification output.
Require an explicit verdict against every Definition of Done item and every
out-of-scope rule. It must inspect actual content and JSON semantics, not infer
success from paths, lint, discovery, or previous reviewer statements.

If it finds an issue, invoke `superpowers:receiving-code-review`, verify the
claim technically, assign the narrow correction, rerun affected gates and the
full verification suite, and obtain a fresh final verdict.

### Step 2: Confirm atomic integration against current main

Fetch `origin/main`, verify the reviewed remote head has not changed, and
integrate only the unique DEV-132 four-path delta. Resolve conflicts in favor
of current `main` plus DEV-132-owned behavior, then rerun Tasks 3 and 4. Stop on
remote drift; never overwrite concurrent work.

### Step 3: Attach durable evidence in Linear

Post one DEV-132 evidence comment containing:

- exact branch, current-main base SHA, final head, and ordered commit list;
- links to all four allowed repository artifacts;
- Task 1 semantic gate result;
- the exact scenario-oracle output and scenario count;
- independent consistency, risk, and whole-issue review verdicts;
- DEV-128/130/131 command results and counts;
- current blocker commands and diagnostics;
- normalized `<host-path>` executable identities, exact host versions,
  resolution-stability results, and explicit prerequisite-only labels;
- the exact allowed-path diff result and clean worktree result;
- downstream propagation issue/comment references; and
- every non-claim and deferred capability.

Link the issue-scoped PR after it exists. Do not mark DEV-132 complete
until the Definition of Done is fully proven and the evidence comment is
durable in Linear.

### Step 4: Verify the atomic PR

The PR targets `main`. Its body must include the Linear issue, four-path scope,
verification summary, blockers/non-claims, and current base/head bindings.

### Step 5: Final completion gate

Invoke `superpowers:verification-before-completion` and rerun the fresh commands
it requires. Then confirm:

- DEV-132 issue evidence and downstream propagation are current;
- the PR diff contains only the four allowed paths;
- all required deterministic and compile gates pass;
- each host row used one captured executable, records normalized `<host-path>`
  plus exact version, and rejects resolution drift;
- all unsupported capabilities are blocked or not run, never false passes;
- all focused and final reviews are resolved; and
- the worktree is clean.

Only then may DEV-132 be marked complete.
