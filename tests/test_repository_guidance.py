from __future__ import annotations

import contextlib
import importlib.util
import io
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "sync_generated_artifacts.py"
CANONICAL = ROOT / "CLAUDE.md"
GENERATED = ROOT / "AGENTS.md"
CANONICAL_INPUTS = (
    Path("CLAUDE.md"),
    Path(".claude-plugin/marketplace.json"),
    Path("metadata/codex-marketplace.json"),
    Path("plugins/apple-foundation-models-handoff/.claude-plugin/plugin.json"),
    Path("plugins/apple-foundation-models-handoff/metadata/codex-interface.json"),
)
BEGIN = "<!-- BEGIN GENERATED AGENTS ADAPTER -->"
END = "<!-- END GENERATED AGENTS ADAPTER -->"
HEADER = (
    "# AGENTS.md\n\n"
    "<!-- Generated from CLAUDE.md by scripts/sync_generated_artifacts.py. "
    "Do not edit directly. -->\n\n"
)


spec = importlib.util.spec_from_file_location("sync_generated_artifacts", SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError("unable to load generated-artifact synchronization module")
sync_generated_artifacts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync_generated_artifacts)


def run_isolated_cli(root: Path, mode: str) -> subprocess.CompletedProcess[str]:
    scripts = root / "scripts"
    scripts.mkdir()
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


def normalized_guide(path: Path) -> str:
    return re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))


class _MutateAfterRead:
    def __init__(self, stream, mutation):
        self._stream = stream
        self._mutation = mutation

    def __enter__(self):
        return self

    def __exit__(self, *arguments):
        return self._stream.__exit__(*arguments)

    def __getattr__(self, name):
        return getattr(self._stream, name)

    def read(self, *arguments, **keywords):
        content = self._stream.read(*arguments, **keywords)
        self._mutation()
        return content


@contextlib.contextmanager
def mutate_after_read(read_number: int, mutation):
    real_fdopen = sync_generated_artifacts.os.fdopen
    reads = 0

    def wrapped_fdopen(*arguments, **keywords):
        nonlocal reads
        reads += 1
        stream = real_fdopen(*arguments, **keywords)
        if reads == read_number:
            return _MutateAfterRead(stream, mutation)
        return stream

    with mock.patch.object(
        sync_generated_artifacts.os, "fdopen", side_effect=wrapped_fdopen
    ):
        yield


class RepositoryGuidanceTests(unittest.TestCase):
    def _copy_canonical_inputs(self, destination: Path) -> None:
        for relative_path in CANONICAL_INPUTS:
            target = destination / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative_path, target)

    def test_generated_agents_matches_canonical_adapter_exactly(self):
        canonical_text = CANONICAL.read_text(encoding="utf-8")
        body = canonical_text.split(BEGIN, 1)[1].split(END, 1)[0].strip("\n")
        expected = HEADER + body + "\n"

        self.assertEqual(expected, sync_generated_artifacts.render_agents(canonical_text))
        self.assertEqual(expected.encode("utf-8"), GENERATED.read_bytes())

        crlf_render = sync_generated_artifacts.render_agents(
            canonical_text.replace("\n", "\r\n")
        )
        self.assertNotIn("\r", crlf_render)

        invalid_sections = (
            f"{BEGIN}\n\n{END}\n",
            f"{END}\ncontent\n{BEGIN}\n",
            canonical_text + f"\n{BEGIN}\nduplicate\n{END}\n",
        )
        for invalid in invalid_sections:
            with self.subTest(invalid=invalid[:32]):
                with self.assertRaises(ValueError):
                    sync_generated_artifacts.render_agents(invalid)

    def test_check_mode_passes_for_the_tracked_adapter(self):
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--check"],
            cwd=ROOT,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("generated artifacts are synchronized\n", result.stdout)
        self.assertEqual("", result.stderr)

    def test_write_mode_is_idempotent_in_an_isolated_root(self):
        with tempfile.TemporaryDirectory() as directory:
            isolated_root = Path(directory)
            self._copy_canonical_inputs(isolated_root)

            self.assertTrue(sync_generated_artifacts.synchronize(isolated_root, write=True))
            first_bytes = (isolated_root / "AGENTS.md").read_bytes()
            self.assertTrue(sync_generated_artifacts.synchronize(isolated_root, write=True))

            self.assertEqual(first_bytes, (isolated_root / "AGENTS.md").read_bytes())

    def test_check_mode_rejects_isolated_generated_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            isolated_root = Path(directory)
            self._copy_canonical_inputs(isolated_root)
            self.assertTrue(sync_generated_artifacts.synchronize(isolated_root, write=True))
            with (isolated_root / "AGENTS.md").open(
                "a", encoding="utf-8", newline="\n"
            ) as generated:
                generated.write("drift\n")

            diagnostic = io.StringIO()
            with contextlib.redirect_stderr(diagnostic):
                synchronized = sync_generated_artifacts.synchronize(
                    isolated_root, write=False
                )

            self.assertFalse(synchronized)
            self.assertEqual(
                "AGENTS.md: generated content is out of date\n",
                diagnostic.getvalue(),
            )
            self.assertNotIn(str(isolated_root), diagnostic.getvalue())

    def test_synchronize_normalizes_invalid_canonical_input(self):
        with tempfile.TemporaryDirectory() as directory:
            isolated_root = Path(directory)
            (isolated_root / "CLAUDE.md").write_text(
                "invalid canonical guide\n", encoding="utf-8", newline="\n"
            )
            diagnostic = io.StringIO()

            with contextlib.redirect_stderr(diagnostic):
                synchronized = sync_generated_artifacts.synchronize(
                    isolated_root, write=False
                )

            self.assertFalse(synchronized)
            self.assertEqual(
                "CLAUDE.md: invalid canonical adapter input\n",
                diagnostic.getvalue(),
            )

    def test_generated_output_rejects_symlink_without_mutating_target(self):
        for mode in ("--write", "--check"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                temporary_root = Path(directory)
                isolated_root = temporary_root / "repository"
                isolated_root.mkdir()
                self._copy_canonical_inputs(isolated_root)
                sentinel = temporary_root / "external-sentinel"
                original = b"external sentinel must remain unchanged\n"
                sentinel.write_bytes(original)
                (isolated_root / "AGENTS.md").symlink_to(sentinel)

                result = run_isolated_cli(isolated_root, mode)

                self.assertEqual(original, sentinel.read_bytes())
                self.assertTrue((isolated_root / "AGENTS.md").is_symlink())
                self.assertEqual(1, result.returncode)
                self.assertEqual("", result.stdout)
                self.assertEqual(
                    "AGENTS.md: unsafe or unwritable generated output\n",
                    result.stderr,
                )

    def test_cli_distinguishes_generated_obstruction_from_canonical_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            isolated_root = Path(directory)
            self._copy_canonical_inputs(isolated_root)
            (isolated_root / "AGENTS.md").mkdir()

            result = run_isolated_cli(isolated_root, "--write")

            self.assertEqual(1, result.returncode)
            self.assertEqual("", result.stdout)
            self.assertEqual(
                "AGENTS.md: unsafe or unwritable generated output\n",
                result.stderr,
            )
            self.assertNotIn("CLAUDE.md: invalid canonical metadata input", result.stderr)
            self.assertTrue((isolated_root / "AGENTS.md").is_dir())

        with tempfile.TemporaryDirectory() as directory:
            isolated_root = Path(directory)
            self._copy_canonical_inputs(isolated_root)
            (isolated_root / "CLAUDE.md").write_text(
                "invalid canonical guide\n", encoding="utf-8", newline="\n"
            )

            result = run_isolated_cli(isolated_root, "--write")

            self.assertEqual(1, result.returncode)
            self.assertEqual("", result.stdout)
            self.assertEqual(
                "CLAUDE.md: invalid canonical metadata input\n",
                result.stderr,
            )

    def test_canonical_input_rejects_symlink_without_reading_target(self):
        for mode in ("--write", "--check"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                temporary_root = Path(directory)
                isolated_root = temporary_root / "repository"
                isolated_root.mkdir()
                sentinel = temporary_root / "canonical-sentinel"
                original = CANONICAL.read_bytes()
                sentinel.write_bytes(original)
                (isolated_root / "CLAUDE.md").symlink_to(sentinel)

                result = run_isolated_cli(isolated_root, mode)

                self.assertEqual(original, sentinel.read_bytes())
                self.assertFalse(os.path.lexists(isolated_root / "AGENTS.md"))
                self.assertEqual(1, result.returncode)
                self.assertEqual("", result.stdout)
                self.assertEqual(
                    "CLAUDE.md: invalid canonical metadata input\n",
                    result.stderr,
                )
                self.assertNotIn(str(temporary_root), result.stdout + result.stderr)

    def test_canonical_input_rejects_nonregular_obstruction(self):
        for mode in ("--write", "--check"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                isolated_root = Path(directory)
                (isolated_root / "CLAUDE.md").mkdir()

                result = run_isolated_cli(isolated_root, mode)

                self.assertEqual(1, result.returncode)
                self.assertEqual("", result.stdout)
                self.assertEqual(
                    "CLAUDE.md: invalid canonical metadata input\n",
                    result.stderr,
                )
                self.assertFalse(os.path.lexists(isolated_root / "AGENTS.md"))

    def _assert_post_read_change_is_rejected(
        self, target_name: str, read_number: int, diagnostic_text: str, change: str
    ):
        with tempfile.TemporaryDirectory() as directory:
            isolated_root = Path(directory)
            shutil.copyfile(CANONICAL, isolated_root / "CLAUDE.md")
            self.assertTrue(sync_generated_artifacts.synchronize(isolated_root, True))
            target = isolated_root / target_name

            if change == "replacement":
                replacement = isolated_root / "replacement"
                replacement.write_bytes(target.read_bytes())

                def mutation():
                    os.replace(replacement, target)

            else:

                def mutation():
                    with target.open("ab") as stream:
                        stream.write(b"post-read change\n")

            diagnostic = io.StringIO()
            with mutate_after_read(read_number, mutation):
                with contextlib.redirect_stderr(diagnostic):
                    synchronized = sync_generated_artifacts.synchronize(
                        isolated_root, write=False
                    )

            self.assertFalse(synchronized)
            self.assertEqual(diagnostic_text, diagnostic.getvalue())
            self.assertNotIn(str(isolated_root), diagnostic.getvalue())

    def test_canonical_input_rejects_post_read_changes(self):
        for change in ("replacement", "in-place mutation"):
            with self.subTest(change=change):
                self._assert_post_read_change_is_rejected(
                    "CLAUDE.md",
                    1,
                    "CLAUDE.md: invalid canonical adapter input\n",
                    change,
                )

    def test_generated_output_rejects_post_read_changes(self):
        for change in ("replacement", "in-place mutation"):
            with self.subTest(change=change):
                self._assert_post_read_change_is_rejected(
                    "AGENTS.md",
                    2,
                    "AGENTS.md: unsafe or unwritable generated output\n",
                    change,
                )

    def test_temporary_path_swap_is_rejected_and_cleaned(self):
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
            real_replace = sync_generated_artifacts.os.replace

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
            with mock.patch.object(
                sync_generated_artifacts.os, "replace", swap_temporary_path
            ):
                with contextlib.redirect_stderr(diagnostic):
                    synchronized = sync_generated_artifacts.synchronize(
                        isolated_root, write=True
                    )

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

            with mock.patch.object(
                sync_generated_artifacts.os, "replace", side_effect=OSError
            ):
                with contextlib.redirect_stderr(diagnostic):
                    synchronized = sync_generated_artifacts.synchronize(
                        isolated_root, write=True
                    )

            self.assertFalse(synchronized)
            self.assertEqual(
                "AGENTS.md: unsafe or unwritable generated output\n",
                diagnostic.getvalue(),
            )
            self.assertEqual(original, generated.read_bytes())
            self.assertFalse(generated.is_symlink())
            self.assertEqual([], list(isolated_root.glob(".AGENTS.md.*.tmp")))

    def test_adapter_is_bounded_and_smaller_than_canonical(self):
        canonical_bytes = CANONICAL.read_bytes()
        generated_bytes = GENERATED.read_bytes()

        self.assertLessEqual(len(generated_bytes.decode("utf-8").splitlines()), 90)
        self.assertLessEqual(len(generated_bytes), 6500)
        self.assertLess(len(generated_bytes), len(canonical_bytes))

    def test_only_one_root_agents_file_exists(self):
        agents_files = sorted(ROOT.rglob("AGENTS.md"))

        self.assertEqual([GENERATED], agents_files)
        self.assertFalse(GENERATED.is_symlink())

    def test_guidance_names_canonical_generated_and_non_editable_paths(self):
        canonical_text = CANONICAL.read_text(encoding="utf-8")
        generated_text = GENERATED.read_text(encoding="utf-8")

        for text in (canonical_text, generated_text):
            self.assertIn("`CLAUDE.md` is the only authored canonical", text)
            self.assertIn("`AGENTS.md` is generated", text)
            self.assertIn("Never edit `AGENTS.md` directly", text)
            self.assertIn("`scripts/sync_generated_artifacts.py`", text)

    def test_guidance_distinguishes_current_artifacts_from_planned_payloads(self):
        for guide in (CANONICAL, GENERATED):
            text = normalized_guide(guide)

            self.assertIn(
                "Today the repository-guidance artifact set is exactly authored "
                "canonical `CLAUDE.md` and generated root `AGENTS.md`",
                text,
            )
            self.assertIn(
                "no plugin metadata, skill/reference payload, or generated manifest "
                "is present under DEV-133",
                text,
            )
            self.assertIn(
                "DEV-135 owns planned plugin metadata inputs and generated manifest "
                "outputs",
                text,
            )
            self.assertIn(
                "remain absent until it implements them through the shared "
                "synchronization entry point",
                text,
            )
            self.assertNotIn("Authored canonical inputs include", text)

    def test_guidance_bounds_positive_workflows_and_non_positive_routing(self):
        for guide in (CANONICAL, GENERATED):
            text = normalized_guide(guide)

            self.assertIn(
                "five positive workflows: design, implement, review, debug, and "
                "validate",
                text,
            )
            self.assertIn(
                "may only clarify, decline, or hand off other requests",
                text,
            )
            self.assertIn("not a sixth positive skill", text)
            self.assertIn(
                "distinct from the later DEV-142 through DEV-145 cost "
                "router, `PostToolUse` hook, and Swift bridge chain",
                text,
            )
            self.assertIn(
                "DEV-133 is guidance-only and implements no runtime",
                text,
            )
            self.assertNotIn("Keep exactly five narrow skills", text)
            self.assertNotIn("Select the one skill matching the request", text)

    def test_guidance_commands_and_markdown_links_resolve(self):
        canonical_text = CANONICAL.read_text(encoding="utf-8")
        required_commands = (
            "python3 scripts/sync_generated_artifacts.py --write",
            "python3 scripts/sync_generated_artifacts.py --check",
            "PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests "
            "-p 'test_*.py' -v",
        )
        for command in required_commands:
            self.assertIn(command, canonical_text)

        links = re.findall(r"\[[^]]+\]\(([^)]+)\)", canonical_text)
        self.assertEqual(2, len(links))
        for link in links:
            with self.subTest(link=link):
                self.assertFalse(Path(link).is_absolute())
                self.assertTrue((ROOT / link).is_file())

    def test_guidance_preserves_plugin_payload_and_host_boundaries(self):
        canonical_text = normalized_guide(CANONICAL)
        required_contracts = (
            "DEV-135 selects conventional source "
            "`./plugins/apple-foundation-models-handoff`",
            "effective cached plugin payload",
            "repository-only docs, research, fixtures, tests, and private state",
            "Claude Code `2.1.91`",
            "Codex CLI `0.144.5`",
            "Before host operations, a missing/non-runnable executable",
            "baseline mismatch emits normalized `blocked`",
            "After capture, resolution or version drift emits normalized `fail`",
            "strict single-line version",
            "raw `PATH`",
            "`compiled_sdk_26_5`",
            "`interface_verified_sdk_26_5`",
        )
        for contract in required_contracts:
            with self.subTest(contract=contract):
                self.assertIn(contract, canonical_text)

    def test_guidance_defines_conditional_host_loading_and_status_lifecycle(self):
        canonical_text = normalized_guide(CANONICAL)
        generated_text = normalized_guide(GENERATED)
        required_contracts = (
            "captured approved `2.1.91` executable with session-only `--plugin-dir "
            "<repo>` or an isolated packaging/cache install",
            "Codex `0.144.5` uses its captured executable with isolated `CODEX_HOME`, "
            "marketplace registration, plugin install/add, then a fresh task",
            "`codex --plugin-dir` is not approved",
            "Claude `2.1.140` is diagnostic-only and cannot substitute",
            "metadata-only scaffold with zero capabilities",
            "Skills, references, hooks, commands, agents, MCP servers, scripts, "
            "dependencies, and runtime code are absent",
            "Normalize the repository as `<repo>` and executable as `<host-path>`",
            "never commit literal resolutions, other private absolute paths, or raw "
            "`PATH`",
            "Before host operations, a missing/non-runnable executable, malformed/"
            "unavailable version, or baseline mismatch emits normalized `blocked` "
            "with stable reason/version metadata",
            "After capture, resolution or version drift emits normalized `fail`, "
            "invalidates the row, and requires a fresh run",
        )

        for text in (canonical_text, generated_text):
            self.assertEqual(1, text.count("resolution or version drift"))
            for contract in required_contracts:
                with self.subTest(contract=contract, guide=text[:12]):
                    self.assertIn(contract, text)

    def test_guidance_preserves_safe_synthetic_and_redacted_evidence_exception(self):
        canonical_text = normalized_guide(CANONICAL)
        generated_text = normalized_guide(GENERATED)
        required_contracts = (
            "Exclude raw/live prompts, responses, reasoning, tool arguments/results, "
            "credentials, private configuration, real user/third-party data, raw "
            "diagnostics, `.trace`, and `.xcresult`",
            "hash-bound synthetic or approved-redacted rubric stimulus, bounded rubric "
            "rationales, and redacted summary may be committed only after DEV-131 "
            "path, content, structured-key, classification, and hash scans pass",
            "Runtime/live-host logs, traces, and derived capability telemetry "
            "contribute normalized metadata only.",
        )

        for text in (canonical_text, generated_text):
            for contract in required_contracts:
                with self.subTest(contract=contract, guide=text[:12]):
                    self.assertIn(contract, text)

    def test_guidance_contains_no_literal_private_paths_or_placeholders(self):
        combined = CANONICAL.read_text(encoding="utf-8") + GENERATED.read_text(
            encoding="utf-8"
        )
        host_executable = (
            r"(?:cla"
            + r"ude|cod"
            + r"ex)(?:[-_.][A-Za-z0-9][A-Za-z0-9._-]*)?"
            + r"(?=$|[\s`'\"\]\[(){}.,;:])"
        )
        private_patterns = (
            r"(?<![A-Za-z0-9._-])/(?:Us" + r"ers|ho" + r"me)/",
            r"(?<![A-Za-z0-9._-])/(?:pri" + r"vate/)?var/fol" + r"ders/",
            r"(?<![A-Za-z0-9._-])/t" + r"mp/",
            r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]+Us" + r"ers[\\/]+",
            r"(?<![:\\/])(?:\\\\|//)[^\\/]+[\\/]+(?:Us"
            + r"ers|ho"
            + r"me)[\\/]+",
            r"(?<![A-Za-z0-9._:/-])/(?:[^/\\\r\n\t]+/)*" + host_executable,
            r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]+(?:[^\\/\r\n\t]+[\\/]+)*"
            + host_executable,
            r"(?<![:\\/])(?:\\\\|//)[^\\/\r\n\t]+[\\/]+(?:[^\\/\r\n\t]+[\\/]+)*"
            + host_executable,
        )
        private_path = re.compile("|".join(private_patterns), re.IGNORECASE)
        unfinished = re.compile(
            r"\b(?:T"
            + r"ODO|T"
            + r"BD|F"
            + r"IXME)\b|fill in detai"
            + r"ls|implement lat"
            + r"er",
            re.IGNORECASE,
        )

        unsafe_samples = (
            "/pri" + "vate/var/fol" + "ders/ab/cd/private-item",
            "/var/fol" + "ders/ab/cd/private-item",
            "/t" + "mp/private-item",
            "C:" + "\\" + "Us" + "ers" + "\\" + "person\\private-item",
            "\\\\server\\" + "Us" + "ers" + "\\person\\private-item",
            "/usr/loc" + "al/bin/cla" + "ude",
            "/opt/home" + "brew/bin/cod" + "ex",
            "/custom/toolchain/cla" + "ude-2.1.91",
            "/srv/tools/cod" + "ex.exe",
            "D:\\Portable\\cla" + "ude.exe",
            "\\\\build-host\\tools\\cod" + "ex-0.144.5.exe",
            "/Applications/Model Tools/cla" + "ude-2.1.91",
            "D:\\Program Files\\Codex Tools\\cod" + "ex.exe",
            "\\\\build-host\\Shared Tools\\cla" + "ude.exe",
        )
        safe_samples = (
            "docs/t" + "mp/example.md",
            "fixtures/var/fol" + "ders/example",
            "docs/tools/cla" + "ude.md",
            "https://example.test/tools/cla" + "ude",
            "http://localhost/docs/cod" + "ex",
            "<repo>",
            "<host-path>",
            "cla" + "ude",
            "cod" + "ex",
        )

        self.assertIsNone(private_path.search(combined))
        for unsafe in unsafe_samples:
            with self.subTest(unsafe=unsafe):
                self.assertIsNotNone(private_path.search(unsafe))
        for safe in safe_samples:
            with self.subTest(safe=safe):
                self.assertIsNone(private_path.search(safe))
        self.assertIsNone(unfinished.search(combined))


if __name__ == "__main__":
    unittest.main()
