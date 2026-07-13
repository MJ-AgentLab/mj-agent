---
type: sdd-adapter
artifact: development-agent
state: active
version: 1.0
owner: ranzuozhou
created: 2026-07-13
updated: 2026-07-13
track: engineering-workflow
ai_visibility: source-of-truth
---

# Adapter: Development Agent (dual-tool compatibility)

> dual-agent-compat v5 P1 落地（#320 / ADR-036）——本 adapter 吸收 Claude Code 与 Codex 的
> **入口、审批载体与调用差异**；它不拥有业务规则，也不是第二事实源（program plan
> [[../../plans/[PLAN]_dual-agent-compat|v5]] §7 层级：本文件属「派生清单/平台适配」层，
> canonical 规则只在 kernel——`sdd/` + `policies/` + capability contracts）。
> 机器可读侧 = [[../development-agent|sdd/development-agent.yml]]（manifest，唯一覆盖状态 SoT）。

## §Scope

**Included**：

- `sdd/development-agent.yml` — 37 项 in-tree skill 能力的双工具覆盖 / 审批 / 证据索引 +
  `projection` 三档（D-014 白名单 SoT）+ `mcp` per-server 三档（D-013）+ `codex.posture` 手写段
- 双工具行为矩阵（同一 canonical 停点的 per-tool 载体，见 §Behavior Matrix）
- 根 + 4 嵌套 `AGENTS.md` 与同层 `CLAUDE.md` `@AGENTS.md` 引用关系（V8 校验面）
- 投影域结构规则（引用闭包 / reconcile / lock；V9 校验面；产物本体属 S1+）

**Excluded**：

- 各 skill 的语义正文（canonical 在 `.claude/skills/*/SKILL.md`，由 claude-code-skill adapter 治理）
- in-source runtime canonical（→ runtime-skill / prompt adapters）
- `.mcp.json` 本体（A14 保护面；本 adapter 只消费其 server 清单事实）
- `agents_sync.py` 生成器与 `.agents/` / `.codex/config.toml` 产物（S1/S2 落地；D-011 唯一豁免）

## §Behavior Matrix（同一停点，per-tool 载体）

停点本身 tool-neutral（`OWNER_APPROVAL_REQUIRED`，canonical 10-enum per
[[../../policies/ai-agent|policies/ai-agent]] §4 + AGENTS Git Owner gate）；只有载体不同：

| 面 | Claude Code 载体 | Codex 载体 |
|---|---|---|
| 4 项专属必停（runtime×3 + guardrail） | settings `ask` 逐写拍板门 + harness prompt | `AGENTS.md` 自守 prose（boundary 3） |
| Git Owner gate（commit/push/pr-create/merge） | 会话内 Owner 明示批准（ADR-034） | 同左（AGENTS.md boundary 4） |
| G1/G2 Git 纪律 | fail-closed PreToolUse hook（`guard-git-workflow.ps1`） | `AGENTS.md` boundary 5 自守 |
| 数据边界（ADR-006/009） | 4-tool 链 + L1/L1b guardrail + RO role | 同一链；`AGENTS.md` boundary 1 自守 |
| Secrets 边界 | permissions deny + sanitized 脚本缝 | `AGENTS.md` boundary 2 自守 |
| 同层局部约束 | 嵌套 `CLAUDE.md`（`@AGENTS.md` 导入） | 嵌套 `AGENTS.md`（root→cwd 逐级发现） |
| 程序性确认（AskUserQuestion 等） | harness 原语 | 会话对话等价（非 Owner 门；manifest `approval.mode: none`） |

## §Standards（manifest 契约摘要；全文 = program plan §9，checker 逐条执行）

> **V8 规则声明锚**：以下由 `scripts/sdd/check_development_agent.py` 机器校验。

- 顶层必含 `schema_version` / `snapshot` / `owners` / `capabilities`；未知 `schema_version` 拒绝。
- capability 必含 `id` / `group` / `required` / `claude` / `codex` / `evidence`；`id` 全仓唯一且
  对应 `.claude/skills/<id>/` 在盘存在。
- 每侧三正交字段：`support_mode`（5 枚举）/ `approval`（`{mode, gates}`）/ `enforcement`（5 枚举 list）。
- `approval.mode: none` ⇒ `gates: []`；`owner-hitl` ⇒ ≥1 gate 且 `policy_ref` ∈ canonical 10-enum
  ∪ `agents-git-owner-gate`；gate 必含 `policy_ref/trigger/stop_before/evidence_required`。
- `required: true` 双侧均不得 `unsupported`；`unsupported` 仅限 `required: false` 且
  approval none + enforcement 空；其余 support_mode 要求 enforcement 非空。
- `adapter-backed` 必带 `adapter_ref` 指向本文件；`script-ci` 的 evidence 须含可在 clean clone
  运行的仓内脚本或 CI job。
- `projection` ∈ project / after-neutralization / never（D-014：投影副本不计入 37 计数 SoT）；
  `mcp.servers.*.projection_policy` ∈ project / project-with-adr / never（D-013：biz×5 +
  ssh-manager 永 never）。
- 禁 `owner_agent` / 工具专属固定职责字段；统计（37 等计数）只由 manifest 派生，正文不再作 SoT。
- 根 + 4 嵌套 `AGENTS.md` 存在且同层 `CLAUDE.md` 含 `@AGENTS.md` 导入（V8 结构面）。

> **V9 规则声明锚**：以下由 `scripts/sdd/check_agents_projection.py` 机器校验。

- **引用闭包**：`projection: project` 技能 SKILL.md 的 `## Handoff*` 段 `/mj-agent-*` 出边必须
  ∈ project 集（`.agents/` 未落地时降 warning——S0 空态；产物出现后 error）。
- **全量 reconcile**：`.agents/skills/` 现存目录 ≟ manifest project 集；多出/缺失 = FAIL；
  `.agents/` 不存在 = vacuous pass（S0 空态不假红）。
- **lock 一致性**：`.agents.lock.json` ↔ 产物 `body_sha256`（LF 归一 canonical 算法，复用
  `scripts/sdd/_common/frontmatter.py`）；两者均缺 = pass，仅一方存在 = FAIL。

## §CI Gate

| Gate | 脚本 | 阻塞模式（真值） |
|---|---|---|
| V8 | `scripts/sdd/check_development_agent.py --all --fail-on error` | **warning**（P1 首发 `continue-on-error: true`；P4 观察期满 + Owner 批准后按 `ci-blocking-gate-toggle` 流程翻转） |
| V9 | `scripts/sdd/check_agents_projection.py --all` | **warning**（同上；S2 起 MCP 产物面 day-1 blocking per D-016，届时另立执行记录） |

单测：`tests/unit/test_sdd_development_agent.py`（含双发现 canary：on-disk `.claude/skills/`
目录数 ≟ manifest 计数）。注册：[[../gates|sdd/gates.md]] §2。

## §Current Implementation Status

- P1+S0（#320）：manifest + V8/V9 checker + 单测 + canary 落地；CI warning 首发。
- S1（未落地）：`agents_sync.py` + 🟢 首批投影 + `.agents.lock.json` + drift gate。
- S2（未落地；3 spike 硬前置）：emitter B（`.codex/config.toml`）+ MCP 产物 gate day-1 blocking。
- S3（未落地）：doctor（trust 只读 + `-Reload` 集成 + canary 迁入）+ skills gate blocking 转正。
