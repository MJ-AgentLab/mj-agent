---
type: adr
domain: AGENT
summary: SQL 工具异常（ValueError/RuntimeError）通过单个 SQLToolErrorMiddleware（wrap_tool_call + awrap_tool_call 双 hook；2026-07-07 amendment 取代原 @wrap_tool_call 装饰器形态）转换为 ToolMessage，使 LLM 能读到失败原因并自纠正；工具函数本身保留 raise 行为，保留 tests/smoke + tests/unit 现有契约
owner: 项目负责人
created: 2026-05-12
updated: 2026-09-02
state: active
decision: accepted
track: code
tags:
  - adr
  - tool-error
  - middleware
  - langchain
  - tool-message
  - self-correct
---

# ADR-029: Tool Error Surfacing to LLM via Middleware

## Context

mj-agent 的 SQL 工具链（`src/mj_agent/tools/sql/execute.py` + `tools/sql/introspect.py`）按 [[decisions/ADR-006_Fail_Safe_Reads|ADR-006]] §L1（regex guardrail）/ §L1b（sqlglot 精检 precheck）/ §L3（read-only connection via `readonly_cursor()`）/ §L4（analyst 角色的 `statement_timeout=60s`）分层拒绝越界 SQL：

| 来源 | 异常 | 出现位置 |
|---|---|---|
| L1 guardrail 拒绝 | `ValueError` | `execute.py:95` |
| L1b precheck 拒绝（如 `require_time_range`） | `ValueError` | `execute.py:99` |
| L4 statement_timeout 60s 触发 | `RuntimeError` | `execute.py:107` |
| L3 其它 DB 错误 | `RuntimeError` | `execute.py:112` |
| introspect allowlist 拒绝 | `ValueError` | `introspect.py:115` / `:128` |

`src/mj_agent/agent.py` 通过 `langchain.agents.create_agent(model, tools, system_prompt)` 装配 graph，**未传 `middleware` 参数**。LangGraph `ToolNode` 默认在该版本（langgraph 1.1.8 / langchain 1.2.15）通过 `_default_handle_tool_errors` 直接 re-raise 任何工具异常；graph step 报错后既不产生 `ToolMessage`，也不写入 checkpointer，Chainlit `astream` 永远等不到下一条消息——用户表现为"前端询问没有回应"。

实际触发场景（2026-05-12 frontend hang 排查复盘）：用户发"查 top 10 产品"，LLM 生成不含 `data_date` 谓词的 SELECT，被 L1b precheck 拒绝抛 `ValueError`，graph 静默失败。

## Decision

**SQL 工具异常通过 middleware 层转换为 `ToolMessage`，工具函数本身保留 raise 行为。**

实现位于 `src/mj_agent/middleware/tool_errors.py`，使用 LangChain 1.x 公开 API `langchain.agents.middleware.wrap_tool_call`：

```python
@wrap_tool_call
def handle_sql_tool_errors(request, handler):
    try:
        return handler(request)
    except (ValueError, RuntimeError) as exc:
        return _convert(request, exc)  # → ToolMessage(content="工具...", tool_call_id=...)
```

~~同模块同时提供 async 变体 `ahandle_sql_tool_errors`，覆盖 Chainlit `agraph.astream` 路径（参 [[decisions/ADR-006_Fail_Safe_Reads|ADR-006]] §L3 async bugfix 同源约束）。~~

~~`make_graph()` 在 `create_agent` kwargs 中追加 `middleware=[handle_sql_tool_errors]`（sync 和 async 均挂载——LangChain `wrap_tool_call` 装饰器内部按 handler 协程性自动派发）。~~

> **❌ 上两段的机制断言错误，已由 2026-07-07 Amendment（issue #288）更正**：装饰器不会
> "自动派发"；`ahandle_sql_tool_errors` 是独立 middleware 对象且从未注册。实际形态见下方
> Amendment——单个 `SQLToolErrorMiddleware` 类同时 override 双 hook。

### 错误消息约定

| 异常类 | 中文前缀 | 附加提示 |
|---|---|---|
| `ValueError`（校验类） | `工具调用未通过校验：` | 末行追加`请根据错误信息调整 SQL 或工具参数后重试。` |
| `RuntimeError`（执行类） | `工具执行失败：` | 透传原异常文案（`execute.py:107` 已含中文超时提示） |
| 其它（防御性兜底） | `工具执行失败（意外异常 <ClassName>）：` | LLM 通常会请求人工帮助而非重试 |

`tool_call_id` 从 `request.tool_call["id"]` 透传，保证 message graph 内一一对应。

## Consequences

- **正面**：
  - 前端 hang 根因消除——任何工具异常都会产生一条 `ToolMessage`，graph 推进继续
  - LLM 可在下一轮 turn 读到具体拒绝原因（"require_time_range: ..."），按系统提示词的"加 `WHERE data_date >= ...`" 模板自纠正
  - 与现有四层 guardrail（[[decisions/ADR-006_Fail_Safe_Reads|ADR-006]]）正交——L1/L1b/L3/L4 rule 文本不动，只改"如何把拒绝告诉 LLM"
- **负面**：
  - 多一层间接性：tool 报错后 LLM 看到的是中间件包装过的中文文本，不是原始 traceback；调试需在 `docker logs` 或 LangSmith trace 看原始异常
  - 中文错误前缀进入 LLM 上下文意味着多语言场景下需做翻译适配（当前 mj-agent 单语 zh-CN，不阻塞）
- **中性**：
  - 工具函数 raise 契约不变，`tests/unit/test_precheck.py` / `tests/smoke/test_agent_smoke.py:126-153`（`pytest.raises(ValueError, ...)`）继续通过——这是本 ADR 选 middleware 而非"在 execute_sql 里 try/except 改返回值"的关键考量

## Alternatives considered

### 方案 A — 修改 `execute_sql` 直接返回错误信封

把 line 95 / 99 / 107 / 112 的 raise 改成返回 `{"error": "...", "rows": [], ...}`。

未采纳原因：
- 破坏 `tests/smoke/test_agent_smoke.py` 4 条 `pytest.raises(ValueError, match=...)` 契约（130/137/144 行）+ `tests/integration/test_mj_system_db.py:47-56` 同样模式
- 直接调用方（脚本/REPL）失去"快速失败"语义，需在每个 caller 检查 `result["error"]`
- 不符合 mj-agent "工具函数即纯函数" 现有风格

### 方案 B — `ToolNode(handle_tool_errors=True)` 子类化

绕开 `create_agent`，自己拼装 LangGraph workflow。

未采纳原因：
- 重新实现 `create_agent` 已经做好的 model loop / system prompt / state 管理
- 与 [[decisions/ADR-002_Skills_As_First_Class_Citizens|ADR-002]] "skill body 经 `_build_system_prompt` 注入 create_agent" 的装配模型冲突

### 方案 C — 在 `agent.py` 用 `try/except` 包装每个 tool 注册

把 `ALL_TOOLS` 列表里每个工具替换成 try/except 包装版本。

未采纳原因：
- 与 LangChain 1.x 推荐路径（"Tool error handling has been relocated to middleware"）相反
- 对 LangChain 1.3+ 不向前兼容

## Amendment（2026-07-07 — issue #288：async 链断裂事故）

**事故**：Chainlit serve（`graph.astream`，async）下任何带工具调用的问题永久转圈。
checkpointer 库 `checkpoint_writes` `__error__` 通道记录：
`NotImplementedError('Asynchronous implementation of awrap_tool_call is not available...')`。
LangGraph Studio 同为 async 入口，同样中招；smoke 测试全走 sync `invoke()`，CI 从未覆盖。

**原文两处断言证伪**（langchain 1.2.15 源码 `agents/factory.py:878-911` +
`agents/middleware/types.py` base class）：

1. `@wrap_tool_call` 装饰器**不会**"按 handler 协程性自动派发"——它按被装饰函数的协程性
   生成**单侧** middleware（sync 函数 → 只有 `wrap_tool_call`；async 函数 → 只有
   `awrap_tool_call`）。`ahandle_sql_tool_errors` 因此是**第二个独立 middleware 对象**，
   且从未被注册进 `make_graph()`（死代码）。
2. factory 把 override 任一侧 hook 的 middleware **同时**纳入 sync/async 两条工具链；
   未 override 侧落到 base class 直接 `raise NotImplementedError`。推论：**把两个单侧
   实例一起注册也不行**——各自在对侧模式炸掉。

**修正后的机制**（本 amendment 起为本 ADR 的权威实现形态）：

```python
class SQLToolErrorMiddleware(AgentMiddleware):
    def wrap_tool_call(self, request, handler):        # sync: invoke / stream
        try: return handler(request)
        except (ValueError, RuntimeError) as exc: return _convert(request, exc)

    async def awrap_tool_call(self, request, handler): # async: ainvoke / astream
        try: return await handler(request)
        except (ValueError, RuntimeError) as exc: return _convert(request, exc)

handle_sql_tool_errors = SQLToolErrorMiddleware()      # 单实例，双链共用
```

错误消息约定、`_convert` 语义、"工具函数保留 raise 行为"契约均不变；变的只是
middleware 的**装配形态**：单类双 hook，注册处 `middleware=[handle_sql_tool_errors]`
不变。**不变式**：该 middleware 必须同时 override 双 hook——由
`tests/unit/test_tool_error_middleware.py::TestBothHooksOverridden` +
`tests/unit/test_agent_async_tool_path.py`（graph 级 fake-model async E2E）常驻回归。

同事故次生加固（`ui.py`）：`on_message` 对 `astream` 加异常兜底写回前端（杜绝无声转圈）；
空回复 fallback 改 `await graph.aget_state()`（AsyncPostgresSaver 的同步 `get_state`
在事件循环主线程必 raise）。

## References

- [[decisions/ADR-006_Fail_Safe_Reads|ADR-006]] — L1/L1b/L3/L4 防御层，本 ADR 决定如何把这些层的 reject 告诉 LLM
- [[decisions/ADR-002_Skills_As_First_Class_Citizens|ADR-002]] — `create_agent` 装配模型为何不绕开
- LangChain 1.2.x 文档：`langchain.agents.middleware.wrap_tool_call`（`/websites/langchain_oss_python_langchain` via Context7）
- LangGraph `ToolCallRequest` 数据结构：`.venv/Lib/site-packages/langgraph/prebuilt/tool_node.py:130`
- 触发本 ADR 的 frontend hang 排查：`develop` branch 2026-05-12 排查日志 / `docker logs mj-agent` 复现 traceback
