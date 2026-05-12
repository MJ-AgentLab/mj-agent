"""Agent middleware modules (LangChain 1.x ``@wrap_tool_call`` etc.).

Imported lazily by ``mj_agent.agent.make_graph``; importing this package
does not instantiate the LLM or touch external services.
"""

from mj_agent.middleware.tool_errors import handle_sql_tool_errors

__all__ = ["handle_sql_tool_errors"]
