from __future__ import annotations

import hashlib
import os
from pathlib import Path
import shlex
import tempfile
import unittest
from unittest import mock
from tests.e2e import codex_plugin_load as plugin_probe
from tests.e2e import codex_reference_disclosure as probe


TASK_ID = "synthetic-case"
OWNER_NAME = "apple-api-availability.md"
OWNER = f"{probe.REFERENCE_ROOT_RELATIVE}/apple-api-availability.md"
DISCOVERY = f"rg --files {probe.REFERENCE_ROOT_RELATIVE}"
DISCOVERY_PATHS = tuple(
    f"{probe.REFERENCE_ROOT_RELATIVE}/{name}"
    for name in sorted(probe.REFERENCE_NAMES)
)
DISCOVERY_OUTPUT = "\n".join(DISCOVERY_PATHS) + "\n"
READ_OUTPUT = (probe.REFERENCE_ROOT / OWNER_NAME).read_text(encoding="utf-8")
MESSAGE_TEXT = '{"result":"get_only_interface_verified_sdk_26_5"}'


def command_lifecycle(
    command: str,
    *,
    identifier: str,
    output: str,
    completion_status: str = "completed",
    exit_code: int = 0,
) -> list[dict[str, object]]:
    return [
        {
            "type": "item.started",
            "item": {
                "aggregated_output": "",
                "command": command,
                "exit_code": None,
                "id": identifier,
                "status": "in_progress",
                "type": "command_execution",
            },
        },
        {
            "type": "item.completed",
            "item": {
                "aggregated_output": output,
                "command": command,
                "exit_code": exit_code,
                "id": identifier,
                "status": completion_status,
                "type": "command_execution",
            },
        },
    ]


def agent_message(
    *, identifier: str = "message-1", text: str = MESSAGE_TEXT
) -> dict[str, object]:
    return {
        "type": "item.completed",
        "item": {
            "id": identifier,
            "text": text,
            "type": "agent_message",
        },
    }


def valid_events(
    *,
    discovery_command: str = DISCOVERY,
    read_command: str = f"cat {OWNER}",
    discovery_output: str = DISCOVERY_OUTPUT,
    read_output: str = READ_OUTPUT,
) -> list[dict[str, object]]:
    return [
        *command_lifecycle(
            discovery_command,
            identifier="discovery-1",
            output=discovery_output,
        ),
        *command_lifecycle(
            read_command,
            identifier="read-1",
            output=read_output,
        ),
        agent_message(),
    ]


class ClosedDisclosureParserTests(unittest.TestCase):
    def parse(self, events: list[dict[str, object]]):
        parser = getattr(probe, "parse_disclosure_events", None)
        self.assertIsNotNone(parser, "closed disclosure parser is missing")
        assert parser is not None
        return parser(events, TASK_ID)

    def assert_rejected(self, events: list[dict[str, object]]) -> None:
        with self.assertRaises(probe.ProbeFailure):
            self.parse(events)

    def test_exact_sequence_binds_owner_result_and_hashes(self) -> None:
        parsed = self.parse(valid_events())

        self.assertEqual(OWNER_NAME, parsed.reference_name)
        self.assertEqual(
            "get_only_interface_verified_sdk_26_5",
            parsed.result,
        )
        self.assertEqual(
            hashlib.sha256(READ_OUTPUT.encode("utf-8")).hexdigest(),
            parsed.reference_sha256,
        )
        self.assertEqual(
            hashlib.sha256(MESSAGE_TEXT.encode("utf-8")).hexdigest(),
            parsed.result_sha256,
        )

    def test_bare_and_absolute_supported_shell_wrappers_are_grammar_only(self) -> None:
        wrappers = (
            "sh",
            "bash",
            "zsh",
            "/bin/sh",
            "/bin/bash",
            "/bin/zsh",
            "/configured/toolchain/bash",
        )
        for wrapper in wrappers:
            with self.subTest(wrapper=wrapper):
                discovery = f"{wrapper} -lc {shlex.quote(DISCOVERY)}"
                read = f"{wrapper} -lc {shlex.quote(f'cat {OWNER}')}"
                self.assertEqual(
                    OWNER_NAME,
                    self.parse(
                        valid_events(
                            discovery_command=discovery,
                            read_command=read,
                        )
                    ).reference_name,
                )

    def test_relative_path_and_modified_wrappers_are_rejected(self) -> None:
        wrappers = (
            "./bash",
            "tools/zsh",
            "bash -c",
            "bash -lc 'bash -lc \"%s\"'" % DISCOVERY,
            "env bash -lc",
        )
        for wrapper in wrappers:
            with self.subTest(wrapper=wrapper):
                command = (
                    wrapper
                    if wrapper.startswith("bash -lc '")
                    else f"{wrapper} {shlex.quote(DISCOVERY)}"
                )
                self.assert_rejected(valid_events(discovery_command=command))

    def test_exact_command_grammar_and_path_containment_fail_closed(self) -> None:
        rejected = (
            ("discovery", f"ls {probe.REFERENCE_ROOT_RELATIVE}"),
            ("discovery", f"rg needle {probe.REFERENCE_ROOT_RELATIVE}"),
            ("discovery", DISCOVERY + " && true"),
            ("read", f"cat {OWNER} {OWNER}"),
            ("read", f"cat {probe.REFERENCE_ROOT_RELATIVE}/*.md"),
            ("read", f"cat {probe.REFERENCE_ROOT_RELATIVE}/../CLAUDE.md"),
            ("read", f"cat {probe.ROOT.parent}/references/{OWNER_NAME}"),
            ("read", f"rg needle {OWNER}"),
        )
        for position, command in rejected:
            with self.subTest(position=position, command=command):
                kwargs = {f"{position}_command": command}
                self.assert_rejected(valid_events(**kwargs))  # type: ignore[arg-type]

    def test_discovery_output_must_be_exactly_the_five_canonical_paths(self) -> None:
        invalid = (
            "",
            "\n",
            "\n".join(DISCOVERY_PATHS[:-1]) + "\n",
            DISCOVERY_OUTPUT + f"{DISCOVERY_PATHS[0]}\n",
            DISCOVERY_OUTPUT + "unrelated.md\n",
            DISCOVERY_OUTPUT.replace(DISCOVERY_PATHS[0], Path(DISCOVERY_PATHS[0]).name),
        )
        for output in invalid:
            with self.subTest(output=output):
                self.assert_rejected(valid_events(discovery_output=output))

    def test_discovery_output_may_list_the_exact_paths_in_host_order(self) -> None:
        reverse_output = "\n".join(reversed(DISCOVERY_PATHS)) + "\n"
        self.assertEqual(
            OWNER_NAME,
            self.parse(valid_events(discovery_output=reverse_output)).reference_name,
        )

    def test_read_output_must_equal_nonempty_regular_source_bytes(self) -> None:
        for output in ("", READ_OUTPUT + " ", READ_OUTPUT[:-1]):
            with self.subTest(output_length=len(output)):
                self.assert_rejected(valid_events(read_output=output))

    def test_read_before_discovery_and_reversed_commands_are_rejected(self) -> None:
        events = valid_events()
        reversed_lifecycles = events[2:4] + events[0:2] + events[4:]
        self.assert_rejected(reversed_lifecycles)

    def test_interleaved_lifecycles_are_rejected(self) -> None:
        events = valid_events()
        self.assert_rejected([events[0], events[2], events[1], events[3], events[4]])

    def test_duplicate_or_reused_logical_ids_are_rejected(self) -> None:
        cases = []
        duplicate_commands = valid_events()
        duplicate_commands[2]["item"]["id"] = "discovery-1"  # type: ignore[index]
        duplicate_commands[3]["item"]["id"] = "discovery-1"  # type: ignore[index]
        cases.append(duplicate_commands)
        replayed_message_id = valid_events()
        replayed_message_id[4]["item"]["id"] = "read-1"  # type: ignore[index]
        cases.append(replayed_message_id)
        for events in cases:
            with self.subTest(events=events):
                self.assert_rejected(events)

    def test_unpaired_duplicate_or_updated_command_events_are_rejected(self) -> None:
        missing_completion = valid_events()
        missing_completion.pop(1)
        duplicate_completion = valid_events()
        duplicate_completion.insert(2, duplicate_completion[1])
        updated = valid_events()
        updated[1] = {**updated[1], "type": "item.updated"}
        for events in (missing_completion, duplicate_completion, updated):
            with self.subTest(events=events):
                self.assert_rejected(events)

    def test_failed_command_and_failed_action_events_are_rejected(self) -> None:
        failed_command = valid_events()
        failed_command[3]["item"]["status"] = "failed"  # type: ignore[index]
        failed_command[3]["item"]["exit_code"] = 1  # type: ignore[index]
        failed_action = valid_events()
        failed_action.insert(
            4,
            {
                "type": "item.completed",
                "item": {
                    "id": "action-1",
                    "status": "failed",
                    "type": "mcp_tool_call",
                },
            },
        )
        for events in (failed_command, failed_action):
            with self.subTest(events=events):
                self.assert_rejected(events)

    def test_extra_successful_action_is_rejected(self) -> None:
        events = valid_events()
        events.insert(
            4,
            {
                "type": "item.completed",
                "item": {
                    "id": "action-1",
                    "status": "completed",
                    "type": "web_search",
                },
            },
        )
        self.assert_rejected(events)

    def test_passive_error_and_failed_terminal_events_are_rejected(self) -> None:
        passive_error = valid_events()
        passive_error.insert(
            4,
            {
                "type": "item.completed",
                "item": {
                    "id": "error-1",
                    "message": "synthetic",
                    "type": "error",
                },
            },
        )
        failed_terminal = valid_events() + [
            {"type": "turn.failed", "error": {"message": "synthetic"}}
        ]
        for events in (passive_error, failed_terminal):
            with self.subTest(events=events):
                self.assert_rejected(events)

    def test_one_schema_pinned_top_level_final_message_is_required(self) -> None:
        missing = valid_events()[:-1]
        multiple = valid_events() + [agent_message(identifier="message-2")]
        pre_read = [agent_message(), *valid_events()[:-1]]
        turn_before_thread = [
            {"type": "turn.started"},
            {"thread_id": "thread-1", "type": "thread.started"},
            *valid_events(),
        ]
        wrong_event = valid_events()
        wrong_event[4] = {**wrong_event[4], "type": "item.started"}
        extra_key = valid_events()
        extra_key[4]["item"]["status"] = "completed"  # type: ignore[index]
        no_id = valid_events()
        del no_id[4]["item"]["id"]  # type: ignore[index]
        for events in (
            missing,
            multiple,
            pre_read,
            turn_before_thread,
            wrong_event,
            extra_key,
            no_id,
        ):
            with self.subTest(events=events):
                self.assert_rejected(events)

    def test_nested_and_lookalike_messages_are_rejected(self) -> None:
        nested = valid_events()[:-1] + [
            {
                "type": "item.completed",
                "item": {
                    "id": "reasoning-1",
                    "text": "synthetic",
                    "type": "reasoning",
                    "payload": agent_message(),
                },
            }
        ]
        lookalike = valid_events()[:-1] + [
            {"type": "agent_message", "id": "message-1", "text": MESSAGE_TEXT}
        ]
        for events in (nested, lookalike):
            with self.subTest(events=events):
                self.assert_rejected(events)

    def test_message_must_be_bounded_closed_json(self) -> None:
        invalid = (
            "",
            "{}",
            '{"result":1}',
            '{"result":"get_only_interface_verified_sdk_26_5","extra":true}',
            "```json\n" + MESSAGE_TEXT + "\n```",
            MESSAGE_TEXT + "\nprose",
        )
        for text in invalid:
            with self.subTest(text=text):
                events = valid_events()
                events[-1] = agent_message(text=text)
                self.assert_rejected(events)

    def test_fictional_signature_is_rejected_in_reasoning_or_final_message(self) -> None:
        final = valid_events()
        final[-1] = agent_message(
            text=(
                "func transferBaton(to destination: Profile)\n"
                '{"result":"unsupported_no_verified_first_class_api"}'
            )
        )
        reasoning = valid_events()
        reasoning.insert(
            4,
            {
                "type": "item.completed",
                "item": {
                    "id": "reasoning-1",
                    "text": "public func handoffSession(to: Profile)",
                    "type": "reasoning",
                },
            },
        )
        for events in (final, reasoning):
            with self.subTest(events=events):
                with self.assertRaises(probe.ProbeFailure) as raised:
                    parser = getattr(probe, "parse_disclosure_events", None)
                    self.assertIsNotNone(parser)
                    assert parser is not None
                    parser(events, "fictional-transfer-baton-api")
                self.assertEqual(
                    "invented_fictional_api_signature",
                    raised.exception.reason,
                )

    def test_reasoning_is_schema_pinned_passive_and_cannot_change_order(self) -> None:
        events = valid_events()
        events.insert(
            2,
            {
                "type": "item.completed",
                "item": {
                    "id": "reasoning-1",
                    "text": "selected owner from discovered names",
                    "type": "reasoning",
                },
            },
        )
        self.assertEqual(OWNER_NAME, self.parse(events).reference_name)

        pending_reasoning = valid_events()
        pending_reasoning.insert(
            1,
            {
                "type": "item.completed",
                "item": {
                    "id": "reasoning-1",
                    "text": "interleaved with a pending command",
                    "type": "reasoning",
                },
            },
        )
        self.assert_rejected(pending_reasoning)


class ProbeBoundaryTests(unittest.TestCase):
    def test_jsonl_and_owner_neutral_prompt_are_closed(self) -> None:
        invalid = (b"", b"\xff", b"[]\n", b'{"x":1,"x":2}\n', b'{"x":NaN}\n')
        for payload in invalid:
            with self.subTest(payload=payload), self.assertRaises(probe.ProbeFailure):
                probe.decode_json_lines(payload, TASK_ID)

        case = probe.CASES["sdk-26-5-transcript"]
        prompt = probe.build_prompt("sdk-26-5-transcript", case)
        self.assertIn(f"run exactly `rg --files {probe.REFERENCE_ROOT_RELATIVE}`", prompt)
        self.assertIn("run exactly `cat <one-approved-owner-path>`", prompt)
        self.assertNotIn(case["expectedReferences"][0], prompt)
        self.assertIn("Do not combine", prompt)

    def test_closed_blocker_normalization_rejects_generic_words(self) -> None:
        blockers = (
            b'{"error":{"code":"not_authenticated"}}',
            b'{"error":{"code":"model_unavailable"}}',
            b"429 Too Many Requests",
            b"error sending request for url",
        )
        ordinary = (b"model selected", b"connection ready", b"feature unavailable")
        for payload in blockers:
            with self.subTest(payload=payload):
                self.assertTrue(probe.execution_is_unavailable(payload, b""))
        for payload in ordinary:
            with self.subTest(payload=payload):
                self.assertFalse(probe.execution_is_unavailable(payload, b""))

    def test_run_case_uses_closed_parser_and_normalizes_execution_failures(self) -> None:
        unavailable = mock.Mock(returncode=1, stdout=b"", stderr=b"401 Unauthorized")
        unknown = mock.Mock(returncode=1, stdout=b"", stderr=b"synthetic failure")
        for completed, exception in (
            (unavailable, probe.ProbeBlocked),
            (unknown, probe.ProbeFailure),
        ):
            with self.subTest(returncode=completed.returncode), mock.patch.object(
                probe.subprocess, "run", return_value=completed
            ), self.assertRaises(exception):
                probe.run_case("codex", {}, TASK_ID, probe.CASES["sdk-26-5-transcript"])

        parsed = probe.ParsedDisclosure(
            reference_name=OWNER_NAME,
            reference_sha256="a" * 64,
            result="get_only_interface_verified_sdk_26_5",
            result_sha256="b" * 64,
        )
        completed = mock.Mock(returncode=0, stdout=b"{}\n", stderr=b"")
        with (
            mock.patch.object(probe.subprocess, "run", return_value=completed),
            mock.patch.object(probe, "decode_json_lines", return_value=[{}]),
            mock.patch.object(
                probe, "parse_disclosure_events", return_value=parsed
            ) as parser,
        ):
            probe.run_case("codex", {}, TASK_ID, probe.CASES["sdk-26-5-transcript"])
        parser.assert_called_once_with([{}], TASK_ID)
        for removed in ("observed_reference_reads", "mapping_reference_reads",
                        "parse_bounded_result", "exact_reference_reads"):
            self.assertFalse(hasattr(probe, removed), removed)

    def test_isolated_plugin_checks_source_cache_before_and_after_yield(self) -> None:
        calls: list[str] = []
        with (
            mock.patch.object(
                probe,
                "require_unchanged_host",
                side_effect=lambda *_args: calls.append("host"),
            ),
            mock.patch.object(
                plugin_probe,
                "install_isolated_plugin",
                side_effect=lambda *_args: calls.append("install") or Path("cache"),
            ),
            mock.patch.object(
                plugin_probe,
                "require_source_cache_identity",
                side_effect=lambda *_args: calls.append("identity"),
            ),
        ):
            with probe.prepare_isolated_plugin(
                "codex", Path("codex"), Path("codex"), (1, 2, 3, 4, 5, 6, 7), {"PATH": ""}
            ) as environment:
                self.assertIn("CODEX_HOME", environment)
                self.assertEqual(["host", "install", "host", "identity"], calls)
        self.assertEqual(
            ["host", "install", "host", "identity", "identity", "host"], calls
        )


class HostIdentityTests(unittest.TestCase):
    def test_capture_host_rejects_replacement_during_initial_version_check(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            locator = Path(directory) / "codex"
            replacement = Path(f"{locator}.replacement")
            locator.write_text(
                "#!/bin/sh\n"
                '/bin/mv "$0.replacement" "$0"\n'
                "printf 'codex-cli 0.144.5\\n'\n",
                encoding="utf-8",
                newline="\n",
            )
            locator.chmod(0o700)
            replacement.write_text(
                "#!/bin/sh\nprintf 'codex-cli 0.144.5\\n'\n",
                encoding="utf-8",
                newline="\n",
            )
            replacement.chmod(0o700)

            with (
                mock.patch.dict(os.environ, {"PATH": directory}, clear=True),
                self.assertRaisesRegex(
                    probe.ProbeFailure,
                    "host_resolution_or_version_drift",
                ),
            ):
                probe.capture_host()

    def test_main_normalizes_initial_capture_drift_as_fail(self) -> None:
        emitted: list[dict[str, object]] = []
        with (
            mock.patch.object(
                probe,
                "capture_host",
                side_effect=probe.ProbeFailure("host_resolution_or_version_drift"),
            ),
            mock.patch.object(probe, "emit_result", side_effect=emitted.append),
        ):
            self.assertEqual(1, probe.main())

        self.assertEqual(1, len(emitted))
        self.assertEqual("fail", emitted[0]["status"])
        self.assertEqual(
            "host_resolution_or_version_drift",
            emitted[0]["reason"],
        )

    def test_same_path_same_version_replacement_is_rejected_before_execution(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            locator = Path(directory) / "codex"
            replacement = Path(directory) / "replacement"
            marker = Path(directory) / "executed"
            script = "#!/bin/sh\nprintf 'codex-cli 0.144.5\\n'\n"
            locator.write_text(script, encoding="utf-8", newline="\n")
            locator.chmod(0o700)
            initial_resolution = locator.resolve(strict=True)
            initial_snapshot = plugin_probe.metadata_snapshot(locator.stat())
            replacement.write_text(
                f"#!/bin/sh\ntouch '{marker}'\nprintf 'codex-cli 0.144.5\\n'\n",
                encoding="utf-8",
                newline="\n",
            )
            replacement.chmod(0o700)
            replacement.replace(locator)

            stable_host = getattr(probe, "require_unchanged_host", None)
            self.assertIs(
                plugin_probe.require_stable_host,
                stable_host,
                "disclosure probe does not reuse the PR9 stable-host contract",
            )
            assert stable_host is not None
            with self.assertRaisesRegex(
                plugin_probe.ProbeFailure,
                "host_resolution_or_version_drift",
            ):
                stable_host(
                    str(initial_resolution),
                    locator,
                    initial_resolution,
                    initial_snapshot,
                    {"PATH": os.environ.get("PATH", "")},
                )
            self.assertFalse(marker.exists(), "replaced host was executed")

    def test_same_path_same_version_replacement_during_version_check_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            locator = Path(directory) / "codex"
            replacement = Path(f"{locator}.replacement")
            locator.write_text(
                "#!/bin/sh\n"
                'mv "$0.replacement" "$0"\n'
                "printf 'codex-cli 0.144.5\\n'\n",
                encoding="utf-8",
                newline="\n",
            )
            locator.chmod(0o700)
            replacement.write_text(
                "#!/bin/sh\nprintf 'codex-cli 0.144.5\\n'\n",
                encoding="utf-8",
                newline="\n",
            )
            replacement.chmod(0o700)
            initial_resolution = locator.resolve(strict=True)
            initial_snapshot = plugin_probe.metadata_snapshot(locator.stat())

            stable_host = getattr(probe, "require_unchanged_host", None)
            self.assertIs(
                plugin_probe.require_stable_host,
                stable_host,
                "disclosure probe does not reuse the PR9 stable-host contract",
            )
            assert stable_host is not None
            with self.assertRaisesRegex(
                plugin_probe.ProbeFailure,
                "host_resolution_or_version_drift",
            ):
                stable_host(
                    str(initial_resolution),
                    locator,
                    initial_resolution,
                    initial_snapshot,
                    {"PATH": os.environ.get("PATH", "")},
                )

    def test_every_case_execution_is_bracketed_by_host_checks(self) -> None:
        calls: list[str] = []
        emitted: list[dict[str, object]] = []

        def checked(*_args, **_kwargs) -> None:
            calls.append("check")

        def executed(*_args, **_kwargs) -> dict[str, object]:
            calls.append("case")
            return {
                "expectedReferences": [OWNER_NAME],
                "observedReferences": [OWNER_NAME],
                "referenceSha256": "0" * 64,
                "resultClassification": "synthetic",
                "resultSha256": "0" * 64,
                "taskId": TASK_ID,
                "taskSha256": "0" * 64,
            }

        with (
            mock.patch.object(probe, "CASES", {"one": {}, "two": {}}),
            mock.patch.object(
                probe,
                "capture_host",
                return_value=(
                    "codex",
                    Path("codex"),
                    Path("codex"),
                    (1, 2, 3, 4, 5, 6, 7),
                    {},
                ),
            ),
            mock.patch.object(probe, "prepare_isolated_plugin") as prepared,
            mock.patch.object(probe, "require_unchanged_host", side_effect=checked),
            mock.patch.object(probe, "run_case", side_effect=executed),
            mock.patch.object(probe, "emit_result", side_effect=emitted.append),
        ):
            prepared.return_value.__enter__.return_value = {}
            prepared.return_value.__exit__.return_value = False
            self.assertEqual(0, probe.main())

        self.assertEqual(
            ["check", "case", "check", "check", "case", "check", "check"],
            calls,
        )
        self.assertEqual(1, len(emitted))
        self.assertEqual(2, len(emitted[0]["cases"]))  # type: ignore[arg-type]
        self.assertTrue(
            all(
                isinstance(result, dict)
                for result in emitted[0]["cases"]  # type: ignore[union-attr]
            )
        )


if __name__ == "__main__":
    unittest.main()
