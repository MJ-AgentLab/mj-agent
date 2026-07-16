---
type: plan
summary: dual-agent-compat v5 settings biz allow 收窄执行计划（#312 递延议题 4 = A′：删 .claude/settings.json prod-lan/prod-wan 两条 allow；allow 26→24、biz 子集 5→3）+ 为保留 dev/test×3 定退出判据四要素（锚点/窗口/指标/判定口径，复用 A6 季度审计节律）+ #312 议题 3（pg 凭据 default 单一真相）vault 备料〔不拍板、不实施〕+ 更正 #312 comment 失真数字；1 PR（#344 `maintain/344-settings-biz-allow-narrow`）；不改 ci.yml、不翻 gate 姿态、不动 .mcp.json/manifest/4 必停面；总锚 #312
owner: ranzuozhou
created: 2026-07-16
updated: 2026-07-16
completed: 2026-07-16
state: completed
track: shared
---

# [PLAN] 双工具兼容 v5 — settings biz allow 收窄切片（issue #344）

## 1 Linked Artifacts

- Issue：#344（本切片）；总锚 **#312**（v5 实施总锚，「独立拍板议题」4 项之第 4 项 = 本切片）
- Intake：[[[INTAKE]_dual-agent-compat_settings-narrow|本切片 Intake]]（Owner 拍板记录 §7 + brief 三处失真更正 §3）
- 程序计划：[[[PLAN]_dual-agent-compat|v5 计划]]（§11.2 P4 判定口径 / D-013 MCP 三档 / D-017）
- 前序切片：[[[INTAKE]_dual-agent-compat_p4-gate-definition|#341 INTAKE]]（`:85` = 本切片 scope 权威锚）
- Vault 依据（不入仓）：`claude-codex-agent-kernel/mj-agent/[ASSESSMENT]_settings-biz-allow-narrowing-2026-07-14.md`（S2 #330 AC10 产物）
- 治理：[[../policies/ai-agent|ai-agent]] §4（HITL 10-enum）· [[../policies/ci-gates|ci-gates]] §5.1（A13）· [[../decisions/ADR-006_Fail_Safe_Reads|ADR-006]]（数据边界四层）

## 2 Context

`.claude/settings.json` `permissions.allow` 现 **26 条**（`:5-30`），其中 biz pg server 5 条
（`:22-26`）+ ssh-manager 1 条（`:27`）为**工具级通配**——会话内对这些 MCP server 的任意调用
**免 prompt 自动放行**。

**纪律张力（vault 评估 §二）**：`mcp__pg-mj-system-biz-prod-{lan,wan}__query` 直连**绕开 L1/L1b**
（ADR-006 四层中 L1 regex + L1b sqlglot precheck 只在 agent 4-tool 链内）。L3
（`default_transaction_read_only`）+ L4（analyst GRANT + `statement_timeout=60s`）仍兜底 → **写被挡**；
但 SELECT 不受 `no_select_star` / `require_time_range` / `require_limit` 约束。prod 面免 prompt
与「prod 面必停」姿态不一致。

**本切片 = A′**，Owner 2026-07-16 拍板（Intake §7）。P4 本体同期实测排除（Intake §2）。

## 3 Scope

**In-scope（4 项）**

1. **A′ 收窄**：删 `.claude/settings.json:25` + `:26` 两行 → allow 26→24，biz 子集 5→3
2. **退出判据**：为保留的 `:22-24`（dev / test-lan / test-wan）定四要素（§4）
3. **议题 3 备料**：vault 产出 pg 凭据 default 单一真相评估/提案（**不拍板、不实施**）
4. **更正 #312 comment 失真数字**（`~9 distinct SHA` / 「20-run 腿先绑定」→ 实测 12 / 18，日历腿绑定）

**Out-of-scope（防 scope drift；逐项有据）**

| 项 | 不做的理由 |
|---|---|
| `.claude/settings.json:27` `mcp__ssh-manager__*` | 承 [[[INTAKE]_dual-agent-compat_p4-gate-definition|#341]] §7 拍板项 6 + vault §四：ssh 最终形态（工具子集白名单 vs 全删）与 #312「ssh-manager wrapper」议题**一次拍板** |
| memory×5 promotion → `project` | 依赖议题 3 先决（Intake §3 F4：guard 现 dormant，promotion 即触发） |
| pg-default **实施** | 本切片仅备料；拍板另起切片 |
| P4 本体 / 任何 gate 姿态翻转 | 观察期未满（Intake §2）；翻转须逐 gate `ci-blocking-gate-toggle` |
| `.mcp.json` / manifest `mcp`·`codex.posture` | A14 / D-017，不在本次授权内 |
| `evidence/ai-context-audit/2026-Q2.md:110` | write-once 冻结快照（`SCHEMA.md` §1），已先于本切片漂移；改它污染审计链 |
| `policies/ci-gates.md:67-68` 归属描述不精 | 先于本切片存在、与本切片正交 → Intake §9-4 登记待议 |

## 4 退出判据设计（保留 dev/test×3；Owner 已拍板「一并定」）

> **设计原则**（承 #341 教训）：判据必须**可裁定**——两个分支都产出**可核验动作**，无「按需评估」
> 类空口径。**不新设时钟**：复用 A6 季度审计既有节律与产物（与 §11.2(4)「吸收时序、保留产物」同构）。

| 要素 | 定义 |
|---|---|
| **锚点** | 本切片 PR 合入 develop 的 merge commit（窗口起点）。基线值见下方「基线快照」，由**逾期的 2026-Q3 审计**记录（见下方「窗口 = Q4 而非 Q3」）。 |
| **窗口** | 至 **2026-Q4 A6 审计**产出（`evidence/ai-context-audit/2026-Q4.md`；到期 = 2026-09-30 之后的季度自然边界 ≈ **2026-10-01**）为止 → 真实观察期 ≈ **2.5 月**。复用 `evidence/ai-context-audit/SCHEMA.md` §3 季度自然边界节律（**非 CI cron**——SCHEMA §1 明示 cron 会静默失效）。该审计 `scope` 本就含 `claude-settings-hooks`，本判据是其既有覆盖面内的一条 finding，非新增审计品类。 |
| **指标** | Q4 entry 记一条二值 finding `biz_devtest_allow_used: yes/no` = 窗口内三条 allow 是否发生**真实调用**，佐以两项可机器复核的证据（见下）。 |
| **判定口径** | **`no`（零调用）** → 默认提 PR 删三条（allow 24→21），Owner 拍板即合，无需新评估。<br>**`yes`（有调用）** → Q4 entry **逐条**记具体用途；Owner 在 (a) 维持通配 / (b) 收窄为 per-tool 子集（如仅 `__query`）之间拍板。 |

**窗口 = Q4 而非 Q3（Owner 2026-07-16 前提更正后重确认；留档不覆盖）**

初版判据锚 Q3，建立在 AI 提供的**两条错误事实**上（「Q3 ≈ 2026-10-01」+「`M-FU-AI-AUDIT` 提醒已存在」）。
实测更正：

| 项 | 实测 |
|---|---|
| Q3 审计到期 | **2026-07-01** —— `evidence/ai-context-audit/2026-Q2.md:145` 逐字「register `M-FU-AI-AUDIT-2026-Q3` plan **after 2026-06-30** (next quarter boundary)」→ 今日（2026-07-16）**已逾期 ~15 日**（未及 SCHEMA §3 的 >30 日 lapse 门槛） |
| `M-FU-AI-AUDIT-2026-Q3` 提醒 | **从未注册** —— `plans/` 无该文件；全仓 `M-FU-AI-AUDIT` 命中仅为「机制引用」（`SCHEMA.md:54` 规则 / `ADR-032:109` 注 / `2026-Q2.md:145` 注册指令 / 本切片自身） |

→ 若锚 Q3：关闭事件**已过**，判据以**零观察**触发并默认删除它本要观察的三条 —— 即 #341
「按字面执行不产生预期效果」同型洞。**Owner 在更正后的前提下重新拍板：改锚 Q4。**

- **逾期的 Q3 审计 = 基线快照记录者，不是窗口关闭者**：它须记录本切片的 E1/E2 锚点值（Intake §9-5 已登记该 re-baseline）。
- **诚实风险（写入判据，不藏）**：A6 提醒机制**已实证会失效**（Q3 即例）。若 Q4 亦失效，本判据永不触发。
  缓解 = §6 W6 在本切片登记 M-FU 补注册 Q3 + Q4 提醒；**但这只是缓解，不是保证** —— 该残余风险由 Owner 明示接受。

**指标的两项证据**

- **E1 — 真实调用计数（尽力而为）**：对本机 Claude Code transcripts 匹配**精确 tool_use pattern**：

  ```bash
  grep -rl '"name":"mcp__pg-mj-system-biz-\(dev\|test-lan\|test-wan\)__' ~/.claude/projects/ | wc -l
  ```

  > **判据自身的一部分——必须用精确 pattern**：裸名 grep（`mcp__pg-mj-system-biz-dev__`）会被 agent
  > 讨论正文污染。2026-07-16 实测：裸名命中 **1077** 文件，精确 tool_use pattern 命中 **2** —— 约
  > **500× 假阳**。将来执行此判据者若用裸名 grep 会得出「大量使用」的错误结论。

- **E2 — 仓内不变量（权威、可 CI 复核）**：`grep -rln "settings\.json" scripts/ .github/ tests/ --include=*.py | wc -l` → **0**（无任何 `.py` 读该文件）。
  > **反例警告**：勿用「biz server 名」计数做此不变量——`grep -rn "pg-mj-system-biz-dev\|...-test-lan\|...-test-wan" scripts/ .github/ .claude/skills/ tests/` 今日 = **6**，但 6 处**全部**是
  > `check_development_agent.py:68-70` 的 `MCP_FORCED_NEVER` 常量 + `test_agents_sync.py:300,328` /
  > `test_sdd_development_agent.py:300` 的 `.mcp.json` projection fixture ——**同名不同面**，与 settings allow 无关。

**基线快照（2026-07-16，锚点值）**

| 项 | 值 |
|---|---|
| E1 真实调用（历史全量，本机） | `biz-test-lan__query` = 2 文件 · `biz-dev__query` = 1 文件 · `biz-test-wan__*` = **0 文件** |
| E2 仓内不变量 | 0（无 `.py` 读 settings.json） |
| allow 条数 | 26 → 24（本切片后） |

**诚实边界（写入判据，防将来误读）**

- E1 是**本机、仓外**证据：transcripts 可被清理/轮转、不覆盖其他工程师机器 → **尽力而为，非权威计数**。
  故 `no` 分支须由 Owner 使用自述**交叉确认**后方可执行默认删除。
- E2 是权威但**只证「无自动路径依赖」**，不证「无人使用」。两项互补，缺一不可。

## 5 收窄的真实影响（不夸大、不缩小）

- **不是断连**：`.claude/settings.local.json:14-29` `enabledMcpjsonServers` 仍启用全部 14 server；
  `.mcp.json` 14 条定义不动。删 allow 只把「免 prompt 自动放行」→「弹 prompt」（= 拍板载体），
  **且仅交互模式成立**（`auto`/`bypass` 下不成立）。是真实 HITL 收紧，**不是物理隔离**。
- **不是零影响**：2026-07-16 实测 transcripts，`mcp__pg-mj-system-biz-prod-lan__query` **曾被实际调用**
  （1 文件，精确 tool_use pattern）。故收窄后该类调用**会新增 prompt**——这正是本切片的**意图**，
  但须如实记录：prod 面并非"从未使用"。`prod-wan` = 0 文件。
- **代价已在案**：vault §三 选项 B 已记「prod 面回 prompt，infra 核验交互摩擦↑」。

## 6 Work Breakdown（1 PR，`maintain/344-settings-biz-allow-narrow`）

| # | 动作 | 文件 | 备注 |
|---|---|---|---|
| W1 | 删 2 行 allow | `.claude/settings.json:25-26` | protected path → 写入弹 prompt（= 拍板）；**收窄**方向 classifier 不硬拦 |
| W2 | `[Unreleased]` 条目 | `CHANGELOG.md` | 依家族先例（`:46` playwright allow-add / `:85` ADR-034 deny→ask / `:123` skillListingBudgetFraction） |
| W3 | 落盘 Intake + Plan | `plans/[INTAKE]_…_settings-narrow.md` + 本文件 | `state: active`；merge 后 flip `completed`（家族惯例 = 独立小 PR） |
| W4 | vault pg-default 评估 | `D:/Document/My-Local-Vault/claude-codex-agent-kernel/mj-agent/` | **不入仓**（S2 §61 先例：产物落 vault、不进 PR 代码面） |
| W5 | 更正 #312 comment | GitHub | 原帖留档不覆盖 → **新发一帖**更正（承「原始记录留档不覆盖」纪律） |
| W6 | 登记 A6 提醒补注册 M-FU | Intake §9-5 + #312 | `M-FU-AI-AUDIT-2026-Q3`（逾期，记基线）+ `M-FU-AI-AUDIT-2026-Q4`（本判据的关闭者）**均未注册** → 本切片**登记**，实际注册与补跑审计**不在本切片**（A6 审计是独立产物，折入会撑大切片） |

## 7 Verification

- **Level A（read-only）**：`ruff check` · `mypy src/mj_agent` · `pytest tests/unit tests/eval`
  （clean worktree 无 #298 假红）· `check_frontmatter.py` · `check_wikilinks.py`
- **Level A（gate 四件）**：`check_development_agent.py --all`（V8）· `check_agents_projection.py --all`（V9）·
  `agents_sync.py --check --surface skills`（V10）· `--surface mcp`（V11）
  > **预期零变化**（Stage 3 已实证）：无 `.py` 读 settings.json → 四 gate 对本 diff 不可见。
  > Stage 3 对抗验证已在副本上**实际应用删除并复跑四 gate**，pre/post 完全一致（V8 0E/0W ·
  > V9 0E/0W · V10 `OK: projection in sync` · V11 同）——本 PR 内仍须复跑，不承袭该结论。
- **Level A（自证 grep）**：AC-1 ~ AC-5（见 §8）——**AC-5 在 PR 内重跑「零自动依赖」不变量**
- **Level B**：无（不跑 side-effect；不改 CI、不翻 gate、不动容器）
- 唯一 CI 侧接触面：`.github/workflows/check-stale-docs.yml:24` path-filter 含 `.claude/**` →
  跑 `find_stale_docs.py`；仅 rename/delete 面、恒 exit 0、`continue-on-error: true` → 不会红。

## 8 验收标准（全部可执行自证；承 #341「AC 逮住作者本人」教训）

- **AC-1** `grep -c "biz-prod-lan\|biz-prod-wan" .claude/settings.json` → `0`
- **AC-2** `grep -c "biz-dev__\*\|biz-test-lan__\*\|biz-test-wan__\*" .claude/settings.json` → `3`
- **AC-3** `grep -c "mcp__ssh-manager__\*" .claude/settings.json` → `1`（out-of-scope 未越界）
- **AC-4** `uv run python -c "import json;d=json.load(open('.claude/settings.json'));a=d['permissions']['allow'];assert len(a)==24, len(a);print('allow =',len(a))"` → exit 0 且打印 `allow = 24`
  （**须 `uv run python`**——本机裸 `python` 不在 PATH，仓惯例见 CLAUDE.md Commands 段；单命令同时自证「JSON 合法」与「条数 = 24」）
- **AC-5** `grep -rln "settings\.json" scripts/ .github/ tests/ --include=*.py | wc -l` → `0`（PR 内重跑，不承袭 Intake）
- **AC-6** 本文件 §4 四要素齐且均可裁定：锚点 / 窗口 / 指标 / 判定口径 各有落值，两分支均有可核验动作
- **AC-7** vault pg-default 评估产出，每条事实断言带 `file:line`，至少覆盖
  `agents_sync.py:262-268` · `:237` · `check_agents_projection.py:137` · `sdd/development-agent.yml:731-735` · `.mcp.json:27,36,45,54,63`
- **AC-8** #312 更正帖所述数字 == 实测：
  `gh run list --workflow ci.yml --limit 100 --json createdAt,headSha --jq '[.[] | select(.createdAt >= "2026-07-14T03:39:45Z")] | map(.headSha[0:8]) | unique | length'`
- **AC-9** 四 gate 脚本本地全绿（V8/V9/V10/V11 各 exit 0）
- **AC-10** CI 全绿；V8/V9/V10 step 输出 clean（本切片不改其姿态）
- **AC-11** `check_frontmatter.py` + `check_wikilinks.py` exit 0
- **AC-12** #312 议题 4 复选框勾选；议题 3 **保持未勾**（本切片只备料）

## 9 Risks / Anti-goals

| 风险 | 缓解 |
|---|---|
| **判据变空口径**（#341 同型洞复发） | §4 两分支均绑定可核验动作；`no` 分支默认动作明确（提 PR 删），非「再评估」 |
| **判据锚在已失效的机制上**（本切片自评实际逮到的洞） | 初版锚 Q3 = 关闭事件已过 → 零观察即触发。已由 Owner 前提更正后重确认改锚 Q4（§4）；A6 提醒失效风险显式留在 §4 且由 Owner 接受，W6 登记补注册 |
| **将来执行判据者用裸名 grep 误判** | §4 把「精确 pattern + 500× 假阳实测」写进判据正文，非脚注 |
| **scope drift 到 ssh-manager / memory×5** | §3 Out-of-scope 逐项有据；AC-3 grep 硬证 ssh 行未动 |
| **误伤保留 3 条** | AC-2 grep 硬证 = 3 |
| 收窄导致 infra 核验摩擦↑ | 已知代价（vault §三 B）；dev/test 面保留 → 日常核验零摩擦 |
| **把 vault Option B 当作本切片 verbatim** | Intake §7.1 显式区分：A′ = B 的 prod 子集；权威 scope 锚 = #341 INTAKE `:85` |

**Anti-goals**：不放宽任何权限面；不动 4 必停；不翻 gate 姿态；不改 `.mcp.json`/manifest；
不重写任何 `state: completed` 的前序切片记录（F3 行号更正在 Intake §3 就地记，不回改 #341）。

## 10 Owner Gates

| Gate | 触发点 |
|---|---|
| Stage 5 | 本 Plan 拍板（进 Stage 8 实施前） |
| protected-path prompt | W1 写 `.claude/settings.json`（harness 硬编码，`allow` 不可抑制） |
| Stage 13 | commit / push / PR 创建 **各单独拍板** |
| merge | **交 Owner**（classifier 拦 agent 直合 develop） |
| **不触发** | `ci-blocking-gate-toggle`（不改 gate 姿态）· A14（不动 `.mcp.json`）· D-017（不动 manifest） |
| **A13 适用** | settings allowlist diff 走 PR 合并审查 |

## 11 Next Step

Gate 5 拍板 → Stage 8 实施（W1-W5）→ Stage 10/11 验证 + 自评（含 5-lens 对抗审查）→
Gate 13 PR → 交 Owner 合并 → Stage 17 post-merge（state flip PR + #312 议题 4 勾选 +
分支双清 + `closingIssuesReferences` 独立核验）。
