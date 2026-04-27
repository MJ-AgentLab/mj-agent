---
type: adr
domain: GUARDRAIL
summary: biz 库访问用只读账号 + SQL guardrail middleware 双层保护，四层防御
owner: 项目负责人
created: 2026-04-24
updated: 2026-04-24
state: active
decision: accepted
---

# ADR-006: Fail-Safe Reads

## Context

mj-agent 面向内部分析师，访问 mj-system biz 域的汇总数据。
两个风险必须规避：
1. **误写**：LLM 生成的 SQL 意外含有 `UPDATE`/`DELETE`/`DROP`，污染或损毁业务数据
2. **越权读**：越过 biz_dws 边界读到 biz_ods 原始数据或 ops_* 运维数据

单层保护（例如"在 prompt 里强调不要写 DML"）不够——LLM 的行为在 long tail 中必然偏离指令。
需要**纵深防御**：即便 LLM 生成恶意或错误 SQL，至少要有一层能拦住。

## Decision

采用**四层防御**体系（实现了 [[ADR]_000_Data_LLM_Boundary_Principles|ADR-000]] 的 P3 工具中介原则）：

| 层 | 机制 | 实现位置 |
|---|---|---|
| **L1 Guardrail** | 正则校验：单语句、只读关键词白名单（SELECT / WITH）、schema 前缀白名单（`biz_dws.` / `biz_dwd.` 两个 dim 表） | `src/mj_agent/tools/sql/guardrail.py` |
| **L2 语义** | SKILL.md 明确列出可见表清单，引导 LLM 写合法 SQL | `src/mj_agent/skills/*/SKILL.md` |
| **L3 连接** | psycopg 连接字符串设 `default_transaction_read_only=on`，DML 在连接层会失败 | `src/mj_agent/integrations/mj_system_db.py` |
| **L4 角色** | mj-system 侧的 `analyst` PostgreSQL 角色只 GRANT 读权限 + `statement_timeout=60s` | mj-system `R__analyst_permissions.sql` |

四层**任意一层**拦截都能阻止越权，不依赖上层单点有效。

## Consequences

**正面**
- LLM 即便完全失控，也无法修改业务数据（L3、L4 是物理边界）
- 越权读取在 L4 层被数据库角色权限拦截，errors 可审计
- 新成员可以明确知道"这是最后一道防线，别指望在它之前的代码足够严"

**负面**
- 每次 SQL 执行经过四层校验，有固定延迟（实测 < 5ms，可接受）
- L1 的正则较为保守，某些复杂合法 SQL（例如动态窗口函数）可能被误拒；需要靠 SKILL.md 引导 LLM 写更朴素的等价形式
- L2 与 L4 的表清单必须保持同步，mj-system schema 变更时需要触发契约同步（ADR-011 biz schema 三层同步机制）

**中性**
- Guardrail 的细节规则本身不是 ADR，将在 `[STANDARD]_SQL_Guardrail_Rules_v1.0.md`（Phase 0.5）里明确

## Alternatives considered

**仅用数据库角色权限（L4）**：拒绝——应用层没有错误提前拦截，LLM 生成失败后只能通过数据库错误字符串反馈，用户体验差且日志不易归类。

**仅用应用层校验（L1+L2）**：拒绝——应用层 bug 会直接暴露底层权限。

**四层（本 ADR 选项）**：采纳。

## References

- [[ADR]_000_Data_LLM_Boundary_Principles|ADR-000]]（P3 工具中介）
- [[ADR]_009_Biz_Domain_As_Primary_Data_Source|ADR-009]]（L2/L4 白名单的数据范围由 ADR-009 定义）
- `src/mj_agent/tools/sql/guardrail.py`、`execute.py`、`introspect.py`
- `src/mj_agent/integrations/mj_system_db.py`
