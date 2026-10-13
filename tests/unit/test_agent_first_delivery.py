"""Delivery boundaries: task routing, scoped reuse, and safe evidence output."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest
from scripts.sdd.codex_hook_guard import classify
from scripts.sdd.git_command_review import publication


def test_registered_child_and_final_pr_use_exact_task_routes() -> None:
    route = {"task_id": "582", "repo": "synthetic/repo", "active": True,
             "integration": "feature/task-582-integration", "mainline": "develop",
             "children": ["feature/582-cli", "maintain/582-harness"]}
    for head, base in (("feature/582-cli", route["integration"]),
                       (route["integration"], "develop")):
        command = ["gh", "pr", "create", "--repo", "synthetic/repo", "--head", head,
                   "--base", base, "--title", "Title", "--body-file", "body.md"]
        assert publication(command, task_routes=[route])["status"] == "TASK_AUTHORIZATION_CONTEXT"
    command[command.index("--head") + 1] = "feature/unregistered"
    command[command.index("--base") + 1] = route["integration"]
    assert publication(command, task_routes=[route])["status"] == "FORBIDDEN"
    command[command.index("--repo") + 1] = "other/repo"
    assert publication(command, task_routes=[route])["status"] == "FORBIDDEN"


def test_revoked_and_ambiguous_routes_cannot_open_an_integration_base() -> None:
    route = {"task_id": "582", "repo": "synthetic/repo", "active": False,
             "integration": "feature/task-582-integration", "mainline": "develop",
             "children": ["feature/582-cli"]}
    command = ["gh", "pr", "create", "-R", "synthetic/repo", "-H", "feature/582-cli",
               "-B", route["integration"], "-t", "Title", "-F", "body.md"]
    assert publication(command, task_routes=[route])["status"] == "FORBIDDEN"
    route["active"] = True
    assert publication(command, task_routes=[route, copy.deepcopy(route)])["status"] == "UNKNOWN"


def test_merge_requires_explicit_repository_version_and_no_bypass() -> None:
    command = ["gh", "pr", "merge", "12", "--repo", "synthetic/repo", "--merge",
               "--match-head-commit", "a" * 40]
    assert publication(command)["status"] == "TASK_AUTHORIZATION_CONTEXT"
    for suffix in (["--admin"], ["--auto"], ["--delete-branch"]):
        assert publication([*command, *suffix])["status"] == "FORBIDDEN"
    assert publication(["gh", "pr", "merge", "12"])["status"] == "UNKNOWN"


def test_protected_edit_is_risk_context_not_authentication() -> None:
    payload = {"hook_event_name": "PreToolUse", "tool_name": "apply_patch",
               "tool_input": "*** Update File: src/mj_agent/tools/sql/guardrail.py\n@@\n-x\n+y"}
    state, reason = classify(payload)
    assert state == "TASK_AUTHORIZATION_CONTEXT"
    assert "risk" in reason.lower()
    payload["tool_input"] = "*** Update File: config/secrets.enc\n@@\n-x\n+y"
    assert classify(payload)[0] == "FORBIDDEN"


def test_junit_output_must_be_new_external_regular_path(tmp_path: Path) -> None:
    from scripts.sdd.run_offline_pytest import RunnerError, _junit_target

    root = tmp_path / "repo"
    root.mkdir()
    output = tmp_path / "evidence" / "tests.xml"
    output.parent.mkdir()
    assert _junit_target(str(output), root) == str(output.absolute())
    for path in (root / "tests.xml", output.parent / ".env"):
        with pytest.raises(RunnerError):
            _junit_target(str(path), root)
    output.write_text("original", encoding="utf-8")
    with pytest.raises(RunnerError):
        _junit_target(str(output), root)
    assert output.read_text(encoding="utf-8") == "original"


def test_task_scope_reuses_content_changes_but_not_resource_changes() -> None:
    from scripts.sdd.check_git_actions import review_actions

    item = {"id": "commit", "kind": "commit", "command": ["git", "commit", "-m", "one"],
            "scope": {"repo": "synthetic/repo", "branch": "maintain/example", "head": "a" * 40,
                      "files": ["scripts/example.py"], "staged_diff_sha256": "1" * 64},
            "authorization_scope": {"task_id": "example", "source": "Owner instruction",
                                    "repo": "synthetic/repo", "environment": "local",
                                    "actions": ["commit"], "branches": ["maintain/example"],
                                    "files": ["scripts/**"], "remotes": []}}
    current = copy.deepcopy(item)
    current["scope"].update(head="b" * 40, staged_diff_sha256="2" * 64)
    current["command"][-1] = "two"
    report = review_actions([item], [current], mode="never")
    assert report["items"][0]["status"] == "READY_FOR_REVIEW"
    assert report["owner_approval"] == "NOT_ASSESSED"
    current["scope"]["files"] = ["config/example.py"]
    assert review_actions([item], [current], mode="never")["items"][0]["status"] == "CHANGED"


def test_merge_command_matches_every_declared_object() -> None:
    from scripts.sdd.check_git_actions import review_actions

    item = {"id": "merge", "kind": "merge",
            "command": ["gh", "pr", "merge", "12", "--repo", "synthetic/repo", "--merge",
                        "--match-head-commit", "a" * 40],
            "scope": {"repo": "synthetic/repo", "pr": "12", "head": "feature/example",
                      "head_sha": "a" * 40, "base": "develop", "method": "merge"}}
    assert review_actions([item], [item], mode="never")["items"][0]["status"] == "READY_FOR_REVIEW"
    for index, value in ((3, "999"), (5, "other/repo"), (8, "b" * 40)):
        changed = copy.deepcopy(item)
        changed["command"][index] = value
        assert review_actions([changed], [changed], mode="never")["items"][0]["status"] == "UNKNOWN_COMMAND"


def test_registered_child_command_matches_but_feature_final_cannot_target_main() -> None:
    from scripts.sdd.check_git_actions import _command_matches
    from scripts.sdd.task_delivery import valid_pr_base

    route = {"task_id": "example", "repo": "synthetic/repo", "active": True,
             "integration": "feature/task-example-integration", "mainline": "develop",
             "children": ["feature/example"]}
    item = {"id": "pr", "kind": "pr_create", "task_routes": [route],
            "command": ["gh", "pr", "create", "--repo", "synthetic/repo", "--head", "feature/example",
                        "--base", route["integration"], "--title", "Example", "--body-file", "body.md"],
            "scope": {"repo": "synthetic/repo", "head": "feature/example", "head_sha": "a" * 40,
                      "base": route["integration"], "title": "Example", "body_sha256": "b" * 64}}
    assert _command_matches(item)
    route["mainline"] = "main"
    with pytest.raises(ValueError):
        valid_pr_base("synthetic/repo", route["integration"], "main", [route])


def test_task_reuse_only_exempts_known_content_fields() -> None:
    from scripts.sdd.check_git_actions import review_actions

    item = {"id": "commit", "kind": "commit", "command": ["git", "commit", "-m", "one"],
            "scope": {"repo": "synthetic/repo", "branch": "maintain/example", "head": "a" * 40,
                      "files": ["scripts/example.py"], "staged_diff_sha256": "1" * 64,
                      "environment": "local", "permissions": "read", "risk": "bounded"},
            "authorization_scope": {"task_id": "example", "source": "Owner instruction",
                                    "repo": "synthetic/repo", "environment": "local",
                                    "actions": ["commit"], "branches": ["maintain/example"],
                                    "files": ["scripts/**"], "remotes": []}}
    for location, field, value in (("scope", "environment", "prod"), ("scope", "permissions", "admin"),
                                   ("scope", "risk", "irreversible"), ("top", "risk", "unbounded")):
        changed = copy.deepcopy(item)
        changed["scope"]["head"] = "b" * 40
        (changed["scope"] if location == "scope" else changed)[field] = value
        assert review_actions([item], [changed], mode="never")["items"][0]["status"] == "CHANGED"


def test_windows_alias_edit_is_blocked_and_direct_branch_creation_is_g1() -> None:
    for path in (".env ", ".env::$DATA", "ordinary.json:stream", "config/credentials.json", "ordinary.md."):
        payload = {"hook_event_name": "PreToolUse", "tool_name": "Write", "tool_input": {"file_path": path}}
        assert classify(payload)[0] in {"FORBIDDEN", "UNKNOWN"}
    for command in ("git branch feature/example", "git branch feature/example HEAD", "git branch --copy example",
                    "git branch -v feature/example", "git branch --sort=refname feature/example"):
        payload = {"hook_event_name": "PreToolUse", "tool_name": "exec_command", "tool_input": {"cmd": command}}
        assert classify(payload)[0] == "FORBIDDEN"
    for command in ("git branch", "git branch --list feature/*", "git branch -d feature/example"):
        payload["tool_input"] = {"cmd": command}
        assert classify(payload)[0] == "ALLOW"


def test_junit_rejects_parent_aliases_before_metadata(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.sdd.run_offline_pytest import RunnerError, _junit_target

    root = tmp_path / "repo"
    root.mkdir()
    paths = (tmp_path / ".." / tmp_path.name / "repo" / "new.xml", tmp_path / "ordinary.xml::$DATA",
             tmp_path / "ordinary.xml ")

    def unexpected_metadata(*args: object, **kwargs: object) -> None:
        pytest.fail("invalid output path reached metadata")

    for path in paths:
        with monkeypatch.context() as scoped:
            scoped.setattr(Path, "exists", unexpected_metadata)
            with pytest.raises(RunnerError):
                _junit_target(str(path), root)


def test_real_pr_route_process_blocks_unregistered_and_inactive_routes(tmp_path: Path) -> None:
    import json
    import subprocess
    import sys

    script = Path(__file__).resolve().parents[2] / "scripts/sdd/task_delivery.py"
    directory = tmp_path / "plans"
    directory.mkdir()
    route = {"task_id": "example", "repo": "synthetic/repo", "active": True,
             "integration": "feature/task-example-integration", "mainline": "develop",
             "children": ["feature/example"]}
    record = directory / "[PLAN]_synthetic.md"
    for active, head, base, expected in ((True, "maintain/example", "develop", 0),
                                        (True, "dependabot/github_actions/gha-minor-patch", "develop", 0),
                                        (True, "feature/example", route["integration"], 0),
                                        (True, "feature/unregistered", route["integration"], 1),
                                        (False, "feature/example", route["integration"], 1),
                                        (True, route["integration"], "main", 1)):
        route["active"] = active
        record.write_text("<!-- agent-first-routes\n" + json.dumps({"schema_version": 1, "routes": [route]})
                          + "\n-->\n", encoding="utf-8")
        result = subprocess.run([sys.executable, str(script), "--root", str(tmp_path), "--repo", "synthetic/repo",
                                 "--head", head, "--base", base], check=False, capture_output=True, text=True)
        assert result.returncode == expected
        assert json.loads(result.stdout)["authorization"] == "NOT_ASSESSED"
