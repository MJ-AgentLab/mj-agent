# Changelog

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### Fixed — hardened offline pytest boundary and Agent/CI runner (#499)

- **PR-0b (`bugfix/499-offline-test-boundary`)**：safe direct pytest 始终 offline；新增
  Settings construction seam、静态 boundary checker 与 hardened Agent/CI runner；external
  pytest bands 仅验证 `SKIP_POLICY_EXTERNAL_DEPENDENCY`，凭据不会启用 live route。

### Fixed — execution-loop 章节交叉引用系统性指错 + 新增 `kernel-section-refs` gate（#453）

- **19 个活体文件 / 66 处交叉引用重指向 + 机器化兜底（`maintain`，branch
  `maintain/453-loop-section-refs`）**：**根因** = kernel `sdd/workflows/execution-loop.md` 的 `§4`
  在 M6 PR4 重构中**换义**——历史源 HITL_Prompt 的 `§4.1`-`§4.15` 是 per-stage prompt，kernel
  的 Kernel home note 明写**不 re-port**（归 `.claude/skills/mj-agent-*` 本体），而 kernel `§4` 现为
  「Stage → Skill 映射表」（port 自 HITL_Prompt **`§5`**）；被 re-port 的两节亦重编号
  （`§4.8`→`§5`、`§4.9`→`§6`、`§4.15`→`§7`）。**改动**：(1) 35 处 `dangling-section`
  （`§4.3/4.4/4.5/4.6/4.7/6.6/§11/§12` 等）按语义逐条重指向，per-stage prompt 一律改写为
  「`§4.1` 的 Stage N 映射 + 历史源 HITL_Prompt `§4.X`」；`§11 self-review` 实为 **stage 号误作章节号**
  （Stage 11 = AI Self-review，住 kernel `§6`）。(2) 31 处 `positional-hitl-index`（`必停 10/11/12/13`）
  改引 canonical enum 名——`§3.1` 通用必停已从 9 增至 **12**，专属 4 项的位号早已从 10-13 漂到
  **13-16**；`flow-intake` Step 8 同步补齐缺失的 3 条通用必停。(3) `flow-self-review` 的 `§6` 清单出处
  按 kernel 真值订正（item 10 = version bump、item 11 = commit type/scope；原引「`§4.7` Rule 12」不存在）。
  (4) 新增 **`scripts/check_loop_section_refs.py`** + 41 条 unit test，挂 `ci` job **warning-first**。
  **不动**：写作「原 HITL_Prompt `§4.X`」的**正确归档署名**（据此 5 个 infra freeze skill 全部干净，
  **无需 re-freeze / bump content hash**）；`CHANGELOG.md` / `plans/` / `evidence/` / `archive/` 等历史账本。
  `flow-diagnose` 在 `.agents/` 投影白名单内，已同批 `agents_sync.py sync`（V10 绿）。
  配套 `sdd/gates.md` v0.10→v0.11（新增 `kernel-section-refs` 行，明写语义盲区与账本排除面）+
  `[STANDARD]_MJ_Agent_Skill_Authoring_Craft` v1.0→v1.1。**新增 warning gate ≠ posture 翻转**
  （#444 判例），不触发 `ci-blocking-gate-toggle`。

### Added — memory checkpoint TTL 逐出（mechanism C；#386；ADR-038 可选叠加）

- **`data-agent.memory-checkpointer` 新增 opt-in TTL 逐出（`feature/386-memory-ttl-eviction`；owning
  issue #386；承 #365 mechanism B）**：ADR-038 采纳为「可选叠加」的机制 C 落地——新增
  `mj-agent memory-evict [--older-than DAYS] [--dry-run]` CLI，删除**最近活跃早于 TTL** 的整条
  checkpoint 线程（线程龄取自 langgraph uuid6 `checkpoint_id`，无需 schema 变更；经 langgraph
  `adelete_thread` 删 `checkpoints`+`checkpoint_blobs`+`checkpoint_writes`），以此**界定 at-rest 残留
  的存活时长**——含 mechanism B 的 row-digest **不覆盖**的 answer-side（`AIMessage` NL）biz 值。
  **默认关 + 不可逆**：`MJ_AGENT_MEMORY_TTL_DAYS` 默认 `0`（禁用；opt-in），逐出是硬 DELETE（异于
  mechanism B 的非破坏性 forward digest），`--dry-run` 先看；creds 缺失 / TTL≤0 均 no-op exit 0；
  **无 in-app 调度器**——外部 cron 驱动（runbook §6）。**安全**：删前对每线程**再核龄**（TOCTOU 缓解，
  竞态转新则跳过），非 uuid6 / 损坏 id 跳过而非中止整轮。**验证**：`tests/unit/test_memory_retention.py`
  （uuid6→epoch 对钉 langgraph 1.1.8、边界、dry-run、竞态 / 损坏跳过）+
  `tests/unit/test_cli_memory_evict.py`（opt-in 门 / SKIP / override / dry-run）+
  `tests/smoke/test_memory_retention_smoke.py`（真库选择性逐出 + MAX-picks-newest，容器门控〔执行递延〕）。
  capability 演进：REQ-005 + `contracts/checkpoint-retention.contract.yml`（INV-R1..R4）+ behavior.feature
  ×2 + trace + design §6 + runbook §6 + evidence；ADR-038 §Relationship addendum。经 5 维对抗性 review
  （确认龄 / 边界 / MAX 逻辑正确；4 项 low finding 已修）。

### Added — memory checkpoint at-rest 脱敏 default-on + capability 升 active（#365 AC4-6；ADR-038）

- **`data-agent.memory-checkpointer` capability 升 `active` + `MJ_AGENT_MEMORY_REDACT_BIZ_ROWS`
  默认开（`feature/365-redaction-activation`；owning issue #365；承 #366 ADR-038 / #367 spec /
  #368 build-core）**：**行为变更（用户/运维可见）**——checkpoint 持久化时，`execute_sql`
  ToolMessage 的逐字 biz `rows` 现**默认**被替换为确定性 per-column 计数摘要（`{non_null, distinct}`），
  保留 `executed_sql` 供 recoverable-by-refetch；**活跃对话（in-process message state）字节不变**
  （REQ-002），LLM 当轮所读不受影响——仅写入 `mj_agent_memory` 的字节改变，关闭 ADR-037 记录的
  「checkpoint 明文存 biz 派生行」at-rest 残留暴露面。**回退**：`.env` 置
  `MJ_AGENT_MEMORY_REDACT_BIZ_ROWS=false`（可逆、纯配置、无数据迁移；forward-only——升级前既存
  checkpoint 不回溯脱敏）。**验证**：新增 `tests/smoke/test_memory_redaction_canary.py`——直接读原始
  `checkpoint_blobs`（`aput`）**与** `checkpoint_writes`（`aput_writes`）BYTEA，断言两条 on-disk 路径
  均无逐字 cell 值（both-hooks-or-it-leaks，同 ADR-029 #288 类）+ 冒烟 round-trip 断言冷恢复读回为
  digested + 保留 `executed_sql`；含 negative-control（stock saver 两路径均泄漏 → 证 canary 真能抓漏）。
  capability 12-artifact 补齐：`contracts/behavior.feature`（4 @risk:medium scenarios，REQ-001/002/003
  offline pytest-bdd 自动化、REQ-004 both-paths 走容器 canary）+ `trace.yml`（schema v1.2）+
  `runbook.md` + `evidence/verification/`；`lifecycle_state: planned → active`（G8 evidence gate 满足）。

### Added — investigation-type schema 正式化：SCHEMA §2.2 + validator 扩展（#362 / a2 #2-9）

- **`evidence/ai-context-audit/SCHEMA.md` §2.2 正式定义 `ai-context-investigation` frontmatter schema +
  `scripts/check_ai_context_audit.py` 扩展校验之（`maintain`, branch `maintain/362-investigation-schema`；
  A6 durability gate #359 / #347 §三.2 的登记 follow-up〔该 slice Intake §9-1〕；**非** #312 tracker 行）**：
  **动机**：`evidence/ai-context-audit/` 含两类条目——`ai-context-audit` 季度 cycle（`YYYY-QN.md`）+
  `ai-context-investigation` ad-hoc 调查（`YYYY-MM-DD_*.md`，现存 05-22 a2/a3 ×2）；A6 gate 初版**只校 audit**
  （plan §5.2 Option (a)，拒 Option (c)「撑大切片」并登记 follow-up），SCHEMA §2 从未定义 investigation 类
  → validator 按 filename 天然跳过（诚实临时态）；a2 finding **#2-9** + `schema_extension_request: true`
  提请正式化。**改动（Gate 5 拍板 = D1 formalize+validate + D2 same-blocking-gate day-one）**：
  ① SCHEMA §2 泛化标题为「Entry Frontmatter Schemas」+ 新增 **§2.2** 定义 investigation schema（required 5 =
  `type`/`investigation`/`auditor`/`scope`/`findings_summary`；optional `subtype`/`related_episodes`/
  `parent_artifacts` 仅在出现时校；`phase`/`date`/`schema_extension_request` 文档化不受约束；**不携
  `content_hash_snapshot`** = 与 audit 的关键结构差异，故 §2.1 面集推导不适用）；② validator
  `find_cycle_entries`→`find_entries` 三分（cycle/investigation/other，filename-based：
  investigation=`YYYY-MM-DD_*.md`）+ 新增 `validate_investigation_entry`，`check`/`run` 校两类；两既存
  investigation 文件 **green day-one**。**治理（承 §三.1）**：coverage-expansion of an **already-blocking**
  gate（**无** `continue-on-error` flip、**无** `ci.yml` edit）——**不**自判 `ci-blocking-gate-toggle` /
  ci-gates §4:41 为 N/A；Owner 2026-07-20 D2 显式裁定 = 视作既有 blocking gate 的 coverage 扩展（语料 2 文件
  均 green、structural-only，类比 A6 #360 / V11 #330）。**有意非目标**（同 A6）：不重算 hash / 不校 key 路径 /
  不做 blocking 派生匹配。单测扩至 65（新增 investigation schema 正/负向 + `find_entries` 三分 + 真实树 a2/a3
  green 钉线；audit 侧全绿无回归）。**配套**：`plans/[INTAKE]/[PLAN]_dual-agent-compat_investigation-schema.md`。

### Added — A6 durability gate：evidence/ai-context-audit 专属 schema validator（#359 / #347 §三.2）

- **新增 `scripts/check_ai_context_audit.py`（`maintain`, branch `maintain/359-a6-durability-gate`；
  #347 §三.2 / `evidence/ai-context-audit/SCHEMA.md` §2.1 披露的 durability 缺口 follow-up；**非** #312
  tracker 行）**：**动机**：`evidence/ai-context-audit/` 的季度 A6 审计快照用 SCHEMA §2 **自有** schema
  （`type: ai-context-audit` + `cycle`/`auditor`/`scope`/`findings_summary`/`content_hash_snapshot`，**非**
  canonical base 7 字段），且该目录在 `check_frontmatter.py` `SCAN_ROOTS` **之外** → 无 CI gate 校验其 §2
  schema；A6 提醒机制已实证会静默失效（`M-FU-AI-AUDIT-2026-Q3` 从未注册）→ 结构性 gate 是正解；SCHEMA §2.1
  durability 边界本就自陈「应加一支专属 §2 validator」。**改动（Gate 5 拍板 = Option 2 + investigation-(a) +
  blocking）**：新 validator 校 `ai-context-audit` §2 frontmatter schema（结构）+ `--derive` 子命令**机器化**
  §2.1 面集推导（供下期 auditor 现场生成面集，消除人肉写死风险 = #304→Q2-15-stale 病因）；`ci.yml` 新增
  **blocking** gate step（Q2/Q3 已合规；**`ci-blocking-gate-toggle`**——Owner 2026-07-20 显式 waive
  `policies/ci-gates.md` §4:41「blocking 前 1 周 dry-run」〔非 D-016 信任面豁免〕，执行记录随 PR/#359，类比 V11 #330）；
  `SCHEMA.md` §2.1 durability 注更新为「gate 已存在」；
  38 单测（schema 正/负向 + tmp_path git-init 派生 + 真实树钉线）。**有意非目标**（**time-varying**——是**下期
  审计**要检的 drift，非 gate 违规）：**不重算** hash 值 / **不校** key 路径当前存在 / **不做 blocking 派生
  匹配**（面集 Q2=15→Q3=23 随仓变，blocking 会 false-fail 并强制每次改动重跑季度审计，违 §1 A6
  quarterly-not-cron 设计）。`ai-context-investigation` 类跳过（SCHEMA §2 未正式定义，正式化另立 follow-up）。
  **配套**：`plans/[INTAKE]/[PLAN]_dual-agent-compat_a6-durability.md`。

### Changed — ssh-manager settings allow 收窄（#312 独立拍板议题 2，#356）

- **`.claude/settings.json` `permissions.allow` 删 `mcp__ssh-manager__*` 单条通配（`maintain`,
  branch `maintain/356-ssh-manager-allow-narrow`；vault `[ASSESSMENT]_settings-biz-allow-narrowing-2026-07-14.md`
  §四 框定 ssh 最终形态；总锚 #312）**：**动机**：该通配令 ssh-manager 全部 **37 工具**（24 为写/状态面，
  含 `ssh_execute_sudo` / `ssh_deploy` / `ssh_db_import` 等 root/部署/DB 写入，且 ssh **无 biz 的 ADR-006
  L3/L4 DB 侧兜底**）在会话内**免 prompt 自动放行**，`deny`/`ask` 无兜底 —— 是比 #344 已收窄的 biz-prod
  **更宽**的面（无下游 floor）。**改动（Gate 5 Owner 拍板口径 A = 全删）**：删该行 → allow **24 → 23**；
  ssh-manager 全部工具由自动放行 → 弹 prompt（= 拍板载体），与 #344 biz-prod 处置逐字同构。**诚实边界**：
  `.mcp.json` server def + `settings.local.json` `enabledMcpjsonServers` 不动 —— **不是断连**，ssh-manager
  仍可**显式批准后**调用；**且仅交互模式完全成立**（`bypass` 下无 deny 兜底、全放行——Owner 已在 A/C 权衡中
  知悉并选 A）。**零自动依赖**：全仓无 skill/script/src 调用任何 ssh-manager 工具（唯一**调用面/功能**引用 =
  `mj-agent-infra-app-start/SKILL.md` 的否定引用；`ssh-manager` 名另现于 `never`-tier 投影治理元数据
  〔manifest / check 脚本〕，非工具调用），收窄不破坏任何自动化流程。**配套**：新增
  `plans/[INTAKE]/[PLAN]_dual-agent-compat_ssh-manager.md`（含 37 工具面分类 + 零调用证据 + A/B/C 分析）。

### Changed — ci-gates ADR-034 同步 + 补跑逾期 2026-Q3 A6 审计（#312 P4 等待期切片，#347）

- **`policies/ci-gates.md` 同步 ADR-034 `deny→ask`（`documentation`，branch
  `documentation/347-a6q3-cigates-sync`；总锚 #312）**：ADR-034（2026-06-20）把 5 项必停面由
  `permissions.deny` 物理硬锁改为 `permissions.ask` 逐写拍板门，但本文件未同步 —— `:67` 仍称
  settings.json = 「`deny` 红线（4 项必停文件 + secrets.enc）」、`:68` 把 `allow` 归
  `settings.local.json`（实况 settings.json 持 **24** 条 allow）、`:88`（**A13 PR 阻塞条件 b**）
  引用该失效定义、`:38`（**A6 季度审计自身的 scope 条款**）只列 `deny` 未提 `ask`。**改动**：§5
  边界表两行改「`deny` ∪ `ask` 两档合起来的边界」+ 加 ADR-034 释义注；A13(b) 去失效引用 + 新增
  **(d)**「5 项必停面不得脱离 `ask` 档」；§4:38 审计项加 `permissions.ask`；连带 3 处硬编码计数
  （「3 条」等）去数字化；`version` 0.2→0.3。
- **补跑逾期的 2026-Q3 A6 审计（`evidence/ai-context-audit/2026-Q3.md`，write-once）**：Q3 到期
  2026-07-01，实执 2026-07-16（**逾期 ~15 日** < SCHEMA §3 的 30 日 MUST-gap 门槛，gap 自愿留痕）。
  **头条发现**：8 个冻结 infra skill **8/8 drift-clean vs contract**（6 面 vs Q2 漂移全由已记录的
  再冻结解释，`frozen_at` 均晚于 Q2）—— 冻结治理成立。**面集 15→23**（Owner 拍板 D1 = ask 门所护的
  **markdown/AI-context 面**：5 CLAUDE.md + 9 runtime SKILL.md + system.md + 8 infra；`ask` 档另 3 个
  **非-markdown** 必停面〔`guardrail.py`/`precheck.py`/`qcm_catalog.yaml`〕由各自 contract/必停门监控、
  不入本 hash 审计）；8 新面无 Q2 基线 → baseline-only。
  **实证 A6 提醒机制静默失效**：`M-FU-AI-AUDIT-2026-Q3` 从未注册（`ls plans/` 无该文件），讽刺点 =
  SCHEMA 选 M-FU 提醒而非 CI cron 正为规避「silent lapse」，结果 M-FU 自身以同样方式失效。
  记 **#344 保留项判据的 E1/E2 锚点**（窗口锚 = #345 merge `07e1be6`；E1 精确 tool_use pattern = **2**、
  对照裸名 grep = **1136** ≈ 568× 假阳；E2 = `settings.json:22-24` 三条 biz allow）。
- **`evidence/ai-context-audit/SCHEMA.md` §2.1 改推导规则（Owner 拍板 D3）**：本次病因 =
  「15-surface / 6 infra / 3 runtime」硬编码常量无 gate 盯而静默过期（#304 加两冻结 infra skill 时
  无人回改）。改为**从执行面机械推导**（必停轨 = `ask` glob 命中 ∪ contract 冻结 infra；CLAUDE.md 轨 =
  `git ls-files`），数量降为观测值；§3/§4 硬编码去数字化 + 标历史条款。
- **补注册 `plans/[PLAN]_m-fu-ai-audit-2026-Q3.md`（completed）+ `-Q4.md`（active）**：Q3 =
  逾期补注册 + 闭合；Q4 = 前瞻提醒，兼 **#344 保留项退出判据的关闭者**（2026-Q4 复测 E1/E2 作
  `biz_devtest_allow_used` 二值判定）。**残余风险**（Owner 已明示接受）：Q4 提醒若亦失效则 #344
  判据永不触发。
- **诚实边界**：本切片**零** `src/` / config / CI gate 姿态变更；改的是**描述** CI gate 的文档，
  非 gate 本身（无 `ci-blocking-gate-toggle`）。**方向 = 修正/收敛**，非 permission widening →
  agent 可 commit。**P4 本体不在本切片**——实测 V10 腿 14/20（绑定腿）+ 日历腿 2026-07-28 未到，
  §11.1 AND → 今日结构性出局。配套 `plans/[INTAKE]/[PLAN]_dual-agent-compat_a6q3-cigates.md`。

### Changed — settings biz allow prod 面收窄（#312 递延议题 4 = A′，#344）

- **`.claude/settings.json` `permissions.allow` 删 2 条 biz prod 通配（`maintain`，branch
  `maintain/344-settings-biz-allow-narrow`；vault `[ASSESSMENT]_settings-biz-allow-narrowing-2026-07-14.md`
  = S2 #330 AC10 产物；总锚 #312）**：**动机**：`mcp__pg-mj-system-biz-prod-{lan,wan}__query` 直连
  **绕开 L1/L1b**（ADR-006 四层中 L1 regex 单句/SELECT-only + L1b sqlglot `no_select_star` /
  `require_time_range` / `require_limit` 只在 agent 4-tool 链内生效）；L3
  （`default_transaction_read_only`）+ L4（analyst GRANT + `statement_timeout=60s`）仍兜底 → **写被挡**，
  但 SELECT 无 guardrail/precheck 约束。prod 面「免 prompt 自动放行」与「prod 面必停」姿态不一致。
  **改动**：删 `permissions.allow` 的 `mcp__pg-mj-system-biz-prod-lan__*` + `mcp__pg-mj-system-biz-prod-wan__*`
  两行 → allow **26 → 24**，biz 子集 **5 → 3**（保留 `dev` / `test-lan` / `test-wan`）。
  **效果的诚实边界**：`.claude/settings.local.json` `enabledMcpjsonServers` 仍启用全部 14 server、
  `.mcp.json` 14 条定义不动 —— **不是断连**，只是把自动放行变成弹 prompt（= 拍板载体），
  **且仅交互模式成立**（`auto`/`bypass` 下 `ask`/allow 语义不同）。**亦非零影响**：实测本机
  transcripts（精确 tool_use pattern），`mcp__pg-mj-system-biz-prod-lan__query` **曾被实际调用**
  （`prod-wan` = 0）→ 该类调用此后会新增 prompt，此即本次意图。**配套**：新增
  `plans/[PLAN]_dual-agent-compat_settings-narrow.md` §4 为**保留的 dev/test×3 定退出判据四要素**
  （锚点 = 本 PR merge commit；窗口 = 至 **2026-Q4** A6 审计产出（≈ 2026-10-01，观察期 ≈ 2.5 月），
  **复用 `evidence/ai-context-audit/SCHEMA.md` §3 既有季度节律，不新设时钟**——初版锚 Q3 系错误前提
  （Q3 实为 2026-07-01 到期、今已逾期 ~15 日，见 `2026-Q2.md:145`；且 `M-FU-AI-AUDIT-2026-Q3` 提醒
  **从未注册**），锚 Q3 会令判据零观察即触发 → Owner 前提更正后重确认改锚 Q4，逾期 Q3 审计改任基线
  快照记录者；指标 = transcripts 真实 tool_use 调用
  计数 + 仓内不变量「无 `.py` 读 settings.json」；判定口径 = 零调用→默认提 PR 删三条 / 有调用→逐条记用途后
  Owner 在「维持通配 vs 收窄 per-tool 子集」间拍板）+ `plans/[INTAKE]_dual-agent-compat_settings-narrow.md`。
  **不动**：`mcp__ssh-manager__*`（`:27` 单条通配，覆盖含 `ssh_execute_sudo`/`ssh_db_import`/`ssh_deploy`
  写面 —— 整体推 #312「ssh-manager wrapper」议题一次拍板，per #341 INTAKE §7 拍板项 6 + vault §四）；
  `.mcp.json`（A14）；manifest `mcp`/`codex.posture`（D-017）；4 必停面；任何 gate 姿态。
  **验证**：四 gate 全绿且**对本 diff 不可见**——仓内无任何 `.py` 读 `.claude/settings.json`
  （`grep -rln "settings\.json" scripts/ .github/ tests/ --include=*.py` = 0）；
  `check_development_agent.py:67-74` 命中 biz 名（含本次删除的 prod-lan/prod-wan，`:71-72`）系
  `MCP_FORCED_NEVER` 常量（biz×5 + ssh-manager 全在此常量内，属 `.mcp.json` never-tier 校验面），
  **同名不同面**。A13 合并审查适用（allowlist diff）；`ci-blocking-gate-toggle` 不适用。

### Changed — bidirectional reverse-triggers on 3 frozen peer infra skills（#306）

- **`.claude/skills/mj-agent-infra-{env-teardown,docker-compose,studio-probe}/SKILL.md` +
  `capabilities/infrastructure/mcp-server-governance/contracts/claude-skill.contract.yml` +
  `policies/ai-agent.md` + `CHANGELOG.md`（`maintain`，branch
  `maintain/306-bidirectional-reverse-triggers`）**：#304/PR #305 给新 `app-start` / `-app-stop`
  只装了**单向** reverse-trigger（新技能 defer 到 3 个 peer，但 peer 不 defer 回来），adversarial
  self-review finding #5 因 3 peer 是 content-hash **frozen**、改 description 须 re-freeze
  （`mcp-server-trust-posture-change` HITL）而**有意延后**。今日实测过火：`env-teardown` 的 Level-1
  `down` 与 `app-stop` 的非破坏容器停机重叠；裸 "起 Studio" 同时触发 `studio-probe` + `app-start`。
  **改动**：(1) 3 个 peer 的 `description` `Do not use for:` 块各加一条 `app-start`/`app-stop`
  deferral 从句（house-style 括注 `(use …)`；**body 逐字不动 / 仍单物理行 / 仍 ≥200 字符含
  `Do not use for:`**）——`env-teardown`→非破坏停机转 `app-stop`；`docker-compose`→有序整机起停转
  `app-start`/`app-stop`（本技能是它们下委的 up/ps/logs/down 原语）；`studio-probe`→裸启动转
  `app-start`（本技能是 H1/H2/H3/R1/R2 walkthrough 非 launcher），顺手删陈旧 `in PR-C3` 引用。
  (2) **re-freeze**（Owner 拍板；`mcp-server-trust-posture-change` HITL）：contract 3 条记录
  `description_hash` 改（`f27f41f2→013d8ec2` / `77ca5b0c→388b327a` / `815bed2b→d60021f7`）+
  `frozen_at`→2026-07-08，**`body_content_hash` + `body_section_heads` 逐字不变**；先复现全 8 技能
  16 hash（**16/16 MATCH**）再录新值，per freeze discipline。(3) 顺修 `policies/ai-agent.md §7`
  陈旧 infra freeze 计数 `6→8`（连带求和 `10→12`；#304 遗留，`updated`→2026-07-08）。**验证**：
  post-edit 全 8 技能 16 hash 全复现（3 改 desc / body 不变 / 另 5 不变）、`check_claude_skill_contracts.py`
  0 WARN、pytest unit+eval + mcp-governance contract PASS、doc-validate clean。**无运行时影响**（改的是
  trigger 元数据；deferral-only 负触发 → 只降过火不改正当命中率）。Closes #306

### Added — infra app-lifecycle skills：app-start / app-stop（#304）

- **`.claude/skills/mj-agent-infra-app-start/` + `.claude/skills/mj-agent-infra-app-stop/` + doc-sync（`.claude/skills/SKILL_INDEX.md` / `docs/INDEX.md` / `sdd/workflows/execution-loop.md` / `CLAUDE.md`）+ `capabilities/infrastructure/mcp-server-governance/contracts/claude-skill.contract.yml`（`docs`，branch `feature/304-infra-app-lifecycle-skills`）**：原 6 个 infra skill 只管 **capacity**（secrets/containers/storage/endpoints——名词），无 skill owns 操作 app **runtime**（launch/stop——动词）：没有统一起服动作、`uv run mj-agent serve` 无主、停 host-run 进程（`langgraph dev` :2024 / Chainlit）无主（studio-probe 明确拒杀、env-teardown 只拆 Docker）。**改动**：(1) `mj-agent-infra-app-start`——有序 START 编排器（prereq gate via 默认 `mj-agent check`（含一次 memory-pg ping，`memory-unreachable`≠创口，分三类处理）→ storage/stack up（容器栈本步即 `up -d` 全栈，先于 `check --live`）→ `check --live`（Studio in-memory 的 async-memory FAIL 属预期）→ 运行时选择（默认容器栈 / Studio / Chainlit serve）→ launch → `curl --noproxy '*'` 根路径 verify）；slim HITL H1-H4（AskUserQuestion 仅留真选择 + `check --live` FAIL 条件确认，非破坏命令由 harness Bash prompt 当执行拍板 per ADR-034）。(2) `mj-agent-infra-app-stop`——非破坏 STOP（数据全保留），净新能力=停 host 进程（端口 owner tree-kill `taskkill /T /F`，因 `serve` `subprocess.call` spawn 一个 chainlit 子进程，单 PID kill 留孤儿）+ 容器 Level-1 `down`；STOP 节点拒破坏性 `down -v`/`--rmi local` → 转 `env-teardown`（含其自身 H3 hard-confirm），删前 offer pg_dump（仅 dev profile）。命名归 `infra` 家族（匹配 `check_claude_skill_contracts.py` 硬编码 5-family regex → 0 WARN，无需 ADR-016 amendment / validator 改动；原请求的 `ops-*` 被 ADR-016 §Decision 1 有意去掉）。(3) doc-sync（SoT=`check_claude_skill_contracts.py --all`=37）：infra 计数 6→8、execution-loop §4 域工具 skill 数同步。(4) **freeze**（Owner 拍板；`mcp-server-trust-posture-change` HITL）：`claude-skill.contract.yml` +2 条目（documented canonical algo=regex-strip frontmatter + LF-normalize + sha256；先复现 env-teardown + env-setup 记录 hash **4/4 EXACTLY** 再录新值，全 8 skill 现可复现）+ `CLAUDE.md` "Infra freeze skills" 6→8。**验证**：37 PASS / 0 WARN / 0 FAIL、`check_wikilinks` + `check_frontmatter` clean、545 tests（unit+eval+contract）pass、2-agent 对抗 self-review（1 blocker + 4 major 修：`check --live` 顺序 vs storage、H1 误路由到 env-setup、studio-probe handoff 对 Chainlit 不适用、Studio-trigger 与 studio-probe 冲突、`execution-loop` §-ref 号 §3.1→§5）。**延后 follow-up**：3 个 frozen peer skill（env-teardown / docker-compose / studio-probe）的双向 reverse-trigger（编辑其 description 会破 freeze hash + 扩 scope，须单独 PR + re-freeze）；`SKILL_INDEX` §2 Layer 1 flow-diagnose 回填（既有 count-refresh M-FU，不随本 PR 收敛）。Closes #304

### Changed — secrets 管线 LLM provider-profile 机制 + env/onboarding 完整性修齐（#297）

- **`scripts/setup-env.ps1` + `config/secrets.example` + `.env.example` + 文档群（`infra`+`docs`，branch `maintain/297-env-config-provider-profiles`）**：#294/#295 重启会话暴露两类债——① bundle §2c 单套值把 DGX 机器特例（隧道 + `host.docker.internal`）耦合进团队 bundle，且值已陈旧（仍 `127.0.0.1:18000`），任何 `setup-env.ps1 -Force` 都会回滚 07-07 的手工修正；② 新人 fresh-clone 路径多处结构洞（MCP bundle 步骤缺席主 onboarding 三文档、`NO_PROXY`/`MJ_AGENT_PG_SUPERUSER_PASSWORD` 无模板、DGX 端点全线文档给 LAN 直连假形态——vLLM 只绑 loopback 从未可用）。**改动**：(1) `setup-env.ps1` 增 `-LlmProfile ark|dgx`——bundle §2c 改携带两套命名空间键（`LLM_PROFILE_{ARK,DGX}__*` + `LLM_PROFILE_DEFAULT`），生成时解析一套落 plain 键（优先级：参数 > DEFAULT > 唯一非空套 > 交互；空值跳过；命名空间键永不落 `.env`；老 bundle plain 键向后兼容、混存时 profile 胜出 + WARN）；(2) `secrets.example` §2c 重写两套 profile + §4b 增 `MJ_AGENT_PG_SUPERUSER_PASSWORD`（compose-only，三处登记规则显式豁免 config.py）；(3) `.env.example` 增 `NO_PROXY=localhost,127.0.0.1,::1` 默认行 + `MJ_AGENT_PG_SUPERUSER_PASSWORD=` 空位（init-once 语义注释）+ `LLM_BASE_URL` 注释改隧道真形态；(4) README/Developer_Onboarding/Quick_Start 补 MCP bundle 步骤（含"完全重启"坑）+ `-LlmProfile` 用法 + proxy-502 与 /doctor-MCP 诊断行 + GitHub PAT/playwright chromium 前置；(5) ADR-027 D.3 Amendment（LAN 直连例订正为隧道 + `host.docker.internal:18000`，host 侧可达性 07-08 实测）+ ADR-030 Amendment（计数 6-8→8+§2c、D.4 迁移脚本移除）+ llm-provider runbook §1 同步；(6) frozen SKILL `mj-agent-infra-env-setup` Step 2「22 secret 注入 .env」订正为 2-bundle 事实 + 按 canonical algo re-freeze（`body_content_hash` → `f05b0fbc`，description 逐字未动、hash 复验一致）；(7) 删 `scripts/migrate-secrets-bundle-split.ps1`（一次性工具，键清单已漂移）。**Owner 侧**：`secrets.conf` 按新 schema 填值 re-encrypt + 双端 `check --live` 验证 regen 不回滚（Q1 闭环）+ fresh 拷贝 ark 套开箱即用（Q2 闭环）。Closes #297

### Fixed — Docker 镜像不可构建：Dependabot 跨 minor 把基础镜像 bump 到 3.14（#294）

- **`docker/Dockerfile` + `.github/dependabot.yml` + `capabilities/infrastructure/docker-compose/contracts/docker.contract.yml`（`fix`，branch `bugfix/294-dockerfile-python313-repin`）**：Dependabot `0a32957`（05-18）把两处 FROM 从 `python:3.13-slim@d49c1ff` 跨 minor bump 到 `3.14-slim`（`fb6875a` 05-25 续 bump 至 `c845af`，实测 Python 3.14.5），与 `requires-python >=3.13,<3.14` + `UV_PYTHON_PREFERENCE=only-system`（`eb4a7cb`，#134 venv-copy 修复）冲突——builder 阶段 `uv sync` 报 "No interpreter found for Python ==3.13.*"，镜像自 05-18 起不可构建；CI 无 docker build gate（V5 仅 contract lint），8 周无人发现。**改动**：(1) 两处 FROM 钉回 `python:3.13-slim@eb43ff1`（当日上游最新 digest，实测 Python 3.13.14；image-base 必停面 Owner 拍板 2026-07-07）+ 同步陈旧注释（header 关于 Dependabot 会同步 tag 注释的说法实践证伪）；(2) `dependabot.yml` docker 生态给 `python` 加 `ignore: version-update:semver-major/minor`——3.13-slim 线内 digest bump 照常流动，跨 minor/major 必须人工 PR 同步 requires-python + uv.lock；(3) `docker.contract.yml` `base_image` 段同步真实值（原记录 3.14-slim + "actual Python = 3.13.13" 系未验证的错误认知）+ freeze_anchor 行数 123→126。**验证**：build BUILD_EXIT=0、运行时镜像 Python 3.13.14、`SQLToolErrorMiddleware` 双 hook 在场（#288）、全栈 up 后容器内 `check --live` biz-db + async-memory PASS、`check_docker_contracts.py --bdd --tdd --compose-config` PASS 2/FAIL 0。**范围外（follow-up 登记于 #294 checklist）**：CI docker-build gate（让不可构建的 Dockerfile 在 CI 快速失败）。Closes #294

### Added — Playwright MCP server（第 14 个）供 Chainlit web-UI 开发/自测

- **`.mcp.json` + `.claude/settings.json` + `capabilities/infrastructure/mcp-server-governance/*` + `tests/bdd/infrastructure/mcp_governance/`（`feat`，branch `feature/playwright-mcp-web-ui-testing`；A14 治理 per [[decisions/ADR-028_MCP_Server_Inventory_And_Governance\|ADR-028]]）**：接入 Microsoft `@playwright/mcp`（stdio，`cmd /c npx -y @playwright/mcp@latest`，headed 默认），让 Claude Code 能驱动真实浏览器**开发 + 自测 Chainlit web UI**（`http://127.0.0.1:8000`，`mj-agent serve`）——mj-agent 当前唯一活体 web UI（Studio :2024 是脆的第三方 SPA、已有手动 probe skill 覆盖；Phase-3 Next.js 前端未启动）。**trust_posture: third-party**（Microsoft `microsoft/playwright-mcp`；本仓 `first-party` 仅指 Anthropic 发布，serena/ssh-manager 为 third-party 先例），**credential_mode: none**（无 secret / 零 `.env` / 零 secrets-bundle 改动）。**改动**：(1) `.mcp.json` 追加 `playwright` 条目（第 14 个 server）；(2) `.claude/settings.json` `permissions.allow` 加 `mcp__playwright__*`；(3) **A14 治理仪式**——`mcp-server.contract.yml` `expected_total_entries` 13→14 + 新增 `servers:` 条目，capability SoT（spec/requirements/design/runbook/trace/tasks + governance/claude-skill contract）13→14 全量刷新，BDD 基线 13→14 且把 Scenario "Adding a 14th…" 改为计数无关的 "Adding a new MCP server…"（feature ↔ test `@scenario`/`re.escape` regex ↔ trace.yml 三处锁步），消除未来加 server 的 off-by-one 重触。**验证**：`tests/bdd` 9 passed / 7 skipped、G1/G2/G9 gates PASS、ruff clean、`npx @playwright/mcp@latest` 启动（v0.0.77）；host 侧 `npx playwright install chromium` 一次性装 Chromium（`@playwright/mcp` 默认引擎）。**范围外（deferred）**：Chainlit Web-自测约定（CLAUDE.md 指针 + in-tree skill，待 UI 功能迭代起步时补）；`.claude/settings.local.json` `enabledMcpjsonServers` 加 `playwright` 为 gitignored + per-worktree 的本地启用步骤（在实际运行 Claude Code 的 `develop/` 里做）。

### Fixed — `system.md` frontmatter `model_binding: deepseek-v3` 过期治理元数据（#286）

- **`src/mj_agent/prompts/system.md`（`docs`，branch `documentation/286-model-binding-provider-agnostic`）**：frontmatter `model_binding: deepseek-v3` 是 ADR-027 多 provider 化**之前**的单厂商绑定表述，已过期——运行时绑定现由 `LLM_PROVIDER` + `LLM_MODEL_ID` 决定（ark @ `deepseek-v3-2-251201` 或 local-openai-compat @ 任意 OpenAI-compat 端点，如 DGX `nemotron-3-super`）；#285 模型身份误报排障中曾被作为嫌疑源逐一排查、浪费排障时间（本 issue 从 #285 scope 拆出）。**改动**：(1) `model_binding` → `multi-provider (ADR-027; runtime binding via LLM_PROVIDER + LLM_MODEL_ID)`，`updated:` 同步 2026-07-07；(2) 同步 `capabilities/data-agent/llm-provider/contracts/prompt.contract.yml` `frontmatter_freeze.model_binding` 冻结镜像值；(3) 顺修 `capabilities/data-agent/safe-sql/design.md` touchpoint 注记里的次生 `deepseek-v3` 表述。**零运行时影响**：`load_prompt()` 剥离 frontmatter，该字段不进 LLM 上下文。**必停面例外登记（Owner 拍板）**：`system.md` 是 `prompt-version-or-body-change` ask-gated 必停面，`sdd/adapters/prompt.md`§`model_binding` 规则将其变更判为语义级→触发 `prompt-version-bump` 必停；但本次系**元数据订正**（反映 ADR-027 既有 provider-agnostic 现实，非 model 迁移——§规则的 silent-regression 理由不适用），**body 逐字不变 / `version: v1.8` 不变 / body `content_hash` frozen anchor `994d4a2d…` 不变**，故**不 bump version、不 re-freeze**。`check_prompt_contracts.py` 通过（content_hash 匹配、必填字段齐全）。Closes #286

### Added — `mj-agent check --live` 深探针层，消灭 check 假绿盲区（#290）

- **`src/mj_agent/server/cli.py` + 新 `src/mj_agent/runtime.py` + `src/mj_agent/ui.py`（`feat`，branch `feature/290-check-live-probes`）**：默认 `mj-agent check` 只做**凭据存在性** + 一次**同步** memory-DB ping，因此探不到三类真实故障——(1) **async 盲区**：从不走 Chainlit serve 依赖的 `AsyncConnectionPool` / `AsyncPostgresSaver.setup()` 异步路径（正是 #283 Windows `ProactorEventLoop` 不兼容能带病发布的原因，check 说 OK/serve 已坏）；(2) **biz 盲区**：只断言 `postgres_analyst_user` 非空，从不连 biz DB；(3) **LLM 盲区**：只断言凭据存在，从不调 LLM。兑现 #283 条目预登记的 "async 探针另行登记"。**改动**：(1) 新增 `mj-agent check --live` 开关，跑三个 **creds-gated** 深探针——`_probe_memory_async`（`open_checkpointer()` enter/exit，经 `run_async(asyncio.wait_for(..., 8s))` 跑；8s 上限因 #283 失败表现为 ~30s pool retry-timeout）、`_probe_biz_sync`（`readonly_cursor` → `SELECT 1`）、`_probe_llm_sync`（`make_llm().invoke("ping", max_tokens=1)`，只断言不抛，content 可空；tool-calling 深查仍归 `/mj-agent-infra-llm-endpoint-probe` skill）；每探针 PASS/**SKIP**（凭据缺，永不 FAIL/不影响 exit code）/**FAIL**（尝试失败→exit 1）+ summary tally，**三探针全 SKIP 时 stderr 明确告警**（防"跑了 --live 说 OK 实则零验证"的新假绿）。(2) 抽 `mj_agent.runtime`（`apply_event_loop_policy()` + `run_async()`）——把 #283 的 Windows 事件循环 guard 从 `ui.py` 私有函数提取为共享模块，`ui.py` import 期改调它（时序不变），CLI 深探针复用（不 import chainlit）。**默认 `mj-agent check` 与 Docker `HEALTHCHECK` 命令串/字段逐字不变**（保护 10s timeout + 不每 30s 烧 LLM token + 不触 docker healthcheck-字段必停）。**注**：首次 `check --live` 会对 fresh memory DB 建 checkpoint 表（幂等 DDL，同首次 serve）。**测试** +9 用例（`test_runtime_event_loop` guard + `run_async` 桥；`test_cli_check_live` 全-SKIP 契约 + 尝试-FAIL⇒exit1 + no-`--live` 不跑探针；`test_check_live_smoke` `-m smoke` 端到端），全经 sync `run_async` 桥测试 → 无需 async-test 基建；Windows 实机 `check --live` 三探针 PASS（async memory PASS = #283 CLI 级回归门）。附带**校准 4 处文档 over-claim**（Onboarding `db: ok` 从不输出、`config/README` "DB OK + Ark LLM OK"、`docker/README` + `Dockerfile` 注释 "探活 biz DB + Ark"——默认 check 从不连 biz/不调 LLM，改为区分默认 vs `--live`；Dockerfile 仅注释非 healthcheck 字段→不触必停）。**延后 follow-up**：biz/LLM 同步探针无紧连接上限（可选 `mj_system_db._dsn()` 加 `connect_timeout=5`，`db`-scope）；`check --live` LLM 探针可选 `ainvoke + wait_for` 硬 bound。Closes #290

### Fixed — Chainlit serve 下任何工具调用因 middleware 缺 async 实现永久卡死（#288）

- **`src/mj_agent/middleware/tool_errors.py` + `src/mj_agent/ui.py`（`fix`，branch `bugfix/288-async-tool-middleware`）**：ADR-029 工具错误中间件只以 sync `@wrap_tool_call` 形态注册；langchain 1.2.15 factory 把 override 任一侧 hook 的 middleware 同时纳入 sync/async 两条工具链，Chainlit/Studio 的 async 入口（`astream`/`ainvoke`）调到 base `awrap_tool_call` 直接 `NotImplementedError`——tools 节点炸图、前端空消息永久转圈（checkpointer 库 `checkpoint_writes.__error__` 通道留有原文证据）；async 变体 `ahandle_sql_tool_errors` 自 af0e81d 起是从未注册的死代码，且「装饰器按协程性自动派发」的原断言证伪（两个单侧实例并注册也会在对侧模式各自炸）。**修复**：(1) 重构为单 `SQLToolErrorMiddleware(AgentMiddleware)` 同时 override `wrap_tool_call` + `awrap_tool_call`，模块级单例 `handle_sql_tool_errors` 名称不变（`agent.py`/`__init__.py` 零改动）；`_convert` 与三个中文前缀常量逐字保留；(2) `ui.py` `on_message` 对 `astream` 加异常兜底写回前端消息（杜绝无声转圈），空回复 fallback `get_state` → `await aget_state`（AsyncPostgresSaver 同步调用在事件循环主线程必 raise）。**测试** +10 回归用例（wrap 层 sync/async 各 3 + 双 hook 注册 pin ×2 + graph 级 fake tool-calling model `ainvoke`/`invoke` E2E ×2，全仓首批 async 测试，无需 creds 进 CI default-selected）；同步 safe-sql capability（`python.contract.yml` exports/wiring、requirements/runbook/tasks/design/trace 闭原 TBD-M3 缺口）+ ADR-029 2026-07-07 amendment（更正错误机制断言，固化单类双 hook 不变式）。**延后 follow-up**：serve NO_PROXY / biz-lan 凭据既登记项不在本 PR。Closes #288

### Fixed — agent 自我误报模型为 deepseek-chat（模型身份泄漏 + 缺失）（#285）

- **`src/mj_agent/tools/analysis/token_estimator.py` + `src/mj_agent/agent.py`（`fix`，branch `bugfix/285-model-identity-leak`）**：`estimate_tokens` 签名默认值 `model_id="deepseek-chat"` 是 Ark 时代残留——工具为 plain callable，`create_agent` 把签名默认值编入 LLM tool schema，该字符串成为模型上下文中**唯一**具体模型名；DGX 部署（`local-openai-compat` @ `nemotron-3-super`）下用户问"当前使用的模型是什么"时 agent 自我误报 deepseek-chat（端到端复现，模型自证出处；裸模型直连正确自称 Nemotron，排除单纯幻觉）。**修复**：(1) 默认改 `model_id: str | None = None`，调用时解析 `settings.llm_model_id`（`or` 兜底 LLM 传 null/空串），docstring 去厂商模型名（docstring 即 LLM 所见工具描述）；(2) `_build_system_prompt()` 在 base identity 与 skill 块之间注入 `# Runtime` 段（provider + model id，~45 tokens），agent 可如实报告部署模型。评估并否决 `InjectedToolArg` 藏参数方案（引入 langchain_core 依赖破坏 analysis 模块 plain-callable 约定；settings 兜底后误传仅扰动 tokenizer 选择）。**测试** +5 回归用例（默认/None 解析到 settings、显式传参回显、Runtime 段存在 + `# Identity` 与首个 `# Skill:` 之间位置）；e2e 验证 DGX 隧道下回答 `nemotron-3-super`。**延后 follow-up**：#286（`prompts/system.md` frontmatter `model_binding: deepseek-v3` 过期治理元数据——`load_prompt()` 剥离 frontmatter 零运行时影响，provider-agnostic 化 + `prompt.contract.yml` frozen 值同步，必停面单独 PR）。Closes #285

### Fixed — Windows 本机 Chainlit serve 事件循环不兼容致 checkpointer 池超时（#283）

- **`src/mj_agent/ui.py`（`fix`，branch `bugfix/283-windows-selector-event-loop`）**：psycopg async 模式无法运行在 Windows 默认 `ProactorEventLoop` 上（psycopg 已知限制），`AsyncPostgresSaver` 的 `AsyncConnectionPool` 一条连接都建不起来（每次建连抛 `InterfaceError`），`on_chat_start` 30s 后 `PoolTimeout`，页面发消息无响应。**修复**：`ui.py` 模块导入期新增 `_apply_windows_event_loop_policy()` guard——`sys.platform == "win32"` 时切 `WindowsSelectorEventLoopPolicy`（chainlit 先 import 本模块、uvicorn 后建事件循环，故 import 期设置决定 loop 类型）；非 Windows no-op。Docker（Linux）路径不受影响。**测试** +3 回归用例（win32 导入副作用 / guard 本体 Proactor→Selector / 非 Windows no-op；policy 快照-恢复 fixture 防跨测试泄漏）；Windows 实机端到端验证：真实入口 serve → 浏览器会话建图 → DGX LLM 调用 200 OK。**延后 follow-up**：`mj-agent check` 用同步 psycopg 探不到该缺口（假绿盲区之一，async 探针另行登记）。Closes #283

### Fixed — L1 guardrail 引号标识符 allowlist 绕过（#280）

- **`src/mj_agent/tools/sql/guardrail.py`（`fix`，branch `bugfix/280-guardrail-quoted-ident`）**：L1 SQL guardrail 用正则（`_QUAL_REF`）抽取 `schema.table` 引用，无法匹配双引号标识符，故 `FROM "biz_ods"."t"` 绕过 schema/表 allowlist、仅靠 L4 DB GRANT 拦截（纵深防御缺口，非活体泄漏——只读 `analyst` 角色 GRANT 权威）。**修复**：正则抽取改为 sqlglot AST（`_qualified_refs`，遍历 `exp.Table`）——引号无关，且额外覆盖逗号 JOIN、UNION 腿、WHERE/CTE 子查询等正则从不可见的位置。sqlglot 解析失败（或病态嵌套 `RecursionError`）时 **fail-closed 拒绝**（而非退化到弱正则）——allowlist 是安全边界，无法静态背书的语句不放行（对比 L1b precheck 的*质量*规则 fail-open）；Owner 拍板 fail-closed（HITL，`sql-guardrail-relax` 必停面）。行为保持：既有 accept/reject 理由串逐字不变，`is_safe_select` 仍不抛（`RecursionError` 现已捕获）；代价=极少数 valid-but-unparseable PostgreSQL（jsonb `@?`、`ORDER BY … USING <`）在 L1 被拒并给清晰 “could not parse … simplify” 理由。**测试** +19 回归用例（引号/混合引号/大小写混合、`biz_ads`/`ops_meta`、UNION/逗号 JOIN/WHERE 子查询腿、引号禁库 dwd 表、字符串字面量伪引用、fail-closed 不可解析 + 病态嵌套）；3-agent 对抗性 review：33 禁库变体全拒、22 合法形态零误拒、无残留绕过。同步 safe-sql capability contracts + design（`sql-guardrail.contract.yml` / `execute-sql.contract.yml` / `design.md`）到 AST/fail-closed 机制 + 刷新行锚。**延后 follow-up**：behavior.feature 新增 allowlist-拒绝 scenario（单测已覆盖）；REQ-001 “L1 regex guardrail” 名 + behavior.feature/runbook.md “regex” 标签协调重命名；spec.yml “14 dangerous keywords” 既存漂移（应 16）；precheck.py `RecursionError` 捕获（现已被 L1 fail-closed 前置拦截，不可达）。Closes #280

### Changed — T-5 DGX 真实 e2e 采纳（ADR-027 active）

- **`decisions/ADR-027_LLM_Provider_Abstraction.md`（`docs`，branch `documentation/dgx-e2e-t5`）**：§Cross-ref 状态 `pending dgx-mlops Phase 2 integration` → `active`（2026-07-03 真实 e2e 跑通：`make_graph()` + metric 问题经 DGX vLLM `nemotron-3-super` 端到端，≥1 纯 + ≥1 tool-calling completion，dgx-mlops 侧 S1-S4 + S1a 断言全 PASS）；§Cross-ref 标题同批去 pending 字样（自洽）。
- **`decisions/ADR-033_DGX_Ops_Sister_Repo_Boundary.md`**：§Cross-ref 槽位状态同步 `active` + §跟踪锚点 T-2/T-5 行标 done（T-2 = 零 drift 核对 @ dgx-mlops `72933bb`，#255 comment）。
- **`capabilities/data-agent/llm-provider/evidence/runtime/2026-07-03_dgx_e2e.md`**：consumer 侧 e2e evidence（真实 runtime 路径 + tool-calling 捕获；SSH 隧道拓扑如实记录；burst 429 诚实 defer）。闭 dgx-mlops M7 Phase-2 出口①②③⑤ 的 mj-agent 半边（HITL-CROSS 双签，本 PR 先合取 hash）。配套 `plans/[PLAN]_255_dgx-e2e-t5.md` 落盘。Refs #255

### Changed — T-1 dgx-mlops cross-ref 采纳（ADR-027 + ADR-033）

- **`decisions/ADR-027_LLM_Provider_Abstraction.md`（`docs`，branch `documentation/dgx-cross-ref-t1`）**：增「Cross-ref — dgx-mlops provider contracts」段，绑定 `CTR-AGENTOUT-001` + `CTR-BRIDGE-001`（PRIMARY），状态 pending dgx-mlops Phase 2 integration。
- **`decisions/ADR-033_DGX_Ops_Sister_Repo_Boundary.md`**：「Cross-ref 槽位」由 pending 占位填实为实 ID 集合；闭 dgx-mlops M7 Phase-1 exit #3 的 mj-agent 半边（HITL-CROSS）。Refs #255

### Changed — HITL 机制改「AI 提议 → Owner 拍板 → AI 落盘」(ADR-034)

- **HITL 由「AI 出 diff 草案 → Owner 手动落盘」改为「AI 提议 + Owner 拍板 + AI 落盘」，彻底消灭手动转写（`maintain`，branch `maintain/hitl-deny-to-ask-model`，[[decisions/ADR-034_HITL_Propose_Decide_Apply_Model\|ADR-034]]，HITL 治理变更 + 放宽 4 必停物理门）**：**动机**：旧机制把"决策"与"逐字转写"都压在 Owner（runtime-* 标 read-only 让 Owner 拿 diff 自己 Edit；flow-plan/post-merge/review-respond 出草案让 Owner 手动 Write/paste；5 安全面 settings.json 物理 deny AI 完全不能写），toil 高。**改动**：(1) **kernel docs**：`sdd/workflows/execution-loop.md`（v1.2→v1.3）新增 §3.0 拍板执行模型 + §3.1 enforce 注 + §3.3 HITL 提问格式增 `Owner 执行步骤` 字段 + §4.2 Runtime 约束反转；`policies/ai-agent.md` §4 enforce 机制注 + 新增 §8 External-Info Handoff Discipline + §9 Protected-Path 拍板 + Merge-Review 兜底；`policies/data-boundary.md` §3 执行机制重写（**修文档漂移**：guard-git-workflow.ps1 仅 matcher=Bash 管 G1/G2，不拦 4 面 Edit/Write——真正的门是 settings.json `ask`）；`sdd/gates.md` §4 + G6 真值化为 ask-gated；`CLAUDE.md` 必停 surfaces 段同步。(2) **`.claude/settings.json` deny→ask**（Owner 手动应用——auto-mode classifier 硬拦 agent 自写权限放宽）：4 项 in-source 专属必停（`tools/sql/{guardrail,precheck}.py` / `prompts/system.md` / `skills/**/SKILL.md` / `biz_catalog/qcm_catalog.yaml`）从 `permissions.deny` 移到新 `permissions.ask`（precedence deny>ask>allow，逐写 prompt=拍板）；`.env`/`secrets*.enc`/`rm -rf` 保持 deny。(3) **14 个 skill body 重写**：4 `runtime-*`（skill-doc-improve / prompt-version-bump / biz-catalog-sync / eval-baseline）由 read-only 反转为 propose→拍板→apply（拍板后经 `ask` 门直接落盘；prompt-version-bump 的 ADR-000/006/009 sanity check 保留）；4 `flow-*`（plan 拍板后 AI Write、scope-drift 拍板后 amend、post-merge 拍板后 AI Edit frontmatter active→completed、review-respond 拍板后 AI 经 gh/mcp__github__ 自动发 GitHub 回复）；2 `doc-*`（author/sync 的 B 风味委派语言 propose diff→propose→拍板→apply）。**不动**：`flow-self-review`（不 auto-commit）/ `flow-verify`（不 auto-run Level C）/ `flow-intake`（仅评估）/ `doc-validate`（validator）——其「不 auto-X」指向仍保留的 commit/destructive/创建 gate；6 个 `infra-*` frozen skill（已是 External-Info concrete-steps 范式样板）；`tools/sql/{guardrail,precheck}.py` 逻辑本体；commit/push/PR/merge gate（Stage 12/13/14/16 照停）。(4) **决策口径**（owner 拍板）：Q1 全覆盖 deny→ask（安全面也 AI 落盘）；Q2 落盘 + GitHub 发帖（commit/push/PR/merge 仍 gate）；Q3 `.claude/settings.json` + `.mcp.json` 归同模型，A13/A14 合并审查兜底。**仅交互模式成立**——`auto`/`bypass` 模式下 `ask` 自动放行 + protected-path privilege-escalation 被 classifier 硬拦（harness 固定不可禁用），故放宽类改动须交互模式执行（本 PR 即在交互模式落地，settings.json 因 auto-classifier 由 Owner 手动应用）。supersede ADR-015 §决策点 4 runtime read-only 硬约束残留；数据边界（ADR-006/009/000）不变。配套 `decisions/INDEX.md`（+1 行 23 ADR）+ `docs/INDEX.md` ADR 表 +1 行。

### Added — ADR-033 DGX 运维姊妹仓边界决策（DGX 消费侧 PR-B）

- **新建 `decisions/ADR-033_DGX_Ops_Sister_Repo_Boundary.md`（`docs`，branch `documentation/adr-dgx-ops-sister-repo`；vault `[PLAN]_mj-agent_DGX_Consumer_Side_Execution.md` v1.1 §1 PR-B）**：固化 2026-06-11 dgx-mlops 治理批次（r1-r3）owner 决策——(1) DGX-Spark serving/ops 由独立姊妹仓 `MJ-AgentLab/dgx-mlops` 治理，mj-agent 仓不承载 DGX serving/ops 资产；(2) **mj-agent 是唯一 DGX consumer**，消费路径唯一经 ADR-027 provider 抽象（`LLM_PROVIDER=local-openai-compat` + `LLM_MODEL_ID` 覆写）；(3) DGX 不部署 mj-agent（重申 ADR-026 正文 2026-05-09 决策句），`Profile` enum 不扩 dgx；(4) 跨仓反耦合预算 cross-ref 总数 ≤5（**mj-agent 自设约束**，ADR 内显式标注）+ 不存 dgx-mlops secrets + 不替其执行 M/D-phase。含 cross-ref 槽位（dgx-mlops `capabilities/mj-agent/llm-provider-bridge/` contract ID，pending M2、T-1 填实）+ T-1/T-2/T-5 跟踪锚点表（防触发项只活在 vault 蒸发）。配套：`decisions/INDEX.md` +1 行（22 ADR）+ `docs/INDEX.md` ADR 表 +1 行；**CLAUDE.md 零新增行**（既有 "DGX is an LLM-endpoint switch, not a deploy target" 已覆盖）。验证：`check_frontmatter.py` / `check_wikilinks.py` clean；wikilink 解析手动核验（A4 未实装）；ADR-026/027/028 + archive ADR-025 引用按实文核对。out-of-scope：ADR-027 cross-ref 段（T-1 触发）；dgx-mlops 侧 stale "ADR-030" 引用修正（r4 联动，不在本仓）；T-3/T-4（跨仓 HITL / 运维动作无 PR 面）。

### Changed — LLM endpoint probe skill 增 Step 3b tool-calling smoke + 冻结刷新（DGX 消费侧 PR-A）

- **`.claude/skills/mj-agent-infra-llm-endpoint-probe/SKILL.md` 3-step → 4-step：新增 Step 3b "Tool-calling Smoke"（`docs`，branch `maintain/probe-skill-tool-calling`；vault `[PLAN]_mj-agent_DGX_Consumer_Side_Execution.md` v1.1 §1 PR-A；dgx-mlops 核查报告 v1.2 §8.2/§9.2.3 双向 tool-calling 覆盖的 mj-agent 侧半边）**：**问题**：mj-agent runtime 把 `ALL_TOOLS`（清单见 `src/mj_agent/tools/__init__.py`）全量绑定进 `create_agent`，tool-calling 是硬依赖；但现 probe 只测 1-token chat——模型/parser 不支持 tool-call 时探针假阳性（Step 3 过、runtime 实际不可用）。**改动**：(1) SKILL.md 新增 Step 3b：最小 tools 数组（单 function schema、≥1 required 参数、`max_tokens` 128、不带 `extra_body`），主路径默认 auto tool choice（贴 `create_agent` 生产路径）+ prompt 强引导 + 低 temperature，断言 `finish_reason=="tool_calls"` + 合法 `function.name` + 可解析 JSON `arguments`；判别重试：auto 无 tool_call 补发一次 named `tool_choice`（named/guided decoding 不依赖 `--enable-auto-tool-choice`）——auto败/named成 → "endpoint 未开 tool parser"、双败 → "模型不具备 tool-call 能力"（→ dgx-mlops HITL-MODEL 换型），两类均兼容性警告非硬失败；(2) frontmatter description 同步（"3-step" → "4-step" + 枚举增 (4) + tool parser flags 故障面；触发词不变；1991 chars ≥ 200 + "Do not use for:" 保留）；(3) Step 4 报告模板增 "Step 3b: Tool-calling" 段 + Verdict 增 "⚠ PASS with tool-calling warning" 降级判定；(4) §Troubleshooting +3 行（vLLM `--enable-auto-tool-choice --tool-call-parser <模型族>`——flag 拼写按 vLLM stable tool_calling 文档实证；3b 422 查 serving 参数；auto+named 双败换模型）；(5) Anti-patterns +2（3b 不带 `extra_body`、不超 1 次工具往返——探针不做 agent loop）；(6) Reference Files + `tools/__init__.py`（ALL_TOOLS 事实源）+ vLLM tool_calling 文档；Handoff + Step 3b warning 路由；Step 3 判定表 "✅ probe pass" → "→ Step 3b"。(7) **冻结刷新**：`capabilities/infrastructure/mcp-server-governance/contracts/claude-skill.contract.yml` 该条目 `description_hash` + `body_content_hash` **双字段**按 canonical algo（regex-strip frontmatter + LF-norm + sha256）重算 + `frozen_at` bump 2026-06-11 + 头部 re-freeze 记录；`body_section_heads` 核对零变化（Step 3b 为 "###" 级）。infra-freeze 必停面计划内 HITL（`mcp-server-trust-posture-change` + `declared-contract-change`；逐次用户授权落地）。(8) **5a stale-ref 同步**（"3-step/3 步" → "4-step/4 步"，living docs only）：`.claude/skills/SKILL_INDEX.md`（infra 行 + updated bump）+ `decisions/ADR-027`（D.4 步骤列表增 Step 3b 行注 2026-06-11 + Consequences/References 两处 + updated bump）+ `capabilities/data-agent/llm-provider/{design,runbook}.md`（各 2 处 + updated bump）；evidence/archive/历史 CHANGELOG·plans 为时点记录不动。**验证**：编辑前先在基线复现旧双 hash（重算方法实证）→ 编辑后重算即新记录值；`uv run python scripts/sdd/check_claude_skill_contracts.py --all` V4 clean（注意 V4 仅 Mode-A schema-lint **不校验 hash**，双 hash 一致性靠本地重算复现）；ruff + mypy + pytest 不受影响（无 src 改动）。out-of-scope：`mj-agent check` tool-calling 网络探测（vault 计划 §3 候选，待 T-4 演练暴露需求）；`tests/conftest.py` skip 键 provider-aware 化（§3）；PR-B ADR-033 分仓边界；T-1~T-5 触发项。

### Changed — Secrets bundle 拆分对齐 mj-system v2.3 范式 (ADR-030)

- **2-bundle secrets 拆分**：把 MCP 基础设施 secrets（5 SSH + 10 PG URL = 15 keys）从 `config/secrets.enc` 拆出到独立的 `config/secrets-mcp.enc`，解密后**直接写 OS User-level env**，永不入 `.env`。对齐 mj-system v2.3 `secrets-sys-ops.enc` 范式（`infra(infra)`，branch `maintain/secrets-bundle-split-for-mcp`，[[decisions/ADR-030_Secrets_Bundle_Split_For_MCP_Isolation\|ADR-030]]）。
  - **新增文件**：`config/secrets-mcp.example`（schema 15 keys）+ `config/secrets-mcp.enc`（加密包，team admin 跑 migrate 脚本生成）+ `.claude/scripts/setup-mcp-secrets.ps1`（解密 → HKCU\Environment）+ `scripts/encrypt-secrets-mcp.ps1`（生成 .enc）+ `scripts/migrate-secrets-bundle-split.ps1`（一次性迁移工具）+ `decisions/ADR-030_Secrets_Bundle_Split_For_MCP_Isolation.md`
  - **删除文件**：`.claude/scripts/setup-mcp-env.ps1`（旧路径 `.env → OS env mirror`，拆分后无事可做——`.mcp.json` 16 个 `${VAR}` 全是 secrets，14 个由新脚本覆盖，剩 1 个 `GITHUB_PERSONAL_ACCESS_TOKEN` 由外部 OS env 提供，不在 mj-agent 治理范围）
  - **修改文件**：`.env.example`（移除 §8 SSH + §9 PG URL；加 ADR-030 引用注释）+ `config/secrets.example`（移除 §5 SSH + §6 PG URL）+ `scripts/setup-env.ps1`（输出"Next step"指向 setup-mcp-secrets.ps1）+ `config/README.md`（重写 §6.4 反映新 2-bundle 模型 + 顶部分组介绍 + 文件清单）+ `docs/infrastructure/mcp/[STANDARD]_MJ_Agent_MCP_Server_Governance.md`（§3 credential mode wrapped script 行注 ADR-030；§5 inventory Independent secrets pipeline 段重写；§7 加 ADR-030 ref）+ `decisions/ADR-028_MCP_Server_Inventory_And_Governance.md`（§D.3 升级描述 + References 加 ADR-030）+ `CLAUDE.md`（§Environment variables 段重写为 2-bundle + Commands 提示新 setup 流程）+ `.claude/skills/mj-agent-infra-env-setup/SKILL.md`（description 含两个脚本；Overview 拆 2 步；Reference 加 setup-mcp-secrets.ps1 + ADR-030）+ `docs/INDEX.md`（ADR-030 行）+ `.github/PULL_REQUEST_TEMPLATE/maintain.md`（A14 行 `setup-mcp-env.ps1 → setup-mcp-secrets.ps1`）+ `src/mj_agent/env_drift.py`（docstring 说明 drift scope 仅 app keys；MCP keys 由 setup-mcp-secrets.ps1 -Reload 单独负责）+ `.gitignore`（加 `config/secrets-mcp.conf`）
  - **业务零影响**：业务代码不读 MCP secrets（`grep MJ_AGENT_SSH_ src/ tests/` → 0；`grep MJ_AGENT_PG_.*_URL src/ tests/` → 0）；pydantic-settings / docker compose / Python runtime 路径完全不变。
  - **迁移**：team admin 跑 `.\scripts\migrate-secrets-bundle-split.ps1` 一次性拆分 + 重加密；commit 两份新 `.enc`；团队成员 pull 后跑 `setup-env.ps1` + `setup-mcp-secrets.ps1`。两 bundle 共享团队口令（不为口令隔离，仅为信任边界 + 注入路径隔离）。
  - **依据**：mj-system v2.3 `[SPEC]_SYS_Secrets_Encryption_And_Setup_Automation.md` + `setup-sys-ops-env.ps1`。

### Changed — biz_dws fact 表 SQL 必填时间谓词 + 默认窗口策略 (#156)

- **`src/mj_agent/prompts/system.md` (v1.7 → v1.8) + `src/mj_agent/skills/safe-sql-analysis/SKILL.md` (v0.1 → v0.2) 强制 LLM 在第一轮 SQL 就带时间谓词，并在用户未指定窗口时自动选合理默认 + 在回复里说明所选窗口（`feat`，branch `feature/prompt-time-predicate-prevention`，PR [#156](https://github.com/MJ-AgentLab/mj-agent/pull/156)，HITL §3.1 必停 10+11 触发）**：**问题**：PR [#154](https://github.com/MJ-AgentLab/mj-agent/pull/154) 已经把 SQL 工具的 `require_time_range` ValueError 转成 ToolMessage 让 LLM 自纠正，**但每次第一轮无时间谓词 SQL 仍是浪费一个 tool round-trip**（用户体感：top-N 类问题 "查 top 10 产品成交量" 没说窗口时，LLM 第一轮生成无 WHERE 子句的 fact-table SELECT，被 precheck 拒，第二轮才补 `data_date >= ...`）。**改动**：(1) `prompts/system.md` 新增 **Hard rule #9** "Time predicate is mandatory for `biz_dws` fact tables"：定义 `biz_dws.dws_qcm_*` fact 表 (除 3 signal 表) 必带 WHERE 时间列谓词；用户没指定窗口 → 默认 daily=30d / monthly=3m / quarterly=4q / yearly=3y 并在回复里说明所选窗口；明确 Top-N 明细查询同样需要时间谓词（precheck 与 LIMIT 无关）；version `v1.7 → v1.8` bump 触发 §3.1 必停 11。(2) `safe-sql-analysis/SKILL.md` Planning workflow 自检清单重排：时间谓词从第 3 项提到第 1 项 + 加 `【最关键 — precheck 必查】` callout + 复述默认窗口规则 + cross-ref system.md Hard rule #9。新增 **Common pattern D「Top-N 用户没说窗口」** 示例 SQL 演示如何应用默认窗口策略（pcat_l1 + SUM(day_qrynum) + `WHERE data_date >= CURRENT_DATE - INTERVAL '30 days'`）；version `v0.1 → v0.2` bump 触发 §3.1 必停 10。**与 PR #154 的关系**：双保险路径——prompt 侧 (本 PR) 让 LLM 第一轮就命中正确 SQL 形态；middleware 安全网 (#154) 仍负责 precheck 真的拒绝时 graceful 降级。**§4.15 Rule 11**：post-merge 将自动开 `[EVAL backlog] system.md+safe-sql-analysis @ <commit>` issue（A8/A11 transitional waiver 沿用；`eval_references: []` 保留 TODO；Phase D EVAL framework 落地时跟进 baseline）。验证：`scripts/check_frontmatter.py` ✅ 96 canonical docs；`scripts/check_wikilinks.py` ✅ 0 violations；`uv run ruff check` ✅；`uv run mypy src/mj_agent` ✅ 44 files；`uv run pytest tests/unit tests/eval` ✅ **270 passed**（含 `test_prompts_loader` ×4——loader 走 frontmatter strip 契约，version v1.7 → v1.8 不破坏 body 加载）。out-of-scope：`skills/qcm-analysis/SKILL.md` 与 `query-writing/SKILL.md`（已有 template 自带时间谓词，无观测缺陷）；`tools/sql/precheck.py`（rule 行为不动，本 PR 只改 prompt 让 LLM 第一轮命中）；EVAL dataset (Phase 2/D 工作)；默认窗口可配置化（保持 prompt 硬编码以简化 LLM 决策路径；单独 PR 处理）。

### Fixed — SQL 工具异常转 ToolMessage 防止 Chainlit 前端 hang (#154)

- **`src/mj_agent/middleware/tool_errors.py` 用 LangChain 1.x `@wrap_tool_call` 把 SQL 工具链 `ValueError`/`RuntimeError` 转为 `ToolMessage`，修掉 2026-05-12 frontend hang 根因（`fix(agent)`，branch `bugfix/sql-tool-error-middleware`，PR [#154](https://github.com/MJ-AgentLab/mj-agent/pull/154)，ADR-029）**：**问题**：用户在 Chainlit (http://localhost:8001) 提问"查 dws_qcm_qrynum_daily_total top 10"无回应；容器 healthy 但 graph 永远不出 reply。**根因**：`src/mj_agent/tools/sql/execute.py:99` 当 LLM 生成不含时间谓词的 biz_dws fact 表查询时抛 `ValueError("SQL rejected by precheck: require_time_range: ...")`；`agent.py:84` 调 `create_agent(model, tools, system_prompt)` **未传 `middleware` 参数**，LangGraph 1.1.8 / LangChain 1.2.15 的 `ToolNode` 默认 `_default_handle_tool_errors` 直接 re-raise，graph step 报错既不产生 `ToolMessage` 也不写 checkpointer，Chainlit `astream` 永远等不到下一条消息。`mj-agent check` 报 healthy 是因为它只验 DB + LLM creds + drift，不实际跑 graph。**改动**：(1) 新建 `src/mj_agent/middleware/{__init__.py, tool_errors.py}` —— sync `handle_sql_tool_errors` + async `ahandle_sql_tool_errors` + `_convert` helper；`@wrap_tool_call` runtime-introspects `iscoroutinefunction` 把 sync/async 分别装到 `wrap_tool_call`/`awrap_tool_call` 方法上；中文错误前缀（`工具调用未通过校验：` for ValueError / `工具执行失败：` for RuntimeError + 重试提示），`tool_call_id` 从 `request.tool_call["id"]` 透传；防御性兜底捕获 TypeError/KeyError 等意外异常。(2) `src/mj_agent/agent.py` —— `make_graph()` kwargs 加 `middleware=[handle_sql_tool_errors]`（+2 行：import + kwarg）。(3) `tests/unit/test_tool_error_middleware.py` —— 6 个 case（ValueError×2 precheck/guardrail + RuntimeError×2 timeout/db + 防御兜底 TypeError/KeyError×2）锚定 `_convert` 契约；用 `_StubRequest` dataclass 替代真 `ToolCallRequest` 避免 langgraph 内部耦合。(4) 新增 `decisions/ADR-029_Tool_Error_Surfacing_To_LLM.md` —— 决策 + 3 个候选方案（修改 execute_sql 直接返回错误信封 / 子类化 ToolNode 走 `handle_tool_errors=True` / 包装每个 tool 注册）及不采纳理由；cross-ref ADR-006 / ADR-002。(5) `CLAUDE.md` —— Architecture 段加 Middleware 行 + 装配描述改写 + ADR enumeration 段加 ADR-029 注释。(6) `docs/INDEX.md` —— ADR 表加 ADR-029 行（A5 sync）。**工具函数本身保留 raise 行为**——保留 `tests/smoke/test_agent_smoke.py:126-153` 的 `pytest.raises(ValueError, ...)` 契约；middleware 只拦截 agent graph 内 ToolNode 这一层。验证：`uv run ruff check` clean；`uv run mypy src/mj_agent` 44 files 0 issues；`uv run pytest tests/unit tests/eval` **270 passed** (baseline 264 + 6 new)；`scripts/check_frontmatter.py` 96 docs OK；`scripts/check_wikilinks.py` 0 violations；live container E2E proof（重新 build mj-agent image + `docker exec mj-agent python -c "execute_sql(bad_sql) → ValueError → _convert(req, e) → ToolMessage"` 全链路通），3 容器全 healthy 无 traceback。out-of-scope：教 LLM "先加时间谓词再 SELECT" 的 prompt-side prevention（middleware 是 load-bearing 安全网，可在 follow-up 加 prompt 强化）；其它 `tools/sql/introspect.py` allowlist 拒绝（middleware 已覆盖 ValueError 通用面，无需逐 site 改）；`CLAUDE.md` Commands 段 docker compose `--env-file .env` 缺失的文档 gap（本次排查时另行发现，独立 follow-up）；Windows host curl 502 proxy 问题（已有 `docs/runbook/proxy_*` runbook 覆盖，红 herring，与本 bug 无关）。

### Added — `mj-agent check` 增 `.env.example` → `.env` template drift detection (#110)

- **`mj-agent check` 现在跑 `.env.example` → `.env` drift 检测，覆盖跳过 `setup-env.ps1` 的场景（`feat`，branch `feature/env-drift-detection-and-test-isolation`，PR [#110](https://github.com/MJ-AgentLab/mj-agent/pull/110)）**：commit c91ed81（rename memory pg role `mj_agent_memory` → `mj_agent_app`）+ 17fcc47（在 `setup-env.ps1` 加 drift 检测）的 follow-up。**问题**：drift 检测只在 `setup-env.ps1` 里跑，已有 `.env` 跳过 Step 2 的开发者永远看不到 `[DRIFT]` 警告 —— 用户跑 `/mj-agent-infra-env-setup` 时 `mj-agent check` 在 `.env` 含 18 key 漂移（c91ed81 rename + ADR-025 PR-2/3 新 keys 未跟）情况下安静失败在 memory DB 认证。**改动**：(1) 新建 `src/mj_agent/env_drift.py` —— Python 侧独立实现 drift 算法（与 PowerShell 完全一致：行解析、首个 `=` 拆 key、求差集；文件缺失返回 `[]` 保持 CI 兼容）；(2) `src/mj_agent/server/cli.py` —— `mj-agent check` 在 failures 输出前打 `[DRIFT] / [MISSING]` 块（warn-only，不影响 exit code；走 stderr；与 PowerShell 文案完全 mirror）；(3) `tests/unit/test_env_drift.py` 6 case 锚定算法行为（同步 / 缺 / 多 / 注释 / 含 `=` 值 / 文件缺失）；(4) `CLAUDE.md` "Environment variables" 段补 1 段说明；(5) `.claude/skills/mj-agent-infra-env-setup/SKILL.md` Step 5 注释 `[DRIFT]` 块含义。验证：ruff + mypy clean；pytest 264 passed (+7：6 drift + 1 isolation regression)；live `mj-agent check` 在用户当前 `.env`（缺 18 keys）下显示完整 `[DRIFT]` 块 + 格式与 `setup-env.ps1` 一致；CI `ci` + `check-stale-docs` SUCCESS。out-of-scope：用户本地 `.env` / pg role 修复（手动；PR body 含 A/B 选项）+ `.env.example` MJ_AGENT_MEMORY_PORT 5432/5433 注释强化（plan polish #1，本次 follow-up PR 顺手做）。

### Fixed — 3 个 Settings()-using unit test 不再受本地 `.env` 污染 (#110)

- **`tests/unit/test_phase1_skeleton.py` 3 处 test isolation 修复（`test`，同 PR [#110](https://github.com/MJ-AgentLab/mj-agent/pull/110)）**：`test_cli_check_reports_missing_env` 之前在本地有 `.env` 时 fail（CI 因为没 `.env` 一直绿，掩盖问题）；`test_settings_default_memory_db_name` / `test_settings_default_chainlit_bind` 是同类 latent bug（靠 `.env` 值碰巧等于默认才没炸；上游一旦改 default 就显式失败但根因不明显）。**根因**：`monkeypatch.delenv()` 只清 `os.environ`；pydantic-settings 在 `Settings()` 实例化时仍从磁盘 re-read `.env`。**修法**：3 处改 `Settings(_env_file=None)`（pydantic-settings 原生支持的"本次实例化禁用 .env"语义；2.14.0 验证可用）+ 新增回归 test `test_settings_env_file_none_isolates_from_dotenv` 主动 assert `Settings()` 读 `.env` / `Settings(_env_file=None)` 不读，守住契约（防 pydantic-settings 升级把这条语义破坏）。

### Fixed — `/doctor` MCP env warnings 9/9 via setup-mcp-env.ps1 (4 WAN MCP servers functional capability deferred) + skill listing truncation

- **Fix `/doctor` 9 个 MCP env warnings + skill listing 截断（`infra`，branch `maintain/fix-doctor-mcp-env-warnings`；4 WAN MCP server 实际可连能力 deferred to follow-up）**：ADR-025 PR-3 落地的 `.mcp.json` 在 13 servers 中引入 9 个 `${MJ_AGENT_*}` 变量替换占位（5 SSH passwords + 4 WAN postgres URLs），但 Claude Code 启动时**不会**自动加载 `.env`，导致 `/doctor` 报 `[Warning] Missing environment variables` 且 ssh-manager + 4 WAN postgres MCP servers 拉不起来。本 PR 引入 mj-ops 风格 OS-level env sync 机制，**消除全部 9 个 /doctor warnings**（claude /doctor 的 missing 检查仅判 var 是否存在于 env，不判 value 是否非空；4 WAN URLs 在 `secrets.conf` §6 字面值为空，OS env 写入空字符串后 var 仍"存在"，所以 /doctor 不报）。但 **4 个 WAN MCP servers 实际仍不能连**（postgres client 拿空 URL 会 connection failure；非 /doctor 级问题），delegated to follow-up issue 跟踪填实值与 FRP 路由。落地：(1) 新建 `.claude/scripts/setup-mcp-env.ps1`（~180 行；mirror mj-system `setup-sys-ops-env.ps1` L74-97 helpers + L119-149 `-Reload` 模式架构；改造为读已解密的 `.env` 而非平行加密管道，以**复用现有 `secrets.enc → setup-env.ps1 → .env` 单一管道**），用 `[Environment]::SetEnvironmentVariable($k, $v, "User")` 把 `.mcp.json` `${VAR}` 引用 auto-derive（`Read-McpVarRefs` regex `\$\{([A-Z_][A-Z0-9_]*)(?::-[^}]*)?\}` 抽 16 个 ref）的子集 mirror 到 `HKCU\Environment`；提供 `-Reload` 诊断模式（不写入；mask-value 输出 SET/MISSING）+ `-Force` 跳过覆盖确认；(2) `CLAUDE.md` env 段尾加 5 行指向新脚本 + 安全代价 brief；(3) `config/README.md` §6.4 全段重写：工作流 + 用法 + 验证 V1-V4 矩阵 + 安全代价（HKCU 明文 / 跨进程可见 / 跨 worktree 共享）+ 与 mj-system mj-ops 差异表（secret 源 + 是否写 .env + Expected 列表来源）；(4) `.claude/settings.json` `skillListingBudgetFraction: 0.03 → 0.04` 修 skill listing 截断（实际 3.1% 击穿 3% budget；多 6k tokens/session 换 mj-agent-code-doc-author description 不被 drop）。**安全代价已用户确认接受**：HKCU\Environment 明文持久化 + 跨进程可见 + 跨 worktree 共享 OS env。换取「任何 shell（PS / cmd / Git Bash）/ IDE / VS Code 启动 claude 都自动可见」，无 wrapper / alias / profile entry。验证（用户手动）：V1 `setup-mcp-env.ps1 -Reload` 首次见 `1/16 set, 15 missing`（GITHUB_PERSONAL_ACCESS_TOKEN 已 from 历史 OS env）→ V2 `setup-mcp-env.ps1` 写 15 个到 User env（GITHUB_PAT absent in .env，预期）→ V3 `-Reload` 见 `16/16 set` → V4 **关键：完全关闭 PS terminal 开新 PS**（Windows User-level env vars 仅对新启动进程可见，同一终端 claude 子进程继承 stale env），或在当前 PS 跑 `foreach($k in (Get-Item HKCU:\Environment).Property){ [Environment]::SetEnvironmentVariable($k, [Environment]::GetEnvironmentVariable($k, 'User'), 'Process') }` 不重启而 hot-reload User → Process → V5 新（或刷新过的）terminal 跑 claude `/doctor` 应见 **0 个 `Missing environment variables`**（4 WAN URLs 虽空但 var key 存在 → /doctor 不报；实际连 WAN pg 仍会失败，per follow-up issue）。out-of-scope：4 WAN MCP server 实际可连能力（follow-up issue；需 FRP 路由配置 + 真实远程 pg 凭据填入 secrets.conf §6）+ 自动注入 OS env（手动跑该脚本是设计意图）+ secret rotation 自动化（`.env` 每次 `setup-env.ps1` 重写后需重跑该脚本）+ Profile/IDE 启动 claude 配置（个人 dev environment 范畴；OS-level 持久化后所有入口都自动可见，本来也不需要改）。

### Added — PR-4 of multi-env+DGX+MCP bundle (env-teardown skill + ADR-025 + CLAUDE.md sync) — bundle 收尾

- **PR-4 — env-teardown skill + ADR-025 + CLAUDE.md sync（`docs`，issue [#104](https://github.com/MJ-AgentLab/mj-agent/issues/104)；plan `[PLAN]_multi_env_dgx_mcp_bundle.md`）**：bundle 收尾 PR — 落地 4 项：(1) **新建 `mj-agent-infra-env-teardown` SKILL** — 镜像 mj-system 的 `mj-sys-ops-env-teardown` 3-level 模式（`down` / `down -v` / `down -v --rmi local --remove-orphans`）；适配 mj-agent 3 服务栈 (mj-agent / mj-agent-postgres / mj-agent-redis) + 4-file profile 分层；profile-aware Step 0（必须与 up 用相同 -f 链）；H3 hard-confirm Level 2/3（明示丢失项：langgraph checkpointer history + redis appendonly）；description ≥ 200 chars 含 `Do not use for:` 反向触发（A12 PR gate）；(2) **新建 ADR-025 `Multi_Environment_And_LLM_Provider_Abstraction`** — 跨多 domain 决策统一记录（compose 4-file 分层 + LLM provider 抽象 + .mcp.json governance + DGX 算力消费侧设计；用户 5 项决策；4 PR 序列；不 supersede；track: shared；ref ADR-008/006/009/013/016/018/022/024 + Meta v2.2）；(3) **CLAUDE.md 同步** — §Architecture 加 4-file compose 列表 + §Commands 替换为 3 profile 命令 + §LLM provider 重写为 dual provider 矩阵 + §Environment variables 加 LLM_PROVIDER / MJ_AGENT_SSH_* / MJ_AGENT_PG_*_URL 段 + §Documentation ADR summary block 加 ADR-025 段（与 ADR-017..024 块格式对齐）+ §A14 行修订（STANDARD 引用路径 `docs/rule/...` → `docs/infrastructure/mcp/...`，去 "(Phase C+)" 占位，A14 PR gate 正式生效）+ §Active in-tree skills 表 infra family 加 2 行（`mj-agent-infra-llm-endpoint-probe` PR-2 + `mj-agent-infra-env-teardown` PR-4）；(4) **`config/README.md` §6** Multi-environment + multi-LLM-provider 段（LLM provider 分支 secret 必填 / SSH passwords 独立命名空间 / .mcp.json postgres URL overrides）；(5) **`.claude/skills/mj-agent-infra-storage-stack/SKILL.md`** 加 profile 注解（storage 操作与 profile 无关）+ DGX troubleshooting 行（DGX 不部署 mj-agent，引导去 llm-endpoint-probe）。**PR-4 收尾**（compose layering ✅ #99 → LLM provider abstraction ✅ #101 → .mcp.json governance ✅ #103 → ADR-025 + doc sync 本 PR）；merge 后 mj-agent-flow-post-merge Step 9 自动标 `plans/[PLAN]_multi_env_dgx_mcp_bundle.md` `state: completed`。验证：`scripts/check_frontmatter.py` all pass（含新 ADR-025 + env-teardown SKILL）；`scripts/check_wikilinks.py` 0 violations；`scripts/find_stale_docs.py` no rename/move/delete；ruff + mypy clean；pytest 163 pass + 1 pre-existing fail（同前 3 PR baseline，与 PR-4 无关）。out-of-scope：物理归档 `plans/archive/` per ADR-021 + ADR-023（6 月阈值未到）；LLM serving 容器部署（用户决策；另议）；Profile enum 加 dgx（用户决策；DGX 不部署 mj-agent）；mj-system 同名 STANDARD 派生（mj-agent 原生 ADR-025；informant：mj-system 未来可派生）。**累计 4 PR / 1 ADR / 1 STANDARD / 2 新 SKILL / 4 compose 文件 / 13 MCP servers / 完整 CLAUDE.md sync**。

### Added — PR-3 of multi-env+DGX+MCP bundle (.mcp.json + STANDARD MCP_Server_Governance)

- **PR-3 — .mcp.json + MCP Server Governance（`feat(infra)`，issue [#102](https://github.com/MJ-AgentLab/mj-agent/issues/102)；plan `[PLAN]_multi_env_dgx_mcp_bundle.md`）**：建立 mj-agent 自有的 `.mcp.json`（13 servers，对标 mj-system `.mcp.json` 模式但用独立 secrets 命名空间 per ADR-008），并落地领域专属 STANDARD `docs/infrastructure/mcp/[STANDARD]_MJ_Agent_MCP_Server_Governance.md`（per ADR-022 C.3.2 + Meta v2.2 §3.7；无 `_v1.0` 后缀 per ADR-018），填补 CLAUDE.md §A14 dangling reference。落地：(1) **`.mcp.json` 13 servers** — `github` (first-party) + `serena` (third-party oraios) + `pg-mj-agent-memory-{dev,test-lan,test-wan,prod-lan,prod-wan}` × 5（mj-agent-memory langgraph checkpointer DB；wrapped script 修 timestamp 转 UTC bug）+ `pg-mj-system-biz-{dev,test-lan,test-wan,prod-lan,prod-wan}` × 5（mj-system biz pg via analyst RO；ADR-006/009 数据边界 DB-side GRANT 兜底）+ `ssh-manager` (third-party `@iflow-mcp`；9 SSH entries: cloud + 4 hosts × 2 lan/wan，含 DGX-Spark 192.168.0.189)；省略 `n8n-docs`（mj-agent 无 n8n）；(2) **`.claude/scripts/pg-server-{start.cmd,wrapper.mjs}`** verbatim 从 mj-system 复制（`@modelcontextprotocol/server-postgres` 启动 wrapper + npx cache 修复 + `pg.types.setTypeParser(1114/1184, val => val)` 修 timestamp UTC 转换 bug；A14 trust posture 在 PR body 声明）；(3) **`docs/infrastructure/mcp/[STANDARD]_MJ_Agent_MCP_Server_Governance.md`** v1.0：§1 scope §2 trust posture 3 等级 §3 credential mode 5 类矩阵 §4 PR-body 强制声明模板（A14 实施细则）§5 13-server inventory 完整分类 §6 季度 audit cadence §7 cross-ref ADR-008/013/014/016/018/022 + Meta v2.2；track: engineering-workflow；(4) **`docs/infrastructure/mcp/INDEX.md`** 与 git/cicd 子目录 INDEX 平行结构；(5) `.env.example` §8 (5 个 `MJ_AGENT_SSH_SERVER_*_PASSWORD` placeholder) + §9 (10 个 `MJ_AGENT_PG_*_URL` 可选 override placeholder)；(6) `config/secrets.example` §2b (LLM_API_KEY 可选) + §5 (5 SSH 密码) + §6 (10 PG URL) 同步。**PR-3 of 4 sequential PRs**（compose layering ✅ #99 → LLM provider abstraction ✅ #101 → .mcp.json governance → ADR-025 + doc sync）。验证：`.mcp.json` JSON lint pass（13 servers 列出正确）；`scripts/check_frontmatter.py` 81 docs all pass（含新建 STANDARD + INDEX）；`scripts/check_wikilinks.py` 0 violations；`scripts/find_stale_docs.py` no rename/move/delete；ruff + mypy clean；pytest 163 pass + 1 pre-existing fail（同前 2 PR baseline，与 PR-3 无关）。out-of-scope：ADR-025 起草 + CLAUDE.md A14 行 STANDARD 引用路径调整 + §Documentation ADR summary block 加 ADR-025 段（PR-4）；env-teardown skill（PR-4）；实际 secrets.enc 注入团队真实凭证（user 用 setup-env.ps1 解密；本 PR 仅改 .env.example/secrets.example placeholder）。

### Added — PR-2 of multi-env+DGX+MCP bundle (LLM provider abstraction)

- **PR-2 — LLM provider abstraction（`feat(llm)`，issue [#100](https://github.com/MJ-AgentLab/mj-agent/issues/100)；plan `[PLAN]_multi_env_dgx_mcp_bundle.md`）**：把 `src/mj_agent/llm.py` 从单一 Volcengine Ark 路径扩展为多 provider factory，让 mj-agent 可在 `.env` 切 `LLM_PROVIDER=ark|local-openai-compat`，分别走 Ark Chat Completions（DeepSeek V3）或任何 OpenAI-compatible 本地 endpoint（DGX-Spark vLLM/SGLang/Ollama/TGI/llama.cpp；deployment 责任另议，mj-agent 仅消费侧）。落地：(1) `src/mj_agent/config.py` 加 `llm_provider: Literal["ark","local-openai-compat"] = "ark"` + `llm_base_url: str = ""` + `llm_api_key: SecretStr` 字段 + `effective_llm_base_url` / `effective_llm_api_key` cached_property（ark provider fallback 至 `ark_*` 字段，向后兼容；local-openai-compat key 缺省 `EMPTY` sentinel 防 ChatOpenAI 抛 `OpenAIError: api_key client option must be set`）；(2) `src/mj_agent/llm.py` `make_llm()` factory 分支：ark 路径保留 `extra_body.thinking` + back-compat `api_key=ark_api_key SecretStr`；local-openai-compat 路径用 `ChatOpenAI(base_url, api_key, ...)` **不带 `extra_body`**（vLLM/SGLang/Ollama 不接受 Ark DeepSeek 私有参数，传入会 422）；(3) `src/mj_agent/server/cli.py` `mj-agent check` provider-aware：ark 模式查 `ARK_API_KEY` / local-openai-compat 模式查 `LLM_BASE_URL`，OK 输出新增 `llm provider = <name> (endpoint=<url>)` 行；(4) `.env.example` §2 重写：`LLM_PROVIDER` + `LLM_BASE_URL` + `LLM_API_KEY` 通用字段 + `ARK_*` 保留向后兼容；(5) 新建 `.claude/skills/mj-agent-infra-llm-endpoint-probe/SKILL.md`：DGX vLLM healthcheck 3 步（reachable + model id match + 1-token chat smoke；Ollama `/api/tags` fallback；description ~3000 chars 含 `Do not use for:` 反向触发）；(6) `.claude/skills/mj-agent-infra-env-setup/SKILL.md` Step 3 加 LLM provider 分支检查 + cross-link endpoint-probe；(7) `.claude/skills/mj-agent-infra-studio-probe/SKILL.md` Step 0 加 endpoint-probe pre-check（仅 local-openai-compat）。**PR-2 of 4 sequential PRs**（compose layering ✅ #99 → LLM provider abstraction → .mcp.json governance → ADR-025 + doc sync）。验证：3 smoke 全 pass（ark 路径含 `extra_body.thinking` / local 路径不含 / 缺 `LLM_BASE_URL` 抛 `LLMConfigError` fail-fast）；ruff + mypy clean；pytest 163 pass + 1 pre-existing fail（`test_cli_check_reports_missing_env`，PR-1 merge 前后均 fail，与 PR-2 无关）；既有 `"ARK_API_KEY not set"` test 子串保留通过（保 back-compat）。out-of-scope：`.mcp.json` 创建（PR-3）；ADR-025 起草 + CLAUDE.md 全量同步（PR-4）；Profile enum 加 dgx（用户决策；DGX 不部署 mj-agent，无 profile 概念）；LLM serving 容器部署（用户决策；另议）。

### Added — PR-1 of multi-env+DGX+MCP bundle (4-file docker-compose layering)

- **PR-1 — Multi-env docker-compose layering（`feat(infra)`，issue [#98](https://github.com/MJ-AgentLab/mj-agent/issues/98)；plan `[PLAN]_multi_env_dgx_mcp_bundle.md`）**：refactor `infra/docker/docker-compose.mj-agent.yml` 为 env-agnostic base + 新建 `infra/docker/docker-compose.{override,test,prod}.yml`，对标 mj-system v3.2.2 4-file 模式落 dev/test/prod 三 profile。落地：(1) base：`name: mj-agent`、env vars `${VAR:-default}`、universal env (`MJ_AGENT_MEMORY_HOST` / `MJ_AGENT_REDIS_HOST` / `CHAINLIT_HOST=0.0.0.0`)、networks + volumes；移除硬编码 `POSTGRES_DEV_HOST: mj-postgres` 与 `com.mj-agent.environment: "development"` 转入 override.yml；(2) DEV override：`build:` 本地 Dockerfile + `MJ_CONFIG_PROFILE=dev` + `POSTGRES_DEV_HOST=mj-postgres` + `MJ_AGENT_LOG_LEVEL=debug` + 3 服务 `com.mj-agent.environment: "development"` label；(3) TEST overlay：`image: 8.135.38.175/mj-agent/mj-agent:0.1` Harbor pull + `MJ_CONFIG_PROFILE=test` + `POSTGRES_TEST_HOST=mj-postgres` + 资源限制 mj-agent 8C/12G + mj-agent-postgres 4C/8G；(4) PROD overlay：Harbor pull + `MJ_CONFIG_PROFILE=prod` + `POSTGRES_PROD_HOST=mj-postgres` + 4C/12G + json-file logging（`max-size: 50m max-file: 5`）+ `MJ_DEBUG=false` + `MJ_AGENT_LOG_LEVEL=warning`；(5) 重要 quirk：dev 也用显式 `-f base -f override`（auto-load 仅在 cwd default 模式触发；本仓 compose 在 `infra/docker/` 子目录 + `-f` 显式 base 时不生效）；(6) `infra/docker/README.md` 加 §Compose 4-file profile 分层（Profile Matrix + DGX 算力消费侧注解 + Pre-flight）+ Quick start 4 profile 命令；(7) `mj-agent-infra-docker-compose` SKILL.md description 1746 chars + Profile Matrix + 4 profile 命令 + troubleshooting 3 新条目（Harbor pull denied / dev profile env 没生效 / TEST/PROD 同主机 prereq）。**PR-1 of 4 sequential PRs**（multi-env compose → LLM provider abstraction → .mcp.json governance → ADR-025 + doc sync）。验证：3 profile `docker compose config` 全 lint pass；dev 显式 `-f override` 合并配置注入 `POSTGRES_DEV_HOST: mj-postgres` 等正确；ruff + mypy clean；pytest 163 pass + 1 pre-existing failure（test_cli_check_reports_missing_env，develop 同样 fail；与 PR-1 无关）。out-of-scope：LLM provider 抽象（PR-2）、`.mcp.json` 创建（PR-3）、ADR-025 起草 + CLAUDE.md 全量同步（PR-4）、DGX-specific compose（用户决策；Phase 1 仅做配置抽象）。

### Changed — Phase D-3 (ADR-024 + Agent_Side v1.1→v1.2 archive ceremony + §4 EVAL spec) — Phase D 收尾

- **PR Phase-D-3 — EVAL framework spec + Agent_Side v1.2（`docs(rule)`，issue [#95](https://github.com/MJ-AgentLab/mj-agent/issues/95)；主体 PR #96 + sync 完成 PR #97）**：(1) 新建 ADR-024（EVAL framework spec；不 supersede；mj-agent 原生）；(2) Agent_Side v1.1 → v1.2 archive ceremony：v1.1 archive 至 \`[DEPRECATED]_..._v1.1.md\`（state: deprecated；archived: 2026-05-09；replaced-by stable path；\`[!warning]\` banner）；v1.2 在原 stable path（per ADR-018；filename 不变；version: v1.2）；(3) §4 EVAL Authoring 完整规范（从 4 行占位升级为 ~150 行规范 §4.1-§4.7：4 子类 outcome/trajectory/component/integration + body 八段 + frontmatter schema + A8/A11 waiver roadmap）；(4) check_frontmatter.py 加 EVAL type-conditional（state: active 强制 eval_kind/dataset_path/baseline_metric/baseline_value/regression_threshold）；(5) A8/A11 transitional waiver 延续 Phase E（spec 落地；runtime 推迟；前置条件 4 项 roadmap）；(6) docs/INDEX.md（Agent_Side v1.2 + ADR-024 row）+ CLAUDE.md（Versioning rule 段加 ADR-024 mention）+ 本 CHANGELOG sync。**Phase D 收尾**（D-1 templates + D-2 scripts/infra + D-3 EVAL spec）；**累计：mj-agent 文档治理 P0/P1/P2/P3 全项落地（10 PRs / 9 ADRs： ADR-017 → ADR-024）**。out-of-scope（Phase E）：实际 EVAL runtime 实现 / 落首批 EVAL 文档 / 关闭 A8/A11 waiver / TEMPLATE_EVAL.md align。**Note**：主体 PR #96 sync edits 5 项因 worktree-specific Read-tracking 失败漏；本 hotfix #97 完成 sync。

### Changed — Phase D-2 (ADR-023 + scripts/infra: find_stale_docs + plan GC + Meta §5.11.5)

- **PR Phase-D-2 — scripts/infra 增强（`refactor(scripts)`，issue [#92](https://github.com/MJ-AgentLab/mj-agent/issues/92)）**：(1) 新建 ADR-023（不 supersede；与 ADR-020/021 互补；落实 ADR-020 §Alternatives B + ADR-021 §Consequences follow-up）；(2) 新建 \`scripts/find_stale_docs.py\`（mj-system v5.2 §7.1.1 派生；path-level rename detection；warning 模式；JSON output stderr）；(3) 新建 \`.github/workflows/check-stale-docs.yml\`（PR-time CI；4 周观察期；不阻塞合并）；(4) 新建 \`scripts/find_old_completed_plans.py\`（ADR-021 follow-up；扫 plans/ \`state: completed\` AND \`updated\` ≥ 180 天的 GC 候选；不实跑）；(5) Meta v2.2 §5.11.5 加 archived 物理归档实施指引段（操作流程 + 当前状态 2026-05-09 mj-agent 最早 completed < 1 月，6 月阈值未到）；(6) docs/INDEX.md / CLAUDE.md / 本 CHANGELOG sync。Phase D 子包 2/3；out-of-scope：实际首次 GC（2026-11+）+ symbol-level rename detection（Phase E+ 候选）+ warning → blocking 升级（4 周观察后评估）+ EVAL framework（Phase D-3）。

### Changed — Phase D-1 (3 templates 占位转 active + RUNBOOK last-verified)

- **PR Phase-D-1 — POSTMORTEM/ISSUE/ASSESSMENT 模板补齐 + RUNBOOK last-verified（`docs(template)`，issue [#90](https://github.com/MJ-AgentLab/mj-agent/issues/90)）**：3 个模板（POSTMORTEM / ISSUE / ASSESSMENT）从占位 "(Phase D PR-D1)" 转 active；body 段落已存在（200-300 行 each）；本 PR 主要做 frontmatter 字段名对齐 ADR-022 C.3.1（POSTMORTEM `incident-date`/`resolved-at`；ISSUE `risk-level` — 下划线改短横线）+ 默认值填合理（severity: P2 / risk-level: Medium）。同期 TEMPLATE_RUNBOOK 加 `last-verified` 字段（ADR-022 C.3.1）。docs/INDEX.md Templates 表 4 entries 同步更新（移除 PR-D1 占位标记 + 注 ADR-022 C.3.1 frontmatter）。Phase D 子包 1/3；不引入新 ADR（实施 ADR-022 工作）；out-of-scope：Phase D-2 archived 物理归档 + find_stale_docs.py / Phase D-3 EVAL framework。

### Changed — Phase C-4 (ADR-022 + 5 P2 framework enhancements bundle)

- **PR Phase-C-4 — P2 framework enhancements bundle（`docs(rule)`，issue [#88](https://github.com/MJ-AgentLab/mj-agent/issues/88)）**：按 mj-system v5.2 §3.6/§4.1/§4.4 派生，5 项 P2 framework rule 增强一个 PR bundle 落地。落地：(1) 新建 ADR-022（不 supersede；与 ADR-011/017-021 全部 sustained 互补）；(2) **C.3.1 类型专属 frontmatter**（4 类 8 字段）：Code_Side v1.1 §3.4 加 RUNBOOK \`last-verified\` / §3.5 加 POSTMORTEM \`severity\`+\`incident-date\`+\`resolved-at\` / §3.7 加 ISSUE \`priority\`+\`risk-level\` / §3.8 加 ASSESSMENT \`dimensions\`+\`period\`；\`scripts/check_frontmatter.py\` type-conditional 校验（state: active/completed 时强制；draft/deprecated 宽松）；(3) **C.3.2 STANDARD §3.7 placement 决策矩阵**：Meta v2.2 §3.7 加全局 \`docs/rule/\` vs API 专属 \`docs/api/\` vs 领域专属 \`docs/infrastructure/<domain>/\` 判定；(4) **C.3.3 ISSUE NNN+DomainAbbr 命名**：Meta v2.2 §4.5 加 \`[ISSUE]_NNN_DomainAbbr_Description.md\` 格式；(5) **C.3.4 supersedes list 文档化**：Meta v2.2 §4.6 加 list 语义说明（mj-agent 已是 list；本 PR 仅文档化）；(6) **C.3.6 STANDARD §3.8 拆分阈值**：Meta v2.2 §3.8 加 >500 行 + ≥5 主题 + ≥10 引用 三条件；(7) 2 RUNBOOK 文件回填 \`last-verified\` 字段（dev_deployment / dev_studio_walkthrough）；(8) docs/INDEX.md / CLAUDE.md / 本 CHANGELOG sync。**Phase C-4 收尾**（mj-system v5.2 §3.6 + §4.1 + §4.4 + §4.5 + §10 派生完成；累计 6 ADR / 7 PR / 全 P0/P1/P2 项目落地）。out-of-scope：Phase D 范畴（archived 物理归档 / find_stale_docs.py 完整版 / EVAL framework / 模板补全实测）。

### Changed — Phase C-3-3 (ADR-021 + working doc 4 态机；3-PR Phase C-3 收尾)

- **PR Phase-C-3-3 — Working doc 4 态机（`docs(rule)`，issue [#86](https://github.com/MJ-AgentLab/mj-agent/issues/86)）**：按 mj-system v5.2 §10.5 派生，引入 plans/ 工作文档 4 态机（draft → active → completed → archived）。落地：(1) 新建 ADR-021（不 supersede 任何 ADR；与 ADR-011/017/018/019/020 互补）；(2) Meta v2.2 §5.11（in-place 加段；§5.9 反例 #5 字段补充；不触发 archive ceremony）；(3) `mj-agent-flow-post-merge` SKILL Step 9 cross-ref 从 "Meta v2.0 §10.5"（forward-ref）改 "Meta v2.2 §5.11"（实落）；(4) retroactive 标 7 plans state: completed（5 PLAN_doc_governance_* + PLAN_F + PLAN_G）；(5) docs/INDEX.md ADR 表加 ADR-021；CLAUDE.md "Versioning rule" 段加 ADR-021 mention。`archived` 物理归档延 Phase D。**Phase C-3 P1 三联包收尾**（C-3-1 ADR-020 + C-3-2 banner + C-3-3 ADR-021 共完成 mj-system v5.2 §4.1/§7.1.1/§10.1/§10.2/§10.5 派生）。

### Changed — Phase C-3-2 (archive banner 标准化)

- **PR Phase-C-3-2 — 5 旧 archive banner 格式统一（`docs(rule)`，issue [#84](https://github.com/MJ-AgentLab/mj-agent/issues/84)）**：把 5 个旧 archived 文件的 body 顶部 banner 统一为 mj-system §10.2 step 4 风格（`> [!warning]` callout + archived 日期 + stable path 链接 + ADR cross-refs + cite-by-vintage 语义）。涉：v1.0/v1.1 Documentation_Management_Framework + v2.0 Meta_Framework + v1.0 Code_Side / Agent_Side trio。banner 风格之前参差（v1.0 大写 `[!WARNING]` / v1.1 简短 `**DEPRECATED**` / v2.0 trio 普通 `> **归档状态...**` 块），不一致。本 PR 全部统一。注：v2.1 archive 在 Phase C-1a 已规范，不在本 PR 范围。Phase C-3 P1 三联包子包 2/3；不引入新 ADR（C.3.5 是规范化执行；ADR-019 §Decision 隐含规则）。

### Changed — Phase C-3-1 (ADR-020 + check_wikilinks.py auto-discovery)

- **PR Phase-C-3-1 — check_wikilinks.py 通用化（`refactor(scripts)`，issue [#82](https://github.com/MJ-AgentLab/mj-agent/issues/82)）**：把 `scripts/check_wikilinks.py` 从硬编码 NEEDLES（6 模式 tuple）改为 auto-discover from `docs/archive/rule/[DEPRECATED]_*.md` glob。落地：(1) 新建 ADR-020（不 supersede ADR-019；仅落实 §References 标记的 Phase C-3 follow-up）；(2) `discover_needles()` 函数 — sorted glob 派生 NEEDLES + ARCHIVE_PREFIXES；(3) docs/INDEX.md ADR 表加 ADR-020；(4) CLAUDE.md "Versioning rule" 段加 ADR-020 mention。零维护：未来新加 archive 自动纳入校验。验证 OK 0 violations。Phase C-3 P1 三联包子包 1/3；out-of-scope：mj-system find_stale_docs.py 完整版（warning-mode CI + path-level rename detection）— Phase D 范畴。

### Changed — Phase C-1b (ADR-019 + Archive [DEPRECATED]_ prefix + frontmatter archived/replaced-by) — 3-PR 序列收尾

- **PR Phase-C-1b — archive 命名规范化（`docs(rule)`，issue [#80](https://github.com/MJ-AgentLab/mj-agent/issues/80)）**：按 mj-system v5.2 §10.2 派生，引入 archive 命名规范化（archive 文件名加 `[DEPRECATED]_` 前缀 + frontmatter 必含 `archived: <date>` + `replaced-by: <stable-path>` 直指当前活跃稳定路径）。落地：(1) 新建 ADR-019（partial supersede ADR-011 §5.6.2 第 2 段；ADR-011 §5.6.1/3/4 sustained）；(2) 6 archived 文件 rename 加 `[DEPRECATED]_` 前缀（git mv 保留 history；rule application 解读，不触发 archive ceremony 套娃）；(3) 6 archived 文件 frontmatter 加 `archived: 2026-05-09` + `replaced-by: ../../rule/<stable-path>`（直接指当前 active，不指 legacy chain；mj-system §10.2 line 653 模式）；(4) ~37 cascading FROZEN refs bulk perl replace（`archive/rule/[STANDARD]_..._v*` → `archive/rule/[DEPRECATED]_[STANDARD]_..._v*`）；(5) `scripts/check_wikilinks.py` NEEDLES + ARCHIVE_PREFIXES 同步加 `[DEPRECATED]_` 前缀；(6) docs/INDEX.md / CLAUDE.md / 本 CHANGELOG sync。**3-PR 序列收尾**（Phase C-2 ADR-017 + Phase C-1a ADR-018 + Phase C-1b ADR-019 三 ADR 共同完成 mj-system v5.2 §4.1 + §10.1 + §10.2 派生）。out-of-scope：Phase C-3+ scripts 通用化（auto-discover archive）。

### Changed — Phase C-1a (ADR-018 + Active Path Stability + 6 STANDARDs rename + PR_TEMPLATE drift fix)

- **PR Phase-C-1a — active 路径稳定化（`docs(rule)`，issue [#78](https://github.com/MJ-AgentLab/mj-agent/issues/78)）**：按 mj-system v5.2 §4.1 + changelog 2026-05-05 派生，引入 active canonical 路径稳定原则（active 文件名默认无 `_vX.Y` 后缀；版本仅在 frontmatter）。落地：(1) 新建 ADR-018（partial supersede ADR-011 §4.2 + §5.6.2）；(2) Meta v2.1 → v2.2 archive ceremony（双重触发：rule introduction + filename rename；§5.9 trigger #4 + substantive 演进）；(3) 5 其他 STANDARDs in-place rename（rule application 解读，非 §5.9 #4 改名；ADR-018 §Decision 子条款）— Code_Side / Agent_Side / HITL_Prompt / Commit_Message / GitHub_Markdown；(4) 7 PR_TEMPLATE drift fix（Phase B 漏改）；(5) scripts/check_wikilinks.py NEEDLE → NEEDLES list（6 模式；C-3 通用化推迟）；(6) ~500 ref audit（CLAUDE.md / docs/** / .claude/skills/** / src/mj_agent/{skills,prompts}/__init__.py / 7 PR_TEMPLATEs / etc.）。3-PR 序列第 2 步（C → A → B）；out-of-scope：Phase C-1b（archive `[DEPRECATED]_` 前缀 + frontmatter；ADR-019）。

### Added — Phase C-2 (ADR-017 + Meta v2.1 §5.9 archive trigger quantification)

- **PR Phase-C-2 — 引入 4 类必触发 + 1 类反例归档量化判定（`docs(rule)`，issue [#76](https://github.com/MJ-AgentLab/mj-agent/issues/76)）**：新建 `docs/adr/[ADR]_017_Archive_Trigger_Quantification.md`（state: active；decision: accepted；track: shared）记录决策与 mj-system v5.2 §10.1 派生论证；Meta v2.1 §5 加 §5.9（in-place edit，无 version bump）落 4+1 触发表 + cross-ref ADR-017；docs/INDEX.md ADR 表收录 ADR-017；CLAUDE.md "## Documentation" 元规则段加 ADR-017 mention。本 PR 自洽 dogfood：所做改动（in-place 加新段）属 §5.9 反例 ❌（字段补充），不触发 archive ceremony。3-PR 序列第 1 步（C → A → B）；不 supersede ADR-011 §5.6.1（仅细化）；out-of-scope：active 路径稳定化（PR-2 Phase C-1a，ADR-018）+ archive 命名（PR-3 Phase C-1b，ADR-019）。

### Added — Plan G Phase 0.5 governance / onboarding skeleton

- **PR1 TEMPLATE_GUIDE + Code_Side §3.1 codify（`docs(infra)`，08b7cea）**：`docs/_templates/TEMPLATE_GUIDE.md` 新增（mirror 4 reference GUIDE 的 CN-numbered 形态：TL;DR / Prerequisites / 目录 / §0 适用场景 / §1..§N / 关联文档 / 更新记录）；Code_Side `[STANDARD]_*Code_Side*_v1.0.md` §3.1 GUIDE Authoring 段从 Phase 1 占位翻为详规（§3.1.1 frontmatter + §3.1.2 body 骨架 + §3.1.3 复用原则 + §3.1.4 实例参考）；CLAUDE.md Templates 行加 `TEMPLATE_GUIDE`；docs/INDEX.md Templates 表加 TEMPLATE_GUIDE 行；STANDARD `version` 不升（ADR-011：填占位非结构性）。
- **PR2 Developer Onboarding GUIDE（`docs(infra)`，c6e5c7a）**：`docs/guide/[GUIDE]_Developer_Onboarding.md` v0.1 新增（mj-agent 新成员 Day-1 与长假回归者端到端上手路径：§1 仓库与远端 → §2 工作目录与分支 → §3 本地环境 → §4 测试运行 → §5 双轨道文档 → §6 提交推送 → §7 Studio 首跑 → §8 速查表）；`docs/guide/INDEX.md` 新增；Push_Workflow §0:84 / §6 冲突解决段 / §文末延伸阅读 三处 forward-ref 升级为 active wikilink；docs/INDEX.md 加「上手指南 (docs/guide/)」节；CLAUDE.md §Documentation 元规则段加 onboarding 入口。
- **PR3 Release Process RUNBOOK + cicd/INDEX（`docs(infra)`，f1e6d58）**：`docs/infrastructure/cicd/INDEX.md` 新增；`docs/infrastructure/cicd/[RUNBOOK]_Release_Process.md` v0.1 新增（Phase 0.5 Minimal 起步版：Trigger / Pre-checks / 7-Step 主流程 / Rollback / Post-mortem trigger；Steps 1-6 当前可执行——CHANGELOG cut → version bump → infra(release) commit → annotated tag → 双推 origin+gitee → GitHub Release；Step 7 deploy/CD 留 Phase 1 stub）；docs/INDEX.md 基础设施表加 cicd/ 行。
- **PR4 CHANGELOG §2/§10 状态翻转 + audit（本 PR）**：Push_Workflow §2 删除 "Phase 0.5+ 目标态" IMPORTANT 段头与 5 处「Phase 0.5+ 启用后」限定语；§2 流程从前瞻 stub 翻转为 active；§10 加 2026-05-06 行；CHANGELOG `[Unreleased]` 补 Plan G PR1-PR4 4 条 entry。

### Changed — Plan C C2 closeout (ADR roster alignment)

- **CLAUDE.md + docs/INDEX.md ADR 表对齐实际**：`docs/adr/` 实际有 11 条 ADR（000/001/002/003/006/008/009/010/011/012/013），但 CLAUDE.md "Repo conventions, code-side" 段只列到 011，docs/INDEX.md ADR 表也只到 011。本次同步 + 补 012/013 两行（state: draft，decision: accepted）。
- Plan C C2 "ADR backfill" 至此完成：原 plan §4.2 决策矩阵的三选一（mirror / reference / stub）均不适用——mj-agent-design 仓库无 `adr/` 子目录，mj-agent 已是单一权威源。Plan C 整体（C1 已在 PR4 stack 完成 + C2 本 PR）可在 vault 标 `已执行`。

### Added — MVP (data-agent-mvp PR1-PR4, branched off develop@9f0cdfe)

- **PR1 — biz 域语义上下文层（`feat(agent)`，6a0206c）**：新增 `src/mj_agent/biz_catalog/` 包（`qcm_catalog.yaml` 静态镜像 mj-system `[STANDARD]_Biz_DWS_Naming_Stability.md` §2-§4 + `loader.py` + `finder.py`）；新增 LLM 工具 `find_biz_context(question)` 一次性回吐候选 metric / period / dimension / 时间列 / 同环比列 / 信号表 / 维表 join key；表级 allowlist 收紧——`BIZ_ALLOWED_DWD_TABLES=dwd_dim_product_interface,dwd_dim_institution`，guardrail/`introspect`/`execute_sql` 全部走 `settings.is_table_allowed`；prompt v1.0→v1.1 + skill v0.1→v0.2 钉死工具调用顺序 `find_biz_context → list_biz_tables → describe_biz_table → execute_sql`；新增 `pyyaml` 运行时依赖与 `types-PyYAML` 开发依赖；新增 27 单元测试。
- **PR2 — sqlglot AST 预校验 + execute_sql envelope 扩展（`feat(sql)`，16ab5f9）**：新增 `src/mj_agent/tools/sql/precheck.py`（与 `[PROMPT]_component_judge.md` 的 P0/P1 规则**共用规则源**：`no_select_star`、`require_time_range` on biz_dws fact tables、`require_limit` 非聚合明细、`limit_too_large > 1000`，parse 失败优雅降级到 DB 校验）；`execute_sql` envelope 扩展为 `executed_sql / columns / rows / row_count / truncated / statement_timeout_hit / business_summary / precheck_warnings`；显式捕获 `psycopg.errors.QueryCanceled` 并重抛友好错误（提示加聚合 / 缩时间 / 减 JOIN）；新增 `sqlglot>=25.0` 运行时依赖；prompt v1.1→v1.2 文档新 envelope 与 AST precheck；新增 13 单元测试。
- **PR3 — query-writing 拆 3 skill（`feat(skill)`，806db05）**：`src/mj_agent/skills/{biz-domain-context,qcm-analysis,safe-sql-analysis}/SKILL.md` 各自 v0.1 active；MVP 阶段静态全载（`agent.py:_ACTIVE_SKILLS` 元组），dynamic skill selector 推迟到 1.5；老 `query-writing` 标 `state: deprecated` + `deprecated_in_favor_of`，文件保留作历史参考但 agent 不再加载；`qcm-analysis` 的 curated NL→SQL examples 来源指向 `golden_seed.jsonl` 的 reference_sql 字段；新增 6 单元测试（active skill 加载 + 系统提示拼装）。
- **PR4 — Evals + Studio runbook（`feat(eval)`，d1e5cbc）**：`tests/eval/golden_seed.jsonl`（15 case，从 vault 复制入库）+ `test_golden_seed_schema.py`（结构 / id 唯一 / 难度分布 / 查询 vs 澄清拆分）+ `test_component_against_seed.py`（precheck 跑遍 reference_sql，与 PR2 规则源共享）；smoke 扩展 #2-#4（`describe_biz_table` / `find_biz_context→execute_sql` Top-N / 拒绝 `biz_ods` 请求）；GUIDE §6.1 6 条 psql 案例镜像为 smoke 直接 `execute_sql`（合并 Plan C 的 C1）；`docs/runbook/dev_studio_walkthrough.md` 引用 Plan A 的 H1/H2/H3/R1/R2 evidence（不重写）；`plans/[PLAN]_mj-agent-data-agent-mvp-framework.md` v2 入库；新增 47 单元 + eval 测试，6 smoke 测试（marker gated）。

> 累计：162 unit/eval 测试 ✅，ruff + mypy strict ✅，6 smoke 测试 marker gated 等待 DB+LLM 凭据。

### Added — MVP 端到端验证后的修订（DEV profile 实测后落地）

- **Catalog 漂移修正（`fix(agent)`，593b803）**：端到端验证发现 staged STANDARD 草案与实际 DEV DB schema 显著漂移——时间列 `stat_date / stat_week / stat_month / stat_quarter / stat_year` 实际为 `data_date / week / month / quarter / year`；metric 列 `qrynum / tntcnt` 在 daily 周期实为 `<period>_<metric>`（如 `day_qrynum`）、weekly+ 实为 `<period>_<metric>_sum + daily_<metric>_avg/max/min/std/q25/median/q75` 分位数族；`biz_dwd.dwd_dim_institution` join key 实为 `tenant_id` 而非 STANDARD §4 的 `tenant_code`。`biz_catalog/qcm_catalog.yaml` v0.1.0→v0.2.0：mirror 实际 DB；`source.status: drift_detected` + `drift_notes`；新增 `metric_column_shapes` 块说明各周期 metric 列形状。3 个 SKILL.md 全部重写 SQL 示例；prompt v1.1→v1.2 文档漂移；7 个测试文件断言更新到实际列名；`tests/integration/test_mj_system_db.py` 第二个用例补时间谓词；smoke GUIDE §6.1 case 1 用 `data_date` 替代 `stat_date`。新增运行时依赖 `socksio>=1.0` 修 SOCKS proxy 环境；`tests/conftest.py` 模块导入时 `load_dotenv()` 让 skip-gates 看到 `.env` 凭据。
- **Plan A walkthrough evidence 回填（`docs(runbook)`，ffad3b5）**：新增 `scripts/capture_walkthrough_evidence.py` 5-case 捕获脚本（H1/H2/H3 happy path + R1/R2 red line 各跑一次）；`docs/runbook/walkthrough_evidence.md` 入库实测快照；`docs/runbook/dev_studio_walkthrough.md` §4 表格从 reference 升级为 inline 预期 vs 实际并列。首次跑捕获到两个软拒绝问题：R1 silent substitute、R2 4-call gradual degradation；安全合规口径未被穿透，但 prompt 应硬化（即下一条）。
- **Prompt v1.3 hard refusal + clarifying turn（`feat(prompt)`，0f99672）**：system.md hard rule 2 显式要求"碰到 `biz_ods` / `biz_ads` / `ops_*` 时首句声明边界 + 引用 ADR-006/008 + 提供 DWS 替代"；hard rule 3 显式要求"无界请求必须先反询时间窗 / 聚合 / Top-N，禁止任何探索性 `execute_sql`"。重跑 capture 实测：R1 60s/3-call silent → 48s/3-call explicit-boundary（"根据数据治理策略，`biz_ods.ods_query_volume_daily` 原始数据层对分析师角色不可访问"）；R2 53s/4-call gradual → **10s/0-call clarifying turn**（直接列时间窗 / 聚合 / 数据量控制 3 选 1）。

> MVP 验证后累计：167 unit/eval/integration 测试 ✅（5 条 live DB integration 实跑），ruff + mypy strict ✅，6+4 = 10 条 smoke 全过（GUIDE §6.1 6 条镜像 + agent trajectory 4 条 H1-H3+R1）。

### Added — earlier Phase 0
- **Phase 0 Foundation 垂直切片**：最小可跑通的 agent 骨架 —— LangChain 1.2.* + LangGraph 1.1.8；`langchain.agents.create_agent` 驱动；`src/mj_agent/{agent,config,llm,state}.py` + `integrations/mj_system_db.py` + `tools/sql/{guardrail,execute,introspect}.py` + `prompts/system.md` + `skills/query-writing/SKILL.md`；`langgraph.json` 指向 `make_graph` 工厂供 LangGraph Studio 使用
- **Volcengine Ark + DeepSeek V3 作为唯一 LLM provider**：`src/mj_agent/llm.py:make_llm` 构造 `ChatOpenAI`（OpenAI 兼容端点），环境变量 `ARK_API_KEY` / `ARK_BASE_URL` / `LLM_MODEL_ID` / `LLM_THINKING_ENABLED` / `LLM_TIMEOUT_SEC`；缺 key 时 `LLMConfigError` fail-fast
- **biz 域只读访问与四层防护（ADR-006）**：连接层 `default_transaction_read_only=on` + 角色层 analyst GRANT（DB 侧兜底，mj-system `R__analyst_permissions.sql`）+ 应用 guardrail（单语句 SELECT / 关键字黑名单 / schema allowlist `biz_dws,biz_dwd`）+ skill 语义层（`mj-ddd-semantics` 待 PR3 补齐，当前由 `query-writing` 承载基本规则）
- **`.env.example` 对齐 mj-system**：`##### N. Title #####` 分节风格、`POSTGRES_{DEV,TEST,PROD}_HOST/PORT` + `POSTGRES_ANALYST_USER/PASSWORD` 变量命名；`POSTGRES_USER/PASSWORD` 保留为空并注明"mj-agent 运行时不使用，勿填 admin 凭据"
- **测试脚手架**：`tests/unit/`（21 cases，guardrail + prompt loader）+ `tests/integration/test_mj_system_db.py`（live biz 域，`live_db` fixture 按 `POSTGRES_ANALYST_USER` 存在性 skip）+ `tests/smoke/test_agent_smoke.py`（end-to-end，按 `ARK_API_KEY` 存在性 skip）；pytest marker `smoke` 默认不跑
- **依赖锁定与复现**：`pyproject.toml` pin `langchain==1.2.*` / `langgraph==1.1.8` / `langchain-openai>=1.0,<2`；`uv.lock` 入库
- **开发者文档**：`README.md` 重写（Quick start + LLM provider + 测试矩阵 + 数据边界摘要 + Phase 0 结构图）、`CLAUDE.md` 升级为 Phase 0 架构说明、`plans/[PLAN]_Phase0_LangGraph_Studio_Walkthrough.md` 新增 run-book 风格 Studio 端到端手册（前置 / 步骤 / happy-path+red-line case / 9 项故障矩阵 / 完成标志）
- **`.gitignore` 对齐 mj-system**：分节风格 + `.claude/settings.local.json` 窄忽略保留 marketplace 配置 + mj-agent 独有节（pytest/mypy/ruff 缓存、LangGraph Studio `.langgraph_api/`）
- **Phase 0 setup-env 加密注入工具链（PLAN D）**：`scripts/setup-env.ps1` + `scripts/encrypt-secrets.ps1`（OpenSSL AES-256-CBC + PBKDF2，复用 mj-system 已上线骨架）+ `config/{secrets.example,README.md,secrets.enc}` 4-key schema（`POSTGRES_ANALYST_{USER,PASSWORD}` + `ARK_API_KEY` + `LANGSMITH_API_KEY`）+ `README.md` Quick start §2 切到脚本注入；与 mj-system 独立口令（ADR-006 数据边界精神）；§端到端验证 §1-§6 + §8 通过
- **`.env.example` 转 ASCII**：解决 python-dotenv 在 langgraph_api 内部 `DotEnv()` 不传 encoding 时，中文 Windows GBK 撞 UTF-8 字节导致 `uv run langgraph dev` `UnicodeDecodeError` 启动失败；所有中文注释翻成英文，`##### N. Title #####` 章节风格 / 变量名 / 默认值 / 章节顺序 0 改动

### Removed
- 删除 `main.py` Hello World 占位（由 `langgraph dev` 启动入口取代）
