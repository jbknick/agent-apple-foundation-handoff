from __future__ import annotations

import importlib.util
import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


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
SKILLS_ROOT = Path("plugins/apple-foundation-models-handoff/skills")
CANONICAL_INPUTS = (
    Path("CLAUDE.md"),
    CLAUDE_MARKETPLACE,
    CODEX_MARKETPLACE,
    SHARED_MANIFEST,
    CODEX_INTERFACE,
)
GENERATED_OUTPUTS = (
    Path("AGENTS.md"),
    Path(".agents/plugins/marketplace.json"),
    Path(
        "plugins/apple-foundation-models-handoff/"
        ".codex-plugin/plugin.json"
    ),
)
SKILLS = (
    "design-apple-foundation-models-handoff",
    "implement-apple-foundation-models-handoff",
    "review-apple-foundation-models-handoff",
    "debug-apple-foundation-models-handoff",
    "validate-apple-foundation-models-handoff",
)
PLUGIN_DESCRIPTION = (
    "Design, implement, review, debug, and validate Apple Foundation Models "
    "handoff architectures."
)
DEFAULT_PROMPT = (
    "Design an Apple Foundation Models baton pass from a research profile to a "
    "review profile that owns the final answer."
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


class _SwapAfterScandir:
    def __init__(self, iterator, swap) -> None:
        self.iterator = iterator
        self.swap = swap

    def __enter__(self):
        return self.iterator.__enter__()

    def __exit__(self, exception_type, exception, traceback):
        result = self.iterator.__exit__(exception_type, exception, traceback)
        self.swap()
        return result


class GeneratedArtifactTests(unittest.TestCase):
    def _copy_canonical_inputs(self, destination: Path) -> None:
        for relative_path in CANONICAL_INPUTS:
            target = destination / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative_path, target)
        shutil.copytree(
            ROOT / SKILLS_ROOT,
            destination / SKILLS_ROOT,
        )

    def _assert_private_safe_skill_error(
        self,
        raised: sync.CanonicalInputError,
        *private_paths: Path,
    ) -> None:
        diagnostic = str(raised)
        self.assertEqual(SKILLS_ROOT.as_posix(), diagnostic)
        for private_path in private_paths:
            self.assertNotIn(str(private_path), diagnostic)
        self.assertFalse(Path(diagnostic).is_absolute())

    def _run_isolated_cli(
        self, root: Path, mode: str
    ) -> subprocess.CompletedProcess[str]:
        scripts = root / "scripts"
        scripts.mkdir(exist_ok=True)
        shutil.copyfile(SCRIPT, scripts / "sync_generated_artifacts.py")
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        return subprocess.run(
            [sys.executable, str(scripts / "sync_generated_artifacts.py"), mode],
            cwd=root,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )

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

    def _assert_rendered_json_is_rejected_before_destination_inspection(
        self,
        renderer_name: str,
        rendered: bytes,
        relative_path: Path,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            isolated_root = Path(directory)
            self._copy_canonical_inputs(isolated_root)
            self.assertTrue(sync.synchronize(isolated_root, write=True))
            before = {
                path: (isolated_root / path).read_bytes()
                for path in GENERATED_OUTPUTS
            }
            diagnostic = io.StringIO()

            with mock.patch.object(sync, renderer_name, return_value=rendered):
                with mock.patch.object(sync, "_scan_generated_namespaces") as scan:
                    with contextlib.redirect_stderr(diagnostic):
                        synchronized = sync.synchronize(isolated_root, write=True)

            self.assertFalse(synchronized)
            scan.assert_not_called()
            self.assertEqual(
                f"{relative_path.as_posix()}: "
                "unsafe or unwritable generated output\n",
                diagnostic.getvalue(),
            )
            self.assertEqual(
                before,
                {
                    path: (isolated_root / path).read_bytes()
                    for path in GENERATED_OUTPUTS
                },
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
        self.assertEqual(PLUGIN_DESCRIPTION, rendered["description"])
        self.assertEqual(list(SKILLS), rendered["interface"]["capabilities"])
        self.assertEqual([DEFAULT_PROMPT], rendered["interface"]["defaultPrompt"])
        self.assertEqual("./skills/", rendered.get("skills"))
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
                "skills",
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

    def test_malformed_rendered_json_is_rejected_before_destination_inspection(self):
        inputs = sync.load_canonical_inputs(ROOT)
        marketplace_with_duplicate_key = sync.render_codex_marketplace(inputs).replace(
            b'  "name": "agent-apple-foundation-handoff",\n',
            b'  "name": "agent-apple-foundation-handoff",\n'
            b'  "name": "agent-apple-foundation-handoff",\n',
            1,
        )
        cases = (
            (
                "manifest malformed JSON",
                "render_codex_manifest",
                b"not-json\n",
                GENERATED_OUTPUTS[2],
            ),
            (
                "marketplace invalid UTF-8",
                "render_codex_marketplace",
                b"\xff\n",
                GENERATED_OUTPUTS[1],
            ),
            (
                "marketplace duplicate key",
                "render_codex_marketplace",
                marketplace_with_duplicate_key,
                GENERATED_OUTPUTS[1],
            ),
        )

        for name, renderer_name, rendered, relative_path in cases:
            with self.subTest(name=name):
                self._assert_rendered_json_is_rejected_before_destination_inspection(
                    renderer_name, rendered, relative_path
                )

    def test_renderer_ownership_and_closed_shapes_are_enforced_before_writes(self):
        inputs = sync.load_canonical_inputs(ROOT)
        manifest_ownership_drift = json.loads(sync.render_codex_manifest(inputs))
        manifest_ownership_drift["description"] = "Renderer-owned description drift."
        manifest_extra_key = json.loads(sync.render_codex_manifest(inputs))
        manifest_extra_key["unexpected"] = True
        marketplace_ownership_drift = json.loads(sync.render_codex_marketplace(inputs))
        marketplace_ownership_drift["plugins"][0]["name"] = "wrong-plugin"
        marketplace_extra_key = json.loads(sync.render_codex_marketplace(inputs))
        marketplace_extra_key["plugins"][0]["unexpected"] = True
        cases = (
            (
                "manifest ownership drift",
                "render_codex_manifest",
                manifest_ownership_drift,
                GENERATED_OUTPUTS[2],
            ),
            (
                "manifest extra key",
                "render_codex_manifest",
                manifest_extra_key,
                GENERATED_OUTPUTS[2],
            ),
            (
                "marketplace ownership drift",
                "render_codex_marketplace",
                marketplace_ownership_drift,
                GENERATED_OUTPUTS[1],
            ),
            (
                "marketplace extra key",
                "render_codex_marketplace",
                marketplace_extra_key,
                GENERATED_OUTPUTS[1],
            ),
        )

        for name, renderer_name, rendered, relative_path in cases:
            with self.subTest(name=name):
                self._assert_rendered_json_is_rejected_before_destination_inspection(
                    renderer_name,
                    (json.dumps(rendered, ensure_ascii=False, indent=2) + "\n").encode(
                        "utf-8"
                    ),
                    relative_path,
                )

    def test_write_creates_all_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            isolated_root = Path(directory)
            self._copy_canonical_inputs(isolated_root)
            expected = sync.expected_artifacts(isolated_root)

            result = self._run_isolated_cli(isolated_root, "--write")

            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual("updated generated artifacts\n", result.stdout)
            self.assertEqual("", result.stderr)
            self.assertEqual(set(GENERATED_OUTPUTS), set(expected))
            for relative_path, content in expected.items():
                with self.subTest(relative_path=relative_path):
                    self.assertEqual(content, (isolated_root / relative_path).read_bytes())

    def test_write_is_byte_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            isolated_root = Path(directory)
            self._copy_canonical_inputs(isolated_root)
            first = self._run_isolated_cli(isolated_root, "--write")
            self.assertEqual(0, first.returncode, first.stderr)
            snapshot = {
                path: (isolated_root / path).read_bytes()
                for path in GENERATED_OUTPUTS
            }

            second = self._run_isolated_cli(isolated_root, "--write")

            self.assertEqual(0, second.returncode, second.stderr)
            self.assertEqual("generated artifacts are synchronized\n", second.stdout)
            self.assertEqual(
                snapshot,
                {path: (isolated_root / path).read_bytes() for path in GENERATED_OUTPUTS},
            )

    def test_check_rejects_drift_in_each_output_without_writing(self):
        for drifted in GENERATED_OUTPUTS:
            with self.subTest(drifted=drifted), tempfile.TemporaryDirectory() as directory:
                isolated_root = Path(directory)
                self._copy_canonical_inputs(isolated_root)
                written = self._run_isolated_cli(isolated_root, "--write")
                self.assertEqual(0, written.returncode, written.stderr)
                with (isolated_root / drifted).open("ab") as output:
                    output.write(b"drift\n")
                snapshot = {
                    path: (isolated_root / path).read_bytes()
                    for path in GENERATED_OUTPUTS
                }

                result = self._run_isolated_cli(isolated_root, "--check")

                self.assertEqual(1, result.returncode)
                self.assertEqual("", result.stdout)
                self.assertEqual(
                    f"{drifted.as_posix()}: generated content is out of date\n",
                    result.stderr,
                )
                self.assertEqual(
                    snapshot,
                    {
                        path: (isolated_root / path).read_bytes()
                        for path in GENERATED_OUTPUTS
                    },
                )

    def test_preflight_prevents_partial_write(self):
        with tempfile.TemporaryDirectory() as directory:
            isolated_root = Path(directory)
            self._copy_canonical_inputs(isolated_root)
            written = self._run_isolated_cli(isolated_root, "--write")
            self.assertEqual(0, written.returncode, written.stderr)
            agents = isolated_root / "AGENTS.md"
            stale = b"stale AGENTS output\n"
            agents.write_bytes(stale)
            shutil.rmtree(isolated_root / ".agents", ignore_errors=True)
            (isolated_root / ".agents").write_text(
                "obstruction\n", encoding="utf-8", newline="\n"
            )

            result = self._run_isolated_cli(isolated_root, "--write")

            self.assertEqual(1, result.returncode)
            self.assertEqual("", result.stdout)
            self.assertEqual(
                ".agents/plugins/marketplace.json: unsafe or unwritable generated output\n",
                result.stderr,
            )
            self.assertEqual(stale, agents.read_bytes())

    def test_nested_parent_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            temporary_root = Path(directory)
            isolated_root = temporary_root / "repository"
            isolated_root.mkdir()
            self._copy_canonical_inputs(isolated_root)
            external = temporary_root / "external"
            external.mkdir()
            sentinel = external / "plugin.json"
            original = b"external target\n"
            sentinel.write_bytes(original)
            plugin_root = isolated_root / "plugins/apple-foundation-models-handoff"
            (plugin_root / ".codex-plugin").symlink_to(external, target_is_directory=True)

            result = self._run_isolated_cli(isolated_root, "--write")

            self.assertEqual(1, result.returncode)
            self.assertEqual("", result.stdout)
            self.assertEqual(
                "plugins/apple-foundation-models-handoff/.codex-plugin/plugin.json: "
                "unsafe or unwritable generated output\n",
                result.stderr,
            )
            self.assertEqual(original, sentinel.read_bytes())
            self.assertFalse((isolated_root / "AGENTS.md").exists())

    def test_generated_output_symlink_cannot_mutate_target(self):
        with tempfile.TemporaryDirectory() as directory:
            temporary_root = Path(directory)
            isolated_root = temporary_root / "repository"
            isolated_root.mkdir()
            self._copy_canonical_inputs(isolated_root)
            external = temporary_root / "external-marketplace"
            original = b"external target\n"
            external.write_bytes(original)
            output = isolated_root / ".agents/plugins/marketplace.json"
            output.parent.mkdir(parents=True)
            output.symlink_to(external)

            result = self._run_isolated_cli(isolated_root, "--write")

            self.assertEqual(1, result.returncode)
            self.assertEqual(original, external.read_bytes())
            self.assertTrue(output.is_symlink())
            self.assertEqual(
                ".agents/plugins/marketplace.json: unsafe or unwritable generated output\n",
                result.stderr,
            )

    def test_unexpected_generated_file_is_rejected(self):
        unexpected_paths = (
            Path(".agents/plugins/unexpected.json"),
            Path(
                "plugins/apple-foundation-models-handoff/"
                ".codex-plugin/unexpected.json"
            ),
        )
        for unexpected in unexpected_paths:
            with self.subTest(unexpected=unexpected), tempfile.TemporaryDirectory() as directory:
                isolated_root = Path(directory)
                self._copy_canonical_inputs(isolated_root)
                target = isolated_root / unexpected
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("{}\n", encoding="utf-8", newline="\n")

                result = self._run_isolated_cli(isolated_root, "--check")

                self.assertEqual(1, result.returncode)
                self.assertEqual("", result.stdout)
                self.assertEqual(
                    "generated artifacts: unexpected generated path\n", result.stderr
                )

    def test_unexpected_empty_generated_directory_is_rejected(self):
        unexpected_paths = (
            Path(".agents/plugins/unowned-empty-directory"),
            Path(
                "plugins/apple-foundation-models-handoff/"
                ".codex-plugin/unowned-empty-directory"
            ),
        )
        for unexpected in unexpected_paths:
            with self.subTest(
                unexpected=unexpected
            ), tempfile.TemporaryDirectory() as directory:
                isolated_root = Path(directory)
                self._copy_canonical_inputs(isolated_root)
                written = self._run_isolated_cli(isolated_root, "--write")
                self.assertEqual(0, written.returncode, written.stderr)
                (isolated_root / unexpected).mkdir()

                result = self._run_isolated_cli(isolated_root, "--check")

                self.assertEqual(1, result.returncode)
                self.assertEqual("", result.stdout)
                self.assertEqual(
                    "generated artifacts: unexpected generated path\n", result.stderr
                )

    def test_root_agents_staging_name_is_rejected_in_check_and_write_modes(self):
        unrelated_names = (
            ".AGENTS.md.not-a-generator-token.tmp",
            ".AGENTS.md.AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA.tmp",
            "unrelated-root-file.txt",
        )
        with tempfile.TemporaryDirectory() as directory:
            isolated_root = Path(directory)
            self._copy_canonical_inputs(isolated_root)
            self.assertTrue(sync.synchronize(isolated_root, write=True))
            for name in unrelated_names:
                (isolated_root / name).write_text(
                    "unrelated\n", encoding="utf-8", newline="\n"
                )

            accepted = self._run_isolated_cli(isolated_root, "--check")

            self.assertEqual(0, accepted.returncode, accepted.stderr)
            self.assertEqual(
                "generated artifacts are synchronized\n", accepted.stdout
            )

        for mode in ("--check", "--write"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                isolated_root = Path(directory)
                self._copy_canonical_inputs(isolated_root)
                self.assertTrue(sync.synchronize(isolated_root, write=True))
                staging = isolated_root / (
                    ".AGENTS.md.0123456789abcdef0123456789abcdef.tmp"
                )
                staging.write_text("stale\n", encoding="utf-8", newline="\n")
                agents = isolated_root / "AGENTS.md"
                if mode == "--write":
                    agents.write_bytes(b"stale generated output\n")
                snapshot = agents.read_bytes()

                result = self._run_isolated_cli(isolated_root, mode)

                self.assertEqual(1, result.returncode)
                self.assertEqual("", result.stdout)
                self.assertEqual(
                    "generated artifacts: unexpected generated path\n",
                    result.stderr,
                )
                self.assertEqual(snapshot, agents.read_bytes())
                self.assertTrue(staging.is_file())

    def test_missing_nested_parents_are_drift_then_created_safely(self):
        with tempfile.TemporaryDirectory() as directory:
            isolated_root = Path(directory)
            self._copy_canonical_inputs(isolated_root)
            expected = sync.expected_artifacts(isolated_root)
            (isolated_root / "AGENTS.md").write_bytes(expected[Path("AGENTS.md")])

            checked = self._run_isolated_cli(isolated_root, "--check")

            self.assertEqual(1, checked.returncode)
            self.assertEqual(
                ".agents/plugins/marketplace.json: generated content is out of date\n"
                "plugins/apple-foundation-models-handoff/.codex-plugin/plugin.json: "
                "generated content is out of date\n",
                checked.stderr,
            )
            self.assertFalse((isolated_root / ".agents").exists())
            self.assertFalse(
                (
                    isolated_root
                    / "plugins/apple-foundation-models-handoff/.codex-plugin"
                ).exists()
            )

            written = self._run_isolated_cli(isolated_root, "--write")

            self.assertEqual(0, written.returncode, written.stderr)
            self.assertEqual("updated generated artifacts\n", written.stdout)
            for relative_path, content in expected.items():
                self.assertEqual(content, (isolated_root / relative_path).read_bytes())

    def test_temporary_path_swap_is_normalized_and_cleaned(self):
        with tempfile.TemporaryDirectory() as directory:
            temporary_root = Path(directory)
            isolated_root = temporary_root / "repository"
            isolated_root.mkdir()
            self._copy_canonical_inputs(isolated_root)
            generated = isolated_root / "AGENTS.md"
            generated.write_bytes(b"stale generated output\n")
            sentinel = temporary_root / "external-sentinel"
            original = b"external sentinel must remain unchanged\n"
            sentinel.write_bytes(original)
            real_replace = sync.os.replace

            def swap_temporary_path(
                source,
                destination,
                *,
                src_dir_fd=None,
                dst_dir_fd=None,
            ):
                os.unlink(source, dir_fd=src_dir_fd)
                os.symlink(sentinel, source, dir_fd=src_dir_fd)
                return real_replace(
                    source,
                    destination,
                    src_dir_fd=src_dir_fd,
                    dst_dir_fd=dst_dir_fd,
                )

            diagnostic = io.StringIO()
            with mock.patch.object(sync.os, "replace", swap_temporary_path):
                with contextlib.redirect_stderr(diagnostic):
                    synchronized = sync.synchronize(isolated_root, write=True)

            self.assertFalse(synchronized)
            self.assertEqual(
                "AGENTS.md: unsafe or unwritable generated output\n",
                diagnostic.getvalue(),
            )
            self.assertEqual(original, sentinel.read_bytes())
            self.assertFalse(os.path.lexists(generated))
            self.assertEqual([], list(isolated_root.glob(".AGENTS.md.*.tmp")))

    def test_atomic_replace_failure_is_normalized_and_cleans_temporary(self):
        with tempfile.TemporaryDirectory() as directory:
            isolated_root = Path(directory)
            self._copy_canonical_inputs(isolated_root)
            generated = isolated_root / "AGENTS.md"
            original = b"stale generated output\n"
            generated.write_bytes(original)
            diagnostic = io.StringIO()

            with mock.patch.object(sync.os, "replace", side_effect=OSError):
                with contextlib.redirect_stderr(diagnostic):
                    synchronized = sync.synchronize(isolated_root, write=True)

            self.assertFalse(synchronized)
            self.assertEqual(
                "AGENTS.md: unsafe or unwritable generated output\n",
                diagnostic.getvalue(),
            )
            self.assertEqual(original, generated.read_bytes())
            self.assertFalse(generated.is_symlink())
            self.assertEqual([], list(isolated_root.glob(".AGENTS.md.*.tmp")))

    def test_later_temporary_open_failure_prevents_every_replacement(self):
        with tempfile.TemporaryDirectory() as directory:
            isolated_root = Path(directory)
            self._copy_canonical_inputs(isolated_root)
            self.assertTrue(sync.synchronize(isolated_root, write=True))

            agents = isolated_root / GENERATED_OUTPUTS[0]
            marketplace = isolated_root / GENERATED_OUTPUTS[1]
            agents.write_bytes(b"stale AGENTS output\n")
            marketplace.write_bytes(b"stale marketplace output\n")
            before = {
                path: (isolated_root / path).read_bytes()
                for path in GENERATED_OUTPUTS
            }
            real_open = sync.os.open

            def fail_marketplace_temporary_open(
                path,
                flags,
                mode=0o777,
                *,
                dir_fd=None,
            ):
                if (
                    isinstance(path, str)
                    and path.startswith(".marketplace.json.")
                    and path.endswith(".tmp")
                    and flags & os.O_CREAT
                ):
                    raise PermissionError
                return real_open(path, flags, mode, dir_fd=dir_fd)

            diagnostic = io.StringIO()
            with mock.patch.object(sync.os, "open", fail_marketplace_temporary_open):
                with contextlib.redirect_stderr(diagnostic):
                    synchronized = sync.synchronize(isolated_root, write=True)

            self.assertFalse(synchronized)
            self.assertEqual(
                ".agents/plugins/marketplace.json: "
                "unsafe or unwritable generated output\n",
                diagnostic.getvalue(),
            )
            self.assertEqual(
                before,
                {
                    path: (isolated_root / path).read_bytes()
                    for path in GENERATED_OUTPUTS
                },
            )
            temporary_paths = []
            for output in GENERATED_OUTPUTS:
                temporary_paths.extend(
                    (isolated_root / output.parent).glob(f".{output.name}.*.tmp")
                )
            self.assertEqual([], temporary_paths)

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

    def test_capability_boundary_mutations_are_rejected(self):
        mutations = (
            ("missing", None),
            ("reordered", list(reversed(SKILLS))),
            ("duplicate", [*SKILLS[:-1], SKILLS[-2]]),
            ("sixth", [*SKILLS, "extra-apple-foundation-models-handoff"]),
        )
        for name, replacement in mutations:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                isolated_root = Path(directory)
                self._copy_canonical_inputs(isolated_root)
                if replacement is None:
                    self._mutate_json(
                        isolated_root,
                        CODEX_INTERFACE,
                        lambda value: _delete_nested(value, ("capabilities",)),
                    )
                else:
                    self._mutate_json(
                        isolated_root,
                        CODEX_INTERFACE,
                        lambda value, replacement=replacement: _set_nested(
                            value, ("capabilities",), replacement
                        ),
                    )

                with self.assertRaises(sync.CanonicalInputError) as raised:
                    sync.load_canonical_inputs(isolated_root)

                self.assertEqual(CODEX_INTERFACE.as_posix(), str(raised.exception))

    def test_skills_root_swap_to_external_exact_tree_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            temporary_root = Path(directory)
            isolated_root = temporary_root / "repository"
            isolated_root.mkdir()
            self._copy_canonical_inputs(isolated_root)
            skills_root = isolated_root / SKILLS_ROOT
            external = temporary_root / "external-skills"
            original = temporary_root / "original-skills"
            shutil.copytree(skills_root, external)
            real_scandir = sync.os.scandir
            calls = 0
            swapped = False

            def swap_root() -> None:
                nonlocal swapped
                skills_root.rename(original)
                skills_root.symlink_to(external, target_is_directory=True)
                swapped = True

            def attacked_scandir(path):
                nonlocal calls
                calls += 1
                iterator = real_scandir(path)
                if calls == 1:
                    return _SwapAfterScandir(iterator, swap_root)
                return iterator

            with mock.patch.object(sync.os, "scandir", attacked_scandir):
                with self.assertRaises(sync.CanonicalInputError) as raised:
                    sync.load_canonical_inputs(isolated_root)

            self.assertTrue(swapped)
            self._assert_private_safe_skill_error(
                raised.exception,
                isolated_root,
                external,
                original,
            )

    def test_skill_child_swap_to_external_exact_tree_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            temporary_root = Path(directory)
            isolated_root = temporary_root / "repository"
            isolated_root.mkdir()
            self._copy_canonical_inputs(isolated_root)
            skill_directory = isolated_root / SKILLS_ROOT / SKILLS[0]
            external = temporary_root / "external-skill"
            original = temporary_root / "original-skill"
            shutil.copytree(skill_directory, external)
            real_scandir = sync.os.scandir
            calls = 0
            swapped = False

            def swap_child() -> None:
                nonlocal swapped
                skill_directory.rename(original)
                skill_directory.symlink_to(external, target_is_directory=True)
                swapped = True

            def attacked_scandir(path):
                nonlocal calls
                calls += 1
                iterator = real_scandir(path)
                if calls == 2:
                    return _SwapAfterScandir(iterator, swap_child)
                return iterator

            with mock.patch.object(sync.os, "scandir", attacked_scandir):
                with self.assertRaises(sync.CanonicalInputError) as raised:
                    sync.load_canonical_inputs(isolated_root)

            self.assertTrue(swapped)
            self._assert_private_safe_skill_error(
                raised.exception,
                isolated_root,
                external,
                original,
            )

    def test_skill_file_identity_swap_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            temporary_root = Path(directory)
            isolated_root = temporary_root / "repository"
            isolated_root.mkdir()
            self._copy_canonical_inputs(isolated_root)
            skill_file = isolated_root / SKILLS_ROOT / SKILLS[0] / "SKILL.md"
            external = temporary_root / "external-SKILL.md"
            original = temporary_root / "original-SKILL.md"
            shutil.copyfile(skill_file, external)
            real_open = sync.os.open
            attacked = False

            def attacked_open(path, flags, mode=0o777, *, dir_fd=None):
                nonlocal attacked
                if not attacked and str(path).endswith("SKILL.md"):
                    skill_file.rename(original)
                    skill_file.symlink_to(external)
                    attacked = True
                return real_open(path, flags, mode, dir_fd=dir_fd)

            with mock.patch.object(sync.os, "open", attacked_open):
                with self.assertRaises(sync.CanonicalInputError) as raised:
                    sync.load_canonical_inputs(isolated_root)

            self.assertTrue(attacked)
            self._assert_private_safe_skill_error(
                raised.exception,
                isolated_root,
                external,
                original,
            )

    def test_skill_component_mutations_are_rejected(self):
        def mutate_first_skill(root: Path, mutate) -> None:
            skill = root / SKILLS_ROOT / SKILLS[0] / "SKILL.md"
            original = skill.read_text(encoding="utf-8")
            mutated = mutate(original)
            self.assertNotEqual(original, mutated)
            skill.write_text(mutated, encoding="utf-8")

        def remove_skill(root: Path) -> None:
            shutil.rmtree(root / SKILLS_ROOT / SKILLS[0])

        def add_sixth_skill(root: Path) -> None:
            extra = (
                root
                / "plugins/apple-foundation-models-handoff/skills/extra-workflow"
            )
            extra.mkdir()
            (extra / "SKILL.md").write_text(
                "---\nname: extra-workflow\ndescription: Extra.\n---\n",
                encoding="utf-8",
            )

        def mismatch_frontmatter(root: Path) -> None:
            mutate_first_skill(
                root,
                lambda text: text.replace(
                    f"name: {SKILLS[0]}", "name: wrong-skill", 1
                ),
            )

        def duplicate_name(root: Path) -> None:
            mutate_first_skill(
                root,
                lambda text: text.replace(
                    f"name: {SKILLS[0]}\n",
                    f"name: {SKILLS[0]}\nname: {SKILLS[0]}\n",
                    1,
                ),
            )

        def duplicate_description(root: Path) -> None:
            def mutate(text: str) -> str:
                description = next(
                    line for line in text.splitlines() if line.startswith("description: ")
                )
                return text.replace(description, f"{description}\n{description}", 1)

            mutate_first_skill(root, mutate)

        def extra_frontmatter_key(root: Path) -> None:
            mutate_first_skill(
                root,
                lambda text: text.replace(
                    f"name: {SKILLS[0]}\n",
                    f"name: {SKILLS[0]}\nunexpected: value\n",
                    1,
                ),
            )

        def missing_closing_delimiter(root: Path) -> None:
            mutate_first_skill(
                root,
                lambda text: text.replace("\n---\n\n#", "\n\n#", 1),
            )

        def malformed_description(root: Path) -> None:
            mutate_first_skill(
                root,
                lambda text: text.replace("\ndescription: ", "\ndescription ", 1),
            )

        for name, mutate in (
            ("missing skill", remove_skill),
            ("sixth skill", add_sixth_skill),
            ("capability name mismatch", mismatch_frontmatter),
            ("duplicate name", duplicate_name),
            ("duplicate description", duplicate_description),
            ("extra frontmatter key", extra_frontmatter_key),
            ("missing closing delimiter", missing_closing_delimiter),
            ("malformed description", malformed_description),
        ):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                isolated_root = Path(directory)
                self._copy_canonical_inputs(isolated_root)
                mutate(isolated_root)

                with self.assertRaises(sync.CanonicalInputError) as raised:
                    sync.load_canonical_inputs(isolated_root)

                self.assertEqual(
                    "plugins/apple-foundation-models-handoff/skills",
                    str(raised.exception),
                )

    def test_exact_capabilities_and_skill_component_are_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            isolated_root = Path(directory)
            self._copy_canonical_inputs(isolated_root)
            inputs = sync.load_canonical_inputs(isolated_root)

            self.assertEqual("./skills/", inputs.shared_manifest.get("skills"))
            self.assertEqual(list(SKILLS), inputs.codex_interface["capabilities"])

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
                lambda value: _set_nested(value, ("unexpected",), True),
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
