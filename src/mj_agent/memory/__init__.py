"""Persistent memory: LangGraph checkpoint storage in PostgreSQL.

Phase 1 (sub 1.A) introduces the checkpointer; deeper memory abstractions
(long-term store, summarization) are Phase 2+.

Public surface:
  - ``open_checkpointer()`` — context-manager that yields a ready-to-use
    ``PostgresSaver`` (tables created on first call).
  - ``memory_conn_string()`` — assemble a libpq DSN for the memory DB.
"""

from mj_agent.memory.checkpointer import memory_conn_string, open_checkpointer

__all__ = ["memory_conn_string", "open_checkpointer"]
