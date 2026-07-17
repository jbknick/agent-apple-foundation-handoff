import json
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "fixtures" / "dev-138"
SOURCES = (
    FIXTURE_ROOT / "HandoffReducer.swift",
    FIXTURE_ROOT / "DeterministicScenarios.swift",
)
ORACLE = FIXTURE_ROOT / "expected-results.jsonl"

CHECK_IDS = {
    "D-SCHEMA-001",
    "D-ROUTE-001",
    "D-OWNER-001",
    "D-TRANSITION-001",
    "D-TOOL-001",
    "D-CONTEXT-001",
    "D-CONTEXT-002",
    "D-GRANT-001",
    "D-PHASE-001",
    "D-EFFECT-001",
    "D-EFFECT-002",
    "D-FALLBACK-001",
    "D-EVIDENCE-001",
    "D-RUBRIC-001",
}

RESULT_KEYS = {
    "schemaVersion",
    "caseId",
    "status",
    "violations",
    "pattern",
    "activeProfile",
    "finalResponseOwner",
    "phase",
    "stateVersion",
    "policyVersion",
    "transitionCount",
    "transitionBudget",
    "executorCommandCount",
    "effectCount",
    "fallback",
    "contextIncluded",
    "contextExcluded",
    "auditEvents",
}

EXPECTED_CASE_IDS = {
    "DEV138-BATON-VALID",
    "DEV138-BUDGET-EXCEEDED",
    "DEV138-C2-REDACTED",
    "DEV138-C2-UNREDACTED",
    "DEV138-C3-BLOCKED",
    "DEV138-C3-LEAK",
    "DEV138-CANCEL-ERASES-RECOVERY",
    "DEV138-CANCEL-PRECOMMIT",
    "DEV138-CANCEL-UNCERTAIN",
    "DEV138-CONSULTATION-VALID",
    "DEV138-CONTEXT-REQUIRED-MISSING",
    "DEV138-EDGE-INVALID",
    "DEV138-EFFECT-DUPLICATE-LEDGER",
    "DEV138-EFFECT-REPLAY-COMMAND",
    "DEV138-EFFECT-RETRY-BEFORE-RECONCILE",
    "DEV138-EVIDENCE-LEAKAGE",
    "DEV138-FALLBACK-EXPANDS-TRUST",
    "DEV138-GRANT-AUTH-EXPIRED",
    "DEV138-GRANT-CLASS-MISMATCH",
    "DEV138-GRANT-DESTINATION-MISMATCH",
    "DEV138-GRANT-FIELD-MISMATCH",
    "DEV138-GRANT-POLICY-STALE",
    "DEV138-GRANT-PURPOSE-MISMATCH",
    "DEV138-GRANT-STATE-STALE",
    "DEV138-INJECTION-IGNORED",
    "DEV138-LOOP",
    "DEV138-MODEL-UNAVAILABLE-EXPLICIT",
    "DEV138-MODEL-UNAVAILABLE-SAFE",
    "DEV138-OWNER-BATON-SOURCE",
    "DEV138-OWNER-CONSULT-CHILD",
    "DEV138-PHASE-INVALID",
    "DEV138-PRECOMMIT-ROLLBACK",
    "DEV138-RECONCILED-RETRY",
    "DEV138-RECONCILIATION-UNAVAILABLE",
    "DEV138-RECOVERY-TERMINATED",
    "DEV138-REPLAY-SUPPRESSED",
    "DEV138-RESULT-SPOOFED",
    "DEV138-ROUTE-DISALLOWED",
    "DEV138-SCHEMA-MISSING",
    "DEV138-TOOL-UNAUTHORIZED",
    "DEV138-TRANSCRIPT-REPAIRED",
    "DEV138-TRANSCRIPT-UNBALANCED",
    "DEV138-UNCERTAIN-RECOVERY",
}


class Dev138FixtureTests(unittest.TestCase):
    _temporary_directory = None
    _executable = None

    @classmethod
    def tearDownClass(cls):
        if cls._temporary_directory is not None:
            cls._temporary_directory.cleanup()

    @classmethod
    def _compile_fixture(cls):
        if cls._executable is not None:
            return cls._executable

        cls._temporary_directory = tempfile.TemporaryDirectory(prefix="dev-138-")
        cls._executable = Path(cls._temporary_directory.name) / "dev-138-fixtures"
        completed = subprocess.run(
            ["swiftc", *map(str, SOURCES), "-o", str(cls._executable)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            raise AssertionError(
                "Swift fixture compilation failed:\n"
                f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
            )
        return cls._executable

    @classmethod
    def _invoke_fixture(cls, *arguments):
        return subprocess.run(
            [str(cls._compile_fixture()), *arguments],
            cwd=ROOT,
            capture_output=True,
            check=False,
        )

    @classmethod
    def _run_fixture(cls, *arguments):
        completed = cls._invoke_fixture(*arguments)
        if completed.returncode != 0:
            raise AssertionError(
                "Swift fixture execution failed:\n"
                f"stdout:\n{completed.stdout.decode()}\n"
                f"stderr:\n{completed.stderr.decode()}"
            )
        return completed.stdout

    def _run_reducer_probe(self, source):
        with tempfile.TemporaryDirectory(prefix="dev-138-probe-") as directory:
            directory = Path(directory)
            harness = directory / "Probe.swift"
            executable = directory / "probe"
            harness.write_text(source)
            completed = subprocess.run(
                [
                    "swiftc",
                    "-warnings-as-errors",
                    "-parse-as-library",
                    str(SOURCES[0]),
                    str(harness),
                    "-o",
                    str(executable),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(
                completed.returncode,
                0,
                f"probe compilation failed:\n{completed.stderr}",
            )
            return subprocess.run(
                [str(executable)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=True,
            ).stdout

    @staticmethod
    def _oracle_rows():
        return [json.loads(line) for line in ORACLE.read_text().splitlines()]

    def test_output_matches_exact_oracle(self):
        for source in SOURCES:
            self.assertTrue(
                source.exists(),
                f"missing fixture source: {source.relative_to(ROOT)}",
            )

        first_run = self._run_fixture()
        second_run = self._run_fixture()
        expected = ORACLE.read_bytes()

        self.assertEqual(first_run, expected)
        self.assertEqual(second_run, expected)
        self.assertEqual(first_run, second_run)

    def test_oracle_is_canonical_closed_shape_and_complete(self):
        raw_lines = ORACLE.read_text().splitlines(keepends=True)
        rows = self._oracle_rows()

        self.assertEqual(len(rows), 43)
        self.assertEqual([row["caseId"] for row in rows], sorted(EXPECTED_CASE_IDS))
        self.assertEqual(EXPECTED_CASE_IDS, {row["caseId"] for row in rows})
        self.assertTrue(ORACLE.read_bytes().endswith(b"\n"))

        for raw_line, row in zip(raw_lines, rows, strict=True):
            self.assertEqual(set(row), RESULT_KEYS, row["caseId"])
            self.assertEqual(
                raw_line,
                json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n",
                row["caseId"],
            )
            self.assertEqual(row["violations"], sorted(set(row["violations"])))
            self.assertLessEqual(set(row["violations"]), CHECK_IDS)
            self.assertEqual(row["status"], "pass" if not row["violations"] else "fail")

    def test_mutations_isolate_every_validator_family_and_grant_binding(self):
        independent_mutations = {
            "tool_unauthorized": ["D-TOOL-001"],
            "context_required_missing": ["D-CONTEXT-001"],
            "context_c3_leak": ["D-CONTEXT-002"],
            "phase_invalid": ["D-PHASE-001"],
            "effect_duplicate": ["D-EFFECT-001"],
            "effect_replay": ["D-EFFECT-002"],
            "fallback_expands_trust": ["D-FALLBACK-001"],
            "evidence_leak": ["D-EVIDENCE-001"],
        }
        grant_mutations = {
            "grant_person_mismatch",
            "grant_session_mismatch",
            "grant_source_profile_mismatch",
            "grant_source_provider_mismatch",
            "grant_destination_profile_mismatch",
            "grant_destination_provider_mismatch",
            "grant_purpose_mismatch",
            "grant_class_mismatch",
            "grant_field_mismatch",
            "grant_tool_mismatch",
            "grant_retention_mismatch",
            "grant_expired",
            "grant_exceptional_c2_missing",
            "grant_state_version_stale",
            "grant_policy_version_stale",
        }
        independent_mutations.update(
            {mutation: ["D-GRANT-001"] for mutation in grant_mutations}
        )

        for mutation, expected in independent_mutations.items():
            with self.subTest(mutation=mutation):
                output = self._run_fixture("--mutation", mutation)
                rows = output.decode().splitlines()
                self.assertEqual(len(rows), 1)
                result = json.loads(rows[0])
                self.assertEqual(result["violations"], expected)
                self.assertEqual(result["status"], "fail")

    def test_recovery_reconciliation_and_late_cancellation_observables(self):
        by_case = {row["caseId"]: row for row in self._oracle_rows()}
        unavailable = by_case["DEV138-RECONCILIATION-UNAVAILABLE"]
        required_snapshot_facts = {
            "authority=destination",
            "pendingEffect=effect-001",
            "checkpoint=uncertain",
            "transitionCount=1",
            "executorCommandCount=1",
            "ledgerCount=1",
            "repair=unavailable",
            "snapshot=unchanged",
        }

        self.assertEqual(unavailable["phase"], "recoveryRequired")
        self.assertEqual(unavailable["executorCommandCount"], 1)
        self.assertEqual(unavailable["effectCount"], 1)
        self.assertLessEqual(required_snapshot_facts, set(unavailable["auditEvents"]))

        replay = by_case["DEV138-REPLAY-SUPPRESSED"]
        self.assertEqual((replay["executorCommandCount"], replay["effectCount"]), (1, 1))
        retried = by_case["DEV138-RECONCILED-RETRY"]
        self.assertEqual((retried["executorCommandCount"], retried["effectCount"]), (2, 1))
        late_cancel = by_case["DEV138-CANCEL-ERASES-RECOVERY"]
        self.assertEqual(
            late_cancel["violations"], ["D-EFFECT-001", "D-PHASE-001"]
        )

    def test_no_safe_reconciliation_and_replay_preserve_the_exact_snapshot(self):
        unavailable = json.loads(
            self._run_fixture(
                "--probe-recovery", "reconciliation-unavailable"
            ).decode()
        )
        replay = json.loads(
            self._run_fixture("--probe-recovery", "replay-suppressed").decode()
        )

        for probe in (unavailable, replay):
            self.assertEqual(probe["before"], probe["after"])
            self.assertIn("repairFacts", probe["before"])
            self.assertIn("auditEvents", probe["before"])
            self.assertTrue(probe["before"]["repairFacts"])
            self.assertTrue(probe["before"]["auditEvents"])
            self.assertFalse(probe["commandEmitted"])
            self.assertEqual(probe["before"]["authority"], "destination")
            self.assertEqual(probe["before"]["phase"], "recoveryRequired")
            self.assertEqual(probe["before"]["pendingEffect"], "effect-001")
            self.assertEqual(
                probe["before"]["pendingTransition"], "effect-reconciliation"
            )
            self.assertEqual(probe["before"]["checkpoint"], "uncertain")
            self.assertEqual(
                probe["before"]["stableCheckpoint"], "baton-committed"
            )
            self.assertEqual(probe["before"]["transitionCount"], 1)
            self.assertEqual(probe["before"]["executorCommandCount"], 1)
            self.assertEqual(probe["before"]["effectCount"], 1)
            self.assertEqual(
                probe["before"]["effectLedger"],
                [
                    {
                        "checkpoint": "committed",
                        "command": "executor.run",
                        "effectID": "effect-001",
                        "reconciled": False,
                        "stateVersion": 2,
                        "truth": "commandIssued",
                    }
                ],
            )

        self.assertEqual(unavailable["outcome"], "repair-blocked/unavailable")
        self.assertEqual(replay["outcome"], "replay-suppressed")

    def test_baton_pass_requires_a_typed_proposal_before_commit(self):
        output = self._run_reducer_probe(
            r'''
import Foundation

@main
struct Probe {
    static func main() {
        let direct = HandoffReducer.reduce(.initial, event: .commitBaton)
        let proposed = HandoffReducer.reduce(.initial, event: .proposeBaton)
        let committed = HandoffReducer.reduce(proposed.state, event: .commitBaton)
        let values = [
            direct.state.phase.rawValue,
            direct.state.activeProfile,
            String(direct.command == nil),
            proposed.state.phase.rawValue,
            proposed.state.activeProfile,
            proposed.state.pendingTransition ?? "none",
            committed.state.phase.rawValue,
            committed.state.activeProfile,
            committed.state.finalResponseOwner,
            String(committed.state.transitionCount),
        ]
        print(values.joined(separator: "|"))
    }
}
'''
        )
        self.assertEqual(
            output,
            "stable|source|true|transitioning|source|baton-pass|stable|destination|destination|1\n",
        )

    def test_recovery_refuses_late_or_wrong_phase_events_without_mutation(self):
        output = self._run_reducer_probe(
            r'''
import Foundation

@main
struct Probe {
    static func main() {
        var recovery = HandoffState.initial
        recovery.activeProfile = "destination"
        recovery.finalResponseOwner = "destination"
        recovery.phase = .recoveryRequired
        recovery.transitionCount = 1
        recovery.executorCommandCount = 1
        recovery.pendingEffectID = "effect-001"
        recovery.pendingTransition = "effect-reconciliation"
        recovery.lastCheckpoint = "uncertain"
        recovery.lastStableCheckpoint = "baton-committed"

        let events: [TrustedEvent] = [
            .completeConsultation,
            .failPrecommit,
            .cancelPrecommit,
            .cancelUncertain,
            .suppressReplay,
            .repairTranscript,
            .ignoreUntrustedInput,
        ]
        let refused = events.map { event -> String in
            let decision = HandoffReducer.reduce(recovery, event: event)
            return String(decision.state == recovery && decision.command == nil)
        }
        print(refused.joined(separator: "|"))
    }
}
'''
        )
        self.assertEqual(output, "true|true|true|true|true|true|true\n")

    def test_adversarial_execution_requests_are_refused_without_state_change(self):
        output = self._run_reducer_probe(
            r'''
import Foundation

@main
struct Probe {
    static func main() {
        let proposed = HandoffReducer.reduce(.initial, event: .proposeBaton)
        let committed = HandoffReducer.reduce(proposed.state, event: .commitBaton).state

        var unauthorized = ExecutionRequest.fixture(state: committed)
        unauthorized.authorization.actorProfile = "source"

        var c3 = ExecutionRequest.fixture(state: committed)
        c3.context.append(
            ContextField(
                name: "never_transfer",
                outputLabel: "never_transfer",
                dataClass: .c3NeverTransfer,
                included: true,
                redacted: false,
                sourceMetadata: "source:secret"
            )
        )

        var grantSuperset = ExecutionRequest.fixture(state: committed)
        grantSuperset.grant.allowedDataClasses.insert(.c2Sensitive)

        let requests = [unauthorized, c3, grantSuperset]
        let refused = requests.map { request -> String in
            let decision = HandoffReducer.reduce(
                committed,
                event: .execute(request: request)
            )
            return String(
                decision.state == committed
                    && decision.command == nil
                    && decision.disposition == .refusedPolicy
            )
        }
        print(refused.joined(separator: "|"))
    }
}
'''
        )
        self.assertEqual(output, "true|true|true\n")

    def test_typed_tool_result_provenance_is_refused_by_reducer(self):
        output = self._run_reducer_probe(
            r'''
import Foundation

@main
struct Probe {
    static func main() {
        let proposed = HandoffReducer.reduce(.initial, event: .proposeBaton)
        let committed = HandoffReducer.reduce(proposed.state, event: .commitBaton).state
        let request = ExecutionRequest.fixture(state: committed)
        let executed = HandoffReducer.reduce(committed, event: .execute(request: request)).state
        var forged = ToolResult(
            callID: request.authorization.callID,
            binding: request.authorization.binding,
            stateVersion: executed.stateVersion
        )
        forged.binding.resultType = "ForgedResult"
        let decision = HandoffReducer.reduce(
            executed,
            event: .acceptToolResult(
                result: forged,
                authorization: request.authorization
            )
        )
        print(
            decision.state == executed
                && decision.command == nil
                && decision.disposition == .refusedPolicy
        )
    }
}
'''
        )
        self.assertEqual(output, "true\n")

    def test_adversarial_matrix_records_refusal_and_command_suppression(self):
        by_case = {row["caseId"]: row for row in self._oracle_rows()}
        refused_without_execution = {
            "DEV138-C2-UNREDACTED",
            "DEV138-C3-LEAK",
            "DEV138-CONTEXT-REQUIRED-MISSING",
            "DEV138-GRANT-AUTH-EXPIRED",
            "DEV138-GRANT-CLASS-MISMATCH",
            "DEV138-GRANT-DESTINATION-MISMATCH",
            "DEV138-GRANT-FIELD-MISMATCH",
            "DEV138-GRANT-POLICY-STALE",
            "DEV138-GRANT-PURPOSE-MISMATCH",
            "DEV138-GRANT-STATE-STALE",
            "DEV138-TOOL-UNAUTHORIZED",
        }
        for case_id in refused_without_execution:
            with self.subTest(case_id=case_id):
                row = by_case[case_id]
                self.assertEqual(row["executorCommandCount"], 0)
                self.assertEqual(row["effectCount"], 0)
                self.assertTrue(
                    any(event.startswith("refusal:") for event in row["auditEvents"])
                )

        spoofed = by_case["DEV138-RESULT-SPOOFED"]
        self.assertEqual((spoofed["executorCommandCount"], spoofed["effectCount"]), (1, 1))
        self.assertIn("refusal:tool-result", spoofed["auditEvents"])

    def test_scenarios_do_not_self_attest_policy_verdicts(self):
        swift_source = "\n".join(source.read_text() for source in SOURCES)
        forbidden_verdict_fields = {
            "routeAllowed",
            "transitionEdgeAllowed",
            "loopDetected",
            "handoffCommitted",
            "commandRequested",
            "commandAuthorized",
            "commandOriginTrusted",
            "untrustedResultAccepted",
            "phaseRuleValid",
            "duplicateLedgerDetected",
            "replayCommandIssued",
            "retryBeforeReconciliation",
            "cancellationErasedRecovery",
            "fallbackExpandedTrust",
            "transcriptBalanced",
            "transcriptRepaired",
            "evidenceSanitized",
            "rubricComplete",
        }
        found = sorted(
            field for field in forbidden_verdict_fields if field in swift_source
        )
        self.assertEqual(found, [], f"self-attested verdict fields remain: {found}")

    def test_exact_grants_and_typed_tool_results_reject_independent_mutations(self):
        mutations = {
            "grant_extra_class": ["D-GRANT-001"],
            "grant_extra_c3_class": ["D-GRANT-001"],
            "grant_extra_field": ["D-GRANT-001"],
            "result_call_id_mismatch": ["D-TOOL-001"],
            "result_tool_version_mismatch": ["D-TOOL-001"],
            "result_provider_mismatch": ["D-TOOL-001"],
            "result_type_mismatch": ["D-TOOL-001"],
            "result_state_version_stale": ["D-TOOL-001"],
        }
        for mutation, expected in mutations.items():
            with self.subTest(mutation=mutation):
                completed = self._invoke_fixture("--mutation", mutation)
                self.assertEqual(
                    completed.returncode,
                    0,
                    completed.stderr.decode(),
                )
                result = json.loads(completed.stdout)
                self.assertEqual(result["violations"], expected)

    def test_jsonl_is_the_only_expected_outcome_oracle(self):
        test_source = Path(__file__).read_text()
        duplicate_map_name = "EXPECTED_" + "VIOLATIONS"
        self.assertNotIn(duplicate_map_name, test_source)

    def test_swift_does_not_duplicate_dev_131_rubric_scoring(self):
        swift_source = "\n".join(source.read_text() for source in SOURCES)
        self.assertNotIn("D-" + "RUBRIC-001", swift_source)
        self.assertNotIn("rubric_" + "incomplete", swift_source)

    def test_context_fallback_transcript_and_evidence_are_safely_observable(self):
        by_case = {row["caseId"]: row for row in self._oracle_rows()}

        self.assertIn("customer_record:redacted", by_case["DEV138-C2-REDACTED"]["contextIncluded"])
        self.assertIn("raw_secret", by_case["DEV138-C3-BLOCKED"]["contextExcluded"])
        self.assertEqual(by_case["DEV138-MODEL-UNAVAILABLE-SAFE"]["fallback"], "safeAlternative")
        self.assertEqual(by_case["DEV138-MODEL-UNAVAILABLE-EXPLICIT"]["fallback"], "unavailable")
        self.assertIn("transcript:repaired", by_case["DEV138-TRANSCRIPT-REPAIRED"]["auditEvents"])

        output = self._run_fixture()
        for prohibited in (
            b"blocked-c3-sentinel",
            b"synthetic-credential-sentinel",
            b"/Users/fixture/private",
            b"session.trace",
            b"raw-evidence-payload",
        ):
            self.assertNotIn(prohibited, output)

        context_probe = json.loads(self._run_fixture("--probe-context").decode())
        self.assertEqual(set(context_probe["blockedPayload"]), {"task_summary"})
        self.assertEqual(context_probe["rejectedLeakPayload"], {})
        self.assertNotIn("blocked-c3-sentinel", json.dumps(context_probe))

    def test_scenarios_are_oracle_independent_and_foundation_only(self):
        reducer_source = SOURCES[0].read_text()
        scenario_source = SOURCES[1].read_text()

        self.assertNotIn("expected-results.jsonl", reducer_source)
        self.assertNotIn("expected-results.jsonl", scenario_source)
        self.assertNotIn("expectedViolations", scenario_source)
        self.assertNotIn("expectedStatus", scenario_source)
        self.assertNotIn('"D-', scenario_source)

        imports = {
            line.strip()
            for source in SOURCES
            for line in source.read_text().splitlines()
            if line.startswith("import ")
        }
        self.assertEqual(imports, {"import Foundation"})


if __name__ == "__main__":
    unittest.main()
