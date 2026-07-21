"""Closed, offline DEV-142 policy envelopes.

This module deliberately performs no host, process, or model operation.
"""

import json
import math
import re
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
    if name not in _FIELD_NAMES:
        raise ContractError("field name is not allowlisted")
    if field["origin"] != "trustedLocal":
        raise ContractError("invalid field origin")
    if field["classification"] not in ("C0", "C1"):
        raise ContractError("invalid field classification")
    if field["purpose"] != Policy.RESULT_TYPE:
        raise ContractError("invalid field purpose")
    if field["destination"] != "apple_on_device":
        raise ContractError("invalid field destination")
    if field["retention"] != "ephemeral":
        raise ContractError("invalid field retention")
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
    if value["policyVersion"] != Policy.POLICY_VERSION:
        raise ContractError("invalid policyVersion")
    _string(value["callID"], "callID")
    if value["toolName"] != Policy.TOOL_NAME:
        raise ContractError("invalid toolName")
    _string(value["toolVersion"], "toolVersion")
    _string(value["stateVersion"], "stateVersion")
    if value["action"] != Policy.ACTION:
        raise ContractError("invalid action")
    if value["commandClass"] not in _COMMAND_CLASSES:
        raise ContractError("invalid commandClass")
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
    if value["severity"] not in _SEVERITIES:
        raise ContractError("invalid diagnostic severity")
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
        if diagnostic["id"] in identities:
            raise ContractError("duplicate diagnostic identity")
        identities.add(diagnostic["id"])
    _integer(value["warningCount"], "warningCount", minimum=0)
    _integer(value["omittedWarningCount"], "omittedWarningCount", minimum=0, maximum=value["warningCount"])
    return value


def validate_result(value):
    bindings = (
        "schemaVersion", "policyVersion", "callID", "toolName", "toolVersion",
        "stateVersion", "action", "commandClass", "originalResultType",
        "originalResultDigest", "outcome", "exitStatus", "interrupted",
    )
    if type(value) is not dict or value.get("outcome") not in ("applied", "declined", "fail"):
        raise ContractError("invalid result outcome")
    if value["outcome"] == "applied":
        _validate_bindings(value, (*bindings, "resultType", "condensation"))
        if value["resultType"] != Policy.RESULT_TYPE:
            raise ContractError("invalid resultType")
        _validate_condensation(value["condensation"])
    else:
        _validate_bindings(value, (*bindings, "reasonCode"))
        if value["reasonCode"] not in _REASON_CODES:
            raise ContractError("invalid reasonCode")
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
    if value["commandClass"] not in _COMMAND_CLASSES:
        raise ContractError("invalid case commandClass")
    _string(value["commandForm"], "commandForm")
    if value["classification"] not in ("C0", "C1"):
        raise ContractError("invalid case classification")
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
    if value["arm"] not in ("pluginOff", "pluginOn"):
        raise ContractError("invalid arm")
    if value["provider"] not in ("openai-responses-usage-v1", "anthropic-messages-usage-v1"):
        raise ContractError("invalid provider")
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
    if value["status"] not in ("valid", "blocked"):
        raise ContractError("invalid pair status")
    _finite_number(value["reduction"], "reduction", minimum=-1, maximum=1, nullable=True)
    if value["status"] == "blocked" and value["reduction"] is not None:
        raise ContractError("blocked pair has reduction")
    return value


def _validate_release(value):
    _closed(value, (
        "status", "validRequiredPairs", "blockedRequiredPairs", "medianReduction",
        "correctnessRegressions", "additionalParentModelTurns",
    ))
    if value["status"] not in ("pass", "fail", "blocked"):
        raise ContractError("invalid release status")
    for key in ("validRequiredPairs", "blockedRequiredPairs", "correctnessRegressions", "additionalParentModelTurns"):
        _integer(value[key], key, minimum=0)
    _finite_number(value["medianReduction"], "medianReduction", minimum=-1, maximum=1, nullable=True)
    return value


def validate_benchmark(value):
    if type(value) is not dict or value.get("kind") not in ("corpus", "evidence"):
        raise ContractError("invalid benchmark kind")
    if value["kind"] == "corpus":
        _closed(value, ("schemaVersion", "policyVersion", "kind", "corpusVersion", "corpusSha256", "cases"))
        _integer(value["schemaVersion"], "schemaVersion", minimum=Policy.SCHEMA_VERSION, maximum=Policy.SCHEMA_VERSION)
        if value["policyVersion"] != Policy.POLICY_VERSION:
            raise ContractError("invalid policyVersion")
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
        if value["policyVersion"] != Policy.POLICY_VERSION:
            raise ContractError("invalid policyVersion")
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
