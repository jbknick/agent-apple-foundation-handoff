import hashlib
import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADAPTER = (
    ROOT
    / "fixtures/runtime-v1-capability/synthetic-plugin"
    / "hooks/codex/probe.py"
)
CONTRACT = ROOT / "fixtures/dev-142/runtime_contract.py"
SWIFT_SOURCE = (
    ROOT
    / "fixtures/runtime-v1-capability/synthetic-plugin"
    / "runtime/DiagnosticCondenser.swift"
)
HARNESS = ROOT / "tests/e2e/codex_runtime_v1_capability_probe.py"


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
        self.assertTrue(ADAPTER.is_file(), "adapter not implemented")
        self.adapter = load_module("runtime_v1_adapter", ADAPTER)
        self.contract = load_module(
            "dev142_contract_for_runtime_v1",
            CONTRACT,
        )

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

    def evaluate(self, output, consult, *, payload=None, observed=None):
        return self.adapter.evaluate(
            hook_payload(output) if payload is None else payload,
            contract=self.contract,
            consult=consult,
            repo_root=ROOT,
            approved_stimulus_sha256=hashlib.sha256(
                output.encode("utf-8")
            ).hexdigest(),
            observe=(
                observed if observed is not None else []
            ).append,
        )

    def applied(self, **changes):
        value = {
            "status": "applied",
            "reasonCode": None,
            "appleAvailable": True,
            "localeSupported": True,
            "contextSize": 4096,
            "occupiedTokens": 2048,
            "appleAttempts": 1,
            "condensation": self.adapter.source_facts(0),
        }
        value.update(changes)
        return value

    def test_applied_consultation_emits_only_stop_reason(self):
        observed = []

        def consult(_request):
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
        self.assertEqual(
            sum(row["event"] == "hook_invoked" for row in observed),
            1,
        )

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

    def test_closed_hook_boundary_declines_before_bridge(self):
        output = self.eligible_output()
        base = hook_payload(output)
        mutations = {
            "unknown key": {**base, "unknown": True},
            "wrong event": {**base, "hook_event_name": "PreToolUse"},
            "wrong tool": {**base, "tool_name": "Read"},
            "wrong call": {**base, "tool_use_id": "call-other"},
            "wrong cwd": {**base, "cwd": str(ROOT.parent)},
            "wrong command": {
                **base,
                "tool_input": {"command": "python3 -m unittest -q other"},
            },
        }
        for label, payload in mutations.items():
            calls = []
            with self.subTest(label=label):
                self.assertIsNone(
                    self.evaluate(output, calls.append, payload=payload)
                )
                self.assertEqual(calls, [])

    def test_wrong_digest_and_sensitive_message_decline_before_bridge(self):
        output = self.eligible_output()
        calls = []
        self.assertIsNone(
            self.adapter.evaluate(
                hook_payload(output),
                contract=self.contract,
                consult=calls.append,
                repo_root=ROOT,
                approved_stimulus_sha256="0" * 64,
                observe=lambda _: None,
            )
        )
        self.assertEqual(calls, [])

        sensitive = output + "/Users/example/private.txt\n"
        self.assertIsNone(self.evaluate(sensitive, calls.append))
        self.assertEqual(calls, [])

    def test_input_size_bounds_decline_before_bridge(self):
        for output in ("short", self.eligible_output() + ("b" * 66000)):
            calls = []
            with self.subTest(size=len(output)):
                self.assertIsNone(self.evaluate(output, calls.append))
                self.assertEqual(calls, [])

    def test_unavailable_locale_and_context_budget_fall_back(self):
        output = self.eligible_output()
        consultations = (
            self.applied(
                status="declined",
                reasonCode="apple_unavailable",
                appleAvailable=False,
                appleAttempts=0,
                condensation=None,
            ),
            self.applied(
                status="declined",
                reasonCode="locale_unsupported",
                localeSupported=False,
                appleAttempts=0,
                condensation=None,
            ),
            self.applied(
                status="declined",
                reasonCode="context_budget_exceeded",
                occupiedTokens=3073,
                appleAttempts=0,
                condensation=None,
            ),
        )
        for consultation in consultations:
            observed = []
            with self.subTest(reason=consultation["reasonCode"]):
                self.assertIsNone(
                    self.evaluate(
                        output,
                        lambda _: deepcopy(consultation),
                        observed=observed,
                    )
                )
                completed = [
                    row
                    for row in observed
                    if row["event"] == "consultation_completed"
                ]
                self.assertEqual(completed[0]["appleAttempts"], 0)

    def test_malformed_or_invalid_consultation_falls_back(self):
        output = self.eligible_output()
        malformed = self.applied()
        malformed["extra"] = True
        invalid = self.applied()
        invalid["condensation"]["summary"] = "invented"
        for consultation in (malformed, invalid):
            with self.subTest(keys=sorted(consultation)):
                self.assertIsNone(
                    self.evaluate(
                        output,
                        lambda _: deepcopy(consultation),
                    )
                )

    def test_oversized_valid_condensation_falls_back(self):
        output = self.eligible_output()
        oversized = self.adapter.source_facts(0)
        oversized["summary"] = "x" * 5000
        original = self.adapter.source_facts
        self.adapter.source_facts = lambda _: deepcopy(oversized)
        try:
            self.assertIsNone(
                self.evaluate(output, lambda _: self.applied())
            )
        finally:
            self.adapter.source_facts = original

    def test_applied_consultation_requires_one_apple_attempt(self):
        output = self.eligible_output()
        self.assertIsNone(
            self.evaluate(
                output,
                lambda _: self.applied(appleAttempts=0),
            )
        )

    def test_observations_never_contain_original_sentinel(self):
        output = self.eligible_output()
        observed = []
        self.assertIsNotNone(
            self.evaluate(
                output,
                lambda _: self.applied(),
                observed=observed,
            )
        )
        self.assertNotIn(
            "RUNTIME_V1_ORIGINAL_SENTINEL",
            json.dumps(observed, sort_keys=True),
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
        self.assertIn(
            "tokenCount(\n"
            "            for: DiagnosticCondensation.generationSchema",
            source,
        )
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
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        if sdk_version.returncode != 0 or sdk_version.stdout != "26.5\n":
            self.skipTest("blocked/sdk_26_5_unavailable")
        sdk_path = subprocess.run(
            [xcrun, "--sdk", "macosx", "--show-sdk-path"],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        ).stdout.strip()
        completed = subprocess.run(
            [
                swiftc,
                "-typecheck",
                "-parse-as-library",
                "-target",
                "arm64-apple-macos26.4",
                "-sdk",
                sdk_path,
                str(SWIFT_SOURCE),
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def hooks_list(current_hash: str, trust_status: str) -> dict[str, object]:
    return {
        "data": [
            {
                "cwd": str(ROOT),
                "hooks": [
                    {
                        "key": (
                            "runtime-v1-capability-probe@"
                            "runtime-v1-capability:"
                            "hooks/codex/hooks.json:post_tool_use:0:0"
                        ),
                        "matcher": "Bash",
                        "handlerType": "command",
                        "source": "plugin",
                        "pluginId": (
                            "runtime-v1-capability-probe@"
                            "runtime-v1-capability"
                        ),
                        "enabled": True,
                        "isManaged": False,
                        "currentHash": current_hash,
                        "trustStatus": trust_status,
                    }
                ],
                "warnings": [],
                "errors": [],
            }
        ]
    }


class FakeRpc:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.methods = []

    def call(self, method, params):
        self.methods.append(method)
        return next(self.responses)


class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(HARNESS.is_file(), "harness not implemented")
        self.harness = load_module("runtime_v1_harness", HARNESS)

    def test_strict_codex_capture_requires_exact_0145(self):
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "codex"
            executable.write_text(
                "#!/bin/sh\nprintf 'codex-cli 0.145.0\\n'\n",
                encoding="utf-8",
            )
            executable.chmod(0o700)
            captured = self.harness.capture_codex(executable)
            captured.recheck()
            executable.write_text(
                "#!/bin/sh\nprintf 'codex-cli 0.146.0\\n'\n",
                encoding="utf-8",
            )
            executable.chmod(0o700)
            with self.assertRaises(self.harness.ProbeFailure):
                captured.recheck()

    def test_trust_uses_list_hash_batch_write_and_readback(self):
        rpc = FakeRpc(
            [
                hooks_list("sha256:reviewed", "untrusted"),
                {},
                hooks_list("sha256:reviewed", "trusted"),
            ]
        )
        result = self.harness.trust_hook(
            rpc,
            cwd=ROOT,
            plugin_id=(
                "runtime-v1-capability-probe@runtime-v1-capability"
            ),
            approved_hash="sha256:reviewed",
        )
        self.assertTrue(result)
        self.assertEqual(
            rpc.methods,
            ["hooks/list", "config/batchWrite", "hooks/list"],
        )

    def test_second_request_contains_replacement_not_original(self):
        row = self.harness.classify_row(
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
        row = self.harness.classify_row(
            row_id="bridge_crash",
            bridge_kind="crash",
            stimulus=stimulus,
            approved_stimulus_sha256=digest(stimulus),
            hook_input_sha256=digest(stimulus),
            replacement_sha256=None,
            next_output=(
                b"Exit code: 0\n"
                b"Wall time: 0.1 seconds\n"
                b"Output:\n"
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
