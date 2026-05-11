---
type: plan
summary: 修 infra/docker/postgres-init/01-bootstrap-mj-agent-memory.sh heredoc password 转义 bug — 改用 quoted heredoc <<-'EOSQL' + psql \getenv + :'var'/:"var" + format('%I %L', ...) 让任意字符（含 $/backtick/括号）的 MJ_AGENT_MEMORY_PASSWORD 安全落到 postgres role；config/README.md 补 password 字符集安全注记
owner: ranzuozhou
created: 2026-05-11
updated: 2026-05-11
completed: 2026-05-11
state: completed
track: code
---

# [PLAN] postgres-init bootstrap password escaping (heredoc shell-metachar safety)

> 单 PR bugfix：把 init script 的 unquoted heredoc + bash 字符串插值改为 quoted heredoc + psql `\getenv` + 安全引用，让 password 任意字符（含 `$`/`` ` ``/`(`/`'`）都能正确写入 pg role；docs 同步注记。改动 ~30 LOC bash + ~25 LOC docs。

## 1. Linked Artifacts

- Issue: [#144](https://github.com/MJ-AgentLab/mj-agent/issues/144) `[Bugfix] postgres-init bootstrap heredoc mis-expands shell metachars in MJ_AGENT_MEMORY_PASSWORD`
- 上游触发: 本会话 `/mj-agent-infra-docker-compose` Stage 8 sub C-flavor up 运行时暴露
- 同 file 上游 fix: [PR #138](https://github.com/MJ-AgentLab/mj-agent/pull/138) (`fix(infra): pg-init CREATE OR ALTER for password sync + rotation docs`) — `plans/[PLAN]_pg_role_password_sync_fix.md` state=completed；与本 plan **互补**（PR #138 修存量场景 idempotency；本 plan 修 fresh-volume password 字符安全）
- 上游"fix N → expose N+1"链: PR #131 → #134 (venv) → #136/#138 (idempotency) → **#144 (本 plan)**
- Stage 3 Repo Scan: Plan still valid，Risk Medium，无 §3.1 4 项触发
- 相关 ADR: [[../docs/adr/[ADR]_008_Co_Deployment_With_Upstream_Warehouse|ADR-008]] (mj-agent owned storage stack 双隔离)

## 2. Context

本会话 `/mj-agent-infra-docker-compose` 触发 fresh-volume `up -d`，三 service 中 mj-agent 永远 `health: starting`，logs 反复输出：

```
FATAL: password authentication failed for user "mj_agent_app"
```

`docker logs mj-agent-postgres` 揭示 init script 首次启动时：

```
/docker-entrypoint-initdb.d/01-bootstrap-mj-agent-memory.sh: line 31: MJ_AGENT_MEMORY_PASSWORD: command not found
DO
CREATE DATABASE
GRANT
GRANT
[mj-agent-memory init] done.
```

行 31 是 `psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL`（**unquoted** `EOSQL` delimiter）→ bash 对 heredoc body 跑 parameter / command / arithmetic expansion。SQL 内的单引号 `'...'` **不**阻止 bash expansion（heredoc 语义 ≠ 双引号字符串）。

如果 `MJ_AGENT_MEMORY_PASSWORD` value 含 `` `...` `` / `$(...)` / `$word` 任一 shell metachar，bash 二次解析失败 → 替换为空串或截断值 → 落地 DB 的 password literal ≠ app 之后用 raw env value 算的 hash → 永久 auth 失败。

PR #138 的 `ELSE ALTER ROLE` 分支仍走同一 heredoc，所以 idempotent path 也带同样 bug。

**期望产出**：

1. Init script 改用 quoted heredoc + psql native variable substitution，让 password 任意字符安全
2. PR #138 idempotent CREATE OR ALTER 行为保留（fresh + existing volume 双路径均成立）
3. `config/README.md` Memory pg password rotation § 加 password 字符集安全注记 + bug 说明

## 3. Scope

### 3.1 Init script heredoc 安全化（风味 C infra）

- 含:
  - `infra/docker/postgres-init/01-bootstrap-mj-agent-memory.sh:31-57` 重写 — heredoc delimiter 改为 `<<-'EOSQL'`（quoted；禁 bash expansion）
  - SQL body 改用 psql `\getenv` 直读 env var（bypass shell）+ `:'var'` 字面量引用 + `:"var"` 标识符引用 + `format('%I %L', ...)` 处理 CREATE ROLE/DATABASE DDL（这两条 DDL 不支持参数化）
  - 保留 `: "${MJ_AGENT_MEMORY_PASSWORD:?...}"` guards（line 24-27）— 仍在 bash 层校验 env var 已设
  - 保留 `CREATE OR ALTER ROLE` idempotent 语义（PR #138 主旨）
  - 更新 script 顶部注释反映新机制（"safe for arbitrary password chars via psql \getenv"）
- 不含:
  - 修改 docker-compose.mj-agent.yml 服务定义（不需要；env vars 注入路径不变）
  - 修改 `infra/docker/postgres-init/` 目录结构 / 新增 init 脚本
  - 修改 mj-agent 应用代码（pydantic-settings 已正确读 raw env）
- 风味: **C infra**
- 验证: `bash -n script.sh` 语法 OK；`docker compose ... config` lint OK；Stage 10 Level B 复现路径 + 回归路径双跑

### 3.2 docs 同步（风味 A 纯代码，文档侧）

- 含:
  - `config/README.md` "Memory pg password rotation" § 后追加新子段 `### 场景 D: password 字符集安全`：说明 #144 bug 现象 + 简明描述（"init script 自 #144 起用 psql \getenv 安全读取；任意字符 password 均安全"）+ 不再需要手动 alter 的注脚
- 不含:
  - 替换或重写 §A/B/C 场景内容（保留 PR #138 既有 workflow）
  - 修改 `infra/docker/README.md` / `CLAUDE.md` / 其他 docs（反向 grep 无内容更新需求）
- 风味: **A 纯代码（docs 内容）**
- 验证: `python scripts/check_wikilinks.py` OK；`python scripts/check_frontmatter.py` OK（README 无 frontmatter，但脚本可识别 markdown）

### 3.3 Documentation Decision（手填，PR-B4 前）

| Type | Action | Path | Reason |
|---|---|---|---|
| Plan | Create | `plans/[PLAN]_pg_init_password_escaping.md` | 本文件 — Stage 4 not exempt |
| SPEC | None | — | Bash bugfix，无新接口契约 |
| ADR | None | — | 无新架构决策，沿用 ADR-008 |
| RUNBOOK | None | — | Operator flow 已在 config/README.md |
| GUIDE | None | — | n/a |
| STANDARD | None | — | n/a |
| Local ISSUE | None | — | GitHub #144 足够 |
| ASSESSMENT | None | — | n/a |
| CHANGELOG | None | — | 非 user-visible（dev/test/prod ops 内部） |
| INDEX | None | — | 无新 canonical doc |

Cross-update only: `config/README.md`（§3.2）

## 4. Execution Order

| Stage | 动作 | Skill | 风味 |
|---|---|---|---|
| 8a | 重写 `01-bootstrap-mj-agent-memory.sh` heredoc + psql \getenv | `/mj-agent-flow-implement` | C |
| 8b | 追加 `config/README.md` "场景 D: password 字符集安全" 子段 | `/mj-agent-flow-implement` | A |
| 10A | `bash -n` + `docker compose ... config` + ruff/mypy/pytest unit + wikilinks/frontmatter | `/mj-agent-flow-verify` Level A | — |
| 10B | Level C 复现路径（含 `$` password fresh up） + 回归路径（existing volume PR #138 alter-role） | `/mj-agent-flow-verify` Level B HITL | — |
| 11 | Self-review §4.9 5a/5b/5c/5d 反向扫描；scope-drift None expected | `/mj-agent-flow-self-review` | — |
| 12-14 | commit / push / PR | `/mj-agent-git-commit` + `/mj-agent-git-push` + `/mj-agent-git-pr` | — |
| 17 | Post-merge：mark this plan `state: completed` + close #144 + sync develop worktree | `/mj-agent-flow-post-merge` | — |

## 5. Risk

| 风险 | 等级 | 风味 | 缓解 / Rollback |
|---|---|---|---|
| psql `\getenv` 在 postgres:18-alpine 不可用 | Low | C | postgres:18-alpine 含 psql 18，`\getenv` PG14+ 已 GA；`bash -n` + 沙盒跑一次 init 验证；如不可用回退 (β) 法（`-v pw="$VAR"` + `:'pw'`） |
| psql `:'var'` 在 `format(...)` 内不被识别 | Low | C | `:'var'` 在 SQL command 层做 lexical 替换 (psql client-side)；`format()` 是 server-side function；二者层次正交，传入 `format('%L', :'pw')` 安全；如有兼容性疑问，pre-test minimal repro |
| `CREATE ROLE`/`CREATE DATABASE` 不支持 SQL 参数化 → 必须 server-side `format()` 拼 + `\gexec` | Low | C | 已采用方案；保证 PG `format()` 函数对身份符 `%I` 自动加 quote 防注入 |
| PR #138 idempotent ALTER ROLE 路径回归 | Medium | C | Stage 10 Level B 显式跑回归路径（保留 volume + 改 .env password + restart） |
| Init script 顶部注释 / 行号漂移影响下游 grep | Low | A | 反向 grep `01-bootstrap-mj-agent-memory` 10 文件中 9 个不依赖行号；script 顶部注释段同步更新 |
| docs 更新与代码不同步 | Low | A | 同 PR commit；Stage 11 self-review 拉 diff 检查 |

无 §3.1 4 项 mj-agent 专属升档触发（不动 SKILL.md body / system.md / qcm_catalog / sql guardrail）。

## 6. Verification

### 6.1 Stage 10 本地验证（Level A 只读 / 必跑）

```powershell
uv run ruff check
uv run mypy src/mj_agent
uv run pytest tests/unit
python -m compileall src
python scripts/check_wikilinks.py
python scripts/check_frontmatter.py
bash -n infra/docker/postgres-init/01-bootstrap-mj-agent-memory.sh
docker compose -f infra/docker/docker-compose.mj-agent.yml `
               -f infra/docker/docker-compose.override.yml config | Out-Null
```

期望：全部 exit 0；无 ruff/mypy warnings 新增。

### 6.2 Stage 10 Level B（HITL Level C 破坏性后跑）

**6.2.1 复现路径（fresh volume + metachar password）** — 证明 bug 修好

```powershell
# 当前 stack 已 down -v（来自本会话）；如有残留：
docker compose ... down -v

# 改 .env 临时设 metachar password（注意：仅本机；不 commit）
# MJ_AGENT_MEMORY_PASSWORD=test$pwd`abc(

docker compose -f infra/docker/docker-compose.mj-agent.yml `
               -f infra/docker/docker-compose.override.yml up -d

# 期望 30-60s 内 mj-agent 转 healthy；init log 无 "command not found"
docker compose ... ps
docker compose ... logs mj-agent-postgres | grep "command not found"  # 期望: empty
docker exec mj-agent mj-agent check  # 期望: ✅ DB OK
```

**6.2.2 回归路径（existing volume PR #138 alter-role 不破坏）**

```powershell
# 6.2.1 stack 仍 up；在 .env 改 password 到另一安全值（如 abc123-safe）
# 不 down -v；只 restart mj-agent-postgres 让它重读 env

docker compose ... restart mj-agent-postgres
# init script 不会重跑（postgres image 行为）

# 用 config/README.md §A 场景手动 ALTER ROLE 同步
$pwd = (Get-Content .env | Select-String '^MJ_AGENT_MEMORY_PASSWORD=' -Raw) `
       -replace '^MJ_AGENT_MEMORY_PASSWORD=',''
docker exec -i mj-agent-postgres `
    psql -U postgres -c "ALTER ROLE mj_agent_app WITH LOGIN PASSWORD '$pwd';"

# 期望: ALTER ROLE → mj-agent check ✅
docker compose ... restart mj-agent  # 让 healthcheck 重跑
docker exec mj-agent mj-agent check
```

**6.2.3 Clean restore**

```powershell
# 复原 .env password 到安全默认值，并 down -v 留干净状态
docker compose ... down -v
```

### 6.3 Stage 11 AI 自检 tie-in

- §4.9 Rule 5a (rename) — N/A（无重命名）
- §4.9 Rule 5b (path) — N/A（无移动）
- §4.9 Rule 5c (SQL identifier) — N/A（CREATE ROLE 名字 `mj_agent_app` 不变）
- §4.9 Rule 5d (内部行为优化) — **触发**：init script 实现机制变（外部接口/env contract 不变）→ 反向 grep `01-bootstrap-mj-agent-memory` 10 文件已确认 9 个不需更新；只更 config/README.md 一处
- mj-agent 扩展反向扫描: runtime SKILL.md / system.md / qcm_catalog — 全不涉及
- scope-drift Severity: 预期 None（PR 边界严格 = 1 bash + 1 markdown）

## 7. Completion Criteria

- [x] AC1: `01-bootstrap-mj-agent-memory.sh` 重写为 quoted heredoc + psql `\getenv` + `:'var'`/`:"var"` + `format('%I %L', ...)` for DDL
- [x] AC2: 验证手段 — ephemeral `docker run --rm postgres:18-alpine` with `MJ_AGENT_MEMORY_PASSWORD=p@ssw0rd$test(123` mounted with new init script → init log clean (无 "command not found")，role created，auth OK as `mj_agent_app` with metachar password
- [x] AC3: `docker exec mj-agent mj-agent check` 输出 `CHECK OK profile=dev biz host=mj-postgres:5432 memory db=mj_agent_memory chainlit=0.0.0.0:8000 llm provider=ark (endpoint=https://ark.cn-beijing.volces.com/api/v3)` (after #150 workaround manual ALTER ROLE)
- [x] AC4: existing volume + manual `ALTER ROLE mj_agent_app WITH LOGIN PASSWORD '...'` → mj-agent re-auths → CHECK OK；PR #138 alter-role 路径直接 cover
- [x] AC5: `config/README.md` "场景 D: password 字符集安全（#144 起 init script 已无字符集约束）" 子段已合入 develop
- [x] AC6: Stage 10 Level A 6/6 PASS (bugfix worktree) + Stage 17 在 develop 再跑 ephemeral test + compose lifecycle 通过
- [x] AC7: PR #147 merged 2026-05-11T13:26:07Z (squash commit `aa52edc8`)
- [x] AC8: post-merge — plan state updated (本 commit) + completed=2026-05-11 + #144 closed

## 8. Linked Items

- Issue: #144
- 上游 PR: #138 (idempotency；互补 fix)
- "fix N → expose N+1" 链上下文: #131 → #134 → #136/#138 → **#144**
- Repo Scan Result: 本会话 Stage 3 对话输出（无独立文件）
- 目标文件:
  - `infra/docker/postgres-init/01-bootstrap-mj-agent-memory.sh` (rewrite §31-57)
  - `config/README.md` (append 场景 D 子段)
- 不动文件（显式声明）:
  - `infra/docker/docker-compose.mj-agent.yml` / override.yml / test.yml / prod.yml
  - `src/mj_agent/**` (Python 应用代码全不涉及)
  - `src/mj_agent/skills/**` (B 风味 in-source canonical 不动；§3.1 trigger 10 不触发)
  - `src/mj_agent/prompts/system.md` (§3.1 trigger 11 不触发)
  - `src/mj_agent/biz_catalog/qcm_catalog.yaml` (§3.1 trigger 12 不触发)
  - `src/mj_agent/tools/sql/{guardrail,precheck}.py` (§3.1 trigger 13 不触发)
- 后续 follow-up issues:
  - **#150** `[Bugfix] compose env-file asymmetry: postgres gets default value while app gets .env value` (Stage 17 deferred-AC verification 暴露；同链 fix N → expose N+1 模式延续)
- 后续独立 PR: 无
