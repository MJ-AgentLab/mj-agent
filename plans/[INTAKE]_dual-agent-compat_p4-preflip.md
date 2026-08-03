---
type: intake
summary: >-
  P4 前置切片（program plan §11 P4「强制执行与清理」的 pre-flip 准备腿）的 Stage 0/3 落盘——
  maintain/Medium/预计 1 PR；产出 evidence/ai-context-audit/2026-07_ci_audit.md（§11.2(4) CI 计数账本）
  + 登记负向测试实现 follow-up（#391）；**不翻转任何 gate**（P4 双轴翻转是独立 07-28 动作）。Stage-3
  对抗性发现：(b) 死元数据/无引用 adapter 清理 = 0 可删（9 adapter 全 live 4-33 引用 + validator wired；
  stale-stat removable_count=0，13 候选全 legit cross-repo/write-once/regression-guard）——诚实负结果；
  (a) §12 负向测试 5 类中 2 committed-passing / 2 prose-only / 1 missing（adapter-deletion）→ 归 #391。
  修正自查子代理 over-read：plan §555 [x] 是**计划完整性**自查（非实现声明），正确无需改。对应执行 issue #390；
  #312 P4 tracker 行的子切片（晋级证据回填 #312），非 tracker 行本身。
owner: ranzuozhou
created: 2026-07-24
updated: 2026-08-03
state: completed
track: shared
---

# [INTAKE] dual-agent-compat P4 前置切片（issue #390）

> Stage 0/3 输出于 2026-07-24 会话内产生并当日落盘（worktree `maintain/390-p4-preflip` 内，保 develop 干净）。
> 触发 §2.1 落盘判定（family convention：dual-agent-compat 恒落 [INTAKE] 成对；HITL 点：(a) disposition
> 拍板 + commit/push/PR + follow-up issue 登记）。**本切片是 pre-flip 准备腿，绝不翻任何 gate 姿态**——把 P4
> 「清理 + 证据 + 观察窗计数」前移，使 07-28（最早翻转资格）压缩成「拍板 + 翻转 + 复验」。
> 前序：dual-agent-compat #312 P0-P3 + S0-S2 全闭环，develop @ `2dde848`。

## 1 Task Classification

- **Type**: `maintain`（CI 计数证据 evidence + follow-up 登记；无 src/ 运行时、无 gate 翻转）
- **Base**: develop → PR `--base develop`
- **影响范围**：
  - `evidence/ai-context-audit/2026-07_ci_audit.md` — **新增**月度 CI 计数账本（§11.2(4)）；validator「other」桶
    （文件名非 `YYYY-QN` 非 `YYYY-MM-DD_*` → skip 不校验；`evidence/` 亦在 `check_frontmatter` SCAN_ROOTS 外）
  - `plans/[INTAKE]_dual-agent-compat_p4-preflip.md` — 本 Stage 0/3 落盘（working doc）
  - **不触**：任何 gate posture / 4 必停 / D-017 面（agents_sync.py / manifest mcp·codex.posture / .agents/ / .codex/）
- **Risk**: Medium（原含删除动作面；Stage-3 证实 0 可删 → 实际 Low-Medium；无 gate 翻转、无必停）

## 2 Scope（Owner 拍板 "Tight" disposition，2026-07-24）

- **In-scope**：(c) 2026-07_ci_audit.md 计数账本 · (b) 死元数据清理**负结果**登记（本文件 §4）· (a) 负向测试
  覆盖现状登记 + 实现 follow-up #391。
- **Out-of-scope**：P4 blocking 翻转本体（双轴，独立 07-28 逐 gate `ci-blocking-gate-toggle` 拍板）· 任何 gate
  posture 改动 · 4 必停面 · D-017 面 · §12 负向测试的**实现**（归 #391）· Spike 2b/AC-10 live-Codex（需 Owner 环境）。

## 3 CI 计数证据（(c) 交付；详见账本）

`evidence/ai-context-audit/2026-07_ci_audit.md`。要点（本快照 2026-07-24）：

- 窗口锚 2026-07-14（三 gate 同日首挂）→ 最早翻转资格 **2026-07-28**（14 日；本快照 +10 日）。
- 50 个 distinct head-SHA（全 `push`，merge-to-develop 不触发 ci.yml），**全 job-success**。
- 双证据法（annotations 全窗扫 + 本地 HEAD 复现 + 最新 run step-log 直抓）：**V8/V9/V10 全窗 0 violation**
  （50 run 0 annotations = 无任一 gate 非零退出；HEAD 复现 0E/0W + in-sync；最新 run 三 gate step-clean）。
- 保守连续-clean 下界：V8/V9 ≥50、V10 = 44（其 36d185d 起窗）——**均 ≥20**。**权威计数按 §11.2(3) 留 07-28
  实测**（勿外推）；本账本确立工件 + 方法 + 强资格指示。
- **修正 brief 沿用的「V10 14/20 as of 07-16」**：实测全窗 V10 无 drift（44/44）。

## 4 死元数据清理（(b) 交付 = 诚实负结果，0 可删）

Stage-3 对抗性 workflow（3 独立 read-only 审计员，find→adversarial-verify）判定 **(b) 无任何可安全删除项**：

- **无引用 adapter**：`sdd/adapters/*.md` 9 个**全 live**——引用 4-33 次（docs/INDEX、policies、constitution、
  GLOSSARY、CONTRIBUTING、CLAUDE/AGENTS 指针、6 份 PR 模板、manifest 19× `adapter_ref`、SKILL body、capability
  contract）+ **每个 A7-A12 validator 均 wired 进 ci.yml**（python L152 / langchain-agent L156 / prompt L159 /
  claude-code-skill L162 / docker-container L165 / runtime-skill L178 / bdd-tdd L226·252·270 / contract L290 /
  development-agent L330·334）。**orphan = 0，不删任何 adapter。**
- **失效统计**：`removable_count = 0`。旧「35/34P」计数 P0 已零残留（`_p1s0.md:31` 实证）；13 个 `34`/`35` grep
  命中全 legit——`35` = mj-system 跨仓归因（ADR-014/016），`34`/`34P` = write-once 历史（Q2 audit、SCHEMA §4
  「历史条款」、M2 premise-调查 ADR-032/contract.yml/claude-code-skill.md「实测观察」段、dated assessments），
  或 **regression-guard forbidden-literal**（`test_dual_agent_compat.py:126` 反而**禁止** `34P/0W/0F` 复现）。
  1 个「uncertain」：`ADR-016:74`「现 on-disk 35」——present-tense 但 write-once 2026-06-22 ADR 补记且 defer
  权威给 live script；**默认留**（ADR 补记 write-once），Owner 若视 ADR 补记可变则单独裁。
- **结论**：符合 §Verification 判断注——「若扫描无真可删项，(a)+(c) 独立即合法推进 P4 资格」。本切片不做任何删除。

## 5 负向测试覆盖现状（(a) 交付 = 现状登记 + follow-up；无实现）

plan §12 **已定义**的 5 类负向测试当前实现状况（#390 对抗性审计 + 自核）：hook fail-closed ✅committed /
commit-no-write ✅committed / **adapter-deletion ❌missing** / **biz-DB ⚠prose-only** / **env/secrets ⚠prose-only**
（详见 #391 表）。§12 是**验收标准定义**（正确），实现属 P4「补齐负向测试证据」——本切片按 Tight disposition
**归 follow-up #391**，不在本 PR 实现（adapter-deletion 是微妙的架构不变量测试，值得独立设计 + 5-lens 对抗评审）。

> **修正自查子代理 over-read（verify-before-act）**：#390 审计子代理称 plan §555 `[x]` 是「false/unbacked
> checkbox」。**自核推翻**：§19 是**计划文档完整性**自查（§554「已定义」/§555「完整」= 计划*定义/覆盖*这些主题，
> 非实现声明），§12 确已定义 adapter-deletion 测试 → **§555 [x] 正确，无需改**。故 Tight disposition 中「改
> false [x]」子动作前提假 → 作废（scope 收窄一处编辑，核心意图不变）。

## 6 Verification Plan

- Level A（本切片实跑，worktree cwd 复用 develop/.venv，离线）：
  - `check_ai_context_audit.py`（账本落 other 桶 skip + exit 0）✅ 已验
  - `check_frontmatter.py`（本 [INTAKE] doc 过 schema；evidence 账本不入 scan）✅ 已验
  - `check_wikilinks.py`✅ 已验 · `ruff check` · `mypy src/mj_agent` · `pytest tests/unit tests/eval`
- Checks not run（+why）：integration/smoke（需 .env/creds；本切片无 src 改动）；full step-log 50-run scrape
  （GitHub logs 端点 rate-limit；按 §11.2(3) 权威计数留 07-28 实测）。

## 7 HITL / 交付

- Gate-5 (a) disposition：Owner 选 **Tight**（ledger + honesty + follow-up）2026-07-24。
- 交付：`2026-07_ci_audit.md` + 本 [INTAKE] + follow-up **#391**；commit/push/PR 各单独 Owner 拍板。
- 晋级证据回填 **#312** P4 行（pre-flip 腿：计数工件 + 观察窗证据就位）。

## Related

- 执行 issue：**#390** · follow-up：**#391** · tracker：**#312**（P4 行）
- `plans/[PLAN]_dual-agent-compat.md` §11.1 / §11.2 / §12 · `policies/ci-gates.md` §4.1
- `evidence/ai-context-audit/2026-07_ci_audit.md`（本切片账本）
