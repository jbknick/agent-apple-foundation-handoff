#!/usr/bin/env python3
"""Generate or check provider adapters derived from canonical repository data."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import stat
import sys
import tempfile
from typing import Sequence


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


def _expected_bytes(root: Path) -> bytes:
    try:
        canonical_text = (root / "CLAUDE.md").read_bytes().decode("utf-8")
        return render_agents(canonical_text).encode("utf-8")
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
        if not stat.S_ISREG(opened.st_mode) or (
            opened.st_dev,
            opened.st_ino,
        ) != (metadata.st_dev, metadata.st_ino):
            raise GeneratedOutputError
        with os.fdopen(descriptor, "rb") as stream:
            descriptor = None
            return stream.read()
    except OSError as error:
        raise GeneratedOutputError from error
    finally:
        if descriptor is not None:
            os.close(descriptor)


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
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = None
            stream.write(expected)
            stream.flush()
            os.fsync(stream.fileno())

        temporary_metadata = temporary.lstat()
        if not stat.S_ISREG(temporary_metadata.st_mode):
            raise GeneratedOutputError
        _regular_output_metadata(generated)
        os.replace(temporary, generated)
        temporary = None
    except GeneratedOutputError:
        raise
    except OSError as error:
        raise GeneratedOutputError from error
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if temporary is not None:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
            except OSError:
                pass


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
