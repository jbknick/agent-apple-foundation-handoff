#!/usr/bin/env python3
"""Generate or check AGENTS.md from the bounded CLAUDE.md section."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

BEGIN = "<!-- BEGIN GENERATED AGENTS ADAPTER -->"
END = "<!-- END GENERATED AGENTS ADAPTER -->"
HEADER = (
    "# AGENTS.md\n\n"
    "<!-- Generated from CLAUDE.md by scripts/sync_generated_artifacts.py. "
    "Do not edit directly. -->\n\n"
)


def render(source: str) -> str:
    if source.count(BEGIN) != 1 or source.count(END) != 1:
        raise ValueError("CLAUDE.md must contain one generated adapter section")
    body = source.split(BEGIN, 1)[1].split(END, 1)[0].strip()
    if not body:
        raise ValueError("generated adapter section is empty")
    return HEADER + body + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = render(Path("CLAUDE.md").read_text(encoding="utf-8"))
    target = Path("AGENTS.md")
    if args.write:
        target.write_text(expected, encoding="utf-8")
        return 0
    if not target.exists() or target.read_text(encoding="utf-8") != expected:
        print("generated content is out of date", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
