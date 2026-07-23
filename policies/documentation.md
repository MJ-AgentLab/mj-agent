---
type: policy
artifact: documentation
state: active
version: 1.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-06-23
track: shared
ai_visibility: source-of-truth
---

# Policy: Documentation

> **Kernel home note (M6 PR4a)**: 本 policy 是文档治理的 **kernel 真相源**。它收纳了
> 三轨 STANDARD（Meta_Framework / Code_Side / Agent_Side / HITL_Prompt）中的**文档治理**内容：
> 12 类文档分类、`track` frontmatter 字段、PR 门禁 A1-A6 + OB1-OB5、frontmatter schema
> （含类型专属字段）、CLAUDE.md sync allowlist。这些规则的 canonical home **自本 policy 起**就是这里。
>
> 在 M6 PR4 archive ceremony 落地前，源 STANDARD 仍 `state: active` 留在 `docs/rule/` 作为
> **历史源**；PR4 把它们整体迁入 `archive/rule/` + `state: deprecated`，living 引用同步重指本 policy。
> 详见 [[decisions/ADR-031_Spec_Anchored_Refactor|ADR-031]] §Phase M6 + [[policies/archive|policies/archive]] §4。
>
> **不在本 policy 范围**（cross-ref，不重复 port）：
> - A7-A11（agent-side SKILL/PROMPT/EVAL/CONTRACT 专属门禁）→ `sdd/adapters/runtime-skill.md`
>   + `sdd/adapters/prompt.md` + [[policies/ai-agent|policies/ai-agent]] §4 canonical 10-enum（surface-anchored 子集）
> - A12-A14（engineering-workflow `.claude/**` + `.mcp.json` 专属门禁）→ `sdd/adapters/claude-code-skill.md`
>   + [[policies/ai-agent|policies/ai-agent]] §4（`mcp-server-trust-posture-change`）+ Meta §7.7（历史源）
> - EVAL authoring 完整规范（4 子类 + body 八段）→ [[decisions/ADR-024_Eval_Framework_Spec|ADR-024]]
>   + Agent_Side §4（历史源；Phase E EVAL framework 落地前不迁入本 policy）
> - 归档触发量化 / active-path-stability → [[policies/archive|policies/archive]] §1（Meta §5.9 / §4.4 的迁入目标）
> - 17-stage HITL 执行闭环 → [[policies/ai-agent|policies/ai-agent]]（HITL_Prompt §1/§4.* 的迁入目标）

## §1 docs-as-contract 原则

文档治理把 canonical 文档当作**契约**而非附属说明。三条 track-specific 失败模式区分了治理强度：

| Track | 失败模式 | 含义 | Reviewer 强度 |
|---|---|---|---|
| **Track A（code）** | **响亮失败** | compile / test / deploy break；问题立即可见 | SWE Reviewer 一名充分 |
| **Track B（agent）** | **沉默失败** | 错答案 / 幻觉 / 业务决策漂移；每次消费 SKILL/PROMPT body 的 LLM 调用都是生产输出 | Domain Expert / Prompt Engineer **+** SWE（≥ 2 reviewer） |
| **Track C（engineering-workflow）** | **流程漂移** | HITL 跳过 / 错 skill / settings 退化；与 A 响亮、B 沉默均不同 | Tooling Reviewer + SWE |

派生原则（自 Meta §1 + Code_Side §1）：

| 原则 | 说明 |
|---|---|
| 真实资产优先 | 文档描述真实存在的代码 / 配置 / 流程；不为未来占位空写 |
| 目录即职责 | 物理路径决定治理归属（见 §3 path-to-track 决策树） |
| 真相源最小化 | 每条规则单一 canonical home；其他位置 cross-ref 不复制 |
| 代码-文档双向追溯 | 代码侧 ADR / SPEC 的决策应在同 PR 内同步实施 |
| in-source 治理 | `src/mj_agent/{skills,prompts}/**` 的 SKILL.md / system.md body 字面被 LLM 消费——字面修改即行为修改 |
| 三轨分轨 | A 代码侧 / B 智能体侧 / C 工程流程；plugin loader 边界尊重（Track C 资产不经 mj-agent Python loader） |

## §2 文档类型分类（12 类 canonical）

> 源：Meta §3（类型与目录）+ Code_Side §0（8 类代码侧）+ Agent_Side §0（4 类智能体侧）。
> **类型枚举不变**（12 类 canonical）；这是与 SDD capability-package ontology（spec / contract /
> tasks / runbook / evidence）**正交的另一轴**——本分类治理 `docs/**` + in-source canonical 文档卫生。

### §2.1 12 类 canonical 类型 + 默认 track

| 类型 | 默认 track | 由哪个深度规则治理 |
|---|---|---|
| GUIDE | code | Code_Side §3.1 |
| ADR | shared（按主题决定） | Code_Side（code-ADR）/ Agent_Side（agent-ADR）/ engineering-workflow-ADR（如 ADR-014/016） |
| SPEC | shared | 同 ADR |
| RUNBOOK | code | Code_Side §3.4（见 §6.2 类型专属 frontmatter） |
| POSTMORTEM | shared | 按事件类型 |
| STANDARD | shared | Meta（跨轨）/ Code_Side（代码规约）/ engineering-workflow（如 HITL_Prompt） |
| ISSUE | shared | 按主题（见 §6.2 类型专属 frontmatter + §2.4 命名约定） |
| ASSESSMENT | shared | 按评估对象（见 §6.2 类型专属 frontmatter） |
| **SKILL** | **agent**（默认）/ **engineering-workflow**（路径 `.claude/skills/**` 时） | Agent_Side §2（in-source 13 字段）/ `sdd/adapters/claude-code-skill.md`（in-tree ADR-013 native 2 字段） |
| **PROMPT** | **agent** | Agent_Side §3 / `sdd/adapters/prompt.md` |
| **EVAL** | **agent** | Agent_Side §4 / [[decisions/ADR-024_Eval_Framework_Spec|ADR-024]] |
| **CONTRACT** | shared | Agent_Side（agent-facing tool）/ Code_Side（cross-service） |

**8 类代码侧**（Code_Side §0；默认 `track: code`）：GUIDE / ADR-code / SPEC-code / RUNBOOK /
POSTMORTEM-code / STANDARD-code / ISSUE-code / ASSESSMENT-code。
**4 类智能体侧**（Agent_Side §0；默认 `track: agent`）：SKILL（in-source）/ PROMPT / EVAL /
CONTRACT（agent-facing tool）。

### §2.2 目录归属优先级（Meta §3.5）

新建 canonical 文档按以下优先级选目录（高序号让位低序号）：

0. **Engineering-workflow 专属**：进入 `.claude/skills/<name>/`、`.claude/scripts/`、
   `.claude/hooks/`、`.claude/settings.json`、`.mcp.json`（不进入 `docs/` 或 `src/`）
1. Agent 专属：`src/mj_agent/{skills,prompts}/**`
2. 子系统专属
3. 基础设施专属
4. 跨子系统 API 约定
5. 跨领域通用规则（`docs/rule/`）
6. 跨领域操作指南

### §2.3 STANDARD 归属：全局规则 vs 领域专属（Meta §3.7）

| 范畴 | 路径 | 判定 |
|---|---|---|
| **全局规则** | `docs/rule/`（M6 后：本 policy + `sdd/` + `policies/`） | 跨领域、跨服务、跨工具的项目级规范 |
| **API 专属** | `docs/api/` | 跨服务的 API 约定（mj-agent 当前空） |
| **领域专属** | `docs/infrastructure/<domain>/` | 与具体技术领域绑定（database / docker / git / cicd）；与该域 GUIDE / RUNBOOK / SPEC 同目录扁平 |

**就近原则**：领域专属 STANDARD 与对应 GUIDE/RUNBOOK/SPEC 同目录；不引入
`docs/rule/<topic>/` 或 `docs/infrastructure/<domain>/<sub>/` 嵌套。

### §2.4 ISSUE 命名约定（Meta §4.5）

`docs/issues/` 文件命名格式 `[ISSUE]_NNN_DomainAbbr_Description.md`：

- `NNN`：3 位顺序编号（001 起；与 ADR 编号独立）
- `DomainAbbr`：mj-agent domain 缩写（`SYS / AGENT / DATA / SKILL / PROMPT / GUARDRAIL /
  OPS / INTEGRATION / WORKFLOW / ...`）
- `Description`：英文描述，`_` 连接，无空格

### §2.5 STANDARD 大型规范拆分阈值（Meta §3.8）

当 STANDARD **同时**满足以下三条件时，拆分为多份单一主题 STANDARD（每份用 5 章模板）：

| 条件 | 阈值 |
|---|---|
| 行数 | >500 |
| 主题章节 | ≥5 个独立 |
| 跨文件引用 | ≥10 处 |

**例外**：单一主题大型 STANDARD 即使满足三条件，可不拆。
**HITL 入口**：拆分判定结果纳入 [[policies/archive|policies/archive]] §1 archive trigger（拆分 / 合并 / 改名 → archive ceremony）。

### §2.6 项目根目录具名特殊文件（Meta §2.6）

以下 5 文件保留在项目根目录，**不使用** `[TYPE]_` 前缀；被单独点名赋予固定职责：

| 文件 | 职责 |
|---|---|
| `README.md` | 项目入口和快速启动 |
| `CONTRIBUTING.md` | 协作与提交流程 |
| `CHANGELOG.md` | 版本变更日志 |
| `GLOSSARY.md` | 项目术语索引（不与 `docs/glossary/<topic>.md` 专题词典重叠） |
| `CLAUDE.md` | AI 高频上下文缓存（同步策略见 §7） |

**治理例外条款**：项目根 5 文件**不进入 canonical 治理表**——不强制 frontmatter（A2 不适用）、
不强制类型 body 骨架、不计入 A1-A3 PR 门禁。**但仍受**：A4 wikilink 完整性、A6 CLAUDE.md sync
（§7 allowlist 触发时同步）、GitHub_Markdown §14 项目根特例。与 §3 path-to-track 决策树第 0 条衔接。

**AI-agent 指令契约例外（`AGENTS.md`，根 + 4 嵌套）**：`AGENTS.md` 是 **AI agent 指令契约**（所有
authorized agent 的 tool-neutral operating contract；per ADR-035）——与上述 5 个「项目元信息」文件
**并列于 canonical 治理之外，但属不同类别**。自 dual-agent-compat v5 P1（#320 / ADR-036）起共 **5
件**：根 `AGENTS.md` + 4 嵌套（`capabilities/` / `docker/` / `src/mj_agent/` / `tests/`），嵌套件
与根件同待遇。统一处理：**不写 frontmatter**（Codex 直读该文件，frontmatter 会污染其指令语义）、
**A1-A3 不适用**、**A4 wikilink 完整性 + A6 CLAUDE.md sync 仍适用**（根件 §Codex Status 内容与
`CLAUDE.md` §Codex Status 同步；各层 `CLAUDE.md` 以 `@AGENTS.md` 导入同层规则、不复制正文）、
GitHub_Markdown §14 语法特例同样覆盖；下文代偿纪律亦适用。归档 stale-ref sweep
（[[policies/archive|policies/archive]] §1）须一并覆盖全部 5 件；存在性与 `CLAUDE.md` 引用关系由
`scripts/sdd/check_development_agent.py`（V8）机器校验。

> **代偿纪律（gate-light ≠ 免责）**：项目根 5 文件豁免 A1-A3、缺自动化卫生门兜底，故**不得复制易变派生事实**
> ——如 active 技能数/名单（真值在 `agent.py:_ACTIVE_SKILLS`）、工具数、middleware 数等。这类事实**一律指向
> 单一真值源**（代码 / 对应 kernel policy），不在根文件硬写数字或枚举，避免无 sync 门时的 code→doc 漂移复发。

## §3 track frontmatter 字段（4 值枚举 + 决策树）

> 源：Meta §4.3.1。`track` 字段是三轨治理的脊柱；`scripts/check_frontmatter.py` 的
> `TRACK_VALUES` 枚举锚定于本节。

```yaml
---
...
track: code | agent | engineering-workflow | shared
---
```

| 取值 | 含义 | 默认值 |
|---|---|---|
| `code` | Track A — 代码侧文档（开发 / 部署 / 运维） | 见 §2 类型表 |
| `agent` | Track B — 智能体侧文档（runtime 直接影响业务） | 见 §2 类型表 |
| `engineering-workflow` | Track C — 工程流程文档（`.claude/` + HITL_Prompt + 工程流程 STANDARD） | 物理路径在 `.claude/**` 或 HITL_Prompt / AI_Engineering / Claude_Code_Settings / MCP_Server_Governance STANDARD 时强制 |
| `shared` | 跨轨 — 多 track reviewer 都需介入 | **过渡期**默认值；Phase 1 末收紧为 explicit required |

### §3.1 path-to-track 决策树（Meta §4.3.1）

新建 canonical 文档时按物理路径强制定 track：

0. 路径是项目根 markdown（`README.md` / `CONTRIBUTING.md` / `CHANGELOG.md` / `GLOSSARY.md` /
   `CLAUDE.md`）？→ **不适用 track**（per §2.6 例外条款；不写 frontmatter；A1-A3 不适用）
1. 路径在 `src/mj_agent/{skills,prompts}/**`？→ **agent**
2. 路径在 `src/mj_agent/{其他}/**`？→ **code**
3. 路径在 `.claude/**` 或 `.mcp.json` 或 `docs/rule/[STANDARD]_*_HITL_Prompt*.md` /
   `_AI_Engineering_*.md` / `_Claude_Code_Settings_*.md` / `_MCP_Server_Governance_*.md`？→ **engineering-workflow**
4. 路径在 `docs/evaluation/`？→ **agent**
5. 路径在 `docs/{infrastructure,runbook,api}/`？→ **code**
6. 路径在 `docs/rule/` 但治"engineering 流程"？→ **engineering-workflow**
7. 路径在 `docs/rule/` 治文档/代码/数据？→ **code** 或 **shared**
8. 其他 → 默认 `shared` 并 PR body 论证

边界 artifact 归属规则见 [[decisions/ADR-014_Tri_Track_Documentation_Governance|ADR-014]] §Decision 决策点 4。

## §4 Review Cadence（A6 — Anthropic 大型代码库最佳实践；native）

CLAUDE.md（root + 4 subdir）+ AGENTS.md（root + 4 subdir，per §2.6 例外条款）+ `.claudeignore` +
`.claude/settings.json` + `.claude/plugins.json` + `.claude/hooks/` **每 3-6 月或新 Claude 模型发布
后强制审计**.

| 触发 | 频率 | 责任人 | 检查项 |
|---|---|---|---|
| 定期 | 季度（每 3 月） | DRI（ranzuozhou） | 行数 / 命令链是否过时 / HITL 边界是否合理 / 4 项必停是否仍有效 |
| 模型 release | model major bump 1 周内 | DRI | 新模型行为变化（如 Opus 4.7 → 4.8）；旧 prompt 在新模型下是否反效果 |
| Phase 切换 | 每 Phase 末 | DRI + reviewer | Phase 引入的新 capability / gate 是否需在 CLAUDE.md 索引 |

**审计输出**：`evidence/ai-context-audit/<YYYY-MM>_audit.md`（capability 无关；属仓库级；
由 `.claude/hooks/stop-claude-md-improver/` 产出 diff 草案，user 审后落地）.

**触发 A6 时的产出物**：

1. CLAUDE.md（root + 4 subdir）的实际行数 vs 上限
2. 过时命令清单（运行失败的）
3. HITL 触发条件 vs 实际触发频率（过严 / 过松）
4. 4 项专属必停是否仍代表真实风险
5. 新 capability / gate 索引差距

**与其他文件联动**：

- `policies/ci-gates.md` §Review Cadence — 同期审计 settings.json + hooks 健康
- `mj-agent-doc-sync` skill — Phase 末 user 触发批量应用 proposed updates

## §5 PR 门禁 A1-A6（阻塞）+ OB1-OB5（非阻塞）

> 源：Code_Side §7.1（A1-A6 定义，canonical 源）+ §7.2（OB1-OB5）。**这是 A1-A6 的唯一权威定义**——
> Meta §7.1 只引用本表，不定义。约 50 个 living 文件按编号调用这些门禁（PR_TEMPLATE / CONTRIBUTING.md /
> `.claude/skills/mj-agent-{doc,flow}-*` / docs/INDEX.md）。

### §5.1 阻塞式检查 A1-A6（全部 track 共享）

| 编号 | 检查项 | 定义 | 适用 track | 自动化 |
|---|---|---|---|---|
| **A1** | 路径与文件名合法 | `[TYPE][_Subject]_Description[_vX.Y].md` 或 type-specific 格式（如 `[ISSUE]_NNN_DomainAbbr_Description.md`、`.claude/skills/mj-agent-<group>-<verb>/`） | code / agent / engineering-workflow / shared | Phase 2 CI |
| **A2** | Frontmatter schema 完整 | 必填基础字段 `type / domain / summary / owner / created / updated / state`（kernel policy 用 `type / summary / owner / created / updated / state / track`）；带 `version` 的类型（STANDARD/SPEC/EVAL/CONTRACT/ASSESSMENT）也填 `version` | code / agent / engineering-workflow / shared | Phase 2 CI（`scripts/check_frontmatter.py`） |
| **A3** | state 与专属字段枚举合法 | `state ∈ {draft, active, deprecated}`（working 文档 + `completed`）；type-specific enum 合法（`decision` / `resolution` / `eval_kind` / `contract_kind`） | code / agent / engineering-workflow / shared | Phase 2 CI |
| **A4** | 内部 Wikilink 目标存在 | `[[...]]` 目标存在于仓库中 | code / agent / engineering-workflow / shared | Phase 2 CI（`scripts/check_wikilinks.py`） |
| **A5** | INDEX.md 已同步或可重建 | 必要的 `docs/INDEX.md` / `docs/**/INDEX.md` 已同步或可由生成器重建 | code / agent / engineering-workflow / shared | Phase 2 CI |
| **A6** | allowlist 文档变更同步检查 CLAUDE.md | §7 4 类 allowlist（框架 / 架构 / 核心运行入口 / runtime 语义）变更需同步检查 `CLAUDE.md` | code / agent / engineering-workflow / shared | Phase 0 PR review |

> **A1-A6 是 track-shared**：通用 hygiene 检查，与 track 失败模式无关，对全部 4 track 生效（Code_Side v1.1 加注，与 Meta §7.1 一致）。
> **engineering-workflow 专属补丁**：A2 schema 在 `track: engineering-workflow` + 路径 `.claude/skills/**` 时，
> schema 是 ADR-013 native 2 字段（`name` + `description`），不是 13 字段。详见
> [[decisions/ADR-013_Plugin_SKILL_md_Schema_Separation|ADR-013]] + `sdd/adapters/claude-code-skill.md`。

### §5.2 非阻塞式观察 OB1-OB5（Code_Side §7.2）

非阻塞观察项，对全部 track 资产适用（Phase 1 阈值定稿）：

| 编号 | 观察项 |
|---|---|
| OB1 | 文档长度区间（过短 / 过长） |
| OB2 | 时态一致性 |
| OB3 | 内容边界（是否越界到他 track 治理范围） |
| OB4 | 摘要质量（`summary` frontmatter 是否准确反映正文） |
| OB5 | 内部一致性（章节交叉引用、术语一致） |

### §5.3 跨轨门禁分工 + 不在本 policy 的门禁

`track: shared` 文档由本 policy §5.1 A1-A6 + 各轨专属门禁共同执行：

- **A1-A6**（hygiene）由本 policy，对全部 track 生效
- **A7-A11**（agent-side 专属：SKILL/PROMPT/EVAL/CONTRACT `state: active` + `eval_references`
  非空 + `schema_ref` 存在）由 Agent_Side §7.1（历史源）；surface-anchored 子集落
  `sdd/adapters/runtime-skill.md` + `sdd/adapters/prompt.md` + [[policies/ai-agent|policies/ai-agent]] §4。
  仅对 `track: agent` 或 `shared` 触及 SKILL/PROMPT/EVAL/CONTRACT 时生效
- **A12-A14**（engineering-workflow 专属：`.claude/skills/` ADR-013 schema + `.claude/settings.json`
  allowlist + `.mcp.json` trust posture）由 Meta §7.7（历史源）；落 `sdd/adapters/claude-code-skill.md`
  + [[policies/ai-agent|policies/ai-agent]] §4（`mcp-server-trust-posture-change`）。
  仅对 `track: engineering-workflow` 或 `shared` 触及 `.claude/**` / `.mcp.json` 时生效

### §5.4 审阅角色

| 文档类别 | 必要 reviewer |
|---|---|
| 纯 code-side | SWE Reviewer 一名（Code_Side §8） |
| agent-side（SKILL/PROMPT/EVAL/CONTRACT） | Domain Expert / Prompt Engineer **+** SWE（≥ 2，Agent_Side §8） |
| engineering-workflow（`.claude/**` / `.mcp.json`） | Tooling Reviewer + SWE |
| `track: shared` | 各触及 track 的 reviewer 都需介入 |

## §6 Frontmatter schema（通用字段 + 类型专属）

> 源：Meta §4 + Code_Side §3.4.1/§3.5.1/§3.7.1/§3.8.1。这些字段背书 `scripts/check_frontmatter.py` 的 schema。

### §6.1 通用必填字段（A2）

每 canonical 文档声明（项目根 5 文件例外，§2.6）：

```yaml
---
type: <canonical 类型>
domain: <§2.4 domain 枚举之一>
summary: <一句话摘要>
owner: <DRI>
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
state: draft | active | deprecated   # working 文档另加 completed
track: code | agent | engineering-workflow | shared
---
```

带 `version` 的类型（STANDARD / SPEC / EVAL / CONTRACT / ASSESSMENT）额外填 `version`。
`supersedes` 字段接受 **list**（非单一 string）：单一替代 list 含单 string；拆分替代
（1 旧 → N 新）每个新 doc 都列旧 doc；合并替代（N 旧 → 1 新）list 含 N strings（Meta §4.6）。
**forbidden 字段**：`derives_from`（cross-repo decoupling 后移除；lineage 只用 `supersedes` + archive `replaced-by`）。

### §6.2 类型专属 frontmatter（Code_Side §3.x；ADR-022）

`scripts/check_frontmatter.py` 在 `state: active` 时强制以下类型专属字段（draft / deprecated 不强制）：

**RUNBOOK**（Code_Side §3.4.1）：

```yaml
last-verified: <YYYY-MM-DD>     # 最近一次按手册实测验证通过的日期；state: active 时必填
```

理由：RUNBOOK 是操作型文档，过期会误导现场操作；`last-verified` 让 reviewer / 工具识别陈旧 RUNBOOK。

**POSTMORTEM**（Code_Side §3.5.1）：

```yaml
severity: P0 | P1 | P2 | P3       # 事故严重程度
incident-date: <YYYY-MM-DD>       # 事故发生日期
resolved-at: <YYYY-MM-DDTHH:MM>   # 事故恢复时间戳（ISO 8601）
```

理由：支持后续按 severity / 时段聚合复盘分析。

**ISSUE**（Code_Side §3.7.1）：

```yaml
priority: P0 | P1 | P2 | P3                      # 处理优先级
risk-level: Low | Medium | High                 # 风险等级
resolution: open | fixed | wontfix | obsolete   # 处理结果
```

理由：`priority` + `risk-level` 支持优先级排序与风险审计（`state: active` 时强制 `priority` + `risk-level`）。

**ASSESSMENT**（Code_Side §3.8.1）：

```yaml
dimensions:                       # 评估维度列表
  - <dim-1>
  - <dim-2>
period: <daterange>               # 评估周期（如 "Phase 0" / "2026-04-01 → 2026-05-01"）
```

理由：`dimensions` + `period` 支持跨评估对比与时间序列分析。

### §6.3 Domain 枚举（Meta §9）

`domain` 取 16 值之一（含 v2.1 新增 `WORKFLOW`）：`SYS / AGENT / DATA / SKILL / PROMPT /
GUARDRAIL / OPS / INTEGRATION / WORKFLOW / ...`。`engineering-workflow` track 默认 domain
`WORKFLOW`，但跨领域工作流（git / doc 流程）可保留各自原 domain（`SYS` / `OPS`）+ `track: engineering-workflow`。

## §7 CLAUDE.md Sync Allowlist（A6 触发条件）

> 源：Meta §6.4（4 类 allowlist）+ §6.4.1（三轨分段）。本节定义 A6 PR gate **何时**要求 per-PR
> 同步 CLAUDE.md。

### §7.1 4 类 allowlist

以下 4 类文档变更触发 §5.1 A6 PR gate（同步检查 `CLAUDE.md`）；其余文档默认按需读取，**不要求**缓存进 CLAUDE.md：

| 类别 | mj-agent 具体例 |
|---|---|
| **类 1 — 全局高频标准** | trio（Meta / Code_Side / Agent_Side）+ HITL_Prompt + Commit_Message + GitHub_Markdown + 跨轨元规则 ADR（如 011 / 012 / 013 / 014 / 017 / 018） |
| **类 2 — 高频运行信息** | 入口命令矩阵（`uv run mj-agent serve` / `check` / `langgraph dev`）+ 端口规则（8000 Chainlit / 2024 LangGraph Studio）+ 关键环境变量（`ARK_API_KEY` / `MJ_CONFIG_PROFILE` / `LLM_PROVIDER`） |
| **类 3 — 项目目录入口** | `docs/INDEX.md` + 核心运行时模块位置（`src/mj_agent/{agent,llm,config}.py` + `tools/` / `skills/` / `prompts/`） |
| **类 4 — runtime 语义（mj-agent 特化）** | LLM provider matrix（Ark vs `local-openai-compat` 二分；`make_llm()` 实现，[[decisions/ADR-027_LLM_Provider_Abstraction|ADR-027]]）+ Data boundary L1-L4（hybrid guardrail / sqlglot precheck / SKILL semantics / read-only conn + GRANT；[[decisions/ADR-006_Fail_Safe_Reads|ADR-006]]）+ HITL gates（stage 5 plan / 7 SPEC / 9 self-review / 11 push / 13 review-CI） |

> **类 4 理由**：CLAUDE.md 中 LLM provider + Data boundary + HITL gates 三块占比 ~40%，是 mj-agent
> native 内容；显式列入避免 reviewer 在「这条规则改是否要 sync CLAUDE.md」上反复判断。

### §7.2 CLAUDE.md 三轨分段（Meta §6.4.1）

CLAUDE.md 内部按 track 分段，元规则放最顶。PR 触发 §7.1 allowlist 同步时，按文档自身
`track` 落入对应段；`shared` 落入元规则段：

- 顶部 **元规则段**：Meta_Framework 自身 + `track: shared` 的 ADR（如 ADR-011/012/013/014/017/018）
- `## Code-Side Documentation`：`track: code` 项；Phase 1+ 由 `mj-agent-doc-sync` 维护
- `## Agent-Side Documentation`：`track: agent` 项；维护方同上
- `## Engineering-Workflow Documentation`：`track: engineering-workflow` 项；A12-A14 门禁说明 +
  slash command 命名空间 + skill catalog 表 + HITL_Prompt 引用

## §8 Per-type body authoring depth

> 源：Code_Side §3.1 + §3.1.3（GUIDE）+ §3.4（RUNBOOK）。这些是 STANDARD 里的**逐类型 body
> authoring 深度规则**；M6 PR4 archive ceremony 落地后从历史源迁入本节。

### §8.0 Canonical body-authoring-depth authority

`docs/_templates/TEMPLATE_*.md` 是**逐类型 body authoring-depth 的 canonical 权威**——每个
canonical 类型（GUIDE / ADR / SPEC / RUNBOOK / POSTMORTEM / STANDARD / ISSUE / ASSESSMENT /
SKILL / PROMPT / EVAL / CONTRACT）的 body 骨架由对应 `TEMPLATE_<TYPE>.md` 承载；撰写时
**copy 模板、不即兴造 body**。本 §8 收纳 GUIDE / RUNBOOK 两类的 load-bearing 细节（骨架 + 原则），
其余类型（POSTMORTEM / SPEC / ADR / ISSUE / ASSESSMENT / ...）的 body 深度直接以各自
`TEMPLATE_*.md` 为准——例如 POSTMORTEM body 权威是 [[../docs/_templates/TEMPLATE_POSTMORTEM|TEMPLATE_POSTMORTEM]]，
SPEC body 权威是 [[../docs/_templates/TEMPLATE_SPEC|TEMPLATE_SPEC]]，ADR body 权威是
[[../docs/_templates/TEMPLATE_ADR|TEMPLATE_ADR]]。frontmatter schema（含类型专属字段）见 §6；
本节只治 body。

### §8.1 GUIDE body authoring（ORPH-09；源 Code_Side §3.1 + §3.1.3）

GUIDE body 骨架（CN-numbered，codified；权威模板 [[../docs/_templates/TEMPLATE_GUIDE|TEMPLATE_GUIDE]]）：

```markdown
# <GUIDE 标题>

> **适用范围** / **目标受众** / **版本** / **最后更新** / **派生自** /
> **关联文档**（header block，每行一项）

## TL;DR
- 阅读时间 / 涵盖范围 / 适用场景

## Prerequisites
- 目标读者 / 必备知识 / 建议了解

## 目录
- §0 适用场景
- §1 ... §N

## §0 适用场景
## §1 <主体 1>
## §2 <主体 2>
## §N <主体 N>

## 关联文档
## 更新记录（表格：日期 | 版本 | 变更）
```

**复用原则（Code_Side §3.1.3；load-bearing）**：GUIDE 自身**不复述**已在其它 canonical 来源
（README / CLAUDE.md / 其它 GUIDE / STANDARD）讲过的命令、配置、字段；**命令行 / 配置优先 wikilink
到 README / CLAUDE.md**，GUIDE 仅承担「读哪份 / 顺序怎么连」，**不复制命令**。规避点：与 README /
CLAUDE.md 的内容漂移。

### §8.2 RUNBOOK body authoring（ORPH-10；源 Code_Side §3.4）

RUNBOOK body 节段规约（权威模板 [[../docs/_templates/TEMPLATE_RUNBOOK|TEMPLATE_RUNBOOK]]）：

```
Trigger / Pre-checks / Steps / Rollback / Post-mortem trigger
```

| 节段 | 职责 |
|---|---|
| **Trigger** | 什么情况下执行本 RUNBOOK（告警特征 / 现象 / 与相邻 RUNBOOK 的边界），不含推测性 catch-all |
| **Pre-checks** | 执行 Steps 前必须验证的状态 / 权限 / 备份；任一失败则不进 Steps |
| **Steps** | 顺序执行，每步可复制粘贴命令 + 期望输出特征 + 异常处理 |
| **Rollback** | 何时回滚 + 回滚命令组 + 回滚后验证 |
| **Post-mortem trigger** | 事后判定是否建 POSTMORTEM |

**Post-mortem-trigger rationale**：RUNBOOK 收尾显式判定「是否升级为 POSTMORTEM」，把「操作型即时
修复」与「需要结构化复盘的事故」分流——故障导致生产事故 / 数据错误 / P1·P2 级影响时**必建**
POSTMORTEM（`docs/postmortem/[POSTMORTEM]_*.md`），恢复时长超预期 ×2 **建议建**轻量版，纯流程 /
命令修订则回到 RUNBOOK 本体编辑、不另建。POSTMORTEM body 权威见 §8.0 指定的
[[../docs/_templates/TEMPLATE_POSTMORTEM|TEMPLATE_POSTMORTEM]]。

---

> *M6 PR4a — kernel home for doc-governance（12 类分类 / `track` 字段 / A1-A6+OB1-OB5 / frontmatter
> schema / CLAUDE.md sync allowlist）；§4 Review Cadence native sustained。§8 per-type body
> authoring depth（ORPH-09 GUIDE + ORPH-10 RUNBOOK；TEMPLATE_*.md designated authority）M6 PR4-OB-2
> 迁入。源 STANDARD 在 PR4 archive 前留作历史源。*
