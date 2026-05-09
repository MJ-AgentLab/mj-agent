---
type: adr
domain: SYS
summary: 5 项 P2 framework rule 增强 bundle 决策（mj-system v5.2 派生）：类型专属 frontmatter / STANDARD placement 决策 / ISSUE 编号 / supersedes list / STANDARD 拆分阈值
owner: 项目负责人
created: 2026-05-09
updated: 2026-05-09
state: active
decision: accepted
track: shared
tags:
  - adr
  - documentation
  - framework
  - p2-bundle
  - mj-system-derivation
---

# ADR 022: P2 Framework Enhancements Bundle

## Context

mj-agent Phase C 前序 6 PRs 完成 P0/P1 项目（ADR-017/018/019/020/021）；私有计划 `glistening-shannon` §C.3 还有 5 项 P2 framework 规则增强（mj-system v5.2 既有规则的派生借鉴），单个 PR bundle 落地：

- **C.3.1**：5 类 8 个类型专属 frontmatter 字段（mj-system §4.4 派生）
- **C.3.2**：STANDARD placement 决策矩阵（全局 vs 域专属；mj-system §3.6 派生）
- **C.3.3**：ISSUE 顺序编号 + DomainAbbr 命名（mj-system §4.1 派生）
- **C.3.4**：`supersedes: [list]` 多文档语义（mj-system §4.4 派生；mj-agent 当前已是 list；本次仅文档化）
- **C.3.6**：STANDARD 大型规范拆分阈值（>500 行 + ≥5 主题 + ≥10 跨引用；mj-system §3.6 派生）

每个单独成 ADR 过度（5 个 micro ADR 增加治理噪声）；bundle 单个 ADR-022 + Meta v2.2 / Code_Side v1.1 实落规则文本。

## Decision

### C.3.1 类型专属 frontmatter（落 Code_Side v1.1 §3.4-§3.8）

| Type | Required Fields（state: active/completed 时强制；draft/deprecated 宽松） | Field Description |
|---|---|---|
| RUNBOOK | `last-verified: <YYYY-MM-DD>` | 最近一次按手册验证通过的日期 |
| POSTMORTEM | `severity: P0\|P1\|P2\|P3` + `incident-date: <date>` + `resolved-at: <datetime>` | 事故分级 / 时间戳 |
| ASSESSMENT | `dimensions: [...]` + `period: <daterange>` | 评估维度列表 + 周期（已有现存实例 `[ASSESSMENT]_MJ_System_Git_Conventions_Adoption_v1.0` 含此字段） |
| ISSUE | `priority: P0\|P1\|P2\|P3` + `risk-level: Low\|Medium\|High` | 优先级 + 风险等级（已有 `resolution`；本 ADR 加这两个） |

### C.3.2 STANDARD placement（落 Meta v2.2 §3.7）

| 范畴 | 路径 | 判定 |
|---|---|---|
| **全局规则** | `docs/rule/` | 跨领域、跨服务、跨工具的项目级规范 |
| **API 专属** | `docs/api/` | 跨服务的 API 约定 |
| **领域专属** | `docs/infrastructure/<domain>/` | 与具体技术领域绑定（database / docker / git / cicd / 等） |

**就近原则**：领域专属 STANDARD 与对应 GUIDE/RUNBOOK/SPEC 同目录扁平。

mj-agent 当前 STANDARD 全部跨领域，落 `docs/rule/`，无域专属候选；规则订立但**不做**迁移。

### C.3.3 ISSUE 顺序编号 + DomainAbbr（落 Meta v2.2 §4.5）

`docs/issues/` 文件命名格式：

```
[ISSUE]_NNN_DomainAbbr_Description.md
```

- `NNN`：3 位顺序编号（001 起；与 ADR 编号独立）
- `DomainAbbr`：mj-agent domain 缩写（per Meta §9：`SYS / AGENT / DATA / SKILL / PROMPT / GUARDRAIL / OPS / INTEGRATION / WORKFLOW / ...`）
- `Description`：英文描述，`_` 连接，无空格

`docs/issues/` 当前空；订立规则不做迁移。

### C.3.4 `supersedes: [list]` 多文档语义

mj-agent 当前 `supersedes` 字段已是 list（见 ADR-011/017/018/019/020/021 frontmatter）；mj-system §4.4 同模式。本 ADR **仅文档化**：明确 `supersedes` 接受 list（非单一 string），用于拆分场景（1 doc → N，每个新 doc supersedes 旧；旧 doc replaced-by 是 list）。

`scripts/check_frontmatter.py` 已隐式支持 list（YAML 自动解析）；本 PR 不改 schema，仅在 Meta v2.2 §4.x 加文档化注释。

### C.3.6 STANDARD 拆分阈值（落 Meta v2.2 §3.8）

当 STANDARD 满足以下**全部**条件时，拆分为多份单一主题 STANDARD：

| 条件 | 阈值 |
|---|---|
| 行数 | >500 |
| 主题章节 | ≥5 个独立 |
| 跨文件引用 | ≥10 处 |

**判定示例**（mj-agent 当前最大 STANDARD）：

- Meta v2.2: ~610 行（>500 ✓）/ 11 章（≥5 ✓）/ 多处引用（≥10 ✓）— **三条件全满足**
- 但 Meta v2.2 是单一主题（"文档治理元框架"），强行拆分会损害一致性 —— **不立即拆**

规则订立为 Phase D+ 决策依据；当前不触发拆分。mj-system v5.2 实际触发：Flyway / SQL / N8N 等大型 STANDARD 拆为子 STANDARD（mj-agent 无对应规模）。

## Consequences

### 正面

1. **类型专属 frontmatter 落地** — RUNBOOK / POSTMORTEM / ASSESSMENT / ISSUE 模板补全 frontmatter；未来 retention / 复盘 / 评估统计有数据基础
2. **STANDARD placement 决策矩阵显式** — 未来引入 docker / database 等域 STANDARD 时直接 cite §3.7
3. **ISSUE 编号约定提前订立** — `docs/issues/` 首个 ISSUE 创建时格式确定
4. **`supersedes` list 语义清晰** — 拆分场景的 frontmatter 表达力提升
5. **拆分阈值显式** — Meta v2.2 自身 borderline；规则订立为未来决策依据
6. **mj-system v5.2 派生 P2 项 6/6 完成**（含本 ADR）— 双向兼容程度最高

### 负面

1. **类型专属字段对现有 RUNBOOK / POSTMORTEM / ISSUE 文件**（如有）需回填 — mj-agent 当前 docs/runbook/ 1 文件 / docs/postmortem/ 0 / docs/issues/ 0；少量回填
2. **check_frontmatter.py 加 type-conditional 复杂度** — 但 active/completed 强制 + draft/deprecated 宽松权衡合理
3. **ADR-022 是 bundle ADR**（5 决策合一）— 治理纯度略损；权衡：5 micro ADR 噪声更大

### 中性

1. **不 supersede 任何 ADR** — 与 ADR-011/017/018/019/020/021 全部 sustained
2. **本 PR 自身按 ADR-017 §5.9 判定**：trigger #1-4 ❌；反例 #5 字段补充 ✅（Meta §3.7/§3.8/§4.5 in-place 加段；Code_Side §3.4-§3.8 字段补充；§5.9 反例 #5）→ 不触发 archive ceremony
3. **mj-agent 实际 STANDARD 规模** — Meta v2.2 borderline 拆分阈值；Phase D 评估是否实施

## Alternatives considered

### A. 5 个 micro ADR（022-026）

**拒绝原因**：每个 P2 项目都是小规则（10-50 行 ADR）；5 个 ADR 增加 docs/adr/ 噪声。bundle 单 ADR-022 是治理实用主义。

### B. 不引入 ADR，仅 Meta + Code_Side 内嵌规则

**拒绝原因**：违反 mj-agent ADR governance pattern（每个治理决策有 ADR 记录）；缺 mj-system 派生论证 + Alternatives 表达。

### C. 拆为 Phase C-4 + Phase C-5（C.3.1 单独 PR）

**拒绝原因**：C.3.1 是最大的 P2 项（~50 行 frontmatter 表 + check_frontmatter 改 30 行），仍小于 C-1a/C-1b 主 PR；bundle 一个 PR 节省协调成本。Phase D 是 EVAL framework 等更大工作，与 C-3 P1 + C-4 P2 解耦。

### D. 推迟到 Phase D 与 EVAL framework 一起

**拒绝原因**：Phase D EVAL framework 涉及 A8/A11 transitional waiver 关闭（重大门禁切换）；P2 framework 规则与 EVAL 正交；解耦避免相互拖累。

## References

- 派生源：mj-system v5.2 `[STANDARD]_Documentation_Management_Framework.md` §3.6 / §4.1 / §4.4
- 落地：[[../rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta v2.2]] §3.7 / §3.8 / §4.5；[[../rule/[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework|Code_Side v1.1]] §3.4 / §3.5 / §3.7 / §3.8；`scripts/check_frontmatter.py` type-conditional 校验
- 关联 ADR：ADR-011/017/018/019/020/021 全部 sustained；本 ADR 与之互补不重叠
- 私有评估：plan §C.3.1 / §C.3.2 / §C.3.3 / §C.3.4 / §C.3.6
- 关联 GitHub Issue：[#88](https://github.com/MJ-AgentLab/mj-agent/issues/88)
- 后续（Phase D 范畴）：archived 物理归档 / find_stale_docs.py 完整版 / EVAL framework / 模板补全实测
