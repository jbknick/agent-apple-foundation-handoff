# DEV-132 Apple Foundation Models Handoff MVP Architecture Implementation Plan

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
- The active sequential PR review plan and the user's publication authorization
  govern this branch: workers never push or merge; the main agent may update the
  PR and squash-merge only after all three review rounds and current gates pass.
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

## Task 1: Amend the canonical design and durable decision record

**Files:**

- Amend:
  `docs/superpowers/specs/2026-07-17-dev-132-mvp-architecture-design.md`
- Amend:
  `docs/architecture/apple-foundation-models-handoff-mvp-decision-record.md`
- Read:
  `docs/research/dev-128-foundation-models-api-map.md`
- Read:
  `docs/research/dev-129-production-pattern-comparison.md`
- Read:
  `docs/research/dev-130-handoff-threat-model.md`
- Read:
  `docs/research/dev-131-evaluation-strategy.md`

### Step 1: Apply the July 18 architecture amendment

Read the sources above before editing. Amend the canonical design first, then
keep the existing decision record consistent with it rather than creating a
parallel design. After any design edit, Task 2 must refresh the scenario JSON's
`designArtifactSha256`. Together, the design and record must:

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

### Step 2: Run semantic and consistency gates

Run:

```bash
set -e
record=docs/architecture/apple-foundation-models-handoff-mvp-decision-record.md
test -s "$record"
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
  rg -q -F "## $section" "$record"
done
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
  'No safe reconciliation' 'metadata-only' 'rubric stimulus' \
  '<host-path>' 'no_activation' 'clarification_required' \
  'condense_diagnostic_output' 'providerNormalizationVersion' \
  'D-OWNER-001' 'not_applicable' 'DEV-141' 'DEV-145'; do
  rg -q -F "$token" "$record"
done
git diff --check -- "$record"
```

Expected: every assertion exits `0`; the placeholder search prints nothing.

## Task 2: Amend the machine-checkable seven-scenario architecture proof

**Files:**

- Amend:
  `docs/research/evidence/dev-132-architecture-scenarios.json`
- Read:
  `docs/superpowers/specs/2026-07-17-dev-132-mvp-architecture-design.md`
- Read:
  `docs/architecture/apple-foundation-models-handoff-mvp-decision-record.md`
- Read:
  `fixtures/dev-131/proof_runner.py`

### Step 1: Preserve the observed RED evidence

Round 1 checked the pre-amendment four-case snapshot for scenarios 001-007 and
the `no_activation`, `clarification_required`, and
`condense_diagnostic_output` contract. The recorded result was
`DEV132_AMENDMENT_RED rc=1`: scenarios 005-007 and the July 18 routing/cost
contract were absent. This is historical RED evidence; the Step 3 oracle is the
current acceptance gate.

### Step 2: Amend the normalized JSON evidence

Change only the scenario JSON. Use normalized synthetic data: no raw prompt,
response, reasoning, or tool content; no real user data or credentials; and no
claim that a design-level case ran a real host, model, provider, or Apple
runtime. The evidence must satisfy the DEV-131 path, content, structured-key,
classification, and hash boundaries; it does not authorize raw/live evidence.
Top-level fields must be:

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

### Step 3: Run the semantic oracle

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

## Task 3: Run complete issue verification

Do not edit while collecting the first verification result. If a gate fails,
establish root cause and address the narrow correction in the active review
round before rerunning the affected gate.

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

Run Task 1 Step 2, Task 2 Step 3, and:

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
their capability-specific diagnostics. Static macros are positive under Xcode
26.6. The availability values themselves remain host-state observations; their
four output shapes are the gate.
Unique `mktemp` artifacts remain outside the repository because destructive
cleanup commands are not permitted in this execution environment.

### Step 6: Preserve historical host evidence without false passes

The July 17 host probe and its normalized output remain as provenance in the
chronological DEV-132 Linear comments and evidence. Do not rerun that probe or
treat its obsolete host and Command Line Tools observations as current
acceptance.

Current bounded compile evidence is Xcode 26.6, Swift 6.3.3, and macOS SDK
26.5, with the six-positive/two-strict-blocker DEV-128 matrix in Step 5.
Live Apple execution, paired `pluginOff`/`pluginOn` cost telemetry, and the
DEV-143 through DEV-145 runtime chain remain `blocked`, not inferred from
compile or historical evidence. Each downstream issue owns its current
captured executable, normalized `<host-path>`, exact version, resolution
stability, and model matrix. DEV-132 claims no plugin discovery, activation,
reference loading, model execution, device execution, or Xcode 27 evidence.

### Step 7: Verify downstream Linear propagation

Read DEV-133 through DEV-145 from Linear, including DEV-136/137 and DEV-139
through DEV-145. Confirm each affected issue contains the
DEV-132 propagation comment with decision, rationale, source issue, and impact,
and that no stale assumption contradicts the approved root/fallback, five
positive workflows, bounded non-positive router, generated-artifact ownership,
Apple-first runtime chain, security, or cost/evidence contracts. If a durable
decision changed, update DEV-132 first, then every affected downstream issue
before proceeding.

## Task 4: Complete the three-round review and publish evidence

### Step 1: Run exactly three main-agent review/fix rounds

The main agent reviews the complete four-path delta against the latest DEV-132
issue, chronological comments, GitHub feedback, blocker documents, and current
verification output:

1. correctness and scope, including every Definition of Done item and
   out-of-scope rule;
2. simplicity, including readability, concise ownership, DRY, and removal of
   dead or speculative scaffolding; and
3. adversarial acceptance, including recovery, replay, decline/failure,
   evidence honesty, stale bindings, and whole-PR readiness.

For every round, record severity-ranked findings with exact evidence and the
smallest bounded correction. A fresh worker may change only named allowed
paths, commits locally, and never pushes or merges. Use RED/GREEN evidence for
behavioral corrections. The main agent inspects every fix and reruns the
affected gates; a clean round creates no no-op commit. Finish only when all
three rounds have zero actionable findings.

### Step 2: Confirm atomic integration against current main

Immediately re-read Linear and GitHub, fetch `origin/main`, and verify the
reviewed remote head has not changed. Keep only the unique DEV-132 four-path
delta, resolving conflicts in favor of current `main` plus DEV-132-owned
behavior. Stop on remote drift or lease failure; never overwrite concurrent
work. Rerun Task 3 after integration.

### Step 3: Attach durable evidence in Linear

Post one DEV-132 evidence comment containing:

- exact branch, current-main base SHA, final head, and ordered commit list;
- links to all four allowed repository artifacts;
- Task 1 semantic gate result;
- the exact scenario-oracle output and scenario count;
- the three main-agent review verdicts and closed findings;
- DEV-128/130/131 command results and counts;
- normalized blocker evidence containing only probe, status, exit code, and
  `diagnosticClass`; raw diagnostics remain transient;
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
- every cited host row uses one captured executable, records normalized
  `<host-path>` plus exact version, and rejects resolution drift;
- all unsupported capabilities are blocked or not run, never false passes;
- all three review rounds have zero actionable findings; and
- the worktree is clean.

Only then may DEV-132 be marked complete.
