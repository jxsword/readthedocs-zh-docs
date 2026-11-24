"""Wrapping Sphinx configuration for the Chinese Read the Docs user docs.

The authoritative configuration lives in ``upstream/docs/conf.py`` and is never
modified. This file evaluates it with ``PROJECT=user``, then overrides only the
settings that must point at this repository: translation catalogs, templates,
and upstream commit metadata.

Usage (from the repository root)::

    PROJECT=user sphinx-build -b gettext -c . upstream/docs _build/gettext
    PROJECT=user sphinx-build -b html -c . -D language=zh_CN upstream/docs _build/html
"""

from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
UPSTREAM_DOCS = ROOT / "upstream" / "docs"
USER_DOCS = UPSTREAM_DOCS / "user"

# sphinx-multiproject selects the docset from this environment variable.
os.environ["PROJECT"] = "user"

# Evaluate the upstream conf in its own directory: it appends ``_ext`` to
# sys.path via a relative path and derives template paths from __file__.
_upstream_conf = UPSTREAM_DOCS / "conf.py"
_original_cwd = os.getcwd()
try:
    os.chdir(UPSTREAM_DOCS)
    _upstream_globals: dict[str, object] = {
        "__file__": str(_upstream_conf),
        "__name__": "upstream_conf",
    }
    exec(compile(_upstream_conf.read_text(encoding="utf-8"), str(_upstream_conf), "exec"), _upstream_globals)
finally:
    os.chdir(_original_cwd)

for _key, _value in _upstream_globals.items():
    if not _key.startswith("_"):
        globals()[_key] = _value

# --- Overrides that bind the build to this repository ---------------------

# Translation catalogs produced by sphinx-intl live at the repository root.
locale_dirs = [str(ROOT / "locale")]

# Keep the upstream templates and prepend ours so the commit marker template
# can extend the theme while preserving upstream's extrahead block.
templates_path = [
    str(ROOT / "_templates"),
    str(UPSTREAM_DOCS / "_templates"),
]

# Upstream paths are relative to its own confdir; resolve them against ROOT.
html_static_path = [
    str(UPSTREAM_DOCS / "_static"),
    str(USER_DOCS / "_static"),
]
html_logo = str(UPSTREAM_DOCS / "img" / "logo.svg")

language = "zh_CN"

# Inject the frozen upstream commit metadata generated before the build.
_meta_path = ROOT / "_generated" / "upstream_meta.json"
if _meta_path.exists():
    _meta = json.loads(_meta_path.read_text(encoding="utf-8"))
else:
    _meta = {
        "sha": "unknown",
        "short_sha": "unknown",
        "commit_time": "unknown",
        "commit_url": "",
    }

html_context = dict(globals().get("html_context", {}))
html_context.update(
    {
        "upstream_sha": _meta["sha"],
        "upstream_short_sha": _meta["short_sha"],
        "upstream_commit_time": _meta["commit_time"],
        "upstream_commit_url": _meta["commit_url"],
    }
)
