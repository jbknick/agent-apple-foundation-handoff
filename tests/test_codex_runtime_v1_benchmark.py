import importlib.util
import json
import os
from copy import deepcopy
from pathlib import Path
import stat
import sys
import tempfile
import tomllib
import urllib.error
import urllib.request
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "tests/e2e/codex_runtime_v1_benchmark.py"
SPEC = importlib.util.spec_from_file_location("codex_runtime_v1_benchmark", RUNNER_PATH)
runner = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = runner
assert SPEC.loader is not None
SPEC.loader.exec_module(runner)


class RuntimeV1RunnerTests(unittest.TestCase):
    def _forwarding_boundary_failure(
        self,
        *,
        run_error=None,
        provider_exit_error=None,
        cleanup_error=None,
        direct_requests_error=None,
        request_count=2,
        command_counter_value="1",
        run_check=None,
    ):
        codex = mock.Mock(
            resolved=Path("/host/codex"), version="0.145.0"
        )
        python = mock.Mock(resolved=Path(sys.executable))
        server = mock.Mock(
            server_address=("127.0.0.1", 1234),
            requests=[{} for _ in range(request_count)],
        )
        provider = mock.MagicMock()
        provider.__enter__.return_value = server
        provider.__exit__.side_effect = provider_exit_error
        rpc = mock.MagicMock()
        parsed = runner.ParsedEvents(
            usage=mock.Mock(),
            command_executions=1,
            completed_parent_turns=1,
            final_agent_message="",
        )

        def run_once(*_arguments, **arguments):
            if run_error is not None:
                raise run_error
            if run_check is not None:
                run_check(arguments)
            if command_counter_value is not None:
                Path(
                    arguments["env"]["DEV254_PROBE_COMMAND_COUNTER"]
                ).write_text(command_counter_value, encoding="utf-8")
            Path(
                arguments["env"]["RUNTIME_V1_BENCHMARK_OBSERVATION_PATH"]
            ).write_text("{}", encoding="utf-8")
            return mock.Mock(returncode=0, stderr=b"", stdout=b"events")

        observation = {
            "status": "replacement_emitted",
            "replacementEmitted": True,
            "replacementBytes": len(b"forwarded"),
            "replacementSha256": runner.hashlib.sha256(
                b"forwarded"
            ).hexdigest(),
        }
        unlink_error = OSError("private unlink detail") if (
            cleanup_error == "unlink"
        ) else None
        rmdir_error = OSError("private rmdir detail") if (
            cleanup_error == "rmdir"
        ) else None
        with mock.patch.object(
            runner.shutil,
            "copytree",
            side_effect=lambda _source, target, **_kwargs: target.mkdir(),
        ), mock.patch.object(
            runner,
            "install_plugin",
            return_value=(
                {
                    "CODEX_HOME": "/isolated/codex-home",
                    "PATH": "/isolated/bin",
                    "PYTHONDONTWRITEBYTECODE": "1",
                    "RUNTIME_V1_PYTHON": sys.executable,
                },
                Path("/installed"),
            ),
        ), mock.patch.object(
            runner.production,
            "materialize_workspace",
            side_effect=lambda path, **_kwargs: path.mkdir(),
        ), mock.patch.object(
            runner.production,
            "JsonRpcProcess",
            return_value=rpc,
        ), mock.patch.object(
            runner,
            "trust_hook",
        ), mock.patch.object(
            runner.production,
            "responses_server",
            return_value=provider,
        ), mock.patch.object(
            runner.subprocess,
            "run",
            side_effect=run_once,
        ) as run, mock.patch.object(
            runner,
            "discard_classified_codex_stderr",
            wraps=runner.discard_classified_codex_stderr,
        ), mock.patch.object(
            runner,
            "parse_event_stream",
            return_value=parsed,
        ), mock.patch.object(
            runner,
            "_require_code_mode_exec_requests",
            side_effect=direct_requests_error,
        ), mock.patch.object(
            runner.production,
            "stimulus_bytes",
            return_value=b"original",
        ), mock.patch.object(
            runner,
            "_sole_forwarded_custom_tool_output",
            return_value=b"forwarded",
        ), mock.patch.object(
            runner,
            "consume_runtime_v1_observation",
            return_value=observation,
        ), mock.patch.object(
            Path,
            "unlink",
            autospec=True,
            side_effect=unlink_error,
        ), mock.patch.object(
            Path,
            "rmdir",
            autospec=True,
            side_effect=rmdir_error,
        ), self.assertRaises(
            runner.ForwardingPreflightBlocked
        ) as caught:
            runner.run_forwarding_preflight(
                codex=codex,
                python=python,
                candidate_commit="a" * 40,
                production_identities=self.identities(),
                approved_hook_hash="sha256:" + "b" * 64,
            )
        return caught.exception, run.call_count

    def test_exact_executable_capture_and_recheck_detects_drift(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            executable = Path(directory) / "codex"
            executable.write_text(
                "#!/bin/sh\nprintf 'codex-cli 0.145.0\\n'\n",
                encoding="utf-8",
            )
            executable.chmod(
                stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR
            )
            captured = runner.capture_codex(executable)
            captured.recheck()
            executable.write_text(
                "#!/bin/sh\nprintf 'codex-cli 0.145.1\\n'\n",
                encoding="utf-8",
            )
            with self.assertRaises(runner.production.ProbeFailure):
                captured.recheck()

    def test_imported_probe_errors_are_stable_and_path_free(self):
        with mock.patch.object(
            runner,
            "capture_codex",
            side_effect=runner.production.ProbeBlocked(
                "/private/raw-capture-detail"
            ),
        ), self.assertRaisesRegex(
            runner.BenchmarkBlocked,
            "^host_prerequisite_unavailable$",
        ):
            runner.capture_hosts(Path("/private/codex"), Path("/private/python"))
        with mock.patch.object(
            runner,
            "_execute_benchmark_arm",
            side_effect=runner.production.ProbeFailure(
                "/Users/raw-drift-detail"
            ),
        ), self.assertRaisesRegex(
            runner.BenchmarkFailure,
            "^production_identity_drift$",
        ):
            runner._run_benchmark_arm()

        class Drifting:
            def recheck(self):
                raise runner.production.ProbeFailure(
                    "/private/raw-recheck-detail"
                )

        with self.assertRaisesRegex(
            runner.BenchmarkFailure,
            "^host_identity_drift$",
        ):
            runner.recheck_hosts(Drifting(), Drifting())

    def test_coordinates_are_exact_and_deterministic(self):
        coordinates = runner.fixed_pair_coordinates()
        self.assertEqual(len(coordinates), 24)
        self.assertEqual(
            [row["fixtureID"] for row in coordinates],
            list(runner.contract.EXACT_DEV142_FIXTURE_IDS),
        )
        self.assertTrue(all(row["codexVersion"] == "0.145.0" for row in coordinates))
        self.assertTrue(all(row["parentModel"] == "gpt-5.6-sol" for row in coordinates))
        self.assertTrue(all(row["reasoningEffort"] == "medium" for row in coordinates))

    def test_capture_candidate_requires_clean_exact_ancestor(self):
        calls = []

        def clean(args):
            calls.append(tuple(args))
            values = {
                ("rev-parse", "HEAD"): "a" * 40 + "\n",
                ("status", "--porcelain"): "",
                ("merge-base", "--is-ancestor", runner.PRODUCTION_COMMIT, "a" * 40): "",
            }
            return values[tuple(args)]

        captured = runner.capture_candidate_identity(
            ROOT, "a" * 40, run_git=clean
        )
        self.assertEqual(captured.candidate_commit, "a" * 40)
        self.assertIn(("status", "--porcelain"), calls)
        with self.assertRaises(runner.BenchmarkFailure):
            runner.capture_candidate_identity(
                ROOT,
                "a" * 40,
                run_git=lambda args: "dirty\n" if args[0] == "status" else "a" * 40 + "\n",
            )

    def test_build_exec_arguments_is_one_direct_codex_invocation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            schema = runner.materialize_parent_output_schema(root)
            args = runner.build_exec_arguments(
                root / "workspace",
                root / "output",
                schema,
                "approved task",
            )
        self.assertEqual(args[0], "exec")
        self.assertEqual(args.count("exec"), 1)
        self.assertEqual(args.count("--output-schema"), 1)
        self.assertEqual(args[args.index("--output-schema") + 1], str(schema))
        self.assertIn("gpt-5.6-sol", args)
        self.assertIn('model_reasoning_effort="medium"', args)
        self.assertEqual(
            [
                argument
                for argument in args
                if argument.startswith("model_providers.openai.")
            ],
            [
                "model_providers.openai.request_max_retries=0",
                "model_providers.openai.stream_max_retries=0",
            ],
        )
        self.assertEqual(args[-1], "approved task")

    def test_parent_output_schema_is_closed_and_dev142_compatible(self):
        schema = runner.parent_output_schema()
        supported = {
            "type", "pattern", "enum", "minimum", "properties", "required",
            "additionalProperties", "items", "minItems",
        }

        def matches(value, rule):
            self.assertFalse(set(rule) - supported)
            kinds = rule["type"]
            if type(kinds) is str:
                kinds = [kinds]
            type_matches = {
                "null": lambda item: item is None,
                "string": lambda item: type(item) is str,
                "integer": lambda item: type(item) is int,
                "array": lambda item: type(item) is list,
                "object": lambda item: type(item) is dict,
            }
            if not any(type_matches[kind](value) for kind in kinds):
                return False
            if value is None:
                return True
            if "enum" in rule and value not in rule["enum"]:
                return False
            if "pattern" in rule and __import__("re").search(
                rule["pattern"], value
            ) is None:
                return False
            if "minimum" in rule and value < rule["minimum"]:
                return False
            if type(value) is list:
                return len(value) >= rule.get("minItems", 0) and all(
                    matches(item, rule["items"]) for item in value
                )
            if type(value) is dict:
                required = set(rule["required"])
                if not required.issubset(value):
                    return False
                if rule["additionalProperties"] is False and set(value) != set(
                    rule["properties"]
                ):
                    return False
                return all(
                    matches(value[key], child)
                    for key, child in rule["properties"].items()
                )
            return True

        expected = {
            "commandOutcome", "summary", "summaryFacts", "diagnostics",
            "warningCount", "omittedWarningCount", "nextAction",
            "completionFacts",
        }
        self.assertEqual(set(schema["properties"]), expected)
        self.assertEqual(set(schema["required"]), expected)
        self.assertIs(schema["additionalProperties"], False)
        diagnostic = schema["properties"]["diagnostics"]["items"]
        self.assertEqual(
            set(diagnostic["required"]),
            {
                "id", "severity", "code", "message", "file", "line",
                "column", "failedTestID",
            },
        )
        self.assertIs(diagnostic["additionalProperties"], False)
        encoded = json.dumps(schema, separators=(",", ":"), sort_keys=True)
        self.assertNotIn("uniqueItems", encoded)
        valid_facts = []
        for case in runner._corpus_cases():
            facts = runner.production.adapter.source_facts(
                runner.contract._DEV142.render_case(case).decode("utf-8")
            )
            valid_facts.append(facts)
            self.assertTrue(matches(facts, schema))
            result = {
                "schemaVersion": 1,
                "policyVersion": "diagnostic-condensation-v1",
                "callID": "parent-outcome",
                "toolName": "Bash",
                "toolVersion": "codex-cli-0.145.0",
                "stateVersion": "runtime-v1-direct-consultation-v1",
                "action": "condense_diagnostic_output",
                "commandClass": case["commandClass"],
                "originalResultType": "string",
                "originalResultDigest": case["renderedSha256"],
                "outcome": "applied",
                "exitStatus": case["expected"]["exitStatus"],
                "interrupted": case["expected"]["interrupted"],
                "resultType": "diagnostic_condensation",
                "condensation": facts,
            }
            self.assertIs(runner.contract._DEV142.validate_result(result), result)
        for invalid in (
            {key: value for key, value in valid_facts[0].items() if key != "summary"},
            {**valid_facts[0], "extra": None},
            {**valid_facts[0], "summary": ""},
            {**valid_facts[0], "summaryFacts": []},
            {**valid_facts[0], "warningCount": -1},
            {
                **valid_facts[0],
                "diagnostics": [
                    {**valid_facts[0]["diagnostics"][0], "severity": "unknown"}
                ],
            },
        ):
            with self.subTest(invalid=tuple(invalid)):
                self.assertFalse(matches(invalid, schema))
        application_only = deepcopy(valid_facts[0])
        application_only["summaryFacts"].append(
            application_only["summaryFacts"][0]
        )
        self.assertTrue(matches(application_only, schema))
        with self.assertRaises(runner.contract._DEV142.ContractError):
            runner.contract._DEV142.validate_result(
                {**result, "condensation": application_only}
            )

    def test_parent_output_schema_file_is_private_bound_and_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            schema = runner.materialize_parent_output_schema(root)
            self.assertEqual(stat.S_IMODE(schema.stat().st_mode), 0o600)
            self.assertIsNone(runner.validate_parent_output_schema(schema))
            schema.write_bytes(b"{}")
            with self.assertRaisesRegex(
                runner.BenchmarkBlocked, "^parent_output_schema_invalid$"
            ):
                runner.build_exec_arguments(
                    root / "workspace",
                    root / "output",
                    schema,
                    "approved task",
                )

    def test_forwarding_preflight_uses_benchmark_model_and_effort(self):
        args = runner._forwarding_exec_arguments(
            "http://127.0.0.1:1234", Path("/tmp/workspace")
        )
        self.assertEqual(args.count("exec"), 1)
        self.assertEqual(args.count("-m"), 1)
        self.assertEqual(args[args.index("-m") + 1], "gpt-5.6-sol")
        self.assertEqual(
            sum(
                argument.startswith("model_reasoning_effort=")
                for argument in args
            ),
            1,
        )
        self.assertNotIn("gpt-5.1-codex", args)
        with mock.patch.object(
            runner.production,
            "_exec_arguments",
            return_value=["exec", "-m", "drifted-model"],
        ), self.assertRaisesRegex(
            runner.BenchmarkBlocked,
            "^replacement_forwarding_unproven$",
        ):
            runner._forwarding_exec_arguments(
                "http://127.0.0.1:1234", Path("/tmp/workspace")
            )
        with mock.patch.object(
            runner.production,
            "_exec_arguments",
            return_value=[
                "exec", "-c", 'model_reasoning_effort="high"',
                "-m", "gpt-5.1-codex",
            ],
        ), self.assertRaisesRegex(
            runner.BenchmarkBlocked,
            "^replacement_forwarding_unproven$",
        ):
            runner._forwarding_exec_arguments(
                "http://127.0.0.1:1234", Path("/tmp/workspace")
            )

    def test_fixture_workspace_executes_exact_rendered_dev142_output(self):
        case = runner._corpus_cases()[12]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            workspace, rendered = runner._materialize_workspace(root, case)
            environment = {
                **os.environ,
                "PATH": f"{root / 'bin'}:{os.environ.get('PATH', '')}",
                "DEV255_FIXTURE_OUTPUT": str(root / "fixture-output"),
                "DEV255_FIXTURE_EXIT": str(case["expected"]["exitStatus"]),
            }
            completed = __import__("subprocess").run(
                runner._command_for_case(case).split(),
                cwd=workspace,
                env=environment,
                stdout=__import__("subprocess").PIPE,
                stderr=__import__("subprocess").PIPE,
                check=False,
            )
            self.assertEqual(rendered, completed.stdout)
            self.assertEqual(case["expected"]["exitStatus"], completed.returncode)
            self.assertEqual(b"", completed.stderr)

    def test_parent_outcome_is_hash_bound_and_dev142_scored(self):
        case = runner._corpus_cases()[0]
        facts = runner.production.adapter.source_facts(
            runner.contract._DEV142.render_case(case).decode("utf-8")
        )
        coordinate = runner.fixed_pair_coordinates()[0]
        encoded = json.dumps(
            facts,
            separators=(",", ":"),
            sort_keys=True,
        ).encode()
        self.assertTrue(
            runner.score_parent_outcome(
                encoded,
                case=case,
                coordinate=coordinate,
                candidate_commit="a" * 40,
                final_agent_message=encoded.decode(),
            )
        )
        self.assertIsNone(runner._parent_outcome_failure_stage(
            encoded,
            case=case,
            coordinate=coordinate,
            candidate_commit="a" * 40,
            final_agent_message=encoded.decode(),
        ))
        semantic = json.dumps(
            facts,
            ensure_ascii=False,
            indent=2,
            sort_keys=False,
        ).encode()
        self.assertTrue(
            runner.score_parent_outcome(
                semantic,
                case=case,
                coordinate=coordinate,
                candidate_commit="a" * 40,
                final_agent_message=semantic.decode(),
            )
        )
        mutated = {**facts, "summary": "invented"}
        self.assertFalse(
            runner.score_parent_outcome(
                json.dumps(
                    mutated,
                    separators=(",", ":"),
                    sort_keys=True,
                ).encode(),
                case=case,
                coordinate=coordinate,
                candidate_commit="a" * 40,
                final_agent_message=json.dumps(
                    mutated,
                    separators=(",", ":"),
                    sort_keys=True,
                ),
            )
        )
        defaults = {
            "case": case,
            "coordinate": coordinate,
            "candidate_commit": "a" * 40,
            "final_agent_message": encoded.decode(),
        }
        invalid_contract = json.dumps(
            {**facts, "summary": False}, separators=(",", ":"), sort_keys=True
        ).encode()
        cases = (
            (encoded, {"final_agent_message": "different"}, "output_binding"),
            (b"{", {"final_agent_message": "{"}, "parent_json"),
            (b"{}", {"final_agent_message": "{}"}, "parent_schema"),
            (
                invalid_contract,
                {"final_agent_message": invalid_contract.decode()},
                "result_contract",
            ),
            (
                json.dumps(mutated, separators=(",", ":"), sort_keys=True).encode(),
                {
                    "final_agent_message": json.dumps(
                        mutated, separators=(",", ":"), sort_keys=True
                    )
                },
                "quality_score",
            ),
        )
        for value, overrides, expected in cases:
            with self.subTest(expected=expected):
                arguments = {**defaults, **overrides}
                self.assertEqual(
                    expected,
                    runner._parent_outcome_failure_stage(value, **arguments),
                )
                self.assertFalse(runner.score_parent_outcome(value, **arguments))
        surrogate = json.dumps(
            {**facts, "summary": "\ud800"},
            separators=(",", ":"),
            sort_keys=True,
        ).encode()
        self.assertEqual(
            "parent_json",
            runner._parent_outcome_failure_stage(
                surrogate,
                **{**defaults, "final_agent_message": surrogate.decode()},
            ),
        )
        self.assertFalse(runner.score_parent_outcome(
            surrogate,
            **{**defaults, "final_agent_message": surrogate.decode()},
        ))
        with mock.patch.object(
            runner.contract._DEV142,
            "validate_result",
            side_effect=UnicodeError,
        ):
            self.assertEqual(
                "result_contract",
                runner._parent_outcome_failure_stage(encoded, **defaults),
            )
        with mock.patch.object(
            runner.contract._DEV142,
            "score_condensation",
            side_effect=UnicodeError,
        ):
            self.assertEqual(
                "quality_score",
                runner._parent_outcome_failure_stage(encoded, **defaults),
            )
        prompt = runner._task(case)
        self.assertNotIn(case["id"], prompt)
        self.assertNotIn(case["renderedSha256"], prompt)
        self.assertNotIn(case["expected"]["summary"], prompt)

    def test_output_allowlist_is_exact_existing_parent_and_no_resume(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            candidate = Path(directory) / "runtime-v1-benchmark.json"
            with mock.patch.object(runner, "OUTPUT_PATH", candidate):
                self.assertIsNone(runner.validate_output_path(candidate))
                candidate.write_text("occupied", encoding="utf-8")
                with self.assertRaises(runner.BenchmarkFailure):
                    runner.validate_output_path(candidate)
        with self.assertRaises(runner.BenchmarkFailure):
            runner.validate_output_path(ROOT / "other.json")
        if not runner.OUTPUT_PATH.exists():
            self.assertEqual(
                runner.OUTPUT_PATH,
                runner.normalize_output_path(
                    "docs/research/evidence/runtime-v1-benchmark.json"
                ),
            )
            with self.assertRaises(runner.BenchmarkFailure):
                runner.normalize_output_path(
                    "./docs/research/evidence/runtime-v1-benchmark.json"
                )

    def test_evidence_file_rejects_duplicate_keys_and_nonfinite_numbers(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            path = Path(directory) / "evidence.json"
            for encoded in (
                b'{"schemaVersion":1,"schemaVersion":1}',
                b'{"schemaVersion":1e999}',
                b'{"schemaVersion":NaN}',
            ):
                path.write_bytes(encoded)
                with self.subTest(encoded=encoded), self.assertRaisesRegex(
                    runner.BenchmarkFailure,
                    "evidence_shape_invalid",
                ):
                    runner.read_outer_evidence(path)

    def test_validate_evidence_cli_normalizes_paths_and_parse_failures(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            duplicate = Path(directory) / "private-evidence.json"
            duplicate.write_bytes(
                b'{"schemaVersion":1,"schemaVersion":1}'
            )
            for candidate in (
                duplicate,
                Path("/private/dev255-secret-evidence.json"),
            ):
                completed = __import__("subprocess").run(
                    [
                        sys.executable,
                        str(RUNNER_PATH),
                        "--validate-evidence",
                        str(candidate),
                    ],
                    env={
                        **os.environ,
                        "PYTHONDONTWRITEBYTECODE": "1",
                    },
                    stdout=__import__("subprocess").PIPE,
                    stderr=__import__("subprocess").PIPE,
                    check=False,
                )
                self.assertEqual(1, completed.returncode)
                self.assertEqual(b"", completed.stderr)
                self.assertEqual(
                    {
                        "status": "fail",
                        "reasonCodes": ["evidence_shape_invalid"],
                    },
                    json.loads(completed.stdout),
                )
                self.assertNotIn(
                    str(candidate).encode(),
                    completed.stdout,
                )

    def test_runner_has_complete_and_usage_dry_run_paths_without_old_blocker(self):
        source = RUNNER_PATH.read_text(encoding="utf-8")
        self.assertIn('options.through == "usage-dry-run"', source)
        self.assertIn("collect_arms(coordinates, run_arm)", source)
        self.assertIn("consume_runtime_v1_observation", source)
        self.assertIn("invoke_with_otel_counter", source)
        self.assertNotIn("apple_attempt_counter_unobservable", source)
        final_write = source[source.rindex("    write_evidence("):]
        self.assertLess(
            final_write.index('["rev-parse", "HEAD"]'),
            final_write.index('["status", "--porcelain"]'),
        )
        self.assertLess(
            final_write.index('["status", "--porcelain"]'),
            final_write.index("read_outer_evidence(output)"),
        )
        coordinates = runner.fixed_pair_coordinates()
        self.assertEqual(
            [(coordinates[0], "pluginOff")],
            runner.usage_dry_run_plan(coordinates),
        )
        arm = self.arm(coordinates[0], "pluginOff")
        terminal = runner.usage_dry_run_terminal([arm])
        self.assertEqual(
            {
                "status": "usage-dry-run",
                "observedArms": 1,
                "providerRequests": [2],
                "stderrBytes": 0,
            },
            terminal,
        )
        for stderr_bytes in (38, False, 0.0):
            with self.subTest(
                stderr_bytes=stderr_bytes
            ), self.assertRaisesRegex(
                runner.BenchmarkBlocked,
                "provider_usage_schema_or_semantic_drift",
            ):
                runner.usage_dry_run_terminal(
                    [{**arm, "stderrBytes": stderr_bytes}]
                )

    def test_parse_event_stream_requires_one_closed_completed_turn(self):
        events = [
            {"type": "thread.started", "thread_id": "synthetic"},
            {"type": "turn.started"},
            {
                "type": "item.started",
                "item": {
                    "id": "item_0",
                    "type": "command_execution",
                    "command": "swift test",
                    "aggregated_output": "",
                    "exit_code": None,
                    "status": "in_progress",
                },
            },
            {
                "type": "item.completed",
                "item": {
                    "id": "item_0",
                    "type": "command_execution",
                    "command": "swift test",
                    "aggregated_output": "synthetic",
                    "exit_code": 0,
                    "status": "completed",
                },
            },
            {
                "type": "item.completed",
                "item": {
                    "id": "item_1",
                    "type": "reasoning",
                    "text": "derived observed facts",
                },
            },
            {
                "type": "item.completed",
                "item": {
                    "id": "item_2",
                    "type": "agent_message",
                    "text": "{}",
                },
            },
            {"type": "turn.completed", "usage": self.usage()},
        ]
        parsed = runner.parse_event_stream(
            "\n".join(json.dumps(row) for row in events).encode()
        )
        self.assertEqual(parsed.command_executions, 1)
        self.assertEqual(parsed.completed_parent_turns, 1)
        self.assertEqual(parsed.usage.total_parent_tokens, 1000)
        self.assertEqual(parsed.final_agent_message, "{}")
        for mutation in (
            events[:-1],
            events + [events[-1]],
            [*events, {"type": "error"}],
            [events[0], events[1], events[-1]],
            [{**events[0], "extra": True}, *events[1:]],
            [events[0], events[1], *events[3:]],
            [
                *events[:3],
                {
                    **events[3],
                    "item": {**events[3]["item"], "command": "swift build"},
                },
                *events[4:],
            ],
            [events[0], events[1], events[2], events[2], *events[3:]],
            [events[0], events[2], events[1], *events[3:]],
            [
                *events[:4],
                {
                    "type": "item.started",
                    "item": {
                        "id": "item_1",
                        "type": "reasoning",
                        "text": "not completion-only",
                    },
                },
                *events[4:],
            ],
            [
                *events[:4],
                {
                    "type": "item.completed",
                    "item": {
                        "id": "item_1",
                        "type": "reasoning",
                        "text": "",
                    },
                },
                *events[5:],
            ],
        ):
            with self.subTest(mutation=mutation), self.assertRaises(runner.BenchmarkBlocked):
                runner.parse_event_stream(
                    "\n".join(json.dumps(row) for row in mutation).encode()
                )

    def test_command_oracle_binds_exact_rendered_bytes_and_digest(self):
        stream = self.event_stream()
        rendered = b"synthetic"
        digest = __import__("hashlib").sha256(rendered).hexdigest()
        self.assertTrue(
            runner._command_result_matches(
                stream,
                command="swift test",
                exit_status=0,
                rendered=rendered,
                rendered_sha256=digest,
            )
        )
        for mutation in (
            {"rendered": b"synthetic\n", "rendered_sha256": digest},
            {"rendered": rendered, "rendered_sha256": "0" * 64},
        ):
            with self.subTest(mutation=mutation):
                self.assertFalse(
                    runner._command_result_matches(
                        stream,
                        command="swift test",
                        exit_status=0,
                        **mutation,
                    )
                )
        self.assertEqual(
            runner._command_result_failure_stage(
                stream,
                command="other",
                exit_status=0,
                rendered=rendered,
                rendered_sha256=digest,
            ),
            "command_text",
        )
        self.assertEqual(
            runner._command_result_failure_stage(
                stream,
                command="swift test",
                exit_status=0,
                rendered=b"other",
                rendered_sha256=digest,
            ),
            "output_bytes",
        )
        rows = [json.loads(line) for line in stream.decode().splitlines()]
        without_command = b"\n".join(
            json.dumps(row).encode()
            for row in rows
            if not (
                row.get("type") == "item.completed"
                and row.get("item", {}).get("type") == "command_execution"
            )
        )
        wrong_output_type = [dict(row) for row in rows]
        wrong_output_type[3] = {
            **wrong_output_type[3],
            "item": {
                **wrong_output_type[3]["item"],
                "aggregated_output": False,
            },
        }
        cases = (
            (b"\xff", {}, "event_shape"),
            (without_command, {}, "command_count"),
            (stream, {"command": "other"}, "command_text"),
            (stream, {"exit_status": 1}, "exit_status"),
            (
                b"\n".join(
                    json.dumps(row).encode() for row in wrong_output_type
                ),
                {},
                "output_type",
            ),
            (stream, {"rendered": b"other"}, "output_bytes"),
            (stream, {"rendered_sha256": "0" * 64}, "fixture_digest"),
            (stream, {}, None),
        )
        defaults = {
            "command": "swift test",
            "exit_status": 0,
            "rendered": rendered,
            "rendered_sha256": digest,
        }
        for candidate_stream, overrides, expected in cases:
            arguments = {**defaults, **overrides}
            with self.subTest(expected=expected):
                self.assertEqual(
                    runner._command_result_failure_stage(
                        candidate_stream, **arguments
                    ),
                    expected,
                )
                self.assertEqual(
                    runner._command_result_matches(
                        candidate_stream, **arguments
                    ),
                    expected is None,
                )

    def test_command_oracle_missing_output_short_circuits_stream_parser(self):
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(
            runner,
            "_command_result_failure_stage",
            side_effect=AssertionError("parser called"),
        ):
            self.assertEqual(
                runner._command_oracle_stage(
                    Path(directory) / "missing",
                    b"not-json",
                    command="swift test",
                    exit_status=0,
                    rendered=b"synthetic",
                    rendered_sha256="0" * 64,
                ),
                "parent_output_file",
            )

    def test_reported_command_accepts_only_exact_system_shell_wrapper(self):
        command = "swift test"
        for value in (
            command,
            "/bin/bash -c 'swift test'",
            "/bin/bash -lc 'swift test'",
            "/bin/zsh -c 'swift test'",
            "/bin/zsh -lc 'swift test'",
        ):
            self.assertTrue(runner._reported_command_matches(value, command))
        for value in (
            False,
            "bash -lc 'swift test'",
            "/bin/sh -lc 'swift test'",
            "/bin/bash -ilc 'swift test'",
            "/bin/zsh --login -c 'swift test'",
            "/bin/zsh -c 'swift test' extra",
            "/bin/zsh -lc 'swift test; echo extra'",
            "/bin/zsh -lc 'swift test' extra",
            "/bin/zsh -lc 'unterminated",
        ):
            self.assertFalse(runner._reported_command_matches(value, command))

        rows = [
            json.loads(line) for line in self.event_stream().decode().splitlines()
        ]
        rows[3]["item"]["command"] = "/bin/zsh -lc 'swift test'"
        stream = b"\n".join(json.dumps(row).encode() for row in rows)
        rendered = b"synthetic"
        self.assertIsNone(runner._command_result_failure_stage(
            stream,
            command=command,
            exit_status=0,
            rendered=rendered,
            rendered_sha256=__import__("hashlib").sha256(rendered).hexdigest(),
        ))

    def test_isolated_zsh_login_restores_fixture_bin_prefix(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bin_path = root / "bin"
            bin_path.mkdir()
            swift = bin_path / "swift"
            swift.write_text("#!/bin/sh\n", encoding="utf-8")
            swift.chmod(0o700)
            environment = {"PATH": f"{bin_path}:/usr/bin:/bin"}
            baseline = __import__("subprocess").run(
                ["/bin/zsh", "-lc", "command -v swift"],
                env=environment,
                stdout=__import__("subprocess").PIPE,
                stderr=__import__("subprocess").PIPE,
                check=False,
            )
            self.assertEqual(0, baseline.returncode)
            self.assertNotEqual(f"{swift}\n".encode(), baseline.stdout)
            self.assertNotIn("HOME", environment)
            runner.configure_zsh_login_path(root, bin_path, environment)
            completed = __import__("subprocess").run(
                ["/bin/zsh", "-lc", "command -v swift"],
                env=environment,
                stdout=__import__("subprocess").PIPE,
                stderr=__import__("subprocess").PIPE,
                check=False,
            )
            self.assertEqual(0, completed.returncode)
            self.assertEqual(f"{swift}\n".encode(), completed.stdout)
            self.assertEqual(b"", completed.stderr)
            profile_root = root / "zsh-profile"
            self.assertEqual(str(profile_root), environment["ZDOTDIR"])
            self.assertNotIn("HOME", environment)
            self.assertEqual(0o700, stat.S_IMODE(profile_root.stat().st_mode))
            profile = profile_root / ".zprofile"
            self.assertEqual(0o600, stat.S_IMODE(profile.stat().st_mode))
            self.assertEqual(
                f"export PATH={runner.shlex.quote(str(bin_path))}:\"$PATH\"\n",
                profile.read_text(encoding="utf-8"),
            )

    def test_normalized_arm_requires_request_apple_latency_and_role_invariants(self):
        observation = runner.ArmObservation(
            event_stream=self.event_stream(),
            parent_requests=2,
            apple_attempts=0,
            validated_applied=False,
            correctness_passed=True,
            parent_latency_ns=10,
            pre_receipt_hook_latency_ns=0,
            pre_receipt_hook_latency_samples=0,
            apple_latency_ns=0,
            apple_latency_samples=0,
            stderr_bytes=0,
            cleanup_complete=True,
        )
        arm = runner.normalized_arm(
            runner.fixed_pair_coordinates()[0], "pluginOff", observation
        )
        self.assertEqual(arm["parent_requests"], 2)
        self.assertEqual(arm["latency"]["parent"]["denominator"], 1)
        self.assertEqual(
            arm["latency"]["preReceiptHook"]["denominator"], 0
        )
        self.assertIsNone(
            arm["latency"]["preReceiptHook"]["averageNanoseconds"]
        )
        self.assertNotIn("hook", arm["latency"])
        self.assertEqual(arm["stderrBytes"], 0)
        with self.assertRaises(runner.BenchmarkBlocked):
            runner.normalized_arm(
                runner.fixed_pair_coordinates()[0],
                "pluginOff",
                runner.ArmObservation(**{**observation.__dict__, "parent_requests": None}),
            )
        with self.assertRaisesRegex(
            runner.BenchmarkBlocked,
            "arm_invariant_invalid",
        ):
            runner.normalized_arm(
                runner.fixed_pair_coordinates()[0],
                "pluginOff",
                runner.ArmObservation(
                    **{**observation.__dict__, "cleanup_complete": False}
                ),
            )
        for stderr_bytes in (False, 0.0):
            with self.subTest(
                stderr_bytes=stderr_bytes
            ), self.assertRaisesRegex(
                runner.BenchmarkBlocked,
                "arm_invariant_invalid",
            ):
                runner.normalized_arm(
                    runner.fixed_pair_coordinates()[0],
                    "pluginOff",
                    runner.ArmObservation(
                        **{
                            **observation.__dict__,
                            "stderr_bytes": stderr_bytes,
                        }
                    ),
                )

    def test_arm_invariant_diagnostic_preserves_predicate_and_precedence(self):
        observation = runner.ArmObservation(
            event_stream=self.event_stream(),
            parent_requests=2,
            apple_attempts=0,
            validated_applied=False,
            correctness_passed=True,
            parent_latency_ns=10,
            pre_receipt_hook_latency_ns=0,
            pre_receipt_hook_latency_samples=0,
            apple_latency_ns=0,
            apple_latency_samples=0,
            stderr_bytes=0,
            cleanup_complete=True,
        )
        parsed = runner.parse_event_stream(observation.event_stream)
        self.assertIsNone(
            runner._arm_invariant_failure_stage(
                "pluginOff", observation, parsed
            )
        )
        plugin_on = runner.replace(
            observation,
            pre_receipt_hook_latency_samples=1,
        )
        cases = (
            ("invalid", observation, parsed, "role"),
            ("pluginOff", runner.replace(observation, parent_requests=False), parsed, "parent_requests"),
            ("pluginOff", runner.replace(observation, parent_requests=1), parsed, "parent_requests"),
            ("pluginOff", observation, runner.replace(parsed, command_executions=2), "command_executions"),
            ("pluginOff", observation, runner.replace(parsed, completed_parent_turns=2), "parent_turns"),
            ("pluginOff", runner.replace(observation, apple_attempts=False), parsed, "apple_attempts"),
            ("pluginOff", runner.replace(observation, apple_attempts=2), parsed, "apple_attempts"),
            ("pluginOff", runner.replace(observation, apple_attempts=1), parsed, "role_state"),
            ("pluginOn", runner.replace(plugin_on, validated_applied=True), parsed, "role_state"),
            ("pluginOff", runner.replace(observation, correctness_passed=1), parsed, "correctness"),
            ("pluginOff", runner.replace(observation, stderr_bytes=False), parsed, "stderr"),
            ("pluginOff", runner.replace(observation, stderr_bytes=1), parsed, "stderr"),
            ("pluginOff", runner.replace(observation, pre_receipt_hook_latency_samples=False), parsed, "hook_latency_samples"),
            ("pluginOff", runner.replace(observation, pre_receipt_hook_latency_samples=2), parsed, "hook_latency_samples"),
            ("pluginOff", runner.replace(observation, pre_receipt_hook_latency_ns=1), parsed, "hook_role_state"),
            ("pluginOff", runner.replace(observation, pre_receipt_hook_latency_samples=1), parsed, "hook_role_state"),
            ("pluginOn", runner.replace(plugin_on, pre_receipt_hook_latency_samples=0), parsed, "hook_role_state"),
            ("pluginOff", runner.replace(observation, cleanup_complete=False), parsed, "cleanup"),
            (
                "pluginOff",
                runner.replace(
                    observation,
                    parent_requests=1,
                    cleanup_complete=False,
                ),
                parsed,
                "parent_requests",
            ),
        )
        for role, candidate, candidate_parsed, expected in cases:
            with self.subTest(expected=expected):
                self.assertEqual(
                    runner._arm_invariant_failure_stage(
                        role, candidate, candidate_parsed
                    ),
                    expected,
                )
        error = runner.ArmInvariantBlocked("parent_requests")
        self.assertEqual(
            runner.blocked_terminal(error),
            {
                "status": "blocked",
                "reasonCodes": ["arm_invariant_invalid"],
                "invariantStage": "parent_requests",
            },
        )
        with self.assertRaisesRegex(ValueError, "invalid arm invariant stage"):
            runner.ArmInvariantBlocked("raw_value")

    def test_observation_consumer_requires_closed_secure_emitted_union(self):
        value = {
            "schemaVersion": 1,
            "event": "runtime_v1_observation",
            "status": "replacement_emitted",
            "reasonCode": None,
            "appleAttempts": 1,
            "appleValidResults": 1,
            "replacementEmitted": True,
            "replacementSha256": "a" * 64,
            "replacementBytes": 42,
            "preReceiptHookLatencyNanoseconds": 10,
            "appleLatencyNanoseconds": 5,
            "appleLatencySamples": 1,
        }
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            parent = Path(directory) / ".runtime-v1-observation"
            parent.mkdir()
            path = parent / "runtime-v1-observation.json"
            path.write_text(
                json.dumps(value, separators=(",", ":")) + "\n",
                encoding="utf-8",
            )
            path.chmod(0o600)
            self.assertEqual(
                value,
                runner.consume_runtime_v1_observation(path),
            )
        for mutation in (
            {**value, "extra": True},
            {**value, "validatedApplied": True},
            {**value, "appleAttempts": 0},
            {**value, "status": "blocked", "reasonCode": None},
            {**value, "replacementSha256": "not-a-digest"},
            {
                **value,
                "status": "fallback",
                "appleAttempts": 0,
                "appleValidResults": 0,
                "replacementEmitted": False,
                "replacementSha256": None,
                "replacementBytes": None,
                "appleLatencyNanoseconds": 5,
                "appleLatencySamples": 1,
            },
        ):
            with self.subTest(mutation=mutation), self.assertRaises(
                runner.BenchmarkBlocked
            ):
                runner.parse_runtime_v1_observation(
                    (json.dumps(mutation) + "\n").encode()
                )

    def test_applied_is_outer_composite_not_observation_owned(self):
        inputs = {
            "role": "pluginOn",
            "replacement_emitted": True,
            "apple_attempts": 1,
            "parent_requests": 2,
            "completed_parent_turns": 1,
            "command_executions": 1,
            "correctness_passed": True,
            "forwarding_preflight_passed": True,
        }
        self.assertTrue(runner.derive_validated_applied(**inputs))
        for key in (
            "parent_requests",
            "completed_parent_turns",
            "command_executions",
            "correctness_passed",
            "forwarding_preflight_passed",
        ):
            mutation = dict(inputs)
            mutation[key] = False if key.endswith("passed") else 0
            with self.subTest(key=key):
                self.assertFalse(
                    runner.derive_validated_applied(**mutation)
                )

    def test_forwarding_proof_is_bound_to_current_candidate_and_bytes(self):
        identities = self.identities()
        proof = runner.ForwardingProof(
            "pass",
            "a" * 40,
            "0.145.0",
            runner.CODEX_SOURCE_COMMIT,
            identities["productionPluginSha256"],
            "sha256:" + "b" * 64,
            identities["pythonAdapterSha256"],
        )
        self.assertIsNone(
            runner.validate_forwarding_proof(
                proof,
                candidate_commit="a" * 40,
                production_identities=identities,
                approved_hook_hash="sha256:" + "b" * 64,
            )
        )
        with self.assertRaisesRegex(
            runner.BenchmarkBlocked,
            "replacement_forwarding_unproven",
        ):
            runner.validate_forwarding_proof(
                proof,
                candidate_commit="c" * 40,
                production_identities=identities,
                approved_hook_hash="sha256:" + "b" * 64,
            )

    def test_forwarding_blocked_terminal_classifies_every_closed_stage_once(self):
        stages = (
            "preflight_setup",
            "process_execution",
            "provider_teardown",
            "observation_cleanup",
            "process_stderr",
            "process_exit",
            "jsonl",
            "request_count",
            "direct_tool_contract",
            "function_output",
            "command_counter_presence",
            "command_counter_value",
            "original_exclusion",
            "receipt",
            "identity_trust",
        )
        terminals = []
        for stage in stages:
            calls = []

            def execute(**arguments):
                calls.append(arguments)
                arguments["_failure_state"].enter(stage)
                raise runner.BenchmarkBlocked(
                    "raw prompt response /Users/private request body "
                    "stdout stderr JSONL command output observation traceback"
                )

            with self.subTest(stage=stage), mock.patch.object(
                runner,
                "_execute_forwarding_preflight",
                side_effect=execute,
            ), self.assertRaises(runner.ForwardingPreflightBlocked) as caught:
                runner.run_forwarding_preflight(synthetic=True)
            self.assertEqual(1, len(calls))
            terminal = runner.blocked_terminal(caught.exception)
            self.assertEqual(
                {
                    "status": "blocked",
                    "reasonCodes": [
                        "replacement_forwarding_unproven"
                    ],
                    "failureStage": stage,
                },
                terminal,
            )
            terminals.append(terminal)
        encoded = json.dumps(terminals, sort_keys=True)
        for prohibited in (
            "/Users/private",
            "raw prompt",
            "response ",
            "request body",
            "stdout ",
            "JSONL ",
            "command output",
            "observation ",
            "traceback",
        ):
            with self.subTest(prohibited=prohibited):
                self.assertNotIn(prohibited, encoded)

    def test_forwarding_setup_boundary_classifies_root_creation_error(self):
        with mock.patch.object(
            runner,
            "isolated_arm_root",
            side_effect=OSError("private setup detail"),
        ), self.assertRaises(
            runner.ForwardingPreflightBlocked
        ) as caught:
            runner.run_forwarding_preflight(
                codex=mock.Mock(),
                python=mock.Mock(),
                candidate_commit="a" * 40,
                production_identities=self.identities(),
                approved_hook_hash="sha256:" + "b" * 64,
            )
        self.assertEqual("preflight_setup", caught.exception.failure_stage)

    def test_forwarding_process_boundary_classifies_spawn_and_timeout(self):
        for error in (
            OSError("private spawn detail"),
            runner.subprocess.TimeoutExpired("private command", 90),
        ):
            with self.subTest(error=type(error).__name__):
                error, calls = self._forwarding_boundary_failure(
                    run_error=error
                )
                self.assertEqual("process_execution", error.failure_stage)
                self.assertEqual(1, calls)

    def test_forwarding_preflight_excludes_ambient_logging_environment(self):
        def check(arguments):
            environment = arguments["env"]
            self.assertEqual("off", environment["RUST_LOG"])
            self.assertNotIn("DEV255_UNAPPROVED_AMBIENT", environment)
            self.assertEqual("/isolated/codex-home", environment["CODEX_HOME"])
            self.assertEqual("/isolated/bin", environment["PATH"])
            self.assertEqual(sys.executable, environment["RUNTIME_V1_PYTHON"])
            self.assertEqual("1", environment["PYTHONDONTWRITEBYTECODE"])
            self.assertEqual("1", environment["NO_COLOR"])
            self.assertEqual("0", environment["PYTHON_COLORS"])
            self.assertIs(arguments["stdin"], runner.subprocess.DEVNULL)

        with mock.patch.dict(
            runner.os.environ,
            {
                "RUST_LOG": "present-but-unapproved",
                "DEV255_UNAPPROVED_AMBIENT": "must-not-cross",
            },
        ):
            error, calls = self._forwarding_boundary_failure(run_check=check)
        self.assertEqual(1, calls)
        self.assertNotEqual("process_stderr", error.failure_stage)

    def test_benchmark_arm_excludes_ambient_logging_environment(self):
        identities = self.identities()
        candidate_commit = "a" * 40
        approved_hook_hash = "sha256:" + "b" * 64
        proof = runner.ForwardingProof(
            "pass",
            candidate_commit,
            "0.145.0",
            runner.CODEX_SOURCE_COMMIT,
            identities["productionPluginSha256"],
            approved_hook_hash,
            identities["pythonAdapterSha256"],
        )

        def invoke(_codex, *, environment, **_arguments):
            self.assertEqual("off", environment["RUST_LOG"])
            self.assertNotIn("DEV255_UNAPPROVED_AMBIENT", environment)
            self.assertTrue(environment["PATH"].endswith(":/approved/bin"))
            self.assertEqual("1", environment["NO_COLOR"])
            self.assertEqual("0", environment["PYTHON_COLORS"])
            self.assertEqual("1", environment["PYTHONDONTWRITEBYTECODE"])
            self.assertIn("CODEX_HOME", environment)
            raise runner.BenchmarkBlocked("arm_completion_uncertain")

        with mock.patch.dict(
            runner.os.environ,
            {
                "PATH": "/approved/bin",
                "RUST_LOG": "present-but-unapproved",
                "DEV255_UNAPPROVED_AMBIENT": "must-not-cross",
            },
        ), mock.patch.object(
            runner,
            "invoke_with_otel_counter",
            side_effect=invoke,
        ) as invoked, mock.patch.object(
            runner,
            "staged_parent_auth",
            return_value=__import__("contextlib").nullcontext(),
        ), self.assertRaisesRegex(
            runner.BenchmarkBlocked,
            "^arm_completion_uncertain$",
        ):
            runner._execute_benchmark_arm(
                runner.fixed_pair_coordinates()[0],
                "pluginOff",
                codex=mock.Mock(resolved=Path("/host/codex")),
                python=mock.Mock(resolved=Path(sys.executable)),
                approved_hook_hash=approved_hook_hash,
                production_identities=identities,
                candidate_commit=candidate_commit,
                forwarding_proof=proof,
            )
        invoked.assert_called_once()

    def test_forwarding_provider_exit_boundary_is_closed(self):
        error, calls = self._forwarding_boundary_failure(
            provider_exit_error=OSError("private provider detail")
        )
        self.assertEqual("provider_teardown", error.failure_stage)
        self.assertEqual(1, calls)

    def test_forwarding_observation_cleanup_boundaries_are_closed(self):
        for operation in ("unlink", "rmdir"):
            with self.subTest(operation=operation):
                error, calls = self._forwarding_boundary_failure(
                    cleanup_error=operation
                )
                self.assertEqual(
                    "observation_cleanup", error.failure_stage
                )
                self.assertEqual(1, calls)

    def test_forwarding_request_count_is_closed_before_direct_tool_validation(self):
        for request_count in (0, 1, 3):
            helper_calls = []

            def require_direct_requests(_requests):
                helper_calls.append(True)

            with self.subTest(request_count=request_count):
                error, calls = self._forwarding_boundary_failure(
                    request_count=request_count,
                    direct_requests_error=require_direct_requests,
                )
                self.assertEqual("request_count", error.failure_stage)
                self.assertEqual(1, calls)
                self.assertEqual([], helper_calls)

    def test_forwarding_direct_request_boundaries_are_closed(self):
        sensitive = "private prompt response /Users/private traceback"
        cases = (
            (
                "function_output",
                {
                    "direct_requests_error": runner.production.ProbeFailure(
                        "provider_request_invalid"
                    )
                },
            ),
            (
                "direct_tool_contract",
                {
                    "direct_requests_error": runner.production.ProbeFailure(
                        "direct_tool_mode_unavailable"
                    )
                },
            ),
        )
        for stage, arguments in cases:
            with self.subTest(stage=stage):
                error, calls = self._forwarding_boundary_failure(**arguments)
                terminal = runner.blocked_terminal(error)
                self.assertEqual(1, calls)
                self.assertEqual(
                    {
                        "status": "blocked",
                        "reasonCodes": ["replacement_forwarding_unproven"],
                        "failureStage": stage,
                    },
                    terminal,
                )
                self.assertNotIn(sensitive, json.dumps(terminal))

    def test_forwarding_unknown_direct_request_errors_are_unexpected(self):
        sensitive = "private prompt response /Users/private traceback"
        errors = (
            RuntimeError(sensitive),
            runner.production.ProbeFailure("unknown_probe_failure"),
        )
        for error in errors:
            with self.subTest(error=type(error).__name__):
                caught, calls = self._forwarding_boundary_failure(
                    direct_requests_error=error,
                )
                terminal = runner.blocked_terminal(caught)
                self.assertEqual(1, calls)
                self.assertEqual(
                    {
                        "status": "blocked",
                        "reasonCodes": ["replacement_forwarding_unproven"],
                        "failureStage": "unexpected_exception",
                    },
                    terminal,
                )
                self.assertNotIn(sensitive, json.dumps(terminal))

    def test_forwarding_command_counter_boundaries_are_closed(self):
        sensitive = "private prompt response /Users/private traceback"
        cases = (
            (
                "command_counter_presence",
                {"command_counter_value": None},
            ),
            (
                "command_counter_value",
                {"command_counter_value": "0"},
            ),
            (
                "command_counter_value",
                {"command_counter_value": "2"},
            ),
        )
        for stage, arguments in cases:
            with self.subTest(stage=stage, arguments=arguments):
                error, calls = self._forwarding_boundary_failure(**arguments)
                terminal = runner.blocked_terminal(error)
                self.assertEqual(1, calls)
                self.assertEqual(
                    {
                        "status": "blocked",
                        "reasonCodes": ["replacement_forwarding_unproven"],
                        "failureStage": stage,
                    },
                    terminal,
                )
                self.assertNotIn(sensitive, json.dumps(terminal))

    def test_forwarding_unexpected_exception_is_content_free_and_not_retried(self):
        sensitive = (
            "private exception /Users/private prompt response request body "
            "stdout stderr JSONL command output observation traceback"
        )
        for error_type in (RuntimeError, runner.BenchmarkBlocked):
            calls = []

            def execute(**arguments):
                calls.append(arguments)
                raise error_type(sensitive)

            with self.subTest(error_type=error_type), mock.patch.object(
                runner,
                "_execute_forwarding_preflight",
                side_effect=execute,
            ), self.assertRaises(
                runner.ForwardingPreflightBlocked
            ) as caught:
                runner.run_forwarding_preflight(synthetic=True)
            self.assertEqual(1, len(calls))
            terminal = runner.blocked_terminal(caught.exception)
            self.assertEqual(
                {
                    "status": "blocked",
                    "reasonCodes": [
                        "replacement_forwarding_unproven"
                    ],
                    "failureStage": "unexpected_exception",
                },
                terminal,
            )
            self.assertNotIn(
                sensitive,
                json.dumps(terminal, sort_keys=True),
            )
            self.assertIsNone(caught.exception.__cause__)
            self.assertIsNone(caught.exception.__context__)

    def test_forwarding_cleanup_supersedes_stage_with_location_only(self):
        calls = []

        def execute(**arguments):
            calls.append(arguments)
            arguments["_failure_state"].enter("receipt")
            raise runner.CleanupBlocked("forwarding_root")

        with mock.patch.object(
            runner,
            "_execute_forwarding_preflight",
            side_effect=execute,
        ), self.assertRaisesRegex(
            runner.BenchmarkBlocked,
            "^cleanup_incomplete$",
        ) as caught:
            runner.run_forwarding_preflight(synthetic=True)
        self.assertEqual(1, len(calls))
        self.assertEqual(
            {
                "status": "blocked",
                "reasonCodes": ["cleanup_incomplete"],
                "cleanupStage": "forwarding_root",
            },
            runner.blocked_terminal(caught.exception),
        )

    def test_forwarding_pass_has_no_failure_stage(self):
        proof = runner.ForwardingProof(
            "pass",
            "a" * 40,
            "0.145.0",
            runner.CODEX_SOURCE_COMMIT,
            "b" * 64,
            "sha256:" + "c" * 64,
            "d" * 64,
        )
        calls = []

        def execute(**arguments):
            calls.append(arguments)
            return proof

        with mock.patch.object(
            runner,
            "_execute_forwarding_preflight",
            side_effect=execute,
        ):
            observed = runner.run_forwarding_preflight(synthetic=True)
        self.assertIs(proof, observed)
        self.assertEqual(1, len(calls))
        self.assertNotIn("failureStage", runner.asdict(observed))

    def test_forwarding_requires_one_second_request_output_and_original_absence(self):
        replacement = "replacement"
        first = {"input": []}
        second = {
            "input": [{
                "type": "custom_tool_call_output",
                "call_id": "call-runtime-v1",
                "output": [
                    {
                        "type": "input_text",
                        "text": (
                            "Script completed\nWall time 0.2 seconds\n"
                            "Output:\n"
                        ),
                    },
                    {"type": "input_text", "text": replacement},
                ],
            }]
        }
        self.assertEqual(
            replacement.encode(),
            runner._sole_forwarded_custom_tool_output(
                first,
                second,
                original=b"original",
            ),
        )
        mutations = (
            (
                {"input": [second["input"][0]]},
                second,
                b"original",
            ),
            (
                first,
                {"input": [second["input"][0], dict(second["input"][0])]},
                b"original",
            ),
            (
                first,
                {**second, "metadata": "original"},
                b"original",
            ),
            (
                first,
                {
                    **second,
                    "metadata": 'line\n"quoted" café ☃',
                },
                'line\n"quoted" café ☃'.encode("utf-8"),
            ),
        )
        for request_one, request_two, original in mutations:
            with self.subTest(
                request_one=request_one,
                request_two=request_two,
            ), self.assertRaisesRegex(
                runner.BenchmarkBlocked,
                "replacement_forwarding_unproven",
            ):
                runner._sole_forwarded_custom_tool_output(
                    request_one,
                    request_two,
                    original=original,
                )
    def test_forwarding_code_mode_contract_is_closed(self):
        outer_exec = {"type": "custom", "name": "exec"}
        call = {
            "type": "custom_tool_call",
            "call_id": "call-runtime-v1",
            "name": "exec",
            "input": runner._CODE_MODE_INPUT,
        }
        self.assertEqual(
            call,
            next(
                event["item"]
                for event in runner._code_mode_provider_events(1)
                if event["type"] == "response.output_item.done"
            ),
        )
        self.assertEqual(1, runner._CODE_MODE_INPUT.count("tools.exec_command"))
        self.assertIn(
            "catch (error) { text(String(error)); }",
            runner._CODE_MODE_INPUT,
        )
        output = {
            "type": "custom_tool_call_output",
            "call_id": "call-runtime-v1",
            "output": [
                {
                    "type": "input_text",
                    "text": (
                        "Script completed\nWall time 0.2 seconds\nOutput:\n"
                    ),
                },
                {"type": "input_text", "text": "replacement"},
            ],
        }
        requests = [
            {
                "input": [{
                    "type": "additional_tools",
                    "role": "developer",
                    "tools": [
                        outer_exec,
                        {"type": "function", "name": "update_plan"},
                    ],
                }],
            },
            {
                "input": [
                    {
                        "type": "additional_tools",
                        "role": "developer",
                        "tools": [outer_exec],
                    },
                    call,
                    output,
                ],
            },
        ]
        runner._require_code_mode_exec_requests(requests)
        self.assertEqual(
            b"replacement",
            runner._sole_forwarded_custom_tool_output(
                requests[0], requests[1], original=b"original"
            ),
        )

        def extra_nested_call(value):
            value[1]["input"][1]["input"] += " text('extra');"

        def wrong_command(value):
            value[1]["input"][1]["input"] = (
                "const result = await tools.exec_command({cmd:\"wrong\"}); "
                "text(result.output);"
            )

        def direct_function_call(value):
            value[1]["input"].append({
                "type": "function_call",
                "call_id": "direct",
                "name": "exec_command",
                "arguments": "{}",
            })

        def direct_function_output(value):
            value[1]["input"].append({
                "type": "function_call_output",
                "call_id": "direct",
                "output": "unsupported",
            })

        def missing_outer_exec(value):
            value[0]["input"][0]["tools"].pop(0)

        def duplicate_outer_exec(value):
            value[1]["input"][0]["tools"].append(deepcopy(outer_exec))

        def mismatched_output(value):
            value[1]["input"][2]["call_id"] = "mismatch"

        def reversed_call_output(value):
            value[1]["input"][1:] = reversed(value[1]["input"][1:])

        def duplicate_prefix(value):
            value[0]["input"].append(deepcopy(value[0]["input"][0]))

        def missing_prefix(value):
            value[0]["input"].pop(0)

        def wrong_prefix_role(value):
            value[0]["input"][0]["role"] = "user"

        def malformed_embedded_tools(value):
            value[0]["input"][0]["tools"] = "not-a-list"

        def simultaneous_top_level_tools(value):
            value[1]["tools"] = [deepcopy(outer_exec)]

        def explicit_top_level_null(value):
            value[1]["tools"] = None

        def tools_elsewhere(value):
            value[0]["input"].append({
                "type": "message",
                "role": "developer",
                "tools": [],
            })

        def direct_shell_tool(value):
            value[0]["input"][0]["tools"].append({
                "type": "function",
                "name": "shell_command",
            })

        def direct_exec_tool(value):
            value[0]["input"][0]["tools"].append({
                "type": "function",
                "name": "exec_command",
            })

        def extra_prefix_key(value):
            value[0]["input"][0]["id"] = "unsupported"

        def nonleading_prefix(value):
            value[0]["input"].insert(0, {
                "type": "message",
                "role": "developer",
                "content": [],
            })

        mutations = (
            extra_nested_call,
            wrong_command,
            direct_function_call,
            direct_function_output,
            missing_outer_exec,
            duplicate_outer_exec,
            mismatched_output,
            reversed_call_output,
            duplicate_prefix,
            missing_prefix,
            wrong_prefix_role,
            malformed_embedded_tools,
            simultaneous_top_level_tools,
            explicit_top_level_null,
            tools_elsewhere,
            direct_shell_tool,
            direct_exec_tool,
            extra_prefix_key,
            nonleading_prefix,
        )
        for mutate in mutations:
            value = deepcopy(requests)
            mutate(value)
            with self.subTest(mutation=mutate.__name__), self.assertRaises(
                runner.production.ProbeFailure
            ):
                runner._require_code_mode_exec_requests(value)

        output_mutations = {
            "failed": lambda value: value[1]["input"][2]["output"][0].update(
                text="Script failed\nWall time 0.2 seconds\nOutput:\n"
            ),
            "running": lambda value: value[1]["input"][2]["output"][0].update(
                text="Script running\nWall time 0.2 seconds\nOutput:\n"
            ),
            "terminated": lambda value: value[1]["input"][2]["output"][0].update(
                text="Script terminated\nWall time 0.2 seconds\nOutput:\n"
            ),
            "extra": lambda value: value[1]["input"][2]["output"].append(
                {"type": "input_text", "text": "extra"}
            ),
            "image": lambda value: value[1]["input"][2]["output"][1].update(
                type="input_image"
            ),
            "string": lambda value: value[1]["input"][2].update(
                output="replacement"
            ),
            "wall time precision": lambda value: value[1]["input"][2][
                "output"
            ][0].update(
                text="Script completed\nWall time 0.25 seconds\nOutput:\n"
            ),
        }
        for label, mutate in output_mutations.items():
            value = deepcopy(requests)
            mutate(value)
            with self.subTest(output=label), self.assertRaises(
                runner.production.ProbeFailure
            ):
                runner._require_code_mode_exec_requests(value)

        leaked = deepcopy(requests)
        leaked[1]["metadata"] = "original"
        with self.assertRaisesRegex(
            runner.BenchmarkBlocked,
            "replacement_forwarding_unproven",
        ):
            runner._sole_forwarded_custom_tool_output(
                leaked[0], leaked[1], original=b"original"
            )

    def test_matrix_order_cancellation_resume_and_atomic_evidence(self):
        coordinates = runner.fixed_pair_coordinates()
        calls = []

        def run(coordinate, role):
            calls.append((coordinate["fixtureID"], role))
            arm = self.arm(coordinate, role)
            arm.pop("stderrBytes")
            return arm

        arms = runner.collect_arms(coordinates, run)
        self.assertEqual(len(arms), 48)
        self.assertEqual(calls[0], (coordinates[0]["fixtureID"], "pluginOff"))
        self.assertEqual(calls[1], (coordinates[0]["fixtureID"], "pluginOn"))
        for malformed in (
            arms[:-1],
            [*arms[:-1], arms[0]],
        ):
            with self.subTest(length=len(malformed)), self.assertRaisesRegex(
                runner.BenchmarkFailure,
                "arm_matrix_invalid",
            ):
                runner.build_evidence(
                    malformed,
                    candidate_commit="a" * 40,
                    production_identities=self.identities(),
                    host={
                        "codexVersion": "0.145.0",
                        "codexExecutable": "<host-path>",
                    },
                )
        with self.assertRaises(runner.BenchmarkBlocked):
            runner.collect_arms(coordinates, lambda _coordinate, _role: (_ for _ in ()).throw(KeyboardInterrupt()))
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            output = Path(directory) / "evidence.json"
            evidence = runner.build_evidence(
                arms,
                candidate_commit="a" * 40,
                production_identities=self.identities(),
                host={"codexVersion": "0.145.0", "codexExecutable": "<host-path>"},
            )
            malformed_arms = []
            missing_latency = __import__("copy").deepcopy(arms)
            missing_latency[0].pop("latency")
            malformed_arms.append(missing_latency)

            negative_latency = __import__("copy").deepcopy(arms)
            negative_latency[0]["latency"]["parent"][
                "numeratorNanoseconds"
            ] = -1
            malformed_arms.append(negative_latency)

            extra_latency = __import__("copy").deepcopy(arms)
            extra_latency[0]["latency"]["parent"]["extra"] = 0
            malformed_arms.append(extra_latency)

            extra_latency_kind = __import__("copy").deepcopy(arms)
            extra_latency_kind[0]["latency"]["totalHook"] = {
                "numeratorNanoseconds": 0,
                "denominator": 0,
                "averageNanoseconds": None,
            }
            malformed_arms.append(extra_latency_kind)

            wrong_arithmetic = __import__("copy").deepcopy(arms)
            wrong_arithmetic[0]["latency"]["parent"][
                "averageNanoseconds"
            ] += 1
            malformed_arms.append(wrong_arithmetic)

            boolean_latency = __import__("copy").deepcopy(arms)
            boolean_latency[0]["latency"]["parent"][
                "denominator"
            ] = True
            malformed_arms.append(boolean_latency)

            for stderr_value in (False, 39):
                extra_stderr = __import__("copy").deepcopy(arms)
                extra_stderr[0]["stderrBytes"] = stderr_value
                malformed_arms.append(extra_stderr)

            for malformed in malformed_arms:
                with self.subTest(
                    malformed=malformed[0]
                ), self.assertRaises(runner.BenchmarkFailure):
                    runner.build_evidence(
                        malformed,
                        candidate_commit="a" * 40,
                        production_identities=self.identities(),
                        host={
                            "codexVersion": "0.145.0",
                            "codexExecutable": "<host-path>",
                        },
                    )
                forged = {
                    **__import__("copy").deepcopy(evidence),
                    "arms": malformed,
                }
                with self.assertRaises(runner.BenchmarkFailure):
                    runner.validate_outer_evidence(forged)
            with mock.patch.object(runner, "OUTPUT_PATH", output):
                runner.write_evidence(output, evidence)
            self.assertEqual(json.loads(output.read_text())["observedArms"], 48)
            self.assertIsNone(runner.validate_outer_evidence(evidence))
            with mock.patch.object(
                runner,
                "OUTPUT_PATH",
                output,
            ), self.assertRaises(runner.BenchmarkFailure):
                runner.write_evidence(output, evidence)

    def test_identity_validation_and_unsafe_evidence_fail_closed(self):
        identities = self.identities()
        self.assertEqual(runner.current_production_identities(), identities)
        self.assertEqual(runner.validate_production_identities(identities), identities)
        with self.assertRaises(runner.BenchmarkBlocked):
            runner.validate_production_identities({**identities, "swiftSourceSha256": "0"})

    def test_provider_counter_blocker_has_closed_normalized_stages(self):
        for stage in ("process_exit", "telemetry_payload", "telemetry_batch"):
            payload_stage = "record" if stage == "telemetry_payload" else None
            self.assertEqual(
                runner.blocked_terminal(
                    runner.ProviderCounterBlocked(
                        stage,
                        payload_stage=payload_stage,
                    )
                ),
                {
                    "status": "blocked",
                    "reasonCodes": ["provider_request_counter_invalid"],
                    "failureStage": stage,
                    **(
                        {"payloadStage": payload_stage}
                        if payload_stage is not None else {}
                    ),
                },
            )
        with self.assertRaisesRegex(ValueError, "invalid provider counter"):
            runner.ProviderCounterBlocked("raw_detail")
        with self.assertRaisesRegex(ValueError, "invalid provider payload"):
            runner.ProviderCounterBlocked("telemetry_payload")
        self.assertIsNone(
            runner.provider_counter_failure_stage(
                0, counter_invalid=False, counter_batches=1
            )
        )

    def test_correctness_oracle_failure_has_closed_stage(self):
        for stage, oracle_stage in (
            ("command_result", "command_text"),
            ("parent_outcome", "quality_score"),
        ):
            self.assertEqual(
                runner.failed_terminal(runner.CorrectnessOracleFailure(
                    stage, oracle_stage=oracle_stage
                )),
                {
                    "status": "fail",
                    "reasonCodes": ["correctness_oracle_failed"],
                    "failureStage": stage,
                    **(
                        {"oracleStage": oracle_stage}
                        if oracle_stage is not None else {}
                    ),
                },
            )
        with self.assertRaisesRegex(ValueError, "invalid correctness oracle"):
            runner.CorrectnessOracleFailure("raw_detail")
        with self.assertRaisesRegex(ValueError, "invalid correctness oracle substage"):
            runner.CorrectnessOracleFailure("command_result")
        with self.assertRaisesRegex(ValueError, "invalid correctness oracle substage"):
            runner.CorrectnessOracleFailure(
                "command_result", oracle_stage="raw_detail"
            )
        with self.assertRaisesRegex(ValueError, "invalid correctness oracle substage"):
            runner.CorrectnessOracleFailure(
                "parent_outcome", oracle_stage="command_text"
            )
        with self.assertRaisesRegex(ValueError, "invalid correctness oracle substage"):
            runner.CorrectnessOracleFailure("parent_outcome")
        self.assertEqual(
            runner.failed_terminal(runner.BenchmarkFailure("unsafe_evidence")),
            {"status": "fail", "reasonCodes": ["unsafe_evidence"]},
        )
        for cleanup_stage in (
            "parent_auth", "isolated_root", "forwarding_root", "arm_pending",
        ):
            self.assertEqual(
                runner.blocked_terminal(
                    runner.CleanupBlocked(cleanup_stage)
                ),
                {
                    "status": "blocked",
                    "reasonCodes": ["cleanup_incomplete"],
                    "cleanupStage": cleanup_stage,
                },
            )
        with self.assertRaisesRegex(ValueError, "invalid cleanup stage"):
            runner.CleanupBlocked("raw_detail")
        for values, expected in (
            ((False, False, 1), "process_exit"),
            ((0, 0, 1), "telemetry_payload"),
            ((0, False, True), "telemetry_batch"),
        ):
            self.assertEqual(
                runner.provider_counter_failure_stage(
                    values[0],
                    counter_invalid=values[1],
                    counter_batches=values[2],
                ),
                expected,
            )

    def test_staged_parent_auth_is_private_ephemeral_and_deleted(self):
        completed = __import__("subprocess").CompletedProcess(
            [], 0, b"authenticated", b""
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_home = root / "source-home"
            isolated_home = root / "isolated-home"
            source_home.mkdir()
            isolated_home.mkdir()
            source = source_home / ".codex/auth.json"
            source.parent.mkdir()
            source.write_bytes(b"{}")
            source.chmod(0o600)
            codex = mock.Mock(resolved=Path("/approved/codex"))
            environment = {"CODEX_HOME": str(isolated_home)}
            with mock.patch.object(
                runner.Path, "home", return_value=source_home
            ), mock.patch.object(
                runner.subprocess, "run", return_value=completed
            ):
                with runner.staged_parent_auth(codex, environment):
                    staged = isolated_home / "auth.json"
                    self.assertEqual(staged.read_bytes(), b"{}")
                    self.assertEqual(stat.S_IMODE(staged.stat().st_mode), 0o600)
            self.assertFalse((isolated_home / "auth.json").exists())
            self.assertEqual(source.read_bytes(), b"{}")
            self.assertEqual(completed.stdout, b"")
            self.assertEqual(completed.stderr, b"")
            self.assertEqual(codex.recheck.call_count, 2)

    def test_staged_parent_auth_cleans_partial_and_broken_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_home = root / "source-home"
            isolated_home = root / "isolated-home"
            source_home.mkdir()
            isolated_home.mkdir()
            source = source_home / ".codex/auth.json"
            source.parent.mkdir()
            source.write_bytes(b"{}")
            source.chmod(0o600)
            destination = isolated_home / "auth.json"
            codex = mock.Mock(resolved=Path("/approved/codex"))
            environment = {"CODEX_HOME": str(isolated_home)}

            def partial_copy(_reader, writer, **_kwargs):
                writer.write(b"{")
                raise OSError

            with mock.patch.object(
                runner.Path, "home", return_value=source_home
            ), mock.patch.object(
                runner.shutil, "copyfileobj", side_effect=partial_copy
            ), self.assertRaisesRegex(
                runner.BenchmarkBlocked, "parent_auth_unavailable"
            ):
                with runner.staged_parent_auth(codex, environment):
                    self.fail("partial copy cannot yield")
            self.assertFalse(os.path.lexists(destination))
            self.assertEqual(codex.recheck.call_count, 1)

            codex.reset_mock()
            completed = __import__("subprocess").CompletedProcess(
                [], 0, b"authenticated", b""
            )
            with mock.patch.object(
                runner.Path, "home", return_value=source_home
            ), mock.patch.object(
                runner.subprocess, "run", return_value=completed
            ):
                with runner.staged_parent_auth(codex, environment):
                    destination.unlink()
                    destination.symlink_to(root / "missing")
            self.assertFalse(os.path.lexists(destination))
            self.assertEqual(codex.recheck.call_count, 2)

    def test_staged_parent_auth_cleanup_failure_is_classified(self):
        completed = __import__("subprocess").CompletedProcess(
            [], 0, b"authenticated", b""
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_home = root / "source-home"
            isolated_home = root / "isolated-home"
            source_home.mkdir()
            isolated_home.mkdir()
            source = source_home / ".codex/auth.json"
            source.parent.mkdir()
            source.write_bytes(b"{}")
            source.chmod(0o600)
            codex = mock.Mock(resolved=Path("/approved/codex"))
            environment = {"CODEX_HOME": str(isolated_home)}
            with mock.patch.object(
                runner.Path, "home", return_value=source_home
            ), mock.patch.object(
                runner.subprocess, "run", return_value=completed
            ), mock.patch.object(
                runner.Path, "unlink", side_effect=OSError
            ), self.assertRaises(runner.CleanupBlocked) as raised:
                with runner.staged_parent_auth(codex, environment):
                    pass
            self.assertIs(type(raised.exception), runner.CleanupBlocked)
            self.assertEqual(
                runner.blocked_terminal(raised.exception),
                {
                    "status": "blocked",
                    "reasonCodes": ["cleanup_incomplete"],
                    "cleanupStage": "parent_auth",
                },
            )
            (isolated_home / "auth.json").unlink()

    def test_staged_parent_auth_rechecks_host_on_login_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_home = root / "source-home"
            isolated_home = root / "isolated-home"
            source_home.mkdir()
            isolated_home.mkdir()
            source = source_home / ".codex/auth.json"
            source.parent.mkdir()
            source.write_bytes(b"{}")
            source.chmod(0o600)
            codex = mock.Mock(resolved=Path("/approved/codex"))
            environment = {"CODEX_HOME": str(isolated_home)}
            denied = __import__("subprocess").CompletedProcess(
                [], 1, b"", b""
            )
            with mock.patch.object(
                runner.Path, "home", return_value=source_home
            ), mock.patch.object(
                runner.subprocess, "run", return_value=denied
            ), self.assertRaisesRegex(
                runner.BenchmarkBlocked, "parent_auth_unavailable"
            ):
                with runner.staged_parent_auth(codex, environment):
                    self.fail("failed login cannot yield")
            self.assertFalse(os.path.lexists(isolated_home / "auth.json"))
            self.assertEqual(codex.recheck.call_count, 2)

            codex.reset_mock()
            codex.recheck.side_effect = [
                None,
                runner.production.ProbeFailure("host_identity_drift"),
            ]
            with mock.patch.object(
                runner.Path, "home", return_value=source_home
            ), mock.patch.object(
                runner.subprocess,
                "run",
                side_effect=runner.subprocess.TimeoutExpired("login", 30),
            ), self.assertRaises(runner.production.ProbeFailure):
                with runner.staged_parent_auth(codex, environment):
                    self.fail("timeout cannot yield")
            self.assertFalse(os.path.lexists(isolated_home / "auth.json"))
            self.assertEqual(codex.recheck.call_count, 2)
        self.assertGreater(
            runner.unsafe_evidence_findings({"prompt": "secret", "path": "/Users/private"}),
            0,
        )
        self.assertGreater(
            runner.unsafe_evidence_findings({"metric": float("nan")}),
            0,
        )

    def test_role_state_requires_empty_off_and_installed_trusted_on(self):
        identities = self.identities()
        self.assertIsNone(
            runner.validate_role_state(
                "pluginOff",
                installed=False,
                trusted=False,
                production_identities=identities,
            )
        )
        self.assertIsNone(
            runner.validate_role_state(
                "pluginOn",
                installed=True,
                trusted=True,
                production_identities=identities,
            )
        )
        for values in (
            ("pluginOff", True, False),
            ("pluginOff", False, True),
            ("pluginOn", False, True),
            ("pluginOn", True, False),
        ):
            with self.subTest(values=values), self.assertRaises(runner.BenchmarkBlocked):
                runner.validate_role_state(
                    values[0],
                    installed=values[1],
                    trusted=values[2],
                    production_identities=identities,
                )

    def test_otel_collector_counts_only_api_requests_and_retains_no_batch(self):
        batch = {
            "resourceLogs": [{
                "scopeLogs": [{
                    "logRecords": [
                        {
                            **self.log_record("codex.api_request", "/responses"),
                            "eventName": "codex.api_request",
                        },
                        self.log_record("codex.other"),
                        self.log_record("codex.api_request", "/models"),
                        self.log_record("codex.api_request", "/responses"),
                    ]
                }]
            }]
        }
        with runner.otel_request_counter() as counter:
            request = urllib.request.Request(
                counter.endpoint,
                data=json.dumps(batch).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=5) as response:
                self.assertEqual(response.status, 202)
        self.assertEqual(counter.api_requests, 2)
        self.assertEqual(counter.batches, 1)
        self.assertFalse(hasattr(counter, "payloads"))
        self.assertFalse(counter.invalid)
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            runner.configure_otel_counter(home, "http://127.0.0.1:1234/v1/logs")
            config = tomllib.loads((home / "config.toml").read_text())
            self.assertFalse(config["otel"]["log_user_prompt"])
            self.assertEqual(config["otel"]["trace_exporter"], "none")
            self.assertEqual(config["otel"]["metrics_exporter"], "none")
        self.assertTrue(
            runner.invocation_result_is_valid(
                0,
                counter_invalid=False,
                counter_batches=1,
            )
        )
        self.assertFalse(
            runner.invocation_result_is_valid(
                1,
                counter_invalid=False,
                counter_batches=1,
            )
        )
        for stderr in (
            b"",
            b"Reading additional input from stdin...\n",
        ):
            completed = __import__("subprocess").CompletedProcess(
                [], 0, b"", stderr
            )
            self.assertEqual(
                len(stderr),
                runner.discard_classified_codex_stderr(
                    completed,
                    codex_version="0.145.0",
                    source_commit=runner.CODEX_SOURCE_COMMIT,
                    stdin_nonterminal=True,
                ),
            )
            self.assertEqual(b"", completed.stderr)
        for stderr in (
            b"Reading additional input from stdin...",
            b"Reading additional input from stdin...\r\n",
            b" Reading additional input from stdin...\n",
            b"\x1b[31mReading additional input from stdin...\n",
            b"Reading additional input from stdin...\n" * 2,
            b"Reading additional input from stdin...\nextra",
            b"warning\n",
            "not-bytes",
        ):
            completed = __import__("subprocess").CompletedProcess(
                [], 0, b"", stderr
            )
            with self.subTest(stderr=stderr), self.assertRaisesRegex(
                runner.BenchmarkBlocked,
                "codex_stderr_unclassified",
            ):
                runner.discard_classified_codex_stderr(
                    completed,
                    codex_version="0.145.0",
                    source_commit=runner.CODEX_SOURCE_COMMIT,
                    stdin_nonterminal=True,
                )
            self.assertEqual(b"", completed.stderr)
        for version, source, nonterminal in (
            ("0.145.1", runner.CODEX_SOURCE_COMMIT, True),
            ("0.145.0", "different", True),
            ("0.145.0", runner.CODEX_SOURCE_COMMIT, False),
        ):
            completed = __import__("subprocess").CompletedProcess(
                [], 0, b"",
                b"Reading additional input from stdin...\n",
            )
            with self.subTest(
                version=version,
                source=source,
                nonterminal=nonterminal,
            ), self.assertRaisesRegex(
                runner.BenchmarkBlocked,
                "codex_stderr_unclassified",
            ):
                runner.discard_classified_codex_stderr(
                    completed,
                    codex_version=version,
                    source_commit=source,
                    stdin_nonterminal=nonterminal,
                )
            self.assertEqual(b"", completed.stderr)

    def test_otel_rejects_missing_or_duplicate_api_discriminators(self):
        self.assertEqual(
            runner._api_request_count({
                "resourceLogs": [{
                    "scopeLogs": [{
                        "logRecords": [{
                            "eventName": "codex.api_request",
                            "attributes": [],
                        }],
                    }],
                }],
            }),
            0,
        )
        for event_name in ("", "x" * 257, False, 1):
            with self.subTest(eventName=event_name), self.assertRaises(ValueError):
                runner._api_request_count({
                    "resourceLogs": [{
                        "scopeLogs": [{
                            "logRecords": [{
                                "eventName": event_name,
                                "attributes": [],
                            }],
                        }],
                    }],
                })
        for value, stage in (
            ({}, "envelope"),
            ({"resourceLogs": [False]}, "resource"),
            ({"resourceLogs": [{"scopeLogs": [False]}]}, "scope"),
            ({
                "resourceLogs": [{
                    "scopeLogs": [{"logRecords": [False]}],
                }],
            }, "record"),
        ):
            with self.subTest(stage=stage), self.assertRaises(
                runner.OtelPayloadError
            ) as raised:
                runner._api_request_count(value)
            self.assertEqual(raised.exception.stage, stage)
        for attributes in (
            [{
                "key": "event.name",
                "value": {"stringValue": "codex.api_request"},
            }],
            [
                {
                    "key": "event.name",
                    "value": {"stringValue": "codex.api_request"},
                },
                {
                    "key": "endpoint",
                    "value": {"stringValue": "/responses"},
                },
                {
                    "key": "endpoint",
                    "value": {"stringValue": "/responses"},
                },
            ],
        ):
            batch = {
                "resourceLogs": [{
                    "scopeLogs": [{"logRecords": [{"attributes": attributes}]}]
                }]
            }
            with self.subTest(attributes=attributes), self.assertRaises(
                ValueError
            ):
                runner._api_request_count(batch)

    def test_otel_accepts_v1_6_resource_entity_refs(self):
        def batch(entity_refs):
            return {
                "resourceLogs": [{
                    "resource": {
                        "attributes": [{
                            "key": "service.name",
                            "value": {"stringValue": "codex"},
                        }],
                        "entityRefs": entity_refs,
                    },
                    "scopeLogs": [{"logRecords": [self.log_record(
                        "codex.api_request", "/responses"
                    )]}],
                }],
            }

        valid = [{
            "schemaUrl": "https://opentelemetry.io/schemas/1.37.0",
            "type": "service",
            "idKeys": ["service.name"],
            "descriptionKeys": [],
        }]
        self.assertEqual(runner._api_request_count(batch(valid)), 1)
        for malformed in (
            False,
            [False],
            [{"unknown": "value"}],
            [{"schemaUrl": False}],
            [{"type": False}],
            [{"idKeys": False}],
            [{"idKeys": [False]}],
            [{"descriptionKeys": False}],
            [{"descriptionKeys": [False]}],
        ):
            with self.subTest(malformed=malformed), self.assertRaises(
                runner.OtelPayloadError
            ) as raised:
                runner._api_request_count(batch(malformed))
            self.assertEqual(raised.exception.stage, "resource")

    def test_otel_accepts_empty_any_value_without_counting_it(self):
        batch = {
            "resourceLogs": [{
                "resource": {"attributes": [{"key": "empty", "value": {}}]},
                "scopeLogs": [{"logRecords": [self.log_record(
                    "codex.api_request", "/responses"
                )]}],
            }],
        }
        self.assertEqual(runner._api_request_count(batch), 1)

        record = batch["resourceLogs"][0]["scopeLogs"][0]["logRecords"][0]
        record["attributes"][0]["value"] = {}
        with self.assertRaises(runner.OtelPayloadError) as raised:
            runner._api_request_count(batch)
        self.assertEqual(raised.exception.stage, "discriminator")

    def test_otel_accepts_omitted_empty_nested_value_lists(self):
        for value in ({"arrayValue": {}}, {"kvlistValue": {}}):
            batch = {
                "resourceLogs": [{
                    "resource": {"attributes": [{
                        "key": "empty", "value": value,
                    }]},
                    "scopeLogs": [{"logRecords": [self.log_record(
                        "codex.api_request", "/responses"
                    )]}],
                }],
            }
            with self.subTest(value=value):
                self.assertEqual(runner._api_request_count(batch), 1)

        for key in ("arrayValue", "kvlistValue"):
            with self.subTest(key=key), self.assertRaises(
                runner.OtelPayloadError
            ) as raised:
                runner._validate_otlp_any_value({key: {"unknown": []}})
            self.assertEqual(
                raised.exception.stage,
                "value_array" if key == "arrayValue" else "value_kvlist",
            )

    def test_otel_any_value_failures_have_closed_substages(self):
        cases = (
            (False, "value_container"),
            ({"stringValue": "x", "boolValue": True}, "value_container"),
            ({"stringValue": False}, "value_string"),
            ({"boolValue": "false"}, "value_bool"),
            ({"intValue": False}, "value_integer_bytes"),
            ({"doubleValue": False}, "value_double"),
            ({"arrayValue": False}, "value_array"),
            ({"kvlistValue": False}, "value_kvlist"),
            ({"unknown": "value"}, "value_union"),
            ({
                "arrayValue": {"values": [{"stringValue": False}]},
            }, "value_string"),
            ({
                "kvlistValue": {"values": [{
                    "key": "nested", "value": {"boolValue": "false"},
                }]},
            }, "value_bool"),
        )
        for value, stage in cases:
            with self.subTest(stage=stage), self.assertRaises(
                runner.OtelPayloadError
            ) as raised:
                runner._validate_otlp_any_value(value)
            self.assertEqual(raised.exception.stage, stage)

    def test_otel_accepts_null_any_value_only_as_unset(self):
        batch = {
            "resourceLogs": [{
                "resource": {"attributes": [{"key": "unset", "value": None}]},
                "scopeLogs": [{"logRecords": [{
                    **self.log_record("codex.api_request", "/responses"),
                    "body": None,
                }]}],
            }],
        }
        self.assertEqual(runner._api_request_count(batch), 1)

        record = batch["resourceLogs"][0]["scopeLogs"][0]["logRecords"][0]
        for index in (0, 1):
            original = record["attributes"][index]["value"]
            record["attributes"][index]["value"] = None
            with self.subTest(index=index), self.assertRaises(
                runner.OtelPayloadError
            ) as raised:
                runner._api_request_count(batch)
            self.assertEqual(raised.exception.stage, "discriminator")
            record["attributes"][index]["value"] = original

        with self.assertRaises(runner.OtelPayloadError) as raised:
            runner._validate_otlp_any_value({
                "arrayValue": {"values": [None]},
            })
        self.assertEqual(raised.exception.stage, "value_container")

    def test_otel_json_rejects_duplicate_keys(self):
        with runner.otel_request_counter() as counter:
            request = urllib.request.Request(
                counter.endpoint,
                data=b'{"resourceLogs":[],"resourceLogs":[]}',
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with self.assertRaises(urllib.error.HTTPError) as raised:
                urllib.request.urlopen(request, timeout=5)
            raised.exception.close()
        self.assertTrue(counter.invalid)
        self.assertEqual(counter.invalid_stage, "json")

    def test_cleanup_failure_blocks_before_arm_can_be_returned(self):
        root = None
        with mock.patch.object(
            runner.shutil,
            "rmtree",
            side_effect=OSError,
        ), self.assertRaisesRegex(
            runner.BenchmarkBlocked,
            "cleanup_incomplete",
        ) as raised:
            with runner.isolated_arm_root() as candidate:
                root = candidate
        self.assertIs(type(raised.exception), runner.BenchmarkBlocked)
        self.assertEqual(
            runner.blocked_terminal(raised.exception),
            {
                "status": "blocked",
                "reasonCodes": ["cleanup_incomplete"],
            },
        )
        self.assertIsNotNone(root)
        runner.shutil.rmtree(root)
        with mock.patch.object(
            runner.shutil,
            "rmtree",
            side_effect=OSError,
        ), self.assertRaisesRegex(
            runner.CleanupBlocked,
            "cleanup_incomplete",
        ) as raised:
            with runner.isolated_arm_root(
                cleanup_stage="isolated_root"
            ) as candidate:
                classified_root = candidate
        self.assertEqual("isolated_root", raised.exception.cleanup_stage)
        runner.shutil.rmtree(classified_root)
        for side_effect in (OSError, None):
            with mock.patch.object(
                runner.shutil,
                "rmtree",
                side_effect=side_effect,
            ), self.assertRaises(runner.CleanupBlocked) as raised:
                with runner.isolated_arm_root(
                    cleanup_stage="forwarding_root"
                ) as candidate:
                    forwarding_root = candidate
            self.assertEqual(
                runner.blocked_terminal(raised.exception),
                {
                    "status": "blocked",
                    "reasonCodes": ["cleanup_incomplete"],
                    "cleanupStage": "forwarding_root",
                },
            )
            runner.shutil.rmtree(forwarding_root)
        for stage in ("parent_auth", "arm_pending"):
            with self.assertRaisesRegex(
                ValueError, "invalid isolated root cleanup"
            ):
                with runner.isolated_arm_root(cleanup_stage=stage):
                    pass

    def test_missing_pending_arm_has_closed_cleanup_location(self):
        class SuppressingRoot:
            def __enter__(self):
                return Path("/synthetic-root")

            def __exit__(self, error_type, _error, _traceback):
                return error_type is runner.BenchmarkBlocked

        coordinate = runner.fixed_pair_coordinates()[0]
        with mock.patch.object(
            runner, "validate_forwarding_proof"
        ), mock.patch.object(
            runner, "isolated_arm_root", return_value=SuppressingRoot()
        ), mock.patch.object(
            runner,
            "_materialize_workspace",
            side_effect=runner.BenchmarkBlocked("synthetic"),
        ), self.assertRaises(runner.CleanupBlocked) as raised:
            runner._execute_benchmark_arm(
                coordinate,
                "pluginOff",
                codex=mock.Mock(),
                python=mock.Mock(),
                approved_hook_hash="sha256:" + "a" * 64,
                production_identities={},
                candidate_commit="b" * 40,
                forwarding_proof=mock.Mock(),
            )
        self.assertEqual(
            runner.blocked_terminal(raised.exception),
            {
                "status": "blocked",
                "reasonCodes": ["cleanup_incomplete"],
                "cleanupStage": "arm_pending",
            },
        )

    def usage(self):
        return {
            "input_tokens": 900,
            "cached_input_tokens": 300,
            "cache_write_input_tokens": 200,
            "output_tokens": 100,
            "reasoning_output_tokens": 50,
        }

    def event_stream(self):
        rows = [
            {"type": "thread.started", "thread_id": "synthetic"},
            {"type": "turn.started"},
            {
                "type": "item.started",
                "item": {
                    "id": "item_0",
                    "type": "command_execution",
                    "command": "swift test",
                    "aggregated_output": "",
                    "exit_code": None,
                    "status": "in_progress",
                },
            },
            {
                "type": "item.completed",
                "item": {
                    "id": "item_0",
                    "type": "command_execution",
                    "command": "swift test",
                    "aggregated_output": "synthetic",
                    "exit_code": 0,
                    "status": "completed",
                },
            },
            {
                "type": "item.completed",
                "item": {
                    "id": "item_1",
                    "type": "agent_message",
                    "text": "{}",
                },
            },
            {"type": "turn.completed", "usage": self.usage()},
        ]
        return "\n".join(json.dumps(row) for row in rows).encode()

    def arm(self, coordinate, role):
        return runner.normalized_arm(
            coordinate,
            role,
            runner.ArmObservation(
                event_stream=self.event_stream(),
                parent_requests=2,
                apple_attempts=0 if role == "pluginOff" else 1,
                validated_applied=role == "pluginOn",
                correctness_passed=True,
                parent_latency_ns=10,
                pre_receipt_hook_latency_ns=(
                    0 if role == "pluginOff" else 5
                ),
                pre_receipt_hook_latency_samples=(
                    0 if role == "pluginOff" else 1
                ),
                apple_latency_ns=0 if role == "pluginOff" else 3,
                apple_latency_samples=0 if role == "pluginOff" else 1,
                stderr_bytes=0 if role == "pluginOff" else 39,
                cleanup_complete=True,
            ),
        )

    def identities(self):
        return dict(runner._APPROVED_IDENTITIES)

    def log_record(self, event_name, endpoint=None):
        attributes = [{
            "key": "event.name",
            "value": {"stringValue": event_name},
        }]
        if endpoint is not None:
            attributes.append({
                "key": "endpoint",
                "value": {"stringValue": endpoint},
            })
        return {"attributes": attributes}


if __name__ == "__main__":
    unittest.main()
