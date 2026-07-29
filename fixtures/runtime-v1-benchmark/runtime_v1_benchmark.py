"""Closed, offline DEV-255 Runtime V1 benchmark arithmetic."""

import hashlib
import importlib.util
import json
from dataclasses import asdict, dataclass
from pathlib import Path
import re
from types import MappingProxyType


_DEV142_PATH = (
    Path(__file__).resolve().parents[1] / "dev-142" / "runtime_contract.py"
)
_DEV142_SPEC = importlib.util.spec_from_file_location(
    "dev142_runtime_contract_for_runtime_v1", _DEV142_PATH
)
_DEV142 = importlib.util.module_from_spec(_DEV142_SPEC)
assert _DEV142_SPEC.loader is not None
_DEV142_SPEC.loader.exec_module(_DEV142)
BlockedEvidence = _DEV142.BlockedEvidence
load_closed_json = _DEV142.load_closed_json
normalize_usage = _DEV142.normalize_usage


PROFILE = "codex-runtime-v1-cost-v1"
REQUIRED_PAIRS = 24
REQUIRED_ARMS = 48
MINIMUM_MEDIAN_REDUCTION_PPM = 100_000
EXACT_DEV142_FIXTURE_IDS = (
    "test-swift-success-unicode-01",
    "test-swift-failure-02",
    "test-xcode-success-03",
    "test-xcode-failure-04",
    "test-pytest-success-05",
    "test-pytest-failure-06",
    "build-swift-success-07",
    "build-swift-failure-08",
    "build-xcode-success-09",
    "build-xcode-failure-10",
    "build-pnpm-success-11",
    "build-pnpm-failure-12",
    "typecheck-swiftc-success-13",
    "typecheck-swiftc-failure-14",
    "typecheck-mypy-success-15",
    "typecheck-mypy-failure-16",
    "typecheck-npm-success-17",
    "typecheck-npm-failure-18",
    "lint-swift-format-success-19",
    "lint-swift-format-failure-20",
    "lint-ruff-success-21",
    "lint-ruff-failure-22",
    "lint-pnpm-success-23",
    "lint-pnpm-failure-24",
)

_CORPUS_SHA256 = (
    "3d671c7e01892eb212b9ccbedeae0dcd13ea84848dbab744d3c3587e42730134"
)
_MAX_UNSIGNED_64 = (1 << 64) - 1
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_CODEX_USAGE_KEYS = frozenset(
    (
        "input_tokens",
        "cached_input_tokens",
        "cache_write_input_tokens",
        "output_tokens",
        "reasoning_output_tokens",
    )
)
_ARM_KEYS = frozenset(
    (
        "fixture_id",
        "fixture_sha256",
        "arm",
        "codex_version",
        "parent_model",
        "reasoning_effort",
        "provider",
        "provider_normalization",
        "policy_version",
        "command_class",
        "command_form",
        "task_prompt_sha256",
        "usage",
        "parent_requests",
        "completed_parent_turns",
        "apple_attempts",
        "validated_applied",
        "command_executions",
        "correctness_passed",
        "cleanup_complete",
    )
)
_PAIR_IDENTITY_FIELDS = (
    "fixture_id",
    "fixture_sha256",
    "codex_version",
    "parent_model",
    "reasoning_effort",
    "provider",
    "provider_normalization",
    "policy_version",
    "command_class",
    "command_form",
    "task_prompt_sha256",
)
_EVIDENCE_KEYS = frozenset(
    (
        "benchmark_profile",
        "required_pairs",
        "required_arms",
        "observed_pairs",
        "observed_arms",
        "arms",
        "pairs",
        "release",
        "unsafe_committed_evidence_findings",
        "status",
        "reason_codes",
    )
)


def _load_fixture_map():
    corpus = load_closed_json(
        Path(__file__).resolve().parents[1]
        / "dev-142"
        / "benchmark-corpus.json"
    )
    if (
        type(corpus) is not dict
        or set(corpus)
        != {
            "schemaVersion",
            "policyVersion",
            "kind",
            "corpusVersion",
            "corpusSha256",
            "cases",
        }
        or corpus["schemaVersion"] != 1
        or corpus["policyVersion"] != "diagnostic-condensation-v1"
        or corpus["kind"] != "corpus"
        or corpus["corpusVersion"] != "dev-142-v1"
        or corpus["corpusSha256"] != _CORPUS_SHA256
        or type(corpus["cases"]) is not list
    ):
        raise RuntimeError("invalid immutable DEV-142 corpus")
    bound = {key: value for key, value in corpus.items() if key != "corpusSha256"}
    digest = hashlib.sha256(
        json.dumps(
            bound,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    if digest != _CORPUS_SHA256:
        raise RuntimeError("invalid immutable DEV-142 corpus")
    identities = tuple(case.get("id") for case in corpus["cases"])
    if (
        identities != EXACT_DEV142_FIXTURE_IDS
        or len(set(identities)) != REQUIRED_PAIRS
    ):
        raise RuntimeError("invalid immutable DEV-142 corpus")
    result = {}
    for case in corpus["cases"]:
        if any(
            type(case.get(key)) is not str or not case[key]
            for key in ("renderedSha256", "commandClass", "commandForm")
        ):
            raise RuntimeError("invalid immutable DEV-142 corpus")
        result[case["id"]] = (
            case["renderedSha256"],
            case["commandClass"],
            case["commandForm"],
        )
    return MappingProxyType(result)


_FIXTURES = _load_fixture_map()


@dataclass(frozen=True)
class RuntimeV1Usage:
    input_tokens: int
    cached_input_tokens: int
    cache_write_input_tokens: int
    output_tokens: int
    reasoning_output_tokens: int
    total_parent_tokens: int


@dataclass(frozen=True)
class RuntimeV1Arm:
    fixture_id: str
    fixture_sha256: str
    arm: str
    codex_version: str
    parent_model: str
    reasoning_effort: str
    provider: str
    provider_normalization: str
    policy_version: str
    command_class: str
    command_form: str
    task_prompt_sha256: str
    usage: RuntimeV1Usage
    parent_requests: int
    completed_parent_turns: int
    apple_attempts: int
    validated_applied: bool
    command_executions: int
    correctness_passed: bool
    cleanup_complete: bool


@dataclass(frozen=True)
class RuntimeV1ArmPair:
    plugin_off: RuntimeV1Arm
    plugin_on: RuntimeV1Arm


@dataclass(frozen=True)
class RuntimeV1PairScore:
    fixture_id: str
    reduction_ppm: int | None
    status: str
    reason_codes: tuple[str, ...]
    correctness_regressions: int
    additional_parent_requests: int
    additional_parent_turns: int
    apple_attempts: int
    validated_applied_rows: int
    command_reruns: int
    cleanup_failures: int


def _unsigned_64(value):
    if type(value) is not int or not 0 <= value <= _MAX_UNSIGNED_64:
        raise BlockedEvidence("provider_usage_schema_or_semantic_drift")
    return value


def normalize_codex_usage(value: object) -> RuntimeV1Usage:
    if type(value) is not dict or set(value) != _CODEX_USAGE_KEYS:
        raise BlockedEvidence("provider_usage_schema_or_semantic_drift")
    fields = {key: _unsigned_64(value[key]) for key in _CODEX_USAGE_KEYS}
    if (
        fields["cached_input_tokens"] > fields["input_tokens"]
        or fields["cache_write_input_tokens"] > fields["input_tokens"]
        or fields["reasoning_output_tokens"] > fields["output_tokens"]
    ):
        raise BlockedEvidence("provider_usage_schema_or_semantic_drift")
    try:
        normalized = normalize_usage(
            "openai-responses-usage-v1",
            {
                "input_tokens": fields["input_tokens"],
                "cached_tokens": fields["cached_input_tokens"],
                "output_tokens": fields["output_tokens"],
                "reasoning_tokens": fields["reasoning_output_tokens"],
            },
        )
    except BlockedEvidence as error:
        raise BlockedEvidence(
            "provider_usage_schema_or_semantic_drift"
        ) from error
    expected_total = fields["input_tokens"] + fields["output_tokens"]
    if (
        normalized.provider != "openai-responses-usage-v1"
        or normalized.input_tokens != fields["input_tokens"]
        or normalized.cached_input_tokens != fields["cached_input_tokens"]
        or normalized.output_tokens != fields["output_tokens"]
        or normalized.reasoning_tokens != fields["reasoning_output_tokens"]
        or normalized.total_parent_model_tokens != expected_total
        or expected_total > _MAX_UNSIGNED_64
    ):
        raise BlockedEvidence("provider_usage_schema_or_semantic_drift")
    return RuntimeV1Usage(
        fields["input_tokens"],
        fields["cached_input_tokens"],
        fields["cache_write_input_tokens"],
        fields["output_tokens"],
        fields["reasoning_output_tokens"],
        expected_total,
    )


def _counter(value):
    if type(value) is not int or value < 0:
        raise BlockedEvidence("invalid_arm_schema")
    return value


def validate_arm(value: object) -> RuntimeV1Arm:
    if type(value) is not dict or set(value) != _ARM_KEYS:
        raise BlockedEvidence("invalid_arm_schema")
    fixture_id = value["fixture_id"]
    if type(fixture_id) is not str or fixture_id not in _FIXTURES:
        raise BlockedEvidence("invalid_fixture_identity")
    expected_sha, expected_class, expected_form = _FIXTURES[fixture_id]
    if (
        value["fixture_sha256"] != expected_sha
        or value["command_class"] != expected_class
        or value["command_form"] != expected_form
    ):
        raise BlockedEvidence("fixture_identity_mismatch")
    fixed = {
        "codex_version": "0.145.0",
        "parent_model": "gpt-5.6-sol",
        "reasoning_effort": "medium",
        "provider": "openai-responses-usage-v1",
        "provider_normalization": "openai-responses-usage-v1",
        "policy_version": "diagnostic-condensation-v1",
    }
    if any(value.get(key) != expected for key, expected in fixed.items()):
        raise BlockedEvidence("pair_identity_mismatch")
    if value["arm"] not in ("pluginOff", "pluginOn"):
        raise BlockedEvidence("invalid_arm_role")
    if (
        type(value["task_prompt_sha256"]) is not str
        or not _DIGEST.fullmatch(value["task_prompt_sha256"])
    ):
        raise BlockedEvidence("invalid_pair_identity")
    for key in (
        "parent_requests",
        "completed_parent_turns",
        "apple_attempts",
        "command_executions",
    ):
        _counter(value[key])
    for key in ("validated_applied", "correctness_passed", "cleanup_complete"):
        if type(value[key]) is not bool:
            raise BlockedEvidence("invalid_arm_schema")
    return RuntimeV1Arm(
        **{**value, "usage": normalize_codex_usage(value["usage"])}
    )


def validate_arm_pair(value: object) -> RuntimeV1ArmPair:
    if type(value) is not dict or set(value) != {"plugin_off", "plugin_on"}:
        raise BlockedEvidence("invalid_arm_pair_schema")
    off = validate_arm(value["plugin_off"])
    on = validate_arm(value["plugin_on"])
    if (off.arm, on.arm) != ("pluginOff", "pluginOn"):
        raise BlockedEvidence("pair_role_mismatch")
    if any(
        getattr(off, field) != getattr(on, field)
        for field in _PAIR_IDENTITY_FIELDS
    ):
        raise BlockedEvidence("pair_identity_mismatch")
    return RuntimeV1ArmPair(off, on)


def _fixture_id(value):
    if type(value) is dict:
        off = value.get("plugin_off")
        if type(off) is dict and type(off.get("fixture_id")) is str:
            return off["fixture_id"]
    return ""


def _blocked_pair(fixture_id, reason):
    return RuntimeV1PairScore(
        fixture_id,
        None,
        "blocked",
        (reason,),
        0,
        0,
        0,
        0,
        0,
        0,
        0,
    )


def score_pair(off: object, on: object) -> RuntimeV1PairScore:
    raw = {"plugin_off": off, "plugin_on": on}
    fixture_id = _fixture_id(raw)
    try:
        pair = validate_arm_pair(raw)
    except BlockedEvidence as error:
        return _blocked_pair(fixture_id, error.reason)
    off_arm, on_arm = pair.plugin_off, pair.plugin_on
    if off_arm.usage.total_parent_tokens == 0:
        return _blocked_pair(fixture_id, "zero_plugin_off_denominator")
    reduction_ppm = (
        (off_arm.usage.total_parent_tokens - on_arm.usage.total_parent_tokens)
        * 1_000_000
        // off_arm.usage.total_parent_tokens
    )
    correctness_regressions = int(
        not off_arm.correctness_passed or not on_arm.correctness_passed
    )
    additional_parent_requests = max(
        on_arm.parent_requests - off_arm.parent_requests, 0
    )
    additional_parent_turns = max(
        on_arm.completed_parent_turns - off_arm.completed_parent_turns, 0
    )
    command_reruns = max(off_arm.command_executions - 1, 0) + max(
        on_arm.command_executions - 1, 0
    )
    cleanup_failures = int(not off_arm.cleanup_complete) + int(
        not on_arm.cleanup_complete
    )
    reasons = set()
    if correctness_regressions:
        reasons.add("correctness_regression")
    if off_arm.parent_requests != 2 or on_arm.parent_requests != 2:
        reasons.add("invalid_parent_request_count")
    if (
        off_arm.completed_parent_turns != 1
        or on_arm.completed_parent_turns != 1
    ):
        reasons.add("invalid_completed_parent_turn_count")
    if (
        off_arm.apple_attempts != 0
        or off_arm.validated_applied
        or on_arm.apple_attempts > 1
        or (on_arm.validated_applied and on_arm.apple_attempts != 1)
    ):
        reasons.add("invalid_apple_attempts")
    if off_arm.command_executions != 1 or on_arm.command_executions != 1:
        reasons.add("command_rerun")
    if cleanup_failures:
        return RuntimeV1PairScore(
            fixture_id,
            None,
            "blocked",
            ("cleanup_incomplete",),
            correctness_regressions,
            additional_parent_requests,
            additional_parent_turns,
            on_arm.apple_attempts,
            int(on_arm.validated_applied),
            command_reruns,
            cleanup_failures,
        )
    return RuntimeV1PairScore(
        fixture_id,
        reduction_ppm,
        "fail" if reasons else "pass",
        tuple(sorted(reasons)),
        correctness_regressions,
        additional_parent_requests,
        additional_parent_turns,
        on_arm.apple_attempts,
        int(on_arm.validated_applied),
        command_reruns,
        0,
    )


def _safety_count(value):
    if type(value) is not int or value < 0:
        raise ValueError("invalid evidence safety count")
    return value


def release_gate(
    arm_pairs: list[object],
    *,
    unsafe_committed_evidence_findings: int,
) -> dict[str, object]:
    _safety_count(unsafe_committed_evidence_findings)
    if type(arm_pairs) is not list:
        raise ValueError("invalid arm pairs")
    if any(type(value) is RuntimeV1PairScore for value in arm_pairs):
        raise ValueError("pair scores are derived output only")

    derived_pairs = []
    identities = []
    for raw in arm_pairs:
        if type(raw) is not dict:
            raise ValueError("invalid arm pair")
        identities.append(_fixture_id(raw))
        try:
            validate_arm_pair(raw)
        except BlockedEvidence as error:
            derived_pairs.append(
                _blocked_pair(_fixture_id(raw), error.reason)
            )
        else:
            derived_pairs.append(
                score_pair(raw["plugin_off"], raw["plugin_on"])
            )
    identity_set = set(identities)
    duplicate_pairs = len(identities) != len(identity_set)
    exact_identities = identity_set == set(EXACT_DEV142_FIXTURE_IDS)
    blocked_pairs = sum(pair.status == "blocked" for pair in derived_pairs)
    failed_pairs = sum(pair.status == "fail" for pair in derived_pairs)
    reductions = sorted(
        pair.reduction_ppm
        for pair in derived_pairs
        if pair.reduction_ppm is not None
    )
    median_reduction_ppm = (
        (reductions[11] + reductions[12]) // 2
        if len(reductions) == REQUIRED_PAIRS
        else None
    )
    totals = {
        key: sum(getattr(pair, key) for pair in derived_pairs)
        for key in (
            "correctness_regressions",
            "additional_parent_requests",
            "additional_parent_turns",
            "apple_attempts",
            "validated_applied_rows",
            "command_reruns",
            "cleanup_failures",
        )
    }
    reasons = set()
    if len(derived_pairs) != REQUIRED_PAIRS:
        reasons.add("missing_or_extra_required_pair")
    if duplicate_pairs:
        reasons.add("duplicate_required_pair")
    if not exact_identities:
        reasons.add("required_fixture_identity_mismatch")
    if blocked_pairs:
        reasons.add("blocked_required_pair")
    if failed_pairs:
        reasons.add("failed_required_pair")
    if (
        median_reduction_ppm is not None
        and median_reduction_ppm < MINIMUM_MEDIAN_REDUCTION_PPM
    ):
        reasons.add("minimum_median_reduction_not_met")
    for key in (
        "correctness_regressions",
        "additional_parent_requests",
        "additional_parent_turns",
        "command_reruns",
    ):
        if totals[key]:
            reasons.add(key)
    if totals["apple_attempts"] < 1:
        reasons.add("missing_real_apple_attempt")
    if totals["validated_applied_rows"] < 1:
        reasons.add("missing_validated_applied_row")
    if totals["cleanup_failures"]:
        reasons.add("cleanup_incomplete")
    if unsafe_committed_evidence_findings:
        reasons.add("unsafe_committed_evidence")
    blocked = (
        len(derived_pairs) != REQUIRED_PAIRS
        or duplicate_pairs
        or not exact_identities
        or blocked_pairs != 0
        or totals["cleanup_failures"] != 0
        or median_reduction_ppm is None
    )
    status = "blocked" if blocked else "fail" if reasons else "pass"
    return {
        "benchmark_profile": PROFILE,
        "required_pairs": REQUIRED_PAIRS,
        "required_arms": REQUIRED_ARMS,
        "observed_pairs": len(derived_pairs),
        "observed_arms": len(derived_pairs) * 2,
        "median_reduction_ppm": median_reduction_ppm,
        **totals,
        "unsafe_committed_evidence_findings":
            unsafe_committed_evidence_findings,
        "status": status,
        "reason_codes": sorted(reasons),
    }


def _serialized_pair(score):
    value = asdict(score)
    value["reason_codes"] = list(score.reason_codes)
    return value


def validate_evidence(value: object) -> None:
    if type(value) is not dict or set(value) != _EVIDENCE_KEYS:
        raise ValueError("invalid evidence shape")
    arms = value["arms"]
    if type(arms) is not list:
        raise ValueError("invalid evidence arms")
    grouped = {}
    for arm in arms:
        if type(arm) is not dict:
            raise ValueError("invalid evidence arm")
        try:
            validate_arm(arm)
        except BlockedEvidence as error:
            raise ValueError("invalid evidence arm") from error
        fixture_id, role = arm.get("fixture_id"), arm.get("arm")
        if type(fixture_id) is not str or role not in ("pluginOff", "pluginOn"):
            raise ValueError("invalid evidence arm identity")
        roles = grouped.setdefault(fixture_id, {})
        if role in roles:
            raise ValueError("duplicate evidence arm")
        roles[role] = arm
    if set(grouped) != set(EXACT_DEV142_FIXTURE_IDS) or any(
        set(roles) != {"pluginOff", "pluginOn"} for roles in grouped.values()
    ):
        raise ValueError("incomplete evidence arm pairs")
    arm_pairs = [
        {
            "plugin_off": grouped[fixture_id]["pluginOff"],
            "plugin_on": grouped[fixture_id]["pluginOn"],
        }
        for fixture_id in EXACT_DEV142_FIXTURE_IDS
    ]
    unsafe = _safety_count(value["unsafe_committed_evidence_findings"])
    release = release_gate(
        arm_pairs, unsafe_committed_evidence_findings=unsafe
    )
    pair_summaries = [
        _serialized_pair(
            score_pair(pair["plugin_off"], pair["plugin_on"])
        )
        for pair in arm_pairs
    ]
    expected = {
        "benchmark_profile": PROFILE,
        "required_pairs": REQUIRED_PAIRS,
        "required_arms": REQUIRED_ARMS,
        "observed_pairs": REQUIRED_PAIRS,
        "observed_arms": REQUIRED_ARMS,
        "arms": arms,
        "pairs": pair_summaries,
        "release": release,
        "unsafe_committed_evidence_findings": unsafe,
        "status": release["status"],
        "reason_codes": release["reason_codes"],
    }
    if value != expected:
        raise ValueError("evidence aggregates are not derived")
