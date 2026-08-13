---
type: adr
domain: WORKFLOW
summary: 以单 Epic、18 个串行 PR 与人工合并门闭合 Claude–Codex Agent Kernel
owner: ranzuozhou
created: 2026-08-13
updated: 2026-08-13
state: active
decision: accepted
track: engineering-workflow
tags:
  - adr
  - agent-kernel
  - codex
  - cross-carrier
  - dual-agent
  - workflow
---

# ADR-039: Codex Cross-Carrier Agent Kernel

## Status and approval gate

Owner 于 2026-08-13 在当前 Codex task 审阅下述 exact lifecycle / ADR-036 disposition diff，并给出独立
procedural approval；本 PR-0a change tree 因此记录本 ADR 为 `active / accepted`。该状态仅在 PR-0a
人工 merge 后进入 shared `develop`；在此之前 `origin/develop` 仍以 ADR-036/v1 为生效基线。
该批准只覆盖本 exact lifecycle/disposition diff，不覆盖 commit、push、PR create、merge 或 PR-0b。

当前状态码：`ACTIVE_ACCEPTED_PR0A_IN_PROGRESS`。

## Context

ADR-035 已授权 Claude Code 与 Codex 作为同等全职责开发参与者。ADR-036 进一步建立：

- 项目内 Kernel + 薄 compatibility adapter；
- `sdd/development-agent.yml` 派生清单；
- V8/V9 checkers；
- 仅覆盖 `.agents/skills/**` 与 `.codex/config.toml` 的 scoped `agents_sync`；
- generated artifact commit 入仓、禁止手改；
- manifest `projection` 驱动的 5-skill 初始 whitelist；
- canonical 10-enum 与 biz/Secrets/trust 边界不变。

该 v1 机制已稳定工作，但 required 18 中只有 5 项拥有 Codex project carrier；lock 仍是无
`schema_version` 的 legacy flat map；reconcile 以目录 allowlist 删除邻居；不存在 translated carrier、
closed fidelity/probe/receipt contract 或 project enforcement carrier。Epic #499 的 external v8 plan
提出在不改变数据边界和人工 merge authority 的前提下闭合这些缺口。

PR-0a fresh audit base：

- `origin/develop@c549880f6d1e5342c6402d9fb6d84639090020b5`；
- external v8 SHA-256
  `ce87a6a928ce539433db678f1158c50f725ab0f14ec8a0a250ef783c21e9a76a`；
- manifest 37 total / 18 required / 19 optional；
- projection 5 project / 21 after-neutralization / 11 never；
- required projection 5 project / 10 after-neutralization / 3 never；
- V8/V9 0 error / 0 warning；V10/V11 drift clean。

## Decision

采用仓内 `plans/[PLAN]_codex_cross_carrier_kernel.md` 定义的 v8 program：

1. 单一 Epic、18 个 delivery PR 严格串行，`max_active_stage = 1`。
2. one goal / worktree / branch / PR；前一 PR 人工 merge 并完成 Stage 17 后下一阶段才 eligible。
3. P0 分为 offline boundary、sanitized biz snapshot/source repair、post-merge EVAL/baseline。
4. 18 required capability 最终拥有 5 byte-copy + 13 deterministic translated native carriers。
5. manifest/lock/workflow/translation/fidelity/probe/receipt/ready-host 使用 closed versioned schemas。
6. reconcile 只管理经 verified lock/owner 声明的路径，保留所有 unowned neighbors。
7. deterministic discovery/path/collision/budget 为 blocking；implicit model-trigger 3× corpus 仅 telemetry。
8. V12/V13 按实际执行命令登记；D2 只把与 observation byte-identical 的 predicate 接入 blocking Tests。
9. direct pytest 最终成为人类/IDE 安全默认；Agent/CI 必须使用 hardened offline runner。
10. canonical HITL 保持 10-enum；kernel-meta approval 单列，不发明第 11 个 enum。
11. PR-F 保持 plan active；只有 PR-G 在 PR-F 人工 merge 后执行 lifecycle/Epic closure。
12. 每个 goal 在 `AWAITING_HUMAN_MERGE` 停止；agent 不 merge、不 auto-merge、不提前创建下一阶段。

## ADR-036 relationship

本 ADR **定向 revise、并不整体 supersede ADR-036**。ADR-036 继续作为已实施 v1 与历史决策基线；
以下 disposition 在本 PR-0a change tree 中获接受，并只在 PR-0a 人工 merge 后进入 shared `develop`：

- **D-011 — revised：** 保留 `agents_sync` 是“不引入全量配置生成器”的唯一 scoped exception，
  但将其闭合集从当前 skill/config 两面扩展为 manifest / typed source 明确声明的 managed outputs：
  `.agents/skills/<id>/SKILL.md`、`.agents/README.md`、`.codex/config.toml` 的 MCP/enforcement members、
  `.codex/hooks.json`、declared `.codex/rules/*.rules`，以及其 `.agents.lock.json` owner ledger。
  这不授予对 `.agents/**` 或 `.codex/**` 的目录级所有权；未声明邻居必须保留，继续拒绝第三方同步器。
- **D-012 — revised：** 保留 generated artifacts commit 入仓、禁止手改、作者侧 `sync` 与 byte-copy
  `--adopt` + HITL 原则；把 legacy flat lock/output contract 升级为 closed v2 typed inputs、canonical slices、
  output/member digests、byte-copy/translated render strategy 与 verified lock owner ledger。reconcile 只作用于
  已验证 owner 的 declared desired paths；通过 preflight 后允许可识别的 partial apply，但必须可安全重试收敛。
  translated/enforcement outputs 不可 adopt，byte-copy adopt 还必须满足 v2 lock CAS。
- **D-014 — revised：** 保留 manifest 是 projection whitelist SoT；将单独依赖 `projection` 的 v1 选择器
  修订为 manifest v2 的 `projection` + `codex_carrier` + translated `carrier_binding` closed contract。
  `codex_carrier != none` 当且仅当 `projection == project`，required capability 必须有 carrier；
  expected/reconcile/lock sets 按 carrier strategy 派生，adopt set 只按 byte-copy 派生。PR-C1 终态覆盖
  required 18 = 5 byte-copy + 13 translated；schema/checker 从 manifest 动态派生，不把计数硬编码为协议常量。

**保持不变：** D-013 的 MCP per-server tiers 与 biz×5 + ssh-manager 永久 `never`；D-015 的 doctor
只读和每工程师 × 每 worktree 手工 trust；D-016 的既有 gate posture / 独立 toggle 纪律（V12/V13 按本计划
warning observation，D2 另行审批 identical predicate）；D-017 与 D-010 的 canonical 10-enum、protected-anchor
审批纪律。ADR-000/006/009 数据边界、Owner human merge authority 及 ADR-036 其余未明示修订条款全部不变。
本 disposition 不直接修改 ADR-036 文件，也不预先批准后续 A0/C1/D1a/D2 的 protected/kernel hunks。

## Consequences

### Positive

- required 18 的 Codex carrier、dependency closure 与 fidelity 证据成为可重复验证的仓库事实。
- generated ownership 从目录 allowlist 收紧为 typed source + canonical desired oracle + verified lock owner。
- Claude authoring source 保持单一；Codex translation 是确定性产物，不建立第二份手写 workflow prose。
- execution/evidence/lifecycle 都绑定同一 Epic 与人工 merge barrier。

### Costs and limitations

- 新增 schema、renderer、registry、probe、receipt 与 enforcement 的维护成本。
- ready-host 与 behavioral observation 只能证明已列场景，不证明所有机器或模型语义恒等。
- warning telemetry 不构成 blocking guarantee；SKIP 不得冒充 PASS。
- 本计划不交付 managed identity、authenticated Owner proxy、least-privilege subagents 或 network proxy。

## Alternatives considered

- **维持 ADR-036/v1 的 5-skill byte-copy 范围**：拒绝作为目标态；无法闭合 required 18。
- **手写第二套 Codex workflow prose**：拒绝；产生双 SoT 与长期语义漂移。
- **全目录 reconcile / 删除未知邻居**：拒绝；ownership 不可证明且破坏用户文件。
- **并行或 stacked delivery**：拒绝；绕过 per-stage evidence 与人工 merge barrier。
- **把 implicit model trigger 作为 blocking**：拒绝；模型选择非确定，保留为 telemetry。

## Scope and non-decisions

本 ADR 不授权：

- 修改 SQL guardrail/system prompt/qcm catalog；
- 读取 Secrets、直连 biz DB 或使用数据库客户端；
- 自动 merge、auto-merge、force-push、rebase；
- 在 PR-0a 修改 `policies/**`、`sdd/**`、`.claude/**`、`.mcp.json`、generated artifacts、
  implementation 或 tests；
- 提前开始 PR-0b 或任何后续 worktree/branch。

## References

- [Epic #499](https://github.com/MJ-AgentLab/mj-agent/issues/499)
- `plans/[PLAN]_codex_cross_carrier_kernel.md`
- [[ADR-036_Dual_Agent_Thin_Adapter_And_Projection|ADR-036]]
- [[ADR-035_Codex_Full_Development_Participant|ADR-035]]
- [[ADR-034_HITL_Propose_Decide_Apply_Model|ADR-034]]
- [[ADR-006_Fail_Safe_Reads|ADR-006]]
- [[ADR-009_Biz_Domain_As_Primary_Data_Source|ADR-009]]
- Owner procedural approval：2026-08-13，当前 Codex task，exact lifecycle / ADR-036 disposition diff
