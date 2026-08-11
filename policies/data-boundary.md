---
type: policy
artifact: data-boundary
state: draft
version: 0.2
owner: ranzuozhou
created: 2026-05-20
updated: 2026-08-11
track: shared
ai_visibility: source-of-truth
---

# Policy: Data Boundary

> 数据-LLM 三原则（ADR-000）✓ · **4 层 SQL 守则总则 ✓**（v0.2 / #482 内容填充）· 4 项专属必停 ✓.
> 各层的 REQ 级验收标准与 BDD 例在 capability `data-agent.safe-sql`；本 policy 只定命名口径、
> 不旁路不变式与配置参数总览，不复述实现细节.

## §1 数据-LLM 边界三原则（ADR-000；native）

mj-agent 的核心安全主线 —— 后续所有安全相关决策的理论基础.

### 原则 1 — 最小必要出网（minimal egress）

LLM 调用**仅**在响应用户问题时触发；不在数据加载 / ETL / 后台批处理阶段触发.

- ✅ 用户问"上月 product interface 调用量趋势" → 触发 1 次 LLM agent run
- ❌ 凌晨定时 catalog refresh → 不应触发 LLM
- ❌ biz pg 健康检查 → 不应触发 LLM

**why**：LLM 调用 ≈ 数据出网；出网频率与业务问题数量绑定，不与 ETL / 后台节奏绑定.

### 原则 2 — 通道隔离（channel isolation）

biz 数据访问（read-only analyst grant）与 LLM 出网走**不同连接池 + 不同凭据**：

| 通道 | 凭据 | 网络出口 |
|---|---|---|
| biz pg | `analyst` PostgreSQL role（read-only） | `mj-system-backend-network` 内网（ADR-008） |
| LLM | `ARK_API_KEY` / `LLM_API_KEY` | 公网（ark）或 DGX 内网（local-openai-compat） |

`src/mj_agent/integrations/mj_system_db.py` 与 `src/mj_agent/llm.py` 不共享 connection pool /
credential / network egress；secrets 在 `config/secrets.enc` 内分键存放（ADR-030）.

**why**：通道隔离避免凭据 spillover；biz 数据出网必经"工具中介"层（原则 3），不可绕过.

### 原则 3 — 工具中介（tool mediation）

LLM **不直接握 SQL**，所有数据访问经 `src/mj_agent/tools/sql/{guardrail,precheck,execute}.py`：

- L1 guardrail.py — regex 单句 / SELECT-only / blocked-keyword + sqlglot AST schema + biz_dwd table allowlist
- L1b precheck.py — sqlglot AST（no_select_star / require_time_range / require_limit advisory）
- L2 SKILL.md semantics — 可见表清单（in-source canonical）
- L3 `integrations/mj_system_db.py` — `default_transaction_read_only=on` + `lock_timeout=5s` +
  `idle_in_transaction_session_timeout=10s`
- L4 GRANT — upstream `R__analyst_permissions.sql` 显式权限

**why**：LLM 输出本质是 string；不允许 string → 直接 DB 执行；必经过 4 层防御.

## §2 4 层 SQL 守则总则

分层清单见 §1 原则 3。**每层的 REQ 级验收标准 + BDD 例**在 capability `data-agent.safe-sql`
（`requirements.md`：REQ-001 = L1 / REQ-002 = L1b / REQ-003 = L3 / REQ-004 = L4；架构图见
`design.md` §3）。本节**不复述**那些细节，只定 policy 级的三件事：命名口径、不旁路不变式、
配置参数总览。

### §2.1 命名口径（canonical = ADR-006）

**共 4 层**：`L1` guardrail · `L2` SKILL.md 语义 · `L3` 连接 · `L4` 角色。
`precheck.py`（sqlglot AST 静态规则）是 L1 之后追加的**子层，记作 `L1b`** —— 它**不占 `L2`
位号**，`L2` 始终指 in-source SKILL.md 的可见表语义（ADR-006 §Decision 的四层防御表）。任何把 precheck
称作 "L2" 的表述，以本节 + ADR-006 为准。

### §2.2 不旁路不变式（本节是本 policy 的规范部分）

"4 层互不旁路"不是四道并排的墙，而是下面 4 条不变式。**任一条被打破，整条安全主线的论证即
失效**；改动触及任一条 → 按 §4 走 `sdd/workflows/cross-capability-change.md` + HITL。

**I1 — LLM 生成的 SQL 文本只有一个入口。** `execute_sql()` 内 L1 → L1b **无条件前置**于任何
数据库接触（`is_safe_select` 不过即 `raise ValueError`；`precheck_sql` 有 P0 error 亦 `raise
ValueError`），没有旁路分支、没有可关闭的开关、没有"可信来源"豁免。
*可检查*：`grep -rn "with readonly_cursor()" --include=*.py src/` 恰有 **4** 个调用点 ——
`tools/sql/execute.py`（唯一承载 LLM 生成 SQL **文本**者，受 L1+L1b 前置）·
`tools/sql/introspect.py` ×2 · `server/cli.py` ×1。后三处执行的是**模块常量 SQL + 绑定参数**，
LLM 输入只在经 `settings.is_table_allowed()` 校验后进入**参数位**，永不拼进 SQL 文本。

**I2 — biz 域连接只有一个出口。** biz 连接一律由 `integrations/mj_system_db.py:get_pool()`
单例产出（`atexit` 关闭），L3 的三个 `-c` 开关内嵌在该 DSN 里。仓内其余 `psycopg` 使用方
（`memory/checkpointer.py`、`server/cli.py` 的 memory 探针）连的是 **mj-agent 自有 memory 库**，
属另一 capability，**不在 ADR-006 的 biz 边界内，不得与之混谈**。

**I3 — 失败方向按层分化，且该不对称依赖 L3/L4 仍然权威。**

| 层 | 静态验证失败时 | 依据 |
|---|---|---|
| L1 | **fail-closed** — sqlglot 解析不了就直接拒（`_qualified_refs` 返回 `None` → reject） | allowlist 是**安全**边界；验不了就不放行 |
| L1b | **fail-open** — 降级为一条 `sqlglot_parse_failed` warning 并 `ok=True` 放行 | 它的规则是**质量**规则，最终验证者是数据库 |

L1b 的 fail-open **只在 L3/L4 仍然权威时才是安全的**：被放过的语句仍处在只读事务 + `analyst`
只读 GRANT 之下，最坏结果是"一条低质量但只读的查询"。因此**削弱 L3 或 L4，会把 L1b 的
fail-open 变成真漏洞**，其风险等级等同于放宽 L1/L1b。
⚠ 载体现状（如实记录）：L1/L1b 所在的 `tools/sql/{guardrail,precheck}.py` 在
`.claude/settings.json` `permissions.ask` 列表内（§3），而 **L3 所在的
`integrations/mj_system_db.py` 不在**——该面目前只靠本节纪律 + 合并审查兜底，无 harness 门、
也无审批类 CI gate（与 `policies/docker-runtime.md` §4 的 Dockerfile 供应链面同属一档）。

**I4 — L4 是权威层，且不由 mj-agent 掌握。** 即便 L1/L1b/L3 全部失效，`analyst` 角色也没有写
权限，`statement_timeout=60s` 由角色侧 `ALTER ROLE` 设定 —— **应用侧改不动**。L4 归上游业务系统
所有（`R__analyst_permissions.sql`）；mj-agent 侧只做两件事：把 `QueryCanceled` 捕获成带中文
自纠提示的 `RuntimeError`，以及 `introspect.list_biz_tables()` 按
`information_schema.table_privileges` 过滤做 GRANT 可见性 sanity check。**这也是"L4 优先"的
由来** —— 应用层拦截只为提前给出可读错误，不是安全的最后依据（ADR-006 §Alternatives considered：
"仅用应用层校验（L1+L2）：拒绝——应用层 bug 会直接暴露底层权限"）。

### §2.3 配置参数总览

| 参数 | 生效值 | 设定位置 | 层 | 备注 |
|---|---|---|---|---|
| `BIZ_ALLOWED_SCHEMAS` | `biz_dws`, `biz_dwd` | `config.py`（env 可覆盖，逗号分隔） | L1 | 扩容 = 扩大可达面 → 走 §4 |
| `BIZ_ALLOWED_DWD_TABLES` | `dwd_dim_product_interface`, `dwd_dim_institution` | `config.py` | L1 | `biz_dws` 为 wildcard；`biz_dwd` 白名单外一律拒 |
| `SQL_MAX_ROWS` | `500` | `config.py` | 应用 | `execute_sql` 取 `max+1` 行以判 `truncated` |
| `default_transaction_read_only` | `on` | `_dsn()` 的 DSN `options` | L3 | |
| `lock_timeout` | `5000`（ms） | 同上 | L3 | |
| `idle_in_transaction_session_timeout` | `10000`（ms） | 同上 | L3 | |
| 连接池 | `min_size=1` / `max_size=4` / `autocommit=False` / `row_factory=dict_row` | `get_pool()` | L3 | `readonly_cursor()` 在 `finally` 必 `rollback()` |
| `search_path` | **有意不设** | — | L3 | 表引用必须 schema-qualified，由 L1 强制 |
| `statement_timeout` | `60s` | **上游** `ALTER ROLE analyst`（`R__analyst_permissions.sql`） | L4 | 客户端**有意不设**（`_dsn()` docstring 明写） |
| `SQL_STATEMENT_TIMEOUT_SEC` | `60` —— **inert** | `config.py` + `.env.example` | — | ⚠ **全仓无读取方**；真正的 60s 来自上一行的 L4 设定。**改这个 env var 不产生任何效果**；处置（接线 or 删除）另立单 |

> 本表与实现冲突时**以实现为准**，并同步修正本表 —— 散文治理表不是 ground truth
> （同 `policies/archive.md` 脚注判例）。

## §3 4 项 mj-agent 专属必停（native；与 `sdd/gates.md` §4 同步）

任一修改触发以下文件必须 HITL（**逐写拍板，不可静默绕过；不在 CI gate 自动化覆盖范围**）：

| Hard Stop | 路径 | 触发原因 | 工作流 |
|---|---|---|---|
| sql-guardrail-relax | `src/mj_agent/tools/sql/{guardrail,precheck}.py` | L1/L1b 防御层；放宽 = 安全主线动摇 | `sdd/workflows/cross-capability-change.md` |
| runtime-skill-content-change | `src/mj_agent/skills/*/SKILL.md` body | LLM 行为契约 | `mj-agent-runtime-skill-doc-improve` skill（propose+拍板+apply） |
| prompt-version-bump | `src/mj_agent/prompts/system.md` version + body | 系统提示词行为边界 | `mj-agent-runtime-prompt-version-bump` skill（propose+拍板+apply） |
| biz-catalog-sync | `src/mj_agent/biz_catalog/qcm_catalog.yaml` | mirror 上游业务系统数据字典 | `mj-agent-runtime-biz-catalog-sync` skill（propose+拍板+apply） |

**执行机制**（ADR-034；拍板即落盘——AI 提议 + Owner 拍板 + AI 落盘，不再要求 Owner 手动转写）：

1. **`ask` 权限门（逐写拍板）**：上述 4 路径在 `.claude/settings.json` `permissions.ask`
   列表（precedence `deny` > `ask` > `allow`，覆盖顶部 blanket `Edit`/`Write` allow）——AI 对其
   Edit/Write 在交互模式触发**逐写权限 prompt**（= Owner 拍板）；批准后 AI 落盘。
   （原 `deny` 物理硬锁已于 ADR-034 解除。）⚠️ **注**：`.claude/scripts/guard-git-workflow.ps1`
   PreToolUse hook 仅 `matcher=Bash` 且只管 G1/G2 git 命令，**不**拦上述 4 路径的 Edit/Write——
   本 4 面的门来自 settings.json `ask`，非该 hook。
2. **Runtime skill 工作流**：`.claude/skills/mj-agent-runtime-*/SKILL.md` 先做 propose diff +
   impact 反扫，**Owner 拍板后**由 skill 经 `ask` 门落盘（`## Anti-patterns` 段写"❌ 未经
   Owner 拍板就落盘 / ❌ 跳过 impact 分析直接改"；per A12 description gate）.
3. **A12-A14 PR gate（合并审查兜底）**：PR review 阶段 reviewer 必须 check 4 项专属必停清单 +
   A13 settings allowlist diff；落盘后的合并审查是物理硬锁解除后的主兜底层.

## §4 跨能力变更触发条件

数据-LLM 边界三原则相关变更（即使本文件不修改）→ 触发本 policy；必走
`sdd/workflows/cross-capability-change.md` workflow + HITL.

典型场景：

- 新 tool 引入（如新 chart 工具直接访问 biz pg）→ 触发原则 2（通道隔离）的 review
- LLM provider 切换（ark ↔ local-openai-compat）→ 原则 2 通道复核 + endpoint 健康探针
- biz_dwd 可见表 allowlist 扩展 → 原则 3 工具中介的 L1 配置变更 + ADR-006 reference

---

> *`state: draft` — §1-§4 均已是 live SoT（§2 于 v0.2 补齐，本文件不再有待填充节）。*
>
> *v0.2（2026-08-11）：#482 — 填 §2「4 层 SQL 守则总则」，关闭本文件在
> `M6-FU-POLICIES-TBD-SWEEP` 中的唯一 TBD 块。内容全部从实现本体重新取证，未照抄任何散文表：
> §2.1 按 ADR-006 钉死 `L2` = SKILL.md 语义（`precheck.py` 是 `L1b` 子层，不占 `L2` 位号）；
> §2.2 把"互不旁路"落成 4 条可检查的不变式，其中 I1 的单一入口由
> `grep -rn "with readonly_cursor()" --include=*.py src/` 恰 4 命中佐证，I3 记录了 L1
> fail-closed 与 L1b fail-open 的**方向不对称**及其对 L3/L4 权威性的依赖；§2.3 汇总 10 项配置
> 参数。**两处如实记录**：(a) L3 的 `integrations/mj_system_db.py` 不在 `permissions.ask` 内，
> 该面无 harness 门；(b) `SQL_STATEMENT_TIMEOUT_SEC` 是 inert 配置项——`config.py` 声明 +
> `.env.example` 暴露但全仓无读取方，真正的 60s 来自 L4 的 `ALTER ROLE`，改它不产生任何效果
> （处置另立单）。同批修正 §1 原则 3 的 `L3 connection.py` —— 该文件不存在，实为
> `integrations/mj_system_db.py`；并删除 TBD 块里指向 `mj-agent-refactored-structure.md`
> 的悬空引用（仓内无同名文件，只有 `learning/` 下的 `[LEARNING]_*` 派生件）。
> `state` 不动：内容填充不构成 live-kernel-home 意义上的操作必要性（per #480 /
> `sdd/lifecycle.md` §4.1）。*
