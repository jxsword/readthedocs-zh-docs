#!/usr/bin/env python3
"""Assist PO translation: export untranslated entries and import verified translations.

The exported JSON is a list of ``{"id": <msgid>, "loc": <source location>}``.
The import JSON is a flat object mapping msgid -> translation. On import, the
tool verifies gettext placeholders and inline-code tokens are preserved before
writing, and clears the fuzzy flag on the header.

Usage::

    python scripts/translate_po.py export locale/zh_CN/LC_MESSAGES/index.po -o /tmp/index.json
    python scripts/translate_po.py import locale/zh_CN/LC_MESSAGES/index.po /tmp/index.zh.json
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from babel.messages import pofile

PLACEHOLDER_RE = re.compile(r"%\([^)]+\)[sdif]|%[sdif]|\{\{?[^}]*\}?\}|\{[A-Za-z_][A-Za-z0-9_.]*\}")
INLINE_LITERAL_RE = re.compile(r"``[^`]+``|\|[^|]+\|")
ROLE_RE = re.compile(r":([a-z]+):`([^`]*)`")
REF_RE = re.compile(r"`([^`]+)`_")

# Inline markup whose *content* is translatable but whose *presence* is not.
# Only the count of each kind is compared, not the text between the markers.
MARKUP_KINDS = ("``", "**", "``__", "`__")


def _invariant_of_inner(inner: str) -> str:
    """For a role/reference body, return the invariant part.

    ``text <target>`` -> ``target`` (display text is translatable); otherwise
    the whole body is invariant (e.g. a named reference such as ``on their
    documentation`` or ``:envvar:`X```).
    """
    target = re.match(r"[^<]*<([^>]+)>$", inner)
    return target.group(1) if target else inner


def markup_counts(text: str) -> dict[str, int]:
    """Count inline markup constructs by kind.

    The *content* inside inline literals, emphasis and strong markers is
    translatable, so only their counts are compared between source and
    translation. Counting avoids false positives from greedy matching (for
    example ``:numref:`x``` where the trailing triple backtick merges two
    separate literals).
    """
    stripped = ROLE_RE.sub("", text)
    stripped = REF_RE.sub("", stripped)
    counts = {
        "literal": len(re.findall(r"``", text)) // 2,
        "strong": len(re.findall(r"\*\*", text)) // 2,
        "emphasis": len(re.findall(r"(?<!\*)\*(?!\*)", text)) // 2,
        "named_ref": len(re.findall(r"`[^`\n]+`_{1,2}", text)),
        "substitution": len(re.findall(r"\|[^|\n]+\|", text)),
    }
    return counts


def tokens(text: str) -> set[str]:
    """Return invariant tokens: placeholders, inline literals, role/ref targets.

    Display text of hyperlink roles (``:doc:`X </path>```) and inline URLs
    (`` `X <https://...>`_ ``) is translatable; only the target is invariant.
    Named references with no target (`` `X`_ ``) are fully invariant.
    """
    result = set(PLACEHOLDER_RE.findall(text))
    for m in ROLE_RE.finditer(text):
        role, inner = m.group(1), m.group(2)
        if role == "abbr":
            # ``:abbr:`CSV (full name)```: only the abbreviation itself is invariant.
            abbr = re.match(r"([^\s(（]+)", inner)
            if abbr:
                result.add(abbr.group(1))
        else:
            result.add(_invariant_of_inner(inner))
    stripped = ROLE_RE.sub("", text)
    for inner in REF_RE.findall(stripped):
        result.add(_invariant_of_inner(inner))
    stripped = REF_RE.sub("", stripped)
    # Substitution references (|name|) keep their name verbatim.
    result |= set(re.findall(r"\|([^|\n]+)\|", stripped))
    return result


def export(po: Path, out: Path) -> None:
    with po.open(encoding="utf-8") as fh:
        catalog = pofile.read_po(fh)
    entries = []
    for msg in catalog:
        if not msg.id or msg.fuzzy or msg.string:
            continue
        loc = msg.locations[0] if msg.locations else ""
        entries.append({"id": msg.id if isinstance(msg.id, str) else msg.id[0], "loc": loc})
    out.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[export] {po.name}: {len(entries)} entries -> {out}")


def import_translations(po: Path, src: Path) -> int:
    translations = json.loads(src.read_text(encoding="utf-8"))
    with po.open(encoding="utf-8") as fh:
        catalog = pofile.read_po(fh)
    applied = 0
    errors = 0
    for msg in catalog:
        if not msg.id or msg.fuzzy or msg.string:
            continue
        key = msg.id if isinstance(msg.id, str) else msg.id[0]
        if key not in translations:
            continue
        value = translations[key]
        missing = tokens(key) - tokens(value)
        extra = tokens(value) - tokens(key)
        src_counts = markup_counts(key)
        dst_counts = markup_counts(value)
        if src_counts != dst_counts:
            print(f"[warn] markup count mismatch in {po.name}: {key[:60]!r}")
            print(f"       source: {src_counts}")
            print(f"       target: {dst_counts}")
            errors += 1
            continue
        if missing or extra:
            print(f"[warn] token mismatch in {po.name}: {key[:60]!r}")
            if missing:
                print(f"       missing: {sorted(missing)}")
            if extra:
                print(f"       extra: {sorted(extra)}")
            errors += 1
            continue
        msg.string = value
        applied += 1
    header = catalog.get("")
    if header is not None:
        header.fuzzy = False
    with po.open("wb") as fh:
        pofile.write_po(fh, catalog, omit_header=False, width=79)
    print(f"[import] {po.name}: applied {applied}, errors {errors}")
    return 1 if errors else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    ex = sub.add_parser("export")
    ex.add_argument("po", type=Path)
    ex.add_argument("-o", "--out", type=Path, required=True)
    im = sub.add_parser("import")
    im.add_argument("po", type=Path)
    im.add_argument("json", type=Path)
    args = parser.parse_args()
    if args.cmd == "export":
        export(args.po, args.out)
        return 0
    return import_translations(args.po, args.json)


if __name__ == "__main__":
    raise SystemExit(main())
