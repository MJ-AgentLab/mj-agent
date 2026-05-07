---
type: adr
domain: SKILL
summary: 所有专业能力以 skills/{name}/SKILL.md 格式封装，对齐 Claude Code skills 约定
owner: 项目负责人
created: 2026-04-24
updated: 2026-04-24
state: active
decision: accepted
track: agent
---

# ADR-002: Skills as First-Class Citizens

## Context

Agent 的"专业能力"——SQL 编写、DDD 语义解析、异常检测、漏斗分析——如果全部堆进 system prompt，会出现三类问题：
1. **token 膨胀**：prompt 随 skill 数量线性增长
2. **维护分散**：每个能力的规则夹杂在同一个长 prompt 里，变更时难以隔离影响面
3. **评估困难**：无法为单个能力编写独立的 eval 套件

Anthropic 在 Claude Code 与 Skills 生态中推动了 `<skill-name>/SKILL.md`（YAML frontmatter + markdown 指令）的约定，已经成为 agent 能力封装的事实标准。mj-agent 选择对齐该约定，同时在 Phase 0 把 skill 纳入本项目文档治理框架的 canonical 层。

## Decision

每一项专业能力打包为独立 skill，物理位置：

```
src/mj_agent/skills/<skill-name>/SKILL.md
```

- 目录名即 skill 身份（全小写、连字符）
- SKILL.md 前端是 YAML frontmatter（符合 mj-agent 文档治理框架 §4.4 的 `[SKILL]` schema）
- SKILL.md 正文是自然语言的能力说明：When to use / Planning workflow / Common patterns / Anti-patterns

Agent runtime 通过 `load_skill(name)` 读取 body（剥离 frontmatter）并作为 system prompt 的一部分注入。
Phase 1+ 将引入 skill registry 和 progressive disclosure（ADR-003）。

## Consequences

**正面**
- 每个 skill 独立可测、独立可版本化、独立可 eval
- 加入新能力的路径清晰：新建目录 + 写 SKILL.md + 在 registry 注册（Phase 1+）
- 与 Anthropic 生态对齐，团队成员的 Claude Code 经验可以直接迁移
- Skill 质量可以通过本框架的 A7 合并门禁强制（目录与身份一致、有 Python 实现或 registry 注册）

**负面**
- 需要维护一个 loader 层（`src/mj_agent/skills/__init__.py`），并且 loader 必须做 frontmatter 剥离，否则会污染 LLM 输入（v1.0 已修复）
- 当 skill 数量上升时，需要额外的选择逻辑（ADR-003 progressive disclosure）

**中性**
- Skill 的文档（SKILL.md）和运行时资产是同一份文件，省去同步成本，但也意味着 `src/` 目录受本文档框架治理

## Alternatives considered

**单一 system.md 存放全部能力**：拒绝——token 膨胀与维护分散问题无法解决。

**YAML 配置文件定义能力（仿 CrewAI 的 agents.yaml）**：拒绝——丢失自然语言叙述，LLM 理解成本反而更高；与 Anthropic 生态脱节。

**Python 类封装能力（每个 skill 一个 class，有 `prompt` 属性）**：拒绝——把行为描述藏进源码，非技术同事（例如业务分析师自己写 skill）参与成本过高。

## References

- [[ADR]_003_Progressive_Disclosure|ADR-003]]（skill 的加载策略）
- Anthropic Skills: `github.com/anthropics/skills`
- Agent Skills best practices: `agentskills.io/skill-creation/best-practices`
- 本仓库实例：`src/mj_agent/skills/query-writing/SKILL.md`
