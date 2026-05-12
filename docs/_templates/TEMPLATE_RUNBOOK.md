---
type: runbook
domain: SYS
summary: 20-60 字摘要，一句话说这份 RUNBOOK 解决什么运维场景、何时触发、是否含回滚
tags:
  - runbook
aliases: []
created: YYYY-MM-DD
updated: YYYY-MM-DD
state: draft
version: v0.1
track: code
owner: 项目负责人
last-verified: YYYY-MM-DD
---

# <RUNBOOK 标题：动作型短句，如"手动重置 mj-agent-postgres 容器"或"切换 LLM provider 到备用"</RUNBOOK 标题>

> **适用范围**：本 RUNBOOK 处理的具体故障 / 操作场景
> **目标受众**：oncall 工程师 / 运维 / 项目负责人
> **版本**：v0.1
> **最后更新**：YYYY-MM-DD
> **关联文档**：相关 ADR / SPEC / GUIDE 的 wikilink

---

## TL;DR

- **触发场景**：1-2 句话，何时打开这份 RUNBOOK
- **预计耗时**：~N 分钟
- **是否需要 HITL**：是 / 否（涉及生产数据 / 删除文件 / 修改 secret 时为是）
- **是否可回滚**：是 / 否 / 部分可回滚

---

## §1 Trigger（触发条件）

明确列出**什么情况下**应该执行本 RUNBOOK。

应包含：

- 监控告警特征（如有：哪个 dashboard 哪个指标）
- 用户 / oncall 报告的现象（如何从用户描述映射到本场景）
- 与相邻 RUNBOOK 的边界（"如果 X 现象，去 RUNBOOK Y 而不是本份"）

不应包含：

- 推测性触发条件（"可能在...时也适用"）
- 含糊的 catch-all 描述

---

## §2 Pre-checks（前置检查）

执行 Steps 前必须验证的状态、权限、备份：

| # | 检查项 | 命令或方式 | 期望结果 | 失败时 |
|---|---|---|---|---|
| 1 | （如：mj-agent-postgres 容器是否健康） | `docker ps \| grep mj-agent-postgres` | running 状态 | 跳到 §5 Rollback |
| 2 | （如：当前用户是否有 sudo / docker 权限） | `docker info` | 返回成功 | HITL 升权 |
| 3 | （如：备份是否存在） | `ls /var/lib/mj-agent-backup/...` | 文件存在 | HITL 暂停，先做备份 |

如有任一 pre-check 失败，**不要继续 §3 Steps**——按"失败时"列指引处理。

---

## §3 Steps（执行步骤）

按顺序执行；每步给出**可复制粘贴的命令**和**期望输出特征**。

### Step 1: <动作描述>

```bash
# 命令
command-1 --arg
```

**期望输出**：（描述输出特征 / 状态码）

**异常处理**：（如 Step 1 失败，跳到 Step N 或 Rollback）

### Step 2: <动作描述>

```bash
command-2
```

...

### Step N: 验证完成

```bash
# 验证命令
verify-command
```

**期望**：（具体验证状态）

---

## §4 Verification（验证）

完成 §3 后必须做的事后验证：

- 跑相关测试 / 健康检查 / smoke probe
- 监控指标恢复 / 告警自动 close
- 业务侧确认 / 用户感知验证

mj-agent 常用验证命令（按 RUNBOOK 范围适当选择）：

| 命令 | 验证点 |
|---|---|
| `uv run mj-agent check` | DB + LLM creds 健康 |
| `uv run langgraph dev` | Studio 可起；LangGraph runtime 正常 |
| `uv run pytest tests/integration` | 集成测试（需 live biz DB） |
| `docker compose -f infra/docker/docker-compose.mj-agent.yml ps` | mj-agent compose 容器状态 |

---

## §5 Rollback（回滚）

> **何时回滚**：§3 中任何 step 失败、§4 验证不通过、或 oncall 判断需要立即回滚。

```bash
# 回滚命令组
rollback-command-1
rollback-command-2
```

回滚后必须验证：

- 系统状态回到 §1 Trigger 之前的状态
- 没有遗留的临时文件 / 锁 / 半完成的事务

---

## §6 Post-mortem trigger（事后复盘判定）

执行完本 RUNBOOK 后，**按以下规则**判断是否需要建 POSTMORTEM：

| 触发条件 | 是否建 POSTMORTEM |
|---|---|
| 故障导致生产事故 / 数据错误 / P1 / P2 级影响 | **必建**（`docs/postmortem/[POSTMORTEM]_*.md`） |
| 故障恢复时长超出预期（>预计耗时 ×2） | **建议建**（轻量版） |
| 故障由本 RUNBOOK 之外原因触发 | **不必建**（更新触发条件即可） |
| 流程 / 命令需要修订 | **不必建**，回到本 RUNBOOK 编辑 |

详见 [[../rule/[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework|Code_Side]] §3.5 POSTMORTEM Authoring。

---

## 关联文档

- [[wikilink-related-1|描述]]
- [[wikilink-related-2|描述]]

## 更新记录

| 日期 | 版本 | 变更 |
| --- | --- | --- |
| YYYY-MM-DD | v0.1 | 初稿 |
