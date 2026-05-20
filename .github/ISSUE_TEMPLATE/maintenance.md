---
name: Maintenance
about: CI/CD / Docker / deps / scripts / 配置；走 maintain/ branch
title: "[MAINT] <one-line summary>"
labels: ["type:maintenance"]
assignees: []
---

> Phase M0 skeleton template — 完整字段在 Phase M2 内容填充.

## TL;DR

<一句话：要维护什么基础设施 / 工具链？>

## Scope

- CI 配置（`.github/workflows/`）
- Docker（Dockerfile / compose）
- Dependencies（`pyproject.toml` / `uv.lock`）
- Scripts（`scripts/` / `scripts/sdd/` / `.claude/scripts/`）
- Tooling（mypy / ruff / pytest 配置）
- Claude Code config（`.claude/settings.json` / `.claudeignore` / hooks / `.mcp.json`）

## Capability 影响

- 不影响业务 capability（纯基础设施）
- 影响 `infrastructure/docker-compose` capability
- 影响 `infrastructure/mcp-server-governance` capability
- ...

## HITL Trigger Check

- [ ] CI blocking gate 启用 / 关闭？（必 HITL）
- [ ] `.claude/settings.json` `permissions.deny` 红线修改？
- [ ] `.mcp.json` 新增 server？（A14 PR gate 触发）
- [ ] `pyproject.toml` 升级主版本（LangChain / LangGraph / pydantic）？
- [ ] Dockerfile / compose.prod.yml 修改？（生产红线）
- [ ] secrets pipeline 修改（`config/secrets*.enc` / `setup-*.ps1`）？

## Verification Plan

```bash
# 维护变更后必跑
uv sync
uv run mypy src/mj_agent
uv run ruff check
uv run pytest tests/unit
```

---

> *Phase M0 skeleton — Phase M2 起按 maintenance 类型细化字段.*
