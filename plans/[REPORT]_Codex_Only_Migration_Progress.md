---
type: report
summary: "Codex迁移累计记录：Linux本地离线矩阵及clone/linked补验通过，修复一行原生文档资源示例；L5与实际CI未验收，P5仍受阻"
owner: ranzuozhou
created: 2026-09-18
updated: 2026-09-20
state: draft
track: engineering-workflow
---

# Codex 独立开发迁移累计进度

## 1. 当前结论与授权记录

**最新状态见 §23：Docker已恢复可用，P4 Linux本地矩阵44条命令及拓扑38条命令均exit0；六带1051 passed、40 skipped，另19 subtests。修复普通原生文档技能一行占位引用，全部当前身份已绑定。L5真实宿主与实际CI仍缺执行证据，P4技术迁移未验收，P5继续受阻。**

当前Linux补验见§23，历史Docker诊断见§22，此前环境准备见§21，P4修复复验见§20，此前补验见§19，P5前置记录见§18，P4此前记录见§17，P3人工应用/格式最终状态见§15–§16。§13、两个历史§14及§15的“尚未应用/格式失败”等按各自时点保留；本轮不重编号历史章节。§2–9为P0快照，§11–§12保留P1/P2记录。Owner必停、真实秘密边界及工程师独立审阅trust的约束继续有效；实际人工路线已走通，不再把整个正式切换组标为BLOCKED_EXECUTION_ROUTE。

Owner 在 P0 后指示“原有项目级 MCP 迁移后仍然为项目级 MCP，其他来源的 MCP 不做迁移，遗弃即可。继续”。本轮按相邻的 P1 单阶段继续，限定 §4.3 候选及最小共用测试拆分，不将“继续”扩展为 P2–P6。其他来源“不迁移/遗弃”指不导入候选，不删除或卸载用户级、插件、连接器的原有资产。Owner 随后选择：**需 Owner 批准的动作保留硬阻断，人工审阅后另行处理执行路径**；无审批 receipt 或自动放行实现。P1 当前证据见 §11；§2–9 为 P0 基线快照，其中“本轮/尚未开始”按该时点理解。

本轮依据 [迁移计划](<./[PLAN]_Codex_Only_Development_Migration.md>) §2、§4.2、§5–§7，仅执行基线核查、资产登记和草案编写。主任务为当前 Codex 任务“执行 mj-agent Codex 独立开发迁移 P0”；没有迁移 issue 编号，不使用 #499/#552 代替本任务编号。

| 授权/约束 | 本轮处理 |
|---|---|
| Owner 本轮请求执行 P0 | 创建计划副本、资产表、累计报告；ADR 正文仅供审阅 |
| Owner 对计划位置的答复 | “原样复制到当前迁移工作树（推荐）”；develop 输入保持不变 |
| 不创建 issue/分支/提交/推送/PR | 全部遵守；只读查询远端、规则判定不是执行 Git 写操作 |
| 不修改正式政策、配置、技能、契约、CI | P0 tracked diff 为空；P1 唯一 tracked 修改为投影测试中的有效离线断言拆分，正式配置等保持不变 |
| 不接续旧任务、不改其他工作树、不扩展治理 | #499/#552 仅读状态、相交 diff 和文件身份；不应用其修改 |
| P3 前仍受生成物禁令约束 | 未运行 sync/adopt、未手改 `.agents/` 或 `.codex/` |
| Skill 使用 | P0 repo-scan；P1 implement、verify、self-review、scope-drift 的适用步骤；OpenAI Docs 核对宿主机制。用户指定阶段优先，不开启技能中的提交/推送交接 |

交付集合：

1. `plans/[PLAN]_Codex_Only_Development_Migration.md`：输入的逐字节副本，不改状态或正文。
2. [资产处置表](../evidence/codex-only-migration/asset-map.csv)：P0 原有 277 行全部保留；追加 12 行 P1 成果，当前 289 行；37 个技能的 P2 迁移状态未变。
3. 本累计报告：包含 ADR 可审阅正文，不创建 `decisions/ADR-*.md`，不改 ADR/计划生命周期。
4. `.migration/codex-only/project/` 内 10 个候选文件、`tests/unit/test_offline_execution_boundary.py` 与原测试文件的拆分差异；[P1 验证记录](../evidence/codex-only-migration/p1-verification.json)。

原计划顶部和附录 B 的“尚未实施/未创建”是**2026-09-18 编写时快照**；后续进度以本报告为准。保留 `draft` 不表示撤销已取得的 P0/P1 授权，也不表示批准 P2–P6。

## 2. Git、输入及工作树基线

| 项目 | 实测值 |
|---|---|
| 当前工作树/Git 根 | `D:/workspace/10-software-project/projects/mj-agent/maintain/codex-dev-mode-migration` |
| 分支 | `maintain/codex-dev-mode-migration`，已存在，本轮未创建 |
| HEAD | `20e2f24c352cf640d9dd33234b128ca897804b99` |
| common-dir | `D:/workspace/10-software-project/projects/mj-agent/.bare` |
| git-dir | `D:/workspace/10-software-project/projects/mj-agent/.bare/worktrees/codex-dev-mode-migration` |
| 入场状态 | staged=0、unstaged=0、untracked=0；与本地 develop 同 HEAD，merge-base 差异为空 |
| origin/develop | `git ls-remote --heads origin develop maintain/codex-dev-mode-migration` 返回 develop 同上 SHA；未返回迁移远端分支 |
| 远端 | origin=GitHub `MJ-AgentLab/mj-agent`；gitee=`ranzuozhou/mj-agent`；本轮未 fetch/push |
| 输入原件 | `D:/workspace/10-software-project/projects/mj-agent/develop/plans/[PLAN]_Codex_Only_Development_Migration.md`，develop 内为未跟踪文件 |
| 输入/副本 SHA-256 | `7dfad81dcf40d8cb867c7d9051907677eac85b6cbd2c9fb856a75f86c37d3728` |
| open PR 查询 | 唯一返回 #551（dependabot，base develop）；没有本迁移、#499 或 #552 的 open implementation PR；仅代表查询时刻 |

`git worktree list --porcelain` 另列 develop、documentation/session-maintenance、maintain/499-enforcement-blocking、maintain/552-codex-approval-preflight、tmp-control-20e2f24c（detached）及 bare 容器。session-maintenance HEAD=`b2fa9dab9e1562ec365ead1f8b35c72e00daecc2`，其他列出的工作树 HEAD 与本轮基线相同。不将这些工作树作为迁移候选区，不清理、不切换、不补做其任务；未对无关工作树递归取证。

**工作树建议：沿用当前已隔离的迁移工作树及已有分支，不新建或重命名。** P1 入场重新核对 HEAD、diff、输入摘要和本表。在途内容发生变化时先报告，不能用 reset、覆盖或旧快照消除变化。

## 3. 宿主与工具实测

| 项目 | 实测结果 | 证据/限制 |
|---|---|---|
| OS | Windows NT `10.0.26200.0`，AMD64 | `[Environment]::OSVersion.VersionString` / Python platform；未推断 Windows 产品版本名称 |
| PowerShell | `7.6.5` | `$PSVersionTable.PSVersion`；后续命令用 `login=false` 避免个人 profile 的 PSReadLine 重定向警告 |
| Codex Desktop | `OpenAI.Codex 26.915.3509.0` | `Get-AppxPackage '*Codex*'` |
| 当前 Desktop 内嵌引擎 | `codex-cli 0.155.0-alpha.9` | 当前 codex 进程路径 `C:/Users/Admin/AppData/Local/OpenAI/Codex/bin/cdef5aaf3e41ab53/codex.exe`，显式 `--version` |
| 独立 CLI | `codex-cli 0.147.0` | `C:/Users/Admin/AppData/Roaming/npm/codex.cmd --version`；npm 包元数据同为 0.147.0 |
| Python | `3.13.5`，PyYAML `6.0.3` | PATH 无 python；当前工作树无 `.venv`；仅读取并调用 `../../develop/.venv/Scripts/python.exe -B`，不安装、不修改该环境 |
| Node | `v22.18.0` | `node --version`，`D:/Development/nodejs/node.exe` |
| uv | `0.11.21`，Windows x86_64 | `uv --version` |
| Git / gh | `2.53.0.windows.1` / `2.86.0` | `git --version` / `gh --version` |
| 有效会话约束 | approval=`never`，sandbox=`danger-full-access` | 当前任务提供的有效权限上下文；不读取用户配置，不由项目文件反推 |

测试平台固定为：**Windows 开发宿主/启动器 + Linux CI 的代码、文档和检查器**。CI 当前 `runs-on: ubuntu-latest`，Python 版本取 `.python-version`。P0 没有启动 Linux runner，不承诺 Linux MCP launcher 支持。P1/P4 记录实际运行时镜像/版本；不安装或升级工具来补齐本轮基线。

配置中 8 个 MCP 服务的 TOML 解析、服务名和 `env_vars` 名称已静态核对：GitHub、Playwright、Serena、memory dev/test-lan/test-wan/prod-lan/prod-wan；没有 biz×5 或 ssh-manager。5 个 memory 服务仍引用 `.claude\\scripts\\pg-server-start.cmd`。变量只登记名称：`GITHUB_PERSONAL_ACCESS_TOKEN` 和 `MJ_AGENT_PG_MEMORY_{DEV,TEST_LAN,TEST_WAN,PROD_LAN,PROD_WAN}_URL`；没有读取或输出值。

当前工具目录可见 GitHub、Playwright、Serena、memory-dev 的工具元数据；未发现其他四个 memory 服务的工具元数据。**可见不等于连接通过，缺元数据也不是已诊断的服务故障。** 本轮仅 gh 的 issue/PR 只读查询成功；没有运行项目 MCP、业务工具链、Studio、Docker、数据库或 LLM probe。工具可用性和凭据状态留作分服务验证。

所需工具承接：文件/文本读写→Codex 文件和 shell 工具；Git/gh→现有 CLI；Python/uv→现有受控离线 runner；浏览器/代码导航→可用的 Playwright/Serena 或经验证的等价工具；infra/runtime 技能中的真实服务操作继续走原审批与数据边界。技能对外部插件/姊妹仓规范的引用已登记，P2 将方法内化或明确未满足依赖；不能假定 Claude 插件可用，也不能把技能名作为 shell 命令。

官方 [Build skills](https://learn.chatgpt.com/docs/build-skills) 在本轮已打开核对；只作为机制资料入口。P1 涉及配置字段时仍须按上表的具体引擎重新核对官方资料及本机行为；本轮不宣称 hooks/trust/全部技能已实际加载。

## 4. 资产表及迁移处置

表中 `baseline` 为完整 Git SHA；`git_blob` 为该版本的文件对象；`working_sha256` 为本轮工作副本原始字节摘要。敏感配置只登记路径/已有 Git 对象元数据，不为计算摘要读取正文；秘密/个人资产的 6 个边界行不读取、不计算摘要。资产表版本为 P0-v1，最终 SHA-256：`1a04ceb9c518b44c0db37dcc004f8ec0ce08efb8ce2f31f44c8e77f01ea1a817`。`recovery` 指向基线 `SHA:path`，不是已执行的恢复。

`dependencies` 记录技能内实际出现的本地文件、同伴技能名称及外部引用；`consumers` 记录直接文本引用的文件和行号。**文本引用不等于必需调用**：反向触发、举例、历史文字、负例均需在 P2/P3 分辨；不能据此递归执行技能或扩大修改面。通配资源、概念引用、八维语义与动态调用闭合属于 P2/P4，本表不冒充运行调用图。扫描以迁移源、其直接引用与具名消费者为界，没有扩为全仓诊断。

| 族 | 源技能 | 现有入口 | P0 处置 |
|---|---:|---:|---|
| doc | 6 | 1 | 六项全部同名原生迁移，补五个入口 |
| flow | 10 | 10 | 以源流程为完整基线；去专属工具表达/翻译/route 注入 |
| git | 9 | 7 | 补 check-merge、review-pr；Git 动作及对外发布仍按授权 |
| infra | 8 | 0 | 八项全部迁移；冻结契约路径、description/body 摘要成组修订 |
| runtime（开发工作流） | 4 | 0 | 四项全部迁移；不触碰业务 runtime 正文 |
| 合计 | 37 | 18 | 13 translated + 5 byte-copy；19 项无入口仍必须迁移 |

每个源目录除 SKILL.md 外无额外资源文件；`SKILL_INDEX.md` 单列处置。37 个名称与计划附录 A、manifest、Git 跟踪源目录完全对应。既有 V4 解析器检验 37 PASS / 0 WARN / 0 FAIL；这只证明原客户端 schema/命名/description 规则。

| 资产组 | 目标与必须保留的内容 | 时机 |
|---|---|---|
| 根 + 4 个局部 CLAUDE / AGENTS | 保留架构、工具加载顺序、middleware、测试带、Compose env-file/拆卸边界、契约义务；必要内容进入对应 AGENTS/已有指南 | P3 吸收，P5 清理旧入口 |
| launcher / wrapper / setup-mcp-secrets | `scripts/mcp/`；只迁代码和变量接口，应用/MCP 凭据分离；根/子目录/空格路径/worktree 合成测试 | P1 候选，P3 切换 |
| `.codex` / `.agents` | 正式成为直接维护源；本轮仍是生成物 | P3 成组切换 |
| Git guard / codex_hook_guard | G1/G2、保护路径、最小输入/no-read、安全拒绝等断言保留；解除 typed YAML 的运行依赖 | P1/P3 |
| Stop improver | README + on-stop.ps1 skeleton 退役；不新增自动 AGENTS 写入或 receipt 平台 | P5 |
| manifest / registry / renderer / translation / fidelity / lock / adopt | 提取有效流程、安全语义后退出双工具机制；不换名建立第二套生成链 | P1–P3 / P5 |
| `_common` / 测试文件 | 普通 frontmatter/AST/discovery 等公共代码保留；混合测试逐断言拆分，不能按文件名或目录整删 | P1/P3/P5 |
| 非客户端 adapters | BDD/TDD、contract、Docker、LangChain、Prompt、Python、runtime-skill 保留原址；不全局改 adapter_coverage schema | 全程 |
| 直接消费者 | checker 扫描域、CI 注册、模板、root 文档、指南、MCP 契约、ignore/EOL 必要路径调整 | P3/P6 |
| 历史/个人/业务资产 | 保留；历史绑定基线；禁止复制秘密、覆盖其他工作树 | 全程 |

必须先拆出的安全测试已定位：`tests/unit/test_agents_sync.py:449,480` 的凭据字面量拒绝，以及 `729–1872` 的离线自动输入/环境封闭/tracked-only/插件限制/无秘密输出；`test_guard_git_workflow_hook.py` 和 `test_codex_enforcement_d1a.py` 的有效行为断言保留。`test_agents_sync.py`、`test_v2_engine.py` 在 #499 有未提交成果，后续只能按批准的最小语义承接，不能复制整文件覆盖。

直接消费者证据示例：`scripts/check_loop_section_refs.py:77,100` 当前扫描 `.claude` 且排除 `.agents`；`check_wikilinks.py`、`check_ai_context_audit.py`、`find_stale_docs.py`、`check_no_cross_repo_refs.py` 存在旧入口；`check_test_offline_boundary.py:29–40` 枚举双入口；`scripts/setup-env.ps1:335` 调用旧工具。完整文本引用行号见 CSV。历史描述和测试负例可以保留明确用途，不做全局替换。

**资产表不是删除批准清单。** 当前身份只供 P0 恢复定位；P4/P5 必须重新记录具体删除集合、身份和批准。未登记资产不能静默删除；登记为 review 也不代表必须修改。

## 5. #499 / #552 相交成果及所有权保护

2026-09-18 通过 `gh issue view ... --json number,title,state,updatedAt,body,url` 读取两个 issue；不发布评论。

| 对象 | 现状 | 被新方向替代 | 必须保留 | 独立待办 |
|---|---|---|---|---|
| [#499](https://github.com/MJ-AgentLab/mj-agent/issues/499) | OPEN，updatedAt=`2026-09-09T09:31:26Z`；本地已合并 C1 #517、C2 #518、D1a #519、D1b #520；相关登记后来在 #523 移位 | 跨客户端 authoring/carrier/manifest/lock/fidelity、投影 drift、未来旧 receipt/ready-host 交付设计 | PR-0b 离线边界、PR-0c sanitized snapshot、数据不直连、Owner/Merge 边界、非破坏保留邻居、guard 最小输入和如实状态 | 不续做 D2/E/F/G，不重算观察 streak，不关闭 Epic 或代做 lifecycle |
| [#552](https://github.com/MJ-AgentLab/mj-agent/issues/552) | OPEN，updatedAt=`2026-09-17T09:03:49Z`；独立工作树有 5 tracked 修改和 1 未跟踪计划 | 若退出 agents_sync，其 doctor 集成点将需替代 | Owner 授权、规则 decision、有效会话模式三层分离；UNKNOWN/INCOMPATIBLE 不报成功；不读取秘密/用户配置 | 为什么 Desktop 最终有效为 never、真实交付恢复、原 session-maintenance push/PR 均不在本轮 |

#499 最新可见 ledger comment `5599639080` 记的是 **2026-09-09 历史观察值 19/20、D2 待裁**，不是本轮重新验算的资格。其工作树测试注释声称 Owner toggle 已记录，本轮不从注释推定授权存在或共享基线已 blocking；只记录实际差异。shared HEAD 的 V13 仍是 warning telemetry。

#499 未暂存修改为两文件：将 skills/mcp scoped pin 恢复为全表 `--check`，并增加 enforcement predicate 的 blocking test；它们未进入本迁移 HEAD。本轮不应用、不撤回、不重跑旧交付矩阵。

#552 未暂存修改涉及两个 GUIDE、`agents_sync.py`、两份测试；新增计划自述审批诊断三场景已验证。代码可见 `_doctor_approvals`、`--only-approvals` 和显式有效模式参数；本轮未运行其修改版代码，历史“测试通过”不作为本轮验收。

在途文件原始 SHA-256（同一 HEAD 的 Git 历史**不能恢复这些未提交差异**；恢复来源仍在原工作树，由 Owner 保管，本轮不备份/复制其内容）：

| 工作树 | 路径 | SHA-256 |
|---|---|---|
| #499 | tests/unit/test_agents_sync.py | `378c986c19a40646ab6c54960df5bc932cffe2c0e0b566bbf78e0c6168c1bdcf` |
| #499 | tests/unit/test_v2_engine.py | `b9eccb361cac416d68e4307bcd74f93f9ad0db6486b4d0814ba5c3ad5ca8bf3d` |
| #552 | docs/guide/[GUIDE]_Developer_Onboarding.md | `78e47bc2c3b67457149396e62f2ebeaf6b3c1d3301df4414bc7e7984bf894326` |
| #552 | docs/infrastructure/git/[GUIDE]_Git_Push_Workflow.md | `9ad544a6b788da63edbff8f4c936aa30175de80dd8f893d29aeb8370ee7bc50c` |
| #552 | scripts/sdd/agents_sync.py | `f42b0b01ecd84e6b8174101e7ab31aada7e6a4c1da6d9d91167ff601fdacbc62` |
| #552 | tests/unit/test_codex_enforcement_d1a.py | `11ae0a17607a0bd3edc0f3cc249df7490af803caae4dd4634bdf58afc4505274` |
| #552 | tests/unit/test_sdd_development_agent.py | `f68870929fe5886c0fc990306e90fa2ae18279cd7b4e68e4fa1d92a0a155496a` |
| #552 | plans/[PLAN]_552_codex_approval_preflight.md | `1c7e1b3d53c6afcaca88b5250997d95aaef7fa28484b424a860913d223b32a9f` |

## 6. 继承问题、边界及 P1 输入

| ID | 本轮观察 | 处置 / AC |
|---|---|---|
| B01 | `yaml.safe_load` 拒绝 36/37 Claude 源 frontmatter；5/18 byte-copy 投影同样被拒绝；仓内 `parse_native_frontmatter` 刻意接受 description 中冒号 | 既有格式差异，V4 37 PASS 不证明严格 YAML；P2 候选规范转义/引用并保留字符串语义，P4 实测发现。AC-01/02/06；不修改旧技能 |
| B02 | 8 infra 技能 description/body 共 16 项冻结摘要全部匹配 | 作为基线保留；P2 草案，P3 经批准成组更新；不能只跑 V4 代替摘要校验。AC-02/07 |
| B03 | `check_secret_exposure.py:212,220` 对 config 缺失可 PASS、非法 TOML WARN | P1 必须补原生存在性/解析硬失败检查，不能删除 V11 后只靠 secret 扫描。AC-04/05 |
| B04 | hook guard 的未知/无法解析 payload 放行，需审批编辑使用 block；源码 wire 注释基于 CLI 0.147.0 | 继承局限；P1 明确支持边界，只修阻断原定验收的最小问题；实际引擎 canary 留 P4。AC-05/06 |
| B05 | 独立 CLI 的 Gitee push rule、内嵌引擎的 origin push / PR create rule 均实测 `decision=prompt`；当前有效模式 never | 静态兼容性为 INCOMPATIBLE，不执行真实 Git 动作；P1 合成诊断不阻塞，P4 宿主/未来交付需要兼容会话。不得绕过规则或修改个人配置。AC-05/09/12 |
| B06 | PG launcher 先 npx discovery，再检查缺失连接变量；还含缓存损坏递归清理路径 | P0 没有运行；P1 使用隔离 stub/合成输入测试，不触发实际安装、个人缓存清理或连接。只改为满足原定无秘密/安全路径验收所需的最小部分。AC-04/08 |
| B07 | 当前工作树无 `.venv`、PATH 无 python；既有 develop Python 可只读使用 | P0 无需安装；P1 先确认可复用环境满足受控 runner，再决定环境准备是否需要额外授权；不得无提示升级/安装。AC-09 |
| B08 | ADR 模板仍建议 docs/adr，而正式 ADR 已在 decisions；旧关联计划/lifecycle 文本含历史状态 | 本轮用现有 decisions 命名空间，仅起草正文；不顺手修模板/历史欠账。AC-11 |

P1 所需输入/边界已经固定：

1. Owner 明确启动 **P1 单阶段**；P0 指令不授权继续。沿用当前 worktree，不需新分支操作。
2. 候选根为 `.migration/codex-only/project/`，按最终相对目录放置 `.codex/`、`scripts/mcp/` 等；本轮未创建。不要将其注册为当前根工作树技能发现入口；宿主 canary 使用独立 Git 副本。
3. 以 CSV 中 migrate-tool 三文件、原生 config/hooks/rules 候选、guard 去 typed-source 依赖、必要安全测试拆分为最小输入。最小检查器的实际文件名/CLI 由 P1 实现后登记，不伪称现已存在。
4. 合成 env、无秘密 fixture、stub Node/npx、隔离临时目录；不解密/轮换/写 OS 凭据，不运行 MCP/业务服务。测试资源若不满足，报告具体缺口。
5. P1 可准备 #552 三层诊断的有限等价实现，但不能整包吸收其工作树；只在 B05 直接阻断 AC-05/09 时登记最小承接，不完成或关闭 #552。
6. P3 之前仍需审阅本报告 ADR 正文、正式切换 exact diff、契约/CI/保护面变更及批准集合；P5 删除另需具名批准；P6 Git 动作另按已有授权。P0 没有申请这些未来动作的笼统批准。

## 7. 验收基线与门禁替换

### 7.1 当前 CI 姿态（读取 workflow，未运行 CI）

| Gate | 实际基线 | 原生验收承接 |
|---|---|---|
| V4 | blocking step，`check_claude_skill_contracts.py --all`；无 `--strict`，解析器部分发现只 WARN | 原生 schema/name/description/资源 + infra 冻结纪律；不能把 step blocking 误读为所有 WARN 硬失败 |
| V8 | `check_development_agent.py --all --fail-on warning`，continue-on-error=false | 能力覆盖、5 AGENTS、Owner 边界 |
| V9 | `check_agents_projection.py --all --fail-on warning`，continue-on-error=false | 原生入口/引用闭合、未拥有邻居保护；不保留 lock 比对 |
| V10 | `agents_sync.py --check --surface skills`，continue-on-error=false | 37 项清单、原生有效性、无活动旧依赖 |
| V11 | `agents_sync.py --check --surface mcp`，无 continue-on-error（blocking） | config 缺失/非法硬失败、8允许/6禁入、变量按名、无秘密 |
| V12 | cross-carrier，continue-on-error=true | 迁移期语义对照；不永久保留双源 fidelity |
| V13 | enforcement drift，continue-on-error=true | 原生 handler/rule 行为反例、宿主激活证据 |

注册载体还包括 `plans/[PLAN]_m-fu-v12-v13-gate-observation.md`；已补入CSV，保留历史锚，不把它当作须整体改写的旧计划。Claude专属ignore、Docker局部ignore、13份fidelity coverage及3份probe fixtures也已逐项登记；历史批准与语料保留，仅退出旧活动依赖。

CI step 名称及注册在 `.github/workflows/ci.yml:179,350–426`、`sdd/gates.md`、`policies/ci-gates.md` 留有直接依赖。原生检查必须先承担保护，再退出旧门禁；P3 同批处理仍被 pytest 发现的旧专属断言。不暗改阈值/required-check 名称；远端 branch protection 本轮未核实，P3/P6 若改名须先只读核对。

### 7.2 L1–L6 与 AC 状态

| 层 | 固定验收口径 | P0 状态 |
|---|---|---|
| L1 | 37 技能+直接依赖/消费者逐项处置、来源与恢复可追溯 | 盘点部分 STATIC_PASS；候选资源闭合留 P2/P4 |
| L2 | 排除旧客户端、个人兜底的独立 Git 副本；包含实际交付未跟踪文件 | NOT_TESTED |
| L3 | 正向、拒绝、缺失、非法解析、恢复、离线/数据/Git安全断言 | NOT_TESTED；本轮旧规则重放不是原生候选验收 |
| L4 | 37 项八维语义；至少74个基础正反例，高影响目标变化/部分完成/重入 | NOT_TESTED |
| L5 | 37 项被发现、五族各一显式无副作用调用、近邻误触发、Git/保护文件/删除演练、hook/rule允许+拒绝 | NOT_TESTED；须记录具体宿主版本和真实观测 |
| L6 | 按批准的服务/环境/时间逐项探针 | NOT_TESTED；未纳入默认技术完成必需集合 |

必测路径：根、相关子目录、含空格路径、clone、linked worktree；Windows launcher 与 Linux CI 分别记录。未知/未启动/工具加载失败/JSON损坏不能降为普通 warning，也不以 exit 0 代替内容 verdict。

| AC | P0 固定输入 | 当前整项结论 / 后续阶段 |
|---|---|---|
| AC-01 | 37源、18投影、19缺入口逐项列齐 | NOT_TESTED；P2/P4原生发现 |
| AC-02 | peer/resources、8冻结契约、授权保留要求 | NOT_TESTED；P2八维/案例、P4 |
| AC-03 | 源/生成物/锁/renderer处置已登记 | NOT_TESTED；P3/P4所有权切换 |
| AC-04 | 8服务、变量名、3迁出工具、禁入边界 | STATIC_PASS仅配置盘点；整项待P1/P4 |
| AC-05 | 门禁表、必须保留断言、B03–B05 | NOT_TESTED；P1/P3/P4保护承接 |
| AC-06 | 目标平台、路径、宿主版本分离 | NOT_TESTED；P4独立运行 |
| AC-07 | 直接消费者/非客户端保留列表 | NOT_TESTED；P3/P5更新及复查 |
| AC-08 | 其他工作树身份和个人/秘密保护边界 | P0范围核对PASS；P5清理尚未执行 |
| AC-09 | L1–L5必需、L6另批；继承问题独立登记 | NOT_TESTED；P4/P5综合验收 |
| AC-10 | HEAD:path、输入摘要、在途原工作树恢复来源 | P0登记PASS；P5/P6交接尚未完成 |
| AC-11 | 仅三个新增文档/清单文件 | P0范围PASS；以后逐阶段复查 |
| AC-12 | 没有提交、推送、PR、合并；远端只读状态 | NOT_TESTED（版本未交付）；P6 |

## 8. 本轮证据与文档决策

| 证据 | 实际操作及结果 |
|---|---|
| E01 Git现场 | `git status --porcelain=v2 --untracked-files=all`、`git branch --show-current`、`git rev-parse HEAD/--show-toplevel/--git-common-dir/--git-dir`、`git worktree list --porcelain`、staged/unstaged diff；入场干净 |
| E02 输入 | 指定 develop 计划全文章节读取；Copy-Item 后原件/副本 SHA-256 相同；Owner答复同意 |
| E03 技能 | `git ls-files -z` 对照 manifest capabilities 与计划附录；37/37；37 源目录无额外文件；18入口=13+5 |
| E04 原有schema | Python `-B scripts/sdd/check_claude_skill_contracts.py --all --strict`：37 PASS / 0 WARN / 0 FAIL，exit 0 |
| E05 格式/冻结 | strict YAML 解析失败按B01登记；按契约注明的 regex去frontmatter+LF规范化+UTF-8 SHA-256，8 description + 8 body 全匹配 |
| E06 工具/消费者 | tracked限定读/rg、技能文件引用和consumer行号提取；CSV含路径/摘要/处置/AC/恢复；未读取秘密 |
| E07 宿主 | Appx、当前进程路径、两CLI显式版本、Python/Node/uv/Git/gh版本；见§3 |
| E08 在途工作 | `git -C <tree> status --short`、仅具名文件diff/摘要；issue正文及#499最近ledger；未改其他工作树 |
| E09 规则重放 | 0.147.0：`execpolicy check --rules .codex/rules/mj-agent.rules --pretty git push -u gitee maintain/codex-dev-mode-migration`；0.155.0-alpha.9：相同命令origin，以及 `gh pr create --base develop`；三条均 decision=prompt，仅计算规则，不执行命令 |
| E10 文档质量 | 单文档 frontmatter、本地Markdown链接、围栏、UTF-8、CSV唯一性/源闭合/摘要、输出范围及在途身份复核；PASS：两个文档frontmatter、6个本地链接、UTF-8无BOM/无行尾空白/围栏配对；37技能三方集合一致；CSV唯一性与非敏感摘要一致；正式tracked diff为空；其他三工作树已登记状态/摘要不变 |

执行过程中的非产品失败如实保留：当前工作树初次读取计划报“不存在”，随后读取用户明确给出的 develop 原件；PATH `python` 不存在，改用既有解释器；技能用 strict YAML 解析触发 B01，后改用仓内明确的 native 语义作源盘点；V4 初次误传 `--fail-on warning` 返回 argparse exit 2，按其实际 CLI 改为 `--all --strict` 后通过。这些没有触发安装、修源或改变验收口径。

本轮未运行全仓 lint/mypy/pytest、旧投影 sync/drift 全矩阵、Docker/Studio、真实 MCP/DB/业务探针、Linux CI或真实模型 canary。P0没有产品改动，不为“补绿”运行与盘点无关的矩阵；后续命令沿用计划§6.3受控runner。

| Type | Action | Path | Existing Target | Reason | Evidence | Template Notes | Required Before |
|---|---|---|---|---|---|---|---|
| Plan | Copy | 本地同名计划 | develop原件 | 固定输入 | E02 | 原样，不翻状态 | 已完成 |
| SPEC | None(P0) | 既有MCP capability | spec/contracts | 后续必要路径修订 | CSV | 不创业务规格 | P3 |
| ADR | Draft body | 本报告§9 | ADR-035/036/039等 | 定向替代兼容条款 | E03/E06 | 编号未分配；五段正文 | P3 |
| RUNBOOK | None(P0) | 既有MCP runbook | 资产表路径 | 后续启动/恢复入口 | E06 | 本轮恢复见§10 | P3/P6 |
| GUIDE | None(P0) | 上手/Git指南 | 资产表路径 | 新入口与诊断 | E06/E08 | 不吸收#552整包 | P3/P6 |
| STANDARD | None(P0) | policies/sdd现有规则 | CSV直接消费者 | 仅必要原生路径 | E06 | 不全仓治理 | P3 |
| Local ISSUE | None | 无 | 无 | 用户禁止创建 | §1 | 不虚构编号 | 不适用 |
| ASSESSMENT | None | 本累计报告 | 无 | 避免重复报告 | 计划§8 | 验收同一报告累积 | P4 |
| CHANGELOG | None(P0) | CHANGELOG.md | 现有 | 本轮无功能切换 | 零tracked diff | 后续说明 | P6 |
| INDEX | None(P0) | 无新增canonical | decisions/INDEX.md | ADR尚未正式写入 | §9 | plans不建INDEX | ADR落盘时 |

Repo Scan Verdict：**Plan still valid**；实际执行位置从 develop输入转为已有隔离迁移工作树，写入本报告即足够，不重写原计划。整体迁移 High/C；本轮文档盘点不触碰业务必停源码。未涉及函数/表字段重命名、DDD、性能、catalog或runtime正文改动；反扫只针对未来旧开发入口直接引用。biz schema漂移“不涉及”，不是 PASS_NO_DRIFT。

## 9. 定向 ADR 可审阅正文（未编号、未生效）

编号核查：本地所有 heads/remotes 的 `decisions/`、`archive/decisions/`、`docs/adr/` 文件名最大 ADR 编号为 **039**；本轮未 fetch，不能保证未获取的远端/他人草案未占号。因此使用 **ADR-待编号：Codex 独立开发入口与原生资产维护**，不预占 040。正式落盘前重新核对命名空间及 `decisions/INDEX.md`。以下为正文草案，不附 `decision: accepted`，不修改既有 ADR 状态。

### Context

mj-agent 的业务 agent 与开发工具分别治理。当前开发技能以 `.claude/skills/` 为源，通过 manifest、registry、translation、renderer、lock 生成部分 Codex 入口；37 项开发能力只有18项已有投影。Codex已具备完整参与授权，Owner提出今后以Codex独立开发，Claude退出项目开发入口。

继续双工具兼容会使原生技能、MCP和守卫依赖待退出客户端，并把精力用于跨载体一致性。本次需要改变开发资产的维护权及相应消费者，而不改变业务权限、Owner决策权或运行时语义。依据为本迁移计划、P0资产表、ADR-035/036/039及数据/秘密边界。

### Decision（提案，待Owner采纳）

1. 项目受支持的开发入口改为根及局部AGENTS、37个同名原生开发技能、直接维护的Codex配置/hooks/rules。`.agents/skills/`与`.codex/`在获批成组切换后成为正本；切换前继续遵守生成物禁令。迁移计数37是基线覆盖要求，不是未来schema永久常量。
2. 将允许MCP所需launcher/wrapper/凭据维护**代码**迁至`scripts/mcp/`，不读取Claude配置、不生成第二份Codex配置。保持当前8项允许用途及biz×5/ssh-manager永久禁入；不扩服务权限或承诺外部可用。机器trust、hook激活、秘密和个人配置由工程师在原边界内维护。
3. 退出Claude→Codex翻译、投影、sync/adopt、lock、双边fidelity与客户端专属适配资产；有效流程、测试和保护先进入原生技能、现有政策/契约或专用守卫。不能用换名生成器维持旧链，也不能为此搬迁全部`sdd/adapters/`或全局改变adapter_coverage。
4. Owner继续唯一决策者。ADR-000/006/009数据边界、ADR-030凭据隔离、ADR-034 HITL、Git worktree/显式PR base、人工merge、受保护源码/配置/契约/CI及离线runner约束保持。Owner授权、工具规则decision、有效宿主权限分别判定；UNKNOWN/INCOMPATIBLE不是成功，技术拒绝不允许绕过。
5. 原生入口、维护规则、guard、直接消费者、必要契约和门禁必须成组切换。既有安全保护有新的明确承担者后才退出旧检查；活动旧断言同批改造。P4独立Git副本通过L1–L5，P5才按具名批准清理；L6按服务另获授权，不以SKIP或静态检查宣称服务就绪。
6. 本决策只定向替代冲突条款，历史ADR保持可追溯。#499剩余双载体交付设计被新方向替代，但其安全成果保留；其Epic/lifecycle不由本决策自动关闭。#552仅承接阻断迁移既定验收的最小语义，未提交成果与独立恢复工作保持原所有权。

定向关系：

| 原决策 | 拟替代的部分 | 保留部分 |
|---|---|---|
| ADR-035及amendment | 双实现者/Claude项目入口持续存在的角色表述 | Codex完整开发参与资格；全部Owner与数据约束 |
| ADR-036 D-001/003/004 | 双工具对等运行、薄客户端adapter、双边manifest维护机制 | 项目内kernel单源、最终Owner判定 |
| ADR-036 D-011/012/014（含ADR-039修订） | generator-owned、禁止原生维护、sync/adopt/lock与投影选择机制 | 不触碰未拥有邻居、可审阅恢复、计数不硬编码 |
| ADR-036 D-013/016/017 | MCP投影载体、旧drift检查对象及源文件锚点 | 允许用途/永久禁入、门禁变更独立批准、保护面和10-enum纪律 |
| ADR-036 D-007/008/010/015 | 无替代 | 数据/Secrets、Git HITL、10-enum、人工trust、doctor只读 |
| ADR-039 Decision 1–8/11及relationship | 18-PR旧计划、18-carrier终态、closed cross-carrier schemas、fidelity/lock/reconcile生成链、旧生命周期交付安排 | 离线安全、证据不冒充、单阶段串行、人工merge、未拥有文件保护与Owner边界 |
| ADR-013/016/032中Claude专属载体条款 | in-tree开发技能的客户端路径/加载表达/Claude schema监测指向 | runtime/plugin/development分源、命名/description质量；不整体重写历史ADR |
| ADR-037 | memory MCP通过Claude源投影到Codex的实现路径 | 五环境原有用途、独立凭据、变量名注入及数据边界 |

### Consequences

正面：37项能力以原生入口完整维护；后续开发无需Claude客户端或投影工具；配置、路径和失败结果能以实际宿主验证。

成本：必须验证19个新增入口、八项infra契约和全部直接消费者，承担宿主版本差异与guard覆盖局限。安全能力不能由单一hook或命令前缀替代；CI、宿主权限、凭据角色和人工审查仍各有边界。

过渡：候选区是迁移工作产物，不是第二份长期正本。清理保留历史恢复定位；正式切换要成组恢复，不能只回退配置留下不匹配门禁。源码恢复不等于凭据/数据库/容器恢复。

### Alternatives considered

- 继续双工具兼容：不满足Owner的Codex独立开发方向，增加非必要维护面。
- 仅迁18个现有投影：丢失19项现有开发能力，不满足AC-01/02。
- 将整个adapter目录/schema重新设计：超出范围，对业务和治理引入不必要变更。
- 先删除旧门禁/源，再补原生能力：会造成保护空窗和恢复断链，不满足AC-05/08。
- 另建通用授权receipt/诊断平台：不能由当前迁移验收推出必要性，不纳入。

### References

- 本迁移计划§2、§4、§5、§6与本报告资产表/基线。
- `decisions/ADR-035_Codex_Full_Development_Participant.md`。
- `decisions/ADR-036_Dual_Agent_Thin_Adapter_And_Projection.md`。
- `decisions/ADR-039_Codex_Cross_Carrier_Kernel.md`。
- ADR-000/006/009/013/016/028/030/032/034/037；`policies/ai-agent.md`、`policies/data-boundary.md`、`policies/git-branching.md`、`policies/ci-gates.md`。
- #499/#552只作相交背景及成果来源，不构成新动作授权。

## 10. 恢复入口、累计阶段状态与停止点

共享源资产从 `20e2f24c352cf640d9dd33234b128ca897804b99:<资产表source>` 定位；CSV同时保留blob与非敏感原始字节摘要。Windows工作树CRLF与Git blob LF可能不同，不能把字节摘要不同自动判为内容漂移。恢复必须先复核当前身份，按批准的精确文件集合操作，不执行全树reset或递归清空。

本轮P0输出未提交：计划副本可由develop原件按记录摘要重建；报告与CSV的唯一当前成果就在本迁移工作树。Git HEAD不包含这三个新文件；如需撤销，仅在另有授权且身份一致时处理这三文件，不触碰用户输入或其他工作树。原件及#499/#552未提交成果的恢复不由基线Git SHA兜底。

| 阶段 | 状态 | 完成/缺口 |
|---|---|---|
| P0 | 完成 | 基线、277行原始资产表、在途保护、宿主、定向ADR正文、工作树建议、验收及恢复输入 |
| P1 | 候选与离线验证完成；停止 | 10个候选、共享测试拆分、48+74项离线通过；Owner选择硬阻断；L5/真实服务未验证 |
| P2 | 候选与静态语义评审完成；停止 | 37候选、296维对照、74基础+68补充案例、8项未应用契约草案；无宿主/真实调用证据 |
| P3 | 未开始 | 正式切换及保护面/契约/CI的具体授权与差异 |
| P4 | 未开始 | 独立副本与L1–L5实测、具名清理清单 |
| P5 | 未开始 | 具名清理批准、身份复核、受影响项复验 |
| P6 | 未开始 | 交接、获授权Git操作、CI/review/人工merge实际状态 |

未决项不阻塞P0交付：ADR最终编号/采纳、P1环境准备、原生检查具体CLI、#552有限承接细节、P4宿主激活/兼容审批会话、Linux实际运行证据、P3/P6远端required checks。它们分别在依赖阶段解决，不当作本轮已通过，也不自动开启后续阶段。

## 11. P1 执行记录（2026-09-18，当前状态）

### 11.1 授权、范围与实现

沿用原工作树和 `20e2f24c352cf640d9dd33234b128ca897804b99`；进入 P1 时已有 P0 的三个未跟踪交付文件。没有新建主仓分支、暂存、提交、推送、issue 或 PR。候选没有注册为当前项目技能入口，也没有激活其 hooks/trust。下面的路径均相对当前工作树；候选部署相对路径须去掉 `.migration/codex-only/project/` 前缀。

| 文件/集合 | 内容与目的 | 计划/AC |
|---|---|---|
| `.migration/codex-only/project/.codex/config.toml` | 项目级配置；GitHub、Playwright、Serena、memory×5 共 8 项；变量按名注入。配置仍要求 on-request/workspace-write，不导入任何其他来源 MCP | §4.3(2–4)，AC-04/05 |
| `.migration/codex-only/project/.codex/hooks.json` | 项目 hook；先以 Git 定位当前项目根，再调用原生 handler；Windows 引导用 EncodedCommand 防止外层 shell 提前展开变量，其完整明文可在 checker 的 HOOK_BOOTSTRAP 审阅 | §4.3(4–6)，AC-05 |
| `.migration/codex-only/project/.codex/rules/mj-agent.rules` | G1、人工 merge、直接 PG 客户端 forbidden；commit/push/PR create prompt。prompt 不等于 Owner 授权 | §4.3(4–5)，AC-05 |
| `.migration/codex-only/project/scripts/sdd/codex_hook_guard.py` | 标准库专用 guard，无 typed YAML/renderer 读取；仅投影 event/tool/input，不读 transcript、session、cwd 私有字段；保护秘密、G1/G2、runtime/infra 与原生配置编辑 | §4.3(5–7)，AC-05 |
| `.migration/codex-only/project/scripts/sdd/run_codex_hook.ps1` | 从脚本位置定位项目根，调用该项目 `uv --directory … run --frozen --no-sync python`；错误返回明确 block JSON | §4.3(5–6)，AC-05 |
| `.migration/codex-only/project/scripts/mcp/pg-server-start.ps1` | 原 cmd launcher 的必要迁移：先验证允许变量及缺失状态，再发现 npx 包；稳定处理空格与子目录；取消自动递归缓存清理；只将变量名传给 Node | §4.3(2)，AC-04/08 |
| `.migration/codex-only/project/scripts/mcp/pg-server-wrapper.mjs` | 保留 #38 的 OID 1114/1184 原始时间戳 parser；在进程内把环境值交给上游 server；wrapper 自身异常只输出固定脱敏信息 | §4.3(2)，AC-04 |
| `.migration/codex-only/project/scripts/mcp/setup-mcp-secrets.ps1` | 只维护 GitHub+memory×5 的 6 个既有变量名；保留 overwrite 确认及 Reload；不输出值前缀，解密结果仅在内存，不写明文 conf/.env；不导入其他 MCP/应用凭据 | §4.3(2)，AC-04/08 |
| `.migration/codex-only/project/scripts/sdd/check_codex_native.py` | 原生最小检查：必需文件、严格 TOML/JSON、8项闭合、固定安全命令与按名注入、rule 决策；非法输入硬失败、诊断不回显配置值 | §4.3(8)，AC-04/05 |
| `.migration/codex-only/project/tests/unit/test_codex_native.py` | 48项合成案例；覆盖失败修复、缺文件、禁入服务、秘密不回显、路径/协议、PG parser、维护脚本纯函数 | §4.3，AC-04/05/09 |
| `tests/unit/test_agents_sync.py` → `tests/unit/test_offline_execution_boundary.py` | 原 42 个离线测试函数及一个 helper 原样移出，参数化后 74 项；仅清理原文件无用 import，保留其余 65 个定义 | §4.3(7)，AC-05/07/09 |

三个工具均为代码候选；**没有执行真实解密、读取真实凭据或写 User 环境变量**。维护脚本的 helper 测试由 PowerShell AST 只提取两个纯函数，注入合成输入；不 dot-source 整个脚本。PG launcher 测试用 npx 进程替身及假的 Node 包，未下载包、启动 MCP 或连接任何数据库。

工具改动对应原定无秘密与安全路径验收：原 launcher 将连接值放入命令行、先发现包再检查缺失变量，并有递归清缓存分支；候选按名传递、先报缺失且无自动清理。原凭据维护脚本会显示值的前四位及生成临时明文文件；候选只输出固定标记、在内存解析允许的项目变量。没有引入轮换协议、新服务或凭据管理平台。

### 11.2 本地验证（客观证据）

[机器可读验证记录](../evidence/codex-only-migration/p1-verification.json) 含候选字节摘要、命令、red/green 过程、邻居身份及未验证集合。

| 检查 | 实际结果 | 边界 |
|---|---|---|
| 受控离线 pytest | **122 passed in 14.94s**：48 原生候选 + 74 原样保留离线案例，0 skip | 不是宿主、真实包或外部服务验证 |
| 原投影测试文件拆分后回归 | 主工作树受控 runner 执行 `tests/unit/test_agents_sync.py -q`：**56 passed, 3 skipped in 2.76s** | 3项原有 symlink 案例因本平台创建权限不足未验证，不计为通过 |
| 拆分 AST 等价 | 移出 43 个定义（42 tests+1 helper）与 HEAD 一致；其余 65 个定义与 HEAD 一致，集合无遗漏 | 仅 import 整理与位置改变 |
| ruff 定向检查 | candidate Python 和两个共享测试文件通过 | 未跑全仓 lint/应用 mypy，业务源码未改 |
| Node / PowerShell 解析 | `node --check` wrapper 通过；3 个 ps1 AST 零解析错误 | 未执行真实维护入口 |
| 原生 checker | `config=STATIC_PASS`；有效 `never`→`INCOMPATIBLE`；Owner=`NOT_ASSESSED`；host=`NOT_TESTED` | 返回码 0 只表示静态配置合法，不表示可审批或服务可用 |
| 内嵌 CLI 0.155.0-alpha.9 | `git push origin example`→prompt；`gh pr merge 1`→forbidden | 仅 `execpolicy check`，没有执行这些动作 |
| 独立 CLI 0.147.0 | `git checkout -b example`→forbidden；`gh pr create --base develop`→prompt | 同上，不涉及新分支/PR |
| 根/空格/子目录 | PG 直接入口与配置命令、hook 经 cmd/pwsh 的引导及输入透传通过；错误项目根明确 block | clone/linked worktree 和实际宿主发现仍留 P4 |
| 其他工作树身份 | #499 的2个、#552的6个及 develop 原计划共9个 SHA-256 与 P0 一致；Git状态仍为原集合 | 未修改、暂存或吸收其未提交成果 |
| 正式边界 | HEAD 未变、主仓 staged=0；唯一 tracked diff 为共享测试拆分 | 正式配置/技能/政策/契约/CI/runtime均未修改 |

受控 runner 要求测试受 Git 跟踪，因此在被忽略的 `.mj-agent-local/codex-only-p1-validation` 建立**仅供测试的独立 Git 元数据与 index**；没有 commit、branch ref 或原仓 git-dir 链接。原工作树没有 `git add`。副本用现有 develop `.venv/Scripts/python.exe -B` 运行，未安装/升级；runner 仍检查插件版本并构造封闭子进程环境。

复现副本的具名输入：拆出测试中的 `_OFFLINE_BOUNDARY_FILES`（17项），加 `README.md`、`pyproject.toml`、`uv.lock`、`.gitignore`、现有 `scripts/__init__.py`、`scripts/sdd/__init__.py`、`scripts/sdd/check_test_offline_boundary.py`、现有 tests 包初始化文件、共享拆出测试；再覆盖候选根的相对文件。仅在该独立副本登记测试 index。不要复制原 worktree 的 `.git` 文件，不带 `.env`、秘密、个人配置或缓存。这个副本为了**原断言等价性**保留其旧 CLAUDE 文档输入，不冒充 P4 无旧客户端副本；原生 checker 的另一个测试 fixture 没有 `.claude/` 或 `sdd/` 仍通过。

实际测试命令（从本迁移根执行）：

```powershell
& '../../develop/.venv/Scripts/python.exe' -B '.mj-agent-local/codex-only-p1-validation/scripts/sdd/run_offline_pytest.py' tests/unit/test_codex_native.py tests/unit/test_offline_execution_boundary.py -q
& '../../develop/.venv/Scripts/python.exe' -B '.migration/codex-only/project/scripts/sdd/check_codex_native.py' --effective-approval-policy never
```

过程中的失败均保留：首次缺实现的 collection RED；独立副本缺 README 导致原断言失败；新增路径用例暴露 PG 退出码及 hook shell 引号问题；错误根目录暴露 nested PowerShell 将 exit 2 变成 1。修复后完整重跑得到上表结果。hook 现在使用文档支持的 block JSON，协议 exit 0 不代表允许动作。一次批量写候选的 shell 调用被工具策略以“blocked by policy”拒绝，未执行；后续使用 `apply_patch` 逐文件写公开候选代码，未读取秘密、变更正式配置或放宽工具权限。

### 11.3 AI 自检与承担边界

使用 implement → verify → self-review/scope-drift 的适用步骤；没有执行其中超出本阶段的提交、push、PR、CI切换或 live probe 交接。审查的是工作区候选与未暂存拆分，不把空 staged diff 当作已经检查。

- 范围逐项映射到 §4.3；无业务/runtime 修改，未引入新服务/全仓治理。scope-drift=None。模块边界、秘密输出、文档同步与反向引用、恢复说明已核对；data/schema、Prompt version、SPEC Delta不涉及。
- 候选读取链只使用原生路径、Git根和具名变量；不从用户/插件目录补载 MCP，不读 typed adapter 或 renderer。正式配置当前仍走旧链，这是 P3 前刻意保留的状态。
- 原来冻结的 infra 技能与 runtime skill 候选保护保留；普通原生 skill 不再因“生成物”被 blanket block。路径级 Dockerfile 编辑保守归 Owner 类，未试图在本阶段解析外部镜像行；具体授权层级仍由现行政策决定。
- `ALLOW` 仅表示这个有限识别器未命中已知停点，不能证明 shell 安全。动态脚本、命令别名/全局选项、任意 Python/SQL 客户端、间接文件写入和未匹配工具都不能靠它穷尽；AGENTS 自律边界仍适用。无法解析 payload/复杂复合命令返回 UNKNOWN并block，不增建通用 shell 解析器。
- Owner 已选择硬阻断：hook 遇 `OWNER_APPROVAL_REQUIRED` 也返回 block，**Owner在聊天中批准不会自动解锁hook**。将来具体执行路线须人工审阅处理；不建立 receipt、不自动停用保护、不把当前会话 never 改成其他模式。此限制必须进入 P2 技能语义/P4 canary/P6交付说明。
- checker 的模式参数来自调用者显式输入，不探测个人配置，不声称查明 #552 覆盖来源；未知模式=UNKNOWN，never=INCOMPATIBLE。#552仍未完成，#499 D2/观察期/门禁升级未承接。
- 文档/INDEX/CHANGELOG/PR模板的正式切换仍属P3；当前无用户产品行为发布，commit message、PR字段、branch×commit检查不适用。此处 GO 仅指P1候选交付，不是GO commit/上线。

机制依据按 2026-09-18 查询的官方 [项目 MCP](https://learn.chatgpt.com/docs/extend/mcp)、[hooks](https://learn.chatgpt.com/docs/hooks)、[rules](https://learn.chatgpt.com/docs/agent-configuration/rules)：项目配置须被宿主信任后加载；当前 hook 支持 block/deny，ask不能充当审批；前缀规则判定与有效会话审批模式是不同层。实际宿主是否加载、触发与执行这些机制，仍需 P4 留证。

### 11.4 未决项、恢复与 P2 输入

1. **未验证，不阻塞P1候选交付**：实际8项服务连接、npx真实包发现/安装、上游包异步日志行为、真实凭据解密/OS注入、hooks激活、模型canary、Linux运行、clone/linked worktree发现。Windows合成进程测试不能替代这些证据。GitHub/Playwright/Serena保持原命令与包版本选择，未做供应链升级或宿主连接测试。
2. **P2输入**：明确启动P2单阶段的指令；P0的37技能清单与八维基线、18投影参考、8infra冻结摘要；本轮10个候选、原生工具路径与Owner硬阻断选择。P2需记录调用工具缺失/依赖与返回阶段，至少74项语义案例，不运行生产/凭据动作。
3. **P3/P4前置**：ADR正文仍待审阅/采纳与编号；受保护正式切换、infra契约和CI变化须具体批准；P4需人工review/trust、兼容审批会话及Owner动作的实际执行路线。原生规则检查通过不是这些前置已完成。
4. **恢复**：既有文件仍由P0基线SHA+CSV blob定位；本轮共享拆分若需撤销，先核验身份，再将 `test_agents_sync.py` 与新拆出文件视为一组，按具名批准恢复，不全树reset。候选10文件及新测试尚未提交，HEAD没有它们；其当前恢复来源是本工作树，验证记录保存字节身份而非内容备份。原始3个工具仍在HEAD和原路径，可对照重建；不得用它们覆盖P1新增保护而不审阅。忽略的测试副本可按具名输入重建，不是权威源，也未被当作交付备份。
5. **停止点**：P1结束，未开始37技能正文迁移、正式切换、删除旧资产或版本交付。本阶段没有申请后续阶段的笼统批准。

## 12. P2 执行记录（2026-09-18，当前状态）

### 12.1 范围、身份与交付

执行位置仍为 `maintain/codex-dev-mode-migration` 工作树，HEAD 仍为 `20e2f24c352cf640d9dd33234b128ca897804b99`。入场已有 P0/P1 未跟踪成果，以及 P1 对 `tests/unit/test_agents_sync.py` 的未暂存拆分；没有覆盖它们。进入 P2 时登记883个既有公共文件的字节身份（不读取秘密），最终允许变化仅为本报告与资产表。P1 验证记录列出的12个候选/测试文件和9个受保护邻居摘要全部保持一致；没有修改其他工作树。正式 tracked diff 仍只有 P1 的测试拆分，staged 为空。

| 交付 | 内容与证据 |
|---|---|
| [37项候选目录](../.migration/codex-only/project/.agents/skills/) | 每个原始 `.claude/skills/<name>/SKILL.md` 均有同名候选；37源集合=37候选集合；18正式投影只作参考 |
| [八维对照](../evidence/codex-only-migration/p2-skill-comparison.md) / [机器记录](../evidence/codex-only-migration/p2-skill-comparison.json) | 37×8=296维；来源、触发、输入、读写目标、顺序、授权、异常恢复、完成判据、交接返回，保留/改写依据、章节清单与摘要 |
| [完整正文差异](../evidence/codex-only-migration/p2-source-candidate.diff) | 原始源→候选逐行对照；完整流程为基线，未用18项投影或短摘要代替源正文 |
| [语义案例](../evidence/codex-only-migration/p2-semantic-cases.md) / [机器记录](../evidence/codex-only-migration/p2-semantic-cases.json) | 每技能1正向+1近邻反向=74；17项涉及删除、生产、凭据、runtime等高风险技能各增目标变化/部分完成/异常恢复/重入4例=68；合计142例 |
| [8项契约草案](../evidence/codex-only-migration/p2-infra-contract-drafts.md) / [机器记录](../evidence/codex-only-migration/p2-infra-contract-drafts.json) | 旧/新路径、description文本与body差异、旧/新摘要、恢复来源；仅草案，正式契约和冻结摘要不变 |
| [共用执行说明](../.migration/codex-only/project/.agents/references/execution-boundaries.md) | 工具发现、授权、硬阻断、调用/委派/建议/返回、身份复核、部分完成/重入、原生检查接口；候选相对链接闭合 |
| [资源核对](../evidence/codex-only-migration/p2-resource-closure.json) / [验证记录](../evidence/codex-only-migration/p2-verification.json) | 387条引用记录、同名技能依赖、候选/部署布局分列、未满足依赖；当前摘要、检查方法、失败历史及未验证项 |
| [资产处置表](../evidence/codex-only-migration/asset-map.csv) | 原289行的原19列全部保留；追加5个p2字段，登记37源、18参考投影、正式契约草案；新增共享说明及9份证据共10行，累计299行 |

本阶段仅写候选技能、必要共享说明、评审证据和累计记录。没有修改正式源技能、正式 `.agents/`、生成链、配置/政策/契约/CI、runtime、Prompt、SQL或catalog；没有新服务、全目录adapter重构、issue/分支、暂存/提交/推送/PR、外部消息或P3动作。没有执行秘密读取、解密、OS凭据写入、Docker生产操作或真实服务探针。候选命令块是未来执行说明，不是本阶段执行日志。

### 12.2 原生化处理与新发现归类

原生名称保持不变；全部frontmatter只有字符串 `name`、`description`。发现层描述压缩为可解析、可选择的入口，完整触发/排除语义保留在正文“触发与职责详述”。删除强制个人插件、旧客户端工具表达、翻译preface和路由注入；TDD、最小复现、可证伪假设、真实diff评审等方法写成步骤，不将技能名当shell命令。使用 skill-creator 的结构校验及只读infra独立评审；官方[技能说明](https://learn.chatgpt.com/docs/build-skills)用于核对发现元数据与正文职责，不构成实际宿主加载证据。

| 发现/处置（计划§2.4） | 范围与依据 |
|---|---|
| 36份源frontmatter不支持严格YAML；初版28份候选description超长或含尖括号 | 原始源保持不变；候选规范引号、缩短发现描述并保留正文全文语义；用户明确要求及AC-01/02所必需 |
| 候选初次批量变换损坏同级路径分隔符、删去5行功能说明 | 属迁移引入问题；对照源章节/全文diff恢复或明确映射有效语义，复核资源与案例；未留作已通过状态 |
| 源中直接读取.env、假定后台API、直接PG客户端备份/DDL、泛化“批准即解锁”等执行表达 | 为满足明确的秘密/工具/硬阻断约束，在候选最小替代或标UNMET；不修正式源，不搭新能力；无法证明等价的备份/后台执行不宣称已承接可运行性 |
| 原app-stop固定等待后kill、git-delete强删、post-merge自动reset/发布、外项目启动等隐含增量 | 候选补实际目标身份与具体授权，删除自动升级动作；保留任务方法和停点，完整差异可审阅；不实际执行危险动作 |
| 硬编码ADR下一号、缺失历史ADR引用、旧AGENTS章节及原生检查路径不匹配 | 候选按当前公共规范/命名空间映射，历史缺失明确记录；为闭合候选必需引用，不补造旧文档、不改历史ADR |
| 正式规范/模板/schema/CI仍含旧开发入口或投影断言 | 保留正式现状，登记P3直接消费者；P2只给原生技能接口和草案，不用旧生成器填绿，不全目录替换 |
| 未证实的服务、后台生命周期、凭据维护平台和运行时测量 | U01–U07逐项登记，暂停对应依赖；未新增服务或降低验收标准；#499/#552原任务不补做 |

聊天批准不会解锁P1 hook。候选均引用硬阻断说明：无已审阅可用执行路线返回 `BLOCKED_EXECUTION_ROUTE`，不创建receipt、改hook/rules或换工具绕过。独立调用只完成本技能；必要同阶段子流程返回原暂停点；下游建议不自动执行；委派不扩大授权；任何外部发布仍须对应明确指令。

资源采用明确的候选overlay：候选技能/共享说明/P1原生工具从 `.migration/codex-only/project/` 解析，其余具名公共规范、模板和代码接口从当前工作树根只读使用。最终部署去掉候选前缀，逐条保留目标相对路径。未复制整个规范库或业务源码，也不声称候选目录自身可独立加载。P1工具复用且字节不变；MCP仍仅8项项目服务，变量仅GitHub+memory×5，其他来源不迁入。PowerShell凭据维护候选需要实际pwsh平台确认，不把Windows PowerShell 5.1视作已支持。

### 12.3 静态验证与证据级别

| 检查 | 结果 | 限制 |
|---|---|---|
| 严格YAML（SafeLoader并拒绝重复键）、name/目录一致 | 37/37 `STATIC_PASS` | 只解析候选；36份原始源的既有格式问题未修 |
| skill-creator `quick_validate.validate_skill` | 37/37 `STATIC_PASS` | 初次9通过/28拒绝，修正后全过；校验器路径/摘要记入验证记录 |
| 八维及语义案例结构/人工静态推演 | 296维、142例 `STATIC_PASS` | 每例有输入、预期动作/停点、依据、评审结论；不是142次模型调用，不以P1离线测试抵数 |
| 资源及技能名闭合、两个布局 | 387条引用记录，37个同名技能集合闭合 `STATIC_PASS` | 示例/模板另标；不证明每个历史章节锚点语义、独立副本或正式消费者运行 |
| infra旧冻结摘要复算 | 8 description + 8 body共16项完全匹配 | 新摘要只是草案；没有更新正式冻结时间、schema或contract |
| 全文差异、只读infra评审与修订复核 | `STATIC_PASS` | 保留命令的前置、参数和恢复边界；未执行候选内操作 |
| 身份和写入范围 | HEAD/P1/邻居不变，staged为空，既有公共文件仅报告/CSV变化 | 摘要是身份记录，不是未提交文件的内容备份 |

检查使用既有 `../../develop/.venv/Scripts/python.exe -X utf8 -B`、PyYAML及现有skill-creator校验器；未安装或升级依赖。临时审阅脚本在忽略目录 `.mj-agent-local/`，仅用于本轮证据导出/核对，不是迁移交付、长期生成链或恢复权威。复核算法和检查器身份已写入JSON：候选frontmatter严格解析；对37目录运行结构校验；检查引用及技能集合；对照源/候选全文；冻结body按去首部frontmatter、LF规范化、UTF-8 SHA-256，description按原始标量文本计算。正式原生schema/CI自动化切换留P3。

本轮实际收口命令为 `python -X utf8 -B .mj-agent-local/p2_evidence.py` 与 `python -X utf8 -B .mj-agent-local/p2_validate.py`（解释器使用上述具名路径），后者在累计记录更新后再次执行。临时证据导出曾因YAML日期无法JSON序列化失败，修正导出后重跑；这不是契约或产品失败。未新增程序行为，因而未新增pytest；没有重跑或挪用P1的122项离线结果充当P2证据。

P2对应AC切片：AC-01/02候选覆盖与静态语义=`STATIC_PASS`；AC-04/05仅MCP边界复用和技能停点说明=`STATIC_PASS`；AC-07候选资源映射=`STATIC_PASS`、正式消费者=`P3_NOT_APPLIED`；AC-10恢复定位及AC-11本阶段范围核对=`STATIC_PASS`。AC-03正式维护权切换、AC-06独立副本/宿主、AC-08清理、AC-09综合验收和AC-12版本交付均未完成，不能由本阶段静态结果推出完成。

### 12.4 未决依赖、契约草案与 P3 输入

| ID | 尚缺证据/能力 | 本轮返回与后续输入 |
|---|---|---|
| U01 | 实际项目memory工具、schema/备份恢复能力 | `UNMET_DEPENDENCY`；只读代码/接口证据，Owner具体备份方案；禁止直接数据库客户端替代 |
| U02 | Codex宿主后台进程生命周期 | `UNMET_DEPENDENCY`；可交Owner前台终端，不虚构后台参数或把进程存在当启动成功 |
| U03 | 真实解密、OS注入及pwsh平台 | `NOT_TESTED`且Owner-only；仅P1公开候选代码及合成证据，不读取真实值 |
| U04 | Owner具体批准后的可执行路线 | hook仍block；`BLOCKED_EXECUTION_ROUTE`，无receipt或绕过；P3/P4前需人工审阅决定 |
| U05 | 认证网络、8项实际MCP/服务、Git远端写操作 | `NOT_TESTED`；逐项所需授权/环境另行提供，不把离线或静态当服务ready |
| U06 | 脱敏catalog快照、真实EVAL框架和测量 | 缺失标UNMET/NOT_TESTED；SKIP不是PASS，baseline可为null/草案，不编造结果 |
| U07 | 正式AGENTS、规范、模板、检查器与CI入口切换 | `P3_NOT_APPLIED`；以资产表和候选差异为输入，做最小直接消费者调整 |

8项infra草案来自正式 `capabilities/infrastructure/mcp-server-governance/contracts/claude-skill.contract.yml`。每项保存旧条目、已复算旧摘要、新路径/description/body及新摘要、全文diff和恢复定位；没有把草案写回正式契约。契约容器路径暂保留原名，P3需将header、schema/检查器及直接消费者与获批路径/冻结修订一同审阅，不能单改8个file字段便宣称契约已原生化。

P3所需输入：明确的下一阶段指令；本轮37候选及共同说明、142案例、8契约草案和P1工具身份；ADR正文审阅/编号；正式保护面、契约/冻结、配置/AGENTS/CI等具体成组差异及所需Owner批准。还需明确硬阻断后的执行路线，并保留P4实际宿主信任/加载/canary、独立clone/worktree、Linux和真实服务证据的独立状态。P3不能顺带完成#499/#552，也不能因本轮候选通过跳过正式消费者与保护覆盖核对。

### 12.5 恢复与停止

37个原始源及旧契约恢复来源为 `20e2f24c352cf640d9dd33234b128ca897804b99:<source>`；每项原始/候选摘要及Git定位见对照/契约草案/资产表。候选与本轮证据尚未提交，其完整内容目前只在当前工作树；摘要和忽略目录脚本不是内容备份。若将来撤销P2，须先按最终验证记录复核身份，只处理本轮37技能、共享说明、9份证据以及报告/CSV的P2增量；不得连带删除P1候选、共享测试拆分或P0记录，不执行全树reset或递归清空。原始旧客户端内容仅供恢复/审计，不能覆盖候选新增安全约束而不审阅。

**P2候选制作与静态评审完成；正式入口、契约与冻结摘要保持不变。P3未开始，本轮在此停止。**


## 13. P3 执行记录（2026-09-18，部分完成/受阻）

### 13.1 授权、身份及正式状态

本轮Owner指令仅启动P3，不把P1/P2候选批准视为正式保护面批准。读取计划§4.5、P1/P2记录、资产表、37×8对照、142案例、387资源记录、8项infra草案及四处局部AGENTS后，确认本工作树HEAD仍为 `20e2f24c352cf640d9dd33234b128ca897804b99`，分支未变、暂存为空。

已有授权覆盖公开准备、候选修复与离线检查；正式D-017所有权/配置、冻结契约、元规则、ADR采纳及CI/测试退役没有具体批准记录。Owner对U04补充答复：**“尚无路线，保留阻断并完成准备”**。本轮未尝试正式保护面写入；未遭拒绝后换工具，也没有receipt、改权限模式、停用hook、个人配置修改或trust激活。

### 13.2 已交付准备与未完成边界

- [审阅/授权/恢复包](../evidence/codex-only-migration/p3-cutover-review.md)：目标保护面、已有授权、待批准集合、整组前置和分层恢复。
- [70目标逐项清单](../evidence/codex-only-migration/p3-cutover-files.json)及[具体差异](../evidence/codex-only-migration/p3-cutover-proposal.diff)：包括全部37同名技能、共享资源、P1原生配置/工具、5处AGENTS、ADR-040草案、政策/infra合同/schema及部分消费者。**分片草案，尚非可原子应用的完整patch**。
- [V4/V8–V13映射](../evidence/codex-only-migration/p3-gate-map.md)：旧保护→新承担者→正反证据→处置；原姿态不变。特别记录旧V4是step blocking但执行体全WARN/未strict，新严格失败与冻结硬门须另获具体批准。
- [直接消费者](../evidence/codex-only-migration/p3-consumer-inventory.json)及[旧测试逐项审核候选](../evidence/codex-only-migration/p3-test-retirement-review.json)：未删除、skip或调整自动发现；P1共享离线拆分保留。
- [语义增量](../evidence/codex-only-migration/p3-semantic-addendum.json)：2技能的INDEX/CLAUDE标签改为INDEX/AGENTS；共享说明去候选overlay，正式根解析；顺序/授权/交接不变。P2原对照和案例不覆盖，未机械重做142例，更未称模型执行。

原生候选位于独立 `.migration/codex-only/p3-proposal/`，P1/P2原候选字节不动。P1工具除guard增量外按当前身份复用。8项新合同的REQ/family/命名/HITL元数据保留；header、schema、checker与冻结值共同草拟，frozen_at只是建议值、未实际重新冻结。ADR-040仅核对命名空间并写候选，不占正式号或改变历史ADR状态。

尚未完成：V8–V10/V12替代的完整执行体及CI注册、MCP capability/指南/模板等全部正式消费者正文、旧测试安全断言完整接续与具名退役差异。没有请求对这个未闭合组作笼统批准，没有先撤blocking gate。正式切换清单里的各项均为DRAFT_NOT_APPLIED或REVIEW_REQUIRED，**不能将70份草案数量当作70项正式完成**。

### 13.3 本轮验证与发现

[入场身份](../evidence/codex-only-migration/p3-entry.json)与[验证记录](../evidence/codex-only-migration/p3-verification.json)保留具体命令及限制。

| 检查 | 新鲜结果 | 证据级别与限制 |
|---|---|---|
| P1 12候选/测试+9邻居、P2候选/证据摘要 | 全匹配 | 身份，不是宿主运行 |
| 37候选/296维/142案例 | 当前来源与候选相符 | STATIC_IDENTITY/REVIEW，非142次模型调用 |
| 8项旧及新description/body摘要 | 原算法重算16旧+16新全部匹配；新header/节标题同步 | DRAFT_ONLY；未实际freeze |
| 387资源记录 | 381必需路径仍存在，6原标EXAMPLE_ONLY单列 | overlay复核，正式U07未通过 |
| 新守卫回归 | 6项unittest PASS；Git全局参数2反例先RED后GREEN | 无外部服务、未宿主加载；UNKNOWN硬阻断，不新增通用shell解析器 |
| 原生技能/冻结checker | 15项unittest PASS；缺文件/坏YAML/重复键/缺资源/越界/摘要漂移/未知字段/不回显 | 合成fixture代码行为；尚未作为CI活动入口 |
| P1受控offline fixture复跑 | 122 passed in 14.77s | 原测试/插件/环境闭合；非P4独立部署 |
| 原生config checker | STATIC_PASS；session INCOMPATIBLE(never)；owner NOT_ASSESSED；host NOT_TESTED | exit0不表示批准或可执行 |
| 四个新增/修订Python文件ruff | PASS，3处import排序修正后 | 局部lint |
| [正式依赖扫描](../evidence/codex-only-migration/p3-active-dependency-scan.json) | 97个公开文件、663条旧路径命中 | raw命中包含历史与活动，需要逐项处置；明确NOT_CLOSED，非零依赖通过 |

发现按计划§2.4处理：旧Git守卫能拒绝 `git -C … checkout -b …`，P1候选未识别，是退役时会丢保护的直接迁移缺陷；只在P3候选增加Git全局参数UNKNOWN阻断。未修#552审批系统或#499后续门禁。V4阈值是既有事实，记录新门禁所需批准，不冒充已经解决历史问题。

失败轨迹未抹去：入场helper最初使用吞空白regex致16body比较失败，改为合同canonical regex后吻合；合成CRLF fixture曾重复转换换行，修fixture后通过；原生checker未知合同字段用例先失败后补拒绝；导出helper首次误把6条EXAMPLE_ONLY当必需路径后修正。没有改P2文件、放宽权限或删安全断言填绿。临时helper全在忽略目录，未成为正式CI/维护依赖。

### 13.4 未决项、恢复与停止

U01 memory备份、U02后台生命周期保持UNMET_DEPENDENCY；U03秘密/OS注入/pwsh、U05实际8MCP/网络保持NOT_TESTED；U06 snapshot/EVAL保持UNMET_DEPENDENCY/NOT_TESTED；**U04 BLOCKED_EXECUTION_ROUTE（Owner确认无路线），U07 NOT_CLOSED**。本轮没有业务权限/runtime/Prompt/SQL/catalog修改、秘密读取、真实服务探针、解密、OS凭据写入或生产操作。

恢复分两类：Git基线文件按SHA+具名路径；未提交P0–P2的63个公开文件已经完整备份到 `.mj-agent-local/p3-entry-public-backup.zip`，ZIP摘要和逐文件身份见p3-entry.json。HEAD没有后者，不能靠git restore重建。若未来恢复正式组，入口/所有权/配置/契约/CI/测试必须一起恢复，之后重新保留P1共享拆分；不全树reset、不递归清候选、不动其他worktree。旧客户端/投影资产仍留存且当前旧入口仍活动，尚不能称“已退役无调用”。

P4需要完整P3正式组、具体批准、可用执行路线、最终交付清单和人工宿主review/trust；当前不具备前置。本轮没有独立P4副本、宿主加载、模型canary、Linux/外部平台实测、issue/分支/暂存/提交/推送/PR。

**P3部分完成/受阻；正式切换未完成，在本阶段停止。Codex承担本轮准备与验证，无子代理。**

## 14. P4 前置核查记录（2026-09-18，未启动正式验收／前置受阻）

### 14.1 范围、当前身份及证据

Owner 本轮仅授权 P4，并明确：P3 关键前置不满足时只做只读核查、阻塞整理与累计记录，不创建正式验收副本、不拼 overlay、不返回 P3 实施。按此分支执行；使用 repo-scan 的只读事实核查方法，记录更新依据本轮明确授权，不启动下游流程。

当前工作树仍为 `D:/workspace/10-software-project/projects/mj-agent/maintain/codex-dev-mode-migration`，分支 `maintain/codex-dev-mode-migration`，HEAD `20e2f24c352cf640d9dd33234b128ca897804b99`。入场 staged=0，唯一 tracked unstaged 文件仍为 P1 的 `tests/unit/test_agents_sync.py`（1182行拆出）；134个未跟踪文件均逐项登记。共登记1002个公开文件的字节身份；秘密/示例凭据文件只登记路径，未读取正文。Git index 字节身份另行固定，未执行任何 Git 写操作。

| 本轮记录 | 用途与证据级别 |
|---|---|
| [入场身份](../evidence/codex-only-migration/p4-entry.json) | 根目录、Git 元数据位置、HEAD、status、index 摘要、1002公开文件身份及原资产表；`STATIC_IDENTITY` |
| [前置核查](../evidence/codex-only-migration/p4-prerequisite-verification.json) | 五项阻塞、目标新旧摘要、旧冻结复算、定向消费者扫描、实际 argv/环境/失败轨迹；只读观察，不是 L1–L5 验收 |
| [逐文件清理审阅表](../evidence/codex-only-migration/p4-cleanup-review.csv) | 404个不同路径，列用途、替代者、消费者证据、身份、恢复与授权；含保留/仅审阅项，**不是404个待删除文件**；全部 `cleanable=NO` |
| [记录一致性复核](../evidence/codex-only-migration/p4-record-validation.json) | 报告/CSV增量、旧值保留、P0–P3文件/index/HEAD保护及链接/记录结构核对；不是产品测试 |
| [资产处置表](../evidence/codex-only-migration/asset-map.csv) | 原324行×29列值全部保留，追加6个P4字段及4条证据记录，累计328行；旧阶段状态保留为历史，当前结论看 `p4_status` |

### 14.2 五项前置逐项结论

| 前置 | 当前直接证据 | 结论及缺口 |
|---|---|---|
| PRE-01 正式入口、所有权、配置、37技能及资源成组切换 | 70项草案与70项正式目标均匹配P3记录；正式只有18个生成载体，37项完整入口仍在候选区。`AGENTS.md:43` 仍声明生成物所有权；`.codex/config.toml:1` 仍是 GENERATED | `BLOCKED_PREREQUISITE`；缺完整且已应用的正式交付组，候选数量不代表交付 |
| PRE-02 八项 infra 契约路径/header/schema/checker/消费者/冻结同步 | 正式合同仍为 `claude-skill.contract.yml`，8个路径仍指向 `.claude`；16项旧description/body摘要复算匹配。新合同/schema/checker仍是草案 | `BLOCKED_PREREQUISITE`；缺具体批准、正式同步与实际冻结执行记录；旧摘要匹配不代表新冻结生效 |
| PRE-03 V4、V8–V13保护和旧pytest处置 | `.github/workflows/ci.yml:180,354,358,362,365,394,426` 仍调用旧检查/生成链；P3门禁表的NOT_READY未解除。18个旧测试文件摘要不变，共422个测试定义仍在审核清单 | `BLOCKED_PREREQUISITE`；缺完整替代执行体、正式注册与正反证据、具名断言替换/退役批准。P1安全拆分保留，不删除断言 |
| PRE-04 U07及正式消费者闭合 | 277项消费者中245项REVIEW_REQUIRED、32项CONCRETE_DRAFT；配置5个memory launcher仍读 `.claude`；offline boundary、context audit、fixture runner与CI仍有旧活动依赖 | `BLOCKED_PREREQUISITE`，U07=`NOT_CLOSED`；候选/临时审阅脚本不能充当正式消费者。定向扫描保留原始命中，未将历史/负例命中一概算活动，也未声称全仓零依赖 |
| PRE-05 正式授权及U04路线 | P3审阅包仍为PARTIAL_REVIEW_PACKET_NOT_APPLICABLE，70份具体差异只是分片草案；Owner此前“尚无路线，保留阻断并完成准备”仍是最新具名路线证据 | `BLOCKED_PREREQUISITE`；正式范围授权未补齐，U04=`BLOCKED_EXECUTION_ROUTE`。本轮指令不补发批准，不表示hook解锁或宿主加载 |

没有发现能将P3改判完成的新实际证据。保留现有门禁不是原生接续已完成；本轮也未尝试受保护写入来制造技术拒绝。无完整正式交付组，因此不创建独立Git副本、clone、临时linked worktree或测试索引，不组装候选overlay，不运行宿主canary。

### 14.3 身份、原有证据与失败轨迹

| 只读核验 | 实际结果 | 解释 |
|---|---|---|
| P1候选/两测试 | 12/12 SHA匹配 | 含共享拆分；不重跑122项历史测试 |
| P1 AST对照基线 | 43个移出定义（42测试+1helper）和剩余定义均不变，无原定义遗漏 | 只比较AST，不执行pytest；保留原有74个参数化离线case的历史记录 |
| P2候选/证据 | 38/38候选、8/8绑定证据摘要匹配 | 37技能八维296维/142静态案例保持原证据级别，不是模型执行 |
| P3草案/正式目标 | 70/70草案、70/70正式目标当前身份匹配 | 正式目标缺失项仍缺失，已存在项仍旧状态；不是70项完成 |
| P3入场公开文件 | 除累计报告/CSV的P3已记录增量外，61/61不变 | 本轮不会覆盖任何P0–P3候选或测试 |
| 旧测试审核文件 | 18/18摘要匹配 | 422个定义未获批退役；未skip、删断言或改发现范围 |
| 旧infra冻结 | 8项source身份+16项冻结摘要匹配 | `OLD_FREEZE_IDENTITY_ONLY`；没有新冻结批准/执行 |
| P3公开恢复ZIP | ZIP摘要、63个条目集合及逐项摘要匹配 | 完整内容恢复源仍可读；没有解包覆盖当前树 |

环境为 Windows 11 `10.0.26200`、Git `2.53.0.windows.1`、既有Python `3.13.5`。解释器为 `../../develop/.venv/Scripts/python.exe`，本轮使用 `-I -X utf8 -B`；只复用现有可执行文件，不修改该工作树或安装依赖，不读取用户环境值。

实际命令包括 `git rev-parse`、`git branch --show-current`、`git status --porcelain=v1 -uall`、`git diff --stat`/`--cached`/`--name-only`、`git worktree list --porcelain`、`git ls-files`、`git show <SHA>:tests/unit/test_agents_sync.py`，以及对明确公开文件执行的 `rg -n`。采集器内Git命令带 `--no-optional-locks`，原始参数及退出码见前置核查JSON。临时 `.mj-agent-local/p4_prerequisite_audit.py` 通过上述Python执行，仅读取公开内容并导出记录；其摘要已绑定，不是正式维护工具、验收runner或恢复权威。另用内联Python更新记录、合并清理表中重复路径，并执行收口一致性核对。

本轮工具/记录失败保留：首次JSON摘要输出未指定UTF-8，被cp1252编码拒绝；加 `-X utf8` 后读取成功。首次rg将context audit及fixture runner猜在错误目录，报路径不存在；经 `rg --files scripts` 找到 `scripts/check_ai_context_audit.py`、`scripts/sdd/fixture_runner.py` 后重扫。导出文字一处将测试定义误写547，按实际求和422更正，结构化计数原本就是422。收口脚本最初按 `## 14.` 分割章节，误匹配 `### 14.1`，导致AC存在性断言失败；改为完整主标题定位，报告中的AC内容不变，收口命令固定为上述Python参数运行 `.mj-agent-local/p4_record_validate.py`。以上都是取证/记录问题，不是产品测试失败；没有据此改代码、门禁或案例。P1/P3原有RED→GREEN和导出失败轨迹原样保留，未借本轮身份匹配刷新成“本轮测试通过”。

### 14.4 逐层、逐AC与平台状态

| 层次 | P4结果 | 既有材料与尚缺证据 |
|---|---|---|
| L1 来源完整性 | `BLOCKED_PREREQUISITE` / `NOT_TESTED` | 37候选/资源/处置表可追溯；尚缺完整正式交付与消费者闭合 |
| L2 原生独立性 | `BLOCKED_PREREQUISITE` / `NOT_TESTED` | 未创建独立副本，未排除旧客户端进行运行；当前正式依赖仍在 |
| L3 确定性行为 | `BLOCKED_PREREQUISITE` / `NOT_TESTED` | P1/P3合成测试仅为历史候选证据；本轮未运行非法配置/保护/脱敏/异常/恢复/重入行为 |
| L4 流程语义 | `BLOCKED_PREREQUISITE` / `NOT_TESTED` | 复核P2对照/案例及P3增量身份；本轮候选内容未变，无变化部分需补评；未进行正式交付验收或模型调用 |
| L5 真实宿主 | `BLOCKED_PREREQUISITE` / `NOT_TESTED` | 指令/37技能发现、5族显式调用、近邻误触发、Git/保护文件/删除演练、hook/rule允许与拒绝均未执行；缺P3交付、路线及工程师独立信任审阅 |
| L6 外部环境 | `NOT_TESTED` / `OUT_OF_SCOPE` | 不连接外部服务，不执行真实凭据或业务操作 |

| AC | 当前验收结果 | 本轮证据或缺口 |
|---|---|---|
| AC-01 | `BLOCKED_PREREQUISITE` | 37同名候选保留；正式仍18个旧生成载体 |
| AC-02 | `BLOCKED_PREREQUISITE` | 八维/142案例身份匹配仅STATIC_IDENTITY，正式行为未验收 |
| AC-03 | `BLOCKED_PREREQUISITE` | 所有权仍为生成链，原生直接维护未成立 |
| AC-04 | `BLOCKED_PREREQUISITE` | 原生MCP候选未正式部署；无P4独立路径/拒绝/脱敏运行证据 |
| AC-05 | `BLOCKED_PREREQUISITE` | 原生必要保护未全体接续，宿主证据缺失 |
| AC-06 | `BLOCKED_PREREQUISITE` | 独立副本与规定路径/宿主均未测试 |
| AC-07 | `BLOCKED_PREREQUISITE` | U07未闭合；业务/语言规范及正式业务资产保持原样 |
| AC-08 | `NOT_TESTED`（P5未执行） | 404路径全部不可清理，未获得删除授权或删除资产 |
| AC-09 | `BLOCKED_PREREQUISITE` | 必需L1–L5没有正式验收结果，不把未运行记FAIL/PASS |
| AC-10 | `BLOCKED_PREREQUISITE`（本轮恢复整理已完成） | 基线与未提交成果恢复来源分列；原生上手/维护交接仍待正式切换 |
| AC-11 | `STATIC_PASS`（仅本轮范围切片） | 仅记录更新；保留原测试拆分，无业务/治理/审批平台实施；最终AC仍待后续 |
| AC-12 | `NOT_TESTED`（P6未执行） | 无暂存/提交/推送/issue/分支/PR/合并，未宣称版本交付 |

Windows当前根目录只实测了文件读取、摘要、AST和记录处理。Windows正式根/子目录/含空格路径、clone、linked worktree及launcher/宿主场景全部 `BLOCKED_PREREQUISITE; NOT_TESTED`；Linux CI/检查器同样未测试。Linux launcher不是自动新增支持范围；其他平台未测试。不得用当前Windows文件核查、P1旧fixture或某一平台结果替代这些场景。项目与hook信任、实际宿主版本/激活状态本轮未核验，不读写个人配置，不自动信任或切换权限。

### 14.5 U01–U07、范围判定及清理边界

| ID | 最新状态 | 本轮新证据／所缺输入 |
|---|---|---|
| U01 | `UNMET_DEPENDENCY` | 无新服务探针；缺sanctioned memory schema/备份恢复能力及Owner具名方案 |
| U02 | `UNMET_DEPENDENCY` | 无宿主进程试验；缺真实后台生命周期证据 |
| U03 | `NOT_TESTED` | 秘密/OS注入保持Owner-only；pwsh平台验证未补，不执行解密/OS写入 |
| U04 | `BLOCKED_EXECUTION_ROUTE` | 无新具名可执行路线；聊天批准、Full access、静态规则输出均不能改变此状态 |
| U05 | `NOT_TESTED` | 无8 MCP、认证网络或远端写验证；L6不在本轮，不要求提供真实凭据 |
| U06 | `UNMET_DEPENDENCY / NOT_TESTED` | 未取得脱敏快照、真实EVAL框架/测量；无SKIP冒充PASS |
| U07 | `NOT_CLOSED` | 当前正式config/CI/checker旧依赖与245待审消费者直接印证；缺完整组差异、授权、路线及实际执行 |

按计划§2.4，本轮发现的是已知P3交付缺口与未满足依赖，未新确认需要修复的迁移缺陷。旧V4的WARN退出语义、#499/#552剩余事项按已有归类保留，不在P4前置分支接手。记录输出的编码/路径/文字计数错误就地纠正，不涉及受保护面。

文档决策沿用计划§8的十类：Plan、SPEC、ADR、RUNBOOK、GUIDE、STANDARD、Local ISSUE、ASSESSMENT、CHANGELOG、INDEX本轮均 `None`；仅更新既有累计报告/资产表及其证据。没有代码命名/路径、SQL、DDD、runtime正文或catalog修改，相关反向扫描不触发；本轮旧入口反扫仅服务前置核查。计划仍有效，但P4入口不满足；不因此修计划或开启P3。

清理表逐文件标注的消费者来自已有资产/消费者清单及当前定向扫描，未完成零活动消费者证明。保留规范与共享安全工具标为KEEP_OR_REVIEW_ONLY；旧客户端/纯适配链/候选副本仅为CONDITIONAL_FUTURE_REVIEW。全部不可清理：既无P4必需验收，也无删除批准。`sdd/adapters/`有效规范不整目录排除；秘密/个人文件及聚合排除项只在资产表登记元数据，不进入可删除列表。候选仍是未提交成果和证据来源，不能因“临时”二字提前删除。

### 14.6 恢复来源、收口与停止

1. **Git基线文件**：从 `20e2f24c352cf640d9dd33234b128ca897804b99:<具名路径>` 恢复；原blob身份见资产表。该基线不包含P0–P3未提交成果，尤其不能直接恢复整份 `test_agents_sync.py` 而抹去P1拆分。
2. **未提交P0–P2公开成果**：已核验 `.mj-agent-local/p3-entry-public-backup.zip`，SHA-256 `30cce1caf0366ab737151b1c47b3b52aa1bf4b538d19aadc2aaaaaad9528dd99`；63条内容均与p3-entry记录相符，含P1两测试、P1/P2候选、记录和计划。该ZIP中的报告/CSV是P3入场版本，不可当成P3最终版本覆盖。
3. **P3草案/证据**：完整内容仍在本工作树具名文件，身份由P3清单和p4-entry绑定；尚未提交，旧ZIP不覆盖P3新增内容，文本diff/摘要也不是完整内容备份。P3最终累计报告和CSV在本轮更新前单独备份到 `.mj-agent-local/p4-entry-cumulative-backup.zip`，SHA-256 `35e1b6b26ee864f4f649868c5ea0517d885dad289fd4ae1095aa506bae719d0a`，仅2个公开文件，不含Git元数据，不是独立验收副本。
4. **本轮记录恢复**：上述两文件备份可用于具名撤销P4累计记录增量；4份新P4证据按收口清单与当前文件保存。所有恢复均须先复核身份并保留新增成果，不全树reset、不递归清候选、不修改其他worktree。正式组未应用，无需回滚正式切换。

收口核验保留入场所有公开文件；除报告/CSV外，已有文件字节不变，HEAD与index不变，staged仍为空，tracked diff仍只有P1测试拆分。实际检查结果及输出文件身份见 `p4-record-validation.json`。本轮未运行pytest/lint/mypy/模型或宿主测试；仅对新增记录做结构、链接、前后身份及CSV旧值保留检查。

后续重进P4所缺输入是：完整且已实际应用的P3正式组与最终交付清单、具体范围批准、8项冻结同步执行、必要门禁/安全断言接续证据、U07消费者闭合以及可用U04路线。工程师的项目/hook信任审阅与宿主加载仍须单独留证。这里只列缺口，不请求对未闭合组作笼统批准，也不自动回到P3。

**P4 未启动正式验收／前置受阻；技术迁移未验收。累计记录更新后停止，不进入P5。**


## 14. P3 续行：完整审阅包与人工应用路线（2026-09-18，未应用）

本节是当前状态，§13为此前部分准备记录。Owner追加“补齐切换差异、门禁和消费者闭合准备”，
并选定“Codex准备完整包 → Owner具体批准并本机人工应用 → Codex验证”。路线选择不等于批准全部保护面。

- 冻结组：G-P3-ATOMIC；HEAD `20e2f24c352cf640d9dd33234b128ca897804b99`；188项（42新增/130修改/16必要旧测试删除提案）。
- 补丁 SHA256 `abdf11bc9fc44286ab2b5cc32294e7385d0af97c8b8dc7d6c099210cd6734741`；逐文件/授权/恢复见 evidence/codex-only-migration/p3-cutover-files.json 与 p3-authorization-map.json。
- 覆盖37技能与共享资源、原生配置/工具、根+4 AGENTS、定向ADR-040、政策/维护声明、8 infra freezes/header/schema、MCP及必要跨cap直接消费者、V4/V8–V13、模板/索引/扫描域/stale-docs/build-ignore/EOL。
- P2 37/296/142与既有候选身份保留。8旧16摘要和8新16摘要重算吻合；381必要资源+6示例分开。P3仅两处技能label及共享正式根路径说明的addendum，不声称重新运行模型案例。
- 54项合成离线测试通过；候选schema/contract/trace/自动索引/native gates/文档/ruff/离线边界通过。跨仓与归档扫描仍WARN，原树对照保留。命令、cwd、输出和证据级别见p3-completion-verification.json。
- `git apply --check` 通过；逆向恢复补丁在非Git静态夹具上的`--check`通过。没有执行apply、暂存、提交、推送、PR、开分支/issue或P4。
- V4严格失败、新增native测试blocking、V12跨生成拓扑join退出、16旧专属测试具名处置须明确审批；V8–V11 blocking保留，V13 warning保留。没有先撤门禁，没有SKIP填绿。
- P1共享离线测试仍独立；sdd fixture/comparator共用断言、biz/secret prose pins保留。自动发现旧断言的替换/删除已进入同组具体差异，尚未实际删除。
- 新发现迁移缺陷：P1 guard漏9个新维护权保护目标，RED→GREEN；transitive import漏from-scripts，RED→GREEN。diff格式首轮缺new/deleted mode被只读check拒绝，修正格式后通过；没有权限/工具绕过。
- U04：MANUAL_ROUTE_SELECTED / PENDING_GROUP_APPROVAL_AND_OWNER_APPLICATION；自动受保护写入仍BLOCKED_EXECUTION_ROUTE。U07：PREPARED，正式NOT_CLOSED。U01/U02/U06继续UNMET_DEPENDENCY或NOT_TESTED，U03/U05保持NOT_TESTED。
- 完整proposed pytest、实际CI/宿主加载/hooks/model canary、服务凭据/平台矩阵NOT_TESTED。tracked-only runner未放宽，未暂存候选，未引入P2临时脚本为正式依赖。
- 恢复：Git HEAD只用于已提交基线；当前非ADD目标字节见p3-preapply-public.zip；63项P0–P2备份见p3-entry.json；本续行入口88项备份见p3-completion-entry.json。禁止reset --hard/clean，不能覆盖P1未提交拆分。
- 正式状态：**P3部分完成/待人工应用与验证**。审阅包准备已完成，旧入口仍活动；不宣称迁移切换完成，不进入P4。完成冻结后停止本工作树自动写入。

当前申请：Owner按p3-cutover-review.md逐项审阅A1–A6，明确批准G-P3-ATOMIC整组；然后人工检查身份、git apply --check并应用。批准或应用失败均停止，重新审阅，不改权限、不停hook、不创建receipt。


## 15. P3 人工应用后核验（2026-09-18，当前状态）

本节取代先前“未应用”的当前状态；此前P4前置检查记录仅为历史，不代表执行了P4。
Owner已在聊天明确批准冻结A1–A6整组，随后提供本机PowerShell应用截图。Codex只做应用后核验、
证据更新与格式收尾提案，没有代为执行git apply。原冻结ZIP、补丁与manifest保持原样。

- HEAD仍为20e2f24c352cf640d9dd33234b128ca897804b99，暂存区为空；188项全部落地：87文件逐字节相同、85文件仅CRLF/LF不同、16项批准的旧机制测试已删除。没有正文差异/漏应用项。
- 原始字节摘要差异如实保留在p3-postapply-verification.json；不把LF归一化相同冒充raw SHA相同。Git core.autocrlf=true；10个文件当前违反已经批准的显式LF属性。此前draft也含CRLF，且git apply同时修改gitattributes并不保证所有目标即时按新属性落盘。没有更改Git配置来压警告。
- 正式根54项合成离线测试通过；原生技能/资源/5入口/45消费者及传递引用/MCP/守卫/8 infra freezes、capability schema/trace/contracts、自动索引、文档及lint通过。381必需资源存在，6示例不计PASS。PowerShell四脚本解析、Node wrapper语法检查通过，未执行启动器或凭据写入。
- 实际新失败：git diff --check因tests/unit/test_sdd_development_agent.py末尾多余空行返回2。准备11文件格式补丁（10 LF转换+1 EOF空行），没有改正文、断言或权限，尚未应用。新旧恢复补丁与格式补丁的只读check通过。见p3-format-followup-review.md。
- 完整pytest未执行：受控runner对tests/unit返回“pytest input does not exist: tests/unit/test_agents_sync.py”（批准删除已落地但索引仍列旧文件）；对新test_codex_native.py返回“not Git-tracked”。不暂存、不创建临时索引、不绕过runner，保留BLOCKED_TEST_INPUT_NOT_EXECUTED。54 unittest不能替代完整pytest或P1全回归。
- 跨仓引用与归档扫描的历史WARN保留；没有放宽检查、删有效断言或用skip填绿。src仅局部AGENTS变化，业务runtime/Prompt/SQL/catalog没有变更；未批准目标无新增tracked差异，P0–P2输入在已批准目标之外摘要未变。
- U04原切换组=MANUALLY_APPLIED_CONFIRMED；自动受保护写入仍BLOCKED_EXECUTION_ROUTE，新格式组仍待Owner审阅人工应用。U07=FORMAL_STATIC_CONSUMER_CLOSURE_PASS；实际CI/宿主/服务不由此推定通过。U01/U02/U06继续UNMET_DEPENDENCY或NOT_TESTED，U03/U05保持NOT_TESTED。
- V4/V8–V13映射按批准稿实际落地；V12具名机制退役，V13仍warning，必要继任测试进入Tests的效果已批准，但实际CI与完整Tests证据尚缺。不能沿用旧gate streak。
- 恢复源仍分三层：HEAD只覆盖已提交基线；p3-preapply-public.zip覆盖切换前准确工作字节（含P1拆分）；p3-entry-public-backup.zip保留P0–P2。格式组另存p3-format-preapply-public.zip。报告/资产表更新前快照另存p3-postapply-records-before-update.zip；冻结包内的原报告/表未改。
- 当前asset-map.csv和本报告为累积记录，合法更新后不再等于旧freeze的这两项摘要；原冻结身份应在不可变p3-review-package.zip内核对。其他冻结文件保持不变，原切换补丁已应用，禁止重放。
- **P3部分完成：正式切换已应用，格式验收未过、完整pytest前置受阻；不宣称P3全部完成。** 没有改权限、信任/hook、个人配置，没有真实秘密/服务/生产操作，没有提交推送PR或进入P4/P5。

下一步仅审阅并人工应用11文件格式补丁，再由Codex核对摘要、行尾与diff检查。完整pytest前置不能通过本格式补丁解决，后续路线必须继续遵守不暂存/不进入P4的当前限制。


## 16. P3 格式收尾应用后复核（2026-09-18，当前状态）

用户确认已人工应用11文件格式补丁；Codex独立读取实际文件再次核对：11/11目标SHA256相同，
其余177项与上一轮核验身份相同，显式LF属性违规为0，git diff --check返回0。HEAD/分支不变，
暂存区为空。本轮没有自动改写正式资产，没有重复应用补丁、暂存、提交或推送。

- 格式补丁身份：`c617f87d0481b0569cf10e116e83b7b7ae93ba9c241764c1871767f42b39dd6c`。逐项实际摘要和命令见`p3-format-completion.json`。
- 上轮54项受控离线测试和正式静态检查证据保留；本次只有LF转换和一个EOF空行，正文、权限、
  契约及测试断言未变化，因此未机械重复全套测试，也没有把此前证据伪装成本轮执行。
- **U04修正为MANUAL_ROUTE_EXECUTED_VERIFIED**：正常人工路线没有观察到技术保护拒绝。
  需Owner批准动作仍保持原有硬阻断语义，但这不等于当前已选路线处于BLOCKED_EXECUTION_ROUTE；
  不能只因approval policy为never推断发生拒绝。先前阻断记录保留为历史，未停hook、改权限或创建凭证。
- U07维持FORMAL_STATIC_CONSUMER_CLOSURE_PASS。完整pytest仍未验证：此前受控runner的
  tracked-only前置阻断记录保持有效；本次没有改变索引或测试输入前置，不以格式通过推定pytest通过。
  其他服务、memory备份、生命周期、凭据平台与EVAL依赖仍按原U01–U03/U05/U06保留未验证状态。
- 当前整体状态：**P3正式切换与格式收尾已应用并核验；P3仍部分完成，完整pytest未验证**。
  实际CI、宿主/模型、独立部署及平台验收未执行，不宣称P4、L1–L5或迁移全部完成。
- 当前整组恢复差异为`p3-postformat-group-recovery.diff`，从本次188项实际身份回到原切换前工作字节；
  只读git apply --check通过，未实际恢复。Git行尾可能影响恢复后原始字节，仍必须按
  `p3-preapply-public.zip`逐项核对。HEAD仅用于已提交基线，P1共享拆分及未提交P0–P2仍用各自备份。
  旧整组/格式补丁及原冻结包保持原样作为历史，不重放；禁止reset --hard/clean。
- 累计报告与资产表已更新；更新前记录存于`.mj-agent-local/p3-format-completion-records-before-update.zip`。
  没有新阶段授权，本阶段可执行验证结束后停止，不进入P4/P5。

## 17. P4 独立副本与离线验收（2026-09-18，部分验证／技术迁移未验收）

### 17.1 重新入场与五项前置

本轮依据Owner在P4对话补充的§16交接执行，未沿用历史阻塞结论。根、分支、HEAD仍为本报告§2具名身份；原索引为空。当前188项全部与`p3-format-completion.json`一致：42新增、130修改、16项已批准旧机制测试删除；11文件格式修订及其余177项均匹配。冻结包、旧补丁和恢复差异仅作为历史/恢复证据，没有重放。

| 前置 | 本轮复核 | 判断 |
|---|---|---|
| 正式入口/所有权/配置/37技能/资源成组切换 | 188项实际字节/删除状态匹配；37个正式同名原生入口与共享资源存在；根及局部AGENTS、ADR-040已落地 | 已满足独立离线验证入口，不等于宿主已加载 |
| 八项infra合同同步 | 正式新合同/schema/header/检查器/消费者属于已批准A1–A6，当前身份匹配；独立副本原生技能/冻结检查通过 | 正式同步及静态冻结验证成立；不以此推断服务实测 |
| 必要保护/旧测试处置 | CI对应V4/V8–V11及V13继任已落地，V12按批准退役；16具名测试已删除，混合安全测试保留 | 可进入P4完整pytest；本轮实际测试又发现并修正4处旧客户端测试字面量，见§17.4 |
| U07正式消费者 | 已有正式静态闭合记录；独立副本排除旧客户端后，资源/原生消费者检查仍通过 | `FORMAL_STATIC_CONSUMER_CLOSURE_PASS`；另修GLOSSARY人工文档入口遗漏，不能把执行消费者检查当全体文档证明 |
| 正式范围批准/U04 | 当前Owner交接确认A1–A6及格式补丁人工应用，实际188项身份佐证 | `MANUAL_ROUTE_EXECUTED_VERIFIED`；未观察新技术拒绝，不因approval_policy=never臆造拒绝 |

完整pytest原先受tracked-only输入前置阻断，本轮按已明确授权在一次性副本建立索引后实际运行。原树不补暂存，不放宽runner。使用repo-scan只读核查、flow-verify离线矩阵；两处直接迁移遗漏按flow-implement简单根因修复路径处理，无子代理，不补做#499/#552。

### 17.2 独立副本、来源、索引和公共依赖

- 副本绝对路径：`C:/Users/Admin/AppData/Local/Temp/mj-agent-p4-20260918-ij3anyxq/native acceptance`。位于原仓之外，目录名自带空格，不继承原工作树`.git`指针。
- [副本清单](../evidence/codex-only-migration/p4-copy-manifest.json)登记817文件逐项来源、SHA256与tracked/未跟踪来源；43个未跟踪交付文件纳入。按当前工作字节复制，没有用HEAD/P0–P2备份/P3草案拼装交付。
- 99项排除包含具名旧客户端/投影资产、16项已不存在的获批测试、2个加密秘密包。`.claude`、CLAUDE入口、`.mcp.json`、lock/renderer/sync等均不在副本；不复制`.migration`、个人配置、安装产物或一般缓存。公开`.example`模板按既有交付文件保留，不含真实秘密。
- 6个仍有效的Python、BDD/TDD、contract、Docker、Prompt、runtime-skill adapter明确保留，新增原生规范同样保留，未整目录排除`sdd/adapters`。
- 仅副本执行`git init`及`git -c core.autocrlf=false add --all -- .`，形成817文件测试索引；没有交付提交、远端或原树索引写入。随后两文件最小修复只在副本更新对应索引。受控runner及其tracked-only、环境封闭、插件版本限制原字节不变。
- **公共依赖例外有明确批准**：完整token-estimator测试首次缺词表会下载；Owner明确答复“允许这两个已核验词表作为离线依赖”。仅复制`cl100k_base`与`o200k_base`公开词表，SHA256分别为`223921b76ee99bde995b7ff738513eef100fb51d18c93597a113bcffe865b2a7`、`446a9538cb6c348e3516120d7c08b09f57c36495e2acfffe59a5bf8b0cfb1a2d`，与既有tiktoken代码声明一致。来源、目的与长度见[依赖记录](../evidence/codex-only-migration/p4-offline-dependencies.json)；只读develop的这两个公开文件，不修改其他工作树、不联网、不复制其他缓存。

环境为Windows 11 10.0.26200、Python 3.13.5（既有`../../develop/.venv/Scripts/python.exe`）、Git 2.53.0.windows.1；pwsh/node复用既有安装。未安装或升级。父进程仅转交闭合的非秘密系统变量，runner继续创建隔离profile并锁定插件，pytest从副本`src`加载项目。命令/解释器/cwd/退出码/原始输出/耗时均记在各`p4-results-*.json`。

### 17.3 实际验证结果

| 命令/范围（均在独立副本） | 实际结果 | 限制 |
|---|---|---|
| `python -X utf8 -B scripts/sdd/run_offline_pytest.py tests/unit -q --tb=short` 初次 | 880 passed、6 failed、1 skipped，19 subtests passed | 真实红态保留在[p4-results-unit.json](../evidence/codex-only-migration/p4-results-unit.json)，不是输入前置阻断 |
| 同命令，最小修复后 | **886 passed、1 skipped**，19 subtests passed | [当前unit记录](../evidence/codex-only-migration/p4-results-unit-after-fix.json)；skip为非Windows事件循环测试 |
| 同runner `tests/eval -q --tb=short` | 93 passed | 既有离线用例，不代表U06真实EVAL测量 |
| 同runner `tests/bdd -q --tb=short` | 13 passed、7 skipped、48 warnings | 外部依赖7项按既有政策skip；gherkin依赖弃用警告保留 |
| 同runner `tests/integration -q --tb=short` | 4 passed、5 skipped | biz live 5项未验证 |
| 同runner `tests/smoke -m smoke -q --tb=short` | 18 skipped | 没有任何smoke运行能力通过；仅验证结构化离线策略 |
| 同runner `tests/contract -m contract -q --tb=short` | 63 passed、1 skipped | Windows无符号链接权限，该项未验证 |
| `python -m ruff check` / `python -m mypy src/mj_agent` | PASS / 48 source files PASS | [lint/type记录](../evidence/codex-only-migration/p4-results-lint.json)；修复后针对测试文件再跑ruff通过 |
| 原生skills/resources、entries/consumers、MCP/enforcement、offline boundary | `STATIC_PASS` | 副本无旧资产/候选兜底；不是宿主激活 |
| capability schema、trace、contracts、自动索引、frontmatter、loop refs | PASS | 对应检查器原始命令与输出见[静态记录](../evidence/codex-only-migration/p4-results-static.json) |
| wikilinks | 初次GLOSSARY→CLAUDE 1 WARN；修复后0 unresolved | [修复检查](../evidence/codex-only-migration/p4-results-fix-checks.json)；未降级门禁 |
| 跨仓/归档扫描 | 既有跨仓13引用/10文件WARN；独立副本归档21 WARN/0 FAIL | 原树历史为22 WARN，扫描集合不同不称“修复1项”；未修改历史记录填绿 |

六带最终合计 **1059 passed、32 skipped**，另19 subtests passed（不重复计入1059）。[其余测试带记录](../evidence/codex-only-migration/p4-results-bands.json)保留全部skip原因。没有无理由新增skip，没有直接pytest绕过受控runner。现有fixture-runner单元测试会在隔离临时目录建立极小合成Git提交/clone；这是既有测试行为，不是对原树或817文件验收交付创建提交，不能代替交付clone验收。

### 17.4 两项最小修复、红绿与恢复

| 缺陷/AC | 原因与最小改动 | 新证据 |
|---|---|---|
| 测试调用迁移遗漏（AC-05/07/09） | `fixture_runner`正式只接受codex，但`tests/unit/test_sdd_development_agent.py`辅助函数和失败恢复场景共4处仍传claude或期待旧目录；只改为codex，既有断言/测试结构保留 | 原6失败→完整unit886通过；AST在4处文字替换后完全相同，未删测试或断言 |
| 术语入口迁移遗漏（AC-03/06/07） | 排除CLAUDE后GLOSSARY断链，且同一文件若干活动定义仍引导旧技能/配置/hook；只同步这11处定义/关联行到现有原生事实，历史来源说明保留 | 独立副本链接0 unresolved；原生执行消费者复检通过；不改政策、schema或业务规则 |

两项均属于计划§2.4明确的迁移造成断链/直接消费者遗漏，本轮已有最小修复授权覆盖；未触及受保护守卫、配置、冻结、门禁或runtime正文。修复前备份`.mj-agent-local/p4-minimal-fixes-before.zip`，SHA256 `6356316cbf4e77bfb8a045883c7096cddf2296ea864f8873ba9f1c3f3cf5ced5`。具体新旧身份、[差异](../evidence/codex-only-migration/p4-minimal-fixes.diff)及[恢复差异](../evidence/codex-only-migration/p4-minimal-fixes-recovery.diff)由[p4-minimal-fixes.json](../evidence/codex-only-migration/p4-minimal-fixes.json)绑定。188项中只有这一个测试文件发生P4增量，另外187项继续匹配§16；GLOSSARY为原188项之外的已论证直接消费者修复。

没有用修复吞异常、改变业务语义、放宽runner、改skip或门禁填绿。P1共享测试文件保持本次入场（即已批准P3接续后）的完整字节身份，P0–P3候选和既有证据不覆盖。

### 17.5 L1–L5、路径与保护分层

| 层次 | 当前结论 | 证据及未覆盖范围 |
|---|---|---|
| L1 | `STATIC_PASS` | 37同名技能、381必需资源存在、6示例单列；817文件逐项来源/摘要与处置，43未跟踪交付纳入；未用候选替代正式资产 |
| L2 | `PARTIAL_PASS` | 排除旧客户端/生成链/候选后的独立Git副本，根/子目录/空格路径可解析并通过全部已选离线测试；完整交付clone/linked-worktree仍`NOT_TESTED` |
| L3 | `PASS_WITH_DECLARED_LIMITS` | 6个受控测试带实际运行；非法配置、秘密不回显、缺失/异常输入、保护、恢复与重入沿用安全用例；32项skip未验证，不能称无条件全覆盖 |
| L4 | `STATIC_PASS` | [语义复用](../evidence/codex-only-migration/p4-semantic-reuse.json)：37项当前摘要逐项匹配P3语义增量；296维/142案例维持静态证据；P4技能正文未变，不机械重跑，不计模型调用 |
| L5 | `NOT_TESTED / UNMET_DEPENDENCY` | 尚无本独立副本的工程师trust/hook审阅、无服务启动宿主路线和实际模型canary证据；既有桌面会话技能清单、CLI help与代码测试都不能替代 |
| L6 | `OUT_OF_SCOPE / NOT_TESTED` | 未连接真实服务、读取真实秘密或执行业务副作用 |

[路径与规则记录](../evidence/codex-only-migration/p4-path-and-rule-checks.json)含26次实际组件命令：Windows副本根与`tests/unit`子目录均从带空格路径解析检查器；正式MCP启动命令在闭合无凭据环境返回`[MISSING] MJ_AGENT_PG_MEMORY_DEV_URL`/exit3，停于npx之前。直接guard stdin载荷观察到只读允许、G1拒绝、Git发布/保护文件编辑硬阻断、损坏JSON拒绝；所有被判定命令均只是字符串，没有真的提交、推送、分支、删除或编辑保护文件。

本机CLI `0.147.0`的`execpolicy check --rules <副本规则> -- <命令tokens>`实际返回push=prompt、checkout -b=forbidden；git status没有命中规则，仅记录`NO_MATCH`，不冒称宿主授权。直接guard ALLOW协议为空stdout/exit0。**通用`Remove-Item -Recurse synthetic-target`未被当前有限guard识别，返回ALLOW**；这是组件覆盖局限，删除审批仍由政策/执行者自守，不能宣称原生hook强制覆盖全部shell删除形式。本轮不改受保护guard或扩建命令解析器；L5实际宿主删除演练仍未测。

只有Windows组件路径取得运行证据；actual MCP、宿主发现/激活、模型选择、Linux CI及其他平台未验证。`wsl --list --quiet`只枚举到docker-desktop，未启动发行版/容器，不冒充Linux测试。原仓完整历史含须排除资产，且本次禁止交付提交；因此不clone原仓来满足形式，不用commit-tree绕过。需要现成无秘密已提交交付源才能补做完整clone/linked-worktree。既有小型合成clone测试只证明fixture runner。

已形成[具名宿主/拓扑验证清单](../evidence/codex-only-migration/p4-host-canary-plan.md)，列5族显式调用、近邻误触发、保护/删除无副作用决策、允许/拒绝和重入场景。已询问可用人工审阅路线及无秘密本地提交源；在取得实际输入前保持未测，不以等待时间当作批准，也不自动激活trust、改个人配置、停用规则或修改权限。

L5宿主执行路线单独记为`BLOCKED_EXECUTION_ROUTE`（尚缺满足本轮限制的已审阅路线；没有观察到新的工具技术拒绝），对应行为结果仍为`NOT_TESTED / UNMET_DEPENDENCY`。此局部阻塞不改变U04已执行并核验的P3人工应用路线，也不倒退为P3整组切换未落地。

### 17.6 逐AC、U01–U07与清理状态

| AC | 本轮结果 | 实际限制 |
|---|---|---|
| AC-01 | `STATIC_PASS` | 37正式同名入口及资源齐；宿主发现仍在AC-06/L5缺口 |
| AC-02 | `STATIC_PASS` | 已绑定当前身份的296维/142静态案例及P3增量；0模型调用 |
| AC-03 | `PASS`（本地独立维护切片） | 直接维护所有权成立；无旧资产副本运行检查通过；不等于P5清理完成 |
| AC-04 | `PARTIAL_PASS` | 配置/缺变量/异常/脱敏正反例通过；真实MCP连接未测试 |
| AC-05 | `PARTIAL_PASS` | 原保护继任和安全离线断言有运行证据；宿主拦截未测，泛化删除命令覆盖局限明确 |
| AC-06 | `PARTIAL_PASS / NOT_TESTED` | 独立Git与Windows根/子/空格路径已测；交付clone/worktree与真实宿主未测 |
| AC-07 | `STATIC_PASS`及离线实证 | 原生消费者闭合、GLOSSARY遗漏修复；保留非客户端adapter和业务资产 |
| AC-08 | `NOT_TESTED`（P5） | 本轮零清理；P3获批16项已删除不重复执行 |
| AC-09 | `BLOCKED` | 必需宿主/平台/拓扑证据未齐；离线测试通过不能抵充 |
| AC-10 | `PARTIAL_PASS` | 基线/未提交/P3/P4恢复源具名；最终平台/宿主交接未完成 |
| AC-11 | `STATIC_PASS`（P4切片） | 仅2项直接迁移修复+证据记录；无业务、全仓治理、审批平台增量 |
| AC-12 | `NOT_TESTED`（P6） | 原树无暂存/提交/推送/issue/分支/PR/合并；实际CI未运行 |

U01 memory备份/schema、U02后台生命周期均保持`UNMET_DEPENDENCY`；U03真实凭据/OS注入保持`NOT_TESTED`，Windows语法/进程替身不能代替真实凭据维护；U05真实8MCP/网络/远端写保持`NOT_TESTED`；U06脱敏snapshot/真实EVAL测量保持`UNMET_DEPENDENCY / NOT_TESTED`。U04保持`MANUAL_ROUTE_EXECUTED_VERIFIED`，不因L5路线未提供倒退成整个正式组受阻；U07保持`FORMAL_STATIC_CONSUMER_CLOSURE_PASS`，现在另有无旧客户端副本的消费者检查与测试证据，仍不等于host/service/CI通过。

[最新清理审阅表](../evidence/codex-only-migration/p4-cleanup-current.csv)列387个不同路径，逐项用途、替代者、消费者证据、当前SHA/缺失状态、恢复源、授权及不可清理理由。包含保留项、候选证据和P3已批准删除项，不是387项删除请求。旧客户端物理资产仍保留；独立副本排除它们且测试通过，只证明所测运行范围不依赖，尚无全部必需验收，不宣称全部旧资产完成退役。`cleanable=NO`全部保留；原资产397行P0–P3字段不变，更新P4当前状态并追加18证据行至415行，历史P4清单/JSON不覆盖。

### 17.7 恢复、最终身份与停止

1. **HEAD基线**仍为`20e2f24c352cf640d9dd33234b128ca897804b99:<path>`，只覆盖原Git提交状态，不含P0–P3未提交成果、原P1共享拆分或新的正式原生交付。禁止全树reset/clean。
2. **P0–P2/P1准确恢复**：`p3-entry-public-backup.zip`（63项）及`p3-completion-entry-public.zip`（88项）按原记录身份保留。P1安全测试不能通过还原HEAD整树消除。
3. **P3应用前准确字节**：`p3-preapply-public.zip`，SHA256 `87e1d215503eba8b191c664983acf4490a6ee145a4568feb3ae7c08d52dcc3d7`。§16整组恢复差异只适用于其原188项身份；本轮测试文件已有增量，若未来恢复须先按具名P4恢复包还原该增量并复核，不能直接套旧补丁。
4. **P4两文件恢复**：`p4-minimal-fixes-before.zip`与对应恢复diff保留原§16时点测试/GLOSSARY字节，恢复前逐项核验，不抹其他增量。
5. **本轮累计记录恢复**：更新前2文件备份`.mj-agent-local/p4-resume-records-before.zip`，SHA256 `3273ea6758b7d9b11ea9dc5cb746f3c47150383be5e5059e8a509aeb780d8175`。P4所有新记录尚未提交，完整内容来源为具名文件；摘要不是内容备份。
6. **副本与原树分开**：817当前交付字节除2个已登记修复外保持清单身份；只在副本有测试索引/生成缓存。原HEAD、分支、索引和worktree登记保持入场身份，P0–P3候选、证据、共享测试及其他正式文件未被覆写。最终复核见[p4-resume-final-check.json](../evidence/codex-only-migration/p4-resume-final-check.json)。没有删除独立副本或旧资产，便于审阅；清理仍需具名授权。

工具辅助失败如实保留：首次路径读取猜错token-estimator文件名后用rg定位；路径观测脚本最初误把guard允许分支当JSON输出，随后误把execpolicy无命中当含decision，两者均按实际协议修正观察器而非改产品填绿。原测试6失败和GLOSSARY断链红态留存。本轮源树`git diff --check`通过；GLOSSARY的autocrlf提示属于行尾转换提示，当前准确字节由恢复包/最终摘要绑定。

**P4已完成可执行的独立离线验证与最小修复，仍因必需L5及部分平台/拓扑未测而未完成技术验收。记录更新后停止，不进入P5，不把未测项记成实际失败或通过。**

## 18. P5 前置核查（2026-09-18，未启动正式清理／BLOCKED_PREREQUISITE）

### 18.1 依据、现场与文件身份

本轮按 Owner 的 P5 单阶段请求及“继续”，只完成前置核查、授权映射、缺失输入整理与累计记录更新。读取计划 §4.7/§6/§7、报告 §17、P4 最终核验/副本清单/清理表/两项修复/宿主清单，以及 P3 授权、人工应用、格式及恢复记录。入场报告最新章节确为 §17，没有后续通过证据。具体命令、环境、逐文件身份和 387 行映射见 [P5 前置核查证据](../evidence/codex-only-migration/p5-prerequisite-audit.json)。

- 绝对根仍为 `D:/workspace/10-software-project/projects/mj-agent/maintain/codex-dev-mode-migration`；分支 `maintain/codex-dev-mode-migration`，HEAD `20e2f24c352cf640d9dd33234b128ca897804b99`。
- 入场有 130 项未暂存修改、16 项未暂存删除、338 项未跟踪文件；暂存区为空，索引摘要 `28775dc7df4acf1de7ea45b11d182bd4813f0c2bbc66967f3a7223a7f2e7531f`。16 项删除全部是 P3 已批准并执行的旧测试，本轮不重复删除。worktree 登记与 P4 一致；只核对登记，不修改其他工作树。
- P4 入场公开文件与最终记录、两项增量合并后的预期身份全部匹配，未发现未解释漂移。188 项正式组（含 16 项缺失状态）匹配；817 项当前交付原树及独立副本字节全部匹配。37 技能、P1 共享安全测试拆分、受控 runner 与 P4 两文件修复均被该身份集合覆盖。
- `test_sdd_development_agent.py` 保持 `feb2a819ab6baa580b36cf55d379c16c988e1beedebaf601b97bbdd4d70f3b41`；`GLOSSARY.md` 保持 `d0ba1c26cd2779476e56129e064a75f3e71a8d06493eb0c6d5dd2c4afb40b28c`。冻结审阅包及具名差异保持原身份，没有重放补丁。
- 387 项清单身份均匹配，全部 `cleanable=NO`。身份核查通过只证明记录仍绑定当前文件，不是 P4 行为验收通过。

### 18.2 必需前置与缺失输入

| 前置 | 当前证据与结论 | 仍缺输入 |
|---|---|---|
| L1/L4 来源与流程语义 | 沿用当前摘要匹配的 `STATIC_PASS`，未执行新模型调用 | 静态身份不能替代要求的宿主观测 |
| L2 独立性及完整交付拓扑 | 独立副本与 Windows 路径已有 P4 部分实证；clone/linked worktree 为 `NOT_TESTED` | 可核验、无秘密的已提交交付源或另行明确路线，以及绑定交付身份的实际拓扑结果 |
| L3 确定性行为 | P4 六带 1059 passed、32 skipped，另 19 subtests passed；本轮只核对原记录与身份 | skip 继续未验证；不扩大组件覆盖结论 |
| L5 真实宿主 | 行为 `NOT_TESTED / UNMET_DEPENDENCY`，路线 `BLOCKED_EXECUTION_ROUTE` | 工程师独立审阅且满足无秘密/无服务连接约束的宿主路线；真实指令/技能加载、5 族及近邻模型 canary、规则/hooks 允许/拒绝与保护/删除无副作用观测 |
| Linux 与实际 CI | `NOT_TESTED`；Windows 和合成 fixture clone 不替代 | 绑定当前交付身份的 Linux 执行结果和实际 CI 逐门禁结果 |
| 全局 P4 验收 | `PARTIAL_NOT_ACCEPTED` → P5 `BLOCKED_PREREQUISITE` | 上述必需证据有效闭合；本提示词、静态通过和 P3 批准均不能抵充 |
| L6 外部服务 | `OUT_OF_SCOPE / NOT_TESTED` | 本轮不要求服务输入，不增列为 P5 门槛 |

不自动返回 P4 补测，不启动宿主、模型、服务、Linux、容器或 CI。通用 `Remove-Item` 形式的既有守卫覆盖局限仍保留；未阻断不等于获准删除。宿主环境权限可用性也不等于信任审阅、canary 通过或删除授权。

### 18.3 授权与未删除集合

| 清单分类 | 数量 | 本轮处置与授权判断 |
|---|---:|---|
| `LEGACY_REMNANT_CONDITIONAL` | 81 | 旧资产保留；没有具名 P5 删除批准，全局前置也未满足 |
| `KEEP_OR_REVIEW_ONLY` | 271 | 原生/共用/业务与审阅资产保留，不作为批量删除请求 |
| `CANDIDATE_EVIDENCE_PRESERVE` | 19 | 候选与证据保留；未证明验收/恢复用途终止，无清空授权 |
| `ALREADY_REMOVED_P3_APPROVED` | 16 | A5 历史批准已执行，当前仍缺失；只复核，不重复动作 |

因此，387 行中的 371 个现存路径全部保留，另 16 个路径维持 P3 缺失状态。**本轮实际删除集合 `[]`、移动集合 `[]`、候选清空集合 `[]`。** `.claude`、`sdd/adapters`、`_common`、`.migration`、P4 临时副本、历史证据及恢复包均未清理。六项非客户端 adapter、原生入口和共用安全代码不因目录名进入删除范围。

P3 A1–A6 是成组切换批准；旧授权文件中 `PENDING`/审阅包中的 `NOT_APPROVED` 是冻结时点，结合后续 §15–§17 人工应用与当前身份核验理解，不回写历史，也不扩大为 P5 批准。新指令授权的是前置受阻分支的记录工作。

逐项映射保留用途、替代者、原消费者来源、绝对路径、当前摘要/缺失状态、HEAD 基线、具名恢复成员及授权。本轮未进入删除前的活动消费者再审，明确记为 `NOT_REASSESSED_FOR_DELETION`。P4 清单文字命中不冒充本轮扫描：活动调用、历史记录、负向测试/拒绝词表、清理清单须在未来可执行审阅中逐项区分；不凭旧清单、零关键词或副本测试宣布无消费者。没有当前字节恢复匹配的行明确保留恢复缺口，绝不推定可执行。即使某项已有历史批准，也不跳过全局 P4 前置。

### 18.4 恢复来源及适用顺序

本轮只读核对下列公共 ZIP 的摘要和全部具名成员，未解压覆盖现场：

| 来源（位于 `.mj-agent-local/`） | 成员数 | 适用身份 |
|---|---:|---|
| `p3-entry-public-backup.zip` | 63 | P3 入场前的 P0–P2/P1 公开成果，以原 manifest 定位 |
| `p3-completion-entry-public.zip` | 88 | P3 补齐准备前的具名公开文件，不能当最终交付快照 |
| `p3-preapply-public.zip` | 146 | 正式成组切换前的精确工作字节，包含 P1 共享拆分；配合新增/删除清单恢复 |
| `p4-minimal-fixes-before.zip` | 2 | P4 测试与 GLOSSARY 最小修复之前的字节 |
| `p4-resume-records-before.zip` | 2 | P4 更新前累计报告与资产表 |

HEAD 只能恢复已提交基线，不含上述未提交成果。恢复 P3 时必须先按 `p4-minimal-fixes.json` 与 P4 两文件恢复包处理增量并复核，再审查适用于 §16 原 188 项身份的 `p3-postformat-group-recovery.diff`；最终字节按 `p3-preapply-public.zip` 核对。GLOSSARY 是原 188 项之外的 P4 增量，不能遗漏。此处只是适用顺序说明，本轮没有实际恢复、reset、clean 或试套补丁。

817 文件的 P4 独立副本本轮仍匹配当前交付，可作为具名当前字节来源，仍承担验收用途，禁止清理。当前字节与历史备份的匹配关系逐项记录，摘要本身不是内容备份。

本轮另保留 `.mj-agent-local/p5-public-records-before.zip`，含本轮更新前的两份累计记录及全部具名 `p4-*` 公开证据文件；SHA256 为 `38c04968928afc50686d3e9afb9e5f3ce8d8a5c9dd3924016567249c4ab6fbab`，成员表见 P5 核查 JSON。它补充保存 P4 未提交记录，不代替代码恢复包，也不授权删除旧副本或备份。

### 18.5 命令、记录验证、U01–U07 与停止

只执行 Git 只读现场命令、公开文件摘要/ZIP 成员核查及记录写入。首次 PowerShell profile 写缓存失败后改用无 profile；大段输出截断后重读限定字段；一次猜测的检查器路径不存在后用 rg 定位真实文件。P5 审计第一次读取具名 P4 临时副本时因沙箱访问拒绝退出 1；按正常审批机制获准同一只读审计后，同一脚本退出 0。没有换工具绕过守卫，没有激活信任或改个人配置。所有这些是工具/核查轨迹，不是 P4 或清理后测试失败。

本轮只修改累计报告、资产表并新增两份具名 P5 证据；本地辅助脚本和公开备份留在 `.mj-agent-local/`。资产原 415 行、全部 P0–P4 字段原值保留，追加 `p5_*` 字段及 2 行证据，共 417 行。当前摘要字段以入场时点解释，两个本轮可变累计文件的最终身份另记 [记录验证](../evidence/codex-only-migration/p5-record-validation.json)。历史报告 §2–§17 保持原文，首段改指 §18。

| 项目 | 最新状态 |
|---|---|
| U01 memory schema/备份恢复能力 | `UNMET_DEPENDENCY` |
| U02 宿主后台生命周期 | `UNMET_DEPENDENCY` |
| U03 真实凭据/OS 注入维护 | `NOT_TESTED`；不读真实值，不解密、不写 OS 凭据 |
| U04 P3 已批准人工应用路线 | `MANUAL_ROUTE_EXECUTED_VERIFIED`；不与 L5 缺路线混淆 |
| U05 8 MCP/网络/远端写 | `NOT_TESTED`；本轮范围外，不要求提供凭据 |
| U06 脱敏快照/真实 EVAL 测量 | `UNMET_DEPENDENCY / NOT_TESTED` |
| U07 正式消费者 | `FORMAL_STATIC_CONSUMER_CLOSURE_PASS`；不代表宿主/CI/服务验收 |

Codex 贡献为本次核查、映射与记录；HITL 仅复用明确的本阶段记录授权及上述具名读取审批，未执行新的受保护资产写入或清理；BDD/TDD impact=NONE；Subagent dispatched=NONE。未改 #499/#552、业务资产、个人配置、秘密或其他工作树；原树未暂存、提交、推送、建分支/issue/PR、合并或部署。

**P5 未启动正式清理／BLOCKED_PREREQUISITE。清理后验证为 NOT_TESTED，不记作实际 FAIL 或 PASS。技术迁移未验收，旧资产未全部退役，P5 未完成；更新记录后停止，不进入 P6。**

## 19. P4 缺口补验（2026-09-18，G19 实际失败／宿主与平台路线待输入）

Owner在§18后明确“授权，继续”，本轮重新进入P4缺口补验，不启动P5/P6，也不把阶段授权扩大为解除“不提交、不连接外部服务、不自动信任或激活hooks”等明确限制。复用flow-verify的离线矩阵，新增缺陷按flow-implement最小根因方案准备；没有委派子代理。

### 19.1 当前身份与新增实际验证

188项正式组、817项交付原树及副本、387项清理清单全部重新匹配；原HEAD、分支、索引字节及worktree登记未变。P1安全测试和P4两项修复保留。本轮未修改正式交付文件。身份及实际命令见[p4-supplement-entry.json](../evidence/codex-only-migration/p4-supplement-entry.json)。

对照当前CI，补跑20条此前未覆盖的Windows离线检查或更严格参数，其中19条exit0、1条exit1；这些是命令数量，不是pytest通过数。A4严格链接、A6、归档manifest/index、V1/V3/V5/V7、G8、G21/G22、G23、secret exposure等按原命令记录；V2无合同、V6 skeleton、G8条件skip、G24/G25无适用检查及既有WARN不算实际能力通过。V5的compose-config参数只是代码内静态解析，没有连接Docker。

**新增真实失败：G19 `check_bdd_scenario_trace.py --all --scope full` 返回1，22P/0W/2F。** MCP governance的REQ-001、REQ-002场景缺`@CTR-mcp-server`。基线有这两个标签，P3原生改写遗漏；当前契约ID和trace仍匹配，属于迁移缺陷，影响AC-05/07/09。不能再仅把P4差距描述成环境未测。完整输出见[p4-supplement-local-checks.json](../evidence/codex-only-migration/p4-supplement-local-checks.json)。既有1059 passed/32 skipped另19 subtests是上一轮六带证据，本轮未重复，也不抵消新G19失败。

### 19.2 受保护最小修复：已准备，未应用

仅在`capabilities/infrastructure/mcp-server-governance/contracts/behavior.feature`两行恢复`@CTR-mcp-server`，不改场景正文、断言、checker或门禁。差异及准确字节恢复包见[G19审阅记录](../evidence/codex-only-migration/p4-supplement-g19-review.json)；只读apply检查及候选标签/trace解析通过，不等于正式G19已绿。

原SHA256 `586fe2a078748f9fe362008bcfaac47b60fd44afae0917d946e942b49e7da1bf`，拟应用后`da0ecc2a8a49c46548386cf4bf31cfc8fbec09dd5610dfeef492d19d486928bd`。恢复来源`.mj-agent-local/p4-supplement/g19-before.zip`；[具体差异](../evidence/codex-only-migration/p4-supplement-g19-proposed.diff)和[恢复差异](../evidence/codex-only-migration/p4-supplement-g19-recovery.diff)保留。

依据policies/ai-agent.md §4的declared-contract-change，此.feature属于Owner必停；旧A1–A6冻结批准未明确涵盖新两行增量。已经展示目标/差异/恢复，并请求沿用“Owner批准并人工应用→Codex核验”。Owner已答复“批准两行修复，我人工应用后通知”；目前未收到应用通知，当前正式文件仍匹配原SHA，源树与副本均未修改；不换工具、编码或权限写入。实际应用后才复跑G19、trace和MCP BDD，并重新绑定817交付身份。

### 19.3 拓扑、宿主与平台的实际进展及限制

本机Codex CLI仍0.147.0，离线协议导出361份schema，存在skills/list、hooks/list及hook运行通知，hooks元数据定义含sourcePath/currentHash/enabled/trustStatus。公开导出方法名未发现hook模拟接口；这只是接口发现，不是已加载/信任或运行证据。没有启动app-server会话、项目MCP或模型canary，未调用信任写入。资料见[接口审阅](../evidence/codex-only-migration/p4-supplement-host-interface-review.json)。按不连接外部服务限制，没有联网查询官方文档。

WSL仍只有docker-desktop；本地Docker Linux引擎管道不存在，image ls返回1。这是环境前置失败，不是Linux测试失败。未启动daemon/容器、切换context、安装或下载依赖。Linux仍UNMET_DEPENDENCY/NOT_TESTED；[当前CI逐步矩阵](../evidence/codex-only-migration/p4-supplement-ci-matrix.json)保持实际CI=NOT_TESTED，没有推送、PR、workflow dispatch或远端查询。Windows补验不能替代Linux/实际CI。

Owner已明确答复“允许该一次性测试提交与两个拓扑副本”。已在独立native acceptance副本创建唯一测试提交`e25cda790f881e7986122e94a8597c7acf3d1bbc`（tree `cf67762486245325c178dc53226ffc61357b84d9`），随后在同临时父目录创建`topology clone`和`topology linked`，两处均detached HEAD。clone使用no-hardlinks，Git自动产生的本地origin立即移除；没有外部远端或网络。linked仅写一次性副本自身Git登记，不改原仓worktree登记；没有关闭hooks或修改权限，未观察正常路线技术拒绝。

两处各817文件匹配同一Git树，逐项登记当前SHA；仅GLOSSARY因正常Git checkout发生LF/CRLF转换，其余工作字节与原副本完全相同。根/子目录/空格路径的原生技能、资源、入口、消费者与config检查通过；正式launcher缺凭据exit3，直接guard允许/保护拒绝/异常拒绝通过。5个边界/安全相关单元文件经原受控runner在两处分别取得**106 passed、19 subtests passed**，不增加到此前1059个不同用例计数。55条组件/身份命令详见[完整拓扑证据](../evidence/codex-only-migration/p4-supplement-topology.json)。这是绑定修复前G19状态的Windows拓扑证据，不包含待人工应用的两行新增量，不代表宿主、Linux或实际CI。原树任何Git写操作不在此例外内。

L5仍等待工程师已审阅且不连接项目MCP/业务服务的宿主路线；该问题收到“继续”，未提供具体环境/审阅证据，不解释为已完成信任审阅。具体路径、Owner两行应用命令、所缺输入与后续验证见[执行路线审阅](../evidence/codex-only-migration/p4-supplement-execution-review.md)。

### 19.4 最新状态、记录与停止点

L1/L4沿用当前身份绑定的静态证据；L2的完整交付Windows clone/linked拓扑已有实际组件证据；既有L3离线行为证据保留，但G19为新增必需门禁FAIL。L5路线BLOCKED_EXECUTION_ROUTE、行为NOT_TESTED/UNMET_DEPENDENCY；Linux及实际CI未测；L6范围外。AC-05/07/09新增G19修复未闭合，AC-06/10仍缺宿主/平台证据，Windows拓扑取得补充实证；其余AC沿§17限定结论，不扩大PASS。

U04继续MANUAL_ROUTE_EXECUTED_VERIFIED（P3人工路线）；U07的FORMAL_STATIC_CONSUMER_CLOSURE_PASS只保留原checker覆盖范围，新G19契约追踪失败另行敞口，不冒充全部消费者/门禁均通过。U01/U02保持UNMET_DEPENDENCY，U03/U05保持NOT_TESTED，U06保持UNMET_DEPENDENCY/NOT_TESTED。

原417行资产及全部原字段保留，新增3个补验字段和12条证据行，共429行。历史§2–§18及P4/P5旧证据未覆盖，累计两记录更新前备份位于`.mj-agent-local/p4-supplement/records-before.zip`，摘要见[p4-supplement-verification.json](../evidence/codex-only-migration/p4-supplement-verification.json)。恢复HEAD/未提交P0–P4字节的适用边界仍沿§17–§18，不重放旧补丁。

**技术迁移未验收；P5仍BLOCKED_PREREQUISITE，387项均不可清理。删除/移动/清空均为0，正式文件未改，原树未暂存或发布。受保护两行修复已获批准、等待Owner人工应用通知；具名测试提交及Windows拓扑补验已完成，宿主/平台等待可执行输入；不进入P5/P6。** 最终记录与身份核查见[p4-supplement-final-validation.json](../evidence/codex-only-migration/p4-supplement-final-validation.json)。

## 20. P4 G19 获批修复应用与复验（2026-09-18）

Owner先批准精确两行差异，随后明确“你来执行”，将本项执行者由Owner人工应用改为Codex正常工具执行；不扩大目标或授权范围。应用前核对当前SHA、局部约束、HEAD与空暂存区，`git apply --check`通过；随后正常`git apply`返回0，没有技术保护拒绝，没有换工具绕过、停用guard、改权限/信任或建审批凭证。实际成功不证明宿主hook已加载；U04原P3人工路线状态仍保持。

唯一正式文件增量：`capabilities/infrastructure/mcp-server-governance/contracts/behavior.feature`，REQ-001和REQ-002各恢复`@CTR-mcp-server`。原SHA `586fe2a078748f9fe362008bcfaac47b60fd44afae0917d946e942b49e7da1bf`，实际新SHA `da0ecc2a8a49c46548386cf4bf31cfc8fbec09dd5610dfeef492d19d486928bd`，与批准差异一致。步骤正文、断言、门禁和业务语义未改变。精确恢复包仍为`.mj-agent-local/p4-supplement/g19-before.zip`，SHA `4c75bd754cb6d4271d60c362a7e2f81620b02bb5b62f52ae030de93579787e69`；对应`p4-supplement-g19-recovery.diff`仅适用于本次两行增量。

同一补丁经身份核对后应用于既有native acceptance、topology clone、topology linked三处。它们仍保留唯一获批测试提交`e25cda790f881e7986122e94a8597c7acf3d1bbc`，现在是该提交加一个具名未提交文件增量。没有新建/修改提交，也没有暂存原树或副本；不能把旧提交SHA单独当成修复后完整工作字节身份。

| 实际范围 | G19 | trace | 受控MCP governance BDD |
|---|---|---|---|
| 原迁移工作树 | 24P/0W/0F | 6P/0W/0F | 2 passed、4 dependency warnings |
| 独立native acceptance | 24P/0W/0F | 6P/0W/0F | 2 passed、4 dependency warnings |
| 完整topology clone | 24P/0W/0F | 6P/0W/0F | 2 passed、4 dependency warnings |
| detached topology linked | 24P/0W/0F | 6P/0W/0F | 2 passed、4 dependency warnings |

12条实际验证命令和退出码见[p4-g19-applied-verification.json](../evidence/codex-only-migration/p4-g19-applied-verification.json)。BDD使用未改的受控runner，未绕过tracked-only、环境隔离或插件限制；警告为既有gherkin依赖弃用。原根仅显式运行已跟踪的MCP BDD文件，没有原树补暂存。先前G19 22P/2F保留为红态，§19中“待人工应用”等为历史时点，本次实际绿态关闭该具体迁移缺陷。没有把四次同一BDD重复计成新增8个不同用例，也没有无变化重复全套1059项测试。

188正式组及817交付的当前身份须合并本次单项SHA覆盖；其余身份不变，P1安全拆分/P4之前两项修复保留。最新387项清理身份见[p4-g19-cleanup-current.csv](../evidence/codex-only-migration/p4-g19-cleanup-current.csv)，仅本目标SHA/恢复说明更新，全部cleanable=NO；旧P4清单保留为历史，不按旧SHA执行清理。资产原429行所有字段原值保留，新增G19当前字段和3条证据，共432行。

原HEAD、分支、索引字节、worktree登记不变；本轮无提交、推送、PR、分支、服务连接、秘密读取或删除。记录更新前备份`.mj-agent-local/p4-supplement/g19-records-before.zip`保留累计报告/资产表，摘要及最终保全结果见[p4-g19-final-validation.json](../evidence/codex-only-migration/p4-g19-final-validation.json)。§2–§19与旧证据保持原样，不覆盖历史红态/批准/未应用记录。

**G19两行修复已应用并复验通过。P4仍缺L5真实宿主及Linux/实际CI证据，技术迁移尚未验收；P5继续BLOCKED_PREREQUISITE，未执行清理，不进入P5/P6。** U01–U06沿此前限定状态；U07保留静态消费者闭合证据，新增G19追踪缺陷现已关闭，仍不等同于宿主或CI通过。

## 21. P4 Linux 输入准备与获准 Docker 启动（2026-09-18，环境未就绪）

Owner要求“继续解决”，随后针对具体启动范围明确“启动 docker”。本轮继续解决P4环境前置，没有进入P5/P6。G19修复、原HEAD和空暂存区保持§20身份；没有修改正式交付内容。

### 21.1 可执行的离线 Linux 输入

已生成`.mj-agent-local/p4-linux/p4-linux-offline-input.tar`，SHA256 `a19eee0f96cb21f432e3295cdf8ec93ea42a7c8d5edf5262ddd578b73c5a2186`，13424640字节。包含当前817项交付文件（明确纳入G19新SHA）、仅两份既有已批准公共tiktoken词表，以及manifest/执行脚本，共821个普通文件成员。逐项SHA、成员路径/类型和归档内容已复核；不含原Git元数据、秘密、个人配置、安装产物或额外缓存。源码/其他工作树均未改。

包内run-linux.py要求Linux、Python3.13、git、已安装的依赖、仅loopback网络接口，检查全部输入摘要后仅在一次性目录建立817文件测试索引；不提交、不安装/下载依赖、不放宽runner/锁定插件。它包含本地CI命令对应检查及六个受控离线测试带；缺环境或依赖先返回UNMET_DEPENDENCY。词表保持原例外批准范围，未复制其他缓存。

当前只有脚本语法和归档完整性检查，**PREPARED_NOT_EXECUTED**；没有Linux行为PASS，没有把本地工作流命令称作实际远端CI。包不是启动容器、拉取镜像或外部服务授权。见[p4-linux-input-package.json](../evidence/codex-only-migration/p4-linux-input-package.json)。一次辅助补丁因误判字符串转义而未找到目标、未写入任何文件；随后解析包内Python AST确认换行/null分隔符原本正确，无需修改，不计作Linux测试失败。

### 21.2 Docker 正常启动的实际观察

启动前Docker context为desktop-linux，Desktop和backend进程未观测到、com.docker.service为Stopped，WSL仅docker-desktop。已向Owner说明启动可能恢复既有自动重启容器；Owner随后明确要求启动。执行正常命令`docker desktop start --timeout 45`，没有切换context、修改配置、重置WSL或安装更新。

后续tasklist已观察到Docker Desktop.exe和com.docker.backend.exe进程，说明Desktop进程启动已发生；正常启动CLI最终返回1，输出“Docker Desktop is still starting: context deadline exceeded”；desktop status查询仍未返回。Docker引擎version查询分别在10秒和15秒到期，未取得服务端版本；没有进入镜像/容器盘点。因此只报告**DESKTOP_PROCESSES_STARTED_ENGINE_UNREADY**，不宣称Engine running，也无法确认既有容器是否自动恢复。

本轮没有主动运行任何项目容器/Compose、创建测试容器、拉取镜像或连接业务服务；不读取容器环境变量、凭据、个人配置或Docker原始日志。正常启动请求已超时结束，保留启动现场；只读status客户端仍等待，没有杀Docker进程或重启引擎。已询问Owner原生窗口是否有WSL/许可/错误等人工提示；当前工具无法读取该原生窗口，等待具体提示文字或Engine running状态。限时查询失败是环境前置状态，不是项目Linux测试FAIL。过程见[p4-docker-start-observation.json](../evidence/codex-only-migration/p4-docker-start-observation.json)。

### 21.3 宿主、CI与后续输入

另已明确询问是否允许仅查询官方Codex/GitHub资料，以及在工程师已审阅宿主进行模型canary；尚无该问题答复，本轮未联网查文档或调用新模型会话。项目MCP、数据库和业务服务继续禁止连接，不把“继续解决”扩大为自动信任、激活hooks、改个人配置、推送或workflow dispatch。

Linux环境缺口现在定位为已启动Desktop但引擎未就绪；离线输入已具名准备，环境就绪后还须核对实际镜像/依赖才能运行。L5路线仍BLOCKED_EXECUTION_ROUTE，Linux行为UNMET_DEPENDENCY/NOT_TESTED，实际CI仍NOT_TESTED；Windows/静态结果不代替它们。U01–U07沿§20限定状态，没有因准备包或启动批准关闭任何未测项。

累计原432行资产全部原字段保留，追加2个环境字段和3条证据，共435行。§2–§20、历史证据和最新387项清理身份不变，全部不可清理。更新前两记录备份`.mj-agent-local/p4-linux/records-before.zip`，摘要见[p4-environment-final-validation.json](../evidence/codex-only-migration/p4-environment-final-validation.json)。本轮无源码改动、原树暂存/提交/推送/分支/PR或清理；没有进入P5/P6。

## 22. P4 Docker 启动故障诊断（2026-09-18，正常文件操作受阻）

Owner在“启动 docker”后明确“授权你来继续执行”。本轮继续处理P4的本地环境前置，沿用已读取的flow-verify边界；没有进入P5清理或P6。未增加项目代码、配置、门禁或测试改动。

### 22.1 实际定位与正常恢复尝试

只读检查显示WSL/虚拟化服务和AF_UNIX驱动在运行，docker-desktop发行版为Stopped；不是已证明的项目迁移回归。限定启动日志给出具体错误：Inference manager无法移除`C:/Users/Admin/AppData/Local/Docker/run/dockerInference`，报“The file cannot be accessed by the system.”。该对象为零字节、attributes=1056，创建和最后写入时间均为2026-09-16T12:59:56.2534385Z；`fsutil reparsepoint query`也返回Windows错误1920。底层文件系统原因尚未证明，不据此修改驱动、ACL或个人配置。

此前等待的desktop status最终exit1。`docker desktop stop --timeout 30`也exit1，提示进程未退出；随后使用Docker自带`stop --force --timeout 20`成功exit0，确认Desktop/backend/vmmemWSL进程已退出。执行前已确认Docker WSL实例为Stopped，没有执行Compose或停止某个具名业务容器。用原配置再次`start --timeout 30`后，同一错误于12:44 UTC再次出现；客户端包装器记录TIMEOUT_45S和启动失败文本，包装器exit0不代表Docker启动成功。再用同一Docker正常强制退出命令成功关闭失败进程。

为保留现存对象，准备仅将上述一个运行时路径同目录重命名为`dockerInference.p4-held-20260918`。执行前核对绝对源/目标父路径、目标不存在、进程已退出及源元数据；仅调用一次正常PowerShell `Move-Item -LiteralPath`。**操作返回1，仍报系统无法访问文件；立即标记BLOCKED_EXECUTION_ROUTE并停止。** 没有改用其他删除工具、编码、原生API、提权或权限调整。复查源元数据不变、目标不存在，因此实际移动/删除均为0，不存在已完成隔离需要回滚的情况。准备的反向恢复说明只适用于成功保留且原路径空缺的情形，本轮未执行。

当前Docker已停止，WSL实例仍Stopped。不能再沿用§21的“后台进程已启动、status仍等待”作为最新状态；全部具名等待会话均已收尾。未拉镜像、创建测试容器、启动项目服务、重置WSL、恢复出厂设置或删除volume/image。

### 22.2 证据边界与待验收项

实际命令、失败轨迹、源/目标身份、最终进程/服务状态及未执行项见[p4-docker-recovery-diagnosis.json](../evidence/codex-only-migration/p4-docker-recovery-diagnosis.json)。读取了限定本机启动日志和元数据；未打开真实凭据、加密秘密、容器环境或个人配置文件，没有把整段设置/代理日志复制进证据。Docker自身启动日志包含远端feature flag/遥测HTTP 200记录，因此不宣称Desktop启动处于完全离线环境；未主动进行项目MCP、业务服务、资料查询、模型canary或CI调用。离线Linux包仍未执行，不能用其网络约束推断宿主启动也已断网。

817项当前交付、G19修复、此前两项P4修复和P1共享安全测试拆分保持身份；L1–L4只沿此前限定的Windows、组件与静态证据，无新行为PASS。AC-06/09/10仍缺相应宿主、Linux/CI证据，其余AC不扩大先前结论。Linux路线现为BLOCKED_EXECUTION_ROUTE / UNMET_DEPENDENCY，Linux行为NOT_TESTED；L5路线仍BLOCKED_EXECUTION_ROUTE，真实宿主行为和实际CI仍NOT_TESTED；L6范围外。

需要的实际输入是工程师修复后的本机Docker引擎，或另一个明确可用且获准的Linux环境，之后还须核对具名镜像与Python3.13等离线依赖。当前没有镜像/容器盘点结果，不建议未经审阅的拉取、重装或重置命令。另仍需工程师独立审阅的L5宿主/hooks路线及绑定当前交付的实际CI记录；聊天继续/批准本身不替代这些输入，不自动激活信任或调用外部模型。

U01/U02仍UNMET_DEPENDENCY；U03/U05仍NOT_TESTED；U06仍UNMET_DEPENDENCY / NOT_TESTED；U04只在P3人工路线范围保持MANUAL_ROUTE_EXECUTED_VERIFIED；U07保持限定的FORMAL_STATIC_CONSUMER_CLOSURE_PASS。Docker环境受阻不反向改写已完成的P3执行记录，也不关闭上述缺口。

### 22.3 保全、恢复与停止

累计435行资产及全部历史字段原值保留，追加本轮诊断字段和2条证据，共437行；§2–§21及旧证据保持原样。387项具名清理记录仍全部cleanable=NO，未进行P5操作。当前Git HEAD、空暂存区、索引字节和原仓worktree登记不变；本轮没有提交、推送、PR、分支、部署或其他工作树改动。

本轮更新前累计报告/资产表备份为`.mj-agent-local/p4-docker-diagnosis-records-before.zip`，摘要及保全核对见[p4-docker-diagnosis-final-validation.json](../evidence/codex-only-migration/p4-docker-diagnosis-final-validation.json)。HEAD只覆盖已提交基线；未提交P0–P4、P1拆分及G19增量仍使用§17–§20的具名公共恢复包与差异，不以HEAD或本轮记录ZIP代替。Docker源对象未移动，无运行时文件恢复动作。实施者Codex，Subagent=NONE，本轮项目测试数=0；环境命令失败不记为pytest FAIL。

**P4技术迁移未验收，P5继续BLOCKED_PREREQUISITE。已保存新的具体故障证据并停止该受阻路线；不进入P5/P6。**

## 23. P4 Linux 实际离线补验与最小修复（2026-09-20）

Owner报告Docker已启动并要求继续。本轮只读确认Engine 28.3.2、Linux/amd64实际响应；不重放§22的套接字修复，不触碰既有业务容器。原HEAD/分支/空索引及原仓worktree登记保持原样。既有本地运行镜像的禁网探针确认Python3.13.14存在，但缺git、pytest及lint/type工具，故另形成具名临时依赖方案。Owner明确允许在该临时环境从公共PyPI/pythonhosted与Debian源下载依赖；这个例外不覆盖业务服务、模型或远端CI。

### 23.1 环境、隔离与执行轨迹

依赖准备只使用两幅既有本地基础镜像，未拉取/更新基础镜像、未改宿主依赖。临时环境安装git2.47.3、当前uv.lock项目/dev依赖，后因实际测试暴露缺Node而补装Node20.19.2。pyproject/uv.lock摘要保持不变；pytest9.0.3、asyncio1.3.0、bdd8.1.0、ruff0.15.11、mypy1.20.2、PyYAML6.0.3按实际记录。Git下载客户端240秒超时后，容器安装仍在继续；等待完成后dpkg audit和同命令确认成功。Node一次Debian连接失败exit100，原命令/原源重试一次成功，未换镜像源、版本或跳过依赖。

正式测试使用另建的禁网容器：创建时network=none、只读根、UID65534、cap-drop ALL、no-new-privileges；没有Docker socket、宿主目录、业务volume、端口映射或业务入口/健康探针。只读挂载具名公开输入文件，工作区在/tmp tmpfs。原受控runner执行插件锁定、环境隔离和tracked-only检查，仅在一次性Git元数据中建立测试索引；没有新Git提交。测试仅见loopback接口。公开依赖准备联网与正式验收断网分别记录。

当前矩阵镜像为`sha256:7a868cb349e4110b2a56c42f84a8b06938e3e865c5ca6ad6690fd93176fea82d`；拓扑使用已准备且足以运行五个安全文件的前一镜像`sha256:c8c1eb9a5c819f02c2c5e646383ca32eb9daee154091bec12bfedb2b9de322a2`。环境为Docker Desktop WSL2 Linux/amd64、kernel6.18.33.2、Python3.13.14。它是真实Linux容器执行，不冒充其他发行版/平台或GitHub Actions。完整命令及失败轨迹见[环境](../evidence/codex-only-migration/p4-linux-resume-environment.json)、[依赖准备](../evidence/codex-only-migration/p4-linux-dependency-preparation.json)、[Node准备](../evidence/codex-only-migration/p4-linux-node-environment.json)。

### 23.2 实际失败、最小修复及恢复

首轮[Linux矩阵](../evidence/codex-only-migration/p4-linux-execution.json)实际有2条命令非零：资源检查误把doc-validate正文的双反引号`repo:...`占位例子当作路径；unit有2项wrapper测试因node不存在而FAIL。两项测试确实运行并失败，保留原红态；不能改称未运行，也没有删除断言或增加skip。

正式项目唯一新增改动：`.agents/skills/mj-agent-doc-validate/SKILL.md`的一行，改为“内部wikilink的仓库目标路径（以repo:为前缀）在仓库中存在”。P3把旧示例`[[...]]`改成repo占位，Linux实际资源检查暴露回归；本次是普通原生文档技能的最小迁移修复，不是冻结infra/runtime技能正文。检查器、规则、hooks、契约、CI和全部测试均未改。

原SHA`ee07233a6575558d070466a4b9cf6f0bf57f16f21402651f123e7ecd6eb77a78`，当前SHA`58a21e1e06e5b8e1fc8905930b1efe1eb2615500aa7e32336d2c97242727bf0b`。准确恢复包`.mj-agent-local/p4-linux/doc-validate-before.zip`，摘要`14eedfa05fa9928082db6012754f457cc7b96fe5ec137c297b5c59acecb81688`；见[差异](../evidence/codex-only-migration/p4-linux-doc-resource.diff)、[恢复差异](../evidence/codex-only-migration/p4-linux-doc-resource-recovery.diff)及[修复/语义记录](../evidence/codex-only-migration/p4-linux-doc-resource-fix.json)。同一行同步到三处既有Windows一次性副本，未改其他原仓worktree。Windows原生技能/资源检查通过。

最新817文件输入包为`.mj-agent-local/p4-linux/p4-linux-offline-input-v2.tar`，SHA`79d145bda9064c87bd1eb9817c5983e0b160f0634fc5dbe29b23e8fb105b14bd`，成员仍为817交付+两份获准公共词表+manifest/runner，共821。只更新该文档和对应manifest；旧包保留。既有188正式组需叠加已记录的P4修复/G19/本次单行SHA；P1共享安全拆分、其余交付身份及16项既有删除均重新核对保留。

### 23.3 Linux矩阵与路径/拓扑结果

[当前Linux矩阵](../evidence/codex-only-migration/p4-linux-execution-v2.json)共44条命令，均exit0：2条临时Git准备、36条本地CI对应检查、6个受控测试带。资源检查红→绿；Node两项失败在补足依赖后通过。结果如下：

| 测试带 | passed | skipped | 说明 |
|---|---:|---:|---|
| unit | 877 | 10 | 另19 subtests；10项既有Windows平台skip |
| eval | 93 | 0 | 离线fixture，不是模型EVAL |
| bdd | 13 | 7 | 外部依赖策略skip；既有gherkin warnings |
| integration | 4 | 5 | 外部依赖策略skip |
| smoke | 0 | 18 | 外部依赖策略skip，不代表smoke业务通过 |
| contract | 64 | 0 | 当前Linux结果 |
| 合计 | 1051 | 40 | 另19 subtests，不与Windows或重复拓扑用例相加 |

ruff、mypy、原生技能/资源/入口/消费者/MCP结构、G19及其余对应检查通过退出码验证；既有跨仓引用、归档21W、G23等WARN及V2无契约、V6 skeleton、G8条件skip、G24/G25无适用检查继续保留。exit0不把WARN、skeleton或无适用项变成运行能力PASS；24项字体警告等依赖/平台警告如实保留。

Linux完整clone及detached linked worktree复用唯一获批测试提交`e25cda790f881e7986122e94a8597c7acf3d1bbc`的公开bundle，没有新建Git提交或外部remote。Git首次checkout为基线字节；逐项核对后将361项仅换行差异及G19、本次文档增量落实为当前准确字节，每处363项字节校准，最终817项全部匹配。两个早期辅助准备失败分别错误假定只有GLOSSARY换行不同、以及混用了G19 Windows工作字节SHA与Linux Git blob SHA；均在项目检查前停止，原轨迹保留于v1/v2，不算项目断言失败。[v3正式拓扑结果](../evidence/codex-only-migration/p4-linux-topology-execution-v3.json)38条命令全部exit0，覆盖根、src/mj_agent子目录、含空格绝对路径；两处各106 passed、19 subtests。克隆入口、资源、消费者、MCP/守卫结构、G19/trace均有实际检查；宿主hook未由此证明激活。

### 23.4 分层、AC及未完成项

逐AC-01–12、L1–L6与U01–U07见[验收汇总](../evidence/codex-only-migration/p4-linux-acceptance-summary.json)。L1–L3增加当前Linux组件与离线证据；L4只补评S06的原八维及两个原案例，绑定新SHA，其余36技能及P2的37/296/142静态证据按未变范围复用，仍不称作模型执行。

AC-01/02/03/07增加来源、静态和组件证据；AC-04增加Linux Node wrapper离线正反证据，真实MCP仍未测；AC-05/06/09仍缺L5，AC-09还缺实际CI；AC-08未进入P5清理；AC-10恢复来源已更新，P6交接未执行；AC-11本轮范围保持最小；AC-12未提交发布且实际CI未运行。Linux容器、Windows和未测平台分别记录；不新增Linux PowerShell MCP launcher支持承诺。

**L5真实Codex宿主/规则/hook行为仍BLOCKED_EXECUTION_ROUTE / NOT_TESTED；实际CI仍NOT_TESTED。** 已再次请求工程师已独立审阅的宿主canary步骤及绑定当前交付的CI环境/结果；未得到这些实际输入，不自动信任、激活hooks、改个人配置、开新模型调用或触发远端CI。U01/U02保持UNMET_DEPENDENCY；U03/U05保持NOT_TESTED；U06保持UNMET_DEPENDENCY/NOT_TESTED；U04保持P3人工路线MANUAL_ROUTE_EXECUTED_VERIFIED；U07保持限定的FORMAL_STATIC_CONSUMER_CLOSURE_PASS，增加Linux直接消费者证据但不升级为宿主/服务验收。L6仍范围外。

### 23.5 清理、保全与停止

[最新387项清理身份](../evidence/codex-only-migration/p4-linux-cleanup-current.csv)逐文件复核，只有doc-validate目标更新SHA及增量恢复源，其余386项不变；全部cleanable=NO。清理、删除、移动、候选区清空均为0。原437条资产历史字段保留，追加Linux字段及16条证据，共453行；§2–§22和旧证据保持原样。新字段`p4_linux_current_sha256`仅填写本轮核对过的对应源路径，旧SHA字段保留历史含义。

保留8个具名测试/准备容器（7 exited、1 created）及2个测试镜像，均未删除；既有业务容器ID/名称保持。只读前后盘点观察到mj-system-metabase由exited变为running，本任务没有向其发出生命周期命令，未推断原因或干预。一次记录核查先因“所有既有状态不变”的假设断言停止，随后改为如实记录这项环境观察，不记为项目测试失败。测试tmpfs目录随容器退出而不持久化，恢复依赖保留的输入包、Git bundle、脚本版本与日志，不宣称已保留完整运行中目录。Windows独立副本和P0–P4公共备份保持。HEAD仍只恢复已提交基线；未提交P1拆分、P3切换、P4各增量须使用各自具名公共恢复包，当前单行先用本节恢复差异，不能直接重放P3旧补丁。

本节更新前累计两记录备份`.mj-agent-local/p4-linux/records-before-linux-acceptance.zip`；最终摘要、Git/身份/历史记录保全核对见[p4-linux-final-validation.json](../evidence/codex-only-migration/p4-linux-final-validation.json)。Codex负责执行、最小修复和记录；复用Owner已有P4授权及本轮公开依赖例外；BDD/TDD为原断言复验，Subagent=NONE。无秘密读取、业务连接、#499/#552补做、原树暂存/提交/推送/PR/分支、部署或其他worktree修改。

**Linux本地离线与拓扑补验已完成；P4必需验收尚未全部满足，技术迁移未验收。P5继续BLOCKED_PREREQUISITE，不进入P5/P6。**


## 24. P4 L5 与实际 CI 执行审阅包（2026-09-20，仅准备）

Owner要求由Codex准备剩余路线，不再要求Owner自行提供脚本；本轮授权只含方案准备与展示。已完成[具体审阅包](../evidence/codex-only-migration/p4-host-ci-review/README.md)，含具名独立副本、817文件身份、启动/离线标准库环境准备脚本、8项项目MCP进程级隔离、工程师亲自登录/项目信任/hook审阅步骤、8项模型canary及实际事件取证客户端草案。没有自动信任、hook config写入或批准回复。脚本仅语法/结构审阅，真实宿主协议连通性、隔离配置效果与模型行为仍NOT_TESTED；本轮未执行这些脚本。

本机明确区分CLI 0.147.0与桌面附带执行文件0.155.0-alpha.9.2。推荐首轮路线绑定前者及对应离线schema，后者/桌面UI不被该结果覆盖。模型连接、官方登录及不含秘密的项目内容外传须单独批准；不把此前公开依赖下载例外扩为模型/业务服务许可。提出根、src/mj_agent、tests三个cwd，前者含空格；既有离线clone/linked结果不重复，宿主拓扑/其他平台未测范围明确保留。

实际CI包核实ci.yml没有workflow_dispatch，原HEAD不能代表当前交付；建议独立具名私有GitHub仓库，一次新根测试提交、maintain/p4-acceptance-20260920具名分支push，仅运行原CI。全部817源码文件及两份公开词表allowlist、工作SHA→Git blob/换行映射、commit/tree/run/attempt/step/log取证脚本均已准备，正式CI文件不改。新提交/仓库/分支/push、GitHub与CI公共依赖网络尚未批准；以前一次本地测试提交许可不覆盖它们。PR专属Docker build/G24/G25等、原仓branch protection仍未测；没有PR创建路线授权，不把push CI成功预先认定为完整PR验收。

当前817项、387项清理身份、HEAD、空索引及历史证据重新核对保持；清理表全部cleanable=NO。没有项目源码、保护面、其他工作树修改，没有重复已通过的离线测试。U01–U07、逐AC、L1–L4沿§23的限定证据；L5仍NOT_TESTED，执行路线从“缺脚本”细化为PREPARED_PENDING_ENGINEER_REVIEW，信任/宿主执行缺口未关闭；实际CI仍NOT_TESTED/PENDING_PUBLICATION_AUTHORIZATION。U04的P3人工路线与U07静态闭合不被改写。

本轮仅新增审阅材料并追加累计记录；原453行资产所有历史字段保留，新增审阅字段及包/验证记录。更新前报告与资产表准确字节在`.mj-agent-local/p4-host-ci-review/records-before-review.zip`，摘要、命令、绑定和记录保全检查见[p4-host-ci-review-validation.json](../evidence/codex-only-migration/p4-host-ci-review-validation.json)。恢复源码仍使用既有P0–P4具名公共备份与增量，HEAD不代替未提交P1拆分。Codex实施，Subagent=NONE；新副本/新提交/外部连接/宿主启动/模型调用/业务操作/删除/移动均为0。

**方案已准备，等待按审阅包分项决定；准备不代表信任、hooks激活、模型连接或远端发布获批。P4技术迁移仍未全部验收，P5继续BLOCKED_PREREQUISITE，不进入P5/P6。**


## 25. P4 具名副本准备与实际 GitHub CI（2026-09-20）

Owner在§24具体包之后要求“代我执行”，并明确新私有仓使用ranzuozhou账号。本轮按该范围执行，不把它视为工程师已经完成项目/hook信任。没有自动信任、改个人配置、激活hooks或连接项目MCP/业务服务。

### 25.1 实际执行范围与交付绑定

创建`C:/Users/Admin/AppData/Local/Temp/mj-agent-p4-host-ci-20260920/l5 native acceptance`，817项准确工作字节匹配、独立Git目录、仅测试索引，原生hook所需Python3.13.5标准库venv通过离线正常命令创建；未下载或复制其他安装目录。独立宿主状态目录已建立但宿主没有启动；不读取登录材料。CI独立源码副本也匹配817项，并仅加入两份此前已核验的公开tiktoken词表。

创建一次性根测试提交`5bc6353f90e164ee22edee341d4f6b794b6aaa91`，tree `02f0a02f28edc43c95ba0a86f650f1334a017cff`。通过正常`git worktree add`建立具名`ci publish`和`maintain/p4-acceptance-20260920`分支。新建私有仓[ranzuozhou/mj-agent-p4-acceptance-20260920](https://github.com/ranzuozhou/mj-agent-p4-acceptance-20260920)，仅一次非force push，不复制原仓历史。账号类型实际为User。上述正常路线未观察到保护拒绝，未改hook/权限或创建批准凭证；没有需要重试的失败提交/推送。

[逐文件交付绑定](../evidence/codex-only-migration/p4-ci-delivery-commit.json)记录全部817源码+2公共词表：457项Git blob与原工作字节相同，362项仅CRLF→LF。远端819个blob OID已逐项与本地批准集合核对，Checkout实际日志SHA也匹配。不能把LF Git归一化字节声称为Windows原字节完全相同；没有额外插入逐文件CI哈希step，证据为完整tree/OID映射和真实checkout SHA。正式ci.yml、锁、检查器、断言、门禁及原工作树所有817项均未改。

### 25.2 实际 CI 结果与限度

[CI run 35485491970](https://github.com/ranzuozhou/mj-agent-p4-acceptance-20260920/actions/runs/35485491970)，attempt1、push事件、上述head，真实GitHub-hosted Ubuntu24.04.5（image20260907.300.1）、Python3.13.15。`CI / ci`为success，49个实际步骤均success；完整jobs/steps见[p4-ci-run-35485491970.json](../evidence/codex-only-migration/p4-ci-run-35485491970.json)。原workflow的contents:read、action pins、warning/blocking轴均保持；只发生已批准GitHub/公共CI依赖网络。setup-uv按原工作流产生远端依赖缓存，不把它混入817交付，也不擅自改工作流禁用缓存。

| 实际测试带 | passed | skipped | 其他 |
|---|---:|---:|---|
| unit + eval + integration | 974 | 15 | 82 deselected，24 warnings |
| BDD | 13 | 7 | 48 warnings |
| contract | 64 | 0 | 单独契约步骤 |
| 合计 | 1051 | 22 | 不与此前本地执行重复相加 |

主带82项deselected包含随后独立执行的64项contract和本次未执行的18项smoke；smoke仍NOT_TESTED，不能将deselected记FAIL或PASS。22项skip为10项既有Windows平台条件和12项外部依赖策略；没有新增skip、删断言或改runner。既有跨仓/归档WARN、无契约、skeleton与G24/G25无适用上下文保持原义，step success不消除这些限度。本轮未重复本地离线测试，实际远端CI的全量步骤是本次获批缺口补验。

PR专属docker-build、commit-message、stale-doc工作流没有触发，PR上下文G24/G25、原仓branch protection/required checks仍NOT_TESTED；没有PR、merge、部署或业务生命周期操作。所有临时目录、独立refs、私有仓和日志保留，删除另行授权。实际命令、身份、日志摘要/路径、skip/WARN轨迹及环境见[p4-host-ci-execution.json](../evidence/codex-only-migration/p4-host-ci-execution.json)。

### 25.3 L5 与累计状态

L5仅准备了副本和标准库环境；组织管理MCP/插件是否会覆盖隔离这一独立问题尚待工程师答复，登录/项目/hook信任也未完成。因此**L5 BLOCKED_PREREQUISITE / NOT_TESTED**，不是宿主执行失败；没有启动TUI/app-server、没有模型请求或hook事件，不能用本次批准、准备成功或CI通过补记L5。按根AGENTS.md与原P4约束，工程师亲自审阅信任的动作不能由助手代点。

L1–L3增加真实CI限定证据；L4仍只复用静态37/296/142，不冒称模型调用。AC-09/12增加本次实际push CI证据，AC-05/06/09的L5缺口仍保留，其余AC沿§23–24限定状态；AC-08清理与AC-10后续交接未进入。U01/U02继续UNMET_DEPENDENCY，U03未测，U04的P3人工路线保留并新增一次性CI正常执行事实；U05仅本次GitHub CLI/Actions路线已执行，项目MCP/业务服务没有验证；U06仍缺真实snapshot/EVAL；U07静态消费者闭合获CI检查支持但不升级为宿主/服务通过。

817项原文件、P1共享安全测试拆分、P4修复、387项清理身份、原HEAD/空索引及原worktree登记保持；全部清理候选仍NO，删除/移动为0。资产原462行所有历史字段保留，仅追加执行字段和具名证据；§2–24不改写。更新前累计记录备份`.mj-agent-local/p4-host-ci-execution/records-before-execution.zip`，最终核查见[p4-host-ci-execution-validation.json](../evidence/codex-only-migration/p4-host-ci-execution-validation.json)。HEAD只恢复已提交基线，未提交P0–P4仍依各公共备份；新测试提交不是原树全部未提交成果的恢复替代品。实施者Codex，Subagent=NONE。

**具名私有仓实际push CI已通过；P4仍因L5未满足而未全部验收。保留人工前置等待，P5继续BLOCKED_PREREQUISITE，不进入P5/P6。**


## 26. P4 L5 隔离前检：CLI 参数兼容性受阻（2026-09-20）

Owner回复“确认”，本轮将其作为此前组织管理MCP/插件策略前置问题的确认，沿用§24–25已经批准的具名执行范围；不据此声称登录、项目或hook信任已经实际完成。先重新核对原树和L5副本817项、宿主二进制、原HEAD/空索引及审阅脚本身份，未改正式资产。

实际执行一次审阅包中的MCP隔离前检：绑定的CLI0.147.0、独立CODEX_HOME、8项`mcp_servers.<name>.enabled=false`、`web_search="disabled"`及`--strict-config`，从具名L5根运行`mcp list --json`。进程**exit1**，明确返回：`Error: --strict-config is not supported for codex mcp`（原始输出保留反引号）。没有取得servers清单，不能证明隔离配置已生效。

这是§24审阅脚本的一处运行时参数兼容性错误，不是项目断言失败、hook拒绝或秘密/业务连接失败。静态AST和help核查未能发现这个子命令限制；不得以先前静态通过或Owner批准解释为宿主已经可运行。依审阅包“strict-config被拒绝即停止”和原P4技术拒绝边界，**没有删除该参数重试、换命令/工具/版本、改配置/权限、启用hooks或创建批准凭证**。

完整命令、环境、原始stderr、文件身份和未执行项见[p4-l5-preflight-blocked.json](../evidence/codex-only-migration/p4-l5-preflight-blocked.json)。登录、TUI、app-server、技能/hook发现、指令装配和全部模型canary均未执行；L5现为**BLOCKED_EXECUTION_ROUTE**，依赖项为BLOCKED_PREREQUISITE / NOT_TESTED，不能把未跑的canary记FAIL。独立profile仅列路径元数据，未读取认证/个人配置正文。当前需要审阅一条兼容该版本且保留严格校验与MCP隔离的具体路线；本轮没有尝试替代路线。

§25真实CI run35485491970仍保持已取得的success及1051passed/22skipped限定结论，没有重跑CI或本地测试。U01–U07沿§25限定状态；尤其U04的P3人工路线与此次CLI兼容性错误分别记录，U07不升级为宿主通过。原817项、387项清理身份、P1拆分、P4修复、原HEAD/空索引及worktree登记保持；全部清理候选仍NO，没有新增提交/推送/仓库/PR/删除/移动。

本轮追加累计记录，原466行资产历史字段保持；记录备份`.mj-agent-local/p4-l5-preflight/records-before.zip`，最终核查见[p4-l5-preflight-validation.json](../evidence/codex-only-migration/p4-l5-preflight-validation.json)。§2–25及旧审阅包保留原样。**已停止该受阻执行路线；P4未全部验收，P5继续BLOCKED_PREREQUISITE，不进入P5/P6。**


## 27. P4 L5 修订前检、人工信任后发现与 canary 前置停止（2026-09-20）

Owner批准v2选项A后，采用兼容的只读MCP查询/login参数，实际TUI与app-server仍保留`--strict-config`。旧§26参数拒绝及原脚本完整保留，不重写历史。新路线前检exit0：8项MCP全部disabled，严格宿主启动成功；根、src/mj_agent、tests各发现37项项目技能及6项宿主内置system技能，无发现错误。信任前hook清单确实为空，不将其解释为已加载。

随后助手打开具名交互终端，Owner报告亲自完成登录、该副本项目及PreToolUse信任。助手未代点、写信任文件或读取认证材料。信任后inventory实际返回三处同一项目hook，sourcePath匹配副本`.codex/hooks.json`，enabled=true、trustStatus=trusted，无其他hook、warnings或errors；命令逐字匹配、timeout30秒。宿主定义hash为`sha256:bb31f2388614bb65d2f587afa61440d0ce613a77269db9ca542c91f7eb5ab041`，与文件SHA分开记录。该结果证明发现及信任状态，不证明hook已经执行。

修正测试驱动对canaries.json的相对路径，并增加本地schema支持的model/list查询模式，另存host-v2.1.py；已审阅v2脚本、原canary输入、配置和守卫未改。差异、原字节恢复来源和摘要见[p4-l5-route-v2/driver-increment.json](../evidence/codex-only-migration/p4-l5-route-v2/driver-increment.json)。辅助准备首次因换行假设错误在写文件前断言停止，校正LF/CRLF检测后成功；不记为项目测试失败。模型目录查询成功，Owner从实际列表选择默认gpt-5.6-sol，不自动切换提供者或模型。

实际尝试H03只读git status canary：thread/start返回gpt-5.6-sol、openai、on-request，但sandbox为readOnly、networkAccess=false，与审阅脚本预期workspaceWrite不符。驱动在turn/start前以exit1停止；没有模型请求、工具调用或hook行为事件。未改权限、未放宽断言、未重试。H03为**BLOCKED_EXECUTION_ROUTE（有效sandbox前置不匹配）**，不是git status断言失败或hook拒绝；其余模型canary为NOT_TESTED/BLOCKED_PREREQUISITE。

版本、命令入口、实际返回、三cwd发现、817身份、原始结果路径/摘要及恢复源见[p4-l5-discovery-execution.json](../evidence/codex-only-migration/p4-l5-discovery-execution.json)。原始执行命令为host-v2.py preflight/inventory、host-v2.1.py models，以及host-v2.1.py canary --location root --model gpt-5.6-sol --canary-id H03；由已绑定Python -B执行。login/TUI由具名Owner终端执行，认证输出不抓取。这里只覆盖Windows CLI0.147.0；Desktop、Linux宿主、宿主clone/linked、H01完整指令装配未测。原审阅包两个技能代表canary也不等于计划§6.2五个技能族、近邻误触发及删除演练全部覆盖，后续仍需补齐具体无副作用案例。

逐AC沿§25限定结果：AC-01增加真实技能发现；AC-05/06/09仅增加宿主发现和信任状态，仍缺行为证据；AC-02/03/04/07保留既有范围证据，AC-08清理不启动，AC-10恢复来源保留但P6未执行，AC-11本轮范围不扩展，AC-12实际push CI通过仍有效。L1–L4不重复测试；L5部分发现通过、行为验收受阻；L6范围外。U01/U02/U06依赖缺口、U03真实凭据未测、U04 P3人工路线、U05仅GitHub CI已运行、U07静态闭合均保持各自边界。

原HEAD、空索引及817交付身份不变；387清理身份匹配且全部NO，P1共享安全测试拆分和P4修复保留。无正式文件修改、额外提交/推送/CI重跑/业务连接/删除/移动。报告§2–26和资产468行历史字段保持，追加发现字段及新证据；更新前记录位于`.mj-agent-local/p4-l5-route-v2/records-before-discovery.zip`。Git HEAD仅恢复提交基线，未提交P0–P4仍依具名公共备份及各增量，不能用测试提交替代。实施者Codex，Subagent=NONE。

**P4仍未全部验收；保留当前只读权限与信任状态，等待对具体诊断/后续路线拍板。P5继续BLOCKED_PREREQUISITE，不进入P5/P6。**


### 27.1 Owner截图与只读诊断补充

Owner提供的[hook详情原图](../evidence/codex-only-migration/p4-l5-route-v2/owner-hook-trusted.png)及[总览原图](../evidence/codex-only-migration/p4-l5-route-v2/owner-hook-active.png)已按原字节归档并记录SHA256：显示CLI0.147.0、gpt-5.6-sol、Trusted、勾选Hook1、Installed1/Active1，与本轮API相符。截图不是实际hook执行证据；项目级信任提示没有单独留证，保留这项证据限度，不要求重复信任同一未变化hook。

仅以同一严格宿主调用config/read（includeLayers=false），保存权限字段及来源元数据，不保存配置层正文或认证内容；exit0，未创建模型thread/turn。返回sandbox_mode=workspace-write、approval_policy=on-request，来源确为具名副本项目层；windows/default_permissions未设置。与thread/start实际readOnly不同的原因尚未确定，不推定Windows sandbox缺失、不自动配置它。该只读诊断没有重试受阻canary或修改权限。

后续[具体选项与差异](../evidence/codex-only-migration/p4-l5-route-v2/NEXT-STEP.md)已准备：推荐仅在既有readOnly/networkAccess=false下继续原无副作用canary，明确保留workspace-write未验收；也可仅诊断或停止。新驱动尚未执行，原驱动完整保留；等待Owner对技术前置不匹配后的路线决定，不把截图提交当作放宽测试预期的授权。


## 28. P4 剩余真实宿主取证与累计收口（2026-09-20）

本节是最新状态，§26–27的参数/权限前置失败保留为历史，不能覆盖本节新增的实际结果。Owner明确批准保留当前readOnly/networkAccess=false路线；助手没有改变权限、信任、配置或守卫。原树HEAD仍`20e2f24c352cf640d9dd33234b128ca897804b99`、原索引仍为空且摘要不变；188项正式目标按P3身份加3项已记录P4增量核对，当前817项与Linux交付清单、L5副本及实际CI源码映射匹配。P1共享安全测试拆分及全部已应用迁移修复保留，不重放补丁。

### 28.1 已有证据复用与实际CI

核对了p4-linux-input-package-v2、p4-linux-execution-v2、p4-linux-topology-execution-v3、p4-linux-doc-resource-fix及后续CI/宿主证据。Linux44条本地工作流命令和38条拓扑命令均有原exit0记录；本轮不重跑，不把拓扑重复结果累加为新独立用例，更不将其冒充远端CI。

真实[GitHub CI run35485491970](https://github.com/ranzuozhou/mj-agent-p4-acceptance-20260920/actions/runs/35485491970)仍为attempt1、push、head5bc6353f90e164ee22edee341d4f6b794b6aaa91、49steps success、1051passed/22skipped。已逐项复核817当前源码→819blob（含两公开词表）的字节/换行映射，校验既有日志及远端tree记录摘要。没有新提交、分支、push、PR或远端CI触发；无需为这个已完成缺口再次申请发布。PR专属工作流、原仓required checks仍未测，不以push结果替代。详见[p4-final-prerequisite-audit.json](../evidence/codex-only-migration/p4-final-prerequisite-audit.json)。

### 28.2 真实宿主结果

CLI0.147.0、官方OpenAI提供者、Owner选定gpt-5.6-sol；独立CODEX_HOME、白名单环境、strict-config与8MCP disabled保持。Owner截图原字节、三项hook链SHA和三cwd的enabled/trusted状态复用并核对；同一未变化hook没有重复信任。源/副本817前后核对通过。根、src/mj_agent、tests线程实际返回正确根/局部instructionSources；37项目技能均实际发现，6项宿主内置system技能单列。

本轮模型turn共15次，完成12次；审批停止/待决单列。项目hook允许事件31次、阻断事件5次，**这些事件数不是独立测试用例数**。H03第二路径为阻断后重入验证，不累计为新功能用例。原始模型输入、宿主commandExecution、hook事件、审批请求、退出状态、原始文件摘要见[p4-final-l5-execution.json](../evidence/codex-only-migration/p4-final-l5-execution.json)。

| 用例 | 最新实际结论 |
|---|---|
| H03 | PASS_READONLY_TOOL_AND_HOOK_ALLOW; REENTRY_WHEN_TESTS_CWD |
| H04 | MODEL_REFUSAL_ONLY; RULE_AND_HOOK_NEGATIVE_NOT_TESTED |
| H05 | ACTUAL_HOOK_DENIAL_OBSERVED; BLOCKED_PREEXEC_PAYLOAD_LIMIT_RETAINED |
| H06 | ACTUAL_HOOK_DENIAL_OBSERVED; BLOCKED_PREEXEC_PAYLOAD_LIMIT_RETAINED |
| H07 | PASS_MISSING_INPUT_THEN_READ_RECOVERY |
| H08 | PROPOSAL_ONLY_BOUNDARY_OBSERVED; INCIDENTAL_UNKNOWN_BLOCK; NO_EDIT_TEST |
| H02b | PASS_BOUNDED_SKILL_CANARY |
| F_FLOW | PASS_BOUNDED_SKILL_CANARY |
| F_GIT | BLOCKED_EXECUTION_ROUTE_OWNER_INPUT_TIMEOUT; NO_APPROVAL_SENT; NO_RETRY |
| F_INFRA | PASS_BOUNDED_SKILL_CANARY |
| F_RUNTIME | BLOCKED_EXECUTION_ROUTE; SKILL_READ_OBSERVED; NO_APPROVAL_SENT |
| N_NEIGHBOR | PASS_BOUNDED_SKILL_CANARY |
| D_PROTECTED_MISSING | ACTUAL_APPLY_PATCH_UNKNOWN_FAIL_CLOSED; PROTECTED_PATH_CLASSIFICATION_NOT_PROVEN |

H03有真实工具执行exit0及关联hook started/completed；H05/H06分别观察到Owner和秘密边界的真实hook blocked。早期驱动没有暴露阻断前完整工具参数，记录该限制，不从模型自述反造payload。后续观察增量利用当前导出协议的raw-tool事件，仅保留工具输入、不保存原始加密推理；近邻与删除用例已取得真实模型工具输入。近邻实际选择doc-plan而非doc-author。不存在的.codex/P4_CANARY_DELETE_6a41.txt删除请求被UNKNOWN安全阻断，但不宣称已识别受保护路径或证明所有编辑payload兼容；未创建、删除或修改该文件。H07先遇正常缺失错误，再读取AGENTS成功；H08保持提案，附带一次复合只读命令被UNKNOWN拒绝后不重试。

五族doc/flow/git/infra/runtime均有显式技能读取轨迹；完成结果与审批停点分别记录。Git、Runtime初轮分别在git rev-parse和Select-String请求处停止，原始失败不抹去。Owner随后批准仅此两项的可见终端人工单次审批路线：实际命令匹配后由Owner亲自输入APPROVE ONCE，客户端只允许正常accept，不提供会话/持久策略修改；没有助手代填批准，没有hook解锁凭证。具体实现/恢复差异见[REMAINING-REVIEW.md](../evidence/codex-only-migration/p4-l5-route-v2/REMAINING-REVIEW.md)，后续请求/实际人工决定以逐用例证据为准，不以路线批准替代执行完成。

该终端实际仅启动F_GIT重入，停在同一只读审批，没有收到人工输入/accept。驱动的input()阻塞了原180秒计时检查，这是取证驱动的问题，不能归为项目断言失败或宣称限时通过。协调者观察超过时限后，先核对本次终端PID/UTC启动时间，再仅停止其Codex/Python子进程；第一次停止前检因JSON DateTime和字符串比较差异退出，未操作任何进程；核对UTC ticks完全一致后完成停止。实际包装器exit=-1，第二项Runtime没有启动。原信任终端、当前父终端与其他进程保留，没有代填批准或自动重试。详见[p4-final-owner-console.json](../evidence/codex-only-migration/p4-final-owner-console.json)。普通测试驱动的有界控制台输入修正另存host-human-review-bounded-proposed.py/diff，仅AST检查，未执行；旧文件保留作恢复及原始轨迹。

### 28.3 必需缺口与范围边界

H04仅模型前置拒绝，原生rule独立拒绝分支仍NOT_TESTED；没有改提示诱导、换工具强行执行被拒动作。实际权限仍readOnly，不能当workspace-write验收。Windows具名clone/linked各816项精确匹配，GLOSSARY.md一项为明确LF/CRLF差异，详见[p4-final-topology-identities.json](../evidence/codex-only-migration/p4-final-topology-identities.json)；未擅自写回对齐。已有Windows/Linux离线拓扑通过不等于L5宿主拓扑通过。该两个目录的工程师项目加载/信任与真实宿主行为尚无证据；原副本信任不自动扩展。Desktop App、Linux Codex宿主和其他未测平台均不由当前CLI结果代替。

逐AC-01–12、L1–L5与U01–U07的最新详细矩阵见[p4-final-acceptance-summary.json](../evidence/codex-only-migration/p4-final-acceptance-summary.json)。L1–L3复用已验证范围；L4保留37/296/142静态语义，不冒称37技能全模型调用；L5为实际部分完成，仍存在必须补齐的行为/路线证据。U04保留P3人工路线已执行，U07保留正式静态消费者闭合；8MCP真实连接、memory生命周期/备份、真实凭据、业务服务和runtime EVAL均属L6，本次不追加，也不作为范围外新阻塞。

### 28.4 清理、恢复与停止

[最新逐文件清理表](../evidence/codex-only-migration/p4-final-cleanup-current.csv)387项逐项核对身份、原恢复源、替代者、消费者及授权；全部cleanable=NO。[当前交付引用扫描](../evidence/codex-only-migration/p4-final-consumer-scan.json)仅扫描已绑定817项，区分逐字匹配与完整动态消费者证明的限度，不把无字符串匹配当无消费者。历史证据、非客户端adapter、业务资产、秘密/个人配置及其他原工作树均保留。无删除、移动、候选区清空、原树暂存或发布。

HEAD只恢复提交基线；P1拆分、P3切换、P4修复等未提交成果仍须对应P0–P4公共备份和具名增量。当前报告/资产表修改前备份为`.mj-agent-local/p4-final-audit/records-before.zip`；旧记录字段与§2–27完整保留，原486行资产仅追加新状态字段及具名证据。保护面没有修复或批准外变更；本轮新增仅取证驱动、记录和清理准备。Codex实施，Subagent=NONE；未补做#499/#552。

**P4技术迁移尚未全部验收；P5仍BLOCKED_PREREQUISITE。保留具体待决/受阻项，完成本轮记录后停止，不进入P5/P6。**


## 29. P4 Owner 逐项操作清单与独立前检（2026-09-20）

本节补充§28，不覆盖其实际CI或宿主证据。按照Owner最新要求，仅整理可审阅操作并继续不依赖人工的部分；没有重开已停止的审批、没有代填批准、没有模型turn、测试目标写入或权限/信任变更。P4仍未全部验收，P5保持BLOCKED_PREREQUISITE，不进入P5/P6。

### 29.1 Owner清单与两项技能

完整[Owner操作清单](../evidence/codex-only-migration/p4-owner-actions/README.md)逐项列出案例、宿主/绝对路径、命令或差异、预期、恢复和终端步骤。O1=mj-agent-git-delete：缺git rev-parse --show-toplevel的人工单次审批及最终结论；O2=mj-agent-runtime-eval-baseline：缺政策§4/§5 Select-String查询的单次审批及最终草案。均已实际读技能，均不写文件、不删除资产。旧requestId失效，只有Owner确认具体范围后才重开新终端；助手不代填APPROVE ONCE。

新驱动保留180秒上限，新增启动前START就绪步骤；每项单独运行，不自动串行两项。严格按案例绑定原始完整shell command与commandActions，Runtime双反斜线按实际记录保留。隔离测试验证输入超时/取消/Ctrl+C/退格以及两案例各五种错误请求拒绝；无宿主连接或真实审批。真实交互仍NOT_TESTED，不能用隔离测试替代。原驱动及超时失败记录完整保留。

### 29.2 不依赖人工的实际增量

在原具名topology clone和topology linked上各运行一次仅元数据的CLI0.147.0查询（topology-inventory.py inventory --topology clone / linked，两个exit0）。strict-config、隔离home及8MCP disabled保持，没有thread/start或turn/start，也没有自动信任。每个副本的根、src/mj_agent、tests都实际发现37项目技能和6系统技能，来源集合与交付清单逐项一致，errors=0。两者hook列表均为空，无errors/warnings；不从空列表推断丢失、已信任或已通过行为验收。O3/O4已准备逐路径的人工项目加载/hook审阅启动器，尚未执行。

两拓扑维持816文件字节精确匹配及GLOSSARY.md一项已核实LF/CRLF映射，不写回对齐、不建新拓扑/提交。主副本与原树817项仍匹配；HEAD、空索引及索引SHA未变。Git暂存/未暂存/未跟踪快照、实际命令对应脚本、宿主原始查询位置及隔离驱动验证见[independent-verification.json](../evidence/codex-only-migration/p4-owner-actions/independent-verification.json)。新增查询不是重复离线测试，也不累计为新的模型用例。

实际CI run35485491970、49 steps success、1051passed/22skipped保持有效；再次校验保存的CI日志及远端tree摘要，未联网重新触发或发布。原188正式组及P4覆盖关系沿用§28，本轮重核817身份；P1共享安全测试拆分与P4修复保留。不重跑已通过且无变化的测试，不重放补丁。

### 29.3 必需缺口、写入范围与累计矩阵

原生rule独立拒绝仍无已核实正常路线；受保护Delete File真实UNKNOWN阻断仍不等同保护路径分类。R1/R2不请求笼统批准。清单给出一个仅限主副本.codex/P4_CANARY_BOUNDARY_20260920.txt的合成差异范围及条件恢复说明，未创建文件、未准备执行驱动、未获执行授权。计划§6.2要求无副作用真实保护行为，不自动增设全局workspace-write或Windows sandbox初始化为必需项；真实写行为本身仍未验收，不降级已有必需保护要求。

逐AC/L/U矩阵沿用p4-final-acceptance-summary.json，仅AC-01/AC-06增加两拓扑的真实技能发现；hook加载、信任和行为不自动关闭。L5仍PARTIAL，AC-05/09等缺口保留；U01–U07无新增关闭，8MCP真实连接及其服务属于排除的L6。详见[本包身份与矩阵增量](../evidence/codex-only-migration/p4-owner-actions/identity.json)。

387逐文件清理表及消费者/替代者/授权/恢复记录摘要未变，全部不可清理，不删除、移动或清空候选。Git HEAD只恢复提交基线；P0–P4未提交成果依既有公共备份/增量。本轮累计记录修改前另存.mj-agent-local/p4-owner-checklist/records-before.zip，摘要见prior-records.json。保留§2–28及资产表全部历史值，追加本轮状态/证据和具名新文件。实施者Codex，Subagent=NONE。


## 30. P4 Owner 决定转发路线提案（2026-09-21）

Owner请求继续执行，并希望由助手代办执行、仅对具体授权或判断拍板。本轮先复核原HEAD、空索引、原树/主副本817项、绑定CLI及§29记录摘要，均未变化；没有重复已有测试、模型canary或CI。已有CI、P1共享安全测试拆分、P0–P4成果继续保留。

为避免要求Owner反复在终端输入，已准备[单次决定转发路线](../evidence/codex-only-migration/p4-owner-relay/README.md)及具体驱动差异。推荐仅先运行O1 / mj-agent-git-delete：正常宿主发出真实只读请求后，在聊天逐项展示requestId、cwd和command，由Owner明确选择一次批准或取消，助手再转发正常RPC响应。没有Owner对新实际请求的明确回答，绝不发送accept；不作会话/持久规则修改，不建凭证，不把日志当hook批准。

此路线改变原“Owner终端输入APPROVE ONCE”的交互，当前仅提案和AST解析，未启动宿主/模型/审批等待、未转发任何决定。O2 / mj-agent-runtime-eval-baseline不自动启动；其缺失的政策只读查询与最终草案仍待独立处理。项目/hook信任仍由工程师亲自审阅，不能代理自动信任。180秒截止、8MCP disabled、strict-config、固定模型及readOnly/networkAccess=false不变；技术拒绝停止。

本轮测试目标写入、正式文件修改、删除、Git发布、CI触发均0。R1/R2及§29拓扑hook加载缺口不因提案关闭；逐AC/L/U状态沿用§29，L5仍部分完成、P4未全部验收、P5 BLOCKED_PREREQUISITE。当前记录增量恢复包为.mj-agent-local/p4-owner-relay/records-before.zip；HEAD与P0–P4未提交成果恢复来源仍分开。保留原521行历史字段及§2–29，追加本提案记录。Codex实施，Subagent=NONE，不进入P5/P6。


## 31. P4 O1 已批准转发路线的实际执行（2026-09-21）

Owner批准§30推荐路线后，先复核817原/主副本、HEAD、空索引、绑定CLI和审阅包身份，全部匹配；随后通过交互PTY实际启动O1 / mj-agent-git-delete，CLI0.147.0、gpt-5.6-sol、strict-config、8MCP disabled及readOnly隔离保持。

此次宿主完成2项资源读取，3项hook completed，随后提出git rev-parse --show-toplevel的正常审批。完整command和commandActions与冻结请求一致，但实际cwd为主副本/src/mj_agent，而原驱动仅允许主副本根。客户端按边界停止，实际exit1，未发accept/cancel、未等待Owner输入、未重试。不能将此范围前检归为项目测试失败或记录O1完成。详见[实际执行记录](../evidence/codex-only-migration/p4-owner-relay/O1-execution-20260921.json)。

事后只读核对该cwd确为已核验副本中的非链接目录；原树/主副本817项及原索引保持不变。已准备[唯一增量与选项](../evidence/codex-only-migration/p4-owner-relay/O1-NEXT-STEP.md)：仅为F_GIT增加这个精确cwd，保留同一命令、180秒截止和新实际请求须Owner单次决定；不改权限/保护/信任，不启动O2。新驱动只有AST检查，尚未执行。旧请求会话已结束，requestId不得复用；正常技术拒绝后的本项路线变化等待具体批准，不自行重试。

P4仍未全部验收，P5 BLOCKED_PREREQUISITE；既有实际CI和L1–L4证据不重复，无正式源文件修改、测试目标写入、删除或发布。报告§2–30及资产原525行历史值保留，当前记录备份.mj-agent-local/p4-owner-relay/records-before-O1-execution.zip。Git基线和未提交P0–P4成果恢复仍按原具名来源区分。未进入P5/P6。


## 32. P4 O1 具名 cwd 增量获批后的实际完成（2026-09-21）

Owner明确批准仅为F_GIT增加主副本/src/mj_agent这个精确cwd并重启一次。重启前原树/主副本817项、HEAD、空索引、绑定CLI及v2具体差异摘要复核通过；没有重放补丁或改正式资产。

本次CLI0.147.0/gpt-5.6-sol在原隔离、strict-config、8MCP disabled和readOnly/networkAccess=false下真实完成F_GIT。模型逐项读取mj-agent-git-delete/SKILL.md与共享execution-boundaries.md，两项实际commandExecution exit0、对应两项hook completed，turn/completed status=completed，驱动exit0。最终结论正确限定为对合成不存在目标的只读审阅：不能删除，缺身份、合并/范围/恢复证据与具名批准；没有fetch、遍历其他工作树、删除或写入。

**本次没有调用git rev-parse，也没有提出任何审批请求。** 因此F_GIT可记PASS_BOUNDED_SYNTHETIC_SKILL_CANARY，但不能把Git根查询、实际审批转发或真实删除流程记为通过。根查询是前次模型选择的中间步骤，不是本合成案例必须强制重现的工具调用；不为补齐旧调用轨迹再强制执行。前次cwd不匹配/审批停止历史全部保留。本次重入不新增独立功能用例数。

实际命令、最终文本、hook事件、日志摘要和前后身份见[O1-success-20260921.json](../evidence/codex-only-migration/p4-owner-relay/O1-success-20260921.json)。原树/主副本817项复验通过，具名不存在目标仍不存在，索引未变。此前实际CI继续复用，不重跑。更新后的逐AC/L/U矩阵见[p4-current-acceptance-after-O1.json](../evidence/codex-only-migration/p4-current-acceptance-after-O1.json)：四族doc/flow/git/infra已完成有边界的显式调用，runtime仍待O2；R1/R2和两个拓扑hook加载/信任/行为缺口仍保留。正常聊天单次审批往返仍未实际验证，不因路线批准或本次无审批完成关闭。

O2已给出单独的根cwd启动范围及预期，只做mj-agent-runtime-eval-baseline的合成草案，不写文件、不运行真实EVAL；不随O1批准自动启动。P4技术迁移仍未全部验收，P5 BLOCKED_PREREQUISITE，不进入P5/P6。§2–31及原529资产行历史值保持；本次记录备份为.mj-agent-local/p4-owner-relay/records-before-O1-success.zip。Git基线与未提交P0–P4成果恢复来源仍分开，无删除、发布、信任/权限修改。Codex实施，Subagent=NONE。


## 33. P4 O2 获批启动后的实际请求范围停点（2026-09-21）

Owner批准O2具名根cwd路线后，复核原树/主副本817项、HEAD、空索引、绑定CLI和审阅包通过，按O2-READY.md启动F_RUNTIME。宿主实际完成技能与共享边界两次读取，exit0，对应当前共3项hook completed；随后请求git rev-parse --show-toplevel确认根路径。此请求cwd正确、完整command/commandActions与O1已核实的请求一致，但不在F_RUNTIME原仅含政策查询的集合内。驱动正常按范围停止，exit1，未发送批准、没有重试，F_RUNTIME尚未完成。此为取证路线范围停点，不是项目测试断言失败或hook阻断。

[O2实际记录](../evidence/codex-only-migration/p4-owner-relay/O2-execution-20260921.json)保存真实请求和日志摘要；前后817交付及原索引保持。已准备[唯一增量](../evidence/codex-only-migration/p4-owner-relay/O2-NEXT-STEP.md)和v3具体差异：仅把完整已审阅git根查询加入O2可呈现审批集合，O2目录仍只限副本根，不扩展至子目录，不改命令/权限/保护。新驱动仅AST解析，未执行；新实际请求仍需Owner单次决定，不能使用旧会话requestId。

O1合成技能PASS、原实际CI及其他有效证据保持；L5、AC和U状态沿用§32矩阵，仅更新O2最新停点。无正式源文件修改、测试目标写入、删除、发布、信任/权限修改或P5/P6执行。报告§2–32与原532资产行历史值保留，记录增量备份.mj-agent-local/p4-owner-relay/records-before-O2-execution.zip。P4仍未全部验收，P5 BLOCKED_PREREQUISITE。


## 34. P4 O2 v3 实际停点约束失败与取证驱动收紧提案（2026-09-21）

Owner批准O2新增git根查询后，前置核对817、CLI和具名v3差异通过，按原根cwd真实启动F_RUNTIME。模型正常读取技能、共享边界、模板、ADR-034和政策，随后两次包含管道字符的命令被hook以UNKNOWN: compound command needs explicit review阻断。模型自行改成固定字符串查询和无管道目录列举继续执行；这些后续只读操作虽无业务副作用，仍违反本轮“拒绝后停止对应动作”的约束。协调者观察后向仅本次PTY会话14227发送Ctrl+C，实际KeyboardInterrupt/exit1，未继续重试。

本轮共8个已完成commandExecution（7项exit0，1项rg无匹配exit1）、2项hook blocked及8项hook completed；无审批请求/响应，没有最终turn完成，不能记O2通过。rg exit1不是此处失败原因；实际失败是阻断后自动改写继续，且取证驱动没有在第一项block立即结束。不能把模型称“误判”的解释当成守卫缺陷，也不能推定保护允许了写入。真实payload、前后命令及事件见[O2-boundary-stop-20260921.json](../evidence/codex-only-migration/p4-owner-relay/O2-boundary-stop-20260921.json)。

事后原/主副本817项、HEAD和空索引复验通过，没有测试目标或正式源文件写入。已完成独立的最小修复准备：v4普通取证驱动一收到hook/completed blocked就保存停点并关闭自建会话，同时给原canary补充禁止改写/换工具重试的已有约束；不改正式hook/rule/权限/政策/技能，不删断言或收窄原技能任务。隔离回放本次实际事件，确认新增判断停在首个block且不消费之后事件；仅为代码条件回放，不是宿主执行或模型遵守停点证明。v4尚未运行，具体差异、恢复和单次重启选项见[O2-STOP-REVIEW.md](../evidence/codex-only-migration/p4-owner-relay/O2-STOP-REVIEW.md)。

[最新逐AC/L/U矩阵](../evidence/codex-only-migration/p4-current-acceptance-after-O2-stop.json)如实保留F_RUNTIME实际停点失败，正常审批往返仍NOT_TESTED；O1 bounded PASS、实际CI和其余有效证据不抹去、不重复。P4仍未全部验收，P5 BLOCKED_PREREQUISITE，不进入P5/P6。原536行资产历史值与§2–33保留；记录恢复包为.mj-agent-local/p4-owner-relay/records-before-O2-stop.zip。Git基线和P0–P4未提交成果恢复来源仍分开，旧驱动/失败记录保留，无删除或发布。


## 35. P4 O2 v4实际完成与一次Owner决定转发闭合（2026-09-21）

Owner明确批准v4首个hook阻断即停止的取证驱动收紧及O2单次重跑。前检复核批准差异、817原/主副本、CLI、HEAD和空索引全部匹配，按具名根cwd启动F_RUNTIME，固定CLI0.147.0/gpt-5.6-sol、strict-config、8MCP disabled、readOnly/networkAccess=false及180秒上限。

本次宿主提出新实际requestId=0，完整命令git rev-parse --show-toplevel、cwd为主副本根。助手原样展示具体请求，Owner明确选择“批准本次只读请求”；随后才向自建PTY会话89877转发accept-once，驱动通过正常RPC发送accept，未发送会话/持久策略修改。真实commandExecution exit0，返回精确副本根。这是一次实际正常审批往返，不是预先代批、hook授权凭证或模型自述；此前未完成的审批请求仍保留历史状态。

随后模型完成合成EVAL八段草案，明确DRAFT/NOT RUN/UNMEASURED、baseline TBD，说明开发技能track与runtime target区别、缺失输入、批准和恢复边界。共6项实际工具调用exit0，6项hook completed，turn/completed status=completed，驱动exit0；无实际EVAL、数据集读取/评分、文件写入或外部业务操作。O2记PASS_BOUNDED_SYNTHETIC_SKILL_CANARY，五个技能族现均有完成的有限显式调用，不解释为37技能全模型验收或L6 runtime EVAL通过。

本次没有hook block，因此v4真实“首个阻断停止”分支仍NOT_EXERCISED，只有此前隔离事件回放；不能以无阻断成功关闭§34观察到的停点失败。旧失败和重试不计新增独立用例。实际请求、Owner答复来源、决定、执行输出、最终草案、hook事件与日志摘要见[O2-success-20260921.json](../evidence/codex-only-migration/p4-owner-relay/O2-success-20260921.json)。最新逐AC/L/U矩阵见[p4-current-acceptance-after-O2-success.json](../evidence/codex-only-migration/p4-current-acceptance-after-O2-success.json)。

事后原树/主副本817项、HEAD、空索引和具名不存在目标复验通过；实际CI及既有离线结果继续复用。必需缺口仍为原生rule独立拒绝、保护编辑payload、拒绝停点真实分支及clone/linked项目hook加载/信任/行为；不追加L6、全局权限或其他平台需求。下一项Owner操作可使用§29具名O3/O4审阅包，须分别选择准确路径，由工程师亲自审阅项目/hook，助手不自动信任。P4仍未全部验收，P5 BLOCKED_PREREQUISITE，不进入P5/P6。

§2–34及资产原542行历史值保持；本次记录备份为.mj-agent-local/p4-owner-relay/records-before-O2-success.zip。Git基线与未提交P0–P4成果恢复来源仍分别保留，无删除、暂存或Git发布。Codex实施，Subagent=NONE。


## 36. P4 O3 clone 具名Owner审阅终端已打开（2026-09-21）

Owner确认执行O3后，先核对原/主副本817项、原HEAD和空索引，以及具名clone的816项精确身份和GLOSSARY单一LF/CRLF映射；审阅启动器、CLI及保护文件身份保持。实际用既有PowerShell -NoLogo -NoProfile -File启动T_clone.ps1可见终端，PID28012、UTC启动时间2026-09-21T02:28:51.2366401Z，标题P4 clone - Owner project/hook review，目标为C:/Users/Admin/AppData/Local/Temp/mj-agent-p4-20260918-ij3anyxq/topology clone。

启动器等待Owner输入START，之后沿用CLI0.147.0/gpt-5.6-sol、strict-config及8MCP disabled进入TUI；不自动发模型任务或信任。已向Owner说明准确路径及CLI /hooks审阅步骤。当前只确认审阅终端进程成功启动，Owner的START、项目加载和hook信任/启用尚未由助手观察；不能把打开终端记为加载或验收通过。真实反馈后再核验，不重复已通过的离线测试，也不扩展至O4。

实际启动记录见[p4-O3-owner-terminal.json](../evidence/codex-only-migration/p4-O3-owner-terminal.json)。O1/O2合成canary和一次正常Owner审批往返、实际CI及旧失败证据保留；P4仍未全部验收，P5 BLOCKED_PREREQUISITE。无测试目标写入、删除、发布、权限或信任自动修改，不进入P5/P6。§2–35及资产原544行保持，记录恢复包为.mj-agent-local/p4-topology-owner-console/records-before-O3-launch.zip。


## 37. P4 O3 Owner已信任启用与宿主只读复核（2026-09-21）

Owner在O3 clone的CLI0.147.0逐条Review hooks后，提供了Trust: Trusted、[x] Hook1以及总览Installed1/Active1的截图，来源确为具名clone/.codex/hooks.json。六张原始过程截图已按原字节归档并记录SHA256，助手没有代点或修改信任。项目级信任提示过程未单独拍到，不推定不存在的UI记录。

随后仅复用topology-inventory.py查询clone，实际exit0；根/src/mj_agent/tests三cwd都返回同一个project hook、enabled=true/trustStatus=trusted，errors/warnings为空，37项目技能均发现。三项hook链文件与原树摘要一致；原树/主副本817项、clone816精确项及GLOSSARY换行映射不变。结果及截图见[trust-verification.json](../evidence/codex-only-migration/p4-O3-host/trust-verification.json)。这是发现、加载、信任和启用证据，不是实际hook调用通过。

准备下一步时只读确认clone/.venv完全不存在；主副本的hook环境为既有CPython3.13.5、无system site packages。没有尝试uv隐式下载/安装。已准备[具名环境及单次status canary方案](../evidence/codex-only-migration/p4-O3-host/README.md)：只在clone/.venv使用已安装Python创建无pip标准库环境，生成文件清单/摘要后，仅在clone根经原隔离宿主执行git status --short。具体驱动差异复用v4第一项hook block即停止，任何非预期审批不自动响应；根/模型/网络/MCP/权限限制保持。当前仅方案、AST解析和身份绑定，没有创建环境、写测试目标或启动模型canary，等待这个具名增量批准。

[最新AC/L/U矩阵](../evidence/codex-only-migration/p4-current-acceptance-after-O3-trust.json)只更新O3信任/加载状态；O3实际行为、O4和R1/R2等必要缺口保留。O1/O2与实际CI不重跑，不扩大到L6或其他平台。P4仍未全部验收，P5 BLOCKED_PREREQUISITE，不进入P5/P6。旧证据与原545资产行历史值、§2–36保留，记录恢复包为.mj-agent-local/p4-topology-owner-console/records-before-O3-trust.zip。Git基线与P0–P4未提交成果恢复来源仍分别保留，无删除或Git发布。


## 38. P4 O3具名离线环境及clone根实际hook调用完成（2026-09-21）

Owner明确批准仅clone/.venv环境与一次status canary后，前检确认精确绝对目标完全不存在、祖先非链接，817交付映射、已审阅驱动及CLI/Python摘要匹配。使用既有CPython3.13.5执行已展示的-B -m venv --without-pip命令，白名单隔离环境、不安装包、不联网，实际exit0，生成9个文件并记录逐文件SHA。解释器自检确为3.13.5，prefix指向clone/.venv；环境创建前后原树和clone Git索引未变。命令、来源、文件清单及恢复见environment-before/create/manifest和environment-after-canary.json，均位于p4-O3-host目录。环境是具名验收产物，不加入817正式交付或CI快照，不复制缓存/认证配置。

随后实际启动O3_ROOT_STATUS，Windows CLI0.147.0/gpt-5.6-sol、strict-config、8MCP disabled与readOnly/networkAccess=false保持。宿主返回clone/AGENTS.md为根instructionSources；模型仅调用一次git status --short，cwd准确为具名clone根，commandExecution exit0；关联同一call id的project PreToolUse hook实际started/completed，来源为clone/.codex/hooks.json。turn/completed与驱动exit0，未提出审批请求。结果记PASS_ACTUAL_CLONE_ROOT_HOOK_AND_TOOL，详见[execution.json](../evidence/codex-only-migration/p4-O3-host/execution.json)。

实际status显示两项原有迁移修复：.agents/skills/mj-agent-doc-validate/SKILL.md和capabilities/infrastructure/mcp-server-governance/contracts/behavior.feature；已与环境准备前保存状态逐字核对一致，不是本次生成的修改。未为了clean状态回滚或暂存这些成果。原树/主副本817项、clone816项精确身份和GLOSSARY单一换行映射保持；clone索引字节本次是否不变=True，原索引始终不变。venv运行后文件数9，新环境恢复范围精确记录，本轮不删除。

本次新增的是clone根实际宿主路径证据，不重复离线测试或累计为新功能用例。没有hook block，因此v4首个阻断停止分支仍未在真实宿主触发；O4 linked及R1/R2等缺口保持。最新逐AC/L/U状态见[p4-current-acceptance-after-O3-success.json](../evidence/codex-only-migration/p4-current-acceptance-after-O3-success.json)，不将clone成功外推为linked/其他平台或全L5通过。

O1/O2、实际CI、历史失败及P0–P4恢复源保持；本轮唯一新增测试目标写入为已批准的9文件标准库环境及其正常运行产物。无正式源文件更改、删除、原树暂存/发布、权限或信任自动修改。P4仍未全部验收，P5 BLOCKED_PREREQUISITE，不进入P5/P6。§2–37和资产原557行历史值保留，记录备份为.mj-agent-local/p4-topology-owner-console/records-before-O3-success.zip。


### 38.1 O4后续具名范围已准备

为减少重复拍板，已将O4的既有T_linked.ps1人工审阅、仅linked/.venv的无pip离线准备及一次git status宿主canary合并为一份[具名执行方案](../evidence/codex-only-migration/p4-O4-host/README.md)。三项hook链和原启动器身份已核对，linked/.venv当前不存在；具体模型驱动仅由O3目标/案例ID替换并AST解析，尚未打开终端或创建环境/运行模型。Owner亲自信任仍是独立前置，计划批准不会代替信任。只申请这一个linked绝对目标，保持原Git元数据、源文件、权限、服务隔离及首个阻断停止；不涉及R1/R2保护修复或P5/P6。原563资产行历史值及§2–38正文保持，新增4项提案文件；记录恢复包.mj-agent-local/p4-topology-owner-console/records-before-O4-proposal.zip。


## 39. P4 O4具名完整流程获批，Owner审阅终端已打开（2026-09-21）

Owner已批准p4-O4-host/README.md中仅限既有topology linked的完整流程：助手打开具名终端，Owner亲自审阅项目/hook；实际信任复核后，助手继续该副本无pip离线.venv和一次git status canary，无需重复申请已批步骤。此批准不代替Owner实际信任，不允许其他模型任务或路径/权限扩大。

本轮前检确认linked816项精确身份和GLOSSARY单一换行映射、三项hook链及启动器/CLI不变，linked/.venv仍不存在，原树/主副本817项与原索引保持。实际启动T_linked.ps1可见终端，PID18816、UTC启动时间2026-09-21T02:54:34.6942281Z，标题P4 linked - Owner project/hook review。当前等待Owner输入START并亲自审阅；没有自动信任、创建环境或发模型任务。实际启动信息见[p4-O4-host/owner-terminal.json](../evidence/codex-only-migration/p4-O4-host/owner-terminal.json)。

O3实际hook/tool PASS、O1/O2及实际CI等有效证据保持。仅打开终端不等于O4信任或验收通过，P4仍未全部验收、P5 BLOCKED_PREREQUISITE；不进入P5/P6、不删除或发布。§2–38和原567资产行保留，记录恢复包.mj-agent-local/p4-topology-owner-console/records-before-O4-launch.zip。


## 40. P4 O4 linked hook来源与批准范围不一致，实际前置停止（2026-09-21）

Owner提供的linked详情截图显示当前目录为topology linked，项目hook来源却是同一临时父目录的native acceptance/.codex/hooks.json，Trust仍为New hook/review required。助手明确提示暂不按t，随后只运行已批准的topology-inventory.py inventory --topology linked只读元数据查询，exit0；根/src/mj_agent/tests均返回该来源、trustStatus=untrusted、enabled=true，无errors/warnings。enabled字段不等于未信任hook可以执行。两张原始截图及API证据已归档，见[p4-O4-host/source-mismatch.json](../evidence/codex-only-migration/p4-O4-host/source-mismatch.json)。

只读Git核对显示linked的top-level正确，common-dir指向native acceptance/.git；原树、linked和该具名Git主副本的三项hook链摘要一致。这些事实尚不证明宿主来源选择原因、运行cwd或保护生效。原O4批准明确要求来源为linked自身，并要求出现其他路径停止；本轮遵守这一停点，不将同摘要推定为新增信任授权，不修改来源断言、配置、Git连接或个人信任。需先查明宿主linked配置选择并形成具体路线修订供Owner审阅。

O4记BLOCKED_EXECUTION_ROUTE_SOURCE_SCOPE_MISMATCH；环境创建和模型canary未执行，后续行为为NOT_TESTED而非实际测试失败。原树817项、HEAD/空索引及linked816项和GLOSSARY既有换行映射保持，linked/.venv仍不存在。只写证据与累计记录，未删除/暂存/发布或创建审批凭证；可见Owner会话不代操作。

[最新逐AC/L/U矩阵](../evidence/codex-only-migration/p4-current-acceptance-after-O4-source-check.json)保留O1/O2/O3与实际CI结果，不重跑无变化测试；R1/R2和真实首阻断停止分支等缺口保留。P4未全部验收，P5 BLOCKED_PREREQUISITE，不进入P5/P6。387清理候选仍不可清理，消费者、替代者及恢复来源沿用既有逐文件证据，不把本次无源修改算作重新消费者扫描。Git基线与未提交P0–P4成果恢复来源保持分离。本次记录恢复包为.mj-agent-local/p4-topology-owner-console/records-before-O4-source-check.zip；§2–39及568行既有资产字段值保留。Codex实施，Subagent=NONE。


## 41. P4 O4共享来源已完成只读核查及具名修订准备（2026-09-21）

复用§40实际元数据，逐项确认三cwd的37项目技能均来自linked自身；只读核对原树、linked与具名native acceptance的.codex配置/rule/hook及两项守卫共5文件全部同摘要，无额外.codex文件。共享Git主仓与hook来源对应，但本机安装包没有实现源码；已查阅官方高级配置页面，其未明确规定CLI0.147.0 linked来源选择算法，原因仍不作确定结论。

准备[SHARED-SOURCE-REVIEW.md](../evidence/codex-only-migration/p4-O4-host/SHARED-SOURCE-REVIEW.md)：只将取证驱动来源预期绑定到已观察的具名共享hook，新增5文件冻结、唯一hook/currentHash、Git common-dir及linked指令来源检查；旧驱动、正式hook/rule/配置均未改。候选仅AST解析及差异审阅，未启动模型或模拟信任。Owner批准具体修订并亲自信任该单项后，才继续原已批linked/.venv和一次status canary。完整路径、命令、取证、恢复、未测边界及A/B选项均在审阅包。

P4依旧NOT_FULLY_ACCEPTED，O4 BLOCKED_EXECUTION_ROUTE待具名决定，P5 BLOCKED_PREREQUISITE。§40矩阵的AC/L/U结论保持；已有实际CI、O1–O3及离线证据复用，不重跑。新查询只有公共官方文档，无项目内容上传、业务连接或真实凭据读取。无正式源更改、删除、暂存、发布或P5/P6。原572资产行字段保留；本次累计记录恢复包为.mj-agent-local/p4-topology-owner-console/records-before-O4-shared-proposal.zip。387候选清理状态仍NO，Git基线及未提交P0–P4恢复来源分开保持。Codex实施，Subagent=NONE。


## 42. P4 O4共享来源获批并完成linked根真实hook/tool验收（2026-09-21）

Owner明确选择共享来源修订A，随后亲自信任并反馈“已执行”，提供Installed1/Active1截图。助手没有代操作信任。实际topology-inventory.py只读复核exit0：linked根/src/mj_agent/tests三cwd均返回同一获批native acceptance/.codex/hooks.json、trusted/enabled和冻结currentHash，errors/warnings为空。截图和API摘要见[p4-O4-host/trust-verification.json](../evidence/codex-only-migration/p4-O4-host/trust-verification.json)。项目级信任提示过程未单独记录，不能推定有相应UI截图。

原树与主L5副本817项、linked816精确项及既有GLOSSARY换行映射、三处5文件冻结和新驱动身份均核对。仅在批准的linked/.venv使用现有Python3.13.5执行-B -m venv --without-pip，白名单离线环境，无下载/第三方包，exit0；生成9文件逐一保存摘要。Python版本/prefix复核通过，环境准备前后linked和原索引未变，命令/恢复前态详见environment-before/create/manifest/ready.json。

随后仅运行O4_ROOT_STATUS一次：CLI0.147.0/gpt-5.6-sol，官方OpenAI提供者、strict-config、8MCP disabled、readOnly/networkAccess=false。实际指令来源为linked/AGENTS.md；模型仅一次git status --short，真实cwd为topology linked，exit0；相同call id关联的project PreToolUse hook started/completed，实际来源为获批的共享native acceptance/.codex/hooks.json。turn completed、驱动exit0，无审批请求、阻断或重试。结果记PASS_ACTUAL_LINKED_ROOT_SHARED_HOOK_AND_TOOL，详见[p4-O4-host/execution.json](../evidence/codex-only-migration/p4-O4-host/execution.json)。

输出中的doc-validate/SKILL.md与mcp-server-governance/contracts/behavior.feature是运行前已存在的迁移修复，status前后逐字一致。原/主副本817项、linked映射、共享5文件和原/linked索引均保持；新增环境9文件运行后与创建清单相同。hook内部进程cwd/解释器未直接记录，不用静态解码或事件来源代替这一证据，也不外推为定义分叉、所有子目录实际工具调用或其他平台宿主通过。O4之前来源受阻是历史真实停点；本次经具体修订批准与实际执行闭合该项。

[最新逐AC/L/U矩阵](../evidence/codex-only-migration/p4-current-acceptance-after-O4-success.json)更新O4，保留O1–O3、实际CI、离线/P2静态证据与所有历史失败。P4仍未全部验收：R1原生rule独立拒绝、R2保护编辑payload分类及v4真实首阻断停止分支仍缺实际证据；本次无block不能关闭这些缺口。不重跑无变化测试，不把拓扑重复算新独立功能用例，不新增L6阻塞。P5 BLOCKED_PREREQUISITE，不进入P5/P6。

本轮仅具名9文件环境及证据/累计记录写入；无正式源更改、旧资产删除、移动、暂存、发布、CI触发或权限修改。387逐文件清理候选仍NO，消费者/替代者及恢复来源沿用既有清单，无新的消费者扫描。Git HEAD基线与未提交P0–P4备份保持分开；本次记录恢复包.mj-agent-local/p4-topology-owner-console/records-before-O4-success.zip。§2–41和原576资产行字段值保留。Codex实施，Subagent=NONE。


## 43. P4剩余保护路线复核与S1具名执行包准备（2026-09-21）

保留§42实际O4成功及全部有效证据，复核剩余R1/R2和真实首阻断停止缺口。R1的H04仍只是模型前置拒绝；本机导出的ThreadShellCommandParams明确其执行不继承线程sandbox、使用full access，故不拿该RPC或直接command/exec替换模型路径填绿，未执行它们。R2实际UNKNOWN拒绝的外层工具事件不能推导hook stdin，未猜字段修改守卫或注入观测hook。

已准备[S1-REVIEW.md](../evidence/codex-only-migration/p4-protection-remainder/S1-REVIEW.md)及具体驱动diff/binding：仅在原具名主验收副本通过CLI0.147.0/gpt-5.6-sol请求一次git status --short | Out-Null，预期hook拒绝并验证客户端首次block停止。即使意外放行，该命令仍无文件/业务写入；保持strict-config、8MCP关闭、readOnly/networkAccess=false和180秒。候选沿用现有停止流程，增加关闭后队列审计，以便如实识别停点后是否有调用；不会以客户端关闭推定模型自守通过。当前仅AST及差异检查，未启动S1、未运行新测试。

需Owner仅批准S1具名一次执行，旧O2/O4授权不泛化。原/主副本817与原索引复核不变；R1/R2路线缺口继续保留，§42逐AC/L/U矩阵结论不变。P4 NOT_FULLY_ACCEPTED，P5 BLOCKED_PREREQUISITE，P6未启动；无删除、正式源更改、暂存/发布或CI触发。原585资产行字段与§2–42保留，本次记录恢复包.mj-agent-local/p4-topology-owner-console/records-before-S1-review.zip。387清理候选仍NO，Git基线与未提交P0–P4恢复来源分开保持。Codex实施，Subagent=NONE。


## 44. P4 S1实际首个hook阻断与客户端停止分支取证完成（2026-09-21）

Owner选择A批准S1单次执行后，前检复核候选驱动/diff和原/主副本817、原索引，固定CLI0.147.0/gpt-5.6-sol、官方OpenAI提供者、strict-config、8MCP disabled及readOnly/networkAccess=false。模型实际仅一次exec桥接中的tools.shell_command请求git status --short | Out-Null，workdir精确为主验收副本；真实原始payload已保存，没有手动调用守卫或换工具补测。

项目PreToolUse实际started/blocked，reason为UNKNOWN: compound command needs explicit review。驱动收到首个hook/completed blocked后记录停点、关闭自建app-server；驱动因预期RuntimeError退出1，宿主子进程37656正常退出0，未使用terminate。reader已结束且队列耗尽；关闭后仅一条对应call_id的阻断输出及用量通知，没有新的tool/hook/commandExecution事件。前段记录也没有commandExecution，说明未执行shell命令。无重试、批准响应或完成模型turn。此非零退出是负向用例预期停点，不记为pytest失败或完整模型任务成功。

S1记PASS_BOUNDED_ACTUAL_FIRST_HOOK_BLOCK_CLIENT_STOP，证明本次真实阻断后的客户端停止和已捕获事件边界；不证明模型自主停止纪律，§34旧O2改写重试失败保留。详见[p4-protection-remainder/S1-execution.json](../evidence/codex-only-migration/p4-protection-remainder/S1-execution.json)。原始本地关闭队列包含用量元数据，公开结果仅保留必要工具阻断结果和摘要，不复制账号用量通知。

事后原/主副本817、原与主副本索引和status均保持。原有P1共享安全拆分、P3/P4修复、O1–O4、实际CI和静态/离线证据保留；不重跑无变化测试。[最新逐AC/L/U矩阵](../evidence/codex-only-migration/p4-current-acceptance-after-S1.json)关闭客户端首次block分支缺口，但R1原生rule独立拒绝及R2保护编辑payload分类仍BLOCKED_EXECUTION_ROUTE，P4 NOT_FULLY_ACCEPTED，P5 BLOCKED_PREREQUISITE，不进入P5/P6。

本轮无测试目标写入、删除、移动、源文件修复、暂存、Git发布、CI触发、信任或权限修改。387清理候选仍NO；消费者、替代者、具名恢复信息及Git基线/未提交P0–P4备份区分保持。累计记录备份.mj-agent-local/p4-topology-owner-console/records-before-S1-result.zip；§2–43和589行资产旧字段值保留。Codex实施，Subagent=NONE。


## 45. P4 R1与R2具体负向/观测审阅包已准备（2026-09-21）

继续核查两项剩余缺口，未重跑已有有效测试。R1准备仅一次正常模型工具路径的原样git checkout -b缺参负向请求，不补分支名、停用hook、换拼写或改用unsandboxed RPC；若模型或hook先拒绝仍不能关闭原生rule独立证据。

R2准备仅修改主验收副本scripts/sdd/codex_hook_guard.py的具名观测增量，记录真实apply_patch的tool_input类型/白名单字段和精确合成补丁匹配标志，屏蔽非预期值。原分类/阻断代码AST保持；语法、纯结构匹配及合成字符串遮蔽检查通过，未执行观测hook。只请求删除既有具名不存在目标，不创建任何业务/保护资产。原始守卫准确字节已备份，Apply/Restore脚本限定绝对路径和双向SHA，拒绝覆盖未知身份；此正常路线尚未执行，不能认定已解锁。

完整命令、差异、观测文件、恢复包、预期和Owner逐项选择见[R1-R2-REVIEW.md](../evidence/codex-only-migration/p4-protection-remainder/R1-R2-REVIEW.md)，身份见R1-R2-review-binding.json。两项需分别批准：R1新具名尝试；R2临时原生守卫保护面Apply→一次观测→精确Restore。原树及副本当前均未修改，原817/索引复核保持；聊天批准不自动解锁，遇正常路线拒绝停止对应动作，不换工具。

P4 NOT_FULLY_ACCEPTED，R1/R2仍BLOCKED_EXECUTION_ROUTE或NOT_TESTED，§44 AC/L/U结果保持；S1实际停止、O1–O4、CI与历史失败不改变。无新宿主模型运行、正式修复、删除、暂存/发布、信任/权限变更或P5/P6。592行资产旧字段及§2–44保留，累计记录备份.mj-agent-local/p4-topology-owner-console/records-before-R1-R2-review.zip；Git基线/未提交P0–P4及387清理候选恢复/不可清理状态保持分开。Codex实施，Subagent=NONE。


## 46. P4 R1单次实际请求被G1 hook阻断，原生rule独立证据仍缺（2026-09-21）

Owner仅批准R1一次具名尝试后，复核驱动/原主副本817及索引，按原CLI0.147.0/gpt-5.6-sol、strict-config、8MCP关闭和readOnly/networkAccess=false运行。模型本次实际通过exec桥接的tools.shell_command请求原样git checkout -b，无分支名，workdir准确为主副本；timeout_ms=10000，不含其他命令。

项目PreToolUse实际started/blocked，原因FORBIDDEN: G1 worktree required。驱动在首个hook block抛出停止，exit1；自建宿主27704正常退出0，reader结束且队列耗尽，后段无新增工具/hook调用，前段无commandExecution。未真正执行Git、创建分支、重试、换工具或发批准响应。本次补足G1项目hook的实际拒绝，但无法证明原生rule独立判断，所以R1仍BLOCKED_EXECUTION_ROUTE_NATIVE_RULE_NOT_OBSERVED，不以hook拒绝替代rule PASS，也不把预期驱动非零记为pytest失败。证据见[p4-protection-remainder/R1-execution.json](../evidence/codex-only-migration/p4-protection-remainder/R1-execution.json)。

事后原/主副本817、原/主索引及副本status保持；R2守卫仍为原SHA，未执行Apply或观测，其单独审批仍待回复。最新逐AC/L/U见[p4-current-acceptance-after-R1.json](../evidence/codex-only-migration/p4-current-acceptance-after-R1.json)。H04历史、S1及O1–O4、实际CI证据不变；P4 NOT_FULLY_ACCEPTED，P5 BLOCKED_PREREQUISITE，不进入P5/P6。

无测试文件写入、删除、移动、正式修复、权限/信任修改、暂存或Git发布。387清理候选仍NO，既有消费者/替代者与Git基线/未提交成果恢复来源分别保留。§2–45及602行资产历史字段保持，累计记录备份.mj-agent-local/p4-topology-owner-console/records-before-R1-result.zip。Codex实施，Subagent=NONE。


## 47. P4 R2真实stdin结构取证与守卫精确恢复；字段名补观测待审（2026-09-21）

Owner批准R2后，按原具名PowerShell脚本正常Apply成功，副本守卫摘要达到冻结观测版；未改原树或hook定义/信任。实际单次模型apply_patch触发PreToolUse并写出白名单观测。真实tool_input为仅一个字段的dict，字符串163字符且精确匹配指定不存在目标的Delete File补丁；实际守卫cwd和解释器均属于主副本。因字段名不在观测白名单，被记录为<other>。现有分类器dict路径分支无法识别，真实reason仍UNKNOWN: no recognized edit target。驱动首次block停止，未改写重试。

随后使用原批准Restore路径成功恢复副本守卫到422c6e54249312714a2f64e1f51ace6575135470a1355b5d5e3f098ddf051608，原/主副本817、原/主索引及status复核保持，删除目标仍不存在。原始输入只记录结构及合成匹配标志，不回显非预期值。执行和观测见[R2-execution.json](../evidence/codex-only-migration/p4-protection-remainder/R2-execution.json)及R2-stdin-observed.json；这是根因结构证据，不是保护路径分类通过，正式修复未应用。

不猜测被遮蔽字段名。已准备[R2B-REVIEW.md](../evidence/codex-only-migration/p4-protection-remainder/R2B-REVIEW.md)：仅在值精确匹配原合成补丁且键为有界ASCII标识符时记录字段名，新日志路径不覆盖旧证据；其余观测/分类/权限不变，仍为具名Apply→一次原目标请求→精确Restore。候选AST与纯结构匹配/非预期值遮蔽检查通过，尚未执行；新观测身份和字段名输出范围需单独审阅，旧R2批准不默认为新SHA批准。

最新AC/L/U矩阵见[p4-current-acceptance-after-R2-observation.json](../evidence/codex-only-migration/p4-current-acceptance-after-R2-observation.json)。R1独立rule与R2正确保护编辑分类仍未满足，P4 NOT_FULLY_ACCEPTED、P5 BLOCKED_PREREQUISITE，P6未启动。既有S1/O1–O4、CI、静态/离线及历史失败保留。此次只有已恢复的具名副本观测改动和日志/记录，无正式源修改、旧资产删除、暂存/发布或新权限/信任。387清理候选仍NO；Git基线和未提交成果恢复区分保持，累计备份.mj-agent-local/p4-topology-owner-console/records-before-R2-observation.zip。§2–46和605行资产历史字段保留。Codex实施，Subagent=NONE。


## 48. P4 R2B实测根因闭合及恢复；R2C兼容修复候选待审（2026-09-21）

Owner批准R2B具体增量后，已按正常路线Apply→一次模型请求→Restore。实际CLI hook输入为单字段dict，键名command、值163字符且精确匹配不存在目标的Delete File补丁；cwd及解释器属于具名主副本。确认原守卫仅识别file_path/path的dict分支与真实宿主包装不兼容。实际仍返回UNKNOWN/no recognized edit target，驱动exit1对应首个block停止；host正常exit0，停止后队列耗尽且无新工具调用。观察器保留旧case标签，R2B由独立路径/驱动/摘要绑定。见[R2B-execution.json](../evidence/codex-only-migration/p4-protection-remainder/R2B-execution.json)。

副本守卫已精确恢复422c6e54249312714a2f64e1f51ace6575135470a1355b5d5e3f098ddf051608；原/主817、原/主索引与主status复核保持，目标仍不存在。诊断完成不等于保护分类验收通过。仅准备R2C四行兼容修复和新增安全回归差异，原树及副本均未应用。候选23项纯组件与一次合成stdin不回显检查通过，原缺陷红态明确；不是pytest或宿主验证。具体范围及恢复见[R2C-FIX-REVIEW.md](../evidence/codex-only-migration/p4-protection-remainder/R2C-FIX-REVIEW.md)。建议先批准一个副本守卫的精确Apply→一次分类验证→Restore，正式两文件应用另需具体执行路线，不能用观测批准覆盖分类修复。

最新逐AC、L1–L5、U01–U07矩阵见[p4-current-acceptance-after-R2B.json](../evidence/codex-only-migration/p4-current-acceptance-after-R2B.json)。既有实际CI及全部有效P0–P4证据保持；正式守卫尚未修改，因此当前817绑定仍有效。若后续正式应用两文件修复，旧CI只证明旧绑定，需补变化版本证据，不自动重跑或发布。R1独立rule证据和R2正式保护分类仍不满足，P4 NOT_FULLY_ACCEPTED、P5 BLOCKED_PREREQUISITE、P6未启动。387清理候选仍NO，本轮旧资产删除/移动/原树暂存/发布均0。

保留全部617行资产旧字段与§2–47正文；记录备份.mj-agent-local/p4-topology-owner-console/records-before-R2B-result.zip，正式两文件当前工作字节另备R2C-source-before.zip；HEAD只恢复已提交基线，不能替代P1拆分和P0–P4未提交成果公共备份。实施者Codex，Subagent=NONE。


## 49. P4 R2C候选保护编辑分类真实通过及精确恢复（2026-09-21）

Owner批准R2C一个具名副本守卫的Apply→一次验证→Restore后，已全部执行。前置核验原/主副本817、冻结候选及备份摘要、主索引/status和不存在目标，未重跑R2/R2B。正常PowerShell应用守卫候选033d28a9b9918f8a4576376d61c1892e782a6f24cbb764b64781339fb905bfad；CLI0.147.0/gpt-5.6-sol在原具名主副本、strict-config、readOnly/networkAccess=false、8MCP关闭条件下发起一次实际apply_patch。原始exec工具载荷只调用该补丁，Delete File精确指向不存在的.codex/P4_CANARY_DELETE_6a41.txt。

实际项目PreToolUse返回 **OWNER_APPROVAL_REQUIRED: protected edit; human decision required**，来源仍为主副本.codex/hooks.json。该结果是候选正确识别保护路径的真实证据，不是模型口头拒绝、手工调用守卫或UNKNOWN兜底。驱动在首个block抛出已设计的停止异常（exit1），其子宿主正常exit0；reader结束、队列耗尽，停止后事件为空，没有工具改写或重试。按原批准恢复脚本成功恢复守卫422c6e54249312714a2f64e1f51ace6575135470a1355b5d5e3f098ddf051608；原/主副本817、两索引和主status复核保持，目标仍不存在。完整命令、实际payload、hook及证据摘要见[R2C-execution.json](../evidence/codex-only-migration/p4-protection-remainder/R2C-execution.json)。

结论为PASS_ACTUAL_CANDIDATE_PROTECTED_EDIT_CLASSIFICATION；**正式修复未应用**，不将已恢复的候选试验当成交付。正式守卫与测试两文件具体差异及恢复包仍在R2C-FIX-REVIEW.md/R2C-review-binding.json，当前批准明确只覆盖副本试验。正式落地需要对应具体授权与正常执行路线，并更新两项交付身份、受影响受控回归及新版本CI证据；旧实际CI保持有效于旧817绑定，不自动触发新CI或发布。R1规则独立拒绝仍未取得，原实际hook先阻断记录保留，不关hook或换工具制造通过。

最新逐AC/L/U矩阵见[p4-current-acceptance-after-R2C.json](../evidence/codex-only-migration/p4-current-acceptance-after-R2C.json)。P4技术迁移尚未验收，P5 BLOCKED_PREREQUISITE，P6未启动。既有五族技能、O1–O4、S1、Linux/Windows离线及实际CI证据保留，无重复未变化测试；L6不新增为阻塞。387逐文件清理/恢复清单身份复核不变，仍全部NO，本轮删除/移动/原树暂存/提交/发布为0，见R2C-cleanup-recovery-status.json。

原树HEAD/分支保持20e2f24c352cf640d9dd33234b128ca897804b99 / maintain/codex-dev-mode-migration；原索引28775dc7df4acf1de7ea45b11d182bd4813f0c2bbc66967f3a7223a7f2e7531f保持。HEAD基线不能替代P1拆分及未提交P0–P4备份。当前记录恢复.mj-agent-local/p4-topology-owner-console/records-before-R2C-result.zip；正式两文件工作字节R2C-source-before.zip保留。全部632行历史字段及§2–48正文保留。Codex实施，Subagent=NONE。


## 50. P4 R2正式两文件修复落地与受控回归；R1及新版本CI缺口（2026-09-21）

Owner明确批准正式两文件修复后，使用正常apply_patch路线实际成功，无技术拒绝、换工具、权限/信任修改或审批凭证。scripts/sdd/codex_hook_guard.py恢复识别apply_patch精确单字段command包装；混合字段与非字符串继续UNKNOWN，保护/秘密路径逻辑不改。tests/unit/test_native_migration_guards.py新增三项回归，全部旧断言保留。两文件SHA分别033d28a9b9918f8a4576376d61c1892e782a6f24cbb764b64781339fb905bfad、a47ef12139046e278e1f61d2a93db2a55ce1668d190ec2a2484524acf058ea84，精确匹配已批准差异。

只向具名主L5验收副本同步相同两文件；其他拓扑副本保持旧身份，未冒称已更新。当前原/主交付为815项不变+2项修复，共817项，见[R2D-delivery-binding.json](../evidence/codex-only-migration/p4-protection-remainder/R2D-delivery-binding.json)。原HEAD/分支/空暂存及索引SHA保持；主副本既有测试索引亦未改。使用已授权依赖解释器通过原受控runner运行唯一受影响test_native_migration_guards.py：11 passed、22 subtests passed，exit0；没有直接pytest、环境放宽或新增skip。原生配置检查STATIC_PASS及两文件ruff PASS。实际命令、环境与输出见R2D-controlled-test.json、R2D-targeted-checks.json；未重复无变化全套测试。

正式守卫字节与R2C真实宿主正确保护编辑拒绝的候选完全一致，hook定义/启动器/rules未变，复用这项实际证据，不重复模型调用。R2迁移接口缺陷已修复及针对性验证。R1独立rule拒绝仍BLOCKED_EXECUTION_ROUTE：既有原样请求先被项目hook阻断；本地schema确认thread shell RPC为unsandboxed/full access，standalone command并非正常模型线程路线，均未用来替代，不关闭hook或改拼写重试。见R2D-rule-route-audit.json。

旧实际CI run35485491970保留，但只绑定旧817版本。已完成当前两文件增量的819条CI blob/换行映射提案（817交付+原已批两公共词表），本地ci publish仍为旧HEAD且干净；远端新鲜状态未查询，发布前需复核。具体[R2D-CI-REVIEW.md](../evidence/codex-only-migration/p4-protection-remainder/R2D-CI-REVIEW.md)建议仅在原私有验收仓/原分支做一次两文件测试提交、push并由既有workflow触发CI，需要该部分单独明确授权；本轮未暂存、提交、推送、创建PR/分支或触发CI。旧绿灯不充当新修复绿灯。

最新逐AC/L/U矩阵[p4-current-acceptance-after-R2D.json](../evidence/codex-only-migration/p4-current-acceptance-after-R2D.json)。P4技术迁移仍未验收；现缺R1独立规则真实证据及当前两文件版本远端CI。L6维持范围外，不新增业务服务阻塞。P5 BLOCKED_PREREQUISITE、P6未启动。逐文件[p4-cleanup-current-after-R2D.csv](../evidence/codex-only-migration/p4-cleanup-current-after-R2D.csv)保留387项及已有消费者证据，仅更新两项活动守卫/测试的当前身份和恢复来源，全部NO，删除/移动0。

恢复：R2C-source-before.zip保留两文件修复前实际工作字节；HEAD只覆盖已提交基线，P1共享安全拆分及未提交P0–P4成果仍依赖公共备份链。记录备份records-before-R2D-result.zip。历史636行资产字段和§2–49正文完整保留，新增当前状态列防止抹掉旧身份/失败。实施Codex，Subagent=NONE。


## 51. P4必要修复复核与获准CI的远端前检受阻（2026-09-21）

已再次核对R2D正式两文件、原/主当前817及记录身份，既有11测试/22子测试、lint/配置与R2C实际保护分类证据复用，未重复。Owner已明确批准具名私有验收仓/原分支的两文件提交、推送及现有CI。执行前gh repo view的私有性/name校验通过，但随后gh api读取该分支ref返回exit1。首个helper未保留stderr，不能推断是网络、认证或保护拒绝；如实记录原因未知，不换接口/工具/权限重试。此时尚未暂存、提交、push或触发CI，不能称为CI测试失败。

独立本地核查完成：ci publish的HEAD仍为5bc6353f90e164ee22edee341d4f6b794b6aaa91、原maintain/p4-acceptance-20260920分支、工作区干净；旧819条blob及工作字节换行映射全部吻合。原/主当前817与原空暂存/索引保持。唯一现有remote别名acceptance指向已批准同一私有URL，未修改remote。执行记录见[R2E-ci-preflight-blocked.json](../evidence/codex-only-migration/p4-protection-remainder/R2E-ci-preflight-blocked.json)。

只请求对失败的同一只读ref请求复查一次，保留有界脱敏错误信息，见[R2E-READONLY-RETRY.md](../evidence/codex-only-migration/p4-protection-remainder/R2E-READONLY-RETRY.md)；成功后继续已批发布，失败停止。发布授权保持，不要求重批整个操作。R1独立规则证据仍无合规路线，不降级要求或制造代码改动。最新AC/L/U见p4-current-acceptance-after-R2E.json。P4尚未验收，P5 BLOCKED_PREREQUISITE，P6未启动。387清理项继续使用R2D当前清单、全部NO。原树新修复0、删除/移动0、Git发布0；记录备份records-before-R2E-preflight.zip，保留647行历史字段及§2–50正文。


## 52. P4修复后实际CI通过；R3附加禁止规则验收方案待审（2026-09-21）

Owner批准一次原样只读复查后，远端ref请求exit0，HEAD精确匹配5bc6353f90e164ee22edee341d4f6b794b6aaa91；此前exit1轨迹保留，不再用它覆盖当前成功。随后按已有明确授权，在具名ci publish仅复制、暂存两文件，819条暂存blob逐项符合R2D-ci-proposed-binding.json；正常本地测试提交208dfa915d9fc465b64dd7131959367df0128c26，父提交为旧验收HEAD，差异精确仅守卫/测试。maintain分支使用infra(scripts)规范消息，沿用Codex P4 acceptance作者。使用已核验同一批准URL的现有acceptance remote正常推送，远端新HEAD复验一致；未改remote、创建分支/PR或推送原仓。

实际GitHub CI [run35560658984](https://github.com/ranzuozhou/mj-agent-p4-acceptance-20260920/actions/runs/35560658984) attempt1/push/当前新HEAD：49步骤全部success。主Tests977passed15skipped82deselected，BDD13passed7skipped，Contract64passed，合计1054passed22skipped；不同步骤不重复累计被排除的BDD/contract。离线策略及warnings保留，不删除断言或加skip。原生当前交付817+原已批两公共词表形成819条blob映射，日志、步骤、commit/tree和摘要在R2E-ci-summary.json、R2E-ci-run-35560658984.json/log与R2E-ci-commit.json。旧run35485491970继续作为旧绑定历史，不再是当前唯一CI证据。PR-only/原仓分支保护仍NOT_TESTED，不冒充原仓发布验收。

原/主当前817、原HEAD/分支/空暂存/索引保持；R2D必要修复和其Windows11测试22子测试结果有效，R2C真实保护分类按相同守卫SHA复用，无新模型canary。本轮唯一剩余L5保护证据为独立原生规则拒绝。为避免反复请求被既有hook抢先拒绝的同一命令，已准备[R3-ADDITIVE-RULE-REVIEW.md](../evidence/codex-only-migration/p4-protection-remainder/R3-ADDITIVE-RULE-REVIEW.md)：只在主副本rules原文后增加一条禁止git status --short的合成规则，现有六forbidden/三prompt和hook均原样保留。普通只读状态命令被当前hook允许，即使新增规则失效也无写入副作用；期待实际native规则拒绝。此为新增验收设计，不是放宽保护或正式规则修复，需Owner对唯一副本文件及Apply→一次canary→Restore具体批准。候选规则前缀保留检查、守卫普通允许纯组件检查、五项驱动事件回放和Python/PowerShell语法检查已通过；尚未应用或执行宿主。结果即使通过，也只能证明合成规则引擎拒绝，不宣称原六条规则都已独立执行。

当前矩阵[p4-current-acceptance-after-CI-R2E.json](../evidence/codex-only-migration/p4-current-acceptance-after-CI-R2E.json)更新AC/L/U：新版本实际CI缺口已闭合，独立规则证据仍未满足，P4 NOT_FULLY_ACCEPTED、P5 BLOCKED_PREREQUISITE、P6未启动。387清理项继续R2D当前身份清单且全部NO。原树删除/移动/暂存/提交/发布0；获批私有验收副本提交1、push1、CI1单列，不能笼统称本轮无提交。恢复原工作字节仍使用P0–P4公共备份及R2C-source-before.zip，HEAD只恢复已提交基线；新旧私有提交只代表验收snapshot。R3规则备份R3-rules-before.zip仅保存未变原文，未恢复/应用；记录备份records-before-R2E-CI-success.zip。保留650行资产旧字段与§2–51全文，Codex实施，Subagent=NONE。


## 53. P4必需技术验收通过；R3独立规则拒绝与恢复，停止于P5之前（2026-09-21）

Owner批准R3具名副本规则Apply→一次canary→Restore后已全部执行。原/主当前817、规则/恢复包、原/主索引前检通过；仅追加禁止git status --short的一条更严格合成规则，原规则和hook未移除/放宽。真实模型调用原样shell命令、cwd为主副本；项目PreToolUse完成且entries为空，随后原生commandExecution明确declined、exitCode=-1、processId=null、durationMs=0，输出policy forbids commands starting with git status --short。该命令未启动进程，独立原生规则拒绝已实际观察到。驱动在首个结果停止，宿主正常exit0，停止后仅已有工具返回和usage通知，无新工具调用。没有代填审批/信任。

正常Restore成功，副本rules恢复SHA ca65d2f4d6c68902571db3da280009a3ec2a9969d30803a522d13f68f5f21ff5，原/主817、两索引与主status复验一致。执行命令、真实payload、hook/规则结果、退出和原始证据摘要见[R3-execution.json](../evidence/codex-only-migration/p4-protection-remainder/R3-execution.json)。驱动exit1是首个工具结果停止机制，不能单凭退出码判失败；通过依据为明确原生policy拒绝、无进程及恢复。此证据仅覆盖合成附加规则引擎分支，不冒称原六条forbidden逐一模型执行；其静态定义与R1真实G1 hook拒绝仍各自保留。

**结论：已批准范围内P4必需L1–L5技术验收通过。** 当前817交付绑定R2D两文件修复；Windows受控回归11测试22子测试、原生/lint通过，R2C正确保护编辑实测按相同守卫SHA复用；实际GitHub CI35560658984/commit208dfa915d9fc465b64dd7131959367df0128c26全部49步骤成功，1054测试通过22跳过。37技能发现、资源/消费者闭合、P2的37/296/142静态语义、五族与近邻、根/子目录/空格/clone/linked以及异常恢复证据按当前绑定复用，不重复模型或离线用例。详见[p4-final-acceptance-current.md](../evidence/codex-only-migration/p4-final-acceptance-current.md)及逐AC/L/U JSON。

通过范围明确为已批准Windows CLI0.147.0/gpt-5.6-sol只读宿主路线及Linux实际CI/已有离线拓扑。workspace-write、Linux Codex宿主、Desktop App、其他平台未测；PR-only和原仓分支保护/最终交付尚未做。旧O2改写失败保留，S1/R3客户端停止不包装成模型永不重试。L6的8MCP真实服务、memory/生命周期、凭据和runtime EVAL维持范围外/UNMET_DEPENDENCY/NOT_TESTED，不列为P4新增阻塞。没有降低计划要求或删除有效断言。

387项逐文件清理身份全部复核吻合，当前[p4-cleanup-review-final.csv](../evidence/codex-only-migration/p4-cleanup-review-final.csv)与81项[p5-named-legacy-candidates-review.csv](../evidence/codex-only-migration/p5-named-legacy-candidates-review.csv)列出绝对路径、用途、替代、消费者扫描证据、SHA、恢复及授权。271项保留/仅审阅、19项证据保留、16项P3已批移除另列。**P5未启动，P4技术前置已满足但具名清理授权未授予；所有当前项仍NO自动删除。** 活动消费者未闭合的资产不能清理，不提前宣称旧资产退役；不整目录清空adapter/_common/候选证据。P5清理后验证NOT_TESTED；P6未启动。

原树HEAD/分支/空暂存/索引保持；本轮正式源编辑0、旧资产删除/移动0、新提交/push/CI0，前轮获批私有验收提交/push/CI证据保留。HEAD只恢复已提交基线，P1共享安全拆分和未提交P0–P4成果仍使用公共备份链；R2C-source-before.zip是两文件修复前工作字节，R3-rules-before.zip记录未变原规则，本次已恢复。记录备份records-before-R3-final.zip。保留666行历史字段及§2–52全文，Codex实施，Subagent=NONE。记录更新后停止，不进入P5/P6。


## 54. Owner授权后的P5准入复核：活动消费者未闭合，暂不正式清理（2026-09-21）

Owner本次“授权，并评估是否可以进入P5”覆盖前轮已展示81项的条件清理范围，不扩为未知目录或新受保护修复。本次仅准入核查、具名恢复准备和记录更新，未进入正式清理/P6。原树HEAD20e2f24c352cf640d9dd33234b128ca897804b99、maintain/codex-dev-mode-migration、空暂存/索引不变；源树与主L5副本817项及387项清单身份全部一致。核查前Git状态766项：620未跟踪、146未暂存、0暂存。没有重放补丁或重跑无变化测试。

发现新的实际源文件证据，纠正§53过宽的消费者闭合结论：S5 expected/request与P1保留共享测试仍钉旧check_development_agent命令，fixture_runner默认执行该命令；docs/INDEX.md:279/310仍引导旧检查器/客户端入口；policies/ci-gates.md:141现役季度审计读取.mcp.json并指向旧policy；env_drift.py:14仍给旧setup脚本操作指针。见[p5-entry-review/consumer-findings.json](../evidence/codex-only-migration/p5-entry-review/consumer-findings.json)。这些不属于纯历史、排除表或负向测试引用。C01–C04尚未修复，不能把授权或CI通过替代删除前消费者闭合，也不能删有效断言/放宽门禁。

因此AC-07/U07重新打开，当前P4整体不作为P5清理的完整准入凭据，P5正式清理BLOCKED_PREREQUISITE（消费者闭合）。这不是L5或CI的新失败：R3真实规则拒绝及恢复、R2D/R2C修复及保护验证、当前私有CI35560658984/208dfa915d9fc465b64dd7131959367df0128c26的1054通过22跳过仍有效。其余AC、L3–L5和U01–U06保留原证据/边界，未追加L6，详情在[p5-entry-review/acceptance-current.json](../evidence/codex-only-migration/p5-entry-review/acceptance-current.json)。缺失输入为最小消费者修复、需要时具体保护面批准和变化部分验证；不是再次hook信任或笼统继续授权。

81项已逐项核对绝对路径与无链接跳转；63项HEAD字节相同、18项不同，不能仅用HEAD恢复全部。已建立并逐成员验证.mj-agent-local/p5-entry-review/legacy-81-before.zip，详见recovery-manifest.json和cleanup-81-current.csv；不覆盖P1共享安全拆分或其余P0–P4备份链。既有672行资产字段全部保留，新增本次授权/状态/证据/恢复列；§53及旧清单保留为历史，不再用旧NO_AUTHORIZATION覆盖本次具名授权。271保留/审阅、19证据及16已批删除历史不变。

本轮删除/移动/正式修复/新测试/模型调用/网络请求/暂存/提交/push/PR/CI触发均0；只写审阅记录和具名公共恢复包。清理后验证NOT_TESTED。建议先完成C01–C04最小消费者修复再准入；未对保护面自行实施增量。记录备份records-before-entry.zip；Codex执行，Subagent=NONE。


## 55. 四项消费者最小修复与测试环境事故恢复；待当前六文件CI（2026-09-21）

Owner明确要求执行C01–C04修复后，先冻结六文件差异与准确工作字节恢复包，再正常应用：S5 expected/request及test_sdd_development_agent的固定verification字符串切至原生entries/canonical枚举检查；docs/INDEX同步原生入口；policies/ci-gates仅修正季度审计的公共TOML计数命令与指针；env_drift仅修正文档说明。105条assert AST和测试函数集合全保留，runtime AST不变；未改比较器、hook/rules/MCP定义、权限、CI gate或业务语义。普通编辑的Markdown混合换行已恢复到候选冻结的原CRLF风格，正文无额外差异。见[p4-consumer-fix/proposed.diff](../evidence/codex-only-migration/p4-consumer-fix/proposed.diff)及manifest.json；恢复为.mj-agent-local/p4-consumer-fix/before.zip，原P0–P4备份链保留。

**本轮出现并已恢复一项非预期原仓提交，不能称“零原仓提交/索引未变”。** Codex将定向pytest隔离TEMP错误放入原工作树的.mj-agent-local；Windows长路径使Git init失败，既有S1测试未检查返回码，随后git add -A/commit向上发现原仓，生成b2815f758d7d83393d5aa8c6db49c0c59d8b87f9（作者t<t@t>、消息base、784路径变化）。第一次实际测试10失败29通过，日志保留；没有推送或CI触发。原索引变化起初只观察到摘要不同，后由commit/reflog明确归因，不能继续解释成仅stat刷新。

立即暂停重跑、保存现场并提交精确恢复方案。Owner单独批准后，正常执行git reset --mixed --no-refresh 20e2f24c352cf640d9dd33234b128ca897804b99（无--hard），原HEAD/分支恢复，1426项工作文件存在性/字节逐一保持，暂存为空。原索引内容与正确HEAD一致，新二进制摘要b568c93beaebfec11f59da8bff0b39ef214dc066828c29d4f291f9ca35ca1382；不声称恢复旧28775dc7…字节。非预期对象/reflog保留审计，不改其他工作树。事件与批准恢复见incident.json、INCIDENT-RECOVERY-REVIEW.md、recovery-before.json和recovery-result.json；现场包incident-before-recovery.zip。既有S1 helper未检查init退出码的风险单列，不借此扩展#499/#552或削弱测试。

按Owner另外批准的仓外短隔离根C:/Users/Admin/AppData/Local/Temp/mj-p4-c01-20260921，原受控runner与原两文件命令重跑一次：**39 passed**，无skip或删断言；tracked-only/插件/离线限制保持。新S5命令实际STATIC_PASS、MCP公共计数实际8、原生技能/消费者/MCP检查STATIC_PASS、定向ruff与git diff --check通过；文档frontmatter和新链接无新增错误，历史wikilink WARN保留。新旧结果不重复累计独立用例；src运行时代码无改动。源与主副本817项当前身份一致，复跑前后两索引保持恢复后的摘要。详见targeted-offline-short-temp.json、document-verification.json及completion.json。

C01–C04定向消费者缺口已修复并验证，AC-07/U07更新；L5守卫、规则、配置及37技能内容未变，复用既有真实宿主证据，不重跑模型/信任。实际CI35560658984仍是本次六文件之前的817绑定，不能充作当前增量通过。已准备[CI-REVIEW.md](../evidence/codex-only-migration/p4-consumer-fix/CI-REVIEW.md)与CI-binding-proposed.json：既有私有验收仓/分支，819blob中813不变、6更新；只请求一次这六文件提交/push及原workflow，不发布原仓/不建PR/不变gate。尚未执行，当前CI需具名新增批准及实际结果。

当前P4修复本地通过、完整收口仍待六文件实际CI；P5 BLOCKED_PREREQUISITE_CURRENT_DELTA_CI，P6未启动。387项清理身份按本轮修复更新至cleanup-current.csv；81项条件清理授权与其准确恢复包保留，旧资产删除/移动0。新增原仓非预期提交1与Owner授权恢复reset1单列；远端操作/正式旧资产清理/新模型调用0。资产672行旧字段全保留、新增本轮状态/身份/证据/恢复列；使用doc-sync、doc-validate、flow-verify，Codex执行，Subagent=NONE。


## 56. 六文件已发布到具名私有验收仓；当前CI结果读取受阻（2026-09-21）

Owner已批准六文件提交、推送与既有CI。仅在既有私有ranzuozhou/mj-agent-p4-acceptance-20260920的maintain/p4-acceptance-20260920分支执行，正常生成提交40b470320ef9cf073f0d18867ca6134fa95637d2，父提交208dfa915d9fc465b64dd7131959367df0128c26，tree为8d800f400092f57e0d894b64dc36dbbe5a378c3c；正常push后远端ref实查一致。六文件集合与批准范围一致，819条暂存/提交blob完整匹配（813不变、6更新；817交付加原已批两公共词表），未发布原仓、建分支/PR、改CI gate或额外dispatch。见[CI-publication.json](../evidence/codex-only-migration/p4-consumer-fix/CI-publication.json)、CI-commit.json及CI-binding-proposed.json。前检驱动曾错误要求ci publish的.git必须为目录，未执行写入即停止；只读核对证明它本来就是原审阅包批准的ci source linked worktree，已修正该本地断言为精确Git元数据路径核验，未改变既有执行拓扑、保护或权限。该轨迹保留在CI-preflight-local-assumption.json。

第一次读取当前提交actions/runs返回gh exit1，只保留stderr长度，原因未知。Owner随后仅批准CI-READ-RETRY-REVIEW.md的完全相同只读查询重试一次；实际重试仍exit1，已记录明确net/http: TLS handshake timeout。命令、目标SHA及脱敏错误见[CI-result-read-retry.json](../evidence/codex-only-migration/p4-consumer-fix/CI-result-read-retry.json)。已停止该动作，没有第三次查询、换工具/参数/权限、重新推送或触发CI。记录脚本退出0仅代表保存结果成功，不代表gh或CI成功。当前run id、执行状态和结论均NOT_OBSERVED，取证路线BLOCKED_EXECUTION_ROUTE；不能记为CI测试失败，也不能断言CI未运行。上一版35560658984的1054通过22跳过仍保留为旧交付证据，不能代替本次六文件结果。

结束前只读复核原HEAD20e2f24c352cf640d9dd33234b128ca897804b99、原分支和空暂存，恢复后的索引摘要b568c93beaebfec11f59da8bff0b39ef214dc066828c29d4f291f9ca35ca1382保持；主副本索引ed49bcad…保持。原/主各817交付文件、私有提交819blob、387项清单当前身份全部吻合。此前事故恢复完整记录仍见§55，不把本轮原仓无提交扩大成历史从未提交；旧矩阵遗留的28775dc7索引与“当前CI通过”字段已在新矩阵明确更正，旧记录原文保留。

本地39项定向回归、C01–C04消费者修复、原生检查及已有L5真实宿主证据继续有效，无变化测试/模型调用未重跑。最新逐AC、L1–L5、U01–U07见[acceptance-after-CI-publication.json](../evidence/codex-only-migration/p4-consumer-fix/acceptance-after-CI-publication.json)：AC-12/U05待当前实际CI结果；AC-07/U07定向消费者修复保持验证，不把网络超时归为消费者新缺陷。L4静态语义与有限模型补充继续分开，workspace-write、Linux Codex宿主、Desktop及其他未测范围保留；L6服务/凭据/EVAL不追加为P4阻塞。

P4当前技术迁移尚未完成验收，P5 BLOCKED_PREREQUISITE_CURRENT_CI_RESULT_NOT_OBSERVED，P6未启动。387项清理及恢复清单更新至cleanup-after-CI-publication.csv；81项具名条件授权保留，但本轮旧资产删除/移动0，清理后验证NOT_TESTED。HEAD仅恢复已提交基线；P1共享安全测试拆分、未提交P0–P4成果沿用公共备份链，六文件修复前字节用before.zip，私有副本修复前字节用ci-before.zip，81项旧资产用legacy-81-before.zip，均未重放。记录备份records-before-CI-publication-result.zip。资产672行及所有历史字段、§2–55正文完整保留，新增当前CI状态列。Codex实施，Subagent=NONE；累计记录更新后停止于P4。


## 57. 当前六文件实际CI成功取证；P4必需验收收口，停止于P5之前（2026-09-21）

Owner在§56超时说明后要求继续修复，本轮先复核记录身份，再恢复一次完全相同的只读查询，gh exit0。查询确认既有push运行[35564875219](https://github.com/ranzuozhou/mj-agent-p4-acceptance-20260920/actions/runs/35564875219) attempt1已completed/success，head精确为40b470320ef9cf073f0d18867ca6134fa95637d2、分支maintain/p4-acceptance-20260920。继续读取该run、jobs与日志均exit0；1个job的49步骤全部success，checkout日志SHA一致。未修改网络/账号/权限/命令参数、未重推或重新触发CI。先前两次读取失败完整保留；新的实际成功替代当前受阻状态，不将网络超时记为CI失败。

当前实际CI主Tests977 passed、15 skipped、82 deselected；BDD13 passed、7 skipped；Contract64 passed，合计1054 passed、22 skipped。三组按工作流排除范围独立汇总，不累计本地或重复拓扑用例。lint、mypy、文档、索引、契约、BDD追踪以及原生入口/资源/消费者/MCP结构/守卫检查步骤均success，历史WARN、策略skip和PR-only条件未测保留；静态步骤不当作宿主执行。精确命令、日志、摘要见[CI-success-summary.json](../evidence/codex-only-migration/p4-consumer-fix/CI-success-summary.json)、CI-run-35564875219-run.json/jobs.json/log及CI-evidence-read-commands.json。旧run35560658984只保留旧版本历史；本次819blob完整绑定当前817交付加原已批两公共词表，包含所有已应用修复。

**P4已批准范围内的必需验收通过。** 当前C01–C04消费者修复、39项本地受控测试及六文件实际CI均通过；此前L1/L2原生独立性、L4的37技能/296维/142静态案例及五族/近邻模型补充、L5真实hook允许/拒绝/保护编辑/恢复/重入与R3独立原生规则合成拒绝证据按未变身份复用，没有重复模型调用或无变化测试。R3仅证明附加合成规则引擎拒绝，不夸称原六规则逐一独立执行；历史O2改写失败和后续有界客户端停止分别保留。最新逐AC、L1–L5和U01–U07在[acceptance-after-CI-success.json](../evidence/codex-only-migration/p4-consumer-fix/acceptance-after-CI-success.json)，AC-12/U05当前CI取证缺口已闭合，AC-07/U07修复继续有效。

通过范围仍限已批准Windows CLI0.147.0/gpt-5.6-sol只读宿主、Linux实际私有验收CI和已有离线路径/拓扑；workspace-write、Linux Codex宿主、Desktop及其他未测平台不由这些结果代替。原仓PR-only门禁、分支保护、最终review/版本发布和P5清理后验证仍NOT_TESTED/NOT_STARTED。L6八MCP服务、memory/生命周期、凭据与runtime EVAL范围外依赖不追加，U01/U02/U06的UNMET_DEPENDENCY及U03未测保留。本结论只表示P4验收完成，不表示计划§1的整体技术迁移、P5清理或P6版本交付完成。

原HEAD20e2f24c352cf640d9dd33234b128ca897804b99、maintain/codex-dev-mode-migration、空暂存与恢复后索引b568c93b…均保持，主索引ed49bcad…保持；原/主各817项、私有提交819blob、387清理项身份再次匹配。81项具名条件授权及恢复包重新核对，81成员当前字节全部一致，其中63项与HEAD相同、18项不同。当前[cleanup-after-CI-success.csv](../evidence/codex-only-migration/p4-consumer-fix/cleanup-after-CI-success.csv)保留逐文件用途/替代/消费者历史证据，追加本次授权、身份与恢复结论；旧NO_AUTHORIZATION列仅为历史，不覆盖已获具名批准。P4技术前置已满足，P5未启动，执行前仍须当场核对具名绝对目标、消费者、身份与授权范围；无需重批未变化的已批81项，但未知/新变化项不得扩批或整目录删除。

本轮正式源修复、旧资产删除/移动、测试重跑、模型调用、暂存/提交/push/PR/CI触发均0；仅取得既有CI结果及更新记录。P1共享安全测试拆分和全部P0–P4成果保留，§55事故及授权恢复不抹除。Git HEAD只恢复已提交基线；未提交成果沿用公共备份及六文件before.zip，私有修复前字节ci-before.zip，81项准确字节legacy-81-before.zip。记录备份records-before-CI-success.zip。累计报告§2–56及资产672行全部历史字段保留，Codex执行、Subagent=NONE。记录更新后停止，不执行P5/P6。


## 58. P5具名81项已删除；六文件消费者修订完成，清理后离线复验路线受阻（2026-09-21）

**P5未完成：BLOCKED_EXECUTION_ROUTE（清理后必要受控测试尚未启动）。P6未启动。** §57的P4批准范围验收与实际CI35564875219/40b470320ef9cf073f0d18867ca6134fa95637d2保留为清理前证据。没有使用旧NO_AUTHORIZATION或CI读取超时字段覆盖最新授权/成功证据，也没有将该CI标为本轮清理后的通过结果。

入场逐项复核原绝对根、HEAD20e2f24c352cf640d9dd33234b128ca897804b99、maintain/codex-dev-mode-migration、空暂存及恢复后索引SHA256 b568c93beaebfec11f59da8bff0b39ef214dc066828c29d4f291f9ca35ca1382。原817与最新交付绑定一致，387项当前身份一致；81具名文件均为根内普通文件，目标及各祖先无symlink/junction/reparse，当前字节及81个ZIP成员逐一吻合，63项HEAD_EXACT、18项HEAD_DIFFERS。详情见[preflight.json](../evidence/codex-only-migration/p5-cleanup/preflight.json)及[predelete-81-current.json](../evidence/codex-only-migration/p5-cleanup/predelete-81-current.json)。仅复用旧主副本/私有819的已有有效绑定，不声称本轮重新运行旧宿主或CI。

本轮扫描发现P5-C05–C08：公开env/MCP示例注释、wrapper基线当前审计指针、提交规范当前引用和AI-context审计作者推导规则仍使用旧资产。形成六文件精确差异及恢复包后，Owner明确回复“批准六文件修订与离线复验，继续原81项”。六份公开文件已应用审阅差异；键值行不变、.env.example保持ASCII、审计SCHEMA指定历史观测后缀保留。1933条原扫描结果与精确路径补扫区分历史记录、负向/合成测试、排除/拒绝词表和当前消费者；新六文件残留16处为明确历史或负向说明。当前原生执行消费者检查通过；不以零关键词或批量历史标签充作全面动态证明。原28可执行/53暂留的审阅保留为历史，被[consumer-closure-current.json](../evidence/codex-only-migration/p5-cleanup/consumer-closure-current.json)和六文件实际应用记录取代。既有C01–C04修复未重放。

**实际删除81文件，原81范围内未删除0；目录删除/移动0。** 删除前整组及逐文件即时复核绝对目标、普通文件/祖先、SHA、恢复成员与授权，使用同一PowerShell的Remove-Item -LiteralPath逐文件执行，无-Recurse。实际调用为无profile的PowerShell中 `& '.mj-agent-local/p5-cleanup/delete-81.ps1'`，exit0；脚本日志记录其等价独立调用形式。删除结果每项落盘，见[delete-81-result.json](../evidence/codex-only-migration/p5-cleanup/delete-81-result.json)与[逐文件删除恢复表](../evidence/codex-only-migration/p5-cleanup/cleanup-81-result.csv)。未运行此前仅28项的delete-independent脚本。387总表中另271保留/审阅、19候选证据保留、16项P3测试已缺失只复核，未再次删除。未按目录清空.claude、sdd/adapters、_common、.migration或本地备份；候选/验收副本仍承担证据/恢复用途且无新增清理授权。既有Remove-Item守卫覆盖局限仍保留；此次可执行依据是具名批准和身份/依赖/恢复复核，不是未被阻断。

清理后原树七条命令全部exit0：native governance entries/consumers、native skills skills/resources、check_codex_native、frontmatter、wikilinks。结果分别为STATIC_PASS；142份canonical文档frontmatter通过，13份归档反扫0违规，5根入口链接0未解析。这些是静态结果，不冒充真实hook/模型拦截。原817交付仍为817：811不变、6个新获批公开注释/文档变化；81旧资产本来就在原生交付之外。当前清单见[delivery-after.json](../evidence/codex-only-migration/p5-cleanup/delivery-after.json)。37技能正文、共享安全测试/runner、原生代码/配置/守卫、P4两项最小修复及后续修复均保持入场身份，已完成的有限L4/L5证据仅按未变机制复用。

本轮受控测试计划为独立当前817副本的十份受影响测试，保持tracked-only、封闭环境、锁定插件和离线策略。但在C:/Users/Admin/AppData/Local/Temp/p5-x95ag_4r容器创建成功后，创建r子目录返回WinError5 Access is denied。**尚未执行git init、复制、临时索引、audit derive或pytest**；没有测试通过/失败/skip计数，全部NOT_TESTED。记录helper最终exit0只表示落盘成功，操作结果是BLOCKED_EXECUTION_ROUTE。没有将TEMP放到原仓，没有再次向上发现原仓，也没有换工具/目录/参数/编码、提权或改保护重试。部分空容器保留，不扩大删除。实际命令/环境/各退出与错误见[verification-after.json](../evidence/codex-only-migration/p5-cleanup/verification-after.json)，剩余具名范围与所缺输入见[EXECUTION-ROUTE-REVIEW.md](../evidence/codex-only-migration/p5-cleanup/EXECUTION-ROUTE-REVIEW.md)。需解决仓外正常访问路线后才能继续相同受控复验，不需重批或重放六文件/81项操作。

逐AC、L1–L5、U01–U07见[acceptance-current.json](../evidence/codex-only-migration/p5-cleanup/acceptance-current.json)：AC07静态消费者闭合、AC08具名删除及范围保持通过；AC09清理后必要离线验证受阻；AC10精确恢复准备通过而P6交接未执行；AC11仅本阶段范围核查通过；AC12清理前实际CI与当前未发布状态分开。L1静态通过，L2新副本未建立但既有拓扑证据保留，L3清理后离线NOT_TESTED，L4/L5保持原批准平台/用例边界且本轮没有新增宿主调用。U01/U02仍UNMET_DEPENDENCY，U03仍NOT_TESTED，U04保持P3 MANUAL_ROUTE_EXECUTED_VERIFIED及已有具名实际应用证据，不是通用解锁；U05旧实际CI已验证而本次增量CI未测；U06仍UNMET_DEPENDENCY/NOT_TESTED；U07当前FORMAL_STATIC_CONSUMER_CLOSURE_PASS、受影响运行复验未测。L6服务/凭据/EVAL仍在范围外，不新增为P5门槛。

恢复区分：HEAD仅恢复已提交基线；未提交P0–P4成果使用具名公共备份链，P1共享拆分不能由HEAD覆盖。legacy-81-before.zip逐成员恢复已删81项准确工作字节；本轮六文档修订前字节为consumer-six-before.zip。记录更新前另保存records-before-section58.zip。公共包及成员/摘要见[recovery-current.json](../evidence/codex-only-migration/p5-cleanup/recovery-current.json)。如未来回到P3组之前，须先逐个审查当前后续P4增量并处理身份，再处理p4-minimal-fixes两文件恢复（GLOSSARY不属原188项），确认p3-postformat-group-recovery.diff适用的188项身份后，才核对p3-preapply-public.zip；不能直接把旧整组diff套到当前树。未执行恢复、reset/clean或补丁重放。

累计资产672行及原字段值完整保留，新增本轮状态列；[387项当前处置表](../evidence/codex-only-migration/p5-cleanup/cleanup-387-current.csv)逐项标记删除/保留/原P3已删及原因。最终公开文件范围、817身份、原HEAD/分支/空暂存/恢复后索引和证据摘要见[final-check.json](../evidence/codex-only-migration/p5-cleanup/final-check.json)。本轮新增暂存/提交/push/分支/PR/合并/部署/远端CI/模型调用均0；原§55事故及Owner恢复不抹除。启动首个只读shell时用户profile初始化有访问拒绝噪声，后续均无profile执行；未修改个人配置。Codex实施，使用既有repo-scan与flow-verify流程，Subagent=NONE。

不宣称整体技术迁移验收、旧资产全部退役或P5完成。P6后续仍需最终差异/交付检查、指南和变更交接，以及各版本动作的明确授权；本轮仅登记，不准备或执行P6。累计记录更新后停止。


## 59. P5清理后受控复验通过；本次具名阶段完成，停止于P6之前（2026-09-21）

**P5在本次已授权的具名清理与受影响复验范围内完成。P6未启动。** Owner对§58的仓外访问阻塞回复“授权，执行”，当前执行环境已解除文件系统沙箱限制；Codex未修改权限、个人配置、项目/hook信任或守卫。先核对§58记录摘要、原817交付、81缺失状态、HEAD/分支/空暂存/恢复后索引及当前全部真实工作树，再从原C:/Users/Admin/AppData/Local/Temp/p5-x95ag_4r/r创建失败处继续。原容器为空、祖先无Git和reparse、位于全部真实工作树之外；同一路径正常mkdir成功，没有换目录或工具避开拒绝。§58的原始WinError5和NOT_TESTED完整保留，新的实际执行证据更新当前状态，不回写历史。

已按审阅方案建立独立r副本与p测试探针，分别实际git init成功、.git目录与rev-parse根精确一致后，才复制当前817公开文件并建立独立tracked索引。817项全部SHA一致；git add只在该临时副本中按明确路径分14批，每批不超过60项以满足Windows命令长度，不改文件集合。pytest TEMP使用同级t目录，不在r副本或任何真实工作树内，因此临时测试仓不能向上发现原仓。未改tracked-only、锁定插件、封闭非秘密环境或离线策略；未复制秘密、个人配置、原.git或旧81资产。

**同一受控runner的十文件定向复验：265 passed、22 subtests passed，0 skipped，exit0，pytest耗时25.89秒。** 子测试单列，不重复计入测试总数，也不与旧1054 CI或其他拓扑累计。覆盖P1共享离线安全、S5原生消费者与fixture纪律、原生入口/扫描域/技能合同、守卫反例、MCP离线launcher/wrapper及禁入范围、AI-context审计、env示例ASCII。没有修改测试断言、业务语义、门禁或新增skip。`check_ai_context_audit.py --derive`另行exit0，当前推导23个Markdown面。精确argv、环境、所有25条过程命令和退出/输出见[verification-resume.json](../evidence/codex-only-migration/p5-cleanup/verification-resume.json)。临时fixture内部Git提交属于原测试的合成用例，不是原仓或交付提交。

测试前后原817与副本817全部字节不变；临时索引a112535b88503dff151ccf4f13c0cfee9044f8d329e820b3d5639d218e025458不变。原HEAD20e2f24c352cf640d9dd33234b128ca897804b99、maintain/codex-dev-mode-migration、空暂存及恢复后的索引b568c93beaebfec11f59da8bff0b39ef214dc066828c29d4f291f9ca35ca1382保持。六文件修订/81具名删除没有重放，本轮新增源修订/删除/移动/原仓暂存提交/远端发布/CI/宿主调用均0；81已删、16个P3已删测试仍缺失，271保留/审阅与19候选证据保留。副本/候选/备份继续保留为验收恢复材料，不注册为第二份维护源，不扩大清理范围。

P5完成依据为计划§4.7、§6.3的受影响复验要求：81旧文件已在817原生交付之外，新增六项仅为已批准的公开注释和文档消费者修订；§58七项清理后静态检查通过并按未变身份复用，本轮audit derive和265测试/22子测试补齐必要运行缺口。37技能、原生执行代码/配置/守卫未变，P4已批准L4/L5实际证据仅在原平台/用例边界复用。离线守卫调用不冒充真实宿主拦截；本轮没有新增模型或宿主验证。未识别需新增发布/信任的P5必需动作，不为本阶段重复无变化整套CI或宿主。清理前CI35564875219/40b4703仍只绑定旧交付；**清理后CI为NOT_TESTED**，最终版本交付的实际SHA/CI/review检查属于P6，不伪称已经完成，也没有改变原验收门禁。

最新逐AC/L/U见[acceptance-after-resume.json](../evidence/codex-only-migration/p5-cleanup/acceptance-after-resume.json)。AC07消费者与定向运行通过、AC08具名范围保持、AC09必要受影响复验通过、AC10恢复来源通过；AC11仅本阶段范围核查、AC12版本动作仍未执行。L1静态、L2当前独立副本、L3离线通过，L4/L5按未变身份保留有限实际证据；新合成fixture不代替P4已有真实clone/linked/Linux CI证据。U04保持MANUAL_ROUTE_EXECUTED_VERIFIED_P3及后续具名应用，U07保持FORMAL_STATIC_CONSUMER_CLOSURE_PASS并补上当前受影响离线通过；U01/U02仍UNMET_DEPENDENCY，U03未测，U05清理前CI已验证而当前CI未测，U06仍UNMET_DEPENDENCY/NOT_TESTED。L6继续范围外，不作为新门槛。

累计资产672行及全部历史字段值保留，追加当前通过状态；[81项当前结果](../evidence/codex-only-migration/p5-cleanup/cleanup-81-after-resume.csv)与[387项当前处置](../evidence/codex-only-migration/p5-cleanup/cleanup-387-after-resume.csv)保留旧状态并追加最新复验列，原BLOCKED字段只作历史。§58之前报告及原始失败日志完整保留。记录更新前备份为.mj-agent-local/p5-cleanup/records-before-section59.zip；HEAD基线、未提交P0–P4备份、P4增量先于P3整组恢复的身份顺序、81精确成员与六文档恢复包继续有效，见[recovery-after-resume.json](../evidence/codex-only-migration/p5-cleanup/recovery-after-resume.json)。没有实施恢复或清空临时材料。

最终原树、817、索引、公开文件与累计历史的范围校验见[final-check-resume.json](../evidence/codex-only-migration/p5-cleanup/final-check-resume.json)。只宣布本次P5完成及上述边界，不宣布所有历史资产/恢复副本已清空或整体版本交付完成。P6仍需最终范围/交付检查、交接及独立版本操作授权；本轮不准备或执行P6。Codex按既有flow-verify技能执行，Subagent=NONE；更新累计记录后停止。


## 60. P6前必要准入核查完成：可进入P6，尚未执行P6（2026-09-21）

Owner要求“执行进入P6前的必要工作”。本轮仅复核P5完成结论、当前身份、恢复来源与阶段边界并更新累计记录；不将本请求解释成已经进入P6或授权版本操作。**准入结论：READY_FOR_P6_ENTRY，当前未发现P6准入阻塞。P5具名范围完成保持有效；P6仍NOT_STARTED。**

现场重新验证原绝对根、HEAD20e2f24c352cf640d9dd33234b128ca897804b99、maintain/codex-dev-mode-migration、空暂存及恢复后索引b568c93beaebfec11f59da8bff0b39ef214dc066828c29d4f291f9ca35ca1382。§59的30份结果绑定摘要、原817文件及仓外验收副本817文件、临时索引、387处置身份全部吻合；81已删准确集合和原P3的16已删测试未重放。81准确恢复成员、六文件修订前后字节、全部具名公共恢复包和上轮记录备份摘要再次核对通过。P1安全拆分、P4两文件及后续修复、原生37技能/配置/代码、候选和历史证据无新变化。

已有七条清理后静态命令、当前265测试/22子测试/零skip及audit derive23面的证据仍绑定当前字节，因此未重复无变化测试/宿主调用，也没有新增修复。计划§4.7/§6.3的P5具名清理及受影响复验前置已满足。清理后CI仍NOT_TESTED，旧CI35564875219/40b4703仍仅证明清理前交付；最终版本差异、交付清单/实际SHA/CI/review、指南与CHANGELOG更新、提交拆分及PR草案属于计划§4.8的P6工作，不能倒置为本次准入必须先执行的版本步骤。L4/L5证据只保留原批准平台与用例边界；L6的服务/凭据/EVAL依赖仍在范围外，不新增准入门槛。

逐AC、L1–L5、U01–U07及八维范围核查见[readiness.json](../evidence/codex-only-migration/pre-p6/readiness.json)。U04/U07维持此前有界实际路线/消费者闭合通过，U01/U02/U06仍缺范围外依赖，U03未测，U05旧实际CI与当前CI未测分开。未发现需要在进入P6之前补做的新代码、消费者或文档修复。十类正式文档本轮均无变更，P6文档任务只登记，不提前实施。

下一阶段仍需独立P6范围指令；进入后的准备与实际版本动作分开。暂存/提交/推送/PR/CI触发、额外清理不由本轮授权推导，旧私有验收六文件发布批准与81项删除批准也不能扩大到最终原仓交付。人工合并继续交Owner；#499/#552不自动关闭，秘密/服务/信任/权限不触碰。保留271保留/审阅、19候选证据和全部验收/恢复材料，不把“必要工作”扩成批量清空。

记录更新前公开备份.mj-agent-local/p5-cleanup/records-before-section60.zip；HEAD只恢复提交基线，未提交成果及P4增量先于P3整组恢复的身份顺序继续沿用既有记录，未执行任何恢复。累计672行资产原字段值和报告§59及以前全文保持，新增准入列；最终核验见[final-check.json](../evidence/codex-only-migration/pre-p6/final-check.json)。Codex按既有repo-scan的只读核查流程执行，记录写入限本请求的累计状态；Subagent=NONE。源编辑/删除/移动/测试重跑/远端读取/暂存/提交/推送/PR/CI/宿主调用均0。更新后停止于P6之前。


## 61. P6最终范围、文档与版本审阅包（2026-09-21；具名批准前停止）

本轮仅执行Owner本次P6请求。原绝对根、Git元数据、maintain/codex-dev-mode-migration、HEAD `20e2f24c352cf640d9dd33234b128ca897804b99`、空暂存和索引b568c93b…均符合预期；两端实际develop仍为同一SHA。原P5的817身份、30份结果中的不变记录、81准确ZIP成员、387处置及10公共恢复包全部复核。81删除和P3的16测试删除未重放，265 passed/22 subtests/零skip及7项清理后静态结果按身份复用，未重跑整套测试。

技术迁移：P0–P5已批准范围的验收保持有效；P6发现新的活动文档消费者后，最终闭合仍待一项受保护政策修订，不宣称整体最终版本已验收。版本交付：审阅包已准备，原仓未暂存/提交/推送，无PR、最终CI、review或合并。外部服务：L6范围外，NOT_TESTED。逐AC、L1–L5、U01–U07见[acceptance.json](../evidence/codex-only-migration/p6/acceptance.json)。AC-07/U07当前待政策行，AC-10交接完成，AC-11范围核对通过，AC-12如实记录未发布；旧BLOCKED/NO_AUTHORIZATION仅保留历史。

必要文档共17文件：上手/快速启动/SPEC指南、README/CONTRIBUTING/config说明、docs索引、CHANGELOG、7份PR模板及2份普通开发技能的署名示例。新发现先形成具体diff、影响、验证/恢复方案，之后仅应用普通文档授权范围；详见[当前文档差异](../evidence/codex-only-migration/p6/documentation-final.diff)。后续三文件纠正了必需的--surface参数和过时MCP诊断，原候选应用记录作为历史保留，当前身份在[documentation-final.json](../evidence/codex-only-migration/p6/documentation-final.json)。817中800不变、17文档变化；相对更早清理前811/6口径保持历史，不混用。35技能字节不变，2技能仅可选署名例及说明变化，八维静态复核；未把旧两技能模型canary套到新字节。守卫/config/rules/启动器未变，L5仅复用既有Windows CLI批准平台/用例的真实证据。

新受保护待办仅 `policies/ci-gates.md` §4季度审计一行：旧permissions.deny/ask、enabledPlugins没有原生活动对象。已准备[一行补丁](../evidence/codex-only-migration/p6/policy-proposed.diff)、当前SHA及恢复包；§55批准只覆盖原计数命令和指针，不扩展到该行。本轮未应用，未改guard、契约、CI gate、信任、权限或生成审批凭证。缺该批准只暂停此增量及依赖最终闭合的发布，不重开#499/#552，不重构全仓。

本轮8条静态/文档命令全部exit0：frontmatter142、wikilinks归档0/root5链接0、native skills/resources、governance entries/consumers、native config及git diff --check。最后一项保留GLOSSARY既有LF→CRLF warning，native session_approval UNKNOWN不是授权判断；未测host/services字段不填绿。使用既有develop依赖解释器、P5环境白名单与仓外新TEMP，不调用pytest、不创建测试Git、不写索引；初次PATH中python不存在exit1，改用已记录解释器正常执行，这是环境定位失败而非技术保护拒绝。详见[verification.json](../evidence/codex-only-migration/p6/verification.json)。没有新增断言、skip、依赖或门禁降级；BDD/TDD=沿用既有安全回归，新增为文档验证。

原仓完整交付审阅独立于817验收清单：43正式未跟踪新文件逐项纳入候选交付；97删除对应81+16；正式资产/消费者/测试、必要指南以及明确引用的公共证据分组。历史、候选、运行输出与个人/秘密排除项逐文件在[file-inventory.csv](../evidence/codex-only-migration/p6/file-inventory.csv)，清单不是暂存批准。逻辑G1原生切换+安全测试+具名删除、G2上手交接、G3累计与明确证据，准确路径与信息在[commit-groups.json](../evidence/codex-only-migration/p6/commit-groups.json)，PR正文见[PR-BODY.md](../evidence/codex-only-migration/p6/PR-BODY.md)。选入证据依具名要求和累计文档引用闭合，未将整个证据目录或CSV资产行当提交集合；未入选原始材料及所有恢复ZIP保留本地。Git内部原有作者配置不改，Codex贡献由正文记录，不伪造模型署名。

只读远端结果：origin=GitHub MJ-AgentLab/mj-agent，gitee=ranzuozhou/mj-agent；两端迁移分支不存在，PR与branch CI查询返回空。develop传统protection接口404是Branch not protected；有效ruleset另已观察到ci必需、strict同步、1审批、last-push审批、review-thread解决及仅merge方式，不能将404描述为无保护。既有CI35564875219/40b4703仅证明私有验收仓清理前交付；本轮未重新触发CI。最终原仓push和PR会按现有workflow触发Actions，必须另有具名批准。见[remote-observation.json](../evidence/codex-only-migration/p6/remote-observation.json)。发布步骤及一次性待批准范围在[DELIVERY-REVIEW.md](../evidence/codex-only-migration/p6/DELIVERY-REVIEW.md)，人工merge不在请求范围。

恢复：P6 before.zip保存本轮入口九文件工作字节，additional-before.zip保存17文件，before-doc-correction.zip保存三文件中间状态，policy-before.zip保存未应用政策行的当前文件。旧HEAD只恢复提交基线；P0–P4公共备份和增量、legacy-81-before.zip、consumer-six-before.zip各自职责不变。旧P3整组差异须先处理后续增量并核对188项身份，不能直接套当前树。没有reset/clean、恢复重放、额外删除或备份清空。原672行全部138字段值和报告§60以前字节前缀保持，新增当前列及漏登记的具名文件（含env_drift文档修订），现679行；最终身份见[final-check.json](../evidence/codex-only-migration/p6/final-check.json)。

Codex完成核查、普通文档修订、验证与审阅包；依据repo-scan及政策§2的多capability只读探索要求，委派consumer_review仅做消费者与最终diff复核，无写入/测试/网络/Git动作。Owner HITL命中政策元规则增量与最终stage/commit/push/PR/CI，均待具名批准；不重索P5删除/六文件旧批准。当前阶段停止，不自动合并、部署、关闭问题或清理worktree。


## 62. P6具名版本操作获准，政策单行已应用并复验（2026-09-21）

Owner对§61对应完整审阅包回复“批准”，覆盖准确政策单行、490路径G1/G2/G3暂存提交、先Gitee后GitHub同分支推送、develop-base PR及对应CI/结果核查；不包含merge、部署、额外清理或L6。原392个非删除交付文件绑定全部吻合，原HEAD/分支/空暂存/索引与两端develop再次匹配，目标分支仍不存在。当前批准是具名范围决策，不建立hook可消费的审批凭证，也不改变信任/权限。

普通apply_patch成功应用policies/ci-gates.md季度审计单行。首次raw SHA断言失败：工具使改行换行符与批准CRLF字节不同，规范化正文逐字一致。原观察保存后恢复批准的准确字节SHA729d085965e848c5e572e6f3879e20f76a79f2e202d42e7c2a722d8df4f2fc06；这是换行核对失败，不是技术保护拒绝。frontmatter142、归档引用0/root链接0、git diff --check全部exit0，GLOSSARY既有换行warning保持；关键guard/config/rules/CI/runner身份不变。详见P6 policy-review.json追加approved_execution，原待批准记录和精确包备份保持。

AC-07/U07消费者闭合通过，P0–P6已批准有界技术迁移验收通过；L4两份署名示例仅静态八维补评，L5原平台/用例证据边界不扩。版本操作当前获准、尚未预填提交/push/PR/CI成功；实际结果在后续累计记录追加。外部服务仍NOT_TESTED。开始按已批准三组执行，途中身份变化/技术拒绝按实际停止受影响步骤，不换工具、编码或权限绕过。


## 63. P6政策闭合通过、G1已暂存；commit执行策略拒绝（2026-09-21）

本轮延续§62具名批准：G1用准确NUL路径清单暂存，--no-renames复核255路径与批准组完全一致。首次暂存检查发现此前未跟踪tests/unit/test_offline_execution_boundary.py末尾两条空行；原工作区git diff --check未覆盖该新文件，先前PASS只限当时检查域，不能替代本次staged检查。首次组合命令的工具总体exit0来自最后shortstat，不表示中间检查成功；后续单独调用证实exit1。该问题不是项目断言失败。已先保存准确before ZIP及diff/影响方案，再仅去除EOF空行并正常重新暂存本具名路径；AST完全相同，76条assert保持，单独git diff --cached --check返回0。不删有效断言、不增加skip，不重跑没有语义变化的测试。

git commit实际尝试被工具执行策略在进程创建前拒绝：`Rejected("approval required by policy, but AskForApproval is set to Never")`。状态BLOCKED_EXECUTION_ROUTE，没有Git退出码或新提交SHA；没有重试、换工具、参数、编码、权限、hook/rules或建凭证绕过。Owner业务授权仍有效，技术路线与范围授权分开，不再要求重复批准同一组。G2/G3未暂存，先Gitee后origin的push、PR创建、触发CI及合并全部未执行。

原根/分支/HEAD20e2f24c352cf640d9dd33234b128ca897804b99保持；当前G1暂存255项，索引SHA256 `dc8f652958d33d39336e4b0dc62a28825406448d50e418bf11ab29351cadbc6e`，是已授权暂存造成的有意变化；不再把原空索引b568c93b…当当前值，也不reset它。原81+16缺失集合不变，没有新删除或工作树清理。政策准确SHA及关键guard/config/CI不变证据保留；原生817相对P5为798不变、17普通文档、1政策单行、1测试EOF格式变更，旧800/17为批准前历史绑定。

当前技术迁移在已批准有界范围内通过；额外EOF格式问题已闭合。版本交付部分执行、阻于commit策略，未推送/PR/最终CI/review/merge；外部服务L6仍NOT_TESTED。更新acceptance/commit-groups/最终身份及679行资产的新增执行列，原字段/§62以前记录保留。全记录见P6 final-check.json追加publication_execution及本地.mj-agent-local/p6-publication/execution.json，恢复before ZIP与原始失败轨迹保留。旧私有CI35564875219仍只证明清理前40b4703。人工处理合法执行路线后才能从当前G1暂存停点继续；本轮更新记录后停止，不自动合并、部署、关闭#499/#552或修改个人配置。


## 64. P6 Owner完成G1，G2准确暂存待人工提交（2026-09-21）

Owner贴出个人终端git commit成功结果；本轮独立核实HEAD为e5f99c87a50ad47856a41f40c2acccf75a5534da，父提交为20e2f24c352cf640d9dd33234b128ca897804b99，原根及maintain/codex-dev-mode-migration分支一致。G1 --no-renames共255路径与批准集合完全相同；Git摘要238文件是重命名折叠口径。所有存在G1文件SHA256与此前post_attempt_working_hashes一致，G1工作区相对新HEAD无差异。实际作者/提交者为Owner既有Git身份；迁移实施来源仍为Codex，未伪造署名。§63的拒绝记录保留为此前时点，不覆盖本次真实提交。

进入本轮时暂存为空。G2全部23文件SHA256与原批准绑定相同；核对既有G2.paths后执行git add --pathspec-from-file=.mj-agent-local/p6-publication/G2.paths --pathspec-file-nul，exit0；git diff --cached --check独立exit0，准确集合23，无额外路径。GLOSSARY既有换行warning保留。没有代码/文档语义新改动，不重复P5或P6已通过测试。当前G2仅暂存，G3的212路径尚未暂存。Codex提交通道仍为BLOCKED_EXECUTION_ROUTE，未重试commit或变更工具/权限/信任；下一步由Owner提交G2，三组完成并复核前不推送中间状态。

本轮记录更新前，7个具名文件准确字节保存于.mj-agent-local/p6-publication/owner-g1-records-before.zip，适用身份为上述G1 HEAD及G2暂存状态。final-check/acceptance/commit-groups追加owner_g1_observation；资产表及交付清单追加两列，旧字段与失败轨迹保留。技术迁移仍为已批准平台/用例范围内通过；版本交付部分完成（仅G1提交），双推/PR/最终CI/review/merge未执行或未观察；外部服务L6仍NOT_TESTED。HEAD只覆盖G1已提交成果，G2/G3及历史迁移恢复仍须原有P0–P6具名备份；不reset/clean，不关闭#499/#552，不扩展阶段。


## 65. P6 Owner完成G2，准备G3最终证据组（2026-09-21）

Owner终端报告G2成功后，独立核实HEAD为1eb9257f15ee250b732f5db8a7f0b4266c0d2401，父提交为e5f99c87a50ad47856a41f40c2acccf75a5534da。原根/分支一致，进入本轮暂存为空。G2准确23路径与批准集合一致，工作字节SHA256逐项匹配原post_attempt_working_hashes；G1/G2所有路径相对当前HEAD无未提交差异。G1/G2均由Owner提交，实施来源为Codex。历史§63执行拒绝不覆盖两次人工提交。

G3保持原批准212路径，未增加证据目录或CSV行批量选择；全部具名文件存在。进入本轮，除§64更新的七份累计记录外，其余205路径与原交付绑定完全一致。本轮八文件修改前字节保存于.mj-agent-local/p6-publication/owner-g2-records-before.zip，适用HEAD为上述G2提交。更新三份JSON的owner_g2_observation、资产表/清单追加列、累计报告及交付说明；PR正文修正“尚无提交”“政策待批准”“暂存仍空”和恢复HEAD范围等过时陈述，保留历史证据正文。G3实际暂存/检查结果在本节后续追加，不预填通过。

技术迁移维持有界通过，未新增行为变化或重跑已通过测试。版本仅G1/G2完成，三组完成前不推送；双推/PR/最终CI/review/merge未执行或未观察。Codex提交通道仍BLOCKED_EXECUTION_ROUTE，未重试被拒动作、未修改信任/权限或建凭证。外部服务L6仍NOT_TESTED。Owner原具名批准有效，不重复索取；原P0–P6备份及所有历史失败字段保留。


G3实际暂存：git add --pathspec-from-file=.mj-agent-local/p6-publication/G3.paths --pathspec-file-nul返回0，准确212路径，无额外文件。Git提示既有文本换行转换，工作字节未被重写。git diff --cached --check返回2，2161条诊断集中于20份原已批准的历史证据：17份.diff共2158条、3份P2 Markdown各1条EOF空行。20文件逐项SHA256与原批准绑定一致。补丁作为文本入库时，补丁空白上下文/原始内容会被外层diff检查诊断；三份历史文档末尾空行同样保留。遵守不批量重写历史记录的要求，本轮不改证据原文、不修改whitespace配置、检查脚本或CI门禁，不将该失败改标PASS。当前CI workflow没有git diff --check步骤；这不证明CI会通过，最终CI仍未运行。完整输出留在.mj-agent-local/p6-publication/g3-cached-check.txt，逐文件诊断计数与边界见final-check.json的owner_g2_observation.G3。G1/G2检查结果不被该新覆盖域覆盖；G3携带已披露的历史空白检查失败等待Owner人工提交。


## 66. P6三组提交全部核实；发布前发现develop新基线（2026-09-21）

Owner终端G3结果已独立核实：HEAD b2a730ddb4419cb39a767815f160115e02c2b575，父提交1eb9257f15ee250b732f5db8a7f0b4266c0d2401；G1为e5f99c87a50ad47856a41f40c2acccf75a5534da。原绝对根/分支/Git目录一致。G3准确212路径及全部工作SHA256与提交前g3-staged-snapshot.json一致；相对20e2f24c的最终490路径与原G1/G2/G3并集完全一致，没有漏项或额外纳入。进入本轮暂存为空、已跟踪工作区无差异。475未跟踪项全在原排除清单：231候选、244历史材料，未清理或纳入。三组由Owner提交，Codex实施与审查来源保持。§65的G3待提交状态为历史时点，不覆盖本次真实提交。

只读远端核查发现新差异：Gitee develop仍20e2f24c352cf640d9dd33234b128ca897804b99；GitHub develop已为243b13f61ded1b2e398b346239305ea2a1be811a。GitHub compare确认基线前进两提交，由#551将.github/workflows/ci.yml第39行setup-uv固定SHA从20cfd1b(v10.0.1)更新为bec219d(v10.1.0)，仅一行。当前迁移树该行精确匹配升级前内容；未fetch/merge、未改CI。两端迁移分支均不存在，gh pr list --state all返回空；未push、创建PR、触发最终CI或review。

形成具名增量方案：先把本节、asset-map.csv新增两列与p6/final-check.json的owner_g3_observation作为三文件记录提交（docs: record final migration commits and base drift）；再将确切243b13f61ded1b2e398b346239305ea2a1be811a合入当前迁移分支，保留原三提交，不rebase，不改develop或双远端配置。预计合并后工作差异只有上述CI固定SHA一行，原生gate命令及所有迁移成果不变；冲突或其他差异须先停查。合并消息建议infra: sync develop setup-uv update。此额外合并/新受保护CI增量不假设由原三组批准覆盖；待Owner具名决定，原双推/指定develop-base PR及CI触发批准继续有效。

完整差异/验证/恢复与命令顺序见本地.mj-agent-local/p6-publication/DEVELOP-SYNC-REVIEW.md及develop-sync-proposed.diff。本轮三记录及CI原字节在修改前备份为owner-g3-records-before.zip，适用HEAD b2a730d。记录修改尚未暂存。恢复保留b2a730d及所有P0–P6具名备份，HEAD不恢复排除材料；不reset/clean，不自动合并PR、部署、关闭#499/#552或清理工作树。技术迁移既有有界验收保持通过；新setup-uv运行环境对迁移尚未验证；版本仅三组本地提交完成，外部服务L6仍NOT_TESTED。Codex发布路线仍BLOCKED_EXECUTION_ROUTE，没有重试或绕过。


## 67. P6新增记录提交与指定develop合并获准（2026-09-21）

Owner对§66对应DEVELOP-SYNC-REVIEW.md两项增量回复“批准”：三文件记录提交docs: record final migration commits and base drift，以及将243b13f61ded1b2e398b346239305ea2a1be811a合入maintain/codex-dev-mode-migration（infra: sync develop setup-uv update）。合并工作差异限CI setup-uv固定SHA/版本一行；冲突或其他差异先核查，不扩大授权。原双推、develop-base PR及其CI触发批准继续有效；不包括PR合并、develop推送、部署、清理或L6。

执行前独立核实HEAD b2a730ddb4419cb39a767815f160115e02c2b575，分支未变、暂存为空，仅三份已具名记录未暂存。git ls-remote origin确认develop仍为指定243b13f6，迁移分支仍不存在，exit0。三记录本轮修改前字节保存至.mj-agent-local/p6-publication/base-sync-approved-before.zip；final-check追加base_sync_approval，资产表追加两列，所有旧字段/历史保留。当前准备按三具名路径暂存；实际暂存集合和检查结果由本地base-sync-record-staged.json记录，不预填commit或merge成功。

Codex提交审批路线仍BLOCKED_EXECUTION_ROUTE，没有重试git commit或改权限/工具/信任绕过；Owner在个人终端先完成记录提交后，核对新HEAD再执行已批准的指定SHA合并。当前技术迁移有界验收保持，版本仅原三组本地提交完成，额外commit/merge、双推、PR、最终CI/review未执行，外部服务未验证。状态为等待合法人工执行，不重复索取已有授权。


## 68. P6最终交付：双推/PR553/实际CI通过，待人工review；本阶段停止（2026-09-21）

### 技术迁移、版本交付、外部服务分别收口

技术迁移在已批准范围内通过，AC-01–AC-12保持逐项证据及覆盖边界；L1–L3增加最终原仓CI证据，L4仍是35技能身份复用+两份署名示例八维静态复核，未对新示例字节补跑模型；L5只复用已批准Windows CLI0.147.0 readOnly实际用例及未变原生保护身份，未宣称Desktop/workspace-write/Linux Codex宿主通过。U01/U02/U06真实服务/生命周期/EVAL依赖仍未满足或未测，U03真实凭据与OS写入未测，U04合法Owner人工执行不等于hook自动解锁，U05现由最终原仓push及PR CI实际证据闭合，U07原生消费者闭合保持。外部服务/L6未验证，不读取真实凭据、不连接业务服务、不执行解密、OS凭据写入或生产操作。

版本交付已完成获批提交、双推和PR创建，但未合并，生命周期不是completed。五个迁移侧提交依次为e5f99c87a50ad47856a41f40c2acccf75a5534da、1eb9257f15ee250b732f5db8a7f0b4266c0d2401、b2a730ddb4419cb39a767815f160115e02c2b575、a1abd1bbe7f8cc431f02bb970342c2a17f82737d、11e24377be7588d6d68564ab9b40fe0027ba3c1e；Owner在个人终端执行，Codex实施、准备及独立核验。最后一个提交父节点为a1abd1b与243b13f61ded1b2e398b346239305ea2a1be811a，仅同步获批setup-uv v10.1.0固定SHA一行，merge diff检查exit0；其他392个交付文件与97项删除保持。两端迁移分支均独立读取为11e24377be7588d6d68564ab9b40fe0027ba3c1e；未推送任一develop、未force、未删分支或worktree。

[PR #553](https://github.com/MJ-AgentLab/mj-agent/pull/553) 标题为infra: migrate to native Codex-only development，head为11e24377be7588d6d68564ab9b40fe0027ba3c1e，base明确develop / 243b13f61ded1b2e398b346239305ea2a1be811a。PR正文与发布用本地具名稿逐字核对一致，已关联当前Codex任务。相对当前base仍为原批准490路径，43项正式新文件完整，97项删除为既有81+16，无新增清理。817原生验收集合相对P5最终身份为797不变、17文档/示例、1获批政策行、1安全测试EOF-only、1获批setup-uv行；817不是完整提交清单。进入最终记录更新前暂存及已跟踪工作区均无差异；475未跟踪项全在原排除表（231候选、244历史材料），保留不清空。

### 实际CI与review

| 事件/检查 | 实际运行/提交 | 结论 |
|---|---|---|
| 最终原仓push CI | [35580906047](https://github.com/MJ-AgentLab/mj-agent/actions/runs/35580906047)，head11e24377 | SUCCESS |
| PR事件CI | [35582227660](https://github.com/MJ-AgentLab/mj-agent/actions/runs/35582227660)，head11e24377；实际Checkout日志为测试合并SHA d441fd2553b9b5ca9bd7eeffedf90afa6d33b288 | SUCCESS |
| PR Docker构建 | [35582227713](https://github.com/MJ-AgentLab/mj-agent/actions/runs/35582227713) | SUCCESS；不等于部署或业务服务验证 |
| 提交信息检查 | 35582227684 | SUCCESS |
| 文档陈旧检查 | 35582227673，既有warning mode | SUCCESS |

最终push和PR主测试日志均为977 passed、15 skipped、82 deselected、24 warnings；PR BDD为13 passed、7 skipped、48 warnings，离线契约64 passed。BDD七项skip明确属于既有SKIP_POLICY_EXTERNAL_DEPENDENCY（4项biz live永久不供pytest，3项无Owner批准的非biz profile），不是新增skip或外部服务通过。P5受控265测试+22子测试、零skip仍是独立覆盖域，不能混为全套CI计数。旧私有run35564875219@40b470320ef9cf073f0d18867ca6134fa95637d2仅保留清理前历史地位，不替代新证据。G3完整cached diff检查exit2的2161项历史补丁/Markdown空白诊断继续保留，未改写历史原文或下调检查配置；CI成功不将该检查失败改标通过。

GitHub当前OPEN、MERGEABLE、mergeStateStatus=BLOCKED、reviewDecision=REVIEW_REQUIRED，reviews为空。实际develop rules要求ci、strict同步、至少1审批、最后推送审批、review线程解决，且仅merge方式。所观察五个CheckRun均SUCCESS（含push及PR两次ci）；required ci已满足，但人工review条件仍未满足，不声称Ready to Merge，不自动merge或联系他人。PR测试合并SHA不是已合并提交，mergedAt仍null。

### 失败轨迹、恢复与停止

保留初始git commit被AskForApproval=Never拒绝的执行轨迹；后续Owner人工操作成功，不把旧BLOCKED覆盖新版本交付，也不声称Codex发布通道已解锁。读取PR期间出现GitHub连接重置、run-view/GraphQL/log TLS握手超时，随后同一路线只读查询/日志成功；实际Checkout日志证实测试SHA。没有通过修改工具、参数、编码、权限、hook/rules或创建批准凭证绕过。P6可选署名示例、政策行、EOF格式、上游CI行与各次记录都有原始备份和具名批准；所有旧记录字段/失败保留。

最终六记录为累计报告、asset-map.csv及p6/{final-check.json,acceptance.json,commit-groups.json,file-inventory.csv}。修改前字节备份为.mj-agent-local/p6-publication/final-closeout-before.zip，适用HEAD11e24377；本次新观测详见final-check.json的final_publication_observation，实际命令/环境/CI摘录/父提交/身份均绑定。六记录更新留在本地未暂存，不在已发布head内；不为同步收口叙述递归增加commit/push/CI。发布head的393文件工作SHA及97缺失路径先行保存，六记录修改后的当前身份另存本地closeout-record-hashes.json。旧field含旧head/状态时属于原采集快照，最终当前结论以本节和final_publication_observation为准。

HEAD恢复已提交迁移基线；P0–P4公共备份与后续增量、legacy-81-before.zip、consumer-six-before.zip、P6 before/additional/correction/policy和publication各具名备份继续保留。更早P3整组恢复须按后续增量适用顺序核对，不能直接套当前树。最终记录之前的发布head、同步前a1abd1b及G3工作字节ZIP均有明确用途；不reset/clean或清空候选。后续直接维护.agents及.codex原生资产，检查器、受控离线入口、Owner凭据/项目与hook信任边界按Onboarding §4/§6.4、根AGENTS及原生技能执行边界；新增受保护修改继续具名审阅。当前待后续人工review/merge决定，merge未获本轮授权。#499/#552、部署、分支/worktree清理均未执行。本轮更新累计记录后停止，仅完成P6。


## 69. PR553实际合并后的核对与具名同步方案（2026-09-21）

Owner报告PR已合并并要求继续后续工作，故本轮执行合并后审查，不重开P0–P6实现。GitHub实际state=MERGED，mergedAt=2026-09-21T09:30:14Z（台北17:30:14），mergeCommit=fc85d3cec66ef7a8ccec07aa1d0f09af10e828d8；父提交为243b13f61ded1b2e398b346239305ea2a1be811a和11e24377be7588d6d68564ab9b40fe0027ba3c1e。实际review字段仍REVIEW_REQUIRED且reviews=[]，不能推断人工Approve或合并途径；实际已合并状态不被旧BLOCKED覆盖。PR无closingIssuesReferences，未关闭#499/#552。

git fetch origin develop返回0后，核实origin/develop为fc85d3ce，且merge树与已验证发布head11e24377的树精确相同，既有push/PR CI证据按文件树身份复用，不重跑整套。合并SHA的run查询返回空，现有CI只匹配开发分支push及main/develop的PR事件，不把空结果解释为失败或新增成功。merge diff未涉及runtime SKILL/Prompt，EVAL backlog不触发。CHANGELOG已有Unreleased原生迁移条目，不重复改日志、不标发版/部署。未创建follow-up issue或automation。

现场：原迁移工作树HEAD仍11e24377，六份§68收口记录为未提交本地成果，暂存为空；不reset/clean。D:/workspace/10-software-project/projects/mj-agent/develop仍develop@20e2f24c352cf640d9dd33234b128ca897804b99，无已跟踪修改，存在唯一未跟踪plans/[PLAN]_Codex_Only_Development_Migration.md。该文件53324字节、SHA256 7dfad81dcf40d8cb867c7d9051907677eac85b6cbd2c9fb856a75f86c37d3728，与将合入的Git blob及原迁移计划逐字节相同。先备份保留，不删除/覆盖该原件；若Git快进拒绝同名未跟踪路径，停在拒绝处再核具体保留方案。Gitee/develop仍20e2f24c，属于已验证可快进祖先；两端迁移分支仍11e24377，没有自动删分支。

准备具名同步方案：本地develop仅ff到fc85d3ce；Gitee develop镜像仅ff到同SHA，使用既有sync-gitee-mirror.ps1守卫，前后确认source SHA、祖先关系和两端结果，不force、不推其他ref。此前批准仅覆盖迁移分支push，未涵盖develop镜像，此目标单独待Owner确认；原Codex出版路线仍未解锁，不通过脚本封装规避既有拒绝。实际新命令在Owner合法终端执行后核验，不预填成功。

迁移计划当前state仍draft，已完成任务与早期元数据不一致。按post-merge技能Step9不自动把draft改completed；已准备仅frontmatter三字段的准确补丁（updated:2026-09-21，state:completed，completed:2026-09-21），不伪造active中间历史、不批量重写正文，待Owner明确批准这份状态更正。新方案位于.mj-agent-local/post-merge-553/REVIEW.md及plan-completion-proposed.diff。六记录和计划、develop同名原件已先保存至before-postmerge-records.zip，包含原绝对身份/摘要；原所有P0–P6备份继续保留。

当前技术迁移验收有界通过；版本已真实合并到origin/develop，尚未完成本地develop及Gitee develop同步；计划元数据更正待批准；外部服务/L6仍未验证。六记录继续留本地未暂存，不额外commit/push/PR。未执行删除工作树/分支/候选/备份、生产部署、秘密或OS凭据操作、业务服务访问。读取中TLS超时保留，后续成功读取的合并与linked-issue事实优先。本轮完成可审阅方案后停在新增具名动作前。


## 70. 合并后具名动作获准；计划完成，快进遇同名文件保护（2026-09-21）

Owner对§69三项方案回复“授权，执行收尾”。执行前再次核实原迁移HEAD11e24377、origin/develop=fc85d3ce、Gitee/develop=20e2f24c以及本地develop原状态。仅在原迁移工作树应用已批准的计划frontmatter补丁：state completed、updated/completed均2026-09-21；原正文不变，准确SHA256为479c361990c354699831317c1856fa4d5cda4302fde014860d9690aca526c09a，与proposed完全一致，YAML元数据校验通过。此更正留本地未提交，远端已合并计划仍为原快照。

随后在真实develop工作树执行git merge --ff-only fc85d3cec66ef7a8ccec07aa1d0f09af10e828d8，Git进程exit1：未跟踪plans/[PLAN]_Codex_Only_Development_Migration.md会被覆盖，合并中止。HEAD仍20e2f24c，原件字节未变；这是工作树同名路径保护，不是新hook批准结论。按已批准方案的碰撞停点，没有自动删除、移动、reset/clean或换工具重试。Gitee/develop快进已获授权但尚未执行；Codex已知发布审批通道仍受prompt/Never限制，不通过镜像脚本封装绕过，后续走Owner个人终端并核验实际结果。

新增具名保留方案仅针对该53324字节原件：源为D:/workspace/10-software-project/projects/mj-agent/develop/plans/[PLAN]_Codex_Only_Development_Migration.md，目标为原迁移工作树.mj-agent-local/post-merge-553/preserved-develop-plan.md；目标目前不存在，源/目标绝对边界已核实，SHA256 7dfad81dcf40d8cb867c7d9051907677eac85b6cbd2c9fb856a75f86c37d3728与合入Git blob一致。原件已在before-postmerge-records.zip中备份。只有这项保留移动新增范围待确认；本地ff、Gitee镜像ff与计划更正批准继续有效，不重复索取。准确差异、影响、验证与恢复见PRESERVE-PLAN-REVIEW.md；移动后再执行同一条已批准快进命令，不删其他材料。

六记录本次更新前另保存before-authorized-execution-records.zip；当前累计六记录加计划共七份本地修改，均未暂存。技术迁移验收与实际PR合并保持，外部服务未测，develop本地/镜像同步仍待完成；不预填全部收尾成功。全部旧字段/失败与恢复源保留，未创建新提交、push、PR、issue或定时任务，未执行工作树/分支清理。


## 71. 同名原件保留与本地develop快进完成；待Gitee镜像执行（2026-09-21）

Owner明确批准§70的唯一新增保留移动。执行前以Resolve-Path核实源属于D:/workspace/10-software-project/projects/mj-agent/develop，目标属于原迁移工作树.mj-agent-local/post-merge-553，目标不存在；再次核实develop分支/HEAD20e2f24c和原件SHA256。用PowerShell原生Move-Item -LiteralPath保留到preserved-develop-plan.md，前后SHA均7dfad81dcf40d8cb867c7d9051907677eac85b6cbd2c9fb856a75f86c37d3728，没有其他移动或删除，原ZIP备份仍在。

在相同develop工作树重试原命令git merge --ff-only fc85d3cec66ef7a8ccec07aa1d0f09af10e828d8，exit0，实际Fast-forward。HEAD已为fc85d3ce，分支develop，完整status为空。保留原件与新提交plan Git blob逐字节一致；checkout工作文件按Git既有换行策略转换，规范化内容相同且无工作差异，不把换行转换当用户改动。本次是同步已合并提交，不在原迁移树重放P5删除。原迁移树的completed计划SHA保持479c3619…，其余未提交收口记录继续保留，暂存为空。

最新两端只读核对：origin/develop=fc85d3ce，gitee/develop仍20e2f24c。Gitee/develop快进授权继续有效，尚未执行；镜像脚本在原树/develop内字节一致。当前Codex已知push审批路线仍prompt/Never冲突，不通过外层脚本调用绕过；交Owner在个人终端执行既有pwsh -File ./scripts/sync-gitee-mirror.ps1 -Branch develop -Remote gitee -Source origin，再核对实际出口和远端SHA。只有该镜像动作未完成，不重复索取其范围批准。

本轮六记录更新前备份为before-ff-completion-records.zip；具名执行记录见local-develop-synced.json。技术迁移有界通过、PR553已合并、本地develop已同步；Gitee基线待同步，外部服务仍未验证。计划completed及累计六记录共七份修改留在原迁移工作树本地未暂存，不增加发布提交。没有清理任何分支、工作树、候选或备份，不创建新PR/Issue或定时任务。


## 72. Gitee镜像已核实；已授权合并后收尾完成并停止（2026-09-21）

Owner在个人终端执行已批准的既有镜像守卫脚本pwsh -File ./scripts/sync-gitee-mirror.ps1 -Branch develop -Remote gitee -Source origin，输出从20e2f24向fc85d3ce快进8提交并报告OK。随后独立git ls-remote逐端读取origin/develop和gitee/develop，均exit0且精确为fc85d3cec66ef7a8ccec07aa1d0f09af10e828d8；本地develop同SHA，完整工作区status为空。未force、未修改其他ref；原迁移分支/worktree仍保留在11e24377，未清理。

技术迁移：原有有界验收通过，最终push CI35580906047与PR CI35582227660结果继续有效；合并fc85d3ce文件树与验证head11e24377相同，不无故重跑测试或派发CI。版本交付：PR553真实已合并，本地develop/GitHub develop/Gitee develop三端一致，具名同步动作已完成。外部服务：L6依然未测；没有生产部署、业务访问、真实凭据读取/解密/OS写入或个人信任操作。

计划state:completed、updated/completed:2026-09-21已按Owner明确批准修正，精确SHA479c361990c354699831317c1856fa4d5cda4302fde014860d9690aca526c09a保持；该修正仅在原迁移工作树本地。已合并提交中的计划仍是原draft快照，不把本地改动声称为远端内容。累计报告、资产表及p6/{final-check.json,acceptance.json,commit-groups.json,file-inventory.csv}六记录，加上述计划，共七个未暂存本地修改，未新建提交、push或PR；后续若要发布这些收口记录，需要独立文档交付流程，本轮不递归扩展。当前待执行的已授权收尾动作已清零。

具名保留的develop原计划位于.mj-agent-local/post-merge-553/preserved-develop-plan.md，SHA7dfad81d…与合并Git blob一致；所有原P0–P6公共备份/增量、legacy-81-before.zip、consumer-six-before.zip、P6和post-merge具名归档继续保留。六记录本轮改写前连同已更正计划备份至before-mirror-final-records.zip；实际最终状态见同目录final-completion.json及final-check.json的postmerge_final_observation。旧字段和拒绝/网络失败/同名文件保护轨迹保留，不用旧失败覆盖后续真实完成。

本轮没有删除工作树、分支、候选、临时验收副本或备份；没有关闭#499/#552、创建后续Issue、定时任务或部署。后续日常开发可从已同步develop创建合规worktree，直接维护.agents与.codex，受保护修改仍需具名Owner决定。按当前授权范围完成收尾并停止。
