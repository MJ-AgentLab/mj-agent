"""Static QCM catalog loader.

Loads ``qcm_catalog.yaml`` — the in-tree mirror of mj-system's
``[STANDARD]_Biz_DWS_Naming_Stability.md`` §2-§4. The YAML enumerates
QCM metric families, period granularities, dimension suffixes,
period-over-period column patterns, signal tables, and dimension table
join keys.

The catalog is a *static* projection of the contract — when mj-system
PR1/PR2 land and any enumeration shifts, the YAML is updated in a sync
PR (per the MVP plan's Assumptions §mj-system 上游契约状态).

Loading is cached per-process; tests can clear the cache via
``load_catalog.cache_clear()``.
"""

from __future__ import annotations

from functools import cache
from pathlib import Path
from typing import Any

import yaml

_CATALOG_FILENAME = "qcm_catalog.yaml"


def catalog_path() -> Path:
    """Return the absolute path of the bundled QCM catalog YAML."""
    return Path(__file__).parent / _CATALOG_FILENAME


@cache
def load_catalog() -> dict[str, Any]:
    """Load and return the QCM catalog as a dict.

    Returns:
        The parsed YAML root mapping. Top-level keys: ``version``,
        ``catalog_kind``, ``source``, ``metrics``, ``periods``,
        ``dimensions``, ``period_over_period_columns``, ``signal_tables``,
        ``dimension_tables``, ``fact_table_pattern``, ``forbidden_access``,
        ``runtime_constraints``.

    Raises:
        FileNotFoundError: if the bundled YAML is missing (packaging bug).
        yaml.YAMLError: if the YAML is malformed.
    """
    path = catalog_path()
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"qcm_catalog.yaml top-level must be a mapping, got {type(data)}")
    return data
