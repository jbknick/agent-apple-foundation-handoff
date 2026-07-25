import hashlib
import importlib.util
import json
import unittest
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADAPTER = (
    ROOT
    / "fixtures/runtime-v1-capability/synthetic-plugin"
    / "hooks/codex/probe.py"
)
CONTRACT = ROOT / "fixtures/dev-142/runtime_contract.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def hook_payload(output: str) -> dict[str, object]:
    return {
        "session_id": "session-1",
        "transcript_path": "/transient/not-committed.jsonl",
        "cwd": str(ROOT),
        "hook_event_name": "PostToolUse",
        "model": "gpt-5.1-codex",
        "turn_id": "turn-1",
        "permission_mode": "never",
        "tool_name": "Bash",
        "tool_input": {
            "command": "python3 -m unittest -q diagnostic_fixture",
        },
        "tool_response": output,
        "tool_use_id": "call-runtime-v1",
    }


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(ADAPTER.is_file(), "adapter not implemented")
        self.adapter = load_module("runtime_v1_adapter", ADAPTER)
        self.contract = load_module(
            "dev142_contract_for_runtime_v1",
            CONTRACT,
        )

    def eligible_output(self) -> str:
        return (
            "RUNTIME_V1_ORIGINAL_SENTINEL\n"
            "suite=synthetic unittest\n"
            "command-class=test\n"
            "outcome=success\n"
            "exit-status=0\n"
            "warning-count=0\n"
            "command-finished=true\n"
            "task-complete=true\n"
            "next-action=continue after successful synthetic unittest\n"
            "filler="
            + ("a" * 8200)
            + "\n"
        )

    def evaluate(self, output, consult, *, payload=None, observed=None):
        return self.adapter.evaluate(
            hook_payload(output) if payload is None else payload,
            contract=self.contract,
            consult=consult,
            repo_root=ROOT,
            approved_stimulus_sha256=hashlib.sha256(
                output.encode("utf-8")
            ).hexdigest(),
            observe=(
                observed if observed is not None else []
            ).append,
        )

    def applied(self, **changes):
        value = {
            "status": "applied",
            "reasonCode": None,
            "appleAvailable": True,
            "localeSupported": True,
            "contextSize": 4096,
            "occupiedTokens": 2048,
            "appleAttempts": 1,
            "condensation": self.adapter.source_facts(0),
        }
        value.update(changes)
        return value

    def test_applied_consultation_emits_only_stop_reason(self):
        observed = []

        def consult(_request):
            return {
                "status": "applied",
                "reasonCode": None,
                "appleAvailable": True,
                "localeSupported": True,
                "contextSize": 4096,
                "occupiedTokens": 2048,
                "appleAttempts": 1,
                "condensation": self.adapter.source_facts(0),
            }

        output = self.eligible_output()
        response = self.adapter.evaluate(
            hook_payload(output),
            contract=self.contract,
            consult=consult,
            repo_root=ROOT,
            approved_stimulus_sha256=hashlib.sha256(
                output.encode("utf-8")
            ).hexdigest(),
            observe=observed.append,
        )

        self.assertEqual(set(response), {"continue", "stopReason"})
        self.assertIs(response["continue"], False)
        result = json.loads(response["stopReason"])
        self.contract.validate_result(result)
        self.assertEqual(result["outcome"], "applied")
        self.assertLessEqual(
            len(response["stopReason"].encode("utf-8")),
            self.contract.Policy.MAXIMUM_CONDENSED_BYTES,
        )
        self.assertEqual(
            sum(row["event"] == "hook_invoked" for row in observed),
            1,
        )

    def test_below_minimum_never_calls_bridge_and_returns_no_output(self):
        def unexpected(*_):
            self.fail("bridge must not run for an ineligible result")

        output = "short"
        response = self.adapter.evaluate(
            hook_payload(output),
            contract=self.contract,
            consult=unexpected,
            repo_root=ROOT,
            approved_stimulus_sha256=hashlib.sha256(
                output.encode("utf-8")
            ).hexdigest(),
            observe=lambda _: None,
        )
        self.assertIsNone(response)

    def test_bridge_exception_returns_no_output(self):
        def broken(*_):
            raise OSError("synthetic bridge failure")

        output = self.eligible_output()
        response = self.adapter.evaluate(
            hook_payload(output),
            contract=self.contract,
            consult=broken,
            repo_root=ROOT,
            approved_stimulus_sha256=hashlib.sha256(
                output.encode("utf-8")
            ).hexdigest(),
            observe=lambda _: None,
        )
        self.assertIsNone(response)

    def test_closed_hook_boundary_declines_before_bridge(self):
        output = self.eligible_output()
        base = hook_payload(output)
        mutations = {
            "unknown key": {**base, "unknown": True},
            "wrong event": {**base, "hook_event_name": "PreToolUse"},
            "wrong tool": {**base, "tool_name": "Read"},
            "wrong call": {**base, "tool_use_id": "call-other"},
            "wrong cwd": {**base, "cwd": str(ROOT.parent)},
            "wrong command": {
                **base,
                "tool_input": {"command": "python3 -m unittest -q other"},
            },
        }
        for label, payload in mutations.items():
            calls = []
            with self.subTest(label=label):
                self.assertIsNone(
                    self.evaluate(output, calls.append, payload=payload)
                )
                self.assertEqual(calls, [])

    def test_wrong_digest_and_sensitive_message_decline_before_bridge(self):
        output = self.eligible_output()
        calls = []
        self.assertIsNone(
            self.adapter.evaluate(
                hook_payload(output),
                contract=self.contract,
                consult=calls.append,
                repo_root=ROOT,
                approved_stimulus_sha256="0" * 64,
                observe=lambda _: None,
            )
        )
        self.assertEqual(calls, [])

        sensitive = output + "/Users/example/private.txt\n"
        self.assertIsNone(self.evaluate(sensitive, calls.append))
        self.assertEqual(calls, [])

    def test_input_size_bounds_decline_before_bridge(self):
        for output in ("short", self.eligible_output() + ("b" * 66000)):
            calls = []
            with self.subTest(size=len(output)):
                self.assertIsNone(self.evaluate(output, calls.append))
                self.assertEqual(calls, [])

    def test_unavailable_locale_and_context_budget_fall_back(self):
        output = self.eligible_output()
        consultations = (
            self.applied(
                status="declined",
                reasonCode="apple_unavailable",
                appleAvailable=False,
                appleAttempts=0,
                condensation=None,
            ),
            self.applied(
                status="declined",
                reasonCode="locale_unsupported",
                localeSupported=False,
                appleAttempts=0,
                condensation=None,
            ),
            self.applied(
                status="declined",
                reasonCode="context_budget_exceeded",
                occupiedTokens=3073,
                appleAttempts=0,
                condensation=None,
            ),
        )
        for consultation in consultations:
            observed = []
            with self.subTest(reason=consultation["reasonCode"]):
                self.assertIsNone(
                    self.evaluate(
                        output,
                        lambda _: deepcopy(consultation),
                        observed=observed,
                    )
                )
                completed = [
                    row
                    for row in observed
                    if row["event"] == "consultation_completed"
                ]
                self.assertEqual(completed[0]["appleAttempts"], 0)

    def test_malformed_or_invalid_consultation_falls_back(self):
        output = self.eligible_output()
        malformed = self.applied()
        malformed["extra"] = True
        invalid = self.applied()
        invalid["condensation"]["summary"] = "invented"
        for consultation in (malformed, invalid):
            with self.subTest(keys=sorted(consultation)):
                self.assertIsNone(
                    self.evaluate(
                        output,
                        lambda _: deepcopy(consultation),
                    )
                )

    def test_oversized_valid_condensation_falls_back(self):
        output = self.eligible_output()
        oversized = self.adapter.source_facts(0)
        oversized["summary"] = "x" * 5000
        original = self.adapter.source_facts
        self.adapter.source_facts = lambda _: deepcopy(oversized)
        try:
            self.assertIsNone(
                self.evaluate(output, lambda _: self.applied())
            )
        finally:
            self.adapter.source_facts = original

    def test_applied_consultation_requires_one_apple_attempt(self):
        output = self.eligible_output()
        self.assertIsNone(
            self.evaluate(
                output,
                lambda _: self.applied(appleAttempts=0),
            )
        )

    def test_observations_never_contain_original_sentinel(self):
        output = self.eligible_output()
        observed = []
        self.assertIsNotNone(
            self.evaluate(
                output,
                lambda _: self.applied(),
                observed=observed,
            )
        )
        self.assertNotIn(
            "RUNTIME_V1_ORIGINAL_SENTINEL",
            json.dumps(observed, sort_keys=True),
        )
