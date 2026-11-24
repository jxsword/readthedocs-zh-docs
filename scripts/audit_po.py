#!/usr/bin/env python3
"""Audit translated PO entries for malformed RST inline markup.

Checks that inline literals (double backticks) and strong/emphasis markers
are balanced in every translated msgstr. Reports file, source line and a
short excerpt for each offending entry.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from babel.messages import pofile

ROOT = Path(__file__).resolve().parent.parent
LOCALE = ROOT / "locale" / "zh_CN" / "LC_MESSAGES"


def audit() -> int:
    problems: list[tuple[str, str, str, str]] = []
    for f in sorted(LOCALE.rglob("*.po")):
        with f.open(encoding="utf-8") as fh:
            catalog = pofile.read_po(fh)
        for msg in catalog:
            if not msg.id or not msg.string or msg.fuzzy:
                continue
            text = msg.string
            loc = msg.locations[0][1] if msg.locations else -1
            if text.count("``") % 2:
                problems.append((f.name, str(loc), "literal", text[:100]))
            if text.count("**") % 2:
                problems.append((f.name, str(loc), "strong", text[:100]))
            stripped = re.sub(r"``[^`]*``", "", text)
            if stripped.count("`") % 2:
                problems.append((f.name, str(loc), "backtick", text[:100]))
    print(f"problems: {len(problems)}")
    for name, loc, kind, text in problems:
        print(f"  {name}:{loc} [{kind}] {text!r}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(audit())
