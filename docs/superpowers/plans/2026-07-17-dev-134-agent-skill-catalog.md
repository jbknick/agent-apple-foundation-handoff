# DEV-134 Agent Skill Catalog Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:subagent-driven-development` (recommended) or
> `superpowers:executing-plans` to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish a precise five-skill activation, workflow, output, reference,
and design-prototype verification contract without implementing production
skills or plugin artifacts.

**Architecture:** One canonical design defines direct positive preselection for
the five exact DEV-132 skills plus one bounded non-positive router that can only
decline or clarify. A compact architecture contract gives downstream authors
stable names, sections, and routing rules, while a hash-bound JSON artifact
executes exactly 15 synthetic activation cases against identical Claude/Codex
design expectations. Real host activation remains blocked until the production
candidate exists.

**Tech Stack:** Markdown, JSON, Python 3 standard library, Git, Linear, Swift
6.3.2 regression fixtures, macOS SDK 26.5, Claude Code 2.1.91 prerequisite, and
Codex CLI 0.144.5 prerequisite.

## Global Constraints

- Work on `codex/dev-134-skill-architecture` from merged `main`
  `6134d4f40ab802b9f292e2b631177561f2b5e25d` (through DEV-133 / PR #7).
- DEV-134 does not edit repository guidance or generated adapters.
- Do not push, open or edit a pull request, merge, tag, release, publish, or
  move DEV-134 beyond `In Progress`.
- Apply repository changes with `apply_patch`; keep commits single-purpose.
- Do not add production `SKILL.md`, manifests, marketplaces, schemas, scripts,
  Swift fixtures, agents, hooks, commands, MCP servers, apps, dependencies, or
  runtime packages.
- Preserve exactly five direct positive workflow names and one physical
  provider-neutral skill/reference corpus. No skill invokes another skill.
- One bounded non-positive router may return only `no_activation` or
  `clarification_required` for out-of-domain, ambiguous-domain, or
  missing-approved-contract input. It is not a sixth workflow; positive input
  bypasses it, including compound review-first.
- The non-positive router cannot select or invoke a workflow, load references,
  emit `architectureResult`, or use tools, effects, commands, agents, hooks,
  MCP, apps, scripts, dependencies, or runtime, and makes no Apple/host claim.
  The DEV-142 through DEV-145 cost router, `PostToolUse` hook, and Swift bridge
  chain are separate later runtime.
- Preserve DEV-132's five concern-owned reference filenames unchanged. A
  reference has one concern owner and every skill-to-reference edge is direct.
- No plugin-local worker is approved. Per-skill `agents/openai.yaml` remains
  optional presentation metadata only and is not created in this issue.
- Positive results use `architectureSchemaVersion: "1.0"` and preserve all
  DEV-132 state, security, recovery, evidence, and limitation domains.
- Executed Apple claim labels are exactly `compiled_sdk_26_5` and
  `interface_verified_sdk_26_5`; SDK 26.x is a family boundary only.
- OS/Xcode 27 beta, deterministic pseudocode/mock, and blocked claims remain
  separate from locally executed SDK 26.5 evidence.
- Ordinary budget/no-safe-path termination applies only from `stable`.
  Uncertain external truth remains `recoveryRequired` until explicit successful
  reconciliation; late/replayed events mutate nothing and emit no command.
- Runtime/live-host telemetry contributes normalized metadata only. The
  DEV-131 synthetic/approved-redacted rubric allowance remains separately
  scanner- and hash-gated.
- Default validation uses no live model, PCC, custom provider, credential,
  network, paid service, entitlement, hardware, or full Xcode.

## Exact Allowed Path Set

The final DEV-134 diff contains exactly:

```text
docs/superpowers/plans/2026-07-17-dev-134-agent-skill-catalog.md
docs/superpowers/specs/2026-07-17-dev-134-agent-skill-catalog-design.md
docs/architecture/apple-foundation-models-handoff-skill-contract.md
docs/research/evidence/dev-134-activation-prototype.json
```

Any review correction changes only one or more of these paths and receives a
separate single-purpose commit.

---

### Task 1: Write the canonical Agent Skill catalog design

**Files:**

- Create:
  `docs/superpowers/specs/2026-07-17-dev-134-agent-skill-catalog-design.md`
- Read:
  `docs/superpowers/specs/2026-07-17-dev-132-mvp-architecture-design.md`
- Read:
  `docs/architecture/apple-foundation-models-handoff-mvp-decision-record.md`
- Read: `docs/research/dev-128-foundation-models-api-map.md`
- Read: `docs/research/dev-129-production-pattern-comparison.md`
- Read: `docs/research/dev-130-handoff-threat-model.md`
- Read: `docs/research/dev-131-evaluation-strategy.md`

**Interfaces:**

- Consumes: governing DEV-134 Linear comments
  `3213d6cd-2fae-4168-aeeb-5a124f9af937`,
  `5d3d7021-a125-4e08-9d58-d8797b36af09`, and
  `ceceacdc-ad41-4f11-94a2-beca1026e369`, with original decision
  `e90f2a39-d887-48b6-a8ce-17a2fa56e0a3` as historical context, plus the
  merged DEV-132/DEV-133 contracts.
- Produces: the authoritative DEV-134 catalog, direct positive preselection,
  bounded non-positive router, common output sections, workflow-specific
  contracts, reference-routing matrix, 15 case identities, and two full
  walkthrough expectations.

- [ ] **Step 1: Assign one fresh SDD implementer**

  Give the worker Task 1 only. Require it to read every listed source, make no
  Linear update, and change only the design path. It must not create production
  skills or reinterpret structural references as Apple API authority.

- [ ] **Step 2: Prove the design contract is RED before creation**

  Run:

  ```bash
  set +e
  design=docs/superpowers/specs/2026-07-17-dev-134-agent-skill-catalog-design.md
  test -s "$design"
  red_file_rc=$?
  (
    for section in \
      'Purpose and authority' \
      'Resolved approaches' \
      'MVP scope and non-goals' \
      'Preselection contract' \
      'Common result contracts' \
      'Exact skill catalog' \
      'Progressive-disclosure routing' \
      'Plugin-agent decision' \
      'Design-prototype E2E suite' \
      'Host capability boundary' \
      'Downstream handoff' \
      'Completion criteria'; do
      rg -q -F "## $section" "$design" || exit 1
    done
  )
  red_semantic_rc=$?
  set -e
  test "$red_file_rc" -ne 0
  test "$red_semantic_rc" -ne 0
  ```

  Expected: both captured checks are nonzero because the file does not exist.

- [ ] **Step 3: Create the canonical design**

  Use `apply_patch`. The design must:

  1. cite exact merged DEV-128 through DEV-133 inputs and distinguish Apple
     primary-source authority from structural references;
  2. compare the selected five direct workflows plus bounded non-positive
     router with duplicated-workflow and collapsed/provider-specific
     alternatives;
  3. state every in-scope deliverable and every issue exclusion;
  4. define direct positive preselection by `requestedOperation`,
     `artifactState`, and `evidenceState`; define the bounded non-positive
     router, its two-only result set and prohibitions, and the direct
     review-first compound default;
  5. define positive, no-activation, and clarification result shapes;
  6. give every exact skill its purpose, exact what-and-when activation
     description, positive triggers, non-triggers, required inputs, ordered
     workflow, direct references, workflow-specific output, failure behavior,
     and non-goals;
  7. preserve the complete `1.0` result contract and corrected recovery,
     replay, fallback, SDK label, and evidence split;
  8. preserve the five exact reference filenames with sole concern ownership
     and deterministic direct links;
  9. reject a plugin-local worker and define optional per-skill YAML as
     presentation-only downstream metadata;
  10. specify exactly six positive, six negative, and three ambiguous synthetic
      cases with identical normalized Claude/Codex expectations;
  11. fully walk the new baton-pass design and flawed-reducer review cases
      through every common/workflow-specific section and guardrail;
  12. mark real Claude/Codex activation blocked until production skills and
      references exist, and name the later E rows; and
  13. map the resulting contract to DEV-135 through DEV-141 without moving
      implementation scope into DEV-134.

- [ ] **Step 4: Run GREEN design semantics**

  Run:

  ```bash
  set -e
  design=docs/superpowers/specs/2026-07-17-dev-134-agent-skill-catalog-design.md
  test -s "$design"
  for section in \
    'Purpose and authority' \
    'Resolved approaches' \
    'MVP scope and non-goals' \
      'Preselection contract' \
    'Common result contracts' \
    'Exact skill catalog' \
    'Progressive-disclosure routing' \
    'Plugin-agent decision' \
    'Design-prototype E2E suite' \
    'Host capability boundary' \
    'Downstream handoff' \
    'Completion criteria'; do
    rg -q -F "## $section" "$design"
  done
  for token in \
    'design-apple-foundation-models-handoff' \
    'implement-apple-foundation-models-handoff' \
    'review-apple-foundation-models-handoff' \
    'debug-apple-foundation-models-handoff' \
    'validate-apple-foundation-models-handoff' \
    'activationOwner = direct_workflow' \
    'activationOwner = non_positive_router' \
    'requestedOperation' 'artifactState' 'evidenceState' \
    'architectureSchemaVersion' 'stateVersion' 'policyVersion' \
    'recoveryRequired' 'compiled_sdk_26_5' \
    'interface_verified_sdk_26_5' 'design_contract_prototype' \
    'E-CLAUDE-ACTIVATE-001' 'E-CODEX-ACTIVATE-001'; do
    rg -q -F "$token" "$design"
  done
  test "$(rg -c '^### DEV134-POS-00[1-6]:' "$design")" -eq 6
  test "$(rg -c '^### DEV134-NEG-00[1-6]:' "$design")" -eq 6
  test "$(rg -c '^### DEV134-AMB-00[1-3]:' "$design")" -eq 3
  placeholder_re='T(BD)|TO(DO)|FIX(ME)|fill in detai(ls)|implement lat(er)'
  if rg -n -e "$placeholder_re" "$design"; then
    exit 1
  fi
  git diff --check -- "$design"
  ```

  Expected: all assertions exit `0`; the placeholder search emits nothing.

- [ ] **Step 5: Obtain two read-only Task 1 reviews**

  Assign a fresh spec-compliance reviewer to compare every design section with
  DEV-134, the Linear decision, and DEV-128 through DEV-132. After confirmed
  findings are corrected, assign a fresh quality/security reviewer to inspect
  activation overlap, missing inputs, Apple overclaims, state/recovery drift,
  reference duplication, and false host capability claims. Reviewers make no
  edits. Rerun Step 4 after every correction.

- [ ] **Step 6: Commit Task 1 atomically**

  Run:

  ```bash
  git add docs/superpowers/specs/2026-07-17-dev-134-agent-skill-catalog-design.md
  git diff --cached --check
  test "$(git diff --cached --name-only | wc -l | tr -d ' ')" -eq 1
  git commit -m 'docs(DEV-134): design Agent Skill catalog'
  ```

  Expected staged path: the canonical design only.

---

### Task 2: Publish the compact downstream skill contract

**Files:**

- Create:
  `docs/architecture/apple-foundation-models-handoff-skill-contract.md`
- Read:
  `docs/superpowers/specs/2026-07-17-dev-134-agent-skill-catalog-design.md`
- Read:
  `docs/architecture/apple-foundation-models-handoff-mvp-decision-record.md`

**Interfaces:**

- Consumes: the exact catalog, preselection, outputs, reference routes, and case IDs
  from Task 1.
- Produces: a concise non-authoritative downstream index that DEV-135 through
  DEV-141 can consume without duplicating the canonical design.

- [ ] **Step 1: Assign one fresh SDD implementer**

  Give the worker Task 2 only. It may change only the contract path. It must
  copy exact names and normalized fields, not invent a second design.

- [ ] **Step 2: Prove the compact contract is RED**

  Run:

  ```bash
  set +e
  contract=docs/architecture/apple-foundation-models-handoff-skill-contract.md
  test -s "$contract"
  red_file_rc=$?
  (
    for section in \
      'Contract authority' \
      'Positive preselection and bounded non-positive router' \
      'Exact catalog' \
      'Common positive result' \
      'Non-positive activation result' \
      'Skill contracts' \
      'Reference routing' \
      'Activation prototype IDs' \
      'Downstream handoff'; do
      rg -q -F "## $section" "$contract" || exit 1
    done
  )
  red_semantic_rc=$?
  set -e
  test "$red_file_rc" -ne 0
  test "$red_semantic_rc" -ne 0
  ```

  Expected: both captured checks are nonzero.

- [ ] **Step 3: Create the compact contract**

  Use `apply_patch`. Include:

  - canonical-design and Linear-decision pointers;
  - normalized direct-positive and bounded non-positive preselection;
  - exact positive/no-activation/clarification result fields;
  - direct-positive versus non-positive-router ownership and the router's
    two-result/prohibited-power boundary;
  - one row per skill with ownership, input gate, direct references, output
    additions, and failure boundary;
  - one row per reference with sole concern and direct consumer skills;
  - all 15 case IDs and expected activation outcome;
  - exact real-host blocker/nonclaim language; and
  - issue-specific downstream responsibilities.

  Keep this artifact compact. Detailed rationale and representative synthetic
  requests stay canonical in the Task 1 design.

- [ ] **Step 4: Run contract consistency gates**

  Run:

  ```bash
  set -e
  design=docs/superpowers/specs/2026-07-17-dev-134-agent-skill-catalog-design.md
  contract=docs/architecture/apple-foundation-models-handoff-skill-contract.md
  test -s "$contract"
  for section in \
    'Contract authority' \
    'Positive preselection and bounded non-positive router' \
    'Exact catalog' \
    'Common positive result' \
    'Non-positive activation result' \
    'Skill contracts' \
    'Reference routing' \
    'Activation prototype IDs' \
    'Downstream handoff'; do
    rg -q -F "## $section" "$contract"
  done
  for skill in \
    design-apple-foundation-models-handoff \
    implement-apple-foundation-models-handoff \
    review-apple-foundation-models-handoff \
    debug-apple-foundation-models-handoff \
    validate-apple-foundation-models-handoff; do
    test "$(rg -c -F "$skill" "$contract")" -ge 1
    rg -q -F "$skill" "$design"
  done
  for reference in \
    architecture-and-state.md \
    orchestration-patterns.md \
    apple-api-availability.md \
    security-context-and-recovery.md \
    evaluation-and-observability.md; do
    test "$(rg -c -F "$reference" "$contract")" -eq 1
    rg -q -F "$reference" "$design"
  done
  for prefix_count in POS:6 NEG:6 AMB:3; do
    prefix="${prefix_count%%:*}"
    expected="${prefix_count##*:}"
    test "$(rg -o "DEV134-${prefix}-[0-9]{3}" "$contract" | sort -u | wc -l | tr -d ' ')" -eq "$expected"
  done
  placeholder_re='T(BD)|TO(DO)|FIX(ME)|fill in detai(ls)|implement lat(er)'
  if rg -n -e "$placeholder_re" "$contract"; then
    exit 1
  fi
  git diff --check -- "$contract"
  ```

- [ ] **Step 5: Review and commit Task 2**

  Assign a fresh read-only contract reviewer to compare every normalized field,
  exact name, reference owner, case ID, and host nonclaim with Task 1. Resolve
  confirmed findings, rerun Step 4, then commit:

  ```bash
  git add docs/architecture/apple-foundation-models-handoff-skill-contract.md
  git diff --cached --check
  test "$(git diff --cached --name-only | wc -l | tr -d ' ')" -eq 1
  git commit -m 'docs(DEV-134): publish Agent Skill contract'
  ```

---

### Task 3: Execute the 15-case design activation prototype

**Files:**

- Create: `docs/research/evidence/dev-134-activation-prototype.json`
- Read:
  `docs/superpowers/specs/2026-07-17-dev-134-agent-skill-catalog-design.md`
- Read:
  `docs/architecture/apple-foundation-models-handoff-skill-contract.md`
- Read: `fixtures/dev-131/proof_runner.py`

**Interfaces:**

- Consumes: 15 exact case identities, normalized outcomes, common section set,
  full-walkthrough rules, and real-host blocker semantics.
- Produces: hash-bound, synthetic, machine-checkable
  `design_contract_prototype` evidence with no raw/live host or user content.

- [ ] **Step 1: Assign one fresh SDD implementer**

  Give the worker Task 3 only. It may change only the JSON path. Require exact
  schema keys and normalized synthetic values. Prohibit keys/content for raw
  prompts, responses, reasoning, tool arguments/results, credentials, paths,
  host identity, real user data, `.trace`, or `.xcresult`.

- [ ] **Step 2: Prove activation ownership is RED**

  Run:

  ```bash
  set +e
  PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
  import json
  from pathlib import Path

  artifact = Path('docs/research/evidence/dev-134-activation-prototype.json')
  data = json.loads(artifact.read_text())
  for case in data['cases']:
      expected_owner = (
          'direct_workflow'
          if case['category'] == 'positive'
          or case['id'] == 'DEV134-AMB-003'
          else 'non_positive_router'
      )
      assert case['activationOwner'] == expected_owner
  PY
  red_rc=$?
  set -e
  test "$red_rc" -ne 0
  ```

  Expected during the amendment: nonzero because the prior 15-case artifact
  cannot distinguish direct positive ownership from non-positive routing.

- [ ] **Step 3: Create the normalized prototype evidence**

  Use `apply_patch`. Top-level fields are exactly:

  ```text
  schemaVersion
  evidenceKind = design_contract_prototype
  sourceIssue = DEV-134
  designArtifact
  designArtifactSha256
  contractArtifact
  contractArtifactSha256
  executionLayer = design_contract_prototype
  status = pass
  realHostRows
  limitations
  cases
  ```

  `realHostRows` contains exactly Claude and Codex rows with `status=blocked`,
  `reason=production_skill_not_implemented`, and their activation evidence ID.

  Every case contains exactly:

  ```text
  id
  category = positive | negative | ambiguous
  activationOwner = direct_workflow | non_positive_router
  inputClass
  requestedOperation
  artifactState
  evidenceState
  expectedActivation
  hostExpectations = { claude, codex }
  expectedReferences
  expectedOutputSections
  expectedGuardrails = {
    applicable = [ordered stable D IDs]
    not_applicable = [ordered stable D IDs explicitly documented N/A]
  }
  fullWalkthrough
  resolution
  ```

  A guardrail ID omitted from both arrays is outside the case's asserted
  coverage; omission is not an implicit `not_applicable` status.

  Case outcomes are:

  | ID | Owner | Expected activation | Resolution |
  | --- | --- | --- | --- |
  | `DEV134-POS-001` | direct workflow | design skill | new baton-pass design, full walkthrough |
  | `DEV134-POS-002` | direct workflow | review skill | flawed reducer review, full walkthrough |
  | `DEV134-POS-003` | direct workflow | implement skill | approved contract change |
  | `DEV134-POS-004` | direct workflow | debug skill | observed uncertain-effect failure |
  | `DEV134-POS-005` | direct workflow | validate skill | proof-only evidence matrix |
  | `DEV134-POS-006` | direct workflow | design skill | isolated-consultation selection |
  | `DEV134-NEG-001` | non-positive router | no activation | App Intents |
  | `DEV134-NEG-002` | non-positive router | no activation | Apple Handoff |
  | `DEV134-NEG-003` | non-positive router | no activation | generic Swift |
  | `DEV134-NEG-004` | non-positive router | no activation | generic Core ML/Foundation Models education |
  | `DEV134-NEG-005` | non-positive router | no activation | coding-session handoff |
  | `DEV134-NEG-006` | non-positive router | no activation | Foundation Models runtime Skills alone |
  | `DEV134-AMB-001` | non-positive router | clarification required | “Apple handoff” domain ambiguity |
  | `DEV134-AMB-002` | non-positive router | clarification required | implementation lacks approved contract |
  | `DEV134-AMB-003` | direct workflow | review skill | documented review-first compound default |

- [ ] **Step 4: Run the complete semantic oracle**

  Run:

  ```bash
  PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
  import copy
  import hashlib
  import json
  from pathlib import Path, PurePosixPath

  artifact = Path('docs/research/evidence/dev-134-activation-prototype.json')
  data = json.loads(artifact.read_text())
  EXPECTED_ARTIFACTS = {
      'designArtifact': (
          'docs/superpowers/specs/'
          '2026-07-17-dev-134-agent-skill-catalog-design.md'
      ),
      'contractArtifact': (
          'docs/architecture/'
          'apple-foundation-models-handoff-skill-contract.md'
      ),
  }

  COMMON = [
      'Activation and Scope', 'Pattern and Ownership',
      'Apple API Availability', 'State and Lifecycle',
      'Trust and Model Boundaries', 'Context Policy',
      'Tools Effects and Confirmation', 'Failure Recovery and Fallback',
      'Verification and Evidence', 'Limitations',
  ]
  OUTPUTS = {
      'none': [],
      'design': COMMON + [
          'Alternatives', 'Decision Rationale', 'Proposed Components',
          'Implementation and Test Plan',
      ],
      'review': COMMON + ['Findings'],
      'implement': COMMON + [
          'Approved Decision', 'Change Boundary', 'Changed Paths',
          'Compilation and Regression Results',
      ],
      'debug': COMMON + [
          'Observed and Expected State', 'First Divergence', 'Root Cause',
          'Correction', 'Regression Proof',
      ],
      'validate': COMMON + [
          'Layer Matrix', 'Counts and Hashes', 'Rubric Result',
          'Blockers and Skips', 'Release Implication',
      ],
  }
  REFERENCES = {
      'none': [],
      'all': [
          'state', 'patterns', 'apple-availability', 'security-recovery',
          'evaluation',
      ],
      'debug': ['state', 'security-recovery', 'evaluation'],
  }
  GUARDRAILS = {
      'full_design': [
          'D-SCHEMA-001', 'D-ROUTE-001', 'D-OWNER-001',
          'D-TRANSITION-001', 'D-CONTEXT-001', 'D-CONTEXT-002',
          'D-GRANT-001', 'D-PHASE-001', 'D-FALLBACK-001',
          'D-EVIDENCE-001', 'D-RUBRIC-001',
      ],
      'design': [
          'D-ROUTE-001', 'D-OWNER-001', 'D-TRANSITION-001',
          'D-CONTEXT-001', 'D-CONTEXT-002', 'D-GRANT-001',
          'D-PHASE-001', 'D-FALLBACK-001', 'D-EVIDENCE-001',
          'D-RUBRIC-001',
      ],
      'review': [
          'D-SCHEMA-001', 'D-ROUTE-001', 'D-OWNER-001',
          'D-TRANSITION-001', 'D-TOOL-001', 'D-CONTEXT-001',
          'D-CONTEXT-002', 'D-GRANT-001', 'D-PHASE-001',
          'D-EFFECT-001', 'D-EFFECT-002', 'D-FALLBACK-001',
          'D-EVIDENCE-001', 'D-RUBRIC-001',
      ],
      'implement': [
          'D-SCHEMA-001', 'D-ROUTE-001', 'D-OWNER-001',
          'D-TRANSITION-001', 'D-CONTEXT-001', 'D-CONTEXT-002',
          'D-GRANT-001', 'D-PHASE-001', 'D-FALLBACK-001',
          'D-EVIDENCE-001', 'D-RUBRIC-001',
      ],
      'debug': [
          'D-SCHEMA-001', 'D-ROUTE-001', 'D-OWNER-001',
          'D-TRANSITION-001', 'D-TOOL-001', 'D-CONTEXT-001',
          'D-CONTEXT-002', 'D-GRANT-001', 'D-PHASE-001',
          'D-EFFECT-001', 'D-EFFECT-002', 'D-FALLBACK-001',
          'D-EVIDENCE-001', 'D-RUBRIC-001',
      ],
      'validate': [
          'D-SCHEMA-001', 'D-ROUTE-001', 'D-OWNER-001',
          'D-TRANSITION-001', 'D-TOOL-001', 'D-CONTEXT-001',
          'D-CONTEXT-002', 'D-GRANT-001', 'D-PHASE-001',
          'D-EFFECT-001', 'D-EFFECT-002', 'D-FALLBACK-001',
          'D-EVIDENCE-001', 'D-RUBRIC-001',
      ],
      'route': ['D-ROUTE-001'],
      'compound_review': [
          'D-ROUTE-001', 'D-OWNER-001', 'D-TRANSITION-001',
          'D-TOOL-001', 'D-CONTEXT-001', 'D-CONTEXT-002',
          'D-GRANT-001', 'D-PHASE-001', 'D-EFFECT-001',
          'D-EFFECT-002', 'D-FALLBACK-001', 'D-EVIDENCE-001',
          'D-RUBRIC-001',
      ],
  }
  POS1_NOT_APPLICABLE = [
      'D-TOOL-001', 'D-EFFECT-001', 'D-EFFECT-002',
  ]
  SPECS = [
      ('DEV134-POS-001', 'positive', 'direct_workflow',
       'new_baton_pass_architecture',
       'design', 'absent', 'missing',
       'design-apple-foundation-models-handoff', 'all', 'design',
       'full_design',
       POS1_NOT_APPLICABLE, True, 'baton_pass_destination_owner_selected'),
      ('DEV134-POS-002', 'positive', 'direct_workflow',
       'flawed_reducer_findings_review',
       'review', 'implementation', 'failing',
       'review-apple-foundation-models-handoff', 'all', 'review', 'review',
       [], True, 'reject_flawed_reducer_with_findings'),
      ('DEV134-POS-003', 'positive', 'direct_workflow',
       'approved_bounded_contract_change',
       'implement', 'approved_contract', 'available',
       'implement-apple-foundation-models-handoff', 'all', 'implement',
       'implement', [], False, 'bounded_approved_contract_change'),
      ('DEV134-POS-004', 'positive', 'direct_workflow',
       'uncertain_effect_recovery_failure',
       'debug', 'implementation', 'failing',
       'debug-apple-foundation-models-handoff', 'debug', 'debug', 'debug',
       [], False, 'recovery_required_reconciliation_without_replay'),
      ('DEV134-POS-005', 'positive', 'direct_workflow',
       'proof_only_evidence_matrix',
       'validate', 'evidence_bundle', 'available',
       'validate-apple-foundation-models-handoff', 'all', 'validate',
       'validate', [], False, 'proof_matrix_without_edits'),
      ('DEV134-POS-006', 'positive', 'direct_workflow',
       'isolated_consultation_architecture',
       'design', 'absent', 'missing',
       'design-apple-foundation-models-handoff', 'all', 'design', 'design',
       [], False, 'isolated_consultation_parent_owner_selected'),
      ('DEV134-NEG-001', 'negative', 'non_positive_router',
       'app_intents_request', 'unspecified',
       'unknown', 'unknown', 'no_activation', 'none', 'none', 'route', [],
       False, 'reject_out_of_domain'),
      ('DEV134-NEG-002', 'negative', 'non_positive_router',
       'apple_handoff_request', 'unspecified',
       'unknown', 'unknown', 'no_activation', 'none', 'none', 'route', [],
       False, 'reject_out_of_domain'),
      ('DEV134-NEG-003', 'negative', 'non_positive_router',
       'generic_swift_request', 'unspecified',
       'unknown', 'unknown', 'no_activation', 'none', 'none', 'route', [],
       False, 'reject_out_of_domain'),
      ('DEV134-NEG-004', 'negative', 'non_positive_router',
       'generic_foundation_models_education',
       'unspecified', 'unknown', 'unknown', 'no_activation', 'none', 'none',
       'route', [], False, 'reject_out_of_domain'),
      ('DEV134-NEG-005', 'negative', 'non_positive_router',
       'coding_session_handoff_request',
       'unspecified', 'unknown', 'unknown', 'no_activation', 'none', 'none',
       'route', [], False, 'reject_out_of_domain'),
      ('DEV134-NEG-006', 'negative', 'non_positive_router',
       'foundation_models_runtime_skills_request', 'unspecified', 'unknown',
       'unknown', 'no_activation', 'none', 'none', 'route', [], False,
       'reject_out_of_domain'),
      ('DEV134-AMB-001', 'ambiguous', 'non_positive_router',
       'ambiguous_apple_handoff_domain',
       'unspecified', 'unknown', 'unknown', 'clarification_required', 'none',
       'none', 'route', [], False, 'bounded_domain_clarification'),
      ('DEV134-AMB-002', 'ambiguous', 'non_positive_router',
       'implementation_without_approved_contract', 'implement', 'unknown',
       'missing', 'clarification_required', 'none', 'none', 'route', [],
       False, 'bounded_contract_clarification'),
      ('DEV134-AMB-003', 'ambiguous', 'direct_workflow',
       'compound_review_and_fix',
       'compound_review_fix', 'implementation', 'failing',
       'review-apple-foundation-models-handoff', 'all', 'review',
       'compound_review', [], False, 'documented_default_review_first'),
  ]

  def expected_cases():
      built = []
      for spec in SPECS:
          (case_id, category, activation_owner, input_class, operation,
           artifact_state, evidence_state, activation, refs, outputs, guards,
           not_applicable, full, resolution) = spec
          built.append({
              'id': case_id,
              'category': category,
              'activationOwner': activation_owner,
              'inputClass': input_class,
              'requestedOperation': operation,
              'artifactState': artifact_state,
              'evidenceState': evidence_state,
              'expectedActivation': activation,
              'hostExpectations': {
                  'claude': activation,
                  'codex': activation,
              },
              'expectedReferences': REFERENCES[refs],
              'expectedOutputSections': OUTPUTS[outputs],
              'expectedGuardrails': {
                  'applicable': GUARDRAILS[guards],
                  'not_applicable': not_applicable,
              },
              'fullWalkthrough': full,
              'resolution': resolution,
          })
      return built

  def check(candidate):
      assert set(candidate) == {
          'schemaVersion', 'evidenceKind', 'sourceIssue', 'designArtifact',
          'designArtifactSha256', 'contractArtifact',
          'contractArtifactSha256', 'executionLayer', 'status',
          'realHostRows', 'limitations', 'cases',
      }
      assert candidate['schemaVersion'] == '1.0'
      assert candidate['evidenceKind'] == 'design_contract_prototype'
      assert candidate['sourceIssue'] == 'DEV-134'
      assert candidate['executionLayer'] == 'design_contract_prototype'
      assert candidate['status'] == 'pass'

      # Exact binding is deliberately before Path construction or file reads.
      for key, expected in EXPECTED_ARTIFACTS.items():
          assert candidate[key] == expected

      repository_root = Path.cwd().resolve()
      for key, expected in EXPECTED_ARTIFACTS.items():
          pure = PurePosixPath(expected)
          assert not pure.is_absolute()
          assert '..' not in pure.parts
          assert pure.as_posix() == expected
          bound = Path(expected)
          assert not bound.is_symlink()
          assert bound.is_file()
          assert bound.resolve(strict=True).is_relative_to(repository_root)
          assert candidate[f'{key}Sha256'] == hashlib.sha256(
              bound.read_bytes()
          ).hexdigest()

      assert candidate['limitations']
      assert candidate['realHostRows'] == {
          'claude': {
              'status': 'blocked',
              'reason': 'production_skill_not_implemented',
              'requiredEvidenceId': 'E-CLAUDE-ACTIVATE-001',
          },
          'codex': {
              'status': 'blocked',
              'reason': 'production_skill_not_implemented',
              'requiredEvidenceId': 'E-CODEX-ACTIVATE-001',
          },
      }
      assert candidate['cases'] == expected_cases()
      for case in candidate['cases']:
          assert case['activationOwner'] in {
              'direct_workflow', 'non_positive_router',
          }
          statuses = case['expectedGuardrails']
          assert set(statuses) == {'applicable', 'not_applicable'}
          assert not set(statuses['applicable']) & set(
              statuses['not_applicable']
          )

  check(data)
  print(
      'DEV134_ACTIVATION_PROTOTYPE_PASS total=15 positive=6 negative=6 '
      'ambiguous=3 full=2 hosts=blocked oracle=exact'
  )

  def case(candidate, case_id):
      return next(row for row in candidate['cases'] if row['id'] == case_id)

  def assert_rejected(name, mutate):
      candidate = copy.deepcopy(data)
      mutate(candidate)
      try:
          check(candidate)
      except AssertionError:
          print(f'DEV134_HARD_ORACLE_MUTATION_REJECTED name={name}')
          return
      raise AssertionError(f'mutation accepted: {name}')

  assert_rejected(
      'positive_routed_through_router',
      lambda d: case(d, 'DEV134-POS-001').update(
          activationOwner='non_positive_router'
      ),
  )
  assert_rejected(
      'non_positive_bypasses_router',
      lambda d: case(d, 'DEV134-NEG-001').update(
          activationOwner='direct_workflow'
      ),
  )
  assert_rejected(
      'implementation_absent_contract',
      lambda d: case(d, 'DEV134-POS-003').update(
          artifactState='absent', evidenceState='missing'
      ),
  )
  assert_rejected(
      'unsafe_retry',
      lambda d: case(d, 'DEV134-POS-004').update(
          resolution='retry_effect_immediately_without_reconciliation'
      ),
  )
  assert_rejected(
      'missing_review_guardrails',
      lambda d: case(d, 'DEV134-POS-002')['expectedGuardrails'][
          'applicable'
      ].remove('D-GRANT-001'),
  )
  assert_rejected(
      'missing_validation_refs',
      lambda d: case(d, 'DEV134-POS-005')['expectedReferences'].remove(
          'evaluation'
      ),
  )

  def add_pos001_effect_ids(candidate):
      statuses = case(candidate, 'DEV134-POS-001')['expectedGuardrails']
      statuses['applicable'].extend(statuses['not_applicable'])
      statuses['not_applicable'] = []

  assert_rejected('pos001_effect_ids', add_pos001_effect_ids)

  def route_ambiguous_to_effect(candidate):
      row = case(candidate, 'DEV134-AMB-001')
      row.update(
          inputClass='uncertain_effect_recovery_failure',
          requestedOperation='debug',
          artifactState='implementation',
          evidenceState='failing',
      )
      row['expectedGuardrails']['applicable'].extend([
          'D-EFFECT-001', 'D-EFFECT-002',
      ])

  assert_rejected('ambiguous_route_to_effect', route_ambiguous_to_effect)
  assert_rejected(
      'missing_output_section',
      lambda d: case(d, 'DEV134-POS-003')['expectedOutputSections'].remove(
          'Changed Paths'
      ),
  )

  def retarget(candidate, path_key, hash_key, value):
      candidate[path_key] = value
      candidate[hash_key] = hashlib.sha256(
          Path(value).read_bytes()
      ).hexdigest()

  assert_rejected(
      'wrong_file_retarget',
      lambda d: retarget(
          d, 'designArtifact', 'designArtifactSha256', 'README.md'
      ),
  )
  assert_rejected(
      'absolute_path_retarget',
      lambda d: retarget(
          d, 'contractArtifact', 'contractArtifactSha256', '/etc/hosts'
      ),
  )
  assert_rejected(
      'traversal_path_retarget',
      lambda d: retarget(
          d, 'designArtifact', 'designArtifactSha256',
          'docs/../README.md'
      ),
  )
  print('DEV134_ACTIVATION_MUTATION_PASS rejected=12')
  PY
  ```

  Expected:

  ```text
  DEV134_ACTIVATION_PROTOTYPE_PASS total=15 positive=6 negative=6 ambiguous=3 full=2 hosts=blocked oracle=exact
  DEV134_ACTIVATION_MUTATION_PASS rejected=12
  ```

- [ ] **Step 5: Run DEV-131 safety scanners against the JSON**

  Run:

  ```bash
  PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
  import importlib.util
  import json
  from pathlib import Path

  module_path = Path('fixtures/dev-131/proof_runner.py')
  spec = importlib.util.spec_from_file_location('dev131_proof_runner', module_path)
  module = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(module)
  artifact = Path('docs/research/evidence/dev-134-activation-prototype.json')
  text = artifact.read_text()
  data = json.loads(text)
  assert module._text_is_safe(text)
  assert module._structured_content_is_safe(data)
  print('DEV134_EVIDENCE_SAFETY_PASS text=pass structured=pass')
  PY
  test -z "$(find . -type d -name '__pycache__' -print -quit)"
  test -z "$(find . -type f -name '*.pyc' -print -quit)"
  ```

- [ ] **Step 6: Obtain activation and adversarial reviews**

  Run two read-only reviewers in parallel because they share no mutable state:

  1. activation reviewer: exact case counts/identities, skill routing,
     non-triggers, ambiguity resolution, direct references, host equality, and
     full section coverage;
  2. adversarial reviewer: implementation-without-contract, review/debug/
     validate overlap, C3 transfer, provider fallback, recovery/replay,
     Apple-version overclaims, raw evidence, and structural-only host pass.

  The Task 3 implementer resolves confirmed findings only. Rerun Steps 4 and 5
  after every correction.

- [ ] **Step 7: Commit Task 3 atomically**

  Run:

  ```bash
  git add docs/research/evidence/dev-134-activation-prototype.json
  git diff --cached --check
  test "$(git diff --cached --name-only | wc -l | tr -d ' ')" -eq 1
  git commit -m 'docs(DEV-134): record activation prototype proof'
  ```

---

### Task 4: Verify the complete issue and attach durable evidence

**Files:**

- Verify all four allowed paths.
- Modify no repository file unless a confirmed review finding requires a
  separately committed correction.

**Interfaces:**

- Consumes: all Task 1 through Task 3 artifacts and review results.
- Produces: fresh verification output, final whole-issue review, and a durable
  DEV-134 Linear evidence comment while leaving the issue `In Progress`.

- [ ] **Step 1: Verify exact scope, history, parent, and cleanliness**

  Run:

  ```bash
  set -e
  base=6134d4f40ab802b9f292e2b631177561f2b5e25d
  git merge-base --is-ancestor "$base" HEAD
  test "$(git rev-parse "$base")" = "$base"
  git diff --check "$base"..HEAD
  actual="$(mktemp)"
  expected="$(mktemp)"
  git diff --name-only "$base"..HEAD | sort > "$actual"
  printf '%s\n' \
    docs/architecture/apple-foundation-models-handoff-skill-contract.md \
    docs/research/evidence/dev-134-activation-prototype.json \
    docs/superpowers/plans/2026-07-17-dev-134-agent-skill-catalog.md \
    docs/superpowers/specs/2026-07-17-dev-134-agent-skill-catalog-design.md \
    | sort > "$expected"
  diff -u "$expected" "$actual"
  test -z "$(git status --short)"
  ```

- [ ] **Step 2: Rerun every DEV-134 semantic and evidence gate**

  Run Task 1 Step 4, Task 2 Step 4, and Task 3 Steps 4 and 5 from the exact
  final head. Then run:

  ```bash
  set -e
  design=docs/superpowers/specs/2026-07-17-dev-134-agent-skill-catalog-design.md
  plan=docs/superpowers/plans/2026-07-17-dev-134-agent-skill-catalog.md
  contract=docs/architecture/apple-foundation-models-handoff-skill-contract.md
  evidence=docs/research/evidence/dev-134-activation-prototype.json
  for artifact in "$design" "$plan" "$contract" "$evidence"; do
    test -s "$artifact"
  done
  placeholder_re='T(BD)|TO(DO)|FIX(ME)|fill in detai(ls)|implement lat(er)'
  if rg -n -e "$placeholder_re" "$design" "$plan" "$contract" "$evidence"; then
    exit 1
  fi
  mac_user_root='/'"Users/"
  linux_home_root='/'"home/"
  temp_root='/'"tmp/"
  if rg -n -F \
    -e "$mac_user_root" \
    -e "$linux_home_root" \
    -e "$temp_root" \
    "$design" "$plan" "$contract" "$evidence"; then
    exit 1
  fi
  git diff --check 6134d4f40ab802b9f292e2b631177561f2b5e25d..HEAD
  ```

- [ ] **Step 3: Rerun inherited deterministic regressions**

  Run DEV-131:

  ```bash
  set -e
  PYTHONDONTWRITEBYTECODE=1 \
    python3 -m unittest discover -s fixtures/dev-131/tests -p 'test_*.py' -v
  PYTHONDONTWRITEBYTECODE=1 python3 fixtures/dev-131/proof_runner.py
  pycache_root="$(mktemp -d)"
  PYTHONPYCACHEPREFIX="$pycache_root" python3 -m compileall -q fixtures/dev-131
  test -z "$(find . -type d -name '__pycache__' -print -quit)"
  test -z "$(find . -type f -name '*.pyc' -print -quit)"
  ```

  Expected: 26 tests pass, 11/11 oracle matches, evidence/rubric gates pass,
  and zero denominator remains `not_applicable`.

  Run DEV-130:

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

  Run DEV-128:

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
    > "$artifact_dir/beta.out" 2>&1
  beta_rc=$?
  set -e
  test "$beta_rc" -ne 0
  rg -q "DynamicProfile.*not a member type|has no member 'Profile'" \
    "$artifact_dir/beta.out"
  rg -q "extra arguments at positions #1, #2 in call" \
    "$artifact_dir/beta.out"
  rg -q "extra argument 'toolCallingMode' in call" \
    "$artifact_dir/beta.out"
  set +e
  swiftc -warnings-as-errors -typecheck -target arm64-apple-macos27.0 \
    -sdk "$SDK" fixtures/dev-128/blocked/evaluations-import.swift \
    > "$artifact_dir/evaluations.out" 2>&1
  evaluations_rc=$?
  set -e
  test "$evaluations_rc" -ne 0
  rg -q "no such module 'Evaluations'" "$artifact_dir/evaluations.out"
  ```

  Expected: exact SDK 26.5 matrix six positive gates and two strict,
  diagnostic-specific expected blockers pass.

- [ ] **Step 4: Record honest host prerequisites and capability blockers**

  In one controlled shell, capture one Claude and Codex executable before any
  operation, validate strict single-line versions, and recheck resolution and
  version after the row. Expected approved prerequisites are Claude Code 2.1.91
  and Codex 0.144.5. Record only `<host-path>`, exact version, normalized state,
  and reason. Missing/non-runnable/wrong versions are prerequisite `blocked`;
  post-capture drift is `fail`.

  Do not run a fake plugin task. Record both activation rows as:

  ```text
  E-CLAUDE-ACTIVATE-001 blocked production_skill_not_implemented
  E-CODEX-ACTIVATE-001 blocked production_skill_not_implemented
  ```

  Version prerequisites do not change those capability blockers.

- [ ] **Step 5: Verify durable Linear propagation**

  Read DEV-134 and DEV-135 through DEV-141 immediately before acceptance.
  Require the current governing chain:

  ```text
  original: e90f2a39-d887-48b6-a8ce-17a2fa56e0a3
  bounded router: 5d3d7021-a125-4e08-9d58-d8797b36af09
  separate cost router: ceceacdc-ad41-4f11-94a2-beca1026e369
  latest amendment: 3213d6cd-2fae-4168-aeeb-5a124f9af937
  ```

  Require a newer issue-specific propagation comment on every affected
  downstream issue. Each must include source, decision, rationale, direct
  positive versus bounded non-positive ownership, separate cost routing, and
  issue-specific impact. Pre-amendment propagation is not sufficient. Correct
  DEV-134 first, then update every affected downstream comment before
  continuing.

- [ ] **Step 6: Obtain final independent whole-issue review**

  Assign a fresh reviewer who was not a Task 1/2/3 implementer or prior focused
  reviewer. Give it the complete Linear issue/comments, all four artifacts,
  exact commit sequence, and fresh verification output. Require finding-first
  Critical/Important/Minor counts, every Definition-of-Done item, and every
  out-of-scope exclusion. File existence or Markdown lint is not evidence.

  If it finds a problem, invoke `superpowers:receiving-code-review`, verify the
  claim, make the narrow correction in a separate commit, rerun all affected
  and full gates, and obtain a fresh final verdict.

- [ ] **Step 7: Attach durable Linear evidence**

  Add one DEV-134 comment with:

  - branch, exact parent, final head, ordered commits, and four-path scope;
  - links or exact paths to all four artifacts and their SHA-256 values;
  - design and compact-contract semantic results;
  - exact activation-oracle and evidence-safety outputs;
  - focused and final review verdicts;
  - DEV-128/130/131 regression counts;
  - normalized host prerequisite rows and explicit activation blockers;
  - clean worktree and no-cache results;
  - propagation comment IDs; and
  - every nonclaim and deferred capability.

  The main PR-review agent owns re-verification, push, merge, evidence
  propagation, and any status transition. Change issue status only when the
  current issue-level completion contract is satisfied.
