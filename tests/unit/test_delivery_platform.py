"""Offline platform-control checks; no credentials, live API or platform mutation."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from scripts.sdd import check_delivery_platform as platform

REPOSITORY = "synthetic/repo"
NAMES = ("protect-develop", "protect-main", "protect-task-integration")


def _ruleset(name: str = "protect-develop") -> dict[str, Any]:
    refs = {"protect-develop": "refs/heads/develop", "protect-main": "refs/heads/main",
            "protect-task-integration": "refs/heads/feature/task-*-integration"}
    rules = [{"type": "deletion"}, {"type": "non_fast_forward"}]
    if name == "protect-main":
        rules.append({"type": "creation"})
    rules.extend([
        {"type": "pull_request", "parameters": {
            "required_approving_review_count": 1, "dismiss_stale_reviews_on_push": True,
            "require_last_push_approval": True, "required_review_thread_resolution": True,
            "require_code_owner_review": True, "allowed_merge_methods": ["merge"],
        }},
        {"type": "required_status_checks", "parameters": {
            "strict_required_status_checks_policy": True,
            "do_not_enforce_on_create": name == "protect-task-integration",
            "required_status_checks": [{"context": "ci", "integration_id": 15368},
                                       {"context": "docker-build", "integration_id": 15368}],
        }},
    ])
    return {"id": NAMES.index(name) + 1, "name": name, "target": "branch", "enforcement": "active",
            "conditions": {"ref_name": {"include": [refs[name]], "exclude": []}}, "bypass_actors": [],
            "current_user_can_bypass": "never", "rules": rules}


def _parameters(payload: dict[str, Any], kind: str) -> dict[str, Any]:
    return next(row["parameters"] for row in payload["rules"] if row["type"] == kind)


@pytest.mark.parametrize("name", NAMES)
def test_exact_supported_targets_validate(name: str) -> None:
    assert platform.ruleset_errors(_ruleset(name), integration=name == NAMES[2]) == []


@pytest.mark.parametrize("name", NAMES)
def test_all_delivery_targets_require_owner_review(name: str) -> None:
    payload = _ruleset(name)
    _parameters(payload, "pull_request")["require_code_owner_review"] = False
    assert platform.ruleset_errors(payload, expected_name=name)


@pytest.mark.parametrize("name", NAMES)
@pytest.mark.parametrize("condition", ["unrelated", "excluded", "broad", "missing", "duplicate"])
def test_wrong_or_excluded_ruleset_target_cannot_validate(name: str, condition: str) -> None:
    payload = _ruleset(name)
    target = payload["conditions"]["ref_name"]
    if condition == "missing":
        del payload["conditions"]
    elif condition == "excluded":
        target["exclude"] = list(target["include"])
    elif condition == "unrelated":
        target["include"] = ["refs/heads/unrelated"]
    elif condition == "broad":
        target["include"] = ["~ALL"]
    else:
        target["include"] *= 2
    assert platform.ruleset_errors(payload, integration=name == NAMES[2])


@pytest.mark.parametrize("defect", ["code_owner", "creation", "creation_checks"])
def test_main_protects_code_owners_and_creation(defect: str) -> None:
    payload = _ruleset("protect-main")
    if defect == "code_owner":
        _parameters(payload, "pull_request")["require_code_owner_review"] = False
    elif defect == "creation":
        payload["rules"] = [row for row in payload["rules"] if row["type"] != "creation"]
    else:
        _parameters(payload, "required_status_checks")["do_not_enforce_on_create"] = True
    assert platform.ruleset_errors(payload)


def test_integration_baseline_creation_is_not_blocked() -> None:
    payload = _ruleset("protect-task-integration")
    payload["rules"].append({"type": "creation"})
    assert platform.ruleset_errors(payload, integration=True)


@pytest.mark.parametrize("payload", [{"name": []}, {"name": "unknown"}, {}])
def test_missing_or_ambiguous_rule_identity_fails_closed(payload: dict[str, Any]) -> None:
    assert platform.ruleset_errors(payload)


def test_expected_ruleset_name_is_bound_to_the_lookup() -> None:
    assert platform.ruleset_errors(_ruleset("protect-develop"), expected_name="protect-main")


@pytest.mark.parametrize("field", ["dismiss_stale_reviews_on_push", "require_last_push_approval",
                                   "required_review_thread_resolution", "required_approving_review_count",
                                   "allowed_merge_methods"])
def test_review_conditions_cannot_be_weakened(field: str) -> None:
    payload = _ruleset()
    value: Any = ["squash"] if field == "allowed_merge_methods" else 0 if field == "required_approving_review_count" else False
    _parameters(payload, "pull_request")[field] = value
    assert platform.ruleset_errors(payload)


@pytest.mark.parametrize("defect", ["non_strict", "missing_ci", "missing_docker", "source", "duplicate", "bypass", "duplicate_rule"])
def test_sources_strictness_and_no_bypass_are_enforced(defect: str) -> None:
    payload = _ruleset()
    checks = _parameters(payload, "required_status_checks")
    if defect == "non_strict":
        checks["strict_required_status_checks_policy"] = False
    elif defect in {"missing_ci", "missing_docker"}:
        omitted = "ci" if defect == "missing_ci" else "docker-build"
        checks["required_status_checks"] = [row for row in checks["required_status_checks"] if row["context"] != omitted]
    elif defect == "source":
        checks["required_status_checks"][0]["integration_id"] = None
    elif defect == "duplicate":
        checks["required_status_checks"].append({"context": "ci", "integration_id": 999})
    elif defect == "bypass":
        payload["bypass_actors"] = [{"actor_type": "Integration", "actor_id": 12, "bypass_mode": "always"}]
    else:
        payload["rules"].append(copy.deepcopy(payload["rules"][-1]))
    assert platform.ruleset_errors(payload)


@pytest.fixture
def prepared_root(tmp_path: Path) -> Path:
    directory = tmp_path / ".github" / "agent-first"
    directory.mkdir(parents=True)
    (tmp_path / ".github/CODEOWNERS").write_text("* @ranzuozhou\n", encoding="utf-8")
    for name in NAMES:
        (directory / f"{name}.ruleset.json").write_text(json.dumps(_ruleset(name)), encoding="utf-8")
    (directory / "executor-app-manifest.json").write_text(json.dumps({
        "public": False, "hook_attributes": {"active": False, "url": "https://invalid.invalid/mj-agent-unused-webhook"},
        "default_events": [],
        "default_permissions": {"metadata": "read", "contents": "write", "pull_requests": "write", "workflows": "write"},
    }), encoding="utf-8")
    return tmp_path


def test_owner_coverage_cannot_be_replaced_or_overridden(prepared_root: Path) -> None:
    for value in ("", "* @other-reviewer", "* @ranzuozhou\nscripts/** @other-reviewer"):
        (prepared_root / ".github/CODEOWNERS").write_text(value, encoding="utf-8")
        assert platform.check_local(prepared_root)["state"] == "FAIL"


def test_configuration_is_separate_from_runtime_readiness(prepared_root: Path) -> None:
    result = platform.check_local(prepared_root)
    assert result["state"] == "CONFIG_VALID"
    assert result["platform_canary"] == "NOT_RUN"
    assert result["host_hook"] == "NOT_TESTED"
    assert result["execution_identity"] == result["installation"] == "NOT_ASSESSED"


def test_local_wrong_target_returns_failure_exit(prepared_root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = prepared_root / ".github/agent-first/protect-develop.ruleset.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["conditions"]["ref_name"]["include"] = ["refs/heads/unrelated"]
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert platform.main(["--root", str(prepared_root)]) == 1
    assert json.loads(capsys.readouterr().out)["state"] == "FAIL"


@pytest.mark.parametrize("defect", ["public", "webhook_active", "webhook_url", "events", "missing_hook_url"])
def test_app_manifest_does_not_enable_unsanctioned_events_or_webhook(prepared_root: Path, defect: str) -> None:
    path = prepared_root / ".github/agent-first/executor-app-manifest.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    if defect == "public":
        payload["public"] = True
    elif defect == "webhook_active":
        payload["hook_attributes"]["active"] = True
    elif defect == "webhook_url":
        payload["hook_attributes"]["url"] = "https://unapproved.invalid/receiver"
    elif defect == "events":
        payload["default_events"] = ["push"]
    else:
        del payload["hook_attributes"]["url"]
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert platform.check_local(prepared_root)["state"] == "FAIL"


def _mock_remote(monkeypatch: pytest.MonkeyPatch, *, admin: bool = False, defect: str = "") -> list[str]:
    calls: list[str] = []
    rules = {name: _ruleset(name) for name in NAMES}
    if defect == "main_code_owner":
        _parameters(rules["protect-main"], "pull_request")["require_code_owner_review"] = False
    if defect == "bypass":
        rules["protect-develop"]["current_user_can_bypass"] = "always"

    def get(endpoint: str) -> Any:
        calls.append(endpoint)
        if endpoint.startswith(f"repos/{REPOSITORY}/rulesets?") or endpoint == f"repos/{REPOSITORY}/rulesets":
            return [{"name": name, "id": row["id"]} for name, row in rules.items()]
        if endpoint.startswith(f"repos/{REPOSITORY}/rulesets/"):
            return next(row for row in rules.values() if endpoint.endswith(str(row["id"])))
        if endpoint == f"repos/{REPOSITORY}":
            return {"full_name": REPOSITORY, "permissions": {"admin": admin}, "allow_merge_commit": True,
                    "allow_squash_merge": False, "allow_rebase_merge": False}
        if endpoint.startswith("installation/repositories"):
            if defect == "not_installation":
                raise RuntimeError("installation metadata unavailable")
            repositories = [{"full_name": REPOSITORY}]
            if defect == "multi_repo":
                repositories.append({"full_name": "synthetic/other"})
            return {"total_count": len(repositories), "repositories": repositories}
        raise AssertionError(f"unexpected remote request: {endpoint}")

    monkeypatch.setattr(platform, "_get", get)
    return calls


def test_remote_main_cannot_omit_code_owner_review(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_remote(monkeypatch, defect="main_code_owner")
    report = platform.inspect_platform(REPOSITORY)
    row = next(item for item in report["checks"] if item["name"] == "protect-main")
    assert row["state"] == "NOT_READY"


def test_owner_admin_identity_cannot_become_executor(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_remote(monkeypatch, admin=True)
    result = platform.inspect_platform(REPOSITORY)
    assert result["state"] == result["execution_identity"] == "NOT_READY"
    assert result["platform_canary"] == "NOT_RUN"
    assert result["host_hook"] == "NOT_TESTED"


@pytest.mark.parametrize("defect", ["not_installation", "multi_repo", "bypass"])
def test_observed_unsafe_or_unknown_identity_stays_not_ready(monkeypatch: pytest.MonkeyPatch, defect: str) -> None:
    _mock_remote(monkeypatch, defect=defect)
    result = platform.inspect_platform(REPOSITORY)
    assert result["state"] == result["execution_identity"] == "NOT_READY"


def test_single_repo_token_is_not_proof_of_least_privilege(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_remote(monkeypatch)
    result = platform.inspect_platform(REPOSITORY)
    assert result["installation"] == "VERIFIED_SINGLE_REPOSITORY_TOKEN"
    assert result["app_permissions"] == "NOT_ASSESSED"
    assert result["execution_identity"] == result["state"] == "NOT_READY"


@pytest.mark.parametrize("unexpected", [{"administration": "write"}, {"checks": "write"}, {"workflows": "write"}, {"issues": "write"}])
def test_daily_permission_map_must_be_minimal(unexpected: dict[str, str]) -> None:
    permissions = {"metadata": "read", "contents": "write", "pull_requests": "write"}
    assert platform.app_permission_errors(permissions) == []
    assert platform.app_permission_errors({**permissions, **unexpected})


@pytest.mark.parametrize("permissions", [None, {}, {"metadata": "read", "contents": "write"}, []])
def test_absent_permission_facts_cannot_establish_least_privilege(permissions: Any) -> None:
    assert platform.app_permission_errors(permissions)


def test_queries_are_get_only_and_select_nonsecret_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []

    def run(command: list[str], **kwargs: Any) -> Any:
        calls.append(command)
        return type("ReadResult", (), {"returncode": 0, "stdout": "{}"})()

    monkeypatch.setattr(platform.subprocess, "run", run)
    platform._get(f"repos/{REPOSITORY}")
    platform._get("installation/repositories?per_page=100&page=1")
    for command in calls:
        assert command[:4] == ["gh", "api", "--method", "GET"]
        assert "--jq" in command
        assert "temp_clone_token" not in command[-1]


def test_missing_config_returns_unknown_exit_without_payload(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert platform.main(["--root", str(tmp_path)]) == 2
    result = json.loads(capsys.readouterr().out)
    assert result["state"] == "UNKNOWN"
    assert result["execution"] == "NOT_ATTEMPTED"
