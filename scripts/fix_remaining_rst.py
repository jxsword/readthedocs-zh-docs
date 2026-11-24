#!/usr/bin/env python3
"""Fix specific RST reference issues introduced during translation.

Uses substring replacement (not exact msgstr match) because translations
can span multiple physical lines in the PO file.
"""

from __future__ import annotations

import sys
from pathlib import Path

from babel.messages import pofile

ROOT = Path(__file__).resolve().parent.parent
LOCALE = ROOT / "locale" / "zh_CN" / "LC_MESSAGES"

FIXES = {
    "reference/environment-variables.po": [
        ("</custom-domains>`（", "</custom-domains>` （"),
    ],
    "automation-rules.po": [
        ("`语义化版本 <https://semver.org/>`__（", "`语义化版本 <https://semver.org/>`__ （"),
    ],
    "reference/git-integration.po": [
        ("`Bitbucket 官方 API 范围文档 <official Bitbucket documentation on API scopes>`_",
         "`official Bitbucket documentation on API scopes`_"),
        ("`请求个人 OAuth 访问权限 <requesting access to your personal OAuth>`_",
         "`requesting access to your personal OAuth`_"),
        ("`请求组织 OAuth 访问权限 <requesting access to your organization OAuth>`_",
         "`requesting access to your organization OAuth`_"),
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
