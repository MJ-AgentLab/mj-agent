---
type: plan
summary: 按 Issue 605 调整 MJ Agent Site 显示名称与稳定英文 slug，并记录文档核验和 PR 交付
owner: ranzuozhou
created: 2026-10-29
updated: 2026-10-29
state: active
track: engineering-workflow
---

# [PLAN] Site 命名规则调整

## 接受基线

- 来源：[Issue #605](https://github.com/MJ-AgentLab/mj-agent/issues/605) 与 Owner 本会话五项修正要求；Owner 已确认 `MJ Agemt` 为笔误，统一使用 `MJ Agent`。
- AC-1：项目显示名 `MJ Agent`；后台名 `MJ Agent｜用途或主题`；浏览器标题 `用途或主题｜MJ Agent`；主标题直接说明用途或主题，不强制冒号。
- AC-2：新 slug 采用 `mj-agent-` 前缀加稳定英文用途，不要求拆成两个语义部分；单段后缀与多词后缀均可，字符限制及语义核对继续适用。
- AC-3：正文、示例、自检、版本日期、索引一致，保留既有身份及地址复用、平台值回读和维护核验要求。
- AC-4：独立 worktree 完成提交，以 `develop` 为显式 base 创建 PR，提供适用本地验证及独立核验结果。
- 排除：线上 Site 更名、slug 迁移、发布；runtime、业务数据、权限和 CI 门禁变更。

## 执行授权

- Owner 已授权建立 Issue、worktree、执行修正及提交 PR；包含必要的文档编辑、离线检查、暂存、commit、普通 push 与 PR 创建。
- 仓库：`MJ-AgentLab/mj-agent`；分支/worktree：`documentation/605-site-naming-alignment`；比较基线：`develop`，启动 SHA `ec6ded0138b0d7205132404eb083899dd05a881f`。
- 环境：本地 Windows，日期 Asia/Taipei 2026-10-29；网络副作用限定本任务 Issue、具名分支和 PR；不执行 merge、删除、权限变更、容器生命周期或 live probe。
- GitHub push/PR 使用既有受控单仓 App 后台，秘密仅由后台处理，模型不打开、打印或复制凭据；不新建 App 或调整个人配置。
- Owner 在发布范围澄清中明确决定“执行双推”：Gitee → GitHub。Gitee 使用正常 Git 凭据机制，GitHub 使用指定受控 App；模型不读取或输出任何凭据，不改持久配置。两端实际 SHA 分别回读，不将技术可用性作为授权。
- 任何授权撤销、实质 scope/权限变化或技术拒绝，仅暂停受影响动作；保留原错，不换身份或路线绕过。Owner 对规则的决定与对实际成果版本的最终接受分开记录。

## 任务与依赖

1. Issue → 基于 develop 创建独立 worktree → 更新规范及索引（AC-1～AC-3）。
2. 文档与格式正负例检查 → 独立 Agent 读取真实差异并复现（AC-1～AC-3）。
3. 自检 → 暂存本任务三个文件并 commit → 正常 App push → 创建单 PR `documentation/605-site-naming-alignment` → `develop`（AC-4）。

| 对象 | 决策 | 理由 |
| --- | --- | --- |
| Site 命名 STANDARD | update | v1.1 修订已确认的名称及 slug 结构，保持原路径 |
| docs/INDEX.md | update | 显示名、版本和摘要同步 |
| 本 Plan | create | 保留接受基线、授权、核验及交付检查点 |
| AGENTS.md | none | 已有规范链接仍有效，不复制正文规则 |
| runtime / ADR / capability / CHANGELOG | none | 无实现、契约或产品运行行为变化 |

## 验证与验收包

- 本地验证：`scripts/check_frontmatter.py`、`scripts/check_wikilinks.py`、`git diff --check`；读取实际 exit 与报告。
- 文本反扫覆盖 docs、根入口、runtime skills/prompts，区分现行规则与冻结历史；正负例核对实际 slug 正则，另核修改文档 Markdown 链接与章节锚。
- BDD/TDD：NONE，纯文档规则调整，不新增实现镜像测试；pytest、ruff、mypy 不适用，不以静态检查声称线上行为通过。
- 独立核验：从本节 AC 建立预期，读取实际 worktree/diff 并复现适用检查；共享工作区由执行者独占修改，核验者只读。继承同模型/effort，不变更权限。
- 仓外核验记录：`D:/workspace/10-software-project/projects/mj-agent-delivery-evidence/site-naming-605/`；绑定启动 SHA 与本次差异，最终提交与 PR metadata 另行回读。
- 软件规则核验、GitHub CI、仓库审核、集成、交付和 Owner 接受分别记录；本任务不包含线上 Site 修改或实测。

## 检查点与完成

- 已完成：Issue #605；独立 worktree 建立；规范及索引修正；Owner 明确双推；App daily audit 返回 EXECUTOR_VERIFIED、token_revocation CONFIRMED。
- 本地验证：frontmatter 158 canonical 文档通过（exit 0）；wikilinks 严格模式零 archive-ref/根文件未解析目标（exit 0）；修改文档的普通相对链接与目录锚单独核对通过；实际 slug 正则 4 个正例与 9 个负例符合预期（exit 0）；`git diff --check` 通过。
- 独立核验：Agent `site_naming_review` 从 AC 读真实三文件、建立期望并复现 46 项只读检查，AC-1～AC-3 通过，无 scope drift；仓外 `independent-review.json` 绑定实际输入摘要。AC-4 的 commit/push/PR 在执行后单列核对。
- AI 自检：三个文件均在授权范围；规范路径与 AGENTS 入口引用不变，索引同步；不涉及 rename/move、SQL、DDD、runtime skills/prompts 或 catalog 改动，5a-d 无额外同步对象。12 项提交前检查的适用项已核，无秘密/调试残留；BDD/TDD、业务数据核验、system.md/EVAL、CHANGELOG 产品行为条目均不适用。A1-A6 适用项通过；A7-A11、A12-A14 对应资产未改，不以 N/A 计运行 PASS。OB1 长度约 195 行略低于技能建议的 200 行，仅非阻塞观察；其余内容边界、摘要、时态和一致性已审阅。
- 进行中：commit、双推与 PR 创建准备；校验脚本复用 develop 的既有 Python 3.13 环境，不安装依赖或读取 .env。
- 未执行：commit、push、PR 创建；合并及 Owner 最终接受不在已完成范围。
- 计划保持 active；仅在 AC 满足、成果可用且 Owner 明确接受实际版本后改为 completed。重入先核对 Git/平台状态，已成功动作不重复。
