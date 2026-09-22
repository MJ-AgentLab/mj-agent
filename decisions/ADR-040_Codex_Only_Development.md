---
type: adr
state: active
decision: accepted
domain: WORKFLOW
owner: ranzuozhou
created: 2026-09-18
updated: 2026-09-18
track: engineering-workflow
summary: "将开发资产维护权定向交给 Codex 原生入口，保留安全与人工决策边界"
---

# ADR-040: Codex 独立开发

此正文属于待批准的成组审阅包；文件元数据是批准并人工应用后的目标状态，不表示已经获批。
ADR-040 已核对本工作树现有 active/archive 命名空间；人工应用前还须核对冻结身份及编号无冲突。
未修改既有 ADR 历史。Owner 批准本组时包括该 ADR 状态转换。

### Context

mj-agent 的业务 agent 与开发工具分别治理。当前开发技能以 `.claude/skills/` 为源，通过 manifest、registry、translation、renderer、lock 生成部分 Codex 入口；37 项开发能力只有18项已有投影。Codex已具备完整参与授权，Owner提出今后以Codex独立开发，Claude退出项目开发入口。

继续双工具兼容会使原生技能、MCP和守卫依赖待退出客户端，并把精力用于跨载体一致性。本次需要改变开发资产的维护权及相应消费者，而不改变业务权限、Owner决策权或运行时语义。依据为本迁移计划、P0资产表、ADR-035/036/039及数据/秘密边界。

### Decision

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


## P3 成组生效前置

正式采用需 Owner 明确批准本 ADR、原生所有权、8项冻结契约、元规则和具名测试/CI切换集合。U04 采用 Owner 批准并人工应用、Codex 验证路线；自动受保护写入仍 BLOCKED_EXECUTION_ROUTE。V4/V8–V11 blocking 保持（V4 严格化另列批准）；V13 warning 保持，V12 生成拓扑 join 在必要保护接续后具名退役，具体以门禁映射为准。P1/P2 STATIC_PASS 不等于真实宿主、模型或服务通过。
