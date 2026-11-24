# 决策记录

## DR-001 2026-11-24 翻译范围限定为 docs/user/ [状态:生效]

- 背景：`docs.readthedocs.com/platform/stable` 的 “Edit on GitHub” 指向上游 `readthedocs/readthedocs.org` 的 `docs/user/index.rst`；该目录约 154 个 `.rst`，即线上 stable 文档的实际源。
- 选项与权衡：
  - A 仅 `docs/user/`：与线上站点 1:1 对齐，增量 diff 集中；需核对少量跨目录 include。（采纳）
  - B `docs/` 全目录：最彻底；约 1434 文件，翻译与冲突面扩大数倍，且包含不进入该站点的 dev 资料。（弃用：范围溢出）
  - C 仅导航可见页：见效快；不满足“全量”，后续补页需重做流程。（弃用：不完整）
- 结论：翻译范围 = 上游 `docs/user/` 全量页面，不含 `docs/dev/`、`_ext/`、`_static/` 等。
- 理由：与用户指定的线上文档边界完全一致，并将上游更新同步冲突限制在单一目录。
- 影响：同步脚本、提交标记注入、RTD 构建与本地预览均只针对 `docs/user/`。
- 时间/会话：2026-11-24 14:10 GMT+8，WorkBuddy 会话。

## DR-002 2026-11-24 翻译载体采用 sphinx-intl + PO [状态:生效]

- 背景：上游 154 个 `.rst` 需与译文分离并支持增量同步；已按“先找轮子”核实 sphinx-intl / po4a / Weblate 三个候选（官网、文档、源码 URL 均实测 200）。
- 选项与权衡：
  - A sphinx-intl + PO：源文零改动，`sphinx-intl update` 自动增量，RTD 原生中文构建；需补 sphinx-intl/gettext 依赖。（采纳）
  - B 镜像 `.rst` 原位翻译：预览直观；上游更新需三方合并，154 文件冲突面大。（弃用：增量成本高）
  - C MyST 转 Markdown：diff 友好；RST 指令/角色转换有损，需长期维护转换层。（弃用：偏离上游源）
- 结论：译文存放 `locale/zh_CN/LC_MESSAGES/*.po`；同步流程为 Sphinx gettext builder + `sphinx-intl update`。
- 理由：唯一同时满足“不改动上游源、自动增量刷新、RTD 原生中文构建”的路径。
- 影响：README.md 需详述本机依赖安装部署；构建与同步脚本围绕 pot/po 设计。
- 时间/会话：2026-11-24，WorkBuddy 会话。

## DR-003 2026-11-24 上游版本锚定采用 git submodule [状态:生效]

- 背景：需在本地构建时动态生成“基于上游提交 id/时间”的标记，且生成后冻结，仅下次上游更新才变化。
- 选项与权衡：
  - S1 git submodule 固定上游 commit：id/时间由 git 原生提供，可追溯。（采纳）
  - S2 vendor 快照 + `UPSTREAM_REVISION`：结构简单但 id/时间靠脚本写入，易与源码错位。（弃用）
  - S3 构建时实时拉 upstream HEAD：始终最新但违反“生成后不再变动”，构建不可复现。（弃用）
- 结论：以 `upstream/` submodule 的 HEAD 作为唯一版本锚点；构建脚本读取其 commit id 与提交时间并注入页面。
- 理由：避免硬编码，精确满足“构建时动态读取、产物冻结、上游更新才变化”。
- 影响：`.gitmodules` 与 RTD `.readthedocs.yaml` 需开启 submodules；同步流程为 bump submodule + `sphinx-intl update`。
- 时间/会话：2026-11-24，WorkBuddy 会话。

## DR-004 2026-11-24 目标仓库定为 jxsword/readthedocs-zh-docs，远端动作后置 [状态:生效]

- 背景：gh 已登录 `jxsword`（具备 repo scope），`jxsword/readthedocs-zh-docs` 目前不存在，本地尚未 git init。
- 选项与权衡：
  - R1 `jxsword/readthedocs-zh-docs`，本地全量翻译与预览验收后再创建推送：同名、外部动作后置。（采纳）
  - R2 其他 owner/仓库名：可适配组织托管，但需用户指定，计划 URL 需重做。（弃用：无此需求）
  - R3 仅本地初始化不推送：最保守，但不满足“用 gh 创建同名仓库推送”。（弃用）
- 结论：本地验收通过后执行 `gh repo create jxsword/readthedocs-zh-docs --public --source=. --remote=origin --push`。
- 理由：与工作区目录同名，且把不可逆的远端创建动作放在本地质量门槛之后。
- 影响：README、RTD 导入路径均使用该仓库 URL；gh 命令列在流程末段而非本阶段。
- 时间/会话：2026-11-24，WorkBuddy 会话。

## DR-005 2026-11-24 本轮交付物限定为计划文档 [状态:生效]

- 背景：用户原始诉求为“制定翻译计划”，同时描述了后续“翻译→预览→推送”的完整流程，需界定本轮边界。
- 选项与权衡：
  - P1 仅计划文档：快速产出可审阅方案，不产生半成品。（采纳）
  - P2 计划 + 脚手架：目录与脚本一次就位，但本轮会初始化仓库且仍无译文。（弃用：本轮不需要）
  - P3 计划 + 脚手架 + 立即翻译：一步到位，但 154 页翻译难以即时审阅且资源消耗大。（弃用）
- 结论：本轮只写 `docs/translation_plan.md` 与决策日志，不执行 `git init`、不拉取 submodule、不翻译正文。
- 理由：符合“先方案、后执行”的协作习惯，先固化决策再分批实施。
- 影响：后续阶段按本计划第 12 节里程碑推进。
- 时间/会话：2026-11-24，WorkBuddy 会话。
