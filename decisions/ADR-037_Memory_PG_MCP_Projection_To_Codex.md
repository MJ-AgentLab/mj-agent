---
type: adr
domain: WORKFLOW
summary: 授权把 mj-agent 自有的 memory PostgreSQL MCP servers（pg-mj-agent-memory-*×5）投影进 Codex 的 .codex/config.toml（dual-agent-compat v5 议题 1）——把 manifest mcp 档位由 project-with-adr 翻转为 project；理据（5-lens 2026-07-17 更正后的诚实前提）= memory pg 是独立数据库 + 独立凭据（mj_agent_memory_user ≠ analyst），其 checkpoint **确含 execute_sql 输出的 biz 派生行**（当前无摘要，Phase 2+），但读它无法触达 biz TABLES / 绕 L1/L1b、只得历史已过 guardrail 的结果，且 Claude Code 已有同径访问（本 ADR extends 非 creates），消费受 HKCU env + Codex trust 双门 + AGENTS.md 自守；凭据经 env_vars 按名透传、零字面凭据入仓（G7/PJ044 守，机制与 github #330 AC7 逐字相同）；议题 3(#353) pass-by-name 改造已消除 .mcp.json 内嵌 default（单一真相 = secrets-mcp.enc→HKCU env、未设即显式失败）；biz×5 + ssh-manager 保持 PERMANENTLY never（ADR-006/009 数据边界 + prod surface 不变，D-013）；可逆（翻回 never + re-sync）；该翻转即 project-with-adr 档名承诺的 ADR 半边（D-013/D-017 Owner 拍板 + 前提更正后重确认）
owner: ranzuozhou
created: 2026-07-17
updated: 2026-07-17
state: active
decision: accepted
track: engineering-workflow
tags:
  - adr
  - dual-agent
  - codex
  - mcp
  - data-boundary
  - projection
  - workflow
---

# ADR-037: Memory PostgreSQL MCP Projection to Codex (议题 1)

## Context

[[ADR-036_Dual_Agent_Thin_Adapter_And_Projection|ADR-036]] D-013 确立 MCP 投影按 per-server 三档
（`project` / `project-with-adr` / `never`，默认 `never`）：首批 `project` = github / playwright /
serena；**`pg-mj-system-biz-*`×5 + ssh-manager = `never`**（[[ADR-006_Fail_Safe_Reads|ADR-006]]/ADR-009
数据边界 + prod surface，永不投影）；而 **`pg-mj-agent-memory-*`×5 = `project-with-adr`**——一个
**停泊档**，语义为「意图投影，但落地须配 ADR + 独立拍板」（program plan §S3 议题 1「memory×5 落地
`project-with-adr`」；D-013「独立拍板后落地」）。

停泊而非直接 `project` 有两重原因：

1. **治理**：把 mj-agent 的一个数据面暴露给第二个 harness（Codex）是难逆的信任姿态变更（D-017
   `mcp-server-trust-posture-change`），值得一条决策记录。
2. **技术前置**：投影一经开启即被 emitter 两道 fail-close guard 挡死——G-A（`"${" in arg`，
   `agents_sync.py` 无条件子串测试）与 G-B（URL userinfo 形状）——因当时 `.mcp.json` 的 pg args 内嵌
   `${VAR:-postgresql://…}` 字面 default。解开它需要先做 **pass-by-name 改造**（议题 3 / #353）。

议题 3（#353，本 ADR 同批切片）已完成该改造：`.mcp.json` 10 个 pg server 的 args 改为**具名变量**
（`MJ_AGENT_PG_MEMORY_DEV_URL` 等）、`env` 改为 `{NAME: "${NAME}"}`；`pg-server-start.cmd` 从具名 env
解析 URL、无内嵌 default、未设即显式失败。**单一真相 = `secrets-mcp.enc`→HKCU env**
（[[ADR-030_Secrets_Bundle_Split_For_MCP_Isolation|ADR-030]] 2-bundle；MCP secret 永不入 `.env`）。
至此 memory×5 的 args 无 `${`（过 G-A）、无 credential 形状（过 G-B），env 为纯 `${VAR}` 引用
（过 `_ENV_REF` 纯度 → 渲染 `env_vars=[NAME]`），可 verbatim 投影。

本 ADR 即 `project-with-adr` 档名承诺的「ADR 半边」，授权把 memory×5 由 `project-with-adr` 翻转为
`project`。

## Decision

**接受**：把 `sdd/development-agent.yml` 的 `mcp.servers` 中 `pg-mj-agent-memory-*`×5 的
`projection_policy` 由 `project-with-adr` 翻转为 `project`，使 `agents_sync.py sync` 将其投影进
`.codex/config.toml`（Codex 消费）。

理据：

1. **memory pg 是独立库 + 独立凭据——但其 checkpoint 确含 biz 派生行（5-lens 2026-07-17 更正的诚实前提）**。
   ADR-006/009 数据边界保护的是**上游业务数仓**（`pg-mj-system-biz-*`）：L1/L1b SQL guardrail、`analyst`
   只读角色、schema allowlist——因为 raw client 直投 = 把绕过 guardrail 的通道递给无 harness 门的工具。
   `pg-mj-agent-memory-*` 是 **mj-agent 自有的 memory / checkpointer 状态库**（AsyncPostgresSaver，
   `mj-agent-postgres` 容器，凭据 `mj_agent_memory_user` ≠ `analyst`）。**关键澄清**（本 ADR 初稿误述
   memory「不含 biz 数据」，5-lens security+honesty 双 lens 逮到）：checkpointer 持久化完整 message state，
   **含 `execute_sql` 的 ToolMessage（envelope 携 biz `rows`/`business_summary`）**，且当前无裁剪/摘要
   （summarization = Phase 2+）→ memory 库**确会含 biz 查询结果**。真正可辩护的边界不是「无 biz 数据」，
   而是：**(a)** memory 是独立库 + 独立凭据 → 读它**无法触达 biz TABLES、无法绕 L1/L1b、无法发起新 biz
   查询**，只得**历史上已过 guardrail 批准的结果**；**(b)** Claude Code 已有对同一 memory 库同径 raw 访问
   （同 5 个 MCP server）→ 本 ADR 是 **extends 非 creates** 暴露面；**(c)** 消费受每工程师 HKCU env +
   Codex trust（D-015）双门；**(d)** Codex 由 AGENTS.md 自守数据边界。据此增量风险有界、可接受——初稿前提有误已带更正回 Owner；**Owner 2026-07-17 在更正前提下重确认
   投影决策成立**（承 [[feedback_wrong_premise_voids_decision|错误前提纪律]]）。

2. **凭据零字面入仓**。投影只写 `env_vars = ["MJ_AGENT_PG_MEMORY_*_URL"]`（按名白名单）；连接串
   由 Codex 从父进程 HKCU env 按名透传给 MCP 子进程，**`.codex/config.toml` 内无任何字面凭据**
   （G7 secret 扫描 + V9 PJ044 守）。该机制与已投影的 `github`（`env_vars=["GITHUB_PERSONAL_ACCESS_TOKEN"]`）
   **逐字相同**，且 github 已在 S2 #330 AC7 实机验证成功（走 env_vars 凭据链）。

3. **单一真相 + 显式失败**（议题 3 收益）。default 不再两处（HKCU env / `.mcp.json` 内嵌）分叉；
   env 未设 = 显式失败（exit 3），不再静默连 localhost 兜底。

4. **biz×5 + ssh-manager 不动**。保持 `never`，永不投影（D-013；ADR-006/009 数据边界 + prod surface
   不变）。本 ADR **不**放宽任何数据边界，只授权 mj-agent 自有 memory 面的投影。

## Consequences

- **正向**：Codex 与 Claude Code 在 memory MCP 上能力对等（closes dual-agent-compat 议题 1）。
- **新暴露面（诚实描述）**：Codex（在受信仓内、HKCU env 已设）可经 5 个 memory MCP server 对 memory 库跑
  raw `query`（`@modelcontextprotocol/server-postgres` 暴露）→ 可 `SELECT` 到历史 checkpoint 中**含 biz
  查询结果**的会话状态。**可接受性据 Decision 理据 1 的 (a)-(d)**（独立库/独立凭据、无法绕 L1/L1b、
  extends 非 creates、双门 gated、AGENTS.md 自守）；凭据仍经 OS env 按名传递、从不入仓、从不明文落
  `.codex/config.toml`。**驱动**：本暴露面是优先推进 Phase-2 checkpoint 摘要/脱敏的动因之一。
- **可逆**：任意时刻把档位翻回 `never`（或 `project-with-adr`）+ `agents_sync.py sync` 即完全撤销投影
  （源从未被改写；D-012）。
- **消费前置**：Codex 侧实际连接仍需 (a) 该工程师机器的 HKCU env 已设 `MJ_AGENT_PG_MEMORY_*_URL`
  （`setup-mcp-secrets.ps1`）、(b) 该仓为 Codex 受信 project（D-015，每工程师×每 worktree 人工 trust）。
  全链路实机核验（`codex mcp list` + 一 memory-server 查询）为 #353 的实施期 AC（Owner 协同）。

## Alternatives considered

- **B — 不投影（维持 `project-with-adr`，关议题 1）**：Codex 侧若需 memory MCP 走个人
  `~/.codex/config.toml`（仓治理外）。**否决**——留下 Claude↔Codex 长期能力不对等，且不解决
  `.mcp.json` 两处真相问题。
- **C — emitter 侧字面转换**（仿 serena `transform`）：Codex TOML 无 `${VAR}` 插值 → emitter 只能内嵌
  **字面**连接串 → 恰是 G-B 存在的目的（`literal credentials are never projected`），等于把凭据写进
  受版本控制的 `.codex/config.toml`。**设计上否决**（违反 ADR-030 + G7）。

## Relationship

- 实施 D-013（memory×5 落地档）+ D-017（trust-posture 变更 Owner 拍板）。
- 依赖议题 3（#353 pass-by-name 改造）为技术前置；二者同批切片、同一 Owner 拍板（2026-07-17）。
- 不改 ADR-006/009 数据边界（biz×5 + ssh 永 `never`）；不改 ADR-030 secrets 边界（凭据按名、永不入仓）。
- 总锚：#312（dual-agent-compat v5 实施总锚，议题 1 复选框）。
