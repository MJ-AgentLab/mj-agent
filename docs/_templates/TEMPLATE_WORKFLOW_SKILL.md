---
name: mj-agent-<group>-<verb>
description: 1-2 sentences describing what this skill does, then "Triggers on" + positive trigger phrases (Chinese + English keywords). Then "Do not use for:" + reverse-trigger block. Total ≥ 200 chars per A12 quality gate. Make the description "pushy" — undertriggering is the default failure mode.
---

# TEMPLATE: Engineering-Workflow SKILL（Track C）

> **此模板用于 `.claude/skills/mj-agent-<group>-<verb>/SKILL.md`**（in-tree workflow skill；engineering-workflow track；ADR-013 native 2-field schema）。
>
> **不**用本模板：
> - 起草 `src/mj_agent/skills/<name>/SKILL.md`（runtime SKILL；Track B；13-field schema + 五段式 body）→ 用 [[TEMPLATE_SKILL|TEMPLATE_SKILL]]
> - 起草 marketplace plugin SKILL.md（出本仓 governance）→ 参考 ADR-013 §Decision 内嵌范本
>
> **规格依据**：[[sdd/adapters/claude-code-skill|claude-code-skill adapter]] §Standards + ADR-013（2-field schema 决策）+ ADR-016（in-tree skill 命名 + lifecycle）。

---

## 复制本模板的步骤

1. 复制本文件到 `.claude/skills/mj-agent-<group>-<verb>/SKILL.md`
2. 删除本模板的 "TEMPLATE" header + "复制本模板的步骤" 段（即下方 fenced block 之前所有内容）
3. 替换 frontmatter 中的 `name` 为目标 skill 命名（必须等于目录名）
4. 替换 `description`：见下方 §1 Description 撰写规则
5. 填充 body：见下方 §2 Body 结构

`<group>` ∈ {flow, git, doc, runtime, infra}（5 类，详见 ADR-016）；`<verb>` 是动作短词（intake / commit / validate / studio-probe / skill-doc-improve 等）。

---

## §1 Description 撰写规则（A12 阻塞门禁）

**目标**：让 Claude Code 在用户描述触及本 skill 业务范围时**主动调用**。description 是唯一触发机制——Claude Code 只读 frontmatter，不读 body。

**A12 阻塞条件**（[[sdd/adapters/claude-code-skill|sdd/adapters/claude-code-skill]] §Standards/§CI Gate；原 Meta §7.7）：

1. ≥ 200 chars
2. 含**正向触发短语**（What it does + When to trigger，含中英文关键词）
3. 含**反向触发段** `Do not use for:` 列出邻近但不适用的场景（防 over-triggering）
4. 用 "pushy" 措辞对抗 undertriggering（默认失败模式）—— `Make sure to use this skill whenever ...` / `Triggers on ... 创建issue / new issue / report bug ...` 这类表达

**写法示例**（上游业务系统 mj-sys-git-issue 实测有效，本模板保留供参考）：

```
This skill should be used when the user asks to create a GitHub Issue,
select an issue template, fill issue fields, or start a new task or bug
report in MJ System. Triggers on "创建issue", "新建issue", "提issue",
"报bug", "新任务", "create issue", "new issue", "report bug", "file issue",
"open issue". Uses gh CLI with --body-file and reads .github/ISSUE_TEMPLATE
at runtime for title prefix and labels.
```

**反向触发示例**（防 over-triggering）：

```
Do not use for: branch creation (use mj-agent-git-branch instead),
commit message authoring (use mj-agent-git-commit), or PR creation
(use mj-agent-git-pr).
```

**5-iteration 描述优化**（推荐但非阻塞）：

skill-creator skill 提供的 5-iteration trigger eval 循环（10 should-trigger + 10 should-not-trigger query × 5 轮迭代）能显著改善 description 质量。新 skill 起草时建议跑一轮，但 Phase B/C 落地时可先以本节示例为模板，Phase D+ 再统一优化。

**禁止**：

- 在 description 中加 13-field schema 字段（如 `track`、`type`、`version`）—— Claude Code 不读这些字段，反而会污染 description
- 写"this is a skill that..."这种 self-referential 开头 —— 信息密度低
- 把 body 内容塞进 description —— description 应仅描述 "what + when + scope"

---

## §2 Body 结构（上游业务系统 风格）

上游业务系统 marketplace 现存 mj-sys-* skill body 风格作为既定事实标准（[[decisions/ADR-013_Plugin_SKILL_md_Schema_Separation|ADR-013]] §Decision 决策点 2）。Track C in-tree skill 沿用相同风格——**不**强制 Agent_Side §2.1 五段式（那是 Track B 专属）。

典型段落：

```markdown
# <Skill Title>

## Overview

<1-2 段：本 skill 解决什么问题；workflow 中的位置；上下游 skill；何时被调用>

**Workflow position**: <展示在 17-stage 闭环 / 5 family 编排中的位置>

```text
[upstream-skill] -> THIS-SKILL -> [downstream-skill]
```

## Prerequisite Check

<前置条件：执行环境 / 工具依赖 / 当前分支状态等；不满足时 H<N> 触发停止>

```bash
<Prerequisite check 命令>
```

## 快速开始（交互模式）

<可选；上游业务系统 mj-sys-git-* 的 v3.0 风格：信息充足性判断表 + 追问用语模板 + 直接生成命令的最短路径>

### 信息充足性判断

| 已知信息 | 行动 |
|---|---|
| <情况 1> | <对应行动> |
| <信息完整> | 直接生成命令 |

### 追问用语模板

- <情况 1>：<问句模板>

## Step 1 / Step 2 / ... / Step N（核心 workflow）

<逐步 workflow，命令可复制粘贴；每步给出期望输出 + 异常处理>

```bash
<命令>
```

## Quick Reference / Common patterns（可选）

<高频用法 / 速查表 / 范例>

## 人工介入场景（STOP & ASK）/ Human Intervention Points

<H1 / H2 / ... 列表：触发条件 + skill 行为>

| # | 触发条件 | skill 行为 |
|---|---|---|
| H1 | <条件> | <行为> |

## Anti-patterns（可选；runtime 类目专属时强制）

<列出邻近但不应该做的模式；与 Common patterns 对照>

**runtime 类目专属硬约束**：

- Do NOT modify `src/mj_agent/skills/**`
- Do NOT modify `src/mj_agent/prompts/**`
- Do NOT modify `src/mj_agent/agent.py`、`src/mj_agent/tools/**`
- Only propose diffs / run reverse-scans / list affected files；最终 write 由项目负责人 HITL 决定

## Handoff to <next-skill>（可选）

<workflow 衔接：本 skill 完成后下一步推荐 skill>

## Detailed XXX -> <bundled-reference>.md（可选）

<progressive disclosure：把不常用的细节放到 references/ 子目录；body 保持精简>
```

---

## §3 Bundled Resources（可选；progressive disclosure）

如 SKILL.md 主体接近 500 行（参考 上游业务系统 实测 SKILL.md 平均 200-300 行；上限 500 行），把详细参考资料拆到子目录：

```
.claude/skills/mj-agent-<group>-<verb>/
├── SKILL.md                  ← 主文件（≤500 行）
├── scripts/                  ← 可选：可执行脚本（不进 LLM 上下文）
│   └── *.py / *.ps1
├── references/               ← 可选：详细参考（按需加载，SKILL.md 显式引用）
│   └── *.md
└── assets/                   ← 可选：模板 / 数据 / 静态资源
    └── *
```

引用方式：在 SKILL.md 中显式 `Detailed XXX → references/<file>.md` 或代码块中 `python scripts/<file>.py`。

> Phase B/C 期间不强制使用 bundled resources（5 P0 git skill 全 inline 即可）；Phase D 视用量增长决议。

---

## §4 命名约定

- 目录名 = `name` frontmatter 字段 = slash command name（`/mj-agent-<group>-<verb>` 自动生成）
- `<group>` 5 类（详见 ADR-016）：
  - `flow`：编排 stage 0/3/4/8/9/10/11/15/17（~9 skills）
  - `git`：编排 stage 1/2/12/13/14/16/17（~9 skills）
  - `doc`：doc 创建 / 校验 / 同步 / 迁移（~6 skills）
  - `runtime`：**read-only inspect** in-source SKILL/PROMPT/biz_catalog（~4 skills）
  - `infra`：env-setup / docker-compose / storage-stack / studio-probe（~4 skills）
- `<verb>`：动作短词，kebab-case
  - 单词：`intake` / `commit` / `push` / `validate` / `delete`
  - 多词：`studio-probe` / `skill-doc-improve` / `prompt-version-bump` / `biz-catalog-sync`

---

## §5 与 上游业务系统 的差异（mj-agent 适配 cheatsheet）

| 维度 | 上游业务系统 | mj-agent |
|---|---|---|
| 语言/包管理 | Java + Maven | Python 3.13 + uv |
| 测试 | Maven test | pytest（unit/eval/integration/smoke/contract 五类） |
| Lint/类型 | maven plugins | ruff + mypy strict |
| ETL 编排 | n8n（7 plugin skill） | **不用** |
| DB schema 演进 | Flyway + Trigger + pg_cron | **只读消费者**（ADR-006 + ADR-009） |
| 服务架构 | 多服务（aec/dqv/qvl/qcm/sac/fc） | 单服务（LangGraph + Chainlit + CLI） |
| 部署 | 多 compose project | 独立 compose project（ADR-008） |
| 分支类型 | 6 类（feature/bugfix/documentation/maintain/optimization/hotfix） | **5 类**（去 optimization） |
| commit type | 8 类 | **7 类**（同 上游业务系统 但不引入 optimization） |
| commit scope allowlist | 6 类（aec/dqv/qvl/qcm/sac/fc + 跨代码） | **12 类**（agent/llm/prompt/skill/sql/db/config + tests/eval/ci/deps/infra） |
| Push 远程 | gitee + origin（双推；CI Runner 拉 gitee） | gitee + origin（同样双推；详见 [[../infrastructure/git/[GUIDE]_Git_Push_Workflow|Git_Push_Workflow]]） |

---

## §6 关联文档

- [[sdd/workflows/execution-loop|sdd/workflows/execution-loop]]（本类 SKILL 在 17-stage 闭环中的位置；§4 stage→skill 映射）
- [[sdd/adapters/claude-code-skill|sdd/adapters/claude-code-skill]] §Standards（in-tree workflow SKILL 治理；原 Meta §3.10）
- [[decisions/ADR-013_Plugin_SKILL_md_Schema_Separation|ADR-013]]（2-field schema 决策）
- [[decisions/ADR-016_In_Tree_Claude_Skills_Ecosystem|ADR-016]]（PR-B1 落地，命名空间 + lifecycle）
- 上游业务系统 v5.0+ `.claude/skills/mj-sys-*/SKILL.md`（直接派生源）

## §7 更新记录

| 日期 | 版本 | 变更 |
| --- | --- | --- |
| 2026-05-08 | v0.1 | 初稿（与 ADR-016 + 5 P0 git skills 同 PR-B1 落地） |
