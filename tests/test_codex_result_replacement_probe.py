from __future__ import annotations

import importlib.util
import hashlib
import json
from pathlib import Path
import unittest


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


def load_probe():
    if not PROBE_PATH.is_file():
        raise AssertionError(f"probe module is missing: {PROBE_PATH}")
    spec = importlib.util.spec_from_file_location("dev_246_probe", PROBE_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError("probe module could not be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class VerdictSchemaTests(unittest.TestCase):
    def passing_observation(self) -> dict[str, object]:
        return {
            "schemaVersion": 1,
            "issue": "DEV-246",
            "codexVersion": "0.144.5",
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


if __name__ == "__main__":
    unittest.main()
