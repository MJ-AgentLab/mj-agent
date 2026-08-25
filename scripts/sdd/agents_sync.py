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
import json
import os
import platform
import re
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

from scripts.sdd._common.frontmatter import body_sha256  # noqa: E402
from scripts.sdd._common.projection_loader import (  # noqa: E402
    CODEX_CONFIG_RELPATH,
    CODEX_LOCK_KEY,
    LOCK_RELPATH,
    LockVerificationError,
    VerifiedLock,
    load_verified_lock,
)
from scripts.sdd.check_agents_projection import (  # noqa: E402
    FatalCheckError,
    load_mcp_projection,
    load_project_set,
)

SOURCE_DIR = Path(".claude/skills")
AGENTS_DIR = Path(".agents")
SKILLS_DIR = AGENTS_DIR / "skills"
CODEX_DIR = Path(".codex")
MCP_JSON_RELPATH = Path(".mcp.json")

# Emitter B rendering rules (S2 #330). Source `.mcp.json` server fields the emitter
# understands; anything else is an Owner decision, not a silent projection.
_ALLOWED_SERVER_FIELDS = {"type", "command", "args", "env"}
# Pure by-name reference form — the ONLY env value shape that may be projected
# (becomes an `env_vars` whitelist entry; `${VAR:-default}` carries literals, refuse).
_ENV_REF = re.compile(r"^\$\{([A-Za-z_][A-Za-z0-9_]*)\}$")
# args are projected verbatim, so they must carry NO substitution syntax at all:
# Codex does not interpolate `${VAR}` (a pure ref silently breaks the server) and
# `${VAR:-default}` defaults embed literals (e.g. credential URLs) — both refuse.
_ARG_USERINFO = re.compile(r"://[^/\s:@]+:[^@\s]+@")
# Arg-pair rewrite (manifest serena `transform` note): Codex consumes its own context.
_CONTEXT_ARG = "--context"
_CONTEXT_TRANSFORM = {"claude-code": "codex"}
_POSTURE_KEYS = ("approval_policy", "sandbox_mode", "project_doc_max_bytes")

CODEX_CONFIG_HEADER = """\
# GENERATED -- do not edit this file. Owned 100% by scripts/sdd/agents_sync.py
# (emitter B; dual-agent-compat v5 S2 #330, ADR-036 D-011/D-012).
# Derived from .mcp.json (A14 hard-stop source, human-maintained) filtered by the
# manifest `mcp` per-server tiers (D-013) + `codex.posture` (D-017) in
# sdd/development-agent.yml. Secrets are referenced BY NAME via `env_vars`
# (Codex TOML has no ${VAR} interpolation; Codex sanitizes MCP child env and
# `env_vars` inherits the named variables from the parent environment) --
# literal credentials must never appear here (G7 scans this file; V11 blocks drift).
# To change: edit the SOURCE through its own gate, then run
# `python scripts/sdd/agents_sync.py sync` and commit config + .agents.lock.json.
"""

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


def _toml_str(value: str) -> str:
    # JSON string escaping is a valid TOML basic-string subset for our charset
    # (both escape backslash/quote the same way; \\uXXXX is valid TOML).
    return json.dumps(value, ensure_ascii=True)


def _transform_args(args: list[str]) -> list[str]:
    out = list(args)
    for i, arg in enumerate(out[:-1]):
        if arg == _CONTEXT_ARG and out[i + 1] in _CONTEXT_TRANSFORM:
            out[i + 1] = _CONTEXT_TRANSFORM[out[i + 1]]
    return out


def _render_codex_config(
    mcp_project: dict[str, dict[str, Any]],
    posture: dict[str, Any] | None,
    mcp_json_servers: dict[str, Any],
) -> str:
    """Render `.codex/config.toml` text (LF, ASCII, deterministic). Fail-closed on
    anything the emitter does not positively understand."""
    if not isinstance(posture, dict):
        raise FatalCheckError(
            "manifest codex.posture section required to render .codex/config.toml"
        )
    lines = CODEX_CONFIG_HEADER.rstrip("\n").split("\n")
    lines.append("")
    for key in _POSTURE_KEYS:
        value = posture.get(key)
        if isinstance(value, bool) or value is None:
            raise FatalCheckError(f"codex.posture.{key} missing or invalid")
        if isinstance(value, int):
            lines.append(f"{key} = {value}")
        elif isinstance(value, str):
            lines.append(f"{key} = {_toml_str(value)}")
        else:
            raise FatalCheckError(f"codex.posture.{key} must be a string or integer")

    for name in sorted(mcp_project):
        if not re.fullmatch(r"[A-Za-z0-9_-]+", name):
            raise FatalCheckError(f"mcp server name {name!r} is not a bare TOML key")
        defn = mcp_json_servers.get(name)
        if not isinstance(defn, dict):
            raise FatalCheckError(
                f"project-tier mcp server '{name}' missing from .mcp.json"
            )
        unknown = sorted(set(defn) - _ALLOWED_SERVER_FIELDS)
        if unknown:
            raise FatalCheckError(
                f"server '{name}' has field(s) the emitter does not understand:"
                f" {', '.join(unknown)} (fail-closed; needs an Owner decision)"
            )
        if defn.get("type", "stdio") != "stdio":
            raise FatalCheckError(
                f"server '{name}' has type {defn.get('type')!r} — only stdio servers"
                " are projectable (fail-closed; needs an Owner decision)"
            )
        command = defn.get("command")
        if not isinstance(command, str) or not command:
            raise FatalCheckError(f"server '{name}' needs a non-empty string 'command'")
        args = defn.get("args", [])
        if not isinstance(args, list) or not all(isinstance(a, str) for a in args):
            raise FatalCheckError(f"server '{name}' 'args' must be a list of strings")
        for arg in args:
            if "${" in arg:
                raise FatalCheckError(
                    f"server '{name}' has a substitution expression in args — Codex"
                    " does not interpolate ${VAR} (and ${VAR:-default} embeds"
                    " literals); args must be projectable verbatim (fail-closed)"
                )
            if _ARG_USERINFO.search(arg):
                raise FatalCheckError(
                    f"server '{name}' has a URL userinfo credential shape in args"
                    " — literal credentials are never projected (fail-closed)"
                )
        env = defn.get("env", {})
        if not isinstance(env, dict):
            raise FatalCheckError(f"server '{name}' 'env' must be a mapping")
        env_names: list[str] = []
        for env_key in sorted(env):
            env_val = env[env_key]
            match = _ENV_REF.match(env_val) if isinstance(env_val, str) else None
            if match is None:
                raise FatalCheckError(
                    f"server '{name}' env '{env_key}' is not a pure ${{VAR}} reference"
                    " -- literal values are never projected (fail-closed; secrets go"
                    " by NAME via env_vars)"
                )
            env_names.append(match.group(1))
        # The context rewrite is gated on the manifest per-server `transform` field
        # (D-013 SoT) — servers without it are projected with untouched args.
        if mcp_project[name].get("transform"):
            args = _transform_args(args)
        lines.append("")
        lines.append(f"[mcp_servers.{name}]")
        lines.append(f"command = {_toml_str(command)}")
        rendered_args = ", ".join(_toml_str(a) for a in args)
        lines.append(f"args = [{rendered_args}]")
        if env_names:
            rendered_env = ", ".join(_toml_str(n) for n in sorted(set(env_names)))
            lines.append(f"env_vars = [{rendered_env}]")
    return "\n".join(lines) + "\n"


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
            lock: dict[str, Any] = json.loads(lock_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
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
    """Copy artifact bytes back over the source, then realign via sync."""
    if name not in project:
        raise FatalCheckError(
            f"--adopt target '{name}' is not a manifest `projection: project` capability"
        )
    artifact = repo_root / SKILLS_DIR / name / "SKILL.md"
    if not artifact.is_file():
        raise FatalCheckError(f"--adopt target artifact missing: {artifact}")
    src = _source_path(repo_root, name)
    changes: list[str] = []
    data = artifact.read_bytes()
    # A missing source is a legitimate recovery state (restore a deleted source
    # from its committed artifact) — recreate it instead of crashing.
    if not src.is_file() or src.read_bytes() != data:
        src.parent.mkdir(parents=True, exist_ok=True)
        src.write_bytes(data)
        changes.append(f"adopt {SOURCE_DIR.as_posix()}/{name}/SKILL.md <- artifact")
    changes += do_sync(repo_root, project)
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
        "--surface", choices=["skills", "mcp", "all"], default="all",
        help="scope --check to one projection surface (V10=skills warning,"
             " V11=mcp blocking); default: all",
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
                if args.surface in ("skills", "all"):
                    print(PRESCRIBED_ACTION)
                if args.surface == "mcp" or (
                    args.surface == "all"
                    and any(".codex" in line for line in drift)
                ):
                    print(PRESCRIBED_ACTION_MCP)
                return 1
            print(
                f"OK: projection in sync (surface={args.surface}, {len(project)}"
                " skills, lock consistent)"
            )
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
        return 2


if __name__ == "__main__":
    sys.exit(main())
