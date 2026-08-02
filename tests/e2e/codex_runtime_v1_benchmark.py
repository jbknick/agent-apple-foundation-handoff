#!/usr/bin/env python3
"""Authorized, fail-closed outer runner for codex-runtime-v1-cost-v1."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import asdict, dataclass, replace
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import threading
import time
from typing import Callable, Iterator


ROOT = Path(__file__).resolve().parents[2]
PRODUCTION = ROOT / "tests/e2e/codex_runtime_v1_production.py"
CONTRACT = (
    ROOT
    / "fixtures/runtime-v1-benchmark/runtime_v1_benchmark.py"
)
CORPUS = ROOT / "fixtures/dev-142/benchmark-corpus.json"
PLUGIN = ROOT / "plugins/apple-foundation-models-handoff"
PRODUCTION_COMMIT = "6d336044b0c21dfeca485b6676a18d50bf085487"
PROFILE = "codex-runtime-v1-cost-v1"
CODEX_SOURCE_COMMIT = "25af12f7"
_COMMIT = re.compile(r"[0-9a-f]{40}\Z")
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_OBSERVATION_KEYS = {
    "schemaVersion", "event", "status", "reasonCode", "appleAttempts",
    "appleValidResults", "replacementEmitted", "replacementSha256",
    "replacementBytes", "preReceiptHookLatencyNanoseconds",
    "appleLatencyNanoseconds", "appleLatencySamples",
}
_FORWARDING_FAILURE_STAGES = {
    "preflight_setup",
    "process_execution",
    "provider_teardown",
    "observation_cleanup",
    "process_stderr",
    "process_exit",
    "jsonl",
    "request_count",
    "direct_tool_contract",
    "function_output",
    "command_counter_presence",
    "command_counter_value",
    "original_exclusion",
    "receipt",
    "identity_trust",
    "unexpected_exception",
}
_PROVIDER_COUNTER_FAILURE_STAGES = {
    "process_exit",
    "telemetry_payload",
    "telemetry_batch",
}


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"{name}_unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


production = _load(PRODUCTION, "runtime_v1_benchmark_production_helpers")
contract = _load(CONTRACT, "runtime_v1_benchmark_contract")
capture_codex = production.capture_codex
capture_python = production.capture_python
install_plugin = production.install_plugin
trust_hook = production.trust_hook
tree_sha256 = production.tree_sha256
atomic_write_json = production.atomic_write_json


class BenchmarkBlocked(ValueError):
    pass


class BenchmarkFailure(ValueError):
    pass


class ForwardingPreflightBlocked(BenchmarkBlocked):
    def __init__(self, failure_stage: str):
        if failure_stage not in _FORWARDING_FAILURE_STAGES:
            raise ValueError("invalid forwarding failure stage")
        super().__init__("replacement_forwarding_unproven")
        self.failure_stage = failure_stage


class ProviderCounterBlocked(BenchmarkBlocked):
    def __init__(self, failure_stage: str):
        if failure_stage not in _PROVIDER_COUNTER_FAILURE_STAGES:
            raise ValueError("invalid provider counter failure stage")
        super().__init__("provider_request_counter_invalid")
        self.failure_stage = failure_stage


@dataclass
class _ForwardingFailureState:
    stage: str | None = None

    def enter(self, stage: str) -> None:
        if stage not in _FORWARDING_FAILURE_STAGES - {
            "unexpected_exception"
        }:
            raise ValueError("invalid forwarding failure stage")
        self.stage = stage

    def leave(self) -> None:
        self.stage = None


@dataclass(frozen=True)
class CandidateIdentity:
    repository: Path
    candidate_commit: str
    production_commit: str
    run_git: Callable[[list[str]], str]

    def recheck(self) -> None:
        if self.run_git(["rev-parse", "HEAD"]).strip() != self.candidate_commit:
            raise BenchmarkFailure("candidate_identity_drift")
        if self.run_git(["status", "--porcelain"]) != "":
            raise BenchmarkFailure("candidate_identity_drift")


@dataclass(frozen=True)
class ParsedEvents:
    usage: contract.RuntimeV1Usage
    command_executions: int
    completed_parent_turns: int
    final_agent_message: str


@dataclass(frozen=True)
class ArmObservation:
    event_stream: bytes
    parent_requests: int | None
    apple_attempts: int
    validated_applied: bool
    correctness_passed: bool
    parent_latency_ns: int
    pre_receipt_hook_latency_ns: int
    pre_receipt_hook_latency_samples: int
    apple_latency_ns: int
    apple_latency_samples: int
    stderr_bytes: int
    cleanup_complete: bool


@dataclass(frozen=True)
class ForwardingProof:
    status: str
    candidate_commit: str
    codex_version: str
    codex_source_commit: str
    plugin_sha256: str
    hook_hash: str
    adapter_sha256: str


def validate_forwarding_proof(
    proof: ForwardingProof,
    *,
    candidate_commit: str,
    production_identities: dict[str, str],
    approved_hook_hash: str,
) -> None:
    if (
        not isinstance(proof, ForwardingProof)
        or proof.status != "pass"
        or proof.candidate_commit != candidate_commit
        or proof.codex_version != "0.145.0"
        or proof.codex_source_commit != CODEX_SOURCE_COMMIT
        or proof.plugin_sha256
        != production_identities["productionPluginSha256"]
        or proof.adapter_sha256
        != production_identities["pythonAdapterSha256"]
        or proof.hook_hash != approved_hook_hash
    ):
        raise BenchmarkBlocked("replacement_forwarding_unproven")


def derive_validated_applied(
    *,
    role: str,
    replacement_emitted: bool,
    apple_attempts: int | None,
    parent_requests: int,
    completed_parent_turns: int,
    command_executions: int,
    correctness_passed: bool,
    forwarding_preflight_passed: bool,
) -> bool:
    return (
        role == "pluginOn"
        and replacement_emitted is True
        and apple_attempts == 1
        and parent_requests == 2
        and completed_parent_turns == 1
        and command_executions == 1
        and correctness_passed is True
        and forwarding_preflight_passed is True
    )


def _closed_json_object(pairs):
    decoded = {}
    for key, child in pairs:
        if key in decoded:
            raise ValueError("duplicate JSON key")
        decoded[key] = child
    return decoded


def parse_runtime_v1_observation(value: bytes) -> dict[str, object]:
    try:
        if not value.endswith(b"\n") or value.count(b"\n") != 1:
            raise ValueError("invalid observation framing")
        row = json.loads(
            value,
            object_pairs_hook=_closed_json_object,
            parse_constant=lambda _value: (_ for _ in ()).throw(ValueError()),
        )
    except (UnicodeError, ValueError, json.JSONDecodeError):
        raise BenchmarkBlocked("observation_invariant_failed") from None
    if (
        type(row) is not dict
        or set(row) != _OBSERVATION_KEYS
        or type(row["schemaVersion"]) is not int
        or row["schemaVersion"] != 1
        or row["event"] != "runtime_v1_observation"
        or row["status"] not in {
            "replacement_emitted", "fallback", "blocked"
        }
        or row["reasonCode"] not in {
            None, "apple_attempt_count_uncertain",
            "observation_invariant_failed",
        }
        or (
            row["appleAttempts"] is not None
            and (
                type(row["appleAttempts"]) is not int
                or row["appleAttempts"] not in {0, 1}
            )
        )
        or type(row["appleValidResults"]) is not int
        or row["appleValidResults"] not in {0, 1}
        or type(row["replacementEmitted"]) is not bool
        or type(row["preReceiptHookLatencyNanoseconds"]) is not int
        or row["preReceiptHookLatencyNanoseconds"] < 0
        or type(row["appleLatencySamples"]) is not int
        or row["appleLatencySamples"] not in {0, 1}
        or (
            row["appleLatencyNanoseconds"] is not None
            and (
                type(row["appleLatencyNanoseconds"]) is not int
                or row["appleLatencyNanoseconds"] < 0
            )
        )
        or (
            row["replacementSha256"] is not None
            and (
                type(row["replacementSha256"]) is not str
                or _DIGEST.fullmatch(row["replacementSha256"]) is None
            )
        )
        or (
            row["replacementBytes"] is not None
            and (
                type(row["replacementBytes"]) is not int
                or row["replacementBytes"] < 0
            )
        )
    ):
        raise BenchmarkBlocked("observation_invariant_failed")
    status = row["status"]
    applied = status == "replacement_emitted"
    if (
        (status == "blocked")
        or (
            applied
            and (
                row["reasonCode"] is not None
                or row["appleAttempts"] != 1
                or row["appleValidResults"] != 1
                or row["replacementEmitted"] is not True
                or row["replacementSha256"] is None
                or row["replacementBytes"] is None
                or row["appleLatencySamples"] != 1
            )
        )
        or (
            status == "fallback"
            and (
                row["reasonCode"] is not None
                or row["appleValidResults"] != 0
                or row["replacementEmitted"] is not False
                or row["replacementSha256"] is not None
                or row["replacementBytes"] is not None
            )
        )
        or (
            row["appleLatencySamples"] == 0
            and row["appleLatencyNanoseconds"] is not None
        )
        or (
            row["appleLatencySamples"] == 1
            and row["appleLatencyNanoseconds"] is None
        )
        or (
            row["appleAttempts"] == 0
            and row["appleLatencySamples"] != 0
        )
        or (
            row["appleAttempts"] == 1
            and row["appleLatencySamples"] != 1
        )
        or (
            row["appleAttempts"] is None
            and row["appleLatencySamples"] != 0
        )
    ):
        reason = (
            "apple_attempt_count_uncertain"
            if status == "blocked"
            and row["reasonCode"] == "apple_attempt_count_uncertain"
            else "observation_invariant_failed"
        )
        raise BenchmarkBlocked(reason)
    return row


def consume_runtime_v1_observation(path: Path) -> dict[str, object]:
    descriptor = -1
    try:
        metadata = path.lstat()
        if (
            path.name != "runtime-v1-observation.json"
            or path.parent.name != ".runtime-v1-observation"
            or path.resolve(strict=True) != path
            or not stat.S_ISREG(metadata.st_mode)
            or metadata.st_nlink != 1
            or stat.S_IMODE(metadata.st_mode) != 0o600
        ):
            raise ValueError
        descriptor = os.open(
            path,
            os.O_RDONLY
            | os.O_NOFOLLOW
            | os.O_CLOEXEC,
        )
        opened = os.fstat(descriptor)
        identity = (
            opened.st_dev,
            opened.st_ino,
            stat.S_IFMT(opened.st_mode),
            stat.S_IMODE(opened.st_mode),
            opened.st_nlink,
        )
        if identity != (
            metadata.st_dev,
            metadata.st_ino,
            stat.S_IFMT(metadata.st_mode),
            stat.S_IMODE(metadata.st_mode),
            metadata.st_nlink,
        ):
            raise ValueError
        value = os.read(descriptor, 4097)
        if len(value) > 4096 or os.read(descriptor, 1):
            raise ValueError
        os.close(descriptor)
        descriptor = -1
        after = path.lstat()
        if identity != (
            after.st_dev,
            after.st_ino,
            stat.S_IFMT(after.st_mode),
            stat.S_IMODE(after.st_mode),
            after.st_nlink,
        ):
            raise ValueError
        return parse_runtime_v1_observation(value)
    except BenchmarkBlocked:
        raise
    except (OSError, ValueError):
        raise BenchmarkBlocked("observation_invariant_failed") from None
    finally:
        if descriptor >= 0:
            os.close(descriptor)


class _OtelCounterServer(ThreadingHTTPServer):
    def __init__(self):
        super().__init__(("127.0.0.1", 0), _OtelHandler)
        self.api_requests = 0
        self.batches = 0
        self.invalid = False


def _validate_otlp_any_value(value: object) -> None:
    if type(value) is not dict or len(value) != 1:
        raise ValueError("invalid OTLP batch")
    key, child = next(iter(value.items()))
    if key == "stringValue":
        valid = type(child) is str
    elif key == "boolValue":
        valid = type(child) is bool
    elif key in {"intValue", "bytesValue"}:
        valid = type(child) in {str, int, float}
    elif key == "doubleValue":
        valid = (
            type(child) in {str, int, float}
            and not (
                type(child) is float
                and not math.isfinite(child)
            )
        )
    elif key == "arrayValue":
        valid = (
            type(child) is dict
            and set(child) == {"values"}
            and type(child["values"]) is list
        )
        if valid:
            for item in child["values"]:
                _validate_otlp_any_value(item)
    elif key == "kvlistValue":
        valid = (
            type(child) is dict
            and set(child) == {"values"}
            and type(child["values"]) is list
        )
        if valid:
            _validate_otlp_attributes(child["values"])
    else:
        valid = False
    if not valid:
        raise ValueError("invalid OTLP batch")


def _validate_otlp_attributes(value: object) -> None:
    if type(value) is not list:
        raise ValueError("invalid OTLP batch")
    keys = set()
    for attribute in value:
        if (
            type(attribute) is not dict
            or set(attribute) != {"key", "value"}
            or type(attribute["key"]) is not str
        ):
            raise ValueError("invalid OTLP batch")
        if attribute["key"] in keys:
            raise ValueError("invalid OTLP batch")
        keys.add(attribute["key"])
        _validate_otlp_any_value(attribute["value"])


def _api_request_count(value: object) -> int:
    if type(value) is not dict or set(value) != {"resourceLogs"}:
        raise ValueError("invalid OTLP batch")
    count = 0
    resources = value.get("resourceLogs")
    if type(resources) is not list:
        raise ValueError("invalid OTLP batch")
    for resource in resources:
        scopes = resource.get("scopeLogs") if type(resource) is dict else None
        if (
            type(resource) is not dict
            or not set(resource).issubset(
                {"resource", "scopeLogs", "schemaUrl"}
            )
            or type(scopes) is not list
        ):
            raise ValueError("invalid OTLP batch")
        resource_value = resource.get("resource")
        if resource_value is not None:
            if (
                type(resource_value) is not dict
                or not set(resource_value).issubset(
                    {"attributes", "droppedAttributesCount"}
                )
            ):
                raise ValueError("invalid OTLP batch")
            _validate_otlp_attributes(
                resource_value.get("attributes", [])
            )
        for scope in scopes:
            records = scope.get("logRecords") if type(scope) is dict else None
            if (
                type(scope) is not dict
                or not set(scope).issubset(
                    {"scope", "logRecords", "schemaUrl"}
                )
                or type(records) is not list
            ):
                raise ValueError("invalid OTLP batch")
            scope_value = scope.get("scope")
            if scope_value is not None:
                if (
                    type(scope_value) is not dict
                    or not set(scope_value).issubset(
                        {
                            "name", "version", "attributes",
                            "droppedAttributesCount",
                        }
                    )
                ):
                    raise ValueError("invalid OTLP batch")
                _validate_otlp_attributes(
                    scope_value.get("attributes", [])
                )
            for record in records:
                attributes = (
                    record.get("attributes") if type(record) is dict else None
                )
                if (
                    type(record) is not dict
                    or not set(record).issubset(
                        {
                            "timeUnixNano", "observedTimeUnixNano",
                            "severityNumber", "severityText", "body",
                            "attributes", "droppedAttributesCount", "flags",
                            "traceId", "spanId",
                        }
                    )
                    or type(attributes) is not list
                ):
                    raise ValueError("invalid OTLP batch")
                if "body" in record:
                    _validate_otlp_any_value(record["body"])
                _validate_otlp_attributes(attributes)
                names = []
                endpoints = []
                for attribute in attributes:
                    child = attribute["value"]
                    if attribute.get("key") == "event.name":
                        if (
                            set(child) != {"stringValue"}
                        ):
                            raise ValueError("invalid OTLP batch")
                        names.append(child.get("stringValue"))
                    if attribute.get("key") == "endpoint":
                        if set(child) != {"stringValue"}:
                            raise ValueError("invalid OTLP batch")
                        endpoints.append(child.get("stringValue"))
                if len(names) > 1 or len(endpoints) > 1:
                    raise ValueError("invalid OTLP batch")
                if names == ["codex.api_request"]:
                    if len(endpoints) != 1:
                        raise ValueError("invalid OTLP batch")
                    count += endpoints == ["/responses"]
    return count


class _OtelHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        server = self.server
        if (
            not isinstance(server, _OtelCounterServer)
            or self.path != "/v1/logs"
            or not self.headers.get("Content-Type", "").startswith(
                "application/json"
            )
        ):
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", ""))
            if not 0 < length <= 4 * 1024 * 1024:
                raise ValueError("invalid length")
            value = json.loads(
                self.rfile.read(length),
                object_pairs_hook=_closed_json_object,
                parse_constant=lambda _value: (_ for _ in ()).throw(
                    ValueError("non-standard JSON constant")
                ),
            )
            count = _api_request_count(value)
        except (ValueError, json.JSONDecodeError):
            server.invalid = True
            self.send_error(400)
            return
        server.api_requests += count
        server.batches += 1
        self.send_response(202)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, _format, *_arguments):
        return


@dataclass
class OtelRequestCounter:
    server: _OtelCounterServer

    @property
    def endpoint(self) -> str:
        host, port = self.server.server_address
        return f"http://{host}:{port}/v1/logs"

    @property
    def api_requests(self) -> int:
        return self.server.api_requests

    @property
    def batches(self) -> int:
        return self.server.batches

    @property
    def invalid(self) -> bool:
        return self.server.invalid


@contextmanager
def otel_request_counter() -> Iterator[OtelRequestCounter]:
    server = _OtelCounterServer()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    counter = OtelRequestCounter(server)
    try:
        yield counter
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        if thread.is_alive():
            server.invalid = True


def configure_otel_counter(codex_home: Path, endpoint: str) -> None:
    if not endpoint.startswith("http://127.0.0.1:") or not endpoint.endswith(
        "/v1/logs"
    ):
        raise BenchmarkFailure("otel_counter_invalid")
    config = codex_home / "config.toml"
    previous = config.read_text(encoding="utf-8") if config.exists() else ""
    if "[otel]" in previous:
        raise BenchmarkFailure("otel_counter_config_conflict")
    config.write_text(
        previous
        + (
            "\n[otel]\n"
            'environment = "dev255-runtime-v1"\n'
            "log_user_prompt = false\n"
            f'exporter = {{ otlp-http = {{ endpoint = "{endpoint}", '
            'protocol = "json" } }\n'
            'trace_exporter = "none"\n'
            'metrics_exporter = "none"\n'
        ),
        encoding="utf-8",
        newline="\n",
    )


def controlled_host_environment() -> dict[str, str]:
    return {
        "PATH": os.environ.get("PATH", ""),
        "NO_COLOR": "1",
        "PYTHON_COLORS": "0",
        "PYTHONDONTWRITEBYTECODE": "1",
        "RUST_LOG": "off",
    }


def invoke_with_otel_counter(
    codex,
    *,
    environment: dict[str, str],
    arguments: list[str],
    codex_home: Path,
    timeout_seconds: int = 900,
) -> tuple[bytes, int, int]:
    with otel_request_counter() as counter:
        configure_otel_counter(codex_home, counter.endpoint)
        codex.recheck()
        started = time.monotonic_ns()
        try:
            completed = subprocess.run(
                [str(codex.resolved), *arguments],
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                shell=False,
                timeout=timeout_seconds,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise BenchmarkBlocked("arm_completion_uncertain") from error
        stderr_bytes = discard_classified_codex_stderr(
            completed,
            codex_version=codex.version,
            source_commit=CODEX_SOURCE_COMMIT,
            stdin_nonterminal=True,
        )
        elapsed = time.monotonic_ns() - started
        codex.recheck()
    failure_stage = provider_counter_failure_stage(
        completed.returncode,
        counter_invalid=counter.invalid,
        counter_batches=counter.batches,
    )
    if failure_stage is not None:
        raise ProviderCounterBlocked(failure_stage)
    return completed.stdout, counter.api_requests, elapsed, stderr_bytes


def discard_classified_codex_stderr(
    completed: subprocess.CompletedProcess,
    *,
    codex_version: str,
    source_commit: str,
    stdin_nonterminal: bool,
) -> int:
    value = completed.stderr
    completed.stderr = b""
    if value == b"":
        return 0
    if (
        value == b"Reading additional input from stdin...\n"
        and codex_version == "0.145.0"
        and source_commit == CODEX_SOURCE_COMMIT
        and stdin_nonterminal is True
    ):
        return 39
    raise BenchmarkBlocked("codex_stderr_unclassified")


def invocation_result_is_valid(
    returncode: int,
    *,
    counter_invalid: bool,
    counter_batches: int,
) -> bool:
    return provider_counter_failure_stage(
        returncode,
        counter_invalid=counter_invalid,
        counter_batches=counter_batches,
    ) is None


def provider_counter_failure_stage(
    returncode: object,
    *,
    counter_invalid: object,
    counter_batches: object,
) -> str | None:
    if type(returncode) is not int or returncode != 0:
        return "process_exit"
    if counter_invalid is not False:
        return "telemetry_payload"
    if type(counter_batches) is not int or counter_batches < 1:
        return "telemetry_batch"
    return None


_APPROVED_IDENTITIES = {
    "productionPluginSha256":
        "b9348701fd4892766402f2a6080e4f0251e3645363e0c254ea411d6a2ff451fc",
    "codexManifestSha256":
        "6c10d51db5a08a1531ba3c7964d77a5cf2b258f3ca838b655a5350d901b1927a",
    "hooksManifestSha256":
        "932234483e15c3277376c5b25cae2e63f8c83bc9dd63a77bc02f6fb13dbb6759",
    "pythonAdapterSha256":
        "21710a9f22aa830b262ce46565958a369bf7eb6140bcdf2dacd5b15f5dc33049",
    "swiftSourceSha256":
        "da40e06fa160b106bb6e9ff278aae4422be415c953ae3afba1391614d309e668",
    "corpusSha256":
        "2801e94ba54a65fa7eed7b85a12333446c6ba7b6be3745e40d26979acba4c1c6",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def current_production_identities() -> dict[str, str]:
    return {
        "productionPluginSha256": tree_sha256(PLUGIN),
        "codexManifestSha256": _sha256(PLUGIN / ".codex-plugin/plugin.json"),
        "hooksManifestSha256": _sha256(PLUGIN / "hooks/codex/hooks.json"),
        "pythonAdapterSha256":
            _sha256(PLUGIN / "hooks/codex/diagnostic_condensation.py"),
        "swiftSourceSha256":
            _sha256(PLUGIN / "runtime/DiagnosticCondenser.swift"),
        "corpusSha256": _sha256(CORPUS),
    }


def validate_production_identities(value: object) -> dict[str, str]:
    if (
        type(value) is not dict
        or set(value) != set(_APPROVED_IDENTITIES)
        or any(type(item) is not str or not _DIGEST.fullmatch(item) for item in value.values())
    ):
        raise BenchmarkBlocked("production_identity_unapproved")
    if value != _APPROVED_IDENTITIES:
        raise BenchmarkBlocked("production_identity_unapproved")
    return value


def validate_role_state(
    role: str,
    *,
    installed: bool,
    trusted: bool,
    production_identities: dict[str, str],
) -> None:
    validate_production_identities(production_identities)
    if (
        role not in ("pluginOff", "pluginOn")
        or type(installed) is not bool
        or type(trusted) is not bool
        or (role == "pluginOff" and (installed or trusted))
        or (role == "pluginOn" and (not installed or not trusted))
    ):
        raise BenchmarkBlocked("plugin_role_state_invalid")


def recheck_hook_trust(
    rpc,
    *,
    workspace: Path,
    approved_hook_hash: str,
) -> None:
    value = rpc.call("hooks/list", {"cwds": [str(workspace)]})
    rows = value.get("data") if type(value) is dict else None
    hooks = (
        rows[0].get("hooks")
        if type(rows) is list and len(rows) == 1
        and type(rows[0]) is dict
        else None
    )
    if (
        type(hooks) is not list
        or len(hooks) != 1
        or hooks[0].get("pluginId") != production.PLUGIN_ID
        or hooks[0].get("currentHash") != approved_hook_hash
        or hooks[0].get("trustStatus") != "trusted"
    ):
        raise BenchmarkFailure("hook_identity_drift")


def _real_git(repository: Path, arguments: list[str]) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=repository,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        shell=False,
        timeout=30,
        text=True,
    )
    if completed.returncode != 0 or completed.stderr:
        if arguments[:2] == ["merge-base", "--is-ancestor"]:
            raise BenchmarkBlocked("production_commit_not_contained")
        raise BenchmarkFailure("candidate_identity_drift")
    return completed.stdout


def capture_candidate_identity(
    repository: Path,
    approved_candidate_commit: str,
    *,
    run_git: Callable[[list[str]], str] | None = None,
) -> CandidateIdentity:
    if type(approved_candidate_commit) is not str or not _COMMIT.fullmatch(
        approved_candidate_commit
    ):
        raise BenchmarkBlocked("candidate_identity_unapproved")
    operation = (
        (lambda arguments: _real_git(repository, arguments))
        if run_git is None
        else run_git
    )
    if operation(["rev-parse", "HEAD"]).strip() != approved_candidate_commit:
        raise BenchmarkFailure("candidate_identity_drift")
    if operation(["status", "--porcelain"]) != "":
        raise BenchmarkFailure("candidate_identity_drift")
    try:
        operation(
            [
                "merge-base",
                "--is-ancestor",
                PRODUCTION_COMMIT,
                approved_candidate_commit,
            ]
        )
    except BenchmarkBlocked:
        raise
    except Exception as error:
        raise BenchmarkBlocked("production_commit_not_contained") from error
    captured = CandidateIdentity(
        repository,
        approved_candidate_commit,
        PRODUCTION_COMMIT,
        operation,
    )
    captured.recheck()
    return captured


def _corpus_cases() -> list[dict[str, object]]:
    value = json.loads(CORPUS.read_text(encoding="utf-8"))
    cases = value.get("cases") if type(value) is dict else None
    if (
        type(cases) is not list
        or tuple(case.get("id") for case in cases)
        != contract.EXACT_DEV142_FIXTURE_IDS
    ):
        raise BenchmarkBlocked("corpus_identity_drift")
    return cases


def _task(case: dict[str, object]) -> str:
    command = _command_for_case(case)
    return (
        f"Run the approved direct Bash command {command} exactly once; make "
        "no other tool call. Then return only canonical JSON containing "
        "exactly commandOutcome, summary, summaryFacts, diagnostics, "
        "warningCount, omittedWarningCount, nextAction, and completionFacts. "
        "Derive every value only from the observed tool result."
    )


def _command_for_case(case: dict[str, object]) -> str:
    suffixes = {
        "swiftc -typecheck": " Fixture.swift",
        "swift format lint": " Fixture.swift",
        "python3 -m mypy": " tests",
        "python3 -m ruff check": " tests",
    }
    form = case["commandForm"]
    return form + suffixes.get(form, "")


def fixed_pair_coordinates() -> list[dict[str, str]]:
    rows = []
    for case in _corpus_cases():
        prompt = _task(case)
        rows.append(
            {
                "benchmarkProfile": PROFILE,
                "fixtureID": case["id"],
                "fixtureSha256": case["renderedSha256"],
                "parentModel": "gpt-5.6-sol",
                "reasoningEffort": "medium",
                "provider": "openai-responses-usage-v1",
                "codexVersion": "0.145.0",
                "policyVersion": "diagnostic-condensation-v1",
                "commandClass": case["commandClass"],
                "commandForm": case["commandForm"],
                "taskPromptSha256": hashlib.sha256(prompt.encode()).hexdigest(),
            }
        )
    return rows


def build_exec_arguments(
    workspace: Path,
    transient_output: Path,
    approved_task: str,
) -> list[str]:
    return [
        "exec",
        "--ephemeral",
        "--json",
        "--strict-config",
        "--skip-git-repo-check",
        "--enable",
        "hooks",
        "--disable",
        "code_mode",
        "--disable",
        "code_mode_only",
        "-c",
        'web_search="disabled"',
        "-c",
        'approval_policy="never"',
        "-c",
        'model_reasoning_effort="medium"',
        "-m",
        "gpt-5.6-sol",
        "-s",
        "danger-full-access",
        "--output-last-message",
        str(transient_output),
        "-C",
        str(workspace),
        approved_task,
    ]


def _forwarding_exec_arguments(
    server_url: str,
    workspace: Path,
) -> list[str]:
    arguments = production._exec_arguments(server_url, workspace)
    if arguments.count("-m") != 1:
        raise BenchmarkBlocked("replacement_forwarding_unproven")
    model_index = arguments.index("-m")
    if (
        model_index + 1 >= len(arguments)
        or arguments[model_index + 1] != "gpt-5.1-codex"
        or any(
            re.fullmatch(r"\s*model_reasoning_effort\s*=.*", argument)
            for argument in arguments
        )
    ):
        raise BenchmarkBlocked("replacement_forwarding_unproven")
    arguments[model_index + 1] = "gpt-5.6-sol"
    arguments[model_index:model_index] = [
        "-c", 'model_reasoning_effort="medium"',
    ]
    return arguments


def parse_event_stream(value: bytes) -> ParsedEvents:
    def closed_json(pairs):
        decoded = {}
        for key, child in pairs:
            if key in decoded:
                raise ValueError("duplicate key")
            decoded[key] = child
        return decoded

    command_keys = {
        "id", "type", "command", "aggregated_output",
        "exit_code", "status",
    }
    text_keys = {"id", "type", "text"}
    try:
        lines = value.decode("utf-8").splitlines()
        if not lines or any(not line for line in lines):
            raise ValueError("blank record")
        events = [
            json.loads(
                line,
                object_pairs_hook=closed_json,
                parse_constant=lambda _value: (_ for _ in ()).throw(
                    ValueError("non-standard constant")
                ),
            )
            for line in lines
        ]
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError):
        raise BenchmarkBlocked(
            "provider_usage_schema_or_semantic_drift"
        ) from None
    if not events or any(type(event) is not dict for event in events):
        raise BenchmarkBlocked("provider_usage_schema_or_semantic_drift")
    if (
        set(events[0]) != {"type", "thread_id"}
        or events[0]["type"] != "thread.started"
        or type(events[0]["thread_id"]) is not str
        or not events[0]["thread_id"]
    ):
        raise BenchmarkBlocked("provider_usage_schema_or_semantic_drift")
    terminals = [
        index
        for index, event in enumerate(events)
        if event.get("type") in ("turn.completed", "turn.failed", "error")
    ]
    if (
        len(terminals) != 1
        or terminals[0] != len(events) - 1
        or events[-1].get("type") != "turn.completed"
        or sum(event.get("type") == "turn.started" for event in events) != 1
        or sum(event.get("type") == "thread.started" for event in events) != 1
        or set(events[1]) != {"type"}
        or events[1]["type"] != "turn.started"
        or set(events[-1]) != {"type", "usage"}
    ):
        raise BenchmarkBlocked("provider_usage_schema_or_semantic_drift")
    open_items: dict[str, str] = {}
    seen_items = set()
    command_executions = 0
    final_agent_message = None
    for event in events[2:-1]:
        event_type = event.get("type")
        if (
            event_type not in ("item.started", "item.completed")
            or set(event) != {"type", "item"}
        ):
            raise BenchmarkBlocked("provider_usage_schema_or_semantic_drift")
        item = event["item"]
        if (
            type(item) is not dict
            or type(item.get("id")) is not str
            or re.fullmatch(r"item_[0-9]+", item["id"]) is None
            or type(item.get("type")) is not str
            or item["type"] not in {
                "command_execution", "agent_message", "reasoning"
            }
        ):
            raise BenchmarkBlocked("provider_usage_schema_or_semantic_drift")
        identity = item["id"]
        item_type = item["type"]
        if open_items and not (
            event_type == "item.completed"
            and item_type == "command_execution"
            and identity in open_items
        ):
            raise BenchmarkBlocked("provider_usage_schema_or_semantic_drift")
        if item_type == "command_execution":
            if (
                set(item) != command_keys
                or type(item["command"]) is not str
                or not item["command"]
                or type(item["aggregated_output"]) is not str
            ):
                raise BenchmarkBlocked("provider_usage_schema_or_semantic_drift")
            if event_type == "item.started":
                if (
                    identity in seen_items
                    or item["status"] != "in_progress"
                    or item["aggregated_output"] != ""
                    or item["exit_code"] is not None
                ):
                    raise BenchmarkBlocked(
                        "provider_usage_schema_or_semantic_drift"
                    )
                seen_items.add(identity)
                open_items[identity] = item["command"]
            else:
                if (
                    open_items.get(identity) != item["command"]
                    or item["status"] not in {
                        "completed", "failed", "declined"
                    }
                    or (
                        item["exit_code"] is not None
                        and type(item["exit_code"]) is not int
                    )
                    or (
                        item["status"] == "declined"
                        and item["exit_code"] is not None
                    )
                    or (
                        item["status"] in {"completed", "failed"}
                        and type(item["exit_code"]) is not int
                    )
                ):
                    raise BenchmarkBlocked(
                        "provider_usage_schema_or_semantic_drift"
                    )
                del open_items[identity]
                command_executions += 1
        else:
            if (
                event_type != "item.completed"
                or set(item) != text_keys
                or identity in seen_items
                or type(item["text"]) is not str
                or not item["text"]
            ):
                raise BenchmarkBlocked("provider_usage_schema_or_semantic_drift")
            seen_items.add(identity)
            if item_type == "agent_message":
                final_agent_message = item["text"]
    if open_items or command_executions != 1:
        raise BenchmarkBlocked("provider_usage_schema_or_semantic_drift")
    if (
        final_agent_message is None
        or events[-2].get("type") != "item.completed"
        or events[-2].get("item", {}).get("type") != "agent_message"
    ):
        raise BenchmarkBlocked("provider_usage_schema_or_semantic_drift")
    try:
        usage = contract.normalize_codex_usage(events[-1]["usage"])
    except (KeyError, contract.BlockedEvidence) as error:
        raise BenchmarkBlocked(
            "provider_usage_schema_or_semantic_drift"
        ) from error
    return ParsedEvents(usage, command_executions, 1, final_agent_message)


def _latency(value: int, denominator: int) -> dict[str, int | None]:
    if type(value) is not int or value < 0 or type(denominator) is not int or denominator < 0:
        raise BenchmarkBlocked("invalid_latency")
    return {
        "numeratorNanoseconds": value,
        "denominator": denominator,
        "averageNanoseconds": value // denominator if denominator else None,
    }


def normalized_arm(
    coordinate: dict[str, str],
    role: str,
    observation: ArmObservation,
) -> dict[str, object]:
    parsed = parse_event_stream(observation.event_stream)
    if (
        role not in ("pluginOff", "pluginOn")
        or type(observation.parent_requests) is not int
        or observation.parent_requests != 2
        or parsed.command_executions != 1
        or parsed.completed_parent_turns != 1
        or type(observation.apple_attempts) is not int
        or not 0 <= observation.apple_attempts <= 1
        or (role == "pluginOff" and (observation.apple_attempts or observation.validated_applied))
        or (observation.validated_applied and observation.apple_attempts != 1)
        or type(observation.correctness_passed) is not bool
        or type(observation.stderr_bytes) is not int
        or observation.stderr_bytes not in (0, 39)
        or type(observation.pre_receipt_hook_latency_samples) is not int
        or observation.pre_receipt_hook_latency_samples not in (0, 1)
        or (
            role == "pluginOff"
            and (
                observation.pre_receipt_hook_latency_ns != 0
                or observation.pre_receipt_hook_latency_samples != 0
            )
        )
        or (
            role == "pluginOn"
            and observation.pre_receipt_hook_latency_samples != 1
        )
        or observation.cleanup_complete is not True
    ):
        raise BenchmarkBlocked("arm_invariant_invalid")
    arm = {
        "fixture_id": coordinate["fixtureID"],
        "fixture_sha256": coordinate["fixtureSha256"],
        "arm": role,
        "codex_version": coordinate["codexVersion"],
        "parent_model": coordinate["parentModel"],
        "reasoning_effort": coordinate["reasoningEffort"],
        "provider": coordinate["provider"],
        "provider_normalization": coordinate["provider"],
        "policy_version": coordinate["policyVersion"],
        "command_class": coordinate["commandClass"],
        "command_form": coordinate["commandForm"],
        "task_prompt_sha256": coordinate["taskPromptSha256"],
        "usage": {
            "input_tokens": parsed.usage.input_tokens,
            "cached_input_tokens": parsed.usage.cached_input_tokens,
            "cache_write_input_tokens": parsed.usage.cache_write_input_tokens,
            "output_tokens": parsed.usage.output_tokens,
            "reasoning_output_tokens": parsed.usage.reasoning_output_tokens,
        },
        "parent_requests": observation.parent_requests,
        "completed_parent_turns": parsed.completed_parent_turns,
        "apple_attempts": observation.apple_attempts,
        "validated_applied": observation.validated_applied,
        "command_executions": parsed.command_executions,
        "correctness_passed": observation.correctness_passed,
        "cleanup_complete": observation.cleanup_complete,
    }
    contract.validate_arm(arm)
    return {
        **arm,
        "stderrBytes": observation.stderr_bytes,
        "latency": {
            "parent": _latency(observation.parent_latency_ns, 1),
            "preReceiptHook": _latency(
                observation.pre_receipt_hook_latency_ns,
                observation.pre_receipt_hook_latency_samples,
            ),
            "apple": _latency(
                observation.apple_latency_ns,
                observation.apple_latency_samples,
            ),
        },
    }


def collect_arms(
    coordinates: list[dict[str, str]],
    runner: Callable[[dict[str, str], str], dict[str, object]],
) -> list[dict[str, object]]:
    if [row["fixtureID"] for row in coordinates] != list(
        contract.EXACT_DEV142_FIXTURE_IDS
    ):
        raise BenchmarkBlocked("corpus_identity_drift")
    arms = []
    try:
        for coordinate in coordinates:
            arms.append(runner(coordinate, "pluginOff"))
            arms.append(runner(coordinate, "pluginOn"))
    except KeyboardInterrupt as error:
        raise BenchmarkBlocked("run_cancelled") from error
    return arms


def usage_dry_run_plan(
    coordinates: list[dict[str, str]],
) -> list[tuple[dict[str, str], str]]:
    if not coordinates:
        raise BenchmarkBlocked("corpus_identity_drift")
    return [(coordinates[0], "pluginOff")]


def usage_dry_run_terminal(arms: list[dict[str, object]]) -> dict[str, object]:
    if (
        type(arms) is not list
        or len(arms) != 1
        or type(arms[0].get("stderrBytes")) is not int
        or arms[0]["stderrBytes"] not in (0, 39)
        or type(arms[0].get("parent_requests")) is not int
    ):
        raise BenchmarkBlocked("provider_usage_schema_or_semantic_drift")
    return {
        "status": "usage-dry-run",
        "observedArms": 1,
        "providerRequests": [arms[0]["parent_requests"]],
        "stderrBytes": arms[0]["stderrBytes"],
    }


def _validate_complete_latency(
    value: object,
    *,
    expected_denominator: int,
) -> None:
    if (
        type(value) is not dict
        or set(value) != {
            "numeratorNanoseconds",
            "denominator",
            "averageNanoseconds",
        }
        or type(value["numeratorNanoseconds"]) is not int
        or value["numeratorNanoseconds"] < 0
        or type(value["denominator"]) is not int
        or value["denominator"] != expected_denominator
    ):
        raise BenchmarkFailure("complete_arm_latency_invalid")
    numerator = value["numeratorNanoseconds"]
    average = value["averageNanoseconds"]
    if expected_denominator == 0:
        valid = numerator == 0 and average is None
    else:
        valid = (
            type(average) is int
            and average == numerator // expected_denominator
        )
    if not valid:
        raise BenchmarkFailure("complete_arm_latency_invalid")


def _contract_arm(arm: dict[str, object]) -> dict[str, object]:
    if (
        type(arm) is not dict
        or set(arm) != set(contract._ARM_KEYS) | {"latency"}
        or "stderrBytes" in arm
    ):
        raise BenchmarkFailure("complete_arm_shape_invalid")
    raw = {
        key: deepcopy(value)
        for key, value in arm.items()
        if key != "latency"
    }
    contract.validate_arm(raw)
    latency = arm["latency"]
    if (
        type(latency) is not dict
        or set(latency) != {
            "parent",
            "preReceiptHook",
            "apple",
        }
    ):
        raise BenchmarkFailure("complete_arm_latency_invalid")
    role = raw["arm"]
    _validate_complete_latency(
        latency["parent"],
        expected_denominator=1,
    )
    _validate_complete_latency(
        latency["preReceiptHook"],
        expected_denominator=0 if role == "pluginOff" else 1,
    )
    _validate_complete_latency(
        latency["apple"],
        expected_denominator=raw["apple_attempts"],
    )
    return raw


def _task2_view(arms: list[dict[str, object]]) -> tuple[list[dict[str, object]], dict[str, object]]:
    expected = {
        (fixture, role)
        for fixture in contract.EXACT_DEV142_FIXTURE_IDS
        for role in ("pluginOff", "pluginOn")
    }
    if type(arms) is not list or len(arms) != len(expected):
        raise BenchmarkFailure("arm_matrix_invalid")
    grouped = {}
    observed = set()
    for arm in arms:
        raw = _contract_arm(arm)
        identity = (raw["fixture_id"], raw["arm"])
        if identity not in expected or identity in observed:
            raise BenchmarkFailure("arm_matrix_invalid")
        observed.add(identity)
        grouped.setdefault(raw["fixture_id"], {})[raw["arm"]] = raw
    if observed != expected:
        raise BenchmarkFailure("arm_matrix_invalid")
    pairs = [
        {
            "plugin_off": grouped[fixture]["pluginOff"],
            "plugin_on": grouped[fixture]["pluginOn"],
        }
        for fixture in contract.EXACT_DEV142_FIXTURE_IDS
    ]
    release = contract.release_gate(
        pairs, unsafe_committed_evidence_findings=0
    )
    return pairs, release


def unsafe_evidence_findings(value: object) -> int:
    prohibited = {
        "prompt", "response", "transcript", "toolInput", "toolOutput",
        "appleOutput", "providerBody", "rawEvents", "reasoning",
    }
    private = re.compile(
        r"(?:/Users/|/home/|/private/|"
        r"\b(?:Bearer|password|secret|credential|authorization|api[_ -]?key)\b)",
        re.IGNORECASE,
    )
    findings = 0

    def visit(item):
        nonlocal findings
        if type(item) is dict:
            for key, child in item.items():
                if key in prohibited:
                    findings += 1
                visit(child)
        elif type(item) is list:
            for child in item:
                visit(child)
        elif type(item) is float and not math.isfinite(item):
            findings += 1
        elif type(item) is str and private.search(item):
            findings += 1

    visit(value)
    return findings


def build_evidence(
    arms: list[dict[str, object]],
    *,
    candidate_commit: str,
    production_identities: dict[str, str],
    host: dict[str, object],
) -> dict[str, object]:
    if not _COMMIT.fullmatch(candidate_commit):
        raise BenchmarkFailure("candidate_identity_drift")
    validate_production_identities(production_identities)
    if host != {
        "codexVersion": "0.145.0",
        "codexExecutable": "<host-path>",
    }:
        raise BenchmarkFailure("host_identity_invalid")
    pairs, release = _task2_view(arms)
    pair_scores = [
        contract.score_pair(pair["plugin_off"], pair["plugin_on"])
        for pair in pairs
    ]
    evidence = {
        "schemaVersion": 1,
        "benchmarkProfile": PROFILE,
        "status": release["status"],
        "reasonCodes": release["reason_codes"],
        "candidateCommit": candidate_commit,
        "productionIdentities": production_identities,
        "host": host,
        "usageContract": {
            "codexVersion": "0.145.0",
            "parentModel": "gpt-5.6-sol",
            "reasoningEffort": "medium",
            "terminalEvent": "turn.completed",
            "rawKeys": [
                "input_tokens", "cached_input_tokens",
                "cache_write_input_tokens", "output_tokens",
                "reasoning_output_tokens",
            ],
            "dev142Mapping": {
                "input_tokens": "input_tokens",
                "cached_input_tokens": "cached_tokens",
                "output_tokens": "output_tokens",
                "reasoning_output_tokens": "reasoning_tokens",
            },
            "subsetSemantics": [
                "cached_input_tokens <= input_tokens",
                "cache_write_input_tokens <= input_tokens",
                "reasoning_output_tokens <= output_tokens",
            ],
            "totalFormula": "input_tokens + output_tokens",
        },
        "requiredPairs": 24,
        "requiredArms": 48,
        "observedPairs": len(pairs),
        "observedArms": len(arms),
        "arms": arms,
        "pairs": [
            {**asdict(score), "reason_codes": list(score.reason_codes)}
            for score in pair_scores
        ],
        "release": release,
    }
    findings = unsafe_evidence_findings(evidence)
    if findings:
        raise BenchmarkFailure("unsafe_evidence")
    return evidence


def write_evidence(
    path: Path,
    evidence: dict[str, object],
    *,
    expected_parent_identity: tuple[int, int, int, int] | None = None,
) -> None:
    validate_output_path(path)
    if (
        expected_parent_identity is not None
        and directory_identity(path.parent) != expected_parent_identity
    ):
        raise BenchmarkFailure("output_path_invalid")
    if path.exists():
        raise BenchmarkFailure("resume_rejected")
    if unsafe_evidence_findings(evidence):
        raise BenchmarkFailure("unsafe_evidence")
    try:
        json.dumps(evidence, allow_nan=False)
    except (TypeError, ValueError):
        raise BenchmarkFailure("evidence_shape_invalid") from None
    atomic_write_json(path, evidence)
    if (
        expected_parent_identity is not None
        and directory_identity(path.parent) != expected_parent_identity
    ):
        raise BenchmarkFailure("output_path_invalid")


def validate_outer_evidence(value: object) -> None:
    keys = {
        "schemaVersion", "benchmarkProfile", "status", "reasonCodes",
        "candidateCommit", "productionIdentities", "host", "usageContract",
        "requiredPairs", "requiredArms", "observedPairs", "observedArms",
        "arms", "pairs", "release",
    }
    if type(value) is not dict or set(value) != keys:
        raise BenchmarkFailure("evidence_shape_invalid")
    rebuilt = build_evidence(
        value["arms"],
        candidate_commit=value["candidateCommit"],
        production_identities=value["productionIdentities"],
        host=value["host"],
    )
    if value != rebuilt:
        raise BenchmarkFailure("evidence_derivation_invalid")


def read_outer_evidence(path: Path) -> dict[str, object]:
    try:
        value = json.loads(
            path.read_bytes(),
            object_pairs_hook=_closed_json_object,
            parse_constant=lambda _value: (_ for _ in ()).throw(ValueError()),
        )
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError):
        raise BenchmarkFailure("evidence_shape_invalid") from None
    try:
        if unsafe_evidence_findings(value):
            raise BenchmarkFailure("evidence_shape_invalid")
        validate_outer_evidence(value)
    except BenchmarkFailure:
        raise
    except Exception:
        raise BenchmarkFailure("evidence_shape_invalid") from None
    return value


OUTPUT_PATH = ROOT / "docs/research/evidence/runtime-v1-benchmark.json"
OUTPUT_RELATIVE = Path(
    "docs/research/evidence/runtime-v1-benchmark.json"
)


def directory_identity(path: Path) -> tuple[int, int, int, int]:
    try:
        metadata = path.lstat()
        if (
            path.resolve(strict=True) != path
            or not stat.S_ISDIR(metadata.st_mode)
        ):
            raise OSError
    except OSError:
        raise BenchmarkFailure("output_path_invalid") from None
    return (
        metadata.st_dev,
        metadata.st_ino,
        stat.S_IFMT(metadata.st_mode),
        stat.S_IMODE(metadata.st_mode),
    )


def normalize_output_path(raw: str | Path) -> Path:
    path = Path(raw)
    if path.is_absolute():
        normalized = path
    elif (
        type(raw) is str
        and raw == OUTPUT_RELATIVE.as_posix()
        and path == OUTPUT_RELATIVE
    ):
        normalized = ROOT / path
    else:
        raise BenchmarkFailure("output_path_invalid")
    validate_output_path(normalized)
    return normalized


def validate_output_path(path: Path) -> None:
    if (
        not path.is_absolute()
        or path != OUTPUT_PATH
        or path.exists()
        or path.is_symlink()
        or not path.parent.is_dir()
        or path.parent.resolve(strict=True) != path.parent
    ):
        raise BenchmarkFailure("output_path_invalid")


def _materialize_workspace(
    root: Path,
    case: dict[str, object],
) -> tuple[Path, bytes]:
    workspace = root / "workspace"
    workspace.mkdir()
    (workspace / "tests").mkdir()
    (workspace / "Fixture.swift").write_text("", encoding="utf-8")
    for diagnostic_id in (
        case["expected"]["requiredDiagnosticIDs"]
        + case["expected"]["warningRepresentativeIDs"]
    ):
        diagnostic = contract._DEV142._diagnostic_for_case(
            case,
            diagnostic_id,
        )
        relative = diagnostic["file"]
        if relative is not None:
            target = workspace / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.touch()
    rendered = contract._DEV142.render_case(case)
    fixture = root / "fixture-output"
    fixture.write_bytes(rendered)
    bin_path = root / "bin"
    bin_path.mkdir()
    shim = (
        "#!/usr/bin/python3\n"
        "import os, pathlib, sys\n"
        "sys.stdout.buffer.write(pathlib.Path("
        "os.environ['DEV255_FIXTURE_OUTPUT']).read_bytes())\n"
        "raise SystemExit(int(os.environ['DEV255_FIXTURE_EXIT']))\n"
    )
    for executable in ("swift", "xcodebuild", "python3", "pnpm", "swiftc", "npm"):
        target = bin_path / executable
        target.write_text(shim, encoding="utf-8", newline="\n")
        target.chmod(0o700)
    return workspace, rendered


def _command_result_matches(
    stream: bytes,
    *,
    command: str,
    exit_status: int,
    rendered: bytes,
    rendered_sha256: str,
) -> bool:
    try:
        events = [
            json.loads(line)
            for line in stream.decode("utf-8").splitlines()
        ]
        commands = [
            event["item"]
            for event in events
            if event.get("type") == "item.completed"
            and type(event.get("item")) is dict
            and event["item"].get("type") == "command_execution"
        ]
    except (UnicodeError, json.JSONDecodeError):
        return False
    return (
        len(commands) == 1
        and commands[0].get("command") == command
        and commands[0].get("exit_code") == exit_status
        and type(commands[0].get("aggregated_output")) is str
        and commands[0]["aggregated_output"].encode("utf-8") == rendered
        and hashlib.sha256(rendered).hexdigest() == rendered_sha256
    )


def score_parent_outcome(
    value: bytes,
    *,
    case: dict[str, object],
    coordinate: dict[str, str],
    candidate_commit: str,
    final_agent_message: str,
) -> bool:
    try:
        if (
            len(value)
            > contract._DEV142.Policy.MAXIMUM_CONDENSED_BYTES
            or type(final_agent_message) is not str
            or value.decode("utf-8") != final_agent_message
            or _COMMIT.fullmatch(candidate_commit) is None
            or coordinate["fixtureID"] != case["id"]
            or coordinate["fixtureSha256"] != case["renderedSha256"]
        ):
            return False
        parent = json.loads(
            value,
            object_pairs_hook=_closed_json_object,
            parse_constant=lambda _value: (_ for _ in ()).throw(ValueError()),
        )
        if (
            type(parent) is not dict
            or set(parent) != {
                "commandOutcome", "summary", "summaryFacts", "diagnostics",
                "warningCount", "omittedWarningCount", "nextAction",
                "completionFacts",
            }
        ):
            return False
        canonical = json.dumps(
            parent,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        result = {
            "schemaVersion": 1,
            "policyVersion": "diagnostic-condensation-v1",
            "callID": "parent-outcome",
            "toolName": "Bash",
            "toolVersion": "codex-cli-0.145.0",
            "stateVersion": "runtime-v1-direct-consultation-v1",
            "action": "condense_diagnostic_output",
            "commandClass": case["commandClass"],
            "originalResultType": "string",
            "originalResultDigest": case["renderedSha256"],
            "outcome": "applied",
            "exitStatus": case["expected"]["exitStatus"],
            "interrupted": case["expected"]["interrupted"],
            "resultType": "diagnostic_condensation",
            "condensation": parent,
        }
        contract._DEV142.validate_result(result)
        score = contract._DEV142.score_condensation(case, result)
        outcome_sha = hashlib.sha256(canonical).hexdigest()
        binding = {
            "candidateCommit": candidate_commit,
            "coordinate": coordinate,
            "taskPromptSha256": coordinate["taskPromptSha256"],
            "renderedSha256": case["renderedSha256"],
            "parentOutcomeSha256": outcome_sha,
        }
        binding_sha256 = hashlib.sha256(
            json.dumps(
                binding,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()
        return (
            _DIGEST.fullmatch(binding_sha256) is not None
            and score.passed
            and score.reason_codes == ()
        )
    except (
        UnicodeError,
        ValueError,
        json.JSONDecodeError,
        contract._DEV142.ContractError,
    ):
        return False


_CODE_MODE_INPUT = (
    "try { const result = await tools.exec_command({cmd:"
    + json.dumps(production.helpers.APPROVED_COMMAND, separators=(",", ":"))
    + "}); text(result.output); } catch (error) { text(String(error)); }"
)
_CODE_MODE_COMPLETED = re.compile(
    r"\AScript completed\nWall time [0-9]+\.[0-9] seconds\nOutput:\n\Z"
)


def _code_mode_provider_events(index: int) -> list[dict[str, object]]:
    response_id = f"resp-{index}"
    created = {
        "type": "response.created",
        "response": {"id": response_id},
    }
    if index == 1:
        item = {
            "type": "response.output_item.done",
            "item": {
                "type": "custom_tool_call",
                "call_id": production.helpers.APPROVED_CALL_ID,
                "name": "exec",
                "input": _CODE_MODE_INPUT,
            },
        }
    else:
        item = {
            "type": "response.output_item.done",
            "item": {
                "id": "message-2",
                "type": "message",
                "role": "assistant",
                "content": [{
                    "type": "output_text",
                    "text": "done",
                    "annotations": [],
                }],
            },
        }
    return [created, item, production.helpers._completed(response_id)]


def _custom_tool_output(request: object) -> bytes:
    if type(request) is not dict or type(request.get("input")) is not list:
        raise production.ProbeFailure("provider_request_invalid")
    outputs = [
        item for item in request["input"]
        if type(item) is dict
        and item.get("type") == "custom_tool_call_output"
    ]
    if (
        len(outputs) != 1
        or set(outputs[0]) != {"type", "call_id", "output"}
        or outputs[0].get("call_id") != production.helpers.APPROVED_CALL_ID
    ):
        raise production.ProbeFailure("provider_request_invalid")
    value = outputs[0].get("output")
    if (
        type(value) is not list
        or len(value) != 2
        or any(
            type(item) is not dict
            or set(item) != {"type", "text"}
            or item.get("type") != "input_text"
            or type(item.get("text")) is not str
            for item in value
        )
        or _CODE_MODE_COMPLETED.fullmatch(value[0]["text"]) is None
    ):
        raise production.ProbeFailure("provider_request_invalid")
    return value[1]["text"].encode("utf-8")


def _responses_lite_tools(
    request: object,
) -> tuple[list[object], list[object]]:
    if (
        type(request) is not dict
        or "tools" in request
        or type(request.get("input")) is not list
    ):
        raise production.ProbeFailure("direct_tool_mode_unavailable")
    items = request["input"]
    prefixes = [
        item for item in items
        if type(item) is dict and item.get("type") == "additional_tools"
    ]
    if (
        len(prefixes) != 1
        or not items
        or prefixes[0] is not items[0]
        or set(prefixes[0]) != {"type", "role", "tools"}
        or prefixes[0].get("role") != "developer"
        or type(prefixes[0].get("tools")) is not list
    ):
        raise production.ProbeFailure("direct_tool_mode_unavailable")

    def contains_tool_definitions(value: object) -> bool:
        if type(value) is list:
            return any(contains_tool_definitions(item) for item in value)
        if type(value) is dict:
            return (
                "tools" in value
                or value.get("type") == "additional_tools"
                or any(contains_tool_definitions(item) for item in value.values())
            )
        return False

    if any(contains_tool_definitions(item) for item in items[1:]):
        raise production.ProbeFailure("direct_tool_mode_unavailable")
    return prefixes[0]["tools"], items


def _require_code_mode_exec_requests(
    requests: list[dict[str, object]],
) -> None:
    if len(requests) != 2:
        raise production.ProbeFailure("provider_request_invalid")
    calls = []
    outputs = []
    for index, request in enumerate(requests):
        tools, items = _responses_lite_tools(request)
        named_tools = [
            tool for tool in tools
            if type(tool) is dict and type(tool.get("name")) is str
        ]
        exec_tools = [
            tool for tool in named_tools if tool["name"] == "exec"
        ]
        if (
            len(exec_tools) != 1
            or exec_tools[0].get("type") != "custom"
            or any(
                tool["name"] in {"exec_command", "shell_command"}
                for tool in named_tools
            )
        ):
            raise production.ProbeFailure("direct_tool_mode_unavailable")
        if any(
            type(item) is dict
            and item.get("type") in {"function_call", "function_call_output"}
            for item in items
        ):
            raise production.ProbeFailure("direct_tool_mode_unavailable")
        request_calls = [
            item for item in items
            if type(item) is dict and item.get("type") == "custom_tool_call"
        ]
        request_outputs = [
            item for item in items
            if type(item) is dict
            and item.get("type") == "custom_tool_call_output"
        ]
        if index == 0 and (request_calls or request_outputs):
            raise production.ProbeFailure("direct_tool_mode_unavailable")
        calls.extend(request_calls)
        outputs.extend(request_outputs)
    if (
        len(calls) != 1
        or set(calls[0]) != {"type", "call_id", "name", "input"}
        or calls[0].get("call_id") != production.helpers.APPROVED_CALL_ID
        or calls[0].get("name") != "exec"
        or calls[0].get("input") != _CODE_MODE_INPUT
        or len(outputs) != 1
    ):
        raise production.ProbeFailure("direct_tool_mode_unavailable")
    if [
        item for item in requests[1]["input"]
        if type(item) is dict
        and item.get("type") in {
            "custom_tool_call", "custom_tool_call_output",
        }
    ] != [calls[0], outputs[0]]:
        raise production.ProbeFailure("direct_tool_mode_unavailable")
    _custom_tool_output(requests[1])


def _sole_forwarded_custom_tool_output(
    first_request: object,
    second_request: object,
    *,
    original: bytes,
) -> bytes:
    if type(first_request) is not dict or type(second_request) is not dict:
        raise BenchmarkBlocked("replacement_forwarding_unproven")
    first_items = first_request.get("input")
    second_items = second_request.get("input")
    if type(first_items) is not list or type(second_items) is not list:
        raise BenchmarkBlocked("replacement_forwarding_unproven")
    first_outputs = [
        item for item in first_items
        if type(item) is dict and item.get("type") == "custom_tool_call_output"
    ]
    second_outputs = [
        item for item in second_items
        if type(item) is dict and item.get("type") == "custom_tool_call_output"
    ]
    if first_outputs or len(second_outputs) != 1:
        raise BenchmarkBlocked("replacement_forwarding_unproven")
    forwarded = _custom_tool_output(second_request)
    try:
        original_text = original.decode("utf-8")
    except UnicodeError:
        raise BenchmarkBlocked("replacement_forwarding_unproven") from None

    def contains_original(value: object) -> bool:
        if type(value) is str:
            return original_text in value
        if type(value) is list:
            return any(contains_original(child) for child in value)
        if type(value) is dict:
            return any(
                contains_original(key) or contains_original(child)
                for key, child in value.items()
            )
        return False

    if contains_original(second_request):
        raise BenchmarkBlocked("replacement_forwarding_unproven")
    return forwarded


@contextmanager
def isolated_arm_root() -> Iterator[Path]:
    root = Path(
        tempfile.mkdtemp(prefix="dev255-runtime-v1-")
    ).resolve()
    try:
        yield root
    finally:
        try:
            shutil.rmtree(root)
        except OSError:
            raise BenchmarkBlocked("cleanup_incomplete") from None
        if root.exists():
            raise BenchmarkBlocked("cleanup_incomplete")


def _execute_forwarding_preflight(
    *,
    codex,
    python,
    candidate_commit: str,
    production_identities: dict[str, str],
    approved_hook_hash: str,
    _failure_state: _ForwardingFailureState,
) -> ForwardingProof:
    pending = None
    _failure_state.enter("preflight_setup")
    with isolated_arm_root() as root:
        _failure_state.enter("identity_trust")
        staged = root / "staged-plugin"
        shutil.copytree(PLUGIN, staged, symlinks=False)
        environment, installed = install_plugin(
            codex,
            staged,
            root,
            python.resolved,
        )
        workspace = root / "workspace"
        production.materialize_workspace(workspace, classification="C0")
        with production.JsonRpcProcess(codex.resolved, environment) as rpc:
            trust_hook(
                rpc,
                cwd=workspace,
                plugin_id=production.PLUGIN_ID,
                approved_hash=approved_hook_hash,
            )
        _failure_state.enter("preflight_setup")
        bridge = root / "synthetic-bridge"
        bridge.write_text(
            f"#!{python.resolved}\n"
            "import json, sys\n"
            "request = json.load(sys.stdin)\n"
            "json.dump({\n"
            " 'status': 'applied', 'reasonCode': None,\n"
            " 'appleAvailable': True, 'localeSupported': True,\n"
            " 'contextSize': 32768, 'occupiedTokens': 4096,\n"
            " 'appleAttempts': 1,\n"
            " 'condensation': request['sourceFacts'],\n"
            "}, sys.stdout, separators=(',', ':'), sort_keys=True)\n"
            "sys.stdout.write('\\n')\n",
            encoding="utf-8",
            newline="\n",
        )
        bridge.chmod(0o700)
        observation_directory = workspace / ".runtime-v1-observation"
        observation_directory.mkdir()
        observation_path = (
            observation_directory / "runtime-v1-observation.json"
        )
        command_counter = root / "command-counter"
        row_environment = {
            **controlled_host_environment(),
            **environment,
            "RUNTIME_V1_BRIDGE_EXECUTABLE": str(bridge),
            "RUNTIME_V1_REPO_ROOT": str(workspace),
            "RUNTIME_V1_BENCHMARK_OBSERVATION_PATH":
                str(observation_path),
            "DEV254_PROBE_PROVIDER_KEY": "local-forwarding-preflight",
            "DEV254_PROBE_COMMAND_COUNTER": str(command_counter),
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        with production.responses_server(
            event_factory=_code_mode_provider_events,
        ) as server:
            host, port = server.server_address
            _failure_state.enter("process_execution")
            completed = subprocess.run(
                [
                    str(codex.resolved),
                    *_forwarding_exec_arguments(
                        f"http://{host}:{port}",
                        workspace,
                    ),
                ],
                env=row_environment,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                shell=False,
                timeout=90,
            )
            _failure_state.enter("provider_teardown")
        _failure_state.enter("process_stderr")
        discard_classified_codex_stderr(
            completed,
            codex_version=codex.version,
            source_commit=CODEX_SOURCE_COMMIT,
            stdin_nonterminal=True,
        )
        _failure_state.enter("process_exit")
        if completed.returncode != 0:
            raise BenchmarkBlocked("replacement_forwarding_unproven")
        _failure_state.enter("jsonl")
        parsed = parse_event_stream(completed.stdout)
        original = b""
        forwarded = b""
        try:
            _failure_state.enter("request_count")
            if len(server.requests) != 2:
                raise BenchmarkBlocked("replacement_forwarding_unproven")
            _failure_state.enter("direct_tool_contract")
            try:
                _require_code_mode_exec_requests(server.requests)
            except production.ProbeFailure as error:
                if error.args == ("provider_request_invalid",):
                    _failure_state.enter("function_output")
                elif error.args != ("direct_tool_mode_unavailable",):
                    _failure_state.leave()
                raise
            except Exception:
                _failure_state.leave()
                raise
            _failure_state.enter("command_counter_presence")
            if not command_counter.is_file():
                raise BenchmarkBlocked("replacement_forwarding_unproven")
            _failure_state.enter("command_counter_value")
            if command_counter.read_text(encoding="utf-8") != "1":
                raise BenchmarkBlocked("replacement_forwarding_unproven")
            _failure_state.enter("original_exclusion")
            original = production.stimulus_bytes("C0")
            forwarded = _sole_forwarded_custom_tool_output(
                server.requests[0],
                server.requests[1],
                original=original,
            )
            _failure_state.enter("receipt")
            observation = consume_runtime_v1_observation(observation_path)
            if (
                observation["status"] != "replacement_emitted"
                or observation["replacementEmitted"] is not True
                or len(forwarded) != observation["replacementBytes"]
                or hashlib.sha256(forwarded).hexdigest()
                != observation["replacementSha256"]
                or hashlib.sha256(original).hexdigest()
                == hashlib.sha256(forwarded).hexdigest()
                or original in forwarded
            ):
                raise BenchmarkBlocked("replacement_forwarding_unproven")
            _failure_state.leave()
        finally:
            server.requests.clear()
            forwarded = b""
            original = b""
        _failure_state.enter("observation_cleanup")
        observation_path.unlink()
        observation_directory.rmdir()
        _failure_state.enter("identity_trust")
        codex.recheck()
        python.recheck()
        if (
            tree_sha256(installed)
            != production_identities["productionPluginSha256"]
            or current_production_identities() != production_identities
        ):
            raise BenchmarkBlocked("replacement_forwarding_unproven")
        with production.JsonRpcProcess(codex.resolved, environment) as rpc:
            recheck_hook_trust(
                rpc,
                workspace=workspace,
                approved_hook_hash=approved_hook_hash,
            )
        _failure_state.leave()
        pending = ForwardingProof(
            "pass",
            candidate_commit,
            "0.145.0",
            CODEX_SOURCE_COMMIT,
            production_identities["productionPluginSha256"],
            approved_hook_hash,
            production_identities["pythonAdapterSha256"],
        )
    _failure_state.enter("identity_trust")
    validate_forwarding_proof(
        pending,
        candidate_commit=candidate_commit,
        production_identities=production_identities,
        approved_hook_hash=approved_hook_hash,
    )
    _failure_state.leave()
    return pending


def run_forwarding_preflight(**arguments) -> ForwardingProof:
    failure_state = _ForwardingFailureState()
    failure_stage = None
    try:
        return _execute_forwarding_preflight(
            **arguments,
            _failure_state=failure_state,
        )
    except BenchmarkBlocked as error:
        if str(error) == "cleanup_incomplete":
            raise
        failure_stage = (
            failure_state.stage or "unexpected_exception"
        )
    except Exception:
        failure_stage = failure_state.stage or "unexpected_exception"
    raise ForwardingPreflightBlocked(failure_stage)


def blocked_terminal(error: BenchmarkBlocked) -> dict[str, object]:
    terminal: dict[str, object] = {
        "status": "blocked",
        "reasonCodes": [str(error)],
    }
    if isinstance(error, (ForwardingPreflightBlocked, ProviderCounterBlocked)):
        terminal["failureStage"] = error.failure_stage
    return terminal


def _execute_benchmark_arm(
    coordinate: dict[str, str],
    role: str,
    *,
    codex,
    python,
    approved_hook_hash: str,
    production_identities: dict[str, str],
    candidate_commit: str,
    forwarding_proof: ForwardingProof,
) -> dict[str, object]:
    validate_forwarding_proof(
        forwarding_proof,
        candidate_commit=candidate_commit,
        production_identities=production_identities,
        approved_hook_hash=approved_hook_hash,
    )
    case = next(
        row for row in _corpus_cases()
        if row["id"] == coordinate["fixtureID"]
    )
    pending = None
    with isolated_arm_root() as root:
        workspace, rendered = _materialize_workspace(root, case)
        command = _command_for_case(case)
        output = root / "parent-output"
        environment = controlled_host_environment()
        environment.update(
            {
                "PATH": f"{root / 'bin'}:{environment.get('PATH', '')}",
                "PYTHONDONTWRITEBYTECODE": "1",
                "DEV255_FIXTURE_OUTPUT": str(root / "fixture-output"),
                "DEV255_FIXTURE_EXIT": str(case["expected"]["exitStatus"]),
            }
        )
        observation_path = None
        observation = None
        installed = None
        sdk_identity = None
        if role == "pluginOff":
            codex_home = root / "codex-home"
            codex_home.mkdir()
            environment["CODEX_HOME"] = str(codex_home)
            validate_role_state(
                role,
                installed=False,
                trusted=False,
                production_identities=production_identities,
            )
        else:
            staged = root / "staged-plugin"
            shutil.copytree(PLUGIN, staged, symlinks=False)
            if tree_sha256(staged) != production_identities["productionPluginSha256"]:
                raise BenchmarkFailure("staged_plugin_drift")
            installed_environment, installed = install_plugin(
                codex, staged, root, python.resolved
            )
            environment.update(installed_environment)
            environment["PATH"] = (
                f"{root / 'bin'}:{installed_environment.get('PATH', '')}"
            )
            if tree_sha256(installed) != production_identities["productionPluginSha256"]:
                raise BenchmarkFailure("installed_plugin_drift")
            with production.JsonRpcProcess(codex.resolved, environment) as rpc:
                trust_hook(
                    rpc,
                    cwd=workspace,
                    plugin_id=production.PLUGIN_ID,
                    approved_hash=approved_hook_hash,
                )
            bridge_stage = root / "bridge-plugin"
            shutil.copytree(PLUGIN, bridge_stage, symlinks=False)
            locator, sdk, sdk_snapshot = production.capture_sdk()
            sdk_identity = (locator, sdk, sdk_snapshot)
            bridge = production.compile_bridge(bridge_stage, xcrun=sdk)
            observation_directory = workspace / ".runtime-v1-observation"
            observation_directory.mkdir()
            observation_path = (
                observation_directory / "runtime-v1-observation.json"
            )
            environment.update(
                {
                    "RUNTIME_V1_BRIDGE_EXECUTABLE": str(bridge),
                    "RUNTIME_V1_REPO_ROOT": str(workspace),
                    "RUNTIME_V1_BENCHMARK_OBSERVATION_PATH":
                        str(observation_path),
                }
            )
            validate_role_state(
                role,
                installed=True,
                trusted=True,
                production_identities=production_identities,
            )
        stream, requests, parent_latency, stderr_bytes = invoke_with_otel_counter(
            codex,
            environment=environment,
            arguments=build_exec_arguments(
                workspace,
                output,
                _task(case),
            ),
            codex_home=Path(environment["CODEX_HOME"]),
        )
        if stderr_bytes not in {0, 39}:
            raise BenchmarkBlocked("codex_stderr_unclassified")
        parsed = parse_event_stream(stream)
        if not output.is_file() or not _command_result_matches(
            stream,
            command=command,
            exit_status=case["expected"]["exitStatus"],
            rendered=rendered,
            rendered_sha256=case["renderedSha256"],
        ):
            raise BenchmarkFailure("correctness_oracle_failed")
        if observation_path is None:
            apple_attempts = 0
            replacement_emitted = False
            pre_receipt_hook_latency = 0
            apple_latency = 0
            apple_samples = 0
        else:
            observation = consume_runtime_v1_observation(observation_path)
            apple_attempts = observation["appleAttempts"]
            replacement_emitted = (
                observation["status"] == "replacement_emitted"
                and observation["replacementEmitted"] is True
            )
            pre_receipt_hook_latency = observation[
                "preReceiptHookLatencyNanoseconds"
            ]
            apple_latency = observation["appleLatencyNanoseconds"] or 0
            apple_samples = observation["appleLatencySamples"]
            observation_path.unlink()
            observation_path.parent.rmdir()
        correctness_passed = score_parent_outcome(
            output.read_bytes(),
            case=case,
            coordinate=coordinate,
            candidate_commit=candidate_commit,
            final_agent_message=parsed.final_agent_message,
        )
        if not correctness_passed:
            raise BenchmarkFailure("correctness_oracle_failed")
        validated_applied = derive_validated_applied(
            role=role,
            replacement_emitted=replacement_emitted,
            apple_attempts=apple_attempts,
            parent_requests=requests,
            completed_parent_turns=parsed.completed_parent_turns,
            command_executions=parsed.command_executions,
            correctness_passed=correctness_passed,
            forwarding_preflight_passed=True,
        )
        codex.recheck()
        python.recheck()
        if current_production_identities() != production_identities:
            raise BenchmarkFailure("production_identity_drift")
        if installed is not None:
            if tree_sha256(installed) != production_identities[
                "productionPluginSha256"
            ]:
                raise BenchmarkFailure("installed_plugin_drift")
            with production.JsonRpcProcess(
                codex.resolved,
                environment,
            ) as rpc:
                recheck_hook_trust(
                    rpc,
                    workspace=workspace,
                    approved_hook_hash=approved_hook_hash,
                )
        if sdk_identity is not None:
            production.recheck_sdk(*sdk_identity)
        pending = ArmObservation(
            event_stream=stream,
            parent_requests=requests,
            apple_attempts=apple_attempts,
            validated_applied=validated_applied,
            correctness_passed=correctness_passed,
            parent_latency_ns=parent_latency,
            pre_receipt_hook_latency_ns=pre_receipt_hook_latency,
            pre_receipt_hook_latency_samples=(
                0 if role == "pluginOff" else 1
            ),
            apple_latency_ns=apple_latency,
            apple_latency_samples=apple_samples,
            stderr_bytes=stderr_bytes,
            cleanup_complete=False,
        )
    if pending is None:
        raise BenchmarkBlocked("cleanup_incomplete")
    return normalized_arm(
        coordinate,
        role,
        replace(pending, cleanup_complete=True),
    )


def _run_benchmark_arm(*arguments, **keywords) -> dict[str, object]:
    try:
        return _execute_benchmark_arm(*arguments, **keywords)
    except (BenchmarkBlocked, BenchmarkFailure):
        raise
    except production.ProbeBlocked:
        raise BenchmarkBlocked("production_prerequisite_blocked") from None
    except production.ProbeFailure:
        raise BenchmarkFailure("production_identity_drift") from None
    except OSError:
        raise BenchmarkBlocked("arm_completion_uncertain") from None


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--codex-executable")
    parser.add_argument("--python-executable")
    parser.add_argument("--approved-production-commit")
    parser.add_argument("--approved-candidate-commit")
    parser.add_argument("--approved-plugin-sha256")
    parser.add_argument("--approved-hook-hash")
    parser.add_argument("--through", choices=("usage-dry-run", "complete"))
    parser.add_argument("--output")
    parser.add_argument("--validate-evidence")
    return parser


def capture_hosts(codex_path: Path, python_path: Path):
    try:
        return capture_codex(codex_path), capture_python(python_path)
    except production.ProbeBlocked:
        raise BenchmarkBlocked("host_prerequisite_unavailable") from None
    except production.ProbeFailure:
        raise BenchmarkFailure("host_identity_drift") from None
    except (OSError, ValueError):
        raise BenchmarkBlocked("host_prerequisite_unavailable") from None


def recheck_hosts(codex, python) -> None:
    try:
        codex.recheck()
        python.recheck()
    except production.ProbeBlocked:
        raise BenchmarkBlocked("host_prerequisite_unavailable") from None
    except production.ProbeFailure:
        raise BenchmarkFailure("host_identity_drift") from None
    except (OSError, ValueError):
        raise BenchmarkFailure("host_identity_drift") from None


def main(argv: list[str] | None = None) -> int:
    options = _parser().parse_args(argv)
    if options.validate_evidence:
        value = read_outer_evidence(Path(options.validate_evidence))
        print(json.dumps({"status": value["status"], "reasonCodes": value["reasonCodes"]}, sort_keys=True))
        return 0
    required = (
        options.codex_executable,
        options.python_executable,
        options.approved_production_commit,
        options.approved_candidate_commit,
        options.approved_plugin_sha256,
        options.approved_hook_hash,
        options.through,
    )
    if any(value is None for value in required):
        raise BenchmarkBlocked("missing_required_option")
    if options.approved_production_commit != PRODUCTION_COMMIT:
        raise BenchmarkBlocked("production_commit_unapproved")
    candidate = capture_candidate_identity(
        ROOT,
        options.approved_candidate_commit,
    )
    codex, python = capture_hosts(
        Path(options.codex_executable),
        Path(options.python_executable),
    )
    identities = validate_production_identities(current_production_identities())
    if options.approved_plugin_sha256 != identities["productionPluginSha256"]:
        raise BenchmarkBlocked("plugin_identity_unapproved")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", options.approved_hook_hash):
        raise BenchmarkBlocked("hook_identity_unapproved")
    recheck_hosts(codex, python)
    coordinates = fixed_pair_coordinates()
    forwarding_proof = run_forwarding_preflight(
        codex=codex,
        python=python,
        candidate_commit=options.approved_candidate_commit,
        production_identities=identities,
        approved_hook_hash=options.approved_hook_hash,
    )
    candidate.recheck()

    def run_arm(coordinate, role):
        candidate.recheck()
        result = _run_benchmark_arm(
            coordinate,
            role,
            codex=codex,
            python=python,
            approved_hook_hash=options.approved_hook_hash,
            production_identities=identities,
            candidate_commit=options.approved_candidate_commit,
            forwarding_proof=forwarding_proof,
        )
        candidate.recheck()
        recheck_hosts(codex, python)
        if options.through == "complete":
            result.pop("stderrBytes")
        return result

    if options.through == "usage-dry-run":
        if options.output is not None:
            raise BenchmarkFailure("output_path_invalid")
        arms = [
            run_arm(coordinate, role)
            for coordinate, role in usage_dry_run_plan(coordinates)
        ]
        print(
            json.dumps(
                usage_dry_run_terminal(arms),
                sort_keys=True,
            )
        )
        return 0
    if options.output is None:
        raise BenchmarkFailure("output_path_invalid")
    output = normalize_output_path(options.output)
    output_parent_identity = directory_identity(output.parent)
    arms = collect_arms(coordinates, run_arm)
    candidate.recheck()
    evidence = build_evidence(
        arms,
        candidate_commit=options.approved_candidate_commit,
        production_identities=identities,
        host={
            "codexVersion": "0.145.0",
            "codexExecutable": "<host-path>",
        },
    )
    candidate.recheck()
    write_evidence(
        output,
        evidence,
        expected_parent_identity=output_parent_identity,
    )
    if _real_git(ROOT, ["rev-parse", "HEAD"]).strip() != candidate.candidate_commit:
        raise BenchmarkFailure("candidate_identity_drift")
    expected_status = f"?? {output.relative_to(ROOT)}\n"
    if _real_git(ROOT, ["status", "--porcelain"]) != expected_status:
        raise BenchmarkFailure("candidate_identity_drift")
    read_outer_evidence(output)
    print(
        json.dumps(
            {
                "status": evidence["status"],
                "reasonCodes": evidence["reasonCodes"],
                "output": str(output.relative_to(ROOT)),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BenchmarkBlocked as error:
        print(json.dumps(blocked_terminal(error), sort_keys=True))
        raise SystemExit(2)
    except BenchmarkFailure as error:
        print(json.dumps({"status": "fail", "reasonCodes": [str(error)]}, sort_keys=True))
        raise SystemExit(1)
    except production.ProbeBlocked:
        print(json.dumps({"status": "blocked", "reasonCodes": ["host_prerequisite_unavailable"]}, sort_keys=True))
        raise SystemExit(2)
    except production.ProbeFailure:
        print(json.dumps({"status": "fail", "reasonCodes": ["host_identity_drift"]}, sort_keys=True))
        raise SystemExit(1)
