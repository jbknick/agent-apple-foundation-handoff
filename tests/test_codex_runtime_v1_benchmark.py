import importlib.util
import json
import os
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
            if command_counter_value is not None:
                Path(
                    arguments["env"]["DEV254_PROBE_COMMAND_COUNTER"]
                ).write_text(command_counter_value, encoding="utf-8")
            Path(
                arguments["env"]["RUNTIME_V1_BENCHMARK_OBSERVATION_PATH"]
            ).write_text("{}", encoding="utf-8")
            return mock.Mock(returncode=0, stderr=b"", stdout=b"events")

        wrapper = runner._serialized_hook_wrapper(b"forwarded")
        observation = {
            "status": "replacement_emitted",
            "replacementEmitted": True,
            "replacementBytes": len(wrapper),
            "replacementSha256": runner.hashlib.sha256(wrapper).hexdigest(),
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
            return_value=({}, Path("/installed")),
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
        ), mock.patch.object(
            runner,
            "parse_event_stream",
            return_value=parsed,
        ), mock.patch.object(
            runner.production,
            "require_direct_exec_requests",
            side_effect=direct_requests_error,
        ), mock.patch.object(
            runner.production,
            "stimulus_bytes",
            return_value=b"original",
        ), mock.patch.object(
            runner,
            "_sole_forwarded_function_output",
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
        args = runner.build_exec_arguments(
            Path("/tmp/workspace"), Path("/tmp/output"), "approved task"
        )
        self.assertEqual(args[0], "exec")
        self.assertEqual(args.count("exec"), 1)
        self.assertIn("gpt-5.6-sol", args)
        self.assertIn('model_reasoning_effort="medium"', args)
        self.assertEqual(args[-1], "approved task")

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

    def test_forwarding_cleanup_supersedes_stage_without_diagnostic(self):
        calls = []

        def execute(**arguments):
            calls.append(arguments)
            arguments["_failure_state"].enter("receipt")
            raise runner.BenchmarkBlocked("cleanup_incomplete")

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
                "type": "function_call_output",
                "call_id": "call-runtime-v1",
                "output": replacement,
            }]
        }
        self.assertEqual(
            replacement.encode(),
            runner._sole_forwarded_function_output(
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
                runner._sole_forwarded_function_output(
                    request_one,
                    request_two,
                    original=original,
                )
        wrapper = runner._serialized_hook_wrapper(replacement.encode())
        decoded_wrapper = json.loads(wrapper)
        self.assertEqual(
            replacement,
            decoded_wrapper["stopReason"],
        )
        self.assertFalse(decoded_wrapper["continue"])

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
        self.assertEqual(runner.validate_production_identities(identities), identities)
        with self.assertRaises(runner.BenchmarkBlocked):
            runner.validate_production_identities({**identities, "swiftSourceSha256": "0"})
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
                        self.log_record("codex.api_request", "/responses"),
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

    def test_cleanup_failure_blocks_before_arm_can_be_returned(self):
        root = None
        with mock.patch.object(
            runner.shutil,
            "rmtree",
            side_effect=OSError,
        ), self.assertRaisesRegex(
            runner.BenchmarkBlocked,
            "cleanup_incomplete",
        ):
            with runner.isolated_arm_root() as candidate:
                root = candidate
        self.assertIsNotNone(root)
        runner.shutil.rmtree(root)

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
