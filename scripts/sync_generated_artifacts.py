#!/usr/bin/env python3
"""Generate or check provider adapters derived from canonical repository data."""

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import secrets
import stat
import sys
from typing import Mapping, Sequence


BEGIN = "<!-- BEGIN GENERATED AGENTS ADAPTER -->"
END = "<!-- END GENERATED AGENTS ADAPTER -->"
GENERATED_HEADER = (
    "# AGENTS.md\n\n"
    "<!-- Generated from CLAUDE.md by scripts/sync_generated_artifacts.py. "
    "Do not edit directly. -->\n\n"
)
CANONICAL_DIAGNOSTIC = "invalid canonical metadata input"
DRIFT_DIAGNOSTIC = "generated content is out of date"
OUTPUT_DIAGNOSTIC = "unsafe or unwritable generated output"
UNEXPECTED_DIAGNOSTIC = "generated artifacts: unexpected generated path"
PLUGIN_ID = "apple-foundation-models-handoff"
PLUGIN_ROOT = Path("plugins") / PLUGIN_ID
SKILLS_COMPONENT = PLUGIN_ROOT / "skills"
CLAUDE_MARKETPLACE = Path(".claude-plugin/marketplace.json")
CODEX_MARKETPLACE_INPUT = Path("metadata/codex-marketplace.json")
SHARED_MANIFEST = PLUGIN_ROOT / ".claude-plugin/plugin.json"
CODEX_INTERFACE_INPUT = PLUGIN_ROOT / "metadata/codex-interface.json"
CODEX_MANIFEST = PLUGIN_ROOT / ".codex-plugin/plugin.json"
CODEX_MARKETPLACE = Path(".agents/plugins/marketplace.json")
GENERATED_PATHS = (Path("AGENTS.md"), CODEX_MARKETPLACE, CODEX_MANIFEST)
EXPECTED_SOURCE = "./plugins/apple-foundation-models-handoff"
EXPECTED_VERSION = "0.1.0"
WORKFLOW_SKILLS = (
    "design-apple-foundation-models-handoff",
    "implement-apple-foundation-models-handoff",
    "review-apple-foundation-models-handoff",
    "debug-apple-foundation-models-handoff",
    "validate-apple-foundation-models-handoff",
)
ROUTER_SKILL = "route-apple-foundation-models-handoff"
ALL_CAPABILITIES = (*WORKFLOW_SKILLS, ROUTER_SKILL)
EXPECTED_SKILL_DESCRIPTIONS = {
    "design-apple-foundation-models-handoff": (
        "Design an Apple Foundation Models handoff architecture, topology, pattern, "
        "state model, or trust boundary when the user is creating or materially "
        "revising how sessions, profiles, or providers transfer control or provide "
        "isolated consultation."
    ),
    "implement-apple-foundation-models-handoff": (
        "Implement an Apple Foundation Models handoff architecture when an approved "
        "architecture or decision reference and an exact application change boundary "
        "already exist."
    ),
    "review-apple-foundation-models-handoff": (
        "Review an existing Apple Foundation Models handoff artifact when the user "
        "wants severity-ranked findings about architecture, Apple API grounding, "
        "state, security, recovery, or evidence claims rather than changes."
    ),
    "debug-apple-foundation-models-handoff": (
        "Debug an Apple Foundation Models handoff when an observed routing, ownership, "
        "transition, context, tool, effect, recovery, fallback, availability, or "
        "version-labelled behavior differs from its expected contract and the cause "
        "is not yet established."
    ),
    "validate-apple-foundation-models-handoff": (
        "Validate an Apple Foundation Models handoff artifact when the user requests "
        "reproducible proof, a complete pass/fail/blocked/not_applicable matrix, "
        "cross-host comparison, or release implication rather than design, edits, "
        "findings-only review, or diagnosis."
    ),
    ROUTER_SKILL: (
        "Route a non-positive Apple Foundation Models handoff request before workflow "
        "selection: reject App Intents or Shortcuts, Apple Handoff or NSUserActivity, "
        "generic Swift or actors, generic Core ML, coding-session handoff, Agent "
        "Skills, and Foundation Models runtime Skills; ask one clarification for "
        "ambiguous Apple handoff wording or implementation without an approved "
        "architecture and exact change boundary. Return only no_activation or "
        "clarification_required; never use for a confirmed request that can select "
        "design, implement, review, debug, or validate."
    ),
}
ROOT_AGENTS_TEMP_PREFIX = ".AGENTS.md."
ROOT_AGENTS_TEMP_SUFFIX = ".tmp"
ROOT_AGENTS_TEMP_TOKEN_LENGTH = 32
LOWERCASE_HEX = frozenset("0123456789abcdef")


@dataclass(frozen=True)
class CanonicalInputs:
    guidance: str
    claude_marketplace: Mapping[str, object]
    codex_marketplace: Mapping[str, object]
    shared_manifest: Mapping[str, object]
    codex_interface: Mapping[str, object]


class CanonicalInputError(Exception):
    """Canonical guidance cannot be read or rendered safely."""


class GeneratedOutputError(Exception):
    """Generated output cannot be inspected or replaced safely."""

    def __init__(self, relative_path: Path | None = None) -> None:
        super().__init__(relative_path.as_posix() if relative_path is not None else "")
        self.relative_path = relative_path


class UnexpectedGeneratedPath(Exception):
    """A reserved generated namespace contains an unowned path."""


@dataclass
class _PreparedGeneratedOutput:
    """A verified temporary output awaiting ordered atomic replacement."""

    parent_fd: int
    name: str
    temporary: str
    descriptor: int | None
    temporary_exists: bool = True


def _adapter_body(canonical_text: str) -> str:
    if canonical_text.count(BEGIN) != 1 or canonical_text.count(END) != 1:
        raise ValueError("canonical guide must contain exactly one adapter section")

    begin_index = canonical_text.index(BEGIN) + len(BEGIN)
    end_index = canonical_text.index(END)
    if begin_index >= end_index:
        raise ValueError("canonical adapter delimiters are reversed")

    body = canonical_text[begin_index:end_index].strip("\n")
    if not body.strip():
        raise ValueError("canonical adapter section is empty")
    return body


def render_agents(canonical_text: str) -> str:
    """Render the root Codex adapter from canonical repository guidance."""

    canonical_text = canonical_text.replace("\r\n", "\n").replace("\r", "\n")
    return GENERATED_HEADER + _adapter_body(canonical_text) + "\n"


def _same_file(left: os.stat_result, right: os.stat_result) -> bool:
    return (left.st_dev, left.st_ino) == (right.st_dev, right.st_ino)


def _same_snapshot(left: os.stat_result, right: os.stat_result) -> bool:
    return _same_file(left, right) and (
        left.st_mode,
        left.st_size,
        left.st_mtime_ns,
        left.st_ctime_ns,
    ) == (
        right.st_mode,
        right.st_size,
        right.st_mtime_ns,
        right.st_ctime_ns,
    )


def _unchanged_after_read(
    opened: os.stat_result, after_read: os.stat_result, current: os.stat_result
) -> bool:
    return (
        stat.S_ISREG(after_read.st_mode)
        and stat.S_ISREG(current.st_mode)
        and _same_snapshot(opened, after_read)
        and _same_snapshot(after_read, current)
    )


def _read_canonical(canonical: Path) -> bytes:
    descriptor: int | None = None
    try:
        metadata = canonical.lstat()
        if not stat.S_ISREG(metadata.st_mode):
            raise CanonicalInputError
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(canonical, flags)
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or not _same_file(metadata, opened):
            raise CanonicalInputError
        with os.fdopen(descriptor, "rb") as stream:
            descriptor = None
            content = stream.read()
            after_read = os.fstat(stream.fileno())
            current = canonical.lstat()
            if not _unchanged_after_read(opened, after_read, current):
                raise CanonicalInputError
            return content
    except CanonicalInputError:
        raise
    except OSError as error:
        raise CanonicalInputError from error
    finally:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError as error:
                raise CanonicalInputError from error


def _pairs_without_duplicates(
    pairs: list[tuple[str, object]],
) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON key")
        value[key] = item
    return value


def _json_input(root: Path, relative_path: Path) -> Mapping[str, object]:
    try:
        encoded = _read_canonical(root / relative_path)
        value = json.loads(
            encoded.decode("utf-8"), object_pairs_hook=_pairs_without_duplicates
        )
        if not isinstance(value, dict):
            raise ValueError("JSON input must be an object")
        return value
    except (CanonicalInputError, TypeError, UnicodeError, ValueError) as error:
        raise CanonicalInputError(relative_path.as_posix()) from error


def _closed_object(
    value: object,
    required: set[str],
    allowed: set[str],
) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise ValueError("object")
    keys = set(value)
    if not required.issubset(keys) or not keys.issubset(allowed):
        raise ValueError("closed object")
    return value


def _string(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("non-empty string")
    return value


def _https(value: object) -> str:
    url = _string(value)
    if not url.startswith("https://"):
        raise ValueError("HTTPS URL")
    return url


def _validate_shared_manifest(value: object) -> None:
    fields = {
        "name",
        "version",
        "description",
        "author",
        "homepage",
        "repository",
        "license",
        "keywords",
        "skills",
    }
    value = _closed_object(value, fields, fields)
    if value["name"] != PLUGIN_ID:
        raise ValueError("plugin identity")
    if value["version"] != EXPECTED_VERSION:
        raise ValueError("plugin version")
    _string(value["description"])
    author = _closed_object(value["author"], {"name", "url"}, {"name", "url"})
    _string(author["name"])
    _https(author["url"])
    _https(value["homepage"])
    _https(value["repository"])
    _string(value["license"])
    keywords = value["keywords"]
    if not isinstance(keywords, list) or not keywords:
        raise ValueError("keywords")
    if len(set(keywords)) != len(keywords):
        raise ValueError("duplicate keywords")
    for keyword in keywords:
        _string(keyword)
    if value["skills"] != "./skills/":
        raise ValueError("skills component")


def _validate_codex_interface(value: object) -> None:
    fields = {
        "displayName",
        "shortDescription",
        "longDescription",
        "developerName",
        "category",
        "capabilities",
        "websiteURL",
        "defaultPrompt",
    }
    value = _closed_object(value, fields, fields)
    for field in (
        "displayName",
        "shortDescription",
        "longDescription",
        "developerName",
    ):
        _string(value[field])
    if value["category"] != "Developer Tools":
        raise ValueError("interface category")
    capabilities = value["capabilities"]
    if capabilities != list(ALL_CAPABILITIES):
        raise ValueError("capabilities")
    if tuple(capabilities[:-1]) != WORKFLOW_SKILLS or capabilities[-1] != ROUTER_SKILL:
        raise ValueError("capability topology")
    prompts = value["defaultPrompt"]
    if not isinstance(prompts, list) or not 1 <= len(prompts) <= 3:
        raise ValueError("prompt count")
    for prompt in prompts:
        if len(_string(prompt)) > 128:
            raise ValueError("prompt length")
    _https(value["websiteURL"])


def _open_bound_directory_at(
    parent_fd: int,
    name: str,
) -> tuple[int, os.stat_result]:
    metadata = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    if not stat.S_ISDIR(metadata.st_mode):
        raise ValueError("directory")
    descriptor: int | None = None
    try:
        descriptor = os.open(name, _directory_flags(), dir_fd=parent_fd)
        opened = os.fstat(descriptor)
        if not stat.S_ISDIR(opened.st_mode) or not _same_file(metadata, opened):
            raise ValueError("directory identity")
        result = descriptor
        descriptor = None
        return result, opened
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _recheck_bound_directory_at(
    parent_fd: int,
    name: str,
    descriptor: int,
    opened: os.stat_result,
) -> None:
    current = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    held = os.fstat(descriptor)
    if (
        not stat.S_ISDIR(current.st_mode)
        or not stat.S_ISDIR(held.st_mode)
        or not _same_file(current, opened)
        or not _same_file(held, opened)
    ):
        raise ValueError("directory identity")


def _read_bound_regular_file(parent_fd: int, name: str) -> str:
    metadata = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    if not stat.S_ISREG(metadata.st_mode):
        raise ValueError("regular file")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor: int | None = None
    try:
        descriptor = os.open(name, flags, dir_fd=parent_fd)
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or not _same_file(metadata, opened):
            raise ValueError("file identity")
        with os.fdopen(os.dup(descriptor), "rb") as stream:
            encoded = stream.read()
        current = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        held = os.fstat(descriptor)
        if (
            not stat.S_ISREG(current.st_mode)
            or not stat.S_ISREG(held.st_mode)
            or not _same_file(current, opened)
            or not _same_file(held, opened)
        ):
            raise ValueError("file identity")
        return encoded.decode("utf-8")
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _validate_skill_frontmatter(skill_text: str, capability: str) -> None:
    lines = skill_text.splitlines()
    if not lines or lines[0] != "---":
        raise ValueError("frontmatter opening delimiter")
    try:
        closing = lines.index("---", 1)
    except ValueError as error:
        raise ValueError("frontmatter closing delimiter") from error
    if closing != 3 or closing + 1 >= len(lines):
        raise ValueError("frontmatter boundary")

    fields: list[tuple[str, str]] = []
    for line in lines[1:closing]:
        key, separator, value = line.partition(": ")
        if not separator or not key or not value or value != value.strip():
            raise ValueError("frontmatter field")
        fields.append((key, value))
    if [key for key, _ in fields] != ["name", "description"]:
        raise ValueError("frontmatter fields")
    if fields[0][1] != capability:
        raise ValueError("skill identity")
    expected_description = EXPECTED_SKILL_DESCRIPTIONS[capability]
    if capability == ROUTER_SKILL:
        expected_description = f"'{expected_description}'"
    if fields[1][1] != expected_description:
        raise ValueError("skill description")


def _validate_skill_component(
    root: object,
    shared_manifest: Mapping[str, object],
    codex_interface: Mapping[str, object],
) -> None:
    if not isinstance(root, Path):
        raise ValueError("repository root")
    if shared_manifest["skills"] != "./skills/":
        raise ValueError("skills component")
    capabilities = codex_interface["capabilities"]
    if capabilities != list(ALL_CAPABILITIES):
        raise ValueError("capabilities")
    if tuple(capabilities[:-1]) != WORKFLOW_SKILLS or capabilities[-1] != ROUTER_SKILL:
        raise ValueError("capability topology")

    descriptors: list[int] = []
    try:
        root_metadata = root.lstat()
        if not stat.S_ISDIR(root_metadata.st_mode):
            raise ValueError("repository root")
        root_fd = os.open(root, _directory_flags())
        descriptors.append(root_fd)
        opened_root = os.fstat(root_fd)
        if not stat.S_ISDIR(opened_root.st_mode) or not _same_file(
            root_metadata, opened_root
        ):
            raise ValueError("repository root identity")

        plugins_fd, opened_plugins = _open_bound_directory_at(root_fd, "plugins")
        descriptors.append(plugins_fd)
        plugin_fd, opened_plugin = _open_bound_directory_at(plugins_fd, PLUGIN_ID)
        descriptors.append(plugin_fd)
        skills_fd, opened_skills = _open_bound_directory_at(plugin_fd, "skills")
        descriptors.append(skills_fd)

        with os.scandir(skills_fd) as entries:
            discovered = {entry.name for entry in entries}
        if discovered != set(ALL_CAPABILITIES):
            raise ValueError("skill directories")

        for capability in ALL_CAPABILITIES:
            skill_fd, opened_skill = _open_bound_directory_at(
                skills_fd, capability
            )
            descriptors.append(skill_fd)
            try:
                with os.scandir(skill_fd) as children:
                    child_names = {child.name for child in children}
                if child_names != {"SKILL.md"}:
                    raise ValueError("skill contents")
                skill_text = _read_bound_regular_file(skill_fd, "SKILL.md")
                _validate_skill_frontmatter(skill_text, capability)
                _recheck_bound_directory_at(
                    skills_fd,
                    capability,
                    skill_fd,
                    opened_skill,
                )
            finally:
                descriptors.pop()
                os.close(skill_fd)

        _recheck_bound_directory_at(
            plugin_fd,
            "skills",
            skills_fd,
            opened_skills,
        )
        _recheck_bound_directory_at(
            plugins_fd,
            PLUGIN_ID,
            plugin_fd,
            opened_plugin,
        )
        _recheck_bound_directory_at(
            root_fd,
            "plugins",
            plugins_fd,
            opened_plugins,
        )
        current_root = root.lstat()
        held_root = os.fstat(root_fd)
        if (
            not stat.S_ISDIR(current_root.st_mode)
            or not stat.S_ISDIR(held_root.st_mode)
            or not _same_file(current_root, opened_root)
            or not _same_file(held_root, opened_root)
        ):
            raise ValueError("repository root identity")
    except (OSError, UnicodeError, ValueError) as error:
        raise ValueError("skills component") from error
    finally:
        cleanup_error: OSError | None = None
        for descriptor in reversed(descriptors):
            try:
                os.close(descriptor)
            except OSError as error:
                cleanup_error = cleanup_error or error
        if cleanup_error is not None:
            raise ValueError("skills component cleanup") from cleanup_error


def _validate_claude_marketplace(
    value: object, shared_manifest: Mapping[str, object]
) -> None:
    fields = {"name", "owner", "plugins"}
    value = _closed_object(value, fields, fields)
    if value["name"] != "agent-apple-foundation-handoff":
        raise ValueError("Claude marketplace identity")
    owner = _closed_object(value["owner"], {"name"}, {"name"})
    if owner["name"] != "Joseph Knickerbocker":
        raise ValueError("Claude marketplace owner")
    plugins = value["plugins"]
    if not isinstance(plugins, list) or len(plugins) != 1:
        raise ValueError("Claude marketplace plugins")
    plugin_fields = {"name", "source", "description", "version"}
    plugin = _closed_object(plugins[0], plugin_fields, plugin_fields)
    if plugin["name"] != shared_manifest["name"]:
        raise ValueError("Claude plugin identity")
    if plugin["description"] != shared_manifest["description"]:
        raise ValueError("Claude plugin description")
    if plugin["version"] != shared_manifest["version"]:
        raise ValueError("Claude plugin version")
    if plugin["source"] != EXPECTED_SOURCE:
        raise ValueError("Claude plugin source")


def _validate_codex_marketplace(
    value: object, shared_manifest: Mapping[str, object]
) -> None:
    fields = {"name", "interface", "plugins"}
    value = _closed_object(value, fields, fields)
    if value["name"] != "agent-apple-foundation-handoff":
        raise ValueError("Codex marketplace identity")
    interface = _closed_object(value["interface"], {"displayName"}, {"displayName"})
    if interface["displayName"] != "Agent Apple Foundation Handoff":
        raise ValueError("Codex marketplace display identity")
    plugins = value["plugins"]
    if not isinstance(plugins, list) or len(plugins) != 1:
        raise ValueError("Codex marketplace plugins")
    plugin_fields = {"name", "source", "policy", "category"}
    plugin = _closed_object(plugins[0], plugin_fields, plugin_fields)
    if plugin["name"] != shared_manifest["name"]:
        raise ValueError("Codex plugin identity")
    source = _closed_object(plugin["source"], {"source", "path"}, {"source", "path"})
    if source["source"] != "local" or source["path"] != EXPECTED_SOURCE:
        raise ValueError("Codex plugin source")
    policy_fields = {"installation", "authentication"}
    policy = _closed_object(plugin["policy"], policy_fields, policy_fields)
    if policy["installation"] != "AVAILABLE":
        raise ValueError("Codex installation policy")
    if policy["authentication"] != "ON_INSTALL":
        raise ValueError("Codex authentication policy")
    if plugin["category"] != "Developer Tools":
        raise ValueError("Codex marketplace category")


def _validate_input(
    relative_path: Path,
    validator,
    value: object,
    *extra: object,
) -> None:
    try:
        validator(value, *extra)
    except (TypeError, ValueError) as error:
        raise CanonicalInputError(relative_path.as_posix()) from error


def load_canonical_inputs(root: Path) -> CanonicalInputs:
    guidance_path = Path("CLAUDE.md")
    try:
        guidance = _read_canonical(root / guidance_path).decode("utf-8")
    except (CanonicalInputError, UnicodeError) as error:
        raise CanonicalInputError(guidance_path.as_posix()) from error

    shared = _json_input(root, SHARED_MANIFEST)
    claude_marketplace = _json_input(root, CLAUDE_MARKETPLACE)
    codex_interface = _json_input(root, CODEX_INTERFACE_INPUT)
    codex_marketplace = _json_input(root, CODEX_MARKETPLACE_INPUT)
    _validate_input(guidance_path, _adapter_body, guidance)
    _validate_input(SHARED_MANIFEST, _validate_shared_manifest, shared)
    _validate_input(
        CLAUDE_MARKETPLACE,
        _validate_claude_marketplace,
        claude_marketplace,
        shared,
    )
    _validate_input(CODEX_INTERFACE_INPUT, _validate_codex_interface, codex_interface)
    _validate_input(
        SKILLS_COMPONENT,
        _validate_skill_component,
        root,
        shared,
        codex_interface,
    )
    _validate_input(
        CODEX_MARKETPLACE_INPUT,
        _validate_codex_marketplace,
        codex_marketplace,
        shared,
    )
    return CanonicalInputs(
        guidance, claude_marketplace, codex_marketplace, shared, codex_interface
    )


def _json_bytes(value: Mapping[str, object]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def render_codex_manifest(inputs: CanonicalInputs) -> bytes:
    """Render the Codex plugin manifest from validated canonical inputs."""

    shared = inputs.shared_manifest
    author = shared["author"]
    interface = inputs.codex_interface
    return _json_bytes(
        {
            "name": shared["name"],
            "version": shared["version"],
            "description": shared["description"],
            "author": {
                "name": author["name"],
                "url": author["url"],
            },
            "homepage": shared["homepage"],
            "repository": shared["repository"],
            "license": shared["license"],
            "keywords": list(shared["keywords"]),
            "skills": shared["skills"],
            "interface": {
                "displayName": interface["displayName"],
                "shortDescription": interface["shortDescription"],
                "longDescription": interface["longDescription"],
                "developerName": interface["developerName"],
                "category": interface["category"],
                "capabilities": list(interface["capabilities"]),
                "websiteURL": interface["websiteURL"],
                "defaultPrompt": list(interface["defaultPrompt"]),
            },
        }
    )


def render_codex_marketplace(inputs: CanonicalInputs) -> bytes:
    """Render the Codex marketplace from validated canonical inputs."""

    marketplace = inputs.codex_marketplace
    interface = marketplace["interface"]
    plugin = marketplace["plugins"][0]
    source = plugin["source"]
    policy = plugin["policy"]
    return _json_bytes(
        {
            "name": marketplace["name"],
            "interface": {"displayName": interface["displayName"]},
            "plugins": [
                {
                    "name": inputs.shared_manifest["name"],
                    "source": {
                        "source": source["source"],
                        "path": source["path"],
                    },
                    "policy": {
                        "installation": policy["installation"],
                        "authentication": policy["authentication"],
                    },
                    "category": plugin["category"],
                }
            ],
        }
    )


def _rendered_json(encoded: bytes, relative_path: Path) -> Mapping[str, object]:
    """Parse one rendered JSON output without exposing parser details."""

    try:
        if not isinstance(encoded, bytes):
            raise TypeError("rendered JSON must be bytes")
        value = json.loads(
            encoded.decode("utf-8"), object_pairs_hook=_pairs_without_duplicates
        )
        if not isinstance(value, dict):
            raise ValueError("rendered JSON must be an object")
        return value
    except (TypeError, UnicodeError, ValueError) as error:
        raise GeneratedOutputError(relative_path) from error


def _validate_rendered_codex_manifest(
    encoded: bytes, inputs: CanonicalInputs
) -> None:
    """Validate the generated manifest's closed shape and canonical ownership."""

    rendered = _rendered_json(encoded, CODEX_MANIFEST)
    shared_fields = set(inputs.shared_manifest)
    fields = shared_fields | {"interface"}
    try:
        rendered = _closed_object(rendered, fields, fields)
        shared = {field: rendered[field] for field in inputs.shared_manifest}
        _validate_shared_manifest(shared)
        _validate_codex_interface(rendered["interface"])
        if shared != inputs.shared_manifest:
            raise ValueError("generated shared identity ownership")
        if rendered["interface"] != inputs.codex_interface:
            raise ValueError("generated interface ownership")
    except (TypeError, ValueError) as error:
        raise GeneratedOutputError(CODEX_MANIFEST) from error


def _validate_rendered_codex_marketplace(
    encoded: bytes, inputs: CanonicalInputs
) -> None:
    """Validate the generated marketplace's contract and canonical parity."""

    rendered = _rendered_json(encoded, CODEX_MARKETPLACE)
    try:
        _validate_codex_marketplace(rendered, inputs.shared_manifest)
        if rendered != inputs.codex_marketplace:
            raise ValueError("generated marketplace ownership")
    except (TypeError, ValueError) as error:
        raise GeneratedOutputError(CODEX_MARKETPLACE) from error


def expected_artifacts(root: Path) -> dict[Path, bytes]:
    """Render every generated artifact without writing it."""

    inputs = load_canonical_inputs(root)
    agents = render_agents(inputs.guidance).encode("utf-8")
    marketplace = render_codex_marketplace(inputs)
    manifest = render_codex_manifest(inputs)
    _validate_rendered_codex_marketplace(marketplace, inputs)
    _validate_rendered_codex_manifest(manifest, inputs)
    return {
        Path("AGENTS.md"): agents,
        CODEX_MARKETPLACE: marketplace,
        CODEX_MANIFEST: manifest,
    }


def _directory_flags() -> int:
    return (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )


def _open_directory_chain(root: Path, relative: Path, create: bool) -> int | None:
    """Open a repository-relative directory without following path components."""

    descriptor: int | None = None
    try:
        descriptor = os.open(root, _directory_flags())
        for component in relative.parts:
            if component in ("", "."):
                continue
            try:
                child = os.open(component, _directory_flags(), dir_fd=descriptor)
            except FileNotFoundError:
                if not create:
                    return None
                os.mkdir(component, mode=0o755, dir_fd=descriptor)
                child = os.open(component, _directory_flags(), dir_fd=descriptor)
            previous = descriptor
            descriptor = child
            os.close(previous)
        result = descriptor
        descriptor = None
        return result
    except OSError as error:
        raise GeneratedOutputError from error
    finally:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass


def _regular_output_at(parent_fd: int, name: str) -> os.stat_result | None:
    try:
        metadata = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        return None
    except OSError as error:
        raise GeneratedOutputError from error
    if not stat.S_ISREG(metadata.st_mode):
        raise GeneratedOutputError
    return metadata


def _read_generated_at(parent_fd: int, name: str) -> bytes | None:
    metadata = _regular_output_at(parent_fd, name)
    if metadata is None:
        return None

    descriptor: int | None = None
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(name, flags, dir_fd=parent_fd)
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or not _same_file(metadata, opened):
            raise GeneratedOutputError
        with os.fdopen(descriptor, "rb") as stream:
            descriptor = None
            content = stream.read()
            after_read = os.fstat(stream.fileno())
            current = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
            if not _unchanged_after_read(opened, after_read, current):
                raise GeneratedOutputError
            return content
    except OSError as error:
        raise GeneratedOutputError from error
    finally:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError as error:
                raise GeneratedOutputError from error


def _remove_unsafe_output_at(parent_fd: int, name: str) -> None:
    try:
        metadata = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        return
    except OSError as error:
        raise GeneratedOutputError from error
    if stat.S_ISDIR(metadata.st_mode):
        raise GeneratedOutputError
    try:
        os.unlink(name, dir_fd=parent_fd)
    except FileNotFoundError:
        return
    except OSError as error:
        raise GeneratedOutputError from error


def _cleanup_prepared_output(prepared: _PreparedGeneratedOutput) -> None:
    cleanup_error: OSError | None = None
    if prepared.descriptor is not None:
        try:
            os.close(prepared.descriptor)
        except OSError as error:
            cleanup_error = error
        prepared.descriptor = None
    if prepared.temporary_exists:
        try:
            os.unlink(prepared.temporary, dir_fd=prepared.parent_fd)
        except FileNotFoundError:
            pass
        except OSError as error:
            cleanup_error = cleanup_error or error
        else:
            prepared.temporary_exists = False
    if cleanup_error is not None:
        raise GeneratedOutputError from cleanup_error


def _prepare_generated_at(
    parent_fd: int, name: str, expected: bytes
) -> _PreparedGeneratedOutput:
    """Create and inode-verify one staged output without replacing its target."""

    _regular_output_at(parent_fd, name)
    temporary = f".{name}.{secrets.token_hex(16)}.tmp"
    prepared: _PreparedGeneratedOutput | None = None
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_BINARY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        descriptor = os.open(temporary, flags, 0o644, dir_fd=parent_fd)
        prepared = _PreparedGeneratedOutput(
            parent_fd=parent_fd,
            name=name,
            temporary=temporary,
            descriptor=descriptor,
        )
        if hasattr(os, "fchmod"):
            os.fchmod(descriptor, 0o644)
        with os.fdopen(os.dup(descriptor), "wb") as stream:
            stream.write(expected)
            stream.flush()
            os.fsync(stream.fileno())

        intended_metadata = os.fstat(descriptor)
        temporary_metadata = os.stat(
            temporary, dir_fd=parent_fd, follow_symlinks=False
        )
        if not stat.S_ISREG(temporary_metadata.st_mode) or not _same_file(
            intended_metadata, temporary_metadata
        ):
            raise GeneratedOutputError
        return prepared
    except (GeneratedOutputError, OSError) as error:
        if prepared is not None:
            try:
                _cleanup_prepared_output(prepared)
            except GeneratedOutputError as cleanup_error:
                raise cleanup_error from error
        if isinstance(error, GeneratedOutputError):
            raise
        raise GeneratedOutputError from error


def _commit_prepared_output(prepared: _PreparedGeneratedOutput) -> None:
    """Atomically replace one target from an already verified staged output."""

    if prepared.descriptor is None or not prepared.temporary_exists:
        raise GeneratedOutputError
    try:
        intended_metadata = os.fstat(prepared.descriptor)
        temporary_metadata = os.stat(
            prepared.temporary,
            dir_fd=prepared.parent_fd,
            follow_symlinks=False,
        )
        if not stat.S_ISREG(temporary_metadata.st_mode) or not _same_file(
            intended_metadata, temporary_metadata
        ):
            raise GeneratedOutputError

        _regular_output_at(prepared.parent_fd, prepared.name)
        os.replace(
            prepared.temporary,
            prepared.name,
            src_dir_fd=prepared.parent_fd,
            dst_dir_fd=prepared.parent_fd,
        )
        prepared.temporary_exists = False
        try:
            generated_metadata = os.stat(
                prepared.name,
                dir_fd=prepared.parent_fd,
                follow_symlinks=False,
            )
            if not stat.S_ISREG(generated_metadata.st_mode) or not _same_file(
                intended_metadata, generated_metadata
            ):
                raise GeneratedOutputError
        except (GeneratedOutputError, OSError) as error:
            _remove_unsafe_output_at(prepared.parent_fd, prepared.name)
            raise GeneratedOutputError from error
    except GeneratedOutputError:
        raise
    except OSError as error:
        raise GeneratedOutputError from error


def _scan_directory(
    parent_fd: int,
    relative: Path,
    allowed: set[Path],
) -> None:
    try:
        with os.scandir(parent_fd) as entries:
            for entry in entries:
                candidate = relative / entry.name
                if candidate not in allowed:
                    raise UnexpectedGeneratedPath
    except UnexpectedGeneratedPath:
        raise
    except OSError as error:
        raise GeneratedOutputError from error


def _scan_generated_namespaces(root: Path) -> None:
    root_descriptor: int | None = None
    try:
        root_descriptor = _open_directory_chain(root, Path(), create=False)
        if root_descriptor is None:
            raise GeneratedOutputError(Path("AGENTS.md"))
        with os.scandir(root_descriptor) as entries:
            for entry in entries:
                name = entry.name
                if not name.startswith(ROOT_AGENTS_TEMP_PREFIX):
                    continue
                if not name.endswith(ROOT_AGENTS_TEMP_SUFFIX):
                    continue
                token = name[
                    len(ROOT_AGENTS_TEMP_PREFIX) : -len(ROOT_AGENTS_TEMP_SUFFIX)
                ]
                if (
                    len(token) == ROOT_AGENTS_TEMP_TOKEN_LENGTH
                    and all(character in LOWERCASE_HEX for character in token)
                ):
                    raise UnexpectedGeneratedPath
    except UnexpectedGeneratedPath:
        raise
    except GeneratedOutputError:
        raise
    except OSError as error:
        raise GeneratedOutputError(Path("AGENTS.md")) from error
    finally:
        if root_descriptor is not None:
            try:
                os.close(root_descriptor)
            except OSError as error:
                raise GeneratedOutputError(Path("AGENTS.md")) from error

    allowed = set(GENERATED_PATHS)
    for namespace, generated_path in (
        (CODEX_MARKETPLACE.parent, CODEX_MARKETPLACE),
        (CODEX_MANIFEST.parent, CODEX_MANIFEST),
    ):
        descriptor: int | None = None
        try:
            descriptor = _open_directory_chain(root, namespace, create=False)
            if descriptor is not None:
                _scan_directory(descriptor, namespace, allowed)
        except UnexpectedGeneratedPath:
            raise
        except GeneratedOutputError as error:
            raise GeneratedOutputError(generated_path) from error
        finally:
            if descriptor is not None:
                try:
                    os.close(descriptor)
                except OSError as error:
                    raise GeneratedOutputError(generated_path) from error


def _output_error(relative_path: Path, error: GeneratedOutputError) -> None:
    if error.relative_path is not None:
        raise error
    raise GeneratedOutputError(relative_path) from error


def _synchronize(root: Path, write: bool) -> tuple[bool, bool]:
    expected = expected_artifacts(root)
    _scan_generated_namespaces(root)

    parent_descriptors: dict[Path, int | None] = {}
    observed: dict[Path, bytes | None] = {}
    prepared_outputs: list[tuple[Path, _PreparedGeneratedOutput]] = []
    try:
        for relative_path in GENERATED_PATHS:
            try:
                parent_fd = _open_directory_chain(
                    root, relative_path.parent, create=False
                )
                parent_descriptors[relative_path] = parent_fd
                observed[relative_path] = (
                    None
                    if parent_fd is None
                    else _read_generated_at(parent_fd, relative_path.name)
                )
            except GeneratedOutputError as error:
                _output_error(relative_path, error)

        drifted = [
            relative_path
            for relative_path in GENERATED_PATHS
            if observed[relative_path] != expected[relative_path]
        ]
        if not write:
            for relative_path in drifted:
                print(
                    f"{relative_path.as_posix()}: {DRIFT_DIAGNOSTIC}",
                    file=sys.stderr,
                )
            return not drifted, False

        for relative_path in GENERATED_PATHS:
            if parent_descriptors[relative_path] is None:
                try:
                    parent_descriptors[relative_path] = _open_directory_chain(
                        root, relative_path.parent, create=True
                    )
                except GeneratedOutputError as error:
                    _output_error(relative_path, error)

        for relative_path in GENERATED_PATHS:
            parent_fd = parent_descriptors[relative_path]
            if parent_fd is None:
                raise GeneratedOutputError(relative_path)
            try:
                current = _read_generated_at(parent_fd, relative_path.name)
                if current != expected[relative_path]:
                    prepared_outputs.append(
                        (
                            relative_path,
                            _prepare_generated_at(
                                parent_fd,
                                relative_path.name,
                                expected[relative_path],
                            ),
                        )
                    )
            except GeneratedOutputError as error:
                _output_error(relative_path, error)

        for relative_path, prepared in prepared_outputs:
            try:
                _commit_prepared_output(prepared)
            except GeneratedOutputError as error:
                _output_error(relative_path, error)
        return True, bool(prepared_outputs)
    finally:
        close_error: Path | None = None
        for relative_path, prepared in prepared_outputs:
            try:
                _cleanup_prepared_output(prepared)
            except GeneratedOutputError:
                close_error = close_error or relative_path
        for relative_path, descriptor in parent_descriptors.items():
            if descriptor is not None:
                try:
                    os.close(descriptor)
                except OSError:
                    close_error = close_error or relative_path
        if close_error is not None:
            raise GeneratedOutputError(close_error)


def synchronize(root: Path, write: bool) -> bool:
    """Write all generated artifacts or report whether their bytes match."""

    try:
        synchronized, _ = _synchronize(root, write)
    except CanonicalInputError as error:
        relative_path = str(error) or "CLAUDE.md"
        print(f"{relative_path}: {CANONICAL_DIAGNOSTIC}", file=sys.stderr)
        return False
    except UnexpectedGeneratedPath:
        print(UNEXPECTED_DIAGNOSTIC, file=sys.stderr)
        return False
    except GeneratedOutputError as error:
        relative_path = error.relative_path or Path("AGENTS.md")
        print(f"{relative_path.as_posix()}: {OUTPUT_DIAGNOSTIC}", file=sys.stderr)
        return False
    return synchronized


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="write generated files")
    mode.add_argument("--check", action="store_true", help="check generated files")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    root = Path(__file__).resolve().parent.parent

    try:
        synchronized, changed = _synchronize(root, write=arguments.write)
    except CanonicalInputError as error:
        relative_path = str(error) or "CLAUDE.md"
        print(f"{relative_path}: {CANONICAL_DIAGNOSTIC}", file=sys.stderr)
        return 1
    except UnexpectedGeneratedPath:
        print(UNEXPECTED_DIAGNOSTIC, file=sys.stderr)
        return 1
    except GeneratedOutputError as error:
        relative_path = error.relative_path or Path("AGENTS.md")
        print(f"{relative_path.as_posix()}: {OUTPUT_DIAGNOSTIC}", file=sys.stderr)
        return 1

    if not synchronized:
        return 1
    if arguments.write and changed:
        print("updated generated artifacts")
    else:
        print("generated artifacts are synchronized")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
