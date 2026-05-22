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
content_hash_snapshot:          # 15-surface 双轨基线 (10 必停 + 5 CLAUDE.md);
                                # 未来 cycle 用此 map diff 检测 drift
  CLAUDE.md: <sha256-hex>
  src/mj_agent/CLAUDE.md: <sha256-hex>
  # ... 其余 13 项
---
```

`content_hash_snapshot` 算法:
- **10 必停 surface** (3 `src/mj_agent/skills/*/SKILL.md` + `src/mj_agent/prompts/system.md` +
  6 `.claude/skills/mj-agent-infra-*/SKILL.md`): canonical regex-strip 算法 (per
  `runtime-skill.contract.yml` / `claude-skill.contract.yml` header comment) —
  strip frontmatter via `(?ms)^---\r?\n.*?\r?\n---\r?\n` regex + LF normalise +
  SHA-256 hex lowercase. 与 contract YAML 中 `content_hash` / `body_content_hash`
  字段同算法.
- **5 CLAUDE.md** (root + 4 subdir): plain SHA-256 of full file UTF-8 bytes (CLAUDE.md
  无 frontmatter; full-file hash 即 body hash).

## §3 Cadence + Reminder Mechanism

Trigger: quarter natural boundary (2026-Q2 / 2026-Q3 / 2026-Q4 / 2027-Q1 / ...).
Reminder mechanism: at end of each cycle, register `M-FU-AI-AUDIT-<next-cycle>`
plan as owner reminder (NOT CI cron — cron silently lapses without ownership
acknowledgement). Single cycle deliverable = one `<cycle>.md` entry in this dir.

Lapse policy: if next cycle is > 30 days overdue, auditor MUST record gap in
the catch-up entry's findings_summary (e.g., `"2027-Q1 deferred 45 days; gap
recorded; drift-vs-2026-Q4 across 15 surfaces inventoried"`).

## §4 First-Cycle Scope Expectation (2026-Q2)

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
