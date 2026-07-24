---
type: adr
domain: DATA
summary: 决定 memory checkpoint 中 execute_sql 逐字 biz 派生行的 at-rest 脱敏方向（ADR-037 命名为 Phase-2 动因、零机制设计的后继）。Owner 两裁定（2026-07-20）：Ruling 1 = store-at-rest 数据最小化是目标（独立于「谁读」，ADR-037 的 Codex memory 投影维持不变、不走 MCP-flip 回退）；Ruling 2 = 机制 B——持久化时把 execute_sql ToolMessage 的 rows 替换为确定性 per-column 摘要（min/max/count/distinct）、保留 executed_sql 供 recoverable-by-refetch，live 会话不动（persist-time hook，仅 memory/、非必停面），可选叠 C（TTL）收标准暴露窗口。B 优于 A（不可逆抹除、roadmap 脆）/ C（仅补充）/ D（保密非最小化、对 Codex 不透明冲突 ADR-037、加密钥管理）。不放宽 ADR-006/009/000 数据边界；实现递延 #365；langgraph 内部假设须对钉版 wheel 核验、canary 锁「双写-否则漏」footgun（ADR-029 #288 类）
owner: ranzuozhou
created: 2026-07-20
updated: 2026-07-20
state: active
decision: accepted
track: code
tags:
  - adr
  - data-boundary
  - memory
  - checkpointer
  - desensitization
  - phase-2
  - data-agent
---

# ADR-038: Memory Checkpoint At-Rest Desensitization of biz-derived rows（Phase-2；ADR-037 后继）

## Context

[[ADR-037_Memory_PG_MCP_Projection_To_Codex|ADR-037]]（2026-07-17）在 5-lens security+honesty 双 lens
更正后诚实记录：memory checkpointer 持久化**完整** message state，**含 `execute_sql` 的 ToolMessage
（envelope 携逐字 biz `rows`/`business_summary`）**，且当前**无裁剪/摘要**（summarization = Phase 2+）
→ memory 库**确含 biz 查询结果**。ADR-037 把「本 at-rest 暴露面」列为**优先推进 Phase-2 checkpoint
摘要/脱敏的动因之一**（ADR-037:90）——但**只是动因，零机制设计**。本 ADR 即该后继，**裁定方向**。

grounded 现状（file:line）：

- checkpointer 在 `src/mj_agent/memory/checkpointer.py:88` 以 `AsyncPostgresSaver(pool)` **裸装配**
  （无 `serde=`、无 wrapper、graph 与 Postgres 之间无拦截 hook），写入**独立** `mj_agent_memory` 库
  （专属 `mj-agent-postgres` 容器，读写凭据 `mj_agent_memory_user` ≠ biz `analyst` RO）。
- `execute_sql`（`src/mj_agent/tools/sql/execute.py:118-127`）返回 8 键 dict，**唯 `rows` 携真实 biz
  cell 值**（≤`sql_max_rows`=500）；`business_summary`（`execute.py:38-53`）是仅由 row_count/truncated/
  timeout 算出的**启发式占位、不含真实值**，当前**不能替代 rows**。成功路径下 LangGraph tool executor
  把整 envelope 序列化进 `ToolMessage.content`（JSON 串），进 message 通道 → 被默认 `JsonPlusSerializer`
  写入 `checkpoint_blobs`（BYTEA）。**无 TTL/retention/eviction**，rows 按 thread_id 无界累积。
- `src/mj_agent/memory/` **非 4 项 in-source 专属必停面**（`src/mj_agent/AGENTS.md`「独立 capability」）
  → persist-time hook **不触必停**。

为什么这不是边界破口、但仍是缺口：memory 独立库+独立凭据 → 读它无法触达 biz 表、无法绕 L1/L1b、
无法发起新 biz 查询，只得**历史上已过 guardrail 批准**的结果（[[ADR-006_Fail_Safe_Reads|ADR-006]]/
[[ADR-009_Biz_Domain_As_Primary_Data_Source|ADR-009]] 保护的是上游数仓，不是本 memory 面）。但它
**确是一份「已批准 biz 结果」的 at-rest 副本**坐在第二库、post-ADR-037 也可被 Codex 读——这正是本
ADR 要 harden 的对象。

两条载荷事实（作者亲跑 file:line 复核，防错误前提——选项里的事实断言是拍板前提、断言为假则原拍板作废）：

1. **durable 跨会话 resume 今日未上线**——`src/mj_agent/ui.py:134-137` 每 `on_chat_start` 铸新
   `thread_id = str(uuid.uuid4())`，全 `src/mj_agent/` **无 `on_chat_resume` handler** → 持久化的 rows
   写多读回少。Caveat：LangGraph Studio 可按 `thread_id` resume（dev 工具），roadmap 指向 durable
   multi-turn memory → 该事实**今真、roadmap 脆**。
2. **memory×5 MCP tier = `project`**（`sdd/development-agent.yml:735-739`）；biz×5 + ssh-manager
   = `never`（740-745）——「只在意 Codex 读路径」的廉价 MCP-flip 回退**技术上可行**，但见 Ruling 1 被否。

设计空间已由两个 workflow 做实（Understand 5 readers + Design-space 4 approaches + critic）：4 机制族
A/B/C/D + critic 补 5（GRANT 收权 / 不落盘 / 侧表指针 / 可逆 tokenization / 存储层 TDE）+ 叠合性
（A⊕B 互斥、C·D 正交可叠）。全文见设计证据（见 §Relationship）。**勿混淆**：roadmap 的「代号化/脱敏」
是 egress 路径 customer-NAME 匿名化（ADR-014-planned LLM Gateway，从未落地）——是 cloud LLM 看什么，
非 checkpointer at-rest 脱敏；Phase-3 `episodic_staleness` 是 90 天 drift 清理——也不是脱敏。

## Decision

Owner 两裁定（2026-07-20，AskUserQuestion）：

**Ruling 1（范围）= Store-at-rest 数据最小化是目标**。关切对象是 at-rest 库里逐字 biz 派生行本身
（数据最小化），**独立于「谁读」**；[[ADR-037_Memory_PG_MCP_Projection_To_Codex|ADR-037]] 的 Codex
memory 投影**维持不变**（不撤 2026-07-17 拍板、不走 memory×5 `project→never` 的 MCP-flip 回退）。

**Ruling 2（机制）= B（persist-time 确定性摘要 + 留 SQL）**。在**持久化时**把 `execute_sql`
ToolMessage 的 `rows` 替换为**确定性 per-column 摘要**（如每列 `{non_null, distinct, min, max}`）、
**保留 `executed_sql`**（recoverable-by-refetch）；**live 会话不动**（hook 仅在 `memory/` 落，非必停）。
**可选叠 C（TTL）** 收标准暴露窗口。

选 B 的理据（对比 A/C/D）：

1. **满足 Ruling 1 最小化**：抹去逐字 cell 值。
2. **与保留的 ADR-037 一致**：留 envelope 形状/统计/SQL 给 Codex——Codex 保留**有意义但非逐字**的
   memory 可见性（非只见 stub 或密文）。
3. **对 resume roadmap 稳健**：留 `executed_sql` → cold resume 可重跑同一 guardrail-approved 查询
   **refetch** 全 rows（相对时间/「latest」查询有 drift caveat）。
4. **工程性质温和**：确定性、可单测、**不调 LLM**（LLM 摘要会把 biz 行再 egress、非确定、可幻觉，对
   at-rest 控制净负）、**无密钥管理、无新依赖、非必停**、default-off flag 可控回滚。

## Consequences

- **正向**：以数据最小化控制关闭 ADR-037 记录的 at-rest 残留；Codex 仍保留 envelope 形状/统计/SQL 的
  memory 可见性（不破坏 ADR-037 意图）。
- **负向 / 诚实局限**：
  1. **不覆盖 AIMessage 里被助手复述的 biz 值**（NL 答案原样持久化）→ B 是**强 bulk 最小化**，非完整
     at-rest 保证；答案侧属 egress/answer-side 控制、**out of scope**。
  2. **forward-only**：部署前已存 checkpoint 仍含全 rows，除非另 fund 一次性 backfill（对 BYTEA
     serializer-encoded blob，单独 job）。
  3. **refetch drift**：相对时间查询重跑结果可能异于原 turn。
  4. **`row_digest` 仍是 biz 派生**（列聚合），敏感度远低于逐字行、但非零——如需更强，走 §Alternatives
     的 GRANT 收权 / 侧表隔离。
  5. **机制细节依赖 langgraph 内部假设**（双 `aput`/`aput_writes` override、默认 serde 路径）——**实现
     切片必须对钉版 wheel 核验**；**canary 测锁「双写-否则漏」footgun**（同
     [[ADR-029_Tool_Error_Surfacing_To_LLM|ADR-029]] #288 单/双 hook 教训）。
- **中性 / 递延**：**实现递延 #365**（本 ADR 是其阻塞决策 AC1）。build 期 carrier 门：`memory/` code =
  普通 PR（非必停）；**若日后转 D 加密**须 [[ADR-030_Secrets_Bundle_Split_For_MCP_Isolation|ADR-030]]
  附录记 AES-key sourcing/rotation/backup-co-location（丢钥=历史永久不可读）；**被否的 MCP-flip** 会触
  D-017 + V11 blocking gate；**任何新 canary blocking CI gate** 受 `ci-blocking-gate-toggle` +
  `policies/ci-gates.md` §4:41 一周 dry-run（**不得自判 N/A**，D-016 day-1 豁免仅信任面/MCP）。capability
  slot `data-agent.memory-checkpointer`（现按名保留）在 build 切片实体化。

## Alternatives considered

- **A — persist-time 硬抹除（shape-stub）**：rows 降为占位 stub、保留 executed_sql。**否为主选**——
  cold-resume 不可逆丢 rows、roadmap 一旦上线 durable resume 即变错（今日无 resume UX 下 fidelity≈0）、
  比 B 少留给 Codex 的信号。**保留为退路**（若 digest 成本被判不值）。
- **C — TTL/retention 单用**：仅收标准暴露窗口、不脱敏 live/recent → 补充非独立解。**采纳为可选叠加**
  （须配 backup-retention 才真成保留控制，否则有效窗口 = MIN(TTL, backup-retention)）。
- **D — encrypt-at-rest**（langgraph `EncryptedSerializer`）：无损 + 保密，但**是保密非最小化**（全数据
  仍在）、令 checkpoint 对 Codex 不透明（**冲突保留的 ADR-037**）、加 AES 密钥管理。**否**（不契合最小化目标）。
- **MCP-flip（memory×5 `project→never`）**：「只在意 Codex 读路径」的廉价回退。**Ruling 1 否**——会撤销
  2026-07-17 刚拍板赋予 Codex 的 memory 可见性。
- **设计评估另补 5 机制**（GRANT 收权 / 不落盘 ephemeral / 侧表指针 detach / 可逆 tokenization / 存储层
  TDE-LUKS）：**点名未采纳**，需求变化时可再评。

## Relationship

- **后继** [[ADR-037_Memory_PG_MCP_Projection_To_Codex|ADR-037]]（本 ADR 即其命名为动因的 Phase-2 方向）；
  **不改** ADR-037 的投影决策。
- **不放宽** [[ADR-000_Data_LLM_Boundary_Principles|ADR-000]]/[[ADR-006_Fail_Safe_Reads|ADR-006]]/
  [[ADR-009_Biz_Domain_As_Primary_Data_Source|ADR-009]] 数据边界（biz×5 + ssh 永 `never`、L1/L1b 不变）
  ——memory 库从来不是 biz 表通道。
- **不改** [[ADR-030_Secrets_Bundle_Split_For_MCP_Isolation|ADR-030]] secrets 边界。
- **追踪**：#365（owning issue，本 ADR = 其 AC1）；相关总锚 #312。
- **机制 C 落地（#386）**：本 ADR 采纳为「可选叠加」的机制 C（TTL 逐出）已实现，落
  `capabilities/data-agent/memory-checkpointer` REQ-005 + `contracts/checkpoint-retention.contract.yml`
  ——opt-in `mj-agent memory-evict`（默认关；按 uuid6 `checkpoint_id` 定龄；经 langgraph `adelete_thread`
  删整线程；无 in-app 调度器→外部 cron）。§Consequences「可选叠 C」+ §Alternatives「C 采纳为可选叠加」
  于此兑现；backup-retention 依赖仍为设计注记（当前无备份管线）。
- **设计证据**：`[ASSESSMENT]_checkpoint-desensitization-design-space`（Owner vault 草稿 v0.1；升格后落
  `evidence/assessments/`）——4+5 机制族全枚举 + 两裁定 + 7 open questions。
