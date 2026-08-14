"""scripts/sdd/task0_freeze.py — Epic #499 Task-0 baseline emit / freeze verification.

Implements the carrier for `plans/[PLAN]_codex_cross_carrier_kernel.md` §4.2 (Task-0
timing / records) and §4.3 (freeze enforcement). Before this script the §4.3 rule
"compare merge-base -> HEAD against Task-0 identity; any other difference is
`STOP_FROZEN_SURFACE_DRIFT`" had no executable carrier at all.

Two modes:

``--emit``
    Recompute the tracked-path inventory and the frozen-surface identity from a git
    revision and write both JSON artifacts. Deterministic: same revision in, same
    bytes out, on any platform.

``--check``
    Recompute from the current revision and compare the **frozen surfaces only**
    against the committed baseline. The full inventory is a baseline snapshot, not a
    checked invariant — the tree is expected to grow as the Epic proceeds.

Content basis is the **git blob**, never the worktree file. `.gitattributes` sets
``* text=auto`` with per-type ``eol=lf`` overrides, so on Windows a checked-out
``.md`` carries CRLF while its blob carries LF. Hashing worktree bytes would mint a
platform-local identity that Linux CI could never reproduce; hashing blob content is
reproducible from the commit alone.

Only git-**tracked** paths are visited. That is what keeps this script compliant with
§1.1's prohibition on opening, printing, hashing or transmitting ignored/private
harness state (`.claude/scheduled_tasks.lock` and friends): such paths are untracked,
so they are excluded by construction rather than by an allowlist that could rot.

Identity is `(path, mode, sha256)`, not content alone. A mode flip — an exec bit
landing on a frozen hook script, or a regular file becoming a symlink — is a change by
git's own accounting and must trip §4.3, even though the blob is byte-identical.
Gitlinks (mode 160000) are recorded rather than skipped, because a submodule grafted
under a hard-frozen prefix attaches arbitrary third-party content to that surface; they
have no blob, so they get a domain-separated stand-in digest (`gitlink_digest`).

Result codes (printed on the last line):

``TASK0_FREEZE_CLEAN``          exit 0 — every frozen surface matches the baseline
``STOP_FROZEN_SURFACE_DRIFT``   exit 1 — a hard-frozen path changed/appeared/vanished
``CONTROLLED_SURFACE_CHANGED``  exit 1 — the controlled-frozen surface changed
``ERROR_NO_BASELINE``           exit 2 — baseline artifact absent; nothing was verified
``ERROR_MALFORMED_BASELINE``    exit 2 — baseline artifact unreadable; nothing verified
``ERROR_NOT_A_REPO``            exit 2 — git invocation failed; nothing was verified

An absent or malformed baseline exits 2, never 0: a missing baseline is not a pass.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import threading
from collections.abc import Iterable
from pathlib import Path
from typing import Any, NamedTuple

EPIC_ID = 499
UNIT_ID = "PR-0d"

INVENTORY_SCHEMA = "task0-inventory-v1"
IDENTITY_SCHEMA = "task0-freeze-identity-v1"

DEFAULT_OUT_DIR = Path("evidence/development-agent-v8")
INVENTORY_NAME = "task0-inventory.json"
IDENTITY_NAME = "task0-freeze-identity.json"

# --- frozen surfaces, transcribed from plan §1.1 -----------------------------------
# The plan writes `capabilities/{CLAUDE,AGENTS}.md`; brace groups are expanded here so
# the matcher stays a plain string comparison with no glob semantics to get wrong.
HARD_FROZEN_PREFIXES: tuple[str, ...] = (".claude/",)
HARD_FROZEN_EXACT: tuple[str, ...] = (
    ".claudeignore",
    ".mcp.json",
    "CLAUDE.md",
    "capabilities/CLAUDE.md",
    "capabilities/AGENTS.md",
    "docker/CLAUDE.md",
    "docker/AGENTS.md",
    "src/mj_agent/CLAUDE.md",
    "src/mj_agent/AGENTS.md",
    "tests/CLAUDE.md",
    "tests/AGENTS.md",
    "tests/unit/test_guard_git_workflow_hook.py",
)
CONTROLLED_FROZEN_EXACT: tuple[str, ...] = ("AGENTS.md",)

# --- owning-surface taxonomy -------------------------------------------------------
# First match wins, so the frozen buckets shadow the generic prefixes below them
# (e.g. `src/mj_agent/AGENTS.md` is hard-frozen, not runtime-src).
SURFACE_PREFIXES: tuple[tuple[str, str], ...] = (
    (".agents/", "generated-projection"),
    (".codex/", "generated-projection"),
    (".github/", "ci-workflow"),
    ("policies/", "kernel-policies"),
    ("sdd/", "kernel-sdd"),
    ("capabilities/", "capability"),
    ("src/", "runtime-src"),
    ("tests/", "tests"),
    ("scripts/", "scripts"),
    ("docker/", "docker"),
    ("decisions/", "decisions"),
    ("plans/", "plans"),
    ("docs/", "docs"),
    ("evidence/", "evidence"),
    ("archive/", "archive"),
    ("config/", "config"),
)
SURFACE_EXACT: tuple[tuple[str, str], ...] = (
    (".agents.lock.json", "generated-projection"),
)

SURFACE_HARD_FROZEN = "hard-frozen"
SURFACE_CONTROLLED_FROZEN = "controlled-frozen"
SURFACE_REPO_ROOT = "repo-root"


class Entry(NamedTuple):
    """One tracked path at a revision."""

    path: str
    mode: str
    blob: str
    sha256: str
    surface: str


class GitError(RuntimeError):
    """git invocation failed."""


def _git(repo_root: Path, *args: str) -> bytes:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(repo_root),
        capture_output=True,
    )
    if proc.returncode != 0:
        raise GitError(
            f"git {' '.join(args)} failed (rc={proc.returncode}): "
            f"{proc.stderr.decode('utf-8', 'replace').strip()}"
        )
    return proc.stdout


def resolve_rev(repo_root: Path, rev: str) -> str:
    """Return the full commit SHA for ``rev``."""
    return _git(repo_root, "rev-parse", rev).decode().strip()


def list_tree(repo_root: Path, rev: str) -> list[tuple[str, str, str, str]]:
    """Return ``(mode, object_type, sha1, path)`` for every entry tracked at ``rev``.

    ``-r`` already recurses into trees, so the only object types that reach us are
    ``blob`` (regular file mode 100644 / executable 100755 / symlink 120000) and
    ``commit`` (a gitlink, mode 160000).

    Gitlinks are **kept**, not skipped. A gitlink has no blob content in this tree,
    but it is still a tracked entry that can graft arbitrary third-party content under
    a hard-frozen prefix; dropping it would make that graft invisible to the inventory,
    to the frozen counts and to the identity digest alike. See ``gitlink_digest`` for
    how such an entry is given a comparable digest.

    NUL-delimited so paths containing spaces or non-ASCII survive intact.
    """
    raw = _git(repo_root, "ls-tree", "-r", "-z", rev)
    out: list[tuple[str, str, str, str]] = []
    for record in raw.split(b"\x00"):
        if not record:
            continue
        meta, _, path = record.partition(b"\t")
        mode, obj_type, sha = meta.decode().split()
        out.append((mode, obj_type, sha, path.decode("utf-8")))
    return out


def gitlink_digest(commit_sha1: str) -> str:
    """Digest standing in for a gitlink, which has no blob content of its own.

    Deliberately domain-separated from any real blob digest by the ``gitlink:``
    prefix, so a gitlink can never collide with a file whose content happens to be
    the same 40 hex characters.
    """
    return hashlib.sha256(f"gitlink:{commit_sha1}".encode()).hexdigest()


def blob_digests(repo_root: Path, blobs: Iterable[str]) -> dict[str, str]:
    """Map blob SHA-1 -> SHA-256 of that blob's exact bytes.

    Uses one ``git cat-file --batch`` process. stdin is fed from a writer thread
    because feeding ~800 requests before reading any response would deadlock once the
    OS pipe buffer fills.
    """
    wanted = sorted(set(blobs))
    if not wanted:
        return {}

    proc = subprocess.Popen(
        ["git", "cat-file", "--batch"],
        cwd=str(repo_root),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    assert proc.stdin is not None and proc.stdout is not None

    def _feed() -> None:
        try:
            for sha in wanted:
                proc.stdin.write(f"{sha}\n".encode())  # type: ignore[union-attr]
            proc.stdin.close()  # type: ignore[union-attr]
        except BrokenPipeError:  # pragma: no cover - only on a crashed git
            pass

    writer = threading.Thread(target=_feed, daemon=True)
    writer.start()

    digests: dict[str, str] = {}
    for sha in wanted:
        header = proc.stdout.readline().decode().strip()
        parts = header.split()
        if len(parts) != 3 or parts[1] != "blob":
            proc.kill()
            writer.join(timeout=5)
            raise GitError(f"unexpected cat-file header for {sha}: {header!r}")
        size = int(parts[2])
        payload = proc.stdout.read(size)
        proc.stdout.read(1)  # trailing newline emitted by --batch
        digests[sha] = hashlib.sha256(payload).hexdigest()

    writer.join(timeout=5)
    proc.stdout.close()
    proc.wait(timeout=30)
    return digests


def is_hard_frozen(path: str) -> bool:
    return path in HARD_FROZEN_EXACT or path.startswith(HARD_FROZEN_PREFIXES)


def is_controlled_frozen(path: str) -> bool:
    return path in CONTROLLED_FROZEN_EXACT


def classify(path: str) -> str:
    """Return the owning surface for ``path``. First match wins."""
    if is_hard_frozen(path):
        return SURFACE_HARD_FROZEN
    if is_controlled_frozen(path):
        return SURFACE_CONTROLLED_FROZEN
    for name, surface in SURFACE_EXACT:
        if path == name:
            return surface
    for prefix, surface in SURFACE_PREFIXES:
        if path.startswith(prefix):
            return surface
    if "/" not in path:
        return SURFACE_REPO_ROOT
    return "other"


def collect(repo_root: Path, rev: str) -> tuple[str, list[Entry]]:
    """Return ``(commit_sha, entries)`` for the tracked tree at ``rev``."""
    commit = resolve_rev(repo_root, rev)
    tree = list_tree(repo_root, commit)
    # Only blobs go to `cat-file --batch`; asking it for a commit object would return a
    # `commit` header and blow up the blob reader.
    digests = blob_digests(
        repo_root, (sha for _mode, obj_type, sha, _path in tree if obj_type == "blob")
    )
    entries = [
        Entry(
            path=path,
            mode=mode,
            blob=sha,
            sha256=digests[sha] if obj_type == "blob" else gitlink_digest(sha),
            surface=classify(path),
        )
        for mode, obj_type, sha, path in tree
    ]
    entries.sort(key=lambda e: e.path)
    return commit, entries


def surface_digest(entries: Iterable[Entry]) -> str:
    """Digest over a surface's ``path\\0mode\\0sha256`` lines, path-sorted.

    Documented here because `--check` reproducibility depends on it: any change to
    this serialization changes every recorded digest and must be treated as a schema
    bump, not a silent fix.
    """
    payload = "\n".join(
        f"{e.path}\0{e.mode}\0{e.sha256}" for e in sorted(entries, key=lambda e: e.path)
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _frozen_block(
    entries: list[Entry],
    exact: tuple[str, ...],
    prefixes: tuple[str, ...],
    predicate: Any,
) -> dict[str, Any]:
    matched = [e for e in entries if predicate(e.path)]
    present = {e.path for e in matched}
    # Record patterns that matched nothing explicitly. An empty match set must be
    # visible in the artifact, not silently indistinguishable from a clean one.
    absent = [name for name in exact if name not in present]
    return {
        "patterns_exact": list(exact),
        "patterns_prefix": list(prefixes),
        "absent_exact_patterns": absent,
        "count": len(matched),
        "digest": surface_digest(matched),
        "files": [{"path": e.path, "mode": e.mode, "sha256": e.sha256} for e in matched],
    }


def build_inventory(commit: str, entries: list[Entry]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for e in entries:
        counts[e.surface] = counts.get(e.surface, 0) + 1
    return {
        "schema_version": INVENTORY_SCHEMA,
        "epic_id": EPIC_ID,
        "unit_id": UNIT_ID,
        "rev": commit,
        "content_basis": "git-blob",
        "hash_algorithm": "sha256",
        "gitlink_sha256_convention": (
            "a mode-160000 entry has no blob; its sha256 is sha256('gitlink:' + commit_sha1)"
        ),
        "file_count": len(entries),
        "surface_counts": dict(sorted(counts.items())),
        "files": [
            {"path": e.path, "mode": e.mode, "sha256": e.sha256, "surface": e.surface}
            for e in entries
        ],
    }


def build_identity(commit: str, entries: list[Entry]) -> dict[str, Any]:
    hard = _frozen_block(entries, HARD_FROZEN_EXACT, HARD_FROZEN_PREFIXES, is_hard_frozen)
    controlled = _frozen_block(entries, CONTROLLED_FROZEN_EXACT, (), is_controlled_frozen)
    identity = hashlib.sha256(
        f"{hard['digest']}\0{controlled['digest']}".encode()
    ).hexdigest()
    return {
        "schema_version": IDENTITY_SCHEMA,
        "epic_id": EPIC_ID,
        "unit_id": UNIT_ID,
        "rev": commit,
        "content_basis": "git-blob",
        "hash_algorithm": "sha256",
        "gitlink_sha256_convention": (
            "a mode-160000 entry has no blob; its sha256 is sha256('gitlink:' + commit_sha1)"
        ),
        "digest_serialization": "sha256 over path\\0mode\\0sha256 lines joined by \\n, path-sorted",
        "hard_frozen": hard,
        "controlled_frozen": controlled,
        "identity_digest": identity,
    }


def dump_json(path: Path, payload: dict[str, Any]) -> None:
    """Write ``payload`` deterministically: LF endings, stable key order, UTF-8."""
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=False) + "\n"
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def _compare_block(
    label: str, baseline: dict[str, Any], current: dict[str, Any]
) -> list[str]:
    """Return human-readable difference lines for one frozen surface.

    Keyed on ``(mode, sha256)``, not on content alone. ``mode`` is part of every
    Task-0 record (plan §4.2) and part of ``surface_digest``, and git itself reports a
    mode flip as a change — so comparing content alone would let an exec bit appear on
    a frozen hook script, or a regular file become a symlink, while the verdict still
    read ``TASK0_FREEZE_CLEAN``.
    """
    old = {f["path"]: (f["mode"], f["sha256"]) for f in baseline.get("files", [])}
    new = {f["path"]: (f["mode"], f["sha256"]) for f in current.get("files", [])}
    lines: list[str] = []
    for path in sorted(set(old) - set(new)):
        lines.append(f"  [{label}] REMOVED  {path}")
    for path in sorted(set(new) - set(old)):
        lines.append(f"  [{label}] ADDED    {path}")
    for path in sorted(set(old) & set(new)):
        old_mode, old_sha = old[path]
        new_mode, new_sha = new[path]
        if old_sha != new_sha:
            lines.append(
                f"  [{label}] MODIFIED {path}\n"
                f"           baseline sha256={old_sha}\n"
                f"           current  sha256={new_sha}"
            )
        if old_mode != new_mode:
            lines.append(
                f"  [{label}] MODE     {path}\n"
                f"           baseline mode={old_mode}\n"
                f"           current  mode={new_mode}"
            )
    return lines


def _emit(repo_root: Path, rev: str, out_dir: Path) -> int:
    commit, entries = collect(repo_root, rev)
    inv_path = repo_root / out_dir / INVENTORY_NAME
    idn_path = repo_root / out_dir / IDENTITY_NAME
    inventory = build_inventory(commit, entries)
    identity = build_identity(commit, entries)
    dump_json(inv_path, inventory)
    dump_json(idn_path, identity)
    print(f"rev              = {commit}")
    print(f"tracked files    = {inventory['file_count']}")
    print(f"hard-frozen      = {identity['hard_frozen']['count']} files")
    print(f"controlled       = {identity['controlled_frozen']['count']} files")
    print(f"identity digest  = {identity['identity_digest']}")
    print(f"wrote            = {out_dir / INVENTORY_NAME}")
    print(f"wrote            = {out_dir / IDENTITY_NAME}")
    print("TASK0_FREEZE_CLEAN")
    return 0


def _check(repo_root: Path, rev: str, out_dir: Path) -> int:
    idn_path = repo_root / out_dir / IDENTITY_NAME
    if not idn_path.is_file():
        print(f"baseline artifact absent: {out_dir / IDENTITY_NAME}", file=sys.stderr)
        print("nothing was verified - an absent baseline is not a pass", file=sys.stderr)
        print("ERROR_NO_BASELINE")
        return 2
    try:
        baseline = json.loads(idn_path.read_text(encoding="utf-8"))
        if baseline.get("schema_version") != IDENTITY_SCHEMA:
            raise ValueError(
                f"schema_version {baseline.get('schema_version')!r} != {IDENTITY_SCHEMA!r}"
            )
        for key in ("hard_frozen", "controlled_frozen", "identity_digest"):
            if key not in baseline:
                raise ValueError(f"missing key {key!r}")
    except (ValueError, OSError) as exc:
        print(f"baseline artifact unreadable: {exc}", file=sys.stderr)
        print("nothing was verified", file=sys.stderr)
        print("ERROR_MALFORMED_BASELINE")
        return 2

    commit, entries = collect(repo_root, rev)
    current = build_identity(commit, entries)

    hard_diff = _compare_block("hard", baseline["hard_frozen"], current["hard_frozen"])
    ctrl_diff = _compare_block(
        "controlled", baseline["controlled_frozen"], current["controlled_frozen"]
    )

    print(f"baseline rev     = {baseline.get('rev')}")
    print(f"current rev      = {commit}")
    print(f"baseline identity= {baseline['identity_digest']}")
    print(f"current identity = {current['identity_digest']}")
    print(
        f"hard-frozen      = {current['hard_frozen']['count']} files "
        f"(baseline {baseline['hard_frozen']['count']})"
    )
    print(
        f"controlled       = {current['controlled_frozen']['count']} files "
        f"(baseline {baseline['controlled_frozen']['count']})"
    )

    # Backstop. The per-file diff above is the diagnostic; the identity digest is the
    # authority. If they ever disagree — a digest change this comparison cannot name —
    # the safe reading is drift, not clean. Without this the script could print two
    # visibly different identity digests and still return TASK0_FREEZE_CLEAN.
    identity_mismatch = baseline["identity_digest"] != current["identity_digest"]
    if identity_mismatch and not (hard_diff or ctrl_diff):
        hard_diff = [
            "  [hard] IDENTITY digest differs with no per-file difference located",
            f"           baseline identity={baseline['identity_digest']}",
            f"           current  identity={current['identity_digest']}",
            "           the comparison could not name the change; treat as drift",
        ]

    if hard_diff:
        print("hard-frozen surface drifted:")
        for line in hard_diff:
            print(line)
        if ctrl_diff:
            print("controlled-frozen surface also changed:")
            for line in ctrl_diff:
                print(line)
        print("STOP_FROZEN_SURFACE_DRIFT")
        return 1

    if ctrl_diff:
        print("controlled-frozen surface changed:")
        for line in ctrl_diff:
            print(line)
        print(
            "plan §4.3 allows only the PR-C1 carrier-ownership hunk and the PR-D1a "
            "hooks/rules cooperative-scope hunk here; confirm the change is one of "
            "them before proceeding."
        )
        print("CONTROLLED_SURFACE_CHANGED")
        return 1

    print("TASK0_FREEZE_CLEAN")
    return 0


def main(argv: list[str] | None = None, repo_root: Path | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Emit or verify the Epic #499 Task-0 baseline "
            "(plan §4.2 records / §4.3 freeze enforcement)."
        )
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--emit", action="store_true", help="write the baseline artifacts")
    mode.add_argument(
        "--check",
        action="store_true",
        help="verify frozen surfaces against the committed baseline",
    )
    parser.add_argument("--rev", default="HEAD", help="git revision (default: HEAD)")
    parser.add_argument(
        "--out-dir",
        default=str(DEFAULT_OUT_DIR),
        help=f"artifact directory relative to the repo root (default: {DEFAULT_OUT_DIR})",
    )
    args = parser.parse_args(argv)

    root = (repo_root or Path(__file__).resolve().parent.parent.parent).resolve()
    out_dir = Path(args.out_dir)

    try:
        if args.emit:
            return _emit(root, args.rev, out_dir)
        return _check(root, args.rev, out_dir)
    except GitError as exc:
        print(f"git failure: {exc}", file=sys.stderr)
        print("nothing was verified", file=sys.stderr)
        print("ERROR_NOT_A_REPO")
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
