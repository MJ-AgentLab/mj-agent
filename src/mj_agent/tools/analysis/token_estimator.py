"""Token-budget estimator for SQL row sets (ADR-012 落地).

Estimates how many LLM tokens a row set would consume if shoved into
the prompt as JSON, and reports whether the result is within the
configured budget. The agent uses this to decide whether to feed rows
to the LLM directly or first call ``aggregate`` / ``drill_down``.
"""

from __future__ import annotations

import json
from functools import cache
from typing import Any

import tiktoken

# Default budget per ADR-012: 5000 tokens of data per LLM call. The
# value is exposed via the result envelope so tests / runtime configs
# can override at the call site.
DEFAULT_TOKEN_BUDGET = 5000


@cache
def _encoder_for(model_id: str) -> tiktoken.Encoding:
    """Resolve a tiktoken encoding for ``model_id``.

    Falls back to ``cl100k_base`` (OpenAI's general-purpose tokenizer) if
    the model isn't in tiktoken's registry — covers DeepSeek and other
    third-party models served via Ark's OpenAI-compatible endpoint, where
    exact tokenization differs slightly but the order-of-magnitude
    estimate is what we care about for budgeting.
    """
    try:
        return tiktoken.encoding_for_model(model_id)
    except KeyError:
        return tiktoken.get_encoding("cl100k_base")


def estimate_tokens(
    rows: list[dict[str, Any]],
    model_id: str = "deepseek-chat",
    budget: int = DEFAULT_TOKEN_BUDGET,
) -> dict[str, Any]:
    """Estimate the token cost of feeding ``rows`` to the LLM.

    Serializes rows to compact JSON (the wire form they'd take inside
    a tool result) and counts tokens via tiktoken.

    Args:
        rows: row set, typically ``execute_sql`` output's ``rows`` field.
        model_id: LLM model id; tiktoken-known names are exact, others
            fall back to ``cl100k_base`` (close enough for budgeting).
        budget: max tokens to allow before suggesting compression
            (default ``DEFAULT_TOKEN_BUDGET = 5000``, per ADR-012).

    Returns:
        Envelope dict:
          - ``token_count`` — estimated tokens for the row set
          - ``budget`` — echoed input
          - ``within_budget`` — bool, True iff token_count <= budget
          - ``row_count``
          - ``model_id`` echoed (or ``cl100k_base`` if fallback used)
          - ``suggestion`` — string hint for the agent if over budget
            (e.g. "call aggregate(...) or drill_down(...) to compress")
    """
    if budget <= 0:
        raise ValueError(f"budget must be > 0, got {budget}")

    # Normalize rows to JSON the same way they'd appear in a tool reply.
    payload = json.dumps(rows, ensure_ascii=False, default=str, separators=(",", ":"))
    enc = _encoder_for(model_id)
    n = len(enc.encode(payload))

    suggestion: str | None = None
    if n > budget:
        suggestion = (
            f"row set is {n} tokens (> {budget} budget); call aggregate("
            "rows, group_by=..., aggregations=...) or drill_down("
            "rows, metric_column=..., top_n=...) to compress before "
            "feeding to the LLM"
        )

    return {
        "token_count": n,
        "budget": budget,
        "within_budget": n <= budget,
        "row_count": len(rows),
        "model_id": model_id,
        "suggestion": suggestion,
    }
