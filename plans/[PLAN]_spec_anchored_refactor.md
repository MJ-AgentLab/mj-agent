---
type: plan
slug: spec-anchored-refactor
summary: 长寿命 working plan 覆盖 mj-agent Maximum Spec-Anchored Refactor 的 Phase M0-M6 (~14-16 周) — 把当前 tri-track STANDARD + 20 ADR + ~100 docs 治理框架重构为 SDD Kernel + Capability Package + Business Policy 三柱结构，并落地 A1-A6 + B1 大型代码库 AI 协作最佳实践骨架；refines mj-agent-roadmap-v1.6 + data-agent-mvp-framework（不取代）；起源于 ADR-031 决策
state: completed
version: 0.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-08-12
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
  M3: completed                # PR #182 (Phase M3 close)
  M4:
    A: completed                # PR #183 merged 2026-05-22 (Stage A; +353 lines / 3 commits)
    B: completed                # PR #185 merged 2026-05-25T08:24:21Z (Stage B+C bundled; +920 lines / 12 commits; SHA 09adcd5)
    C: completed                # same PR #185
    D: completed                # PR #187/#188/#189/#190/#191 merged 2026-05-26..28 (5 units D-1..D-5; +2,492 insertions cumulative; SHA 0886f8a)
    E: completed                # E-0a #195 + E-0b #198 + E-1/E-2 BLOCKING flip #199 + E-3/G24 #194 + E-4 soak-period (#200-#209) all landed; E-4 soak EARLY-ACCEPTED on run-based criterion 2026-06-03 (owner risk acceptance — 10 clean blocking-runs #200-#209 + negative-test gate-block verification; calendar window waived; tracker: plans/stage-e-alpha-prime-e-4-soak.md)
    F: completed                # M4 closure 2026-06-03: 4/5 capabilities promoted drafting→active (safe-sql/biz-catalog/llm-provider/docker-compose; mcp-server-governance held → M4-FU-MCP-GOV-PROMOTION-DEFER); G26-G28 conditional → M6; EVAL baseline done #201. F-7 cluster: governance-insight capture done, but the 4 F-7 polish/code items (incl DOCSTRING-DRIFT-DETECTOR ~150-300 LOC) + G22-BDD-HELPERS-CONSOLIDATE were DESCOPED from M4 → post-M4 tail/M5 (M4-FU follow-ups, NOT M4-blocking); F-6 dropped per A-3 R-2 verdict
  overall: completed            # A+B+C+D+E+F done (2026-06-03); M4-FU tail rolls forward per §M4-FU Registry (F-7 polish + mcp-gov promotion → later; M-FU#9 → M6; 3 carries → M5); phase-m4-complete tag applied post-merge
  M5: completed                # M5 closure 2026-06-04 (re-scoped per #214): PR0 gate-prep #213 + PR1 template-align #212 + PR2 docker→docker/ #215 + PR3a active-ADR docs/adr→decisions/ #216 + PR3b deprecated-ADR→archive/decisions/superseded/ #217 + PR6 F-7 amend #218. STANDARD-archive + PR4a kernel-authoring + runbook/assessments/infra relocations + EVAL port → re-sequenced to M6 (draft-b finding); archive-gate blocking-flip → M6. docs/INDEX refs current (no redirect-map artifact). phase-m5-complete tag applied post-merge.
  M6: completed                # M6 closure 2026-06-08 (this PR; closes the M0-M6 refactor). DELIVERED: PR4a kernel-authoring (#220-#223) + PR4-OB orphan backfill (#224-#225) + PR4-refs D1-D3 (#226-#228) + PR4 tri-track STANDARD archive/consol (#229-#231) + claudemd-slim-v1 (#232) + PR4-flip G11/G12 BLOCKING (#233) + cross-cutting doc migration X1-X6 (#234/#236/#237/#238/#240/#241) + PR4-refs-gap (#235) + freeze-refresh w/ reproducible contract re-freeze (#242) + CLAUDE.md 601→150 aggressive slim w/ R-G4 6-case validation (#243) + first SDD-structure metrics report (#244). Full suite green (unit/eval/bdd/contract 414+). DEFERRED → Phase-2 (draft-b Q4 owner decision): EVAL framework authoring-spec port + EVAL baseline run + 4 mj-agent-evidence-* skills + scripts/sdd metrics-automation generator. ROLLED FORWARD as M6-FU: (1) 8-gate-full-blocking — G11/G12 + G21/G22 BLOCKING done; G14/G15/G17 + G23 remain WARNING → **M6-FU-G14G15-BLOCKING-FLIP** (needs archive/legacy + archive/capabilities forward-ref rework FIRST, then ci-blocking-gate-toggle owner must-stop) + M-FU#9 G23-TASKS-CURATION; (2) mcp-server-governance drafting→active still held (M4-FU-MCP-GOV-PROMOTION-DEFER); (3) pre-existing GUIDE-staleness sweeps (GitHub_Setup release-runbook path → cicd/; git-GUIDE archived-ref refs). ≥5 case-study ✅ (R-G4 via #243). phase-m6-complete tag applied post-merge.
---

# [PLAN] Spec-Anchored Refactor — Long-Lived Working Plan

> 长寿命 working plan；覆盖 Phase M0-M6 全程进度跟踪；伴随每 Phase PR merge 更新 `phase_progress`
> frontmatter 字段.
> **refines**：`plans/mj-agent-roadmap-v1.6.md`（不取代；本 plan 是 roadmap 内 SDD 治理 layer
> 的具体实施）+ `plans/[PLAN]_mj-agent-data-agent-mvp-framework.md`（不取代；本 plan 是 MVP
> framework 之上的治理重构）.

## §1 Scope

mj-agent **Maximum Spec-Anchored Refactor** — 把当前 tri-track STANDARD + 20 ADR + ~100 doc
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
  at `decisions/ADR-032_Claude_Skill_Schema_Monitoring.md` (`state: draft / decision:
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

#### Stage A (PR #183; merged 2026-05-22)

**Volume**: 3 commits / +353 insertions; V4 validator promote; ci.yml 8→9 BLOCKING gates; ADR-032 unblock.

**Key landings**:

- **A-1 V4-SKILLS-COMPLETE** — 34/34 SKILLs pass; `scripts/sdd/check_claude_skill_contracts.py` flipped
  warning → BLOCKING in ci.yml.
- **A-2 BODY-SHA256 + V4 Mode B joint investigation** — read-only joint investigation report at
  `evidence/ai-context-audit/2026-05-22_a2-investigation.md` (245 lines); 4 M4-FU candidates surfaced
  (Bundle B-α + M5+ defer set).
- **A-3 A2-HOOK readiness eval** — read-only readiness report at
  `evidence/ai-context-audit/2026-05-22_a3-readiness-eval.md` (97 lines); M5+ defer per R-2 verdict.

**F-6 dropped per A-3 R-2** (Phase M4 outline §1 Stage F 8 → 7 units; A2-HOOK improver body M5+ defer).

**§7 episodes**: 19 cumulative (carried to F-7 cluster amend).

#### Stage B+C (PR #185; merged 2026-05-25T08:24:21Z; SHA `09adcd5`)

**Volume**: 12 commits / +920 lines net (B 5 commits +181 runbook gap-fill / C 7 commits +739 evidence).
Base develop @ `6662529` (post PR #183 M4-A; 1-commit Dependabot #184 divergence merged-back during PR
#185 resolution).

**Stage B** (5 runbook gap-fill units; §6 SOPs capability-discretionary 5-data-point validated):

| Unit | Commit | File | Lines |
|---|---|---|---|
| B-1 | `c961dfc` | safe-sql/runbook.md (§3 extend + §6 3 SOPs; Path γ via Option β reframe) | +73 |
| B-2 | `c9a5e91` | biz-catalog/runbook.md (§3 extend + §6 3 SOPs; Path γ) | +63 |
| B-3 | `25c6c99` | llm-provider/runbook.md (frontmatter-only; Path β / Option b) | -1 (CRLF) |
| B-4 | `c8f37d6` | docker-compose/runbook.md (§6 2 SOPs volume + init; Path δ mid-scale) | +40 |
| B-5 | `46b0147` | mcp-server-governance/runbook.md (§1+§3+§4 micro 微调; Path β +5) | +5 |

**Stage C** (7 evidence units; 4 subdirs verification/+security/+runtime/×4; 7 distinct §3 schemas):

| Unit | Commit | Subdir | Lines | §3 Schema | §4 Finding |
|---|---|---|---|---|---|
| C-1a | `82ff0ab` | verification/ | 80 | Per-keyword pass rate | SUT-spec UNDOCUMENTED drift |
| C-1b | `92ebb9f` | verification/ | 95 | Per-rule-ID pass rate | SUT-runbook UNDOCUMENTED (10× magnitude) |
| C-1c | `26a7876` | security/ | 116 | Attack-vector × layer matrix | SUT-internal-docstring UNDOCUMENTED (1st sub-type; execute.py) |
| C-2 | `cf674a9` | runtime/ | 96 | Per-source freshness status | DOCUMENTED-drift positive null (biz-catalog governance maturity) |
| C-3 | `e7e6646` | runtime/ | 98 | Per-REQ probe status | SUT-internal-docstring UNDOCUMENTED (2nd; 3-file scope) |
| C-4 | `977203b` | runtime/ | 108 | Per-service smoke matrix | SUT-internal-docstring UNDOCUMENTED (3rd; +★ #C4-1 critical path correction) |
| C-5 | `d2cd5da` | runtime/ | 146 | Per-audit-task matrix | SUT-internal-docstring UNDOCUMENTED (4th; ★★★ 11-file cumulative scope) |

**Convention validation 5-data-point**: NO YAML frontmatter / H1 + 4-bullets / 6 sections / §3 adapts per
content nature / §6 cluster forward link.

**Cumulative metrics**:

- §0 substantive surfacing rate: **7/7 = 100%** (Stage C); Stage B→C cumulative **11/11 = 100%**.
- UNDOCUMENTED drift rate: 5/7 = 71% (Stage C); 1 documented-positive-null + 1 critical path correction.
- SUT-internal-docstring sub-type repeat rate: **4/7 = 57%** (leading; F-7 docstring drift detector
  candidate).
- Cumulative 11-file SUT-internal-docstring scope (4 src/ + .env.example + docker-compose.mj-agent.yml +
  6 SKILL.md).
- §7 episodes Stage B+C: 62 (Stage A 19 + Stage B 24 + Stage C 38 = 81 cumulative).

#### Stage D (5 PRs #187/#188/#189/#190/#191; merged 2026-05-26..28; develop SHA `0886f8a`)

**Volume**: 12 commits / +2,492 insertions cumulative across 5 units. Per Path β degraded
dual-stage reframe (D=implement validators / E α'=flip warning→blocking;original Path α
"flip pre-existing" found 5/5 validators absent at §0 — reframe locked at Stage D kickoff).

**Stage D 5 units** (BDD/TDD gate implementation;Section 5 stability validated cumulative
— 0 _common extension across D-3+D-4+D-5;3 reuse units via import-only):

| Unit | Commit | Gate | Mode | Files | Lines | Validator | Calibration |
|---|---|---|---|---|---|---|---|
| D-1 | `02e1502`+`6d44da7` | G8 capability evidence | BLOCKING | 3 | 155 | `check_capability_evidence_required.py` | Simple Solo -38% (n=1) |
| D-2 | `1500e4b` | G19 BDD scenario trace | BLOCKING | 4 | 693 | `check_bdd_scenario_trace.py` + `_common.bdd_helpers` (8th module deploy) | Compound +41% (n=1) |
| D-3 | `c820664` | G21 BDD acceptance | WARNING (phased) | 3 | 372 | `check_bdd_acceptance.py` (bdd_helpers FULL 5-func reuse) | Complex Solo +18% (n=1) |
| D-4 | `f938221` | G22 BDD unautomated justification | WARNING (R-10-8 phased) | 3 | 413 | `check_bdd_unautomated.py` (bdd_helpers 4-of-5 SUBSET) | Complex Solo +32% (n=2) |
| D-5 | `a254461` | G23 + G24 TDD pair | WARN+BLOCKING (R-12-3 immediate;dormant SKIP) | 3 | 425 | `check_tdd_test_list.py` single+subflag (V5 precedent;extract_headings reuse) | TDD Solo +1% (n=1) ★ best-aligned |

**G20 omission**: Phase M4 outline §1 Option A locked at Stage D kickoff (gates.md L96
"G21/G22 启用;G23/G24 warning" + L62 G23 "M4 warning / M6 blocking") — G20 step coverage
deferred to Phase M5+ (NOT in Stage D scope).

**Cumulative metrics**:

- ci.yml steps: 25 → **31** (+6;G8 + G19 + G21 + G22 + G23 + G24)
- `continue-on-error: true` count: 2 → **5** (G21 + G22 + G23 WARNING;G24 BLOCKING)
- 5 validators alive on develop (G19 full 16P/1W/0F + docker 3P/0W/0F + G21 14P/1W/0F +
  G22 0P/14W/0F + G23 15P/5W/0F + G24 0P/0W/0F SKIP)
- WARN baselines surfacing real curation gaps (honest signal):
  * G19+G21 cross-gate: `llm-provider/REQ-003` trace gap (M-FU#1 priority reinforced)
  * G22: 14W runbook 4-field justification absence (5 pilots × ~3 critical/high;M-FU#7)
  * G23: 5W tasks.md TDD test_list absence (5 critical/high tasks;M-FU#9 ACTIVATED)
- M-FU#3 sub-taxonomy calibration **4 patterns** locked-progress (Simple Solo n=1 / Complex
  Solo n=2 mean +25% / Compound n=1 / TDD Solo n=1)
- §7 episodes Stage D: ~79 (Stage A 19 + B+C 62 + D 79 = **160 cumulative** F-7 baseline)

**Key R-N progression locked Stage D全程** (v2→v12 cumulative):

- R-N v6 (D-1): lifecycle_state per sdd/lifecycle.md L69 SoT (most-specific wins)
- R-N v7 (D-2): trace.yml graceful (R-1) + quintuple→quadruple verify (R-2) + Step 1.5
  shared infra mini-review (R-3)
- R-N v8 (D-2): G19 FAIL/WARN/PASS Decision Matrix policy separation (helper FACTS /
  validator POLICY)
- R-N v9 (D-3): G21 4-layer policy (filter + tag + trace + evidence-DEFERRED) + Option B
  MVP pattern transplant
- R-N v10 (D-4): G22 2-layer + R-10-8 phased-rollout framing (L121 "M4 blocking" =
  end-state via Stage E α' flip per outline §4 R-1''; NOT spec deviation)
- R-N v11 (D-4): conditional cap raise (R-11-2b 400→460 pre-authorized) + Complex Solo
  variance flag
- R-N v12 (D-5): single+subflag dispatch + G24 BLOCKING immediate (NOT R-10-8 transplant)
  + branch-conditional SKIP + R-12-9 fire-path test 强制

#### M4-FU Registry (19 entries: 9 carry + 9 NEW Stage D trajectory + 1 post-Stage-E `M4-FU-MCP-GOV-PROMOTION-DEFER` [E-4-PR11]; Action-N-1 reconcile + Action-N-2 closure)

- **M4-FU-BODY-SHA256-DOCSTRING-CLARIFY** — **state: active**; disposition: Bundle B-α small docs scope;
  blocked_by: M4-A close; scope: 澄清 `scripts/sdd/_common/frontmatter.py::body_sha256()` docstring 关于
  Mode A (canonical regex-strip via `parse_native_frontmatter`) vs Mode B (per-validator `_strip_frontmatter`
  helpers; deferred) 的语义；~3-5 line docstring edit. surfaced_at: A-2 investigation 2026-05-22.

- **M4-FU-V4-MODE-B-CLEANUP** — **state: active**; disposition: Bundle B-α small docs scope; blocked_by:
  M4-A close; scope: 清理 `scripts/sdd/check_claude_skill_contracts.py` 中 V4 Mode B 残留 comments /
  dead-code 引用 (V4 已实施 Mode A only; Mode B 提案被 reject 后未清理); ~10-15 line edit. surfaced_at:
  A-2 investigation 2026-05-22.

- **M4-FU-BODY-SHA256-CANONICAL-REFACTOR** — **state: active**; disposition: M5+ defer (larger refactor
  scope); blocked_by: M5 archive ceremony freezes touch on `_common/frontmatter.py`; scope: refactor
  `body_sha256()` to use canonical regex-strip primary path + strict-YAML fallback (per 6 infra SKILLs
  `Do not use for:` colon-space surfaced in A-2); affects V3 + V7 calls (NOT V4 per Mode B reject).
  surfaced_at: A-2 episode #6.

- **M4-FU-V4-MODE-B-IMPL** — **state: active**; disposition: M5+ defer; blocked_by: M5 ADR-032 promote →
  accepted at Layer 1 V4 blocking promotion; scope: 评估 V4 Mode B implementation (per-skill
  `_strip_frontmatter` helper) 是否 still needed post Mode A 稳定运行; likely WITHDRAW per Mode A canonical
  adequacy; M5 final decision. surfaced_at: A-2 episode #3.

- **M4-FU-A2-HOOK-IMPROVER-BODY-M5-DEFER** — **state: active**; disposition: M5+ defer per A-3 R-2 verdict;
  blocked_by: D-1b skeleton + EVAL framework Phase 2 maturity + R-G21 mitigation validation; scope: 替换
  D-1b stubbed `Write-Host` + `exit 0` body 为 draft-producer 真逻辑 (session signal analysis + proposed
  CLAUDE.md update draft 生成 →
  `evidence/ai-context-audit/<YYYY-MM-DD>_session_<id>_proposed_claude_md_update.md`); 调用
  `Test-PathAllowed` allowlist + denylist 边界. Hook 永不直接 write root CLAUDE.md. surfaced_at: A-3
  readiness eval 2026-05-22.

- **M4-FU-OUTLINE-STAGE-B-WORDING-REFRAME** — **state: active**; disposition: F-7/F-8 cluster amend;
  blocked_by: F-7 closure; scope: 修正 Phase M4 outline §1 Stage B 描述 wording (per B-1 §0 #B1-1 critical
  reframe finding; outline "补 §L2/§L3/§L4" 段落 assumed §-numbered sections; reality runbook §1-§5 + L1/
  L1b/L4 as INSIDE §3 tags); ~5-10 line outline edit. originated_at: B-1 §0 2026-05-23 (Phase M4 Stage B
  kickoff).

- **M4-FU-DOCSTRING-DRIFT-DETECTOR** ★ **NEW (Stage C trajectory)** — **state: active**; disposition: F-7
  governance cluster amend; blocked_by: F-7 closure; trigger: C-1c+C-3+C-4+C-5 §4.1 SUT-internal-docstring
  sub-type 4/7 = 57% repeat rate (cumulative 11-file scope reveals systematic ADR archive ceremony lag
  across `.claude/skills/mj-agent-infra-*/` SKILL family + src/ + canonical infra YAML + env template);
  scope: implement docstring drift detector (类 C-2 4-mechanism governance maturity template OR
  `scripts/diff_biz_schema.py` pattern; scope = source module docstrings + SKILL.md frontmatter/description
  + canonical YAML/env templates references vs ADR active/archived state at PR review time);
  estimated_effort: ~150-300 lines Python detector + ci.yml integration + tests. surfaced_at: C-5 §4.1
  Grep finding 2026-05-25.

- **M4-FU-11-FILE-ADR-025-RECONCILE-SMALL-DOCS-PR** ★ **NEW (Stage C trajectory)** — **state: completed (E-4-PR8/#207 4 free comment/docstring refs [llm.py/config.py/.env.example→027, compose→026] + E-4-PR9 6 content_hash-locked infra SKILLs reconciled + contract re-frozen via mcp-server-trust-posture-change HITL; execute.py = no-ref N/A)**;
  disposition: independent post-Action 2 OR bundled into F-7 cluster amend; blocked_by: NONE (ready);
  trigger: C-5 §4.1 #C5-4 11-file cumulative SUT-internal-docstring scope discovered via Grep; scope:
  ~11-line edit across 11 files; per-file authoritative ADR target per
  `evidence/security/2026-05-23_sql_injection_audit.md` §4.1 +
  `evidence/runtime/2026-05-23_quarterly_audit_q2.md` §4.1 per-file tables (llm.py L3 → ADR-027; config.py
  L62 → ADR-027; execute.py L4-15 → 4-layer L1/L1b/L3/L4 per ADR-029; 6 SKILL.md per-file ADR targets;
  .env.example L54 → ADR-027; docker-compose.mj-agent.yml L2 → ADR-026); estimated_effort: ~30 min review
  + 11-line edit + commit + push + PR. surfaced_at: C-5 §4.1 2026-05-25.

- **M4-FU-F8-SKILL-STEP-8-WORKTREE-SYNC-FIX** ★ **NEW (F-8 in-flight discovery)** — **state: completed (E-4-PR7 2026-06-02; recipe already worktree-safe via git-sync Step 4 `git merge origin/develop`; #185-lesson guard note added to post-merge Step 8)**;
  disposition: small docs/skill PR OR bundled into F-7 cluster amend; blocked_by: NONE (ready); trigger:
  F-8 Step 8 skill recipe bug — bare-repo `update-ref` updates HEAD pointer but NOT worktree files (13
  stale files surfaced in PR #185 F-8 run; workaround `git reset --hard HEAD` applied); scope:
  `.claude/skills/mj-agent-flow-post-merge/SKILL.md` Step 8 recipe edit — replace bare-repo `update-ref`
  with worktree `cd develop && git pull --ff-only` pattern OR add explicit `git reset --hard` post
  update-ref. estimated_effort: ~3-5 line skill recipe edit. surfaced_at: F-8 PR #185 execution
  2026-05-25.

**9 NEW Stage D trajectory M-FU** (M-FU#1..#9; Action-N-1 propagated to registry per R-13-7
reconcile; category triage per R-13-* assessment):

- **M-FU#1 `M4-FU-LLM-PROVIDER-TRACE-YML-BDD-COMPLETE`** — **state: active**; **category: Stage E α'
  Prerequisite (G21 + G22 cross-gate)**; blocked_by: E-0 curation gate; scope:
  `capabilities/data-agent/llm-provider/contracts/trace.yml` add scenario name
  `effective_llm_api_key returns "EMPTY" sentinel for local provider when LLM_API_KEY is empty`
  to bdd 层 REQ-003 link (1-line additive); cross-gate signal G19 (D-2) + G21 (D-3) + G22 (D-4
  filter excludes) all surface this scenario — curation drives 3-gate resolution in tandem.
  surfaced_at: D-2 §0 #3 trace.yml audit 2026-05-26.

- **M-FU#2 `M4-FU-D-1-BRIEF-STEP-5-RUFF-MYPY-PARITY`** — **state: active**; **category:
  Informational (process discipline)**; blocked_by: NONE; scope: Step 5(a) brief template wording
  strengthen to `uv run ruff check --fix` (auto-fix flag mandatory; lesson registered after D-1
  I001 import sort recurrence + D-2..D-5 4× cumulative reapplication). surfaced_at: D-2 5(a) ruff
  fix recurrence 2026-05-26.

- **M-FU#3 `M4-FU-FLOOR-ESTIMATE-CALIBRATION`** — **state: active**; **category: Informational
  (calibration accumulator)**; blocked_by: NONE; scope: §9 Mid estimate calibration multi-AMEND
  across D-2/D-3/D-4/D-5; sub-taxonomy 4 patterns locked-progress: **Simple Solo** D-1 -38% (n=1;
  Mid -20% baseline) + **Complex Solo** D-3 +18% / D-4 +32% (n=2 mean +25%; Mid ×1.5 cap heuristic)
  + **Compound** D-2 +41% (n=1; Mid ×1.4) + **TDD Solo NEW** D-5 +1% (n=1; Mid ×1.0 best-aligned;
  single+subflag economy). E-stage data may surface NEW patterns (Curation / Flip Solo).
  surfaced_at: D-2 §9 + D-3 sub-taxonomy R-11-3 refinement 2026-05-27.

- **M-FU#4 `M4-FU-G21-EVIDENCE-PASS-RATE-STRICT`** — **state: active**; **category: Stage E α'
  Prerequisite (G21 flip)**; blocked_by: E-0 curation gate; scope: G21 strict mode tightening
  before BLOCKING flip — add `load_bdd_evidence` helper to `_common.bdd_helpers` (Section 5
  additive expansion + R-N v?? + Step 1.5 reinstate) + `evidence/bdd/*.md` frontmatter
  `pass_rate: 1.0` field check + justification fallback semantic (location TBD per bdd-tdd.md
  L161 wording "或 justification"); validator extend layer (d) from DEFERRED to actual check.
  surfaced_at: D-3 §0 Trigger #2 materialized + Option B selection 2026-05-27.

- **M-FU#5 `M4-FU-G21-RISK-CRITICAL-HIGH-FILTER-SCOPE-CLARIFY`** — **state: active**; **category:
  Stage E α' Prerequisite (G21 flip)**; blocked_by: E-0 curation gate; scope: spec wording
  ambiguity reconcile — gates.md L60 "关键 (key)" vs bdd-tdd.md L161 "@risk:critical|high"
  explicit clarification before BLOCKING flip; specific question: "关键" = critical|high or
  critical-only? mcp-server-governance medium-only G21 excluded? D-3 default critical|high per
  L161 authoritative most-specific-SoT. surfaced_at: D-3 §0 #3 5-pilot inventory 2026-05-27.

- **M-FU#6 `M4-FU-G22-MODE-WARN-TO-BLOCKING-FLIP`** — **state: active**; **category: Stage E α'
  Prerequisite (G22 flip)**; blocked_by: E-0 curation gate (M-FU#7 runbook); scope: G22 ci.yml
  flip `continue-on-error: true` → `false` + Severity.WARN → Severity.FAIL reclassification on
  curation gap (per L121 end-state via Stage E α' flip per outline §4 R-1''; R-10-8 phased-
  rollout framing); requires M-FU#7 runbook 0W validation pre-flip. surfaced_at: D-4 §0 L96
  vs L121 reframe + Option B + R-10-8 phased-rollout lock 2026-05-28.

- **M-FU#7 `M4-FU-RUNBOOK-JUSTIFICATION-CURATE-ALL-PILOTS`** — **state: active**; **category: Stage
  E α' Prerequisite (G22 flip) ★ LARGEST**; blocked_by: capability-owner curation per Option (b)
  (R-13-3); scope: 14 critical|high × unautomated scenarios × 5 pilots add `runbook.md`
  justification 4-field per scenario (原因 / 替代验证手段 / 升级触发条件 / 预计时间); SDD scaffold
  may provide template skeleton from observable facts (scenario tag + automation_status + ADR
  archive ceremony deferral) but owner authors domain specifics; per R-13-10 SDD/product
  boundary discipline. surfaced_at: D-4 §0 #4 5-pilot runbook gap 0/5 justification 2026-05-28.

- **M-FU#8 `M4-FU-G24-BUGFIX-BRANCH-WORKFLOW-READINESS`** (expanded per D-5 N-3) — **state:
  active**; **category: Stage E α' Prerequisite (G24 readiness)**; blocked_by: NONE (decoupled
  per R-13-9); scope: pre-first-bugfix-PR validate G24 predicate + bugfix workflow docs +
  **predicate precision review** (false-positive: config-only fix on bugfix may误阻 legit PR;
  false-negative: unrelated tests/ change may误 PASS) + bugfix-exempt edge cases (config-only /
  doc-only fix on bugfix branch) + possible escape hatch (PR label / commit trailer override) +
  first live-exercise simulation; E-3 decoupled track (parallel E-0 curation). surfaced_at: D-5
  §0 G24 BLOCKING immediate + branch-conditional SKIP safety analysis + R-12-9 fire-path test
  2026-05-28.

- **M-FU#9 `M4-FU-G23-TASKS-CURATION-SURFACE`** — **state: active**; **category: M6 Horizon (G23
  flips @ M6 per L62 designed phased)**; blocked_by: NONE (informational at Stage E α'); scope:
  5 critical/high priority tasks across 5 pilots missing `**TDD test_list**:` section in tasks.md;
  capability content maintenance scope per Option (b); SDD scaffold may provide test_list
  template from existing test files but owner audits/extends; **NOT Stage E α' blocking** (G23
  WARNING at M4 per L62 designed M4→M6 phased). surfaced_at: D-5 Step 5(d) dry-run 15P/5W/0F
  ACTIVATED 2026-05-28.

**M-FU Registry Drift Lesson** (R-13-7 + R-13-10): running F-8 lighter snapshots cumulative
mis-counted M-FU carry as "14" (likely conflation with §7 episode count OR pre-Stage-D total
estimation drift); plans/[PLAN] L237 authoritative SoT was always **9 entries** pre-Stage-D
(per Stage A 6 + Stage C 3 NEW); post-Stage-D total = 9 + 9 = **18** (correction landed in
this Action-N-1 PR). **Discipline forward**: M-FU count cite plans/[PLAN] §M4-FU Registry as
SoT; F-8 lighter snapshots quote registry directly (NOT self-accumulate). Implicit themes
(PHASE-MAP-RECONCILE referenced in D-3/D-4/D-5 commit bodies as cumulative AMEND target) NOT
counted as standalone M-FU entries — they are tracking aids,not deliverables。

**M-FU Category Triage** (Stage E α' readiness;per R-13-* assessment):

- **Cat 1 Stage E α' Prerequisite (6 entries)**: M-FU#1 / #4 / #5 (G21 flip) + #6 / #7 (G22
  flip) + #8 (G24 readiness) — must resolve BEFORE corresponding flip lands。
- **Cat 2 M6 Horizon (4 entries)**: M-FU#9 (G23 flips @ M6) + M4-FU-BODY-SHA256-CANONICAL-
  REFACTOR + M4-FU-V4-MODE-B-IMPL + M4-FU-A2-HOOK-IMPROVER-BODY-M5-DEFER (3 carry M5+ defers)。
- **Cat 3 Informational / Process (2 entries)**: M-FU#2 (--fix flag discipline) + M-FU#3
  (calibration accumulator)。
- **Cat 4 F-7/F-8 Cluster Amend (6 entries)**: M4-FU-BODY-SHA256-DOCSTRING-CLARIFY +
  M4-FU-V4-MODE-B-CLEANUP + M4-FU-OUTLINE-STAGE-B-WORDING-REFRAME + M4-FU-DOCSTRING-DRIFT-
  DETECTOR + M4-FU-11-FILE-ADR-025-RECONCILE-SMALL-DOCS-PR + M4-FU-F8-SKILL-STEP-8-WORKTREE-
  SYNC-FIX。

**Action-N-2 M-FU Registry Reconciliation Batch (E-4-PR5; 2026-06-02)**:

> Propagates Stage E α' resolutions per the §Action-N-2 trigger below, after #194-#203 landed.
> This batch table is the **current-disposition SoT**; the per-entry inline `state:` fields above
> record Stage-D-capture-time trajectory state (historical). Per registry-drift discipline
> (R-13-7/R-13-10): no new M-FU numbers pre-allocated; nothing silently kept active.

| M-FU / item | Disposition | Evidence | Follow-up |
|---|---|---|---|
| **M-FU#1** LLM-PROVIDER-TRACE-YML-BDD-COMPLETE | ✅ completed | #195 (E-0a) | none |
| **M-FU#4** G21-EVIDENCE-PASS-RATE-STRICT | ✅ completed | #195 (E-0a) | none |
| **M-FU#5** G21-RISK-CRITICAL-HIGH-FILTER-SCOPE-CLARIFY | ✅ completed | #195 (E-0a) | none |
| **M-FU#6** G22-MODE-WARN-TO-BLOCKING-FLIP | ✅ completed | #199 (E-1/E-2 flip) | none |
| **M-FU#7** RUNBOOK-JUSTIFICATION-CURATE-ALL-PILOTS | ✅ completed | #198 (E-0b) | none |
| **M-FU#8** G24-BUGFIX-BRANCH-WORKFLOW-READINESS | ✅ completed | #194 (E-3) | none |
| **M-FU#2** D-1-BRIEF-STEP-5-RUFF-MYPY-PARITY | ✅ completed (process lesson registered) | Stage D briefs | none |
| **M-FU#3** FLOOR-ESTIMATE-CALIBRATION | 🔵 informational (ongoing accumulator) | — | no PR action; calibration continues across phases |
| **M-FU#9** G23-TASKS-CURATION-SURFACE | ⏳ deferred → **M6** | per L62 G23 M4-warn/M6-block | M6 (G23 flip + `tasks.md` tdd.test_list curation) |
| M4-FU-BODY-SHA256-CANONICAL-REFACTOR | ⏳ deferred → **M6** | larger refactor of `body_sha256()`; build post-archive-ceremony on the settled tree | M6 |
| M4-FU-V4-MODE-B-IMPL | ✅ **WITHDRAWN** (M5-PR6, 2026-06-04) | Mode A schema-linting canonical + adequate; Mode B per-contract `skill_path` validation never needed (content_hash freeze enforced via mcp-server-trust-posture-change HITL) | none |
| M4-FU-A2-HOOK-IMPROVER-BODY-M5-DEFER | ⏳ deferred → **M6** | blocked_by EVAL Phase-2 maturity (an M6 deliverable) | M6 |
| M4-FU-BODY-SHA256-DOCSTRING-CLARIFY | ✅ **done** (M5-PR6) | `body_sha256()` docstring clarifies the Mode-A canonical `strip_frontmatter` path (Mode B withdrawn) | none |
| M4-FU-V4-MODE-B-CLEANUP | ✅ **done** (M5-PR6) | `check_claude_skill_contracts.py` docstring → Mode-A-only; the dead Mode B "two modes" promise removed + WITHDRAW recorded | none |
| M4-FU-OUTLINE-STAGE-B-WORDING-REFRAME | ✅ **resolved-moot** (M5-PR6) | the "补 §L2/§L3/§L4" wording lived in an ephemeral B-1 kickoff brief (not a tracked repo doc); the reframe finding (runbook §1-§5 + L1/L1b/L4 as tags inside §3) is recorded in this registry — no repo edit needed | none |
| M4-FU-DOCSTRING-DRIFT-DETECTOR | ⏳ deferred → **M6** | ~150-300 LOC detector + ci.yml + tests; build post-ceremony so its baseline is the settled tree | M6 |
| M4-FU-G22-BDD-HELPERS-CONSOLIDATE | ✅ **done** (M5-PR6) | G22 now imports `JUSTIFICATION_FIELDS` + `check_justification_fields` from `bdd_helpers` directly (shared with G21); the byte-equivalent D-4 local duplicate + its drift-guard test retired (G22 still 15P/0W/0F) | none |
| **M4-FU-MCP-GOV-PROMOTION-DEFER** ★ NEW (E-4-PR11) | 🟡 active → **post-M4 capability promotion** | E-4-PR11 (4/5 promoted; mcp-gov held drafting) | owner caveat-accept (medium-only) OR added @risk:high\|critical coverage |
| M4-FU-11-FILE-ADR-025-RECONCILE-SMALL-DOCS-PR | ✅ completed (E-4-PR8 + E-4-PR9) | 4 free refs (#207) + 6 locked infra SKILLs reconciled & contract re-frozen (E-4-PR9); execute.py no-ref N/A | none |
| M4-FU-F8-SKILL-STEP-8-WORKTREE-SYNC-FIX | ✅ completed (E-4-PR7) | recipe already worktree-safe (git-sync Step 4 `git merge`); #185-lesson guard note added to post-merge Step 8 | none |
| M3 carry-over `m3_fu_v4_skills_complete` | ✅ completed | #183 / #202 | none |
| M3 carry-over `m3_fu_skill_5segment_normalize` | ✅ completed | #203 | none |

**Outcome**: Cat-1 (6) all completed (E-0a/E-0b/E-1/E-2/E-3); M-FU#2 completed; M-FU#3 informational-ongoing; M3 carry-over (2) completed (#202/#203). **Remaining**: M-FU#9 → M6; 3 carries → M5; 6 → Stage F (F-7 cluster); of these `F8-SKILL-STEP-8` ✅ done (E-4-PR7/#206) and `11-FILE-ADR-025-RECONCILE` ✅ done (E-4-PR8/#207 4 free refs + E-4-PR9 6 content_hash-locked infra SKILLs reconciled & contract re-frozen; `execute.py` no-ref = N/A). Remaining F-7 cluster = 4 (DOCSTRING-CLARIFY / V4-MODE-B-CLEANUP / OUTLINE-WORDING / DOCSTRING-DRIFT-DETECTOR). Supplementary (not in the 18-entry triage): `M4-FU-G22-BDD-HELPERS-CONSOLIDATE` surfaced in #195 commit — post-Stage-E paired-edit consolidation; drift-guard test (`test_drift_guard_matches_g22_d4_constants`) enforces parity meanwhile. No `phase-m4-complete` tag, capability promotion, or Stage F closure in this PR *(E-4-PR5 snapshot — superseded by the **M4 Closure Batch** below, which executed all three in E-4-PR11)*.

**2 ★ Deferred to F-7 cluster amend** (NOT standalone M4-FU; per cumulative §4.1 disposition; bundle with
`M4-FU-11-FILE-ADR-025-RECONCILE-SMALL-DOCS-PR` OR F-7 batch):

- C-1a §4.1 SUT-spec drift (spec.yml REQ-001 "14 dangerous keywords" vs guardrail.py 16+SET SESSION = 17;
  reconcile via spec doc update OR special-case SET SESSION)
- C-1b §4.1 SUT-runbook drift (B-1 `c961dfc` runbook §3 L99 "10000" vs precheck.py L155 "1000" per
  authoritative; 10× magnitude wording correction)

**M4 Closure Batch (E-4-PR11; 2026-06-03)** — Stage F closure executed; soak **early-accepted on run-based criterion** (owner risk acceptance):

| Item | Disposition | Evidence |
|---|---|---|
| G21/G22 soak | ✅ **early-accepted** (run-based, N≥5 clean runs; calendar window waived) | post-flip blocking CI runs: #200-#204 = 5 genuine post-flip + #205-#209 same-workstream prep PRs, **all clean** (0 FP / 0 real-violation). G24 = branch-conditional (SKIP on these non-bugfix doc PRs → no G24 soak signal expected; fire-path validated separately #194). + **2 negative tests proving the gate blocks**: (a) runbook 4-field break → G21+G22 both 9P/6W/0F exit 1; (b) @REQ-tag drop → G21 14P/0W/1F exit 1; both restored clean |
| Capability promotion | ✅ **4/5** drafting→active | safe-sql / biz-catalog / llm-provider / docker-compose `lifecycle_state: active`; G8 4P/0W/0F/**1SKIP (=mcp-gov, held drafting)**; `INDEX.auto.md` regenerated (G9 ✓) |
| `infrastructure.mcp-server-governance` | ⏸ **held** → `M4-FU-MCP-GOV-PROMOTION-DEFER` | medium-only (G21/G22 SKIP — scenarios @risk:medium, no coverage); readiness rests on own contracts + evidence; promote on owner caveat-accept OR added @risk:high\|critical coverage |
| F-7 cluster (4) + G22-BDD-HELPERS-CONSOLIDATE | ⏩ **roll forward** (post-M4 tail / M5) | DOCSTRING-CLARIFY / V4-MODE-B-CLEANUP / OUTLINE-WORDING / DOCSTRING-DRIFT-DETECTOR — non-blocking polish/code M4-FU; governance insights captured in F-7 note below |
| G26-G28 conditional + EVAL placeholders | ⏩ G26-G28 → M6; EVAL baseline ✅ #201 | `eval.baseline.pass_rate=1.0` |
| `phase_progress.M4` | ✅ **completed** (E+F) | `phase-m4-complete` tag applied post-merge; the Stage-E sub-tag `phase-m4-stage-e-alpha-prime-complete` is **subsumed by `phase-m4-complete`** (not separately applied) |

> **NEW M4-FU** `M4-FU-MCP-GOV-PROMOTION-DEFER` (state: active; category: post-M4 capability promotion): promote `infrastructure.mcp-server-governance` drafting→active once (a) owner accepts the medium-only G21/G22-SKIP posture, OR (b) @risk:high|critical scenario coverage added. blocked_by: owner caveat-accept OR coverage. Named per post-Stage-D convention (no ad-hoc number; registry SoT per R-13-7/R-13-10).

> **Soak early-accept rationale (owner risk acceptance, 2026-06-03)**: R-13-6's 1–2 wk *calendar* window is a self-imposed governance criterion, not a hard technical gate. Owner re-based it to a **run-based** criterion (N clean blocking-runs) — satisfied by #200-#209 (10 PRs, 0 FP / 0 real-violation) + actively verified the gate blocks on a real violation (negative test). Tradeoff accepted: trades calendar time-coverage for speed; risk low given clean signal + simple `--strict` gate on a stable 0W baseline + verified blocking (2 negative tests). Auditable override, **not** a silent skip. **Provenance**: owner authorized the run-based re-base + risk acceptance in-session on 2026-06-03; this E-4-PR11 closure PR is the recorded artifact, reviewed at merge. **N threshold**: ≥5 clean post-flip blocking runs (satisfied: #200-#204 genuine post-flip + #205-#209 prep, 0 FAIL).

#### F-7 Cluster Amend Trajectory Note

**Cumulative §7 episodes for F-7 cluster amend**: **160 total** (Stage A 19 + Stage B 24 + Stage C 38
+ Stage D ~79;updated post-Action-N-1 reconcile @ this PR).

**Disposition pattern** (per cumulative §4.1 precedent established Stage C):

- §0 pre-flight intercepts (per-unit brief synthesis stage) accumulated to F-7
- §4.1 in-evidence drift documentation → F-7 observation per C-1a/b/c+C-3/C-4/C-5 cumulative
- NOT M4-FU registry inflation (orthogonal: M-FU captures concrete deliverables; §7 captures epistemic
  observations + intercept patterns)
- F-7 single batch amend at Phase F closure aggregates all 81 episodes + governance insights

**F-7 governance insight key candidates**:

- **Docstring drift detector** (per `M4-FU-DOCSTRING-DRIFT-DETECTOR` ★; 11-file evidence systematic across
  Stage C SUT-internal-docstring sub-type 57% repeat rate)
- Spec-anchored discipline locks spec/behavior/runbook (PR review + freeze contracts) but in-source
  docstrings + SKILL descriptions + env templates lag behind ADR archive ceremonies (PR-Γ 2026-05-11
  ADR-025 split was last touch; subsequent updates didn't propagate to in-source references)
- **PHASE-MAP-RECONCILE pattern** (Stage D cumulative): gates.md L96 generic phase mode wording
  ("启用" / "warning") repeatedly conflicts with bdd-tdd.md specific row schedule overrides
  (L121 G22 "M4 blocking" / L62 G23 "M4 warning/M6 blocking" / L63 G24 "M4 blocking") —
  D-2 R-N v6 most-specific-SoT-wins discipline established; D-3 R-9-1 spec scope expansion;
  D-4 R-10-8 phased-rollout reframe (outline grounded) vs D-5 R-12-3 phased NOT applicable
  (no outline grounding for G24). Pattern lesson: gates.md L96 generic mode column should
  reference specific-row overrides explicitly OR phase-map outline §4 R-1'' coverage expand.
- **G24 dormant-BLOCKING pattern** (D-5 R-12-9): branch-conditional BLOCKING gate landed without
  live-fire on landing PR (non-bugfix branch SKIP); R-12-9 unit-test fire-path 强制 covers 3
  cases (PASS+FAIL+SKIP) to validate before first live-exercise via real bugfix/* PR. Discipline
  forward: dormant BLOCKING gates require explicit fire-path test + M-FU pre-first-fire readiness.
- **M-FU Registry SoT discipline drift** (R-13-7+R-13-10): running F-8 lighter snapshots cumulative
  mis-counted carry "14" vs plans/[PLAN] L237 SoT "9" pre-Stage-D; Action-N-1 reconciled to 18
  total post-Stage-D + drift lesson registered. Discipline forward: cite plans/ SoT directly;
  snapshots quote not accumulate.

**F-8 closure** ✅ **(2026-06-03; E-4-PR11)**: master plan `phase_progress.M4: completed` — Stages D+E+F all landed; `phase-m4-complete` tag applied post-merge.

#### Stage E α' Outline (planning kickoff @ this PR Action-N-1; sub-stages E-0..E-4 per R-13-1)

**Goal**: G21+G22 BLOCKING flip (curation prereqs done) + G24 bugfix workflow readiness
(decoupled per R-13-9) + EVAL framework baseline (per outline §4 R-1'') + soak window
+ Action-N-2 M-FU batch resolutions + plans/ Stage E close。

**★ Scoping decision (R-13-3 lock-in)**: **Option (b) — capability-owner curation;SDD
scaffold-only;infra/product boundary**。 G21/G22 WARN signals come from capability artifact
content gaps (runbook justification / trace.yml bdd binding);SDD refactor team **does NOT**
author product-domain content (domain expert authors;avoids anti-fabrication risk of fake
justification defeating gate purpose);applies even when owner = same person (different hats:
capability-owner authors specifics / SDD-team scaffolds + flips gates)。Scaffolding bridge:
Claude Code may generate template skeletons from observable facts (scenario tags / automation_
status / known ADR deferrals) but owner fills domain specifics。SDD/product boundary
discipline (R-13-10) prevents:
1. SDD writing capability product content (out-of-bound;HITL violation)
2. SDD fabricating plausible-but-wrong justifications (defeats G22 semantic)

**Decouple tracks (R-13-9 lock-in)**:

- **Curation-dependent track**: E-1 + E-2 flips gated on E-0 curation completion
- **Curation-independent track**: E-3 (G24 readiness) + E-4-prep (EVAL framework harness) =
  pure SDD infra,not waiting on capability content → 并行推进;avoids Stage E α' stalling
  if curation cadence slow

**Sub-stage decomposition**:

| Sub-Stage | Scope | Dependencies | Write-Scope | Est. Volume |
|---|---|---|---|---|
| **E-0** | Curation prerequisite **gate** (NOT SDD-execution sub-stage):#1 trace add (1 line) + #4 evidence framework + #5 spec clarify (sdd/ amend) + #7 runbook 14W (★ LARGEST: 5 pilots × ~3 critical/high × 4-field;~500-800 lines artifact writes);SDD-team provides templates (R-13-3 scaffold) + verify WARN→0 → unlocks flips | Stage D close ✅ | ★ owner-authored `capabilities/*/{trace.yml, runbook.md}` + sdd/* spec amend | Largest (~500-800 lines;mostly owner content) |
| **E-1** | G21 BLOCKING flip (ci.yml `continue-on-error: true` → `false` + WARN→FAIL Severity reclassification per R-N v8 R-1 + verify 0W) + EVAL baseline integration | E-0 G21 prereqs done (#1/#4/#5) | ci.yml + `check_bdd_acceptance.py` + tests | Small (~80-150 lines;类 D-3 retrofit) |
| **E-2** | G22 BLOCKING flip (#6 ci.yml reclass + verify runbook 0W) + EVAL baseline integration | E-0 G22 prereqs done (#6/#7) | ci.yml + `check_bdd_unautomated.py` + tests | Small (~80-120 lines) |
| **E-3** ⟂ | G24 bugfix workflow readiness — #8 predicate precision review + bugfix-exempt edge cases + escape hatch + first live-exercise simulation | M-FU#8 ready (NO E-0 dep;**parallel** per R-13-9) | `check_tdd_test_list.py` validator extension + tests + docs | Medium (~150-250 lines) |
| **E-4** | Soak window (1-2 wk per R-13-6) + EVAL baseline harness completion (`tests/eval/` extensions per outline §4 R-1'' + ADR-024) + Action-N-2 M-FU resolutions batch + plans/[PLAN] Stage E close + `phase-m4-stage-e-alpha-prime-complete` tag eligible | E-1..E-3 done + soak observed clean | plans/ + tests/eval/ | Medium (~200-400 lines) |

**Stage E α' progress (updated 2026-06-02)**:

- ✅ **E-0a** — M-FU#1/#4/#5 (G21 evidence predicate + trace fix + spec amend) — PR #195
- ✅ **E-0b** — M-FU#7 runbook 4-field justification curation (4 pilots × 15 critical|high scenarios; +261 lines) → G21/G22 15W→0W — PR #198
- ✅ **E-1/E-2** — G21+G22 combined BLOCKING flip (`continue-on-error:false` + `--strict`) — PR #199 (2026-06-02)
- ✅ **E-3** — G24 bugfix workflow readiness — PR #194
- ✅ **E-4** — **complete (2026-06-03)**: EVAL baseline (#201) + M3 carry-over closed (#202/#203) + Action-N-2 registry reconciled (#204) + promotion-readiness preflight + soak checkpoint (#205) + F8 worktree-safe fix (#206) + 11-FILE-ADR-025 reconcile (#207/#208) + Stage F prep (#209) + **M4 closure (E-4-PR11): G21/G22 soak EARLY-ACCEPTED on run-based criterion (owner risk acceptance — 10 clean blocking-runs #200-#209 + negative-test gate-block verification; calendar window waived) + 4/5 capabilities promoted drafting→active (safe-sql/biz-catalog/llm-provider/docker-compose; mcp-server-governance held → `M4-FU-MCP-GOV-PROMOTION-DEFER`) → `phase_progress.M4` completed** — trackers `plans/stage-e-alpha-prime-e-4-soak.md` + `plans/stage-f-m4-closure-prep.md`

> **Impl reconcile**: E-1/E-2 actual mechanism = `--strict` (WARN→exit 1 via `_common/cli.py` `Summary.exit_code`), **not** the "WARN→FAIL Severity reclassification" wording in the E-1 row above (L525). Per the E-1/E-2 decision no validator severity was rewritten.

**EVAL baseline state** (per pre-flight findings):

- Existing harness: `tests/eval/` (golden_seed.jsonl + test_component_against_seed.py + test_golden_seed_schema.py)
- ✅ **E-4-PR2 baseline established (2026-06-02)**: `uv run pytest tests/eval -q` → 93P/0F/0skip exit 0;
  `eval.baseline.pass_rate = 1.0` (component + golden-seed schema; no live dep). Evidence:
  `capabilities/data-agent/safe-sql/evidence/reports/2026-06-02_adr-024-eval-baseline.md`. Outcome-layer
  (live DB) eval remains smoke-only per ADR-024.
- G21 tiered baselines defined (bdd-tdd.md L109): 70% baseline / 100% target / 50% advisory
  (RD9=B 试行;M3 末批观察 1 月再定)
- E-4 work scope: baseline measure framework establish + soak observation

**Soak window definition** (R-13-6;to refine in E-4 brief):

- Duration: 1-2 weeks of CI runs without regression (default;refine per real cadence)
- Pass standard: 0 FAIL across G21+G22+G24 over soak window
- Monitoring: CI run history daily check;M-FU triggered on FAIL surge
- Exit criteria: `phase-m4-stage-e-alpha-prime-complete` tag eligible

**Action-N-2 trigger** ✅ **FIRED (E-4-PR11; 2026-06-03)**: soak EARLY-ACCEPTED on run-based
criterion (calendar window waived per owner risk acceptance) → Stage E α' closed + M-FU resolutions
batch propagated (M-FU#1..#9 resolved/deferred + carry M-FU updated) + Stage F closed (M4 complete);
see **M4 Closure Batch** above for the promotion + soak-accept disposition。

### Phase M5 ✅ **COMPLETED 2026-06-04**（~1-1.5 周；**re-scoped 2026-06-03** per draft-b finding — STANDARD archive + 跨切面迁移 + 新增 PR4a 全部 → M6）

> **M5 closure (2026-06-04)**: re-scoped M5 (docker + ADR structural moves) done — PR0 gate-prep #213 · PR1 template-align #212 · PR2 `infra/docker/`→`docker/` #215 · PR3a 20 active ADR `docs/adr/`→`decisions/` (rename) #216 · PR3b 9 deprecated ADR→`archive/decisions/superseded/` #217 · PR6 F-7 amend #218. **Deferred to M6** (draft-b finding): 4 tri-track STANDARD archive→`archive/rule/` + the **PR4a kernel-authoring** prereq + runbook/assessments/infra relocations + EVAL spec port + the **archive-gate blocking-flip** (G11/G12/G14/G15 → blocking once `archive/rule/` + its manifests exist & the 47 forward-ref WARNs resolve). `phase-m5-complete` tag applied post-merge.

**目标**：低风险结构迁移（**不依赖** doc-governance kernel backfill）—

- 现 `docs/adr/` 20 active ADR → `decisions/`（per-file RENAME `[ADR]_NNN_*` → `ADR-NNN_*`；ADR-031 已在 `decisions/`）；现 `docs/archive/adr/` 9 deprecated ADR → `archive/decisions/superseded/` + `archive.yml` + TOMBSTONE（**PR3**）
- `infra/docker/` → `docker/`（compose 文件 **RENAME** `docker/compose*.yml` per decision-a 2026-06-03；ADR-026）（**PR2**；唯一 build-breaking 迁移）
- `docs/INDEX.md` → redirect map（**仅覆盖本期 ADR + docker 迁移**；STANDARD/runbook/assessments/infra 行待 M6）
- ✅ 已落：M5-PR0 archive catch-gates（#213，WARNING-mode）+ M5-PR1 template-align（#212）

> **Re-sequenced to M6（draft-b 2026-06-03 finding + owner decision）**：4 tri-track STANDARD 归档 +
> 跨切面文档迁移（`docs/runbook/`→capability runbook.md / `docs/assessments/`→`policies/` / `docs/infrastructure/git`→`policies/git-branching.md` / `docs/infrastructure/mcp`→mcp-server-governance capability）
> + **新增前置子步 PR4a kernel-authoring**。原因：M2 只回填了 `sdd/adapters/*`（v0.2 ready），未回填
> doc-governance pillar（`policies/documentation.md` / `sdd/constitution` / `sdd/gates` 仍 M0 skeleton "TBD Phase M2"）；
> **0/4 STANDARD 今天可被干净 supersede**——直接归档会丢失 A1-A6/OB1-OB5 定义、`track` frontmatter 字段规范、
> 12-type doc taxonomy、17-stage HITL loop 等 ~50 living files 依赖的治理。详 .claude `m5-standard-successor-mapping-draft`。
> **Owner-approved homes（2026-06-03）**：A1-A6/OB + 12-type taxonomy + `track` 字段 → `policies/documentation.md`（填 M0 stubs）；
> 17-stage execution loop → 新 `sdd/workflows/execution-loop.md`；EVAL authoring spec → defer 到 M6 EVAL 工作。

**HITL 重点**：docker move 是唯一 build-breaking 迁移（contract `path`+`freeze_anchor` 同 commit；V5 BLOCKING）；
ADR rename 双倍 wikilink 改写面；archive catch-gate（#213）blocking-flip 逐 move-PR HITL pause（policies/ai-agent.md HITL #5）.

**M5 Task Breakdown — Follow-ups from Phase M2**（独立小 PR；与 archive ceremony 主线分离；
便于 review / revert）：

- **M5-FU-TEMPLATE-ALIGN** ✅ **DONE（#212 / M5-PR1, 2026-06-03）** — 整理 `sdd/templates/contracts/` 与 M2 adapter doc 演进形态对齐
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

### Phase M6（~3-4 周）— ✅ COMPLETE @ tag `phase-m6-complete` (2026-06-08; closes M0-M6)

> **Closure (2026-06-08)**: DELIVERED archive ceremony + kernel-authoring + cross-cutting
> migration X1-X6 + freeze-refresh + CLAUDE.md ≤150 slim (R-G4 validated) + metrics report +
> green test suite (see `phase_progress.M6` for the per-PR list). DEFERRED → Phase-2: EVAL
> framework port + baseline + 4 evidence-family skills + metrics-automation. ROLLED FORWARD
> as M6-FU: full-gate-blocking (G14/G15/G17/G23 flip — prereq forward-ref rework + owner
> ci-blocking-gate-toggle must-stop), mcp-gov promotion, GUIDE-staleness sweeps. The goals
> below are the original M6 plan; ✅ = done, ⏭ Phase-2, 🔁 M6-FU annotations inline.

**目标**：

- ✅ **Archive ceremony（从 M5 re-sequenced；draft-b 2026-06-03 finding）** — 前置 **PR4a kernel-authoring**：把
  doc-governance gap content 回填进 kernel/policies（A1-A6/OB1-OB5 + 12-type taxonomy + `track` 字段 →
  `policies/documentation.md`；archive-trigger 量化 + active-path-stability → `policies/archive.md`；working-doc
  lifecycle → `sdd/lifecycle.md`；17-stage loop → 新 `sdd/workflows/execution-loop.md`）；然后 **PR4** 4 tri-track
  STANDARD → `archive/rule/` + 跨切面文档迁移（runbook→capability / assessments→policies / infra/git→git-branching /
  infra/mcp→capability）+ ref repoint + full INDEX redirect。PR4a 规模 ≈ 被 M2 跳过的 doc-governance backfill
  子阶段（详 .claude `m5-standard-successor-mapping-draft`；owner-approved homes 见 §M5 re-sequence note）
- ⏭ **Phase-2**: EVAL authoring spec（Agent_Side §4 / ADR-024）port → EVAL framework 工作（draft-b Q4 defer 决策）
- ✅ CLAUDE.md root 瘦身至 ≤150 行（#243: 601→150；R-G4 6-case validated）
- 🔁 **M6-FU**: 8 adapter gate 全 blocking（G11/G12 + G21/G22 done；G14/G15/G17 + G23 仍 WARNING → M6-FU-G14G15-BLOCKING-FLIP：需 forward-ref rework + owner ci-blocking-gate-toggle must-stop）
- ⏭ **Phase-2**: EVAL framework baseline run PASS
- ⏭ **Phase-2**: 4 个 evidence family skill 加载（`mj-agent-evidence-*`）
- ✅ 度量首份报告（#244: `evidence/metrics/2026-06-08_sdd_structure_metrics.md`；自动化 generator → Phase-2）
- ✅ 全 test 通过（unit/eval/bdd/contract green；integration/smoke skip-clean no-creds）

#### Post-M6 Completion-Audit Disposition Registry（M6-FU batch; 2026-06-10）

> 完成度评估（vault `mj-agent-refactor-completion-assessment.md` v1.0 §4.2 "登记外缺口"）
> 全仓核验后的 4-PR 修复链（audit PR1-PR4）处置总账 — 目标：消灭全部"登记外"状态，每项
> 要么修复、要么 ceremony 登记（defer / WITHDRAWN / decline）。沿 Action-N-2 批次表格式；
> 本表为这批条目的 current-disposition SoT。lifecycle 不禁对 `state: completed` plan 追加
> 登记段（本段即追加；plan 主体不动）。

| M-FU / item | Disposition | Evidence | Follow-up |
|---|---|---|---|
| M6-FU-TRACE-AUTOMATION-TRUTH-UP | ✅ completed | audit PR1（#247）：17 条 bdd link 13 翻 `automated` / 4 留 honest `unautomated`；~54 个 TBD-M3/M4 测试占位消灭（真绑定 / 新测试 / re-scope 指针）；G22 基线 15P→**4P/0W/0F**；新增 test_llm / test_dsn_options / test_execute_sql_envelope 共 17 测试 | none |
| M6-FU-GATES-TRUTH-UP | ✅ completed | audit PR2（#248）：G3 real impl（5P/0W/0F）+ G7 新建（2P/1W/0F；含语义修正——禁的是解密产物非 .enc 密文）+ G25 子旗；ci.yml 3 warning step 接线 + 陈旧 step 名刷新；gates.md v0.2 阻塞模式真值化（G4/G20→manual-canonical；G5→covered-by(G2)） | G3/G7/G25 blocking flip 各自走 ci-blocking-gate-toggle HITL（无日程承诺） |
| M6-FU-G26-RED-GREEN-WITHDRAWN | ✅ **WITHDRAWN**（2026-06-10） | R-G19 缓解已将 red-green evidence 软化为 AI-代码场景软要求；PR 模板 "Verification Plan" 段承载等效证据；gates.md v0.2 G26 行已标 withdrawn（per M4-FU-V4-MODE-B-IMPL WITHDRAWN 先例） | 复活条件：EVAL Phase-2 evidence harness 落地后重评 |
| M6-FU-G27-G28-TDD-REFACTOR-CONTRACT-DEFER | ⏳ deferred → **Phase-2** | `check_tdd_refactor_contract.py`（G27/G28 + docker-tdd-contract-test 同执行体家族）从未建；原 gates.md §5 "G28 M3 blocking 严格执行" 经 audit 核验从未接线；v0.2 已真值化为 deferred | Phase-2（与 EVAL harness 同窗评估实装价值） |
| M6-FU-BRANCH-TYPE-5LOCK | ✅ completed | audit PR3（本 PR）：`policies/git-branching.md` §1/§2 Decision 块 DECLINED — 维持 5 branch type + 7 commit type；M0-M6 ~70 PR 无一需要新型；archive 走 documentation/*、release 由 policies/release.md 承载 | 复活条件写明于 Decision 块（≥3 PR 类型误标 → owner 重开 ADR） |
| M6-FU-POLICIES-TBD-SWEEP | ✅ completed | carrier issue **#482**（epic；7 个子 PR，2026-08-11..08-12）。登记的 **20 个 `> TBD` 块 + 3 处 footer 提及**逐块处置完毕 = **19 filled + 1 整块 DECLINED**（`security.md` §2 CVE exception —— 实测无任何输入源：Dependabot alerts / security updates / secret_scanning 全 disabled、仓内无 `.github/SECURITY.md`，附 3 条复活条件）；另 `ci-gates.md` §3 的 filled 正文内含 **1 处子项 DECLINE**（不为零实例场景造「capability 长期豁免 ADR 申请规则」）。落点：data-boundary #483 `e71ee22` · security #487 `48f5faf` v0.1→v0.2 · git-branching #489 `90219fa` v0.1→v0.2 · docker-runtime #490 `f29f501` v0.3→v0.4 · ci-gates #491 `e1843a3` v0.5→v0.6 · claude-code-skill #492 `6f18794` v0.1→v0.2 · ai-agent #493 `9d5ce71` v0.4→v0.5（`policies/` 累计 +974 / −101）。收尾复验 @ `9d5ce71`：10 份 policy 全扫，`^> TBD` = **0**（残留占位块为零，显式 DECLINED 决策块不计）；`state` 字段零变更（AC-4）；残留 4 处 "Phase M2" 均为历史陈述、无承诺未来填充语义（AC-3）。**共同取证结论**：规则实体大多早已在仓内（代码 / workflow / ruleset / 契约），只是从未成文；多块的原 TBD **前提本身已死或写反**，故一律先验前提再落正文，取证回到实现本体而非散文治理表 | 本条闭合。sweep 期间新取证的差距另行登记（A12 CI 调用不带 `--strict` 且 finding 全 WARN ⇒ 恒 exit 0 / A13 无任何机器载体 / A14 契约指名的 `check_a14_gate.py` 仓内不存在 等）；姊妹条 `M6-FU-CAPABILITIES-TBD-SWEEP` 不在本条范围内、仍 🟡 active |
| M6-FU-TESTS-DOCKER-PHASE2-RESCOPE | ⏳ deferred → **Phase-2** | tests/docker/ 17 条占位 audit PR1 已从 docker-compose trace.yml 删除并指回本条；compose-config 静态面今日已被 `check_docker_contracts.py --compose-config`（BLOCKING）部分覆盖；真 compose 行为 harness 需 CI docker 支持或本地 smoke 框架 | Phase-2 |
| M6-FU-TESTS-CONTRACT-DIR-RENAME-RESCOPE | ⏳ deferred → **Phase-2** | 蓝图 tests/ 7/11 缺口的可行动面：`tests/contract`→`contracts` 改名悬置 + mcp-gov 7 条 contract-test 占位（audit PR1 已删并指回本条）；db / data_quality / agents / prompts 子目录对应 Phase-2 功能面（非 M0-M6 欠账） | Phase-2 |
| M6-FU-CAPABILITIES-TBD-SWEEP | 🟡 active | **验证 workflow（11-agent adversarial pass）增补发现**：trace.yml 真值化后，capabilities/ 兄弟文档仍存 **111 处 TBD-M3/M4 跨 19 文件**（INDEX.md + 各 capability 的 spec.yml / requirements.md / design.md / tasks.md / runbook.md / contracts/*.contract.yml），部分已被 PR1 真值化反向证伪（如 tasks.md 仍把已建的 test_llm.py 等标 TBD；runbook §7 justification 正文引用已被改写的 trace.yml 行段——已由 PR1 状态注框定为 historical record）；另含 4 个链外 validator docstring 的 gates.md v0.1 行号引用（check_bdd_* 等；chain 内 check_tdd_test_list.py 已 audit PR2 follow-up 修正） | Phase-2 逐 capability 内容对账（与 M6-FU-POLICIES-TBD-SWEEP 同批；§7.4 closure checklist 防再逃逸） |
| M6-FU-D9-RESIDUAL-ACCEPT | ✅ accepted+annotated | 评估 §4.2 D-9 七子项中除 settings-deny（audit PR4 实装）与 prompts-record（M6-FU-PROMPTS-TOPLEVEL-NO-MIGRATE）外的 5 残项显式处置：(1) `docker/healthchecks/healthcheck.sh` 不建——compose 内联 healthcheck 为事实标准，接受偏差；(2) `db/` 占位 + grants.contract.yml——并入 Phase-2 memory-checkpointer capability 时一并裁决；(3) `diff_biz_schema.py` 改名入 sdd/——低优先，随下次 scripts 整理；(4) CLAUDE.md 长度软超（capabilities/ 114>100、docker/ 98>80）——OB1 级观察项，接受不动；(5) GLOSSARY ~349 / README ~251 超软上限——软上限，接受 | none（(2)(3) 各随其宿主工作自然消化；无独立日程） |
| M6-FU-PROMPTS-TOPLEVEL-NO-MIGRATE | ✅ completed（评估记录；不迁） | audit PR4：蓝图 §12 顶层 `prompts/` 目录准则在 mj-agent 不适用成立——`src/mj_agent/prompts/system.md` 是 prompt freeze surface（V3 contract）+ `prompt-version-or-body-change` 必停面 + `load_prompt()` 加载路径；迁顶层零收益、反增 freeze/loader/必停三处接线变更面。不开 ADR（评估记录级；per 蓝图准则"已有强约束面不为对齐而迁"） | none（Phase-2 多 prompt 文件出现时重评） |
| M6-FU-STACK-SKILLS-PHASE2 | ⏳ deferred → **Phase-2** | 蓝图 stack-* 工程 skill ×4 未建（34 active skill 中无 stack-* family；evidence-* 已有 Phase-2 登记而 stack-* 此前登记外）：`stack-compose-config` 语义已被 `check_docker_contracts.py --compose-config`（BLOCKING）部分覆盖（skill 化收益存疑）；`stack-prompt-regression` / `stack-agent-eval` 依赖 EVAL framework（Phase-2 主交付）；其余按 EVAL 同窗评估 | Phase-2（与 EVAL framework + evidence-* skills 同批） |

## §3 Risk Control

详 ADR-031 §7 + 实施蓝图 `spec-anchored-calm-lampson.md` §10（23 项风险全集）.

本 plan 跟踪的关键风险：

| 风险 | 触发 Phase | 缓解 |
|---|---|---|
| R-G1 目录大规模迁移引用失效 | M5（ADR+docker）/ M6（STANDARD+跨切面） | 启动前全仓 grep + redirect map + G14/G15 blocking（catch-gates #213 已建 WARNING；逐 move-PR flip blocking）|
| R-G4 CLAUDE.md 瘦身丢失关键约束 | M6 | M6 末跑 ≥ 5 个典型 AI 任务 case study 验证；4 项必停 / Codex Status / archive 规则强制保留 |
| R-G5 Archive 被 AI 误读为当前事实 | M6（STANDARD archive re-sequenced + PR4a 先 author successors）| archive.yml ai_visibility 必填；G17 blocking；TOMBSTONE 顶部红 NOTE；PR4a 先把 governance 内容落 kernel 再归档 |
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
