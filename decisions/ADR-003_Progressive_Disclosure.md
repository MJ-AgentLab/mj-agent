---
type: adr
domain: PROMPT
summary: 全局 system prompt 只含身份与原则；具体能力按需加载
owner: 项目负责人
created: 2026-04-24
updated: 2026-04-24
state: active
decision: accepted
track: agent
---

# ADR-003: Progressive Disclosure

## Context

[[decisions/ADR-002_Skills_As_First_Class_Citizens|ADR-002]] 确立了 skill 化路径。当 skill 数量增长到 5+（Phase 1 目标），把全部 SKILL.md 拼进 system prompt 会出现两类问题：

1. **token 成本**：每次请求携带所有 skill 定义，即使当次用不到
2. **注意力稀释**：LLM 的上下文注意力被不相关的 skill 细节占用，影响当前任务表现

Anthropic Skills 白皮书测算过，在 skill 多而每次只用少量的场景下，progressive disclosure 能带来 ~90% 的 token 节省。

## Decision

System prompt 按**两层结构**组织：

- **全局层（始终注入）**：Agent 身份、数据边界原则（ADR-000 的 P1/P2/P3）、通用工具清单、硬规则
- **按需层（按任务激活）**：具体 skill 的 SKILL.md 内容

Phase 0 暂用**静态拼接**（`load_prompt("system") + load_skill("query-writing")`，见 `src/mj_agent/agent.py:30-35`）。
Phase 1 引入 **skill 选择器**，基于用户提问的语义选取 top-K skill 激活；其余 skill 仅以 `summary` 出现在 skill 目录中，让 LLM 知道它们"存在但未展开"。

选择器实现策略（Phase 1 时再定稿）：
- L1：基于关键词的粗筛
- L2：基于 embedding 的语义匹配
- L3：必要时由 LLM 自己在第一轮输出中声明要激活哪些 skill

## Consequences

**正面**
- Skill 数量可以自由扩展，不影响每次请求的 token 成本
- LLM 在具体任务中只看到相关能力细节，注意力更集中
- 为 Phase 4 的团队特化 skills 奠定基础（不同团队激活不同 skill 子集）

**负面**
- 选择器本身是一个需要设计、测试、eval 的组件（Phase 1 新增复杂度）
- 选错 skill 会导致行为失准，需要配套 eval 发现回归
- 存在"skill 目录摘要表"和"完整 SKILL.md"两层真相源，需要索引保持同步（通过本框架 §6.1 的 skill INDEX 生成器在 Phase 1+ 解决）

**中性**
- Phase 0 目前只有一个 skill，本 ADR 的选择器部分尚未实现，仅做架构前置声明

## Alternatives considered

**永远注入全部 skill**：拒绝——token 成本与注意力稀释不可持续。

**LLM 自己在对话中请求加载 skill**（tool-based skill loader）：保留未来可能，但 Phase 1 先用选择器方案，原因是减少一次不必要的 LLM 往返。

**静态命名空间选择**（按用户所在团队固定一组 skill）：与本 ADR 选择器不冲突，Phase 4 RBAC 时叠加。

## References

- [[decisions/ADR-002_Skills_As_First_Class_Citizens|ADR-002]]（skill 是封装单位）
- `src/mj_agent/agent.py` — Phase 0 静态拼接实现
- `src/mj_agent/prompts/system.md` — 全局层内容
- Anthropic: *Equipping agents for the real world with Agent Skills*（关于 progressive disclosure 的 token 测算）
