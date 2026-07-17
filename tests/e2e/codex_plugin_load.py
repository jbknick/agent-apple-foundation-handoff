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
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PLUGIN_ID = "apple-foundation-models-handoff"
MARKETPLACE = "agent-apple-foundation-handoff"
PLUGIN_ROOT = ROOT / "plugins" / PLUGIN_ID
VERSION_RE = re.compile(r"^codex-cli 0\.144\.5$")
EXPECTED_CACHE_FILES = {
    ".claude-plugin/plugin.json",
    ".codex-plugin/plugin.json",
    "metadata/codex-interface.json",
}

EVIDENCE_ID = "E-CODEX-LOAD-001"
PLUGIN_VERSION = "0.1.0"
SELECTOR = f"{PLUGIN_ID}@{MARKETPLACE}"


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
    try:
        parsed = json.loads(result.stdout)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ProbeFailure(reason) from None
    if not isinstance(parsed, dict):
        raise ProbeFailure(reason)
    return parsed


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ProbeFailure(reason)


def require_plugin_entry(
    entry: object,
    *,
    installed: bool,
    enabled: bool,
    reason: str,
) -> None:
    require(isinstance(entry, dict), reason)
    assert isinstance(entry, dict)
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


def read_regular_file(path: Path, reason: str) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError:
        raise ProbeFailure(reason) from None
    try:
        metadata = os.fstat(descriptor)
        require(stat.S_ISREG(metadata.st_mode), reason)
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
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

    expected_directories = {
        Path(relative_path).parent.as_posix()
        for relative_path in EXPECTED_CACHE_FILES
    }
    require(observed_directories == expected_directories, reason)
    require(observed_files == EXPECTED_CACHE_FILES, reason)
    return observed_files


def probe(executable: str, locator: Path, initial_resolution: Path) -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as temporary_home:
        codex_home = Path(temporary_home).resolve(strict=True)
        environment = {"CODEX_HOME": str(codex_home)}

        marketplace_add = run_json(
            executable,
            ["plugin", "marketplace", "add", str(ROOT), "--json"],
            environment,
            "marketplace_add_failed",
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
        require(installed.get("pluginId") == SELECTOR, "plugin_add_contract_mismatch")
        require(installed.get("name") == PLUGIN_ID, "plugin_add_contract_mismatch")
        require(
            installed.get("marketplaceName") == MARKETPLACE,
            "plugin_add_contract_mismatch",
        )
        require(
            installed.get("version") == PLUGIN_VERSION,
            "plugin_add_contract_mismatch",
        )
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
        try:
            installed_path = Path(installed_path_value).resolve(strict=True)
        except OSError:
            raise ProbeFailure("installed_path_invalid") from None
        require(
            installed_path.is_relative_to(codex_home),
            "installed_path_outside_isolated_home",
        )

        installed_list = run_json(
            executable,
            ["plugin", "list", "--json"],
            environment,
            "installed_list_failed",
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
        require(
            installed_list.get("available") == [],
            "installed_plugin_contract_mismatch",
        )

        try:
            final_resolution = locator.resolve(strict=True)
            final_metadata = final_resolution.stat()
        except OSError:
            raise ProbeFailure("host_resolution_or_version_drift") from None
        require(final_resolution == initial_resolution, "host_resolution_or_version_drift")
        require(stat.S_ISREG(final_metadata.st_mode), "host_resolution_or_version_drift")
        require(os.access(locator, os.X_OK), "host_resolution_or_version_drift")
        require(
            exact_version(executable, environment),
            "host_resolution_or_version_drift",
        )

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

        try:
            generated_manifest = json.loads(
                read_regular_file(
                    PLUGIN_ROOT / ".codex-plugin/plugin.json",
                    "generated_manifest_invalid",
                )
            )
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ProbeFailure("generated_manifest_invalid") from None
        require(isinstance(generated_manifest, dict), "generated_manifest_invalid")
        interface = generated_manifest.get("interface")
        require(isinstance(interface, dict), "generated_manifest_invalid")
        assert isinstance(interface, dict)
        require(interface.get("capabilities") == [], "capabilities_not_empty")

        return {
            "status": "pass",
            "evidenceId": EVIDENCE_ID,
            "host": "codex",
            "hostPath": "<host-path>",
            "hostVersion": "0.144.5",
            "marketplace": MARKETPLACE,
            "pluginId": SELECTOR,
            "pluginVersion": PLUGIN_VERSION,
            "enabled": True,
            "capabilities": [],
            "cacheFiles": sorted(EXPECTED_CACHE_FILES),
            "canonicalManifestSha256": source_hashes[
                ".claude-plugin/plugin.json"
            ],
            "generatedManifestSha256": source_hashes[
                ".codex-plugin/plugin.json"
            ],
            "capabilityActivation": "blocked/production_skill_not_implemented",
        }


def main() -> int:
    host = shutil.which("codex")
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
    if not exact_version(executable, {}):
        return blocked()

    try:
        result = probe(executable, locator, initial_resolution)
    except ProbeFailure as failure:
        return failed(failure.reason)
    except Exception:
        return failed("unexpected_probe_failure")
    emit_result(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
