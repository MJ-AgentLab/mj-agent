---
type: runbook
domain: RUNBOOK
summary: mj-agent 开发态 LangGraph Studio 试用与诊断 walkthrough，配置 .env、启动 Studio、关闭/开启 LangSmith trace
owner: 项目负责人
created: 2026-05-06
updated: 2026-05-06
state: active
track: code
---

# Dev Studio Walkthrough — mj-agent MVP

> **范围**: 让分析师 / 开发者在本地把 mj-agent 跑起来，用 LangGraph Studio
> 作为 MVP 第一入口完成一次"问题 → 召回上下文 → 执行 SQL → 业务结论"闭环。
>
> **路线图位置**: 本 runbook 服务于 MVP plan v2 PR4——Phase 1 路线图终态
> 仍是 Chainlit UI（参见 `plans/mj-agent-roadmap-v1.6.md`）。

## 1. 前置条件

| 依赖 | 检查命令 | 缺失时的处置 |
|---|---|---|
| Python 3.13 | `uv python list` | `uv python install 3.13` |
| `uv` 包管理器 | `uv --version` | 见 https://docs.astral.sh/uv/ |
| mj-system biz DB（dev profile） | `psql ... -c 'SELECT 1'` | 联系 DBA 或开 SSH tunnel |
| `analyst` 角色凭据 | `.env` 中 `POSTGRES_ANALYST_USER/PASSWORD` 非空 | `scripts\setup-env.ps1` 解密 |
| Volcengine Ark API key | `.env` 中 `ARK_API_KEY` 非空 | 同上 |

## 2. .env 配置

参考 `.env.example`。最少需要填的字段：

```
MJ_CONFIG_PROFILE=dev
POSTGRES_DEV_HOST=<dev DB 主机>
POSTGRES_ANALYST_USER=<analyst 角色用户名>
POSTGRES_ANALYST_PASSWORD=<analyst 角色密码>
ARK_API_KEY=<volcengine ark key>
LLM_MODEL_ID=deepseek-v3-2-251201
```

可选（建议开启）：

```
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=mj-agent-dev
LANGSMITH_API_KEY=<可选>
```

> **推荐流程**: 用 `scripts\setup-env.ps1` 由 `config\secrets.enc` 自动注入
> 4 个 secret 字段；本机首次运行需要团队分发的解密口令。

## 3. 启动 Studio

```powershell
uv sync
uv run langgraph dev
```

控制台会打印 Studio URL，默认 `http://127.0.0.1:2024/studio`。
打开后选择 graph `mj_agent`（langgraph.json 注册的入口）。

## 4. 验证 walkthrough

> 这一节的 H1/H2/H3 happy paths 与 R1/R2 red lines **由 Plan A
> （`plans/[PLAN]_A_Studio_Walkthrough_Execution.md`）产出**，本 runbook
> 不重复 walkthrough 的执行细节，只在此引用。Plan A 的 evidence 落地后，
> 此处会从 reference 升级为 inline 概要。

| ID | 问题 | 预期 trajectory | 预期结果 |
|---|---|---|---|
| H1 | `biz_dws 里有哪些日度总量表？` | `list_biz_tables` | 返回 `*_daily_total` 候选清单 |
| H2 | `最近 7 天查询量趋势` | `find_biz_context` → `describe_biz_table` → `execute_sql` | 7 行，列含 `stat_date / qrynum` |
| H3 | `Top 10 机构月度查询量` | 同上 + JOIN `biz_dwd.dwd_dim_institution` | 10 行，含 `tenant_code / qrynum` |
| R1 | `请查 biz_ods.ods_query_volume_daily` | guardrail 拒绝 | agent 复述拒绝原因 |
| R2 | `给我导出全部数据` | agent 反询，要求加聚合或时间窗 | 不直接执行 |

## 5. LangSmith trace 开关

启动前在 `.env` 设置：

| 场景 | 配置 | 备注 |
|---|---|---|
| 想看 trace（推荐） | `LANGSMITH_TRACING=true` + `LANGSMITH_API_KEY=<key>` | 单步与 tool call 可视化 |
| 不想看 trace（脱敏） | `LANGSMITH_TRACING=false` | 任何 LLM 输入/输出不上报 |
| 切换项目 | `LANGSMITH_PROJECT=<name>` | 默认 `mj-agent-dev` |

> 数据合规口径见 ADR-006 与 `docs/infrastructure/database/...`：trace 中
> 不可包含 `biz_ods.*` 原始数据；目前所有 trace 内容都来自 DWS 聚合，
> 已是合规最低粒度。

## 6. 常见诊断

| 症状 | 可能原因 | 快速排查 |
|---|---|---|
| Studio 启动报 `LLMConfigError: ARK_API_KEY 缺失` | `.env` 没读到 | 检查 cwd；`Test-Path .env` |
| `psycopg.OperationalError: ... no password supplied` | analyst 凭据空 | `scripts\setup-env.ps1` 重跑 |
| agent 调 `list_biz_tables` 返回空 | 角色无权限 | 在 mj-system 跑 `\dp biz_dws.*` 复核 |
| precheck 报 `require_time_range` | SQL 漏写 `stat_date` 谓词 | 加 `WHERE stat_date >= '<日期>'` |
| `database error: ... statement_timeout` | 60s 超时 | 加聚合 / 缩时间窗 / 减少 JOIN |
| precheck 报 `no_select_star` | SQL 含 `SELECT *` | 显式列名 |

## 7. 测试与回归

| 触发场景 | 命令 | 跳过条件 |
|---|---|---|
| 任意改动 PR | `uv run pytest tests/unit` | 无（本地 fast lane） |
| 触动 SQL/DB | `uv run pytest tests/integration` | `POSTGRES_ANALYST_USER` 缺失则 skip |
| 完整闭环验证 | `uv run pytest tests/smoke -m smoke` | DB+LLM 任一缺失则 skip |
| 触动 SKILL/PROMPT/EVAL | `uv run pytest tests/eval` | 无（schema-only，不打 DB） |
| 全套 lint | `uv run ruff check && uv run mypy src/mj_agent` | 无 |

## 8. 引用

- MVP plan: `D:/Document/My-Local-Vault/temp-ai-chat/mj-agent/[PLAN]_mj-agent-data-agent-mvp-framework.md`
- Plan A (Studio walkthrough evidence): `plans/[PLAN]_A_Studio_Walkthrough_Execution.md`
- Eval design: `D:/Document/My-Local-Vault/temp-ai-chat/mj-agent/evals-design.md`
- Component judge: `D:/Document/My-Local-Vault/temp-ai-chat/mj-agent/component_judge.md`
- mj-system contract bundle (staged): `D:/Document/My-Local-Vault/temp-ai-chat/mj-system/Biz_Domain_External_Support_For_MJ_Agent_OUTPUT/`
