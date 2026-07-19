from __future__ import annotations

import hashlib
import os
from pathlib import Path
import shlex
import tempfile
import unittest
from unittest import mock
from typing import Any

from tests.e2e import codex_plugin_load as plugin_probe
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
    def test_explicit_paths_ownership_remains_supported(self) -> None:
        controls = {
            "direct": {"label": "selected", "paths": [OWNER]},
            "nested passive metadata": {
                "metadata": {"label": "selected", "paths": [OWNER]}
            },
        }
        expected = ({OWNER.rsplit("/", 1)[-1]}, 1)

        for surface, arguments in controls.items():
            with self.subTest(surface=surface):
                try:
                    observed = probe.mapping_reference_reads(
                        arguments,
                        probe.ROOT,
                        TASK_ID,
                    )
                except probe.ProbeFailure as failure:
                    self.fail(
                        f"valid explicit paths record rejected: {failure.reason}"
                    )

                self.assertEqual(expected, observed)

    def test_unowned_split_reference_branches_fail_closed(self) -> None:
        compact = f'{{"program":["sort"],"args":["{OWNER}"]}}'
        rejected = {
            "list siblings": {"program": ["sort"], "args": [OWNER]},
            "split nested mappings": {
                "left": {"program": ["sort"]},
                "right": {"args": [OWNER]},
            },
            "compact JSON": compact,
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

    def test_path_collections_are_data_only_at_mapping_and_observed_boundaries(
        self,
    ) -> None:
        rejected: dict[str, tuple[object, dict[str, Any]]] = {
            "bare top-level owner": (OWNER, {"arguments": OWNER}),
            "bare input owner": ({"input": OWNER}, {"input": OWNER}),
            "top-level command string list": (
                [f"cat {OWNER}"],
                {"arguments": [f"cat {OWNER}"]},
            ),
            "paths duplicate command string": (
                {"paths": [f"cat {OWNER} {OWNER}"]},
                {
                    "arguments": {
                        "paths": [f"cat {OWNER} {OWNER}"]
                    }
                },
            ),
            "paths command mapping": (
                {"paths": {"command": f"cat {OWNER}"}},
                {
                    "arguments": {
                        "paths": {"command": f"cat {OWNER}"}
                    }
                },
            ),
            "paths list-wrapped command mapping": (
                {"paths": [{"command": f"cat {OWNER}"}]},
                {
                    "arguments": {
                        "paths": [{"command": f"cat {OWNER}"}]
                    }
                },
            ),
        }

        for surface, (mapping_payload, observed_inputs) in rejected.items():
            with self.subTest(surface=surface, boundary="mapping"):
                with self.assertRaises(probe.ProbeFailure) as raised:
                    probe.mapping_reference_reads(
                        mapping_payload,
                        probe.ROOT,
                        TASK_ID,
                    )

                self.assertEqual(
                    "invalid_tool_event",
                    raised.exception.reason,
                )

            with self.subTest(surface=surface, boundary="observed"):
                with self.assertRaises(probe.ProbeFailure) as raised:
                    probe.observed_reference_reads(
                        tool_events(observed_inputs),
                        TASK_ID,
                    )

                self.assertEqual(
                    "invalid_tool_event",
                    raised.exception.reason,
                )

    def test_unowned_explicit_path_records_under_command_branches_fail_closed(
        self,
    ) -> None:
        rejected = {
            "program container and args path": {
                "program": ["sort"],
                "args": {"path": OWNER},
            },
            "program container and args paths": {
                "program": ["sort"],
                "args": {"paths": [OWNER]},
            },
            "split nested mappings with path": {
                "left": {"program": ["sort"]},
                "right": {"args": {"path": OWNER}},
            },
            "split nested mappings with paths": {
                "left": {"program": ["sort"]},
                "right": {"args": {"paths": [OWNER]}},
            },
            "serialized args path": (
                f'{{"program":["sort"],"args":{{"path":"{OWNER}"}}}}'
            ),
            "serialized args paths": (
                f'{{"program":["sort"],"args":{{"paths":["{OWNER}"]}}}}'
            ),
        }

        for surface, arguments in rejected.items():
            with self.subTest(surface=surface, boundary="mapping"):
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

            with self.subTest(surface=surface, boundary="observed"):
                with self.assertRaises(probe.ProbeFailure) as raised:
                    probe.observed_reference_reads(
                        tool_events({"arguments": arguments}),
                        TASK_ID,
                    )

                self.assertEqual(
                    "invalid_tool_event",
                    raised.exception.reason,
                )

    def test_ambiguous_structural_siblings_fail_closed_at_both_boundaries(
        self,
    ) -> None:
        rejected = {
            # Independently observed scalar and serialized program gaps.
            "program scalar with args path": {
                "program": "sort",
                "args": {"path": OWNER},
            },
            "program scalar with args paths": {
                "program": "sort",
                "args": {"paths": [OWNER]},
            },
            "program scalar split with args path": {
                "left": {"program": "sort"},
                "right": {"args": {"path": OWNER}},
            },
            "program serialized value with args path": {
                "program": '["sort"]',
                "args": {"path": OWNER},
            },
            "program serialized envelope with args path": (
                f'{{"program":"sort","args":{{"path":"{OWNER}"}}}}'
            ),
            # List and mapping values keep the matrix independent of shape.
            "program list with args path": {
                "program": ["sort"],
                "args": {"path": OWNER},
            },
            "program mapping with args paths": {
                "program": {"name": "sort"},
                "args": {"paths": [OWNER]},
            },
            "executable scalar with args path": {
                "executable": "sort",
                "args": {"path": OWNER},
            },
            "executable list with args paths": {
                "executable": ["sort"],
                "args": {"paths": [OWNER]},
            },
            "executable mapping with args path": {
                "executable": {"name": "sort"},
                "args": {"path": OWNER},
            },
            "executable split with args paths": {
                "left": {"executable": "sort"},
                "right": {"args": {"paths": [OWNER]}},
            },
            "executable serialized with args path": (
                f'{{"executable":"sort","args":{{"path":"{OWNER}"}}}}'
            ),
            "binary scalar with args paths": {
                "binary": "sort",
                "args": {"paths": [OWNER]},
            },
            "binary list with args path": {
                "binary": ["sort"],
                "args": {"path": OWNER},
            },
            "binary mapping with args paths": {
                "binary": {"name": "sort"},
                "args": {"paths": [OWNER]},
            },
            "binary split with args path": {
                "left": {"binary": "sort"},
                "right": {"args": {"path": OWNER}},
            },
            "binary serialized with args paths": (
                f'{{"binary":"sort","args":{{"paths":["{OWNER}"]}}}}'
            ),
            "arbitrary scalar aliases with path": {
                "alpha": "sort",
                "omega": {"path": OWNER},
            },
            "arbitrary list aliases with paths": {
                "alpha": ["sort"],
                "omega": {"paths": [OWNER]},
            },
            "arbitrary mapping aliases with path": {
                "alpha": {"name": "sort"},
                "omega": {"path": OWNER},
            },
            "arbitrary split aliases with paths": {
                "left": {"alpha": "sort"},
                "right": {"omega": {"paths": [OWNER]}},
            },
            "arbitrary serialized aliases with path": (
                f'{{"alpha":"sort","omega":{{"path":"{OWNER}"}}}}'
            ),
        }

        for surface, arguments in rejected.items():
            with self.subTest(surface=surface, boundary="mapping"):
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

            with self.subTest(surface=surface, boundary="observed"):
                with self.assertRaises(probe.ProbeFailure) as raised:
                    probe.observed_reference_reads(
                        tool_events({"arguments": arguments}),
                        TASK_ID,
                    )

                self.assertEqual(
                    "invalid_tool_event",
                    raised.exception.reason,
                )

    def test_structural_sibling_positive_controls_remain_supported(
        self,
    ) -> None:
        expected_owner = ({OWNER.rsplit("/", 1)[-1]}, 1)
        controls = {
            "direct path record with passive metadata": (
                {
                    "path": OWNER,
                    "label": "primary",
                    "line": 12,
                    "kind": "reference",
                },
                expected_owner,
                True,
            ),
            "direct label and paths": (
                {"label": "selected", "paths": [OWNER]},
                expected_owner,
                True,
            ),
            "single passive wrapper around direct owner": (
                {"metadata": {"path": OWNER, "label": "wrapped"}},
                expected_owner,
                True,
            ),
            "top-level data-only reference list": (
                [OWNER],
                expected_owner,
                False,
            ),
            "mapping with no reference-bearing children": (
                {"program": "sort", "args": {"label": "synthetic"}},
                (set(), 0),
                True,
            ),
        }

        for surface, (
            arguments,
            expected_mapping,
            has_observed_form,
        ) in controls.items():
            with self.subTest(surface=surface, boundary="mapping"):
                self.assertEqual(
                    expected_mapping,
                    probe.mapping_reference_reads(
                        arguments,
                        probe.ROOT,
                        TASK_ID,
                    ),
                )

            if not has_observed_form:
                continue
            with self.subTest(surface=surface, boundary="observed"):
                self.assertEqual(
                    expected_mapping[0],
                    probe.observed_reference_reads(
                        tool_events({"arguments": arguments}),
                        TASK_ID,
                    ),
                )

    def test_duplicate_path_data_preserves_occurrence_count_and_is_bulk(
        self,
    ) -> None:
        duplicates = {
            "clean path strings": {"paths": [OWNER, OWNER]},
            "explicit path records": {
                "paths": [
                    {"path": OWNER, "label": "first"},
                    {"path": OWNER, "label": "second"},
                ]
            },
        }
        expected = ({OWNER.rsplit("/", 1)[-1]}, 2)

        for surface, arguments in duplicates.items():
            with self.subTest(surface=surface, boundary="mapping"):
                self.assertEqual(
                    expected,
                    probe.mapping_reference_reads(
                        arguments,
                        probe.ROOT,
                        TASK_ID,
                    ),
                )

            with self.subTest(surface=surface, boundary="observed"):
                with self.assertRaises(probe.ProbeFailure) as raised:
                    probe.observed_reference_reads(
                        tool_events({"arguments": arguments}),
                        TASK_ID,
                    )

                self.assertEqual(
                    "bulk_reference_content_read",
                    raised.exception.reason,
                )

    def test_duplicate_command_operands_preserve_count_and_are_bulk(
        self,
    ) -> None:
        duplicate = f"cat {OWNER} {OWNER}"
        commands = {
            "direct command": {"command": duplicate},
            "syntactic input command": {"input": duplicate},
        }
        expected = ({OWNER.rsplit("/", 1)[-1]}, 2)

        for surface, arguments in commands.items():
            with self.subTest(surface=surface, boundary="mapping"):
                self.assertEqual(
                    expected,
                    probe.mapping_reference_reads(
                        arguments,
                        probe.ROOT,
                        TASK_ID,
                    ),
                )

            with self.subTest(surface=surface, boundary="observed"):
                with self.assertRaises(probe.ProbeFailure) as raised:
                    probe.observed_reference_reads(
                        tool_events(arguments),
                        TASK_ID,
                    )

                self.assertEqual(
                    "bulk_reference_content_read",
                    raised.exception.reason,
                )

    def test_single_owner_command_inputs_remain_supported(self) -> None:
        command = f"cat {OWNER}"
        controls = {
            "direct command": {"command": command},
            "syntactic input command": {"input": command},
        }
        expected_mapping = ({OWNER.rsplit("/", 1)[-1]}, 1)
        expected_observed = {OWNER.rsplit("/", 1)[-1]}

        for surface, arguments in controls.items():
            with self.subTest(surface=surface, boundary="mapping"):
                self.assertEqual(
                    expected_mapping,
                    probe.mapping_reference_reads(
                        arguments,
                        probe.ROOT,
                        TASK_ID,
                    ),
                )

            with self.subTest(surface=surface, boundary="observed"):
                self.assertEqual(
                    expected_observed,
                    probe.observed_reference_reads(
                        tool_events(arguments),
                        TASK_ID,
                    ),
                )

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

    def test_direct_path_records_with_metadata_remain_supported(self) -> None:
        other_owner = (
            f"{probe.REFERENCE_ROOT_RELATIVE}/architecture-and-state.md"
        )
        records = {
            "path": {
                "path": OWNER,
                "label": "primary",
                "line": 12,
                "kind": "reference",
                "score": 0.9,
            },
            "file_path": {
                "file_path": other_owner,
                "label": "secondary",
                "line": 24,
                "kind": "reference",
                "score": 0.8,
            },
        }
        expected = {
            "path": ({OWNER.rsplit("/", 1)[-1]}, 1),
            "file_path": ({"architecture-and-state.md"}, 1),
        }

        for field, record in records.items():
            with self.subTest(field=field):
                standalone = probe.mapping_reference_reads(
                    record,
                    probe.ROOT,
                    TASK_ID,
                )
                try:
                    list_wrapped = probe.mapping_reference_reads(
                        [record],
                        probe.ROOT,
                        TASK_ID,
                    )
                except probe.ProbeFailure as failure:
                    self.fail(
                        f"valid {field} metadata record rejected: "
                        f"{failure.reason}"
                    )

                self.assertEqual(expected[field], standalone)
                self.assertEqual(standalone, list_wrapped)

    def test_alias_independent_structural_siblings_fail_closed(self) -> None:
        compact = (
            f'{{"binary":"sort","parameters":{{"values":["{OWNER}"]}}}}'
        )
        rejected = {
            "executable and arguments": {
                "executable": "sort",
                "arguments": [OWNER],
            },
            "program and args": {"program": "sort", "args": [OWNER]},
            "exe and params": {"exe": "sort", "params": [OWNER]},
            "binary and parameters": {
                "binary": "sort",
                "parameters": [OWNER],
            },
            "arbitrary aliases": {"alpha": "sort", "omega": [OWNER]},
            "nested aliases": {
                "metadata": {"program": "sort", "args": [OWNER]}
            },
            "compact JSON aliases": compact,
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


OWNER_NAME = "apple-api-availability.md"
OWNER = f"{probe.REFERENCE_ROOT_RELATIVE}/{OWNER_NAME}"
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
