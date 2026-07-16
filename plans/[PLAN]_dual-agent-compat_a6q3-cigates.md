---
type: plan
slug: dual-agent-compat-a6q3-cigates
summary: 双工具兼容 v5 第十执行切片实施计划——F(policies/ci-gates.md ADR-034 同步 :67/:68/:88/:38) + A(补跑逾期 2026-Q3 A6 审计〔23 面推导快照 + 冻结面 8/8 drift-clean〕 + SCHEMA §2.1 改推导规则 + M-FU Q3/Q4 补注册 + #344 判据 E1/E2 锚点)；1 PR，documentation/347-a6q3-cigates-sync；对应 issue #347（总锚 #312）
owner: ranzuozhou
created: 2026-07-16
updated: 2026-07-16
state: active
version: 1.0
track: shared
related_adrs:
  - decisions/ADR-034_HITL_Propose_Decide_Apply_Model.md
  - decisions/ADR-032_Claude_Skill_Schema_Monitoring.md
---

# [PLAN] 双工具兼容 v5 — ci-gates ADR-034 同步 + Q3 审计补跑切片（issue #347）

## 1 Linked Artifacts

- 成对 INTAKE：`plans/[INTAKE]_dual-agent-compat_a6q3-cigates.md`
- 总锚 #312 · issue #347 · 前序 #344（PR #345 `07e1be6` / flip #346 `a576eea`）
- 依据：`decisions/ADR-034`（deny→ask）· `evidence/ai-context-audit/SCHEMA.md`
  · `plans/[PLAN]_dual-agent-compat_settings-narrow.md:83`（Q3 = 基线记录者）

## 2 Context

P4 观察期未满（V10 腿 14/20 + 日历腿 07-28 未到，§11.1 AND），本切片填充等待窗口做两件
**互有排序依赖**的治理修复：

1. **F** — `policies/ci-gates.md` 自 ADR-034（2026-06-20）起未同步：仍称 5 项必停面 =
   `permissions.deny` 硬锁，而实况已 `deny→ask`。该失效定义被一道 **PR 阻塞门**（A13 条件 b，
   `:88`）+ 本审计自身的 scope 条款（`:38`）引用。
2. **A** — 2026-Q3 A6 审计逾期 ~15 日（提醒机制静默失效，见 Q3 F7）；且它是 #344 保留项
   退出判据（2026-Q4 关闭）的**基线记录者**（记 E1/E2 锚点）。

**排序**：`:38` 令审计对象 = `:67` 定义的红线 → F 先修定义，A 后按修正后定义审计。

## 3 Scope

**In**：`policies/ci-gates.md`（`:67/:68/:88/:38` + 连带的硬编码计数）·
`evidence/ai-context-audit/2026-Q3.md`（新建）· `evidence/ai-context-audit/SCHEMA.md`（§2.1
推导规则 + §3/§4 去硬编码）· `plans/`（本 INTAKE+PLAN + 2 M-FU）· `CHANGELOG.md`。

**Out**：`.mcp.json`(A14) · manifest(D-017) · `.claude/settings.json` 本体 · P4 gate 姿态 ·
#312 议题 1/2/3 · S3a doctor · `sdd/adapters/claude-code-skill.md:71`（复核只复述 A13 secret-pattern
半边，仍准确 → 不涉）· `policies/security.md:72`（是指针、不复述「4 项必停文件」，仍在 F 范围外；
但其 `deny 红线列表` gloss 变陈 → **登记 INTAKE §9 follow-up**，未在本 PR 改，避免越出已拍板 4 行 F 范围）。

## 4 退出判据设计对齐（承 #344）

本切片**不**新设退出判据；它**履行** #344 已定判据的一个前置：Q3 entry §7 记录 E1/E2 锚点
（窗口锚 `07e1be6`、E1=2/对照 1136、E2=3 条 biz allow），供 2026-Q4 审计关闭 #344 判据时比对。

## 5 收窄的真实影响（不夸大、不缩小）

- **F**：纯描述性修正；无运行时/gate 行为变化。修复后 A13 的 PR 阻塞判据 (b) 可满足、
  新增 (d)〔必停面不得脱离 `ask`〕把 ADR-034 的口头约束升为 reviewer 可核条款。
- **A**：write-once evidence + 一份 canonical schema 的规则化。SCHEMA §2.1 由硬编码常量改为
  推导规则 → 消除本次病因（常量无 gate 盯而静默过期）。
- **零** src/ / config / CI 姿态变更。

## 6 Work Breakdown（1 PR，`documentation/347-a6q3-cigates-sync`）

| # | 工件 | 动作 | AC |
|---|---|---|---|
| W1 | `policies/ci-gates.md` | `:67`/`:68` §5 表两行改 deny∪ask + 注；`:88` A13(b) 去失效引用 + 增 (d)；`:38` §4 审计项加 ask；连带 3 处硬编码计数去数字化；version 0.2→0.3 | AC-1..AC-4 |
| W2 | `evidence/ai-context-audit/2026-Q3.md` | 新建；23 面推导快照 + 冻结面 8/8 vs contract + §7 E1/E2 锚点 + F1-F11 findings | AC-5..AC-7,AC-9,AC-11 |
| W3 | `evidence/ai-context-audit/SCHEMA.md` | §2.1 推导规则；§3/§4 去硬编码（标历史条款） | AC-8 |
| W4 | `plans/[PLAN]_m-fu-ai-audit-2026-Q3.md` + `-Q4.md` | 补注册（Q3 completed / Q4 active，兼 #344 关闭者） | AC-12 |
| W5 | `plans/` INTAKE+PLAN | 本对 | — |
| W6 | `CHANGELOG.md` | `[Unreleased]` 条目 | — |

## 7 Verification

- `uv run pytest tests/unit tests/eval`（跑**全套**，非仅 gate validator——#217 教训）
- `uv run ruff check` · `uv run mypy src/mj_agent`
- `uv run python scripts/check_frontmatter.py --all` · `check_wikilinks.py`
  · `check_claude_skill_contracts.py --all` · `check_development_agent.py --all`
  · `check_agents_projection.py --all`
- 手动核验：`evidence/` 在 SCAN_ROOTS 外——Q3 hash 由独立脚本复算（先复现 Q2 4 面证算法）

## 8 验收标准（全部可执行自证；承 #341/#344「AC 逮住作者本人」教训）

- **AC-1** `grep -c "4 项必停文件" policies/ci-gates.md` == 0
- **AC-2** §5 表 `settings.local.json` 行不再声称持 `permissions.allow` 白名单
- **AC-3** `grep -c "红线（4 项必停文件" policies/ci-gates.md` == 0
- **AC-4** §4:38 审计项行含 `permissions.ask`
- **AC-5** `2026-Q3.md` frontmatter 合 SCHEMA §2 六字段
- **AC-6** `content_hash_snapshot` **恰 23 项**、逐项路径在盘、逐项 hash 可复算、
  且集合 == §2.1 推导规则输出（`uv run python`，非裸 `python`）
- **AC-7** Q3 §7 记 E1=2/对照 1136、E2=3 条、窗口锚 `07e1be6`
- **AC-8** `grep -cE "15-surface|6 \`\.claude/skills/mj-agent-infra|3 \`src/mj_agent/skills" SCHEMA.md` == 0
- **AC-9** `git diff --name-only develop... | grep -c 2026-Q2.md` == 0（write-once）
- **AC-10** full suite 全绿（pytest unit+eval + 全 checker + ruff + mypy）
- **AC-11** Q3 逾期 ~15 日 < SCHEMA:58 的 30 日门槛 → gap 自愿留痕（逐字核对 SCHEMA §3 后落笔）
- **AC-12** `ls plans/ | grep -c m-fu-ai-audit` == 2

## 9 Risks / Anti-goals

- **Anti**：不扩到 P4 gate 姿态；不改 `.claude/settings.json` 本体；不碰 #312 议题 1/2/3。
- **Risk**：`evidence/` 无 SAN_ROOTS gate → 手动核验兜底；hash 算法坑 → 已先复现 Q2 证明。
- **Risk**：A13(d) 新增条款改动 PR 阻塞 ruleset → 描述性收紧、与 ADR-034 同向，非 widening。

## 10 Owner Gates

- 4 项已拍（§7 INTAKE）。
- 剩：commit / push / PR 创建**单独拍板**；merge 交 Owner（classifier 拦 agent 直合 develop）。
- `Closes #347` 在本仓**不生效**（base=develop≠默认分支 main）→ merge 后**手动** `gh issue close`。

## 11 Next Step

- full-suite verify + 5-lens 对抗审查 → Owner-gated commit/push/PR
- merge 后独立小 PR flip 本 INTAKE+PLAN `state: completed` + `completed:` 字段
- Q3 M-FU 已 completed；Q4 M-FU active（2026-Q4 关闭 #344 判据时消费）
