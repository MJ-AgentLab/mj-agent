# Issue #555 验收证据矩阵与受控对象清单（2026-09-23）

当前导读（E11，2026-10-09）：以下首段依据日期是首次验收快照。最新逐条核对以 [现行 24 条快照](current-clauses-2026-10-09.json)、[一致性审阅](consistency-review-2026-10-09.md) 和本文 E11 为准。现行条款范围内 22 项已验证，AC-22/24 的实际加载及恢复关联仍 UNKNOWN；支持首答不替代诊断。#555 OPEN、计划 active。E1–E10 各时点结果及原始拒绝保留，新的记录交付仍待独立动作批准。

依据：[#555 当前正文](https://github.com/MJ-AgentLab/mj-agent/issues/555)（`updatedAt=2026-09-22T07:06:27Z`）、[ADR-041](../../decisions/ADR-041_Command_Specific_Git_Execution_Policy.md)、[实施计划](../../plans/[PLAN]_555_approved_deletion.md) §11，以及已合并的 [#558](https://github.com/MJ-AgentLab/mj-agent/pull/558)、[#560](https://github.com/MJ-AgentLab/mj-agent/pull/560)、[#561](https://github.com/MJ-AgentLab/mj-agent/pull/561)。Issue 折叠的旧方案只作历史证据。`已验证` 指该项要求的离线或报告性检查已有实际结果；`仅静态验证` 指项目源码、文档或检查器已核对，但目标宿主加载/执行未得到证明；`真实链路未验证` 指该项明确要求的独立受控会话或双远端动作尚无完整结果。没有整项 AC 被新决策取消；旧方案中 AC-4/9/13 的统一 on-request 前置条件已被 ADR-041 与 Issue 当前条款替代。

## 证据索引

| 代号 | 本次与既有证据 | 边界 |
| --- | --- | --- |
| P558 | #558 MERGED，merge `cfb2ea339452a752c01503bf2e6856f2964673e4`，head `f3001bd3a5a656d60f64fe29ea84df188e5bc96e` | 删除前核验与五类动作比较；PR 正文明确真实链路未验收 |
| P560 | #560 MERGED，merge `b577fb690dffb31b80d7e72b45dda3bc310c6738`，head `bc8ce154017e6d122b87245931f60b9153c278df` | 旧条件下 commit、双推、显式 base PR 的既有执行证据；不是本次临时对象的 AC-9/24 |
| P561 | #561 MERGED，merge `8a029e7bb3f29af4bd510b916e6bafbeaaf4b074`，head `5177274a03dc1214a3e9d730d046fed7bdaffdb5` | 本轮规则、hook、诊断和文档；PR 正文仍保留 AC-4/9/13/24 |
| T1 | `uv run --frozen --no-sync python scripts/sdd/run_offline_pytest.py tests/unit/test_deletion_targets.py tests/unit/test_codex_native.py tests/unit/test_git_hook_review.py tests/unit/test_git_action_review.py tests/unit/test_native_migration_guards.py tests/unit/test_guard_git_workflow_hook.py tests/unit/test_native_governance.py tests/unit/test_native_skill_contracts.py -q`：230 passed、30 subtests passed，exit 0 | 定向离线回归，不证明宿主执行 |
| T2 | `uv run --frozen --no-sync python scripts/sdd/run_offline_pytest.py tests/unit -q`：1095 passed、1 skipped（非 Windows）、30 subtests passed，exit 0；1 条上游 Pydantic 弃用 warning | 全量离线单元回归；外部依赖仍按离线策略隔离 |
| T3 | `check_codex_native.py --effective-approval-policy never`：`STATIC_PASS`、`PER_COMMAND`、`rule_loading=UNKNOWN`、`host_enforcement=NOT_TESTED`；`check_native_skills.py`、`check_native_governance.py --surface entries/consumers` 均 `STATIC_PASS`，exit 0 | 有效模式 `never` 来自当前任务权限声明；加载来源仍未知 |
| T4 | `ruff check`、`mypy src/mj_agent`（48 文件）、`check_frontmatter.py`（146 篇）、`check_wikilinks.py`（0 违规、5 个根入口 0 unresolved）均 exit 0 | 文档/代码静态及本地执行检查 |
| T5 | `check_codex_approvals.py --effective-approval-policy never --action commit --action push --action pr_create`：exit 0，项目 Git/gh `NO_MATCH`、hook 静态 `TASK_AUTHORIZATION_CONTEXT`；本地删除加远端删除筛选：exit 1 仅因 `Remove-Item` 为 `prompt×never`，Git 清理与远端删除为 `NO_MATCH` | 诊断器自身明确 `rule_loading=UNKNOWN`、`host_enforcement=NOT_TESTED`，不是宿主授权 |
| R1 | `git ls-remote --heads gitee` 与 `git ls-remote --heads origin` 均 exit 0，2026-09-23 只读查询：`codex/555-approval-regression`、`codex/555-command-policy` 两端均不存在；`maintain/555-approved-deletion` 仍存在，Gitee `b2706ea93d01630f231c39fe9b95781f8ab94cbe`、origin `f3001bd3a5a656d60f64fe29ea84df188e5bc96e` | 前两支已缺失，不重复删除；第三支 tip 不同且非本次临时对象，保留 |
| W1 | `git worktree list --porcelain` 与逐工作树 `git status --porcelain=v1 --untracked-files=all`：develop 原先干净；旧 `maintain/499-enforcement-blocking` 2 修改，`maintain/552-codex-approval-preflight` 5 修改+1 未跟踪，`maintain/codex-dev-mode-migration` 7 修改+475 未跟踪 | 均保留，不用当前 #555 清理授权消费；develop 有忽略内容，亦不作为删除目标 |
| E2 | 2026-10-08 04:27–04:32 UTC 的第二轮具名动作：commit `6d331438990c458599025bccf3196fabbd694514`、独立双端发布、Draft PR #571、本地测试 worktree/branch 删除、独立双端 ref 删除；原始命令、工具 chunk、时间及目标 JSONL 行号见末节 | 本轮实际 on-request/workspace-write；经正常 require_escalated 宿主入口执行，人工弹窗/已有规则放行的分类未独立记录；加载仍 UNKNOWN |

## AC-1～AC-24

| AC | 结论 | 证据与仍缺少的事实 |
| --- | --- | --- |
| 1 | 已验证 | Owner 一次批准五类具名动作后，S/A/B 本地和远端清理均按清单执行，没有对同一对象重复索取批准；P558/P561 与 T1 为规则/回归依据。 |
| 2 | 已验证 | `test_deletion_targets.py` 的临时 Git、tracked/dirty/untracked/ignored、备份失败、路径逃逸、重解析点与 Windows 占用探测在 T1/T2 通过；真实删除前仍须按当时对象重检。 |
| 3 | 已验证 | 现行条款允许回归/会话验收；T1/T2 的临时 Git 与动作矩阵实际运行，覆盖内容/路径/范围变化、撤销输入、其他 worktree 和部分成功，本次受控会话也未把批准扩展到其他动作。真实 Owner 撤销未人为制造，离线夹具不充当真实授权。 |
| 4 | 已验证 | 首轮逐对象核验后正常清理 S/A/B；E2 的单一测试 worktree 1311 节点均无重解析点/占用/并发变化，1046 tracked flags=H、无 dirty/untracked/ignored，内容由 develop 同 tip 保留；正常 worktree remove、branch -d 各 exit 0 并独立确认目录/元数据/分支不存在。T5 的 Remove-Item 冲突没有套给 Git，也未调用该命令。 |
| 5 | 已验证 | T1/T2 覆盖 Never、index.lock/权限、网络和未知来源样本；#560 与计划 §10 保留过往原始 Never 拒绝，当前任务未制造新拒绝。 |
| 6 | 已验证 | 按该项指定的原生检查器、文档反扫和守卫正反回归，P558/P561 与 T1/T3 覆盖有限 hook、UNKNOWN/FORBIDDEN、G1/G2 和检查器一致性；目标 Desktop 实际加载另由 AC-22/24 保留 UNKNOWN。 |
| 7 | 已验证 | T3/T5、首轮 never 与 E2 OnRequest 执行分别记录。E3 已取得目标 conversationId 的审批请求、同 id 的 accept 及部分通知 approve action；未由成功推断审批。当前新 turn 已为 never/danger-full-access，不回写 E2。项目实际加载仍 UNKNOWN，单列 AC-24。 |
| 8 | 已验证 | Owner 在同一回复分别批准五类动作，实际执行未把删除授权扩展到发布、未执行 merge；T1/T2 覆盖只授权一类/撤销/变化。 |
| 9 | 已验证 | 首轮 commit 878b474...→双推→显式 base Draft PR #566；E2 commit `6d331438990c458599025bccf3196fabbd694514`→独立两端查询同 SHA→base=develop 的 Draft PR #571，head/title/body 精确回读一致。E3 补得对应目标审批请求/accept，具体命令通过同线程唯一调用时段及 JSONL 跨来源关联，Desktop 回执行不含 argv；加载缺口仍列 AC-24。 |
| 10 | 已验证 | origin 首次 push 连接重置后记 UNKNOWN，不盲重试；成功查询证实远端缺失后才续推，随后逐端对账；T1/T2 覆盖拒绝重试及响应丢失场景。 |
| 11 | 已验证 | 本矩阵把本地删除、两端远端引用和发布链路分列，T3/T5 与 R1 分清项目变更、模式声明、静态检查、实际执行；真实缺口逐项保留。 |
| 12 | 已验证 | S/A/B 分别绑定 Gitee/origin 精确 ref、批准时和执行前 `407e...` tip；与 develop 同 tip 的合并证据、保护分支排除及 T1/T2 反例齐备；远端删除与普通 push 独立批准。 |
| 13 | 已验证 | 首轮 S 在本地分支已删后单删、A/B 批量删，逐端逐引用成功查询确认不存在；E2 新建双端测试 ref，均核实 tip=`9b754...`，本地对象移除后再独立 Gitee→origin 删除，每端成功 ls-remote 空输出。失败/响应丢失变体由 T1/T2 覆盖，不伪称本轮实际发生；旧已删分支未重复删除。 |
| 14 | 已验证 | `test_git_action_review.py` 合成计划 completed 但未提交场景在 T1/T2 通过；本记录和计划保持 active/未提交，旧 #552 工作树单列保留。真实清理状态已按下文逐对象记录。 |
| 15 | 已验证 | `.codex/rules/mj-agent.rules` 当前仅四条：Remove-Item prompt、三个 DB forbidden；P561、T3/T5、规则集合断言及反扫满足现行条款；目标 Desktop 加载另见 AC-24。 |
| 16 | 已验证 | P561、T1/T2 的 hook 协议正反例证明识别成功时输出 `TASK_AUTHORIZATION_CONTEXT`，G1/G2/merge 等仍阻断；目标会话 hook 加载另见 AC-24。 |
| 17 | 已验证 | P561 的 `test_git_command_policy.py` 在 T2 覆盖重复消息、等号、消息文件、引号/argv 和互斥/缺值。 |
| 18 | 已验证 | P561 的命令参数与 `test_git_action_review.py` 临时 Git 引用用例在 T1/T2 覆盖 upstream 换序、显式 refspec、拒绝 force/空源/通配。 |
| 19 | 已验证 | T1/T2 覆盖短/全 ref、单/多分支、逐目标 tip/合并与批次暂停；A/B 批量删除在 Gitee 与 origin 均有逐引用实际结果。 |
| 20 | 已验证 | P561 的 `test_git_command_policy.py` 与 G2 负例在 T2 覆盖 PR 短参数/等号、base、重复冲突与缺值。 |
| 21 | 已验证 | T5 在当前文件上证实 Git/gh 不因 never 单独阻断、Remove-Item 仍冲突；T1/T2 覆盖预检 CLI/JSON、三种模式、动作矩阵、损坏规则与只读性。`check_git_actions.py` 的真实 Gitee 查询 UNKNOWN 仍单独记录；实际宿主加载另见 AC-24。 |
| 22 | 真实链路未验证 | T1/T2 与首轮网络 UNKNOWN→对账→续推证据保留。历史 Desktop `26.917.51856/build 10492/prod` 已核实，原时段加载永久 UNKNOWN。Owner 批准新会话补验并随后允许先执行五类动作；E2 核实模式改为 on-request、正常宿主入口下五类命令成功，未出现新 Git 拒绝，但不据此证明项目定义加载或规则变更后的恢复。加载/信任/版本及与已知拒绝来源的对应关系仍 UNKNOWN，整项未闭合。 |
| 23 | 已验证 | P561 涵盖入口/政策/共用边界/五技能/两指南、Plan/ADR/CHANGELOG/INDEX；T3/T4 与定向 `rg` 反扫通过，历史旧语义仍按时点标注，满足本项指定文档/治理检查。 |
| 24 | 真实链路未验证 | 首轮 never、E2 实际 OnRequest 的具名 Git 链路与逐端证据保留；E3 补得目标正常宿主审批请求/accept，部分通知有 approve action。历史 Desktop `26.917.51856/build 10492/prod` 已核实，原时段加载/信任/版本永久 UNKNOWN；新实例项目实际定义加载亦 UNKNOWN。hooks/list 路由成功无 cwd/定义/hash/信任/加载结果，不替代；E3/E4 的 never、E5 新 turn 的 on-request/user 与 E7 当前 never 分列。E5 反馈正文已送达、附件 0；E7 新增记录仍无独立加载证明。整项仍未闭合。 |

## 临时对象与拟执行顺序：批准前快照（实际结果见下文）

仓库：GitHub `https://github.com/MJ-AgentLab/mj-agent`（`origin`），Gitee `https://gitee.com/ranzuozhou/mj-agent.git`（`gitee`）。起点 `develop=407e06877fbb8913fe2f702c8601a16f8ba41fb9`；两端 `refs/heads/develop` 在 R1 的成功查询均为该 SHA。所有临时分支由 `git worktree add ../codex/<branch> -b <branch>` 创建，当前本地 tip 均为起点。2026-09-23 查询两端临时 ref 和同名 PR 均为空；任何后续出现、tip 变化或未授权新增内容都暂停受影响项。

| 用途 | 绝对工作树 | 精确本地与预期远端引用 | 当前 tip / 内容 |
| --- | --- | --- | --- |
| AC-9/24 发布 | `D:/workspace/10-software-project/projects/mj-agent/codex/555-ac9-publish-20260923` | `refs/heads/codex/555-ac9-publish-20260923` | `407e06877fbb8913fe2f702c8601a16f8ba41fb9`；只暂存 `ac9-canary-20260923.md`（blob `1ab6c9302fec7faa35e9b8d545aef92c681bd898`）和 `ac9-pr-body-20260923.md`（blob `5ea3b911f52cf3270f9fade9ff0ce0a7cdd529c4`），未跟踪=0；新 commit SHA 只能提交后获知 |
| AC-13 单分支 S | `D:/workspace/10-software-project/projects/mj-agent/codex/555-ac13-delete-20260923` | `refs/heads/codex/555-ac13-delete-20260923` | `407e06877fbb8913fe2f702c8601a16f8ba41fb9`；clean，未跟踪/忽略=0；与 develop 同 tip 即合并证据，无新增提交 |
| AC-13 批量 A | `D:/workspace/10-software-project/projects/mj-agent/codex/555-ac13-batch-a-20260923` | `refs/heads/codex/555-ac13-batch-a-20260923` | 同上；clean，未跟踪/忽略=0，已由 develop 包含 |
| AC-13 批量 B | `D:/workspace/10-software-project/projects/mj-agent/codex/555-ac13-batch-b-20260923` | `refs/heads/codex/555-ac13-batch-b-20260923` | 同上；clean，未跟踪/忽略=0，已由 develop 包含 |

五类动作分开授权：

2026-09-23 03:09 UTC 的预检：三个删除候选的绝对路径均在具名 `.../mj-agent/codex/` 下，目标目录不是重解析点；各自 `git status --porcelain=v1 --ignored --untracked-files=all` 为 0 行、HEAD 都是 `407e...`。这是当前快照，实际删除紧前仍要复核祖先/后代、占用和并发变化；不以这次预检替代执行时核验。

1. **commit**：仅发布 worktree 的以上两个已暂存文件，拟 `git commit -m "docs(evidence): add #555 controlled delivery canary"`。执行紧前复查分支/HEAD、index blob、`git diff --cached --check` 和未暂存/未跟踪/忽略内容；成功后记录 SHA、文件集、作者和状态。计划/本矩阵自身未纳入此提交。
2. **普通 push**：先发布分支 `git push gitee codex/555-ac9-publish-20260923`、再 `git push origin codex/555-ac9-publish-20260923`；S/A/B 各自先 Gitee 后 origin，以相同 `git push <remote> <branch>` 创建测试引用。每次前查询两端精确目标是否仍不存在，发布分支源 tip 为新 commit，删除候选源 tip 固定为 `407e...`；每步后 `git ls-remote --heads <remote> refs/heads/<branch>` 独立核实完整 SHA。某端成功后不得重复。
3. **PR 创建**：仅发布分支，拟 `gh pr create --repo MJ-AgentLab/mj-agent --head codex/555-ac9-publish-20260923 --base develop --title "docs(evidence): verify #555 controlled delivery canary" --body-file evidence/issue-555/ac9-pr-body-20260923.md --draft`；先确认 origin 分支 tip 与本地提交相同、同 head/base 无 PR；响应丢失先 `gh pr list/view` 对账。创建后记录 URL、head/base/正文，保持 Draft，不自动 merge。此测试 PR 的后续关闭/删除另行决定。
4. **本地删除**：只针对 S/A/B 三个新建且清洁的 worktree 与本地分支；拟从 develop 执行每个 `git worktree remove ../codex/<name>` 后 `git branch -d codex/<name>`。S 可在远端删除前执行，以实测“本地分支已不存在仍可远端删除”；A/B 在远端删除后执行。紧前核验绝对路径、Git 跟踪/未提交/未跟踪/忽略、重解析点、占用及必要备份；任一变化暂停该目标。`Remove-Item` 另有项目 prompt，当前 never 下静态诊断 INCOMPATIBLE，本清单不请求用它执行。
5. **远端引用删除**：仅 S/A/B 三条，Gitee → origin。单分支命令为 `git push gitee --delete codex/555-ac13-delete-20260923` 与同形态 `origin`；批量命令为 `git push gitee --delete codex/555-ac13-batch-a-20260923 codex/555-ac13-batch-b-20260923` 与同形态 `origin`。批准时和执行紧前逐端逐 ref 核对 tip 都为 `407e...`、develop 包含该提交、保护分支排除、两端无异；批内任一目标变化则暂停该批。每次后成功查询每端每条 ref 的缺失；查询失败记 UNKNOWN，不推定已删。先端成功次端失败时只对账并续做合规的失败端，不改变命令形态绕过已知拒绝。

精确预期命令如下。每条命令仍以前置核验、对应动作授权和上一条实际成功为条件；清单不是批量执行脚本。

```text
# cwd: D:/workspace/10-software-project/projects/mj-agent/codex/555-ac9-publish-20260923
git commit -m "docs(evidence): add #555 controlled delivery canary"
git push gitee codex/555-ac9-publish-20260923
git push origin codex/555-ac9-publish-20260923
gh pr create --repo MJ-AgentLab/mj-agent --head codex/555-ac9-publish-20260923 --base develop --title "docs(evidence): verify #555 controlled delivery canary" --body-file evidence/issue-555/ac9-pr-body-20260923.md --draft

# cwd: D:/workspace/10-software-project/projects/mj-agent/develop
git push gitee codex/555-ac13-delete-20260923
git push origin codex/555-ac13-delete-20260923
git push gitee codex/555-ac13-batch-a-20260923
git push origin codex/555-ac13-batch-a-20260923
git push gitee codex/555-ac13-batch-b-20260923
git push origin codex/555-ac13-batch-b-20260923
git worktree remove ../codex/555-ac13-delete-20260923
git branch -d codex/555-ac13-delete-20260923
git push gitee --delete codex/555-ac13-delete-20260923
git push origin --delete codex/555-ac13-delete-20260923
git push gitee --delete codex/555-ac13-batch-a-20260923 codex/555-ac13-batch-b-20260923
git push origin --delete codex/555-ac13-batch-a-20260923 codex/555-ac13-batch-b-20260923
git worktree remove ../codex/555-ac13-batch-a-20260923
git branch -d codex/555-ac13-batch-a-20260923
git worktree remove ../codex/555-ac13-batch-b-20260923
git branch -d codex/555-ac13-batch-b-20260923
```

静态 `NO_MATCH` 不证明宿主放行。遇到拒绝保留原始错误，定位 hook、规则/危险命令、模式、权限/占用或网络；来源不明记 UNKNOWN_LAYER，已知阻断不重复试探。每端和每 ref 使用 `DELETED`、`ALREADY_ABSENT`、`REJECTED`、`FAILED`、`NOT_EXECUTED`、`UNKNOWN` 六种状态单列。#555 保持 OPEN，Plan 保持 active；计划文档和本记录当前 `UNCOMMITTED`，其提交/发布另属独立授权。

## Owner 批准后的第一轮实际执行（2026-09-23 03:13 UTC）

Owner 在本任务明确回复“批准上述五类全部动作”，范围仅为上表四条临时分支及具名本地/远端删除对象；未批准计划与本记录的另行提交、force 或 merge。当前会话权限声明仍为 `never` / `danger-full-access`；本次成功的 `git commit` 与 Gitee push 均通过正常 `exec_command` 返回 exit 0，未观察到显式宿主审批请求；Desktop 对新规则与 hook 的实际加载仍未取得独立证明。

| 动作/引用 | Gitee | origin | 证据与下一步 |
| --- | --- | --- | --- |
| 发布 commit | 不适用 | 不适用 | `878b474d56e1e4201bba335b60caa9ad7ee018cd`，只含批准的两文件、12 行，作者/提交者 `ranzuozhou <ranzuozhou@gmail.com>`；执行前 HEAD、index blob、无未暂存/未跟踪/忽略内容与远端不存在均复核 |
| `refs/heads/codex/555-ac9-publish-20260923` 普通 push | SUCCESS，`ls-remote`=`878b474d56e1e4201bba335b60caa9ad7ee018cd` | UNKNOWN | 第四次同一精确查询曾 exit 0 且无引用，随后原定 `git push origin` 返回连接重置；推送后的对账查询也连接重置。先查远端实际 tip，不重复推送 |
| `refs/heads/codex/555-ac13-delete-20260923` 普通 push | SUCCESS，`ls-remote`=`407e06877fbb8913fe2f702c8601a16f8ba41fb9` | NOT_EXECUTED | 本地 tip 与 develop 同 SHA；等待 origin 查询恢复 |
| `refs/heads/codex/555-ac13-batch-a-20260923` 普通 push | SUCCESS，`ls-remote`=`407e06877fbb8913fe2f702c8601a16f8ba41fb9` | NOT_EXECUTED | 同上 |
| `refs/heads/codex/555-ac13-batch-b-20260923` 普通 push | SUCCESS，`ls-remote`=`407e06877fbb8913fe2f702c8601a16f8ba41fb9` | NOT_EXECUTED | 同上 |
| PR 创建 | 不适用 | NOT_EXECUTED | 依赖 origin 发布引用，不用 Gitee push 冒充 GitHub PR 前置 |
| S/A/B 本地 worktree/branch 删除 | NOT_EXECUTED | 不适用 | S 的本地分支需先用于原定 origin 普通 push；旧工作树全部保留 |
| S 单引用与 A/B 批量远端删除 | NOT_EXECUTED | NOT_EXECUTED | 不把 Gitee 单端已创建视作双端可删；未执行任一删除命令 |

原始 origin 只读错误（同一 `git ls-remote --heads origin refs/heads/codex/555-ac9-publish-20260923` 初始连续三次，均 exit 1）：`fatal: unable to access 'https://github.com/MJ-AgentLab/mj-agent/': Recv failure: Connection was reset`。第四次同一查询 exit 0、空输出后，按原定命令执行 `git push origin codex/555-ac9-publish-20260923`，exit 1 且原始错误仍为上述连接重置；紧随其后的同一只读查询也 exit 1、同错。当前不能判定 origin push 是否完成，记 `UNKNOWN`；这不是宿主审批或 hook 拒绝证据。未改写命令或改用其他工具判断引用不存在，也不重试该 push。下一步先用同一只读查询对账，若引用存在且 tip 为 `878b474...` 则记成功并跳过推送；若成功查询证实不存在，才按未完成项继续。其他 origin 候选尚未推送。

## 最新执行结果与逐端对账（2026-09-23 03:28 UTC）

同一 origin 精确只读查询随后 exit 0 且无引用，证明首次写入未完成；才按批准的原命令重试一次 `git push origin codex/555-ac9-publish-20260923`，exit 0，随后 `ls-remote` 核实 `878b474d56e1e4201bba335b60caa9ad7ee018cd`。S/A/B 的 origin 普通 push 各自 exit 0、随后逐条查询为 `407e06877fbb8913fe2f702c8601a16f8ba41fb9`。Gitee 已成功项没有重复推送。网络错误的原文与 UNKNOWN 阶段保留于上一节，不能把瞬时成功倒写成“从未失败”。

`gh pr create --repo MJ-AgentLab/mj-agent --head codex/555-ac9-publish-20260923 --base develop ... --draft` 通过正常工具 exit 0，创建 [Draft PR #566](https://github.com/MJ-AgentLab/mj-agent/pull/566)。随后 `gh pr view 566` 核实 OPEN/Draft、head=`878b474d56e1e4201bba335b60caa9ad7ee018cd`、base=`develop`、标题及 body 与批准文件一致；未 merge。commit、两端普通 push 和 PR 创建各自有独立结果，且未见显式宿主审批请求；这不证明新 rules/hook 实际加载。

| 删除对象 | 本地 worktree/分支 | Gitee | origin | 执行前依据 |
| --- | --- | --- | --- | --- |
| S：`refs/heads/codex/555-ac13-delete-20260923` | `git worktree remove` 与 `git branch -d` 均 exit 0；路径、worktree 注册和本地 ref 复查不存在 | DELETED；`git push gitee --delete` exit 0，随后精确 `ls-remote --refs --heads` exit 0、无匹配 | DELETED；同样命令及成功空查询 | 本地工作树 1046 tracked、无 dirty/untracked/ignored、祖先/后代无重解析点、1311 个节点 DELETE 共享探测均 AVAILABLE；两端 ref/develop 均 `407e...`，本地分支删后仍从 develop 完成远端核验 |
| A：`refs/heads/codex/555-ac13-batch-a-20260923` | 同上，路径/worktree/ref 均不存在 | DELETED；与 B 同批，响应逐条列出删除，随后成功空查询 | DELETED；同批响应逐条列出删除，随后成功空查询 | 两端 A/B ref/develop 均 `407e...`；本地无 dirty/untracked/ignored、无重解析点、1311 节点均 AVAILABLE |
| B：`refs/heads/codex/555-ac13-batch-b-20260923` | 同上，路径/worktree/ref 均不存在 | DELETED；与 A 同批，成功空查询 | DELETED；与 A 同批，成功空查询 | 与 A 分别核验；批次没有保护分支、tip 变化或不一致 |

最终两次成功 `git ls-remote --refs --heads <remote>` 同时查询四个临时 ref，Gitee 与 origin 都只返回发布分支 `878b474d56e1e4201bba335b60caa9ad7ee018cd`，S/A/B 均无匹配；这与每步独立空查询一致。旧 #560/#561 引用没有重复删除，`maintain/555-approved-deletion` 未动，其他有内容旧工作树未动。发布 canary 的本地工作树和双端引用保留以供 Draft PR 审阅。

只读 `check_git_actions.py` 对 S 的两次执行均把 Gitee 查询标 `UNKNOWN`，而同一时段直接 `git ls-remote --refs --heads gitee` 成功返回精确 tip。检查器 `_git` 使用缩减环境、屏蔽全局 Git 配置，且把子进程错误压为 UNKNOWN；当前证据不足以将两者差异归因于某个单独环境变量。远端执行前以正常 Git 命令成功查询两端精确引用和 develop，并核对合并关系；该检查器的 Gitee live 查询覆盖保持未验证，不把它的 exit 1 写成通过或授权凭证。

当前矩阵中 AC-9 与 AC-13 的实际命令链已完成；AC-24 仍缺目标 Desktop 实际加载新 rules/hook 的独立证据，AC-22/24 的限定见逐项表。Issue 应保持 OPEN，Plan 保持 active。本记录与 Plan 的新修改仍 `UNCOMMITTED`；提交/双推/为这些文档另建 PR 不在本次五类动作的具名批准范围内。

Owner 随后确认本任务有效审批模式为 `never`，认可受控动作的逐项对账不能证明目标 Codex Desktop 已加载新版项目 rules/hook；暂不调整 AC-22/24 范围，要求 #555 保持 OPEN。补充的宿主只读核查已确认 Desktop `26.917.51856`（build `10492`，prod），本机配置为 `mj-agent=trusted`；目标 develop 会话对当前 `.codex/hooks.json` 的信任或加载记录仍未找到。受控执行时段（2026-09-23 03:13–03:28 UTC）的可查日志没有项目 rules/hook 加载事件，日志缺失不能证明未加载。另起 CLI 的 `OnRequest` 属不同进程，不替代目标任务的 `never`。最小剩余事项是取得可追溯的目标会话 rules/hook 加载状态与版本记录，再按现行条款复核 AC-22/24。此次侧对话未修改信任、配置或仓库，也未授权额外 Git 动作。

## 只读历史复核与新一轮对象准备（2026-09-23）

- 目标 Desktop 线程 `01a0cc2d-5760-7163-82ee-9ac75ff8b177` 的 session meta 为 `2026-09-23T02:51:58.897Z`、cwd=`D:/workspace/10-software-project/projects/mj-agent/develop`、`originator=Codex Desktop`、引擎 `0.155.0-alpha.16`。`C:/Users/Admin/.codex/logs_2.sqlite` 的目标线程 `feedback_tags` 在受控时段记载 `approval_policy=Never` 和 `CodexHooks` 功能标记；后者不是项目 hook 加载证明。Desktop `26.917.51856`（build `10492`，prod）来自 Owner 已核实的宿主只读核查。
- Desktop 文本日志 `C:/Users/Admin/AppData/Local/Codex/Logs/2026/09/23/codex-desktop-8549a67d-0068-41a0-851b-3599b8c6d16a-49820-t0-i1-003111-0.log` 在会话启动至 03:28 UTC 的可查记录及上述结构化日志中，没有与目标线程绑定的 `.codex/hooks.json`、`mj-agent.rules`、守卫路径、加载哈希或信任决定；session JSONL 也无独立加载回执。日志缺失不证明未加载。执行基线 `407e06877fbb8913fe2f702c8601a16f8ba41fb9` 的项目定义 blob 为 hooks=`f97a196bec330a8a49cd8cbb59cf21bcbb5956ad`、rules=`66772d5a40780ebe9a792afcddd0b21047de8efc`、runner=`01d61ff6c0fafe8bcf7c13d81caf3d19ff3d59c0`、guard=`dfd2ead68566b2ef6108e8fc27911369078b7a24`；这些只标识仓库文件，不能推出已加载。
- 对照现行 AC 自身的验证方式和 T1–T5，AC-3/6/15/16/21/23 改为“已验证（项目实现/离线范围）”；自基线 `407e...` 到当前 `9b754a690d0ef0b432d7ea431c2edda1043361b2`，关联规则、守卫、检查器及测试 diff 为零。本次未重跑测试，也未制造真实 Owner 撤销；目标宿主加载及已知拒绝的加载后恢复仍仅在 AC-22/24 为“真实链路未验证”。
- Owner 对两分支草案回复“同意，执行”后，按 G1 从 develop 创建 `codex/555-ac24-load-publish-20260923` 与 `codex/555-ac24-load-delete-20260923` 的具名 worktree。两者本地初始 tip=`9b754a690d0ef0b432d7ea431c2edda1043361b2`；创建前 Gitee、origin `refs/heads/develop` 同 tip，候选远端 ref 均不存在。发布 worktree 仅暂存 `evidence/issue-555/ac24-host-load-canary-20260923.md`，index blob=`134e0813e2d94e99c87b6ba08f37be8ac25693ed`，5 行；删除候选 worktree 仍清洁。Draft PR 正文草案位于 `C:/Users/Admin/AppData/Local/Temp/mj-agent-555-ac24-pr-body-20260923.md`（SHA256 `ED1514F2DD708C0D931CB6DCFB9E411AF0DEFB38D1B2C4E18EEAA1DDE33871C6`），尚未提交或用于 PR。
- 新目标 Desktop 会话的项目 rules/hook 加载路径、实际哈希、信任和加载状态仍无可追溯记录，当前任务也没有能出具该回执的诊断工具。因此本轮 **未执行 commit、普通 push、PR 创建或远端删除**；上述新本地分支、worktree 和暂存内容保留待核验，不把静态定义、当前 `trusted` 配置或命令成功作为加载证据。#555 保持 OPEN，Plan 保持 active；本记录/计划自身仍未提交。
- `.playwright-mcp/page-2026-09-23T04-07-42-592Z.yml` 的时间与另一个 Desktop 线程 `01a0cc2e-b80c-7463-a04d-c8ab3883f975` 于 04:07:39 UTC 调用 Playwright 导航 GitHub issue #495 相符；该文件及同目录 console 日志均未清理、暂存或纳入 #555 发布范围。

### AC-22/24 新一轮逐动作审阅清单（尚未执行 Git 发布或删除）

仓库为 GitHub `MJ-AgentLab/mj-agent`（`origin=https://github.com/MJ-AgentLab/mj-agent`）与 Gitee `ranzuozhou/mj-agent`（`gitee=https://gitee.com/ranzuozhou/mj-agent.git`）。2026-09-23 本次再次以成功的 `git ls-remote --heads` 分别核实两端 `refs/heads/develop=9b754a690d0ef0b432d7ea431c2edda1043361b2`，两条下列候选远端引用均不存在；`gh pr list --head codex/555-ac24-load-publish-20260923 --state all` 返回空。清单只绑定以下精确对象，执行前须重新对账；查询失败不等于引用不存在。

| 用途 | worktree 绝对路径 | 本地/两端精确 ref | 当前 tip 与内容 | 合并/备份依据 |
| --- | --- | --- | --- | --- |
| 发布 | `D:/workspace/10-software-project/projects/mj-agent/codex/555-ac24-load-publish-20260923` | `refs/heads/codex/555-ac24-load-publish-20260923` | `9b754a690d0ef0b432d7ea431c2edda1043361b2`；只暂存 `evidence/issue-555/ac24-host-load-canary-20260923.md`，blob `134e0813e2d94e99c87b6ba08f37be8ac25693ed` | 不列为删除对象；提交后新 SHA 须单独记录 |
| 删除测试 | `D:/workspace/10-software-project/projects/mj-agent/codex/555-ac24-load-delete-20260923` | `refs/heads/codex/555-ac24-load-delete-20260923` | `9b754a690d0ef0b432d7ea431c2edda1043361b2`；创建后清洁 | 与两端 develop 当前 tip 相同，已有内容由 develop 保留；若产生未提交/未跟踪/忽略内容、占用、重解析点或 tip 变化，暂停并重新审阅备份条件 |

拟分别授权的正常命令如下；每一行只在取得新目标 Desktop 会话的规则/hook **实际加载来源、定义哈希或版本、信任/加载状态、时间戳、有效模式**的可核对记录，并完成该动作自身的对象授权及紧前核验后执行。新规则文件存在、`trusted` 配置、`CodexHooks` 标记和命令成功均不代替加载回执。当前同意创建本地对象的回复不作为未核实加载状态下的发布/删除执行证据。

| 独立动作 | 精确拟用命令（按列出顺序） | 成功与异常对账 |
| --- | --- | --- |
| commit（发布 worktree） | `git commit -m "docs(evidence): add #555 host-load canary"` | 紧前复核 branch、HEAD、index blob、仅一文件 staged、其他未暂存/未跟踪/忽略内容及 `git diff --cached --check`；成功后记录新 SHA、实际文件集和 authorship；响应不明先 `git log`/status 对账，不重复提交 |
| 普通 push（发布分支） | `git push gitee codex/555-ac24-load-publish-20260923`；`git push origin codex/555-ac24-load-publish-20260923` | 每端成功的 `git ls-remote --heads <remote> refs/heads/codex/555-ac24-load-publish-20260923` 必须等于新 commit SHA；首端成功不重复，次端失败先查询实际 tip |
| Draft PR 创建 | `gh pr create --repo MJ-AgentLab/mj-agent --head codex/555-ac24-load-publish-20260923 --base develop --title "docs(evidence): verify #555 host-load canary" --body-file D:/workspace/10-software-project/projects/mj-agent/develop/evidence/issue-555/ac24-pr-body-2026-10-08.md --draft` | 2026-10-08 恢复的持久草案，SHA256=`ED1514F2DD708C0D931CB6DCFB9E411AF0DEFB38D1B2C4E18EEAA1DDE33871C6`，与原草案相同；原临时路径已不存在，新路径待 Owner 审阅。先查无同 head PR 与 origin tip；成功后记录 URL、head SHA、base、Draft；响应不明先 `gh pr list/view` 对账，不创建重复 PR |
| 普通 push（删除测试分支） | `git push gitee codex/555-ac24-load-delete-20260923`；`git push origin codex/555-ac24-load-delete-20260923` | 每端精确 ref 均须经成功查询为 `9b754a690d0ef0b432d7ea431c2edda1043361b2`；不借发布分支双推结果验收 |
| 本地删除（仅删除测试 worktree/branch） | 从 develop：`git worktree remove D:/workspace/10-software-project/projects/mj-agent/codex/555-ac24-load-delete-20260923`；`git branch -d codex/555-ac24-load-delete-20260923` | 删除紧前核验绝对路径、追踪/未提交/未跟踪/忽略、占用、重解析点及备份依据；之后 `git worktree list` 与 `git show-ref --verify` 分别核实缺失；不触及其他旧 worktree 或发布 worktree |
| 远端引用删除（仅删除测试 ref） | `git push gitee --delete codex/555-ac24-load-delete-20260923`；`git push origin --delete codex/555-ac24-load-delete-20260923` | 紧前两端成功查询的 tip 必须仍为 `9b754...` 且 develop 包含该提交；每端删除后单独成功查询精确 ref 不存在才记 DELETED；ALREADY_ABSENT、REJECTED、FAILED、NOT_EXECUTED、UNKNOWN 分端记录；首端结果不证明次端 |

任何实际宿主拒绝都保留原始错误并核对适用规则、hook、审批模式、危险命令/权限/网络等已知条件；无法归因记 UNKNOWN，不换工具、改写命令或借另一 remote 绕过。无加载回执或某动作授权不满足时，该动作维持 NOT_EXECUTED。没有请求 force、merge、旧工作树清理或计划文档提交。

## 反馈上传回执与历史证据可追溯程度（2026-10-08）

Owner 本次要求继续补记反馈取证进展、只读调查及准备后续选项。本节没有调整 AC-22/24，也没有消费第一轮对象批准来执行第二轮 Git 动作。#555 保持 OPEN，实施计划保持 active。

留存来源为目标会话 `C:/Users/Admin/.codex/sessions/2026/09/23/rollout-2026-09-23T10-51-58-01a0cc2d-5760-7163-82ee-9ac75ff8b177.jsonl`。以下行号对应本次复查的原始 JSONL；工具输出是当时只读查询的留存摘录，不能升级为 Desktop 独立加载回执。原时段 Desktop 日志目录 `C:/Users/Admin/AppData/Local/Codex/Logs/2026/09/23` 本次已不存在，当前 `logs_2.sqlite` 的原时段目标线程记录和下述原始行 ID 已不可直接查询。

| 字段 | 已取得的证据及来源 | 可追溯程度 / 结论 |
| --- | --- | --- |
| 线程、cwd 与起始时间 | JSONL 第 1 行 `session_meta`：目标 ID=`01a0cc2d-5760-7163-82ee-9ac75ff8b177`，payload 时间 `2026-09-23T02:51:58.897Z`，wrapper 时间 `02:52:00.208Z`，cwd 为目标 develop，originator=`Codex Desktop` | 当前原始 session meta 可直接复查；受控窗口内有 516 个事件，未找到独立加载回执 |
| Desktop / 引擎版本 | Owner 独立只读核实 Desktop `26.917.51856`（build `10492`，prod）；JSONL session meta 引擎 `0.155.0-alpha.16` | Desktop 为 Owner 已核实事实，引擎为原 session 字段；不能据当前安装版本回填历史加载版本 |
| 当时有效审批模式 | 按目标 thread_id 筛选的只读查询见 JSONL 第 1692 行，`logs_2.sqlite` 原 ID `25045011`（03:25:00 UTC）、`25047374`（03:28:26 UTC）含 `approval_policy=Never`；源 `core/src/session/turn.rs:2433`、进程 `pid:40336:5f0e4100-d044-4056-b706-c6bf346614d6`。查询输出留于第 1695 行（04:22:27.345Z），第 2334/2341 行为后续复核摘录 | 原 SQLite 行已不可查询，留存的查询条件与输出可关联原 ID、时点、线程与模式。`CodexHooks=True` 仅是功能标记；另起 CLI 的 OnRequest 不适用 |
| 实际 rules/hook 来源、定义版本/哈希 | 执行基线 `407e068...` 的 hooks/rules/runner/guard blob 已列在前节；原日志查验及 session 留存未取得与目标线程绑定的加载路径或实际定义标识 | 仓库定义可追溯，实际加载的来源和版本均 UNKNOWN |
| 项目与 hook 信任决定 | Owner 核实本机配置 `mj-agent=trusted`；目标线程、原时段的项目与 `.codex/hooks.json` 信任决定无可追溯事件 | 静态配置事实与会话决定分列；目标会话两种信任状态均 UNKNOWN |
| 实际加载/跳过、原因与事件时间 | 当时可查 Desktop 日志在窗口有目标线程活动，但没有项目 rules/hook 加载/跳过事件；本次未取得独立诊断答复 | 加载/跳过、原因、对应时间戳均 UNKNOWN。日志缺失不证明未加载 |

### 已上传反馈：送达事实与诊断结论分列

- Feedback ID=`01a0cc2d-5760-7163-82ee-9ac75ff8b177`，与目标 thread_id 相同。原结构化日志 ID `25176077` 于 **2026-09-23 05:06:58 UTC** 记录 `feedback event uploaded to Sentry`、同一 thread_id、`uploaded_attachments=13`、`attachments_failed=false`、`elapsed_ms=3298`；来源 `feedback/src/lib.rs:681`。该查询输出保存在目标 JSONL 第 **2527** 行（05:12:20.939Z）与第 **2534** 行（05:12:31.014Z）。
- 原 Desktop 日志 `codex-desktop-adf65238-c2fa-4e78-9289-13e16efac79d-70200-t0-i1-042637-0.log:4685` 于 `05:06:58.029Z` 记录 `method=feedback/upload`、`errorCode=null`、同一 `conversationId`，requestId=`c5348d11-4dc9-428d-b92a-e44563d06897`。留存查询输出为 JSONL 第 **2492** 行（05:11:37.108Z）及第 **2499** 行（05:11:44.394Z）。原文本日志和 SQLite 行本次已不可直接复查，留存摘录的局限明确保留。
- 两来源支持反馈及 13 个附件上传成功；没有附件内容清单，不能推定附件已包含所需加载事件，也不能推定已获支持答复。本次启用工具中没有反馈结果查询或目标 Desktop rules/hook 加载诊断接口；未取得加载报告。未再次提交反馈或上传日志。
- 如通过原聊天反馈关联的诊断/支持渠道补充取证，应索取：目标 thread_id 与进程/session 关联键；原始事件时间及 UTC/时钟来源；rules、hooks.json、runner、guard 的解析来源绝对路径与当时实际加载哈希/版本；项目与 hook 的独立信任决定及来源；加载/跳过状态、原因和生效时间；有效审批模式及覆盖来源；记录保留范围/缺失情况。关联反馈 ID 与上述上传 requestId，要求说明怎样关联原目标会话。任何后续提供的材料先由 Owner 检查凭据、个人路径及业务内容等敏感信息，再决定是否提交；本节没有上传授权。

## 新一轮对象及审阅选项更新（2026-10-08）

本次正常只读查询与预检如下：

| 核验 | 命令 / 当前结果 |
| --- | --- |
| 两端引用 | 各端 `git ls-remote --heads <gitee/origin> refs/heads/develop refs/heads/codex/555-ac9-publish-20260923 refs/heads/codex/555-ac24-load-publish-20260923 refs/heads/codex/555-ac24-load-delete-20260923` 均 exit 0；develop=`9b754a690d0ef0b432d7ea431c2edda1043361b2`，第一轮发布=`878b474d56e1e4201bba335b60caa9ad7ee018cd`；第二轮两个精确 ref 各端均不存在 |
| 第一轮 PR / 新 PR 查重 | `gh pr view 566 --json state,isDraft,headRefName,headRefOid,baseRefName,url`：OPEN/Draft、head=`878b474...`、base=develop；`gh pr list --repo MJ-AgentLab/mj-agent --head codex/555-ac24-load-publish-20260923 --state all --json number,headRefName,state,isDraft` 返回 `[]`，均 exit 0 |
| 新发布 worktree | 前节具名绝对路径保留，HEAD=`9b754a690d0ef0b432d7ea431c2edda1043361b2`；`status --porcelain=v1 --ignored --untracked-files=all` 仅一 staged canary，`ls-files --stage` blob=`134e0813e2d94e99c87b6ba08f37be8ac25693ed`；SHA256=`8399AAC7CF457B3B40CFC0936F3173F09DAB5FDFF671383CD6187F5AC069D22F`；`diff --cached --check` exit 0 |
| 新删除 worktree | 前节具名绝对路径保留，HEAD 同上，`status --porcelain=v1 --ignored --untracked-files=all` 空；`git merge-base --is-ancestor codex/555-ac24-load-delete-20260923 develop` exit 0。该内容由 develop 保留；占用、路径及重解析点须在删除紧前重检，本次不声称已完成删除前全部核验 |
| PR 正文草案 | 原临时路径查询返回 `Could not find file 'C:\Users\Admin\AppData\Local\Temp\mj-agent-555-ac24-pr-body-20260923.md'.`，属于准备文件缺失。本次由既有正文恢复到 [持久草案](ac24-pr-body-2026-10-08.md)，SHA256=`ED1514F2DD708C0D931CB6DCFB9E411AF0DEFB38D1B2C4E18EEAA1DDE33871C6`，与原文件一致；仅更新上方待审命令的 body-file 路径，尚未创建 PR |

AC-3/6/15/16/21/23 的现行验证方式和既有 T1–T5 结果已在矩阵逐项对齐，六项保持“已验证（项目实现/离线范围）”。本次没有运行功能回归或新增加载证明。`.playwright-mcp/`、有内容的旧工作树与新临时工作树均保留；新轮 commit、push、PR 创建、本地删除、远端引用删除均 NOT_EXECUTED。记录、计划与 AGENTS 原则修改仍 UNCOMMITTED，正文草案未暂存。

### Owner 决策选项（批准前快照，实际决定见末节）

1. **新会话补验（推荐）**：明确调整 AC-22/24 的剩余验收为具有完整可追溯加载记录的新目标 Desktop 会话。原时段加载状态永久保留 UNKNOWN，新记录只证明新执行；AC-22 的已知拒绝条件变化与恢复仍须独立核验，不能用网络恢复代替。理由：原日志已不在本机，继续验收需要可获得的会话证据。先取得实际加载/信任/模式记录，再按前节精确对象和更新的正文路径分别批准五类动作；本选项本身不批准 Git 写操作或个人配置/信任修改。
2. **维持历史范围**：保持现行 AC-22/24，继续通过已上传的反馈 ID 索取原时段记录；没有充分原始证据前保持 UNKNOWN、OPEN、active，保留已准备对象，不启动新轮动作。

最小剩余事项：取得可追溯原时段加载记录，或由 Owner 明确选择上述范围调整；按所选范围补齐 AC-22/24 的实际加载及恢复证据。新轮执行前需核对五类独立动作的精确授权与最新对象快照。项目/原生信任的工程师独立审阅及宿主实际审批依 AGENTS 执行，不由聊天选择替代。验收记录/计划/AGENTS 原则的另行提交仍是独立交付待办。以上条件满足后才重新评估关闭 #555。

### 本轮文档校验与实施来源

`uv run --frozen --no-sync python scripts/check_frontmatter.py`：146 篇 canonical 文档通过，exit 0；`uv run --frozen --no-sync python scripts/check_wikilinks.py`：0 archive-ref violations、5 根入口 0 unresolved，exit 0。`git diff --check` 通过；证据目录不在 canonical 扫描范围，另逐文件检查本记录与 PR 正文的尾空白及相对链接，均无问题。没有重跑功能测试或外部服务探针；这些结果不增加加载/宿主实测证据。实施来源 Codex，未委派；本次为记录维护，无产品行为改变，BDD/TDD 不适用。

本次通过正常 `gh issue edit 555 --repo MJ-AgentLab/mj-agent --body-file <已审阅正文文件>` 补记上传与取证进展；回读 `updatedAt=2026-10-08T03:44:38Z`、state=OPEN。原现行 24 条 AC、既有正文前缀与折叠历史区逐字保持原样，只新增 2026-10-08 当前记录节；回读 body SHA256=`e2d9aff2ea60da60de53ca6021a5cdd9681e33433ee4b2f0e30f4cd4df1896d6`。首次回读发现临时正文写入时换行转换，已恢复原换行并重新严格核对，通过后才记本结果；没有改写验收条款或关闭 Issue。

## Owner 批准新会话补验后的执行前核查（2026-10-08）

Owner 对“新会话补验（推荐）”回复 **“同意推荐，授权执行”**。本任务据此采纳范围调整：AC-22/24 的剩余实际验收可由具有完整可追溯加载记录的新目标 Desktop 会话完成；原 `2026-09-23 03:13–03:28 UTC` 的加载结论永久保持 UNKNOWN，新结果只证明新执行。原时段作为唯一补验窗口的限制被新决定替代，整项 AC 未取消，实际加载前置条件及 AC-22 已知拒绝的条件变化/恢复仍保留。

本批准分别适用于前节五类精确对象与命令：发布 worktree 的一个 staged canary commit；发布/删除测试两分支 Gitee→origin 普通 push；发布分支显式 base=develop 且使用已恢复持久正文的 Draft PR；仅删除测试 worktree/本地分支；仅两端删除测试精确 ref、tip=`9b754a690d0ef0b432d7ea431c2edda1043361b2`。本次对五类授权分别登记为 **APPROVED**，不再请求同一批准。记录/计划/AGENTS 原则的另行提交、merge、force、信任/个人配置修改及日志上传不包含在此范围。

### 新运行实例证据及不能替代的事实

- 找到新文件 `C:/Users/Admin/.codex/sessions/2026/10/08/rollout-2026-10-08T11-13-41-01a0cc2d-5760-7163-82ee-9ac75ff8b177_01a11980-9d00-7d70-a9a8-b68b6b201678.jsonl`。第 1 行 session meta 时间 `2026-10-08T03:13:41.632Z`（wrapper `03:13:41.797Z`），originator=Codex Desktop、目标 develop、引擎 `0.162.0-alpha.2`；thread_id 仍为原聊天，运行实例与原时段不同。第 255 行本轮 turn `01a119a6-26bd-70c2-8e5a-a7e50e1355e8`（03:54:41.779Z）记录 never / danger-full-access。
- `logs_2.sqlite` 目标 thread_id 的原生 `feedback_tags` 行 `27260206`（03:54:57 UTC）、`27260952`（03:55:33 UTC）、`27262119`（03:56:18 UTC）记载 Never；来源 `core/src/session/turn.rs:2548`，进程 `pid:115512:d28f44c9-467c-4323-878e-0ba63ea77ce0`。原生日志与 turn 字段相符；这项是实际会话模式证据，单独不证明规则/hook 加载。
- 当前安装包登记 `OpenAI.Codex=26.1002.7124.0`，该包 ASAR 内 `package.json` 的应用 version=`26.1002.52244`；不混同 9 月历史已核实版本，当前 build/prod 元数据未独立核实。新 session 无独立加载事件类型，world_state 无 rules/hook/trust 字段；目标结构化记录中未找到定义路径、实际哈希、信任或加载事件。当日唯一 `codex_core::hook_runtime` WARN 属其他 thread/进程且为 legacy_notify，不可作为本目标项目加载证据。当前进程的三个 Desktop 文本日志文件均为 0 字节；缺记录不证明未加载。
- 只读检查已安装 Desktop 的前端静态代码，确认存在 Hooks 设置 `hooks/list` 请求（`cwds` 参数）及 `currentHash`/`trustStatus` 字段，但没有 thread_id 参数；列表结果还须绑定目标实例及实际加载事实。信任/启用修改使用另一 `config/batchWrite` 入口，本次未调用。Agent 工具目录不提供 Hooks 查询或目标线程加载诊断接口，原生 Desktop 控制不可用，未经私有 IPC、另起 CLI、手动运行 hook 或配置改动制造证据。

来源、当前静态定义 SHA256、诊断入口限制与必须补齐的字段已准备为 [新会话诊断请求草案](ac24-desktop-diagnostic-request-2026-10-08.md)，未发送或上传。[官方 Hooks 文档](https://learn.chatgpt.com/docs/hooks)仅作检查入口与信任边界的说明，不能证明本目标实例加载。

### 授权与执行条件分账

本次再次逐工作树 status/HEAD/index 核对：两条新分支仍为 `9b754a690d0ef0b432d7ea431c2edda1043361b2`，发布仍仅 staged canary blob=`134e0813e2d94e99c87b6ba08f37be8ac25693ed`，删除候选 clean；正常两端精确 `ls-remote` 均 exit 0，develop 同 tip，两个候选 ref 均不存在。持久 PR 正文 SHA256 仍为 `ED1514F2DD708C0D931CB6DCFB9E411AF0DEFB38D1B2C4E18EEAA1DDE33871C6`。没有实质对象变化；删除紧前的完整占用/路径/重解析点与并发核验仍待执行。

| 动作 | Owner 授权 | 本轮实际状态 / 前置条件 |
| --- | --- | --- |
| canary commit | APPROVED | NOT_EXECUTED：目标实际加载证据未取得 |
| 两分支普通 push | APPROVED，两端分别覆盖 | NOT_EXECUTED：加载证据未取得；发布 push 还依赖 canary commit |
| 显式 base Draft PR | APPROVED，持久正文路径已包括 | NOT_EXECUTED：加载证据未取得；还依赖两端发布/查重 |
| 仅删除测试 worktree/本地分支 | APPROVED | NOT_EXECUTED：加载证据未取得；紧前删除核验未运行 |
| 仅删除测试两端精确 ref | APPROVED | NOT_EXECUTED：加载证据未取得；还依赖测试 ref 的创建与逐端 tip 核验 |

停点为 **UNMET_HOST_LOAD_EVIDENCE**。本轮没有新的 Git 命令拒绝或宿主批准失败，不将缺证据写成已观察到的 `BLOCKED_EXECUTION_ROUTE`。授权继续有效；取得充分目标加载记录后，从各自紧前预检继续正常命令，无需重复同一批准。AC-22/24 仍真实链路未验证/UNKNOWN，#555 OPEN、计划 active；原时段 UNKNOWN、旧工作树及 `.playwright-mcp/` 均保留。最小剩余事项是获得新目标实例可追溯的加载/信任/版本记录，然后完成已批准五类动作及分项对账。

本轮记录校验：frontmatter 146 篇 PASS，wikilinks 0 archive-ref violations/5 根入口 0 unresolved，`git diff --check` 与证据相对链接/尾空白检查通过；`check_codex_native.py --effective-approval-policy never` 返回 STATIC_PASS/PER_COMMAND、rule_loading=UNKNOWN、host_enforcement=NOT_TESTED、owner_approval=NOT_ASSESSED，均 exit 0。Owner 真实批准依据为上引人类回复，静态检查器的 NOT_ASSESSED 不被改造成批准证明。没有新增行为变更或功能回归，实施来源 Codex、未委派。

#555 已补记本范围决定、五类授权与新候选核查，回读 `updatedAt=2026-10-08T04:07:50Z`、state=OPEN，body SHA256=`e17de04e60bfbd09fe3a8845c8aea92b925eb321daa08a497ddda0fd2739171f`。现行 AC 仍 24 条，仅 AC-22/24 附加获批新会话范围、对应矩阵两行同步，其余 22 条及折叠历史正文保持原样；本地记录未提交。

## 实际审批模式切换与正常宿主入口核对（2026-10-08 04:14 UTC）

Owner 告知“已经调整为 ask for approval 模式，继续执行”。本次复用既有五类具名动作批准，先只读核实本任务的实际变化。范围与加载前置条件继续依据上节获批方案；该回复没有取消实际加载记录要求或授权信任/配置修改。

| 证据 | 实际结果与来源 |
| --- | --- |
| 模式应用事件 | 上节 10 月 8 日目标 JSONL 第 **411** 行，`2026-10-08T04:14:22.115Z`，`event_msg/thread_settings_applied`，关联目标 thread_id；字段含 approval_policy / approvals_reviewer，无 rules/hook/trust 加载字段 |
| 本轮有效 turn | 同文件第 **417** 行，`2026-10-08T04:14:22.221Z`，turn_id=`01a119b8-298e-78e2-a42b-48ad103c3d14`，cwd 为目标 develop、approval_policy=`on-request`，sandbox_policy=`workspace-write`、network_access=false；之前 never/danger-full-access 记录仅保留为切换前事实 |
| 原生结构化佐证 | `logs_2.sqlite` 行 **27274879**，`2026-10-08 04:14:22 UTC`、ts_nanos=`259044300`，目标 thread_id、feedback_tags、`approval_policy=OnRequest`；源 `core/src/session/turn.rs:2548`，进程仍为 `pid:115512:d28f44c9-467c-4323-878e-0ba63ea77ce0` |
| 目标加载记录 | 当前 session 类型、event_msg 子类型、thread_settings 字段与目标结构化查询均无 rules/hook 加载路径、实际定义哈希、项目/hook 信任及加载/跳过记录；保持 UNKNOWN，缺记录不证明未加载 |
| 精确对象 | 两新 worktree HEAD 仍 `9b754a690d0ef0b432d7ea431c2edda1043361b2`，发布只 staged canary blob=`134e0813e2d94e99c87b6ba08f37be8ac25693ed`，删除候选 clean。两端正常 `git ls-remote --heads <remote> refs/heads/develop refs/heads/codex/555-ac24-load-publish-20260923 refs/heads/codex/555-ac24-load-delete-20260923` 分别 exit 0、develop 同 tip、两个候选 ref 不存在 |

### 本轮正常审批入口的观察及原始错误

1. 同一只读 `gh issue view 555 --repo MJ-AgentLab/mj-agent --json body,state,updatedAt,url` 在受限网络内 exit 1，原文：

   ```text
   Post "https://api.github.com/graphql": proxyconnect tcp: dial tcp 127.0.0.1:9: connectex: No connection could be made because the target machine actively refused it.
   ```

   按本轮宿主提供的正常机制，对**同一命令**请求 `sandbox_permissions=require_escalated` 后 exit 0；完整正文复读仍 OPEN，updatedAt=`2026-10-08T04:07:50Z`。没有改代理、网络配置或换工具；这是该只读命令的正常宿主路线结果，不能证明 Git 写动作或项目 hook 加载。执行结果未独立给出“人工弹窗批准/规则免弹窗”的分类，该细节不由 exit 0 推断。
2. `uv run --frozen --no-sync python scripts/sdd/check_codex_native.py --effective-approval-policy on-request` 受限缓存访问 exit 1，原文：

   ```text
   error: Failed to initialize cache at `C:\uv_cache`
     Caused by: failed to open file `C:\uv_cache\sdists-v9\.git`: Access is denied. (os error 5)
   ```

   按同一正常宿主机制批准范围申请，对**同一命令**在沙箱外执行 exit 0：STATIC_PASS / PER_COMMAND，effective_approval_policy=on-request，rule_loading=UNKNOWN、host_enforcement=NOT_TESTED、owner_approval=NOT_ASSESSED。该参数化静态结果与上表原始会话证据分列；没有改缓存路径或权限。缓存错误不是 canary commit、worktree 删除或远端动作的拒绝证据。

当前实际 on-request 已取得可追溯证明；加载证据仍是独立未满足条件。五类授权继续 APPROVED，五类 Git 命令本轮均 NOT_EXECUTED，停点仍为 UNMET_HOST_LOAD_EVIDENCE。没有通过 commit/push 成功猜测加载，也没有把受限网络/缓存报错记成 Git 宿主拒绝或实际 Git 恢复。取得加载记录后，按本轮 workspace-write 的实际条件，对确需沙箱外权限的具名命令走正常宿主审批。#555 OPEN、计划 active，原时段 UNKNOWN、旧工作树与 `.playwright-mcp/` 保留；最小剩余输入为新目标实例的实际加载/信任/定义记录，五类动作批准无需重复。

## Owner 批准先执行具名动作（2026-10-08）

Owner 对执行顺序选项明确选择：**“先执行已批准的受控动作（推荐）：独立验证命令能力，加载状态继续 UNKNOWN，#555 保持 OPEN；实际拒绝立即保留原错并停止受影响步骤。”** 本次仅将新会话加载回执从五类动作的执行前置移为独立未完成验收，复用前节五类具体对象批准；AC-22/24 的实际加载/信任/定义与拒绝恢复验收未取消，原时段 UNKNOWN 不回填。上节加载优先停点为本决定前快照。

执行范围仍是一个 canary commit、两个具名分支 Gitee→origin 普通 push、显式 base=develop 的具名 Draft PR、仅测试 worktree/本地分支、仅测试精确两端 ref 删除。正常宿主审批与项目授权分列；每项紧前预检、逐端对账后再推进，实际拒绝保留原错并暂停受影响动作。记录/计划/AGENTS 提交、信任/配置修改、上传、force、merge、旧工作树与 `.playwright-mcp/` 处理均不包括。

## E2：本轮真实执行与逐动作对账（2026-10-08 04:27–04:32 UTC）

本节证据来自前述 10 月 8 日目标 session JSONL 的原始工具调用及返回；下表行号和时间是该文件的输出记录坐标，chunk 可对应实际 shell 返回。关联 thread_id=`01a0cc2d-5760-7163-82ee-9ac75ff8b177`、本轮 turn=`01a119b8-298e-78e2-a42b-48ad103c3d14`。实际模式由第 417 行 turn 与 SQLite 行 27274879 证明，不能由命令参数反推。

仓库和两端 remote 未变：Gitee=`https://gitee.com/ranzuozhou/mj-agent.git`、origin=`https://github.com/MJ-AgentLab/mj-agent`。发布 ref=`refs/heads/codex/555-ac24-load-publish-20260923`，删除测试 ref=`refs/heads/codex/555-ac24-load-delete-20260923`。所有写命令逐条通过正常 `exec_command` 请求 `sandbox_permissions=require_escalated` 后成功；没有换工具、修改代理/权限/信任、force 或 merge。原始工具记录未独立给出人工弹窗批准还是既有规则放行的分类，记 **UNKNOWN**；本节只证明所请求正常入口的实际结果。

### commit → Gitee → origin → 显式 base Draft PR

| 动作 / 精确命令 | 实际结果及独立核对 | UTC / 原始输出坐标 |
| --- | --- | --- |
| 在批准的发布 worktree `git commit -m "docs(evidence): add #555 host-load canary"` | SUCCESS，SHA=`6d331438990c458599025bccf3196fabbd694514`；仅 `evidence/issue-555/ac24-host-load-canary-20260923.md`，5 insertions，blob=`134e0813e2d94e99c87b6ba08f37be8ac25693ed`、文件 SHA256=`8399AAC7CF457B3B40CFC0936F3173F09DAB5FDFF671383CD6187F5AC069D22F`。`show --format=fuller --stat` 作者/提交者均 `ranzuozhou <ranzuozhou@gmail.com>`，实际实施者 Codex；发布工作树 clean，无额外 staged/untracked/ignored。未修改署名配置 | 04:27:41.932Z，JSONL 547，chunk `8f3057`，exit 0；提交时间 04:27:41 UTC |
| `git push gitee codex/555-ac24-load-publish-20260923` | SUCCESS；随后 `git ls-remote --heads gitee refs/heads/codex/555-ac24-load-publish-20260923` exit 0，精确 tip=`6d331438990c458599025bccf3196fabbd694514` | push 04:28:05.771Z，560 / `54633c`；查询 04:28:10.497Z，565 / `40530b` |
| `git push origin codex/555-ac24-load-publish-20260923` | SUCCESS；随后 origin 同一精确 ref 查询 exit 0，同完整 SHA；未重复成功端 | push 04:28:20.576Z，570 / `707668`；查询 04:28:55.072Z，577 / `3838fe` |
| `gh pr create --repo MJ-AgentLab/mj-agent --head codex/555-ac24-load-publish-20260923 --base develop --title "docs(evidence): verify #555 host-load canary" --body-file D:/workspace/10-software-project/projects/mj-agent/develop/evidence/issue-555/ac24-pr-body-2026-10-08.md --draft` | SUCCESS，[PR #571](https://github.com/MJ-AgentLab/mj-agent/pull/571)；创建前查重 `[]`。回读 OPEN/Draft，head 为上述完整 SHA、headRefName 精确一致、base=develop、title 一致；body 与草案 UTF-8 字节对应文字完全一致，SHA256=`ED1514F2DD708C0D931CB6DCFB9E411AF0DEFB38D1B2C4E18EEAA1DDE33871C6`。已附加本任务，未 merge/close | create 04:29:08.633Z，586 / `da595b`；服务 createdAt=04:29:07Z；回读 04:29:18.490Z，592 / `a4c02b` |

### 删除测试 ref 的创建、保存证据及本地删除

| 动作 / 核验 | 实际结果与边界 | UTC / 原始输出坐标 |
| --- | --- | --- |
| `git push gitee codex/555-ac24-load-delete-20260923` | SUCCESS；随后 Gitee 精确 ref 查询 exit 0，tip=`9b754a690d0ef0b432d7ea431c2edda1043361b2` | push 04:29:55.410Z，608 / `6cd326`；查询 04:29:59.668Z，613 / `140000` |
| `git push origin codex/555-ac24-load-delete-20260923` | SUCCESS；随后 origin 精确 ref 查询 exit 0，同完整 SHA | push 04:30:13.629Z，618 / `64fec6`；查询 04:31:01.717Z，626 / `275662` |
| 删除紧前只读完整核验 | 正确绝对路径、目标分支/tip、当前执行目录均匹配批准；祖先及后代无 reparse，1311 节点 DELETE access probe 全部 AVAILABLE；1046 tracked flags 均 H，dirty/untracked/ignored=NONE、无额外文件/目录/硬链接，前后 identity snapshot 未变化。秘密路径只核对元数据，未读正文或 hash；`.git` 是控制文件，共享 Git 目录不在删除路径。tip 与本地/两端 develop 完全一致，`merge-base --is-ancestor` exit 0，因此 Git 清洁内容由 develop 保留，无未提交内容需备份。这些只读检查不是授权凭证 | guard 自报 04:31:01.658248Z；626 / `6ad258`，exit 0 |
| `git worktree remove D:/workspace/10-software-project/projects/mj-agent/codex/555-ac24-load-delete-20260923` | DELETED，exit 0；随后 `worktree list --porcelain` 无目标条目、`Test-Path -LiteralPath` 为 False，目录与元数据分别核实不存在，分支当时仍是批准 tip | 04:31:17.578Z，635 / `d2154f`；复查 04:31:22.439Z，640 / `cb4799` |
| `git branch -d codex/555-ac24-load-delete-20260923` | DELETED，exit 0，原始输出 `Deleted branch codex/555-ac24-load-delete-20260923 (was 9b754a6).`；随后 `for-each-ref` 查询该精确本地 ref 空，tip 仍由 develop 保留；未用 -D | 04:31:32.713Z，645 / `1da719`；复查 04:31:40.275Z，652 / `84767f` |

### 本地对象已删除后，Gitee / origin 远端引用独立删除

执行前从保留的 develop 分别成功查询两端：删除测试 ref 及各端 develop 均为 `9b754a690d0ef0b432d7ea431c2edda1043361b2`（chunks `abc549` / `958c9c`），符合批准 tip、保存证据及非保护对象范围。不使用旧 remote-tracking ref 代替当前查询，也不重建已删除本地对象。

| remote / 精确命令 | 实际结果与事后查询 | UTC / 原始输出坐标 |
| --- | --- | --- |
| Gitee：`git push gitee --delete codex/555-ac24-load-delete-20260923` | DELETED，exit 0；`git ls-remote --heads gitee refs/heads/codex/555-ac24-load-delete-20260923` exit 0，空输出，独立证明该端 ref 不存在 | 删除 04:31:51.513Z，658 / `e3c95b`；查询 04:31:55.530Z，663 / `749aa7` |
| origin：`git push origin --delete codex/555-ac24-load-delete-20260923` | DELETED，exit 0；origin 同一精确 ref 的 ls-remote exit 0，空输出，独立证明该端 ref 不存在 | 删除 04:32:07.566Z，668 / `7d75ff`；查询 04:32:11.869Z，673 / `e6e41f` |

最终两端再次正常精确查询 exit 0（chunks `3fb5ba` / `1a72e6`）：develop 仍 `9b754...`、发布 ref 均 `6d331...`，删除测试 ref 均不存在。本轮无新的 Git 宿主拒绝、网络失败或响应未知；未制造失败/批量等额外对象，首轮及 T1/T2 的相关变体证据仍保留。此前已删除分支未重复操作。

### 剩余验收与保留内容

五类动作分别为 SUCCESS / SUCCESS / SUCCESS / DELETED / 双端 DELETED；这是 E2 本次可执行性证据。实际 on-request 的原始变化与执行结果已经取得，但**项目 rules/hook 的来源、实际加载定义哈希/版本、项目及 hook 信任决定、加载/跳过状态/原因/时间，以及其与原拒绝来源的关系仍 UNKNOWN**。没有把模式切换或成功命令写成项目规则加载及加载后的恢复；AC-22/24 保持“真实链路未验证”，原 9 月时段 UNKNOWN 永久保留，#555 OPEN、计划 active。

最小剩余事项：取得本目标 Desktop 运行实例可追溯的加载/信任/定义回执并按 AC-22/24 复核；不可取得时由 Owner 明确决定剩余范围，未作决定前保持 OPEN。诊断请求草案已准备但未发送；补充日志须先检查敏感信息，再由 Owner 判断发送范围。记录、计划和 AGENTS 原则的 Git 提交另属独立待办，仍 UNCOMMITTED。

有内容旧工作树、两次发布 worktree/引用与 PR #566/#571 均保留。`.playwright-mcp/page-2026-09-23T04-07-42-592Z.yml` 仍未跟踪，SHA256=`DA16C930A7AA8D21768A822EA99374E2B788A44186D04B492B74CE086665A943` 未变；未清理/暂存。实施来源 Codex，未委派；canary 与记录无产品行为改变，BDD/TDD 不适用新增行为，沿用既有 T1–T5 离线结果。

### E2 文档校验与 Issue 同步回执

本轮更新后 `check_frontmatter.py` 为 146 canonical PASS，`check_wikilinks.py` 为 0 archive-ref violations/5 根入口 0 unresolved，`git diff --check` 及三份 evidence 文件尾空白/相对链接检查均 exit 0。两项 uv 检查因已核实缓存沙箱限制，经正常 require_escalated 入口运行原命令；无安装依赖或功能测试追加。这些文档/静态结果不增加实际加载证据。

#555 通过正常 `gh issue edit ... --body-file` 补记模式原始来源、Owner 顺序决定与 E2 命令/逐端对账结果，回读 `updatedAt=2026-10-08T04:41:10Z`、state=OPEN；正文与预备 UTF-8 文件逐字一致，SHA256=`8c5f359dc2bac392b8ff6d3280ddb03797b1e24e88027618e69f7f5060e6c1bc`。现行 24 条 AC 与折叠历史逐字不变，仅同步六行证据矩阵及追加时间序列结果，未取消 AC-22/24 或关闭 Issue。计划 active，记录/计划/AGENTS 修改及两份持久草案仍未提交/未新增暂存。

## E3：授权后的只读取证补充（2026-10-08）

Owner 回复“授权执行”，继续推进剩余诊断；已成功动作不重复，本次没有 commit、push、PR 创建或删除。项目加载取证、当前模式与 E2 时段模式分别复核。

### 当前模式与执行窗口模式分列

目标 session 第 815 行（04:44:38.405Z），turn_id=`01a119d3-e042-70e0-a75e-e501267f041a`，实际 never / danger-full-access、approvals_reviewer=auto_review；SQLite 行 27305181（04:44:38 UTC，ts_nanos=462621400）关联原 thread/process 并记录 Never。本轮遵循当前实际权限，不请求 require_escalated；这是新 turn 条件，不回写 E2。

E2 的原 turn 及 04:27–04:33 UTC 237 条原生记录仍支持 OnRequest，逐命令完成时模式行包括 commit=27284359、发布 Gitee=27284665、发布 origin=27284933、PR=27285210、测试 Gitee=27285714、测试 origin=27286421、worktree=27287258、branch=27287388、Gitee 删除=27287645、origin 删除=27287825。04:31:42.926Z 的 session 第 654 行为 thread_settings_applied / never，不能单独推翻正在执行 turn 及原生逐命令模式记录；两类事件均保留，作用时间须由 Desktop 诊断明确。

### 正常宿主审批请求与 accept 回执已补证

此前三份文本日志为空是检查时快照。本次找到以下可读且非空的 Desktop 文件（t0、t1、t2 及另一进程两份，共 5 份）；未独立核对两次观察是否为相同文件身份，不推定增长原因，也不回写先前观察。主要来源：`C:/Users/Admin/AppData/Local/Packages/OpenAI.Codex_2p2nqsd0c76g0/LocalCache/Local/Codex/Logs/2026/10/08/codex-desktop-1aa7db1d-8d43-41b3-9c9e-aa75f27a00e7-115740-t0-i1-015621-0.log`。

下表 received 行明确包含目标 `conversationId=01a0cc2d-5760-7163-82ee-9ac75ff8b177`、kind=commandExecution、requestId；response 行使用同 id、method=`item/commandExecution/requestApproval`、decision=accept，形成直接的线程→请求→决定关联。部分还有 `approval-local-<id>` / actionId=approve。精确命令在 E2 的目标 JSONL 调用中保留；Desktop 这些行不含 argv，下表命令名称通过同线程、唯一顺序调用的起讫时段及完成输出关联，属于跨来源时间关联，未声称 Desktop 自身逐字存了命令。未推定响应操作者身份。

| request ID | 对应 E2 动作 | received 行 / UTC | accept 行 / UTC / 决定 | 通知操作行 |
| --- | --- | --- | --- | --- |
| 57 | canary commit | 12245 / 2026-10-08T04:27:36.800Z | 12252 / 2026-10-08T04:27:41.310Z / accept | 12251 / approve |
| 58 | 发布分支 Gitee 普通 push | 12283 / 2026-10-08T04:27:59.212Z | 12289 / 2026-10-08T04:28:03.373Z / accept | 12288 / approve |
| 59 | 发布分支 origin 普通 push | 12379 / 2026-10-08T04:28:15.398Z | 12389 / 2026-10-08T04:28:17.663Z / accept | 12388 / approve |
| 61 | 显式 base Draft PR | 12469 / 2026-10-08T04:29:02.822Z | 12475 / 2026-10-08T04:29:04.858Z / accept | 12474 / approve |
| 64 | 删除测试 Gitee 普通 push | 12620 / 2026-10-08T04:29:48.982Z | 12627 / 2026-10-08T04:29:53.700Z / accept | 12626 / approve |
| 65 | 删除测试 origin 普通 push | 12663 / 2026-10-08T04:30:04.110Z | 12681 / 2026-10-08T04:30:10.726Z / accept | 未找到独立 action 记录 |
| 67 | 测试 worktree remove | 12817 / 2026-10-08T04:31:10.789Z | 12842 / 2026-10-08T04:31:16.927Z / accept | 未找到独立 action 记录 |
| 69 | 测试本地 branch -d | 12866 / 2026-10-08T04:31:29.412Z | 12870 / 2026-10-08T04:31:32.199Z / accept | 未找到独立 action 记录 |
| 70 | Gitee 测试 ref 删除 | 12937 / 2026-10-08T04:31:46.524Z | 12958 / 2026-10-08T04:31:49.607Z / accept | 12957 / approve |
| 71 | origin 测试 ref 删除 | 12976 / 2026-10-08T04:32:00.058Z | 12989 / 2026-10-08T04:32:04.638Z / accept | 未找到独立 action 记录 |

原 E2 的“宿主审批请求/决定无独立回执”是补证前状态，现有上述直接请求/accept 证据；没有把成功执行本身充作审批证明。通知 action 缺失的条目保留其缺口，不统一推定人工弹窗或无审批。

### 加载仍 UNKNOWN 与诊断入口条件

同一 Desktop 日志的 hooks/list 返回只记录 response_routed、conversationId=null、errorCode=null；例如行 12220（04:27:29.070Z，requestId=76681196-addf-4b9b-96b9-be2313fc7869）。没有 cwd、来源文件/内容、定义版本/hash、trustStatus 或实际加载事件。rule 关键词还含性能抽样的 samplingRuleId，与项目规则不同；均未冒充项目加载。目标 session 的原生事件/元字段无加载/信任字段，SQLite 同执行窗口无独立加载/信任事件。项目文件存在、trusted、列表请求成功、审批回执、实际命令及模式均不能补齐实际加载。

可用工具目录仍没有 Feedback 发送或目标诊断回执查询接口，原生 Desktop 控制不可用；本次发送状态 NOT_SENT，原因 **UNAVAILABLE_DIAGNOSTIC_INTERFACE**，不是授权缺失或新宿主拒绝。未提交反馈、上传日志、调用私有 IPC、另起 CLI 代替、读取凭据、改配置或信任。

已更新 [完整诊断请求](ac24-desktop-diagnostic-request-2026-10-08.md)，另准备 [精简反馈正文](ac24-feedback-text-2026-10-08.md) 供正常入口使用。[官方反馈说明](https://learn.chatgpt.com/docs/reference/troubleshooting)要求从原聊天反馈入口选择会话，分享日志前检查敏感信息。当前正文不含凭据；会话/日志附件尚未逐内容审阅，尤其需核对凭据、个人路径、业务内容及无关浏览器标签，不自动附带。上传成功仍不等于诊断答复。

最小剩余事项仍是可追溯的目标实例项目加载定义/信任/状态/原因/时间及拒绝来源对应记录；现在已有审批请求/accept，可缩小诊断问题。AC-22/24 加载部分 UNKNOWN，原时段 UNKNOWN 永久保留，#555 OPEN、计划 active。记录未提交，旧工作树和 `.playwright-mcp/` 保留。实施来源 Codex，无委派，无产品行为或新测试变更。

E3 补充文档的 diff 空白与四份 evidence 相对链接/尾空白检查通过；沿用 E2 的 146 canonical / wikilinks 校验，不追加功能测试。#555 已同步审批回执和加载缺口，最终回读 updatedAt=`2026-10-08T04:55:40Z`、state=OPEN，正文与预备文件精确一致，SHA256=`acedc9f31874651e048d0d821b60e58148681ba3d6b211014128be3d5a79dfea`；现行 24 条 AC 与折叠历史保持，只同步 7/9/24 三行证据与追加 E3。反馈正文的客户端展示请求返回 queued，未声称已经打开或发送。记录、计划、AGENTS 和草案仍未提交。

## E4：反馈执行授权后的宿主拒绝（2026-10-08 05:01 UTC）

Owner 再次明确“授权执行”，本次复用已准备反馈正文的提交授权，没有重新请求批准。工具目录本次提供了 `mcp__node_repl__js`；按 Computer Use 技能正常初始化 `@oai/sky` 并只读列举窗口，返回唯一候选 `OpenAI.Codex_2p2nqsd0c76g0!App`，displayName/title 为 ChatGPT、window id=`3808850`。这是本次观察，E3 的入口缺失结论保留为当时快照。

随后正常目标窗口读取调用（`sky.get_window` / `sky.get_window_state`）返回原始拒绝：

```text
Computer Use was not approved to use ChatGPT
```

原始来源为目标 session `C:/Users/Admin/.codex/sessions/2026/10/08/rollout-2026-10-08T11-13-41-01a0cc2d-5760-7163-82ee-9ac75ff8b177_01a11980-9d00-7d70-a9a8-b68b6b201678.jsonl`：第 1041 行 `item_completed`（05:01:30.011Z）关联 thread=`01a0cc2d-5760-7163-82ee-9ac75ff8b177`、当前 turn=`01a119df-d166-7932-ad02-71fd0a039505`；第 1042 行（05:01:30.020Z）`custom_tool_call_output`、call_id=`call_fa905296909f4d84aa5c83c0b57a0a2b` 保存上述原错。工具没有给出更细的审批规则 ID 或配置来源；拒绝层的详细来源仍 UNKNOWN，不能归因于项目 rules/hook。

Computer Use 技能 `docs/guidance.md` 默认排除 ChatGPT 桌面 UI 自动化；本次在 Owner 已明确委托反馈提交后尝试正常工具入口，实际入口仍拒绝访问。按 AGENTS.md 的实际拒绝处理要求停止受影响步骤，状态为 **NOT_SENT / BLOCKED_EXECUTION_ROUTE（反馈 UI）**。未取得窗口状态或截图，未调用输入/提交，未上传会话、日志或浏览器附件；没有换工具、私有 IPC、改写调用或修改信任/权限绕过。此拒绝属于本次反馈界面访问，不是 E2 Git 动作拒绝，也不是项目定义实际加载证据。

后续可行选项：**推荐** Owner 在原聊天正常 `/feedback` 入口粘贴 [已准备正文](ac24-feedback-text-2026-10-08.md)，先不附带未经敏感审阅的日志/浏览器材料；或者提供正常诊断入口已允许该目标应用的可核对条件变化，再由 Codex 继续受阻步骤。重复聊天批准本身不证明宿主条件改变。

AC-22/24 的目标实例加载路径、实际定义版本/哈希、项目及 hook 信任、加载/跳过状态/原因/时间与拒绝来源的对应仍 UNKNOWN。#555 保持 OPEN、计划 active；此前成功的独立 Git 链路不重复。记录仅作工作区编辑，未 commit/push；旧工作树及 `.playwright-mcp/` 保留。

### E4 的 GitHub 同步准备亦受阻

读取 GitHub 当前正文确认仍 OPEN、updatedAt=2026-10-08T04:55:40Z，与 E3 完整正文一致。仅在其后追加 E4 的预备正文为 55,884 字符，现行 AC 和折叠历史未改。通过正常 node_repl 文件操作准备 UTF-8 body-file 时，自动审批检查于 05:05:00.096Z 返回原始拒绝：

```text
JavaScript execution exceeds the 64000-byte strict auto-review limit
```

同目标 session 第 1104 行 custom_tool_call_output、call_id=call_a7b49d89f3f9478097197a2800dd710e 保存原错；提交的 JavaScript UTF-8 大小为 102845 字节，确实超过报错中的 64,000 字节上限。没有取得文件生成路径/hash 回执，没有执行 gh issue edit；本轮 E4 **仅更新本地记录，GitHub 尚未同步**。按 AGENTS.md 停止此受影响步骤，不改写/压缩/拆分载荷或换工具绕过检查。此拒绝属于正文准备工具的载荷审批限制，不是 Git 操作拒绝或项目加载证据。同步状态 BLOCKED_EXECUTION_ROUTE，待正常入口条件发生可核对变化后复用授权继续。Issue 保持原 OPEN 状态，计划 active。

## E5：新审批模式下的反馈提交回执（2026-10-08 05:08–05:13 UTC）

Owner 要求在 ask for approval 模式继续。本目标 session 第 1147 行 turn_context（05:08:12.549Z）直接记录 turn=`01a119e9-743b-7270-9732-f42cca305f52`、approval_policy=`on-request`、approvals_reviewer=`user`、workspace-write / network_access=false；第 1142 行 05:08:12.494Z 为线程设置事件。与 E4 的 never / auto_review 分列，模式证据不是项目实际加载证据。

### 逐项复核正常入口

- `gh issue view 555 --repo MJ-AgentLab/mj-agent --json state,updatedAt,url` 在受限网络返回原错 `Post "https://api.github.com/graphql": proxyconnect tcp: dial tcp 127.0.0.1:9: connectex: No connection could be made because the target machine actively refused it.`；按本轮正常 require_escalated 入口执行**同一命令**后 exit 0（chunks `4ce739` / `7fedd0`），仍 OPEN / updatedAt=2026-10-08T04:55:40Z。未改网络配置。
- 原 102,845 字节正文准备 JavaScript 在新模式下原样重试，仍返回 `JavaScript execution exceeds the 64000-byte strict auto-review limit`。目标 JSONL 第 1187 行、05:09:54.082Z、call_id=`call_4a011ccdb4a44b28b1b3cb49e4a45b64` 保存原错；模式变化没有清除此限制，正文准备与 GitHub 正文同步仍 **BLOCKED_EXECUTION_ROUTE / NOT_UPDATED**。未拆分、压缩、改写该载荷或换工具绕过。
- 同一 Computer Use 正常目标窗口读取入口本轮成功；UI 确认当前聊天“继续完成 Issue #555 验收”后，进入 Help → Send Feedback。这只证明本轮窗口访问可用，不证明项目规则加载，也不回写 E4 原拒绝。未修改信任或权限配置。

### 已提交正文，附件数为 0

复用具名正文提交授权，选择 Other，关闭默认勾选的 `Include ChatGPT diagnostic logs` 与 `Include all browser tabs and browser logs`，填入 [精简正文](ac24-feedback-text-2026-10-08.md) 并核对后提交。实际正文按 UTF-8 读取后 trim，共 695 字符，SHA256=`510598a633a720fb6d3d93d0ca42a491abe5a495e9a7f612dcf91dfd352ceec1`。无凭据；未添加会话/日志/浏览器附件。

提交后界面明确显示 **Feedback submitted**，Feedback ID=`01a0cc2d-5760-7163-82ee-9ac75ff8b177`。原始 UI 返回保存于上述目标 JSONL 第 1279 行、05:13:03.407Z、call_id=`call_1bd97d8869b74203a6cc49609a1d6968`；后续同一观察的 text 2684 直接给出 ID。该 ID 与原反馈相同，不把相同 ID 当作独立支持答复或历史加载证据。

原生 SQLite `C:/Users/Admin/.codex/logs_2.sqlite` 第 27354057 行（05:12:54 UTC、ts_nanos=362166400，target=codex_feedback）直接关联原 thread、process=`pid:115512:d28f44c9-467c-4323-878e-0ba63ea77ce0`，记录 `uploaded_attachments=0`、`attachments_failed=false`、`elapsed_ms=301`。Desktop 主日志同 E3 路径第 18256 行于 05:12:54.362Z，method=`feedback/upload`、requestId=`b8bda338-4546-44a0-bba1-0afb1bfb9d61`、conversationId 为目标线程、errorCode=null。这些与 UI 一起支持本次 **SUBMITTED / 0 attachments**；上传送达不保证支持答复，也不满足加载验收。

### 当前最小剩余事项

AC-22/24 的实际来源路径、加载定义版本/hash、项目与 hook 信任、加载/跳过原因/状态/时间及与原拒绝的对应记录仍 UNKNOWN；原 9 月时段 UNKNOWN 永久保留。等待可追溯诊断材料后逐字段复核；没有材料时由 Owner 明确决定剩余范围。#555 OPEN、计划 active。本次不重复 Git 成功动作，记录未提交，旧工作树及 `.playwright-mcp/` 保留。

E4/E5 的完整 GitHub 正文同步仍受阻。本地准备 [具名状态评论草案](ac24-issue-comment-draft-2026-10-08.md) 供 Owner 决定：推荐另行批准将本轮结果发布为独立评论，正文准备拒绝继续保留；另一选项是等待原正文准备入口可核对地解除限制后继续原动作。草案 **NOT_POSTED**，没有将改发评论自动视为已批准的恢复路线。

评论对象为 `MJ-AgentLab/mj-agent` 的 Issue #555，草案文件字节 SHA256=`B73D23E2FFB73009BA6C69A9E8E163ACFE2A941209B5447F948C0EADBBE6C486`。拟议正常命令：`gh issue comment 555 --repo MJ-AgentLab/mj-agent --body-file D:/workspace/10-software-project/projects/mj-agent/develop/evidence/issue-555/ac24-issue-comment-draft-2026-10-08.md`；获批后按实际网络限制走宿主审批。若返回未知，先正常只读回查该 Issue 评论，对比正文、发布时间和操作者，找到对应条目则不重复；没有充分对账前不重试发布。该选项只发布草案评论，不执行 Git 提交或改变 Issue state/AC。

E5 本地 diff 空白、四份记录相对链接与尾空白校验通过，计划 state=active；develop 未新增 staged 内容。`.playwright-mcp/` 原文件 SHA256 仍为 `DA16C930A7AA8D21768A822EA99374E2B788A44186D04B492B74CE086665A943`。正常宿主审批后的最后只读回查 #555 仍 OPEN、updatedAt=2026-10-08T04:55:40Z（chunk 400648），本轮未编辑正文或发布评论。

## E6：Owner 批准的具名状态评论已发布（2026-10-08 05:27 UTC）

Owner 对 E5 选项明确选择“发布具名状态评论（推荐）：把本轮结果登记到 #555，保留正文准备停点。”批准对象仅为 MJ-AgentLab/mj-agent Issue #555 的一条具名评论；其文件 SHA256 紧前核实仍为 `B73D23E2FFB73009BA6C69A9E8E163ACFE2A941209B5447F948C0EADBBE6C486`，正文未变。批准没有扩展到 Git 提交、推送、PR、删除、关闭 Issue 或改动验收范围。E5 的 NOT_POSTED 是该决定前快照。

当前最后原始 turn_context 仍为目标 session 第 1147 行的 on-request / approvals_reviewer=user / workspace-write；评论发布与回读按本轮实际网络条件通过正常 require_escalated 入口执行。紧前只读确认 Issue OPEN，并以具名标题查询现有评论，返回 `[]`（chunks 1cd1da / 3cec43）；只发布一次。

```text
gh issue comment 555 --repo MJ-AgentLab/mj-agent --body-file D:/workspace/10-software-project/projects/mj-agent/develop/evidence/issue-555/ac24-issue-comment-draft-2026-10-08.md
```

命令 exit 0（chunk `0c249d`），返回 [评论 6053008982](https://github.com/MJ-AgentLab/mj-agent/issues/555#issuecomment-6053008982)。原目标 session JSONL 第 1396 行、05:27:34.665Z、call_id=`call_df1f01bc92504d7ca2d560ad202e97f9` 保存发布结果。

随后正常只读 API 回读（chunk `a93450`）确认 id=6053008982、author=`ranzuozhou`、createdAt=updatedAt=`2026-10-08T05:27:34Z`，1360 字符的正文与获批草案**逐字一致（包含尾换行）**；实施者为 Codex，Git 作者配置未修改。目标 JSONL 第 1406 行、05:28:30.759Z、call_id=`call_56958a66149b49e1aad3257917eb89f9` 保存正文核对及 Issue 状态回读（chunk `753049`），仍 OPEN。

完整 Issue 正文只读回查（chunk `1b7071`，JSONL 第 1418 行、05:29:33.722Z）与 E3 保存的 54,378 字符正文逐字一致，现行 24 条 AC 与折叠历史未改；Issue updatedAt=05:27:34Z 来自评论活动。E4/E5 的本轮结果现已登记为获批评论；**完整正文准备仍 BLOCKED_EXECUTION_ROUTE，未因评论成功宣称恢复**，也没有拆分原载荷或覆盖正文。

反馈状态仍 SUBMITTED / 0 attachments，尚无可追溯加载诊断答复。AC-22/24 实际加载定义、来源、信任、状态/原因/时间及与已知拒绝的对应仍 UNKNOWN，原时段 UNKNOWN 永久保留；#555 OPEN、计划 active。最小剩余事项仍是取得并核对目标实例诊断材料，或 Owner 明确调整剩余范围。记录仅更新工作区，未 commit/push；旧工作树、.playwright-mcp/ 和已成功的独立 Git 链路保留，未重复动作。

## E7：反馈之后的只读取证与剩余范围草案（2026-10-08 06:19 UTC 快照）

Owner 对 E6/计划 §22 的剩余事项回复“执行”；本轮继续查找目标记录并准备可审阅选项，未把该回复解释为取消加载验收、批准记录提交或扩大此前具名外部动作。实施者 Codex，未委派；仅更新下列工作区记录。

### 新增来源与追溯程度

1. **目标 session**：仍为 E3/E5 具名 `C:/Users/Admin/.codex/sessions/2026/10/08/rollout-2026-10-08T11-13-41-01a0cc2d-5760-7163-82ee-9ac75ff8b177_01a11980-9d00-7d70-a9a8-b68b6b201678.jsonl`。06:19:56.087Z 检查时共 1538 行；第 1518 行 turn_context 时间 `2026-10-08T06:18:28.575Z`，turn_id=`01a11a25-9f6f-7c50-8b68-38b6ceefc24d`，cwd 为 develop，approval_policy=`never`、approvals_reviewer=`user`、sandbox_policy.type=`danger-full-access`（chunk `3817f3`）。当前模式来源可追溯；不回写 E2 04:27–04:32 UTC 的 OnRequest，也不证明实际加载。按顶层事件类型和结构化 payload.type 检查，没有独立 rules/hook/trust 事件；聊天正文、工具入参和引用旧日志不算宿主事件。
2. **SQLite 增量**：正常 Python 以 `sqlite3.connect('file:C:/Users/Admin/.codex/logs_2.sqlite?mode=ro', uri=True)` 只读查询，固定 UTC 秒区间 `05:12:54 <= ts <= 06:19:56`，条件为目标 thread_id 或原 process_uuid。目标线程 429 行（id `27354044`–`27378012`），线程与进程合计 2476 行；反馈模式标签分别 OnRequest=21、Never=10。按日志 target 及加载/跳过、hooks/list、trustStatus/currentHash 字段筛选候选，唯一候选为原上传行 `27354057`：uploaded_attachments=0、attachments_failed=false、elapsed_ms=301。没有新增独立加载/信任回执（chunk `378d2d`）；输出只保留来源坐标、枚举和数字字段，没有导出原始日志或凭据。计数和候选缺失仅界定本次可查材料，不证明未加载。
3. **五份 Desktop 日志**：只读复查 `C:/Users/Admin/AppData/Local/Packages/OpenAI.Codex_2p2nqsd0c76g0/LocalCache/Local/Codex/Logs/2026/10/08/` 下已知五份日志。E3 的 `codex-desktop-1aa7db1d-8d43-41b3-9c9e-aa75f27a00e7-115740-t0-i1-015621-0.log` 新增候选仍只是 12 条 hooks/list 路由回执（行 `18442/19342/19427/19694/19773/19812/20080/21350/21555/21658/22186/22315`，05:15:26.592–06:14:01.727Z），conversationId/errorCode 都为 null；没有 cwd、定义/hash、信任、加载状态。feedback/upload 仍是行 18256 的旧成功回执。另一个 `...-115740-t1-i1-015623-0.log` 的 16 个含 hook 的候选（行 `352/353/357/358/364/367/368/372/373/374/375/377/378/384/385/388`）全部为 `[git] git.command.complete` / `core.hooksPath`，没有目标 thread_id 或加载/跳过/信任字段，是 Git hooks 参数日志；没有当作 Codex hooks 证据。其余三份未发现本增量的相关候选（chunks `205acd` / `378d2d`）。
4. **补充入口**：当前工具目录没有反馈答复查询、目标线程 rules/hooks 加载报告接口；官方文档说明反馈可关联既有 session ID、日志共享前须检查敏感信息，但没有在所读页面提供反馈答复查询接口或答复承诺。官方 hook 输出目录线索只用于检查 `C:/Users/Admin/AppData/Local/Temp/hook_outputs/<thread_id>` 与 `C:/Users/Admin/.codex/tmp/hook_outputs/<thread_id>` 是否存在，两处根目录均不存在（chunk `3817f3`）；没有读取其他临时内容，缺目录不证明 hook 未运行。CLI doctor 的本机健康报告不等于目标 Desktop 历史加载报告，本轮未另起 CLI、触发 hooks、修改信任或提交反馈。参考：[反馈与日志](https://learn.chatgpt.com/docs/reference/troubleshooting)、[Hooks](https://learn.chatgpt.com/docs/hooks)、[诊断命令](https://learn.chatgpt.com/docs/developer-commands#codex-doctor)。

### AC-22/24 当前字段

| 字段 | 可核实材料 | 结论 |
| --- | --- | --- |
| 线程/执行实例、时间与 cwd | E3/E5 session meta、各 turn_context 和 SQLite process_uuid；E7 当前 turn 另列 | 已验证各具名运行的关联，不混用时段 |
| Desktop 版本 | 原时段 `26.917.51856/build 10492/prod` 已由 Owner 核实；新安装包与 app.asar version 仅为 E3 静态材料 | 历史版本已核实；不作为加载证据 |
| 实际加载路径与覆盖层级 | E3 仓库候选文件路径；hooks/list 回执无来源 payload | UNKNOWN |
| 当时实际定义的版本/哈希 | E3 文件字节 SHA256 为静态参考，不能等同 hook currentHash 或加载快照 | UNKNOWN |
| 项目层与各 hook 的信任决定及生效时点 | trusted 配置和查询路由不提供目标实例决定 | UNKNOWN |
| 实际加载/跳过、原因、事件时间、匹配/运行 | 可查新增记录未提供相应宿主事件 | UNKNOWN |
| 各运行有效模式与动作审批 | E2 OnRequest、E3 请求/accept、E4/E5 模式/拒绝来源坐标、E7 当前 Never | 分时段已验证；不能替代加载或拒绝解除证据 |

### 当前状态与下一步

正常只读 `gh issue view 555 --repo MJ-AgentLab/mj-agent --json state,updatedAt,body,comments,url` 复核：Issue OPEN、updatedAt=`2026-10-08T05:27:34Z`，仅有 E6 已发布评论 6053008982；54,378 字符正文仍与 E3 逐字一致。没有在此可访问材料中取得新增诊断答复；不声称已查询所有支持渠道。`git worktree list --porcelain` 确认两条发布工作树及三条有历史内容的旧 maintain 工作树仍登记，develop HEAD=`9b754a690d0ef0b432d7ea431c2edda1043361b2`（chunk `60cb89`）。旧 worktree 没有编辑/清理；`.playwright-mcp/` 文件 SHA256 仍为 `DA16C930A7AA8D21768A822EA99374E2B788A44186D04B492B74CE086665A943`，E6 评论具名文件 SHA256 仍为 `B73D23E2FFB73009BA6C69A9E8E163ACFE2A941209B5447F948C0EADBBE6C486`（chunk `b0a5b0`）。暂存区为空，未 commit/push 或发布新评论。

AC-22/24 保持真实链路未验证、加载字段 UNKNOWN；原时段 UNKNOWN 永久保留，Issue OPEN、计划 active。E4/E5 完整正文准备的 64 KB 原错继续 BLOCKED_EXECUTION_ROUTE，本轮没有重试或替代路线补绿。已准备 [剩余验收决策草案](ac24-remaining-scope-options-2026-10-08.md)：推荐保留现行要求，取得具名实例加载诊断；另列可明确批准的有限范围调整文本及影响。该草案没有获得范围调整批准，也不授权 Git 动作、再次上传或关闭 Issue。

本轮必要文档校验：`uv run --frozen --no-sync python scripts/check_frontmatter.py` exit 0，146 canonical docs PASS（chunk `537032`）；`uv run --frozen --no-sync python scripts/check_wikilinks.py` exit 0，archive-ref 0、5 个根文件未解析链接 0（chunk `e5d104`）。检查器未覆盖全部 evidence/plan Markdown 相对链接，因此另对本轮四份文件逐链接解析和尾空白检查，均 PASS；`git diff --check` 无输出，计划 state=active、暂存区空、冻结评论与 Playwright 文件哈希不变（chunk `54e4e3`）。按 mj-agent-doc-validate：计划 frontmatter/track 已验证；evidence 无 frontmatter 为既有惯例，A5/A6/A7–A14 无新入口/runtime/原生资产变更而 SKIP，OB 时态与边界人工核对 PASS。以上为文档/静态校验，没有替代实际加载验收；无需重复已通过且本轮未改的功能测试。

## E8：方案 A 获批，正常支持请求已发送，等待账户输入（2026-10-08 06:54 UTC）

Owner 对 E7 推荐项明确回复“同意推荐，授权执行”。批准的是保留现行加载要求、通过正常诊断/支持入口索取具名报告；不是选择 B 的范围调整，也未授权日志/HAR/截图/个人配置上传或新的 Git 动作。Codex 顺序执行，未委派。

### 增量只读取证

- 目标 session 第 1633 行，`2026-10-08T06:49:32.336Z`、turn_id=`01a11a46-3967-7660-a6b3-6064b417bb39`，仍为 never/user/danger-full-access；本轮当前模式与 E2 的 OnRequest 窗口分列。session 至 1661 行的结构化事件没有新增独立加载回执。
- SQLite 只读增量 `06:19:57–06:51:26 UTC` 中，目标线程 166 行、线程或原进程合计 2194 行。出现两个候选元数据：id=27392074（06:47:40 UTC）、27392180（06:48:19 UTC），target=`codex_app_server::message_processor`、同进程、thread 不匹配、正文各 118 字符（chunk `b605e0`）。随后对精确 id 回查已无行，本机只有 logs_2.sqlite；未能保存其原文，原因 UNKNOWN，不将其元数据判为加载/未加载。Desktop 日志同时间仅有 hooks/list 路由，可作时间线索，不能证明候选原文、定义加载或线程关联。
- E3 具名 Desktop `...-115740-t0-i1-015621-0.log` 本增量七条 hooks/list（行 23317/23562/25498/25560/26253/26362/26823；06:29:20.817–06:58:47.358Z）仍为 conversationId=null，无加载/信任/哈希 payload。其他已知日志没有本筛选条件的加载/信任候选（chunk `16d655`）。现有工具目录没有反馈答复/目标加载报告查询工具；原始加载缺口保持 UNKNOWN。

### 正常 OpenAI Support 入口与发送回执

[官方支持说明](https://help.openai.com/en/articles/6614161-how-can-i-contact-support)给出的正常入口为 help.openai.com 右下聊天按钮。使用当前 cua_repl 浏览器 API，仅打开该官方页面和 Open chat；没有控制 Desktop、私有 IPC 或改设置。新页面不是对 E4 反馈 UI 或 E5 正文准备拒绝的重试/替代执行；是 Owner 单独批准方案 A 中的正常支持取证。

已将 [具名支持正文](ac24-support-request-2026-10-08.md) 的 1469 字符正文填入 chatkit 的 Ask a support question... 输入框；发送前与批准内容作空白归一核对，matchesApprovedText=true。请求正文 SHA256=`bd679ba150d76ad234ed6b1d3816b563c6a08bda9c7d9b994b681e7a9e56b36c`；具名文件 SHA256=`0d3e5c561b884c4232b1985fd7a60fb86558885066c5a4cbdaba037a22ee5ee4`（chunk `d0369c`）。本地文件准备时首行曾误带一个模板“+”，已移除；实际填写及发送正文始终为原批准的 1469 字符，未发送该符号，未重复发送。

正常点击 Send message 的 call_id=`call_04b2a45109b64919b905a3f7258bc2f5`，目标 session 第 1707 行 `06:54:15.590Z` 为调用，第 1710 行 `06:54:15.991Z` 为回执；可见界面出现 You said 与完整正文（chunk `2e0b74` 提取坐标）。随后支持页面答复“输入您的电子邮件以继续”/“请提供您的电子邮件以继续”，展示邮箱、继续和登录选项，未给加载报告或案件编号。

Owner 在字段澄清中选择“在支持页面登录或填写邮箱（推荐）：无需在聊天中披露账户信息，完成后我继续”。此后只读核查仍 requiresAccountInput=true；不以选择、等待时长或聊天授权推定账户步骤已完成，没有读取/填写邮箱、密码、验证码或其他凭据。浏览器页面已 markHandoff 保留，当前状态为 **SUPPORT_TEXT_SENT / WAITING_FOR_ACCOUNT_INPUT**，不是已取得诊断或已建立案件的回执。

邮箱停点的 [原始截图](ac24-support-email-gate-2026-10-08.jpg)来自正常 cua_repl screenshot 的既有输出：目标 session 第 1747 行 `06:56:12.607Z`、call_id=`call_929d6b1eba0e4dc48c5f76ae2eb6bf65`，JPEG 220036 字节，SHA256=`c724c81353ba90d81d71de9eca25377d443f7219c31bb2eefea788a7c4e2ab3b`。从该精确已观察图片输出保存到本地（chunk `16d655`）；截图邮箱为空，仅供审阅，没有上传截图/日志/HAR或个人配置，也没有浏览其他标签的内容。

### 当前状态与恢复入口

正常只读 gh 回读（chunk `56f8c5`）：#555 OPEN、updatedAt=05:27:34Z，仍只有 E6 评论 6053008982；未新增 Issue 写入。本计划 active、记录未提交、旧工作树及 .playwright-mcp/ 保留，AC-22/24 的实际加载字段继续 UNKNOWN。当前账户输入是必要信息缺口，不是新宿主拒绝；E4/E5 的已知 64 KB 原始拒绝及 BLOCKED_EXECUTION_ROUTE 原样保留。

下一步：Owner 完成已打开支持页面的账户步骤后，由 Codex 继续读取该支持聊天并按方案 A 六项字段核对；如答复只给一般指引或无法查询原始记录，明确报告缺失，再在同一正常渠道索取所需字段/可用诊断入口。未取得充分证据前不关闭、不改验收范围，不触发 hooks 或重复成功的 Git 链路；若需要任何附件，先准备具名脱敏材料供 Owner 审阅批准。

本轮文档校验：frontmatter 146 件 PASS（exit 0，chunk `0b8ed4`），archive-ref 0/根入口未解析链接 0（exit 0，chunk `f79273`）；本轮五份 Markdown 相对链接、尾空白与 git diff --check 均 PASS（chunk `c3e380`）。支持正文文件/截图、冻结评论及 .playwright-mcp/ 文件哈希与具名记录一致；计划 active、暂存区为空。静态检查只验证记录，不替代加载验收。

## E9：账户步骤完成，人工支持升级已确认（2026-10-08 07:12 UTC）

Owner 回复“完成登录，继续执行”。Codex 沿用方案 A 的正常支持取证授权，在 E8 已保留的同一 help.openai.com/chatkit 对话继续操作；未另建聊天，未重复发送原 1469 字符请求。实施者 Codex，未委派。E8 的 WAITING_FOR_ACCOUNT_INPUT 为当时快照，本节为最新状态。

### 具体来源与可追溯程度

仍使用 E3/E8 的目标 session：`C:/Users/Admin/.codex/sessions/2026/10/08/rollout-2026-10-08T11-13-41-01a0cc2d-5760-7163-82ee-9ac75ff8b177_01a11980-9d00-7d70-a9a8-b68b6b201678.jsonl`。以下坐标是本轮 UI 观察与执行回执，不是目标执行窗口的宿主加载事件。

| 事项 | 原始坐标 / 时间（UTC） | 证据结论与限制 |
| --- | --- | --- |
| 账户停点解除 | 第 1902 行，07:12:10.749Z，call_id=`call_7605c0353a494f5ba71509cc1795610a` | 同一支持聊天显示“已收到邮件”，不再要求账户输入；Owner 已声明登录完成。未读取/记录账户邮箱、密码或验证码，不由此判定 Desktop 身份或加载 |
| 已发送后续取证请求 | 第 1875/1878 行，07:08:39.934Z / 07:08:40.351Z，call_id=`call_06e971f3ca2a466eb1306a85e1088934` | You said 回读发送正文；要求有查询权限的支持/诊断团队处理，并提供案件编号/转交状态、无法取得字段及正常入口；保留不上传附件边界 |
| 支持升级确认选项与点击 | 第 1913/1916 行，07:12:25.968Z / 07:12:26.340Z，call_id=`call_cdb9681f022b41a2a3061889232e2218` | 页面提供“升级”按钮，按方案 A 的既有授权正常点击；点击的立即回执尚未显示完成，未仅凭点击判为成功 |
| 升级完成回读 | 第 1930 行，07:12:41.634Z，call_id=`call_91f28cc5895a47d299548ec4c0640daa`；第 1944 行，07:12:58.726Z，call_id=`call_d7379308b1374dc5b1ccf30371ebfa58` | 先显示“已请求人工支持专员介入”，后明确“已升级给支持专员”，页面说明回复也将通过电子邮件发送。仅证明该支持页面确认转交；未取得案件编号、人工答复或实际诊断报告，不保证时限或已收到邮件 |
| 当前记录 turn 的有效模式 | 第 1890 行，07:12:00.798Z，turn_id=`01a11a56-c692-7830-a465-eb3ee9e620c2` | approval_policy=never、sandbox_policy.type=danger-full-access；与 E2 的 OnRequest 执行窗口分列，不作为项目加载或历史拒绝解除证据 |

发送的后续正文为：

> 页面已确认“已收到邮件”，请继续处理上文的 Codex Desktop 诊断请求。请由能查询目标 Desktop 反馈/运行记录的支持或诊断团队核查，并提供可追溯的案件编号或转交状态。重点实例和所需六类字段均在上文；若此入口不能查询原始加载/信任记录，请明确说明不能取得的字段、记录保留范围，以及可用的正常 Desktop 诊断入口或支持路径。当前截图、文件存在、trusted 配置或命令成功不能代替报告；无需重做 Git，也不修改信任/配置。若必须提供附件，请先说明最小材料和脱敏要求，暂不上传日志、HAR、截图或个人配置。

[原始升级回执截图](ac24-support-escalation-2026-10-08.jpg)取自正常 cua_repl `getScreenshot()` 的已观察输出：第 1937 行，07:12:45.904Z，call_id=`call_fba3d7f223a648e4884386e345e1a4e2`；JPEG 186208 字节，SHA256=`2d42edfff7a99313613a64fbd223631f46fe8ab1bbf3bf4b53de6d1e4bed6e61`。从该精确工具图片输出原样保存本地（chunk `2415a4`）；未上传，未包含邮箱/凭据。截图只证明当前支持升级状态，不追溯证明任何执行窗口已加载。另一次正常 clip 截图为空白，未保存或用作证据；原始完整截图及文字回执可用。

### 状态、最小剩余事项与交付边界

当前支持状态 **HUMAN_SUPPORT_ESCALATION_CONFIRMED / WAITING_FOR_DIAGNOSTIC_RESPONSE**；账户输入不再是待办。没有收到来源路径、当时定义版本/哈希、项目与各 hook 信任决定、实际加载或跳过/原因/时间、与目标线程/turn/进程的关联报告。E7 字段矩阵结论不变：AC-22/24 实际加载及恢复关联仍 UNKNOWN，原时段 UNKNOWN 保留；现行范围未调整。

最小剩余事项：等待并核对同一支持聊天/其邮件答复中的具名实例诊断或可用正常诊断入口；支持若不能提供，逐字段记录 UNKNOWN，并将可观测新实例方案或明确范围调整交 Owner 决定。需要附件时先准备最小具名脱敏材料，检查凭据、个人路径和业务内容，再取得对应上传授权；本轮没有上传日志、HAR、截图、个人配置或其他附件，也没有读取邮箱。未设置后台自动监控。

正常只读复核（chunk `dc31c7`）：#555 OPEN、updatedAt=`2026-10-08T05:27:34Z`；未发布新的 Issue 正文/评论。计划 active，记录仍 UNCOMMITTED；暂存内容为空，验收文件仅保留原有 intent-to-add 状态。冻结 E6 评论、E8 支持正文及 .playwright-mcp/ 文件 SHA256 不变（chunk `ff4136`）。没有 commit/push/PR/删除/merge、信任/配置修改、触发 hooks 或重试 E4/E5 的 64 KB 受阻路线；旧工作树与 .playwright-mcp/ 保留。支持转交不代替验收，不建议关闭 #555。

本轮仅更改记录，必要文档校验通过：`uv run --frozen --no-sync python scripts/check_frontmatter.py` exit 0、146 canonical docs PASS（chunk `8f398c`）；`uv run --frozen --no-sync python scripts/check_wikilinks.py` exit 0、archive-ref 0、根入口未解析链接 0（chunk `dfbeef`）。四份更改 Markdown 的相对链接与尾空白检查 PASS，`git diff --check` 无输出，冻结评论/支持正文/Playwright 文件及新截图哈希核对一致、计划 active、暂存内容为空（chunk `8482a5`）。这些校验不验证宿主加载；未重复本轮未变的功能测试。

## E10：支持专员已答复，历史诊断仍待核查（2026-10-09 07:51–07:54 UTC 观察）

Owner 要求“检查情况”。Codex 对既有支持渠道只读核查，未发送消息或附件；沿用原任务的记录义务更新本地证据和计划，未委派。用户侧时间为 2026-10-09 15:51–15:54 Asia/Taipei；本节 UTC 均为观察/工具回执时间，不是支持消息发送时间。

### 原始来源与答复内容

正常 cua_repl 获取原 help.openai.com 页面，读取同一 chatkit 对话。页面正文仍含原 thread/Feedback ID=`01a0cc2d-5760-7163-82ee-9ac75ff8b177` 和 execution turn_id=`01a119b8-298e-78e2-a42b-48ad103c3d14`；新增答复署名 Chinedu / OpenAI Support，同时显示中文译文及英文 Original。关联仅证明此答复出现在具名支持对话中，不是目标实例的独立宿主事件。界面未给该答复发送时间、案件编号或事件报告，未从观察时间反推发送时间。

原始回执仍在 E3/E9 的目标 session：`C:/Users/Admin/.codex/sessions/2026/10/08/rollout-2026-10-08T11-13-41-01a0cc2d-5760-7163-82ee-9ac75ff8b177_01a11980-9d00-7d70-a9a8-b68b6b201678.jsonl`：

- 第 2113/2116 行，07:51:41.914Z / 07:51:48.428Z，call_id=`call_b4e2c924780b47a88d80a3b18f2acf5f`，既有页面完整 AX 回读，含目标请求与新答复。
- 第 2146/2149 行，07:54:12.863Z / 07:54:13.045Z，call_id=`call_f1f34fd99fcf4e1798b5ff105a009275`，同一 iframe 可见正文读取，核对 thread/turn 均存在并提取英文原文；工具输出不含账户邮箱或凭据。来源坐标只读提取见 chunk `0f8656`。
- [本地原始答复截图](ac24-support-reply-2026-10-09.jpg)来自正常 `getScreenshot()` 回执，第 2135 行、07:53:33.673Z，call_id=`call_f48e25c171c744dc85ca0efd6ce43e30`。JPEG 185368 字节，SHA256=`49613dfd6c9122f0086f2f1c48f49055578e3fd500a158991da0a81c7416cb01`；从该精确已观察图片输出原样保存，未上传。截图可见答复末尾与署名，完整答复以 AX/正文原始坐标为准；它只证明当前支持答复，不证明历史加载。

支持答复的具体进展：

1. 署名专员接手请求，理解当前截图或成功命令不能回答历史实际加载和信任问题；已记录账户邮箱，无须再提供。
2. 后续将检查既有反馈，确定现有诊断工具可访问哪些历史记录，并区分 10 月 8 日与 9 月 23 日实例。
3. 目前还不能确认历史加载/信任决定、保留覆盖范围或六类字段是否均能重建；认可需要对不可得字段逐项说明，不能用当前配置替代历史证据。
4. 当前不要求上传日志、HAR、截图或个人配置；如需材料，将先说明最小材料与脱敏要求。没有要求重跑 Git 或修改信任/配置。本轮未执行这些动作，未把第三方答复当作新增授权。

### 对 AC-22/24 的字段核对

| 待验字段 | 本次答复提供了什么 | 当前结论 |
| --- | --- | --- |
| 原始事件与 thread/turn/进程/实例的关联机制 | 表示会区分两次实例；未提供原始事件、进程关联或事件时间 | UNKNOWN |
| rules/hooks 实际来源路径、覆盖层级及当时版本/哈希 | 未提供加载快照或定义哈希 | UNKNOWN |
| 项目及各 hook 信任决定、适用哈希和生效时间 | 专员明确尚不能确认历史信任决定 | UNKNOWN |
| 实际加载/跳过、原因、匹配/运行及时间戳 | 专员明确尚不能确认历史加载；未提供相应事件 | UNKNOWN |
| 有效模式及其与既有拒绝/恢复的关联 | 未提供新的独立材料；E2/E3 的已验证 OnRequest 与请求/accept 继续单独保留 | 加载/恢复关联 UNKNOWN |
| 历史记录保留覆盖与无法取得字段 | 尚不能确认保留覆盖；未逐项给出最终不可得结论 | UNKNOWN，不将“尚不能确认”写成“记录不存在” |

状态更新为 **SUPPORT_SPECIALIST_REPLY_RECEIVED / WAITING_FOR_HISTORICAL_DIAGNOSTICS**。本次补齐“支持已答复”的进展，不补齐加载验收；AC-22/24 保持 UNKNOWN，原时段 UNKNOWN 保留。最小剩余事项是取得并核对该具名对话的历史诊断或可用正常采集入口；当前没有新材料上传或重跑动作需要 Owner 执行。

### 定时检查、Issue 与工作区

此前只通过 `automation_update(mode=suggested_create, kind=heartbeat)` 生成每 4 小时检查的建议卡片，工具回执仅为 Rendered automation card；没有可核对的创建 ID/启用/运行回执。本次只读检查 `C:/Users/Admin/.codex/automations/*/automation.toml` 的 name/prompt，未找到 #555、目标线程 ID 或人工支持的匹配（chunk `3e3e6a`）。此检查只界定本地可查文件，不证明所有客户端调度均不存在；监测的实际启用/运行状态仍 UNKNOWN。未新建重复任务或改动任何计划任务。若已有任务，原建议的首个人工答复停止条件已出现，但没有精确 ID 可核验/暂停，本轮未声称已暂停；如继续监测诊断，需按明确的新停止条件更新具名任务。

只读 `gh issue view 555 --repo MJ-AgentLab/mj-agent --json state,updatedAt,url`（chunk `7e3fc3`）仍为 OPEN、updatedAt=`2026-10-08T05:27:34Z`。未发布新 Issue 正文/评论，完整正文准备的 64 KB 原始拒绝与 BLOCKED_EXECUTION_ROUTE 继续保留。计划 active，本次工作区记录未 commit/push；没有新的 PR、删除、merge、配置/信任修改或 hook 执行，旧有内容工作树及 .playwright-mcp/ 保留。不建议关闭 #555。

本轮记录校验：`uv run --frozen --no-sync python scripts/check_frontmatter.py` exit 0、147 canonical docs PASS（chunk `002364`）；`uv run --frozen --no-sync python scripts/check_wikilinks.py` exit 0、archive-ref 0、根入口未解析链接 0（chunk `eccba1`）。四份更改记录相对链接/尾空白、新截图和冻结评论/支持正文/Playwright 哈希核对 PASS，`git diff --check` 无输出、暂存内容为空（chunk `24fce0`）。按既有 mj-agent-doc-validate 方法验证记录，无 runtime/原生资产变更；静态校验不替代宿主加载证据，未重复功能测试。

## E11：验收一致性复核与记录交付准备（2026-10-09）

Owner 接受同步执行建议，批准记录交付准备和一致性核对；本轮未获新增记录 commit、push、PR 或 Issue 发布批准。实施者 Codex，未委派。依据根 AGENTS.md 第 4 项及 ADR-034，各实际发布动作在具名审阅包准备完成后分别交 Owner 决定，历史 canary 的批准不扩展至本次记录。

### 当前条款、实现与真实链路

只读 `gh issue view 555 --repo MJ-AgentLab/mj-agent --json title,state,updatedAt,body,url` 取得完整正文，提取第一个 `<details>` 前 24 条现行 AC，保存 [JSON 快照](current-clauses-2026-10-09.json)。观察时间 2026-10-09T08:23:44.620210+00:00、Issue OPEN、updatedAt=2026-10-08T05:27:34Z；完整正文 UTF-8 SHA256=`acedc9f31874651e048d0d821b60e58148681ba3d6b211014128be3d5a79dfea`，54378 字符。提取及矩阵核对工具 chunk `f3960d`：24 条/24 行、22 已验证、未完成项仅 22/24。未改勾选或公开正文。折叠旧方案仅作历史背景。

[一致性审阅](consistency-review-2026-10-09.md)逐项说明 AC-1～AC-24 证据边界。六项曾为“仅静态验证”的 AC-3/6/15/16/21/23 满足各自现行项目或离线条款，但不证明宿主加载；AC-9 的规则加载情况如实记录 UNKNOWN，不借此关闭 AC-24。原时段 Desktop 版本已核实与加载 UNKNOWN 分列。没有整项 AC 被新决定取消，旧 AC-4/9/13 统一 on-request 前置由现行决定替代。

只读对账仍有首轮 `878b474d56e1e4201bba335b60caa9ad7ee018cd` 和第二轮 `6d331438990c458599025bccf3196fabbd694514` 的双端发布 ref；#566/#571 均 OPEN/Draft、base develop。本地删除、Gitee/origin 引用删除、commit→双推→PR 保留各自原始成功记录，不重复执行。`git diff --name-only 9b754a6..0b2f542e466fe36258046c7e8592ed6770e983f2`（chunk `f3f9c6`）仅返回 AGENTS.md、docs/INDEX.md、Site 命名规范三份文档，没有源码、守卫、测试或配置差异；本次不处理 Site 或其他 Issue，不重复既有 T1/T2 功能回归。

### 工作树、基线与精确交付范围

新记录工作树为 `D:/workspace/10-software-project/projects/mj-agent/documentation/555-acceptance-records-20261009`，分支 `documentation/555-acceptance-records-20261009`，基线 `0b2f542e466fe36258046c7e8592ed6770e983f2`。从清洁的旧 canary 工作树执行正常 `git worktree add <上述绝对路径> -b documentation/555-acceptance-records-20261009 <基线>`，chunk `c4899c` exit 0；健康检查 chunk `17ff7b` 确认普通 Git 工作树和正确分支。这里只创建可审阅工作树，没有提交、推送、PR 或删除。

只读远端查询：origin=`https://github.com/MJ-AgentLab/mj-agent`、Gitee=`https://gitee.com/ranzuozhou/mj-agent.git`。origin/develop 与本地基线同 SHA，Gitee/develop=`4e55aae9d78f59ce9b47be43171b5fb33fe95049`；本地对象 left/right 比较 0/2，Gitee 是基线祖先。本次不同步/推送 develop。新记录分支两端不存在、同 head 的现存 PR 查询为空；查询是当时快照，获批发布前须再核对。

推荐 payload 共 15 份：14 份 evidence（本验收、诊断请求、反馈正文、已发布 E6 评论、历史 canary PR 正文、剩余选项、三份支持截图、已发支持正文，以及现行 AC JSON、一致性审阅、新 [记录 PR 正文](records-pr-body-2026-10-09.md)、新 [状态评论草案](records-issue-comment-draft-2026-10-09.md)），另有既有实施计划。拟拆为 `docs(evidence): preserve #555 acceptance and diagnostic records` 与 `docs(plans): retain #555 host loading acceptance as active` 两提交；实际提交 SHA 尚未产生。具名 manifest/授权清单为本地审阅材料，不纳入这 15 份 payload，避免把授权准备当作授权凭证。

三条有内容旧工作树只读统计仍为 2 tracked/0 untracked、5/1、7/475（chunk `afc508`），全部保留。develop 原未提交 AGENTS.md 的两行 Owner 选项原则单独保留，不混入推荐记录包；新工作树的 AGENTS.md 来自基线。`.playwright-mcp/` 只读来源与哈希沿用 E1，未清理或暂存；两份历史 proposed diff 不改动、不重新应用。

### 公开范围、校验与剩余事项

仓库为 PUBLIC。推荐记录含本机路径、线程/进程 ID、既有 Git 作者公开元数据及支持截图中的账户显示名和对话内容；这些需随精确文件清单交 Owner 审阅公开范围。没有读取或摘要禁止的凭据/个人配置文件，未上传日志、HAR、截图或新支持消息。冻结 E6 评论、已发送支持请求、三份原始截图与 Playwright 文件必须保持原字节及既有哈希。实际检查结果在本节后续记录，不将敏感格式扫描当作公开范围授权。

支持进展仍以 E10 首答为准，本轮没有新增诊断或当前状态截图。AC-22/24 actual-loading/recovery=UNKNOWN，原时段 UNKNOWN 永久保留；历史记录尚不可得不能写成不存在。定时检查启用/运行状态仍 UNKNOWN，不新建重复任务。完整 Issue 正文准备的 64 KB 拒绝仍 BLOCKED_EXECUTION_ROUTE；拟议小评论是独立待批准动作，不解除该停点。#555 OPEN、计划 active，不建议 merge 或关闭。最小剩余验收是取得目标实例来源/哈希、信任、加载/跳过/原因/时间与恢复关联，或 Owner 明确调整范围。

本轮源记录校验已执行：`uv run --frozen --no-sync python scripts/check_frontmatter.py` exit 0、147 canonical docs PASS（chunk `e258c5`）；`uv run --frozen --no-sync python scripts/check_wikilinks.py` exit 0、archive-ref 0、5 根入口 unresolved 0（chunk `088d13`）。2026-10-09T08:35:06.893196+00:00 的 15 文件补充核对（chunk `f400fd`）exit 0：24 条/24 行、22 已验证/22 与 24 未完成，全部相对 Markdown 链接存在、尾空白 0、具名凭据格式命中 0；五份冻结评论/支持正文/截图及 Playwright 哈希一致，Plan active/updated=2026-10-09，`git diff --check` exit 0、cached diff 空。邮箱格式仅在验收/计划的既有 Git 作者记录三处；不把这些元数据或有限格式扫描当作无敏感信息保证。新工作树复制后的检查与最终 payload 哈希另列本地具名交付审阅清单；纯记录不重跑功能测试，不证明加载。
