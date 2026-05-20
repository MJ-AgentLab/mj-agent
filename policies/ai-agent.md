---
type: policy
artifact: ai-agent
state: draft
version: 0.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-05-20
track: engineering-workflow
ai_visibility: source-of-truth
---

# Policy: AI Agent Boundaries

> Phase M0 — 4 段 native 内容 ✓（§Codex 非参与 / §Subagent Split A3 / §Symbol-first Search A5 /
> §HITL Required Scenarios）.
> 其余段（§Read/Write boundary / §Read priority / §Output requirements）在 Phase M2 内容填充.

## §1 Codex 非参与策略层（native；最高优先级）

**当前 mj-agent 项目不采用 Codex 与 Claude Code 协作开发.**

| 原则 | 含义 |
|---|---|
| 实施单一来源 | 所有文件修改、代码实现、测试运行、目录迁移、文档落地、验证总结均由 Claude Code 完成. |
| Codex 只读 | Codex 仅作只读外部评审工具；不修改仓库；不执行任务；不调用 commit / push / migration. |
| 不可委派 | Claude Code 不得把执行任务委派 / 转发 / 暗示给 Codex；不在文档中以"Codex 可以协助 X"等措辞预留协作面. |
| 边界文件 | 详 `AGENTS.md`（顶部红 NOTE）+ `CLAUDE.md` §Codex Status. |

**Why this boundary**：

1. **Single point of accountability** — Claude Code session continuity 保稳定上下文.
2. **Tool execution surface 受控** — 一个 agent 的 permission model 易审计.
3. **4 项专属必停**（sql-guardrail-relax / prompt-version-bump / biz-catalog-sync /
   runtime-skill-content-change）只能由单一 decision-maker enforce.
4. **CLAUDE.md HITL 规则** 是按 Claude Code 读写契约校准的；其他 agent 解释可能漂移.

每次任务输出末尾必须显式声明 `Codex invocation: NONE`，即使本次显然无 Codex 触发也声明.

## §2 Subagent Split 准则（A3 — Anthropic 大型代码库最佳实践；native）

**强制触发条件**（满足任一即必须走 read-only explore subagent，而非 main session 直接 read）：

| 触发 | 行动 |
|---|---|
| scope 涉及 ≥ 2 capability | dispatch `Explore` subagent 输出 RepoScanResult 文件 → main session 读 RepoScanResult 编辑 |
| 预计 Read 文件 ≥ 50 个（含 `docs/` / `archive/`） | 同上 |
| 任务起点是"我需要先了解 X"（探索性问题） | 走 `mj-agent-flow-repo-scan` skill |
| Phase M5 / M6 大规模迁移 / 归档前的 stale-reference 扫描 | dispatch 2-3 parallel explore subagents 分 path-scope |

**理由**（per Anthropic 博客 "Effective context engineering for AI agents"）：split exploration
from editing — read-only subagent 输出 findings 文件，main agent 用文件全貌编辑，避免 main
session context 被探索性 read 污染.

**反例**（违反 A3）：在 main session 连续 `Read` ≥ 50 个 docs/archive/ 文件做"调研" — context
膨胀直接吞掉编辑期可用预算.

## §3 Symbol-first Search 准则（A5 — Anthropic 大型代码库最佳实践；native）

mj-agent 启用 `pyright-lsp` plugin（详 `.claude/plugins.json`）→ Python 符号查询优先 LSP，
而非 string grep.

| 场景 | 旧方式（grep） | LSP 方式 |
|---|---|---|
| 查 `make_graph` 函数 | grep `make_graph` 全仓 → 命中 docstring / 注释 / 旧 plan | LSP `find_definition` → 仅 `src/mj_agent/agent.py:NNN` |
| 查 `ALL_TOOLS` 用法 | grep `ALL_TOOLS` → 命中 `.py` + `.md` + plan | LSP `find_references` → 仅 Python 真实引用 |
| 重命名 `find_biz_context` | sed 全仓替换 → 风险高 | LSP `rename` → 精确 |

**约束（fallback）**：LSP 不替代 grep / Glob —— 当查询是 string pattern（"TODO" / 文档关键字 /
non-Python 文件）时 grep 仍是首选.

**Pyright vs mypy 差异**：mj-agent CI 用 `mypy --strict src/mj_agent`；LSP 用 pyright；二者
type inference 在 some edge case 有差异（per R-G23）. 出现差异时以 mypy 为准（CI 阻塞 source
of truth），LSP 仅作交互式辅助.

## §4 HITL Required Scenarios（与 `sdd/gates.md` §"mj-agent specific hard stops" 同步）

以下场景无论文件路径必须 HITL：

1. 4 项 mj-agent 专属必停（sql-guardrail-relax / runtime-skill-content-change /
   prompt-version-bump / biz-catalog-sync）
2. cross-capability contract 变更
3. 数据库 migration（mj_agent_memory schema）
4. secrets / 权限 / GRANT 变更
5. CI blocking gate 启用 / 关闭
6. 删除 / 迁移 / 归档历史内容
7. Agent tool 列表 + schema 变更
8. Prompt 行为边界变更（不仅 version bump，body 任何修改）
9. 生产运行方式变更（Docker prod compose）
10. 大规模目录迁移（≥10 文件）
11. 数据-LLM 边界三原则（ADR-000）相关任何变更
12. ADR 状态变化（draft → active / active → deprecated / supersede）

## §5 可修改路径白名单 / 必须 HITL 清单

> TBD: Phase M2 — 详 path-level 表（与 root CLAUDE.md "What Claude May Edit" / "What Claude
> Must Not Edit Without Approval" 段同步；详 `mj-agent-refactored-structure.md` §17 CLAUDE.md
> 模板 §What Claude May Edit / §What Claude Must Not Edit Without Approval）.

## §6 每次任务输出要求

> TBD: Phase M2 — 详 12 字段输出模板（详 `mj-agent-refactored-structure.md` §17 CLAUDE.md 模板
> §Output Requirements + spec-anchored-calm-lampson §11.6）.

---

> *Phase M0 — 4 段 native；其余 TBD Phase M2.*
