---
type: adr
domain: SYS
summary: Phase D-2 scripts/infra：mj-system v5.2 §7.1.1 派生 find_stale_docs.py 完整版（warning-mode CI）+ ADR-021 follow-up archived 物理归档候选检测脚本
owner: 项目负责人
created: 2026-05-09
updated: 2026-05-09
state: active
decision: accepted
track: shared
tags:
  - adr
  - documentation
  - script
  - ci
  - mj-system-derivation
---

# ADR 023: Stale Doc Detection + Plan GC Infrastructure

## Context

mj-agent 当前 docs / plans 治理脚本仅有：

- `scripts/check_frontmatter.py`（ADR-022）— frontmatter schema + type-conditional
- `scripts/check_wikilinks.py`（ADR-020）— archive ref freshness（auto-discover from `docs/archive/rule/[DEPRECATED]_*.md`）

**两个 transitional debts** 待落实：

### Debt 1：ADR-021 §Consequences 标记 archived 物理归档为 Phase D follow-up

ADR-021 §Decision 引入 working state 4 态（draft → active → completed → archived）；`archived` 是物理归档（移 `plans/archive/`）。当前 mj-agent 最早 completed plan（Phase F / G）距今 < 1 月，6 月阈值未到；但需要 infra：

- 检测候选清单的脚本
- Meta v2.2 §5.11.5 的实施指引

### Debt 2：mj-system §7.1.1 path-level stale ref detection 借鉴

mj-system v5.2 §7.1.1 引入 `find_stale_docs.py` warning-mode CI：检测 PR diff 中文件 rename / delete 后，backtick 包裹的旧路径 ref 残留。

ADR-020 §Alternatives B 显式拒绝引入 mj-system 完整版"那是 Phase D 范畴"。本 ADR 兑现该承诺。

## Decision

### 1. `scripts/find_stale_docs.py`（mj-system §7.1.1 派生）

输入：`base_ref...head_ref` git diff（默认 `origin/develop...HEAD`）。

逻辑：
1. `git diff --name-status --find-renames` 提取 rename / delete 文件
2. 对每个旧路径，grep backtick 包裹的 \`\`<old-path>\`\` ref，扫描范围：
   - `docs/**/*.md`
   - `plans/**/*.md`
   - `CLAUDE.md` / `CHANGELOG.md` / `README.md`
3. 输出 human-readable 表 + JSON to stderr

退出码：**始终 0（warning 模式）**；4 周观察期满后评估升级 blocking。

### 2. `.github/workflows/check-stale-docs.yml`（CI 集成）

PR-time 触发；输出 `::warning::` annotation 到 GitHub Actions 步骤摘要；`continue-on-error: true`。

### 3. `scripts/find_old_completed_plans.py`（ADR-021 follow-up）

扫 `plans/*.md`，找 `state: completed` AND `updated` 距今 ≥ `threshold_days`（默认 180）的候选。**不实际移动**；输出候选清单。

阈值参数化（位置参数）：`python scripts/find_old_completed_plans.py 90` 可调到 90 天。

### 4. Meta v2.2 §5.11.5 archive 实施指引

补充 §5.11.5 段：
- `plans/archive/` 子目录约定（首次 GC 时按需创建）
- `archived` state frontmatter 同步加 `archived: <YYYY-MM-DD>` 字段
- archived 文件**不更新内部 wikilinks**（per mj-system §10.3 frozen 原则；与 ADR-019 archive 文件相同处理）
- 检测脚本：`scripts/find_old_completed_plans.py` + 人工 review + 手动移动

### 5. 与既有 ADR 关系

- **不 supersede 任何 ADR**
- 与 ADR-020（check_wikilinks 通用化）**互补**：check_wikilinks 校验 archive ref；本 ADR find_stale_docs 校验 path rename
- 与 ADR-021（working doc 4 态机）**follow-up**：落实 ADR-021 标记的 Phase D infrastructure
- ADR-022（C.3.1 类型字段）sustained：本 ADR 不动 frontmatter schema

## Consequences

### 正面

1. **path-level rename 检测落地** — Phase C 期间 6+ PRs 涉及大量 rename（active/archive 路径）；future rename 风险显著降低
2. **warning-mode 4 周观察期** — 实测 false-positive rate 后再决定升 blocking；符合 mj-system 模式（issue #216 同样 4 周观察）
3. **ADR-021 archived state infra 就位** — 6 月阈值到时（约 2026-11，即 PLAN_F/G 完成后 6 月）有现成脚本检测候选
4. **JSON output 可被 CI 二次消费** — 未来集成 PR comment / Slack 通知
5. **mj-system 双向兼容继续** — 同模式（dir scan / git diff scan）

### 负面

1. **新 GH Actions workflow 引入 CI 时间** — 但 warning-mode 不阻塞合并；时间成本可接受
2. **find_stale_docs.py 仅 path-level** — symbol-level rename（Python function / class / SQL 列名）不在本 ADR；mj-system MVP 也仅 path-level
3. **find_old_completed_plans.py 是离线工具** — 不在 CI 中跑；需 manual periodic review

### 中性

1. **MVP 严格守约**：本 PR 只引 infra；不实跑 GC（plans 距今 < 1 月）；不升 blocking（4 周观察期）
2. **本 PR 自身按 ADR-017 §5.9 判定**：trigger #1-4 ❌；反例 #5 字段补充 ✅（Meta §5.11.5 加段；新 scripts 加；§5.9 反例）→ 不触发 archive ceremony

## Alternatives considered

### A. 仅引 find_stale_docs.py，不引 plan GC infra

**拒绝原因**：ADR-021 已标记 plan GC 为 Phase D follow-up；推迟到 D-3 增加 D-3 scope（已是最大 PR）；本 PR 是 scripts/infra 主题，正合适。

### B. find_stale_docs.py 直接 blocking（无观察期）

**拒绝原因**：mj-system 实测：path-level rename detection false-positive 高于预期（特别是 wiki 表格中 backtick 路径旧化）；4 周观察期是 mj-system v5.2 §7.1.1 已验证模式。

### C. 引入 symbol-level rename detection（Python AST + grep）

**拒绝原因**：实现复杂度 5×；mj-system MVP 也仅 path-level；symbol-level 作为 Phase E+ 候选（如有需求）。

### D. 用 GitHub Action 现有 marketplace tool（如 `path-stale-checker`）

**拒绝原因**：mj-agent 偏向 self-hosted 脚本（与 mj-system 一致）；marketplace tool 增加 trust posture 评估负担（per ADR-014 §A14）；自写 Python 脚本控制度更高。

## References

- 派生源：[mj-system@scripts/find_stale_docs.py](https://github.com/MJ-AgentLab/mj-system/blob/develop/scripts/find_stale_docs.py)（完整版借鉴）+ mj-system v5.2 §7.1.1 + issue #216
- 落实：
  - [[../adr/[ADR]_021_Working_Doc_Lifecycle|ADR-021]] §Consequences 负面 #2 archived 物理归档 follow-up（D-2）
  - [[../adr/[ADR]_020_Archive_Auto_Discovery|ADR-020]] §Alternatives B "Phase D 范畴 find_stale_docs 完整版"承诺
- 关联 ADR：与 ADR-020/021 互补；不 supersede 任何 ADR
- 落地：
  - `scripts/find_stale_docs.py`
  - `scripts/find_old_completed_plans.py`
  - `.github/workflows/check-stale-docs.yml`
  - Meta v2.2 §5.11.5（archive 实施指引）
- 关联 GitHub Issue：[#92](https://github.com/MJ-AgentLab/mj-agent/issues/92)
- 后续（Phase E+ 候选）：symbol-level rename detection + 实际首次 GC 操作 + warning → blocking 升级（4 周观察后）
