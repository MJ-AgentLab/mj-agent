---
type: intake
summary: 双工具兼容 v5 第四执行切片（S2 MCP 面）的 Stage 0 Intake 落盘——maintain/High/2-PR；4 项 Owner 拍板记录（锚定 S2 / spike 方案 / 2-PR 拆分 / settings biz allow 收窄同期评估）；对应 issue #330（总锚 #312）
owner: ranzuozhou
created: 2026-07-14
updated: 2026-07-14
state: active
track: shared
---

# [INTAKE] 双工具兼容 v5 — S2 切片（issue #330）

> Stage 0 输出于 2026-07-14 会话内产生并当日落盘；触发 §2.1 落盘判定（多模块 + HITL 点≥3 + High + protected 邻接面）。
> 上游输入：[[[PLAN]_dual-agent-compat|v5 计划]] §8/§11 S2/§11.1/§12/§16/§17；S1 先例 #326（closed AC 9/9，develop @ c866029）；S1→S2 晋级证据三项已齐（golden 双平台 / reconcile 负向 / Codex 实机 PASS）。

## 1 Task Classification

- Type: **maintain**（生成器 emitter B / 新顶层产物 / CI gate / checker / tests / 治理文档——不触 `src/mj_agent/**`、`.mcp.json`、manifest `mcp`/`codex.posture` 段〔均只读〕）
- Base branch: develop @ c866029；G1 worktree `maintain/330-s2-mcp-projection`
- 影响范围：`scripts/sdd/agents_sync.py`（emitter B）· `scripts/sdd/check_agents_projection.py`（V9 投影域扩展）· `.codex/config.toml`〔新，生成产物〕· `.agents.lock.json`（面扩展）· `.github/workflows/ci.yml`（MCP gate day-1 blocking step）· `scripts/sdd/check_secret_exposure.py`（G7 扫描域）· `tests/unit/` · `AGENTS.md` · `sdd/gates.md` · plans 2 件〔新〕

## 2 Risk Assessment

- Level: **High**
- Triggered §3.1 必停项：`ci-blocking-gate-toggle`（MCP 产物 gate day-1 blocking 挂载；D-016 预拍板方向 + 切片内显式 Owner 执行记录）；`mcp-server-trust-posture-change` 邻接（`.codex/config.toml` 受保护邻接面创建，per program plan §17）；commit/push/PR 逐一拍板（恒定）
- mj-agent 专属 4 项（trigger 10-13）：均不触及；A14 不触发（`.mcp.json` 零改动；spike 若逼出源侧需求 → 停，独立拍板）；无新依赖（TOML 写=手写模板，读=stdlib tomllib）
- 秘密纪律：spike 探针 presence-only 不回显值；产物按名引用；G7 扩展钉字面凭据零容忍
- 硬前置：3 spike 全 pass；任一 FAIL → 降级 doctor 引导手工维护用户级 config，切片收缩为 G7 扩展 + 降级文档化

## 3 环境事实（2026-07-14 Intake 实测）

- Codex CLI 0.144.3；仓内无 `.codex/`；`.toml` 已 `.gitattributes` pin `eol=lf`（F10 抖动风险已消）
- Owner 用户级 `~/.codex/config.toml` 实测含 `[mcp_servers]`：`postgres-dev/test-lan/test-wan/prod-lan/prod-wan`×5 + `ssh-manager` + `node_repl`（仅取段名核验，未读值）——与拟投影三档（github/playwright/serena）**零重名**；叠加语义（并集/优先级/posture 覆盖）并入 spike ② 判定项
- 用户级 `[projects]` trust 有 `d:\...\mj-agent` 父目录条目、无 develop worktree 条目——spike ③ 的实测对象
- emitter A 已为 B 预留位（`agents_sync.py` 头注 "emitter B is S2, spike-gated"）；V9 `load_project_set` 可复用读 manifest `mcp` 段

## 4 Documentation Decision（粗评；Stage 3 细化）

Plan=Create（本 2 件，PR-1 携带）；ADR=None（D-011~D-017 已收口，降级路径已预决）；其余全 None。

## 5 Issue

- 总锚 #312（S-轨道 S2 为下一未勾阶段）；S2 执行 #330（Issue Draft 全文即 #330 body，AC 10 条）
- 拆分：**2-PR**（PR-1 = emitter B + 产物 + MCP gate blocking + G7 + tests + 文档一体；PR-2 = plan/intake state flip）；spike 走 scratch + vault 证据不占 PR；合并纪律 = 交 Owner 执行 + `--delete-branch` + 每步核对 baseRefName 已翻 develop

## 6 Owner 拍板记录（2026-07-14）

| # | 阶段 | 决策 |
|---|---|---|
| 1 | Stage 0 | 锚定 **S2 MCP 面**（不换 P2；晋级证据三项已齐） |
| 2 | Stage 0 | **spike 方案批准**：①env 按名透传 presence-only 探针 + github 实连终判 ②scratch 仓实载 + 用户级叠加语义 ③bare+worktree cwd/trust 粒度；分工=非交互段 AI、trust 交互段 Owner（D-015 红线）；证据落 vault `claude-codex-agent-kernel/mj-agent/`；任一 FAIL 即降级 |
| 3 | Stage 0 | PR 拆分 = **方案 A（2 PR）**：PR-1 实施一体 + PR-2 flip；spike 不占 PR |
| 4 | Stage 0 | **settings biz allow 收窄同期评估**：仅出评估产物待独立拍板，不并入本切片实施（#330 AC10） |

> spike 结果出来后另有**进/退拍板**（第二道 HITL）；day-1 blocking 挂载时另有 `ci-blocking-gate-toggle` 显式执行记录。

## 7 Verification Plan

- Level A（每 PR）：`uv run pytest tests/unit tests/eval` · `uv run ruff check` · `uv run mypy src/mj_agent` · V8/V9/V10 `--all` · `check_secret_exposure.py --all`
- Level B：`codex mcp list` + 三 project 档实调（Owner 跑 trust 交互段）；CI 实跑含 fork/无 secrets 语义核验

## 8 Next Step

Stage 3 repo-scan → spike 先行（scratch）→ 进/退拍板 → Stage 4 计划落盘 → Stage 8 实施。S2 merge 后本文件 state flip completed（Rule 12，PR-2 运载）。
