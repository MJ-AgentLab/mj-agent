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


def _executor_observation(phase: str = "daily") -> dict[str, Any]:
    permissions = {"metadata": "read", "contents": "write", "pull_requests": "write"}
    if phase == "bootstrap":
        permissions["workflows"] = "write"
    return {
        "state": "EXECUTOR_VERIFIED", "source": "GITHUB_API_RUNTIME", "repository": REPOSITORY,
        "permission_phase": phase, "token_revocation": "CONFIRMED",
        "app": {"id": 42, "slug": "mj-agent-delivery-executor", "owner": "synthetic",
                "permissions": permissions.copy()},
        "installation": {"id": 63, "app_id": 42, "account": "synthetic",
                         "repository_selection": "selected", "suspended_at": None,
                         "permissions": permissions.copy()},
        "token_grant": {"permissions": permissions.copy(), "total_count": 1,
                        "repositories": [{"id": 91, "full_name": REPOSITORY}]},
    }


@pytest.mark.parametrize("phase", ["daily", "bootstrap"])
def test_real_app_installation_and_token_observations_establish_executor(phase: str) -> None:
    assert platform.executor_identity_errors(_executor_observation(phase), REPOSITORY, phase) == []


@pytest.mark.parametrize("defect", ["claim_file", "repository", "phase", "revocation", "app_id",
                                   "slug", "owner", "installation_id", "installation_app", "account",
                                   "all_repositories", "suspended", "missing_suspension", "token_scope",
                                   "token_repository", "token_repository_id", "missing_app", "missing_grant"])
def test_incomplete_changed_or_mismatched_executor_cannot_pass(defect: str) -> None:
    payload = _executor_observation()
    if defect in {"claim_file", "repository", "phase", "revocation"}:
        key = {"claim_file": "source", "repository": "repository", "phase": "permission_phase",
               "revocation": "token_revocation"}[defect]
        payload[key] = {"claim_file": "LOCAL_CLAIM", "repository": "synthetic/other",
                        "phase": "bootstrap", "revocation": "UNKNOWN"}[defect]
    elif defect in {"app_id", "slug", "owner"}:
        key = {"app_id": "id", "slug": "slug", "owner": "owner"}[defect]
        payload["app"][key] = {"app_id": True, "slug": "other-app", "owner": "other"}[defect]
    elif defect in {"installation_id", "installation_app", "account", "all_repositories", "suspended"}:
        key = {"installation_id": "id", "installation_app": "app_id", "account": "account",
               "all_repositories": "repository_selection", "suspended": "suspended_at"}[defect]
        payload["installation"][key] = {"installation_id": False, "installation_app": 999,
                                        "account": "other", "all_repositories": "all",
                                        "suspended": "2026-01-01T00:00:00Z"}[defect]
    elif defect == "missing_suspension":
        del payload["installation"]["suspended_at"]
    elif defect == "token_scope":
        payload["token_grant"]["total_count"] = 2
    elif defect == "token_repository":
        payload["token_grant"]["repositories"][0]["full_name"] = "synthetic/other"
    elif defect == "token_repository_id":
        payload["token_grant"]["repositories"][0]["id"] = True
    else:
        del payload[{"missing_app": "app", "missing_grant": "token_grant"}[defect]]
    assert platform.executor_identity_errors(payload, REPOSITORY, "daily")


@pytest.mark.parametrize("layer", ["app", "installation", "token_grant"])
@pytest.mark.parametrize("extra", ["administration", "checks", "workflows"])
def test_every_actual_permission_layer_must_remain_minimal(layer: str, extra: str) -> None:
    payload = _executor_observation()
    payload[layer]["permissions"][extra] = "write"
    assert platform.executor_identity_errors(payload, REPOSITORY, "daily")


def _mock_executor(monkeypatch: pytest.MonkeyPatch, *, defect: str = "", admin: bool = False) -> list[str]:
    _mock_remote(monkeypatch, admin=admin)
    calls: list[str] = []

    def observe(root: Path, vault: Path, phase: str, action: str, endpoint: str | None = None) -> dict[str, Any]:
        calls.append(action)
        result = _executor_observation(phase)
        if defect == "invalid_audit" or defect == "identity_changed" and action == "public-get":
            result["token_revocation"] = "UNKNOWN"
        if defect == "identity_rotated" and action == "public-get":
            result["app"]["id"] = result["installation"]["app_id"] = 43
            result["installation"]["id"] = 64
            result["token_grant"]["repositories"][0]["id"] = 92
        if action == "public-get":
            result["data"] = platform._get(str(endpoint))
            if endpoint == f"repos/{REPOSITORY}" and not admin:
                # Installation-token responses need not include an OAuth-user role map.
                del result["data"]["permissions"]
        return result

    monkeypatch.setattr(platform, "_executor_json", observe)
    return calls


def test_opaque_provider_audit_can_verify_config_without_claiming_host_or_acceptance(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _mock_executor(monkeypatch)
    report = platform.inspect_platform(REPOSITORY, executor_vault=Path("synthetic-vault"))
    assert calls[0] == "audit" and "public-get" in calls
    assert report["state"] == "CONFIG_VERIFIED"
    assert report["execution_identity"] == report["app_permissions"] == "VERIFIED"
    assert report["platform_canary"] == "NOT_RUN" and report["host_hook"] == "NOT_TESTED"
    assert report["owner_authorization"] == "NOT_ASSESSED"


def test_failed_executor_audit_stops_before_more_token_or_provider_requests(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _mock_executor(monkeypatch, defect="invalid_audit")
    report = platform.inspect_platform(REPOSITORY, executor_vault=Path("synthetic-vault"))
    assert calls == ["audit"]
    assert report["state"] == "NOT_READY"


def test_changed_executor_during_observation_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_executor(monkeypatch, defect="identity_changed")
    with pytest.raises(ValueError, match="identity changed"):
        platform.inspect_platform(REPOSITORY, executor_vault=Path("synthetic-vault"))


def test_legal_but_different_executor_cannot_reuse_first_observation(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _mock_executor(monkeypatch, defect="identity_rotated")
    with pytest.raises(ValueError, match="identity changed"):
        platform.inspect_platform(REPOSITORY, executor_vault=Path("synthetic-vault"))
    assert calls == ["audit", "public-get"]


def test_admin_metadata_cannot_be_laundered_by_otherwise_valid_app_claims(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_executor(monkeypatch, admin=True)
    report = platform.inspect_platform(REPOSITORY, executor_vault=Path("synthetic-vault"))
    assert report["state"] == "NOT_READY"


def test_executor_request_uses_only_the_controlled_cli_not_a_claim_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def run(command: list[str], **kwargs: Any) -> Any:
        calls.append(command)
        return type("ExecutorResult", (), {"returncode": 0, "stdout": json.dumps(_executor_observation())})()

    monkeypatch.setattr(platform.subprocess, "run", run)
    platform._executor_json(tmp_path, tmp_path / "sealed-vault", "daily", "public-get", f"repos/{REPOSITORY}")
    assert calls[0][1] == "-I"
    assert Path(calls[0][2]) == tmp_path / "scripts/sdd/delivery_executor.py"
    assert calls[0][3] == "public-get" and calls[0][-2:] == ["--endpoint", f"/repos/{REPOSITORY}"]
    assert "--permission-phase" in calls[0]


def test_executor_python_startup_rejects_ambient_credentials_and_import_injection(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    captured: list[tuple[list[str], dict[str, Any]]] = []
    for name in ("GH_TOKEN", "GITHUB_TOKEN", "GIT_CONFIG_COUNT", "GIT_CONFIG_VALUE_0", "GIT_TRACE",
                 "HTTPS_PROXY", "SSLKEYLOGFILE", "PYTHONPATH", "PYTHONHOME", "PYTHONUSERBASE",
                 "ARK_API_KEY", "GH_DEBUG"):
        monkeypatch.setenv(name, "SYNTHETIC_OLD_CREDENTIAL_OR_STARTUP_INJECTION")

    def run(command: list[str], **kwargs: Any) -> Any:
        captured.append((command, kwargs))
        return type("ExecutorResult", (), {"returncode": 0, "stdout": json.dumps(_executor_observation())})()

    monkeypatch.setattr(platform.subprocess, "run", run)
    platform._executor_json(tmp_path, tmp_path / "new-app-vault", "daily", "audit")
    command, options = captured[0]
    assert command[1] == "-I"  # Disables Python environment variables and the user site before imports.
    assert options["cwd"] == tmp_path
    assert set(options["env"]) <= set(platform._EXECUTOR_ENV)
    assert "SYNTHETIC_OLD_CREDENTIAL_OR_STARTUP_INJECTION" not in json.dumps(options["env"])


def test_actual_executor_child_starts_isolated_before_candidate_imports(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    script = tmp_path / "scripts/sdd/delivery_executor.py"
    script.parent.mkdir(parents=True)
    script.write_text(
        "import json, os, sys\n"
        "print(json.dumps({'isolated':sys.flags.isolated, "
        "'credential_present':'GH_TOKEN' in os.environ, "
        "'injection_loaded':'sitecustomize' in sys.modules}))\n", encoding="utf-8",
    )
    injection = tmp_path / "untrusted-import"
    injection.mkdir()
    (injection / "sitecustomize.py").write_text("print('SHADOW_STARTUP_IMPORTED')\n", encoding="utf-8")
    monkeypatch.setenv("PYTHONPATH", str(injection))
    monkeypatch.setenv("GH_TOKEN", "SYNTHETIC_OLD_CREDENTIAL")
    assert platform._executor_json(tmp_path, tmp_path / "new-app-vault", "daily", "audit") == {
        "isolated": 1, "credential_present": False, "injection_loaded": False,
    }


def _hidden_actors(monkeypatch: pytest.MonkeyPatch, *, manager: str = "ranzuozhou",
                   defect: str = "") -> list[str]:
    _mock_executor(monkeypatch)
    metadata_get = platform._get
    management_calls: list[str] = []

    def observe(root: Path, vault: Path, phase: str, action: str, endpoint: str | None = None) -> dict[str, Any]:
        result = _executor_observation(phase)
        if action == "public-get":
            result["data"] = copy.deepcopy(metadata_get(str(endpoint)))
            if isinstance(result["data"], dict):
                result["data"].pop("bypass_actors", None)
                if endpoint == f"repos/{REPOSITORY}":
                    result["data"].pop("permissions", None)
        return result

    def get(endpoint: str) -> Any:
        management_calls.append(endpoint)
        if endpoint == "user":
            return {"login": manager, "type": "User"}
        result = copy.deepcopy(metadata_get(endpoint))
        if isinstance(result, dict) and "bypass_actors" in result:
            if defect == "changed_protection":
                _parameters(result, "pull_request")["require_last_push_approval"] = False
            elif defect == "hidden_bypass":
                result["bypass_actors"] = [{"actor_id": 5, "actor_type": "RepositoryRole", "bypass_mode": "always"}]
            elif defect == "still_hidden":
                del result["bypass_actors"]
        return result

    monkeypatch.setattr(platform, "_executor_json", observe)
    monkeypatch.setattr(platform, "_get", get)
    return management_calls


def test_hidden_bypass_list_is_unknown_without_management_observation(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _hidden_actors(monkeypatch)
    report = platform.inspect_platform(REPOSITORY, executor_vault=Path("synthetic-vault"))
    assert report["state"] == "NOT_READY"
    assert "user" not in calls
    assert all(row["state"] == "NOT_READY" for row in report["checks"])


def test_named_owner_read_only_observation_supplies_only_hidden_matching_fact(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _hidden_actors(monkeypatch)
    report = platform.inspect_platform(REPOSITORY, executor_vault=Path("synthetic-vault"), management_inspect=True)
    assert report["state"] == "CONFIG_VERIFIED"
    assert report["execution_identity"] == "VERIFIED"
    assert report["management_observation"] == "NAMED_OWNER_METADATA_GET"
    assert all(row["bypass_actors_source"] == "NAMED_OWNER_MANAGEMENT_GET" for row in report["checks"])
    assert calls.count("user") == 1


def test_management_cannot_replace_owner_or_mismatched_protection(monkeypatch: pytest.MonkeyPatch) -> None:
    _hidden_actors(monkeypatch, manager="different-user")
    with pytest.raises(ValueError, match="named Owner"):
        platform.inspect_platform(REPOSITORY, executor_vault=Path("synthetic-vault"), management_inspect=True)
    _hidden_actors(monkeypatch, defect="changed_protection")
    with pytest.raises(ValueError, match="observations differ"):
        platform.inspect_platform(REPOSITORY, executor_vault=Path("synthetic-vault"), management_inspect=True)


@pytest.mark.parametrize("defect", ["hidden_bypass", "still_hidden"])
def test_management_visibility_cannot_launder_bypass_or_absence(monkeypatch: pytest.MonkeyPatch, defect: str) -> None:
    _hidden_actors(monkeypatch, defect=defect)
    report = platform.inspect_platform(REPOSITORY, executor_vault=Path("synthetic-vault"), management_inspect=True)
    assert report["state"] == "NOT_READY"


def test_management_cannot_act_as_missing_executor(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_remote(monkeypatch)
    with pytest.raises(ValueError, match="separate executor"):
        platform.inspect_platform(REPOSITORY, management_inspect=True)
