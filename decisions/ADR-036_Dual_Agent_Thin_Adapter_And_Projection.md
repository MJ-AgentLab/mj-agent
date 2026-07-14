---
type: adr
domain: WORKFLOW
summary: 收录 dual-agent-compat v5 的 D-001~D-017 决策集为正式 ADR——项目内 Kernel + 薄 compatibility adapter + 机器可读 manifest（sdd/development-agent.yml）+ V8/V9 checker + scoped 投影生成器 agents_sync（D-011 唯一豁免，仅 .agents/skills/ 与 .codex/config.toml 两面）；投影产物 commit 入仓不可手改（D-012）；MCP per-server 三档且 biz×5 + ssh-manager 永不投影（D-013）；skills 白名单由 manifest projection 字段驱动（D-014）；doctor 只读不写 trust（D-015）；skills gate warning→blocking 惯例 + MCP 面 day-1 blocking（D-016）；canonical 10-enum 不变并扩 A14 surface anchor 至派生 .codex/config.toml、.agents/**、agents_sync.py 与 manifest mcp/codex.posture 段（D-017）
owner: ranzuozhou
created: 2026-07-13
updated: 2026-07-13
state: active
decision: accepted
track: engineering-workflow
tags:
  - adr
  - dual-agent
  - codex
  - manifest
  - projection
  - workflow
---

# ADR-036: Dual-Agent Thin Adapter, Manifest, and Scoped Projection

## Context

[[ADR-035_Codex_Full_Development_Participant|ADR-035]]（+ 2026-07-06 amendment）确立 Claude Code
与 Codex 为双全职责开发参与者，但两工具的发现接线是 per-tool 的：`.claude/skills/` 与
`.mcp.json` 对 Codex 不可见，仓内无传输机制；`.codex/**` / `.agents/**` 不在任何受保护面上；
审批口径、Git guard、hook 行为各有单工具耦合（P0 已消除，#313）。Owner 于 2026-07-13 拍板
《mj-agent 双工具全职责兼容方案》v5（仓内 port：`plans/[PLAN]_dual-agent-compat.md`；裁决依据
评估文档 F1-F18 + 全枚举映射表存 Owner vault），其 §18 含 17 条决策记录 D-001~D-017。P0 期
Owner 拍板将 ADR 收录延至 P1/S0 期（#313 拍板 #3）；本 ADR 即该收录锚，随 P1+S0 切片（#320）
落地。

## Decision

采纳并固化 program plan §18 的 17 条决策（编号与全文以 plan §18 为准；本节逐条一句收录）：

1. **D-001** Claude 与 Codex 采用全职责、结果对等模型（不预设主次/分工）。
2. **D-002** 现有项目内治理（`sdd/` + `policies/` + `capabilities/`）就是 Kernel，不新增外部层。
3. **D-003** 工具差异由薄 compatibility adapter 吸收（`sdd/adapters/development-agent.md`）。
4. **D-004** `sdd/development-agent.yml` 记录覆盖状态，但不凌驾于治理政策（派生清单层）。
5. **D-005** checker 只判定可机器验证规则，Owner 保留最终决策权。
6. **D-006** Path B（Claude Code 通过插件调用 Codex）排除在本计划范围与验收之外；启用须另立 ADR。
7. **D-007** biz 只读、禁止直连、禁止 secrets 读取的边界不变（ADR-006/009/000）。
8. **D-008** Git 写操作继续 Owner HITL，不设默认放行。
9. **D-009** CI 先以 `--fail-on error` + warning 姿态观察；满足 §11.1 条件并获 Owner 批准后方可升格。
10. **D-010** canonical 审批口径保持 10 项，派生文档不得另增编号。
11. **D-011** 引入 scoped 投影生成器 `agents_sync`（仅 `.agents/skills/` 与 `.codex/config.toml`
    两面），为「不引入全量配置生成器」的唯一豁免；扩面须重新拍板；拒绝第三方同步器。
12. **D-012** 投影产物 commit 入仓；「一键」语义前移作者侧（`sync`）；产物不可手改，反灌走
    `--adopt` + 对应 HITL。
13. **D-013** MCP 投影按 per-server 三档（`project` / `project-with-adr` / `never`，默认 `never`）；
    首批 `project` = github / playwright / serena(transform)；memory×5 = `project-with-adr`
    （独立拍板后落地）；**biz×5 + ssh-manager = `never`**（数据边界执行，非同步缺陷）。
14. **D-014** skills 投影白名单由 manifest `projection` 字段驱动（初始 🟢5 / 🟡21 / 🔴11）；
    8 个冻结 infra 技能首版排除；引用闭包为投影硬前置；投影副本不计入 37 计数 SoT。
15. **D-015** doctor 只读不写 trust（红线）；Codex trust = 每工程师 × 每 worktree 一次的人工步骤。
16. **D-016** drift gate 姿态——skills 面沿 warning→blocking 惯例；**MCP 面 day-1 blocking**
    （信任面不设观察期）；落地时按 `ci-blocking-gate-toggle` 流程留执行记录。
17. **D-017** canonical 10-enum 数量不变（D-010 重申）；扩 `mcp-server-trust-posture-change`
    surface anchor 覆盖派生 `.codex/config.toml`、`.agents/**`、`scripts/sdd/agents_sync.py` 与
    manifest `mcp` / `codex.posture` 段。

**随本 ADR 同步落地的 anchor 扩展（D-017 执行）**：`policies/ai-agent.md` §4 A14 行 surface
anchor 增列上述派生面 + §4 Enforce 机制段注明扩展面的兜底载体（Owner 拍板纪律 + V8/V9 gate +
merge review；非 harness 保护路径）+ `.github/PULL_REQUEST_TEMPLATE.md` A14 行同步。

**P1+S0 落地物**（#320，本 ADR 的第一批执行证据）：manifest + `sdd/adapters/development-agent.md`
+ `scripts/sdd/check_development_agent.py`（V8）+ `scripts/sdd/check_agents_projection.py`（V9）
+ `tests/unit/test_sdd_development_agent.py`（含双发现 canary）+ 根及 4 嵌套 `AGENTS.md` +
各层 `CLAUDE.md` `@AGENTS.md` 导入 + `.claudeignore` `.agents/` 行 + CI warning 首发（V8/V9）。

## Consequences

**正面**：

- 两工具在每一层看到相同 canonical 约束；覆盖状态/审批语义可机器复验（V8），不再靠手写计数。
- 投影机制以「产物入仓 + 作者侧一键 + drift gate」实现 `git pull` 即同步；回退性质完整——删
  `.agents/` + `.codex/config.toml` + 生成器 + gate = 完整回到现状（源从未被改写）。
- 保护面缺口（`.codex/**` / `.agents/**`）由 D-017 anchor 扩展提前闭合。

**负面 / 代价**：

- manifest 37 条目为手工著录，须由 V8 + canary 持续钉住漂移；新增技能必须同步 manifest。
- 投影为过渡期治理装置：生态收敛（Claude Code 原生读 `.agents/skills`）后须主动退役（D-011
  预设一键退役路径，退出成本≈0）。
- Codex 侧必停语义在其 harness 内仅靠 AGENTS.md prose 自守（ADR-035 已接受的 prose-only 风险）。

**中性**：S1（agents_sync + 首批投影）、S2（3 spike 硬前置 + emitter B）、S3（doctor + blocking
转正）按 plan §11 S-轨道推进；4 项独立拍板议题登记在 #312。

## Alternatives considered

- **外部/第二套 Kernel**：拒绝——规则单源在项目内 Kernel（D-002；plan §13）。
- **第三方同步器（Ruler / rulesync / dallay-agentsync 等）**：拒绝——SoT 心智反转、治理集成
  缺位、维护风险（plan §6.4；D-011）。
- **手工全量复制技能正文 / symlink 双份维护**：拒绝——人手双份维护面；生成式字节同一投影 +
  lock + reconcile 的双份维护面为零（plan §6.3 澄清）。
- **Path B 作为核心架构**：拒绝——排除在范围外，另立 ADR（D-006）。
- **10→12 enum 扩编 / Claude 专属 in-tree skill / Codex 制度化第二签**（旧 v3 方案元素）：
  拒绝——v5 已完整替代（plan 修订说明）。

## References

- `plans/[PLAN]_dual-agent-compat.md`（v5；§7 层级 / §9 manifest 契约 / §10 checker / §11
  S-轨道 / §17 Owner Gates / §18 决策记录原文）
- `plans/[PLAN]_dual-agent-compat_p1s0.md` + `plans/[INTAKE]_dual-agent-compat_p1s0.md`（#320
  执行计划与拍板记录）
- 总锚 #312 · P0 执行 #313（closed）· P1+S0 执行 #320
- [[ADR-035_Codex_Full_Development_Participant|ADR-035]]（授权基础）·
  [[ADR-034_HITL_Propose_Decide_Apply_Model|ADR-034]]（HITL 模型）·
  [[ADR-006_Fail_Safe_Reads|ADR-006]] / [[ADR-009_Biz_Domain_As_Primary_Data_Source|ADR-009]]
  （数据边界，不变）
- `sdd/adapters/development-agent.md` · `sdd/development-agent.yml` · `sdd/gates.md` §2（V8/V9）
