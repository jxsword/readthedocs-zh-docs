#!/usr/bin/env python3
"""Validate that a batch of PO files is fully translated and has no fuzzy entries.

Usage::

    python scripts/check_batch.py B1
    python scripts/check_batch.py --files locale/zh_CN/LC_MESSAGES/index.po ...

Reads ``docs/batch_manifest.txt`` when given a batch id (B1..B7). Each batch is
expected to be fully translated before it is committed, while the global
``sphinx-intl stat`` gate only applies after all batches are complete.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from babel.messages import pofile

ROOT = Path(__file__).resolve().parent.parent
LOCALE = ROOT / "locale" / "zh_CN" / "LC_MESSAGES"
MANIFEST = ROOT / "docs" / "batch_manifest.txt"


def read_manifest() -> dict[str, list[str]]:
    batches: dict[str, list[str]] = {}
    current: str | None = None
    for raw in MANIFEST.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            current = line[1:].strip()
            batches[current] = []
        elif current:
            batches[current].append(line)
    return batches


def check(rel_paths: list[str]) -> int:
    total = untranslated = fuzzy = 0
    broken: list[str] = []
    for rel in rel_paths:
        path = LOCALE / rel
        if not path.exists():
            broken.append(f"missing PO: {rel}")
            continue
        with path.open(encoding="utf-8") as fh:
            catalog = pofile.read_po(fh)
        for msg in catalog:
            if not msg.id:
                continue
            total += 1
            if msg.fuzzy:
                fuzzy += 1
            elif not msg.string:
                untranslated += 1
    print(f"msgid={total} untranslated={untranslated} fuzzy={fuzzy}")
    for item in broken:
        print(f"  [FAIL] {item}")
    if untranslated or fuzzy or broken:
        print("[check_batch] FAILED: batch is not fully translated.")
        return 1
    print("[check_batch] PASS: batch fully translated, no fuzzy.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("batch", nargs="?", help="batch id from batch_manifest.txt (B1..B7)")
    parser.add_argument("--files", nargs="+", help="explicit PO paths relative to locale/zh_CN/LC_MESSAGES")
    args = parser.parse_args()

    if args.files:
        return check(args.files)
    if not args.batch:
        parser.error("provide a batch id or --files")
    batches = read_manifest()
    if args.batch not in batches:
        print(f"unknown batch {args.batch!r}; available: {', '.join(batches)}", file=sys.stderr)
        return 2
    print(f"batch {args.batch}: {len(batches[args.batch])} PO files")
    return check(batches[args.batch])


if __name__ == "__main__":
    raise SystemExit(main())
