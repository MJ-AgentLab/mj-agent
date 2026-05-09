---
type: standard
domain: WORKFLOW
summary: docs/infrastructure/mcp/ 子目录索引 — mj-agent .mcp.json MCP server 治理领域专属（per ADR-022 C.3.2 + Meta v2.2 §3.7）
owner: 项目负责人
created: 2026-05-09
updated: 2026-05-09
state: active
track: engineering-workflow
---

# MCP 基础设施索引

> **所属目录**：`docs/infrastructure/mcp/`
> **领域专属**落点 per [[../../adr/[ADR]_022_P2_Framework_Enhancements|ADR-022]] §C.3.2 + Meta v2.2 §3.7（与 `docs/infrastructure/git/` / `docs/infrastructure/cicd/` 平行；不在 `docs/rule/` 全局规则目录）
> **建立**：PR-3 of multi-env+DGX+MCP bundle（2026-05-09）

---

## 文档列表

| 文档 | 类型 | 摘要 |
|------|------|------|
| [MJ-Agent MCP Server 治理规范 v1.0](./[STANDARD]_MJ_Agent_MCP_Server_Governance.md) | STANDARD | mj-agent .mcp.json MCP server 治理 — trust posture 分级、credential mode 矩阵、PR-body 强制声明模板（A14 实施细则）、initial 13-server inventory、季度 audit cadence |

---

## 关联入口

- [返回上级索引](../../INDEX.md)
- [[../../rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework|mj-agent 文档治理元框架 v2.2]] §3.7（STANDARD placement）+ §3.10（in-tree SKILL 治理）+ §7.7（A12-A14 PR gates）
- [[../../adr/[ADR]_014_Tri_Track_Documentation_Governance|ADR-014]] §A14（PR gate 来源）
- [[../../adr/[ADR]_022_P2_Framework_Enhancements|ADR-022]] §C.3.2（领域专属 STANDARD placement 决策矩阵）
- [[../../adr/[ADR]_018_Active_Path_Stability|ADR-018]]（active 文件名无 `_vX.Y` 后缀依据）

---

## 派生说明

| 本目录 | mj-system 源 | 主要差异 |
|--------|------------|---------|
| `[STANDARD]_MJ_Agent_MCP_Server_Governance.md` | （mj-system 无对位 STANDARD；mj-agent 原生）| mj-system v5.2 期 .mcp.json governance 隐含在 PR review 经验中，未形成 STANDARD；mj-agent 借落 PR-3 机会显式落地，反向 informant mj-system 后续 STANDARD 演进 |

---

## 演进

- v1.0（2026-05-09）— Initial（PR-3 落地；13-server inventory + A14 约束生效）
- 后续：季度 audit 后由 audit 结论决定 minor/major bump（详见 STANDARD §6 + §8）
