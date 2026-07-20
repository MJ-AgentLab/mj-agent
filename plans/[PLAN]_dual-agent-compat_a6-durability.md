---
type: plan
summary: A6 durability gate 执行计划（#347 §三.2 / SCHEMA.md §2.1 durability 缺口）——新建 scripts/check_ai_context_audit.py 校验 evidence/ai-context-audit/ 的 ai-context-audit §2 frontmatter schema（type/cycle/auditor/scope/findings_summary/content_hash_snapshot；content_hash_snapshot 只校结构非重算 hash——重算=下期审计要检的 drift）+ CI step + SCHEMA §2.1 durability 注更新 + 单测；面集==§2.1 推导 time-varying（当前=23=Q3）→ blocking 派生门拒（违 A6 quarterly-not-cron 设计），至多 --derive helper（Option 2）；scope Gate 5 拍板 = Option 2 + investigation-(a) + blocking day-1（§4:41 dry-run Owner 显式 waive）；1 PR（#359 maintain/359-a6-durability-gate，PR #360 merged 0a2078b）
owner: ranzuozhou
created: 2026-07-17
updated: 2026-07-20
completed: 2026-07-20
state: completed
track: shared
---

# [PLAN] A6 durability gate — evidence/ai-context-audit 专属 validator 切片（issue #359）

## 1 Linked Artifacts

- Issue：#359（本切片）；**非 #312 tracker 行**——#347 §三.2 follow-up
- Intake：[[[INTAKE]_dual-agent-compat_a6-durability|本切片 Intake]]（专属-validator 拍板 §7 + §2.1 派生实测 §4）
- 缺口源：`evidence/ai-context-audit/SCHEMA.md` §2 / §2.1（durability 边界自陈「应加一支专属 §2 validator」）·
  [[[INTAKE]_dual-agent-compat_a6q3-cigates|#347 INTAKE]] §三.2〔`evidence/` 在 SCAN_ROOTS 外须手动核验〕
- 参照：`scripts/check_frontmatter.py`（analogous canonical-doc validator，结构/退出码/输出格式参照）
- 程序计划：[[[PLAN]_dual-agent-compat|v5 计划]]（本切片是其治理卫生的 #347 follow-up，非阶段）

## 2 Context

`evidence/ai-context-audit/` 存季度 A6 AI-context 审计快照（`<cycle>.md`，write-once），用 SCHEMA §2 定义的
**专属 frontmatter schema**（`type: ai-context-audit` + `cycle`/`auditor`/`scope`/`findings_summary`/
`content_hash_snapshot`）。**该目录在 `check_frontmatter.py` `SCAN_ROOTS`（`:38-44`）之外** → 无任何 CI gate
校验这些条目的 schema。SCHEMA §2.1 durability 边界**自陈**此缺口并预告修法（专属 validator）。

**为何不能 naive 扩 SCAN_ROOTS**：`check_frontmatter.py` REQUIRED_FIELDS（`:52-54`）全局要求 canonical
base 7 字段（`type/summary/owner/created/updated/state/track`），审计条目**全缺**（用 §2 schema）→ 扩
SCAN_ROOTS 会令 Q2/Q3/investigation 全挂。故须**专属 validator**。

**A6 设计约束（决定 scope）**：SCHEMA §1 明示 A6 **故意** manual+M-FU 提醒而非 CI cron（cron 静默失效）。
`content_hash_snapshot` 面集**按 §2.1 每 cycle 现场推导**（数量是观测值非规范值）——本切片 §4 实测当前 = **23**
（恰等 Q3），但 Q2=15，面集随仓变。**任何「派生匹配」若做 blocking 门**，会在仓一改 skill/CLAUDE.md 即
false-fail、强制每次都重跑季度审计 → 与 A6 quarterly-not-cron 设计冲突。**本 gate 校 schema 结构，不重算 hash、
不做 blocking 派生匹配**（重算 hash / 派生 diff = 正是**下期审计**要检的 drift）。

## 3 §2 schema 校验规则（ai-context-audit 条目）

validator 对每个 `type: ai-context-audit` 条目校（缺一即 violation）：

| 字段 | 规则 |
|---|---|
| `type` | == `ai-context-audit`（判别键；validator 据此选中） |
| `cycle` | 匹配 `^\d{4}-Q[1-4]$`（如 `2026-Q2`） |
| `auditor` | 非空 str |
| `scope` | 非空 list（元素为 str）——SCHEMA §2 列 5 个示例 surface 类型；**不硬做 enum**（列表内容随 cycle 可增删），可选：非标准项 warning |
| `findings_summary` | 非空 str |
| `content_hash_snapshot` | 非空 mapping（dict）：key = repo-相对路径 str；value = hex str **16 或 64 位**（`^[0-9a-f]{16}$` ∪ `^[0-9a-f]{64}$`——现有为 16 位截断，勿硬要 64） |

**明确非目标（写入 validator 注释 + 本节，防将来误加）**：
- **不重算** `content_hash_snapshot` 的 hash 值与当前文件比对——那是**下期审计**要检的 drift（write-once
  条目快照的是**历史**状态，与当前必然不同）。
- **不校** key 路径在**当前**仓存在——past 条目引用已 rename 的路径（Q2 有 `infra/docker/CLAUDE.md`，今为
  `docker/CLAUDE.md`）是**合法历史**。
- **不改**任何 write-once cycle 条目。

## 4 §2.1 派生规则（当前面集 = 23，实测）

**CLAUDE.md 轨**（`git ls-files` 命中 `**/CLAUDE.md` + 根 `CLAUDE.md`，5）：`CLAUDE.md` · `capabilities/` ·
`docker/` · `src/mj_agent/` · `tests/`。
**必停 markdown 轨**（18）= `.claude/settings.json` `permissions.ask` glob 命中的 `.md`〔`src/mj_agent/skills/**/SKILL.md`
展开 9 + `src/mj_agent/prompts/system.md` = **10**；`.py`/`.yaml` 三项排除〕∪ `claude-skill.contract.yml`
`skills[].file` 声明的 8 个 `.claude/skills/mj-agent-infra-*/SKILL.md`。
→ 并集 **23** = `2026-Q3.md` `content_hash_snapshot` keys（逐一相等，§Intake F8 实测）。

## 5 Scope 三选项 + investigation 处置（Gate 5 拍板）

> **共同前提**：均新建 `scripts/check_ai_context_audit.py` + CI step + 单测 + SCHEMA §2.1 注更新；均**只校
> schema 结构、不重算 hash、不做 blocking 派生匹配**（§2/§3 非目标）。

| 选项 | 内容 | 闭合缺口 | 代价 |
|---|---|---|---|
| **1 schema-only** | validator 只校 §3 schema | 闭「无 schema 校验」半 | 最小；但「派生规则无机器形态」半未闭（未来 auditor 仍可能人肉写死错面集——正是 #304→Q2-15-stale 的病因） |
| **2 schema + `--derive` helper（推荐）** | 1 + `--derive` 子模式：按 §2.1 机械算并打印当前面集（供下期 auditor 直接用，消除人肉写死风险）；单测对 tmp_path fixture 断言派生正确 | **两半全闭**（schema + 派生机器形态） | +派生函数（中等：ask-glob 展开 + contract 冻结面 + git ls-files）；`--derive` 是**手动辅助**不入 CI（无 drift 噪音） |
| **3 schema + blocking 派生匹配** | 1 + CI 里派生当前面集、最新 cycle 面集不等即 **error** | 名义上强制派生 | **拒**：time-varying → skill 一改即 false-fail + 强制每次重跑季度审计，违 SCHEMA §1 A6 quarterly-not-cron 设计（§2） |

### 5.1 推荐 = Option 2

**倾向 2**：#304→Q2-15-stale（人肉写死面集静默过期）正是 §2.1 改推导规则要治的病因；`--derive` 给派生**机器
形态 + 回归锚**（单测），闭合 disclosed gap 的**两半**，而 `--derive` 手动不入 CI → 无 time-variance 噪音。
Option 1 是「真最小」但只闭一半；Option 3 违 A6 设计（拒）。
> 可选 sub-variant 2b：加一支 **warning-only**（非 error）CI 检查，最新 cycle 面集 ≠ 当前派生时 warn——
> 但季度间会持续噪音（skill 一改即常亮），**不默认推荐**，Gate 5 可选。

### 5.2 investigation-type 处置（sub-decision）

目录含 `ai-context-investigation` ×2（SCHEMA §2 未定义，a2 finding #2-9 记「需 amendment」未落地）。选项：
- **(a) 只校 ai-context-audit（推荐）**：validator 只选中 `type==ai-context-audit`；其余 type（investigation）
  + 无 frontmatter（SCHEMA.md/.gitkeep）→ 跳过 + info 行列出。investigation 正式化另立 follow-up（Intake §9-1）。
- (b) investigation 加轻量 presence 校（type/auditor/scope/findings_summary）——但 schema 未正式定义，易漂。
- (c) 先在 SCHEMA §2 正式定义 investigation schema 再校——撑大切片。
→ **推荐 (a)**：validator 聚焦 SCHEMA §2 实际定义的 audit 类；investigation 正式化解耦。

### 5.3 CI posture（Gate 5 拍板）

- **blocking day-1（推荐）**：Q2/Q3 已合规（AC-2 先证）→ 直接 blocking 无过渡风险；durability gate 若 warning-only
  则不「durably 强制」（名不副实）。语料小且受控。
- warning-first：更保守，但本 gate 目的即强制，warning 弱化其意义。
> **注（2026-07-20 更正，5-lens scope-governance 镜逮到）**：**原判「新 gate 直接 blocking 非
> ci-blocking-gate-toggle」是错误前提**——`policies/ci-gates.md` §4:41 令**任何** gate 转 blocking 前须 1 周
> dry-run；D-016 day-1 豁免**仅限信任面/MCP 投影**（§4.1 `:58-61`「无明文观察期的 gate 不享此豁免」），本 gate
> 非信任面 → **`ci-blocking-gate-toggle` 适用**。Owner 2026-07-20 显式 waive §4:41 dry-run（依据同上），执行记录
> 随 PR/#359（类比 V11 #330）。

### 5.4 Gate 5 拍板 = Option 2 + (a) + blocking（2026-07-17）

Owner AskUserQuestion 三问拍板：**scope = Option 2**（schema + `--derive` helper——闭 disclosed gap 两半、
`--derive` 不入 CI 无 time-variance 噪音）· **investigation = (a)**（只校 `ai-context-audit`，investigation
正式化另立 follow-up）· **CI posture = blocking day-1**（Q2/Q3 已合规、durability gate 名副其实）。**Option 3
（blocking 派生匹配）拒**（time-varying 违 A6 quarterly-not-cron 设计，§5 table）。§6-8 已按此实施。

**posture 前提更正 + 重确认（2026-07-20，5-lens）**：Gate-5 posture 选项当时未含 `ci-gates.md` §4:41 语境、且
plan 误标 `ci-blocking-gate-toggle`「N/A」。5-lens scope-governance 镜逮到 → 带正确框定（§4:41 dry-run 适用、
D-016 豁免仅信任面）回 Owner 重确认：**Owner 选 blocking day-1 + 显式 waive §4:41 dry-run**（依据：Q2/Q3 已合规 +
结构-only + 语料小受控 + 零 drift）。**posture（blocking）不变、governance 处置更正**；`ci-blocking-gate-toggle`
执行记录随 PR/#359（类比 V11 #330）。承「错误前提作废」纪律（不单方改写、带正确前提回 Owner）。

## 6 Validator 设计（`scripts/check_ai_context_audit.py`）

- **参照** `check_frontmatter.py`：`python-frontmatter` 解析 · 退出码 0（pass）/1（violation）· stderr 逐条 ·
  `main() -> int` · `repo_root = Path(__file__).resolve().parent.parent`。
- 扫 `evidence/ai-context-audit/*.md`（flat dir，非 rglob）；跳无 frontmatter（SCHEMA.md/.gitkeep）。
- 每条按 §3 校 `ai-context-audit`；investigation/其余按 §5.2(a) 跳过 + info。
- **单测**（`tests/unit/test_check_ai_context_audit.py`，tmp_path 注入式 make fixture，仿 V8/V9 checker 风格）：
  正向（合规 audit 条目 pass）+ 负向（缺 cycle / 坏 `cycle` 格式 / 空 `scope` / 空/非-map `content_hash_snapshot` /
  坏 hex 各拦）+ 真实树钉线（Q2/Q3 pass）。
- **Option 2 增**：`--derive` 子命令（`argparse` `choices` 或 `--derive` flag）→ 按 §4 算并打印面集（sorted）；
  单测对 **tmp_path fixture** 断言派生逻辑（**非**对 live 仓断言精确 23——那会 time-vary）。

## 7 Work Breakdown（1 PR，`maintain/359-a6-durability-gate`）

> 按**推荐 Option 2 + investigation (a) + blocking**写；Gate 5 若变则 §8.1 delta。

| # | 动作 | 文件 | 备注 |
|---|---|---|---|
| W1 | 新 validator（TDD 红绿） | `scripts/check_ai_context_audit.py` | §6 设计；先写失败单测再实现 |
| W2 | 单测 | `tests/unit/test_check_ai_context_audit.py` | 正/负向 + 真实树钉线 + （O2）派生 fixture |
| W3 | CI step | `.github/workflows/ci.yml` | 新 named step（posture Gate 5）；紧邻 frontmatter/wikilinks step |
| W4 | SCHEMA §2.1 durability 注更新 | `evidence/ai-context-audit/SCHEMA.md` | 「无 gate…若将来硬化」→「gate 已存在（`check_ai_context_audit.py`）；仍不重算 hash / 不 blocking 派生（time-varying），派生由 `--derive` 机器化」 |
| W5 | CHANGELOG | `CHANGELOG.md` | `[Unreleased]` 条目 |
| W6 | 落盘 Intake + Plan | 本 2 文件 | `state: active`；merge 后独立小 flip PR |

## 8 验收标准（全部可执行自证；精确 pattern PR 前跑一遍）

- **AC-1** validator 校 `ai-context-audit` §3 六字段（缺任一 → violation）——负向单测覆盖
- **AC-2** `uv run python scripts/check_ai_context_audit.py` → exit 0，Q2/Q3 pass（**先复现既有合规**，否则实现 bug 误报）
- **AC-3** 负向 fixture（缺 `cycle` / `cycle=2026-Q9` 坏格式 / `scope: []` / `content_hash_snapshot: {}` / value=`xyz` 非 hex）各被拦，单测 exit 0（断言 violation 存在）
- **AC-4** CI step 接入 `ci.yml`（posture per Gate 5）；本地跑 validator exit 0
- **AC-5** `uv run pytest tests/unit tests/eval` 全绿（含新单测）+ `ruff check` + `mypy src/mj_agent` 干净
- **AC-6** 既有 gate 不受影响：`check_frontmatter.py`（125→仍 pass，evidence 不入其 SCAN_ROOTS）· `check_wikilinks.py` · V8/V9/V10/V11 各 exit 0
- **AC-7** `SCHEMA.md` §2.1 durability 注更新（grep 命中「`check_ai_context_audit.py`」）
- **AC-8**（Option 2）`--derive` 输出当前面集非空且含已知面（`CLAUDE.md` / `system.md` / 冻结 infra 8）；单测对 fixture 断言派生正确
- **AC-9** validator **不改**任何 write-once 条目（`git diff` 无 `2026-Q*.md` / investigation 改动）
- **AC-10** CI 全绿

### 8.1 Gate 5 若变 scope/posture 的 delta

- 选 **Option 1**：删 W1 的 `--derive` + AC-8；validator 仅 schema。
- 选 **Option 3**：加 blocking 派生匹配（**不推荐**，§5）——W1 增派生 diff + error；AC 增派生匹配断言。
- **investigation (b)/(c)**：W1 增 investigation 校 / 或先改 SCHEMA §2（撑大）。
- **warning-first posture**：W3 加 `continue-on-error: true`。

## 9 Verification

- **Level A（read-only）**：`ruff check` · `mypy src/mj_agent` · `pytest tests/unit tests/eval`（clean worktree 无 #298 假红）
  · `check_frontmatter.py` · `check_wikilinks.py` · V8/V9/V10/V11 · **新** `check_ai_context_audit.py`
- **Level A（自证）**：§8 AC-1~AC-10
- **Level B**：无（CI step 由 PR CI 实证）
- **大闭幕后**：全 diff credential 扫描（validator 无凭据）+ 无 contract/INDEX 冗余体（本切片不改 capabilities/contract）。

## 10 Risks / Anti-goals

| 风险 | 缓解 |
|---|---|
| **validator 误报既有条目** | AC-2 先复现 Q2/Q3 pass（write-once 合规是硬前提） |
| **把「派生匹配」做成 blocking → false-fail** | §2/§5 明拒 Option 3；本 gate 只校 schema 结构、不重算 hash、不 blocking 派生 |
| **hex 硬要 64 位挂 16 位截断** | §3 容 16∪64（Intake F6） |
| **naive 扩 SCAN_ROOTS 挂全部条目** | §2：专属 validator，不动 `check_frontmatter.py` |
| **误改 write-once 条目** | AC-9 `git diff` 硬证；validator 只读 |
| investigation 无 schema 漂 | §5.2(a) 只校 audit，investigation 正式化解耦登记 |
| 新 blocking gate 突然拦 PR | AC-2/AC-6 证语料已绿；posture Gate 5 拍板 |

**Anti-goals**：不重算 hash / 不做 blocking 派生匹配 / 不改 write-once 条目 / 不改 `check_frontmatter.py`
SCAN_ROOTS / 不动 4 必停 / 不引入新依赖（`python-frontmatter` 已在）。

## 11 Owner Gates

| Gate | 触发点 |
|---|---|
| **Stage 5** | 本 Plan 拍板 **+ scope（1/2/3）+ investigation 处置 + CI posture 选定** |
| Stage 13 | commit / push / PR 创建 **各单独拍板** |
| merge | **交 Owner**（classifier 拦 agent 直合 develop） |
| **`ci-blocking-gate-toggle` 适用**（2026-07-20 更正） | 新 blocking gate 受 `ci-gates.md` §4:41；D-016 豁免仅信任面 → 本 gate 不享。**Owner 显式 waive §4:41 dry-run** + 执行记录随 PR/#359（类比 V11 #330）。原标「不触发」= 5-lens 逮到的错误前提 + Owner 重确认 |
| **不触发** | 4 专属必停 · A13（不动 settings allowlist）· A14（不动 `.mcp.json`）· D-017（不动 manifest/`.agents`/`.codex`） |

## 12 Next Step

**Gate 5 拍板 scope + posture** → Stage 8 实施（W1-W6，TDD）→ Stage 10/11 验证 + 自评（含 5-lens）→ Gate 13 PR →
交 Owner 合并 → Stage 17 post-merge（state flip PR + 分支 origin/gitee 双清 + worktree remove + 关闭 #359；
本仓 Closes 恒不生效 → 手动关）。
