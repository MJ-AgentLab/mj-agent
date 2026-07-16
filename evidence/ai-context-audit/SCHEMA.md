# A6 AI-Context Audit — Schema + Cadence

> Lives at `evidence/ai-context-audit/`. Per A6 of B1 best-practices skeleton
> (commit `550e46b`) — promoted to canonical via Stage D D-1c (this file).
> Pair with `policies/ai-agent.md §7 Pre-flight Verification Discipline` — §7
> is ad-hoc per-action; A6 is periodic baseline.

## §1 Purpose

Quarterly audit of AI-context surfaces (CLAUDE.md tree + `.claude/` artefacts +
freeze surfaces) for drift detection. Trigger = quarter natural boundary (manual
+ reminder; **NOT** CI cron, which is brittle and silently lapses). A6 produces
a write-once `<cycle>.md` entry per quarter; future cycles diff against prior
to surface drift. Complements `policies/ai-agent.md §7` (per-action pre-flight)
by establishing periodic baselines that §7 can reference as ground truth.

## §2 Audit Entry Frontmatter Schema (canonical)

Each `<cycle>.md` entry under this directory MUST begin with:

```yaml
---
type: ai-context-audit
cycle: YYYY-QN                  # e.g. 2026-Q2
auditor: <human-or-agent-id>    # 执行者标识 (人名 OR "ai-agent (<model> via <client>; HITL-supervised by <human>)")
scope:                          # 本 cycle 覆盖 surface 类型 (4-5 项)
  - root-claude-md
  - subdir-claude-md
  - claude-skills-inventory
  - freeze-surface-hashes
  - claude-settings-hooks
findings_summary: <one-line>    # 本 cycle 主要发现 (no finding = "baseline OK; no drift detected")
content_hash_snapshot:          # 双轨基线 (必停轨 + CLAUDE.md 轨); 面集 **按下方规则推导**,
                                # 不写死数量; 未来 cycle 用此 map diff 检测 drift
  CLAUDE.md: <sha256-hex>
  src/mj_agent/CLAUDE.md: <sha256-hex>
  # ... 其余各项
---
```

### §2.1 `content_hash_snapshot` 面集 —— 推导规则（**不写死数量**）

> **为何是推导规则**：本节初版把面集**写死为固定数量**（15 面 = 10 必停 + 5 CLAUDE.md），并把
> 必停轨枚举为固定的 3 个 runtime skills + 6 个 infra skills。这些常量**无 gate 盯**，随后静默过期
> —— #304 冻结 `app-start`/`app-stop`（infra 6→8）时无人回改本文件，2026-Q3 审计才发现
> （见 `2026-Q3.md` F3）。故本节改为**从执行面机械推导**：面集跟随磁盘，不再靠人肉回改数字。

本审计快照的是 **AI-context 文本面**（§1：CLAUDE.md 树 + `.claude/` prose artefacts + 冻结面）——
即 hash 算法（regex-strip-frontmatter）**能作用**的 **markdown** 面。面集 = 下列两轨之**并集**，
每 cycle 按当时的仓库状态**现场推导**（数量是**观测值**，不是规范值）：

| 轨 | 推导源（single source） | 算法 |
|---|---|---|
| **必停 markdown 轨** | `.claude/settings.json` `permissions.ask` glob 命中的 **`.md` 文件**（= `skills/**/SKILL.md` 命中项 + `prompts/system.md`；**`.py`/`.yaml` 项不入**——见下）∪ `claude-skill.contract.yml` 声明冻结的 `.claude/skills/mj-agent-infra-*/SKILL.md` | canonical regex-strip |
| **CLAUDE.md 轨** | `git ls-files` 命中的 `**/CLAUDE.md`（根 + 各 subdir） | plain SHA-256 |

> **为何排除 3 个非-markdown 必停面**：`permissions.ask` 共 5 条，其中
> `tools/sql/{guardrail,precheck}.py`（代码）+ `biz_catalog/qcm_catalog.yaml`（数据）
> **是必停面但不是 AI-context markdown 面**：① regex-strip-frontmatter 算法对 `.py`/纯 `.yaml`
> **无意义**（无 frontmatter/body 之分）；② 其 drift 由各自专属机制监控——`.py` 由
> `sql-guardrail-relax` 必停门 + 单测，`qcm_catalog.yaml` 由 `biz-catalog-sync` 必停门。
> 故本 hash 审计**故意不纳入**这 3 面（**非遗漏**）；它们的存在与「另有专门监控」在 cycle entry
> 显式记一笔即可。→ 「必停 markdown 轨」= 5 条 `ask` 中的 **2 类 markdown**（SKILL.md glob +
> system.md）∪ 冻结 infra。

- **canonical regex-strip 算法**（per `runtime-skill.contract.yml` /
  `claude-skill.contract.yml` header comment）：strip frontmatter via
  `(?ms)^---\r?\n.*?\r?\n---\r?\n` regex + LF normalise + SHA-256 hex lowercase。
  与 contract YAML 中 `content_hash` / `body_content_hash` 字段**同算法** ——
  故必停轨的 infra 项可直接与 contract 的 `body_content_hash` 比对以判定冻结违规。
- **plain SHA-256**：full file UTF-8 bytes（CLAUDE.md 无 frontmatter → full-file hash
  即 body hash）。
- **落地纪律**：审计者须**先复现上一 cycle 的若干既有 hash** 证明算法实现正确，再算新面
  （否则实现 bug 会被误报成 drift）。
- **诚实边界（durability）**：本推导规则**降低**了常量腐坏风险（面集从执行面推导，非人肉写死），
  但**未消除**——`evidence/` 在 `scripts/check_frontmatter.py` 的 `SCAN_ROOTS` **之外**，故
  **无 CI gate 强制**执行本推导或校验 entry 的 `content_hash_snapshot`。它依赖审计者每 cycle
  **现场跑推导**（同 A6 选 manual+M-FU 提醒而非 CI cron 的权衡；提醒机制本身仍可能失效，见
  `2026-Q3.md` F7）。若将来硬化，应加一支 `evidence/ai-context-audit/` 专属 §2 validator。

**推导即得的当期观测值**（记录用，非规范）：2026-Q2 = 15 面；2026-Q3 = **23 面**
（必停 markdown 轨 18 = 9 runtime `SKILL.md` + `system.md` + 8 infra；CLAUDE.md 轨 5）。

> **面集变动的处置**：新增面**无上期基线** → 本期记 `baseline-only`，drift 判定从**下**期起；
> 路径重命名（如 `infra/docker/CLAUDE.md` → `docker/CLAUDE.md`）→ 在 entry 内显式标注新旧
> 对应，hash 照常比对。

## §3 Cadence + Reminder Mechanism

Trigger: quarter natural boundary (2026-Q2 / 2026-Q3 / 2026-Q4 / 2027-Q1 / ...).
Reminder mechanism: at end of each cycle, register `M-FU-AI-AUDIT-<next-cycle>`
plan as owner reminder (NOT CI cron — cron silently lapses without ownership
acknowledgement). Single cycle deliverable = one `<cycle>.md` entry in this dir.

Lapse policy: if next cycle is > 30 days overdue, auditor MUST record gap in
the catch-up entry's findings_summary (e.g., `"2027-Q1 deferred 45 days; gap
recorded; drift-vs-2026-Q4 across <N> surfaces inventoried"`, where `<N>` = 本期
按 §2.1 推导所得的面数). 逾期 ≤ 30 日时记 gap 为**自愿**（非 MUST）—— 但 cycle 逾期
本身**始终**应在 findings 中留痕（2026-Q3 即以 ~15 日逾期落此例）。

## §4 First-Cycle Scope Expectation (2026-Q2) — **历史条款**

> **适用范围**：本节是对**首个** cycle（`2026-Q2.md`）的一次性 scope 要求，其中的数量
> （`34` skills / `10` 必停）是 **2026-Q2 当时**的事实，**不是**后续 cycle 的规范 ——
> 后续面集一律按 **§2.1 推导规则**现场推导（2026-Q3 起：skills 37、必停轨 18）。
> 保留本节是为了让 Q2 entry 可被其原始验收条款复核（write-once 纪律：不回改既成事实）。

The first audit entry (`2026-Q2.md`) MUST include:

- **5 CLAUDE.md inventory**: path + line count + plain SHA-256
- **34 `.claude/skills/<name>/SKILL.md` inventory** + canonical regex-strip
  hash per file (compact 1-line each)
- **`.claude/settings.json` snapshot**: hooks 列表 (PreToolUse + Stop entries
  count + paths) + full-file SHA-256
- **10 必停 surface drift check**: canonical regex-strip hash compared
  against `runtime-skill.contract.yml` / `claude-skill.contract.yml` /
  `prompt.contract.yml` `frozen_at` + `content_hash` fields; expected outcome:
  all match (Stage D全程 AC-3 验证未动必停)
- **findings_summary**: one-line summary; baseline-only entries record
  `"baseline established for Q3 comparison"`

Subsequent cycles can reduce inventory depth (only changed surfaces need full
re-snapshot if `content_hash_snapshot` map remains the canonical drift source).
