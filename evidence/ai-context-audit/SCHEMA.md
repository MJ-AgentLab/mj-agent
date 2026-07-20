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

## §2 Entry Frontmatter Schemas (canonical)

本目录含**两类**条目，均由 `scripts/check_ai_context_audit.py` CI 校验（**filename-based** 选中，
非按 `type` 值 → 漏/错 `type` 或带 BOM 的真条目仍被 FAIL 非静默跳过）：**`ai-context-audit`** 季度
cycle（`YYYY-QN.md`；schema = 本节 §2 主体 + §2.1）· **`ai-context-investigation`** ad-hoc 调查
（`YYYY-MM-DD_*.md`；schema = **§2.2**，#362 落地 resolving a2 finding #2-9）。以下 §2 主体定义 **audit** 类。

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
- **诚实边界（durability）—— schema 校验缺口已闭（#359 / #347 §三.2 follow-up）**：本推导规则**降低**
  了常量腐坏风险（面集从执行面推导，非人肉写死）。`evidence/ai-context-audit/` 虽仍在
  `scripts/check_frontmatter.py` 的 `SCAN_ROOTS` **之外**，但已有**专属 validator**
  `scripts/check_ai_context_audit.py`（CI blocking gate）强制校验每个 `ai-context-audit` entry 的 §2
  frontmatter schema（`type`/`cycle` YYYY-QN/`auditor`/`scope`/`findings_summary`/`content_hash_snapshot`
  结构）。**派生规则已机器化**为该脚本 `--derive` 子命令（供审计者现场生成面集，消除人肉写死风险 =
  本节开头所述 #304→Q2-15-stale 病因）。
  - **validator 有意不做的**（**time-varying**——是**下期审计**要检的 drift，非 gate 违规）：**不重算**
    `content_hash_snapshot` 的 hash 值、**不校** key 路径在当前仓存在、**不做 blocking 派生匹配**。面集随仓
    变（Q2=15→Q3=23），blocking 匹配会 false-fail 并强制每次改动重跑季度审计，违 §1 A6「manual+M-FU 而非
    CI cron」设计。故审计者每 cycle 仍须**现场跑 `--derive`** 并按 §2.1 核实（提醒机制本身仍可能失效，见
    `2026-Q3.md` F7）——本 gate 保证**结构**合规，不替代季度**内容**核验。

**推导即得的当期观测值**（记录用，非规范）：2026-Q2 = 15 面；2026-Q3 = **23 面**
（必停 markdown 轨 18 = 9 runtime `SKILL.md` + `system.md` + 8 infra；CLAUDE.md 轨 5）。

> **面集变动的处置**：新增面**无上期基线** → 本期记 `baseline-only`，drift 判定从**下**期起；
> 路径重命名（如 `infra/docker/CLAUDE.md` → `docker/CLAUDE.md`）→ 在 entry 内显式标注新旧
> 对应，hash 照常比对。

## §2.2 Investigation Entry Frontmatter Schema (`ai-context-investigation`)

> **落地 #362**（resolving `2026-05-22_a2-investigation.md` finding **#2-9** +
> `schema_extension_request: true`）。A6 gate（#359）初版**只校 audit**（Gate-5 investigation-(a)
> skip）；本节正式定义 investigation 类型，`check_ai_context_audit.py` validator 现予强制。
> investigation 条目是 **ad-hoc**（非季度）：read-only 的 cross-finding 调查报告，任一 phase 皆可产出，
> 命名 `YYYY-MM-DD_<slug>.md`。

每个 `YYYY-MM-DD_<slug>.md` 条目 MUST 以如下 frontmatter 开头：

```yaml
---
type: ai-context-investigation
investigation: <slug>            # 本次调查 slug（类比 audit 的 cycle）; e.g. a2-body-sha256-v4-mode-b-joint
auditor: <human-or-agent-id>     # 同 §2（人名 OR "ai-agent (<model> via <client>; HITL-supervised by <human>)"）
scope:                           # 本次调查覆盖的面/主题（≥1）
  - <scope-item>
findings_summary: <one-line>     # 主要发现一行
# —— 以下均 optional ——
subtype: <slug>                  # e.g. readiness-eval（细分调查类型）
phase: <phase-id>                # e.g. M4-Stage-A-unit-A-2
date: YYYY-MM-DD                 # 调查日期（filename 已编码；冗余留痕）
related_episodes:                # 关联 episode 列表
  - "<episode>"
parent_artifacts:                # 上游工件列表
  - "<artifact>"
schema_extension_request: true   # 若本调查提请 SCHEMA amendment
---
```

**Required**（5）：`type`（== `ai-context-investigation`）· `investigation`（非空 slug）·
`auditor`（非空 str）· `scope`（非空 list of 非空 str）· `findings_summary`（非空 str）。

**Optional**（**仅在出现时**校验）：`subtype`（非空 str）· `related_episodes` /
`parent_artifacts`（非空 list of 非空 str）。`phase` / `date` / `schema_extension_request`
文档化但**不**受 validator 约束（`date` 由 YAML 解析为 date 对象，filename 已编码日期）。

**与 §2（audit）的关键结构差异**：investigation 用 `investigation` slug 取代 `cycle`，且
**不携带 `content_hash_snapshot`**（它是叙事报告，非 hash 快照）——故 §2.1 的面集推导规则
**不适用**于 investigation 条目（investigation 不进 `--derive` 面集）。

> **filename-based 选中（同 §2 纪律）**：validator 按 `YYYY-MM-DD_*.md` 文件名选中 investigation
> 条目（非按 `type` 值）——漏/错 `type` 或带 UTF-8 BOM 的真 investigation 条目仍被 **FAIL** 非静默跳过。
> 既非 cycle 亦非 investigation 的**已扫描 `.md`**（如 `SCHEMA.md`）→ 报 skip、不校验；仅 `*.md`
> 被扫描，故非 `.md` 文件（`.gitkeep`）根本不进扫描。

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
