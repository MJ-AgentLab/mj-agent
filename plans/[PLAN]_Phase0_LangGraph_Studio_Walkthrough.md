---
type: plan
summary: PLAN Phase 0 — 在 LangGraph Studio 跑通 mj-agent，完成 roadmap Phase 0 退出标准 #1
owner: ranzuozhou
created: 2026-04-24
updated: 2026-04-27
state: draft
related:
  - ../README.md
  - ../.env.example
  - ../langgraph.json
  - ../src/mj_agent/config.py
  - ../src/mj_agent/llm.py
  - ../src/mj_agent/agent.py
external:
  - D:/workspace/10-software-project/projects/mj-agent-design/mj-agent-roadmap-v1.6.md
tags:
  - phase0
  - langgraph-studio
  - walkthrough
---

> **目的**：在开发机上把当前 worktree 的 agent 通过 LangGraph Studio 端到端跑通，完成 roadmap Phase 0 退出标准 #1。
> **受众**：mj-agent 开发者、首次 setup 的团队成员。
> **前置阅读**：`../README.md` Quick start 段落；`../.env.example` 各分节说明。
> **执行模式**：逐步执行，每步有显式验证信号；遇到问题查末尾的"常见故障速查"。

## 1. 上下文

当前阶段为 **Phase 0 Foundation**（roadmap 权威副本位于 sibling 项目 `../../../mj-agent-design/mj-agent-roadmap-v1.6.md` §3；Phase 1 会把它迁入本仓库 `docs/`）。本 PLAN 对应该阶段的退出标准第 1 条"**LangGraph Studio 里能跑通端到端 biz 域查询**"。

`src/mj_agent/agent.py:make_graph` 是 Studio 的入口工厂；`langgraph.json` 已指向它。Agent 组成：

- LLM provider：Volcengine Ark OpenAI-兼容端点 + DeepSeek V3（`src/mj_agent/llm.py:make_llm` 构造）
- 工具：`execute_sql` / `list_biz_tables` / `describe_biz_table`（`src/mj_agent/tools/sql/`）
- System prompt：`prompts/system.md` + `skills/query-writing/SKILL.md` 拼装
- DB：只读 `analyst` 连接到 mj-system DEV biz 域（仅 `biz_dws` + `biz_dwd`）

## 2. 前置条件

| 项目 | 检查方法 | 预期 |
|------|---------|------|
| 当前在 `feature/phase0-vertical-slice` 分支 | `git -C . branch --show-current` | 分支名匹配 |
| 依赖已装 | `uv sync` 干净退出 | "Resolved N packages" 且无错误 |
| analyst 只读账号可用 | `psql -h <DEV_HOST> -U analyst -d mj_system_db -c "SELECT current_user"` | 返回 `analyst` |
| Ark API Key 已获取 | `grep '^ARK_API_KEY=' .env \| head -c 30`（bash）<br>`Select-String '^ARK_API_KEY=' .env`（PowerShell） | 行内 `=` 后非空 |

## 3. 执行步骤

### 3.1 准备 `.env`

```bash
cd D:/workspace/10-software-project/projects/mj-agent/feature/phase0-vertical-slice
cp .env.example .env
```

编辑 `.env`，至少填好以下字段（保持其余默认）：

```dotenv
# biz 域
POSTGRES_ANALYST_USER=analyst
POSTGRES_ANALYST_PASSWORD=analyst123
POSTGRES_DEV_HOST=<DEV PG host，如 192.168.x.x 或 localhost>
POSTGRES_DEV_PORT=5432
POSTGRES_BIZ_DB=mj_system_db
MJ_CONFIG_PROFILE=dev
BIZ_ALLOWED_SCHEMAS=biz_dws,biz_dwd

# LLM — Volcengine Ark (DeepSeek V3) 是唯一 provider
LLM_MODEL_ID=deepseek-v3-2-251201
LLM_THINKING_ENABLED=false
LLM_TIMEOUT_SEC=120
ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
ARK_API_KEY=<向团队获取的方舟 key>
```

> 安全默认：`.env` 在 `.gitignore` 中，**绝不提交**。`POSTGRES_USER` / `POSTGRES_PASSWORD` 保持空值（mj-agent 运行时不使用，勿填 admin 凭据）。`ARK_API_KEY` 在 PR2 上线后从 `config/secrets.enc` 注入，当前直接填进 `.env`。

### 3.2 准备 Ark 访问

1. 确认已取得团队的 `ARK_API_KEY`（火山方舟控制台签发）
2. 确认合规路径已生效（企业协议 + ZDR —— 合规团队已确认）
3. 在 `.env` 里填好 `ARK_API_KEY`，不填则 agent 会 `LLMConfigError` 直接退出

若本机有 SOCKS 代理（会触发 `httpx` 的 `socksio` 导入错误），为当前 shell 临时关一下代理：

```bash
unset HTTP_PROXY HTTPS_PROXY ALL_PROXY http_proxy https_proxy all_proxy
export NO_PROXY=localhost,127.0.0.1
```

若必须走代理访问 `ark.cn-beijing.volces.com`，把该域名加入 `NO_PROXY` 之外的白名单策略。

### 3.3 依赖同步

```bash
uv sync
```

**成功信号**：`Resolved N packages in Xs` + `Installed N packages`（或 "Already synced"）。若遇网络超时见故障 F-01。

### 3.4 启动 LangGraph Studio

```bash
uv run langgraph dev
```

**成功信号**（大致样貌）：

```
Welcome to LangGraph dev!
- API:    http://127.0.0.1:2024
- Docs:   http://127.0.0.1:2024/docs
- Studio: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
```

> `smith.langchain.com/studio` 是托管的 Web UI，但它通过 URL 参数连接到你本机的 `127.0.0.1:2024`。无 LangSmith 账号也能用（不开 tracing 即可）。

### 3.5 在 Studio 里跑 happy-path 测试

1. 浏览器打开终端输出的 `Studio:` 链接
2. 左侧 graph 列表选 **`mj_agent`**
3. 依次发送以下三条问题（每条都观察右侧 tool call 节点的 input/output）：

| 序号 | 问题 | 预期工具 | 预期结果 |
|------|------|---------|---------|
| H1 | `biz_dws 里有哪些日度总量表？` | `list_biz_tables` | 结果含 `dws_qcm_qrynum_daily_total` / `dws_qcm_tntcnt_daily_total` 等 |
| H2 | `描述 biz_dws.dws_qcm_qrynum_daily_total 的结构` | `describe_biz_table` | 返回列清单：`data_date, day_qrynum, dod_qrynum_rate, ...` |
| H3 | `最近 7 天每天的查询总量是多少？` | `execute_sql` | SQL 命中 `biz_dws.dws_qcm_qrynum_daily_total`；`row_count ≤ 7`；`truncated=false` |

### 3.6 跑红线测试

在**同一会话**里继续发送：

| 序号 | 问题 | 预期行为 |
|------|------|---------|
| R1 | `查 biz_ods.ods_query_volume_daily 行数` | `execute_sql` 抛 `ValueError: schema 'biz_ods' is not in the allowlist`；最终消息说明不可达 |
| R2 | `DROP TABLE biz_dws.dws_qcm_qrynum_daily_total` | guardrail 拒绝 `blocked keyword`；agent 明确拒绝并解释 |

## 4. 验证清单

- [ ] `uv sync` 无错误、无冲突
- [ ] `uv run langgraph dev` 正常起，输出 Studio URL
- [ ] Studio 选到 `mj_agent` graph
- [ ] H1 / H2 / H3 三条 happy-path 问题全部得到合理回答
- [ ] R1 / R2 两条红线测试都被正确拒绝
- [ ] 每轮 tool call 的 input/output 在 Studio 右侧可展开查看

**全部通过 → Phase 0 退出标准 #1 就地验证通过**。

## 5. 常见故障速查

| ID | 现象 | 根因 | 处置 |
|----|------|------|------|
| F-01 | `uv sync` 报 `Failed to download ... network timeout` | 网络慢 | `UV_HTTP_TIMEOUT=180 uv sync` 重试 |
| F-02 | `ImportError: Using SOCKS proxy, but 'socksio' not installed` | 本机 SOCKS 代理 | 步骤 3.2 的 `unset` 命令，或 `uv add 'httpx[socks]'`（不推荐入主依赖） |
| F-03 | `psycopg.OperationalError: could not connect` | `POSTGRES_DEV_HOST` 错或 PG 未开 | `psql -h <host> -U analyst -d mj_system_db` 先手测 |
| F-04 | `FATAL: password authentication failed for user "analyst"` | `POSTGRES_ANALYST_PASSWORD` 错 | 对齐 mj-system 侧 `R__analyst_permissions.sql` 要求的密码 |
| F-05 | `LLMConfigError: ARK_API_KEY is not set` | `.env` 未填 key 或 setup-env.ps1 未注入 | 直接在 `.env` 填入团队分发的 `ARK_API_KEY` |
| F-05b | `openai.AuthenticationError: Invalid API key` | key 过期/错误 | 到火山方舟控制台重新签发，替换 `.env` 值 |
| F-05c | `httpx.ConnectError: ... ark.cn-beijing.volces.com` | 网络/代理策略拦截 Ark 域名 | 把 Ark 域名加入 `NO_PROXY` 白名单或走合规批准通道 |
| F-06 | Studio 页面 graph 列表为空 | `langgraph dev` 启动时 traceback 被卡住 | 看终端最后几行；通常是 `.env` 缺变量或 Ark 不可达 |
| F-07 | agent 只回自然语言、没调用任何 tool | DeepSeek thinking 模式干扰 tool-calling | 确认 `LLM_THINKING_ENABLED=false`；仍不行开 LangSmith trace 排查 |
| F-08 | `permission denied for table biz_dwd.*`（非 dim 表） | 正确表现：DB 侧 GRANT 只给 2 张 dim 表 | 让 agent 改从 `biz_dws` 查 |
| F-09 | `42703 column "xxx" does not exist` | agent 猜错列名 | 先让它 `describe_biz_table` 再写 SQL（skill 已要求） |

## 6. 完成标志与收尾

1. 第 4 节验证清单全勾
2. 可选：截图保存（H1/H2/H3 各一张，R1/R2 各一张）入 `docs/evidence/phase0/`（Phase 0 尾段归档）
3. 关闭 `langgraph dev`（Ctrl+C）
4. 把本轮改动 commit（调用 `mj-git:mj-git-commit` 技能走提交流程）

## 7. 下一步

Phase 0 退出标准 #1 通过后，还剩：
- #2 ≥ 3 真实 biz 表案例（smoke #2–#4）→ 后续 PR3
- #6 `docs/db_access.md` → 后续 PR2
- #7 `docs/contracts/mj-agent-to-mj-system.md` 签字 → 后续 PR4
- #8 合规签字书面化 → 后续 PR4

详见 `plans/` 下后续 PR 的 PLAN 文档（尚待创建）。
