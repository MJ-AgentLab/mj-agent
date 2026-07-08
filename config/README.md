# mj-agent secrets

本目录承载 mj-agent 运行所需的敏感变量的加密分发与解密注入。**自 ADR-030 起采用 2-bundle 拆分模型**（对齐 mj-system v2.3 `secrets-sys-ops.enc` 范式）：

### App bundle (config/secrets.enc) — 8 个应用层 secrets + §2c LLM provider profiles

- `POSTGRES_ANALYST_USER` / `POSTGRES_ANALYST_PASSWORD`（biz pg consumer access；mj-system 颁发的 analyst RO role）
- `ARK_API_KEY`（Volcengine Ark LLM）
- `LLM_API_KEY`（可选；`LLM_PROVIDER=local-openai-compat` 且 vLLM 启用 `--api-key` 时填）
- `LANGSMITH_API_KEY`（observability，可选）
- `MJ_AGENT_MEMORY_USER` / `MJ_AGENT_MEMORY_PASSWORD`（mj-agent 自家 memory pg 的 RW role；storage-stack PR 加入）
- `MJ_AGENT_PG_SUPERUSER_PASSWORD`（compose-only；mj-agent-postgres 容器超管，postgres-init + healthcheck 用；#297 加入）
- **§2c LLM provider profiles**（非密钥持久层；#297）：`LLM_PROFILE_DEFAULT` +
  `LLM_PROFILE_{ARK,DGX}__{LLM_PROVIDER,LLM_BASE_URL,LLM_MODEL_ID,NO_PROXY}` 两套，
  生成 `.env` 时由 `setup-env.ps1 -LlmProfile <ark|dgx>` 解析出**一套**落到 plain 键——
  使 regen 不回滚 provider 切换，同时不把 DGX 机器特例强加给无隧道机器。

注入路径：`secrets.enc → scripts/setup-env.ps1 → .env`（Python runtime / docker compose 消费）。

### MCP bundle (config/secrets-mcp.enc) — 15 个基础设施层 secrets

- 5 个 `MJ_AGENT_SSH_SERVER_{CLOUD,RUNNER,TEST,PROD,DGX}_PASSWORD`（ssh-manager MCP；9 entries：cloud + 4 hosts × 2 lan/wan）
- 10 个 `MJ_AGENT_PG_{MEMORY,BIZ}_{DEV,TEST_LAN,TEST_WAN,PROD_LAN,PROD_WAN}_URL`（`.mcp.json` pg-server wrapper URL overrides）

注入路径：`secrets-mcp.enc → .claude/scripts/setup-mcp-secrets.ps1 → HKCU\Environment`（**不入 .env**；claude.exe 启动时读 OS env 解析 `.mcp.json` `${VAR}`）。

**两份 bundle 共享同一团队口令**（不为口令隔离，仅为信任边界 + 注入路径隔离）。详细决策见 [[decisions/ADR-030_Secrets_Bundle_Split_For_MCP_Isolation|ADR-030]]。

**与 mj-system 的关系**：mj-agent 是独立 compose project（[[decisions/ADR-008_Co_Deployment_With_Upstream_Warehouse|ADR-008]]），
**不共享 mj-system 的 secrets.enc / 团队口令**。变量命名虽与 mj-system 对齐（操作一致性），
但解密管道完全独立——本 secrets.enc 由 mj-agent 团队自管。

## 文件清单

| 文件 | 状态 | 用途 |
| --- | --- | --- |
| `secrets.example` | committed | App bundle 明文 schema（8 secrets + §2c LLM provider profiles） |
| `secrets.enc` | committed | App bundle AES-256-CBC + PBKDF2 加密包，由 `..\scripts\encrypt-secrets.ps1` 生成 |
| `secrets.conf` | gitignored | App bundle 解密 / 编辑过程明文中间产物，**永不提交** |
| `secrets-mcp.example` (ADR-030) | committed | MCP bundle 明文 schema（5 SSH + 10 PG URL = 15 keys） |
| `secrets-mcp.enc` (ADR-030) | committed | MCP bundle 加密包，由 `..\scripts\encrypt-secrets-mcp.ps1` 生成 |
| `secrets-mcp.conf` (ADR-030) | gitignored | MCP bundle 明文中间产物，**永不提交** |

## 获取口令

口令通过团队内部安全渠道分发，不在本仓出现、不在群聊广播、不进 issue。
新成员加入项目时向项目负责人申请。

## 开发者：从加密包恢复 .env + OS env（ADR-030 2-bundle）

新开发者首次配置 / 任何 secret 轮换后，按顺序跑 2 个脚本：

```powershell
# Step 1: App bundle -> .env (Python runtime / docker compose 消费)
.\scripts\setup-env.ps1 -LlmProfile ark      # 无 DGX 隧道的机器（新人默认）
# .\scripts\setup-env.ps1 -LlmProfile dgx    # 有 DGX 隧道 + Docker Desktop 的机器
# 提示输入口令，脚本自动解密 secrets.enc、合并到 .env、清理临时 secrets.conf
# 省略 -LlmProfile 时按 LLM_PROFILE_DEFAULT（bundle 内）或交互选择

# Step 2: MCP bundle -> OS User-level env (Claude Code 主进程消费 .mcp.json ${VAR})
.\.claude\scripts\setup-mcp-secrets.ps1
# 提示输入口令（与 Step 1 相同），脚本解密 secrets-mcp.enc 直接写 HKCU\Environment
# 不写 .env 文件！
```

**Step 2 后必须重启**：Windows User-level env 变量只对**新启动的进程**可见。重启
PowerShell 终端 + Claude Code，才能看到新 OS env 值。

幂等：两个脚本都幂等。重跑 `setup-env.ps1` 会比对每个变量并以 `[SKIP]` /
`[CHANGED]` / `[NEW]` 标注（强制覆盖加 `-Force`）；重跑 `setup-mcp-secrets.ps1`
对 OS env 同样比对（强制覆盖加 `-Force`）。

诊断模式：
```powershell
.\.claude\scripts\setup-mcp-secrets.ps1 -Reload
# 无需口令；只报当前 HKCU\Environment 与 secrets-mcp.example 的对比（SET / MISSING）
```

如果 `setup-env.ps1` 输出 `[DRIFT] .env.example declares N key(s) missing from your .env`，
说明 `.env.example` 在你上次生成 `.env` 之后新增了 key。按提示加 `-Force` 重跑即可，
但注意 `-Force` 会从 `.env.example` 模板整体重生 `.env`，你对非 secret key 的本地
修改（如 `MJ_CONFIG_PROFILE`）会被重置为模板默认值——重跑后再调一次。LLM provider
切换**不受此影响**：`LLM_PROVIDER` / `LLM_BASE_URL` / `LLM_MODEL_ID` / `NO_PROXY`
由 bundle 的 §2c profile 携带，regen 时按所选 profile 重新注入（#297）。

### LLM provider profile 选择（#297）

bundle §2c 携带 **ark / dgx 两套**命名空间键（`LLM_PROFILE_ARK__*` /
`LLM_PROFILE_DGX__*`）+ 可选 `LLM_PROFILE_DEFAULT` 标记；`setup-env.ps1`
生成 `.env` 时解析出**恰好一套**落到 plain 键，命名空间键永不落 `.env`：

- **选择优先级**：`-LlmProfile` 参数 > bundle 内 `LLM_PROFILE_DEFAULT` >
  仅一套非空则用之 > 交互提问 `[ark/dgx]`
- **空值跳过**：所选 profile 内的空值不注入（模板默认值保留）
- **向后兼容**：老 bundle 只有 plain §2c 键（无 `LLM_PROFILE_*`）→ 行为与
  #297 前完全一致；新旧混存 → profile 值胜出 + `[WARN]`
- **dgx 套机器前置**：Docker Desktop（提供 host.docker.internal）+ owner 隧道
  `ssh -L 0.0.0.0:18000:127.0.0.1:8000 <user>@192.168.0.189`（vLLM 只绑 DGX
  loopback，LAN 直连不通）；无前置的机器用 `-LlmProfile ark`

注：自 ADR-030 起 `setup-env.ps1` 的 drift 检测**仅覆盖 app keys**（`.env.example`
所声明的范围）。MCP keys 的 drift 由 `setup-mcp-secrets.ps1 -Reload` 单独负责
（对比 `secrets-mcp.example`）。

## 管理员：新增或轮换密钥

> 两个 bundle 各自独立加密 + 各自的 setup 脚本（ADR-030）。app bundle（`secrets.enc`）
> 见下；MCP bundle（`secrets-mcp.enc`）的并列流程见本节末。

### App bundle（secrets.enc）

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
  登记此处，避免 pydantic-settings 把它们当成 mj-agent 自己的配置；
  **compose-only 键同理豁免**——如 `MJ_AGENT_PG_SUPERUSER_PASSWORD` 仅被
  `docker/compose.yaml` `${...}` 替换消费，只登记前两处）

**轮换 vs 新增 key 的团队动作差异**：
- **轮换**（key 不变，值变）：team 成员只需重跑 `.\scripts\setup-env.ps1`，
  脚本以 `[CHANGED]` 标注差异并提示覆盖。无需 `-Force`。
- **新增 key**（schema 变化）：team 成员需重跑 `.\scripts\setup-env.ps1 -Force`。
  脚本会先以 `[DRIFT]` 列出 `.env.example` 中存在但本地 `.env` 中缺失的
  key，提示用户加 `-Force` 重生模板。**通过安全渠道通知团队时务必注明
  "本次为新增 key，需 -Force 重跑"**，否则 team 成员只跑无 `-Force` 版本
  会看到 `[DRIFT]` 警告但 `.env` 不会被刷新。

### MCP bundle（secrets-mcp.enc）

MCP 基础设施 secrets（5 SSH + 10 PG URL）走独立 bundle + 独立注入路径（→ `HKCU\Environment`，
不入 `.env`；详见 §6.4）。加密 / 轮换与 app bundle 并列，但键清单与目标不同：

```powershell
# 1. 准备明文
Copy-Item config\secrets-mcp.example config\secrets-mcp.conf
# 编辑 secrets-mcp.conf 填入新值（或修改既有值）

# 2. 加密（口令与 secrets.enc 相同）
.\scripts\encrypt-secrets-mcp.ps1

# 3. 提交加密包，删除明文
git add config\secrets-mcp.enc
Remove-Item config\secrets-mcp.conf  # 切勿提交

# 4. 通过安全渠道告知团队"MCP bundle 已更新"
```

新增 MCP key（如新 SSH host / 新 PG URL）时，只登记**两处**（与 app 的三处对照）：
- `config/secrets-mcp.example` 增加键名（值留空）
- `.mcp.json` 增加对应 `${VAR}` 引用（在 server config 里消费）
- **显式不登记** `.env.example` / `src/mj_agent/config.py`——ADR-030 核心红线：MCP 键永不入
  `.env`，Python runtime 不消费（误登记 config.py 会让 pydantic-settings 把它当成 app 配置）。

**团队动作差异**：无论轮换还是新增，team 成员都重跑
`.\.claude\scripts\setup-mcp-secrets.ps1`（值变加 `-Force`）**并重启 terminal / IDE / claude**
（OS User-level env 仅对新启动的进程可见——这是与 app bundle `.env` 流程的关键差异；
诊断 `.\.claude\scripts\setup-mcp-secrets.ps1 -Reload` 报 SET/MISSING）。

## 应急：旧加密口令遗失（cold reset）

如果**所有团队成员都不记得团队口令**（或单人开发场景下你自己忘了），无法走常规
rotation 路径。两个 bundle **共享同一团队口令**（ADR-030），所以口令遗失时
`secrets.enc`（app）与 `secrets-mcp.enc`（MCP）**都要用新口令重建**。前提是至少一台
机器还留着两类值的来源：**(a)** app 值 = 该机 `.env`；**(b)** MCP 值 = 该机
`HKCU\Environment`（之前跑过 `setup-mcp-secrets.ps1` 写入的 OS User-level env）。

用同一新口令依次重建两个 bundle（顺序无所谓，但两次输入的口令必须一致）。

### App bundle（secrets.enc）— 值从 `.env` 抄

```powershell
# 1. 备份现有 secrets.enc（保险）
Copy-Item config\secrets.enc config\secrets.enc.bak.<date>

# 2. 从现有 .env 抽 app secret 值，新建 secrets.conf
Copy-Item config\secrets.example config\secrets.conf
notepad config\secrets.conf
#    照 secrets.example schema，把以下值从你的 .env 复制粘贴进对应行
#    （这些就是 app bundle 的全部键——MCP 的 SSH / PG URL 不在此，见下方 MCP bundle）：
#      POSTGRES_ANALYST_USER / POSTGRES_ANALYST_PASSWORD
#      ARK_API_KEY
#      LANGSMITH_API_KEY    (可空)
#      LLM_API_KEY          (可空)
#      MJ_AGENT_MEMORY_USER / MJ_AGENT_MEMORY_PASSWORD
#      MJ_AGENT_PG_SUPERUSER_PASSWORD (可空——空则 compose 用占位 fallback)
#      §2c LLM_PROFILE_* 两套（非密钥；照 secrets.example 已提交的默认值填 ark/dgx）

# 3. 用新口令加密
.\scripts\encrypt-secrets.ps1

# 4. 验证（应能解 + 写出 .env）
.\scripts\setup-env.ps1 -Force

# 5. 清理
Remove-Item config\secrets.conf
Remove-Item config\secrets.enc.bak.<date>
```

### MCP bundle（secrets-mcp.enc）— 值从 `HKCU\Environment` 读

> ⚠ **切勿**把 MCP 的 SSH / PG URL 键填进上面的 app `secrets.conf`：它们不在
> `.env.example`，`setup-env.ps1` 会走 append 分支（`scripts/setup-env.ps1` L316）把它们
> **明文写进 `.env`**，直接违反 ADR-030「MCP secrets 永不入 .env」红线。MCP 键只走本 bundle。

```powershell
# 1. 备份现有 secrets-mcp.enc（保险）
Copy-Item config\secrets-mcp.enc config\secrets-mcp.enc.bak.<date>

# 2. 从当前 OS env dump 15 个 MCP 键的现值（-Reload 只报 SET/MISSING、屏蔽值，无法取值；
#    下面循环按 secrets-mcp.example 的键名逐个读 HKCU\Environment 当前值）：
Get-Content config\secrets-mcp.example |
  ForEach-Object { if ($_ -match '^\s*([A-Za-z0-9_]+)\s*=') {
      $k = $Matches[1]; "$k=$([Environment]::GetEnvironmentVariable($k,'User'))" } }

# 3. 新建 secrets-mcp.conf，粘贴上一步输出（空值保持空——LAN URL 有 .mcp.json fallback）
Copy-Item config\secrets-mcp.example config\secrets-mcp.conf
notepad config\secrets-mcp.conf

# 4. 用同一新口令加密（与 app bundle 口令一致）
.\scripts\encrypt-secrets-mcp.ps1

# 5. 验证（应能解 + 写 OS env）：提示新口令，期望 "15 processed"
.\.claude\scripts\setup-mcp-secrets.ps1

# 6. 清理
Remove-Item config\secrets-mcp.conf
Remove-Item config\secrets-mcp.enc.bak.<date>
```

### 收尾

通过安全渠道通知团队「团队口令已轮换」。两 bundle 的值未变、只换了口令，team 成员
用新口令重跑对应 setup 脚本即可（值一致，多为 `[SKIP]`）：
- **App**：`.\scripts\setup-env.ps1`。
- **MCP**：`.\.claude\scripts\setup-mcp-secrets.ps1` + **重启 terminal / IDE / claude**
  （OS User-level env 仅对新启动的进程可见）。

**前提条件**：cold reset 两个 bundle 各需一个可用来源——
- **App bundle**：至少一台机器有可用 `.env`。若连 `.env` 也丢，从源头重拿 **5-8 个** app 值
  （找 mj-system DBA 拿 analyst 凭据 / Ark 控制台拿 API key / memory pg RW 凭据 / etc.）。
- **MCP bundle**：至少一台机器 `HKCU\Environment` 仍持有 MCP 值。若连 OS env 也丢，从源头重拿
  **5 个 SSH 密码**（对应主机管理员）+ **4 个 FRP WAN URL**（隧道 / FRP 配置）；6 个 LAN URL
  有 `.mcp.json` 占位 fallback，可空。

补齐来源后，各按对应 bundle 的加密流程执行（填 conf → encrypt → 验证 → 清理）。

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
| 本地 mj-agent-postgres 容器（如已跑过） | `docker compose --env-file .env -f docker/compose.yaml -f docker/compose.override.yml down -v` 销毁卷；`up -d` 触发 init script 用新 role 重建。**checkpointer history 全丢**（dev 可接受）。 |
| TEST / PROD 部署 | 不存在（mj-agent 未部署 TEST/PROD）；将来部署时 init script 直接用新 role 创建，无迁移负担。 |

**已部署 prod 的备选**（将来若需要在已运行环境改名而不丢数据）：
```sql
-- 在 mj-agent-postgres 的 super-user 会话中：
ALTER ROLE mj_agent_memory RENAME TO mj_agent_app;
-- pg ALTER ROLE 自动迁移所有 GRANTs；连接池会断 5-10s（applications 重连）
```

## Memory pg password rotation（dev / TEST / PROD 操作流程）

`docker/postgres-init/01-bootstrap-mj-agent-memory.sh` 只在 volume
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
# 注意变量名：$pwd 是 PowerShell 只读自动变量（$PWD），赋值会直接报错——用 $memPwd。
# （Select-String 的 -Raw 是 PS7+ 参数；.Line 写法兼容 5.1/7。）
$memPwd = ((Get-Content .env | Select-String '^MJ_AGENT_MEMORY_PASSWORD=').Line `
       -replace '^MJ_AGENT_MEMORY_PASSWORD=','')
docker exec -i mj-agent-postgres `
    psql -U postgres -c "ALTER ROLE mj_agent_app WITH LOGIN PASSWORD '$memPwd';"
# 期望: ALTER ROLE

# 验
docker exec mj-agent mj-agent check
# 期望: CHECK OK（默认 check = 凭据在 + memory DB ping，含刚重置的 mj_agent_app 登录）
# 深验 biz DB + LLM + async memory: docker exec mj-agent mj-agent check --live
```

### 场景 B: dev / test — 可以全清（**Level C 破坏性**）

丢 langgraph checkpoint 数据；用于 dev / test 环境快速重置。

```powershell
docker compose --env-file .env -f docker/compose.yaml `
               -f docker/compose.override.yml down -v
docker compose --env-file .env -f docker/compose.yaml `
               -f docker/compose.override.yml up -d
# 重启时 volume 重建，init script 跑新 password（含 #136 后的 CREATE OR ALTER 改造）
```

### 场景 C: prod — 不能丢数据 + 高可用约束

不能跑 down -v；用场景 A 的 ALTER ROLE 命令。跑前先验证 `.env` password
与 `secrets.enc` 解密一致（避免再次漂移）。如有备份/还原计划，参 ADR-008
storage stack 双隔离约束 + 各环境 backup 策略文档。

### 场景 D: password 字符集安全（#144 起 init script 已无字符集约束）

历史背景：早期（#144 之前）`docker/postgres-init/01-bootstrap-mj-agent-memory.sh`
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
（在容器内或 host 上 `grep '\\getenv mem_user' docker/postgres-init/01-bootstrap-mj-agent-memory.sh` 应命中）；命中仍报错请走场景 A 手动同步并 file follow-up。

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
| `local-openai-compat` | `LLM_BASE_URL`（必）+ `LLM_API_KEY`（可选；vLLM 启用 `--api-key` 时填） | DGX-Spark vLLM/SGLang/Ollama 消费侧；**端点只绑 DGX loopback，须经 owner 隧道 + `host.docker.internal:18000`（见 §2c profile）**；LLM serving 部署责任另议 |

`secrets.example` §2b 已加 `LLM_API_KEY` 占位（可选，vLLM 启用 auth 时启用）；
§2c 携带 ark/dgx 两套 provider profile（#297，见上文「LLM provider profile 选择」）。

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

详见 `capabilities/infrastructure/mcp-server-governance/contracts/mcp-server.contract.yml`（13-server inventory；former MCP STANDARD §5，M6 X5 archived）。

### 6.4 Claude Code MCP secrets 注入（ADR-030 后；mj-ops 风格 OS-level 注入）

Claude Code 的 `.mcp.json` 变量替换（`${MJ_AGENT_SSH_SERVER_*_PASSWORD}` /
`${MJ_AGENT_PG_*_URL}` 等 16 个，含 1 个外部 `${GITHUB_PERSONAL_ACCESS_TOKEN}`）
在 claude.exe 启动时一次性 evaluate process env。Claude Code 本身**不会**
自动加载 `.env` 文件，所以仅有 `.env` 不够 —— 必须让 claude 进程能从 process
env 读到这些 secrets，否则 `/doctor` 会列出 `Missing environment variables`
告警 + ssh-manager 和 WAN postgres MCP server 拉不起来。

自 ADR-030 起，本仓采用 **完整对齐 mj-system v2.3 secrets-sys-ops.enc 模式**：
独立加密包 + 独立 setup 脚本 + 直接写 OS env（永不入 `.env`）。

#### 工作流（2-bundle 后）

```
config/secrets.enc      -[scripts/setup-env.ps1]-> .env
                                                  -[docker compose env_file]-> mj-agent container
                                                  -[pydantic-settings]-> Python runtime

config/secrets-mcp.enc  -[.claude/scripts/setup-mcp-secrets.ps1]-> HKCU\Environment
                                                                  -[claude.exe @ startup]-> .mcp.json ${VAR}
```

两条管道**完全独立**：app secrets 在 `.env`，MCP secrets 在 OS env。Python
应用不读 OS env 里的 MCP secrets（业务零依赖）；Claude Code 不读 `.env` 里的
任何东西（mcp 引用走 OS env）。

#### 用法

```powershell
# 首次（或每次 secrets 轮转 / 首次 clone 后）：
.\scripts\setup-env.ps1 -LlmProfile ark            # 解密 secrets.enc → .env (8 app secrets + LLM profile)
.\.claude\scripts\setup-mcp-secrets.ps1            # 解密 secrets-mcp.enc → OS env (15 MCP secrets)
# 重启 terminal / IDE / claude

# 强制覆盖既有 User env vars 不交互问：
.\.claude\scripts\setup-mcp-secrets.ps1 -Force

# 诊断模式（不写入，对比 OS env vs secrets-mcp.example）：
.\.claude\scripts\setup-mcp-secrets.ps1 -Reload
```

`-Reload` 在调试 "脚本跑了为什么 /doctor 仍报缺失" 时救命：
- 显示 SET 但 /doctor 报 MISSING → 问题在 claude 启动入口（terminal stale）
- 显示 MISSING → 口令错 / `.enc` 文件缺失 / 上一次 setup 漏跑

#### 验证

| 编号 | 命令 | 期望 |
|---|---|---|
| V1 | `.\.claude\scripts\setup-mcp-secrets.ps1 -Reload`（首次 sync 前）| `0 / 15 set, 15 missing` |
| V2 | `.\.claude\scripts\setup-mcp-secrets.ps1`（默认）| `15 processed (15 written)`；提示 `Restart terminal / IDE` |
| V3 | 关闭终端 → 重开 → 同 V1 | `15 / 15 set, 0 missing` |
| V4 | 重启 claude code → `/doctor` | 0 个 mj-agent 相关 `Missing environment variables` 告警（注：`GITHUB_PERSONAL_ACCESS_TOKEN` 由外部提供，不在 mj-agent 治理范围）|

> **Windows env 同步坑（terminal-stale）**：Windows User-level env vars **仅对新启动的进程**可见。同一 PS terminal 里跑 V2 后立即跑 `claude`，子 claude 继承父 PS 的 stale env，会出现「`-Reload` 显示 `15/15 set` 但 `/doctor` 仍报 missing」。两条解：(a) **完全关闭** PS terminal 进程（不只 `/exit`；要红 X 关窗口或 `exit` 退 shell；用 Windows Terminal 时需杀掉整个 wt.exe，因为 WT app 本身也是 stale）→ 从 Start menu 开新 PS → cd worktree → `claude`；(b) 在当前 PS 跑 hot-reload one-liner 不重启：
>
> ```powershell
> foreach ($k in (Get-Item HKCU:\Environment).Property) {
>     [Environment]::SetEnvironmentVariable($k, [Environment]::GetEnvironmentVariable($k, 'User'), 'Process')
> }
> ```
>
> 然后同 PS 跑 `claude` 即可。注意：claude `/doctor` 的 `Missing environment variables` 检查仅判 var key 存在与否，不判 value 是否非空 —— 即使 secrets-mcp.conf §2 某 WAN URL 是空字符串，OS env 写入空 string 后 var 仍"存在"，/doctor 不报；但 MCP server 实际尝试连接时会因空 URL 失败（runtime issue，非 /doctor 级）。

#### 安全代价（已知 trade-off；vs ADR-030 前的对比）

- **HKCU\Environment 明文持久化**：5 SSH passwords + 10 PG URLs（含密码）
  以明文存于注册表 `HKEY_CURRENT_USER\Environment`（**不变**）
- **跨进程可见**：本机任何进程可 `Get-EnvironmentVariable('User')` 读到（**不变**）
- **跨 worktree 共享**：所有 mj-agent worktrees 共享同一组 OS env vars；
  最后一次 `setup-mcp-secrets.ps1` 决定全局值（**不变**）
- **`.env` 不再含 MCP secrets**（**改进**）：之前 `.env` 复制一份 15 个 MCP
  secrets，磁盘上有 2 处明文（`.env` + HKCU）；ADR-030 后只剩 HKCU 一处
- **secret 轮换时只需跑对应脚本**（**改进**）：之前 MCP secret 改了既要重跑
  `setup-env.ps1` 又要重跑 `setup-mcp-env.ps1`；ADR-030 后只跑 `setup-mcp-secrets.ps1`

接受这些代价的换取：**任何 shell（PS / cmd / Git Bash）/ IDE / VS Code 启动
claude 都自动可见**，无 wrapper / 无 alias / 无 PowerShell profile entry。

#### 与 mj-system 的对齐 / 差异

ADR-030 后基本完全对齐 mj-system v2.3 secrets-sys-ops.enc 范式：

| 维度 | mj-system `setup-sys-ops-env.ps1` | mj-agent `setup-mcp-secrets.ps1`（ADR-030 后）|
|---|---|---|
| Secret 源 | 直接解密 `secrets-sys-ops.enc` | 直接解密 `secrets-mcp.enc` ✅ 同 |
| 是否写 `.env` | 否（避免污染主 .env）| 否 ✅ 同 |
| Expected 列表来源 | `secrets-sys-ops.example` 静态列表 | `secrets-mcp.example` 静态列表 ✅ 同 |
| Reload 模式 | 同 | 同 ✅ |
| Helper 函数 | `Format-MaskedValue` / `Read-EnvFile` / `Read-ExampleKeys` | 完全 port ✅ |

剩余差异：
- **命名空间**：mj-system 用 `MJ_SYS_SSH_*` / `MJ_SYS_POSTGRES_*_URL`；mj-agent
  用 `MJ_AGENT_SSH_*` / `MJ_AGENT_PG_*_URL`。独立 per ADR-008。
- **GitHub PAT**：mj-system 有独立 `secrets-sys-git.enc`；mj-agent 无（GitHub
  PAT 借用现有 OS env，不在 mj-agent 治理范围）。

#### 历史：从 ADR-030 前的旧路径迁移

ADR-030 前的旧路径：`secrets.enc → setup-env.ps1 → .env → setup-mcp-env.ps1
→ HKCU`。两阶段，MCP secrets 在 `.env` 磁盘留痕。

已有 `.env` 的开发者需要的迁移：
1. `git pull` 拿到合并后的 develop（含 secrets-mcp.enc + 新 setup-mcp-secrets.ps1）
2. 跑 `.\.claude\scripts\setup-mcp-secrets.ps1`（口令同 secrets.enc）
3. （可选）跑 `.\scripts\setup-env.ps1 -Force` 重生 `.env`，去掉残留的 15 个 MCP
   keys（不重生也无害，业务不读那些 keys）

> 当年的团队管理员一次性迁移工具 `scripts/migrate-secrets-bundle-split.ps1`
> 已随 #297 移除——其内置键清单早于 §2c profile schema（含已裁撤的
> `MJ_AGENT_REDIS_PASSWORD`、缺 §2c 键），如今重跑会产出与现行 schema
> 不一致的 bundle。迁移已完成（commit `b555af9`），工具使命终结。
