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

### MCP bundle — 原生消费范围

仓库 bundle 保留既有治理。原生 setup 只接受 GitHub token 名称和 memory PG 五个 URL 名称，不导入 biz/SSH；它们是否存在于现有 bundle 不构成迁入理由。应用凭据与 MCP 凭据分离。原生入口为 `scripts/mcp/setup-mcp-secrets.ps1`；解密/OS User env 写入需另行授权。真实凭据与平台可用性未由静态迁移验证。

## secrets.conf 填写指南（填 / 不填 / 预留）

首次配置或 cold-reset 时把 `.example` 复制成 `.conf` 填值——本节是每个字段「该不该填」
的单一真值源（SoT）。**你填的是 `secrets.conf`（→ `encrypt-secrets*.ps1` → `.enc`），不是
`.env`。** 三条铁律先记住：

> - **普通 secret 键留空 → `setup-env.ps1` 会把 `.env` 对应行刷成空** → 启动崩。所以下表「必填」项必须填真值。
> - **§2c `LLM_PROFILE_*` 键留空 → 跳过注入**，`.env.example` 默认值保留（安全）。
> - **MCP 15 键对 app 启动零影响**（ADR-030 业务零依赖）——纯本地开发可全空，按「要用哪些 MCP 工具」决定。

### App bundle `secrets.example`

**§1-§4 的 8 个 app secret（真凭据）**：

| 字段 | 分类 | 说明 |
|---|---|---|
| `POSTGRES_ANALYST_USER` / `POSTGRES_ANALYST_PASSWORD` | **必填** | biz 查询 analyst RO；留空 → `check` fail + 刷空 `.env` |
| `ARK_API_KEY` | **必填**（ark）/ 可空（纯 DGX） | `LLM_PROVIDER=ark` 时缺则 `LLMConfigError` fail-fast |
| `MJ_AGENT_MEMORY_USER` / `MJ_AGENT_MEMORY_PASSWORD` | **必填** | memory pg RW；postgres-init 建 role；⚠ 留空会刷空 `.env` 的 working placeholder → 启动崩 |
| `LLM_API_KEY` | 可空（预留） | vLLM 无鉴权时空即可（回落 `EMPTY` sentinel）；端点启用 `--api-key` 才填 |
| `LANGSMITH_API_KEY` | 可空（预留） | `LANGSMITH_TRACING=false` 时不需要 |
| `MJ_AGENT_PG_SUPERUSER_PASSWORD` | 可空（预留） | compose `:-local-dev-only-replace` fallback 兜底；空值安全 |

**§2c 的 9 个 LLM provider profile 键（非密钥持久层）**：

| 字段 | 分类 | 说明 |
|---|---|---|
| `LLM_PROFILE_DEFAULT` | 可选填 | 填 `ark`/`dgx` 固化机器默认；空则靠 `-LlmProfile` 参数或交互选择 |
| `LLM_PROFILE_ARK__LLM_PROVIDER` = `ark` | 照抄预填 | profile 固定值 |
| `LLM_PROFILE_ARK__LLM_BASE_URL` | **强制留空** | 填了 = ark 打到该端点 → `The model ... does not exist` 404 事故（#297） |
| `LLM_PROFILE_ARK__LLM_MODEL_ID` = `deepseek-v3-2-251201` | 照抄（可微调） | 若你的 key 走接入点授权，改成 `ep-xxxx` |
| `LLM_PROFILE_ARK__NO_PROXY` = `localhost,...,ark.cn-beijing.volces.com` | 照抄预填 | Clash/v2ray 机器防 502 |
| `LLM_PROFILE_DGX__LLM_PROVIDER` = `local-openai-compat` | 照抄预填 | — |
| `LLM_PROFILE_DGX__LLM_BASE_URL` = `http://host.docker.internal:18000/v1` | 照抄（按端点） | 隧道形态；换端点则改 |
| `LLM_PROFILE_DGX__LLM_MODEL_ID` = `nemotron-3-super` | 照抄（按端点） | 须匹配 `--served-model-name` |
| `LLM_PROFILE_DGX__NO_PROXY` = `...,host.docker.internal,192.168.0.189,...` | 照抄预填 | 隧道 + Ark 域名一并放行 |

> 小结：app secret **8**（必填 5 / 纯 DGX 4 · 可空 3）+ §2c profile **9**（照抄 7 · 强制留空 1 · 可选 1）。

### MCP bundle 原生白名单

以 `.codex/config.toml` 的 `env_vars` 和 `scripts/mcp/setup-mcp-secrets.ps1` 的六项白名单为准。变量缺失时对应服务失败；所有 memory URL 都无默认值。不得回显值。历史 SSH/biz 键不被原生 setup 写入，也不进入原生 MCP 子进程。

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

# Step 2: MCP bundle -> OS User-level env (Codex 按 env_vars 白名单继承变量)
.\scripts\mcp\setup-mcp-secrets.ps1
# 提示输入口令（与 Step 1 相同），脚本解密 secrets-mcp.enc 直接写 HKCU\Environment
# 不写 .env 文件！
```

**Step 2 后必须重启**：Windows User-level env 变量只对**新启动的进程**可见。重启
PowerShell 终端 + Codex，才能看到新 OS env 值。

幂等：两个脚本都幂等。重跑 `setup-env.ps1` 会比对每个变量并以 `[SKIP]` /
`[CHANGED]` / `[NEW]` 标注（强制覆盖加 `-Force`）；重跑 `setup-mcp-secrets.ps1`
对 OS env 同样比对（强制覆盖加 `-Force`）。

诊断模式：
```powershell
.\scripts\mcp\setup-mcp-secrets.ps1 -Reload
# 无需口令；仅按原生六项白名单报告 HKCU\Environment 中 SET / MISSING，值不回显
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
  Python runtime 需要消费该值时；纯 `.codex/config.toml` 用的 GitHub/memory MCP 凭据 不要
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

历史 MCP bundle 包含 5 SSH + 10 PG URL；原生 setup 只维护既有 GitHub token 与 memory×5 URL 白名单。历史 bundle 的其他键不迁入，仍走独立 bundle + 独立注入路径（→ `HKCU\Environment`，
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

原生 MCP 变量变更须先取得具名 Owner 批准，并同时核对以下公开接口；不能按历史 bundle 键扩充服务或导入 SSH/biz：
- `config/secrets-mcp.example` 增加键名（值留空）
- 经 Owner 审阅 `.codex/config.toml` 对应 `env_vars` 名称及 `scripts/mcp/setup-mcp-secrets.ps1` 的白名单（变量按名转交，不回显值）
- **显式不登记** `.env.example` / `src/mj_agent/config.py`——ADR-030 核心红线：MCP 键永不入
  `.env`，Python runtime 不消费（误登记 config.py 会让 pydantic-settings 把它当成 app 配置）。

**团队动作差异**：无论轮换还是新增，team 成员都重跑
`.\scripts\mcp\setup-mcp-secrets.ps1`（值变加 `-Force`）**并重启 terminal / IDE / Codex**
（OS User-level env 仅对新启动的进程可见——这是与 app bundle `.env` 流程的关键差异；
诊断 `.\scripts\mcp\setup-mcp-secrets.ps1 -Reload` 报 SET/MISSING）。

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
#    （每字段该填/留空/照抄见上文「## secrets.conf 填写指南」；MCP 的 SSH / PG URL
#     不在此，见下方 MCP bundle）：
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

### MCP bundle 应急恢复

由 Owner 按凭据平台既有流程人工处理；迁移不提供导出真实值的命令，不执行解密、OS 写入或服务探针。原生白名单范围见上文，应用 bundle 的恢复流程独立。

### 收尾

通过安全渠道通知团队「团队口令已轮换」。两 bundle 的值未变、只换了口令，team 成员
用新口令重跑对应 setup 脚本即可（值一致，多为 `[SKIP]`）：
- **App**：`.\scripts\setup-env.ps1`。
- **MCP**：`.\scripts\mcp\setup-mcp-secrets.ps1` + **重启 terminal / IDE / Codex**
  （OS User-level env 仅对新启动的进程可见）。

**前提条件**：cold reset 两个 bundle 各需一个可用来源——
- **App bundle**：至少一台机器有可用 `.env`。若连 `.env` 也丢，从源头重拿 **8 个 app secret
  中的必填 5**（analyst 凭据×2 找 mj-system DBA / Ark API key×1 找 Ark 控制台 / memory pg RW×2）；
  可空 3（LLM_API_KEY / LANGSMITH / SUPERUSER）按上文「填写指南」酌情（详见 `## secrets.conf 填写指南`）。
- **MCP bundle**：至少一台机器 `HKCU\Environment` 仍持有 MCP 值。若连 OS env 也丢，从源头重拿
  **5 个 SSH 密码**（对应主机管理员）+ **4 个 FRP WAN URL**（隧道 / FRP 配置）；6 个 DEV/LAN URL
  可空——留空只是对应 pg MCP server 起不来（`exit /b 3`），app 侧零影响。

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
分层与 LLM provider 抽象保持原规则；原生 MCP 仅承接八项既有项目服务，完整列表见配置及治理契约。

### 6.1 LLM provider 分支

`LLM_PROVIDER` 决定 secret 必填项：

| Provider | 必填 secret | 备注 |
|---|---|---|
| `ark`（默认） | `ARK_API_KEY` | 现有 Ark + DeepSeek V3；既有流程不变 |
| `local-openai-compat` | `LLM_BASE_URL`（必）+ `LLM_API_KEY`（可选；vLLM 启用 `--api-key` 时填） | DGX-Spark vLLM/SGLang/Ollama 消费侧；**端点只绑 DGX loopback，须经 owner 隧道 + `host.docker.internal:18000`（见 §2c profile）**；LLM serving 部署责任另议 |

`secrets.example` §2b 已加 `LLM_API_KEY` 占位（可选，vLLM 启用 auth 时启用）；
§2c 携带 ark/dgx 两套 provider profile（#297，见上文「LLM provider profile 选择」）。
每字段填/留空/照抄的完整分类见上文「## secrets.conf 填写指南」。

### 6.2 SSH / biz 不进入原生 MCP

这些旧客户端连接不参与当前开发入口。业务查询继续遵守 agent tool-chain，不能以 MCP 或数据库客户端绕过。

### 6.3 Memory PG by-name 注入

五个 `pg-mj-agent-memory-*` 项由 `.codex/config.toml` 配置；通过 `scripts/mcp/pg-server-start.ps1` 调用同目录 Node wrapper。只传变量名，使用 `env_vars` 白名单；无默认 URL，未设置或为空即失败，不回显值。

### 6.4 Codex 原生 MCP 设置与证据

`scripts/mcp/setup-mcp-secrets.ps1` 默认解密现有 MCP bundle 并只写六项允许的 User env；`-Reload` 只报告 SET/MISSING，`-Force` 可能覆盖已有值。这些真实操作需 Owner 单独批准，不能作为离线验收命令。SET 不证明服务可运行。更新变量后须由工程师重启宿主并另做获准的服务验证。

`python scripts/sdd/check_codex_native.py --surface mcp` 只检查公开结构，不读取变量值、不启动服务。项目和 hooks 信任由工程师手工审阅；仓库脚本不得修改个人配置或自动激活。Windows 平台与后台生命周期尚需独立验证，其他平台不可由 Windows 静态结果推定通过。
