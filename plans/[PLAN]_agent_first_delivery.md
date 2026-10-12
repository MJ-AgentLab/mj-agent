---
type: plan
summary: 交付 Agent-first 治理软件与证据格式设计，#582 CLI 已转交且平台前置与接受未完成
owner: ranzuozhou
created: 2026-10-12
updated: 2026-10-12
state: active
track: engineering-workflow
---

# [PLAN] Agent-first 软件交付改造

> 最新scope决定：Owner在本会话真实选项中明确确认#582转交聊天“整理 #564 EVAL 承接方案”。本会话继续治理软件部分和#582治理证据格式要求设计；CLI实现/commit不再纳入本会话。原接受基线保留为历史任务边界，接手会话维护新的CLI基线。

> 来源：Owner 本轮 `PLEASE IMPLEMENT THIS PLAN` 及所附完整 Agent-first 计划。ADR-042 记录已批准治理决定；本 Plan 保存接受基线、动作授权、真实实施状态和恢复入口。批准实施不表示已接受成果或完成平台启用。

## 原接受基线与当前生效范围

- 目标：Agent 在明确任务授权内自主构建/验证，Owner 作实质决定并依据成果和风险证据接受；直接消费者一致，不以新增 override 掩盖旧固定停点。
- 治理：同步政策、阶段检查点、开发技能/发现描述/图/交接、模板、冻结契约、原生守卫及 CI。保留领域参数、命令、反扫、异常恢复与验收步骤；旧 ADR 和冻结历史证据不改写。
- #582原基线（TRANSFERRED，保留历史任务边界）：保持 ReplayInputs/replay 纯内存公开行为及既定32检查、22-case、严格窗口/状态/阈值；文件CLI补齐本地路径/限额/输出防覆盖/IO错误/真实进程退出并取得独立运行证据。
- Harness：schema/trace违规真实非零失败；`ci`、`docker-build`覆盖支持目标，版本绑定仓外artifact记录产物/输入/依赖摘要、环境/命令退出/逐AC，负例能发现错误。
- 平台：仅本仓专用安装身份、有效独立Owner批准及最后推送审核、严格版本检查/讨论解决/禁止force/bypass；原生加载/宿主canary由工程师独立核验。文件准备不能计平台运行通过。
- 永久边界：biz只读工具链、SQL不变量、秘密保护、禁入MCP、不自动信任或绕过技术拒绝。
- 延期：独立受控强制核验系统、actual采样、部署自动化、实际恢复演练、历史capability证据渐进迁移。候选能改自身gate定义的风险首期由Owner审核补偿，尚无防自降可信执行证明。

## 执行授权与停止条件

授权来源为Owner实施请求及最新转交决定，当前覆盖已审定治理/CI/原生守卫改造、#582治理证据格式要求设计、相关本地验证/文档及治理工作区正常stage/commit；CLI实现/commit已转交，不纳入本会话。普通内容迭代核实际diff/staged/SHA，范围、对象、环境、权限和风险未实质变化时复用。

| 对象/动作 | 条件与状态 |
|---|---|
| 治理工作区 | `D:/workspace/10-software-project/projects/mj-agent/maintain/agent-first-delivery`，分支 `maintain/agent-first-delivery` |
| #582 工作区 | TRANSFERRED至“整理 #564 EVAL 承接方案”；`D:/workspace/10-software-project/projects/mj-agent/feature/582-offline-eval-cli` / `feature/582-offline-eval-cli`完整保留，本会话不再修改/提交 |
| 比较基线 | 两工作区创建/核查时 HEAD `5b8833c523f4401de7b70deb5a82b908f3a9c763`；每次执行重新核现实 |
| push / PR / merge | 具名专用App身份、平台规则与有效批准前置满足后正常执行；当前NOT_READY，不使用个人admin身份替代 |
| 平台/信任/秘密 | App创建/安装及秘密维护、规则应用权限、独立原生信任加载/canary由工程师路线核具体授权；当前NOT_READY/NOT_TESTED，无自动激活 |
| runtime/live | 本次不授权实际runtime/LLM/biz采样、容器生命周期或部署；synthetic只证明软件行为 |
| 删除/权限变更 | 不从普通实施授权推定；清理须独立精确对象、必要备份、损失及恢复条件 |

停止受影响项：授权撤销或目标/对象/环境/权限/风险实质变化；接受标准或安全/业务/外发/breaking/gate变化未决定；实际技术拒绝；秘密/数据边界风险；必要前置缺失。部分成功或结果未知先对账副作用，成功步骤不重复。资源按实际平台支持与任务限制安排，无新增付费资源或自动更换模型。

## 任务、依赖与文档

原拆分为两个独立PR单元；Owner最新决定后，本会话仅治理单PR通常指向develop，CLI独立单元TRANSFERRED。以下CLI方法是原计划历史边界与依赖交付记录，不执行。分层路由只是未启用canary准备，登记不产生授权。

1. 治理单元：ADR/政策/SDD/入口/技能/模板一致性 → guard/CI/schema/trace/证据改造 → 离线及负例核验 → 独立审阅。
2. #582 单元（TRANSFERRED，不在本会话实施/commit）：T-006文件适配 → 公共CLI契约/文档/trace → unit/BDD/真实CLI进程与22-case复现 → 独立核验。
3. 启动前置：工程师专用App、仅本仓安装/秘密、平台规则、原生加载及具名临时分支canary；证据齐全后才推进依赖发布步骤。
4. 本次完成基线为治理软件部分与#582治理证据格式设计；CLI真实交付依赖由接手会话继续tracked，不要求Owner重述已有决定。交付：实际版本验收包、限制延期、风险恢复及Owner待决定；有效平台批准与业务接受分别记录，未接受不completed。

文档决策：治理ADR/指南/本Plan新增；活动政策/工作流/技能/描述/模板/索引及原生保护说明更新；#582 CLI contract/指南/trace由该独立单元维护；历史ADR、归档记录、原验收证据不改写。并行写按文件归属与独立工作区；共享平台写由协调者排序。

<!-- agent-first-routes
{"schema_version":1,"routes":[{"task_id":"agent-first-canary","repo":"MJ-AgentLab/mj-agent","active":false,"integration":"feature/task-agent-first-canary-integration","mainline":"develop","children":["feature/agent-first-canary-child-a","maintain/agent-first-canary-child-b"]}]}
-->

路由供有限守卫观察事实，不认证授权。平台/身份/宿主前置仍NOT_READY，因此不启用或创建此集成分支。

平台 canary 准备清单（均未创建/未执行）：单 PR `feature/agent-first-canary-single → develop`；独立 PR `feature/agent-first-canary-independent-a/b → develop`；分层使用上述精确两子分支及任务集成分支，最终 `integration → develop`。在具权工程师核实规则/身份/宿主加载与副作用后，登记真实 SHA/PR，再验证补推使旧审核失效、Owner 有效批准、CI/构建红灯和讨论未解决阻断、无 bypass merge。G2 CI 根据真实事件 head/base 核登记关系；名字不产生授权。删除这些本地/远端分支及临时记录须另列当时真实清单、备份与授权。

## 验证与当前检查点

| 项目 | 当前结果/证据边界 |
|---|---|
| 根协调者离线验证 | 最终完整离线测试exit0：1416通过、6跳过、82未选、30subtests通过；BDD19通过/7策略跳过；contract63通过/1Windows软链接权限不足跳过。ruff/mypy（53源文件）、G1/G2各7、frontmatter154、wikilink/section refs及原生检查通过。先前3个永久边界原文断言失败已保持断言恢复表述；随后1个EOL夹具失败修为单变量并65证据域复验通过。实际日志在仓外验收包，不声称CI/平台运行 |
| #582 CLI | TRANSFERRED；协调者确认HEAD `5b8833c523f4401de7b70deb5a82b908f3a9c763`、全部未提交材料完整保留、无在途/无push；此前130项/Windows别名及独立复验状态作为原检查点转交，接手会话维护新基线 |
| 文档/技能 | 治理Agent已恢复全部37技能原领域方法并定向同步；分别fresh exit0：skills/resources STATIC_PASS、154 canonical frontmatter PASS、wikilink零违规、looprefs零（20sections）、diff检查零；平台/宿主/完整Harness未由这些静态检查证明 |
| infra冻结 | 修改前8×description/body共16旧hash及section heads实算匹配；8infra正文方法保留。治理初次冻结2026-10-12T04:29:22Z；独立审阅发现compose删除授权复用旧句后定向修复，该项hash/heads再冻结2026-10-12T04:49:22Z，fresh检查STATIC_PASS |
| 平台/身份/宿主canary | NOT_READY / NOT_TESTED / NOT_RUN，只有准备文件和只读核验入口，不计实际强制证明 |
| Owner接受 | 未决定；成果仍在实施/核验，不completed |

最终独立核验：Standards定向闭合所有发现；Spec实际188项通过，真实JUnit核套件10个AC/74条ID无缺失/失败/跳过，原未跟踪输入完整链现拒绝，合法本地Git链来源LOCAL_OFFLINE_RUNTIME且无法重标cloud。随后明确增加已通过的真实PR路由进程用例绑定，共75条引用，最终以collector为准。所有AC为软件SELFTEST，不替实际平台/运行验收。治理候选具名暂存135件（含本轮CHANGELOG），未包含原develop材料或已转交CLI。

本地复现入口：`scripts/sdd/delivery_evidence.py` 的 run/check，套件 `evidence/delivery/agent-first.suite.json`。先核干净的已提交候选版本；Windows交付输入依据`.gitattributes`保持LF；输出必须仓外且尚不存在。真实本地运行显式使用`--execution-kind local`及`local://offline/<safe-id>`；CI使用github-actions类型。分别提供实际head/base SHA、repo与output-dir，两种来源不互相冒充。完整命令、SHA/输入/依赖/blob摘要、逐AC及限制保存在生成的仓外delivery.json和命令原始日志，版本变化后重评，不把文档中的旧数字当新证据。

### 交接检查点（软件候选已验证，平台待启动）

- 软件实现提交 `cf1bbd97031a820b9d7c44e7a4904bc04b234a7d`，真实本地collector run/check与独立check均exit0：10AC/75条测试引用软件通过，42提交文件摘要闭合，source LOCAL_OFFLINE_RUNTIME，Owner接受/运行基线资格/来源认证均false。
- 完整离线日志在 `C:/Users/Admin/AppData/Local/Temp/mj-agent-agent-first-20261012-0510-01a12e01/`；初次collector严格拒绝3个EOL属性切换后的旧index状态。逐文件证明原始bytes等于HEADblob，正常刷新index，确认无内容差异且输出未创建后重试成功，没有降低检查。
- 本次检查点是文档记录更新，未改变软件或接受标准。最终分支HEAD与测试版本读取仓外长期验收包：`D:/workspace/10-software-project/projects/mj-agent-delivery-evidence/agent-first-delivery/2026-10-12/delivery/delivery.json`；说明文件为同层`acceptance.md`。引用稳定位置而不在自身正文写入未来SHA，避免提交哈希循环。若文件尚不存在或与HEAD不符，保持未知并核在途动作，不能据正文宣称通过。
- 当前无push/PR/merge/平台配置/信任激活/live副作用；#582已转交且本会话不再写入/测试。重入先核实际branch/HEAD、clean、artifact版本和未决授权。实际执行身份仍缺专用App，当前个人admin不得替代；工程师独立信任/秘密/宿主条件和平台canary仍待完成。
- 接受状态：待Owner明确实际版本及范围。整体Plan仍active；若只接受软件并延期平台，须Owner作明确范围决定并分别跟踪，延期不计通过。

独立审阅分 Standards 与 Spec 两轴，均直接读取实际候选并按基线建立期望。此前发现的路径别名、合并对象错配、授权风险复用、仓内JUnit路径、无关SHA、未跟踪输入及Owner审核缺口都以负例驱动修复；最终运行结果绑定真实Git版本。Windows通过仓库 `.gitattributes` 固定交付输入LF，保留严格working/blob字节比对，不修改个人配置或降低接受标准。

本轮运行记录：实施后Owner新增一次职责转交决定，未逐项审批普通实现。协调者按明确文件归属并行执行，真实并发上限为根加3子Agent；独立核验实际选择high effort，作者继承会话配置，未更换模型或新增付费资源。开始时点、完整成本和总token未被独立记录，标UNKNOWN；测试耗时只使用实际运行输出，不推算总体交付周期。缺陷/返工保留上述审阅与红→绿记录；恢复演练尚未运行。

验证矩阵按实际变化运行相关离线unit/BDD/CLI、ruff/mypy、frontmatter/wikilink、native配置/技能及gate负例。external pytest通过hardened runner结构化SKIP，不计PASS。独立核验者从AC建期望，读取真实成果并复现；另一Agent的通过总结不能替代运行证据。

阶段完成、集成前或交接时更新：目标/AC/授权、工作区/ref/SHA、已集成/验证/交付/接受状态、证据位置、在途副作用/失败/未知/延期、下一步与停止条件。当前本会话在途仅治理实现/验证。#582已TRANSFERRED，无在途/无push且未提交材料完整保留；没有平台注册、规则应用、合并或live副作用。

## 交付、恢复与待决定

提供成果使用入口、逐AC预期/实际、实际版本环境时点与复现artifact、未测/延期、风险/恢复以及待工程师与Owner事项。记录Owner介入、周期、缺陷返工、门禁负例、证据完整性和资源消耗，不能以命令/HTTP成功独自证明业务正确。

恢复：代码/规则通过成组回退PR和独立具权路线，具名资源操作先核实际备份；未进行真实恢复演练。治理交付结束由工程师移除App临时Workflows write、吊销token、关闭临时通道，逐项留证。

下一步：治理完整离线验证与独立审阅、治理软件验收包及#582证据格式要求设计；CLI修复与独立复验由接手会话继续。治理发布依赖：工程师App/平台/宿主启动前置 → 授权内发布及有效结果式审核 → 集成核实 → Owner明确接受实际版本。核心若单独满足自身AC可分段交付；延期影响整体接受基线须Owner决定，不能计作通过。

## 关联文档

- [ADR-042](../decisions/ADR-042_Agent_First_Delivery_Governance.md)
- [交付指南](../docs/guide/[GUIDE]_Agent_First_Delivery.md)
- [接受与授权](../policies/ai-agent.md) §4
- [生命周期](../sdd/lifecycle.md) §2
