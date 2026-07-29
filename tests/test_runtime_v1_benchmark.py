import importlib.util
import json
import sys
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = (
    ROOT / "fixtures" / "runtime-v1-benchmark" / "runtime_v1_benchmark.py"
)
CORPUS_PATH = ROOT / "fixtures" / "dev-142" / "benchmark-corpus.json"
CORPUS = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
FIXTURES = {case["id"]: case for case in CORPUS["cases"]}
FIXTURE_IDS = tuple(FIXTURES)
SPEC = importlib.util.spec_from_file_location("runtime_v1_benchmark", CONTRACT_PATH)
benchmark = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = benchmark
assert SPEC.loader is not None
SPEC.loader.exec_module(benchmark)


class RuntimeV1BenchmarkTests(unittest.TestCase):
    def usage(self, *, input_tokens=900, output_tokens=100, **changes):
        bounded_input = input_tokens if type(input_tokens) is int else 0
        bounded_output = output_tokens if type(output_tokens) is int else 0
        value = {
            "input_tokens": input_tokens,
            "cached_input_tokens": min(300, max(0, bounded_input)),
            "cache_write_input_tokens": min(200, max(0, bounded_input)),
            "output_tokens": output_tokens,
            "reasoning_output_tokens": min(50, max(0, bounded_output)),
        }
        value.update(changes)
        return value

    def arm(self, role, *, fixture_id=None, total=1000, **changes):
        fixture_id = FIXTURE_IDS[0] if fixture_id is None else fixture_id
        fixture = FIXTURES.get(fixture_id, FIXTURES[FIXTURE_IDS[0]])
        input_tokens = total - 100
        value = {
            "fixture_id": fixture_id,
            "fixture_sha256": fixture["renderedSha256"],
            "arm": role,
            "codex_version": "0.145.0",
            "parent_model": "gpt-5.6-sol",
            "reasoning_effort": "medium",
            "provider": "openai-responses-usage-v1",
            "provider_normalization": "openai-responses-usage-v1",
            "policy_version": "diagnostic-condensation-v1",
            "command_class": fixture["commandClass"],
            "command_form": fixture["commandForm"],
            "task_prompt_sha256": "b" * 64,
            "usage": self.usage(input_tokens=input_tokens),
            "parent_requests": 2,
            "completed_parent_turns": 1,
            "apple_attempts": 0 if role == "pluginOff" else 1,
            "validated_applied": role == "pluginOn",
            "command_executions": 1,
            "correctness_passed": True,
            "cleanup_complete": True,
        }
        value.update(changes)
        return value

    def arm_pair(
        self, fixture_id=None, *, off_total=1000, on_total=900, off=None, on=None
    ):
        return {
            "plugin_off": self.arm(
                "pluginOff",
                fixture_id=fixture_id,
                total=off_total,
                **({} if off is None else off),
            ),
            "plugin_on": self.arm(
                "pluginOn",
                fixture_id=fixture_id,
                total=on_total,
                **({} if on is None else on),
            ),
        }

    def pair(self, fixture_id=None, **changes):
        raw = self.arm_pair(fixture_id, **changes)
        return benchmark.score_pair(raw["plugin_off"], raw["plugin_on"])

    def passing_arm_pairs(self, *, off_total=1000, on_total=900):
        return [
            self.arm_pair(
                fixture_id, off_total=off_total, on_total=on_total
            )
            for fixture_id in FIXTURE_IDS
        ]

    def pair_dict(self, score):
        value = asdict(score)
        value["reason_codes"] = list(value["reason_codes"])
        return value

    def evidence(self, arm_pairs=None, *, unsafe=0):
        arm_pairs = (
            self.passing_arm_pairs() if arm_pairs is None else arm_pairs
        )
        arms = [
            pair[role]
            for pair in arm_pairs
            for role in ("plugin_off", "plugin_on")
        ]
        scores = [
            benchmark.score_pair(pair["plugin_off"], pair["plugin_on"])
            for pair in arm_pairs
        ]
        release = benchmark.release_gate(
            arm_pairs, unsafe_committed_evidence_findings=unsafe
        )
        return {
            "benchmark_profile": benchmark.PROFILE,
            "required_pairs": benchmark.REQUIRED_PAIRS,
            "required_arms": benchmark.REQUIRED_ARMS,
            "observed_pairs": len(arm_pairs),
            "observed_arms": len(arms),
            "arms": arms,
            "pairs": [self.pair_dict(score) for score in scores],
            "release": release,
            "unsafe_committed_evidence_findings": unsafe,
            "status": release["status"],
            "reason_codes": release["reason_codes"],
        }

    def test_constants_corpus_and_frozen_records_are_exact(self):
        self.assertEqual(benchmark.PROFILE, "codex-runtime-v1-cost-v1")
        self.assertEqual(benchmark.REQUIRED_PAIRS, 24)
        self.assertEqual(benchmark.REQUIRED_ARMS, 48)
        self.assertEqual(benchmark.MINIMUM_MEDIAN_REDUCTION_PPM, 100_000)
        self.assertEqual(
            set(benchmark.EXACT_DEV142_FIXTURE_IDS), set(FIXTURE_IDS)
        )
        usage = benchmark.normalize_codex_usage(self.usage())
        with self.assertRaises(Exception):
            usage.input_tokens = 1

    def test_normalize_codex_usage_maps_exactly_through_dev_142(self):
        usage = benchmark.normalize_codex_usage(self.usage())
        self.assertEqual(
            usage,
            benchmark.RuntimeV1Usage(900, 300, 200, 100, 50, 1000),
        )

    def test_cache_write_is_recorded_without_double_counting(self):
        usage = benchmark.normalize_codex_usage(
            self.usage(cache_write_input_tokens=800)
        )
        self.assertEqual(usage.cache_write_input_tokens, 800)
        self.assertEqual(usage.total_parent_tokens, 1000)

    def test_usage_requires_exact_five_keys(self):
        valid = self.usage()
        for key in tuple(valid):
            candidate = dict(valid)
            candidate.pop(key)
            with self.subTest(missing=key), self.assertRaises(
                benchmark.BlockedEvidence
            ):
                benchmark.normalize_codex_usage(candidate)
        with self.assertRaises(benchmark.BlockedEvidence):
            benchmark.normalize_codex_usage({**valid, "total_tokens": 1000})

    def test_usage_rejects_invalid_unsigned_64_values(self):
        for invalid in (True, 1.0, "1", -1, 1 << 64):
            with self.subTest(value=invalid), self.assertRaises(
                benchmark.BlockedEvidence
            ):
                benchmark.normalize_codex_usage(
                    self.usage(input_tokens=invalid)
                )

    def test_usage_rejects_each_subset_violation(self):
        invalid = (
            self.usage(cached_input_tokens=901),
            self.usage(cache_write_input_tokens=901),
            self.usage(reasoning_output_tokens=101),
        )
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(
                benchmark.BlockedEvidence
            ):
                benchmark.normalize_codex_usage(value)

    def test_validate_arm_requires_exact_corpus_identity(self):
        arm = self.arm("pluginOff")
        validated = benchmark.validate_arm(arm)
        self.assertEqual(validated.fixture_id, FIXTURE_IDS[0])
        fixture = FIXTURES[FIXTURE_IDS[0]]
        mutations = (
            {"fixture_id": "arbitrary-01"},
            {"fixture_sha256": "0" * 64},
            {"command_class": "build"},
            {"command_form": "xcodebuild test"},
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation), self.assertRaises(
                benchmark.BlockedEvidence
            ):
                benchmark.validate_arm({**arm, **mutation})
        self.assertEqual(validated.fixture_sha256, fixture["renderedSha256"])

    def test_validate_arm_and_arm_pair_are_closed(self):
        arm = self.arm("pluginOff")
        for candidate in (
            {key: value for key, value in arm.items() if key != "fixture_id"},
            {**arm, "extra": 1},
            {**arm, "arm": "control"},
        ):
            with self.subTest(candidate=candidate), self.assertRaises(
                benchmark.BlockedEvidence
            ):
                benchmark.validate_arm(candidate)
        raw = self.arm_pair()
        pair = benchmark.validate_arm_pair(raw)
        self.assertIsInstance(pair, benchmark.RuntimeV1ArmPair)
        for candidate in (
            {"plugin_off": raw["plugin_off"]},
            {**raw, "extra": {}},
            {
                **raw,
                "plugin_on": self.arm(
                    "pluginOn", fixture_id=FIXTURE_IDS[1]
                ),
            },
        ):
            with self.subTest(candidate=candidate), self.assertRaises(
                benchmark.BlockedEvidence
            ):
                benchmark.validate_arm_pair(candidate)

    def test_pair_blocks_schema_identity_role_and_zero_denominator(self):
        zero = self.arm_pair()
        zero["plugin_off"]["usage"] = self.usage(
            input_tokens=0,
            output_tokens=0,
            cached_input_tokens=0,
            cache_write_input_tokens=0,
            reasoning_output_tokens=0,
        )
        cases = (
            benchmark.score_pair({}, self.arm("pluginOn")),
            benchmark.score_pair(
                self.arm("pluginOff"),
                self.arm("pluginOn", fixture_id=FIXTURE_IDS[1]),
            ),
            benchmark.score_pair(self.arm("pluginOn"), self.arm("pluginOff")),
            benchmark.score_pair(zero["plugin_off"], zero["plugin_on"]),
        )
        for score in cases:
            self.assertEqual(score.status, "blocked")
            self.assertIsNone(score.reduction_ppm)

    def test_pair_passes_at_exactly_ten_percent(self):
        score = self.pair()
        self.assertEqual(score.status, "pass")
        self.assertEqual(score.reduction_ppm, 100_000)
        self.assertEqual(score.apple_attempts, 1)
        self.assertEqual(score.validated_applied_rows, 1)

    def test_pair_failures_cover_correctness_and_operational_invariants(self):
        changes = (
            {"correctness_passed": False},
            {"parent_requests": 3},
            {"completed_parent_turns": 2},
            {"apple_attempts": 2},
            {"command_executions": 2},
        )
        for change in changes:
            with self.subTest(change=change):
                self.assertEqual(self.pair(on=change).status, "fail")
        self.assertEqual(
            self.pair(on={"cleanup_complete": False}).status, "blocked"
        )

    def test_release_gate_passes_exact_24_raw_arm_pairs(self):
        release = benchmark.release_gate(
            self.passing_arm_pairs(),
            unsafe_committed_evidence_findings=0,
        )
        self.assertEqual(release["status"], "pass")
        self.assertEqual(release["observed_pairs"], 24)
        self.assertEqual(release["observed_arms"], 48)
        self.assertEqual(release["median_reduction_ppm"], 100_000)

    def test_release_gate_uses_floor_average_for_even_median(self):
        arm_pairs = [
            self.arm_pair(
                fixture_id,
                off_total=1_000_000,
                on_total=900_001 if index < 12 else 899_998,
            )
            for index, fixture_id in enumerate(FIXTURE_IDS)
        ]
        release = benchmark.release_gate(
            arm_pairs, unsafe_committed_evidence_findings=0
        )
        self.assertEqual(release["median_reduction_ppm"], 100_000)

    def test_24_arbitrary_unique_fixture_ids_cannot_pass(self):
        arm_pairs = [
            self.arm_pair(f"arbitrary-{index:02}") for index in range(24)
        ]
        release = benchmark.release_gate(
            arm_pairs, unsafe_committed_evidence_findings=0
        )
        self.assertEqual(release["status"], "blocked")

    def test_release_blocks_wrong_corpus_sha_class_or_form(self):
        for mutation in (
            {"fixture_sha256": "0" * 64},
            {"command_class": "build"},
            {"command_form": "xcodebuild test"},
        ):
            arm_pairs = self.passing_arm_pairs()
            arm_pairs[0]["plugin_on"].update(mutation)
            with self.subTest(mutation=mutation):
                self.assertEqual(
                    benchmark.release_gate(
                        arm_pairs, unsafe_committed_evidence_findings=0
                    )["status"],
                    "blocked",
                )

    def test_release_blocks_extra_arm_pair_wrapper_keys(self):
        arm_pairs = self.passing_arm_pairs()
        arm_pairs[0]["extra"] = {}
        self.assertEqual(
            benchmark.release_gate(
                arm_pairs, unsafe_committed_evidence_findings=0
            )["status"],
            "blocked",
        )

    def test_release_blocks_missing_extra_duplicate_or_substituted_identity(self):
        passing = self.passing_arm_pairs()
        substituted = deepcopy(passing)
        substituted[0] = self.arm_pair("arbitrary-substitution")
        variants = (
            passing[:-1],
            passing + [deepcopy(passing[0])],
            [*passing[:-1], deepcopy(passing[0])],
            substituted,
        )
        for arm_pairs in variants:
            with self.subTest(length=len(arm_pairs)):
                release = benchmark.release_gate(
                    arm_pairs, unsafe_committed_evidence_findings=0
                )
                self.assertEqual(release["status"], "blocked")

    def test_forged_pair_score_cannot_bypass_release_derivation(self):
        forged = [
            benchmark.RuntimeV1PairScore(
                fixture_id,
                1_000_000,
                "pass",
                (),
                0,
                0,
                0,
                1,
                1,
                0,
                0,
            )
            for fixture_id in FIXTURE_IDS
        ]
        with self.assertRaises(ValueError):
            benchmark.release_gate(
                forged, unsafe_committed_evidence_findings=0
            )

    def test_release_fails_below_threshold_or_safety_requirement(self):
        below = benchmark.release_gate(
            self.passing_arm_pairs(on_total=901),
            unsafe_committed_evidence_findings=0,
        )
        unsafe = benchmark.release_gate(
            self.passing_arm_pairs(), unsafe_committed_evidence_findings=1
        )
        no_apple = self.passing_arm_pairs()
        for pair in no_apple:
            pair["plugin_on"].update(
                apple_attempts=0, validated_applied=False
            )
        for release in (
            below,
            unsafe,
            benchmark.release_gate(
                no_apple, unsafe_committed_evidence_findings=0
            ),
        ):
            self.assertEqual(release["status"], "fail")

    def test_release_rederives_regressions_and_invariants_from_arms(self):
        mutations = (
            {"correctness_passed": False},
            {"parent_requests": 3},
            {"completed_parent_turns": 2},
            {"command_executions": 2},
            {"cleanup_complete": False},
        )
        for mutation in mutations:
            arm_pairs = self.passing_arm_pairs()
            arm_pairs[0]["plugin_on"].update(mutation)
            with self.subTest(mutation=mutation):
                expected = (
                    "blocked"
                    if mutation == {"cleanup_complete": False}
                    else "fail"
                )
                self.assertEqual(
                    benchmark.release_gate(
                        arm_pairs, unsafe_committed_evidence_findings=0
                    )["status"],
                    expected,
                )

    def test_validate_evidence_rederives_pairs_release_and_counts(self):
        evidence = self.evidence()
        self.assertIsNone(benchmark.validate_evidence(evidence))
        mutations = []
        forged_pair = deepcopy(evidence)
        forged_pair["pairs"][0]["reduction_ppm"] = 1_000_000
        mutations.append(forged_pair)
        forged_release = deepcopy(evidence)
        forged_release["release"]["median_reduction_ppm"] = 1_000_000
        mutations.append(forged_release)
        forged_count = deepcopy(evidence)
        forged_count["observed_arms"] = 47
        mutations.append(forged_count)
        forged_status = deepcopy(evidence)
        forged_status["status"] = "fail"
        mutations.append(forged_status)
        extra = {**evidence, "raw": "secret"}
        mutations.append(extra)
        for value in mutations:
            with self.subTest(keys=value.keys()), self.assertRaises(ValueError):
                benchmark.validate_evidence(value)

    def test_validate_evidence_rejects_nested_arm_extras_before_grouping(self):
        arm_pairs = self.passing_arm_pairs()
        arm_pairs[0]["plugin_on"]["extra"] = "untrusted"
        evidence = self.evidence(arm_pairs)
        with self.assertRaises(ValueError):
            benchmark.validate_evidence(evidence)

    def test_pair_score_is_closed_when_serialized(self):
        self.assertEqual(
            set(asdict(self.pair())),
            {
                "fixture_id",
                "reduction_ppm",
                "status",
                "reason_codes",
                "correctness_regressions",
                "additional_parent_requests",
                "additional_parent_turns",
                "apple_attempts",
                "validated_applied_rows",
                "command_reruns",
                "cleanup_failures",
            },
        )


if __name__ == "__main__":
    unittest.main()
