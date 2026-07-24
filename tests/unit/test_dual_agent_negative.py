"""#391 — dual-agent-compat §12 negative-test classes not previously committed.

Implements the two §12 acceptance classes surfaced as gaps by the #390 P4 pre-flip audit:

  A. Adapter-deletion replaceability (plan §12 L447-449 + principle 7 L42): deleting a tool's
     adapter surface leaves the Kernel, the other tool's path, and the shared test semantics
     intact — proving the adapter is a replaceable reference target, not a hidden source of truth.
  B. biz / env self-enforced boundary (plan §12 L442-443): committed proxy for the AGENTS.md
     self-enforced data / secrets boundary that binds Codex (which has no harness gate).

§12 negative-test coverage ledger (this file closes the last two open classes):
  - biz (L442) / env (L443)      -> Deliverable B here (committed proxy + documented limitation).
  - commit-not-approved (L444)   -> already committed: S4/S5 no-write-and-classification-exact
                                    fixtures (test_sdd_development_agent.py) + git owner-hitl gate.
  - hook fail-closed (L445)      -> already committed: test_guard_git_workflow_hook.py
                                    (non-JSON / empty / unknown / missing-field -> exit 2).
  - adapter-deletion (L447-449)  -> Deliverable A here.

Deliverable B is a STATIC proxy, NOT a runtime refusal proof. The literal §12 clause
"证明两者都拒绝 raw DB 连接 / 不读取 secrets" is a property of a live dual-agent session and is
reproducible only by the harness (manual scans of uncommitted trajectory logs — see
evidence/development-agent-p2,p3/SUMMARY.md); no ``uv run pytest`` can reproduce it. B1/B2 pin the
AGENTS.md prose that IS Codex's self-enforcement surface; the structural leg (biz/ssh MCP never
reach Codex) is already guarded by PJ044 (V9) / V11 (blocking) / the codex golden — not duplicated.

Adapter framing: the live manifest carries ONE shared adapter doc
(sdd/adapters/development-agent.md) referenced only by the 18 codex-side ``adapter_ref`` entries;
the claude side is always support_mode native. A1/A1b therefore use SYNTHETIC distinct per-tool
adapter docs to prove the checker's per-side independence (the DA033 loop is symmetric over both
sides), while the real-tree test exercises the real shared adapter against the real
projection/other-tool path. Synthetic repos are built under tmp_path and injected via
``main(argv, repo_root=...)`` (#217 pattern); the real-tree test operates on a temp COPY and never
mutates the live repo.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import pytest
from scripts.sdd.agents_sync import main as agents_sync_main
from scripts.sdd.check_agents_projection import main as v9_main
from scripts.sdd.check_development_agent import main as v8_main

from tests.unit.test_agents_sync import make_projection_repo
from tests.unit.test_sdd_development_agent import _write, cap, make_repo

REPO_ROOT = Path(__file__).resolve().parents[2]

CLAUDE_ADAPTER = "sdd/adapters/claude-dev.md"
CODEX_ADAPTER = "sdd/adapters/codex-dev.md"
LIVE_ADAPTER = "sdd/adapters/development-agent.md"

_COPY_IGNORE = shutil.ignore_patterns(
    ".git", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "node_modules"
)


def _adapter_side(adapter_ref: str) -> dict[str, Any]:
    return {
        "support_mode": "adapter-backed",
        "approval": {"mode": "none", "gates": []},
        "enforcement": ["adapter"],
        "adapter_ref": adapter_ref,
    }


def _adapter_tree(tmp_path: Path) -> Path:
    """Green synthetic tree: mj-agent-a is claude-adapter-backed, mj-agent-b codex-adapter-backed."""
    root = make_repo(
        tmp_path,
        [
            cap("mj-agent-a", claude=_adapter_side(CLAUDE_ADAPTER)),
            cap("mj-agent-b", codex=_adapter_side(CODEX_ADAPTER)),
        ],
    )
    _write(root / CLAUDE_ADAPTER, "# claude adapter\n")
    _write(root / CODEX_ADAPTER, "# codex adapter\n")
    return root


def _error_violations(capsys: Any) -> list[dict[str, Any]]:
    """Error-severity violations from a single ``--json`` V8 run (drain capsys before calling)."""
    payload = json.loads(capsys.readouterr().out)
    return [v for v in payload["violations"] if v["severity"] == "error"]


# ---------------------------------------------- A: adapter-deletion replaceability (§12 L447-449)


def test_deleting_claude_adapter_breaks_only_its_own_pointer(tmp_path: Path, capsys: Any) -> None:
    """Delete the Claude adapter -> only its DA033 fires; the Codex adapter and every other
    Kernel check are unaffected (no cascade). Proves per-side independence of the adapter ref."""
    root = _adapter_tree(tmp_path)
    assert v8_main(["--all"], repo_root=root) == 0  # green baseline
    capsys.readouterr()  # drain baseline output before the measured --json run
    (root / CLAUDE_ADAPTER).unlink()
    assert v8_main(["--all", "--json"], repo_root=root) == 1
    errs = _error_violations(capsys)
    assert [v["code"] for v in errs] == ["DA033"]  # exactly one; no cascade, no codex DA033
    assert errs[0]["path"] == CLAUDE_ADAPTER
    assert "claude" in errs[0]["message"]
    assert (root / CODEX_ADAPTER).is_file()  # the other tool's adapter survives untouched


def test_deleting_codex_adapter_breaks_only_its_own_pointer(tmp_path: Path, capsys: Any) -> None:
    """Symmetric to the Claude case: delete the Codex adapter -> only its DA033 fires; the Claude
    adapter and the rest of the Kernel stay green."""
    root = _adapter_tree(tmp_path)
    assert v8_main(["--all"], repo_root=root) == 0
    capsys.readouterr()
    (root / CODEX_ADAPTER).unlink()
    assert v8_main(["--all", "--json"], repo_root=root) == 1
    errs = _error_violations(capsys)
    assert [v["code"] for v in errs] == ["DA033"]
    assert errs[0]["path"] == CODEX_ADAPTER
    assert "codex" in errs[0]["message"]
    assert (root / CLAUDE_ADAPTER).is_file()


def test_adapter_is_replaceable_any_file_restores_green(tmp_path: Path) -> None:
    """V8 treats ``adapter_ref`` as a pure existence pointer (content-agnostic): re-supplying ANY
    file at the path restores green, proving the adapter carries no unique rule / is not a hidden
    SoT. (This bounds the DA033 mechanism only; body-duplication of rules is a separate §14
    mitigation, not exercised here.)"""
    root = _adapter_tree(tmp_path)
    (root / CLAUDE_ADAPTER).unlink()
    assert v8_main(["--all"], repo_root=root) == 1
    _write(root / CLAUDE_ADAPTER, "completely different content — irrelevant to the checker\n")
    assert v8_main(["--all"], repo_root=root) == 0


def test_projection_domain_is_independent_of_the_adapter_doc(tmp_path: Path) -> None:
    """The other tool's projection path (V9 over a real .agents/ closure+reconcile+lock) is
    unaffected by writing or deleting an adapter doc. Non-vacuous: ``sync`` makes V9 validate a
    fully-closed projection that is green even at --fail-on warning, so this is NOT an empty-set
    S0 pass — V9 is doing real work while the adapter appears and disappears."""
    root = make_projection_repo(tmp_path)
    assert agents_sync_main(["sync"], repo_root=root) == 0
    assert v9_main(["--all", "--fail-on", "warning"], repo_root=root) == 0  # real, closed projection
    _write(root / LIVE_ADAPTER, "# adapter doc\n")
    assert v9_main(["--all", "--fail-on", "warning"], repo_root=root) == 0
    (root / LIVE_ADAPTER).unlink()
    assert v9_main(["--all", "--fail-on", "warning"], repo_root=root) == 0


def test_adapter_that_is_also_evidence_double_hits(tmp_path: Path, capsys: Any) -> None:
    """Mirrors the live dual role (development-agent.md is BOTH ``adapter_ref`` AND required
    evidence for 2 caps): deleting it yields DA033 (dangling pointer) + DA032 (missing evidence),
    both at error severity because the cap is required. Asserts the code CATEGORY, not a count."""
    dual = cap(
        "mj-agent-a",
        required=True,
        codex=_adapter_side(CODEX_ADAPTER),
        evidence=[".claude/skills/mj-agent-a/SKILL.md", CODEX_ADAPTER],
    )
    root = make_repo(tmp_path, [dual])
    _write(root / CODEX_ADAPTER, "# dual-role adapter\n")
    assert v8_main(["--all"], repo_root=root) == 0
    capsys.readouterr()
    (root / CODEX_ADAPTER).unlink()
    assert v8_main(["--all", "--json"], repo_root=root) == 1
    assert sorted({v["code"] for v in _error_violations(capsys)}) == ["DA032", "DA033"]


def test_real_tree_adapter_deletion_is_contained(tmp_path: Path, capsys: Any) -> None:
    """On a COPY of the real tree, deleting sdd/adapters/development-agent.md keeps the other
    tool's path (V9) green and confines ALL V8 errors to the adapter pointer (codes in
    {DA032, DA033}, every error path == the adapter) — no count hardcode, no Kernel cascade. The
    shared-test surface (fixture_comparators + S1-S6 scenarios) is untouched — this discharges the
    §12 '共享测试/测试语义仍成立' clause: every surviving Kernel/test rule still validates and only
    the adapter pointer breaks. Never mutates the live tree (operates on the tmp copy); skips only
    if copytree cannot complete."""
    dst = tmp_path / "repo"
    try:
        shutil.copytree(REPO_ROOT, dst, ignore=_COPY_IGNORE)
    except (OSError, shutil.Error) as exc:  # pragma: no cover — environment-dependent
        pytest.skip(f"real-tree copy unavailable: {exc!r}")
    assert (dst / LIVE_ADAPTER).is_file()
    assert v8_main(["--all"], repo_root=dst) == 0  # faithful green copy
    assert v9_main(["--all"], repo_root=dst) == 0
    (dst / LIVE_ADAPTER).unlink()
    assert v9_main(["--all"], repo_root=dst) == 0  # other-tool projection path survives
    capsys.readouterr()  # drain prior text output before the measured --json run
    assert v8_main(["--all", "--json"], repo_root=dst) == 1
    errs = _error_violations(capsys)
    assert errs  # something broke
    assert {v["code"] for v in errs} <= {"DA032", "DA033"}
    assert {v["path"] for v in errs} == {LIVE_ADAPTER}  # nothing outside the adapter regressed
    assert (dst / "scripts" / "sdd" / "fixture_comparators.py").is_file()
    assert (dst / "tests" / "fixtures" / "development-agent" / "scenarios").is_dir()


# ---------------------------------------------- B: biz/env self-enforced boundary (§12 L442-443)


def _agents_md() -> str:
    return (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")


def test_agents_md_pins_biz_data_boundary_prose() -> None:
    """§12 L442 committed proxy: AGENTS.md self-enforced biz boundary (Codex's ONLY enforcement —
    it runs under no harness gate) must forbid raw DB connections. Static proxy for the RULE TEXT;
    the runtime refusal itself is harness-reproducible-only (see module docstring)."""
    text = _agents_md()
    assert "Do NOT connect to any database directly" in text
    assert "never bypass it" in text


def test_agents_md_pins_secrets_boundary_prose() -> None:
    """§12 L443 committed proxy: AGENTS.md self-enforced secrets boundary must forbid reading /
    exfiltrating credentials. Static proxy for the rule text (see module docstring)."""
    assert "never read or exfiltrate" in _agents_md()
