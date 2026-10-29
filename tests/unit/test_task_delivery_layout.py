"""New working directories retain exact routing and fail-closed path boundaries."""

from __future__ import annotations

import json
import stat
from pathlib import Path

import pytest
from scripts.sdd.task_delivery import load_task_routes, main, valid_pr_base


def route() -> dict:
    return {"task_id": "stable-task", "repo": "synthetic/repo", "active": True,
            "integration": "feature/task-stable-task-integration", "mainline": "develop",
            "children": ["maintain/example"]}


def write_record(path: Path, payload: dict | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("<!-- agent-first-routes\n"
                    + json.dumps(payload or {"schema_version": 1, "routes": [route()]})
                    + "\n-->\n", encoding="utf-8")


@pytest.mark.parametrize("topic", ["I608-P700-working-docs", "I608-working-docs",
                                   "P700-working-docs", "working-docs"])
def test_new_layout_discovers_exact_route(topic: str, tmp_path: Path) -> None:
    write_record(tmp_path / "plans" / topic / f"[PLAN]_{topic}.md")
    routes = load_task_routes(tmp_path)
    assert routes == [route()]
    assert valid_pr_base("synthetic/repo", "maintain/example",
                         "feature/task-stable-task-integration", routes)
    assert not valid_pr_base("other/repo", "maintain/example",
                             "feature/task-stable-task-integration", routes)


def test_legacy_layout_and_report_only_directory_remain_readable(tmp_path: Path) -> None:
    write_record(tmp_path / "plans/[PLAN]_legacy_Name.md")
    reports = tmp_path / "plans/I608-analysis"
    reports.mkdir()
    (reports / "[REPORT]_findings.md").write_text("done", encoding="utf-8")
    assert load_task_routes(tmp_path) == [route()]


def test_controlled_renumber_keeps_task_id_and_exact_relation(tmp_path: Path) -> None:
    old = tmp_path / "plans/I608-working-docs/[PLAN]_I608-working-docs.md"
    write_record(old)
    before = load_task_routes(tmp_path)
    # Ordinary fixture-local moves simulate the documented source/target operation.
    new_dir = old.parent.with_name("I608-P700-working-docs")
    old.parent.rename(new_dir)
    (new_dir / old.name).rename(new_dir / "[PLAN]_I608-P700-working-docs.md")
    assert load_task_routes(tmp_path) == before
    assert before[0]["task_id"] == "stable-task"


@pytest.mark.parametrize("names", [
    ["[PLAN]_different.md"],
    ["[PLAN]_working-docs.md", "[PLAN]_extra.md"],
])
def test_mismatched_or_multiple_main_plans_are_rejected(names: list[str], tmp_path: Path) -> None:
    for name in names:
        write_record(tmp_path / "plans/working-docs" / name)
    with pytest.raises(ValueError):
        load_task_routes(tmp_path)


def test_route_below_supported_depth_cannot_register_a_child(tmp_path: Path) -> None:
    write_record(tmp_path / "plans/working-docs/deeper/[PLAN]_deeper.md")
    assert not valid_pr_base("synthetic/repo", "maintain/example",
                             route()["integration"], load_task_routes(tmp_path))


def test_duplicate_routing_across_old_and_new_layout_is_unknown(tmp_path: Path,
                                                               capsys: pytest.CaptureFixture) -> None:
    write_record(tmp_path / "plans/[PLAN]_legacy.md")
    write_record(tmp_path / "plans/working-docs/[PLAN]_working-docs.md")
    result = main(["--root", str(tmp_path), "--repo", "synthetic/repo",
                   "--head", "maintain/example", "--base", route()["integration"]])
    assert result == 2
    assert json.loads(capsys.readouterr().out)["state"] == "UNKNOWN"


@pytest.mark.parametrize("level", ["plans", "topic", "record"])
def test_reparse_point_at_every_read_layer_is_rejected(level: str, tmp_path: Path,
                                                       monkeypatch: pytest.MonkeyPatch) -> None:
    record = tmp_path / "plans/working-docs/[PLAN]_working-docs.md"
    write_record(record)
    target = {"plans": record.parent.parent, "topic": record.parent, "record": record}[level]
    original = Path.lstat

    def indirect(path: Path, *args: object, **kwargs: object):
        info = original(path, *args, **kwargs)
        if path == target:
            class Reparse:
                st_mode = stat.S_IFDIR if level != "record" else stat.S_IFREG
                st_file_attributes = 0x400
                st_size = 100
            return Reparse()
        return info

    monkeypatch.setattr(Path, "lstat", indirect)
    with pytest.raises(ValueError, match="indirect"):
        load_task_routes(tmp_path)


@pytest.mark.parametrize("kind", ["oversize", "duplicate-block", "malformed-json",
                                  "unclosed-block", "invalid-route"])
def test_bad_nested_record_fails_closed(kind: str, tmp_path: Path) -> None:
    record = tmp_path / "plans/working-docs/[PLAN]_working-docs.md"
    write_record(record)
    content = record.read_text(encoding="utf-8")
    if kind == "oversize":
        content += "x" * (1024 * 1024)
    elif kind == "duplicate-block":
        content += content
    elif kind == "malformed-json":
        content = "<!-- agent-first-routes\n{\n-->\n"
    elif kind == "unclosed-block":
        content = "<!-- agent-first-routes\n{}"
    else:
        content = "<!-- agent-first-routes\n" + json.dumps(
            {"schema_version": 1, "routes": [{"task_id": "bad"}]}) + "\n-->\n"
    record.write_text(content, encoding="utf-8")
    with pytest.raises((ValueError, TypeError)):
        load_task_routes(tmp_path)

