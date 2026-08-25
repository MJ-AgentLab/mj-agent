"""check_development_agent.py — V8: dual-agent manifest / entry-file / drift checker.

Contract: plans/[PLAN]_dual-agent-compat.md §9 (manifest fields + enums) + §10 (CLI +
rules + exit codes). Declared in sdd/adapters/development-agent.md §Standards; registered
in sdd/gates.md §2 (V8). CI mounts it warning-first (P1); blocking flip is a separate
`ci-blocking-gate-toggle` HITL action.

CLI (own family — deliberately NOT `_common.cli.build_argparser`, per plan §10):
    python scripts/sdd/check_development_agent.py --all [--json] [--fail-on error|warning]
    python scripts/sdd/check_development_agent.py --changed-from <ref> [--json] [...]

Exit codes: 0 = no violation at threshold; 1 = >=1 violation at threshold;
2 = CLI usage / bad ref / manifest unreadable / unknown schema_version.

`main(argv=None, repo_root=None)` — repo_root injectable for tests (#217 pattern).
Read-only: never writes files, never reads secrets, never touches a database.
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

_SCRIPT_NAME = "check_development_agent.py"
_REPO_ROOT = Path(__file__).resolve().parents[2]

MANIFEST_RELPATH = Path("sdd/development-agent.yml")
JSON_SCHEMA_VERSION = 1
# Manifest v2 (Epic #499 plan §2.1) is accepted DORMANT since PR-B: the real tree
# stays schema_version 1 byte-identical until the PR-C1 cutover; unknown versions
# keep exiting 2. The v2 discriminator governs ONLY this manifest — never use it
# to guess the schema of the lock or any other typed source.
KNOWN_MANIFEST_SCHEMA_VERSIONS = {1, 2}

SUPPORT_MODES = {"native", "adapter-backed", "script-ci", "manual", "unsupported"}
# Manifest v2 carrier fields (plan §2.1; validated only when schema_version == 2).
CODEX_CARRIERS = {"none", "byte-copy", "translated"}
CAPABILITY_ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")
APPROVAL_MODES = {"none", "owner-hitl"}
STOP_BEFORE = {"write", "execute", "commit", "push", "pr-create", "merge"}
EVIDENCE_REQUIRED = {"explicit-owner-message", "pr-approval-record"}
ENFORCEMENT = {"native-permission", "adapter", "script", "ci", "manual"}
PROJECTION = {"project", "after-neutralization", "never"}
MCP_POLICIES = {"project", "project-with-adr", "never"}
GROUPS = {"doc", "flow", "git", "infra", "runtime"}

# Canonical 10-enum (policies/ai-agent.md §4). The checker ALSO re-counts the policy
# table / PR template so the list below cannot silently drift alone.
CANONICAL_HITL_10 = (
    "sql-guardrail-relax",
    "runtime-skill-content-change",
    "prompt-version-or-body-change",
    "biz-catalog-sync",
    "mcp-server-trust-posture-change",
    "declared-contract-change",
    "database-migration",
    "secrets-grants-or-prod-config",
    "ci-blocking-gate-toggle",
    "bulk-content-purge-or-migration",
)
# AGENTS.md Git Owner gate (commit/push/pr-create/merge) — the non-enum policy_ref target.
AGENTS_GIT_OWNER_GATE = "agents-git-owner-gate"
VALID_POLICY_REFS = set(CANONICAL_HITL_10) | {AGENTS_GIT_OWNER_GATE}

# D-013: these servers are PERMANENTLY `never` (data boundary / prod surface).
MCP_FORCED_NEVER = {
    "pg-mj-system-biz-dev",
    "pg-mj-system-biz-test-lan",
    "pg-mj-system-biz-test-wan",
    "pg-mj-system-biz-prod-lan",
    "pg-mj-system-biz-prod-wan",
    "ssh-manager",
}

# Nested AGENTS.md entry adapters (program plan §8) + sibling CLAUDE.md import relation.
NESTED_AGENTS_DIRS = ("capabilities", "docker", "src/mj_agent", "tests")

# --changed-from watched prefixes: only these paths can affect V8 verdicts.
WATCHED_PREFIXES = (
    "sdd/development-agent.yml",
    "sdd/adapters/development-agent.md",
    "AGENTS.md",
    "CLAUDE.md",
    "capabilities/AGENTS.md",
    "capabilities/CLAUDE.md",
    "docker/AGENTS.md",
    "docker/CLAUDE.md",
    "src/mj_agent/AGENTS.md",
    "src/mj_agent/CLAUDE.md",
    "tests/AGENTS.md",
    "tests/CLAUDE.md",
    ".claude/skills/",
    ".mcp.json",
    "policies/ai-agent.md",
    ".github/PULL_REQUEST_TEMPLATE.md",
    "scripts/sdd/check_development_agent.py",
)


@dataclass
class Violation:
    code: str
    severity: str  # error | warning | info
    capability_id: str
    path: str
    message: str


class FatalCheckError(Exception):
    """Exit-code-2 conditions: bad ref / unreadable manifest / unknown schema."""


def _v(code: str, severity: str, cap: str, path: str, message: str) -> Violation:
    return Violation(code=code, severity=severity, capability_id=cap, path=path, message=message)


# --------------------------------------------------------------------------- loading


def load_manifest(repo_root: Path) -> dict[str, Any]:
    path = repo_root / MANIFEST_RELPATH
    if not path.is_file():
        raise FatalCheckError(f"manifest not found: {MANIFEST_RELPATH}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise FatalCheckError(f"manifest unreadable: {exc}") from exc
    if not isinstance(data, dict):
        raise FatalCheckError("manifest top level must be a mapping")
    version = data.get("schema_version")
    if version not in KNOWN_MANIFEST_SCHEMA_VERSIONS:
        raise FatalCheckError(
            f"unknown schema_version {version!r}; known: {sorted(KNOWN_MANIFEST_SCHEMA_VERSIONS)}"
        )
    return data


# --------------------------------------------------------------------------- checks


def check_top_level(manifest: dict[str, Any]) -> list[Violation]:
    out: list[Violation] = []
    mpath = str(MANIFEST_RELPATH)
    for field in ("schema_version", "snapshot", "owners", "capabilities"):
        if field not in manifest:
            out.append(_v("DA001", "error", "", mpath, f"missing top-level field '{field}'"))
    if not isinstance(manifest.get("owners"), list) or not manifest.get("owners"):
        out.append(_v("DA001", "error", "", mpath, "'owners' must be a non-empty list"))
    if "owner_agent" in manifest:
        out.append(_v("DA002", "error", "", mpath, "forbidden field 'owner_agent' (§9)"))
    return out


def _check_gates(cap_id: str, side: str, approval: Any) -> list[Violation]:
    out: list[Violation] = []
    mpath = str(MANIFEST_RELPATH)
    if not isinstance(approval, dict) or "mode" not in approval or "gates" not in approval:
        out.append(
            _v("DA010", "error", cap_id, mpath, f"{side}.approval must be {{mode, gates}}")
        )
        return out
    mode = approval["mode"]
    gates = approval["gates"]
    if mode not in APPROVAL_MODES:
        out.append(_v("DA011", "error", cap_id, mpath, f"{side}.approval.mode '{mode}' invalid"))
        return out
    if not isinstance(gates, list):
        out.append(_v("DA010", "error", cap_id, mpath, f"{side}.approval.gates must be a list"))
        return out
    if mode == "none" and gates:
        out.append(
            _v("DA012", "error", cap_id, mpath, f"{side}: approval.mode none requires gates []")
        )
    if mode == "owner-hitl" and not gates:
        out.append(
            _v("DA013", "error", cap_id, mpath, f"{side}: owner-hitl requires >=1 gate")
        )
    for gate in gates:
        if not isinstance(gate, dict):
            out.append(_v("DA014", "error", cap_id, mpath, f"{side}: gate must be a mapping"))
            continue
        for field in ("policy_ref", "trigger", "stop_before", "evidence_required"):
            if field not in gate:
                out.append(
                    _v("DA014", "error", cap_id, mpath, f"{side}: gate missing '{field}'")
                )
        if gate.get("policy_ref") is not None and gate.get("policy_ref") not in VALID_POLICY_REFS:
            out.append(
                _v(
                    "DA015",
                    "error",
                    cap_id,
                    mpath,
                    f"{side}: policy_ref '{gate.get('policy_ref')}' does not resolve to the"
                    f" canonical 10-enum or '{AGENTS_GIT_OWNER_GATE}'",
                )
            )
        if gate.get("stop_before") is not None and gate.get("stop_before") not in STOP_BEFORE:
            out.append(
                _v("DA016", "error", cap_id, mpath,
                   f"{side}: stop_before '{gate.get('stop_before')}' invalid")
            )
        if (
            gate.get("evidence_required") is not None
            and gate.get("evidence_required") not in EVIDENCE_REQUIRED
        ):
            out.append(
                _v("DA017", "error", cap_id, mpath,
                   f"{side}: evidence_required '{gate.get('evidence_required')}' invalid")
            )
    return out


def _check_side(cap: dict[str, Any], side: str) -> list[Violation]:
    out: list[Violation] = []
    cap_id = str(cap.get("id", "<missing-id>"))
    mpath = str(MANIFEST_RELPATH)
    node = cap.get(side)
    if not isinstance(node, dict):
        out.append(_v("DA020", "error", cap_id, mpath, f"missing/invalid '{side}' entry"))
        return out
    mode = node.get("support_mode")
    if mode not in SUPPORT_MODES:
        out.append(_v("DA021", "error", cap_id, mpath, f"{side}.support_mode '{mode}' invalid"))
    enforcement = node.get("enforcement")
    if not isinstance(enforcement, list) or any(e not in ENFORCEMENT for e in enforcement or []):
        out.append(
            _v("DA022", "error", cap_id, mpath, f"{side}.enforcement invalid: {enforcement!r}")
        )
        enforcement = []
    out.extend(_check_gates(cap_id, side, node.get("approval")))
    if mode == "unsupported":
        if cap.get("required") is True:
            out.append(
                _v("DA023", "error", cap_id, mpath,
                   f"required capability has {side}.support_mode unsupported (§9)")
            )
        approval = node.get("approval") or {}
        if approval.get("mode") != "none" or approval.get("gates"):
            out.append(
                _v("DA024", "error", cap_id, mpath,
                   f"{side}: unsupported requires approval none + gates []")
            )
        if enforcement:
            out.append(
                _v("DA024", "error", cap_id, mpath,
                   f"{side}: unsupported requires enforcement []")
            )
    elif mode in SUPPORT_MODES and not enforcement:
        out.append(
            _v("DA025", "error", cap_id, mpath,
               f"{side}: support_mode '{mode}' requires non-empty enforcement")
        )
    if mode == "adapter-backed" and not node.get("adapter_ref"):
        out.append(
            _v("DA026", "error", cap_id, mpath,
               f"{side}: adapter-backed requires adapter_ref pointing at the adapter doc")
        )
    if "owner_agent" in node or "owner_agent" in cap:
        out.append(_v("DA002", "error", cap_id, mpath, "forbidden field 'owner_agent' (§9)"))
    return out


def check_capabilities(manifest: dict[str, Any], repo_root: Path) -> list[Violation]:
    out: list[Violation] = []
    mpath = str(MANIFEST_RELPATH)
    caps = manifest.get("capabilities")
    if not isinstance(caps, list) or not caps:
        return [_v("DA003", "error", "", mpath, "'capabilities' must be a non-empty list")]
    seen: set[str] = set()
    for cap in caps:
        if not isinstance(cap, dict):
            out.append(_v("DA003", "error", "", mpath, "capability entry must be a mapping"))
            continue
        cap_id = str(cap.get("id", "<missing-id>"))
        for field in ("id", "group", "required", "claude", "codex", "evidence"):
            if field not in cap:
                out.append(_v("DA004", "error", cap_id, mpath, f"missing field '{field}'"))
        if cap_id in seen:
            out.append(_v("DA005", "error", cap_id, mpath, "duplicate capability id"))
        seen.add(cap_id)
        if cap.get("group") not in GROUPS:
            out.append(
                _v("DA006", "error", cap_id, mpath, f"group '{cap.get('group')}' invalid")
            )
        if not isinstance(cap.get("required"), bool):
            out.append(_v("DA007", "error", cap_id, mpath, "'required' must be a boolean"))
        if cap.get("projection") not in PROJECTION:
            out.append(
                _v("DA008", "error", cap_id, mpath,
                   f"projection '{cap.get('projection')}' invalid (project /"
                   f" after-neutralization / never)")
            )
        out.extend(_check_side(cap, "claude"))
        out.extend(_check_side(cap, "codex"))
        # file references
        skill_md = repo_root / ".claude" / "skills" / cap_id / "SKILL.md"
        if not skill_md.is_file():
            out.append(
                _v("DA030", "error", cap_id, mpath,
                   f"capability id has no on-disk skill: {skill_md.relative_to(repo_root)}")
            )
        evidence = cap.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            out.append(_v("DA031", "error", cap_id, mpath, "'evidence' must be non-empty list"))
        else:
            for item in evidence:
                if not isinstance(item, str) or not (repo_root / item).exists():
                    severity = "error" if cap.get("required") is True else "warning"
                    out.append(
                        _v("DA032", severity, cap_id, str(item),
                           "evidence reference does not exist on disk")
                    )
        for side in ("claude", "codex"):
            node = cap.get(side)
            if (
                isinstance(node, dict)
                and node.get("adapter_ref")
                and not (repo_root / str(node["adapter_ref"])).is_file()
            ):
                out.append(
                    _v("DA033", "error", cap_id, str(node["adapter_ref"]),
                       f"{side}.adapter_ref does not exist on disk")
                )
    return out


def check_codex_carrier(manifest: dict[str, Any]) -> list[Violation]:
    """Manifest v2 carrier schema (Epic #499 plan §2.1) — DA级 validation so the
    blocking manifest gate is not blind to the new fields.

    v1 manifests must NOT carry the v2-only fields (closed v1 schema); v2
    manifests must carry `codex_carrier` on EVERY capability (closed v2 schema —
    absence is not an implicit `none`). `carrier_binding` exists exactly for
    `translated` and holds exactly one key, `workflow_id` (its registry closure —
    exists exactly once + reverse capability match — is V9's job, plan §2.1).
    Invariants checked here: (1) codex_carrier != none <=> projection == project;
    (2) required == true => codex_carrier != none. The output path is NOT a
    manifest field: it derives from the capability id as
    `.agents/skills/<id>/SKILL.md`, so the id must satisfy the id syntax and be
    casefold-unique (one owner per derived path on any filesystem).
    """
    out: list[Violation] = []
    mpath = str(MANIFEST_RELPATH)
    version = manifest.get("schema_version")
    caps = [c for c in manifest.get("capabilities") or [] if isinstance(c, dict)]

    if version == 1:
        for c in caps:
            cap_id = str(c.get("id", "<missing-id>"))
            for field in ("codex_carrier", "carrier_binding"):
                if field in c:
                    out.append(
                        _v("DA090", "error", cap_id, mpath,
                           f"'{field}' is a manifest v2 field; schema_version 1 does"
                           " not define it (closed schema — bump schema_version via"
                           " the PR-C1 cutover, do not mix versions)")
                    )
        return out

    casefolded: dict[str, str] = {}
    for c in caps:
        cap_id = str(c.get("id", "<missing-id>"))
        carrier = c.get("codex_carrier")
        if carrier not in CODEX_CARRIERS:
            out.append(
                _v("DA091", "error", cap_id, mpath,
                   f"codex_carrier {carrier!r} invalid — v2 requires an explicit"
                   f" value from {sorted(CODEX_CARRIERS)} on every capability")
            )
            carrier = None
        binding = c.get("carrier_binding")
        if carrier == "translated":
            if not isinstance(binding, dict) or set(binding) != {"workflow_id"}:
                out.append(
                    _v("DA092", "error", cap_id, mpath,
                       "translated carrier requires carrier_binding with exactly"
                       " one key: workflow_id")
                )
            elif not isinstance(binding.get("workflow_id"), str) or not binding["workflow_id"]:
                out.append(
                    _v("DA092", "error", cap_id, mpath,
                       "carrier_binding.workflow_id must be a non-empty string")
                )
        elif binding is not None or "carrier_binding" in c:
            out.append(
                _v("DA093", "error", cap_id, mpath,
                   f"carrier_binding is only defined for codex_carrier: translated"
                   f" (found on {carrier!r})")
            )
        projection = c.get("projection")
        if carrier is not None and (carrier != "none") != (projection == "project"):
            out.append(
                _v("DA094", "error", cap_id, mpath,
                   f"invariant 1 violated: codex_carrier {carrier!r} with projection"
                   f" {projection!r} — codex_carrier != none <=> projection: project")
            )
        if c.get("required") is True and carrier == "none":
            out.append(
                _v("DA095", "error", cap_id, mpath,
                   "invariant 2 violated: required capability must have a Codex"
                   " carrier (codex_carrier != none)")
            )
        if CAPABILITY_ID.fullmatch(cap_id) is None:
            out.append(
                _v("DA096", "error", cap_id, mpath,
                   "capability id does not satisfy the id syntax"
                   " ^[a-z0-9][a-z0-9-]*$ — the derived artifact path"
                   " .agents/skills/<id>/SKILL.md must stay inside its root")
            )
        elif cap_id.casefold() in casefolded:
            out.append(
                _v("DA096", "error", cap_id, mpath,
                   f"capability id casefold-collides with"
                   f" '{casefolded[cap_id.casefold()]}' — one owner per derived"
                   " artifact path on any filesystem")
            )
        else:
            casefolded[cap_id.casefold()] = cap_id
    return out


def check_agents_entries(repo_root: Path) -> list[Violation]:
    """Root + nested AGENTS.md existence and sibling CLAUDE.md @AGENTS.md import."""
    out: list[Violation] = []
    pairs = [("", "AGENTS.md", "CLAUDE.md")] + [
        (d, f"{d}/AGENTS.md", f"{d}/CLAUDE.md") for d in NESTED_AGENTS_DIRS
    ]
    for _, agents_rel, claude_rel in pairs:
        agents_path = repo_root / agents_rel
        claude_path = repo_root / claude_rel
        if not agents_path.is_file():
            out.append(_v("DA040", "error", "", agents_rel, "AGENTS.md entry file missing"))
        if not claude_path.is_file():
            out.append(_v("DA041", "error", "", claude_rel, "sibling CLAUDE.md missing"))
            continue
        text = claude_path.read_text(encoding="utf-8")
        if not re.search(r"^@AGENTS\.md\s*$", text, flags=re.MULTILINE):
            out.append(
                _v("DA042", "error", "", claude_rel,
                   "sibling CLAUDE.md lacks same-layer '@AGENTS.md' import line")
            )
    return out


def check_canonical_count(repo_root: Path) -> list[Violation]:
    """Guard the canonical-10 approval vocabulary against re-drift (12-vs-10 incident)."""
    out: list[Violation] = []
    policy = repo_root / "policies" / "ai-agent.md"
    if not policy.is_file():
        return [_v("DA050", "error", "", "policies/ai-agent.md", "policy file missing")]
    text = policy.read_text(encoding="utf-8")
    for name in CANONICAL_HITL_10:
        if name not in text:
            out.append(
                _v("DA051", "error", "", "policies/ai-agent.md",
                   f"canonical enum '{name}' not found in §4 policy text")
            )
    section = re.search(r"## §4 .*?(?=\n## |\Z)", text, flags=re.DOTALL)
    if section is not None:
        rows = re.findall(r"^\|\s*`([a-z0-9-]+)`", section.group(0), flags=re.MULTILINE)
        if rows and len(rows) != len(CANONICAL_HITL_10):
            out.append(
                _v("DA051", "error", "", "policies/ai-agent.md",
                   f"§4 table has {len(rows)} enum rows; canonical is"
                   f" {len(CANONICAL_HITL_10)} (D-010/D-017)")
            )
    template = repo_root / ".github" / "PULL_REQUEST_TEMPLATE.md"
    if template.is_file():
        t_text = template.read_text(encoding="utf-8")
        section = re.search(
            r"## HITL Trigger Inventory.*?(?=\n## |\Z)", t_text, flags=re.DOTALL
        )
        if section is None:
            out.append(
                _v("DA052", "error", "", ".github/PULL_REQUEST_TEMPLATE.md",
                   "HITL Trigger Inventory section missing")
            )
        else:
            boxes = re.findall(r"^- \[ \] ([a-z0-9-]+)", section.group(0), flags=re.MULTILINE)
            if len(boxes) != len(CANONICAL_HITL_10):
                out.append(
                    _v("DA053", "error", "", ".github/PULL_REQUEST_TEMPLATE.md",
                       f"HITL Trigger Inventory has {len(boxes)} rows; canonical is"
                       f" {len(CANONICAL_HITL_10)}")
                )
            for name in CANONICAL_HITL_10:
                if name not in boxes:
                    out.append(
                        _v("DA053", "error", "", ".github/PULL_REQUEST_TEMPLATE.md",
                           f"canonical enum '{name}' missing from HITL Trigger Inventory")
                    )
    else:
        out.append(
            _v("DA052", "error", "", ".github/PULL_REQUEST_TEMPLATE.md", "PR template missing")
        )
    return out


def check_stats(manifest: dict[str, Any], repo_root: Path) -> list[Violation]:
    """Counts derive from the manifest — on-disk mismatch = error, index drift = warning."""
    out: list[Violation] = []
    caps = manifest.get("capabilities") or []
    manifest_ids = {str(c.get("id")) for c in caps if isinstance(c, dict)}
    skills_dir = repo_root / ".claude" / "skills"
    on_disk = {
        p.parent.name for p in skills_dir.glob("*/SKILL.md")
    } if skills_dir.is_dir() else set()
    missing = sorted(on_disk - manifest_ids)
    extra = sorted(manifest_ids - on_disk)
    if missing:
        out.append(
            _v("DA060", "error", "", str(MANIFEST_RELPATH),
               f"on-disk skills missing from manifest: {', '.join(missing)}")
        )
    if extra:
        out.append(
            _v("DA060", "error", "", str(MANIFEST_RELPATH),
               f"manifest capabilities with no on-disk skill: {', '.join(extra)}")
        )
    index = skills_dir / "SKILL_INDEX.md"
    if index.is_file():
        m = re.search(r"\*\*(\d+)\*\*", index.read_text(encoding="utf-8"))
        if m and int(m.group(1)) != len(on_disk):
            out.append(
                _v("DA061", "warning", "", ".claude/skills/SKILL_INDEX.md",
                   f"SKILL_INDEX declares {m.group(1)} skills; on-disk count is {len(on_disk)}"
                   f" (stats drift — counts derive from the manifest)")
            )
    return out


def check_mcp_section(manifest: dict[str, Any], repo_root: Path) -> list[Violation]:
    out: list[Violation] = []
    mpath = str(MANIFEST_RELPATH)
    mcp = manifest.get("mcp")
    if not isinstance(mcp, dict) or not isinstance(mcp.get("servers"), dict):
        return [_v("DA070", "error", "", mpath, "mcp section with 'servers' mapping required")]
    if mcp.get("default_projection_policy") != "never":
        out.append(
            _v("DA071", "warning", "", mpath,
               "mcp.default_projection_policy should be 'never' (D-013 default)")
        )
    servers: dict[str, Any] = mcp["servers"]
    for name, node in servers.items():
        policy = node.get("projection_policy") if isinstance(node, dict) else None
        if policy not in MCP_POLICIES:
            out.append(
                _v("DA072", "error", "", mpath,
                   f"mcp server '{name}': projection_policy '{policy}' invalid")
            )
        if name in MCP_FORCED_NEVER and policy != "never":
            out.append(
                _v("DA073", "error", "", mpath,
                   f"mcp server '{name}' must be 'never' — data boundary / prod surface"
                   f" (D-013; ADR-006/009)")
            )
    mcp_json = repo_root / ".mcp.json"
    if mcp_json.is_file():
        try:
            live = set(json.loads(mcp_json.read_text(encoding="utf-8")).get("mcpServers", {}))
        except (OSError, json.JSONDecodeError):
            live = set()
            out.append(_v("DA074", "warning", "", ".mcp.json", "could not parse .mcp.json"))
        unknown = sorted(set(servers) - live)
        uncovered = sorted(live - set(servers))
        if unknown:
            out.append(
                _v("DA075", "error", "", mpath,
                   f"manifest mcp servers not in .mcp.json: {', '.join(unknown)}")
            )
        if uncovered:
            out.append(
                _v("DA076", "warning", "", mpath,
                   f".mcp.json servers missing a manifest tier (default never applies):"
                   f" {', '.join(uncovered)}")
            )
    return out


def check_codex_posture(manifest: dict[str, Any]) -> list[Violation]:
    out: list[Violation] = []
    mpath = str(MANIFEST_RELPATH)
    posture = (manifest.get("codex") or {}).get("posture") if isinstance(
        manifest.get("codex"), dict) else None
    if not isinstance(posture, dict):
        return [_v("DA080", "error", "", mpath, "codex.posture handwritten section required")]
    for key, typ in (
        ("approval_policy", str),
        ("sandbox_mode", str),
        ("project_doc_max_bytes", int),
    ):
        if not isinstance(posture.get(key), typ):
            out.append(
                _v("DA081", "error", "", mpath,
                   f"codex.posture.{key} missing or not {typ.__name__}")
            )
    return out


# --------------------------------------------------------------------------- driver


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


def run_checks(repo_root: Path) -> list[Violation]:
    manifest = load_manifest(repo_root)
    violations: list[Violation] = []
    violations += check_top_level(manifest)
    violations += check_capabilities(manifest, repo_root)
    violations += check_codex_carrier(manifest)
    violations += check_agents_entries(repo_root)
    violations += check_canonical_count(repo_root)
    violations += check_stats(manifest, repo_root)
    violations += check_mcp_section(manifest, repo_root)
    violations += check_codex_posture(manifest)
    return violations


def _build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=_SCRIPT_NAME,
        description="V8 dual-agent manifest checker (plan §10 interface)",
    )
    parser.add_argument("--all", action="store_true", help="check the full manifest + refs")
    parser.add_argument(
        "--changed-from", metavar="REF",
        help="check impact of changes since merge-base(REF, HEAD)",
    )
    parser.add_argument("--json", action="store_true", help="structured JSON on stdout")
    parser.add_argument(
        "--fail-on", choices=["error", "warning"], default="error",
        help="threshold severity (default: error)",
    )
    return parser


def main(argv: list[str] | None = None, repo_root: Path | None = None) -> int:
    parser = _build_argparser()
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
