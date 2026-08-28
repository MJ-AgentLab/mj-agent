"""agents_sync.py — scoped projection generator, emitters A+B (dual-agent-compat v5).

Contract: plans/[PLAN]_dual-agent-compat.md §8 (generator terms) + D-011 (scoped, two
surfaces only — emitter A covers `.agents/skills/` [S1 #326]; emitter B covers
`.codex/config.toml` [S2 #330, 3-spike-gated, all PASS + Owner 进拍板 2026-07-14])
+ D-012 (artifacts committed, generator-owned, never hand-edited) + D-014 (skills
whitelist SoT = manifest `projection: project`) + D-013 (mcp per-server tiers SoT =
manifest `mcp` section; biz x5 + ssh-manager permanently `never`).
Drift gates: V10 skills surface warning-first; V11 mcp surface BLOCKING day-1 per
D-016 (sdd/gates.md §2; Owner execution record in #330).

Emitter B derivation (pure syntactic): `[mcp_servers.<name>]` entries for every
manifest mcp `projection_policy: project` server, definition taken from `.mcp.json`
(A14 hard-stop source, human-maintained, read-only here); the arg pair
`--context claude-code` is rewritten to `--context codex` (manifest serena transform);
source `env` values MUST be pure `${VAR}` references and become an `env_vars`
name-whitelist (spike 1: Codex sanitizes MCP child env; `env_vars` inherits by NAME —
no literal secret ever enters the artifact, fail-closed otherwise); posture keys are
transcribed from manifest `codex.posture` (D-017).

Modes (exactly one):
  sync            Regenerate `.agents/skills/<name>/SKILL.md` (raw-byte copy of the
                  whitelisted `.claude/skills/<name>/SKILL.md` sources), the directory
                  README (`.agents/README.md`, fixed template), `.codex/config.toml`
                  (emitter B), and `.agents.lock.json` (key -> `sha256:<body_sha256>`
                  over LF-normalized artifact text — byte-compatible with V9
                  `check_agents_projection.check_lock`; the mcp artifact uses the
                  reserved path-shaped key `.codex/config.toml`). Owned-only
                  reconcile on both trees (ADR-039 D-012 revised, Epic #499
                  PR-A1): deletion requires a verified lock owner + safe path +
                  absence from the desired set; unowned neighbors are preserved;
                  unknown/malformed lock or path hazard exits 2 with zero
                  deletes/writes. Idempotent.
  doctor          Read-only per-machine health report (S3a) -- Codex trust posture
                  (`~/.codex/config.toml` `[projects]`), HKCU MCP-secret env presence
                  (`setup-mcp-secrets.ps1 -Reload`, values masked), and the
                  on-disk-skills == manifest capability canary. Writes NOTHING
                  (D-015 red line: doctor never authors user-level Codex trust);
                  warning-only; NEVER runs in CI (env/machine-aware exception).
  --check         Read-only drift check (optionally scoped via --surface
                  skills|mcp|all, default all). All content comparisons are
                  LF-normalized (F10). Exit 1 on any drift, with the prescribed
                  action printed once.
  --adopt NAME    Explicit reverse-feed (D-012): copy the artifact bytes back over the
                  source SKILL.md (the source's own gates / Owner HITL apply to that
                  write), then run the sync routine so lock + README realign. There is
                  NO adopt path for `.codex/config.toml` (fully derived, no single
                  source file).

Generation (`sync` / `--check` / `--adopt`) is a pure syntactic transformation: zero
env parsing, zero network, zero secrets — safe on forks and clean clones (plan §8).
`doctor` is the deliberate machine-aware exception (reads trust/env; never in CI).
Exit codes: 0 clean/success; 1 drift; 2 usage error / manifest or source unreadable.
`main(argv=None, repo_root=None)` — repo_root injectable for tests (#217 pattern).
ASCII-only output (#318 lesson: Windows consoles may not be UTF-8).
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import platform
import shutil
import stat
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

_SCRIPT_NAME = "agents_sync.py"
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# CODEX_CONFIG_HEADER is a deliberate re-export: the emitter moved to the
# focused renderer module at Epic #499 PR-B; existing importers (tests) keep
# reading it from here.
from scripts.sdd._common.codex_config_renderer import (  # noqa: E402
    CODEX_CONFIG_HEADER as CODEX_CONFIG_HEADER,
)
from scripts.sdd._common.codex_config_renderer import (  # noqa: E402
    ConfigRenderError,
    render_codex_config,
)
from scripts.sdd._common.codex_readme_renderer import (  # noqa: E402
    ReadmeRenderError,
    render_skills_readme,
)
from scripts.sdd._common.codex_rule_renderer import (  # noqa: E402
    RuleRenderError,
    render_rules,
)
from scripts.sdd._common.enforcement_source import (  # noqa: E402
    ENFORCEMENT_SOURCE_RELPATH,
    EnforcementSourceError,
    load_enforcement_source,
    policy_ref_inventory,
)
from scripts.sdd._common.frontmatter import body_sha256  # noqa: E402
from scripts.sdd._common.projection_loader import (  # noqa: E402  # noqa: E402
    CODEX_CONFIG_RELPATH,
    CODEX_HOOKS_KEY,
    CODEX_LOCK_KEY,
    CODEX_RULES_PREFIX,
    LOCK_RELPATH,
    LockVerificationError,
    VerifiedLock,
    canonicalize,
    classify_lock,
    codex_posture_slice,
    load_verified_lock,
    lock_v2_canonical_text,
    manifest_capability_slice,
    manifest_mcp_slice,
    module_source_sha256,
    sha256_of_bytes,
    sha256_of_canonical,
    verify_lock,
    verify_lock_v2,
)
from scripts.sdd._common.skill_renderer import (  # noqa: E402
    PREFACE_RELPATH,
    TRANSLATION_MAP_RELPATH,
    WORKFLOW_REGISTRY_RELPATH,
    TranslationError,
    expand_wildcard,
    load_translation_map,
    load_workflow_registry,
    render_translated,
)
from scripts.sdd.check_agents_projection import (  # noqa: E402
    FatalCheckError,
    load_manifest_raw,
    load_mcp_projection,
    load_project_set,
)

SOURCE_DIR = Path(".claude/skills")
AGENTS_DIR = Path(".agents")
SKILLS_DIR = AGENTS_DIR / "skills"
CODEX_DIR = Path(".codex")
MCP_JSON_RELPATH = Path(".mcp.json")

# Emitter B rendering rules moved VERBATIM to
# scripts/sdd/_common/codex_config_renderer.py at Epic #499 PR-B (the config
# output class gets its own focused renderer module/version, plan §2.6; the
# module is the `codex_config_renderer` pre-registered in the A14 row (b)
# D-017 enumeration). CODEX_CONFIG_HEADER is re-exported above for existing
# importers; `_render_codex_config` below adapts ConfigRenderError to this
# script's FatalCheckError so call sites and exit-2 messages stay identical.

README_TEMPLATE = """\
# GENERATED — do not edit anything under `.agents/`

Every file in this tree plus the repo-root `.agents.lock.json` and the generated
`.codex/config.toml` (emitter B, S2 #330) is a **generated artifact** owned 100%
by `scripts/sdd/agents_sync.py` (dual-agent-compat v5, ADR-036
D-011/D-012/D-013/D-014). `.agents/skills/<name>/SKILL.md` is a byte-identical
projection of `.claude/skills/<name>/SKILL.md` for every manifest capability with
`projection: project` (`sdd/development-agent.yml` is the whitelist SoT). Codex
discovers these skills natively under `.agents/skills`; projected copies do NOT
count toward the 37-skill SoT.

How to change a projected skill:

1. Edit the SOURCE: `.claude/skills/<name>/SKILL.md` (its own gates apply).
2. Run `python scripts/sdd/agents_sync.py sync`.
3. Commit source + artifacts + `.agents.lock.json` together.

Never hand-edit these files — CI runs `agents_sync.py --check` (drift gate V10)
and `check_agents_projection.py` (V9) against them. To reverse-feed an artifact
edit into the source use `python scripts/sdd/agents_sync.py --adopt <name>`
(Owner HITL applies). On merge conflicts in generated files: merge the source,
re-run `sync` to overwrite the artifacts — do not 3-way-merge artifacts.

Semantic difference declaration: the Claude Code harness `ask`-gates, protected-path
prompts and PreToolUse hooks referenced inside projected skill bodies are NOT present
under Codex. Under Codex those stop points are AGENTS.md self-enforced duties
(see the repo-root `AGENTS.md`, sections "Self-enforced boundaries" and
"Generated projections").
"""

PRESCRIBED_ACTION = (
    "Prescribed action (D-012): edit the SOURCE (.claude/skills/<name>/SKILL.md),"
    " then run `python scripts/sdd/agents_sync.py sync` and commit source + artifacts"
    " + .agents.lock.json together. Never hand-edit .agents/** or .agents.lock.json."
    " To reverse-feed an artifact edit into the source, run"
    " `python scripts/sdd/agents_sync.py --adopt <name>` (Owner HITL applies)."
    " On merge conflicts in generated files: merge the source, re-run `sync` to"
    " overwrite the artifacts - do not 3-way-merge artifacts."
)

PRESCRIBED_ACTION_MCP = (
    "For .codex/config.toml (emitter B): the SOURCES are .mcp.json (A14 hard-stop"
    " surface, human-maintained) and the manifest `mcp` / `codex.posture` sections"
    " (protected-adjacent, D-017 Owner approval). Change the source through its own"
    " gate, then run `python scripts/sdd/agents_sync.py sync` and commit"
    " .codex/config.toml + .agents.lock.json together. Never hand-edit it; there is"
    " no --adopt path (fully derived)."
)

PRESCRIBED_ACTION_ENFORCEMENT = (
    "For .codex/hooks.json + .codex/rules/*.rules (Epic #499 PR-D1a): the SOURCE is"
    " sdd/adapters/codex-enforcement.yml (protected-adjacent typed source, D-017"
    " Owner approval) plus the files it declares in `policy_refs`. Change the source"
    " through its own gate, then run `python scripts/sdd/agents_sync.py sync` and"
    " commit source + artifacts + .agents.lock.json together. Never hand-edit them;"
    " there is no --adopt path (enforcement outputs are not adoptable, D-012 revised)."
)

# V13 (Codex Enforcement Drift) result codes. Emitted ONLY for
# `--check --surface enforcement` so the V10 (skills) and V11 (mcp) BLOCKING
# steps keep byte-identical stdout. Registered streak semantics (plan §5.9):
# SKIP_* is neutral; EXECUTED_WITH_FINDINGS resets the epoch.
# NOTE both EXECUTED_CLEAN and the SKIP_* codes exit 0 — the run/step conclusion
# is therefore NOT a usable predicate; PR-D1b must read THIS stdout token.
RESULT_EXECUTED_CLEAN = "EXECUTED_CLEAN"
RESULT_EXECUTED_WITH_FINDINGS = "EXECUTED_WITH_FINDINGS"
RESULT_ERROR_UNREADABLE = "ERROR_UNREADABLE"
RESULT_SKIP_MANIFEST_V1 = "SKIP_MANIFEST_V1"
RESULT_SKIP_NO_ENFORCEMENT_SOURCE = "SKIP_NO_ENFORCEMENT_SOURCE"


def _lf(text: str) -> str:
    return text.replace("\r\n", "\n")


def _read_lf(path: Path) -> str:
    return _lf(path.read_text(encoding="utf-8"))


def _lock_hash(artifact_text: str) -> str:
    """LF-normalized body hash, byte-compatible with V9 `_normalized_body_hash`."""
    return "sha256:" + body_sha256(_lf(artifact_text))


def _expected_lock(
    repo_root: Path, project: set[str], *, include_codex: bool
) -> dict[str, str]:
    lock: dict[str, str] = {}
    for name in sorted(project):
        artifact = repo_root / SKILLS_DIR / name / "SKILL.md"
        if artifact.is_file():
            lock[name] = _lock_hash(artifact.read_text(encoding="utf-8"))
    config = repo_root / CODEX_CONFIG_RELPATH
    if include_codex and config.is_file():
        # Reserved path-shaped key (Owner 拍板 2026-07-14); TOML has no frontmatter,
        # so body_sha256 degenerates to a whole-text hash — same recipe as V9 PJ043.
        # `include_codex` is False when the manifest mcp project tier is empty:
        # the lock is the OWNER LEDGER (PR-A1), and claiming a config the
        # generator did not render would fabricate ownership over an unowned
        # stale file — which a later sync would then wrongly "own" and delete.
        lock[CODEX_LOCK_KEY] = _lock_hash(config.read_text(encoding="utf-8"))
    return lock


def _load_mcp_json(repo_root: Path) -> dict[str, Any]:
    """Read `.mcp.json` server definitions (source side; strictly read-only here)."""
    path = repo_root / MCP_JSON_RELPATH
    if not path.is_file():
        raise FatalCheckError(".mcp.json not found (emitter B source)")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FatalCheckError(f".mcp.json unreadable: {exc}") from exc
    servers = data.get("mcpServers")
    if not isinstance(servers, dict):
        raise FatalCheckError(".mcp.json must contain an 'mcpServers' mapping")
    return servers


def _render_codex_config(
    mcp_project: dict[str, dict[str, Any]],
    posture: dict[str, Any] | None,
    mcp_json_servers: dict[str, Any],
) -> str:
    """Emitter B via the extracted focused renderer module (Epic #499 PR-B) —
    ConfigRenderError becomes this script's FatalCheckError so every call site
    and exit-2 message stays identical to the pre-extraction emitter."""
    try:
        return render_codex_config(mcp_project, posture, mcp_json_servers)
    except ConfigRenderError as exc:
        raise FatalCheckError(str(exc)) from exc


def _lock_text(lock: dict[str, str]) -> str:
    return json.dumps(lock, indent=2, sort_keys=True) + "\n"


def _source_path(repo_root: Path, name: str) -> Path:
    return repo_root / SOURCE_DIR / name / "SKILL.md"


def _require_sources(repo_root: Path, project: set[str]) -> None:
    missing = [n for n in sorted(project) if not _source_path(repo_root, n).is_file()]
    if missing:
        raise FatalCheckError(
            "projection source missing for: " + ", ".join(missing)
            + " (manifest `projection: project` entries need on-disk SKILL.md)"
        )


def _expected_files(project: set[str]) -> set[Path]:
    """Relative paths (under repo root) that may exist inside `.agents/`."""
    expected = {AGENTS_DIR / "README.md"}
    for name in project:
        expected.add(SKILLS_DIR / name / "SKILL.md")
    return expected


def _is_reparse(path: Path) -> bool:
    """Symlink on any OS, or a Windows reparse point (junction etc.)."""
    try:
        st = os.lstat(path)
    except OSError:
        return False
    if stat.S_ISLNK(st.st_mode):
        return True
    attrs = getattr(st, "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(attrs & reparse_flag)


def _reparse_ancestor(repo_root: Path, rel: Path) -> Path | None:
    """First symlink/reparse directory component between repo_root and rel.

    `_is_reparse` (lstat-based) runs BEFORE the exists() gate: a DANGLING
    symlink/junction reports exists()==False (exists follows links), so the
    old exists-first order let it bypass the hazard check entirely (Stage 11
    finding F3 — an owned delete could land before the hazard fired)."""
    cur = repo_root
    for part in rel.parts[:-1]:
        cur = cur / part
        if _is_reparse(cur):
            return cur
        if not cur.exists():
            return None
    return None


def _casefold_squatter(parent: Path, name: str) -> str | None:
    """Direntry of `parent` that casefolds to `name` without being exactly it,
    when the exact entry is absent. On a case-insensitive filesystem the exact
    path then RESOLVES to that differently-cased neighbor, so a managed write
    would clobber it and a managed delete would delete it — a path hazard."""
    if not parent.is_dir():
        return None
    entries = {e.name for e in parent.iterdir()}
    if name in entries:
        return None  # exact entry exists; a case-variant is a distinct neighbor
    for entry in entries:
        if entry.casefold() == name.casefold():
            return entry
    return None


def _casefold_component_squatter(repo_root: Path, rel: Path) -> tuple[str, str] | None:
    """First (squatter_name, expected_component) along rel where the exact
    entry is absent but a casefold variant exists — checked for EVERY
    component, not just the leaf (Stage 11 finding F6: an unowned case-variant
    DIRECTORY absorbs managed writes on a case-insensitive filesystem and gets
    laundered into the owner ledger). Fails closed on every platform so the
    behavior does not diverge between case-sensitive and -insensitive trees."""
    cur = repo_root
    for part in rel.parts:
        squatter = _casefold_squatter(cur, part)
        if squatter is not None:
            return squatter, part
        cur = cur / part
        if not cur.exists():
            return None  # nothing on disk from here down — no squat possible
    return None


def _preflight_owned_reconcile(
    repo_root: Path, verified: VerifiedLock | None, desired: set[Path]
) -> list[Path]:
    """Owned-only reconcile preflight (ADR-039 D-012 revised; plan §5.5, PR-A1).

    Returns the verified deletion list (relative paths, sorted). Deletion
    requires ALL of: a verified lock owner (entry present AND on-disk bytes
    still matching the lock hash), a safe path (regular file, no symlink or
    reparse ancestor, no casefold squat), and absence from the desired set.
    Every hazard raises FatalCheckError BEFORE the first delete/write —
    unowned neighbors are never touched (AC-05); unknown/malformed lock and
    unsafe paths fail closed with zero deletes/writes (AC-06).
    """
    deletions: list[Path] = []
    if verified is not None:
        for key in sorted(verified.owned_paths):
            rel = Path(verified.owned_paths[key])
            if rel in desired:
                continue  # still a managed write target, not a deletion
            target = repo_root / rel
            ancestor = _reparse_ancestor(repo_root, rel)
            if ancestor is not None:
                raise FatalCheckError(
                    f"symlink/reparse ancestor '{ancestor}' above lock-owned"
                    f" '{rel.as_posix()}' (path hazard; zero delete/write)"
                )
            squat = _casefold_component_squatter(repo_root, rel)
            if squat is not None:
                raise FatalCheckError(
                    f"'{squat[0]}' casefold-collides with component '{squat[1]}' of"
                    f" lock-owned '{rel.as_posix()}' (owner ambiguity; zero"
                    " delete/write)"
                )
            # is_symlink (lstat) runs OUTSIDE the exists() gate: a dangling
            # symlink reports exists()==False but is still an on-disk entry
            # we must not treat as ours (Stage 11 findings F3/F5).
            if target.is_symlink() or (target.exists() and not target.is_file()):
                raise FatalCheckError(
                    f"lock-owned '{rel.as_posix()}' is not a regular file"
                    " (path hazard; zero delete/write)"
                )
            if not target.exists():
                continue  # already gone — nothing to delete
            try:
                on_disk = _lock_hash(target.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError) as exc:
                raise FatalCheckError(
                    f"lock-owned '{rel.as_posix()}' unreadable: {exc}"
                    " (ownership unverifiable; zero delete/write)"
                ) from exc
            if on_disk != verified.entries[key]:
                raise FatalCheckError(
                    f"lock-owned '{rel.as_posix()}' does not match its lock hash"
                    " (owner ambiguity — possible hand edit; zero delete/write)"
                )
            deletions.append(rel)
    for rel in sorted(desired, key=lambda p: p.as_posix()):
        ancestor = _reparse_ancestor(repo_root, rel)
        if ancestor is not None:
            raise FatalCheckError(
                f"symlink/reparse ancestor '{ancestor}' above managed target"
                f" '{rel.as_posix()}' (path hazard; zero write)"
            )
        cur = repo_root
        for part in rel.parts[:-1]:
            cur = cur / part
            if cur.exists() and not cur.is_dir():
                raise FatalCheckError(
                    f"managed target '{rel.as_posix()}' is blocked by"
                    f" non-directory '{cur.relative_to(repo_root).as_posix()}'"
                    " (path hazard; zero write — remove it manually; owned-only"
                    " sync will not delete what it does not own)"
                )
        target = repo_root / rel
        # is_symlink (lstat) outside the exists() gate — a dangling symlink at
        # a managed target would otherwise pass every guard and write THROUGH
        # the link outside the managed tree (Stage 11 finding F5).
        if target.is_symlink() or (target.exists() and not target.is_file()):
            raise FatalCheckError(
                f"managed target '{rel.as_posix()}' is squatted by a non-regular"
                " file (path hazard; zero write — remove it manually)"
            )
        squat = _casefold_component_squatter(repo_root, rel)
        if squat is not None:
            raise FatalCheckError(
                f"'{squat[0]}' casefold-collides with component '{squat[1]}' of"
                f" managed target '{rel.as_posix()}' (path hazard; zero write —"
                " remove or rename it manually)"
            )
    return sorted(deletions, key=lambda p: p.as_posix())


def _prune_empty_dirs(repo_root: Path, start: Path, changes: list[str]) -> None:
    """Remove now-empty directories left behind by an owned deletion — never
    crossing a non-empty directory (unowned neighbors keep their parents
    alive) and never removing the fixed tree roots."""
    keep = {repo_root, repo_root / AGENTS_DIR, repo_root / SKILLS_DIR}
    cur = start
    while cur not in keep and repo_root in cur.parents:
        try:
            cur.rmdir()
        except OSError:
            return  # not empty — an unowned neighbor lives here
        changes.append(f"remove {cur.relative_to(repo_root).as_posix()}/")
        cur = cur.parent


def do_sync(repo_root: Path, project: set[str]) -> list[str]:
    """Regenerate artifacts + README + config.toml + lock; owned-only reconcile.

    Every fail-able derivation (source presence, mcp load, emitter B render,
    lock verification, deletion/write path safety) runs BEFORE the first
    delete/write, so a FatalCheckError can never leave a half-updated tree
    with a stale lock (review finding #330-3) — and the generator never
    deletes content it cannot prove it owns (ADR-039 D-012 revised; Epic #499
    PR-A1, AC-05/AC-06). Returns change log.
    """
    manifest = load_manifest_raw(repo_root)
    lock_class, lock_raw = _lock_state_tolerant(repo_root)
    if _manifest_version(manifest) == 2:
        if lock_class == "malformed":
            raise FatalCheckError(
                "lock is malformed/mixed under manifest v2 (zero delete/write)"
            )
        return _do_sync_v2(repo_root, manifest, lock_class, lock_raw)
    if lock_class == "v2":
        # Rollback row of the §2.6 matrix: v1 manifest + verified v2 lock —
        # converge the v1 desired set using the v2 entries as a READ-ONLY
        # owner ledger, then write back a v1 lock.
        return _do_sync_v1_rollback(repo_root, project, lock_raw)

    _require_sources(repo_root, project)
    mcp_project, posture, _never = load_mcp_projection(repo_root)
    rendered: str | None = None
    if mcp_project:
        rendered = _render_codex_config(mcp_project, posture, _load_mcp_json(repo_root))

    # Owned-only reconcile preflight: the OLD on-disk lock is the owner ledger.
    try:
        verified = load_verified_lock(repo_root)
    except LockVerificationError as exc:
        raise FatalCheckError(str(exc)) from exc
    desired = _expected_files(project)
    if rendered is not None:
        desired.add(CODEX_CONFIG_RELPATH)
    # The lock itself is a managed write target — it gets the same hazard
    # battery (dir squat / symlink / casefold), or its final write_text would
    # be the one mutation that can fail AFTER others landed (Stage 11
    # finding F2; do_sync's zero-write-on-hazard promise must include it).
    desired.add(LOCK_RELPATH)
    deletions = _preflight_owned_reconcile(repo_root, verified, desired)

    changes: list[str] = []
    for rel in deletions:
        path = repo_root / rel
        path.unlink()
        changes.append(f"remove {rel.as_posix()}")
        _prune_empty_dirs(repo_root, path.parent, changes)

    for name in sorted(project):
        src = _source_path(repo_root, name)
        dst = repo_root / SKILLS_DIR / name / "SKILL.md"
        data = src.read_bytes()
        if not dst.is_file() or dst.read_bytes() != data:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(data)
            changes.append(f"write {SKILLS_DIR.as_posix()}/{name}/SKILL.md")

    readme = repo_root / AGENTS_DIR / "README.md"
    if not readme.is_file() or _read_lf(readme) != README_TEMPLATE:
        readme.parent.mkdir(parents=True, exist_ok=True)
        readme.write_text(README_TEMPLATE, encoding="utf-8", newline="\n")
        changes.append(f"write {AGENTS_DIR.as_posix()}/README.md")

    # Emitter B: .codex/config.toml (S2 #330; rendered up top, before any
    # write). Unowned neighbors under .codex/ (future hooks/rules, user files)
    # are preserved; an empty mcp project tier deletes only the lock-owned
    # config — already handled by the owned deletion pass above.
    if rendered is not None:
        config_path = repo_root / CODEX_CONFIG_RELPATH
        if not config_path.is_file() or _read_lf(config_path) != rendered:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(rendered, encoding="utf-8", newline="\n")
            changes.append(f"write {CODEX_CONFIG_RELPATH.as_posix()}")

    lock_path = repo_root / LOCK_RELPATH
    lock_text = _lock_text(
        _expected_lock(repo_root, project, include_codex=rendered is not None)
    )
    if not lock_path.is_file() or _read_lf(lock_path) != lock_text:
        lock_path.write_text(lock_text, encoding="utf-8", newline="\n")
        changes.append(f"write {LOCK_RELPATH.as_posix()}")

    return changes


def do_check(repo_root: Path, project: set[str], surface: str = "all") -> list[str]:
    """Read-only drift check (LF-normalized). Returns drift messages.

    `surface` scopes the check: "skills" (V10 warning gate), "mcp" (V11 blocking
    gate), or "all" (local one-shot). The shared lock file is checked per-key under
    a scoped surface so mcp drift never reddens the skills step and vice versa.
    """
    manifest = load_manifest_raw(repo_root)
    lock_class, _lock_raw = _lock_state_tolerant(repo_root)
    version = _manifest_version(manifest)
    if version == 2:
        if lock_class in ("v2", None):
            return _do_check_v2(repo_root, manifest, surface)
        if lock_class == "v1":
            return [
                "lock schema v1 does not match manifest v2 (§2.6 matrix"
                " mismatch — cutover pending; run sync)"
            ]
        return ["lock is malformed/mixed under manifest v2 (regenerate via sync)"]
    if lock_class == "v2":
        return [
            "lock schema v2 does not match manifest v1 (§2.6 matrix mismatch —"
            " rollback pending; run sync)"
        ]

    drift: list[str] = []
    check_skills = surface in ("skills", "all")
    check_mcp = surface in ("mcp", "all")

    if check_skills:
        _require_sources(repo_root, project)
        for name in sorted(project):
            artifact = repo_root / SKILLS_DIR / name / "SKILL.md"
            if not artifact.is_file():
                drift.append(f"missing artifact: {SKILLS_DIR.as_posix()}/{name}/SKILL.md")
                continue
            if _read_lf(artifact) != _read_lf(_source_path(repo_root, name)):
                drift.append(
                    f"artifact != source for '{name}' (hand-edited artifact OR source"
                    " edited without re-running sync)"
                )

        readme = repo_root / AGENTS_DIR / "README.md"
        if not readme.is_file():
            drift.append(f"missing {AGENTS_DIR.as_posix()}/README.md")
        elif _read_lf(readme) != README_TEMPLATE:
            drift.append(f"{AGENTS_DIR.as_posix()}/README.md differs from the fixed template")

        expected = _expected_files(project)
        expected_dirs = {p.parent for p in expected} | {AGENTS_DIR, SKILLS_DIR}
        agents_root = repo_root / AGENTS_DIR
        if agents_root.is_dir():
            for path in sorted(agents_root.rglob("*")):
                rel = path.relative_to(repo_root)
                if path.is_file() and rel not in expected:
                    drift.append(
                        f"unexpected file: {rel.as_posix()} (unowned neighbor —"
                        " owned-only sync will NOT delete it; remove manually)"
                    )
                elif path.is_dir() and rel not in expected_dirs:
                    drift.append(
                        f"unexpected directory: {rel.as_posix()}/ (unowned neighbor —"
                        " owned-only sync will NOT delete it; remove manually)"
                    )

    mcp_project, posture, _never = load_mcp_projection(repo_root)
    config_path = repo_root / CODEX_CONFIG_RELPATH
    if check_mcp:
        # Unowned neighbors under .codex/ (future hooks/rules, user files) are
        # NOT drift (owned-only reconcile, ADR-039 D-012 revised; Epic #499
        # PR-A1) — V9 PJ045 reports them info-only for visibility.
        if mcp_project:
            rendered = _render_codex_config(
                mcp_project, posture, _load_mcp_json(repo_root)
            )
            if not config_path.is_file():
                drift.append(f"missing {CODEX_CONFIG_RELPATH.as_posix()} (run sync)")
            elif _read_lf(config_path) != rendered:
                drift.append(
                    f"{CODEX_CONFIG_RELPATH.as_posix()} != rendered from .mcp.json +"
                    " manifest (hand-edited artifact OR source changed without"
                    " re-running sync)"
                )
        elif config_path.is_file():
            drift.append(
                f"stale {CODEX_CONFIG_RELPATH.as_posix()} (manifest mcp project tier"
                " is empty; owned-only reconcile deletes it only with a verified"
                " lock owner — run sync, or remove it manually if unowned;"
                " other .codex/ neighbors are always preserved)"
            )

    lock_path = repo_root / LOCK_RELPATH
    if not lock_path.is_file():
        drift.append(f"missing {LOCK_RELPATH.as_posix()}")
    elif surface == "all":
        if _read_lf(lock_path) != _lock_text(
            _expected_lock(repo_root, project, include_codex=bool(mcp_project))
        ):
            drift.append(
                f"{LOCK_RELPATH.as_posix()} out of date (lock is regenerated by sync,"
                " one sorted entry per line)"
            )
    else:
        try:
            from scripts.sdd._common.projection_loader import parse_lock_json

            parsed = parse_lock_json(lock_path.read_text(encoding="utf-8"))
            lock: dict[str, Any] = parsed if isinstance(parsed, dict) else {}
            if not isinstance(parsed, dict):
                drift.append(
                    f"{LOCK_RELPATH.as_posix()} unreadable (regenerate via sync)"
                )
        except (OSError, LockVerificationError):
            # Duplicate keys / invalid JSON: the same malformed ledger sync
            # refuses with exit 2 must also redden the scoped gates
            # (Stage 11 #10/#29).
            drift.append(f"{LOCK_RELPATH.as_posix()} unreadable (regenerate via sync)")
            lock = {}
        if surface == "skills":
            for name in sorted(project):
                artifact = repo_root / SKILLS_DIR / name / "SKILL.md"
                if not artifact.is_file():
                    continue  # missing artifact already reported above
                if lock.get(name) != _lock_hash(artifact.read_text(encoding="utf-8")):
                    drift.append(f"lock entry out of date for '{name}'")
            # Orphan keys (neither a whitelisted skill nor the reserved mcp key)
            # belong to the skills surface so they cannot escape both scoped gates
            # (review finding #330-4; V9 PJ034 + the all-surface check back this up).
            for name in sorted(set(lock) - project - {CODEX_LOCK_KEY}):
                drift.append(f"unknown lock entry '{name}' (regenerate via sync)")
        else:  # mcp
            # include_codex semantics (PR-A1): the reserved key is expected
            # ONLY when the mcp project tier is non-empty — with an empty tier
            # the lock correctly omits it (claiming an unowned stale config
            # would fabricate ownership), so demanding it here would emit a
            # false, sync-unfixable diagnosis (Stage 11 finding F4).
            if config_path.is_file() and mcp_project:
                expected_hash = _lock_hash(config_path.read_text(encoding="utf-8"))
                if lock.get(CODEX_LOCK_KEY) != expected_hash:
                    drift.append(
                        f"lock reserved key '{CODEX_LOCK_KEY}' missing or out of date"
                    )
            elif CODEX_LOCK_KEY in lock:
                reason = (
                    f"{CODEX_CONFIG_RELPATH.as_posix()} absent"
                    if not config_path.is_file()
                    else "manifest mcp project tier is empty"
                )
                drift.append(
                    f"stale lock reserved key '{CODEX_LOCK_KEY}' ({reason})"
                )

    return drift


def do_adopt(repo_root: Path, project: set[str], name: str) -> list[str]:
    """byte-copy recovery/import escape hatch (plan §2.1 invariant 7 / §2.7):
    a legacy v1 lock's body-only digest cannot prove the frontmatter unchanged,
    so adopt is ADOPT_REQUIRES_LOCK_V2 / exit 2 / zero source-artifact-lock
    writes until the tree carries a verified v2 lock; under a verified v2 lock
    the full CAS table applies. The pre-PR-B unconditional copy-back is gone
    BY CONTRACT (dormant v2 engine; the real tree keeps its v1 lock, so adopt
    is disabled there until the PR-C1 cutover)."""
    manifest = load_manifest_raw(repo_root)
    lock_class, lock_raw = _lock_state_tolerant(repo_root)
    if lock_class == "malformed":
        raise FatalCheckError(
            "lock is malformed/mixed — adopt proves nothing (zero writes)"
        )
    return _do_adopt_v2(repo_root, manifest, lock_class, lock_raw, name)


# --------------------------------------------------------------------------- v2 engine
# Dormant until the PR-C1 cutover (Epic #499 plan §2.6 compatibility matrix).
# The real tree is manifest v1 + legacy v1 lock and takes the UNTOUCHED legacy
# paths above. The v2 engine activates only on fixture/cutover trees:
#   v2 manifest + v2/absent lock  -> full v2 deterministic converge
#   v2 manifest + verified v1 lock -> cutover (v1 keys as read-only ledger)
#   v1 manifest + verified v2 lock -> rollback (v2 entries as read-only ledger,
#                                     converge v1 desired set, write v1 lock)
#   anything malformed/mixed       -> exit 2, zero writes/deletes


def _manifest_version(manifest: dict[str, Any]) -> int:
    version = manifest.get("schema_version")
    return int(version) if isinstance(version, int) else 1


def _print_enforcement_error_code(args: Any) -> None:
    """Emit V13's error result_code on the exit-2 path.

    Without this the enforcement surface has a THIRD outcome its own contract
    does not cover: a typed source that fails to load exits 2 with no token at
    all, and because the CI step is `continue-on-error: true` the exit code is
    swallowed — so PR-D1b's stdout anchor would see neither a clean, a findings,
    nor a skip token, and the epoch would silently fail to reset. It has to be
    fixed here: PR-D1b is specified as anchor-only with zero behavior diff.
    """
    if getattr(args, "check", False) and getattr(args, "surface", None) == "enforcement":
        print(RESULT_ERROR_UNREADABLE)


def _enforcement_result_code(repo_root: Path) -> str:
    """V13's clean-run result code (plan §5.9 streak semantics).

    Distinguishes "ran and found nothing" from "had nothing to run", because
    both exit 0 and the registered streak treats them differently: a SKIP is
    epoch-NEUTRAL while an EXECUTED_CLEAN counts toward the eligibility streak.
    PR-D1b registers this stdout token, never the step conclusion.
    """
    try:
        manifest = load_manifest_raw(repo_root)
    except FatalCheckError:
        return RESULT_SKIP_MANIFEST_V1
    if _manifest_version(manifest) != 2:
        return RESULT_SKIP_MANIFEST_V1
    if not (repo_root / ENFORCEMENT_SOURCE_RELPATH).is_file():
        return RESULT_SKIP_NO_ENFORCEMENT_SOURCE
    return RESULT_EXECUTED_CLEAN


def _lock_state(repo_root: Path) -> tuple[str | None, dict[str, Any] | None]:
    """(lock class 'v1'/'v2'/None, raw lock). Malformed/mixed -> FatalCheckError."""
    raw = load_verified_lock_raw(repo_root)
    if raw is None:
        return None, None
    try:
        return classify_lock(raw), raw
    except LockVerificationError as exc:
        raise FatalCheckError(str(exc)) from exc


def _lock_state_tolerant(repo_root: Path) -> tuple[str | None, dict[str, Any] | None]:
    """Like _lock_state but maps any malformed/mixed/unreadable ledger to
    ('malformed', None) so the LEGACY v1 paths keep their exact pre-PR-B
    behavior (they re-verify and produce the identical diagnosis); the v2
    paths treat 'malformed' as fail-closed."""
    try:
        return _lock_state(repo_root)
    except FatalCheckError:
        return "malformed", None


def _do_sync_v1_rollback(
    repo_root: Path, project: set[str], lock_raw: dict[str, Any] | None
) -> list[str]:
    """§2.6 matrix rollback row: converge the v1 desired set while treating
    the verified v2 entries as a READ-ONLY owner ledger, then write back a v1
    lock. Golden scenario: the old-owned translated outputs are deleted, the
    byte-copy artifacts and every unowned neighbor survive."""
    _require_sources(repo_root, project)
    mcp_project, posture, _never = load_mcp_projection(repo_root)
    rendered: str | None = None
    if mcp_project:
        rendered = _render_codex_config(mcp_project, posture, _load_mcp_json(repo_root))
    desired = _expected_files(project)
    if rendered is not None:
        desired.add(CODEX_CONFIG_RELPATH)
    desired.add(LOCK_RELPATH)
    owned = _owned_paths_any("v2", lock_raw)
    deletions = _preflight_owned_reconcile_any(repo_root, owned, desired)

    changes: list[str] = []
    for rel in deletions:
        path = repo_root / rel
        path.unlink()
        changes.append(f"remove {rel.as_posix()}")
        _prune_empty_dirs(repo_root, path.parent, changes)

    for name in sorted(project):
        src = _source_path(repo_root, name)
        dst = repo_root / SKILLS_DIR / name / "SKILL.md"
        data = src.read_bytes()
        if not dst.is_file() or dst.read_bytes() != data:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(data)
            changes.append(f"write {SKILLS_DIR.as_posix()}/{name}/SKILL.md")

    readme = repo_root / AGENTS_DIR / "README.md"
    if not readme.is_file() or _read_lf(readme) != README_TEMPLATE:
        readme.parent.mkdir(parents=True, exist_ok=True)
        readme.write_text(README_TEMPLATE, encoding="utf-8", newline="\n")
        changes.append(f"write {AGENTS_DIR.as_posix()}/README.md")

    if rendered is not None:
        config_path = repo_root / CODEX_CONFIG_RELPATH
        if not config_path.is_file() or _read_lf(config_path) != rendered:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(rendered, encoding="utf-8", newline="\n")
            changes.append(f"write {CODEX_CONFIG_RELPATH.as_posix()}")

    lock_path = repo_root / LOCK_RELPATH
    lock_text = _lock_text(
        _expected_lock(repo_root, project, include_codex=rendered is not None)
    )
    if not lock_path.is_file() or _read_lf(lock_path) != lock_text:
        lock_path.write_text(lock_text, encoding="utf-8", newline="\n")
        changes.append(f"write {LOCK_RELPATH.as_posix()}")
    return changes


def load_verified_lock_raw(repo_root: Path) -> dict[str, Any] | None:
    from scripts.sdd._common.projection_loader import read_lock

    try:
        return read_lock(repo_root)
    except LockVerificationError as exc:
        raise FatalCheckError(str(exc)) from exc


def _owned_paths_any(
    lock_class: str | None,
    raw: dict[str, Any] | None,
    v1_allowed_keys: set[str] | None = None,
) -> dict[str, tuple[Path, str, str]]:
    """Owner ledger view for either lock schema: key -> (relpath, kind, expect)
    where kind selects the on-disk ownership re-verification recipe.

    `v1_allowed_keys` implements the §2.6 "verified old lock" mappability
    requirement (Stage 11 #16): a legacy v1 key used as a deletion ledger must
    be rebuildable from the manifest — a shape-valid key naming no manifest
    capability proves nothing and fails the WHOLE ledger (ownership
    laundering guard, same class as the A1 findings)."""
    if lock_class is None or raw is None:
        return {}
    if lock_class == "v1":
        verified = verify_lock(raw)
        if v1_allowed_keys is not None:
            unknown = set(verified.entries) - v1_allowed_keys - {CODEX_LOCK_KEY}
            if unknown:
                raise FatalCheckError(
                    f"legacy v1 lock key(s) {sorted(unknown)} cannot be rebuilt"
                    " from the manifest capabilities (unprovable ledger; zero"
                    " delete/write)"
                )
        return {
            key: (Path(rel), "v1-body-hash", verified.entries[key])
            for key, rel in verified.owned_paths.items()
        }
    verified_v2 = verify_lock_v2(raw)
    return {
        key: (
            Path(key),
            entry.normalization_policy,
            entry.output_sha256,
        )
        for key, entry in verified_v2.entries.items()
    }


def _owned_still_matches(target: Path, kind: str, expect: str) -> bool:
    if kind == "v1-body-hash":
        return _lock_hash(target.read_text(encoding="utf-8")) == expect
    return sha256_of_bytes(canonicalize(target.read_bytes(), kind)) == expect


def _preflight_owned_reconcile_any(
    repo_root: Path,
    owned: dict[str, tuple[Path, str, str]],
    desired: set[Path],
) -> list[Path]:
    """Owned-only reconcile preflight generalized over both lock schemas —
    same hazard battery and messages as the legacy path (AC-05/AC-06)."""
    deletions: list[Path] = []
    for key in sorted(owned):
        rel, kind, expect = owned[key]
        if rel in desired:
            continue
        target = repo_root / rel
        ancestor = _reparse_ancestor(repo_root, rel)
        if ancestor is not None:
            raise FatalCheckError(
                f"symlink/reparse ancestor '{ancestor}' above lock-owned"
                f" '{rel.as_posix()}' (path hazard; zero delete/write)"
            )
        squat = _casefold_component_squatter(repo_root, rel)
        if squat is not None:
            raise FatalCheckError(
                f"'{squat[0]}' casefold-collides with component '{squat[1]}' of"
                f" lock-owned '{rel.as_posix()}' (owner ambiguity; zero"
                " delete/write)"
            )
        if target.is_symlink() or (target.exists() and not target.is_file()):
            raise FatalCheckError(
                f"lock-owned '{rel.as_posix()}' is not a regular file"
                " (path hazard; zero delete/write)"
            )
        if not target.exists():
            continue
        try:
            matches = _owned_still_matches(target, kind, expect)
        except (OSError, UnicodeDecodeError, LockVerificationError) as exc:
            raise FatalCheckError(
                f"lock-owned '{rel.as_posix()}' unreadable: {exc}"
                " (ownership unverifiable; zero delete/write)"
            ) from exc
        if not matches:
            raise FatalCheckError(
                f"lock-owned '{rel.as_posix()}' does not match its lock hash"
                " (owner ambiguity — possible hand edit; zero delete/write)"
            )
        deletions.append(rel)
    for rel in sorted(desired, key=lambda p: p.as_posix()):
        ancestor = _reparse_ancestor(repo_root, rel)
        if ancestor is not None:
            raise FatalCheckError(
                f"symlink/reparse ancestor '{ancestor}' above managed target"
                f" '{rel.as_posix()}' (path hazard; zero write)"
            )
        cur = repo_root
        for part in rel.parts[:-1]:
            cur = cur / part
            if cur.exists() and not cur.is_dir():
                raise FatalCheckError(
                    f"managed target '{rel.as_posix()}' is blocked by"
                    f" non-directory '{cur.relative_to(repo_root).as_posix()}'"
                    " (path hazard; zero write — remove it manually; owned-only"
                    " sync will not delete what it does not own)"
                )
        target = repo_root / rel
        if target.is_symlink() or (target.exists() and not target.is_file()):
            raise FatalCheckError(
                f"managed target '{rel.as_posix()}' is squatted by a non-regular"
                " file (path hazard; zero write — remove it manually)"
            )
        squat = _casefold_component_squatter(repo_root, rel)
        if squat is not None:
            raise FatalCheckError(
                f"'{squat[0]}' casefold-collides with component '{squat[1]}' of"
                f" managed target '{rel.as_posix()}' (path hazard; zero write —"
                " remove or rename it manually)"
            )
    return sorted(deletions, key=lambda p: p.as_posix())


def _read_typed_sources(repo_root: Path) -> tuple[Any, Any, str]:
    try:
        registry = load_workflow_registry(
            (repo_root / WORKFLOW_REGISTRY_RELPATH).read_text(encoding="utf-8")
        )
        tmap = load_translation_map(
            (repo_root / TRANSLATION_MAP_RELPATH).read_text(encoding="utf-8")
        )
        preface = (repo_root / PREFACE_RELPATH).read_text(encoding="utf-8")
    except (OSError, TranslationError) as exc:
        raise FatalCheckError(f"v2 typed sources unavailable: {exc}") from exc
    return registry, tmap, preface


def _translation_map_projection(tmap: Any) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "preface_template_version": tmap.preface_template_version,
        "lexicon": [
            {
                "category": c.name,
                "patterns": list(c.patterns),
                "disposition": c.disposition,
            }
            for c in sorted(tmap.lexicon.values(), key=lambda c: c.name)
        ],
        "sites": [
            {
                "site_id": s.site_id,
                "capability_id": s.capability_id,
                "path": s.path,
                "marker": s.marker,
                "disposition": s.disposition,
                "owner_gate_reason": s.owner_gate_reason,
            }
            for s in sorted(tmap.sites.values(), key=lambda s: s.site_id)
        ],
        "templates": dict(sorted(tmap.templates.items())),
    }


def _workflow_slice(
    registry: Any, cap_id: str, all_ids: set[str]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    wf = registry.workflow_for_capability(cap_id)
    if wf is None:
        raise FatalCheckError(
            f"translated capability '{cap_id}' has no workflow record"
        )
    edges: list[dict[str, Any]] = []
    expansions: list[dict[str, Any]] = []
    for e in registry.edges_from(cap_id):
        rec: dict[str, Any] = {
            "id": e.edge_id, "from": e.from_id, "to": e.to_id,
            "relation": e.relation, "activation": e.activation,
            "closure": e.closure,
        }
        if e.substitute is not None:
            rec["codex_substitute"] = {
                k: v for k, v in (
                    ("kind", e.substitute.kind),
                    ("route_ref", e.substitute.route_ref),
                    ("policy_ref", e.substitute.policy_ref),
                    ("rationale", e.substitute.rationale),
                ) if v is not None
            }
        if e.evidence is not None:
            rec["source_evidence"] = {
                "marker_id": e.evidence.marker_id,
                "path": e.evidence.path,
                "marker": e.evidence.marker,
                "construct": e.evidence.construct,
                "placement": e.evidence.placement,
            }
        edges.append(rec)
        if e.to_id.endswith("*"):
            expansions.append(
                {
                    "pattern": f"/{e.to_id}",
                    "resolved_ids": expand_wildcard(e.to_id, all_ids),
                }
            )
    expansions.sort(key=lambda x: x["pattern"])
    slice_obj = {
        "workflow": {
            "workflow_id": wf.workflow_id,
            "capability_id": wf.capability_id,
            "codex_discovery_summary": wf.codex_discovery_summary,
            "required_trigger_terms": list(wf.required_trigger_terms),
        },
        "edges": edges,
        "wildcard_expansions": expansions,
    }
    return slice_obj, expansions


def _v2_desired_state(
    repo_root: Path, manifest: dict[str, Any]
) -> tuple[dict[Path, bytes], dict[str, dict[str, Any]]]:
    """All v2 desired outputs + their lock entries (plan §2.6). Every
    derivation runs BEFORE any write; failures leave zero managed writes."""
    import scripts.sdd._common.codex_config_renderer as config_mod
    import scripts.sdd._common.codex_hook_renderer as hook_mod
    import scripts.sdd._common.codex_readme_renderer as readme_mod
    import scripts.sdd._common.codex_rule_renderer as rule_mod
    import scripts.sdd._common.skill_renderer as skill_mod

    caps = [c for c in manifest.get("capabilities") or [] if isinstance(c, dict)]
    all_ids = {str(c.get("id")) for c in caps}
    byte_copy = [c for c in caps if c.get("codex_carrier") == "byte-copy"]
    translated = [c for c in caps if c.get("codex_carrier") == "translated"]
    carrier_ids = {str(c["id"]) for c in byte_copy + translated}
    registry, tmap, preface = _read_typed_sources(repo_root)
    # Engine-level edge closure (plan §2.5 判定规则; Stage 11 #15): tests pin
    # the committed registry, but the ENGINE itself must refuse a bad one —
    # carrier-required needs a carrier target; every no-carrier target needs a
    # substitute; wildcards must expand non-empty.
    for edge in registry.edges.values():
        if edge.to_id.endswith("*"):
            try:
                expand_wildcard(edge.to_id, all_ids)
            except TranslationError as exc:
                raise FatalCheckError(str(exc)) from exc
            target_has_carrier = False
        else:
            target_has_carrier = edge.to_id in carrier_ids
        if edge.closure == "carrier-required" and not target_has_carrier:
            raise FatalCheckError(
                f"edge {edge.edge_id}: carrier-required target"
                f" {edge.to_id!r} has no Codex carrier (a substitute cannot"
                " stand in; fail closed)"
            )
        if not target_has_carrier and edge.substitute is None:
            raise FatalCheckError(
                f"edge {edge.edge_id}: target {edge.to_id!r} has no carrier and"
                " no codex_substitute (fail closed)"
            )
    skill_mod_sha = module_source_sha256(Path(skill_mod.__file__))
    readme_mod_sha = module_source_sha256(Path(readme_mod.__file__))
    config_mod_sha = module_source_sha256(Path(config_mod.__file__))
    map_sha = sha256_of_canonical(_translation_map_projection(tmap))
    preface_sha = sha256_of_bytes(
        (repo_root / PREFACE_RELPATH).read_bytes().replace(b"\r\n", b"\n")
    )

    outputs: dict[Path, bytes] = {}
    entries: dict[str, dict[str, Any]] = {}

    for cap in byte_copy:
        cap_id = str(cap["id"])
        src = _source_path(repo_root, cap_id)
        if not src.is_file():
            raise FatalCheckError(f"projection source missing for: {cap_id}")
        data = src.read_bytes()
        key = f".agents/skills/{cap_id}/SKILL.md"
        outputs[Path(key)] = data
        entries[key] = {
            "entry_kind": "skill-byte-copy",
            "owner": f"capability:{cap_id}",
            "surface_members": ["skills"],
            "strategy": "byte-copy",
            "normalization_policy": "raw-bytes-v1",
            "output_sha256": sha256_of_bytes(data),
            "inputs": {
                "source_path": f".claude/skills/{cap_id}/SKILL.md",
                "source_sha256": sha256_of_bytes(data),
                "manifest_slice_sha256": sha256_of_canonical(
                    manifest_capability_slice(cap)
                ),
                "renderer_module": skill_mod.RENDERER_MODULE,
                "renderer_module_sha256": skill_mod_sha,
                "renderer_version": skill_mod.RENDERER_VERSION,
            },
        }

    for cap in translated:
        cap_id = str(cap["id"])
        src = _source_path(repo_root, cap_id)
        if not src.is_file():
            raise FatalCheckError(f"projection source missing for: {cap_id}")
        source_bytes = src.read_bytes()
        try:
            rendered = render_translated(
                source_bytes, cap_id, registry, tmap, preface, carrier_ids
            )
        except TranslationError as exc:
            raise FatalCheckError(str(exc)) from exc
        data = rendered.encode("utf-8")
        slice_obj, expansions = _workflow_slice(registry, cap_id, all_ids)
        key = f".agents/skills/{cap_id}/SKILL.md"
        outputs[Path(key)] = data
        entries[key] = {
            "entry_kind": "skill-translated",
            "owner": f"capability:{cap_id}",
            "surface_members": ["skills"],
            "strategy": "translated",
            "normalization_policy": "translated-utf8-lf-v1",
            "output_sha256": sha256_of_bytes(data),
            "inputs": {
                "source_path": f".claude/skills/{cap_id}/SKILL.md",
                "source_sha256": sha256_of_bytes(
                    source_bytes.replace(b"\r\n", b"\n")
                ),
                "manifest_slice_sha256": sha256_of_canonical(
                    manifest_capability_slice(cap)
                ),
                "workflow_slice_sha256": sha256_of_canonical(slice_obj),
                "translation_map_sha256": map_sha,
                "preface_sha256": preface_sha,
                "renderer_module": skill_mod.RENDERER_MODULE,
                "renderer_module_sha256": skill_mod_sha,
                "renderer_version": skill_mod.RENDERER_VERSION,
                "wildcard_expansions": expansions,
                "wildcard_expansions_sha256": sha256_of_canonical(expansions),
            },
        }

    template_path = repo_root / "sdd" / "adapters" / "codex-skills-readme.md"
    template_version = manifest.get("codex_readme_template_version")
    if isinstance(template_version, bool) or not isinstance(template_version, int) \
            or template_version < 1:
        raise FatalCheckError(
            "manifest v2 requires integer codex_readme_template_version >= 1"
        )
    try:
        template_text = template_path.read_text(encoding="utf-8")
        readme_text = render_skills_readme(template_text, caps)
    except (OSError, ReadmeRenderError) as exc:
        raise FatalCheckError(f"README render failed: {exc}") from exc
    readme_bytes = readme_text.encode("utf-8")
    outputs[Path(".agents/README.md")] = readme_bytes
    entries[".agents/README.md"] = {
        "entry_kind": "skills-readme",
        "owner": "system:skills-readme",
        "surface_members": ["skills"],
        "strategy": "rendered",
        "normalization_policy": "generated-utf8-lf-v1",
        "output_sha256": sha256_of_bytes(readme_bytes),
        "inputs": {
            "manifest_slice_sha256": sha256_of_canonical(
                [manifest_capability_slice(c) for c in caps]
            ),
            "template_path": "sdd/adapters/codex-skills-readme.md",
            "template_sha256": sha256_of_bytes(
                template_path.read_bytes().replace(b"\r\n", b"\n")
            ),
            "template_version": template_version,
            "renderer_module": readme_mod.RENDERER_MODULE,
            "renderer_module_sha256": readme_mod_sha,
            "renderer_version": readme_mod.RENDERER_VERSION,
        },
    }

    mcp_project, posture, _never = load_mcp_projection(repo_root)
    if mcp_project:
        rendered_config = _render_codex_config(
            mcp_project, posture, _load_mcp_json(repo_root)
        )
        config_bytes = rendered_config.encode("utf-8")
        outputs[CODEX_CONFIG_RELPATH] = config_bytes
        mcp_json_bytes = (repo_root / MCP_JSON_RELPATH).read_bytes()
        entries[CODEX_LOCK_KEY] = {
            "entry_kind": "codex-config-mcp",
            "owner": "system:codex-config",
            "surface_members": ["mcp"],
            "strategy": "rendered",
            "normalization_policy": "canonical-toml-v1",
            "output_sha256": sha256_of_bytes(config_bytes),
            "inputs": {
                "mcp_source_path": ".mcp.json",
                "mcp_source_sha256": sha256_of_bytes(
                    mcp_json_bytes.replace(b"\r\n", b"\n")
                ),
                "manifest_mcp_slice_sha256": sha256_of_canonical(
                    manifest_mcp_slice(
                        (manifest.get("mcp") or {}).get("servers") or {}
                    )
                ),
                "codex_posture_slice_sha256": sha256_of_canonical(
                    codex_posture_slice(posture or {})
                ),
                "renderer_module": config_mod.RENDERER_MODULE,
                "renderer_module_sha256": config_mod_sha,
                "renderer_version": config_mod.RENDERER_VERSION,
            },
        }

    # --- enforcement surface (Epic #499 PR-D1a, plan §5.9 / §2.8.7) ----------
    # DIRECT ROUTE (Gate 1 拍板): no `config_binding` is rendered, so
    # `.codex/config.toml` above stays a pure `codex-config-mcp` entry and the
    # BLOCKING V11 mcp gate keeps exactly its registered scope. The composite
    # entry kind stays unused until/unless the explicit route is ever chosen.
    #
    # An ABSENT typed source means "no enforcement declared" and renders
    # nothing — the same shape as the `if mcp_project:` empty-tier branch above.
    # That is what keeps `.codex/hooks.json` an unowned neighbor in fixture
    # repos that declare no enforcement source (the plan §5.5 AC-05 negatives).
    source_path = repo_root / ENFORCEMENT_SOURCE_RELPATH
    if source_path.is_file():
        try:
            enforcement = load_enforcement_source(
                source_path.read_text(encoding="utf-8")
            )
            refs_inventory = policy_ref_inventory(repo_root, enforcement.policy_refs)
            hooks_text = hook_mod.render_hooks(enforcement)
            rules_texts = {
                rf.output_path: render_rules(rf) for rf in enforcement.rule_files
            }
        except (
            OSError,
            EnforcementSourceError,
            RuleRenderError,
            ValueError,
            # A YAML mapping with mixed-type keys reaches the validators as a
            # heterogeneous key set; anything that still raises TypeError from
            # that shape must become exit 2, never a traceback.
            TypeError,
        ) as exc:
            raise FatalCheckError(f"enforcement render failed: {exc}") from exc

        hook_mod_sha = module_source_sha256(Path(hook_mod.__file__))
        rule_mod_sha = module_source_sha256(Path(rule_mod.__file__))
        # Both output classes bind the SAME two inputs (plan §2.6 exact
        # input_keys): the typed source bytes and the policy-ref inventory, so
        # editing any declared policy_ref is a re-render trigger.
        enforcement_source_sha = sha256_of_bytes(
            source_path.read_bytes().replace(b"\r\n", b"\n")
        )
        policy_refs_sha = sha256_of_canonical(refs_inventory)

        hooks_bytes = hooks_text.encode("utf-8")
        outputs[Path(CODEX_HOOKS_KEY)] = hooks_bytes
        entries[CODEX_HOOKS_KEY] = {
            "entry_kind": "codex-hook",
            "owner": "system:codex-hooks",
            "surface_members": ["enforcement"],
            "strategy": "rendered",
            "normalization_policy": "canonical-json-v1",
            "output_sha256": sha256_of_bytes(hooks_bytes),
            "inputs": {
                "enforcement_source_sha256": enforcement_source_sha,
                "policy_refs_sha256": policy_refs_sha,
                "renderer_module": hook_mod.RENDERER_MODULE,
                "renderer_module_sha256": hook_mod_sha,
                "renderer_version": hook_mod.RENDERER_VERSION,
            },
        }
        for out_path, text in sorted(rules_texts.items()):
            rule_bytes = text.encode("utf-8")
            outputs[Path(out_path)] = rule_bytes
            entries[out_path] = {
                "entry_kind": "codex-rule",
                "owner": f"system:codex-rules:{out_path}",
                "surface_members": ["enforcement"],
                "strategy": "rendered",
                "normalization_policy": "generated-utf8-lf-v1",
                "output_sha256": sha256_of_bytes(rule_bytes),
                "inputs": {
                    "enforcement_source_sha256": enforcement_source_sha,
                    "policy_refs_sha256": policy_refs_sha,
                    "renderer_module": rule_mod.RENDERER_MODULE,
                    "renderer_module_sha256": rule_mod_sha,
                    "renderer_version": rule_mod.RENDERER_VERSION,
                },
            }
    return outputs, entries


def _v2_lock_envelope(entries: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": 2,
        "generator_protocol_version": 1,
        "entries": {k: entries[k] for k in sorted(entries)},
    }


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".agents-sync-tmp")
    try:
        tmp.write_bytes(data)
        os.replace(tmp, path)
    except OSError:
        # Best-effort tmp cleanup so a failed write does not strand a
        # permanent unowned neighbor that --check flags forever (Stage 11 #12).
        with contextlib.suppress(OSError):
            tmp.unlink(missing_ok=True)
        raise


def _do_sync_v2(
    repo_root: Path,
    manifest: dict[str, Any],
    lock_class: str | None,
    lock_raw: dict[str, Any] | None,
) -> list[str]:
    """v2 converge (cutover included: a verified v1 lock acts as a read-only
    owner ledger). No cross-file transaction is faked: every derivation runs
    before the first write; the apply phase uses per-file tmp+atomic-replace
    and reports completed/pending targets on failure, and the next sync
    converges (plan §1.2)."""
    outputs, entries = _v2_desired_state(repo_root, manifest)
    try:
        lock_text = lock_v2_canonical_text(_v2_lock_envelope(entries))
    except LockVerificationError as exc:
        raise FatalCheckError(
            f"generated lock failed its own verifier: {exc} (zero writes)"
        ) from exc
    manifest_ids = {
        str(c.get("id"))
        for c in manifest.get("capabilities") or []
        if isinstance(c, dict)
    }
    owned = _owned_paths_any(lock_class, lock_raw, v1_allowed_keys=manifest_ids)
    desired = {Path(p) for p in outputs} | {LOCK_RELPATH}
    deletions = _preflight_owned_reconcile_any(repo_root, owned, desired)

    changes: list[str] = []
    for rel in deletions:
        path = repo_root / rel
        path.unlink()
        changes.append(f"remove {rel.as_posix()}")
        _prune_empty_dirs(repo_root, path.parent, changes)

    pending = sorted(outputs, key=lambda p: p.as_posix())
    done: list[str] = []
    try:
        for rel in pending:
            target = repo_root / rel
            data = outputs[rel]
            entry_key = rel.as_posix()
            policy = entries.get(entry_key, {}).get(
                "normalization_policy", "raw-bytes-v1"
            )
            if not target.is_file() or canonicalize(
                target.read_bytes(), policy
            ) != canonicalize(data, policy):
                _atomic_write(target, data)
                changes.append(f"write {rel.as_posix()}")
            done.append(rel.as_posix())
        lock_path = repo_root / LOCK_RELPATH
        if not lock_path.is_file() or _read_lf(lock_path) != lock_text:
            _atomic_write(lock_path, lock_text.encode("utf-8"))
            changes.append(f"write {LOCK_RELPATH.as_posix()}")
    except OSError as exc:
        remaining = [p.as_posix() for p in pending if p.as_posix() not in done]
        raise FatalCheckError(
            f"partial apply: {exc}; completed: {done or ['(none)']};"
            f" pending: {remaining + [LOCK_RELPATH.as_posix()]} — rerun sync to"
            " converge (per-file atomic replace; no cross-file transaction)"
        ) from exc
    return changes


def _do_check_v2(
    repo_root: Path, manifest: dict[str, Any], surface: str
) -> list[str]:
    outputs, entries = _v2_desired_state(repo_root, manifest)
    lock_text = lock_v2_canonical_text(_v2_lock_envelope(entries))
    drift: list[str] = []
    check_skills = surface in ("skills", "all")

    def _in_scope(key: str) -> bool:
        """Route by the entry's OWN `surface_members` (plan §2.6), not by an
        `is_mcp = key == CODEX_LOCK_KEY` dichotomy.

        The dichotomy was correct while `skills` and `mcp` were the only
        surfaces, but it classifies anything that is not the reserved config key
        as `skills` — so once PR-D1a lands `.codex/hooks.json` and
        `.codex/rules/*.rules`, enforcement drift would be enforced by V10
        (BLOCKING, registered scope = skills) instead of V13 (warning). That is
        the "borrow an existing blocking gate to bypass the new one" shape the
        plan forbids; this narrows V10 back to its registered scope.
        """
        return surface == "all" or surface in entries[key]["surface_members"]

    for rel in sorted(outputs, key=lambda p: p.as_posix()):
        posix = rel.as_posix()
        if not _in_scope(posix):
            continue
        policy = entries[posix]["normalization_policy"]
        target = repo_root / rel
        if not target.is_file():
            drift.append(f"missing artifact: {posix} (run sync)")
        elif canonicalize(target.read_bytes(), policy) != canonicalize(
            outputs[rel], policy
        ):
            drift.append(
                f"artifact != desired render for '{posix}' (hand-edited artifact"
                " OR source edited without re-running sync)"
            )
    if check_skills:
        # Only skills-surface outputs live under `.agents/`; selecting them by
        # surface_members (rather than "everything except the config key") keeps
        # the orphan scan honest now that enforcement outputs also exist.
        expected = {
            Path(p)
            for p in outputs
            if "skills" in entries[p.as_posix()]["surface_members"]
        }
        expected_dirs = {p.parent for p in expected} | {AGENTS_DIR, SKILLS_DIR}
        agents_root = repo_root / AGENTS_DIR
        if agents_root.is_dir():
            for path in sorted(agents_root.rglob("*")):
                rel = path.relative_to(repo_root)
                if path.is_file() and rel not in expected:
                    drift.append(
                        f"unexpected file: {rel.as_posix()} (unowned neighbor —"
                        " owned-only sync will NOT delete it; remove manually)"
                    )
                elif path.is_dir() and rel not in expected_dirs:
                    drift.append(
                        f"unexpected directory: {rel.as_posix()}/ (unowned"
                        " neighbor — owned-only sync will NOT delete it; remove"
                        " manually)"
                    )
    lock_path = repo_root / LOCK_RELPATH
    if not lock_path.is_file():
        drift.append(f"missing {LOCK_RELPATH.as_posix()}")
    elif surface == "all":
        if _read_lf(lock_path) != lock_text:
            drift.append(
                f"{LOCK_RELPATH.as_posix()} out of date (v2 canonical envelope"
                " is regenerated by sync)"
            )
    else:
        # Scoped surfaces validate THEIR lock entries too — otherwise a stale
        # input-digest closure ships through the V10/V11 gates after the
        # cutover (Stage 11 #4/#31). Entries outside the scope are ignored so
        # mcp drift never reddens the skills step and vice versa.
        from scripts.sdd._common.projection_loader import parse_lock_json

        try:
            on_disk = parse_lock_json(lock_path.read_text(encoding="utf-8"))
        except LockVerificationError:
            on_disk = None
        disk_entries = (
            on_disk.get("entries")
            if isinstance(on_disk, dict) and isinstance(on_disk.get("entries"), dict)
            else None
        )
        if disk_entries is None:
            drift.append(
                f"{LOCK_RELPATH.as_posix()} is not a readable v2 envelope"
                " (regenerate via sync)"
            )
        else:
            for key in sorted(entries):
                if not _in_scope(key):
                    continue
                if disk_entries.get(key) != entries[key]:
                    drift.append(
                        f"lock entry out of date for '{key}' (input/output"
                        " digest closure; regenerate via sync)"
                    )
    return drift


def _do_adopt_v2(
    repo_root: Path,
    manifest: dict[str, Any],
    lock_class: str | None,
    lock_raw: dict[str, Any] | None,
    name: str,
) -> list[str]:
    """byte-copy recovery/import escape hatch under a verified v2 lock ONLY
    (plan §2.7 CAS table). Everything else exits 2 with zero writes."""
    if lock_class != "v2" or lock_raw is None:
        raise FatalCheckError(
            "ADOPT_REQUIRES_LOCK_V2: the legacy v1 lock's body-only digest"
            " cannot prove the frontmatter unchanged — adopt is disabled until"
            " the tree carries a verified v2 lock (zero source/artifact/lock"
            " writes)"
        )
    verified = verify_lock_v2(lock_raw)
    caps = {
        str(c.get("id")): c
        for c in manifest.get("capabilities") or []
        if isinstance(c, dict)
    }
    cap = caps.get(name)
    if cap is None or cap.get("codex_carrier") != "byte-copy":
        raise FatalCheckError(
            f"--adopt eligible set derives from codex_carrier: byte-copy only;"
            f" '{name}' is {((cap or {}).get('codex_carrier'))!r} (exit 2, zero"
            " writes)"
        )
    key = f".agents/skills/{name}/SKILL.md"
    entry = verified.entries.get(key)
    if entry is None or entry.owner != f"capability:{name}" \
            or entry.strategy != "byte-copy":
        raise FatalCheckError(
            f"verified v2 lock has no byte-copy owner for '{key}' (zero writes)"
        )
    assert entry.inputs is not None
    base_source = str(entry.inputs["source_sha256"])
    base_output = entry.output_sha256
    src = _source_path(repo_root, name)
    artifact = repo_root / SKILLS_DIR / name / "SKILL.md"

    def _digest(path: Path) -> str | None:
        return sha256_of_bytes(path.read_bytes()) if path.is_file() else None

    source_state = _digest(src)
    artifact_state = _digest(artifact)
    source_is_base = source_state == base_source
    artifact_is_base = artifact_state == base_output
    changes: list[str] = []
    if source_is_base and artifact_is_base:
        return changes  # no-op, exit 0, zero writes
    adoptable = (
        (source_is_base and artifact_state is not None and not artifact_is_base)
        or (source_state is None and artifact_is_base)
    )
    if not adoptable:
        raise FatalCheckError(
            f"--adopt CAS failed for '{name}': source"
            f" {'base' if source_is_base else ('missing' if source_state is None else 'changed')},"
            f" artifact"
            f" {'base' if artifact_is_base else ('missing' if artifact_state is None else 'changed')}"
            " — ambiguous/mixed state; zero writes (plan §2.7)"
        )
    data = artifact.read_bytes()
    # The SOURCE write target gets the full hazard battery too (plan §2.7
    # containment/type checks; Stage 11 F2 — a junction/casefold squat at
    # .claude/skills/<name> must never let adopt write outside the repo).
    _preflight_owned_reconcile_any(
        repo_root, {}, {Path(".claude") / "skills" / name / "SKILL.md"}
    )
    # apply-time re-verification: the CAS must still hold at the write moment
    if _digest(artifact) != artifact_state or _digest(src) != source_state:
        raise FatalCheckError(
            f"--adopt CAS re-check failed for '{name}' (state moved; zero writes)"
        )
    src.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write(src, data)
    changes.append(f"adopt {SOURCE_DIR.as_posix()}/{name}/SKILL.md <- artifact")
    changes += _do_sync_v2(repo_root, manifest, "v2", lock_raw)
    return changes


# --------------------------------------------------------------------------- doctor
# `doctor` is the machine-aware exception to the CI-pure contract above: it reads
# per-machine state (Codex trust, HKCU MCP-secret env, skill/manifest canary) and
# NEVER runs in CI. It writes nothing (D-015). Warning-only: warnings are printed but
# never change the exit code (0 = report produced; 2 only on a fatal unreadable
# manifest, via load_project_set -> FatalCheckError).


def _norm_path(p: str) -> str:
    r"""Normalize a path string for trust-entry comparison: strip the Windows `\\?\`
    extended-length prefix, unify separators, drop a trailing slash, and casefold
    (Codex `[projects]` keys are Windows-case-insensitive and appear with mixed
    drive-letter case + backslashes)."""
    p = p.strip()
    if p.startswith("\\\\?\\"):
        p = p[4:]
    return p.replace("\\", "/").rstrip("/").casefold()


def _doctor_trust(repo_root: Path, home: Path) -> list[str]:
    out = ["", "TRUST (Codex ~/.codex/config.toml [projects]; read-only, D-015):"]
    config = home / ".codex" / "config.toml"
    if not config.is_file():
        out.append(f"  [WARN] no {config} -- current root is UNTRUSTED to Codex")
        out.append(
            "         (Codex trust is a manual per-engineer x per-worktree step;"
            " see onboarding -- doctor never writes it)"
        )
        return out
    try:
        data = tomllib.loads(config.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        # UnicodeDecodeError: a hand-edited config saved in a non-UTF-8 codepage
        # (plausible on a Chinese-locale Windows box) must degrade to [WARN], not
        # crash -- mirroring the lenient decode in _doctor_env.
        out.append(f"  [WARN] {config} unreadable: {exc}")
        return out
    projects = data.get("projects")
    trusted = {
        _norm_path(key)
        for key, val in (projects.items() if isinstance(projects, dict) else ())
        if isinstance(val, dict) and val.get("trust_level") == "trusted"
    }
    # Codex matches the exact project root OR an in-repo ancestor entry (the container
    # entry covers every worktree; S2 spike 3). Report the first ancestor that matches.
    match = next(
        (anc for anc in (repo_root, *repo_root.parents)
         if _norm_path(str(anc)) in trusted),
        None,
    )
    if match is not None:
        out.append(f"  [PASS] current root is TRUSTED via [projects] entry: {match}")
    else:
        out.append(f"  [WARN] {repo_root} is UNTRUSTED (no matching [projects] entry)")
    return out


def _doctor_env(repo_root: Path, system: str) -> list[str]:
    out = ["", "ENV (HKCU MCP-secret vars; setup-mcp-secrets.ps1 -Reload; presence only):"]
    if system != "Windows":
        out.append(f"  [N/A] non-Windows ({system or 'unknown'}); HKCU env is Windows-only")
        return out
    script = repo_root / ".claude" / "scripts" / "setup-mcp-secrets.ps1"
    if shutil.which("powershell") is None or not script.is_file():
        out.append("  [N/A] powershell or setup-mcp-secrets.ps1 unavailable")
        return out
    try:
        # Capture BYTES, not text: PowerShell console output is not reliably UTF-8
        # (Windows codepage), so text=True's reader thread would crash on invalid
        # continuation bytes and leave stdout=None. Decode leniently below; the
        # status markers ([SET]/[MISSING]/[Done]) are ASCII regardless of codepage,
        # and the whole report is ASCII-coerced downstream anyway.
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-File", str(script), "-Reload"],
            cwd=str(repo_root),
            capture_output=True,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        out.append(f"  [WARN] -Reload did not run: {exc}")
        return out
    # Report PRESENCE ONLY. setup-mcp-secrets.ps1 -Reload prints a first-4-chars mask
    # ([SET] key = abcd****), which for a password is a partial secret. Keep only the
    # [SET]/[MISSING]/[Done]/[Reload] status lines and strip every value fragment, so
    # doctor never echoes any part of a secret (plan AC: presence only, no secret echo).
    text = proc.stdout.decode("utf-8", "replace") if proc.stdout else ""
    status: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line.startswith("["):
            continue  # drop banner / openssl-path / separator noise
        if line.startswith("[SET]") and " = " in line:
            line = line.split(" = ", 1)[0].rstrip()  # drop "= <first-4-chars>****"
        status.append(f"  {line}")
    out += status if status else ["  [WARN] -Reload produced no status lines"]
    return out


def _doctor_canary(repo_root: Path) -> list[str]:
    out = ["", "CANARY (on-disk .claude/skills == manifest capabilities):"]
    _, all_ids = load_project_set(repo_root)  # FatalCheckError -> exit 2 if unreadable
    on_disk = {p.parent.name for p in (repo_root / SOURCE_DIR).glob("*/SKILL.md")}
    if all_ids == on_disk:
        out.append(f"  [PASS] {len(all_ids)} skills match manifest")
        return out
    missing = sorted(all_ids - on_disk)
    extra = sorted(on_disk - all_ids)
    out.append(f"  [WARN] drift: manifest={len(all_ids)} on-disk={len(on_disk)}")
    if missing:
        out.append(f"         in manifest but not on disk: {', '.join(missing)}")
    if extra:
        out.append(f"         on disk but not in manifest: {', '.join(extra)}")
    out.append(
        "         (the CI-enforced canary unit test guards this; re-run sync or"
        " fix the manifest)"
    )
    return out


def do_doctor(
    repo_root: Path,
    *,
    home: Path | None = None,
    system: str | None = None,
) -> list[str]:
    """Read-only per-machine health report (trust / HKCU env / canary). Writes nothing
    (D-015). `home` / `system` are injectable for tests. Output is coerced to ASCII
    (#318: Windows consoles may not be UTF-8)."""
    home = home if home is not None else Path.home()
    system = system if system is not None else platform.system()
    lines = ["agents_sync doctor -- read-only per-machine checks (never runs in CI)"]
    lines += _doctor_trust(repo_root, home)
    lines += _doctor_env(repo_root, system)
    lines += _doctor_canary(repo_root)
    return [ln.encode("ascii", "replace").decode("ascii") for ln in lines]


def main(argv: list[str] | None = None, repo_root: Path | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog=_SCRIPT_NAME,
        description=(
            "Scoped projection generator, emitters A+B: .claude/skills whitelist ->"
            " .agents/skills artifacts; .mcp.json x manifest mcp tiers ->"
            " .codex/config.toml; + .agents.lock.json"
            " (plan §8, D-011/D-012/D-013/D-014/D-015)"
        ),
    )
    parser.add_argument(
        "command", nargs="?", choices=["sync", "doctor"],
        help="sync: regenerate artifacts + README + config.toml + lock"
             " (owned-only reconcile, ADR-039 D-012 revised; idempotent)."
             " doctor: read-only per-machine trust/env/canary"
             " report (S3a; never in CI; writes nothing, D-015)",
    )
    parser.add_argument(
        "--check", action="store_true",
        help="read-only drift check (LF-normalized); exit 1 on drift",
    )
    parser.add_argument(
        "--surface", choices=["skills", "mcp", "enforcement", "all"], default="all",
        help="scope --check to one projection surface (V10=skills warning,"
             " V11=mcp blocking, V13=enforcement warning); default: all",
    )
    parser.add_argument(
        "--adopt", metavar="SKILL",
        help="explicit reverse-feed: artifact -> source, then realign (Owner HITL"
             " applies; skills surface only)",
    )
    args = parser.parse_args(argv)
    root = repo_root if repo_root is not None else _REPO_ROOT

    modes = [
        args.command == "sync",
        args.command == "doctor",
        args.check,
        args.adopt is not None,
    ]
    if sum(modes) != 1:
        parser.print_usage(sys.stderr)
        print(
            f"{_SCRIPT_NAME}: exactly one mode required:"
            " `sync` XOR `doctor` XOR --check XOR --adopt",
            file=sys.stderr,
        )
        return 2
    if args.surface != "all" and not args.check:
        parser.print_usage(sys.stderr)
        print(f"{_SCRIPT_NAME}: --surface only applies to --check", file=sys.stderr)
        return 2

    try:
        if args.command == "doctor":
            for line in do_doctor(root):
                print(line)
            return 0
        project, _ = load_project_set(root)
        if args.check:
            drift = do_check(root, project, surface=args.surface)
            for line in drift:
                print(f"[DRIFT] {line}")
            if drift:
                # A scoped surface always prints its own remediation line; "all"
                # prints the skills line plus the mcp line when mcp drift is present
                # (review finding #330-7: never exit 1 without a prescribed action).
                enforcement_drift = any(
                    (CODEX_HOOKS_KEY in line) or (CODEX_RULES_PREFIX in line)
                    for line in drift
                )
                if args.surface in ("skills", "all"):
                    print(PRESCRIBED_ACTION)
                if args.surface == "mcp" or (
                    args.surface == "all"
                    and any(".codex" in line for line in drift)
                ):
                    print(PRESCRIBED_ACTION_MCP)
                # Under surface=all an enforcement-only drift used to print ONLY
                # the skills and mcp actions, sending the reader to
                # `.claude/skills/` and `.mcp.json` for a problem whose source is
                # `sdd/adapters/codex-enforcement.yml`.
                if args.surface == "enforcement" or (
                    args.surface == "all" and enforcement_drift
                ):
                    print(PRESCRIBED_ACTION_ENFORCEMENT)
                if args.surface == "enforcement":
                    print(RESULT_EXECUTED_WITH_FINDINGS)
                return 1
            print(
                f"OK: projection in sync (surface={args.surface}, {len(project)}"
                " skills, lock consistent)"
            )
            if args.surface == "enforcement":
                print(_enforcement_result_code(root))
            return 0
        if args.adopt is not None:
            changes = do_adopt(root, project, args.adopt)
            for line in changes:
                print(line)
            print(
                "NOTE: --adopt wrote the SOURCE skill; the source's own gates / Owner"
                " HITL apply to that change. Review and commit source + artifacts +"
                " lock together."
            )
            return 0
        changes = do_sync(root, project)
        for line in changes:
            print(line)
        print(
            f"OK: {len(changes)} change(s)" if changes
            else f"OK: up to date ({len(project)} skills)"
        )
        return 0
    except FatalCheckError as exc:
        print(f"{_SCRIPT_NAME}: {exc}", file=sys.stderr)
        _print_enforcement_error_code(args)
        return 2
    except LockVerificationError as exc:
        # A malformed/mixed ledger surfacing from any depth of the v2 engine
        # is the SAME exit-2 zero-write contract, never a traceback
        # (Stage 11 #9/#11/#27).
        print(f"{_SCRIPT_NAME}: {exc}", file=sys.stderr)
        _print_enforcement_error_code(args)
        return 2


if __name__ == "__main__":
    sys.exit(main())
