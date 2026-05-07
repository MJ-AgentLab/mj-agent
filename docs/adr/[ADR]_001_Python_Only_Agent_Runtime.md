---
type: adr
domain: SYS
summary: Agent 逻辑、tools、skills、memory 全部留在 Python；前端仅作通信与渲染
owner: 项目负责人
created: 2026-04-24
updated: 2026-04-24
state: active
decision: accepted
track: code
---

# ADR-001: Python-Only Agent Runtime

## Context

LangChain 与 LangGraph 生态的成熟语言是 Python——evals 框架、memory primitives、skill loading、checkpointer 等工具链在 Python 侧最完整。mj-agent 路线图横跨 Phase 1（Chainlit 界面）到 Phase 3（Next.js + CopilotKit 生成式 UI），存在在前端引入 agent 逻辑层的诱惑（例如用 TypeScript 的 Vercel AI SDK）。

但该诱惑会带来**双运行时**的状态/工具同步成本，以及 evals、observability、guardrail 的重复实现。Phase 4 的 RBAC / 多团队治理同样要求单一 agent 运行时作为审计锚点。

## Decision

所有 agent 智能——包括 graph、tools、skills、memory、guardrail、gateway、evals——**全部在 Python 进程中运行**。
前端仅负责：(a) 人机交互界面；(b) 通过 API 与 agent 进程通信；(c) 接收 agent 返回的结构化结果（包括 Phase 3 的 `dataRef` 句柄）并渲染。

"Agent 智能"在前端 = 0 行代码。前端可以做本地表单校验、拖拽交互、图表渲染，但不做 tool 调用决策、不做 prompt 拼装、不做记忆管理。

## Consequences

**正面**
- 整个 agent 行为的可复现性集中在 Python 单一运行时，evals 和 observability 只需覆盖一套
- 审计日志、LangSmith trace、memory store 是唯一真相源，不存在前后端漂移
- 新开发者上手路径清晰：学 Python + LangGraph 即可参与 agent 开发

**负面**
- 前端需要富交互时（如实时流式 tool 调用过程）必须通过 WebSocket / SSE 从 Python 中转
- 某些"前端本地决策"的微优化（例如根据浏览器指纹选模板）无法实现

**中性**
- 前端 SDK 的选择变为纯工程问题（React、Vue、Chainlit），不影响 agent 语义

## Alternatives considered

**TypeScript 前端 + Python 后端的双层 agent**：前端做轻量编排、后端做重量级 tool 调用。拒绝——状态同步和工具定义会变成两份；LangGraph 的 checkpointer 语义难以跨语言表达；evals 体系会拆成两套。

**前端零智能，后端全智能（本 ADR 选项）**：采纳。

**前端全智能，后端仅 DB 代理**：拒绝——把 LLM API Key 放在浏览器侧违反 ADR-000 的 P3（工具中介）；也无法做审计。

## References

- ADR-000 数据-LLM 边界原则（P3 工具中介要求 agent 智能在受控环境内）
- ADR-013 Generative UI with Data Handle Pattern（Phase 3，前端渲染侧约定）
- `src/mj_agent/agent.py` — 当前 Python-only 实现入口
