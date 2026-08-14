"""Synthetic-snapshot helpers for the biz contract band (Epic #499 PR-0c).

Deliberately **not** a ``conftest.py``: the offline boundary checker forbids automatic
pytest inputs from performing repo-path discovery (``__file__``), and these helpers need
to locate their fixture directory. Test modules import this explicitly instead.

Nothing here reads a database, ``.env``, or the wall clock. "Now" is always injected by
the caller as a fixed instant, so freshness behaviour is deterministic.
"""

from __future__ import annotations

import datetime as dt
import shutil
from pathlib import Path
from typing import Any

from scripts.diff_biz_schema import SNAPSHOT_ROOT, load_snapshot

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "biz_snapshots"
VALID_SNAPSHOT = "valid_fresh.yaml"

#: Keeps ``valid_fresh.yaml`` (captured 2026-08-13T00:00Z) inside the 7-day window.
FRESH_NOW = dt.datetime(2026, 8, 13, 12, 0, tzinfo=dt.UTC)
#: 12 days after capture — outside the 7-day window.
STALE_NOW = dt.datetime(2026, 8, 25, 0, 0, tzinfo=dt.UTC)


def load_valid_payload() -> dict[str, Any]:
    """Payload of the valid synthetic snapshot, via the production validator.

    Routing the fixture through ``load_snapshot`` keeps it continuously proven against the
    same closed ``schema-v1`` envelope the real path enforces — if the fixture ever drifts
    out of contract, these tests fail rather than silently testing a non-conforming shape.
    """
    _captured_at, payload = load_snapshot(FIXTURE_DIR / VALID_SNAPSHOT)
    assert payload.get("schemas"), f"{VALID_SNAPSHOT} payload has no schemas block"
    return payload


def tables_of(payload: dict[str, Any]) -> dict[str, set[str]]:
    """``{schema: {table_name, ...}}`` from a snapshot payload."""
    by_schema = {
        schema: set(block.get("tables", {}))
        for schema, block in payload["schemas"].items()
    }
    assert by_schema, "synthetic snapshot exposed zero schemas"
    assert any(by_schema.values()), "synthetic snapshot exposed zero tables"
    return by_schema


def columns_of(payload: dict[str, Any], full: str) -> set[str]:
    """Column names of ``'<schema>.<table>'`` within a snapshot payload."""
    schema, name = full.split(".", 1)
    tables = payload["schemas"].get(schema, {}).get("tables", {})
    assert name in tables, (
        f"{full} is not in the synthetic snapshot; add it to "
        f"tests/contract/fixtures/biz_snapshots/{VALID_SNAPSHOT}"
    )
    columns = {c["name"] for c in tables[name]["columns"]}
    assert columns, f"{full} has an empty column list in the synthetic snapshot"
    return columns


def make_repo_root(tmp_path: Path) -> Path:
    """A throwaway repo root containing an empty sanctioned snapshot directory."""
    (tmp_path / SNAPSHOT_ROOT).mkdir(parents=True)
    return tmp_path


def install(repo_root: Path, fixture_name: str, *, as_name: str | None = None) -> Path:
    """Copy a fixture into ``repo_root``'s sanctioned snapshot directory."""
    target = repo_root / SNAPSHOT_ROOT / (as_name or fixture_name)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(FIXTURE_DIR / fixture_name, target)
    return target
