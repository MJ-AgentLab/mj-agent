"""Contract tests for the PR-P1b leg of ``scripts/sdd/run_codex_carrier_probe.py``.

Epic #499 plan §5.6: P1b probes the output of the EXACT production renderer /
module / version rather than raw source candidates. These tests are offline —
the real ``codex`` binary is never invoked and no model call happens (per
``tests/AGENTS.md``) — and they never mutate the live tree.

The `_record_p1b_cases` battery is deliberately driven from hand-built
``CandidateRender`` values: every new deterministic case gets an explicit
NEGATIVE control proving it can actually report FAIL. A case family that can
only ever pass is evidence of nothing, and the whole point of P1b is that its
``PASS`` verdict is load-bearing (it is what unblocks PR-C0).
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest
from scripts.sdd import run_codex_carrier_probe as probe

REPO_ROOT = Path(__file__).resolve().parents[2]


# --------------------------------------------------------------------------- #
# frontmatter scalar unquoting (PR-P1b Stage 3 finding)
# --------------------------------------------------------------------------- #


def test_unquote_plain_scalar_is_identity() -> None:
    raw = "Stage 0 task intake: convert a requirement; use for 评估任务."
    assert probe.unquote_frontmatter_scalar(raw) == raw


def test_unquote_double_quoted_scalar_returns_parsed_value() -> None:
    value = 'Validate docs; use when asked to "check docs", 检查文档格式.'
    literal = json.dumps(value, ensure_ascii=False)
    assert literal.startswith('"') and literal.endswith('"')
    assert probe.unquote_frontmatter_scalar(literal) == value
    # the quotes are exactly the 2-character difference the smoke run measured
    assert len(literal) - len(value) >= 2


def test_unquote_leaves_undecodable_quoted_literal_alone() -> None:
    # opens and closes with a quote but is not a valid JSON string: guessing
    # would be worse than reporting the literal as-is.
    raw = '"unterminated \\q escape"'
    assert probe.unquote_frontmatter_scalar(raw) == raw


def test_unquote_ignores_short_and_unquoted() -> None:
    assert probe.unquote_frontmatter_scalar('"') == '"'
    assert probe.unquote_frontmatter_scalar("") == ""
    assert probe.unquote_frontmatter_scalar('"opens only') == '"opens only'


def test_frontmatter_description_unquotes_a_rendered_carrier() -> None:
    value = "Stage 10 local verification; use for 本地验证, 跑测试."
    blob = (
        "---\nname: mj-agent-flow-verify\ndescription: "
        + json.dumps(value, ensure_ascii=False)
        + "\n---\n\nbody\n"
    ).encode()
    assert probe.frontmatter_description(blob) == value


def test_frontmatter_description_rejects_malformed() -> None:
    assert probe.frontmatter_description(b"no frontmatter here\n") is None


def test_no_live_source_uses_a_quoted_description() -> None:
    """P1a semantics are unchanged by the unquoting step ONLY while no raw
    source carries a double-quoted description. Pin that premise: if a future
    source starts quoting, P1a's published expectations would silently shift."""
    head = probe.git_head(REPO_ROOT)
    quoted = []
    for cid in probe.REQUIRED_18:
        # git blob, not the worktree file: `* text=auto` gives Windows checkouts
        # CRLF, which the frontmatter parser rejects outright.
        blob = probe.git_blob_bytes(
            REPO_ROOT, head, f"{probe.SOURCE_ROOT}/{cid}/SKILL.md"
        )
        front = probe.parse_frontmatter(blob)
        assert front is not None, cid
        raw = front["description"]
        if raw.startswith('"') and raw.endswith('"'):
            quoted.append(cid)
    assert quoted == []


# --------------------------------------------------------------------------- #
# candidate manifest derivation
# --------------------------------------------------------------------------- #


class _FakeWorkflow:
    def __init__(self, workflow_id: str, capability_id: str) -> None:
        self.workflow_id = workflow_id
        self.capability_id = capability_id


class _FakeRegistry:
    def __init__(self, pairs: dict[str, str]) -> None:
        self.workflows = {
            wid: _FakeWorkflow(wid, cid) for wid, cid in pairs.items()
        }


def _manifest(caps: list[dict[str, Any]]) -> dict[str, Any]:
    return {"schema_version": 1, "capabilities": caps}


def test_derive_candidate_manifest_partitions_by_registry_and_projection() -> None:
    manifest = _manifest(
        [
            {"id": "mj-agent-git-sync", "projection": "project", "required": True,
             "codex": {"support_mode": "adapter-backed"}},
            {"id": "mj-agent-git-pr", "projection": "after-neutralization",
             "required": False, "codex": {"support_mode": "adapter-backed"}},
            {"id": "mj-agent-doc-author", "projection": "after-neutralization",
             "required": False, "codex": {"support_mode": "adapter-backed"}},
            {"id": "mj-agent-infra-app-start", "projection": "never",
             "required": False},
        ]
    )
    registry = _FakeRegistry({"git-pr": "mj-agent-git-pr"})
    candidate = probe.derive_candidate_manifest(manifest, registry)

    assert candidate["schema_version"] == 2
    assert candidate["codex_readme_template_version"] == 1
    by_id = {c["id"]: c for c in candidate["capabilities"]}

    assert by_id["mj-agent-git-sync"]["codex_carrier"] == "byte-copy"
    assert "carrier_binding" not in by_id["mj-agent-git-sync"]
    assert by_id["mj-agent-git-sync"]["codex"]["support_mode"] == "native"

    pr = by_id["mj-agent-git-pr"]
    assert pr["codex_carrier"] == "translated"
    assert pr["carrier_binding"] == {"workflow_id": "git-pr"}
    assert pr["required"] is True
    assert pr["projection"] == "project"
    assert pr["codex"]["support_mode"] == "native"

    for nid in ("mj-agent-doc-author", "mj-agent-infra-app-start"):
        assert by_id[nid]["codex_carrier"] == "none"
        assert "carrier_binding" not in by_id[nid]
        # a non-carrier row keeps its projection and its support mode untouched
        assert by_id[nid]["projection"] != "project"

    assert probe.candidate_partition(candidate) == {
        "byte-copy": ["mj-agent-git-sync"],
        "translated": ["mj-agent-git-pr"],
    }


def test_derive_candidate_manifest_drops_stale_carrier_binding() -> None:
    manifest = _manifest(
        [{"id": "mj-agent-git-sync", "projection": "project",
          "carrier_binding": {"workflow_id": "stale"}}]
    )
    candidate = probe.derive_candidate_manifest(manifest, _FakeRegistry({}))
    assert "carrier_binding" not in candidate["capabilities"][0]


def test_derive_candidate_manifest_does_not_mutate_the_input() -> None:
    manifest = _manifest([{"id": "mj-agent-git-sync", "projection": "project"}])
    probe.derive_candidate_manifest(manifest, _FakeRegistry({}))
    assert manifest["schema_version"] == 1
    assert "codex_carrier" not in manifest["capabilities"][0]


def test_candidate_partition_sorts_and_ignores_none_rows() -> None:
    candidate = {
        "capabilities": [
            {"id": "mj-agent-z", "codex_carrier": "translated"},
            {"id": "mj-agent-a", "codex_carrier": "translated"},
            {"id": "mj-agent-m", "codex_carrier": "none"},
            {"id": "mj-agent-b", "codex_carrier": "byte-copy"},
        ]
    }
    assert probe.candidate_partition(candidate) == {
        "byte-copy": ["mj-agent-b"],
        "translated": ["mj-agent-a", "mj-agent-z"],
    }


def test_candidate_manifest_violations_formats_a_real_violation() -> None:
    """Drive the REAL checker, not a hand-built CandidateRender.

    The first version of this suite injected a pre-formatted violation string
    straight into CandidateRender.manifest_violations, so it exercised the case
    recorder while never once calling candidate_manifest_violations(). That let a
    wrong attribute name (`v.capability`, where the production Violation dataclass
    exposes `capability_id`) survive: the formatter only evaluates when at least
    one error-severity violation exists, i.e. exactly in the situation det-11 is
    supposed to report. This test executes the formatting path.
    """
    mods = probe.production_modules()
    invalid = {
        "schema_version": 2,
        "codex_readme_template_version": 1,
        "capabilities": [
            # translated with no carrier_binding -> DA092 (error severity)
            {"id": "mj-agent-git-pr", "projection": "project", "required": True,
             "codex_carrier": "translated"},
        ],
    }
    violations = probe.candidate_manifest_violations(invalid, mods)
    assert violations, "an invalid candidate must produce violations, not an empty list"
    assert all(isinstance(v, str) for v in violations)
    assert any(v.startswith("DA092:") for v in violations), violations
    assert violations == sorted(violations)


def test_candidate_manifest_violations_is_empty_for_the_live_candidate(
    tmp_path: Path,
) -> None:
    """The other half of the control: the real derived candidate is clean, so
    det-11's PASS in the published evidence is a genuine result and not the
    empty-list-by-crash-avoidance that the bug above would have produced."""
    render = probe.build_candidate_render(
        REPO_ROOT, probe.git_head(REPO_ROOT), tmp_path
    )
    assert render.manifest_violations == []


def test_candidate_surface_maps_lock_surface_members() -> None:
    assert probe.candidate_surface({"surface_members": ["mcp"]}) == "config"
    assert probe.candidate_surface({"surface_members": ["skills"]}) == "skill"
    assert probe.candidate_surface({}) == "skill"


def test_staged_artifacts_never_include_the_rendered_codex_config() -> None:
    """A staged throwaway project must not be handed a route to spawn the real
    MCP servers (several of which are database-backed), and the telemetry leg's
    `project_config_sha256` is only honest while no project config is present."""
    outputs = {
        ".agents/skills/mj-agent-git-pr/SKILL.md": b"a",
        ".agents/README.md": b"b",
        ".codex/config.toml": b"[mcp_servers.pg-mj-agent-memory-dev]\n",
    }
    staged = probe.staged_skill_artifacts(outputs)
    assert set(staged) == {
        ".agents/skills/mj-agent-git-pr/SKILL.md",
        ".agents/README.md",
    }
    assert not any(path.startswith(".codex/") for path in staged)


def test_live_render_has_a_codex_config_that_staging_must_drop(tmp_path: Path) -> None:
    """Guard the premise of the test above: if the production render ever stopped
    emitting a project config, the filter would be silently protecting nothing."""
    render = probe.build_candidate_render(
        REPO_ROOT, probe.git_head(REPO_ROOT), tmp_path
    )
    assert ".codex/config.toml" in render.outputs
    assert ".codex/config.toml" not in probe.staged_skill_artifacts(render.outputs)


# --------------------------------------------------------------------------- #
# _record_p1b_cases — one negative control per case family
# --------------------------------------------------------------------------- #


def _render(**overrides: Any) -> probe.CandidateRender:
    outputs = {
        ".agents/skills/mj-agent-git-pr/SKILL.md": b"translated carrier\n",
        ".codex/config.toml": b"[mcp_servers.x]\n",
    }
    entries = {
        ".agents/skills/mj-agent-git-pr/SKILL.md": {
            "entry_kind": "skill-translated", "surface_members": ["skills"]},
        ".codex/config.toml": {
            "entry_kind": "codex-config-mcp", "surface_members": ["mcp"]},
    }
    base = {
        "outputs": outputs,
        "entries": entries,
        "partition": {
            "byte-copy": sorted(probe.BYTE_COPY_5),
            "translated": sorted(probe.TRANSLATED_13),
        },
        "manifest_violations": [],
        "renderer_identity": {
            "m": {"relpath": "scripts/sdd/_common/skill_renderer.py",
                  "imported_sha256": "a" * 64, "blob_sha256": "a" * 64,
                  "renderer_version": 1}
        },
        "input_sha256": {"sdd/development-agent.yml": "b" * 64},
        "deterministic": True,
        "candidate_manifest_slice_sha256": "c" * 64,
    }
    base.update(overrides)
    return probe.CandidateRender(**base)  # type: ignore[arg-type]


def _fixture_for(render: probe.CandidateRender) -> dict[str, Any]:
    output_shas = {p: probe.sha256_hex(d) for p, d in render.outputs.items()}
    # Deep copy: a fixture that ALIASES the render's own dicts would let a test
    # "tamper with the fixture" and silently tamper with the observation too,
    # making the two sides agree again and the negative control pass vacuously.
    return json.loads(
        json.dumps(
            {
                "candidate_output_sha256": output_shas,
                "candidate_set_sha256": probe.set_digest(output_shas),
                "renderer_modules": render.renderer_identity,
                "render_input_sha256": render.input_sha256,
            }
        )
    )


def _run_cases(
    render: probe.CandidateRender, fixture: dict[str, Any] | None = None
) -> dict[str, dict[str, Any]]:
    rec = probe.CaseRecorder(Path(__file__).parent / "__unused__", "codex-test")
    probe._record_p1b_cases(
        rec, fixture if fixture is not None else _fixture_for(render),
        "fid", "f" * 64, render,
    )
    return {c["case_id"]: c for c in rec.cases}


@pytest.fixture(autouse=True)
def _no_local_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """CaseRecorder makes its local dir on construction; keep it in tmp_path."""
    monkeypatch.setattr(
        probe.CaseRecorder, "__init__",
        lambda self, local_dir, codex_build: (
            setattr(self, "cases", []),
            setattr(self, "local_dir", tmp_path / "local"),
            setattr(self, "codex_build", codex_build),
            (tmp_path / "local").mkdir(parents=True, exist_ok=True),
        )[0],
    )


def test_p1b_cases_all_pass_on_a_matching_render() -> None:
    cases = _run_cases(_render())
    assert {c["status"] for c in cases.values()} == {"PASS"}
    # every family is actually represented — an empty battery would also have
    # an all-PASS status set.
    assert {cid.split("--")[0] for cid in cases} == {
        "det-11-candidate-manifest-v2-schema",
        "det-12-renderer-identity",
        "det-13-render-exact-byte",
        "det-14-render-determinism",
        "det-15-candidate-set-digest",
        "det-16-carrier-partition",
        "det-17-render-inputs",
    }
    assert len([c for c in cases if c.startswith("det-13-")]) == 2


def test_det11_fails_on_candidate_manifest_violation() -> None:
    cases = _run_cases(_render(manifest_violations=["DA092:mj-agent-git-pr:no binding"]))
    case = cases["det-11-candidate-manifest-v2-schema"]
    assert case["status"] == "FAIL"
    assert case["reason_code"] == "CANDIDATE_MANIFEST_INVALID"


def test_det12_fails_when_the_module_is_not_the_frozen_one() -> None:
    render = _render(
        renderer_identity={
            "m": {"relpath": "scripts/sdd/_common/skill_renderer.py",
                  "imported_sha256": "a" * 64, "blob_sha256": "d" * 64,
                  "renderer_version": 1}
        }
    )
    # the fixture agrees with what was imported, so only the blob comparison can
    # catch this: a locally edited renderer must not be able to certify itself.
    cases = _run_cases(render, _fixture_for(render))
    case = cases["det-12-renderer-identity--m"]
    assert case["status"] == "FAIL"
    assert case["reason_code"] == "RENDERER_MODULE_NOT_FROZEN"


def test_det12_fails_on_renderer_version_drift() -> None:
    render = _render()
    fixture = _fixture_for(render)
    fixture["renderer_modules"] = {
        "m": {**render.renderer_identity["m"], "renderer_version": 2}
    }
    case = _run_cases(render, fixture)["det-12-renderer-identity--m"]
    assert case["status"] == "FAIL"
    assert case["reason_code"] == "RENDERER_IDENTITY_MISMATCH"


def test_det12_reports_a_module_that_dropped_out_of_the_pipeline() -> None:
    """A pinned module vanishing must FAIL, not silently emit zero cases."""
    render = _render()
    fixture = _fixture_for(render)
    fixture["renderer_modules"]["scripts.sdd.agents_sync"] = {
        "relpath": "scripts/sdd/agents_sync.py",
        "imported_sha256": "e" * 64,
        "blob_sha256": "e" * 64,
        "renderer_version": None,
    }
    case = _run_cases(render, fixture)[
        "det-12-renderer-identity--scripts.sdd.agents_sync"
    ]
    assert case["status"] == "FAIL"
    assert case["reason_code"] == "RENDERER_MODULE_ABSENT"


def test_renderer_identity_covers_every_production_module(tmp_path: Path) -> None:
    """det-12 must pin the whole render pipeline, not only the three modules that
    happen to declare RENDERER_VERSION. agents_sync emits the 5 byte-copy carriers
    verbatim and derives every output path; if it were unpinned, a locally edited
    engine would certify its own drift, because the fixture is emitted from the
    same working tree the check then runs against."""
    head = probe.git_head(REPO_ROOT)
    mods = probe.production_modules()
    identity = probe.renderer_identity(REPO_ROOT, head, mods)

    assert set(identity) == {m.__name__ for m in mods}
    assert "scripts.sdd.agents_sync" in identity
    assert "scripts.sdd._common.projection_loader" in identity
    assert "scripts.sdd.check_development_agent" in identity
    assert "scripts.sdd.check_agents_projection" in identity
    for name, ident in identity.items():
        assert ident["imported_sha256"] == ident["blob_sha256"], name
        assert len(ident["imported_sha256"]) == 64
        assert ident["relpath"].startswith("scripts/sdd/")
    # only the three renderer output-class modules carry a RENDERER_VERSION
    versioned = {n for n, i in identity.items() if i["renderer_version"] is not None}
    assert versioned == {
        "scripts.sdd._common.skill_renderer",
        "scripts.sdd._common.codex_readme_renderer",
        "scripts.sdd._common.codex_config_renderer",
    }


def test_det13_fails_on_a_changed_output_byte() -> None:
    render = _render()
    fixture = _fixture_for(render)
    key = ".agents/skills/mj-agent-git-pr/SKILL.md"
    fixture["candidate_output_sha256"][key] = "0" * 64
    case = _run_cases(render, fixture)[f"det-13-render-exact-byte--{key}"]
    assert case["status"] == "FAIL"
    assert case["reason_code"] == "CANDIDATE_DIGEST_MISMATCH"
    assert case["capability_id"] == "mj-agent-git-pr"
    assert case["surface"] == "skill"


def test_det13_reports_an_output_the_fixture_expected_but_the_render_dropped() -> None:
    render = _render()
    fixture = _fixture_for(render)
    fixture["candidate_output_sha256"][".agents/README.md"] = "1" * 64
    case = _run_cases(render, fixture)["det-13-render-exact-byte--.agents/README.md"]
    assert case["status"] == "FAIL"
    assert case["reason_code"] == "CANDIDATE_OUTPUT_MISSING"


def test_det13_maps_the_mcp_output_onto_the_config_surface() -> None:
    case = _run_cases(_render())["det-13-render-exact-byte--.codex/config.toml"]
    assert case["surface"] == "config"
    assert case["capability_id"] is None


def test_det14_fails_when_two_renders_diverge() -> None:
    case = _run_cases(_render(deterministic=False))["det-14-render-determinism"]
    assert case["status"] == "FAIL"
    assert case["reason_code"] == "RENDER_NON_DETERMINISTIC"


def test_det15_fails_on_set_digest_drift() -> None:
    render = _render()
    fixture = _fixture_for(render)
    fixture["candidate_set_sha256"] = "2" * 64
    case = _run_cases(render, fixture)["det-15-candidate-set-digest"]
    assert case["status"] == "FAIL"
    assert case["reason_code"] == "CANDIDATE_SET_DIGEST_MISMATCH"


def test_det16_fails_when_a_capability_lands_in_both_halves() -> None:
    both = sorted(probe.BYTE_COPY_5) + [probe.TRANSLATED_13[0]]
    case = _run_cases(
        _render(partition={"byte-copy": sorted(both),
                           "translated": sorted(probe.TRANSLATED_13)})
    )["det-16-carrier-partition"]
    assert case["status"] == "FAIL"
    assert case["reason_code"] == "CARRIER_PARTITION_MISMATCH"


def test_det16_fails_when_a_required_carrier_is_missing() -> None:
    case = _run_cases(
        _render(partition={"byte-copy": sorted(probe.BYTE_COPY_5),
                           "translated": sorted(probe.TRANSLATED_13[1:])})
    )["det-16-carrier-partition"]
    assert case["status"] == "FAIL"


def test_det17_fails_on_render_input_drift() -> None:
    render = _render()
    fixture = _fixture_for(render)
    fixture["render_input_sha256"] = {"sdd/development-agent.yml": "3" * 64}
    case = _run_cases(render, fixture)["det-17-render-inputs"]
    assert case["status"] == "FAIL"
    assert case["reason_code"] == "RENDER_INPUT_MISMATCH"


# --------------------------------------------------------------------------- #
# staging with explicit production-rendered artifacts
# --------------------------------------------------------------------------- #


def test_stage_candidate_project_writes_supplied_artifact_bytes(tmp_path: Path) -> None:
    artifacts = {
        ".agents/skills/mj-agent-git-pr/SKILL.md": b"---\nname: x\n---\nrendered\n",
        ".agents/README.md": b"readme\n",
        ".codex/config.toml": b"[mcp_servers.y]\n",
    }
    layout = probe.stage_candidate_project(
        tmp_path / "unused-repo", "HEAD", tmp_path / "stage",
        artifacts=artifacts, prefix="p1b-test-",
    )
    for rel, data in artifacts.items():
        assert (layout.root / rel).read_bytes() == data
    # only skill carriers enter the candidate digest map
    assert set(layout.candidate_shas) == {"mj-agent-git-pr"}
    assert layout.candidate_shas["mj-agent-git-pr"] == probe.sha256_hex(
        artifacts[".agents/skills/mj-agent-git-pr/SKILL.md"]
    )
    # the layout is complete: nested cwd, linked worktree, both isolated homes
    assert layout.nested.is_dir()
    assert layout.worktree.is_dir()
    assert (layout.worktree / ".agents/skills/mj-agent-git-pr/SKILL.md").is_file()
    assert not (layout.home_empty / "config.toml").exists()
    assert "trust_level" in (layout.home_trusted / "config.toml").read_text(
        encoding="utf-8"
    )


def test_stage_without_artifacts_still_uses_source_blobs(tmp_path: Path) -> None:
    """The P1a path must be untouched by the artifacts parameter."""
    repo = tmp_path / "repo"
    repo.mkdir()
    for args in (("init", "-q"), ("config", "user.email", "t@l"),
                 ("config", "user.name", "t"), ("config", "core.autocrlf", "false")):
        subprocess.run(["git", *args], cwd=str(repo), check=True, capture_output=True)
    src = repo / probe.SOURCE_ROOT / "mj-agent-git-sync" / "SKILL.md"
    src.parent.mkdir(parents=True)
    src.write_bytes(b"---\nname: mj-agent-git-sync\ndescription: d\n---\nbody\n")
    subprocess.run(["git", "add", "-A"], cwd=str(repo), check=True, capture_output=True)
    subprocess.run(["git", "commit", "-q", "-m", "x"], cwd=str(repo), check=True,
                   capture_output=True)
    head = probe.git_head(repo)
    layout = probe.stage_candidate_project(
        repo, head, tmp_path / "stage", capability_ids=("mj-agent-git-sync",),
    )
    staged = layout.root / probe.ARTIFACT_ROOT / "mj-agent-git-sync" / "SKILL.md"
    assert staged.read_bytes() == src.read_bytes()


# --------------------------------------------------------------------------- #
# rev resolution
# --------------------------------------------------------------------------- #


def test_resolve_rev_returns_a_full_commit_sha() -> None:
    head = probe.git_head(REPO_ROOT)
    assert probe.resolve_rev(REPO_ROOT, "HEAD") == head
    assert probe.resolve_rev(REPO_ROOT, head[:12]) == head
    assert len(head) == 40


# --------------------------------------------------------------------------- #
# end-to-end: the live tree still renders a complete candidate set
# --------------------------------------------------------------------------- #


def test_build_candidate_render_on_the_live_tree(tmp_path: Path) -> None:
    """The production v2 path renders the full candidate carrier set from the
    committed typed sources, deterministically, with a schema-valid candidate
    manifest. Counts are derived from the registry, never hardcoded (AC-04)."""
    head = probe.git_head(REPO_ROOT)
    render = probe.build_candidate_render(REPO_ROOT, head, tmp_path)

    mods = probe.production_modules()
    registry = mods.skill_renderer.load_workflow_registry(
        probe.git_blob_bytes(
            REPO_ROOT, head, mods.skill_renderer.WORKFLOW_REGISTRY_RELPATH
        ).decode("utf-8")
    )
    expected_translated = len(registry.workflows)

    assert render.manifest_violations == []
    assert render.deterministic is True
    assert len(render.partition["translated"]) == expected_translated
    assert render.partition["byte-copy"]
    assert not set(render.partition["byte-copy"]) & set(render.partition["translated"])

    carriers = render.partition["byte-copy"] + render.partition["translated"]
    for cid in carriers:
        key = f"{probe.ARTIFACT_ROOT}/{cid}/SKILL.md"
        assert key in render.outputs, key
        assert render.entries[key]["owner"] == f"capability:{cid}"
    assert ".agents/README.md" in render.outputs

    # every rendered carrier is loadable and fits the Codex discovery budget
    for cid in carriers:
        blob = render.outputs[f"{probe.ARTIFACT_ROOT}/{cid}/SKILL.md"]
        description = probe.frontmatter_description(blob)
        assert isinstance(description, str) and description, cid
        assert probe.predicted_render_mode(description) == "complete", cid

    # renderer identity: what executed equals what is frozen at `head`
    assert render.renderer_identity
    for name, ident in render.renderer_identity.items():
        assert ident["imported_sha256"] == ident["blob_sha256"], name
        version = ident["renderer_version"]
        assert version is None or version >= 1, name

    # blob-sourced inputs only: no CRLF can reach a byte-copy output
    for cid in render.partition["byte-copy"]:
        assert b"\r\n" not in render.outputs[f"{probe.ARTIFACT_ROOT}/{cid}/SKILL.md"]
