---
type: adr
domain: WORKFLOW
summary: 决议 mj-agent .claude/skills/ in-tree 工程编排技能命名空间 mj-agent-<group>-<verb>（5 family）+ 与 marketplace mj-agent-code-doc 插件共存 + lifecycle (P0/P1/P2 + sunset 规则)；Phase B PR-B1 起首落地
owner: 项目负责人
created: 2026-05-08
updated: 2026-05-08
state: active
decision: accepted
track: engineering-workflow
tags:
  - adr
  - claude-skills
  - in-tree
  - engineering-workflow
  - namespace
  - lifecycle
---

# ADR 016: In-Tree `.claude/skills/` Ecosystem — Namespace, Scope vs Marketplace, Lifecycle

## Context

[[../rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.1|Meta v2.1]] §3.10 + [[../rule/[STANDARD]_MJ_Agent_AI_Engineering_Execution_HITL_Prompt_v1.0|HITL_Prompt v1.0]] §5 锁定了 mj-agent 引入 in-tree 工程编排 SKILL 的方向：32 skills 分 5 family（flow 9 / git 9 / doc 6 / runtime 4 / infra 4），全部进 `.claude/skills/`，不走 marketplace。但落地前还有几个具体决策没明确：

### 空白 1：命名空间 collision 风险

mj-agent 仓内同时存在三种 SKILL 实体（[[../adr/[ADR]_013_Plugin_SKILL_md_Schema_Separation|ADR-013]] §决策点 1-3 已定边界）：

- in-source（runtime）：`src/mj_agent/skills/<name>/SKILL.md`，无前缀（如 `biz-domain-context`）
- in-tree（workflow，本 ADR 引入）：`.claude/skills/<name>/SKILL.md`
- marketplace plugin：`mj-agentlab-marketplace/plugins/<plugin>/skills/<skill>/`

如果 in-tree 命名不规范，可能与 in-source 撞名（同名两个 skill，loader 无法区分）；与 marketplace 现存 `mj-agent-code-doc-author` / `mj-agent-code-doc-plan` 命名重叠（同名两个 plugin/skill，Claude Code 触发匹配冲突）。

### 空白 2：与 marketplace `mj-agent-code-doc` 插件的功能重叠

marketplace 已有 `mj-agent-code-doc` 插件（4 个 skill 计划：plan / author / validate / sync；目前 author + plan 已 active）专门治"Documents-Driven-Development"。本 ADR 要在 in-tree 加 `mj-agent-doc-*` 6 skill 治"工程流程中的文档动作"。两者功能上 ~30% 重叠（都做 doc author / plan）。

不立 ADR 锁定边界，未来落地 PR-B4 / PR-C1 doc family 时会反复争议"为什么不直接扩 marketplace 插件而要 in-tree 重写"。

### 空白 3：32 skills 分阶段落地的优先级排序

HITL_Prompt §5 列出 32 skills 的目标态，但没说哪些先落地、哪些后做。如果不按优先级推进，Phase B 可能走偏（先做了 P2 而非 P0），导致 17-stage 闭环关键 stage 没 skill 支持。

### 空白 4：skill lifecycle（promote / deprecate / sunset）

新 skill 进 P0 → active 的标准是什么？哪些情况下应 deprecate？skill 长期不被调用应该清理吗？没有 lifecycle 政策长期会积累"僵尸 skill"。

---

## Decision

### 决策点 1：命名空间锁定 `mj-agent-<group>-<verb>`

所有 in-tree workflow skill 强制使用 `mj-agent-<group>-<verb>` 三段式命名：

```
.claude/skills/mj-agent-<group>-<verb>/SKILL.md
                    ^^^^^^^   ^^^^^^
                    (1)       (2)
```

**(1) `<group>` ∈ {flow, git, doc, runtime, infra}**——5 个固定 family，不允许扩展（除非另开 ADR）：

| family | 职责 | stage 覆盖 | 数量 |
|---|---|---|---|
| `flow` | 编排器（高阶 stage 调度，sub-call 域工具） | stage 0/3/4/8/9/10/11/15/17 | 9 |
| `git` | git 域工具（branch/commit/push/...） | stage 1/2/12/13/14/16/17 | 9 |
| `doc` | 文档域工具（plan/author/validate/...） | stage 4/6/11 sub | 6 |
| `runtime` | **read-only inspect** in-source canonical（SKILL/PROMPT/biz_catalog） | stage 8 (B-flavor) sub | 4 |
| `infra` | 项目专属基础设施（env-setup/docker-compose/storage-stack/studio-probe） | stage 8 (C-flavor) + stage 10 sub | 4 |

**(2) `<verb>`**：kebab-case 动作短词（`intake` / `commit` / `validate` / `studio-probe` / `skill-doc-improve` 等）。

slash command 自然成形 `/mj-agent-<group>-<verb>`。

**理由**：

1. 与 in-source SKILL（无前缀）显式区分，loader 边界清晰
2. 与 marketplace `mj-agent-code-doc-*` 共存——marketplace 命名是 `<plugin>-<skill>` 二段式，本 ADR 命名是 `mj-agent-<group>-<verb>` 三段式（含 `-<verb>` 多一段），不会撞
3. 与 mj-system `mj-sys-<group>-<verb>` 风格对齐，开发者切换两仓 mental model 一致
4. 5 family 与 mj-system 4 family（flow/git/doc/n8n/ops 共 5 含 ETL）有意分流：mj-agent 去 n8n + ops，加 runtime + infra（差异源自架构，不是命名偏好）

### 决策点 2：与 marketplace `mj-agent-code-doc` 插件**共存**（不替代）

marketplace `mj-agentlab-marketplace/plugins/mj-agent-code-doc/`（含 `mj-agent-code-doc-author` + `mj-agent-code-doc-plan` 已 active；`-validate` + `-sync` 待 Phase 1 落地）继续保留并使用。本 ADR 引入的 in-tree `.claude/skills/mj-agent-doc-*` 6 skill 与之并行存在。

| 维度 | marketplace `mj-agent-code-doc-*` | in-tree `mj-agent-doc-*`（本 ADR 引入） |
|---|---|---|
| 物理位置 | marketplace 仓 | mj-agent 仓 `.claude/skills/` |
| 跨项目复用 | ✅ 任何 mj-agent-* 仓可装（如未来 mj-anything 仓） | ❌ 仅 mj-agent 仓 |
| 内容耦合 | 通用 DDD（Documents-Driven-Development） | 与 HITL_Prompt v1.0 §4.X stage 紧耦合（如 §4.6 stage 6 SPEC/ADR/RUNBOOK） |
| Schema | ADR-013 native 2 字段 | ADR-013 native 2 字段（同样） |
| 升级触发 | marketplace 仓 PR | mj-agent 仓 PR |
| 安装方式 | `enabledPlugins` 在 `.claude/settings.json` 加 entry | git clone mj-agent 仓即获得 |

允许两者**有 30% 概念重叠**——marketplace 提供"通用 author"能力；in-tree 提供"stage-aware author"能力（含 mj-agent 特定 stage 上下文）。Phase D 后视使用情况决议是否需要进一步分工或合并。

**理由**：

1. **marketplace 优势**（跨项目复用、独立升级周期）和 **in-tree 优势**（stage-aware、与本仓版本绑定）正交，没必要二选一
2. 强制把 `mj-agent-doc-*` 全推 marketplace 会让 stage-aware skill 在 marketplace 显得过于 mj-agent 专属，违反 marketplace 仓"跨项目通用"定位
3. 强制 mj-agent 不用 marketplace 会浪费已落地的 `mj-agent-code-doc-author/plan` 工作
4. 共存方案让两个 plugin family 各自演进；冲突时 Claude Code description 触发匹配自然分流

### 决策点 3：32 skills 分阶段落地优先级（P0 / P1 / P2）

| 优先级 | 数量 | 落地 phase | 依据 |
|---|---|---|---|
| **P0** | 13 | Phase B（PR-B1...B4） | 17-stage 闭环必经 stage 的 Preferred Skill；缺失时 HITL_Prompt §4.X 失去执行能力 |
| **P1** | 14 | Phase B/C（PR-B3 末 + PR-C1/C2/C3） | 增强能力 / 后置 stage / 非常用但有价值 |
| **P2** | 5 | Phase D（PR-D2/D3） | EVAL / migrate 等长期能力，依赖 Phase 2 EVAL 框架 |

**P0 13 个**（与 HITL_Prompt §5 矩阵中 P0 标记一致）：

| Family | P0 skills |
|---|---|
| flow | intake / repo-scan / plan / implement / verify / self-review（共 6） |
| git | issue / branch / commit / push / pr（共 5） |
| doc | plan / author / validate（共 3）—— 但**注意**：这 3 个 P0 已有 marketplace 对应（`mj-agent-code-doc-{plan,author}`）；in-tree 版按 §决策点 2 共存并强调 stage-aware |
| infra | env-setup / studio-probe（共 2） |

PR 起首顺序按 stage 频次：

- **PR-B1**（本 ADR 落地）：git family 5 P0（issue/branch/commit/push/pr）—— 13/17 stage 直接覆盖（stage 1/2/12/13/14）
- **PR-B2**：flow family 4 P0（intake/repo-scan/plan/implement）—— 4/17 stage（0/3/4/8）
- **PR-B3**：flow family 完成（verify/self-review/scope-drift/review-respond/post-merge）+ infra 2 P0（env-setup/studio-probe）+ **promote PR**（v2.0 trio archive + v2.1 trio + HITL_Prompt 转 active）
- **PR-B4**：doc family 3 P0（plan/author/validate）

P1 14 / P2 5 详细 phase 分布见 [外部 plan file](C:/Users/Admin/.claude/plans/d-workspace-10-software-project-projects-golden-shannon.md) §4 编目表。

### 决策点 4：skill lifecycle 策略

**state 字段**：本 ADR 不引入 state 字段进 frontmatter（ADR-013 native schema 仅 2 字段）。lifecycle 状态通过 4 种**惯例机制**间接表达：

| 状态 | 表达方式 | 对应行动 |
|---|---|---|
| **proposed** | 在 plan file / ADR References 列出但 SKILL.md 未存在 | 等待 PR 落地 |
| **active** | SKILL.md 存在；description ≥ 200 chars 含正向/反向触发；在 HITL_Prompt §5 矩阵中有占位 | 可 invoke |
| **deprecated** | description 顶部加注 `**Deprecated**: 自 YYYY-MM-DD 起，请改用 mj-agent-<replacement>`；SKILL.md body 不删，保留兼容 | grep `\*\*Deprecated\*\*` 列出；累计 ≥3 月不被 invoke 时升级到 sunset |
| **sunset** | SKILL.md 文件 `git rm` 删除；HITL_Prompt §5 矩阵对应行删；ADR 记录 sunset 决策 | grep `scripts/check_wikilinks.py` 校验无 living refs |

**promote 触发**（proposed → active）：

- description 通过 A12 阻塞门禁（≥ 200 chars + 正向/反向触发）
- HITL_Prompt §5 矩阵对应行已填充
- 5-iteration trigger eval（推荐但非阻塞）recall ≥ 70% / precision ≥ 90%

**deprecate 触发**：

- 同 family 引入新 skill 取代（如 `mj-agent-doc-author` v2 取代 v1）
- 上游 mj-system 对应 skill 演进，本仓需要回归对位（差异显著时）
- 5-iteration trigger eval recall < 50%（"用户从来不调"信号）

**sunset 触发**（deprecate 后）：

- 累计 ≥ 3 个月 git log 中无相关 PR / Issue / 用户提问引用
- HITL_Prompt §5 矩阵已删除对应行
- 项目负责人 HITL 决议

---

## Consequences

### 正面

- **命名空间清晰**：3 种 SKILL 实体不撞名；slash command 自然分流
- **PR-B1...B4 优先级有据**：13 P0 skills 覆盖 17-stage 闭环关键路径，先落地这批让 HITL_Prompt §4 prompts 有实际执行入口
- **marketplace + in-tree 共存**：保留已落地的 `mj-agent-code-doc-{author,plan}` 工作，同时不阻碍本 ADR 引入 stage-aware in-tree 版
- **lifecycle 政策清晰**：未来 deprecate / sunset 有依据，避免僵尸 skill
- **5 family 与 mj-system 显式分流**：去 n8n + ops，加 runtime + infra；分流原因是架构差异（不用 n8n / ETL；多了 in-source canonical 治理需求 + 项目专属 infra），不是任意命名偏好
- **TEMPLATE_WORKFLOW_SKILL.md（PR-B1 同期落地）让后续 skill 起草成本低**：复制模板 + 填 description + 写 body，~30 分钟一个 skill

### 负面

- **5 family 边界长期可能不稳定**：例如未来若需要 `eval` family（治 EVAL 数据集 / judges），会触发 ADR 修订（增加 6th family）。当前判断：Phase 2 EVAL framework 起步时已有 `runtime/-eval-baseline` skill 占位，短期不需新 family；长期未定
- **runtime 类目的 "read-only by design" 没有技术性强制**：A12 描述质量 + Anti-patterns 段落是软强制；Claude Code 没有 per-skill tool allowlist 隔离机制；如未来 runtime skill 误改 `src/`，需要 hooks 兜底（Phase D 评估）
- **3 month sunset 阈值可能太激进或太保守**：runtime / infra family 调用频次本来就低（不是每个 PR 都跑），3 个月可能误判为僵尸；flow / git family 高频调用，3 个月不被调反而是真信号。本 ADR 接受单一阈值的简化代价；Phase D 视实际使用决议是否引入 per-family 阈值
- **5-iteration trigger eval 在 PR-B1 起首阶段不强制（推荐但非阻塞）**：可能首批 5 git skill 的 description 质量参差。缓解：PR-B1 review 时人工 sample 比对 mj-system 对位 skill 的 description；后续 PR 可补 eval

### 中性

- **ADR-013 dual schema 边界**：本 ADR 沿用 ADR-013 §决策点 5 关于 mj-agent docs/_templates/TEMPLATE_SKILL.md 仅服务 in-source SKILL 的限定；本 ADR 同期引入的 TEMPLATE_WORKFLOW_SKILL.md 是 in-tree workflow SKILL 专用，与 TEMPLATE_SKILL.md 互引"wrong template?"banner（已在 TEMPLATE_WORKFLOW_SKILL.md §0 实施）
- **HITL_Prompt §5 矩阵会随 skill 落地渐进填充**：当前 §5 各表 status 列标 "P0；PR-Bx 落地" 占位；PR 落地后改为 "active"；deprecate / sunset 时再调整。本 ADR 锁定 §5 矩阵作为 skill catalog 单一权威源
- **未来 plugin 数量增长可能触发 marketplace 独立模板**：如 PR-D 后 marketplace plugin 数量超过 4 个，可能需要 `mj-agentlab-marketplace/docs/templates/PLUGIN_SKILL.md`。本 ADR 不做承诺；视未来需要决议
- **本 ADR 自身的 promote 节奏**：与 ADR-014 / ADR-015 同样 skeleton-first（state: draft 落地，Phase B PR-B3 末次 promote PR 内转 active）

---

## Alternatives considered

### 方案 I（不分 family，全部扁平）

`.claude/skills/<verb>/SKILL.md`，无 `mj-agent-<group>-` 前缀。

**未采纳**：

- 与 in-source SKILL 命名空间撞（如果 in-source 加 `intake` skill 怎么办）
- 与 marketplace plugin 安装到同一 Claude Code 实例时撞名
- mj-system 4 family 命名实测有效；不分 family 长期会让 32 skills 一锅粥

### 方案 II（沿用 mj-system 风格 `mj-agent-<verb>` 二段式）

`.claude/skills/mj-agent-intake/`、`mj-agent-issue/` 等，去掉 `<group>`。

**未采纳**：

- 看不出 family 归属（如 `mj-agent-validate` 是 doc family 还是 infra family？）
- mj-system 实际是 `mj-sys-<group>-<verb>` 三段式（如 `mj-sys-flow-intake` / `mj-sys-git-issue`）；mj-agent 沿用三段式与之对位

### 方案 III（5 family 分别独立 plugin）

不进 mj-agent 仓 `.claude/skills/`，改成 5 个 marketplace plugin（`mj-agent-flow` / `mj-agent-git` / `mj-agent-doc` / `mj-agent-runtime` / `mj-agent-infra`）。

**未采纳**：

- 用户 2026-05-08 brainstorming 明确选择"全部 in-tree（mj-system 风格）"
- runtime + infra family 与 mj-agent 项目深度耦合（read-only src/ 约束 / 项目专属 storage stack 编排），不适合 marketplace 通用化
- 5 个 plugin 安装维护成本高于 1 个 in-tree

### 方案 IV（合并 in-tree + marketplace `mj-agent-code-doc`）

把 `mj-agent-code-doc` 插件迁回 in-tree（删 marketplace 版），mj-agent 仓只有 in-tree skills。

**未采纳**：

- marketplace 版已 active 并被其他项目（如未来 mj-anything 仓）潜在复用；删除是 breaking change
- in-tree 与 marketplace 双源是 ADR-013 决议的设计目的（schema 各自演化）
- 两者 30% 重叠是可接受的功能冗余，换取双方各自演进的灵活性

### 方案 V（per-family 独立 lifecycle 阈值）

deprecate / sunset 阈值按 family 不同（flow/git 3 月，runtime/infra 12 月等）。

**未采纳**：

- Phase B/C 起步阶段单一阈值已经够用
- per-family 阈值会引入治理复杂度，没必要在没有数据支持时引入
- Phase D 视实际使用决议是否升级（已写入 §Negative consequences）

---

## References

- 直接前置：
  - [[../rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.1|Meta v2.1]] §3.10（in-tree workflow SKILL 治理）
  - [[../rule/[STANDARD]_MJ_Agent_AI_Engineering_Execution_HITL_Prompt_v1.0|HITL_Prompt v1.0]] §5（32 skills hint matrix）
  - [[../adr/[ADR]_013_Plugin_SKILL_md_Schema_Separation|ADR-013]]（dual schema 边界）
  - [[../adr/[ADR]_014_Tri_Track_Documentation_Governance|ADR-014]] §决策点 5（命名空间初步）
  - [[../adr/[ADR]_015_HITL_Prompt_v1_0_Derivation|ADR-015]] §决策点 4（runtime 类目硬约束）
- 同期落地（PR-B1，本 PR）：
  - 5 P0 git skills：`.claude/skills/mj-agent-git-{issue,branch,commit,push,pr}/SKILL.md`
  - [[../_templates/TEMPLATE_WORKFLOW_SKILL|TEMPLATE_WORKFLOW_SKILL.md]]
  - 本 ADR
- 后续 PR：
  - PR-B2: flow family 4 P0
  - PR-B3: flow family 完成 + infra 2 P0 + promote PR
  - PR-B4: doc family 3 P0
  - PR-C1/C2/C3: P1 + mj-agent 专属 (doc 完成 + runtime + infra 余项)
  - PR-D1/D2/D3: P2 + EVAL infra
- 上游派生源：
  - mj-system v5.0+ `.claude/skills/mj-sys-*/`（35 in-tree skills；4 family 编排范式；mj-agent 5 family 派生源）
- marketplace 相关：
  - `mj-agentlab-marketplace/plugins/mj-agent-code-doc/`（active；与本 ADR in-tree `mj-agent-doc-*` 共存）
- 行业精度：
  - mj-system v5.0+ 35 in-tree skills 已实证可行（2026-05 至今）
  - Anthropic Skills 仓（github.com/anthropics/skills）：SKILL.md 工业标准 + bundled resources progressive disclosure
  - Claude Code plugin marketplace 与 in-tree 二元生态：[Claude Code docs](https://docs.claude.com/en/docs/claude-code/plugins)
- 用户互动证据：
  - 2026-05-08 brainstorming session：4 决策（建设侧 / skill 放置 / HITL 深度 / 框架重构）
  - 外部 plan 文件：`C:/Users/Admin/.claude/plans/d-workspace-10-software-project-projects-golden-shannon.md` §4 编目表 + §10 Open follow-ups
