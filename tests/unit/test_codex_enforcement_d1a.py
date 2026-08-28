"""Codex cooperative enforcement carrier — Epic #499 PR-D1a (plan §5.9 / §2.8.7).

Covers the four things the unit is accountable for:

1. TYPED SOURCE fail-closed contract — closed top keys, glob-free `policy_refs`,
   PreToolUse-only events (a PostToolUse deny would be a rollback, not a block),
   and every malformed shape refusing BEFORE any managed write.
2. HOOK DENY CANARY — the render/reconcile half provably blocks BEFORE the side
   effect: a refused enforcement render leaves a byte-identical tree, proven by
   a full-tree snapshot rather than by an after-the-fact cleanup.
3. NO-READ SPY (AC-12) — the runtime guard never touches `transcript_path`,
   `last_assistant_message`, `session_id` or any other forbidden payload field.
4. SURFACE ISOLATION — enforcement drift reddens ONLY the enforcement surface.
   Without this, `.codex/hooks.json` would fall into the skills bucket and the
   BLOCKING V10 gate would enforce V13's scope.

DELIBERATELY ABSENT: any "the real tree is in sync" assertion. This file runs in
the BLOCKING `Tests` CI step, so a real-tree enforcement drift pin here would
silently make the warning-only V13 gate blocking through the back door. Real-tree
drift is V13's job, and V13 is `continue-on-error: true` by design.

The `codex execpolicy` leg is a genuine runtime execution and is SKIPPED — not
passed — when the codex CLI is absent (plan §1.4: an unexecuted runtime leg is
SKIP, never PASS). codex is not installed on the CI runner.

Two source levels are exercised on purpose. The synthetic FIXTURE_SOURCE covers
the loader/renderer contract and the matching SEMANTICS (exact name vs prefix vs
substring); the REAL typed source is exercised separately, because a fixture that
never loads `sdd/adapters/codex-enforcement.yml` cannot catch a bad pattern in the
shipped guards. The fixture declares its own `secret.key` pattern rather than the
dotenv path only because `check_test_offline_boundary.py` refuses a bare dotenv
string constant inside a call in an automatic pytest input — correctly, since it
cannot tell a guard fixture from an actual read. The real source's dotenv and
`config/secrets*` patterns are covered through `config/secrets*.enc` spellings and
through the `codex execpolicy` leg.
"""

from __future__ import annotations

import io
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml
from scripts.sdd import codex_hook_guard as guard_module
from scripts.sdd._common import codex_hook_renderer, codex_rule_renderer
from scripts.sdd._common.enforcement_source import (
    EnforcementSourceError,
    load_enforcement_source,
    policy_ref_inventory,
)
from scripts.sdd._common.projection_loader import parse_lock_json, verify_lock_v2
from scripts.sdd.agents_sync import main as sync_main
from scripts.sdd.codex_hook_guard import (
    ALLOWED_INPUT_KEYS,
    FORBIDDEN_INPUT_KEYS,
    evaluate,
    project_payload,
)

from tests.unit.test_v2_engine import _write, make_v2_repo

SOURCE_RELPATH = "sdd/adapters/codex-enforcement.yml"
REAL_REPO_ROOT = Path(__file__).resolve().parents[2]

FIXTURE_SOURCE = """\
schema_version: 1

policy_refs:
  - AGENTS.md

hooks:
  handler:
    command: ["python", "scripts/sdd/codex_hook_guard.py"]
    timeout_seconds: 10
    status_message: "fixture guard"
  events:
    - event: PreToolUse
      matcher: shell
  guards:
    - id: fixture-secrets
      applies_to: [path, command_arg]
      decision: block
      deny_patterns:
        - secret.key
      reason: "fixture secrets guard"
    - id: fixture-branch
      applies_to: [command]
      decision: block
      deny_patterns:
        - git checkout -b
      reason: "fixture G1 guard"

rules:
  - output_path: .codex/rules/mj-agent.rules
    prefix_rules:
      - id: fixture-forbid
        pattern: ["git", "checkout", "-b"]
        decision: forbidden
        reason: "fixture"
"""


def _source_doc() -> dict[str, Any]:
    return yaml.safe_load(FIXTURE_SOURCE)


def _dump(doc: dict[str, Any]) -> str:
    return yaml.safe_dump(doc, sort_keys=False, allow_unicode=True)


def make_enforcement_repo(tmp_path: Path, *, source: str | None = None) -> Path:
    """A v2 fixture repo that DECLARES an enforcement source."""
    root = make_v2_repo(tmp_path)
    _write(root / "AGENTS.md", "# fixture AGENTS\n")
    _write(root / SOURCE_RELPATH, FIXTURE_SOURCE if source is None else source)
    return root


def snapshot(root: Path) -> dict[str, bytes]:
    """Full byte snapshot of every managed surface, `.codex/**` included.

    The pre-existing helper in test_agents_sync covers `.agents/**` +
    `.codex/config.toml` only; the enforcement outputs need the whole `.codex`
    tree or a stray write would go unnoticed.
    """
    snap: dict[str, bytes] = {}
    for rel in (".agents", ".codex"):
        base = root / rel
        if base.is_dir():
            for path in sorted(base.rglob("*")):
                if path.is_file():
                    snap[path.relative_to(root).as_posix()] = path.read_bytes()
    lock = root / ".agents.lock.json"
    if lock.is_file():
        snap[".agents.lock.json"] = lock.read_bytes()
    return snap


# --------------------------------------------------------------- typed source


def test_fixture_source_loads() -> None:
    source = load_enforcement_source(FIXTURE_SOURCE)
    assert source.schema_version == 1
    assert source.policy_refs == ("AGENTS.md",)
    assert [g.guard_id for g in source.guards] == ["fixture-secrets", "fixture-branch"]
    assert source.rule_files[0].output_path == ".codex/rules/mj-agent.rules"
    # Optional-by-design at v1 (plan §5.9 calls config_binding "optional";
    # §3.3 stages receipt_policy to PR-E).
    assert source.config_binding is None
    assert source.receipt_policy is None


def test_optional_top_keys_are_accepted_when_present() -> None:
    doc = _source_doc()
    doc["config_binding"] = {"note": "explicit"}
    doc["receipt_policy"] = {"note": "PR-E"}
    source = load_enforcement_source(_dump(doc))
    assert source.config_binding == {"note": "explicit"}
    assert source.receipt_policy == {"note": "PR-E"}


def test_unknown_top_key_is_refused() -> None:
    doc = _source_doc()
    doc["surprise"] = 1
    with pytest.raises(EnforcementSourceError, match="unknown key"):
        load_enforcement_source(_dump(doc))


@pytest.mark.parametrize("missing", ["schema_version", "policy_refs", "hooks", "rules"])
def test_missing_required_top_key_is_refused(missing: str) -> None:
    doc = _source_doc()
    doc.pop(missing)
    with pytest.raises(EnforcementSourceError):
        load_enforcement_source(_dump(doc))


def test_wrong_schema_version_is_refused() -> None:
    doc = _source_doc()
    doc["schema_version"] = 2
    with pytest.raises(EnforcementSourceError, match="schema_version"):
        load_enforcement_source(_dump(doc))


@pytest.mark.parametrize(
    "bad_ref",
    ["policies/*.md", "/etc/passwd", "../outside.md", "policies//ai-agent.md"],
)
def test_unsafe_or_glob_policy_ref_is_refused(bad_ref: str) -> None:
    doc = _source_doc()
    doc["policy_refs"] = [bad_ref]
    with pytest.raises(EnforcementSourceError):
        load_enforcement_source(_dump(doc))


def test_duplicate_policy_refs_are_refused() -> None:
    doc = _source_doc()
    doc["policy_refs"] = ["AGENTS.md", "AGENTS.md"]
    with pytest.raises(EnforcementSourceError, match="duplicate"):
        load_enforcement_source(_dump(doc))


def test_post_tool_use_event_is_refused() -> None:
    """A PostToolUse deny would be a ROLLBACK, not a block before the side
    effect — plan §5.9 requires the latter, so the loader refuses the former."""
    doc = _source_doc()
    doc["hooks"]["events"] = [{"event": "PostToolUse", "matcher": "shell"}]
    with pytest.raises(EnforcementSourceError, match="PreToolUse"):
        load_enforcement_source(_dump(doc))


def test_unknown_guard_surface_is_refused() -> None:
    doc = _source_doc()
    doc["hooks"]["guards"][0]["applies_to"] = ["telepathy"]
    with pytest.raises(EnforcementSourceError, match="applies_to"):
        load_enforcement_source(_dump(doc))


def test_unknown_rule_decision_is_refused() -> None:
    doc = _source_doc()
    doc["rules"][0]["prefix_rules"][0]["decision"] = "maybe"
    with pytest.raises(EnforcementSourceError, match="decision"):
        load_enforcement_source(_dump(doc))


def test_empty_prefix_rules_is_refused() -> None:
    """codex itself refuses an empty policy ('rules prefix_rules cannot be empty')."""
    doc = _source_doc()
    doc["rules"][0]["prefix_rules"] = []
    with pytest.raises(EnforcementSourceError, match="prefix_rules"):
        load_enforcement_source(_dump(doc))


@pytest.mark.parametrize(
    "bad_path",
    [".codex/hooks.json", "rules/mj-agent.rules", ".codex/rules/nested/x.rules",
     ".codex/rules/mj-agent.txt"],
)
def test_rule_output_path_grammar_is_enforced(bad_path: str) -> None:
    doc = _source_doc()
    doc["rules"][0]["output_path"] = bad_path
    with pytest.raises(EnforcementSourceError, match="output_path"):
        load_enforcement_source(_dump(doc))


def test_duplicate_guard_ids_are_refused() -> None:
    doc = _source_doc()
    doc["hooks"]["guards"][1]["id"] = doc["hooks"]["guards"][0]["id"]
    with pytest.raises(EnforcementSourceError, match="duplicate"):
        load_enforcement_source(_dump(doc))


# ------------------------------------------------------- policy ref inventory


def test_policy_ref_inventory_shape_and_missing_file(tmp_path: Path) -> None:
    (tmp_path / "b.md").write_bytes(b"beta\n")
    (tmp_path / "a.md").write_bytes(b"alpha\n")
    inventory = policy_ref_inventory(tmp_path, ("b.md", "a.md"))
    assert inventory["schema_version"] == 1
    assert [f["path"] for f in inventory["files"]] == ["a.md", "b.md"]  # sorted
    assert set(inventory["files"][0]) == {"path", "raw_sha256"}  # exact item keys
    with pytest.raises(EnforcementSourceError, match="unreadable"):
        policy_ref_inventory(tmp_path, ("gone.md",))


def test_policy_ref_digest_is_eol_insensitive(tmp_path: Path) -> None:
    """A CRLF working copy must not change the digest — otherwise a Windows
    checkout and the Linux CI runner would disagree about the lock."""
    (tmp_path / "lf.md").write_bytes(b"a\nb\n")
    (tmp_path / "crlf.md").write_bytes(b"a\r\nb\r\n")
    lf = policy_ref_inventory(tmp_path, ("lf.md",))["files"][0]["raw_sha256"]
    crlf = policy_ref_inventory(tmp_path, ("crlf.md",))["files"][0]["raw_sha256"]
    assert lf == crlf


# ------------------------------------------------------------------ renderers


def test_hook_render_is_canonical_and_deterministic() -> None:
    source = load_enforcement_source(FIXTURE_SOURCE)
    first = codex_hook_renderer.render_hooks(source)
    assert first == codex_hook_renderer.render_hooks(source)
    assert first.endswith("}\n") and not first.endswith("\n\n")
    assert "\r" not in first
    document = json.loads(first)
    assert set(document["hooks"]) == {"PreToolUse"}
    entry = document["hooks"]["PreToolUse"][0]
    assert entry["matcher"] == "shell"
    assert entry["hooks"][0]["type"] == "command"
    assert entry["hooks"][0]["timeout"] == 10
    # canonical-json-v1: `canonicalize()` only LF-normalizes, so the RENDERER
    # must already emit sorted keys / 2-space indent or check never converges.
    assert first == json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def test_rule_render_is_deterministic_and_lf() -> None:
    source = load_enforcement_source(FIXTURE_SOURCE)
    rule_file = source.rule_files[0]
    first = codex_rule_renderer.render_rules(rule_file)
    assert first == codex_rule_renderer.render_rules(rule_file)
    assert "\r" not in first
    assert first.endswith(")\n") and not first.endswith("\n\n")
    assert 'pattern=["git", "checkout", "-b"]' in first
    assert 'decision="forbidden"' in first


# ------------------------------------------- deny canary: block BEFORE effect


@pytest.mark.parametrize(
    ("mutate", "label"),
    [
        (lambda doc: doc.__setitem__("surprise", 1), "unknown-top-key"),
        (lambda doc: doc.__setitem__("policy_refs", ["policies/*.md"]), "glob-ref"),
        (lambda doc: doc.__setitem__("policy_refs", ["does-not-exist.md"]), "missing-ref"),
        (
            lambda doc: doc["hooks"]["events"].__setitem__(
                0, {"event": "PostToolUse", "matcher": "shell"}
            ),
            "post-tool-use",
        ),
    ],
)
def test_malformed_source_blocks_before_any_side_effect(
    tmp_path: Path, mutate: Any, label: str
) -> None:
    """THE deny canary (plan §5.9): a refused enforcement render must block
    BEFORE the side effect, not roll back after it. Proven by a full-tree byte
    snapshot taken before the failing sync and compared after."""
    root = make_enforcement_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0  # converge once, cleanly
    before = snapshot(root)
    assert before, "snapshot is empty — the assertion would be vacuous"

    doc = _source_doc()
    mutate(doc)
    _write(root / SOURCE_RELPATH, _dump(doc))

    assert sync_main(["sync"], repo_root=root) != 0, f"{label}: sync should refuse"
    assert snapshot(root) == before, f"{label}: sync mutated the tree before refusing"


def test_absent_source_renders_nothing_and_preserves_neighbors(tmp_path: Path) -> None:
    """No typed source == no enforcement declared. `.codex/hooks.json` then stays
    an UNOWNED neighbor, which is what keeps the plan §5.5 AC-05 negatives live."""
    root = make_v2_repo(tmp_path)  # no enforcement source
    assert sync_main(["sync"], repo_root=root) == 0
    hooks = root / ".codex" / "hooks.json"
    hooks.write_text("{}\n", encoding="utf-8")
    assert sync_main(["sync"], repo_root=root) == 0
    assert hooks.read_text(encoding="utf-8") == "{}\n"  # preserved, not deleted
    lock = verify_lock_v2(
        parse_lock_json((root / ".agents.lock.json").read_text(encoding="utf-8"))
    )
    assert ".codex/hooks.json" not in lock.entries


# ------------------------------------------------------- no-read spy (AC-12)


class _SpyDict(dict):
    """Records every key lookup so 'never an input' can be asserted, not promised."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.touched: set[str] = set()

    def __getitem__(self, key: Any) -> Any:
        self.touched.add(key)
        return super().__getitem__(key)

    def get(self, key: Any, default: Any = None) -> Any:
        self.touched.add(key)
        return super().get(key, default)

    def __contains__(self, key: Any) -> bool:
        self.touched.add(key)
        return super().__contains__(key)


def test_guard_never_reads_forbidden_payload_fields() -> None:
    """AC-12 no-read spy: transcript / last assistant message / session state are
    NEVER inputs to the enforcement path (plan §5.9)."""
    payload = _SpyDict(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "shell",
            "tool_input": {"command": ["git", "checkout", "-b", "x"]},
            "transcript_path": "/should/never/be/read",
            "agent_transcript_path": "/should/never/be/read",
            "last_assistant_message": "should never be read",
            "session_id": "s-1",
            "turn_id": "t-1",
            "stop_hook_active": True,
        }
    )
    projected = project_payload(payload)
    source = load_enforcement_source(FIXTURE_SOURCE)
    assert evaluate(source, projected) is not None  # it really did evaluate

    leaked = payload.touched & set(FORBIDDEN_INPUT_KEYS)
    assert not leaked, f"guard read forbidden payload field(s): {sorted(leaked)}"
    assert set(projected) <= set(ALLOWED_INPUT_KEYS)
    for forbidden in FORBIDDEN_INPUT_KEYS:
        assert forbidden not in projected


# ------------------------------------------------------- guard decision matrix


@pytest.mark.parametrize(
    ("command", "expected_guard"),
    [
        (["git", "checkout", "-b", "x"], "fixture-branch"),
        (["git", "checkout", "--", "README.md"], None),  # token-prefix, not substring
        (["cat", "secret.key"], "fixture-secrets"),
        (["cat", "secret.key.example"], None),  # exact name, so a template stays readable
        (["ls", "vault/mysecret.key"], None),  # a substring test would wrongly fire here
        (["ls", "-la"], None),
    ],
)
def test_guard_decisions(command: list[str], expected_guard: str | None) -> None:
    source = load_enforcement_source(FIXTURE_SOURCE)
    projected = project_payload(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "shell",
            "tool_input": {"command": command},
        }
    )
    guard = evaluate(source, projected)
    assert (guard.guard_id if guard else None) == expected_guard


def test_apply_patch_path_guard_reads_hunk_headers() -> None:
    """apply_patch arrives as {"command": ["apply_patch", "*** Begin Patch..."]};
    the WRITE target comes from the hunk headers, not from a path field."""
    source = load_enforcement_source(FIXTURE_SOURCE)
    patch = "*** Begin Patch\n*** Update File: secret.key\n@@\n-a\n+b\n*** End Patch"
    projected = project_payload(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "apply_patch",
            "tool_input": {"command": ["apply_patch", patch]},
        }
    )
    guard = evaluate(source, projected)
    assert guard is not None and guard.guard_id == "fixture-secrets"


def test_project_payload_keeps_only_allowlisted_keys() -> None:
    projected = project_payload(
        {"hook_event_name": "Stop", "transcript_path": "/nope", "tool_name": "shell"}
    )
    assert projected == {"hook_event_name": "Stop", "tool_name": "shell"}


# ------------------------------------------------------------ surface routing


def test_enforcement_drift_does_not_redden_blocking_surfaces(
    tmp_path: Path, capsys: Any
) -> None:
    """The regression that matters most: `_do_check_v2` used to classify every
    non-config key as `skills`, so enforcement drift would have been enforced by
    V10 (BLOCKING) instead of V13 (warning). Routing is by `surface_members`."""
    root = make_enforcement_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    (root / ".codex" / "hooks.json").write_text("{}\n", encoding="utf-8")
    capsys.readouterr()

    assert sync_main(["--check", "--surface", "skills"], repo_root=root) == 0  # V10
    assert sync_main(["--check", "--surface", "mcp"], repo_root=root) == 0  # V11
    assert sync_main(["--check", "--surface", "enforcement"], repo_root=root) == 1  # V13
    assert sync_main(["--check"], repo_root=root) == 1  # surface=all still sees it


def test_enforcement_entries_carry_the_pr_b_lock_contract(tmp_path: Path) -> None:
    root = make_enforcement_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    lock = verify_lock_v2(
        parse_lock_json((root / ".agents.lock.json").read_text(encoding="utf-8"))
    )
    hook = lock.entries[".codex/hooks.json"]
    assert hook.entry_kind == "codex-hook"
    assert hook.owner == "system:codex-hooks"
    assert hook.surface_members == ("enforcement",)
    assert hook.normalization_policy == "canonical-json-v1"
    rule_key = ".codex/rules/mj-agent.rules"
    rule = lock.entries[rule_key]
    assert rule.entry_kind == "codex-rule"
    assert rule.owner == f"system:codex-rules:{rule_key}"
    assert rule.surface_members == ("enforcement",)
    assert rule.normalization_policy == "generated-utf8-lf-v1"
    # The config entry must NOT have become composite — Gate 1 chose the direct
    # route precisely so V11's registered scope stays untouched.
    assert lock.entries[".codex/config.toml"].entry_kind == "codex-config-mcp"
    assert lock.surface_owned_keys("enforcement") == (".codex/hooks.json", rule_key)


# --------------------------------------------------------------- result codes


def _run_check(root: Path, surface: str, capsys: Any) -> tuple[int, str]:
    code = sync_main(["--check", "--surface", surface], repo_root=root)
    return code, capsys.readouterr().out


def test_enforcement_result_codes(tmp_path: Path, capsys: Any) -> None:
    """V13's predicate lives in STDOUT, not in the exit code: EXECUTED_CLEAN and
    every SKIP_* both exit 0, so the step conclusion cannot distinguish them."""
    root = make_enforcement_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    capsys.readouterr()

    code, out = _run_check(root, "enforcement", capsys)
    assert code == 0 and "EXECUTED_CLEAN" in out

    (root / ".codex" / "hooks.json").write_text("{}\n", encoding="utf-8")
    code, out = _run_check(root, "enforcement", capsys)
    assert code == 1 and "EXECUTED_WITH_FINDINGS" in out


def test_hand_edited_owned_artifact_makes_sync_refuse(tmp_path: Path) -> None:
    """Owned-only reconcile (AC-05/AC-06): a lock-owned artifact that no longer
    matches its lock hash is owner-ambiguous, so sync refuses with zero
    delete/write rather than clobbering a possible hand edit."""
    root = make_enforcement_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    (root / ".codex" / "hooks.json").write_text("{}\n", encoding="utf-8")
    (root / SOURCE_RELPATH).unlink()
    before = snapshot(root)
    assert sync_main(["sync"], repo_root=root) == 2
    assert snapshot(root) == before


def test_removing_source_deletes_owned_outputs_then_skips(
    tmp_path: Path, capsys: Any
) -> None:
    """Undeclaring the enforcement source retires its owned outputs cleanly, and
    the surface then reports a NEUTRAL skip rather than a clean run."""
    root = make_enforcement_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    hooks = root / ".codex" / "hooks.json"
    rules = root / ".codex" / "rules" / "mj-agent.rules"
    assert hooks.is_file() and rules.is_file()

    (root / SOURCE_RELPATH).unlink()
    assert sync_main(["sync"], repo_root=root) == 0
    assert not hooks.exists() and not rules.exists()
    assert (root / ".codex" / "config.toml").is_file()  # unrelated surface untouched
    capsys.readouterr()

    code, out = _run_check(root, "enforcement", capsys)
    assert code == 0 and "SKIP_NO_ENFORCEMENT_SOURCE" in out


def test_blocking_surfaces_emit_no_result_code_token(tmp_path: Path, capsys: Any) -> None:
    """V10 / V11 stdout must stay byte-unchanged by PR-D1a (Gate 1 拍板)."""
    root = make_enforcement_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    capsys.readouterr()
    for surface in ("skills", "mcp", "all"):
        code, out = _run_check(root, surface, capsys)
        assert code == 0
        assert "EXECUTED_CLEAN" not in out
        assert "SKIP_" not in out


# ------------------------------------------- codex execpolicy (runtime, SKIP-able)

_CODEX = shutil.which("codex")
_needs_codex = pytest.mark.skipif(
    _CODEX is None,
    reason="SKIP_NOT_INSTALLED: codex CLI absent (not installed on CI runners);"
    " an unexecuted runtime leg is SKIP, never PASS (plan §1.4)",
)


@_needs_codex
def test_rendered_rules_load_and_decide_in_codex(tmp_path: Path) -> None:
    """Rule fixtures via `codex execpolicy check`, asserting the decision codex
    itself reports (it already aggregates the STRICTEST decision across matched
    rules and across --rules files, so we never re-derive precedence).

    Two traps this asserts around, both verified against codex-cli 0.147.0:
      * `execpolicy check` exits 0 even for `forbidden` — the exit code is not a
        verdict, so it is deliberately not asserted on;
      * when nothing matches, the `decision` KEY IS ABSENT rather than "allow",
        so key presence is asserted explicitly instead of `.get(...) != "allow"`.
    """
    source = load_enforcement_source(
        (Path(__file__).resolve().parents[2] / SOURCE_RELPATH).read_text(encoding="utf-8")
    )
    rules_path = tmp_path / "mj-agent.rules"
    rules_path.write_text(
        codex_rule_renderer.render_rules(source.rule_files[0]), encoding="utf-8", newline="\n"
    )

    def decide(command: list[str]) -> dict[str, Any]:
        assert _CODEX is not None
        result = subprocess.run(  # noqa: S603 - fixed argv, no shell
            [_CODEX, "execpolicy", "check", "--rules", str(rules_path), *command],
            capture_output=True, text=True, timeout=60, check=False,
        )
        return json.loads(result.stdout)

    forbidden = decide(["git", "checkout", "-b", "x"])
    assert "decision" in forbidden, "no rule matched — fixture would be vacuous"
    assert forbidden["decision"] == "forbidden"

    prompted = decide(["git", "commit", "-m", "x"])
    assert "decision" in prompted and prompted["decision"] == "prompt"

    # The CORRECT G1 path must not be blocked, or the guard is worse than useless.
    allowed = decide(["git", "worktree", "add", "../x", "-b", "x"])
    assert allowed["matchedRules"] == []
    assert "decision" not in allowed  # absent, NOT "allow"


# ------------------------------------------- main() entrypoint (the real wire)
# Stage 11 finding E2: nothing exercised `main()` — the function `.codex/hooks.json`
# actually invokes — so the block-decision wire itself had zero coverage and the
# no-read spy could not observe the real entrypoint.


def _run_main(payload: Any, monkeypatch: Any, capsys: Any, root: Path | None = None) -> str:
    monkeypatch.setattr(
        guard_module.sys, "stdin", io.StringIO(json.dumps(payload)), raising=False
    )
    rc = guard_module.main(repo_root=root or REAL_REPO_ROOT)
    assert rc == 0, "the guard always exits 0; the verdict travels in stdout JSON"
    return capsys.readouterr().out


def test_main_emits_the_block_wire(monkeypatch: Any, capsys: Any) -> None:
    """codex 0.147.0 accepts {"decision":"block","reason":<non-empty>} and
    explicitly refuses decision:approve / permissionDecision:allow|ask, so the
    deny path must emit exactly this and the allow path must emit nothing."""
    out = _run_main(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "shell",
            "tool_input": {"command": ["git", "checkout", "-b", "x"]},
            "transcript_path": "/never/read",
            "last_assistant_message": "never read",
        },
        monkeypatch,
        capsys,
    )
    wire = json.loads(out)
    assert set(wire) == {"decision", "reason"}
    assert wire["decision"] == "block"
    assert wire["reason"].strip(), "codex refuses decision:block without a reason"
    assert "g1-branch-creation" in wire["reason"]


def test_main_allow_path_emits_nothing(monkeypatch: Any, capsys: Any) -> None:
    out = _run_main(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "shell",
            "tool_input": {"command": ["git", "worktree", "add", "../x", "-b", "x"]},
        },
        monkeypatch,
        capsys,
    )
    assert out == "", "an allow must be silent: decision:approve is unsupported"


@pytest.mark.parametrize(
    "payload",
    ["not json at all", "[]", '"a string"', '{"hook_event_name": "Stop"}'],
)
def test_main_fails_open_on_unusable_payload(
    payload: str, monkeypatch: Any, capsys: Any
) -> None:
    """Cooperative aid: an unparseable or non-PreToolUse payload must never wedge
    a Codex session. Fail-open here is deliberate and disclosed."""
    monkeypatch.setattr(guard_module.sys, "stdin", io.StringIO(payload), raising=False)
    assert guard_module.main(repo_root=REAL_REPO_ROOT) == 0
    assert capsys.readouterr().out == ""


def test_main_is_silent_when_no_typed_source(
    tmp_path: Path, monkeypatch: Any, capsys: Any
) -> None:
    out = _run_main(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "shell",
            "tool_input": {"command": ["git", "checkout", "-b", "x"]},
        },
        monkeypatch,
        capsys,
        root=tmp_path,
    )
    assert out == ""


# --------------------------------------- the REAL typed source's guards
# Stage 11 finding E3: the execpolicy leg exercises rules[].prefix_rules only,
# so the real source's hooks.guards deny_patterns had no coverage at all.

REAL_SOURCE = load_enforcement_source(
    (REAL_REPO_ROOT / SOURCE_RELPATH).read_text(encoding="utf-8")
)


def _real_guard(command: list[str]) -> str | None:
    projected = project_payload(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "shell",
            "tool_input": {"command": command},
        }
    )
    guard = evaluate(REAL_SOURCE, projected)
    return guard.guard_id if guard else None


def test_real_source_declares_the_expected_guards() -> None:
    assert [g.guard_id for g in REAL_SOURCE.guards] == [
        "data-boundary-direct-db",
        "secrets-read",
        "g1-branch-creation",
        "must-stop-surfaces",
        "generated-artifact-hand-edit",
    ]


@pytest.mark.parametrize(
    ("command", "expected"),
    [
        (["psql", "-h", "host"], "data-boundary-direct-db"),
        (["pg_dump", "db"], "data-boundary-direct-db"),
        (["git", "checkout", "-b", "x"], "g1-branch-creation"),
        (["git", "switch", "-c", "x"], "g1-branch-creation"),
        (["cat", "config/secrets.enc"], "secrets-read"),
        (["cat", "config/secrets-mcp.enc"], "secrets-read"),
        (["git", "worktree", "add", "../x", "-b", "x"], None),
        (["git", "checkout", "--", "README.md"], None),
        (["ls", "-la"], None),
        (["uv", "run", "pytest"], None),
        (["codex", "execpolicy", "check", "--rules", ".codex/rules/mj-agent.rules"], None),
    ],
)
def test_real_source_command_guards(command: list[str], expected: str | None) -> None:
    assert _real_guard(command) == expected


def test_real_source_exempts_the_documented_compose_command() -> None:
    """CLAUDE.md documents this exact invocation; blocking the project's own
    canonical command would make the guard actively wrong."""
    assert _real_guard(
        ["docker", "compose", "--env-file", ".env", "-f", "docker/compose.yaml", "up", "-d"]
    ) is None


def _patch_guard(target: str, key: str = "command") -> str | None:
    patch = f"*** Begin Patch\n*** Update File: {target}\n@@\n-a\n+b\n*** End Patch"
    payload = (
        {"command": ["apply_patch", patch]} if key == "command" else {key: patch}
    )
    projected = project_payload(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "apply_patch",
            "tool_input": payload,
        }
    )
    guard = evaluate(REAL_SOURCE, projected)
    return guard.guard_id if guard else None


@pytest.mark.parametrize(
    ("target", "expected"),
    [
        ("src/mj_agent/tools/sql/guardrail.py", "must-stop-surfaces"),
        ("src/mj_agent/tools/sql/precheck.py", "must-stop-surfaces"),
        ("src/mj_agent/prompts/system.md", "must-stop-surfaces"),
        ("src/mj_agent/biz_catalog/qcm_catalog.yaml", "must-stop-surfaces"),
        (".claude/settings.json", "must-stop-surfaces"),
        (".mcp.json", "must-stop-surfaces"),
        (".agents/skills/mj-agent-git-pr/SKILL.md", "generated-artifact-hand-edit"),
        (".codex/hooks.json", "generated-artifact-hand-edit"),
        (".agents.lock.json", "generated-artifact-hand-edit"),
        ("README.md", None),
        ("src/mj_agent/agent.py", None),
    ],
)
def test_real_source_path_guards_via_apply_patch(target: str, expected: str | None) -> None:
    assert _patch_guard(target) == expected


def test_path_guard_survives_an_absolute_spelling() -> None:
    """A multi-segment pattern must match a prefixed spelling of the same file,
    or the must-stop patterns degrade to exact repo-relative string equality."""
    assert _patch_guard("D:/repo/src/mj_agent/prompts/system.md") == "must-stop-surfaces"


def test_patch_envelope_is_found_under_any_tool_input_key() -> None:
    """The documented shape is command=[apply_patch, ...], but a differently-keyed
    payload must not silently yield zero write targets."""
    assert _patch_guard("src/mj_agent/prompts/system.md", key="input") == "must-stop-surfaces"


# ------------------------------------------------ loader hardening (Stage 11)


def test_secret_bearing_policy_ref_is_refused() -> None:
    """policy_refs are read as RAW BYTES and their digests are committed to the
    lock, so declaring a secret would publish a digest of it."""
    doc = _source_doc()
    for secret in ("config/secrets.enc", "config/secrets-mcp.enc"):
        doc["policy_refs"] = [secret]
        with pytest.raises(EnforcementSourceError, match="secret"):
            load_enforcement_source(_dump(doc))


def test_bracket_named_canonical_doc_is_a_valid_policy_ref() -> None:
    """This repo's canonical documents are named [TYPE]_Name.md — including the
    plan governing this Epic. Treating brackets as glob syntax would make most of
    the policy corpus undeclarable."""
    doc = _source_doc()
    doc["policy_refs"] = ["plans/[PLAN]_codex_cross_carrier_kernel.md"]
    source = load_enforcement_source(_dump(doc))
    assert source.policy_refs == ("plans/[PLAN]_codex_cross_carrier_kernel.md",)
    inventory = policy_ref_inventory(REAL_REPO_ROOT, source.policy_refs)
    assert inventory["files"][0]["path"] == "plans/[PLAN]_codex_cross_carrier_kernel.md"


def test_mixed_type_keys_do_not_escape_as_a_traceback(tmp_path: Path) -> None:
    """sorted() over a heterogeneous key set raises TypeError; the engine contract
    is exit 2 with a message, never a traceback."""
    root = make_enforcement_repo(tmp_path)
    _write(
        root / SOURCE_RELPATH,
        "schema_version: 1\n1: a\ntrue: b\npolicy_refs: [AGENTS.md]\n",
    )
    before = snapshot(root)
    assert sync_main(["sync"], repo_root=root) == 2
    assert snapshot(root) == before
    assert sync_main(["--check", "--surface", "enforcement"], repo_root=root) == 2


# ------------------------------------------------- result codes (Stage 11)


def test_error_path_emits_a_result_code(tmp_path: Path, capsys: Any) -> None:
    """rc 2 must still print a token: continue-on-error: true swallows the exit
    code, so a silent error would leave PR-D1b unable to reset the epoch."""
    root = make_enforcement_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    _write(root / SOURCE_RELPATH, "schema_version: 99\n")
    capsys.readouterr()
    assert sync_main(["--check", "--surface", "enforcement"], repo_root=root) == 2
    assert "ERROR_UNREADABLE" in capsys.readouterr().out


def test_v1_manifest_reports_a_neutral_skip(tmp_path: Path, capsys: Any) -> None:
    """A pre-cutover tree must report SKIP (epoch-neutral), never EXECUTED_CLEAN —
    otherwise PR-D1b's eligibility streak would be silently inflated."""
    root = make_v2_repo(tmp_path, schema_version=1)
    assert sync_main(["sync"], repo_root=root) == 0
    capsys.readouterr()
    assert sync_main(["--check", "--surface", "enforcement"], repo_root=root) == 0
    out = capsys.readouterr().out
    assert "SKIP_MANIFEST_V1" in out
    assert "EXECUTED_CLEAN" not in out


def test_surface_all_names_the_enforcement_source_in_its_remediation(
    tmp_path: Path, capsys: Any
) -> None:
    """--check (surface=all) is the documented local workflow; an
    enforcement-only drift must not send the reader to .claude/skills or .mcp.json."""
    root = make_enforcement_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    (root / ".codex" / "hooks.json").write_text("{}\n", encoding="utf-8")
    capsys.readouterr()
    assert sync_main(["--check"], repo_root=root) == 1
    assert "sdd/adapters/codex-enforcement.yml" in capsys.readouterr().out
