"""find_biz_context — semantic context retrieval.

Given a natural-language question, return the relevant slice of the
QCM catalog: candidate metrics, periods, dimensions, time columns,
period-over-period column patterns, signal tables, dimension joins,
and best-guess fact table names.

Intentionally rule-based and deterministic — the goal is to give the LLM
a focused subset of catalog context so the next step (``list_biz_tables``
+ ``describe_biz_table``) is well-aimed. Fuzzy matching is left to the LLM.
"""

from __future__ import annotations

from typing import Any

from mj_agent.biz_catalog.loader import load_catalog

_METRIC_KEYWORDS: dict[str, tuple[str, ...]] = {
    "qrynum": ("query", "查询", "调用", "请求", "qrynum", "qry"),
    "tntcnt": ("tenant", "机构", "租户", "tntcnt"),
}

_PERIOD_KEYWORDS: dict[str, tuple[str, ...]] = {
    "daily": ("day", "daily", "日", "每日", "天"),
    "weekly": ("week", "weekly", "周"),
    "monthly": ("month", "monthly", "月"),
    "quarterly": ("quarter", "quarterly", "季", "q1", "q2", "q3", "q4"),
    "yearly": ("year", "yearly", "annual", "年"),
}

_COMPARISON_KEYWORDS: tuple[str, ...] = (
    "yoy", "mom", "wow", "qoq", "dod",
    "同比", "环比", "对比", "去年同期", "上月", "上周", "上一期",
)

_DIMENSION_KEYWORDS: dict[str, tuple[str, ...]] = {
    "_total": ("total", "总量", "整体", "全部"),
    "_by_industry": ("industry", "行业"),
    "_by_tenant": ("tenant", "机构", "租户", "客户"),
    "_by_pcat_l1": ("pcat l1", "一级分类", "产品大类", "产品一级"),
    "_by_pcat_l2": ("pcat l2", "二级分类", "细分", "产品细分", "产品二级"),
    "_by_scenario": ("scenario", "场景"),
}


def _match_any(haystack: str, needles: tuple[str, ...]) -> bool:
    return any(n in haystack for n in needles)


def _match_keys(haystack: str, mapping: dict[str, tuple[str, ...]]) -> list[str]:
    return [key for key, kws in mapping.items() if _match_any(haystack, kws)]


def find_biz_context(question: str) -> dict[str, Any]:
    """Return the relevant slice of the QCM catalog for a question.

    Args:
        question: the analyst's natural-language question.

    Returns:
        A dict containing:
          - ``question`` (str): echoed input
          - ``candidate_metrics`` (list[str]): matched metric keys
          - ``candidate_periods`` (list[str]): matched period keys
          - ``candidate_dimensions`` (list[str]): matched dimension suffixes
          - ``needs_period_over_period`` (bool)
          - ``time_columns`` (dict[str, str]): period → time column
          - ``period_abbreviations`` (dict[str, str]): period → abbrev
          - ``period_over_period_patterns`` (dict): pattern definitions when
            comparison is detected, else empty
          - ``signal_tables`` (list[dict]): always returned for ETL/ready checks
          - ``dimension_tables`` (list[dict]): the two exposed biz_dwd tables
          - ``fact_table_pattern`` (dict): naming template
          - ``candidate_table_names`` (list[str]): cross product of
            metric × period × dimension, best-guess fact table names
          - ``forbidden_access`` (dict): mirror of GUIDE §2-§3 deny list
          - ``runtime_constraints`` (dict): timeout + lock hints
          - ``notes`` (list[str]): rationale when defaults were applied

    The result is meant to be small and focused — feed it to the LLM as
    a hint for the next tool call (``list_biz_tables`` / ``describe_biz_table``).
    """
    catalog = load_catalog()
    haystack = question.lower()
    notes: list[str] = []

    metrics = _match_keys(haystack, _METRIC_KEYWORDS)
    periods = _match_keys(haystack, _PERIOD_KEYWORDS)
    dimensions = _match_keys(haystack, _DIMENSION_KEYWORDS)
    needs_pop = _match_any(haystack, _COMPARISON_KEYWORDS)

    if not metrics:
        notes.append("未识别明确指标关键词，返回全部 metric 候选")
        metrics = list(catalog["metrics"].keys())
    if not periods:
        notes.append("未识别明确周期关键词，返回 daily / monthly 作为最常用候选")
        periods = ["daily", "monthly"]
    if not dimensions:
        notes.append("未识别明确维度关键词，返回 _total 作为默认候选")
        dimensions = ["_total"]

    candidate_table_names: list[str] = []
    for metric in metrics:
        for period in periods:
            period_suffix = catalog["periods"][period]["suffix"]
            for dim in dimensions:
                candidate_table_names.append(
                    f"biz_dws.dws_qcm_{metric}{period_suffix}{dim}"
                )

    return {
        "question": question,
        "candidate_metrics": metrics,
        "candidate_periods": periods,
        "candidate_dimensions": dimensions,
        "needs_period_over_period": needs_pop,
        "time_columns": {p: catalog["periods"][p]["time_column"] for p in periods},
        "period_abbreviations": {p: catalog["periods"][p]["abbreviation"] for p in periods},
        "period_over_period_patterns": (
            catalog["period_over_period_columns"] if needs_pop else {}
        ),
        "signal_tables": catalog["signal_tables"],
        "dimension_tables": catalog["dimension_tables"],
        "fact_table_pattern": catalog["fact_table_pattern"],
        "candidate_table_names": candidate_table_names,
        "forbidden_access": catalog.get("forbidden_access", {}),
        "runtime_constraints": catalog.get("runtime_constraints", {}),
        "notes": notes,
    }
