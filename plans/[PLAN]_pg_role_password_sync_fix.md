---
type: plan
summary: 修 infra/docker/postgres-init/01-bootstrap-mj-agent-memory.sh idempotency (CREATE OR ALTER ROLE 模式) + config/README.md 加 password rotation operator workflow + dev env 用 ALTER USER 立即修复 PR #137 Stage 8 暴露的 mj_agent_app password mismatch
owner: ranzuozhou
created: 2026-05-11
updated: 2026-05-11
completed: 2026-05-11
state: completed
track: code
---

# [PLAN] mj-agent-postgres init script idempotency + password rotation workflow

> 单 PR bugfix：修 init script DO 块缺少 ALTER ROLE 分支（"idempotent for existence, not for state"）+ docs 补 password rotation operator workflow + apply ALTER USER 在 dev env 立即修复 mj-agent check fail。改动 ≤ 40 LOC，2 files。

## 1. Linked Artifacts

- Issue: [#136](https://github.com/MJ-AgentLab/mj-agent/issues/136) `[Bugfix] mj-agent-postgres volume stale credentials for mj_agent_app`
- 上游触发: PR #137 (`fix(infra): pin python:3.13-slim + uv only-system for runtime venv`) Stage 8 verify 暴露
- Pre-existing source: commit `c91ed81 infra: rename memory pg role mj_agent_memory -> mj_agent_app`（doc anchor: `config/README.md` "Memory pg role rename" 段）
- Stage 3 Repo Scan: Plan needs update — (b)+(c) bundle + (b) 当前 dev env apply

## 2. Context

PR #137 Stage 8 verify mj-agent container 不再 crash（venv 修复成功），但 `mj-agent check` 内部 langgraph AsyncPostgresSaver 连 mj-agent-postgres 失败：

```
psycopg.OperationalError: password authentication failed for user "mj_agent_app"
psycopg_pool.PoolTimeout: couldn't get a connection after 30.00 sec
```

**Stage 3 Repo Scan 揭示精确根因**：

- `mj-agent-postgres` 容器内 role `mj_agent_app` 已存在（名字正确，per `\du`）
- database `mj_agent_memory` 已存在，owner = mj_agent_app
- 失败 = **password mismatch**（NOT user 名错；NOT db 缺）
- `infra/docker/postgres-init/01-bootstrap-mj-agent-memory.sh` DO 块只 `CREATE ROLE IF NOT EXISTS`，**缺 ELSE ALTER ROLE password 同步**
- postgres 镜像 `/docker-entrypoint-initdb.d/` 只在 volume 空时跑，已存在 volume 整个 skip

事件序列推测：c91ed81 role rename 完成后，team password rotation / secrets pipeline 解密生成新 password 写入 `.env`；volume 留旧 password；app 连接 reject。

**期望产出**：

1. Init script 永久解决 password drift（CREATE OR ALTER 模式）
2. config/README.md 补 password rotation operator workflow
3. 当前 dev env apply ALTER USER 立即修 mj-agent check（不动 volume 保留 langgraph 数据）

## 3. Scope

### 3.1 Init script idempotency 修复（风味 C infra）

- 含：
  - `infra/docker/postgres-init/01-bootstrap-mj-agent-memory.sh` DO 块改造：role 存在时跑 `ALTER ROLE ... WITH LOGIN PASSWORD '...'`；不存在时仍走 `CREATE ROLE`
  - 同时修正 script 头部 "Idempotent: ... no-op if the object already exists" 误导注释（改为准确描述 "creates role if missing, otherwise syncs password from env"）
- 不含：
  - 不动 database 创建逻辑（已通过 `\gexec` IF NOT EXISTS 保证 idempotency）
  - 不动 GRANT 段（PG GRANT 默认 idempotent）

### 3.2 Operator workflow 文档（C 风味 docs；与 c91ed81 风格对齐）

- 含：
  - `config/README.md` 在 `## Memory pg role rename：...` 段后新加一节 "## Memory pg password rotation（dev / TEST / PROD 操作流程）"
  - 内容：解释 init script only-on-fresh-volume；后续 password 改 .env 后需要的 (b)/(a) 选项；示例 `docker exec` ALTER USER 命令
- 不含：
  - 不写完整 ops RUNBOOK（不在 docs/runbook/）；config/README.md 就近原则
  - 不改 c91ed81 现有 "Memory pg role rename" 段

### 3.3 当前 dev env 应用（Stage 10 verify 步骤，非 commit）

- Stage 10 Level B：在当前 mj-agent-postgres 跑 ALTER USER 同步 password
- 不是 commit 内容；是 verify 行动

### 3.4 严格守约（Out-of-Scope）

- 不动 `src/mj_agent/**`（checkpointer.py / config.py 等都不涉及）
- 不动 `pyproject.toml` / `uv.lock`（依赖未变）
- 不动 `infra/docker/Dockerfile`（PR #131 + #137 已落）
- 不动 `infra/docker/docker-compose.*.yml`（env vars 已对）
- 不动 `.env.example`（命名已对）
- 不动 `CLAUDE.md`（A6 gate 不触发；存储路径/命名未变）
- 不动 `docs/adr/` / `docs/runbook/`
- 不强制 down -v（保 langgraph 数据；本 PR 默认走 ALTER 路径）

## 4. HITL Gates

- **Stage 5 Gate 1（Plan 确认）**：本 plan body 审批
- **Stage 7 Gate 2（设计确认）**：SPEC inline §5.2 4-选项对比 + (b+c) 组合选择 → 与 Stage 5 一并 approve
- **Stage 9 Scope drift**：实施中越界改其他文件必停
- **Stage 10 verify HITL**：apply ALTER USER 前 user 显式确认（Level B 写 DB；密码经 stdin pipe 避免 shell history 留痕）
- **Stage 11 Self-review**：commit 前
- **Stage 13 Push gate**

## 5. Implementation (Stage 8 — C-flavor) 详解

### 5.1 实现 diff sketch（伪代码；非最终）

#### 5.1.1 `infra/docker/postgres-init/01-bootstrap-mj-agent-memory.sh`

```diff
-# Idempotent: each statement is wrapped in DO blocks that no-op if the
-# object already exists. Safe to re-run if the volume is preserved but
-# the bootstrap was previously interrupted.
+# Idempotent: creates role if missing, otherwise syncs LOGIN + PASSWORD
+# from env on each run. Safe to re-run if the bootstrap was previously
+# interrupted. Note: postgres image only invokes this script when the
+# data dir is empty (first boot); for password rotation on an existing
+# volume see `config/README.md "Memory pg password rotation"`.

 psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
-    -- Create the application role if it doesn't exist.
+    -- Create the application role, or sync its password if it exists.
     DO \$\$
     BEGIN
         IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '${MJ_AGENT_MEMORY_USER}') THEN
             CREATE ROLE "${MJ_AGENT_MEMORY_USER}" LOGIN PASSWORD '${MJ_AGENT_MEMORY_PASSWORD}';
+        ELSE
+            ALTER ROLE "${MJ_AGENT_MEMORY_USER}" WITH LOGIN PASSWORD '${MJ_AGENT_MEMORY_PASSWORD}';
         END IF;
     END
     \$\$;
```

#### 5.1.2 `config/README.md` 新增段

紧接现有 `## Memory pg role rename：mj_agent_memory → mj_agent_app（dev-only 一次性）` 段之后插入：

```markdown
## Memory pg password rotation（dev / TEST / PROD 操作流程）

`infra/docker/postgres-init/01-bootstrap-mj-agent-memory.sh` 只在 volume **首次创建**（data dir 空）由 postgres 镜像调用；后续 `.env` 中 `MJ_AGENT_MEMORY_PASSWORD` 改变后**不会自动同步** ——会出现 `password authentication failed for user "mj_agent_app"` (PoolTimeout)。

按场景选：

### 场景 A: dev — 保留 langgraph 数据

（推荐；不丢 checkpoint 数据）

```powershell
# 从 .env 读 password，用 stdin pipe 注入避免 shell history 留痕
$pwd = (Get-Content .env | Select-String '^MJ_AGENT_MEMORY_PASSWORD=' -Raw) -replace '^MJ_AGENT_MEMORY_PASSWORD=',''
docker exec -i mj-agent-postgres psql -U postgres -c "ALTER ROLE mj_agent_app WITH LOGIN PASSWORD '$pwd';"
```

### 场景 B: dev / test — 可以全清

（**Level C 破坏性**；丢 langgraph checkpoint 数据）

```powershell
docker compose -f infra/docker/docker-compose.mj-agent.yml `
               -f infra/docker/docker-compose.override.yml down -v
docker compose -f infra/docker/docker-compose.mj-agent.yml `
               -f infra/docker/docker-compose.override.yml up -d
# 重启时 volume 重建，init script 跑新 password
```

### 场景 C: prod — 不能丢数据 + 高可用约束

不能跑 down -v；用场景 A 的 ALTER ROLE 命令，但跑前先验证 .env password 与 secrets.enc 解密一致（避免再次漂移）。
```

### 5.2 设计选项权衡（inline SPEC）

| 选项 | 实现 | dev 修当下 | 永久修 future | 复杂度 |
|---|---|---|---|---|
| **(a)** down -v + up | 全清 volume | ✅ | ✅（init 跑） | Low（操作；丢数据）|
| **(b)** ALTER ROLE 命令 | docker exec ALTER | ✅ | ❌（下次 down -v 又复发） | Very Low |
| **(c)** Init script CREATE OR ALTER | DO 块加 ELSE | ❌（volume 不重跑 init） | ✅ | Low（10 LOC）|
| **(b)+(c) ⭐ 推荐** | 组合 | ✅ via (b) | ✅ via (c) | Low+VeryLow |

**选 (b)+(c)**：

- (c) 修 script 永久 idempotency — 任何未来 password rotation + 任何 fresh volume 都 sync OK
- (b) 当前 dev env 即时修 — 不动 volume，langgraph 数据保留
- docs (`config/README.md` § password rotation) 把 (a)/(b)/(c) 关系讲清，与 c91ed81 § role rename 风格对齐

### 5.3 Documentation Decision

| Type | Action | Path | Reason |
|---|---|---|---|
| Plan | Create | `plans/[PLAN]_pg_role_password_sync_fix.md` | 本文件 |
| SPEC | None (inline §5.2) | — | 改动 ≤ 40 LOC；script + docs |
| ADR | None | — | 非架构；script 内部 idempotency 修 |
| **GUIDE / README** | **Update** | `config/README.md` § password rotation | 与 c91ed81 § role rename 风格对齐；ops workflow |
| RUNBOOK / STANDARD / Local ISSUE / ASSESSMENT / INDEX | None | — | — |
| CHANGELOG | None | — | 非 user-visible runtime；infra/ops fix |

## 6. Risk

| 风险 | 等级 | 风味 | 缓解 / Rollback |
|---|---|---|---|
| ALTER ROLE password 注入 shell history 留痕 | Medium | C | docs §A 用 PowerShell `-c "...$pwd..."` + docker exec `-i` stdin pipe；plan §5.1.2 示例正确 |
| 现 dev env apply ALTER ROLE 失败 | Low | C | postgres super user 操作；error 不破坏数据；可重跑 |
| script idempotency 改后 fresh volume 行为 | Very Low | C | Stage 10b 验：`down -v` + `up -d` 后看 role + password 一致；或模拟 (idempotency 测试) |
| `WITH LOGIN PASSWORD` 字符串 escape（.env 含特殊字符）| Low | C | bash heredoc + `${...}` 展开 → 已是现状（CREATE 路径就用同样）；ALTER 路径同 escape；新增 risk = 0 |
| TEST/PROD 部署受影响 | None | — | TEST/PROD Harbor pull image；init script 改动随下次 CI build 落 image；现 TEST/PROD volume 不动 |
| docs `config/README.md` § placement / 内容偏差 | Very Low | — | §5.1.2 草稿与 c91ed81 § role rename 风格对齐；reviewer 易调 |

## 7. Verification

### 7.1 Stage 10 Level A（必跑）

```powershell
uv run ruff check
uv run mypy src/mj_agent
uv run pytest tests/unit
docker compose -f infra/docker/docker-compose.mj-agent.yml `
               -f infra/docker/docker-compose.override.yml config
uv run python scripts/check_wikilinks.py
uv run python scripts/check_frontmatter.py
```

### 7.2 Stage 10 Level B —— 当前 dev env apply (b)（HITL-confirm）

```powershell
# 1. 从 .env 读 password (host 侧；stdin pipe 避免 history 留痕)
$pwd = (Get-Content .env | Where-Object { $_ -match '^MJ_AGENT_MEMORY_PASSWORD=' }) -replace '^MJ_AGENT_MEMORY_PASSWORD=',''

# 2. ALTER ROLE
docker exec -i mj-agent-postgres psql -U postgres -c "ALTER ROLE mj_agent_app WITH LOGIN PASSWORD '$pwd';"
# 期望: ALTER ROLE

# 3. 起 mj-agent service (storage 已 Up)
docker compose -f infra/docker/docker-compose.mj-agent.yml `
               -f infra/docker/docker-compose.override.yml up -d mj-agent

# 4. 等 healthcheck (start-period 20s + probe 30s)
Start-Sleep -Seconds 60
docker compose -f infra/docker/docker-compose.mj-agent.yml `
               -f infra/docker/docker-compose.override.yml ps
# 期望: 三 service 全 healthy

# 5. 核心 AC
docker exec mj-agent mj-agent check
# 期望: ✅ DB OK + ✅ Ark LLM OK
```

### 7.3 Stage 10 Level B —— 验 (c) idempotency（轻量；非 down -v）

模拟 idempotency（不动 volume，直接在 mj-agent-postgres 里手跑两次 SQL 段）：

```powershell
$pwd = (Get-Content .env | Where-Object { $_ -match '^MJ_AGENT_MEMORY_PASSWORD=' }) -replace '^MJ_AGENT_MEMORY_PASSWORD=',''

# 第二次跑同样 DO 块 (期望: 走 ELSE ALTER 分支，无 error)
$sql = @"
DO `$`$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'mj_agent_app') THEN
        CREATE ROLE "mj_agent_app" LOGIN PASSWORD '$pwd';
    ELSE
        ALTER ROLE "mj_agent_app" WITH LOGIN PASSWORD '$pwd';
    END IF;
END
`$`$;
"@
$sql | docker exec -i mj-agent-postgres psql -U postgres
# 期望: DO (无 error)
```

如有 HITL Level C 全验需求：`down -v` + `up -d` + 看 fresh init 跑通（可在 follow-up PR 验，本 PR 不强求）。

### 7.4 Stage 11 Self-review

- §4.9 Rule 5 反扫：corpus grep `01-bootstrap-mj-agent-memory.sh` / `CREATE ROLE IF NOT EXISTS` → 仅命中文件自身 + plan body；无 stale doc
- 5b new doc / Update: `config/README.md` 新 § + plan body — check_frontmatter pass
- 5c INDEX / CLAUDE.md / CHANGELOG: 无同步需求
- 5d SPEC Delta: None（inline）

## 8. Completion Criteria（AC checklist）

- [ ] AC1: Level A 6/6 ✅（含 check_wikilinks + check_frontmatter）
- [ ] AC2: `infra/docker/postgres-init/01-bootstrap-mj-agent-memory.sh` DO 块加 ELSE ALTER ROLE 分支
- [ ] AC3: `config/README.md` 加 password rotation 段（紧接 role rename 段后）
- [ ] AC4: dev env apply ALTER USER + verify `docker exec mj-agent mj-agent check` ✅ DB OK
- [ ] AC5: 三 service `compose ... ps` 全 healthy（**本 PR 核心修复 — PR #137 deferred AC3-5 此处回填**）
- [ ] AC6: PR body 含 before/after evidence（auth fail → ALTER ROLE → check OK）
- [ ] AC7: Level B (c) idempotency 模拟测试通过（DO 块第二次跑无 error，走 ALTER 分支）
- [ ] AC8: commit `fix(infra):` per Commit Convention §4
- [ ] AC9: PR CI 全绿 + ≥1 SWE approve

## 9. 关联

- Issue: [#136](https://github.com/MJ-AgentLab/mj-agent/issues/136)
- 上游 PR: [#137](https://github.com/MJ-AgentLab/mj-agent/pull/137)（Stage 8 verify 暴露）
- Pre-existing source: commit `c91ed81 infra: rename memory pg role mj_agent_memory -> mj_agent_app`（doc anchor: `config/README.md` "Memory pg role rename" 段）
- 目标文件:
  - `infra/docker/postgres-init/01-bootstrap-mj-agent-memory.sh`（+~5 / -3 行 DO 块改造 + 注释更新）
  - `config/README.md`（+~30 行 new password rotation 段）
  - `plans/[PLAN]_pg_role_password_sync_fix.md`（本文件）
- 不动文件:
  - `src/mj_agent/**`（含 memory/checkpointer.py、config.py 等）
  - `pyproject.toml` / `uv.lock`
  - `infra/docker/Dockerfile` / `docker-compose.*.yml`
  - `.env*`（命名已对；password 解密走 setup-env.ps1 不在本 PR scope）
  - `.github/workflows/*` / `dependabot.yml`
  - `CLAUDE.md`
  - 任何 `docs/`（除非 reviewer 要求把 password rotation 升级到 `docs/runbook/`）
- 后续 follow-up（PR #131 / #137 chain 仍 pending）:
  - **[#132](https://github.com/MJ-AgentLab/mj-agent/issues/132)** apt Acquire::Retries=3
  - **[#133](https://github.com/MJ-AgentLab/mj-agent/issues/133)** CLAUDE.md:126 stale ADR-025 ref
  - **[#135](https://github.com/MJ-AgentLab/mj-agent/issues/135)** plan state mark completed (含 #131 + #137 + 本 PR 的 plan)
