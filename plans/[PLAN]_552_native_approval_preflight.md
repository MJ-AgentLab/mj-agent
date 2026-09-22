---
type: plan
summary: Issue 552 原生 Codex 交付审批兼容性预检
owner: 项目负责人
created: 2026-09-22
updated: 2026-09-22
state: active
track: shared
---

# Issue 552 原生审批预检

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
