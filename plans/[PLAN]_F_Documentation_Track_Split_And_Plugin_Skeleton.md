---
type: plan
summary: 双轨分轨骨架交付与 plugin 构建计划 — Phase 0.5 起逐 phase 落地 Meta v2.0 / Code_Side / Agent_Side 三 STANDARDs + mj-agent-agent-doc / mj-agent-code-doc 双 plugin
owner: 项目负责人
created: 2026-04-27
updated: 2026-04-29
state: draft
track: shared
---

# PLAN F — 双轨分轨骨架交付与 plugin 构建

## Revision History

| 日期 | 修订 | 受影响章节 |
|---|---|---|
| 2026-04-27 | 初稿 | 全文 |
| 2026-04-29 | **plugin sequencing 翻转**：agent-doc 整体推迟（原 Phase 0.5 紧迫）；code-doc 的 `plan` + `author` 提前到 Phase 0.5 部分骨架（原全推迟 Phase 1）。详细 sequencing 由独立 PLAN 承载（外部笔记 `D:\Document\My_Local_Vault\temp-ai-chat\mj-agentlab-marketplace\[PLAN]_Marketplace_Plugin_Construction.md`） | §Context, §V-skel-4, §V-skel-5, §V-content-2, §Exit 判据 |
| 2026-04-29 | **schema 修正**：marketplace plugin SKILL.md 改用 Claude Code 原生 schema（name + description 两字段），不再引用 in-source 13 字段 schema。决策由 [[../docs/adr/[ADR]_013_Plugin_SKILL_md_Schema_Separation\|ADR-013]] 锁定；body 结构与 marketplace 现存 mj-sys-* plugin 风格对齐，不强制本仓 Agent_Side §2.1 五段式 | §V-skel-4 schema correction sub-banner, §V-skel-5 schema correction sub-banner |

## Context — 为什么现在做

[[../docs/adr/[ADR]_012_Two_Track_Documentation_Governance|ADR-012]] 决定了双轨治理 + skeleton-first 演进。本 PLAN 落地 Phase 0.5 起的逐步骨架交付与内容填充计划，覆盖：

- 3 STANDARD 骨架（[[../docs/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta v2.0]] + [[../docs/rule/[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework|Code_Side]] + [[../docs/rule/[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework|Agent_Side]]）的 promote 路径
- 双 plugin 骨架（`mj-agent-agent-doc` + `mj-agent-code-doc`）在 mj-agentlab-marketplace 仓的构建（**2026-04-29 翻转**：agent-doc 推迟、code-doc plan/author 提前——见 §V-skel-4 / §V-skel-5 banner）
- 11 个 skill（agent-doc 7 + code-doc 4）的逐 phase 引入时序
- frontmatter `track` 字段的 rollout（Phase 0.5 引入，Phase 1 末收紧为 explicit required）

本 PLAN **不**包括：

- v1.1 内容修订（v1.1 在 [[[PLAN]_E_Phase0_Docs_Governance_Verification|PLAN E]] V1-V13 全绿前不动）
- v1.6 roadmap 中 ADR-012 / 013 / 014 重编号到 015+（另开 PR；ADR-012 §References 列出受影响行号）
- skill 业务内容本身（每个 skill 内容由起 skill 的 PR 自行交付）
- PLAN 内容真空率超 30% 的"空壳骨架"

---

## 决策前提（已确认）

| 决策 | 选择 | 来源 |
|---|---|---|
| 双轨分轨架构 | **采纳 Option III**（双 plugin + 双 STANDARD + Meta 元层） | brainstorming + ADR-012 |
| skeleton-first 原则 | **是**（骨架内容真空率 ≤30%） | brainstorming |
| v1.1 共存策略 | **v2.0 三 STANDARD 以 `state: draft` 落 `docs/rule/`，v1.1 保持 active 直至 PLAN E 全绿 + Phase 0.5 promote PR** | brainstorming |
| plugin 命名 | `mj-agent-agent-doc` + `mj-agent-code-doc`（最终） | brainstorming + ADR-012 |
| ADR 编号 | **ADR-012**（接受 v1.6 roadmap 重编号成本） | brainstorming + ADR-012 |
| frontmatter `track` 字段 | 三值（code / agent / shared）；Phase 1 末收紧为 explicit required | ADR-012 决策点 4 |
| 边界 artifact 归属规则 | 见 [[../docs/adr/[ADR]_012_Two_Track_Documentation_Governance|ADR-012]] §Decision 决策点 4 表 | ADR-012 |

---

## 与现有 PLAN 的边界

| PLAN | 关心范围 | 与本 PLAN 关系 |
|---|---|---|
| [[[PLAN]_A_Studio_Walkthrough_Execution|PLAN A]] | Phase 0 walkthrough 验证 | 无重叠 |
| [[[PLAN]_B_PR2_DB_Access_Doc|PLAN B]] | DB 访问文档 | 无重叠 |
| [[[PLAN]_C_Smoke_Expansion_and_ADR_Backfill|PLAN C]] | smoke 扩展 + ADR 004/005/007 补 | **协调**：ADR backfill 的 ADR 应带 `track` 字段；建议 PLAN C 在 v2.0 promote 后或同期执行 |
| [[[PLAN]_D_Setup_Env_Scripts|PLAN D]] | 环境脚本 | 无重叠 |
| **[[[PLAN]_E_Phase0_Docs_Governance_Verification|PLAN E]]** | v1.1 验证矩阵 V1-V13 | **前置依赖**：本 PLAN 的 V-skel-3（promote PR）必须在 PLAN E V1-V13 全绿后启动 |

---

## 阶段 1：Phase 0.5 — 骨架落地（本 PLAN 写入即满足 V-skel-1）

### V-skel-1 STANDARD + ADR + PLAN 骨架已存在

| 验证项 | Pass 判据 |
|---|---|
| Meta_Framework v2.0 文件存在 | `docs/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework.md` 存在；frontmatter `state: draft, version: v2.0, track: shared` |
| Code_Side v1.0 文件存在 | `docs/rule/[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework.md` 存在；frontmatter `state: draft, track: code` |
| Agent_Side v1.0 文件存在 | `docs/rule/[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework.md` 存在；frontmatter `state: draft, track: agent` |
| ADR-012 存在 | `docs/adr/[ADR]_012_Two_Track_Documentation_Governance.md` 存在；frontmatter `state: draft, decision: accepted, track: shared` |
| 本 PLAN 存在 | `plans/[PLAN]_F_Documentation_Track_Split_And_Plugin_Skeleton.md` 存在；frontmatter `state: draft` |
| 骨架内容真空率 | 每份 STANDARD 章节大纲 + 引用回 v1.1 + TODO 之外的实质内容 ≥70% |

✅ **本 PR 写入完成时即满足**

### V-skel-2 PLAN E V1-V13 全绿（前置）

V-skel-3 必须等待 [[[PLAN]_E_Phase0_Docs_Governance_Verification|PLAN E]] V1-V13 全部 Pass 后再启动，避免 v1.1 验证未通过就开始 v2.0 升级。

| 验证项 | Pass 判据 |
|---|---|
| PLAN E V1-V13 全绿 | 见 PLAN E §Exit 判据 |
| 当前 worktree 已合并到 develop | `git log develop` 含本 worktree 全部 commits |

### V-skel-3 Phase 0.5 promote PR

PLAN E 全绿且本 worktree 合并到 develop 后，开 Phase 0.5 promote PR：

| 步骤 | 验证 |
|---|---|
| Meta_Framework v2.0 frontmatter `state: draft → active` | grep `state:` Meta v2.0 == active |
| Code_Side / Agent_Side frontmatter `state: draft → active` | grep == active |
| v1.1 走 [[../docs/archive/rule/[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.1\|v1.1（archive）]] §5.6.2 archive 流程 | `git mv docs/rule/[STANDARD]_..._Framework_v1.1.md docs/archive/rule/[STANDARD]_..._Framework_v1.1.md`；archive 副本 frontmatter `state: active → deprecated`；body 顶部加状态横幅指向 v2.0 |
| ADR-012 frontmatter `state: draft → active` | grep state == active |
| 现有 canonical 文档增补 `track` 字段 | 全部 .md frontmatter 含 `track`（默认 `shared`，逐文档审计实际归属） |
| `docs/INDEX.md` 更新引用 v2.0 + 双轨 | grep `Meta_Framework_v2.0` in INDEX |
| CLAUDE.md 同步更新（按 Meta v2.0 §6.4） | CLAUDE.md `## Documentation` 段引用 v2.0 |
| Wikilink 全仓审计（PLAN E V12 同款） | 所有 `[[...]]` 解析成功 |

### V-skel-4 mj-agent-agent-doc plugin 骨架（marketplace 仓，~~Phase 0.5 紧迫~~ → **整体推迟**）

> **⚠️ REVISED 2026-04-29**：原 Phase 0.5 紧迫的 agent-doc plugin 整体推迟到后续 phase 决议。理由（项目负责人决定）：runtime 侧 SKILL/PROMPT/EVAL/CONTRACT 框架尚未到使用密度阈值，agent-doc plugin 即使现在交付也短期内利用率低；优先验证 plugin 构建工艺于 code-doc（参考实例多）。本节以下 marketplace 仓动作清单 / plugin.json 模板等保留作 future reference，但 **不在 Phase 0.5 执行**。

> **⚠️ schema correction（[[../docs/adr/[ADR]_013_Plugin_SKILL_md_Schema_Separation|ADR-013]]，2026-04-29）**：本节后续示例（含 plugin.json 模板与"三 skill 骨架 SKILL.md 关键 frontmatter"段的 13 字段 yaml）**错误地把 mj-agent in-source SKILL.md 的 schema 套用到了 marketplace plugin SKILL.md**。修订决策：marketplace plugin SKILL.md 使用 Claude Code 原生 schema（仅 `name` + `description` 两字段）；body 结构与 marketplace 现存 mj-sys-* 4 plugin 风格对齐（如 `Overview` / `Workflow` / `Quick Reference` / `Examples` / `Anti-patterns`），不强制 [[../docs/rule/[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework|Agent_Side v1.0]] §2.1 的 Purpose / When to use / Planning workflow / Common patterns / Anti-patterns 五段式（§2.1 五段式仅适用于 in-source SKILL.md）。具体范本与理由见 ADR-013 + Agent_Side v1.0 §9.1。本节以下 13 字段 yaml 示例保留作 in-source 模板 reference，**不作为 plugin SKILL.md 模板**。

> **位置**：本 PR 在 mj-agent 仓不动；动作发生在 [mj-agentlab-marketplace](https://github.com/MJ-AgentLab/mj-agentlab-marketplace) 仓的独立 PR。

mj-agentlab-marketplace 仓动作清单：

```
plugins/mj-agent-agent-doc/
├── .claude-plugin/plugin.json     ← 创建（必填）
├── README.md                       ← 创建（描述 + 安装 + 使用示例）
├── skills/
│   ├── mj-agent-agent-doc-skill-author/SKILL.md          ← Phase 0.5 紧迫
│   ├── mj-agent-agent-doc-validate/SKILL.md              ← Phase 0.5 紧迫
│   └── mj-agent-agent-doc-tool-contract-author/SKILL.md  ← Phase 0.5 紧迫
└── （其他 4 skills 留 Phase 1 / 2 加：plan / prompt-author / sync / eval-author）
```

**`plugin.json` 模板**：

```json
{
  "name": "mj-agent-agent-doc",
  "description": "MJ-Agent 智能体侧文档治理工具：SKILL/PROMPT/EVAL/agent-facing CONTRACT 的 authoring + A7-A10/A11 校验 + frontmatter strip 自检（Track B）",
  "version": "0.1.0",
  "author": { "name": "MJ-AgentLab" },
  "repository": "https://github.com/MJ-AgentLab/mj-agentlab-marketplace",
  "license": "MIT",
  "keywords": ["mj-agent", "agent", "skill", "prompt", "eval", "contract", "documentation", "track-b"],
  "skills": "./skills/"
}
```

**marketplace.json 添加条目**：

```json
{
  "name": "mj-agent-agent-doc",
  "source": "./plugins/mj-agent-agent-doc",
  "description": "MJ-Agent 智能体侧文档治理（Track B）",
  "version": "0.1.0",
  "author": { "name": "MJ-AgentLab" },
  "category": "documentation",
  "keywords": ["mj-agent", "agent-side", "skill-authoring", "track-b"],
  "license": "MIT"
}
```

#### 三 skill 骨架 SKILL.md 关键 frontmatter

每 skill 的 SKILL.md 含完整 frontmatter（参照 [[../docs/_templates/TEMPLATE_SKILL|TEMPLATE_SKILL]]），body 暂为最小可执行版本（Phase 1 完整填充）。

**`mj-agent-agent-doc-skill-author/SKILL.md`**：

```yaml
---
type: skill
domain: SKILL
summary: 创建/改写 mj-agent SKILL.md，含 frontmatter + 五段式 body（Purpose/When-to-use/Workflow/Patterns/Anti-patterns）+ 渐进披露脚手架（scripts/references/assets）
owner: MJ-AgentLab
created: 2026-04-27
updated: 2026-04-27
state: draft
version: v0.1
track: agent
activation:
  when_to_use: "用户提到「新增 skill」「写一个能力处理 X」「改 SKILL.md」「加 references 文件夹」「skill 触发描述优化」时主动触发；即使用户未明确说 skill 也应触发"
  when_not_to_use: "不替代修改 Python 代码（路过 src/mj_agent/skills/<name>/__init__.py 但不动）；不跑 EVAL（交给 eval-author skill）"
tool_dependencies: []
related_prompts: []
---
```

body 五段式（最小可执行版本）：

```markdown
## Purpose
（最小版）创建符合 Agent_Side_Framework v1.0 §2 要求的 SKILL.md：完整 frontmatter（含 track: agent）+ 五段式 body + 可选 bundled resources 目录脚手架。

## When to use
（最小版）参见 frontmatter activation.when_to_use。

## Planning workflow
（Phase 1 主体填充）
1. 确认 skill 名（kebab-case）
2. 选 domain（默认 SKILL）
3. 拷贝 TEMPLATE_SKILL 起 frontmatter
4. 起 body 五段式
5. 决定是否需要 scripts/references/assets

## Common patterns
TODO Phase 1。

## Anti-patterns
- ❌ 跳过五段式 body 直接写说明
- ❌ frontmatter 漏 track 字段
- ❌ scripts/ 文件未被 SKILL.md 引用（孤儿）
```

`mj-agent-agent-doc-validate` 与 `mj-agent-agent-doc-tool-contract-author` 的骨架按相同模板。

### V-skel-5 mj-agent-code-doc plugin 骨架（~~推迟到 Phase 1~~ → **plan + author Phase 0.5 部分提前；validate + sync 仍 Phase 1**）

> **⚠️ REVISED 2026-04-29**：原全推迟 Phase 1 的 code-doc plugin 部分提前——`plan` + `author` 两个 skill 现在 Phase 0.5 部分骨架交付（内容来自 Code_Side §3-§4 active + mj-agent 已有 PLAN/ADR/STANDARD 正例，vacuum < 30%）。`validate` + `sync` 仍 Phase 1（依赖 §7.2 OB1-OB5 阈值定稿 + §7.6 `.claude/` 边界细化，目前 100% TODO）。

> **⚠️ schema correction（[[../docs/adr/[ADR]_013_Plugin_SKILL_md_Schema_Separation|ADR-013]]，2026-04-29）**：与 §V-skel-4 同一修订——`mj-agent-code-doc-plan` 与 `mj-agent-code-doc-author` 两 skill 的 SKILL.md 使用 Claude Code 原生 schema（`name` + `description`），body 结构与 marketplace 现存 mj-sys-* plugin 风格对齐，不强制本仓 [[../docs/rule/[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework|Agent_Side v1.0]] §2.1 五段式。详细内容蓝图（按修订后 schema）参见 working notes `[PLAN]_Marketplace_Plugin_Construction.md` 的 §11 修订清单（M-wn-1/M-wn-2/M-wn-3）。

**Phase 0.5 部分骨架范围**：

```
plugins/mj-agent-code-doc/
├── .claude-plugin/plugin.json     ← 创建（必填）
├── README.md                       ← 创建（明确标注：v0.1 仅含 plan + author）
├── CHANGELOG.md
├── skills/
│   ├── mj-agent-code-doc-plan/SKILL.md           ← Phase 0.5 部分提前（plan）
│   └── mj-agent-code-doc-author/SKILL.md         ← Phase 0.5 部分提前（author）
└── （validate + sync 留 Phase 1）
```

`marketplace.json` 追加 1 条 `mj-agent-code-doc` 条目（version: 0.1.0）。

**详细内容蓝图**：plugin.json 字段 / SKILL.md 五段式 body 大纲 / bundled refs 清单 / verification checklist 见独立 PLAN：

> `D:\Document\My_Local_Vault\temp-ai-chat\mj-agentlab-marketplace\[PLAN]_Marketplace_Plugin_Construction.md`

（该 PLAN 是 marketplace 仓的内容蓝图，跨仓 working layer 文档；不在本仓 plans/ 范围。）

**原 Phase 1 全推迟理由（部分仍生效）**：

- ~~"Track A 内容继承自 v1.1 + mj-sys-doc 间接服务可用"~~——v1.1 已 archive 到 `docs/archive/rule/`，Code_Side v1.0 已 active；Track A 已有自治 STANDARD，不再依赖 v1.1；mj-sys-doc 仅服务 mj-system 仓
- ✓ "validate 依赖 OB1-OB5 阈值"——仍生效，留 Phase 1
- ✓ "sync 依赖 .claude/ 边界细化"——仍生效，留 Phase 1

---

## 阶段 2：Phase 1 — 内容主体填充

### V-content-1 Code_Side / Agent_Side 章节内容主体

| 验证项 | Pass 判据 |
|---|---|
| Code_Side §3.1-§3.8（8 类 Authoring 章节）填充 | 每节 ≥50 行实质内容（非 TODO） |
| Code_Side §7.2 OB1-OB5 完整定义 | 5 项观察项规则明确（移植 mj-system v5.0） |
| Agent_Side §3.1 SKILL Authoring 主体填充 | body 五段式 / 渐进披露 / 触发描述质量 / EVAL coupling 全部完整 |
| Agent_Side §3.2 PROMPT Authoring 填充 | 版本演进 / EVAL 引用 / token 预算 / model_binding 完整 |
| Agent_Side §3.4 CONTRACT (agent-facing tool) 填充 | tool / agent-facing mcp 子类规则完整（与 SQL guardrail 同期） |
| Meta v2.0 §6.4.1 CLAUDE.md 双轨分段细则 | 完整 |
| Meta v2.0 §7.6 `.claude/` 边界 | 区分 marketplace 边界 vs 项目级 settings.json |

### V-content-2 双 plugin skill 完整化

> **⚠️ REVISED 2026-04-29**：sequencing 翻转后，本节"全部完整化"改为分两步：(1) Phase 1 内补完 code-doc 的 validate + sync（OB1-OB5 阈值定稿后）；(2) agent-doc plugin 整体（含 7 skill）于后续 phase 启动并完整化，时间窗待项目负责人决议。

| 验证项 | Pass 判据 | Sequencing 注记 |
|---|---|---|
| mj-agent-agent-doc plugin 整体上线 | plugin.json + marketplace.json + 7 skill 完整化 | **整体推迟**（2026-04-29 翻转） |
| mj-agent-code-doc plugin 完整化 | 4 skill（plan / author / validate / sync）全部上线 | plan + author 已在 Phase 0.5 部分骨架交付；validate + sync 仍 Phase 1 |
| 双 plugin 的 validate skill 实现 | Code_Side validate 实现 A1-A6 + OB1-OB5；Agent_Side validate 实现 A7-A10 + A11 + §7.5 自检 | Code_Side validate Phase 1；Agent_Side validate 推迟（随 agent-doc plugin） |
| INDEX 自动生成 | `docs/design/skills/INDEX.md` 由 agent-doc-sync 重建 | 推迟（依赖 agent-doc plugin） |

### V-content-3 frontmatter `track` 字段收紧

| 验证项 | Pass 判据 |
|---|---|
| Meta v2.0 §4.3.1 移除"过渡期默认 shared"语句 | grep `默认值` §4.3.1 无 |
| 全仓 canonical 文档显式标注 track | 任意 grep `track:` 在所有 .md 中找到，无遗漏 |
| PR 模板按 track 拆 reviewer 期望 | `.github/PULL_REQUEST_TEMPLATE/feature.md` 等含 track-aware reviewer 提示 |

---

## 阶段 3：Phase 2 — EVAL 体系 + A11 激活

| 验证项 | Pass 判据 |
|---|---|
| Agent_Side §3.3 EVAL Authoring 完整填充 | eval_kind / dataset_path / judges / baseline / regression_threshold 全部完整 |
| `mj-agent-agent-doc-eval-author` skill 上线 | marketplace 含此 skill |
| **A11 激活** | validate skill 强制检查 SKILL `state: active` 时 `eval_references` 非空 |
| A7.x 语义校验占位填充 | doc 描述 vs 代码行为对齐校验上线（A7.1 / A7.2） |

---

## 阶段 4：Phase 3+ — 视需要扩展

不在本 PLAN 范围内的后续 phase 工作（按需触发）：

- `migrate` skill（v1.x → v1.y 迁移）
- `review` skill（PR review 增强）
- `description-optimize` skill（skill-creator 5-iteration loop）
- `hook-author` / `subagent-author` / `Plugin_Authoring` 章节（mj-agent-* 第一个非 doc 插件触发）

---

## Exit 判据

本 PLAN 视为**全部完成**当且仅当：

- [ ] V-skel-1 至 V-skel-3 全 Pass + V-skel-5 部分 Pass（plan + author 骨架，Phase 0.5 末）
- [ ] V-content-1 至 V-content-3 全 Pass（Phase 1 末——其中 V-content-2 仅含 code-doc validate/sync；agent-doc plugin 完整化推迟）
- [ ] V-eval（Phase 2 EVAL 体系 + A11 激活）全 Pass（Phase 2 末）
- [ ] V-skel-4（agent-doc plugin 整体上线）：phase 时间窗待项目负责人决议（**2026-04-29 翻转后未定**）

任一 Pass 失败 → 归入对应阶段处理；不阻塞已 Pass 的阶段。

---

## 明确不做（留给其他 PLAN / ADR）

- ❌ v1.6 roadmap ADR-012/013/014 重编号到 015+（另开 PR；ADR-012 §References 列出受影响行号）
- ❌ Phase 4+ RBAC 相关治理改造
- ❌ mj-sys-doc 与 mj-agent-code-doc 长期合并决策（开放问题，待未来 ADR）
- ❌ 多平台 skill 兼容性（CC / Copilot / Gemini / Codex）—— 研究级 gap，留给 Phase 3+
- ❌ doc-as-spec / 代码生成（C2 研究级 gap）
- ❌ 双 plugin 共享代码层归属（开放问题 4 留给未来 ADR）

---

## 合入 develop 的后续动作（V-skel-1 完成后）

V-skel-1 完成（本 PR 写完文件）后，本 worktree 的 5 个新文件可单独走 PR 合入 develop（在 PLAN E V1-V13 全绿后）。PR 标题示例：

> docs(governance): scaffold two-track documentation governance v2.0 skeletons (ADR-012 + 3 STANDARDs + PLAN F)

PR 描述应当：

- 说明 v1.1 仍 active；v2.0 三 STANDARD 与 ADR-012 全部 `state: draft`
- 引用 ADR-012 决策依据
- 列出 V-skel-3 promote PR 的预期触发时机（PLAN E 全绿后）
- 在 CHANGELOG.md 的 `[Unreleased]` 区块登记 `docs(governance): scaffold v2.0 dual-track skeletons (draft state)`
- 受影响 v1.6 roadmap 行号清单（提示维护者重编号）

V-skel-3 promote PR 是另一个独立 PR，不在本 PR 写入范围。

---

## 风险与缓解

| 风险 | 缓解 |
|---|---|
| v1.1（active）与 v2.0（draft）共存期间，作者不知道用哪份 | docs/INDEX.md 显式标注"权威版本：v1.1，v2.0 在草稿"；CLAUDE.md 同步说明；ADR-012 §Consequences "负面" 段记录此风险 |
| ADR-012 与 v1.6 roadmap 已规划的 ADR-012/013/014 冲突 | ADR-012 §References 列出受影响 v1.6 行号；维护者重编号到 015+ |
| Phase 0.5 promote PR 推迟（PLAN E 长期不全绿） | v2.0 三 STANDARD 持续保持 draft；不影响 v1.1 active 状态；可任意推迟无副作用 |
| marketplace 仓 `mj-agent-agent-doc` plugin PR 与 mj-agent 主仓的 STANDARD 落地不同步 | V-skel-4 显式标注 marketplace 仓动作；建议两仓 PR 同期开启，相互引用；plugin 骨架的 SKILL 内容由 PR 描述指向 Agent_Side STANDARD §章节 |
| Phase 1 内容主体填充工作量超估（每个 STANDARD 章节 ≥50 行 × 多章节） | 允许逐章节 PR；不强求一 PR 完成全部填充；V-content-1 各项独立可 Pass |
| plugin 命名 `mj-agent-agent-doc`（agent-agent 重复）被认为不合适 | 修订需另开 ADR 修订（涉及 marketplace 改名 + 用户重装）；本 PLAN 锁定此命名 |
| 边界 artifact `track: shared` 文档审阅周期延长 | ADR-012 决策点 4 预先列出常见边界 artifact 归属；遇争议时按表归类，不重启讨论 |

---

## 附录：文件清单

本 PR 创建的 5 个文件：

| 文件 | 路径 | 大小估算 |
|---|---|---|
| Meta_Framework v2.0 | `docs/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework.md` | ~150 行 |
| Code_Side v1.0 | `docs/rule/[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework.md` | ~130 行 |
| Agent_Side v1.0 | `docs/rule/[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework.md` | ~200 行 |
| ADR-012 | `docs/adr/[ADR]_012_Two_Track_Documentation_Governance.md` | ~150 行 |
| 本 PLAN | `plans/[PLAN]_F_Documentation_Track_Split_And_Plugin_Skeleton.md` | ~230 行 |

总计 ~860 行，骨架内容真空率 ≤30%（章节大纲 + 引用回 v1.1 + 显式 TODO 之外的实质内容 ≥70%）。
