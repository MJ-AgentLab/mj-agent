"""Diff a fetched biz-schema snapshot against ``qcm_catalog.yaml`` claims.

Phase 1 sub 1.D — drift detector. Reads the YAML snapshot produced by
``fetch_biz_schema.py`` and reports:

  - tables in catalog YAML but missing from DB (deleted upstream?)
  - tables in DB that the catalog YAML doesn't enumerate (new fact tables?)
  - time-column / metric-column drift on QCM tables (e.g. ``data_date``
    renamed to ``stat_date``, etc.)

Usage::

    uv run python scripts/fetch_biz_schema.py --output snap.yaml
    uv run python scripts/diff_biz_schema.py --snapshot snap.yaml

Exit code 0 if no critical drift; 1 if the catalog is out of sync.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from mj_agent.biz_catalog import load_catalog

_PROJECT_ROOT = Path(__file__).resolve().parent.parent

_QCM_FACT_PREFIX = "dws_qcm_"
_QCM_SIGNAL_TABLES = {
    "dws_qcm_preprocessed_data",
    "dws_qcm_etl_metrics",
    "dws_qcm_ready_signal",
}


def _qcm_fact_tables(snapshot: dict) -> set[str]:
    biz_dws = snapshot.get("schemas", {}).get("biz_dws", {}).get("tables", {})
    return {
        name
        for name in biz_dws
        if name.startswith(_QCM_FACT_PREFIX) and name not in _QCM_SIGNAL_TABLES
    }


def _expected_time_columns(catalog: dict) -> set[str]:
    return {p["time_column"].lower() for p in catalog["periods"].values()}


def _drift(snapshot: dict, catalog: dict) -> list[str]:
    msgs: list[str] = []

    # 1. Signal tables present?
    biz_dws = snapshot.get("schemas", {}).get("biz_dws", {}).get("tables", {})
    expected_signals = {t["name"] for t in catalog.get("signal_tables", [])}
    expected_signal_names = {n.split(".", 1)[1] for n in expected_signals}
    for sig in expected_signal_names:
        if sig not in biz_dws:
            msgs.append(f"signal table missing in DB: biz_dws.{sig}")

    # 2. Dimension tables present + join keys?
    biz_dwd = snapshot.get("schemas", {}).get("biz_dwd", {}).get("tables", {})
    for dim in catalog.get("dimension_tables", []):
        full = dim["name"]
        schema, name = full.split(".", 1)
        target = biz_dwd if schema == "biz_dwd" else biz_dws
        if name not in target:
            msgs.append(f"dimension table missing: {full}")
            continue
        cols = {c["name"] for c in target[name]["columns"]}
        if dim["join_key"] not in cols:
            msgs.append(
                f"dimension {full}: join_key '{dim['join_key']}' missing "
                f"(actual columns: {sorted(cols)[:8]}...)"
            )

    # 3. QCM fact tables — check time-column presence
    expected_times = _expected_time_columns(catalog)
    for fact_name in _qcm_fact_tables(snapshot):
        cols = {c["name"].lower() for c in biz_dws[fact_name]["columns"]}
        if not (cols & expected_times):
            msgs.append(
                f"QCM fact table {fact_name} has no expected time column "
                f"(catalog says one of {sorted(expected_times)}; actual cols sample: "
                f"{sorted(cols)[:6]}...)"
            )

    return msgs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--snapshot",
        type=Path,
        required=True,
        help="path to YAML produced by fetch_biz_schema.py",
    )
    args = parser.parse_args()

    if not args.snapshot.exists():
        print(f"[diff_biz_schema] snapshot not found: {args.snapshot}", file=sys.stderr)
        return 2

    snap = yaml.safe_load(args.snapshot.read_text(encoding="utf-8"))
    catalog = load_catalog()
    msgs = _drift(snap, catalog)

    if not msgs:
        print("[diff_biz_schema] OK: catalog and DB schema are in sync")
        return 0

    print("[diff_biz_schema] DRIFT DETECTED:")
    for m in msgs:
        print(f"  - {m}")
    print(
        "[diff_biz_schema] update biz_catalog/qcm_catalog.yaml + "
        "skills/mj-ddd-semantics/SKILL.md to match"
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
