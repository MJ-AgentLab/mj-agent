"""Unit tests for the static QCM biz catalog loader."""

from __future__ import annotations

import pytest

from mj_agent.biz_catalog import catalog_path, load_catalog


@pytest.fixture(autouse=True)
def _clear_catalog_cache() -> None:
    load_catalog.cache_clear()


def test_catalog_file_exists() -> None:
    assert catalog_path().exists(), "qcm_catalog.yaml must ship with the package"


def test_catalog_top_level_keys() -> None:
    catalog = load_catalog()
    expected_keys = {
        "version",
        "catalog_kind",
        "source",
        "metrics",
        "periods",
        "dimensions",
        "period_over_period_columns",
        "signal_tables",
        "dimension_tables",
        "fact_table_pattern",
        "forbidden_access",
        "runtime_constraints",
    }
    missing = expected_keys - catalog.keys()
    assert not missing, f"missing top-level keys: {sorted(missing)}"


def test_catalog_metrics_match_standard() -> None:
    catalog = load_catalog()
    assert set(catalog["metrics"].keys()) == {"qrynum", "tntcnt"}


def test_catalog_periods_match_standard() -> None:
    """STANDARD §2.1 — 5 period granularities, locked names."""
    catalog = load_catalog()
    assert set(catalog["periods"].keys()) == {
        "daily", "weekly", "monthly", "quarterly", "yearly"
    }


def test_catalog_period_time_columns() -> None:
    """STANDARD §2.1 — exact time column per period."""
    catalog = load_catalog()
    expected = {
        "daily": "stat_date",
        "weekly": "stat_week",
        "monthly": "stat_month",
        "quarterly": "stat_quarter",
        "yearly": "stat_year",
    }
    actual = {p: cfg["time_column"] for p, cfg in catalog["periods"].items()}
    assert actual == expected


def test_catalog_period_abbreviations() -> None:
    """STANDARD §3.2 — locked period abbreviations (cannot revert to long form)."""
    catalog = load_catalog()
    expected = {
        "daily": "dod",
        "weekly": "wow",
        "monthly": "mom",
        "quarterly": "qoq",
        "yearly": "yoy",
    }
    actual = {p: cfg["abbreviation"] for p, cfg in catalog["periods"].items()}
    assert actual == expected


def test_catalog_dimensions_count() -> None:
    """STANDARD §3 — 8 locked dimension suffixes."""
    catalog = load_catalog()
    suffixes = [d["suffix"] for d in catalog["dimensions"]]
    assert len(suffixes) == 8
    assert "_total" in suffixes
    assert "_by_tenant" in suffixes
    assert "_by_industry" in suffixes


def test_catalog_dimension_tables_exact() -> None:
    """ADR-008 Decision 4 — exactly 2 dimension tables exposed to analyst."""
    catalog = load_catalog()
    names = sorted(t["name"] for t in catalog["dimension_tables"])
    assert names == [
        "biz_dwd.dwd_dim_institution",
        "biz_dwd.dwd_dim_product_interface",
    ]


def test_catalog_dimension_join_keys() -> None:
    """STANDARD §4 — join keys are stable, locked names."""
    catalog = load_catalog()
    by_name = {t["name"]: t for t in catalog["dimension_tables"]}
    assert by_name["biz_dwd.dwd_dim_product_interface"]["join_key"] == "interface_id"
    assert by_name["biz_dwd.dwd_dim_institution"]["join_key"] == "tenant_code"


def test_catalog_signal_tables_three() -> None:
    """STANDARD §3 — exactly 3 QCM signal tables."""
    catalog = load_catalog()
    names = sorted(t["name"] for t in catalog["signal_tables"])
    assert names == [
        "biz_dws.dws_qcm_etl_metrics",
        "biz_dws.dws_qcm_preprocessed_data",
        "biz_dws.dws_qcm_ready_signal",
    ]


def test_catalog_pop_columns_pattern() -> None:
    """STANDARD §3.1 — period-over-period column conventions."""
    catalog = load_catalog()
    pop = catalog["period_over_period_columns"]
    assert pop["previous_value"]["pattern"] == "prev_<period>_<metric>"
    assert pop["diff"]["pattern"] == "<period_abbrev>_<metric>_diff"
    assert pop["rate"]["pattern"] == "<period_abbrev>_<metric>_rate"


def test_catalog_load_is_cached() -> None:
    a = load_catalog()
    b = load_catalog()
    assert a is b
