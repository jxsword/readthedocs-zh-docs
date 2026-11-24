# Read the Docs 官方文档中文翻译计划

- 日期：2026-11-24
- 状态：方案已确认，待分批执行
- 目标站点：Read the Docs（非 GitHub Pages）
- 目标仓库：`jxsword/readthedocs-zh-docs`
- 决策依据：`docs/decision_log.md` 中 DR-001 ~ DR-005
- 实施约束：实施过程中若发现本计划存在错误、歧义或需补充之处，必须先修订本文件（涉及决策时同步 `docs/decision_log.md`）并确认，再继续执行；不得绕过计划直接改动实施。

## 1. 目标与范围

1. 权威源：`https://github.com/readthedocs/readthedocs.org` 的 `docs/user/`（与 `https://docs.readthedocs.com/platform/stable/` 线上内容同源；已实测该站 “Edit on GitHub” 指向 `docs/user/index.rst`）。
2. 范围：上游 `docs/user/` 全量页面，约 154 个 `.rst` + 1 个 `.md`；不翻译 `docs/dev/`、`_ext/`、`_static/`、`_templates/`。
3. 产物：中文 Sphinx 站点，完整保留上游结构、交叉引用、指令与代码块；页脚/首页标注所依据的上游提交 id 与时间。
4. 流程：本地全量翻译 → 本地预览验收 → 用 gh 创建同名仓库并推送 → 在 RTD 托管。远端动作在完成本地验收之后执行。

## 2. 已确认决策摘要

| 编号 | 决策 | 结论 |
|---|---|---|
| DR-001 | 翻译范围 | 仅 `docs/user/` 全量 |
| DR-002 | 翻译载体 | sphinx-intl + PO，源文不改动 |
| DR-003 | 版本锚定 | git submodule 固定上游 commit，构建时动态读取元数据 |
| DR-004 | 目标仓库 | `jxsword/readthedocs-zh-docs`，本地验收后再创建推送 |
| DR-005 | 本轮交付 | 仅计划文档与决策日志，不初始化仓库、不翻译正文 |

## 3. 技术架构

### 3.1 目录结构（后续阶段创建）

```text
readthedocs-zh-docs/
├── .gitmodules                     # upstream -> readthedocs/readthedocs.org (branch=main)
├── .readthedocs.yaml               # RTD v2 配置，开启 submodules
├── conf.py                         # 包装配置：加载上游 conf，覆盖 locale_dirs/language/html_context
├── Makefile                        # gettext / update / build / preview / check
├── README.md                       # 本机依赖安装部署详述（用户明确要求）
├── requirements-local.txt          # 本地工具额外依赖（如 polib 等，若需要）
├── docs/
│   ├── decision_log.md
│   ├── translation_plan.md
│   └── glossary.md                 # 术语表：专名保留英文，代码/内联代码不译
├── locale/
│   └── zh_CN/LC_MESSAGES/          # *.po 译文，唯一手工翻译产物
├── _templates/
│   └── layout.html                 # 注入“基于上游提交”标记
├── scripts/
│   ├── gen_upstream_meta.py        # 从 submodule 动态读取 commit id / time
│   ├── sync_upstream.sh            # bump submodule + 生成 pot + 合并 po
│   ├── translate_po.py             # 批量翻译未翻译条目（AI 辅助）
│   └── check_translation.sh        # sphinx-intl stat + 构建门禁
├── upstream/                       # submodule，只读，不修改
└── _build/                         # 本地构建产物，不入库
```

### 3.2 数据流

```text
upstream/docs/user/*.rst
        │  sphinx-build -b gettext -c . upstream/docs/user _build/gettext
        ▼
_build/gettext/*.pot
        │  sphinx-intl update -d locale -p _build/gettext -l zh_CN --no-obsolete
        ▼
locale/zh_CN/LC_MESSAGES/*.po  ←── translate_po.py + glossary.md（唯一人工/AI 翻译面）
        │  sphinx-intl build -d locale -l zh_CN   （po → mo）
        ▼
sphinx-build -b html -c . -D language=zh_CN upstream/docs/user _build/html
        │  同时由 gen_upstream_meta.py 注入 html_context
        ▼
带提交标记的中文 HTML（静态产物，生成后冻结）
```

关键点：上游 `.rst` 始终来自 submodule，翻译只落在 `.po`。上游更新时不会覆盖译文，只会在 `.po` 中新增/失效条目。

### 3.3 提交标记生成机制

1. `scripts/gen_upstream_meta.py` 在每次本地构建和 RTD 构建时执行：
   - `git -C upstream rev-parse HEAD` → 完整 commit id
   - `git -C upstream log -1 --format=%cI` → committer date（ISO 8601，作为“提交时间”）
   - 写入 `_generated/upstream_meta.json`，供 `conf.py` 读入 `html_context`。
2. `_templates/layout.html` 在页脚（并在首页顶部卡片）渲染：
   - `中文翻译基于上游文档提交 <short-sha>（<commit-time>）`
   - 链接到 `https://github.com/readthedocs/readthedocs.org/commit/<full-sha>`
3. 值来自 submodule HEAD 而非硬编码；HTML 生成后即为静态值，只有执行 `sync_upstream.sh` 推高 submodule 并重新构建才会变化。
4. “最新”定义为**同步时刻上游 `main` 的最新提交**；若上游 stable 对应其它 ref，只需修改 `.gitmodules` 的 `branch`，其余流程不变。

## 4. 本机依赖环境与安装部署（README.md 必须详述）

### 4.1 依赖清单

| 依赖 | 用途 | 来源 |
|---|---|---|
| Python 3.13 + venv | 构建环境隔离 | 本机已有 Python 3.13.14 |
| `upstream/requirements/docs.txt` | Sphinx 8.2.3、sphinx-intl 2.4.0、sphinx-multiproject、主题与扩展 | 上游仓库固定版本 |
| GNU gettext（`msgfmt`/`msgmerge`） | PO/MO 编译与合并兜底 | 当前 Windows 环境**未安装**，需补 |
| git 2.55 + gh 2.101 | submodule 与远端创建推送 | 本机已有，gh 已登录 `jxsword` 且具 repo scope |
| `polib`（可选） | PO 批量翻译脚本解析 | 若 `translate_po.py` 需要 |

环境风险：本机全局 `sphinx-build` 为 9.1.0，而上游 `requirements/docs.txt` 固定 `sphinx==8.2.3`。**必须使用 venv 安装上游锁定依赖**，否则可能出现扩展不兼容或构建结果不可复现。

### 4.2 Windows 安装步骤（写入 README）

```bash
# 1) 进入项目并创建虚拟环境
cd /e/proj/readthedocs-guide/readthedocs-zh-docs
python -m venv .venv
source .venv/Scripts/activate          # Git Bash；PowerShell 用 .venv\Scripts\Activate.ps1

# 2) 安装上游锁定依赖（含 sphinx / sphinx-intl）
pip install -r upstream/requirements/docs.txt

# 3) 安装 GNU gettext（若 msgfmt --version 不可用）
scoop install gettext
msgfmt --version
msgmerge --version

# 4) 初始化 submodule
git submodule update --init --recursive

# 5) 验证
python --version && sphinx-build --version && sphinx-intl --version && gh auth status
```

### 4.3 Linux / macOS 安装步骤（写入 README）

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r upstream/requirements/docs.txt
sudo apt-get install gettext          # Debian/Ubuntu
brew install gettext                  # macOS
git submodule update --init --recursive
```

### 4.4 依赖验证清单

- `sphinx-build --version` 输出 8.2.3（venv 内）
- `sphinx-intl --version` 可用
- `msgfmt --version`、`msgmerge --version` 可用
- `git -C upstream rev-parse HEAD` 输出 40 位 sha
- `gh auth status` 显示 `jxsword`

## 5. 仓库初始化与 submodule

```bash
git init
git add . && git commit -m "docs: add translation plan and decision log"

git submodule add -b main https://github.com/readthedocs/readthedocs.org.git upstream
git commit -m "chore: pin upstream docs source"

# 后续每次同步上游
./scripts/sync_upstream.sh
# 内部：git submodule update --remote upstream
#       PROJECT=user sphinx-build -b gettext -c . upstream/docs/user _build/gettext
#       sphinx-intl update -d locale -p _build/gettext -l zh_CN --no-obsolete
#       git add upstream locale && git commit -m "chore: sync upstream and refresh po"
```

## 6. 翻译工作流

### 6.1 首次全量

1. 初始化 submodule，锁定一个上游 commit。
2. 用包装 `conf.py` 生成 pot：`PROJECT=user sphinx-build -b gettext -c . upstream/docs/user _build/gettext`。
3. `sphinx-intl update -d locale -p _build/gettext -l zh_CN --no-obsolete` 生成全部 PO。
4. 建立 `docs/glossary.md`，约定：
   - 专名保留英文：Read the Docs、Sphinx、MkDocs、Jupyter、Git、GitHub、API、Webhook 等；
   - 代码块、内联代码、路径、命令、配置键不译；
   - RST 角色/指令（`:doc:`、``.. note::`` 等）结构不译，只译其文本内容。
5. 按批次翻译 PO（见 6.3），每批提交一次。
6. `sphinx-intl stat -d locale -l zh_CN` 必须退出码 0（全部已翻译且非 fuzzy）。

### 6.2 增量更新（上游有新提交时）

1. `git submodule update --remote upstream`，审查上游 diff，必要时人工确认 breaking change。
2. 重新生成 pot 并 `sphinx-intl update`：已有译文自动保留；新增/变更条目变为未翻译或 fuzzy。
3. 只翻译新增/失效条目，不重译已确认条目。
4. 更新提交标记（自动来自新 submodule HEAD），重新构建与预览。
5. 提交：`git add upstream locale && git commit -m "chore: sync upstream <sha>"`。

### 6.3 翻译批次（按上游 toctree caption 划分）

| 批次 | 内容 | 验收 |
|---|---|---|
| B1 | Getting started（tutorial、intro、examples） | 该目录 PO 全译、预览通过 |
| B2 | Project setup and configuration | 同上 |
| B3 | Build process | 同上 |
| B4 | Hosting documentation | 同上 |
| B5 | AI and agents / Maintaining projects | 同上 |
| B6 | Business features / How-to guides | 同上 |
| B7 | Reference / API / Changelog / About | 全站 `sphinx-intl stat` 通过 |

### 6.4 PO 翻译规范

- 保留所有 gettext 占位符（`%(name)s`、`{}`、`{var}`）与 RST 内联标记。
- 不译：命令行、文件路径、配置键、代码、产品专名、链接 URL。
- 术语统一查 `docs/glossary.md`；新增术语先补表再翻译。
- 不改动上游 submodule 中任何文件。

## 7. 本地构建与预览

```bash
# 生成元数据 + 编译 mo + 构建 HTML
python scripts/gen_upstream_meta.py
sphinx-intl build -d locale -l zh_CN
PROJECT=user sphinx-build -b html -c . -D language=zh_CN upstream/docs/user _build/html

# 实时预览
PROJECT=user sphinx-autobuild -c . -D language=zh_CN upstream/docs/user _build/html \
  --host 127.0.0.1 --port 8000
```

验收点：打开 `http://127.0.0.1:8000`，检查中文标题、侧边栏、交叉引用、代码块、页脚提交标记、搜索页。

## 8. 质量门槛

| 门槛 | 命令/条件 | 通过标准 |
|---|---|---|
| 译文完整 | `sphinx-intl stat -d locale -l zh_CN` | 退出码 0，无 fuzzy |
| 构建无错 | `sphinx-build -b html -W --keep-going ...` | 0 error（warning 逐项登记） |
| 标记正确 | 页面页脚文本 vs `git -C upstream rev-parse HEAD` | sha 与时间一致 |
| 源文零改动 | `git -C upstream status --porcelain` | 输出为空 |
| 本地预览 | 人工巡检 7 个批次代表页 | 无乱码、无断裂链接 |

## 9. RTD 托管配置（非 GitHub Pages）

在仓库根放置 `.readthedocs.yaml`（v2 语法已对照官方文档核实）：

```yaml
version: 2
build:
  os: ubuntu-24.04
  tools:
    python: "3.13"
  jobs:
    pre_build:
      - python scripts/gen_upstream_meta.py
      - sphinx-intl build -d locale -l zh_CN
    build:
      html:
        - sphinx-build -b html -c . -D language=zh_CN upstream/docs/user $READTHEDOCS_OUTPUT/html
submodules:
  include: all
python:
  install:
    - requirements: upstream/requirements/docs.txt
```

RTD 网站侧设置：导入 `jxsword/readthedocs-zh-docs`，默认分支 `main`；不启用 GitHub Pages；如需 `stable` 别名，用 RTD 的 version alias 配置指向 `main`。

## 10. GitHub 创建与推送（本地验收后执行）

```bash
git add . && git commit -m "docs: complete zh_CN translation"
gh repo create jxsword/readthedocs-zh-docs --public --source=. --remote=origin --push
git branch --set-upstream-to=origin/main main
```

前提：第 8 节全部门槛通过；`gh auth status` 正常。远端创建为不可逆外部动作，执行前再次确认仓库名与公开性。

## 11. 风险与缓解

| 风险 | 影响 | 缓解 |
|---|---|---|
| 上游 `docs/conf.py` 依赖 `PROJECT` 环境变量与 `_ext` 相对路径 | 包装 conf 加载失败 | 包装 conf 中先 `os.chdir(upstream/docs)` 再 exec 上游 conf，随后覆盖 locale_dirs/language/html_context |
| 全局 Sphinx 9.1 与上游锁定 8.2.3 冲突 | 构建结果不一致 | 强制 venv + `requirements/docs.txt` |
| Windows 缺 gettext CLI | PO/MO 编译失败 | README 写明 scoop/ apt / brew 安装与验证 |
| 上游 stable 可能对应其它 ref | “最新提交”语义偏差 | `.gitmodules` branch 可切换；标记始终取自 submodule HEAD |
| 154 页 PO 翻译质量不一 | 术语漂移 | glossary + 分批验收 + `sphinx-intl stat` 门禁 |
| RTD submodule 未拉取 | 构建缺源 | `.readthedocs.yaml` 设 `submodules.include: all` |

## 12. 阶段里程碑与验收清单

1. M0 计划确认（本轮）：`docs/translation_plan.md` + `docs/decision_log.md`。
2. M1 脚手架：git init、submodule、conf.py 包装、脚本、README 依赖章节。
3. M2 B1–B7 翻译：每批 `sphinx-intl stat` 通过。
4. M3 本地预览与全量验收：第 8 节五项全绿。
5. M4 远端：gh 创建 `jxsword/readthedocs-zh-docs` 并推送。
6. M5 RTD 上线：导入仓库、构建成功、页脚标记显示正确 sha/时间。

## 附录 A：已核实的参考链接

- 官方中文目标文档站：<https://docs.readthedocs.com/platform/stable/>（200）
- 上游源码仓库：<https://github.com/readthedocs/readthedocs.org>（200）
- RTD 配置 v2 参考：<https://docs.readthedocs.com/platform/stable/config-file/v2.html>（200）
- sphinx-intl 文档：<https://sphinx-intl.readthedocs.io/en/master/>（200）
- upstream 依赖锁定文件：`requirements/docs.txt`（经 GitHub API 实测读取）
