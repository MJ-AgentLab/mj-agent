---
type: adr
adr_id: ADR-031
slug: spec-anchored-refactor
summary: mj-agent Maximum Spec-Anchored Refactor (Phase M0-M6) — restructure the tri-track STANDARD + 20 active ADR + ~100 docs governance corpus into the SDD Kernel + Capability Package + Business Policy three-pillar architecture, landing machine-readable contracts + capability lifecycle + CI gates.
state: active
decision: accepted
version: 1.0
owner: ranzuozhou
created: 2026-05-20
updated: 2026-08-10
domain: SYS
track: shared
ai_visibility: source-of-truth
---

# ADR-031: Spec-Anchored Refactor

## §1 Status

**state**：`active`
**decision**：`accepted`（promoted 2026-07-23，per §9 HITL Gate — Phase M1 末 promote 条件已达成：Spec-Anchored Refactor M0-M6 全部完成、#245 闭幕 2026-06-08；Owner ratify #372。历史：Phase M0 起草为 `draft`/`proposed`，per RD7=B 延迟 promote 至 Phase M1 末）.

## §2 Context

mj-agent 在 Phase 0 期间形成的 tri-track STANDARD（v2.2 / Code_Side v1.1 / Agent_Side v1.2 /
HITL_Prompt v1.1）+ 20 个 active ADR + ~100 个 `docs/` 文档构成了当前治理框架. 但实际开发中
暴露出以下结构性问题：

1. **缺乏机器可读 contract** — 20 个 ADR + 4 framework STANDARD 是人类可读的文字规则，CI 仅
   能校验 frontmatter / wikilink；行为契约靠 reviewer 记忆.
2. **缺乏 capability 作为组织单元** — 业务逻辑（safe-sql / biz-catalog / llm-provider /
   docker-compose / mcp-governance）散落在 `src/mj_agent/**`、`tests/**`、`docs/**`、
   `infra/**`、`.claude/**`；要全景理解某一能力的边界需读 ≥ 10 文件.
3. **缺乏 traceability** — REQ → CONTRACT → TEST → EVIDENCE 无机器可读链路；trace.yml 不存在.
4. **CLAUDE.md 行数膨胀** — 当前 ~580 行；新成员 / Claude Code session start 时 context 浪费
   严重；A1-A6 大型代码库最佳实践未落地.

业界参考：Anthropic 博客 "Effective context engineering for AI agents" 提出 7 项 A1-A6 +
B1 实践（split exploration from editing / Stop hook self-improvement / .claudeignore /
subdirectory CLAUDE.md / LSP integration / Review Cadence / minimal context budget）.

## §3 Decision

引入 **Spec-Driven Development (SDD) Kernel** + **Capability Package** 双柱重构：

1. **SDD Kernel**（`sdd/`）— 治理元规则中心：constitution / lifecycle / gates / workflows /
   adapters / templates. Source of truth for governance.
2. **Capability Package**（`capabilities/<domain>/<slug>/`）— 自包含工作单元：spec.yml /
   requirements / design / contracts / tasks / runbook / trace / evidence. Source of truth
   for business behavior.
3. **Business Policy**（`policies/`）— 9 native 文件分门别类治理（documentation /
   git-branching / ci-gates / ai-agent / claude-code-skill / docker-runtime / data-boundary /
   archive / security）.
4. **CI Gate 体系**（G1-G17 全局 + 8 stack-specific + G19-G28 BDD/TDD = ~33 gate；渐进启用）.
5. **A1-A6 + B1 大型代码库最佳实践骨架** — 4 个 subdir CLAUDE.md + .claudeignore +
   plugins.json + Stop hook + Review Cadence + Subagent Split + Symbol-first Search.

## §4 已确认 RD（10 RD 矩阵）

| RD | 决策 | 来源 |
|---|---|---|
| RD1 | (B) parallel 并存 — 旧 docs/ 在 Phase M0-M5 保留 | 用户确认（Phase M0 启动前） |
| RD2 | (A) 完整 archive 替换 — 旧 STANDARD 在 Phase M5 整体 archive ceremony | 用户确认 |
| RD3 | (C) `.claude/skills/` 物理 namespace 不重命名 — 用 SKILL_INDEX.md 5-layer 双索引提供逻辑分层 | 推荐默认值（用户接受） |
| RD4 | (C) `tests/` 11 子目录矩阵（unit / contracts 复数 / bdd / agents / prompts / docker / db / data_quality / integration / smoke + 其他）| 推荐默认值（用户接受） |
| RD5 | (C) 5 pilot capability 齐推 — safe-sql / biz-catalog / llm-provider / docker-compose / mcp-governance | 用户确认 |
| RD6 | (A) RQ-1 全量精细更新 — 不走"最小侵入"草案 | 推荐默认值（用户接受） |
| RD7 | (B) RQ-2 双轨 Adapter — Phase M0 ADR-031 落 draft；Phase M1 末 promote active | 推荐默认值（用户接受） |
| RD8 | (A) RQ-3 tests/ 11 子目录矩阵 | 推荐默认值（用户接受） |
| RD9 | (B) RQ-4 BDD 早 / TDD 晚 — BDD scenarios 在 Phase M1 起；TDD test list / red-green-refactor 在 Phase M3 起 | 推荐默认值（用户接受） |
| RD10 | (C) 18 skill 仅清单 / CLAUDE.md inline §17 / Phase 文件路径级 | 推荐默认值（用户接受） |

## §5 7 启用 Adapter 清单

| Adapter | 启用 Phase | Contract Output |
|---|---|---|
| python | M2 active | `python.contract.yml` |
| langchain-agent | M2 active | `agent.contract.yml` |
| prompt | M2 active | `prompt.contract.yml` |
| runtime-skill | M2 active | `runtime-skill.contract.yml` |
| claude-code-skill | M2 active | `claude-skill.contract.yml` |
| docker-container | M2 active | `docker.contract.yml` + `compose.contract.yml` + `runtime.expected.yaml` |
| **bdd-tdd** ★ 第 7 横切 | **M2 active** | `bdd-tdd.contract.yml`（不绑定单一 capability） |

**不启用**：`postgres-ddl`（仅引用；mj-agent 只读消费上游业务系统）、`etl`（mj-agent 不做
ETL）.

## §6 Phase M0-M6 路线图

| Phase | 周期 | 主要产出 |
|---|---|---|
| **M0** | ~1 周 | SDD Kernel skeleton + Business Policy + scripts/sdd/ + PR/Issue 模板 + AGENTS.md + GLOSSARY.md + ADR-031 draft + 长寿命 working plan + A1-A6+B1 大型代码库实践骨架. **不修改任何代码 / 测试.** |
| M1 | ~2-3 周 | 5 pilot capability 各落地 9-artifact 套件 + capabilities/INDEX.md + sdd/workflows/new-capability 内容填充 |
| M2 | ~2 周 | sdd/adapters/ 6 文档内容填充 + 6 新 contract 校验脚本 + 反向 contract 生成 |
| M3 | ~2 周 | 关键 contract test blocking + tests/contract → tests/contracts 改名 + BDD step definitions 落地 + G28 contract-test-first blocking |
| M4 | ~2 周 | Evidence + Runbook + HITL gates + EVAL framework baseline（ADR-024 联动）+ G19-G22 BDD 自动化 |
| M5 | ~2 周 | Archive ceremony — 旧 STANDARD 全集 → `archive/rule/` + 现 `docs/archive/` → `archive/decisions/superseded/` + `docs/` 拆分迁入 capability/policies/ + INDEX 自动生成 |
| M6 | ~3-4 周 | CLAUDE.md ≤150 行 + 全 adapter gate blocking + EVAL run PASS + 4 evidence skill 加载 + 度量首份报告 |

总周期：~14-16 周.

## §7 Consequences

### Positive

- 机器可读 contract → CI 校验 + reviewer 关注点收敛
- capability package → 业务能力自包含；新人 onboarding 路径清晰
- trace.yml → REQ → BDD → CONTRACT → TEST → TASK → PR → EVIDENCE 全链路审计
- CLAUDE.md ≤150 行 + 4 subdir CLAUDE.md → Claude Code context 预算合理
- A1-A6 大型代码库实践落地 → AI-assisted 开发的长期可持续性

### Negative / Risks

详 `plans/[PLAN]_spec_anchored_refactor.md` §Risk Control 段（spec-anchored-calm-lampson §10 23
项风险全集）.

主要风险摘录：
- R-G1 目录大规模迁移导致引用失效（Phase M5）
- R-G4 CLAUDE.md 瘦身丢失关键 4 项必停 / Codex Status / archive 规则
- R-G5 Archive 被 AI 误读为当前事实
- R-G19 TDD test-first 在 AI-generated code 不现实（per RD9=B 缓解）

### Neutral

- 旧 docs/ 在 Phase M0-M5 期间并存；develop always-shippable
- 现 20 active ADR 平移至 `decisions/`，编号 + content 保留

## §8 Implementation Plan Reference

详 `plans/[PLAN]_spec_anchored_refactor.md`（长寿命 working plan；覆盖 Phase M0-M6）.

实施蓝图来源（不入仓，仅供参考）：

- `D:/Document/My-Local-Vault/sdd-development/mj-agent/spec-anchored-calm-lampson.md` v2.2 —
  实施方案（22 模块 × 最大化采用方式 + Phase 0-6 分阶段 + 验收 + 回滚）
- `D:/Document/My-Local-Vault/sdd-development/mj-agent/mj-agent-refactored-structure.md` v2.0 —
  目标态全景结构.

## §9 HITL Triggers in this ADR

- Phase M0 启动前：用户确认 10 RD 决策（已完成；详 §4）
- Phase M1 末：ADR-031 状态 `draft → accepted` promote → HITL Gate ✅ **done 2026-07-23**（#372；Phase M1 末条件 = M0-M6 完成 #245）
- Phase M3 / M5 / M6：每 phase 启动前用户审蓝图 phase scope（避免漂移）
- 4 项专属必停 / cross-capability / archive ceremony / blocking gate 切换：全程 HITL

## §10 Related

- `sdd/constitution.md` — 三柱原则 + mj-agent native 补充
- `plans/[PLAN]_spec_anchored_refactor.md` — 长寿命 working plan
- `policies/*.md` — 9 native business policy
- ADR-000 / ADR-006 / ADR-008 / ADR-009 / ADR-011 / ADR-013 / ADR-014 / ADR-016 / ADR-024 /
  ADR-026 / ADR-027 / ADR-028 / ADR-029 / ADR-030 — 本重构所继承的现有 ADR 决策集

---

> *Promoted 2026-07-23 — `state: active` / `decision: accepted`* (per §9 HITL Gate；Phase M1 末 promote 条件达成——M0-M6 完成、#245 闭幕；Owner ratify #372). *历史：Phase M0 起草为 `draft` / `proposed`.*
