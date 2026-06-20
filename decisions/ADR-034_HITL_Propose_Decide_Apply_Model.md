---
type: adr
domain: WORKFLOW
summary: HITL 由「AI 出 diff 草案 → Owner 手动落盘」改为「AI 提议 → Owner 拍板 → AI 落盘」；4 项 in-source 专属必停 deny→ask 逐写拍板门 + A13/A14 合并审查兜底；protected paths（.claude/** / .mcp.json）AI 改、harness 强制 prompt 即拍板；runtime-* 由 read-only 改 propose→拍板→apply；新增 External-Info Handoff 纪律；仅交互模式成立（auto 模式 classifier 硬拦放宽类改动）
owner: 项目负责人
created: 2026-06-20
updated: 2026-06-20
state: active
decision: accepted
track: engineering-workflow
tags:
  - adr
  - hitl
  - workflow
  - permissions
  - deny-to-ask
  - protected-paths
  - runtime-skill
---

# ADR-034: HITL Propose → 拍板 → Apply Model

## Context

mj-agent 既有 HITL 机制是「**AI 产出 diff 草案 / 选项 → Owner 手动粘贴 / 复制 / 编写落盘**」：

- 4 个 `runtime-*` skill 标「read-only by design，永不写盘」，Owner 拿 diff 自己 Edit；
- `flow-plan` 出 plan 草案让 Owner 自己 Write；`flow-post-merge` 出 frontmatter diff 草案让 Owner 用 Edit 应用；`flow-review-respond` 出回复草案让 Owner 手动 paste 到 GitHub；
- 5 个安全红线面（`tools/sql/{guardrail,precheck}.py`、`prompts/system.md`、in-source `skills/*/SKILL.md`、`biz_catalog/qcm_catalog.yaml`）被 `.claude/settings.json` 物理 `deny`，AI 完全不能写。

这套设计把"决策"与"转写"都压在 Owner 身上：Owner 不仅要拍板，还要逐字落盘，toil 高。项目负责人决策把机制改为 **AI 提议 + Owner 拍板（决策）+ AI 落盘**，合并审查兜底，彻底消灭手动转写。

附带修正一处文档漂移：`policies/data-boundary.md §3` 曾称 `guard-git-workflow.ps1` PreToolUse hook 在 Edit/Write 拦截 4 安全面——实测该 hook 仅 `matcher=Bash` 且只查 G1/G2 git 命令，真正拦 Edit/Write 的是 `settings.json` 物理 `deny`。

核查 Claude Code 官方权限模型确认：`.claude/**`（除 `.claude/worktrees`）、`.mcp.json`、`.claude.json` 是**硬编码 protected paths**——交互模式下写入永不自动批准、一律弹强制 prompt（`permissions.allow` 不可抑制），该 prompt 即 Owner 拍板；唯 `auto` 模式把 protected-path 写路由到 classifier，privilege-escalation（放宽 settings.json / 改 .mcp.json trust）被硬拦（harness 固定、不可禁用）。

## Decision

1. **HITL 执行模型 = propose → 拍板 → apply**：HITL 暂停 ≠ 让 Owner 手动转写。AI 呈现方案 / 选项 / diff + impact 分析 → Owner 拍板（`AskUserQuestion` 选择，或权限 prompt 批准）→ **AI 直接落盘并执行**。Owner 职责是决策，不是粘贴 / 复制 / 编写。kernel home = [[../sdd/workflows/execution-loop|execution-loop]] §3.0。

2. **4 项 in-source 专属必停 deny→ask**：`tools/sql/{guardrail,precheck}.py` / `prompts/system.md` / `skills/**/SKILL.md` / `biz_catalog/qcm_catalog.yaml` 从 `settings.json` `permissions.deny` 移到新 `permissions.ask` 列表（precedence `deny` > `ask` > `allow`）——AI 对其 Edit/Write 在交互模式触发**逐写权限 prompt（= Owner 拍板）**，批准后落盘。物理硬锁兜底转为 **拍板 prompt + 合并审查（A13 settings allowlist / A14）**。

3. **protected paths 归入同模型**：`.claude/**` / `.mcp.json` / `.claude.json` 由 AI 改——交互模式 harness 强制 prompt（= 拍板，allow 不可抑制）+ A13/A14 合并审查兜底，消灭手动编辑。

4. **runtime-* 角色反转**：4 个 `mj-agent-runtime-*` 由「read-only inspect / 永不写」改为「**分析 + propose diff + impact → Owner 拍板 → 经 `ask` 门直接落盘**」。`prompt-version-bump` 的 ADR-000/006/009 数据边界 sanity check（任一 fail 即 STOP）保留。

5. **External-Info Handoff 纪律**（[[../policies/ai-agent|policies/ai-agent]] §8）：需要 AI 无法自取的外部信息（ip / port / key / token / endpoint / secret）时，AI 必须给具体可执行 Owner 步骤（精确命令 + env 名 + 失败现象），不得含糊提问；HITL 提问格式（execution-loop §3.3）新增 `Owner 执行步骤` 字段。

6. **GitHub 发帖纳入拍板后执行**：Owner 拍板后 AI 经 `gh` / `mcp__github__` 自动发 review 回复 / issue 评论（去除 `flow-review-respond` 的手动 paste）；但 `git commit/push/PR 创建/merge` 仍是独立 HITL gate（Stage 12/13/14/16 照停）。

7. **保留 `deny` 的面**：`.env`（含 Read）/ `config/secrets*.enc` / `rm -rf` 类——这些不是「拍板后让 AI 写」的对象（AI 取不到的外部 secret 走第 5 条给 Owner 步骤）。

8. **执行前提 = 交互模式**：本模型放宽类改动（deny→ask、protected-path privilege-escalation）仅在 `default`/`plan`/`acceptEdits` 交互模式成立；`auto` 模式 classifier 硬拦（harness 固定），`bypass` 模式跳过全部检查——故这两类改动须在交互模式执行。

本 ADR **supersede ADR-015 §决策点 4**（runtime 类目「read-only 永不写」硬约束）的语义残留。数据边界本身（ADR-006 4 层 guardrail / ADR-009 biz 域 only / ADR-000 三原则）**不变**——本 ADR 改的是"谁落盘、怎么拍板"的元门，不放宽数据边界规则。

## Consequences

- **正面**：消灭 Owner 手动转写 toil——AI 提议后 Owner 一次拍板即落盘；HITL 从"暂停等人写"变"暂停等人拍板"；兜底从分散的 skill anti-pattern 收敛到 settings.json `ask` 门 + A13/A14 合并审查。
- **负面**：deny→ask 把"物理不可写"降为"逐写拍板"——`auto`/`bypass` 模式下 `ask` 会被自动放行，弱化硬屏障；故强制交互模式执行。`settings.json` 放宽类改动本身在 `auto` 模式被 classifier 硬拦（不可禁用），落地本 ADR 时该文件由 Owner 手动应用（交互模式则 AI 可落盘）。
- **中性**：runtime-* 仍先做 propose + impact 反扫（拍板前），分析价值不变；只是落盘从 Owner 手动改为 AI 拍板后执行。`flow-self-review`（不 auto-commit）/ `flow-verify`（不 auto-run Level C）/ `flow-intake`（仅评估）维持原样——它们的「不 auto-X」指向仍保留的 commit/destructive/创建 gate，非手动转写。

## Alternatives considered

- **A. 维持 deny + 手动落盘**：拒绝。Owner 明确要求消灭手动转写；维持 deny 则 4 安全面仍需 Owner 手写。
- **B. 仅工作流面归新模型，安全面保持 deny**：拒绝。Owner 拍板选「全覆盖（deny→ask）」（Q1）——安全面也要 AI 落盘，`ask` 逐写拍板保留人工门即可。
- **C. runtime-* 保持 read-only，仅改 handoff 措辞**：拒绝。read-only 身份与"AI 落盘"目标矛盾；须反转为 propose→拍板→apply。
- **D. 落盘后不依赖合并审查、仅靠拍板**：部分采纳。拍板是首道门，但放宽硬屏障后必须有 A13/A14 合并审查兜底，二者叠加。

## References

- [[../sdd/workflows/execution-loop|execution-loop]] §3.0（拍板模型）/ §3.1（4 必停 enforce）/ §3.3（Owner 执行步骤字段）/ §4.2（Runtime 约束）
- [[../policies/ai-agent|policies/ai-agent]] §4（10-enum enforce 机制）/ §8（External-Info Handoff）/ §9（Protected-Path 拍板 + Merge-Review 兜底）
- [[../policies/data-boundary|policies/data-boundary]] §3（4 必停执行机制；含 hook 漂移修正）
- [[../sdd/gates|sdd/gates]] §4（4 hard stops 真值化为 ask-gated）
- `.claude/settings.json`（deny→ask）；A13 settings allowlist review / A14 `.mcp.json` trust posture（PR 模板）
- [[ADR-006_Fail_Safe_Reads|ADR-006]] / [[ADR-009_Biz_Domain_As_Primary_Data_Source|ADR-009]] / ADR-000 — 数据边界**不变**（本 ADR 改元门非边界规则）
- [[ADR-013_Plugin_SKILL_md_Schema_Separation|ADR-013]] / [[ADR-016_In_Tree_Claude_Skills_Ecosystem|ADR-016]] — in-tree skill schema / 命名空间
- ADR-015 §决策点 4（archived）— 被本 ADR supersede 的 runtime read-only 硬约束语义残留
