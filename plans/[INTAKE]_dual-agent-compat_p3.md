---
type: intake
summary: 双工具兼容 v5 第六执行切片（P3 第二批四 flow skills + S6 双工具实跑 + 剩余 A/B/C 映射）的 Stage 0 Intake 落盘——maintain/Medium/2 PR（1 码+1 flip）；2 项 Owner 拍板（锚=P3 全范围 / S6 证据=新采+引用冻结 P2 S1-S5）；对应 issue #337（总锚 #312）
owner: ranzuozhou
created: 2026-07-15
updated: 2026-07-15
state: active
track: shared
---

# [INTAKE] 双工具兼容 v5 — P3 切片（issue #337）

> Stage 0 输出于 2026-07-15 会话内产生并当日落盘（worktree 内）；触发 §2.1 落盘判定
> （多模块 + HITL 点≥3〔commit/push/PR/merge × 2 PR〕 + 多迭代周期）。
> 上游输入：[[[PLAN]_dual-agent-compat|v5 计划]] §11 P3 / §11.1 P3→P4 观察期门 / §12 S6 行（逐字为准）；
> 前序：P0/P1/S0/S1/S2/P2 全闭环（P2 执行 #333 closed AC 10/10，develop @ `4ebd92e`；S1–S5 20/20 PASS）；
> S3 完整收口 + P4 blocking 翻转均受 P4 观察期约束（V10 2026-07-14 首挂，≥14 自然日 + 20 次连续 CI）暂不可做
> → P3 为主轨道自然下一步。

## 1 Task Classification

- Type: **maintain**（证据采集 + manifest `evidence` bookkeeping + plan 状态）+ **documentation**（§11 flip / A/B/C 映射确认）——不触 `.claude/skills/**` 白名单源、`.mcp.json`、manifest `mcp`/`codex.posture` 段、4 必停面、真实 `.github/workflows/ci.yml`
- Base branch: develop @ `4ebd92e`；G1 worktree `maintain/337-p3-second-batch`
- 影响范围：`evidence/development-agent-p3/`〔新〕· `sdd/development-agent.yml`（仅四 flow 条目 `evidence` 列表；**非** `mcp`/`codex.posture` 受保护段）· `sdd/adapters/development-agent.md`（§Current Implementation Status 追加 P3 行 + 剩余映射确认）· `plans/` 2 件〔新 + flip〕· `tests/fixtures/development-agent/scenarios/S1–S6`（**只读复用**，不改，除非 §12 逼出同 PR 变更）· `scripts/sdd/fixture_*.py`（**只读复用**，同上）

## 2 Risk Assessment

- Level: **Medium**（多模块 bookkeeping + 跨工具执行面；无 schema/secret/prod/必停面实改；无新依赖）
- Triggered §3.1 必停项：无直接触发。数据/secret 边界靠 fixture 协议 + 采集期硬扫自证（复用 P2 负向面口径）。
- Gated actions：commit/push/PR 逐次拍板（恒定，per ADR-034 / AGENTS.md boundary 4）；merge 交 Owner（classifier 拦 agent 直合 develop）；Codex clean-clone trust 若需新增条目由 Owner 按 D-015 亲手配（P2 已证容器根 trust 覆盖全部 `fixture-runs/` clone，预期零阻塞）
- 升档 watch：若 S6 双跑逼出 harness/fixture 缺陷需改 `fixture_comparators.py`/fixture，则该改动 **§12 同 PR 评审**，并**自动触发全 S1–S6 单基线重采**（反转本 Intake 的 S6-only 决策）。`.mcp.json`/`codex.posture`/CI blocking toggle 零接触。
- 已知陷阱沿用：LF 归一双平台稳定（F10；`.gitattributes` 已 pin yml/json/toml/patch/py eol=lf）；#298 假红不适用（clean clone 无 .env）；Codex-on-Windows 四坑（Git Bash 全路径 / `codex exec --json` / 单可写根 `--add-dir` / `UV_CACHE_DIR` 重定向，详 P2 SUMMARY）；半成品 run-dir 须 `onexc` chmod+w 强删；合并确认用 `gh pr view --json state` 独立验证（不与清理串同一命令）。

## 3 环境事实（2026-07-15 Intake 粗扫 + 基线核验）

- **Harness 已 P3-ready**（零改）：`fixture_runner.py` `SCENARIO_IDS` 含 S6；`fixture_comparators.py` `report-schema-exact` + `validate_result_schema(expect_report=True)` 已实装。
- **S6 fixture 完整**：`request.md` + `context.json`（merged-PR 模拟）+ `expected.yml`（comparator=`report-schema-exact`，stage_path=[17]，risk=Low，5 action 干跑）+ `golden_result.json`。
- **四 P3 技能 manifest 现状**均非 `unsupported`：flow-scope-drift/self-review/review-respond/post-merge 全 `claude:native` + `codex:adapter-backed` + `projection:after-neutralization`；`evidence` 现仅指各自 SKILL.md（P2 六项已指 `evidence/development-agent-p2/SUMMARY.md`）→ P3 收口即追加双跑证据指针。
- **A/B/C 映射已在 manifest 落库**：全 37 项 `projection` 三档 = §4.4 的 🟢5（flow-diagnose + git-commit/delete/push/sync）/ 🟡21 / 🔴11（doc-validate + flow-verify + git-issue + 8 infra）**逐字吻合**——P3「剩余映射」是**确认 + 记录**，非新分类。
- **基线全绿**（worktree @ 4ebd92e，uv sync 后）：V8 0E/0W · V9 0E/0W · V10 `OK 5 skills lock consistent` · `pytest -k S6` 2 passed · `test_sdd_development_agent.py + test_agents_sync.py` 89 passed。
- #312 OPEN，P3 为下一未勾项（P0/P1/S0/S1/S2/P2 已勾）。

## 4 Documentation Decision（粗评；Stage 3 已细化）

Plan=Create（`plans/[PLAN]_dual-agent-compat_p3.md`，PR-1 携带）；Evidence=Create（`evidence/development-agent-p3/SUMMARY.md` + S6 结构化件）；Adapter=Update（`sdd/adapters/development-agent.md` §Current Implementation Status 追 P3 行）；SPEC/ADR/RUNBOOK=None（§12 已是 spec；harness 沿用 P2 定稿）。

## 5 Issue

- 总锚 #312（P3 为主轨道下一未勾阶段）；P3 执行 issue **#337**（Issue Draft 全文即 body，AC 6 条）
- 拆分：**1 码 PR + 1 flip**——PR-1（maintain，`maintain/337-p3-second-batch`）= [INTAKE]/[PLAN]_p3 + `evidence/development-agent-p3/`（S6 双工具各 2× 实跑）+ 四技能 manifest `evidence` + adapter §Status/剩余映射确认；PR-2（documentation，`documentation/337-p3-flip`）= plan §11 P3 flip→completed + §11.1 晋级门勾稽 + [INTAKE]/[PLAN]_p3 state→completed。证据跑在**本 base**（develop @ 4ebd92e）——harness 字节冻结不变，无需等 PR-1 merge。
- 合并纪律 = 交 Owner 执行 + `--delete-branch` + 每步核对 baseRefName + 合并确认用 `gh pr view --json state` 独立验证（不与清理串同一命令）+ merge 后 origin+gitee 分支手动双清。

## 6 Owner 拍板记录（2026-07-15）

| # | 阶段 | 决策 |
|---|---|---|
| 1 | Stage 0 | **锚 = P3 全范围**（AskUserQuestion 确认；非 settings biz-allow 收窄 / 非 S3 非观察期部分）：四技能 manifest 收口 + S6 双工具实跑 + 剩余 A/B/C 判断，达成 §11.1 P3→P4 晋级门。 |
| 2 | Stage 0 | **S6 证据范围 = 新采 S6 + 引用冻结 P2 S1–S5**（AskUserQuestion 确认；非全 S1–S6 重采）：harness（runner + comparators + fixtures）复用 P2 定稿、字节冻结不变，P2 的 S1–S5 20/20 仍有效；P3 只新采 S6（2 工具 × 2 run = 4 runs），SUMMARY 交叉引用 → 完整 S1–S6 矩阵。**前提**：P3 不改 harness/fixture；若被迫改则自动转全量重采（§升档 watch）。 |
| 3 | Stage 0（AI 提议，Gate 5 复核） | **诚实覆盖口径**：四技能仅 flow-post-merge 有专属 fixture（S6）；flow-self-review（Stage 11）由 S2/S3 传递覆盖（已在 P2 20/20）；flow-scope-drift（Stage 9）/ flow-review-respond（Stage 15）**无 fixture stage_path**——由 manifest 分类 + adapter 行为矩阵 + SUMMARY 的**据实推理覆盖**承载，**不伪造 fixture**。 |

## 7 Verification Plan

- Level A（每 PR）：`uv run pytest tests/unit -q`（clean clone 无 #298 假红）· `uv run ruff check` · `uv run mypy src/mj_agent`（若触 .py）· `check_development_agent.py --all`（V8）· `check_agents_projection.py --all`（V9）· `agents_sync.py --check --surface skills`（V10）· `check_frontmatter.py` + `check_wikilinks.py`（plans/evidence 文档）
- Level B：S6 双工具各连续 2× clean-clone 实跑（Claude 侧 AI；Codex 侧 `codex exec --json`）；证据 = result.json + verdict.json + setup.json + commands.log 退出码 + comparator 结果；轨迹日志不入仓（扫负向面后弃）

## 8 Next Step

Stage 4 计划落盘（本 worktree）→ Gate 5 拍板 → Stage 8 实施（S6 双跑编排 scratch 重建 + manifest + adapter + 证据）→ Stage 10/11 验证/自评 → Gate 13 PR → 交 Owner 合并。P3 merge 后本文件 state flip completed（Rule 12，PR-2 运载）。
