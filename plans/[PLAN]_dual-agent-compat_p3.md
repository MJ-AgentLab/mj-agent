---
type: plan
summary: dual-agent-compat v5 P3 执行计划——第二批四 flow skills（scope-drift/self-review/review-respond/post-merge）收口 + S6 双工具 clean-clone 实跑（report-schema-exact，复用 P2 harness）+ 剩余 A/B/C 映射确认，达成 §11.1 P3→P4 观察期门；1 码 PR（#337 `maintain/337-p3-second-batch`）+ 1 flip PR；总锚 #312
owner: ranzuozhou
created: 2026-07-15
updated: 2026-07-15
state: active
track: shared
---

# [PLAN] 双工具兼容 v5 — P3 切片（issue #337）

## 1 Linked Artifacts

- Issue: #337（AC1–AC6）；总锚 #312 P3 项
- Intake: [[[INTAKE]_dual-agent-compat_p3]]（3 项 Stage 0 拍板）
- Program plan: [[[PLAN]_dual-agent-compat]] §11 P3 / §11.1 P3→P4 / §12 S6 行（fixture 面逐字 SoT）
- 前序：P2 #333（closed，S1–S5 20/20），develop @ `4ebd92e`；P2 证据 `evidence/development-agent-p2/SUMMARY.md`

## 2 Context

P0/P1/S0/S1/S2/P2 已闭环。P2 以 S1–S5 双工具各连续 2×（20/20 PASS）达成 P2→P3 晋级门；
harness（`fixture_runner.py` + `fixture_comparators.py` + fixtures S1–S6）骨架引入于 #334，
comparators + S1–S5 fixtures 精化定稿于 `b1973a9`（#333 evidence，经 #335 merge `3797e38`）并自此
字节冻结（`git diff b1973a9 4ebd92e -- scripts/sdd/fixture_*.py tests/fixtures/development-agent/** = 空`）。
四 P3 capability 的 support_mode 现状均非 unsupported（全 `claude:native` +
`codex:adapter-backed` + `projection:after-neutralization`），`evidence` 仅指各自 SKILL.md。
S6 fixture（`report-schema-exact`，stage_path=[17]→flow-post-merge）在 P2 只经 `-k S6` 单测通道
建齐 schema，**双工具实跑留 P3**。

P3 按结果验收（D-001）：**复用 P2 harness 不重写**；以 S6 双跑证明两工具在同一 Stage-17 任务输入下
产出结构一致的 post-merge 干跑报告；四技能收口 = manifest `evidence` 指针 + 诚实覆盖论证；
剩余 A/B/C = 确认 manifest 三档分类已是 P3 终态映射。Stage 3 repo-scan 确认基线全绿 + harness P3-ready +
A/B/C 三档已吻合 §4.4。

## 3 Scope

- 包含：见 issue #337 In-scope（S6 双跑证据 + 四技能 manifest evidence + 剩余 A/B/C 确认 + 晋级门证据 + flip）
- 不包含：全 S1–S6 重采（Owner 拍板 2：S6-new + 引用冻结 P2 S1–S5）；harness/fixture 改写（除非 §12 逼出→同 PR + 自动转全量重采）；P4 blocking flip（观察期未满）；S3 完整收口；投影/中立化扩面；`.mcp.json` / manifest mcp/codex.posture 段（零改动）；三独立拍板议题；settings biz-allow 收窄
- 前置依赖：无（worktree 已建 + uv sync 完成）

## 4 任务拆解（风味 A 证据/bookkeeping；PR-1 = 8a–8e，PR-2 = 8f）

### 8a S6 双工具编排 scratch 重建（不入仓）

- 编排脚本（P2 的 `p2_evidence_orchestrate.py` / `p2_batch.py` 是 scratch 未入仓）按 `evidence/development-agent-p2/SUMMARY.md` 的 Codex-on-Windows 四坑 + 工具形态在 scratchpad 重建：
  1. **Git Bash 全路径**（`C:\Program Files\Git\bin\bash.exe`）——Python `subprocess(["bash",...])` 会解析到 WSL bash → codex 跑不起来
  2. **`codex exec --json --color never -s workspace-write --add-dir <run-dir>`**——TUI 在非 TTY 崩且零输出
  3. **单可写根 `--add-dir <run-dir>`**——沙箱拒 split writable roots；run-dir 含 clone + RESULT_PATH 单棵树
  4. **`UV_CACHE_DIR=<run-dir>/uv_cache`** + prompt 走 stdin + 输出用真实文件句柄捕获
- Claude 形态：`claude -p "$(cat prompt.md)" --permission-mode acceptEdits --add-dir <run-dir>`，cwd=clone，全新会话
- 流程：runner `setup`（--scenario S6 --tool <t> --run <n> --runs-root <scratch>）→ 调用工具 → runner `verify` → 归档结构化件 → `teardown`
- 验证：正式采证前各做 1 次 S6 dry-run（不计入连续 2 次）

### 8b S6 正式采证（本 base develop @ 4ebd92e；harness 字节冻结）

- S6 × {claude,codex} × 2 连续 run；归档 `evidence/development-agent-p3/S6/<tool>/run-<n>/{result.json,verdict.json,setup.json}`（`commands.log` 被 `*.log` gitignore；退出码在 verdict.json；轨迹日志扫负向面后弃、不入仓）
- comparator = `report-schema-exact`：action 类型/目标/executed/reason 结构比对 + `remote_actions==[]`；无 no-write 快照门、无 classification 门（S6 最简比较器）
- 验证：全 4 verdict PASS；FAIL → 若 fixture/runner 缺陷则同 PR 评审修 + 自动转全量重采（§升档 watch），否则修编排 scratch 重跑

### 8c evidence/development-agent-p3/SUMMARY.md

- 采集环境（机器 / git / claude / codex 版本 / base SHA `4ebd92e` / clean-clone 布局 / Codex trust 只读核验）
- **S6 矩阵**（1 场景 × 2 工具 × 2 = 4 格，全 PASS）+ 结构化结果差异分析（report.actions 跨工具收敛；remote_actions=[] 全 4 次）
- **§11.1 P3→P4 晋级门装配**：显式声明「S1–S5 引用冻结 P2 证据（harness 字节不变，见 P2 SUMMARY），S6 本目录新采」→ 合成完整 S1–S6 两工具各 2× 矩阵
- **四技能诚实覆盖论证**（Owner 拍板 3）：post-merge←S6 专属 fixture；self-review←S2/S3 传递覆盖（P2 20/20，procedural_gates 含 11）；scope-drift（9）/ review-respond（15）**无 fixture**——manifest 分类 `native`/`adapter-backed` 无 Claude 专属 enforcement（二者 approval.mode=none、enforcement=[manual]/[adapter]），Codex 侧 adapter 行为矩阵等价承载；据实说明而非伪造 fixture
- **负向面**（复用 P2 口径）：S6 `changed_paths:[]` + `remote_actions:[]` + 干跑全 executed:false；轨迹硬扫 `exec.*(psql|psycopg|cat .env|Get-Content secrets)` = 空
- 验证：`check_frontmatter.py` + `check_wikilinks.py` 绿

### 8d manifest 四技能 `evidence` 指针（sdd/development-agent.yml）

- flow-post-merge：追加 `evidence/development-agent-p3/SUMMARY.md`（S6 专属）+ `tests/fixtures/development-agent/scenarios/S6/expected.yml`
- flow-self-review：追加 `evidence/development-agent-p2/SUMMARY.md`（S2/S3 覆盖 Stage 11）+ `evidence/development-agent-p3/SUMMARY.md`（P3 确认）
- flow-scope-drift / flow-review-respond：追加 `sdd/adapters/development-agent.md`（Behavior Matrix 覆盖 Stage-9/15 停点）+ `evidence/development-agent-p3/SUMMARY.md`（含二者据实推理覆盖论证）
- 硬约束：**只改这四条目的 `evidence` 列表**，不动 `mcp`/`codex.posture` 受保护段、不动 support_mode/projection/approval
- 验证：`check_development_agent.py --all` 0E/0W（evidence 须可定位到在盘文件）

### 8e adapter §Status + 剩余 A/B/C 映射确认（sdd/adapters/development-agent.md）

- §Current Implementation Status 追加 P3（#337）行：四技能收口 + S6 双跑 + 剩余映射确认
- **剩余 A/B/C 映射确认**（§11 P3「剩余映射」）：记录全 37 项 `projection` 三档已 = §4.4 的 🟢5/🟡21/🔴11 终态——🔴11（doc-validate/flow-verify=script-ci 等价 · git-issue=gh CLI 等价 · 8 infra=freeze 排除）为「已有普通脚本/文档/CI 等价通道的便利型技能，不强制迁移」；🟡21 为中立化/闭包后可投候选（各自前置未闭前不投）；结论：P3 无新增强制迁移，S1 已投 🟢5 不变
- 验证：`check_frontmatter.py` + `check_wikilinks.py` 绿；V8/V9/V10 不受影响自证

### 8f PR-2：plan/intake state flip + §11.1 晋级门勾稽（documentation 小 PR，Rule 12）

- program plan `[PLAN]_dual-agent-compat.md` §11 P3 段 flip→completed + §11.1 P3→P4 勾稽注记 + §12 S6 行注「P3 双跑完成」
- `[INTAKE]`/`[PLAN]_dual-agent-compat_p3.md` state→completed（+ completed 日期）
- #312 P3 勾 + 晋级证据 comment（merge 后 post-merge 段执行）

### Documentation Decision

Plan=Create（本文件，PR-1）；Evidence=Create（8c，PR-1）；Adapter=Update（8e，PR-1）；其余 9 类 None。

## 5 风险

| 风险 | 等级 | 风味 | 缓解 / Rollback |
|---|---|---|---|
| codex exec 四坑复现失败（Git Bash/JSON/writable-root/UV_CACHE） | Medium | A | 严格照 P2 SUMMARY 四坑；dry-run 先行；fallback=Owner TUI（差异如实记录进 SUMMARY） |
| S6 report.actions 跨工具/跨 run 措辞漂移 → 结构不齐 | Low | A | report-schema-exact 只比结构（type/target/executed/reason），不比自由文本；漂移=request.md 措辞缺陷 → 修 fixture（§12 同 PR）重跑并自动转全量重采 |
| harness 被迫改写（§12 逼出）→ S1–S5 冻结引用失效 | Low | A | 触发即自动转全 S1–S6 单基线重采（Intake §升档 watch）；本 PR 同时评审 fixture+checker 变更 |
| develop HEAD 在 run 间移动 → 基线漂移 | Low | A | 4 次 S6 采集在同一 develop SHA（4ebd92e）完成；每 run 记 base SHA |
| 证据文档误触既有 gate（frontmatter/wikilinks/G7 secret 扫） | Low | A | evidence/ 在 frontmatter SCAN_ROOTS 外须手动核验；轨迹日志不入仓（只入结构化件）；PR-1 全 gate 本地跑 |
| manifest 误改受保护段 | — | — | 只改四条目 `evidence` 列表；mcp/codex.posture 零字节不动（A14/D-017） |
| 4 必停面 / A14 / CI blocking toggle | — | — | 零接触 |

## 6 验证

- Level A（PR-1/PR-2 每次提交前）：`uv run pytest tests/unit -q` · `uv run ruff check` · `uv run mypy src/mj_agent`（若触 .py）· `check_development_agent.py --all`（V8）· `check_agents_projection.py --all`（V9）· `agents_sync.py --check --surface skills`（V10）· `check_frontmatter.py` + `check_wikilinks.py`
- Level B（PR-1 采证即验证本体）：8a/8b 规程；全 4 S6 verdict PASS
- 测试缝：既有 `test_sdd_development_agent.py` `-k S6` 单测已覆盖 golden vs expected（不开新缝，除非 §12 逼出）
- Stage 11 tie-in：反扫 N/A（纯新增证据 + evidence 指针）；scope-drift 预期 Severity=None

## 7 完成标准

Issue #337 AC1–AC6 逐条（勾稽见 issue）；PR-1/PR-2 全 merge + CI 绿（V8/V9/V10 warning，Linux checker 全绿）；
#312 P3 勾 + §11.1 晋级门证据 comment；post-merge 清理（worktree/分支/scratch run-dirs）。

## 8 关联

- Issue #337；总锚 #312；前序 #333（P2）/ #330（S2）
- 目标文件：§4 各子任务列示
- 不动文件：`src/mj_agent/**` 全部 · `.claude/**` · `.mcp.json` · `.github/workflows/ci.yml` ·
  `sdd/development-agent.yml` 的 mcp/codex.posture 段 · `.agents/**` · `.codex/**` ·
  `scripts/sdd/fixture_*.py` + `tests/fixtures/**`（只读复用，除非 §12 逼出）
- 后续独立 PR/切片：P4（观察期满后 blocking flip）· S3（doctor + skills gate 转正 + 三独立议题）
