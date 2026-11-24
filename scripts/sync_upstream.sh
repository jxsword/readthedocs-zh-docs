#!/usr/bin/env bash
# Bump the upstream submodule, regenerate gettext catalogs, and merge them
# into the zh_CN PO files. Existing translations are preserved by sphinx-intl.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

VENV_BIN="$ROOT/.venv/Scripts"
[ -d "$VENV_BIN" ] || VENV_BIN="$ROOT/.venv/bin"
PY="$VENV_BIN/python"
SPHINX_BUILD="$VENV_BIN/sphinx-build"
SPHINX_INTL="$VENV_BIN/sphinx-intl"

if [ ! -x "$PY" ]; then
  echo "[sync] 未找到虚拟环境，请先按 README.md 创建 .venv 并安装依赖。" >&2
  exit 1
fi

echo "[sync] 1/4 bump upstream submodule"
git submodule update --remote upstream

echo "[sync] 2/4 regenerate gettext catalogs"
rm -rf _build/gettext
PROJECT=user "$SPHINX_BUILD" -b gettext -c . upstream/docs _build/gettext

echo "[sync] 3/4 merge catalogs into locale/zh_CN (existing translations kept)"
"$SPHINX_INTL" update -d locale -p _build/gettext -l zh_CN --no-obsolete

echo "[sync] 4/4 refresh upstream commit metadata"
"$PY" scripts/gen_upstream_meta.py

echo "[sync] 完成。请检查 git diff 后提交："
echo "  git add upstream locale _generated && git commit -m 'chore: sync upstream <sha>'"
