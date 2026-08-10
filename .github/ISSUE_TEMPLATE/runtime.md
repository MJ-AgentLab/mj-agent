---
name: Runtime
about: 运行时 / 部署 / Studio / 监控相关；触及 infrastructure capability
title: "[Runtime] <one-line summary>"
labels: ["maintain"]
assignees: []
---

## TL;DR

<一句话：运行时层面什么场景？>

## Scope

- LangGraph Studio 启动 / 调试
- Chainlit UI 部署
- Docker compose 3 profile（DEV / TEST / PROD）
- Healthcheck 异常
- LLM endpoint（ark / DGX）
- mj-agent-postgres / mj-agent-redis 状态
- 上游业务系统 biz pg 连接（mj-system-backend-network）
- LangSmith trace / Telemetry

## Capability 影响

- `infrastructure/docker-compose`
- `infrastructure/mcp-server-governance`
- `data-agent.memory-checkpointer`（Phase 2+）
- `data-agent.entry-points`（Phase 4+）

## Environment

- Profile: DEV (本地) / TEST (192.168.0.179) / PROD (192.168.0.106) / DGX (192.168.0.189 — LLM endpoint only, not deployment)
- LLM provider: ark / local-openai-compat
- mj-agent commit SHA: `<sha>`

## Acceptance Criteria

- [ ] AC-1 <可验证陈述>
- [ ] AC-2 <可验证陈述>

> 每条 AC 须落到一种验证手段（pytest / ruff / mypy / `mj-agent check` / Studio 探针 /
> `scripts/**` 校验脚本 / 文档 grep）。写不出验证手段的 AC 应回 Stage 0 重新拆解，而不是照写。

## HITL Trigger Check

- [ ] 触及 prod compose（`docker/compose.prod.yml`）？
- [ ] 触及 healthcheck 配置（影响生产可观测）？
- [ ] 触及 external network（`mj-system-backend-network`）？
- [ ] 触发 LLM endpoint 健康问题（用 `/mj-agent-infra-llm-endpoint-probe`）？
