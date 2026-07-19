import hashlib
import json
from pathlib import Path
import re
import shutil
import stat
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
README = FIXTURE_ROOT / "README.md"
DEV128_ROOT = ROOT / "fixtures" / "dev-128"
DEV134_PROTOTYPE = (
    ROOT / "docs" / "research" / "evidence" / "dev-134-activation-prototype.json"
)
ACTIVATION_CONTRACTS = (
    ROOT / "docs" / "architecture" / "apple-foundation-models-handoff-skill-contract.md",
    ROOT
    / "docs"
    / "superpowers"
    / "specs"
    / "2026-07-17-dev-134-agent-skill-catalog-design.md",
)
EXPECTED_ACTIVATION_ENVELOPES = (
    "activationStatus = activated\n"
    "selectedSkill\n"
    "preselectionInput = { domain, requestedOperation, artifactState, evidenceState }\n"
    "architectureResult",
    "activationStatus = no_activation\n"
    "reasonCode = out_of_domain\n"
    "domain\n"
    "requestedOperation",
    "activationStatus = clarification_required\n"
    "clarificationKind = domain | approved_contract\n"
    "missingInput\n"
    "question",
)
DEV134_FINDING_CASE_IDS = (
    "DEV138-SCHEMA-MISSING",
    "DEV138-ROUTE-DISALLOWED",
    "DEV138-OWNER-BATON-SOURCE",
    "DEV138-BUDGET-EXCEEDED",
    "DEV138-LOOP",
    "DEV138-TOOL-UNAUTHORIZED",
    "DEV138-CONTEXT-REQUIRED-MISSING",
    "DEV138-C3-LEAK",
    "DEV138-GRANT-DESTINATION-MISMATCH",
    "DEV138-RECOVERY-TERMINATED",
    "DEV138-EFFECT-DUPLICATE-LEDGER",
    "DEV138-EFFECT-RETRY-BEFORE-RECONCILE",
    "DEV138-FALLBACK-EXPANDS-TRUST",
    "DEV138-EVIDENCE-LEAKAGE",
)
DEV134_RUNTIME_MAPPINGS = {
    "DEV134-POS-001": {
        "runtimeIdentity": "baton",
        "evidenceLabel": "deterministic_runtime_invariants_only",
        "caseIds": (
            "DEV138-BATON-VALID",
            "DEV138-OWNER-BATON-SOURCE",
        ),
    },
    "DEV134-POS-002": {
        "runtimeIdentity": "flawed_reducer",
        "evidenceLabel": "runtime_findings_only",
        "caseIds": DEV134_FINDING_CASE_IDS,
    },
    "DEV134-POS-004": {
        "runtimeIdentity": "recovery",
        "evidenceLabel": "deterministic_runtime_invariants_only",
        "caseIds": (
            "DEV138-UNCERTAIN-RECOVERY",
            "DEV138-RECONCILIATION-UNAVAILABLE",
            "DEV138-REPLAY-SUPPRESSED",
            "DEV138-RECONCILED-RETRY",
            "DEV138-EFFECT-RETRY-BEFORE-RECONCILE",
        ),
    },
    "DEV134-POS-006": {
        "runtimeIdentity": "consultation",
        "evidenceLabel": "deterministic_runtime_invariants_only",
        "caseIds": (
            "DEV138-CONSULTATION-VALID",
            "DEV138-OWNER-CONSULT-CHILD",
        ),
    },
    "DEV134-AMB-003": {
        "runtimeIdentity": "review_first",
        "evidenceLabel": "runtime_findings_only",
        "caseIds": DEV134_FINDING_CASE_IDS,
    },
}
DEV134_RUNTIME_MAPPING_NONCLAIMS = (
    "deterministic_runtime_invariant_evidence_only",
    "does_not_prove_router_activation",
    "does_not_prove_review_first_or_no_edit",
    "does_not_prove_host_capability",
    "does_not_prove_apple_runtime_behavior",
    "rubric_owned_by_dev_131",
)
SDK_VERSION = "26.5"
SWIFT_VERSION = "6.3.3"
TARGET = "arm64-apple-macos26.0"
DEFAULT_SWIFT_TARGET = "arm64-apple-macosx26.0"
INTERFACE_SHA256 = "ff2285670b0966addb9827dc895a3ee3c9db6e186baae62c034fed012632aacc"


def _metadata_snapshot(path):
    metadata = path.stat()
    return (
        metadata.st_dev,
        metadata.st_ino,
        stat.S_IFMT(metadata.st_mode),
        stat.S_IMODE(metadata.st_mode),
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def _assert_path_identity(locator, resolution, snapshot, reason):
    try:
        current_resolution = locator.resolve(strict=True)
        current_snapshot = _metadata_snapshot(current_resolution)
    except OSError as error:
        raise AssertionError(reason) from error
    if current_resolution != resolution or current_snapshot != snapshot:
        raise AssertionError(reason)


def _capture_bound_executable(
    locator,
    resolution,
    snapshot,
    arguments,
    reason,
    boundaries=(),
):
    _assert_path_identity(locator, resolution, snapshot, reason)
    for boundary in boundaries:
        _assert_path_identity(*boundary)
    completed = subprocess.run(
        [str(resolution), *map(str, arguments)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    _assert_path_identity(locator, resolution, snapshot, reason)
    for boundary in boundaries:
        _assert_path_identity(*boundary)
    return completed

FOUNDATION_COMMANDS = r'''set -e
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT
swiftc -warnings-as-errors -parse-as-library \
  fixtures/dev-138/HandoffReducer.swift \
  fixtures/dev-138/DeterministicScenarios.swift \
  -o "$TMPDIR/dev-138-fixtures"
"$TMPDIR/dev-138-fixtures" >"$TMPDIR/first.jsonl"
"$TMPDIR/dev-138-fixtures" >"$TMPDIR/second.jsonl"
cmp "$TMPDIR/first.jsonl" "$TMPDIR/second.jsonl"
diff -u fixtures/dev-138/expected-results.jsonl "$TMPDIR/first.jsonl"'''

SDK_COMMANDS = r'''set -e
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT
SWIFT_VERSION="$(swiftc --version)"
SDK="$(xcrun --sdk macosx --show-sdk-path)"
SDK_VERSION="$(xcrun --sdk macosx --show-sdk-version)"
TARGET=arm64-apple-macos26.0
test "$SDK_VERSION" = 26.5

swiftc -typecheck -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/stable-surface.swift
swiftc -typecheck -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/generable-macro.swift
swiftc -parse-as-library -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/availability-probe.swift \
  -o "$TMPDIR/availability"
"$TMPDIR/availability" >"$TMPDIR/availability.out"
rg -q '^availability=' "$TMPDIR/availability.out"
rg -q '^isAvailable=' "$TMPDIR/availability.out"
rg -q '^contextSize=[0-9]+$' "$TMPDIR/availability.out"
rg -q '^supportsCurrentLocale=' "$TMPDIR/availability.out"

swiftc -parse-as-library -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/transcript-roundtrip.swift \
  -o "$TMPDIR/transcript"
test "$("$TMPDIR/transcript")" = \
  'entries=3 codableRoundTrip=true rehydrated=true'

swiftc -parse-as-library -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/session-isolation.swift \
  -o "$TMPDIR/isolation"
test "$("$TMPDIR/isolation")" = \
  'parentEntries=1 childEntries=1 isolated=true'

swiftc -parse-as-library -target "$TARGET" -sdk "$SDK" \
  fixtures/dev-128/compiled/baton-pass-state.swift \
  -o "$TMPDIR/baton"
test "$("$TMPDIR/baton")" = \
  'source=research destination=review active=review finalOwner=review transferred=true'

INTERFACE="$(find \
  "$SDK/System/Library/Frameworks/FoundationModels.framework/Modules/FoundationModels.swiftmodule" \
  -name 'arm64e-apple-macos.swiftinterface' -print -quit)"
test -n "$INTERFACE"
test "$(shasum -a 256 "$INTERFACE" | awk '{print $1}')" = \
  ff2285670b0966addb9827dc895a3ee3c9db6e186baae62c034fed012632aacc'''

BLOCKER_COMMANDS = r'''set -e
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT
SDK="$(xcrun --sdk macosx --show-sdk-path)"

set +e
swiftc -typecheck -target arm64-apple-macos27.0 -sdk "$SDK" \
  fixtures/dev-128/blocked/os-27-beta-surface.swift \
  >"$TMPDIR/beta.out" 2>&1
beta_rc=$?
set -e
test "$beta_rc" -ne 0
rg -q "DynamicProfile.*not a member type|has no member 'Profile'" \
  "$TMPDIR/beta.out"
rg -q "extra arguments at positions #1, #2 in call" \
  "$TMPDIR/beta.out"
rg -q "extra argument 'toolCallingMode' in call" \
  "$TMPDIR/beta.out"

set +e
swiftc -typecheck -target arm64-apple-macos27.0 -sdk "$SDK" \
  fixtures/dev-128/blocked/evaluations-import.swift \
  >"$TMPDIR/evaluations.out" 2>&1
evaluations_rc=$?
set -e
test "$evaluations_rc" -ne 0
rg -q "no such module 'Evaluations'" "$TMPDIR/evaluations.out"'''

OBSERVATION_PROBE_HELPER = r'''
func observation(
    state: HandoffState,
    request: ExecutionRequest,
    context: [ContextField]? = nil
) -> ScenarioObservation {
    ScenarioObservation(
        schemaVersion: 1,
        caseID: "validator-probe",
        pattern: .batonPass,
        sourceProfile: "source",
        sourceProvider: "provider-a",
        destinationProfile: "destination",
        destinationProvider: "provider-b",
        personID: "person-001",
        sessionID: "session-001",
        purpose: "task-execution",
        retention: "ephemeral",
        route: RouteContract(
            pattern: .batonPass,
            destinationProfile: "destination",
            destinationProvider: "provider-b",
            allowedEdges: [.sourceToDestination]
        ),
        requiredContextNames: request.requiredContextNames,
        context: context ?? request.context,
        grant: request.grant,
        clock: 100,
        toolAuthorization: request.authorization,
        toolResult: nil,
        evidence: [],
        state: state,
        eventRecords: [],
        recoveryBaseline: nil,
        auditFacts: []
    )
}

func violations(
    _ state: HandoffState,
    request: ExecutionRequest,
    context: [ContextField]? = nil
) -> [String] {
    HandoffReducer.validate(
        observation(state: state, request: request, context: context)
    )
}
'''

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
        let proposed = HandoffReducer.reduce(
            .initial,
            event: .proposeBaton(proposal: HandoffProposal.fixture(from: .initial))
        )
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

    def test_proposals_bind_current_source_and_refuse_revisit_edge_and_budget(self):
        output = self._run_reducer_probe(
            r'''
import Foundation

@main
struct Probe {
    static func main() {
        let initial = HandoffState.initial
        let valid = HandoffProposal.fixture(from: initial)

        var wrongSource = valid
        wrongSource.sourceProfile = "impersonator"
        let wrong = HandoffReducer.reduce(
            initial,
            event: .proposeBaton(proposal: wrongSource)
        )
        var wrongProvider = valid
        wrongProvider.sourceProvider = "impersonator-provider"
        let wrongProviderDecision = HandoffReducer.reduce(
            initial,
            event: .proposeBaton(proposal: wrongProvider)
        )
        var wrongDestinationProvider = valid
        wrongDestinationProvider.destinationProvider = "unapproved-provider"
        let wrongDestinationDecision = HandoffReducer.reduce(
            initial,
            event: .proposeBaton(proposal: wrongDestinationProvider)
        )

        var staleState = initial
        staleState.stateVersion += 1
        let staleStateProposal = HandoffReducer.reduce(
            staleState,
            event: .proposeBaton(proposal: valid)
        )
        var stalePolicy = initial
        stalePolicy.policyVersion += 1
        let stalePolicyProposal = HandoffReducer.reduce(
            stalePolicy,
            event: .proposeBaton(proposal: valid)
        )

        let proposed = HandoffReducer.reduce(
            initial,
            event: .proposeBaton(proposal: valid)
        )
        let committed = HandoffReducer.reduce(
            proposed.state,
            event: .commitBaton
        ).state

        var staleStateCommit = proposed.state
        staleStateCommit.stateVersion += 1
        let staleStateCommitDecision = HandoffReducer.reduce(
            staleStateCommit,
            event: .commitBaton
        )
        var stalePolicyCommit = proposed.state
        stalePolicyCommit.policyVersion += 1
        let stalePolicyCommitDecision = HandoffReducer.reduce(
            stalePolicyCommit,
            event: .commitBaton
        )

        let revisit = HandoffProposal(
            sourceProfile: committed.activeProfile,
            sourceProvider: committed.activeProvider,
            destinationProfile: "source",
            destinationProvider: "provider-a",
            stateVersion: committed.stateVersion,
            policyVersion: committed.policyVersion
        )
        let repeated = HandoffReducer.reduce(
            committed,
            event: .proposeBaton(proposal: revisit)
        )

        var exhausted = initial
        exhausted.transitionBudget = 0
        let overBudget = HandoffReducer.reduce(
            exhausted,
            event: .proposeBaton(proposal: HandoffProposal.fixture(from: exhausted))
        )

        var disallowed = initial
        disallowed.allowedEdges = []
        let badEdge = HandoffReducer.reduce(
            disallowed,
            event: .proposeBaton(proposal: HandoffProposal.fixture(from: disallowed))
        )

        let values = [
            wrong.state == initial && wrong.command == nil && wrong.disposition == .refusedPolicy,
            wrongProviderDecision.state == initial
                && wrongProviderDecision.command == nil
                && wrongProviderDecision.disposition == .refusedPolicy,
            wrongDestinationDecision.state == initial
                && wrongDestinationDecision.command == nil
                && wrongDestinationDecision.disposition == .refusedPolicy,
            valid.stateVersion == initial.stateVersion
                && valid.policyVersion == initial.policyVersion,
            staleStateProposal.state == staleState
                && staleStateProposal.command == nil
                && staleStateProposal.disposition == .refusedPolicy,
            stalePolicyProposal.state == stalePolicy
                && stalePolicyProposal.command == nil
                && stalePolicyProposal.disposition == .refusedPolicy,
            proposed.state.pendingProposal == valid && proposed.state.phase == .transitioning,
            staleStateCommitDecision.state == staleStateCommit
                && staleStateCommitDecision.command == nil
                && staleStateCommitDecision.disposition == .refusedPolicy,
            stalePolicyCommitDecision.state == stalePolicyCommit
                && stalePolicyCommitDecision.command == nil
                && stalePolicyCommitDecision.disposition == .refusedPolicy,
            committed.activeProfile == valid.destinationProfile && committed.activeProvider == valid.destinationProvider,
            repeated.state == committed && repeated.command == nil && repeated.disposition == .refusedPolicy,
            overBudget.state == exhausted && overBudget.command == nil && overBudget.disposition == .refusedBudget,
            badEdge.state == disallowed && badEdge.command == nil && badEdge.disposition == .refusedPolicy,
        ]
        print(values.map(String.init).joined(separator: "|"))
    }
}
'''
        )
        self.assertEqual(
            output,
            "true|true|true|true|true|true|true|true|true|true|true|true|true\n",
        )

    def test_model_availability_is_typed_reducer_owned_and_fail_closed(self):
        output = self._run_reducer_probe(
            r'''
import Foundation

@main
struct Probe {
    static func main() {
        let initial = HandoffState.initial
        var safe = initial.authorizedBoundary
        safe.providerRank -= 1
        safe.maximumDataClass = .c1TaskPrivate
        safe.retentionRank -= 1
        safe.toolRank -= 1
        safe.effectBudget = 0

        let degraded = HandoffReducer.reduce(
            initial,
            event: .modelAvailability(.degraded(candidate: safe))
        )
        let unavailable = HandoffReducer.reduce(
            initial,
            event: .modelAvailability(.unavailable)
        )
        let equal = HandoffReducer.reduce(
            initial,
            event: .modelAvailability(.degraded(candidate: initial.authorizedBoundary))
        )

        var unsafe = initial.authorizedBoundary
        unsafe.providerRank += 1
        let expanded = HandoffReducer.reduce(
            initial,
            event: .modelAvailability(.degraded(candidate: unsafe))
        )

        let values = [
            degraded.state.fallback == .safeAlternative && degraded.disposition == .applied,
            degraded.state.authorizedBoundary == initial.authorizedBoundary,
            unavailable.state.fallback == .unavailable && unavailable.disposition == .applied,
            equal.state.fallback == .safeAlternative && equal.disposition == .applied,
            expanded.state == initial && expanded.command == nil && expanded.disposition == .refusedPolicy,
        ]
        print(values.map(String.init).joined(separator: "|"))
    }
}
'''
        )
        self.assertEqual(output, "true|true|true|true|true\n")

    def test_transcript_repair_starts_partial_and_reuse_rejects_unbalanced(self):
        output = self._run_reducer_probe(
            r'''
import Foundation

@main
struct Probe {
    static func main() {
        let initial = HandoffState.initial
        let repaired = HandoffReducer.reduce(
            initial,
            event: .repairTranscript(entries: [.call("call-001")])
        )
        let reused = HandoffReducer.reduce(
            initial,
            event: .reuseTranscript(entries: [.call("call-001")])
        )
        let malformed = HandoffReducer.reduce(
            initial,
            event: .repairTranscript(entries: [.result("orphan")])
        )

        let values = [
            repaired.state.transcript == [.call("call-001"), .result("call-001")]
                && repaired.disposition == .applied,
            reused.state == initial && reused.command == nil && reused.disposition == .refusedPolicy,
            malformed.state == initial && malformed.command == nil && malformed.disposition == .refusedPolicy,
        ]
        print(values.map(String.init).joined(separator: "|"))
    }
}
'''
        )
        self.assertEqual(output, "true|true|true\n")

        scenario_source = SOURCES[1].read_text()
        self.assertIn(
            '.repairTranscript(entries: [.call("call-001")])',
            scenario_source,
        )
        self.assertNotIn(
            '[.call("call-001"), .result("call-001")]',
            scenario_source,
        )

    def test_evidence_uses_real_sha256_and_rejects_fingerprint_and_content_bypasses(self):
        output = self._run_reducer_probe(
            r'''
import Foundation

@main
struct Probe {
    static func main() {
        let validContent = "case=DEV138;kind=metadata-only"
        let valid = EvidenceRecord(
            classification: .metadataOnly,
            pathKind: .normalizedRelative,
            artifactExtension: ".jsonl",
            redaction: .redacted,
            content: validContent,
            fingerprint: "sha256:" + SHA256.hexDigest(validContent)
        )
        var mismatched = valid
        mismatched.fingerprint = "sha256:" + String(repeating: "0", count: 64)
        var disguised = valid
        disguised.content = "synthetic-" + "credential-sentinel"
        disguised.fingerprint = "sha256:" + SHA256.hexDigest(disguised.content)
        var rawClassification = valid
        rawClassification.classification = .rawContent
        var absolutePath = valid
        absolutePath.pathKind = .absolute
        var prohibitedExtension = valid
        prohibitedExtension.artifactExtension = ".trace"
        var rawRedaction = valid
        rawRedaction.redaction = .raw
        var homePath = valid
        homePath.content = "/home/fixture/private"
        homePath.fingerprint = "sha256:" + SHA256.hexDigest(homePath.content)
        var uppercaseTraceExtension = valid
        uppercaseTraceExtension.artifactExtension = ".TRACE"
        var uppercaseResultExtension = valid
        uppercaseResultExtension.artifactExtension = ".XCRESULT"
        var lowercaseUserPath = valid
        lowercaseUserPath.content = "/users/fixture/private"
        lowercaseUserPath.fingerprint = "sha256:" + SHA256.hexDigest(lowercaseUserPath.content)
        var uppercaseHomePath = valid
        uppercaseHomePath.content = "/HOME/fixture/private"
        uppercaseHomePath.fingerprint = "sha256:" + SHA256.hexDigest(uppercaseHomePath.content)
        var uppercaseTraceContent = valid
        uppercaseTraceContent.content = "SESSION.TRACE"
        uppercaseTraceContent.fingerprint = "sha256:" + SHA256.hexDigest(uppercaseTraceContent.content)
        var uppercaseRawPayload = valid
        uppercaseRawPayload.content = "RAW-EVIDENCE-PAYLOAD"
        uppercaseRawPayload.fingerprint = "sha256:" + SHA256.hexDigest(uppercaseRawPayload.content)

        let values = [
            SHA256.hexDigest("abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
            HandoffReducer.evidenceRecordIsSafe(valid),
            !HandoffReducer.evidenceRecordIsSafe(mismatched),
            !HandoffReducer.evidenceRecordIsSafe(disguised),
            !HandoffReducer.evidenceRecordIsSafe(rawClassification),
            !HandoffReducer.evidenceRecordIsSafe(absolutePath),
            !HandoffReducer.evidenceRecordIsSafe(prohibitedExtension),
            !HandoffReducer.evidenceRecordIsSafe(rawRedaction),
            !HandoffReducer.evidenceRecordIsSafe(homePath),
            !HandoffReducer.evidenceRecordIsSafe(uppercaseTraceExtension),
            !HandoffReducer.evidenceRecordIsSafe(uppercaseResultExtension),
            !HandoffReducer.evidenceRecordIsSafe(lowercaseUserPath),
            !HandoffReducer.evidenceRecordIsSafe(uppercaseHomePath),
            !HandoffReducer.evidenceRecordIsSafe(uppercaseTraceContent),
            !HandoffReducer.evidenceRecordIsSafe(uppercaseRawPayload),
        ]
        print(values.map(String.init).joined(separator: "|"))
    }
}
'''
        )
        self.assertEqual(
            output,
            "true|true|true|true|true|true|true|true|true|true|true|true|true|true|true\n",
        )

        for mutation in (
            "evidence_bad_fingerprint",
            "evidence_mismatched_fingerprint",
            "evidence_metadata_disguised_prohibited",
        ):
            with self.subTest(mutation=mutation):
                raw_result = self._run_fixture("--mutation", mutation)
                result = json.loads(raw_result)
                self.assertEqual(result["violations"], ["D-EVIDENCE-001"])
                self.assertEqual(result["status"], "fail")
                self.assertNotIn(b"synthetic-credential-sentinel", raw_result)

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
            .repairTranscript(entries: [.call("late")]),
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
        let proposed = HandoffReducer.reduce(
            .initial,
            event: .proposeBaton(proposal: HandoffProposal.fixture(from: .initial))
        )
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
        let proposed = HandoffReducer.reduce(
            .initial,
            event: .proposeBaton(proposal: HandoffProposal.fixture(from: .initial))
        )
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

    def test_consultation_and_execution_call_id_replays_are_refused(self):
        output = self._run_reducer_probe(
            r'''
import Foundation

@main
struct Probe {
    static func main() {
        let firstConsultation = HandoffReducer.reduce(
            .initial,
            event: .completeConsultation
        )
        let repeatedConsultation = HandoffReducer.reduce(
            firstConsultation.state,
            event: .completeConsultation
        )

        let proposed = HandoffReducer.reduce(
            .initial,
            event: .proposeBaton(proposal: HandoffProposal.fixture(from: .initial))
        )
        var committed = HandoffReducer.reduce(
            proposed.state,
            event: .commitBaton
        ).state
        committed.effectBudget = 2
        var firstRequest = ExecutionRequest.fixture(state: committed)
        firstRequest.effectID = "effect-001"
        let firstExecution = HandoffReducer.reduce(
            committed,
            event: .execute(request: firstRequest)
        )
        var reusedCall = ExecutionRequest.fixture(state: firstExecution.state)
        reusedCall.effectID = "effect-002"
        let repeatedExecution = HandoffReducer.reduce(
            firstExecution.state,
            event: .execute(request: reusedCall)
        )

        let values = [
            firstConsultation.command != nil
                && firstConsultation.state.ledger.count == 1,
            repeatedConsultation.state == firstConsultation.state
                && repeatedConsultation.command == nil
                && repeatedConsultation.disposition == .refusedReplay,
            repeatedExecution.state == firstExecution.state
                && repeatedExecution.command == nil
                && repeatedExecution.disposition == .refusedReplay,
        ]
        print(values.map(String.init).joined(separator: "|"))
    }
}
'''
        )
        self.assertEqual(output, "true|true|true\n")

    def test_tool_result_matches_one_current_command_and_is_consumed_once(self):
        output = self._run_reducer_probe(
            r'''
import Foundation

@main
struct Probe {
    static func main() {
        let proposed = HandoffReducer.reduce(
            .initial,
            event: .proposeBaton(proposal: HandoffProposal.fixture(from: .initial))
        )
        let committed = HandoffReducer.reduce(proposed.state, event: .commitBaton).state
        let request = ExecutionRequest.fixture(state: committed)
        let executed = HandoffReducer.reduce(committed, event: .execute(request: request)).state
        let result = ToolResult(
            callID: request.authorization.callID,
            binding: request.authorization.binding,
            stateVersion: executed.stateVersion
        )
        let accepted = HandoffReducer.reduce(
            executed,
            event: .acceptToolResult(
                result: result,
                authorization: request.authorization
            )
        )
        let repeated = HandoffReducer.reduce(
            accepted.state,
            event: .acceptToolResult(
                result: result,
                authorization: request.authorization
            )
        )

        var advanced = executed
        advanced.stateVersion += 1
        var currentAuthorization = request.authorization
        currentAuthorization.stateVersion = advanced.stateVersion
        var currentResult = result
        currentResult.stateVersion = advanced.stateVersion
        let staleOrigin = HandoffReducer.reduce(
            advanced,
            event: .acceptToolResult(
                result: currentResult,
                authorization: currentAuthorization
            )
        )

        var ambiguousCall = executed
        ambiguousCall.toolBudget = 2
        ambiguousCall.effectBudget = 2
        var otherBinding = request.authorization.binding
        otherBinding.version = "2.0"
        ambiguousCall.commandHistory.append(
            ExecutorCommand(
                effectID: "effect-002",
                callID: request.authorization.callID,
                binding: otherBinding,
                stateVersion: executed.stateVersion,
                kind: .initial
            )
        )
        ambiguousCall.ledger.append(
            EffectRecord(
                effectID: "effect-002",
                stateVersion: executed.stateVersion,
                command: otherBinding.name,
                checkpoint: "committed",
                truth: "commandIssued",
                reconciled: false
            )
        )
        ambiguousCall.executorCommandCount += 1
        let ambiguousOrigin = HandoffReducer.reduce(
            ambiguousCall,
            event: .acceptToolResult(
                result: result,
                authorization: request.authorization
            )
        )

        var mixedLedger = executed
        var resolvedStaleRecord = mixedLedger.ledger[0]
        resolvedStaleRecord.stateVersion -= 1
        resolvedStaleRecord.truth = "confirmedApplied"
        resolvedStaleRecord.reconciled = true
        mixedLedger.ledger.append(resolvedStaleRecord)
        mixedLedger.effectBudget = 2
        let mixedLedgerResult = HandoffReducer.reduce(
            mixedLedger,
            event: .acceptToolResult(
                result: result,
                authorization: request.authorization
            )
        )

        let values = [
            accepted.disposition == .applied
                && accepted.state.ledger.first?.truth == "resultAccepted",
            repeated.state == accepted.state
                && repeated.command == nil
                && repeated.disposition == .refusedReplay,
            staleOrigin.state == advanced
                && staleOrigin.command == nil
                && staleOrigin.disposition == .refusedPolicy,
            ambiguousOrigin.state == ambiguousCall
                && ambiguousOrigin.command == nil
                && ambiguousOrigin.disposition == .refusedPolicy,
            mixedLedgerResult.state == mixedLedger
                && mixedLedgerResult.command == nil
                && mixedLedgerResult.disposition == .refusedPolicy,
        ]
        print(values.map(String.init).joined(separator: "|"))
    }
}
'''
        )
        self.assertEqual(output, "true|true|true|true|true\n")

    def test_duplicate_context_names_fail_closed_before_serialization(self):
        output = self._run_reducer_probe(
            r'''
import Foundation

@main
struct Probe {
    static func main() {
        let proposed = HandoffReducer.reduce(
            .initial,
            event: .proposeBaton(proposal: HandoffProposal.fixture(from: .initial))
        )
        let committed = HandoffReducer.reduce(proposed.state, event: .commitBaton).state
        var request = ExecutionRequest.fixture(state: committed)
        request.context.append(request.context[0])
        let decision = HandoffReducer.reduce(
            committed,
            event: .execute(request: request)
        )
        let observation = ScenarioObservation(
            schemaVersion: 1,
            caseID: "duplicate-context-probe",
            pattern: .batonPass,
            sourceProfile: "source",
            sourceProvider: "provider-a",
            destinationProfile: "destination",
            destinationProvider: "provider-b",
            personID: "person-001",
            sessionID: "session-001",
            purpose: "task-execution",
            retention: "ephemeral",
            route: RouteContract(
                pattern: .batonPass,
                destinationProfile: "destination",
                destinationProvider: "provider-b",
                allowedEdges: [.sourceToDestination]
            ),
            requiredContextNames: request.requiredContextNames,
            context: request.context,
            grant: request.grant,
            clock: 100,
            toolAuthorization: request.authorization,
            toolResult: nil,
            evidence: [],
            state: committed,
            eventRecords: [],
            recoveryBaseline: nil,
            auditFacts: []
        )
        let payload = HandoffReducer.serializeContextForProvider(observation)
        print(
            decision.state == committed
                && decision.command == nil
                && decision.disposition == .refusedPolicy
                && payload.isEmpty
        )
    }
}
'''
        )
        self.assertEqual(output, "true\n")

    def test_validator_rejects_duplicate_context_and_call_identities(self):
        output = self._run_reducer_probe(
            r'''
import Foundation
'''
            + OBSERVATION_PROBE_HELPER
            + r'''
@main
struct Probe {
    static func main() {
        let proposed = HandoffReducer.reduce(
            .initial,
            event: .proposeBaton(proposal: HandoffProposal.fixture(from: .initial))
        )
        var committed = HandoffReducer.reduce(proposed.state, event: .commitBaton).state
        committed.effectBudget = 2
        let request = ExecutionRequest.fixture(state: committed)
        var duplicatedContext = request.context
        duplicatedContext.append(duplicatedContext[0])
        var duplicatedCall = HandoffReducer.reduce(
            committed,
            event: .execute(request: request)
        ).state
        let firstCommand = duplicatedCall.commandHistory[0]
        duplicatedCall.commandHistory.append(
            ExecutorCommand(
                effectID: "effect-002",
                callID: firstCommand.callID,
                binding: firstCommand.binding,
                stateVersion: firstCommand.stateVersion,
                kind: .initial
            )
        )
        duplicatedCall.ledger.append(
            EffectRecord(
                effectID: "effect-002",
                stateVersion: firstCommand.stateVersion,
                command: firstCommand.binding.name,
                checkpoint: "committed",
                truth: "commandIssued",
                reconciled: false
            )
        )
        duplicatedCall.executorCommandCount += 1

        let executed = HandoffReducer.reduce(
            committed,
            event: .execute(request: request)
        ).state

        var initialWithRetryBasis = executed
        let initialCommand = initialWithRetryBasis.commandHistory[0]
        initialWithRetryBasis.commandHistory[0] = ExecutorCommand(
            effectID: initialCommand.effectID,
            callID: initialCommand.callID,
            binding: initialCommand.binding,
            stateVersion: initialCommand.stateVersion,
            kind: initialCommand.kind,
            retryBasis: .confirmedNotApplied
        )

        var missingLedger = executed
        missingLedger.ledger = []

        var extraLedger = executed
        extraLedger.ledger.append(
            EffectRecord(
                effectID: "effect-002",
                stateVersion: executed.stateVersion,
                command: "executor.run",
                checkpoint: "committed",
                truth: "commandIssued",
                reconciled: false
            )
        )

        var mismatchedCommand = executed
        mismatchedCommand.ledger[0].command = "other.executor"

        var staleLedger = executed
        staleLedger.ledger[0].stateVersion -= 1

        var staleCommand = executed
        let originalCommand = staleCommand.commandHistory[0]
        staleCommand.commandHistory[0] = ExecutorCommand(
            effectID: originalCommand.effectID,
            callID: originalCommand.callID,
            binding: originalCommand.binding,
            stateVersion: originalCommand.stateVersion - 1,
            kind: originalCommand.kind
        )

        var futureVersion = executed
        futureVersion.ledger[0].stateVersion += 1
        futureVersion.commandHistory[0] = ExecutorCommand(
            effectID: originalCommand.effectID,
            callID: originalCommand.callID,
            binding: originalCommand.binding,
            stateVersion: originalCommand.stateVersion + 1,
            kind: originalCommand.kind
        )

        var forgedBinding = executed
        var otherVersion = originalCommand.binding
        otherVersion.version = "2.0"
        forgedBinding.commandHistory[0] = ExecutorCommand(
            effectID: originalCommand.effectID,
            callID: originalCommand.callID,
            binding: otherVersion,
            stateVersion: originalCommand.stateVersion,
            kind: originalCommand.kind
        )

        var fabricatedTruth = executed
        fabricatedTruth.ledger[0].truth = "fabricated"

        var badCheckpoint = executed
        badCheckpoint.ledger[0].checkpoint = "not-committed"

        var overEffectBudget = executed
        overEffectBudget.effectBudget = 0

        var stableAwaiting = executed
        stableAwaiting.repairFacts = RepairFacts(
            effectID: "effect-001",
            lastKnownTruth: "possibleCommit",
            disposition: .awaitingReconciliation,
            reconciliationAttempts: 0,
            retryAuthority: .denied
        )

        let recovery = HandoffReducer.reduce(
            executed,
            event: .commandUncertain(effectID: "effect-001")
        ).state
        var mismatchedRecovery = recovery
        mismatchedRecovery.repairFacts.effectID = "effect-002"

        var recoveryWithoutEffect = recovery
        recoveryWithoutEffect.commandHistory = []
        recoveryWithoutEffect.executorCommandCount = 0
        recoveryWithoutEffect.ledger = []

        let consultation = HandoffReducer.reduce(.initial, event: .completeConsultation)
        let consultationProposal = HandoffReducer.reduce(
            consultation.state,
            event: .proposeBaton(
                proposal: HandoffProposal.fixture(from: consultation.state)
            )
        )
        let consultationCommitted = HandoffReducer.reduce(
            consultationProposal.state,
            event: .commitBaton
        ).state
        let consultationRequest = ExecutionRequest.fixture(state: consultationCommitted)
        var consultationWithRetryBasis = consultationCommitted
        let consultationCommand = consultationWithRetryBasis.commandHistory[0]
        consultationWithRetryBasis.commandHistory[0] = ExecutorCommand(
            effectID: consultationCommand.effectID,
            callID: consultationCommand.callID,
            binding: consultationCommand.binding,
            stateVersion: consultationCommand.stateVersion,
            kind: consultationCommand.kind,
            retryBasis: .confirmedNotApplied
        )

        var orphanRepair = HandoffState.initial
        orphanRepair.repairFacts = RepairFacts(
            effectID: "orphan-effect",
            lastKnownTruth: "confirmedNotApplied",
            disposition: .reconciled,
            reconciliationAttempts: 1,
            retryAuthority: .authorized
        )
        let orphanRequest = ExecutionRequest.fixture(state: orphanRepair)

        let confirmedApplied = HandoffReducer.reduce(
            recovery,
            event: .reconcileSucceeded(truth: .confirmedApplied)
        ).state
        var mismatchedStableRepair = confirmedApplied
        mismatchedStableRepair.repairFacts.effectID = "effect-002"
        var resolvedWithoutRepair = confirmedApplied
        resolvedWithoutRepair.repairFacts = .none
        var zeroReconciliationAttempts = confirmedApplied
        zeroReconciliationAttempts.repairFacts.reconciliationAttempts = 0
        var reconciledWithoutCommand = confirmedApplied
        reconciledWithoutCommand.commandHistory = []
        reconciledWithoutCommand.executorCommandCount = 0

        let pending = HandoffReducer.reduce(
            .initial,
            event: .proposeBaton(proposal: HandoffProposal.fixture(from: .initial))
        ).state
        let pendingRequest = ExecutionRequest.fixture(state: pending)
        var stalePendingState = pending
        stalePendingState.pendingProposal!.stateVersion -= 1
        var stalePendingPolicy = pending
        stalePendingPolicy.pendingProposal!.policyVersion -= 1
        var wrongPendingTransition = pending
        wrongPendingTransition.pendingTransition = "other-transition"
        var disallowedPendingProposal = pending
        disallowedPendingProposal.pendingProposal!.destinationProvider = "other-provider"

        let values = [
            violations(committed, request: request, context: duplicatedContext)
                .contains("D-CONTEXT-002"),
            violations(duplicatedCall, request: request).contains("D-TOOL-001"),
            violations(executed, request: request).isEmpty,
            violations(initialWithRetryBasis, request: request) == ["D-EFFECT-002"],
            violations(missingLedger, request: request) == ["D-EFFECT-001"],
            violations(extraLedger, request: request) == ["D-EFFECT-001"],
            violations(mismatchedCommand, request: request) == ["D-EFFECT-001"],
            violations(staleLedger, request: request) == ["D-EFFECT-001"],
            violations(staleCommand, request: request) == ["D-EFFECT-001"],
            violations(futureVersion, request: request) == ["D-EFFECT-001"],
            violations(forgedBinding, request: request) == ["D-TOOL-001"],
            violations(fabricatedTruth, request: request) == ["D-EFFECT-001"],
            violations(badCheckpoint, request: request) == ["D-EFFECT-001"],
            violations(overEffectBudget, request: request) == ["D-EFFECT-001"],
            violations(stableAwaiting, request: request) == ["D-PHASE-001"],
            violations(mismatchedRecovery, request: request) == ["D-PHASE-001"],
            violations(recoveryWithoutEffect, request: request) == ["D-PHASE-001"],
            violations(consultationCommitted, request: consultationRequest).isEmpty,
            violations(consultationWithRetryBasis, request: consultationRequest)
                == ["D-EFFECT-002"],
            violations(orphanRepair, request: orphanRequest) == ["D-PHASE-001"],
            violations(mismatchedStableRepair, request: request) == ["D-PHASE-001"],
            violations(resolvedWithoutRepair, request: request) == ["D-PHASE-001"],
            violations(zeroReconciliationAttempts, request: request) == ["D-PHASE-001"],
            violations(reconciledWithoutCommand, request: request)
                == ["D-EFFECT-001", "D-PHASE-001"],
            violations(pending, request: pendingRequest).isEmpty,
            violations(stalePendingState, request: pendingRequest) == ["D-PHASE-001"],
            violations(stalePendingPolicy, request: pendingRequest) == ["D-PHASE-001"],
            violations(wrongPendingTransition, request: pendingRequest) == ["D-PHASE-001"],
            violations(disallowedPendingProposal, request: pendingRequest) == ["D-PHASE-001"],
        ]
        print(values.map(String.init).joined(separator: "|"))
    }
}
'''
        )
        self.assertEqual(
            output,
            "true|true|true|true|true|true|true|true|true|true|true|true|true|true|true|true|true|true|true|true|true|true|true|true|true|true|true|true|true\n",
        )

    def test_execution_grant_expiry_uses_the_request_time_inclusively(self):
        output = self._run_reducer_probe(
            r'''
import Foundation

@main
struct Probe {
    static func main() {
        let proposed = HandoffReducer.reduce(
            .initial,
            event: .proposeBaton(proposal: HandoffProposal.fixture(from: .initial))
        )
        let committed = HandoffReducer.reduce(proposed.state, event: .commitBaton).state

        var boundary = ExecutionRequest.fixture(state: committed)
        boundary.requestedAt = boundary.grant.expiresAt
        let boundaryDecision = HandoffReducer.reduce(
            committed,
            event: .execute(request: boundary)
        )

        var expired = ExecutionRequest.fixture(state: committed)
        expired.requestedAt = expired.grant.expiresAt + 1
        let expiredDecision = HandoffReducer.reduce(
            committed,
            event: .execute(request: expired)
        )

        print(
            boundaryDecision.disposition == .applied
                && boundaryDecision.command != nil
                && expiredDecision.state == committed
                && expiredDecision.command == nil
                && expiredDecision.disposition == .refusedPolicy
        )
    }
}
'''
        )
        self.assertEqual(output, "true\n")

    def test_reconciliation_truth_controls_one_retry_and_resolved_effects_stay_closed(self):
        output = self._run_reducer_probe(
            r'''
import Foundation

func executedState() -> (HandoffState, ExecutionRequest) {
    let proposed = HandoffReducer.reduce(
        .initial,
        event: .proposeBaton(proposal: HandoffProposal.fixture(from: .initial))
    )
    let committed = HandoffReducer.reduce(proposed.state, event: .commitBaton).state
    let request = ExecutionRequest.fixture(state: committed)
    return (
        HandoffReducer.reduce(committed, event: .execute(request: request)).state,
        request
    )
}

func recoveryState(_ executed: HandoffState) -> HandoffState {
    HandoffReducer.reduce(
        executed,
        event: .commandUncertain(effectID: "effect-001")
    ).state
}
'''
            + OBSERVATION_PROBE_HELPER
            + r'''
@main
struct Probe {
    static func main() {
        let (executed, request) = executedState()
        let applied = HandoffReducer.reduce(
            recoveryState(executed),
            event: .reconcileSucceeded(truth: .confirmedApplied)
        )
        let forbiddenRetry = HandoffReducer.reduce(
            applied.state,
            event: .retryReconciled(effectID: "effect-001")
        )

        let notApplied = HandoffReducer.reduce(
            recoveryState(executed),
            event: .reconcileSucceeded(truth: .confirmedNotApplied)
        )
        let retry = HandoffReducer.reduce(
            notApplied.state,
            event: .retryReconciled(effectID: "effect-001")
        )
        let repeatedRetry = HandoffReducer.reduce(
            retry.state,
            event: .retryReconciled(effectID: "effect-001")
        )
        let retryCommand = retry.command!
        let retryAuthorization = ToolAuthorization(
            actorProfile: retry.state.activeProfile,
            callID: retryCommand.callID,
            binding: retryCommand.binding,
            stateVersion: retryCommand.stateVersion,
            policyVersion: retry.state.policyVersion
        )
        let retryResult = ToolResult(
            callID: retryCommand.callID,
            binding: retryCommand.binding,
            stateVersion: retryCommand.stateVersion
        )
        let acceptedRetry = HandoffReducer.reduce(
            retry.state,
            event: .acceptToolResult(
                result: retryResult,
                authorization: retryAuthorization
            )
        )
        let lateOriginalResult = ToolResult(
            callID: request.authorization.callID,
            binding: request.authorization.binding,
            stateVersion: retry.state.stateVersion
        )
        let lateOriginal = HandoffReducer.reduce(
            retry.state,
            event: .acceptToolResult(
                result: lateOriginalResult,
                authorization: request.authorization
            )
        )

        var mixedRecovery = recoveryState(executed)
        var resolvedRecord = mixedRecovery.ledger[0]
        resolvedRecord.truth = "confirmedApplied"
        resolvedRecord.reconciled = true
        mixedRecovery.ledger.append(resolvedRecord)
        mixedRecovery.effectBudget = 2
        let mixedReconciliation = HandoffReducer.reduce(
            mixedRecovery,
            event: .reconcileSucceeded(truth: .confirmedNotApplied)
        )

        var mixedRetryState = notApplied.state
        var otherRecord = mixedRetryState.ledger[0]
        otherRecord.truth = "confirmedApplied"
        mixedRetryState.ledger.append(otherRecord)
        mixedRetryState.effectBudget = 2
        let mixedRetry = HandoffReducer.reduce(
            mixedRetryState,
            event: .retryReconciled(effectID: "effect-001")
        )

        let renewedUncertainty = HandoffReducer.reduce(
            retry.state,
            event: .commandUncertain(effectID: "effect-001")
        )
        let laterReconciliation = HandoffReducer.reduce(
            renewedUncertainty.state,
            event: .reconcileSucceeded(truth: .confirmedApplied)
        )
        let laterNotApplied = HandoffReducer.reduce(
            renewedUncertainty.state,
            event: .reconcileSucceeded(truth: .confirmedNotApplied)
        )

        var forgedRetry = notApplied.state
        forgedRetry.commandHistory.append(
            ExecutorCommand(
                effectID: "effect-001",
                callID: "forged-retry",
                binding: request.authorization.binding,
                stateVersion: forgedRetry.stateVersion,
                kind: .retry
            )
        )
        forgedRetry.executorCommandCount += 1
        forgedRetry.ledger[0].truth = "retryIssued"
        forgedRetry.repairFacts.retryAuthority = .denied

        var forgedBasisRetry = notApplied.state
        forgedBasisRetry.commandHistory.append(
            ExecutorCommand(
                effectID: "effect-001",
                callID: "forged-basis-retry",
                binding: request.authorization.binding,
                stateVersion: forgedBasisRetry.stateVersion,
                kind: .retry,
                retryBasis: .confirmedNotApplied
            )
        )
        forgedBasisRetry.executorCommandCount += 1
        forgedBasisRetry.ledger[0].truth = "retryIssued"
        forgedBasisRetry.repairFacts = .none
        let forgedUncertainty = HandoffReducer.reduce(
            forgedBasisRetry,
            event: .commandUncertain(effectID: "effect-001")
        )

        var malformedRecovery = recoveryState(executed)
        malformedRecovery.pendingTransition = "forged-transition"
        malformedRecovery.lastCheckpoint = "forged-checkpoint"
        malformedRecovery.repairFacts.lastKnownTruth = "fabricated"
        malformedRecovery.repairFacts.reconciliationAttempts = -7
        let malformedReconciliation = HandoffReducer.reduce(
            malformedRecovery,
            event: .reconcileSucceeded(truth: .confirmedApplied)
        )

        var loneRetry = retry.state
        loneRetry.commandHistory.removeFirst()
        loneRetry.executorCommandCount = 1

        let result = ToolResult(
            callID: request.authorization.callID,
            binding: request.authorization.binding,
            stateVersion: executed.stateVersion
        )
        let accepted = HandoffReducer.reduce(
            executed,
            event: .acceptToolResult(result: result, authorization: request.authorization)
        )
        let reopened = HandoffReducer.reduce(
            accepted.state,
            event: .commandUncertain(effectID: "effect-001")
        )

        let values = [
            applied.state.repairFacts.lastKnownTruth == "confirmedApplied"
                && forbiddenRetry.state == applied.state
                && forbiddenRetry.command == nil,
            notApplied.state.repairFacts.lastKnownTruth == "confirmedNotApplied"
                && retry.command?.kind == .retry
                && retryCommand.retryBasis == .confirmedNotApplied
                && retry.state.executorCommandCount == 2,
            repeatedRetry.state == retry.state
                && repeatedRetry.command == nil
                && repeatedRetry.disposition == .refusedReplay,
            HandoffReducer.validate(
                observation(state: applied.state, request: request)
            ).isEmpty,
            HandoffReducer.validate(
                observation(state: notApplied.state, request: request)
            ).isEmpty,
            HandoffReducer.validate(
                observation(state: retry.state, request: request)
            ).isEmpty,
            acceptedRetry.disposition == .applied
                && acceptedRetry.state.ledger[0].truth == "resultAccepted"
                && acceptedRetry.state.ledger[0].reconciled
                && HandoffReducer.validate(
                    observation(state: acceptedRetry.state, request: request)
                ).isEmpty,
            lateOriginal.state == retry.state
                && lateOriginal.command == nil
                && lateOriginal.disposition == .refusedPolicy,
            mixedReconciliation.state == mixedRecovery
                && mixedReconciliation.command == nil
                && mixedReconciliation.disposition == .refusedPolicy,
            mixedRetry.state == mixedRetryState
                && mixedRetry.command == nil
                && mixedRetry.disposition == .refusedPolicy,
            renewedUncertainty.disposition == .applied
                && renewedUncertainty.state.repairFacts.reconciliationAttempts == 1
                && HandoffReducer.validate(
                    observation(state: renewedUncertainty.state, request: request)
                ).isEmpty,
            laterReconciliation.disposition == .applied
                && laterReconciliation.state.repairFacts.reconciliationAttempts == 2
                && HandoffReducer.validate(
                    observation(state: laterReconciliation.state, request: request)
                ).isEmpty,
            laterNotApplied.disposition == .applied
                && laterNotApplied.state.repairFacts.reconciliationAttempts == 2
                && laterNotApplied.state.repairFacts.retryAuthority == .denied
                && HandoffReducer.validate(
                    observation(state: laterNotApplied.state, request: request)
                ).isEmpty,
            HandoffReducer.validate(
                observation(state: forgedRetry, request: request)
            ) == ["D-EFFECT-002"],
            HandoffReducer.validate(
                observation(state: forgedBasisRetry, request: request)
            ) == ["D-PHASE-001"],
            forgedUncertainty.state == forgedBasisRetry
                && forgedUncertainty.command == nil
                && forgedUncertainty.disposition == .refusedPolicy,
            malformedReconciliation.state == malformedRecovery
                && malformedReconciliation.command == nil
                && malformedReconciliation.disposition == .refusedPolicy,
            HandoffReducer.validate(
                observation(state: loneRetry, request: request)
            ) == ["D-EFFECT-002"],
            reopened.state == accepted.state
                && reopened.command == nil
                && reopened.disposition == .refusedPolicy,
        ]
        print(values.map(String.init).joined(separator: "|"))
    }
}
'''
        )
        self.assertEqual(
            output,
            "true|true|true|true|true|true|true|true|true|true|true|true|true|true|true|true|true|true|true\n",
        )

    def test_recovery_requires_one_matching_unresolved_ledger_record(self):
        output = self._run_reducer_probe(
            r'''
import Foundation

@main
struct Probe {
    static func main() {
        let proposed = HandoffReducer.reduce(
            .initial,
            event: .proposeBaton(proposal: HandoffProposal.fixture(from: .initial))
        )
        let committed = HandoffReducer.reduce(proposed.state, event: .commitBaton).state
        let request = ExecutionRequest.fixture(state: committed)
        var duplicated = HandoffReducer.reduce(
            committed,
            event: .execute(request: request)
        ).state
        duplicated.ledger.append(duplicated.ledger[0])
        let decision = HandoffReducer.reduce(
            duplicated,
            event: .commandUncertain(effectID: request.effectID)
        )
        var mixed = duplicated
        mixed.ledger.removeLast()
        var resolved = mixed.ledger[0]
        resolved.truth = "confirmedApplied"
        resolved.reconciled = true
        mixed.ledger.append(resolved)
        let mixedDecision = HandoffReducer.reduce(
            mixed,
            event: .commandUncertain(effectID: request.effectID)
        )
        var missingCommand = duplicated
        missingCommand.ledger.removeLast()
        missingCommand.commandHistory = []
        missingCommand.executorCommandCount = 0
        let missingCommandDecision = HandoffReducer.reduce(
            missingCommand,
            event: .commandUncertain(effectID: request.effectID)
        )
        print(
            decision.state == duplicated
                && decision.command == nil
                && decision.disposition == .refusedPolicy
                && mixedDecision.state == mixed
                && mixedDecision.command == nil
                && mixedDecision.disposition == .refusedPolicy
                && missingCommandDecision.state == missingCommand
                && missingCommandDecision.command == nil
                && missingCommandDecision.disposition == .refusedPolicy
        )
    }
}
'''
        )
        self.assertEqual(output, "true\n")

    def test_retry_requires_one_reconciled_record_and_originating_command(self):
        output = self._run_reducer_probe(
            r'''
import Foundation

func retryState() -> HandoffState {
    var state = HandoffState.initial
    state.repairFacts = RepairFacts(
        effectID: "effect-001",
        lastKnownTruth: "confirmedNotApplied",
        disposition: .reconciled,
        reconciliationAttempts: 1,
        retryAuthority: .authorized
    )
    return state
}

func reconciledRecord() -> EffectRecord {
    EffectRecord(
        effectID: "effect-001",
        stateVersion: 1,
        command: "executor.run",
        checkpoint: "committed",
        truth: "confirmedNotApplied",
        reconciled: true
    )
}

func originatingCommand(callID: String) -> ExecutorCommand {
    ExecutorCommand(
        effectID: "effect-001",
        callID: callID,
        binding: ToolBinding(
            name: "executor.run",
            version: "1.0",
            provider: "provider-b",
            resultType: "ExecutionReceipt"
        ),
        stateVersion: 1,
        kind: .initial
    )
}

@main
struct Probe {
    static func main() {
        let empty = retryState()
        let emptyDecision = HandoffReducer.reduce(
            empty,
            event: .retryReconciled(effectID: "effect-001")
        )

        var missingCommand = retryState()
        missingCommand.ledger = [reconciledRecord()]
        let missingCommandDecision = HandoffReducer.reduce(
            missingCommand,
            event: .retryReconciled(effectID: "effect-001")
        )

        var duplicateCommands = missingCommand
        duplicateCommands.toolBudget = 3
        duplicateCommands.executorCommandCount = 2
        duplicateCommands.commandHistory = [
            originatingCommand(callID: "call-001"),
            originatingCommand(callID: "call-002"),
        ]
        let duplicateDecision = HandoffReducer.reduce(
            duplicateCommands,
            event: .retryReconciled(effectID: "effect-001")
        )

        var mixedRecords = missingCommand
        var resolvedDuplicate = reconciledRecord()
        resolvedDuplicate.truth = "confirmedApplied"
        mixedRecords.ledger.append(resolvedDuplicate)
        mixedRecords.effectBudget = 2
        mixedRecords.executorCommandCount = 1
        mixedRecords.commandHistory = [originatingCommand(callID: "call-001")]
        let mixedRecordDecision = HandoffReducer.reduce(
            mixedRecords,
            event: .retryReconciled(effectID: "effect-001")
        )

        var valid = missingCommand
        valid.executorCommandCount = 1
        valid.commandHistory = [originatingCommand(callID: "call-001")]
        let validDecision = HandoffReducer.reduce(
            valid,
            event: .retryReconciled(effectID: "effect-001")
        )

        let values = [
            emptyDecision.state == empty
                && emptyDecision.command == nil
                && emptyDecision.disposition == .refusedPolicy,
            missingCommandDecision.state == missingCommand
                && missingCommandDecision.command == nil
                && missingCommandDecision.disposition == .refusedPolicy,
            duplicateDecision.state == duplicateCommands
                && duplicateDecision.command == nil
                && duplicateDecision.disposition == .refusedPolicy,
            mixedRecordDecision.state == mixedRecords
                && mixedRecordDecision.command == nil
                && mixedRecordDecision.disposition == .refusedPolicy,
            validDecision.command?.kind == .retry
                && validDecision.state.ledger.count == 1
                && validDecision.state.ledger[0].truth == "retryIssued"
                && validDecision.state.repairFacts.retryAuthority == .denied,
        ]
        print(values.map(String.init).joined(separator: "|"))
    }
}
'''
        )
        self.assertEqual(output, "true|true|true|true|true\n")

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
        scenario_source = SOURCES[1].read_text()
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
        for forbidden_assignment in (
            ".state.transitionHistory =",
            ".state.transitionCount =",
            ".state.visitedProfiles =",
            ".state.fallback =",
            ".transcript =",
            "fallbackPlan",
        ):
            self.assertNotIn(forbidden_assignment, scenario_source)

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


class Dev138SDKTests(unittest.TestCase):
    _temporary_directory = None

    @classmethod
    def setUpClass(cls):
        swiftc = shutil.which("swiftc")
        if swiftc is None:
            raise unittest.SkipTest(
                "blocked/missing_swiftc release_blocker=true"
            )
        xcrun = shutil.which("xcrun")
        if xcrun is None:
            raise unittest.SkipTest(
                "blocked/missing_xcrun release_blocker=true"
            )

        cls.swiftc_locator = Path(swiftc)
        cls.xcrun_locator = Path(xcrun)
        cls.swiftc = cls.swiftc_locator.resolve(strict=True)
        cls.xcrun = cls.xcrun_locator.resolve(strict=True)
        cls.swiftc_snapshot = _metadata_snapshot(cls.swiftc)
        cls.xcrun_snapshot = _metadata_snapshot(cls.xcrun)

        swift_version = cls._capture_swiftc("--version")
        if swift_version.returncode != 0:
            raise unittest.SkipTest(
                "blocked/swift_version_unavailable release_blocker=true"
            )
        if not swift_version.stdout.endswith("\n"):
            raise unittest.SkipTest(
                "blocked/swift_version_malformed release_blocker=true"
            )
        combined_swift_version = swift_version.stderr + swift_version.stdout
        version_match = re.fullmatch(
            r"swift-driver version: [0-9]+(?:\.[0-9]+)+ "
            r"Apple Swift version ([0-9]+\.[0-9]+\.[0-9]+) "
            r"\(swiftlang-[0-9.]+ clang-[0-9.]+\)\n"
            r"Target: ([A-Za-z0-9_.-]+)\n",
            combined_swift_version,
        )
        if version_match is None:
            raise unittest.SkipTest(
                "blocked/swift_version_malformed release_blocker=true"
            )
        if version_match.group(1) != SWIFT_VERSION:
            raise unittest.SkipTest(
                "blocked/swift_version_mismatch release_blocker=true"
            )
        if version_match.group(2) != DEFAULT_SWIFT_TARGET:
            raise unittest.SkipTest(
                "blocked/swift_target_mismatch release_blocker=true"
            )
        cls.swift_version_stdout = swift_version.stdout
        cls.swift_version_stderr = swift_version.stderr
        cls.swift_identity = "swift_" + SWIFT_VERSION.replace(".", "_")
        cls.default_swift_target = version_match.group(2)

        sdk_version = cls._capture_xcrun(
            "--sdk", "macosx", "--show-sdk-version"
        )
        if (
            sdk_version.returncode != 0
            or sdk_version.stderr
            or re.fullmatch(r"[0-9]+\.[0-9]+\n", sdk_version.stdout) is None
        ):
            raise unittest.SkipTest(
                "blocked/sdk_version_malformed release_blocker=true"
            )
        cls.sdk_version = sdk_version.stdout.removesuffix("\n")
        if cls.sdk_version != SDK_VERSION:
            raise unittest.SkipTest(
                "blocked/sdk_version_mismatch release_blocker=true"
            )

        sdk_path = cls._capture_xcrun("--sdk", "macosx", "--show-sdk-path")
        sdk_lines = sdk_path.stdout.splitlines()
        if (
            sdk_path.returncode != 0
            or sdk_path.stderr
            or len(sdk_lines) != 1
            or not Path(sdk_lines[0]).is_absolute()
            or not Path(sdk_lines[0]).is_dir()
        ):
            raise unittest.SkipTest(
                "blocked/sdk_path_malformed release_blocker=true"
            )
        cls.sdk_locator = Path(sdk_lines[0])
        cls.sdk_path = cls.sdk_locator.resolve(strict=True)
        cls.sdk_snapshot = _metadata_snapshot(cls.sdk_path)
        cls._temporary_directory = tempfile.TemporaryDirectory(prefix="dev-138-sdk-")
        cls.temporary_root = Path(cls._temporary_directory.name)
        cls.environment_matrix = (
            {
                "identity": cls.swift_identity,
                "target": cls.default_swift_target,
                "status": "pass",
            },
            {
                "identity": "macos_sdk_26_5",
                "target": TARGET,
                "status": "pass",
            },
        )

    @classmethod
    def tearDownClass(cls):
        if cls._temporary_directory is not None:
            cls._temporary_directory.cleanup()

    @staticmethod
    def _capture(arguments):
        return subprocess.run(
            arguments,
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    @classmethod
    def _capture_swiftc(cls, *arguments):
        boundaries = ()
        if hasattr(cls, "sdk_snapshot"):
            boundaries = (
                (
                    cls.sdk_locator,
                    cls.sdk_path,
                    cls.sdk_snapshot,
                    "fail/sdk_directory_identity_drift",
                ),
            )
        return _capture_bound_executable(
            cls.swiftc_locator,
            cls.swiftc,
            cls.swiftc_snapshot,
            arguments,
            "fail/swiftc_identity_drift",
            boundaries,
        )

    @classmethod
    def _capture_xcrun(cls, *arguments):
        return _capture_bound_executable(
            cls.xcrun_locator,
            cls.xcrun,
            cls.xcrun_snapshot,
            arguments,
            "fail/xcrun_identity_drift",
        )

    def setUp(self):
        self._assert_environment_stable()

    def tearDown(self):
        self._assert_environment_stable()

    def _assert_environment_stable(self):
        current_swiftc = shutil.which("swiftc")
        current_xcrun = shutil.which("xcrun")
        self.assertIsNotNone(current_swiftc, "fail/swiftc_resolution_drift")
        self.assertIsNotNone(current_xcrun, "fail/xcrun_resolution_drift")
        self.assertEqual(
            Path(current_swiftc).resolve(),
            self.swiftc,
            "fail/swiftc_resolution_drift",
        )
        self.assertEqual(
            Path(current_xcrun).resolve(),
            self.xcrun,
            "fail/xcrun_resolution_drift",
        )

        _assert_path_identity(
            self.swiftc_locator,
            self.swiftc,
            self.swiftc_snapshot,
            "fail/swiftc_identity_drift",
        )
        _assert_path_identity(
            self.xcrun_locator,
            self.xcrun,
            self.xcrun_snapshot,
            "fail/xcrun_identity_drift",
        )
        _assert_path_identity(
            self.sdk_locator,
            self.sdk_path,
            self.sdk_snapshot,
            "fail/sdk_directory_identity_drift",
        )

        swift_version = self._capture_swiftc("--version")
        self.assertEqual(swift_version.returncode, 0, "fail/swift_version_drift")
        self.assertEqual(
            swift_version.stdout,
            self.swift_version_stdout,
            "fail/swift_version_drift",
        )
        self.assertEqual(
            swift_version.stderr,
            self.swift_version_stderr,
            "fail/swift_version_drift",
        )

        sdk_version = self._capture_xcrun(
            "--sdk", "macosx", "--show-sdk-version"
        )
        self.assertEqual(sdk_version.returncode, 0, "fail/sdk_version_drift")
        self.assertEqual(
            sdk_version.stdout,
            SDK_VERSION + "\n",
            "fail/sdk_version_drift",
        )
        self.assertEqual(sdk_version.stderr, "", "fail/sdk_version_drift")

        sdk_path = self._capture_xcrun(
            "--sdk", "macosx", "--show-sdk-path"
        )
        self.assertEqual(sdk_path.returncode, 0, "fail/sdk_path_drift")
        self.assertEqual(
            sdk_path.stdout,
            str(self.sdk_locator) + "\n",
            "fail/sdk_path_drift",
        )
        self.assertEqual(sdk_path.stderr, "", "fail/sdk_path_drift")

    def _swift(self, *arguments):
        return self._capture_swiftc(*arguments)

    def _assert_compiles(self, source, *, output=None, target=TARGET):
        arguments = ["-target", target, "-sdk", self.sdk_path]
        if output is None:
            arguments.insert(0, "-typecheck")
        else:
            arguments.insert(0, "-parse-as-library")
            arguments.extend(["-o", output])
        arguments.append(source.relative_to(ROOT))
        completed = self._swift(*arguments)
        self.assertEqual(
            completed.returncode,
            0,
            "fail/positive_probe_compile",
        )
        return completed

    def _assert_expected_blocker(self, source, target, diagnostics):
        completed = self._swift(
            "-typecheck",
            "-target",
            target,
            "-sdk",
            self.sdk_path,
            source.relative_to(ROOT),
        )
        self.assertNotEqual(
            completed.returncode,
            0,
            "fail/expected_blocker_now_supported_reclassification_required",
        )
        output = completed.stdout + completed.stderr
        for diagnostic in diagnostics:
            self.assertTrue(
                re.search(diagnostic, output) is not None,
                "fail/expected_blocker_diagnostic_mismatch",
            )

    def test_bound_executable_rejects_same_path_replacement(self):
        with tempfile.TemporaryDirectory(prefix="dev-138-identity-") as directory:
            locator = Path(directory) / "swiftc"
            replacement = Path(directory) / "replacement"
            locator.write_text(
                "#!/bin/sh\n"
                'mv "$0.replacement" "$0"\n'
                "printf 'same-version\\n'\n",
                encoding="utf-8",
                newline="\n",
            )
            locator.chmod(0o700)
            replacement.write_text(
                "#!/bin/sh\nprintf 'same-version\\n'\n",
                encoding="utf-8",
                newline="\n",
            )
            replacement.chmod(0o700)
            replacement.replace(Path(f"{locator}.replacement"))
            resolution = locator.resolve(strict=True)
            snapshot = _metadata_snapshot(resolution)

            with self.assertRaisesRegex(
                AssertionError,
                "fail/test_executable_identity_drift",
            ):
                _capture_bound_executable(
                    locator,
                    resolution,
                    snapshot,
                    ["--version"],
                    "fail/test_executable_identity_drift",
                )

    def test_environment_matrix_is_exact_and_normalized(self):
        self.assertEqual(self.swift_identity, "swift_6_3_3")
        self.assertEqual(self.default_swift_target, DEFAULT_SWIFT_TARGET)
        self.assertEqual(self.sdk_version, SDK_VERSION)
        self.assertEqual(TARGET, "arm64-apple-macos26.0")
        self.assertEqual(
            self.environment_matrix,
            (
                {
                    "identity": "swift_6_3_3",
                    "target": "arm64-apple-macosx26.0",
                    "status": "pass",
                },
                {
                    "identity": "macos_sdk_26_5",
                    "target": "arm64-apple-macos26.0",
                    "status": "pass",
                },
            ),
        )

    def test_expected_blockers_require_all_specific_diagnostics(self):
        self._assert_expected_blocker(
            DEV128_ROOT / "blocked" / "os-27-beta-surface.swift",
            "arm64-apple-macos27.0",
            [
                r"DynamicProfile.*not a member type|has no member 'Profile'",
                r"extra arguments at positions #1, #2 in call",
                r"extra argument 'toolCallingMode' in call",
            ],
        )
        self._assert_expected_blocker(
            DEV128_ROOT / "blocked" / "evaluations-import.swift",
            "arm64-apple-macos27.0",
            [r"no such module 'Evaluations'"],
        )

    def test_interface_identity_is_exact_sdk_26_5(self):
        interface = (
            self.sdk_path
            / "System"
            / "Library"
            / "Frameworks"
            / "FoundationModels.framework"
            / "Modules"
            / "FoundationModels.swiftmodule"
            / "arm64e-apple-macos.swiftinterface"
        )
        self.assertTrue(
            interface.is_file(),
            "blocked/interface_missing release_blocker=true",
        )
        digest = hashlib.sha256(interface.read_bytes()).hexdigest()
        self.assertEqual(digest, INTERFACE_SHA256, "fail/interface_sha256_mismatch")
        self.assertEqual(
            {
                "identity": "foundation_models_arm64e_interface",
                "sdk": self.sdk_version,
                "sha256": digest,
                "evidence": "interface_verified_sdk_26_5",
            },
            {
                "identity": "foundation_models_arm64e_interface",
                "sdk": "26.5",
                "sha256": INTERFACE_SHA256,
                "evidence": "interface_verified_sdk_26_5",
            },
        )

    def test_positive_dev_128_matrix_uses_exact_labels(self):
        compiled = DEV128_ROOT / "compiled"
        evidence_rows = {}
        stable = self._assert_compiles(compiled / "stable-surface.swift")
        self.assertEqual(stable.stdout, "", "fail/stable_surface_output")
        evidence_rows["stable"] = "compiled_sdk_26_5"

        generable = self._assert_compiles(compiled / "generable-macro.swift")
        self.assertEqual(generable.stdout, "", "fail/generable_macro_output")
        evidence_rows["generable"] = "compiled_sdk_26_5"

        availability = self.temporary_root / "availability"
        self._assert_compiles(
            compiled / "availability-probe.swift",
            output=availability,
        )
        availability_run = self._capture([str(availability)])
        self.assertEqual(
            availability_run.returncode,
            0,
            "fail/availability_probe_runtime",
        )
        availability_lines = availability_run.stdout.splitlines()
        self.assertEqual(len(availability_lines), 4, "fail/availability_shape")
        self.assertTrue(
            re.fullmatch(r"availability=.+", availability_lines[0]) is not None,
            "fail/availability_shape",
        )
        self.assertTrue(
            re.fullmatch(r"isAvailable=(true|false)", availability_lines[1])
            is not None,
            "fail/availability_shape",
        )
        self.assertTrue(
            re.fullmatch(r"contextSize=[0-9]+", availability_lines[2]) is not None,
            "fail/availability_shape",
        )
        self.assertTrue(
            re.fullmatch(
                r"supportsCurrentLocale=(true|false)",
                availability_lines[3],
            )
            is not None,
            "fail/availability_shape",
        )
        evidence_rows["availability"] = "compiled_sdk_26_5"

        transcript = self.temporary_root / "transcript"
        self._assert_compiles(
            compiled / "transcript-roundtrip.swift",
            output=transcript,
        )
        transcript_run = self._capture([str(transcript)])
        self.assertEqual(transcript_run.returncode, 0, "fail/transcript_runtime")
        self.assertEqual(
            transcript_run.stdout,
            "entries=3 codableRoundTrip=true rehydrated=true\n",
        )
        evidence_rows["transcript"] = "compiled_sdk_26_5"

        isolation = self.temporary_root / "isolation"
        self._assert_compiles(
            compiled / "session-isolation.swift",
            output=isolation,
        )
        isolation_run = self._capture([str(isolation)])
        self.assertEqual(isolation_run.returncode, 0, "fail/isolation_runtime")
        self.assertEqual(
            isolation_run.stdout,
            "parentEntries=1 childEntries=1 isolated=true\n",
        )
        evidence_rows["session"] = "compiled_sdk_26_5"

        baton = self.temporary_root / "baton"
        self._assert_compiles(
            compiled / "baton-pass-state.swift",
            output=baton,
        )
        baton_run = self._capture([str(baton)])
        self.assertEqual(baton_run.returncode, 0, "fail/baton_runtime")
        self.assertEqual(
            baton_run.stdout,
            "source=research destination=review active=review "
            "finalOwner=review transferred=true\n",
        )
        evidence_rows["baton"] = "pseudocode_deterministic_mock"

        self.assertEqual(
            evidence_rows,
            {
                "stable": "compiled_sdk_26_5",
                "generable": "compiled_sdk_26_5",
                "availability": "compiled_sdk_26_5",
                "transcript": "compiled_sdk_26_5",
                "session": "compiled_sdk_26_5",
                "baton": "pseudocode_deterministic_mock",
            },
        )

    def test_readme_has_exact_commands_boundaries_and_no_private_paths(self):
        self.assertTrue(README.is_file(), "missing fixtures/dev-138/README.md")
        readme = README.read_text()
        for heading in (
            "## Case map",
            "## Truth boundary",
            "## Foundation-only deterministic commands",
            "## SDK 26.5 commands",
            "## Expected-blocker commands",
            "## Release blockers",
        ):
            self.assertIn(heading, readme)
        self.assertLessEqual(
            EXPECTED_CASE_IDS,
            set(re.findall(r"`(DEV138-[A-Z0-9-]+)`", readme)),
        )
        for label in (
            "compiled_sdk_26_5",
            "interface_verified_sdk_26_5",
            "pseudocode_deterministic_mock",
        ):
            self.assertIn(f"`{label}`", readme)
        for commands in (FOUNDATION_COMMANDS, SDK_COMMANDS, BLOCKER_COMMANDS):
            self.assertIn(f"```bash\n{commands}\n```", readme)
        for blocker in (
            "blocked/missing_swiftc",
            "blocked/missing_xcrun",
            "blocked/sdk_version_mismatch",
        ):
            self.assertIn(f"`{blocker}`", readme)
        self.assertIn("Generic nonzero compilation is `fail`", readme)
        for prohibited in (
            "/" + "Users/",
            "/" + "home/",
            "CommandLine" + "Tools/SDKs",
            ".trace",
            ".xcresult",
        ):
            self.assertNotIn(prohibited, readme)


class Dev138ContractTests(unittest.TestCase):
    @staticmethod
    def _prototype():
        return json.loads(DEV134_PROTOTYPE.read_text())

    @staticmethod
    def _activation_envelopes(path):
        blocks = re.findall(r"```text\n(.*?)\n```", path.read_text(), re.DOTALL)
        return tuple(
            block for block in blocks if block.startswith("activationStatus =")
        )

    def test_activation_prototype_counts_guardrails_and_truth_boundary_are_stable(self):
        prototype = self._prototype()
        cases = prototype["cases"]

        self.assertEqual(prototype["schemaVersion"], "1.0")
        self.assertEqual(prototype["evidenceKind"], "design_contract_prototype")
        self.assertEqual(prototype["executionLayer"], "design_contract_prototype")
        self.assertEqual(prototype["status"], "pass")
        self.assertEqual(
            {
                category: sum(case["category"] == category for case in cases)
                for category in ("positive", "negative", "ambiguous")
            },
            {"positive": 6, "negative": 6, "ambiguous": 3},
        )

        identities = [case["id"] for case in cases]
        self.assertEqual(len(identities), 15)
        self.assertEqual(len(identities), len(set(identities)))
        self.assertEqual(
            {
                owner: sum(case["activationOwner"] == owner for case in cases)
                for owner in ("direct_workflow", "non_positive_router")
            },
            {"direct_workflow": 7, "non_positive_router": 8},
        )
        for contract in ACTIVATION_CONTRACTS:
            envelopes = self._activation_envelopes(contract)
            self.assertEqual(envelopes, EXPECTED_ACTIVATION_ENVELOPES, contract)
            self.assertNotIn("activationOwner", "\n".join(envelopes), contract)
        for case in cases:
            applicable = case["expectedGuardrails"]["applicable"]
            not_applicable = case["expectedGuardrails"]["not_applicable"]
            self.assertEqual(applicable, list(dict.fromkeys(applicable)), case["id"])
            self.assertEqual(
                not_applicable,
                list(dict.fromkeys(not_applicable)),
                case["id"],
            )
            self.assertTrue(set(applicable).isdisjoint(not_applicable), case["id"])
            self.assertLessEqual(
                set(applicable) | set(not_applicable),
                CHECK_IDS,
                case["id"],
            )

        self.assertEqual(
            {host: row["status"] for host, row in prototype["realHostRows"].items()},
            {"claude": "blocked", "codex": "blocked"},
        )
        self.assertIn(
            "No Apple runtime enforcement, host capability, or release-readiness claim is made.",
            prototype["limitations"],
        )

    def test_named_runtime_invariant_mappings_are_exact(self):
        mappings = globals().get("DEV134_RUNTIME_MAPPINGS")
        nonclaims = globals().get("DEV134_RUNTIME_MAPPING_NONCLAIMS")
        self.assertIsNotNone(
            mappings,
            "missing DEV134_RUNTIME_MAPPINGS",
        )
        expected_findings = (
            "DEV138-SCHEMA-MISSING",
            "DEV138-ROUTE-DISALLOWED",
            "DEV138-OWNER-BATON-SOURCE",
            "DEV138-BUDGET-EXCEEDED",
            "DEV138-LOOP",
            "DEV138-TOOL-UNAUTHORIZED",
            "DEV138-CONTEXT-REQUIRED-MISSING",
            "DEV138-C3-LEAK",
            "DEV138-GRANT-DESTINATION-MISMATCH",
            "DEV138-RECOVERY-TERMINATED",
            "DEV138-EFFECT-DUPLICATE-LEDGER",
            "DEV138-EFFECT-RETRY-BEFORE-RECONCILE",
            "DEV138-FALLBACK-EXPANDS-TRUST",
            "DEV138-EVIDENCE-LEAKAGE",
        )
        self.assertEqual(
            mappings,
            {
                "DEV134-POS-001": {
                    "runtimeIdentity": "baton",
                    "evidenceLabel": "deterministic_runtime_invariants_only",
                    "caseIds": (
                        "DEV138-BATON-VALID",
                        "DEV138-OWNER-BATON-SOURCE",
                    ),
                },
                "DEV134-POS-002": {
                    "runtimeIdentity": "flawed_reducer",
                    "evidenceLabel": "runtime_findings_only",
                    "caseIds": expected_findings,
                },
                "DEV134-POS-004": {
                    "runtimeIdentity": "recovery",
                    "evidenceLabel": "deterministic_runtime_invariants_only",
                    "caseIds": (
                        "DEV138-UNCERTAIN-RECOVERY",
                        "DEV138-RECONCILIATION-UNAVAILABLE",
                        "DEV138-REPLAY-SUPPRESSED",
                        "DEV138-RECONCILED-RETRY",
                        "DEV138-EFFECT-RETRY-BEFORE-RECONCILE",
                    ),
                },
                "DEV134-POS-006": {
                    "runtimeIdentity": "consultation",
                    "evidenceLabel": "deterministic_runtime_invariants_only",
                    "caseIds": (
                        "DEV138-CONSULTATION-VALID",
                        "DEV138-OWNER-CONSULT-CHILD",
                    ),
                },
                "DEV134-AMB-003": {
                    "runtimeIdentity": "review_first",
                    "evidenceLabel": "runtime_findings_only",
                    "caseIds": expected_findings,
                },
            },
        )
        self.assertEqual(
            nonclaims,
            (
                "deterministic_runtime_invariant_evidence_only",
                "does_not_prove_router_activation",
                "does_not_prove_review_first_or_no_edit",
                "does_not_prove_host_capability",
                "does_not_prove_apple_runtime_behavior",
                "rubric_owned_by_dev_131",
            ),
        )

        prototype_cases = {
            case["id"]: case for case in self._prototype()["cases"]
        }
        oracle_cases = {row["caseId"]: row for row in self._oracle_rows()}
        self.assertEqual(set(mappings), set(prototype_cases) & set(mappings))
        self.assertEqual(
            set(mappings),
            {
                "DEV134-POS-001",
                "DEV134-POS-002",
                "DEV134-POS-004",
                "DEV134-POS-006",
                "DEV134-AMB-003",
            },
        )
        for activation_id, mapping in mappings.items():
            self.assertEqual(
                prototype_cases[activation_id]["hostExpectations"],
                {
                    "claude": prototype_cases[activation_id]["expectedActivation"],
                    "codex": prototype_cases[activation_id]["expectedActivation"],
                },
            )
            self.assertTrue(mapping["caseIds"])
            self.assertEqual(len(mapping["caseIds"]), len(set(mapping["caseIds"])))
            self.assertLessEqual(set(mapping["caseIds"]), set(oracle_cases))
            for case_id in mapping["caseIds"]:
                self.assertNotIn("D-RUBRIC-001", oracle_cases[case_id]["violations"])

    @staticmethod
    def _oracle_rows():
        return [json.loads(line) for line in ORACLE.read_text().splitlines()]


if __name__ == "__main__":
    unittest.main()
