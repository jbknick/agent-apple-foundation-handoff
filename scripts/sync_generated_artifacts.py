#!/usr/bin/env python3
"""Generate or check provider adapters derived from canonical repository data."""

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
from typing import Mapping, Sequence


BEGIN = "<!-- BEGIN GENERATED AGENTS ADAPTER -->"
END = "<!-- END GENERATED AGENTS ADAPTER -->"
GENERATED_HEADER = (
    "# AGENTS.md\n\n"
    "<!-- Generated from CLAUDE.md by scripts/sync_generated_artifacts.py. "
    "Do not edit directly. -->\n\n"
)
CANONICAL_DIAGNOSTIC = "CLAUDE.md: invalid canonical adapter input"
DRIFT_DIAGNOSTIC = "AGENTS.md: generated content is out of date"
OUTPUT_DIAGNOSTIC = "AGENTS.md: unsafe or unwritable generated output"
PLUGIN_ID = "apple-foundation-models-handoff"
PLUGIN_ROOT = Path("plugins") / PLUGIN_ID
CLAUDE_MARKETPLACE = Path(".claude-plugin/marketplace.json")
CODEX_MARKETPLACE_INPUT = Path("metadata/codex-marketplace.json")
SHARED_MANIFEST = PLUGIN_ROOT / ".claude-plugin/plugin.json"
CODEX_INTERFACE_INPUT = PLUGIN_ROOT / "metadata/codex-interface.json"
CODEX_MANIFEST = PLUGIN_ROOT / ".codex-plugin/plugin.json"
CODEX_MARKETPLACE = Path(".agents/plugins/marketplace.json")
GENERATED_PATHS = (Path("AGENTS.md"), CODEX_MARKETPLACE, CODEX_MANIFEST)
EXPECTED_SOURCE = "./plugins/apple-foundation-models-handoff"
EXPECTED_VERSION = "0.1.0"


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
    if capabilities != []:
        raise ValueError("capabilities")
    prompts = value["defaultPrompt"]
    if not isinstance(prompts, list) or not 1 <= len(prompts) <= 3:
        raise ValueError("prompt count")
    for prompt in prompts:
        if len(_string(prompt)) > 128:
            raise ValueError("prompt length")
    _https(value["websiteURL"])


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


def expected_artifacts(root: Path) -> dict[Path, bytes]:
    """Render every generated artifact without writing it."""

    inputs = load_canonical_inputs(root)
    return {
        Path("AGENTS.md"): render_agents(inputs.guidance).encode("utf-8"),
        CODEX_MARKETPLACE: render_codex_marketplace(inputs),
        CODEX_MANIFEST: render_codex_manifest(inputs),
    }


def _expected_bytes(root: Path) -> bytes:
    try:
        canonical_text = _read_canonical(root / "CLAUDE.md").decode("utf-8")
        return render_agents(canonical_text).encode("utf-8")
    except CanonicalInputError:
        raise
    except (OSError, UnicodeError, ValueError) as error:
        raise CanonicalInputError from error


def _regular_output_metadata(generated: Path) -> os.stat_result | None:
    try:
        metadata = generated.lstat()
    except FileNotFoundError:
        return None
    except OSError as error:
        raise GeneratedOutputError from error
    if not stat.S_ISREG(metadata.st_mode):
        raise GeneratedOutputError
    return metadata


def _read_generated(generated: Path) -> bytes | None:
    metadata = _regular_output_metadata(generated)
    if metadata is None:
        return None

    descriptor: int | None = None
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(generated, flags)
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or not _same_file(metadata, opened):
            raise GeneratedOutputError
        with os.fdopen(descriptor, "rb") as stream:
            descriptor = None
            content = stream.read()
            after_read = os.fstat(stream.fileno())
            current = generated.lstat()
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


def _remove_unsafe_output(generated: Path) -> None:
    try:
        metadata = generated.lstat()
    except FileNotFoundError:
        return
    except OSError as error:
        raise GeneratedOutputError from error
    if stat.S_ISDIR(metadata.st_mode):
        raise GeneratedOutputError
    try:
        generated.unlink()
    except FileNotFoundError:
        return
    except OSError as error:
        raise GeneratedOutputError from error


def _write_generated(root: Path, generated: Path, expected: bytes) -> None:
    _regular_output_metadata(generated)
    descriptor: int | None = None
    temporary: Path | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=".AGENTS.md.", suffix=".tmp", dir=root
        )
        temporary = Path(temporary_name)
        if hasattr(os, "fchmod"):
            os.fchmod(descriptor, 0o644)
        with os.fdopen(os.dup(descriptor), "wb") as stream:
            stream.write(expected)
            stream.flush()
            os.fsync(stream.fileno())

        intended_metadata = os.fstat(descriptor)
        temporary_metadata = temporary.lstat()
        if not stat.S_ISREG(temporary_metadata.st_mode) or not _same_file(
            intended_metadata, temporary_metadata
        ):
            raise GeneratedOutputError
        _regular_output_metadata(generated)
        os.replace(temporary, generated)
        try:
            generated_metadata = generated.lstat()
        except OSError as error:
            _remove_unsafe_output(generated)
            raise GeneratedOutputError from error
        if not stat.S_ISREG(generated_metadata.st_mode) or not _same_file(
            intended_metadata, generated_metadata
        ):
            _remove_unsafe_output(generated)
            raise GeneratedOutputError
        temporary = None
    except GeneratedOutputError:
        raise
    except OSError as error:
        raise GeneratedOutputError from error
    finally:
        cleanup_error: OSError | None = None
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError as error:
                cleanup_error = error
        if temporary is not None:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
            except OSError as error:
                cleanup_error = cleanup_error or error
        if cleanup_error is not None:
            raise GeneratedOutputError from cleanup_error


def _synchronize(root: Path, write: bool) -> tuple[bool, bool]:
    expected = _expected_bytes(root)
    generated = root / "AGENTS.md"
    if _read_generated(generated) == expected:
        return True, False
    if not write:
        return False, False
    _write_generated(root, generated, expected)
    return True, True


def synchronize(root: Path, write: bool) -> bool:
    """Write the adapter or return whether its bytes match exactly."""

    try:
        synchronized, _ = _synchronize(root, write)
    except CanonicalInputError:
        print(CANONICAL_DIAGNOSTIC, file=sys.stderr)
        return False
    except GeneratedOutputError:
        print(OUTPUT_DIAGNOSTIC, file=sys.stderr)
        return False
    if not synchronized:
        print(DRIFT_DIAGNOSTIC, file=sys.stderr)
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
    except CanonicalInputError:
        print(CANONICAL_DIAGNOSTIC, file=sys.stderr)
        return 1
    except GeneratedOutputError:
        print(OUTPUT_DIAGNOSTIC, file=sys.stderr)
        return 1

    if not synchronized:
        print(DRIFT_DIAGNOSTIC, file=sys.stderr)
        return 1
    if arguments.write and changed:
        print("updated AGENTS.md")
    else:
        print("generated artifacts are synchronized")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
