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
