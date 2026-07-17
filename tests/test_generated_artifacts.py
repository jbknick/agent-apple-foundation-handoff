from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "sync_generated_artifacts.py"
CLAUDE_MARKETPLACE = Path(".claude-plugin/marketplace.json")
CODEX_MARKETPLACE = Path("metadata/codex-marketplace.json")
SHARED_MANIFEST = Path(
    "plugins/apple-foundation-models-handoff/.claude-plugin/plugin.json"
)
CODEX_INTERFACE = Path(
    "plugins/apple-foundation-models-handoff/metadata/codex-interface.json"
)
CANONICAL_INPUTS = (
    Path("CLAUDE.md"),
    CLAUDE_MARKETPLACE,
    CODEX_MARKETPLACE,
    SHARED_MANIFEST,
    CODEX_INTERFACE,
)


spec = importlib.util.spec_from_file_location(
    "sync_generated_artifacts_generated_tests", SCRIPT
)
if spec is None or spec.loader is None:
    raise RuntimeError("unable to load generated-artifact synchronization module")
sync = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = sync
spec.loader.exec_module(sync)


def _set_nested(value: object, keys: tuple[object, ...], replacement: object) -> None:
    current = value
    for key in keys[:-1]:
        current = current[key]
    current[keys[-1]] = replacement


def _delete_nested(value: object, keys: tuple[object, ...]) -> None:
    current = value
    for key in keys[:-1]:
        current = current[key]
    del current[keys[-1]]


class GeneratedArtifactTests(unittest.TestCase):
    def _copy_canonical_inputs(self, destination: Path) -> None:
        for relative_path in CANONICAL_INPUTS:
            target = destination / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative_path, target)

    def _mutate_json(
        self,
        root: Path,
        relative_path: Path,
        mutate,
    ) -> None:
        target = root / relative_path
        value = json.loads(target.read_text(encoding="utf-8"))
        mutate(value)
        target.write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )

    def test_expected_artifacts_are_the_exact_three_paths(self):
        artifacts = sync.expected_artifacts(ROOT)

        self.assertEqual(
            {
                Path("AGENTS.md"),
                Path(".agents/plugins/marketplace.json"),
                Path(
                    "plugins/apple-foundation-models-handoff/"
                    ".codex-plugin/plugin.json"
                ),
            },
            set(artifacts),
        )
        for content in artifacts.values():
            self.assertTrue(content.endswith(b"\n"))
            self.assertNotIn(b"\r", content)

    def test_rendered_manifest_is_honest_and_explicitly_ordered(self):
        inputs = sync.load_canonical_inputs(ROOT)
        content = sync.render_codex_manifest(inputs)
        rendered = json.loads(content)

        self.assertEqual("0.1.0", rendered["version"])
        self.assertEqual([], rendered["interface"]["capabilities"])
        self.assertNotIn("skills", rendered)
        self.assertEqual(
            [
                "name",
                "version",
                "description",
                "author",
                "homepage",
                "repository",
                "license",
                "keywords",
                "interface",
            ],
            list(rendered),
        )
        self.assertEqual(
            [
                "displayName",
                "shortDescription",
                "longDescription",
                "developerName",
                "category",
                "capabilities",
                "websiteURL",
                "defaultPrompt",
            ],
            list(rendered["interface"]),
        )
        self.assertEqual(content, sync.render_codex_manifest(inputs))

    def test_rendered_marketplace_preserves_distinct_policy_and_order(self):
        inputs = sync.load_canonical_inputs(ROOT)
        content = sync.render_codex_marketplace(inputs)
        rendered = json.loads(content)
        entry = rendered["plugins"][0]

        self.assertEqual("Developer Tools", entry["category"])
        self.assertEqual(
            {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
            entry["policy"],
        )
        self.assertEqual(["name", "interface", "plugins"], list(rendered))
        self.assertEqual(["name", "source", "policy", "category"], list(entry))
        self.assertEqual(content, sync.render_codex_marketplace(inputs))

    def test_coordinated_valid_semver_version_drift_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            isolated_root = Path(directory)
            self._copy_canonical_inputs(isolated_root)
            self._mutate_json(
                isolated_root,
                SHARED_MANIFEST,
                lambda value: _set_nested(value, ("version",), "0.1.1"),
            )
            self._mutate_json(
                isolated_root,
                CLAUDE_MARKETPLACE,
                lambda value: _set_nested(
                    value, ("plugins", 0, "version"), "0.1.1"
                ),
            )

            with self.assertRaises(sync.CanonicalInputError) as raised:
                sync.load_canonical_inputs(isolated_root)

            diagnostic = str(raised.exception)
            self.assertNotIn(str(isolated_root), diagnostic)
            self.assertNotIn(str(ROOT), diagnostic)
            self.assertFalse(Path(diagnostic).is_absolute())

    def test_non_empty_capabilities_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            isolated_root = Path(directory)
            self._copy_canonical_inputs(isolated_root)
            self._mutate_json(
                isolated_root,
                CODEX_INTERFACE,
                lambda value: _set_nested(
                    value, ("capabilities",), ["foundation-models-handoff"]
                ),
            )

            with self.assertRaises(sync.CanonicalInputError) as raised:
                sync.load_canonical_inputs(isolated_root)

            diagnostic = str(raised.exception)
            self.assertNotIn(str(isolated_root), diagnostic)
            self.assertNotIn(str(ROOT), diagnostic)
            self.assertFalse(Path(diagnostic).is_absolute())

    def test_canonical_mutations_are_rejected_without_absolute_paths(self):
        mutations = (
            (
                "duplicate key",
                SHARED_MANIFEST,
                "raw",
                lambda text: text.replace(
                    '"name": "apple-foundation-models-handoff",',
                    '"name": "apple-foundation-models-handoff",\n'
                    '  "name": "apple-foundation-models-handoff",',
                    1,
                ),
            ),
            (
                "missing required field",
                SHARED_MANIFEST,
                "json",
                lambda value: _delete_nested(value, ("license",)),
            ),
            (
                "unknown shared field",
                SHARED_MANIFEST,
                "json",
                lambda value: _set_nested(value, ("skills",), []),
            ),
            (
                "unknown author field",
                SHARED_MANIFEST,
                "json",
                lambda value: _set_nested(
                    value, ("author", "email"), "owner@example.com"
                ),
            ),
            (
                "unknown Claude marketplace field",
                CLAUDE_MARKETPLACE,
                "json",
                lambda value: _set_nested(value, ("unexpected",), True),
            ),
            (
                "unknown Claude owner field",
                CLAUDE_MARKETPLACE,
                "json",
                lambda value: _set_nested(
                    value, ("owner", "url"), "https://example.com"
                ),
            ),
            (
                "unknown Claude plugin field",
                CLAUDE_MARKETPLACE,
                "json",
                lambda value: _set_nested(value, ("plugins", 0, "category"), "Tools"),
            ),
            (
                "unknown Codex interface field",
                CODEX_INTERFACE,
                "json",
                lambda value: _set_nested(value, ("unexpected",), True),
            ),
            (
                "unknown Codex marketplace field",
                CODEX_MARKETPLACE,
                "json",
                lambda value: _set_nested(value, ("unexpected",), True),
            ),
            (
                "unknown Codex marketplace interface field",
                CODEX_MARKETPLACE,
                "json",
                lambda value: _set_nested(value, ("interface", "unexpected"), True),
            ),
            (
                "unknown Codex plugin field",
                CODEX_MARKETPLACE,
                "json",
                lambda value: _set_nested(value, ("plugins", 0, "unexpected"), True),
            ),
            (
                "unknown Codex source field",
                CODEX_MARKETPLACE,
                "json",
                lambda value: _set_nested(
                    value, ("plugins", 0, "source", "unexpected"), True
                ),
            ),
            (
                "unknown Codex policy field",
                CODEX_MARKETPLACE,
                "json",
                lambda value: _set_nested(
                    value, ("plugins", 0, "policy", "unexpected"), True
                ),
            ),
            (
                "wrong plugin identity",
                SHARED_MANIFEST,
                "json",
                lambda value: _set_nested(value, ("name",), "wrong-plugin"),
            ),
            (
                "invalid strict version",
                SHARED_MANIFEST,
                "json",
                lambda value: _set_nested(value, ("version",), "01.0.0"),
            ),
            (
                "Claude version drift",
                CLAUDE_MARKETPLACE,
                "json",
                lambda value: _set_nested(value, ("plugins", 0, "version"), "0.1.1"),
            ),
            (
                "wrong Claude source",
                CLAUDE_MARKETPLACE,
                "json",
                lambda value: _set_nested(value, ("plugins", 0, "source"), "./wrong"),
            ),
            (
                "wrong Codex source kind",
                CODEX_MARKETPLACE,
                "json",
                lambda value: _set_nested(
                    value, ("plugins", 0, "source", "source"), "remote"
                ),
            ),
            (
                "wrong Codex source path",
                CODEX_MARKETPLACE,
                "json",
                lambda value: _set_nested(
                    value, ("plugins", 0, "source", "path"), "./wrong"
                ),
            ),
            (
                "wrong interface category",
                CODEX_INTERFACE,
                "json",
                lambda value: _set_nested(value, ("category",), "Productivity"),
            ),
            (
                "wrong marketplace category",
                CODEX_MARKETPLACE,
                "json",
                lambda value: _set_nested(
                    value, ("plugins", 0, "category"), "Productivity"
                ),
            ),
            (
                "wrong installation policy",
                CODEX_MARKETPLACE,
                "json",
                lambda value: _set_nested(
                    value, ("plugins", 0, "policy", "installation"), "REQUIRED"
                ),
            ),
            (
                "wrong authentication policy",
                CODEX_MARKETPLACE,
                "json",
                lambda value: _set_nested(
                    value, ("plugins", 0, "policy", "authentication"), "NONE"
                ),
            ),
            (
                "product gating",
                CODEX_MARKETPLACE,
                "json",
                lambda value: _set_nested(
                    value, ("plugins", 0, "policy", "products"), ["codex"]
                ),
            ),
            (
                "empty prompts",
                CODEX_INTERFACE,
                "json",
                lambda value: _set_nested(value, ("defaultPrompt",), []),
            ),
            (
                "empty prompt string",
                CODEX_INTERFACE,
                "json",
                lambda value: _set_nested(value, ("defaultPrompt",), [""]),
            ),
            (
                "overlong prompt",
                CODEX_INTERFACE,
                "json",
                lambda value: _set_nested(value, ("defaultPrompt",), ["x" * 129]),
            ),
            (
                "empty capability string",
                CODEX_INTERFACE,
                "json",
                lambda value: _set_nested(value, ("capabilities",), [""]),
            ),
            (
                "non-HTTPS author URL",
                SHARED_MANIFEST,
                "json",
                lambda value: _set_nested(
                    value, ("author", "url"), "http://example.com"
                ),
            ),
            (
                "non-HTTPS homepage URL",
                SHARED_MANIFEST,
                "json",
                lambda value: _set_nested(value, ("homepage",), "http://example.com"),
            ),
            (
                "non-HTTPS repository URL",
                SHARED_MANIFEST,
                "json",
                lambda value: _set_nested(value, ("repository",), "http://example.com"),
            ),
            (
                "non-HTTPS website URL",
                CODEX_INTERFACE,
                "json",
                lambda value: _set_nested(value, ("websiteURL",), "http://example.com"),
            ),
            (
                "Claude marketplace identity drift",
                CLAUDE_MARKETPLACE,
                "json",
                lambda value: _set_nested(value, ("name",), "wrong-marketplace"),
            ),
            (
                "Claude owner identity drift",
                CLAUDE_MARKETPLACE,
                "json",
                lambda value: _set_nested(value, ("owner", "name"), "Wrong Owner"),
            ),
            (
                "Claude plugin identity drift",
                CLAUDE_MARKETPLACE,
                "json",
                lambda value: _set_nested(
                    value, ("plugins", 0, "name"), "wrong-plugin"
                ),
            ),
            (
                "Codex marketplace identity drift",
                CODEX_MARKETPLACE,
                "json",
                lambda value: _set_nested(value, ("name",), "wrong-marketplace"),
            ),
            (
                "Codex marketplace display identity drift",
                CODEX_MARKETPLACE,
                "json",
                lambda value: _set_nested(
                    value, ("interface", "displayName"), "Wrong Marketplace"
                ),
            ),
            (
                "Codex plugin identity drift",
                CODEX_MARKETPLACE,
                "json",
                lambda value: _set_nested(
                    value, ("plugins", 0, "name"), "wrong-plugin"
                ),
            ),
        )

        for name, relative_path, mutation_kind, mutate in mutations:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                isolated_root = Path(directory)
                self._copy_canonical_inputs(isolated_root)
                target = isolated_root / relative_path
                if mutation_kind == "raw":
                    target.write_text(
                        mutate(target.read_text(encoding="utf-8")),
                        encoding="utf-8",
                        newline="\n",
                    )
                else:
                    self._mutate_json(isolated_root, relative_path, mutate)

                with self.assertRaises(sync.CanonicalInputError) as raised:
                    sync.load_canonical_inputs(isolated_root)

                diagnostic = str(raised.exception)
                self.assertNotIn(str(isolated_root), diagnostic)
                self.assertNotIn(str(ROOT), diagnostic)
                self.assertFalse(Path(diagnostic).is_absolute())


if __name__ == "__main__":
    unittest.main()
