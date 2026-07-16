---
type: plan
slug: m-fu-ai-audit-2026-q4
summary: A6 AI-context audit 提醒工件 `M-FU-AI-AUDIT-2026-Q4`（前瞻）——2026-Q4 季度审计到期 ≈2026-10-01；除常规 drift 巡检外，本 cycle 兼任 issue #344 保留项（biz dev/test allow ×3）退出判据的**关闭者**：须复测 E1/E2 并作 `biz_devtest_allow_used` 二值判定
state: active
version: 1.0
owner: ranzuozhou
created: 2026-07-16
updated: 2026-07-16
track: shared
related_adrs:
  - decisions/ADR-032_Claude_Skill_Schema_Monitoring.md
  - decisions/ADR-034_HITL_Propose_Decide_Apply_Model.md
---

# [PLAN] M-FU-AI-AUDIT-2026-Q4 — A6 季度审计提醒（前瞻）

> **标识**：`M-FU-AI-AUDIT-2026-Q4`（per `evidence/ai-context-audit/SCHEMA.md §3`）。
> **触发**：2026-Q4 季度自然边界（到期 ≈ **2026-10-01**）。**执行者**：DRI（HITL）。

## 1 常规 A6 巡检

按 `evidence/ai-context-audit/SCHEMA.md`：

- 产出 write-once `evidence/ai-context-audit/2026-Q4.md`。
- 面集按 `SCHEMA.md §2.1` **推导规则现场推导**（**勿照抄** 2026-Q3 的 23；skills / infra /
  必停面可能再变）。
- 8 个 2026-Q3 baseline-only 面（`biz-schema-exploration` / `mj-ddd-semantics` /
  `monthly-report` / `query-optimization` / `query-writing` / `probe-fixture` +
  infra `app-start` / `app-stop`）**首次可作 drift 判定**。
- 冻结面复算 vs `claude-skill.contract.yml` `body_content_hash`。

## 2 兼任：issue #344 保留项退出判据的关闭者

> 依据 `plans/[PLAN]_dual-agent-compat_settings-narrow.md` §保留项判据 + `2026-Q3.md` §7。

- **窗口**：#345 merge `07e1be6`（2026-07-16）→ 本 cycle 产出为止（≈2.5 月观察期）。
- **两项证据缺一不可**（#344 明示）。**复测 E1**（尽力而为，须在**同一台机器** =
  本切片执行机 = Owner 的 Windows 开发机上跑；`~/.claude/projects/` transcripts）：
  ```bash
  grep -rl '"name":"mcp__pg-mj-system-biz-\(dev\|test-lan\|test-wan\)__' ~/.claude/projects/ | wc -l
  ```
  Q3 锚点值 = **2**（对照裸名 1136）。**务必用精确 `tool_use` pattern**（裸名假阳 ≈ 568×）。
  若 transcript 已被轮转/清理 → Q4 entry 明记「E1 不可测」，**不得以 0 冒充零调用**。
- **复测 E2**（权威、可 CI 复核，仓内跑）：
  ```bash
  grep -rln "settings\.json" scripts/ .github/ tests/ --include=*.py | wc -l   # Q3 锚点值 = 0
  ```
  **勿用 biz server 名计数做此不变量**（`MCP_FORCED_NEVER` 常量 + projection fixture 会假阳，
  见 `2026-Q3.md` §7 E2 反例警告）。
- **判定** `biz_devtest_allow_used: yes/no`：
  - `no`（零调用）→ 默认提 PR 删三条 allow（24→21），Owner 拍板即合，无需新评估。
  - `yes`（有调用）→ Q4 entry 逐条记用途；Owner 在 (a) 维持通配 / (b) 收窄 per-tool
    子集 之间拍板。

## 3 残余风险（Owner 已明示接受）

本工件本身就是「A6 提醒机制会静默失效」（2026-Q3 F7 实证）的**缓解而非保证**：
若本 Q4 提醒亦失效，则 #344 保留项判据将**永不触发**、三条 allow 长期悬留。
Owner 于 `plans/[INTAKE]_dual-agent-compat_settings-narrow.md` §7.2 明示接受该残余风险。

## 4 后继

Q4 cycle 结尾按 SCHEMA §3 注册 `plans/[PLAN]_m-fu-ai-audit-2027-Q1.md`
（勿重蹈本次静默失效——这正是 2026-Q3 逾期的根因）。
