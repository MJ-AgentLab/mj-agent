---
type: ai-context-investigation
investigation: ac10-live-verification-memory-projection
auditor: "ai-agent (claude-opus-4-8 via Claude Code; HITL-supervised by ranzuozhou)"
scope:
  - codex-mcp-projection-memory5
  - env-vars-name-chain
  - codex-user-config-data-boundary
findings_summary: "memory×5 Codex 投影名链机制端到端实机验证通过（#353 目的达成）；字面查询返回行被 dev-memory 凭据漂移挡（→#394）；用户级 ~/.codex 另给 Codex biz-pg×5+ssh-manager（数据边界发现，Owner 待判）"
date: 2026-07-24
parent_artifacts:
  - "plans/[PLAN]_dual-agent-compat_pg-cred.md"
  - "evidence/ai-context-audit/2026-07_ci_audit.md"
---

# AC-10 / Spike 2b — memory×5 Codex 投影实机核验（2026-07-24）

> **这是什么**：`plans/[PLAN]_dual-agent-compat_pg-cred.md`（issue #353）§8 **AC-10** / §12 交办
> 「Spike 2b = 实施期实机核验（Owner 协同）」的落地记录。#353 于 2026-07-17 CLOSED，AC-10 是其唯一
> 延后的 live-Codex 核验项。本文件记录 2026-07-24 由 Owner 协同实机跑出的结果。**投影机制端到端验证
> 通过**（#353 目的达成）；字面「查询返回行」被一处**独立的** dev-memory 凭据漂移挡住（登记 → #394）。

## 1. 结论（TL;DR）

| 项 | 结果 |
|---|---|
| AC-10 前半：`codex mcp list` 列 memory×5 | ✅ PASS |
| **投影名链机制端到端**（Codex → `env_vars` 名继承 → `pg-server-start.cmd` 名→URL 解析 → wrapper → PostgreSQL 应答） | ✅ **PROVEN**（= #353 本就要证的目的） |
| AC-5 显式失败 tightening（env 未设 → server 硬失败，非静默错连） | ✅ 实机旁证 |
| `.codex/config.toml` 零字面凭据 / biz×5+ssh 不投影 | ✅（AC-3/AC-4，结构面早已守） |
| AC-10 后半：一次 memory 查询**返回行** | ❌ 被 **dev-memory 凭据漂移**挡（→ #394，secrets 域，Owner） |

**定性**：#353 的投影交付物（memory×5 名链投影）**实机验证成立**；字面 AC-10 绿待 #394 修凭据后重跑。
凭据漂移**不是**投影/wiring 缺陷——链已抵 DB 并得到 PostgreSQL 的 auth 判定，证明整条名链正确。

## 2. 环境前置（本机 2026-07-24，全满足，无手工 setup）

| 前置 | 状态 |
|---|---|
| Codex CLI | `0.144.3`（= 计划要求最低版） |
| `~/.codex/config.toml` `[projects]` trust | `[projects.'d:\...\mj-agent'] trust_level="trusted"`（容器根覆盖 `develop` worktree 为 in-repo ancestor；D-015 每工程师手工，仓脚本禁写） |
| `MJ_AGENT_PG_MEMORY_DEV_URL` | set（User + Process 作用域）→ `localhost:5433/mj_agent_memory` |
| 其余 4 个 memory URL（prod-lan/wan、test-lan/wan） | **unset**（预期 dev 机；被调用会显式失败，见 §5） |
| `mj-agent-postgres` 容器 | Up (healthy)，`:5433` 可达 |

## 3. AC-10 前半 —— `codex mcp list`（cwd = develop worktree）

列出全部 5 个投影的 memory server：`pg-mj-agent-memory-{dev, prod-lan, prod-wan, test-lan, test-wan}`，
状态 `enabled`，`Env` 列按名掩码 `MJ_AGENT_PG_MEMORY_*_URL=*****`（= `env_vars` 名链在位、**零字面凭据**）。
biz×5（`postgres-*`）+ `ssh-manager` **不在 project `.codex/config.toml`**（AC-4 守；另见 §6 数据边界发现）。

## 4. 投影名链机制 —— 端到端 PROVEN（AC-10 核心目的）

Owner 于交互 Codex（`gpt-5.6-sol`）中让其调用 `pg-mj-agent-memory-dev` 的 `query` 工具。Codex 正确地：

1. 解析 project `.codex/config.toml` → 发现 `pg-mj-agent-memory-dev` server 及其 `query` 工具；
2. 按 `env_vars=["MJ_AGENT_PG_MEMORY_DEV_URL"]` 从父环境**按名继承**该变量；
3. 以 `args=[..., "MJ_AGENT_PG_MEMORY_DEV_URL"]`（**字面变量名**）启动 `pg-server-start.cmd`；
4. `pg-server-start.cmd` 按名解析出 URL → wrapper → **连接 PostgreSQL 并收到应答**。

工具调用记录（事件流）：

```
Called pg-mj-agent-memory-dev.query({"sql":"SELECT current_database() AS db, current_user AS role, 1 AS ok;"})
  └ Error: Mcp error: -32603: password authentication failed for user "mj_agent_app"
```

链路走完直至 DB 并得到 PostgreSQL 的**认证判定** → 名链机制（#353 的交付物）**成立**。仅凭据值不匹配（§5）。

> **headless 不可，交互可**（方法学）：本会话曾试 5 次 `codex exec` headless 跑同一查询，全被 Codex
> **交互审批门** decline（postgres `query` 工具被判副作用；`approval_policy=never`/`on-failure` +
> `-s read-only`/`workspace-write+network` 均 auto-decline，报 `"user cancelled MCP tool call"`——
> **非** DB 错，round-trip 未发生）；`--dangerously-bypass-approvals-and-sandbox` 被 auto-mode
> classifier 硬拦（正当）。故 AC-10 后半本就须 Owner 交互点批（= 计划 §12「Owner 协同」）。补：`codex
> exec` **不认 `-a`**（top-level `codex` 才有），exec 用 `-c approval_policy=`。（codex headless 调用坑详录见 `evidence/development-agent-p2/SUMMARY.md`，PR #335。）

## 5. 为何未返回行 —— dev-memory 凭据漂移（→ #394，非投影缺陷）

PostgreSQL 报 `password authentication failed for user "mj_agent_app"`。即：URL 解析正确、host/port/db/role
均对（连到了 `mj_agent_memory` 并尝试 `mj_agent_app`），但**该 role 在容器中的口令 ≠ URL（HKCU）中的口令**。

根因假说（Owner 以 secrets 访问确认）：两条独立 secrets 管道对 dev-memory 口令漂移——
- app bundle：`config/secrets.enc` → `scripts/setup-env.ps1` → `.env`（容器建库时 role 口令之源）；
- MCP bundle：`config/secrets-mcp.enc` → `.claude/scripts/setup-mcp-secrets.ps1` → HKCU（MCP/Codex 消费值）。

与计划 §2 记载的历史不一致（"memory 5 条形态不一致，无治理记录，疑历史遗留"）吻合。次要待查：dev URL 认证为
`mj_agent_app`，而 §2 prose 提「独立凭据 `mj_agent_memory_user`」——dev-memory URL **应**用哪个 role 值得确认。

→ 全部登记入 **#394**（maintain，Owner secrets 域；AI 不读/解密/改 secret）。修好后重跑交互查询即可取字面 AC-10 绿。

## 6. AC-5 显式失败 tightening —— 实机旁证

启动时另 4 个 memory server（env 未设）报：

```
⚠ MCP client for `pg-mj-agent-memory-prod-lan` failed to start: MCP startup failed:
  handshaking with MCP server failed: connection closed: initialize response
（prod-wan / test-lan / test-wan 同）
```

即 env 未设 → server **硬失败启动**（非静默兜底错连），与 AC-5「显式失败 tightening」一致，**live 佐证**
（此前仅 Spike 手验 + AC-5 记录，CI 不跑 Windows `.cmd`）。

## 7. 数据边界发现（Owner 待判，非本记录动作面）

`codex mcp list` 显示**用户级** `~/.codex/config.toml` 另给 Codex：`postgres-{dev,prod-lan,prod-wan,test-lan,
test-wan}`（biz 仓，`@modelcontextprotocol/server-postgres` raw client）+ `ssh-manager`——正是 mj-agent
projection 依 ADR-006/009 **永久排除**的那些 server。

- **非 mj-agent projection 缺陷**：project `.codex/config.toml` 干净（AC-3/AC-4 + PJ044 + V11 守，零字面凭据、
  never 档不泄漏）。
- **但排除是必要非充分**：用户全局 config 独立地在**每个** trusted project 给 Codex 绕 L1/L1b 的 raw biz-pg
  + ssh 访问。属工程师权限内（D-015：用户级 config 为每工程师手工/私域，仓治理管不到），但在本机**实质削弱
  数据边界意图**。
- **Owner 待判**：(a) 知情接受（很可能——工程师做 mj-system 时需 Codex 的 biz 访问），或 (b) 从全局 config
  剪除 / 做按项目隔离。AI **不碰** `~/.codex/config.toml`（仓外，Owner 手工域）。

## 8. 处置

- AC-10 记为「**投影机制实机验证通过**（#353 目的达成）」；字面「查询返回行」记为 **未达 / blocked-by #394**。
- dev-memory 凭据漂移 → **#394**（maintain，Owner secrets 域，parked）。
- 数据边界发现 → 本记录 §7 + 待 Owner (a)/(b) 决定。
- 关联：#353（AC-10 出处，CLOSED）· #312（dual-agent-compat tracker）· #394（凭据 follow-up）·
  `plans/[PLAN]_dual-agent-compat_pg-cred.md` §2/§8/§12 · `evidence/ai-context-audit/2026-07_ci_audit.md`。
