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
        canonical_text = CANONICAL.read_text(encoding="utf-8")
        required_contracts = (
            "`./` is conditional",
            "`./plugins/apple-foundation-models-handoff`",
            "effective cached plugin payload",
            "repository-only docs, research, fixtures, tests, and private state",
            "Claude Code `2.1.91`",
            "Codex CLI `0.144.5`",
            "Initial absence, non-executability, or version mismatch is `blocked`",
            "Post-capture resolution or version drift is `fail`",
            "strict single-line version",
            "raw `PATH`",
            "`compiled_sdk_26_5`",
            "`interface_verified_sdk_26_5`",
        )
        for contract in required_contracts:
            with self.subTest(contract=contract):
                self.assertIn(contract, canonical_text)

    def test_guidance_contains_no_literal_private_paths_or_placeholders(self):
        combined = CANONICAL.read_text(encoding="utf-8") + GENERATED.read_text(
            encoding="utf-8"
        )
        private_path = re.compile(r"/(?:Us" + r"ers|ho" + r"me)/")
        unfinished = re.compile(
            r"\b(?:T"
            + r"ODO|T"
            + r"BD|F"
            + r"IXME)\b|fill in detai"
            + r"ls|implement lat"
            + r"er",
            re.IGNORECASE,
        )

        self.assertIsNone(private_path.search(combined))
        self.assertIsNone(unfinished.search(combined))


if __name__ == "__main__":
    unittest.main()
