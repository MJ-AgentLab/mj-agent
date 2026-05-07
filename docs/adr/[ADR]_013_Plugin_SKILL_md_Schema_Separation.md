---
type: adr
domain: SYS
summary: marketplace plugin SKILL.md 使用 Claude Code 原生 schema（name + description 两字段），与 mj-agent in-source SKILL.md 的 Agent_Side v1.0 §2 13 字段 schema 独立；两者通过 sync skill（Phase 1）做内容同步，不做 schema 同步
owner: 项目负责人
created: 2026-04-29
updated: 2026-04-29
state: draft
decision: accepted
track: shared
tags:
  - adr
  - documentation
  - plugin
  - schema
  - dual-schema
  - claude-code
---

# ADR 013: Plugin SKILL.md Schema Separation

## Context

[[[ADR]_012_Two_Track_Documentation_Governance|ADR-012]] 引入双轨治理 + 双 plugin 骨架（`mj-agent-agent-doc` / `mj-agent-code-doc`），并在 [[../../plans/[PLAN]_F_Documentation_Track_Split_And_Plugin_Skeleton|PLAN F]] §V-skel-4 / §V-skel-5 + [[../rule/[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework_v1.0|Agent_Side v1.0]] §2 中默认假设 marketplace plugin SKILL.md 与 mj-agent 仓内 `src/mj_agent/skills/**/SKILL.md`（in-source SKILL.md）共用同一套 schema（13 字段 frontmatter + 五段式 body）。

但在 marketplace plugin 实施前的探查（2026-04-29）中发现以下事实：

### 事实 1：marketplace 现存 plugin 不使用 13 字段 schema

[mj-agentlab-marketplace](https://github.com/MJ-AgentLab/mj-agentlab-marketplace) 现有 4 个 plugin（`mj-sys-doc` / `mj-sys-git` / `mj-sys-n8n` / `mj-sys-ops`，均 v2.0+）的 `plugins/<x>/skills/<y>/SKILL.md` 实际只使用 Claude Code 原生 schema：

```yaml
---
name: <plugin>-<skill>
description: <长 description，含触发短语，含"不适用于"反例>
---
```

不存在 `type / domain / state / version / track / owner / created / updated / summary / activation.triggers / related_prompts / eval_references` 这些字段。

### 事实 2：Claude Code plugin loader 不读 13 字段

参照 Anthropic 官方 plugin-dev plugin 的 [skill-development](https://github.com/anthropics/skills) 与 skill-creator 工作流：

> "**name**: Skill identifier
> **description**: When to trigger, what it does. **This is the primary triggering mechanism**."

Claude Code 的 skill 触发完全依赖 frontmatter `description` 字段；mj-agent §2 的 `summary` / `activation.triggers` / `related_prompts` / `eval_references` 等字段都不会被 Claude Code 读取。

### 事实 3：13 字段 schema 是 mj-agent loader 契约的一部分

Agent_Side v1.0 §7.3（frontmatter strip 契约）与 §7.5（语义对齐校验）规定 `src/mj_agent/skills/**/SKILL.md` 必须由 mj-agent 自己的 Python loader 解析、剥离 frontmatter 后只把 body 注入 LLM 上下文。这套契约对 13 字段 schema 是有意义的（loader 用元数据做 routing / version / EVAL 引用）；但**仅对 in-source SKILL.md 有意义**，对由 Claude Code 加载的 plugin SKILL.md 无效。

### 矛盾结论

PLAN F § V-skel-4 line 153/161-199 + Agent_Side §2.1 把 13 字段 schema + 五段式 body 不加范围限定地扩展到了 marketplace plugin SKILL.md。如果按此假设落地：

- marketplace plugin SKILL.md 包含 11 个 Claude Code 不识别的字段，缺关键 `description` 字段
- Claude Code 触发匹配失败 → plugin 在用户 install 后无法激活，等于交付了"沉睡的"文件
- 与 marketplace 现存 4 个 mj-sys-* plugin 的 schema 不一致 → reviewer 困惑、风格分裂

不加 ADR 锁定决策，下次有人按 PLAN F / Agent_Side §2 起草新 plugin 时仍会重蹈覆辙。

---

## Decision

### 决策点 1：marketplace plugin SKILL.md 使用 Claude Code 原生 schema

```yaml
---
name: <plugin-name>-<skill-name>
description: <长 description；含「Make sure to use this skill whenever...」式触发短语；含"不适用于"反例；可包含中英双语 trigger 词>
---
```

frontmatter **只用 name + description 两字段**，不引入 mj-agent §2 的 13 字段。

如果需要追溯 mj-agent 仓内对应内容，可在 plugin SKILL.md body 中加一段 `## Internal metadata`（可选），列 `mj-agent-source-skill` / `mj-agent-track` / `last-sync-with-in-source` 等信息——但这是 body 内容，不是 frontmatter。

### 决策点 2：plugin SKILL.md body 结构与 marketplace 现状对齐

不再强制使用 Agent_Side §2.1 的 Purpose / When to use / Planning workflow / Common patterns / Anti-patterns 五段式。改为与 marketplace 现存 mj-sys-* 4 plugin 风格对齐——典型为：

```
## Overview
## When to use（可选）
## Workflow（步骤化）
## Quick Reference / Common patterns
## Anti-patterns（可选）
```

每个 plugin 可按其领域调整段名，**只要与该 plugin 内部其它 skill 一致即可**；不要求跨 plugin 段名一致。

### 决策点 3：in-source SKILL.md 不变

`src/mj_agent/skills/**/SKILL.md` 仍严格按 Agent_Side v1.0 §2 的 13 字段 schema + 五段式 body。§7.3 / §7.5 frontmatter strip 契约不受影响。

### 决策点 4：双 source 通过 sync skill 同步内容、不同步 schema

未来的 `mj-agent-code-doc-sync` skill（PLAN F §V-content-2，Phase 1）负责在 mj-agent 仓 in-source SKILL.md 和 marketplace plugin SKILL.md 之间做内容同步——但同步的是 body 中的概念性内容（譬如 8 类 canonical 的判断树），不是 frontmatter schema。每一侧在自己的 schema 内独立演化。

### 决策点 5：mj-agent docs/_templates/TEMPLATE_SKILL.md 适用范围

`docs/_templates/TEMPLATE_SKILL.md` 是为 in-source SKILL.md 准备的（13 字段 schema）。在 plugin 起草时**不引用此模板**。如未来 plugin 数量增多，可在 marketplace 仓内独立维护 plugin SKILL.md 模板（譬如 `mj-agentlab-marketplace/docs/templates/PLUGIN_SKILL.md`）。

---

## Consequences

### 正面

- ✅ **marketplace plugin 在 Claude Code 中可正常激活**：本 ADR 的核心目的
- ✅ **§7.3 / §7.5 frontmatter strip 契约不受影响**：in-source loader 行为不变
- ✅ **与 marketplace 现存 4 个 mj-sys-* plugin 一致**：reviewer 期望统一、风格不分裂
- ✅ **下次 plugin 起草不再重蹈覆辙**：ADR-013 + Agent_Side §2 scope note + PLAN F §V-skel-4/-5 sub-banner 三处锁定决策
- ✅ **保留 in-source 13 字段的全部价值**：track 字段、EVAL 引用、frontmatter strip 契约——这些仍是 mj-agent 内部治理工具，不被本 ADR 削弱

### 负面

- ⚠️ **双 schema 双 source**：mj-agent in-source SKILL.md 与 marketplace plugin SKILL.md 内容可能漂移；缓解方案是 Phase 1 的 sync skill
- ⚠️ **三处文档需联动修订**：ADR-013（本文件）+ Agent_Side §2/§9 scope note + PLAN F §V-skel-4/-5 sub-banner，不能只修一处
- ⚠️ **plugin SKILL.md body 结构非强制统一**：mj-sys-* 4 plugin 已有不同变体（Overview/Workflow vs Overview/Prerequisite/Workflow/...），允许 per-plugin 灵活，代价是跨 plugin reviewer 需要适应不同结构

### 中性

- 📌 **现有 4 个 mj-sys-* plugin 视为既定事实**：本 ADR 不要求它们迁移；它们的格式即 marketplace plugin schema 事实标准
- 📌 **未来 plugin 数量增长后可能独立模板**：`mj-agentlab-marketplace/docs/templates/PLUGIN_SKILL.md` 为可选未来工作，不在本 ADR 决定范围

### 风险

- **sync skill 推迟到 Phase 1**：在 sync skill 落地前，如果 mj-agent in-source code-doc skill 也存在（目前不存在），会有内容漂移空窗期。当前空窗期风险可控（in-source 侧空），但 Phase 1 必须落地 sync skill。
- **ADR-013 决策被项目负责人否决的可能**：低概率，但若发生，回退方案是接受 plugin 永久"沉睡"（方向 B）+ 在 mj-agent docs 内部使用，不在 marketplace 真实部署。

---

## Alternatives considered

- **方案 I（统一到 13 字段）**：让 marketplace 现有 4 个 mj-sys-* plugin 全部迁移到 13 字段 schema。**未采纳**：(a) Claude Code 不识别 13 字段，迁移后 4 个 plugin 全部停摆；(b) 已发布版本回退是 breaking change，违反 marketplace SemVer 约束。
- **方案 II（统一到 2 字段）**：让 mj-agent in-source SKILL.md 退到 Claude Code 标准 2 字段。**未采纳**：(a) 破坏 §7.3 frontmatter strip 契约（loader 失去 routing 元数据）；(b) 削弱 §7.5 语义对齐校验（A7.1/A7.2 不再可执行）；(c) 失去 EVAL 引用（A11）—— 整个 Track B 治理体系坍塌。
- **方案 III（接受现状不修）**：不动 PLAN F + Agent_Side，让 plugin 按 13 字段格式落地，承受 plugin 永久"沉睡"。**未采纳**：违背 mj-agentlab-marketplace 仓存在的目的（提供可激活的 plugin）；下次再有人起草 plugin 仍踩同坑。
- **方案 IV（双重 description）**：plugin SKILL.md 同时保留 13 字段 + Claude Code description。**未采纳**：(a) 维护成本翻倍；(b) Claude Code LLM 触发匹配可能被 13 字段 yaml noise 干扰（虽然 LLM 通常忽略未识别字段，但更长的 frontmatter 增加 cache 成本）；(c) 双 source-of-truth 反模式。

---

## References

- 直接前置：[[[ADR]_012_Two_Track_Documentation_Governance|ADR-012]]（双轨治理 + 双 plugin 骨架决策）
- 同期联动修订：
  - [[../rule/[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework_v1.0|Agent_Side v1.0]] §2 + §9（scope note，同 PR 落地）
  - [[../../plans/[PLAN]_F_Documentation_Track_Split_And_Plugin_Skeleton|PLAN F]] §V-skel-4 + §V-skel-5（schema correction sub-banner，同 PR 落地）
- 探查依据（2026-04-29）：
  - marketplace 现状：`mj-agentlab-marketplace/plugins/mj-sys-doc/skills/*/SKILL.md` 实测 frontmatter
  - Anthropic 官方标准：plugin-dev:create-plugin（8 阶段工作流）；skill-creator:skill-creator（创建/迭代/触发优化）
  - working notes 评估文件：`C:\Users\Admin\.claude\plans\d-document-my-local-vault-temp-ai-chat-merry-hartmanis.md` §1-§8
- 未来工作：
  - `mj-agent-code-doc-sync` skill（Phase 1，PLAN F §V-content-2）：双 source 内容同步
  - 可选 `mj-agentlab-marketplace/docs/templates/PLUGIN_SKILL.md`（未来 plugin 数量增长后）
- 行业精度：
  - Anthropic Skills 仓（github.com/anthropics/skills）：SKILL.md 工业标准为 name + description
  - Claude Code plugin 框架：每个 plugin 的 `plugins/<x>/skills/` 目录由 Claude Code 主进程 load
- 关联 PLAN：marketplace 仓内容蓝图 working notes `D:\Document\My_Local_Vault\temp-ai-chat\mj-agentlab-marketplace\[PLAN]_Marketplace_Plugin_Construction.md`（修订后引用 ADR-013）
