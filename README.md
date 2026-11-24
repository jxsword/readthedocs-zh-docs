# Read the Docs 用户文档中文翻译

将 [`readthedocs/readthedocs.org`](https://github.com/readthedocs/readthedocs.org) 的 `docs/user/`（与 <https://docs.readthedocs.com/platform/stable/> 同源）全量译为中文，并通过 Read the Docs 托管上线：**<https://readthedocs-zh-docs.readthedocs.io>**

**当前状态**：B1–B7 全部批次完成（152 个 PO，10832 条 msgid，0 untranslated / 0 fuzzy），已上线 RTD。

**核心原则**

- 上游 `.rst` 零改动：译文只存于 `locale/zh_CN/LC_MESSAGES/*.po`，通过 `sphinx-intl` 注入渲染。
- 版本锚定：`upstream/` 是固定 commit 的 git submodule；页脚标记在构建时从该 submodule 的 HEAD 动态读取，HTML 生成后即冻结。
- 增量优先：上游更新只翻译新增/变更条目，已有译文自动保留，不重译。

---

## 1. 项目结构

```text
readthedocs-zh-docs/
├── .readthedocs.yaml            # RTD v2 构建配置：依赖安装、submodules、自定义构建命令
├── .gitignore                   # 忽略 .venv/、_build/、_generated/、*.mo、.workbuddy/ 等
├── .gitmodules                  # upstream -> readthedocs/readthedocs.org (branch=main)
├── conf.py                      # 包装配置：加载 upstream/docs/conf.py，覆盖 locale_dirs/language，
│                                #   并把 _generated/upstream_meta.json 注入 html_context
├── Makefile                     # gettext / update / build / preview / check / clean
├── README.md                    # 本文档
├── .workbuddy/                  # 工作区记忆与日志（不入库）
│   └── memory/                  #   当日工作日志（append-only）
├── docs/
│   ├── translation_plan.md      # 完整执行方案（架构、批次划分、质量门槛、里程碑）
│   ├── decision_log.md          # 技术决策记录（DR-001 ~ DR-005）
│   ├── glossary.md              # 术语表：不译清单 + 术语对照 + changelog 可译边界
│   └── batch_manifest.txt       # B1–B7 批次清单（check_batch.py 按此读取）
├── scripts/
│   ├── gen_upstream_meta.py     # 从 submodule HEAD 生成 _generated/upstream_meta.json
│   ├── sync_upstream.sh         # 增量同步入口：bump submodule + 重建 pot + 合并 po + 刷新元数据
│   ├── translate_po.py          # PO 批量翻译：export 导出未译条目 / import 校验并写入译文
│   ├── check_batch.py           # 按批次（B1..B7）或文件集校验全译无 fuzzy
│   ├── audit_po.py              # RST 内联标记配对审计（backtick/星号/引用）
│   ├── fix_rst_boundaries.py    # 自动补内联标记后的边界空格（防 docutils 解析错误）
│   ├── fix_named_refs.py        # 命名引用修复辅助（历史批次使用）
│   ├── fix_remaining_rst.py     # 剩余 RST 问题修复辅助（历史批次使用）
│   └── check_translation.sh     # 质量门禁：5 项检查一站式执行（make check 调用）
├── _templates/
│   └── layout.html              # 页脚与首页卡片渲染"基于上游提交"标记
├── locale/
│   └── zh_CN/LC_MESSAGES/       # *.po 译文（唯一翻译产物，152 个文件）
├── upstream/                    # readthedocs.org git submodule，只读，禁止改动
├── _build/                      # 本地构建产物（不入库）
│   ├── gettext/                 #   *.pot 中间产物
│   └── html|b7html|check/       #   HTML 构建输出
└── _generated/                  # 构建时元数据 upstream_meta.json（不入库，每次构建重新生成）
```

> `_generated/` 与 `_build/` 均在 `.gitignore` 中，提交时**不要** `git add` 这两个目录。

---

## 2. 依赖安装

### 2.1 通用前提

| 依赖 | 版本 / 说明 |
|---|---|
| Git | 2.55 或更高，需支持 submodule |
| Python | 3.13（本机实测 3.13.14），必须带 `venv` |
| GNU gettext | 提供 `msgfmt` / `msgmerge`（`sphinx-intl` 编译 `.mo` 需要） |
| GNU make | 仅使用 `Makefile` 时需要；Windows 无 make 时可直接执行等价命令 |
| gh CLI | 2.101 或更高，仅首次创建远端仓库时需要，已登录 `jxsword` |

> **重要**：本机全局 `sphinx-build` 可能与上游 `upstream/requirements/docs.txt` 锁定的 `sphinx==8.2.3` 不一致。**必须使用虚拟环境**，否则扩展可能不兼容，构建结果不可复现。

### 2.2 Windows（Git Bash + scoop）

```bash
# 1) 进入仓库（按你的实际路径调整）
cd /e/proj/readthedocs-guide/readthedocs-zh-docs

# 2) 创建并激活虚拟环境
python -m venv .venv
source .venv/Scripts/activate          # Git Bash
# PowerShell:  .venv\Scripts\Activate.ps1
# CMD:         .venv\Scripts\activate.bat

# 3) 安装上游锁定依赖（Sphinx 8.2.3 / sphinx-intl 2.4.0 等）
python -m pip install --upgrade pip
python -m pip install -r upstream/requirements/docs.txt

# 4) 安装 GNU gettext（若 msgfmt --version 不可用）
scoop install gettext
msgfmt --version
msgmerge --version

# 5) 拉取 submodule（首次或换机后）
git submodule update --init --recursive

# 6) 验证
python --version
sphinx-build --version                  # 期望 Sphinx 8.2.3
sphinx-intl --version
msgfmt --version && msgmerge --version
git -C upstream rev-parse HEAD          # 期望 40 位 sha
git -C upstream status --porcelain      # 期望空输出
```

若未安装 scoop，可改用 [GNU gettext for Windows](https://mlocati.github.io/gettext-iconv-windows/) 并将 `bin/` 加入 `PATH`。

### 2.3 Linux（Debian / Ubuntu）

```bash
cd /path/to/readthedocs-zh-docs
python3 -m venv .venv && source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r upstream/requirements/docs.txt
sudo apt-get update && sudo apt-get install -y gettext make
git submodule update --init --recursive
python --version && sphinx-build --version && sphinx-intl --version
msgfmt --version && msgmerge --version
git -C upstream rev-parse HEAD && git -C upstream status --porcelain
```

Fedora / RHEL 系：`sudo dnf install gettext make`。

### 2.4 macOS

```bash
cd /path/to/readthedocs-zh-docs
python3 -m venv .venv && source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r upstream/requirements/docs.txt
brew install gettext make
# Homebrew gettext 默认不链接到 PATH（与 macOS 自带工具冲突）：
export PATH="$(brew --prefix gettext)/bin:$PATH"   # 建议写入 ~/.zshrc
git submodule update --init --recursive
python --version && sphinx-build --version && sphinx-intl --version
msgfmt --version && msgmerge --version
git -C upstream rev-parse HEAD && git -C upstream status --porcelain
```

### 2.5 验证清单

执行以下检查，全部满足才算环境就绪：

```bash
python --version                        # Python 3.13.x
sphinx-build --version                  # sphinx-build 8.2.3（venv 内）
sphinx-intl --version                   # 可用
msgfmt --version                        # 可用
msgmerge --version                      # 可用
git -C upstream rev-parse HEAD          # 40 位 sha
git -C upstream status --porcelain      # 空
```

---

## 3. 常用命令

所有命令均在项目根目录执行，并已激活 `.venv`。

> **代理提示**：上游 `conf.py` 配置了多个 intersphinx 外部 inventory，部分站点直连受限或超时会产生 warning，使 `sphinx-build -W` 构建失败。受限环境需为构建命令设置代理：
>
> ```bash
> export HTTP_PROXY=http://127.0.0.1:10808 HTTPS_PROXY=http://127.0.0.1:10808
> ```
>
> 已有 intersphinx 缓存时（缓存于构建目录 Doctrees）通常不会重复拉取。RTD 构建环境有公网访问，无需此设置。
>
> **源目录参数**：所有 `sphinx-build` / `sphinx-autobuild` 的源目录均为 `upstream/docs`（**不是** `upstream/docs/user`）。上游 `sphinx-multiproject` 扩展会自行拼接 `PROJECT=user` 子目录，传入 `upstream/docs/user` 会被二次拼接为 `user/user`，导致 `unable to load master document`。

### 3.1 构建 / 预览 / 门禁

```bash
# 生成提交元数据（每次构建前；make build 已包含）
python scripts/gen_upstream_meta.py

# 从未翻译的 .rst 生成 .pot
make gettext

# 重建 .pot 并合并进 locale/zh_CN 的 .po（保留已有译文）
make update

# 编译 .mo 并构建中文 HTML 到 _build/html
make build

# 本地实时预览（详见 3.3 节）
make preview

# 质量门禁（5 项检查，见第 5 节）
make check
```

Windows 若没有 `make`，直接执行等价命令：

```bash
python scripts/gen_upstream_meta.py
sphinx-intl build -d locale -l zh_CN
PROJECT=user sphinx-build -b html -c . -D language=zh_CN upstream/docs _build/html
```

### 3.2 PO 批量翻译工具（增量翻译的核心工具链）

```bash
# 导出某 PO 中所有未翻译条目（自动跳过 fuzzy 与已翻译条目）→ JSON
python scripts/translate_po.py export locale/zh_CN/LC_MESSAGES/<path>.po -o /tmp/<name>.json

# 写好译文后导入（内置校验：gettext 占位符保留 + 内联标记计数 + 不可变目标比对；有 warn 会拒绝写入并退出码 1）
python scripts/translate_po.py import locale/zh_CN/LC_MESSAGES/<path>.po /tmp/<name>.zh.json

# 按批次校验（批次定义见 docs/batch_manifest.txt）
python scripts/check_batch.py B7
# 或按文件集校验
python scripts/check_batch.py --files changelog.po faq.po

# RST 标记审计（backtick / 星号 / 引用配对）
python scripts/audit_po.py

# 自动补内联标记后的边界空格（防 "Inline ... start-string without end-string"）
python scripts/fix_rst_boundaries.py
```

**export/import 注意事项**：

- 导出的 JSON 是 `{"id": <msgid>, "loc": <位置>}` 列表；导入的 JSON 是 **msgid → 译文的扁平对象**。
- **键必须唯一**：重复 msgid 键在 JSON 对象中会互相覆盖，导致部分条目漏译。
- import 校验失败（token mismatch / markup count mismatch）时，对应条目不会被写入；修正译文后重新执行 import 即可，已成功的条目会自动跳过。
- 命名引用（`` `X`_ `` / `` `X`__ ``）与 `:role:`目标`` 的**目标部分不可变**；显示文本可译时必须用 `` `显示文本 <原目标>`_ `` 完整语法，且 target 逐字符一致。

### 3.3 本地预览构建产物（三种方式，已实测可行）

**方式一：`make preview`（推荐，实时预览）**

```bash
source .venv/Scripts/activate        # Git Bash
make preview
```

浏览器打开 **http://127.0.0.1:8000**。该命令先执行一次完整构建（提交元数据 → 编译 `.mo` → HTML），再启动 `sphinx-autobuild` 监听——**修改 `.po` 译文后自动增量重建并刷新浏览器**，适合边译边看。

Windows 无 `make` 时的等价命令：

```bash
python scripts/gen_upstream_meta.py
sphinx-intl build -d locale -l zh_CN
sphinx-autobuild -c . -D language=zh_CN upstream/docs _build/html --host 127.0.0.1 --port 8000
```

**方式二：仅构建，直接打开静态文件**

```bash
make build          # 产物在 _build/html/
```

构建完成后用浏览器直接打开本地 HTML 文件（如 `_build/html/index.html`）。站点是纯静态页，`file://` 协议可正常浏览，但**搜索功能**（依赖同源加载 `searchindex.js`）在 `file://` 下可能受限，需要完整功能时用方式一或方式三。

**方式三：查看已有构建产物（无需重新构建）**

历史构建产物保留在 `_build/` 下的各输出目录（如 B7 验收用的 `_build/b7html/index.html`、门禁检查的 `_build/check/html/`），直接用浏览器打开即可快速核对译文效果。

**巡检要点**（对应质量门槛第 5 项）：

- 中文标题与侧边栏渲染正常；
- 交叉引用（`:doc:` / `:ref:`）跳转不 404；
- 代码块、提示框（note/warning/tip）结构完整；
- 页脚显示「中文翻译基于上游文档提交 `<short-sha>`（`<commit-time>`）」且链接正确；
- 搜索页可搜索中文内容。

> **提示**：构建时若 intersphinx 拉取超时报 warning，先设置代理再构建（见第 3 节开头的代理提示）。

---

## 4. 翻译工作流

### 4.1 术语与翻译规范

术语以 `docs/glossary.md` 为准，核心规则：

| 类别 | 处理 |
|---|---|
| 产品/项目专名 | Read the Docs、Sphinx、MkDocs、Git、GitHub、API、Webhook 等保留英文 |
| 代码与内联代码 | `.. code-block::`、`:doc:`、``conf.py`` 等保留结构，仅译其外文本 |
| 命令与参数、路径与 URL、配置键与环境变量 | 不译 |
| gettext 占位符 | `%(name)s`、`{var}`、`|org_brand|` 原样保留，位置可依中文语序调整 |
| RST 边界 | 内联标记（`` ``X`` ``、`**X**`、`*X*`）与 `:role:`...`` 结束符后**不可紧跟中文或全角标点**，需留半角空格（`fix_rst_boundaries.py` 可兜底） |
| 命名引用 | `` `X`_ `` / `` `X`__ `` 显示文本即链接目标，原样保留 |

新增术语先补 `docs/glossary.md`，再翻译。

### 4.2 增量更新工作流（上游有新提交时）

上游仓库 `readthedocs/readthedocs.org` 的 `main` 分支更新后，按以下流程跟随翻译。**全程上游 `.rst` 零改动，唯一产物是 `.po`。**

**第 1 步：同步上游并合并翻译目录**

```bash
./scripts/sync_upstream.sh
```

脚本依次执行（约 1–3 分钟）：

1. `git submodule update --remote upstream` — 推高 submodule 到上游 `main` 最新提交；
2. `sphinx-build -b gettext -c . upstream/docs _build/gettext` — 重新生成全部 `.pot`；
3. `sphinx-intl update -d locale -p _build/gettext -l zh_CN --no-obsolete` — 合并进现有 `.po`：
   - **已有译文自动保留**（msgid 未变）；
   - **新增条目** → 空译文（untranslated）；
   - **源文变更条目** → 保留旧译文但标记 `fuzzy`（待人工复核）；
   - **上游删除的条目** → `--no-obsolete` 自动从 `.po` 清理；
4. `python scripts/gen_upstream_meta.py` — 刷新提交元数据。

**第 2 步：审查变更范围**

```bash
# 查看上游实际改了什么（确认无 breaking change / 结构性大改）
git -C upstream log --oneline HEAD@{1}..HEAD -- docs/user

# 查看受影响的 PO 与变更统计
git diff --stat locale/zh_CN/LC_MESSAGES/
```

若上游有结构性大改（页面增删、toctree 重构），先更新 `docs/batch_manifest.txt` 与 `docs/translation_plan.md` 再继续。

**第 3 步：处理 fuzzy 条目（人工复核）**

fuzzy 条目不会被 `translate_po.py export` 导出，需人工在 `.po` 中处理：

```bash
grep -rn "fuzzy" locale/zh_CN/LC_MESSAGES/ | grep -v "^.*#, fuzzy$.*previous" | less
# 或用编辑器打开受影响的 .po，搜索 "#, fuzzy"
```

对每条 fuzzy：对照源文变更决定——若旧译文仍适用则删除 `#, fuzzy` 行保留译文；若不适用则重写译文并删除 fuzzy 标记。

**第 4 步：导出并翻译新增条目**

```bash
# 对每个有 untranslated 条目的 PO 导出（export 天然只导出未译条目，即增量）
python scripts/translate_po.py export locale/zh_CN/LC_MESSAGES/<path>.po -o /tmp/<name>.json
```

翻译导出的 JSON（msgid → 中文译文），写入 `<name>.zh.json` 后导入。翻译规范见 4.1 节。

**第 5 步：导入与校验（逐文件）**

```bash
# 导入（有 warn 立即修正译文后重导）
python scripts/translate_po.py import locale/zh_CN/LC_MESSAGES/<path>.po /tmp/<name>.zh.json

# 校验受影响的批次 / 文件：0 untranslated / 0 fuzzy
python scripts/check_batch.py --files <path>.po

# 标记审计与边界修复
python scripts/fix_rst_boundaries.py
python scripts/audit_po.py
```

**第 6 步：全量构建验证**

```bash
make check    # 5 项门禁：译文完整 / 构建无错 / 标记一致 / 上游零改动 / 人工巡检提醒
```

要求 `sphinx-build -W --keep-going` **0 译文相关 warning**（上游既有的 intersphinx 超时、未知交叉引用 warning 不算译文缺陷）。

**第 7 步：提交并推送**

```bash
git add upstream locale
git commit -m "chore: sync upstream <sha> + i18n(zh_CN): incremental translation (<N> msgids)"
git push
```

推送后 RTD 通过 webhook **自动触发构建**（约 3–5 分钟），无需手动操作。

**第 8 步：验证线上效果**

打开 <https://readthedocs-zh-docs.readthedocs.io>：

1. 新翻译的页面内容已中文渲染；
2. 页脚「中文翻译基于上游文档提交 `<short-sha>`（`<commit-time>`）」已更新为新的 submodule HEAD；
3. 链接指向 `https://github.com/readthedocs/readthedocs.org/commit/<full-sha>`。

**第 9 步：记录工作日志（可选但建议）**

在 `.workbuddy/memory/<当日日期>.md` 追加本次增量同步的范围、条目数与遇到的问题（append-only）。

### 4.3 增量工作流速查（TL;DR）

```bash
./scripts/sync_upstream.sh                                       # 1. 同步
git diff --stat locale/                                          # 2. 查变更
# 3. 人工复核 .po 中的 fuzzy 条目
python scripts/translate_po.py export <po> -o /tmp/a.json        # 4. 导出未译
# 5. 翻译 → a.zh.json
python scripts/translate_po.py import <po> /tmp/a.zh.json        # 6. 导入
python scripts/check_batch.py --files <po>                       # 7. 校验
python scripts/fix_rst_boundaries.py && python scripts/audit_po.py
make check                                                       # 8. 门禁
git add upstream locale && git commit && git push                # 9. 推送（RTD 自动构建）
```

---

## 5. 质量门槛

| 门槛 | 命令 / 条件 |
|---|---|
| 单批译文完整 | `python scripts/check_batch.py <批次或 --files ...>` 退出码 0（untranslated=0 且 fuzzy=0） |
| 全站译文完整 | `sphinx-intl stat -d locale -l zh_CN` 退出码 0，无 fuzzy |
| 构建无错 | `sphinx-build -b html -W --keep-going -c . -D language=zh_CN upstream/docs <输出目录>` 0 error；0 译文相关 warning |
| 标记正确 | 页面页脚 sha / 时间 == `git -C upstream rev-parse HEAD` 及其 committer date |
| 源文零改动 | `git -C upstream status --porcelain` 输出为空 |
| 本地预览 | 人工巡检代表页：中文标题、侧边栏、交叉引用、代码块、页脚标记、搜索页 |

`make check`（`scripts/check_translation.sh`）自动执行前 4 项，第 5 项为人工确认。

---

## 6. 提交标记机制

`python scripts/gen_upstream_meta.py` 读取 `upstream/` 的 `git rev-parse HEAD` 与 `git log -1 --format=%cI`，写入 `_generated/upstream_meta.json`；根目录 `conf.py` 将其注入 `html_context`，`_templates/layout.html` 在页脚与首页卡片渲染：

> 中文翻译基于上游文档提交 `<short-sha>`（`<commit-time>`）

链接指向 `https://github.com/readthedocs/readthedocs.org/commit/<full-sha>`。只有执行 `sync_upstream.sh` 推高 submodule 并重新构建后，标记才会变化。HTML 生成后标记即冻结为静态值。

---

## 7. Read the Docs 托管与故障排查

**配置**：仓库根 `.readthedocs.yaml`（v2），关键点：

```yaml
build:
  os: ubuntu-24.04
  tools:
    python: "3.13"
  jobs:
    pre_build:
      - python -m pip install --quiet -r upstream/requirements/docs.txt   # 显式安装，不依赖 python.install 阶段
      - python scripts/gen_upstream_meta.py
      - python -m sphinx_intl build -d locale -l zh_CN                    # python -m 调用，避免 PATH 问题
    build:
      html:
        - python -m sphinx -b html -c . -D language=zh_CN upstream/docs $READTHEDOCS_OUTPUT/html
submodules:
  include: all
python:
  install:
    - requirements: upstream/requirements/docs.txt
```

**已踩过的坑（修改构建配置前必读）**：

1. **依赖必须显式安装**：RTD 的 `python.install` 阶段实测可能未生效，导致 `sphinx-intl: not found`（Exit 127）。pre_build 第一步显式 `pip install`（幂等）。
2. **用 `python -m` 调用**：`sphinx-intl` → `python -m sphinx_intl`；`sphinx-build` → `python -m sphinx`，绕开 venv bin 目录 PATH 不确定性（两个模块入口已本地验证可用）。
3. **源目录必须是 `upstream/docs`**：传 `upstream/docs/user` 会被 sphinx-multiproject 二次拼接为 `user/user`，构建报 `unable to load master document`。
4. **`build.jobs.build` 必须是字典**（按构建格式分键，如 `html:` 下的命令列表），写成纯列表会报 `Expected a dictionary, got type list`。修改 `.readthedocs.yaml` 后先本地 `yaml.safe_load` 校验 `build.jobs` 结构再提交。
5. **`_generated/`、`_build/` 不要 `git add`**（在 `.gitignore` 中）。

**日常操作**：push 到 `main` 即自动构建；RTD 仪表盘 <https://dashboard.readthedocs.org> 可手动 Rebuild、查看构建日志。

---

## 8. 决策与方案文档

| 文档 | 内容 |
|---|---|
| `docs/translation_plan.md` | 完整执行方案：架构、数据流、批次划分（6.3 节）、质量门槛、里程碑 |
| `docs/decision_log.md` | 技术决策 DR-001 ~ DR-005（范围 / 载体 / 锚定 / 仓库 / 交付物）；新增决策从 DR-006 起 |
| `docs/glossary.md` | 术语表：不译清单、术语对照、changelog 可译边界、RST 边界实测约定 |
| `docs/batch_manifest.txt` | B1–B7 批次 ↔ PO 文件清单（`check_batch.py` 按此读取） |
