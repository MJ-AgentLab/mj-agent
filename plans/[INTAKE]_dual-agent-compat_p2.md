---
type: intake
summary: 双工具兼容 v5 第五执行切片（P2 首批六 flow skills fixture 端到端）的 Stage 0 Intake 落盘——maintain/Medium/2码PR+1flip；7 项 Owner 拍板记录（runner 载体 / result.json 产出 / Codex 执行形态 / clean-clone 隔离 / PR 拆分 / S6 范围 / 推进方式）；对应 issue #333（总锚 #312）
owner: ranzuozhou
created: 2026-07-14
updated: 2026-07-14
state: active
track: shared
---

# [INTAKE] 双工具兼容 v5 — P2 切片（issue #333）

> Stage 0 输出于 2026-07-14 会话内产生并当日落盘；触发 §2.1 落盘判定（多模块 + HITL 点≥3 + 多 PR 周期）。
> 上游输入：[[[PLAN]_dual-agent-compat|v5 计划]] §11 P2 / §11.1 P2→P3 晋级门 / §12 fixture 面（逐字为准）；
> 前序：P0/P1/S0/S1/S2 全闭环（S2 执行 #330 closed AC 10/10，develop @ 7d36fb2）；
> S3 完整收口受 P4 观察期约束（V10 2026-07-14 首挂，≥14 自然日 + 20 次连续 CI）暂不可做 → P2 为主轨道自然下一步。

## 1 Task Classification

- Type: **maintain**（fixture/测试基建 + scripts/sdd runner + manifest evidence——不触 `.claude/skills/**` 白名单源、`.mcp.json`、manifest `mcp`/`codex.posture` 段、4 必停面、真实 `.github/workflows/ci.yml`）
- Base branch: develop @ 7d36fb2；G1 worktree `maintain/333-p2-fixture-harness`
- 影响范围：`tests/fixtures/development-agent/scenarios/S1–S6`〔新〕· `scripts/sdd/`（fixture runner + comparator 模块，新）· `tests/unit/test_sdd_development_agent.py`（扩展）· `sdd/development-agent.yml`（仅六 flow 条目 `evidence` 列表）· `plans/` 2 件〔新〕

## 2 Risk Assessment

- Level: **Medium**（多模块 + 跨工具执行面；无 schema/secret/prod/必停面实改）
- Triggered §3.1 必停项：无直接触发。邻接红线两条：S4 fixture 仅为「请求改 system.md」的测试数据，真实 `src/mj_agent/prompts/system.md` 零字节不动（no-write comparator 自证）；S5 的 `continue-on-error` 翻转发生在 fixture 副本上，真实 CI gate 姿态不变 → 不触 `ci-blocking-gate-toggle`；若后续需挂新 CI step 另行独立拍板
- Gated actions：commit/push/PR 逐次拍板（恒定）；Codex clean-clone trust 若需新增条目由 Owner 按 D-015 亲手配
- 新依赖：预期零（runner = stdlib + 既有 pyyaml）；被迫引入则触必停 9 停下
- 已知陷阱沿用：LF 归一双平台稳定（F10）；#298 假红不适用（clean clone 无 .env）；codex exec 须 `</dev/null`；Desktop 常驻会重写 `~/.codex/config.toml`

## 3 环境事实（2026-07-14 Intake 粗扫）

- manifest 六项均非 `unsupported`：flow-diagnose=`project` 双 native；flow-intake/plan/implement/repo-scan=`after-neutralization` + Codex adapter-backed；flow-verify=`never`（script-ci 等价）——§11.1 首条件现状即满足，收口留复核记录
- `tests/fixtures/development-agent/` 不存在（fixture 面绿地）；`tests/unit/test_sdd_development_agent.py` 已存在（S6 `-k S6` 有落点）
- S5 验证命令即 `check_development_agent.py --changed-from <fixture-base> --json --fail-on error`（既有脚本，V8）；S6 验证命令即单测
- #312 OPEN，P2 为首个未勾项

## 4 Documentation Decision（粗评；Stage 3 细化）

Plan=Create（`plans/[PLAN]_dual-agent-compat_p2.md`，PR-1 携带）；SPEC/ADR/RUNBOOK=None（§12 已是 spec；harness 设计已拍板并记录于本文件 §6）。

## 5 Issue

- 总锚 #312（P2 为主轨道下一未勾阶段）；P2 执行 issue **#333**（Issue Draft 全文即 body，AC 10 条）
- 拆分：**2 码 PR + 1 flip**——PR-1（maintain）= S1–S6 fixtures + runner + comparator + result.json schema + 单测（fixture 与 checker schema 同 PR，满足 §12）；PR-2（maintain）= 双工具 S1–S5 各连续 2× 实跑证据 + manifest 六条目 evidence + 晋级证据整理；PR-3（documentation）= plan/intake state flip。证据跑在 PR-1 merge 后的 develop 基线上采
- 合并纪律 = 交 Owner 执行 + `--delete-branch` + 每步核对 baseRefName + 合并确认用 `gh pr view --json state` 独立验证（不与清理串同一命令）

## 6 Owner 拍板记录（2026-07-14）

| # | 阶段 | 决策 |
|---|---|---|
| 1 | Stage 0 | **Runner 载体 = Python CLI in `scripts/sdd/`**：子命令 setup（临时 git 仓 + fixture-base commit）/ verify（命令数组 + comparator）/ report；comparator 独立模块可被单测 import；`_common` bootstrap |
| 2 | Stage 0 | **result.json = Agent 写 + runner 复核**：fixture 协议（request.md 尾部固定段）要求被测 agent 会话结束时写 result.json 到 clone 内约定路径；runner 独立重算 changed_paths / 命令退出码 / 快照 hash 交叉核验——分类字段信 agent 自报（被测物），客观字段以 runner 重算为准，不一致即 FAIL |
| 3 | Stage 0 | **Codex 执行形态 = codex exec 非交互为主**（`</dev/null`、cwd=clone、prompt=request.md 协议）；无人批准语义天然匹配 S4/S5 stop-before-8；Owner TUI 仅作 exec 失败时 fallback（差异如实记录） |
| 4 | Stage 0 | **Clean-clone 隔离 = 容器目录下固定子目录** `D:\workspace\10-software-project\projects\mj-agent\fixture-runs\<tool>-<run>\`：本地 bare clone + fixture-base commit 叠加 + uv sync，不拷 .env；trust 用 `codex mcp list` 零成本 oracle 实证，不行再由 Owner 按 D-015 加父目录条目；跑完 runner 显式清理 |
| 5 | Stage 0 | **PR 拆分 = 2 码 PR + 1 flip**（见 §5） |
| 6 | Stage 0 | **S6 范围 = 建齐 fixture + report-schema-exact 单测，双工具实跑留 P3**（§11.1 P2→P3 只要 S1–S5；S6 stage_path=[17] 对应 flow-post-merge 属 P3 第二批） |
| 7 | Stage 0 | **推进方式确认**：落盘本 INTAKE → gh issue 创建（本项即授权该次 remote action）→ G1 worktree → Stage 3 repo-scan → Stage 4 plan 体 → Gate 5 拍板后动工 |

## 7 Verification Plan

- Level A（每 PR）：`uv run pytest tests/unit -q` · `uv run ruff check` · `uv run mypy src/mj_agent` · `check_development_agent.py --json --fail-on error`（V8）· V9/V10/V11 不受影响自证
- Level B：S1–S5 双工具各连续 2× clean-clone 实跑（Claude 侧 AI 跑；Codex 侧 codex exec，trust 交互段如需则 Owner 跑）；证据 = result.json + 退出码 + 审批事件 + comparator 结果

## 8 Next Step

`/mj-agent-git-issue` 建 P2 执行 issue → `/mj-agent-git-branch` 开 worktree → Stage 3 repo-scan → Stage 4 计划落盘 → Gate 5 → Stage 8 实施。P2 merge 后本文件 state flip completed（Rule 12，PR-3 运载）。
