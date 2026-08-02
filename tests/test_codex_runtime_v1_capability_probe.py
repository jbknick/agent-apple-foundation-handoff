import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock
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
EVIDENCE = (
    ROOT / "docs/research/evidence/runtime-v1-capability-gate.json"
)
INTERPRETATION = ROOT / "docs/research/runtime-v1-capability-gate.md"


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

    def test_actual_applied_observations_match_closed_harness_schema(self):
        observed = []
        output = self.eligible_output()
        response = self.evaluate(
            output,
            lambda _: self.applied(),
            observed=observed,
        )
        self.assertIsNotNone(response)
        replacement = next(
            row
            for row in observed
            if row["event"] == "replacement_emitted"
        )
        self.assertEqual(
            set(replacement),
            {
                "event",
                "callID",
                "replacementSha256",
                "replacementBytes",
                "appleAttempts",
            },
        )
        consultation_index = next(
            index
            for index, row in enumerate(observed)
            if row["event"] == "consultation_completed"
        )
        integrated = observed[:consultation_index]
        integrated.extend(
            [
                {
                    "event": "bridge_process_started",
                    "callID": "call-runtime-v1",
                },
                {
                    "event": "bridge_process_completed",
                    "callID": "call-runtime-v1",
                    "bridgeProcessOutcome": "result_observed",
                },
            ]
        )
        integrated.extend(observed[consultation_index:])
        harness = load_module("runtime_v1_integration_harness", HARNESS)
        self.assertTrue(
            harness.observations_are_closed(
                integrated,
                call_id="call-runtime-v1",
            )
        )
        next_output = response["stopReason"].encode("utf-8")
        self.assertTrue(
            harness.replacement_observation_matches(
                integrated,
                next_output=next_output,
                bridge_process_outcome="result_observed",
            )
        )
        mutations = {
            "missing": lambda rows: rows.pop(),
            "duplicate": lambda rows: rows.append(dict(rows[-1])),
            "byte mismatch": lambda rows: rows[-1].update(
                replacementBytes=len(next_output) + 1
            ),
            "digest mismatch": lambda rows: rows[-1].update(
                replacementSha256="0" * 64
            ),
            "attempt mismatch": lambda rows: rows[-1].update(
                appleAttempts=0
            ),
        }
        for label, mutate in mutations.items():
            changed = deepcopy(integrated)
            mutate(changed)
            with self.subTest(label=label):
                self.assertFalse(
                    harness.replacement_observation_matches(
                        changed,
                        next_output=next_output,
                        bridge_process_outcome="result_observed",
                    )
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

    def test_semantic_rejection_is_observed_after_validation(self):
        output = self.eligible_output()
        invalid = self.applied()
        invalid["condensation"]["summary"] = "invented"
        observed = []

        self.assertIsNone(
            self.evaluate(
                output,
                lambda _: deepcopy(invalid),
                observed=observed,
            )
        )

        completed = [
            row
            for row in observed
            if row["event"] == "consultation_completed"
        ]
        self.assertEqual(
            completed,
            [
                {
                    "event": "consultation_completed",
                    "callID": "call-runtime-v1",
                    "appleAttempts": 1,
                    "appleValidResults": 0,
                    "reasonCode": "contract_invariant_failed",
                }
            ],
        )
        self.assertFalse(
            any(
                row["event"] == "replacement_emitted"
                for row in observed
            )
        )

    def test_route_exception_is_a_closed_semantic_failure(self):
        output = self.eligible_output()
        observed = []

        with mock.patch.object(
            self.contract,
            "route",
            side_effect=RuntimeError("private synthetic detail"),
        ):
            self.assertIsNone(
                self.evaluate(
                    output,
                    lambda _: self.applied(),
                    observed=observed,
                )
            )

        completed = next(
            row
            for row in observed
            if row["event"] == "consultation_completed"
        )
        self.assertEqual(completed["appleAttempts"], 1)
        self.assertEqual(completed["appleValidResults"], 0)
        self.assertEqual(
            completed["reasonCode"],
            "contract_invariant_failed",
        )
        self.assertNotIn(
            "private synthetic detail",
            json.dumps(observed),
        )

    def test_oversized_valid_condensation_falls_back(self):
        output = self.eligible_output()
        oversized = self.adapter.source_facts(0)
        oversized["summary"] = "x" * 5000
        original = self.adapter.source_facts
        self.adapter.source_facts = lambda _: deepcopy(oversized)
        observed = []
        try:
            self.assertIsNone(
                self.evaluate(
                    output,
                    lambda _: self.applied(),
                    observed=observed,
                )
            )
        finally:
            self.adapter.source_facts = original
        completed = next(
            row
            for row in observed
            if row["event"] == "consultation_completed"
        )
        self.assertEqual(completed["appleAttempts"], 1)
        self.assertEqual(completed["appleValidResults"], 0)
        self.assertEqual(
            completed["reasonCode"],
            "contract_invariant_failed",
        )
        self.assertFalse(
            any(
                row["event"] == "replacement_emitted"
                for row in observed
            )
        )

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

    def test_bridge_process_outcomes_are_closed_and_content_free(self):
        request = {
            "callID": "call-runtime-v1",
            "exitStatus": 0,
            "fields": [{"value": "safe"}],
        }
        valid = self.applied()
        cases = {
            "launch_unavailable": OSError("private launch detail"),
            "timed_out": subprocess.TimeoutExpired("private", 1),
            "nonzero_exit": mock.Mock(
                returncode=70,
                stderr=b"private stderr",
                stdout=b"private stdout",
            ),
            "stderr_nonempty": mock.Mock(
                returncode=0,
                stderr=b"private stderr",
                stdout=b"private stdout",
            ),
            "stdout_shape_invalid": mock.Mock(
                returncode=0,
                stderr=b"",
                stdout=b"private stdout",
            ),
            "json_invalid": mock.Mock(
                returncode=0,
                stderr=b"",
                stdout=b"{invalid}\n",
            ),
            "result_shape_invalid": mock.Mock(
                returncode=0,
                stderr=b"",
                stdout=b"{}\n",
            ),
            "result_observed": mock.Mock(
                returncode=0,
                stderr=b"",
                stdout=(
                    json.dumps(valid, separators=(",", ":")).encode()
                    + b"\n"
                ),
            ),
        }
        for outcome, completed in cases.items():
            observations = []
            with (
                self.subTest(outcome=outcome),
                mock.patch.object(
                    self.adapter.subprocess,
                    "run",
                    side_effect=(
                        completed
                        if isinstance(completed, BaseException)
                        else None
                    ),
                    return_value=(
                        None
                        if isinstance(completed, BaseException)
                        else completed
                    ),
                ) as run,
            ):
                result = self.adapter.run_bridge_process(
                    request,
                    executable=Path("/transient/bridge"),
                    timeout_seconds=1,
                    observe=observations.append,
                )
                self.assertEqual(
                    result,
                    valid if outcome == "result_observed" else None,
                )
                if outcome == "result_observed":
                    bridge_input = json.loads(
                        run.call_args.kwargs["input"]
                    )
                    self.assertEqual(
                        bridge_input,
                        {
                            "diagnosticText": "safe",
                            "sourceFacts": self.adapter.source_facts(0),
                        },
                    )
                self.assertEqual(
                    observations,
                    [
                        {
                            "event": "bridge_process_started",
                            "callID": "call-runtime-v1",
                        },
                        {
                            "event": "bridge_process_completed",
                            "callID": "call-runtime-v1",
                            "bridgeProcessOutcome": outcome,
                        },
                    ],
                )
                encoded = json.dumps(observations, sort_keys=True)
                for forbidden in (
                    "private",
                    "70",
                    "/transient/bridge",
                ):
                    self.assertNotIn(forbidden, encoded)
        self.assertFalse(
            self.adapter.bridge_result_is_closed(
                {
                    **valid,
                    "status": "fail",
                    "reasonCode": "private unreviewed reason",
                    "condensation": None,
                }
            )
        )


class SwiftBridgeTests(unittest.TestCase):
    def test_source_encodes_closed_optional_keys_as_null(self):
        source = SWIFT_SOURCE.read_text(encoding="utf-8")
        for key in (
            "file",
            "line",
            "column",
            "failedTestID",
            "reasonCode",
            "condensation",
        ):
            with self.subTest(key=key):
                self.assertIn(
                    f"try container.encodeNil(forKey: .{key})",
                    source,
                )

    def test_source_maps_sdk_generation_errors_without_error_content(self):
        source = SWIFT_SOURCE.read_text(encoding="utf-8")
        expected = {
            "assetsUnavailable": (
                "declined",
                "generation_assets_unavailable",
            ),
            "unsupportedLanguageOrLocale": (
                "declined",
                "generation_unsupported_language_or_locale",
            ),
            "rateLimited": ("declined", "generation_rate_limited"),
            "concurrentRequests": (
                "declined",
                "generation_concurrent_requests",
            ),
            "exceededContextWindowSize": (
                "fail",
                "generation_exceeded_context_window_size",
            ),
            "guardrailViolation": (
                "fail",
                "generation_guardrail_violation",
            ),
            "unsupportedGuide": (
                "fail",
                "generation_unsupported_guide",
            ),
            "decodingFailure": (
                "fail",
                "generation_decoding_failure",
            ),
            "refusal": ("fail", "generation_refusal"),
        }
        for case, (status, reason) in expected.items():
            with self.subTest(case=case):
                self.assertIn(
                    f"case .{case}:\n"
                    f'        return ("{status}", "{reason}")',
                    source,
                )
        self.assertIn("@unknown default:", source)
        self.assertEqual(
            source.count('"generation_unknown_error"'),
            2,
        )
        forbidden = (
            ".debugDescription",
            ".errorDescription",
            ".failureReason",
            ".recoverySuggestion",
            ".transcriptEntries",
            ".explanation",
            "localizedDescription",
            "String(describing:",
            "dump(",
            "print(error",
            r"\(error)",
        )
        for token in forbidden:
            with self.subTest(forbidden=token):
                self.assertNotIn(token, source)

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
            "            for: constrainedSchema",
            source,
        )
        self.assertIn("GenerationSchema(", source)
        self.assertIn("guides: [.constant(value)]", source)
        self.assertIn("guides: [.range(value...value)]", source)
        self.assertIn("schema: constrainedSchema", source)
        self.assertIn("LiteralDiagnosticExtraction(response.content)", source)
        self.assertNotIn("Transcript(", source)
        for embedded in (
            "synthetic unittest success",
            "command-class=test",
            "outcome=success",
            "exit-status=0",
            "warning-count=0",
            "command-finished=true",
            "task-complete=true",
            "continue after successful synthetic unittest",
        ):
            with self.subTest(embedded=embedded):
                self.assertNotIn(embedded, source)
        self.assertNotIn("http://", source)
        self.assertNotIn("https://", source)

    def test_source_uses_benign_synthetic_question(self):
        source = SWIFT_SOURCE.read_text(encoding="utf-8")
        full_consult = source[
            source.index("func consult("):
            source.index("@main")
        ]
        consult = source[
            source.index("func consult("):
            source.index("let responseReserve = 1024")
        ]
        self.assertEqual(full_consult.count("let prompt = Prompt("), 1)
        self.assertEqual(
            full_consult.count("schema: constrainedSchema"),
            1,
        )
        self.assertNotIn(
            "generating: DiagnosticCondensation.self",
            full_consult,
        )
        self.assertIn(
            "Respond with JSON answering the question.",
            consult,
        )
        self.assertIn(
            '{"question":"What was the result of this synthetic unit test?"}',
            consult,
        )
        for contract in (
            "Read only key=value lines before filler.",
            "Set commandOutcome to the exact outcome value.",
            "Set summary to the exact suite value, one ASCII space, then the\n"
            "        exact outcome value.",
            "Copy the complete command-class, outcome, exit-status, and\n"
            "        warning-count lines verbatim into summaryFacts in that order.",
            "Set warningCount to the warning-count integer.",
            "Set nextAction to the exact next-action value.",
            "Copy the complete command-finished and task-complete lines verbatim\n"
            "        into completionFacts in that order.",
            "Copy only literal issue lines into diagnostics.",
            "Set omittedWarningCount to warningCount minus the number of emitted\n"
            "        warning-severity diagnostics.",
            "Do not paraphrase, describe yourself, infer, or add content.",
        ):
            with self.subTest(contract=contract):
                self.assertIn(contract, consult)
        self.assertNotIn("omittedWarningCount to zero", consult)
        self.assertNotIn("diagnostics to an empty array", consult)
        self.assertNotIn("what model", consult.lower())
        self.assertNotIn("llm/slm", consult.lower())
        for trigger in (
            "fatal",
            "error",
            "secrets",
            "diagnoses",
        ):
            with self.subTest(trigger=trigger):
                self.assertNotIn(trigger, consult)

    def test_source_separates_preflight_from_response_errors(self):
        source = SWIFT_SOURCE.read_text(encoding="utf-8")
        consult = source[
            source.index("func consult("):
            source.index("@main")
        ]
        preflight_reason = 'reasonCode: "generation_preflight_unavailable"'
        self.assertEqual(consult.count(preflight_reason), 1)
        preflight_catch = consult.index(preflight_reason)
        session = consult.index("let session = LanguageModelSession(")
        attempt = consult.index("let appleAttempts = 1")
        response = consult.index("try await session.respond(")
        typed_catch = consult.index(
            "catch let generationError\n"
            "        as LanguageModelSession.GenerationError"
        )
        self.assertLess(
            consult.index("tokenCount(for: instructions)"),
            preflight_catch,
        )
        self.assertLess(preflight_catch, session)
        self.assertLess(session, attempt)
        self.assertLess(attempt, response)
        self.assertEqual(consult.count("let appleAttempts = 1"), 1)
        self.assertLess(response, typed_catch)
        preflight_output = consult[
            preflight_catch:
            consult.index(")", preflight_catch) + 1
        ]
        self.assertIn("appleAttempts: 0", preflight_output)
        response_output = consult[typed_catch:]
        self.assertIn("appleAttempts: appleAttempts", response_output)

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

    def test_python_identity_and_version_bracket_every_row(self):
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "python3"
            executable.write_text(
                "#!/bin/sh\nprintf 'Python 3.13.0\\n'\n",
                encoding="utf-8",
            )
            executable.chmod(0o700)
            captured = self.harness.capture_python(executable)

            def drift():
                executable.write_text(
                    "#!/bin/sh\nprintf 'Python 3.14.0\\n'\n",
                    encoding="utf-8",
                )
                executable.chmod(0o700)

            with self.assertRaises(self.harness.ProbeFailure):
                self.harness.run_with_python_bracket(captured, drift)

    def test_provider_fixture_uses_one_closed_exec_command(self):
        calls = [
            event["item"]
            for event in self.harness._provider_events(1)
            if event["type"] == "response.output_item.done"
            and event["item"]["type"] == "function_call"
        ]
        self.assertEqual(
            calls,
            [
                {
                    "type": "function_call",
                    "call_id": "call-runtime-v1",
                    "name": "exec_command",
                    "arguments": json.dumps(
                        {"cmd": self.harness.APPROVED_COMMAND},
                        separators=(",", ":"),
                    ),
                }
            ],
        )

    def test_response_server_event_factory_is_backward_compatible(self):
        custom = mock.Mock(return_value=self.harness._provider_events(1))
        server = self.harness._ResponsesServer(custom)
        try:
            self.assertIs(custom, server.event_factory)
        finally:
            server.server_close()
        server = self.harness._ResponsesServer()
        try:
            self.assertIs(
                self.harness._provider_events,
                server.event_factory,
            )
        finally:
            server.server_close()

    def test_every_parent_request_uses_closed_direct_exec_contract(self):
        tools = [
            {"name": name}
            for name in self.harness.DIRECT_TOOL_NAMES
        ]
        call = {
            "type": "function_call",
            "call_id": "call-runtime-v1",
            "name": "exec_command",
            "arguments": json.dumps(
                {"cmd": self.harness.APPROVED_COMMAND},
                separators=(",", ":"),
            ),
        }
        output = {
            "type": "function_call_output",
            "call_id": "call-runtime-v1",
            "output": "safe",
        }
        requests = [
            {"tools": tools, "input": []},
            {"tools": tools, "input": [call, output]},
        ]
        self.harness.require_direct_exec_requests(requests)

        mutations = {
            "missing advertised tool": lambda value: value[0][
                "tools"
            ].pop(),
            "additional advertised tool": lambda value: value[0][
                "tools"
            ].append({"name": "apply_patch"}),
            "web search advertised": lambda value: value[0][
                "tools"
            ].append({"name": "web_search"}),
            "nameless tool advertised": lambda value: value[0][
                "tools"
            ].append({"description": "not allowed"}),
            "write_stdin call": lambda value: value[1]["input"][0].update(
                name="write_stdin"
            ),
            "additional command call": lambda value: value[1][
                "input"
            ].append(deepcopy(call)),
            "additional argument": lambda value: value[1]["input"][0].update(
                arguments=json.dumps(
                    {
                        "cmd": self.harness.APPROVED_COMMAND,
                        "timeout_ms": 30_000,
                    }
                )
            ),
        }
        for label, mutate in mutations.items():
            value = deepcopy(requests)
            mutate(value)
            with self.subTest(label=label):
                with self.assertRaises(self.harness.ProbeFailure):
                    self.harness.require_direct_exec_requests(value)

    def test_generation_error_gate_mapping_is_closed(self):
        blocked = {
            "generation_assets_unavailable",
            "generation_unsupported_language_or_locale",
            "generation_rate_limited",
            "generation_concurrent_requests",
        }
        failed = {
            "generation_exceeded_context_window_size",
            "generation_guardrail_violation",
            "generation_unsupported_guide",
            "generation_decoding_failure",
            "generation_refusal",
            "generation_unknown_error",
            "contract_invariant_failed",
        }
        for reason in blocked:
            with self.subTest(reason=reason):
                self.assertEqual(
                    self.harness.generation_error_gate_result(reason),
                    "blocked",
                )
        for reason in failed:
            with self.subTest(reason=reason):
                self.assertEqual(
                    self.harness.generation_error_gate_result(reason),
                    "fail",
                )
        with self.assertRaisesRegex(
            self.harness.ProbeFailure,
            "^generation_reason_invalid$",
        ):
            self.harness.generation_error_gate_result(
                "generation_unreviewed_future_case"
            )

    def test_generation_error_terminal_requires_exact_fallback(self):
        row = {
            "status": "pass",
            "appleAttempts": 1,
            "appleValidResults": 0,
            "originalPreserved": True,
            "replacementPresentInNextRequest": False,
            "replacementBytes": 0,
            "spooled": False,
            "commandExecutions": 1,
            "hookInvocations": 1,
            "providerRequests": 2,
            "additionalParentModelTurns": 0,
        }
        blocked = dict(row)
        self.harness.enforce_composed_terminal(
            ["generation_assets_unavailable"],
            blocked,
        )
        self.assertEqual(
            (blocked["status"], blocked["reason"]),
            ("blocked", "generation_assets_unavailable"),
        )
        failed = dict(row)
        self.harness.enforce_composed_terminal(
            ["generation_refusal"],
            failed,
        )
        self.assertEqual(
            (failed["status"], failed["reason"]),
            ("fail", "generation_refusal"),
        )
        invalid = dict(row)
        self.harness.enforce_composed_terminal(
            ["contract_invariant_failed"],
            invalid,
        )
        self.assertEqual(
            (invalid["status"], invalid["reason"]),
            ("fail", "contract_invariant_failed"),
        )
        preflight = dict(row)
        preflight["appleAttempts"] = 0
        for reason in (
            "apple_unavailable",
            "locale_unsupported",
            "context_budget_exceeded",
            "generation_preflight_unavailable",
        ):
            with self.subTest(reason=reason):
                changed = dict(preflight)
                self.harness.enforce_composed_terminal(
                    [reason],
                    changed,
                )
                self.assertEqual(
                    (changed["status"], changed["reason"]),
                    ("blocked", reason),
                )
        mutations = {
            "no attempt": ("appleAttempts", 0),
            "retry": ("appleAttempts", 2),
            "valid result": ("appleValidResults", 1),
            "altered fallback": ("originalPreserved", False),
            "replacement": ("replacementPresentInNextRequest", True),
            "command rerun": ("commandExecutions", 2),
            "extra provider turn": ("providerRequests", 3),
            "added parent turn": ("additionalParentModelTurns", 1),
        }
        for label, (key, value) in mutations.items():
            changed = dict(row)
            changed[key] = value
            with self.subTest(label=label):
                with self.assertRaisesRegex(
                    self.harness.ProbeFailure,
                    "^generation_error_invariant_failed$",
                ):
                    self.harness.enforce_composed_terminal(
                        ["generation_refusal"],
                        changed,
                    )

    def test_bridge_observation_integrity_is_closed(self):
        call_id = "call-runtime-v1"
        start = {
            "event": "bridge_process_started",
            "callID": call_id,
        }
        completion = {
            "event": "bridge_process_completed",
            "callID": call_id,
            "bridgeProcessOutcome": "result_observed",
        }
        cases = {
            "valid": (
                [start, completion],
                ("result_observed", 1, 1),
            ),
            "missing start": (
                [completion],
                ("start_observation_missing", 0, 1),
            ),
            "missing completion": (
                [start],
                ("completion_observation_missing", 1, 0),
            ),
            "duplicate": (
                [start, start, completion],
                ("observation_invalid", 1, 1),
            ),
            "unknown outcome": (
                [
                    start,
                    {
                        **completion,
                        "bridgeProcessOutcome": "unreviewed",
                    },
                ],
                ("observation_invalid", 1, 1),
            ),
            "extra field": (
                [start, {**completion, "raw": "forbidden"}],
                ("observation_invalid", 1, 1),
            ),
        }
        for label, (observations, expected) in cases.items():
            with self.subTest(label=label):
                self.assertEqual(
                    self.harness.summarize_bridge_observations(
                        observations,
                        call_id=call_id,
                        bridge_expected=True,
                    ),
                    expected,
                )

    def test_every_observation_is_closed_before_derivation(self):
        call_id = "call-runtime-v1"
        valid = [
            {
                "event": "hook_invoked",
                "callID": call_id,
                "hookInvocations": 1,
            },
            {
                "event": "original_observed",
                "callID": call_id,
                "originalSha256": "a" * 64,
            },
            {
                "event": "bridge_process_started",
                "callID": call_id,
            },
            {
                "event": "bridge_process_completed",
                "callID": call_id,
                "bridgeProcessOutcome": "result_observed",
            },
            {
                "event": "consultation_completed",
                "callID": call_id,
                "appleAttempts": 1,
                "appleValidResults": 1,
                "reasonCode": None,
            },
            {
                "event": "replacement_emitted",
                "callID": call_id,
                "replacementSha256": "b" * 64,
                "replacementBytes": 512,
                "appleAttempts": 1,
            },
        ]
        self.assertTrue(
            self.harness.observations_are_closed(
                valid,
                call_id=call_id,
            )
        )
        mutations = {
            "unknown event": lambda rows: rows.append(
                {"event": "private_raw_stream", "raw": "Apple output"}
            ),
            "unhashable outcome": lambda rows: rows[3].update(
                bridgeProcessOutcome=[]
            ),
            "extra field": lambda rows: rows[2].update(
                raw="/private/prompt/transcript"
            ),
            "wrong type": lambda rows: rows[0].update(
                hookInvocations=True
            ),
            "wrong call": lambda rows: rows[1].update(callID="other"),
            "duplicate event": lambda rows: rows.append(dict(rows[0])),
            "missing original pairing": lambda rows: rows.pop(1),
            "invalid pairing": lambda rows: rows[4].update(
                appleAttempts=0
            ),
            "replacement without valid result": lambda rows: rows[4].update(
                appleValidResults=0,
                reasonCode="contract_invariant_failed",
            ),
        }
        for label, mutate in mutations.items():
            rows = deepcopy(valid)
            mutate(rows)
            with self.subTest(label=label):
                self.assertFalse(
                    self.harness.observations_are_closed(
                        rows,
                        call_id=call_id,
                    )
                )

    def test_live_process_outcomes_preserve_exact_fallback(self):
        stimulus = b"RUNTIME_V1_ORIGINAL_SENTINEL\nsafe\n"
        envelope = (
            b"Chunk ID: 0a9f\n"
            b"Wall time: 0.1 seconds\n"
            b"Process exited with code 0\n"
            b"Original token count: 2\n"
            b"Output:\n"
            + stimulus
        )
        outcomes = (
            self.harness.BRIDGE_PROCESS_OUTCOMES
            - {"result_observed"}
        ) | self.harness.BRIDGE_OBSERVATION_OUTCOMES
        for outcome in outcomes:
            starts, completions = {
                "start_observation_missing": (0, 0),
                "completion_observation_missing": (1, 0),
            }.get(outcome, (1, 1))
            with self.subTest(outcome=outcome):
                row = self.harness.classify_row(
                    row_id="composed_live_apple_applied",
                    bridge_kind="apple",
                    stimulus=stimulus,
                    approved_stimulus_sha256=digest(stimulus),
                    hook_input_sha256=digest(stimulus),
                    replacement_sha256=None,
                    next_output=envelope,
                    baseline_provider_requests=2,
                    provider_requests=2,
                    command_executions=1,
                    hook_invocations=1,
                    apple_attempts=None,
                    bridge_start_observations=starts,
                    bridge_completion_observations=completions,
                    bridge_process_outcome=outcome,
                )
                self.harness.apply_live_process_outcome(row)
                self.assertTrue(row["originalPreserved"])
                self.assertFalse(
                    row["replacementPresentInNextRequest"]
                )
                self.assertIsNone(row["appleAttempts"])
                self.assertEqual(
                    row["status"],
                    (
                        "blocked"
                        if outcome
                        in self.harness.BRIDGE_PROCESS_BLOCKERS
                        else "fail"
                    ),
                )
                self.assertEqual(row["reason"], outcome)
                self.assertTrue(
                    self.harness.row_observability_is_valid(row)
                )
                if outcome in self.harness.BRIDGE_OBSERVATION_OUTCOMES:
                    fixture_row = self.harness.classify_row(
                        row_id="bridge_crash",
                        bridge_kind="crash",
                        stimulus=stimulus,
                        approved_stimulus_sha256=digest(stimulus),
                        hook_input_sha256=digest(stimulus),
                        replacement_sha256=None,
                        next_output=envelope,
                        baseline_provider_requests=2,
                        provider_requests=2,
                        command_executions=1,
                        hook_invocations=1,
                        apple_attempts=None,
                        bridge_start_observations=starts,
                        bridge_completion_observations=completions,
                        bridge_process_outcome=outcome,
                    )
                    self.harness.apply_live_process_outcome(fixture_row)
                    self.assertEqual(fixture_row["status"], "fail")
                    self.assertIsNone(fixture_row["appleAttempts"])
                    self.assertTrue(
                        self.harness.row_observability_is_valid(
                            fixture_row
                        )
                    )

    def test_installed_row_disables_web_search_per_run(self):
        arguments = self.harness.build_exec_arguments(
            "http://127.0.0.1:1",
            ROOT,
        )
        self.assertEqual(
            list(zip(arguments, arguments[1:])).count(
                ("-c", 'web_search="disabled"')
            ),
            1,
        )

    def test_installed_row_failure_reasons_are_closed_and_ordered(self):
        cases = (
            (-1, b"diagnostic", 1, "codex_process_nonzero"),
            (0, b"diagnostic", 1, "codex_stderr_nonempty"),
            (0, b"", 1, "provider_request_count_invalid"),
        )
        for returncode, stderr, request_count, reason in cases:
            with self.subTest(reason=reason):
                with self.assertRaisesRegex(
                    self.harness.ProbeFailure,
                    f"^{reason}$",
                ):
                    self.harness.validate_installed_row_result(
                        returncode,
                        stderr,
                        request_count,
                    )
        self.harness.validate_installed_row_result(0, b"", 2)

    def test_installed_codex_row_uses_and_closes_pty_stdin(self):
        descriptors = []
        real_openpty = os.openpty

        def openpty():
            pair = real_openpty()
            descriptors.extend(pair)
            return pair

        def run(*_arguments, **options):
            self.assertTrue(os.isatty(options["stdin"]))
            return mock.Mock(returncode=0, stderr=b"", stdout=b"")

        codex = mock.Mock(resolved=Path("/bin/true"))
        with (
            mock.patch.object(
                self.harness.os,
                "openpty",
                side_effect=openpty,
            ),
            mock.patch.object(
                self.harness.subprocess,
                "run",
                side_effect=run,
            ),
            self.assertRaisesRegex(
                self.harness.ProbeFailure,
                "^provider_request_count_invalid$",
            ),
        ):
            self.harness.run_row(
                codex=codex,
                python=Path(shutil.which("python3")),
                plugin=(
                    ROOT
                    / "fixtures/runtime-v1-capability"
                    / "synthetic-plugin"
                ),
                approved_plugin_sha256="a" * 64,
                approved_hook_hash="sha256:" + ("b" * 64),
                approved_stimulus_sha256="c" * 64,
                bridge_executable=Path("/bin/true"),
                phase="plugin_off_baseline",
                baseline_provider_requests=2,
            )
        self.assertEqual(len(descriptors), 2)
        for descriptor in descriptors:
            with self.assertRaises(OSError):
                os.fstat(descriptor)

    def test_blocked_preflight_writes_closed_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "blocked.json"
            result = self.harness.main(
                [
                    "--codex-executable",
                    str(Path(directory) / "missing-codex"),
                    "--python-executable",
                    "/bin/true",
                    "--xcrun-executable",
                    "/bin/true",
                    "--swiftc-executable",
                    "/bin/true",
                    "--plugin",
                    str(
                        ROOT
                        / "fixtures/runtime-v1-capability"
                        / "synthetic-plugin"
                    ),
                    "--approved-plugin-sha256",
                    "a" * 64,
                    "--approved-hook-hash",
                    "sha256:" + ("b" * 64),
                    "--approved-stimulus-sha256",
                    "c" * 64,
                    "--through",
                    "direct",
                    "--output",
                    str(output),
                ]
            )
            self.assertEqual(result, 2)
            evidence = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(set(evidence), set(self.harness.EVIDENCE_KEYS))
            self.assertEqual(
                (evidence["status"], evidence["reason"]),
                ("blocked", "missing_binary_or_version_mismatch"),
            )
            self.assertEqual(evidence["rows"], [])
            self.assertEqual(evidence["cleanupStatus"], "complete")

            failed_output = Path(directory) / "failed.json"
            with mock.patch.object(
                self.harness,
                "execute_outer_gate",
                side_effect=self.harness.ProbeFailure(
                    "synthetic_plugin_drift"
                ),
            ):
                result = self.harness.main(
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
                        "--through",
                        "direct",
                        "--output",
                        str(failed_output),
                    ]
                )
            self.assertEqual(result, 2)
            failed = json.loads(
                failed_output.read_text(encoding="utf-8")
            )
            self.assertEqual(
                (failed["status"], failed["reason"]),
                ("fail", "synthetic_plugin_drift"),
            )

            cleanup_output = Path(directory) / "cleanup.json"
            with mock.patch.object(
                self.harness,
                "execute_outer_gate",
                side_effect=OSError("private diagnostic"),
            ):
                result = self.harness.main(
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
                        "--through",
                        "direct",
                        "--output",
                        str(cleanup_output),
                    ]
                )
            self.assertEqual(result, 2)
            cleanup = json.loads(
                cleanup_output.read_text(encoding="utf-8")
            )
            self.assertEqual(
                (cleanup["status"], cleanup["reason"]),
                ("blocked", "cleanup_incomplete"),
            )
            self.assertEqual(
                cleanup["cleanupStatus"],
                "incomplete",
            )

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

    def test_no_output_preserves_closed_codex_exec_envelope(self):
        stimulus = b"RUNTIME_V1_ORIGINAL_SENTINEL\nsafe\n"
        row = self.harness.classify_row(
            row_id="bridge_crash",
            bridge_kind="crash",
            stimulus=stimulus,
            approved_stimulus_sha256=digest(stimulus),
            hook_input_sha256=digest(stimulus),
            replacement_sha256=None,
            next_output=(
                b"Chunk ID: 0a9f\n"
                b"Wall time: 0.1 seconds\n"
                b"Process exited with code 0\n"
                b"Original token count: 2\n"
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

    def test_no_output_rejects_invalid_codex_exec_envelope(self):
        stimulus = b"RUNTIME_V1_ORIGINAL_SENTINEL\nsafe\n"
        valid_header = (
            b"Chunk ID: 0a9f\n"
            b"Wall time: 0.1 seconds\n"
            b"Process exited with code 0\n"
            b"Original token count: 2\n"
            b"Output:\n"
        )
        invalid_outputs = {
            "obsolete wrapper": (
                b"Exit code: 0\n"
                b"Wall time: 0.1 seconds\n"
                b"Output:\n"
                + stimulus
            ),
            "missing chunk id": valid_header.replace(
                b"Chunk ID: 0a9f\n",
                b"",
            )
            + stimulus,
            "empty chunk id": valid_header.replace(
                b"Chunk ID: 0a9f\n",
                b"Chunk ID: \n",
            )
            + stimulus,
            "uppercase chunk id": valid_header.replace(
                b"0a9f",
                b"0A9F",
            )
            + stimulus,
            "nonzero exit": valid_header.replace(
                b"code 0",
                b"code 1",
            )
            + stimulus,
            "leading-zero wall time": valid_header.replace(
                b"0.1 seconds",
                b"00.1 seconds",
            )
            + stimulus,
            "signed wall time": valid_header.replace(
                b"0.1 seconds",
                b"+0.1 seconds",
            )
            + stimulus,
            "integer-only wall time": valid_header.replace(
                b"0.1 seconds",
                b"0 seconds",
            )
            + stimulus,
            "missing integer wall part": valid_header.replace(
                b"0.1 seconds",
                b".1 seconds",
            )
            + stimulus,
            "leading-zero token count": valid_header.replace(
                b"count: 2",
                b"count: 02",
            )
            + stimulus,
            "negative token count": valid_header.replace(
                b"count: 2",
                b"count: -1",
            )
            + stimulus,
            "wrong output marker": valid_header.replace(
                b"Output:\n",
                b"Final output:\n",
            )
            + stimulus,
            "extra header field": valid_header.replace(
                b"Output:\n",
                b"Transient: forbidden\nOutput:\n",
            )
            + stimulus,
            "altered payload": valid_header + stimulus.replace(
                b"safe",
                b"SAFE",
            ),
            "duplicated payload": valid_header + stimulus + stimulus,
        }
        for name, next_output in invalid_outputs.items():
            with self.subTest(name=name):
                row = self.harness.classify_row(
                    row_id="bridge_crash",
                    bridge_kind="crash",
                    stimulus=stimulus,
                    approved_stimulus_sha256=digest(stimulus),
                    hook_input_sha256=digest(stimulus),
                    replacement_sha256=None,
                    next_output=next_output,
                    baseline_provider_requests=2,
                    provider_requests=2,
                    command_executions=1,
                    hook_invocations=1,
                    apple_attempts=0,
                )
                self.assertFalse(row["originalPreserved"])
                self.assertEqual(
                    (row["status"], row["reason"]),
                    ("fail", "untouched_original_invariant_failed"),
                )

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
                self.assertEqual(completed.stderr, b"")
                self.assertEqual(
                    completed.stdout,
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
        process_outcomes = {
            "direct_fake_applied": "result_observed",
            "composed_live_apple_applied": "result_observed",
            "bridge_malformed": "result_shape_invalid",
            "bridge_crash": "nonzero_exit",
        }
        process_outcome = process_outcomes.get(row_id)
        return {
            "id": row_id,
            "status": "pass",
            "reason": (
                "replacement_observed"
                if replacement
                else "untouched_original_observed"
            ),
            "bridgeKind": {
                "plugin_off_baseline": "valid",
                "direct_fake_applied": "valid",
                "composed_live_apple_applied": "apple",
                "decline_unapproved_stimulus": "valid",
                "bridge_malformed": "malformed",
                "bridge_crash": "crash",
                "adapter_crash": "valid",
                "hook_timeout": "valid",
            }[row_id],
            "commandExecutions": 1,
            "hookInvocations": (
                0 if row_id == "plugin_off_baseline" else 1
            ),
            "bridgeStartObservations": int(process_outcome is not None),
            "bridgeCompletionObservations": int(
                process_outcome is not None
            ),
            "bridgeProcessOutcome": process_outcome,
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
            "timeoutPluginSha256": "a" * 64,
            "timeoutHookCurrentHash": "sha256:" + ("b" * 64),
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

    def test_semantic_rejection_retains_the_composed_row(self):
        value = self.evidence()
        value["rows"] = value["rows"][:3]
        composed = value["rows"][-1]
        composed.update(
            status="fail",
            reason="contract_invariant_failed",
            appleValidResults=0,
            replacementSha256=None,
            originalAbsentFromNextRequest=False,
            replacementPresentInNextRequest=False,
            originalPreserved=True,
            replacementBytes=0,
        )
        value.update(
            status="fail",
            reason="contract_invariant_failed",
        )

        validated = self.harness.validate_evidence(value)

        self.assertEqual(len(validated["rows"]), 3)
        self.assertEqual(
            (
                validated["rows"][-1]["bridgeProcessOutcome"],
                validated["rows"][-1]["appleAttempts"],
                validated["rows"][-1]["appleValidResults"],
            ),
            ("result_observed", 1, 0),
        )

    def test_committed_evidence_is_valid_and_hash_bound(self):
        encoded = EVIDENCE.read_bytes()
        value = self.harness.validate_evidence(json.loads(encoded))
        self.assertEqual(
            (value["status"], value["reason"]),
            ("pass", "capability_proven"),
        )
        self.assertIn(
            hashlib.sha256(encoded).hexdigest(),
            INTERPRETATION.read_text(),
        )

    def test_controlled_results_require_zero_apple_usage(self):
        for key in ("appleAttempts", "appleValidResults"):
            value = self.evidence()
            row = next(
                item
                for item in value["rows"]
                if item["id"] == "direct_fake_applied"
            )
            row[key] = 1
            with self.subTest(key=key):
                with self.assertRaises(self.harness.ProbeFailure):
                    self.harness.validate_evidence(value)

    def test_integrity_failures_precede_process_blockers(self):
        mutations = {
            "hook": (
                "hook_input_invariant_failed",
                lambda row: row.update(hookInputSha256="0" * 64),
            ),
            "grant": (
                "context_grant_invariant_failed",
                lambda row: row.update(
                    originalSha256="0" * 64,
                    hookInputSha256="0" * 64,
                ),
            ),
            "replacement": (
                "replacement_invariant_failed",
                lambda row: row.update(
                    replacementPresentInNextRequest=True
                ),
            ),
            "observation": (
                "bridge_observation_invariant_failed",
                lambda row: row.update(
                    bridgeStartObservations=0
                ),
            ),
        }
        for label, (expected, mutate) in mutations.items():
            rows = self.rows()[:3]
            row = rows[-1]
            row.update(
                status="blocked",
                reason="timed_out",
                bridgeProcessOutcome="timed_out",
                appleAttempts=None,
                appleValidResults=0,
                replacementSha256=None,
                originalAbsentFromNextRequest=False,
                replacementPresentInNextRequest=False,
                originalPreserved=True,
                replacementBytes=0,
            )
            mutate(row)
            with self.subTest(label=label):
                self.assertEqual(self.derive(rows)[1], expected)

    def test_evidence_values_and_pairings_are_closed(self):
        mutations = {
            "top mismatch": lambda value: value.update(
                status="pass",
                reason="timed_out",
            ),
            "unknown row": lambda value: value["rows"][0].update(
                id="private row"
            ),
            "unhashable row list": lambda value: value["rows"][0].update(
                id=[]
            ),
            "unhashable row object": lambda value: value["rows"][0].update(
                id={}
            ),
            "row reason mismatch": lambda value: value["rows"][1].update(
                reason="untouched_original_observed"
            ),
            "bridge kind content": lambda value: value["rows"][1].update(
                bridgeKind="/private/Apple output"
            ),
            "outcome pairing": lambda value: value["rows"][5].update(
                bridgeProcessOutcome="result_observed"
            ),
            "nullable fixture attempt": lambda value: value["rows"][1].update(
                appleAttempts=None
            ),
            "content reason": lambda value: value.update(
                status="fail",
                reason="prompt transcript content",
            ),
            "unhashable status": lambda value: value.update(status=[]),
            "boolean count": lambda value: value["rows"][0].update(
                commandExecutions=True
            ),
        }
        for label, mutate in mutations.items():
            value = self.evidence()
            mutate(value)
            with self.subTest(label=label):
                with self.assertRaises(self.harness.ProbeFailure):
                    self.harness.validate_evidence(value)

    def test_top_level_memberships_reject_every_malformed_value(self):
        terminal = self.evidence()
        terminal.update(
            status="blocked",
            reason="missing_binary_or_version_mismatch",
            codexVersion=None,
            sdkVersion=None,
            swiftVersion=None,
            hookTrustStatus="blocked",
            directToolMode=None,
            codeModeEnabled=None,
            rows=[],
        )
        mutations = {
            "status": ("status", []),
            "reason": ("reason", []),
            "codexVersion": ("codexVersion", []),
            "sdkVersion": ("sdkVersion", {}),
            "swiftVersion": ("swiftVersion", []),
            "hookTrustStatus": ("hookTrustStatus", {}),
            "directToolMode": ("directToolMode", []),
            "codeModeEnabled": ("codeModeEnabled", {}),
            "contextGrantStatus": ("contextGrantStatus", []),
            "cleanupStatus": ("cleanupStatus", {}),
        }
        for label, (key, malformed) in mutations.items():
            value = deepcopy(terminal)
            value[key] = malformed
            with self.subTest(label=label):
                with self.assertRaises(self.harness.ProbeFailure):
                    self.harness.validate_evidence(value)

    def test_invariant_failures_have_exact_row_pairings(self):
        cases = {
            "adapter cannot claim bridge process": (
                "adapter_crash",
                "bridge_process_invariant_failed",
                "untouched_original_invariant_failed",
            ),
            "plugin off cannot claim replacement failure": (
                "plugin_off_baseline",
                "replacement_invariant_failed",
                "row_failed",
            ),
        }
        for label, (row_id, reason, top_reason) in cases.items():
            value = self.evidence()
            row = next(item for item in value["rows"] if item["id"] == row_id)
            row.update(
                status="fail",
                reason=reason,
                bridgeProcessOutcome=None,
                bridgeStartObservations=0,
                bridgeCompletionObservations=0,
                appleAttempts=0,
                appleValidResults=0,
                replacementSha256=None,
                originalAbsentFromNextRequest=False,
                replacementPresentInNextRequest=False,
                originalPreserved=True,
                replacementBytes=0,
            )
            value["status"] = "fail"
            value["reason"] = top_reason
            with self.subTest(label=label):
                with self.assertRaises(self.harness.ProbeFailure):
                    self.harness.validate_evidence(value)

    def test_declared_prerequisite_blockers_remain_blocked(self):
        for reason in (
            "missing_binary_or_version_mismatch",
            "sdk_26_5_unavailable",
            "apple_unavailable",
            "locale_unsupported",
            "generation_preflight_unavailable",
            "generation_assets_unavailable",
            "generation_unsupported_language_or_locale",
            "generation_rate_limited",
            "generation_concurrent_requests",
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

    def test_timeout_trust_identity_is_closed_and_distinct(self):
        self.harness.validate_evidence(self.evidence())
        partial = self.evidence()
        partial["status"] = "fail"
        partial["reason"] = "incomplete_gate"
        partial["rows"] = partial["rows"][:2]
        partial["timeoutPluginSha256"] = None
        partial["timeoutHookCurrentHash"] = None
        self.harness.validate_evidence(partial)

        mutations = {
            "missing field": lambda value: value.pop(
                "timeoutPluginSha256"
            ),
            "unknown field": lambda value: value.__setitem__(
                "unknownTimeoutIdentity",
                "a" * 64,
            ),
            "malformed plugin digest": lambda value: value.__setitem__(
                "timeoutPluginSha256",
                "not-a-digest",
            ),
            "malformed hook digest": lambda value: value.__setitem__(
                "timeoutHookCurrentHash",
                "b" * 64,
            ),
            "same plugin identity": lambda value: value.__setitem__(
                "timeoutPluginSha256",
                value["pluginSha256"],
            ),
            "same hook identity": lambda value: value.__setitem__(
                "timeoutHookCurrentHash",
                value["hookCurrentHash"],
            ),
            "missing complete identities": lambda value: value.update(
                timeoutPluginSha256=None,
                timeoutHookCurrentHash=None,
            ),
        }
        for label, mutate in mutations.items():
            value = self.evidence()
            mutate(value)
            with self.subTest(label=label):
                with self.assertRaises(self.harness.ProbeFailure):
                    self.harness.validate_evidence(value)

    def test_nullable_attempt_requires_unobservable_nonpassing_row(self):
        value = self.evidence()
        value["status"] = "fail"
        value["reason"] = "nonzero_exit"
        value["rows"] = value["rows"][:3]
        row = value["rows"][-1]
        row.update(
            status="fail",
            reason="nonzero_exit",
            bridgeProcessOutcome="nonzero_exit",
            appleAttempts=None,
            appleValidResults=0,
            replacementSha256=None,
            originalAbsentFromNextRequest=False,
            replacementPresentInNextRequest=False,
            originalPreserved=True,
            replacementBytes=0,
        )
        self.harness.validate_evidence(value)

        mutations = {
            "passing unknown attempts": lambda item: item.update(
                status="pass"
            ),
            "result with unknown attempts": lambda item: item.update(
                bridgeProcessOutcome="result_observed"
            ),
            "unknown outcome": lambda item: item.update(
                bridgeProcessOutcome="unreviewed"
            ),
            "unbounded start count": lambda item: item.update(
                bridgeStartObservations=2
            ),
            "altered process fallback": lambda item: item.update(
                originalPreserved=False
            ),
        }
        for label, mutate in mutations.items():
            changed = deepcopy(value)
            mutate(changed["rows"][-1])
            with self.subTest(label=label):
                with self.assertRaises(self.harness.ProbeFailure):
                    self.harness.validate_evidence(changed)

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
            timeout_plugin_sha256="a" * 64,
            timeout_hook_current_hash="sha256:" + ("b" * 64),
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

        complete = self.harness._parse_arguments(
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
                "complete",
                "--output",
                "evidence.json",
            ]
        )
        with self.assertRaises(self.harness.ProbeFailure):
            self.harness.validate_outer_options(complete)
        complete.approved_timeout_plugin_sha256 = "d" * 64
        complete.approved_timeout_hook_hash = (
            "sha256:" + ("e" * 64)
        )
        self.harness.validate_outer_options(complete)
