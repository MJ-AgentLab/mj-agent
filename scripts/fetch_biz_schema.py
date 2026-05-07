"""Snapshot biz-domain schema (allowed schemas + tables) to YAML.

Phase 1 sub 1.D — feeds ``scripts/diff_biz_schema.py`` and the contract
test (Phase 1 sub 1.G) so ``mj-ddd-semantics/SKILL.md`` and
``biz_catalog/qcm_catalog.yaml`` stay aligned with the live DB.

Output schema::

    schemas:
      biz_dws:
        tables:
          dws_qcm_qrynum_daily_total:
            columns:
              - name: data_date
                type: date
                nullable: false
                comment: ...
              - ...

Usage::

    uv run python scripts/fetch_biz_schema.py --output snapshot.yaml
    # default output: docs/runbook/biz_schema_snapshot_<YYYY-MM-DD>.yaml

Requires ``POSTGRES_ANALYST_USER`` etc in env. Skips with a clear
error when biz DB is unreachable.
"""

from __future__ import annotations

import argparse
import datetime
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env", override=False)


def _iter_tables() -> Iterator[dict[str, Any]]:
    """Yield ``{schema, table, comment}`` for every analyst-visible table."""
    from mj_agent.tools.sql.introspect import list_biz_tables

    yield from list_biz_tables()


def _describe(schema: str, table: str) -> dict[str, Any]:
    """Wrapper around ``describe_biz_table`` that returns columns dict."""
    from mj_agent.tools.sql.introspect import describe_biz_table

    return describe_biz_table(f"{schema}.{table}")


def snapshot() -> dict[str, Any]:
    out: dict[str, dict[str, Any]] = {}
    for t in _iter_tables():
        schema = t["schema"]
        table = t["table"]
        out.setdefault(schema, {"tables": {}})
        try:
            desc = _describe(schema, table)
        except Exception as exc:  # noqa: BLE001
            print(f"[fetch_biz_schema] WARN {schema}.{table}: {exc}", file=sys.stderr)
            continue
        out[schema]["tables"][table] = {
            "comment": desc.get("comment"),
            "columns": [
                {
                    "name": c["name"],
                    "type": c["type"],
                    "nullable": c["nullable"],
                    "comment": c["comment"],
                }
                for c in desc["columns"]
            ],
        }
    return {"schemas": out, "fetched_at": datetime.datetime.now(datetime.UTC).isoformat()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="output YAML path (default docs/runbook/biz_schema_snapshot_<date>.yaml)",
    )
    args = parser.parse_args()

    target = args.output or (
        _PROJECT_ROOT
        / "docs"
        / "runbook"
        / f"biz_schema_snapshot_{datetime.date.today():%Y-%m-%d}.yaml"
    )
    target.parent.mkdir(parents=True, exist_ok=True)

    print("[fetch_biz_schema] connecting to live biz DB ...")
    data = snapshot()
    n_tables = sum(len(v["tables"]) for v in data["schemas"].values())
    print(f"[fetch_biz_schema] snapshot: {n_tables} tables across {len(data['schemas'])} schemas")
    target.write_text(
        yaml.safe_dump(data, sort_keys=True, allow_unicode=True), encoding="utf-8"
    )
    print(f"[fetch_biz_schema] wrote {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
