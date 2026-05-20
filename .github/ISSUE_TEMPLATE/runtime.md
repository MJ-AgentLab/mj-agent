---
name: Runtime
about: ★ NEW — 运行时 / 部署 / Studio / 监控相关；触及 infrastructure capability
title: "[RUNTIME] <one-line summary>"
labels: ["type:runtime"]
assignees: []
---

> Phase M0 skeleton template — 完整字段在 Phase M2 内容填充.

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

## HITL Trigger Check

- [ ] 触及 prod compose（`docker/compose.prod.yml`）？
- [ ] 触及 healthcheck 配置（影响生产可观测）？
- [ ] 触及 external network（`mj-system-backend-network`）？
- [ ] 触发 LLM endpoint 健康问题（用 `/mj-agent-infra-llm-endpoint-probe`）？

---

> *Phase M0 skeleton — Phase M2 起按 runtime 场景细化字段.*
