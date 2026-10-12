"""Read-only validation of prepared and observed Agent-first platform controls.

No App creation, authentication change, secret read, rule update or merge occurs.
Static configuration checks do not prove installation, hook loading or canaries.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

_TARGETS = {"protect-develop": "refs/heads/develop", "protect-main": "refs/heads/main",
            "protect-task-integration": "refs/heads/feature/task-*-integration"}
_DAILY_PERMISSIONS = {"metadata": "read", "contents": "write", "pull_requests": "write"}
_DISABLED_WEBHOOK_URL = "https://invalid.invalid/mj-agent-unused-webhook"


def code_owner_errors(text: str) -> list[str]:
    """The transition requires this named Owner for every candidate path."""
    rows = [line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    return [] if rows == ["* @ranzuozhou"] else ["named Owner coverage missing or overridden"]


def app_permission_errors(permissions: Any, *, bootstrap: bool = False) -> list[str]:
    """Validate granted App permission metadata, never infer it from repo role flags."""
    expected = {**_DAILY_PERMISSIONS, **({"workflows": "write"} if bootstrap else {})}
    if permissions != expected:
        return ["missing or unexpected granted App permissions; daily identity must be minimal"]
    return []


def ruleset_errors(payload: dict[str, Any], *, integration: bool = False,
                   expected_name: str | None = None) -> list[str]:
    if not isinstance(payload, dict):
        return ["malformed ruleset"]
    errors: list[str] = []
    name = expected_name or ("protect-task-integration" if integration else payload.get("name"))
    if not isinstance(name, str):
        return ["missing ruleset identity"]
    if name not in _TARGETS or payload.get("name") != name:
        errors.append("missing or unexpected ruleset identity")
    conditions = payload.get("conditions")
    refs = conditions.get("ref_name") if isinstance(conditions, dict) else None
    if (not isinstance(conditions, dict) or set(conditions) != {"ref_name"}
            or not isinstance(refs, dict) or set(refs) != {"include", "exclude"}
            or refs.get("include") != [_TARGETS.get(name)]
            or refs.get("exclude") != []):
        errors.append("ruleset must include only its exact intended target with no exclusions")
    rules: dict[str, Any] = {}
    entries = payload.get("rules")
    if not isinstance(entries, list):
        errors.append("missing rule list")
        entries = []
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("type"), str):
            errors.append("malformed protection rule")
            continue
        kind = entry["type"]
        if kind in rules:
            errors.append("duplicate protection rule")
        rules[kind] = entry
    if payload.get("target") != "branch" or payload.get("enforcement") != "active":
        errors.append("ruleset is not an active branch rule")
    if payload.get("bypass_actors") != []:
        errors.append("bypass actors require a separately controlled emergency route")
    if not {"deletion", "non_fast_forward", "pull_request", "required_status_checks"}.issubset(rules):
        errors.append("missing required protection")
    review = rules.get("pull_request", {}).get("parameters", {})
    if not isinstance(review, dict):
        errors.append("malformed review parameters")
        review = {}
    count = review.get("required_approving_review_count")
    if type(count) is not int or count < 1:
        errors.append("missing effective outcome approval")
    for field in ("dismiss_stale_reviews_on_push", "require_last_push_approval", "required_review_thread_resolution"):
        if review.get(field) is not True:
            errors.append(f"missing review condition: {field}")
    if review.get("allowed_merge_methods") != ["merge"]:
        errors.append("unexpected merge method")
    if review.get("require_code_owner_review") is not True:
        errors.append("Owner Code Owner review missing")
    if name == "protect-main":
        if "creation" not in rules:
            errors.append("main creation protection missing")
    elif "creation" in rules:
        errors.append("creation protection would block the intended baseline creation")
    checks = rules.get("required_status_checks", {}).get("parameters", {})
    if not isinstance(checks, dict):
        errors.append("malformed check parameters")
        checks = {}
    if checks.get("strict_required_status_checks_policy") is not True:
        errors.append("checks do not require the current base")
    contexts: dict[str, Any] = {}
    required = checks.get("required_status_checks")
    if not isinstance(required, list):
        errors.append("missing check list")
        required = []
    for row in required:
        if not isinstance(row, dict) or not isinstance(row.get("context"), str):
            errors.append("malformed required check")
            continue
        context = row["context"]
        if context in contexts:
            errors.append("duplicate required check context")
        contexts[context] = row.get("integration_id")
    if not {"ci", "docker-build"}.issubset(contexts):
        errors.append("ci and docker-build must both be required")
    if any(contexts.get(name) != 15368 for name in ("ci", "docker-build")):
        errors.append("required checks lack observed GitHub Actions source binding")
    if checks.get("do_not_enforce_on_create") is not (name == "protect-task-integration"):
        errors.append("check creation policy does not match the exact target")
    return errors


def check_local(root: Path) -> dict[str, Any]:
    directory = root / ".github" / "agent-first"
    rows = []
    errors = code_owner_errors((root / ".github/CODEOWNERS").read_text(encoding="utf-8"))
    rows.append({"name": "Owner coverage", "state": "FAIL" if errors else "CONFIG_VALID", "errors": errors})
    for name in ("protect-develop", "protect-main", "protect-task-integration"):
        path = directory / f"{name}.ruleset.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        errors = ruleset_errors(payload, expected_name=name)
        rows.append({"name": name, "state": "FAIL" if errors else "CONFIG_VALID", "errors": errors})
    app = json.loads((directory / "executor-app-manifest.json").read_text(encoding="utf-8"))
    errors = app_permission_errors(app.get("default_permissions"), bootstrap=True)
    if app.get("public") is not False:
        errors.append("executor App must be private")
    hook = app.get("hook_attributes")
    if (not isinstance(hook, dict) or hook.get("active") is not False
            or hook.get("url") != _DISABLED_WEBHOOK_URL):
        errors.append("webhook must stay inactive with the closed unused placeholder URL")
    if app.get("default_events") != []:
        errors.append("executor App must not subscribe to events")
    rows.append({"name": "executor-app", "state": "FAIL" if errors else "CONFIG_VALID", "errors": errors})
    return {"state": "CONFIG_VALID" if all(row["state"] == "CONFIG_VALID" for row in rows) else "FAIL",
            "checks": rows, "installation": "NOT_ASSESSED", "execution_identity": "NOT_ASSESSED",
            "app_permissions": "NOT_ASSESSED", "prepared_permission_phase": "BOOTSTRAP_TEMPORARY_WORKFLOWS",
            "platform_canary": "NOT_RUN", "host_hook": "NOT_TESTED",
            "gate_definition_tamper_resistance": "DEFERRED", "owner_authorization": "NOT_ASSESSED"}


def _get(endpoint: str) -> Any:
    command = ["gh", "api", "--method", "GET", endpoint]
    if re.fullmatch(r"repos/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", endpoint):
        # Repository JSON can contain temp_clone_token: select only non-secret facts in gh.
        command.extend(["--jq", "{full_name,permissions,allow_merge_commit,allow_squash_merge,allow_rebase_merge}"])
    elif endpoint.startswith("installation/repositories?"):
        command.extend(["--jq", "{total_count,repositories:[.repositories[]|{full_name}]}"])
    proc = subprocess.run(command, check=False, capture_output=True, text=True, timeout=30)
    if proc.returncode != 0:
        raise RuntimeError(f"GitHub metadata query failed (exit {proc.returncode})")
    return json.loads(proc.stdout)


def inspect_platform(repository: str) -> dict[str, Any]:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("explicit owner/repository required")
    inventory = _get(f"repos/{repository}/rulesets?per_page=100")
    if not isinstance(inventory, list) or not all(isinstance(item, dict) for item in inventory):
        raise ValueError("malformed ruleset inventory")
    rows = []
    for name in ("protect-develop", "protect-main", "protect-task-integration"):
        found = [item for item in inventory if item.get("name") == name]
        if len(found) != 1:
            rows.append({"name": name, "state": "NOT_READY", "errors": ["rule missing or ambiguous"]})
            continue
        actual = _get(f"repos/{repository}/rulesets/{found[0]['id']}")
        errors = ruleset_errors(actual, expected_name=name)
        if actual.get("current_user_can_bypass") != "never":
            errors.append("current identity bypass is allowed or unknown")
        rows.append({"name": name, "state": "NOT_READY" if errors else "CONFIG_VERIFIED", "errors": errors,
                     "current_identity_can_bypass": actual.get("current_user_can_bypass", "UNKNOWN")})
    repo = _get(f"repos/{repository}")
    identity_errors = []
    if repo.get("full_name", "").casefold() != repository.casefold():
        identity_errors.append("repository identity mismatch")
    role = repo.get("permissions")
    if not isinstance(role, dict) or role.get("admin") is not False:
        identity_errors.append("Owner/admin or unknown role cannot be the daily executor")
    if (repo.get("allow_merge_commit") is not True or repo.get("allow_squash_merge") is not False
            or repo.get("allow_rebase_merge") is not False):
        identity_errors.append("repository merge methods do not match merge-only delivery")
    if any(row["state"] != "CONFIG_VERIFIED" for row in rows):
        identity_errors.append("required rulesets are not fully observed without bypass")
    installation = "NOT_READY"
    if isinstance(role, dict) and role.get("admin") is False:
        try:
            access = _get("installation/repositories?per_page=100&page=1")
            repositories = access.get("repositories")
            if (type(access.get("total_count")) is int and access["total_count"] == 1
                    and isinstance(repositories, list) and len(repositories) == 1
                    and isinstance(repositories[0], dict)
                    and repositories[0].get("full_name", "").casefold() == repository.casefold()):
                installation = "VERIFIED_SINGLE_REPOSITORY_TOKEN"
            else:
                identity_errors.append("installation token does not have exact single-repository access")
        except (RuntimeError, OSError, ValueError, TypeError, AttributeError, subprocess.TimeoutExpired):
            identity_errors.append("installation-token identity could not be established")
    # /installation/repositories proves token kind/scope, not granted App permissions.
    # The JWT-only /repos/{repo}/installation endpoint cannot be used with this token:
    # https://docs.github.com/en/rest/apps/apps#get-a-repository-installation-for-the-authenticated-app
    identity_errors.append("granted App permissions require independently observed trusted metadata")
    return {"state": "NOT_READY", "checks": rows, "execution_identity": "NOT_READY",
            "installation": installation, "app_permissions": "NOT_ASSESSED", "identity_errors": identity_errors,
            "platform_canary": "NOT_RUN", "host_hook": "NOT_TESTED",
            "gate_definition_tamper_resistance": "DEFERRED", "owner_authorization": "NOT_ASSESSED"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--repository", default="MJ-AgentLab/mj-agent")
    parser.add_argument("--inspect", action="store_true", help="read remote metadata; never apply changes")
    args = parser.parse_args(argv)
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", args.repository):
        parser.error("explicit owner/repository required")
    try:
        report = inspect_platform(args.repository) if args.inspect else check_local(args.root)
    except (OSError, ValueError, RuntimeError, TypeError, KeyError, AttributeError, subprocess.TimeoutExpired):
        print(json.dumps({"state": "UNKNOWN", "error": "required platform/configuration facts unavailable", "execution": "NOT_ATTEMPTED"}))
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["state"] == "CONFIG_VALID" else 1


if __name__ == "__main__":
    raise SystemExit(main())
