"""Biz domain semantic catalog.

Static mirror of mj-system's external consumer contract (GUIDE + STANDARD
+ ADR-008). The catalog enumerates QCM metric families, period
granularities, dimension suffixes, period-over-period column patterns,
signal tables, and the two exposed dimension tables.

Two entry points:
  - ``load_catalog()`` returns the parsed YAML as a dict.
  - ``find_biz_context(question)`` returns the question-relevant slice.
"""

from mj_agent.biz_catalog.finder import find_biz_context
from mj_agent.biz_catalog.loader import catalog_path, load_catalog

__all__ = ["catalog_path", "find_biz_context", "load_catalog"]
