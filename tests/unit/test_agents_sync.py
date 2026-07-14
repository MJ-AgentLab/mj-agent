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
from typing import Any

from scripts.sdd.agents_sync import CODEX_CONFIG_HEADER, PRESCRIBED_ACTION, PRESCRIBED_ACTION_MCP
from scripts.sdd.agents_sync import main as sync_main
from scripts.sdd.check_agents_projection import CODEX_LOCK_KEY
from scripts.sdd.check_agents_projection import main as v9_main

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


# ------------------------------------------------------------------ real-tree pins


def test_real_tree_projection_in_sync() -> None:
    """Committed artifacts + lock must match sources (D-012: regenerate, never edit)."""
    assert sync_main(["--check"], repo_root=REPO_ROOT) == 0


def test_real_tree_mcp_projection_in_sync() -> None:
    """V11 blocking invariant (D-016 day-1; Owner record #330): the committed
    .codex/config.toml + reserved lock key must match .mcp.json x manifest tiers."""
    assert sync_main(["--check", "--surface", "mcp"], repo_root=REPO_ROOT) == 0
