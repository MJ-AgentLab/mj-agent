---
type: adr
domain: INTEGRATION
summary: mj-agent 仅通过只读账号访问 biz 域，不访问 ODS/DWD 原始层
owner: 项目负责人
created: 2026-04-24
updated: 2026-04-24
state: active
decision: accepted
track: shared
---

# ADR-009: Biz Domain as Primary Data Source

## Context

上游业务系统数据仓库有四层结构：ODS（原始层）、DWD（明细层）、DWS（汇总层）、ADS（应用层）（"上游业务系统"术语见 [[../glossary/upstream_business_warehouse|glossary]]）。
mj-agent 需要选择一个数据边界作为主要访问层。各层的特点：

| 层 | 粒度 | 语义稳定性 | 规模 | 可解释性 |
|---|---|---|---|---|
| ODS | 原始 | 低（上游格式漂移直接暴露） | 最大 | 低 |
| DWD | 清洗后的明细 | 中 | 大 | 中 |
| DWS | 按主题的汇总（带维度） | 高 | 适中 | 高 |
| ADS | 面向应用的小结果集 | 高，但用途锁死 | 小 | 最高 |

分析师场景需要**灵活维度探索 + 较稳语义**，DWS 天然匹配。ODS/DWD 暴露内部 schema 给 LLM 违反 [[decisions/ADR-000_Data_LLM_Boundary_Principles|ADR-000]] 的 P1（最小必要出网）——那些表有大量内部 tracking 字段与半结构化 payload。ADS 语义被锁死，不适合交互式分析。

此外，DWD 层有少数稳定的维度表（如产品接口、机构），分析师做 DWS join 时经常需要。

## Decision

mj-agent 的数据访问边界：

| schema | 访问 |
|---|---|
| `biz_dws.*` | **全部可读** |
| `biz_dwd.dwd_dim_product_interface`、`biz_dwd.dwd_dim_institution` | **可读**（仅这两张维度表） |
| 其余 `biz_dwd.*`、`biz_ods.*`、`biz_ads.*` | **不可读** |
| `ops_*.*` | **不可读** |

可读范围由 **上游业务系统的 `analyst` PostgreSQL 角色** GRANT 精确限定（见 [[decisions/ADR-006_Fail_Safe_Reads|ADR-006]] 的 L4）。
mj-agent 应用层的 SKILL.md 清单与 guardrail schema 白名单须与 L4 保持同步；自动同步机制规划在 Phase 2（[[../../plans/mj-agent-roadmap-v1.6|roadmap v1.6]] §4.4 "schema 自动同步"）。Phase 1 阶段，对齐通过 `tests/contract/*` 防守性 fail-then-manual-fix + manual review 维持。

## Consequences

**正面**
- 访问路径的复杂度收敛到 DWS：skill 作者与 LLM 面对的是人类可理解的业务指标表
- 违反 ADR-000 的面被显著压缩——ODS/DWD 的内部字段永远不会出现在 LLM 上下文中
- DWS 天然有 `prev_*` 与 `*_diff / *_rate` 列，同比环比无需 LLM 二次计算
- biz_dws 的 schema 变更由上游业务系统治理，变更频率可控

**负面**
- 分析师偶尔需要的 DWD 明细下钻不可行，必须回到上游业务系统团队加字段到 DWS 或申请临时 ad-hoc 查询
- 两张 biz_dwd 维度表是"例外开口"，数量上升时需要重新评估边界

**中性**
- biz_dws 全表可读，意味着所有现有 DWS 表的添加、删除都会影响 mj-agent；biz schema **自动同步机制**规划在 Phase 2（见 [[../../plans/mj-agent-roadmap-v1.6|roadmap v1.6]] §4.4）。Phase 1 阶段通过静态 `qcm_catalog.yaml` 镜像 + `tests/contract/*` 防守性 fail-then-manual-fix + manual review 维持对账

## Alternatives considered

**允许 DWD 全读**：拒绝——DWD 包含未聚合的明细行，违反 ADR-000 的 P1；且 DWD schema 经常在 ODS 结构变更时被迫修改。

**仅允许部分 DWS 表**：保留未来按团队/角色细分的可能（Phase 4 RBAC），但 Phase 0-2 统一全读，避免 skill 作者的维护负担。

**通过 ADS 层访问**：拒绝——ADS 按特定应用场景预聚合，无法支持开放式分析。

## References

- [[decisions/ADR-000_Data_LLM_Boundary_Principles|ADR-000]]（P1 最小必要出网）
- [[decisions/ADR-006_Fail_Safe_Reads|ADR-006]]（L4 角色权限实现本 ADR 的数据范围）
- **Future work** — biz schema 自动同步机制规划在 Phase 2（[[../../plans/mj-agent-roadmap-v1.6|roadmap v1.6]] §4.4）；Phase 1 通过 `qcm_catalog.yaml` + `tests/contract/*` + manual review 维持
- `src/mj_agent/skills/query-writing/SKILL.md`（当前 skill 的表清单对齐此 ADR）
- 上游业务系统 `R__analyst_permissions.sql`（L4 GRANT 定义）
