"""sqlglot AST-based SQL pre-validation (Component Judge rule mirror).

Catches issues that the regex L1 guardrail (``guardrail.py``) cannot:
  - SELECT * (non-aggregate star projection)
  - Missing time-column predicate on biz_dws fact tables
  - Missing LIMIT on non-aggregate detail queries

The rule IDs and semantics mirror mj-agent's
``[PROMPT]_component_judge.md`` so that any SQL failing this precheck
would also fail the eval Component Judge — runtime guardrail and
post-hoc eval share one rule source (per the MVP plan PR2 ⇄ PR4
``共用规则源`` commitment).

Deferred rules (require domain reasoning beyond catalog enumeration;
will live in the LLM Component Judge until clean static rules emerge):
  - ``exclude_internal``
  - ``use_stat_dt_not_create_dt``
  - ``use_between_for_date_range``
  - ``group_by_institution_for_cross``
"""

from __future__ import annotations

from dataclasses import dataclass

import sqlglot
from sqlglot import expressions as exp

from mj_agent.biz_catalog import load_catalog

_SIGNAL_TABLES: frozenset[str] = frozenset(
    {
        "dws_qcm_preprocessed_data",
        "dws_qcm_etl_metrics",
        "dws_qcm_ready_signal",
    }
)


@dataclass(frozen=True)
class PrecheckResult:
    """Outcome of static SQL precheck.

    ``errors`` are P0 violations — the caller should reject the SQL.
    ``warnings`` are P1 observations — the caller may surface them as
    hints in the response envelope without blocking execution.
    Each entry is a string of the form ``<rule_id>: <reason>``.
    """

    errors: list[str]
    warnings: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors


def _all_time_columns() -> set[str]:
    return {p["time_column"].lower() for p in load_catalog()["periods"].values()}


def _is_biz_dws_fact_table(table: exp.Table) -> bool:
    """A biz_dws.dws_qcm_* table that is not one of the 3 signal tables."""
    schema = (table.db or "").lower()
    name = (table.name or "").lower()
    if schema != "biz_dws":
        return False
    if not name.startswith("dws_qcm_"):
        return False
    return name not in _SIGNAL_TABLES


def _references_any_column(tree: exp.Expression | exp.Expr, names: set[str]) -> bool:
    return any(col.name.lower() in names for col in tree.find_all(exp.Column))


def _has_aggregation(select: exp.Select) -> bool:
    if select.args.get("group"):
        return True
    return any(True for _ in select.find_all(exp.AggFunc))


def precheck_sql(sql: str) -> PrecheckResult:
    """Run AST-based pre-validation on the candidate SQL.

    Args:
        sql: a SELECT (or WITH ... SELECT) statement that already passed
            the L1 regex guardrail.

    Returns:
        ``PrecheckResult`` with separate ``errors`` (P0, reject) and
        ``warnings`` (P1, advisory). Parse failures degrade gracefully
        to a single warning so we never block on a sqlglot version
        mismatch — the DB is the ultimate validator.
    """
    errors: list[str] = []
    warnings: list[str] = []

    try:
        tree = sqlglot.parse_one(sql, read="postgres")
    except sqlglot.errors.ParseError as exc:
        warnings.append(f"sqlglot_parse_failed: precheck skipped ({exc})")
        return PrecheckResult(errors=errors, warnings=warnings)

    if tree is None:
        warnings.append("sqlglot_parse_failed: precheck skipped (empty AST)")
        return PrecheckResult(errors=errors, warnings=warnings)

    # no_select_star — flag any Star projection that is NOT inside COUNT(*).
    for star in tree.find_all(exp.Star):
        if isinstance(star.parent, exp.Count):
            continue
        errors.append(
            "no_select_star: SELECT * is not allowed; list explicit columns "
            "(COUNT(*) is exempt)"
        )
        break  # one error is enough

    # require_time_range — fact-table queries must reference a known time column.
    fact_tables = [t for t in tree.find_all(exp.Table) if _is_biz_dws_fact_table(t)]
    if fact_tables:
        time_columns = _all_time_columns()
        if not _references_any_column(tree, time_columns):
            errors.append(
                "require_time_range: biz_dws fact table query has no time-column "
                f"predicate (expected one of {sorted(time_columns)})"
            )

    # require_limit — non-aggregate detail SELECT should carry a LIMIT.
    outer_select = tree if isinstance(tree, exp.Select) else tree.find(exp.Select)
    if isinstance(outer_select, exp.Select) and not _has_aggregation(outer_select):
        has_limit = bool(outer_select.args.get("limit") or tree.args.get("limit"))
        if not has_limit:
            warnings.append(
                "require_limit: detail (non-aggregate) SELECT lacks LIMIT; "
                "consider adding LIMIT N or aggregating"
            )
        else:
            _check_limit_size(outer_select, warnings)

    return PrecheckResult(errors=errors, warnings=warnings)


def _check_limit_size(select: exp.Select, warnings: list[str]) -> None:
    """Warn when LIMIT is suspiciously large (P1 advisory only)."""
    limit_node = select.args.get("limit")
    if limit_node is None:
        return
    n = limit_node.expression if isinstance(limit_node, exp.Limit) else limit_node
    if isinstance(n, exp.Literal) and n.is_int:
        try:
            limit_value = int(n.this)
        except (TypeError, ValueError):
            return
        if limit_value > 1000:
            warnings.append(
                f"limit_too_large: LIMIT {limit_value} > 1000; prefer aggregation "
                "or reduce the cap"
            )
