---
name: mj-agent-infra-env-setup
description: "适用于 mj-agent 的环境/依赖/凭据准备指导。输入：工具版本、非秘密profile、Owner状态、锁定依赖。流程：prereq→Owner app/MCP分离维护→脱敏完整性→uv sync→offline/live分开。输出：步骤状态与实际覆盖分开，不以check证明LLM/MCP。Use when：新机器搭建，我自己在终端输入口令。Do not use for：把SSH和biz全部复制到Codex项目MCP；拒绝超8服务/6变量范围，登记不可迁入。授权：口令/秘密不入agent；只6项目变量；P1工具未真实运行；聊天批准不自动解锁 hook。独立调用完成后结束，委派返回调用者；不自动跨阶段、提交或发布外部消息。"
---


# mj-agent Infra — Env Setup

## 本技能的执行约定

执行前读取 [共用执行边界](../../references/execution-boundaries.md)。独立调用只完成本技能；委派时记录调用者与返回阶段，同阶段必要校验完成后返回。下游 Handoff 均为建议，不能自动跨阶段或发布。受保护动作先完成可审阅草案；Owner 批准与宿主执行能力分开，hook 硬阻断时返回 `BLOCKED_EXECUTION_ROUTE`。


## 触发与职责详述

This skill should be used when the user asks to set up the .env file, decrypt secrets.enc, install dependencies, or prepare local environment for mj-agent development. Make sure to use this skill whenever the user says "环境配置", "env setup", ".env 配置", "设置环境", "解密 secrets", "decrypt secrets.enc", "team password", "团队口令", "POSTGRES_ANALYST_USER", "ARK_API_KEY", "LANGSMITH_API_KEY", "uv sync", "first time setup", "新机器搭建", "本地环境", "scripts/setup-env.ps1", "setup-mcp-secrets" in the mj-agent context. Wraps two ADR-030 setup scripts: (1) scripts/setup-env.ps1 (AES-256-CBC + PBKDF2 decrypt config/secrets.enc; 8 app secrets: analyst pg creds + ARK/LANGSMITH/LLM keys + storage-stack memory passwords + pg superuser; merged into .env), and (2) scripts/mcp/setup-mcp-secrets.ps1 (decrypt config/secrets-mcp.enc; 6 permitted project variables: GitHub token and memory URLs for five environments; written directly to OS User-level env, never to .env). Plus uv sync + minimal .env validation. Outputs setup checklist + verification commands; does NOT modify the setup scripts, secrets bundles, or write .env directly (only invokes the scripts with proper params). Note: both decrypt steps require interactive password (TTY); Codex does not collect passwords or execute decryption/OS credential writes — user must run setup scripts in their own PowerShell terminal. Do not use for: Studio probe end-to-end testing (use mj-agent-infra-studio-probe), Docker compose lifecycle (use mj-agent-infra-docker-compose), or storage stack management (use mj-agent-infra-storage-stack).


## Overview

包装 mj-agent 已有的 2 个 secrets setup 脚本（ADR-030 起 2-bundle 拆分）：

1. `scripts/setup-env.ps1` — 解密 `config/secrets.enc`，注入 8 app secrets（+ §2c LLM profile）到 `.env`
2. `scripts/mcp/setup-mcp-secrets.ps1` — 解密 `config/secrets-mcp.enc`，写入 6 项项目变量（GitHub + memory×5） 到 OS User-level env（不入 `.env`）

加上 `uv sync` 依赖安装 + 最小 `.env` validation。**Stage 8 (C-flavor) sub** of the 17-stage 执行闭环。

新机器 / 新贡献者上手时第一个调用的 infra skill。

**Reference**:
- `repo:scripts/setup-env.ps1`（app bundle 解密脚本）
- `repo:scripts/mcp/setup-mcp-secrets.ps1`（MCP bundle 解密脚本；ADR-030 新增）
- `repo:config/README.md`（rotation / onboarding flow + ADR-030 2-bundle 模型）
- `repo:decisions/ADR-030_Secrets_Bundle_Split_For_MCP_Isolation.md`（bundle 拆分决策）
- `repo:config/README.md`（应用配置）与 `repo:.env.example`（仅公开变量名）（secret 列表）

## 前置条件

- 应用脚本按其支持环境由 Owner 执行；MCP 候选需要 PowerShell 7（pwsh，P1测试环境），不能把 5.1 当作已验证支持
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

## Codex vs User Execution Boundary

| Step | 谁执行 | 边界 |
|---|---|---|
| Step 1 前置 | Codex 或 Owner | 仅检查工具版本；不自动安装 |
| Step 2 解密/OS 注入 | Owner 自己的终端 | 不向 agent 提供口令，不回传秘密值 |
| Step 3 完整性 | 已授权时 Codex 可用脱敏脚本 | 仅键名/状态，禁止直接读取 .env |
| Step 4 依赖 | 当前任务授权范围内 | 固定版本与 lock，不为验收擅自升级 |
| Step 5 验证 | 离线与真实探针分开 | `mj-agent check` 含 memory ping，真实执行需明确范围 |

Windows 使用实际 PowerShell；Bash 示例只在相应 shell 可用时采用，不使用旧客户端 `!` 前缀。

## Workflow

### Step 1 — Prerequisite Check

User 终端（PowerShell）：

```powershell
uv --version           # 期望 0.4+
uv python list         # 期望含 3.13.x；缺则 uv python install 3.13
$PSVersionTable        # 期望 PSVersion 5.1+
```

可用 Bash shell 的等价前置检查（未发现时使用上方 PowerShell）：

```bash
uv --version                                                       # 跨 shell 可用
uv python list 2>&1 | head -20                                     # bash 等价
powershell.exe -NoProfile -Command '$PSVersionTable.PSVersion'     # 单引号必需
```

如缺 → 输出对应 install 指引，**不**自动 install（user 决定）。

### Step 2 — 解密两个 bundle（app → .env；MCP → OS env）

以下是**最终部署后 Owner 自己终端的命令**；P2 仅候选路径存在，不执行，也不把秘密包复制进候选根。MCP 维护需要 PowerShell 7/pwsh；5.1 不算该候选已验证平台。

```powershell
# 在 mj-agent 仓 develop/（或任意 worktree）根执行
# 2a. App bundle → .env（-LlmProfile 选 LLM 套装：无 DGX 隧道的机器一律 ark）
.\scripts\setup-env.ps1 -LlmProfile ark
#     有 DGX 隧道 + Docker Desktop 的机器：.\scripts\setup-env.ps1 -Force -LlmProfile dgx

# 2b. MCP bundle → OS User-level env（同一口令；不写 .env）
pwsh -NoProfile -File scripts/mcp/setup-mcp-secrets.ps1
#     ⚠ 跑完必须【完全重启】终端 + Codex（User env 只对新进程可见）
```

脚本会询问团队解密口令（**不**回显 / **不**记录）；两 bundle 同口令、同 AES-256-CBC + PBKDF2 算法，注入目标不同（ADR-030）：

**2a. `secrets.enc` → `.env`（8 app secrets + §2c LLM provider profile）**（脚本末尾打印 `[OK] Decrypted N secrets.` + `LLM profile resolved: <ark|dgx>` 做核对）：

| Key | 来源章节 | 用途 |
|---|---|---|
| `POSTGRES_ANALYST_USER` / `POSTGRES_ANALYST_PASSWORD` | §1 | biz pg analyst RO（ADR-006 / ADR-009） |
| `ARK_API_KEY` | §2 | Volcengine Ark；`LLM_PROVIDER=ark` 必填 |
| `LLM_API_KEY` | §2b | `LLM_PROVIDER=local-openai-compat` 且端点启用 `--api-key` 时填 |
| §2c profile 组（`LLM_PROVIDER`/`LLM_BASE_URL`/`LLM_MODEL_ID`/`NO_PROXY`） | §2c | 按 `-LlmProfile` 从 ark/dgx 两套解析**一套**注入（#297；命名空间键不落 .env） |
| `LANGSMITH_API_KEY` | §3 | LangSmith trace（可选；详见 Developer_Onboarding §7.2） |
| `MJ_AGENT_MEMORY_USER` / `MJ_AGENT_MEMORY_PASSWORD` | §4 | mj-agent-postgres `mj_agent_app` role RW（postgres-init 用此值建 role） |
| `MJ_AGENT_PG_SUPERUSER_PASSWORD` | §4b | mj-agent-postgres 容器超管（compose-only；Python 不读） |

**2b. MCP 维护由 Owner 终端执行 `scripts/mcp/setup-mcp-secrets.ps1`**：仅 `GITHUB_PERSONAL_ACCESS_TOKEN` 与
`MJ_AGENT_PG_MEMORY_{DEV,TEST_LAN,TEST_WAN,PROD_LAN,PROD_WAN}_URL`。按变量名交给原生项目配置；
不迁移 biz/SSH/个人来源。诊断 `-Reload` 也由 Owner 执行；不打印值或前缀。
重启相关进程后只回报状态。P1 只验证了合成输入，不保证真实凭据或服务可用。

> **失败模式**：
> - 口令错 → 脚本失败，无残留 .env 改动；让用户重试 / 联系负责人
> - `secrets.enc` 缺失（git fetch 不全）→ `git fetch origin` 后重试
> - PowerShell 执行策略限制 → 交 Owner 审阅本机执行策略，不由 agent 自动修改

### Step 3 — `.env` 完整性核对

> **LLM provider 分支**（PR-2 / ADR-027 + #297 profile 机制）：mj-agent 现支持两个 LLM provider，secret/config 必填字段不同：
> - `LLM_PROVIDER=ark`（默认）→ 必须 `ARK_API_KEY` 非空（或新通用 `LLM_API_KEY`）
> - `LLM_PROVIDER=local-openai-compat`（DGX-Spark 本地 vLLM/SGLang/Ollama）→ 必须 `LLM_BASE_URL` 非空；`LLM_API_KEY` 可填 `EMPTY`；端点经 owner SSH 隧道 + `host.docker.internal:18000`（ADR-027 D.3 Amendment——LAN 直连不通）
> - provider 切换推荐走 `.\scripts\setup-env.ps1 -Force -LlmProfile <ark|dgx>`（bundle §2c 携带整套值含 `NO_PROXY`；见 config/README.md），不手工拼 .env
> - 切换到 local-openai-compat 后，**必须**跑 `mj-agent-infra-llm-endpoint-probe` 确认 endpoint 健康

任一执行者（Codex shell 执行工具 / Codex / user 终端）统一走脱敏脚本：

```bash
powershell.exe -NoProfile -File scripts/check_env_keys.ps1
# pwsh 亦可：pwsh -NoProfile -File scripts/check_env_keys.ps1
# 输出：INFO LLM_PROVIDER resolved: <ark|local-openai-compat>
#      PRESENT / EMPTY / MISSING <key>（逐键，一行一个）
# exit 0 = 全 PRESENT；exit 1 = 存在 EMPTY / MISSING
```

脚本内部读 `.env` 并判定 provider-aware required secrets（ark → `ARK_API_KEY`；local-openai-compat → `LLM_BASE_URL`；两者都要 `POSTGRES_ANALYST_USER/PASSWORD`）+ 必填非 secret 字段（`MJ_CONFIG_PROFILE` / `POSTGRES_DEV_HOST` / `POSTGRES_DEV_PORT` / `LLM_MODEL_ID` / `LLM_PROVIDER` / `NO_PROXY`——NO_PROXY 自 #297 有模板默认，Clash/v2ray 机器缺失会导致 localhost/隧道请求 502/ConnectError）。**只输出键名与状态，永不回显值**——Agent 不得自行 grep / `Select-String` 解析 `.env`（v5 §5.2 secrets 边界）。

如缺非 secret 字段（`MJ_CONFIG_PROFILE` / `POSTGRES_DEV_HOST` / `LLM_MODEL_ID` / `LLM_PROVIDER` 等）→ user 手动从 `.env.example` 拷贝填写（**不**自动改 .env；secret 字段 + 配置字段拼装策略由 user 控制）。

如 `LLM_PROVIDER=local-openai-compat` → 跑 `mj-agent-infra-llm-endpoint-probe` 验证 DGX vLLM endpoint 可达 + model 加载 + chat smoke。

> **重要**：`.env.example` 是 ASCII-only（python-dotenv 在中文 Windows 上对 UTF-8 非 ASCII 内容会失败；详见 `repo:config/README.md`（应用配置）与 `repo:.env.example`（仅公开变量名））。

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
# 按真实输出记录；默认 check 不证明 biz/LLM live 成功
# 失败 → 检查 .env / secret / 网络
# 若额外出现 [DRIFT] / [MISSING] 段：.env.example 含但 .env 缺的 key 列表
#   （warn-only，不影响 exit code；与 setup-env.ps1 的 [DRIFT] 算法一致）。
#   处理：手动从 .env.example 补缺 key 到 .env；或不带 -Force 重跑
#   `.\scripts\setup-env.ps1` 看完整 drift 报告 + 决定是否 -Force 重生。

# 2. lint + 类型检查（应全过；项目级 CI 等价）
uv run ruff check
uv run mypy src/mj_agent

# 3. fast test（不打 DB / LLM）
uv run --frozen --no-sync python scripts/sdd/run_offline_pytest.py tests/unit
uv run --frozen --no-sync python scripts/sdd/run_offline_pytest.py tests/eval

# 4.（可选）只验证 external bands 的 structured policy skip
# uv run --frozen --no-sync python scripts/sdd/run_offline_pytest.py tests/integration
# uv run --frozen --no-sync python scripts/sdd/run_offline_pytest.py tests/smoke -m smoke
```

`mj-agent check` 的通过仅证明该次检查覆盖项；biz/LLM live、MCP连接与宿主加载分别记录未验证或真实结果。

## What This Skill DOES NOT DO

- ❌ 不直接编辑 `.env`（仅调 setup-env.ps1 + 提示 user 手动补 .env.example 字段）
- ❌ 不修改 `scripts/setup-env.ps1` / `secrets.enc`（**read-only invoke**）
- ❌ 不分发解密口令（必须线下 / IM 接收，不在仓库内）
- ❌ 不安装 uv / Python / PowerShell（仅输出 install 指引；user 决定）
- ❌ 不替代 `mj-agent-infra-studio-probe`（Studio E2E 探针；mj-agent check 仅 creds 健康）
- ❌ 不替代 `mj-agent-infra-docker-compose`（compose lifecycle）
- ❌ 不替代 `mj-agent-infra-storage-stack`（mj-agent-postgres + mj-agent-redis）

## Sub-skill / Tool Calls

| Tool | 谁调 | 用途 |
|---|---|---|
| shell `uv python list` / `uv --version` / `powershell.exe -NoProfile -Command '$PSVersionTable.PSVersion'` | Codex or User | Step 1 prereq |
| **User 终端** `.\scripts\setup-env.ps1`（**不**通过 Codex shell 执行工具；TTY required） | **User only** | Step 2 解密注入 |
| shell `powershell.exe -NoProfile -File scripts/check_env_keys.ps1`（脱敏：只回键名+状态，永不回值） | Codex or User | Step 3 .env 完整性 |
| shell `uv sync` / `uv lock` | Codex or User | Step 4 依赖 |
| shell `uv run mj-agent check` | Codex or User | Step 5 健康探针 |
| shell `uv run ruff` / `mypy` / `pytest` | Codex or User | Step 5 验证 |

## Anti-patterns

- **不要** 在 PR / commit 内提交 `.env`（已 .gitignore；受 mj-agent-git-commit Step 2 H1 硬阻断）
- **不要** 在 PR / commit 提交解密产物（如临时 `.env.decrypted`）
- **不要** 把团队口令写进 SKILL.md / 文档 / commit message
- **不要** 自动 install Python / uv / PowerShell（user 决定）
- **不要** 跳过 Step 5 healthcheck（缺验证可能 .env 字段错但脚本无报）
- **不要** 在 `.env.example` 加非 ASCII 内容（python-dotenv UTF-8 编码失败；详见 AGENTS.md）
- **不要** 让 Agent 直接 grep / `Get-Content` 解析 `.env`（一律走 `scripts/check_env_keys.ps1` 脱敏输出；v5 §5.2 secrets 边界）

## Output Format

```markdown
## Env Setup Result

### Prerequisite Check
- ✅ Python 3.13.5
- ✅ uv 0.4.18
- <实际版本；MCP需pwsh 7，未测版本标未验证>

### Decrypt bundles
- ✅ scripts/setup-env.ps1 完成（8 app secrets 已注入 .env；LLM profile = ark）
- ✅ scripts/mcp/setup-mcp-secrets.ps1 完成（6 项项目变量（GitHub + memory×5） → HKCU；已提示重启终端）
- 注入字段：详见 Step 2 表（§1 analyst pg + §2/§2b LLM keys + §2c profile 组 + §3 LangSmith + §4/§4b storage-stack；GitHub + memory×5 走项目 MCP 维护入口 → OS env）

### .env Completeness（scripts/check_env_keys.ps1 脱敏输出）
- ✅ provider-aware required secrets 全 PRESENT（LLM_PROVIDER=ark → 含 ARK_API_KEY；=local-openai-compat → 含 LLM_BASE_URL）
- ⚠️ MISSING MJ_CONFIG_PROFILE — 请从 .env.example 拷贝填 dev/test/prod
- ⚠️ MISSING POSTGRES_DEV_HOST — 请从 .env.example 拷贝填具体 host
- ✅ PRESENT LLM_MODEL_ID

### uv sync
- ✅ Dependencies synced (87 packages, 0 conflicts)

### Healthcheck
- ✅ uv run mj-agent check — 按实际覆盖项记录，不能推定 LLM live OK
- ✅ uv run ruff check — All checks passed!
- ✅ uv run mypy src/mj_agent — Success: no issues
- ✅ uv run --frozen --no-sync python scripts/sdd/run_offline_pytest.py tests/unit — 87 passed

### Next Steps
- 进入开发：mj-agent-flow-intake
- 启 Studio：mj-agent-infra-studio-probe
- compose 起 storage：mj-agent-infra-docker-compose
```

## Reference Files

- `scripts/setup-env.ps1`（解密脚本）
- `config/README.md`（rotation / onboarding flow）
- `config/secrets.enc`（加密 secret 包）
- `.env.example`（非 secret 字段模板；ASCII-only）
- `repo:config/README.md`（应用配置）与 `repo:.env.example`（仅公开变量名）
- `pyproject.toml` / `uv.lock`（依赖）
- `repo:docs/guide/[GUIDE]_Developer_Onboarding.md` §7（Studio 探针前置）
- `repo:sdd/workflows/execution-loop.md`（C 风味 secret 同步硬约束；原 HITL_Prompt §4.7 Rule 15，M6 PR4 archived → kernel）

## Handoff

```
Env setup 完成 ✓
下一步：
- 启 Studio: mj-agent-infra-studio-probe
- 起 compose: mj-agent-infra-docker-compose
- 进开发: mj-agent-flow-intake → 17-stage 闭环
```
