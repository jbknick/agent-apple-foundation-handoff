#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from typing import Any, Mapping


class ProbeError(ValueError):
    pass


OBSERVATION_KEYS = (
    "schemaVersion",
    "issue",
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
)
VERDICT_KEYS = (
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
)
HOOK_INPUT_KEYS = (
    "session_id",
    "transcript_path",
    "cwd",
    "hook_event_name",
    "model",
    "turn_id",
    "permission_mode",
    "tool_name",
    "tool_input",
    "tool_response",
    "tool_use_id",
)
DIRECT_BOUNDARY_SOURCE = "provider_next_request"
NON_BOUNDARY_SOURCES = frozenset(
    {"hook_stdout", "system_message", "transcript", "model_response", None}
)
SHA256_RE = re.compile(r"[0-9a-f]{64}")


def _require_closed_keys(value: Mapping[str, Any], expected: tuple[str, ...]) -> None:
    if set(value) != set(expected):
        raise ProbeError("schema_keys_invalid")


def _require_sha256(value: Any) -> str:
    if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
        raise ProbeError("sha256_invalid")
    return value


def normalize_verdict(observation: Mapping[str, Any]) -> dict[str, Any]:
    _require_closed_keys(observation, OBSERVATION_KEYS)
    if observation["schemaVersion"] != 1 or observation["issue"] != "DEV-246":
        raise ProbeError("identity_invalid")
    for key in (
        "manualSha256",
        "pluginSha256",
        "originalSha256",
        "compactSha256",
    ):
        _require_sha256(observation[key])

    boundary_source = observation["boundarySource"]
    original_absent = observation["originalAbsentFromNextRequest"]
    compact_present = observation["compactPresentInNextRequest"]

    if (
        observation["hookInvocations"] != 1
        or observation["additionalParentModelTurns"] != 0
    ):
        status, reason = "fail", "execution_invariant_failed"
    elif boundary_source in NON_BOUNDARY_SOURCES:
        status, reason = "blocked", "model_boundary_not_observable"
    elif boundary_source != DIRECT_BOUNDARY_SOURCE:
        raise ProbeError("boundary_source_invalid")
    elif original_absent is not True or compact_present is not True:
        status, reason = "blocked", "host_replacement_unavailable"
    else:
        status, reason = "pass", "replacement_proven"

    values = {
        "schemaVersion": 1,
        "issue": "DEV-246",
        "status": status,
        "reason": reason,
        "codexVersion": observation["codexVersion"],
        "codexExecutable": (
            "<host-path>" if observation["codexExecutable"] else None
        ),
        "manualSha256": observation["manualSha256"],
        "pluginSha256": observation["pluginSha256"],
        "originalSha256": observation["originalSha256"],
        "compactSha256": observation["compactSha256"],
        "boundarySource": boundary_source,
        "originalAbsentFromNextRequest": original_absent,
        "compactPresentInNextRequest": compact_present,
        "additionalParentModelTurns": observation["additionalParentModelTurns"],
        "hookInvocations": observation["hookInvocations"],
        "trustConfirmed": observation["trustConfirmed"],
        "cleanupStatus": observation["cleanupStatus"],
    }
    return {key: values[key] for key in VERDICT_KEYS}


def _canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_candidate_response(
    payload: Mapping[str, Any],
    *,
    expected_marker: str,
    expected_digest: str,
    compact_sentinel: str,
) -> dict[str, Any]:
    _require_closed_keys(payload, HOOK_INPUT_KEYS)
    if payload["hook_event_name"] != "PostToolUse" or payload["tool_name"] != "Bash":
        raise ProbeError("hook_identity_invalid")
    _require_sha256(expected_digest)
    if not expected_marker or not compact_sentinel:
        raise ProbeError("sentinel_invalid")
    serialized_response = json.dumps(
        payload["tool_response"],
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    if expected_marker not in serialized_response:
        raise ProbeError("original_marker_missing")
    if _canonical_sha256(payload["tool_response"]) != expected_digest:
        raise ProbeError("original_digest_mismatch")
    if expected_marker in compact_sentinel:
        raise ProbeError("compact_sentinel_leaks_original")
    return {
        "continue": True,
        "systemMessage": compact_sentinel,
        "suppressOutput": True,
    }


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise ProbeError("hook_input_not_object")
        response = build_candidate_response(
            payload,
            expected_marker=os.environ["DEV246_ORIGINAL_SENTINEL"],
            expected_digest=os.environ["DEV246_ORIGINAL_SHA256"],
            compact_sentinel=os.environ["DEV246_COMPACT_SENTINEL"],
        )
    except (KeyError, json.JSONDecodeError, ProbeError):
        sys.stderr.write("dev246_probe_input_rejected\n")
        return 2
    json.dump(response, sys.stdout, separators=(",", ":"), sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
