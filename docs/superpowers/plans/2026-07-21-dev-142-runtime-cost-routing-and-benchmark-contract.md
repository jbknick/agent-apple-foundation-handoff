# DEV-142 Runtime Cost-Routing and Benchmark Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the deterministic, offline-verifiable DEV-142 policy, schema, corpus, quality, and paired-cost contract without adding the production Swift bridge or either host hook.

**Architecture:** Add one repository-only Python contract module behind closed JSON schemas, then layer exact command parsing and routing, a hash-bound synthetic corpus, and provider-specific paired-cost scoring over it. A deterministic proof runner emits normalized metadata only; repository and plugin documentation inherit the frozen values while the distributable plugin remains runtime-free.

**Tech Stack:** Python 3 standard library, JSON Schema documents, `unittest`, repository fixture conventions, Markdown, Git.

## Global Constraints

- Policy identity is exactly schema `1`, policy `diagnostic-condensation-v1`, action `condense_diagnostic_output`, result type `diagnostic_condensation`.
- Only `PostToolUse` / `Bash` and the exact narrow Swift/Xcode, npm/pnpm, and Python command grammar in the approved spec are eligible.
- Canonical input is 8,192–65,536 UTF-8 bytes; maximum condensation is 4,096 bytes; minimum estimated and realized savings are 4,096 bytes.
- Apple response budget is 1,024 tokens and total request occupancy is at most `floor(contextSize * 0.75)`.
- Only allowlisted C0/C1 `trustedLocal` fields may route; unknown, unclassified, disallowed, or mixed-provenance content declines the whole route.
- Every decline or failure preserves the original host-visible bytes; no code in DEV-142 executes a source command, invokes Apple, calls a provider, or installs a hook.
- The deterministic corpus has exactly 24 eligible fixtures; the required release matrix is 24 fixtures × 2 baseline hosts = 48 pairs and 96 arms.
- Release requires at least 10% median parent-token reduction, zero correctness regressions, zero additional parent turns, and zero blocked required pairs.
- Provider normalizations are exactly `openai-responses-usage-v1` and `anthropic-messages-usage-v1`; missing required usage is `blocked`, never estimated.
- Default validation requires no network, Apple generation, PCC, credential, paid service, device hardware, or full Xcode.
- Do not edit `AGENTS.md`, `.agents/plugins/marketplace.json`, or the plugin-local `.codex-plugin/plugin.json` directly.
- Each implementation task uses a tests-only RED commit followed by a GREEN commit; no DEV-143 runtime path enters this branch.

---

## File Map

- `fixtures/dev-142/runtime_contract.py`: pure deterministic policy, parser, envelope, corpus, quality, and cost functions; never invokes a process or model.
- `schemas/dev-142-request.schema.json`: closed request-envelope schema.
- `schemas/dev-142-result.schema.json`: closed applied/declined/fail result-envelope schema.
- `schemas/dev-142-benchmark.schema.json`: closed corpus and paired-evidence schema.
- `fixtures/dev-142/benchmark-corpus.json`: 24 compact synthetic source definitions and their reviewed expectations/hashes.
- `fixtures/dev-142/proof_runner.py`: offline CLI that validates schemas, corpus, routing matrix, quality, normalization, and release arithmetic.
- `fixtures/dev-142/README.md`: exact commands, evidence meanings, and nonclaims.
- `tests/test_dev_142_contract.py`: focused mutation, boundary, corpus, quality, and cost tests.
- `docs/research/evidence/dev-142-contract-verification.json`: normalized deterministic proof metadata only.
- `docs/architecture/apple-foundation-models-handoff-mvp-decision-record.md`: exact DEV-142 refinements.
- `plugins/apple-foundation-models-handoff/references/orchestration-patterns.md`: exact routing and fallback contract.
- `plugins/apple-foundation-models-handoff/references/security-context-and-recovery.md`: exact field/data/fallback contract.
- `plugins/apple-foundation-models-handoff/references/evaluation-and-observability.md`: exact corpus, normalization, and 48-pair release gate.

---

### Task 1: Closed Schemas and Policy Primitives

**Files:**
- Create: `tests/test_dev_142_contract.py`
- Create: `fixtures/dev-142/runtime_contract.py`
- Create: `schemas/dev-142-request.schema.json`
- Create: `schemas/dev-142-result.schema.json`
- Create: `schemas/dev-142-benchmark.schema.json`

**Interfaces:**
- Consumes: approved DEV-142 design constants and standard-library JSON values.
- Produces: `Policy`, `ContractError`, `load_closed_json(path)`, `validate_request(value)`, `validate_result(value)`, `validate_benchmark(value)`.

- [ ] **Step 1: Add failing closed-schema tests**

Create `tests/test_dev_142_contract.py` with imports through `importlib.util`, exact constant assertions, a canonical request/result/benchmark factory, duplicate-key rejection, non-finite-number rejection, unknown-key rejection, and one independent mutation per required field. The first test must include:

```python
class Dev142PolicySchemaTests(unittest.TestCase):
    def test_policy_identity_and_closed_request_are_exact(self):
        self.assertEqual(contract.Policy.SCHEMA_VERSION, 1)
        self.assertEqual(contract.Policy.POLICY_VERSION, "diagnostic-condensation-v1")
        self.assertEqual(contract.Policy.ACTION, "condense_diagnostic_output")
        self.assertEqual(contract.Policy.RESULT_TYPE, "diagnostic_condensation")
        request = canonical_request()
        self.assertEqual(contract.validate_request(request), request)
        for key in tuple(request):
            mutated = dict(request)
            mutated.pop(key)
            with self.subTest(key=key), self.assertRaises(contract.ContractError):
                contract.validate_request(mutated)
        with self.assertRaises(contract.ContractError):
            contract.validate_request({**request, "unexpected": True})
```

- [ ] **Step 2: Run RED and commit tests only**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_dev_142_contract.Dev142PolicySchemaTests -v
```

Expected: import failure because `fixtures/dev-142/runtime_contract.py` does not exist.

Commit only the test:

```bash
git add tests/test_dev_142_contract.py
git commit -m "test(dev-142): define closed policy envelopes"
```

- [ ] **Step 3: Implement immutable policy and closed validators**

Create the module with frozen constants and validators that reject `bool` where an integer is required, duplicate JSON keys, `NaN`/infinity, unknown keys, missing keys, invalid enums, invalid SHA-256 values, and inconsistent interruption/exit status:

```python
class Policy:
    SCHEMA_VERSION = 1
    POLICY_VERSION = "diagnostic-condensation-v1"
    ACTION = "condense_diagnostic_output"
    RESULT_TYPE = "diagnostic_condensation"
    TOOL_NAME = "Bash"
    EVENT_NAME = "PostToolUse"
    MINIMUM_INPUT_BYTES = 8192
    MAXIMUM_INPUT_BYTES = 65536
    MAXIMUM_CONDENSED_BYTES = 4096
    MINIMUM_ESTIMATED_SAVINGS_BYTES = 4096
    MINIMUM_REALIZED_SAVINGS_BYTES = 4096
    MAXIMUM_APPLE_RESPONSE_TOKENS = 1024
    MAXIMUM_APPLE_CONTEXT_NUMERATOR = 3
    MAXIMUM_APPLE_CONTEXT_DENOMINATOR = 4


class ContractError(ValueError):
    pass


def _closed(value, required):
    if type(value) is not dict or set(value) != set(required):
        raise ContractError("closed schema mismatch")
    return value
```

The exact request keys are `schemaVersion`, `policyVersion`, `callID`, `toolName`, `toolVersion`, `stateVersion`, `action`, `commandClass`, `originalResultType`, `originalResultDigest`, `exitStatus`, `interrupted`, `inputBytes`, `estimatedSavingsBytes`, and `fields`. The result schema is a closed tagged union for `applied`, `declined`, and `fail`; only `applied` carries a condensation.

Create JSON Schema draft 2020-12 documents whose `required`, `additionalProperties: false`, enums, integer bounds, digest patterns, and tagged-result conditions match the Python validator exactly. The benchmark schema closes corpus metadata, case definitions, arm telemetry, pair status, and release summary without embedding raw results.

- [ ] **Step 4: Run focused GREEN and schema syntax checks**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_dev_142_contract.Dev142PolicySchemaTests -v
python3 - <<'PY'
import json
from pathlib import Path
for path in sorted(Path("schemas").glob("dev-142-*.schema.json")):
    json.loads(path.read_text())
    print(path)
PY
```

Expected: all focused tests pass and exactly three schema paths print.

- [ ] **Step 5: Commit GREEN**

```bash
git add fixtures/dev-142/runtime_contract.py schemas/dev-142-*.schema.json
git commit -m "feat(dev-142): add closed runtime contract schemas"
```

---

### Task 2: Exact Command Parser and Deterministic Router

**Files:**
- Modify: `tests/test_dev_142_contract.py`
- Modify: `fixtures/dev-142/runtime_contract.py`

**Interfaces:**
- Consumes: `Policy`, validated request dictionaries, repository root, canonical field list.
- Produces: `parse_command(command, repo_root) -> CommandSelection`, `estimate_savings(input_bytes) -> int`, `fits_apple_budget(...) -> bool`, `route(request, context) -> dict`.

- [ ] **Step 1: Add failing command and routing matrix tests**

Add `Dev142CommandParserTests` with one accepted row for every exact prefix, suffix-boundary tests for every terminal, and rejection rows for absolute executables, wrappers, assignments, multiline input, shell operators, redirections, duplicates, unknown flags, escaping paths, symlink ambiguity, and filesystem drift. Add `Dev142RoutingTests` covering selected/unselected tool, each command class, 8191/8192/65536/65537 bytes, 4095/4096 estimated savings, 75% occupancy boundary, unknown classification, C2/C3, unavailable Apple, and one eligible attempt:

```python
def test_exact_size_and_budget_boundaries(self):
    self.assertEqual(contract.estimate_savings(8192), 4096)
    with self.assertRaises(contract.RouteDeclined) as caught:
        contract.estimate_savings(8191)
    self.assertEqual(caught.exception.reason, "input_below_minimum")
    self.assertTrue(contract.fits_apple_budget(6144, 8192))
    self.assertFalse(contract.fits_apple_budget(6145, 8192))
```

The at-most-once test passes a fake bridge callable that increments a counter and asserts the count is exactly one only for an eligible request and zero for every decline.

- [ ] **Step 2: Run RED and commit tests only**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_dev_142_contract.Dev142CommandParserTests \
  tests.test_dev_142_contract.Dev142RoutingTests -v
git add tests/test_dev_142_contract.py
git commit -m "test(dev-142): define exact routing matrix"
```

Expected: failures for missing parser/router interfaces.

- [ ] **Step 3: Implement the exact parser and gates**

Use `shlex.split(..., posix=True)` only after rejecting NUL, CR/LF, and the shell metacharacter families from the spec. Match a closed tuple table, then validate suffix tokens with command-specific functions. Resolve candidate repository paths using `lstat`, `resolve(strict=False)`, captured root identity, and containment; reject symlinks and post-read identity changes.

Implement exact checked gates:

```python
def estimate_savings(input_bytes):
    _require_int(input_bytes, 0)
    if input_bytes < Policy.MINIMUM_INPUT_BYTES:
        raise RouteDeclined("input_below_minimum")
    if input_bytes > Policy.MAXIMUM_INPUT_BYTES:
        raise RouteDeclined("input_above_maximum")
    estimate = input_bytes - Policy.MAXIMUM_CONDENSED_BYTES
    if estimate < Policy.MINIMUM_ESTIMATED_SAVINGS_BYTES:
        raise RouteDeclined("estimated_savings_below_minimum")
    return estimate


def fits_apple_budget(occupied_tokens, context_size):
    _require_int(occupied_tokens, 0)
    _require_int(context_size, 1)
    return (
        occupied_tokens * Policy.MAXIMUM_APPLE_CONTEXT_DENOMINATOR
        <= context_size * Policy.MAXIMUM_APPLE_CONTEXT_NUMERATOR
    )
```

`route` validates the request, event/tool/action/policy, command, field provenance/classification, byte and context gates, and availability before calling the injected bridge once. It validates response bindings and realized bytes. It returns a closed `declined` or `fail` envelope plus `preserveOriginal: true`; it never stores or returns original bytes in evidence.

- [ ] **Step 4: Run focused GREEN**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_dev_142_contract.Dev142CommandParserTests \
  tests.test_dev_142_contract.Dev142RoutingTests -v
```

Expected: all parser and routing cases pass.

- [ ] **Step 5: Commit GREEN**

```bash
git add fixtures/dev-142/runtime_contract.py
git commit -m "feat(dev-142): implement deterministic cost routing policy"
```

---

### Task 3: Hash-Bound Benchmark Corpus and Quality Oracle

**Files:**
- Modify: `tests/test_dev_142_contract.py`
- Modify: `fixtures/dev-142/runtime_contract.py`
- Create: `fixtures/dev-142/benchmark-corpus.json`

**Interfaces:**
- Consumes: closed benchmark schema and deterministic synthetic case definitions.
- Produces: `render_case(case) -> bytes`, `corpus_digest(corpus) -> str`, `score_condensation(case, result) -> QualityScore`.

- [ ] **Step 1: Add failing corpus and mutation tests**

Add tests requiring exactly 24 unique cases, twelve approved command forms with success/failure representatives, exactly six rows per command class, 8–64 KiB rendered output, reviewed SHA-256 per rendered case, C0/C1 synthetic-only content, all required error/fatal identities, warning counts, Unicode byte/token divergence, and boundary fixtures outside the eligible 24. Add mutations that remove or invent a fatal diagnostic, change exit/interruption, change a path/line/code/test ID, miscount warnings, or exceed 4 KiB:

```python
def test_corpus_is_exact_hash_bound_and_balanced(self):
    corpus = contract.load_closed_json(CORPUS)
    contract.validate_benchmark(corpus)
    self.assertEqual(len(corpus["cases"]), 24)
    self.assertEqual(Counter(row["commandClass"] for row in corpus["cases"]), {
        "test": 6, "build": 6, "typecheck": 6, "lint": 6,
    })
    for row in corpus["cases"]:
        rendered = contract.render_case(row)
        self.assertEqual(hashlib.sha256(rendered).hexdigest(), row["renderedSha256"])
        self.assertGreaterEqual(len(rendered), 8192)
        self.assertLessEqual(len(rendered), 65536)
```

- [ ] **Step 2: Run RED and commit tests only**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_dev_142_contract.Dev142CorpusTests -v
git add tests/test_dev_142_contract.py
git commit -m "test(dev-142): define benchmark corpus oracle"
```

Expected: corpus file and rendering/scoring interfaces are missing.

- [ ] **Step 3: Implement corpus rendering and scoring**

Represent noise compactly as a fixed synthetic line plus repeat count. Render canonical UTF-8 with `\n`, deterministic field order, and no timestamps, random values, absolute paths, secrets, or real user data. Each of the twelve command forms has one success and one failure fixture; fixture expectations store exit/interruption, required fatal/error identities, failed-test IDs, warning totals, and summary facts.

Implement a frozen score:

```python
@dataclass(frozen=True)
class QualityScore:
    passed: bool
    reason_codes: tuple[str, ...]


def score_condensation(case, result):
    reasons = []
    if result["exitStatus"] != case["expected"]["exitStatus"]:
        reasons.append("exit_status_regression")
    if result["interrupted"] != case["expected"]["interrupted"]:
        reasons.append("interruption_regression")
    if _diagnostic_identities(result) != _required_identities(case):
        reasons.append("diagnostic_identity_regression")
    if _invented_facts(case, result):
        reasons.append("invented_fact")
    return QualityScore(not reasons, tuple(sorted(reasons)))
```

Generate and commit reviewed hashes only after rendering all cases twice and proving byte identity.

- [ ] **Step 4: Run focused GREEN and determinism check**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_dev_142_contract.Dev142CorpusTests -v
python3 - <<'PY'
import hashlib, importlib.util, json
from pathlib import Path
path = Path("fixtures/dev-142/runtime_contract.py")
spec = importlib.util.spec_from_file_location("dev142", path)
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
corpus = module.load_closed_json(Path("fixtures/dev-142/benchmark-corpus.json"))
first = [module.render_case(row) for row in corpus["cases"]]
second = [module.render_case(row) for row in corpus["cases"]]
assert first == second
print(hashlib.sha256(b"".join(first)).hexdigest())
PY
```

Expected: focused tests pass and one stable lowercase SHA-256 prints.

- [ ] **Step 5: Commit GREEN**

```bash
git add fixtures/dev-142/runtime_contract.py fixtures/dev-142/benchmark-corpus.json
git commit -m "feat(dev-142): add deterministic diagnostic benchmark corpus"
```

---

### Task 4: Provider Normalization and Release Gate

**Files:**
- Modify: `tests/test_dev_142_contract.py`
- Modify: `fixtures/dev-142/runtime_contract.py`

**Interfaces:**
- Consumes: validated plugin-off/plugin-on telemetry arms and `QualityScore`.
- Produces: `normalize_usage(provider, usage) -> NormalizedUsage`, `score_pair(off, on) -> PairScore`, `release_gate(pairs) -> ReleaseScore`.

- [ ] **Step 1: Add failing provider and release arithmetic tests**

Cover OpenAI subset semantics, Anthropic additive cache semantics, nonnegative integer/type checks, overflow, missing fields, mismatched pair identity, zero denominator, exactly 10% boundary, median for even 48 rows, correctness regression, extra parent turn, blocked pair, missing pair, duplicate pair, extra exploratory pair, and 48-valid-pair success:

```python
def test_openai_subsets_are_not_double_counted(self):
    usage = contract.normalize_usage("openai-responses-usage-v1", {
        "input_tokens": 1000,
        "cached_tokens": 600,
        "output_tokens": 200,
        "reasoning_tokens": 150,
    })
    self.assertEqual(usage.total_parent_model_tokens, 1200)

def test_release_requires_complete_10_0_0_matrix(self):
    pairs = make_48_pairs(off_total=1000, on_total=900)
    score = contract.release_gate(pairs)
    self.assertEqual(score.status, "pass")
    self.assertEqual(score.median_reduction_ppm, 100000)
```

- [ ] **Step 2: Run RED and commit tests only**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_dev_142_contract.Dev142CostTests -v
git add tests/test_dev_142_contract.py
git commit -m "test(dev-142): define provider cost release gate"
```

Expected: missing normalization and release interfaces.

- [ ] **Step 3: Implement exact integer normalization and median**

Use integers only. Represent reductions as signed parts per million to avoid floating-point drift:

```python
def _reduction_ppm(off_total, on_total):
    if type(off_total) is not int or off_total <= 0:
        raise BlockedEvidence("invalid_plugin_off_denominator")
    if type(on_total) is not int or on_total < 0:
        raise BlockedEvidence("invalid_plugin_on_total")
    return ((off_total - on_total) * 1_000_000) // off_total


def _median_ppm(values):
    ordered = sorted(values)
    count = len(ordered)
    if count % 2:
        return ordered[count // 2]
    return (ordered[count // 2 - 1] + ordered[count // 2]) // 2
```

OpenAI total is input plus output; cached and reasoning are required validated subsets. Anthropic total is input plus cache-read plus cache-creation plus output; normalized reasoning is null. `release_gate` requires every expected `(host, caseID)` exactly once, 48 `pass` pairs, no blocked/fail rows, median at least `100000` ppm, zero correctness regression, and zero additional turns.

- [ ] **Step 4: Run focused GREEN**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_dev_142_contract.Dev142CostTests -v
```

Expected: all cost and blocker tests pass.

- [ ] **Step 5: Commit GREEN**

```bash
git add fixtures/dev-142/runtime_contract.py
git commit -m "feat(dev-142): add paired provider cost scoring"
```

---

### Task 5: Offline Proof, Documentation, and Contract Evidence

**Files:**
- Modify: `tests/test_dev_142_contract.py`
- Create: `fixtures/dev-142/proof_runner.py`
- Create: `fixtures/dev-142/README.md`
- Create: `docs/research/evidence/dev-142-contract-verification.json`
- Modify: `docs/architecture/apple-foundation-models-handoff-mvp-decision-record.md`
- Modify: `plugins/apple-foundation-models-handoff/references/orchestration-patterns.md`
- Modify: `plugins/apple-foundation-models-handoff/references/security-context-and-recovery.md`
- Modify: `plugins/apple-foundation-models-handoff/references/evaluation-and-observability.md`

**Interfaces:**
- Consumes: Tasks 1–4 contract APIs, schemas, and corpus.
- Produces: `python3 fixtures/dev-142/proof_runner.py --output <path>` and normalized proof JSON with no raw diagnostic/model content.

- [ ] **Step 1: Add failing end-to-end and documentation tests**

Add tests that run the proof runner twice into temporary files and require byte-identical closed JSON. Require checks for schema count, 24 cases, 48 required pair identities, command classes, boundary matrix, policy constants, corpus aggregate hash, and `status = pass` only for deterministic contract proof. Require explicit nonclaims for Apple invocation, host hook activation, parent-token savings, and live provider evidence. Mutation tests must reject absolute/private paths, raw prompts/results/responses, credentials, `.trace`, `.xcresult`, extra keys, and self-attested model correctness.

- [ ] **Step 2: Run RED and commit tests only**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_dev_142_contract.Dev142ProofTests -v
git add tests/test_dev_142_contract.py
git commit -m "test(dev-142): define deterministic contract proof"
```

Expected: proof runner, evidence, and documentation are absent.

- [ ] **Step 3: Implement proof runner and normalized evidence**

The CLI accepts only optional `--output`. It loads the three schemas and corpus with duplicate-key rejection, runs every parser/routing boundary using injected non-model outcomes, scores all reviewed corpus expectations, exercises both provider formulas and the release boundary, and writes an atomic, sorted, indented JSON document. Its top level is:

```python
evidence = {
    "schemaVersion": 1,
    "issue": "DEV-142",
    "status": "pass",
    "policyVersion": Policy.POLICY_VERSION,
    "action": Policy.ACTION,
    "schemaCount": 3,
    "eligibleCaseCount": 24,
    "requiredPairCount": 48,
    "corpusSha256": corpus_digest(corpus),
    "checks": sorted(checks, key=lambda row: row["id"]),
    "liveClaims": {
        "appleInvocation": "not_applicable",
        "codexHook": "not_applicable",
        "claudeHook": "not_applicable",
        "parentTokenReduction": "blocked/provider_usage_not_executed",
    },
}
```

Write the README commands and update only the relevant paragraphs in the decision record and three references with exact policy values and ownership boundaries. Do not advertise a runtime capability in plugin metadata.

- [ ] **Step 4: Run focused GREEN and regenerate evidence**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_dev_142_contract.Dev142ProofTests -v
python3 fixtures/dev-142/proof_runner.py \
  --output docs/research/evidence/dev-142-contract-verification.json
python3 fixtures/dev-142/proof_runner.py --output /tmp/dev-142-proof.json
cmp docs/research/evidence/dev-142-contract-verification.json /tmp/dev-142-proof.json
```

Expected: focused tests pass and evidence bytes match.

- [ ] **Step 5: Run the complete repository gate**

```bash
python3 scripts/sync_generated_artifacts.py --check
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py' -v
bats tests/plugin_skeleton.bats
git diff --check
git status --short
```

Expected: generator synchronized; all repository tests pass with only the existing opt-in external-link skip; Bats 3/3; no whitespace error; only intended tracked changes remain.

- [ ] **Step 6: Commit GREEN**

```bash
git add \
  fixtures/dev-142/proof_runner.py \
  fixtures/dev-142/README.md \
  docs/research/evidence/dev-142-contract-verification.json \
  docs/architecture/apple-foundation-models-handoff-mvp-decision-record.md \
  plugins/apple-foundation-models-handoff/references/orchestration-patterns.md \
  plugins/apple-foundation-models-handoff/references/security-context-and-recovery.md \
  plugins/apple-foundation-models-handoff/references/evaluation-and-observability.md
git commit -m "docs(dev-142): publish verified routing contract"
```

---

## Final Issue Gate

- [ ] Run the self-review checklist: map every approved design section to a task, search the plan and implementation for placeholders, and confirm type/signature consistency.
- [ ] Run `python3 scripts/sync_generated_artifacts.py --check`, the complete Python suite, Bats, the proof runner twice with `cmp`, `git diff --check`, and clean-status checks.
- [ ] Generate an independent whole-branch review package from the branch merge base and obtain clean spec-compliance and code-quality verdicts.
- [ ] Push one DEV-142 branch, open one atomic PR, wait for CI, attach normalized proof to Linear, and merge only after all required checks and review are green.
- [ ] Verify merged `main` with the same complete gate before starting DEV-143.
