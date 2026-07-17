#!/usr/bin/env python3
"""Generate or check provider adapters derived from canonical repository data."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Sequence


BEGIN = "<!-- BEGIN GENERATED AGENTS ADAPTER -->"
END = "<!-- END GENERATED AGENTS ADAPTER -->"
GENERATED_HEADER = (
    "# AGENTS.md\n\n"
    "<!-- Generated from CLAUDE.md by scripts/sync_generated_artifacts.py. "
    "Do not edit directly. -->\n\n"
)


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
    canonical_text = (root / "CLAUDE.md").read_bytes().decode("utf-8")
    return render_agents(canonical_text).encode("utf-8")


def synchronize(root: Path, write: bool) -> bool:
    """Write the adapter or return whether its bytes match exactly."""

    expected = _expected_bytes(root)
    generated = root / "AGENTS.md"
    if generated.is_file() and generated.read_bytes() == expected:
        return True
    if write:
        generated.write_bytes(expected)
        return True

    print("AGENTS.md: generated content is out of date", file=sys.stderr)
    return False


def _is_synchronized(root: Path) -> bool:
    generated = root / "AGENTS.md"
    return generated.is_file() and generated.read_bytes() == _expected_bytes(root)


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
        already_synchronized = _is_synchronized(root)
        if not synchronize(root, write=arguments.write):
            return 1
    except (OSError, UnicodeError, ValueError):
        print("CLAUDE.md: invalid canonical adapter input", file=sys.stderr)
        return 1

    if arguments.write and not already_synchronized:
        print("updated AGENTS.md")
    else:
        print("generated artifacts are synchronized")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
