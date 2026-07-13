---
type: template
domain: WORKFLOW
summary: HITL Stage 3 Repo Scan Result 输出结构模板（对话输出，**不**写文件）；与 mj-agent-flow-repo-scan SKILL Output Format 一致
tags:
  - template
  - workflow
  - repo-scan
  - hitl-stage-3
aliases:
  - mj-agent Repo Scan Result Template
created: 2026-05-11
updated: 2026-05-11
state: draft
version: v0.1
track: shared
owner: 项目负责人
---

# TEMPLATE: Repo Scan Result（HITL Stage 3）

> **使用方法**：`/mj-agent-flow-repo-scan` 执行完成后，把下方 fenced markdown block 内容**复制为对话输出**（不写文件，per [[sdd/workflows/execution-loop|执行闭环 workflow]] Stage 3 Repo Scan Rules）。
>
> **何时复制本模板**：
> - 用户已有 Issue + branch，准备进 Stage 4 Plan / Stage 6 SPEC / Stage 8 实现
> - 用户请求"事实核查 / repo scan / Plan 是否成立 / Documentation Decision / 反向扫描"
>
> **不**用本模板：
> - 创建独立 `[REPO_SCAN_RESULT]_*.md` 文件（违反 §4.4 Rules：read-only 输出）
> - Stage 0 Intake 准入（用 mj-agent-flow-intake 输出 Intake Result）
> - Stage 9 实施中 scope drift 检测（用 mj-agent-flow-scope-drift）
>
> **关联**：[[sdd/workflows/execution-loop|执行闭环 workflow]] Stage 3 + `.claude/skills/mj-agent-flow-repo-scan/SKILL.md`（承载 8-dim 扫描详细步骤）。

---

## Repo Scan Result 模板

````markdown
## Repo Scan Result

- **Decision**: <Plan still valid / Plan needs update / Split issue / Need spike / Need HITL>
- **Risk Level**: <Low / Medium / High>（如升档：`Risk escalated: <旧> → <新>`，原因：<触及 §3.1 必停第 N 项>）
- **Next Step**: <Update Plan / Draft SPEC / Implement / Ask HITL / Create follow-up Issue>

## Current State

<3-5 句仓库事实摘要：当前 branch / diff 规模 / 已识别的关键 anchor>

## Evidence Map

| Area | Evidence | Notes |
|---|---|---|
| Issue / Plan | `gh issue view <num>` 摘要 / `plans/[PLAN]_*.md` 路径 | <一致性 / 冲突点> |
| Code (mj-agent 7 模块) | `git diff --name-only` 涉及 `src/mj_agent/{agent,llm,tools,memory,integrations,config,server,ui}/` | <主要改动模块> |
| API / Studio / Chainlit | `langgraph.json` / `src/mj_agent/ui.py` / `src/mj_agent/server/cli.py` 是否涉及 | <interface 变化> |
| Data Source (biz_catalog) | `qcm_catalog.yaml` diff / `find_biz_context` 真实返回 | <镜像漂移 = §3.1 必停 12> |
| Database — 上游业务系统 biz pg consumer | 4-tool 链（`find_biz_context` / `list_biz_tables` / `describe_biz_table`）/ 连接配置 | <红线 ADR-006/009 检查；禁 raw PG 直读> |
| Database — mj-agent-postgres memory | mcp pg-mj-agent-memory-* / compose exec psql | <自有 checkpointer 库，非 biz 边界对象> |
| Config / Secrets | `.env.example` / `secrets.enc` / `.mcp.json` 一致性 | <新增 var / 漂移> |
| Tests / CI | `tests/{unit,eval,integration,smoke,contract}/` + `.github/workflows/` | <覆盖度 / 失败> |
| Docs | `docs/**/*.md` + `INDEX.md` + `CLAUDE.md` + `CHANGELOG.md` | <反向扫描命中 / 同步需求> |

## Affected Areas

- **Modules**: <list of `src/mj_agent/<module>/` paths>
- **Code paths**: <具体函数 / 类 / 文件>
- **Studio**: <H1/H2/H3/R1/R2 矩阵中受影响项>
- **Database**: <biz pg / mj-agent-postgres 影响>
- **Config / CI / Docker**: <受影响项>
- **Docs**: <受影响 canonical 文档清单>

## Documentation Decision（§7.1 完整 10 行）

| Type | Action | Path | Existing Target | Reason | Evidence | Template Notes | Required Before |
|---|---|---|---|---|---|---|---|
| Plan | Create / Update / None | `plans/[PLAN]_*.md` | <现有路径或无> | <为什么需要> | <Issue / diff / grep 命中> | TEMPLATE_PLAN.md 6 段 | SPEC / Implementation |
| SPEC | Create / Update / None | `docs/design/{module}/[SPEC]_*.md` | … | <新接口 / 新表 / 行为变化> | <代码 / API / biz_catalog 证据> | TEMPLATE_SPEC.md 9 段；含 EVAL coverage 子段 | Implementation |
| ADR | Create / Update / None | `docs/adr/[ADR]_*.md` | … | <长期架构 / 数据边界 / CI 决策> | <冲突 / 备选 / 约束> | TEMPLATE_ADR.md；含 alternatives | SPEC / Implementation |
| RUNBOOK | Create / Update / None | `docs/runbook/[RUNBOOK]_*.md` 或 `docs/infrastructure/**/[RUNBOOK]_*.md` | … | <运维 / 回滚 / 排障> | <部署 / 容器 / Studio 证据> | TEMPLATE_RUNBOOK.md 7 段 | PR / Release |
| GUIDE | Create / Update / None | `docs/guide/` 或 `docs/infrastructure/**` | … | <开发者上手 / 操作路径> | <命令 / 工作流证据> | TEMPLATE_GUIDE.md CN-numbered | PR |
| STANDARD | Create / Update / None | `docs/rule/[STANDARD]_*_v1.0.md` | … | <长期规则 / 命名 / 治理 / 工程流程> | <规范冲突 / 重复证据> | MUST/SHOULD/MAY + version 必填 | PR |
| Local ISSUE | Create / Update / None | `docs/issues/[ISSUE]_*.md` | … | <中高风险长期知识锚点> | <证据 / 根因 / 影响> | TEMPLATE_ISSUE.md | Plan |
| ASSESSMENT | Create / Update / None | `docs/assessments/[ASSESSMENT]_*_v1.0.md` | … | <优化后基线对比> | <基线 / 指标证据> | TEMPLATE_ASSESSMENT.md | Post-implementation |
| CHANGELOG | Update / None | `CHANGELOG.md` | … | <user-visible / release> | <行为 / 发布证据> | 仅 user-visible 或 release | Commit / PR |
| INDEX | Update / Regenerate / None | `docs/INDEX.md` 或 `docs/**/INDEX.md` | … | <新增 / 迁移 canonical> | <新文档路径 / 入口变更> | canonical 入口必须同步 | PR |

## Stale Doc Reverse Scan（§7.2.1，mj-agent 扩展）

- **已扫改动类型**：<rename / move / SQL-rename / DDD-restructure / internal-opt / biz_catalog-drift / runtime-canonical-change / N/A>
- **命中文档**：<列入 Documentation Decision Update 行 / 无命中 / 不涉及>
- **grep 证据**：`<命令 + 命中行号>`
- **biz_catalog drift status**：`<scripts/diff_biz_schema.py 输出 / N/A>`
- **runtime canonical 反向扫描结果**：<src/mj_agent/skills/**/SKILL.md + src/mj_agent/prompts/*.md 中 backtick 引用命中清单 / 无命中>

## SPEC Type & Checklist（仅当 Documentation Decision 中 SPEC = Create / Update）

- **任务类型**（按 [[../guide/[GUIDE]_MJ_Agent_SPEC_Authoring|SPEC Authoring GUIDE]] §4 识别）：<1 Python 应用代码 / 2 SQL guardrail / 3 In-source canonical / 4 Docker compose / 5 CI/CD scripts / 6 Config secrets / 7 Engineering-workflow infra / 8 文档治理>
- **必填段**：<按任务类型从 GUIDE §4.X 列出>
- **可选 / 不涉及段**：<按任务类型显式标注>

## Plan Verdict

- **是否成立**：<是 / 否 / 部分>
- **需写回 Plan 的内容**：<具体 §X.Y 改动建议；无则写"无变更">

## Verification Plan

### Level A 只读检查（必跑）

```bash
uv run ruff check
uv run mypy src/mj_agent
uv run pytest tests/unit
uv run pytest tests/eval
python -m compileall src
python scripts/check_wikilinks.py    # 文档变更时
python scripts/check_frontmatter.py  # 文档变更时
```

### Level B HITL-confirm（按需）

```bash
uv run pytest tests/integration       # 需 POSTGRES_ANALYST_USER
uv run pytest tests/smoke -m smoke    # 需 ARK_API_KEY；CI 不跑
uv run mj-agent check                 # DB + LLM creds 健康
uv run langgraph dev                  # Studio 探针 H1/H2/H3/R1/R2
docker compose -f docker/compose.yaml up -d
```

### Checks not run and why

<显式说明：环境缺 creds / 改动不涉及 / HITL 未批>

## HITL Questions（§3.3 7-段格式；仅 Risk = Medium/High 或多方案取舍时输出，最多 3-5 个）

```
问题 N：
- 当前观察：
- 不确定点：
- 为什么重要：
- 可选方案：A. / B. / C.
- 我的建议：
- 默认假设：
- 是否必须等待人工确认：是 / 否
```

## Next Step Context

- <交给 Stage 4 Plan / Stage 6 SPEC / Stage 8 Implementation 的执行上下文摘要>
- <若需 follow-up Issue：标题 + body 草稿>
````

---

## 字段说明

| 字段 | 说明 |
|---|---|
| `Decision` | 5 选 1：Plan still valid / needs update / Split / Need spike / Need HITL |
| `Risk Level` | Low / Medium / High；如触发 §3.1 必停 4 项 mj-agent 专属 → 自动 High |
| `Next Step` | 明确下一阶段动作（不要只写"继续"） |
| `Evidence Map` | 8 行 8-dim 全填；不涉及的写 "不涉及（理由：...）" |
| `Documentation Decision` | 10 行全填，None 占位即可 |
| `Stale Doc Reverse Scan` | mj-agent 扩展 7 类改动 + biz_catalog drift + runtime canonical 反向扫描 |

---

## 关联文档

- [[sdd/workflows/execution-loop|执行闭环 workflow]] Stage 3（Repo Scan）
- `.claude/skills/mj-agent-flow-repo-scan/SKILL.md`（承载 8-dim 扫描完整步骤）
- [[../guide/[GUIDE]_MJ_Agent_SPEC_Authoring|SPEC Authoring GUIDE]]（如 SPEC = Create/Update 时使用）

## 更新记录

| 日期 | 版本 | 变更 |
| --- | --- | --- |
| 2026-05-11 | v0.1 | 初稿（PR-118 commit-3 落地；G1 gap 修复） |
