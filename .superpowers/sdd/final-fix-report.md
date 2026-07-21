# DEV-142 final-fix report

Date: 2026-07-21

Status: complete.

Frozen implementation tuple:
`foundation_models_handoff / implement / approved_architecture / review_findings_available`.

## Commits

- RED: `992362a80200c2b5a25c4c446b2c35aba9b8dcf7` — `test(dev-142): reproduce final review findings`
- GREEN: `7189fcfc1fdba0afa87640c85b46bab37f318e10` — `fix(dev-142): close runtime and benchmark contracts`
- GREEN: `8a321891ecc6dc746fe9fd4840ce5c312dd6d9e3` — `fix(dev-142): harden offline proof evidence`
- GREEN: `3637625da473290dbd451841fa98206251136d92` — `fix(dev-142): exercise result schema semantics`
- RED: `bce9d3d464dc58252dabea6ed16a4fbe29dc8369` — `test(dev-142): reproduce audit exploit variants`
- GREEN: `9b9dac6ee192de56443c4615b674cdda6a65f90e` — `fix(dev-142): close adversarial audit gaps`
- REPORT: `d27723c1dbc101601333d3b16f3d1191f02316e7` — `docs(dev-142): record final fix verification`
- RED: `bc906bf58026fd68914d76819395097e62f38498` — `test(dev-142): reproduce missing operand drift`
- GREEN: `62dcc69b2d0e99de8699ea1677932ed6f761e6f8` — `fix(dev-142): recheck missing operand state`

The tests-only RED commit reproduced all seven binding findings. The full
DEV-142 module at that commit ran 59 tests and failed as intended, with 43
failures and 25 errors across tests and subtests. No implementation, fixture,
schema, evidence, or documentation change was included in that commit.

An independent adversarial review then identified additional fail-open variants.
The tests-only audit RED ended with five focused audit tests producing nine
failures and five errors. The second GREEN closes those variants without adding
runtime execution or weakening the original contracts.

The final independent re-review isolated `DEV142-PATH-002`: an operand that was
absent before the bridge could be created during the bridge because only its
existing ancestor snapshot survived parsing. The tests-only RED observed an
incorrect applied result. The final GREEN retains both the existing snapshot
and missing-path tuple for every operand and rechecks both after the bridge,
normalizing drift to `fail / invalid_response / preserveOriginal`.

## Finding-to-fix self-review

| Finding | Closed contract and proof |
| --- | --- |
| `DEV142-SEC-001` | Canonical UTF-8 field encoding is recomputed before routing; recursive field-value safety rejects secret, credential, and private-path families before any bridge attempt; declared bytes and estimated savings must match. |
| `DEV142-RESP-001` | The route freezes JSON-isolated request bindings and source facts, gives the bridge a deep copy, validates bindings for all three outcomes, and applies only an exact deterministic semantic match with contained regular POSIX paths. |
| `DEV142-COST-001` | The serialized evidence contract contains exactly 96 canonical role-bound arms and 48 corpus/hash/class-bound pairs. Provider components, counters, pair scores, and release aggregates are validated or derived; missing telemetry blocks. |
| `DEV142-PATH-001` | Repository root, full ancestor chain, nearest existing parent, and existing target identities are captured and rechecked. Filesystem errors, disappearance, replacement, and drift normalize to fail-closed route outcomes. |
| `DEV142-PATH-002` | Each command operand carries its existing identity snapshot and its missing-path tuple through the immutable route state. Both are rechecked after the bridge and before application, so creation of a previously absent target fails closed with the original output preserved. |
| `DEV142-QUALITY-001` | The corpus independently stores and hashes warning representatives, summary facts, next action, completion facts, and success/failure outcomes. The scorer reports omission and invention independently; interruption is boundary-only. |
| `DEV142-EVIDENCE-001` | The proof semantically evaluates all three schemas and their exact custom vocabulary, including exact warning accounting; exact-enums every evidence check/boundary; recursively rejects prohibited keys and values; and regenerates metadata-only evidence. |
| `DEV142-PARSER-001` | Shell operators are rejected quote-aware before POSIX tokenization; quoted balanced pytest expressions pass; Swift-format, mypy, and Ruff optional flags follow the approved fixed order. |

## Adversarial audit closure

- Sensitive-data validation covers generic absolute POSIX, Windows-drive, UNC,
  file-URI, provider-token, credential-label, and private-key families in both
  runtime metadata and proof artifacts.
- Command operands reject option-like path values. All operand, field, source,
  root, ancestor, parent, target, and captured-absence identities, including
  initially absent operand tuples, survive the bridge boundary and are
  rechecked before application.
- Missing budget inputs decline deterministically. Route counters are bounded,
  mutually coherent, and included in direct scoring; plugin-off telemetry is
  exactly zero or null as applicable.
- Boundary fixtures now exercise the exact 4,096/4,097 output and
  8,191/8,192/65,536/65,537 input boundaries with arithmetically derived byte
  savings.
- Quality scoring verifies the rendered-case hash before evaluation and returns
  a failed score, rather than raising, for malformed condensation shapes or
  unhashable fact arrays.
- The proof demonstrates that its metadata safety scanner owns rejection of
  the prohibited mutation set instead of relying on closed-schema rejection.

## Commands and outputs

Focused DEV-142 contract:

```text
$ PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_dev_142_contract -v
Ran 66 tests in 2.438s
OK
```

Proof and semantic-schema gates after the final proof refinement:

```text
$ PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
    tests.test_dev_142_contract.Dev142ProofTests \
    tests.test_dev_142_contract.Dev142SchemaParityTests -v
Ran 11 tests in 3.074s
OK
```

Full repository suite on the final implementation HEAD:

```text
$ PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py' -v
Ran 402 tests in 60.278s
OK (skipped=1)
```

Generated artifacts and Bats:

```text
$ python3 scripts/sync_generated_artifacts.py --check
generated artifacts are synchronized

$ bats tests/plugin_skeleton.bats
1..3
ok 1 tracked generated artifacts are synchronized
ok 2 write mode is idempotent for all generated artifacts
ok 3 check mode rejects generated Codex manifest drift
```

Deterministic proof:

```text
$ python3 fixtures/dev-142/proof_runner.py --output <temp>/first.json
$ python3 fixtures/dev-142/proof_runner.py --output <temp>/second.json
$ cmp <temp>/first.json <temp>/second.json
$ cmp docs/research/evidence/dev-142-contract-verification.json <temp>/first.json
$ shasum -a 256 <temp>/first.json <temp>/second.json \
    docs/research/evidence/dev-142-contract-verification.json
8b35b3b3a32ac1a1b958c8f918734ae6af83d1271c4c2dd6e5fd03a509dbfc8b  <temp>/first.json
8b35b3b3a32ac1a1b958c8f918734ae6af83d1271c4c2dd6e5fd03a509dbfc8b  <temp>/second.json
8b35b3b3a32ac1a1b958c8f918734ae6af83d1271c4c2dd6e5fd03a509dbfc8b  docs/research/evidence/dev-142-contract-verification.json
```

Privacy, classification, and hash checks:

```text
$ PYTHONDONTWRITEBYTECODE=1 python3 <inline DEV-142 evidence validator>
privacy scan: pass
classification/hash scan: pass
```

Diff, placeholder, and pre-report clean-tree checks:

```text
$ git diff --check
[no output]
$ rg <TODO/FIXME/XXX/TBD/NotImplementedError pattern> <DEV-142 owned files>
[no matches]
$ git status --short
[no output]
```

## Scope and completion review

- The approved spec, policy identity, byte/token bounds, exact action, and
  contract-only ownership remain unchanged.
- The change adds no production hook, Apple bridge, model invocation, process
  execution, network access, dependency, credential, or live telemetry.
- The 24-case corpus remains synthetic and hash-bound; all 12 approved command
  forms contain one numeric success and one numeric non-interrupted failure.
- Only the Task 5 consistency paragraphs were changed in the decision record,
  proof README, evaluation reference, and security reference. Plugin metadata
  does not advertise a runtime capability.
- Placeholder search was empty, validator/schema signatures agree through the
  full 402-test suite, generated artifacts are synchronized, and the proof is
  byte-identical across both fresh runs and the committed evidence.
- Live Apple and host claims remain `not_applicable`. Parent-token reduction
  remains `blocked/provider_usage_not_executed`; structural/offline proof is
  not relabelled as capability or savings evidence.

Concern: none for the deterministic DEV-142 contract. Live Apple, host-hook,
and paired provider-cost evidence remain deliberately outside this issue and
blocked or not applicable as recorded above.
