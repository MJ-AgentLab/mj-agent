# docker/AGENTS.md

> Codex 局部约束，与根 AGENTS.md 共同生效；规则正文仍在项目 kernel。

## 风险与执行条件

按 `policies/docker-runtime.md` §4实际影响分类：生产策略/权限、跨仓network所有权、观测接受标准及供应链信任来源变化先Owner决定。任务内具名dev维护、兼容healthcheck修复、保持信任来源的镜像更新可自主完成，独立核验按风险覆盖工程/供应链视角，不要求真人或固定人数。

内部COPY stage不是外部镜像信任来源；构建成功不证明来源可信或prod运行通过。具名运行授权、接受基线与平台审核分别核验。

## Env & secrets carrier rule

- Agents must NOT read `.env` / `config/secrets*.enc` themselves (root `AGENTS.md`
  boundary 2). Passing `--env-file .env` to `docker compose` is the sanctioned carrier: the
  docker process parses the file; the agent never sees values.
- Compose quirk: the project directory is `docker/`, so repo-root `.env` is only picked up
  via an explicit `--env-file .env`; overlays never auto-load — always chain
  `-f docker/compose.yaml -f docker/compose.<overlay>.yml` (ADR-026).

## Destructive teardown

`down -v` (and `--rmi`) destroys mj-agent-postgres / mj-agent-redis volumes — 独立列明具名对象、损失、必要备份及恢复条件后才能执行Level2/3；已有相同授权复用。

## Verification (either tool, from repo root)

```bash
docker compose --env-file .env -f docker/compose.yaml -f docker/compose.override.yml config
uv run python scripts/sdd/check_docker_contracts.py --all --bdd --tdd --compose-config
```

## See also

- Root `AGENTS.md`
- `sdd/adapters/docker-container.md` · ADR-026 / ADR-008 (in `decisions/`)

## Runtime details

DEV/TEST/PROD 均使用 base + 具名 overlay；profile 不等于操作授权。启动前确认既有 external network。teardown L1 保留卷；L2 删卷、L3 连镜像均须具名目标确认。非 root runtime 约束保持；V5/V6 与构建 gate 以 CI 注册为准。
