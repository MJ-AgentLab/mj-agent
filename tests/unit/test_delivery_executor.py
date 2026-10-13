"""Synthetic controller tests: no registration, credentials or live services."""

from __future__ import annotations

import base64
import copy
import hashlib
import json
import os
import subprocess
import sys
import threading
import urllib.parse
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from http.client import HTTPConnection
from pathlib import Path

import pytest
from scripts.sdd import delivery_executor as executor


class SyntheticCipher:
    def protect(self, value: bytes) -> bytes:
        return b"synthetic-cipher:" + value[::-1]

    def unprotect(self, value: bytes) -> bytes:
        assert value.startswith(b"synthetic-cipher:")
        return value.removeprefix(b"synthetic-cipher:")[::-1]


def conversion() -> dict:
    return {"id": 777, "slug": executor.APP_SLUG, "name": executor.APP_SLUG,
            "owner": {"login": executor.OWNER}, "permissions": executor.BOOTSTRAP_PERMISSIONS,
            "events": [], "pem": "SYNTHETIC_PRIVATE_MATERIAL", "client_secret": "DISCARDED_CLIENT_VALUE",
            "webhook_secret": "DISCARDED_WEBHOOK_VALUE"}


def vault(tmp_path: Path) -> executor.SecretVault:
    return executor.SecretVault(tmp_path / executor.APP_SLUG, repo_root=tmp_path / "repo",
                                cipher=SyntheticCipher())


def test_registration_consumes_state_nonce_and_never_returns_credentials(tmp_path: Path) -> None:
    store = vault(tmp_path)
    calls = []

    def api(method: str, path: str, *, credential: str | None = None, body: dict | None = None):
        calls.append((method, path))
        return conversion()

    registration = executor.Registration(store, api=api)
    state, nonce = registration.begin()
    result = registration.complete("SYNTHETIC_CODE", state, nonce)
    assert result == {"status": "REGISTERED", "app_id": 777, "app_slug": executor.APP_SLUG,
                      "repository": executor.REPOSITORY}
    output = json.dumps(result)
    assert all(value not in output for value in ("SYNTHETIC_CODE", "PRIVATE", "CLIENT", "WEBHOOK"))
    assert b"SYNTHETIC_PRIVATE_MATERIAL" not in store.path.read_bytes()
    with pytest.raises(executor.PublicError):
        registration.complete("SYNTHETIC_CODE", state, nonce)
    assert len(calls) == 1


@pytest.mark.parametrize("mutation", ["state", "nonce", "expired", "bad_slug", "extra_grant"])
def test_invalid_registration_never_stores_a_secret(tmp_path: Path, mutation: str) -> None:
    store = vault(tmp_path)
    now = [100.0]
    response = conversion()
    if mutation == "bad_slug":
        response["slug"] = "unrelated-app"
    if mutation == "extra_grant":
        response["permissions"] = {**executor.BOOTSTRAP_PERMISSIONS, "administration": "write"}
    registration = executor.Registration(store, api=lambda *a, **k: response, clock=lambda: now[0])
    state, nonce = registration.begin()
    if mutation == "state":
        state = "different"
    if mutation == "nonce":
        nonce = "different"
    if mutation == "expired":
        now[0] += 3601
    with pytest.raises(executor.PublicError):
        registration.complete("SYNTHETIC_CODE", state, nonce)
    assert not store.path.exists()


def test_existing_vault_and_uncertain_attempt_are_not_overwritten(tmp_path: Path) -> None:
    store = vault(tmp_path)
    registration = executor.Registration(store, api=lambda *a, **k: conversion())
    state, nonce = registration.begin()
    registration.complete("SYNTHETIC_CODE", state, nonce)
    before = store.path.read_bytes()
    with pytest.raises(executor.PublicError):
        executor.Registration(store, api=lambda *a, **k: conversion()).begin()
    assert store.path.read_bytes() == before


@pytest.mark.skipif(os.name != "nt", reason="Windows user DPAPI only; synthetic bytes only")
def test_actual_windows_dpapi_roundtrip_of_synthetic_bytes() -> None:
    cipher = executor.WindowsDPAPI()
    payload = b"synthetic-public-fixture-no-service-credential"
    protected = cipher.protect(payload)
    assert payload not in protected
    assert cipher.unprotect(protected) == payload


class SyntheticAPI:
    def __init__(self, defect: str = "") -> None:
        self.calls = []
        self.defect = defect

    def __call__(self, method: str, path: str, *, credential: str | None = None, body: dict | None = None):
        self.calls.append((method, path, body))
        installation = {"id": 123, "app_id": 777, "account": {"login": executor.OWNER},
                        "repository_selection": "selected", "permissions": executor.BOOTSTRAP_PERMISSIONS,
                        "suspended_at": "2026-01-01T00:00:00Z" if self.defect == "suspended" else None}
        if path == "/app":
            return conversion()
        if path == "/app/installations?per_page=100":
            return [installation, installation] if self.defect == "multi_install" else [installation]
        if path == f"/repos/{executor.REPOSITORY}/installation":
            if self.defect == "admin":
                installation["permissions"] = {**executor.BOOTSTRAP_PERMISSIONS, "administration": "write"}
            return installation
        if method == "POST" and path == "/app/installations/123/access_tokens":
            assert body == {"repositories": [executor.REPO_NAME], "permissions": executor.BOOTSTRAP_PERMISSIONS}
            if self.defect == "mint_unknown":
                raise TimeoutError("SYNTHETIC_JWT private upstream request")
            expiry = (datetime.now(UTC) + timedelta(minutes=59)).isoformat()
            if self.defect == "long_ttl":
                expiry = "2099-01-01T00:00:00Z"
            if self.defect == "invalid_ttl":
                expiry = "SYNTHETIC_SECRET_IN_EXPIRY"
            return {"token": "SYNTHETIC_INSTALLATION_TOKEN", "permissions": executor.BOOTSTRAP_PERMISSIONS,
                    "expires_at": expiry}
        if path == "/installation/repositories":
            return {"total_count": True if self.defect == "bool_count" else (2 if self.defect == "multi_repo" else 1),
                    "repositories": [{"id": 456, "full_name": executor.REPOSITORY}]}
        if method == "DELETE" and path == "/installation/token":
            if self.defect == "revoke":
                raise RuntimeError("SYNTHETIC_INSTALLATION_TOKEN must stay private")
            return {}
        if path == f"/repos/{executor.REPOSITORY}":
            return {"id": 456, "full_name": executor.REPOSITORY, "private": True,
                    "token": "HIDDEN_EXTRA", "credentials": "HIDDEN_EXTRA"}
        raise AssertionError("unexpected synthetic endpoint")


def broker(tmp_path: Path, api: SyntheticAPI) -> executor.Controller:
    store = vault(tmp_path)
    store.save(conversion())
    return executor.Controller(store, api=api, signer=lambda *args: "SYNTHETIC_JWT")


def allow_mocked_toolchain(monkeypatch: pytest.MonkeyPatch) -> None:
    """Only command-shape unit tests; real preflight cases below use actual Git."""
    @contextmanager
    def trusted(root):
        yield {"GIT_DIR": str(root / "synthetic-git-dir"), "GIT_COMMON_DIR": str(root / "synthetic-common-dir"),
               "GIT_WORK_TREE": str(root), "hooks": str(root / "synthetic-empty-hooks")}

    monkeypatch.setattr(executor, "_trusted_toolchain", trusted)


def test_audit_proves_actual_mocked_grants_and_scope_then_revokes(tmp_path: Path) -> None:
    api = SyntheticAPI()
    result = broker(tmp_path, api).audit("bootstrap")
    assert result["source"] == "GITHUB_API_RUNTIME"
    assert result["state"] == "EXECUTOR_VERIFIED"
    assert result["repository"] == executor.REPOSITORY
    assert result["permission_phase"] == "bootstrap"
    assert result["token_grant"]["total_count"] == 1
    assert result["app"]["permissions"] == executor.BOOTSTRAP_PERMISSIONS
    assert result["token_revocation"] == "CONFIRMED"
    assert api.calls[-1][:2] == ("DELETE", "/installation/token")
    assert "SYNTHETIC" not in json.dumps(result)


@pytest.mark.parametrize("defect", ["admin", "multi_install", "multi_repo", "suspended", "long_ttl", "invalid_ttl", "bool_count"])
def test_unsafe_observed_grants_never_become_ready(tmp_path: Path, defect: str) -> None:
    api = SyntheticAPI(defect)
    with pytest.raises(executor.PublicError):
        broker(tmp_path, api).audit("bootstrap")
    if defect in {"multi_repo", "long_ttl", "invalid_ttl", "bool_count"}:
        assert api.calls[-1][:2] == ("DELETE", "/installation/token")


def test_revocation_failure_is_public_unknown_without_secret(tmp_path: Path) -> None:
    result = broker(tmp_path, SyntheticAPI("revoke")).audit("bootstrap")
    assert result["token_revocation"] == "UNKNOWN"
    assert result["state"] == "UNKNOWN"
    assert "SYNTHETIC_INSTALLATION_TOKEN" not in json.dumps(result)


def test_public_get_only_returns_allowlisted_fields(tmp_path: Path) -> None:
    result = broker(tmp_path, SyntheticAPI()).public_get(f"/repos/{executor.REPOSITORY}", "bootstrap")
    assert result["data"] == {"id": 456, "full_name": executor.REPOSITORY, "private": True}
    assert "HIDDEN_EXTRA" not in json.dumps(result)


@pytest.mark.parametrize("endpoint", ["/user", "/repos/other/repo", "/app-manifests/secret/conversions",
                                      f"/repos/{executor.REPOSITORY}/rulesets/1?x=secret"])
def test_unapproved_endpoint_never_reaches_network(tmp_path: Path, endpoint: str) -> None:
    api = SyntheticAPI()
    with pytest.raises(executor.PublicError):
        broker(tmp_path, api).public_get(endpoint, "bootstrap")
    assert api.calls == []


def test_cli_does_not_offer_vault_dump_arbitrary_exec_or_api(capsys: pytest.CaptureFixture[str]) -> None:
    assert executor.main(["dump", "SYNTHETIC_PRIVATE_VALUE"]) == 2
    assert "SYNTHETIC_PRIVATE_VALUE" not in capsys.readouterr().out


def test_child_environment_never_inherits_authentication_or_trace(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("GH_TOKEN", "GITHUB_TOKEN", "GH_DEBUG", "GIT_TRACE", "GIT_CURL_VERBOSE", "ARK_API_KEY"):
        monkeypatch.setenv(name, "EXISTING_FORBIDDEN_CREDENTIAL")
    result = executor.child_environment("SYNTHETIC_NEW_TOKEN", Path("temporary-profile"))
    assert "EXISTING_FORBIDDEN_CREDENTIAL" not in json.dumps(result)
    assert result["GH_TOKEN"] == "SYNTHETIC_NEW_TOKEN"
    assert all(name not in result for name in ("GH_DEBUG", "GIT_TRACE", "GIT_CURL_VERBOSE", "ARK_API_KEY"))


def test_token_mint_timeout_is_not_retried_and_has_safe_uncertainty(tmp_path: Path) -> None:
    api = SyntheticAPI("mint_unknown")
    with pytest.raises(executor.PublicError) as caught:
        broker(tmp_path, api).audit("bootstrap")
    assert caught.value.details["side_effects"] == "TOKEN_MAY_HAVE_BEEN_CREATED"
    assert caught.value.details["retry"] == "FORBIDDEN_PENDING_RECONCILIATION"
    assert len([row for row in api.calls if row[0] == "POST"]) == 1
    assert "SYNTHETIC" not in json.dumps(caught.value.details)


@pytest.mark.parametrize("name", [".env.synthetic-forbidden", "secret.pem", "body.txt::$DATA", "body.txt."])
def test_pr_body_secret_and_alias_paths_are_rejected_before_metadata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str,
) -> None:
    controller = broker(tmp_path, SyntheticAPI())
    calls = []
    monkeypatch.setattr(Path, "is_file", lambda path: calls.append(str(path)) or True)
    with pytest.raises(executor.PublicError):
        controller.execute("pr-create", {"head": "maintain/task", "base": "develop", "title": "Governance",
                                         "body_file": str(tmp_path / name)}, tmp_path, "bootstrap")
    assert calls == []  # No candidate secret or Windows alias is inspected.


def test_command_failure_revokes_token_without_exposing_captured_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = SyntheticAPI()
    controller = broker(tmp_path, api)
    allow_mocked_toolchain(monkeypatch)
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(
        a[0], 1, "SYNTHETIC_INSTALLATION_TOKEN", "SYNTHETIC_JWT"))
    with pytest.raises(executor.PublicError) as caught:
        controller.execute("merge", {"pr": "12", "head_sha": "a" * 40}, tmp_path, "bootstrap")
    assert caught.value.details["token_revocation"] == "CONFIRMED"
    assert "SYNTHETIC" not in json.dumps(caught.value.details)
    assert api.calls[-1][:2] == ("DELETE", "/installation/token")


@pytest.mark.parametrize("mode", ["success", "conversion_timeout", "invalid_callback"])
def test_loopback_callback_always_removes_code_without_request_logs(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], mode: str,
) -> None:
    calls = []

    def api(*args, **kwargs):
        calls.append(args)
        if mode == "conversion_timeout":
            raise TimeoutError("SYNTHETIC_PRIVATE_MATERIAL must never appear")
        return conversion()

    server, registration = executor.make_server(vault(tmp_path), api=api)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        assert server.server_address[0] == "127.0.0.1"
        connection = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        connection.request("GET", "/register")
        response = connection.getresponse()
        assert response.status == 200
        cookie = response.getheader("Set-Cookie").split(";", 1)[0]
        response.read()
        query = urllib.parse.urlencode({"state": registration._state, "code": "SYNTHETIC_CODE"})
        if mode == "invalid_callback":
            query += "&code=SYNTHETIC_DUPLICATE"
        connection.request("GET", f"/manifest/callback?{query}", headers={"Cookie": cookie})
        response = connection.getresponse()
        assert response.status == 303
        assert response.getheader("Location") == "/result"
        assert response.read() == b""
        if mode != "invalid_callback":
            registration._worker.join(timeout=5)
        connection.request("GET", "/result")
        response = connection.getresponse()
        public = json.loads(response.read())
        assert public["status"] == {"success": "REGISTERED", "conversion_timeout": "UNKNOWN",
                                     "invalid_callback": "ERROR"}[mode]
        assert "SYNTHETIC" not in json.dumps(public)
        assert "SYNTHETIC" not in str(capsys.readouterr())
        if mode != "invalid_callback":
            assert len(calls) == 1
        connection.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_loopback_rejects_foreign_host_without_starting_registration(tmp_path: Path) -> None:
    server, registration = executor.make_server(vault(tmp_path), api=lambda *a, **k: conversion())
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        connection = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        connection.request("GET", "/register", headers={"Host": "attacker.invalid"})
        response = connection.getresponse()
        assert response.status == 400
        response.read()
        assert registration.result["status"] == "NOT_STARTED"
        assert not registration.vault.attempt.exists()
        connection.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_rs256_signer_uses_short_jwt_with_synthetic_key_only() -> None:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding, rsa

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    encoded = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                serialization.NoEncryption())
    jwt = executor._private_jwt({"app_id": 777, "pem": encoded.decode("ascii")})
    head, payload, signature = jwt.split(".")
    def decode(value: str) -> bytes:
        return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    assert json.loads(decode(head)) == {"alg": "RS256", "typ": "JWT"}
    claims = json.loads(decode(payload))
    assert claims["iss"] == "777"
    assert claims["exp"] - claims["iat"] == 600
    key.public_key().verify(decode(signature), f"{head}.{payload}".encode("ascii"),
                            padding.PKCS1v15(), hashes.SHA256())


def test_push_requires_actual_push_destination_not_only_fetch_url(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    controller = broker(tmp_path, SyntheticAPI())
    allow_mocked_toolchain(monkeypatch)
    commands = []

    def run(command, **kwargs):
        commands.append(command)
        if command[-2:] == ["rev-parse", "HEAD"]:
            output = "a" * 40
        elif command[-2:] == ["branch", "--show-current"]:
            output = "maintain/task"
        elif "get-url" in command:
            output = "https://github.com/unapproved/repository.git" if "--push" in command else f"https://github.com/{executor.REPOSITORY}.git"
        else:
            return subprocess.CompletedProcess(command, 0, "", "")
        return subprocess.CompletedProcess(command, 0, output, "")

    monkeypatch.setattr(subprocess, "run", run)
    with pytest.raises(executor.PublicError):
        controller.execute("push", {"branch": "maintain/task", "head_sha": "a" * 40}, tmp_path, "bootstrap")
    assert not any("push" in command for command in commands)


def test_pr_create_is_fixed_base_and_secret_free_subprocess_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    controller = broker(tmp_path, SyntheticAPI())
    allow_mocked_toolchain(monkeypatch)
    body = tmp_path / "reviewable-pr-body.md"
    body.write_text("Synthetic public PR body", encoding="utf-8")
    commands = []

    def run(command, **kwargs):
        commands.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, f"https://github.com/{executor.REPOSITORY}/pull/12\n",
                                           "SYNTHETIC_PRIVATE_STDERR")

    monkeypatch.setattr(subprocess, "run", run)
    result = controller.execute("pr-create", {"head": "maintain/task", "base": "develop", "title": "Governance",
                                             "body_file": str(body)}, tmp_path, "bootstrap")
    command, kwargs = commands[0]
    assert command[:3] == ["gh", "pr", "create"]
    assert command[command.index("--base") + 1] == "develop"
    assert command[command.index("--repo") + 1] == executor.REPOSITORY
    assert kwargs.get("shell") is not True
    assert result["token_revocation"] == "CONFIRMED"
    assert "SYNTHETIC" not in json.dumps(result)


def test_structured_payload_cannot_hide_secrets_under_public_repo_fields(tmp_path: Path) -> None:
    class MalformedAPI(SyntheticAPI):
        def __call__(self, method: str, path: str, **kwargs):
            result = super().__call__(method, path, **kwargs)
            if path == f"/repos/{executor.REPOSITORY}":
                result["private"] = {"token": "SYNTHETIC_SECRET"}
            return result

    with pytest.raises(executor.PublicError):
        broker(tmp_path, MalformedAPI()).public_get(f"/repos/{executor.REPOSITORY}", "bootstrap")


def test_transport_never_enables_ambient_keylog_proxy_or_redirect(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    keylog = tmp_path / "synthetic-tls-keylog-not-created.log"
    monkeypatch.setenv("SSLKEYLOGFILE", str(keylog))
    for name in ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy"):
        monkeypatch.setenv(name, "http://synthetic-credential@proxy.invalid:8080")
    captured = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self, limit):
            return b'{}'

    class Opener:
        def open(self, request, timeout):
            captured["url"] = request.full_url
            return Response()

    def build_opener(*handlers):
        captured["handlers"] = handlers
        return Opener()

    def forbidden_context(*args, **kwargs):
        pytest.fail("create_default_context would apply ambient keylog settings")

    monkeypatch.setattr(executor.ssl, "create_default_context", forbidden_context)
    monkeypatch.setattr(executor.urllib.request, "build_opener", build_opener)
    assert executor._GitHubAPI()("GET", "/app", credential="SYNTHETIC_JWT") == {}
    handlers = captured["handlers"]
    proxy = next(handler for handler in handlers if isinstance(handler, executor.urllib.request.ProxyHandler))
    transport = next(handler for handler in handlers if isinstance(handler, executor.urllib.request.HTTPSHandler))
    assert proxy.proxies == {}
    assert transport._context.keylog_filename is None
    assert transport._context.check_hostname is True
    assert transport._context.verify_mode == executor.ssl.CERT_REQUIRED
    assert not keylog.exists()
    assert captured["url"] == "https://api.github.com/app"
    redirect = next(handler for handler in handlers if isinstance(handler, executor._NoRedirect))
    with pytest.raises(executor.PublicError):
        redirect.redirect_request(None, None, 302, "", {}, "https://unapproved.invalid/")


def synthetic_repo(tmp_path: Path) -> tuple[Path, dict[str, str]]:
    root = tmp_path / "synthetic-repository"
    source = tmp_path / "synthetic-source-repository"
    profile = tmp_path / "synthetic-git-profile"
    profile.mkdir()
    (profile / "empty.gitconfig").write_bytes(b"")
    env = executor.child_environment(None, profile)
    process = subprocess.run(["git", "init", "--initial-branch=maintain/source", str(source)],
                             env=env, capture_output=True, text=True, check=False)
    assert process.returncode == 0
    commands = (["git", "-C", str(source), "-c", "user.name=Synthetic", "-c", "user.email=synthetic@example.invalid",
                 "commit", "--allow-empty", "-m", "Synthetic offline baseline"],
                ["git", "-C", str(source), "worktree", "add", "-b", "maintain/task", str(root)])
    for command in commands:
        process = subprocess.run(command, env=env, capture_output=True, text=True, check=False)
        assert process.returncode == 0
    return root, env


def synthetic_git_paths(root: Path) -> tuple[Path, Path]:
    marker = (root / ".git").read_text(encoding="utf-8").strip()
    gitdir = Path(marker.removeprefix("gitdir: "))
    common = Path(os.path.normpath(gitdir / (gitdir / "commondir").read_text(encoding="utf-8").strip()))
    return gitdir, common


@pytest.mark.parametrize("key", ["http.extraheader", "http.https://github.com/.extraheader", "http.proxy",
                                 "http.sslverify", "remote.origin.proxy", "credential.helper",
                                 "core.hookspath", "core.sshcommand", "include.path", "core.fsmonitor",
                                 "push.gpgsign", "gpg.program", "gpg.ssh.program", "unknown.candidateexec"])
def test_real_git_unsafe_key_blocks_before_token_and_action(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, key: str,
) -> None:
    root, env = synthetic_repo(tmp_path)
    configured = subprocess.run(["git", "-C", str(root), "config", "--local", key, "SYNTHETIC_UNTRUSTED_VALUE"],
                                env=env, capture_output=True, text=True, check=False)
    assert configured.returncode == 0
    api = SyntheticAPI()
    controller = broker(tmp_path, api)
    real_run = subprocess.run
    action_calls = []

    def run(command, **kwargs):
        assert "GH_TOKEN" not in kwargs["env"]
        if command[0] == "gh":
            action_calls.append(command)
            return subprocess.CompletedProcess(command, 0, "", "")
        assert "--name-only" in command  # Reject keys before later commands parse includes.
        result = real_run(command, **kwargs)
        assert "SYNTHETIC_UNTRUSTED_VALUE" not in result.stdout
        return result

    monkeypatch.setattr(subprocess, "run", run)
    with pytest.raises(executor.PublicError) as caught:
        controller.execute("merge", {"pr": "12", "head_sha": "a" * 40}, root, "bootstrap")
    assert caught.value.code == "TOOLCHAIN_CONFIG_UNTRUSTED"
    assert api.calls == []
    assert action_calls == []


def test_real_pre_push_hook_blocks_before_token_without_reading_hook_contents(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, _ = synthetic_repo(tmp_path)
    _, common = synthetic_git_paths(root)
    hook = common / "hooks" / "pre-push"
    hook.write_text("synthetic-not-executed-hook", encoding="utf-8")
    api = SyntheticAPI()
    controller = broker(tmp_path, api)
    real_read = Path.read_bytes

    def read(path):
        assert path != hook
        return real_read(path)

    monkeypatch.setattr(Path, "read_bytes", read)
    with pytest.raises(executor.PublicError) as caught:
        controller.execute("merge", {"pr": "12", "head_sha": "a" * 40}, root, "bootstrap")
    assert caught.value.code == "TOOLCHAIN_HOOK_UNTRUSTED"
    assert api.calls == []


@pytest.mark.parametrize("active,child,base,allowed", [
    (True, "maintain/task", "feature/task-delivery-integration", True),
    (False, "maintain/task", "feature/task-delivery-integration", False),
    (True, "maintain/other", "feature/task-delivery-integration", False),
    (True, "maintain/task", "feature/task-unregistered-integration", False),
])
def test_integration_pr_requires_exact_active_plan_registry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, active: bool, child: str, base: str, allowed: bool,
) -> None:
    root, _ = synthetic_repo(tmp_path)
    plans = root / "plans"
    plans.mkdir()
    payload = {"schema_version": 1, "routes": [{"task_id": "delivery", "integration": "feature/task-delivery-integration",
                "children": ["maintain/task"], "mainline": "develop", "repo": executor.REPOSITORY, "active": active}]}
    (plans / "[PLAN]_synthetic.md").write_text("<!-- agent-first-routes\n" + json.dumps(payload) + "\n-->", encoding="utf-8")
    body = root / "public-pr-body.md"
    body.write_text("Synthetic public body", encoding="utf-8")
    api = SyntheticAPI()
    controller = broker(tmp_path, api)
    real_run = subprocess.run
    commands = []

    def run(command, **kwargs):
        if command[0] != "gh":
            assert "GH_TOKEN" not in kwargs["env"]
            return real_run(command, **kwargs)
        commands.append(command)
        return subprocess.CompletedProcess(command, 0, f"https://github.com/{executor.REPOSITORY}/pull/12", "")

    monkeypatch.setattr(subprocess, "run", run)
    args = {"head": child, "base": base, "title": "Synthetic delivery", "body_file": str(body)}
    if allowed:
        result = controller.execute("pr-create", args, root, "bootstrap")
        assert result["token_revocation"] == "CONFIRMED"
        assert commands[0][commands[0].index("--base") + 1] == base
    else:
        with pytest.raises(executor.PublicError):
            controller.execute("pr-create", args, root, "bootstrap")
        assert api.calls == []
        assert commands == []


def test_registration_revalidates_changed_parent_before_any_marker_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = vault(tmp_path)
    original = executor._local_path

    def changed(path):
        if path == store.attempt or path == store.directory:
            raise executor.PublicError("VAULT_PATH_INVALID")
        return original(path)

    monkeypatch.setattr(executor, "_local_path", changed)
    with pytest.raises(executor.PublicError):
        executor.Registration(store, api=lambda *a, **k: conversion()).begin()
    assert not store.attempt.exists()


@pytest.mark.skipif(os.name != "nt", reason="Windows junction metadata rejection")
@pytest.mark.parametrize("action", ["begin", "save"])
def test_actual_windows_junction_swap_is_rejected_before_writing(tmp_path: Path, action: str) -> None:
    parent = tmp_path / "original-parent"
    target = tmp_path / "synthetic-junction-target"
    parent.mkdir()
    target.mkdir()
    store = executor.SecretVault(parent / executor.APP_SLUG, repo_root=tmp_path / "repo", cipher=SyntheticCipher())
    parent.rename(tmp_path / "original-parent-backup")
    made = subprocess.run(["cmd", "/c", "mklink", "/J", str(parent), str(target)],
                          capture_output=True, text=True, check=False)
    if made.returncode:
        pytest.skip("Normal Windows junction creation unavailable")
    try:
        with pytest.raises(executor.PublicError):
            if action == "begin":
                executor.Registration(store, api=lambda *a, **k: conversion()).begin()
            else:
                store.save(conversion())
        assert list(target.iterdir()) == []
    finally:
        os.rmdir(parent)  # This exact synthetic junction, never its target contents.


@pytest.mark.skipif(os.name != "nt", reason="Windows metadata handle sharing guarantees")
def test_actual_windows_parent_handle_prevents_rename_during_write_guard(tmp_path: Path) -> None:
    parent = tmp_path / "synthetic-parent-held-during-write"
    path = parent / executor.APP_SLUG / "synthetic-output.bin"
    with executor._path_guard(path, create_parents=True):
        with pytest.raises(OSError):
            parent.rename(tmp_path / "synthetic-swapped-parent")
        path.write_bytes(b"synthetic public bytes")
    assert path.read_bytes() == b"synthetic public bytes"


@pytest.mark.skipif(os.name != "nt", reason="Windows config metadata handle sharing guarantees")
def test_actual_windows_config_lock_prevents_replacement_before_token(tmp_path: Path) -> None:
    root, _ = synthetic_repo(tmp_path)
    _, common = synthetic_git_paths(root)
    config = common / "config"
    with executor._trusted_toolchain(root):
        with pytest.raises(OSError):
            config.rename(config.with_name("synthetic-config-replaced"))
        with pytest.raises(OSError):
            config.open("a", encoding="utf-8")


def test_isolated_direct_script_loads_fixed_route_library_without_user_pythonpath(tmp_path: Path) -> None:
    root, env = synthetic_repo(tmp_path)
    plans = root / "plans"
    plans.mkdir()
    payload = {"schema_version": 1, "routes": [{"task_id": "delivery", "integration": "feature/task-delivery-integration",
                "children": ["maintain/task"], "mainline": "develop", "repo": executor.REPOSITORY, "active": True}]}
    (plans / "[PLAN]_synthetic.md").write_text("<!-- agent-first-routes\n" + json.dumps(payload) + "\n-->", encoding="utf-8")
    body = root / "public-pr-body.md"
    body.write_text("Synthetic public body", encoding="utf-8")
    (tmp_path / executor.APP_SLUG).mkdir()
    process = subprocess.run([sys.executable, "-I", str(Path(executor.__file__)), "pr-create", "--root", str(root),
        "--vault-dir", str(tmp_path / executor.APP_SLUG), "--head", "maintain/task",
        "--base", "feature/task-delivery-integration", "--title", "Synthetic PR", "--body-file", str(body)],
        env=env, capture_output=True, text=True, check=False, timeout=20)
    assert process.returncode == 2
    # The exact active route was accepted, then the missing new-App vault blocks
    # before any network or credential creation can occur.
    assert json.loads(process.stdout)["error"] == "NEW_APP_VAULT_INVALID"
    assert process.stderr == ""


def test_original_absent_commondir_context_is_never_accepted(tmp_path: Path) -> None:
    root, _ = synthetic_repo(tmp_path)
    gitdir, _ = synthetic_git_paths(root)
    (gitdir / "commondir").rename(gitdir / "synthetic-missing-commondir")
    with pytest.raises(executor.PublicError) as caught:
        with executor._trusted_toolchain(root):
            pytest.fail("An unbound common configuration source must never be accepted")
    assert caught.value.code == "TOOLCHAIN_LINKED_WORKTREE_REQUIRED"


@pytest.mark.skipif(os.name != "nt", reason="Windows config/marker handle guarantees")
def test_real_git_sources_stay_fixed_after_untrusted_sources_are_added(tmp_path: Path) -> None:
    root, _ = synthetic_repo(tmp_path)
    gitdir, common = synthetic_git_paths(root)
    with executor._trusted_toolchain(root) as binding:
        assert isinstance(binding, dict)
        # A new worktree-local config must not become the effective config.
        (gitdir / "config").write_text("[http]\nextraHeader = SYNTHETIC_UNCHECKED_HEADER\n", encoding="utf-8")
        with pytest.raises(OSError):
            (gitdir / "commondir").write_text("SYNTHETIC_ALTERNATE_SOURCE", encoding="utf-8")
        profile = tmp_path / "bound-child-profile"
        profile.mkdir()
        (profile / "empty.gitconfig").write_bytes(b"")
        env = executor.child_environment(None, profile, toolchain=binding)
        process = subprocess.run(["git", "-C", str(root), "config", "--no-includes", "--name-only", "--list"],
                                 env=env, capture_output=True, text=True, check=False)
        assert process.returncode == 0
        assert "http.extraheader" not in process.stdout.lower()
        assert env["GIT_DIR"] == str(gitdir)
        assert env["GIT_COMMON_DIR"] == str(common)
        assert env["GIT_WORK_TREE"] == str(root)


def test_new_repository_hook_never_executes_in_fixed_child_context(tmp_path: Path) -> None:
    root, _ = synthetic_repo(tmp_path)
    _, common = synthetic_git_paths(root)
    marker = tmp_path / "synthetic-hook-must-not-execute.txt"
    with executor._trusted_toolchain(root) as binding:
        hook = common / "hooks" / "pre-push"
        hook.write_text(f'#!/bin/sh\nprintf synthetic > "{marker.as_posix()}"\n', encoding="utf-8")
        hook.chmod(0o700)
        profile = tmp_path / "bound-hook-child-profile"
        profile.mkdir()
        (profile / "empty.gitconfig").write_bytes(b"")
        env = executor.child_environment(None, profile, toolchain=binding)
        # Real Git's hook dispatcher, entirely local and without a token/API.
        process = subprocess.run(["git", "-C", str(root), "hook", "run", "--ignore-missing", "pre-push"],
                                 env=env, capture_output=True, text=True, check=False)
        assert process.returncode == 0
        assert not marker.exists()
        actual_path = subprocess.run(["git", "-C", str(root), "config", "--get", "core.hooksPath"],
                                     env=env, capture_output=True, text=True, check=False)
        assert actual_path.returncode == 0
        assert Path(actual_path.stdout.strip()).is_relative_to(Path(binding["hooks"]).parent)
        assert not Path(actual_path.stdout.strip()).is_relative_to(root)
    # Isolation cannot be used to clear the next real first-inspection refusal.
    with pytest.raises(executor.PublicError, match="TOOLCHAIN_HOOK_UNTRUSTED"):
        with executor._trusted_toolchain(root):
            pytest.fail("Existing active hook must still block")


@pytest.mark.parametrize("suffix", ["", ".git"])
def test_fixed_publisher_accepts_exact_https_origin_with_or_without_git_suffix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, suffix: str,
) -> None:
    controller = broker(tmp_path, SyntheticAPI())
    allow_mocked_toolchain(monkeypatch)
    commands = []

    def run(command, **kwargs):
        commands.append(command)
        if command[-2:] == ["rev-parse", "HEAD"]:
            output = "a" * 40
        elif command[-2:] == ["branch", "--show-current"]:
            output = "maintain/task"
        elif "get-url" in command:
            output = f"https://github.com/{executor.REPOSITORY}{suffix}"
        else:
            output = ""
        return subprocess.CompletedProcess(command, 0, output, "")

    monkeypatch.setattr(subprocess, "run", run)
    result = controller.execute("push", {"branch": "maintain/task", "head_sha": "a" * 40}, tmp_path, "bootstrap")
    assert result["token_revocation"] == "CONFIRMED"
    assert sum("push" in command for command in commands) == 1


@pytest.mark.parametrize("route", ["https://github.com/foreign/repo", "https://github.com/MJ-AgentLab/mj-agent?secret=x",
                                    "https://user@github.com/MJ-AgentLab/mj-agent", "https://github.com/MJ-AgentLab/mj-agent#x",
                                    "https://github.com/MJ-AgentLab/mj-agent\nhttps://github.com/foreign/repo"])
def test_fixed_origin_rejects_credentials_foreign_or_multiple_routes(route: str) -> None:
    assert not executor._origin_matches(route)


def test_real_git_signing_program_is_rejected_before_any_token_or_execution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, env = synthetic_repo(tmp_path)
    marker = tmp_path / "synthetic-signing-must-not-execute.txt"
    program = tmp_path / ("synthetic-signing.cmd" if os.name == "nt" else "synthetic-signing.sh")
    content = f'@echo off\necho synthetic > "{marker}"\n' if os.name == "nt" else f'#!/bin/sh\necho synthetic > "{marker.as_posix()}"\n'
    program.write_text(content, encoding="utf-8")
    program.chmod(0o700)
    for key, value in (("push.gpgSign", "true"), ("gpg.program", str(program))):
        process = subprocess.run(["git", "-C", str(root), "config", "--local", key, value],
                                 env=env, capture_output=True, text=True, check=False)
        assert process.returncode == 0
    api = SyntheticAPI()
    controller = broker(tmp_path, api)
    real_run = subprocess.run
    commands = []

    def run(command, **kwargs):
        commands.append(command)
        assert "GH_TOKEN" not in kwargs["env"]
        return real_run(command, **kwargs)

    monkeypatch.setattr(subprocess, "run", run)
    with pytest.raises(executor.PublicError, match="TOOLCHAIN_CONFIG_UNTRUSTED"):
        controller.execute("push", {"branch": "maintain/task", "head_sha": "a" * 40}, root, "bootstrap")
    assert api.calls == []
    assert not marker.exists()
    assert all("--name-only" in command for command in commands)


@pytest.mark.parametrize("suffix", ["", ".git"])
def test_real_git_authentication_matches_only_the_exact_normal_https_route(tmp_path: Path, suffix: str) -> None:
    root, _ = synthetic_repo(tmp_path)
    with executor._trusted_toolchain(root) as binding:
        profile = tmp_path / "synthetic-urlmatch-profile"
        profile.mkdir()
        (profile / "empty.gitconfig").write_bytes(b"")
        token = "SYNTHETIC_NEW_TOKEN_NO_SERVICE"
        env = executor.child_environment(token, profile, toolchain=binding)
        url = f"https://github.com/{executor.REPOSITORY}{suffix}"
        process = subprocess.run(["git", "-C", str(root), "config", "--get-urlmatch", "http.extraheader", url],
                                 env=env, capture_output=True, text=True, check=False)
        expected = "Authorization: Basic " + base64.b64encode(f"x-access-token:{token}".encode()).decode()
        assert process.returncode == 0
        assert process.stdout.splitlines() == [expected]  # No duplicate/old header.
        foreign = subprocess.run(["git", "-C", str(root), "config", "--get-urlmatch", "http.extraheader",
                                  "https://github.com/foreign/repository.git"],
                                 env=env, capture_output=True, text=True, check=False)
        assert foreign.returncode == 1
        assert foreign.stdout == ""


@pytest.mark.parametrize("stop_pending", [False, True])
def test_callback_redirects_before_blocked_conversion_and_never_repeats(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], stop_pending: bool,
) -> None:
    started, release = threading.Event(), threading.Event()
    calls = []

    def api(*args, **kwargs):
        calls.append(args)
        started.set()
        assert release.wait(timeout=5)
        return conversion()

    store = vault(tmp_path)
    server, registration = executor.make_server(store, api=api)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    connection = HTTPConnection("127.0.0.1", server.server_port, timeout=0.5)
    try:
        connection.request("GET", "/register")
        response = connection.getresponse()
        cookie = response.getheader("Set-Cookie").split(";", 1)[0]
        response.read()
        query = urllib.parse.urlencode({"state": registration._state, "code": "SYNTHETIC_ASYNC_CODE"})
        connection.request("GET", f"/manifest/callback?{query}", headers={"Cookie": cookie})
        response = connection.getresponse()  # Must not await the blocked API.
        assert response.status == 303
        assert response.getheader("Location") == "/result"
        assert response.read() == b""
        assert started.wait(timeout=1)
        connection.request("GET", "/result")
        response = connection.getresponse()
        public = json.loads(response.read())
        assert public["status"] == "WAITING"
        assert "SYNTHETIC" not in json.dumps(public)
        connection.request("GET", f"/manifest/callback?{query}", headers={"Cookie": cookie})
        response = connection.getresponse()
        assert response.status == 303
        response.read()
        assert len(calls) == 1
        if stop_pending:
            server.shutdown()
            server.server_close()
            assert registration.result["status"] == "UNKNOWN"
            assert registration.result["retry"] == "FORBIDDEN_PENDING_RECONCILIATION"
        release.set()
        registration._worker.join(timeout=5)
        assert len(calls) == 1
        assert registration.result["status"] == ("UNKNOWN" if stop_pending else "REGISTERED")
        assert store.path.exists() is not stop_pending
        assert store.attempt.exists()
        assert "SYNTHETIC" not in str(capsys.readouterr())
    finally:
        release.set()
        connection.close()
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.mark.parametrize("key", ["alias.pushall", "branch.develop.vscode-merge-base", "branch.main.vscode-merge-base",
                                 "branch.maintain/synthetic-compatibility.vscode-merge-base"])
def test_only_reviewed_inert_compatibility_keys_are_accepted(key: str) -> None:
    assert executor._git_config_untrusted(key) is False


@pytest.mark.parametrize("key", ["alias.other", "alias.pushallx", "alias.pushall.command", "Alias.pushall", "alias.PushAll",
    "branch..vscode-merge-base", "branch.foo/../bar.vscode-merge-base", "branch.foo//bar.vscode-merge-base",
    "branch.foo.lock.vscode-merge-base", "branch.foo/.hidden.vscode-merge-base", "branch.foo/.vscode-merge-base",
    "branch.foo.vscode-merge-basex", "branch.foo.vscode-merge-base.command", "branch.foo.vscode-merge-base\n",
    "gpg.program", "gpg.ssh.program", "push.gpgsign", "http.extraheader", "credential.helper", "core.hookspath",
    "include.path", "core.fsmonitor", "unknown.candidateexec"])
def test_compatibility_never_accepts_neighbor_alias_unknown_or_executable_keys(key: str) -> None:
    assert executor._git_config_untrusted(key) is True


def test_actual_git_fixed_commands_never_select_allowed_synthetic_alias(tmp_path: Path) -> None:
    root, env = synthetic_repo(tmp_path)
    marker = tmp_path / "synthetic-inert-alias-must-not-execute.txt"
    configured = subprocess.run(["git", "-C", str(root), "config", "--local", "alias.pushall",
                                 "!printf synthetic > '" + marker.as_posix() + "'"],
                                env=env, capture_output=True, text=True, check=False)
    assert configured.returncode == 0
    configured = subprocess.run(["git", "-C", str(root), "config", "--local",
                                 "branch.maintain/task.vscode-merge-base", "SYNTHETIC_IDE_METADATA"],
                                env=env, capture_output=True, text=True, check=False)
    assert configured.returncode == 0
    with executor._trusted_toolchain(root) as binding:
        profile = tmp_path / "synthetic-inert-child-profile"
        profile.mkdir()
        (profile / "empty.gitconfig").write_bytes(b"")
        child = executor.child_environment(None, profile, toolchain=binding)
        for arguments in (["config", "--no-includes", "--name-only", "--list"], ["rev-parse", "HEAD"],
                          ["branch", "--show-current"]):
            result = subprocess.run(["git", "-C", str(root), *arguments], env=child,
                                    capture_output=True, text=True, check=False)
            assert result.returncode == 0
            assert not marker.exists()
    # Positive control selects only the self-created harmless fixture alias.
    result = subprocess.run(["git", "-C", str(root), "pushall"], env=env,
                            capture_output=True, text=True, check=False)
    assert result.returncode == 0
    assert marker.read_text(encoding="utf-8") == "synthetic"
    with pytest.raises(executor.PublicError, match="ACTION_FORBIDDEN"):
        executor.Controller(None, api=lambda *a, **k: pytest.fail("API forbidden")).execute(
            "pushall", {}, root, "daily")


def protected_ruleset() -> dict:
    return {"id": 123, "name": "Protect development", "target": "branch", "enforcement": "active",
            "conditions": {"ref_name": {"include": ["refs/heads/develop"], "exclude": []}},
            "rules": [{"type": "pull_request", "parameters": {
                "required_approving_review_count": 1, "require_last_push_approval": True,
                "required_reviewers": [{"reviewer_id": 7, "reviewer_type": "Team"}],
                "dismissal_restriction": {"teams": [11]},
                "require_extra_approval_for_unattributed_changes": True,
                "unknown_private_parameter": {"token": "SYNTHETIC_PRIVATE_EXTRA"}}}],
            "bypass_actors": [], "current_user_can_bypass": False,
            "webhook_secret": "SYNTHETIC_PRIVATE_EXTRA"}


def test_protection_digest_binds_all_raw_rules_without_disclosing_unknown_parameters() -> None:
    row = protected_ruleset()
    result = executor._public_ruleset(row)
    subset = {key: row[key] for key in ("id", "name", "target", "enforcement", "conditions", "rules")}
    expected = hashlib.sha256(json.dumps(subset, sort_keys=True, separators=(",", ":"),
                                        ensure_ascii=True, allow_nan=False).encode("utf-8")).hexdigest()
    assert result["protection_sha256"] == expected
    assert "SYNTHETIC_PRIVATE_EXTRA" not in json.dumps(result)
    assert "required_reviewers" not in result["rules"][0]["parameters"]
    changed = copy.deepcopy(row)
    changed["rules"][0]["parameters"]["required_reviewers"][0]["reviewer_id"] = 8
    assert executor._public_ruleset(changed)["protection_sha256"] != result["protection_sha256"]


def test_protection_digest_ignores_actors_extra_fields_and_dict_order_but_distinguishes_missing() -> None:
    row = protected_ruleset()
    original = executor._public_ruleset(row)["protection_sha256"]
    changed = dict(reversed(list(row.items())))
    changed["bypass_actors"] = [{"actor_id": 999, "actor_type": "Integration", "bypass_mode": "always"}]
    changed["current_user_can_bypass"] = "always"
    changed["unknown_top_level"] = "SYNTHETIC_PRIVATE_EXTRA"
    assert executor._public_ruleset(changed)["protection_sha256"] == original
    missing = copy.deepcopy(row)
    del missing["conditions"]
    null = copy.deepcopy(row)
    null["conditions"] = None
    assert executor._public_ruleset(missing)["protection_sha256"] != executor._public_ruleset(null)["protection_sha256"]


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf"), (1, 2), {1: "bad"}, {"bad-set"}])
def test_noncanonical_protected_parameters_are_rejected_without_raw_payload(bad) -> None:
    row = protected_ruleset()
    row["rules"][0]["parameters"]["unknown_private_parameter"] = bad
    with pytest.raises(executor.PublicError) as caught:
        executor._public_ruleset(row)
    assert "SYNTHETIC_PRIVATE_EXTRA" not in str(caught.value)


def test_protection_digest_matches_independent_ascii_escaped_canonical_literal() -> None:
    row = {"id": 3, "name": "保护", "target": "branch", "enforcement": "active", "conditions": {},
           "rules": [{"type": "pull_request", "parameters": {"unknown": "审阅"}}]}
    canonical = (r'{"conditions":{},"enforcement":"active","id":3,"name":"\u4fdd\u62a4",'
                 r'"rules":[{"parameters":{"unknown":"\u5ba1\u9605"},"type":"pull_request"}],"target":"branch"}')
    assert executor._public_ruleset(row)["protection_sha256"] == hashlib.sha256(canonical.encode("ascii")).hexdigest()


def test_noncanonical_api_rule_is_unknown_and_revokes_without_raw_fields(tmp_path: Path) -> None:
    class RulesAPI(SyntheticAPI):
        def __call__(self, method: str, path: str, **kwargs):
            if path == f"/repos/{executor.REPOSITORY}/rulesets/123":
                row = protected_ruleset()
                row["rules"][0]["parameters"]["unknown_private_parameter"]["nonfinite"] = float("nan")
                return row
            return super().__call__(method, path, **kwargs)

    api = RulesAPI()
    with pytest.raises(executor.PublicError) as caught:
        broker(tmp_path, api).public_get(f"/repos/{executor.REPOSITORY}/rulesets/123", "bootstrap")
    assert caught.value.code == "REMOTE_RESPONSE_INVALID"
    assert caught.value.details["state"] == "UNKNOWN"
    assert caught.value.details["token_revocation"] == "CONFIRMED"
    assert "SYNTHETIC" not in json.dumps(caught.value.details)
    assert api.calls[-1][:2] == ("DELETE", "/installation/token")
