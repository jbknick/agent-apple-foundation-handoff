# DEV-132 Apple Foundation Models Handoff MVP Architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:subagent-driven-development` to execute this plan task by task.

**Goal:** Publish a durable, internally consistent MVP architecture decision
record and machine-checkable proof for four representative design scenarios,
without creating any production plugin artifact.

**Architecture:** The canonical design spec fixes the product and repository
contract. A concise decision record will restate every binding choice with its
source, rationale, and downstream impact. A normalized JSON evidence file will
encode four representative scenarios against one small design-proof schema so
deterministic checks can validate activation, pattern, ownership, safety,
version labels, and expected verification IDs. Existing DEV-128, DEV-130, and
DEV-131 fixtures remain the executable regression authorities.

**Tech Stack:** Markdown, JSON, Python 3 standard library, Swift 6.3.2,
macOS SDK 26.5, Git, Linear, Claude Code 2.1.91, and Codex CLI 0.144.5.

## Global constraints

- Work only in
  `/Users/josephknickerbocker/.codex/worktrees/agent-apple-foundation-handoff/dev-132`
  on `codex/dev-132-mvp-architecture`.
- The reviewed stack base is
  `3792e8c98a387b7f9c48bd210d25938b40cdd5fe` (DEV-131). Before opening the
  stacked PR, rebase onto the final reviewed DEV-131 head if that head changed.
- The stacked PR targets `codex/dev-131-evaluation-strategy`, not `main`.
- The design commit is
  `61e40ae` (`docs(DEV-132): design MVP architecture`). Preserve it as an
  independently reviewable commit.
- Do not push, merge, tag, publish, or release unless the active issue separately
  authorizes that action. Opening the issue-scoped PR is permitted only after
  final verification and review.
- Do not create production manifests, marketplaces, skills, references,
  schemas, generators, tests, Swift fixtures, hooks, agents, commands, MCP
  servers, apps, dependencies, or runtime packages in DEV-132.
- Do not edit any generated artifact. The proposed generated paths in the
  design are downstream contracts, not DEV-132 deliverables.
- Use Apple-owned material and the installed SDK for Apple API truth. Structural
  reference repositories never establish Apple API behavior.
- Never turn missing Xcode, SDK, device, simulator, Instruments, Evaluations,
  host automation, authentication, or model access into a pass.
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
- Exactly five workflow skills: design, implement, review, debug, and validate,
  using the exact directory names in the design spec.
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

1. identify DEV-127 through DEV-131 and their reviewed heads as source issues;
2. state the plugin identity, users, five workflows, exact skill names, and
   explicit MVP exclusions;
3. state one physical skill/reference corpus and the five concern-owned
   references;
4. distinguish canonical inputs, generated outputs, and edit rules;
5. include the complete root candidate tree and complete conventional fallback
   tree, the precise fallback triggers, marketplace source for each, and the
   exclusion of repository-only material from capabilities and effective cached
   payload content;
6. state that root placement is conditional evidence, not a present success;
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
12. record rejected alternatives and deferred work; and
13. provide a decision-propagation table for DEV-133 through DEV-141 with
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
  'D-OWNER-001' 'not_applicable' 'DEV-141'; do
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

## Task 2: Add machine-checkable four-scenario architecture proof

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

### Step 2: Establish the JSON contract RED

Run before creating the file:

```bash
set +e
python3 - <<'PY'
import json
from pathlib import Path

path = Path('docs/research/evidence/dev-132-architecture-scenarios.json')
data = json.loads(path.read_text())
assert data['schemaVersion'] == '1.0'
assert len(data['scenarios']) == 4
PY
red_rc=$?
set -e
test "$red_rc" -ne 0
```

Expected: nonzero because the evidence file does not yet exist.

### Step 3: Create the normalized JSON evidence

Use `apply_patch`. Top-level fields must be:

```text
schemaVersion
evidenceKind = design_scenario
sourceIssue = DEV-132
designArtifact
designArtifactSha256
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

Encode exactly these cases:

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
assert d['status'] == 'pass'
assert isinstance(d['limitations'], list) and d['limitations']

scenarios = d['scenarios']
assert [s['id'] for s in scenarios] == [
    'DEV132-SCENARIO-001',
    'DEV132-SCENARIO-002',
    'DEV132-SCENARIO-003',
    'DEV132-SCENARIO-004',
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

s1, s2, s3, s4 = scenarios
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

allowed_labels = {
    'compiled_sdk_26_5', 'interface_verified_sdk_26_5',
    'official_os_xcode_27_beta_locally_unverified',
    'pseudocode_deterministic_mock', 'blocked',
}
assert all(c['versionLabel'] in allowed_labels
           for s in scenarios for c in s['apiClaims'])
print('DEV132_SCENARIOS_PASS count=4 semantic_contract=pass')
PY
```

Expected output:
`DEV132_SCENARIOS_PASS count=4 semantic_contract=pass`.

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
base=3792e8c98a387b7f9c48bd210d25938b40cdd5fe
git merge-base --is-ancestor "$base" HEAD
git diff --check "$base"..HEAD
git diff --name-only "$base"..HEAD | sort > /tmp/dev132-actual-paths
printf '%s\n' \
  docs/architecture/apple-foundation-models-handoff-mvp-decision-record.md \
  docs/research/evidence/dev-132-architecture-scenarios.json \
  docs/superpowers/plans/2026-07-17-dev-132-mvp-architecture.md \
  docs/superpowers/specs/2026-07-17-dev-132-mvp-architecture-design.md \
  | sort > /tmp/dev132-expected-paths
diff -u /tmp/dev132-expected-paths /tmp/dev132-actual-paths
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
test "$(rg -c '^### Scenario [1-4]:' "$spec")" -eq 4
git diff --check 3792e8c98a387b7f9c48bd210d25938b40cdd5fe..HEAD
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
rg -q '^SUMMARY passed=7 failed=0$' "$artifact_dir/first.out"
```

Expected: warnings-as-errors compile succeeds, exact golden matches, summary is
7 pass/0 fail, and the repeat is byte-identical.

### Step 5: Re-run DEV-128 compiled SDK 26.x matrix

```bash
set -e
artifact_dir="$(mktemp -d)"
SDK="$(xcrun --sdk macosx --show-sdk-path)"
TARGET=arm64-apple-macos26.0
swiftc -warnings-as-errors -typecheck -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/stable-surface.swift
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
```

Expected: all compiles and assertions pass. The availability values themselves
remain host-state observations; their four output shapes are the gate.
Unique `mktemp` artifacts remain outside the repository because destructive
cleanup commands are not permitted in this execution environment.

### Step 6: Reconfirm narrow blockers without false passes

Run and record exit status plus exact diagnostics:

```bash
xcode-select -p
xcodebuild -version
xcrun --find instruments
xcrun --find xctrace
xcrun --sdk iphoneos --show-sdk-path
xcrun --find simctl
printf 'import Evaluations\n' > /tmp/dev132-evaluations.swift
xcrun swiftc -typecheck /tmp/dev132-evaluations.swift
claude --version
codex --version
```

Expected on the planning host: Command Line Tools path is available;
`xcodebuild`, Instruments/xctrace, iPhone SDK, simctl, and Evaluations remain
blocked; Claude reports 2.1.91 and Codex reports 0.144.5. Version commands prove
binary prerequisites only. DEV-132 does not claim plugin discovery, activation,
reference loading, model execution, device execution, or Xcode 27 evidence.

### Step 7: Verify downstream Linear propagation

Read DEV-133 through DEV-141 from Linear. Confirm each issue contains the
DEV-132 propagation comment with decision, rationale, source issue, and impact,
and that no stale assumption contradicts the approved root/fallback, five-skill,
generation, security, or evidence contracts. If a durable decision changed,
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

### Step 2: Rebase the stack safely if required

Fetch/review the current DEV-131 head. If it differs from the recorded base,
rebase `codex/dev-132-mvp-architecture` onto that reviewed head, preserving the
atomic commit boundaries. Resolve only DEV-132 conflicts. Re-run Tasks 3 and 4
after the rebase. Do not merge the parent branch into this branch.

### Step 3: Attach durable evidence in Linear

Post one DEV-132 evidence comment containing:

- exact branch, parent branch, base SHA, final head, and ordered commit list;
- links to all four allowed repository artifacts;
- Task 1 semantic gate result;
- the exact scenario-oracle output and scenario count;
- independent consistency, risk, and whole-issue review verdicts;
- DEV-128/130/131 command results and counts;
- current blocker commands and diagnostics;
- host binary versions, explicitly labelled prerequisite-only;
- the exact allowed-path diff result and clean worktree result;
- downstream propagation issue/comment references; and
- every non-claim and deferred capability.

Link the issue-scoped stacked PR after it exists. Do not mark DEV-132 complete
until the Definition of Done is fully proven and the evidence comment is
durable in Linear.

### Step 4: Open the atomic stacked PR

Only after all gates and reviews pass, push the DEV-132 branch and open a PR
targeting `codex/dev-131-evaluation-strategy`. The PR body must include the
Linear issue, commit-by-commit review guide, four-path scope, verification
summary, blockers/non-claims, and stack dependency. Do not merge it.

### Step 5: Final completion gate

Invoke `superpowers:verification-before-completion` and rerun the fresh commands
it requires. Then confirm:

- DEV-132 issue evidence and downstream propagation are current;
- the stacked PR diff contains only the four allowed paths;
- all required deterministic and compile gates pass;
- all unsupported capabilities are blocked or not run, never false passes;
- all focused and final reviews are resolved; and
- the worktree is clean.

Only then may DEV-132 be marked complete.
