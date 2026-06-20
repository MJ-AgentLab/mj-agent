---
type: policy
artifact: data-boundary
state: draft
version: 0.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-06-20
track: shared
ai_visibility: source-of-truth
---

# Policy: Data Boundary

> Phase M0 — 数据-LLM 三原则（ADR-000）native 段 ✓ + 4 项专属必停 native 段 ✓.
> 4 层 SQL 守则总则（继承 ADR-006/009）在 Phase M2 内容填充.

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

- L1 guardrail.py — regex allowlist + SELECT-only + schema + biz_dwd table allowlist
- L1b precheck.py — sqlglot AST（no_select_star / require_time_range / require_limit advisory）
- L2 SKILL.md semantics — 可见表清单（in-source canonical）
- L3 connection.py — `default_transaction_read_only=on` + `lock_timeout=5s` +
  `idle_in_transaction_session_timeout=10s`
- L4 GRANT — upstream `R__analyst_permissions.sql` 显式权限

**why**：LLM 输出本质是 string；不允许 string → 直接 DB 执行；必经过 4 层防御.

## §2 4 层 SQL 守则总则

> TBD: Phase M2 — 详 4 层防御互不旁路的设计 + 配置参数总览
> （继承 ADR-006/009；详 `mj-agent-refactored-structure.md` §"Data boundary" 节 + capability
> `data-agent.safe-sql` `requirements.md`）.

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

> *Phase M0 — 数据-LLM 三原则 + 4 项必停 native；4 层总则 TBD Phase M2.*
