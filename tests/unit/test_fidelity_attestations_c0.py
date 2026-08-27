"""PR-C0 fidelity attestation contracts — Epic #499 plan §2.7 item 9 / §2.8.5.

Two things are pinned here, and they are deliberately kept apart:

* **Closure** — the committed coverage reports satisfy the INDEPENDENT checker
  (`check_fidelity_attestations.py`), which re-derives the inventory without
  importing the renderer that produced them.
* **Binding** — every digest in those reports equals what PR-P1b published for
  the pinned candidate commit, so the review subject is the artifact set whose
  determinism PR-P1b already proved.

No test here needs Git history. `ci.yml` checks out shallow (no
`fetch-depth: 0`), so a test that re-rendered the candidate from
`36f298a…` would pass locally and error in CI. The binding is proved
transitively instead: committed report digests == the tracked PR-P1b fixture,
which PR-P1b bound to a deterministic render at that revision.

The producer negatives drive the REAL entry points (`load_bindings` /
`build_index`) with real inputs — a negative that only exercises a recorder
proves nothing about the code path an actual violation would take
(PR-P1b Stage 11 judgment).
"""

from __future__ import annotations

import copy
import json
import re
import shutil
from pathlib import Path
from typing import Any

import pytest
import yaml
from scripts.sdd.build_fidelity_attestations import (
    BINDING_KEYS,
    CANDIDATE_REV,
    COVERAGE_RELDIR,
    PACKET_RELDIR,
    TRANCHES,
    build_index,
    canonical_json_bytes,
    coverage_bytes,
    coverage_drift,
    load_bindings,
    set_digest,
)
from scripts.sdd.check_fidelity_attestations import (
    ITEM_KEYS,
    ITEM_KINDS,
    STATUSES,
    TRANSFORM_CLASSES,
    check_index,
)
from scripts.sdd.check_fidelity_attestations import main as fidelity_main

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = (
    REPO_ROOT / "evidence" / "development-agent-v8" / "probe" / "fixtures"
    / "p1b-deterministic-expected.json"
)
COVERAGE_DIR = REPO_ROOT / COVERAGE_RELDIR
WORKFLOW_REGISTRY = REPO_ROOT / "sdd" / "workflows" / "development-agent-workflows.yml"


@pytest.fixture(scope="module")
def p1b_fixture() -> dict[str, Any]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def translated(p1b_fixture: dict[str, Any]) -> list[str]:
    caps = sorted(p1b_fixture["carrier_partition"]["translated"])
    assert len(caps) == 13, "the translated carrier count is a §2.2.1 invariant"
    return caps


@pytest.fixture(scope="module")
def reports(translated: list[str]) -> dict[str, dict[str, Any]]:
    out = {
        cap: json.loads((COVERAGE_DIR / f"{cap}.json").read_text(encoding="utf-8"))
        for cap in translated
    }
    assert out, "no coverage reports parsed — an empty set passes vacuously"
    return out


# ------------------------------------------------------------- digest wire


def test_set_digest_wire_reproduces_the_published_candidate_set(
    p1b_fixture: dict[str, Any],
) -> None:
    """The §2.7 set-digest wire, pinned against a value someone else published.

    Recomputing it over PR-P1b's per-path digests must land on PR-P1b's
    `candidate_set_sha256` — otherwise this producer's notion of a set digest
    is not the project's.
    """
    per_path = p1b_fixture["candidate_output_sha256"]
    assert len(per_path) == 20
    assert set_digest(per_path) == p1b_fixture["candidate_set_sha256"]


def test_set_digest_is_order_independent_but_content_sensitive(
    p1b_fixture: dict[str, Any],
) -> None:
    per_path = dict(p1b_fixture["candidate_output_sha256"])
    reversed_insertion = dict(reversed(list(per_path.items())))
    assert set_digest(reversed_insertion) == set_digest(per_path)

    mutated = copy.deepcopy(per_path)
    victim = sorted(mutated)[0]
    mutated[victim] = "0" * 64
    assert set_digest(mutated) != set_digest(per_path)


def test_canonical_json_bytes_are_lf_utf8_with_final_newline() -> None:
    raw = canonical_json_bytes({"b": 1, "a": "中"})
    assert raw.endswith(b"\n")
    assert b"\r" not in raw
    assert raw.decode("utf-8").index('"a"') < raw.decode("utf-8").index('"b"')
    assert "中".encode() in raw


# ------------------------------------------------------------- coverage set


def test_coverage_reports_cover_exactly_the_13_translated_carriers(
    translated: list[str],
) -> None:
    on_disk = sorted(p.stem for p in COVERAGE_DIR.glob("*.json"))
    assert on_disk == translated


def test_coverage_reports_bind_to_the_published_candidate_digests(
    reports: dict[str, dict[str, Any]], p1b_fixture: dict[str, Any]
) -> None:
    """Every committed report points at the exact bytes PR-P1b published.

    This is the whole review-subject argument: the reviewer approves a digest
    set, and that set is the one whose deterministic render already has
    evidence behind it.
    """
    checked = 0
    for cap, report in reports.items():
        assert report["source_sha256"] == p1b_fixture["source_sha256"][cap], cap
        artifact_key = f".agents/skills/{cap}/SKILL.md"
        assert (
            report["artifact_sha256"]
            == p1b_fixture["candidate_output_sha256"][artifact_key]
        ), cap
        assert report["source_path"] == f".claude/skills/{cap}/SKILL.md"
        assert report["artifact_path"] == artifact_key
        checked += 1
    assert checked == 13


def test_coverage_reports_use_exact_schema_keys_and_closed_enums(
    reports: dict[str, dict[str, Any]]
) -> None:
    top_keys = {
        "schema_version", "capability_id", "source_path", "artifact_path",
        "source_sha256", "artifact_sha256", "inventory_sha256", "items",
    }
    items_seen = 0
    for cap, report in reports.items():
        assert set(report) == top_keys, cap
        assert report["schema_version"] == 1
        assert report["capability_id"] == cap
        item_ids = set()
        for item in report["items"]:
            assert set(item) == ITEM_KEYS, cap
            assert item["item_kind"] in ITEM_KINDS
            assert item["transform_class"] in TRANSFORM_CLASSES
            assert item["status"] in STATUSES
            assert item["item_id"] not in item_ids, f"{cap}: duplicate item_id"
            item_ids.add(item["item_id"])
            items_seen += 1
    assert items_seen == 617, (
        "the committed inventory changed size — regenerate the reports and"
        " re-run the review binding rather than editing this number"
    )


def test_coverage_inventory_sha256_is_self_consistent(
    reports: dict[str, dict[str, Any]]
) -> None:
    """A stale `inventory_sha256` is how a hand-edited report would look."""
    from scripts.sdd.check_fidelity_attestations import _canonical_sha256

    for cap, report in reports.items():
        assert _canonical_sha256(report["items"]) == report["inventory_sha256"], cap


def test_every_report_carries_exactly_one_frontmatter_description(
    reports: dict[str, dict[str, Any]]
) -> None:
    for cap, report in reports.items():
        descriptions = [
            i for i in report["items"]
            if i["item_kind"] == "frontmatter-description"
        ]
        assert len(descriptions) == 1, cap
        assert descriptions[0]["source_locator"] == "frontmatter:description"


def test_coverage_drift_detector_is_clean_against_the_committed_reports(
    reports: dict[str, dict[str, Any]]
) -> None:
    """`build-coverage --check` over the real tree, minus the render step: the
    committed bytes must be exactly what `coverage_bytes` produces."""
    blobs = {cap: coverage_bytes(report) for cap, report in reports.items()}
    assert coverage_drift(REPO_ROOT, blobs) == []


def test_coverage_drift_detector_reports_edited_and_missing_reports(
    tmp_path: Path, reports: dict[str, dict[str, Any]]
) -> None:
    """Negative control for the detector above — without it, a drift verdict
    of `[]` could mean "nothing drifted" or "nothing was compared"."""
    blobs = {cap: coverage_bytes(report) for cap, report in reports.items()}
    fake = tmp_path / "tree"
    (fake / COVERAGE_RELDIR).mkdir(parents=True)
    victims = sorted(blobs)[:2]
    for cap, data in blobs.items():
        if cap == victims[0]:
            continue  # missing entirely
        payload = data + b"\n" if cap == victims[1] else data  # byte-edited
        (fake / COVERAGE_RELDIR / f"{cap}.json").write_bytes(payload)
    assert coverage_drift(fake, blobs) == sorted(victims)


# ----------------------------------------------------- independent closure


def _closure_tree(tmp_path: Path, translated: list[str]) -> Path:
    """A tree the independent checker can run against: real sources, real
    registry, the REAL committed coverage reports, and a structurally valid
    index. Digests in the index are placeholders — this fixture targets
    inventory closure, not binding authenticity (that is `build_index`'s job).
    """
    root = tmp_path / "closure"
    for cap in translated:
        dest = root / ".claude" / "skills" / cap / "SKILL.md"
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(REPO_ROOT / ".claude" / "skills" / cap / "SKILL.md", dest)
    registry_dest = root / "sdd" / "workflows" / "development-agent-workflows.yml"
    registry_dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(WORKFLOW_REGISTRY, registry_dest)
    coverage_dest = root / COVERAGE_RELDIR
    coverage_dest.mkdir(parents=True, exist_ok=True)
    for cap in translated:
        shutil.copy(COVERAGE_DIR / f"{cap}.json", coverage_dest / f"{cap}.json")
    index = {
        "schema_version": 1,
        "translated_capabilities": translated,
        "coverage_reports": [f"{COVERAGE_RELDIR}/{c}.json" for c in translated],
        "tranches": [
            {
                "tranche_id": tid,
                "capability_ids": list(members),
                "candidate_commit_sha": CANDIDATE_REV,
                "manifest_set_sha256": "a" * 64,
                "source_set_sha256": "b" * 64,
                "artifact_set_sha256": "c" * 64,
                "translation_set_sha256": "d" * 64,
                "workflow_set_sha256": "e" * 64,
                "preface_sha256": "f" * 64,
                "renderer_set_sha256": "0" * 64,
                "coverage_set_sha256": "1" * 64,
                "approval_binding": {
                    "record_system": "github-pull-request-review",
                    "immutable_record_id": f"fixture-record-{i}",
                    "reviewer_identity": "fixture-reviewer",
                    "verdict": "approved",
                    "reviewed_candidate_commit_sha": CANDIDATE_REV,
                    "reviewed_source_set_sha256": "b" * 64,
                    "reviewed_artifact_set_sha256": "c" * 64,
                    "recorded_at": "2026-08-26T00:00:00Z",
                },
            }
            for i, (tid, members) in enumerate(TRANCHES)
        ],
    }
    index_dest = root / "sdd" / "adapters" / "codex-skill-fidelity.yml"
    index_dest.parent.mkdir(parents=True, exist_ok=True)
    index_dest.write_text(
        yaml.safe_dump(index, sort_keys=False, allow_unicode=True),
        encoding="utf-8", newline="\n",
    )
    return root


def test_independent_checker_closes_over_the_committed_reports(
    tmp_path: Path, translated: list[str]
) -> None:
    """The committed reports survive a checker that never saw the generator.

    Sources are copied from this checkout, i.e. CRLF under `* text=auto` — the
    closure must be EOL-robust, which is also why the reports' own digests are
    taken from Git blobs rather than the worktree.
    """
    root = _closure_tree(tmp_path, translated)
    assert fidelity_main(["--all"], repo_root=root) == 0


def test_dropping_one_committed_item_reds_the_independent_checker(
    tmp_path: Path, translated: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    """The mandated negative, aimed at the COMMITTED reports: if the renderer
    and its own report had both missed an item, the independent inventory would
    still catch it. Proves the green result above is not vacuous."""
    from scripts.sdd.check_fidelity_attestations import _canonical_sha256

    root = _closure_tree(tmp_path, translated)
    victim = root / COVERAGE_RELDIR / "mj-agent-git-branch.json"
    report = json.loads(victim.read_text(encoding="utf-8"))
    before = len(report["items"])
    report["items"] = [i for i in report["items"] if i["item_kind"] != "git-rule"]
    assert len(report["items"]) < before, "negative control removed nothing"
    report["inventory_sha256"] = _canonical_sha256(report["items"])
    victim.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8", newline="\n",
    )
    assert fidelity_main(["--all"], repo_root=root) == 1
    assert "independent inventory expects" in capsys.readouterr().out


def test_surplus_item_also_reds_the_independent_checker(
    tmp_path: Path, translated: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    """EXACT closure cuts both ways — an invented item fails too."""
    from scripts.sdd.check_fidelity_attestations import _canonical_sha256

    root = _closure_tree(tmp_path, translated)
    victim = root / COVERAGE_RELDIR / "mj-agent-git-pr.json"
    report = json.loads(victim.read_text(encoding="utf-8"))
    extra = copy.deepcopy(report["items"][0])
    extra["item_id"] = "heading-999"
    report["items"].append(extra)
    report["inventory_sha256"] = _canonical_sha256(report["items"])
    victim.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8", newline="\n",
    )
    assert fidelity_main(["--all"], repo_root=root) == 1
    assert "EXACT closure" in capsys.readouterr().out


# ------------------------------------------------------------- partition


def test_declared_partition_is_an_exact_3_to_4_way_split(
    translated: list[str]
) -> None:
    members: list[str] = []
    for _tid, group in TRANCHES:
        members.extend(group)
    assert 3 <= len(TRANCHES) <= 4
    assert sorted(members) == translated, "gap or extra vs the translated set"
    assert len(members) == len(set(members)), "tranche overlap"
    assert len({tid for tid, _ in TRANCHES}) == len(TRANCHES)


# ------------------------------------------------------- reviewer packets


PACKET_DIR = REPO_ROOT / PACKET_RELDIR


@pytest.fixture(scope="module")
def packets() -> dict[str, str]:
    out = {
        tid: (PACKET_DIR / f"{tid}.md").read_text(encoding="utf-8")
        for tid, _members in TRANCHES
    }
    assert len(out) == len(TRANCHES) >= 3, "packet set empty or short"
    return out


def test_packet_digest_table_matches_digests_recomputed_from_the_p1b_fixture(
    packets: dict[str, str], p1b_fixture: dict[str, Any]
) -> None:
    """The three values a reviewer copies into their record are the ones the
    tranche actually covers.

    Recomputed here from the tracked PR-P1b fixture and this module's own
    `set_digest` — deliberately NOT from `tranche_digests`, which needs Git
    history and so cannot run in CI. If the producer's composition ever
    diverges from "the digests of exactly these members", this fails.
    """
    checked = 0
    for tid, members in TRANCHES:
        text = packets[tid]
        source_set = {
            f".claude/skills/{cap}/SKILL.md": p1b_fixture["source_sha256"][cap]
            for cap in members
        }
        artifact_set = {
            f".agents/skills/{cap}/SKILL.md":
                p1b_fixture["candidate_output_sha256"][
                    f".agents/skills/{cap}/SKILL.md"]
            for cap in members
        }
        assert f"| `reviewed_candidate_commit_sha` | `{CANDIDATE_REV}` |" in text
        assert (
            f"| `reviewed_source_set_sha256` | `{set_digest(source_set)}` |"
            in text
        ), tid
        assert (
            f"| `reviewed_artifact_set_sha256` | `{set_digest(artifact_set)}` |"
            in text
        ), tid
        checked += 1
    assert checked == len(TRANCHES)


def test_packet_item_accounting_sums_to_each_capability_item_total(
    packets: dict[str, str], reports: dict[str, dict[str, Any]]
) -> None:
    """The four buckets the packet shows a reviewer must account for every
    item — otherwise "this is your spot-check surface" understates the work."""
    pat = re.compile(
        r"- \*\*(\d+)\*\* byte-identical.*?"
        r"- \*\*(\d+)\*\* identical apart.*?"
        r"- \*\*1\*\* frontmatter description.*?"
        r"- \*\*(\d+)\*\* carry a declared",
        re.S,
    )
    grand = 0
    for tid, members in TRANCHES:
        buckets = pat.findall(packets[tid])
        assert len(buckets) == len(members), (
            f"{tid}: parsed {len(buckets)} accounting blocks for"
            f" {len(members)} capabilities"
        )
        for cap, (ident, ws, tr) in zip(members, buckets, strict=True):
            total = int(ident) + int(ws) + 1 + int(tr)
            assert total == len(reports[cap]["items"]), cap
            grand += total
    assert grand == 617


def test_packet_spot_check_surface_is_declared_transforms_not_digest_inequality(
    reports: dict[str, dict[str, Any]]
) -> None:
    """Pins the distinction the packet rests on: digest inequality alone is a
    bad proxy for "transformed", because the report digests the raw source line
    against the stripped artifact slice."""
    noop_but_differing = [
        i for r in reports.values() for i in r["items"]
        if i["transform_class"] == "NOOP"
        and i["source_sha256"] != i["artifact_sha256"]
    ]
    assert noop_but_differing, (
        "no NOOP-yet-differing items — the packet's whitespace bucket would be"
        " vacuous and the distinction untested"
    )
    declared = [
        i for r in reports.values() for i in r["items"]
        if i["transform_class"] != "NOOP"
    ]
    assert len(declared) == 37
    assert {i["transform_class"] for i in declared} == {"T2a", "T2b"}


def test_packets_do_not_tell_the_reviewer_to_run_emit_fixtures(
    packets: dict[str, str]
) -> None:
    """`emit-fixtures` writes into the tracked probe fixture directory and emits
    digests rather than carrier text — a reviewer must never be pointed at it
    (Stage 11 finding)."""
    for tid, text in packets.items():
        recipe = text.split("## 3.")[-1]
        assert "--fixtures-dir" not in recipe, tid
        assert "build-coverage --check" in recipe, tid
        # the only mention of emit-fixtures must be the explicit warning
        for line in recipe.splitlines():
            if "emit-fixtures" in line:
                assert "Do **not** run" in line or "not** run" in line, tid


# --------------------------------------------- producer approval negatives


def _binding(tranche_id: str, index: int, **overrides: Any) -> dict[str, Any]:
    record = {
        "tranche_id": tranche_id,
        "record_system": "github-pull-request-review",
        "immutable_record_id": f"PRR_fixture_{index}",
        "reviewer_identity": "fixture-reviewer",
        "verdict": "approved",
        "reviewed_candidate_commit_sha": CANDIDATE_REV,
        "reviewed_source_set_sha256": "b" * 64,
        "reviewed_artifact_set_sha256": "c" * 64,
        "recorded_at": "2026-08-26T00:00:00Z",
    }
    record.update(overrides)
    return record


def _bindings_file(tmp_path: Path, records: list[dict[str, Any]]) -> Path:
    path = tmp_path / "bindings.json"
    path.write_text(
        json.dumps(records, ensure_ascii=False, indent=2),
        encoding="utf-8", newline="\n",
    )
    return path


def _all_tranche_ids() -> list[str]:
    return [tid for tid, _ in TRANCHES]


def test_load_bindings_accepts_a_complete_reviewer_supplied_set(
    tmp_path: Path
) -> None:
    """Positive control — without it, every negative below could be passing for
    the wrong reason."""
    records = [_binding(tid, i) for i, tid in enumerate(_all_tranche_ids())]
    loaded = load_bindings(_bindings_file(tmp_path, records), _all_tranche_ids())
    assert sorted(loaded) == sorted(_all_tranche_ids())
    for binding in loaded.values():
        assert set(binding) == BINDING_KEYS


def test_load_bindings_blocks_when_a_tranche_has_no_record(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    records = [_binding(tid, i) for i, tid in enumerate(_all_tranche_ids()[:-1])]
    with pytest.raises(SystemExit) as exc:
        load_bindings(_bindings_file(tmp_path, records), _all_tranche_ids())
    assert exc.value.code == 2
    assert "BLOCKED_PREREQUISITE" in capsys.readouterr().err


@pytest.mark.parametrize("verdict", ["pending", "approved_with_comments", "", "APPROVED"])
def test_load_bindings_rejects_any_verdict_outside_the_closed_enum(
    tmp_path: Path, verdict: str
) -> None:
    records = [_binding(tid, i) for i, tid in enumerate(_all_tranche_ids())]
    records[0]["verdict"] = verdict
    with pytest.raises(SystemExit) as exc:
        load_bindings(_bindings_file(tmp_path, records), _all_tranche_ids())
    assert exc.value.code == 2


def test_load_bindings_rejects_a_reused_immutable_record_id(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    records = [_binding(tid, i) for i, tid in enumerate(_all_tranche_ids())]
    records[1]["immutable_record_id"] = records[0]["immutable_record_id"]
    with pytest.raises(SystemExit) as exc:
        load_bindings(_bindings_file(tmp_path, records), _all_tranche_ids())
    assert exc.value.code == 2
    assert "NEW record" in capsys.readouterr().err


def test_load_bindings_rejects_inexact_binding_keys(tmp_path: Path) -> None:
    records = [_binding(tid, i) for i, tid in enumerate(_all_tranche_ids())]
    records[2]["reviewer_note"] = "looks fine"
    with pytest.raises(SystemExit) as exc:
        load_bindings(_bindings_file(tmp_path, records), _all_tranche_ids())
    assert exc.value.code == 2


class _StubRender:
    """Minimal stand-in for CandidateRender — `build_index` only reads the
    partition, so the negatives below need no Git history."""

    def __init__(self, translated_caps: list[str]) -> None:
        self.partition = {"translated": list(translated_caps), "byte-copy": []}


def _digest_table() -> dict[str, dict[str, str]]:
    return {
        tid: {
            "manifest_set_sha256": "a" * 64,
            "source_set_sha256": "b" * 64,
            "artifact_set_sha256": "c" * 64,
            "translation_set_sha256": "d" * 64,
            "workflow_set_sha256": "e" * 64,
            "preface_sha256": "f" * 64,
            "renderer_set_sha256": "0" * 64,
            "coverage_set_sha256": "1" * 64,
        }
        for tid, _ in TRANCHES
    }


def test_build_index_emits_a_structurally_valid_index(
    translated: list[str]
) -> None:
    """Positive control for the two negatives that follow, and a direct check
    that the producer's output satisfies the independent checker's index
    rules."""
    bindings = {
        tid: {k: v for k, v in _binding(tid, i).items() if k != "tranche_id"}
        for i, tid in enumerate(_all_tranche_ids())
    }
    index = build_index(
        _StubRender(translated), _digest_table(), bindings, CANDIDATE_REV
    )
    assert index["schema_version"] == 1
    assert index["translated_capabilities"] == translated
    assert len(index["tranches"]) == len(TRANCHES)
    problems: list[str] = []
    check_index(REPO_ROOT, index, problems)
    assert problems == []


class _StubProbe:
    """Probe stand-in for the packet fail-closed negative: real bytes in, but
    `frontmatter_description` behaves as it does on an unparseable blob."""

    GitError = RuntimeError

    def __init__(self, description: str | None) -> None:
        self._description = description

    def git_blob_bytes(self, repo_root: Path, rev: str, relpath: str) -> bytes:
        return b"---\nname: x\ndescription: y\n---\n\n# body\n"

    def frontmatter_description(self, blob: bytes) -> str | None:
        return self._description

    def resolve_rev(self, repo_root: Path, rev: str) -> str:
        return CANDIDATE_REV


def test_build_packet_fails_closed_when_a_description_does_not_parse(
    monkeypatch: pytest.MonkeyPatch, reports: dict[str, dict[str, Any]],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`frontmatter_description` returns None for a blob it cannot parse (a CRLF
    blob does). Defaulting that to "" would publish an EMPTY trigger judgment —
    the one thing §2.7 item 9 makes mandatory — and still exit 0."""
    import scripts.sdd.build_fidelity_attestations as producer

    tid, members = TRANCHES[0]
    render = _StubRender(list(members))
    render.outputs = {  # type: ignore[attr-defined]
        f".agents/skills/{cap}/SKILL.md": b"---\ndescription: z\n---\n"
        for cap in members
    }
    digests = _digest_table()[tid]

    monkeypatch.setattr(producer, "_probe_module", lambda: _StubProbe("ok"))
    text = producer.build_packet(
        REPO_ROOT, CANDIDATE_REV, render, tid, members, reports, digests
    )
    assert "```text\nok\n```" in text, "positive control did not build"

    monkeypatch.setattr(producer, "_probe_module", lambda: _StubProbe(None))
    with pytest.raises(SystemExit) as exc:
        producer.build_packet(
            REPO_ROOT, CANDIDATE_REV, render, tid, members, reports, digests
        )
    assert exc.value.code == 2
    assert "empty judgment surface" in capsys.readouterr().err


@pytest.mark.parametrize("mode", ["build-packet", "build-index"])
def test_check_is_refused_for_modes_that_do_not_implement_it(mode: str) -> None:
    """A flag whose help says "instead of writing" must never write. It is
    implemented for build-coverage only, so the others must refuse it rather
    than ignore it and write anyway (Stage 11 finding). This runs before any
    Git access, so it is shallow-clone safe."""
    import scripts.sdd.build_fidelity_attestations as producer

    with pytest.raises(SystemExit) as exc:
        producer.main([mode, "--check"], repo_root=REPO_ROOT)
    assert exc.value.code == 2


@pytest.mark.parametrize(
    "field",
    [
        "reviewed_source_set_sha256",
        "reviewed_artifact_set_sha256",
        "reviewed_candidate_commit_sha",
    ],
)
def test_build_index_refuses_a_record_reviewed_against_other_inputs(
    translated: list[str], field: str, capsys: pytest.CaptureFixture[str]
) -> None:
    """The gap the independent checker leaves open: it validates that the
    `reviewed_*` fields are well-formed hex, never that they match the tranche
    they are attached to. The producer closes it, so a review of stale inputs
    cannot be rebound to a newer digest set."""
    bindings = {
        tid: {k: v for k, v in _binding(tid, i).items() if k != "tranche_id"}
        for i, tid in enumerate(_all_tranche_ids())
    }
    stale = "9" * (40 if field.endswith("commit_sha") else 64)
    bindings[_all_tranche_ids()[0]][field] = stale
    with pytest.raises(SystemExit) as exc:
        build_index(
            _StubRender(translated), _digest_table(), bindings, CANDIDATE_REV
        )
    assert exc.value.code == 2
    assert "may not be rebound here" in capsys.readouterr().err
