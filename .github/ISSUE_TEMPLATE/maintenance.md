---
name: Maintenance
about: CI/CD / Docker / deps / scripts / 配置；走 maintain/ branch
title: "[Maintain] <one-line summary>"
labels: ["maintain"]
assignees: []
---

## TL;DR

<一句话：要维护什么基础设施 / 工具链？>

## Scope

- CI 配置（`.github/workflows/`）
- Docker（Dockerfile / compose）
- Dependencies（`pyproject.toml` / `uv.lock`）
- Scripts（`scripts/` / `scripts/sdd/` / `scripts/mcp/`）
- Tooling（mypy / ruff / pytest 配置）
- Codex project config（`.codex/hooks.json` / `.dockerignore` / hooks / `.codex/config.toml`）

## Capability 影响

- 不影响业务 capability（纯基础设施）
- 影响 `infrastructure/docker-compose` capability
- 影响 `infrastructure/mcp-server-governance` capability
- ...

## Acceptance Criteria

- [ ] AC-1 <可验证陈述>
- [ ] AC-2 <可验证陈述>

> 每条 AC 须落到一种验证手段（pytest / ruff / mypy / `mj-agent check` / Studio 探针 /
> `scripts/**` 校验脚本 / 文档 grep）。写不出验证手段的 AC 应回 Stage 0 重新拆解，而不是照写。

## HITL Trigger Check

- [ ] CI blocking gate 启用 / 关闭？（必 HITL）
- [ ] `.codex/hooks.json` 原生 hook/rules 保护边界修改？
- [ ] `.codex/config.toml` 新增 server？（A14 PR gate 触发）
- [ ] `pyproject.toml` 升级主版本（LangChain / LangGraph / pydantic）？
- [ ] Dockerfile 外部镜像引用是否改变供应链信任来源？来源变化由 Owner 决定；既定来源内 tag/digest 维护在授权内自主执行并提供构建与供应链证据。内部 stage 引用不在外部镜像面。
- [ ] `compose.prod.yml` 修改？（生产红线）
- [ ] Dockerfile 其余行 / dev compose 修改？在授权内自主维护，独立核验按风险覆盖工程/供应链视角，不固定真人或人数。
- [ ] secrets pipeline 修改（`config/secrets*.enc` / `setup-*.ps1`）？

## Verification Plan

```bash
# 维护变更后必跑
uv sync
uv run mypy src/mj_agent
uv run ruff check
uv run pytest tests/unit
```
