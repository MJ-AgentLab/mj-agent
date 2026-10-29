"""Task-folder layout and retirement regressions for Issue #608."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from scripts.check_working_docs import check, main, valid_topic


def _write(root: Path, rel: str, text: str = "# artifact\n") -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


@pytest.mark.parametrize("topic", ["I608-P609-working-docs", "I608-working-docs", "P609-working-docs", "working-docs"])
def test_four_topic_forms(topic: str, tmp_path: Path) -> None:
    assert valid_topic(topic)
    _write(tmp_path, f"plans/{topic}/[PLAN]_{topic}.md")
    assert check(tmp_path) == {}


@pytest.mark.parametrize("topic", ["I0-topic", "P0-topic", "I608-P0-topic", "i608-P609-topic", "I608-I609-topic", "P609-I608-topic", "I608-P609-Topic", "topic_name", "中文", "topic--name", "-topic", "topic-", "I608-P609-I610-topic"])
def test_invalid_topics(topic: str) -> None:
    assert not valid_topic(topic)


def test_wrong_plan_topic_and_duplicate_main_plan(tmp_path: Path) -> None:
    _write(tmp_path, "plans/topic/[PLAN]_topic.md")
    other = _write(tmp_path, "plans/topic/[PLAN]_other.md")
    bad = check(tmp_path)
    assert bad
    assert any("one main Plan" in problem for problems in bad.values() for problem in problems)
    assert any("match" in problem for problem in bad[other.relative_to(tmp_path)])


def test_intake_can_precede_plan_or_remain_without_plan(tmp_path: Path) -> None:
    _write(tmp_path, "plans/intake-only/[INTAKE]_intake-only.md")
    _write(tmp_path, "plans/report-only/Final assessment.md")
    assert check(tmp_path) == {}
    _write(tmp_path, "plans/intake-only/[PLAN]_intake-only.md")
    assert check(tmp_path) == {}


def test_legacy_root_files_keep_original_names(tmp_path: Path) -> None:
    _write(tmp_path, "plans/[PLAN]_old_123_Chinese.md", "[historic](./missing-snapshot.md)")
    assert check(tmp_path) == {}


def test_shared_report_has_one_owner_and_child_plan_own_folder(tmp_path: Path) -> None:
    _write(tmp_path, "plans/parent/[REPORT]_review.md")
    _write(tmp_path, "plans/parent/[PLAN]_parent.md", "[child](../child/[PLAN]_child.md)")
    _write(tmp_path, "plans/child/[PLAN]_child.md", "[shared](../parent/[REPORT]_review.md)")
    assert check(tmp_path) == {}


def test_deep_broken_relative_link_is_blocking(tmp_path: Path) -> None:
    plan = _write(tmp_path, "plans/topic/[PLAN]_topic.md", "[spec](../../docs/missing.md)")
    assert "unresolved" in " ".join(check(tmp_path)[plan.relative_to(tmp_path)])
    _write(tmp_path, "docs/missing.md")
    assert main([], repo_root=tmp_path) == 0


def test_controlled_rename_requires_all_active_links_to_follow(tmp_path: Path) -> None:
    plan = _write(tmp_path, "plans/topic/[PLAN]_topic.md")
    report = _write(tmp_path, "plans/topic/[REPORT]_review.md", "[plan](./[PLAN]_topic.md)")
    assert check(tmp_path) == {}
    destination = tmp_path / "plans/I608-topic"
    plan.parent.rename(destination)
    (destination / plan.name).rename(destination / "[PLAN]_I608-topic.md")
    assert check(tmp_path)  # old active report link is no longer valid
    (destination / report.name).write_text("[plan](./[PLAN]_I608-topic.md)", encoding="utf-8")
    assert check(tmp_path) == {}


def test_unreadable_collection_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write(tmp_path, "plans/topic/[PLAN]_topic.md")
    original = Path.iterdir

    def broken(path: Path):
        if path == tmp_path / "plans":
            raise PermissionError("collection unavailable")
        return original(path)

    monkeypatch.setattr(Path, "iterdir", broken)
    assert main([], repo_root=tmp_path) == 1


def test_symlink_documents_are_rejected(tmp_path: Path) -> None:
    source = _write(tmp_path, "source.md")
    target = tmp_path / "plans/topic/[PLAN]_topic.md"
    target.parent.mkdir(parents=True)
    try:
        target.symlink_to(source)
    except OSError:
        pytest.skip("host cannot create a symlink")
    assert check(tmp_path)


def test_gc_script_is_retired_and_never_scans(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    from scripts import find_old_completed_plans

    monkeypatch.setattr(Path, "glob", lambda *_: (_ for _ in ()).throw(AssertionError("retired GC must not scan")))
    monkeypatch.setattr("sys.argv", ["find_old_completed_plans.py", "180"])
    assert find_old_completed_plans.main() == 0
    assert "RETIRED" in capsys.readouterr().out


def test_primary_pr_is_explicit_and_not_inferred_from_first_link(tmp_path: Path) -> None:
    plan = _write(tmp_path, "plans/I608-P610-topic/[PLAN]_I608-P610-topic.md", "Sub PR: https://github.com/MJ-AgentLab/mj-agent/pull/609\nPrimary PR: https://github.com/MJ-AgentLab/mj-agent/pull/610")
    assert check(tmp_path) == {}
    plan.write_text("主要 PR: https://github.com/MJ-AgentLab/mj-agent/pull/609", encoding="utf-8")
    assert check(tmp_path)


def test_reparse_flag_is_rejected_without_requiring_symlink_creation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    plan = _write(tmp_path, "plans/topic/[PLAN]_topic.md")
    original = Path.lstat
    def flagged(path: Path, *args: object, **kwargs: object):
        if path == plan:
            return SimpleNamespace(st_mode=0, st_file_attributes=0x400)
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, "lstat", flagged)
    assert check(tmp_path)


def test_bounded_file_size_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write(tmp_path, "plans/topic/[PLAN]_topic.md", "too big")
    monkeypatch.setattr("scripts.check_working_docs.MAX_DOCUMENT_BYTES", 3)
    assert check(tmp_path)


def test_bounded_document_count_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write(tmp_path, "plans/topic/[PLAN]_topic.md")
    _write(tmp_path, "plans/topic/[REPORT]_review.md")
    monkeypatch.setattr("scripts.check_working_docs.MAX_DOCUMENTS", 1)
    assert check(tmp_path)


def test_explicit_primary_link_cannot_use_other_repository(tmp_path: Path) -> None:
    _write(tmp_path, "plans/I608-topic/[PLAN]_I608-topic.md", "主要 Issue: https://github.com/Other/repo/issues/608")
    assert check(tmp_path)


def test_ci_keeps_structure_validation_and_has_no_working_gc_invocation() -> None:
    root = Path(__file__).resolve().parents[2]
    ci = (root / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "python scripts/check_working_docs.py" in ci
    assert "python scripts/check_frontmatter.py" in ci
    assert "python scripts/check_wikilinks.py" in ci
    assert "python scripts/find_old_completed_plans.py" not in ci
