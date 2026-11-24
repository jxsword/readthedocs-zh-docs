#!/usr/bin/env python3
"""Normalize RST inline-markup boundaries in translated msgstr.

docutils requires whitespace or ASCII punctuation after a closing inline
marker (``, **, *). A full-width parenthesis or CJK character immediately
after the closing marker prevents recognition of the end-string. This script
inserts a space only after a *complete* markup pair, never after an opening
marker, so code spans containing CJK remain intact.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from babel.messages import pofile

ROOT = Path(__file__).resolve().parent.parent
LOCALE = ROOT / "locale" / "zh_CN" / "LC_MESSAGES"

CJK_CLASS = "\u4e00-\u9fff"
# Full-width punctuation that docutils does not treat as a valid boundary.
FW_PUNCT = "\uff08\uff09\uff1a\uff1b\uff0c\uff1a\uff1b\uff0c\u3001\u3002\uff01\uff1f\u300c\u300d\u300e\u300f\uff08\uff09"
BOUNDARY = FW_PUNCT + CJK_CLASS

# Full complete pairs with a problematic char right after the closing marker.
LITERAL_RE = re.compile(r"(``[^`\n]+``)(?=[" + BOUNDARY + r"])")
STRONG_RE = re.compile(r"(\*\*[^*\n]+\*\*)(?=[" + BOUNDARY + r"])")
EMPH_RE = re.compile(r"(?<!\*)(\*[^*\n]+\*)(?!\*)(?=[" + BOUNDARY + r"])")
# Named / anonymous references: `text`_ or `text`__
NAMED_REF_RE = re.compile(r"(`[^`\n]+`_{1,2})(?=[" + BOUNDARY + r"])")
# Explicit roles: :guilabel:`text`, :doc:`text <target>`, :term:`text`
ROLE_REF_RE = re.compile(r"(:[a-z]+:`[^`\n]+`)(?=[" + BOUNDARY + r"])")


def fix_text(text: str) -> str:
    text = LITERAL_RE.sub(r"\1 ", text)
    text = STRONG_RE.sub(r"\1 ", text)
    text = EMPH_RE.sub(r"\1 ", text)
    text = NAMED_REF_RE.sub(r"\1 ", text)
    text = ROLE_REF_RE.sub(r"\1 ", text)
    return text


def main() -> int:
    changed = 0
    for f in sorted(LOCALE.rglob("*.po")):
        with f.open(encoding="utf-8") as fh:
            catalog = pofile.read_po(fh)
        dirty = False
        for msg in catalog:
            if not msg.id or not msg.string or msg.fuzzy:
                continue
            fixed = fix_text(msg.string)
            if fixed != msg.string:
                msg.string = fixed
                dirty = True
                changed += 1
        if dirty:
            with f.open("wb") as fh:
                pofile.write_po(fh, catalog, omit_header=False, width=79)
    print(f"fixed {changed} entries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
