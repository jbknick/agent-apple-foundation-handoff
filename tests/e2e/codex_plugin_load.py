from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import tempfile
from typing import Any, NoReturn


ROOT = Path(__file__).resolve().parents[2]
PLUGIN_ID = "apple-foundation-models-handoff"
MARKETPLACE = "agent-apple-foundation-handoff"
PLUGIN_ROOT = ROOT / "plugins" / PLUGIN_ID
VERSION_RE = re.compile(r"^codex-cli 0\.144\.5$")
REFERENCE_FILES = {
    f"references/{name}"
    for name in (
        "architecture-and-state.md",
        "orchestration-patterns.md",
        "apple-api-availability.md",
        "security-context-and-recovery.md",
        "evaluation-and-observability.md",
    )
}
EXPECTED_CACHE_FILES = {
    ".claude-plugin/plugin.json",
    ".codex-plugin/plugin.json",
    "metadata/codex-interface.json",
    *REFERENCE_FILES,
    "skills/design-apple-foundation-models-handoff/SKILL.md",
    "skills/implement-apple-foundation-models-handoff/SKILL.md",
    "skills/review-apple-foundation-models-handoff/SKILL.md",
    "skills/debug-apple-foundation-models-handoff/SKILL.md",
    "skills/validate-apple-foundation-models-handoff/SKILL.md",
}
EXPECTED_CACHE_DIRECTORIES = {
    ".claude-plugin",
    ".codex-plugin",
    "metadata",
    "references",
    "skills",
    "skills/design-apple-foundation-models-handoff",
    "skills/implement-apple-foundation-models-handoff",
    "skills/review-apple-foundation-models-handoff",
    "skills/debug-apple-foundation-models-handoff",
    "skills/validate-apple-foundation-models-handoff",
}
EXPECTED_CAPABILITIES = [
    "design-apple-foundation-models-handoff",
    "implement-apple-foundation-models-handoff",
    "review-apple-foundation-models-handoff",
    "debug-apple-foundation-models-handoff",
    "validate-apple-foundation-models-handoff",
]

EVIDENCE_ID = "E-CODEX-LOAD-001"
PLUGIN_VERSION = "0.1.0"
SELECTOR = f"{PLUGIN_ID}@{MARKETPLACE}"
MARKETPLACE_ADD_KEYS = {
    "marketplaceName",
    "installedRoot",
    "alreadyAdded",
}
LIST_DOCUMENT_KEYS = {"installed", "available"}
PLUGIN_ENTRY_KEYS = {
    "pluginId",
    "name",
    "marketplaceName",
    "version",
    "installed",
    "enabled",
    "source",
    "marketplaceSource",
    "installPolicy",
    "authPolicy",
}
PLUGIN_ADD_KEYS = {
    "pluginId",
    "name",
    "marketplaceName",
    "version",
    "authPolicy",
    "installedPath",
}
HostSnapshot = tuple[int, int, int, int, int, int, int]


class ProbeFailure(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def emit_result(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True))


def blocked() -> int:
    emit_result(
        {
            "evidenceId": EVIDENCE_ID,
            "reason": "missing_binary_or_version_mismatch",
            "status": "blocked",
        }
    )
    return 2


def failed(reason: str) -> int:
    emit_result(
        {
            "evidenceId": EVIDENCE_ID,
            "reason": reason,
            "status": "fail",
        }
    )
    return 1


def exact_version(executable: str, environment: dict[str, str]) -> bool:
    try:
        result = subprocess.run(
            [executable, "--version"],
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False

    if result.returncode != 0 or result.stderr:
        return False
    try:
        output = result.stdout.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return False
    if output.endswith("\n"):
        output = output[:-1]
    if "\n" in output or "\r" in output:
        return False
    return VERSION_RE.fullmatch(output) is not None


def pairs_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    document: dict[str, Any] = {}
    for key, value in pairs:
        if key in document:
            raise ValueError("duplicate JSON key")
        document[key] = value
    return document


def reject_nonfinite_constant(_: str) -> NoReturn:
    raise ValueError("non-finite JSON constant")


def parse_json_object(payload: bytes, reason: str) -> dict[str, Any]:
    try:
        parsed = json.loads(
            payload,
            object_pairs_hook=pairs_without_duplicates,
            parse_constant=reject_nonfinite_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        raise ProbeFailure(reason) from None
    if not isinstance(parsed, dict):
        raise ProbeFailure(reason)
    return parsed


def run_json(
    executable: str,
    arguments: list[str],
    environment: dict[str, str],
    reason: str,
) -> dict[str, Any]:
    try:
        result = subprocess.run(
            [executable, *arguments],
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        raise ProbeFailure(reason) from None

    if result.returncode != 0 or result.stderr:
        raise ProbeFailure(reason)
    return parse_json_object(result.stdout, reason)


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ProbeFailure(reason)


def metadata_snapshot(
    metadata: os.stat_result,
) -> HostSnapshot:
    return (
        metadata.st_dev,
        metadata.st_ino,
        stat.S_IFMT(metadata.st_mode),
        stat.S_IMODE(metadata.st_mode),
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def require_current_host_identity(
    executable: str,
    locator: Path,
    initial_resolution: Path,
    initial_snapshot: HostSnapshot,
) -> None:
    reason = "host_resolution_or_version_drift"
    try:
        current_resolution = locator.resolve(strict=True)
        current_metadata = current_resolution.stat()
    except OSError:
        raise ProbeFailure(reason) from None
    require(current_resolution == initial_resolution, reason)
    require(stat.S_ISREG(current_metadata.st_mode), reason)
    require(metadata_snapshot(current_metadata) == initial_snapshot, reason)
    require(os.access(locator, os.X_OK), reason)


def stable_host_version_matches(
    executable: str,
    locator: Path,
    initial_resolution: Path,
    initial_snapshot: HostSnapshot,
    environment: dict[str, str],
) -> bool:
    require_current_host_identity(
        executable,
        locator,
        initial_resolution,
        initial_snapshot,
    )
    matches = exact_version(executable, environment)
    require_current_host_identity(
        executable,
        locator,
        initial_resolution,
        initial_snapshot,
    )
    return matches


def require_stable_host(
    executable: str,
    locator: Path,
    initial_resolution: Path,
    initial_snapshot: HostSnapshot,
    environment: dict[str, str],
) -> None:
    require(
        stable_host_version_matches(
            executable,
            locator,
            initial_resolution,
            initial_snapshot,
            environment,
        ),
        "host_resolution_or_version_drift",
    )


def install_isolated_plugin(
    executable: str,
    environment: dict[str, str],
    codex_home: Path,
) -> Path:
    marketplace_add = run_json(
        executable,
        ["plugin", "marketplace", "add", str(ROOT), "--json"],
        environment,
        "marketplace_add_failed",
    )
    require_exact_keys(
        marketplace_add,
        MARKETPLACE_ADD_KEYS,
        "marketplace_contract_mismatch",
    )
    require(
        marketplace_add.get("marketplaceName") == MARKETPLACE,
        "marketplace_contract_mismatch",
    )
    require(
        marketplace_add.get("installedRoot") == str(ROOT),
        "marketplace_contract_mismatch",
    )
    require(
        marketplace_add.get("alreadyAdded") is False,
        "marketplace_contract_mismatch",
    )

    available = run_json(
        executable,
        ["plugin", "list", "--available", "--json"],
        environment,
        "available_list_failed",
    )
    require_exact_keys(
        available,
        LIST_DOCUMENT_KEYS,
        "available_plugin_contract_mismatch",
    )
    require(available.get("installed") == [], "available_plugin_contract_mismatch")
    available_entry = require_single_entry(
        available, "available", "available_plugin_contract_mismatch"
    )
    require_plugin_entry(
        available_entry,
        installed=False,
        enabled=False,
        reason="available_plugin_contract_mismatch",
    )

    installed = run_json(
        executable,
        ["plugin", "add", SELECTOR, "--json"],
        environment,
        "plugin_add_failed",
    )
    require_exact_keys(installed, PLUGIN_ADD_KEYS, "plugin_add_contract_mismatch")
    require(installed.get("pluginId") == SELECTOR, "plugin_add_contract_mismatch")
    require(installed.get("name") == PLUGIN_ID, "plugin_add_contract_mismatch")
    require(
        installed.get("marketplaceName") == MARKETPLACE,
        "plugin_add_contract_mismatch",
    )
    require(installed.get("version") == PLUGIN_VERSION, "plugin_add_contract_mismatch")
    require(
        installed.get("authPolicy") == "ON_INSTALL",
        "plugin_add_contract_mismatch",
    )
    installed_path_value = installed.get("installedPath")
    require(
        isinstance(installed_path_value, str) and bool(installed_path_value),
        "plugin_add_contract_mismatch",
    )
    assert isinstance(installed_path_value, str)
    installed_path = validate_installed_path(installed_path_value, codex_home)

    installed_list = run_json(
        executable,
        ["plugin", "list", "--json"],
        environment,
        "installed_list_failed",
    )
    require_exact_keys(
        installed_list,
        LIST_DOCUMENT_KEYS,
        "installed_plugin_contract_mismatch",
    )
    installed_entry = require_single_entry(
        installed_list, "installed", "installed_plugin_contract_mismatch"
    )
    require_plugin_entry(
        installed_entry,
        installed=True,
        enabled=True,
        reason="installed_plugin_contract_mismatch",
    )
    require(installed_list.get("available") == [], "installed_plugin_contract_mismatch")
    return installed_path


def require_source_cache_identity(installed_path: Path) -> dict[str, str]:
    scan_payload(PLUGIN_ROOT, "source_payload_contract_mismatch")
    scan_payload(installed_path, "cache_payload_contract_mismatch")
    source_hashes = {
        relative_path: sha256(PLUGIN_ROOT / relative_path)
        for relative_path in EXPECTED_CACHE_FILES
    }
    cached_hashes = {
        relative_path: sha256(installed_path / relative_path)
        for relative_path in EXPECTED_CACHE_FILES
    }
    require(source_hashes == cached_hashes, "cache_integrity_mismatch")
    return source_hashes


def require_exact_keys(
    document: dict[str, Any], expected_keys: set[str], reason: str
) -> None:
    require(set(document) == expected_keys, reason)


def require_plugin_entry(
    entry: object,
    *,
    installed: bool,
    enabled: bool,
    reason: str,
) -> None:
    require(isinstance(entry, dict), reason)
    assert isinstance(entry, dict)
    require_exact_keys(entry, PLUGIN_ENTRY_KEYS, reason)
    expected_source = {"source": "local", "path": str(PLUGIN_ROOT)}
    expected_marketplace_source = {
        "sourceType": "local",
        "source": str(ROOT),
    }
    require(entry.get("pluginId") == SELECTOR, reason)
    require(entry.get("name") == PLUGIN_ID, reason)
    require(entry.get("marketplaceName") == MARKETPLACE, reason)
    require(entry.get("version") == PLUGIN_VERSION, reason)
    require(entry.get("installed") is installed, reason)
    require(entry.get("enabled") is enabled, reason)
    require(entry.get("source") == expected_source, reason)
    require(entry.get("marketplaceSource") == expected_marketplace_source, reason)
    require(entry.get("installPolicy") == "AVAILABLE", reason)
    require(entry.get("authPolicy") == "ON_INSTALL", reason)


def require_single_entry(
    document: dict[str, Any], key: str, reason: str
) -> dict[str, Any]:
    entries = document.get(key)
    require(isinstance(entries, list) and len(entries) == 1, reason)
    entry = entries[0]
    require(isinstance(entry, dict), reason)
    assert isinstance(entry, dict)
    return entry


def validate_installed_path(reported: str, codex_home: Path) -> Path:
    reported_path = Path(reported)
    try:
        reported_metadata = reported_path.lstat()
    except (OSError, ValueError):
        raise ProbeFailure("installed_path_invalid") from None
    require(not stat.S_ISLNK(reported_metadata.st_mode), "installed_path_invalid")
    require(stat.S_ISDIR(reported_metadata.st_mode), "installed_path_invalid")

    try:
        resolved = reported_path.resolve(strict=True)
    except (OSError, RuntimeError, ValueError):
        raise ProbeFailure("installed_path_invalid") from None
    require(
        resolved != codex_home and resolved.is_relative_to(codex_home),
        "installed_path_outside_isolated_home",
    )
    return resolved


def read_regular_file(path: Path, reason: str) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        initial_metadata = path.lstat()
        require(stat.S_ISREG(initial_metadata.st_mode), reason)
        initial_snapshot = metadata_snapshot(initial_metadata)
        descriptor = os.open(path, flags)
    except OSError:
        raise ProbeFailure(reason) from None
    try:
        opened_metadata = os.fstat(descriptor)
        require(stat.S_ISREG(opened_metadata.st_mode), reason)
        require(metadata_snapshot(opened_metadata) == initial_snapshot, reason)
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        final_metadata = os.fstat(descriptor)
        current_metadata = path.lstat()
        require(
            metadata_snapshot(final_metadata)
            == metadata_snapshot(current_metadata)
            == initial_snapshot,
            reason,
        )
        return b"".join(chunks)
    except OSError:
        raise ProbeFailure(reason) from None
    finally:
        os.close(descriptor)


def sha256(path: Path, reason: str = "cache_integrity_mismatch") -> str:
    return hashlib.sha256(read_regular_file(path, reason)).hexdigest()


def scan_payload(root: Path, reason: str) -> set[str]:
    try:
        root_metadata = root.lstat()
    except OSError:
        raise ProbeFailure(reason) from None
    require(not stat.S_ISLNK(root_metadata.st_mode), reason)
    require(stat.S_ISDIR(root_metadata.st_mode), reason)

    observed_files: set[str] = set()
    observed_directories: set[str] = set()

    def walk_error(_: OSError) -> None:
        raise ProbeFailure(reason)

    try:
        for current, directory_names, file_names in os.walk(
            root, topdown=True, onerror=walk_error, followlinks=False
        ):
            current_path = Path(current)
            current_metadata = current_path.lstat()
            require(not stat.S_ISLNK(current_metadata.st_mode), reason)
            require(stat.S_ISDIR(current_metadata.st_mode), reason)

            for name in directory_names:
                path = current_path / name
                metadata = path.lstat()
                require(not stat.S_ISLNK(metadata.st_mode), reason)
                require(stat.S_ISDIR(metadata.st_mode), reason)
                observed_directories.add(path.relative_to(root).as_posix())

            for name in file_names:
                path = current_path / name
                metadata = path.lstat()
                require(not stat.S_ISLNK(metadata.st_mode), reason)
                require(stat.S_ISREG(metadata.st_mode), reason)
                observed_files.add(path.relative_to(root).as_posix())
    except OSError:
        raise ProbeFailure(reason) from None

    require(observed_directories == EXPECTED_CACHE_DIRECTORIES, reason)
    require(observed_files == EXPECTED_CACHE_FILES, reason)
    return observed_files


def probe(
    executable: str,
    locator: Path,
    initial_resolution: Path,
    initial_snapshot: HostSnapshot,
    base_environment: dict[str, str],
) -> dict[str, Any]:
    host_identity = executable, locator, initial_resolution, initial_snapshot
    with tempfile.TemporaryDirectory() as temporary_home:
        codex_home = Path(temporary_home).resolve(strict=True)
        environment = dict(base_environment)
        environment["CODEX_HOME"] = str(codex_home)

        require_stable_host(*host_identity, environment)
        installed_path = install_isolated_plugin(
            executable,
            environment,
            codex_home,
        )

        require_stable_host(*host_identity, environment)

        source_hashes = require_source_cache_identity(installed_path)
        require_stable_host(*host_identity, environment)

        generated_manifest = parse_json_object(
            read_regular_file(
                PLUGIN_ROOT / ".codex-plugin/plugin.json",
                "generated_manifest_invalid",
            ),
            "generated_manifest_invalid",
        )
        interface = generated_manifest.get("interface")
        require(isinstance(interface, dict), "generated_manifest_invalid")
        assert isinstance(interface, dict)
        require(
            interface.get("capabilities") == EXPECTED_CAPABILITIES,
            "capabilities_mismatch",
        )

        result = {
            "status": "pass",
            "evidenceId": EVIDENCE_ID,
            "host": "codex",
            "hostPath": "<host-path>",
            "hostVersion": "0.144.5",
            "marketplace": MARKETPLACE,
            "pluginId": SELECTOR,
            "pluginVersion": PLUGIN_VERSION,
            "enabled": True,
            "capabilities": list(EXPECTED_CAPABILITIES),
            "cacheFiles": sorted(EXPECTED_CACHE_FILES),
            "referenceFiles": sorted(REFERENCE_FILES),
            "referenceSha256": {
                relative_path: source_hashes[relative_path]
                for relative_path in sorted(REFERENCE_FILES)
            },
            "canonicalManifestSha256": source_hashes[
                ".claude-plugin/plugin.json"
            ],
            "generatedManifestSha256": source_hashes[
                ".codex-plugin/plugin.json"
            ],
            "capabilityActivation": "not_applicable/behavior_owned_by_forward_runner",
        }

    require_stable_host(*host_identity, base_environment)
    return result


def main() -> int:
    search_path = os.environ.get("PATH")
    if search_path is None:
        return blocked()
    base_environment = {"PATH": search_path}
    host = shutil.which("codex", path=search_path)
    if host is None:
        return blocked()
    locator = Path(host)
    try:
        initial_resolution = locator.resolve(strict=True)
        initial_metadata = initial_resolution.stat()
    except OSError:
        return blocked()
    if not stat.S_ISREG(initial_metadata.st_mode) or not os.access(locator, os.X_OK):
        return blocked()
    executable = str(initial_resolution)
    initial_snapshot = metadata_snapshot(initial_metadata)
    try:
        if not stable_host_version_matches(
            executable,
            locator,
            initial_resolution,
            initial_snapshot,
            base_environment,
        ):
            return blocked()
    except ProbeFailure as failure:
        return failed(failure.reason)

    try:
        result = probe(
            executable,
            locator,
            initial_resolution,
            initial_snapshot,
            base_environment,
        )
    except ProbeFailure as failure:
        return failed(failure.reason)
    except Exception:
        return failed("unexpected_probe_failure")
    emit_result(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
