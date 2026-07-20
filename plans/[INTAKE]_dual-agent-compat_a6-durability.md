---
type: intake
summary: A6 durability gate 切片（#347 §三.2 / SCHEMA.md §2.1 披露的 durability 缺口）的 Stage 0 Intake 落盘——maintain/Low-Medium/预计 1 PR；给 evidence/ai-context-audit/ 加专属 frontmatter-schema validator（scripts/check_ai_context_audit.py）+ CI step，因审计条目用 SCHEMA §2 自有 schema（type=ai-context-audit + cycle/auditor/scope/findings_summary/content_hash_snapshot、非 canonical base）→ 无法靠 SCAN_ROOTS 扩展；「面集==§2.1 推导」time-varying（Q2=15→Q3=23）→ 不做 blocking 门；scope（Option 1 schema-only / 2 +derive-helper / 3 blocking〔拒〕）+ CI posture Gate 5 拍板；对应 issue #359（非 #312 tracker 行，#347 follow-up）
owner: ranzuozhou
created: 2026-07-17
updated: 2026-07-20
state: active
track: shared
---

# [INTAKE] A6 durability gate — evidence/ai-context-audit 专属 validator 切片（issue #359）

> Stage 0 输出于 2026-07-17 会话内产生并当日落盘（worktree 内，保 develop 干净）；触发 §2.1 落盘判定
> （HITL 点 ≥3〔scope 拍板 + CI posture 拍板 + commit/push/PR〕 + 治理面〔CI-CD gate 新增〕变更）。
> 上游输入：#347（a6q3-cigates）§三.2 披露 + `evidence/ai-context-audit/SCHEMA.md` §2.1 durability 边界
> **自陈**「若将来硬化，应加一支 evidence/ai-context-audit/ 专属 §2 validator」。
> **非 #312 tracker 行**——是 #347 §三.2 的独立 follow-up（brief §四.A 候选 A）。
> 前序：#356 ssh-manager 收窄全闭环，develop @ `6e8adfa`。

## 1 Task Classification

- Type: **maintain**（新 validator 脚本 + CI step；非代码行为、非纯文档）
- Base branch: develop @ `6e8adfa`；G1 worktree `maintain/359-a6-durability-gate`（已建 @ `6e8adfa`）
- 影响范围：`scripts/check_ai_context_audit.py`（新）· `.github/workflows/ci.yml`（新 gate step）·
  `evidence/ai-context-audit/SCHEMA.md`（§2.1 durability 注更新）· `tests/`（validator 单测）·
  `CHANGELOG.md` · `plans/` 2 件。**不触** `src/mj_agent/**`、`.claude/**`、`.mcp.json`、任何 4 必停面、
  任何 write-once cycle 条目（`2026-Q2.md`/`2026-Q3.md`/investigation×2）。

## 2 影响范围（mj-agent 7 模块 + 跨边界）

- 7 模块：**均不触**（不动 agent/llm/prompt/skill/sql/db/config 任一 `src/` 面）。
- CI-CD：新增一支 gate step（§3.1 #6）——posture（blocking / warning-first）Gate 5 拍板。
- 数据边界 ADR-006/009/000：**不涉**（validator 只读 markdown frontmatter；不连 DB、不碰 biz/ssh）。

## 3 核查产出（Stage 0 事实核验，file:line 溯源）

| # | 事实 | 溯源 |
|---|---|---|
| F1 | `evidence/` 在 `check_frontmatter.py` `SCAN_ROOTS` 外（`docs/plans/decisions/src/mj_agent/{skills,prompts}`） | `scripts/check_frontmatter.py:38-44` |
| F2 | 审计条目用 **SCHEMA §2 自有 schema**（`type=ai-context-audit` + `cycle`/`auditor`/`scope`/`findings_summary`/`content_hash_snapshot`），**无** canonical base 7 字段 | `evidence/ai-context-audit/2026-Q2.md` + `2026-Q3.md` frontmatter |
| F3 | **naive SCAN_ROOTS 扩展会全挂**——`check_frontmatter.py` REQUIRED_FIELDS 全局要求 base 7 字段，审计条目全缺 → 须**专属 validator**（= SCHEMA §2.1 自陈的方案） | `check_frontmatter.py:52-54` |
| F4 | 目录含 **2 类**：`ai-context-audit` ×2（Q2/Q3）+ `ai-context-investigation` ×2（05-22 a2/a3）；SCHEMA §2 **只定义** ai-context-audit（investigation 是非正式扩展，a2 finding #2-9 记「需 SCHEMA amendment」但未落地） | 4 文件 frontmatter + SCHEMA §2 |
| F5 | `SCHEMA.md` **无 frontmatter**（`#` 标题起）→ validator 须跳过（非 cycle 条目）；`.gitkeep` 空 → 跳过 | `SCHEMA.md:1` |
| F6 | hash 是 **16 位截断** sha256（如 `998d8d13c4b5ad9a`），非 64 位——validator 校 hex 形态须容 16/64（勿硬要 64） | Q2/Q3 `content_hash_snapshot` 值 |
| F7 | **无既有 validator**（无 dup）；`ci.yml` 有多个 named gate step 先例（G1/G2/V1-V7…，blocking + continue-on-error 混用） | `grep` scripts + `ci.yml:94-187` |
| F8 | **§2.1 面集是 time-varying**：实测当前推导 = **23**（5 CLAUDE.md + 9 runtime SKILL.md + system.md + 8 frozen infra）**恰等 Q3**，但 Q2=15 —— 面集随仓变（skills 3→9/infra 6→8/路径 rename） | 见 §4 推导实测 |

## 4 §2.1 派生规则实测（当前面集 = 23，恰等 Q3）

**CLAUDE.md 轨**（`git ls-files **/CLAUDE.md`，5）：`CLAUDE.md` · `capabilities/CLAUDE.md` ·
`docker/CLAUDE.md` · `src/mj_agent/CLAUDE.md` · `tests/CLAUDE.md`。
**必停 markdown 轨**（18）= `.claude/settings.json` `ask` glob 命中的 `.md`〔`src/mj_agent/skills/**/SKILL.md`
展开 = 9 runtime + `src/mj_agent/prompts/system.md` = 10〕∪ `claude-skill.contract.yml` 冻结 infra〔8：
app-start/app-stop/docker-compose/env-setup/env-teardown/llm-endpoint-probe/storage-stack/studio-probe〕。
→ 并集 **23**，与 `2026-Q3.md` `content_hash_snapshot` keys 逐一相等。

> **time-variance 含义**：今日 == Q3 纯因 #356 未动这些面；一旦加/删 runtime skill 或 CLAUDE.md，派生
> 立即 ≠ 最新 cycle → **blocking 派生匹配门会 false-fail 且强制每次 skill 改动都重跑季度审计**，直接
> 违背 SCHEMA §1「A6 **故意** manual+M-FU 而非 CI cron」的设计。故 blocking 派生门（Option 3）不可取。

## 5 Risk Assessment

- Level: **Low–Medium**
- Triggered §3.1 必停项：**#6（CI-CD）**——新增 CI gate step → posture（blocking/warning）HITL 拍板。
  **非** 4 专属必停（不触 guardrail/precheck/system.md body/SKILL.md body/qcm_catalog）。
- A13 **不适用**（不动 `.claude/settings.json` allowlist）；A14 / D-017 **不适用**。**`ci-blocking-gate-toggle`
  适用（2026-07-20 更正）**：新 blocking gate 受 `policies/ci-gates.md` §4:41「blocking 前 1 周 dry-run」约束，
  D-016 day-1-blocking 豁免**仅限信任面/MCP 投影**（`ci-gates.md` §4.1 `:58-61`「无明文观察期的 gate 不享此豁免」）
  → 本 gate 非信任面，原标「N/A」= 5-lens 逮到的**错误前提**。Owner 2026-07-20 **显式 waive** §4:41 dry-run
  （依据：Q2/Q3 已合规 + 结构-only 校验 + 语料小受控 + 零 drift 风险），`ci-blocking-gate-toggle` 执行记录随 PR/#359
  留档（类比 V11 #330）。承「错误前提作废」纪律：posture（blocking）不变、governance 处置更正后带回 Owner 重确认。
- 数据边界：不涉（validator 只读 markdown）。
- Gated actions：commit/push/PR 逐次拍板；merge 交 Owner。

## 6 Documentation Decision（粗评；Stage 4 已细化）

Plan=Create（`plans/[PLAN]_dual-agent-compat_a6-durability.md`）；**CHANGELOG=Update**（`[Unreleased]`）；
**SCHEMA.md §2.1 durability 注=Update**（改「无 gate → 若将来硬化…」为「gate 已存在」；SCHEMA 非 write-once
cycle 条目，可编辑——Q3 即改过 §2.1）；ADR=**None**（SCHEMA §2.1 已预告该 validator，无新架构决策）；
INDEX=None；SPEC/RUNBOOK/GUIDE/STANDARD/ISSUE/ASSESSMENT=None。

**不动 write-once**：`2026-Q2.md`/`2026-Q3.md`/investigation×2 是冻结快照 → validator 只**读校**，不改。

## 7 Owner 拍板记录

| # | 决策 | 结果 |
|---|---|---|
| 1 | **锚 + 专属 validator 方案** | **建专属 issue + worktree → 写 plan**；确认专属 validator（非 SCAN_ROOTS 扩展，因 F3）+ 面集派生 time-varying 不做 blocking 门。AskUserQuestion 确认 2026-07-17。 |
| 2 | **scope（Option 1/2/3）+ CI posture** | **拍板 = Option 2（schema + `--derive` helper）+ investigation-(a)（只校 ai-context-audit）+ blocking day-1**（Gate 5，AskUserQuestion 确认 2026-07-17）。Option 3（blocking 派生匹配）拒（time-varying 违 A6 quarterly-not-cron 设计）。PLAN §5-8 已按此实施。 |

### 7.1 拍板前提溯源

AskUserQuestion 选项内断言均提问前 file:line 核验（SCAN_ROOTS `:38-44` / 审计 schema F2 / naive 扩展会挂 F3 /
time-variance F8 实测）。承「错误前提作废」纪律（#341 §7.1）。

## 8 Verification Plan

- Level A（read-only）：`check_frontmatter.py` · `check_wikilinks.py` · V8/V9/V10/V11 · `pytest tests/unit tests/eval`
  · `ruff check` · `mypy src/mj_agent` · **新** `check_ai_context_audit.py`（正向：Q2/Q3 pass）
- Level A（自证）：AC grep + 负向 fixture 单测（缺字段/坏 cycle/空 snapshot/坏 hex 被拦）
- Level B：无（不跑 side-effect；CI step 由 PR CI 实证）

## 9 交办事项（本切片范围外，登记）

1. **investigation-type schema 正式化**（a2 finding #2-9）：SCHEMA §2 只定义 ai-context-audit；investigation
   是非正式扩展。若 Gate 5 选「只校 audit」，则 investigation 正式化另立 follow-up。
2. 承前序未决项（非本切片）：INDEX ADR 表 drift（031/032/035/036）· `policies/security.md:72` ADR-034 stale gloss ·
   A6 提醒 M-FU-AI-AUDIT-2026-Q4 注册状态（本 gate 不替代提醒，只校结构）· gitee/develop 落后 origin。

## 10 Next Step

Stage 4 计划落盘（本 worktree，同 PR）→ **Gate 5 拍板 scope（1/2/3）+ CI posture** → Stage 8 实施（TDD 红绿：
validator + 单测 + CI step + SCHEMA §2.1 注 + CHANGELOG）→ Stage 10/11 验证/自评（含 5-lens）→ Gate 13 PR →
交 Owner 合并 → Stage 17 post-merge（state flip PR + 分支双清 + worktree remove + 关闭 #359）。
