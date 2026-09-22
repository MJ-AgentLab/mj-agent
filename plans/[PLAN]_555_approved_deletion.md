---
type: plan
summary: 删除与 Git 发布的动作级授权、只读核验、有限 hook 路由及部分完成恢复
owner: ranzuozhou
created: 2026-09-22
updated: 2026-09-22
state: active
track: engineering-workflow
---

# [PLAN] Issue 555 已批准删除与 Git 发布流程

> Issue: [#555](https://github.com/MJ-AgentLab/mj-agent/issues/555)
> 关联: [#552](https://github.com/MJ-AgentLab/mj-agent/issues/552)
> 状态：Owner 首次回复“实施”批准7文件方案，后要求按更新后的 Issue 继续实施，并明确批准 proposed-git-hook.diff 及说明同步。§1–§8 保留首次方案/验证的历史记录，当前范围与结果以 §9 为准。真实 on-request 宿主验收未完成，计划保持 active；本文件不是授权凭证。

## 1. Repo Scan Result 与证据

- Decision: Need HITL。Risk: High，命中 mcp-server-trust-posture-change 及政策元规则。
- develop、origin/develop 本地引用与本工作树起点均为 `6055f23e11f4b47fcf0836bd4ebf4a8e274e9230`；没有把本地远端跟踪引用描述为已重新 fetch 的远端状态。
- 工作树：`D:/workspace/10-software-project/projects/mj-agent/maintain/555-approved-deletion`；分支 `maintain/555-approved-deletion`。通过 `git worktree add` 创建，原 develop 工作区干净。
- 当前有效会话：`approval_policy=never`，`sandbox_mode=danger-full-access`（来自会话权限声明）。Desktop 内嵌引擎版本及 hook 实际加载状态未验证。
- 没有执行任何实际清理，没有重试历史失败命令，没有读取秘密或个人配置。

| 维度 | 当前事实 / 依据 | 影响 |
|---|---|---|
| 业务模块 / API / Studio | Issue 明确排除业务改动；目标文件集中于开发治理 | 无 runtime 代码修改 |
| biz_catalog / biz 数据流 | 未涉及业务对象 | 不访问数据库，不运行 schema probe |
| memory / 数据库 | 不涉及 schema 或存储生命周期 | 无 migration |
| 配置 / 环境 | `.codex/rules/mj-agent.rules` 现有 9 条规则；删除无独立 prefix rule | 拟增加具名删除命令 prompt，保留全部既有规则 |
| hook | `scripts/sdd/codex_hook_guard.py::classify` 单条 Remove-Item 落入末尾 ALLOW；复合命令 UNKNOWN；受保护编辑 OWNER_APPROVAL_REQUIRED；main 将非 ALLOW 输出 block | 不能把“所有删除必被 hook 阻断”当事实；不修改 UNKNOWN/FORBIDDEN 的阻断 |
| 检查器 / 测试 | `check_codex_native.py::approval_status` 已覆盖 never/on-request/unknown；规则集合精确匹配 | 扩展现有集合和回归，不另造审批体系 |
| 文档 | 政策 §4 执行机制、共用边界 §授权与硬阻断第4条、git-delete 概述及目录残留示例 | 存在重复确认和预设人工处理的直接消费者 |
| 架构 / 契约 | ADR-040 第4点已区分 Owner、工具规则、有效宿主权限；冻结契约仅锁8项 infra 技能 | 不改 ADR，不改冻结技能及契约；本轮不命中 declared-contract-change |

反向检索：`rg -n 'hook.*block|需手动|每个关键节点|人工删除|执行路线未人工' AGENTS.md policies/ai-agent.md .agents/references .agents/skills docs/guide/`。直接修订对象见 §3；历史 plans/archive 不机械重写。无函数重命名、路径迁移、SQL对象改名、runtime canonical 或 catalog 漂移。

## 2. Scope 与行为决定

### In-scope

1. 当前任务中对具体目标、动作和已知内容的明确批准复用；不重复索取批准或额外理由。
2. 新增只读删除核验工具；记录目标身份和内容状态，比较执行前变化，逐项返回可继续、暂停或已不存在。
3. 明确单条正常工具删除由宿主危险命令检查及审批处理。hook 不认证聊天，不读取 transcript，不消费自建授权凭证。
4. 回归保护当前单条命令与 UNKNOWN/FORBIDDEN 的差异；同步删除 prompt 规则及精确检查器。
5. 错误诊断保存原始错误；已知证据才归因；通用 blocked by policy 标 UNKNOWN_LAYER。

### Out-of-scope

原 develop 的真实清理、其他 worktree、真实资料备份移动、停止未知进程、个人配置/信任/hook激活、MCP变更、Docker、CI blocking gate、依赖升级、通用授权令牌，以及 commit/push/PR/merge。文件核验结果不能替代 Owner 授权，也不能解锁工具审批。

## 3. 具体文件与任务拆解

### 3.1 规则及直接消费者（C：开发治理）

具体文字差异见 [proposed-policy.diff](../evidence/issue-555/proposed-policy.diff)，本轮获批准后已正常应用；GUIDE另补已实现CLI的具体用法。该差异作为历史审阅依据保存，不应重新应用。原始带上下文补丁的准确字节另存本地恢复目录，仓内版本改为等价零上下文格式以避免补丁内容自身触发trailing-whitespace检查；没有改变获批的7文件差异。

| 文件 | 拟修改 |
|---|---|
| `AGENTS.md` | 补具名清单授权复用、前置核验、实际拒绝后按证据定位 |
| `policies/ai-agent.md` §4 执行机制 | 删除 blanket 的“需审批即 hook 永久 block”解释；保留具体批准、实际技术拒绝不得绕过 |
| `.agents/references/execution-boundaries.md` | 删除复用条件、目标差异暂停、未知错误不归因、备份/占用及路径边界 |
| `.agents/skills/mj-agent-git-delete/SKILL.md` | Step 1 已有明确范围时直接复用；H1/H4 按差异暂停；去掉“目录残留需手动”预设；force/远端删除仍须动作级批准 |
| `docs/guide/[GUIDE]_Developer_Onboarding.md` §6.5 | 增补正常执行顺序、never/on-request/unknown矩阵和实际拒绝诊断 |
| `.codex/rules/mj-agent.rules` | 仅新增 `Remove-Item` 命令族 prompt；不增加 allow、不削弱已有 forbidden/prompt |
| `scripts/sdd/check_codex_native.py` | RULES 精确集合同步新增规则；复用现有有效模式诊断 |

本次无需修改 `.codex/hooks.json`、hook launcher 或 `codex_hook_guard.py` 的放行逻辑：单条正常删除已不被 blanket block。用新增测试固定该事实；未知/复合命令继续阻断。不能为了让复合命令通过而改成全部 ALLOW，也不能在实际拒绝后改写命令再试。执行前即选择单项正常原生命令，不把预检脚本做成隐藏删除执行器。

新增 prefix rule 在真实 PowerShell 载体的匹配行为须通过正常宿主实测；静态规则重放不能证明 Desktop 能分解或匹配 shell cmdlet。若正常宿主未按预期处理，保留未验证并提交具体后续差异，不临时扩展 rule 或换执行载体。

### 3.2 只读前置核验（A：纯代码；新文件）

新增 `scripts/sdd/check_deletion_targets.py`，仅输出核验数据，不删除、不移动、不结束进程、不更改权限。

输入为显式工作树根、具名目标及先前核验快照；快照只是比较基线，不是授权 receipt。Owner 批准、撤销及动作范围由当前任务单独记录。

- 路径：要求绝对路径；拒绝根目录、工作树根、`.git`、路径逃逸、其他 worktree、通配/设备路径等非普通目标；逐层 lstat 检查祖先、目标及后代，不跟随 symlink/junction/reparse point。未知重解析标签暂停。
- Git：记录根及 HEAD、tracked/untracked/ignored、staged/unstaged 状态；检查目录内全部成员，不能只看 git tracked 集合。失败不能当空集合。
- 内容：记录普通非秘密文件的身份、大小及摘要与成员集合；执行前比较内容新增、修改、路径替换和根身份变化。秘密路径只记录禁止状态，不打开、不哈希、不输出内容。
- 备份：需要备份的 dirty/untracked/ignored 内容无经核验恢复来源时暂停；显式批准丢弃已审阅内容可由会话记录说明，工具不推断批准。核验不创建或移动真实备份。
- 占用：Windows 用受控临时文件验证检测方法；不能以能读文件证明可删。无法可靠检测删除共享/占用时返回 UNKNOWN，不报告可删；不杀进程。文件系统并发变化无法由一次扫描消除，删除紧前重检，异常立即停止受影响项。
- 状态：逐项目输出 READY_FOR_REVIEW / CHANGED / OUT_OF_SCOPE / REPARSE_POINT / SECRET_BOUNDARY / BACKUP_REQUIRED / IN_USE / UNKNOWN / ALREADY_ABSENT 等具名结果；没有“已获授权”状态。
- 错误：分类显式 hook decision、prompt+never、文件占用/权限及证据不足的 UNKNOWN_LAYER；保存正常工具原始错误，不回显凭据。

### 3.3 回归（A：先红后绿）

新增 `tests/unit/test_deletion_targets.py`，并扩展 `test_codex_native.py`、`test_native_governance.py`。不修改离线 runner 保护或测试配置。

| AC | 可自动验证 | 必须单独记录 |
|---|---|---|
| AC-1 | 文本一致性、没有“逐节点重复确认/残留必人工”旧断言 | 受控会话确实复用同一具体批准 |
| AC-2 | 临时Git库内 tracked/dirty/untracked/ignored、逃逸、junction、占用和备份失败 | 真实资料不参与夹具 |
| AC-3 | 内容变更、路径替换、成员新增、其他worktree、部分成功/已缺失 | 会话授权撤销及范围扩大，只暂停受影响项 |
| AC-4 | 规则重放只能证明 prompt decision | 真实 on-request 会话、版本、工具请求、审批及删除后的实际结果 |
| AC-5 | 已知/未知错误样本不误归因 | 实际拒绝原始错误，不换载体重试 |
| AC-6 | 单条删除现有行为、UNKNOWN/FORBIDDEN仍block、既有秘密/G1/G2/Owner边界不退化、3类原生检查 | 宿主实际加载另记 |
| AC-7 | never/on-request/unknown矩阵；项目授权不由快照或mode推定 | 当前never不能冒充on-request验证 |

BDD/TDD：用离线临时Git库及受控占用场景观察失败，再实现核验；不新增业务BDD或runtime EVAL。测试夹具表示输入场景，不能作为真实授权。

### 3.4 Documentation Decision

| Type | Action | Path | Existing Target | Reason | Evidence | Template Notes | Required Before |
|---|---|---|---|---|---|---|---|
| Plan | Create | 本文件 | 无555计划 | 高风险范围/AC/批准锚点 | Issue、本次scan | TEMPLATE_PLAN已存在；使用draft | 实施 |
| SPEC | None | — | — | 无业务接口/跨capability契约变化；辅助CLI契约在计划和测试明确 | §3.2 | 不新建重复文档 | — |
| ADR | None | — | ADR-040 | 沿用三层分离及无receipt决定 | ADR-040第4点 | 历史记录保持 | — |
| RUNBOOK | None | — | Onboarding §6.5 | 恢复说明纳入同一开发入口 | 现有GUIDE | 不再建平行入口 | — |
| GUIDE | Update | docs/guide/[GUIDE]_Developer_Onboarding.md | §6.5 | 正常审批及诊断 | scan | 保留结构/更新元数据 | PR |
| STANDARD | None | — | policies/ai-agent.md | 直接更新已有政策载体，非新增STANDARD | §4执行机制 | 政策更新须Owner | 实施 |
| Local ISSUE | None | — | GitHub #555 | 已有长期追踪锚 | Issue | 不重复开单 | — |
| ASSESSMENT | None | — | — | 无性能基线评估 | scope | — | — |
| CHANGELOG | None | — | CHANGELOG.md | 开发治理维护，不改产品运行行为 | scope | 发布时依项目要求复核 | — |
| INDEX | None | — | docs/INDEX.md | 无新增canonical文档/移动路径 | 文件清单 | Plan为working文档 | — |

根入口、共用边界、技能和规则是直接消费者，已在§3.1显式列出，不漏入文档矩阵之外。

## 4. 执行顺序与批准范围

1. Owner 审阅本方案及具名差异，批准§3.1保护面和§3.2–3.3实现范围。
2. 写失败回归，正常工具修改已批准文件，运行离线验证。任何实际拒绝原样记录；批准不构成绕过许可。
3. 核对完整diff与直接消费者；无新增冻结契约/infra技能变化，否则单列新增范围。
4. 工程师在正常配置流程准备有效on-request会话并核实引擎版本与规则加载。Codex不改个人配置或自动信任。
5. 当前任务明确批准具名临时清单后，按同一正常工具执行受控验收；如宿主要求审批，使用其正常审批流程。逐项验证结果并登记AC。
6. 未有真实on-request证据则AC-4和AC-7宿主部分保持未验证，Issue不得宣称已完全解决。

commit/push/PR/merge、原清理任务和真实数据不包含在本实施批准中。

## 5. Risk Control 与恢复

| 风险 | 控制 / 恢复 |
|---|---|
| 把核验数据当授权 | 快照不提供授权字段；不交hook作为自动放行凭据；会话决定单独记录 |
| 删除越界/链接/竞态 | 检查祖先及成员，执行紧前复核；未知暂停；绝不以“无未提交文件”推断安全 |
| 秘密或有价值ignored内容被读取/丢弃 | 不读秘密；其他内容逐项核验与备份条件；本Issue不删除真实资料 |
| hook变成宽泛allow | 保持现有分类和block；补正反例；不支持payload继续UNKNOWN |
| 静态规则通过冒充宿主成功 | STATIC_PASS、授权、模式、实际加载和结果分别记录 |
| 与#552并行工作冲突 | 不读取/复制其他worktree未提交实现，仅复用本基线已合入的approval_status；未来合入变化重新比对 |

恢复来源：实施前保存将修改文件的准确字节与身份；已提交基线可从 `6055f23` 读取，本轮草案另行保留。恢复只针对具名文件，不执行全仓reset/clean，不把Git当未提交内容/真实数据备份。新增文件仅在独立授权后删除。

## 6. Verification 与本次结果

2026-09-22，在未修改实现的develop基线实际执行：

- `uv run --frozen --no-sync python scripts/sdd/run_offline_pytest.py tests/unit/test_codex_native.py tests/unit/test_native_governance.py tests/unit/test_native_skill_contracts.py -q`：**81 passed in 6.55s**，exit 0。
- 现有`.venv/Scripts/python.exe`执行`check_codex_native.py --effective-approval-policy never`：config STATIC_PASS；session_approval INCOMPATIBLE；owner_approval NOT_ASSESSED；host_enforcement NOT_TESTED，exit 0。exit 0不是宿主可执行证明。
- 同解释器执行`check_native_skills.py`：STATIC_PASS，exit 0。
- `check_native_governance.py --surface entries`和`--surface consumers`：分别STATIC_PASS，exit 0。Issue中未带surface的示例实际报缺少必填参数，exit 2；实施命令已纠正。

实施后必跑：上述离线pytest加入新核验测试；三个检查器及两个governance surface；ruff和mypy；变更文档frontmatter/wikilinks验证；`git diff --check`。所有测试走既有offline runner，不读真实凭据，不跑live业务探针。

当前没有新行为TDD红绿证据；没有宿主审批或实际删除结果；没有运行无改动范围的全量ruff/mypy。不将81项既有基线当作本Issue完成证据。

草案自身已检查：frontmatter YAML、AC-1至AC-7、证据链接及7文件差异清单通过；`git apply --check --whitespace=error-all evidence/issue-555/proposed-policy.diff` exit 0（仅检查，未应用）。初版补丁因目标文件换行形式不同未通过，已按各文件原始LF/CRLF重生成后通过。此检查不等于正式文档全量校验或实施验收。

## 7. 完成标准与交接

- [x] §3.1具名保护面方案获Owner批准并正常应用。
- [x] 新增核验及诊断回归先红后绿，原边界回归保持通过。
- [ ] AC-1/2/3/5/6离线及流程证据逐项齐备。
- [ ] AC-4及AC-7宿主部分有真实有效模式、实际审批/执行及删除结果。
- [ ] 文档消费者闭合、未验证项明确；发布阶段另获授权。

实施来源：Codex完成扫描、独立工作树、实现、文档同步与验证；HITL=Owner对本方案回复“实施”，保护面正常应用；BDD/TDD=新行为及修复均有红绿记录；Subagent dispatched=NONE。

## 8. 本轮实施与验收记录（2026-09-22）

### 实现结果

- 新增只读CLI `scripts/sdd/check_deletion_targets.py`；路径/秘密/重解析点/嵌套仓库保护，Git索引及状态核验，成员/身份/摘要比较，备份完整性检查，Windows DELETE共享探测，逐项差异及拒绝分类。
- 命令行首次核验与baseline重检、目录备份、有效模式诊断见已更新的Onboarding §6.5。UNKNOWN及缺备份不被当作通过；工具不删除任何文件。
- 7文件拟议修改已应用；新增42项核验测试、1项hook/rules边界测试和1项直接文档消费者回归。没有修改hook分类逻辑、冻结契约、个人权限、业务代码、CI或依赖。
- 对工作树根及其他worktree的删除仍由各自Git流程核验，不将当前CLI用于越界删除。POSIX文件占用检测未实现，返回UNKNOWN；真实on-request验收未做。

### TDD与诊断证据

1. 初始新测试因模块不存在失败；既有文件中的两条新回归分别因Remove-Item规则缺失、逐节点确认旧文字失败。
2. 首轮114例中5例失败，最小临时文件复现路径stat与句柄fstat的ctime不一致；birthtime、mtime、inode一致。固定回归先红后绿，身份比较改用可用的birthtime，保留文件ID/mtime/内容摘要和前后复核。
3. 三条补充失败回归暴露skip-worktree/assume-unchanged隐藏内容及核验中变更；Git flags纳入备份判断，扫描末尾再次比对内容/Git/HEAD后转绿。
4. 四个变化场景先以缺少differences失败，再实现新增/移除/修改成员清单。原始红态计数为各轮观测，不与最终测试总数混用。

### 最终本地验证

使用develop既有`.venv/Scripts/python.exe`运行本工作树脚本，未安装依赖、未uv sync。pytest由未修改的`run_offline_pytest.py`执行；新测试以`git add --intent-to-add`登记以满足tracked输入要求，没有暂存文件内容、提交或发布。

| 检查 | 结果 |
|---|---|
| offline runner：test_deletion_targets、test_codex_native、test_native_governance、test_native_skill_contracts、test_native_migration_guards、test_native_scan_domains、test_native_mcp_scopes | 144 passed，22 subtests passed，18.98s，exit 0 |
| 全仓 `python -m ruff check` | All checks passed，exit 0 |
| `python -m mypy src/mj_agent` | 48个源文件无问题，exit 0 |
| `python -m mypy scripts/sdd/check_deletion_targets.py` | 1个源文件无问题，exit 0 |
| check_codex_native --effective-approval-policy never | config STATIC_PASS；session INCOMPATIBLE；owner NOT_ASSESSED；host NOT_TESTED |
| check_native_skills | STATIC_PASS；host/services NOT_TESTED |
| check_native_governance --surface entries / consumers | 两者STATIC_PASS |
| check_frontmatter | 143篇canonical文档通过 |
| check_wikilinks | 0 archive-ref violations；5个根文件0 unresolved targets |
| git diff --check | 通过；历史补丁转为等价零上下文格式后不再有补丁上下文空行的空白告警 |
| Codex CLI规则重放 | 实测codex-cli 0.147.0；Remove-Item命中prompt；仅计算decision，未执行删除 |

### AC实际覆盖

| AC | 本轮结论 |
|---|---|
| AC-1 | 规则/技能文本及回归通过；真实删除任务中复用批准的受控会话未验收 |
| AC-2 | 离线临时Git库、备份失败/完整目录、junction、秘密路径保护、实际Windows占用探测通过 |
| AC-3 | 内容/成员/路径替换、Git索引/HEAD、其他worktree及部分缺失逐项回归通过；会话撤销流程文字齐备，真实会话验收待补 |
| AC-4 | 未验证：当前有效模式never；未发起宿主删除请求，未观察正常审批及执行结果 |
| AC-5 | 已知/未知拒绝样本分类及原始错误保留通过；本轮未发生工具策略拒绝，不虚构归因或恢复 |
| AC-6 | 既有hook行为保持，新增prompt及精确校验一致；原生检查和正反例通过；没有把UNKNOWN改成ALLOW |
| AC-7 | never/on-request/unknown离线矩阵及操作说明通过；Desktop模式切换、实际hook加载与正常审批尚未验证 |

不关闭issue，不把CLI版本当Desktop引擎版本。未运行业务/外部服务、真实清理、commit/push/PR/merge。

### 恢复与后续

7个已批准目标的修改前准确字节：`.mj-agent-local/issue-555/before-approved-policy.zip`；同目录JSON记录原文件及ZIP SHA-256。原获批补丁：`approved-proposal-original.diff`。未修改develop或其他已有工作树；没有对这些文件执行自动恢复或清理。

后续依赖：工程师在正常配置流程提供并核实有效on-request会话及Desktop引擎版本；在该会话审阅具名临时清单，完成正常审批/执行并逐项验证结果。沿用本任务已给出的实现授权，不重复要求相同实现批准；真实临时清单的删除授权及宿主审批分别记录。当前仅宿主和受控会话验收未闭合，独立实现成果已可审阅。

## 9. Issue 更新后的实施（2026-09-22）

### 输入、范围及风险决定

读取 Issue updatedAt=2026-09-22T02:39:10Z，AC 扩至 14 项。当前范围增加 commit/普通 push/PR 的动作级授权复用，合并后双端远程引用删除，以及明确 never 阻断、部分成功和响应丢失后的恢复。真实发布/删除、个人权限/信任、#552 生命周期及旧工作树不在本次执行范围。

工作树从 6055f23 快进至本地 develop=7446e731649c2577c6246d57bbfdccc2d91e780e，复用已合入 #552 的 `scripts/check_codex_approvals.py`。变更前准确字节保存在 `.mj-agent-local/issue-555/update-20260922/before-sync.zip` 及摘要 JSON；autostash 9bd7628 保留。唯一重叠测试合并保留 #552 与 #555 双方新增断言，冲突清零，没有创建提交、推送或修改其他工作树。

原生 hook 方案见 [proposed-git-hook.diff](../evidence/issue-555/proposed-git-hook.diff)，Owner 明确回复“批准应用该 hook 补丁”，已应用。只对有限命令返回 HOST_APPROVAL_REQUIRED 的 additionalContext，既有 prompt 不变，UNKNOWN/FORBIDDEN/受保护编辑仍 block。没有 allow/ask/updatedInput，没有读取聊天或认证批准字段。官方 [Hooks](https://learn.chatgpt.com/docs/hooks) 支持该上下文协议并标 permissionDecision=ask 不支持；文档不证明本机 Desktop 实际兼容。恢复为 7446e73 的具名 hook 原文件；初次 git apply 因补丁 CRLF 空白检查失败，规范为等价 LF 后成功，不是策略拒绝。

不改 ADR 的决策权/信任模型，不改冻结契约、infra 技能、hook launcher、服务集合或 CI gate。本轮是有限执行流程与治理消费者修正，不建立可信授权传递体系；核验输出不能当审批 receipt。其他保护分支、实际远程身份和 squash/rebase PR 来源仍需独立观察，检查器不读取可能包含秘密的远程配置来声称这些已验证。

### 任务及 Documentation Decision

| 对象 | 决策与完成内容 |
|---|---|
| check_deletion_targets / tests | update：补 AskForApproval Never、index.lock Permission denied、网络拒绝诊断及原错保留 |
| check_git_actions / test_git_action_review | create：只读精确远端清单、保护引用、tip 差异、祖先与 squash/rebase 证据比较；五动作范围/撤销/恢复和分项报告 |
| codex_hook_guard / hook tests | update：获批有限路由及正反例、未知复合命令、wire JSON 协议 |
| check_codex_approvals / test_codex_native | update：五类动作、两端共7行命令覆盖 never/on-request/unknown；复用批准文字；静态状态不认证执行 |
| AGENTS / ai-agent / execution-boundaries | update：动作独立、已有批准复用、有限路由、部分成功对账和共同阻断 |
| git-commit / git-push / git-pr / git-delete / flow-post-merge | update：各自前置/后置证据、远端独立删除和报告、去掉吞查询错误及仅祖先推断 squash 合并 |
| Onboarding §6.6 / Git Push Workflow §0.1 | update：实际接口、输出语义、恢复限制及三条真实验收链路；引用现有入口，无文档移动/新增 canonical 页面 |
| INDEX / SPEC / ADR / 冻结契约 / CHANGELOG | none：现有指南入口仍有效；决策模型/契约/API/runtime 不变，维护工具链不改业务用户行为 |

### 本次方法与验证

TDD：新 action-review 测试先因模块缺失报红；诊断3条新样本先失败；有限 hook 的20例先失败，再应用获批实现。首次合并后定向组合118 passed、22 subtests passed。新增恢复及 CLI 案例随后纳入最终矩阵，以上中间结果不冒充最终结果。

只读辅助不执行动作：远端 CLI 不 fetch/delete；恢复函数只比较调用方观察，owner_approval=NOT_ASSESSED、execution=NOT_ATTEMPTED。未实现自动 commit 前置收集或自动 PR 查询；对应真实操作前核验由技能执行，不能用合成 scope 输入代替实际 staged diff、可写条件、两端/PR 对账及任务授权。

最终验证结果在下方完成后记录；全部使用既有解释器和原 offline runner，无依赖同步。新测试仅 intent-to-add，以满足 tracked 输入，没有暂存文件内容。临时 bare remote 的测试推送/引用变更是隔离夹具，不是 Gitee/GitHub 真实发布证据。

### AC 与未验证项

| AC | 仓库实施 / 本次证据边界 |
|---|---|
| 1–3 | 原删除核验与批准复用保留；新增动作范围/撤销/变化仅暂停受影响项；真实受控会话仍未验收 |
| 4 | 未验证：本地临时清单的真实 on-request 请求/审批/删除结果 |
| 5 | 四类指定拒绝及其他明确层级离线回归；本次未发生实际工具策略拒绝，不虚构归因 |
| 6 | 有限 hook 路由、prompt 校验、直接消费者及正反例同步；实际宿主加载未验证 |
| 7–8 | 五动作 × never/on-request/未知，单项/多项/撤销/变化合成范围比较；不把输入当真实授权 |
| 9 | 未验证：受控仓库 commit → Gitee/origin 双推 → 显式 base PR 的真实审批及全链路结果 |
| 10 | never 持续、模式变化、部分成功与响应丢失先对账；恢复函数不接受网络恢复作为解除模式阻断的输入 |
| 11 | 本地删除、远端删除及 Git 发布三链分开；工程师宿主配置与仓库变更分开 |
| 12 | 临时 bare remotes 覆盖精确 refs/tip、保护、tip 不同/变化、未合并、squash/rebase、查询失败；实际远端身份/保护仍需查实 |
| 13 | 离线状态/引用回归；真实 Gitee/origin 删除及正常审批未验证，没有获批测试远端或支持审批的有效会话 |
| 14 | develop=7446e73 的合成报告分别列本地、两端、completed、UNCOMMITTED、#552 OUT_OF_SCOPE；未处置真实对象 |

实施来源 Codex；HITL 为当前任务的实施授权与新增 hook 具体补丁批准；BDD/TDD 为离线行为回归，无真实会话 BDD；未委派。无 commit/push/PR/merge、真实远端删除或 issue 状态改动。当前有效会话仍 never，不能通过重复授权解除；不尝试真实破坏性动作来验证已知阻断。

### 本轮最终验证记录

| 验证 | 本次实际结果 |
|---|---|
| offline runner：test_deletion_targets、test_git_action_review、test_git_hook_review、test_codex_native、test_guard_git_workflow_hook、test_native_governance、test_native_skill_contracts、test_native_migration_guards、test_native_scan_domains、test_native_mcp_scopes | **213 passed，30 subtests passed，40.91s，exit 0** |
| 全仓 `python -m ruff check` | All checks passed，exit 0 |
| mypy src/mj_agent + check_git_actions、check_deletion_targets、codex_hook_guard、check_codex_approvals | 52 source files 无问题，exit 0；首次检查发现新增辅助的2处类型问题及 approval_status 的既有 Optional 键类型问题，均已修正后通过 |
| check_codex_native --effective-approval-policy never | config STATIC_PASS；session INCOMPATIBLE；owner NOT_ASSESSED；host NOT_TESTED |
| check_native_skills / check_native_governance entries、consumers | 三项 STATIC_PASS |
| check_frontmatter / check_wikilinks | 144篇 canonical 文档通过；0 archive-ref violations；5个根文件0 unresolved |
| check_codex_approvals --effective-approval-policy never | 7行命令全部 INCOMPATIBLE，exit 1（预期诊断结果，不是运行失败的远端动作） |
| codex execpolicy check：合成远端删除 / PR 命令 | 两项实际计算 decision=prompt，exit 0；没有执行被检查命令，不代替宿主端到端验收 |
| git diff --check / git ls-files -u / git diff --cached --stat | 空白检查通过；无冲突；无暂存内容 |

文档审阅（mj-agent-doc-sync → mj-agent-doc-validate）：A1–A4 路径/元数据/状态/链接通过；A5 无新 canonical 页面或入口变化，INDEX 无需改；A6 HITL 入口同步；A7–A11 无 runtime canonical 变更，不适用；A12–A14 原生技能/规则/信任边界静态通过，宿主加载与服务保持未验证。OB 静态审阅确认示例标为合成、接口与代码一致、历史方案有明确时间界限、无重复迁移正文。无实际发布、破坏性操作、宿主配置或工程师恢复动作可报告为已执行。

## 10. #558 合并后流程回归修复（2026-09-22）

### 10.1 输入、根因与范围

- 读取 Issue #555 `updatedAt=2026-09-22T04:38:07Z`；Owner 本次要求“根据刚刚更新 issue 555 中的内容，执行修复”。基线为 #558 merge `cfb2ea339452a752c01503bf2e6856f2964673e4`，独立 worktree 分支 `codex/555-approval-regression`。
- Issue 新现场是两个其他分支的批量远程删除在创建进程前被拒；本任务上一轮也在已知 never 下发起单分支删除并收到同类拒绝。两者都属于执行流程错误；不能把“用户再次要求尝试”当成模式恢复证据。
- 静态源码显示 `_host_review` 已将单分支删除交宿主审批、多分支形态判为 UNKNOWN；`review_actions` 即使没有既往拒绝记录也会在 never 下返回 BLOCKED_EXECUTION_ROUTE。根因是调用前未遵守已有兼容性结论，不是必须放宽 hook 才能处理的缺陷。
- 本次只补守卫/恢复回归、删除与 post-merge 技能的执行入口、既有 Onboarding §6.6 和本计划。原生 hook、`.codex/**`、政策/SDD 元规则、冻结契约及运行时代码不改；不新增批量识别，不修改宿主权限或信任，不重试真实清理，不发布 commit/push/PR，不关闭 Issue。

### 10.2 实施与文档决策

| 对象 | 改动与原因 |
|---|---|
| `tests/unit/test_git_hook_review.py` | 增补 16 组：两端 × 短名/完整 ref × string/argv × 单分支/多分支；同时验证分类与实际 hook JSON 输出，单分支仅 additionalContext，多分支 UNKNOWN/block，伪造批准字段不能放行 |
| `tests/unit/test_git_action_review.py` | 增补 5 类动作的首次请求前 never 场景，无既往拒绝且比较范围相同也保持 NOT_EXECUTED / NOT_ATTEMPTED；重复审阅不解除阻断 |
| `mj-agent-git-delete` | 把有效模式核验置于命令序列之前；已知 never 时连首次“试一次”也不发起；补多分支反例，恢复后逐端、逐分支核验 |
| `mj-agent-flow-post-merge` | Step 7 显式接入上述执行入口，区分预检未执行和历史真实拒绝 |
| Onboarding GUIDE §6.6 | 单/多分支形态表、宿主错误归因边界及受控会话验收记录要求 |
| 本计划 | 分开保留 #558 离线实现、后续失败现场、本轮回归和仍未完成的真实验收 |

无文件重命名、新文档入口、runtime canonical、依赖或契约变更，INDEX、ADR/SPEC、CHANGELOG、EVAL 无新增修改需求；根 AGENTS 与共用执行边界原有不绕过/不重复试探要求继续有效。

### 10.3 会话证据与验收边界

| 场景 | 证据与结论 |
|---|---|
| 本任务上一轮“评估…如果没有尝试再次执行” | 会话声明 never，既有规则要求 prompt；实际调用单分支 Gitee 删除，返回 `approval required by policy, but AskForApproval is set to Never`。这是 AC-10 的负例，不能当验收成功；进程未启动，hook 是否执行未知，不能归因于自动审批模型 |
| Issue 描述的其他两分支批量删除 | 仅作为 Issue 来源的失败记录；本轮未重新执行。多分支 UNKNOWN 是本地代码及离线回归结论，不冒充现场 hook 返回 |
| 本次修复会话 | 权限声明仍为 never；只读审批预检 7 行全部 INCOMPATIBLE，exit 1。保留旧任务授权，不调用真实删除/commit/push/PR，不拆分批量命令、不改权限或另换工具；此为本轮行为记录，不等于已完成所有受控会话场景 |

AC-6 本轮补充单分支正例、多分支反例及示例一致性；AC-10 离线回归与失败/修正记录分别保留，独立受控会话中“首次请求”“拒绝后重复尝试”“环境确实恢复”的完整验收仍待执行。AC-4/9/13 仍需工程师核实有效审批环境、Desktop 引擎版本、配置覆盖来源及规则/hook 加载，并对另行批准的临时对象走真实链路。Issue 保持 OPEN，计划保持 active；本节未提交，不把文档更新当作远端操作结果。

### 10.4 本次验证

- 现有离线 runner 执行 `test_git_hook_review.py` 与 `test_git_action_review.py`：**68 passed，12.33s，exit 0**。
- Ruff 检查两份修改的 Python 测试：通过，exit 0。
- 关联原生检查器/技能回归 `test_codex_native.py`、`test_native_governance.py`、`test_native_skill_contracts.py`：**97 passed，6.54s，exit 0**；两批共 165 项通过。
- `check_native_skills`、`check_native_governance --surface entries/consumers`、`check_codex_native --effective-approval-policy never`：静态通过；后者 session 仍 INCOMPATIBLE，host NOT_TESTED。
- `check_frontmatter`：145 篇 canonical 文档通过；`check_wikilinks`：0 archive-ref violations，5 个根入口 0 unresolved；`git diff --check` 通过，无暂存内容。
- 文档静态审阅：A1–A4 路径/元数据/链接通过，A5–A6 无入口变化，A7–A11 无 runtime canonical 变更，A12–A14 保留既有保护面和实际宿主未验证状态。Onboarding GUIDE 长度超过建议 500 行，记 OB1 WARN（原指南已超过建议长度，本次按既有 §6.6 局部补充）；无新路径或移动，其他 OB 未见本次新增矛盾。检查已有推送 GUIDE 的 never 恢复说明与本次入口一致，未重复修改。
- `check_codex_approvals.py --effective-approval-policy never`：7 行 INCOMPATIBLE，exit 1（预期停止诊断）；owner NOT_ASSESSED、host NOT_TESTED。
- 本次是既有行为的覆盖补充与流程说明修复，测试首次运行通过，未宣称 red-green 修复了 hook 行为。实施来源 Codex；未委派；未执行外部业务测试或宿主成功验收。
