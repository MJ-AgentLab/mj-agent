---
name: mj-agent-infra-env-teardown
description: "适用于 mj-agent 的明确重置/销毁dev资源。输入：context/host/project/profile/-f、精确volume/image、level、备份。流程：profile→资源清单→level→损失+批准→执行→逐项verify。输出：level目标逐项完成；残留和不可恢复数据诚实报告。Use when：准备清理dev两个已确认volume的Level2方案。Do not use for：只停Studio，保留数据；建议app-stop，不进入volume清理。授权：Level2/3硬批准；prod单独停；外部网络/他人资源禁止；聊天批准不自动解锁 hook。独立调用完成后结束，委派返回调用者；不自动跨阶段、提交或发布外部消息。"
---


# mj-agent Infra — Env Teardown

## 本技能的执行约定

执行前读取 [共用执行边界](../../references/execution-boundaries.md)。独立调用只完成本技能；委派时记录调用者与返回阶段，同阶段必要校验完成后返回。下游 Handoff 均为建议，不能自动跨阶段或发布。受保护动作先完成可审阅草案；Owner 批准与宿主执行能力分开，hook 硬阻断时返回 `BLOCKED_EXECUTION_ROUTE`。


## 触发与职责详述

This skill provides 3-level Docker environment cleanup for the mj-agent independent compose project (3 services — mj-agent / mj-agent-postgres / mj-agent-redis; per ADR-008 standalone pattern + ADR-026 4-file layering). Profile-aware Step 0 picks which `-f` chain to teardown (dev `-f base -f override` / test `-f base -f test` / prod `-f base -f prod`). Three levels with safety confirmation: Level 1 `down` (containers + networks; volumes preserved → langgraph checkpointer data safe), Level 2 `down -v` (also wipes mj-agent-postgres-data + mj-agent-redis-data volumes — **all checkpointer + redis data lost permanently**), Level 3 `down -v --rmi local --remove-orphans` (also wipes locally-built images including mj-agent:0.1 → next `up` requires full rebuild ~3-5 minutes; Harbor-pulled test/prod images stay). Mirror of mj-system mj-sys-ops-env-teardown adapted to mj-agent's 3-service stack and 4-profile layering. Use this skill whenever the user says "停止 mj-agent compose", "清理 mj-agent 环境", "重置 mj-agent", "docker compose down", "mj-agent teardown", "拆 mj-agent 栈", "mj-agent compose down", "mj-agent 清空", "释放 mj-agent 资源", "重置 langgraph checkpointer 数据", "清掉 mj-agent volumes", "重新构建 mj-agent 镜像", or after compose-related troubleshooting wants a clean slate. Do not use for: env setup + secret 配置 (use mj-agent-infra-env-setup); Studio probe (use mj-agent-infra-studio-probe); LLM endpoint probe (use mj-agent-infra-llm-endpoint-probe); compose lifecycle up/ps/logs (use mj-agent-infra-docker-compose); a plain non-destructive stop of the running app runtime — host `langgraph dev` / `serve` processes or Level-1 `down` with all data preserved (use mj-agent-infra-app-stop; this teardown skill is for destructive Level 2/3 volume/image wipe + clean-slate reset); storage stack internals like postgres init script / redis schema (use mj-agent-infra-storage-stack); modifying compose files structure (that is C-flavor infra change; use mj-agent-flow-implement); mj-system biz pg lifecycle (out of mj-agent governance — owned by mj-system stack).


## Overview

3-level Docker 清理 skill — 与 `mj-agent-infra-env-setup` / `mj-agent-infra-docker-compose` 互补。**Stage 17 sub** of the 17-stage 执行闭环（post-merge / 工作完结清理）；也可作为 **Stage 8 sub C-flavor**（mid-task 清理重来）。

mj-agent 3 服务栈：

| Service | 容器 | 数据风险（Level 2 删 volume）|
|---|---|---|
| `mj-agent` | mj-agent | 无（无 volume）|
| `mj-agent-postgres` | mj-agent-postgres | **langgraph checkpointer 全丢**（mj-agent-postgres-data volume）|
| `mj-agent-redis` | mj-agent-redis | redis appendonly 全丢（mj-agent-redis-data volume）|

PR-1 / ADR-026 4-file 分层意味着 teardown 命令必须**与 `up` 用同样的 `-f` 链**（compose 通过 name + -f 计算服务集合）。

## When to Use

**MUST run when**：
- 用户说 "停 mj-agent / down / 清理 / 重置 mj-agent stack"
- 完工后释放本地 Docker 资源
- compose 故障想 clean slate 重来
- Dockerfile 改了要全重建（Level 3）

**MAY skip when**：
- 仅 stop 单个 container（用 `docker stop <name>`，不走本 skill 全栈）
- 缺 .env 时仅停止依赖配置的动作；仍核对已知 project 的容器、volume 和镜像，不据此断言无需清理

**MUST NOT use for**：
- ❌ env / secrets 配置 → mj-agent-infra-env-setup
- ❌ Studio probe → mj-agent-infra-studio-probe
- ❌ LLM endpoint probe → mj-agent-infra-llm-endpoint-probe
- ❌ compose lifecycle up/ps/logs → mj-agent-infra-docker-compose
- ❌ postgres init / redis schema → mj-agent-infra-storage-stack
- ❌ 修改 compose 文件结构 → mj-agent-flow-implement
- ❌ mj-system biz pg 操作（lifecycle 归 mj-system；ADR-008 边界）

## Workflow

### Step 0 — Profile selection（PR-1 / ADR-026 4-file 分层）

询问 user 当前要 teardown 哪个 profile（必须与之前 `up` 用的 -f 链一致）：

| Profile | -f 链 | 适用 |
|---|---|---|
| **dev** | `-f compose.yaml -f compose.override.yml` | 本地开发机 |
| **test** | `-f compose.yaml -f compose.test.yml` | 192.168.0.179 |
| **prod** | `-f compose.yaml -f compose.prod.yml` | 192.168.0.106 |

`-f` 链不一致会导致 compose 找不到服务集合 → 报错或部分清理。

### Step 1 — Check Current Status

**Why**: 先 verify 是否真有运行容器和 volume，避免空操作。

```powershell
# 状态（用 Step 0 选的 -f 链）
docker compose --env-file .env -f docker/compose.yaml `
               -f docker/compose.<profile>.yml ps `
               --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

# Volumes（mj-agent 命名空间）
docker volume ls --filter name=mj-agent
```

**[H1] 早退**：目标清单中无容器（含已停止）、无 volume，且 Level 3 无待清本地镜像 → "环境已干净，无需清理"，结束。

### Step 2 — Choose Cleanup Level

**[H2] 向 Owner 询问** 让 user 选 1/2/3：

| Level | 名称 | 命令 | 销毁 | 保留 | 恢复成本 |
|---|---|---|---|---|---|
| 1 | 停止服务 | `down` | 容器、网络 | volumes（langgraph checkpointer + redis 数据）+ 镜像 | `up -d` 秒起 |
| 2 | 清除数据 | `down -v` | 容器、网络、**mj-agent-postgres-data + mj-agent-redis-data volumes** | 镜像 | `up -d` 触发 postgres-init script 重建 mj_agent_memory DB + role；checkpointer history **全丢** |
| 3 | 彻底重置 | `down -v --rmi local --remove-orphans` | 容器、网络、volumes、**本地构建的 mj-agent 镜像**（dev profile：`mj-agent:0.1`）| Harbor-pulled 镜像（test/prod profile） | `up -d --build` 重建本地镜像（~3-5 分钟）+ Step 2 后续 |

**[H3] Hard Confirm（Level 2/3 only）** 向 Owner 询问 二次确认明确丢失项：

- **Level 2 文案**："将删除 `mj-agent-postgres-data` + `mj-agent-redis-data` volumes，**所有 langgraph checkpointer 历史 + redis appendonly 数据将永久丢失**。继续？"
- **Level 3 文案**："将删除所有 volumes + **本地构建的 `mj-agent:0.1` 镜像**。下次 `up` 需 `--build` 重建（~3-5 分钟）。Harbor-pulled 镜像（test/prod profile）不受影响。继续？"

> Level 1 无需二次确认 — 容器停止后数据安全保留在 volumes。

### Step 3 — Execute & Verify

执行 Step 2 选定命令（用 Step 0 的 -f 链），然后：

```powershell
# 所有 Level：确认无容器
docker compose --env-file .env -f docker/compose.yaml `
               -f docker/compose.<profile>.yml ps

# Level 2/3：确认 volumes 已清
docker volume ls --filter name=mj-agent
# 期望：空（或仅有 docker network 的隐式 volume，无 mj-agent-*-data）

# Level 3：确认本地镜像已删
docker images | grep "^mj-agent\s"
# 期望：空（mj-agent:0.1 已删；Harbor 镜像 8.135.38.175/mj-agent/mj-agent:0.1 仍可能在）
```

## §HITL 介入场景

| ID | 类型 | 触发条件 | 行为 |
|----|------|---------|------|
| **H1** | Info | 环境已干净 | 提示无需清理，结束 |
| **H2** | Choice | Step 2 开始 | 向 Owner 询问 选 Level 1/2/3 |
| **H3** | Hard Confirm | Level 2 / 3 | 二次确认明示丢失项 |

> H3 是保护性阻断 — Level 2 删 langgraph checkpointer 数据是不可逆操作。

## §Troubleshooting

| 症状 | 可能原因 | 修复 |
|---|---|---|
| `network mj-system-backend-network: removing` 警告 | 该 external network 由 mj-system 拥有；mj-agent down 不应 remove | 忽略警告（compose 会自动跳过 external network；ADR-008 边界） |
| Level 2 后再 up 报 `password authentication failed for user mj_agent_app` | postgres-init script 用 .env 当前的 `MJ_AGENT_MEMORY_PASSWORD` 重建 role；如 .env 中此密码与之前不一致，会出错 | 检查 `.env` 的 `MJ_AGENT_MEMORY_PASSWORD` 与 user 期望一致；或重跑 `mj-agent-infra-env-setup` 重新注入 secrets |
| Level 3 后 `up` 报 `pull access denied for 8.135.38.175/mj-agent/mj-agent` | test/prod profile 用 Harbor 镜像；本地未 docker login | `docker login 8.135.38.175` 后 retry |
| `down` hang 在 mj-agent stop | mj-agent healthcheck 进程未优雅退出 | 超时后记录实际 project/container/PID 身份及状态，交 Owner 决定；不自动强杀 |

## What This Skill DOES NOT DO

- ❌ 不替代 `mj-agent-infra-env-setup`（env / secret 配置）
- ❌ 不替代 `mj-agent-infra-docker-compose`（up/ps/logs lifecycle；本 skill 仅 down/clean）
- ❌ 不删 mj-system 的 mj-postgres / mj-system-backend-network（external 资源；归 mj-system）
- ❌ 不强制 Level 3（除非 user 明确选；默认建议从 Level 1 开始）
- ❌ 不带 user 重新 `up`（Handoff 提示去 `mj-agent-infra-docker-compose`）

## Sub-skill / Tool Calls

| Tool | 用途 |
|---|---|
| shell `docker compose ps / down [-v] [--rmi local]` | Step 1/3 lifecycle |
| shell `docker volume ls / images` | Step 1/3 verify |
| 向 Owner 询问 | H2 level 选择 + H3 hard confirm |

## Reference Files

- `repo:decisions/ADR-008_Co_Deployment_With_Upstream_Warehouse.md`（独立 compose project；mj-agent down 不影响 mj-system）
- `repo:decisions/ADR-026_Multi_Environment_Compose_Profile.md`（4-file profile 分层；teardown 必须与 up 用相同 -f 链）
- `repo:docker/compose.yaml` / `.override.yml` / `.test.yml` / `.prod.yml`
- `repo:sdd/workflows/execution-loop.md` §7（Stage 17 post-merge cleanup）+ `repo:policies/ai-agent.md` §4（破坏性操作必触 HITL）；原 HITL_Prompt §3.1 / §4.15，M6 PR4 archived → kernel

## Anti-patterns

- ❌ 不在没确认 user 意图时跑 `down -v`（必 H3）
- ❌ 不忘记 Step 0 profile 选择（错 -f 链 = 部分清理或报错）
- ❌ 不用 `docker compose down` 单 -f 链（会与 up 时的 -f 链不匹配；compose 通过 name + -f 计算服务集合）
- ❌ 不主动建议 Level 3 除非 user 明确说 "Dockerfile 改了" / "全清重建"（recovery 成本最高）
- ❌ 不删 `mj-system-backend-network`（external；归 mj-system；compose 会自动跳过但要告知 user）

## Handoff

按执行的 Level 输出：

- **Level 1**："服务已停。volumes 保留 → `docker compose -f ... -f ... up -d` 秒起。"
- **Level 2**："服务停 + volumes 清。下次 up 触发 postgres-init 重建 role + DB；checkpointer 历史已不可恢复。重新搭建：`mj-agent-infra-env-setup` → `mj-agent-infra-docker-compose` up。"
- **Level 3**："环境彻底重置。下次 up 需 `--build`（dev profile）；Harbor 镜像（test/prod）需 `docker login` + pull。重新搭建：`mj-agent-infra-env-setup` → `mj-agent-infra-docker-compose` up --build。"
