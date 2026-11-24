#!/usr/bin/env python3
"""Read the upstream submodule's HEAD metadata into _generated/upstream_meta.json.

The generated JSON is consumed by the root ``conf.py`` and injected into
``html_context`` so the rendered pages can display the exact upstream commit
the translation is based on. Values come from git, never from hardcoded text.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UPSTREAM = ROOT / "upstream"
OUTPUT = ROOT / "_generated" / "upstream_meta.json"


def git(*args: str) -> str:
    """Run a git command against the upstream submodule and return stdout."""
    result = subprocess.run(
        ["git", "-C", str(UPSTREAM), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def main() -> None:
    sha = git("rev-parse", "HEAD")
    short_sha = git("rev-parse", "--short=12", "HEAD")
    commit_time = git("log", "-1", "--format=%cI")
    meta = {
        "sha": sha,
        "short_sha": short_sha,
        "commit_time": commit_time,
        "commit_url": f"https://github.com/readthedocs/readthedocs.org/commit/{sha}",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[upstream-meta] {short_sha} {commit_time} -> {OUTPUT.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
