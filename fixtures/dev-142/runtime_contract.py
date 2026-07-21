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
from dataclasses import dataclass
from pathlib import Path


class _FrozenPolicy(type):
    def __setattr__(cls, name, value):
        if name in cls.__dict__:
            raise AttributeError("Policy is immutable")
        super().__setattr__(name, value)

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


@dataclass(frozen=True)
class QualityScore:
    passed: bool
    reason_codes: tuple[str, ...]


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


def _optional_integer(value, label, *, minimum=0):
    if value is None:
        return value
    return _integer(value, label, minimum=minimum)


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
    if value.startswith("/") or "\x00" in value or any(part in ("", ".", "..") for part in value.split("/")):
        raise ContractError(f"invalid {label}")
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
    names = set()
    for field in value["fields"]:
        _validate_field(field)
        if field["name"] in names:
            raise ContractError("duplicate field name")
        names.add(field["name"])
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
    _closed(value, ("summary", "diagnostics", "warningCount", "omittedWarningCount"))
    _string(value["summary"], "summary")
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
    _closed(value, ("exitStatus", "interrupted", "warningCount", "requiredDiagnosticIDs", "failedTestIDs"))
    _exit_status(value["exitStatus"], value["interrupted"])
    _integer(value["warningCount"], "warningCount", minimum=0)
    for key in ("requiredDiagnosticIDs", "failedTestIDs"):
        if type(value[key]) is not list or any(type(item) is not str or not item for item in value[key]):
            raise ContractError(f"invalid {key}")
        if len(set(value[key])) != len(value[key]):
            raise ContractError(f"duplicate {key}")
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
        "id", "pairID", "arm", "provider", "inputTokens", "cachedInputTokens",
        "outputTokens", "reasoningTokens", "totalParentModelTokens", "parentTurns",
        "appleAttempts", "replacements", "declines", "fallbacks", "latencyMilliseconds", "correct",
    ))
    _string(value["id"], "arm id")
    _string(value["pairID"], "pair id")
    _enum(value["arm"], ("pluginOff", "pluginOn"), "arm")
    _enum(value["provider"], ("openai-responses-usage-v1", "anthropic-messages-usage-v1"), "provider")
    for key in (
        "inputTokens", "cachedInputTokens", "outputTokens", "reasoningTokens",
        "totalParentModelTokens", "parentTurns", "appleAttempts", "replacements",
        "declines", "fallbacks", "latencyMilliseconds",
    ):
        _optional_integer(value[key], key)
    if value["correct"] is not None and type(value["correct"]) is not bool:
        raise ContractError("invalid correct")
    if value["arm"] == "pluginOff" and (value["appleAttempts"] not in (None, 0) or value["replacements"] not in (None, 0)):
        raise ContractError("pluginOff cannot use Apple or replace output")
    return value


def _validate_pair(value):
    _closed(value, ("id", "status", "reduction"))
    _string(value["id"], "pair id")
    _enum(value["status"], ("valid", "blocked"), "pair status")
    _finite_number(value["reduction"], "reduction", minimum=-1, maximum=1, nullable=True)
    if value["status"] == "blocked" and value["reduction"] is not None:
        raise ContractError("blocked pair has reduction")
    return value


def _validate_release(value):
    _closed(value, (
        "status", "validRequiredPairs", "blockedRequiredPairs", "medianReduction",
        "correctnessRegressions", "additionalParentModelTurns",
    ))
    _enum(value["status"], ("pass", "fail", "blocked"), "release status")
    for key in ("validRequiredPairs", "blockedRequiredPairs", "correctnessRegressions", "additionalParentModelTurns"):
        _integer(value[key], key, minimum=0)
    _finite_number(value["medianReduction"], "medianReduction", minimum=-1, maximum=1, nullable=True)
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
    else:
        _closed(value, ("schemaVersion", "policyVersion", "kind", "arms", "pairs", "release"))
        _integer(value["schemaVersion"], "schemaVersion", minimum=Policy.SCHEMA_VERSION, maximum=Policy.SCHEMA_VERSION)
        _enum(value["policyVersion"], (Policy.POLICY_VERSION,), "policyVersion")
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
    return value


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
    if severity not in ("fatal", "error") or index < 1:
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
    return f"synthetic {case['commandForm']} summary"


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
        ("summary", _case_summary(case)),
    )
    rendered = [f"{key}: {value}\n" for key, value in lines]
    for diagnostic_id in expected["requiredDiagnosticIDs"]:
        diagnostic = _diagnostic_for_case(case, diagnostic_id)
        rendered.append(
            "diagnostic: " + json.dumps(
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


def _invented_facts(case, result):
    try:
        condensation = result["condensation"]
        if type(condensation) is not dict:
            return True
        if condensation["summary"] != _case_summary(case):
            return True
        if condensation["warningCount"] != case["expected"]["warningCount"]:
            return True
        if type(condensation["warningCount"]) is not int or type(condensation["omittedWarningCount"]) is not int or not 0 <= condensation["omittedWarningCount"] <= condensation["warningCount"]:
            return True
    except (KeyError, TypeError):
        return True
    return False


def score_condensation(case, result):
    """Score a normalized condensation against its immutable synthetic case."""
    _validate_case(case)
    reasons = []
    try:
        if result["exitStatus"] != case["expected"]["exitStatus"]:
            reasons.append("exit_status_regression")
        if result["interrupted"] != case["expected"]["interrupted"]:
            reasons.append("interruption_regression")
    except (KeyError, TypeError):
        reasons.extend(("exit_status_regression", "interruption_regression"))
    if _diagnostic_identities(result) != _required_identities(case):
        reasons.append("diagnostic_identity_regression")
    if _invented_facts(case, result):
        reasons.append("invented_fact")
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
        {"id": "below-input-minimum", "inputBytes": 8191, "outputBytes": 4096, "realizedSavingsBytes": 4095, "occupiedTokens": 6144, "contextSize": 8192},
        {"id": "minimum-input", "inputBytes": 8192, "outputBytes": 4096, "realizedSavingsBytes": 4096, "occupiedTokens": 6144, "contextSize": 8192},
        {"id": "maximum-input", "inputBytes": 65536, "outputBytes": 61440, "realizedSavingsBytes": 61440, "occupiedTokens": 6144, "contextSize": 8192},
        {"id": "above-input-maximum", "inputBytes": 65537, "outputBytes": 61440, "realizedSavingsBytes": 4097, "occupiedTokens": 6145, "contextSize": 8192},
        {"id": "below-output-minimum", "inputBytes": 8192, "outputBytes": 4095, "realizedSavingsBytes": 4097, "occupiedTokens": 6145, "contextSize": 8192},
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
    estimate = input_bytes - Policy.MAXIMUM_CONDENSED_BYTES
    if estimate < Policy.MINIMUM_ESTIMATED_SAVINGS_BYTES:
        raise RouteDeclined("estimated_savings_below_minimum")
    return estimate


def fits_apple_budget(occupied_tokens, context_size):
    _require_int(occupied_tokens, 0)
    _require_int(context_size, 1)
    return (
        occupied_tokens * Policy.MAXIMUM_APPLE_CONTEXT_DENOMINATOR
        <= context_size * Policy.MAXIMUM_APPLE_CONTEXT_NUMERATOR
    )


def _identity(path):
    record = _lstat(path)
    return record.st_dev, record.st_ino, record.st_mode


def _contained(candidate, root):
    try:
        candidate.relative_to(root)
    except ValueError as error:
        raise RouteDeclined("command_not_allowed") from error


def _repository_root(repo_root):
    if not isinstance(repo_root, (str, Path)):
        raise RouteDeclined("command_not_allowed")
    root = Path(repo_root)
    try:
        root_identity = _identity(root)
        if stat.S_ISLNK(root_identity[2]) or not stat.S_ISDIR(root_identity[2]):
            raise RouteDeclined("command_not_allowed")
        resolved = root.resolve(strict=False)
    except (OSError, RuntimeError) as error:
        raise RouteDeclined("command_not_allowed") from error
    if _identity(root) != root_identity:
        raise RouteDeclined("command_not_allowed")
    return resolved, root_identity


def _path_value(token):
    if type(token) is not str or not token or token.startswith("/") or "\\" in token:
        raise RouteDeclined("command_not_allowed")
    if any(part in ("", ".", "..") for part in token.split("/")):
        raise RouteDeclined("command_not_allowed")
    return token


def _reject_symlink_ancestors(candidate, root):
    _contained(candidate, root)
    current = root
    missing = False
    for component in candidate.relative_to(root).parts[:-1]:
        current /= component
        try:
            identity = _identity(current)
        except OSError:
            missing = True
            continue
        if missing or stat.S_ISLNK(identity[2]):
            raise RouteDeclined("command_not_allowed")


def _resolve_repo_path(token, root, *, directory=False, suffix=None, regular=False):
    token = _path_value(token)
    candidate = root / token
    _reject_symlink_ancestors(candidate, root)
    try:
        first = _identity(candidate)
        exists = True
    except OSError:
        exists = False
        parent = candidate.parent
        while parent != root:
            try:
                parent_identity = _identity(parent)
                break
            except OSError:
                parent = parent.parent
        try:
            parent_identity = _identity(parent)
            if stat.S_ISLNK(parent_identity[2]):
                raise RouteDeclined("command_not_allowed")
            _contained(parent.resolve(strict=False), root)
        except (OSError, RuntimeError) as error:
            raise RouteDeclined("command_not_allowed") from error
        if not directory:
            raise RouteDeclined("command_not_allowed")
    if exists:
        if stat.S_ISLNK(first[2]):
            raise RouteDeclined("command_not_allowed")
        try:
            resolved = candidate.resolve(strict=False)
        except (OSError, RuntimeError) as error:
            raise RouteDeclined("command_not_allowed") from error
        _contained(resolved, root)
        if _identity(candidate) != first:
            raise RouteDeclined("command_not_allowed")
        _reject_symlink_ancestors(candidate, root)
        if directory and not stat.S_ISDIR(first[2]):
            raise RouteDeclined("command_not_allowed")
        if regular and not stat.S_ISREG(first[2]):
            raise RouteDeclined("command_not_allowed")
    if suffix is not None and not token.endswith(suffix):
        raise RouteDeclined("command_not_allowed")
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


def _take_pairs(tokens, allowed, root, *, values=None):
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
            _resolve_repo_path(value, root, directory=True)
        elif validator == "configuration":
            if value not in values:
                raise RouteDeclined("command_not_allowed")
        elif validator == "selector":
            _safe_selector(value)
        elif validator == "glob":
            if not _SAFE_GLOB.fullmatch(value):
                raise RouteDeclined("command_not_allowed")
        index += 2


def _swift_suffix(tokens, root, *, build=False):
    allowed = {"--configuration": "configuration", "--package-path": "directory", "--scratch-path": "directory"}
    if not build:
        allowed["--filter"] = "selector"
    _take_pairs(tokens, allowed, root, values=frozenset(("debug", "release")))


def _swiftc_suffix(tokens, root):
    if not tokens:
        raise RouteDeclined("command_not_allowed")
    for token in tokens:
        _resolve_repo_path(token, root, suffix=".swift", regular=True)


def _swift_format_suffix(tokens, root):
    seen = set()
    while tokens and tokens[0] in ("--recursive", "--strict"):
        option = tokens.pop(0)
        if option in seen:
            raise RouteDeclined("command_not_allowed")
        seen.add(option)
    if not tokens:
        raise RouteDeclined("command_not_allowed")
    for token in tokens:
        _resolve_repo_path(token, root)


def _xcodebuild_suffix(tokens, root):
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
            _resolve_repo_path(value, root, suffix=".xcodeproj", directory=True)
        elif kind == "workspace":
            _resolve_repo_path(value, root, suffix=".xcworkspace", directory=True)
        elif kind == "configuration":
            if value not in ("Debug", "Release"):
                raise RouteDeclined("command_not_allowed")
        elif kind == "directory":
            _resolve_repo_path(value, root, directory=True)
        else:
            _safe_selector(value)
        index += 2
    if "-project" in seen and "-workspace" in seen:
        raise RouteDeclined("command_not_allowed")


def _unittest_suffix(tokens, root):
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
    _take_pairs(tokens, {"-s": "directory", "-p": "glob", "-t": "directory"}, root)


def _pytest_suffix(tokens, root):
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
            _resolve_repo_path(path, root)
            if separator and (not selector or any(not _PYTHON_IDENTIFIER.fullmatch(part) for part in selector.split("::"))):
                raise RouteDeclined("command_not_allowed")
        index += 1


def _build_suffix(tokens):
    if len(tokens) > 2 or len(set(tokens)) != len(tokens) or any(token not in ("--sdist", "--wheel") for token in tokens):
        raise RouteDeclined("command_not_allowed")


def _mypy_suffix(tokens, root):
    seen = set()
    while tokens and tokens[0] in ("--strict", "--no-incremental"):
        option = tokens.pop(0)
        if option in seen:
            raise RouteDeclined("command_not_allowed")
        seen.add(option)
    if not tokens:
        raise RouteDeclined("command_not_allowed")
    for token in tokens:
        _resolve_repo_path(token, root)


def _ruff_suffix(tokens, root):
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
        _resolve_repo_path(token, root)


_COMMAND_PREFIXES = (
    (("python3", "-m", "ruff", "check"), "lint", _ruff_suffix),
    (("python3", "-m", "unittest"), "test", _unittest_suffix),
    (("python3", "-m", "pytest"), "test", _pytest_suffix),
    (("python3", "-m", "build"), "build", lambda tokens, root: _build_suffix(tokens)),
    (("python3", "-m", "mypy"), "typecheck", _mypy_suffix),
    (("swift", "format", "lint"), "lint", _swift_format_suffix),
    (("swiftc", "-typecheck"), "typecheck", _swiftc_suffix),
    (("xcodebuild", "test"), "test", _xcodebuild_suffix),
    (("xcodebuild", "build"), "build", _xcodebuild_suffix),
    (("swift", "test"), "test", lambda tokens, root: _swift_suffix(tokens, root)),
    (("swift", "build"), "build", lambda tokens, root: _swift_suffix(tokens, root, build=True)),
    (("npm", "run", "test"), "test", None), (("npm", "test"), "test", None),
    (("pnpm", "run", "test"), "test", None), (("pnpm", "test"), "test", None),
    (("npm", "run", "build"), "build", None), (("pnpm", "run", "build"), "build", None),
    (("pnpm", "build"), "build", None),
    (("npm", "run", "typecheck"), "typecheck", None), (("pnpm", "run", "typecheck"), "typecheck", None),
    (("pnpm", "typecheck"), "typecheck", None),
    (("npm", "run", "lint"), "lint", None), (("pnpm", "run", "lint"), "lint", None), (("pnpm", "lint"), "lint", None),
)


def parse_command(command, repo_root):
    if type(command) is not str or not command.strip() or any(character in _SHELL_METACHARACTERS for character in command):
        raise RouteDeclined("compound_command")
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError as error:
        raise RouteDeclined("compound_command") from error
    if not tokens or any(not token for token in tokens):
        raise RouteDeclined("command_not_allowed")
    root, root_identity = _repository_root(repo_root)
    for prefix, command_class, validator in _COMMAND_PREFIXES:
        if tuple(tokens[:len(prefix)]) != prefix:
            continue
        suffix = tokens[len(prefix):]
        if validator is None:
            if suffix:
                raise RouteDeclined("command_not_allowed")
        else:
            validator(list(suffix), root)
        if _identity(root) != root_identity:
            raise RouteDeclined("command_not_allowed")
        return CommandSelection(command_class, tuple(tokens))
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
        estimate_savings(request.get("inputBytes"))
        for field in request.get("fields", ()):
            if type(field) is not dict or field.get("origin") != "trustedLocal" or field.get("classification") not in ("C0", "C1"):
                return _fallback("declined", "data_policy_denied")
            if field.get("name") == "file":
                try:
                    root, root_identity = _repository_root(context.get("repoRoot"))
                    _resolve_repo_path(field.get("value"), root, regular=True)
                    if _identity(root) != root_identity:
                        raise RouteDeclined("command_not_allowed")
                except RouteDeclined:
                    return _fallback("declined", "data_policy_denied")
        validate_request(request)
        if request["action"] != Policy.ACTION or request["policyVersion"] != Policy.POLICY_VERSION:
            return _fallback("declined", "contract_invariant_failed")
        selection = parse_command(context.get("command"), context.get("repoRoot"))
        if selection.command_class != request["commandClass"]:
            return _fallback("declined", "command_not_allowed")
        estimate = estimate_savings(request["inputBytes"])
        if request["estimatedSavingsBytes"] != estimate:
            return _fallback("declined", "contract_invariant_failed")
        if context.get("appleAvailable") is not True:
            return _fallback("declined", "apple_unavailable")
        if context.get("localeSupported") is not True:
            return _fallback("declined", "locale_unsupported")
        if not fits_apple_budget(context.get("occupiedTokens"), context.get("contextSize")):
            return _fallback("declined", "context_budget_exceeded")
        bridge = context.get("bridge")
        if not callable(bridge):
            raise ContractError("invalid bridge")
    except RouteDeclined as error:
        return _fallback("declined", error.reason)
    except ContractError:
        return _fallback("fail", "contract_invariant_failed")

    try:
        response = bridge(request)
    except RouteDeclined as error:
        return _fallback("declined", error.reason if error.reason in _REASON_CODES else "generation_declined")
    except Exception:
        return _fallback("fail", "contract_invariant_failed")
    try:
        validate_result(response)
        if response["outcome"] != "applied":
            return _fallback(response["outcome"], response["reasonCode"])
        if not _request_bindings_match(request, response):
            raise ContractError("response bindings mismatch")
        output_bytes = _response_bytes(response)
        if output_bytes > Policy.MAXIMUM_CONDENSED_BYTES or request["inputBytes"] - output_bytes < Policy.MINIMUM_REALIZED_SAVINGS_BYTES:
            return _fallback("declined", "insufficient_realized_savings")
        return response
    except ContractError:
        return _fallback("fail", "invalid_response")
