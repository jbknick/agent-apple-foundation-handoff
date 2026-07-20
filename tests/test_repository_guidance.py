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
SKILLS_ROOT = Path("plugins/apple-foundation-models-handoff/skills")
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
WORKFLOW_SKILLS = (
    "design-apple-foundation-models-handoff",
    "implement-apple-foundation-models-handoff",
    "review-apple-foundation-models-handoff",
    "debug-apple-foundation-models-handoff",
    "validate-apple-foundation-models-handoff",
)
ROUTER_SKILL = "route-apple-foundation-models-handoff"
ALL_CAPABILITIES = (*WORKFLOW_SKILLS, ROUTER_SKILL)
ROUTER_FIRST_GUIDANCE_CONTRACTS = (
    "Before selecting any positive workflow, resolve non-positive pre-selection "
    "in this order: `domain = out_of_domain`, `domain = ambiguous`, then a "
    "confirmed implementation request missing an approved architecture or exact "
    "change boundary.",
    f"For any of those cases, select and load only `{ROUTER_SKILL}`, copy its "
    "exact matching branch before inspection or non-skill tool use, and select no "
    "positive workflow.",
    "Otherwise select exactly one matching positive workflow; once selected, it "
    "remains the only workflow owner for the request.",
)
GENERIC_SWIFT_ACTOR_ROUTER_RECIPE = (
    "Treat a request asking only about Swift actors, actor isolation, or a Swift "
    "example as `domain = out_of_domain` even when it asks for implementation; "
    "select only `route-apple-foundation-models-handoff` and return its "
    "`no_activation` result before positive selection."
)
CLOSED_RESPONSE_COMPILER_GUIDANCE = (
    "Treat pre-selection as one closed compilation transaction: resolve and "
    "freeze `domain`, `requestedOperation`, `artifactState`, and `evidenceState` "
    "exactly once; emit a router-owned outcome immediately before positive "
    "selection, or pass the same frozen tuple to the one selected positive "
    "workflow for unchanged serialization without re-inference."
)
DOMAIN_CLASSIFICATION_GUIDANCE = (
    "Set `domain = foundation_models_handoff` only for explicit Apple Foundation "
    "Models session, profile, or provider coordination; set `domain = ambiguous` "
    "for bare `Apple handoff` regardless of operation, artifact, failure, or "
    "evidence wording; set `domain = out_of_domain` for App Intents or Shortcuts, "
    "Apple Handoff or NSUserActivity, generic Swift or actors, generic Core ML, "
    "coding-session handoff, Agent Skills, and Foundation Models runtime Skills."
)
SYNTHETIC_DEBUG_DIVERGENCE_GUIDANCE = (
    "Before positive selection, set `domain = foundation_models_handoff` for a "
    "debug request only when it explicitly describes a synthetic handoff reducer "
    "or effect that redispatches or replays before completion or reconciliation; "
    "bare `Apple handoff` remains `domain = ambiguous`, and all adjacent "
    "exclusions remain `domain = out_of_domain`."
)
IMMUTABLE_PRESELECTION_GUIDANCE = (
    "On positive activation, `routerInput` is an immutable pre-selection record, "
    "not a workflow finding. Serialize the exact four normalized values from the "
    "source request in the shown field order; never use inspection, execution, "
    "evidence results, or drafted output to infer or revise a value. This "
    "serialization neither invokes nor emulates the router and has no branch or "
    "ownership effect."
)
PRESELECTION_GUIDANCE_CONTRACTS = (
    ROUTER_FIRST_GUIDANCE_CONTRACTS[0],
    DOMAIN_CLASSIFICATION_GUIDANCE,
    SYNTHETIC_DEBUG_DIVERGENCE_GUIDANCE,
    ROUTER_FIRST_GUIDANCE_CONTRACTS[1],
    CLOSED_RESPONSE_COMPILER_GUIDANCE,
    IMMUTABLE_PRESELECTION_GUIDANCE,
    GENERIC_SWIFT_ACTOR_ROUTER_RECIPE,
    ROUTER_FIRST_GUIDANCE_CONTRACTS[2],
)
GUIDANCE_REUSE_GUARDRAIL = (
    "Load one needed reference; never copy workflows or reference corpora or add "
    "a plugin-local worker."
)
STALE_WORKFLOW_CLAIMS = (
    "remain unimplemented",
    "must not be advertised as active",
    "DEV-136 will create",
    "future `skills/**` and `references/**`",
    "pending/future `references/**`",
    "DEV-137 integration blocker",
)
WORKFLOW_GUIDANCE_CONTRACTS = (
    "The five production workflows are implemented",
    "five workflows plus one non-positive router",
    ROUTER_SKILL,
    "`skills/**` and `references/**` are current plugin-local canonical inputs",
    "DEV-137 references are integrated and link-resolved",
    "DEV-136 host evidence is Codex-only",
    "Claude execution and cross-host comparison are `blocked/owner-deferred`",
    "Behavioral capability claims require fresh exact-model DEV-136 forward "
    "evidence",
    "Structural integration alone is not a pass",
    "Discovery, file presence, and installation are structural prerequisites and "
    "cannot prove behavioral or capability activation",
    GUIDANCE_REUSE_GUARDRAIL,
    *PRESELECTION_GUIDANCE_CONTRACTS,
)
ADAPTER_SAFETY_SEMANTIC_GROUPS = (
    (
        "exclusive Apple authority",
        (
            "Apple API claims use only current official docs, installed SDK "
            "interfaces, WWDC material, and Apple-owned repositories",
            "production references are not authority",
        ),
    ),
    (
        "no Apple tutorials or unapproved examples",
        ("add no Apple tutorials or unapproved examples",),
    ),
    (
        "exact committed evidence metadata",
        (
            "committed evidence uses normalized `<host-path>`, exact version or "
            "`null`",
            "stable diagnostic class, exit code, and status",
        ),
    ),
    (
        "persistent recovery",
        ("persistent recovery until explicit reconciliation",),
    ),
    (
        "complete reproducible capability proof",
        (
            "reproducible fresh-host activation",
            "progressive reference loading",
            "valid/invalid outcomes",
            "complete outputs",
        ),
    ),
    (
        "separate release authority",
        ("Push, merge, tag, publish, or release only when separately authorized",),
    ),
)
SKILL_OWNED_SECTION_HEADINGS = (
    "Routing and Inspection",
    "Common Workflow Protocol",
    "Output Contract",
    "References",
    "Guardrails",
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


def assert_workflow_guidance_contract(
    test_case: unittest.TestCase, text: str
) -> None:
    normalized_text = re.sub(r"\s+", " ", text)
    for skill in WORKFLOW_SKILLS:
        test_case.assertTrue(
            skill in normalized_text,
            f"missing workflow: {skill}",
        )
    test_case.assertIn(ROUTER_SKILL, normalized_text, "missing non-positive router")
    test_case.assertIn(
        "five workflows plus one non-positive router",
        normalized_text,
        "guidance must distinguish the five workflows from the router",
    )
    test_case.assertNotRegex(
        normalized_text,
        r"(?:six|6)(?:th)? (?:production )?workflows?|"
        r"route-apple-foundation-models-handoff[^.]{0,80}(?:is|as) (?:a )?workflow",
        "guidance must not call the router a workflow",
    )
    for claim in STALE_WORKFLOW_CLAIMS:
        test_case.assertFalse(
            claim in normalized_text,
            f"stale workflow guidance remains: {claim}",
        )
    for contract in WORKFLOW_GUIDANCE_CONTRACTS:
        test_case.assertTrue(
            contract in normalized_text,
            f"missing workflow guidance contract: {contract}",
        )
    positions = tuple(
        normalized_text.index(contract) for contract in PRESELECTION_GUIDANCE_CONTRACTS
    )
    test_case.assertEqual(
        tuple(sorted(positions)),
        positions,
        "router-owned branches must resolve before positive workflow selection",
    )


def assert_guidance_does_not_duplicate_skill_sections(
    test_case: unittest.TestCase, text: str
) -> None:
    for heading in SKILL_OWNED_SECTION_HEADINGS:
        test_case.assertNotRegex(
            text,
            rf"(?mi)^#{{2,6}}\s+{re.escape(heading)}\s*$",
            f"root guidance must not duplicate skill-owned section: {heading}",
        )


def assert_guidance_reuse_guardrail(
    test_case: unittest.TestCase, text: str
) -> None:
    normalized_text = re.sub(r"\s+", " ", text)
    test_case.assertIn(
        GUIDANCE_REUSE_GUARDRAIL,
        normalized_text,
        "guidance must preserve workflow, reference-corpus, and worker guardrails",
    )


def assert_adapter_safety_semantics(
    test_case: unittest.TestCase, text: str
) -> None:
    normalized_text = re.sub(r"\s+", " ", text)
    for label, clauses in ADAPTER_SAFETY_SEMANTIC_GROUPS:
        test_case.assertTrue(
            all(clause in normalized_text for clause in clauses),
            f"missing adapter safety semantic group: {label}",
        )


class RepositoryGuidanceTests(unittest.TestCase):
    def _copy_canonical_inputs(self, destination: Path) -> None:
        for relative_path in CANONICAL_INPUTS:
            target = destination / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative_path, target)
        shutil.copytree(ROOT / SKILLS_ROOT, destination / SKILLS_ROOT)

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
            self._copy_canonical_inputs(isolated_root)
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
                "CLAUDE.md: invalid canonical metadata input\n",
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
            self._copy_canonical_inputs(isolated_root)
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
                    "CLAUDE.md: invalid canonical metadata input\n",
                    change,
                )

    def test_generated_output_rejects_post_read_changes(self):
        for change in ("replacement", "in-place mutation"):
            with self.subTest(change=change):
                self._assert_post_read_change_is_rejected(
                    "AGENTS.md",
                    6,
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

    def test_guidance_distinguishes_metadata_from_planned_capabilities(self):
        for guide in (CANONICAL, GENERATED):
            text = normalized_guide(guide)

            self.assertIn(
                "Root canonical inputs are `CLAUDE.md`, "
                "`.claude-plugin/marketplace.json`, and "
                "`metadata/codex-marketplace.json`",
                text,
            )
            self.assertIn(
                "Plugin-local canonical inputs are "
                "`plugins/apple-foundation-models-handoff/.claude-plugin/plugin.json`",
                text,
            )
            self.assertIn(
                "`AGENTS.md`, `.agents/plugins/marketplace.json`, and "
                "`plugins/apple-foundation-models-handoff/.codex-plugin/plugin.json` "
                "are generated",
                text,
            )
            self.assertIn(
                "non-executable scaffold with zero capabilities",
                text,
            )
            self.assertIn(
                "Exactly five package reference files are present as "
                "documentation-only inputs and provide zero runtime capabilities",
                text,
            )
            self.assertIn(
                "Skills, hooks, commands, agents, MCP servers, package scripts, "
                "dependencies, and runtime code remain absent",
                text,
            )

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
            self.assertIn("not a sixth positive workflow", text)
            self.assertIn(
                "distinct from the DEV-142 through DEV-145 cost router, "
                "`PostToolUse` hooks, and Swift bridge chain",
                text,
            )
            self.assertIn("runtime code remain absent", text)
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

    def test_guidance_preserves_adapter_safety_semantics(self):
        for path in (CANONICAL, GENERATED):
            normalized_text = re.sub(
                r"\s+", " ", path.read_text(encoding="utf-8")
            )
            for label, clauses in ADAPTER_SAFETY_SEMANTIC_GROUPS:
                with self.subTest(path=path.name, semantic_group=label):
                    self.assertTrue(
                        all(clause in normalized_text for clause in clauses)
                    )

    def test_adapter_safety_oracle_rejects_removal_and_weakened_synonyms(self):
        valid = " ".join(
            clause
            for _, clauses in ADAPTER_SAFETY_SEMANTIC_GROUPS
            for clause in clauses
        )
        assert_adapter_safety_semantics(self, valid)

        removals = {
            f"removed {label}: {clause}": valid.replace(clause, "", 1)
            for label, clauses in ADAPTER_SAFETY_SEMANTIC_GROUPS
            for clause in clauses
        }
        weakenings = {
            "non-authoritative sources allowed": valid.replace(
                "use only current official docs",
                "may use unofficial sources alongside current docs",
                1,
            ),
            "production references treated as authority": valid.replace(
                "production references are not authority",
                "production references may establish authority",
                1,
            ),
            "Apple tutorial ban removed": valid.replace(
                "add no Apple tutorials or unapproved examples",
                "add Apple tutorials or examples when useful",
                1,
            ),
            "exact committed version weakened": valid.replace(
                "exact version or `null`",
                "approximate version when available",
                1,
            ),
            "stable committed diagnostics weakened": valid.replace(
                "stable diagnostic class, exit code, and status",
                "a diagnostic summary",
                1,
            ),
            "persistent recovery weakened": valid.replace(
                "persistent recovery until explicit reconciliation",
                "best-effort recovery",
                1,
            ),
            "fresh-host reproducibility weakened": valid.replace(
                "reproducible fresh-host activation",
                "installation on any host",
                1,
            ),
            "progressive reference loading weakened": valid.replace(
                "progressive reference loading",
                "reference availability",
                1,
            ),
            "invalid outcomes omitted": valid.replace(
                "valid/invalid outcomes",
                "valid outcomes",
                1,
            ),
            "complete outputs weakened": valid.replace(
                "complete outputs",
                "partial outputs",
                1,
            ),
            "separate release authority weakened": valid.replace(
                "only when separately authorized",
                "when locally convenient",
                1,
            ),
        }
        for mutation, candidate in {**removals, **weakenings}.items():
            with self.subTest(mutation=mutation), self.assertRaises(AssertionError):
                assert_adapter_safety_semantics(self, candidate)

    def test_guidance_defines_conditional_host_loading_and_status_lifecycle(self):
        canonical_text = normalized_guide(CANONICAL)
        generated_text = normalized_guide(GENERATED)
        required_contracts = (
            "Claude Code uses the captured approved `2.1.91` executable with "
            "session-only `--plugin-dir <repo>` or an isolated install for packaging "
            "and cache tests.",
            "Codex `0.144.5` uses the captured executable with isolated `CODEX_HOME`, "
            "marketplace registration, plugin install/add, and then a fresh task.",
            "`codex --plugin-dir` is not an approved workflow for Codex `0.144.5`.",
            "Claude Code `2.1.140` is diagnostic only and cannot substitute.",
            "DEV-135 provides metadata for structural discovery and installation.",
            "Normalize repository location as `<repo>` and executable identity as "
            "`<host-path>`; never commit their literal resolutions or raw `PATH`.",
            "Before host operations, a missing or non-runnable executable, unavailable "
            "or malformed version, or approved-baseline mismatch emits a normalized "
            "`blocked` row with stable reason/version metadata before exit.",
            "After successful capture, resolution or version drift emits normalized "
            "`fail` before exit, invalidates the row, and requires a fresh run.",
        )

        for text in (canonical_text, generated_text):
            self.assertEqual(1, text.count("resolution or version drift"))
            for contract in required_contracts:
                with self.subTest(contract=contract, guide=text[:12]):
                    self.assertIn(contract, text)

    def test_guidance_truthfully_names_implemented_workflows_and_host_evidence_boundary(
        self,
    ):
        canonical_text = CANONICAL.read_text(encoding="utf-8")
        generated_text = GENERATED.read_text(encoding="utf-8")

        for text in (canonical_text, generated_text):
            with self.subTest(guide=text[:12]):
                assert_workflow_guidance_contract(self, text)

    def test_guidance_resolves_non_positive_router_before_workflow_selection(self):
        for path in (CANONICAL, GENERATED):
            with self.subTest(path=path.name):
                assert_workflow_guidance_contract(
                    self, path.read_text(encoding="utf-8")
                )

    def test_guidance_preserves_workflow_reference_and_worker_guardrails(self):
        for path in (CANONICAL, GENERATED):
            with self.subTest(path=path.name):
                assert_guidance_reuse_guardrail(
                    self, path.read_text(encoding="utf-8")
                )

        assert_guidance_reuse_guardrail(self, GUIDANCE_REUSE_GUARDRAIL)
        mutations = {
            "missing guardrail": "",
            "workflow copy reversal": GUIDANCE_REUSE_GUARDRAIL.replace(
                "never copy workflows",
                "copy workflows",
                1,
            ),
            "reference corpus removal": GUIDANCE_REUSE_GUARDRAIL.replace(
                "reference corpora",
                "reference snippets",
                1,
            ),
            "worker addition reversal": GUIDANCE_REUSE_GUARDRAIL.replace(
                "or add a plugin-local worker",
                "and add a plugin-local worker",
                1,
            ),
        }
        for mutation, candidate in mutations.items():
            with self.subTest(mutation=mutation), self.assertRaises(AssertionError):
                assert_guidance_reuse_guardrail(self, candidate)

    def test_guidance_oracle_rejects_removed_truthfulness_contract(self):
        valid = " ".join((*WORKFLOW_SKILLS, *WORKFLOW_GUIDANCE_CONTRACTS))

        assert_workflow_guidance_contract(self, valid)
        for contract in WORKFLOW_GUIDANCE_CONTRACTS:
            mutation = valid.replace(contract, "")
            with self.subTest(contract=contract), self.assertRaises(AssertionError):
                assert_workflow_guidance_contract(self, mutation)

    def test_guidance_oracle_rejects_stale_integration_claims(self):
        valid = " ".join((*WORKFLOW_SKILLS, *WORKFLOW_GUIDANCE_CONTRACTS))

        assert_workflow_guidance_contract(self, valid)
        for claim in STALE_WORKFLOW_CLAIMS:
            with self.subTest(claim=claim), self.assertRaises(AssertionError):
                assert_workflow_guidance_contract(self, f"{valid} {claim}")

    def test_guidance_oracle_rejects_router_as_workflow(self):
        valid = " ".join((*WORKFLOW_SKILLS, *WORKFLOW_GUIDANCE_CONTRACTS))
        assert_workflow_guidance_contract(self, valid)

        for claim in (
            "six production workflows",
            f"{ROUTER_SKILL} is a workflow",
        ):
            with self.subTest(claim=claim), self.assertRaises(AssertionError):
                assert_workflow_guidance_contract(self, f"{valid} {claim}")

    def test_guidance_oracle_rejects_late_router_preselection(self):
        prefix = " ".join(
            (
                *WORKFLOW_SKILLS,
                *(
                    contract
                    for contract in WORKFLOW_GUIDANCE_CONTRACTS
                    if contract not in PRESELECTION_GUIDANCE_CONTRACTS
                ),
            )
        )
        reordered = " ".join(
            (
                prefix,
                PRESELECTION_GUIDANCE_CONTRACTS[-1],
                *PRESELECTION_GUIDANCE_CONTRACTS[:-1],
            )
        )

        with self.assertRaises(AssertionError):
            assert_workflow_guidance_contract(self, reordered)

    def test_guidance_oracle_rejects_closed_response_compiler_mutations(self):
        valid = " ".join((*WORKFLOW_SKILLS, *WORKFLOW_GUIDANCE_CONTRACTS))

        assert_workflow_guidance_contract(self, valid)
        mutations = {
            "removed compiler": valid.replace(
                CLOSED_RESPONSE_COMPILER_GUIDANCE,
                "",
                1,
            ),
            "wrong resolution cardinality": valid.replace(
                "exactly once; emit a router-owned outcome immediately",
                "again after selection; emit a router-owned outcome eventually",
                1,
            ),
            "wrong positive tuple": valid.replace(
                "same frozen tuple",
                "newly inferred tuple",
                1,
            ),
        }
        for mutation, candidate in mutations.items():
            with self.subTest(mutation=mutation), self.assertRaises(AssertionError):
                assert_workflow_guidance_contract(self, candidate)

    def test_guidance_oracle_rejects_domain_and_immutable_preselection_mutations(
        self,
    ):
        valid = " ".join((*WORKFLOW_SKILLS, *WORKFLOW_GUIDANCE_CONTRACTS))

        assert_workflow_guidance_contract(self, valid)
        mutations = {
            "missing domain recipe": valid.replace(
                DOMAIN_CLASSIFICATION_GUIDANCE,
                "",
                1,
            ),
            "wrong explicit Foundation Models domain": valid.replace(
                "Set `domain = foundation_models_handoff` only",
                "Set `domain = ambiguous` only",
                1,
            ),
            "wrong bare Apple handoff domain": valid.replace(
                "set `domain = ambiguous` for bare",
                "set `domain = foundation_models_handoff` for bare",
                1,
            ),
            "wrong adjacent-domain classification": valid.replace(
                "set `domain = out_of_domain` for App Intents",
                "set `domain = foundation_models_handoff` for App Intents",
                1,
            ),
            "missing synthetic debug divergence recipe": valid.replace(
                SYNTHETIC_DEBUG_DIVERGENCE_GUIDANCE,
                "",
                1,
            ),
            "synthetic debug divergence widened beyond explicit": valid.replace(
                "only when it explicitly describes",
                "whenever it may imply",
                1,
            ),
            "synthetic debug divergence selected after inspection": valid.replace(
                "Before positive selection",
                "After positive selection and inspection",
                1,
            ),
            "synthetic debug divergence timing generalized": valid.replace(
                "redispatches or replays before completion or reconciliation",
                "fails at any time",
                1,
            ),
            "synthetic debug divergence overrides bare ambiguity": valid.replace(
                "bare `Apple handoff` remains `domain = ambiguous`",
                "bare `Apple handoff` becomes `domain = foundation_models_handoff`",
                1,
            ),
            "synthetic debug divergence overrides adjacent exclusions": valid.replace(
                "all adjacent exclusions remain `domain = out_of_domain`",
                "adjacent exclusions become `domain = foundation_models_handoff`",
                1,
            ),
            "bare handoff precedence reversal": valid.replace(
                "regardless of operation, artifact, failure, or evidence wording",
                "unless operation, artifact, failure, or evidence wording selects "
                "a workflow",
                1,
            ),
            "omitted route skill load": valid.replace(
                "select and load only",
                "select only",
                1,
            ),
            "paraphrased router branch": valid.replace(
                "copy its exact matching branch",
                "paraphrase its matching branch",
                1,
            ),
            "positive workflow selected": valid.replace(
                "select no positive workflow",
                "select a positive workflow",
                1,
            ),
            "adjacent domain omitted": valid.replace(
                "coding-session handoff, ",
                "",
                1,
            ),
            "workflow finding reversal": valid.replace(
                "an immutable pre-selection record, not a workflow finding",
                "a mutable workflow finding, not a pre-selection record",
                1,
            ),
            "post-inspection source reversal": valid.replace(
                "the source request in the shown field order",
                "post-inspection findings in a convenient field order",
                1,
            ),
            "revision reversal": valid.replace(
                "never use inspection, execution, evidence results, or drafted "
                "output to infer or revise a value",
                "use inspection, execution, evidence results, or drafted output "
                "to infer or revise a value",
                1,
            ),
            "router emulation reversal": valid.replace(
                "neither invokes nor emulates the router",
                "invokes and emulates the router",
                1,
            ),
        }
        for mutation, candidate in mutations.items():
            with self.subTest(mutation=mutation), self.assertRaises(AssertionError):
                assert_workflow_guidance_contract(self, candidate)

    def test_guidance_does_not_duplicate_skill_owned_contract_sections(self):
        for path in (CANONICAL, GENERATED):
            with self.subTest(path=path.name):
                assert_guidance_does_not_duplicate_skill_sections(
                    self, path.read_text(encoding="utf-8")
                )

    def test_guidance_section_ownership_oracle_rejects_copy_without_remove(self):
        valid = "# Repository guidance\n"
        assert_guidance_does_not_duplicate_skill_sections(self, valid)

        for level in (3, 4):
            for heading in SKILL_OWNED_SECTION_HEADINGS:
                with (
                    self.subTest(level=level, heading=heading),
                    self.assertRaises(AssertionError),
                ):
                    assert_guidance_does_not_duplicate_skill_sections(
                        self,
                        f"{valid}\n{'#' * level} {heading}\n"
                        "Duplicated workflow content.\n",
                    )

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
