# DEV-254 Production Runtime V1 Direct Consultation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the exact passing DEV-253 boundary into the smallest production Codex plugin path for `diagnostic-condensation-v1`.

**Architecture:** Preserve DEV-142 as the policy authority and generate its runtime module into the plugin payload. A Codex-only trusted `PostToolUse` hook invokes one Python adapter, which validates the request, calls one staged Swift Foundation Models executable, validates the result, and emits `continue:false` only for a complete applied result; every decline or failure emits nothing.

**Tech Stack:** Python 3 standard library and `unittest`; Codex CLI `0.145.0`; generated Codex plugin metadata; Swift 6.3.3; macOS SDK 26.5 `FoundationModels`; JSON and SHA-256.

**Linear issue:** [DEV-254](https://linear.app/devprentice/issue/DEV-254/i10-implement-production-runtime-v1-direct-diagnostic-consultation)

**Spec source:** `docs/superpowers/specs/2026-07-26-runtime-v1-successor-linear-backlog-design.md`

**Blocked by:** DEV-253.

---

## Predecessor assumptions and mandatory refresh

This plan is executable only after DEV-253 is `pass`, merged, complete in Linear, and locally synchronized. Before changing code, confirm that its normalized evidence proves:

```text
codexVersion = 0.145.0
directToolMode = true
codeModeEnabled = false
originalAbsentFromNextRequest = true
replacementPresentInNextRequest = true
spooled = false
commandExecutions = 1
additionalParentModelTurns = 0
appleAttempts = 1
appleValidResults = 1
cleanupStatus = complete
```

The plan assumes the passing row also proves that the trusted hook inherits the four explicit runtime variables used by the staged plugin: `RUNTIME_V1_PYTHON`, `RUNTIME_V1_BRIDGE_EXECUTABLE`, `RUNTIME_V1_REPO_ROOT`, and `RUNTIME_V1_PLUGIN_ROOT`. If any assertion or variable contract differs, stop before implementation and request a Sol/High plan refresh. Do not adapt around a failed or blocked predecessor.

## File structure

- Modify `CLAUDE.md` — declare the Codex-only runtime component and generated contract path.
- Modify `plugins/apple-foundation-models-handoff/metadata/codex-interface.json` — add the canonical Codex hook component path.
- Modify `scripts/sync_generated_artifacts.py` — render the top-level Codex `hooks` field and an exact generated copy of the DEV-142 runtime contract.
- Modify `tests/test_generated_artifacts.py` — prove closed metadata, generation parity, drift, and unsafe-output behavior for both new generated outputs.
- Create `plugins/apple-foundation-models-handoff/hooks/codex/hooks.json` — one production `PostToolUse`/`Bash` handler.
- Create `plugins/apple-foundation-models-handoff/hooks/codex/diagnostic_condensation.py` — production eligibility, one bridge call, validation, observation, and no-output fallback.
- Create `plugins/apple-foundation-models-handoff/runtime/DiagnosticCondenser.swift` — one fresh local structured response with no tools.
- Generate `plugins/apple-foundation-models-handoff/runtime/runtime_contract.py` — byte-identical DEV-142 contract payload.
- Modify `plugins/apple-foundation-models-handoff/.codex-plugin/plugin.json` through the generator only.
- Create `tests/test_runtime_v1_production.py` — deterministic production adapter, bridge, metadata, and safety tests.
- Create `tests/e2e/codex_runtime_v1_production.py` — isolated staging, compile, install, trust, direct success, and fallback proof.
- Create `docs/runtime-v1-installation.md` — bounded staging, environment, trust, direct-mode, and uninstall instructions.

No package manager, dependency, MCP server, provider abstraction, transcript store, retry layer, or persistent runtime state is added.

### Task 1: Refresh and freeze the DEV-253 boundary

**Files:**
- Read: `docs/research/evidence/runtime-v1-capability-gate.json`
- Read: `docs/research/runtime-v1-capability-gate.md`
- Read: `fixtures/runtime-v1-capability/synthetic-plugin/hooks/codex/probe.py`
- Read: `fixtures/runtime-v1-capability/synthetic-plugin/runtime/DiagnosticCondenser.swift`
- Modify only if the verified interface changed: `docs/superpowers/plans/2026-07-26-dev-254-production-runtime-v1-direct-consultation.md`

- [ ] **Step 1: Verify the predecessor state**

Run:

```bash
git status --short --branch
git merge-base --is-ancestor origin/main HEAD
python3 -m json.tool docs/research/evidence/runtime-v1-capability-gate.json >/dev/null
```

Expected: clean issue branch from the merged baseline and valid normalized evidence.

- [ ] **Step 2: Check the exact pass assertions**

Run:

```bash
python3 - <<'PY'
import json
from pathlib import Path

value = json.loads(Path("docs/research/evidence/runtime-v1-capability-gate.json").read_text())
assert value["status"] == "pass"
assert value["reason"] == "capability_proven"
assert value["codexVersion"] == "0.145.0"
assert value["directToolMode"] is True
assert value["codeModeEnabled"] is False
assert value["cleanupStatus"] == "complete"
assert value["unsafeCommittedEvidenceFindings"] == 0
rows = {row["id"]: row for row in value["rows"]}
live = rows["composed_live_apple_applied"]
assert live["commandExecutions"] == 1
assert live["appleAttempts"] == 1
assert live["appleValidResults"] == 1
assert live["additionalParentModelTurns"] == 0
assert live["originalAbsentFromNextRequest"] is True
assert live["replacementPresentInNextRequest"] is True
assert live["spooled"] is False
PY
```

Expected: exit `0`. Any failure stops DEV-254.

- [ ] **Step 3: Capture the proved source identities**

Run:

```bash
git ls-files --error-unmatch \
  fixtures/runtime-v1-capability/synthetic-plugin/hooks/codex/probe.py \
  fixtures/runtime-v1-capability/synthetic-plugin/runtime/DiagnosticCondenser.swift \
  tests/e2e/codex_runtime_v1_capability_probe.py
shasum -a 256 \
  fixtures/runtime-v1-capability/synthetic-plugin/hooks/codex/probe.py \
  fixtures/runtime-v1-capability/synthetic-plugin/runtime/DiagnosticCondenser.swift \
  tests/e2e/codex_runtime_v1_capability_probe.py
```

Expected: all three paths are tracked and three lowercase SHA-256 identities are recorded in the DEV-254 implementation note.

### Task 2: Add the Codex-only generated runtime component

**Files:**
- Modify: `CLAUDE.md`
- Modify: `plugins/apple-foundation-models-handoff/metadata/codex-interface.json`
- Modify: `scripts/sync_generated_artifacts.py`
- Modify: `tests/test_generated_artifacts.py`
- Generate: `AGENTS.md`
- Generate: `plugins/apple-foundation-models-handoff/.codex-plugin/plugin.json`
- Generate: `plugins/apple-foundation-models-handoff/runtime/runtime_contract.py`

- [ ] **Step 1: Write failing generator tests**

Add assertions that the canonical Codex interface contains:

```json
{
  "hooks": "./hooks/codex/hooks.json"
}
```

and that the generated manifest has the same top-level `hooks` value. Add a byte-parity assertion:

```python
self.assertEqual(
    (ROOT / "plugins/apple-foundation-models-handoff/runtime/runtime_contract.py").read_bytes(),
    (ROOT / "fixtures/dev-142/runtime_contract.py").read_bytes(),
)
```

Also add drift tests for a changed hook path and a changed generated runtime-contract byte.

- [ ] **Step 2: Run the focused tests and verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_generated_artifacts -v
```

Expected: FAIL because `hooks` and the generated runtime contract are not owned yet.

- [ ] **Step 3: Extend the generator minimally**

Add:

```python
RUNTIME_CONTRACT_INPUT = Path("fixtures/dev-142/runtime_contract.py")
RUNTIME_CONTRACT_OUTPUT = (
    PLUGIN_ROOT / "runtime/runtime_contract.py"
)
GENERATED_PATHS = (
    Path("AGENTS.md"),
    CODEX_MARKETPLACE,
    CODEX_MANIFEST,
    RUNTIME_CONTRACT_OUTPUT,
)
```

Allow exactly one additional `codex-interface.json` field:

```python
fields = {
    "displayName",
    "shortDescription",
    "longDescription",
    "developerName",
    "category",
    "capabilities",
    "websiteURL",
    "defaultPrompt",
    "hooks",
}
if value["hooks"] != "./hooks/codex/hooks.json":
    raise ValueError("hooks component")
```

Render the manifest with:

```python
"hooks": interface["hooks"],
```

but keep the nested `interface` object limited to its existing eight reader-facing fields. Add the runtime-contract bytes to `expected_artifacts` by reading the canonical DEV-142 file through the existing safe canonical-file reader.

- [ ] **Step 4: Record the canonical/generated boundary**

Update `CLAUDE.md` so `metadata/codex-interface.json`, the hook/Swift sources, and DEV-142 contract are canonical inputs, while the Codex manifest and plugin-local `runtime/runtime_contract.py` are generated outputs. Do not hand-edit `AGENTS.md`.

- [ ] **Step 5: Generate and verify GREEN**

Run:

```bash
python3 scripts/sync_generated_artifacts.py --write
python3 scripts/sync_generated_artifacts.py --check
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_generated_artifacts -v
```

Expected: generator synchronized and focused tests PASS.

- [ ] **Step 6: Commit the component boundary**

Run:

```bash
git add \
  CLAUDE.md AGENTS.md \
  plugins/apple-foundation-models-handoff/metadata/codex-interface.json \
  plugins/apple-foundation-models-handoff/.codex-plugin/plugin.json \
  plugins/apple-foundation-models-handoff/runtime/runtime_contract.py \
  scripts/sync_generated_artifacts.py tests/test_generated_artifacts.py
git commit -m "feat(DEV-254): add Codex runtime component boundary"
```

### Task 3: Promote the proved adapter and Swift consultation

**Files:**
- Create: `plugins/apple-foundation-models-handoff/hooks/codex/hooks.json`
- Create: `plugins/apple-foundation-models-handoff/hooks/codex/diagnostic_condensation.py`
- Create: `plugins/apple-foundation-models-handoff/runtime/DiagnosticCondenser.swift`
- Create: `tests/test_runtime_v1_production.py`

- [ ] **Step 1: Write the failing production tests**

Cover the closed hook payload; canonical `PostToolUse` plus `Bash`; direct mode; DEV-142 command allowlist; C0/C1 grant; 8,192–65,536-byte bounds; 75% context ceiling; at-most-one bridge call; complete semantic validation; 4,096-byte output/savings gates; and no-output fallback for every decline, malformed response, exception, timeout, cancellation, or unknown state.

The successful assertion is:

```python
self.assertEqual(set(response), {"continue", "stopReason"})
self.assertIs(response["continue"], False)
result = json.loads(response["stopReason"])
contract.validate_result(result)
self.assertEqual(result["outcome"], "applied")
```

The failure assertion is:

```python
self.assertIsNone(response)
self.assertEqual(command_executions, 0)
self.assertLessEqual(apple_attempts, 1)
```

`command_executions` is zero inside the hook because Codex alone owns the already-completed command.

- [ ] **Step 2: Run the production tests and verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_runtime_v1_production -v
```

Expected: FAIL because the production files do not exist.

- [ ] **Step 3: Add the one production hook**

Create:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "\"$RUNTIME_V1_PYTHON\" \"$PLUGIN_ROOT/hooks/codex/diagnostic_condensation.py\"",
            "timeout": 60,
            "statusMessage": "checking local diagnostic consultation"
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 4: Implement the adapter with the proved interface**

Expose only these interfaces:

```text
evaluate(payload: dict[str, object], *, contract, consult, repo_root: Path, observe) -> dict[str, object] | None
run_bridge_process(request: dict[str, object], *, executable: Path, timeout_seconds: float) -> dict[str, object]
```

The implementation order is fixed:

1. Validate the exact payload keys and direct `PostToolUse`/`Bash` identity.
2. Parse the command with generated `runtime_contract.parse_command`.
3. Classify each transferred field atomically; allow only purpose-bound C0/C1 `trustedLocal`.
4. Build and validate the frozen DEV-142 request.
5. Invoke the captured bridge once with a closed stdin object.
6. Build the full result from trusted bindings plus only the generated condensation.
7. Route and validate once with DEV-142.
8. Enforce output and realized-savings bounds.
9. Return only `{"continue": False, "stopReason": canonical_result}`.
10. Catch all other paths and return `None` without writing a reason to stdout.

The executable entrypoint loads only:

```python
plugin_root = Path(os.environ["RUNTIME_V1_PLUGIN_ROOT"])
repo_root = Path(os.environ["RUNTIME_V1_REPO_ROOT"])
bridge = Path(os.environ["RUNTIME_V1_BRIDGE_EXECUTABLE"])
contract = load_module(plugin_root / "runtime/runtime_contract.py")
```

It rejects missing, relative, symlinked, non-regular, or identity-drifting paths before consultation.

- [ ] **Step 5: Add the Swift source**

Promote the exact DEV-253 structured types and one-response flow, replacing the synthetic-only instruction with:

```swift
let instructions = Instructions(
    """
    Condense only literal diagnostic facts supplied by the application.
    Preserve command outcome, fatal and error identities, failed test
    identities, warning accounting, actionable next action, and completion.
    Do not invent paths, diagnoses, commands, secrets, or advice.
    """
)
```

Keep `SystemLanguageModel.default`, one fresh `LanguageModelSession`, `tools: []`, exact token counting, the 75% context ceiling, greedy sampling, a 1,024-token response limit, and `appleAttempts = 1` immediately before the sole `respond`.

- [ ] **Step 6: Run focused GREEN**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_runtime_v1_production \
  tests.test_dev_142_contract -v
xcrun --sdk macosx swiftc \
  -parse-as-library \
  plugins/apple-foundation-models-handoff/runtime/DiagnosticCondenser.swift \
  -o /tmp/runtime-v1-dev-254-condenser
rm -f /tmp/runtime-v1-dev-254-condenser
```

Expected: tests PASS, Swift compiles with the approved SDK, and the temporary executable is removed.

- [ ] **Step 7: Commit the runtime**

Run:

```bash
git add \
  plugins/apple-foundation-models-handoff/hooks/codex/hooks.json \
  plugins/apple-foundation-models-handoff/hooks/codex/diagnostic_condensation.py \
  plugins/apple-foundation-models-handoff/runtime/DiagnosticCondenser.swift \
  tests/test_runtime_v1_production.py
git commit -m "feat(DEV-254): add direct local diagnostic consultation"
```

### Task 4: Prove isolated production installation and fallback

**Files:**
- Create: `tests/e2e/codex_runtime_v1_production.py`
- Create: `docs/runtime-v1-installation.md`

- [ ] **Step 1: Write failing harness tests**

Require exact executable/version capture, isolated marketplace install, plugin-tree hash, explicit hook hash trust, environment inheritance, direct mode, one command, one Apple attempt, exact successful replacement, all approved no-output fallbacks, executable rechecks, and complete cleanup.

- [ ] **Step 2: Run the harness tests and verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_runtime_v1_production.ProductionHarnessTests -v
```

Expected: FAIL until the harness entrypoints exist.

- [ ] **Step 3: Implement the harness by reusing proved helpers**

Import only the exact host-capture, isolated-install, trust, loopback-provider, atomic-write, and cleanup helpers whose hashes were accepted by DEV-253. Do not import its synthetic row classifier or fault modes. Compile `DiagnosticCondenser.swift` into the isolated staged plugin root before installation, then launch captured Codex with the four explicit runtime variables.

- [ ] **Step 4: Document the bounded operation**

Document the exact stage/compile/install/trust/direct-mode invocation, supported host requirements, environment variables, fallback semantics, raw-data prohibition, and removal commands. State that packaging and savings remain unproved until DEV-255.

- [ ] **Step 5: Run deterministic and installed checks**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_runtime_v1_production -v
python3 scripts/sync_generated_artifacts.py --check
git diff --check
```

Run the installed success/fallback rows only from an authorized outer Codex session. Missing authentication, model, hardware, locale, trust, or cleanup is `blocked`, never substituted.

- [ ] **Step 6: Commit the production proof**

Run:

```bash
git add tests/e2e/codex_runtime_v1_production.py docs/runtime-v1-installation.md
git commit -m "test(DEV-254): prove production Runtime V1 installation"
```

### Task 5: Complete regression and review gates

**Files:**
- Verify all DEV-254 paths above.

- [ ] **Step 1: Run repository gates**

Run:

```bash
python3 scripts/sync_generated_artifacts.py --check
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests -p 'test_*.py' -v
git diff --check
git status --short
```

Expected: generator synchronized, full suite PASS except declared pre-existing skips, no diff errors, and only DEV-254 paths changed.

- [ ] **Step 2: Run Sol/High architecture and security review**

Review exact predecessor fidelity, generated authority, command ownership, one-attempt semantics, no-output fallback, trust binding, path safety, evidence safety, and absence of alternate providers or speculative framework code. Resolve every actionable finding and rerun Step 1.

- [ ] **Step 3: Finish the issue**

Open one DEV-254 PR, wait for green CI, merge, synchronize the baseline, verify ancestry and a clean worktree, then mark DEV-254 complete with exact proof. DEV-255 stays blocked until its plan refresh is complete.
