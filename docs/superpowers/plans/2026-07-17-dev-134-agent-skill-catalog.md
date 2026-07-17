# DEV-134 Agent Skill Catalog Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:subagent-driven-development` (recommended) or
> `superpowers:executing-plans` to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish a precise five-skill activation, workflow, output, reference,
and design-prototype verification contract without implementing production
skills or plugin artifacts.

**Architecture:** One canonical design defines action-plus-artifact-state
routing for the five exact DEV-132 skills. A compact architecture contract
gives downstream authors stable names, sections, and routing rules, while a
hash-bound JSON artifact executes exactly 15 synthetic activation cases against
identical Claude/Codex design expectations. Real host activation remains
blocked until the production candidate exists.

**Tech Stack:** Markdown, JSON, Python 3 standard library, Git, Linear, Swift
6.3.2 regression fixtures, macOS SDK 26.5, Claude Code 2.1.91 prerequisite, and
Codex CLI 0.144.5 prerequisite.

## Global Constraints

- Work on `codex/dev-134-skill-architecture` from exact parent
  `ca767a0c50e1b527fed5c87e0922bf51cf655295` (DEV-132 / PR #6).
- Root will later rebase this independent branch onto the final DEV-133 head;
  DEV-134 does not edit repository guidance or generated adapters.
- Do not push, open or edit a pull request, merge, tag, release, publish, or
  move DEV-134 beyond `In Progress`.
- Apply repository changes with `apply_patch`; keep commits single-purpose.
- Do not add production `SKILL.md`, manifests, marketplaces, schemas, scripts,
  Swift fixtures, agents, hooks, commands, MCP servers, apps, dependencies, or
  runtime packages.
- Preserve exactly five skill names and one physical provider-neutral skill and
  reference corpus. No skill invokes another skill.
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

- Consumes: DEV-134 Linear decision comment
  `e90f2a39-d887-48b6-a8ce-17a2fa56e0a3` and DEV-132 schema/state/security
  contracts.
- Produces: the authoritative DEV-134 catalog, activation router, common output
  sections, workflow-specific contracts, reference-routing matrix, 15 case
  identities, and two full walkthrough expectations.

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
      'Activation router' \
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

  1. cite exact reviewed DEV-128 through DEV-132 heads and distinguish Apple
     primary-source authority from structural references;
  2. compare the selected five-skill router with duplicated-workflow and
     collapsed/provider-specific alternatives;
  3. state every in-scope deliverable and every issue exclusion;
  4. define domain-first routing by `requestedOperation`, `artifactState`, and
     `evidenceState`, plus one bounded clarification and the review-first
     compound default;
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
    'Activation router' \
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
  ! rg -n -e "$placeholder_re" "$design"
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

- Consumes: the exact catalog, router, outputs, reference routes, and case IDs
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
      'Router schema' \
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
  - the normalized domain/operation/artifact/evidence router;
  - exact positive/no-activation/clarification result fields;
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
    'Router schema' \
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
  ! rg -n -e "$placeholder_re" "$contract"
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

- [ ] **Step 2: Prove the JSON prototype is RED**

  Run:

  ```bash
  set +e
  PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
  import json
  from pathlib import Path

  artifact = Path('docs/research/evidence/dev-134-activation-prototype.json')
  data = json.loads(artifact.read_text())
  assert data['schemaVersion'] == '1.0'
  assert len(data['cases']) == 15
  PY
  red_rc=$?
  set -e
  test "$red_rc" -ne 0
  ```

  Expected: nonzero because the JSON does not exist.

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
  inputClass
  requestedOperation
  artifactState
  evidenceState
  expectedActivation
  hostExpectations = { claude, codex }
  expectedReferences
  expectedOutputSections
  expectedGuardrails
  fullWalkthrough
  resolution
  ```

  Case outcomes are:

  | ID | Expected activation | Resolution |
  | --- | --- | --- |
  | `DEV134-POS-001` | design skill | new baton-pass design, full walkthrough |
  | `DEV134-POS-002` | review skill | flawed reducer review, full walkthrough |
  | `DEV134-POS-003` | implement skill | approved contract change |
  | `DEV134-POS-004` | debug skill | observed uncertain-effect failure |
  | `DEV134-POS-005` | validate skill | proof-only evidence matrix |
  | `DEV134-POS-006` | design skill | isolated-consultation selection |
  | `DEV134-NEG-001` | no activation | App Intents |
  | `DEV134-NEG-002` | no activation | Apple Handoff |
  | `DEV134-NEG-003` | no activation | generic Swift |
  | `DEV134-NEG-004` | no activation | generic Core ML/Foundation Models education |
  | `DEV134-NEG-005` | no activation | coding-session handoff |
  | `DEV134-NEG-006` | no activation | Foundation Models runtime Skills alone |
  | `DEV134-AMB-001` | clarification required | “Apple handoff” domain ambiguity |
  | `DEV134-AMB-002` | clarification required | implementation lacks approved contract |
  | `DEV134-AMB-003` | review skill | documented review-first compound default |

- [ ] **Step 4: Run the complete semantic oracle**

  Run:

  ```bash
  PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
  import hashlib
  import json
  from pathlib import Path

  artifact = Path('docs/research/evidence/dev-134-activation-prototype.json')
  data = json.loads(artifact.read_text())
  assert set(data) == {
      'schemaVersion', 'evidenceKind', 'sourceIssue', 'designArtifact',
      'designArtifactSha256', 'contractArtifact', 'contractArtifactSha256',
      'executionLayer', 'status', 'realHostRows', 'limitations', 'cases',
  }
  assert data['schemaVersion'] == '1.0'
  assert data['evidenceKind'] == 'design_contract_prototype'
  assert data['sourceIssue'] == 'DEV-134'
  assert data['executionLayer'] == 'design_contract_prototype'
  assert data['status'] == 'pass'
  design = Path(data['designArtifact'])
  contract = Path(data['contractArtifact'])
  assert data['designArtifactSha256'] == hashlib.sha256(design.read_bytes()).hexdigest()
  assert data['contractArtifactSha256'] == hashlib.sha256(contract.read_bytes()).hexdigest()
  assert data['limitations']

  rows = data['realHostRows']
  assert set(rows) == {'claude', 'codex'}
  assert rows['claude'] == {
      'status': 'blocked',
      'reason': 'production_skill_not_implemented',
      'requiredEvidenceId': 'E-CLAUDE-ACTIVATE-001',
  }
  assert rows['codex'] == {
      'status': 'blocked',
      'reason': 'production_skill_not_implemented',
      'requiredEvidenceId': 'E-CODEX-ACTIVATE-001',
  }

  cases = data['cases']
  assert len(cases) == 15
  assert len({case['id'] for case in cases}) == 15
  assert [case['id'] for case in cases] == [
      *(f'DEV134-POS-{i:03d}' for i in range(1, 7)),
      *(f'DEV134-NEG-{i:03d}' for i in range(1, 7)),
      *(f'DEV134-AMB-{i:03d}' for i in range(1, 4)),
  ]
  required_case_keys = {
      'id', 'category', 'inputClass', 'requestedOperation', 'artifactState',
      'evidenceState', 'expectedActivation', 'hostExpectations',
      'expectedReferences', 'expectedOutputSections', 'expectedGuardrails',
      'fullWalkthrough', 'resolution',
  }
  assert all(set(case) == required_case_keys for case in cases)
  assert all(case['hostExpectations'] == {
      'claude': case['expectedActivation'],
      'codex': case['expectedActivation'],
  } for case in cases)
  assert sum(case['category'] == 'positive' for case in cases) == 6
  assert sum(case['category'] == 'negative' for case in cases) == 6
  assert sum(case['category'] == 'ambiguous' for case in cases) == 3

  by_id = {case['id']: case for case in cases}
  expected = {
      'DEV134-POS-001': 'design-apple-foundation-models-handoff',
      'DEV134-POS-002': 'review-apple-foundation-models-handoff',
      'DEV134-POS-003': 'implement-apple-foundation-models-handoff',
      'DEV134-POS-004': 'debug-apple-foundation-models-handoff',
      'DEV134-POS-005': 'validate-apple-foundation-models-handoff',
      'DEV134-POS-006': 'design-apple-foundation-models-handoff',
      **{f'DEV134-NEG-{i:03d}': 'no_activation' for i in range(1, 7)},
      'DEV134-AMB-001': 'clarification_required',
      'DEV134-AMB-002': 'clarification_required',
      'DEV134-AMB-003': 'review-apple-foundation-models-handoff',
  }
  assert {case_id: by_id[case_id]['expectedActivation'] for case_id in expected} == expected

  for i in range(1, 7):
      case = by_id[f'DEV134-NEG-{i:03d}']
      assert not case['expectedReferences']
      assert not case['expectedOutputSections']
      assert case['resolution'] == 'reject_out_of_domain'

  assert by_id['DEV134-AMB-001']['resolution'] == 'bounded_domain_clarification'
  assert by_id['DEV134-AMB-002']['resolution'] == 'bounded_contract_clarification'
  assert by_id['DEV134-AMB-003']['resolution'] == 'documented_default_review_first'

  common_sections = {
      'Activation and Scope', 'Pattern and Ownership', 'Apple API Availability',
      'State and Lifecycle', 'Trust and Model Boundaries', 'Context Policy',
      'Tools Effects and Confirmation', 'Failure Recovery and Fallback',
      'Verification and Evidence', 'Limitations',
  }
  design_sections = {
      'Alternatives', 'Decision Rationale', 'Proposed Components',
      'Implementation and Test Plan',
  }
  review_sections = {'Findings'}
  full = [case for case in cases if case['fullWalkthrough']]
  assert [case['id'] for case in full] == ['DEV134-POS-001', 'DEV134-POS-002']
  assert common_sections | design_sections <= set(by_id['DEV134-POS-001']['expectedOutputSections'])
  assert common_sections | review_sections <= set(by_id['DEV134-POS-002']['expectedOutputSections'])
  assert {
      'D-ROUTE-001', 'D-OWNER-001', 'D-TRANSITION-001',
      'D-CONTEXT-001', 'D-CONTEXT-002', 'D-GRANT-001', 'D-EVIDENCE-001',
  } <= set(by_id['DEV134-POS-001']['expectedGuardrails'])
  assert {
      'D-OWNER-001', 'D-TRANSITION-001', 'D-CONTEXT-001', 'D-CONTEXT-002',
  } <= set(by_id['DEV134-POS-002']['expectedGuardrails'])
  assert all(case['expectedGuardrails'] for case in cases)
  print('DEV134_ACTIVATION_PROTOTYPE_PASS total=15 positive=6 negative=6 ambiguous=3 full=2 hosts=blocked')
  PY
  ```

  Expected:
  `DEV134_ACTIVATION_PROTOTYPE_PASS total=15 positive=6 negative=6 ambiguous=3 full=2 hosts=blocked`.

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
  base=ca767a0c50e1b527fed5c87e0922bf51cf655295
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
  ! rg -n -e "$placeholder_re" "$design" "$plan" "$contract" "$evidence"
  ! rg -n -e '/Users/' -e '/home/' -e '/tmp/' -e 'josephknickerbocker' \
    "$design" "$plan" "$contract" "$evidence"
  git diff --check ca767a0c50e1b527fed5c87e0922bf51cf655295..HEAD
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
  rg -q '^SUMMARY passed=7 failed=0$' "$artifact_dir/first.out"
  ```

  Run DEV-128:

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

  Expected: exact SDK 26.5 matrix 5/5 passes.

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

  Read DEV-134 and DEV-135 through DEV-141. Require the current decision comment
  and the seven issue-specific propagation comments:

  ```text
  DEV-134 e90f2a39-d887-48b6-a8ce-17a2fa56e0a3
  DEV-135 6b282bbf-288a-4582-8bd2-13c1719df5e1
  DEV-136 bb357f9f-679d-4433-8d51-9ae87d224aca
  DEV-137 345a6d29-124d-4af4-a62d-cd6d572c4d0b
  DEV-138 c1ba1445-e61f-4930-8cbb-12967bf99897
  DEV-139 d4eb842d-261f-4a8d-bc93-f6a822ea4549
  DEV-140 45d66203-53a2-43ea-85e7-ef9ab04b1a3f
  DEV-141 090f7959-846f-426a-b994-845e259f8ece
  ```

  Every comment must include source, decision, rationale, and issue-specific
  impact. Correct a durable decision in DEV-134 first, then update every
  affected downstream comment before continuing.

- [ ] **Step 6: Obtain final independent whole-issue review**

  Assign a fresh reviewer who was not a Task 1/2/3 implementer or prior focused
  reviewer. Give it the complete Linear issue/comments, all four artifacts,
  exact commit sequence, and fresh verification output. Require finding-first
  Critical/Important/Minor counts, every Definition-of-Done item, and every
  out-of-scope exclusion. File existence or Markdown lint is not evidence.

  If it finds a problem, invoke `superpowers:receiving-code-review`, verify the
  claim, make the narrow correction in a separate commit, rerun all affected
  and full gates, and obtain a fresh final verdict.

- [ ] **Step 7: Attach durable Linear evidence without changing final status**

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

  Leave DEV-134 `In Progress`. Root owns later rebase, re-verification, push,
  stacked PR creation, and status transition.
