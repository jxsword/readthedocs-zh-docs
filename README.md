# Read the Docs 用户文档中文翻译

将 [`readthedocs/readthedocs.org`](https://github.com/readthedocs/readthedocs.org) 的 `docs/user/`（与 <https://docs.readthedocs.com/platform/stable/> 同源，约 154 个 `.rst` + 1 个 `.md`）全量译为中文。

**核心原则**

- 上游 `.rst` 零改动：译文只存于 `locale/zh_CN/LC_MESSAGES/*.po`，通过 `sphinx-intl` 注入。
- 版本锚定：`upstream/` 是固定 commit 的 git submodule；页脚标记在构建时从该 submodule 的 HEAD 动态读取，HTML 生成后即冻结。
- 远端后置：本地全量翻译与预览验收通过后，才用 `gh` 创建并推送 `jxsword/readthedocs-zh-docs`，由 Read the Docs 托管（非 GitHub Pages）。

---

## 1. 目录结构

```text
conf.py                       包装配置：加载 upstream/docs/conf.py，覆盖译文目录与提交标记
Makefile                      gettext / update / build / preview / check
scripts/
  gen_upstream_meta.py        从 submodule HEAD 生成 _generated/upstream_meta.json
  sync_upstream.sh            bump submodule + 重建 pot + 合并 po
  check_translation.sh        质量门禁
_templates/layout.html        页脚与首页的“基于上游提交”标记
docs/
  translation_plan.md         完整执行方案
  decision_log.md             技术决策记录（DR-001 起）
  glossary.md                 术语表
locale/zh_CN/LC_MESSAGES/     *.po 译文（唯一翻译产物）
upstream/                     readthedocs.org submodule，只读
_build/                       本地构建产物（不入库）
_generated/                   构建时元数据（不入库）
```

---

## 2. 依赖安装

### 2.1 通用前提

| 依赖 | 版本 / 说明 |
|---|---|
| Git | 2.55 或更高，需支持 submodule |
| Python | 3.13（本机实测 3.13.14），必须带 `venv` |
| GNU gettext | 提供 `msgfmt` / `msgmerge`（`sphinx-intl` 编译 `.mo` 需要） |
| GNU make | 仅使用 `Makefile` 时需要；也可直接调用等价脚本 |
| gh CLI | 2.101 或更高，**仅 M4 远端阶段需要**，本机已登录 `jxsword` |

> **重要**：本机全局 `sphinx-build` 为 9.1.0，而上游 `upstream/requirements/docs.txt` 锁定 `sphinx==8.2.3`。**必须使用虚拟环境**，否则扩展可能不兼容，构建结果不可复现。

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

若未安装 scoop，可改用 [GNU gettext for Windows](https://mlocati.github.io/gettext-iconv-windows/) 并将 `bin/` 加入 `PATH`；macOS/Linux 见下。

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
gh auth status                          # 仅远端阶段：显示 jxsword
```

---

## 3. 常用命令

所有命令均在项目根目录执行，并已激活 `.venv`。

> **代理提示**：上游 `conf.py` 配置了 17 个 intersphinx 外部 inventory，其中部分站点（如 `rst-to-myst.readthedocs.io`）超时会产生 warning，使 `sphinx-build -W` 构建失败。直连受限的环境需为构建命令设置代理，例如：
>
> ```bash
> export HTTP_PROXY=http://127.0.0.1:10808 HTTPS_PROXY=http://127.0.0.1:10808
> ```
>
> 已有 intersphinx 缓存时（`intersphinx_cache_limit = 14`，缓存于构建目录Doctrees）通常不会重复拉取。RTD 构建环境有公网访问，无需此设置。
>
> **源目录参数**：所有 `sphinx-build` / `sphinx-autobuild` 的源目录均为 `upstream/docs`（非 `upstream/docs/user`）。上游 `sphinx-multiproject` 扩展会自行拼接 `PROJECT=user` 子目录。

```bash
# 生成提交元数据（每次构建前）
python scripts/gen_upstream_meta.py

# 从未翻译的 .rst 生成 .pot
make gettext

# 重建 .pot 并合并进 locale/zh_CN 的 .po（保留已有译文）
make update
# 等价脚本（会同时 bump submodule）：
./scripts/sync_upstream.sh

# 编译 .mo 并构建中文 HTML 到 _build/html
make build

# 本地实时预览 http://127.0.0.1:8000
make preview

# 质量门禁（译文完整 / 构建无错 / 标记一致 / 上游零改动）
make check
```

Windows 若没有 `make`，直接执行 `Makefile` 中的命令即可，例如：

```bash
python scripts/gen_upstream_meta.py
sphinx-intl build -d locale -l zh_CN
PROJECT=user sphinx-build -b html -c . -D language=zh_CN upstream/docs _build/html
```

---

## 4. 翻译工作流

1. `./scripts/sync_upstream.sh`：bump submodule → 生成 pot → `sphinx-intl update` 合并 po。
2. 按 `docs/translation_plan.md` 第 6.3 节的 B1–B7 批次翻译 `locale/zh_CN/LC_MESSAGES/*.po`。
3. 术语以 `docs/glossary.md` 为准：专名、代码/内联代码、命令、路径、配置键不译；RST 指令/角色结构与 gettext 占位符保留。
4. 每批执行 `sphinx-intl stat -d locale -l zh_CN` 与本地预览；全量完成后运行 `make check`。
5. 本地全部通过后才执行远端创建与推送（见 `docs/translation_plan.md` 第 10 节）。

---

## 5. 质量门槛

| 门槛 | 命令 / 条件 |
|---|---|
| 译文完整 | `sphinx-intl stat -d locale -l zh_CN` 退出码 0，无 fuzzy |
| 构建无错 | `sphinx-build -b html -W --keep-going ...` 0 error |
| 标记正确 | 页面页脚 sha / 时间 == `git -C upstream rev-parse HEAD` 及其 committer date |
| 源文零改动 | `git -C upstream status --porcelain` 输出为空 |
| 本地预览 | 人工巡检各批次代表页，无乱码、无断裂链接 |

---

## 6. 提交标记机制

`python scripts/gen_upstream_meta.py` 读取 `upstream/` 的 `git rev-parse HEAD` 与 `git log -1 --format=%cI`，写入 `_generated/upstream_meta.json`；根目录 `conf.py` 将其注入 `html_context`，`_templates/layout.html` 在页脚与首页卡片渲染：

> 中文翻译基于上游文档提交 `<short-sha>`（`<commit-time>`）

链接指向 `https://github.com/readthedocs/readthedocs.org/commit/<full-sha>`。只有执行 `sync_upstream.sh` 推高 submodule 并重新构建后，标记才会变化。

---

## 7. 决策与方案

- `docs/translation_plan.md`：完整执行方案与里程碑。
- `docs/decision_log.md`：DR-001 ~ DR-005 为已确认决策；新增决策从 DR-006 起。
- `docs/glossary.md`：翻译术语表。

线上站点使用 Read the Docs 托管，配置见仓库根 `.readthedocs.yaml`（v2，开启 submodules）。
