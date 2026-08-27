"""check_cross_carrier.py — V12 "Cross-Carrier Structure" (warning telemetry).

Epic #499 plan §5.8. V12 reports the manifest ↔ registry ↔ artifact ↔ lock ↔
fidelity relationship for the Codex carrier set. Four of those five surfaces
have a blocking owner already:

    manifest   sdd/development-agent.yml                        V8         BLOCKING
    registry   sdd/workflows/development-agent-workflows.yml    V9 PJ050-053  BLOCKING
    artifact   .agents/skills/**/SKILL.md + .agents/README.md   V10        BLOCKING
    lock       .agents.lock.json                                V9 PJ030-034 / V10  BLOCKING
    fidelity   sdd/adapters/codex-skill-fidelity.yml            NO CI MOUNT

The fidelity row is the exception and must not be described otherwise:
`check_fidelity_attestations.py` exists and passes on the real tree, but it is
NOT a CI step (Epic #499 follow-up F11, deliberately still open — mounting a new
gate is a separate Owner governance action). So for that one surface V12's X07
join is the ONLY CI-visible signal, which is why X07 warns rather than passes
when the index is missing.

This script does NOT re-implement any of their validation and is NOT a second
opinion on it. It owns the CROSS-surface joins that no single blocking gate
carries end to end — "is the same carrier set present, and consistently shaped,
on all five surfaces at once" — and it reports them as telemetry.

Per plan §5.8 V12 stays warning-only in this program: it is mounted with
`continue-on-error: true` and a blocking flip is explicitly a separate
plan/toggle. PR-C2 registers the observation anchor from the first real CI run
of merged PR-C1; until then the anchor is `PENDING_PR_C1_FIRST_CI`.

Counts are always DERIVED from the manifest, never hardcoded (AC-04): this
script contains no 5/13/18/20 constant.

No git history is read. `ci.yml` checks out at depth 1, so anything
history-dependent would pass locally and degrade in CI.

Result codes (also written to `--status-json`):

``EXECUTED_CLEAN``          every cross-surface join closed
``EXECUTED_WITH_FINDINGS``  at least one join did not close
``SKIP_MANIFEST_V1``        pre-cutover tree; neutral for the streak (§5.8)
``ERROR_UNREADABLE``        a surface could not be read; nothing was concluded

Exit codes: 0 clean or skip; 1 findings; 2 unreadable. The CI step is
non-blocking, so a non-zero exit surfaces as a red step inside a green job —
which is exactly the intended warning visibility.

Read-only; no secrets; no network.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.sdd._common.cli import Severity, Summary  # noqa: E402
from scripts.sdd._common.projection_loader import (  # noqa: E402
    SKILLS_README_KEY,
    LockVerificationError,
    classify_lock,
    read_lock,
    verify_lock_v2,
)

GATE_ID = "V12"
GATE_NAME = "Cross-Carrier Structure"
STATUS_SCHEMA = "cross-carrier-status-v1"
OBSERVATION_ANCHOR = "PENDING_PR_C1_FIRST_CI"

KNOWN_MANIFEST_SCHEMA_VERSIONS = frozenset({1, 2})

MANIFEST_RELPATH = Path("sdd/development-agent.yml")
REGISTRY_RELPATH = Path("sdd/workflows/development-agent-workflows.yml")
FIDELITY_RELPATH = Path("sdd/adapters/codex-skill-fidelity.yml")
SKILLS_RELDIR = Path(".agents/skills")

# entry_kind expected for each carrier strategy (plan §2.6 closed union).
KIND_FOR_STRATEGY = {"byte-copy": "skill-byte-copy", "translated": "skill-translated"}


class SurfaceError(RuntimeError):
    """A surface could not be read; the run concludes nothing."""


def _artifact_key(cap_id: str) -> str:
    return f".agents/skills/{cap_id}/SKILL.md"


def load_manifest(repo_root: Path) -> dict[str, Any]:
    path = repo_root / MANIFEST_RELPATH
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise SurfaceError(f"{MANIFEST_RELPATH}: {exc}") from exc
    if not isinstance(data, dict):
        raise SurfaceError(f"{MANIFEST_RELPATH}: not a mapping")
    version = data.get("schema_version")
    if version not in KNOWN_MANIFEST_SCHEMA_VERSIONS:
        # Fail closed. Reporting an unknown schema as the pre-cutover SKIP would
        # label it streak-neutral (plan §5.8) while concluding nothing about it.
        raise SurfaceError(
            f"{MANIFEST_RELPATH}: unknown schema_version {version!r}"
            f" (known: {sorted(KNOWN_MANIFEST_SCHEMA_VERSIONS)})"
        )
    return data


def carrier_partition(manifest: dict[str, Any]) -> dict[str, str]:
    """capability id -> codex_carrier, for rows that declare a carrier."""
    out: dict[str, str] = {}
    for cap in manifest.get("capabilities") or []:
        if not isinstance(cap, dict):
            continue
        carrier = cap.get("codex_carrier")
        if carrier in KIND_FOR_STRATEGY:
            out[str(cap.get("id"))] = str(carrier)
    return out


def load_registry(repo_root: Path) -> Any:
    path = repo_root / REGISTRY_RELPATH
    if not path.is_file():
        raise SurfaceError(f"{REGISTRY_RELPATH}: absent")
    # Local import: same loader the generator and V9 use (one-implementation rule).
    from scripts.sdd._common.skill_renderer import TranslationError, load_workflow_registry

    try:
        return load_workflow_registry(path.read_text(encoding="utf-8"))
    except (OSError, TranslationError) as exc:
        raise SurfaceError(f"{REGISTRY_RELPATH}: {exc}") from exc


def load_fidelity_capabilities(repo_root: Path) -> set[str] | None:
    """Translated capabilities covered by the PR-C0 attestation index.

    Returns None when the index is absent — that is a legitimate pre-PR-C0
    state, reported as an informational skip rather than a finding.
    """
    path = repo_root / FIDELITY_RELPATH
    if not path.is_file():
        return None
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise SurfaceError(f"{FIDELITY_RELPATH}: {exc}") from exc
    if not isinstance(data, dict):
        raise SurfaceError(f"{FIDELITY_RELPATH}: not a mapping")
    covered: set[str] = set()
    for tranche in data.get("tranches") or []:
        if isinstance(tranche, dict):
            covered.update(str(c) for c in tranche.get("capability_ids") or [])
    return covered


def on_disk_carriers(repo_root: Path) -> set[str]:
    skills_dir = repo_root / SKILLS_RELDIR
    if not skills_dir.is_dir():
        return set()
    return {
        entry.name
        for entry in skills_dir.iterdir()
        if entry.is_dir() and (entry / "SKILL.md").is_file()
    }


def run_checks(repo_root: Path) -> tuple[Summary, dict[str, Any]]:
    """Cross-surface joins. Returns (summary, status payload fragment)."""
    summary = Summary()
    manifest = load_manifest(repo_root)
    schema_version = manifest.get("schema_version")
    partition = carrier_partition(manifest)

    surfaces: dict[str, Any] = {
        "manifest_schema_version": schema_version,
        "carriers_declared": len(partition),
        "carriers_by_strategy": {
            s: sorted(c for c, v in partition.items() if v == s)
            for s in sorted(KIND_FOR_STRATEGY)
        },
    }

    if schema_version != 2:
        summary.add(
            Severity.PASS,
            f"manifest schema_version={schema_version!r} — pre-cutover tree,"
            " cross-carrier joins do not apply yet (neutral SKIP)",
        )
        return summary, surfaces

    registry = load_registry(repo_root)
    fidelity = load_fidelity_capabilities(repo_root)
    disk = on_disk_carriers(repo_root)

    translated = {c for c, v in partition.items() if v == "translated"}
    registry_caps = {w.capability_id for w in registry.workflows.values()}
    surfaces["registry_workflows"] = len(registry.workflows)
    surfaces["registry_edges"] = len(registry.edges)
    surfaces["artifacts_on_disk"] = len(disk)
    # Recorded at load time, not at X07: the lock section below can return early,
    # and the status artifact should describe every surface it actually read.
    surfaces["fidelity_index"] = "absent" if fidelity is None else "present"

    # --- X02 translated <-> registry bijection -----------------------------
    if translated == registry_caps:
        summary.add(
            Severity.PASS,
            f"X02 translated<->registry bijection closed ({len(translated)} capabilities)",
        )
    else:
        for cap in sorted(translated - registry_caps):
            summary.add(Severity.WARN, f"X02 translated {cap!r} has no registry workflow")
        for cap in sorted(registry_caps - translated):
            summary.add(
                Severity.WARN, f"X02 registry workflow for {cap!r} has no translated capability"
            )

    # --- X03 carrier <-> artifact on disk ----------------------------------
    missing = sorted(set(partition) - disk)
    orphan = sorted(disk - set(partition))
    if not missing and not orphan:
        summary.add(
            Severity.PASS, f"X03 carrier<->artifact closed ({len(partition)} SKILL.md present)"
        )
    for cap in missing:
        summary.add(Severity.WARN, f"X03 carrier {cap!r} has no artifact on disk")
    for cap in orphan:
        summary.add(Severity.WARN, f"X06 artifact dir {cap!r} has no manifest carrier (orphan)")

    # --- X04/X05 carrier <-> lock entry ------------------------------------
    # read_lock / classify_lock raise LockVerificationError (a ValueError), NOT
    # SurfaceError — an unreadable ledger must surface as ERROR_UNREADABLE, never
    # as a traceback that exit-code-maps onto EXECUTED_WITH_FINDINGS.
    try:
        raw_lock = read_lock(repo_root)
    except LockVerificationError as exc:
        raise SurfaceError(f".agents.lock.json: {exc}") from exc
    if raw_lock is None:
        summary.add(Severity.WARN, "X04 .agents.lock.json absent — no ownership ledger")
        surfaces["lock_class"] = "absent"
        return summary, surfaces
    try:
        lock_class = classify_lock(raw_lock)
    except LockVerificationError as exc:
        raise SurfaceError(f".agents.lock.json: {exc}") from exc
    surfaces["lock_class"] = lock_class
    if lock_class != "v2":
        summary.add(
            Severity.WARN,
            f"X04 manifest is v2 but lock classifies as {lock_class!r}"
            " — cutover/rollback mismatch (V9/V10 own the verdict)",
        )
        return summary, surfaces
    try:
        lock = verify_lock_v2(raw_lock)
    except LockVerificationError as exc:
        raise SurfaceError(f".agents.lock.json: {exc}") from exc
    surfaces["lock_entries"] = len(lock.entries)
    surfaces["lock_kinds"] = {
        kind: sum(1 for e in lock.entries.values() if e.entry_kind == kind)
        for kind in sorted({e.entry_kind for e in lock.entries.values()})
    }

    kind_mismatch = 0
    for cap, strategy in sorted(partition.items()):
        entry = lock.entries.get(_artifact_key(cap))
        if entry is None:
            summary.add(Severity.WARN, f"X04 carrier {cap!r} has no lock entry")
            kind_mismatch += 1
            continue
        expected_kind = KIND_FOR_STRATEGY[strategy]
        if entry.entry_kind != expected_kind:
            summary.add(
                Severity.WARN,
                f"X04 carrier {cap!r} is {strategy!r} but its lock entry_kind is"
                f" {entry.entry_kind!r} (expected {expected_kind!r})",
            )
            kind_mismatch += 1
        if entry.owner != f"capability:{cap}":
            summary.add(
                Severity.WARN,
                f"X04 carrier {cap!r} lock owner is {entry.owner!r}"
                f" (expected 'capability:{cap}')",
            )
            kind_mismatch += 1
    if kind_mismatch == 0:
        summary.add(
            Severity.PASS,
            f"X04 carrier<->lock closed ({len(partition)} entries, kind+owner consistent)",
        )

    skill_keys = {
        k for k, e in lock.entries.items() if e.entry_kind in set(KIND_FOR_STRATEGY.values())
    }
    lock_orphans = sorted(skill_keys - {_artifact_key(c) for c in partition})
    for key in lock_orphans:
        summary.add(Severity.WARN, f"X05 lock skill entry {key!r} has no manifest carrier")
    if not lock_orphans:
        summary.add(Severity.PASS, "X05 no orphan skill entries in the lock")

    # --- X08 README artifact + lock entry ----------------------------------
    readme_ok = (repo_root / SKILLS_README_KEY).is_file()
    readme_locked = SKILLS_README_KEY in lock.entries
    if readme_ok and readme_locked:
        summary.add(Severity.PASS, f"X08 {SKILLS_README_KEY} present and lock-owned")
    else:
        if not readme_ok:
            summary.add(Severity.WARN, f"X08 {SKILLS_README_KEY} is missing on disk")
        if not readme_locked:
            summary.add(Severity.WARN, f"X08 {SKILLS_README_KEY} has no lock entry")

    # --- X07 translated <-> fidelity attestation coverage ------------------
    if fidelity is None:
        # NOT a PASS. The index is a permanent tracked artifact since PR-C0, and
        # nothing else in CI reads it (follow-up F11 — check_fidelity_attestations
        # has no mount), so a silent degrade-to-default here would make a deleted
        # or renamed governance artifact indistinguishable from a healthy tree.
        summary.add(
            Severity.WARN,
            f"X07 {FIDELITY_RELPATH} is absent — translated-carrier fidelity coverage"
            " is unasserted, and no other CI step reads this surface",
        )
    elif fidelity == translated:
        summary.add(
            Severity.PASS,
            f"X07 fidelity index covers exactly the translated set ({len(translated)})",
        )
    else:
        for cap in sorted(translated - fidelity):
            summary.add(Severity.WARN, f"X07 translated {cap!r} is not in the fidelity index")
        for cap in sorted(fidelity - translated):
            summary.add(
                Severity.WARN, f"X07 fidelity index lists {cap!r}, which is not translated"
            )

    # --- X09 registry edge substitute closure ------------------------------
    from scripts.sdd._common.skill_renderer import TranslationError, expand_wildcard

    all_ids = {str(c.get("id")) for c in manifest.get("capabilities") or [] if isinstance(c, dict)}
    unsubstituted = 0
    for edge in sorted(registry.edges.values(), key=lambda e: e.edge_id):
        if edge.to_id.endswith("*"):
            # Mirror the engine exactly (agents_sync._v2_desired_state): a wildcard
            # edge NEVER counts as having a carrier target, so it always needs a
            # substitute. Skipping it because some expanded id happens to be a
            # carrier would let V12 report closure for a tree `sync` refuses to build.
            try:
                expand_wildcard(edge.to_id, all_ids)
            except TranslationError:
                summary.add(Severity.WARN, f"X09 edge {edge.edge_id!r} wildcard does not expand")
                unsubstituted += 1
                continue
            targets = set()
        else:
            targets = {edge.to_id}
        if targets & set(partition):
            continue
        if edge.substitute is None:
            summary.add(
                Severity.WARN,
                f"X09 edge {edge.edge_id!r} targets {edge.to_id!r} which has no carrier"
                " and no codex_substitute",
            )
            unsubstituted += 1
    if unsubstituted == 0:
        summary.add(
            Severity.PASS,
            f"X09 registry edge closure holds ({len(registry.edges)} edges:"
            " every no-carrier target has a substitute)",
        )

    return summary, surfaces


def build_status(summary: Summary, surfaces: dict[str, Any], result_code: str) -> dict[str, Any]:
    return {
        "schema_version": STATUS_SCHEMA,
        "gate_id": GATE_ID,
        "gate_name": GATE_NAME,
        "posture": "warning",
        "observation_anchor": OBSERVATION_ANCHOR,
        "result_code": result_code,
        "pass_count": summary.pass_count,
        "warn_count": summary.warn_count,
        "fail_count": summary.fail_count,
        "surfaces": surfaces,
        "messages": list(summary.messages),
    }


def write_status(path: Path, payload: dict[str, Any]) -> None:
    """Deterministic status artifact. Creates its parent — the CI job does not."""
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def main(argv: list[str] | None = None, repo_root: Path | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="check_cross_carrier.py",
        description=(
            f"{GATE_ID} / {GATE_NAME} — cross-surface carrier telemetry"
            " (warning-only; plan §5.8)"
        ),
    )
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument(
        "--status-json",
        type=Path,
        default=None,
        help="write the machine-readable status artifact to this path",
    )
    args = parser.parse_args(argv)
    root = repo_root or args.repo_root or Path(__file__).resolve().parents[2]

    print(f"=== {GATE_ID} {GATE_NAME} (warning telemetry; anchor {OBSERVATION_ANCHOR}) ===")
    try:
        summary, surfaces = run_checks(root)
    except SurfaceError as exc:
        print(f"  [FAIL] surface unreadable: {exc}", file=sys.stderr)
        print("nothing was concluded — an unreadable surface is not a pass", file=sys.stderr)
        payload = build_status(Summary(), {"error": str(exc)}, "ERROR_UNREADABLE")
        if args.status_json is not None:
            write_status(args.status_json, payload)
        print("ERROR_UNREADABLE")
        return 2

    summary.print_messages()
    if surfaces.get("manifest_schema_version") != 2:
        result_code = "SKIP_MANIFEST_V1"
    elif summary.warn_count or summary.fail_count:
        result_code = "EXECUTED_WITH_FINDINGS"
    else:
        result_code = "EXECUTED_CLEAN"

    print(
        f"=== Summary === pass: {summary.pass_count} /"
        f" warnings: {summary.warn_count} / errors: {summary.fail_count}"
    )
    if args.status_json is not None:
        write_status(args.status_json, build_status(summary, surfaces, result_code))
        print(f"status written = {args.status_json}")
    print(result_code)
    return 1 if result_code == "EXECUTED_WITH_FINDINGS" else 0


if __name__ == "__main__":
    raise SystemExit(main())
