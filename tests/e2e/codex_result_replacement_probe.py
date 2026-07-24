#!/usr/bin/env python3
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
from typing import Callable, Iterable, Iterator


VERSION_LINE = b"codex-cli 0.145.0\n"
MARKETPLACE_NAME = "dev-246-synthetic"
PLUGIN_NAME = "dev-246-result-replacement-probe"
PLUGIN_SELECTOR = f"{PLUGIN_NAME}@{MARKETPLACE_NAME}"
DIRECT_BOUNDARY_SOURCE = "provider_next_request"
NON_BOUNDARY_SOURCES = frozenset(
    {"hook_stdout", "system_message", "transcript", "model_response", None}
)
ORIGINAL_SENTINEL = b"DEV246_ORIGINAL_SENTINEL_7f21"
COMPACT_SENTINEL = b"DEV246_COMPACT_SENTINEL_9ac4"
OFFICIAL_MANUAL_SHA256 = (
    "6cff0c5701d5a8b10ae497b5dda6ee70f478518d4fa029558168ee2bcc18918b"
)
POST_TOOL_USE_UNSUPPORTED_MARKERS = (
    b"`suppressOutput` | Parsed today but not yet implemented",
    b"`suppressOutput` is parsed but not currently supported for that event",
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
HostSnapshot = tuple[int, int, int, int, int, int, int]


class ProbeBlocked(Exception):
    pass


class ProbeFailure(Exception):
    pass


def _snapshot(metadata: os.stat_result) -> HostSnapshot:
    return (
        metadata.st_dev,
        metadata.st_ino,
        stat.S_IFMT(metadata.st_mode),
        stat.S_IMODE(metadata.st_mode),
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def _strict_version(executable: Path, environment: dict[str, str]) -> bool:
    try:
        completed = subprocess.run(
            [str(executable), "--version"],
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            shell=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return (
        completed.returncode == 0
        and completed.stderr == b""
        and completed.stdout == VERSION_LINE
    )


def _regular_file_bytes(path: Path, reason: str) -> bytes:
    try:
        metadata = path.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            raise ProbeBlocked(reason)
        return path.read_bytes()
    except ProbeBlocked:
        raise
    except OSError:
        raise ProbeBlocked(reason) from None


def _plugin_files(root: Path) -> Iterable[tuple[str, bytes]]:
    try:
        metadata = root.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise ProbeBlocked("synthetic_plugin_unavailable")
        paths = sorted(root.rglob("*"), key=lambda path: path.relative_to(root).as_posix())
        if not paths:
            raise ProbeBlocked("synthetic_plugin_unavailable")
        for path in paths:
            child_metadata = path.lstat()
            if stat.S_ISLNK(child_metadata.st_mode):
                raise ProbeBlocked("synthetic_plugin_unavailable")
            if stat.S_ISREG(child_metadata.st_mode):
                yield path.relative_to(root).as_posix(), path.read_bytes()
            elif not stat.S_ISDIR(child_metadata.st_mode):
                raise ProbeBlocked("synthetic_plugin_unavailable")
    except ProbeBlocked:
        raise
    except OSError:
        raise ProbeBlocked("synthetic_plugin_unavailable") from None


def _tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    found = False
    for relative, content in _plugin_files(root):
        found = True
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(len(content)).encode("ascii"))
        digest.update(b"\0")
        digest.update(content)
        digest.update(b"\0")
    if not found:
        raise ProbeBlocked("synthetic_plugin_unavailable")
    return digest.hexdigest()


class HostCapture:
    __slots__ = (
        "codex_version",
        "environment",
        "executable",
        "manual_bytes",
        "manual_sha256",
        "normalized_executable",
        "plugin_sha256",
        "resolved",
        "snapshot",
    )

    def __init__(
        self,
        *,
        executable: Path,
        resolved: Path,
        snapshot: HostSnapshot,
        environment: dict[str, str],
        manual_bytes: bytes,
        manual_sha256: str,
        plugin_sha256: str,
    ) -> None:
        self.codex_version = "0.145.0"
        self.environment = environment
        self.executable = executable
        self.manual_bytes = manual_bytes
        self.manual_sha256 = manual_sha256
        self.normalized_executable = "<host-path>"
        self.plugin_sha256 = plugin_sha256
        self.resolved = resolved
        self.snapshot = snapshot

    def recheck(self) -> None:
        reason = "host_resolution_or_version_drift"
        try:
            current_resolved = self.executable.resolve(strict=True)
            current_metadata = current_resolved.stat()
        except OSError:
            raise ProbeFailure(reason) from None
        if (
            current_resolved != self.resolved
            or not stat.S_ISREG(current_metadata.st_mode)
            or _snapshot(current_metadata) != self.snapshot
            or not os.access(self.executable, os.X_OK)
        ):
            raise ProbeFailure(reason)
        if not _strict_version(self.resolved, self.environment):
            raise ProbeFailure(reason)
        try:
            final_resolved = self.executable.resolve(strict=True)
            final_metadata = final_resolved.stat()
        except OSError:
            raise ProbeFailure(reason) from None
        if final_resolved != self.resolved or _snapshot(final_metadata) != self.snapshot:
            raise ProbeFailure(reason)


def capture_preflight(
    codex_executable: Path,
    manual: Path,
    plugin: Path,
) -> HostCapture:
    try:
        resolved = codex_executable.resolve(strict=True)
        metadata = resolved.stat()
    except OSError:
        raise ProbeBlocked("missing_binary_or_version_mismatch") from None
    if (
        not stat.S_ISREG(metadata.st_mode)
        or not os.access(codex_executable, os.X_OK)
    ):
        raise ProbeBlocked("missing_binary_or_version_mismatch")

    snapshot = _snapshot(metadata)
    environment = {"PATH": os.environ.get("PATH", "")}
    if not _strict_version(resolved, environment):
        try:
            if (
                codex_executable.resolve(strict=True) != resolved
                or _snapshot(resolved.stat()) != snapshot
            ):
                raise ProbeFailure("host_resolution_or_version_drift")
        except OSError:
            raise ProbeFailure("host_resolution_or_version_drift") from None
        raise ProbeBlocked("missing_binary_or_version_mismatch")
    try:
        if (
            codex_executable.resolve(strict=True) != resolved
            or _snapshot(resolved.stat()) != snapshot
        ):
            raise ProbeFailure("host_resolution_or_version_drift")
    except OSError:
        raise ProbeFailure("host_resolution_or_version_drift") from None

    manual_bytes = _regular_file_bytes(manual, "official_manual_unavailable")
    manual_sha256 = hashlib.sha256(manual_bytes).hexdigest()
    plugin_sha256 = _tree_sha256(plugin)
    return HostCapture(
        executable=codex_executable,
        resolved=resolved,
        snapshot=snapshot,
        environment=environment,
        manual_bytes=manual_bytes,
        manual_sha256=manual_sha256,
        plugin_sha256=plugin_sha256,
    )


def inspect_model_boundary(
    *,
    boundary_source: str | None,
    request_items: Iterable[bytes] | None,
    original_sha256: str,
    compact_sha256: str,
    additional_parent_model_turns: int,
    hook_invocations: int,
) -> dict[str, object]:
    if boundary_source in NON_BOUNDARY_SOURCES:
        if request_items is not None and boundary_source is None:
            raise ProbeFailure("boundary_source_missing")
        original_absent: bool | None = None
        compact_present: bool | None = None
    elif boundary_source == DIRECT_BOUNDARY_SOURCE:
        if request_items is None:
            raise ProbeFailure("direct_boundary_missing")
        observed_hashes: set[str] = set()
        for item in request_items:
            if not isinstance(item, bytes):
                raise ProbeFailure("direct_boundary_item_invalid")
            observed_hashes.add(hashlib.sha256(item).hexdigest())
        original_absent = original_sha256 not in observed_hashes
        compact_present = compact_sha256 in observed_hashes
    else:
        raise ProbeFailure("boundary_source_invalid")
    return {
        "boundarySource": boundary_source,
        "originalAbsentFromNextRequest": original_absent,
        "compactPresentInNextRequest": compact_present,
        "additionalParentModelTurns": additional_parent_model_turns,
        "hookInvocations": hook_invocations,
    }


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _materialize_marketplace(plugin: Path, marketplace: Path) -> None:
    destination = marketplace / "plugins" / PLUGIN_NAME
    destination.parent.mkdir(parents=True)
    try:
        shutil.copytree(plugin, destination, symlinks=False)
    except OSError:
        raise ProbeFailure("marketplace_materialization_failed") from None
    _write_json(
        marketplace / ".claude-plugin" / "marketplace.json",
        {
            "name": MARKETPLACE_NAME,
            "owner": {"name": "DEV-246 synthetic probe"},
            "plugins": [
                {
                    "description": "Synthetic result-replacement capability probe.",
                    "name": PLUGIN_NAME,
                    "source": f"./plugins/{PLUGIN_NAME}",
                    "version": "0.0.1",
                }
            ],
        },
    )
    _write_json(
        marketplace / "metadata" / "codex-marketplace.json",
        {
            "interface": {"displayName": "DEV-246 synthetic marketplace"},
            "name": MARKETPLACE_NAME,
            "plugins": [
                {
                    "category": "Developer Tools",
                    "name": PLUGIN_NAME,
                    "policy": {
                        "authentication": "ON_INSTALL",
                        "installation": "AVAILABLE",
                    },
                    "source": {
                        "path": f"./plugins/{PLUGIN_NAME}",
                        "source": "local",
                    },
                }
            ],
        },
    )


def _run_json(
    executable: Path,
    arguments: list[str],
    environment: dict[str, str],
    reason: str,
) -> dict[str, object]:
    try:
        completed = subprocess.run(
            [str(executable), *arguments],
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            shell=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        raise ProbeFailure(reason) from None
    if completed.returncode != 0 or completed.stderr:
        raise ProbeFailure(reason)
    try:
        value = json.loads(completed.stdout)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ProbeFailure(reason) from None
    if not isinstance(value, dict):
        raise ProbeFailure(reason)
    return value


def _require_authenticated(
    executable: Path,
    environment: dict[str, str],
) -> None:
    try:
        completed = subprocess.run(
            [str(executable), "login", "status"],
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            shell=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        raise ProbeBlocked("isolated_auth_unavailable") from None
    if completed.returncode != 0:
        raise ProbeBlocked("isolated_auth_unavailable")


def _manual_blocks_replacement(manual_bytes: bytes) -> bool:
    return all(
        marker in manual_bytes for marker in POST_TOOL_USE_UNSUPPORTED_MARKERS
    )


class LifecycleContext:
    __slots__ = ("cleanup_status", "environment", "trust_confirmed")

    def __init__(self, environment: dict[str, str], trust_confirmed: bool) -> None:
        self.cleanup_status = "pending"
        self.environment = environment
        self.trust_confirmed = trust_confirmed


@contextmanager
def isolated_lifecycle(
    capture: HostCapture,
    plugin: Path,
    *,
    trust_hook: Callable[[dict[str, str]], bool],
) -> Iterator[LifecycleContext]:
    context: LifecycleContext | None = None
    with tempfile.TemporaryDirectory() as directory:
        temporary_root = Path(directory).resolve(strict=True)
        codex_home = temporary_root / "codex-home"
        marketplace = temporary_root / "marketplace"
        codex_home.mkdir()
        _materialize_marketplace(plugin, marketplace)
        installed_plugin = marketplace / "plugins" / PLUGIN_NAME
        try:
            installed_sha256 = _tree_sha256(installed_plugin)
        except ProbeBlocked:
            raise ProbeFailure("synthetic_plugin_drift") from None
        if installed_sha256 != capture.plugin_sha256:
            raise ProbeFailure("synthetic_plugin_drift")
        environment = dict(capture.environment)
        environment["CODEX_HOME"] = str(codex_home)
        try:
            capture.recheck()
            _require_authenticated(capture.resolved, environment)
            _run_json(
                capture.resolved,
                ["plugin", "marketplace", "add", str(marketplace), "--json"],
                environment,
                "marketplace_add_failed",
            )
            _run_json(
                capture.resolved,
                ["plugin", "add", PLUGIN_SELECTOR, "--json"],
                environment,
                "plugin_add_failed",
            )
            trust_confirmed = trust_hook(environment)
            if trust_confirmed is not True:
                raise ProbeBlocked("hook_trust_unavailable")
            capture.recheck()
            context = LifecycleContext(environment, trust_confirmed)
            yield context
        finally:
            if context is not None:
                context.cleanup_status = "complete"
            capture.recheck()


def _verdict(
    *,
    status: str,
    reason: str,
    capture: HostCapture | None,
    trust_confirmed: bool,
    cleanup_status: str,
) -> dict[str, object]:
    values: dict[str, object] = {
        "schemaVersion": 1,
        "issue": "DEV-246",
        "status": status,
        "reason": reason,
        "codexVersion": capture.codex_version if capture else None,
        "codexExecutable": capture.normalized_executable if capture else None,
        "manualSha256": capture.manual_sha256 if capture else None,
        "pluginSha256": capture.plugin_sha256 if capture else None,
        "originalSha256": hashlib.sha256(ORIGINAL_SENTINEL).hexdigest(),
        "compactSha256": hashlib.sha256(COMPACT_SENTINEL).hexdigest(),
        "boundarySource": None,
        "originalAbsentFromNextRequest": None,
        "compactPresentInNextRequest": None,
        "additionalParentModelTurns": 0,
        "hookInvocations": 0,
        "trustConfirmed": trust_confirmed,
        "cleanupStatus": cleanup_status,
    }
    return {key: values[key] for key in VERDICT_KEYS}


def run_discovery(
    codex_executable: Path,
    manual: Path,
    plugin: Path,
    *,
    trust_hook: Callable[[dict[str, str]], bool],
    expected_manual_sha256: str = OFFICIAL_MANUAL_SHA256,
) -> dict[str, object]:
    capture: HostCapture | None = None
    trust_confirmed = False

    try:
        capture = capture_preflight(codex_executable, manual, plugin)
        capture.recheck()
        if capture.manual_sha256 != expected_manual_sha256:
            return _verdict(
                status="fail",
                reason="official_manual_hash_mismatch",
                capture=capture,
                trust_confirmed=False,
                cleanup_status="complete",
            )
        if not _manual_blocks_replacement(capture.manual_bytes):
            return _verdict(
                status="fail",
                reason="official_manual_contract_drift",
                capture=capture,
                trust_confirmed=False,
                cleanup_status="complete",
            )
        return _verdict(
            status="blocked",
            reason="host_replacement_unavailable",
            capture=capture,
            trust_confirmed=False,
            cleanup_status="complete",
        )
    except ProbeBlocked as failure:
        return _verdict(
            status="blocked",
            reason=str(failure),
            capture=capture,
            trust_confirmed=trust_confirmed,
            cleanup_status="complete",
        )
    except ProbeFailure as failure:
        return _verdict(
            status="fail",
            reason=str(failure),
            capture=capture,
            trust_confirmed=trust_confirmed,
            cleanup_status="complete",
        )
    except subprocess.TimeoutExpired:
        return _verdict(
            status="fail",
            reason="host_timeout",
            capture=capture,
            trust_confirmed=trust_confirmed,
            cleanup_status="complete",
        )
    except OSError:
        return _verdict(
            status="fail",
            reason="lifecycle_filesystem_failed",
            capture=capture,
            trust_confirmed=trust_confirmed,
            cleanup_status="incomplete",
        )


def _interactive_trust_unavailable(_: dict[str, str]) -> bool:
    return False


def _parse_arguments(arguments: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--codex-executable", type=Path, required=True)
    parser.add_argument("--manual", type=Path, required=True)
    parser.add_argument("--plugin", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(arguments)


def _atomic_write_json(path: Path, value: object) -> None:
    parent = path.parent.resolve(strict=True)
    if not parent.is_dir() or path.parent.is_symlink():
        raise OSError("output_parent_invalid")
    destination = parent / path.name
    try:
        metadata = destination.lstat()
    except FileNotFoundError:
        metadata = None
    if metadata is not None and (
        stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode)
    ):
        raise OSError("output_destination_invalid")
    before = (
        None
        if metadata is None
        else (
            metadata.st_dev,
            metadata.st_ino,
            metadata.st_mode,
            metadata.st_size,
            metadata.st_mtime_ns,
        )
    )
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=parent,
    )
    temporary: Path | None = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            descriptor = -1
            stream.write(json.dumps(value, ensure_ascii=True, indent=2) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        try:
            current = destination.lstat()
        except FileNotFoundError:
            current = None
        current_snapshot = (
            None
            if current is None
            else (
                current.st_dev,
                current.st_ino,
                current.st_mode,
                current.st_size,
                current.st_mtime_ns,
            )
        )
        if current_snapshot != before:
            raise OSError("output_destination_drift")
        os.replace(temporary, destination)
        temporary = None
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if temporary is not None and temporary.exists():
            temporary.unlink()


def main(
    arguments: list[str] | None = None,
    *,
    trust_hook: Callable[[dict[str, str]], bool] | None = None,
) -> int:
    options = _parse_arguments(arguments)
    verdict = run_discovery(
        options.codex_executable,
        options.manual,
        options.plugin,
        trust_hook=trust_hook or _interactive_trust_unavailable,
    )
    try:
        _atomic_write_json(options.output, verdict)
    except OSError:
        return 1
    status = verdict["status"]
    return 0 if status == "pass" else 2 if status == "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
