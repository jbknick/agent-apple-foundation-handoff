#!/usr/bin/env python3
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
from typing import Callable, Iterable, Iterator


VERSION_LINE = b"codex-cli 0.144.5\n"
MARKETPLACE_NAME = "dev-246-synthetic"
PLUGIN_NAME = "dev-246-result-replacement-probe"
PLUGIN_SELECTOR = f"{PLUGIN_NAME}@{MARKETPLACE_NAME}"
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
        manual_sha256: str,
        plugin_sha256: str,
    ) -> None:
        self.codex_version = "0.144.5"
        self.environment = environment
        self.executable = executable
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

    manual_sha256 = hashlib.sha256(
        _regular_file_bytes(manual, "official_manual_unavailable")
    ).hexdigest()
    plugin_sha256 = _tree_sha256(plugin)
    return HostCapture(
        executable=codex_executable,
        resolved=resolved,
        snapshot=snapshot,
        environment=environment,
        manual_sha256=manual_sha256,
        plugin_sha256=plugin_sha256,
    )


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
        environment = dict(capture.environment)
        environment["CODEX_HOME"] = str(codex_home)
        try:
            capture.recheck()
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
