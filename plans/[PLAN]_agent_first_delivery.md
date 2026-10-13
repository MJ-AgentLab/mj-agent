---
type: plan
summary: Agent-first 治理已交付并获 Owner 接受，GitHub 闭环完成，镜像与宿主等延期独立跟踪
owner: ranzuozhou
created: 2026-10-12
updated: 2026-10-13
state: completed
track: engineering-workflow
---

# [PLAN] Agent-first 软件交付改造

## Q20 接受与记录收尾检查点（2026-10-13）

Owner 在本会话真实 Q20 选项中选择「接受治理成果，按上述范围收尾（推荐）」。接受对象为治理 #590 的实际合并版本 `08522a265038d8d9d06f94aa57b83e5e15812630`、当前 develop `5d4b0cd5e4ce5b764a86ab259bec5cc2a8ff04a6` 上的治理兼容复验及已完成的 GitHub 闭环；不代接手会话接受整个 #582。对应接受基线满足、成果已可用，Plan 按生命周期改为 completed；业务接受、仓库审核、集成、实际运行和本次状态文档交付分别记录。

仓外证据根为 `D:/workspace/10-software-project/projects/mj-agent-delivery-evidence/agent-first-delivery/2026-10-12/agent-operated/`；以下相对路径均从此根解析。验收包为 `after-q12-q13/recovery/owner-governance-acceptance.md`，Q20 原始决定与状态文档实际 SHA/PR/集成结果分别留存于同层收尾记录，不在本文写入自身未来提交 SHA。

| 状态 | 真实版本、结果及证据 |
|---|---|
| 治理已集成、已交付 | [PR #590](https://github.com/MJ-AgentLab/mj-agent/pull/590) 由无 bypass App 正常 merge 为 `08522a26`；实际 parents `[a96d759c,06bb0292]` 及 tree 与原 PR CI 的测试合并完全一致。`after-q12-q13/recovery/pr590-actual-governance-merged.json` 与 `actual-governance-delivery-independent-review.md` 分别保存平台及实际版本核验。085 未触发额外 push CI，0 runs/0 checks 为 NOT_RUN，不计 PASS |
| 软件已验证、独立核验通过 | 当前 5d4b0cd5 的治理与 Windows 两包为 15 AC、351＋6 用例通过，零失败/错误/跳过；绑定实际 head/base/tree、输入/依赖、原命令/log/JUnit。`after-q12-q13/recovery/current-develop-governance-delivery/`、`current-develop-windows-delivery/` 及 `current-develop-governance-independent-review.md` 保存原证据与独立重算；32 个并发 #582 改动路径与治理 44/Windows 15 个绑定文件无交集，绑定 Git blobs 相对085不变 |
| 三种 PR 模式与门禁已演练 | 单 PR #590；独立 #593/#594；子 #591/#592→临时 integration，最终 #596→develop。真实 CI/build 红灯、补推旧审核 DISMISSED、未解决讨论阻断、正常解决后 App 临时 merge 均已观察；Q12–Q17 的实际版本批准与门禁结果分记，证据在 `after-q12-q13/recovery/`。负例 App 返回 UNKNOWN 保留原值并对账目标未变，不声称获得 endpoint 拒绝；平台 UI/公开门禁另证实际阻断 |
| App 日常权限及撤销已核验 | App `5284037` / installation `170545174` / repository `1172583390`，仅 Metadata read、Contents/PR write，单仓且无 Administration、Checks write、Workflows write 或 bypass。临时 Workflows 已撤回，每次短期 token 撤销 CONFIRMED，原注册通道已关闭且未重开；`after-q12-q13/recovery/app-audit-daily-closeout.json`、`registration-channel-closeout-pid.json` 与 `app-workflows-removed.png` 分别留证。既有凭据值不进入模型，新 App 材料只由已批准不可见后台处理 |
| Q19 定向规则恢复已验证 | 合并后 protect-develop ID15606888 出现 RepositoryRole5/always bypass，操作者未知；真实 NOT_READY 后暂停。Owner Q19 决定后仅清空当前 bypass_actors，保留全部其他当时 provider 保护字段；`after-q12-q13/recovery/develop-rule-q19-recovery-journal.json` 与 `develop-rule-q19-recovery-independent-review.md` 支持精确恢复，`platform-readback-daily-after-q19.json` 完整回读三规则 CONFIG_VERIFIED、App can-bypass=never。单项设置恢复不等于完整备份恢复演练 |
| Owner 已接受 | Q20 接受上述实际治理成果及已披露限制/延期。原软件包的 `owner_accepted`、`runtime_baseline_eligible`、`independent_source_authenticated` 三项 false 保留；真实聊天接受另记，不改写历史测试声明 |
| 状态文档交付进行中 | 本次仅维护原 Plan 的完成状态、检查点和任务路由 active=false，保留历史决定/证据。正常 stage/commit、App daily push/PR 和不同 Owner 身份的实际版本审核仍分别核验；本文完成状态不冒充该文档 PR 已合并 |

延期持续单列：Q10 Gitee 镜像 DEFERRED/NOT_EXECUTED，Q11 宿主项目信任/hooks 加载与运行 canary DEFERRED/NOT_TESTED；独立受控门禁定义防自降、actual 采样、部署自动化、完整恢复演练和历史 capability 证据渐进迁移均未完成、不计 PASS。首期候选可修改检查定义的风险继续由 Owner 有效审核过渡补偿。原云包搬到 Windows 的 check CLI 不支持完整校验，失败原记录保留；原 ZIP/provider 摘要、实际 Git blobs、log/JUnit/AC 已分别独立核对，不能宣称跨宿主 check PASS。biz/LLM live、部署与实际 runtime 未运行。

本任务 canary 路由例外已按 Q20 关闭（active=false），精确路由作为历史保留。按 Q15/Q17 保留 #593/#594/#596 未合并以及相关分支、工作区和公开证据；develop 未跟踪 `.playwright-mcp/` 保留，#582 遗留目录不操作。没有删除/force/bypass、新身份或付费资源授权，恢复代码走新 PR、平台走已具权正常路线，完整恢复未演练。

重入先核实际 workspace/ref/SHA、当前保护/App 权限、版本证据和文档 PR 状态；成功操作不重复，未知先对账后决定是否重试。当前下一步仅完成本次记录的正常验证/提交/PR/有效审核与集成回读；实质版本/对象/权限/风险或保护漂移只暂停受影响项。Owner 决定与认证按本会话真实 Q 记录追溯；起点、全程耗时、成本和总 token 未完整采集仍为 UNKNOWN，不推算。以下旧「当前」「下一步」及 active/待接受表述均保留为对应阶段历史，不替代本检查点。

> 最新scope决定：Owner在本会话真实选项中明确确认#582转交聊天“整理 #564 EVAL 承接方案”。本会话继续治理软件部分和#582治理证据格式要求设计；CLI实现/commit不再纳入本会话。原接受基线保留为历史任务边界，接手会话维护新的CLI基线。

> 执行主体新决定：Owner明确回答Q4/Q5/Q6，取消工程师向导，全流程由Agent执行。平台Q3目标/对象/权限/规则不变，仅新单仓App材料可经受控后台不可见地创建/DPAPI保存/签名/注入/撤销；独立Agent审阅真实配置/守卫负例后，执行Agent经正常宿主机制启用本项目信任。Owner在聊天对实际成果/SHA作批准/接受决定，Agent依决定用不同于作者/末推送者的Owner身份执行审核。原向导已superseded，仓外旧文件保留历史。

> 来源：Owner 本轮 `PLEASE IMPLEMENT THIS PLAN` 及所附完整 Agent-first 计划。ADR-042 记录已批准治理决定；本 Plan 保存接受基线、动作授权、真实实施状态和恢复入口。批准实施不表示已接受成果或完成平台启用。

> Q10/Q11 最新范围决定：Owner 明确选择本任务 GitHub 发布、Gitee 被动镜像延期，并延期宿主运行验收，继续 GitHub 闭环。例外仅绑定 `agent-first-delivery`、治理分支 `maintain/agent-first-delivery` 及原计划六个具名 canary head/integration：`feature/agent-first-canary-single`、`feature/agent-first-canary-independent-a`、`feature/agent-first-canary-independent-b`、`feature/agent-first-canary-child-a`、`maintain/agent-first-canary-child-b`、`feature/task-agent-first-canary-integration`，仅向 `MJ-AgentLab/mj-agent` 的 origin 发布；不新增其他分支、取消默认双推或扩新 App 例外到 Gitee。宿主项目/hooks 运行验收 DEFERRED、实际仍 NOT_TESTED，保留原信任规则；延期不计 PASS，也不等于 Owner 已接受版本。最新状态见「Q10/Q11 当前交接检查点」，后续旧软件段落保持历史语境。

## 原接受基线与当前生效范围

- 目标：Agent 在明确任务授权内自主构建/验证，Owner 作实质决定并依据成果和风险证据接受；直接消费者一致，不以新增 override 掩盖旧固定停点。
- 治理：同步政策、阶段检查点、开发技能/发现描述/图/交接、模板、冻结契约、原生守卫及 CI。保留领域参数、命令、反扫、异常恢复与验收步骤；旧 ADR 和冻结历史证据不改写。
- #582原基线（TRANSFERRED，保留历史任务边界）：保持 ReplayInputs/replay 纯内存公开行为及既定32检查、22-case、严格窗口/状态/阈值；文件CLI补齐本地路径/限额/输出防覆盖/IO错误/真实进程退出并取得独立运行证据。
- Harness：schema/trace违规真实非零失败；`ci`、`docker-build`覆盖支持目标，版本绑定仓外artifact记录产物/输入/依赖摘要、环境/命令退出/逐AC，负例能发现错误。
- 平台：仅本仓专用安装身份、有效独立Owner批准及最后推送审核、严格版本检查/讨论解决/禁止force/bypass。GitHub 规则及发布演练仍须实际证据；Q11 将本次宿主项目/hooks 加载与运行 canary 验收独立延期，保留独立 Agent 核验后正常宿主启用的规则。文件准备不能计平台运行通过。
- 永久边界：biz只读工具链、SQL不变量、秘密保护、禁入MCP、项目范围信任先独立Agent核验再正常宿主启用，禁止个人config/权限扩张及技术拒绝绕过。
- 延期：独立受控强制核验系统、actual采样、部署自动化、实际恢复演练、历史capability证据渐进迁移。候选能改自身gate定义的风险首期由Owner审核补偿，尚无防自降可信执行证明。

## 执行授权与停止条件

授权来源为Owner实施请求及最新转交决定，当前覆盖已审定治理/CI/原生守卫改造、#582治理证据格式要求设计、相关本地验证/文档及治理工作区正常stage/commit；新App注册/DPAPI后台/项目范围正常宿主启用和依真实Owner决定执行审核按Q3/Q4/Q5/Q6边界推进；CLI实现/commit已转交，不纳入本会话。普通内容迭代核实际diff/staged/SHA，范围、对象、环境、权限和风险未实质变化时复用。

| 对象/动作 | 条件与状态 |
|---|---|
| 治理工作区 | `D:/workspace/10-software-project/projects/mj-agent/maintain/agent-first-delivery`，分支 `maintain/agent-first-delivery` |
| #582 工作区 | TRANSFERRED至“整理 #564 EVAL 承接方案”；转交时路径（历史）为`D:/workspace/10-software-project/projects/mj-agent/feature/582-offline-eval-cli` / `feature/582-offline-eval-cli`，现已由接手会话按其授权清理登记/分支，见最新develop状态。本会话不操作其遗留目录 |
| 比较基线 | 两工作区创建/核查时 HEAD `5b8833c523f4401de7b70deb5a82b908f3a9c763`；每次执行重新核现实 |
| push / PR / merge | Q10 仅 origin / `MJ-AgentLab/mj-agent` 发布本任务分支及原已授权具名 canary，Gitee 为 DEFERRED/NOT_EXECUTED；通过专用 App、实际门禁和 Owner 对实际成果/SHA 的有效决定推进 GitHub 闭环，不用个人 admin 替代日常 App 身份，不隐含删除或 force 授权 |
| 平台/信任/新App材料 | 新 App 单仓安装与 bootstrap 审计已实际完成；旧候选平台回读 CONFIG_VERIFIED，详见本轮检查点。Q11 宿主运行验收 DEFERRED、实际加载仍 NOT_TESTED；新 App 材料仅受控后台处理、既有秘密不读，原信任/权限/拒绝边界保留 |
| runtime/live | 本次不授权实际runtime/LLM/biz采样、容器生命周期或部署；synthetic只证明软件行为 |
| 删除/权限变更 | 不从普通实施授权推定；清理须独立精确对象、必要备份、损失及恢复条件 |

停止受影响项：授权撤销或目标/对象/环境/权限/风险实质变化；接受标准或安全/业务/外发/breaking/gate变化未决定；实际技术拒绝；秘密/数据边界风险；必要前置缺失。部分成功或结果未知先对账副作用，成功步骤不重复。资源按实际平台支持与任务限制安排，无新增付费资源或自动更换模型。

## 任务、依赖与文档

原拆分为两个独立PR单元；Owner最新决定后，本会话仅治理单PR通常指向develop，CLI独立单元TRANSFERRED。以下CLI方法是原计划历史边界与依赖交付记录，不执行。分层路由只是未启用canary准备，登记不产生授权。

1. 治理单元：ADR/政策/SDD/入口/技能/模板一致性 → guard/CI/schema/trace/证据改造 → 离线及负例核验 → 独立审阅。
2. #582 单元（TRANSFERRED，不在本会话实施/commit）：T-006文件适配 → 公共CLI契约/文档/trace → unit/BDD/真实CLI进程与22-case复现 → 独立核验。
3. GitHub 前置：专用单仓 App 与受控后台、实际平台规则、独立 Agent 技术核验及具名 GitHub canary；按 Q10/Q11 限定范围核依赖，宿主运行验收与 Gitee 镜像单列延期，不用延期替代 GitHub 门禁或有效审核。
4. 最新完成基线包含治理软件部分、#582治理证据格式设计及新增受控后台/独立Agent审阅/平台执行的实际验证；Q10/Q11 将 Gitee 镜像和宿主运行验收独立列为 DEFERRED，当前 GitHub 闭环继续，其他未实现或未运行项仍不通过。CLI真实交付依赖由接手会话继续tracked，不要求Owner重述已有决定。交付：实际版本验收包、限制延期、风险恢复及Owner待决定；有效平台批准与业务接受分别记录，未接受不completed。

文档决策：治理ADR/指南/本Plan新增；活动政策/工作流/技能/描述/模板/索引及原生保护说明更新；#582 CLI contract/指南/trace由该独立单元维护；历史ADR、归档记录、原验收证据不改写。并行写按文件归属与独立工作区；共享平台写由协调者排序。

<!-- agent-first-routes
{"schema_version":1,"routes":[{"task_id":"agent-first-canary","repo":"MJ-AgentLab/mj-agent","active":false,"integration":"feature/task-agent-first-canary-integration","mainline":"develop","children":["feature/agent-first-canary-child-a","maintain/agent-first-canary-child-b"]}]}
-->

路由供有限守卫观察事实，不认证授权。原关系按 Q3 具名演练范围及 Q10/Q11 激活，现按 Q20 完成任务后关闭；active=false 保留关系历史但不再允许新任务集成例外，不删除既有 PR、分支或工作区。

平台 canary 准备清单（当前尚未创建/执行）：单 PR 与最终成功 develop 交付复用真实治理 `maintain/agent-first-delivery → develop`。独立 PR 模式保留 `feature/agent-first-canary-independent-a → develop` 及 `feature/agent-first-canary-independent-b → develop` 的真实创建、各自 CI/有效审核及阻断观察。分层模式由 `feature/agent-first-canary-child-a`、`maintain/agent-first-canary-child-b` 分别指向登记的 `feature/task-agent-first-canary-integration`，验证子 PR 门禁及成功临时集成；再保留最终 `integration → develop` 的真实创建/门禁观察，不以治理单 PR 或子 PR 代替该路由证据，也不要求临时 canary 成功 merge develop。在 Agent 核已有 Q3 授权、实际规则/身份及副作用后登记真实 SHA/PR，验证补推使旧审核失效、Owner 有效批准、CI/构建红灯和讨论未解决阻断、无 bypass merge。Q11 只延期宿主运行验收。删除临时对象另列真实清单、备份及授权。

## 新后台任务与验收条件

### Q10/Q11 当前交接检查点

- 本次范围记录修改开始时真实 HEAD 为 `edd2e1eec561e5f32c9cc92030823e52064c9220`，比较主线为 `a96d759c080f4568e6810084f90fadce7b2c75cf`。这是已观察旧版本，不是本文档提交后的自引用 SHA；新版本产物另存仓外 `agent-operated/after-q10-q11/`，尚未生成或 binding 不符不得宣称通过。后续发布/验收读取实际 HEAD、diff 及新证据 binding。
- 已读取仓外 `agent-operated/after-q9/app-audit-bootstrap.json`：App `5284037`、installation `170545174`、repository `1172583390`，EXECUTOR_VERIFIED，三层仅 Metadata read、Contents/PR write、临时 Workflows write，单仓 token 撤销 CONFIRMED。新 App 例外不扩 Gitee，既有个人/MCP/DB/App 秘密不读。
- 同层 `platform-apply/journal.json` 保存规则应用 APPLIED_PENDING_EXECUTOR_READBACK；独立 `platform-readback.json` 在旧候选 edd2e1e 上 exit0、CONFIG_VERIFIED，三规则保护摘要匹配且 App can-bypass=never。这里只证明已观察的平台配置/执行身份，不证明 GitHub canary、发布、宿主加载或 Owner 接受；后续版本/配置变化时重核适用性。写前备份在 `agent-operated/platform-backup-before-apply/`，恢复演练未运行。
- Q10：仅本任务及原已授权具名 canary 的 origin 发布，默认 Gitee-first 双推继续用于其他任务。Gitee 镜像 DEFERRED/NOT_EXECUTED；不得报告双推完成，不探测或借用现有 Gitee 凭据。恢复镜像需独立具名执行身份、对象及动作授权，并核真实 ref/tip 后补齐，当前不新建该身份。
- Q11：宿主项目/hooks 加载及运行 canary 验收 DEFERRED，实际结果仍 NOT_TESTED。仅延期本任务接受范围，不修改个人 config、原生信任或权限规则，不调用会暴露个人 hooks 的接口，不绕实际技术拒绝。GitHub canary/CI/有效批准仍分别留证。
- 当前下一步为本次范围文档验证与实际版本检查，再继续已授权 GitHub 发布/审核/集成闭环。Owner 最终接受未作出，Plan 保持 active；临时 Workflows 权限撤回、短期 token 撤销及通道关闭独立核实际结果。
- 协调者已报告 fresh 公开只读预发布核对，证据为同层 `after-q10-q11/prepublish.json`：正常 Owner 身份 `ranzuozhou`，develop 仍为 a96d759，治理远端 ref/PR 当时不存在；这只记录该次观察，不代替实际发布成功或随后远端变化核验。本文件不引用自己的未来提交 SHA。

### 以下为 Q10/Q11 前的软件与平台历史检查点

- 文档修订从真实clean HEAD `8bf8888e573991ee09fb1cb5b5fea6a419c48d56`开始；8infra旧16摘要/8节标题集先实算匹配。新主体修订仅3infra技能必要正文/描述变更，按canonical算法再冻结于`2026-10-12T06:30:56Z`，冻结不证明后台或宿主运行。
- 本轮文档/native静态fresh验证逐命令exit0：skills/resources STATIC_PASS，codex config STATIC_PASS（rule_loading UNKNOWN、host NOT_TESTED、Owner审批NOT_ASSESSED），frontmatter154、wiki零、looprefs零/20sections、diff格式通过；这些不证明App后台/注册/信任启用/平台已运行。
- 新后台由evidence_implementation维护`scripts/sdd/delivery_executor.py`；本文档单元不改.py/CI/tests，不触CLI工作区。私钥/token/JWT值不得出现在模型/聊天/日志，既有应用/MCP/DB/个人秘密始终不读。
- 独立技术审阅绑定真实配置/守卫与负例结果；正常宿主仅本项目启用必须核实际支持、加载与canary，未知/不支持如实未验证，不借个人config或权限变化绕过。
- Owner聊天决定绑定实际成果/SHA；平台审核执行身份须与作者/末推送者不同，实际review/merge状态留证。App作者身份无admin/checks-write/bypass，执行授权不扩大。
- 注册/签名/注入/撤销/信任及平台启动未运行前不得PASS；旧软件日志是原版本证据，不复用为新增后台行为证明。整体Plan仍active，Owner最终接受未完成。
- 本轮后台第一轮完整离线运行为1487通过/6策略跳过/82未选/30subtests，日志在仓外`agent-operated/verification/`。独立审阅随后发现Git本地配置干扰、连续观察身份绑定、写入路径复验及Python启动环境继承问题；旧运行不作为修复后候选最终证据，闭合后重新验证并绑定实际版本。
- 当前宿主`codex-cli 0.147.0`公开协议的`hooks/list`会返回原始命令及用户/系统来源，缺少服务端project-only/metadata-only筛选，本会话未调用；正常CLI尝试未取得项目实际加载/信任canary证据。未读取个人配置/命令，未用bypass或修改个人配置，宿主项保持NOT_TESTED；未观测技术拒绝时不冒称BLOCKED_EXECUTION_ROUTE。实际平台工作与该状态分别记录，依赖条件不自动豁免。
- 新版本逐项软件验收使用更新后的`evidence/delivery/agent-first.suite.json`，仓外产物另存`D:/workspace/10-software-project/projects/mj-agent-delivery-evidence/agent-first-delivery/2026-10-12/agent-operated/final/delivery/delivery.json`，原8bf8888验收包及本轮首次引用失败包保留历史。新增后台和连续权限审计均以SELFTEST_SOFTWARE记录，真实平台注册/安装/权限/宿主/平台演练待实际核验。
- Windows原生软件验证独立使用`evidence/delivery/executor-windows.suite.json`，产物另存同层`final/windows-delivery/`，必须核实际head/base、源码摘要与通用包相同；Linux合法SKIP不得冒充Windows通过。当前不新增付费Windows CI资源。
- GitHub规则API仅向具有规则写权限者显示bypass actors；执行App不增加Administration。具名管理只读核验通过明确`--management-inspect`补足隐藏名单，先核fresh App身份，再核真实`ranzuozhou`及同rule保护字段一致，App自身can-bypass仍独立核。缺失、冲突或实际API拒绝不切备用路线。
- 最新develop已更新为`a96d759c080f4568e6810084f90fadce7b2c75cf`：#588依赖更新及#589 synthetic-only CLI已合入；#582/其Plan仍OPEN/active、actual/live未运行。转交时未提交材料/feature工作区记录保留历史，接手会话已按其授权清理登记/分支并保留备份；本会话不操作其遗留空目录。治理候选须纳入这一实际基线再作组合验证。
- 平台备份已由正常具名Owner路线只读获取，目录为仓外`agent-operated/platform-backup-0810/`；当前观测protect-develop/main两规则、无integration、无其他规则及三种merge均启用，管理身份仍具仓库admin/maintain/push。仅证明当前读权限/备份和可用恢复身份，未改平台、未演练恢复；写前重核状态与备份一致。
- 本轮组合软件检查点：`45f0557`纳入Q4/Q5/Q6及后台，正常合入实际develop后的`ef5eed0`全量离线1643通过/6策略跳过/30subtests，BDD23通过/7策略跳过，contract63通过/1Windows软链接权限不足跳过；ruff/mypy55源文件通过。日志在仓外`agent-operated/verification/integration-final/`。独立Agent复验了真实Windows来源/路径/hook/signing及异步回调负例，注册子流程代码GO；不等于安装、平台或宿主GO。
- 初次通用collector命令通过，却因回调测试新增参数化后套件旧引用缺失而返回NOT_TESTED；失败包`agent-operated/delivery/`保留。仅把该引用绑定已实际运行的三个参数用例，不改断言或接受条件；更新后候选SHA及14软件AC、Windows6用例结果以final两包实际binding为准，未生成/错配不算PASS。
- Q7正常Owner二次认证已完成，浏览器仅核公开页面title为Create GitHub App，不读密码/验证码。截图在仓外`agent-operated/browser-proof/github-sudo-required.png`保存认证要求。当时尚未创建/安装App、激活项目信任或写入平台；创建/安装在提交前遵循浏览器工具的安全访问确认，接受及发布授权仍分开记录。
- Q8实际动作确认后，Agent通过正常GitHub manifest创建私有`mj-agent-delivery-executor`，App `5284037`仅安装到mj-agent，installation `170545174`、repository `1172583390`。bootstrap实际审计exit0为EXECUTOR_VERIFIED：App/installation/token层均仅Metadata read、Contents/PR write、临时Workflows write，单仓短期token已CONFIRMED撤销；既有秘密未读取，新App值仅后台DPAPI托管。公开运行证据在仓外`agent-operated/final/app-audit-bootstrap.json`，安装截图在`agent-operated/browser-proof/github-app-installed.png`。浏览器本机结果页实际拒绝`net::ERR_BLOCKED_BY_CLIENT`保留，没有改安全设置或重复注册；后台公开结果与正常GitHub页面闭合。注册通道已核具名进程/端口关闭，后续audit走已核验后台，不需要重开注册。
- 本候选真实无token预检曾返回TOOLCHAIN_CONFIG_UNTRUSTED；只读名称诊断为`alias.pushall`及8条分支IDE缓存键，未读值/改配置/放宽门禁/执行发布。作者与独立Agent各自仓外复现27个分类用例、5个实际本地合成Git命令，固定命令不触发alias、正控触发、接收库零refs，原守卫仍拒绝。Owner Q9明确批准仅这两类惰性键定向兼容；实施回归、独立核验及新版本正常预检闭合前，发布保持BLOCKED_EXECUTION_ROUTE，其他实际拒绝不豁免。
- 实际平台只读复核先返回UNKNOWN；无改动诊断证明同一App的audit、rulesets及protect-develop GET均成功且token撤销CONFIRMED。原因是公开投影省略原始pull_request的required_reviewers/dismissal_restriction/require_extra_approval_for_unattributed_changes参数，造成完整保护比较不等。修复以后台原始保护规范摘要作严格同源比较，不删除参数或放行错配；对应负例与版本证据必须重新取得。平台规则尚未应用、宿主仍NOT_TESTED、canary/推送/PR/merge/Owner接受均未完成。
- Q9后的新候选通用/Windows软件包另存仓外`agent-operated/after-q9/delivery/`与`agent-operated/after-q9/windows-delivery/`，绑定实际新head/base及输入摘要。原`final/`14AC/304通用用例与Windows6项独立通过包保留为26487aa历史证据，不能因旧软件通过宣称新版本通过。实际状态与下一步记录在新验收说明；未生成或不匹配时保持未知。
- Q9定向实现完成后，作者真实本仓无token/无网络预检为PUBLIC_METADATA_PREFLIGHT_PASS；独立Agent从实际两模块复验234项离线测试exit0，并验证完整未知参数一致可比较、改变立即拒绝、原始私有sentinel不透传。套件绑定新行为IDs及123/117/111最低用例数；新版本与证据包仍须实际闭合。该软件及元数据预检结论不替宿主加载、平台保护/演练或Owner接受。
- Q9后本地完整unit运行1593通过、1项非Windows覆盖条件跳过、30subtests通过，exit0；日志和JUnit保存于`agent-operated/after-q9/verification/`。该补充运行处于提交前，随后版本绑定collector仍须对实际新SHA执行。ruff/mypy55、frontmatter154、wikilinks/looprefs及native配置/技能检查均exit0；此前BDD/contract运行保留原版本，不谎报已重跑。

## 原软件验证与当前未验证检查点

| 项目 | 当前结果/证据边界 |
|---|---|
| 根协调者原软件版本离线验证（不证明本轮新增后台） | 当时完整离线测试exit0：1416通过、6跳过、82未选、30subtests通过；BDD19通过/7策略跳过；contract63通过/1Windows软链接权限不足跳过。ruff/mypy（53源文件）、G1/G2各7、frontmatter154、wikilink/section refs及原生检查通过。先前3个永久边界原文断言失败已保持断言恢复表述；随后1个EOL夹具失败修为单变量并65证据域复验通过。实际日志在仓外验收包，不声称CI/平台运行 |
| #582 CLI | TRANSFERRED；协调者确认HEAD `5b8833c523f4401de7b70deb5a82b908f3a9c763`、全部未提交材料完整保留、无在途/无push；此前130项/Windows别名及独立复验状态作为原检查点转交，接手会话维护新基线 |
| 文档/技能（原软件基线记录） | 治理Agent已恢复全部37技能原领域方法并定向同步；分别fresh exit0：skills/resources STATIC_PASS、154 canonical frontmatter PASS、wikilink零违规、looprefs零（20sections）、diff检查零；平台/宿主/完整Harness未由这些静态检查证明 |
| infra冻结 | 修改前8×description/body共16旧hash及section heads实算匹配；8infra正文方法保留。治理初次冻结2026-10-12T04:29:22Z；独立审阅发现compose删除授权复用旧句后定向修复，该项hash/heads再冻结2026-10-12T04:49:22Z，fresh检查STATIC_PASS |
| 平台/身份/宿主canary | NOT_READY / NOT_TESTED / NOT_RUN，只有准备文件和只读核验入口，不计实际强制证明 |
| Owner接受 | 未决定；成果仍在实施/核验，不completed |

最终独立核验：Standards定向闭合所有发现；Spec实际188项通过，真实JUnit核套件10个AC/74条ID无缺失/失败/跳过，原未跟踪输入完整链现拒绝，合法本地Git链来源LOCAL_OFFLINE_RUNTIME且无法重标cloud。随后明确增加已通过的真实PR路由进程用例绑定，共75条引用，最终以collector为准。所有AC为软件SELFTEST，不替实际平台/运行验收。治理候选具名暂存135件（含本轮CHANGELOG），未包含原develop材料或已转交CLI。

本地复现入口：`scripts/sdd/delivery_evidence.py` 的 run/check，套件 `evidence/delivery/agent-first.suite.json`。先核干净的已提交候选版本；Windows交付输入依据`.gitattributes`保持LF；输出必须仓外且尚不存在。真实本地运行显式使用`--execution-kind local`及`local://offline/<safe-id>`；CI使用github-actions类型。分别提供实际head/base SHA、repo与output-dir，两种来源不互相冒充。完整命令、SHA/输入/依赖/blob摘要、逐AC及限制保存在生成的仓外delivery.json和命令原始日志，版本变化后重评，不把文档中的旧数字当新证据。

### 原软件历史交接检查点（当时软件候选已验证，平台待启动）

- 软件实现提交 `cf1bbd97031a820b9d7c44e7a4904bc04b234a7d`，真实本地collector run/check与独立check均exit0：10AC/75条测试引用软件通过，42提交文件摘要闭合，source LOCAL_OFFLINE_RUNTIME，Owner接受/运行基线资格/来源认证均false。
- 完整离线日志在 `C:/Users/Admin/AppData/Local/Temp/mj-agent-agent-first-20261012-0510-01a12e01/`；初次collector严格拒绝3个EOL属性切换后的旧index状态。逐文件证明原始bytes等于HEADblob，正常刷新index，确认无内容差异且输出未创建后重试成功，没有降低检查。
- 本次检查点是文档记录更新，未改变软件或接受标准。最终分支HEAD与测试版本读取仓外长期验收包：`D:/workspace/10-software-project/projects/mj-agent-delivery-evidence/agent-first-delivery/2026-10-12/delivery/delivery.json`；说明文件为同层`acceptance.md`。引用稳定位置而不在自身正文写入未来SHA，避免提交哈希循环。若文件尚不存在或与HEAD不符，保持未知并核在途动作，不能据正文宣称通过。
- 当前无push/PR/merge/平台配置/信任激活/live副作用；#582已转交且本会话不再写入/测试。重入先核实际branch/HEAD、clean、artifact版本和未决授权。实际执行身份仍缺专用App，当前个人admin不得替代；原工程师向导已由新决定superseded，Agent受控新App后台/独立技术审阅/正常宿主项目启用和平台canary仍待真实验证。
- 接受状态：待Owner明确实际版本及范围。整体Plan仍active；若只接受软件并延期平台，须Owner作明确范围决定并分别跟踪，延期不计通过。

独立审阅分 Standards 与 Spec 两轴，均直接读取实际候选并按基线建立期望。此前发现的路径别名、合并对象错配、授权风险复用、仓内JUnit路径、无关SHA、未跟踪输入及Owner审核缺口都以负例驱动修复；最终运行结果绑定真实Git版本。Windows通过仓库 `.gitattributes` 固定交付输入LF，保留严格working/blob字节比对，不修改个人配置或降低接受标准。

原软件阶段运行记录：Owner新增职责转交决定，未逐项审批普通实现。随后Owner变更启动执行主体并选择Q4/Q5/Q6；这些属于凭据、信任和结果决策，仍不逐项审批普通修复。协调者按明确文件归属并行执行，真实并发上限为根加3子Agent；独立核验实际选择high effort，作者继承会话配置，未更换模型或新增付费资源。开始时点、完整成本和总token未被独立记录，标UNKNOWN；测试耗时只使用实际运行输出，不推算总体交付周期。缺陷/返工保留上述审阅与红→绿记录；恢复演练尚未运行。

验证矩阵按实际变化运行相关离线unit/BDD/CLI、ruff/mypy、frontmatter/wikilink、native配置/技能及gate负例。external pytest通过hardened runner结构化SKIP，不计PASS。独立核验者从AC建期望，读取真实成果并复现；另一Agent的通过总结不能替代运行证据。

阶段完成、集成前或交接时更新：目标/AC/授权、工作区/ref/SHA、已集成/验证/交付/接受状态、证据位置、在途副作用/失败/未知/延期、下一步与停止条件。#582 转交时无push/未提交材料保留及“无平台注册/规则应用”属于历史检查点；后续 App 安装、规则应用和回读已分别留证，当前状态以 Q10/Q11 检查点及实际证据为准。本会话不操作 #582 遗留目录，不把配置回读计作发布或 Owner 接受。

## 交付、恢复与待决定

提供成果使用入口、逐AC预期/实际、实际版本环境时点与复现artifact、未测/延期、风险/恢复以及待Agent实现/验证与Owner实质决定事项。记录Owner介入、周期、缺陷返工、门禁负例、证据完整性和资源消耗，不能以命令/HTTP成功独自证明业务正确。

恢复：代码/规则通过成组回退PR和独立具权路线，具名资源操作先核实际备份；未进行真实恢复演练。治理交付结束由Agent按授权移除App临时Workflows write、撤销新App短期token并关闭通道，逐项留证。

下一步：按 Q10/Q11 核当前软件版本与 App/平台证据 → origin 发布及实际 GitHub CI/canary → Owner 对实际成果/SHA 决定、不同身份有效审核 → 授权内集成核实 → Owner 明确接受版本及延期清单。Gitee 镜像与宿主运行验收单列 DEFERRED，不计 PASS；默认双推/原生信任规则及其他必要 GitHub 门禁保持。#582 独立后续由接手会话维护，本会话不重建已合入的 synthetic-only CLI。

## 关联文档

- [ADR-042](../decisions/ADR-042_Agent_First_Delivery_Governance.md)
- [交付指南](../docs/guide/[GUIDE]_Agent_First_Delivery.md)
- [接受与授权](../policies/ai-agent.md) §4
- [生命周期](../sdd/lifecycle.md) §2
