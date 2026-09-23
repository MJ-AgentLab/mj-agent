---
type: plan
summary: Issue 552 原生 Codex 交付审批兼容性预检
owner: 项目负责人
created: 2026-09-22
updated: 2026-09-23
state: completed
completed: 2026-09-22
track: shared
---

# Issue 552 原生审批预检

> §1–§8 保留 PR #556 的实施时点记录；其中 Git `prompt`、统一 `never` 不兼容和旧返回码是历史行为。当前语义与逐项收尾结论见 §9，以 ADR-040、ADR-041 和已合并 PR #561 为准。`completed: 2026-09-22` 对应 #556 实施合并日，不表示 #552 已关闭、收尾文档已提交或 #555 真实链路已验收。

## 1 关联与执行范围

Owner 请求「解决 issue 552」并继续执行。本轮完成诊断脚本、离线回归和文档；提交、推送、PR、关闭 issue、原分支交付及个人配置变更不在本轮执行范围。

基线 develop `6055f23`；工作树 `maintain/552-native-approval-preflight`。旧工作树 `maintain/552-codex-approval-preflight` 的六项未提交成果保留原样，仅作历史参考。

## 2 现状与仓库扫描

[#552](https://github.com/MJ-AgentLab/mj-agent/issues/552) 的诊断目标仍成立，实施载体须按 ADR-040 更新。旧 agents_sync/typed-source 已退役；当前 `scripts/sdd/check_codex_native.py` 已有 approval_status 和原生 enforcement 静态校验。它本身属于受保护检查器，不在本轮修改范围。

新入口 `scripts/check_codex_approvals.py` 是普通只读开发诊断，导入现有原生检查函数。它不执行命令、不作为门禁、不改变规则或 hook。逐项报告 commit、Gitee push、origin push、PR create 的规则来源、有效模式及审批状态。

八维核查：开发脚本/测试/指南受影响；业务模块、API/Studio、biz 数据流、biz/memory 数据库、部署配置均不变，n8n 不适用。反扫 approval/审批/on-request/never 命中现有原生测试；两份交付入口指南缺少本 issue 所需指引。无重命名、移动、catalog 或 runtime canonical 改动。

## 3 实施顺序与行为

1. 在已 tracked 的 `tests/unit/test_codex_native.py` 增加回归，使用临时项目 fixture，先记录 RED。
2. 新增 stdlib 诊断入口，复用原生检查器；模式只接受调用者实际观察值，省略即 UNKNOWN。未知输入不从项目/用户配置推断。
3. 原生规则/钩子缺失、间接路径或校验失败时诊断 UNKNOWN；有效规则下 never 为 INCOMPATIBLE，on-request 为 APPROVAL_REQUIRED，未知为 UNKNOWN。后者不等于 Owner 批准或宿主 hook 可执行。
4. 返回码：0=仍需批准；1=模式不兼容；2=未知/输入无效。输出另外标注 Owner、实际宿主和远端认证未验证。
5. 更新 Git GUIDE 的提交前预检/恢复流程，Onboarding 加入口；验收与限制记录于本计划。

## 4 Documentation Decision

| Type | Action | Path / 理由 |
| --- | --- | --- |
| Plan | Create | 本文件，记录迁移后实施与 AC 映射 |
| SPEC | None | 内部只读诊断 CLI，由 GUIDE 描述 |
| ADR | None | 遵守 ADR-040，不改治理设计 |
| RUNBOOK | None | 恢复步骤并入 Git GUIDE |
| GUIDE | Update | Developer Onboarding / Git Push Workflow |
| STANDARD | None | 不改规范 |
| Local ISSUE | None | GitHub #552 已承载问题 |
| ASSESSMENT | None | 无性能/架构评估 |
| CHANGELOG | None | 无应用行为或版本变化 |
| INDEX | None | 无 canonical 文档新增、移动 |

## 5 风险与恢复

风险 Medium，风味 C。静态项目规则不能证明全部活动规则、项目受信任或宿主可请求批准；显式输出这些未验证项。on-request 仅为模式兼容，原生 hook 仍可能返回 OWNER_APPROVAL_REQUIRED/BLOCKED_EXECUTION_ROUTE。禁止更换工具、移除规则或生成凭证绕过拒绝。

不读用户配置、环境凭据或转录；不连接服务。恢复仅涉及本轮新脚本/计划与既有测试/两指南的 diff，原文件可由本分支基线恢复；不对旧 #552 工作树做恢复或清理。

## 6 验证方案

- 项目受控 offline runner 运行 `tests/unit/test_codex_native.py`；新增用例覆盖三种模式、两远端及 PR、无效/缺失规则、只读边界、CLI 返回码。
- 独立 `codex execpolicy check` 重放 Gitee/origin push 和 PR create，只计算规则，不执行动作。
- 原生 all/enforcement 检查替代旧 AC-4 的 agents_sync；检查既有禁止规则与受保护文件 diff 为零。
- ruff、mypy、frontmatter、wikilinks 和指南语义静态审阅。
- 当前会话 never 可作已知输入；on-request 只是测试输入。Desktop 审批切换、覆盖来源、真实 push/PR 未验证，不以离线结果替代。

## 7 验收映射

- AC-1：逐命令状态/来源/模式与 never/on-request/unknown 离线回归。
- AC-2：Gitee/origin/PR 示例与真实 CLI 无副作用规则重放；远端认证 NOT_TESTED。
- AC-3：恢复指南、来源链接及受控手工诊断；真实会话恢复另记未验证。
- AC-4：按 ADR-040 原生资产单一来源，保留既有禁令；不再运行已退役生成器。

## 8 执行记录

### 本地验证（2026-09-22）

- TDD：首批 10 项回归因诊断模块缺失全部 RED，实现后 10/10 GREEN；再补间接输入和真实 CLI 入口的 4 项边界用例。受控 runner 完整运行 `tests/unit/test_codex_native.py`：62 passed，0 skipped，6.00s。无直接 pytest、凭据读取或外部服务连接。
- 新工作树通过 `UV_PROJECT_ENVIRONMENT` 复用 develop 已有虚拟环境；全部 uv 命令带 `--frozen --no-sync`，没有安装/同步依赖。
- `ruff check` 全仓通过；`mypy src/mj_agent`：48 source files 无错误。
- 原生 all/enforcement 检查各自 `STATIC_PASS`，会话 never 各自正确显示 `INCOMPATIBLE`。这两个结果不能相互替代。
- 本机 `codex-cli 0.147.0` 实际执行三条 `execpolicy check`：Gitee/origin push、PR create 顶层 decision 均为 prompt；未启动对应交付动作。CLI 帮助确认 on-request/workspace-write 启动参数存在。
- 新诊断 CLI 手工重放：当前观察到的 never = INCOMPATIBLE / exit 1；on-request 测试输入 = APPROVAL_REQUIRED / exit 0；省略模式 = UNKNOWN / exit 2。每次均列出四项命令、规则来源及未验证层。on-request 重放不表示本会话切换成功。
- frontmatter：143 canonical docs 全通过；wikilinks：0 archive-ref violations，5 个根文件 0 unresolved。该工具不覆盖两份 GUIDE 的全部 Markdown 链接；本轮新增的两条本地链接另逐一核对目标存在，Onboarding 小节锚与标题匹配。
- GUIDE 手工语义验收：三层区别、danger-full-access、覆盖来源、CLI/桌面证据区分、Owner 恢复操作、hook 硬阻断、真实恢复未验证均有对应说明；依据官方 Rules/Config basics 页面及本机帮助。OB 格式/标题/路径经静态审阅，未渲染网页。
- `git diff --check` 通过。受保护目录与 `scripts/sdd` 的 diff 为空；develop 工作树仍干净，旧 #552 工作树仍为原六项未提交集合。未暂存、commit、push、建 PR 或关闭 issue。

### AI 自检与完成边界

五文件分别映射脚本、测试、两 GUIDE、本计划；无 scope drift、无新依赖。AC-1/2 的诊断与回归、AC-3 的操作说明、AC-4 的原生等价检查完成。Desktop 为何曾有效 never、实际审批弹窗/会话切换、原分支真实交付仍未验证，原 issue 不据此自动关闭。撤销入口为本轮五文件 diff 与基线 `6055f23`；旧工作树成果不属于此恢复范围。

Codex 实施；HITL 受保护面变更=NONE；BDD 行为契约不变，TDD=14 项新增诊断回归；Subagent dispatched=NONE。发布动作仍须 Owner 的具体指令和合法执行路线。

## 9 收尾核对（2026-09-23）

### 9.1 合并与基线证据

- [PR #556](https://github.com/MJ-AgentLab/mj-agent/pull/556)：MERGED，2026-09-22 02:23:45 UTC；head `75fb7db1cb762e8c09491454cca20d12ab73060a`，merge `7446e731649c2577c6246d57bbfdccc2d91e780e`，base `develop`。交付只读预检、14 项新增回归、两份 GUIDE 和本计划。
- [PR #561](https://github.com/MJ-AgentLab/mj-agent/pull/561)：MERGED，2026-09-22 08:28:22 UTC；head `5177274a03dc1214a3e9d730d046fed7bdaffdb5`，merge `8a029e7bb3f29af4bd510b916e6bafbeaaf4b074`，base `develop`。按 [ADR-041](../decisions/ADR-041_Command_Specific_Git_Execution_Policy.md) 定向替代 Git/gh 项目规则及相应诊断语义。
- 核对时本地 `develop`、origin/develop、gitee/develop 均为 `8a029e7bb3f29af4bd510b916e6bafbeaaf4b074`，包含上述两个 merge；develop 工作树干净。
- `documentation/552-closeout` 原 HEAD 为 `7446e73`，唯一未提交内容是本计划 `active → completed` 与 `completed: 2026-09-22`。已备份原文件/diff，并快进到 `8a029e7`；同步不产生新提交、不覆盖原改动。本次只更新该计划的日期、历史说明与收尾证据。

### 9.2 #552 验收逐项结论

| 目标 | 已合并实现及现行替代 | 验收边界 |
| --- | --- | --- |
| AC-1：`prompt + never`、命令/来源/有效模式及未知输入 | #556 已实现只读诊断及三模式回归；#561 改为 `session_approval=PER_COMMAND`。现行 Git/gh 无项目规则匹配，不能仅因 never 判不兼容；保留的 Remove-Item prompt 在 never/on-request/unknown 下分别为 INCOMPATIBLE/APPROVAL_REQUIRED/UNKNOWN | 模式未知仍明确输出 unknown / mode_source=UNKNOWN；Git 的 NO_PROJECT_RULE_REQUIREMENT 只说明文件层无要求，不是会话 PASS。规则缺失/损坏仍 UNKNOWN；离线覆盖见 `tests/unit/test_codex_native.py`、`tests/unit/test_git_command_policy.py` |
| AC-2：Gitee push、origin push、PR create 及认证分层 | #556 已覆盖三类命令并保留当时的 prompt 重放记录；#561 移除 Git/gh 六条 rules，当前三个命令的项目规则重放为无匹配，原来要求三项 prompt 的预期被替代 | 规则重放不执行传入命令；on-request 不是动作批准。预检的 remote_authentication=NOT_TESTED，不替代真实推送或 PR 验收 |
| AC-3：可操作恢复指引与 Owner HITL | #556 已补两份 GUIDE；#561 更新为具体命令、有效模式/来源、实际加载规则和已知拒绝来源分别核验。Owner 授权继续绑定动作/对象；danger-full-access 不代表批准，规则文件改变不代表会话已加载或历史拒绝已解除 | 原先统一要求 Git 切换 on-request 的恢复路线被 ADR-041 替代。Desktop 历史覆盖来源、受控会话加载/审批及完整真实交付仍未验证，由 #555 继续承载 |
| AC-4：单一来源与禁止规则 | [ADR-040](../decisions/ADR-040_Codex_Only_Development.md) 已将 agents_sync/typed-source 投影迁为原生直接维护；#556 使用原生 all/enforcement 校验。#561/ADR-041 又经审阅移除 Git/gh 三条 prompt 与三条 forbidden，保留 Remove-Item prompt 和三条数据库 forbidden | 不运行退役生成器，不恢复旧规则以满足历史断言；G1/G2、人工 merge、秘密/数据/受保护编辑边界继续由政策与有限 hook 承担。静态校验不能证明宿主实际拦截 |

现行入口：[Git Push Workflow §0.1–§0.2](../docs/infrastructure/git/[GUIDE]_Git_Push_Workflow.md)、[Developer Onboarding §4.1/§6.6](../docs/guide/[GUIDE]_Developer_Onboarding.md)。本次不修改规则、hook、个人配置、信任、凭据或任何运行时文件。

### 9.3 #555 保留的真实执行验收

[#555](https://github.com/MJ-AgentLab/mj-agent/issues/555) 核对时为 OPEN；本次不关闭、不勾选其 AC。PR #561 明确将 AC-4/9/13/24 的受控真实链路留待验收：

- AC-4：临时对象上的本地 Git 清理与 Remove-Item，逐命令记录实际执行条件与结果。
- AC-9：另行批准的测试对象上，commit → Gitee/origin 双推 → 显式 base 的 PR，记录提交/两端 SHA、PR URL/head/base 及宿主审批或拒绝事实。
- AC-13：独立批准的临时远端引用删除，逐端逐 ref 查询与部分完成恢复证据。
- AC-24：新规则下 never 场景的目标会话加载证据及上述动作真实结果；旧规则下成功、已合并 PR 和静态预检均不能代替。

因此 #552 收尾范围为已交付诊断、指南与被正式替代的旧验收方式；不宣称发布/删除全链路恢复，也不把原分支交付或 Desktop 历史覆盖原因调查记为完成。

### 9.4 旧工作树成果归属与保留

归属：#552 在 ADR-040 原生迁移前的实施草稿，保管/后续取舍由 Owner 决定；不属于 #555 清理对象，也不属于本次待提交文件集。旧分支 `maintain/552-codex-approval-preflight`，HEAD `20e2f24c352cf640d9dd33234b128ca897804b99`；绝对路径 `D:/workspace/10-software-project/projects/mj-agent/maintain/552-codex-approval-preflight`。

| Git 状态 | 相对旧工作树路径 |
| --- | --- |
| tracked，未暂存修改 | `docs/guide/[GUIDE]_Developer_Onboarding.md` |
| tracked，未暂存修改 | `docs/infrastructure/git/[GUIDE]_Git_Push_Workflow.md` |
| tracked，未暂存修改 | `scripts/sdd/agents_sync.py` |
| tracked，未暂存修改 | `tests/unit/test_codex_enforcement_d1a.py` |
| tracked，未暂存修改 | `tests/unit/test_sdd_development_agent.py` |
| untracked | `plans/[PLAN]_552_codex_approval_preflight.md` |

五项 tracked diff 合计 310 insertions / 18 deletions；另有一份 untracked 计划。六文件已登记 SHA-256 供本次前后核对，原内容保持原地；工作树、分支及其中其他内容一并保留，不删除、归档、迁移、覆盖或并入本次提交。旧工作树 HEAD 不是未提交内容的备份。

### 9.5 本轮验证与交付状态

以下为本轮在 `documentation/552-closeout` / `8a029e7` 上的实际结果；uv 均使用 `--frozen --no-sync`，通过 `UV_PROJECT_ENVIRONMENT` 复用 develop 既有 `.venv`，未安装依赖。

| 检查 | 实际结果 |
| --- | --- |
| `python scripts/sdd/run_offline_pytest.py tests/unit/test_codex_native.py tests/unit/test_git_command_policy.py -q` | 135 passed，0 skipped，6.90s，exit 0 |
| `python scripts/sdd/check_codex_native.py --surface all --effective-approval-policy never` 与 `--surface enforcement` | 两项 STATIC_PASS / exit 0；PER_COMMAND，rule_loading=UNKNOWN，host_enforcement=NOT_TESTED |
| `python scripts/check_codex_approvals.py --effective-approval-policy <mode> --action commit --action push --action pr_create` | never/on-request/unknown 三组均为 4 项 NO_PROJECT_RULE_REQUIREMENT / exit 0；unknown 保持 mode_source=UNKNOWN |
| 同一 CLI `--action local_delete` 三模式 | 只有 Remove-Item 分别 INCOMPATIBLE/APPROVAL_REQUIRED/UNKNOWN，exit 1/0/2；两项 Git 本地清理仍无项目规则要求。均为只读示例诊断，未删除对象 |
| `codex execpolicy check --rules .codex/rules/mj-agent.rules --pretty` 重放 Gitee/origin push 与 PR create | CLI 0.147.0，三项 `matchedRules: []` / exit 0；不执行传入动作，不称为 host ALLOW |
| `python scripts/check_frontmatter.py` | 146 篇通过，exit 0；包含本 working Plan |
| `python scripts/check_wikilinks.py` | 0 archive-ref violations；5 个根入口 0 unresolved，exit 0；不代表全部 Markdown 链接覆盖 |
| 本文件新增本地链接、历史/现行说明、范围与 `git diff --check` | 静态核对；A1–A4/OB2–OB5 通过，OB1 无 Plan 长度阈值，未做网页渲染；A5/A6 无 INDEX/入口同步需求，A7–A14 无对应文件改动 |

never 来源为本任务已提供的有效模式；on-request/unknown 仅为回归输入，不表示切换会话。所有预检均保留 rule_loading=UNKNOWN、owner_approval=NOT_ASSESSED、host_enforcement=NOT_TESTED、remote_authentication=NOT_TESTED。本次远端只读查询成功仅证明对应读取可用，不证明 push 写权限。未跑应用 lint/mypy、全仓 pytest、live probe 或发布/删除验收；本次仅改一份文档，已用相关回归验证结论，不扩大到运行时测试。

收尾仅涉及 working Plan，路径不变，不需要 canonical INDEX、CHANGELOG 或 EVAL backlog。Codex 实施；受保护面变更=NONE；BDD/TDD=无行为变更，复用现有离线回归；Subagent dispatched=NONE。

收尾文档发布状态单独核对：本节准备时 UNCOMMITTED；commit、双端普通 push、PR 创建等待 Owner 对具体结果拍板，PR base 为 develop，merge 由 Owner 人工处理。#552 的评论和关闭已有本任务条件授权，必须先确认收尾 PR 已合并，再发布逐项结论/证据并关闭；#555 及旧工作树保持独立。
