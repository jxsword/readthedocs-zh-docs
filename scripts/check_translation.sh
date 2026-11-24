#!/usr/bin/env bash
# Quality gates for the current translation state.
# 1) sphinx-intl stat  2) warning-free build  3) upstream marker
# 4) upstream pristine  5) reminder for manual preview inspection
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

VENV_BIN="$ROOT/.venv/Scripts"
[ -d "$VENV_BIN" ] || VENV_BIN="$ROOT/.venv/bin"
PY="$VENV_BIN/python"
SPHINX_BUILD="$VENV_BIN/sphinx-build"
SPHINX_INTL="$VENV_BIN/sphinx-intl"

if [ ! -x "$PY" ]; then
  echo "[check] 未找到虚拟环境，请先按 README.md 创建 .venv 并安装依赖。" >&2
  exit 1
fi

fail=0
pass() { printf '  [PASS] %s\n' "$1"; }
bad() { printf '  [FAIL] %s\n' "$1"; fail=1; }

echo "== 1/5 译文完整性 (sphinx-intl stat) =="
STAT_OUTPUT="$("$SPHINX_INTL" stat -d locale -l zh_CN 2>&1)"
STAT_RC=$?
printf '%s\n' "$STAT_OUTPUT"
if [ "$STAT_RC" -eq 0 ]; then
  pass "sphinx-intl stat 退出码为 0"
else
  bad "sphinx-intl stat 退出码为 $STAT_RC（期望 0）"
fi

echo "== 2/5 构建无错 (sphinx-build -W --keep-going) =="
"$PY" scripts/gen_upstream_meta.py
"$SPHINX_INTL" build -d locale -l zh_CN
rm -rf _build/check
if PROJECT=user "$SPHINX_BUILD" -b html -W --keep-going -c . -D language=zh_CN \
    upstream/docs _build/check/html; then
  pass "sphinx-build -W --keep-going 0 error"
else
  bad "sphinx-build 构建失败或存在 warning（-W）"
fi

echo "== 3/5 提交标记一致性 =="
EXPECTED_SHA="$(git -C upstream rev-parse HEAD)"
EXPECTED_SHORT="$(git -C upstream rev-parse --short=12 HEAD)"
EXPECTED_TIME="$(git -C upstream log -1 --format=%cI)"
INDEX_HTML="_build/check/html/index.html"
if [ ! -f "$INDEX_HTML" ]; then
  bad "未找到构建产物 $INDEX_HTML"
else
  if grep -Fq "$EXPECTED_SHA" "$INDEX_HTML"; then
    pass "页脚 full sha == $EXPECTED_SHA"
  else
    bad "页脚未包含 full sha $EXPECTED_SHA"
  fi
  if grep -Fq "$EXPECTED_TIME" "$INDEX_HTML"; then
    pass "页脚 commit time == $EXPECTED_TIME"
  else
    bad "页脚未包含 commit time $EXPECTED_TIME（short sha: $EXPECTED_SHORT）"
  fi
fi

echo "== 4/5 上游源文零改动 =="
UPSTREAM_STATUS="$(git -C upstream status --porcelain)"
if [ -z "$UPSTREAM_STATUS" ]; then
  pass "git -C upstream status --porcelain 为空"
else
  bad "upstream 存在改动："
  printf '%s\n' "$UPSTREAM_STATUS"
fi

echo "== 5/5 本地预览人工巡检 =="
echo "  请运行 make preview，打开 http://127.0.0.1:8000"
echo "  巡检各批次代表页：中文标题、侧边栏、交叉引用、代码块、页脚标记、搜索页。"

if [ "$fail" -ne 0 ]; then
  echo "[check] 质量门禁未通过，请修复上述失败项。" >&2
  exit 1
fi
echo "[check] 自动门禁全部通过；人工巡检结果由执行者确认。"
