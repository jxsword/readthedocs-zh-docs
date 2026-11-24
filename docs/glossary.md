# 中文翻译术语表

本表约束 `locale/zh_CN/LC_MESSAGES/*.po` 的全部译文。新增术语时先补本表，再翻译条目。

## 1. 不译内容（硬性规则）

| 类别 | 示例 | 处理方式 |
|---|---|---|
| 产品 / 项目专名 | Read the Docs、Sphinx、MkDocs、Jupyter、Git、GitHub、GitLab、Bitbucket、API、Webhook、Docker、Python | 原文保留 |
| 代码与内联代码 | ``.. code-block:: python``、``:doc:``、``:ref:``、``conf.py`` | 保留反引号内容与 RST 结构，仅译其外文本 |
| 命令与参数 | ``git clone``、``sphinx-build``、``--keep-going`` | 不译 |
| 文件路径与 URL | ``docs/user/index.rst``、``https://docs.readthedocs.com/`` | 不译 |
| 配置键与环境变量 | ``version: 2``、``formats:``、``READTHEDOCS`` | 不译 |
| gettext 占位符 | ``%(name)s``、``{}``、``{var}``、``|org_brand|`` | 原样保留，位置可依中文语序调整 |

## 2. 通用术语对照

| 英文 | 建议中文 | 备注 |
|---|---|---|
| project | 项目 | 指 RTD 上的文档项目 |
| build | 构建 | 动词用“构建” |
| version | 版本 | |
| documentation | 文档 | |
| theme | 主题 | |
| extension | 扩展 | Sphinx 扩展 |
| repository | 仓库 | |
| config file | 配置文件 | 具体文件名不译 |
| automation rule | 自动化规则 | |
| search analytics | 搜索分析 | |
| hosting | 托管 | |
| integration | 集成 | |
| add-on / addon | Addon | RTD 功能名，保留英文 |
| custom domain | 自定义域名 | |
| environment variable | 环境变量 | 变量名不译 |
| pull request | Pull Request | 保留英文 |
| issue | Issue | 保留英文 |
| search index | 搜索索引 | |
| linter | Linter | 工具类别名，保留英文 |

## 3. 风格约定

- 使用简体中文，标点采用中文全角标点（代码块内除外）。
- 句子中的英文专名与中文之间不加空格，例如“使用 Sphinx 构建”。
- 标题首字母不需大写；英文标题仅译文本，保留 RST 标题修饰。
- 保留上游的 `.. note::` / `.. warning::` / `.. tip::` 指令与 `:doc:` / `:ref:` 角色结构。
