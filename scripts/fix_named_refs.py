#!/usr/bin/env python3
"""Fix named-reference targets broken by translation.

Upstream uses `` `semantic versioning <https://semver.org/>`_ `` style named
references whose display text doubles as the link target. Rewriting the
display text (or adding angle brackets) makes Sphinx report
"inconsistent references in translated message".
"""

from __future__ import annotations

import sys
from pathlib import Path

from babel.messages import pofile

ROOT = Path(__file__).resolve().parent.parent
LOCALE = ROOT / "locale" / "zh_CN" / "LC_MESSAGES"

FIXES = {
    "versions.po": [
        ("`语义化版本 <https://semver.org/>`_", "`semantic versioning <https://semver.org/>`_"),
    ],
    "automation-rules.po": [
        ("`语义化版本 <https://semver.org/>`__", "`semantic versioning <https://semver.org/>`__"),
    ],
}


def main() -> int:
    changed = 0
    for name, pairs in FIXES.items():
        path = LOCALE / name
        with path.open(encoding="utf-8") as fh:
            catalog = pofile.read_po(fh)
        dirty = False
        for msg in catalog:
            if not msg.string:
                continue
            new = msg.string
            for old, replacement in pairs:
                new = new.replace(old, replacement)
            if new != msg.string:
                msg.string = new
                dirty = True
                changed += 1
        if dirty:
            with path.open("wb") as fh:
                pofile.write_po(fh, catalog, omit_header=False, width=79)
    print(f"fixed {changed} entries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
