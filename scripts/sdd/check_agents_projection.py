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
   Both absent == pass; exactly one present == FAIL; hash mismatch == FAIL.

Exit codes: 0 / 1 / 2 as in check_development_agent.py.
`main(argv=None, repo_root=None)` — repo_root injectable for tests (#217 pattern).
Read-only; no secrets; no network.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

_SCRIPT_NAME = "check_agents_projection.py"
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.sdd._common.frontmatter import body_sha256  # noqa: E402

MANIFEST_RELPATH = Path("sdd/development-agent.yml")
JSON_SCHEMA_VERSION = 1
KNOWN_MANIFEST_SCHEMA_VERSIONS = {1}

WATCHED_PREFIXES = (
    "sdd/development-agent.yml",
    ".agents/",
    ".agents.lock.json",
    ".codex/",
    ".claude/skills/",
    "scripts/sdd/check_agents_projection.py",
)

_HANDOFF_HEADING = re.compile(r"^(#{2,})\s*Handoff", flags=re.IGNORECASE)
_HEADING = re.compile(r"^(#{2,})\s")
_SKILL_REF = re.compile(r"/(mj-agent-[a-z0-9-]+\*?)")


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


def load_project_set(repo_root: Path) -> tuple[set[str], set[str]]:
    """Return (project set, all skill ids) from the manifest."""
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
    caps = data.get("capabilities") or []
    all_ids = {str(c.get("id")) for c in caps if isinstance(c, dict)}
    project = {
        str(c.get("id"))
        for c in caps
        if isinstance(c, dict) and c.get("projection") == "project"
    }
    return project, all_ids


def _handoff_refs(skill_text: str) -> set[str]:
    """Collect /mj-agent-* refs that appear inside `## Handoff*` sections only."""
    refs: set[str] = set()
    in_handoff = False
    handoff_level = 0
    for line in skill_text.splitlines():
        m = _HEADING.match(line)
        if m:
            hm = _HANDOFF_HEADING.match(line)
            if hm:
                in_handoff = True
                handoff_level = len(hm.group(1))
                continue
            if in_handoff and len(m.group(1)) <= handoff_level:
                in_handoff = False
            continue
        if in_handoff:
            refs.update(_SKILL_REF.findall(line))
    return refs


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
        for ref in sorted(_handoff_refs(skill_md.read_text(encoding="utf-8"))):
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
    for name in sorted(set(lock) - project):
        out.append(
            _v("PJ034", "error", name, ".agents.lock.json",
               "lock entry has no manifest 'projection: project' capability")
        )
    return out


def run_checks(repo_root: Path) -> list[Violation]:
    project, all_ids = load_project_set(repo_root)
    violations: list[Violation] = []
    violations += check_closure(repo_root, project, all_ids)
    violations += check_reconcile(repo_root, project)
    violations += check_lock(repo_root, project)
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
