---
type: plan
summary: PLAN A — 执行 LangGraph Studio Walkthrough 并归档证据，完成 Phase 0 退出标准 #1
owner: ranzuozhou
created: 2026-04-24
updated: 2026-04-27
state: draft
related:
  - ./[PLAN]_Phase0_LangGraph_Studio_Walkthrough.md
  - ../README.md
  - ../.env.example
  - ../langgraph.json
  - ../src/mj_agent/agent.py
external:
  - D:/workspace/10-software-project/projects/mj-agent-design/mj-agent-roadmap-v1.6.md
tags:
  - phase0
  - walkthrough
  - execution
  - evidence
---

> **目的**：把 `[PLAN]_Phase0_LangGraph_Studio_Walkthrough.md` 跑一遍，并把可复核的证据落进仓库，完成 Phase 0 退出标准 #1。
> **受众**：首次执行该退出标准的工程师。
> **前置阅读**：参考 walkthrough PLAN（操作细节以它为准，本文件只管"执行 + 归档 + PR"）。

## 1. 范围

| 做什么 | 不做什么 |
|---|---|
| 在本机按 walkthrough §3 端到端跑一次 | 修改 agent 代码（guardrail / 工具 / prompt） |
| H1-H3 happy-path + R1-R2 红线各留一份证据 | 补 smoke #2–#4（那是 PLAN C1） |
| 发现 walkthrough 文档有错当场修正 | 同 PR 改 `.env.example` 以外的配置规范（另开 maintain PR） |

## 2. 前置条件

| 项 | 必需 | 验证方式 |
|---|---|---|
| Ark API Key | ✅ | 写进本机 `.env` 后 `uv run python -c "from mj_agent.llm import make_llm; make_llm()"` 不抛 `LLMConfigError` |
| DEV PG `analyst` 可达 | ✅ | `psql -h $POSTGRES_DEV_HOST -U analyst -d mj_system_db -c "SELECT 1"` 返回 1 |
| `mj-system` 已在 DEV 跑过 `R__analyst_permissions.sql` | ✅ | `biz_dws` 下能 SELECT，`biz_ods` 下 permission denied |
| 合规/ZDR 路径仍然有效 | ✅ | 合规签字记录（见 PR4） |

任一不满足 → 切到 **PLAN B**（纯文档，无外部依赖）。

## 3. 分支与 worktree

```bash
git -C develop worktree add ../feature/studio-walkthrough-evidence \
  -b feature/studio-walkthrough-evidence develop
```

> 当前 `documentation/phase0-next-plans` 分支只装计划文档，**不**在这里跑 walkthrough。

## 4. 执行步骤

### 4.1 本机准备

严格按 walkthrough `§3.1–3.3` 操作：复制 `.env.example` → 填 Ark key / PG / 模型 id → `uv sync`。

> `.env` 仍然 **禁止** 提交。本 PR 的 diff 只包含 `docs/evidence/phase0/**` 和（若需要）walkthrough 文档的修正。

### 4.2 跑 Studio

按 walkthrough `§3.4–3.6` 启 `uv run langgraph dev`，依次发送 H1/H2/H3/R1/R2。

### 4.3 证据归档

目录：`docs/evidence/phase0/studio-walkthrough-<YYYYMMDD>/`

需要的文件：

| 文件 | 内容 |
|---|---|
| `h1_list_biz_tables.png` | Studio 右侧 tool call 展开 + 最终回答截图 |
| `h1_list_biz_tables.md` | tool input / output JSON 摘要 + 用时 + 模型 id |
| `h2_describe.png` / `.md` | 同上，工具 `describe_biz_table` |
| `h3_execute_sql.png` / `.md` | 同上，工具 `execute_sql`；`.md` 里**原样粘贴** SQL，断言 `row_count ≤ 7` 且 `truncated=false` |
| `r1_schema_blocked.png` / `.md` | 截到 allowlist ValueError + agent 的用户级解释 |
| `r2_guardrail_blocked.png` / `.md` | 截到 guardrail `blocked keyword` + agent 拒绝 |
| `session_log.md` | 时间戳、模型 id、Ark region、`.env` **脱敏**摘要（没有 key / host / 密码） |

> `session_log.md` 是给将来回溯用的——PR 合进后凭据、主机名会过期，这份脱敏摘要是唯一还能看的元数据。

### 4.4 walkthrough 文档纠偏（如需要）

发现 walkthrough 和实际不符（比如故障速查表漏了一种现象）→ 同 PR 直接改 `[PLAN]_Phase0_LangGraph_Studio_Walkthrough.md`，commit 单独记：

```
docs(walkthrough): 补 F-10 <现象> <根因> <处置>
```

### 4.5 CHANGELOG

在 `CHANGELOG.md` 的 *Unreleased* 段加：

```
- phase0: LangGraph Studio walkthrough evidence captured (exit criterion #1)
```

## 5. 验证清单

- [ ] H1/H2/H3 各一张截图 + 一份摘要
- [ ] R1/R2 各一张截图 + 一份摘要
- [ ] `session_log.md` 含时间戳、模型 id、Ark region
- [ ] walkthrough `§4` 验证清单在 session_log 里逐条标注 ✅
- [ ] 没有凭据泄漏（`rg -n 'ARK_API_KEY|password|analyst123' docs/evidence/` 为空）
- [ ] `CHANGELOG.md` 已更新

## 6. 退路

| 触发 | 切到 |
|---|---|
| Ark 域名被代理拦 / key 无效 | 先做 PLAN B（纯文档） |
| DEV PG 不可达 | 先做 PLAN B；同时在 mj-system 侧起 issue 跟进 `R__analyst_permissions.sql` 上线 |
| Studio 启不起来 / graph 列表空 | 参 walkthrough F-06；仍不行 → 单开 `bugfix/` 分支修 agent 启动路径 |

## 7. PR 流程

- 调用 `mj-git:mj-git-commit` 做 Conventional Commits；每类改动单独 commit：
  - `docs(phase0): add Studio walkthrough evidence`
  - `docs(walkthrough): <如需修订>`
  - `chore(changelog): phase0 exit #1`
- 调用 `mj-git:mj-git-pr` 开 PR，使用 `.github/PULL_REQUEST_TEMPLATE/documentation.md`
- PR 描述里必须链接：
  - 本 PLAN（`plans/[PLAN]_A_Studio_Walkthrough_Execution.md`）
  - walkthrough PLAN
  - roadmap Phase 0 §3 退出标准 #1

## 8. 收尾

合并后：

1. `git worktree remove feature/studio-walkthrough-evidence`
2. 在本 PLAN 顶部 frontmatter 把 `status: 草案` 改成 `status: 已执行 <日期> <PR#>`（或删除本 PLAN，留到归档目录）
