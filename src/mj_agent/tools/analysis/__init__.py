"""Local row-set post-processing tools (ADR-012 落地, Phase 1 sub 1.B).

Five LLM-callable functions exposed to the agent. Usage pattern per
ADR-012's analysis loop:

    SQL plan → execute_sql → estimate_tokens(rows)
                              │
                              ├─ ≤ budget → LLM 直接解读
                              │
                              └─ > budget → aggregate / drill_down / compare_periods
                                            → 再 estimate_tokens 复检 → LLM 解读

These tools are **post-processors** on rows already returned by
``execute_sql``. The preferred path is still to write aggregating SQL up
front (which keeps the row count small at the source); these tools are
the fallback for when an unsplit query came back too large.

Public surface (registered in ``mj_agent.tools.ALL_TOOLS``):

  - ``aggregate(rows, group_by, aggregations) -> dict``
  - ``compare_periods(rows, time_column, metric_columns) -> dict``
  - ``drill_down(rows, dimension_column, metric_column, top_n) -> dict``
  - ``detect_anomaly(rows, metric_column, method, threshold) -> dict``
  - ``estimate_tokens(rows, model_id) -> dict``
"""

from mj_agent.tools.analysis.aggregate import aggregate
from mj_agent.tools.analysis.compare_periods import compare_periods
from mj_agent.tools.analysis.detect_anomaly import detect_anomaly
from mj_agent.tools.analysis.drill_down import drill_down
from mj_agent.tools.analysis.token_estimator import estimate_tokens

__all__ = [
    "aggregate",
    "compare_periods",
    "detect_anomaly",
    "drill_down",
    "estimate_tokens",
]
