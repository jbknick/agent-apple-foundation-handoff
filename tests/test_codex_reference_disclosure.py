from __future__ import annotations

import unittest
from typing import Any

from tests.e2e import codex_reference_disclosure as probe


TASK_ID = "synthetic-case"
OWNER = f"{probe.REFERENCE_ROOT_RELATIVE}/apple-api-availability.md"


def command_events(
    command: str,
    *,
    identifier: str,
    cwd: str | None = None,
) -> list[dict[str, Any]]:
    inputs: dict[str, Any] = {"command": command}
    if cwd is not None:
        inputs["cwd"] = cwd
    return [
        {
            "type": "item.started",
            "item": {
                **inputs,
                "aggregated_output": "",
                "exit_code": None,
                "id": identifier,
                "status": "in_progress",
                "type": "command_execution",
            },
        },
        {
            "type": "item.completed",
            "item": {
                **inputs,
                "aggregated_output": "synthetic command output",
                "exit_code": 0,
                "id": identifier,
                "status": "completed",
                "type": "command_execution",
            },
        },
    ]


def tool_events(
    inputs: dict[str, Any],
    *,
    identifier: str = "tool-1",
) -> list[dict[str, Any]]:
    common = {
        "id": identifier,
        "type": "mcp_tool_call",
        **inputs,
    }
    return [
        {
            "type": "item.started",
            "item": {**common, "status": "in_progress"},
        },
        {
            "type": "item.completed",
            "item": {**common, "status": "completed"},
        },
    ]


class ReferenceAccessSequenceTests(unittest.TestCase):
    def test_one_tool_item_cannot_own_discovery_and_content_read(self) -> None:
        events = tool_events(
            {
                "arguments": {
                    "first": {
                        "command": (
                            f"rg --files {probe.REFERENCE_ROOT_RELATIVE}"
                        ),
                        "cwd": str(probe.ROOT),
                    },
                    "second": {
                        "command": f"rg -n needle {OWNER}",
                        "cwd": str(probe.ROOT),
                    },
                }
            }
        )

        with self.assertRaises(probe.ProbeFailure) as raised:
            probe.observed_reference_reads(events, TASK_ID)

        self.assertEqual(
            "bulk_reference_content_read",
            raised.exception.reason,
        )


class ReferenceCommandGrammarTests(unittest.TestCase):
    def test_env_prefixed_repository_search_fails_closed(self) -> None:
        events = command_events(
            "env rg Apple .",
            identifier="hidden-search-1",
            cwd=str(probe.ROOT),
        )

        with self.assertRaises(probe.ProbeFailure) as raised:
            probe.observed_reference_reads(events, TASK_ID)

        self.assertEqual("ambiguous_reference_read", raised.exception.reason)

    def test_reference_cwd_glob_read_fails_closed(self) -> None:
        events = command_events(
            "cat *.md",
            identifier="hidden-read-1",
            cwd=str(probe.REFERENCE_ROOT),
        )

        with self.assertRaises(probe.ProbeFailure) as raised:
            probe.observed_reference_reads(events, TASK_ID)

        self.assertEqual(
            "bulk_reference_content_read",
            raised.exception.reason,
        )

    def test_structured_command_array_fails_closed(self) -> None:
        events = tool_events(
            {
                "arguments": {
                    "payload": {
                        "command": ["rg", "needle", OWNER, "."],
                        "cwd": str(probe.ROOT),
                    }
                }
            }
        )

        with self.assertRaises(probe.ProbeFailure) as raised:
            probe.observed_reference_reads(events, TASK_ID)

        self.assertEqual("invalid_tool_event", raised.exception.reason)


class ReferenceToolPayloadTests(unittest.TestCase):
    def test_command_like_structured_payloads_are_not_inferred_as_reads(self) -> None:
        rejected = {
            "unknown argv list": {"argv": ["cat", OWNER]},
            "structured input list": {"input": ["cat", OWNER]},
            "structured input object": {
                "input": {"command": f"cat {OWNER}"}
            },
            "JSON-string command envelope": {
                "payload": f'{{"command":"cat {OWNER}"}}'
            },
        }

        for surface, arguments in rejected.items():
            with self.subTest(surface=surface):
                with self.assertRaises(probe.ProbeFailure) as raised:
                    probe.mapping_reference_reads(
                        arguments,
                        probe.ROOT,
                        TASK_ID,
                    )

                self.assertEqual(
                    "invalid_tool_event",
                    raised.exception.reason,
                )

    def test_argv_arrays_are_not_inferred_as_targeted_reads(self) -> None:
        compact_argv = f'["cat","{OWNER}"]'
        rejected = {
            "direct arguments": ["cat", OWNER],
            "JSON-encoded arguments": compact_argv,
            "unknown metadata list": {
                "metadata": {"values": ["cat", OWNER]}
            },
            "unknown metadata JSON string": {
                "metadata": {"values": compact_argv}
            },
            "compact input JSON array": {"input": compact_argv},
        }

        for surface, arguments in rejected.items():
            with self.subTest(surface=surface):
                with self.assertRaises(probe.ProbeFailure) as raised:
                    probe.mapping_reference_reads(
                        arguments,
                        probe.ROOT,
                        TASK_ID,
                    )

                self.assertEqual(
                    "invalid_tool_event",
                    raised.exception.reason,
                )

    def test_mixed_reference_scalar_arrays_fail_closed(self) -> None:
        compact_sort = f'["sort","{OWNER}"]'
        rejected = {
            "unknown sort": ["sort", OWNER],
            "unknown strings": ["strings", OWNER],
            "unknown dd": ["dd", OWNER],
            "unknown cp": ["cp", OWNER],
            "unknown fish": ["fish", OWNER],
            "unknown busybox": ["busybox", OWNER],
            "leading flag": ["--stable", OWNER],
            "leading environment assignment": ["MODE=synthetic", OWNER],
            "deep nested": {
                "metadata": {"details": {"values": ["sort", OWNER]}}
            },
            "compact JSON": compact_sort,
            "reversed": [OWNER, "sort"],
        }

        for surface, arguments in rejected.items():
            with self.subTest(surface=surface):
                with self.assertRaises(probe.ProbeFailure) as raised:
                    probe.mapping_reference_reads(
                        arguments,
                        probe.ROOT,
                        TASK_ID,
                    )

                self.assertEqual(
                    "invalid_tool_event",
                    raised.exception.reason,
                )

    def test_nested_split_command_containers_fail_closed(self) -> None:
        compact = f'["sort",{{"path":"{OWNER}"}}]'
        rejected = {
            "non-reference then nested reference": ["sort", [OWNER]],
            "nested reference then non-reference": [[OWNER], "sort"],
            "non-reference then path mapping": ["sort", {"path": OWNER}],
            "compact JSON": compact,
            "deep nested": {
                "a": {"b": ["sort", {"c": [OWNER]}]}
            },
            "executable and args siblings": {
                "executable": "sort",
                "args": [OWNER],
            },
            "executable and argv siblings": {
                "executable": "sort",
                "argv": [OWNER],
            },
        }

        for surface, arguments in rejected.items():
            with self.subTest(surface=surface):
                with self.assertRaises(probe.ProbeFailure) as raised:
                    probe.mapping_reference_reads(
                        arguments,
                        probe.ROOT,
                        TASK_ID,
                    )

                self.assertEqual(
                    "invalid_tool_event",
                    raised.exception.reason,
                )

    def test_ordinary_nested_metadata_and_paths_remain_supported(self) -> None:
        other_owner = (
            f"{probe.REFERENCE_ROOT_RELATIVE}/architecture-and-state.md"
        )
        metadata = probe.mapping_reference_reads(
            {
                "metadata": {
                    "groups": [["synthetic"], {"labels": ["control"]}]
                }
            },
            probe.ROOT,
            TASK_ID,
        )
        paths = probe.mapping_reference_reads(
            {
                "metadata": {
                    "paths": [[OWNER], {"path": other_owner}]
                }
            },
            probe.ROOT,
            TASK_ID,
        )

        self.assertEqual((set(), 0), metadata)
        self.assertEqual(
            ({OWNER.rsplit("/", 1)[-1], "architecture-and-state.md"}, 2),
            paths,
        )

    def test_ordinary_metadata_and_path_lists_remain_supported(self) -> None:
        other_owner = (
            f"{probe.REFERENCE_ROOT_RELATIVE}/architecture-and-state.md"
        )
        metadata = probe.mapping_reference_reads(
            {"metadata": ["synthetic", "control"]},
            probe.ROOT,
            TASK_ID,
        )
        paths = probe.mapping_reference_reads(
            {"paths": [OWNER]},
            probe.ROOT,
            TASK_ID,
        )
        all_reference_paths = probe.mapping_reference_reads(
            [OWNER, other_owner],
            probe.ROOT,
            TASK_ID,
        )
        no_reference_paths = probe.mapping_reference_reads(
            ["sort", "MODE=synthetic", "--stable"],
            probe.ROOT,
            TASK_ID,
        )

        self.assertEqual((set(), 0), metadata)
        self.assertEqual(({OWNER.rsplit("/", 1)[-1]}, 1), paths)
        self.assertEqual(
            ({OWNER.rsplit("/", 1)[-1], "architecture-and-state.md"}, 2),
            all_reference_paths,
        )
        self.assertEqual((set(), 0), no_reference_paths)

    def test_malformed_json_is_normalized(self) -> None:
        arguments = f'{{"path":"{OWNER}"'

        with self.assertRaises(probe.ProbeFailure) as raised:
            probe.mapping_reference_reads(arguments, probe.ROOT, TASK_ID)

        self.assertEqual("invalid_tool_event", raised.exception.reason)

    def test_duplicate_key_json_is_normalized(self) -> None:
        arguments = f'{{"path":"{OWNER}","path":"{OWNER}"}}'

        with self.assertRaises(probe.ProbeFailure) as raised:
            probe.mapping_reference_reads(arguments, probe.ROOT, TASK_ID)

        self.assertEqual("invalid_tool_event", raised.exception.reason)


if __name__ == "__main__":
    unittest.main()
