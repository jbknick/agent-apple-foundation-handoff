# DEV-134 Agent Skill Catalog Verification Runbook

## Purpose and governing inputs

This runbook verifies the completed DEV-134 design-only artifact set. The
branch input is merged `main`
`6134d4f40ab802b9f292e2b631177561f2b5e25d` (through DEV-133 / PR #7).
The current Linear amendments are, in governing order:

- `3213d6cd-2fae-4168-aeeb-5a124f9af937`: five positive workflows plus one
  bounded non-positive router;
- `5d3d7021-a125-4e08-9d58-d8797b36af09`: router ownership and prohibited
  powers; and
- `ceceacdc-ad41-4f11-94a2-beca1026e369`: DEV-142 through DEV-145 cost routing
  is separate later runtime.

The original decision `e90f2a39-d887-48b6-a8ce-17a2fa56e0a3` is historical
context only where it conflicts with those amendments.

The complete DEV-134 diff is exactly these four paths:

```text
docs/architecture/apple-foundation-models-handoff-skill-contract.md
docs/research/evidence/dev-134-activation-prototype.json
docs/superpowers/plans/2026-07-17-dev-134-agent-skill-catalog.md
docs/superpowers/specs/2026-07-17-dev-134-agent-skill-catalog-design.md
```

DEV-134 remains architecture and deterministic design-prototype work. It adds
no production `SKILL.md`, plugin metadata, reference payload, generated file,
agent, hook, command, MCP server, app, dependency, script, Swift fixture, cost
router, bridge, or runtime behavior.

## Frozen acceptance contract

- The positive catalog is exactly
  `design-apple-foundation-models-handoff`,
  `implement-apple-foundation-models-handoff`,
  `review-apple-foundation-models-handoff`,
  `debug-apple-foundation-models-handoff`, and
  `validate-apple-foundation-models-handoff`.
- Positive preselection directly chooses one workflow. It bypasses the
  non-positive router, including the review-first compound default. No skill
  invokes another skill.
- The bounded non-positive router owns only out-of-domain rejection,
  ambiguous-domain clarification, and missing-approved-contract clarification.
  It returns only `no_activation` or `clarification_required`. It cannot select
  or invoke a workflow, load references, emit `architectureResult`, or use
  tools, effects, commands, agents, hooks, MCP, apps, scripts, dependencies, or
  runtime, and it makes no Apple or host-capability claim. It is not a sixth
  workflow. DEV-142 through DEV-145 cost routing, `PostToolUse`, and the Swift
  bridge chain remain separate later runtime.
- The common positive contract is `architectureSchemaVersion: "1.0"` and
  preserves state/owner transitions, C0-C3 grants, confirmation/tool/effect
  gates, no-rerun recovery and reconciliation, replay/cancellation safety,
  provenance, original-result behavior, fallback boundaries, evidence safety,
  and honest Apple/host labels.
- The five sole-owner references remain `architecture-and-state.md`,
  `orchestration-patterns.md`, `apple-api-availability.md`,
  `security-context-and-recovery.md`, and
  `evaluation-and-observability.md`; every consumer edge is direct.
- The prototype is exactly 6 positive, 6 negative, and 3 ambiguous cases.
  `DEV134-POS-001` and `DEV134-POS-002` are the two full walkthroughs. Seven
  cases have `direct_workflow` ownership and eight have
  `non_positive_router` ownership. Those `activationOwner` values are prototype
  evidence metadata, not emitted envelope fields. Claude and Codex expectations
  are identical.
- Canonical shared metadata remains authored from Claude-side inputs. Codex
  artifacts are generated or regenerated from those inputs and are never
  hand-edited. DEV-134 creates neither.
- Real production activation stays `blocked` for both hosts with
  `production_skill_not_implemented`. Structural checks, an alternate model,
  retries, or a fabricated host task cannot establish capability.
- Dependent non-positive and ambiguous completion remains gated on reviewed
  DEV-136 affected-subset evidence and the full 25-case Codex `0.144.5` matrix
  on the combined tip; Claude execution remains deferred. That downstream gate
  did not run here and does not block this design-prototype verification.

## Verification ladder

Run every gate from the repository root. Any failed assertion, changed
governing comment, unsafe evidence, hash drift, or missing prerequisite stops
acceptance; do not weaken a gate.

### 1. Canonical design and compact-contract semantics

```bash
set -e
design_file=docs/superpowers/specs/2026-07-17-dev-134-agent-skill-catalog-design.md
contract_file=docs/architecture/apple-foundation-models-handoff-skill-contract.md

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
  rg -q -F "## $section" "$design_file"
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
  rg -q -F "$token" "$design_file"
done
test "$(rg -c '^### DEV134-POS-00[1-6]:' "$design_file")" -eq 6
test "$(rg -c '^### DEV134-NEG-00[1-6]:' "$design_file")" -eq 6
test "$(rg -c '^### DEV134-AMB-00[1-3]:' "$design_file")" -eq 3

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
  rg -q -F "## $section" "$contract_file"
done
for skill_name in \
  design-apple-foundation-models-handoff \
  implement-apple-foundation-models-handoff \
  review-apple-foundation-models-handoff \
  debug-apple-foundation-models-handoff \
  validate-apple-foundation-models-handoff; do
  test "$(rg -c -F "$skill_name" "$contract_file")" -ge 1
  rg -q -F "$skill_name" "$design_file"
done
for reference_file in \
  architecture-and-state.md \
  orchestration-patterns.md \
  apple-api-availability.md \
  security-context-and-recovery.md \
  evaluation-and-observability.md; do
  test "$(rg -c -F "$reference_file" "$contract_file")" -eq 1
  rg -q -F "$reference_file" "$design_file"
done
for prefix_count in POS:6 NEG:6 AMB:3; do
  prefix_name="${prefix_count%%:*}"
  expected_count="${prefix_count##*:}"
  actual_count="$(rg -o "DEV134-${prefix_name}-[0-9]{3}" \
    "$contract_file" | sort -u | wc -l | tr -d ' ')"
  test "$actual_count" -eq "$expected_count"
done
rg -q -F 'architectureSchemaVersion: "1.0"' "$contract_file"
rg -q -F 'no_activation' "$contract_file"
rg -q -F 'clarification_required' "$contract_file"
rg -q -F 'DEV-142 through DEV-145 cost router' "$contract_file"

PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import re
from pathlib import Path

contract = Path(
    'docs/architecture/apple-foundation-models-handoff-skill-contract.md'
)
design = Path(
    'docs/superpowers/specs/'
    '2026-07-17-dev-134-agent-skill-catalog-design.md'
)
positive = (
    'activationStatus = activated',
    'selectedSkill',
    'preselectionInput = { domain, requestedOperation, artifactState, evidenceState }',
    'architectureResult',
)
no_activation = (
    'activationStatus = no_activation',
    'reasonCode = out_of_domain',
    'domain',
    'requestedOperation',
)
clarification = (
    'activationStatus = clarification_required',
    'clarificationKind = domain | approved_contract',
    'missingInput',
    'question',
)
checks = (
    (contract, '## Common positive result', 0, positive),
    (contract, '## Non-positive activation result', 0, no_activation),
    (contract, '## Non-positive activation result', 1, clarification),
    (design, '### Positive activation envelope', 0, positive),
    (design, '### Non-positive activation results', 0, no_activation),
    (design, '### Non-positive activation results', 1, clarification),
)

for source, heading, block_index, expected_lines in checks:
    text = source.read_text()
    start = text.index(heading)
    level = len(heading) - len(heading.lstrip('#'))
    tail = text[start + len(heading):]
    boundary = re.search(rf'^#{{1,{level}}} ', tail, re.MULTILINE)
    section = tail[:boundary.start()] if boundary else tail
    blocks = re.findall(r'```text\n(.*?)```', section, re.DOTALL)
    actual_lines = tuple(blocks[block_index].strip().splitlines())
    assert actual_lines == expected_lines, (source, heading, block_index)
    assert all('activationOwner' not in line for line in actual_lines)

print(
    'DEV134_EMITTED_ENVELOPE_SHAPE_PASS '
    'positive=2 no_activation=2 clarification=2'
)
PY
```

### 2. Independent hard activation oracle

This oracle owns its expected schema, paths, hashes, values, case matrix,
guardrail assignments, and mutation set. It does not derive expectations from
the JSON or canonical prose.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import copy
import hashlib
import json
from collections import Counter
from pathlib import Path, PurePosixPath

EVIDENCE = Path('docs/research/evidence/dev-134-activation-prototype.json')
data = json.loads(EVIDENCE.read_text())

ARTIFACTS = {
    'designArtifact': (
        'docs/superpowers/specs/'
        '2026-07-17-dev-134-agent-skill-catalog-design.md',
        '07541f46a0de721498e7526723769f6f69be3912c9e7d858097e685a72156ca7',
    ),
    'contractArtifact': (
        'docs/architecture/'
        'apple-foundation-models-handoff-skill-contract.md',
        '0b492a9702fa338bc714d5da182ab92509f3166fc3e8b554f0ca64c06d4ef094',
    ),
}
TOP_KEYS = {
    'schemaVersion', 'evidenceKind', 'sourceIssue', 'designArtifact',
    'designArtifactSha256', 'contractArtifact', 'contractArtifactSha256',
    'executionLayer', 'status', 'realHostRows', 'limitations', 'cases',
}
CASE_KEYS = {
    'id', 'category', 'activationOwner', 'inputClass',
    'requestedOperation', 'artifactState', 'evidenceState',
    'expectedActivation', 'hostExpectations', 'expectedReferences',
    'expectedOutputSections', 'expectedGuardrails', 'fullWalkthrough',
    'resolution',
}
LIMITATIONS = [
    'Design-contract prototype only.',
    'Production skills and concern references are not implemented.',
    'Real Claude and Codex activation remains blocked.',
    ('No live model, PCC, custom provider, credentials, network, hardware, '
     'paid service, or host automation ran.'),
    ('No Apple runtime enforcement, host capability, or release-readiness '
     'claim is made.'),
    ('JSON validity, artifact hashes, and safety scans do not establish '
     'activation capability.'),
]
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
DESIGN_GUARDRAILS = [
    'D-ROUTE-001', 'D-OWNER-001', 'D-TRANSITION-001',
    'D-CONTEXT-001', 'D-CONTEXT-002', 'D-GRANT-001',
    'D-PHASE-001', 'D-FALLBACK-001', 'D-EVIDENCE-001',
    'D-RUBRIC-001',
]
EFFECT_GUARDRAILS = [
    'D-SCHEMA-001', 'D-ROUTE-001', 'D-OWNER-001',
    'D-TRANSITION-001', 'D-TOOL-001', 'D-CONTEXT-001',
    'D-CONTEXT-002', 'D-GRANT-001', 'D-PHASE-001',
    'D-EFFECT-001', 'D-EFFECT-002', 'D-FALLBACK-001',
    'D-EVIDENCE-001', 'D-RUBRIC-001',
]
GUARDRAILS = {
    'full_design': ['D-SCHEMA-001'] + DESIGN_GUARDRAILS,
    'design': DESIGN_GUARDRAILS,
    'review': EFFECT_GUARDRAILS,
    'implement': ['D-SCHEMA-001'] + DESIGN_GUARDRAILS,
    'debug': EFFECT_GUARDRAILS,
    'validate': EFFECT_GUARDRAILS,
    'route': ['D-ROUTE-001'],
    'compound_review': EFFECT_GUARDRAILS[1:],
}
SPECS = [
    ('DEV134-POS-001', 'positive', 'direct_workflow',
     'new_baton_pass_architecture', 'design', 'absent', 'missing',
     'design-apple-foundation-models-handoff', 'all', 'design',
     'full_design', ['D-TOOL-001', 'D-EFFECT-001', 'D-EFFECT-002'], True,
     'baton_pass_destination_owner_selected'),
    ('DEV134-POS-002', 'positive', 'direct_workflow',
     'flawed_reducer_findings_review', 'review', 'implementation', 'failing',
     'review-apple-foundation-models-handoff', 'all', 'review', 'review', [],
     True, 'reject_flawed_reducer_with_findings'),
    ('DEV134-POS-003', 'positive', 'direct_workflow',
     'approved_bounded_contract_change', 'implement', 'approved_contract',
     'available', 'implement-apple-foundation-models-handoff', 'all',
     'implement', 'implement', [], False, 'bounded_approved_contract_change'),
    ('DEV134-POS-004', 'positive', 'direct_workflow',
     'uncertain_effect_recovery_failure', 'debug', 'implementation', 'failing',
     'debug-apple-foundation-models-handoff', 'debug', 'debug', 'debug', [],
     False, 'recovery_required_reconciliation_without_replay'),
    ('DEV134-POS-005', 'positive', 'direct_workflow',
     'proof_only_evidence_matrix', 'validate', 'evidence_bundle', 'available',
     'validate-apple-foundation-models-handoff', 'all', 'validate', 'validate',
     [], False, 'proof_matrix_without_edits'),
    ('DEV134-POS-006', 'positive', 'direct_workflow',
     'isolated_consultation_architecture', 'design', 'absent', 'missing',
     'design-apple-foundation-models-handoff', 'all', 'design', 'design', [],
     False, 'isolated_consultation_parent_owner_selected'),
    ('DEV134-NEG-001', 'negative', 'non_positive_router',
     'app_intents_request', 'unspecified', 'unknown', 'unknown',
     'no_activation', 'none', 'none', 'route', [], False,
     'reject_out_of_domain'),
    ('DEV134-NEG-002', 'negative', 'non_positive_router',
     'apple_handoff_request', 'unspecified', 'unknown', 'unknown',
     'no_activation', 'none', 'none', 'route', [], False,
     'reject_out_of_domain'),
    ('DEV134-NEG-003', 'negative', 'non_positive_router',
     'generic_swift_request', 'unspecified', 'unknown', 'unknown',
     'no_activation', 'none', 'none', 'route', [], False,
     'reject_out_of_domain'),
    ('DEV134-NEG-004', 'negative', 'non_positive_router',
     'generic_foundation_models_education', 'unspecified', 'unknown', 'unknown',
     'no_activation', 'none', 'none', 'route', [], False,
     'reject_out_of_domain'),
    ('DEV134-NEG-005', 'negative', 'non_positive_router',
     'coding_session_handoff_request', 'unspecified', 'unknown', 'unknown',
     'no_activation', 'none', 'none', 'route', [], False,
     'reject_out_of_domain'),
    ('DEV134-NEG-006', 'negative', 'non_positive_router',
     'foundation_models_runtime_skills_request', 'unspecified', 'unknown',
     'unknown', 'no_activation', 'none', 'none', 'route', [], False,
     'reject_out_of_domain'),
    ('DEV134-AMB-001', 'ambiguous', 'non_positive_router',
     'ambiguous_apple_handoff_domain', 'unspecified', 'unknown', 'unknown',
     'clarification_required', 'none', 'none', 'route', [], False,
     'bounded_domain_clarification'),
    ('DEV134-AMB-002', 'ambiguous', 'non_positive_router',
     'implementation_without_approved_contract', 'implement', 'unknown',
     'missing', 'clarification_required', 'none', 'none', 'route', [], False,
     'bounded_contract_clarification'),
    ('DEV134-AMB-003', 'ambiguous', 'direct_workflow',
     'compound_review_and_fix', 'compound_review_fix', 'implementation',
     'failing', 'review-apple-foundation-models-handoff', 'all', 'review',
     'compound_review', [], False, 'documented_default_review_first'),
]

def expected_cases():
    rows = []
    for spec in SPECS:
        (case_id, category, owner, input_class, operation, artifact_state,
         evidence_state, activation, refs, outputs, guards, not_applicable,
         full, resolution) = spec
        rows.append({
            'id': case_id,
            'category': category,
            'activationOwner': owner,
            'inputClass': input_class,
            'requestedOperation': operation,
            'artifactState': artifact_state,
            'evidenceState': evidence_state,
            'expectedActivation': activation,
            'hostExpectations': {'claude': activation, 'codex': activation},
            'expectedReferences': REFERENCES[refs],
            'expectedOutputSections': OUTPUTS[outputs],
            'expectedGuardrails': {
                'applicable': GUARDRAILS[guards],
                'not_applicable': not_applicable,
            },
            'fullWalkthrough': full,
            'resolution': resolution,
        })
    return rows

EXPECTED_CASES = expected_cases()

def check(candidate):
    assert set(candidate) == TOP_KEYS
    assert candidate['schemaVersion'] == '1.0'
    assert candidate['evidenceKind'] == 'design_contract_prototype'
    assert candidate['sourceIssue'] == 'DEV-134'
    assert candidate['executionLayer'] == 'design_contract_prototype'
    assert candidate['status'] == 'pass'
    assert candidate['limitations'] == LIMITATIONS
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

    repository_root = Path.cwd().resolve()
    for key, (expected_file, expected_hash) in ARTIFACTS.items():
        assert candidate[key] == expected_file
        assert candidate[f'{key}Sha256'] == expected_hash
        pure_file = PurePosixPath(expected_file)
        assert not pure_file.is_absolute()
        assert '..' not in pure_file.parts
        assert pure_file.as_posix() == expected_file
        bound_file = Path(expected_file)
        assert not bound_file.is_symlink()
        assert bound_file.is_file()
        assert bound_file.resolve(strict=True).is_relative_to(repository_root)
        assert hashlib.sha256(bound_file.read_bytes()).hexdigest() == expected_hash

    assert candidate['cases'] == EXPECTED_CASES
    assert Counter(row['category'] for row in candidate['cases']) == {
        'positive': 6, 'negative': 6, 'ambiguous': 3,
    }
    assert Counter(row['activationOwner'] for row in candidate['cases']) == {
        'direct_workflow': 7, 'non_positive_router': 8,
    }
    assert sum(row['fullWalkthrough'] for row in candidate['cases']) == 2
    for row in candidate['cases']:
        assert set(row) == CASE_KEYS
        guardrails = row['expectedGuardrails']
        assert set(guardrails) == {'applicable', 'not_applicable'}
        assert not set(guardrails['applicable']) & set(
            guardrails['not_applicable']
        )

check(data)
print(
    'DEV134_ACTIVATION_PROTOTYPE_PASS total=15 positive=6 negative=6 '
    'ambiguous=3 full=2 hosts=blocked oracle=exact'
)

def find_case(candidate, case_id):
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

def add_pos001_effect_ids(candidate):
    guardrails = find_case(candidate, 'DEV134-POS-001')['expectedGuardrails']
    guardrails['applicable'].extend(guardrails['not_applicable'])
    guardrails['not_applicable'] = []

def route_ambiguous_to_effect(candidate):
    row = find_case(candidate, 'DEV134-AMB-001')
    row.update(
        inputClass='uncertain_effect_recovery_failure',
        requestedOperation='debug',
        artifactState='implementation',
        evidenceState='failing',
    )
    row['expectedGuardrails']['applicable'].extend([
        'D-EFFECT-001', 'D-EFFECT-002',
    ])

MUTATIONS = [
    ('positive_routed_through_router', lambda d: find_case(
        d, 'DEV134-POS-001').update(activationOwner='non_positive_router')),
    ('non_positive_bypasses_router', lambda d: find_case(
        d, 'DEV134-NEG-001').update(activationOwner='direct_workflow')),
    ('implementation_absent_contract', lambda d: find_case(
        d, 'DEV134-POS-003').update(
            artifactState='absent', evidenceState='missing')),
    ('unsafe_retry', lambda d: find_case(
        d, 'DEV134-POS-004').update(
            resolution='retry_effect_immediately_without_reconciliation')),
    ('missing_review_guardrails', lambda d: find_case(
        d, 'DEV134-POS-002')['expectedGuardrails']['applicable'].remove(
            'D-GRANT-001')),
    ('missing_validation_refs', lambda d: find_case(
        d, 'DEV134-POS-005')['expectedReferences'].remove('evaluation')),
    ('pos001_effect_ids', add_pos001_effect_ids),
    ('ambiguous_route_to_effect', route_ambiguous_to_effect),
    ('missing_output_section', lambda d: find_case(
        d, 'DEV134-POS-003')['expectedOutputSections'].remove('Changed Paths')),
    ('wrong_file_retarget', lambda d: d.update(designArtifact='README.md')),
    ('absolute_path_retarget', lambda d: d.update(contractArtifact='/etc/hosts')),
    ('traversal_path_retarget', lambda d: d.update(
        designArtifact='docs/../README.md')),
]
for mutation_name, mutation in MUTATIONS:
    assert_rejected(mutation_name, mutation)
print('DEV134_ACTIVATION_MUTATION_PASS rejected=12')
PY
```

Required final lines:

```text
DEV134_ACTIVATION_PROTOTYPE_PASS total=15 positive=6 negative=6 ambiguous=3 full=2 hosts=blocked oracle=exact
DEV134_ACTIVATION_MUTATION_PASS rejected=12
```

### 3. DEV-131 evidence safety

```bash
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import importlib.util
import json
from pathlib import Path

module_file = Path('fixtures/dev-131/proof_runner.py')
module_spec = importlib.util.spec_from_file_location(
    'dev131_proof_runner', module_file
)
module = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(module)
evidence_file = Path(
    'docs/research/evidence/dev-134-activation-prototype.json'
)
text = evidence_file.read_text()
structured = json.loads(text)
assert module._text_is_safe(text)
assert module._structured_content_is_safe(structured)
print('DEV134_EVIDENCE_SAFETY_PASS text=pass structured=pass')
PY
```

### 4. Inherited deterministic regressions

DEV-131 must report 26 passing unit tests, an 11/11 proof matrix, safe evidence
and rubric gates, and `not_applicable` for zero denominator:

```bash
set -e
PYTHONDONTWRITEBYTECODE=1 \
  python3 -m unittest discover -s fixtures/dev-131/tests -p 'test_*.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 fixtures/dev-131/proof_runner.py
dev131_cache="$(mktemp -d)"
PYTHONPYCACHEPREFIX="$dev131_cache" python3 -m compileall -q fixtures/dev-131
```

DEV-130 must report the exact 8/0 golden output twice, byte-identically:

```bash
set -e
dev130_dir="$(mktemp -d)"
swiftc -warnings-as-errors -parse-as-library \
  fixtures/dev-130/HandoffSecurityPolicy.swift \
  fixtures/dev-130/AdversarialScenarios.swift \
  -o "$dev130_dir/dev130"
"$dev130_dir/dev130" > "$dev130_dir/first.out"
diff -u fixtures/dev-130/expected-output.txt "$dev130_dir/first.out"
"$dev130_dir/dev130" > "$dev130_dir/second.out"
cmp "$dev130_dir/first.out" "$dev130_dir/second.out"
rg -q '^SUMMARY passed=8 failed=0$' "$dev130_dir/first.out"
```

DEV-128 must pass the README's six positive SDK 26.5 gates and its two strict,
diagnostic-specific expected blockers:

```bash
set -e
dev128_dir="$(mktemp -d)"
dev128_sdk="$(xcrun --sdk macosx --show-sdk-path)"
dev128_target=arm64-apple-macos26.0
swiftc -warnings-as-errors -typecheck -target "$dev128_target" \
  -sdk "$dev128_sdk" fixtures/dev-128/compiled/stable-surface.swift
swiftc -warnings-as-errors -typecheck -target "$dev128_target" \
  -sdk "$dev128_sdk" fixtures/dev-128/compiled/generable-macro.swift
swiftc -warnings-as-errors -parse-as-library -target "$dev128_target" \
  -sdk "$dev128_sdk" fixtures/dev-128/compiled/availability-probe.swift \
  -o "$dev128_dir/availability"
"$dev128_dir/availability" > "$dev128_dir/availability.out"
rg -q '^availability=' "$dev128_dir/availability.out"
rg -q '^isAvailable=' "$dev128_dir/availability.out"
rg -q '^contextSize=[0-9]+$' "$dev128_dir/availability.out"
rg -q '^supportsCurrentLocale=' "$dev128_dir/availability.out"
swiftc -warnings-as-errors -parse-as-library -target "$dev128_target" \
  -sdk "$dev128_sdk" fixtures/dev-128/compiled/transcript-roundtrip.swift \
  -o "$dev128_dir/transcript"
test "$("$dev128_dir/transcript")" = \
  'entries=3 codableRoundTrip=true rehydrated=true'
swiftc -warnings-as-errors -parse-as-library -target "$dev128_target" \
  -sdk "$dev128_sdk" fixtures/dev-128/compiled/session-isolation.swift \
  -o "$dev128_dir/isolation"
test "$("$dev128_dir/isolation")" = \
  'parentEntries=1 childEntries=1 isolated=true'
swiftc -warnings-as-errors -parse-as-library -target "$dev128_target" \
  -sdk "$dev128_sdk" fixtures/dev-128/compiled/baton-pass-state.swift \
  -o "$dev128_dir/baton"
test "$("$dev128_dir/baton")" = \
  'source=research destination=review active=review finalOwner=review transferred=true'
set +e
swiftc -warnings-as-errors -typecheck -target arm64-apple-macos27.0 \
  -sdk "$dev128_sdk" fixtures/dev-128/blocked/os-27-beta-surface.swift \
  > "$dev128_dir/beta.out" 2>&1
beta_rc=$?
set -e
test "$beta_rc" -ne 0
rg -q "DynamicProfile.*not a member type|has no member 'Profile'" \
  "$dev128_dir/beta.out"
rg -q "extra arguments at positions #1, #2 in call" \
  "$dev128_dir/beta.out"
rg -q "extra argument 'toolCallingMode' in call" "$dev128_dir/beta.out"
set +e
swiftc -warnings-as-errors -typecheck -target arm64-apple-macos27.0 \
  -sdk "$dev128_sdk" fixtures/dev-128/blocked/evaluations-import.swift \
  > "$dev128_dir/evaluations.out" 2>&1
evaluations_rc=$?
set -e
test "$evaluations_rc" -ne 0
rg -q "no such module 'Evaluations'" "$dev128_dir/evaluations.out"
```

### 5. Repository, scope, hash, and hygiene gates

```bash
set -e
base_commit=6134d4f40ab802b9f292e2b631177561f2b5e25d
plan_file=docs/superpowers/plans/2026-07-17-dev-134-agent-skill-catalog.md
design_file=docs/superpowers/specs/2026-07-17-dev-134-agent-skill-catalog-design.md
contract_file=docs/architecture/apple-foundation-models-handoff-skill-contract.md
evidence_file=docs/research/evidence/dev-134-activation-prototype.json

python3 scripts/sync_generated_artifacts.py --check
PYTHONDONTWRITEBYTECODE=1 \
  python3 -m unittest discover -s tests -p 'test_*.py' -v
git merge-base --is-ancestor "$base_commit" HEAD
git diff --check "$base_commit"..HEAD
git diff --check

actual_files="$(mktemp)"
expected_files="$(mktemp)"
git diff --name-only "$base_commit"..HEAD | sort > "$actual_files"
printf '%s\n' \
  "$contract_file" "$evidence_file" "$plan_file" "$design_file" \
  | sort > "$expected_files"
diff -u "$expected_files" "$actual_files"
if ! git diff --quiet; then
  test "$(git diff --name-only)" = "$plan_file"
fi

for artifact_file in \
  "$contract_file" "$evidence_file" "$plan_file" "$design_file"; do
  test -f "$artifact_file"
  test ! -L "$artifact_file"
  artifact_resolved="$(python3 -c \
    'from pathlib import Path; import sys; print(Path(sys.argv[1]).resolve(strict=True))' \
    "$artifact_file")"
  case "$artifact_resolved" in
    "$(pwd -P)"/*) ;;
    *) exit 1 ;;
  esac
  test "$(git ls-files --stage -- "$artifact_file" | awk '{print $1}')" = \
    100644
  test -s "$artifact_file"
  shasum -a 256 "$artifact_file"
done
placeholder_re='T(BD)|TO(DO)|FIX(ME)|fill in detai(ls)|implement lat(er)'
if rg -n -e "$placeholder_re" \
  "$contract_file" "$evidence_file" "$plan_file" "$design_file"; then
  exit 1
fi
mac_private_root='/'"Users/"
linux_private_root='/'"home/"
temporary_root='/'"tmp/"
if rg -n -F \
  -e "$mac_private_root" -e "$linux_private_root" -e "$temporary_root" \
  "$contract_file" "$evidence_file" "$plan_file" "$design_file"; then
  exit 1
fi
test -z "$(find . -type d -name '__pycache__' -print -quit)"
test -z "$(find . -type f -name '*.pyc' -print -quit)"
```

The repository test command must report 23 passing tests. After the focused
plan correction is committed, rerun this gate with a clean worktree; the
branch-level diff remains exactly the four allowed paths.

## Host, propagation, and final evidence boundary

DEV-134 does not run a production host task because the production skills and
references do not exist. Keep these capability rows unchanged regardless of
whether Claude Code `2.1.91` or Codex `0.144.5` is locally present:

```text
E-CLAUDE-ACTIVATE-001 blocked production_skill_not_implemented
E-CODEX-ACTIVATE-001 blocked production_skill_not_implemented
```

An alternate executable/model, retry, Markdown/schema success, plugin
discovery, installation, cache state, or enabled state cannot substitute for a
fresh production capability row.

Immediately before acceptance, reread DEV-134 and DEV-135 through DEV-141.
Stop on any newer governing amendment. Each affected downstream issue requires
a newer issue-specific propagation comment that names the source decision,
rationale, direct-positive versus bounded-non-positive ownership, separate
cost-routing boundary, and that issue's exact impact. Do not relabel deferred
host evidence as passed.

Dependent non-positive and ambiguous completion is not a pass until DEV-136
publishes reviewed affected-subset evidence and the full 25-case Codex `0.144.5`
matrix on the combined tip. Claude execution remains deferred. Do not claim
that matrix ran in DEV-134 or use its absence to fail this design-prototype
verification.

Final evidence records the base and reviewed head, the four paths and SHA-256
values, all four DEV-134 pass lines, 6/6/3 cases with two walkthroughs and
7/8 ownership, DEV-131 26 tests and 11/11 proof, DEV-130 8/0 exact repeat,
DEV-128 six positives and two strict blockers, 23 repository tests, generator
sync, clean privacy/cache/diff results, honest host blockers, and propagation
comment IDs. A focused local commit contains only these bounded corrections. The
main PR-review agent owns final re-verification, exact-leased publication,
merge, Linear evidence, and any status transition allowed by the current
issue-level completion contract.
