---
type: capability-runbook
capability: infrastructure.docker-compose
state: drafting
version: 0.2
owner: ranzuozhou
created: 2026-05-20
updated: 2026-06-07
last_verified: 2026-05-20
---

# Runbook: Docker Compose 4-File Profile

> Phase M1 baseline. **M6 X3** absorbed `docs/runbook/dev_deployment.md` (DEV
> deploy prereqs + image build, V1–V9 verification matrix, Chainlit/proxy
> troubleshooting). The source runbook's Phase-1-trial scaffolding (analyst
> trial-loop handoff, out-of-scope notes, changelog) was intentionally dropped;
> 3-level teardown is cross-referenced (§6.1 + `/mj-agent-infra-env-teardown`),
> not duplicated.

## §1 Startup

### Pre-requisites

- mj-system stack up (provides `mj-system-backend-network`)
- `.env` populated at repo root via `setup-env.ps1` (decrypts `config/secrets.enc`)
- `setup-mcp-secrets.ps1` ran once (per ADR-030; injects MCP secrets to OS env)
- docker engine ≥ 20.10 (compose v2)

### Per-profile commands

```bash
# DEV (local; builds image)
docker compose --env-file .env \
  -f docker/compose.yaml \
  -f docker/compose.override.yml up -d

# TEST (192.168.0.179; pulls Harbor image)
docker compose --env-file .env \
  -f docker/compose.yaml \
  -f docker/compose.test.yml up -d

# PROD (192.168.0.106; pulls Harbor image)
docker compose --env-file .env \
  -f docker/compose.yaml \
  -f docker/compose.prod.yml up -d
```

**REQ-001 enforcement**：every invocation MUST include both `--env-file .env` AND the explicit `-f base -f overlay` chain. Forgetting either causes silent regression.

Use the `/mj-agent-infra-docker-compose` skill for guided lifecycle.

### DEV first-deploy: image build + Chainlit access

> Absorbed from `dev_deployment.md` (M6 X3). DEV **builds** the image locally;
> TEST/PROD **pull** the Harbor image (see Per-profile commands above).

DEV host ports must be free before `up`:

| Port | Service | Check (Windows) |
|---|---|---|
| host **8001** → 8000 | mj-agent Chainlit 内网入口 | `netstat -ano \| findstr :8001` empty |
| host **5433** → 5432 | mj-agent-postgres | `netstat -ano \| findstr :5433` empty |
| host **6379** | mj-agent-redis | `netstat -ano \| findstr :6379` empty |

```bash
# 1. Build the DEV image (~780MB; TEST/PROD skip — they pull Harbor)
docker build -f docker/Dockerfile -t mj-agent:0.1 .

# 2. Prepare .env — 6 app keys: first 4 injected by setup-env.ps1, last 2 are
#    .env.example DEV defaults (copy as-is):
#      POSTGRES_ANALYST_USER / POSTGRES_ANALYST_PASSWORD   <- team secret
#      ARK_API_KEY                                          <- team secret
#      LANGSMITH_API_KEY                                    <- team secret
#      MJ_AGENT_MEMORY_USER=mj_agent_app                    <- .env.example default
#      MJ_AGENT_MEMORY_PASSWORD=local-dev-only-...          <- DEV placeholder OK
cp .env.example .env && .\scripts\setup-env.ps1

# 3. up (DEV chain) — also pulls mj-agent-postgres + mj-agent-redis (depends_on
#    service_healthy); first up runs the pg init script to create the
#    mj_agent_memory DB + role + GRANT
docker compose --env-file .env -f docker/compose.yaml -f docker/compose.override.yml up -d

# 4. 内网入口验证
docker exec mj-agent mj-agent check     # expect: CHECK OK + 5-line summary
# browser: http://<DEV-host-ip>:8001     # expect: Chainlit "Welcome"
```

## §2 Health Check

```bash
# Service status
docker compose --env-file .env -f docker/compose.yaml -f docker/compose.<overlay>.yml ps

# Expected after ≤ 90s (REQ-002):
# - mj-agent        Up (healthy)
# - mj-agent-postgres   Up (healthy)
# - mj-agent-redis  Up (healthy)

# Logs
docker compose <chain> logs -f mj-agent
docker compose <chain> logs -f mj-agent-postgres

# Healthcheck output
docker inspect --format='{{.State.Health.Status}}' mj-agent
```

### DEV deployment verification matrix (V1–V9)

> Absorbed from `dev_deployment.md` §3 (M6 X3). DEV deployment is complete when every row is green.

| ID | 验证 | 命令 / 操作 | 期望 |
|----|------|-------------|------|
| V1 | 3 容器 healthy | `docker ps --filter name=mj-agent --format "{{.Names}}: {{.Status}}"` | mj-agent / -postgres / -redis 全 `healthy` |
| V2 | biz DB 可达 | `docker exec mj-agent mj-agent check` | `CHECK OK` |
| V3 | memory DB 可达 | 同 V2，输出含 `memory db = mj_agent_memory` | OK |
| V3b | mj-agent-postgres 直连 | `psql -h localhost -p 5433 -U postgres -d mj_agent_memory -c '\dt'` | 列出 langgraph checkpoint 表（checkpoints / checkpoint_writes / checkpoint_blobs / checkpoint_migrations）|
| V3c | redis 可 ping | `docker exec mj-agent-redis redis-cli ping` | `PONG` |
| V4 | Chainlit 监听 | `docker logs mj-agent \| grep "available at"` | `http://0.0.0.0:8000` |
| V5 | 内网访问 | 浏览器 `http://<DEV-IP>:8001` | Chainlit Welcome |
| V6 | 最小问答 | Chainlit 输入"biz 域有哪些表？" | list_biz_tables → 65+ 表 |
| V7 | 数据边界 | 输入"select * from biz_ods.foo" | L1 guardrail 友好拒绝 |
| V8 | LangSmith trace | V6 后看 LangSmith mj-agent-dev project | 新 trace 含 4 工具调用 |
| V9 | 容器内存 | `docker stats mj-agent mj-agent-postgres mj-agent-redis` | 三容器合 < 1GB（无大查询时）|

## §3 Troubleshooting

### Symptom: `password authentication failed for user "mj_agent_app"`

**Diagnostic**：likely `--env-file .env` was forgotten in compose invocation → CLI substitution fell back to sentinel default `local-dev-only-replace-in-prod` → postgres init baked sentinel into volume → real `.env` password mismatches.

**Resolution**：

```bash
# Tear down + delete volume + restart with --env-file
docker compose <chain> down -v
docker compose --env-file .env <chain> up -d
```

Use `/mj-agent-infra-env-teardown` skill for 3-level safety teardown (Level 2 = down -v). Teardown 只拆 mj-agent / mj-agent-postgres / mj-agent-redis 3 容器 + `mj-agent-storage` 内部网络；`mj-system-postgres` / `-app` / `-n8n` 不受影响（`mj-system-backend-network` 是 external，归 mj-system，per ADR-008）。

### Symptom: `mj-agent` service stuck in "Created" or restarting

**Diagnostic**：`mj-agent` is waiting on `depends_on: service_healthy` for postgres or redis. Check healthcheck status:

```bash
docker inspect --format='{{json .State.Health}}' mj-agent-postgres
docker inspect --format='{{json .State.Health}}' mj-agent-redis
```

**Resolution**：

- If postgres healthcheck failing → check init script logs: `docker logs mj-agent-postgres | grep -i error`
- If init script complains about password mangling → see Symptom "Postgres password with `$` / backticks fails"
- If redis healthcheck failing → check auth config: `MJ_AGENT_REDIS_PASSWORD` set vs unset

### Symptom: `Error: network mj-system-backend-network declared as external, but could not be found`

**Diagnostic**：mj-system stack is not up. mj-agent depends on the external network created by mj-system.

**Resolution**：

```bash
# Verify network presence
docker network ls | grep mj-system-backend-network

# If absent: bring up mj-system stack first (per upstream mj-system runbook)
# OR: temporarily declare a placeholder network (DEV only; do NOT do in TEST/PROD)
```

### Symptom: Postgres password with `$`, backticks, or quotes fails init

**Diagnostic**：REQ-003 contract violation; should NOT happen with current shell-safe init pattern. If it does → regression.

**Resolution**：

- Verify init script is current: `cat docker/postgres-init/01-bootstrap-mj-agent-memory.sh | grep -E "<<-'EOSQL'|\\\\getenv|\\\\gexec"`
- Should see all 3 patterns. If any missing → file `[BUG]` against this capability with init script SHA
- Workaround: temporarily change password to ASCII-only; restart stack; investigate

### Symptom: Production deployment timeout / extreme slow start

**Diagnostic**：PROD has tighter resource limits (4C/12G). If initial load > limit → start_period stretches.

**Resolution**：

- Check resource usage: `docker stats mj-agent --no-stream`
- If CPU sustained near limit → consider raising PROD resource limit (HITL — prod compose modification per `policies/docker-runtime.md`)

### Symptom: `image: 8.135.38.175/mj-agent/mj-agent:0.1` pull failure

**Diagnostic**：TEST/PROD pull Harbor image. CI publishes after PR merge; if registry unreachable from host:

**Resolution**：

- Verify Harbor reachability: `curl -I https://8.135.38.175`
- If unreachable: VPN required for Harbor access from PROD host
- Build locally (DEV pattern) as emergency fallback (not recommended for PROD — bypass CI image signing)

### Symptom: Chainlit 502 / connection refused (DEV 内网入口)

> Absorbed from `dev_deployment.md` §4 (M6 X3). First triage container-internal vs host-side:

```bash
docker exec mj-agent python -c "import urllib.request as r; print(r.urlopen('http://127.0.0.1:8000/').status)"
```

**Diagnostic**：
- Returns `200` → app healthy inside the container; the fault is host-side (proxy) → see the proxy row below.
- Raises / hangs → process not up or bound wrong. `CHAINLIT_HOST` must be `0.0.0.0`, not `127.0.0.1` — the Dockerfile sets this default; if a `.env` override forces `127.0.0.1`, remove it.

**Resolution / DEV runtime quick-reference**：

| 现象 | 根因 | 处置 |
|---|---|---|
| 容器启动 30s 后 unhealthy | `docker logs mj-agent` 常见 `ARK_API_KEY not set` / `POSTGRES_ANALYST_USER not set`（compose env 注入缺失）| 重跑 `setup-env.ps1`；`docker compose --env-file .env <chain> up -d --force-recreate mj-agent` |
| host curl 502 但浏览器 / 容器内 urllib 200 | host shell `HTTP_PROXY`/`HTTPS_PROXY`/`ALL_PROXY`（Clash/v2ray）未排除 localhost；curl 走代理返 502，浏览器有 implicit localhost bypass | 单次 `curl --noproxy '*' http://localhost:8001/`；持久 `$env:NO_PROXY="localhost,127.0.0.1,::1"`（PS）/ `export NO_PROXY=localhost,127.0.0.1,::1`（bash）；应用本身健康，无需 restart |
| `mj-agent check` 报 memory DB unreachable | mj-agent-postgres 未 healthy 或凭据错 | `docker logs mj-agent-postgres` 看 init；若改过 `MJ_AGENT_MEMORY_*` 但 volume 持久旧值 → §6.2 init recovery（`down -v` 丢 checkpoint 历史）|
| 容器内走 5432 而 host 走 5433 的端口困惑 | 正常：容器内 `mj-agent-postgres:5432`；host 经 ports 映射走 5433 | 文档写清即可，不动配置 |
| 跑 SQL 触发 `statement_timeout` | 单查询 > 60s（L4 `analyst` role GRANT 强制；非 compose 问题）| 拆分查询 / 加 `LIMIT` |
| LangSmith trace 看不到 | `.env` 中 `LANGSMITH_TRACING=false` | 改 `true` + 验 `LANGSMITH_API_KEY` 非空；`docker compose --env-file .env <chain> restart mj-agent` |

## §4 Related Artifacts

- `contracts/docker.contract.yml` — Dockerfile lint + entrypoint contract
- `contracts/compose.contract.yml` — 4-file layering + healthcheck + env injection
- `contracts/runtime.expected.yaml` — expected post-up state
- `contracts/behavior.feature` — 3 Gherkin scenarios
- `/mj-agent-infra-docker-compose` skill — lifecycle (up / config / down)
- `/mj-agent-infra-storage-stack` skill — postgres + redis specifics
- `/mj-agent-infra-env-setup` skill — first-time setup (decrypt + compose up)
- `/mj-agent-infra-env-teardown` skill — 3-level safety teardown
- ADR-026 / ADR-008 / ADR-030 — design records
- ADR-006 (4-layer data boundary) / ADR-009 (read-only biz connection) — data-access design (absorbed from dev_deployment 关联文档, M6 X3)
- `docker/README.md` — image build / standalone run / compose detail
- `docs/runbook/dev_studio_walkthrough.md` — broader Studio context (Phase M5 dissolves)
- `§6.1 Volume Backup/Restore SOP` — cross-ref `/mj-agent-infra-env-teardown` Level 2 (destructive; REQ-006 checkpointer data lost warning)
- `§6.2 Postgres Init Failure Recovery SOP` — cross-ref `docker/postgres-init/01-bootstrap-mj-agent-memory.sh` (REQ-003 `\getenv` + `format` + `\gexec` chain)

## §5 Post-mortem Trigger

Escalate to `evidence/postmortems/` when:

- REQ-001 silent regression (operator forgets `--env-file .env` in CI → prod pwd mismatch)
- REQ-002 pg_isready regression sneaks in via Dependabot update → cascade failures
- REQ-003 secret accidentally baked into image (visible in `docker history mj-agent`)
- Network: `mj-system-backend-network` accidentally removed → all mj-agent biz queries fail

Path: `evidence/postmortems/<YYYY-MM-DD>_<incident-slug>.md` per `policies/archive.md` retention class permanent.

## §6 Standard Operating Procedures (SOPs)

> Procedural SOPs for 2 docker-compose operational scenarios beyond §3 reactive troubleshooting.
> Each SOP per B-1 §6 precedent (Trigger / Pre-conditions / Steps / Verify / Rollback);
> Path δ reduced scope (2 sub-sections vs B-1/B-2 3) per outline +15-25 budget.

### §6.1 Volume Backup/Restore SOP

**Trigger**: Routine backup before Level 3 teardown OR restore after data corruption / §6.2 init failure recovery.

**Pre-conditions**: **⚠️ Volume restore REMOVES existing checkpointer data permanently** (REQ-006 LangGraph state lost); HITL approval required; backup snapshot pre-exist required.

**Steps**:
1. Backup (pre-teardown): `docker compose <chain> exec mj-agent-postgres pg_dumpall -U postgres > /backups/mj-agent-postgres-$(date +%Y-%m-%d).dump`
2. **[DESTRUCTIVE]** Teardown (Level 2 per `/mj-agent-infra-env-teardown` SKILL): `docker compose --env-file .env <chain> down -v`
3. Restart with fresh volume (init script auto-runs): `docker compose --env-file .env <chain> up -d`
4. Restore snapshot (if recovering): `cat /backups/mj-agent-postgres-<date>.dump | docker compose <chain> exec -T mj-agent-postgres psql -U postgres`

**Verify**: `docker compose <chain> exec mj-agent-postgres psql -U postgres -d mj_agent_memory -c "\dt"` shows expected LangGraph checkpoint tables.

**Rollback**: Re-restore from earlier dump file; if none → checkpointer state lost (LangGraph restart from scratch acceptable per REQ-006 design tolerance).

### §6.2 Postgres Init Failure Recovery SOP

**Trigger**: Init script `01-bootstrap-mj-agent-memory.sh` failed (symptoms in §3: password auth failed / mj-agent stuck Created / healthcheck failing); cannot recover via Symptom block resolutions alone.

**Pre-conditions**: **⚠️ Recovery requires `down -v` (Level 2 teardown) — REMOVES checkpointer data**; HITL approval required; root-cause first via §3 symptoms.

**Steps** (per init script `\getenv` + `format('%I %L', user, password)` + `\gexec` design):
1. Identify failure: `docker logs mj-agent-postgres | grep -E "(error|CREATE ROLE|CREATE DATABASE)"`
2. Verify `--env-file .env` per REQ-001 + env integrity: `docker compose <chain> config | grep MJ_AGENT_MEMORY`
3. **[DESTRUCTIVE]** Teardown with volume removal (only path to re-trigger init): `docker compose --env-file .env <chain> down -v`
4. Restart — init auto-runs; REQ-003 `\getenv` chain handles shell metacharacters unmangled: `docker compose --env-file .env <chain> up -d`
5. Wait healthy — REQ-002 `psql -U postgres -d mj_agent_memory -tc 'SELECT 1'` must pass before mj-agent starts.

**Verify**: `docker inspect --format='{{.State.Health.Status}}' mj-agent-postgres` returns `healthy`; mj-agent transitions Created → Up (healthy).

**Rollback**: If init still fails post-cleanup → escalate to §5 Post-mortem Trigger (REQ-003 contract violation); file `[BUG]` with init script SHA + env diff evidence.

---

## §7 Unautomated Scenario Justifications (M-FU#7)

> Per `sdd/adapters/bdd-tdd.md` L121 + L160 + L161 (G21+G22 share runbook
> justification source per R-15-1 resolution); BDD scenarios that are not yet
> automated must include 4-field justification (原因 / 替代验证手段 / 升级触发
> 条件 / 预计时间).

### G22/G21 Justification: DEV profile loads with explicit -f chain + --env-file

- **REQ**: REQ-001 / **Risk**: high / **Adapter**: docker-container / **ADR-026**
- **原因**: M1 baseline + ADR-026 4-file profile pattern 已落（base + override
  + test + prod）；BDD 层 docker compose loading verification 推迟 M3
  (docker-bdd-scenario-check per gates.md L51 + V5 sub-flags
  M3-FU-V5-SUBFLAGS)。
- **替代验证手段**: V5 docker contracts validator 自动验
  `docker/compose.yaml` 结构 + DEV/TEST/PROD overlay
  链 (BLOCKING per Stage C C-a 2P/4W/0F clean)；CLAUDE.md § Commands 已
  document DEV/TEST/PROD profile up 命令（含 `-f base -f override
  --env-file` 显式 chain — compose 在子目录 + `-f` 显式 base 时 auto-load
  override.yml 不生效是 quirk，必显式 `-f` 双链）；DEV up manual smoke 验证
  已建立 SOP（per §1 Startup）。
- **升级触发条件**: M3 pytest-bdd step defs + docker compose loading test
  harness（验 `-f base -f override --env-file` chain 加载成功 + 缺 --env-file
  时 `${VAR}` 落回 default sentinel 的 quirk 行为）。
- **预计时间**: M3 EOL（per V5 sub-flags + TBD-M3 markers）。

### G22/G21 Justification: Postgres healthcheck rejects half-initialized DB

- **REQ**: REQ-002 / **Risk**: high / **Adapter**: docker-container
- **原因**: M1 baseline；BDD 层 docker healthcheck 时序验证推迟 M3。
- **替代验证手段**: postgres healthcheck 配置已落在
  `docker/compose.yaml` (`pg_isready` 探针) + init
  script `postgres-init/01-bootstrap-mj-agent-memory.sh` 已实装（storage-stack
  PR 后 auto-creates memory DB on container init）；DEV up 时 healthcheck
  实际生效，manual 验 init script 未完成则探针失败（mj-agent 容器 depends_on
  `service_healthy` 会阻塞启动）。
- **升级触发条件**: M3 pytest-bdd step defs + docker test harness（健康检查
  timing 验证；模拟 init script 中途失败 / 慢启动场景验 healthcheck 正确阻
  mj-agent 启动）。
- **预计时间**: M3 EOL（per TBD-M3 markers）。

### G22/G21 Justification: Postgres init handles password with shell metacharacters unmangled

- **REQ**: REQ-003 / **Risk**: high / **Adapter**: docker-container / **ADR-030**
- **原因**: M1 baseline + ADR-030 secrets pipeline 已落（2-bundle trust-
  boundary split: 应用 bundle `config/secrets.enc` + MCP bundle
  `config/secrets-mcp.enc`）；BDD 层 shell-safety 验证推迟 M3。
- **替代验证手段**: `scripts/setup-env.ps1` + entrypoint shell-safety pattern
  已实装（passwords 经 setup script AES-256-CBC 解密 + 注入 `.env` 时正确
  quote 避免 shell metachar 解释；postgres init script 读 env 时保留原值）；
  manual 验证 with metacharacter-containing test passwords（含 `$/&/;/!`
  等）DEV up 成功。当前无 automated BDD coverage。
- **升级触发条件**: M3 pytest-bdd step defs + secret rotation test harness
  （验 metacharacter passwords 经 setup-env.ps1 → .env → docker env → init
  script 全 round-trip 不被 mangled）。
- **预计时间**: M3 EOL（per ADR-030 + TBD-M3 markers）。

---

> Phase M1 baseline. ADR-026 + ADR-008 + ADR-030 governance.
