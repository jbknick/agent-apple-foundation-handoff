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


class RepositoryGuidanceTests(unittest.TestCase):
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
            shutil.copyfile(CANONICAL, isolated_root / "CLAUDE.md")

            self.assertTrue(sync_generated_artifacts.synchronize(isolated_root, write=True))
            first_bytes = (isolated_root / "AGENTS.md").read_bytes()
            self.assertTrue(sync_generated_artifacts.synchronize(isolated_root, write=True))

            self.assertEqual(first_bytes, (isolated_root / "AGENTS.md").read_bytes())

    def test_check_mode_rejects_isolated_generated_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            isolated_root = Path(directory)
            shutil.copyfile(CANONICAL, isolated_root / "CLAUDE.md")
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
                shutil.copyfile(CANONICAL, isolated_root / "CLAUDE.md")
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
            shutil.copyfile(CANONICAL, isolated_root / "CLAUDE.md")
            (isolated_root / "AGENTS.md").mkdir()

            result = run_isolated_cli(isolated_root, "--write")

            self.assertEqual(1, result.returncode)
            self.assertEqual("", result.stdout)
            self.assertEqual(
                "AGENTS.md: unsafe or unwritable generated output\n",
                result.stderr,
            )
            self.assertNotIn("CLAUDE.md: invalid canonical adapter input", result.stderr)
            self.assertTrue((isolated_root / "AGENTS.md").is_dir())

        with tempfile.TemporaryDirectory() as directory:
            isolated_root = Path(directory)
            (isolated_root / "CLAUDE.md").write_text(
                "invalid canonical guide\n", encoding="utf-8", newline="\n"
            )

            result = run_isolated_cli(isolated_root, "--write")

            self.assertEqual(1, result.returncode)
            self.assertEqual("", result.stdout)
            self.assertEqual(
                "CLAUDE.md: invalid canonical adapter input\n",
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
                    "CLAUDE.md: invalid canonical adapter input\n",
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
                    "CLAUDE.md: invalid canonical adapter input\n",
                    result.stderr,
                )
                self.assertFalse(os.path.lexists(isolated_root / "AGENTS.md"))

    def test_temporary_path_swap_is_rejected_and_cleaned(self):
        with tempfile.TemporaryDirectory() as directory:
            temporary_root = Path(directory)
            isolated_root = temporary_root / "repository"
            isolated_root.mkdir()
            shutil.copyfile(CANONICAL, isolated_root / "CLAUDE.md")
            generated = isolated_root / "AGENTS.md"
            generated.write_bytes(b"stale generated output\n")
            sentinel = temporary_root / "external-sentinel"
            original = b"external sentinel must remain unchanged\n"
            sentinel.write_bytes(original)
            real_replace = sync_generated_artifacts.os.replace

            def swap_temporary_path(source, destination):
                temporary = Path(source)
                temporary.unlink()
                temporary.symlink_to(sentinel)
                return real_replace(source, destination)

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
            shutil.copyfile(CANONICAL, isolated_root / "CLAUDE.md")
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

        self.assertLessEqual(len(generated_bytes.decode("utf-8").splitlines()), 100)
        self.assertLessEqual(len(generated_bytes), 8192)
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
            text = re.sub(r"\s+", " ", guide.read_text(encoding="utf-8"))

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
                "DEV-135 owns the planned plugin metadata inputs and generated manifest "
                "outputs",
                text,
            )
            self.assertIn(
                "remain absent until DEV-135 implements them through the shared "
                "synchronization entry point",
                text,
            )
            self.assertNotIn("Authored canonical inputs include", text)

    def test_guidance_bounds_positive_workflows_and_non_positive_routing(self):
        for guide in (CANONICAL, GENERATED):
            text = re.sub(r"\s+", " ", guide.read_text(encoding="utf-8"))

            self.assertIn(
                "five positive workflows: design, implement, review, debug, and "
                "validate",
                text,
            )
            self.assertIn(
                "may only clarify, decline, or hand off requests outside those "
                "workflows",
                text,
            )
            self.assertIn("It is not a sixth positive skill", text)
            self.assertIn(
                "distinct from the later DEV-142 through DEV-145 deterministic cost "
                "router, `PostToolUse` hook, and Swift bridge chain",
                text,
            )
            self.assertIn(
                "DEV-133 is guidance-only and implements none of that runtime chain",
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
        canonical_text = re.sub(
            r"\s+", " ", CANONICAL.read_text(encoding="utf-8")
        )
        required_contracts = (
            "`./` is conditional",
            "`./plugins/apple-foundation-models-handoff`",
            "effective cached plugin payload",
            "repository-only docs, research, fixtures, tests, and private state",
            "Claude Code `2.1.91`",
            "Codex CLI `0.144.5`",
            "Initial absence, non-executability, or version mismatch is `blocked`",
            "After successful capture, resolution or version drift emits normalized "
            "`fail` before exit",
            "strict single-line version",
            "raw `PATH`",
            "`compiled_sdk_26_5`",
            "`interface_verified_sdk_26_5`",
        )
        for contract in required_contracts:
            with self.subTest(contract=contract):
                self.assertIn(contract, canonical_text)

    def test_guidance_defines_conditional_host_loading_and_status_lifecycle(self):
        canonical_text = CANONICAL.read_text(encoding="utf-8")
        generated_text = GENERATED.read_text(encoding="utf-8")
        required_contracts = (
            "Claude Code uses the captured approved `2.1.91` executable with "
            "session-only `--plugin-dir <repo>` or an isolated install for packaging "
            "and cache tests.",
            "Codex `0.144.5` uses the captured executable with isolated `CODEX_HOME`, "
            "marketplace registration, plugin install/add, and then a fresh task.",
            "`codex --plugin-dir` is not an approved workflow for Codex `0.144.5`.",
            "Claude Code `2.1.140` is diagnostic only and cannot substitute.",
            "DEV-135 owns the planned plugin metadata inputs and generated manifest "
            "outputs. They remain absent until DEV-135 implements them through the "
            "shared synchronization entry point.",
            "Host loading flows remain planned and conditional; they claim no "
            "discovery, installation, activation, reference, or capability success.",
            "Normalize repository location as `<repo>` and executable identity as "
            "`<host-path>`; never commit their literal resolutions or raw `PATH`.",
            "Before host operations, a missing or non-runnable executable, unavailable "
            "or malformed version, or approved-baseline mismatch emits a normalized "
            "`blocked` row with stable reason/version metadata before exit.",
            "After successful capture, resolution or version drift emits normalized "
            "`fail` before exit, invalidates the row, and requires a fresh run.",
        )

        for text in (canonical_text, generated_text):
            normalized_text = re.sub(r"\s+", " ", text)
            self.assertEqual(1, normalized_text.count("resolution or version drift"))
            for contract in required_contracts:
                with self.subTest(contract=contract, guide=text[:12]):
                    self.assertIn(contract, normalized_text)

    def test_guidance_preserves_safe_synthetic_and_redacted_evidence_exception(self):
        canonical_text = CANONICAL.read_text(encoding="utf-8")
        generated_text = GENERATED.read_text(encoding="utf-8")
        required_contracts = (
            "Raw/live prompts, responses, reasoning, tool arguments/results, "
            "credentials, private configuration, real user/third-party data, raw "
            "diagnostics, `.trace`, and `.xcresult` remain excluded.",
            "A hash-bound synthetic or approved-redacted rubric stimulus, rubric "
            "assessments with only bounded rationales, and a redacted summary may be "
            "committed only after the DEV-131 path, content, structured-key, "
            "classification, and hash scanners pass.",
            "Runtime/live-host logs, traces, and derived capability telemetry "
            "contribute normalized metadata only.",
        )

        for text in (canonical_text, generated_text):
            normalized_text = re.sub(r"\s+", " ", text)
            for contract in required_contracts:
                with self.subTest(contract=contract, guide=text[:12]):
                    self.assertIn(contract, normalized_text)

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
