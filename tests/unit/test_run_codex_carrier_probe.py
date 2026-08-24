"""Contract tests for ``scripts/sdd/run_codex_carrier_probe.py`` (Epic #499 PR-P1a).

Every case runs against a synthetic git repository under ``tmp_path`` with an
injectable fake codex runner — the real ``codex`` binary is never invoked and no
model call ever happens here (per ``tests/AGENTS.md``: no dev-machine coupling,
no external legs). The fake runner behaves *structurally* like codex — it
enumerates ``.agents/skills`` of the cwd's git root and honours the isolated
CODEX_HOME trust table — so the staging/layout logic is genuinely exercised.

Digest expectations in the canonicalization tests are recomputed with
``hashlib`` directly, so a bug in the module's own helpers cannot make its
output look correct.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

import pytest
from scripts.sdd import run_codex_carrier_probe as probe

# --------------------------------------------------------------------------- #
# synthetic repo
# --------------------------------------------------------------------------- #


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=str(repo), check=True, capture_output=True)


def _write(repo: Path, rel: str, data: bytes) -> None:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _skill_md(cid: str, description: str) -> bytes:
    return (
        f"---\nname: {cid}\ndescription: {description}\n---\n\n# {cid}\n\nbody 正文\n"
    ).encode()


DESCRIPTIONS = {
    cid: f"Synthetic description for {cid} — 触发词 {i}."
    for i, cid in enumerate(probe.REQUIRED_18)
}
# One deliberately oversized description: its predicted and observed render mode
# must both be "truncated" (the Owner-ratified mechanism-grade criterion).
DESCRIPTIONS["mj-agent-flow-diagnose"] = "diagnose trigger words. " * 60

PROJECT_SERVERS = ("alpha", "beta")


@pytest.fixture()
def synthetic_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@localhost")
    _git(repo, "config", "user.name", "t")
    _git(repo, "config", "core.autocrlf", "false")
    for cid in probe.REQUIRED_18:
        _write(repo, f".claude/skills/{cid}/SKILL.md", _skill_md(cid, DESCRIPTIONS[cid]))
    for cid in probe.BYTE_COPY_5:
        _write(repo, f".agents/skills/{cid}/SKILL.md", _skill_md(cid, DESCRIPTIONS[cid]))
    manifest_lines = ["schema_version: 1", "capabilities:"]
    for cid in probe.REQUIRED_18:
        manifest_lines += [f"  - id: {cid}", "    required: true"]
    manifest_lines += ["  - id: mj-agent-extra-optional", "    required: false"]
    _write(repo, "sdd/development-agent.yml", ("\n".join(manifest_lines) + "\n").encode())
    project_cfg = "".join(
        f'[mcp_servers.{name}]\ncommand = "cmd"\nargs = ["/c", "exit", "0"]\n\n'
        for name in PROJECT_SERVERS
    )
    _write(repo, ".codex/config.toml", project_cfg.encode())
    _write(repo, "AGENTS.md", b"# synthetic\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "synthetic tree")
    return repo


@pytest.fixture()
def user_home(tmp_path: Path, synthetic_repo: Path) -> Path:
    home = tmp_path / "user-codex-home"
    home.mkdir()
    (home / "config.toml").write_text(
        f"[projects.'{synthetic_repo}']\ntrust_level = \"trusted\"\n",
        encoding="utf-8",
    )
    return home


# --------------------------------------------------------------------------- #
# fake codex runner
# --------------------------------------------------------------------------- #

FEATURES_TEXT = "hooks                stable   true\nother                removed  false\n"
EXEC_HELP_TEXT = "--dangerously-bypass-hook-trust\n--ignore-rules\n"


def _git_root_of(cwd: Path) -> Path | None:
    node = cwd
    while True:
        if (node / ".git").exists():
            return node
        if node.parent == node:
            return None
        node = node.parent


CODEX_BUDGET = 1024  # independent literal deliberately NOT derived from the module


def _independent_description_of(md_bytes: bytes) -> str:
    # Independent of the module under test: naive single-line description scan,
    # so a parse_frontmatter regression breaks the comparison instead of
    # cancelling out on both sides (Stage-11 finding TS-03).
    match = re.search(r"^description: (.*)$", md_bytes.decode("utf-8"), re.M)
    return match.group(1) if match else ""


def _fake_prompt_input(cwd: Path) -> bytes:
    root = _git_root_of(cwd)
    entries = []
    skills_root = (root or cwd) / ".agents" / "skills"
    if skills_root.is_dir():
        for skill_dir in sorted(skills_root.iterdir()):
            md = skill_dir / "SKILL.md"
            if not md.is_file():
                continue
            desc = _independent_description_of(md.read_bytes())
            if len(desc) > CODEX_BUDGET:
                # mirror the measured codex budget contract: exact-length prefix + "..."
                desc = desc[: CODEX_BUDGET - 3] + "..."
            entries.append(f"- {skill_dir.name}: {desc} (file: {md})")
    text = "<skills_instructions>\n## Skills\n" + "\n".join(entries) + "\n"
    doc = [{"type": "message", "role": "developer", "content": [{"type": "text", "text": text}]}]
    return json.dumps(doc, ensure_ascii=False).encode("utf-8")


def _fake_mcp_list(cwd: Path, env: dict[str, str]) -> bytes:
    root = _git_root_of(cwd) or cwd
    home = Path(env.get("CODEX_HOME", ""))
    cfg = home / "config.toml"
    trusted = False
    if cfg.is_file():
        entries = probe.parse_user_trust_entries(cfg.read_text(encoding="utf-8"))
        trusted = probe.trust_entry_covering(entries, root) is not None
    servers: list[dict[str, str]] = []
    project_cfg = root / ".codex" / "config.toml"
    if trusted and project_cfg.is_file():
        for m in re.finditer(r"^\[mcp_servers\.([A-Za-z0-9_-]+)\]", project_cfg.read_text(encoding="utf-8"), re.M):
            servers.append({"name": m.group(1)})
    return json.dumps(servers).encode("utf-8")


def _fake_exec_events(stdin: bytes | None) -> bytes:
    prompt = (stdin or b"").decode("utf-8", "replace")
    lines = [json.dumps({"type": "session_configured", "msg": {"model": "fake-model-1"}})]
    # decoy: the model *claims* it will read a carrier — the text carries a real
    # matchable carrier path, so ONLY the agent_message (prose) exclusion keeps
    # this from counting as a trigger (Stage-11 finding TS-01).
    lines.append(
        json.dumps(
            {
                "type": "item.completed",
                "item": {
                    "type": "agent_message",
                    "text": "我会读取 .agents/skills/mj-agent-flow-plan/SKILL.md 并使用该技能",
                },
            }
        )
    )
    for cid in probe.REQUIRED_18:
        if cid in prompt:
            # structural signal: a command reading the carrier, Windows-style path
            command = f"pwsh -Command Get-Content '.agents\\skills\\{cid}\\SKILL.md'"
            lines.append(
                json.dumps(
                    {
                        "type": "item.completed",
                        "item": {"type": "command_execution", "command": command},
                    }
                )
            )
            break
    lines.append(json.dumps({"type": "turn_complete"}))
    return ("\n".join(lines) + "\n").encode("utf-8")


def make_fake_runner(version_rc: int = 0):
    def runner(argv, cwd, env, timeout, stdin=None):
        joined = " ".join(argv)
        if "--version" in argv:
            return probe.RunResult(version_rc, b"codex-cli 0.147.0-test\n", b"")
        if "prompt-input" in argv:
            return probe.RunResult(0, _fake_prompt_input(Path(cwd)), b"")
        if "mcp" in argv and "list" in argv:
            return probe.RunResult(0, _fake_mcp_list(Path(cwd), dict(env)), b"")
        if "features" in argv:
            return probe.RunResult(0, FEATURES_TEXT.encode(), b"")
        if "--help" in argv:
            return probe.RunResult(0, EXEC_HELP_TEXT.encode(), b"")
        if "exec" in argv:
            return probe.RunResult(0, _fake_exec_events(stdin), b"")
        raise AssertionError(f"unexpected fake codex invocation: {joined}")

    return runner


def _run_det(repo: Path, home: Path, tmp: Path, tag: str, runner=None):
    out_dir = tmp / f"out-{tag}"
    fixtures_dir = repo / "evidence" / "development-agent-v8" / "probe" / "fixtures"
    return probe.run_deterministic(
        repo_root=repo,
        out_dir=out_dir,
        local_dir=tmp / f"local-{tag}",
        fixtures_dir=fixtures_dir,
        codex_bin="codex",
        runner=runner or make_fake_runner(),
        parent_env={"PATH": "x"},
        user_codex_home=home,
        stage_parent=tmp / f"stage-{tag}",
    )


# --------------------------------------------------------------------------- #
# canonicalization / helpers
# --------------------------------------------------------------------------- #


def test_canonical_json_bytes_shape() -> None:
    data = {"b": "值", "a": [2, 1]}
    raw = probe.canonical_json_bytes(data)
    assert raw.endswith(b"}\n") and not raw.endswith(b"\n\n")
    assert b"\r" not in raw
    assert "值".encode() in raw  # ensure_ascii=false
    assert raw.index(b'"a"') < raw.index(b'"b"')


def test_digest_distinguishes_inputs() -> None:
    assert probe.digest_of({"a": 1}) != probe.digest_of({"a": 2})


def test_set_digest_matches_manual_recompute() -> None:
    mapping = {"b/p.md": "22" * 32, "a/q.md": "11" * 32}
    manual = hashlib.sha256(
        ('{\n  "a/q.md": "' + "11" * 32 + '",\n  "b/p.md": "' + "22" * 32 + '"\n}\n').encode()
    ).hexdigest()
    assert probe.set_digest(mapping) == manual


def test_make_run_id_format() -> None:
    run_id = probe.make_run_id(probe.DET_SCHEMA, "2026-08-14T09:05:06Z", "a" * 40)
    assert run_id == f"deterministic-gate-v1-20260814T090506Z-{'a' * 12}"


def test_parse_frontmatter_roundtrip() -> None:
    front = probe.parse_frontmatter(_skill_md("mj-agent-git-sync", "desc here"))
    assert front == {"name": "mj-agent-git-sync", "description": "desc here"}
    assert probe.parse_frontmatter(b"no frontmatter\n") is None
    assert probe.parse_frontmatter(b"---\nnever closed\n") is None


def test_parse_frontmatter_accepts_colon_space_in_description() -> None:
    # Real skill descriptions are plain scalars with ": " inside — not strict
    # YAML, but valid for both harness loaders. The probe must not reject them.
    desc = "Use for X. Do not use for: branch creation (use mj-agent-git-branch)."
    front = probe.parse_frontmatter(_skill_md("mj-agent-git-sync", desc))
    assert front is not None and front["description"] == desc
    wrapped = b"---\nname: n\ndescription: first line\n  second line\n---\n\nbody\n"
    front2 = probe.parse_frontmatter(wrapped)
    assert front2 == {"name": "n", "description": "first line second line"}


def test_discovery_parsers() -> None:
    text = "- mj-agent-git-push: push things (file: /x/SKILL.md)\n- other-skill: nope\n"
    assert probe.discovered_skill_names(text) == ("mj-agent-git-push",)
    assert probe.discovery_entry_body(text, "mj-agent-git-push") == "push things"
    assert probe.discovery_entry_body(text, "mj-agent-git-sync") is None


def test_classify_render_mode() -> None:
    budget = probe.DISCOVERY_BUDGET_CHARS
    short = "short description"
    assert probe.classify_render_mode(short, short) == "complete"
    long_desc = "x" * (budget + 200)
    legal = long_desc[: budget - 3] + "..."
    assert len(legal) == budget
    assert probe.classify_render_mode(long_desc, legal) == "truncated"
    # wrong cut length, missing marker, or non-prefix content are all malformed
    assert probe.classify_render_mode(long_desc, long_desc[:500] + "...") == "malformed"
    assert probe.classify_render_mode(long_desc, long_desc[:budget]) == "malformed"
    assert probe.classify_render_mode(long_desc, "y" * (budget - 3) + "...") == "malformed"
    assert probe.predicted_render_mode(short) == "complete"
    assert probe.predicted_render_mode(long_desc) == "truncated"


def test_path_safety_all_required_ids_clean() -> None:
    for cid in probe.REQUIRED_18:
        assert probe.path_safety_violations(cid) == []


def test_path_safety_rejects_bad_ids() -> None:
    assert "ID_SYNTAX" in probe.path_safety_violations("Bad_Upper")
    assert "ID_SYNTAX" in probe.path_safety_violations("..")


def test_trust_entry_covering_ancestor_and_exact(tmp_path: Path) -> None:
    entries = [(str(tmp_path), "trusted")]
    assert probe.trust_entry_covering(entries, tmp_path) is not None
    assert probe.trust_entry_covering(entries, tmp_path / "child" / "wt") is not None
    assert probe.trust_entry_covering([("/elsewhere", "trusted")], tmp_path) is None
    # a section header alone is NOT trust: untrusted / level-less entries never cover
    assert probe.trust_entry_covering([(str(tmp_path), "untrusted")], tmp_path) is None
    assert probe.trust_entry_covering([(str(tmp_path), "")], tmp_path) is None


def test_parse_user_trust_entries_reads_levels() -> None:
    cfg = (
        "[projects.'D:\\proj\\a']\ntrust_level = \"trusted\"\n\n"
        "[projects.'D:\\proj\\b']\ntrust_level = \"untrusted\"\n\n"
        "[projects.'D:\\proj\\c']\n\n"
        "[other]\ntrust_level = \"trusted\"\n"
    )
    entries = probe.parse_user_trust_entries(cfg)
    assert entries == [
        ("D:\\proj\\a", "trusted"),
        ("D:\\proj\\b", "untrusted"),
        ("D:\\proj\\c", ""),
    ]


# --------------------------------------------------------------------------- #
# deterministic leg
# --------------------------------------------------------------------------- #


def test_deterministic_pass_on_clean_tree(synthetic_repo: Path, user_home: Path, tmp_path: Path) -> None:
    fixtures_dir = synthetic_repo / "evidence" / "development-agent-v8" / "probe" / "fixtures"
    probe.emit_fixtures(synthetic_repo, fixtures_dir)
    out_path, verdict = _run_det(synthetic_repo, user_home, tmp_path, "clean")
    assert verdict == "PASS"
    doc = json.loads(out_path.read_bytes().decode("utf-8"))
    assert sorted(doc.keys()) == sorted(
        [
            "schema_version", "probe_kind", "run_id", "started_at", "completed_at",
            "repo_head", "codex_build", "cases", "verdict",
        ]
    )
    assert doc["probe_kind"] == "deterministic-gate-v1"
    assert doc["verdict"] == "PASS"
    assert len(doc["cases"]) == 70
    assert {c["status"] for c in doc["cases"]} == {"PASS"}
    case_keys = [
        "case_id", "capability_id", "surface", "fixture_id", "fixture_sha256",
        "config_sha256", "tool_version", "expected_sha256", "actual_sha256",
        "status", "evidence_sha256", "reason_code",
    ]
    for case in doc["cases"]:
        assert sorted(case.keys()) == sorted(case_keys)
        assert case["surface"] in ("skill", "hook", "rule", "config")
    # canonical serialization: re-encoding the parsed doc reproduces the file bytes
    assert probe.canonical_json_bytes(doc) == out_path.read_bytes()


def test_deterministic_detects_missing_source(synthetic_repo: Path, user_home: Path, tmp_path: Path) -> None:
    fixtures_dir = synthetic_repo / "evidence" / "development-agent-v8" / "probe" / "fixtures"
    probe.emit_fixtures(synthetic_repo, fixtures_dir)
    victim = ".claude/skills/mj-agent-git-sync/SKILL.md"
    _git(synthetic_repo, "rm", "-q", victim)
    _git(synthetic_repo, "commit", "-q", "-m", "drop source")
    out_path, verdict = _run_det(synthetic_repo, user_home, tmp_path, "missing")
    assert verdict == "FAIL"
    doc = json.loads(out_path.read_bytes().decode("utf-8"))
    failing = {c["case_id"]: c["reason_code"] for c in doc["cases"] if c["status"] != "PASS"}
    assert failing["det-02-source-present--mj-agent-git-sync"] == "MISSING_SOURCE"


def test_deterministic_detects_tampered_source_digest(synthetic_repo: Path, user_home: Path, tmp_path: Path) -> None:
    fixtures_dir = synthetic_repo / "evidence" / "development-agent-v8" / "probe" / "fixtures"
    probe.emit_fixtures(synthetic_repo, fixtures_dir)
    victim = synthetic_repo / ".claude/skills/mj-agent-git-push/SKILL.md"
    victim.write_bytes(_skill_md("mj-agent-git-push", "tampered description"))
    _git(synthetic_repo, "add", "-A")
    _git(synthetic_repo, "commit", "-q", "-m", "tamper")
    out_path, verdict = _run_det(synthetic_repo, user_home, tmp_path, "tamper")
    assert verdict == "FAIL"
    doc = json.loads(out_path.read_bytes().decode("utf-8"))
    tampered = [c for c in doc["cases"] if c["case_id"] == "det-02-source-present--mj-agent-git-push"]
    assert tampered[0]["status"] == "FAIL"
    # a pure digest mismatch must be named as such, not conflated with a
    # frontmatter defect (Stage-11 finding TS-02)
    assert tampered[0]["reason_code"] == "SOURCE_DIGEST_MISMATCH"
    # the byte-copy artifact now also disagrees with its source
    art = [c for c in doc["cases"] if c["case_id"] == "det-06-artifact-digest--mj-agent-git-push"]
    assert art[0]["status"] == "FAIL"
    assert art[0]["reason_code"] == "ARTIFACT_DIGEST_MISMATCH"


def test_deterministic_blocked_when_codex_unavailable(synthetic_repo: Path, user_home: Path, tmp_path: Path) -> None:
    fixtures_dir = synthetic_repo / "evidence" / "development-agent-v8" / "probe" / "fixtures"
    probe.emit_fixtures(synthetic_repo, fixtures_dir)
    out_path, verdict = _run_det(
        synthetic_repo, user_home, tmp_path, "blocked", runner=make_fake_runner(version_rc=9)
    )
    assert verdict == "BLOCKED_PREREQUISITE"
    doc = json.loads(out_path.read_bytes().decode("utf-8"))
    assert doc["codex_build"] == "unavailable"
    assert [c["reason_code"] for c in doc["cases"]] == ["CODEX_UNAVAILABLE"]


def test_deterministic_trust_absent_fails_route_case(synthetic_repo: Path, tmp_path: Path) -> None:
    fixtures_dir = synthetic_repo / "evidence" / "development-agent-v8" / "probe" / "fixtures"
    probe.emit_fixtures(synthetic_repo, fixtures_dir)
    bare_home = tmp_path / "home-no-trust"
    bare_home.mkdir()
    (bare_home / "config.toml").write_text("[projects.'/elsewhere']\ntrust_level = \"trusted\"\n", encoding="utf-8")
    out_path, verdict = _run_det(synthetic_repo, bare_home, tmp_path, "notrust")
    doc = json.loads(out_path.read_bytes().decode("utf-8"))
    by_id = {c["case_id"]: c for c in doc["cases"]}
    assert by_id["det-08-trust--user-layer-entry"]["status"] == "FAIL"
    assert by_id["det-08-trust--user-layer-entry"]["reason_code"] == "TRUST_ENTRY_ABSENT"
    # untrusted user layer also means the real project config cannot load
    assert by_id["det-08-trust--real-project-config-loaded"]["status"] == "FAIL"
    assert verdict == "FAIL"


# --------------------------------------------------------------------------- #
# telemetry leg
# --------------------------------------------------------------------------- #


def _mini_corpus(repo: Path) -> Path:
    fixtures_dir = repo / "evidence" / "development-agent-v8" / "probe" / "fixtures"
    fixtures_dir.mkdir(parents=True, exist_ok=True)
    corpus = {
        "schema_version": 1,
        "corpus_id": "test-corpus",
        "prompts": [
            {
                "capability_id": "mj-agent-git-commit",
                "prompt_id": "mj-agent-git-commit--positive",
                "kind": "positive",
                "text": "please mj-agent-git-commit now",
            },
            {
                "capability_id": "mj-agent-git-commit",
                "prompt_id": "mj-agent-git-commit--near-negative",
                "kind": "near-negative",
                "text": "just explain something unrelated",
            },
            {
                "capability_id": "mj-agent-git-push",
                "prompt_id": "mj-agent-git-push--positive",
                "kind": "positive",
                "text": "invoke mj-agent-git-sync instead",
            },
        ],
    }
    path = fixtures_dir / probe.CORPUS_NAME
    path.write_bytes(probe.canonical_json_bytes(corpus))
    return path


def test_telemetry_shape_and_classification(synthetic_repo: Path, user_home: Path, tmp_path: Path) -> None:
    corpus_path = _mini_corpus(synthetic_repo)
    out_path = probe.run_telemetry(
        repo_root=synthetic_repo,
        out_dir=tmp_path / "tel-out",
        local_dir=tmp_path / "tel-local",
        fixtures_dir=corpus_path.parent,
        codex_bin="codex",
        runner=make_fake_runner(),
        parent_env={"PATH": "x"},
        user_codex_home=user_home,
        stage_parent=tmp_path / "tel-stage",
    )
    doc = json.loads(out_path.read_bytes().decode("utf-8"))
    assert sorted(doc.keys()) == sorted(
        [
            "schema_version", "probe_kind", "run_id", "started_at", "completed_at",
            "repo_head", "codex_build", "model_id", "sampling_config",
            "prompt_fixture_sha256", "repetitions", "observations", "warnings",
        ]
    )
    assert doc["probe_kind"] == "model-telemetry-v1"
    assert doc["repetitions"] == 3
    assert "verdict" not in doc and "cases" not in doc  # AC-09: structurally verdict-free
    assert sorted(doc["sampling_config"].keys()) == sorted(
        ["reasoning_effort", "temperature", "seed", "cli_args_sha256", "project_config_sha256"]
    )
    assert doc["sampling_config"]["temperature"] is None
    assert doc["sampling_config"]["seed"] is None
    assert doc["model_id"] == "fake-model-1"

    obs = doc["observations"]
    assert len(obs) == 9  # 3 prompts x 3 runs
    for entry in obs:
        assert sorted(entry.keys()) == sorted(
            ["capability_id", "prompt_id", "run_index", "observed_class", "warning_codes"]
        )
        assert entry["observed_class"] in probe.OBSERVED_CLASSES
    keys = [(o["capability_id"], o["prompt_id"], o["run_index"]) for o in obs]
    assert keys == sorted(keys)
    for pid, expected in (
        ("mj-agent-git-commit--positive", "TRIGGERED_TARGET"),
        ("mj-agent-git-commit--near-negative", "NOT_TRIGGERED"),
        ("mj-agent-git-push--positive", "TRIGGERED_OTHER"),
    ):
        classes = {o["observed_class"] for o in obs if o["prompt_id"] == pid}
        assert classes == {expected}
    # 3 runs per (capability, prompt), run_index exactly 1..3
    for pid in {o["prompt_id"] for o in obs}:
        idx = sorted(o["run_index"] for o in obs if o["prompt_id"] == pid)
        assert idx == [1, 2, 3]

    # metadata only: the prompt text never enters the tracked evidence
    raw = out_path.read_bytes().decode("utf-8")
    assert "please mj-agent-git-commit now" not in raw
    assert "unrelated" not in raw

    # prompt_fixture_sha256 follows the §2.7 wire over the corpus file
    rel = corpus_path.resolve().relative_to(synthetic_repo).as_posix()
    manual = probe.set_digest({rel: hashlib.sha256(corpus_path.read_bytes()).hexdigest()})
    assert doc["prompt_fixture_sha256"] == manual


def test_telemetry_fail_closed_on_existing_output(
    synthetic_repo: Path, user_home: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _mini_corpus(synthetic_repo)
    monkeypatch.setattr(probe, "utc_now_rfc3339", lambda: "2026-08-14T00:00:00Z")
    kwargs = dict(
        repo_root=synthetic_repo,
        out_dir=tmp_path / "tel-out2",
        local_dir=tmp_path / "tel-local2",
        fixtures_dir=synthetic_repo / "evidence" / "development-agent-v8" / "probe" / "fixtures",
        codex_bin="codex",
        runner=make_fake_runner(),
        parent_env={"PATH": "x"},
        user_codex_home=user_home,
        stage_parent=tmp_path / "tel-stage2",
    )
    probe.run_telemetry(**kwargs)
    # pinned timestamp + same head -> identical run id; the second write must fail
    # closed with exit status 2 (a bare-string SystemExit would exit 1)
    with pytest.raises(SystemExit) as excinfo:
        probe.run_telemetry(**kwargs)
    assert excinfo.value.code == 2


def test_telemetry_rejects_duplicate_corpus_entry(
    synthetic_repo: Path, user_home: Path, tmp_path: Path
) -> None:
    fixtures_dir = synthetic_repo / "evidence" / "development-agent-v8" / "probe" / "fixtures"
    fixtures_dir.mkdir(parents=True, exist_ok=True)
    entry = {
        "capability_id": "mj-agent-git-commit",
        "prompt_id": "mj-agent-git-commit--positive",
        "kind": "positive",
        "text": "x",
    }
    (fixtures_dir / probe.CORPUS_NAME).write_bytes(
        probe.canonical_json_bytes({"schema_version": 1, "prompts": [entry, dict(entry)]})
    )
    with pytest.raises(SystemExit) as excinfo:
        probe.run_telemetry(
            repo_root=synthetic_repo,
            out_dir=tmp_path / "dup-out",
            local_dir=tmp_path / "dup-local",
            fixtures_dir=fixtures_dir,
            codex_bin="codex",
            runner=make_fake_runner(),
            parent_env={"PATH": "x"},
            user_codex_home=user_home,
            stage_parent=tmp_path / "dup-stage",
        )
    assert excinfo.value.code == 2


def test_telemetry_project_config_sha_is_hex_not_null(
    synthetic_repo: Path, user_home: Path, tmp_path: Path
) -> None:
    # Stage-11 finding SC-01: every *_sha256 must be 64-hex; absent project
    # config is the domain-separated absent-value digest, never raw null
    _mini_corpus(synthetic_repo)
    out_path = probe.run_telemetry(
        repo_root=synthetic_repo,
        out_dir=tmp_path / "hex-out",
        local_dir=tmp_path / "hex-local",
        fixtures_dir=synthetic_repo / "evidence" / "development-agent-v8" / "probe" / "fixtures",
        codex_bin="codex",
        runner=make_fake_runner(),
        parent_env={"PATH": "x"},
        user_codex_home=user_home,
        stage_parent=tmp_path / "hex-stage",
    )
    doc = json.loads(out_path.read_bytes().decode("utf-8"))
    value = doc["sampling_config"]["project_config_sha256"]
    assert isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value)
    assert value == probe.digest_of(None)


def test_classify_events_unparseable_variants() -> None:
    assert probe.classify_events(b"", "mj-agent-git-commit") == ("UNPARSEABLE", ["EVENT_STREAM_EMPTY"])
    cls, warns = probe.classify_events(b"not json at all\n", "mj-agent-git-commit")
    assert cls == "UNPARSEABLE" and warns == ["EVENT_STREAM_MALFORMED"]


def test_classify_events_structured_field_arm() -> None:
    # the `value == cid` structural arm (Stage-11 finding TS-04): a dedicated
    # skill-invocation event naming the capability id in a structured field
    event = json.dumps(
        {"type": "item.completed", "item": {"type": "tool_use", "skill": "mj-agent-git-commit"}}
    ).encode()
    assert probe.classify_events(event, "mj-agent-git-commit")[0] == "TRIGGERED_TARGET"
    assert probe.classify_events(event, "mj-agent-git-push")[0] == "TRIGGERED_OTHER"


def test_classify_events_ignores_prose_self_report() -> None:
    # an agent_message carrying a REAL carrier path must still not count
    prose = json.dumps(
        {
            "type": "item.completed",
            "item": {"type": "agent_message", "text": "reading .agents/skills/mj-agent-git-commit/SKILL.md"},
        }
    ).encode()
    assert probe.classify_events(prose, "mj-agent-git-commit")[0] == "NOT_TRIGGERED"


def test_discovery_budget_is_the_measured_1024() -> None:
    # Owner-ratified measured contract on codex-cli 0.147.0; an accidental
    # constant edit must fail loudly, independent of any derivation
    assert probe.DISCOVERY_BUDGET_CHARS == 1024


def test_sanitized_child_env_filters_credentials() -> None:
    parent = {
        "PATH": "p",
        "GITHUB_TOKEN": "secret",
        "MJ_AGENT_PG_MEMORY_DEV_URL": "postgres://x",
        "ARK_API_KEY": "k",
    }
    child = probe.sanitized_child_env(parent, "H")
    assert child["PATH"] == "p" and child["CODEX_HOME"] == "H"
    assert "GITHUB_TOKEN" not in child
    assert "MJ_AGENT_PG_MEMORY_DEV_URL" not in child
    assert "ARK_API_KEY" not in child
