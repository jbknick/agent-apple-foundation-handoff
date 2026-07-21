from __future__ import annotations

from contextlib import contextmanager
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
PLUGIN_DESCRIPTION = (
    "Design, implement, review, debug, and validate Apple Foundation Models "
    "handoff architectures."
)
SHORT_DESCRIPTION = "Five workflows plus one non-positive router."
LONG_DESCRIPTION = (
    "Five workflows plus one non-positive router for Apple Foundation Models "
    "handoff requests, with explicit Apple API availability, state, trust, "
    "recovery, and evidence boundaries."
)
DEFAULT_PROMPT = (
    "Design an Apple Foundation Models baton pass from a research profile to a "
    "review profile that owns the final answer."
)
WORKFLOW_SKILLS = (
    "design-apple-foundation-models-handoff",
    "implement-apple-foundation-models-handoff",
    "review-apple-foundation-models-handoff",
    "debug-apple-foundation-models-handoff",
    "validate-apple-foundation-models-handoff",
)
ROUTER_SKILL = "route-apple-foundation-models-handoff"
ALL_CAPABILITIES = (*WORKFLOW_SKILLS, ROUTER_SKILL)
ALLOWED_PACKAGE_FILES = {
    ".claude-plugin/plugin.json",
    ".codex-plugin/plugin.json",
    "metadata/codex-interface.json",
    *REFERENCE_FILES,
    *(f"skills/{skill}/SKILL.md" for skill in ALL_CAPABILITIES),
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
    "skills": "directory",
    **{
        entry: entry_type
        for skill in ALL_CAPABILITIES
        for entry, entry_type in (
            (f"skills/{skill}", "directory"),
            (f"skills/{skill}/SKILL.md", "file"),
        )
    },
}
FORBIDDEN_SURFACES = (
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


def create_reference_plugin_package(plugin_root: Path) -> None:
    plugin_root.mkdir()
    for relative_path, entry_type in ALLOWED_PACKAGE_ENTRIES.items():
        target = plugin_root / relative_path
        if entry_type == "directory":
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("reference fixture\n", encoding="utf-8")


class PluginContractTests(unittest.TestCase):
    def test_canonical_guidance_truthfully_names_present_references(self):
        canonical = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        generated = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        required = (
            "Exactly five package reference files are present",
            "Hooks, commands, agents, MCP servers, package scripts, "
            "dependencies, and runtime code remain absent",
            "zero runtime capabilities",
        )
        for text in (canonical, generated):
            flat = " ".join(text.split())
            for token in required:
                self.assertIn(token, flat)
            self.assertNotIn("Skills, references, hooks", text)

    def test_canonical_identity_is_exact_and_honest(self):
        manifest = load_json(
            "plugins/apple-foundation-models-handoff/.claude-plugin/plugin.json"
        )

        self.assertEqual(PLUGIN_ID, manifest["name"])
        self.assertEqual(VERSION, manifest["version"])
        self.assertEqual(PLUGIN_DESCRIPTION, manifest["description"])
        self.assertEqual(REPOSITORY, manifest["homepage"])
        self.assertEqual(REPOSITORY, manifest["repository"])
        self.assertEqual("./skills/", manifest.get("skills"))
        skills_root = ROOT / "plugins" / PLUGIN_ID / manifest["skills"]
        self.assertEqual(
            sorted(ALL_CAPABILITIES),
            sorted(path.name for path in skills_root.iterdir() if path.is_dir()),
        )
        for field in ("hooks", "mcpServers", "apps", "commands", "agents"):
            self.assertNotIn(field, manifest)

    def test_codex_interface_advertises_five_workflows_plus_one_router(self):
        interface = load_json(
            "plugins/apple-foundation-models-handoff/metadata/codex-interface.json"
        )

        self.assertEqual(SHORT_DESCRIPTION, interface["shortDescription"])
        self.assertEqual(LONG_DESCRIPTION, interface["longDescription"])
        self.assertEqual("Developer Tools", interface["category"])
        self.assertEqual(list(ALL_CAPABILITIES), interface["capabilities"])
        self.assertEqual(list(WORKFLOW_SKILLS), interface["capabilities"][:-1])
        self.assertEqual(ROUTER_SKILL, interface["capabilities"][-1])
        self.assertIn("Five workflows plus one non-positive router", LONG_DESCRIPTION)
        self.assertEqual([DEFAULT_PROMPT], interface["defaultPrompt"])
        self.assertEqual(116, len(DEFAULT_PROMPT))
        self.assertLessEqual(len(DEFAULT_PROMPT), 128)
        for meta_instruction in ("select", "appropriate workflow", "which capability"):
            self.assertNotIn(meta_instruction, DEFAULT_PROMPT.lower())
        for stale_claim in ("metadata-only", "scaffold", "not included"):
            self.assertNotIn(stale_claim, json.dumps(interface).lower())

    def test_each_capability_resolves_to_one_authored_skill_with_the_same_name(self):
        interface = load_json(
            "plugins/apple-foundation-models-handoff/metadata/codex-interface.json"
        )
        skills_root = ROOT / "plugins" / PLUGIN_ID / "skills"

        self.assertEqual(list(ALL_CAPABILITIES), interface["capabilities"])
        self.assertEqual(
            set(ALL_CAPABILITIES), {path.name for path in skills_root.iterdir()}
        )
        for capability in interface["capabilities"]:
            with self.subTest(capability=capability):
                skill_file = skills_root / capability / "SKILL.md"
                self.assertTrue(skill_file.is_file())
                self.assertFalse(skill_file.is_symlink())
                text = skill_file.read_text(encoding="utf-8")
                self.assertTrue(text.startswith(f"---\nname: {capability}\n"))

    def test_marketplaces_use_the_conventional_source(self):
        claude = load_json(".claude-plugin/marketplace.json")
        codex = load_json("metadata/codex-marketplace.json")
        generated_codex = load_json(".agents/plugins/marketplace.json")

        self.assertEqual(MARKETPLACE, claude["name"])
        self.assertEqual(SOURCE, claude["plugins"][0]["source"])
        self.assertEqual(PLUGIN_DESCRIPTION, claude["plugins"][0]["description"])
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
        self.assertEqual("./skills/", generated.get("skills"))
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
        self.assertEqual(
            {"const": list(ALL_CAPABILITIES)}, interface_properties["capabilities"]
        )
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

        missing_capabilities = json.loads(json.dumps(canonical_interface))
        del missing_capabilities["capabilities"]
        with self.assertRaises(ValueError):
            sync._validate_codex_interface(missing_capabilities)

        interface_boundary_mutations = (
            ("empty capabilities", ("capabilities",), []),
            (
                "reordered capabilities",
                ("capabilities",),
                list(reversed(ALL_CAPABILITIES)),
            ),
            (
                "missing router capability",
                ("capabilities",),
                list(WORKFLOW_SKILLS),
            ),
            (
                "duplicated capability",
                ("capabilities",),
                [*ALL_CAPABILITIES, ROUTER_SKILL],
            ),
            (
                "seventh capability",
                ("capabilities",),
                [*ALL_CAPABILITIES, "extra-apple-foundation-models-handoff"],
            ),
            (
                "substituted router",
                ("capabilities",),
                [*WORKFLOW_SKILLS, "wrong-router"],
            ),
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

    def test_plugin_package_contains_only_references_workflows_and_router(self):
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
            if skills.exists():
                shutil.rmtree(skills)
            skills.symlink_to(temporary_root / "missing-skills", target_is_directory=True)

            self.assertTrue(os.path.lexists(skills))
            with self.assertRaises(AssertionError):
                assert_plugin_package_contract(self, plugin_root)

    def test_package_oracle_rejects_forbidden_capability_and_runtime_surfaces(self):
        forbidden_paths = (
            "agents/openai.yaml",
            "commands/extra.md",
            "hooks/hooks.json",
            "mcp/server.json",
            "package.json",
            f"skills/{WORKFLOW_SKILLS[0]}/SKILL-copy.md",
            f"skills/{WORKFLOW_SKILLS[0]}/output-contract.json",
            f"skills/{WORKFLOW_SKILLS[0]}/agents/openai.yaml",
            f"skills/{WORKFLOW_SKILLS[0]}/references/copied.md",
        )
        for relative_path in forbidden_paths:
            with (
                self.subTest(relative_path=relative_path),
                tempfile.TemporaryDirectory() as directory,
            ):
                plugin_root = Path(directory) / PLUGIN_ID
                create_reference_plugin_package(plugin_root)
                assert_plugin_package_contract(self, plugin_root)
                forbidden = plugin_root / relative_path
                forbidden.parent.mkdir(parents=True, exist_ok=True)
                forbidden.write_text("forbidden surface\n", encoding="utf-8")

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
    @contextmanager
    def patched_probe(self, *, drift_after_teardown=False):
        calls: list[str] = []
        emitted: list[dict[str, object]] = []
        temporary_directory = tempfile.TemporaryDirectory

        @contextmanager
        def marked_temporary_directory():
            with temporary_directory() as directory:
                yield directory
            calls.append("teardown")

        def require_stable_host(*_args):
            calls.append("host")
            if drift_after_teardown and "teardown" in calls:
                raise codex_probe.ProbeFailure("host_resolution_or_version_drift")

        source_hashes = {
            relative_path: "a" * 64
            for relative_path in codex_probe.EXPECTED_CACHE_FILES
        }
        with tempfile.TemporaryDirectory() as directory:
            locator = Path(directory) / "codex"
            locator.write_text("#!/bin/sh\n", encoding="utf-8", newline="\n")
            locator.chmod(0o700)
            with (
                mock.patch.object(
                    codex_probe.shutil, "which", return_value=str(locator)
                ),
                mock.patch.object(
                    codex_probe,
                    "stable_host_version_matches",
                    return_value=True,
                ),
                mock.patch.object(
                    codex_probe.tempfile,
                    "TemporaryDirectory",
                    side_effect=marked_temporary_directory,
                ),
                mock.patch.object(
                    codex_probe,
                    "require_stable_host",
                    side_effect=require_stable_host,
                ),
                mock.patch.object(
                    codex_probe,
                    "install_isolated_plugin",
                    side_effect=lambda *_args: calls.append("install")
                    or Path("cache"),
                ),
                mock.patch.object(
                    codex_probe,
                    "require_source_cache_identity",
                    side_effect=lambda *_args: calls.append("identity") or source_hashes,
                ),
                mock.patch.object(
                    codex_probe,
                    "read_regular_file",
                    return_value=json.dumps(
                        {
                            "interface": {
                                "capabilities": codex_probe.EXPECTED_CAPABILITIES
                            }
                        }
                    ).encode("utf-8"),
                ),
                mock.patch.object(
                    codex_probe, "emit_result", side_effect=emitted.append
                ),
            ):
                yield calls, emitted

    def test_probe_brackets_install_identity_and_teardown_with_host_checks(self):
        with self.patched_probe() as (calls, emitted):
            self.assertEqual(0, codex_probe.main())

        self.assertEqual(
            ["host", "install", "host", "identity", "host", "teardown", "host"],
            calls,
        )
        self.assertEqual("pass", emitted[0]["status"])

    def test_main_fails_closed_when_host_drifts_after_teardown(self):
        with self.patched_probe(drift_after_teardown=True) as (_calls, emitted):
            self.assertEqual(1, codex_probe.main())

        self.assertEqual(
            [
                {
                    "evidenceId": codex_probe.EVIDENCE_ID,
                    "reason": "host_resolution_or_version_drift",
                    "status": "fail",
                }
            ],
            emitted,
        )

    def test_main_brackets_the_initial_version_check_with_host_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            locator = Path(directory) / "codex"
            locator.write_text(
                "#!/bin/sh\nprintf 'codex-cli 0.144.5\\n'\n",
                encoding="utf-8",
                newline="\n",
            )
            locator.chmod(0o700)
            emitted: list[dict[str, object]] = []
            payload = {"evidenceId": codex_probe.EVIDENCE_ID, "status": "pass"}

            with (
                mock.patch.object(codex_probe.shutil, "which", return_value=str(locator)),
                mock.patch.object(
                    codex_probe,
                    "stable_host_version_matches",
                    return_value=True,
                ) as stable_version,
                mock.patch.object(
                    codex_probe,
                    "exact_version",
                    side_effect=AssertionError("unbracketed version check"),
                ),
                mock.patch.object(codex_probe, "probe", return_value=payload),
                mock.patch.object(codex_probe, "emit_result", side_effect=emitted.append),
            ):
                self.assertEqual(0, codex_probe.main())

            stable_version.assert_called_once()
            self.assertEqual([payload], emitted)

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
