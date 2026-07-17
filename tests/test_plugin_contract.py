from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ID = "apple-foundation-models-handoff"
VERSION = "0.1.0"
SOURCE = "./plugins/apple-foundation-models-handoff"
MARKETPLACE = "agent-apple-foundation-handoff"
REPOSITORY = "https://github.com/jbknick/agent-apple-foundation-handoff"


def load_json(relative_path: str) -> dict[str, object]:
    with (ROOT / relative_path).open(encoding="utf-8") as source:
        return json.load(source)


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
        package_files = {
            path.relative_to(plugin_root).as_posix()
            for path in plugin_root.rglob("*")
            if path.is_file()
        }

        self.assertEqual(
            {
                ".claude-plugin/plugin.json",
                ".codex-plugin/plugin.json",
                "metadata/codex-interface.json",
            },
            package_files,
        )
        for surface in (
            "skills",
            "references",
            "agents",
            "hooks",
            "mcp",
            "commands",
            "scripts",
            "assets",
        ):
            with self.subTest(surface=surface):
                self.assertFalse((plugin_root / surface).exists())


if __name__ == "__main__":
    unittest.main()
