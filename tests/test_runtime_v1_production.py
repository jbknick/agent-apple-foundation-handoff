from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import shutil
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
ADAPTER = (
    ROOT
    / "plugins/apple-foundation-models-handoff/hooks/codex/"
    "diagnostic_condensation.py"
)
CONTRACT = (
    ROOT
    / "plugins/apple-foundation-models-handoff/runtime/runtime_contract.py"
)
HOOKS = (
    ROOT
    / "plugins/apple-foundation-models-handoff/hooks/codex/hooks.json"
)
SWIFT = (
    ROOT
    / "plugins/apple-foundation-models-handoff/runtime/"
    "DiagnosticCondenser.swift"
)
PRODUCTION_HARNESS = ROOT / "tests/e2e/codex_runtime_v1_production.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


adapter = load_module(ADAPTER, "runtime_v1_production_adapter")
contract = load_module(CONTRACT, "runtime_v1_production_contract")
harness = load_module(
    PRODUCTION_HARNESS,
    "runtime_v1_production_harness",
)


def diagnostic_text(
    *,
    classification: str = "C0",
    exit_status: int = 0,
    size: int = 9000,
) -> str:
    outcome = "success" if exit_status == 0 else "failure"
    task_complete = "true" if exit_status == 0 else "false"
    prefix = (
        "case-id: production-test-01\n"
        "command-class: test\n"
        "command-form: python3 -m unittest\n"
        f"classification: {classification}\n"
        f"exit-status: {exit_status}\n"
        "interrupted: false\n"
        "warning-count: 0\n"
        f"command-outcome: {outcome}\n"
        f"summary: synthetic unittest {outcome}\n"
        "summary-facts: command-class=test|"
        "command-form=python3 -m unittest|"
        f"outcome={outcome}|error-count=0|warning-count=0\n"
        f"next-action: {'continue' if exit_status == 0 else 'inspect'} "
        "after synthetic unittest\n"
        "completion-facts: command-finished=true|"
        f"task-complete={task_complete}\n"
    )
    filler = "synthetic-noise|classification=C0|repeat=1\n"
    return prefix + filler * ((size - len(prefix)) // len(filler) + 1)


def payload(text: str | None = None) -> dict[str, object]:
    return {
        "session_id": "session-runtime-v1",
        "transcript_path": "<transient>",
        "cwd": str(ROOT),
        "hook_event_name": "PostToolUse",
        "model": "parent-model",
        "turn_id": "turn-runtime-v1",
        "permission_mode": "default",
        "tool_name": "Bash",
        "tool_input": {"command": "python3 -m unittest -q"},
        "tool_response": text if text is not None else diagnostic_text(),
        "tool_use_id": "call-runtime-v1",
    }


def command_for_form(command_form: str) -> str:
    suffixes = {
        "python3 -m ruff check": " tests",
        "python3 -m mypy": " tests",
        "swiftc -typecheck": " Fixture.swift",
        "swift format lint": " Fixture.swift",
    }
    return command_form + suffixes.get(command_form, "")


def consultation_for(request: dict[str, object]) -> dict[str, object]:
    facts = request.get("sourceFacts")
    if facts is None:
        facts = adapter.source_facts(request["fields"][0]["value"])
    return {
        "status": "applied",
        "reasonCode": None,
        "appleAvailable": True,
        "localeSupported": True,
        "contextSize": 32_768,
        "occupiedTokens": 4_096,
        "appleAttempts": 1,
        "condensation": facts,
    }


def serialized_hook_response(response):
    return (
        json.dumps(
            response,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


class ProductionMetadataTests(unittest.TestCase):
    def test_hook_is_one_bounded_post_tool_use_handler(self):
        value = json.loads(HOOKS.read_text())
        self.assertEqual(
            {
                "hooks": {
                    "PostToolUse": [
                        {
                            "matcher": "Bash",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": (
                                        '"$RUNTIME_V1_PYTHON" '
                                        '"$PLUGIN_ROOT/hooks/codex/'
                                        'diagnostic_condensation.py"'
                                    ),
                                    "timeout": 60,
                                    "statusMessage": (
                                        "checking local diagnostic consultation"
                                    ),
                                }
                            ],
                        }
                    ]
                }
            },
            value,
        )

    def test_generated_contract_is_byte_identical(self):
        self.assertEqual(
            (ROOT / "fixtures/dev-142/runtime_contract.py").read_bytes(),
            CONTRACT.read_bytes(),
        )


class ProductionAdapterTests(unittest.TestCase):
    def evaluate(self, value, consult=consultation_for, repo_root=ROOT):
        observations = []
        response = adapter.evaluate(
            value,
            contract=contract,
            consult=consult,
            repo_root=repo_root,
            observe=observations.append,
        )
        return response, observations

    def test_success_emits_only_validated_replacement(self):
        calls = []
        validated = []

        def consult(request):
            calls.append(request)
            return consultation_for(request)

        original_validate = contract.validate_result

        def validate(result):
            validated.append(json.loads(json.dumps(result)))
            return original_validate(result)

        with mock.patch.object(contract, "validate_result", side_effect=validate):
            response, observations = self.evaluate(payload(), consult)

        self.assertEqual(1, len(calls))
        self.assertEqual({"diagnosticText", "sourceFacts"}, set(calls[0]))
        self.assertEqual({"continue", "stopReason"}, set(response))
        self.assertIs(response["continue"], False)
        result = json.loads(response["stopReason"])
        expected = adapter.source_facts(diagnostic_text())
        self.assertEqual(expected, result)
        self.assertEqual(
            json.dumps(
                expected,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            ),
            response["stopReason"],
        )
        self.assertTrue(any(
            value.get("outcome") == "applied"
            and value.get("condensation") == expected
            for value in validated
        ))
        self.assertTrue(
            {"schemaVersion", "outcome", "resultType", "condensation"}
            .isdisjoint(result)
        )
        self.assertEqual(
            {"consultation_completed", "replacement_emitted"},
            {row["event"] for row in observations},
        )
        serialized = json.dumps(observations)
        self.assertNotIn("diagnosticText", serialized)
        self.assertNotIn("sourceFacts", serialized)
        self.assertNotIn("synthetic unittest", serialized)

    def test_every_preflight_decline_avoids_consultation(self):
        base = payload()
        cases = {
            "unknown payload key": {**base, "unexpected": True},
            "wrong event": {**base, "hook_event_name": "PreToolUse"},
            "wrong tool": {**base, "tool_name": "Read"},
            "wrong cwd": {**base, "cwd": str(ROOT.parent)},
            "wrong command": {
                **base,
                "tool_input": {"command": "echo unsafe"},
            },
            "too short": payload(diagnostic_text(size=100)),
            "too long": payload(diagnostic_text(size=70_000)),
            "invalid classification": payload(
                diagnostic_text(classification="C2")
            ),
            "sensitive": payload(
                diagnostic_text().replace(
                    "synthetic unittest success",
                    "password=not-approved",
                    1,
                )
            ),
        }
        for name, candidate in cases.items():
            calls = []
            with self.subTest(name=name):
                response, _ = self.evaluate(
                    candidate,
                    lambda request: calls.append(request),
                )
                self.assertIsNone(response)
                self.assertEqual([], calls)

    def test_every_bridge_decline_or_failure_emits_no_output(self):
        variants = (
            None,
            {},
            {
                **consultation_for({"fields": [{"value": diagnostic_text()}]}),
                "status": "declined",
                "reasonCode": "apple_unavailable",
                "appleAvailable": False,
                "appleAttempts": 0,
                "condensation": None,
            },
            {
                **consultation_for({"fields": [{"value": diagnostic_text()}]}),
                "status": "fail",
                "reasonCode": "contract_invariant_failed",
                "condensation": None,
            },
        )
        for value in variants:
            with self.subTest(value=value):
                calls = []

                def consult(_request, value=value):
                    calls.append(True)
                    if value is None:
                        raise TimeoutError
                    return value

                response, _ = self.evaluate(payload(), consult)
                self.assertIsNone(response)
                self.assertEqual([True], calls)

    def test_source_facts_parser_is_closed(self):
        facts = adapter.source_facts(diagnostic_text(exit_status=1))
        contract._validate_source_facts(facts)
        self.assertEqual("failure", facts["commandOutcome"])
        self.assertEqual(0, facts["warningCount"])
        self.assertEqual([], facts["diagnostics"])
        for mutation in (
            diagnostic_text().replace(
                "command-class: test",
                "command-class: unknown",
                1,
            ),
            diagnostic_text().replace(
                "warning-count: 0",
                "warning-count: -1",
                1,
            ),
            diagnostic_text() + "diagnostic: {}\n",
        ):
            with self.subTest():
                with self.assertRaises(ValueError):
                    adapter.source_facts(mutation)

    def test_failure_preserves_exact_semantics(self):
        response, _ = self.evaluate(payload(diagnostic_text(exit_status=65)))

        result = json.loads(response["stopReason"])
        self.assertEqual("failure", result["commandOutcome"])

    def test_source_facts_match_all_twenty_four_reviewed_cases(self):
        corpus = json.loads(
            (ROOT / "fixtures/dev-142/benchmark-corpus.json").read_text()
        )
        for case in corpus["cases"]:
            expected = case["expected"]
            diagnostics = [
                contract._diagnostic_for_case(case, diagnostic_id)
                for diagnostic_id in (
                    expected["requiredDiagnosticIDs"]
                    + expected["warningRepresentativeIDs"]
                )
            ]
            with self.subTest(case=case["id"]):
                self.assertEqual(
                    {
                        "commandOutcome": expected["commandOutcome"],
                        "summary": expected["summary"],
                        "summaryFacts": expected["summaryFacts"],
                        "diagnostics": diagnostics,
                        "warningCount": expected["warningCount"],
                        "omittedWarningCount": (
                            expected["warningCount"]
                            - len(expected["warningRepresentativeIDs"])
                        ),
                        "nextAction": expected["nextAction"],
                        "completionFacts": expected["completionFacts"],
                    },
                    adapter.source_facts(
                        contract.render_case(case).decode("utf-8")
                    ),
                )

    def test_all_twenty_four_cases_bind_command_form_and_exit_status(self):
        corpus = json.loads(
            (ROOT / "fixtures/dev-142/benchmark-corpus.json").read_text()
        )
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            repo_root = Path(directory)
            (repo_root / "tests").mkdir()
            (repo_root / "Fixture.swift").write_text("")
            for case in corpus["cases"]:
                for diagnostic_id in (
                    case["expected"]["requiredDiagnosticIDs"]
                    + case["expected"]["warningRepresentativeIDs"]
                ):
                    diagnostic = contract._diagnostic_for_case(
                        case,
                        diagnostic_id,
                    )
                    if diagnostic["file"] is not None:
                        path = repo_root / diagnostic["file"]
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.touch()
                candidate = payload(
                    contract.render_case(case).decode("utf-8")
                )
                candidate["cwd"] = str(repo_root)
                candidate["tool_input"] = {
                    "command": command_for_form(case["commandForm"])
                }
                with self.subTest(case=case["id"]):
                    response, _ = self.evaluate(
                        candidate,
                        repo_root=repo_root,
                    )
                    result = json.loads(response["stopReason"])
                    self.assertEqual(
                        adapter.source_facts(
                            contract.render_case(case).decode("utf-8")
                        ),
                        result,
                    )

    def test_same_class_cross_form_and_self_classification_are_denied(self):
        variants = (
            diagnostic_text().replace(
                "command-form: python3 -m unittest",
                "command-form: python3 -m pytest",
                1,
            ),
            diagnostic_text(classification="C2"),
            diagnostic_text().replace(
                "synthetic unittest success",
                "password=not-approved",
                1,
            ),
        )
        for candidate in variants:
            calls = []
            with self.subTest():
                response, _ = self.evaluate(
                    payload(candidate),
                    lambda request: calls.append(request),
                )
                self.assertIsNone(response)
                self.assertEqual([], calls)

    def test_bridge_process_is_closed_and_one_shot(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            executable = Path(directory) / "bridge"
            executable.write_text(
                "#!/bin/sh\n"
                "printf '%s\\n' "
                '\'{"status":"fail","reasonCode":"contract_invariant_failed",'
                '"appleAvailable":true,"localeSupported":true,'
                '"contextSize":1,"occupiedTokens":0,"appleAttempts":1,'
                '"condensation":null}\'\n',
                encoding="utf-8",
            )
            executable.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
            request = {
                "diagnosticText": diagnostic_text(),
                "sourceFacts": adapter.source_facts(diagnostic_text()),
            }

            result = adapter.run_bridge_process(
                request,
                executable=executable,
                timeout_seconds=1,
            )

            self.assertEqual("fail", result["status"])
            self.assertEqual(1, result["appleAttempts"])


class ProductionPathTests(unittest.TestCase):
    def test_bound_path_rejects_relative_symlink_and_drift(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            root = Path(directory)
            regular = root / "regular"
            regular.write_text("ok", encoding="utf-8")
            link = root / "link"
            link.symlink_to(regular)

            with self.assertRaises(ValueError):
                adapter.BoundPath.capture(Path("relative"))
            with self.assertRaises(ValueError):
                adapter.BoundPath.capture(link)

            captured = adapter.BoundPath.capture(regular)
            regular.write_text("changed", encoding="utf-8")
            with self.assertRaises(ValueError):
                captured.recheck()

    def test_benchmark_observation_is_absent_by_default(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(adapter._configured_observation_path(ROOT))

    def test_benchmark_observation_is_secure_closed_and_one_shot(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            repo = Path(directory)
            parent = repo / adapter.OBSERVATION_DIRECTORY
            parent.mkdir()
            path = parent / adapter.OBSERVATION_BASENAME
            with mock.patch.dict(
                os.environ,
                {adapter.OBSERVATION_ENV: str(path)},
                clear=True,
            ):
                self.assertEqual(
                    path,
                    adapter._configured_observation_path(repo),
                )
                observer = adapter.BenchmarkObserver(consultation_for)
                started = __import__("time").monotonic_ns()
                response = adapter.evaluate(
                    payload(),
                    contract=contract,
                    consult=observer.consult,
                    repo_root=ROOT,
                    observe=observer.observe,
                )
                value = observer.finish(
                    response,
                    __import__("time").monotonic_ns() - started,
                    serialized_hook_response(response),
                )
                adapter._write_observation(path, value)

            self.assertEqual(0o600, stat.S_IMODE(path.stat().st_mode))
            self.assertEqual(1, path.read_bytes().count(b"\n"))
            decoded = json.loads(path.read_text())
            self.assertEqual(set(adapter.OBSERVATION_KEYS), set(decoded))
            self.assertEqual("replacement_emitted", decoded["status"])
            self.assertEqual(2, decoded["schemaVersion"])
            self.assertIsNone(decoded["preflightStage"])
            self.assertEqual(1, decoded["appleAttempts"])
            self.assertEqual(1, decoded["appleValidResults"])
            self.assertTrue(decoded["replacementEmitted"])
            self.assertEqual(
                hashlib.sha256(
                    response["stopReason"].encode("utf-8")
                ).hexdigest(),
                decoded["replacementSha256"],
            )
            self.assertEqual(
                len(response["stopReason"].encode("utf-8")),
                decoded["replacementBytes"],
            )
            self.assertEqual(1, decoded["appleLatencySamples"])
            with self.assertRaises(FileExistsError):
                adapter._write_observation(path, value)

        observer = adapter.BenchmarkObserver(consultation_for)
        response = adapter.evaluate(
            payload(),
            contract=contract,
            consult=observer.consult,
            repo_root=ROOT,
            observe=observer.observe,
        )
        malformed = observer.finish(response, 1, b"{}\n")
        self.assertEqual("blocked", malformed["status"])
        self.assertFalse(malformed["replacementEmitted"])
        for changed in (
            {**response, "continue": True},
            {"continue": False},
            {**response, "extra": True},
            {**response, "stopReason": 1},
        ):
            with self.subTest(response=changed):
                malformed = observer.finish(
                    changed,
                    1,
                    serialized_hook_response(changed),
                )
                self.assertEqual("blocked", malformed["status"])
                self.assertFalse(malformed["replacementEmitted"])

    def test_benchmark_observation_failure_is_blocked_and_preserves_one_shot(self):
        calls = []

        def unavailable(_request):
            calls.append(True)
            raise TimeoutError

        observer = adapter.BenchmarkObserver(unavailable)
        response = adapter.evaluate(
            payload(),
            contract=contract,
            consult=observer.consult,
            repo_root=ROOT,
            observe=observer.observe,
        )
        value = observer.finish(response, 1)

        self.assertIsNone(response)
        self.assertEqual([True], calls)
        self.assertEqual("blocked", value["status"])
        self.assertEqual(
            "apple_attempt_count_uncertain",
            value["reasonCode"],
        )
        self.assertIsNone(value["appleAttempts"])
        self.assertEqual(0, value["appleValidResults"])
        self.assertFalse(value["replacementEmitted"])
        self.assertIsNone(value["replacementSha256"])
        self.assertIsNone(value["preflightStage"])

    def test_benchmark_fallback_attempt_and_latency_invariants(self):
        zero_attempts = tuple(
            (
                {
                    **consultation_for(
                        {"fields": [{"value": diagnostic_text()}]}
                    ),
                    "status": "declined",
                    "reasonCode": stage,
                    "appleAvailable": stage != "apple_unavailable",
                    "localeSupported": stage not in {
                        "apple_unavailable", "locale_unsupported"
                    },
                    "appleAttempts": 0,
                    "condensation": None,
                },
                0,
                0,
                stage,
            )
            for stage in adapter.PREFLIGHT_STAGES
        )
        variants = zero_attempts + (
            (
                {
                    **consultation_for(
                        {"fields": [{"value": diagnostic_text()}]}
                    ),
                    "status": "fail",
                    "reasonCode": "contract_invariant_failed",
                    "appleAttempts": 1,
                    "condensation": None,
                },
                1,
                1,
                None,
            ),
        )
        for consultation, attempts, samples, stage in variants:
            with self.subTest(attempts=attempts):
                observer = adapter.BenchmarkObserver(
                    lambda _request, value=consultation: value
                )
                response = adapter.evaluate(
                    payload(),
                    contract=contract,
                    consult=observer.consult,
                    repo_root=ROOT,
                    observe=observer.observe,
                )
                value = observer.finish(response, 1)
                self.assertEqual("fallback", value["status"])
                self.assertEqual(attempts, value["appleAttempts"])
                self.assertEqual(samples, value["appleLatencySamples"])
                self.assertEqual(stage, value["preflightStage"])
                self.assertEqual(
                    samples == 1,
                    value["appleLatencyNanoseconds"] is not None,
                )

        invalid = {
            **zero_attempts[0][0],
            "reasonCode": "generation_rate_limited",
        }
        observer = adapter.BenchmarkObserver(lambda _request: invalid)
        response = adapter.evaluate(
            payload(), contract=contract, consult=observer.consult,
            repo_root=ROOT, observe=observer.observe,
        )
        value = observer.finish(response, 1)
        self.assertEqual("blocked", value["status"])
        self.assertIsNone(value["preflightStage"])

    def test_benchmark_observation_rejects_replaced_captured_parent(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            repo = Path(directory)
            parent = repo / adapter.OBSERVATION_DIRECTORY
            parent.mkdir()
            expected_parent = adapter._directory_identity(parent)
            moved = repo / "old-observation-parent"
            parent.rename(moved)
            parent.mkdir()
            path = parent / adapter.OBSERVATION_BASENAME
            observer = adapter.BenchmarkObserver(consultation_for)
            response = adapter.evaluate(
                payload(),
                contract=contract,
                consult=observer.consult,
                repo_root=ROOT,
                observe=observer.observe,
            )
            with self.assertRaisesRegex(ValueError, "identity drift"):
                adapter._write_observation(
                    path,
                    observer.finish(
                        response,
                        1,
                        serialized_hook_response(response),
                    ),
                    expected_parent_identity=expected_parent,
                )
            self.assertFalse(path.exists())

    def test_benchmark_observation_rejects_uncontained_or_preexisting_path(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            repo = Path(directory)
            parent = repo / adapter.OBSERVATION_DIRECTORY
            parent.mkdir()
            expected = parent / adapter.OBSERVATION_BASENAME
            outside = repo / adapter.OBSERVATION_BASENAME
            for candidate in (Path("relative"), outside):
                with self.subTest(candidate=candidate), mock.patch.dict(
                    os.environ,
                    {adapter.OBSERVATION_ENV: str(candidate)},
                    clear=True,
                ):
                    with self.assertRaises(ValueError):
                        adapter._configured_observation_path(repo)
            expected.write_text("occupied", encoding="utf-8")
            with mock.patch.dict(
                os.environ,
                {adapter.OBSERVATION_ENV: str(expected)},
                clear=True,
            ):
                with self.assertRaises(ValueError):
                    adapter._configured_observation_path(repo)

    def test_benchmark_observation_rejects_invalid_union_and_short_write(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            repo = Path(directory)
            parent = repo / adapter.OBSERVATION_DIRECTORY
            parent.mkdir()
            path = parent / adapter.OBSERVATION_BASENAME
            observer = adapter.BenchmarkObserver(consultation_for)
            response = adapter.evaluate(
                payload(),
                contract=contract,
                consult=observer.consult,
                repo_root=ROOT,
                observe=observer.observe,
            )
            value = observer.finish(
                response,
                1,
                serialized_hook_response(response),
            )
            for mutation in (
                {**value, "schemaVersion": 1},
                {key: item for key, item in value.items() if key != "preflightStage"},
                {**value, "preflightStage": "private"},
                {**value, "preflightStage": []},
                {**value, "preflightStage": {}},
                {**value, "appleAttempts": 0},
                {**value, "preflightStage": "apple_unavailable"},
            ):
                with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                    adapter._write_observation(path, mutation)
            with mock.patch.object(
                adapter.os,
                "write",
                return_value=1,
            ), self.assertRaises(ValueError):
                adapter._write_observation(path, value)

    def test_emitted_receipt_follows_full_stdout_flush_and_is_terminal(self):
        observation = {
            "preReceiptHookLatencyNanoseconds": 0,
            "status": "replacement_emitted",
        }
        events = []

        class Output:
            def __init__(self, *, short=False, flush_error=False):
                self.buffer = self
                self.short = short
                self.flush_error = flush_error

            def write(self, value):
                events.append(("stdout", value))
                return len(value) - 1 if self.short else len(value)

            def flush(self):
                events.append(("flush", None))
                if self.flush_error:
                    raise OSError("flush failed")

        def receipt(*_arguments, **_keywords):
            events.append(("receipt", observation["status"]))

        with mock.patch.object(sys, "stdout", Output()), mock.patch.object(
            adapter, "_write_observation", side_effect=receipt
        ):
            adapter._emit_replacement_receipt(
                b"replacement\n",
                Path("/unused"),
                observation,
                started=__import__("time").monotonic_ns(),
                expected_parent_identity=(1, 2, 3, 4),
            )
        self.assertEqual(
            ["stdout", "flush", "receipt"],
            [event[0] for event in events],
        )
        self.assertGreaterEqual(
            observation["preReceiptHookLatencyNanoseconds"], 0
        )

        for output in (Output(short=True), Output(flush_error=True)):
            events.clear()
            with self.subTest(output=output), mock.patch.object(
                sys, "stdout", output
            ), mock.patch.object(
                adapter, "_write_observation"
            ) as write_receipt, self.assertRaises(
                (ValueError, OSError)
            ):
                adapter._emit_replacement_receipt(
                    b"replacement\n",
                    Path("/unused"),
                    dict(observation),
                    started=__import__("time").monotonic_ns(),
                    expected_parent_identity=(1, 2, 3, 4),
                )
            write_receipt.assert_not_called()

        events.clear()
        with mock.patch.object(sys, "stdout", Output()), mock.patch.object(
            adapter,
            "_write_observation",
            side_effect=OSError("receipt failed"),
        ), self.assertRaises(OSError):
            adapter._emit_replacement_receipt(
                b"replacement\n",
                Path("/unused"),
                dict(observation),
                started=__import__("time").monotonic_ns(),
                expected_parent_identity=(1, 2, 3, 4),
            )
        self.assertEqual(["stdout", "flush"], [event[0] for event in events])
        self.assertEqual("replacement_emitted", observation["status"])

    def test_benchmark_observation_detects_post_close_leaf_swap(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            repo = Path(directory)
            parent = repo / adapter.OBSERVATION_DIRECTORY
            parent.mkdir()
            path = parent / adapter.OBSERVATION_BASENAME
            observer = adapter.BenchmarkObserver(consultation_for)
            response = adapter.evaluate(
                payload(),
                contract=contract,
                consult=observer.consult,
                repo_root=ROOT,
                observe=observer.observe,
            )
            value = observer.finish(
                response,
                1,
                serialized_hook_response(response),
            )
            real_close = os.close

            def close_and_swap(descriptor):
                real_close(descriptor)
                path.unlink()
                path.write_text("{}\n", encoding="utf-8")
                path.chmod(0o600)

            with mock.patch.object(
                adapter.os,
                "close",
                side_effect=close_and_swap,
            ), self.assertRaises(ValueError):
                adapter._write_observation(path, value)

    def test_adapter_main_writes_observation_and_emits_validated_replacement(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            repo = Path(directory)
            observation_parent = repo / adapter.OBSERVATION_DIRECTORY
            observation_parent.mkdir()
            observation = (
                observation_parent / adapter.OBSERVATION_BASENAME
            )
            bridge = repo / "bridge"
            bridge.write_text(
                f"#!{sys.executable}\n"
                "import json, sys\n"
                "request = json.load(sys.stdin)\n"
                "json.dump({\n"
                " 'status': 'applied', 'reasonCode': None,\n"
                " 'appleAvailable': True, 'localeSupported': True,\n"
                " 'contextSize': 32768, 'occupiedTokens': 4096,\n"
                " 'appleAttempts': 1,\n"
                " 'condensation': request['sourceFacts'],\n"
                "}, sys.stdout, separators=(',', ':'), sort_keys=True)\n"
                "sys.stdout.write('\\n')\n",
                encoding="utf-8",
                newline="\n",
            )
            bridge.chmod(0o700)
            candidate = payload()
            candidate["cwd"] = str(repo)
            environment = {
                **os.environ,
                "PLUGIN_ROOT": str(
                    ROOT / "plugins/apple-foundation-models-handoff"
                ),
                "RUNTIME_V1_REPO_ROOT": str(repo),
                "RUNTIME_V1_BRIDGE_EXECUTABLE": str(bridge),
                adapter.OBSERVATION_ENV: str(observation),
                "PYTHONDONTWRITEBYTECODE": "1",
            }
            completed = __import__("subprocess").run(
                [sys.executable, str(ADAPTER)],
                input=json.dumps(candidate).encode(),
                env=environment,
                stdout=__import__("subprocess").PIPE,
                stderr=__import__("subprocess").PIPE,
                check=False,
            )

            self.assertEqual(0, completed.returncode)
            self.assertEqual(b"", completed.stderr)
            response = json.loads(completed.stdout)
            self.assertEqual(
                adapter.source_facts(diagnostic_text()),
                json.loads(response["stopReason"]),
            )
            observed = json.loads(observation.read_text())
            self.assertEqual("replacement_emitted", observed["status"])
            self.assertTrue(observed["replacementEmitted"])


class ProductionSwiftTests(unittest.TestCase):
    def test_swift_preserves_the_proved_constrained_single_response(self):
        source = SWIFT.read_text()
        for required in (
            "SystemLanguageModel.default",
            "LiteralDiagnosticExtraction",
            "GenerationSchema(",
            ".constant(value)",
            ".range(value...value)",
            "for: constrainedSchema",
            "tools: []",
            "schema: constrainedSchema",
            "maximumResponseTokens: 1024",
            "let appleAttempts = 1",
            "validatedCondensation(",
        ):
            self.assertIn(required, source)
        self.assertEqual(1, source.count("session.respond("))
        self.assertNotIn("What was the result of this synthetic unit test?", source)

    def test_swift_sends_only_minimized_facts_to_apple(self):
        source = SWIFT.read_text()
        bridge_input = source[
            source.index("struct BridgeInput:"):
            source.index("struct BridgeOutput:")
        ]
        consult = source[source.index("func consult("):source.index("@main")]
        self.assertIn("let diagnosticText: String", bridge_input)
        self.assertIn("let sourceFacts: DiagnosticCondensation", bridge_input)
        self.assertNotIn("input.diagnosticText", consult)
        self.assertNotIn("Diagnostic record:", consult)
        self.assertEqual(1, consult.count("let prompt = Prompt("))
        self.assertIn(
            '"Return the exact literal values required by the constrained schema."',
            consult,
        )
        for required in (
            "tokenCount(for: prompt)",
            "to: prompt",
            "schema: constrainedSchema",
            ".constant(value)",
            ".range(value...value)",
            "validatedCondensation(",
            "generated == sourceFacts",
            "tools: []",
            "sampling: .greedy",
            "maximumResponseTokens: 1024",
            "let appleAttempts = 1",
        ):
            self.assertIn(required, source)
        self.assertEqual(1, consult.count("session.respond("))


class ProductionHarnessTests(unittest.TestCase):
    def test_production_harness_entrypoint_exists(self):
        self.assertTrue(PRODUCTION_HARNESS.is_file())

    def test_harness_reuses_only_proved_host_boundary_helpers(self):
        for name in (
            "capture_codex",
            "capture_python",
            "tree_sha256",
            "trust_hook",
            "responses_server",
            "atomic_write_json",
        ):
            self.assertIs(getattr(harness, name), getattr(harness.helpers, name))

    def test_harness_fixture_is_closed_and_production_parseable(self):
        self.assertGreaterEqual(len(harness.stimulus_bytes("C0")), 8192)
        contract._validate_source_facts(
            adapter.source_facts(harness._record("C0"))
        )
        with self.assertRaises(ValueError):
            adapter.source_facts(harness._record("C2"))

    def test_harness_binds_the_installed_root_and_three_explicit_variables(self):
        source = PRODUCTION_HARNESS.read_text()
        for required in (
            '"RUNTIME_V1_PYTHON"',
            '"RUNTIME_V1_BRIDGE_EXECUTABLE"',
            '"RUNTIME_V1_REPO_ROOT"',
            "tree_sha256(installed) != plugin_sha256",
            'for classification in ("C0", "C2")',
            "compile_bridge(staged, xcrun=sdk_resolved)",
            "--approved-plugin-sha256",
            "--approved-hook-hash",
            "unsafe_evidence_findings",
            "recheck_sdk(",
            "VerifiedTerminal",
        ):
            self.assertIn(required, source)
        self.assertNotIn("RUNTIME_V1_PLUGIN_ROOT", source)
        self.assertNotIn('"RUNTIME_V1_COMMAND_COUNTER":', source)
        self.assertNotIn('"RUNTIME_V1_LOCAL_PROVIDER_KEY":', source)

    def test_harness_applied_oracle_requires_exact_valid_result(self):
        candidate = payload(
            harness.stimulus_bytes("C0").decode("utf-8")
        )
        candidate["tool_use_id"] = "call-runtime-v1"
        response, _ = ProductionAdapterTests().evaluate(candidate)
        encoded = response["stopReason"].encode("utf-8")

        original = harness.stimulus_bytes("C0")
        digest = harness._validated_applied_output(encoded, original)

        self.assertEqual(
            __import__("hashlib").sha256(encoded).hexdigest(),
            digest,
        )
        facts = json.loads(encoded)
        prior_wrapper = {
            "schemaVersion": 1,
            "policyVersion": "diagnostic-condensation-v1",
            "callID": "call-runtime-v1",
            "toolName": "Bash",
            "toolVersion": "codex-cli-0.145.0",
            "stateVersion": "runtime-v1-direct-consultation-v1",
            "action": "condense_diagnostic_output",
            "commandClass": "test",
            "originalResultType": "string",
            "originalResultDigest": hashlib.sha256(original).hexdigest(),
            "outcome": "applied",
            "exitStatus": 0,
            "interrupted": False,
            "resultType": "diagnostic_condensation",
            "condensation": facts,
        }
        missing = dict(facts)
        missing.pop("summary")
        extra = {**facts, "unexpected": True}
        altered = {**facts, "summary": "altered"}
        duplicate = (
            b'{"commandOutcome":"success",'
            + encoded[1:]
        )
        invalid = (
            encoded + b"\n",
            json.dumps(facts, indent=2).encode("utf-8"),
            json.dumps(prior_wrapper, separators=(",", ":"), sort_keys=True).encode(),
            json.dumps(missing, separators=(",", ":"), sort_keys=True).encode(),
            json.dumps(extra, separators=(",", ":"), sort_keys=True).encode(),
            json.dumps(altered, separators=(",", ":"), sort_keys=True).encode(),
            duplicate,
            b"\xff",
        )
        for candidate_output in invalid:
            with self.subTest(candidate_output=candidate_output[:20]):
                with self.assertRaises(harness.ProbeFailure):
                    harness._validated_applied_output(candidate_output, original)

    def test_harness_evidence_scan_detects_raw_and_private_content(self):
        self.assertEqual(
            0,
            harness.unsafe_evidence_findings(
                {"codexExecutable": "<host-path>", "status": "pass"}
            ),
        )
        self.assertGreater(
            harness.unsafe_evidence_findings(
                {"diagnosticText": harness._record("C0")}
            ),
            0,
        )

    def test_harness_verifies_cleanup_on_failure_and_cleanup_error(self):
        with mock.patch.object(
            harness,
            "_execute_in_temporary",
            side_effect=harness.ProbeFailure("synthetic_failure"),
        ):
            with self.assertRaises(harness.VerifiedTerminal) as raised:
                harness.execute(
                    codex_executable=Path("/unreached"),
                    python_executable=Path("/unreached"),
                    approved_plugin_sha256="a" * 64,
                    approved_hook_hash="sha256:" + ("b" * 64),
                    inspect_only=False,
                )
        self.assertEqual("complete", raised.exception.cleanup_status)

        directory = tempfile.mkdtemp(dir=ROOT)

        class FailedCleanup:
            name = directory

            def cleanup(self):
                raise OSError

        try:
            with (
                mock.patch.object(
                    harness.tempfile,
                    "TemporaryDirectory",
                    return_value=FailedCleanup(),
                ),
                mock.patch.object(
                    harness,
                    "_execute_in_temporary",
                    side_effect=harness.ProbeFailure("synthetic_failure"),
                ),
                self.assertRaises(harness.VerifiedTerminal) as raised,
            ):
                harness.execute(
                    codex_executable=Path("/unreached"),
                    python_executable=Path("/unreached"),
                    approved_plugin_sha256="a" * 64,
                    approved_hook_hash="sha256:" + ("b" * 64),
                    inspect_only=False,
                )
            self.assertEqual("blocked", raised.exception.status)
            self.assertEqual("cleanup_incomplete", raised.exception.reason)
            self.assertEqual("incomplete", raised.exception.cleanup_status)
        finally:
            shutil.rmtree(directory)


if __name__ == "__main__":
    unittest.main()
