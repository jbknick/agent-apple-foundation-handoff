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

    def test_input_schemas_are_closed_and_bounded(self):
        interface = load_json("schemas/codex-interface-input.schema.json")
        marketplace = load_json("schemas/codex-marketplace-input.schema.json")

        self.assertFalse(interface["additionalProperties"])
        self.assertEqual(3, interface["properties"]["defaultPrompt"]["maxItems"])
        self.assertEqual(0, interface["properties"]["capabilities"]["minItems"])
        self.assertFalse(marketplace["additionalProperties"])
        self.assertEqual(1, marketplace["properties"]["plugins"]["minItems"])
        self.assertEqual(1, marketplace["properties"]["plugins"]["maxItems"])

    def test_plugin_package_initially_contains_only_canonical_inputs(self):
        plugin_root = ROOT / "plugins" / PLUGIN_ID
        package_files = {
            path.relative_to(plugin_root).as_posix()
            for path in plugin_root.rglob("*")
            if path.is_file()
        }

        self.assertEqual(
            {
                ".claude-plugin/plugin.json",
                "metadata/codex-interface.json",
            },
            package_files,
        )


if __name__ == "__main__":
    unittest.main()
