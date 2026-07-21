"""Closed, offline DEV-142 policy envelopes.

This module deliberately performs no host, process, or model operation.
"""

import json
import hashlib
import math
import os
import re
import shlex
import stat
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path


class _FrozenPolicy(type):
    def __setattr__(cls, name, value):
        raise AttributeError("Policy is immutable")

    def __delattr__(cls, name):
        raise AttributeError("Policy is immutable")


class Policy(metaclass=_FrozenPolicy):
    SCHEMA_VERSION = 1
    POLICY_VERSION = "diagnostic-condensation-v1"
    ACTION = "condense_diagnostic_output"
    RESULT_TYPE = "diagnostic_condensation"
    TOOL_NAME = "Bash"
    EVENT_NAME = "PostToolUse"
    MINIMUM_INPUT_BYTES = 8192
    MAXIMUM_INPUT_BYTES = 65536
    MAXIMUM_CONDENSED_BYTES = 4096
    MINIMUM_ESTIMATED_SAVINGS_BYTES = 4096
    MINIMUM_REALIZED_SAVINGS_BYTES = 4096
    MAXIMUM_APPLE_RESPONSE_TOKENS = 1024
    MAXIMUM_APPLE_CONTEXT_NUMERATOR = 3
    MAXIMUM_APPLE_CONTEXT_DENOMINATOR = 4
    APPROVED_BENCHMARK_COMMAND_FORMS = frozenset((
        "swift test", "xcodebuild test", "python3 -m pytest",
        "swift build", "xcodebuild build", "pnpm build",
        "swiftc -typecheck", "python3 -m mypy", "npm run typecheck",
        "swift format lint", "python3 -m ruff check", "pnpm lint",
    ))


class ContractError(ValueError):
    pass


class RouteDeclined(ValueError):
    def __init__(self, reason):
        self.reason = reason
        super().__init__(reason)


@dataclass(frozen=True)
class CommandSelection:
    command_class: str
    tokens: tuple
    path_state: tuple = ()


@dataclass(frozen=True)
class QualityScore:
    passed: bool
    reason_codes: tuple[str, ...]


class BlockedEvidence(ValueError):
    def __init__(self, reason):
        self.reason = reason
        super().__init__(reason)


@dataclass(frozen=True)
class NormalizedUsage:
    provider: str
    input_tokens: int
    cached_input_tokens: int
    output_tokens: int
    reasoning_tokens: int | None
    total_parent_model_tokens: int


@dataclass(frozen=True)
class PairScore:
    host: str
    case_id: str
    status: str
    reduction_ppm: int | None
    correctness_regressions: int
    additional_parent_model_turns: int
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class ReleaseScore:
    status: str
    valid_required_pairs: int
    blocked_required_pairs: int
    median_reduction_ppm: int | None
    correctness_regressions: int
    additional_parent_model_turns: int
    exploratory_pairs: int
    reason_codes: tuple[str, ...]


_MAX_UNSIGNED_64 = (1 << 64) - 1
_MIN_REDUCTION_PPM = (1 - _MAX_UNSIGNED_64) * 1_000_000
_MAX_REDUCTION_PPM = 1_000_000
_REQUIRED_HOSTS = ("claude-code-2.1.91", "codex-cli-0.144.5")
_REQUIRED_CASE_IDS = (
    "test-swift-success-unicode-01", "test-swift-failure-02",
    "test-xcode-success-03", "test-xcode-failure-04",
    "test-pytest-success-05", "test-pytest-failure-06",
    "build-swift-success-07", "build-swift-failure-08",
    "build-xcode-success-09", "build-xcode-failure-10",
    "build-pnpm-success-11", "build-pnpm-failure-12",
    "typecheck-swiftc-success-13", "typecheck-swiftc-failure-14",
    "typecheck-mypy-success-15", "typecheck-mypy-failure-16",
    "typecheck-npm-success-17", "typecheck-npm-failure-18",
    "lint-swift-format-success-19", "lint-swift-format-failure-20",
    "lint-ruff-success-21", "lint-ruff-failure-22",
    "lint-pnpm-success-23", "lint-pnpm-failure-24",
)
REQUIRED_PAIR_IDENTITIES = tuple(
    (host, case_id) for host in _REQUIRED_HOSTS for case_id in _REQUIRED_CASE_IDS
)


def _usage_integer(value):
    if type(value) is not int or value < 0 or value > _MAX_UNSIGNED_64:
        raise BlockedEvidence("invalid_provider_usage")
    return value


def _checked_usage_add(*values):
    total = 0
    for value in values:
        if total > _MAX_UNSIGNED_64 - value:
            raise BlockedEvidence("usage_overflow")
        total += value
    return total


def normalize_usage(provider, usage):
    """Normalize only the two versioned provider usage contracts."""
    required = {
        "openai-responses-usage-v1": (
            "input_tokens", "cached_tokens", "output_tokens", "reasoning_tokens",
        ),
        "anthropic-messages-usage-v1": (
            "input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens",
            "output_tokens",
        ),
    }
    if provider not in required:
        raise BlockedEvidence("unsupported_provider")
    if type(usage) is not dict or set(usage) != set(required[provider]):
        raise BlockedEvidence("missing_provider_usage_field")
    values = {name: _usage_integer(usage[name]) for name in required[provider]}
    if provider == "openai-responses-usage-v1":
        if values["cached_tokens"] > values["input_tokens"] or values["reasoning_tokens"] > values["output_tokens"]:
            raise BlockedEvidence("invalid_provider_subset")
        return NormalizedUsage(
            provider=provider,
            input_tokens=values["input_tokens"],
            cached_input_tokens=values["cached_tokens"],
            output_tokens=values["output_tokens"],
            reasoning_tokens=values["reasoning_tokens"],
            total_parent_model_tokens=_checked_usage_add(values["input_tokens"], values["output_tokens"]),
        )
    cached_input_tokens = _checked_usage_add(
        values["cache_read_input_tokens"], values["cache_creation_input_tokens"],
    )
    return NormalizedUsage(
        provider=provider,
        input_tokens=values["input_tokens"],
        cached_input_tokens=cached_input_tokens,
        output_tokens=values["output_tokens"],
        reasoning_tokens=None,
        total_parent_model_tokens=_checked_usage_add(
            values["input_tokens"], cached_input_tokens, values["output_tokens"],
        ),
    )


def _reduction_ppm(off_total, on_total):
    if type(off_total) is not int or off_total <= 0:
        raise BlockedEvidence("invalid_plugin_off_denominator")
    if type(on_total) is not int or on_total < 0:
        raise BlockedEvidence("invalid_plugin_on_total")
    return ((off_total - on_total) * 1_000_000) // off_total


def _median_ppm(values):
    if not values:
        return None
    ordered = sorted(values)
    count = len(ordered)
    if count % 2:
        return ordered[count // 2]
    return (ordered[count // 2 - 1] + ordered[count // 2]) // 2


_PAIR_IDENTITY_KEYS = (
    "host", "caseID", "workflow", "parentModel", "provider",
    "normalizationVersion", "toolchain", "policyVersion", "commandClass",
)


def _pair_coordinates(arm):
    if type(arm) is not dict:
        return "", ""
    host = arm.get("host") if type(arm.get("host")) is str else ""
    case_id = arm.get("caseID") if type(arm.get("caseID")) is str else ""
    return host, case_id


def _validated_arm(arm):
    if type(arm) is not dict:
        raise BlockedEvidence("invalid_telemetry_arm")
    identity = []
    for key in _PAIR_IDENTITY_KEYS:
        value = arm.get(key)
        if type(value) is not str or not value:
            raise BlockedEvidence("invalid_pair_identity")
        identity.append(value)
    usage = arm.get("usage")
    if type(usage) is not NormalizedUsage or usage.provider != arm["provider"] or arm["normalizationVersion"] != arm["provider"]:
        raise BlockedEvidence("invalid_normalized_usage")
    parent_turns = arm.get("parentTurns")
    if type(parent_turns) is not int or parent_turns < 0:
        raise BlockedEvidence("invalid_parent_turns")
    quality = arm.get("quality")
    if type(quality) is not QualityScore or type(quality.passed) is not bool:
        raise BlockedEvidence("invalid_quality_score")
    role = arm.get("arm")
    if role not in ("pluginOff", "pluginOn"):
        raise BlockedEvidence("invalid_arm_role")
    apple_attempts = arm.get("appleAttempts")
    replacements = arm.get("replacements")
    declines = arm.get("declines")
    fallbacks = arm.get("fallbacks")
    if (
        type(apple_attempts) is not int
        or type(replacements) is not int
        or type(declines) is not int
        or type(fallbacks) is not int
        or not 0 <= apple_attempts <= 1
        or not 0 <= replacements <= 1
        or not 0 <= declines <= 1
        or not 0 <= fallbacks <= 1
        or replacements > apple_attempts
        or (
            role == "pluginOff"
            and any(
                value != 0
                for value in (apple_attempts, replacements, declines, fallbacks)
            )
        )
        or (
            role == "pluginOn"
            and (replacements + fallbacks != 1 or declines > fallbacks)
        )
    ):
        raise BlockedEvidence("invalid_apple_counters")
    if type(quality.reason_codes) is not tuple or any(
        type(reason) is not str or not reason for reason in quality.reason_codes
    ):
        raise BlockedEvidence("invalid_quality_score")
    if quality.passed == bool(quality.reason_codes):
        raise BlockedEvidence("invalid_quality_score")
    return tuple(identity), usage, parent_turns, quality, role


def score_pair(off, on):
    host, case_id = _pair_coordinates(off)
    try:
        off_identity, off_usage, off_turns, off_quality, off_role = _validated_arm(off)
        on_identity, on_usage, on_turns, on_quality, on_role = _validated_arm(on)
    except BlockedEvidence as error:
        return PairScore(host, case_id, "blocked", None, 0, 0, (error.reason,))
    if off_identity != on_identity:
        return PairScore(host, case_id, "blocked", None, 0, 0, ("pair_identity_mismatch",))
    if (off_role, on_role) != ("pluginOff", "pluginOn"):
        return PairScore(host, case_id, "blocked", None, 0, 0, ("pair_role_mismatch",))
    try:
        reduction_ppm = _reduction_ppm(
            off_usage.total_parent_model_tokens, on_usage.total_parent_model_tokens,
        )
    except BlockedEvidence as error:
        return PairScore(host, case_id, "blocked", None, 0, 0, (error.reason,))
    additional_turns = max(on_turns - off_turns, 0)
    if not off_quality.passed or not on_quality.passed:
        return PairScore(
            host, case_id, "fail", reduction_ppm, 1, additional_turns,
            ("correctness_regression",),
        )
    return PairScore(host, case_id, "pass", reduction_ppm, 0, additional_turns, ())


def _validate_pair_score(pair):
    if type(pair) is not PairScore:
        raise ContractError("invalid pair score")
    if type(pair.host) is not str or not pair.host or type(pair.case_id) is not str or not pair.case_id:
        raise ContractError("invalid pair score identity")
    if pair.status not in ("pass", "fail", "blocked"):
        raise ContractError("invalid pair score status")
    if pair.reduction_ppm is not None:
        if (
            type(pair.reduction_ppm) is not int
            or not _MIN_REDUCTION_PPM <= pair.reduction_ppm <= _MAX_REDUCTION_PPM
        ):
            raise ContractError("invalid pair score reduction")
    if pair.status == "blocked":
        if pair.reduction_ppm is not None:
            raise ContractError("invalid blocked pair score")
    elif pair.reduction_ppm is None:
        raise ContractError("invalid scored pair")
    for value in (pair.correctness_regressions, pair.additional_parent_model_turns):
        if type(value) is not int or value < 0:
            raise ContractError("invalid pair score counter")
    if type(pair.reason_codes) is not tuple or any(type(code) is not str or not code for code in pair.reason_codes):
        raise ContractError("invalid pair score reasons")
    if len(set(pair.reason_codes)) != len(pair.reason_codes):
        raise ContractError("duplicate pair score reason")
    if pair.status == "pass" and pair.reason_codes:
        raise ContractError("invalid passing pair score")
    if pair.status != "pass" and not pair.reason_codes:
        raise ContractError("missing pair score reason")
    return pair


def release_gate(pairs):
    if type(pairs) not in (list, tuple):
        raise ContractError("invalid pair scores")
    for pair in pairs:
        _validate_pair_score(pair)
    expected = set(REQUIRED_PAIR_IDENTITIES)
    grouped = {}
    exploratory_pairs = 0
    for pair in pairs:
        identity = (pair.host, pair.case_id)
        if identity in expected:
            grouped.setdefault(identity, []).append(pair)
        else:
            exploratory_pairs += 1

    valid_required_pairs = 0
    blocked_required_pairs = 0
    correctness_regressions = 0
    additional_parent_model_turns = 0
    reductions = []
    reasons = set()
    failed_required_pair = False
    for identity in REQUIRED_PAIR_IDENTITIES:
        entries = grouped.get(identity, ())
        if not entries:
            blocked_required_pairs += 1
            reasons.add("missing_required_pair")
            continue
        if len(entries) != 1:
            failed_required_pair = True
            reasons.add("duplicate_required_pair")
            continue
        pair = entries[0]
        correctness_regressions += pair.correctness_regressions
        additional_parent_model_turns += pair.additional_parent_model_turns
        if pair.status == "blocked":
            blocked_required_pairs += 1
            reasons.add("blocked_required_pair")
            continue
        if pair.status != "pass":
            failed_required_pair = True
            reasons.add("failed_required_pair")
            continue
        valid_required_pairs += 1
        reductions.append(pair.reduction_ppm)

    median_reduction_ppm = _median_ppm(reductions)
    if blocked_required_pairs:
        status = "blocked"
    elif (
        failed_required_pair
        or valid_required_pairs != len(REQUIRED_PAIR_IDENTITIES)
        or median_reduction_ppm is None
        or median_reduction_ppm < 100000
        or correctness_regressions != 0
        or additional_parent_model_turns != 0
    ):
        status = "fail"
    else:
        status = "pass"
    return ReleaseScore(
        status=status,
        valid_required_pairs=valid_required_pairs,
        blocked_required_pairs=blocked_required_pairs,
        median_reduction_ppm=median_reduction_ppm,
        correctness_regressions=correctness_regressions,
        additional_parent_model_turns=additional_parent_model_turns,
        exploratory_pairs=exploratory_pairs,
        reason_codes=tuple(sorted(reasons)),
    )


_lstat = os.lstat
_SHELL_METACHARACTERS = frozenset(";|&<>$`()\\~!{}\x00\r\n")
_SAFE_SELECTOR = re.compile(r"^[A-Za-z0-9 _\-.,=:/\[\]]{1,128}$")
_SAFE_EXPRESSION = re.compile(r"^[A-Za-z0-9 _\-.():]{1,128}$")
_SAFE_GLOB = re.compile(r"^[A-Za-z0-9_.*?\-]{1,128}$")
_PYTHON_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_COMMAND_CLASSES = frozenset(("test", "build", "typecheck", "lint"))
_FIELD_NAMES = frozenset(("severity", "code", "message", "file", "line", "column"))
_SEVERITIES = frozenset(("fatal", "error", "warning", "info"))
_COMMAND_OUTCOMES = frozenset(("success", "failure", "interrupted"))
_FIELD_ORDER = ("severity", "code", "message", "file", "line", "column")
_SENSITIVE_TEXT_PATTERNS = (
    re.compile(r"-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY-----", re.IGNORECASE),
    re.compile(r"/(?:Users|home|private)/[^\s]+", re.IGNORECASE),
    re.compile(r"(?<![:/A-Za-z0-9_])/(?!/)(?:[^/\s]+/)*[^/\s,;]+"),
    re.compile(r"\bfile:(?://)?/[^\s]+", re.IGNORECASE),
    re.compile(r"\b[A-Za-z]:[\\/][^\s]+", re.IGNORECASE),
    re.compile(r"(?:\\\\|//)[A-Za-z0-9_.-]+[\\/][^\s]+"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/-]{8,}", re.IGNORECASE),
    re.compile(
        r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|"
        r"sk-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|"
        r"xox[baprs]-[A-Za-z0-9-]{10,}|AIza[0-9A-Za-z_-]{20,})\b"
    ),
    re.compile(
        r"\b(?:api[_ -]?key|access[_ -]?token|token|password|secret|credential|"
        r"authorization|private[_ -]?key|client[_ -]?secret|signing[_ -]?key)\b"
        r"\s*[:=]\s*(?!<redacted>|\[redacted\]|null\b)[^\s,}]+",
        re.IGNORECASE,
    ),
)
_REASON_CODES = frozenset(
    (
        "tool_not_allowed",
        "command_not_allowed",
        "compound_command",
        "data_policy_denied",
        "input_below_minimum",
        "input_above_maximum",
        "apple_unavailable",
        "locale_unsupported",
        "context_budget_exceeded",
        "generation_declined",
        "cancelled",
        "deadline_exceeded",
        "invalid_response",
        "insufficient_realized_savings",
        "host_replacement_unavailable",
        "host_replacement_failed",
        "contract_invariant_failed",
    )
)


def _closed(value, required):
    if type(value) is not dict or set(value) != set(required):
        raise ContractError("closed schema mismatch")
    return value


def _string(value, label, *, nonempty=True):
    if type(value) is not str or (nonempty and not value):
        raise ContractError(f"invalid {label}")
    return value


def _integer(value, label, *, minimum=None, maximum=None):
    if type(value) is not int:
        raise ContractError(f"invalid {label}")
    if minimum is not None and value < minimum:
        raise ContractError(f"invalid {label}")
    if maximum is not None and value > maximum:
        raise ContractError(f"invalid {label}")
    return value


def _optional_integer(value, label, *, minimum=0, maximum=None):
    if value is None:
        return value
    return _integer(value, label, minimum=minimum, maximum=maximum)


def _finite_number(value, label, *, minimum=None, maximum=None, nullable=False):
    if value is None and nullable:
        return value
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ContractError(f"invalid {label}")
    if minimum is not None and value < minimum:
        raise ContractError(f"invalid {label}")
    if maximum is not None and value > maximum:
        raise ContractError(f"invalid {label}")
    return value


def _digest(value, label):
    if type(value) is not str or not _DIGEST.fullmatch(value):
        raise ContractError(f"invalid {label}")
    return value


def _enum(value, choices, label):
    _string(value, label)
    if value not in choices:
        raise ContractError(f"invalid {label}")
    return value


def _exit_status(exit_status, interrupted):
    if type(interrupted) is not bool:
        raise ContractError("invalid interrupted")
    if exit_status is None:
        if not interrupted:
            raise ContractError("inconsistent interruption and exit status")
        return
    _integer(exit_status, "exitStatus", minimum=0, maximum=255)


def _path(value, label):
    _string(value, label)
    if value.startswith("/") or "\\" in value or "\x00" in value or any(part in ("", ".", "..") for part in value.split("/")):
        raise ContractError(f"invalid {label}")
    return value


def _value_is_safe(value):
    if type(value) is dict:
        return all(_value_is_safe(key) and _value_is_safe(item) for key, item in value.items())
    if type(value) is list:
        return all(_value_is_safe(item) for item in value)
    if type(value) is str:
        return all(pattern.search(value) is None for pattern in _SENSITIVE_TEXT_PATTERNS)
    return value is None or type(value) in (bool, int, float)


def canonical_field_bytes(fields):
    """Encode only allowlisted diagnostic names and values in one canonical form."""
    if type(fields) is not list or not fields:
        raise ContractError("invalid fields")
    names = set()
    content = []
    for field in fields:
        _validate_field(field)
        name = field["name"]
        if name in names:
            raise ContractError("duplicate field name")
        names.add(name)
        if not _value_is_safe(field["value"]):
            raise ContractError("sensitive field value")
        content.append({"name": name, "value": field["value"]})
    content.sort(key=lambda field: _FIELD_ORDER.index(field["name"]))
    try:
        return json.dumps(
            content, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError) as error:
        raise ContractError("invalid canonical fields") from error


def _string_list(value, label):
    if type(value) is not list or not value:
        raise ContractError(f"invalid {label}")
    if any(type(item) is not str or not item for item in value):
        raise ContractError(f"invalid {label}")
    if len(set(value)) != len(value):
        raise ContractError(f"duplicate {label}")
    return value


def _validate_field(field):
    _closed(
        field,
        (
            "name",
            "value",
            "origin",
            "classification",
            "purpose",
            "destination",
            "retention",
            "redacted",
        ),
    )
    name = _string(field["name"], "field name")
    _enum(name, _FIELD_NAMES, "field name")
    _enum(field["origin"], ("trustedLocal",), "field origin")
    _enum(field["classification"], ("C0", "C1"), "field classification")
    _enum(field["purpose"], (Policy.RESULT_TYPE,), "field purpose")
    _enum(field["destination"], ("apple_on_device",), "field destination")
    _enum(field["retention"], ("ephemeral",), "field retention")
    if type(field["redacted"]) is not bool:
        raise ContractError("invalid field redaction")
    if name in ("line", "column"):
        _integer(field["value"], "field value", minimum=1)
    elif name == "file":
        _path(field["value"], "field value")
    else:
        _string(field["value"], "field value")
    return field


def _validate_bindings(value, required):
    _closed(value, required)
    _integer(value["schemaVersion"], "schemaVersion", minimum=Policy.SCHEMA_VERSION, maximum=Policy.SCHEMA_VERSION)
    _enum(value["policyVersion"], (Policy.POLICY_VERSION,), "policyVersion")
    _string(value["callID"], "callID")
    _enum(value["toolName"], (Policy.TOOL_NAME,), "toolName")
    _string(value["toolVersion"], "toolVersion")
    _string(value["stateVersion"], "stateVersion")
    _enum(value["action"], (Policy.ACTION,), "action")
    _enum(value["commandClass"], _COMMAND_CLASSES, "commandClass")
    _string(value["originalResultType"], "originalResultType")
    _digest(value["originalResultDigest"], "originalResultDigest")
    _exit_status(value["exitStatus"], value["interrupted"])
    return value


def validate_request(value):
    required = (
        "schemaVersion", "policyVersion", "callID", "toolName", "toolVersion",
        "stateVersion", "action", "commandClass", "originalResultType",
        "originalResultDigest", "exitStatus", "interrupted", "inputBytes",
        "estimatedSavingsBytes", "fields",
    )
    _validate_bindings(value, required)
    input_bytes = _integer(value["inputBytes"], "inputBytes", minimum=Policy.MINIMUM_INPUT_BYTES, maximum=Policy.MAXIMUM_INPUT_BYTES)
    estimated = _integer(value["estimatedSavingsBytes"], "estimatedSavingsBytes", minimum=Policy.MINIMUM_ESTIMATED_SAVINGS_BYTES)
    if estimated != input_bytes - Policy.MAXIMUM_CONDENSED_BYTES:
        raise ContractError("invalid estimatedSavingsBytes")
    if type(value["fields"]) is not list or not value["fields"]:
        raise ContractError("invalid fields")
    encoded = canonical_field_bytes(value["fields"])
    if len(encoded) != input_bytes:
        raise ContractError("invalid inputBytes")
    return value


def _validate_diagnostic(value):
    _closed(value, ("id", "severity", "code", "message", "file", "line", "column", "failedTestID"))
    _string(value["id"], "diagnostic id")
    _enum(value["severity"], _SEVERITIES, "diagnostic severity")
    _string(value["code"], "diagnostic code", nonempty=False)
    _string(value["message"], "diagnostic message")
    if value["file"] is not None:
        _path(value["file"], "diagnostic file")
    _optional_integer(value["line"], "diagnostic line", minimum=1)
    _optional_integer(value["column"], "diagnostic column", minimum=1)
    if value["failedTestID"] is not None:
        _string(value["failedTestID"], "failed test id")
    return value


def _validate_condensation(value):
    _closed(value, (
        "commandOutcome", "summary", "summaryFacts", "diagnostics", "warningCount",
        "omittedWarningCount", "nextAction", "completionFacts",
    ))
    _enum(value["commandOutcome"], _COMMAND_OUTCOMES, "command outcome")
    _string(value["summary"], "summary")
    _string_list(value["summaryFacts"], "summary facts")
    if type(value["diagnostics"]) is not list:
        raise ContractError("invalid diagnostics")
    identities = set()
    for diagnostic in value["diagnostics"]:
        _validate_diagnostic(diagnostic)
        identity = tuple(
            diagnostic[key]
            for key in ("severity", "code", "message", "file", "line", "column", "failedTestID")
        )
        if identity in identities:
            raise ContractError("duplicate diagnostic identity")
        identities.add(identity)
    _integer(value["warningCount"], "warningCount", minimum=0)
    _integer(value["omittedWarningCount"], "omittedWarningCount", minimum=0, maximum=value["warningCount"])
    warning_representatives = sum(
        diagnostic["severity"] == "warning" for diagnostic in value["diagnostics"]
    )
    if warning_representatives + value["omittedWarningCount"] != value["warningCount"]:
        raise ContractError("invalid warning accounting")
    _string(value["nextAction"], "next action")
    _string_list(value["completionFacts"], "completion facts")
    return value


def validate_result(value):
    bindings = (
        "schemaVersion", "policyVersion", "callID", "toolName", "toolVersion",
        "stateVersion", "action", "commandClass", "originalResultType",
        "originalResultDigest", "outcome", "exitStatus", "interrupted",
    )
    if type(value) is not dict or "outcome" not in value:
        raise ContractError("invalid result outcome")
    _enum(value["outcome"], ("applied", "declined", "fail"), "result outcome")
    if value["outcome"] == "applied":
        _validate_bindings(value, (*bindings, "resultType", "condensation"))
        _enum(value["resultType"], (Policy.RESULT_TYPE,), "resultType")
        _validate_condensation(value["condensation"])
    else:
        _validate_bindings(value, (*bindings, "reasonCode"))
        _enum(value["reasonCode"], _REASON_CODES, "reasonCode")
    return value


def _validate_expected(value):
    _closed(value, (
        "exitStatus", "interrupted", "commandOutcome", "warningCount",
        "warningRepresentativeIDs", "requiredDiagnosticIDs", "failedTestIDs",
        "summary", "summaryFacts", "nextAction", "completionFacts",
    ))
    _exit_status(value["exitStatus"], value["interrupted"])
    _enum(value["commandOutcome"], ("success", "failure"), "expected command outcome")
    if value["interrupted"] or _semantic_command_outcome(value["exitStatus"], False) != value["commandOutcome"]:
        raise ContractError("invalid expected command outcome")
    _integer(value["warningCount"], "warningCount", minimum=0)
    for key in ("warningRepresentativeIDs", "requiredDiagnosticIDs", "failedTestIDs"):
        if type(value[key]) is not list or any(type(item) is not str or not item for item in value[key]):
            raise ContractError(f"invalid {key}")
        if len(set(value[key])) != len(value[key]):
            raise ContractError(f"duplicate {key}")
    if len(value["warningRepresentativeIDs"]) > value["warningCount"]:
        raise ContractError("invalid warning representatives")
    _string(value["summary"], "expected summary")
    _string_list(value["summaryFacts"], "expected summary facts")
    _string(value["nextAction"], "expected next action")
    _string_list(value["completionFacts"], "expected completion facts")
    return value


def _validate_case(value):
    _closed(value, ("id", "commandClass", "commandForm", "classification", "renderedSha256", "expected"))
    _string(value["id"], "case id")
    _enum(value["commandClass"], _COMMAND_CLASSES, "case commandClass")
    _string(value["commandForm"], "commandForm")
    _enum(value["classification"], ("C0", "C1"), "case classification")
    _digest(value["renderedSha256"], "renderedSha256")
    _validate_expected(value["expected"])
    return value


def _validate_arm(value):
    _closed(value, (
        "id", "pairID", "arm", "host", "caseID", "caseRenderedSha256",
        "commandClass", "workflow", "parentModel", "provider",
        "normalizationVersion", "toolchain", "policyVersion", "providerUsage",
        "parentTurns", "appleAttempts", "replacements", "declines", "fallbacks",
        "latencyMilliseconds", "qualityPassed", "qualityReasonCodes",
    ))
    _string(value["id"], "arm id")
    _string(value["pairID"], "pair id")
    _enum(value["arm"], ("pluginOff", "pluginOn"), "arm")
    _enum(value["host"], _REQUIRED_HOSTS, "host")
    _string(value["caseID"], "case id")
    _digest(value["caseRenderedSha256"], "case rendered hash")
    _enum(value["commandClass"], _COMMAND_CLASSES, "commandClass")
    for key in ("workflow", "parentModel", "toolchain"):
        _string(value[key], key)
    _enum(value["provider"], ("openai-responses-usage-v1", "anthropic-messages-usage-v1"), "provider")
    _enum(value["normalizationVersion"], (value["provider"],), "normalizationVersion")
    _enum(value["policyVersion"], (Policy.POLICY_VERSION,), "policyVersion")
    if value["providerUsage"] is not None:
        try:
            normalize_usage(value["provider"], value["providerUsage"])
        except BlockedEvidence as error:
            raise ContractError("invalid provider usage") from error
    for key in ("parentTurns", "latencyMilliseconds"):
        _optional_integer(value[key], key)
    for key in ("declines", "fallbacks"):
        _optional_integer(value[key], key, maximum=1)
    for key in ("appleAttempts", "replacements"):
        if value[key] is not None:
            _integer(value[key], key, minimum=0, maximum=1)
    if value["qualityPassed"] is not None and type(value["qualityPassed"]) is not bool:
        raise ContractError("invalid quality")
    if type(value["qualityReasonCodes"]) is not list or any(
        type(reason) is not str or not reason for reason in value["qualityReasonCodes"]
    ) or len(set(value["qualityReasonCodes"])) != len(value["qualityReasonCodes"]):
        raise ContractError("invalid quality reasons")
    if value["qualityPassed"] is True and value["qualityReasonCodes"]:
        raise ContractError("passing quality has reasons")
    if value["qualityPassed"] is False and not value["qualityReasonCodes"]:
        raise ContractError("failing quality lacks reasons")
    if value["arm"] == "pluginOff" and any(
        value[key] not in (None, 0)
        for key in ("appleAttempts", "replacements", "declines", "fallbacks")
    ):
        raise ContractError("pluginOff cannot use the plugin route")
    if value["appleAttempts"] is not None and value["replacements"] is not None and value["replacements"] > value["appleAttempts"]:
        raise ContractError("replacement exceeds attempt")
    if value["replacements"] == 1 and value["fallbacks"] == 1:
        raise ContractError("replacement and fallback are exclusive")
    if value["replacements"] == 1 and value["declines"] == 1:
        raise ContractError("replacement and decline are exclusive")
    if value["declines"] == 1 and value["fallbacks"] == 0:
        raise ContractError("decline requires fallback")
    route_counters = tuple(
        value[key]
        for key in ("appleAttempts", "replacements", "declines", "fallbacks")
    )
    if (
        value["arm"] == "pluginOn"
        and all(counter is not None for counter in route_counters)
        and value["replacements"] + value["fallbacks"] != 1
    ):
        raise ContractError("pluginOn terminal outcome missing")
    return value


def _validate_pair(value):
    _closed(value, (
        "id", "host", "caseID", "status", "reductionPPM",
        "correctnessRegressions", "additionalParentModelTurns", "reasonCodes",
    ))
    _string(value["id"], "pair id")
    _enum(value["host"], _REQUIRED_HOSTS, "host")
    _string(value["caseID"], "case id")
    _enum(value["status"], ("pass", "fail", "blocked"), "pair status")
    if value["reductionPPM"] is not None:
        _integer(value["reductionPPM"], "reductionPPM", minimum=_MIN_REDUCTION_PPM, maximum=_MAX_REDUCTION_PPM)
    if value["status"] == "blocked" and value["reductionPPM"] is not None:
        raise ContractError("blocked pair has reduction")
    if value["status"] != "blocked" and value["reductionPPM"] is None:
        raise ContractError("scored pair lacks reduction")
    for key in ("correctnessRegressions", "additionalParentModelTurns"):
        _integer(value[key], key, minimum=0)
    if type(value["reasonCodes"]) is not list or any(
        type(reason) is not str or not reason for reason in value["reasonCodes"]
    ) or len(set(value["reasonCodes"])) != len(value["reasonCodes"]):
        raise ContractError("invalid pair reasons")
    if value["status"] == "pass" and value["reasonCodes"]:
        raise ContractError("passing pair has reasons")
    if value["status"] != "pass" and not value["reasonCodes"]:
        raise ContractError("non-passing pair lacks reasons")
    return value


def _validate_release(value):
    _closed(value, (
        "status", "validRequiredPairs", "blockedRequiredPairs", "medianReductionPPM",
        "correctnessRegressions", "additionalParentModelTurns", "exploratoryPairs",
        "reasonCodes",
    ))
    _enum(value["status"], ("pass", "fail", "blocked"), "release status")
    for key in ("validRequiredPairs", "blockedRequiredPairs", "correctnessRegressions", "additionalParentModelTurns", "exploratoryPairs"):
        _integer(value[key], key, minimum=0)
    if value["medianReductionPPM"] is not None:
        _integer(value["medianReductionPPM"], "medianReductionPPM", minimum=_MIN_REDUCTION_PPM, maximum=_MAX_REDUCTION_PPM)
    if type(value["reasonCodes"]) is not list or any(
        type(reason) is not str or not reason for reason in value["reasonCodes"]
    ) or len(set(value["reasonCodes"])) != len(value["reasonCodes"]):
        raise ContractError("invalid release reasons")
    return value


def validate_benchmark(value):
    if type(value) is not dict or "kind" not in value:
        raise ContractError("invalid benchmark kind")
    _enum(value["kind"], ("corpus", "evidence"), "benchmark kind")
    if value["kind"] == "corpus":
        _closed(value, ("schemaVersion", "policyVersion", "kind", "corpusVersion", "corpusSha256", "cases"))
        _integer(value["schemaVersion"], "schemaVersion", minimum=Policy.SCHEMA_VERSION, maximum=Policy.SCHEMA_VERSION)
        _enum(value["policyVersion"], (Policy.POLICY_VERSION,), "policyVersion")
        _string(value["corpusVersion"], "corpusVersion")
        _digest(value["corpusSha256"], "corpusSha256")
        if type(value["cases"]) is not list or not value["cases"]:
            raise ContractError("invalid cases")
        ids = set()
        for case in value["cases"]:
            _validate_case(case)
            if case["id"] in ids:
                raise ContractError("duplicate case id")
            ids.add(case["id"])
        _validate_corpus_invariants(value)
    else:
        _closed(value, ("schemaVersion", "policyVersion", "kind", "corpusSha256", "arms", "pairs", "release"))
        _integer(value["schemaVersion"], "schemaVersion", minimum=Policy.SCHEMA_VERSION, maximum=Policy.SCHEMA_VERSION)
        _enum(value["policyVersion"], (Policy.POLICY_VERSION,), "policyVersion")
        _digest(value["corpusSha256"], "corpusSha256")
        if type(value["arms"]) is not list or type(value["pairs"]) is not list:
            raise ContractError("invalid benchmark collections")
        arm_ids = set()
        for arm in value["arms"]:
            _validate_arm(arm)
            if arm["id"] in arm_ids:
                raise ContractError("duplicate arm id")
            arm_ids.add(arm["id"])
        pair_ids = set()
        for pair in value["pairs"]:
            _validate_pair(pair)
            if pair["id"] in pair_ids:
                raise ContractError("duplicate pair id")
            pair_ids.add(pair["id"])
        _validate_release(value["release"])
        derived = derive_benchmark(value)
        if value["pairs"] != derived["pairs"] or value["release"] != derived["release"]:
            raise ContractError("serialized benchmark aggregates are not derived")
    return value


def _serialized_pair_dict(score):
    return {
        "id": f"{score.host}:{score.case_id}",
        "host": score.host,
        "caseID": score.case_id,
        "status": score.status,
        "reductionPPM": score.reduction_ppm,
        "correctnessRegressions": score.correctness_regressions,
        "additionalParentModelTurns": score.additional_parent_model_turns,
        "reasonCodes": list(score.reason_codes),
    }


def _serialized_release_dict(score):
    return {
        "status": score.status,
        "validRequiredPairs": score.valid_required_pairs,
        "blockedRequiredPairs": score.blocked_required_pairs,
        "medianReductionPPM": score.median_reduction_ppm,
        "correctnessRegressions": score.correctness_regressions,
        "additionalParentModelTurns": score.additional_parent_model_turns,
        "exploratoryPairs": score.exploratory_pairs,
        "reasonCodes": list(score.reason_codes),
    }


def _serialized_arm_for_scoring(arm):
    required = (
        arm["providerUsage"], arm["parentTurns"], arm["appleAttempts"],
        arm["replacements"], arm["declines"], arm["fallbacks"],
        arm["latencyMilliseconds"], arm["qualityPassed"],
    )
    if any(value is None for value in required):
        raise BlockedEvidence("missing_required_telemetry")
    usage = normalize_usage(arm["provider"], arm["providerUsage"])
    return {
        "host": arm["host"],
        "caseID": arm["caseID"],
        "workflow": arm["workflow"],
        "parentModel": arm["parentModel"],
        "provider": arm["provider"],
        "normalizationVersion": arm["normalizationVersion"],
        "toolchain": arm["toolchain"],
        "policyVersion": arm["policyVersion"],
        "commandClass": arm["commandClass"],
        "arm": arm["arm"],
        "usage": usage,
        "parentTurns": arm["parentTurns"],
        "appleAttempts": arm["appleAttempts"],
        "replacements": arm["replacements"],
        "declines": arm["declines"],
        "fallbacks": arm["fallbacks"],
        "quality": QualityScore(
            arm["qualityPassed"], tuple(arm["qualityReasonCodes"])
        ),
    }


def _score_serialized_pair(off, on):
    host, case_id = off["host"], off["caseID"]
    try:
        return score_pair(
            _serialized_arm_for_scoring(off), _serialized_arm_for_scoring(on)
        )
    except BlockedEvidence as error:
        return PairScore(host, case_id, "blocked", None, 0, 0, (error.reason,))


def derive_benchmark(value):
    """Derive every pair and release aggregate from the exact serialized arms."""
    if type(value) is not dict:
        raise ContractError("invalid benchmark evidence")
    _closed(value, ("schemaVersion", "policyVersion", "kind", "corpusSha256", "arms", "pairs", "release"))
    _integer(value["schemaVersion"], "schemaVersion", minimum=Policy.SCHEMA_VERSION, maximum=Policy.SCHEMA_VERSION)
    _enum(value["policyVersion"], (Policy.POLICY_VERSION,), "policyVersion")
    _enum(value["kind"], ("evidence",), "benchmark kind")
    _digest(value["corpusSha256"], "corpusSha256")
    if type(value["arms"]) is not list or len(value["arms"]) != 96:
        raise ContractError("invalid required arm count")
    corpus = load_closed_json(Path(__file__).with_name("benchmark-corpus.json"))
    _closed(corpus, ("schemaVersion", "policyVersion", "kind", "corpusVersion", "corpusSha256", "cases"))
    if value["corpusSha256"] != corpus["corpusSha256"]:
        raise ContractError("benchmark corpus mismatch")
    cases = {case["id"]: case for case in corpus["cases"]}
    if set(cases) != set(_REQUIRED_CASE_IDS):
        raise ContractError("benchmark case identity mismatch")
    grouped = {}
    arm_ids = set()
    for arm in value["arms"]:
        _validate_arm(arm)
        if arm["id"] in arm_ids:
            raise ContractError("duplicate arm id")
        arm_ids.add(arm["id"])
        identity = (arm["host"], arm["caseID"])
        if identity not in REQUIRED_PAIR_IDENTITIES:
            raise ContractError("unexpected required arm")
        case = cases[arm["caseID"]]
        pair_id = f"{arm['host']}:{arm['caseID']}"
        if (
            arm["pairID"] != pair_id
            or arm["id"] != f"{pair_id}:{arm['arm']}"
            or arm["caseRenderedSha256"] != case["renderedSha256"]
            or arm["commandClass"] != case["commandClass"]
        ):
            raise ContractError("unbound benchmark arm")
        grouped.setdefault(identity, {})[arm["arm"]] = arm
    scores = []
    for identity in REQUIRED_PAIR_IDENTITIES:
        roles = grouped.get(identity, {})
        if set(roles) != {"pluginOff", "pluginOn"}:
            raise ContractError("incomplete benchmark pair roles")
        scores.append(_score_serialized_pair(roles["pluginOff"], roles["pluginOn"]))
    if len(grouped) != 48:
        raise ContractError("invalid required pair count")
    release = release_gate(scores)
    derived = deepcopy(value)
    derived["pairs"] = [_serialized_pair_dict(score) for score in scores]
    derived["release"] = _serialized_release_dict(release)
    return derived


def _validate_corpus_invariants(corpus):
    cases = corpus["cases"]
    if len(cases) != 24:
        raise ContractError("invalid corpus case count")
    counts = {command_class: 0 for command_class in _COMMAND_CLASSES}
    forms = {command_form: [] for command_form in Policy.APPROVED_BENCHMARK_COMMAND_FORMS}
    for case in cases:
        counts[case["commandClass"]] += 1
        if case["commandForm"] not in forms:
            raise ContractError("invalid corpus command form")
        forms[case["commandForm"]].append(case)
        rendered = render_case(case)
        if not Policy.MINIMUM_INPUT_BYTES <= len(rendered) <= Policy.MAXIMUM_INPUT_BYTES:
            raise ContractError("invalid rendered case size")
        if hashlib.sha256(rendered).hexdigest() != case["renderedSha256"]:
            raise ContractError("invalid rendered case hash")
    if counts != {command_class: 6 for command_class in _COMMAND_CLASSES}:
        raise ContractError("invalid corpus command class balance")
    for form_cases in forms.values():
        if len(form_cases) != 2:
            raise ContractError("invalid corpus command form balance")
        successes = sum(case["expected"]["exitStatus"] == 0 for case in form_cases)
        if successes != 1:
            raise ContractError("invalid corpus command outcome balance")
    if corpus_digest(corpus) != corpus["corpusSha256"]:
        raise ContractError("invalid corpus hash")


_SYNTHETIC_NOISE_LINE = "synthetic-noise|unicode=\u00e9\u6f22\U0001f642|classification={classification}|case={case_id}|repeat={repeat}\n"


def _case_ordinal(case):
    try:
        return int(case["id"].rsplit("-", 1)[1])
    except (KeyError, TypeError, ValueError, IndexError) as error:
        raise ContractError("invalid case id") from error


def _diagnostic_for_case(case, diagnostic_id):
    try:
        severity, ordinal = diagnostic_id.split("-", 1)
        index = int(ordinal)
    except (AttributeError, ValueError) as error:
        raise ContractError("invalid diagnostic id") from error
    if severity not in ("fatal", "error", "warning") or index < 1:
        raise ContractError("invalid diagnostic id")
    failed_ids = case["expected"]["failedTestIDs"]
    return {
        "id": diagnostic_id,
        "severity": severity,
        "code": f"{case['commandClass'].upper()}-{index:03d}",
        "message": f"synthetic {case['commandForm']} {severity} diagnostic",
        "file": f"Sources/{case['commandClass'].title()}Case{index}.swift",
        "line": 100 + index,
        "column": 1 + index,
        "failedTestID": failed_ids[0] if failed_ids else None,
    }


def _case_summary(case):
    return case["expected"]["summary"]


def _noise_repeat(case):
    return 176 + _case_ordinal(case) * 3


def render_case(case):
    """Render one reviewed synthetic case with stable UTF-8 bytes."""
    _validate_case(case)
    expected = case["expected"]
    lines = (
        ("case-id", case["id"]),
        ("command-class", case["commandClass"]),
        ("command-form", case["commandForm"]),
        ("classification", case["classification"]),
        ("exit-status", "interrupted" if expected["exitStatus"] is None else str(expected["exitStatus"])),
        ("interrupted", str(expected["interrupted"]).lower()),
        ("warning-count", str(expected["warningCount"])),
        ("command-outcome", expected["commandOutcome"]),
        ("summary", _case_summary(case)),
        ("summary-facts", "|".join(expected["summaryFacts"])),
        ("next-action", expected["nextAction"]),
        ("completion-facts", "|".join(expected["completionFacts"])),
    )
    rendered = [f"{key}: {value}\n" for key, value in lines]
    for diagnostic_id in expected["requiredDiagnosticIDs"]:
        diagnostic = _diagnostic_for_case(case, diagnostic_id)
        rendered.append(
            "diagnostic: " + json.dumps(
                diagnostic, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ) + "\n"
        )
    for diagnostic_id in expected["warningRepresentativeIDs"]:
        diagnostic = _diagnostic_for_case(case, diagnostic_id)
        rendered.append(
            "warning-representative: " + json.dumps(
                diagnostic, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ) + "\n"
        )
    for failed_test_id in expected["failedTestIDs"]:
        rendered.append(f"failed-test: {failed_test_id}\n")
    noise = _SYNTHETIC_NOISE_LINE.format(
        classification=case["classification"], case_id=case["id"], repeat=_noise_repeat(case)
    )
    rendered.extend(noise for _ in range(_noise_repeat(case)))
    return "".join(rendered).encode("utf-8")


def corpus_digest(corpus):
    """Hash the canonical corpus representation without its self-binding field."""
    if type(corpus) is not dict:
        raise ContractError("invalid corpus")
    bound = {key: value for key, value in corpus.items() if key != "corpusSha256"}
    try:
        canonical = json.dumps(bound, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError) as error:
        raise ContractError("invalid corpus") from error
    return hashlib.sha256(canonical).hexdigest()


def _diagnostic_identity(diagnostic):
    if type(diagnostic) is not dict:
        return None
    keys = ("id", "severity", "code", "message", "file", "line", "column", "failedTestID")
    if set(diagnostic) != set(keys):
        return None
    return tuple(diagnostic[key] for key in keys)


def _required_identities(case):
    return frozenset(_diagnostic_identity(_diagnostic_for_case(case, diagnostic_id)) for diagnostic_id in case["expected"]["requiredDiagnosticIDs"])


def _warning_identities(case):
    return frozenset(
        _diagnostic_identity(_diagnostic_for_case(case, diagnostic_id))
        for diagnostic_id in case["expected"]["warningRepresentativeIDs"]
    )


def _diagnostic_identities(result):
    try:
        diagnostics = result["condensation"]["diagnostics"]
    except (KeyError, TypeError):
        return None
    if type(diagnostics) is not list:
        return None
    identities = [_diagnostic_identity(diagnostic) for diagnostic in diagnostics]
    try:
        duplicate = len(set(identities)) != len(identities)
    except TypeError:
        return None
    if any(identity is None for identity in identities) or duplicate:
        return None
    return frozenset(identities)


def _semantic_command_outcome(exit_status, interrupted):
    if interrupted:
        return "interrupted"
    return "success" if exit_status == 0 else "failure"


def score_condensation(case, result):
    """Score a normalized condensation against its immutable synthetic case."""
    _validate_case(case)
    if hashlib.sha256(render_case(case)).hexdigest() != case["renderedSha256"]:
        raise ContractError("stale case oracle hash")
    reasons = []
    try:
        validate_result(result)
    except ContractError:
        reasons.append("invalid_result")
    if type(result) is not dict or any(
        key not in result for key in ("exitStatus", "interrupted", "outcome", "commandClass")
    ):
        return QualityScore(False, tuple(sorted(set(reasons + ["invalid_result"]))))
    raw_condensation = result.get("condensation")
    if raw_condensation is None and result.get("outcome") != "applied":
        condensation = {}
    elif type(raw_condensation) is dict:
        condensation = raw_condensation
    else:
        return QualityScore(False, tuple(sorted(set(reasons + ["invalid_result"]))))
    expected = case["expected"]
    if result["exitStatus"] != expected["exitStatus"]:
        reasons.append("exit_status_regression")
    if result["interrupted"] != expected["interrupted"]:
        reasons.append("interruption_regression")
    if (
        result["outcome"] != "applied"
        or result["commandClass"] != case["commandClass"]
        or _semantic_command_outcome(result["exitStatus"], result["interrupted"])
        != _semantic_command_outcome(expected["exitStatus"], expected["interrupted"])
        or condensation.get("commandOutcome") != expected["commandOutcome"]
    ):
        reasons.append("command_outcome_regression")
    observed = _diagnostic_identities(result)
    required = _required_identities(case)
    warnings = _warning_identities(case)
    if observed is None:
        reasons.extend(("diagnostic_omission", "diagnostic_invention"))
    else:
        observed_required = frozenset(identity for identity in observed if identity[1] in ("fatal", "error"))
        observed_warnings = frozenset(identity for identity in observed if identity[1] == "warning")
        if required - observed_required:
            reasons.append("diagnostic_omission")
        if observed_required - required:
            reasons.append("diagnostic_invention")
        if warnings - observed_warnings:
            reasons.append("warning_omission")
        if observed_warnings - warnings:
            reasons.append("warning_invention")
        if any(identity[1] == "info" for identity in observed):
            reasons.append("diagnostic_invention")
    if condensation.get("summary") != expected["summary"]:
        reasons.extend(("summary_omission", "summary_invention"))
    for field, omission, invention in (
        ("summaryFacts", "summary_fact_omission", "summary_fact_invention"),
        ("completionFacts", "completion_fact_omission", "completion_fact_invention"),
    ):
        observed_facts = condensation.get(field)
        expected_facts = expected[field]
        if type(observed_facts) is list and all(
            type(fact) is str for fact in observed_facts
        ):
            if set(expected_facts) - set(observed_facts):
                reasons.append(omission)
            if set(observed_facts) - set(expected_facts):
                reasons.append(invention)
        else:
            reasons.extend((omission, invention))
    if condensation.get("nextAction") != expected["nextAction"]:
        reasons.extend(("next_action_omission", "next_action_invention"))
    if (
        condensation.get("warningCount") != expected["warningCount"]
        or condensation.get("omittedWarningCount")
        != expected["warningCount"] - len(expected["warningRepresentativeIDs"])
    ):
        reasons.append("warning_count_regression")
    try:
        encoded = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError):
        reasons.append("invented_fact")
        encoded = b""
    if len(encoded) > Policy.MAXIMUM_CONDENSED_BYTES:
        reasons.append("condensed_output_too_large")
    return QualityScore(not reasons, tuple(sorted(set(reasons))))


def benchmark_boundaries():
    """Return fixed ineligible/boundary rows, deliberately separate from corpus cases."""
    return (
        {"id": "below-input-minimum", "inputBytes": 8191, "outputBytes": 4096, "realizedSavingsBytes": 4095, "occupiedTokens": 6144, "contextSize": 8192, "exitStatus": 1, "interrupted": False},
        {"id": "minimum-input", "inputBytes": 8192, "outputBytes": 4096, "realizedSavingsBytes": 4096, "occupiedTokens": 6144, "contextSize": 8192, "exitStatus": 1, "interrupted": False},
        {"id": "maximum-input", "inputBytes": 65536, "outputBytes": 4096, "realizedSavingsBytes": 61440, "occupiedTokens": 6144, "contextSize": 8192, "exitStatus": 1, "interrupted": False},
        {"id": "above-input-maximum", "inputBytes": 65537, "outputBytes": 4097, "realizedSavingsBytes": 61440, "occupiedTokens": 6145, "contextSize": 8192, "exitStatus": 1, "interrupted": False},
        {"id": "above-output-maximum", "inputBytes": 8192, "outputBytes": 4097, "realizedSavingsBytes": 4095, "occupiedTokens": 6145, "contextSize": 8192, "exitStatus": 1, "interrupted": False},
        {"id": "interrupted-command", "inputBytes": 8192, "outputBytes": 4096, "realizedSavingsBytes": 4096, "occupiedTokens": 6144, "contextSize": 8192, "exitStatus": None, "interrupted": True},
    )


def _reject_non_finite(value):
    if type(value) is float and not math.isfinite(value):
        raise ContractError("non-finite JSON number")
    if type(value) is list:
        for item in value:
            _reject_non_finite(item)
    elif type(value) is dict:
        for item in value.values():
            _reject_non_finite(item)


def load_closed_json(path):
    def no_duplicates(pairs):
        result = {}
        for key, item in pairs:
            if key in result:
                raise ContractError("duplicate JSON key")
            result[key] = item
        return result

    def reject_constant(_constant):
        raise ContractError("non-finite JSON number")

    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=no_duplicates, parse_constant=reject_constant)
    except ContractError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ContractError("invalid JSON") from error
    _reject_non_finite(value)
    return value


def _require_int(value, minimum):
    if type(value) is not int or value < minimum:
        raise ContractError("invalid integer")
    return value


def estimate_savings(input_bytes):
    _require_int(input_bytes, 0)
    if input_bytes < Policy.MINIMUM_INPUT_BYTES:
        raise RouteDeclined("input_below_minimum")
    if input_bytes > Policy.MAXIMUM_INPUT_BYTES:
        raise RouteDeclined("input_above_maximum")
    return input_bytes - Policy.MAXIMUM_CONDENSED_BYTES


def fits_apple_budget(occupied_tokens, context_size):
    _require_int(occupied_tokens, 0)
    _require_int(context_size, 1)
    return (
        occupied_tokens * Policy.MAXIMUM_APPLE_CONTEXT_DENOMINATOR
        <= context_size * Policy.MAXIMUM_APPLE_CONTEXT_NUMERATOR
    )


def _identity(path):
    try:
        record = _lstat(path)
    except (OSError, RuntimeError, ValueError) as error:
        raise RouteDeclined("command_not_allowed") from error
    return record.st_dev, record.st_ino, record.st_mode


def _recheck_snapshot(snapshot):
    for path, identity in snapshot:
        if _identity(path) != identity:
            raise RouteDeclined("command_not_allowed")


def _recheck_absence(paths):
    for path in paths:
        try:
            _lstat(path)
        except (FileNotFoundError, NotADirectoryError):
            continue
        except (OSError, RuntimeError, ValueError) as error:
            raise RouteDeclined("command_not_allowed") from error
        raise RouteDeclined("command_not_allowed")


def _capture_chain(path):
    path = Path(path)
    chain = tuple(reversed((path, *path.parents)))
    snapshot = []
    for member in chain:
        identity = _identity(member)
        if stat.S_ISLNK(identity[2]):
            raise RouteDeclined("command_not_allowed")
        snapshot.append((member, identity))
    return tuple(snapshot)


def _contained(candidate, root):
    try:
        candidate.relative_to(root)
    except ValueError as error:
        raise RouteDeclined("command_not_allowed") from error


def _repository_root(repo_root):
    if not isinstance(repo_root, (str, Path)):
        raise RouteDeclined("command_not_allowed")
    try:
        root = Path(os.path.abspath(os.fspath(repo_root)))
        root_identity = _identity(root)
        if stat.S_ISLNK(root_identity[2]) or not stat.S_ISDIR(root_identity[2]):
            raise RouteDeclined("command_not_allowed")
        resolved = root.resolve(strict=False)
        snapshot = _capture_chain(resolved)
    except (OSError, RuntimeError, ValueError) as error:
        raise RouteDeclined("command_not_allowed") from error
    if _identity(root) != root_identity:
        raise RouteDeclined("command_not_allowed")
    _recheck_snapshot(snapshot)
    return resolved, snapshot


def _path_value(token):
    if (
        type(token) is not str
        or not token
        or token.startswith(("/", "-"))
        or "\\" in token
    ):
        raise RouteDeclined("command_not_allowed")
    if any(part in ("", ".", "..") for part in token.split("/")):
        raise RouteDeclined("command_not_allowed")
    return token


def _nearest_existing_snapshot(candidate, root):
    _contained(candidate, root)
    current = candidate
    missing = []
    while True:
        try:
            identity = _identity(current)
            break
        except RouteDeclined as error:
            cause = error.__cause__
            if not isinstance(cause, (FileNotFoundError, NotADirectoryError)):
                raise
            missing.append(current)
            if current == root:
                raise
            current = current.parent
    if stat.S_ISLNK(identity[2]):
        raise RouteDeclined("command_not_allowed")
    relative_parts = current.relative_to(root).parts
    existing_chain = [root]
    for index in range(len(relative_parts)):
        existing_chain.append(root.joinpath(*relative_parts[: index + 1]))
    snapshot = []
    for member in existing_chain:
        member_identity = identity if member == current else _identity(member)
        if stat.S_ISLNK(member_identity[2]):
            raise RouteDeclined("command_not_allowed")
        snapshot.append((member, member_identity))
    try:
        resolved_parent = current.resolve(strict=False)
    except (OSError, RuntimeError, ValueError) as error:
        raise RouteDeclined("command_not_allowed") from error
    _contained(resolved_parent, root)
    _recheck_snapshot(snapshot)
    _recheck_absence(missing)
    return current, tuple(snapshot), tuple(missing)


def _resolve_repo_path(
    token, root, *, directory=False, suffix=None, regular=False,
    snapshot_sink=None,
):
    token = _path_value(token)
    candidate = root / token
    existing, snapshot, missing = _nearest_existing_snapshot(candidate, root)
    exists = not missing
    if not exists and not directory:
        raise RouteDeclined("command_not_allowed")
    if exists:
        first = snapshot[-1][1]
        try:
            resolved = candidate.resolve(strict=False)
        except (OSError, RuntimeError, ValueError) as error:
            raise RouteDeclined("command_not_allowed") from error
        _contained(resolved, root)
        if directory and not stat.S_ISDIR(first[2]):
            raise RouteDeclined("command_not_allowed")
        if regular and not stat.S_ISREG(first[2]):
            raise RouteDeclined("command_not_allowed")
    elif existing == candidate:
        raise RouteDeclined("command_not_allowed")
    if suffix is not None and not token.endswith(suffix):
        raise RouteDeclined("command_not_allowed")
    _recheck_snapshot(snapshot)
    _recheck_absence(missing)
    if snapshot_sink is not None:
        snapshot_sink.append((snapshot, missing))
    return token


def _safe_selector(value):
    if not _SAFE_SELECTOR.fullmatch(value) or value[0] == " " or value[-1] == " ":
        raise RouteDeclined("command_not_allowed")


def _safe_expression(value):
    if not _SAFE_EXPRESSION.fullmatch(value) or value[0] == " " or value[-1] == " ":
        raise RouteDeclined("command_not_allowed")
    depth = 0
    for character in value:
        if character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
            if depth < 0:
                raise RouteDeclined("command_not_allowed")
    if depth:
        raise RouteDeclined("command_not_allowed")


def _take_pairs(tokens, allowed, root, *, values=None, snapshot_sink=None):
    seen = set()
    index = 0
    while index < len(tokens):
        option = tokens[index]
        if option not in allowed or option in seen or index + 1 >= len(tokens):
            raise RouteDeclined("command_not_allowed")
        seen.add(option)
        value = tokens[index + 1]
        validator = allowed[option]
        if validator == "directory":
            _resolve_repo_path(
                value, root, directory=True, snapshot_sink=snapshot_sink
            )
        elif validator == "configuration":
            if value not in values:
                raise RouteDeclined("command_not_allowed")
        elif validator == "selector":
            _safe_selector(value)
        elif validator == "glob":
            if not _SAFE_GLOB.fullmatch(value):
                raise RouteDeclined("command_not_allowed")
        index += 2


def _swift_suffix(tokens, root, snapshot_sink, *, build=False):
    allowed = {"--configuration": "configuration", "--package-path": "directory", "--scratch-path": "directory"}
    if not build:
        allowed["--filter"] = "selector"
    _take_pairs(
        tokens, allowed, root, values=frozenset(("debug", "release")),
        snapshot_sink=snapshot_sink,
    )


def _swiftc_suffix(tokens, root, snapshot_sink):
    if not tokens:
        raise RouteDeclined("command_not_allowed")
    for token in tokens:
        _resolve_repo_path(
            token, root, suffix=".swift", regular=True,
            snapshot_sink=snapshot_sink,
        )


def _swift_format_suffix(tokens, root, snapshot_sink):
    if tokens and tokens[0] == "--recursive":
        tokens.pop(0)
    if tokens and tokens[0] == "--strict":
        tokens.pop(0)
    if not tokens:
        raise RouteDeclined("command_not_allowed")
    for token in tokens:
        _resolve_repo_path(token, root, snapshot_sink=snapshot_sink)


def _xcodebuild_suffix(tokens, root, snapshot_sink):
    paired = {
        "-project": "project", "-workspace": "workspace", "-scheme": "selector",
        "-configuration": "configuration", "-sdk": "selector", "-destination": "selector",
        "-derivedDataPath": "directory",
    }
    seen = set()
    index = 0
    while index < len(tokens):
        option = tokens[index]
        if option == "-quiet":
            if option in seen:
                raise RouteDeclined("command_not_allowed")
            seen.add(option)
            index += 1
            continue
        if option not in paired or option in seen or index + 1 >= len(tokens):
            raise RouteDeclined("command_not_allowed")
        seen.add(option)
        value = tokens[index + 1]
        kind = paired[option]
        if kind == "project":
            _resolve_repo_path(
                value, root, suffix=".xcodeproj", directory=True,
                snapshot_sink=snapshot_sink,
            )
        elif kind == "workspace":
            _resolve_repo_path(
                value, root, suffix=".xcworkspace", directory=True,
                snapshot_sink=snapshot_sink,
            )
        elif kind == "configuration":
            if value not in ("Debug", "Release"):
                raise RouteDeclined("command_not_allowed")
        elif kind == "directory":
            _resolve_repo_path(
                value, root, directory=True, snapshot_sink=snapshot_sink
            )
        else:
            _safe_selector(value)
        index += 2
    if "-project" in seen and "-workspace" in seen:
        raise RouteDeclined("command_not_allowed")


def _unittest_suffix(tokens, root, snapshot_sink):
    if tokens and tokens[0] in ("-v", "-q"):
        tokens.pop(0)
    if not tokens:
        return
    if tokens[0] != "discover":
        for identifier in tokens:
            if not all(_PYTHON_IDENTIFIER.fullmatch(part) for part in identifier.split(".")):
                raise RouteDeclined("command_not_allowed")
        return
    tokens.pop(0)
    _take_pairs(
        tokens, {"-s": "directory", "-p": "glob", "-t": "directory"},
        root, snapshot_sink=snapshot_sink,
    )


def _pytest_suffix(tokens, root, snapshot_sink):
    seen = set()
    operands = False
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token in ("-q", "-v", "-x"):
            if operands or token in seen:
                raise RouteDeclined("command_not_allowed")
            seen.add(token)
        elif token.startswith("--maxfail="):
            if operands or "--maxfail" in seen or not token.removeprefix("--maxfail=").isdigit() or int(token.removeprefix("--maxfail=")) < 1:
                raise RouteDeclined("command_not_allowed")
            seen.add("--maxfail")
        elif token in ("-k", "-m"):
            if operands or token in seen or index + 1 >= len(tokens):
                raise RouteDeclined("command_not_allowed")
            seen.add(token)
            _safe_expression(tokens[index + 1])
            index += 1
        else:
            operands = True
            path, separator, selector = token.partition("::")
            _resolve_repo_path(path, root, snapshot_sink=snapshot_sink)
            if separator and (not selector or any(not _PYTHON_IDENTIFIER.fullmatch(part) for part in selector.split("::"))):
                raise RouteDeclined("command_not_allowed")
        index += 1


def _build_suffix(tokens, _root, _snapshot_sink):
    if len(tokens) > 2 or len(set(tokens)) != len(tokens) or any(token not in ("--sdist", "--wheel") for token in tokens):
        raise RouteDeclined("command_not_allowed")


def _mypy_suffix(tokens, root, snapshot_sink):
    if tokens and tokens[0] == "--strict":
        tokens.pop(0)
    if tokens and tokens[0] == "--no-incremental":
        tokens.pop(0)
    if not tokens:
        raise RouteDeclined("command_not_allowed")
    for token in tokens:
        _resolve_repo_path(token, root, snapshot_sink=snapshot_sink)


def _ruff_suffix(tokens, root, snapshot_sink):
    seen = set()
    if tokens and tokens[0] == "--no-fix":
        seen.add(tokens.pop(0))
    if tokens and tokens[0] == "--output-format":
        tokens.pop(0)
        if not tokens or tokens[0] not in ("concise", "full"):
            raise RouteDeclined("command_not_allowed")
        seen.add("--output-format")
        tokens.pop(0)
    if not tokens:
        raise RouteDeclined("command_not_allowed")
    for token in tokens:
        _resolve_repo_path(token, root, snapshot_sink=snapshot_sink)


_COMMAND_PREFIXES = (
    (("python3", "-m", "ruff", "check"), "lint", _ruff_suffix),
    (("python3", "-m", "unittest"), "test", _unittest_suffix),
    (("python3", "-m", "pytest"), "test", _pytest_suffix),
    (("python3", "-m", "build"), "build", _build_suffix),
    (("python3", "-m", "mypy"), "typecheck", _mypy_suffix),
    (("swift", "format", "lint"), "lint", _swift_format_suffix),
    (("swiftc", "-typecheck"), "typecheck", _swiftc_suffix),
    (("xcodebuild", "test"), "test", _xcodebuild_suffix),
    (("xcodebuild", "build"), "build", _xcodebuild_suffix),
    (("swift", "test"), "test", lambda tokens, root, snapshots: _swift_suffix(tokens, root, snapshots)),
    (("swift", "build"), "build", lambda tokens, root, snapshots: _swift_suffix(tokens, root, snapshots, build=True)),
    (("npm", "run", "test"), "test", None), (("npm", "test"), "test", None),
    (("pnpm", "run", "test"), "test", None), (("pnpm", "test"), "test", None),
    (("npm", "run", "build"), "build", None), (("pnpm", "run", "build"), "build", None),
    (("pnpm", "build"), "build", None),
    (("npm", "run", "typecheck"), "typecheck", None), (("pnpm", "run", "typecheck"), "typecheck", None),
    (("pnpm", "typecheck"), "typecheck", None),
    (("npm", "run", "lint"), "lint", None), (("pnpm", "run", "lint"), "lint", None), (("pnpm", "lint"), "lint", None),
)


def _contains_unquoted_shell_operator(command):
    quote = None
    for character in command:
        if quote is None:
            if character in ("'", '"'):
                quote = character
            elif character in _SHELL_METACHARACTERS:
                return True
        elif character == quote:
            quote = None
        elif quote == '"' and character in ("$", "`", "\\"):
            return True
    return quote is not None


def parse_command(command, repo_root):
    if type(command) is not str or not command.strip() or _contains_unquoted_shell_operator(command):
        raise RouteDeclined("compound_command")
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError as error:
        raise RouteDeclined("compound_command") from error
    if not tokens or any(not token for token in tokens):
        raise RouteDeclined("command_not_allowed")
    root, root_snapshot = _repository_root(repo_root)
    for prefix, command_class, validator in _COMMAND_PREFIXES:
        if tuple(tokens[:len(prefix)]) != prefix:
            continue
        suffix = tokens[len(prefix):]
        operand_path_states = []
        if validator is None:
            if suffix:
                raise RouteDeclined("command_not_allowed")
        else:
            validator(list(suffix), root, operand_path_states)
        _recheck_snapshot(root_snapshot)
        for snapshot, missing in operand_path_states:
            _recheck_snapshot(snapshot)
            _recheck_absence(missing)
        return CommandSelection(
            command_class, tuple(tokens),
            (root_snapshot, tuple(operand_path_states)),
        )
    raise RouteDeclined("command_not_allowed")


def _fallback(outcome, reason):
    return {"outcome": outcome, "reasonCode": reason, "preserveOriginal": True}


def _request_bindings_match(request, result):
    return all(
        result.get(key) == request[key]
        for key in (
            "schemaVersion", "policyVersion", "callID", "toolName", "toolVersion", "stateVersion",
            "action", "commandClass", "originalResultType", "originalResultDigest", "exitStatus", "interrupted",
        )
    )


def _validate_source_facts(value):
    _validate_condensation(value)
    return value


def _json_clone(value, label):
    try:
        return json.loads(json.dumps(value, ensure_ascii=False, allow_nan=False))
    except (TypeError, ValueError, UnicodeError) as error:
        raise ContractError(f"invalid {label}") from error


def _response_semantics_match(request, response, source_facts):
    if response["condensation"] != source_facts:
        return False
    return response["condensation"]["commandOutcome"] == _semantic_command_outcome(
        request["exitStatus"], request["interrupted"]
    )


def _capture_contained_diagnostic_paths(condensation, repo_root):
    root, root_snapshot = _repository_root(repo_root)
    operand_path_states = []
    for diagnostic in condensation["diagnostics"]:
        if diagnostic["file"] is not None:
            _resolve_repo_path(
                diagnostic["file"], root, regular=True,
                snapshot_sink=operand_path_states,
            )
    _recheck_snapshot(root_snapshot)
    return root_snapshot, tuple(operand_path_states)


def _recheck_contained_path_state(path_states):
    for root_snapshot, operand_path_states in path_states:
        _recheck_snapshot(root_snapshot)
        for snapshot, missing in operand_path_states:
            _recheck_snapshot(snapshot)
            _recheck_absence(missing)


def _response_bytes(result):
    try:
        return len(json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
    except UnicodeError as error:
        raise ContractError("invalid response") from error
    except (TypeError, ValueError) as error:
        raise ContractError("invalid response") from error


def route(request, context):
    try:
        if type(context) is not dict:
            raise ContractError("invalid context")
        if context.get("eventName") != Policy.EVENT_NAME or type(request) is not dict or request.get("toolName") != Policy.TOOL_NAME:
            return _fallback("declined", "tool_not_allowed")
        fields = request.get("fields", ())
        if type(fields) is not list or any(
            type(field) is not dict or not _value_is_safe(field.get("value"))
            for field in fields
        ):
            return _fallback("declined", "data_policy_denied")
        try:
            actual_input_bytes = len(canonical_field_bytes(fields))
        except ContractError:
            return _fallback("declined", "data_policy_denied")
        actual_estimate = estimate_savings(actual_input_bytes)
        if (
            request.get("inputBytes") != actual_input_bytes
            or request.get("estimatedSavingsBytes") != actual_estimate
        ):
            return _fallback("declined", "contract_invariant_failed")
        field_path_states = []
        for field in fields:
            if type(field) is not dict or field.get("origin") != "trustedLocal" or field.get("classification") not in ("C0", "C1"):
                return _fallback("declined", "data_policy_denied")
            if field.get("name") == "file":
                try:
                    root, root_snapshot = _repository_root(context.get("repoRoot"))
                    field_snapshots = []
                    _resolve_repo_path(
                        field.get("value"), root, regular=True,
                        snapshot_sink=field_snapshots,
                    )
                    _recheck_snapshot(root_snapshot)
                    field_path_states.append(
                        (root_snapshot, tuple(field_snapshots))
                    )
                except RouteDeclined:
                    return _fallback("declined", "data_policy_denied")
        validate_request(request)
        if request["action"] != Policy.ACTION or request["policyVersion"] != Policy.POLICY_VERSION:
            return _fallback("fail", "contract_invariant_failed")
        selection = parse_command(context.get("command"), context.get("repoRoot"))
        if selection.command_class != request["commandClass"]:
            return _fallback("declined", "command_not_allowed")
        if context.get("appleAvailable") is not True:
            return _fallback("declined", "apple_unavailable")
        if context.get("localeSupported") is not True:
            return _fallback("declined", "locale_unsupported")
        try:
            within_apple_budget = fits_apple_budget(
                context.get("occupiedTokens"), context.get("contextSize")
            )
        except ContractError:
            return _fallback("declined", "context_budget_exceeded")
        if not within_apple_budget:
            return _fallback("declined", "context_budget_exceeded")
        bridge = context.get("bridge")
        if not callable(bridge):
            raise ContractError("invalid bridge")
        source_facts = _json_clone(context.get("sourceFacts"), "source facts")
        _validate_source_facts(source_facts)
        source_path_state = _capture_contained_diagnostic_paths(
            source_facts, context.get("repoRoot")
        )
        frozen_path_states = (
            (selection.path_state,)
            + tuple(field_path_states)
            + (source_path_state,)
        )
        _recheck_contained_path_state(frozen_path_states)
        frozen_request = _json_clone(request, "request")
        frozen_source_facts = _json_clone(source_facts, "source facts")
    except RouteDeclined as error:
        return _fallback("declined", error.reason)
    except ContractError:
        return _fallback("fail", "contract_invariant_failed")

    try:
        response = bridge(deepcopy(frozen_request))
    except RouteDeclined as error:
        return _fallback("declined", error.reason if error.reason in _REASON_CODES else "generation_declined")
    except Exception:
        return _fallback("fail", "contract_invariant_failed")
    try:
        validate_result(response)
        if not _request_bindings_match(frozen_request, response):
            raise ContractError("response bindings mismatch")
        if response["outcome"] != "applied":
            return _fallback(response["outcome"], response["reasonCode"])
        if not _response_semantics_match(frozen_request, response, frozen_source_facts):
            raise ContractError("invalid response semantics")
        _recheck_contained_path_state(frozen_path_states)
        output_bytes = _response_bytes(response)
        if output_bytes > Policy.MAXIMUM_CONDENSED_BYTES or frozen_request["inputBytes"] - output_bytes < Policy.MINIMUM_REALIZED_SAVINGS_BYTES:
            return _fallback("declined", "insufficient_realized_savings")
        return _json_clone(response, "response")
    except (ContractError, RouteDeclined):
        return _fallback("fail", "invalid_response")
