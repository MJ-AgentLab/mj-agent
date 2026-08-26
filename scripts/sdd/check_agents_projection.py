"""check_agents_projection.py — V9: projection-domain checker (closure/reconcile/lock).

Contract: plans/[PLAN]_dual-agent-compat.md §10 (v5 projection rules) — same CLI family
as check_development_agent.py, mounted on the same CI gate (warning-first at P1/S0).
Declared in sdd/adapters/development-agent.md §Standards; registered in sdd/gates.md §2 (V9).

Rules (S0 empty-state MUST NOT false-fail; artifacts land in S1/S2):
1. Reference closure — for every manifest capability with `projection: project`, the
   `/mj-agent-*` out-edges inside its SKILL.md `## Handoff*` sections must themselves be
   in the project set. Severity: warning while `.agents/` does not exist (S0), error once
   it does (S1+). Owner-approved narrow definition (Stage 5 拍板 #5, 2026-07-13).
2. Full reconcile — directories under `.agents/skills/` must equal the manifest project
   set exactly; extra or missing entries FAIL. `.agents/` absent == vacuous pass.
3. Lock consistency — `.agents.lock.json` maps projected skill name -> body sha256
   (LF-normalized, frontmatter-stripped; canonical `_common.frontmatter.body_sha256`).
   Both absent == pass; exactly one present == FAIL; hash mismatch == FAIL. The single
   non-skill key allowed is the S2 reserved path key `.codex/config.toml` (see rule 4).
4. Codex MCP projection (S2 #330, PJ04x) — `.codex/config.toml` pairs with the reserved
   lock key (exactly one present == FAIL); its `[mcp_servers.*]` names must equal the
   manifest `mcp` project-tier set (never-tier names are a dedicated data-boundary
   violation, PJ044); reserved-key hash must match the on-disk file (LF-normalized
   `body_sha256`; a TOML file has no frontmatter so this is a whole-text hash). Both
   file and reserved key absent == vacuous pass (pre-S2 / fork empty state — drift
   enforcement lives in `agents_sync.py --check --surface mcp`, V11 blocking).
   PJ045 (narrowed at Epic #499 PR-A1, ADR-039 D-012 revised): files under
   `.codex/` other than the generated config are UNOWNED NEIGHBORS (future
   hooks/rules, user files) — reported info-only, never gate-affecting; the
   generator preserves them (owned-only reconcile).

Exit codes: 0 / 1 / 2 as in check_development_agent.py.
`main(argv=None, repo_root=None)` — repo_root injectable for tests (#217 pattern).
Read-only; no secrets; no network.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

_SCRIPT_NAME = "check_agents_projection.py"
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.sdd._common.frontmatter import body_sha256  # noqa: E402
from scripts.sdd._common.projection_loader import (  # noqa: E402
    CODEX_CONFIG_RELPATH,
    CODEX_LOCK_KEY,
    handoff_refs,
)

MANIFEST_RELPATH = Path("sdd/development-agent.yml")
JSON_SCHEMA_VERSION = 1
# {1, 2} since Epic #499 PR-B (dormant v2 engine): both manifest versions are
# readable; the real tree stays v1 until the PR-C1 cutover. Unknown versions
# keep raising FatalCheckError (exit 2). The discriminator governs only the
# manifest — the lock and each typed source carry their own schema_version.
KNOWN_MANIFEST_SCHEMA_VERSIONS = {1, 2}

# S2 MCP projection surface (#330): CODEX_CONFIG_RELPATH / CODEX_LOCK_KEY are
# canonical in _common/projection_loader.py since Epic #499 PR-A1 (re-exported
# above for existing importers); the `## Handoff*` parser lives there too, so
# V9 and the PR-B dependency scanner read one implementation (plan §2.5).

WATCHED_PREFIXES = (
    "sdd/development-agent.yml",
    ".agents/",
    ".agents.lock.json",
    ".codex/",
    ".claude/skills/",
    "scripts/sdd/check_agents_projection.py",
    "scripts/sdd/_common/projection_loader.py",
    # v2 closure inputs (Epic #499 PR-B; PJ05x reads the registry through the
    # shared renderer-module loader):
    "sdd/workflows/development-agent-workflows.yml",
    "sdd/adapters/codex-skill-translation.yml",
    "sdd/adapters/codex-skill-preface.md",
    "scripts/sdd/_common/skill_renderer.py",
)


@dataclass
class Violation:
    code: str
    severity: str  # error | warning | info
    capability_id: str
    path: str
    message: str


class FatalCheckError(Exception):
    """Exit-code-2 conditions."""


def _v(code: str, severity: str, cap: str, path: str, message: str) -> Violation:
    return Violation(code=code, severity=severity, capability_id=cap, path=path, message=message)


def _load_manifest(repo_root: Path) -> dict[str, Any]:
    path = repo_root / MANIFEST_RELPATH
    if not path.is_file():
        raise FatalCheckError(f"manifest not found: {MANIFEST_RELPATH}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise FatalCheckError(f"manifest unreadable: {exc}") from exc
    if not isinstance(data, dict):
        raise FatalCheckError("manifest top level must be a mapping")
    if data.get("schema_version") not in KNOWN_MANIFEST_SCHEMA_VERSIONS:
        raise FatalCheckError(f"unknown schema_version {data.get('schema_version')!r}")
    return data


def load_manifest_raw(repo_root: Path) -> dict[str, Any]:
    """Public manifest accessor for the projection domain (generator + PR-B
    v2 engine read the SAME loader; unknown schema_version raises)."""
    return _load_manifest(repo_root)


def load_project_set(repo_root: Path) -> tuple[set[str], set[str]]:
    """Return (project set, all skill ids) from the manifest."""
    data = _load_manifest(repo_root)
    caps = data.get("capabilities") or []
    all_ids = {str(c.get("id")) for c in caps if isinstance(c, dict)}
    project = {
        str(c.get("id"))
        for c in caps
        if isinstance(c, dict) and c.get("projection") == "project"
    }
    return project, all_ids


def load_mcp_projection(
    repo_root: Path,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any] | None, set[str]]:
    """Return (project-tier mcp servers, codex.posture or None, never-tier names).

    Tolerant of a missing/malformed `mcp` section (V8 owns that schema, DA070+):
    it degrades to an empty projection so V9/V10 stay meaningful on partial trees.
    """
    data = _load_manifest(repo_root)
    mcp = data.get("mcp")
    servers = mcp.get("servers") if isinstance(mcp, dict) else None
    project_servers: dict[str, dict[str, Any]] = {}
    never_names: set[str] = set()
    if isinstance(servers, dict):
        for name, node in servers.items():
            policy = node.get("projection_policy") if isinstance(node, dict) else None
            if policy == "project":
                project_servers[str(name)] = node if isinstance(node, dict) else {}
            elif policy == "never":
                never_names.add(str(name))
    codex = data.get("codex")
    posture = codex.get("posture") if isinstance(codex, dict) else None
    return project_servers, posture if isinstance(posture, dict) else None, never_names


def check_closure(repo_root: Path, project: set[str], all_ids: set[str]) -> list[Violation]:
    out: list[Violation] = []
    severity = "error" if (repo_root / ".agents").exists() else "warning"
    for name in sorted(project):
        skill_md = repo_root / ".claude" / "skills" / name / "SKILL.md"
        if not skill_md.is_file():
            out.append(
                _v("PJ010", "error", name, str(skill_md.relative_to(repo_root)),
                   "projection: project capability has no on-disk SKILL.md")
            )
            continue
        for ref in sorted(handoff_refs(skill_md.read_text(encoding="utf-8"))):
            if ref.endswith("*"):
                prefix = ref[:-1]
                targets = {s for s in all_ids if s.startswith(prefix)}
            else:
                targets = {ref}
            for target in sorted(targets):
                if target not in project:
                    out.append(
                        _v("PJ011", severity, name,
                           f".claude/skills/{name}/SKILL.md",
                           f"Handoff out-edge '/{target}' is outside the projection"
                           f" whitelist (closure precondition, D-014)")
                    )
    return out


def check_reconcile(repo_root: Path, project: set[str]) -> list[Violation]:
    out: list[Violation] = []
    agents_skills = repo_root / ".agents" / "skills"
    if not (repo_root / ".agents").exists():
        return out  # S0 empty state — vacuous pass
    on_disk = {p.name for p in agents_skills.iterdir() if p.is_dir()} \
        if agents_skills.is_dir() else set()
    for extra in sorted(on_disk - project):
        out.append(
            _v("PJ020", "error", extra, f".agents/skills/{extra}",
               "projected artifact has no manifest 'projection: project' entry"
               " (full reconcile — extra file)")
        )
    for missing in sorted(project - on_disk):
        out.append(
            _v("PJ021", "error", missing, f".agents/skills/{missing}",
               "manifest 'projection: project' entry has no projected artifact"
               " (full reconcile — missing file)")
        )
    return out


def _normalized_body_hash(path: Path) -> str:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    return body_sha256(text)


def check_lock(repo_root: Path, project: set[str]) -> list[Violation]:
    out: list[Violation] = []
    lock_path = repo_root / ".agents.lock.json"
    agents_dir = repo_root / ".agents"
    if not lock_path.is_file() and not agents_dir.exists():
        return out  # both absent — pass (S0)
    if lock_path.is_file() != agents_dir.exists():
        present, absent = (
            (".agents.lock.json", ".agents/") if lock_path.is_file()
            else (".agents/", ".agents.lock.json")
        )
        return [
            _v("PJ030", "error", "", present,
               f"'{present}' exists but '{absent}' does not — lock and artifacts must"
               f" land together (D-012)")
        ]
    try:
        lock: dict[str, Any] = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [_v("PJ031", "error", "", ".agents.lock.json", f"lock unreadable: {exc}")]
    if isinstance(lock, dict) and lock.get("schema_version") is not None:
        # v2 envelope on disk (dormant until PR-C1) — dispatch by lock schema
        # (plan §2.6): PJ030/PJ032/PJ033/PJ034 semantics preserved, entry
        # structure validated by the shared loader. Never guessed from the
        # manifest version.
        return _check_lock_v2(repo_root, project, lock)
    for name in sorted(project):
        artifact = repo_root / ".agents" / "skills" / name / "SKILL.md"
        if not artifact.is_file():
            continue  # reconcile already reports the missing artifact
        expected = lock.get(name)
        actual = _normalized_body_hash(artifact)
        if expected is None:
            out.append(
                _v("PJ032", "error", name, ".agents.lock.json",
                   "projected artifact missing from lock")
            )
        elif str(expected).removeprefix("sha256:") != actual:
            out.append(
                _v("PJ033", "error", name, f".agents/skills/{name}/SKILL.md",
                   "lock hash mismatch — regenerate via agents_sync (do not hand-edit"
                   " generated artifacts, D-012)")
            )
    for name in sorted(set(lock) - project - {CODEX_LOCK_KEY}):
        out.append(
            _v("PJ034", "error", name, ".agents.lock.json",
               "lock entry has no manifest 'projection: project' capability"
               " (the only reserved non-skill key is '.codex/config.toml')")
        )
    return out


def _check_lock_v2(
    repo_root: Path, project: set[str], lock: dict[str, Any]
) -> list[Violation]:
    """v2 envelope branch of check_lock (PJ030-PJ034 under lock schema 2)."""
    from scripts.sdd._common.projection_loader import (
        LockVerificationError,
        canonicalize,
        parse_lock_json,
        verify_lock_v2,
    )

    out: list[Violation] = []
    try:
        # Re-parse with duplicate-key rejection (the tolerant parse above only
        # picked the branch), then verify the closed union.
        verified = verify_lock_v2(
            parse_lock_json(
                (repo_root / ".agents.lock.json").read_text(encoding="utf-8")
            )
        )
    except LockVerificationError as exc:
        return [_v("PJ031", "error", "", ".agents.lock.json", f"lock rejected: {exc}")]
    skills_keys = {
        key: entry
        for key, entry in verified.entries.items()
        if key.startswith(".agents/skills/")
    }
    for name in sorted(project):
        artifact = repo_root / ".agents" / "skills" / name / "SKILL.md"
        if not artifact.is_file():
            continue  # reconcile already reports the missing artifact
        key = f".agents/skills/{name}/SKILL.md"
        entry = skills_keys.get(key)
        if entry is None:
            out.append(
                _v("PJ032", "error", name, ".agents.lock.json",
                   "projected artifact missing from lock entries")
            )
            continue
        digest = hashlib.sha256(
            canonicalize(artifact.read_bytes(), entry.normalization_policy)
        ).hexdigest()
        if digest != entry.output_sha256:
            out.append(
                _v("PJ033", "error", name, key,
                   "lock hash mismatch — regenerate via agents_sync (do not"
                   " hand-edit generated artifacts, D-012)")
            )
    for key, entry in sorted(skills_keys.items()):
        name = key.split("/")[2]
        if entry.entry_kind in ("skill-byte-copy", "skill-translated") \
                and name not in project:
            out.append(
                _v("PJ034", "error", name, ".agents.lock.json",
                   "lock entry has no manifest 'projection: project' capability")
            )
    return out


def check_codex_config(
    repo_root: Path,
    mcp_project: dict[str, dict[str, Any]],
    never_names: set[str],
) -> list[Violation]:
    """S2 MCP projection surface (PJ040-PJ045). Vacuous pass when both the config
    file and the reserved lock key are absent (pre-S2 / fork empty state)."""
    out: list[Violation] = []
    config_path = repo_root / CODEX_CONFIG_RELPATH
    lock_path = repo_root / ".agents.lock.json"
    lock: dict[str, Any] = {}
    if lock_path.is_file():
        try:
            lock = json.loads(lock_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            lock = {}  # PJ031 already reported by check_lock
    # v2 envelope (dormant until PR-C1): the reserved key lives under
    # `entries` and its hash is the entry's output_sha256 over canonicalized
    # bytes; the legacy flat map keeps the v1 body-hash recipe.
    lock_entries: dict[str, Any] = lock
    if isinstance(lock.get("entries"), dict) and lock.get("schema_version") is not None:
        lock_entries = lock["entries"]
    has_key = CODEX_LOCK_KEY in lock_entries

    if not config_path.is_file() and not has_key:
        return out  # empty state — drift enforcement is V11 (agents_sync --surface mcp)

    if config_path.is_file() != has_key:
        present, absent = (
            (str(CODEX_CONFIG_RELPATH), f"lock key '{CODEX_LOCK_KEY}'")
            if config_path.is_file()
            else (f"lock key '{CODEX_LOCK_KEY}'", str(CODEX_CONFIG_RELPATH))
        )
        out.append(
            _v("PJ042", "error", "", ".codex/config.toml",
               f"'{present}' exists but '{absent}' does not — config and reserved lock"
               f" key must land together (D-012)")
        )

    if not config_path.is_file():
        return out

    text = config_path.read_text(encoding="utf-8")
    try:
        parsed = tomllib.loads(text.replace("\r\n", "\n"))
    except tomllib.TOMLDecodeError as exc:
        out.append(
            _v("PJ041", "error", "", ".codex/config.toml",
               f"config.toml is not valid TOML: {exc}")
        )
        return out

    servers = parsed.get("mcp_servers")
    on_disk = set(servers) if isinstance(servers, dict) else set()
    for leaked in sorted(on_disk & never_names):
        out.append(
            _v("PJ044", "error", leaked, ".codex/config.toml",
               "never-tier server projected to Codex — data boundary / prod surface"
               " (D-013; ADR-006/009)")
        )
    expected = set(mcp_project)
    for extra in sorted(on_disk - expected - never_names):
        out.append(
            _v("PJ040", "error", extra, ".codex/config.toml",
               "server has no manifest mcp 'projection_policy: project' entry"
               " (full reconcile — extra server)")
        )
    for missing in sorted(expected - on_disk):
        out.append(
            _v("PJ040", "error", missing, ".codex/config.toml",
               "manifest mcp project-tier server missing from config.toml"
               " (full reconcile — run agents_sync sync)")
        )

    if has_key:
        entry = lock_entries[CODEX_LOCK_KEY]
        if isinstance(entry, dict):  # v2 entry: raw digest over canonical bytes
            actual = hashlib.sha256(
                text.replace("\r\n", "\n").encode("utf-8")
            ).hexdigest()
            expected_hash = str(entry.get("output_sha256"))
        else:  # legacy v1 reserved key: body-hash recipe
            actual = body_sha256(text.replace("\r\n", "\n"))
            expected_hash = str(entry).removeprefix("sha256:")
        if expected_hash != actual:
            out.append(
                _v("PJ043", "error", "", ".codex/config.toml",
                   "reserved lock key hash mismatch — regenerate via agents_sync"
                   " (do not hand-edit generated artifacts, D-012)")
            )

    codex_dir = repo_root / ".codex"
    if codex_dir.is_dir():
        for path in sorted(codex_dir.rglob("*")):
            rel = path.relative_to(repo_root)
            if path.is_file() and rel != CODEX_CONFIG_RELPATH:
                out.append(
                    _v("PJ045", "info", "", rel.as_posix(),
                       "unowned neighbor under .codex/ — preserved by owned-only"
                       " reconcile (ADR-039 D-012 revised; Epic #499 PR-A1"
                       " narrowing: info-only, never gate-affecting)")
                )
    return out


def check_carrier_binding_closure(repo_root: Path) -> list[Violation]:
    """Manifest v2 <-> workflow registry reverse closure (plan §2.1): every
    translated capability's workflow_id exists exactly once in
    development-agent-workflows.yml and the registry record's capability_id
    equals the capability. Dormant on the v1 real tree (no-op)."""
    out: list[Violation] = []
    data = _load_manifest(repo_root)
    if data.get("schema_version") != 2:
        return out
    registry_path = repo_root / "sdd" / "workflows" / "development-agent-workflows.yml"
    if not registry_path.is_file():
        return [
            _v("PJ050", "error", "", "sdd/workflows/development-agent-workflows.yml",
               "manifest v2 requires the workflow registry typed source")
        ]
    # Local import: the loader lives in the D-017 renderer module; V9 reads the
    # same implementation the generator uses (one-implementation rule).
    from scripts.sdd._common.skill_renderer import (
        TranslationError,
        load_workflow_registry,
    )
    try:
        registry = load_workflow_registry(registry_path.read_text(encoding="utf-8"))
    except TranslationError as exc:
        return [
            _v("PJ050", "error", "", "sdd/workflows/development-agent-workflows.yml",
               f"workflow registry rejected: {exc}")
        ]
    for cap in data.get("capabilities") or []:
        if not isinstance(cap, dict) or cap.get("codex_carrier") != "translated":
            continue
        cap_id = str(cap.get("id"))
        binding = cap.get("carrier_binding")
        wid = binding.get("workflow_id") if isinstance(binding, dict) else None
        record = registry.workflows.get(str(wid)) if wid is not None else None
        if record is None:
            out.append(
                _v("PJ051", "error", cap_id, str(MANIFEST_RELPATH),
                   f"carrier_binding.workflow_id {wid!r} not found in the"
                   " workflow registry (fail closed)")
            )
        elif record.capability_id != cap_id:
            out.append(
                _v("PJ052", "error", cap_id, str(MANIFEST_RELPATH),
                   f"workflow {wid!r} reverse capability_id"
                   f" {record.capability_id!r} != {cap_id!r} (closure)")
            )
    translated_ids = {
        str(c.get("id"))
        for c in data.get("capabilities") or []
        if isinstance(c, dict) and c.get("codex_carrier") == "translated"
    }
    for record in registry.workflows.values():
        if record.capability_id not in translated_ids:
            out.append(
                _v("PJ053", "error", record.capability_id,
                   "sdd/workflows/development-agent-workflows.yml",
                   f"workflow {record.workflow_id!r} has no translated manifest"
                   " capability (reverse closure)")
            )
    return out


def run_checks(repo_root: Path) -> list[Violation]:
    project, all_ids = load_project_set(repo_root)
    mcp_project, _posture, never_names = load_mcp_projection(repo_root)
    violations: list[Violation] = []
    violations += check_closure(repo_root, project, all_ids)
    violations += check_reconcile(repo_root, project)
    violations += check_lock(repo_root, project)
    violations += check_codex_config(repo_root, mcp_project, never_names)
    violations += check_carrier_binding_closure(repo_root)
    return violations


def _git_changed_files(repo_root: Path, ref: str) -> list[str]:
    try:
        base = subprocess.run(
            ["git", "merge-base", ref, "HEAD"],
            cwd=repo_root, capture_output=True, text=True, check=True,
        ).stdout.strip()
        diff = subprocess.run(
            ["git", "diff", "--name-only", f"{base}..HEAD"],
            cwd=repo_root, capture_output=True, text=True, check=True,
        )
    except (subprocess.CalledProcessError, OSError) as exc:
        raise FatalCheckError(f"cannot resolve --changed-from ref '{ref}': {exc}") from exc
    return [line.strip() for line in diff.stdout.splitlines() if line.strip()]


def main(argv: list[str] | None = None, repo_root: Path | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog=_SCRIPT_NAME,
        description="V9 projection-domain checker: closure / reconcile / lock (plan §10 v5)",
    )
    parser.add_argument("--all", action="store_true", help="check the full projection domain")
    parser.add_argument(
        "--changed-from", metavar="REF",
        help="check impact of changes since merge-base(REF, HEAD)",
    )
    parser.add_argument("--json", action="store_true", help="structured JSON on stdout")
    parser.add_argument(
        "--fail-on", choices=["error", "warning"], default="error",
        help="threshold severity (default: error)",
    )
    args = parser.parse_args(argv)
    root = repo_root if repo_root is not None else _REPO_ROOT

    if bool(args.all) == bool(args.changed_from):
        parser.print_usage(sys.stderr)
        print(
            f"{_SCRIPT_NAME}: exactly one scope parameter required: --all XOR --changed-from",
            file=sys.stderr,
        )
        return 2

    mode = "all" if args.all else "changed-from"
    base: str | None = None
    try:
        if args.changed_from:
            base = args.changed_from
            changed = _git_changed_files(root, args.changed_from)
            touched = [
                f for f in changed if any(f == p or f.startswith(p) for p in WATCHED_PREFIXES)
            ]
            violations = run_checks(root) if touched else []
        else:
            violations = run_checks(root)
    except FatalCheckError as exc:
        print(f"{_SCRIPT_NAME}: {exc}", file=sys.stderr)
        return 2

    summary = {
        "error": sum(1 for v in violations if v.severity == "error"),
        "warning": sum(1 for v in violations if v.severity == "warning"),
        "info": sum(1 for v in violations if v.severity == "info"),
    }
    if args.json:
        payload = {
            "schema_version": JSON_SCHEMA_VERSION,
            "mode": mode,
            "base": base,
            "violations": [asdict(v) for v in violations],
            "summary": summary,
        }
        print(json.dumps(payload, ensure_ascii=False))
    else:
        for v in violations:
            print(f"[{v.severity.upper()}] {v.code} {v.capability_id or '-'} ({v.path}):"
                  f" {v.message}")
        print(
            f"=== Summary === errors: {summary['error']} / warnings: {summary['warning']}"
            f" / info: {summary['info']} (mode={mode})"
        )

    at_threshold = summary["error"] > 0 or (args.fail_on == "warning" and summary["warning"] > 0)
    return 1 if at_threshold else 0


if __name__ == "__main__":
    sys.exit(main())
