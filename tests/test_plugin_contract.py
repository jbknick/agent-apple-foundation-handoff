from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ID = "apple-foundation-models-handoff"
VERSION = "0.1.0"
SOURCE = "./plugins/apple-foundation-models-handoff"
MARKETPLACE = "agent-apple-foundation-handoff"
REPOSITORY = "https://github.com/jbknick/agent-apple-foundation-handoff"
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
ALLOWED_PACKAGE_FILES = {
    ".claude-plugin/plugin.json",
    ".codex-plugin/plugin.json",
    "metadata/codex-interface.json",
    *REFERENCE_FILES,
}
ALLOWED_PACKAGE_ENTRIES = {
    ".claude-plugin": "directory",
    ".claude-plugin/plugin.json": "file",
    ".codex-plugin": "directory",
    ".codex-plugin/plugin.json": "file",
    "metadata": "directory",
    "metadata/codex-interface.json": "file",
    "references": "directory",
    **{name: "file" for name in REFERENCE_FILES},
}
FORBIDDEN_SURFACES = (
    "skills",
    "agents",
    "hooks",
    "mcp",
    "commands",
    "scripts",
    "assets",
)
SYNC_SCRIPT = ROOT / "scripts" / "sync_generated_artifacts.py"
CODEX_PROBE_SCRIPT = ROOT / "tests" / "e2e" / "codex_plugin_load.py"


sync_spec = importlib.util.spec_from_file_location(
    "sync_generated_artifacts_contract_tests", SYNC_SCRIPT
)
if sync_spec is None or sync_spec.loader is None:
    raise RuntimeError("unable to load generated-artifact synchronization module")
sync = importlib.util.module_from_spec(sync_spec)
sys.modules[sync_spec.name] = sync
sync_spec.loader.exec_module(sync)

probe_spec = importlib.util.spec_from_file_location(
    "codex_plugin_load_contract_tests", CODEX_PROBE_SCRIPT
)
if probe_spec is None or probe_spec.loader is None:
    raise RuntimeError("unable to load Codex structural probe module")
codex_probe = importlib.util.module_from_spec(probe_spec)
probe_spec.loader.exec_module(codex_probe)


def load_json(relative_path: str) -> dict[str, object]:
    with (ROOT / relative_path).open(encoding="utf-8") as source:
        return json.load(source)


def assert_plugin_package_contract(
    test_case: unittest.TestCase, plugin_root: Path
) -> None:
    root_metadata = plugin_root.lstat()
    test_case.assertFalse(stat.S_ISLNK(root_metadata.st_mode))
    test_case.assertTrue(stat.S_ISDIR(root_metadata.st_mode))

    for surface in FORBIDDEN_SURFACES:
        test_case.assertFalse(os.path.lexists(plugin_root / surface), surface)

    observed: dict[str, str] = {}
    directory_flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )

    def scan_directory(directory_fd: int, relative_directory: Path) -> None:
        with os.scandir(directory_fd) as entries:
            for entry in entries:
                relative_path = relative_directory / entry.name
                relative_name = relative_path.as_posix()
                metadata = entry.stat(follow_symlinks=False)
                test_case.assertFalse(stat.S_ISLNK(metadata.st_mode), relative_name)
                if stat.S_ISDIR(metadata.st_mode):
                    observed[relative_name] = "directory"
                    child_fd = os.open(
                        entry.name, directory_flags, dir_fd=directory_fd
                    )
                    try:
                        opened = os.fstat(child_fd)
                        test_case.assertEqual(
                            (metadata.st_dev, metadata.st_ino),
                            (opened.st_dev, opened.st_ino),
                            relative_name,
                        )
                        scan_directory(child_fd, relative_path)
                    finally:
                        os.close(child_fd)
                else:
                    test_case.assertTrue(stat.S_ISREG(metadata.st_mode), relative_name)
                    observed[relative_name] = "file"

    root_fd = os.open(plugin_root, directory_flags)
    try:
        opened_root = os.fstat(root_fd)
        test_case.assertEqual(
            (root_metadata.st_dev, root_metadata.st_ino),
            (opened_root.st_dev, opened_root.st_ino),
        )
        scan_directory(root_fd, Path())
    finally:
        os.close(root_fd)

    test_case.assertEqual(ALLOWED_PACKAGE_ENTRIES, observed)
    test_case.assertEqual(
        ALLOWED_PACKAGE_FILES,
        {name for name, entry_type in observed.items() if entry_type == "file"},
    )


def assert_dev_138_repository_only_package(test_case: unittest.TestCase) -> None:
    repository_fixture = ROOT / "fixtures" / "dev-138"
    source_plugin_root = ROOT / "plugins" / PLUGIN_ID
    test_case.assertTrue(repository_fixture.is_dir())
    test_case.assertFalse(os.path.lexists(source_plugin_root / "fixtures"))

    with tempfile.TemporaryDirectory(prefix="dev-138-package-") as directory:
        copied_plugin_root = Path(directory) / PLUGIN_ID
        shutil.copytree(source_plugin_root, copied_plugin_root)

        test_case.assertFalse((copied_plugin_root / "fixtures").exists())
        assert_plugin_package_contract(test_case, copied_plugin_root)

        copied_entries = sorted(
            path.relative_to(copied_plugin_root)
            for path in copied_plugin_root.rglob("*")
        )
        forbidden_parts = {"fixtures", "dev-138", "tests", "docs", "research"}
        for relative_path in copied_entries:
            lowered_parts = {part.lower() for part in relative_path.parts}
            test_case.assertTrue(
                lowered_parts.isdisjoint(forbidden_parts),
                relative_path.as_posix(),
            )
            test_case.assertNotIn(
                relative_path.suffix.lower(),
                {".trace", ".xcresult"},
                relative_path.as_posix(),
            )

        payload = b"".join(
            path.read_bytes()
            for path in copied_plugin_root.rglob("*")
            if path.is_file()
        )
        for prohibited in (
            b"synthetic-" + b"credential-sentinel",
            b"DEV138_" + b"SECRET_SENTINEL",
            b"/" + b"Users/",
            b"/" + b"home/",
            b"BEGIN RSA " + b"PRIVATE KEY",
            b"BEGIN OPENSSH " + b"PRIVATE KEY",
            b"BEGIN EC " + b"PRIVATE KEY",
        ):
            test_case.assertNotIn(prohibited, payload)


class PluginContractTests(unittest.TestCase):
    def test_canonical_identity_is_exact_and_honest(self):
        manifest = load_json(
            "plugins/apple-foundation-models-handoff/.claude-plugin/plugin.json"
        )

        self.assertEqual(PLUGIN_ID, manifest["name"])
        self.assertEqual(VERSION, manifest["version"])
        self.assertEqual(REPOSITORY, manifest["homepage"])
        self.assertEqual(REPOSITORY, manifest["repository"])
        self.assertNotIn("skills", manifest)
        for field in ("hooks", "mcpServers", "apps", "commands", "agents"):
            self.assertNotIn(field, manifest)

    def test_codex_interface_has_zero_capabilities(self):
        interface = load_json(
            "plugins/apple-foundation-models-handoff/metadata/codex-interface.json"
        )

        self.assertEqual("Developer Tools", interface["category"])
        self.assertEqual([], interface["capabilities"])
        self.assertEqual(1, len(interface["defaultPrompt"]))
        self.assertLessEqual(len(interface["defaultPrompt"][0]), 128)

    def test_marketplaces_use_the_conventional_source(self):
        claude = load_json(".claude-plugin/marketplace.json")
        codex = load_json("metadata/codex-marketplace.json")
        generated_codex = load_json(".agents/plugins/marketplace.json")

        self.assertEqual(MARKETPLACE, claude["name"])
        self.assertEqual(SOURCE, claude["plugins"][0]["source"])
        entry = codex["plugins"][0]
        self.assertEqual({"source": "local", "path": SOURCE}, entry["source"])
        self.assertEqual(
            {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
            entry["policy"],
        )
        self.assertEqual("Developer Tools", entry["category"])
        self.assertNotIn("products", entry["policy"])
        self.assertEqual(codex, generated_codex)

    def test_generated_codex_manifest_preserves_canonical_ownership(self):
        shared = load_json(
            "plugins/apple-foundation-models-handoff/.claude-plugin/plugin.json"
        )
        interface = load_json(
            "plugins/apple-foundation-models-handoff/metadata/codex-interface.json"
        )
        generated = load_json(
            "plugins/apple-foundation-models-handoff/.codex-plugin/plugin.json"
        )

        for field in (
            "name",
            "version",
            "description",
            "author",
            "homepage",
            "repository",
            "license",
            "keywords",
        ):
            with self.subTest(field=field):
                self.assertEqual(shared[field], generated[field])
        self.assertEqual(interface, generated["interface"])
        self.assertNotIn("skills", generated)
        for field in ("hooks", "mcpServers", "apps", "commands", "agents"):
            self.assertNotIn(field, generated)

    def test_input_schemas_match_closed_custom_validator_contracts(self):
        interface = load_json("schemas/codex-interface-input.schema.json")
        marketplace = load_json("schemas/codex-marketplace-input.schema.json")
        canonical_interface = load_json(
            "plugins/apple-foundation-models-handoff/metadata/codex-interface.json"
        )
        canonical_marketplace = load_json("metadata/codex-marketplace.json")
        shared_manifest = load_json(
            "plugins/apple-foundation-models-handoff/.claude-plugin/plugin.json"
        )
        schema_version = "https://json-schema.org/draft/2020-12/schema"
        self.assertEqual(schema_version, interface["$schema"])
        self.assertEqual(schema_version, marketplace["$schema"])

        def assert_closed_object(
            schema: dict[str, object], expected_properties: set[str]
        ) -> None:
            self.assertEqual("object", schema["type"])
            self.assertFalse(schema["additionalProperties"])
            self.assertEqual(expected_properties, set(schema["properties"]))
            self.assertEqual(expected_properties, set(schema["required"]))

        interface_fields = {
            "displayName",
            "shortDescription",
            "longDescription",
            "developerName",
            "category",
            "capabilities",
            "websiteURL",
            "defaultPrompt",
        }
        assert_closed_object(interface, interface_fields)
        interface_properties = interface["properties"]
        for field in (
            "displayName",
            "shortDescription",
            "longDescription",
            "developerName",
        ):
            with self.subTest(interface_string=field):
                self.assertEqual(
                    {"type": "string", "minLength": 1},
                    interface_properties[field],
                )
        self.assertEqual(
            {"const": "Developer Tools"}, interface_properties["category"]
        )
        self.assertEqual({"const": []}, interface_properties["capabilities"])
        self.assertEqual(
            {"type": "string", "pattern": "^https://"},
            interface_properties["websiteURL"],
        )
        self.assertEqual(
            {
                "type": "array",
                "minItems": 1,
                "maxItems": 3,
                "items": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 128,
                },
            },
            interface_properties["defaultPrompt"],
        )

        marketplace_fields = {"name", "interface", "plugins"}
        assert_closed_object(marketplace, marketplace_fields)
        marketplace_properties = marketplace["properties"]
        self.assertEqual(
            {"const": MARKETPLACE}, marketplace_properties["name"]
        )
        marketplace_interface = marketplace_properties["interface"]
        assert_closed_object(marketplace_interface, {"displayName"})
        self.assertEqual(
            {"const": "Agent Apple Foundation Handoff"},
            marketplace_interface["properties"]["displayName"],
        )
        plugins = marketplace_properties["plugins"]
        self.assertEqual("array", plugins["type"])
        self.assertEqual(1, plugins["minItems"])
        self.assertEqual(1, plugins["maxItems"])
        plugin = plugins["items"]
        assert_closed_object(plugin, {"name", "source", "policy", "category"})
        plugin_properties = plugin["properties"]
        self.assertEqual({"const": PLUGIN_ID}, plugin_properties["name"])
        source = plugin_properties["source"]
        assert_closed_object(source, {"source", "path"})
        self.assertEqual({"const": "local"}, source["properties"]["source"])
        self.assertEqual({"const": SOURCE}, source["properties"]["path"])
        policy = plugin_properties["policy"]
        assert_closed_object(policy, {"installation", "authentication"})
        self.assertEqual(
            {"const": "AVAILABLE"}, policy["properties"]["installation"]
        )
        self.assertEqual(
            {"const": "ON_INSTALL"}, policy["properties"]["authentication"]
        )
        self.assertEqual(
            {"const": "Developer Tools"}, plugin_properties["category"]
        )

        self.assertEqual(
            interface_properties["category"]["const"],
            canonical_interface["category"],
        )
        self.assertEqual(
            interface_properties["capabilities"]["const"],
            canonical_interface["capabilities"],
        )
        self.assertEqual(
            marketplace_properties["name"]["const"],
            canonical_marketplace["name"],
        )
        self.assertEqual(
            plugin_properties["source"]["properties"]["path"]["const"],
            canonical_marketplace["plugins"][0]["source"]["path"],
        )
        sync._validate_codex_interface(canonical_interface)
        sync._validate_codex_marketplace(canonical_marketplace, shared_manifest)

        interface_boundary_mutations = (
            ("non-empty capabilities", ("capabilities",), ["unimplemented"]),
            ("empty presentation string", ("displayName",), ""),
            ("missing prompt", ("defaultPrompt",), []),
            ("too many prompts", ("defaultPrompt",), ["prompt"] * 4),
            ("empty prompt", ("defaultPrompt",), [""]),
            ("overlong prompt", ("defaultPrompt",), ["x" * 129]),
            ("non-HTTPS website", ("websiteURL",), "http://example.com"),
        )
        for name, path, replacement in interface_boundary_mutations:
            with self.subTest(runtime_interface_boundary=name):
                mutated = json.loads(json.dumps(canonical_interface))
                mutated[path[0]] = replacement
                with self.assertRaises(ValueError):
                    sync._validate_codex_interface(mutated)

        for name, plugins in (
            ("missing plugin", []),
            (
                "too many plugins",
                canonical_marketplace["plugins"]
                + canonical_marketplace["plugins"],
            ),
        ):
            with self.subTest(runtime_marketplace_boundary=name):
                mutated = json.loads(json.dumps(canonical_marketplace))
                mutated["plugins"] = plugins
                with self.assertRaises(ValueError):
                    sync._validate_codex_marketplace(mutated, shared_manifest)

    def test_plugin_package_contains_only_approved_contract_files(self):
        plugin_root = ROOT / "plugins" / PLUGIN_ID
        assert_plugin_package_contract(self, plugin_root)

    def test_dev_138_fixtures_are_repository_only(self):
        assertion = globals().get("assert_dev_138_repository_only_package")
        self.assertIsNotNone(
            assertion,
            "missing assert_dev_138_repository_only_package",
        )
        assertion(self)

    def test_package_oracle_rejects_broken_skills_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            temporary_root = Path(directory)
            plugin_root = temporary_root / PLUGIN_ID
            shutil.copytree(ROOT / "plugins" / PLUGIN_ID, plugin_root)
            skills = plugin_root / "skills"
            skills.symlink_to(temporary_root / "missing-skills", target_is_directory=True)

            self.assertTrue(os.path.lexists(skills))
            with self.assertRaises(AssertionError):
                assert_plugin_package_contract(self, plugin_root)

    def test_package_oracle_rejects_unexpected_external_directory_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            temporary_root = Path(directory)
            plugin_root = temporary_root / PLUGIN_ID
            shutil.copytree(ROOT / "plugins" / PLUGIN_ID, plugin_root)
            external = temporary_root / "external"
            external.mkdir()
            (external / "sentinel.txt").write_text(
                "outside package\n", encoding="utf-8", newline="\n"
            )
            external_link = plugin_root / "external-package"
            external_link.symlink_to(external, target_is_directory=True)

            self.assertTrue(os.path.lexists(external_link))
            with self.assertRaises(AssertionError):
                assert_plugin_package_contract(self, plugin_root)


class CodexProbeRaceTests(unittest.TestCase):
    def test_regular_file_read_rejects_path_replacement(self):
        with tempfile.TemporaryDirectory() as directory:
            artifact = Path(directory) / "artifact.json"
            replacement = Path(directory) / "replacement.json"
            artifact.write_bytes(b'{"generation":1}')
            replacement.write_bytes(b'{"generation":2}')
            original_read = os.read
            replaced = False

            def replace_after_read(descriptor: int, size: int) -> bytes:
                nonlocal replaced
                payload = original_read(descriptor, size)
                if payload and not replaced:
                    replacement.replace(artifact)
                    replaced = True
                return payload

            with mock.patch.object(
                codex_probe.os, "read", side_effect=replace_after_read
            ):
                with self.assertRaisesRegex(
                    codex_probe.ProbeFailure, "artifact_changed"
                ):
                    codex_probe.read_regular_file(artifact, "artifact_changed")

    def test_regular_file_read_rejects_in_place_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            artifact = Path(directory) / "artifact.json"
            artifact.write_bytes(b'{"generation":1}')
            original_read = os.read
            mutated = False

            def mutate_after_read(descriptor: int, size: int) -> bytes:
                nonlocal mutated
                payload = original_read(descriptor, size)
                if payload and not mutated:
                    with artifact.open("ab", buffering=0) as mutable_artifact:
                        mutable_artifact.write(b" ")
                        os.fsync(mutable_artifact.fileno())
                    mutated = True
                return payload

            with mock.patch.object(
                codex_probe.os, "read", side_effect=mutate_after_read
            ):
                with self.assertRaisesRegex(
                    codex_probe.ProbeFailure, "artifact_changed"
                ):
                    codex_probe.read_regular_file(artifact, "artifact_changed")

    def test_host_check_rejects_same_version_path_replacement(self):
        check_host = getattr(codex_probe, "require_stable_host", None)
        self.assertIsNotNone(check_host, "probe lacks a stable-host check")
        assert check_host is not None

        with tempfile.TemporaryDirectory() as directory:
            locator = Path(directory) / "codex"
            replacement = Path(directory) / "replacement"
            marker = Path(directory) / "executed"
            script = "#!/bin/sh\nprintf 'codex-cli 0.144.5\\n'\n"
            locator.write_text(script, encoding="utf-8", newline="\n")
            locator.chmod(0o700)
            initial_resolution = locator.resolve(strict=True)
            initial_snapshot = codex_probe.metadata_snapshot(locator.stat())
            replacement.write_text(
                f"#!/bin/sh\ntouch '{marker}'\nprintf 'codex-cli 0.144.5\\n'\n",
                encoding="utf-8",
                newline="\n",
            )
            replacement.chmod(0o700)
            replacement.replace(locator)

            with self.assertRaisesRegex(
                codex_probe.ProbeFailure, "host_resolution_or_version_drift"
            ):
                check_host(
                    str(initial_resolution),
                    locator,
                    initial_resolution,
                    initial_snapshot,
                    {"PATH": os.environ.get("PATH", "")},
                )
            self.assertFalse(marker.exists(), "replaced host was executed")

    def test_host_check_rejects_replacement_during_version_invocation(self):
        with tempfile.TemporaryDirectory() as directory:
            locator = Path(directory) / "codex"
            replacement = Path(f"{locator}.replacement")
            locator.write_text(
                "#!/bin/sh\n"
                'mv "$0.replacement" "$0"\n'
                "printf 'codex-cli 0.144.5\\n'\n",
                encoding="utf-8",
                newline="\n",
            )
            locator.chmod(0o700)
            replacement.write_text(
                "#!/bin/sh\nprintf 'codex-cli 0.144.5\\n'\n",
                encoding="utf-8",
                newline="\n",
            )
            replacement.chmod(0o700)
            initial_resolution = locator.resolve(strict=True)
            initial_snapshot = codex_probe.metadata_snapshot(locator.stat())

            with self.assertRaisesRegex(
                codex_probe.ProbeFailure, "host_resolution_or_version_drift"
            ):
                codex_probe.require_stable_host(
                    str(initial_resolution),
                    locator,
                    initial_resolution,
                    initial_snapshot,
                    {"PATH": os.environ.get("PATH", "")},
                )


if __name__ == "__main__":
    unittest.main()
