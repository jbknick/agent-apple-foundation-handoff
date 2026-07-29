from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest


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

        def consult(request):
            calls.append(request)
            return consultation_for(request)

        response, observations = self.evaluate(payload(), consult)

        self.assertEqual(1, len(calls))
        self.assertEqual({"diagnosticText", "sourceFacts"}, set(calls[0]))
        self.assertEqual({"continue", "stopReason"}, set(response))
        self.assertIs(response["continue"], False)
        result = json.loads(response["stopReason"])
        contract.validate_result(result)
        self.assertEqual("applied", result["outcome"])
        self.assertEqual(0, result["exitStatus"])
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

    def test_failure_preserves_exact_exit_status(self):
        response, _ = self.evaluate(payload(diagnostic_text(exit_status=65)))

        result = json.loads(response["stopReason"])
        self.assertEqual("applied", result["outcome"])
        self.assertEqual(65, result["exitStatus"])

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
                    self.assertEqual("applied", result["outcome"])
                    self.assertEqual(
                        case["expected"]["exitStatus"],
                        result["exitStatus"],
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


if __name__ == "__main__":
    unittest.main()
