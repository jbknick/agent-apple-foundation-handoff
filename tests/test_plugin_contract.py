from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import stat
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ID = "apple-foundation-models-handoff"
VERSION = "0.1.0"
SOURCE = "./plugins/apple-foundation-models-handoff"
MARKETPLACE = "agent-apple-foundation-handoff"
REPOSITORY = "https://github.com/jbknick/agent-apple-foundation-handoff"
ALLOWED_PACKAGE_FILES = {
    ".claude-plugin/plugin.json",
    ".codex-plugin/plugin.json",
    "metadata/codex-interface.json",
}
ALLOWED_PACKAGE_ENTRIES = {
    ".claude-plugin": "directory",
    ".claude-plugin/plugin.json": "file",
    ".codex-plugin": "directory",
    ".codex-plugin/plugin.json": "file",
    "metadata": "directory",
    "metadata/codex-interface.json": "file",
}
FORBIDDEN_SURFACES = (
    "skills",
    "references",
    "agents",
    "hooks",
    "mcp",
    "commands",
    "scripts",
    "assets",
)


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

    def test_input_schemas_are_closed_and_bounded(self):
        interface = load_json("schemas/codex-interface-input.schema.json")
        marketplace = load_json("schemas/codex-marketplace-input.schema.json")

        self.assertFalse(interface["additionalProperties"])
        self.assertEqual(3, interface["properties"]["defaultPrompt"]["maxItems"])
        self.assertEqual(0, interface["properties"]["capabilities"]["minItems"])
        self.assertFalse(marketplace["additionalProperties"])
        self.assertEqual(1, marketplace["properties"]["plugins"]["minItems"])
        self.assertEqual(1, marketplace["properties"]["plugins"]["maxItems"])

    def test_plugin_package_contains_only_metadata_contract_files(self):
        plugin_root = ROOT / "plugins" / PLUGIN_ID
        assert_plugin_package_contract(self, plugin_root)

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


if __name__ == "__main__":
    unittest.main()
