---
type: template
domain: WORKFLOW
summary: HITL Stage 3 Repo Scan Result 输出结构模板（默认对话输出；明确需要保存时用真实 working 类型）；与 mj-agent-flow-repo-scan SKILL Output Format 一致
tags:
  - template
  - workflow
  - repo-scan
  - hitl-stage-3
aliases:
  - mj-agent Repo Scan Result Template
created: 2026-05-11
updated: 2026-10-29
state: draft
version: v0.2
track: shared
owner: 项目负责人
---

# TEMPLATE: Repo Scan Result（HITL Stage 3）

> **使用方法**：`/mj-agent-flow-repo-scan` 执行完成后，把下方 fenced markdown block 内容**复制为对话输出**。明确需要保存时才用 `plans/<topic>/` 下真实类型的 Report/Assessment，不造专用 RepoScan 类型或重复主归属。
>
> **何时复制本模板**：
> - 用户已有 Issue + branch，准备进 Stage 4 Plan / Stage 6 SPEC / Stage 8 实现
> - 用户请求"事实核查 / repo scan / Plan 是否成立 / Documentation Decision / 反向扫描"
>
> **不**用本模板：
> - 未获保存请求便自动创建独立 `[REPO_SCAN_RESULT]_*.md` 文件；默认对话输出，不要求所有结果落盘
> - Stage 0 Intake 准入（用 mj-agent-flow-intake 输出 Intake Result）
> - Stage 9 实施中 scope drift 检测（用 mj-agent-flow-scope-drift）
>
> **关联**：[[sdd/workflows/execution-loop|执行闭环 workflow]] Stage 3 + `.agents/skills/mj-agent-flow-repo-scan/SKILL.md`（承载 8-dim 扫描详细步骤）。

---

## Repo Scan Result 模板

````markdown
## Repo Scan Result

- **Decision**: <Plan still valid / Plan needs update / Split issue / Need spike / Need HITL>
- **Risk Level**: <Low / Medium / High>（如升档：`Risk escalated: <旧> → <新>`，原因：<真实影响的canonical风险标签>）
- **Next Step**: <Update Plan / Draft SPEC / Implement / Ask HITL / Create follow-up Issue>

## Current State

<3-5 句仓库事实摘要：当前 branch / diff 规模 / 已识别的关键 anchor>

## Evidence Map

| Area | Evidence | Notes |
|---|---|---|
| Issue / Plan | `gh issue view <num>` 摘要 / `plans/<topic>/[PLAN]_<topic>.md`（兼容旧根文件）路径 | <一致性 / 冲突点> |
| Code (mj-agent 7 模块) | `git diff --name-only` 涉及 `src/mj_agent/{agent,llm,tools,memory,integrations,config,server,ui}/` | <主要改动模块> |
| API / Studio / Chainlit | `langgraph.json` / `src/mj_agent/ui.py` / `src/mj_agent/server/cli.py` 是否涉及 | <interface 变化> |
| Data Source (biz_catalog) | `qcm_catalog.yaml` diff / `find_biz_context` 真实返回 | <镜像漂移 = §3.1 必停面 biz-catalog-sync> |
| Database — 上游业务系统 biz pg consumer | 4-tool 链（`find_biz_context` / `list_biz_tables` / `describe_biz_table`）/ 连接配置 | <红线 ADR-006/009 检查；禁 raw PG 直读> |
| Database — mj-agent-postgres memory | 离线代码/契约；真实 memory 操作另核具名授权 | <自有 checkpointer 库，非 biz 边界对象> |
| Config / Secrets | 公开变量名/非秘密配置元数据；禁止读取 `.env`、secrets bundle 或真实凭据 | <新增 var / 漂移> |
| Tests / CI | `tests/{unit,eval,integration,smoke,contract}/` + `.github/workflows/` | <覆盖度 / 失败> |
| Docs | `docs/**/*.md` + `INDEX.md` + `AGENTS.md` + `CHANGELOG.md` | <反向扫描命中 / 同步需求> |

## Affected Areas

- **Modules**: <list of `src/mj_agent/<module>/` paths>
- **Code paths**: <具体函数 / 类 / 文件>
- **Studio**: <H1/H2/H3/R1/R2 矩阵中受影响项>
- **Database**: <biz pg / mj-agent-postgres 影响>
- **Config / CI / Docker**: <受影响项>
- **Docs**: <受影响 canonical 文档清单>

## Documentation Decision（按实际受影响对象）

缺口评估只说明 Create / Update / None、路径、理由和先后条件，不代写完整 Plan。下表为关注对象提示，按实际类型补充/合并；不以固定十类表格证明完整性。每个实际受影响对象须有结论。

| 对象/类型 | Action | 真实归属与现有目标 | 理由/证据 | 模板/先后条件 |
|---|---|---|---|---|
| 原意正本 | Create / Update / None | 独立 `docs/intent/[INTENT]_INT-YYYY-NNN_<English_Topic>.md` 或真实 Issue 原意区 | 来源/责任与本次承担范围 | TEMPLATE_INTENT；不明仅 working 草稿 |
| Intake | Create / Update / None | `plans/<topic>/[INTAKE]_<topic>.md` | 需求澄清与执行范围 | TEMPLATE_INTAKE；可先于或无 Plan |
| 主 Plan / 子 Plan | Create / Update / None | `plans/<topic>/[PLAN]_<topic>.md`；子 Plan 独立目录 | 实施、依赖、完整基线/授权和验证 | TEMPLATE_PLAN；新建 draft |
| Report / working Assessment | Create / Update / None | `plans/<topic>/` 按用途命名 | 真实结论/证据/限制；共享材料唯一归属 | TEMPLATE_REPORT / ASSESSMENT轻量分支 |
| SPEC | Create / Update / None | `docs/design/**/[SPEC]_*.md` 或所属归属 | 行为/接口/口径承诺 | TEMPLATE_SPEC；实现前契约 |
| ADR / policy | Create / Update / None | `decisions/ADR-NNN_*.md` / 既有 kernel policy | 长期取舍与规则；不改旧 accepted ADR 的历史决定 | ADR先查活动与归档编号 |
| GUIDE / RUNBOOK / STANDARD | Create / Update / None | 按真实主题就近归属 | 使用/操作/规范入口 | 对应模板，避免复制第二套真相源 |
| ISSUE / canonical Assessment / EVAL / runtime文档 | Create / Update / None | 按真实类型/契约归属 | 实际变更需求 | 对应模板和专属边界，不机械转 working |
| CHANGELOG / INDEX / AGENTS | Update / None | 实际入口 | 变更说明/导航/允许缓存项 | canonical入口同步；working不强制INDEX |

## 原意与布局事实

- 正本准确位置/完整适用基线、本次实际交付/依赖/背景：
- 真实主要 Issue/整体集成主要 PR；未明确主要 PR 省 P，不猜分支数字或最新 PR：
- 新旧布局、无 Plan 独立任务、共享/子 Plan、活动引用与冻结历史分离：
- 结构 PASS 不证明真实关联、语义忠实或接受；冲突/未决列责任和恢复点。

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
uv run --frozen --no-sync python scripts/sdd/run_offline_pytest.py tests/unit
uv run --frozen --no-sync python scripts/sdd/run_offline_pytest.py tests/eval
python -m compileall src
python scripts/check_wikilinks.py    # 文档变更时
python scripts/check_frontmatter.py  # 文档变更时
python scripts/check_working_docs.py # 新目录、主Plan与按文件位置解析的深相对链接
python scripts/sdd/check_codex_native.py
python scripts/sdd/check_native_skills.py
```

### Level B HITL-confirm（按需）

```bash
uv run --frozen --no-sync python scripts/sdd/run_offline_pytest.py tests/integration
uv run --frozen --no-sync python scripts/sdd/run_offline_pytest.py tests/smoke -m smoke
# 外部依赖始终 SKIP_POLICY_EXTERNAL_DEPENDENCY，凭据不启用外部测试
uv run mj-agent check                 # DB + LLM creds 健康
uv run langgraph dev                  # Studio 探针 H1/H2/H3/R1/R2
docker compose -f docker/compose.yaml up -d
```

### Checks not run and why

<显式说明：环境缺 creds / 改动不涉及 / HITL 未批>

## 未决的实质问题（已定方案不重问；技术事实自主查）

```
问题 N：
- 当前观察：
- 不确定点：
- 为什么重要：
- 可选方案：A. / B. / C.
- 工程/机制/授权问题的推荐与影响；真实业务原意仅中性选项：
- 未答状态/恢复点（沉默、超时、预选不是决定）：
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
| `Risk Level` | Low / Medium / High；按实际影响判断，runtime路径不自动High |
| `Next Step` | 明确下一阶段动作（不要只写"继续"） |
| `Evidence Map` | 8 行 8-dim 全填；不涉及的写 "不涉及（理由：...）" |
| `Documentation Decision` | 每实际受影响对象有 Create/Update/None及理由；按真实类型增补，不固定十类 |
| `Stale Doc Reverse Scan` | mj-agent 扩展 7 类改动 + biz_catalog drift + runtime canonical 反向扫描 |

---

## 关联文档

- [[sdd/workflows/execution-loop|执行闭环 workflow]] Stage 3（Repo Scan）
- `.agents/skills/mj-agent-flow-repo-scan/SKILL.md`（承载 8-dim 扫描完整步骤）
- [[../guide/[GUIDE]_MJ_Agent_SPEC_Authoring|SPEC Authoring GUIDE]]（如 SPEC = Create/Update 时使用）

## 更新记录

| 日期 | 版本 | 变更 |
| --- | --- | --- |
| 2026-05-11 | v0.1 | 初稿（PR-118 commit-3 落地；G1 gap 修复） |

| 2026-10-29 | v0.2 | #608：默认对话/真实类型保存、原意与新目录、按实际对象文档决策及离线验证入口 |
