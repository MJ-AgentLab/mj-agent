"""At-rest desensitization of ``execute_sql`` biz rows in the memory checkpointer.

Capability ``data-agent.memory-checkpointer`` (REQ-001/002/003/004; ADR-038 mechanism B).

``RedactingAsyncPostgresSaver`` overrides **both** langgraph write paths — ``aput`` (the
checkpoint → ``checkpoint_blobs``) and ``aput_writes`` (pending writes → ``checkpoint_writes``).
Both, because overriding only one leaks verbatim rows through the other (the both-hooks-or-it-
leaks footgun, same class as ADR-029 #288). Redaction operates on **clones** handed to
``super()``; the live in-memory message objects are never mutated (REQ-002), so what the LLM
reads within an active turn is unchanged — only the bytes written to Postgres differ.

Wired in ``checkpointer.py`` behind ``settings.mj_agent_memory_redact_biz_rows`` (default-on
since #365 AC4-6, after the both-paths on-disk canary + smoke round-trip validated it; set
``MJ_AGENT_MEMORY_REDACT_BIZ_ROWS=false`` to opt out).
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any

from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import ChannelVersions, Checkpoint, CheckpointMetadata
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from mj_agent.memory.digest import digest_rows

# execute_sql envelope shape guard: a JSON object carrying all three keys is treated as an
# execute_sql result. Cleanly skips error-path ToolMessages (plain-string content) and
# chart/excel envelopes (which carry file_path/kind but no rows/executed_sql/row_count).
_ENVELOPE_KEYS = ("executed_sql", "rows", "row_count")


def _redact_tool_message(msg: ToolMessage) -> ToolMessage:
    """Return a clone of an ``execute_sql`` ToolMessage with ``rows`` replaced by a count digest.

    Any message that is not an execute_sql result envelope (wrong ``name``, non-string content,
    non-JSON content, missing envelope keys, or already redacted) is returned **unchanged** (the
    same object), so identity is preserved for the no-op path.
    """
    if msg.name != "execute_sql":
        return msg
    content = msg.content
    if not isinstance(content, str):
        return msg
    try:
        envelope = json.loads(content)
    except (json.JSONDecodeError, ValueError):
        return msg
    if not isinstance(envelope, dict) or not all(k in envelope for k in _ENVELOPE_KEYS):
        return msg
    if envelope.get("rows_redacted"):
        return msg
    rows = envelope.get("rows")
    if not isinstance(rows, list):
        return msg
    columns = envelope.get("columns")
    columns = columns if isinstance(columns, list) else []

    redacted = dict(envelope)
    redacted["rows"] = []  # drop every verbatim cell value
    redacted["row_digest"] = digest_rows(rows, columns)
    redacted["rows_redacted"] = True
    return msg.model_copy(
        update={"content": json.dumps(redacted, ensure_ascii=False, default=str)}
    )


def _redact_value(value: Any) -> Any:
    """Redact execute_sql ToolMessages inside a checkpoint channel value or a write value.

    Handles a single message, a list, or a tuple; everything else passes through unchanged.
    Preserves object identity when nothing changed (so the caller can detect no-ops and avoid
    copying live state).
    """
    if isinstance(value, ToolMessage):
        return _redact_tool_message(value)
    if isinstance(value, list):
        out = [_redact_value(v) for v in value]
        return out if any(a is not b for a, b in zip(out, value, strict=True)) else value
    if isinstance(value, tuple):
        out_t = tuple(_redact_value(v) for v in value)
        return out_t if any(a is not b for a, b in zip(out_t, value, strict=True)) else value
    return value


class RedactingAsyncPostgresSaver(AsyncPostgresSaver):
    """AsyncPostgresSaver that redacts execute_sql biz rows at persist time (both write paths)."""

    @staticmethod
    def _redact_checkpoint(checkpoint: Checkpoint) -> Checkpoint:
        """Return a checkpoint whose ``messages`` (and any other message-bearing) channel values
        have execute_sql rows digested. Returns the ORIGINAL object if nothing changed — the live
        checkpoint is never mutated."""
        channel_values = checkpoint.get("channel_values") or {}
        new_channel_values: dict[str, Any] | None = None
        for key, value in channel_values.items():
            redacted = _redact_value(value)
            if redacted is not value:
                if new_channel_values is None:
                    new_channel_values = dict(channel_values)
                new_channel_values[key] = redacted
        if new_channel_values is None:
            return checkpoint
        new_checkpoint = checkpoint.copy()
        new_checkpoint["channel_values"] = new_channel_values
        return new_checkpoint

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        return await super().aput(
            config, self._redact_checkpoint(checkpoint), metadata, new_versions
        )

    async def aput_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        redacted_writes = [(channel, _redact_value(value)) for channel, value in writes]
        await super().aput_writes(config, redacted_writes, task_id, task_path)
