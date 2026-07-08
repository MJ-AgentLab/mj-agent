---
type: guide
domain: SYS
summary: mj-agent 赶时间版 5 分钟启动 — 9 步从 clone 到 Studio 跑通首问；适用于 demo / 培训 / hotfix 现场
tags:
  - guide
  - quick-start
  - onboarding
aliases:
  - mj-agent Quick Start
  - mj-agent 5 分钟启动
created: 2026-05-18
updated: 2026-07-08
state: draft
version: v0.2
track: code
owner: 项目负责人
---

# mj-agent 快速启动 5 分钟版

> **适用范围**：mj-agent 仓库环境从零到 Studio 首问跑通的赶时间版速查清单
> **目标受众**：demo / 培训 / hotfix 现场赶时间的开发者；已熟悉 mj-agent 仅作 refresh 的回归者
> **版本**：v0.2
> **最后更新**：2026-07-08
> **派生自**：mj-agent 原生（参考 mj-system 仓库 `[GUIDE]_Quick_Start_Setup.md` 9 步速查 + Troubleshooting 表的结构与写法；命令与术语均按 mj-agent 自身资产派生）
> **关联文档**：[[[GUIDE]_Developer_Onboarding|Developer Onboarding（15 分钟完整版）]]、[[../../README|README]]、[[../../CLAUDE|CLAUDE.md]]

---

## TL;DR

- **阅读时间**：~5 分钟（命令执行总耗时取决于网速 / 装机情况）
- **涵盖范围**：9 步从 Python 安装到 LangGraph Studio 首问验证；每步含**命令 + 验证**二件套
- **适用场景**：demo / 培训现场赶时间 / hotfix 现场 / 已熟悉 mj-agent 的长假回归刷新

## Prerequisites

- **目标读者**：5 分钟内要让 mj-agent 跑起来的人
- **必备知识**：基础命令行操作 + PowerShell 5.1+（Windows）/ bash（Linux/macOS）
- **建议了解**：Git worktree 概念（不强求；§4 会简单说明）

---

## 目录

- §0 适用场景
- §1 Step 1 — 装 Python 3.13
- §2 Step 2 — 装 uv
- §3 Step 3 — Clone（PowerShell 脚本一键 bare + worktree）
- §4 Step 4 — 进入 develop worktree
- §5 Step 5 — uv sync 装依赖
- §6 Step 6 — 解密 secrets / 准备 .env
- §7 Step 7 — mj-agent check 验 DB + LLM 凭据
- §8 Step 8 — 启动 LangGraph Studio
- §9 Step 9 — Studio 首问验证
- §10 速查表
- §11 Troubleshooting
- §12 关联文档

---

## §0 适用场景

本 GUIDE 是「**赶时间版**」——只列命令 + 验证；**不讲概念 / 不讲为什么**。若需要：

- 理解仓库结构 / 双远端 / 分支模型 / 三轨道文档 / 提交推送 → [[[GUIDE]_Developer_Onboarding|Developer Onboarding（15 分钟完整版）]]
- 理解 LLM provider 切换 / 数据边界 4 层 / 测试矩阵 → [[../../README|README]] + [[../../CLAUDE|CLAUDE.md]]
- 故障诊断 / LangSmith trace / Studio H1-R2 验证矩阵 → [[[GUIDE]_Developer_Onboarding|Developer Onboarding]] §7

读完本份后下一站：跑通后回到 Developer Onboarding 补背景知识。

---

## §1 Step 1 — 装 Python 3.13

```bash
# 已装 Python 3.13 跳过
python --version           # 期望：Python 3.13.x
```

无 Python 3.13：Windows 用 `winget install Python.Python.3.13`；macOS `brew install python@3.13`；Linux 包管理对应 `python3.13`。

## §2 Step 2 — 装 uv

```bash
pip install uv
uv --version               # 期望：uv 0.5+ 或更新版本
```

## §3 Step 3 — Clone（PowerShell bare + worktree 脚本）

**在你打算放 mj-agent 仓库的父目录下**运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\mj-agent-clone-bare.ps1 `
    -RepoUrl https://github.com/MJ-AgentLab/mj-agent
```

脚本会创建：
```
mj-agent/
├── .bare/              # bare repo
├── .git                # gitdir 指针
└── develop/            # 默认 worktree
```

**验证**：

```bash
ls mj-agent/develop      # 应看到 README.md / pyproject.toml / src/ / docs/ ...
```

## §4 Step 4 — 进入 develop worktree

```bash
cd mj-agent/develop      # 后续所有命令在此目录运行
git status               # 期望：On branch develop / nothing to commit
```

## §5 Step 5 — uv sync 装依赖

```bash
uv sync                  # 装依赖 + 锁版本（首次约 1-3 分钟）
uv run python -c "import mj_agent; print('ok')"   # 期望：ok
```

## §6 Step 6 — 解密 secrets / 准备 .env + OS env（两 bundle）

```powershell
# App bundle → .env（-LlmProfile 选 LLM 套装：无 DGX 隧道的机器一律 ark）
.\scripts\setup-env.ps1 -LlmProfile ark
# 提示输入团队口令 → 自动解密 config/secrets.enc 注入 .env

# MCP bundle → OS User env（Claude Code 的 .mcp.json ${VAR} 消费；同一口令）
.\.claude\scripts\setup-mcp-secrets.ps1
# ⚠ 跑完必须【完全重启】终端 + Claude Code（User env 只对新进程可见）
```

无团队口令的 fallback：

```bash
cp .env.example .env
# 编辑 .env 手工填 ARK_API_KEY + POSTGRES_ANALYST_USER / PASSWORD（向项目负责人申请）
# 此路径没有 MCP secrets——Claude Code 的 ssh-manager / WAN pg MCP 起不来（app 本体不受影响）
```

## §7 Step 7 — mj-agent check 验 DB + LLM 凭据

```bash
uv run mj-agent check
# 期望输出：
#   db: ok
#   llm provider = ark (endpoint=https://ark.cn-beijing.volces.com/api/v3)
```

若 `db: skipped` → 检查 `POSTGRES_ANALYST_USER/PASSWORD`；若 `llm: LLMConfigError` → 检查 `ARK_API_KEY`。详见 §11。

## §8 Step 8 — 启动 LangGraph Studio

```bash
uv run langgraph dev
# 浏览器自动打开 http://127.0.0.1:2024（占用时换 --port 2025）
# 在 Studio 左侧 Graphs 列表选 "mj_agent"
```

## §9 Step 9 — Studio 首问验证

在 Studio 输入框问：

```
biz_dws 里有哪些日度总量表？
```

**期望 agent 行为**：

1. 调 `find_biz_context` 召回 catalog
2. 调 `list_biz_tables` 列出 `dws_qcm_*_daily_total` 系列表名
3. 回复含 5-10 个 `dws_qcm_*_daily_total` 表名清单

若 agent 不调工具直接幻觉回复，检查 `src/mj_agent/skills/biz-domain-context/SKILL.md` 是否加载（agent 启动日志应显示 3 个 active skill）。

---

## §10 速查表

| 任务 | 命令 |
| --- | --- |
| 装依赖 | `uv sync` |
| 启 Studio | `uv run langgraph dev` |
| Lint | `uv run ruff check` |
| Type-check | `uv run mypy src/mj_agent` |
| 单元测试 | `uv run pytest tests/unit` |

---

## §11 Troubleshooting

| 症状 | 一句修复 |
| --- | --- |
| `ARK_API_KEY` 缺失 / `LLMConfigError` | 跑 `setup-env.ps1`，或 `cp .env.example .env` 后手填 |
| 2024 端口占用 | `uv run langgraph dev --port 2025` |
| `psycopg.OperationalError` 连接超时 | 检查 `POSTGRES_*_HOST/PORT` + 上游业务系统 pg 网络可达 |
| `.env` 中文报错（python-dotenv UnicodeDecodeError） | `.env` 去中文注释；`.env.example` 保持 ASCII（[详见 CLAUDE.md §Environment](../../CLAUDE.md)）|
| `pytest tests/smoke` 全 skip | 预期；`conftest.py` 在凭据缺失时 skip 不 fail；smoke 默认排除 |
| PowerShell `ExecutionPolicy` 阻 | `powershell -ExecutionPolicy Bypass -File ...` 或临时 `Set-ExecutionPolicy -Scope Process Bypass` |
| `uv sync` 卡 deepseek/torch 包 | 公网代理 / 镜像源问题；可设 `UV_INDEX_URL` 切国内镜像 |

更深诊断（H1/H2/H3 happy path + R1/R2 red line）见 [[[GUIDE]_Developer_Onboarding|Developer Onboarding]] §7.3 诊断表。

---

## §12 关联文档

- [[[GUIDE]_Developer_Onboarding|Developer Onboarding（15 分钟完整版）]] — 概念 + 顺序 + 文档体系
- [[[GUIDE]_Analyst_Day_One|Analyst Day-One]] — 分析师角色 day-1（非开发者）
- [[../../README|README]] — 技术栈 / 命令矩阵 / 文档导航
- [[../../CLAUDE|CLAUDE.md]] — AI 高频上下文 / Commands / Architecture

## 更新记录

| 日期 | 版本 | 变更 |
| --- | --- | --- |
| 2026-05-18 | v0.1 | 初稿（借鉴 mj-system Quick_Start_Setup 9 步结构 + Troubleshooting 表写法；内容按 mj-agent 自身资产派生） |
| 2026-07-08 | v0.2 | #297 §6 补两 bundle 解密序列（setup-mcp-secrets + 完全重启说明）+ `-LlmProfile` 用法 + 无口令 fallback caveat。补记：#297 时 frontmatter 已 bump v0.2、body 版本行/本表漏跟（#302 追认对齐） |
