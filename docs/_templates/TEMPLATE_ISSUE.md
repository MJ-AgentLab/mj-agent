---
type: issue
domain: SYS
summary: 20-60 字摘要，一句话说这个延后处理的问题、影响、修复方向
tags:
  - issue
aliases: []
created: YYYY-MM-DD
updated: YYYY-MM-DD
state: draft
version: v1.0
track: shared
derives_from: ""
owner: 项目负责人
priority: P2
risk_level: Low / Medium / High
resolution: open
discovered_during: "<during what work>"
related_issue: "<#NNN 或 无>"
related_plan: "<[[PLAN 文档]] 或 无>"
related_spec: "<[[SPEC 文档]] 或 无>"
related_adr: "<[[ADR 文档]] 或 无>"
---

# ISSUE-NNN <问题标题>

> **受影响领域**：<mj-agent module（agent / llm / sql / db / ...）/ infra / docs>
> **发现场景**：<during what work>
> **优先级**：P0 / P1 / P2 / P3
> **风险等级**：Low / Medium / High
> **GitHub Issue**：<#NNN 或 无>
> **派生自**：（如非派生则写"mj-agent 原生"）
> **关联文档**：<相关 ADR / SPEC / GUIDE / RUNBOOK 的 wikilink>

---

## TL;DR

- **问题性质**：<bug 待修 / 优化候选 / 设计讨论 / 调试线索 / 历史记录>
- **风险等级**：<Low / Medium / High>
- **预估工作量**：S（< 1 day）/ M（1-3 day）/ L（1 week）/ XL（> 1 week）
- **mj-agent §3.1 必停 4 项触发**：<无 / runtime-skill-content-change / prompt-version-bump / biz-catalog-sync / sql-guardrail-relax>

---

## 目录

1. [§1 问题摘要](#1-问题摘要)
2. [§2 发现上下文与证据](#2-发现上下文与证据)
3. [§3 问题分析](#3-问题分析)
4. [§4 影响评估](#4-影响评估)
5. [§5 建议修复方向](#5-建议修复方向)
6. [§6 验收标准](#6-验收标准)
7. [§7 验证计划](#7-验证计划)
8. [§8 待确认问题](#8-待确认问题)

---

## §1 问题摘要

<≤ 3 句话：什么问题、在哪里、为什么重要>

---

## §2 发现上下文与证据

<≤ 3 段：做什么工作时发现的、什么证据、为什么延后。证据应尽量引用代码路径、SQL 对象、日志、数据样本、Issue 或 PR>

例：
- 发现于 `feature/xx-yy` 分支 PR #NN review 阶段
- 证据：`src/mj_agent/skills/biz-domain-context/SKILL.md` line 230 描述 dim_xxx 表，但 `qcm_catalog.yaml` 不含此 dim → `find_biz_context` 召回不准
- 延后原因：本 PR scope 为 X，本问题超 scope；建 ISSUE 跟踪

---

## §3 问题分析

### §3.1 技术根因

<根因分析，可引用代码路径>

例：
- root cause: `qcm_catalog.yaml` 上次同步是 mj-system STANDARD §2-§4 的 v2.3 版本；mj-system 已升至 v2.5（新增 dim_xxx）
- mj-agent 镜像漂移；`/mj-agent-runtime-biz-catalog-sync`（PR-C2 落地）下次跑应捕获

### §3.2 复现条件

<什么条件下问题会出现（选填，已知时填写）>

### §3.3 风味识别（mj-agent 专属，per ADR-015 §决策点 3）

- ☐ **A 风味**：pure code（tools / memory / integrations / agent.py / tests / config）
- ☐ **B 风味**：in-source canonical（src/mj_agent/skills/**/SKILL.md / prompts/system.md / biz_catalog/qcm_catalog.yaml）—— **永远 §3.1 必停 HITL**；建议先 propose-via-runtime-* （PR-C2）
- ☐ **C 风味**：infra（infra/docker / pyproject.toml / langgraph.json / .env.example / scripts/）

---

## §4 影响评估

<≤ 2 段：对数据正确性、系统可用性、用户可见性的影响描述>

| 维度 | 影响 |
|---|---|
| 数据正确性 | <如：find_biz_context 召回 5% 不准> |
| 系统可用性 | <如：无影响；纯业务语义层> |
| 用户可见行为 | <如：分析师问关于 dim_xxx 时回答不全> |
| Studio probe 矩阵 | <H1/H2/H3 不受影响 / 受影响；R1/R2 红线必填> |
| smoke test | <list affected 用例> |

**风险来源**：<说明为什么是 Low / Medium / High>

**预估工作量**：S / M / L / XL

---

## §5 建议修复方向

<≤ 5 个要点或简要草图；不是完整设计>

例：
1. 跑 `/mj-agent-runtime-biz-catalog-sync`（PR-C2）—— propose qcm_catalog.yaml diff
2. Domain Expert review propose diff
3. user 接受 → /mj-agent-doc-author 写盘
4. /mj-agent-runtime-skill-doc-improve 同步 biz-domain-context SKILL.md（如反扫命中）
5. /mj-agent-infra-studio-probe 跑 H1/H2/H3 验证 find_biz_context 召回

---

## §6 验收标准

- [ ] <修复或处理完成后可验证的条件 1>
- [ ] <修复或处理完成后可验证的条件 2>
- [ ] <如 B 风味改动：A11 EVAL 引用同步审查 / EVAL backlog ticket 自动开>

---

## §7 验证计划

> 按 [[../rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.1|Meta v2.1]] §4.7 拆「本地验证」与「AI 自检」双段。

### §7.1 本地验证（人类客观可重复检查）

- `uv run pytest tests/<bands>` <按改动范围选；无 src/ 改动则跳>
- `uv run ruff check` + `uv run mypy src/mj_agent`
- `python scripts/check_wikilinks.py` + `python scripts/check_frontmatter.py`
- `uv run mj-agent check`（如 .env 创新字段）
- `uv run langgraph dev` + Studio H1/H2/H3/R1/R2 矩阵（如 B 风味改动）
- `python scripts/diff_biz_schema.py`（如 biz_catalog 触及）

### §7.2 AI 自检（生成内容可信度自查）

- [ ] 影响范围已核对到真实代码 / SQL / 配置（非仅按命名推断）
- [ ] 引用路径有效（issue / PR / 文档相对链接）
- [ ] 无残留调试代码、硬编码或敏感信息
- [ ] 文档与实现一致
- [ ] 5a/5b/5c/5d 反向扫描（per HITL_Prompt §4.9 Rule 5；mj-agent 扩展含 in-source canonical）
- [ ] B 风味改动通过 mj-agent-runtime-* propose-diff 流程（如适用）

---

## §8 待确认问题

- [ ] <如有：会影响执行路径、数据、API、权限、安全、发布或回滚的问题>
- [ ] <如有：跨 PR / 跨 milestone 的边界问题>
- [ ] <如有：上游 mj-system 协调问题（biz_catalog drift / SQL guardrail / 数据边界）>

---

## 关联文档

- **GitHub Issue**：<#NNN 或 无>
- **Plan**：<[[PLAN 文档]] 或 无>
- **SPEC**：<[[SPEC 文档]] 或 无>
- **ADR**：<[[ADR 文档]] 或 无>
- **PR**：<#NNN 或 无；含 follow-up PR 链接>
- **POSTMORTEM**：<[[POSTMORTEM 文档]] 或 无；如本 ISSUE 由事故 follow-up>
- **mj-system 上游 issue / PR**：<如本 ISSUE 触发 mj-system 协调>

## 更新记录

| 日期 | 版本 | 变更 |
| --- | --- | --- |
| YYYY-MM-DD | v1.0 | 初稿 |
| YYYY-MM-DD | v1.1 | <如：分析深化 / 关联 PR 落地 / resolution 升级 closed> |
