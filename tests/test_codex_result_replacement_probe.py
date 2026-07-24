from __future__ import annotations

import importlib.util
import hashlib
import json
from pathlib import Path
import shlex
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
PROBE_PATH = (
    ROOT
    / "fixtures"
    / "dev-246"
    / "synthetic-plugin"
    / "hooks"
    / "codex"
    / "probe.py"
)
HARNESS_PATH = ROOT / "tests" / "e2e" / "codex_result_replacement_probe.py"
PLUGIN_PATH = ROOT / "fixtures" / "dev-246" / "synthetic-plugin"
EVIDENCE_PATH = (
    ROOT
    / "docs"
    / "research"
    / "evidence"
    / "dev-246-codex-result-replacement.json"
)


def load_probe():
    if not PROBE_PATH.is_file():
        raise AssertionError(f"probe module is missing: {PROBE_PATH}")
    spec = importlib.util.spec_from_file_location("dev_246_probe", PROBE_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError("probe module could not be loaded")
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


def load_harness():
    if not HARNESS_PATH.is_file():
        raise AssertionError(f"harness module is missing: {HARNESS_PATH}")
    spec = importlib.util.spec_from_file_location("dev_246_harness", HARNESS_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError("harness module could not be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class VerdictSchemaTests(unittest.TestCase):
    def passing_observation(self) -> dict[str, object]:
        return {
            "schemaVersion": 1,
            "issue": "DEV-246",
            "codexVersion": "0.145.0",
            "codexExecutable": "/captured/codex",
            "manualSha256": "1" * 64,
            "pluginSha256": "2" * 64,
            "originalSha256": "3" * 64,
            "compactSha256": "4" * 64,
            "boundarySource": "provider_next_request",
            "originalAbsentFromNextRequest": True,
            "compactPresentInNextRequest": True,
            "additionalParentModelTurns": 0,
            "hookInvocations": 1,
            "trustConfirmed": True,
            "cleanupStatus": "complete",
        }

    def test_verdict_requires_closed_model_boundary_fields(self) -> None:
        probe = load_probe()

        verdict = probe.normalize_verdict(self.passing_observation())

        self.assertEqual(verdict["status"], "pass")
        self.assertEqual(verdict["reason"], "replacement_proven")
        self.assertTrue(verdict["originalAbsentFromNextRequest"])
        self.assertTrue(verdict["compactPresentInNextRequest"])
        self.assertEqual(verdict["additionalParentModelTurns"], 0)
        self.assertEqual(
            list(verdict),
            [
                "schemaVersion",
                "issue",
                "status",
                "reason",
                "codexVersion",
                "codexExecutable",
                "manualSha256",
                "pluginSha256",
                "originalSha256",
                "compactSha256",
                "boundarySource",
                "originalAbsentFromNextRequest",
                "compactPresentInNextRequest",
                "additionalParentModelTurns",
                "hookInvocations",
                "trustConfirmed",
                "cleanupStatus",
            ],
        )

    def test_feedback_only_is_blocked(self) -> None:
        probe = load_probe()
        observation = self.passing_observation()
        observation["boundarySource"] = "hook_stdout"

        verdict = probe.normalize_verdict(observation)

        self.assertEqual(verdict["status"], "blocked")
        self.assertEqual(verdict["reason"], "model_boundary_not_observable")

    def test_unknown_observation_key_fails_closed(self) -> None:
        probe = load_probe()
        observation = self.passing_observation()
        observation["rawResult"] = "forbidden"

        with self.assertRaises(probe.ProbeError):
            probe.normalize_verdict(observation)


class BoundaryClassificationTests(VerdictSchemaTests):
    def assert_verdict(
        self,
        changes: dict[str, object],
        *,
        status: str,
        reason: str,
    ) -> None:
        probe = load_probe()
        observation = self.passing_observation()
        observation.update(changes)

        verdict = probe.normalize_verdict(observation)

        self.assertEqual(status, verdict["status"])
        self.assertEqual(reason, verdict["reason"])

    def test_no_direct_boundary_interface_is_blocked(self) -> None:
        self.assert_verdict(
            {"boundarySource": None},
            status="blocked",
            reason="model_boundary_not_observable",
        )

    def test_direct_boundary_containing_original_is_blocked(self) -> None:
        self.assert_verdict(
            {"originalAbsentFromNextRequest": False},
            status="blocked",
            reason="host_replacement_unavailable",
        )

    def test_direct_boundary_omitting_compact_is_blocked(self) -> None:
        self.assert_verdict(
            {"compactPresentInNextRequest": False},
            status="blocked",
            reason="host_replacement_unavailable",
        )

    def test_feedback_and_transcript_sources_are_not_direct_evidence(self) -> None:
        for source in ("hook_stdout", "system_message", "transcript", "model_response"):
            with self.subTest(source=source):
                self.assert_verdict(
                    {"boundarySource": source},
                    status="blocked",
                    reason="model_boundary_not_observable",
                )

    def test_multiple_hooks_fail_execution_invariant(self) -> None:
        self.assert_verdict(
            {"hookInvocations": 2},
            status="fail",
            reason="execution_invariant_failed",
        )

    def test_added_parent_turn_fails_execution_invariant(self) -> None:
        self.assert_verdict(
            {"additionalParentModelTurns": 1},
            status="fail",
            reason="execution_invariant_failed",
        )


class BoundaryInspectorTests(unittest.TestCase):
    def test_direct_boundary_compares_hashes_without_serializing_content(self) -> None:
        harness = load_harness()
        inspector = getattr(harness, "inspect_model_boundary", None)
        self.assertIsNotNone(inspector, "model-boundary inspector is missing")
        assert inspector is not None
        original = b"DEV246_ORIGINAL_SENTINEL_7f21"
        compact = b"DEV246_COMPACT_SENTINEL_9ac4"

        result = inspector(
            boundary_source="provider_next_request",
            request_items=[compact],
            original_sha256=hashlib.sha256(original).hexdigest(),
            compact_sha256=hashlib.sha256(compact).hexdigest(),
            additional_parent_model_turns=0,
            hook_invocations=1,
        )

        self.assertTrue(result["originalAbsentFromNextRequest"])
        self.assertTrue(result["compactPresentInNextRequest"])
        serialized = json.dumps(result, sort_keys=True)
        self.assertNotIn(original.decode("ascii"), serialized)
        self.assertNotIn(compact.decode("ascii"), serialized)

    def test_direct_boundary_detects_original_hash(self) -> None:
        harness = load_harness()
        inspector = getattr(harness, "inspect_model_boundary", None)
        self.assertIsNotNone(inspector, "model-boundary inspector is missing")
        assert inspector is not None
        original = b"DEV246_ORIGINAL_SENTINEL_7f21"
        compact = b"DEV246_COMPACT_SENTINEL_9ac4"

        result = inspector(
            boundary_source="provider_next_request",
            request_items=[original, compact],
            original_sha256=hashlib.sha256(original).hexdigest(),
            compact_sha256=hashlib.sha256(compact).hexdigest(),
            additional_parent_model_turns=0,
            hook_invocations=1,
        )

        self.assertFalse(result["originalAbsentFromNextRequest"])
        self.assertTrue(result["compactPresentInNextRequest"])

    def test_missing_direct_interface_returns_unobservable_fields(self) -> None:
        harness = load_harness()
        inspector = getattr(harness, "inspect_model_boundary", None)
        self.assertIsNotNone(inspector, "model-boundary inspector is missing")
        assert inspector is not None

        result = inspector(
            boundary_source=None,
            request_items=None,
            original_sha256="1" * 64,
            compact_sha256="2" * 64,
            additional_parent_model_turns=0,
            hook_invocations=1,
        )

        self.assertIsNone(result["boundarySource"])
        self.assertIsNone(result["originalAbsentFromNextRequest"])
        self.assertIsNone(result["compactPresentInNextRequest"])


class HookResponseTests(unittest.TestCase):
    ORIGINAL = "DEV246_ORIGINAL_SENTINEL_7f21"
    COMPACT = "DEV246_COMPACT_SENTINEL_9ac4"

    def valid_payload(self) -> dict[str, object]:
        return {
            "session_id": "synthetic-session",
            "transcript_path": None,
            "cwd": "/synthetic",
            "hook_event_name": "PostToolUse",
            "model": "synthetic-model",
            "turn_id": "synthetic-turn",
            "permission_mode": "dontAsk",
            "tool_name": "Bash",
            "tool_input": {"command": "synthetic-only"},
            "tool_response": self.ORIGINAL,
            "tool_use_id": "synthetic-tool-use",
        }

    def original_digest(self) -> str:
        encoded = json.dumps(
            self.valid_payload()["tool_response"],
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def test_hook_emits_only_candidate_control_and_compact_feedback(self) -> None:
        probe = load_probe()

        response = probe.build_candidate_response(
            self.valid_payload(),
            expected_marker=self.ORIGINAL,
            expected_digest=self.original_digest(),
            compact_sentinel=self.COMPACT,
        )

        self.assertEqual(
            response,
            {
                "continue": True,
                "systemMessage": self.COMPACT,
                "suppressOutput": True,
            },
        )
        self.assertNotIn(self.ORIGINAL, json.dumps(response, sort_keys=True))

    def test_hook_rejects_unknown_top_level_input_key(self) -> None:
        probe = load_probe()
        payload = self.valid_payload()
        payload["future_field"] = "unexpected"

        with self.assertRaises(probe.ProbeError):
            probe.build_candidate_response(
                payload,
                expected_marker=self.ORIGINAL,
                expected_digest=self.original_digest(),
                compact_sentinel=self.COMPACT,
            )

    def test_hook_rejects_digest_mismatch(self) -> None:
        probe = load_probe()

        with self.assertRaises(probe.ProbeError):
            probe.build_candidate_response(
                self.valid_payload(),
                expected_marker=self.ORIGINAL,
                expected_digest="0" * 64,
                compact_sentinel=self.COMPACT,
            )


class ExactHostPreflightTests(unittest.TestCase):
    def make_executable(self, directory: str, version_output: str) -> Path:
        executable = Path(directory) / "codex"
        executable.write_text(
            "#!/bin/sh\nprintf '%s' " + shlex.quote(version_output) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        executable.chmod(0o700)
        return executable

    def make_inputs(self, directory: str) -> tuple[Path, Path]:
        manual = Path(directory) / "codex-manual.md"
        manual.write_text("# Synthetic official manual fixture\n", encoding="utf-8")
        plugin = Path(directory) / "plugin"
        (plugin / ".codex-plugin").mkdir(parents=True)
        (plugin / ".codex-plugin" / "plugin.json").write_text(
            '{"name":"synthetic"}\n',
            encoding="utf-8",
        )
        return manual, plugin

    def test_missing_executable_is_blocked(self) -> None:
        harness = load_harness()
        with tempfile.TemporaryDirectory() as directory:
            manual, plugin = self.make_inputs(directory)
            with self.assertRaisesRegex(
                harness.ProbeBlocked, "missing_binary_or_version_mismatch"
            ):
                harness.capture_preflight(
                    Path(directory) / "missing", manual, plugin
                )

    def test_non_runnable_executable_is_blocked(self) -> None:
        harness = load_harness()
        with tempfile.TemporaryDirectory() as directory:
            executable = self.make_executable(directory, "codex-cli 0.145.0\n")
            executable.chmod(0o600)
            manual, plugin = self.make_inputs(directory)
            with self.assertRaisesRegex(
                harness.ProbeBlocked, "missing_binary_or_version_mismatch"
            ):
                harness.capture_preflight(executable, manual, plugin)

    def test_malformed_or_wrong_versions_are_blocked(self) -> None:
        harness = load_harness()
        rejected = (
            "codex-cli 0.145.0\nextra\n",
            "/private/path/codex-cli 0.145.0\n",
            "codex-cli 0.144.5\n",
            "codex-cli 0.145.0",
        )
        for index, version_output in enumerate(rejected):
            with self.subTest(version_output=version_output):
                with tempfile.TemporaryDirectory() as directory:
                    executable = self.make_executable(directory, version_output)
                    manual, plugin = self.make_inputs(directory)
                    with self.assertRaisesRegex(
                        harness.ProbeBlocked,
                        "missing_binary_or_version_mismatch",
                    ):
                        harness.capture_preflight(executable, manual, plugin)

    def test_missing_manual_is_blocked(self) -> None:
        harness = load_harness()
        with tempfile.TemporaryDirectory() as directory:
            executable = self.make_executable(directory, "codex-cli 0.145.0\n")
            _, plugin = self.make_inputs(directory)
            with self.assertRaisesRegex(
                harness.ProbeBlocked, "official_manual_unavailable"
            ):
                harness.capture_preflight(
                    executable, Path(directory) / "missing-manual", plugin
                )

    def test_capture_hashes_manual_and_plugin_without_raw_paths(self) -> None:
        harness = load_harness()
        with tempfile.TemporaryDirectory() as directory:
            executable = self.make_executable(directory, "codex-cli 0.145.0\n")
            manual, plugin = self.make_inputs(directory)

            capture = harness.capture_preflight(executable, manual, plugin)

            self.assertEqual("0.145.0", capture.codex_version)
            self.assertEqual("<host-path>", capture.normalized_executable)
            self.assertRegex(capture.manual_sha256, r"^[0-9a-f]{64}$")
            self.assertRegex(capture.plugin_sha256, r"^[0-9a-f]{64}$")

    def test_post_capture_executable_drift_fails(self) -> None:
        harness = load_harness()
        with tempfile.TemporaryDirectory() as directory:
            executable = self.make_executable(directory, "codex-cli 0.145.0\n")
            manual, plugin = self.make_inputs(directory)
            capture = harness.capture_preflight(executable, manual, plugin)
            replacement = Path(directory) / "replacement"
            replacement.write_text(
                "#!/bin/sh\nprintf 'codex-cli 0.145.0\\n'\n",
                encoding="utf-8",
                newline="\n",
            )
            replacement.chmod(0o700)
            replacement.replace(executable)

            with self.assertRaisesRegex(
                harness.ProbeFailure, "host_resolution_or_version_drift"
            ):
                capture.recheck()


class IsolatedLifecycleTests(ExactHostPreflightTests):
    def make_fake_host(
        self,
        directory: str,
        log: Path,
        *,
        authenticated: bool = True,
    ) -> Path:
        login_result = (
            "  printf 'Logged in using synthetic auth\\n'\n  exit 0\n"
            if authenticated
            else "  printf 'Not logged in\\n'\n  exit 1\n"
        )
        executable = Path(directory) / "codex"
        executable.write_text(
            "#!/bin/sh\n"
            f"printf '%s|%s\\n' \"$CODEX_HOME\" \"$*\" >> {shlex.quote(str(log))}\n"
            "if [ \"$1\" = \"--version\" ]; then\n"
            "  printf 'codex-cli 0.145.0\\n'\n"
            "  exit 0\n"
            "fi\n"
            "if [ \"$1\" = \"login\" ] && [ \"$2\" = \"status\" ]; then\n"
            + login_result
            + "fi\n"
            "printf '{\"ok\":true}\\n'\n",
            encoding="utf-8",
            newline="\n",
        )
        executable.chmod(0o700)
        return executable

    def test_fake_host_lifecycle_orders_install_trust_and_rechecks(self) -> None:
        harness = load_harness()
        lifecycle_factory = getattr(harness, "isolated_lifecycle", None)
        self.assertIsNotNone(lifecycle_factory, "isolated lifecycle is missing")
        assert lifecycle_factory is not None
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "commands.log"
            executable = self.make_fake_host(directory, log)
            manual, plugin = self.make_inputs(directory)
            capture = harness.capture_preflight(executable, manual, plugin)
            log.write_text("", encoding="utf-8")
            observed_home: Path | None = None

            def trust_hook(environment: dict[str, str]) -> bool:
                home = Path(environment["CODEX_HOME"])
                with log.open("a", encoding="utf-8") as stream:
                    stream.write(f"{home}|trust-hook\n")
                self.assertTrue(home.is_dir())
                return True

            with lifecycle_factory(
                capture, plugin, trust_hook=trust_hook
            ) as lifecycle:
                observed_home = Path(lifecycle.environment["CODEX_HOME"])
                self.assertTrue(observed_home.is_dir())
                self.assertTrue(lifecycle.trust_confirmed)

            assert observed_home is not None
            self.assertFalse(observed_home.exists())
            lines = log.read_text(encoding="utf-8").splitlines()
            commands = [line.split("|", 1)[1] for line in lines]
            marketplace_index = next(
                index
                for index, command in enumerate(commands)
                if command.startswith("plugin marketplace add ")
            )
            plugin_index = next(
                index
                for index, command in enumerate(commands)
                if command.startswith("plugin add ")
            )
            trust_index = commands.index("trust-hook")
            self.assertLess(marketplace_index, plugin_index)
            self.assertLess(plugin_index, trust_index)
            self.assertEqual("--version", commands[0])
            self.assertEqual("--version", commands[-1])

    def test_cleanup_is_unconditional_across_terminal_paths(self) -> None:
        harness = load_harness()
        lifecycle_factory = getattr(harness, "isolated_lifecycle", None)
        self.assertIsNotNone(lifecycle_factory, "isolated lifecycle is missing")
        assert lifecycle_factory is not None
        terminal_cases = (
            (None, None),
            (harness.ProbeBlocked("trust_unavailable"), harness.ProbeBlocked),
            (harness.ProbeFailure("install_failed"), harness.ProbeFailure),
            (
                __import__("subprocess").TimeoutExpired(["codex"], 1),
                __import__("subprocess").TimeoutExpired,
            ),
            (KeyboardInterrupt(), KeyboardInterrupt),
        )
        for terminal, expected in terminal_cases:
            with self.subTest(terminal=type(terminal).__name__):
                with tempfile.TemporaryDirectory() as directory:
                    log = Path(directory) / "commands.log"
                    executable = self.make_fake_host(directory, log)
                    manual, plugin = self.make_inputs(directory)
                    capture = harness.capture_preflight(executable, manual, plugin)
                    observed: list[Path] = []

                    def trust_hook(environment: dict[str, str]) -> bool:
                        observed.append(Path(environment["CODEX_HOME"]))
                        if terminal is not None:
                            raise terminal
                        return True

                    if expected is None:
                        with lifecycle_factory(
                            capture, plugin, trust_hook=trust_hook
                        ):
                            pass
                    else:
                        with self.assertRaises(expected):
                            with lifecycle_factory(
                                capture, plugin, trust_hook=trust_hook
                            ):
                                pass
                    self.assertEqual(1, len(observed))
                    self.assertFalse(observed[0].exists())


class DiscoverySerializationTests(IsolatedLifecycleTests):
    def test_normalized_evidence_binds_clean_plugin(self) -> None:
        harness = load_harness()
        evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
        transient = [
            path
            for path in PLUGIN_PATH.rglob("*")
            if path.name == "__pycache__" or path.suffix == ".pyc"
        ]

        self.assertEqual([], transient)
        self.assertEqual(
            harness._tree_sha256(PLUGIN_PATH),
            evidence["pluginSha256"],
        )
        self.assertEqual(
            harness.OFFICIAL_MANUAL_SHA256,
            evidence["manualSha256"],
        )

    def test_manual_contract_drift_stops_before_auth_and_trust(self) -> None:
        harness = load_harness()
        runner = getattr(harness, "run_discovery", None)
        self.assertIsNotNone(runner, "discovery runner is missing")
        assert runner is not None
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "commands.log"
            executable = self.make_fake_host(
                directory,
                log,
                authenticated=False,
            )
            manual, plugin = self.make_inputs(directory)
            trust_called = False

            def trust_hook(_environment: dict[str, str]) -> bool:
                nonlocal trust_called
                trust_called = True
                return True

            verdict = runner(
                executable,
                manual,
                plugin,
                trust_hook=trust_hook,
                expected_manual_sha256=hashlib.sha256(
                    manual.read_bytes()
                ).hexdigest(),
            )

        self.assertEqual("fail", verdict["status"])
        self.assertEqual("official_manual_contract_drift", verdict["reason"])
        self.assertFalse(trust_called)
        self.assertFalse(verdict["trustConfirmed"])

    def test_authoritative_manual_blocker_stops_before_auth_and_trust(self) -> None:
        harness = load_harness()
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "commands.log"
            executable = self.make_fake_host(
                directory,
                log,
                authenticated=False,
            )
            manual, plugin = self.make_inputs(directory)
            manual.write_bytes(
                b"\n".join(harness.POST_TOOL_USE_UNSUPPORTED_MARKERS) + b"\n"
            )
            trust_called = False

            def trust_hook(_environment: dict[str, str]) -> bool:
                nonlocal trust_called
                trust_called = True
                return True

            verdict = harness.run_discovery(
                executable,
                manual,
                plugin,
                trust_hook=trust_hook,
                expected_manual_sha256=hashlib.sha256(
                    manual.read_bytes()
                ).hexdigest(),
            )
            commands = log.read_text(encoding="utf-8")

        self.assertEqual("blocked", verdict["status"])
        self.assertEqual("host_replacement_unavailable", verdict["reason"])
        self.assertFalse(trust_called)
        self.assertFalse(verdict["trustConfirmed"])
        self.assertNotIn("login status", commands)

    def test_unavailable_explicit_trust_writes_closed_blocker(self) -> None:
        harness = load_harness()
        runner = getattr(harness, "run_discovery", None)
        self.assertIsNotNone(runner, "discovery runner is missing")
        assert runner is not None
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "commands.log"
            executable = self.make_fake_host(directory, log)
            manual, plugin = self.make_inputs(directory)
            manual.write_bytes(
                b"\n".join(harness.POST_TOOL_USE_UNSUPPORTED_MARKERS) + b"\n"
            )

            verdict = runner(
                executable,
                manual,
                plugin,
                trust_hook=lambda _environment: False,
                expected_manual_sha256=hashlib.sha256(
                    manual.read_bytes()
                ).hexdigest(),
            )

        self.assertEqual("blocked", verdict["status"])
        self.assertEqual("host_replacement_unavailable", verdict["reason"])
        self.assertFalse(verdict["trustConfirmed"])
        self.assertEqual("complete", verdict["cleanupStatus"])
        self.assertEqual("<host-path>", verdict["codexExecutable"])
        self.assertEqual(
            [
                "schemaVersion",
                "issue",
                "status",
                "reason",
                "codexVersion",
                "codexExecutable",
                "manualSha256",
                "pluginSha256",
                "originalSha256",
                "compactSha256",
                "boundarySource",
                "originalAbsentFromNextRequest",
                "compactPresentInNextRequest",
                "additionalParentModelTurns",
                "hookInvocations",
                "trustConfirmed",
                "cleanupStatus",
            ],
            list(verdict),
        )
        serialized = json.dumps(verdict, sort_keys=True)
        self.assertNotIn(directory, serialized)
        self.assertNotIn("DEV246_ORIGINAL_SENTINEL", serialized)
        self.assertNotIn("DEV246_COMPACT_SENTINEL", serialized)

    def test_installed_plugin_must_match_captured_hash(self) -> None:
        harness = load_harness()
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "commands.log"
            executable = self.make_fake_host(directory, log)
            manual, plugin = self.make_inputs(directory)
            capture = harness.capture_preflight(executable, manual, plugin)
            (plugin / ".codex-plugin" / "plugin.json").write_text(
                '{"name":"changed-after-capture"}\n',
                encoding="utf-8",
                newline="\n",
            )

            with self.assertRaisesRegex(
                harness.ProbeFailure,
                "synthetic_plugin_drift",
            ):
                with harness.isolated_lifecycle(
                    capture,
                    plugin,
                    trust_hook=lambda _environment: True,
                ):
                    pass

    def test_main_writes_one_normalized_json_document(self) -> None:
        harness = load_harness()
        entrypoint = getattr(harness, "main", None)
        self.assertIsNotNone(entrypoint, "CLI entrypoint is missing")
        assert entrypoint is not None
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "commands.log"
            executable = self.make_fake_host(directory, log)
            manual, plugin = self.make_inputs(directory)
            output = Path(directory) / "evidence.json"

            exit_code = entrypoint(
                [
                    "--codex-executable",
                    str(executable),
                    "--manual",
                    str(manual),
                    "--plugin",
                    str(plugin),
                    "--output",
                    str(output),
                ],
                trust_hook=lambda _environment: False,
            )

            evidence = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(1, exit_code)
        self.assertEqual("fail", evidence["status"])
        self.assertEqual("official_manual_hash_mismatch", evidence["reason"])

    def test_atomic_writer_rejects_symlink_without_touching_target(self) -> None:
        harness = load_harness()
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "target.json"
            target.write_text("owner-data\n", encoding="utf-8")
            output = Path(directory) / "evidence.json"
            output.symlink_to(target)

            with self.assertRaises(OSError):
                harness._atomic_write_json(output, {"status": "blocked"})

            self.assertEqual("owner-data\n", target.read_text(encoding="utf-8"))

    def test_atomic_writer_preserves_existing_file_on_replace_failure(self) -> None:
        harness = load_harness()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "evidence.json"
            output.write_text("prior-evidence\n", encoding="utf-8")

            with mock.patch.object(
                harness.os,
                "replace",
                side_effect=OSError("synthetic replace failure"),
            ):
                with self.assertRaises(OSError):
                    harness._atomic_write_json(output, {"status": "blocked"})

            self.assertEqual(
                "prior-evidence\n",
                output.read_text(encoding="utf-8"),
            )
            self.assertEqual(
                [],
                list(Path(directory).glob(".evidence.json.*.tmp")),
            )


if __name__ == "__main__":
    unittest.main()
