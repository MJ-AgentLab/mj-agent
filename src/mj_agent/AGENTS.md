# src/mj_agent/AGENTS.md

> Codex 局部约束，与根 AGENTS.md 共同生效；规则正文仍在项目 kernel。

## The 4 mj-agent-specific hard-stop surfaces (OWNER_APPROVAL_REQUIRED)

| Canonical enum | Path | Discipline |
|---|---|---|
| `sql-guardrail-relax` | `tools/sql/{guardrail,precheck}.py` | never relax unilaterally |
| `runtime-skill-content-change` | `skills/*/SKILL.md` body | propose → Owner approves → apply |
| `prompt-version-or-body-change` | `prompts/system.md` body or `version` | propose → Owner approves → apply |
| `biz-catalog-sync` | `biz_catalog/qcm_catalog.yaml` | mirror of the upstream dictionary; sync flow only |

Codex 自守必停边界；hook 保持硬阻断，批准不自动解锁执行路线。

## Data boundary (ADR-006 / ADR-009 — never bypass)

- biz-warehouse access ONLY through the agent tool chain
  `find_biz_context → list_biz_tables → describe_biz_table → execute_sql`; read-only
  `analyst` role; no direct DB clients, no writes, no DDL (root `AGENTS.md` boundary 1).
- mj-agent's own memory PostgreSQL (checkpointer) is a separate capability — do not conflate
  it with the biz boundary.

## Loading contracts

- Runtime skills load via `load_skill()`, which strips frontmatter (gate A11,
  `sdd/adapters/runtime-skill.md`); never `open(SKILL.md).read()` directly.
- Active skill roster + count: single source of truth is `agent.py:_ACTIVE_SKILLS` — do not
  hardcode the list elsewhere.
- 4 freeze surfaces here carry `content_hash` anchors (prompt + runtime-skill contracts);
  body drift without a sanctioned re-freeze fails CI.

## Verification (AI agents, from repo root)

```bash
uv run mypy src/mj_agent          # strict — CI gate
uv run ruff check src/mj_agent
uv run --frozen --no-sync python scripts/sdd/run_offline_pytest.py tests/unit -q
```

Human/IDE direct pytest remains supported and is forced offline by
`tests/conftest.py`; Agent and CI invocations always use the hardened runner.

## See also

- Root `AGENTS.md`
- `policies/ai-agent.md` §4 (canonical 10-enum) + §7 (pre-flight verification discipline)
- `sdd/adapters/python.md` · `sdd/adapters/runtime-skill.md` · `sdd/adapters/prompt.md`

## Runtime structure

工具注册从 `tools/__init__.py:ALL_TOOLS` 读取；middleware 从 `agent.py:make_graph()` 读取，不复制易漂移名单。新增 middleware 走跨 capability workflow；只运行相关测试。V1/V3/V7 与原有 runtime freeze 不受开发客户端迁移影响。
