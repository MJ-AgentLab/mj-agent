---
name: mj-agent-infra-env-setup
description: This skill should be used when the user asks to set up the .env file, decrypt secrets.enc, install dependencies, or prepare local environment for mj-agent development. Make sure to use this skill whenever the user says "环境配置", "env setup", ".env 配置", "设置环境", "解密 secrets", "decrypt secrets.enc", "team password", "团队口令", "POSTGRES_ANALYST_USER", "ARK_API_KEY", "LANGSMITH_API_KEY", "uv sync", "first time setup", "新机器搭建", "本地环境", "scripts/setup-env.ps1" in the mj-agent context. Wraps existing scripts/setup-env.ps1 (AES-256-CBC + PBKDF2 decrypt + 4-secret merge into .env) + uv sync + minimal .env validation. Outputs setup checklist + verification commands; does NOT modify scripts/setup-env.ps1, secrets.enc, or write .env directly (only invokes the script with proper params). Do not use for: Studio probe end-to-end testing (use mj-agent-infra-studio-probe), Docker compose lifecycle (use mj-agent-infra-docker-compose in PR-C3), or storage stack management (use mj-agent-infra-storage-stack in PR-C3).
---

# mj-agent Infra — Env Setup

## Overview

包装 mj-agent 已有的 `scripts/setup-env.ps1`（AES-256-CBC + PBKDF2 解密 + 4 secret 注入 .env）+ `uv sync` 依赖安装 + 最小 .env validation。**Stage 8 (C-flavor) sub** of HITL_Prompt 17-stage 闭环。

新机器 / 新贡献者上手时第一个调用的 infra skill。

**Reference**:
- [[../../../scripts/setup-env.ps1|scripts/setup-env.ps1]]（解密脚本本体）
- [[../../../config/README.md|config/README.md]]（rotation / onboarding flow）
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

## Workflow

### Step 1 — Prerequisite Check

```powershell
# Python 3.13
uv python list
# 期望含 3.13.x；缺则 uv python install 3.13

# uv 包管理
uv --version
# 期望 0.4+；缺则参 https://docs.astral.sh/uv/

# Windows PowerShell（不是 bash；setup-env.ps1 是 .ps1）
$PSVersionTable
# 期望 PSVersion 5.1+
```

如缺 → 输出对应 install 指引，**不**自动 install（user 决定）。

### Step 2 — 解密 secrets.enc（注入 .env 的 4 secrets）

```powershell
# 在 mj-agent 仓 develop/（或任意 worktree）根执行
.\scripts\setup-env.ps1
```

脚本会询问团队解密口令（**不**回显 / **不**记录）；脚本内部用 AES-256-CBC + PBKDF2 解密 `config/secrets.enc`，merge 4 个 secret 到 `.env`：

| Secret | 用途 |
|---|---|
| `POSTGRES_ANALYST_USER` | mj-system biz pg consumer 角色（ADR-009 analyst RO） |
| `POSTGRES_ANALYST_PASSWORD` | 同上密码 |
| `ARK_API_KEY` | Volcengine Ark LLM API key |
| `LANGSMITH_API_KEY` | LangSmith trace（可选；详见 dev_studio_walkthrough §5） |

> **失败模式**：
> - 口令错 → 脚本失败，无残留 .env 改动；让用户重试 / 联系负责人
> - `secrets.enc` 缺失（git fetch 不全）→ `git fetch origin` 后重试
> - PowerShell 执行策略限制 → `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` 后重试

### Step 3 — `.env` 完整性核对

> **LLM provider 分支**（PR-2 / ADR-025）：mj-agent 现支持两个 LLM provider，secret/config 必填字段不同：
> - `LLM_PROVIDER=ark`（默认）→ 必须 `ARK_API_KEY` 非空（或新通用 `LLM_API_KEY`）
> - `LLM_PROVIDER=local-openai-compat`（DGX-Spark 本地 vLLM/SGLang/Ollama）→ 必须 `LLM_BASE_URL` 非空；`LLM_API_KEY` 可填 `EMPTY`
> - 切换到 local-openai-compat 后，**必须**跑 `/mj-agent-infra-llm-endpoint-probe` 确认 endpoint 健康

```powershell
# Determine LLM provider
$provider = (Get-Content .env | Select-String "^LLM_PROVIDER=").Line -replace "^LLM_PROVIDER=",""
if (-not $provider) { $provider = "ark" }   # default per .env.example

# Provider-aware required secret list
$requiredSecrets = @("POSTGRES_ANALYST_USER","POSTGRES_ANALYST_PASSWORD")
if ($provider -eq "ark") {
    $requiredSecrets += "ARK_API_KEY"
} elseif ($provider -eq "local-openai-compat") {
    $requiredSecrets += "LLM_BASE_URL"   # not technically a secret，但 required
}

$requiredSecrets | ForEach-Object {
    if ((Get-Content .env | Select-String "^$_=" | Select-Object -First 1) -match '=$|=\s*$|=""$') {
        Write-Warning "$_ is empty in .env (required for LLM_PROVIDER=$provider)"
    } else {
        Write-Host "✅ $_ present"
    }
}

# 必填非 secret 字段（参 .env.example）
@("MJ_CONFIG_PROFILE","POSTGRES_DEV_HOST","POSTGRES_DEV_PORT","LLM_MODEL_ID","LLM_PROVIDER") | ForEach-Object {
    if (-not (Get-Content .env | Select-String "^$_=")) {
        Write-Warning "$_ missing in .env (copy from .env.example)"
    }
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
# 1. 健康探针（DB + LLM creds）
uv run mj-agent check
# 期望：✅ DB connection OK + ✅ Ark LLM call OK
# 失败 → 检查 .env / secret / 网络

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
- ❌ 不替代 `/mj-agent-infra-docker-compose`（PR-C3 落地；compose lifecycle）
- ❌ 不替代 `/mj-agent-infra-storage-stack`（PR-C3 落地；mj-agent-postgres + mj-agent-redis）

## Sub-skill / Tool Calls

| Tool | 用途 |
|---|---|
| Bash `uv python list` / `uv --version` / `$PSVersionTable` | Step 1 prerequisite |
| Bash `.\scripts\setup-env.ps1` | Step 2 解密注入（**不**带口令参数；脚本会交互问） |
| Bash `Get-Content .env \| Select-String` | Step 3 .env 完整性 |
| Bash `uv sync` / `uv lock` | Step 4 依赖 |
| Bash `uv run mj-agent check` | Step 5 健康探针 |
| Bash `uv run ruff` / `mypy` / `pytest` | Step 5 验证 |

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
- ✅ scripts/setup-env.ps1 完成（4 secret 已注入 .env）
- 注入字段：POSTGRES_ANALYST_USER, POSTGRES_ANALYST_PASSWORD, ARK_API_KEY, LANGSMITH_API_KEY

### .env Completeness
- ✅ 4 secret 全填
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
- 启 Studio：/mj-agent-infra-studio-probe (PR-B3b)
- compose 起 storage：/mj-agent-infra-docker-compose (PR-C3)
```

## Reference Files

- `scripts/setup-env.ps1`（解密脚本）
- `config/README.md`（rotation / onboarding flow）
- `config/secrets.enc`（加密 secret 包）
- `.env.example`（非 secret 字段模板；ASCII-only）
- `CLAUDE.md` "Environment variables" 段
- `pyproject.toml` / `uv.lock`（依赖）
- [[../../../docs/runbook/dev_studio_walkthrough|dev_studio_walkthrough]]（Studio 探针前置）
- [[../../../docs/rule/[STANDARD]_MJ_Agent_AI_Engineering_Execution_HITL_Prompt|HITL_Prompt v1.0]] §4.7 Rule 15（C 风味 secret 同步硬约束）

## Handoff

```
Env setup 完成 ✓
下一步：
- 启 Studio: /mj-agent-infra-studio-probe（PR-B3b 落地）
- 起 compose: /mj-agent-infra-docker-compose（PR-C3 落地）
- 进开发: /mj-agent-flow-intake → 17-stage 闭环
```
