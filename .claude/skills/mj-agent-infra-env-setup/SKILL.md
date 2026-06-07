---
name: mj-agent-infra-env-setup
description: This skill should be used when the user asks to set up the .env file, decrypt secrets.enc, install dependencies, or prepare local environment for mj-agent development. Make sure to use this skill whenever the user says "环境配置", "env setup", ".env 配置", "设置环境", "解密 secrets", "decrypt secrets.enc", "team password", "团队口令", "POSTGRES_ANALYST_USER", "ARK_API_KEY", "LANGSMITH_API_KEY", "uv sync", "first time setup", "新机器搭建", "本地环境", "scripts/setup-env.ps1", "setup-mcp-secrets" in the mj-agent context. Wraps two ADR-030 setup scripts: (1) scripts/setup-env.ps1 (AES-256-CBC + PBKDF2 decrypt config/secrets.enc; ~6-8 app secrets: analyst pg creds + ARK/LANGSMITH/LLM keys + storage-stack memory passwords; merged into .env), and (2) .claude/scripts/setup-mcp-secrets.ps1 (decrypt config/secrets-mcp.enc; 15 MCP secrets: 5 SSH passwords + 10 PG URL placeholders; written directly to OS User-level env, never to .env). Plus uv sync + minimal .env validation. Outputs setup checklist + verification commands; does NOT modify the setup scripts, secrets bundles, or write .env directly (only invokes the scripts with proper params). Note: both decrypt steps require interactive password (TTY); Claude's Bash tool cannot supply it — user must run setup scripts in their own PowerShell terminal. Do not use for: Studio probe end-to-end testing (use mj-agent-infra-studio-probe), Docker compose lifecycle (use mj-agent-infra-docker-compose), or storage stack management (use mj-agent-infra-storage-stack).
---

# mj-agent Infra — Env Setup

## Overview

包装 mj-agent 已有的 2 个 secrets setup 脚本（ADR-030 起 2-bundle 拆分）：

1. `scripts/setup-env.ps1` — 解密 `config/secrets.enc`，注入 ~6-8 app secrets 到 `.env`
2. `.claude/scripts/setup-mcp-secrets.ps1` — 解密 `config/secrets-mcp.enc`，写入 15 MCP secrets 到 OS User-level env（不入 `.env`）

加上 `uv sync` 依赖安装 + 最小 `.env` validation。**Stage 8 (C-flavor) sub** of HITL_Prompt 17-stage 闭环。

新机器 / 新贡献者上手时第一个调用的 infra skill。

**Reference**:
- [[../../../scripts/setup-env.ps1|scripts/setup-env.ps1]]（app bundle 解密脚本）
- [[../../../.claude/scripts/setup-mcp-secrets.ps1|setup-mcp-secrets.ps1]]（MCP bundle 解密脚本；ADR-030 新增）
- [[../../../config/README.md|config/README.md]]（rotation / onboarding flow + ADR-030 2-bundle 模型）
- [[decisions/ADR-030_Secrets_Bundle_Split_For_MCP_Isolation|ADR-030]]（bundle 拆分决策）
- [[../../../CLAUDE.md|CLAUDE.md]] "Environment variables" 段（secret 列表）

## 前置条件

- Windows PowerShell（`scripts/setup-env.ps1` 是 .ps1）
- mj-agent 仓已 clone（含 `.bare` + `develop/`）
- 团队分发的解密口令（联系项目负责人或 onboarding mentor）
- Python 3.13 + uv（`uv --version` 验证；缺 → 见 Step 1 install 指引）

## 快速开始（交互模式）

| 已知 | 行动 |
|---|---|
| 用户说"设置环境"但无解密口令 | 提示先联系项目负责人取口令；本 skill 不处理口令分发 |
| 用户已有口令但还没 .env | 直接进 Step 2 解密 |
| 用户已有 .env 但 uv 没装 | 跳到 Step 3 uv sync |
| 用户在新机器从 0 起 | 完整 5 步 |
| stack 之前用 OS user env 起过（`setup-mcp-env.ps1` 镜像到 HKCU\Environment），仓内无 `.env` | 仍走完整 5 步：`mj-agent serve` / `mj-agent check` 通过 python-dotenv 读 `.env`，不读 process env；docker compose `${VAR}` 用 process env 可起栈但 Python 入口不可 |

## Claude vs User Execution Boundary

| Step | 谁执行 | 原因 |
|---|---|---|
| Step 1 prereq check | Claude or User | 只读探测；Claude 走 Bash tool 时见 §"Bash tool 调用 PowerShell" |
| **Step 2 decrypt** | **User only** | `Read-Host -AsSecureString` 需 TTY；Claude 的 Bash tool 无 TTY 无法供口令；harness `!` 前缀走 bash 也无法供 SecureString |
| Step 3 .env 完整性 | Claude or User | 只读 grep；Claude 走 Bash tool 时见 §"Bash tool 调用 PowerShell" |
| Step 4 `uv sync` | Claude or User | 非交互 |
| Step 5 healthcheck | Claude or User | 非交互 |

### `!` 前缀路径陷阱（Step 2 走 `!` 前缀时必须避开）

- ❌ `! .\scripts\setup-env.ps1` — bash 把 `\s` 当转义 → 命令名变成 `.scriptssetup-env.ps1` not found
- ✅ user 在自己 PowerShell 终端直接跑 `.\scripts\setup-env.ps1`（**推荐**；本机 PS 原生 SecureString 路径）
- ✅ 若坚持 `!` 前缀：`! powershell.exe -NoProfile -File scripts/setup-env.ps1`（用正斜杠避免反斜杠转义）

### Bash tool 调用 PowerShell（Step 1 / Step 3 only）

Claude 的 Bash tool 在 Windows 上是 **git-bash**，不是 PowerShell。所有 `Get-Content / Select-String / $PSVersionTable / Write-Warning` 等 PS cmdlet 在 Bash tool 下直跑必然 `command not found`。两种处理：

- **A（推荐）**：`powershell.exe -NoProfile -Command 'SCRIPT'` — 必须**单引号**包住 SCRIPT（双引号会让 bash 提前展开 `$var`）
- **B（备选）**：用 bash 等价物（`grep -E`、`test -f`、`cut -d= -f2` 等）

下面 Step 1/3 的代码块同时给 user-terminal（PowerShell）与 Claude-bash-tool 两种写法。

## Workflow

### Step 1 — Prerequisite Check

User 终端（PowerShell）：

```powershell
uv --version           # 期望 0.4+
uv python list         # 期望含 3.13.x；缺则 uv python install 3.13
$PSVersionTable        # 期望 PSVersion 5.1+
```

Claude 走 Bash tool 时（git-bash）：

```bash
uv --version                                                       # 跨 shell 可用
uv python list 2>&1 | head -20                                     # bash 等价
powershell.exe -NoProfile -Command '$PSVersionTable.PSVersion'     # 单引号必需
```

如缺 → 输出对应 install 指引，**不**自动 install（user 决定）。

### Step 2 — 解密 secrets.enc（注入 .env 的 22 secrets）

```powershell
# 在 mj-agent 仓 develop/（或任意 worktree）根执行
.\scripts\setup-env.ps1
```

脚本会询问团队解密口令（**不**回显 / **不**记录）；脚本内部用 AES-256-CBC + PBKDF2 解密 `config/secrets.enc`，merge **22 个 secret** 到 `.env`（按 `.env.example` §1–§9 分组；脚本运行末尾打印 `[OK] Decrypted N secrets.` 做核对）：

| Secret | 来源章节 | 用途 |
|---|---|---|
| `POSTGRES_ANALYST_USER` / `POSTGRES_ANALYST_PASSWORD` | §1 | biz pg analyst RO（ADR-006 / ADR-009） |
| `ARK_API_KEY` | §2 | Volcengine Ark；`LLM_PROVIDER=ark` 必填 |
| `LLM_BASE_URL` / `LLM_API_KEY` | §2 | `LLM_PROVIDER=local-openai-compat` 必填（DGX-Spark vLLM/SGLang/Ollama；ADR-027 PR-2） |
| `LANGSMITH_API_KEY` | §3 | LangSmith trace（可选；详见 Developer_Onboarding §7.2） |
| `MJ_AGENT_MEMORY_PASSWORD` | §5 | mj-agent-postgres `mj_agent_app` role RW（storage-stack PR；postgres-init 用此值建 role） |
| `MJ_AGENT_REDIS_PASSWORD` | §5b | future use；container ready 但无 client wired |
| `MJ_AGENT_SSH_SERVER_{CLOUD,RUNNER,TEST,PROD,DGX}_PASSWORD`（**5 个**） | §8 | ssh-manager MCP server（ADR-028 PR-3；9 entries 用 5 unique passwords：lan + wan 同主机共密码） |
| `MJ_AGENT_PG_{MEMORY,BIZ}_{DEV,TEST_LAN,TEST_WAN,PROD_LAN,PROD_WAN}_URL`（**10 个**） | §9 | `.mcp.json` 包装脚本的连接 URL；WAN 必填（FRP 隧道无 fallback）；LAN 可选（有 placeholder） |

> **失败模式**：
> - 口令错 → 脚本失败，无残留 .env 改动；让用户重试 / 联系负责人
> - `secrets.enc` 缺失（git fetch 不全）→ `git fetch origin` 后重试
> - PowerShell 执行策略限制 → `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` 后重试

### Step 3 — `.env` 完整性核对

> **LLM provider 分支**（PR-2 / ADR-027）：mj-agent 现支持两个 LLM provider，secret/config 必填字段不同：
> - `LLM_PROVIDER=ark`（默认）→ 必须 `ARK_API_KEY` 非空（或新通用 `LLM_API_KEY`）
> - `LLM_PROVIDER=local-openai-compat`（DGX-Spark 本地 vLLM/SGLang/Ollama）→ 必须 `LLM_BASE_URL` 非空；`LLM_API_KEY` 可填 `EMPTY`
> - 切换到 local-openai-compat 后，**必须**跑 `/mj-agent-infra-llm-endpoint-probe` 确认 endpoint 健康

Claude 走 Bash tool（git-bash）：

```bash
# Provider 检测
provider=$(grep -E '^LLM_PROVIDER=' .env | head -1 | cut -d= -f2)
provider=${provider:-ark}
echo "LLM_PROVIDER=$provider"

# Provider-aware required keys
case "$provider" in
  ark)                  required=("POSTGRES_ANALYST_USER" "POSTGRES_ANALYST_PASSWORD" "ARK_API_KEY") ;;
  local-openai-compat)  required=("POSTGRES_ANALYST_USER" "POSTGRES_ANALYST_PASSWORD" "LLM_BASE_URL") ;;
esac

for k in "${required[@]}"; do
  v=$(grep -E "^${k}=" .env | head -1 | cut -d= -f2)
  if [ -z "$v" ] || [ "$v" = '""' ]; then
    echo "⚠️  $k is empty (required for LLM_PROVIDER=$provider)"
  else
    echo "✅ $k present"
  fi
done

# 必填非 secret 字段（参 .env.example）
for k in MJ_CONFIG_PROFILE POSTGRES_DEV_HOST POSTGRES_DEV_PORT LLM_MODEL_ID LLM_PROVIDER; do
  grep -qE "^${k}=" .env || echo "⚠️  $k missing in .env (copy from .env.example)"
done
```

User 终端（PowerShell）等价：

```powershell
$provider = (Get-Content .env | Select-String "^LLM_PROVIDER=").Line -replace "^LLM_PROVIDER=",""
if (-not $provider) { $provider = "ark" }

$requiredSecrets = @("POSTGRES_ANALYST_USER","POSTGRES_ANALYST_PASSWORD")
if ($provider -eq "ark") { $requiredSecrets += "ARK_API_KEY" }
elseif ($provider -eq "local-openai-compat") { $requiredSecrets += "LLM_BASE_URL" }

$requiredSecrets | ForEach-Object {
    if ((Get-Content .env | Select-String "^$_=" | Select-Object -First 1) -match '=$|=\s*$|=""$') {
        Write-Warning "$_ is empty in .env (required for LLM_PROVIDER=$provider)"
    } else { Write-Host "✅ $_ present" }
}

@("MJ_CONFIG_PROFILE","POSTGRES_DEV_HOST","POSTGRES_DEV_PORT","LLM_MODEL_ID","LLM_PROVIDER") | ForEach-Object {
    if (-not (Get-Content .env | Select-String "^$_=")) { Write-Warning "$_ missing in .env (copy from .env.example)" }
}
```

如缺非 secret 字段（`MJ_CONFIG_PROFILE` / `POSTGRES_DEV_HOST` / `LLM_MODEL_ID` / `LLM_PROVIDER` 等）→ user 手动从 `.env.example` 拷贝填写（**不**自动改 .env；secret 字段 + 配置字段拼装策略由 user 控制）。

如 `LLM_PROVIDER=local-openai-compat` → 跑 `/mj-agent-infra-llm-endpoint-probe` 验证 DGX vLLM endpoint 可达 + model 加载 + chat smoke。

> **重要**：`.env.example` 是 ASCII-only（python-dotenv 在中文 Windows 上对 UTF-8 非 ASCII 内容会失败；详见 CLAUDE.md "Environment variables" 段）。

### Step 4 — uv sync 依赖安装

```powershell
uv sync
```

> 首次跑会创建 `.venv/` + 锁定依赖；后续修改 pyproject.toml 后重跑。

如失败：

| 错误 | 原因 | 修复 |
|---|---|---|
| `uv` 未识别 | uv 没装 / PATH 没 / 关闭重开终端 | 参 Step 1 |
| `uv.lock` mismatch | pyproject.toml 改了但 lock 未更新 | `uv lock` 后 `uv sync` |
| 网络超时（pip backend） | 防火墙 / 代理 | 配 `UV_INDEX_URL` 或代理 |
| Python 3.13 不可用 | uv 没找到对应 Python | `uv python install 3.13` |

### Step 5 — 健康验证

```powershell
# 1. 健康探针（DB + LLM creds + .env.example drift）
uv run mj-agent check
# 期望：✅ DB connection OK + ✅ Ark LLM call OK
# 失败 → 检查 .env / secret / 网络
# 若额外出现 [DRIFT] / [MISSING] 段：.env.example 含但 .env 缺的 key 列表
#   （warn-only，不影响 exit code；与 setup-env.ps1 的 [DRIFT] 算法一致）。
#   处理：手动从 .env.example 补缺 key 到 .env；或不带 -Force 重跑
#   `.\scripts\setup-env.ps1` 看完整 drift 报告 + 决定是否 -Force 重生。

# 2. lint + 类型检查（应全过；项目级 CI 等价）
uv run ruff check
uv run mypy src/mj_agent

# 3. fast test（不打 DB / LLM）
uv run pytest tests/unit
uv run pytest tests/eval

# 4.（可选）integration / smoke（需 .env 充实）
# uv run pytest tests/integration  # 需 POSTGRES_ANALYST_USER
# uv run pytest tests/smoke -m smoke  # 需 ARK_API_KEY
```

`uv run mj-agent check` 通过 = 环境就绪。

## What This Skill DOES NOT DO

- ❌ 不直接编辑 `.env`（仅调 setup-env.ps1 + 提示 user 手动补 .env.example 字段）
- ❌ 不修改 `scripts/setup-env.ps1` / `secrets.enc`（**read-only invoke**）
- ❌ 不分发解密口令（必须线下 / IM 接收，不在仓库内）
- ❌ 不安装 uv / Python / PowerShell（仅输出 install 指引；user 决定）
- ❌ 不替代 `/mj-agent-infra-studio-probe`（Studio E2E 探针；mj-agent check 仅 creds 健康）
- ❌ 不替代 `/mj-agent-infra-docker-compose`（compose lifecycle）
- ❌ 不替代 `/mj-agent-infra-storage-stack`（mj-agent-postgres + mj-agent-redis）

## Sub-skill / Tool Calls

| Tool | 谁调 | 用途 |
|---|---|---|
| Bash `uv python list` / `uv --version` / `powershell.exe -NoProfile -Command '$PSVersionTable.PSVersion'` | Claude or User | Step 1 prereq |
| **User 终端** `.\scripts\setup-env.ps1`（**不**通过 Claude Bash tool；TTY required） | **User only** | Step 2 解密注入 |
| Bash `grep -E '^KEY=' .env` 或 `powershell.exe -NoProfile -Command 'Get-Content .env \| Select-String ...'` | Claude or User | Step 3 .env 完整性 |
| Bash `uv sync` / `uv lock` | Claude or User | Step 4 依赖 |
| Bash `uv run mj-agent check` | Claude or User | Step 5 健康探针 |
| Bash `uv run ruff` / `mypy` / `pytest` | Claude or User | Step 5 验证 |

## Anti-patterns

- **不要** 在 PR / commit 内提交 `.env`（已 .gitignore；受 mj-agent-git-commit Step 2 H1 硬阻断）
- **不要** 在 PR / commit 提交解密产物（如临时 `.env.decrypted`）
- **不要** 把团队口令写进 SKILL.md / 文档 / commit message
- **不要** 自动 install Python / uv / PowerShell（user 决定）
- **不要** 跳过 Step 5 healthcheck（缺验证可能 .env 字段错但脚本无报）
- **不要** 在 `.env.example` 加非 ASCII 内容（python-dotenv UTF-8 编码失败；详见 CLAUDE.md）

## Output Format

```markdown
## Env Setup Result

### Prerequisite Check
- ✅ Python 3.13.5
- ✅ uv 0.4.18
- ✅ PowerShell 5.1.22000.282

### Decrypt secrets.enc
- ✅ scripts/setup-env.ps1 完成（22 secrets 已注入 .env）
- 注入字段：详见 Step 2 表（§1 analyst pg + §2 LLM + §3 LangSmith + §5/§5b storage-stack + §8 SSH×5 + §9 PG URL×10）

### .env Completeness
- ✅ provider-aware required secrets 全填（LLM_PROVIDER=ark → 含 ARK_API_KEY；=local-openai-compat → 含 LLM_BASE_URL）
- ⚠️ MJ_CONFIG_PROFILE 缺 — 请从 .env.example 拷贝填 dev/test/prod
- ⚠️ POSTGRES_DEV_HOST 缺 — 请从 .env.example 拷贝填具体 host
- ✅ LLM_MODEL_ID = ep-XXXX

### uv sync
- ✅ Dependencies synced (87 packages, 0 conflicts)

### Healthcheck
- ✅ uv run mj-agent check — DB OK + LLM OK
- ✅ uv run ruff check — All checks passed!
- ✅ uv run mypy src/mj_agent — Success: no issues
- ✅ uv run pytest tests/unit — 87 passed

### Next Steps
- 进入开发：/mj-agent-flow-intake
- 启 Studio：/mj-agent-infra-studio-probe
- compose 起 storage：/mj-agent-infra-docker-compose
```

## Reference Files

- `scripts/setup-env.ps1`（解密脚本）
- `config/README.md`（rotation / onboarding flow）
- `config/secrets.enc`（加密 secret 包）
- `.env.example`（非 secret 字段模板；ASCII-only）
- `CLAUDE.md` "Environment variables" 段
- `pyproject.toml` / `uv.lock`（依赖）
- [[../../../docs/guide/[GUIDE]_Developer_Onboarding|Developer Onboarding]] §7（Studio 探针前置）
- [[../../../docs/rule/[STANDARD]_MJ_Agent_AI_Engineering_Execution_HITL_Prompt|HITL_Prompt v1.1]] §4.7 Rule 15（C 风味 secret 同步硬约束）

## Handoff

```
Env setup 完成 ✓
下一步：
- 启 Studio: /mj-agent-infra-studio-probe
- 起 compose: /mj-agent-infra-docker-compose
- 进开发: /mj-agent-flow-intake → 17-stage 闭环
```
