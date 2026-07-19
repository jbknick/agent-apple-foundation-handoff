# DEV-131 Evaluation Strategy Implementation Plan

**Goal:** Define and prove a deterministic, offline-first evaluation contract for Foundation Models handoff architectures while keeping rubric assessment, paired plugin-off/plugin-on runtime cost, and Apple host tooling as explicit, separately evidenced layers.

**Architecture:** A standard-library Python proof runner consumes independent fixture inputs and emits stable check identifiers. It validates deterministic handoff invariants, a human-reviewable rubric record, and a redacted evidence-bundle allowlist. A research report maps those executable checks to cross-host acceptance and current Apple Evaluations/Instruments capabilities without turning the research proof into the production harness reserved for DEV-139.

**Tech Stack:** Python 3 standard library, `unittest`, JSON/JSONL, Markdown, shell-based host probes, Swift compiler probes against the installed Apple SDK.

**Issue and integration constraints:**

- Linear issue: DEV-131.
- Maintain one atomic 28-path DEV-131 delta against current `main`.
- Canonical design: `docs/superpowers/specs/2026-07-17-dev-131-evaluation-strategy-design.md`.
- Do not add production skills, agents, hooks, commands, MCP servers, packages, or network dependencies.
- Do not edit generated Codex artifacts.
- Default tests must not need a model, network, credentials, paid services, Apple Foundation Models availability, or full Xcode.
- Missing host binaries, SDK modules, model availability, automation, or hardware must be reported as `blocked`, never converted into a pass.
- Apple Evaluations and Instruments are an optional Xcode 27 host-evidence layer, not app-owned authorization, orchestration, policy, or recovery semantics.
- The sequential executor owns exactly three main-agent review/fix rounds,
  exact-lease publication, a current Linear/GitHub reread, head-locked squash
  merge, reviewed-tree equality, and merged-result smoke verification. Round 1
  does not claim those later integration steps are complete.

**July 18 runtime-cost amendment:**

- Pair eligible plugin-off/plugin-on workflows with identical stimulus, parent
  model/provider, toolchain, policy, and correctness oracle.
- Preserve provider-reported input, cached-input, output, and reasoning tokens
  when exposed; use a versioned provider normalization for total parent-model
  tokens.
- Keep the exact metric set in separate `pluginOff` and `pluginOn` arms and
  bind the provider normalization version in the comparison record.
- Also capture parent turns, Apple attempts, replacement ratio, declines,
  fallback rate, latency, and correctness.
- Release requires at least 10% median total parent-model token reduction, zero
  correctness regressions, and zero extra parent-model turns.
- Missing provider telemetry/normalization or live Apple prerequisites is
  `blocked`; discovery, activation, byte counts, compile checks, and DEV-138
  mocks cannot satisfy a runtime-cost row.
- DEV-142 owns usage capture/normalization, DEV-143 paired runtime/routing
  measurements, DEV-144 correctness/eligibility, and DEV-145 aggregation and
  release-floor enforcement.

**Current host snapshot (2026-07-19):** macOS 26.5.1 (25F80), Xcode 26.6
(17F113) at `/Applications/Xcode.app/Contents/Developer`, Swift 6.3.3/driver
1.148.6, macOS and iPhoneOS SDK 26.5, xctrace 16.0, simctl, two booted
simulators, Claude Code 2.1.140, and Codex CLI 0.144.5. Xcode/SDK 27,
`Evaluations`, legacy `Instruments`, and live provider/runtime-cost evidence
remain blocked.

---

### Task 1: Add the executable offline evaluation proof

**Files:**

- Create: `fixtures/dev-131/README.md`
- Create: `fixtures/dev-131/index.json`
- Create: `fixtures/dev-131/proof_runner.py`
- Create: `fixtures/dev-131/tests/test_proof_runner.py`
- Create: `fixtures/dev-131/cases/valid/happy-path.json`
- Create: `fixtures/dev-131/cases/valid/replayed-effect.json`
- Create: `fixtures/dev-131/cases/invalid/transition-loop.json`
- Create: `fixtures/dev-131/cases/invalid/wrong-final-owner.json`
- Create: `fixtures/dev-131/cases/invalid/missing-context-policy.json`
- Create: `fixtures/dev-131/cases/invalid/unauthorized-tool.json`
- Create: `fixtures/dev-131/cases/invalid/stale-grant.json`
- Create: `fixtures/dev-131/cases/invalid/invalid-phase.json`
- Create: `fixtures/dev-131/cases/invalid/retry-before-reconciliation.json`
- Create: `fixtures/dev-131/cases/invalid/unsafe-evidence-manifest.json`
- Create: `fixtures/dev-131/example-evidence/summary.md`
- Create: `fixtures/dev-131/example-evidence/checks.json`
- Create: `fixtures/dev-131/example-evidence/commands.jsonl`
- Create: `fixtures/dev-131/example-evidence/environment.json`
- Create: `fixtures/dev-131/example-evidence/host-matrix.json`
- Create: `fixtures/dev-131/example-evidence/rubric/architecture-response.synthetic.md`
- Create: `fixtures/dev-131/example-evidence/rubric/assessment.json`
- Create: `fixtures/dev-131/example-evidence/rubric/assessment.invalid.json`
- Create: `fixtures/dev-131/example-evidence/manifest.json`

**Step 1: Write failing contract tests**

Add `unittest` coverage that imports functions not yet implemented and asserts:

- every case result includes only stable documented check IDs;
- valid cases pass and every invalid case fails with the exact violation ID declared in the independent `index.json` oracle;
- the validator cannot receive expected outcomes from a case fixture;
- the two synthetic workflow identities are represented across the valid cases;
- `stateVersion` and `policyVersion` are checked independently;
- reducer phase, replay, and retry-only-after-`confirmed_absent`
  reconciliation invariants match DEV-130 decisions;
- nested case schemas reject undeclared/oracle/raw fields, context inclusion is
  the exact declared minimum, and evidence paths are allowlisted;
- semantic quality is accepted only through the seven-dimension rubric record and is never inferred from deterministic structural checks;
- a valid example evidence bundle passes its strict allowlist and SHA-256 checks;
- an unsafe manifest and an invalid critical rubric score are rejected;
- zero-denominator metrics serialize as `not_applicable`, never as a fabricated zero-percent pass.

Run the test before implementing the runner:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s fixtures/dev-131/tests -p 'test_*.py' -v
```

Expected: FAIL because `fixtures/dev-131/proof_runner.py` or the named API is missing.

**Step 2: Implement the smallest deterministic validator**

Implement standard-library-only functions with explicit data-in/data-out boundaries:

```python
def evaluate_case(case: dict) -> dict: ...
def validate_rubric(response_path: Path, assessment: dict) -> dict: ...
def validate_evidence_bundle(bundle_root: Path) -> dict: ...
def run(fixtures_root: Path) -> dict: ...
```

The runner must implement the documented check families:

- `D-SCHEMA-001`
- `D-ROUTE-001`
- `D-OWNER-001`
- `D-TRANSITION-001`
- `D-TOOL-001`
- `D-CONTEXT-001` and `D-CONTEXT-002`
- `D-GRANT-001`
- `D-PHASE-001`
- `D-EFFECT-001` and `D-EFFECT-002`
- `D-FALLBACK-001`
- `D-EVIDENCE-001`
- `D-RUBRIC-001`

Keep the expected result outside each input fixture. The runner may read `index.json` only to select cases and compare observed results after validation; `evaluate_case` must not accept or inspect an expected result.

**Step 3: Add minimal positive and negative fixtures**

Model two synthetic workflow identities without copying any production skill content:

- `minimal-route-owner`: valid routing, context, owner, and tool boundary proof;
- `recovery-aware-effect`: valid at-most-once ledger replay and recovery-before-retry proof.

Add one narrowly scoped invalid fixture for each required rejection: transition loop, wrong final owner, missing context policy, unauthorized tool, stale grant version, invalid reducer phase, retry before reconciliation, and unsafe evidence manifest. Each negative fixture must have one intended exact violation ID so regressions remain attributable.

**Step 4: Add a safe example evidence bundle**

Use only synthetic or normalized/redacted content. The manifest allowlist may reference summary, stable check results, normalized command records, environment capability facts, host matrix results, the rubric stimulus, and rubric assessments. Store SHA-256 values for included files. Exclude raw prompts/responses, hidden reasoning, user data, secrets, machine-specific configuration, generated source, model judge reasoning, and raw Instruments traces.

Rubric dimensions use a four-point scale and include:

1. pattern selection;
2. Apple API grounding and version labeling;
3. security-policy completeness;
4. context minimization;
5. failure and recovery behavior;
6. testability and observability; and
7. limitation honesty.

The valid assessment requires a mean score of at least `3.0` and scores of at least `3` for security-policy completeness, failure and recovery behavior, and limitation honesty. A deliberately invalid assessment proves the critical-dimension gate. These names and critical gates intentionally match the approved canonical design; later reports must not substitute a competing dimension set.

**Step 5: Run focused verification**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s fixtures/dev-131/tests -p 'test_*.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 fixtures/dev-131/proof_runner.py
git diff --check
```

Expected: all tests pass; the CLI emits JSON with overall `pass`, exact negative rejection IDs, rubric status, evidence status, `not_applicable` zero-denominator metrics, and an honestly `blocked`/null runtime-cost record.

**Step 6: Self-review and commit**

Review for test weakening, validator/oracle coupling, unsafe evidence, undocumented IDs, accidental Apple-framework claims, and paths outside the task list. Commit only the Task 1 files:

```bash
git add fixtures/dev-131
git commit -m "test(DEV-131): add offline evaluation proof"
```

Record the commit SHA and verification output in the SDD progress ledger.

---

### Task 2: Document the evaluation matrix and host evidence

**Files:**

- Create: `docs/research/evidence/dev-131-evaluation-command-transcript.md`
- Create: `docs/research/dev-131-evaluation-strategy.md`

**Step 1: Write failing document-contract checks**

Before creating the report, run:

```bash
test -f docs/research/dev-131-evaluation-strategy.md
test -f docs/research/evidence/dev-131-evaluation-command-transcript.md
```

Expected: FAIL because neither artifact exists.

**Step 2: Capture reproducible local evidence**

Run and record exact commands, exit codes, timestamps, and summarized outputs for:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s fixtures/dev-131/tests -p 'test_*.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 fixtures/dev-131/proof_runner.py
swift --version
xcrun --show-sdk-version
printf 'import FoundationModels\n' >/tmp/dev-131-foundation-models.swift
xcrun swiftc -typecheck /tmp/dev-131-foundation-models.swift
printf 'import Evaluations\n' >/tmp/dev-131-evaluations.swift
xcrun swiftc -typecheck /tmp/dev-131-evaluations.swift
xcode-select -p
xcodebuild -version
xcrun --find instruments
xcrun --find xctrace
claude --version
codex --version
```

Record unavailable tools/modules as `blocked` with their actual command result. Do not edit output to imply a full-Xcode, Xcode 27, Apple Intelligence, device, simulator, or runtime-model validation that did not run.

**Step 3: Write the evaluation strategy report**

The report must include:

- decision summary and explicit non-goals;
- a matrix covering loading/discovery, activation, architecture, runtime behavior, security/privacy, cross-host structure, cross-host capability, rubric assessment, and Apple host tooling;
- for every row: owner layer, stable check/evidence ID, dataset, metric or invariant, pass rule, blocked rule, and evidence output;
- the deterministic versus nondeterministic separation, including zero-denominator behavior;
- dataset catalog and two synthetic workflow identities;
- the seven-dimension rubric, threshold, critical gates, reviewer/model-judge boundary, and hashed stimulus requirement;
- cross-host structural checks versus real-host acceptance, with Claude Code and Codex host matrix states;
- Apple Evaluations/Xcode 27 mapping for quantitative metrics, qualitative evaluators, typed datasets, trajectory/tool-call expectations, and model-judge dimensions;
- Apple Instruments mapping for time to first token, tokens per second, total latency, session/request/inference/tool hierarchy, and the privacy reason raw traces are excluded;
- a full-Xcode/current-OS prerequisite and an explicit SDK/tool blocker record for this checkout;
- evidence-bundle schema, allowlist, exclusions, retention/redaction guidance, and reproducibility commands;
- propagation impact for DEV-132, DEV-134, DEV-138, DEV-139, and DEV-141;
- official Apple primary-source links and retrieval date.

Use current Apple primary sources only for Apple API/tool claims:

- `https://developer.apple.com/videos/play/wwdc2026/298/`
- `https://developer.apple.com/videos/play/wwdc2026/299/`
- `https://developer.apple.com/videos/play/wwdc2026/243/`
- `https://developer.apple.com/support/xcode/`

Avoid naming exact public Swift identifiers that cannot be confirmed from the installed SDK or official source text. Clearly label mappings inferred from WWDC demonstrations.

**Step 4: Run report and transcript checks**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 fixtures/dev-131/proof_runner.py \
  >/tmp/dev-131-proof.json
python3 -m json.tool /tmp/dev-131-proof.json >/dev/null
rg -n '^## (Decision summary|Evaluation matrix|Dataset catalog|Rubric contract|Cross-host acceptance|Apple Evaluations mapping|Apple Instruments mapping|Evidence bundle|Local validation|Decision propagation|Primary sources)$' docs/research/dev-131-evaluation-strategy.md
rg -n 'blocked|not_applicable|stateVersion|policyVersion|reconciliation|synthetic|SHA-256|Xcode 27' docs/research/dev-131-evaluation-strategy.md
rg -n 'raw prompt|raw response|hidden reasoning|raw Instruments trace' docs/research/dev-131-evaluation-strategy.md
rg -n 'exit code|Swift|SDK|Evaluations|instruments|xctrace|Claude|Codex' docs/research/evidence/dev-131-evaluation-command-transcript.md
git diff --check
```

Expected: every required section and contract term is present; proof JSON parses; transcript includes real blocked outcomes.

**Step 5: Review against the issue and commit**

Check every DEV-131 Definition of Done item against a named report section and executable or captured evidence. Ensure no host blocker is presented as success and no production harness work has leaked into this issue. Commit only the report and transcript:

```bash
git add docs/research/dev-131-evaluation-strategy.md docs/research/evidence/dev-131-evaluation-command-transcript.md
git commit -m "docs(DEV-131): define evaluation and evidence requirements"
```

Record the commit SHA and review result in the SDD progress ledger.

---

### Task 3: Final verification and Linear evidence handoff

**Files:**

- Modify only ignored coordination artifacts under `.superpowers/sdd/` as needed; do not add another tracked repository artifact unless a failing requirement proves it necessary.

**Step 1: Run the complete repository-local verification from a fresh detached checkout**

Use a temporary detached worktree at the DEV-131 head and run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s fixtures/dev-131/tests -p 'test_*.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 fixtures/dev-131/proof_runner.py
git diff --check
```

Also rerun the host probes from Task 2 in the primary DEV-131 worktree and compare the results with the transcript. Any missing prerequisite remains a blocker for that host-only layer, not for the deterministic offline proof.

**Step 2: Run scope and safety checks**

```bash
git diff --name-only origin/main...HEAD
git log --oneline --decorate origin/main..HEAD
git status --short
rg -n 'TBD|TODO|FIXME|fill in details|implement later' docs/superpowers/specs/2026-07-17-dev-131-evaluation-strategy-design.md docs/superpowers/plans/2026-07-17-dev-131-evaluation-strategy.md docs/research/dev-131-evaluation-strategy.md fixtures/dev-131
rg -n '(api[_-]?key|access[_-]?token|password|secret|BEGIN (RSA|OPENSSH|EC) PRIVATE KEY)' fixtures/dev-131 docs/research/evidence/dev-131-evaluation-command-transcript.md
```

Expected: only DEV-131 paths are present; the tree is clean; no placeholder or credential material exists. Literal prohibited-field names in documentation are acceptable only when they describe exclusions, never as stored evidence fields.

**Step 3: Obtain final code review**

The main agent runs exactly three review/fix rounds over `origin/main...HEAD`:
correctness/scope, simplicity, and adversarial acceptance. A fresh worker owns
each round's bounded corrections. Resolve every actionable finding before the
head-locked merge gate.

**Step 4: Attach evidence and update Linear**

Attach or link the evaluation report and command transcript in DEV-131. Add a comment with:

- reviewed head and squash commit/tree identities;
- exact offline verification commands and results;
- real host-probe states, including blockers;
- review result and evidence artifact paths;
- downstream decisions propagated to DEV-132, DEV-134, DEV-138, DEV-139,
  DEV-141, and runtime-evidence owners DEV-142 through DEV-145; and
- honest blocked state for unavailable runtime/host prerequisites.

Post only Definition-of-Done-required Linear evidence. Status changes belong to
the sequential executor after the current issue-level completion contract is
satisfied.
