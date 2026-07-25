# Runtime V1 Successor Capability Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and execute the smallest repository-only gate that proves or blocks one exact Codex CLI `0.145.0` direct-tool result handoff through one real local Apple Foundation Models response, without creating a production runtime.

**Architecture:** Install a synthetic plugin into an isolated `CODEX_HOME`; its trusted `PostToolUse` adapter reuses the frozen DEV-142 contract and calls one compiled Swift condenser. A Python-standard-library harness drives the captured Codex CLI against a loopback deterministic Responses server, observes the exact second provider request, and records only normalized hashes, counters, statuses, timings, and cleanup state. The direct-boundary row uses a fake bridge first; the composed row may run only after that row passes and must use the real Apple bridge.

**Tech Stack:** Python 3 standard library and `unittest`; Codex CLI `0.145.0` plugin, hook, app-server JSON-RPC, and Responses wire interfaces; Swift 6.3.3; macOS SDK 26.5 `FoundationModels`; SHA-256 and JSON.

## Global Constraints

- Design authority: `docs/superpowers/specs/2026-07-25-runtime-v1-direct-local-diagnostic-consultation-design.md`.
- This plan covers only the successor capability gate. It does not implement the production runtime, the 24-pair Codex benchmark, packaging, or release logic.
- Keep every DEV-246 fixture, harness, evidence record, and conclusion unchanged. Never revive `suppressOutput`.
- Reuse `fixtures/dev-142/runtime_contract.py`, its schemas, and its corpus unchanged. Do not create a second routing policy or alter DEV-142 to fit generated output.
- Capture one explicit Codex executable, require the strict line `codex-cli 0.145.0`, snapshot its identity, and recheck it after every host phase.
- Capture and recheck the exact Python, `xcrun`, and Swift compiler executables used by the row. Normalize every committed executable identity to `<host-path>`.
- Accept only direct `shell_command` tool mode. Invoke Codex with `code_mode=false`; reject a first provider request that exposes or uses a code-mode tool.
- Install the exact synthetic plugin by isolated marketplace registration and `plugin add`. Do not use `codex --plugin-dir`.
- Trust the hook only after `hooks/list` returns its exact `currentHash`, the owner approves that hash, `config/batchWrite` persists it, and a second `hooks/list` returns `trustStatus = trusted`. Never use `--dangerously-bypass-hook-trust`.
- The loopback Responses server is a deterministic protocol fixture, not a generation provider. It performs no network inference and requires no real credential. `RUNTIME_V1_LOCAL_PROVIDER_KEY=local-probe` is a non-secret fixture value.
- Apple Foundation Models is the only added generation provider. Use `SystemLanguageModel.default`, one fresh `LanguageModelSession`, no tools, no transcript rehydration, and at most one `respond` per invocation.
- The original diagnostic command executes exactly once per row. Neither the hook nor the bridge may execute, retry, replay, or reconcile that command.
- This gate invokes Apple only for the fixed call ID, command root, command,
  and owner-approved C0 synthetic-result digest. All drift declines before the
  bridge.
- Keep deterministic source facts exclusively in the adapter's
  post-generation validator. Never send the expected condensation, oracle, or
  rubric into the Swift process or Apple prompt.
- A decline or failure emits no hook stdout and must leave the exact original result unchanged in the next provider request. A successful row alone may emit exactly two keys: `continue=false` and `stopReason` equal to the canonical validated DEV-142 result.
- Missing CLI, SDK, compiler, supported OS, eligible hardware, Apple Intelligence/model readiness, locale, trust, or cleanup is `blocked`. A violated invariant is `fail`.
- Do not claim savings from bytes. This gate proves boundary behavior and zero added parent turns only; actual parent-token reduction belongs to the later paired benchmark.
- Keep raw prompts, provider requests, tool contents, original results, Apple prompts/output, transcripts, private paths, configuration, credentials, and traces out of committed evidence.
- Do not modify the production plugin, generated plugin metadata, workflow skills, references, dependencies, package layout, or Linear.

---

## Supported Interface Sources

- [Codex hooks documentation](https://developers.openai.com/codex/hooks) — hook trust and `PostToolUse` control contract.
- [Tagged direct replacement test](https://github.com/openai/codex/blob/rust-v0.145.0/codex-rs/core/tests/suite/hooks.rs#L4497-L4552) — `continue:false` plus `stopReason` appears as the next request's function output.
- Tagged direct-shell output boundaries: [hook input](https://github.com/openai/codex/blob/rust-v0.145.0/codex-rs/core/src/tools/handlers/shell.rs#L205-L245) and [provider envelope](https://github.com/openai/codex/blob/rust-v0.145.0/codex-rs/core/src/tools/mod.rs#L78-L103) — the hook receives the raw command stream, while Codex separately builds the normal provider-facing result envelope.
- [Tagged custom-provider CLI test](https://github.com/openai/codex/blob/rust-v0.145.0/codex-rs/core/tests/suite/cli_stream.rs#L210-L258) — installed `codex exec` can target a loopback Responses endpoint through `model_providers`.
- [Tagged app-server hook API](https://github.com/openai/codex/blob/rust-v0.145.0/codex-rs/app-server/README.md#hooks) — `hooks/list`, `currentHash`, `trustStatus`, and `config/batchWrite`.
- [Apple guided generation](https://developer.apple.com/documentation/foundationmodels/generating-swift-data-structures-with-guided-generation) — `@Generable` structured response.
- [Apple context management](https://developer.apple.com/documentation/foundationmodels/managing-the-context-window) — exact token-count preflight and context window.
- Installed SDK 26.5 interface — `SystemLanguageModel.default`, `contextSize`, `tokenCount`, `LanguageModelSession`, `GenerationOptions.maximumResponseTokens`, and the structured `respond` overload.

## File Structure

- Create `fixtures/runtime-v1-capability/README.md` — exact gate, trust, privacy, stop, and manual execution rules.
- Create `fixtures/runtime-v1-capability/synthetic-plugin/.codex-plugin/plugin.json` — repository-only plugin identity.
- Create `fixtures/runtime-v1-capability/synthetic-plugin/hooks/codex/hooks.json` — one canonical `PostToolUse`/`Bash` handler.
- Create `fixtures/runtime-v1-capability/synthetic-plugin/hooks/codex/probe.py` — DEV-142 adapter, one-bridge boundary, and no-output fallback.
- Create `fixtures/runtime-v1-capability/synthetic-plugin/runtime/DiagnosticCondenser.swift` — one-shot local structured generator.
- Create `tests/e2e/codex_runtime_v1_capability_probe.py` — exact-host capture, isolated install/trust, loopback provider, row runner, and normalized evidence writer.
- Create `tests/test_codex_runtime_v1_capability_probe.py` — deterministic adapter, bridge, JSON-RPC, provider-boundary, fallback, and evidence tests.
- Create `docs/research/evidence/runtime-v1-capability-gate.json` — one closed normalized `pass`, `blocked`, or `fail` result.
- Create `docs/research/runtime-v1-capability-gate.md` — bounded interpretation and the production-work stop decision.

No schema, Python package, Swift package, shared runtime framework, or new dependency is needed. The adapter imports the existing DEV-142 module from the explicitly supplied repository root; the new harness imports only the reusable `_tree_sha256` and `_atomic_write_json` helpers from the historical DEV-246 harness. It does not reuse DEV-246's whole-item boundary inspector because a direct-shell hook sees raw command output while the provider sees Codex's normal result envelope.

## Gate Order

```text
offline adapter and bridge checks
  -> installed direct-boundary row with deterministic fake bridge
      -> composed installed row with one real Apple response
          -> untouched-original failure matrix
              -> normalized safe evidence
```

Stop immediately when a predecessor is `blocked` or `fail`. A source test, compile, plugin listing, hook invocation, fake bridge, or model prose cannot skip a gate.

### Task 1: Freeze the repository-only adapter and no-output fallback

**Files:**
- Create: `fixtures/runtime-v1-capability/synthetic-plugin/.codex-plugin/plugin.json`
- Create: `fixtures/runtime-v1-capability/synthetic-plugin/hooks/codex/hooks.json`
- Create: `fixtures/runtime-v1-capability/synthetic-plugin/hooks/codex/probe.py`
- Create: `tests/test_codex_runtime_v1_capability_probe.py`

**Interfaces:**
- Consumes: exact `PostToolUse` payload keys, `fixtures/dev-142/runtime_contract.py`, one explicit approved command root, one owner-approved synthetic-result SHA-256, and one injected consultation callable.
- Produces: `evaluate(payload, *, contract, consult, repo_root, approved_stimulus_sha256, observe) -> dict[str, object] | None`; `None` means exit `0` with empty stdout and untouched-original fallback.

- [ ] **Step 1: Write the failing adapter tests**

Create the test loader and these focused cases:

```python
ROOT = Path(__file__).resolve().parents[1]
ADAPTER = (
    ROOT / "fixtures/runtime-v1-capability/synthetic-plugin"
    / "hooks/codex/probe.py"
)
CONTRACT = ROOT / "fixtures/dev-142/runtime_contract.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def hook_payload(output: str) -> dict[str, object]:
    return {
        "session_id": "session-1",
        "transcript_path": "/transient/not-committed.jsonl",
        "cwd": str(ROOT),
        "hook_event_name": "PostToolUse",
        "model": "gpt-5.1-codex",
        "turn_id": "turn-1",
        "permission_mode": "never",
        "tool_name": "Bash",
        "tool_input": {
            "command": "python3 -m unittest -q diagnostic_fixture",
        },
        "tool_response": output,
        "tool_use_id": "call-runtime-v1",
    }


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.adapter = load_module("runtime_v1_adapter", ADAPTER)
        self.contract = load_module("dev142_contract_for_runtime_v1", CONTRACT)

    def eligible_output(self) -> str:
        return (
            "RUNTIME_V1_ORIGINAL_SENTINEL\n"
            "suite=synthetic unittest\n"
            "command-class=test\n"
            "outcome=success\n"
            "exit-status=0\n"
            "warning-count=0\n"
            "command-finished=true\n"
            "task-complete=true\n"
            "next-action=continue after successful synthetic unittest\n"
            "filler="
            + ("a" * 8200)
            + "\n"
        )

    def test_applied_consultation_emits_only_stop_reason(self):
        observed = []

        def consult(request):
            return {
                "status": "applied",
                "reasonCode": None,
                "appleAvailable": True,
                "localeSupported": True,
                "contextSize": 4096,
                "occupiedTokens": 2048,
                "appleAttempts": 1,
                "condensation": self.adapter.source_facts(0),
            }

        output = self.eligible_output()
        response = self.adapter.evaluate(
            hook_payload(output),
            contract=self.contract,
            consult=consult,
            repo_root=ROOT,
            approved_stimulus_sha256=hashlib.sha256(
                output.encode("utf-8")
            ).hexdigest(),
            observe=observed.append,
        )

        self.assertEqual(set(response), {"continue", "stopReason"})
        self.assertIs(response["continue"], False)
        result = json.loads(response["stopReason"])
        self.contract.validate_result(result)
        self.assertEqual(result["outcome"], "applied")
        self.assertLessEqual(
            len(response["stopReason"].encode("utf-8")),
            self.contract.Policy.MAXIMUM_CONDENSED_BYTES,
        )
        self.assertEqual(sum(row["event"] == "hook_invoked" for row in observed), 1)

    def test_below_minimum_never_calls_bridge_and_returns_no_output(self):
        def unexpected(*_):
            self.fail("bridge must not run for an ineligible result")

        output = "short"
        response = self.adapter.evaluate(
            hook_payload(output),
            contract=self.contract,
            consult=unexpected,
            repo_root=ROOT,
            approved_stimulus_sha256=hashlib.sha256(
                output.encode("utf-8")
            ).hexdigest(),
            observe=lambda _: None,
        )
        self.assertIsNone(response)

    def test_bridge_exception_returns_no_output(self):
        def broken(*_):
            raise OSError("synthetic bridge failure")

        output = self.eligible_output()
        response = self.adapter.evaluate(
            hook_payload(output),
            contract=self.contract,
            consult=broken,
            repo_root=ROOT,
            approved_stimulus_sha256=hashlib.sha256(
                output.encode("utf-8")
            ).hexdigest(),
            observe=lambda _: None,
        )
        self.assertIsNone(response)
```

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_codex_runtime_v1_capability_probe.AdapterTests -v
```

Expected: FAIL because the adapter path does not exist.

- [ ] **Step 3: Add the exact synthetic plugin declarations**

Use this manifest:

```json
{
  "name": "runtime-v1-capability-probe",
  "version": "0.0.1",
  "description": "Repository-only Runtime V1 direct diagnostic consultation capability gate.",
  "hooks": "./hooks/codex/hooks.json"
}
```

Use one handler with a bounded production-like timeout:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "\"$RUNTIME_V1_PYTHON\" \"$PLUGIN_ROOT/hooks/codex/probe.py\"",
            "timeout": 60,
            "statusMessage": "checking local diagnostic consultation"
          }
        ]
      }
    ]
  }
}
```

Do not add a skill, command, agent, MCP server, app, dependency, or production-plugin reference.

- [ ] **Step 4: Implement the closed adapter**

Define the adapter core exactly:

```python
HOOK_INPUT_KEYS = (
    "session_id", "transcript_path", "cwd", "hook_event_name", "model",
    "turn_id", "permission_mode", "tool_name", "tool_input",
    "tool_response", "tool_use_id",
)
CONSULTATION_KEYS = (
    "status", "reasonCode", "appleAvailable", "localeSupported",
    "contextSize", "occupiedTokens", "appleAttempts", "condensation",
)
STATE_VERSION = "runtime-v1-direct-consultation-v1"
TOOL_VERSION = "codex-cli-0.145.0"
APPROVED_COMMAND = "python3 -m unittest -q diagnostic_fixture"
APPROVED_CALL_ID = "call-runtime-v1"


def source_facts(exit_status: int) -> dict[str, Any]:
    outcome = "success" if exit_status == 0 else "failure"
    return {
        "commandOutcome": outcome,
        "summary": f"synthetic unittest {outcome}",
        "summaryFacts": [
            "command-class=test",
            f"outcome={outcome}",
            f"exit-status={exit_status}",
            "warning-count=0",
        ],
        "diagnostics": [],
        "warningCount": 0,
        "omittedWarningCount": 0,
        "nextAction": (
            "continue after successful synthetic unittest"
            if exit_status == 0
            else "inspect the synthetic unittest failure"
        ),
        "completionFacts": [
            "command-finished=true",
            f"task-complete={'true' if exit_status == 0 else 'false'}",
        ],
    }


def complete_result(
    request: Mapping[str, Any],
    consultation: Mapping[str, Any],
) -> dict[str, Any]:
    bindings = {
        key: request[key]
        for key in (
            "schemaVersion", "policyVersion", "callID", "toolName",
            "toolVersion", "stateVersion", "action", "commandClass",
            "originalResultType", "originalResultDigest", "exitStatus",
            "interrupted",
        )
    }
    if consultation["status"] == "applied":
        return {
            **bindings,
            "outcome": "applied",
            "resultType": "diagnostic_condensation",
            "condensation": consultation["condensation"],
        }
    return {
        **bindings,
        "outcome": consultation["status"],
        "reasonCode": consultation["reasonCode"],
    }


def evaluate(
    payload: Mapping[str, Any],
    *,
    contract: ModuleType,
    consult: Callable[
        [dict[str, Any]], Mapping[str, Any]
    ],
    repo_root: Path,
    approved_stimulus_sha256: str,
    observe: Callable[[Mapping[str, Any]], None],
) -> dict[str, Any] | None:
    try:
        if type(payload) is not dict or set(payload) != set(HOOK_INPUT_KEYS):
            return None
        if (
            payload["hook_event_name"] != "PostToolUse"
            or payload["tool_name"] != "Bash"
            or type(payload["tool_response"]) is not str
            or type(payload["tool_input"]) is not dict
            or set(payload["tool_input"]) != {"command"}
            or type(payload["tool_input"]["command"]) is not str
            or payload["tool_input"]["command"] != APPROVED_COMMAND
            or payload["tool_use_id"] != APPROVED_CALL_ID
            or payload["cwd"] != str(repo_root)
        ):
            return None

        observe({
            "event": "hook_invoked",
            "callID": payload["tool_use_id"],
            "hookInvocations": 1,
        })
        exit_status = 0
        original_bytes = payload["tool_response"].encode("utf-8")
        original_sha256 = hashlib.sha256(original_bytes).hexdigest()
        observe({
            "event": "original_observed",
            "callID": payload["tool_use_id"],
            "originalSha256": original_sha256,
        })
        if (
            not re.fullmatch(r"[0-9a-f]{64}", approved_stimulus_sha256)
            or original_sha256 != approved_stimulus_sha256
        ):
            return None

        fields = [{
            "name": "message",
            "value": payload["tool_response"],
            "origin": "trustedLocal",
            "classification": "C0",
            "purpose": "diagnostic_condensation",
            "destination": "apple_on_device",
            "retention": "ephemeral",
            "redacted": False,
        }]
        input_bytes = len(contract.canonical_field_bytes(fields))
        request = {
            "schemaVersion": 1,
            "policyVersion": "diagnostic-condensation-v1",
            "callID": payload["tool_use_id"],
            "toolName": "Bash",
            "toolVersion": TOOL_VERSION,
            "stateVersion": STATE_VERSION,
            "action": "condense_diagnostic_output",
            "commandClass": "test",
            "originalResultType": "string",
            "originalResultDigest": original_sha256,
            "exitStatus": exit_status,
            "interrupted": False,
            "inputBytes": input_bytes,
            "estimatedSavingsBytes": contract.estimate_savings(input_bytes),
            "fields": fields,
        }
        contract.validate_request(request)
        contract.parse_command(payload["tool_input"]["command"], repo_root)

        expected = source_facts(exit_status)
        consultation = dict(consult(copy.deepcopy(request)))
        if set(consultation) != set(CONSULTATION_KEYS):
            return None
        if (
            consultation["status"] not in {"applied", "declined", "fail"}
            or type(consultation["appleAvailable"]) is not bool
            or type(consultation["localeSupported"]) is not bool
            or type(consultation["contextSize"]) is not int
            or consultation["contextSize"] < 1
            or type(consultation["occupiedTokens"]) is not int
            or consultation["occupiedTokens"] < 0
            or consultation["appleAttempts"] not in {0, 1}
        ):
            return None
        if consultation["status"] == "applied":
            if consultation["reasonCode"] is not None:
                return None
        elif type(consultation["reasonCode"]) is not str:
            return None
        observe({
            "event": "consultation_completed",
            "callID": payload["tool_use_id"],
            "appleAttempts": consultation["appleAttempts"],
            "appleValidResults": int(
                consultation["status"] == "applied"
            ),
        })

        frozen_result = complete_result(request, consultation)
        routed = contract.route(
            request,
            {
                "eventName": "PostToolUse",
                "command": payload["tool_input"]["command"],
                "repoRoot": repo_root,
                "appleAvailable": consultation["appleAvailable"],
                "localeSupported": consultation["localeSupported"],
                "occupiedTokens": consultation["occupiedTokens"],
                "contextSize": consultation["contextSize"],
                "sourceFacts": expected,
                "bridge": lambda _: copy.deepcopy(frozen_result),
            },
        )
        if routed.get("outcome") != "applied":
            return None
        contract.validate_result(routed)
        stop_reason = json.dumps(
            routed,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        replacement_bytes = len(stop_reason.encode("utf-8"))
        if (
            replacement_bytes > contract.Policy.MAXIMUM_CONDENSED_BYTES
            or input_bytes - replacement_bytes
            < contract.Policy.MINIMUM_REALIZED_SAVINGS_BYTES
        ):
            return None
        observe({
            "event": "replacement_emitted",
            "callID": payload["tool_use_id"],
            "replacementSha256": hashlib.sha256(
                stop_reason.encode("utf-8")
            ).hexdigest(),
            "replacementBytes": replacement_bytes,
            "appleAttempts": consultation["appleAttempts"],
        })
        return {"continue": False, "stopReason": stop_reason}
    except Exception:
        return None


def run_bridge_process(
    request: Mapping[str, Any],
    *,
    executable: Path,
    timeout_seconds: float,
) -> Mapping[str, Any]:
    encoded = json.dumps(
        {
            "diagnosticText": request["fields"][0]["value"],
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    completed = subprocess.run(
        [str(executable)],
        input=encoded,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        shell=False,
        timeout=timeout_seconds,
    )
    if (
        completed.returncode != 0
        or completed.stderr != b""
        or not completed.stdout.endswith(b"\n")
        or completed.stdout.count(b"\n") != 1
    ):
        raise OSError("bridge_process_failed")
    decoded = json.loads(completed.stdout)
    if type(decoded) is not dict:
        raise ValueError("bridge_output_invalid")
    return decoded
```

The implementation order embodied above is security-significant:

1. Emit a normalized `hook_invoked` observation containing only `callID` and counters.
2. Require the exact top-level key set, `PostToolUse`, canonical `Bash`, fixed
   call ID, exact approved command, exact command root, a string
   `tool_response`, and a `tool_input` whose only field is `command`.
3. Treat this gate-only direct-shell event as successful only because Codex
   `0.145.0` invokes the post-hook path after the exact command completes
   successfully; bind `exitStatus=0` and do not generalize that inference to
   production.
4. Hash the untouched UTF-8 result and decline unless it equals the
   owner-approved synthetic stimulus digest. Emit only `originalSha256`.
5. Only after that digest grant passes, create one C0 `message` field with
   `origin=trustedLocal`, `purpose=diagnostic_condensation`,
   `destination=apple_on_device`, `retention=ephemeral`, and
   `redacted=false`.
6. Use `contract.canonical_field_bytes`, `contract.estimate_savings`, `contract.validate_request`, and `contract.parse_command` before calling `consult`.
7. Keep the deterministic `source_facts` oracle outside the consultation and
   use it only for post-generation semantic validation.

8. Call `consult` once. Require the exact consultation key set, booleans for availability/locale, positive context size, nonnegative occupied tokens, and `appleAttempts` in `{0,1}`.
9. Build the full response with `complete_result`; only `condensation` comes
   from the consultation.

10. Pass the frozen response through one call to `contract.route`, with actual availability, locale, occupied-token, and context-size values and an in-memory bridge callback returning the frozen result.
11. Emit a hook response only when the routed result is `applied`, `contract.validate_result` passes, canonical UTF-8 size is at most `4096`, and realized savings are at least `4096`.
12. Catch validation, process, timeout, decoding, cancellation, and unknown failures and return `None`. Never place a reason on stdout.

`run_bridge_process` sends a closed JSON object containing only
`diagnosticText`; it requires one compact JSON line on stdout and rejects
stderr or extra bytes. The expected condensation never crosses into the
Swift process or Apple context.

Use this process entry boundary:

```python
def load_contract(repo_root: Path) -> ModuleType:
    path = repo_root / "fixtures/dev-142/runtime_contract.py"
    spec = importlib.util.spec_from_file_location(
        "runtime_v1_dev142_contract",
        path,
    )
    if spec is None or spec.loader is None:
        raise OSError("contract_unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def append_observation(path: Path, value: Mapping[str, Any]) -> None:
    encoded = (
        json.dumps(value, ensure_ascii=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    descriptor = os.open(
        path,
        os.O_APPEND | os.O_CREAT | os.O_WRONLY,
        0o600,
    )
    try:
        os.write(descriptor, encoded)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        if type(payload) is not dict:
            return 0
        repository_root = Path(os.environ["RUNTIME_V1_REPO_ROOT"])
        approved_workspace = Path(
            os.environ["RUNTIME_V1_APPROVED_WORKSPACE"]
        )
        approved_stimulus_sha256 = os.environ[
            "RUNTIME_V1_APPROVED_STIMULUS_SHA256"
        ]
        observation_path = Path(os.environ["RUNTIME_V1_OBSERVATION_PATH"])
        bridge_executable = Path(
            os.environ["RUNTIME_V1_BRIDGE_EXECUTABLE"]
        )
        fault_mode = os.environ.get("RUNTIME_V1_FAULT_MODE", "none")
        if fault_mode not in {"none", "adapter_crash", "hook_timeout"}:
            return 0

        def observe(value: Mapping[str, Any]) -> None:
            append_observation(observation_path, value)
            if value["event"] != "original_observed":
                return
            if fault_mode == "adapter_crash":
                os._exit(70)
            if fault_mode == "hook_timeout":
                time.sleep(61)

        contract = load_contract(repository_root)
        response = evaluate(
            payload,
            contract=contract,
            consult=lambda request: run_bridge_process(
                request,
                executable=bridge_executable,
                timeout_seconds=30,
            ),
            repo_root=approved_workspace,
            approved_stimulus_sha256=approved_stimulus_sha256,
            observe=observe,
        )
        if response is not None:
            json.dump(
                response,
                sys.stdout,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
            sys.stdout.write("\n")
        return 0
    except Exception:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

The repository-only fault modes execute only after the original digest
observation. `hook_timeout` sleeps for `61` seconds so a temporary one-second
hook variant can prove host timeout fallback.

- [ ] **Step 5: Add closed-input and failure tests**

Add exact tests for:

```text
unknown hook key -> no output, zero bridge calls
wrong event/tool -> no output, zero bridge calls
wrong call ID, cwd, command, or stimulus digest -> no output, zero bridge calls
unsafe/private-path or unapproved message -> no output, zero bridge calls
input below 8192 or above 65536 canonical bytes -> no output
malformed consultation keys -> no output
apple unavailable or locale unsupported -> no output, appleAttempts=0
occupiedTokens/contextSize over 75% -> no output
invalid condensation, output over 4096, or savings under 4096 -> no output
valid applied result -> exactly continue=false plus stopReason
```

Assert the original sentinel never occurs in observation JSON and every failure returns `None`.

- [ ] **Step 6: Run focused GREEN checks**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_codex_runtime_v1_capability_probe.AdapterTests -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_dev_142_contract -v
```

Expected: both commands PASS; no Codex, Apple model, network, or live bridge runs.

- [ ] **Step 7: Commit the adapter checkpoint**

```bash
git add \
  fixtures/runtime-v1-capability/synthetic-plugin/.codex-plugin/plugin.json \
  fixtures/runtime-v1-capability/synthetic-plugin/hooks/codex/hooks.json \
  fixtures/runtime-v1-capability/synthetic-plugin/hooks/codex/probe.py \
  tests/test_codex_runtime_v1_capability_probe.py
git commit -m "test: define Runtime V1 capability adapter"
```

### Task 2: Add the one-shot Apple structured condenser

**Files:**
- Create: `fixtures/runtime-v1-capability/synthetic-plugin/runtime/DiagnosticCondenser.swift`
- Modify: `tests/test_codex_runtime_v1_capability_probe.py`

**Interfaces:**
- Consumes: one UTF-8 JSON object on stdin with only `diagnosticText: String`.
- Produces: one `BridgeOutput` JSON object on stdout; raw prompts, Apple output, and errors are never written elsewhere.

- [ ] **Step 1: Write the failing source and compile-contract tests**

Add:

```python
SWIFT_SOURCE = (
    ROOT / "fixtures/runtime-v1-capability/synthetic-plugin"
    / "runtime/DiagnosticCondenser.swift"
)


class SwiftBridgeTests(unittest.TestCase):
    def test_source_uses_one_local_structured_response(self):
        source = SWIFT_SOURCE.read_text(encoding="utf-8")
        self.assertEqual(source.count("try await session.respond("), 1)
        self.assertIn("SystemLanguageModel.default", source)
        self.assertIn("tools: []", source)
        self.assertIn("maximumResponseTokens: 1024", source)
        self.assertIn("tokenCount(for: instructions)", source)
        self.assertIn("tokenCount(for: prompt)", source)
        self.assertIn("tokenCount(for: DiagnosticCondensation.generationSchema)", source)
        self.assertNotIn("Transcript(", source)
        self.assertNotIn("expectedCondensation", source)
        self.assertNotIn("http://", source)
        self.assertNotIn("https://", source)

    def test_source_typechecks_against_sdk_26_5(self):
        xcrun = shutil.which("xcrun")
        swiftc = shutil.which("swiftc")
        if xcrun is None or swiftc is None:
            self.skipTest("blocked/missing_swift_toolchain")
        sdk_version = subprocess.run(
            [xcrun, "--sdk", "macosx", "--show-sdk-version"],
            capture_output=True, text=True, check=False, timeout=30,
        )
        if sdk_version.returncode != 0 or sdk_version.stdout != "26.5\n":
            self.skipTest("blocked/sdk_26_5_unavailable")
        sdk_path = subprocess.run(
            [xcrun, "--sdk", "macosx", "--show-sdk-path"],
            capture_output=True, text=True, check=True, timeout=30,
        ).stdout.strip()
        completed = subprocess.run(
            [
                swiftc, "-typecheck", "-parse-as-library",
                "-target", "arm64-apple-macos26.4",
                "-sdk", sdk_path, str(SWIFT_SOURCE),
            ],
            capture_output=True, text=True, check=False, timeout=60,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
```

- [ ] **Step 2: Run the bridge tests and verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_codex_runtime_v1_capability_probe.SwiftBridgeTests -v
```

Expected: FAIL because `DiagnosticCondenser.swift` does not exist.

- [ ] **Step 3: Implement the installed-SDK structured types**

Use these exact shapes:

```swift
import Foundation
import FoundationModels

@available(macOS 26.4, *)
@Generable
struct GeneratedDiagnostic: Codable {
    @Guide(description: "Stable diagnostic identifier.")
    let id: String
    @Guide(description: "Exactly fatal, error, warning, or info.")
    let severity: String
    let code: String
    let message: String
    let file: String?
    let line: Int?
    let column: Int?
    let failedTestID: String?
}

@available(macOS 26.4, *)
@Generable
struct DiagnosticCondensation: Codable {
    @Guide(description: "Exactly success, failure, or interrupted.")
    let commandOutcome: String
    let summary: String
    let summaryFacts: [String]
    let diagnostics: [GeneratedDiagnostic]
    let warningCount: Int
    let omittedWarningCount: Int
    let nextAction: String
    let completionFacts: [String]
}

@available(macOS 26.4, *)
struct BridgeInput: Decodable {
    let diagnosticText: String
}

@available(macOS 26.4, *)
struct BridgeOutput: Encodable {
    let status: String
    let reasonCode: String?
    let appleAvailable: Bool
    let localeSupported: Bool
    let contextSize: Int
    let occupiedTokens: Int
    let appleAttempts: Int
    let condensation: DiagnosticCondensation?
}
```

- [ ] **Step 4: Implement one availability/token/respond path**

The executable must:

```swift
@available(macOS 26.4, *)
func consult(_ input: BridgeInput) async -> BridgeOutput {
    let model = SystemLanguageModel.default
    let contextSize = model.contextSize

    guard case .available = model.availability else {
        return BridgeOutput(
            status: "declined", reasonCode: "apple_unavailable",
            appleAvailable: false, localeSupported: false,
            contextSize: contextSize, occupiedTokens: 0,
            appleAttempts: 0, condensation: nil
        )
    }
    guard model.supportsLocale() else {
        return BridgeOutput(
            status: "declined", reasonCode: "locale_unsupported",
            appleAvailable: true, localeSupported: false,
            contextSize: contextSize, occupiedTokens: 0,
            appleAttempts: 0, condensation: nil
        )
    }

    let instructions = Instructions(
        """
        Condense only literal facts in the supplied synthetic diagnostic.
        Use the suite and outcome values for the summary. Preserve the ordered
        command-class, outcome, exit-status, and warning-count facts. Use the
        source next-action value unchanged. Preserve command-finished and
        task-complete as ordered completion facts. Emit diagnostics only for
        literal fatal, error, warning, or info records. Do not add paths,
        secrets, diagnoses, or advice.
        """
    )
    let prompt = Prompt(
        "Synthetic diagnostic to condense:\n\(input.diagnosticText)"
    )
    let responseReserve = 1024

    var appleAttempts = 0
    do {
        let instructionTokens =
            try await model.tokenCount(for: instructions)
        let promptTokens = try await model.tokenCount(for: prompt)
        let schemaTokens = try await model.tokenCount(
            for: DiagnosticCondensation.generationSchema
        )
        let occupiedTokens =
            instructionTokens + promptTokens + schemaTokens + responseReserve
        guard occupiedTokens * 4 <= contextSize * 3 else {
            return BridgeOutput(
                status: "declined", reasonCode: "context_budget_exceeded",
                appleAvailable: true, localeSupported: true,
                contextSize: contextSize, occupiedTokens: occupiedTokens,
                appleAttempts: 0, condensation: nil
            )
        }

        let session = LanguageModelSession(
            model: model,
            tools: [],
            instructions: instructions
        )
        appleAttempts = 1
        let response = try await session.respond(
            to: prompt,
            generating: DiagnosticCondensation.self,
            options: GenerationOptions(
                sampling: .greedy,
                maximumResponseTokens: 1024
            )
        )
        return BridgeOutput(
            status: "applied", reasonCode: nil,
            appleAvailable: true, localeSupported: true,
            contextSize: contextSize, occupiedTokens: occupiedTokens,
            appleAttempts: appleAttempts, condensation: response.content
        )
    } catch {
        return BridgeOutput(
            status: "fail", reasonCode: "generation_declined",
            appleAvailable: true, localeSupported: true,
            contextSize: contextSize, occupiedTokens: 0,
            appleAttempts: appleAttempts, condensation: nil
        )
    }
}
```

Add this async entry point:

```swift
@main
struct DiagnosticCondenserMain {
    static func main() async {
        guard #available(macOS 26.4, *) else {
            return
        }
        do {
            let inputData = FileHandle.standardInput.readDataToEndOfFile()
            let input = try JSONDecoder().decode(
                BridgeInput.self,
                from: inputData
            )
            let output = await consult(input)
            var encoded = try JSONEncoder().encode(output)
            encoded.append(0x0A)
            FileHandle.standardOutput.write(encoded)
        } catch {
            let output = BridgeOutput(
                status: "fail",
                reasonCode: "contract_invariant_failed",
                appleAvailable: false,
                localeSupported: false,
                contextSize: 1,
                occupiedTokens: 0,
                appleAttempts: 0,
                condensation: nil
            )
            if var encoded = try? JSONEncoder().encode(output) {
                encoded.append(0x0A)
                FileHandle.standardOutput.write(encoded)
            }
        }
    }
}
```

It reads stdin once, invokes `consult` once, and encodes once on the normal
path. It never prints the model response, prompt, diagnostic, transcript, or
error description to stderr.

- [ ] **Step 5: Verify compile and process boundaries**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_codex_runtime_v1_capability_probe.SwiftBridgeTests -v

runtime_v1_tmp_dir="$(mktemp -d)"
test -d "$runtime_v1_tmp_dir"
trap 'rm -rf -- "$runtime_v1_tmp_dir"' EXIT
runtime_v1_sdk="$(xcrun --sdk macosx --show-sdk-path)"
swiftc -parse-as-library \
  -target arm64-apple-macos26.4 \
  -sdk "$runtime_v1_sdk" \
  fixtures/runtime-v1-capability/synthetic-plugin/runtime/DiagnosticCondenser.swift \
  -o "$runtime_v1_tmp_dir/DiagnosticCondenser"
test -x "$runtime_v1_tmp_dir/DiagnosticCondenser"
```

Expected: tests PASS and a temporary executable exists. Do not invoke it yet; compilation is not live Apple proof.

- [ ] **Step 6: Commit the bridge checkpoint**

```bash
git add \
  fixtures/runtime-v1-capability/synthetic-plugin/runtime/DiagnosticCondenser.swift \
  tests/test_codex_runtime_v1_capability_probe.py
git commit -m "test: add local Apple condenser fixture"
```

### Task 3: Build the installed-CLI direct-boundary harness

**Files:**
- Create: `tests/e2e/codex_runtime_v1_capability_probe.py`
- Modify: `tests/test_codex_runtime_v1_capability_probe.py`

**Interfaces:**
- Consumes: captured Codex/Python/Swift toolchain paths, the exact plugin tree, owner-approved plugin/hook/stimulus hashes, and one phase name.
- Produces: `run_row(*, codex, python, plugin, approved_plugin_sha256, approved_hook_hash, approved_stimulus_sha256, bridge_executable, phase, baseline_provider_requests) -> dict[str, object]`; raw provider requests remain in memory and the returned row contains normalized metadata only.

- [ ] **Step 1: Add failing host, trust, and provider tests**

Add tests for:

```python
def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def hooks_list(current_hash: str, trust_status: str) -> dict[str, object]:
    return {
        "data": [{
            "cwd": str(ROOT),
            "hooks": [{
                "key": (
                    "runtime-v1-capability-probe@runtime-v1-capability:"
                    "hooks/codex/hooks.json:post_tool_use:0:0"
                ),
                "matcher": "Bash",
                "handlerType": "command",
                "source": "plugin",
                "pluginId": (
                    "runtime-v1-capability-probe@runtime-v1-capability"
                ),
                "enabled": True,
                "isManaged": False,
                "currentHash": current_hash,
                "trustStatus": trust_status,
            }],
            "warnings": [],
            "errors": [],
        }],
    }


class FakeRpc:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.methods = []

    def call(self, method, params):
        self.methods.append(method)
        return next(self.responses)


class HarnessTests(unittest.TestCase):
    def test_strict_codex_capture_requires_exact_0145(self):
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "codex"
            executable.write_text(
                "#!/bin/sh\nprintf 'codex-cli 0.145.0\\n'\n",
                encoding="utf-8",
            )
            executable.chmod(0o700)
            captured = harness.capture_codex(executable)
            captured.recheck()
            executable.write_text(
                "#!/bin/sh\nprintf 'codex-cli 0.146.0\\n'\n",
                encoding="utf-8",
            )
            executable.chmod(0o700)
            with self.assertRaises(harness.ProbeFailure):
                captured.recheck()

    def test_trust_uses_list_hash_batch_write_and_readback(self):
        rpc = FakeRpc([
            hooks_list("sha256:reviewed", "untrusted"),
            {},
            hooks_list("sha256:reviewed", "trusted"),
        ])
        result = harness.trust_hook(
            rpc,
            cwd=ROOT,
            plugin_id="runtime-v1-capability-probe@runtime-v1-capability",
            approved_hash="sha256:reviewed",
        )
        self.assertTrue(result)
        self.assertEqual(rpc.methods, [
            "hooks/list", "config/batchWrite", "hooks/list",
        ])

    def test_second_request_contains_replacement_not_original(self):
        row = harness.classify_row(
            row_id="direct_fake_applied",
            bridge_kind="fake",
            stimulus=b"original",
            approved_stimulus_sha256=digest(b"original"),
            hook_input_sha256=digest(b"original"),
            replacement_sha256=digest(b"replacement"),
            next_output=b"replacement",
            baseline_provider_requests=2,
            provider_requests=2,
            command_executions=1,
            hook_invocations=1,
            apple_attempts=0,
        )
        self.assertTrue(row["originalAbsentFromNextRequest"])
        self.assertTrue(row["replacementPresentInNextRequest"])
        self.assertEqual(row["additionalParentModelTurns"], 0)

    def test_no_output_preserves_normal_codex_envelope(self):
        stimulus = b"RUNTIME_V1_ORIGINAL_SENTINEL\nsafe\n"
        row = harness.classify_row(
            row_id="bridge_crash",
            bridge_kind="crash",
            stimulus=stimulus,
            approved_stimulus_sha256=digest(stimulus),
            hook_input_sha256=digest(stimulus),
            replacement_sha256=None,
            next_output=(
                b"Exit code: 0\nWall time: 0.1 seconds\nOutput:\n"
                + stimulus
            ),
            baseline_provider_requests=2,
            provider_requests=2,
            command_executions=1,
            hook_invocations=1,
            apple_attempts=0,
        )
        self.assertTrue(row["originalPreserved"])
        self.assertEqual(row["status"], "pass")
```

- [ ] **Step 2: Run the harness tests and verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_codex_runtime_v1_capability_probe.HarnessTests -v
```

Expected: FAIL because the e2e harness does not exist.

- [ ] **Step 3: Reuse only the safe historical helpers**

Load `tests/e2e/codex_result_replacement_probe.py` through `importlib` and bind:

```python
tree_sha256 = dev246._tree_sha256
atomic_write_json = dev246._atomic_write_json
```

Do not import or call DEV-246 `inspect_model_boundary`, `run_discovery`,
`isolated_lifecycle`, `_manual_blocks_replacement`, or its verdict normalizer.
The inspector compares hashes of whole provider items, but Codex supplies this
hook only the raw direct-shell output. The other helpers intentionally encode
the canceled `suppressOutput` path and obsolete manual blocker.

Implement a new exact-host capture because the DEV-246 preflight requires the obsolete manual:

```python
class ProbeBlocked(Exception):
    pass


class ProbeFailure(Exception):
    pass


def executable_snapshot(metadata: os.stat_result) -> tuple[int, ...]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        stat.S_IFMT(metadata.st_mode),
        stat.S_IMODE(metadata.st_mode),
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


@dataclass(frozen=True)
class CapturedExecutable:
    locator: Path
    resolved: Path
    snapshot: tuple[int, ...]
    version: str

    def recheck(self) -> None:
        try:
            resolved = self.locator.resolve(strict=True)
            metadata = resolved.stat()
        except OSError:
            raise ProbeFailure("host_resolution_or_version_drift") from None
        if (
            resolved != self.resolved
            or executable_snapshot(metadata) != self.snapshot
            or not stat.S_ISREG(metadata.st_mode)
            or not os.access(self.locator, os.X_OK)
        ):
            raise ProbeFailure("host_resolution_or_version_drift")
        completed = subprocess.run(
            [str(self.resolved), "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            shell=False,
            timeout=30,
            env={"PATH": os.environ.get("PATH", "")},
        )
        if (
            completed.returncode != 0
            or completed.stderr != b""
            or completed.stdout != b"codex-cli 0.145.0\n"
        ):
            raise ProbeFailure("host_resolution_or_version_drift")


def capture_codex(path: Path) -> CapturedExecutable:
    try:
        resolved = path.resolve(strict=True)
        metadata = resolved.stat()
    except OSError:
        raise ProbeBlocked("missing_binary_or_version_mismatch") from None
    if not stat.S_ISREG(metadata.st_mode) or not os.access(path, os.X_OK):
        raise ProbeBlocked("missing_binary_or_version_mismatch")
    completed = subprocess.run(
        [str(resolved), "--version"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        shell=False,
        timeout=30,
        env={"PATH": os.environ.get("PATH", "")},
    )
    if (
        completed.returncode != 0
        or completed.stderr != b""
        or completed.stdout != b"codex-cli 0.145.0\n"
    ):
        raise ProbeBlocked("missing_binary_or_version_mismatch")
    captured = CapturedExecutable(
        locator=path,
        resolved=resolved,
        snapshot=executable_snapshot(metadata),
        version="0.145.0",
    )
    captured.recheck()
    return captured
```

`capture_executable` must reject symlinks after resolution drift, non-regular or non-runnable files, stderr, multiline versions, path-bearing versions, timeouts, and identity changes. Snapshot device, inode, file type, mode, size, mtime, and ctime.

- [ ] **Step 4: Implement the loopback Responses server**

Use `ThreadingHTTPServer(("127.0.0.1", 0), Handler)` and accept only `POST /v1/responses`. Keep decoded bodies in a process-memory list.

Return this first SSE sequence:

```python
[
    {"type": "response.created", "response": {"id": "resp-1"}},
    {
        "type": "response.output_item.done",
        "item": {
            "type": "function_call",
            "call_id": "call-runtime-v1",
            "name": "shell_command",
            "arguments": json.dumps({
                "command": "python3 -m unittest -q diagnostic_fixture",
                "timeout_ms": 30_000,
            }, separators=(",", ":")),
        },
    },
    {
        "type": "response.completed",
        "response": {
            "id": "resp-1",
            "usage": {
                "input_tokens": 0,
                "input_tokens_details": None,
                "output_tokens": 0,
                "output_tokens_details": None,
                "total_tokens": 0,
            },
        },
    },
]
```

Return an assistant message plus `response.completed` for the second request. Format every event as:

```python
def sse(events):
    return "".join(
        f"event: {event['type']}\ndata: "
        f"{json.dumps(event, separators=(',', ':'))}\n\n"
        for event in events
    ).encode("utf-8")
```

Reject a third provider request. Do not log headers or bodies.

- [ ] **Step 5: Materialize one deterministic command workspace**

The harness writes `diagnostic_fixture.py` only inside its temporary workspace:

```python
from pathlib import Path
import os
import sys
import unittest

counter = Path(os.environ["RUNTIME_V1_COMMAND_COUNTER"])
previous = int(counter.read_text() or "0") if counter.exists() else 0
counter.write_text(str(previous + 1))

unittest.runner.time.perf_counter = lambda: 0.0

DIAGNOSTIC = (
    "RUNTIME_V1_ORIGINAL_SENTINEL\n"
    "suite=synthetic unittest\n"
    "command-class=test\n"
    "outcome=success\n"
    "exit-status=0\n"
    "warning-count=0\n"
    "command-finished=true\n"
    "task-complete=true\n"
    "next-action=continue after successful synthetic unittest\n"
    "filler="
    + ("a" * 8200)
    + "\n"
)


class DiagnosticFixture(unittest.TestCase):
    def test_large_safe_output(self):
        sys.stdout.write(DIAGNOSTIC)
        sys.stdout.flush()
```

Run with `PYTHON_COLORS=0`, `NO_COLOR=1`, and a non-TTY. The harness
constructs the approved bytes as `DIAGNOSTIC` followed by
`----------------------------------------------------------------------\nRan 1 test in 0.000s\n\nOK\n`,
hashes them before the row, and passes only that reviewed hash as
`RUNTIME_V1_APPROVED_STIMULUS_SHA256`; it never learns a grant from the
observed hook payload. Assert the installed command's aggregated output SHA
equals that same digest. This is the only original command effect. Read the
counter after each row and require exactly `1`.

- [ ] **Step 6: Implement supported installed-plugin trust**

In one temporary root:

1. Create `codex-home`, `marketplace`, `workspace`, `bin`, and transient observation paths.
2. Copy the exact plugin tree into the marketplace and verify `tree_sha256` before and after copying.
3. Create the two marketplace JSON files using the same local-marketplace shape as DEV-246, with marketplace `runtime-v1-capability` and plugin `runtime-v1-capability-probe`.
4. Invoke the captured Codex path:

```python
run_json([
    str(codex.resolved),
    "plugin", "marketplace", "add", str(marketplace), "--json",
], environment)
run_json([
    str(codex.resolved),
    "plugin", "add",
    "runtime-v1-capability-probe@runtime-v1-capability",
    "--json",
], environment)
```

5. Start the same captured executable as `codex app-server --stdio --enable hooks` under the isolated `CODEX_HOME`.
6. Send `initialize`, then `initialized`.
7. Call `hooks/list` for the temporary workspace.
8. Require exactly one enabled, unmanaged, plugin-owned `Bash` hook for the expected plugin and compare `currentHash` to `--approved-hook-hash`.
9. Call `config/batchWrite` with the values returned by `hooks/list`:

```python
rpc.call(
    "config/batchWrite",
    {
        "edits": [{
            "keyPath": "hooks.state",
            "value": {
                hook["key"]: {
                    "trusted_hash": hook["currentHash"],
                },
            },
            "mergeStrategy": "upsert",
        }],
        "reloadUserConfig": True,
    },
)
```

10. Call `hooks/list` again and require the same key/hash plus `trustStatus = trusted`.
11. Shut down app-server and recheck the captured executable.

Implement JSON-RPC over JSONL with `selectors.DefaultSelector` and a 30-second read deadline. Ignore notifications, but reject malformed JSON, duplicate response IDs, stderr, early exit, or a mismatched response ID.

- [ ] **Step 7: Invoke the exact CLI in direct mode**

Use this argument structure:

```python
provider = (
    'model_providers.runtime-v1-local={'
    f'name="runtime-v1-local",base_url="{server_url}/v1",'
    'env_key="RUNTIME_V1_LOCAL_PROVIDER_KEY",'
    'wire_api="responses",requires_openai_auth=false,'
    'supports_websockets=false}'
)
arguments = [
    "exec",
    "--ephemeral",
    "--json",
    "--strict-config",
    "--skip-git-repo-check",
    "--enable", "hooks",
    "--disable", "code_mode",
    "--disable", "code_mode_only",
    "-c", provider,
    "-c", 'model_provider="runtime-v1-local"',
    "-c", 'approval_policy="never"',
    "-m", "gpt-5.1-codex",
    "-s", "danger-full-access",
    "-C", str(workspace),
    "Run the one approved synthetic unittest command exactly once.",
]
```

Do not add the hook-trust bypass flag. Set only controlled environment values
needed by the fixture, including the captured Python path, compiled/fake bridge
path, isolated home, command counter, observation path, repository root, exact
approved workspace, approved stimulus SHA-256, `PYTHON_COLORS=0`,
`NO_COLOR=1`, and `RUNTIME_V1_LOCAL_PROVIDER_KEY=local-probe`.

Before accepting the row, inspect the first in-memory provider request and require a direct `shell_command` tool declaration and no code-mode tool declaration. Inspect the second request's `function_call_output` for `call-runtime-v1`; hash the exact output transiently and discard the body.

- [ ] **Step 8: Implement normalized row classification**

Add these closed row keys:

```text
id, status, reason, bridgeKind, commandExecutions, hookInvocations,
appleAttempts, appleValidResults, providerRequests,
additionalParentModelTurns, originalSha256, hookInputSha256, replacementSha256,
nextRequestOutputSha256, originalAbsentFromNextRequest,
replacementPresentInNextRequest, originalPreserved,
replacementBytes, spooled, cleanupStatus
```

Rules:

```python
def classify_row(
    *,
    row_id: str,
    bridge_kind: str,
    stimulus: bytes,
    approved_stimulus_sha256: str,
    hook_input_sha256: str | None,
    replacement_sha256: str | None,
    next_output: bytes,
    baseline_provider_requests: int,
    provider_requests: int,
    command_executions: int,
    hook_invocations: int,
    apple_attempts: int,
    apple_valid_results: int = 0,
    cleanup_status: str = "complete",
) -> dict[str, object]:
    if (
        not stimulus
        or not re.fullmatch(r"[0-9a-f]{64}", approved_stimulus_sha256)
    ):
        raise ProbeFailure("stimulus_grant_invalid")
    original_sha256 = hashlib.sha256(stimulus).hexdigest()
    expected_grant_match = row_id != "decline_unapproved_stimulus"
    grant_matches = original_sha256 == approved_stimulus_sha256
    expected_hook_invocations = (
        0 if row_id == "plugin_off_baseline" else 1
    )
    hook_input_matches = (
        hook_input_sha256 is None
        if expected_hook_invocations == 0
        else hook_input_sha256 == original_sha256
    )
    next_sha256 = hashlib.sha256(next_output).hexdigest()
    added_turns = max(
        provider_requests - baseline_provider_requests,
        0,
    )
    if replacement_sha256 is not None:
        original_absent = (
            stimulus not in next_output
            and b"RUNTIME_V1_ORIGINAL_SENTINEL" not in next_output
        )
        replacement_present = next_sha256 == replacement_sha256
        original_preserved = False
        replacement_bytes = len(next_output)
        spooled = not replacement_present
        core_passed = (
            command_executions == 1
            and hook_invocations == expected_hook_invocations == 1
            and hook_input_matches
            and grant_matches is True
            and provider_requests == baseline_provider_requests == 2
            and added_turns == 0
            and original_absent is True
            and replacement_present is True
            and replacement_bytes <= 4096
            and spooled is False
        )
        if not core_passed:
            status, reason = "fail", "replacement_invariant_failed"
        elif cleanup_status != "complete":
            status, reason = "blocked", "cleanup_incomplete"
        else:
            status, reason = "pass", "replacement_observed"
    else:
        original_absent = False
        replacement_present = False
        envelope = re.fullmatch(
            rb"Exit code: 0\n"
            rb"Wall time: (?:0|[1-9][0-9]*)(?:\.[0-9]+)? seconds\n"
            rb"Output:\n"
            + re.escape(stimulus),
            next_output,
        )
        original_preserved = envelope is not None
        replacement_bytes = 0
        spooled = False
        core_passed = (
            command_executions == 1
            and hook_invocations == expected_hook_invocations
            and hook_input_matches
            and grant_matches is expected_grant_match
            and provider_requests == baseline_provider_requests == 2
            and added_turns == 0
            and original_preserved
        )
        if not core_passed:
            status, reason = "fail", "untouched_original_invariant_failed"
        elif cleanup_status != "complete":
            status, reason = "blocked", "cleanup_incomplete"
        else:
            status, reason = "pass", "untouched_original_observed"
    return {
        "id": row_id,
        "status": status,
        "reason": reason,
        "bridgeKind": bridge_kind,
        "commandExecutions": command_executions,
        "hookInvocations": hook_invocations,
        "appleAttempts": apple_attempts,
        "appleValidResults": apple_valid_results,
        "providerRequests": provider_requests,
        "additionalParentModelTurns": added_turns,
        "originalSha256": original_sha256,
        "hookInputSha256": hook_input_sha256,
        "replacementSha256": replacement_sha256,
        "nextRequestOutputSha256": next_sha256,
        "originalAbsentFromNextRequest": original_absent,
        "replacementPresentInNextRequest": replacement_present,
        "originalPreserved": original_preserved,
        "replacementBytes": replacement_bytes,
        "spooled": spooled,
        "cleanupStatus": cleanup_status,
    }
```

For plugin-on fallback rows, require the hook-input SHA to equal that row's
observed synthetic-result SHA and the next request to contain exactly Codex's
normal `Exit code`/`Wall time`/`Output` envelope around those same bytes. Every
row except `decline_unapproved_stimulus` must match the approved stimulus
grant; that decline must differ from it.
Require `originalPreserved=true`, no replacement, one command, no second Apple
attempt, and two provider requests. The dynamic wall-time value is accepted;
no prefix, suffix, truncation marker, feedback, or changed raw byte is.

- [ ] **Step 9: Run deterministic harness GREEN checks**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_codex_runtime_v1_capability_probe.HarnessTests -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_codex_runtime_v1_capability_probe \
  tests.test_codex_result_replacement_probe \
  tests.test_dev_142_contract -v
```

Expected: PASS without invoking the installed Codex CLI or Apple model; fake executables and loopback servers only.

- [ ] **Step 10: Commit the harness checkpoint**

```bash
git add \
  tests/e2e/codex_runtime_v1_capability_probe.py \
  tests/test_codex_runtime_v1_capability_probe.py
git commit -m "test: add installed Codex boundary harness"
```

### Task 4: Execute the live gate and publish normalized evidence

**Files:**
- Create: `fixtures/runtime-v1-capability/README.md`
- Create: `docs/research/evidence/runtime-v1-capability-gate.json`
- Create: `docs/research/runtime-v1-capability-gate.md`
- Modify: `tests/e2e/codex_runtime_v1_capability_probe.py`
- Modify: `tests/test_codex_runtime_v1_capability_probe.py`

**Interfaces:**
- Consumes: all Task 1–3 artifacts, explicit executable paths, owner-approved plugin/hook hashes, SDK 26.5, and local model prerequisites.
- Produces: one safe capability verdict. Only `status=pass` may authorize a separate production-runtime issue.

- [ ] **Step 1: Add the closed gate normalizer tests**

Define top-level keys:

```text
schemaVersion, gate, status, reason, codexVersion, codexExecutable,
sdkVersion, swiftVersion, pluginSha256, hookCurrentHash,
hookTrustStatus, approvedStimulusSha256, contextClassification,
contextGrantStatus, directToolMode, codeModeEnabled, rows,
unsafeCommittedEvidenceFindings, cleanupStatus
```

Require these row IDs:

```text
plugin_off_baseline
direct_fake_applied
composed_live_apple_applied
decline_unapproved_stimulus
bridge_malformed
bridge_crash
adapter_crash
hook_timeout
```

Add tests proving:

```text
all prerequisites plus all rows pass -> pass:capability_proven
missing CLI -> blocked:missing_binary_or_version_mismatch
missing SDK/compiler -> blocked:sdk_26_5_unavailable
missing model/hardware -> blocked:apple_unavailable
unsupported locale -> blocked:locale_unsupported
missing trust -> blocked:hook_trust_unavailable
direct or composed replacement invariant violated -> fail:replacement_invariant_failed
fallback original differs -> fail:untouched_original_invariant_failed
hook input differs from its row original -> fail:hook_input_invariant_failed
stimulus grant match is wrong for the row -> fail:context_grant_invariant_failed
commandExecutions != 1 -> fail:command_execution_invariant_failed
composed Apple attempts != 1 -> fail:apple_attempt_invariant_failed
extra parent turn -> fail:parent_turn_invariant_failed
unsafe evidence -> fail:evidence_safety_failed
cleanup failure -> blocked:cleanup_incomplete
unknown top-level or row key -> exception; never normalized away
```

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_codex_runtime_v1_capability_probe.GateNormalizerTests -v
```

Expected: FAIL because the gate normalizer is not defined.

- [ ] **Step 2: Implement the gate normalizer, add inspection mode, and stop for hash approval**

Use this derived status order:

```python
REQUIRED_ROW_IDS = (
    "plugin_off_baseline",
    "direct_fake_applied",
    "composed_live_apple_applied",
    "decline_unapproved_stimulus",
    "bridge_malformed",
    "bridge_crash",
    "adapter_crash",
    "hook_timeout",
)
FALLBACK_ROW_IDS = REQUIRED_ROW_IDS[3:]
ALLOWED_BLOCKERS = {
    "missing_binary_or_version_mismatch",
    "sdk_26_5_unavailable",
    "apple_unavailable",
    "locale_unsupported",
    "hook_trust_unavailable",
    "cleanup_incomplete",
}


def derive_gate_status(
    rows: list[dict[str, object]],
    *,
    approved_stimulus_sha256: str,
    blocker_reason: str | None,
    unsafe_findings: int,
    cleanup_status: str,
) -> tuple[str, str]:
    identities = [row["id"] for row in rows]
    if len(identities) != len(set(identities)):
        raise ProbeFailure("duplicate_row")
    by_id = {row["id"]: row for row in rows}
    if unsafe_findings != 0:
        return "fail", "evidence_safety_failed"
    if any(row["commandExecutions"] != 1 for row in rows):
        return "fail", "command_execution_invariant_failed"
    if any(row["additionalParentModelTurns"] != 0 for row in rows):
        return "fail", "parent_turn_invariant_failed"
    for row in rows:
        expected_hook_sha = (
            None
            if row["id"] == "plugin_off_baseline"
            else row["originalSha256"]
        )
        if row["hookInputSha256"] != expected_hook_sha:
            return "fail", "hook_input_invariant_failed"
        expected_grant_match = (
            row["id"] != "decline_unapproved_stimulus"
        )
        if (
            row["originalSha256"] == approved_stimulus_sha256
        ) is not expected_grant_match:
            return "fail", "context_grant_invariant_failed"
    for row_id in ("direct_fake_applied", "composed_live_apple_applied"):
        row = by_id.get(row_id)
        if row is not None and (
            row["originalAbsentFromNextRequest"] is not True
            or row["replacementPresentInNextRequest"] is not True
            or row["spooled"] is not False
            or row["status"] == "fail"
        ):
            return "fail", "replacement_invariant_failed"
    composed = by_id.get("composed_live_apple_applied")
    if composed is not None and (
        composed["appleAttempts"] != 1
        or composed["appleValidResults"] != 1
    ):
        return "fail", "apple_attempt_invariant_failed"
    for row_id in FALLBACK_ROW_IDS:
        row = by_id.get(row_id)
        if row is not None and (
            row["originalPreserved"] is not True
            or row["replacementPresentInNextRequest"] is not False
            or row["status"] == "fail"
        ):
            return "fail", "untouched_original_invariant_failed"
    if cleanup_status != "complete":
        return "blocked", "cleanup_incomplete"
    if blocker_reason is not None:
        if blocker_reason not in ALLOWED_BLOCKERS:
            raise ProbeFailure("blocker_reason_invalid")
        return "blocked", blocker_reason
    if set(by_id) != set(REQUIRED_ROW_IDS):
        return "fail", "incomplete_gate"
    if any(row["status"] != "pass" for row in rows):
        return "fail", "row_failed"
    return "pass", "capability_proven"
```

The evidence builder inserts that returned `status` and `reason`, then enforces
the exact top-level and row key sets before writing.

Add `--inspect-trust` to install the plugin, list the hook, and write only this
runtime-built object:

```python
inspection = {
    "pluginSha256": plugin_sha256,
    "hookCurrentHash": hook["currentHash"],
    "approvedStimulusSha256": approved_stimulus_sha256,
    "contextClassification": "C0",
    "contextGrantStatus": "approved_exact_synthetic_hash",
    "codexVersion": "0.145.0",
    "codexExecutable": "<host-path>",
    "cleanupStatus": "complete",
}
```

Run:

```bash
runtime_v1_codex_path="$(command -v codex)"
runtime_v1_python_path="$(command -v python3)"
runtime_v1_xcrun_path="$(command -v xcrun)"
runtime_v1_swiftc_path="$(command -v swiftc)"
test -n "$runtime_v1_codex_path"
test -n "$runtime_v1_python_path"
test -n "$runtime_v1_xcrun_path"
test -n "$runtime_v1_swiftc_path"

runtime_v1_command_tmp_dir="$(mktemp -d)"
test -d "$runtime_v1_command_tmp_dir"
trap 'rm -rf -- "$runtime_v1_command_tmp_dir"' EXIT
runtime_v1_inspection_file="$runtime_v1_command_tmp_dir/trust.json"
PYTHONDONTWRITEBYTECODE=1 python3 \
  tests/e2e/codex_runtime_v1_capability_probe.py \
  --inspect-trust \
  --codex-executable "$runtime_v1_codex_path" \
  --python-executable "$runtime_v1_python_path" \
  --plugin fixtures/runtime-v1-capability/synthetic-plugin \
  --output "$runtime_v1_inspection_file"
python3 -m json.tool "$runtime_v1_inspection_file"
```

Expected: exact hashes, normalized host identity, the closed C0 grant, and
complete cleanup. Present the plugin, hook, and stimulus hashes with the
reviewed diff to the owner. Do not continue until the owner explicitly
approves those exact values.

After approval, bind the reviewed values without copying raw content:

```bash
runtime_v1_plugin_sha256="$(
  python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["pluginSha256"])' \
  "$runtime_v1_inspection_file"
)"
runtime_v1_hook_hash="$(
  python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["hookCurrentHash"])' \
  "$runtime_v1_inspection_file"
)"
runtime_v1_stimulus_sha256="$(
  python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["approvedStimulusSha256"])' \
  "$runtime_v1_inspection_file"
)"
```

Run the normalizer test again. Expected: PASS before any live host row.

- [ ] **Step 3: Run the baseline and direct fake bridge row**

After hash approval, invoke:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 \
  tests/e2e/codex_runtime_v1_capability_probe.py \
  --codex-executable "$runtime_v1_codex_path" \
  --python-executable "$runtime_v1_python_path" \
  --xcrun-executable "$runtime_v1_xcrun_path" \
  --swiftc-executable "$runtime_v1_swiftc_path" \
  --plugin fixtures/runtime-v1-capability/synthetic-plugin \
  --approved-plugin-sha256 "$runtime_v1_plugin_sha256" \
  --approved-hook-hash "$runtime_v1_hook_hash" \
  --approved-stimulus-sha256 "$runtime_v1_stimulus_sha256" \
  --through direct \
  --output docs/research/evidence/runtime-v1-capability-gate.json
```

Expected: `plugin_off_baseline` and `direct_fake_applied` pass. The direct row
must show the hook-input SHA equals the approved original SHA, original absent,
fake replacement present, no spooling, one command, one hook, zero Apple
attempts, two provider requests, and zero additional parent turns. Otherwise
write `blocked`/`fail`, clean up, and stop.

- [ ] **Step 4: Compile and run the one real composed Apple row**

The harness compiles the installed plugin copy of `DiagnosticCondenser.swift` into the same temporary root, verifies SDK `26.5` and Swift `6.3.3`, and then runs one fresh Codex task with that exact executable.

Continue:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 \
  tests/e2e/codex_runtime_v1_capability_probe.py \
  --codex-executable "$runtime_v1_codex_path" \
  --python-executable "$runtime_v1_python_path" \
  --xcrun-executable "$runtime_v1_xcrun_path" \
  --swiftc-executable "$runtime_v1_swiftc_path" \
  --plugin fixtures/runtime-v1-capability/synthetic-plugin \
  --approved-plugin-sha256 "$runtime_v1_plugin_sha256" \
  --approved-hook-hash "$runtime_v1_hook_hash" \
  --approved-stimulus-sha256 "$runtime_v1_stimulus_sha256" \
  --through composed \
  --output docs/research/evidence/runtime-v1-capability-gate.json
```

Required composed row:

```text
commandExecutions = 1
hookInvocations = 1
hookInputSha256 = originalSha256
appleAttempts = 1
appleValidResults = 1
providerRequests = 2
additionalParentModelTurns = 0
originalAbsentFromNextRequest = true
replacementPresentInNextRequest = true
replacementBytes <= 4096
spooled = false
cleanupStatus = complete
```

The exact next-request function output SHA must equal the adapter's transient replacement SHA. A model-ready or hardware prerequisite failure is `blocked`; invalid Apple content or any count mismatch is `fail`. Neither authorizes fallback architecture or production work.

If the Apple model, locale, or hardware prerequisite is unavailable, do not
emit a `composed_live_apple_applied` row. Set the matching top-level blocker,
verify cleanup, and stop. A composed row exists only after one real Apple
attempt returns one schema-valid result, so an attempted invalid result is a
failure rather than a prerequisite blocker.

- [ ] **Step 5: Run the untouched-original failure matrix**

Using fresh ephemeral Codex tasks under the same approved isolated install, run:

```text
decline_unapproved_stimulus -> exact command emits a different safe synthetic result; digest grant declines before Apple
bridge_malformed -> fake bridge returns a non-closed object
bridge_crash -> fake bridge exits nonzero
adapter_crash -> repository-only fault after original digest observation
hook_timeout -> temporary marketplace copy changes only hook timeout to 1 second; adapter sleeps 61 seconds after original digest observation
```

For the timeout derivative, compute and record its distinct plugin hash and trust its distinct discovered hook hash through the same explicit owner-approved procedure. Do not reuse the success-row trust hash.

Inspect the derivative without running a task:

```bash
runtime_v1_timeout_inspection_file="$runtime_v1_command_tmp_dir/timeout-trust.json"
PYTHONDONTWRITEBYTECODE=1 python3 \
  tests/e2e/codex_runtime_v1_capability_probe.py \
  --inspect-trust \
  --hook-timeout-seconds 1 \
  --codex-executable "$runtime_v1_codex_path" \
  --python-executable "$runtime_v1_python_path" \
  --plugin fixtures/runtime-v1-capability/synthetic-plugin \
  --output "$runtime_v1_timeout_inspection_file"
python3 -m json.tool "$runtime_v1_timeout_inspection_file"
```

Present the derivative plugin and hook hashes to the owner. After explicit
approval, bind them and run the complete matrix:

```bash
runtime_v1_timeout_plugin_sha256="$(
  python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["pluginSha256"])' \
  "$runtime_v1_timeout_inspection_file"
)"
runtime_v1_timeout_hook_hash="$(
  python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["hookCurrentHash"])' \
  "$runtime_v1_timeout_inspection_file"
)"

PYTHONDONTWRITEBYTECODE=1 python3 \
  tests/e2e/codex_runtime_v1_capability_probe.py \
  --codex-executable "$runtime_v1_codex_path" \
  --python-executable "$runtime_v1_python_path" \
  --xcrun-executable "$runtime_v1_xcrun_path" \
  --swiftc-executable "$runtime_v1_swiftc_path" \
  --plugin fixtures/runtime-v1-capability/synthetic-plugin \
  --approved-plugin-sha256 "$runtime_v1_plugin_sha256" \
  --approved-hook-hash "$runtime_v1_hook_hash" \
  --approved-stimulus-sha256 "$runtime_v1_stimulus_sha256" \
  --approved-timeout-plugin-sha256 "$runtime_v1_timeout_plugin_sha256" \
  --approved-timeout-hook-hash "$runtime_v1_timeout_hook_hash" \
  --through complete \
  --output docs/research/evidence/runtime-v1-capability-gate.json
```

Every row must show:

```text
commandExecutions = 1
providerRequests = 2
additionalParentModelTurns = 0
hookInputSha256 = originalSha256 for plugin-on rows
originalPreserved = true
replacementPresentInNextRequest = false
appleAttempts <= 1
cleanupStatus = complete
```

Any mismatch is `fail:untouched_original_invariant_failed`.

- [ ] **Step 6: Write only normalized evidence**

The final evidence writer must:

1. Build the closed top-level object and closed rows.
2. Reject strings matching private absolute paths, credential forms, prompt/result/transcript keys, or the original sentinel.
3. Require every digest/hash field to match its declared SHA-256 form.
4. Require C0 synthetic classification for the stimulus and no raw-content field.
5. Discard every provider body, hook input, diagnostic, and Apple response
   before writing. Attempt isolated-directory and compiled-binary cleanup, and
   record `cleanupStatus=complete` only when those removals succeed. A cleanup
   failure may write only the normalized `blocked:cleanup_incomplete` record;
   it must never copy remaining temporary content into the repository.

Use `atomic_write_json`; do not write intermediate raw evidence under the repository.

- [ ] **Step 7: Add the bounded README and interpretation**

`fixtures/runtime-v1-capability/README.md` must state:

- this is a repository-only successor gate, not production runtime;
- exact commands and explicit hash trust;
- direct mode only;
- the loopback server is deterministic and non-generative;
- one command and one Apple attempt budgets;
- no-output fallback semantics;
- blocker/fail precedence;
- transient data and cleanup policy; and
- `pass` authorizes planning a separate production issue, not production implementation.

`docs/research/runtime-v1-capability-gate.md` must record the normalized verdict, exact evidence file hash, what was and was not proven, and the stop decision. Do not quote provider, tool, or Apple content.

- [ ] **Step 8: Run evidence safety and repository gates**

Run:

```bash
python3 -m json.tool \
  docs/research/evidence/runtime-v1-capability-gate.json >/dev/null

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_codex_runtime_v1_capability_probe \
  tests.test_codex_result_replacement_probe \
  tests.test_dev_142_contract -v

python3 scripts/sync_generated_artifacts.py --check
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests -p 'test_*.py' -v
git diff --check
git status --short
```

Expected: JSON valid; focused and full tests PASS; generated artifacts synchronized; diff clean; status contains only the nine capability-gate paths. A skipped live prerequisite remains `blocked` in evidence and is never reported as a pass.

- [ ] **Step 9: Review against the conjunctive acceptance gate**

Confirm all thirteen successor-gate criteria from the design spec map to a normalized assertion:

```text
exact CLI -> top-level codexVersion plus executable rechecks
direct/code mode -> directToolMode=true, codeModeEnabled=false
isolated install/trust -> plugin hash plus trusted hook hash
one command -> commandExecutions=1 in every host row
original reaches hook -> hookInputSha256 equals originalSha256 plus hookInvocations=1
real Apple response -> composed appleAttempts=1 and appleValidResults=1
DEV-142 validity -> adapter validates complete applied result
replacement reaches next request -> exact replacement SHA equality
original absent on success -> originalAbsentFromNextRequest=true
zero added turns -> two requests in both baseline and on rows
fallback untouched -> exact original SHA equality in all failure rows
inline delivery -> replacementBytes<=4096 and spooled=false
privacy/cleanup -> zero unsafe findings and cleanup complete
```

If any mapping is absent, add the missing assertion before committing; do not weaken the design.

- [ ] **Step 10: Commit the completed or truthfully blocked gate**

```bash
git add \
  fixtures/runtime-v1-capability \
  tests/e2e/codex_runtime_v1_capability_probe.py \
  tests/test_codex_runtime_v1_capability_probe.py \
  docs/research/evidence/runtime-v1-capability-gate.json \
  docs/research/runtime-v1-capability-gate.md
git commit -m "test: record Runtime V1 capability gate"
```

Stop after the commit and request user review. Do not create or update Linear and do not begin production runtime planning, even when the result is `pass`.

## Execution Boundary

This plan deliberately ends at the successor capability verdict:

- `pass` permits a new, separately approved production Runtime V1 plan.
- `blocked` keeps production work stopped until the named prerequisite changes.
- `fail` rejects the selected architecture on the tested host and returns to product design.

DEV-143, DEV-144, DEV-139, DEV-140, DEV-141, and DEV-145 remain canceled in every outcome until the user separately approves new issue treatment.
