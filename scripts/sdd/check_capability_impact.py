"""scripts/sdd/check_capability_impact.py — file-list→capability impact reporter (NOT a gate).

Backs Step 1 (Impact scope) of ``sdd/workflows/cross-capability-change.md``:
maps a file list onto the capability tree and reports which capabilities are
affected. Input is a plain file list — the plan's touch list *before*
implementation, or ``git diff --name-only | ... --stdin`` *during*
implementation — so the tool works at both stages without requiring a diff
to exist (git is deliberately not embedded).

Boundary (per sdd/gates.md L34): this is NOT G4. The plan-vs-diff *semantic*
gate stays manual-canonical (PR-template "Plan-vs-Diff Scope Declaration" +
Stage 9 /mj-agent-flow-scope-drift skill); this script automates only the
deterministic file→capability mapping half. The ``check_`` prefix follows
scripts/sdd family naming; the semantic here is *reporter* — unmapped files
are WARN (exit 0) unless ``--strict``.

Mapping sources (lightweight, declared-structure only):

1. Direct prefix: ``capabilities/<domain>/<slug>/**`` → that capability
   (capability-relative contracts/ + behavior.feature are covered here).
2. ``cross_capability_refs[].surface`` in spec.yml + trace.yml: first path
   token. Surfaces are free text in schema v1.2, so `` + ``-joined multi-path
   lists, ``:<line-range>`` / ``:<symbol>`` suffixes and ``(annotations)``
   are stripped, and pure-prose surfaces are tolerated by skipping (not
   indexed, no warning). A hit records BOTH capabilities with a
   ``coupling-edge <declaring>→<target>`` label — semantics: the coupling
   point changed and the target owner should co-review; NOT "target code
   was edited". Glob-shaped surfaces (``docker/compose.*.yml``) never match
   (index is exact-path).
3. ``links[].tests[]`` in trace.yml (``::test-id`` suffix stripped) →
   declaring capability (direct attribution).

unmapped ≠ error: spec.yml has no owned_paths[] field yet (full ownership
mapping is the registered TBD in cross-capability-change.md §TBD), so files
outside the declared structure go to per-file WARN for human judgement.
Shape deviations in spec/trace YAML (missing fields / wrong types) are
tolerated as skip + WARN, never a traceback.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.sdd._common.cli import Severity, Summary  # noqa: E402
from scripts.sdd._common.discovery import (  # noqa: E402
    discover_capabilities,
    resolve_display_path,
)

_SCRIPT_NAME = "check_capability_impact"
_PAREN_RE = re.compile(r"\([^)]*\)")


@dataclass(frozen=True)
class CouplingEdge:
    """One declared coupling point: ``declaring`` capability's ref → ``target``."""

    declaring: str
    target: str


@dataclass
class PathIndex:
    """Posix-keyed mapping index built from the capability tree."""

    prefixes: dict[str, str] = field(default_factory=dict)  # "capabilities/<d>/<s>/" → cap id
    surfaces: dict[str, set[CouplingEdge]] = field(default_factory=dict)  # path → edges
    tests: dict[str, set[str]] = field(default_factory=dict)  # path → declaring cap ids
    warnings: list[str] = field(default_factory=list)  # shape deviations seen at build time


@dataclass
class ImpactReport:
    """classify() result: per-capability hits + unmapped + the deduped input list."""

    affected: dict[str, list[tuple[str, str]]] = field(default_factory=dict)  # cap → (file, via)
    unmapped: list[str] = field(default_factory=list)
    files: list[str] = field(default_factory=list)


def normalize_path(raw: str) -> str:
    """Posix-normalize one input path: backslash→slash, trim, drop leading ``./``."""
    path = raw.strip().replace("\\", "/")
    while path.startswith("./"):
        path = path[2:]
    return path


def _first_path_token(surface: object) -> str | None:
    """Extract the first path-like token from a ``cross_capability_refs[].surface`` value.

    Tolerates every shape observed in-tree: `` + ``-joined multi-path lists,
    ``(parenthesised annotations)``, ``:<line-range>`` / ``:<symbol>`` suffixes,
    prose tails without parentheses, and pure-prose surfaces. Returns None when
    no path-like token (containing ``/`` or ``.``) leads the surface.
    """
    if not isinstance(surface, str) or not surface.strip():
        return None
    first_segment = surface.split(" + ", 1)[0]
    cleaned = _PAREN_RE.sub(" ", first_segment).strip()
    if not cleaned:
        return None
    token = cleaned.split()[0].split(":", 1)[0].strip()
    if not token or ("/" not in token and "." not in token):
        return None
    return normalize_path(token)


def _load_yaml_mapping(path: Path, display: str, warnings: list[str]) -> dict[str, object] | None:
    """Read one YAML file; return its mapping root or None (missing / unparseable / non-dict)."""
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except (yaml.YAMLError, OSError) as exc:
        warnings.append(f"{display}: parse failed ({exc}) — skipped")
        return None
    if not isinstance(data, dict):
        warnings.append(f"{display}: root is {type(data).__name__}, not a mapping — skipped")
        return None
    return data


def _index_cross_refs(
    data: dict[str, object], declaring: str, display: str, index: PathIndex
) -> None:
    """Index ``cross_capability_refs[].surface`` first-path-tokens as coupling edges."""
    refs = data.get("cross_capability_refs")
    if refs is None:
        return
    if not isinstance(refs, list):
        index.warnings.append(
            f"{display}: cross_capability_refs is {type(refs).__name__}, not a list — skipped"
        )
        return
    for pos, entry in enumerate(refs):
        if not isinstance(entry, dict):
            index.warnings.append(f"{display}: cross_capability_refs[{pos}] not a mapping — skipped")
            continue
        target = entry.get("target")
        if not isinstance(target, str) or not target.strip():
            index.warnings.append(
                f"{display}: cross_capability_refs[{pos}] target missing/empty — skipped"
            )
            continue
        surface = entry.get("surface")
        if not isinstance(surface, str) or not surface.strip():
            index.warnings.append(
                f"{display}: cross_capability_refs[{pos}] surface missing/empty — skipped"
            )
            continue
        token = _first_path_token(surface)
        if token is None:
            # pure-prose surface (legal free text in schema v1.2) — not machine-mappable
            continue
        index.surfaces.setdefault(token, set()).add(
            CouplingEdge(declaring=declaring, target=target.strip())
        )


def _index_trace_tests(
    trace: dict[str, object], declaring: str, display: str, index: PathIndex
) -> None:
    """Index trace.yml ``links[].tests[]`` paths (``::test-id`` stripped) → declaring cap."""
    links = trace.get("links")
    if links is None:
        return
    if not isinstance(links, list):
        index.warnings.append(
            f"{display}: links is {type(links).__name__}, not a list — skipped"
        )
        return
    for pos, link in enumerate(links):
        if not isinstance(link, dict):
            index.warnings.append(f"{display}: links[{pos}] not a mapping — skipped")
            continue
        tests = link.get("tests")
        if tests is None:
            continue
        if not isinstance(tests, list):
            index.warnings.append(
                f"{display}: links[{pos}].tests is {type(tests).__name__}, not a list — skipped"
            )
            continue
        for entry in tests:
            if not isinstance(entry, str) or not entry.strip():
                index.warnings.append(
                    f"{display}: links[{pos}].tests contains a non-string entry — skipped"
                )
                continue
            path = normalize_path(entry.split("::", 1)[0])
            if path:
                index.tests.setdefault(path, set()).add(declaring)


def build_path_index(repo_root: Path) -> PathIndex:
    """Build the file→capability mapping index from all discovered capabilities."""
    index = PathIndex()
    for cap_dir in discover_capabilities(repo_root):
        rel = resolve_display_path(cap_dir, repo_root).replace("\\", "/")
        fallback_id = f"{cap_dir.parent.name}.{cap_dir.name}"

        spec = _load_yaml_mapping(cap_dir / "spec.yml", f"{rel}/spec.yml", index.warnings)
        spec_id = spec.get("id") if spec else None
        cap_id = spec_id.strip() if isinstance(spec_id, str) and spec_id.strip() else fallback_id

        index.prefixes[f"{rel}/"] = cap_id
        if spec is not None:
            _index_cross_refs(spec, cap_id, f"{rel}/spec.yml", index)

        trace = _load_yaml_mapping(cap_dir / "trace.yml", f"{rel}/trace.yml", index.warnings)
        if trace is not None:
            trace_id = trace.get("capability")
            declaring = (
                trace_id.strip() if isinstance(trace_id, str) and trace_id.strip() else cap_id
            )
            _index_cross_refs(trace, declaring, f"{rel}/trace.yml", index)
            _index_trace_tests(trace, declaring, f"{rel}/trace.yml", index)
    return index


def classify(files: Iterable[str], index: PathIndex) -> ImpactReport:
    """Map normalized + deduped input files onto the index; unmatched → unmapped."""
    report = ImpactReport()
    seen: set[str] = set()
    for raw in files:
        path = normalize_path(raw)
        if not path or path in seen:
            continue
        seen.add(path)
        report.files.append(path)

    for path in report.files:
        hits: list[tuple[str, str]] = []
        for prefix, cap_id in index.prefixes.items():
            if path.startswith(prefix):
                hits.append((cap_id, "capabilities/ prefix"))
        for cap_id in sorted(index.tests.get(path, ())):
            hits.append((cap_id, "trace.yml links[].tests[]"))
        for edge in sorted(index.surfaces.get(path, ()), key=lambda e: (e.declaring, e.target)):
            via = f"coupling-edge {edge.declaring}→{edge.target}"
            hits.append((edge.declaring, via))
            hits.append((edge.target, via))
        if not hits:
            report.unmapped.append(path)
            continue
        for cap_id, via in hits:
            bucket = report.affected.setdefault(cap_id, [])
            if (path, via) not in bucket:
                bucket.append((path, via))
    return report


def _build_argparser() -> argparse.ArgumentParser:
    """Local argparser — input is a file list, not contract discovery, so the
    shared ``_common.cli.build_argparser`` factory (--dry-run/--capability/--all)
    does not fit."""
    parser = argparse.ArgumentParser(
        prog=_SCRIPT_NAME,
        description=(
            "Report which capabilities a file list touches "
            "(cross-capability-change.md Step 1 helper; reporter, not a gate)"
        ),
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="repo-relative file paths (e.g. a plan's touch list)",
    )
    parser.add_argument(
        "--stdin",
        action="store_true",
        help="additionally read newline-separated paths from stdin "
        "(e.g. git diff --name-only | %(prog)s --stdin)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 when any file is unmapped or any mapping-source shape warning fired",
    )
    return parser


def main(argv: list[str] | None = None, repo_root: Path | None = None) -> int:
    """Impact reporter entry point. ``repo_root`` injectable for tests (#217)."""
    args = _build_argparser().parse_args(argv)
    root = repo_root if repo_root is not None else _REPO_ROOT

    raw_files: list[str] = list(args.files)
    if args.stdin:
        raw_files.extend(sys.stdin.read().splitlines())

    if not (root / "capabilities").exists():
        print(f"{_SCRIPT_NAME}: no capabilities/ directory under {root} — nothing can map")

    index = build_path_index(root)
    report = classify(raw_files, index)

    summary = Summary()
    for warning in index.warnings:
        summary.add(Severity.WARN, warning)
    for cap_id in sorted(report.affected):
        for path, via in report.affected[cap_id]:
            summary.add(Severity.PASS, f"{cap_id}: {path} (via {via})")
    for path in report.unmapped:
        summary.add(Severity.WARN, f"unmapped: {path}（交人工 + /mj-agent-flow-scope-drift 判定）")
    summary.print_messages()

    print(
        f"{_SCRIPT_NAME}: {len(report.affected)} capability(ies) affected / "
        f"{len(report.unmapped)} unmapped (over {len(report.files)} files)"
    )
    return summary.exit_code(strict=args.strict)


if __name__ == "__main__":
    sys.exit(main())
