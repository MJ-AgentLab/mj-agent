"""Validate a sanitized biz-schema snapshot and diff it against ``qcm_catalog.yaml``.

Epic #499 PR-0c. This script has **no** database, dotenv or network route. It reads only
Owner-attested sanitized snapshots from the gitignored local root::

    .mj-agent-local/biz-schema-snapshots/

Snapshot envelope is a **closed** ``schema-v1`` document whose top-level keys are exactly::

    schema_version, captured_at, provenance, sanitized, payload

``provenance`` must be ``sanctioned-agent-tool-chain`` and ``sanitized`` must be boolean
``true``. Any unknown top-level key, any YAML alias, and any explicit YAML tag is rejected
rather than ignored.

**``provenance`` is an Owner attestation, not cryptographic proof.** Nothing here can
verify that the capture actually went through the sanctioned agent tool-chain; the field
records that the Owner asserts it did.

Result codes and exit statuses::

    PASS_NO_DRIFT           0   snapshot valid, fresh, and consistent with the catalog
    SKIP_NO_SNAPSHOT        0   no snapshot present  -> nothing was verified
    SKIP_STALE_SNAPSHOT     0   snapshot older than 7 days -> nothing was verified
    DRIFT_DETECTED          1   snapshot valid and fresh, catalog is out of sync
    REJECT_INVALID_SNAPSHOT 2   unsafe path / malformed envelope / caller error

A SKIP never means PASS, and never asserts anything about current database freshness.

Usage::

    uv run python scripts/diff_biz_schema.py                       # auto-select newest
    uv run python scripts/diff_biz_schema.py --snapshot <name>.yaml
"""

from __future__ import annotations

import argparse
import datetime as dt
import stat
import sys
from pathlib import Path
from typing import Any

import yaml

from mj_agent.biz_catalog import load_catalog

#: Gitignored root; snapshots may live nowhere else. Kept as a literal string so the
#: boundary contract test can assert the path without importing this module.
SNAPSHOT_ROOT = ".mj-agent-local/biz-schema-snapshots"

SNAPSHOT_SCHEMA_VERSION = "schema-v1"
SNAPSHOT_REQUIRED_PROVENANCE = "sanctioned-agent-tool-chain"
#: Closed field set — exactly these keys, no more and no fewer.
SNAPSHOT_REQUIRED_FIELDS = frozenset(
    {"schema_version", "captured_at", "provenance", "sanitized", "payload"}
)
SNAPSHOT_MAX_AGE = dt.timedelta(days=7)
#: A snapshot dated in the future would never go stale, so bound clock skew.
SNAPSHOT_MAX_CLOCK_SKEW = dt.timedelta(hours=1)
SNAPSHOT_MAX_BYTES = 5 * 1024 * 1024
SNAPSHOT_SUFFIXES = (".yaml", ".yml")

#: Tags PyYAML resolves implicitly for plain YAML. Anything else in a snapshot is an
#: explicit tag and is rejected — see :class:`_StrictSnapshotLoader`.
_ALLOWED_YAML_TAGS = frozenset(
    {
        "tag:yaml.org,2002:map",
        "tag:yaml.org,2002:seq",
        "tag:yaml.org,2002:str",
        "tag:yaml.org,2002:int",
        "tag:yaml.org,2002:float",
        "tag:yaml.org,2002:bool",
        "tag:yaml.org,2002:null",
        "tag:yaml.org,2002:timestamp",
    }
)

RESULT_PASS = "PASS_NO_DRIFT"
RESULT_DRIFT = "DRIFT_DETECTED"
RESULT_SKIP_NO_SNAPSHOT = "SKIP_NO_SNAPSHOT"
RESULT_SKIP_STALE = "SKIP_STALE_SNAPSHOT"
RESULT_REJECT = "REJECT_INVALID_SNAPSHOT"

EXIT_OK = 0
EXIT_DRIFT = 1
EXIT_REJECT = 2

_QCM_FACT_PREFIX = "dws_qcm_"
_QCM_SIGNAL_TABLES = {
    "dws_qcm_preprocessed_data",
    "dws_qcm_etl_metrics",
    "dws_qcm_ready_signal",
}


class SnapshotRejected(Exception):
    """Snapshot failed closed validation.

    Never degrade this into a SKIP: a rejected snapshot means the input is unsafe or
    malformed, which is a louder condition than "no snapshot".
    """


class _StrictSnapshotLoader(yaml.SafeLoader):
    """``SafeLoader`` that additionally refuses YAML aliases.

    ``SafeLoader`` already refuses unknown/explicit tags such as
    ``!!python/object/apply``. Aliases, however, resolve silently and would let a
    snapshot smuggle a shared mutable node past field-by-field validation.
    """

    def compose_node(self, parent: Any, index: Any) -> Any:
        if self.check_event(yaml.events.AliasEvent):
            event = self.peek_event()
            raise SnapshotRejected(
                f"YAML alias '*{event.anchor}' is not allowed in a snapshot "
                f"(line {event.start_mark.line + 1})"
            )
        node = super().compose_node(parent, index)
        # Explicit tags are rejected here rather than left to SafeLoader's "no constructor"
        # error. SafeLoader would also refuse `!!python/...`, but relying on that makes tag
        # safety a property of PyYAML rather than of this contract — and it would silently
        # weaken if the loader base class ever changed.
        if node is not None and node.tag not in _ALLOWED_YAML_TAGS:
            raise SnapshotRejected(
                f"explicit YAML tag {node.tag!r} is not allowed in a snapshot "
                f"(line {node.start_mark.line + 1}); schema-v1 permits only plain "
                f"scalars, sequences and mappings"
            )
        return node


def _snapshot_root(repo_root: Path) -> Path:
    """The sanctioned root, proven to physically live inside ``repo_root``.

    The **root itself** must be anchored, not merely its entries. If ``.mj-agent-local`` or
    its ``biz-schema-snapshots`` leaf is a symlink/junction, ``root.resolve()`` adopts the
    redirected target as authoritative and the containment check in :func:`_validate_path`
    then compares escaped-against-escaped and passes trivially — a full out-of-repo read
    that would report ``PASS_NO_DRIFT``. Checking only the leaf is insufficient: a junction
    one level up at ``.mj-agent-local`` leaves the leaf a plain directory.
    """
    root = repo_root / SNAPSHOT_ROOT
    if root.exists() and not root.resolve().is_relative_to(repo_root.resolve()):
        raise SnapshotRejected(
            f"sanctioned snapshot root is redirected outside the repo: {root} resolves to "
            f"{root.resolve()}, which is not under {repo_root.resolve()}"
        )
    return root


def _is_reparse_point(path: Path) -> bool:
    """True for symlinks and Windows junctions/reparse points."""
    try:
        st = path.lstat()
    except OSError:
        return True
    attrs = getattr(st, "st_file_attributes", 0)
    if attrs & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0):
        return True
    return path.is_symlink()


def _validate_path(root: Path, candidate: Path) -> Path:
    """Return ``candidate`` proven to be a safe, regular, in-root, size-bounded file."""
    root_resolved = root.resolve()

    # Check for a reparse point BEFORE resolving, so a symlink cannot launder an
    # out-of-root target into an in-root-looking resolved path.
    if _is_reparse_point(candidate):
        raise SnapshotRejected(
            f"snapshot path is a symlink/reparse point, which is not allowed: {candidate}"
        )

    resolved = candidate.resolve()
    if not resolved.is_relative_to(root_resolved):
        raise SnapshotRejected(
            f"snapshot path escapes the sanctioned root: {resolved} is outside {root_resolved}"
        )

    try:
        st = candidate.lstat()
    except OSError as exc:
        raise SnapshotRejected(f"snapshot path is not readable: {candidate} ({exc})") from exc

    if not stat.S_ISREG(st.st_mode):
        raise SnapshotRejected(f"snapshot path is not a regular file: {candidate}")
    if st.st_size == 0:
        raise SnapshotRejected(f"snapshot file is empty: {candidate}")
    if st.st_size > SNAPSHOT_MAX_BYTES:
        raise SnapshotRejected(
            f"snapshot file exceeds the {SNAPSHOT_MAX_BYTES} byte bound: "
            f"{candidate} is {st.st_size} bytes"
        )
    return resolved


def _select_snapshot(root: Path, explicit: Path | None) -> Path | None:
    """Resolve the snapshot to read, or ``None`` when the root holds no candidates."""
    if explicit is not None:
        candidate = explicit if explicit.is_absolute() else (root / explicit)
        if not candidate.exists():
            # An explicitly named missing file is a caller error, not a SKIP: silently
            # skipping would hide a typo behind a green exit.
            raise SnapshotRejected(f"named snapshot does not exist: {candidate}")
        return _validate_path(root, candidate)

    if not root.is_dir():
        return None
    candidates = sorted(p for p in root.iterdir() if p.suffix.lower() in SNAPSHOT_SUFFIXES)
    if not candidates:
        return None

    # Every candidate is path-validated, so one unsafe entry fails the whole run closed
    # rather than being skipped over.
    validated = [_validate_path(root, p) for p in candidates]
    if len(validated) == 1:
        return validated[0]
    # Rank by the *validated* captured_at, never by filename: nothing enforces a
    # date-prefixed naming convention, so one file named e.g. "zz-old.yaml" would sort last
    # lexically and permanently shadow every fresher capture — silently, at exit 0.
    return max(validated, key=lambda p: load_snapshot(p)[0])


def _load_document(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        # Must land inside the guarded region: an unguarded decode error would escape as a
        # traceback with a non-2 exit, and the result-code table promises exit 2 here.
        raise SnapshotRejected(f"snapshot is not readable UTF-8 text: {path} ({exc})") from exc
    try:
        doc = yaml.load(text, Loader=_StrictSnapshotLoader)  # noqa: S506 - strict subclass
    except SnapshotRejected:
        raise
    except yaml.YAMLError as exc:
        raise SnapshotRejected(f"snapshot is not valid YAML: {path} ({exc})") from exc
    if not isinstance(doc, dict):
        raise SnapshotRejected(
            f"snapshot root must be a mapping, got {type(doc).__name__}: {path}"
        )
    return doc


def _parse_captured_at(raw: Any) -> dt.datetime:
    if isinstance(raw, dt.datetime):
        captured = raw
    elif isinstance(raw, str):
        try:
            captured = dt.datetime.fromisoformat(raw)
        except ValueError as exc:
            raise SnapshotRejected(f"captured_at is not ISO-8601: {raw!r}") from exc
    else:
        raise SnapshotRejected(
            f"captured_at must be a timestamp or ISO-8601 string, got {type(raw).__name__}"
        )
    if captured.tzinfo is None:
        raise SnapshotRejected(
            f"captured_at must carry an explicit timezone offset, got naive {raw!r}"
        )
    return captured.astimezone(dt.UTC)


def _validate_envelope(doc: dict[str, Any]) -> tuple[dt.datetime, dict[str, Any]]:
    keys = set(doc)
    missing = sorted(SNAPSHOT_REQUIRED_FIELDS - keys)
    unknown = sorted(keys - SNAPSHOT_REQUIRED_FIELDS)
    if missing:
        raise SnapshotRejected(f"snapshot is missing required field(s): {missing}")
    if unknown:
        raise SnapshotRejected(
            f"snapshot carries unknown top-level field(s): {unknown}; the schema-v1 "
            f"envelope is closed to exactly {sorted(SNAPSHOT_REQUIRED_FIELDS)}"
        )

    if doc["schema_version"] != SNAPSHOT_SCHEMA_VERSION:
        raise SnapshotRejected(
            f"unsupported schema_version {doc['schema_version']!r}; "
            f"expected {SNAPSHOT_SCHEMA_VERSION!r}"
        )
    if doc["provenance"] != SNAPSHOT_REQUIRED_PROVENANCE:
        raise SnapshotRejected(
            f"provenance must be {SNAPSHOT_REQUIRED_PROVENANCE!r}, got {doc['provenance']!r}"
        )
    # `is not True` on purpose: the string "true" and the integer 1 are not attestations.
    if doc["sanitized"] is not True:
        raise SnapshotRejected(
            f"sanitized must be boolean true, got {doc['sanitized']!r} "
            f"({type(doc['sanitized']).__name__})"
        )

    payload = doc["payload"]
    if not isinstance(payload, dict):
        raise SnapshotRejected(f"payload must be a mapping, got {type(payload).__name__}")
    _validate_payload_shape(payload)

    return _parse_captured_at(doc["captured_at"]), payload


def _validate_payload_shape(payload: dict[str, Any]) -> None:
    """Type-check the payload interior that :func:`_drift` will index into.

    Without this, a malformed interior (``tables`` as a list, a column entry that is not a
    mapping, ...) escapes as a ``TypeError``/``KeyError`` rather than
    :class:`SnapshotRejected` — which would exit non-2 and, worse, could be read as
    ``DRIFT_DETECTED`` by a caller following the documented result-code table.

    Deliberately structural only: emptiness is **not** an error here, because the negative
    fixtures rely on a well-formed-but-empty payload to reach their intended envelope
    violation. Coverage is enforced downstream by the catalog-first checks in
    :func:`_drift`, which is where a vacuously-empty snapshot is caught.
    """
    schemas = payload.get("schemas")
    if not isinstance(schemas, dict):
        raise SnapshotRejected(
            f"payload.schemas must be a mapping, got {type(schemas).__name__}"
        )
    for schema_name, block in schemas.items():
        if not isinstance(block, dict):
            raise SnapshotRejected(
                f"payload.schemas[{schema_name!r}] must be a mapping, "
                f"got {type(block).__name__}"
            )
        tables = block.get("tables", {})
        if not isinstance(tables, dict):
            raise SnapshotRejected(
                f"payload.schemas[{schema_name!r}].tables must be a mapping, "
                f"got {type(tables).__name__}"
            )
        for table_name, table in tables.items():
            if not isinstance(table, dict):
                raise SnapshotRejected(
                    f"payload table {schema_name}.{table_name} must be a mapping, "
                    f"got {type(table).__name__}"
                )
            columns = table.get("columns")
            if not isinstance(columns, list):
                raise SnapshotRejected(
                    f"payload table {schema_name}.{table_name}.columns must be a list, "
                    f"got {type(columns).__name__}"
                )
            for column in columns:
                if not isinstance(column, dict) or not isinstance(column.get("name"), str):
                    raise SnapshotRejected(
                        f"payload table {schema_name}.{table_name} has a column entry "
                        f"without a string 'name': {column!r}"
                    )


def load_snapshot(path: Path) -> tuple[dt.datetime, dict[str, Any]]:
    """Load and closed-validate one snapshot file.

    Returns ``(captured_at, payload)``. Raises :class:`SnapshotRejected` on any envelope
    or parse violation. Public so contract tests can prove their synthetic fixtures
    satisfy the same ``schema-v1`` contract the production path enforces.

    Note this does **not** perform the path-safety or freshness checks — those belong to
    :func:`main`, which owns the sanctioned-root and max-age policy.
    """
    return _validate_envelope(_load_document(path))


def _qcm_fact_tables(payload: dict[str, Any]) -> set[str]:
    biz_dws = payload.get("schemas", {}).get("biz_dws", {}).get("tables", {})
    return {
        name
        for name in biz_dws
        if name.startswith(_QCM_FACT_PREFIX) and name not in _QCM_SIGNAL_TABLES
    }


def _expected_time_columns(catalog: dict[str, Any]) -> set[str]:
    return {p["time_column"].lower() for p in catalog["periods"].values()}


def _period_time_column(catalog: dict[str, Any], fact_name: str) -> str | None:
    """The single time column *this table's own period* declares.

    Matching against the union of all five periods' time columns would let a monthly table
    pass on a ``data_date`` column, i.e. exactly the per-period rename this check exists to
    catch. Returns ``None`` when the name carries no recognizable period token, in which
    case the caller falls back to the union.
    """
    for cfg in catalog["periods"].values():
        suffix = cfg["suffix"]
        if f"{suffix}_" in fact_name or fact_name.endswith(suffix):
            return str(cfg["time_column"]).lower()
    return None


def _drift(payload: dict[str, Any], catalog: dict[str, Any]) -> list[str]:
    msgs: list[str] = []

    # 1. Signal tables present?
    biz_dws = payload.get("schemas", {}).get("biz_dws", {}).get("tables", {})
    expected_signals = {t["name"] for t in catalog.get("signal_tables", [])}
    expected_signal_names = {n.split(".", 1)[1] for n in expected_signals}
    for sig in sorted(expected_signal_names):
        if sig not in biz_dws:
            msgs.append(f"signal table missing in snapshot: biz_dws.{sig}")

    # 2. Dimension tables present + join keys?
    biz_dwd = payload.get("schemas", {}).get("biz_dwd", {}).get("tables", {})
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

    # 3a. Catalog-first period coverage. The per-table loop below derives its subject from
    #     the snapshot, so a snapshot carrying no QCM fact tables at all would iterate zero
    #     times and yield PASS_NO_DRIFT while attesting to nothing. Drive the check from the
    #     catalog instead, mirroring catalog-db-alignment.contract.yml `time_columns_resolve`.
    for period, cfg in catalog["periods"].items():
        suffix = cfg["suffix"]
        if not any(
            name.startswith(_QCM_FACT_PREFIX) and name.endswith(f"{suffix}_total")
            for name in biz_dws
        ):
            msgs.append(
                f"no biz_dws.dws_qcm_*{suffix}_total fact table in snapshot for "
                f"period={period}; catalog declares this period, so the snapshot cannot "
                f"attest to it"
            )

    # 3b. QCM fact tables — check time-column presence, per period where determinable
    expected_times = _expected_time_columns(catalog)
    for fact_name in sorted(_qcm_fact_tables(payload)):
        cols = {c["name"].lower() for c in biz_dws[fact_name]["columns"]}
        own = _period_time_column(catalog, fact_name)
        wanted = {own} if own else expected_times
        if not (cols & wanted):
            msgs.append(
                f"QCM fact table {fact_name} has no expected time column "
                f"(catalog says {sorted(wanted)}; actual cols sample: "
                f"{sorted(cols)[:6]}...)"
            )

    return msgs


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--snapshot",
        type=Path,
        default=None,
        help=(
            f"snapshot file inside {SNAPSHOT_ROOT}/ (bare filename or path; must resolve "
            "inside that root). Omit to auto-select the newest."
        ),
    )
    return parser


def main(
    argv: list[str] | None = None,
    *,
    repo_root: Path | None = None,
    now: dt.datetime | None = None,
) -> int:
    """Validate + diff a sanitized snapshot.

    ``repo_root`` and ``now`` are injectable so tests can run against ``tmp_path`` with a
    fixed clock instead of the live tree and wall-clock time.
    """
    args = _parser().parse_args(argv)
    resolved_repo_root = repo_root or Path(__file__).resolve().parent.parent
    now = now or dt.datetime.now(dt.UTC)

    # `_snapshot_root` validates that the root is not redirected outside the repo, so it
    # must sit inside the guarded region too.
    try:
        root = _snapshot_root(resolved_repo_root)
        selected = _select_snapshot(root, args.snapshot)
    except SnapshotRejected as exc:
        print(f"[diff_biz_schema] {RESULT_REJECT}: {exc}", file=sys.stderr)
        return EXIT_REJECT

    if selected is None:
        print(f"[diff_biz_schema] {RESULT_SKIP_NO_SNAPSHOT}: no snapshot under {root}")
        print(
            "[diff_biz_schema] nothing was verified; this is NOT a pass and says nothing "
            "about current database freshness. See scripts/fetch_biz_schema.py for the "
            "sanctioned route."
        )
        return EXIT_OK

    try:
        captured_at, payload = load_snapshot(selected)
    except SnapshotRejected as exc:
        print(f"[diff_biz_schema] {RESULT_REJECT}: {exc}", file=sys.stderr)
        return EXIT_REJECT

    if captured_at > now + SNAPSHOT_MAX_CLOCK_SKEW:
        print(
            f"[diff_biz_schema] {RESULT_REJECT}: captured_at {captured_at.isoformat()} is in "
            f"the future relative to {now.isoformat()}",
            file=sys.stderr,
        )
        return EXIT_REJECT

    age = now - captured_at
    if age > SNAPSHOT_MAX_AGE:
        print(
            f"[diff_biz_schema] {RESULT_SKIP_STALE}: {selected.name} captured "
            f"{captured_at.isoformat()} is {age.days}d old (max {SNAPSHOT_MAX_AGE.days}d)"
        )
        print(
            "[diff_biz_schema] nothing was verified; this is NOT a pass and says nothing "
            "about current database freshness."
        )
        return EXIT_OK

    msgs = _drift(payload, load_catalog())
    if not msgs:
        print(
            f"[diff_biz_schema] {RESULT_PASS}: catalog matches snapshot {selected.name} "
            f"(captured {captured_at.isoformat()})"
        )
        return EXIT_OK

    print(f"[diff_biz_schema] {RESULT_DRIFT}: snapshot {selected.name}", file=sys.stderr)
    for m in msgs:
        print(f"  - {m}", file=sys.stderr)
    print(
        "[diff_biz_schema] update biz_catalog/qcm_catalog.yaml + "
        "skills/mj-ddd-semantics/SKILL.md to match",
        file=sys.stderr,
    )
    return EXIT_DRIFT


if __name__ == "__main__":
    raise SystemExit(main())
