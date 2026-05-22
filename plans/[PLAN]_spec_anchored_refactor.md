---
type: plan
slug: spec-anchored-refactor
summary: 长寿命 working plan 覆盖 mj-agent Maximum Spec-Anchored Refactor 的 Phase M0-M6 (~14-16 周) — 把当前 tri-track STANDARD + 30 ADR + ~100 docs 治理框架重构为 SDD Kernel + Capability Package + Business Policy 三柱结构，并落地 A1-A6 + B1 大型代码库 AI 协作最佳实践骨架；refines mj-agent-roadmap-v1.6 + data-agent-mvp-framework（不取代）；起源于 ADR-031 决策
state: active
version: 0.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-05-20
track: shared
refines:
  - plans/mj-agent-roadmap-v1.6.md
  - plans/[PLAN]_mj-agent-data-agent-mvp-framework.md
supersedes: []
related_adrs:
  - decisions/ADR-031_Spec_Anchored_Refactor.md
phase_progress:
  M0: completed                # PR #177 (Phase M0+M1 merged 2026-05-19/20)
  M1: completed                # PR #177
  M2: completed                # tag phase-m2-complete (2026-05-21)
  M3: pending
  M4: pending
  M5: pending
  M6: pending
---

# [PLAN] Spec-Anchored Refactor — Long-Lived Working Plan

> 长寿命 working plan；覆盖 Phase M0-M6 全程进度跟踪；伴随每 Phase PR merge 更新 `phase_progress`
> frontmatter 字段.
> **refines**：`plans/mj-agent-roadmap-v1.6.md`（不取代；本 plan 是 roadmap 内 SDD 治理 layer
> 的具体实施）+ `plans/[PLAN]_mj-agent-data-agent-mvp-framework.md`（不取代；本 plan 是 MVP
> framework 之上的治理重构）.

## §1 Scope

mj-agent **Maximum Spec-Anchored Refactor** — 把当前 tri-track STANDARD + 30 ADR + ~100 doc
治理框架重构为 **SDD Kernel + Capability Package + Business Policy** 三柱结构，并落地 A1-A6 +
B1 大型代码库 AI 协作最佳实践骨架.

实施蓝图来源（不入仓）：

- `D:/Document/My-Local-Vault/sdd-development/mj-agent/spec-anchored-calm-lampson.md` v2.2
- `D:/Document/My-Local-Vault/sdd-development/mj-agent/mj-agent-refactored-structure.md` v2.0

详 [decisions/ADR-031_Spec_Anchored_Refactor.md](../decisions/ADR-031_Spec_Anchored_Refactor.md).

## §2 Task Breakdown — Phase M0-M6

### Phase M0（~1 周；本 PR 落地）

**目标**：SDD Kernel skeleton + Business Policy（4 native 段 + 5 skeleton）+ scripts/sdd/ 5
skeleton 脚本 + PR/Issue 模板 + AGENTS.md + GLOSSARY.md + ADR-031 draft + 本 plan +
A1-A6+B1 实践骨架（4 subdir CLAUDE.md + .claudeignore + plugins.json + Stop hook skeleton）.

**不修改**：src/、tests/、infra/docker/、docs/（除 INDEX.md）、plans/ 现有文件、
.claude/scripts/、.claude/settings.json、.claude/hooks/ 现有 hooks、.mcp.json、pyproject.toml、
uv.lock、langgraph.json、config/.

**验收**：详 §4 Verification Phase M0 段.

### Phase M1（~2-3 周）

**目标**：5 pilot capability 各落地 9-artifact 套件（spec / requirements / design /
contracts / tasks / runbook / trace / evidence skeleton）+ capabilities/INDEX.md.

**5 pilot**：

1. `capabilities/data-agent/safe-sql/` — 核心安全主线（4 层 SQL 守则；ADR-006 + ADR-029）
2. `capabilities/data-agent/biz-catalog/` — 数据基础（qcm_catalog.yaml mirror）
3. `capabilities/data-agent/llm-provider/` — 双 provider 抽象（ADR-027）
4. `capabilities/infrastructure/docker-compose/` — 生产红线（ADR-026 4-file profile）
5. `capabilities/infrastructure/mcp-server-governance/` — 信任边界（ADR-028 13 server）

**修改**：sdd/workflows/new-capability.md（skeleton → 内容填充）；sdd/adapters/*.md（skeleton
→ 5 pilot 落地经验回填）.

**不修改**：src/、tests/、infra/docker/ 现有内容（contract 反向描述现有代码，不改实现）.

### Phase M2（~2 周）— ✅ COMPLETE @ tag `phase-m2-complete` (2026-05-21)

**目标**：sdd/adapters/ 6 文档内容填充（含 §BDD Rules + §TDD Rules）+ 6 新 contract 校验脚本
（warning mode）+ 现有 SKILL.md / system.md / 4 tools / Dockerfile / Compose 反向生成
contracts 补全（Phase M1 已建框架）.

**ADR-031 promote**：`state: draft → active` + `decision: proposed → accepted`（per RD7=B）.

**Achievements**（Stage A/B/C + partial E3β；Stage D 推 M3）：
- Stage A: 6 adapter validators + `_common` helpers landed (commit `b98badb` post-rebase)
- Stage B: 7 adapter docs M2 content fill 200-280 lines each (commit `1587ddc`)
- Stage C: 4 必停 surface freeze contracts (`13f0b05` + `edf8007` + `5b54f51` + `b3458fa`)
- Stage E (partial E3β): ci.yml 6 adapter gate warning enabled (commit `8ed34b7`);
  G1/G2/G9 toggle deferred per M3-FU-G1G2G9-IMPL (M0 skeleton)
- 9 必停 file freeze under freeze_anchor + HITL gate active
- 4 spec assumption drifts intercepted via pre-flight verification (V4 false claim /
  G1G2G9 skeleton / Stage A vs Stage B canonical drift / Stage A scripts uncommitted)
- 11 M3-FU plans registered for downstream resolution

### Phase M3（~2 周）

**目标**：关键 contract test 切 blocking + `tests/contract/` → `tests/contracts/` 改名 + BDD
step definitions 落地（tests/bdd/ 11 子目录）+ G28 contract-test-first blocking + Plan-vs-Diff
G4 blocking.

**M3 Task Breakdown — Follow-ups from Phase M2**（每条独立小 PR；不混入 M3 main work；便于
review / revert）：

- **M3-FU-V5-SUBFLAGS** — ✅ **COMPLETED 2026-05-21 (Phase M3 Stage A)**.
  `scripts/sdd/check_docker_contracts.py` 加 `--bdd` / `--tdd` /
  `--compose-config` 3 个 sub-flags（M2 V5 实施缓延决定；Q-A2）。Actual ~95 行
  (5 helper functions + argparse + wire-up). Output 2P/4W/0F with all sub-flags.
  CI V5 step updated to exercise all 3. Evidence:
  [[capabilities/infrastructure/docker-compose/evidence/reports/v5-subflags-landing]].
- **M3-FU-CLAUDE-SKILL-ADR** — ✅ **COMPLETED 2026-05-22 (Stage D D-3a)**. ADR draft landed
  at `docs/adr/[ADR]_032_Claude_Skill_Schema_Monitoring.md` (`state: draft / decision:
  proposed`; promote → accepted at next HITL Gate-3 after Layer 1 V4 promotion to blocking).
  Defines 3-layer drift-prevention regime: V4 validator gate (Layer 1) + PR template A12
  prompt (Layer 2; existing per Meta v2.1 §7.7) + A6 quarterly audit (Layer 3; per
  `evidence/ai-context-audit/SCHEMA.md`). Reframed scope landed verbatim — "prevent future
  deviation" replaces failed Q-A3 "fix existing deviation" premise. Cleanup: removed stale
  "gate name finalization deferred to M3-FU-HITL-ENUM" comment from
  `capabilities/infrastructure/mcp-server-governance/contracts/claude-skill.contract.yml`
  `hitl_required[]` (D-3d closing memo). resolved_by: D-3a commit; resolved_at: 2026-05-22.
- **M3-FU-HITL-ENUM** — HITL scenario enum 清理（去除重叠；收敛到稳定 8-10 项；统一
  `policies/ai-agent.md` HITL 列表 + `sdd/lifecycle.md` / `sdd/gates.md` HITL trigger 表述）
  （C5；M2 期间约定但未落实）；估时 ~1h；预计 diff ~50 行；依赖 M3 startup；独立小 PR.
- **M3-FU-S22-CROSSREF** — 蓝图 `spec-anchored-calm-lampson.md` §22 cross-ref 映射更新到 v2.3
  （`python.md→§22.1` / `langchain-agent.md→§22.4` / `prompt.md→§22.5` /
  `runtime-skill.md→§22.6` / `claude-code-skill.md→§22.7` / `docker-container.md→§23` /
  `bdd-tdd.md→§25`）（C1；M2 期间约定但未落实；blueprint 不入仓，plans/ 仅记 task pointer）；
  估时 ~0.5h；vault 文件 in-place 更新；依赖 M3 startup. **state: active**; disposition:
  out-of-repo deferred (新增 disposition 枚举 D-3e; vault-only manual edit by user; not Stage D
  PR scope; user 将在 vault 中独立完成 §22 cross-ref v2.3 更新). deferred_at: 2026-05-21.
- **M3-FU-BDD-TDD-RESTORE** — ✅ **COMPLETED 2026-05-22 (Stage D D-3b)**. `sdd/adapters/bdd-tdd.md`
  §Contract-Test-First Rule restored 4-line compact mention of "G28（PR-level test-first gate）
  与 6 adapter contract validator（schema 反向校验）协同关系" at line 229 (post Schema-layer
  二分; pre 手册 §25.6 gate list). File 280 → 284 lines (within plan body cap "不超 cap").
  resolved_at: 2026-05-22.
  **provenance**: Δ-1 path; canonical source = this M-FU plan body self-citation (lines 132-135
  pre-update; user-authored at `3755c94` plan registration), NOT git verbatim — trim was
  internal to `24b7ea3` (M2 content-fill) authoring Pass 1+2, pre-commit; trimmed verbatim never
  entered git as committed state. §7 Pre-flight Discipline 5th runtime application:
  source-provenance ambiguity intercept resolved by using user-authored canonical source.
- **M3-FU-A2-HOOK-IMPROVER-BODY** — **state: active**; disposition: deferred to M4
  (depends on EVAL framework Phase 2 maturity); blocked_by: D-1b skeleton landing
  (Stage D 2026-05-21) + EVAL framework readiness; scope: 替换 D-1b stubbed body
  (`Write-Host` + `exit 0`) 为 draft-producer 真逻辑 — 含 session signal analysis +
  proposed CLAUDE.md update draft 生成 + 写出到 `evidence/ai-context-audit/<YYYY-MM-DD>_session_<id>_proposed_claude_md_update.md`
  (per existing design commit `550e46b` + R-G21 mitigation per `spec-anchored-calm-lampson.md §10`).
  调用 D-1b 已定义的 `Test-PathAllowed` function 强制 allowlist + denylist 边界. Hook
  永不直接 write root CLAUDE.md; user manual review draft + 手动 apply. registered_at:
  2026-05-21. rationale: D-1b 落 skeleton + defense functions; 真逻辑推 M4 配 EVAL framework.
- **M3-FU-BODY-SHA256-STRICT-YAML-FALLBACK** — **state: active**; disposition: deferred to M4
  (independent validator investigation; 新增 disposition 枚举 D-3e); blocked_by: 调查
  `body_sha256()` 在 `scripts/sdd/_common/` 共享 utility 实际被几个 validator 调用（V3/V4/V7?）
  + 现 fallback 行为是否在这些 validator 上被实际触发; scope: 6 infra SKILLs 的 `Do not use
  for:` colon-space 让 strict-YAML 解析失败，`body_sha256` fallback 返回 full-file hash 而非
  body-only hash；正确算法 = canonical regex-strip（per `claude-skill.contract.yml` spec）；
  调查范围：列 `body_sha256` 被哪些 validator 调用 + 各 validator 是否依赖 body-only 语义，
  若是则修 `body_sha256` 改用 regex-strip primary path + strict-YAML fallback. registered_at:
  2026-05-21 (Stage D D-1c discovery). discovery_evidence: `871f889` commit body +
  `evidence/ai-context-audit/2026-Q2.md` §4b note. rationale: D-1c audit 已用正确算法所以
  baseline 数据正确；bug 在 utility function 本身，影响范围未知，需独立调查不挤压 Stage D scope.

### Phase M4（~2 周）

**目标**：Evidence required gate blocking（G8）+ Runbook 完整化（每 capability ≥ 100 行）+
HITL gates 完整化 + ADR-024 EVAL framework baseline 跑（与 mj-agent-runtime-eval-baseline skill
联动）+ G19-G22 BDD 自动化阈值.

### Phase M5（~2 周）

**目标**：Archive ceremony —

- 旧 tri-track STANDARD（v2.2 / Code_Side v1.1 / Agent_Side v1.2 / HITL_Prompt v1.1）→
  `archive/rule/` + `archive.yml` + TOMBSTONE.md
- 现 `docs/archive/adr/` 9 deprecated ADR → `archive/decisions/superseded/`
- 现 `docs/adr/` 30 active ADR → `decisions/`
- `docs/runbook/` → 各 capability runbook.md
- `docs/assessments/` → 各 capability evidence/assessments/
- `docs/infrastructure/git/` → `policies/git-branching.md` 扩充
- `docs/infrastructure/mcp/` → `capabilities/infrastructure/mcp-server-governance/`
- `infra/docker/` → `docker/`（compose 4-file 平移；ADR-026）
- `docs/INDEX.md` → redirect map（保留作 backward-compat grace period）

**HITL 重点**：大规模目录迁移（≥10 文件）触发 HITL；分 5 sub-PR 拆解.

**M5 Task Breakdown — Follow-ups from Phase M2**（独立小 PR；与 archive ceremony 主线分离；
便于 review / revert）：

- **M5-FU-TEMPLATE-ALIGN** — 整理 `sdd/templates/contracts/` 与 M2 adapter doc 演进形态对齐
  （M2 期 `sdd/templates/` 受 §3.5 保护不修改；M5 整理时回写）；已知 drift item:
  - `runtime-skill.contract.yml.template` 单 `skill_path` 形式 → 多 `skills[]` 集合形式
    （per `sdd/adapters/runtime-skill.md` §Standards M2 evolution）
  - **Open scope** — Phase M2 batch 3 / 4 + Stage C 余下进度发现的 template drift 项在此
    task description append（一项任务覆盖所有 template alignment；不另开 M5-FU entries）
  - Stage C batch 2 appendage（2026-05-21）：
    - `frontmatter_freeze` 字段 new in `#3 llm-provider/prompt.contract.yml` (commit `5b54f51`)；
      `sdd/templates/contracts/prompt.contract.yml.template` 需扩 schema 同步
    - `schema_compliance: ADR-013-native` 字段 new in `#4 mcp-server-governance/
      claude-skill.contract.yml` (commit `b3458fa`)；`claude-skill.contract.yml.template`
      需扩 schema 同步
    - `namespace_pattern` 字段 + inline declarative-only comment style (M2 / M3 timing) 新
      pattern；template 需 capture
    - `description_hash` 字段 (Option B vs option C/A) 新 pattern；template 需 capture canonical
      design choice
  估时 ~1-2h（视 drift 项规模）；scope 限 `sdd/templates/contracts/`；不修改 adapter docs
  自身；依赖 M5 startup；独立小 PR.

### Phase M6（~3-4 周）

**目标**：

- CLAUDE.md root 瘦身至 ≤150 行（Phase M0 仅加 Codex Status；M6 才大瘦身）
- 8 adapter gate 全 blocking
- EVAL framework baseline run PASS
- 4 个 evidence family skill 加载（`mj-agent-evidence-*`）
- 度量首份报告（capability 数量 / contract 数量 / evidence 覆盖率 / HITL trigger 频率）
- 全 test 通过（unit + contracts + bdd + tdd + integration + smoke）

## §3 Risk Control

详 ADR-031 §7 + 实施蓝图 `spec-anchored-calm-lampson.md` §10（23 项风险全集）.

本 plan 跟踪的关键风险：

| 风险 | 触发 Phase | 缓解 |
|---|---|---|
| R-G1 目录大规模迁移引用失效 | M5 | 启动前全仓 grep + redirect map + G14/G15 blocking |
| R-G4 CLAUDE.md 瘦身丢失关键约束 | M6 | M6 末跑 ≥ 5 个典型 AI 任务 case study 验证；4 项必停 / Codex Status / archive 规则强制保留 |
| R-G5 Archive 被 AI 误读为当前事实 | M5 | archive.yml ai_visibility 必填；G17 blocking；TOMBSTONE 顶部红 NOTE |
| R-G18 BDD 自动化负担 | M3-M4 | warning 1 月观察；高风险自动化阈值从 70% 降到 50% 试行 |
| R-G19 AI-generated code 难严格 red-green | M4-M6 | G26 改"PR body 含 test list + green pass" 软要求；G28 contract-test-first 仍严格 |

## §4 Verification（每 Phase 验收）

### Phase M0 验收命令

```bash
# 所有新文件创建到位
ls sdd/constitution.md sdd/lifecycle.md sdd/gates.md
ls sdd/workflows/*.md | wc -l    # 期望 6
ls sdd/adapters/*.md | wc -l     # 期望 7（含 bdd-tdd）
ls policies/*.md | wc -l         # 期望 9
ls scripts/sdd/*.py | wc -l      # 期望 5
test -f AGENTS.md && test -f GLOSSARY.md && test -f decisions/ADR-031_*.md
test -f .claudeignore && test -f .claude/plugins.json
test -f src/mj_agent/CLAUDE.md && test -f capabilities/CLAUDE.md
test -f tests/CLAUDE.md && test -f infra/docker/CLAUDE.md

# 新脚本可运行（dry-run 不报错）
uv run python scripts/sdd/check_capability_schema.py --dry-run
uv run python scripts/sdd/generate_index.py --dry-run

# 现有测试零回归
uv run pytest tests/unit -q
uv run pytest tests/contract -m contract

# Studio 启动 + check 仍 work（本 worktree 缺 .env 时跳过）
uv run mj-agent check
```

### Phase M1-M6 验收

详实施蓝图 `spec-anchored-calm-lampson.md` §6 各 Phase §5 验收命令.

## §5 AC（Acceptance Criteria）

### Phase M0 AC

- [x] §3.2 + §3.3 文件清单 100% 完成（含 skeleton 内容质量基线）
- [x] §4 验证命令全部 pass
- [x] 现有测试零回归
- [x] LangGraph Studio 启动正常（本 worktree 缺 .env 时降级为静态结构验证）
- [x] CLAUDE.md 仅增 ≤10 行 Codex Status 段（不大改）
- [x] AGENTS.md 顶部含 "Codex NOT in dev workflow / read-only review only" 红 NOTE
- [x] .claudeignore 不排除 src/mj_agent/biz_catalog/、src/mj_agent/tools/sql/、
      src/mj_agent/prompts/、src/mj_agent/skills/
- [x] .claude/plugins.json 含 pyright-lsp 启用配置
- [x] policies/ai-agent.md §Codex 非参与 + §Subagent Split + §Symbol-first Search 三段都写了
      native 内容（不是 TBD）
- [x] decisions/ADR-031 状态为 draft
- [x] capabilities/ 目录除 INDEX.md 外为空
- [x] 现有 docs/ 内容除 docs/INDEX.md 外未被修改

### Phase M1-M6 AC

详实施蓝图 `spec-anchored-calm-lampson.md` §9 验证与终标准对照（手册 §18 15 项）.

## §6 Phase 子包

每 Phase 独立 PR（Phase M5 拆 5 sub-PR）；commit type 优先 `docs` / `infra` / `refactor` 不掺
`feat` / `fix`（避免 changelog 误读）.

## §7 严格守约

- **不修改源代码 / 业务行为**（除 Phase M3 起的 contract reverse-engineering 改名与 Phase M5
  的 `infra/docker/` → `docker/` 平移）
- **不触发 4 项专属必停**（任一触发立即停下来 HITL，不"顺手做"）
- **不自动 commit / push**（每 Phase PR 由 user 手工 commit + push）
- **不调用 Codex**（per `policies/ai-agent.md` §1）
- **不删除现有 docs/**（Phase M5 才物理迁移；M0-M4 保留作 backward-compat grace period）
- **不 promote 任何 ADR**（除 ADR-031 在 Phase M1 末 + 现有 ADR 整体平移在 Phase M5；其余 ADR
  保持当前 state）

---

> *Phase M0 — `state: active`（plan 本身 active；不需 promote）.* `phase_progress` 字段在每
> Phase PR merge 后更新（per `mj-agent-flow-post-merge` skill Step 9 diff 草案 + user Edit）.
