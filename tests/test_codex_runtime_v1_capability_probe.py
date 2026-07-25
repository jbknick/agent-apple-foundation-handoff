import hashlib
import importlib.util
import json
import os
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
                self.assertEqual(
                    completed[0]["reasonCode"],
                    consultation["reasonCode"],
                )

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

    def test_harness_compiles_bridge_without_invoking_it(self):
        harness = load_module("runtime_v1_compile_harness", HARNESS)
        xcrun = shutil.which("xcrun")
        swiftc = shutil.which("swiftc")
        if xcrun is None or swiftc is None:
            self.skipTest("blocked/missing_swift_toolchain")
        with tempfile.TemporaryDirectory() as directory:
            executable = harness.compile_swift_bridge(
                xcrun=Path(xcrun),
                swiftc=Path(swiftc),
                source=SWIFT_SOURCE,
                output=Path(directory) / "DiagnosticCondenser",
            )
            self.assertTrue(executable.is_file())
            self.assertTrue(executable.stat().st_mode & 0o100)


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

    def test_fake_bridge_modes_are_process_real(self):
        python = Path(shutil.which("python3"))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for mode in ("valid", "malformed", "crash"):
                with self.subTest(mode=mode):
                    bridge = self.harness.materialize_fake_bridge(
                        root / mode,
                        python,
                        mode,
                    )
                    completed = subprocess.run(
                        [str(bridge)],
                        input=b'{"diagnosticText":"safe"}',
                        capture_output=True,
                        check=False,
                    )
                    if mode == "crash":
                        self.assertNotEqual(completed.returncode, 0)
                    elif mode == "malformed":
                        self.assertEqual(completed.stdout, b"{}\n")
                    else:
                        self.assertEqual(
                            json.loads(completed.stdout)["status"],
                            "applied",
                        )

    def test_failure_matrix_configuration_is_closed(self):
        expected = {
            "plugin_off_baseline": (False, "valid", "none", False, False),
            "direct_fake_applied": (True, "valid", "none", False, False),
            "composed_live_apple_applied": (
                True,
                "apple",
                "none",
                False,
                False,
            ),
            "decline_unapproved_stimulus": (
                True,
                "valid",
                "none",
                True,
                False,
            ),
            "bridge_malformed": (
                True,
                "malformed",
                "none",
                False,
                False,
            ),
            "bridge_crash": (True, "crash", "none", False, False),
            "adapter_crash": (
                True,
                "valid",
                "adapter_crash",
                False,
                False,
            ),
            "hook_timeout": (
                True,
                "valid",
                "hook_timeout",
                False,
                True,
            ),
        }
        for row_id, values in expected.items():
            with self.subTest(row_id=row_id):
                config = self.harness.row_configuration(row_id)
                self.assertEqual(
                    (
                        config["pluginEnabled"],
                        config["bridgeMode"],
                        config["faultMode"],
                        config["unapprovedStimulus"],
                        config["timeoutPlugin"],
                    ),
                    values,
                )

    def test_row_collection_stops_at_first_non_pass(self):
        calls = []

        def runner(row_id, baseline):
            calls.append((row_id, baseline))
            return {
                "id": row_id,
                "status": (
                    "fail"
                    if row_id == "direct_fake_applied"
                    else "pass"
                ),
                "providerRequests": 2,
            }

        rows = self.harness.collect_rows("complete", runner)
        self.assertEqual(
            [row["id"] for row in rows],
            ["plugin_off_baseline", "direct_fake_applied"],
        )
        self.assertEqual(calls, [
            ("plugin_off_baseline", 2),
            ("direct_fake_applied", 2),
        ])

    def test_workspace_variants_match_precomputed_stimuli(self):
        python = Path(shutil.which("python3"))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for unapproved in (False, True):
                workspace = root / str(unapproved)
                self.harness.materialize_workspace(
                    workspace,
                    unapproved=unapproved,
                )
                environment = {
                    **os.environ,
                    "NO_COLOR": "1",
                    "PYTHON_COLORS": "0",
                    "RUNTIME_V1_COMMAND_COUNTER": str(
                        root / f"counter-{unapproved}"
                    ),
                }
                completed = subprocess.run(
                    [
                        str(python),
                        "-m",
                        "unittest",
                        "-q",
                        "diagnostic_fixture",
                    ],
                    cwd=workspace,
                    env=environment,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(completed.returncode, 0)
                self.assertEqual(
                    completed.stdout + completed.stderr,
                    self.harness.stimulus_bytes(
                        unapproved=unapproved
                    ),
                )
        self.assertEqual(
            self.harness.stimulus_for_row(
                "decline_unapproved_stimulus"
            ),
            self.harness.stimulus_bytes(unapproved=True),
        )


class GateNormalizerTests(unittest.TestCase):
    APPROVED = "a" * 64

    def setUp(self):
        self.harness = load_module("runtime_v1_gate", HARNESS)

    def row(self, row_id):
        replacement = row_id in {
            "direct_fake_applied",
            "composed_live_apple_applied",
        }
        original = (
            "b" * 64
            if row_id == "decline_unapproved_stimulus"
            else self.APPROVED
        )
        return {
            "id": row_id,
            "status": "pass",
            "reason": (
                "replacement_observed"
                if replacement
                else "untouched_original_observed"
            ),
            "bridgeKind": "synthetic",
            "commandExecutions": 1,
            "hookInvocations": (
                0 if row_id == "plugin_off_baseline" else 1
            ),
            "appleAttempts": (
                1 if row_id == "composed_live_apple_applied" else 0
            ),
            "appleValidResults": (
                1 if row_id == "composed_live_apple_applied" else 0
            ),
            "providerRequests": 2,
            "additionalParentModelTurns": 0,
            "originalSha256": original,
            "hookInputSha256": (
                None if row_id == "plugin_off_baseline" else original
            ),
            "replacementSha256": "c" * 64 if replacement else None,
            "nextRequestOutputSha256": "d" * 64,
            "originalAbsentFromNextRequest": replacement,
            "replacementPresentInNextRequest": replacement,
            "originalPreserved": not replacement,
            "replacementBytes": 512 if replacement else 0,
            "spooled": False,
            "cleanupStatus": "complete",
        }

    def rows(self):
        return [
            self.row(row_id)
            for row_id in self.harness.REQUIRED_ROW_IDS
        ]

    def derive(
        self,
        rows=None,
        *,
        blocker_reason=None,
        unsafe_findings=0,
        cleanup_status="complete",
    ):
        return self.harness.derive_gate_status(
            self.rows() if rows is None else rows,
            approved_stimulus_sha256=self.APPROVED,
            blocker_reason=blocker_reason,
            unsafe_findings=unsafe_findings,
            cleanup_status=cleanup_status,
        )

    def evidence(self):
        return {
            "schemaVersion": 1,
            "gate": "runtime-v1-successor-capability",
            "status": "pass",
            "reason": "capability_proven",
            "codexVersion": "0.145.0",
            "codexExecutable": "<host-path>",
            "sdkVersion": "26.5",
            "swiftVersion": "6.3.3",
            "pluginSha256": "e" * 64,
            "hookCurrentHash": "sha256:" + ("f" * 64),
            "hookTrustStatus": "trusted",
            "approvedStimulusSha256": self.APPROVED,
            "contextClassification": "C0",
            "contextGrantStatus": "approved_exact_synthetic_hash",
            "directToolMode": True,
            "codeModeEnabled": False,
            "rows": self.rows(),
            "unsafeCommittedEvidenceFindings": 0,
            "cleanupStatus": "complete",
        }

    def test_complete_gate_passes(self):
        self.assertEqual(self.derive(), ("pass", "capability_proven"))

    def test_declared_prerequisite_blockers_remain_blocked(self):
        for reason in (
            "missing_binary_or_version_mismatch",
            "sdk_26_5_unavailable",
            "apple_unavailable",
            "locale_unsupported",
            "hook_trust_unavailable",
        ):
            with self.subTest(reason=reason):
                self.assertEqual(
                    self.derive(blocker_reason=reason),
                    ("blocked", reason),
                )

    def test_invariant_failures_are_not_normalized_away(self):
        mutations = (
            (
                "replacement_invariant_failed",
                "direct_fake_applied",
                "originalAbsentFromNextRequest",
                False,
            ),
            (
                "untouched_original_invariant_failed",
                "bridge_crash",
                "originalPreserved",
                False,
            ),
            (
                "hook_input_invariant_failed",
                "bridge_crash",
                "hookInputSha256",
                "0" * 64,
            ),
            (
                "context_grant_invariant_failed",
                "decline_unapproved_stimulus",
                "originalSha256",
                self.APPROVED,
            ),
            (
                "command_execution_invariant_failed",
                "bridge_crash",
                "commandExecutions",
                2,
            ),
            (
                "apple_attempt_invariant_failed",
                "composed_live_apple_applied",
                "appleAttempts",
                0,
            ),
            (
                "parent_turn_invariant_failed",
                "bridge_crash",
                "additionalParentModelTurns",
                1,
            ),
        )
        for expected, row_id, key, value in mutations:
            rows = self.rows()
            row = next(row for row in rows if row["id"] == row_id)
            row[key] = value
            if key == "originalSha256":
                row["hookInputSha256"] = value
            with self.subTest(reason=expected):
                self.assertEqual(self.derive(rows)[1], expected)

    def test_safety_and_cleanup_precedence(self):
        self.assertEqual(
            self.derive(unsafe_findings=1),
            ("fail", "evidence_safety_failed"),
        )
        self.assertEqual(
            self.derive(cleanup_status="incomplete"),
            ("blocked", "cleanup_incomplete"),
        )

    def test_unknown_evidence_or_row_key_is_rejected(self):
        for target in ("evidence", "row"):
            value = self.evidence()
            if target == "evidence":
                value["unknown"] = True
            else:
                value["rows"][0]["unknown"] = True
            with self.subTest(target=target):
                with self.assertRaises(self.harness.ProbeFailure):
                    self.harness.validate_evidence(value)

    def test_inspection_record_is_closed_and_normalized(self):
        value = self.harness.inspection_record(
            plugin_sha256="1" * 64,
            hook_current_hash="sha256:" + ("2" * 64),
            approved_stimulus_sha256="3" * 64,
            cleanup_status="complete",
        )
        self.assertEqual(
            set(value),
            {
                "pluginSha256",
                "hookCurrentHash",
                "approvedStimulusSha256",
                "contextClassification",
                "contextGrantStatus",
                "codexVersion",
                "codexExecutable",
                "cleanupStatus",
            },
        )
        self.assertNotIn(str(ROOT), json.dumps(value))

    def test_outer_gate_prefix_and_evidence_are_closed(self):
        self.assertEqual(
            self.harness.phases_for("direct"),
            (
                "plugin_off_baseline",
                "direct_fake_applied",
            ),
        )
        self.assertEqual(
            self.harness.phases_for("composed"),
            self.harness.REQUIRED_ROW_IDS[:3],
        )
        value = self.harness.build_evidence(
            rows=self.rows(),
            approved_stimulus_sha256=self.APPROVED,
            plugin_sha256="e" * 64,
            hook_current_hash="sha256:" + ("f" * 64),
            blocker_reason=None,
            cleanup_status="complete",
        )
        self.assertEqual(value["status"], "pass")
        self.assertEqual(set(value), set(self.harness.EVIDENCE_KEYS))

    def test_outer_parser_requires_reviewed_gate_inputs(self):
        options = self.harness._parse_arguments(
            [
                "--codex-executable",
                "/bin/true",
                "--python-executable",
                "/bin/true",
                "--xcrun-executable",
                "/bin/true",
                "--swiftc-executable",
                "/bin/true",
                "--plugin",
                "plugin",
                "--approved-plugin-sha256",
                "a" * 64,
                "--approved-hook-hash",
                "sha256:" + ("b" * 64),
                "--approved-stimulus-sha256",
                "c" * 64,
                "--through",
                "direct",
                "--output",
                "evidence.json",
            ]
        )
        self.assertEqual(options.through, "direct")
        self.harness.validate_outer_options(options)
        options.approved_hook_hash = None
        with self.assertRaises(self.harness.ProbeFailure):
            self.harness.validate_outer_options(options)
