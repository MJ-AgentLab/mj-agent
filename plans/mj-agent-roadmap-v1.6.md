---
summary: mj-agent v1.6 整体 roadmap — Phase 0/1/2 交付路径、ADR 编号空间、安全主线（数据-LLM 边界三原则）
owner: ranzuozhou
created: 2026-04-24
updated: 2026-04-27
state: active
---

# mj-agent (data-agent) 构建路径图

> 版本：v1.6
> 日期：2026-04-24
> 作者：Zack + Claude
> 配套文档：`docs/evals-design.md`、`evaluation/judges/*.md`、`evaluation/datasets/seed/`

**v1.6 更新说明**：

基于对"客户业务数据"性质的澄清（**无 PII，B2B 场景，公司内部使用，不对外输出**），对数据安全架构做系统性补充：

- **新增数据-LLM 边界主线**：新增 ADR-000（三原则）作为后续所有安全相关 ADR 的理论基础
- **新增 ADR-012 Aggregate-first Analysis Loop**：按 token 预算自动聚合
- **新增 ADR-013 Generative UI with Data Handle Pattern**：明细不进 LLM 链路
- **新增 ADR-014 Customer Data Anonymization**：客户名代号化的可配置机制
- **修订 ADR-007**：简化为"角色上下文作用域"，删除残留的多租户/数据隔离暗示
- **Phase 1 新增分析工具集目录**（`tools/analysis/`），补齐分析能力基础设施
- **Phase 1 新增实体解析模块**（`entity/`），从隐含 skill 升级为独立组件
- **Phase 2 新增 LLM Gateway 统一出口层**，集中审计、代号化、token 预算控制
- **附录 C 新增合规前置问题**：ZDR 协议、云 API 合规、监管要求
- **"不做"清单新增 2 条**：明确客户间数据不隔离 + 分析结果不对外输出
- **监控指标新增 2 项**：出域数据量、代号化开关分布

**核心认识转变**：数据安全的核心关切从"防 PII 泄漏 + 多重脱敏"简化为"**控制 LLM API 出域信息量**"。去除了过度设计（特征泛化、客户间隔离、Code Sandbox 作为安全必需品），同时补齐了之前隐含未显式的工程组件（Gateway、Analysis Tools、Entity Resolution）。

**v1.5 更新说明（保留）**：
- 修正 Phase 4 定位：从 "Multi-tenant Expansion"（多租户 SaaS）改为 "Multi-team Expansion"（组织内多团队扩展）
- mj-agent 的服务对象是**公司内部**数据分析、产品、市场、运营、风控等团队，不是外部租户
- Phase 4 完全重写：RBAC + 团队特化 skills + UX 分层 + 审计合规 + 按部门 cost attribution
- ADR-007 Context isolation 改为"角色/团队隔离"，不再涉及多租户
- 清理其他章节中 tenant / 多租户 / SaaS / 机构客户相关表述（共 12 处）
- "不做"清单新增：不做 SaaS 化、不对外部开放

**v1.4 更新说明（保留）**：
- 修正 MJ-AgentLab 生态层级：mj-agent 与 mj-system、mj-agentlab-marketplace 同为一级仓库
- 第 12 节生态对接章节重构
- ADR-010 描述修正为"独立仓库但生态复用"
- CONTRACT 文档位置改为 mj-agent 仓库的 `docs/contracts/`

**v1.3 更新说明（保留）**：
- Phase 2 技术栈新增：DeepEval、sqlglot、sqlparse、pandas
- Phase 2 关键工作大幅扩展 evals 子节
- Phase 2 退出标准细化
- 新增第 13 节：团队责任矩阵

**v1.2 / v1.1 更新说明（保留）**：
- biz schema 三层同步机制按 Phase 展开
- 部署方式与 mj-system 共用 DEV/TEST/PROD Docker 环境
- ADR-008 / ADR-009 / ADR-010 / ADR-011

---

## 0. 文档定位

本文档是 mj-agent（数据智能体）的**分阶段构建路径图**，不是一次性蓝图。每个阶段都是可独立交付的里程碑，阶段间有清晰的**触发信号**决定是否前进，也允许**停在某阶段长期运行**而不升级。

**核心哲学**：先把 agent 的"内功"（skills、memory、evals、数据边界）做扎实，再扩展"外在"（精致 UI、多团队接入、Generative UI）。

**服务对象定位**：mj-agent 是**公司内部工具**，服务于数据分析、产品、市场、运营、风控等**内部团队和角色**。**不是 SaaS、不做多租户、不对外部机构客户开放**。这一定位贯穿所有阶段，决定了架构选型、权限模型、UX 方向。

**数据性质定位 ★ v1.6 新增**：mj-agent 分析的数据是 mj-system 中来自**下游金融机构客户**的**客户业务数据**（客户使用产品产生的调用、查询、交易等行为数据）。该数据**不含 PII**（无自然人身份信息），属性是**客户的商业运营信息**，受服务合同保密条款约束。数据所有权归客户，我方为受托处理方。

**架构定位**：

MJ-AgentLab 生态由**三个一级仓库**和**一个插件生态**组成：

```
MJ-AgentLab Organization
├── mj-system                  一级：业务数据平台（DDD 六层架构，含 biz 域）
├── mj-agent                   一级：数据智能体（本项目）
└── mj-agentlab-marketplace    一级：插件生态 / 可复用资产分发平台
    ├── mj-doc                 插件：文档规范与治理
    ├── mj-git                 插件：Git 工作流与 CI/CD reusable workflows
    ├── mj-n8n                 插件：n8n 工作流模板与调度
    └── mj-ops                 插件:运维监控工具
```

mj-agent 对各方的关系类型不同：
- **对 mj-system**：数据 + 部署紧耦合（核心依赖）
- **对 mj-agentlab-marketplace**：规范与工具的消费者（也向 marketplace 贡献 skills）
- **对 mj-doc/mj-git/mj-n8n/mj-ops 插件**：以插件用户身份遵循其规范

---

## 1. 总览

| 阶段 | 时长 | 核心目标 | 交付形态 | 用户范围 |
|---|---|---|---|---|
| **Phase 0: Foundation** | 1–2 周 | 骨架 + 接通 biz 域 + 可跑通最小 agent | 本地 + LangGraph Studio | 开发者自用 |
| **Phase 1: Python-only MVP** | 3–4 周 | Chainlit UI + biz 域 skills + 基础记忆 + 分析工具集 + 实体解析 + 契约测试 ★ v1.6 | DEV 环境 Web 应用 | 内部分析师 ≤ 5 人 |
| **Phase 2: Production Hardening** | 4–6 周 | 长期记忆 + HITL + LLM Gateway + 完整 evals + 三环境 + schema 自动同步 ★ v1.6 | PROD 级服务 | 全部内部分析师 |
| **Phase 3: Generative UI Layer** | 2–3 月 | Next.js + CopilotKit + dataRef 架构 + 精致可交互 UI + 记忆清理 ★ v1.6 | 完整前端应用 | 内部分析师 + 少量非分析师试点 |
| **Phase 4: Multi-team Expansion** | 3–4 月 | RBAC + 团队特化 skills + 角色 UX 分层 + 审计合规 | 公司内部全员数据对话平台 | 产品 / 市场 / 运营 / 风控等非分析师角色 |

**总计**：Phase 0–2 约 2 个月可上线生产服务；Phase 3 视需求可选；Phase 4 按组织推广节奏决定。

---

## 2. 贯穿所有阶段的核心原则

### 2.1 顶层原则（总纲）

**ADR-000 Data-LLM Boundary Principles（数据与 LLM 的边界原则）★ v1.6 新增**

mj-agent 处理 mj-system 的客户业务数据，通过 LLM API 完成分析任务。客户业务数据不含 PII，但属于客户的商业信息，有服务合同的保密义务。

**核心关切**：客户业务数据在 LLM API 调用过程中**离开公司网络**，需要控制离开网络的数据内容和信息量。

**三条边界原则**：

- **P1 最小必要出域（Minimum Necessary Egress）**：离开公司网络到达 LLM API 的数据量，压缩到完成分析所需的最低限度。明细让位于聚合，精确让位于概要，但不以牺牲分析质量为代价。

- **P2 链路隔离（Channel Isolation）**：业务数据流转路径（本地 SQL、本地渲染）和 LLM 调用路径在架构上分开。LLM 看到的是数据的"引用"和"摘要"，不是"全量载荷"。

- **P3 工具化间接操作（Tool-mediated Operation）**：LLM 不直接操作底层数据，通过生成意图调用本地工具执行。工具在可信域内访问数据，只把必要结果返回给 LLM。

**原则的落地路径**：
- ADR-012 Aggregate-first：P1 的实现机制
- ADR-013 dataRef：P2 的实现机制  
- ADR-014 Customer Anonymization：P1 + P2 的补充机制
- Tools / Skills 体系：P3 的实现机制

**不适用范围**：ADR-000 关注的是 LLM API 调用边界，不涉及客户间数据隔离（内部分析师允许跨客户分析），不涉及多租户（mj-agent 服务单一信任域）。

---

### 2.2 工程原则

**ADR-001 Python-only agent runtime**
所有 agent 逻辑、tools、memory、skills 留在 Python。前端仅作为通信客户端和渲染层。

**ADR-002 Skills as first-class citizens**
所有专业能力打包成 `skills/{name}/SKILL.md` 格式，对齐 Claude Code skills 约定。

**ADR-003 Progressive disclosure**
全局 system prompt 只放身份和原则，具体能力按需加载。

**ADR-004 Memory separation**
明确区分 Checkpointer（线程内）、Store（跨线程长期）、Semantic Cache（查询复用）三层。

**ADR-005 Evals as gating**
每次模型切换、prompt 修改、skill 发布，必须过 LangSmith evals 基线。详见 `docs/evals-design.md`。

**ADR-006 Fail-safe reads**
业务数据库连接用只读账号 + SQL guardrail middleware 双层保护。

**ADR-007 Role-based Context Scoping（角色上下文作用域）★ v1.6 修订**

mj-agent 只服务公司内部，**单一信任域**，不实现多租户或多客户数据隔离。

memory namespace 设计为 `(team, role, user, memory_type)`：
- Phase 1–3：team 默认 `data_analytics`，role 默认 `analyst`
- Phase 4 扩展到真实多团队多角色（产品 / 市场 / 运营 / 风控等）

memory 检索、skill 加载均按用户角色权限过滤，防止低权限用户意外触发高权限能力。**这不涉及数据隔离**（客户业务数据在内部允许跨团队使用），而是能力/视图层面的分层。

**ADR-008 Co-deployment with mj-system**
mj-agent 作为 mj-system 的兄弟服务部署在同一 Docker 环境中（DEV/TEST/PROD 三套）。

**ADR-009 biz 域为主数据源**
mj-agent 仅通过只读账号访问 biz 域，不访问 ODS/DWD 原始层。

**ADR-010 独立仓库但生态复用**
mj-agent 作为 MJ-AgentLab 的一级仓库存在，与 mj-system、mj-agentlab-marketplace 平级。代码所有权、版本号、发布节奏独立。通过以下机制融入生态：

- **文档规范**：遵循 marketplace 中 **mj-doc 插件**的九类文档体系
- **CI/CD**：通过 marketplace 中 **mj-git 插件**提供的 reusable workflows 构建三环境流水线
- **工作流调度**：通过 marketplace 中 **mj-n8n 插件**接入定时任务和异常告警
- **运维监控**：通过 marketplace 中 **mj-ops 插件**的面板和 RUNBOOK 体系
- **部署**：三环境策略沿用 mj-system 模板；Docker 镜像推至同一 registry
- **基础设施共享**：共享 self-hosted runners、PG 实例、NAS 备份
- **契约管理**：biz 域访问契约文档化存于 mj-agent 仓库 `docs/contracts/mj-agent-to-mj-system.md`
- **向 marketplace 贡献**：mj-agent 的通用 skills（特别是 `mj-ddd-semantics`）可发布到 marketplace

**ADR-011 biz schema 三层同步机制**
- L1 结构层（自动化）：cross-repo dispatch + 自动 PR
- L2 语义层（半自动）：PR review gate + 人工补充
- L3 经验层（异步）：episodic memory 运行时积累
- 兜底：CI 必跑契约测试

---

### 2.3 数据边界相关原则（ADR-000 的具体化）★ v1.6 新增

**ADR-012 Aggregate-first Analysis Loop**

LLM 看到的数据量受 **token 预算** 约束（P1 的实现）：

- 单次 LLM 调用传入的数据 ≤ 配置上限（默认 5000 tokens，可覆盖）
- 低于上限：可传明细或采样（适用于异常诊断、数据质量检查等场景）
- 超过上限：由 Agent 自动聚合后传入

**聚合策略由 Agent 自主推理决定**（group by、top-N、时段汇总等），不走硬编码配置表。聚合能力通过 `tools/analysis/` 工具集暴露给 LLM，LLM 通过工具调用触发本地聚合。

**分析循环**：
```
规划 SQL → 本地执行 → token 预算评估 → 必要时调用聚合工具 → LLM 解读
```

**例外场景**：
- 异常诊断：允许传入采样明细（≤ 50 行），因为需要看具体模式
- 数据质量检查：允许传入异常样本
- 客户自查（Phase 4+）：按配置可放宽到该客户自己的明细

**ADR-013 Generative UI with Data Handle Pattern**

Generative UI（Phase 3 引入）的数据流与 LLM 调用流**物理隔离**（P2 的实现）：

- LLM 输出组件 JSON，只包含 `data_ref`（UUID 引用），不含真实数据
- 前端通过独立的 `/api/artifacts/{ref}` 接口直取真实数据
- 真实数据**不进入** LLM 的 context 和 response

**组件 Schema 采用 Pydantic 白名单约束**（初期 6–8 个组件类型：bar_chart / line_chart / kpi_card / table / funnel / comparison_card / trend_card），配合 `with_structured_output` 防止 LLM 自由发挥生成非法组件。

**artifact 生命周期**：
- metadata 包含 `customer_id`（审计用）、`created_at`、`ttl`
- 默认 TTL：会话结束即销毁
- 存储：Redis 或 PG artifact 表
- 不跨会话共享

**ADR-014 Customer Data Anonymization**

客户业务数据中的**客户身份**（机构名、产品名等）支持代号化（P1 + P2 的补充）：

- 通过运行时配置决定是否启用：
  - `anonymize_customer_names`: 默认 `true`（客户名代号化）
  - `anonymize_product_names`: 默认 `false`（产品名通常可直传）

- 代号表（`config/customer_codebook.yaml`）作为主数据维护：
  - 加密存储，RBAC 控制访问
  - 在实体解析（entity resolution）和脱敏（anonymization）之间共享
  - 代号使用无序列码（如 `CUST_7f3a`），避免通过编号推断规模排序

- **前端按用户角色决定反向替换强度**：
  - 分析师 / 风控：完全还原真名
  - 其他角色：按配置保留代号或部分还原

**本 ADR 的目的**：控制"离开公司网络到达 LLM 厂商的信息内容"，使 LLM API 日志中看不到具体客户名。**不是**客户间隔离（mj-agent 允许内部跨客户分析）。

---

## 3. Phase 0: Foundation

### 目标

搭起可验证的最小骨架，证明技术栈能跑通，连上 mj-system DEV 环境的 biz 域，初始化 biz schema snapshot。

### 技术栈

- **Python 3.12** + **uv** 包管理
- **LangChain 1.2+**、**LangGraph 1.x**
- **langchain-anthropic**
- **psycopg[binary]**
- **LangGraph Studio**
- **pytest** + **ruff** + **mypy**
- **pre-commit** + **conventional commits**
- **mj-doc 插件**（通过 marketplace 安装）
- **mj-git 插件**（通过 marketplace 安装)

### 项目结构

```
mj-agent/
├── AGENTS.md
├── README.md
├── pyproject.toml
├── uv.lock
├── .env.example
├── langgraph.json
│
├── src/mj_agent/
│   ├── agent.py
│   ├── config.py
│   ├── state.py
│   ├── skills/
│   │   ├── query-writing/SKILL.md
│   │   └── mj-ddd-semantics/
│   │       ├── SKILL.md
│   │       └── references/biz_schema_snapshot.json
│   ├── tools/sql/{execute,introspect}.py
│   ├── integrations/mj_system_db.py
│   └── prompts/system.md
│
├── scripts/fetch_biz_schema.py
└── tests/smoke_test.py
```

### 关键工作

1. `uv init` 建项目
2. 与 mj-system 团队对接 biz 域契约
3. 写 `integrations/mj_system_db.py`
4. 写 `scripts/fetch_biz_schema.py`
5. 初始化 biz schema snapshot
6. 写最小 `create_agent` + `execute_sql` + 1 个 skill
7. LangGraph Studio 跑通对话
8. 写 3–5 个 smoke test
9. 启用 mj-doc、mj-git 插件初始化规范
10. ★ v1.6：完成合规前置确认（见附录 C）

### 退出标准

- [ ] LangGraph Studio 里能跑通端到端 biz 域查询
- [ ] 至少 3 个真实 biz 域表的查询案例跑通
- [ ] `biz_schema_snapshot.json` 初始化完成
- [ ] `pytest tests/smoke_test.py` 全绿
- [ ] `uv sync` 可复现
- [ ] biz 域只读账号权限清单文档化
- [ ] 与 mj-system 团队就字段 comment、schema 版本化达成口头共识
- [ ] ★ v1.6：合规团队确认云 LLM API 调用方案（ZDR / 企业协议签署路径明确）

---

## 4. Phase 1: Python-only MVP

### 目标

给 3–5 个核心**分析师**用户一个能用的数据对话应用，部署到 DEV 环境。阶段末期引入契约测试。

**★ v1.6 新增目标**：ADR-000 的 P1（最小必要出域）和 P3（工具化间接操作）在 MVP 阶段就落地到代码中——分析工具集 + 实体解析。

### 触发信号

Phase 0 骨架稳定、biz 域连通、skills 机制跑通、合规前置确认通过。

### 技术栈（新增）

- **Chainlit 1.3+**
- **matplotlib** + `chart_style_prompt v3`
- **openpyxl**
- **langgraph-checkpoint-postgres**
- **langsmith**
- **click** / **typer**
- **rapidfuzz**（★ v1.6：实体解析模糊匹配）
- **tiktoken**（★ v1.6：token 预算估算）

### 项目结构（扩展）

```
mj-agent/
├── ...（Phase 0 保持）
├── src/mj_agent/
│   ├── ui.py                    # Chainlit 入口
│   ├── skills/
│   │   ├── biz-schema-exploration/SKILL.md
│   │   ├── query-writing/SKILL.md
│   │   ├── query-optimization/SKILL.md
│   │   ├── monthly-report/
│   │   └── mj-ddd-semantics/    # 核心 skill
│   │
│   ├── tools/
│   │   ├── sql/                 # 已有：SQL 执行
│   │   ├── analysis/            # ★ v1.6 新增：分析工具集
│   │   │   ├── aggregate.py            # group by + agg
│   │   │   ├── compare_periods.py      # 同比环比
│   │   │   ├── drill_down.py           # Top N 下钻
│   │   │   ├── detect_anomaly.py       # IQR / z-score 异常检测
│   │   │   └── token_estimator.py      # 估算结果的 token 成本
│   │   ├── charts/
│   │   └── excel/
│   │
│   ├── entity/                  # ★ v1.6 新增：实体解析
│   │   ├── aliases.yaml                 # 别名词典（客户/产品主数据）
│   │   ├── resolver.py                  # L1 精确 + L2 模糊
│   │   └── tools/entity_lookup.py       # LLM 可调用的解析工具
│   │
│   ├── memory/
│   │   ├── checkpointer.py
│   │   └── migrations/001_checkpoint_tables.sql
│   └── server/cli.py
│
├── config/
│   └── customer_codebook.yaml   # ★ v1.6：客户代号表初版（手工维护）
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/                # 阶段末引入
│       └── test_biz_schema_alignment.py
│
├── infra/docker/
│   ├── Dockerfile
│   └── entrypoint.sh
│
├── scripts/
│   ├── fetch_biz_schema.py
│   └── diff_biz_schema.py
│
└── docs/{architecture,db_access,skills_guide}.md
```

### 关键工作

- 5 个核心 skill（`mj-ddd-semantics` 最重要）
- Chainlit UI：流式对话 / SQL 预览 / 数据表 / matplotlib 图表 / Excel 下载
- Checkpointer 连 `mj_agent_memory` 数据库
- 契约测试验证 skill 声明字段在 biz 域真实存在
- **★ v1.6 新增**：`tools/analysis/` 分析工具集（aggregate / compare_periods / drill_down / detect_anomaly / token_estimator）
- **★ v1.6 新增**：`entity/` 实体解析最小版（L1 别名 + L2 模糊 + 工具化暴露给 LLM）
- **★ v1.6 新增**：token 预算机制的最小实现（进 prompt 前估算、超限触发 aggregate 提示）
- **★ v1.6 新增**：`customer_codebook.yaml` 初版（覆盖常用客户的代号映射），Phase 1 先手工维护

### 部署

作为 mj-system DEV 环境 docker-compose 中的 mj-agent service。

### 退出标准

- [ ] 5 个核心 skill 可用，`mj-ddd-semantics` 覆盖 biz 域 80% 常用表
- [ ] mj-agent 容器稳定运行在 DEV，Chainlit 内网可访问
- [ ] 3–5 个分析师使用 ≥ 2 周
- [ ] 月报场景端到端跑通
- [ ] LangSmith 累积 ≥ 500 条 trace
- [ ] `mj_agent_memory` 备份策略生效
- [ ] 契约测试在 CI 必跑且通过
- [ ] **★ v1.6**：实体解析工具覆盖 biz 域常用机构/产品（人工抽检 ≥ 80% 命中率）
- [ ] **★ v1.6**：`aggregate` / `compare_periods` / `drill_down` 核心分析工具上线并被 LLM 正确调用
- [ ] **★ v1.6**：token 预算机制生效（可在 LangSmith 看到每次 LLM 调用的数据 token 量）
- [ ] **★ v1.6**：ADR-000 P1 的最小实现可演示（给定一个大结果集，agent 能自动转为聚合调用）

---

## 5. Phase 2: Production Hardening

### 目标

生产级服务，部署到 TEST 和 PROD，面向**全部内部分析师**。

**核心新增**：
- 完整 evals 体系
- biz schema 全自动同步机制
- **★ v1.6**：LLM Gateway 统一出口层（ADR-000 三原则的集中落点）

### 触发信号

- Phase 1 用户累积 ≥ 500 条 trace
- 出现"上次问过一样的"复用需求
- 出现"差点执行危险操作"事件
- mj-system TEST/PROD 环境接入就绪
- mj-system 同意埋 biz schema dispatch 事件

### 技术栈（新增）

- **langmem**、**pgvector**
- **LangChain 1.x middleware**
- **pytest-asyncio** + **LangSmith evals**
- **DeepEval ≥ 3.0**
- **sqlglot ≥ 25.0**、**sqlparse ≥ 0.5**
- **pandas ≥ 2.2**
- **GitHub Actions**（通过 mj-git 插件 reusable workflows）
- **GitHub `repository_dispatch`**
- **mj-ops 插件**、**mj-n8n 插件**（通过 marketplace）
- **★ v1.6：sentence-transformers / BGE 系列**（实体解析语义匹配层）

### 项目结构（大幅扩展）

```
mj-agent/
├── ...（Phase 1 保持）
│
├── src/mj_agent/
│   ├── gateway/                  # ★ v1.6 新增：LLM 统一出口层
│   │   ├── llm_gateway.py                # 所有 LLM 调用的唯一入口
│   │   ├── pre_processors/
│   │   │   ├── anonymizer.py             # 代号化（ADR-014）
│   │   │   ├── token_budget_guard.py     # 数据量检查（ADR-012）
│   │   │   └── audit_tagger.py           # 打审计标签
│   │   └── post_processors/
│   │       ├── denonymizer.py            # 代号反向替换（前端侧用）
│   │       └── output_validator.py       # 基本输出校验
│   │
│   ├── middleware/
│   │   ├── sql_guardrail.py
│   │   ├── hitl_approval.py
│   │   └── audit_log.py
│   │
│   ├── context/{write,select,compress,isolate}.py
│   │
│   ├── memory/
│   │   ├── checkpointer.py
│   │   ├── store.py             # PostgresStore + pgvector
│   │   ├── semantic_cache.py
│   │   ├── namespaces.py        # (team, role, user, memory_type)
│   │   ├── schemas.py
│   │   ├── extractors/{fact,episode,rule}.py
│   │   ├── retrievers/{facts,episodes,rules}.py
│   │   └── migrations/001..005.sql
│   │
│   ├── entity/                   # Phase 1 基础 + L3 语义层
│   │   ├── aliases.yaml
│   │   ├── resolver.py                   # L1 + L2 + L3（★ v1.6 扩展）
│   │   ├── embeddings.py                 # ★ v1.6：pgvector 语义匹配
│   │   ├── context_enhancer.py           # ★ v1.6：对话/用户/团队上下文加权
│   │   └── tools/entity_lookup.py
│   │
│   ├── integrations/
│   │   ├── mj_system_db.py
│   │   ├── mcp_servers.py
│   │   └── mj_ops_reporter.py
│   │
│   └── server/api.py
│
├── evaluation/                   # 完整的评估体系
│   ├── judges/
│   │   ├── outcome_judge.md
│   │   ├── trajectory_judge.md
│   │   └── component_judge.md
│   ├── datasets/
│   │   ├── seed/
│   │   ├── smoke/
│   │   ├── basic/
│   │   ├── regression/
│   │   ├── hard/
│   │   ├── known_failures/
│   │   └── production_samples/
│   ├── metrics/
│   ├── runners/
│   └── thresholds.yaml
│
├── config/
│   ├── customer_codebook.yaml    # 升级：加密存储 + 版本化
│   └── anonymization_policy.yaml # ★ v1.6：代号化开关策略
│
├── compatibility.yaml
│
├── tests/{unit,integration,contract,evals}/
│
├── infra/docker/
│   ├── Dockerfile
│   └── docker-compose.{dev,test,prod}.yml
│
├── scripts/{fetch,diff,sync}_biz_schema.py
│
├── .github/workflows/
│   ├── ci.yml
│   ├── deploy-{dev,test,prod}.yml
│   └── biz-schema-sync.yml
│
└── docs/
    ├── architecture.md
    ├── memory_architecture.md
    ├── evals-design.md
    ├── evals-maintenance.md
    ├── schema_sync_flow.md
    ├── llm_gateway.md             # ★ v1.6
    ├── entity_resolution.md       # ★ v1.6
    ├── contracts/mj-agent-to-mj-system.md
    ├── adr/000..014-*.md
    └── handover.md
```

### 关键工作

- 长期记忆三类（Semantic / Episodic / Procedural）
- Middleware 层（sql_guardrail / hitl_approval / audit_log）
- 完整 Evals 体系（四层模型 + 三个 judge + CI/CD 阻断）
- biz schema 自动同步机制（cross-repo dispatch + 自动 PR）
- 三环境 CI/CD（mj-git 插件 reusable workflows）
- **★ v1.6**：LLM Gateway 上线，所有 LLM 调用必经此层
  - pre_processors: 代号化 / token 预算守护 / 审计标签
  - post_processors: 反向替换 / 输出校验
- **★ v1.6**：实体解析 L3 语义层（pgvector 复用 memory 基础设施，无需独立服务）
- **★ v1.6**：Customer codebook 升级为加密存储 + 版本化主数据
- **★ v1.6**：Gateway 审计日志接入 mj-ops 面板（每次调用的 customer_ids 集合、数据量、代号化状态、成本）

### 部署

完全对齐 mj-system 的 DEV/TEST/PROD。memory PG 用独立 database。备份归档到 NAS。监控通过 mj-ops 插件接入。

### 退出标准

- [ ] 三环境稳定运行
- [ ] 完整 evals 体系通过基线
- [ ] biz schema 自动同步机制跑通至少一次
- [ ] 每次 LLM 调用有 audit trace
- [ ] SQL guardrail 拦截成功率 100%（红队测试）
- [ ] HITL 审批路径覆盖高风险操作
- [ ] **★ v1.6**：LLM Gateway 上线，所有 LLM 调用经过它（代码审计可证明无绕过）
- [ ] **★ v1.6**：ADR-000 三原则的可观测机制生效（Gateway 日志可查询任意时段的数据量分布、代号化比例）
- [ ] **★ v1.6**：Entity Resolution L3 接入 pgvector，语义匹配 recall@3 ≥ 90%
- [ ] **★ v1.6**：按 team/user 的 LLM token cost 月度统计可见

---

## 6. Phase 3: Generative UI Layer

### 目标

**只在明确信号出现时启动**。把 Chainlit UI 升级为 Next.js + CopilotKit。引入 episodic memory 过时条目清理。

**★ v1.6 核心强调**：Generative UI 的数据流严格遵循 ADR-013 的 dataRef 模式——LLM 链路和数据链路物理隔离。

### 触发信号（任一）

- 分析师明确要求"图表能钻取/筛选/联动"
- 业务要给非分析师团队（产品、市场、运营）试点做自助查询
- 团队来了能 own 前端的人
- 要把月报结果嵌入到已有企业门户

**反信号**：用户反馈 80% 是"agent 答错了"而不是"UI 不好看" → 留在 Phase 2 打磨 skills。

### 技术栈（新增）

- **Next.js 14 App Router** + **React 19** + **TypeScript 5**
- **CopilotKit** + **AG-UI Protocol**
- **@langchain/langgraph-sdk**（仅作通信客户端）
- **Tailwind CSS** + **shadcn/ui** + **Vega-Lite**
- **pnpm** + **Turborepo**
- **auth.js (NextAuth)**（简单身份管理，Phase 4 会升级到 SSO）
- **★ v1.6：Redis**（artifact 存储，短 TTL 场景）

### 关键新增

- **6 个核心 generative UI 组件**（遵循 ADR-013）：
  - bar_chart / line_chart / kpi_card / data_table / funnel / comparison_card
  - 所有组件 Schema 用 Pydantic 定义，LLM 通过 `with_structured_output` 约束输出
  - 组件只携带 `data_ref`（UUID），不携带原始数据
- **Artifact Storage**：
  - Redis 存储 artifact 数据，key = data_ref
  - TTL 默认随会话（会话结束即销毁）
  - 独立 API `/api/artifacts/{ref}`，前端直取
  - 每个 artifact 带 `customer_ids` 元数据供审计
- **HITL 审批 UI**：
  - Phase 2 的 hitl_approval middleware 在前端可视化
  - 高风险查询（如跨客户 + 大数据量）必须审批
- **Episodic memory 过时条目清理**：
  - `memory/cleanup/episodic_staleness.py` 定期扫描
  - 超过 90 天未复用或与最新 biz schema 不兼容的条目标记 deprecated
- **前端反向替换**：
  - ADR-014 的客户端实现：LLM 输出的 `CUST_xxx` 在前端渲染时按用户角色决定是否还原

### 退出标准

- [ ] 6 个核心 generative UI 组件上线
- [ ] HITL 审批流程在前端工作
- [ ] 首 token 延迟 < 2s
- [ ] Chainlit 停用
- [ ] episodic memory 清理机制跑通
- [ ] **★ v1.6**：所有 generative UI 组件不携带原始数据（代码审计可证明）
- [ ] **★ v1.6**：Artifact TTL 机制生效（压测：1000 并发会话不 OOM，TTL 到期 artifact 确实被清理）
- [ ] **★ v1.6**：前端按角色反向替换代号验证通过（分析师看真名，其他角色看代号）

---

## 7. Phase 4: Multi-team Expansion（组织内多团队扩展）

### 关键认知

这个阶段的核心是把 mj-agent 从"**数据分析师专用工具**"扩展为"**公司内部全员数据对话平台**"，服务**产品、市场、运营、风控**等非分析师角色。

**这不是 SaaS 化，也不是多租户**——mj-agent 只服务公司内部，不对外部客户开放。真正的挑战是：不同**内部角色**的业务视角、技术水平、数据权限差异巨大。

**★ v1.6 补充**：Phase 4 的 RBAC 维度是 **team × role**，**不引入"客户作用域"维度**（客户业务数据在内部允许跨团队使用）。但审计日志要详细记录每次 LLM 调用涉及的客户，便于事后响应客户询问 "你们用我的数据做了哪些分析？"

### 目标

- 让非分析师团队（产品/市场/运营/风控）能直接使用 mj-agent，减轻数据分析团队的"代查"负担
- 通过 RBAC 确保不同角色只能触发应有的能力
- 通过 UX 分层让技术用户和非技术用户都好用
- 通过审计和合规机制保证规模化使用的治理

### 触发信号（任一）

- 非分析师团队（产品/市场/运营）主动提出接入需求
- 数据团队代查工单日均 > 20 次
- 公司推动数据文化建设（data-driven KPI 落地）
- Phase 3 UI 已验证可让非技术用户上手

### 反信号

- 分析师团队自己使用还不稳定 → 先打磨 Phase 2
- 没有跨团队推动人（需要产品经理或业务 lead 背书）
- 公司没有统一身份系统 → SSO 对接工作量过大，先推动基础设施

### 关键前置判断

**情况 A（最佳）**：biz 域已有字段级权限控制 + 公司有 SSO
- 工作量：**3–4 个月**

**情况 B**：无字段级权限 + 有 SSO
- 需要 mj-agent 层实现能力/视图分层
- 工作量：**5–6 个月**

**情况 C**：无 SSO
- 不建议直接进 Phase 4，先推动公司基础设施建设

### 技术栈新增

- **SSO 对接**：飞书 / 企业微信 / AD / LDAP（取决于公司选型）
- **RBAC 实现**：**Casbin** 或自建 policy 引擎
- **结构化审计日志**：Loki 或 ELK
- **按 team tag 的 tracing**（LangSmith custom metadata）
- **按部门成本报表**：自定义 aggregation

### 项目结构（新增）

```
mj-agent/
├── src/mj_agent/
│   ├── auth/                      # ★ Phase 4 新增
│   │   ├── sso_adapter.py         # 飞书/企微/AD 适配
│   │   ├── rbac.py                # Casbin policy engine
│   │   └── session.py
│   │
│   ├── middleware/
│   │   ├── rbac_guard.py          # ★ 按角色拦截 skill/tool
│   │   └── audit_log.py           # 升级：结构化事件 + 客户维度
│   │
│   ├── skills/
│   │   ├── core/                  # 共用核心 skill
│   │   │   ├── mj-ddd-semantics/
│   │   │   └── ...
│   │   └── teams/                 # ★ 团队特化 skills
│   │       ├── product_manager/
│   │       │   ├── product-metrics/SKILL.md
│   │       │   └── ab-testing-analysis/SKILL.md
│   │       ├── marketing/
│   │       │   ├── marketing-dictionary/SKILL.md
│   │       │   ├── campaign-roi/SKILL.md
│   │       │   └── channel-attribution/SKILL.md
│   │       ├── operations/
│   │       └── risk_control/
│   │
│   └── ui_personas/               # ★ UX 分层
│       ├── analyst_view.py        # 显 SQL / 技术细节
│       ├── business_view.py       # 隐 SQL / 图表优先 / 自然语言解读
│       └── executive_view.py      # 关键数字 + 趋势
│
├── config/
│   ├── roles.yaml                 # ★ 角色定义
│   ├── permissions.yaml           # ★ 权限矩阵（team × role）
│   └── team_budgets.yaml          # ★ 部门预算
│
├── scripts/
│   ├── rbac_audit.py              # ★ 权限审计报告
│   └── cost_attribution.py        # ★ 按部门成本报表
│
└── docs/
    ├── multi-role-design.md       # ★ 多角色设计说明
    ├── rbac-policy.md             # ★ 权限策略文档
    └── team-onboarding.md         # ★ 新团队接入手册
```

### 关键设计

#### 7.1 角色权限模型（RBAC）

核心角色清单（示例，需根据公司实际调整）：

| 角色 | 描述 | 核心场景 |
|---|---|---|
| `data_analyst` | 数据分析团队 | Full access，保留 Phase 1–3 完整体验 |
| `product_manager` | 产品经理 | 产品指标、A/B 测试、功能使用分析 |
| `marketing` | 市场运营 | 渠道 ROI、活动归因、转化漏斗 |
| `operations` | 运营团队 | 日常经营看板、用户生命周期 |
| `risk_control` | 风控团队 | 风险看板、异常检测、明细溯源 |
| `executive` | 高管 | 核心指标卡片 + 趋势 |

`config/roles.yaml` 示例：

```yaml
roles:
  data_analyst:
    description: "数据分析团队，保留完整能力"
    skill_allowlist: ["*"]
    table_access: ["all_biz_tables"]
    show_customer_real_name: true   # ★ v1.6：前端还原代号
    ui_persona: analyst_view
    query_limits:
      max_concurrent: 5
      monthly_token_budget: 2000000

  product_manager:
    description: "产品经理"
    skill_allowlist: ["core/*", "teams/product_manager/*"]
    table_access: ["dws_*", "dim_*", "agg_*"]
    show_customer_real_name: true
    ui_persona: business_view
    query_limits:
      max_concurrent: 2
      monthly_token_budget: 500000

  marketing:
    description: "市场运营"
    skill_allowlist: ["core/*", "teams/marketing/*"]
    table_access: ["dws_marketing_*", "dws_channel_*", "dim_*"]
    show_customer_real_name: true
    ui_persona: business_view
    query_limits:
      max_concurrent: 2
      monthly_token_budget: 400000

  risk_control:
    description: "风控团队"
    skill_allowlist: ["core/*", "teams/risk_control/*"]
    table_access: ["all_biz_tables"]
    show_customer_real_name: true
    ui_persona: analyst_view
    requires_2fa: true

  executive:
    description: "高管视图"
    skill_allowlist: ["core/monthly-report", "teams/executive/*"]
    table_access: ["agg_*"]
    show_customer_real_name: false   # ★ v1.6：高管视图只看代号化聚合
    ui_persona: executive_view
    query_limits:
      max_concurrent: 1
      monthly_token_budget: 100000
```

#### 7.2 团队特化 skills

原则：**核心 skills 共用，团队特化 skills 叠加**。

- `core/mj-ddd-semantics`：所有角色共用
- `teams/marketing/marketing-dictionary`：市场团队专用（渠道、活动、归因术语）
- `teams/product_manager/product-metrics`：产品经理专用（留存、活跃、漏斗定义）

**skill 所有权**：团队特化 skill 的 ownership 归该团队的"数据接口人"（business analyst 或 data champion），mj-agent owner 只维护 core/*。

#### 7.3 UX 分层

| Persona | 目标角色 | 特征 |
|---|---|---|
| **Analyst View** | data_analyst / risk_control | 显示 SQL、查询计划、原始数据表；可编辑 SQL 重跑；完整工具链 |
| **Business View** | product / marketing / operations | SQL 完全隐藏；图表优先 + 自然语言解读；"想深挖?" 按钮；预定义问题模板 |
| **Executive View** | executive | 关键数字卡片 + 趋势箭头；无详细数据；只看月度/季度汇总；对比历史基线 |

**关键**：结果呈现差异化是 Phase 4 最大的前端投入。可以参考 ChatGPT / Claude 的 artifact 模式。

#### 7.4 审计 & 合规 ★ v1.6 补充客户维度

每次查询记录完整事件：

```json
{
  "event_id": "evt-xxx",
  "user_id": "zhang.san",
  "user_role": "marketing",
  "team": "channel_ops",
  "question": "微信渠道上月转化率",
  "involved_customers": ["CUST_7f3a", "CUST_c2e8"],
  "accessed_tables": ["dws_marketing_channel_day"],
  "accessed_fields": ["channel_id", "conversion_count"],
  "anonymization_applied": true,
  "data_egress_tokens": 2340,
  "result_row_count": 5,
  "result_summary_hash": "abc123",
  "latency_ms": 3200,
  "total_tokens": 8500,
  "timestamp": "2026-08-15T14:23:01Z",
  "client_ip": "10.x.x.x",
  "approved_by": null
}
```

**新增字段（★ v1.6）**：
- `involved_customers`：本次调用涉及的客户 ID 集合，便于响应客户询问
- `anonymization_applied`：代号化是否生效
- `data_egress_tokens`：出域数据量（ADR-000 P1 的审计依据）

**月度合规报告自动生成**：
- 各角色使用概况
- 各客户的数据使用次数（可应客户要求导出）
- 异常模式（深夜访问、跨角色尝试、超预算调用）
- 按角色的错误率
- HITL 审批通过率

#### 7.5 按部门成本分摊

- LangSmith trace 带 `team` / `role` metadata
- 月度报表：各部门 token 消耗 + 预算执行率 + 按 skill 分拆
- 预算超支分级告警（单日 / 月度）
- 季度成本趋势分析

### 退出标准

- [ ] SSO 对接完成，至少 1 种身份源打通
- [ ] RBAC 生效，角色/权限矩阵清晰并在 CI 中有 policy 测试
- [ ] 至少 3 个非分析师团队正式接入（≥ 5 人/团队）
- [ ] 每个接入团队至少 1 个特化 skill 上线
- [ ] 审计日志 + 月度合规报告机制建立
- [ ] 按团队 cost report 月度可用
- [ ] 非技术用户 UX 验证（SUS 评分 ≥ 70 或主观反馈良好）
- [ ] 数据团队"代查"工单 ↓ 50%
- [ ] RBAC 红队演练通过
- [ ] **★ v1.6**：审计日志可按 customer_id 反查（响应客户询问的能力演练通过）

### 风险

- **风险**：非技术用户错信数据，基于错数据做决策 → **对策**：强制结果解读 + 明确数据口径展示 + 高风险查询 HITL 审批
- **风险**：RBAC 权限漏洞 → **对策**：policy 单元测试 + 季度红队演练
- **风险**：众口难调，跨团队需求冲突 → **对策**：先服务 1–2 个种子团队，跑 2–3 个月后再扩
- **风险**：团队特化 skill 维护负担 → **对策**：skill 所有权归团队数据接口人，mj-agent owner 只维护 core
- **风险**：非分析师查询压力冲击 biz 域 → **对策**：按角色查询限流 + 高峰期排队 + 结果缓存
- **风险**：SSO 对接工期超预期 → **对策**：Phase 4 启动前先做 1 周技术预研
- **★ v1.6 风险**：某客户合同更新后明确禁止数据用于特定分析 → **对策**：Phase 4 审计日志支持按 customer_id 快速检索和下线

---

## 8. 长期"不做"清单

- **不做** LangChain.js / LangGraph.js 侧的 agent 运行时
- **不做** 自研 agent 框架
- **不做** 把模型换成本地部署的开源模型（**Phase 4+ 可重新评估**，作为合规兜底方案）★ v1.6 措辞微调
- **不做** Mobile 原生 App
- **不做** 语音/视频多模态交互
- **不做** 跨企业生态
- **不做** 独立于 mj-system 的基础设施
- **不做** 直接访问 mj-system 的 ODS/DWD 原始层
- **不做** mj-system biz schema 的自动 L2 语义推断
- **不做** 在没有 evals 验证的情况下上线任何 skill/tool/model 变更
- **不做** 把 evals 门槛设为可选/可绕过
- **不做** 绕开 marketplace 插件直接造轮子
- **不做** mj-agent 的 SaaS 化 / 多租户形态
- **不做** 对外部机构客户或终端消费者开放 mj-agent
- **不做** ★ v1.6：客户间数据隔离机制（客户业务数据在内部分析师间允许跨客户使用）
- **不做** ★ v1.6：把 mj-agent 的分析结果对外输出给客户本人（分析结论仅供公司内部使用）
- **不做** ★ v1.6：特征泛化（"亿级"/"西南"等模糊化）机制（内部使用精确数据更有价值，过度设计）
- **不做** ★ v1.6：Code Execution Sandbox 作为 Phase 2 安全必需品（Phase 3+ 可作为能力扩展评估）

---

## 9. 关键决策节点与回退

**决策点 1（Phase 0 启动前）★ v1.6 新增：合规前置确认失败**
- 合规团队明确禁止客户业务数据过云 API → 整体 roadmap 转向本地模型路径
- 合规未明确但有灰色地带 → 先做 POC 演示数据流，再走合规

**决策点 2（Phase 1 末）：biz 域 skills 覆盖率不够**
- 8 周补不上 → 重新评估 agent 方案
- 根因在"biz 字段注释缺失" → 先推动 mj-system 数据字典治理

**决策点 3（Phase 2 初）：mj-system 不愿埋 dispatch 埋点**
- 降级为轮询 diff + 契约测试兜底

**决策点 4（Phase 2 中）：Judge agreement 长期低于 70%**
- Rework judge prompt
- 考虑换更强的 judge 模型
- 极端情况下降级为程序化 check only

**决策点 5（Phase 2 末）：evals 基线建不起来**
- agent 不确定性超预期 → 降级为"SQL 推荐工具"（不自动执行）

**决策点 6（Phase 3 入口）：用户不抱怨 Chainlit**
- 长期停在 Phase 2，精力投入 skills 深化

**决策点 7（Phase 4 入口）：非分析师团队无稳定接入需求**
- 数据团队代查负担低 / 没有跨团队推动人 / 公司无 SSO
- → 停在 Phase 3，不做组织内扩展，保持分析师专用工具形态
- 一旦出现上述 3 个条件中任意 2 个具备，再重启 Phase 4 评估

---

## 10. 可观测性与反馈循环

| 指标 | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|---|---|---|---|---|
| DAU / WAU | 手动统计 | LangSmith + 自建 | 前端埋点 | 按团队 / 角色分析 |
| SQL 准确率 | 人工抽检 | Evals 自动化 (EX + L3) | Evals + 用户反馈 | 按角色分层统计 |
| Judge agreement | – | 月度校准 | 月度校准 | 按团队分层采样校准 |
| 首 token 延迟 | 不关注 | 监控 | P50/P95/P99 | 按角色 SLA |
| Token 成本 | 不关注 | LangSmith 汇总 | 按 skill 分拆 | 按团队 / 部门分摊 |
| Evals 成本占比 | – | ≤ 20% 生产成本 | ≤ 20% | 按团队预算配额 |
| biz 域查询压力 | 人工观察 | 接入 mj-ops 插件 | 告警阈值 | 按角色限流 |
| schema 同步健康度 | 手工 | 自动 PR 数 / TODO 清零率 | 同上 | 同上 |
| 用户满意度 | 口头反馈 | 简单问卷 | NPS | 按角色 NPS |
| RBAC 合规度 | – | – | – | 权限漏洞 = 0 |
| **★ v1.6：出域数据量（每次 LLM 调用的数据 token）** | 不关注 | **Gateway 记录 P50/P95** | 同上 | 按角色/团队分桶 |
| **★ v1.6：代号化开关生效率** | – | **Gateway 记录** | 同上 | 按角色维度统计 |
| **★ v1.6：实体解析命中率** | 人工抽检 | **evals 自动化** | 同上 | 按团队分层 |

监控数据统一接入 mj-ops 插件面板。

---

## 11. 时间线参考

假设全职投入 1 人：

```
2026 Q2 (4-6月)  : Phase 0 + Phase 1   → DEV MVP 上线
                                        含 分析工具集 + 实体解析 + token 预算 ★ v1.6
2026 Q3 (7-9月)  : Phase 2              → 三环境上线 + LLM Gateway + 完整 evals ★ v1.6
2026 Q4 (10-12月): Phase 3 决策窗口    → 启动或停留
2027 H1          : Phase 3（如启动）   → dataRef 模式 + episodic 清理 ★ v1.6
2027 H2+         : Phase 4 决策窗口    → 视组织推广需求
2027 H2 / 2028 H1: Phase 4（如启动）   → RBAC + 多角色扩展 + 客户维度审计 ★ v1.6
```

---

## 12. 与 MJ-AgentLab 生态的深度对接

### 12.1 mj-system（一级仓库，核心依赖）
数据依赖（biz 域只读） + 部署依赖（docker-compose 兄弟服务） + 基础设施依赖 + 生命周期耦合 + 运维契约 + CONTRACT 文档。

### 12.2 mj-agentlab-marketplace（一级仓库，插件生态）
作为消费者：复用 mj-doc / mj-git / mj-n8n / mj-ops 插件。
作为贡献者：发布通用 skills（如 `mj-ddd-semantics`）。

### 12.3 生态拓扑

```
╔═══════════════════ MJ-AgentLab Organization ═══════════════════╗
║                                                                 ║
║   ┌─────────────┐                    ┌─────────────┐           ║
║   │  mj-system  │─── biz 域 只读 ───▶│  mj-agent   │           ║
║   │  (biz 域)   │◀── schema 变更 ────│ (data-agent)│           ║
║   │             │    dispatch        │             │           ║
║   └─────────────┘                    └─────────────┘           ║
║         ▲                                    ▲                  ║
║         │                                    │                  ║
║         │  共用 docker-compose               │                  ║
║         │  共用 PG 实例                      │                  ║
║         │  共用 self-hosted runners          │                  ║
║         ▼                                    ▼                  ║
║   ┌──────────────────────────────────────────────────────┐    ║
║   │         mj-agentlab-marketplace（插件生态）          │    ║
║   │                                                       │    ║
║   │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐    │    ║
║   │  │ mj-doc │  │ mj-git │  │mj-n8n  │  │mj-ops  │    │    ║
║   │  │(文档)  │  │(CI/CD) │  │(工作流)│  │(运维)  │    │    ║
║   │  └────────┘  └────────┘  └────────┘  └────────┘    │    ║
║   │                                                       │    ║
║   │  + 可复用 skills（mj-ddd-semantics 等）              │    ║
║   └──────────────────────────────────────────────────────┘    ║
║                                                                 ║
╚═════════════════════════════════════════════════════════════════╝
```

### 12.4 biz schema 同步流程

详见 `docs/schema_sync_flow.md` 和附录 D。

---

## 13. 团队责任矩阵

### 13.1 角色定义

- **mj-agent owner（Zack）**：agent 整体 owner
- **业务专家（数据分析师）**：领域知识 + golden cases + ★ v1.6：customer_codebook 业务含义维护
- **mj-system 团队**：biz 域 owner
- **marketplace maintainer**：插件维护（目前也是 Zack）
- **运维团队**：基础设施 + 三环境部署
- **★ v1.6：合规/法务对接人**：Phase 0 前置 + Phase 4 RBAC 合规审查
- **Phase 4 新增——团队数据接口人**：各接入团队的 data champion

### 13.2 责任矩阵

| 事项 | mj-agent owner | 业务专家 | mj-system | marketplace | 运维 | 合规 ★ | 团队数据接口人 |
|---|---|---|---|---|---|---|---|
| Agent 代码与架构 | **R/A** | C | I | – | I | – | – |
| 核心 skills 维护 | **R** | **C** | I | C | – | – | – |
| 团队特化 skill 维护（Phase 4）| C | – | – | – | – | – | **R/A** |
| Judge prompt 设计 | **R/A** | C | – | – | – | – | – |
| Golden seed cases | C | **R/A** | – | – | – | – | – |
| Judge 月度校准 | **R** | **C** | – | – | – | – | – |
| Production trace 回捞 | **R** | C | – | – | – | – | – |
| biz 域字段 comment | C | I | **R/A** | – | – | – | – |
| biz schema 版本 tag | I | – | **R/A** | – | – | – | – |
| CONTRACT 文档维护 | **R** | C | **R** | I | I | – | – |
| 三环境部署 | C | – | C | C | **R/A** | – | – |
| 监控告警 | C | – | – | C | **R/A** | – | – |
| RBAC policy 维护（Phase 4）| **R/A** | – | – | – | C | C | C |
| 团队 cost 预算（Phase 4）| **R** | – | – | – | – | – | **C** |
| **★ v1.6：云 LLM API 合规签署** | C | – | – | – | – | **R/A** | – |
| **★ v1.6：customer_codebook 维护** | **R** | **C** | I | – | – | I | – |
| **★ v1.6：Phase 4 客户维度审计响应** | **R** | C | – | – | – | **C** | – |

### 13.3 协作节奏

- **每 PR**：新 eval case；bug fix 必带 regression
- **每周**：mj-agent owner 回看 LangSmith 失败 trace
- **每两周**：owner + 业务专家 review production_samples
- **每月**：judge calibration；Phase 4 还有：按团队 cost 结算 + RBAC 合规报告
- **每季度**：全体回看 golden seed；Phase 4 还有：RBAC 红队演练
- **每次 biz schema 变更**：mj-system 发 tag → mj-agent owner review PR → 业务专家补 L2
- **每次 marketplace 插件 major 升级**：mj-agent owner 评估影响
- **Phase 4 新增——每次新团队接入**：mj-agent owner + 该团队数据接口人共同制定 skill 和 RBAC 配置
- **★ v1.6 新增——每次客户合同变更**：合规对接人提醒 mj-agent owner review 是否影响数据处理策略

---

## 附录 A：外部参考案例索引

- LangChain 官方 `deepagents/examples/text-to-sql-agent`
- `langchain-ai/agent-chat-ui`
- `CopilotKit/generative-ui`
- Spider / BIRD Text-to-SQL benchmarks
- Galileo Agent Evaluation Framework 2026
- Google Cloud "A methodical approach to agent evaluation"
- Maxim "LLM as a Judge: Practical, Reliable Path"
- **Casbin RBAC documentation**（Phase 4）
- **飞书开放平台 SSO 集成文档**（Phase 4 备选方案）
- **★ v1.6：Presidio / Microsoft**（PII 识别器参考，虽然 mj-agent 场景不涉及 PII，但代号化思路可参考其 tokenization 机制）
- **★ v1.6：Anthropic Enterprise / ZDR 协议文档**（Phase 0 合规前置参考）
- **★ v1.6：rapidfuzz / BGE-zh**（实体解析技术栈）

---

## 附录 B：本周立即行动清单

1. **★ v1.6 新增，最高优先级：和公司合规/法务对齐**
   - 客户业务数据通过云 LLM API 的合规路径
   - 需要签署的协议（DPA、ZDR、企业版）
   - 是否有客户合同明确禁止此类处理
   - 行业监管要求（人行、银保监等）
2. **和 mj-system 团队对齐 biz 域访问契约**
3. **和业务专家（数据分析师）对齐 evals 参与约定**：每月 ≥ 4 小时
4. **★ v1.6 新增：和业务专家一起起草 customer_codebook 初版**（至少覆盖常见 10–20 家客户）
5. **把路径图 v1.6 存进 Obsidian 的 `00-Projects/mj-agent/`**
6. **建 mj-agent 仓库结构**：
   - 通过 marketplace 安装 mj-doc / mj-git 插件
   - 落地 ADR-000 / 007（修订）/ 008 / 009 / 010 / 011 / 012 / 013 / 014 ★ v1.6
   - `docs/evals-design.md`
   - `docs/contracts/mj-agent-to-mj-system.md`（初版）
   - `evaluation/judges/` 三个 judge prompt
   - `evaluation/datasets/seed/golden_seed.jsonl`
7. **`uv init` 启动 Phase 0 骨架**

---

## 附录 C：需要澄清/调研的前置问题

### Phase 0 启动前

- [ ] mj-system 的 PG 版本 ≥ 15
- [ ] biz 域字段注释完备度
- [ ] mj-system 的 docker-compose 是否已有 Anthropic API 出口代理
- [ ] mj-ops 插件是否已覆盖日志聚合方案
- [ ] 三环境的 biz 域数据体量差异
- [ ] mj-system 是否已有 migration 工具链
- [ ] mj-system CI 是否能在 post-deploy 阶段运行自定义脚本
- [ ] LangSmith 账号额度是否支持 Phase 2 预期的 eval 运行量
- [ ] 业务专家能否承诺每月 4+ 小时 evals 参与时间
- [ ] marketplace 中 mj-git 插件是否覆盖 Python + Docker + 三环境部署场景
- [ ] marketplace 中 mj-doc 插件当前版本是否适用 mj-agent

### Phase 0 启动前 ★ v1.6 新增（最高优先级）

- [ ] **公司合规/法务确认**：客户业务数据通过云 LLM API（Anthropic / 国内厂商）进行分析，是否需要签 ZDR / 企业协议？合同条款如何？
- [ ] **现有服务合同审查**：是否有条款明确禁止客户业务数据用于任何形式的第三方服务调用？
- [ ] **金融行业监管确认**（人行/银保监等）：对公司作为数据处理方的具体要求是什么？
- [ ] **备选方案评估**：如果云 API 路径被否决，本地模型部署（Qwen/DeepSeek）的硬件预算和交付时间是多少？

### Phase 4 启动前

- [ ] biz 域是否已有字段级权限控制（RLS / column masking）
- [ ] 公司是否有统一 SSO 系统（飞书 / 企业微信 / AD / LDAP）
- [ ] 非分析师团队中有无 data champion（能 own 团队特化 skill 的人）
- [ ] 公司数据合规要求（等保 / 行业规范），决定审计日志粒度和保留期
- [ ] **★ v1.6**：是否有客户要求定期导出"其数据使用情况报告"？（决定审计日志的查询接口设计）

---

## 附录 D：biz schema 三层同步机制详细规范

### D.1 三层模型

| 层 | 内容 | 真相源 | 同步机制 | 阶段引入 |
|---|---|---|---|---|
| **L1 结构** | 表、字段、类型、约束、外键 | biz 域 PG | 自动（dispatch + export + PR） | Phase 0 初始化，Phase 2 全自动 |
| **L2 语义** | 业务含义、计算口径、枚举解释 | 业务专家 + PG `COMMENT` | 半自动（PR 模板 + 人工 review） | Phase 1 手工，Phase 2 规范化 |
| **L3 经验** | 常用查询、few-shot、已知陷阱 | 运行时累积 | 异步（episodic memory） | Phase 2 启动，Phase 3 加清理 |

### D.2 mj-system 侧必须做的事

**Phase 0 就启动**：
- biz 域所有字段必须有 `COMMENT ON COLUMN`
- biz 域 schema 变更走 migration 工具
- migration PR 模板要求写明业务含义

**Phase 2 前完成**：
- 在 CI 中集成 biz schema export 脚本
- 每次 biz 域变更发 tag `biz-schema-vYYYY.M.D`
- Breaking change 提前 2 周通知 + `BREAKING` 标记

### D.3 mj-agent 侧必须做的事

**Phase 0**：
- `scripts/fetch_biz_schema.py` 可手动运行
- 手工维护 `biz_domain_dictionary.md`

**Phase 1 末**：
- `tests/contract/test_biz_schema_alignment.py` CI 必跑

**Phase 2**：
- `.github/workflows/biz-schema-sync.yml` 监听 dispatch
- `scripts/sync_skill_from_schema.py` 处理 diff
- `compatibility.yaml` 版本兼容矩阵
- `docs/schema_sync_flow.md` 记录流程
- `docs/contracts/mj-agent-to-mj-system.md` 维护

**Phase 3**：
- `memory/cleanup/episodic_staleness.py` 处理 memory 漂移

**Phase 4**：
- biz schema 变更影响到团队特化 skill 时，触发对应团队数据接口人 review

### D.4 Breaking change 约定

| 变更类型 | 约定 | mj-agent 侧影响 |
|---|---|---|
| 新增表 | 直接 dispatch | 自动 PR，补 L2 即可 |
| 新增字段 | 直接 dispatch | 自动 PR，补 L2 |
| 字段类型变更（兼容） | 标 `MINOR` | 自动 PR，评估是否影响 SQL |
| 字段类型变更（不兼容） | 标 `BREAKING`，双写期 | 手动 review，全量 eval 回归 |
| 字段重命名 | 两阶段迁移 | 期间 skill 同时描述新旧字段 |
| 字段删除 | 2 周 deprecation 期 | 期内自动标 deprecated |
| 表删除 | 2 周 deprecation 期 | 同上 + episodic memory 扫描 |

### D.5 版本兼容矩阵格式

`compatibility.yaml`：

```yaml
mj_agent_version: 0.5.0
compatible_mj_system_biz:
  min: 2026.3.0
  max: 2026.5.x
tested_against:
  - 2026.3.15
  - 2026.4.1
  - 2026.4.15
known_incompatible:
  - version: 2026.2.x
    reason: 旧版本 dws_loan_credit_day 缺少 stat_dt 字段
startup_check:
  enabled: true
  fail_fast: true
  version_source: biz_domain_meta.version
```

### D.6 CONTRACT 文档位置与维护

CONTRACT 文档存放于 **mj-agent 仓库的 `docs/contracts/mj-agent-to-mj-system.md`**（不在 mj-doc 仓库——mj-doc 是插件，只提供文档规范，不存储具体文档）。

**维护责任**：mj-agent owner 和 mj-system 团队双方都有 PR 权限，任何修改要求对方 review。格式遵循 mj-doc 插件定义的 CONTRACT 规范。

**内容要求**：biz 域访问范围 / 只读账号权限规范 / 查询性能约束 / biz schema 变更流程 / 字段 comment 规范 / Breaking change 约定 / 版本兼容矩阵维护责任 / 联系人与 escalation 路径。

---

## 附录 E：配套文件清单

```
mj-agent/
├── docs/
│   ├── mj-agent-roadmap.md                  # 本文档
│   ├── architecture.md                      # Phase 2
│   ├── memory_architecture.md               # Phase 2
│   ├── context_engineering.md               # Phase 2
│   ├── deployment.md                        # Phase 2
│   ├── db_access.md                         # Phase 0
│   ├── skills_guide.md                      # Phase 1
│   ├── evals-design.md                      # Phase 2
│   ├── evals-maintenance.md                 # Phase 2
│   ├── schema_sync_flow.md                  # Phase 2
│   ├── llm_gateway.md                       # Phase 2 ★ v1.6
│   ├── entity_resolution.md                 # Phase 1-2 ★ v1.6
│   ├── multi-role-design.md                 # Phase 4
│   ├── rbac-policy.md                       # Phase 4
│   ├── team-onboarding.md                   # Phase 4
│   ├── contracts/
│   │   └── mj-agent-to-mj-system.md
│   ├── handover.md
│   └── adr/
│       ├── 000-data-llm-boundary.md         # ★ v1.6
│       ├── 001-python-only-runtime.md
│       ├── 002-skills-first-class.md
│       ├── 003-progressive-disclosure.md
│       ├── 004-memory-separation.md
│       ├── 005-evals-as-gating.md
│       ├── 006-fail-safe-reads.md
│       ├── 007-role-based-scoping.md        # v1.6 重命名
│       ├── 008-co-deployment.md
│       ├── 009-biz-as-primary-source.md
│       ├── 010-independent-repo.md
│       ├── 011-biz-schema-sync.md
│       ├── 012-aggregate-first.md           # ★ v1.6
│       ├── 013-generative-ui-dataref.md     # ★ v1.6
│       └── 014-customer-anonymization.md    # ★ v1.6
│
├── src/mj_agent/
│   ├── tools/
│   │   ├── sql/
│   │   ├── analysis/                        # ★ v1.6（Phase 1）
│   │   ├── charts/
│   │   └── excel/
│   ├── entity/                              # ★ v1.6（Phase 1 L1+L2, Phase 2 L3）
│   ├── gateway/                             # ★ v1.6（Phase 2）
│   ├── memory/
│   ├── middleware/
│   └── ...
│
├── config/
│   ├── customer_codebook.yaml               # ★ v1.6（加密存储）
│   ├── anonymization_policy.yaml            # ★ v1.6
│   ├── roles.yaml                           # Phase 4
│   ├── permissions.yaml                     # Phase 4
│   └── team_budgets.yaml                    # Phase 4
│
├── evaluation/
│   ├── judges/{outcome,trajectory,component}_judge.md
│   ├── datasets/
│   │   └── seed/{README.md, golden_seed.jsonl}
│   ├── metrics/
│   ├── runners/
│   └── thresholds.yaml
│
└── scripts/
    ├── fetch_biz_schema.py                  # Phase 0
    ├── diff_biz_schema.py                   # Phase 1
    ├── sync_skill_from_schema.py            # Phase 2
    ├── rbac_audit.py                        # Phase 4
    └── cost_attribution.py                  # Phase 4
```

**通过 marketplace 安装的插件**：mj-doc / mj-git / mj-n8n / mj-ops

---

## 附录 F：v1.6 版本变更总览 ★ v1.6 新增

### F.1 新增 ADR（4 个）

| ADR | 标题 | 核心内容 |
|---|---|---|
| ADR-000 | Data-LLM Boundary Principles | 三原则总纲：P1 最小必要出域 / P2 链路隔离 / P3 工具化间接操作 |
| ADR-012 | Aggregate-first Analysis Loop | 按 token 预算自动聚合，Agent 自主推理决定聚合策略 |
| ADR-013 | Generative UI with Data Handle Pattern | LLM 只输出 dataRef，真实数据前端直取，两条链路物理隔离 |
| ADR-014 | Customer Data Anonymization | 客户名代号化可配置机制，与实体解析共享主数据 |

### F.2 修订 ADR（1 个）

| ADR | v1.5 → v1.6 变化 |
|---|---|
| ADR-007 | 从 "Context Isolation（角色/团队隔离）" 重命名为 "Role-based Context Scoping"，明确这是能力视图层分层，不涉及数据隔离 |

### F.3 新增工程组件

| 组件 | 位置 | Phase | 目的 |
|---|---|---|---|
| 分析工具集 | `src/mj_agent/tools/analysis/` | Phase 1 | ADR-012 的实现，含 aggregate/compare/drill_down/anomaly/token_estimator |
| 实体解析模块 | `src/mj_agent/entity/` | Phase 1-2 | 机构/产品名称归一化，5 层兜底 |
| LLM Gateway | `src/mj_agent/gateway/` | Phase 2 | 所有 LLM 调用的统一出口，集中代号化 / 预算 / 审计 |
| 客户代号表 | `config/customer_codebook.yaml` | Phase 1 手工、Phase 2 加密主数据 | ADR-014 的实现 |
| 代号化策略 | `config/anonymization_policy.yaml` | Phase 2 | ADR-014 的运行时配置 |

### F.4 删除/降级的设计

| 设计 | 状态变化 | 原因 |
|---|---|---|
| 特征泛化（"亿级"、"西南"泛化） | **删除** | 内部使用精确数据更有价值，过度设计 |
| 客户间数据隔离机制 | **删除** | 内部允许跨客户分析，不是需求 |
| Code Execution Sandbox 作为 Phase 2 安全必需品 | **降级** | 从安全必需变为 Phase 3+ 可选能力扩展 |
| "按敏感度分级聚合" 的复杂配置 | **简化** | 改为按 token 预算自动判断，Agent 自主推理 |
| PII 导向的 T0/T1/T2 分级 | **未采纳** | 数据不含 PII，分级命名不贴切 |

### F.5 v1.5 → v1.6 的核心认识转变

| 维度 | v1.5 | v1.6 |
|---|---|---|
| 数据性质 | 模糊"敏感数据" | 明确"客户业务数据"（无 PII） |
| 核心风险 | 多元（PII / 隔离 / 推断） | 单一（数据出域到云厂商） |
| 防线设计 | 多重组合拳 | 三原则 + 三层轻量机制 |
| 代号化定位 | 强制脱敏 | 可配置开关 |
| Code Sandbox 定位 | 安全必需 | 能力扩展 |
| 聚合策略驱动力 | 隐私保护 | token 预算 + 分析质量 |
| 客户间隔离 | 隐含必要 | 明确不做 |

### F.6 下一步行动

**本周**：
1. 合规对齐会议（最高优先级）
2. Phase 0 骨架启动
3. customer_codebook 初版（10–20 家客户）

**Phase 0 结束前**：
- 确认云 LLM API 合规路径
- 完成 ADR-000/012/013/014 的完整文档

**Phase 1 期间**：
- 实现 tools/analysis/
- 实现 entity/ 最小版（L1+L2）
- 实现 token 预算机制

**Phase 2 期间**：
- LLM Gateway 上线
- 实体解析 L3 语义层
- customer_codebook 升级为加密主数据

---

*文档维护约定：每个阶段结束时做一次 retro。文档版本与 mj-agent 仓库 tag 对应。v1.6 签署：待 Phase 0 合规前置确认后正式生效。*
