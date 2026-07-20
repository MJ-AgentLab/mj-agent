---
type: plan
summary: investigation-type schema 正式化执行计划（a2 #2-9 / A6 follow-up Intake §9-1）——在 evidence/ai-context-audit/SCHEMA.md §2 正式定义 ai-context-investigation frontmatter schema（required: type/investigation/auditor/scope/findings_summary；optional: subtype/phase/date/related_episodes/parent_artifacts/schema_extension_request；不需 content_hash_snapshot——与 audit 的关键结构差异）+ 扩 scripts/check_ai_context_audit.py（新 validate_investigation_entry + find_cycle_entries→find_entries 三分〔cycle/investigation/other〕、按 filename YYYY-MM-DD_*.md 选中 investigation、docstring 更新）+ 单测（加 investigation 用例、改 2 个编码旧 skip 行为的测试）+ CHANGELOG；两既存 investigation 文件 green day-one；D2 = same blocking gate coverage-expansion（无 continue-on-error flip、无 ci.yml edit；§三.1 治理裁定记录）；1 PR（#362 maintain/362-investigation-schema，PR #363 merged b95013e，2026-07-20）
owner: ranzuozhou
created: 2026-07-20
updated: 2026-07-20
completed: 2026-07-20
state: completed
track: shared
---

# [PLAN] investigation-type schema 正式化切片（issue #362）

## 1 Linked Artifacts

- Issue：#362（本切片）；**非 #312 tracker 行**——#359 / #347 §三.2 follow-up（A6 plan Intake §9-1）
- Intake：[[[INTAKE]_dual-agent-compat_investigation-schema|本切片 Intake]]（Gate 5 D1/D2 拍板 §3 + 治理裁定记录）
- 缺口源：`evidence/ai-context-audit/2026-05-22_a2-investigation.md` finding **#2-9** + `schema_extension_request: true` flag ·
  `[PLAN]_dual-agent-compat_a6-durability.md` §5.2 Option (a)〔只校 audit，拒 (c) "撑大切片"〕→ 登记 follow-up（Intake §9-1）
- 参照：`scripts/check_ai_context_audit.py`（本切片扩展对象）· `scripts/check_frontmatter.py`（analogous canonical-doc validator）

## 2 Scope

- **In-scope**：
  1. SCHEMA §2 正式定义 `ai-context-investigation` schema（新子节）。
  2. `check_ai_context_audit.py` 扩展：按 filename 选中 investigation 条目 + 校验 investigation schema；两既存文件 green day-one。
  3. 单测：加 investigation 正/负用例（含 `run()`/`check()` 退出码集成测）；改 2 个编码旧 skip 行为的既有测试。
  4. CHANGELOG。
- **Out-of-scope**：重构 `ai-context-audit` schema；validator 既有 3 项 deliberate non-goals（hash 重算 / path-existence / face-set blocking match）保持 non-goals；Phase-2 checkpoint 脱敏（ADR-037）；INDEX ADR-表 drift；`policies/security.md:72` stale gloss。

> **纵切片归属**：self-verifiable、可独立 review-合的窄完整路径——#359 / #347 §三.2 的登记 follow-up。

## 3 设计（Stage 3 Repo Scan 事实核实后）

### 3.1 Investigation schema（SCHEMA §2 新子节）

事实：两既存条目 `2026-05-22_a2-investigation.md` / `2026-05-22_a3-readiness-eval.md` 共有字段核实（读文件 frontmatter）：

| 字段 | 必需? | 校验规则 | 来源 |
|---|---|---|---|
| `type` | **required** | == `ai-context-investigation` | a2/a3 both |
| `investigation` | **required** | 非空 str（slug；类比 audit 的 `cycle`） | a2/a3 both |
| `auditor` | **required** | 非空 str | a2/a3 both |
| `scope` | **required** | 非空 list of 非空 str | a2/a3 both |
| `findings_summary` | **required** | 非空 str | a2/a3 both |
| `subtype` | optional | 若在 → 非空 str | a3 |
| `phase` | optional | 若在 → 非空 str | a2/a3 |
| `date` | optional | 不强校（YAML 解析为 date 对象；filename 已编码日期） | a2/a3 |
| `related_episodes` | optional | 若在 → 非空 list of 非空 str | a2/a3 |
| `parent_artifacts` | optional | 若在 → 非空 list of 非空 str | a3 |
| `schema_extension_request` | optional | 若在 → bool | a2 |

**关键结构差异 vs audit**：investigation **不需** `content_hash_snapshot`（它不是 hash 快照）；用 `investigation` slug 取代 `cycle`。

**§2 文档编排**：将 §2 标题从「Audit Entry Frontmatter Schema」泛化为「Entry Frontmatter Schemas」+ 加一句 intro（本目录含两类条目：ai-context-audit 季度 cycle + ai-context-investigation 临时调查），既有 audit block + §2.1 保留，新增 **§2.2 Investigation Entry Frontmatter Schema**。**不renumber §3/§4**（validator docstring 引 §1/§3 by number）。

### 3.2 Validator 扩展（`scripts/check_ai_context_audit.py`）

- 加常量：`INVESTIGATION_TYPE = "ai-context-investigation"`；`INVESTIGATION_FILE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}_.+\.md$")`（date-prefixed，distinct from `YYYY-QN.md` + `SCHEMA.md`/`.gitkeep`）；`REQUIRED_INVESTIGATION_FIELDS`。
- 加 `validate_investigation_entry(meta) -> list[str]`，与 `validate_audit_entry` 平行。**可**抽取共享小 helper（`_check_nonempty_str` / `_check_nonempty_str_list`）供两者复用——但**保持既有 violation message 子串逐字不变**（既有 audit 测试 pin 了 "auditor"/"scope must be"/"findings_summary"/"non-empty mapping"/"hex"/"cycle=" 等子串）。
- `find_cycle_entries` → **`find_entries(repo_root) -> (cycle, investigation, other)`** 三分（filename-based：`YYYY-QN.md`→cycle，`YYYY-MM-DD_*.md`→investigation，其余→other）。更新全部 call site（`check`/`run`/测试）。
- `check()`：校 cycle（audit schema）+ investigation（investigation schema），合并返回 `{rel: violations}`。
- `run()`：`other` → `skip (not a cycle or investigation entry)`；成功信息含两类计数；FAIL 信息清晰指向 SCHEMA §2。
- **docstring 更新**：去「validate ai-context-audit only」/「investigation-skip decision」；描述两类校验（cycle by `YYYY-QN.md`，investigation by `YYYY-MM-DD_*.md`，filename-based 选中——mistyped `type`/BOM 仍被 FAIL 非跳过）；注明 Gate-5 investigation-(a) 决策由 #362 supersede。

### 3.3 CI（承 D2）

- `ci.yml:89` 已 blocking 跑 `check_ai_context_audit.py`——同一 step 校更多，**无 continue-on-error flip、无 ci.yml edit**（Stage 3 已核实）。
- 语料 = 2 investigation 文件，均设计为 green day-one → coverage-expansion 不引入新 CI 失败面。

## 4 治理裁定记录（承 §三.1 carry-forward — 最重）

把 already-blocking gate 的 coverage 扩到此前未受门的 investigation 文件 = 对那些文件是 **new blocking behavior**。**不自判** `ci-blocking-gate-toggle` / ci-gates §4:41「blocking 前 1 周 dry-run」为 "N/A"。

- **Owner Gate 5 D2 显式裁定（2026-07-20）**：treat as **coverage-expansion of an existing blocking gate**（非 §4:41-scoped 的 new gate；gate 早已 blocking，无 continue-on-error 翻转）。
- **理据**：语料 2 文件、均 green day-one、structural-only——类比 A6 gate 自身 green day-one 且 Owner 显式 waive §4:41（#360），及 V11 #330 day-1 blocking。
- **落点**：PR body + 本节记录该裁定，provenance 类比 V11 #330 / A6 #360。此为承 §三.1「新 blocking 行为勿自判 N/A」的合规路径（Owner 裁定，非 AI 单方）。

## 5 Acceptance Criteria

- [ ] AC-1：SCHEMA §2 定义 `ai-context-investigation` schema（required vs optional 字段文档化，match 两既存 exemplar）。验证：读 SCHEMA.md §2.2；grep `ai-context-investigation`。
- [ ] AC-2：`check_ai_context_audit.py` 按 filename 选中 investigation 并校验；**两既存 investigation 文件 PASS 不改**。验证：`uv run python scripts/check_ai_context_audit.py` exit 0 + 输出显示 investigation 条目被校（非 skip）。
- [ ] AC-3：既有 Q2/Q3 `ai-context-audit` 仍 PASS（无回归）。验证：同上 exit 0；`test_committed_entries_pass` green。
- [ ] AC-4：malformed investigation fixture **FAIL** 且信息清晰——**`run()`/`check()` 退出码集成测**（非仅纯函数单测）。验证：`test_malformed_investigation_fails` 断言 `run(tmp)==1` + `check(tmp)` 含该文件。
- [ ] AC-5：`uv run python scripts/check_ai_context_audit.py` exit 0；`--derive` 不受影响（face-set 逻辑不动）。
- [ ] AC-6：`uv run pytest tests/unit/test_check_ai_context_audit.py` green；`uv run ruff check` + `uv run mypy src/mj_agent` clean。
- [ ] AC-7：既有 2 个编码旧 skip 行为的测试（`test_non_cycle_files_not_validated` / `test_splits_cycle_vs_other`）已按新行为更新，非删除掩盖。

## 6 Verification Plan

- Level A（自证）：AC grep（SCHEMA §2.2 存在 / `ai-context-investigation` 定义）+ 负向 fixture 单测（缺字段/wrong type/空 scope 被拦）+ 正向（a2/a3 pass）。
- `uv run pytest tests/unit/test_check_ai_context_audit.py -q`
- `uv run python scripts/check_ai_context_audit.py`（+ `--derive`）
- `uv run ruff check && uv run mypy src/mj_agent`
- 大闭幕全 bands（clean worktree）：`uv run pytest tests/unit tests/eval`（per structure-move discipline）+ 全 diff credential 扫描 + 5-lens 对抗审查（workflow）。
- Level B：无 side-effect（CI step 由 PR CI 实证）。

## 7 HITL Gates（execution-loop 5/7/9/11/13）

- Gate 5（Intake/scope）：**已过**——D1/D2 拍板（Intake §3）。
- Gate 7（Plan）：本 plan 落盘。
- Gate 9（scope drift）：实施中若发现需改 ci.yml / 触 audit schema / 触 4 必停 → 停回 Owner。
- Gate 11（self-review）：5-lens 对抗审查。
- Gate 13（PR）：PR 创建单独授权；合入 develop 的 merge 交 Owner（classifier 硬拦 agent 直合）。

## 8 Next Step

Stage 8 TDD（红绿：先改测试编码新行为→跑红→改 SCHEMA + validator→跑绿→CHANGELOG）→ Stage 10/11 验证 + 5-lens → Gate 13 PR `--base develop` → 交 Owner 合并 → Stage 17 post-merge（state flip PR 翻 completed + 加 `completed:` 字段 + summary 同步 + 分支双清〔origin+gitee〕+ worktree remove + prune + 手动 `gh issue close 362`〔Closes #N 本仓恒不生效〕）。

## 9 交办事项（本切片范围外，登记）

1. 承前序未决项（非本切片）：INDEX ADR-表 drift（031/032/035/036/037）· `policies/security.md:72` ADR-034 stale gloss · Phase-2 checkpoint 脱敏（ADR-037 驱动）· gitee/develop 落后 origin（今 43）。
2. Spike 2b / AC-10（live Codex，Owner 协同；#353 唯一剩项）。
