---
type: plan
summary: 删除与 Git 发布的动作级授权、只读核验、有限 hook 路由及部分完成恢复
owner: ranzuozhou
created: 2026-09-22
updated: 2026-10-09
state: active
track: engineering-workflow
---

# [PLAN] Issue 555 已批准删除与 Git 发布流程

> Issue: [#555](https://github.com/MJ-AgentLab/mj-agent/issues/555)
> 关联: [#552](https://github.com/MJ-AgentLab/mj-agent/issues/552)
> 状态：§1–§10 保留 #558/#560 方案、失败与验证历史；最新范围以 §11 及 Issue 现行 AC 为准，§12–§30 记录执行、取证、Owner 批准的新会话验收及顺序调整、实际模式变化、执行结果、反馈入口拒绝、正文送达、状态评论回执、新增记录核查、获批支持请求、人工支持升级、专员首答、记录交付及合并后保护/同步准备与获批执行。旧 Git prompt、统一 on-request 和多分支 UNKNOWN 的要求由对应条款替代。目标 Desktop 加载及恢复证据未完成，计划保持 active；本文件不是授权凭证。

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

## 11. 按实际命令分离项目授权与执行条件（2026-09-22）

### 输入、方法与实施停点（应用前记录）

Issue 最新 updatedAt=2026-09-22T07:06:27Z；Owner 本次要求修复最新内容。基线 develop=b577fb690dffb31b80d7e72b45dda3bc310c6738；独立工作树 codex/555-command-policy。类型 maintain / C infra，风险 High。受保护 diff 按 Issue 的 HITL 约定审阅后应用；本轮先生成完整候选补丁，在未启用的公共源码副本验证，正式工作树规则、个人配置、信任和 hooks 加载均未修改。

副本排除 config/secrets*、非示例 .env 与密钥文件；独立 Git 元数据只供原离线 runner 核验 tracked 输入，未提交或连接真实 remote。使用 develop 既有解释器，未安装依赖。测试流程：51 个新场景先观察 26 failed / 25 passed，再实现到 51 passed；扩大相关回归后 243 passed / 30 subtests passed，后续补充边界的最终结果见交付报告。

### 任务、AC 与 Documentation Decision

| 对象 | 决策、任务及对应 AC |
|---|---|
| .codex/rules + check_codex_native | update：移除六条 Git/gh 条目，准确保留四条剩余规则；规则损坏/重复参数拒绝，主检查器不再输出统一会话不兼容（15、21） |
| git_command_review + codex_hook_guard | create/update：有限词法解析和动作对象，多消息/文件互斥、upstream 换序、显式源:目标、批量删除、PR 短参数/等号；上下文无宿主审批宣称，保留 G1/G2/人工 merge/秘密/受保护编辑（16–20） |
| check_codex_approvals | update：动作筛选和精确 argv；规则匹配、模式来源、加载未知、静态 hook 和宿主未测试分列；Remove-Item 冲突只影响该命令（21） |
| check_git_actions | update：实际 command 与 scope 匹配、显式源和目标只读核验、批量逐 ref 检查与暂停；旧拒绝须核验条件变化及实际加载，成功/未知先对账（18、19、22） |
| sdd/native-consumers.json | update：登记新 helper 这个直接执行依赖；不改 CI gate 或冻结 capability 契约 |
| AGENTS / ai-agent / execution-boundaries | update：动作授权仍独立；移除统一 Git prompt 前提，保留拒绝来源和恢复要求（23） |
| commit/push/PR/delete/post-merge 五技能 | update：按具体命令诊断及批量逐 ref 恢复；其余技能与冻结 infra 保持（23） |
| Onboarding / Git Push Workflow | update：支持参数、CLI/API、状态和实际验收；历史记录保留（23、24） |
| ADR-041 / decisions INDEX / docs INDEX / CHANGELOG | create/update：记录取消 Git 规则的权衡、减少一层防线及宿主边界，入口关联闭合；ADR 为 draft（23） |
| 新旧直接测试 | update：先红后绿及回归；字符串/argv、文本引号、未列参数、规则损坏、未知加载、实际拒绝恢复和逐引用结果 |
| SPEC / RUNBOOK / Local ISSUE / ASSESSMENT / MCP 冻结契约 | none：无需新增；业务与服务集合不变 |

### 授权与证据边界

本候选仅准备 #555 已明确选择的规则治理方案，新增 helper 作为现有原生守卫的直接依赖一并保护、校验和登记。没有用候选规则执行真实 commit/push/PR、删除或修改当前宿主模式，没有建 receipt。移除 rules 不等于取消宿主其他来源的审批/拒绝；同一任务授权不被当作可信执行凭证。

旧拒绝的 prior_blocks、加载哈希与模式是调用者观察，检查器只比较、不认证。只有明确项目 prompt 来源，且核验新条件的加载证据，才可重新评估；未知或其他宿主来源不能由规则文件变更自动解除。对账成功仍优先记 COMPLETE，剩余批次不能重复携带已成功引用。

### 完成标准与未验证项

AC-15～23 的候选代码、文档与离线回归成组交付，审批后只应用已审阅补丁并复核本工作树。AC-4/9/13/24 的临时对象真实链路仍需单独对象授权及目标会话加载/执行证据；当前 never 是真实模式，但候选文件不是当前会话生效规则。Issue 保持 OPEN，Plan 保持 active，不以 #560 已清理或旧条件下发布成功替代新规则验收。

独立报告本地 Git 清理、Remove-Item、提交/双推/PR 和双端逐 ref 删除；没有实测的步骤标未验证。实现来源 Codex；未委派；未运行业务/外部服务、修改个人配置、启用信任或触发新交付循环。

### 批准应用与实际工作树验证（2026-09-22）

Owner 回复“批准应用完整补丁”后，核对基线、干净工作树、28 个目标原始摘要、补丁及恢复包摘要，再以 `git apply --whitespace=error-all` 应用。28 个应用结果的规范化 SHA-256 全部匹配批准清单，无额外文件变更；随后仅同步本段与 ADR-041 的应用状态。原始批准补丁 SHA-256 为 `e31485746e44e245748b46c72df898baab2cba969091632d98afab2617b0c797`，保留于本地交付目录。

实际工作树重新执行九文件离线回归：**301 passed、30 subtests passed，37.86s，exit 0**。全仓 Ruff、五个修改源模块 mypy、原生配置/技能与 governance entries/consumers 均通过。原生检查报告 session_approval=PER_COMMAND、effective_approval_policy=never、rule_loading=UNKNOWN、host_enforcement=NOT_TESTED。

三个新增文件仅登记 intent-to-add 供既有离线 runner 核验；未创建提交、推送、PR 或执行真实删除。实际规则加载与 AC-4/9/13/24 仍未验证，Issue 保持 OPEN、计划保持 active；本轮批准不扩展到 Git 发布或宿主配置变更。

## 12. #561 合并后的 AC-1～AC-24 复核与受控验收准备（2026-09-23）

本节按 Issue 当前有效正文复核，不以折叠历史方案中的统一 on-request、Git prompt 或多分支 UNKNOWN 条款改写验收。完整逐项结论、命令、PR/提交及临时对象清单见 [acceptance-2026-09-23.md](../evidence/issue-555/acceptance-2026-09-23.md)。#558、#560、#561 已合并；其中 #561 merge 为 `8a029e7bb3f29af4bd510b916e6bafbeaaf4b074`，项目层规则与检查器落地，但合并不证明目标 Desktop 实际加载或临时对象真实执行。

### 项目、宿主和三条链路分账（批准前快照）

| 对象 | 2026-09-23 观察 | 验收边界 |
| --- | --- | --- |
| 项目变更 | Git/gh 六条项目 rules 已移除，余 Remove-Item prompt 与三个 DB forbidden；hook/检查器有限识别、G1/G2 和人工 merge 保护的离线回归通过 | 静态文件及离线运行证据，不等于目标宿主加载 |
| 宿主条件 | 当前任务权限声明 `never` / `danger-full-access`；`check_codex_native.py` 报 `PER_COMMAND`、`rule_loading=UNKNOWN`、`host_enforcement=NOT_TESTED` | 不因项目 Git 规则无匹配推断无需宿主审批；旧 on-request 发布现场仅按当时时点保留 |
| 本地删除 | `git worktree remove`、`git branch -d` 的项目诊断与 Remove-Item 分开；三个新建清洁 worktree 可作受控对象 | 尚无本轮 Owner 本地删除授权或正常工具删除结果；有修改/未跟踪内容的旧工作树保留 |
| Gitee 与 origin 远端删除 | 两端只读 `ls-remote --heads` 证明 #560/#561 两条旧 head 引用已缺失；`maintain/555-approved-deletion` 两端仍存在且 tip 不同 | 不重复删除旧引用；旧结果不充当新临时 S/A/B 引用的 AC-13 全部验收 |
| commit→双推→PR | #560 旧条件下的实际发布有 SHA 和 PR URL；新发布 canary 分支已建、两个文件已精确暂存 | AC-9/24 要求的新条件、显式 base、两端 SHA、宿主审批/拒绝与 PR URL 尚未实测 |

### 本次离线验证与交付状态

- 定向 offline runner：230 passed、30 subtests passed，exit 0；全量 `tests/unit`：1095 passed、1 skipped（非 Windows）、30 subtests passed，exit 0。Ruff、mypy（48 源文件）、原生配置/技能/governance 两 surface、frontmatter（146 篇）和 wikilinks（0 违规）均 exit 0。详情及原始命令见验收矩阵；检查器的 `STATIC_PASS` 不代替宿主实测。
- 文档反扫与本节按当前 ADR-041 语义对齐。无业务运行时代码、依赖、Docker、CI gate、MCP 集合或个人权限/信任改动；没有外部业务探针。BDD/TDD：本轮只复跑既有离线回归并准备受控对象，没有新增行为测试或声称新红绿。实施来源 Codex；Subagent dispatched=NONE。
- `develop` 工作树在写本记录前干净；本记录与计划修改后为未提交交付。保留旧 `maintain/499-enforcement-blocking`（2 修改）、`maintain/552-codex-approval-preflight`（5 修改、1 未跟踪）与 `maintain/codex-dev-mode-migration`（7 修改、475 未跟踪）及其忽略内容；不处理 #552 或其他 issue 的交付。
- 批准前 AC-4/9/13/24 的真实链路及若干会话面尚未验收。四条 #555 本地临时分支从 `develop=407e06877fbb8913fe2f702c8601a16f8ba41fb9` 建立：发布一条、远端单删一条、批量双删两条；三条删除候选在批准时 clean 且该 tip 已在 develop。Owner 已在当前任务分别批准验收矩阵的 commit、普通 push、PR 创建、本地删除和远端引用删除五类精确对象及命令；批准不扩展到计划/矩阵提交、force 或 merge。执行紧前重检并逐端对账，先后结果如下。

### 首轮受控执行与网络停点（2026-09-23）

- 已按批准范围执行正常工具 `git commit -m "docs(evidence): add #555 controlled delivery canary"`，得 `878b474d56e1e4201bba335b60caa9ad7ee018cd`；仅两份具名证据文件，12 行、无其他 staged/unstaged/untracked/ignored。实际作者与提交者均为 `ranzuozhou <ranzuozhou@gmail.com>`，未见显式宿主审批请求。
- Gitee 已分别普通 push 发布分支和 S/A/B 三条删除候选，四次 `git ls-remote --heads gitee <精确 ref>` 查询均 exit 0 且各自匹配提交 SHA（发布分支 `878b474...`，S/A/B 均 `407e068...`）。成功项不重复推送。
- origin 对发布分支的推送前 `git ls-remote --heads origin refs/heads/codex/555-ac9-publish-20260923` 初始三次 exit 1，原始错误为 `fatal: unable to access 'https://github.com/MJ-AgentLab/mj-agent/': Recv failure: Connection was reset`。随后同一查询一次 exit 0、空输出；按原命令 `git push origin codex/555-ac9-publish-20260923` 返回相同连接重置，紧后的只读对账也失败。该次 origin push 结果记 UNKNOWN，不重复推送直至成功查询实际 tip；S/A/B 的 origin 普通 push 均 NOT_EXECUTED，Draft PR、本地 S/A/B 清理与双端远程删除均未执行。静态项目规则检查仍不是目标 Desktop rules/hook 实际加载证明，网络错误也不是宿主审批拒绝。
- 因此五类动作中 canary commit 与 Gitee 单端普通 push 有已核实结果，origin 发布 push 有 UNKNOWN 待对账。AC-9/13/24 不闭合；Issue 继续 OPEN、计划继续 active。后续只读查询成功后再按同一批准清单核对未完成端及对象；新拒绝/变化仅暂停受影响项。逐端逐引用明细、恢复命令和保留旧工作树状态见本节所链的验收矩阵。

### 最新恢复与逐链路结果（2026-09-23）

- origin 的同一精确只读查询随后 exit 0 且无发布引用，才重复原定普通 push 一次；该次 exit 0，随后 origin tip 为 `878b474d56e1e4201bba335b60caa9ad7ee018cd`。S/A/B 三条 origin 普通 push 也各自 exit 0、逐条查询为 `407e06877fbb8913fe2f702c8601a16f8ba41fb9`。Gitee 成功端未重推；先前连接重置的原始错误和 UNKNOWN 状态保留，不倒写为从未失败。
- [Draft PR #566](https://github.com/MJ-AgentLab/mj-agent/pull/566) 已经显式 `--base develop` 正常创建，并复查 OPEN/Draft、head=`878b474...`、base=`develop`、标题/body 一致。commit→Gitee→origin→PR 链路有独立真实证据；未 merge、未关闭 Draft PR。
- S 本地 worktree/branch 删除均 exit 0 且分别验证不存在；S 在本地分支缺失后仍完成 Gitee→origin 单引用远端删除。A/B 两端批量远端删除响应逐引用成功，随后每端每条引用的成功 `ls-remote` 查询均证实不存在；最后 A/B 本地 worktree/branch 各自删除并验证。所有远端删除前 tip 与两端 develop 均为 `407e...`，是已合并的同一提交。三个本地删除目标均无 dirty/untracked/ignored、无祖先或后代重解析点，DELETE 共享探测各 1311 节点全为 AVAILABLE；有内容旧工作树未动。
- `check_git_actions.py` 只读 CLI 在当前环境两次将 Gitee 查询报 UNKNOWN；直接正常 `git ls-remote --refs --heads gitee` 同期查询成功，执行以前者失败、后者成功分别记录，不伪称检查器 live 通过。检查器缩减子进程环境且不报告原始子进程错误，具体差异来源尚未确定。
- AC-4/9/13 的实际动作链已完成，详见矩阵逐项结论；目标 Desktop 对新 rules/hook 的实际加载仍无独立证据，AC-24 与其他仅离线覆盖面未完全闭合。当前有效模式声明 never，成功命令未见显式审批；这只证明各命令本次正常工具执行结果，不推定宿主永不审批。Issue 保持 OPEN、计划保持 active。

计划保持 `state: active`，Issue 保持 OPEN。只有全部适用 AC 的真实证据补齐，或 Owner 明确批准调整剩余范围，才建议关闭。计划文档未提交是独立待办，不会由远端清理或测试 PR 自动触发提交。

Owner 随后确认当前任务有效审批模式为 `never`，受控动作的成功与逐项对账不能证明目标 Codex Desktop 已加载新版项目 rules/hook；暂不调整 AC-22/24 范围，要求 #555 保持 OPEN。补充的宿主只读核查已确认 Desktop 安装版本 `26.917.51856`（build `10492`，prod）及本机配置 `mj-agent=trusted`；未找到目标 develop 会话对当前 `.codex/hooks.json` 的信任或加载记录。受控执行时段（2026-09-23 03:13–03:28 UTC）的可查日志无项目 rules/hook 加载事件，但缺失不证明未加载；另起 CLI 显示的 `OnRequest` 属不同进程，不替代目标任务的 `never`。目标会话 rules/hook 加载状态与加载版本仍为 UNKNOWN。下一步是取得可追溯的目标会话加载记录并按现行条款复核 AC-22/24；此次侧对话未修改信任、配置或仓库，也未授权新 Git 动作。

## 13. 历史加载记录复核与新一轮最小对象（2026-09-23）

本次目标线程 session meta、Desktop 文本日志与结构化日志的只读核查详见 `evidence/issue-555/acceptance-2026-09-23.md`。受控时段可核对目标任务的 `Never` 模式，但没有与其绑定的项目 rules/hook 加载来源、哈希或信任决定；`CodexHooks` 功能标记只说明功能存在。执行基线的 `.codex` 与守卫 Git blob 已登记，不能据此推定宿主加载。AC-22/24 仍为真实链路未验证。

现行条款把 AC-3/6/15/16/21/23 的验证范围限定在回归/会话、原生检查器、规则集合、协议、诊断矩阵和文档反扫；T1–T5 对这些范围已有实际结果，因此矩阵六项改列“已验证（项目实现/离线范围）”。真实 Owner 撤销未人为制造，目标宿主加载仍独立留在 AC-22/24；本次没有重新运行测试。#555 保持 OPEN，计划 `state: active`。

Owner 对两分支审阅草案回复“同意，执行”。当前 develop 与 Gitee/origin 的 `refs/heads/develop` 在创建前同为 `9b754a690d0ef0b432d7ea431c2edda1043361b2`，两条候选远端 ref 均不存在。已按 G1 创建两个本地 worktree：`D:/workspace/10-software-project/projects/mj-agent/codex/555-ac24-load-publish-20260923` 和 `D:/workspace/10-software-project/projects/mj-agent/codex/555-ac24-load-delete-20260923`；两条本地分支初始 tip 均为 `9b754...`，前者只暂存 5 行 canary 文件、index blob `134e0813e2d94e99c87b6ba08f37be8ac25693ed`，后者清洁。PR 正文模板草案位于 `C:/Users/Admin/AppData/Local/Temp/mj-agent-555-ac24-pr-body-20260923.md`，未用于创建。

本次尚无新的目标 Desktop 会话实际加载记录，现有工具也未提供能确认加载路径、哈希、信任与有效模式的回执。按 AC-22/24 与已审阅的前置条件，commit、Gitee/origin 普通 push、Draft PR、两端远端删除均 **NOT_EXECUTED**；本地对象和暂存文件保留，不把“同意执行”扩展到尚无加载证明的发布/删除链路。若取得新会话可追溯加载记录，再复核对象、index blob、两端 tip 与各动作授权，并按 Gitee→origin 及响应丢失先对账的顺序继续。未执行本地 worktree/branch 删除、force 或 merge；旧工作树及 `.playwright-mcp/` 保留。

## 14. 反馈回执补记、历史可追溯程度与待决选项（2026-10-08）

Owner 要求继续已准备的取证与记录工作；本次补记反馈上传事实、只读核对留存证据与对象，并准备可选择的后续范围，不调整 AC、不执行新的 Git 发布/删除。详细来源、JSONL 行号、对象及逐动作命令见 [验收记录](../evidence/issue-555/acceptance-2026-09-23.md) 的 2026-10-08 两节。

- Feedback ID 与原目标线程均为 `01a0cc2d-5760-7163-82ee-9ac75ff8b177`。原结构化日志 ID `25176077` 在 **2026-09-23 05:06:58 UTC** 记录上传成功、13 个附件、`attachments_failed=false`；Desktop `feedback/upload` 于 `05:06:58.029Z` 的 requestId=`c5348d11-4dc9-428d-b92a-e44563d06897`、`errorCode=null` 为另一来源。现存目标 session JSONL 留有这些只读查询输出；原 Desktop 文本日志目录和 SQLite 原行已不可直接复查。上传成功只证明送达，未取得诊断答复或项目加载证明；没有再次上传。
- 历史 Desktop **26.917.51856（build 10492，prod）已由 Owner 核实**；目标 session meta 可核对线程、develop 路径及引擎 `0.155.0-alpha.16`，留存结构化查询可关联当时 `Never`。实际 rules/hook 来源、当时加载版本/哈希、项目与 hook 信任决定、加载/跳过状态及原因/时间仍 **UNKNOWN**。静态 blob、trusted 配置、功能标记、另起 CLI 或命令成功均未充当实际加载证据。
- 两端只读查询均 exit 0：develop=`9b754a690d0ef0b432d7ea431c2edda1043361b2`，第一轮发布 tip=`878b474d56e1e4201bba335b60caa9ad7ee018cd`；第二轮两条候选 ref 各端均不存在，新 head 的 PR 查重为空；#566 仍 OPEN/Draft、base=develop。两个新本地 worktree 的 tip、仅一文件 staged 的 canary blob 与删除候选清洁/祖先关系未变。原 PR 正文临时文件缺失，本次恢复为 [持久草案](../evidence/issue-555/ac24-pr-body-2026-10-08.md)，SHA256=`ED1514F2DD708C0D931CB6DCFB9E411AF0DEFB38D1B2C4E18EEAA1DDE33871C6` 与原草案一致；待审命令采用新绝对路径，未用于 PR。
- AC-3/6/15/16/21/23 按各自现行项目/离线验证范围保持已验证。AC-22/24 仍为真实链路未验证/UNKNOWN；本次只校验文档，不把文档检查追加为宿主验收。旧工作树、两个新 worktree 与 `.playwright-mcp/` 均保留；第二轮五类动作仍 NOT_EXECUTED。

Owner 待决选项：**推荐新会话补验**，明确允许有可追溯加载记录的新目标 Desktop 会话完成剩余 AC-22/24，原时段 UNKNOWN 永久保留，新记录只证明新执行；AC-22 已知拒绝的条件变化及恢复仍独立验证。另一选项为**维持历史范围**，通过已有反馈 ID 继续索取原时段记录、暂停新轮动作。两项均未采纳，推荐理由与影响见验收记录；取得新加载记录和五类精确动作授权后再执行正常命令。信任由工程师独立审阅、宿主审批按实际要求处理。

最小剩余事项为目标会话加载证据或明确的范围决定，以及所选范围内 AC-22/24 恢复验收；实施计划继续 `state: active`，#555 继续 OPEN。验收记录、计划及 AGENTS 协作原则仍 UNCOMMITTED；提交它们须单独对象批准。实施来源 Codex，Subagent dispatched=NONE；无业务/runtime 改动，BDD/TDD 不适用本次记录补充，未安装依赖或执行外部测试。

本轮文档校验：`uv run --frozen --no-sync python scripts/check_frontmatter.py` 为 146 篇 PASS，`check_wikilinks.py` 为 0 archive-ref violations、5 根入口 0 unresolved，均 exit 0；`git diff --check` 通过。证据目录另作尾空白及相对链接检查，无问题。上述结果只证明文档检查，不替代 AC-22/24 宿主加载及恢复证据。

#555 已通过正常工具补记本节取证进展，回读 `updatedAt=2026-10-08T03:44:38Z`、state=OPEN；现行 24 条 AC、原正文前缀与折叠历史逐字保持，范围决定仍待 Owner。Issue 更新不是 Git 发布或验收通过证据。

## 15. Owner 批准新会话补验及五类具名动作（2026-10-08）

Owner 回复“同意推荐，授权执行”，已采纳 §14 的推荐方案：剩余 AC-22/24 可由具有完整可追溯加载记录的新目标 Desktop 会话完成；原 `2026-09-23 03:13–03:28 UTC` 的加载状态永久保持 UNKNOWN，新证据不回填历史。AC-22 已知拒绝的条件变化/恢复仍须独立核验。§14 的未采纳/待决描述为批准前快照，以本节为最新状态。

前节验收清单中的五类动作分别获批：发布 worktree 的单文件 canary commit；两条测试分支 Gitee→origin 普通 push；发布分支显式 base=develop 的 Draft PR（使用持久正文）；仅删除测试本地 worktree/branch；仅删除测试两端 ref、固定 tip=`9b754a690d0ef0b432d7ea431c2edda1043361b2`。精确对象、命令、正文哈希及逐动作状态见 [验收记录](../evidence/issue-555/acceptance-2026-09-23.md) 末节。五类均 APPROVED，复用本批准；不包含记录/计划/AGENTS 原则提交、信任/配置修改、日志上传、force 或 merge。

已取得 10 月 8 日新 session 文件、Desktop originator、目标 develop、引擎 `0.162.0-alpha.2` 与本轮 turn 的实际 never/danger-full-access；同线程原生日志的 Never 与进程 `pid:115512:d28f44c9-467c-4323-878e-0ba63ea77ce0` 可关联。当前安装包登记 `26.1002.7124.0`、ASAR 应用 version=`26.1002.52244`，这些与历史 Owner 核实的 `26.917.51856/build 10492/prod` 分列。新目标 rules/hook 来源/实际哈希/信任/加载状态仍 UNKNOWN，没有用版本或模式证明加载。

当前 Desktop 前端有 Hooks 设置只读 `hooks/list` 入口，但该 Agent 工具不能调用，且列表仅按 cwds 读取配置，仍需目标实际加载关联。已准备 [新目标诊断请求草案](../evidence/issue-555/ac24-desktop-diagnostic-request-2026-10-08.md)，未发送/上传；未使用另起 CLI、手动运行 hook、私有 IPC 或改配置获取替代结果。

最新只读预检显示两工作树 tip 和 staged canary 未变、删除候选 clean，两端 develop 同 tip、候选 ref 均不存在，持久 PR 正文哈希未变。加载前置证据仍未满足，所以五类动作均 NOT_EXECUTED，停点为 UNMET_HOST_LOAD_EVIDENCE；没有新宿主拒绝，不虚报 BLOCKED_EXECUTION_ROUTE。取得实际加载记录后按同一授权从紧前预检继续。#555 保持 OPEN、本计划 active；记录仍 UNCOMMITTED，旧工作树及 `.playwright-mcp/` 保留。

本轮 frontmatter 146 篇 PASS、wikilinks 0 violations/5 根入口 0 unresolved、diff 空白与证据相对链接检查通过；原生检查器 STATIC_PASS/PER_COMMAND，加载 UNKNOWN、宿主 NOT_TESTED，不能替代真实证据。#555 范围及授权记录已回读，updatedAt=`2026-10-08T04:07:50Z`、state=OPEN；仅 AC-22/24 附加新会话范围与对应矩阵同步，其余 AC 及折叠历史保持。实施来源 Codex，未委派，BDD/TDD 不适用本次记录维护。

## 16. 实际 on-request 切换与正常审批入口（2026-10-08 04:14 UTC）

Owner 告知已切换 ask for approval 并要求继续。目标 10 月 8 日 session JSONL 第 411 行 `thread_settings_applied`（04:14:22.115Z）、第 417 行 turn（04:14:22.221Z，turn_id=`01a119b8-298e-78e2-a42b-48ad103c3d14`）与原生 SQLite 行 `27274879`（OnRequest，目标 thread/process）证实本轮实际为 **on-request / workspace-write**，network_access=false。上节 never/danger-full-access 是切换前事实；没有用另起 CLI 或声明代替目标会话证据。

只读 gh issue view 在受限网络返回代理连接拒绝，按宿主机制对同一命令请求 require_escalated 后成功；原生静态检查受限 uv 缓存访问被拒，对同一命令经正常审批入口执行后 STATIC_PASS/PER_COMMAND，但加载 UNKNOWN、宿主 NOT_TESTED。两个原始错误及逐命令范围完整留在 [验收记录](../evidence/issue-555/acceptance-2026-09-23.md) 末节；没有改配置、权限或换工具。没有独立“人工弹窗/规则免弹窗”分类，不从成功猜测。

两候选 worktree、tip 与 canary index 未变，删除候选 clean；两端精确引用查询均 exit 0、develop 同 tip、候选 ref 不存在。模式变化已核实，实际项目 rules/hook 的加载路径、定义哈希、信任和加载/跳过状态仍 UNKNOWN；获批的新会话方案保留这一前置，五类动作均 APPROVED / NOT_EXECUTED，取得记录后无需重复批准，从紧前核验及必要的正常宿主审批继续。

本轮未执行 commit、push、PR 创建或删除，也无新的 Git 宿主拒绝；停点仍 UNMET_HOST_LOAD_EVIDENCE，不能把模式切换、只读命令/静态检查成功写成真实 Git 或加载恢复。#555 OPEN、计划 active，原时段 UNKNOWN、旧工作树和 `.playwright-mcp/` 保留，文档仍 UNCOMMITTED。实施来源 Codex，未委派，无功能修改或新回归。

## 17. Owner 调整执行顺序（2026-10-08）

Owner 明确选择“先执行已批准的受控动作（推荐）”：五类具名动作可先按正常宿主审批执行，独立验证命令能力，实际拒绝保留原错并停止受影响步骤。加载记录不再作为这些动作的执行前置，AC-22/24 的实际加载/信任/定义与拒绝恢复验收继续保留 UNKNOWN，#555 OPEN、本计划 active；原时段 UNKNOWN 永久保留。仅调整先后顺序，复用 §15 的逐动作授权，不扩展提交/删除范围或信任/配置修改。§16 的加载优先停点为决定前快照，执行结果另记，不用成功命令推定项目定义已加载。

## 18. 本轮真实执行完成与剩余验收（2026-10-08 04:27–04:32 UTC）

按 §17 决定与 §15 的五类具名授权完成本轮正常工具执行。目标 turn/原生模式证据仍为实际 on-request/workspace-write；各写命令逐条通过 require_escalated 正常宿主入口请求后成功，工具没有独立记录人工弹窗/已有规则放行分类，该分类 UNKNOWN。命令、逐端 tip、时间戳、原始 chunk 与目标 session JSONL 行号完整登记在 [验收记录 E2](../evidence/issue-555/acceptance-2026-09-23.md)。

| 独立链路 | 实际结果 |
| --- | --- |
| commit → 双推 → 显式 base PR | canary commit=`6d331438990c458599025bccf3196fabbd694514`，仅一证据文件/5 行，实际作者及提交者 ranzuozhou，实施者 Codex；Gitee→origin 各 push exit 0、每端成功查询同 SHA；[Draft PR #571](https://github.com/MJ-AgentLab/mj-agent/pull/571) 已创建/附加，回读 OPEN/Draft、head 同 SHA、base=develop、title/body 与已批准草案完全一致 |
| 删除测试双端发布 | 两端分别普通 push 并成功查询 `refs/heads/codex/555-ac24-load-delete-20260923`，tip 固定 `9b754a690d0ef0b432d7ea431c2edda1043361b2`，与本地及两端 develop 同 tip，无新增内容 |
| 本地删除 | 删除紧前 1311 节点无祖先/后代重解析点、DELETE probe 全 AVAILABLE、1046 tracked flags=H，无 dirty/untracked/ignored/额外内容/并发变化；内容由 develop 保留，秘密仅检查元数据。正常 worktree remove、branch -d 各 exit 0，目录/元数据/精确本地 ref 各自确认不存在 |
| Gitee 引用删除 | 本地已删后从 develop 成功复查当前 ref/tip，正常 `git push gitee --delete codex/555-ac24-load-delete-20260923` exit 0；紧后该端精确 ls-remote exit 0、空输出，DELETED |
| origin 引用删除 | 独立正常 `git push origin --delete codex/555-ac24-load-delete-20260923` exit 0；紧后该端精确 ls-remote exit 0、空输出，DELETED |

五类命令本轮全部有实际结果，无新的 Git 宿主拒绝或未知响应。成功端未重复，旧已删除对象未再操作；两发布 worktree/引用与 PR #566/#571、有内容旧工作树均保留，`.playwright-mcp/` 文件未清理或暂存，哈希未变。未 force、merge、调整配置/信任或上传日志。

AC-4/9/13 本轮证据与首轮/T1–T5 分列，六项既有项目/离线验证结论保持。**AC-22/24 仍真实链路未验证/UNKNOWN**：模式变化及真实命令成功不证明项目 rules/hook 实际加载、信任或规则变化后的恢复。最小剩余事项为新目标运行的加载路径/定义哈希/版本、两种信任、加载/跳过原因/时间及与拒绝来源的可追溯关联；得到充分记录或 Owner 明确调整范围后才重评关闭。原 9 月时段 UNKNOWN 永久保留，#555 OPEN、本计划 active。

记录/计划/AGENTS 原则仍 UNCOMMITTED，未纳入 canary commit；其另行提交是独立待办。诊断请求草案仍未发送，材料先做敏感信息检查后再决定发送范围。实施来源 Codex，未委派；无产品行为改变，不新增 BDD/TDD 行为测试，复用既有离线回归。

本轮最终文档检查：frontmatter 146 canonical PASS，wikilinks 0 violations/5 根入口 0 unresolved，diff 空白与三份证据文件相对链接检查通过，均 exit 0；没有重跑功能测试或启用外部依赖。#555 已同步 E2 及原始模式/顺序决定，回读 `updatedAt=2026-10-08T04:41:10Z`、state=OPEN、正文与预备文件精确一致；现行 24 条 AC 与折叠历史逐字保持，仅六行矩阵和追加记录更新。完整 body SHA256 见验收记录 E2 同步回执。本计划仍 active / UNCOMMITTED。

## 19. 授权后取得宿主审批回执（2026-10-08）

Owner 再次授权继续剩余诊断推进。本次找到可读的非空 Desktop 日志，复核取得 E2 目标 conversationId 的 commandExecution 审批请求及同 id 的 accept 回执，覆盖请求 57/58/59/61/64/65/67/69/70/71，部分另有通知 approve action。未独立确认此前空文件与本次文件身份相同，不推定增长原因。来源路径、每行 UTC、请求链和与精确命令的跨来源关联程度详见验收记录 E3；此前无独立回执是补证前状态，未以成功推定审批。操作者身份不从 accept 推断。

本轮新 turn 第 815 行及原生 SQLite 27305181 为实际 never / danger-full-access；E2 原 turn 与逐动作结构化记录仍为 OnRequest，两时段分列。hooks/list 只有无 conversation/cwd/定义内容的路由成功记录，未取得实际加载路径、定义 hash/版本、项目/hook 信任与加载/跳过状态/原因/时间，仍 UNKNOWN；AC-22/24 未闭合。

更新完整诊断草案，准备 [精简反馈正文](../evidence/issue-555/ac24-feedback-text-2026-10-08.md)。当前正常工具目录没有反馈发送/回执查询接口，原生 Desktop 控制不可用，因此 NOT_SENT / UNAVAILABLE_DIAGNOSTIC_INTERFACE；不是授权缺失或实际宿主拒绝，未用私有接口或另起 CLI 制造结果。附件需先敏感审阅，本次未上传。最小剩余事项是取得目标加载回执或 Owner 明确调整范围；#555 OPEN、本计划 active / UNCOMMITTED，未重复 Git 动作，旧工作树及 `.playwright-mcp/` 保留。

E3 的 diff 空白与 evidence 引用检查通过；#555 同步后最终回读 updatedAt=`2026-10-08T04:55:40Z`、state=OPEN、正文与预备文件精确一致，现行 24 条 AC 与折叠历史保持，正文 hash 见验收记录 E3。本计划仍 active，未提交；反馈展示请求仅 queued，发送仍 NOT_SENT。

## 20. 反馈提交授权与正常入口拒绝（2026-10-08 05:01 UTC）

Owner 再次明确“授权执行”，反馈正文提交授权继续有效。本次工具目录已提供 node_repl + @oai/sky；初始化与只读窗口列举成功，目标应用返回 ChatGPT（OpenAI.Codex_2p2nqsd0c76g0!App）。正常窗口读取入口随后返回原错 `Computer Use was not approved to use ChatGPT`，目标 JSONL 第 1041/1042 行、05:01:30.011/020Z 和当前 turn 的关联见 [验收记录 E4](../evidence/issue-555/acceptance-2026-09-23.md)。E3 的工具缺失是此前快照；本次为实际反馈 UI 拒绝，NOT_SENT / BLOCKED_EXECUTION_ROUTE，细化审批来源 UNKNOWN，不归因于项目 rules/hook 或 E2 Git 动作。

Computer Use 技能默认排除 ChatGPT 桌面 UI；已授权的正常工具尝试仍被宿主拒绝。按 AGENTS.md 停止受影响步骤，未输入、提交、上传或换工具绕过。推荐 Owner 在原聊天 /feedback 粘贴已准备正文，未经敏感审阅的附件先不附带；另一选项是提供正常诊断入口允许目标应用的可核对条件变化，再由 Codex 续行。重复批准不替代宿主条件变化。AC-22/24 加载仍 UNKNOWN、#555 OPEN、本计划 active；已成功 Git 链路不重复，记录未提交，旧工作树与 .playwright-mcp/ 保留。

E4 GitHub 同步准备也被自动审批检查拒绝：`JavaScript execution exceeds the 64000-byte strict auto-review limit`，05:05:00.096Z、目标 JSONL 第 1104 行；提交的 JavaScript UTF-8 大小 102845 字节，超过报告上限。未取得 body-file 写入回执，未执行 issue edit，未拆分/改写或换工具绕过。本节与验收 E4 仅保存在本地；GitHub 最近已核实 OPEN / updatedAt=2026-10-08T04:55:40Z，尚未同步本节。正文准备步骤同为 BLOCKED_EXECUTION_ROUTE，计划保持 active。

## 21. on-request 核实与反馈正文送达（2026-10-08 05:08–05:13 UTC）

原 session 第 1147 行（05:08:12.549Z）直接核实新 turn=01a119e9-743b-7270-9732-f42cca305f52 为 on-request / 审批者 user / workspace-write。受限 GitHub 只读查询通过正常 require_escalated 执行原命令后成功，仍 OPEN。原 102,845 字节正文准备调用原样重试仍受 64,000 字节检查拒绝（JSONL 1187，05:09:54.082Z）；此限制未解除，GitHub 正文同步仍 BLOCKED_EXECUTION_ROUTE，不拆分载荷或换工具绕过。

Computer Use 正常窗口读取本轮通过宿主审批成功，在原聊天 Help → Send Feedback 提交已批准的精简正文，Other、两个附件选项关闭。UI 明确 Feedback submitted；原生 SQLite 27354057 与 Desktop 主日志 18256 于 05:12:54 UTC 独立证明 feedback/upload 成功、uploaded_attachments=0、attachments_failed=false，反馈 ID 同目标线程。正文指纹、回执来源与精确时间见 [验收记录 E5](../evidence/issue-555/acceptance-2026-09-23.md)。此前 UI 原拒绝保留为历史；当前窗口可用不等于项目加载或 Git 拒绝恢复。

诊断正文状态改为 SUBMITTED / 0 attachments，尚无加载诊断答复。AC-22/24 实际定义/信任/加载/跳过及与已知拒绝对应仍 UNKNOWN，原时段 UNKNOWN 永久保留；#555 OPEN、本计划 active。E4/E5 已保存本地，未 Git 提交；旧工作树和 .playwright-mcp/ 保留，未重复 Git 动作。准备 [独立状态评论草案](../evidence/issue-555/ac24-issue-comment-draft-2026-10-08.md)，推荐 Owner 另行批准以评论登记本轮结果并保留原正文停点；也可等待原入口限制解除。草案 NOT_POSTED，不将评论路线自动纳入已有正文更新批准。

具名评论草案 SHA256=B73D23E2FFB73009BA6C69A9E8E163ACFE2A941209B5447F948C0EADBBE6C486；拟议 gh issue comment 的精确命令和未知结果对账见验收 E5。E5 diff/引用/尾空白校验通过，develop 无新增 staged 内容，.playwright-mcp/ hash 未变；最终正常审批只读回查 #555 仍 OPEN / updatedAt=2026-10-08T04:55:40Z。评论未发布，正文未编辑。

## 22. 获批状态评论发布与对账（2026-10-08 05:27 UTC）

Owner 明确批准 §21 的具名状态评论，保留原正文准备停点。紧前文件 SHA256 与批准完全一致、Issue OPEN、评论查重 []；正常 gh issue comment 通过宿主审批只发布一次，exit 0，得到 [评论 6053008982](https://github.com/MJ-AgentLab/mj-agent/issues/555#issuecomment-6053008982)。正常 API 回读 createdAt/updatedAt=2026-10-08T05:27:34Z、author=ranzuozhou，1360 字符正文与获批文件逐字一致；精确命令、原始工具输出及 session 行号见 [验收记录 E6](../evidence/issue-555/acceptance-2026-09-23.md)。实际实施者 Codex，未委派。

Issue 仍 OPEN，updatedAt=05:27:34Z；其完整正文与 E3 原文逐字一致，24 条现行 AC 和折叠历史未改。E4/E5 已通过获批评论登记，完整正文准备继续 BLOCKED_EXECUTION_ROUTE，不将评论成功认作限制解除。反馈已提交、附件 0，但加载诊断未取得；AC-22/24 UNKNOWN、原时段 UNKNOWN 永久保留、本计划 active。最小剩余事项为可追溯目标加载诊断及逐项核对，或 Owner 明确调整范围；本轮没有新 Git 动作，工作区记录未提交，旧工作树与 .playwright-mcp/ 保留。

## 23. 新增记录核查与剩余验收选项（2026-10-08 06:19 UTC 快照）

Owner 回复“执行”后，Codex 继续只读取证并准备范围选项，未委派。目标 JSONL 第 1518 行证实当前新 turn `01a11a25-9f6f-7c50-8b68-38b6ceefc24d` 为 never/user/danger-full-access，独立于 E2 的 OnRequest 执行窗口。SQLite 05:12:54–06:19:56 UTC 固定秒区间中，目标线程 429 行、线程/进程合计 2476 行；唯一相关候选仍是附件 0 的既有 feedback/upload 回执。Desktop 新增 12 条 hooks/list 的 conversationId=null，无定义/哈希/信任/加载结果；另 16 条 core.hooksPath 候选均为 Git 日志，没有作为 Codex hook 回执。补充检查的两处目标 hook 输出目录不存在；这些缺失均不能证明未加载。具体路径、行号、SQL 条件、原始输出坐标和字段结论见 [验收记录 E7](../evidence/issue-555/acceptance-2026-09-23.md)。

正常只读 GitHub 查询仍 OPEN、仅有 §22 的具名评论、完整正文与 E3 一致；没有取得新的可追溯诊断。当前可用工具没有目标加载/反馈答复查询接口；官方反馈文档没有提供所需的答复查询承诺。没有新上传、Git 写操作、配置/信任修改或历史拒绝路线重试，既有发布对象、旧 dirty 工作树和 .playwright-mcp/ 保留，记录仍未提交。

已准备 [Owner 选项与明确范围调整草案](../evidence/issue-555/ac24-remaining-scope-options-2026-10-08.md)。推荐继续保留现行 AC-22/24，索取 E2 实例的独立加载报告；若该实例也无记录，先准备可观测新会话采集方案再另行批准具名动作。替代选项明确将实际加载及该加载与恢复的关联从本 Issue 关闭条件中移出，UNKNOWN 和原始拒绝保留；此选项尚未批准，不能当作恢复或验收通过。现行计划继续 active、#555 OPEN，不建议关闭。

本轮文档校验 PASS：146 canonical frontmatter、archive-ref 0、根入口链接 0；对本轮四份文件另外校验相对链接/尾空白和 diff，均通过。暂存区为空，冻结评论与 .playwright-mcp/ 哈希不变；没有用这些静态结果代替 AC-22/24 加载证明。详细命令/退出码见验收记录 E7。

## 24. 方案 A 获批与支持账户停点（2026-10-08 06:54 UTC）

Owner 选择推荐方案 A 并授权执行，保留 AC-22/24 的现行加载要求；方案 B 未批准。Codex 只读检查新增日志，仍没有可追溯加载报告；两个同进程/不关联目标线程的 SQLite 候选原文在后查时不可得，标 UNKNOWN，未推断加载或未加载。当前 turn 的 never 与 E2 OnRequest 分列。详细来源/查询窗口见 [验收记录 E8](../evidence/issue-555/acceptance-2026-09-23.md)。

通过正常 OpenAI 官方支持网页聊天已发送 [1469 字符具名请求](../evidence/issue-555/ac24-support-request-2026-10-08.md)，发送前与批准内容核对一致；界面 You said 回读正文，随后要求账户邮箱，没有诊断答复/案件回执。Owner 选择在页面登录或填写邮箱，最新可见状态仍等待账户输入；已保留支持页面。没有读取或填写凭据，也没有附件上传。支持请求与原 Desktop feedback、完整 Issue 正文准备的已知拒绝分开，未重试该受阻路线。

恢复入口：Owner 完成该页面账户步骤后，Codex 沿用方案 A 授权继续核对支持答复；需要附件时先准备脱敏具名材料，另交 Owner 审阅。没有新 Git 动作、Issue 写入或信任/配置修改；计划 active、#555 OPEN、AC-22/24 加载 UNKNOWN、工作区记录 UNCOMMITTED，旧 dirty worktrees 与 .playwright-mcp/ 保留。截图仅保存到本地审阅，不作为历史加载证明。

文档校验 PASS：frontmatter 146 件、archive-ref 0、根入口未解析链接 0；另核对本轮五份 Markdown 相对链接/尾空白及 diff，通过。具名支持正文/截图、冻结评论与 Playwright 文件哈希一致，暂存区空。命令、退出码与输出坐标见验收记录 E8。

## 25. 账户步骤完成与人工支持升级（2026-10-08 07:12 UTC）

Owner 回复“完成登录，继续执行”，Codex 沿用方案 A 的推进授权。原支持聊天显示“已收到邮件”，账户停点解除；已发送后续字段请求，正常点击页面“升级”，并回读“已请求人工支持专员介入”与“已升级给支持专员”。页面说明答复也将通过邮件发送，但没有案件编号、人工答复或加载诊断。状态 HUMAN_SUPPORT_ESCALATION_CONFIRMED / WAITING_FOR_DIAGNOSTIC_RESPONSE。精确 JSONL 坐标、UTC、call_id 和本地原始截图哈希见 [验收记录 E9](../evidence/issue-555/acceptance-2026-09-23.md)。§24 是此前账户停点快照。

当前记录 turn 的 never 与 E2 的 OnRequest 窗口分列；升级回执仅证明支持转交，不证明目标实例实际加载。AC-22/24 的来源、定义哈希、信任、加载/跳过及恢复关联仍 UNKNOWN；#555 只读复核仍 OPEN，计划 active，B 范围调整未批准。下一步取得并逐字段核对该支持聊天/邮件的具名诊断；无法取得时再提交可观测新实例方案或明确范围调整供 Owner 决定。

本轮未读取账户邮箱/凭据或邮箱内容，未上传附件、修改信任/配置或新增 Git/Issue 写操作；不重复已完成命令，64 KB 原始拒绝仍保留。证据/计划仍 UNCOMMITTED，旧有内容工作树及 .playwright-mcp/ 保留。若支持需要附件，先准备最小具名脱敏清单供 Owner 审阅授权，不将方案 A 推进批准扩展为附件批准。

文档校验通过：146 canonical frontmatter、archive-ref 0、根入口未解析链接 0；四份更改记录的相对链接/尾空白及 diff 通过，冻结具名文件与原始截图哈希一致。命令、退出码和来源见 E9；校验不改变加载 UNKNOWN。

## 26. 支持专员首答与诊断待办（2026-10-09 07:51–07:54 UTC 观察）

只读检查原支持聊天，新增署名 Chinedu / OpenAI Support 的答复。专员将检查既有反馈、确定历史记录可访问性，并区分 10 月 8 日与 9 月 23 日实例；目前尚不能确认历史加载、信任、记录保留覆盖或六类字段能否重建。当前无需上传材料、重跑 Git 或修改信任/配置。页面没有消息发送时间、案件编号或原始事件报告；观察时间不作为发送时间。来源、原始 JSONL 坐标、截图哈希及逐字段核对见 [验收记录 E10](../evidence/issue-555/acceptance-2026-09-23.md)。

状态 SUPPORT_SPECIALIST_REPLY_RECEIVED / WAITING_FOR_HISTORICAL_DIAGNOSTICS；AC-22/24 的加载及恢复关联仍 UNKNOWN，计划 active，#555 只读复核仍 OPEN。下一步取得该目标对话的具名诊断材料；不能把“尚不能确认”改写为记录不存在，也不以首答替代验收。Owner 当前无新增上传或重跑动作；材料请求出现后再准备具名脱敏清单。

此前定时检查仅有 suggested_create 卡片回执；本次本地 automation.toml 未匹配该任务，没有创建/启用/运行 ID 可核对，实际调度状态 UNKNOWN。未重复创建、变更或声称暂停任务；若继续等待实质诊断，应先定位精确任务并明确停止条件。仅更新本地记录，未 Git/Issue 写入，64 KB 停点、旧工作树和 .playwright-mcp/ 保留。

记录校验通过：147 canonical frontmatter、archive-ref 0、根入口未解析链接 0；四份更改记录的相对链接/尾空白与 diff 通过，原始截图及冻结文件哈希一致、暂存内容为空。命令/退出码与来源见 E10，不作为加载验收。

## 27. 验收一致性核对与记录交付准备（2026-10-09）

Owner 接受同步准备建议。Codex 按 [现行 24 条快照](../evidence/issue-555/current-clauses-2026-10-09.json)及 [一致性审阅](../evidence/issue-555/consistency-review-2026-10-09.md)复核：22 项在各自条款范围内已验证，AC-22/24 actual-loading/recovery 仍 UNKNOWN；六项原静态条款的通过不扩展为宿主加载。原时段已核实 Desktop 版本与加载 UNKNOWN 分列，支持 E10 首答不补齐诊断，#555 OPEN、计划 active。

新 documentation 工作树与分支 `documentation/555-acceptance-records-20261009` 已通过正常 git worktree add 创建，基线 `0b2f542e466fe36258046c7e8592ed6770e983f2`（本地/origin develop）。Gitee develop=`4e55aae9d78f59ce9b47be43171b5fb33fe95049` 是其祖先，0/2；本次不推送或同步 develop。两端新分支及现存同 head PR 均未发现，获批执行前须重查。精确绝对工作树、对象、命令及工具回执见 [验收记录 E11](../evidence/issue-555/acceptance-2026-09-23.md)。

推荐记录包 15 份（14 evidence、1 本计划），准备两项 docs 提交、Gitee→origin 普通新分支双推、显式 base=develop 的 Draft PR；另备独立状态评论草案。未 git add、commit、push、创建 PR 或公开评论；旧 canary 授权不覆盖本记录交付。公开仓库中的本机路径/线程标识/支持截图展示范围随文件哈希清单交 Owner 审阅；commit、普通 push、PR 创建与评论发布分别批准。AGENTS 两行治理原则另行保留，Playwright 与三条有内容旧工作树不纳入、不删除。

纯记录范围无 runtime、守卫或配置变更，复用既有 T1/T2，不重复功能测试；文档校验与文件哈希结果登记 E11。本地审阅清单不作为授权凭证，工作树和原始拒绝保留，未绕过完整正文 64 KB 停点。下一步可以在具名动作获批后交付这些记录，剩余验收继续等待目标实例实质诊断或 Owner 明确调整范围；新会话结果不回填原时段 UNKNOWN。

源记录校验 exit 0：147 canonical frontmatter、archive-ref 0/根入口 unresolved 0，15 文件相对链接/尾空白和 JSON/24 条矩阵核对通过；五份冻结文件及 Playwright 哈希一致，cached diff 空。详细命令、UTC、chunk 及扫描边界见 E11；复制后的目标工作树检查与最终清单另备本地审阅。

## 28. 具名记录交付完成，加载验收继续 active（2026-10-09）

Owner 对清单推荐 A 与独立推荐 D 回复“接受推荐，授权执行”。Codex 按冻结 manifest SHA256=`36b1531f0a30e2e5141f4fd143e0c2978d7e5b4224fe6d9d9a581fcc215ced40` 分别执行：14 evidence 提交 `77c382626b8f52f34bbda279c2b4956f274903b5`；仅 Plan 提交 `837c4b49b20c2484a878aad398c643e4ffc71852`；Gitee→origin 普通新分支双推，两端独立查询 tip 与第二提交一致；显式 head=documentation/555-acceptance-records-20261009/base=develop 的 [Draft PR #574](https://github.com/MJ-AgentLab/mj-agent/pull/574)；独立 [状态评论 6077631045](https://github.com/MJ-AgentLab/mj-agent/issues/555#issuecomment-6077631045)。实际文件/blob、作者/提交者、PR/评论正文哈希、UTC 和逐动作工具回执均核对，详见 [E12](../evidence/issue-555/acceptance-2026-09-23.md)及 [本地执行回执](../evidence/issue-555/records-delivery-receipt-2026-10-09.json)。

本轮实际记录发布完成，原本 E11 的未提交/待批准状态保留为准备时快照；新工作树仍保存该批准快照并保留，两次提交已双推。当前本文件 §28 与 E12/导读/receipt 是其后新增的原 develop 本地 UNCOMMITTED 增量，不扩展冻结文件授权再提交。AGENTS 两行原则、.playwright-mcp/、三条有内容旧工作树及检查生成的 ignored pyc 保留；没有 force、merge、close、删除、信任/配置修改或新增附件/支持消息。完整正文 64 KB 停点未重试，独立评论不替代受阻正文路线。

当前工具权限声明 never 与历史 Desktop 模式、实际加载各自分列；正常命令成功不是加载证明。AC-22/24 actual-loading/recovery UNKNOWN，原时段 UNKNOWN 永久保留，#555 OPEN、计划 active。支持仍等待 E10 后的实质诊断，定时任务实际启用/运行未核实。最小剩余验收仍为目标实例可追溯加载/信任/哈希/时间/模式及恢复关联，或 Owner 明确调整剩余范围；本次不建议 merge 或关闭。

本地增量校验 frontmatter 147 PASS、wikilinks 0/0、相对链接/尾空白/receipt JSON、冻结 15 文件/manifest、截图/评论/支持正文/Playwright 哈希与旧工作树内容统计均通过；目标 clean、源 index 空。Issue 正文完整哈希未变，本轮只新增批准评论，仍 OPEN。具体工具 chunk/exit 见 E12；没有新的功能测试或宿主加载诊断。

## 29. PR 链已合并，保护成果与准备同步（2026-10-09）

Owner 要求继续合并后工作，Codex 按 post-merge 技能复核：当前无 OPEN PR，#566/#571/#574 均 MERGED；merge 分别为 `4334a57729137255aa79855d06609a578dd218c2`、`2f707200b166eca9120319779f6ae971f6ac43ba`、`c449dff6baec64b874f899431109fb3542e0ff4f`。最终 head 来自合入 develop 的 merge，均保留原 tip。正常 fetch 对象和远端跟踪引用后核对祖先及路径；未同步 dirty develop 工作树。精确 final head/UTC/工具回执见 [E13](../evidence/issue-555/acceptance-2026-09-23.md)。

origin develop 已到 `c449dff6baec64b874f899431109fb3542e0ff4f`，Gitee develop 仍为 `4e55aae9d78f59ce9b47be43171b5fb33fe95049`。三条发布引用两端 tip 不同，远端删除保留暂停；两个 canary 工作树清洁，记录工作树有十份 ignored pyc，均保留。原 develop 有 AGENTS 两行原则及 E12/Plan 等未提交成果，按 sync H1 先准备固定 16 路径原字节备份、具名保存/ff/恢复清单；.playwright-mcp/ 和其他任务旧工作树不暂存、不删除。原固定文件交付授权不包含本地保存/同步的新增范围或 develop 镜像 push，需 Owner 选择具名推荐方案。

推荐保存后只 fast-forward 本地 develop，再从核对备份恢复 16 路径、保留 stash/备份；Gitee 镜像通过项目守卫仅 ff，push 独立批准。本轮只准备，没有 stash/reset、保存后的恢复、同步、镜像 push、新 commit/PR、删除或新的 Issue/支持消息。CHANGELOG/EVAL 均不触发，剩余验收复用 #555，不另开任务。

原支持对话只读核查仍是 Chinedu 首答，没有实质加载诊断；保持 AC-22/24 UNKNOWN、#555 OPEN、计划 active。PR 合并不补齐宿主加载，不改变原时段 UNKNOWN，也不解除完整正文 64 KB 停点。当前本节/E13/回执为原工作区 UNCOMMITTED 增量。后续取得目标实例可追溯诊断或 Owner 明确调整范围后，再评估完成状态。

本轮文档校验 147 frontmatter PASS、wikilinks 0/0、E13 链接/尾空白/diff 与保留内容核对通过，详见 E13。源 cached diff 空，acceptance 仍有 intent-to-add；具名保存方案将处理该元数据，不把原未跟踪记录视为可直接覆盖。

## 30. 获批保存/快进/恢复与独立镜像、评论执行（2026-10-09）

Owner 接受合并后审阅清单推荐 A 与独立 D，Codex 分别执行获批范围。19 份外部原字节备份保留；16 路径保存于 stash=`62a9170a4ca83c2ad425a7a4670e62df70a90e99`，各保存树 blob 已核对。原 autostash=`9bd7628f4abc7073df120295a947d36fe65c6695` 保留。仅本地 develop fast-forward 至 `c449dff6baec64b874f899431109fb3542e0ff4f`，随后从固定备份恢复十六路径原字节；raw SHA/working blobs、十九份备份、八份排除内容哈希全部匹配，index clean、五份本地原增量仍未提交。没有新 merge commit、stash pop/drop 或旧文件清理。

独立 Gitee develop 守卫普通 ff 补齐 25 commits；分别查询 Gitee/origin 实际 refs/heads/develop 均为 `c449dff6baec64b874f899431109fb3542e0ff4f`，未推 origin develop/发布分支。独立精确 [准备快照评论 6078621332](https://github.com/MJ-AgentLab/mj-agent/issues/555#issuecomment-6078621332) 于 `2026-10-09T09:56:29Z` 发布并回读 raw SHA 匹配，Issue OPEN，完整正文 hash 未变。§29 的未同步描述及评论原文保留为准备快照，实际命令、普通错误/警告、UTC、chunk/exit 见 [验收 E14](../evidence/issue-555/acceptance-2026-09-23.md) 和 [执行回执](../evidence/issue-555/post-merge-sync-receipt-2026-10-09.json)。

所有旧工作树、三条发布分支/两端引用、ignored 内容及 .playwright-mcp/ 保留。没有新项目 commit/PR、PR merge、删除、信任/配置修改、支持消息或附件。E14/本节/回执是恢复后的 UNCOMMITTED 增量，不改写 manifest、stash 或备份。当前声明 never/danger-full-access 与历史 OnRequest 和实际加载分列；命令成功不补齐加载验收，64 KB 完整正文准备拒绝仍 BLOCKED_EXECUTION_ROUTE。

AC-22/24 实际加载及恢复关联仍 UNKNOWN，原时段 UNKNOWN 永久保留；支持最近来源仍为 E13 的只读观察，本轮无新诊断。保持 #555 OPEN、计划 active。最小剩余项为可追溯目标实例加载/信任/来源版本或哈希/事件时间/有效模式及恢复关联，或 Owner 明确调整范围；不建议关闭。实施者 Codex，未委派，BDD/TDD=NONE；只做记录验证，不重复功能回归或运行 infra。

记录校验 exit 0：147 frontmatter PASS、wikilinks archive-ref/root unresolved 0/0、四份 Markdown 的 79 个相对链接和尾空白、post-merge JSON、diff --check、Plan active、index clean 均通过，见 [校验回执](../evidence/issue-555/post-merge-validation-2026-10-09.json) 与 E14。十九份备份、冻结文件、八份排除内容、两个 stash 和三条有内容旧工作树的保留核对通过；不作为实际加载验收。

工作树并非 clean：Git 内容 diff 为五路径，实际 status 有十三份未暂存 M；另外八份冻结文件原字节 SHA 匹配备份、Git 属性处理后的 blob 匹配 HEAD。为保留获批原字节，不规范化或重新暂存，详细路径见执行回执/E14。index clean 与上述工作区状态分别报告。
