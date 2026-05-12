# mj-agent secrets

本目录承载 mj-agent 运行所需的 6 个敏感变量的加密分发与解密注入：

- `POSTGRES_ANALYST_USER` / `POSTGRES_ANALYST_PASSWORD`（biz pg consumer access；mj-system 颁发的 analyst RO role）
- `ARK_API_KEY`（Volcengine Ark LLM）
- `LANGSMITH_API_KEY`（observability，可选）
- `MJ_AGENT_MEMORY_USER` / `MJ_AGENT_MEMORY_PASSWORD`（mj-agent 自家 memory pg 的 RW role；storage-stack PR 加入）

**与 mj-system 的关系**：mj-agent 是独立 compose project（[[../docs/adr/[ADR]_008_Co_Deployment_With_Upstream_Warehouse|ADR-008]]），
**不共享 mj-system 的 secrets.enc / 团队口令**。变量命名虽与 mj-system 对齐（操作一致性），
但解密管道完全独立——本 secrets.enc 由 mj-agent 团队自管。

## 文件清单

| 文件 | 状态 | 用途 |
| --- | --- | --- |
| `secrets.example` | committed | 明文 schema，列出所有应注入的密钥名（值留空） |
| `secrets.enc` | committed | AES-256-CBC + PBKDF2 加密的密钥包，由 `..\scripts\encrypt-secrets.ps1` 生成 |
| `secrets.conf` | gitignored | 解密或编辑过程中的明文中间产物，**永不提交**（`.gitignore` 已排除） |

## 获取口令

口令通过团队内部安全渠道分发，不在本仓出现、不在群聊广播、不进 issue。
新成员加入项目时向项目负责人申请。

## 开发者：从加密包恢复 .env

```powershell
.\scripts\setup-env.ps1
# 提示输入口令，脚本自动解密、合并到 .env、清理临时 secrets.conf
```

幂等：重跑会比对每个变量并以 `[SKIP]` / `[CHANGED]` / `[NEW]` 标注，
仅在差异存在时才请求覆盖确认。强制覆盖加 `-Force`。

如果脚本输出 `[DRIFT] .env.example declares N key(s) missing from your .env`，
说明 `.env.example` 在你上次生成 `.env` 之后新增了 key（典型场景：`git pull`
合并了一个引入 secret 段的 PR，如 ADR-025 PR-3 的 §8 SSH + §9 PG URL）。
按提示加 `-Force` 重跑即可，但注意 `-Force` 会从 `.env.example` 模板整体
重生 `.env`，你对非 secret key 的本地修改（如 `MJ_CONFIG_PROFILE` /
`LLM_PROVIDER`）会被重置为模板默认值——重跑后再调一次。

## 管理员：新增或轮换密钥

```powershell
# 1. 准备明文
cp config\secrets.example config\secrets.conf
# 编辑 secrets.conf 填入新值（或修改既有值）

# 2. 加密
.\scripts\encrypt-secrets.ps1
# 提示输入口令两次（一致才会写入）

# 3. 提交加密包，删除明文
git add config\secrets.enc
Remove-Item config\secrets.conf  # 切勿提交

# 4. 通过安全渠道告知团队"口令已轮换"
```

新增密钥时，需要在三处同步登记：
- `config/secrets.example` 增加键名（值留空）
- `.env.example` 增加键名（值留空，注释中写明"由 setup-env.ps1 注入"）
- `src/mj_agent/config.py` 的 `Settings` 类增加对应字段（仅当 mj-agent
  Python runtime 需要消费该值时；纯 `.mcp.json` 用的 SSH/PG URL 不要
  登记此处，避免 pydantic-settings 把它们当成 mj-agent 自己的配置）

**轮换 vs 新增 key 的团队动作差异**：
- **轮换**（key 不变，值变）：team 成员只需重跑 `.\scripts\setup-env.ps1`，
  脚本以 `[CHANGED]` 标注差异并提示覆盖。无需 `-Force`。
- **新增 key**（schema 变化）：team 成员需重跑 `.\scripts\setup-env.ps1 -Force`。
  脚本会先以 `[DRIFT]` 列出 `.env.example` 中存在但本地 `.env` 中缺失的
  key，提示用户加 `-Force` 重生模板。**通过安全渠道通知团队时务必注明
  "本次为新增 key，需 -Force 重跑"**，否则 team 成员只跑无 `-Force` 版本
  会看到 `[DRIFT]` 警告但 `.env` 不会被刷新。

## 应急：旧加密口令遗失（cold reset）

如果**所有团队成员都不记得 secrets.enc 的加密口令**（或单人开发场景下你
自己忘了），无法走常规 rotation 路径。但只要至少一台机器上的 `.env`
还在，就能 cold reset：

```powershell
# 1. 备份现有 secrets.enc（保险）
Copy-Item config\secrets.enc config\secrets.enc.bak.<date>

# 2. 从现有 .env 抽 secret 值，新建 secrets.conf
Copy-Item config\secrets.example config\secrets.conf
notepad config\secrets.conf
#    照 secrets.example schema，把以下值从你的 .env 复制粘贴进对应行：
#      POSTGRES_ANALYST_USER / POSTGRES_ANALYST_PASSWORD
#      ARK_API_KEY
#      LANGSMITH_API_KEY    (可空)
#      LLM_API_KEY          (可空)
#      MJ_AGENT_MEMORY_USER / MJ_AGENT_MEMORY_PASSWORD
#      MJ_AGENT_SSH_SERVER_*_PASSWORD ×5（你提供）
#      MJ_AGENT_PG_*_WAN_URL ×4（仅 FRP 用；可空）

# 3. 用新口令加密
.\scripts\encrypt-secrets.ps1

# 4. 验证（应能解 + 写出 .env）
.\scripts\setup-env.ps1 -Force

# 5. 清理
Remove-Item config\secrets.conf
Remove-Item config\secrets.enc.bak.<date>

# 6. 通过安全渠道通知团队"口令已轮换 + 本次为新增 key（需 -Force 重跑）"
```

**前提条件**：至少一台机器有可用 `.env`。如果连 `.env` 也丢失，需要从
源头重新拿到 7-12 个值（找 mj-system DBA 拿 analyst 凭据 / Ark 控制台
拿 API key / 对应主机管理员拿 5 SSH 密码 / etc.）后再走步骤 2-6。

## Memory pg role rename：`mj_agent_memory` → `mj_agent_app`（dev-only 一次性）

> 历史记录：本仓初版 RW role 名 = `mj_agent_memory`（与 DB 同名）；后改名
> `mj_agent_app` 以提升业务可读性 + 与 `analyst`（biz RO）配对工整。
> **DB 名 `mj_agent_memory` 保持不变 — 仅 ROLE 改名**。

**Invariant**：DEV / TEST / PROD **三环境共用同一 ROLE name `mj_agent_app`**。
单一 env var `MJ_AGENT_MEMORY_USER`（无 `_DEV`/`_TEST`/`_PROD` 后缀变体），
secrets.enc 内 `MJ_AGENT_MEMORY_USER=mj_agent_app` 一行覆盖所有 env 的 .env。

**rename 时迁移面（dev-only 部署 → 极简）**：

| 已部署的容器 | 动作 |
|---|---|
| 本地 mj-agent-postgres 容器（如已跑过） | `docker compose --env-file .env -f infra/docker/docker-compose.mj-agent.yml -f infra/docker/docker-compose.override.yml down -v` 销毁卷；`up -d` 触发 init script 用新 role 重建。**checkpointer history 全丢**（dev 可接受）。 |
| TEST / PROD 部署 | 不存在（mj-agent 未部署 TEST/PROD）；将来部署时 init script 直接用新 role 创建，无迁移负担。 |

**已部署 prod 的备选**（将来若需要在已运行环境改名而不丢数据）：
```sql
-- 在 mj-agent-postgres 的 super-user 会话中：
ALTER ROLE mj_agent_memory RENAME TO mj_agent_app;
-- pg ALTER ROLE 自动迁移所有 GRANTs；连接池会断 5-10s（applications 重连）
```

## Memory pg password rotation（dev / TEST / PROD 操作流程）

`infra/docker/postgres-init/01-bootstrap-mj-agent-memory.sh` 只在 volume
**首次创建**（data dir 空）由 postgres 镜像调用；后续 `.env` 中
`MJ_AGENT_MEMORY_PASSWORD` 改变后 **不会自动同步**到已存在的 role —— 会出现
`password authentication failed for user "mj_agent_app"` (PoolTimeout)。

> 历史背景：本 §由 Issue #136 引入；触发场景 = PR #137 Stage 8 verify 暴露
> 当前 dev volume 内 role 留旧 password。Init script 自 #136 起已加
> `CREATE OR ALTER ROLE` 模式（脚本 DO 块带 ELSE 分支），volume **重建**
> 时新 password 会被吸收；但 **已存在的** volume 仍需以下操作之一同步。

按场景选：

### 场景 A: dev — 保留 langgraph 数据（推荐）

不丢 checkpointer 数据，无停机。

```powershell
# 从 .env 读 password，用 stdin pipe 注入避免 shell history 留痕
$pwd = (Get-Content .env | Select-String '^MJ_AGENT_MEMORY_PASSWORD=' -Raw) `
       -replace '^MJ_AGENT_MEMORY_PASSWORD=',''
docker exec -i mj-agent-postgres `
    psql -U postgres -c "ALTER ROLE mj_agent_app WITH LOGIN PASSWORD '$pwd';"
# 期望: ALTER ROLE

# 验
docker exec mj-agent mj-agent check
# 期望: ✅ DB OK + ✅ Ark LLM OK
```

### 场景 B: dev / test — 可以全清（**Level C 破坏性**）

丢 langgraph checkpoint 数据；用于 dev / test 环境快速重置。

```powershell
docker compose --env-file .env -f infra/docker/docker-compose.mj-agent.yml `
               -f infra/docker/docker-compose.override.yml down -v
docker compose --env-file .env -f infra/docker/docker-compose.mj-agent.yml `
               -f infra/docker/docker-compose.override.yml up -d
# 重启时 volume 重建，init script 跑新 password（含 #136 后的 CREATE OR ALTER 改造）
```

### 场景 C: prod — 不能丢数据 + 高可用约束

不能跑 down -v；用场景 A 的 ALTER ROLE 命令。跑前先验证 `.env` password
与 `secrets.enc` 解密一致（避免再次漂移）。如有备份/还原计划，参 ADR-008
storage stack 双隔离约束 + 各环境 backup 策略文档。

### 场景 D: password 字符集安全（#144 起 init script 已无字符集约束）

历史背景：早期（#144 之前）`infra/docker/postgres-init/01-bootstrap-mj-agent-memory.sh`
用 `<<-EOSQL` heredoc（**unquoted** delimiter），bash 对 SQL body 跑
parameter / command / arithmetic substitution。如果 `MJ_AGENT_MEMORY_PASSWORD`
含 `$word` / `` `cmd` `` / `$(cmd)` 等 shell metachar，bash 二次解析会**破坏**
password 字面量（"command not found" → 空串/截断），导致 fresh-volume `up -d`
后 pg role 持有的 password ≠ app 读到的 raw env value → 永久 auth fail。

**Issue #144 起本脚本已改为 quoted heredoc `<<-'EOSQL'` + psql `\getenv` 直读
进程 env + `:'var'` / `:"var"` 引用 + server-side `format('%I %L', ...)` 处理
DDL**，完全 bypass shell expansion；任意字符的 password（含 `$` / backtick /
括号 / 单引号 / 空格）均可正确 round-trip 到 pg role。

因此 **现行版本不再有 password 字符集约束**，可在团队 `secrets.enc` 中
使用任意强 password。

诊断提示：若 `mj-agent-postgres` 启动 log 同时出现 `command not found` 与
`password authentication failed`，先确认 init script 版本 ≥ #144 修复
（在容器内或 host 上 `grep '\\getenv mem_user' infra/docker/postgres-init/01-bootstrap-mj-agent-memory.sh` 应命中）；命中仍报错请走场景 A 手动同步并 file follow-up。

## 与 mj-system 的口令独立

mj-agent 的 `secrets.enc` 与 mj-system 的同名文件**故意采用不同口令**，
契合 ADR-006 数据边界隔离精神：mj-system 口令泄漏时 mj-agent 的
`analyst` 凭据与 Ark API key 仍受保护。mj-agent 与 mj-system 同时部署
在一台开发机时，分别在各自仓库运行 `setup-env.ps1` 即可——两个
解密管道**完全独立**，这是刻意设计而非缺陷。

## §6 Multi-environment + multi-LLM-provider（ADR-025）

ADR-025 (PR-1/2/3/4 multi-env+DGX+MCP bundle) 引入 4-file docker-compose
分层 + LLM provider 抽象 + .mcp.json 13 servers，对 secret 管理影响：

### 6.1 LLM provider 分支

`LLM_PROVIDER` 决定 secret 必填项：

| Provider | 必填 secret | 备注 |
|---|---|---|
| `ark`（默认） | `ARK_API_KEY` | 现有 Ark + DeepSeek V3；既有流程不变 |
| `local-openai-compat` | `LLM_BASE_URL`（必）+ `LLM_API_KEY`（可选；vLLM 启用 `--api-key` 时填） | DGX-Spark 192.168.0.189 vLLM/SGLang/Ollama 消费侧；LLM serving 部署责任另议 |

`secrets.example` §2b 已加 `LLM_API_KEY` 占位（可选，vLLM 启用 auth 时启用）。

### 6.2 SSH passwords for ssh-manager MCP（独立命名空间）

`.mcp.json` 中的 `ssh-manager` 9 SSH targets 用 5 个独立 password env vars
驱动（cloud + 4 hosts × 2 lan/wan；同一 host 的 lan/wan 共享 password）：

```
MJ_AGENT_SSH_SERVER_CLOUD_PASSWORD
MJ_AGENT_SSH_SERVER_RUNNER_PASSWORD
MJ_AGENT_SSH_SERVER_TEST_PASSWORD
MJ_AGENT_SSH_SERVER_PROD_PASSWORD
MJ_AGENT_SSH_SERVER_DGX_PASSWORD
```

**`MJ_AGENT_*` 命名空间独立 from mj-system 的 `MJ_SYS_*`** per ADR-008
secrets pipeline isolation。即使两 .env 共存于一台开发机，secret 不互相
污染；mj-system SSH 凭据更换不影响 mj-agent，反之亦然。

### 6.3 .mcp.json postgres URL overrides（可选）

`.mcp.json` 中的 10 个 `pg-mj-{agent-memory,system-biz}-{dev,test-lan,test-wan,
prod-lan,prod-wan}` 默认值带 `REPLACE_WITH_TEAM_*_PASSWORD` 占位字面量；
LAN URLs 由 `MJ_AGENT_PG_*_URL` env vars override，WAN URLs（FRP-tunneled
remote pg）必填 `MJ_AGENT_PG_*_WAN_URL` 否则 MCP server 启动失败。

详见 `docs/infrastructure/mcp/[STANDARD]_MJ_Agent_MCP_Server_Governance.md` §5。

### 6.4 Claude Code MCP env sync（mj-ops 风格 OS-level 注入）

Claude Code 的 `.mcp.json` 变量替换（`${MJ_AGENT_SSH_SERVER_*_PASSWORD}` /
`${MJ_AGENT_PG_*_WAN_URL}` 等 9-16 个）在 claude.exe 启动时一次性 evaluate
当时的 process env。Claude Code 本身**不会**自动加载 `.env` 文件，所以仅有
`.env` 不够 —— 必须让 claude 进程能从 process env 读到这些 secrets，否则
`/doctor` 会列出 `Missing environment variables` 告警 + ssh-manager 和 4 个
WAN postgres MCP server 拉不起来。

本仓采用 **mj-system mj-ops 风格的 User-level OS env 注入** 方案（mirror
`D:\...\mj-system\develop\.claude\scripts\setup-sys-ops-env.ps1` 的 §6.2
Reload 模式架构 + Read-EnvFile / Format-MaskedValue helpers，但**不**
新建平行加密管道 —— 复用现有 `secrets.enc → .env` 单一管道）。

#### 工作流

```
secrets.enc -[scripts/setup-env.ps1]-> .env
           -[.claude/scripts/setup-mcp-env.ps1]-> User OS env
           -[docker compose env_file]-> mj-agent container
           -[pydantic-settings]-> Python runtime
```

`.env` 仍是 canonical secrets file（docker stack + Python 服务必需）；新脚本
只是把 `.mcp.json` 引用的子集额外 mirror 到 OS env 层供 claude code 消费。

#### 用法

```powershell
# 首次（或每次 secrets 轮转 / 首次 clone 后）：
.\scripts\setup-env.ps1                       # 解密 secrets.enc → .env
.\.claude\scripts\setup-mcp-env.ps1           # .env → User OS env
# 重启 terminal / IDE / claude

# 强制覆盖既有 User env vars 不交互问：
.\.claude\scripts\setup-mcp-env.ps1 -Force

# 诊断模式（不写入，只检查 .mcp.json 引用的 var 当前 OS env 状态）：
.\.claude\scripts\setup-mcp-env.ps1 -Reload
```

`-Reload` 在调试 "wrapper 跑了为什么 /doctor 仍报缺失" 时救命：
- 显示 SET 但 /doctor 报 MISSING → 问题在 claude 启动入口（IDE 缓存了旧 env）
- 显示 MISSING → 问题在 `.env` / `setup-env.ps1` / `secrets.conf`（某个 key 没生成进 .env）

#### 验证

| 编号 | 命令 | 期望 |
|---|---|---|
| V1 | `.\.claude\scripts\setup-mcp-env.ps1 -Reload`（首次 sync 前）| `0 / N set, N missing`；N ≈ 16（`.mcp.json` 中 `${VAR}` 引用数）|
| V2 | `.\.claude\scripts\setup-mcp-env.ps1`（默认）| `M wrote, 0 skipped, K absent in .env`；提示 `Restart terminal / IDE` |
| V3 | 关闭终端 → 重开 → 同 V1 | `M / N set, K missing`；K=0 表示完整 |
| V4 | 重启 claude code → `/doctor` | 0 个 `Missing environment variables` 告警 |

> **Windows env 同步坑（terminal-stale）**：Windows User-level env vars **仅对新启动的进程**可见。同一 PS terminal 里跑 V2 后立即跑 `claude`，子 claude 继承父 PS 的 stale env，会出现「`-Reload` 显示 `M/N set` 但 `/doctor` 仍报 missing」。两条解：(a) **完全关闭** PS terminal 进程（不只 `/exit`；要红 X 关窗口或 `exit` 退 shell；用 Windows Terminal 时需杀掉整个 wt.exe，因为 WT app 本身也是 stale）→ 从 Start menu 开新 PS → cd worktree → `claude`；(b) 在当前 PS 跑 hot-reload one-liner 不重启：
>
> ```powershell
> foreach ($k in (Get-Item HKCU:\Environment).Property) {
>     [Environment]::SetEnvironmentVariable($k, [Environment]::GetEnvironmentVariable($k, 'User'), 'Process')
> }
> ```
>
> 然后同 PS 跑 `claude` 即可。注意：claude `/doctor` 的 `Missing environment variables` 检查仅判 var key 存在与否，不判 value 是否非空 —— 即使 `secrets.conf` §6 某 WAN URL 是空字符串，OS env 写入空 string 后 var 仍"存在"，/doctor 不报；但 MCP server 实际尝试连接时会因空 URL 失败（runtime issue，非 /doctor 级）。

#### 安全代价（已知 trade-off）

- **HKCU\Environment 明文持久化**：5 SSH passwords + 10 PG URLs（含密码）
  以明文存于注册表 `HKEY_CURRENT_USER\Environment`
- **跨进程可见**：本机任何进程可 `Get-EnvironmentVariable('User')` 读到
- **跨 worktree 共享**：所有 mj-agent worktrees 共享同一组 OS env vars；
  最后一次 `setup-mcp-env.ps1` 决定全局值。实践中 `.env` 应在 worktrees
  之间保持一致（同一组 secrets.enc）—— 如不同则 OS env 反映最后 sync 的版本
- **编辑 `.env` 后必须重跑 sync 脚本**：不像 wrapper 自动跟随，OS-level
  持久化的固有 trade-off

接受这些代价的换取：**任何 shell（PS / cmd / Git Bash）/ IDE / VS Code 启动
claude 都自动可见**，无 wrapper / 无 alias / 无 PowerShell profile entry。

#### 与 mj-system mj-ops 的差异

| 维度 | mj-system `setup-sys-ops-env.ps1` | mj-agent `setup-mcp-env.ps1` |
|---|---|---|
| Secret 源 | 直接解密 `secrets-sys-ops.enc` | 读已解密的 `.env`（由 `setup-env.ps1` 生成）|
| 是否写 `.env` | 否（避免与主 .env 冲突）| 是（docker / Python 必需，复用现有管道）|
| Expected 列表来源 | `secrets-sys-ops.example` 静态列表 | `.mcp.json` `${VAR}` 引用 auto-derive（`Read-McpVarRefs` 函数）|
| Reload 模式 | 同 | 同（直接 port）|
| Helper 函数 | `Format-MaskedValue` / `Read-EnvFile` / `Read-ExampleKeys` | 前两个直接 port；后者改为 `Read-McpVarRefs` regex 抽 `.mcp.json`|

详见 `docs/infrastructure/mcp/[STANDARD]_MJ_Agent_MCP_Server_Governance.md` §5
（governance）以及借用源 `D:\workspace\10-software-project\projects\mj-system\develop\.claude\scripts\setup-sys-ops-env.ps1`（L74-97 helpers + L119-149 -Reload mode）。
