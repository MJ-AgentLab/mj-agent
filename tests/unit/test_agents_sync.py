"""Unit tests for agents_sync.py (scoped projection generator, emitters A+B).

Covers: sync artifact/README/lock generation + idempotency, --check drift tri-state
(clean / hand-edited artifact / source edited without sync) with prescribed-action
text, full-reconcile negatives (orphan projection dirs, stray files), cross-EOL
stability (F10: Windows CRLF checkout vs ubuntu LF checkout must agree on lock
hashes and --check verdicts), --adopt reverse-feed, mode exclusivity / exit codes,
V9 (check_agents_projection) integration on generated artifacts, and real-tree
pins (committed artifacts stay in sync).

Emitter B (S2 #330): .codex/config.toml golden rendering (three project-tier
servers, serena --context transform, env ${VAR} -> env_vars by-name whitelist),
fail-closed negatives (literal env / unknown field / missing .mcp.json entry),
--surface scoping (mcp drift must never redden the skills gate and vice versa),
reserved lock key + V9 PJ040-PJ045, and the V11 real-tree pin.

Fixtures reuse `make_repo` / `cap` from test_sdd_development_agent and inject
tmp_path via `main(argv, repo_root=...)` (#217 pattern) — never mutate the live tree.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from scripts.sdd import run_offline_pytest as offline_runner
from scripts.sdd.agents_sync import (
    CODEX_CONFIG_HEADER,
    PRESCRIBED_ACTION,
    PRESCRIBED_ACTION_MCP,
)
from scripts.sdd.agents_sync import main as sync_main
from scripts.sdd.check_agents_projection import CODEX_LOCK_KEY
from scripts.sdd.check_agents_projection import main as v9_main
from scripts.sdd.check_test_offline_boundary import Violation as OfflineViolation
from scripts.sdd.check_test_offline_boundary import _read as offline_boundary_read
from scripts.sdd.check_test_offline_boundary import check as offline_boundary_check
from scripts.sdd.check_test_offline_boundary import main as offline_boundary_main

from tests.unit.test_sdd_development_agent import cap, make_repo

REPO_ROOT = Path(__file__).resolve().parents[2]

PROJECT_SKILLS = ("mj-agent-alpha", "mj-agent-beta")


def make_projection_repo(tmp_path: Path, *, bodies: dict[str, str] | None = None) -> Path:
    caps = [cap(name, projection="project") for name in PROJECT_SKILLS]
    caps.append(cap("mj-agent-gamma", projection="never"))
    return make_repo(tmp_path, caps, skill_bodies=bodies)


def _snapshot(root: Path) -> dict[str, bytes]:
    files = [
        root / ".agents.lock.json",
        root / ".codex" / "config.toml",
        *sorted((root / ".agents").rglob("*")),
    ]
    return {str(p): p.read_bytes() for p in files if p.is_file()}


# ------------------------------------------------------------------ sync


def test_sync_creates_artifacts_readme_lock(tmp_path: Path) -> None:
    root = make_projection_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    for name in PROJECT_SKILLS:
        src = root / ".claude" / "skills" / name / "SKILL.md"
        dst = root / ".agents" / "skills" / name / "SKILL.md"
        assert dst.read_bytes() == src.read_bytes()  # byte-identical projection
    assert not (root / ".agents" / "skills" / "mj-agent-gamma").exists()  # never tier
    assert "GENERATED" in (root / ".agents" / "README.md").read_text(encoding="utf-8")
    lock = json.loads((root / ".agents.lock.json").read_text(encoding="utf-8"))
    # default fixture has one project-tier mcp server -> reserved key present too
    assert set(lock) == set(PROJECT_SKILLS) | {CODEX_LOCK_KEY}
    assert all(v.startswith("sha256:") for v in lock.values())
    # one sorted entry per line localizes merge conflicts (plan §8) — pin BOTH
    # properties: per-line entries (a compact-JSON regression collapses them to
    # one line) AND sortedness
    lines = (root / ".agents.lock.json").read_text(encoding="utf-8").splitlines()
    entry_lines = [ln for ln in lines if '"mj-agent-' in ln]
    assert len(entry_lines) == len(PROJECT_SKILLS)
    assert entry_lines == sorted(entry_lines)


def test_sync_is_idempotent(tmp_path: Path, capsys: Any) -> None:
    root = make_projection_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    before = _snapshot(root)
    assert sync_main(["sync"], repo_root=root) == 0
    assert "up to date" in capsys.readouterr().out
    assert _snapshot(root) == before


def test_sync_reconciles_orphans_and_strays(tmp_path: Path) -> None:
    root = make_projection_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    orphan = root / ".agents" / "skills" / "mj-agent-orphan" / "SKILL.md"
    orphan.parent.mkdir(parents=True)
    orphan.write_text("rogue\n", encoding="utf-8")
    (root / ".agents" / "stray.txt").write_text("stray\n", encoding="utf-8")
    assert sync_main(["sync"], repo_root=root) == 0
    assert not orphan.parent.exists()
    assert not (root / ".agents" / "stray.txt").exists()
    assert sync_main(["--check"], repo_root=root) == 0


def test_sync_missing_source_exits_2(tmp_path: Path, capsys: Any) -> None:
    root = make_projection_repo(tmp_path)
    (root / ".claude" / "skills" / "mj-agent-alpha" / "SKILL.md").unlink()
    assert sync_main(["sync"], repo_root=root) == 2
    assert "source missing" in capsys.readouterr().err


# ------------------------------------------------------------------ --check tri-state


def test_check_clean_after_sync(tmp_path: Path, capsys: Any) -> None:
    root = make_projection_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    assert sync_main(["--check"], repo_root=root) == 0
    assert "OK: projection in sync" in capsys.readouterr().out


def test_check_hand_edited_artifact_red_with_prescribed_action(
    tmp_path: Path, capsys: Any
) -> None:
    root = make_projection_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    artifact = root / ".agents" / "skills" / "mj-agent-alpha" / "SKILL.md"
    artifact.write_text(
        artifact.read_text(encoding="utf-8") + "\nrogue edit\n", encoding="utf-8"
    )
    assert sync_main(["--check"], repo_root=root) == 1
    out = capsys.readouterr().out
    assert "artifact != source" in out
    assert PRESCRIBED_ACTION in out
    # independently pin the plan §12 content elements (NOT via the constant, so a
    # trimmed/reworded PRESCRIBED_ACTION cannot silently drop them):
    assert "edit the SOURCE" in out
    assert "agents_sync.py sync" in out
    assert "--adopt" in out  # reverse-feed path
    assert "merge the source" in out and "3-way-merge" in out  # merge-conflict rule


def test_check_source_edited_without_sync_red(tmp_path: Path, capsys: Any) -> None:
    root = make_projection_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    src = root / ".claude" / "skills" / "mj-agent-beta" / "SKILL.md"
    src.write_text(src.read_text(encoding="utf-8") + "\nnew source line\n", encoding="utf-8")
    assert sync_main(["--check"], repo_root=root) == 1
    assert "artifact != source" in capsys.readouterr().out


def test_check_extra_file_and_missing_lock_red(tmp_path: Path, capsys: Any) -> None:
    root = make_projection_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    (root / ".agents" / "skills" / "mj-agent-alpha" / "extra.txt").write_text(
        "x\n", encoding="utf-8"
    )
    (root / ".agents.lock.json").unlink()
    assert sync_main(["--check"], repo_root=root) == 1
    out = capsys.readouterr().out
    assert "unexpected file" in out
    assert "missing .agents.lock.json" in out


def test_check_red_when_agents_tree_absent(tmp_path: Path, capsys: Any) -> None:
    """Fresh pre-sync tree (non-empty project set, no .agents/) must be drift, not
    a vacuous pass — unlike V9's S0 empty-state rule, V10 requires artifacts."""
    root = make_projection_repo(tmp_path)
    assert sync_main(["--check"], repo_root=root) == 1
    out = capsys.readouterr().out
    assert "missing artifact" in out
    assert "missing .agents/README.md" in out
    assert "missing .agents.lock.json" in out


def test_check_red_when_artifacts_deleted_but_lock_remains(
    tmp_path: Path, capsys: Any
) -> None:
    """PJ030 analog: lock present while the .agents/ tree is gone must go red."""
    root = make_projection_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    shutil.rmtree(root / ".agents")
    assert sync_main(["--check"], repo_root=root) == 1
    assert "missing artifact" in capsys.readouterr().out


def test_sync_replaces_stray_file_squatting_on_skill_dir_path(tmp_path: Path) -> None:
    """--check prescribes 'run sync' for a mangled tree; sync must reconcile a stray
    FILE at .agents/skills/<name> instead of crashing on mkdir (review finding #2)."""
    root = make_projection_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    skill_dir = root / ".agents" / "skills" / "mj-agent-alpha"
    shutil.rmtree(skill_dir)
    skill_dir.write_text("stray\n", encoding="utf-8")
    assert sync_main(["sync"], repo_root=root) == 0
    assert (skill_dir / "SKILL.md").is_file()
    assert sync_main(["--check"], repo_root=root) == 0


# ------------------------------------------------------------------ F10 cross-EOL


def test_cross_eol_lock_hash_and_check_stable(tmp_path: Path) -> None:
    """Same logical content as CRLF (Windows checkout) vs LF (ubuntu checkout):
    lock hashes must be identical and --check must stay green either way."""
    body = "# mj-agent-alpha\n\nbody line\n"
    fm = "---\nname: mj-agent-alpha\ndescription: fixture\n---\n\n"
    root_lf = make_projection_repo(tmp_path / "lf")
    root_crlf = make_projection_repo(tmp_path / "crlf")
    (root_lf / ".claude" / "skills" / "mj-agent-alpha" / "SKILL.md").write_bytes(
        (fm + body).encode("utf-8")
    )
    (root_crlf / ".claude" / "skills" / "mj-agent-alpha" / "SKILL.md").write_bytes(
        (fm + body).replace("\n", "\r\n").encode("utf-8")
    )
    assert sync_main(["sync"], repo_root=root_lf) == 0
    assert sync_main(["sync"], repo_root=root_crlf) == 0
    lock_lf = json.loads((root_lf / ".agents.lock.json").read_text(encoding="utf-8"))
    lock_crlf = json.loads((root_crlf / ".agents.lock.json").read_text(encoding="utf-8"))
    assert lock_lf["mj-agent-alpha"] == lock_crlf["mj-agent-alpha"]
    # simulate git flipping the artifact's checkout EOL under an unchanged source
    artifact = root_lf / ".agents" / "skills" / "mj-agent-alpha" / "SKILL.md"
    artifact.write_bytes(artifact.read_bytes().replace(b"\n", b"\r\n"))
    assert sync_main(["--check"], repo_root=root_lf) == 0


# ------------------------------------------------------------------ --adopt


def test_adopt_reverse_feeds_source_and_realigns(tmp_path: Path, capsys: Any) -> None:
    root = make_projection_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    artifact = root / ".agents" / "skills" / "mj-agent-alpha" / "SKILL.md"
    edited = artifact.read_text(encoding="utf-8") + "\nadopted line\n"
    artifact.write_text(edited, encoding="utf-8")
    assert sync_main(["--check"], repo_root=root) == 1
    capsys.readouterr()
    assert sync_main(["--adopt", "mj-agent-alpha"], repo_root=root) == 0
    out = capsys.readouterr().out
    assert "adopt .claude/skills/mj-agent-alpha/SKILL.md <- artifact" in out
    assert "Owner" in out  # HITL reminder
    src = root / ".claude" / "skills" / "mj-agent-alpha" / "SKILL.md"
    assert src.read_text(encoding="utf-8") == edited
    assert sync_main(["--check"], repo_root=root) == 0  # lock realigned by adopt's sync


def test_adopt_unknown_or_non_project_target_exits_2(tmp_path: Path, capsys: Any) -> None:
    root = make_projection_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    assert sync_main(["--adopt", "mj-agent-gamma"], repo_root=root) == 2  # never tier
    assert "not a manifest" in capsys.readouterr().err


def test_adopt_missing_artifact_exits_2(tmp_path: Path, capsys: Any) -> None:
    root = make_projection_repo(tmp_path)  # pre-sync: no artifacts yet
    assert sync_main(["--adopt", "mj-agent-alpha"], repo_root=root) == 2
    assert "artifact missing" in capsys.readouterr().err


def test_adopt_restores_deleted_source(tmp_path: Path) -> None:
    """Recovery path (review finding #1): a deleted source is restored from its
    committed artifact instead of crashing with FileNotFoundError."""
    root = make_projection_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    src = root / ".claude" / "skills" / "mj-agent-alpha" / "SKILL.md"
    expected = src.read_bytes()
    src.unlink()
    assert sync_main(["--adopt", "mj-agent-alpha"], repo_root=root) == 0
    assert src.read_bytes() == expected
    assert sync_main(["--check"], repo_root=root) == 0


# ------------------------------------------------------------------ CLI contract


def test_mode_exclusivity_exits_2(tmp_path: Path) -> None:
    root = make_projection_repo(tmp_path)
    assert sync_main([], repo_root=root) == 2
    assert sync_main(["sync", "--check"], repo_root=root) == 2
    assert sync_main(["sync", "--adopt", "mj-agent-alpha"], repo_root=root) == 2


# ------------------------------------------------------------------ V9 integration


def test_v9_accepts_generated_artifacts_and_flags_hand_edits(tmp_path: Path) -> None:
    root = make_projection_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    assert v9_main(["--all"], repo_root=root) == 0  # closure/reconcile/lock all green
    artifact = root / ".agents" / "skills" / "mj-agent-beta" / "SKILL.md"
    artifact.write_text(
        artifact.read_text(encoding="utf-8") + "\nrogue\n", encoding="utf-8"
    )
    assert v9_main(["--all"], repo_root=root) == 1  # PJ033 lock hash mismatch


# ------------------------------------------------------------------ emitter B (S2 #330)

MCP_TIERS = {
    "github": {"projection_policy": "project"},
    "playwright": {"projection_policy": "project"},
    "serena": {"projection_policy": "project", "transform": "context rewrite"},
    "pg-mj-system-biz-dev": {"projection_policy": "never"},
    "ssh-manager": {"projection_policy": "never"},
}

MCP_JSON = {
    "github": {
        "command": "cmd",
        "args": ["/c", "npx", "-y", "@modelcontextprotocol/server-github"],
        "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_PERSONAL_ACCESS_TOKEN}"},
    },
    "playwright": {
        "type": "stdio",
        "command": "cmd",
        "args": ["/c", "npx", "-y", "@playwright/mcp@latest"],
    },
    "serena": {
        "type": "stdio",
        "command": "cmd",
        "args": [
            "/c", "uv", "tool", "run",
            "--from", "git+https://github.com/oraios/serena",
            "serena", "start-mcp-server",
            "--context", "claude-code",
            "--enable-web-dashboard", "false",
            "--project-from-cwd",
        ],
    },
    # never tier: literal env values here must be irrelevant (never projected)
    "pg-mj-system-biz-dev": {"command": "cmd", "args": ["/c", "x"]},
    "ssh-manager": {"command": "cmd", "env": {"SSH_SERVER_CLOUD_HOST": "1.2.3.4"}},
}

CODEX_GOLDEN = (
    CODEX_CONFIG_HEADER
    + "\n"
    + 'approval_policy = "on-request"\n'
    + 'sandbox_mode = "workspace-write"\n'
    + "project_doc_max_bytes = 65536\n"
    + "\n"
    + "[mcp_servers.github]\n"
    + 'command = "cmd"\n'
    + 'args = ["/c", "npx", "-y", "@modelcontextprotocol/server-github"]\n'
    + 'env_vars = ["GITHUB_PERSONAL_ACCESS_TOKEN"]\n'
    + "\n"
    + "[mcp_servers.playwright]\n"
    + 'command = "cmd"\n'
    + 'args = ["/c", "npx", "-y", "@playwright/mcp@latest"]\n'
    + "\n"
    + "[mcp_servers.serena]\n"
    + 'command = "cmd"\n'
    + 'args = ["/c", "uv", "tool", "run", "--from", "git+https://github.com/oraios/serena",'
    + ' "serena", "start-mcp-server", "--context", "codex", "--enable-web-dashboard",'
    + ' "false", "--project-from-cwd"]\n'
)


def make_mcp_repo(
    tmp_path: Path,
    *,
    mcp_servers: dict[str, Any] | None = None,
    mcp_json_servers: dict[str, Any] | None = None,
) -> Path:
    caps = [cap(name, projection="project") for name in PROJECT_SKILLS]
    return make_repo(
        tmp_path,
        caps,
        mcp_servers=mcp_servers if mcp_servers is not None else dict(MCP_TIERS),
        mcp_json_servers=(
            mcp_json_servers if mcp_json_servers is not None else json.loads(json.dumps(MCP_JSON))
        ),
    )


def test_sync_emits_codex_config_golden(tmp_path: Path) -> None:
    """Golden text: three project-tier servers sorted, serena --context transformed,
    github env ${VAR} projected as an env_vars NAME whitelist, posture transcribed.
    Never-tier servers (biz/ssh) must not appear."""
    root = make_mcp_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    config = root / ".codex" / "config.toml"
    assert config.read_text(encoding="utf-8") == CODEX_GOLDEN
    assert "pg-mj-system-biz" not in CODEX_GOLDEN
    assert "ssh-manager" not in CODEX_GOLDEN
    lock = json.loads((root / ".agents.lock.json").read_text(encoding="utf-8"))
    assert lock[CODEX_LOCK_KEY].startswith("sha256:")
    assert sync_main(["--check"], repo_root=root) == 0


def test_sync_codex_config_idempotent_and_reconciles_strays(tmp_path: Path, capsys: Any) -> None:
    root = make_mcp_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    before = _snapshot(root)
    assert sync_main(["sync"], repo_root=root) == 0
    assert "up to date" in capsys.readouterr().out
    assert _snapshot(root) == before
    (root / ".codex" / "stray.toml").write_text("x = 1\n", encoding="utf-8")
    (root / ".codex" / "sub").mkdir()
    assert sync_main(["sync"], repo_root=root) == 0
    assert not (root / ".codex" / "stray.toml").exists()
    assert not (root / ".codex" / "sub").exists()
    assert sync_main(["--check"], repo_root=root) == 0


def test_literal_env_value_exits_2(tmp_path: Path, capsys: Any) -> None:
    """Fail-closed: a non-${VAR} env value (literal or ${VAR:-default}) must never
    be projected."""
    servers = json.loads(json.dumps(MCP_JSON))
    servers["github"]["env"]["GITHUB_PERSONAL_ACCESS_TOKEN"] = "ghp_literal_secret"
    root = make_mcp_repo(tmp_path, mcp_json_servers=servers)
    assert sync_main(["sync"], repo_root=root) == 2
    assert "not a pure" in capsys.readouterr().err
    servers["github"]["env"]["GITHUB_PERSONAL_ACCESS_TOKEN"] = "${VAR:-default}"
    root2 = make_mcp_repo(tmp_path / "b", mcp_json_servers=servers)
    assert sync_main(["sync"], repo_root=root2) == 2


def test_unknown_server_field_exits_2(tmp_path: Path, capsys: Any) -> None:
    servers = json.loads(json.dumps(MCP_JSON))
    servers["github"]["cwd"] = "somewhere"
    root = make_mcp_repo(tmp_path, mcp_json_servers=servers)
    assert sync_main(["sync"], repo_root=root) == 2
    assert "does not understand" in capsys.readouterr().err


def test_non_stdio_type_exits_2(tmp_path: Path, capsys: Any) -> None:
    """Fail-closed (#330-5): a non-stdio server type must not be silently projected
    as an implicit-stdio entry."""
    servers = json.loads(json.dumps(MCP_JSON))
    servers["playwright"]["type"] = "sse"
    root = make_mcp_repo(tmp_path, mcp_json_servers=servers)
    assert sync_main(["sync"], repo_root=root) == 2
    assert "only stdio" in capsys.readouterr().err


def test_substitution_or_credential_shape_in_args_exits_2(tmp_path: Path, capsys: Any) -> None:
    """Fail-closed (#330-0): args are projected verbatim, so ${VAR}/${VAR:-default}
    (Codex does not interpolate; defaults embed literals) and URL userinfo
    credential shapes must all refuse."""
    for bad_arg, needle in (
        ("${MJ_AGENT_PG_MEMORY_DEV_URL}", "substitution"),
        ("${X:-postgresql://u:hunter2@h:5432/db}", "substitution"),
        ("postgresql://analyst:hunter2@h:5432/db", "userinfo"),
    ):
        servers = json.loads(json.dumps(MCP_JSON))
        servers["playwright"]["args"] = ["/c", bad_arg]
        root = make_mcp_repo(tmp_path / needle[:4] / bad_arg[:4].replace("$", "s").replace("{", "b").replace(":", "c").replace("/", "d"), mcp_json_servers=servers)
        assert sync_main(["sync"], repo_root=root) == 2
        assert needle in capsys.readouterr().err


def test_context_transform_gated_on_manifest_transform_field(tmp_path: Path) -> None:
    """#330-6: the --context rewrite fires only for servers whose manifest node has
    a `transform` field — an untagged server keeps its args untouched."""
    tiers = json.loads(json.dumps(MCP_TIERS))
    del tiers["serena"]["transform"]
    root = make_mcp_repo(tmp_path, mcp_servers=tiers)
    assert sync_main(["sync"], repo_root=root) == 0
    text = (root / ".codex" / "config.toml").read_text(encoding="utf-8")
    assert '"--context", "claude-code"' in text
    assert '"codex"' not in text


def test_sync_failure_leaves_tree_untouched(tmp_path: Path) -> None:
    """Atomicity (#330-3): a FatalCheckError from emitter B must fire before ANY
    write — a previously-synced tree stays byte-identical (lock included)."""
    root = make_mcp_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    before = _snapshot(root)
    # poison the mcp source AND edit a skill source in the same session
    src = root / ".claude" / "skills" / "mj-agent-alpha" / "SKILL.md"
    src.write_text(src.read_text(encoding="utf-8") + "\nnew line\n", encoding="utf-8")
    mcp = json.loads((root / ".mcp.json").read_text(encoding="utf-8"))
    mcp["mcpServers"]["github"]["env"]["GITHUB_PERSONAL_ACCESS_TOKEN"] = "literal"
    (root / ".mcp.json").write_text(json.dumps(mcp), encoding="utf-8")
    assert sync_main(["sync"], repo_root=root) == 2
    assert _snapshot(root) == before  # no half-updated artifacts, no stale lock


def test_scoped_surfaces_flag_orphan_lock_keys(tmp_path: Path, capsys: Any) -> None:
    """#330-4: a stale lock key that is neither a whitelisted skill nor the reserved
    mcp key must not escape both scoped gates — the skills surface owns it."""
    root = make_mcp_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    lock_path = root / ".agents.lock.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    lock["mj-agent-ghost"] = "sha256:" + "0" * 64
    lock_path.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    assert sync_main(["--check", "--surface", "skills"], repo_root=root) == 1
    assert "unknown lock entry 'mj-agent-ghost'" in capsys.readouterr().out
    assert sync_main(["--check", "--surface", "mcp"], repo_root=root) == 0  # isolation kept


def test_mcp_surface_missing_lock_prints_mcp_action(tmp_path: Path, capsys: Any) -> None:
    """#330-7: --surface mcp drift must always print the mcp prescribed action,
    even when the only drift line has no '.codex' substring."""
    root = make_mcp_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    (root / ".agents.lock.json").unlink()
    assert sync_main(["--check", "--surface", "mcp"], repo_root=root) == 1
    assert PRESCRIBED_ACTION_MCP in capsys.readouterr().out


def test_project_server_missing_from_mcp_json_exits_2(tmp_path: Path, capsys: Any) -> None:
    servers = json.loads(json.dumps(MCP_JSON))
    del servers["playwright"]
    root = make_mcp_repo(tmp_path, mcp_json_servers=servers)
    assert sync_main(["sync"], repo_root=root) == 2
    assert "missing from .mcp.json" in capsys.readouterr().err


def test_check_mcp_drift_and_surface_scoping(tmp_path: Path, capsys: Any) -> None:
    """mcp drift must redden --surface mcp (V11 blocking) and --check all, but
    NEVER --surface skills (V10 warning); and vice versa for skills drift."""
    root = make_mcp_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    for surface in ("skills", "mcp", "all"):
        assert sync_main(["--check", "--surface", surface], repo_root=root) == 0
    capsys.readouterr()

    config = root / ".codex" / "config.toml"
    config.write_text(
        config.read_text(encoding="utf-8") + "\n[mcp_servers.rogue]\ncommand = \"x\"\n",
        encoding="utf-8",
    )
    assert sync_main(["--check", "--surface", "skills"], repo_root=root) == 0
    assert sync_main(["--check", "--surface", "mcp"], repo_root=root) == 1
    out = capsys.readouterr().out
    assert "hand-edited artifact OR source changed" in out
    assert PRESCRIBED_ACTION_MCP in out
    assert "A14" in out  # source-change routing pinned independently
    assert sync_main(["--check"], repo_root=root) == 1
    assert sync_main(["sync"], repo_root=root) == 0  # heals

    src = root / ".claude" / "skills" / "mj-agent-alpha" / "SKILL.md"
    src.write_text(src.read_text(encoding="utf-8") + "\nskills drift\n", encoding="utf-8")
    assert sync_main(["--check", "--surface", "mcp"], repo_root=root) == 0
    assert sync_main(["--check", "--surface", "skills"], repo_root=root) == 1


def test_check_mcp_missing_config_red(tmp_path: Path, capsys: Any) -> None:
    root = make_mcp_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    (root / ".codex" / "config.toml").unlink()
    assert sync_main(["--check", "--surface", "mcp"], repo_root=root) == 1
    out = capsys.readouterr().out
    assert "missing .codex/config.toml" in out


def test_surface_requires_check(tmp_path: Path) -> None:
    root = make_mcp_repo(tmp_path)
    assert sync_main(["sync", "--surface", "mcp"], repo_root=root) == 2
    assert sync_main(["--adopt", "mj-agent-alpha", "--surface", "mcp"], repo_root=root) == 2


def test_empty_mcp_tier_removes_codex_tree(tmp_path: Path) -> None:
    root = make_mcp_repo(
        tmp_path,
        mcp_servers={"github": {"projection_policy": "never"}},
        mcp_json_servers={"github": {"command": "x"}},
    )
    (root / ".codex").mkdir()
    (root / ".codex" / "config.toml").write_text("# stale\n", encoding="utf-8")
    assert sync_main(["sync"], repo_root=root) == 0
    assert not (root / ".codex").exists()
    assert sync_main(["--check"], repo_root=root) == 0
    lock = json.loads((root / ".agents.lock.json").read_text(encoding="utf-8"))
    assert CODEX_LOCK_KEY not in lock


def test_cross_eol_codex_config_check_stable(tmp_path: Path) -> None:
    """A CRLF checkout of the generated TOML must not trip --check or V9 (LF-normalized
    comparisons; .gitattributes pins *.toml eol=lf but the tooling stays EOL-proof)."""
    root = make_mcp_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    config = root / ".codex" / "config.toml"
    config.write_bytes(config.read_bytes().replace(b"\n", b"\r\n"))
    assert sync_main(["--check", "--surface", "mcp"], repo_root=root) == 0
    assert v9_main(["--all"], repo_root=root) == 0


# ------------------------------------------------ V9 PJ04x integration (S2 #330)


def _v9_out(root: Path, capsys: Any) -> str:
    rc = v9_main(["--all"], repo_root=root)
    return f"rc={rc} " + capsys.readouterr().out


def test_v9_pj042_pairing(tmp_path: Path, capsys: Any) -> None:
    root = make_mcp_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    (root / ".codex" / "config.toml").unlink()
    out = _v9_out(root, capsys)
    assert "rc=1" in out and "PJ042" in out


def test_v9_pj043_hash_and_pj044_never_leak(tmp_path: Path, capsys: Any) -> None:
    root = make_mcp_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    config = root / ".codex" / "config.toml"
    config.write_text(
        config.read_text(encoding="utf-8") + "\n[mcp_servers.ssh-manager]\ncommand = \"x\"\n",
        encoding="utf-8",
    )
    out = _v9_out(root, capsys)
    assert "rc=1" in out
    assert "PJ043" in out  # hash mismatch (hand edit)
    assert "PJ044" in out  # never-tier data-boundary leak
    assert "data boundary" in out


def test_v9_pj040_extra_and_missing_server(tmp_path: Path, capsys: Any) -> None:
    root = make_mcp_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    config = root / ".codex" / "config.toml"
    text = config.read_text(encoding="utf-8")
    text = text.replace("[mcp_servers.playwright]", "[mcp_servers.rogue]")
    config.write_text(text, encoding="utf-8")
    out = _v9_out(root, capsys)
    assert "rc=1" in out and "PJ040" in out
    assert "'rogue'" in out or "rogue" in out
    assert "playwright" in out  # missing side reported too


def test_v9_pj041_invalid_toml_and_pj045_stray_file(tmp_path: Path, capsys: Any) -> None:
    root = make_mcp_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    (root / ".codex" / "config.toml").write_text("not = [valid\n", encoding="utf-8")
    out = _v9_out(root, capsys)
    assert "rc=1" in out and "PJ041" in out
    assert sync_main(["sync"], repo_root=root) == 0
    (root / ".codex" / "extra.txt").write_text("x\n", encoding="utf-8")
    out = _v9_out(root, capsys)
    assert "rc=1" in out and "PJ045" in out


# -------------------------------------------------------- offline pytest boundary (Epic #499)


_OFFLINE_BOUNDARY_FILES = (
    Path("AGENTS.md"),
    Path("CLAUDE.md"),
    Path("capabilities/AGENTS.md"),
    Path("capabilities/CLAUDE.md"),
    Path("docker/AGENTS.md"),
    Path("docker/CLAUDE.md"),
    Path("src/mj_agent/AGENTS.md"),
    Path("src/mj_agent/CLAUDE.md"),
    Path("src/mj_agent/config.py"),
    Path("tests/AGENTS.md"),
    Path("tests/CLAUDE.md"),
    Path("tests/conftest.py"),
    Path("tests/bdd/conftest.py"),
    Path("sdd/workflows/execution-loop.md"),
    Path(".github/PULL_REQUEST_TEMPLATE.md"),
    Path(".github/workflows/ci.yml"),
    Path("scripts/sdd/run_offline_pytest.py"),
)


def _make_offline_boundary_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    for relative in _OFFLINE_BOUNDARY_FILES:
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO_ROOT / relative, destination)
    return root


def test_offline_boundary_checker_real_tree_green_and_human_readme_excluded() -> None:
    assert offline_boundary_check(REPO_ROOT) == []
    assert "uv run pytest tests/unit" in (REPO_ROOT / "README.md").read_text(encoding="utf-8")


def test_offline_boundary_checker_catches_source_ci_and_instruction_regressions(
    tmp_path: Path,
) -> None:
    root = _make_offline_boundary_repo(tmp_path)
    conftest = root / "tests" / "conftest.py"
    conftest.write_text(
        conftest.read_text(encoding="utf-8")
        + "\nfrom dotenv import load_dotenv\nload_dotenv()\n",
        encoding="utf-8",
    )
    config = root / "src" / "mj_agent" / "config.py"
    config.write_text(
        config.read_text(encoding="utf-8").replace(
            'values["_secrets_dir"] = None', 'values["not_a_source_disabler"] = None'
        ),
        encoding="utf-8",
    )
    instructions = root / "CLAUDE.md"
    instructions.write_text(
        instructions.read_text(encoding="utf-8") + "\nuv run pytest tests/unit\n",
        encoding="utf-8",
    )
    workflow = root / ".github" / "workflows" / "ci.yml"
    workflow.write_text(
        workflow.read_text(encoding="utf-8").replace(
            "uv run --frozen --no-sync python scripts/sdd/run_offline_pytest.py tests/bdd -q",
            "uv run pytest tests/bdd -q",
        ),
        encoding="utf-8",
    )

    messages = [item.message for item in offline_boundary_check(root)]
    assert any("dotenv" in message for message in messages)
    assert any("filesystem-source None writes" in message for message in messages)
    assert any("Agent-facing direct pytest" in message for message in messages)
    assert any("CI step is not bound" in message for message in messages)


def test_offline_boundary_checker_rejects_pre_skip_effect_and_fixture_override(
    tmp_path: Path,
) -> None:
    root = _make_offline_boundary_repo(tmp_path)
    conftest = root / "tests" / "conftest.py"
    conftest.write_text(
        conftest.read_text(encoding="utf-8").replace(
            '    pytest.skip(\n        "SKIP_POLICY_EXTERNAL_DEPENDENCY: biz live legs are permanently unavailable to pytest"\n    )',
            '    external_call()\n    pytest.skip(\n        "SKIP_POLICY_EXTERNAL_DEPENDENCY: biz live legs are permanently unavailable to pytest"\n    )',
        ),
        encoding="utf-8",
    )
    nested = root / "tests" / "unit" / "conftest.py"
    nested.parent.mkdir(parents=True)
    nested.write_text(
        "import pytest\n\n"
        "@pytest.fixture\n"
        "def docker_available():\n"
        "    return object()\n",
        encoding="utf-8",
    )

    messages = [item.message for item in offline_boundary_check(root)]
    assert any("live_db must unconditionally" in message for message in messages)
    assert any("reserved external fixture override: docker_available" in message for message in messages)


@pytest.mark.parametrize(
    "replacement",
    (
        '@external_call()\n@pytest.fixture(scope="session")\ndef live_db() -> None:',
        '@pytest.fixture(scope="session")\ndef live_db(value=external_call()) -> None:',
    ),
)
def test_offline_boundary_checker_rejects_policy_fixture_definition_time_effects(
    tmp_path: Path, replacement: str
) -> None:
    root = _make_offline_boundary_repo(tmp_path)
    conftest = root / "tests" / "conftest.py"
    conftest.write_text(
        conftest.read_text(encoding="utf-8").replace(
            '@pytest.fixture(scope="session")\ndef live_db() -> None:',
            replacement,
        ),
        encoding="utf-8",
    )
    messages = [item.message for item in offline_boundary_check(root)]
    assert any("live_db must remain the exact static session-skip fixture" in item for item in messages)


def test_offline_boundary_checker_rejects_marker_reset_and_renamed_fixture(
    tmp_path: Path,
) -> None:
    root = _make_offline_boundary_repo(tmp_path)
    conftest = root / "tests" / "conftest.py"
    conftest.write_text(
        conftest.read_text(encoding="utf-8")
        + '\nos.environ.pop("MJ_AGENT_OFFLINE_TEST", None)\n',
        encoding="utf-8",
    )
    nested = root / "tests" / "unit" / "conftest.py"
    nested.parent.mkdir(parents=True)
    nested.write_text(
        "import pytest\n\n"
        '@pytest.fixture(name="live_db")\n'
        "def enabled_external_route():\n"
        "    return object()\n",
        encoding="utf-8",
    )

    messages = [item.message for item in offline_boundary_check(root)]
    assert any("offline marker" in message or "process environment" in message for message in messages)
    assert any("reserved external fixture override: live_db" in message for message in messages)

    conftest.write_text(
        conftest.read_text(encoding="utf-8")
        + "\nfrom os import environ\nenviron.clear()\n",
        encoding="utf-8",
    )
    messages = [item.message for item in offline_boundary_check(root)]
    assert any("environment APIs directly" in message for message in messages)


def test_offline_boundary_checker_rejects_canonical_alias_and_functional_fixture(
    tmp_path: Path,
) -> None:
    root = _make_offline_boundary_repo(tmp_path)
    conftest = root / "tests" / "conftest.py"
    conftest.write_text(
        conftest.read_text(encoding="utf-8")
        + "\n@pytest.fixture(name=\"live_db\")\n"
        "def replacement_live_db():\n"
        "    return object()\n",
        encoding="utf-8",
    )
    test_module = root / "tests" / "unit" / "test_override.py"
    test_module.parent.mkdir(parents=True)
    test_module.write_text(
        "import pytest\n\n"
        "def enabled_external_route():\n"
        "    return object()\n\n"
        'pytest.fixture(name="memory_db")(enabled_external_route)\n',
        encoding="utf-8",
    )

    messages = [item.message for item in offline_boundary_check(root)]
    assert any("reserved external fixture override: live_db" in message for message in messages)
    assert any("reserved external fixture override: memory_db" in message for message in messages)


def test_offline_boundary_checker_rejects_nested_canonical_fixture_duplicate(
    tmp_path: Path,
) -> None:
    root = _make_offline_boundary_repo(tmp_path)
    conftest = root / "tests" / "conftest.py"
    conftest.write_text(
        conftest.read_text(encoding="utf-8")
        + "\nif True:\n"
        "    @pytest.fixture\n"
        "    def live_db():\n"
        "        return object()\n",
        encoding="utf-8",
    )
    messages = [item.message for item in offline_boundary_check(root)]
    assert any("reserved external fixture override: live_db" in message for message in messages)


def test_offline_boundary_checker_rejects_dynamic_tuple_and_parametrize_shadows(
    tmp_path: Path,
) -> None:
    root = _make_offline_boundary_repo(tmp_path)
    test_module = root / "tests" / "unit" / "test_override.py"
    test_module.parent.mkdir(parents=True)
    test_module.write_text(
        "import pytest\n\n"
        "def enabled_external_route(): return object()\n"
        '@pytest.fixture(**{"name": "live_db"})\n'
        "def dynamic_live(): return object()\n"
        "memory_db, unused = pytest.fixture(enabled_external_route), None\n"
        '@pytest.mark.parametrize("docker_available", [object()])\n'
        "def test_shadow(docker_available): pass\n",
        encoding="utf-8",
    )
    messages = [item.message for item in offline_boundary_check(root)]
    assert any("static reviewed string" in message for message in messages)
    assert any("memory_db" in message for message in messages)
    assert any("docker_available" in message for message in messages)


def test_offline_boundary_checker_allows_plain_reserved_named_helpers(tmp_path: Path) -> None:
    root = _make_offline_boundary_repo(tmp_path)
    test_module = root / "tests" / "unit" / "test_helpers.py"
    test_module.parent.mkdir(parents=True)
    test_module.write_text(
        "def agent(): return object()\n"
        "live_db = object()\n"
        "def test_helpers(): assert agent() is not live_db\n",
        encoding="utf-8",
    )
    assert offline_boundary_check(root) == []


def test_offline_boundary_checker_rejects_all_automatic_input_routes(
    tmp_path: Path,
) -> None:
    root = _make_offline_boundary_repo(tmp_path)
    unit = root / "tests" / "unit"
    unit.mkdir(parents=True)
    (unit / "conftest.py").write_text(
        "from dotenv import load_dotenv\nload_dotenv()\n",
        encoding="utf-8",
    )
    (unit / "__init__.py").write_text(
        'import os\nos.environ.pop("MJ_AGENT_OFFLINE_TEST", None)\n',
        encoding="utf-8",
    )
    (unit / "test_plugins.py").write_text(
        "from helper import plugins as pytest_plugins\n",
        encoding="utf-8",
    )
    messages = [item.message for item in offline_boundary_check(root)]
    assert any("import dotenv" in message for message in messages)
    assert any("empty or docstring-only" in message for message in messages)
    assert any("pytest_plugins binding/import" in message for message in messages)


def test_offline_boundary_checker_rejects_runtime_plugin_registration(
    tmp_path: Path,
) -> None:
    root = _make_offline_boundary_repo(tmp_path)
    plugin_route = root / "tests" / "unit" / "conftest.py"
    plugin_route.parent.mkdir(parents=True)
    plugin_route.write_text(
        "def pytest_configure(config):\n"
        "    pm = config.pluginmanager\n"
        "    pm.register(object())\n",
        encoding="utf-8",
    )
    violations = offline_boundary_check(root)
    assert any(
        item.path == plugin_route and "dynamic pytest plugin loading" in item.message
        for item in violations
    )


def test_offline_boundary_checker_rejects_top_level_test_inputs_and_path_aliases(
    tmp_path: Path,
) -> None:
    root = _make_offline_boundary_repo(tmp_path)
    unit = root / "tests" / "unit"
    unit.mkdir(parents=True)
    (unit / "test_marker_reset.py").write_text(
        "import os as operating_system\n"
        'operating_system.environ.pop("MJ_AGENT_OFFLINE_TEST", None)\n'
        "def test_ok(): pass\n",
        encoding="utf-8",
    )
    (unit / "test_dotenv.py").write_text(
        "from dotenv import load_dotenv\nload_dotenv()\ndef test_ok(): pass\n",
        encoding="utf-8",
    )
    (unit / "test_manual_env.py").write_text(
        'from pathlib import Path\nPath(".env").read_text()\ndef test_ok(): pass\n',
        encoding="utf-8",
    )
    (unit / "test_local_reset.py").write_text(
        "import os\n"
        "def reset():\n"
        '    os.environ.pop("MJ_AGENT_" + "OFFLINE_TEST", None)\n'
        "reset()\n"
        "def test_ok(): pass\n",
        encoding="utf-8",
    )
    (unit / "conftest.py").write_text(
        "import pathlib\npathlib.Path.home()\n",
        encoding="utf-8",
    )

    messages = [item.message for item in offline_boundary_check(root)]
    assert sum("process environment" in message for message in messages) >= 2
    assert any("import dotenv" in message for message in messages)
    assert any("read a .env file" in message for message in messages)
    assert any("repo/home paths" in message for message in messages)


def test_offline_boundary_checker_rejects_fixture_and_parametrize_factory_aliases(
    tmp_path: Path,
) -> None:
    root = _make_offline_boundary_repo(tmp_path)
    test_module = root / "tests" / "unit" / "test_alias_override.py"
    test_module.parent.mkdir(parents=True)
    test_module.write_text(
        "import pytest\n"
        "fixture_factory, unused = pytest.fixture, None\n"
        "parametrize = pytest.mark.parametrize\n"
        "def enabled_external_route(): return object()\n"
        "memory_db = fixture_factory(enabled_external_route)\n"
        '@parametrize("docker_available", [object()])\n'
        "def test_shadow(docker_available): pass\n",
        encoding="utf-8",
    )

    messages = [item.message for item in offline_boundary_check(root)]
    assert any("memory_db" in message for message in messages)
    assert any("docker_available" in message for message in messages)

    dynamic_module = root / "tests" / "unit" / "test_dynamic_alias.py"
    dynamic_module.write_text(
        "import pytest\n"
        "class Namespace: pass\n"
        "if True:\n"
        "    Namespace.fixture = pytest.fixture\n"
        '@Namespace.fixture(name="live_db")\n'
        "def enabled(): return object()\n"
        'factory = getattr(pytest, "fixture")\n'
        "def test_ok(): pass\n",
        encoding="utf-8",
    )
    violations = offline_boundary_check(root)
    assert any(
        item.path == dynamic_module and "live_db" in item.message for item in violations
    )
    assert any(
        item.path == dynamic_module and "static reviewed string" in item.message
        for item in violations
    )


@pytest.mark.parametrize(
    ("addition", "expected"),
    (
        ('\nos.environb.pop(b"MJ_AGENT_OFFLINE_TEST", None)\n', "process environment"),
        ("\npytest.skip = external_call\n", "rebind os/pytest"),
        ("\npolicy = pytest\npolicy.skip = external_call\n", "rebind os/pytest"),
    ),
)
def test_offline_boundary_checker_rejects_bytes_marker_and_policy_api_mutation(
    tmp_path: Path, addition: str, expected: str
) -> None:
    root = _make_offline_boundary_repo(tmp_path)
    conftest = root / "tests" / "conftest.py"
    conftest.write_text(
        conftest.read_text(encoding="utf-8") + addition,
        encoding="utf-8",
    )
    messages = [item.message for item in offline_boundary_check(root)]
    assert any(expected in message for message in messages)


def test_offline_boundary_checker_rejects_repo_root_conftest(tmp_path: Path) -> None:
    root = _make_offline_boundary_repo(tmp_path)
    (root / "conftest.py").write_text("raise RuntimeError\n", encoding="utf-8")
    messages = [item.message for item in offline_boundary_check(root)]
    assert any("repo-root conftest.py is forbidden" in message for message in messages)


def test_offline_boundary_read_rejects_reparse_before_reading(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "repo"
    target = root / "tests" / "conftest.py"
    target.parent.mkdir(parents=True)
    target.write_text("safe = True\n", encoding="utf-8")
    real_lstat = Path.lstat
    real_read_text = Path.read_text
    read_attempted = False

    def fake_lstat(path: Path) -> Any:
        info = real_lstat(path)
        if path == target:
            return SimpleNamespace(
                st_mode=info.st_mode,
                st_file_attributes=offline_runner._REPARSE_POINT,
            )
        return info

    def guarded_read_text(path: Path, *args: Any, **kwargs: Any) -> str:
        nonlocal read_attempted
        if path == target:
            read_attempted = True
            raise AssertionError("reparse target was read")
        return real_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "lstat", fake_lstat)
    monkeypatch.setattr(Path, "read_text", guarded_read_text)
    violations: list[OfflineViolation] = []
    assert offline_boundary_read(target, root, violations) is None
    assert not read_attempted
    assert any("regular/non-reparse" in item.message for item in violations)


def test_offline_boundary_checker_reports_reparse_test_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _make_offline_boundary_repo(tmp_path)
    unit = root / "tests" / "unit"
    unit.mkdir(parents=True)
    (unit / "test_safe.py").write_text("def test_ok(): pass\n", encoding="utf-8")
    real_lstat = Path.lstat

    def fake_lstat(path: Path) -> Any:
        info = real_lstat(path)
        if path == unit:
            return SimpleNamespace(
                st_mode=info.st_mode,
                st_file_attributes=offline_runner._REPARSE_POINT,
            )
        return info

    monkeypatch.setattr(Path, "lstat", fake_lstat)
    messages = [item.message for item in offline_boundary_check(root)]
    assert any("test directory must be regular/non-reparse" in message for message in messages)


@pytest.mark.parametrize(
    "command",
    (
        "pytest",
        "pytest tests/unit -q",
        "pytest --collect-only tests/unit",
        "pytest -s tests/unit",
        "pytest ./tests/unit",
        "pytest .\\tests\\unit",
        "pytest -- tests/unit",
        "pytest -- ./tests/unit",
        "pytest -- .\\tests\\unit",
        "'pytest' tests/unit",
        'uv run "pytest" tests/unit',
        "pytest \\\n  ./tests/unit",
        "uv run python -m pytest tests/unit -q",
        "uv run -q pytest tests/unit -q",
        "uv run -- pytest tests/unit -q",
        "python -I -m pytest tests/unit -q",
        "python3 -m pytest tests/unit -q",
        "py -3.12 -m pytest tests/unit -q",
    ),
)
def test_offline_boundary_checker_rejects_direct_pytest_variants(
    tmp_path: Path, command: str
) -> None:
    root = _make_offline_boundary_repo(tmp_path)
    instructions = root / "CLAUDE.md"
    instructions.write_text(
        instructions.read_text(encoding="utf-8") + f"\n{command}\n",
        encoding="utf-8",
    )
    messages = [item.message for item in offline_boundary_check(root)]
    assert any("Agent-facing direct pytest" in message for message in messages)


@pytest.mark.parametrize("block_header", ("|", "| # retained comment", "|2-"))
def test_offline_boundary_checker_rejects_multiline_ci_direct_pytest(
    tmp_path: Path, block_header: str
) -> None:
    root = _make_offline_boundary_repo(tmp_path)
    workflow = root / ".github" / "workflows" / "ci.yml"
    workflow.write_text(
        workflow.read_text(encoding="utf-8")
        + "\n  direct-regression:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        f"      - run: {block_header}\n"
        "          pytest \\\n"
        "            --collect-only ./tests/unit\n",
        encoding="utf-8",
    )
    messages = [item.message for item in offline_boundary_check(root)]
    assert any("CI still contains a direct pytest entry" in message for message in messages)


def test_offline_boundary_checker_scans_all_workflows_and_agent_markdown(
    tmp_path: Path,
) -> None:
    root = _make_offline_boundary_repo(tmp_path)
    workflow = root / ".github" / "workflows" / "extra.yml"
    workflow.write_text(
        "name: extra\non: workflow_dispatch\njobs:\n"
        "  direct:\n    runs-on: ubuntu-latest\n    steps:\n"
        "      - run: pytest ./tests/unit\n",
        encoding="utf-8",
    )
    instructions = root / ".claude" / "commands" / "extra.md"
    instructions.parent.mkdir(parents=True)
    instructions.write_text("pytest ./tests/unit\n", encoding="utf-8")

    violations = offline_boundary_check(root)
    assert any(item.path == workflow and "direct pytest" in item.message for item in violations)
    assert any(
        item.path == instructions and "Agent-facing direct pytest" in item.message
        for item in violations
    )


def test_offline_boundary_checker_requires_runner_in_the_named_ci_step(
    tmp_path: Path,
) -> None:
    root = _make_offline_boundary_repo(tmp_path)
    workflow = root / ".github" / "workflows" / "ci.yml"
    expected = (
        "uv run --frozen --no-sync python scripts/sdd/run_offline_pytest.py "
        "tests --ignore tests/bdd"
    )
    source = workflow.read_text(encoding="utf-8")
    source = source.replace(f"        run: {expected}", "        run: echo wrong", 1)
    source += (
        "\n      - name: unrelated runner carrier\n"
        f"        run: {expected}\n"
    )
    workflow.write_text(source, encoding="utf-8")
    messages = [item.message for item in offline_boundary_check(root)]
    assert any("CI step is not bound" in message for message in messages)


def test_offline_boundary_checker_rejects_inverted_settings_condition(tmp_path: Path) -> None:
    root = _make_offline_boundary_repo(tmp_path)
    config = root / "src" / "mj_agent" / "config.py"
    config.write_text(
        config.read_text(encoding="utf-8").replace(
            "os.environ.get(OFFLINE_TEST_ENV) == \"1\"",
            "os.environ.get(OFFLINE_TEST_ENV) != \"1\"",
        ),
        encoding="utf-8",
    )
    messages = [item.message for item in offline_boundary_check(root)]
    assert any("offline branch" in message for message in messages)


def test_offline_boundary_checker_rejects_source_reset_and_constant_rebind(
    tmp_path: Path,
) -> None:
    root = _make_offline_boundary_repo(tmp_path)
    config = root / "src" / "mj_agent" / "config.py"
    config.write_text(
        config.read_text(encoding="utf-8")
        .replace(
            '            values["_secrets_dir"] = None',
            '            values["_secrets_dir"] = None\n'
            '            values["_env_file"] = ".env"',
        )
        .replace(
            'OFFLINE_TEST_ENV = "MJ_AGENT_OFFLINE_TEST"',
            'OFFLINE_TEST_ENV = "MJ_AGENT_OFFLINE_TEST"\n'
            'OFFLINE_TEST_ENV = "MJ_AGENT_OFFLINE_TEST"',
        ),
        encoding="utf-8",
    )
    messages = [item.message for item in offline_boundary_check(root)]
    assert any("two filesystem-source None writes" in message for message in messages)
    assert any("uniquely bound" in message for message in messages)


@pytest.mark.parametrize(
    ("needle", "replacement", "expected"),
    (
        (
            "        super().__init__(**values)",
            "        super().__init__(**values)\n\n"
            "    def __init__(self, **values: Any) -> None:\n"
            "        super().__init__(**values)",
            "unique construction seam",
        ),
        (
            "    # ── 0. Application",
            "    @classmethod\n"
            "    def settings_customise_sources(cls, *sources: Any) -> tuple[Any, ...]:\n"
            "        return sources\n\n"
            "    # ── 0. Application",
            "source hooks bypass",
        ),
        (
            "settings = Settings()",
            "settings = Settings()\nsettings = Settings()",
            "must not be rebound or reconstructed",
        ),
        (
            "settings = Settings()",
            "from dotenv import load_dotenv\nload_dotenv()\nsettings = Settings()",
            "may not execute dotenv",
        ),
        (
            "settings = Settings()",
            "if True:\n"
            "    class Settings(BaseSettings):\n"
            "        pass\n\n"
            "settings = Settings()",
            "one unique top-level class",
        ),
    ),
)
def test_offline_boundary_checker_rejects_alternate_settings_construction_paths(
    tmp_path: Path, needle: str, replacement: str, expected: str
) -> None:
    root = _make_offline_boundary_repo(tmp_path)
    config = root / "src" / "mj_agent" / "config.py"
    source = config.read_text(encoding="utf-8")
    assert needle in source
    config.write_text(source.replace(needle, replacement, 1), encoding="utf-8")
    messages = [item.message for item in offline_boundary_check(root)]
    assert any(expected in message for message in messages)


@pytest.mark.parametrize(
    ("mutation", "expected"),
    (
        (
            lambda source: source + '\nSAFE_PARENT_ENV_NAMES += ("EXAMPLE_API_KEY",)\n',
            "literal closed collection",
        ),
        (
            lambda source: source.replace(
                "    env = _safe_parent_environment()",
                "    env = _safe_parent_environment()\n    env.update(os.environ)",
                1,
            ),
            "reviewed closed environment builder",
        ),
        (
            lambda source: source.replace(
                "def _load_toml(path: Path)",
                "if True:\n"
                "    def _safe_parent_environment() -> dict[str, str]:\n"
                "        return {}\n\n"
                "def _load_toml(path: Path)",
                1,
            ),
            "reviewed closed environment builder",
        ),
    ),
)
def test_offline_boundary_checker_rejects_runner_environment_expansion(
    tmp_path: Path, mutation: Any, expected: str
) -> None:
    root = _make_offline_boundary_repo(tmp_path)
    runner = root / "scripts" / "sdd" / "run_offline_pytest.py"
    runner.write_text(mutation(runner.read_text(encoding="utf-8")), encoding="utf-8")
    messages = [item.message for item in offline_boundary_check(root)]
    assert any(expected in message for message in messages)


def test_offline_boundary_checker_cli_rejects_arguments(capsys: Any) -> None:
    assert offline_boundary_main(["unexpected"], repo_root=REPO_ROOT) == 2
    assert "no command-line arguments" in capsys.readouterr().err


def test_offline_runner_child_environment_is_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    forbidden = (
        "PYTEST_ADDOPTS",
        "PYTEST_PLUGINS",
        "PYTHONPATH",
        "EXAMPLE_CREDENTIAL",
        "EXAMPLE_TOKEN",
        "EXAMPLE_SECRET",
        "EXAMPLE_PASSWORD",
        "EXAMPLE_API_KEY",
        "EXAMPLE_URL",
    )
    for name in forbidden:
        monkeypatch.setenv(name, "synthetic-never-print")

    profile = tmp_path / "profile"
    child = offline_runner._child_environment(profile)

    assert not set(forbidden) & child.keys()
    assert child["MJ_AGENT_OFFLINE_TEST"] == "1"
    assert child["PYTHONNOUSERSITE"] == "1"
    assert child["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "1"
    for name in (
        "HOME",
        "USERPROFILE",
        "XDG_CONFIG_HOME",
        "APPDATA",
        "TEMP",
        "PYTHONPYCACHEPREFIX",
    ):
        assert Path(child[name]).is_relative_to(profile)


def test_offline_runner_expands_only_tracked_test_files_and_rejects_untracked_conftest(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    unit = root / "tests" / "unit"
    unit.mkdir(parents=True)
    tracked_file = unit / "test_tracked.py"
    tracked_file.write_text("def test_ok(): pass\n", encoding="utf-8")
    (unit / "test_untracked.py").write_text("raise RuntimeError\n", encoding="utf-8")
    tracked = {"tests/unit/test_tracked.py"}

    assert offline_runner._expanded_target("tests/unit", root, tracked) == [
        "tests/unit/test_tracked.py"
    ]
    with pytest.raises(offline_runner.RunnerError, match="not Git-tracked"):
        offline_runner._expanded_target("tests/unit/test_untracked.py", root, tracked)

    root_conftest = root / "tests" / "conftest.py"
    root_conftest.write_text("pytest_plugins = ['rogue']\n", encoding="utf-8")
    with pytest.raises(offline_runner.RunnerError, match="not Git-tracked"):
        offline_runner._expanded_target("tests/unit", root, tracked)

    tracked.add("tests/conftest.py")
    with pytest.raises(offline_runner.RunnerError, match="declares pytest_plugins"):
        offline_runner._expanded_target("tests/unit", root, tracked)

    root_conftest.unlink()
    tracked.remove("tests/conftest.py")
    root_init = root / "tests" / "__init__.py"
    root_init.write_text("# package marker\n", encoding="utf-8")
    with pytest.raises(offline_runner.RunnerError, match="not Git-tracked"):
        offline_runner._expanded_target("tests/unit", root, tracked)

    tracked.add("tests/__init__.py")
    root_init.write_text("pytest_plugins = ['rogue']\n", encoding="utf-8")
    with pytest.raises(offline_runner.RunnerError, match="empty/docstring-only"):
        offline_runner._expanded_target("tests/unit", root, tracked)

    root_init.unlink()
    tracked.remove("tests/__init__.py")
    tracked_file.write_text(
        "pytest_plugins = ['rogue']\ndef test_ok(): pass\n", encoding="utf-8"
    )
    with pytest.raises(offline_runner.RunnerError, match="declares pytest_plugins"):
        offline_runner._expanded_target("tests/unit", root, tracked)


def test_offline_runner_rejects_reparse_and_malformed_node_id(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "repo"
    test_file = root / "tests" / "unit" / "test_boundary.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("def test_ok(): pass\n", encoding="utf-8")
    tracked = {"tests/unit/test_boundary.py"}

    with pytest.raises(offline_runner.RunnerError, match="node id is malformed"):
        offline_runner._expanded_target("tests/unit/test_boundary.py::", root, tracked)

    real_lstat = Path.lstat

    def fake_lstat(path: Path) -> Any:
        info = real_lstat(path)
        if path == root / "tests" / "unit":
            return SimpleNamespace(
                st_mode=info.st_mode,
                st_file_attributes=offline_runner._REPARSE_POINT,
            )
        return info

    monkeypatch.setattr(Path, "lstat", fake_lstat)
    with pytest.raises(offline_runner.RunnerError, match="symlink/reparse"):
        offline_runner._expanded_target("tests/unit/test_boundary.py", root, tracked)


def test_offline_runner_rejects_marker_reset_and_renamed_fixture(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    test_file = root / "tests" / "unit" / "test_boundary.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("def test_ok(): pass\n", encoding="utf-8")
    conftest = root / "tests" / "conftest.py"
    conftest.write_text(
        'import os\nos.environ["MJ_AGENT_OFFLINE_TEST"] = "1"\n'
        'os.environ.pop("MJ_AGENT_OFFLINE_TEST", None)\n',
        encoding="utf-8",
    )
    tracked = {"tests/unit/test_boundary.py", "tests/conftest.py"}

    with pytest.raises(offline_runner.RunnerError, match="offline mode|environment"):
        offline_runner._expanded_target("tests/unit/test_boundary.py", root, tracked)

    conftest.write_text(
        'import os\nos.environ["MJ_AGENT_OFFLINE_TEST"] = "1"\n'
        "from os import environ\nenviron.clear()\n",
        encoding="utf-8",
    )
    with pytest.raises(offline_runner.RunnerError, match="environment APIs directly"):
        offline_runner._expanded_target("tests/unit/test_boundary.py", root, tracked)

    conftest.write_text(
        'import os\nos.environ["MJ_AGENT_OFFLINE_TEST"] = "1"\n'
        'os.environb.pop(b"MJ_AGENT_OFFLINE_TEST", None)\n',
        encoding="utf-8",
    )
    with pytest.raises(offline_runner.RunnerError, match="process environment"):
        offline_runner._expanded_target("tests/unit/test_boundary.py", root, tracked)

    conftest.write_text(
        'import os\nos.environ["MJ_AGENT_OFFLINE_TEST"] = "1"\n',
        encoding="utf-8",
    )
    test_file.write_text(
        "import pytest\n"
        '@pytest.fixture(name="live_db")\n'
        "def enabled_external_route(): return object()\n"
        "def test_ok(): pass\n",
        encoding="utf-8",
    )
    with pytest.raises(offline_runner.RunnerError, match="reserved external fixture"):
        offline_runner._expanded_target("tests/unit/test_boundary.py", root, tracked)

    conftest.write_text(
        (REPO_ROOT / "tests" / "conftest.py").read_text(encoding="utf-8")
        + "\nif True:\n"
        "    @pytest.fixture\n"
        "    def live_db(): return object()\n",
        encoding="utf-8",
    )
    test_file.write_text("def test_ok(): pass\n", encoding="utf-8")
    with pytest.raises(offline_runner.RunnerError, match="reserved external fixture"):
        offline_runner._expanded_target("tests/unit/test_boundary.py", root, tracked)

    test_file.write_text(
        "import pytest\n"
        "def enabled_external_route(): return object()\n"
        "live_db, unused = pytest.fixture(enabled_external_route), None\n"
        '@pytest.mark.parametrize("docker_available", [object()])\n'
        "def test_shadow(docker_available): pass\n",
        encoding="utf-8",
    )
    with pytest.raises(offline_runner.RunnerError, match="reserved external fixture"):
        offline_runner._expanded_target("tests/unit/test_boundary.py", root, tracked)

    test_file.write_text(
        "import pytest\n"
        '@pytest.fixture(**{"name": "live_db"})\n'
        "def dynamic_live(): return object()\n"
        "def test_ok(): pass\n",
        encoding="utf-8",
    )
    with pytest.raises(offline_runner.RunnerError, match="dynamic name"):
        offline_runner._expanded_target("tests/unit/test_boundary.py", root, tracked)

    test_file.write_text("def test_ok(): pass\n", encoding="utf-8")
    conftest.write_text(
        'import os\nimport pytest\n'
        'os.environ["MJ_AGENT_OFFLINE_TEST"] = "1"\n'
        '@pytest.fixture(name="live_db")\n'
        "def replacement_live_db(): return object()\n",
        encoding="utf-8",
    )
    with pytest.raises(offline_runner.RunnerError, match="reserved external fixture"):
        offline_runner._expanded_target("tests/unit/test_boundary.py", root, tracked)

    conftest.write_text(
        'import os\nos.environ["MJ_AGENT_OFFLINE_TEST"] = "1"\n',
        encoding="utf-8",
    )
    test_file.write_text(
        "import pytest\n"
        "def enabled_external_route(): return object()\n"
        'pytest.fixture(name="memory_db")(enabled_external_route)\n'
        "def test_ok(): pass\n",
        encoding="utf-8",
    )
    with pytest.raises(offline_runner.RunnerError, match="reserved external fixture"):
        offline_runner._expanded_target("tests/unit/test_boundary.py", root, tracked)


def test_offline_runner_rejects_fixture_and_parametrize_factory_aliases(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    test_file = root / "tests" / "unit" / "test_boundary.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text(
        "import pytest\n"
        "fixture_factory, unused = pytest.fixture, None\n"
        "parametrize = pytest.mark.parametrize\n"
        "def enabled_external_route(): return object()\n"
        "memory_db = fixture_factory(enabled_external_route)\n"
        '@parametrize("docker_available", [object()])\n'
        "def test_shadow(docker_available): pass\n",
        encoding="utf-8",
    )
    with pytest.raises(offline_runner.RunnerError, match="reserved external fixture"):
        offline_runner._expanded_target(
            "tests/unit/test_boundary.py", root, {"tests/unit/test_boundary.py"}
        )

    test_file.write_text(
        "import pytest\n"
        "class Namespace: pass\n"
        "if True:\n"
        "    Namespace.fixture = pytest.fixture\n"
        '@Namespace.fixture(name="live_db")\n'
        "def enabled(): return object()\n"
        'factory = getattr(pytest, "fixture")\n'
        "def test_ok(): pass\n",
        encoding="utf-8",
    )
    with pytest.raises(offline_runner.RunnerError, match="dynamically|reserved external fixture"):
        offline_runner._expanded_target(
            "tests/unit/test_boundary.py", root, {"tests/unit/test_boundary.py"}
        )


@pytest.mark.parametrize(
    ("source", "expected"),
    (
        (
            "import os as operating_system\n"
            'operating_system.environ.pop("MJ_AGENT_OFFLINE_TEST", None)\n'
            "def test_ok(): pass\n",
            "process environment",
        ),
        (
            "from dotenv import load_dotenv\nload_dotenv()\ndef test_ok(): pass\n",
            "imports dotenv",
        ),
        (
            'from pathlib import Path\nPath(".env").read_text()\ndef test_ok(): pass\n',
            "reads a .env file",
        ),
        (
            "import os\n"
            "def reset():\n"
            '    os.environ.pop("MJ_AGENT_" + "OFFLINE_TEST", None)\n'
            "reset()\n"
            "def test_ok(): pass\n",
            "process environment",
        ),
    ),
)
def test_offline_runner_rejects_test_module_top_level_automatic_inputs(
    tmp_path: Path, source: str, expected: str
) -> None:
    root = tmp_path / "repo"
    test_file = root / "tests" / "unit" / "test_boundary.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text(source, encoding="utf-8")
    with pytest.raises(offline_runner.RunnerError, match=expected):
        offline_runner._expanded_target(
            "tests/unit/test_boundary.py", root, {"tests/unit/test_boundary.py"}
        )


def test_offline_runner_rejects_aliased_home_discovery_in_nested_conftest(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    test_file = root / "tests" / "unit" / "test_boundary.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("def test_ok(): pass\n", encoding="utf-8")
    nested = root / "tests" / "unit" / "conftest.py"
    nested.write_text("import pathlib\npathlib.Path.home()\n", encoding="utf-8")
    tracked = {"tests/unit/test_boundary.py", "tests/unit/conftest.py"}
    with pytest.raises(offline_runner.RunnerError, match="repo/home paths"):
        offline_runner._expanded_target("tests/unit/test_boundary.py", root, tracked)


def test_offline_runner_rejects_nested_discovery_package_code_and_plugin_import(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    unit = root / "tests" / "unit"
    unit.mkdir(parents=True)
    test_file = unit / "test_boundary.py"
    test_file.write_text("def test_ok(): pass\n", encoding="utf-8")
    root_conftest = root / "tests" / "conftest.py"
    root_conftest.write_text(
        'import os\nos.environ["MJ_AGENT_OFFLINE_TEST"] = "1"\n',
        encoding="utf-8",
    )
    nested = unit / "conftest.py"
    nested.write_text("from dotenv import load_dotenv\nload_dotenv()\n", encoding="utf-8")
    tracked = {
        "tests/unit/test_boundary.py",
        "tests/conftest.py",
        "tests/unit/conftest.py",
    }
    with pytest.raises(offline_runner.RunnerError, match="imports dotenv"):
        offline_runner._expanded_target("tests/unit/test_boundary.py", root, tracked)

    nested.unlink()
    tracked.remove("tests/unit/conftest.py")
    package = unit / "__init__.py"
    package.write_text(
        'import os\nos.environ.pop("MJ_AGENT_OFFLINE_TEST", None)\n',
        encoding="utf-8",
    )
    tracked.add("tests/unit/__init__.py")
    with pytest.raises(offline_runner.RunnerError, match="empty/docstring-only"):
        offline_runner._expanded_target("tests/unit/test_boundary.py", root, tracked)

    package.unlink()
    tracked.remove("tests/unit/__init__.py")
    test_file.write_text(
        "from helper import plugins as pytest_plugins\n"
        "def test_ok(): pass\n",
        encoding="utf-8",
    )
    with pytest.raises(offline_runner.RunnerError, match="imports pytest_plugins"):
        offline_runner._expanded_target("tests/unit/test_boundary.py", root, tracked)

    test_file.write_text("def test_ok(): pass\n", encoding="utf-8")
    dynamic_plugin = unit / "conftest.py"
    dynamic_plugin.write_text(
        "def pytest_configure(config):\n"
        "    pm = config.pluginmanager\n"
        "    pm.register(object())\n",
        encoding="utf-8",
    )
    tracked.add("tests/unit/conftest.py")
    with pytest.raises(offline_runner.RunnerError, match="loads plugins dynamically"):
        offline_runner._expanded_target("tests/unit/test_boundary.py", root, tracked)


def test_offline_runner_allows_plain_reserved_named_helpers(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    test_file = root / "tests" / "unit" / "test_helpers.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text(
        "def agent(): return object()\n"
        "live_db = object()\n"
        "def test_helpers(): assert agent() is not live_db\n",
        encoding="utf-8",
    )
    assert offline_runner._expanded_target(
        "tests/unit/test_helpers.py", root, {"tests/unit/test_helpers.py"}
    ) == ["tests/unit/test_helpers.py"]


def test_offline_runner_cannot_ignore_boundary_conftest(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    conftest = root / "tests" / "conftest.py"
    conftest.parent.mkdir(parents=True)
    conftest.write_text("# boundary\n", encoding="utf-8")
    tracked = {"tests/conftest.py"}

    with pytest.raises(offline_runner.RunnerError, match="not a test module"):
        offline_runner._validated_ignore("tests/conftest.py", root, tracked)


def test_offline_runner_command_is_isolated_and_plugins_are_exact(tmp_path: Path) -> None:
    plugins = ("pytest_asyncio.plugin", "pytest_bdd.plugin")
    pycache = tmp_path / "pycache"
    command = offline_runner._pytest_command(
        plugins, ["tests/unit/test_agents_sync.py"], pycache
    )
    assert command[:6] == [
        offline_runner.sys.executable,
        "-I",
        "-X",
        f"pycache_prefix={pycache}",
        "-m",
        "pytest",
    ]
    assert command[command.index("-c") + 1] == "pyproject.toml"
    assert command.count("-p") == len(plugins)
    assert [command[index + 1] for index, item in enumerate(command) if item == "-p"] == list(
        plugins
    )


def test_offline_runner_rejects_unreviewed_addopts() -> None:
    project = offline_runner._load_toml(REPO_ROOT / "pyproject.toml")
    tool = project["tool"]
    assert isinstance(tool, dict)
    pytest_section = tool["pytest"]
    assert isinstance(pytest_section, dict)
    options = pytest_section["ini_options"]
    assert isinstance(options, dict)
    options["addopts"] = "-ra --strict-markers -m 'not smoke and not contract' ../outside"

    with pytest.raises(offline_runner.RunnerError, match="differs from the reviewed"):
        offline_runner._pytest_config(project)


def test_offline_runner_rejects_stale_project_lock_metadata() -> None:
    project = offline_runner._load_toml(REPO_ROOT / "pyproject.toml")
    lock = offline_runner._load_toml(REPO_ROOT / "uv.lock")
    packages = lock["package"]
    assert isinstance(packages, list)
    project_record = next(
        item
        for item in packages
        if isinstance(item, dict) and item.get("name") == "mj-agent"
    )
    metadata = project_record["metadata"]
    assert isinstance(metadata, dict)
    requires_dev = metadata["requires-dev"]
    assert isinstance(requires_dev, dict)
    dev = requires_dev["dev"]
    assert isinstance(dev, list)
    pytest_record = next(
        item for item in dev if isinstance(item, dict) and item.get("name") == "pytest"
    )
    pytest_record["specifier"] = ">=999"

    with pytest.raises(offline_runner.RunnerError, match="does not match uv.lock metadata"):
        offline_runner._locked_versions(project, lock)


def test_offline_runner_plugins_match_project_lock_and_active_environment() -> None:
    assert offline_runner._verified_plugin_modules(REPO_ROOT) == (
        "pytest_asyncio.plugin",
        "pytest_bdd.plugin",
    )


def test_offline_runner_error_never_prints_parent_value(
    monkeypatch: pytest.MonkeyPatch, capsys: Any
) -> None:
    sentinel = "synthetic-parent-secret-must-not-appear"
    monkeypatch.setenv("EXAMPLE_SECRET", sentinel)
    assert offline_runner.main(["../outside"], repo_root=REPO_ROOT) == 2
    captured = capsys.readouterr()
    assert sentinel not in captured.out
    assert sentinel not in captured.err


# ------------------------------------------------------------------ real-tree pins


def test_real_tree_projection_in_sync() -> None:
    """Committed artifacts + lock must match sources (D-012: regenerate, never edit)."""
    assert sync_main(["--check"], repo_root=REPO_ROOT) == 0


def test_real_tree_mcp_projection_in_sync() -> None:
    """V11 blocking invariant (D-016 day-1; Owner record #330): the committed
    .codex/config.toml + reserved lock key must match .mcp.json x manifest tiers."""
    assert sync_main(["--check", "--surface", "mcp"], repo_root=REPO_ROOT) == 0
