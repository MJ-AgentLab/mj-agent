# Working 与 INTENT 的创作、定位和引用

适用：创建或维护任务 working、保存需求原意、解释接受记录、补号改名与引用迁移时读取本说明。权威定义在 [documentation](../../policies/documentation.md)、[lifecycle](../../sdd/lifecycle.md)、[archive](../../policies/archive.md)；本说明给技能操作顺序，不另建状态或接受系统。

## 先定位权威来源

| 要回答的问题 | 首要依据 |
|---|---|
| 为什么做、期望结果、成功判断与范围约束 | 提出者原始来源、正式 INTENT 或简单任务的 Issue 原意区 |
| 应有的接口、行为和业务口径 | 已明确的 SPEC、契约及对应决定 |
| 当前实现实际如何工作 | 真实代码、配置与本次运行证据 |
| 本次由谁、按何顺序交付哪部分 | Plan、任务授权及其检查点 |
| 测到了什么、有何限制 | Report/Assessment 的真实证据 |
| 多个 Plan/PR 的覆盖、进度和依赖 | 真实主 Issue；Intent/INDEX 只作稳定导航 |

来源冲突逐项列出预期、现状、证据和影响；普通实现自主修复，涉及目标/业务/授权/接受基线的实质决定交 Owner。AI 整理说明不能改写原意，owner 维护责任不自动等于提出者或接受人。

## 任务目录与受控改名

1. 新 working 保存到 `plans/<topic>/`；主 Plan 为 `[PLAN]_<topic>.md`，目录 topic 与主文件完全一致，每目录至多一个主 Plan。Intake 可先保存，独立报告任务可以始终没有 Plan；本应有实施计划的任务仍须该工件。子 Plan 各自独立目录，共享报告只保留一个主归属，其他任务引用它。Report/Assessment 按用途命名，不机械补号，不强制局部 INDEX。
2. topic 只选四式：`I<issue>-P<pr>-<slug>`、`I<issue>-<slug>`、`P<pr>-<slug>`、`<slug>`。I/P 大写；slug 由小写英文、数字、短横线构成。Issue/PR 各至多一个真实主要关联，先读本仓本任务明确记录；不从分支任意数字推测、不用 I0/假编号、不为名称创建对象。其余关联写正文。
3. 多 PR 选代表整体交付的集成 PR；未明确主要 PR 就省略 P，不选第一条/最新条。主题保持稳定；主要关联首次明确、纠错或明确更换时同步目录和主文件，不追随后续子/补丁/收尾 PR 改名。
4. 改名前列旧/新绝对路径、原因、Git 跟踪及未提交状态、目标冲突、活动引用与交付路由。核目标和后代重解析点、内容完整性及授权边界，再在同一 shell 用原生操作移动。改后验证文件完整、按文档位置解析的链接和实际路由；记录路径映射。部分成功先对账，不重复成功动作。
5. `task_id` 独立于目录名；补号不改变它、历史基线或 INTENT ID。活动引用经 doc-sync 修复；固定提交/完整快照/旧决定保持可恢复，不把旧路径副本留下作为第二主 Plan。历史根布局只兼容读取，批量迁移须具名清单。新 HEAD 的平台审核仍按实际版本核验。

定位时先读任务明确的文件路径，再用 `rg --files plans` 枚举新旧布局并核正文关联，不能只 glob 根目录或按编号猜任务。交付路由交给 `scripts/sdd/task_delivery.py` 的受限 loader，保留重复、大小、路径安全和异常输入拒绝。

## Working 状态与交付

- type 为 plan/intake/report/assessment；必填 `type/summary/owner/created/updated/state/track`，domain/version 不强制。track 按实际主题。新 Plan 默认 draft，记录明确采纳来源后转 active；已有任务授权不因阶段或文件版本重复审批。
- 仅主 Plan 的 completed 要求 AC 满足、成果可用及 Owner 明确接受准确版本。其他 working 按其自身已确定交付条件由 Agent 标 completed；若自身条件包括 Owner 接受，也须满足。报告 completed 只说明文档交付，独立任务整体接受仍由 Owner 在已有 Issue/会话/任务记录表达；主 Plan 的一次接受可同时覆盖整体接受，范围写清即可。
- 一份报告完成不代表整个 Plan 完成。废弃 draft 保持 draft，正文记录原因与恢复条件。completed 原地保留；archived 仅历史兼容。working 物理归档、180 天 GC 与候选检测已取消，canonical 归档另走政策。

## 保存原意与 INTENT

1. 简单单任务可在真实 Issue 原意区保留唯一正本，不强制新 ID 或文件。需跨任务维护时复用 doc-author 保存正式 INTENT，再用 flow-intake 适配任务、flow-plan 编排实施；不新增 flow-intent。
2. 正式正本位于 `docs/intent/[INTENT]_INT-YYYY-NNN_<English_Topic>.md`，独立于 Plan。一个 INTENT 可支撑多个 Plan；一个 Plan 可承担多个 INTENT 的明确范围，分别注明实际交付/依赖/背景。来源或维护责任不明只保存真实类型的 working 草稿，不冒充正式 INTENT。
3. 九字段为 `type/domain/summary/owner/created/updated/state/intent-id/track`；type=intent，version 可选。五正文为问题现状、期望结果、成功判断、范围约束、未决项。前置可读区核提出者/代表、原始来源、维护责任、原意核对、内容接受、当前位置与完整适用基线、真实主 Issue、AI 整理说明；未知写明未知和恢复条件。
4. 分配前和合并前读取全量 ID 集合（含 draft/active/deprecated、保留的历史决定及已撤销 ID），并核当前共享变更。ID 为首次年度加 001–999；标题、跨年、修订、重新接受或拆任务均保留 ID，删除/撤销不释放。集合读取失败标 UNKNOWN，停止分配；共享冲突/999 耗尽由 Owner 决定，不能自动改号或扩位。
5. INTENT 只用 draft/active/deprecated；退役保留原路径、ID、旧决定、原因和后继，Plan/Issue 完成不传播状态。原意核对、内容接受、执行授权、交付接受分别记录，active 或机器 PASS 不替代真实决定。
6. 接受基线绑定固定提交中的文件准确位置，或包含完整内容且可恢复的快照准确位置；摘要、日期、版本号或 hash 单独不足。实质变化保留旧决定、来源/原因/影响，旧接受只覆盖旧内容；纯路径调整不自动重置业务接受。

真实业务原意澄清给中性选项；工程、机制、授权取舍给推荐及理由。预选、沉默、超时与 AI 建议都不是 Owner 决定。真实未决项保持待答状态，不能把未收到回答改成默认决定；环境事实先自行核查，既定方案不重问。

## 核验与返回

运行 `python scripts/check_frontmatter.py`、`python scripts/check_wikilinks.py`、`python scripts/check_working_docs.py`。逐项报告结构、来源忠实、基线、状态和接受是否已核；机器 PASS 只证明覆盖到的结构/链接，不证明真实业务原意、授权或 Owner 接受。保留未测、UNKNOWN、延期原因/影响/恢复条件。
