"""Fixed-repository GitHub App broker; only public data crosses its CLI boundary.

Only newly converted manifest credentials enter this user-DPAPI store. No existing
application/MCP/personal credential carrier, arbitrary API or shell is supported.
"""

from __future__ import annotations

import argparse
import base64
import ctypes
import hashlib
import hmac
import json
import os
import re
import secrets
import ssl
import stat
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from contextlib import ExitStack, contextmanager
from datetime import UTC, datetime
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

OWNER = "MJ-AgentLab"
REPO_NAME = "mj-agent"
REPOSITORY = f"{OWNER}/{REPO_NAME}"
APP_SLUG = "mj-agent-delivery-executor"
DAILY_PERMISSIONS = {"metadata": "read", "contents": "write", "pull_requests": "write"}
BOOTSTRAP_PERMISSIONS = {**DAILY_PERMISSIONS, "workflows": "write"}
_ROOT = Path(__file__).absolute().parents[2]
_MAGIC = b"MJ-AGENT-NEW-APP-DPAPI-V1\n"
_ENTROPY = b"mj-agent-delivery-executor/new-app-only/v1"
_COOKIE = "mj_delivery_registration"
_SAFE_PARENT = ("PATH", "PATHEXT", "SYSTEMROOT", "WINDIR", "COMSPEC", "LANG", "LC_ALL")


class PublicError(Exception):
    """Fixed codes only; never attach private payloads or raw upstream errors."""

    def __init__(self, code: str, *, details: dict | None = None) -> None:
        super().__init__(code)
        self.code = code
        self.details = details or {}


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise PublicError(code)


def _local_path(path: Path) -> Path:
    _require(path.is_absolute(), "VAULT_PATH_INVALID")
    _require(not path.drive or bool(re.fullmatch(r"[A-Za-z]:", path.drive)), "VAULT_PATH_INVALID")
    for component in path.parts:
        if component == path.anchor:
            continue
        _require(not component.endswith((" ", ".")) and not any(
            value in '<>:"|?*\\' or ord(value) < 32 for value in component), "VAULT_PATH_INVALID")
        _require(not component.lower().startswith((".env", "secrets")), "VAULT_PATH_INVALID")
        _require(not re.fullmatch(r"(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?",
                                 component, re.IGNORECASE), "VAULT_PATH_INVALID")
    for ancestor in [path, *path.parents]:
        try:
            info = ancestor.lstat()
        except FileNotFoundError:
            continue
        _require(not stat.S_ISLNK(info.st_mode)
                 and not getattr(info, "st_file_attributes", 0) & 0x400, "VAULT_PATH_INVALID")
    return path.resolve()


def _outside_path(path: Path, repo_root: Path) -> Path:
    resolved = _local_path(path)
    _require(not resolved.is_relative_to(repo_root.resolve()), "VAULT_MUST_BE_EXTERNAL")
    return resolved


@contextmanager
def _metadata_lock(path: Path):
    """Windows metadata handle denies write/delete sharing, including reparse edits.

    This changes neither ACLs nor host approval. Unsupported/open-denied states
    fail closed. Non-Windows synthetic tests get metadata checks; production
    credential persistence still requires WindowsDPAPI.
    """
    _local_path(path)
    if os.name != "nt":
        yield
        _local_path(path)
        return
    from ctypes import wintypes

    class AttributeTag(ctypes.Structure):
        _fields_ = [("attributes", wintypes.DWORD), ("tag", wintypes.DWORD)]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                  ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.GetFileInformationByHandleEx.argtypes = [wintypes.HANDLE, ctypes.c_int,
                                                   ctypes.c_void_p, wintypes.DWORD]
    kernel.GetFileInformationByHandleEx.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    # FILE_READ_ATTRIBUTES alone is exempt from Windows data sharing checks.
    # Add FILE_READ_DATA/LIST_DIRECTORY without ever reading file contents here
    # so competing write/delete handles really are rejected.
    handle = kernel.CreateFileW(str(path), 0x81, 1, None, 3, 0x02000000 | 0x00200000, None)
    _require(handle not in (None, ctypes.c_void_p(-1).value), "PATH_LOCK_UNAVAILABLE")
    try:
        tag = AttributeTag()
        _require(bool(kernel.GetFileInformationByHandleEx(handle, 9, ctypes.byref(tag),
                                                         ctypes.sizeof(tag)))
                 and not tag.attributes & 0x400, "VAULT_PATH_INVALID")
        yield
    finally:
        kernel.CloseHandle(handle)


@contextmanager
def _path_guard(path: Path, *, create_parents: bool = False):
    """Recheck and lock every parent before creating the next child or writing."""
    _local_path(path)
    with ExitStack() as locks:
        for parent in reversed(path.parents):
            if not parent.exists():
                _require(create_parents, "PATH_PARENT_UNAVAILABLE")
                parent.mkdir()  # Its existing parent is already handle-locked.
            locks.enter_context(_metadata_lock(parent))
        if path.exists():
            locks.enter_context(_metadata_lock(path))
        _local_path(path)
        yield


class WindowsDPAPI:
    """Current-user DPAPI, UI forbidden; no plaintext output or machine scope."""

    def _transform(self, payload: bytes, protect: bool) -> bytes:
        _require(os.name == "nt", "WINDOWS_DPAPI_REQUIRED")
        from ctypes import wintypes

        class Blob(ctypes.Structure):
            _fields_ = [("size", wintypes.DWORD), ("data", ctypes.POINTER(ctypes.c_ubyte))]

        incoming = ctypes.create_string_buffer(payload)
        entropy = ctypes.create_string_buffer(_ENTROPY)
        source = Blob(len(payload), ctypes.cast(incoming, ctypes.POINTER(ctypes.c_ubyte)))
        extra = Blob(len(_ENTROPY), ctypes.cast(entropy, ctypes.POINTER(ctypes.c_ubyte)))
        target = Blob()
        crypt = ctypes.WinDLL("crypt32", use_last_error=True)
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        function = crypt.CryptProtectData if protect else crypt.CryptUnprotectData
        function.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.POINTER(Blob),
                             ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
        function.restype = wintypes.BOOL
        kernel.LocalFree.argtypes = [ctypes.c_void_p]
        kernel.LocalFree.restype = ctypes.c_void_p
        try:
            _require(bool(function(ctypes.byref(source), None, ctypes.byref(extra), None,
                                   None, 1, ctypes.byref(target))), "DPAPI_FAILED")
            return ctypes.string_at(target.data, target.size)
        finally:
            ctypes.memset(incoming, 0, len(incoming))
            if target.data:
                ctypes.memset(target.data, 0, target.size)
                kernel.LocalFree(target.data)

    def protect(self, payload: bytes) -> bytes:
        return self._transform(payload, True)

    def unprotect(self, payload: bytes) -> bytes:
        return self._transform(payload, False)


def _app_public(payload: Any, permissions: dict[str, str]) -> dict:
    _require(isinstance(payload, dict) and type(payload.get("id")) is int and payload["id"] > 0,
             "APP_IDENTITY_INVALID")
    _require(payload.get("slug") == APP_SLUG and payload.get("name") == APP_SLUG
             and isinstance(payload.get("owner"), dict) and payload["owner"].get("login") == OWNER,
             "APP_IDENTITY_INVALID")
    _require(payload.get("permissions") == permissions and payload.get("events") == [], "GRANT_MISMATCH")
    return {"id": payload["id"], "slug": APP_SLUG, "owner": OWNER, "permissions": permissions}


class SecretVault:
    """One fixed new-App blob, not a general credential store or decrypt API."""

    def __init__(self, directory: Path, *, repo_root: Path = _ROOT, cipher: Any = None) -> None:
        self._repo_root = repo_root
        self.directory = _outside_path(directory, repo_root)
        _require(self.directory.name == APP_SLUG, "VAULT_NAMESPACE_INVALID")
        self.path = self.directory / f"{APP_SLUG}.dpapi"
        self.attempt = self.directory / "registration-attempt.json"
        self._cipher = cipher or WindowsDPAPI()

    def save(self, payload: dict) -> None:
        public = _app_public(payload, BOOTSTRAP_PERMISSIONS)
        _require(isinstance(payload.get("pem"), str) and 0 < len(payload["pem"]) <= 65536,
                 "NEW_APP_KEY_INVALID")
        record = {"version": 1, "origin": "new-app-manifest", "repository": REPOSITORY,
                  "app_id": public["id"], "slug": APP_SLUG, "owner": OWNER, "pem": payload["pem"]}
        try:
            with _path_guard(self.path, create_parents=True):
                _outside_path(self.path, self._repo_root)
                _require(not self.path.exists(), "REGISTRATION_ALREADY_ATTEMPTED")
                protected = self._cipher.protect(json.dumps(record).encode("utf-8"))
                with self.path.open("xb") as stream:
                    stream.write(_MAGIC + protected)
        except OSError:
            raise PublicError("VAULT_WRITE_UNKNOWN") from None

    def _record(self) -> dict:
        try:
            with _path_guard(self.path):
                _outside_path(self.path, self._repo_root)
                _require(self.path.is_file() and self.path.stat().st_size <= 131072, "NEW_APP_VAULT_INVALID")
                encoded = self.path.read_bytes()
                _require(encoded.startswith(_MAGIC), "NEW_APP_VAULT_INVALID")
                payload = json.loads(self._cipher.unprotect(encoded[len(_MAGIC):]))
        except PublicError:
            raise
        except Exception:
            raise PublicError("NEW_APP_VAULT_UNAVAILABLE") from None
        _require(isinstance(payload, dict) and set(payload) == {
            "version", "origin", "repository", "app_id", "slug", "owner", "pem"}, "NEW_APP_VAULT_INVALID")
        _require(payload["version"] == 1 and payload["origin"] == "new-app-manifest"
                 and payload["repository"] == REPOSITORY and payload["slug"] == APP_SLUG
                 and payload["owner"] == OWNER and type(payload["app_id"]) is int
                 and payload["app_id"] > 0 and isinstance(payload["pem"], str), "NEW_APP_VAULT_INVALID")
        return payload


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args: Any, **kwargs: Any) -> None:
        raise PublicError("REMOTE_REDIRECT_FORBIDDEN")


def _api_allowed(method: str, path: str) -> bool:
    repo = re.escape(REPOSITORY)
    if method == "GET":
        return path in {"/app", "/app/installations?per_page=100", "/installation/repositories",
                        f"/repos/{REPOSITORY}", f"/repos/{REPOSITORY}/installation",
                        f"/repos/{REPOSITORY}/rulesets"} or bool(re.fullmatch(
            rf"/repos/{repo}/(?:rulesets|pulls)/[1-9][0-9]*", path))
    if method == "POST":
        return bool(re.fullmatch(r"/app-manifests/[A-Za-z0-9_-]{1,256}/conversions", path)
                    or re.fullmatch(r"/app/installations/[1-9][0-9]*/access_tokens", path))
    return method == "DELETE" and path == "/installation/token"


class _GitHubAPI:
    def __call__(self, method: str, path: str, *, credential: str | None = None,
                 body: dict | None = None) -> Any:
        _require(_api_allowed(method, path), "ENDPOINT_FORBIDDEN")
        try:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            context.load_default_certs()
            context.keylog_filename = None
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect(),
                                                 urllib.request.HTTPSHandler(context=context, debuglevel=0))
            headers = {"Accept": "application/vnd.github+json", "User-Agent": APP_SLUG,
                       "X-GitHub-Api-Version": "2026-03-10"}
            if credential is not None:
                headers["Authorization"] = f"Bearer {credential}"
            data = None if body is None else json.dumps(body).encode("utf-8")
            if data is not None:
                headers["Content-Type"] = "application/json"
            request = urllib.request.Request(f"https://api.github.com{path}", data=data,
                                             headers=headers, method=method)
            with opener.open(request, timeout=20) as response:
                raw = response.read(1048577)
                _require(len(raw) <= 1048576, "REMOTE_RESPONSE_INVALID")
                return {} if not raw else json.loads(raw)
        except PublicError:
            raise
        except Exception:
            raise PublicError("REMOTE_REQUEST_FAILED") from None


def _private_jwt(record: dict) -> str:
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding, rsa

        key = serialization.load_pem_private_key(record["pem"].encode("utf-8"), password=None)
        _require(isinstance(key, rsa.RSAPrivateKey) and key.key_size >= 2048, "NEW_APP_KEY_INVALID")
        now = int(time.time())
        def encode(value: bytes) -> bytes:
            return base64.urlsafe_b64encode(value).rstrip(b"=")
        head = encode(b'{"alg":"RS256","typ":"JWT"}')
        body = encode(json.dumps({"iat": now - 60, "exp": now + 540,
                                  "iss": str(record["app_id"])}).encode("utf-8"))
        message = head + b"." + body
        signature = key.sign(message, padding.PKCS1v15(), hashes.SHA256())
        return (message + b"." + encode(signature)).decode("ascii")
    except PublicError:
        raise
    except Exception:
        raise PublicError("SIGNING_UNAVAILABLE") from None


class Registration:
    def __init__(self, vault: SecretVault, *, api: Any = None, clock: Any = time.monotonic) -> None:
        self.vault = vault
        self._api = api or _GitHubAPI()
        self._clock = clock
        self._lock = threading.Lock()
        self._state = self._nonce = None
        self._started = 0.0
        self._stopped = False
        self._worker: threading.Thread | None = None
        self.result: dict = {"status": "NOT_STARTED"}

    def begin(self) -> tuple[str, str]:
        with self._lock:
            _require(not self._stopped, "REGISTRATION_ALREADY_STOPPED")
            with _path_guard(self.vault.attempt, create_parents=True):
                _outside_path(self.vault.attempt, self.vault._repo_root)
                _require(self._state is None and not self.vault.path.exists()
                         and not self.vault.attempt.exists(), "REGISTRATION_ALREADY_ATTEMPTED")
                with self.vault.attempt.open("x", encoding="utf-8") as stream:
                    json.dump({"repository": REPOSITORY, "app_slug": APP_SLUG,
                               "started_at": datetime.now(UTC).isoformat(), "status": "PENDING"}, stream)
            self._state, self._nonce = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
            self._started = self._clock()
            self.result = {"status": "PENDING"}
            return self._state, self._nonce

    def _consume(self, code: str, state: str, nonce: str) -> None:
        with self._lock:
            _require(not self._stopped and self._state is not None and isinstance(state, str) and isinstance(nonce, str)
                     and hmac.compare_digest(state, self._state) and hmac.compare_digest(nonce, self._nonce)
                     and self._clock() - self._started <= 3600, "REGISTRATION_STATE_INVALID")
            _require(bool(re.fullmatch(r"[A-Za-z0-9_-]{1,256}", code)), "REGISTRATION_CODE_INVALID")
            self._state = self._nonce = None
            self.result = {"status": "WAITING", "repository": REPOSITORY, "app_slug": APP_SLUG}

    def _convert(self, code: str) -> dict:
        try:
            with self._lock:
                _require(not self._stopped, "CONVERSION_INTERRUPTED")
            payload = self._api("POST", f"/app-manifests/{code}/conversions")
            public = _app_public(payload, BOOTSTRAP_PERMISSIONS)
            with self._lock:
                _require(not self._stopped, "CONVERSION_INTERRUPTED")
                self.vault.save(payload)
                self.result = {"status": "REGISTERED", "app_id": public["id"], "app_slug": APP_SLUG,
                               "repository": REPOSITORY}
                return self.result.copy()
        except Exception:
            with self._lock:
                self.result = self._unknown_result()
                result = self.result.copy()
            raise PublicError(result["error"], details=result) from None

    def _unknown_result(self) -> dict:
        return {"status": "UNKNOWN", "error": "CONVERSION_INTERRUPTED" if self._stopped else "CONVERSION_STORE_UNCERTAIN",
                "side_effects": "APP_MAY_HAVE_BEEN_CREATED", "retry": "FORBIDDEN_PENDING_RECONCILIATION"}

    def complete(self, code: str, state: str, nonce: str) -> dict:
        """Synchronous internal adapter; HTTP callbacks always use dispatch."""
        self._consume(code, state, nonce)
        return self._convert(code)

    def dispatch(self, code: str, state: str, nonce: str) -> None:
        """Consume locally once; conversion never delays the safe 303 response."""
        self._consume(code, state, nonce)

        def convert_once() -> None:
            try:
                self._convert(code)
            except PublicError:
                return  # Public UNKNOWN already stored; never a thread traceback.

        self._worker = threading.Thread(target=convert_once, daemon=True, name="new-app-manifest-conversion")
        try:
            self._worker.start()
        except Exception:
            with self._lock:
                self.result = self._unknown_result()
            raise PublicError("CONVERSION_START_UNKNOWN") from None

    def public_result(self) -> dict:
        with self._lock:
            return self.result.copy()

    def close(self) -> None:
        with self._lock:
            self._stopped = True
            self._state = self._nonce = None
            if self.result.get("status") in {"PENDING", "WAITING"}:
                self.result = self._unknown_result()
        # No join/retry: upstream may have created an App before interruption.
        # The durable attempt marker keeps any restart from repeating the flow.


def _installation_public(row: Any, app_id: int, permissions: dict) -> dict:
    _require(isinstance(row, dict) and type(row.get("id")) is int and row["id"] > 0
             and row.get("app_id") == app_id and isinstance(row.get("account"), dict)
             and row["account"].get("login") == OWNER and row.get("repository_selection") == "selected",
             "INSTALLATION_SCOPE_INVALID")
    _require(row.get("permissions") == permissions, "GRANT_MISMATCH")
    _require("suspended_at" in row and row["suspended_at"] is None, "INSTALLATION_SUSPENDED_OR_UNKNOWN")
    return {"id": row["id"], "app_id": app_id, "account": OWNER,
            "repository_selection": "selected", "permissions": permissions, "suspended_at": None}


def _public_repo(row: Any) -> dict:
    _require(isinstance(row, dict) and row.get("full_name") == REPOSITORY, "REPOSITORY_SCOPE_INVALID")
    public = {"full_name": REPOSITORY}
    if "id" in row:
        _require(type(row["id"]) is int and row["id"] > 0, "REMOTE_RESPONSE_INVALID")
        public["id"] = row["id"]
    for key in ("private", "allow_merge_commit", "allow_squash_merge", "allow_rebase_merge"):
        if key in row:
            _require(type(row[key]) is bool, "REMOTE_RESPONSE_INVALID")
            public[key] = row[key]
    if "default_branch" in row:
        public["default_branch"] = _public_text(row["default_branch"])
    return public


def _public_text(value: Any) -> str:
    _require(isinstance(value, str) and 0 < len(value) <= 256
             and all(ord(char) >= 32 for char in value), "REMOTE_RESPONSE_INVALID")
    return value


def _protection_digest(row: dict) -> str:
    """Bind all raw protection parameters without disclosing their contents."""
    def json_data(value: Any) -> bool:
        if type(value) is dict:
            return all(type(key) is str and json_data(item) for key, item in value.items())
        if type(value) is list:
            return all(json_data(item) for item in value)
        return value is None or type(value) in {str, int, float, bool}

    try:
        subset = {key: row[key] for key in ("id", "name", "target", "enforcement", "conditions", "rules") if key in row}
        _require(json_data(subset), "REMOTE_RESPONSE_INVALID")
        raw = json.dumps(subset, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                         allow_nan=False).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()
    except Exception:
        raise PublicError("REMOTE_RESPONSE_INVALID") from None


def _public_ruleset(row: Any) -> dict:
    _require(isinstance(row, dict), "REMOTE_RESPONSE_INVALID")
    public = {"protection_sha256": _protection_digest(row)}
    for key in ("id", "name", "target", "enforcement", "current_user_can_bypass"):
        if key not in row:
            continue
        value = row[key]
        if key == "id":
            _require(type(value) is int and value > 0, "REMOTE_RESPONSE_INVALID")
        elif key == "current_user_can_bypass":
            _require(type(value) is bool or value in ("always", "pull_requests_only", "never"), "REMOTE_RESPONSE_INVALID")
        else:
            value = _public_text(value)
        public[key] = value
    conditions = row.get("conditions") or {}
    _require(isinstance(conditions, dict), "REMOTE_RESPONSE_INVALID")
    refs = conditions.get("ref_name")
    if isinstance(refs, dict):
        public["conditions"] = {"ref_name": {}}
        for key in ("include", "exclude"):
            if key in refs:
                _require(isinstance(refs[key], list), "REMOTE_RESPONSE_INVALID")
                public["conditions"]["ref_name"][key] = [_public_text(value) for value in refs[key]]
    if isinstance(row.get("bypass_actors"), list):
        public["bypass_actors"] = []
        for actor in row["bypass_actors"]:
            _require(isinstance(actor, dict), "REMOTE_RESPONSE_INVALID")
            item = {}
            for key in ("actor_id", "actor_type", "bypass_mode"):
                if key in actor:
                    if key == "actor_id":
                        _require(actor[key] is None or type(actor[key]) is int, "REMOTE_RESPONSE_INVALID")
                        item[key] = actor[key]
                    else:
                        item[key] = _public_text(actor[key])
            public["bypass_actors"].append(item)
    params = {"required_approving_review_count", "dismiss_stale_reviews_on_push", "require_last_push_approval",
              "required_review_thread_resolution", "require_code_owner_review", "allowed_merge_methods",
              "strict_required_status_checks_policy", "do_not_enforce_on_create"}
    if isinstance(row.get("rules"), list):
        public["rules"] = []
        for rule in row["rules"]:
            if not isinstance(rule, dict) or not isinstance(rule.get("type"), str):
                raise PublicError("REMOTE_RESPONSE_INVALID")
            item = {"type": _public_text(rule["type"])}
            if isinstance(rule.get("parameters"), dict):
                original = rule["parameters"]
                item["parameters"] = {}
                for key in params:
                    if key in original:
                        value = original[key]
                        if key == "allowed_merge_methods":
                            _require(isinstance(value, list), "REMOTE_RESPONSE_INVALID")
                            value = [_public_text(method) for method in value]
                        elif key == "required_approving_review_count":
                            _require(type(value) is int and value >= 0, "REMOTE_RESPONSE_INVALID")
                        else:
                            _require(type(value) is bool, "REMOTE_RESPONSE_INVALID")
                        item["parameters"][key] = value
                if isinstance(original.get("required_status_checks"), list):
                    checks = []
                    for check in original["required_status_checks"]:
                        _require(isinstance(check, dict), "REMOTE_RESPONSE_INVALID")
                        entry = {"context": _public_text(check.get("context"))}
                        if "integration_id" in check:
                            _require(check["integration_id"] is None or type(check["integration_id"]) is int,
                                     "REMOTE_RESPONSE_INVALID")
                            entry["integration_id"] = check["integration_id"]
                        checks.append(entry)
                    item["parameters"]["required_status_checks"] = checks
            public["rules"].append(item)
    return public


def child_environment(token: str | None, profile: Path, *, toolchain: dict | None = None) -> dict[str, str]:
    env = {name: value for name in _SAFE_PARENT if (value := os.environ.get(name)) is not None}
    env.update({"GH_HOST": "github.com", "GH_CONFIG_DIR": str(profile / "gh"),
                "GH_PROMPT_DISABLED": "1", "GIT_TERMINAL_PROMPT": "0", "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_CONFIG_GLOBAL": str(profile / "empty.gitconfig"),
                "GIT_CONFIG_SYSTEM": str(profile / "empty.gitconfig"),
                "HOME": str(profile), "USERPROFILE": str(profile), "XDG_CONFIG_HOME": str(profile)})
    # Only this broker-created short-lived token enters the child. No tracing.
    settings = []
    if toolchain is not None:
        env.update({key: toolchain[key] for key in ("GIT_DIR", "GIT_COMMON_DIR", "GIT_WORK_TREE")})
        if "hooks" in toolchain:
            settings.append(("core.hooksPath", toolchain["hooks"]))
    if token is not None:
        basic = base64.b64encode(f"x-access-token:{token}".encode()).decode("ascii")
        env["GH_TOKEN"] = token
        settings.append(("credential.helper", ""))
        for suffix in ("", ".git"):
            settings.append((f"http.https://github.com/{REPOSITORY}{suffix}.extraheader",
                             f"Authorization: Basic {basic}"))
    if settings:
        env["GIT_CONFIG_COUNT"] = str(len(settings))
        for index, (key, value) in enumerate(settings):
            env[f"GIT_CONFIG_KEY_{index}"] = key
            env[f"GIT_CONFIG_VALUE_{index}"] = value
    return env


def _public_git_marker(path: Path, *, prefix: str = "") -> str:
    """Only Git's bounded gitdir/commondir metadata, never config values."""
    with _path_guard(path):
        _require(path.is_file() and path.stat().st_size <= 4096, "TOOLCHAIN_METADATA_INVALID")
        text = path.read_text(encoding="utf-8").strip()
        _require(text.startswith(prefix) and "\n" not in text and "\r" not in text,
                 "TOOLCHAIN_METADATA_INVALID")
        return text[len(prefix):].strip()


def _inert_compatibility_key(key: str) -> bool:
    """Only two reviewed key forms, inert for the fixed command set.

    This does not approve an alias value or make alias dispatch available.
    Git/tool versions or command-set changes require renewed evidence.
    """
    if key == "alias.pushall":
        return True
    match = re.fullmatch(r"branch\.([A-Za-z0-9][A-Za-z0-9._/-]*)\.vscode-merge-base", key)
    if match is None:
        return False
    branch = match[1]
    return (".." not in branch and "//" not in branch and not branch.endswith("/")
            and all(not part.startswith(".") and not part.endswith((".", ".lock"))
                    for part in branch.split("/")))


def _git_config_untrusted(key: str) -> bool:
    """Only reviewed keys inert for the fixed command set; no alias dispatch."""
    if _inert_compatibility_key(key):
        return False
    key = key.lower()
    safe = {"core.repositoryformatversion", "core.filemode", "core.bare", "core.logallrefupdates",
            "core.ignorecase", "core.precomposeunicode", "core.longpaths", "core.autocrlf", "core.eol",
            "core.symlinks", "core.fscache", "user.name", "user.email", "extensions.objectformat"}
    return not (key in safe or re.fullmatch(r"remote\.[^.\r\n]+\.(?:url|fetch|pushurl)", key)
                or re.fullmatch(r"branch\.[^\r\n]+\.(?:remote|merge|pushremote|gh-merge-base)", key))


def _origin_matches(value: str) -> bool:
    # Two exact canonical HTTPS routes only. No username, query, redirects or
    # multiple destinations are normalized into an acceptable target.
    return bool(re.fullmatch(rf"https://github\.com/{re.escape(REPOSITORY)}(?:\.git)?", value))


@contextmanager
def _trusted_toolchain(root: Path):
    """Reject unreviewed local settings/hooks before minting any new token.

    No config values or active hook contents are requested. Only an existing
    linked worktree is supported, and its Git sources remain handle-locked and
    explicitly pinned. After the first real hook check passes, a broker-owned
    external empty hook path prevents newly added repository scripts from
    inheriting the token. Existing hook/config refusals never fall back here;
    CI, native guard and Owner requirements remain separate and unchanged.
    """
    root = _local_path(root)
    marker = root / ".git"
    _require(marker.is_file(), "TOOLCHAIN_LINKED_WORKTREE_REQUIRED")
    with tempfile.TemporaryDirectory(prefix="mj-public-git-preflight-") as folder, ExitStack() as locks:
        locks.enter_context(_path_guard(marker))
        gitdir = Path(_public_git_marker(marker, prefix="gitdir: "))
        if not gitdir.is_absolute():
            gitdir = root / gitdir
        gitdir = _local_path(Path(os.path.normpath(gitdir)))
        common_marker = gitdir / "commondir"
        _require(common_marker.is_file(), "TOOLCHAIN_LINKED_WORKTREE_REQUIRED")
        locks.enter_context(_path_guard(common_marker))
        common = _local_path(Path(os.path.normpath(gitdir / _public_git_marker(common_marker))))
        _require(common != gitdir, "TOOLCHAIN_LINKED_WORKTREE_REQUIRED")
        config = common / "config"
        hooks = common / "hooks"
        locks.enter_context(_path_guard(config))
        locks.enter_context(_path_guard(gitdir))
        _require(config.is_file(), "TOOLCHAIN_METADATA_INVALID")
        _require(not (gitdir / "config.worktree").exists(), "TOOLCHAIN_CONFIG_UNTRUSTED")
        profile = Path(folder)
        _outside_path(profile, root)
        (profile / "empty.gitconfig").write_bytes(b"")
        binding = {"GIT_DIR": str(gitdir), "GIT_COMMON_DIR": str(common), "GIT_WORK_TREE": str(root)}
        env = child_environment(None, profile, toolchain=binding)
        try:
            checked = subprocess.run(["git", "-C", str(root), "config", "--no-includes", "--name-only", "--list"],
                                     env=env, capture_output=True, text=True, check=False, timeout=20)
        except Exception:
            raise PublicError("TOOLCHAIN_INSPECTION_UNKNOWN") from None
        _require(checked.returncode == 0, "TOOLCHAIN_INSPECTION_UNKNOWN")
        _require(not any(_git_config_untrusted(key) for key in checked.stdout.splitlines()),
                 "TOOLCHAIN_CONFIG_UNTRUSTED")
        if hooks.exists():
            locks.enter_context(_path_guard(hooks))
            _require(hooks.is_dir(), "TOOLCHAIN_HOOK_UNTRUSTED")
            _require(all(path.name.endswith(".sample") and path.is_file() and not path.is_symlink()
                         and not getattr(path.lstat(), "st_file_attributes", 0) & 0x400
                         for path in hooks.iterdir()), "TOOLCHAIN_HOOK_UNTRUSTED")
        isolated_hooks = profile / "verified-empty-hooks"
        isolated_hooks.mkdir()
        locks.enter_context(_path_guard(isolated_hooks))
        _require(not any(isolated_hooks.iterdir()), "TOOLCHAIN_INSPECTION_UNKNOWN")
        binding["hooks"] = str(isolated_hooks)
        # This isolates repository-writable sources, not arbitrary same-user OS
        # access to the broker's process/tempfiles. No ACL/trust changes occur.
        yield binding


def _valid_route(root: Path, head: str, base: str) -> bool:
    """Fixed sibling source supports -I without user site or PYTHONPATH."""
    import importlib.util

    try:
        source = _local_path(Path(__file__).absolute().with_name("task_delivery.py"))
        spec = importlib.util.spec_from_file_location("_mj_delivery_task_routes", source)
        _require(spec is not None and spec.loader is not None, "PR_ROUTE_UNKNOWN")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.valid_pr_base(REPOSITORY, head, base, module.load_task_routes(root))
    except Exception:
        raise PublicError("PR_ROUTE_UNKNOWN") from None


class Controller:
    def __init__(self, vault: SecretVault, *, api: Any = None, signer: Any = _private_jwt) -> None:
        self.vault = vault
        self._api = api or _GitHubAPI()
        self._signer = signer

    def _call(self, method: str, path: str, **kwargs: Any) -> Any:
        _require(_api_allowed(method, path), "ENDPOINT_FORBIDDEN")
        try:
            return self._api(method, path, **kwargs)
        except Exception:
            raise PublicError("REMOTE_REQUEST_FAILED") from None

    @contextmanager
    def _session(self, phase: str):
        _require(phase in {"bootstrap", "daily"}, "PERMISSION_PHASE_INVALID")
        permissions = BOOTSTRAP_PERMISSIONS if phase == "bootstrap" else DAILY_PERMISSIONS
        record = self.vault._record()
        jwt = self._signer(record)
        app = _app_public(self._call("GET", "/app", credential=jwt), permissions)
        _require(app["id"] == record["app_id"], "APP_IDENTITY_INVALID")
        rows = self._call("GET", "/app/installations?per_page=100", credential=jwt)
        _require(isinstance(rows, list) and len(rows) == 1, "INSTALLATION_SCOPE_INVALID")
        install = _installation_public(rows[0], app["id"], permissions)
        observed = _installation_public(self._call("GET", f"/repos/{REPOSITORY}/installation", credential=jwt), app["id"], permissions)
        _require(install == observed, "INSTALLATION_SCOPE_INVALID")
        token = None
        mint_started = False
        failure = None
        public = {"state": "UNKNOWN", "source": "GITHUB_API_RUNTIME", "repository": REPOSITORY,
                  "permission_phase": phase, "app": app, "installation": install,
                  "token_revocation": "NOT_CREATED", "owner_authorization": "NOT_ASSESSED"}
        try:
            mint_started = True
            grant = self._call("POST", f"/app/installations/{install['id']}/access_tokens", credential=jwt,
                               body={"repositories": [REPO_NAME], "permissions": permissions})
            _require(isinstance(grant, dict) and isinstance(grant.get("token"), str) and bool(grant["token"]), "TOKEN_GRANT_INVALID")
            token = grant["token"]
            _require(grant.get("permissions") == permissions and isinstance(grant.get("expires_at"), str), "TOKEN_GRANT_INVALID")
            try:
                expires = datetime.fromisoformat(grant["expires_at"].replace("Z", "+00:00"))
                _require(expires.tzinfo is not None and 0 < (expires - datetime.now(UTC)).total_seconds() <= 3605,
                         "TOKEN_GRANT_INVALID")
                expiry = expires.astimezone(UTC).isoformat()
            except (ValueError, TypeError, OverflowError):
                raise PublicError("TOKEN_GRANT_INVALID") from None
            scope = self._call("GET", "/installation/repositories", credential=token)
            _require(isinstance(scope, dict) and type(scope.get("total_count")) is int and scope["total_count"] == 1
                     and isinstance(scope.get("repositories"), list) and len(scope["repositories"]) == 1,
                     "TOKEN_SCOPE_INVALID")
            repo = _public_repo(scope["repositories"][0])
            _require(type(repo.get("id")) is int and repo["id"] > 0, "TOKEN_SCOPE_INVALID")
            public["token_grant"] = {"total_count": 1, "repositories": [repo],
                                     "permissions": permissions, "expires_at": expiry}
            yield token, public
        except Exception as exc:
            failure = exc.code if isinstance(exc, PublicError) else "TOKEN_OPERATION_UNKNOWN"
        finally:
            if token is not None:
                try:
                    self._call("DELETE", "/installation/token", credential=token)
                    public["token_revocation"] = "CONFIRMED"
                except PublicError:
                    public["token_revocation"] = "UNKNOWN"
        if failure is not None:
            public.update({"retry": "FORBIDDEN_PENDING_RECONCILIATION", "side_effects":
                           "TOKEN_MAY_HAVE_BEEN_CREATED" if mint_started and token is None else "POSSIBLE_DO_NOT_RETRY",
                           "token_expiry": public.get("token_grant", {}).get(
                               "expires_at", "UNKNOWN_UP_TO_ONE_HOUR_FROM_ISSUANCE")})
            raise PublicError(failure, details=public) from None
        public["state"] = "EXECUTOR_VERIFIED" if public["token_revocation"] == "CONFIRMED" else "UNKNOWN"

    def audit(self, phase: str) -> dict:
        with self._session(phase) as (_, public):
            result = public
        return result

    def public_get(self, endpoint: str, phase: str) -> dict:
        _require(endpoint in {f"/repos/{REPOSITORY}", f"/repos/{REPOSITORY}/rulesets"}
                 or bool(re.fullmatch(rf"/repos/{re.escape(REPOSITORY)}/rulesets/[1-9][0-9]*", endpoint)),
                 "ENDPOINT_FORBIDDEN")
        with self._session(phase) as (token, public):
            original = self._call("GET", endpoint, credential=token)
            if endpoint == f"/repos/{REPOSITORY}":
                data = _public_repo(original)
            elif endpoint.endswith("/rulesets"):
                _require(isinstance(original, list), "REMOTE_RESPONSE_INVALID")
                data = [_public_ruleset(row) for row in original]
            else:
                data = _public_ruleset(original)
            result = {**public, "data": data}
        result.update({key: public[key] for key in ("state", "token_revocation")})
        return result

    def execute(self, action: str, arguments: dict, root: Path, phase: str) -> dict:
        _require(action in {"push", "pr-create", "merge"}, "ACTION_FORBIDDEN")
        root = root.resolve()
        branch = arguments.get("branch") if action == "push" else arguments.get("head")
        sha = arguments.get("head_sha")
        if action in {"push", "pr-create"}:
            _require(isinstance(branch, str) and bool(re.fullmatch(
                r"(?:feature|bugfix|documentation|maintain|hotfix)/[A-Za-z0-9][A-Za-z0-9_.-]*", branch)), "BRANCH_INVALID")
        if action in {"push", "merge"}:
            _require(isinstance(sha, str) and bool(re.fullmatch(r"[0-9a-f]{40}", sha)), "HEAD_INVALID")
        if action == "pr-create":
            _require(isinstance(arguments.get("base"), str) and isinstance(arguments.get("title"), str)
                     and 0 < len(arguments["title"]) <= 200, "PR_REQUEST_INVALID")
            _require(_valid_route(root, branch, arguments["base"]), "PR_BASE_INVALID")
            body = Path(arguments["body_file"])
            _require(body.suffix.lower() in {".md", ".txt"}, "PR_BODY_INVALID")
            body = _local_path(body)
            _require(body.is_file() and body.stat().st_size <= 65536, "PR_BODY_INVALID")
            command = ["gh", "pr", "create", "--repo", REPOSITORY, "--head", branch,
                       "--base", arguments["base"], "--title", arguments["title"], "--body-file", str(body)]
        elif action == "merge":
            _require(str(arguments.get("pr", "")).isdigit() and int(arguments["pr"]) > 0, "PR_REQUEST_INVALID")
            command = ["gh", "pr", "merge", str(arguments["pr"]), "--repo", REPOSITORY,
                       "--merge", "--match-head-commit", sha]
        else:
            command = ["git", "-C", str(root), "push", "--no-follow-tags", "--recurse-submodules=no",
                       "origin", f"{sha}:refs/heads/{branch}"]
        with _trusted_toolchain(root) as binding, self._session(phase) as (token, public), tempfile.TemporaryDirectory(prefix="mj-new-app-child-") as folder:
            profile = Path(folder)
            (profile / "empty.gitconfig").write_bytes(b"")
            env = child_environment(token, profile, toolchain=binding)
            try:
                if action == "push":
                    for check, expected in ((["git", "-C", str(root), "rev-parse", "HEAD"], sha),
                                            (["git", "-C", str(root), "branch", "--show-current"], branch)):
                        checked = subprocess.run(check, env=env, capture_output=True, text=True, check=False, timeout=20)
                        _require(checked.returncode == 0 and checked.stdout.strip() == expected, "PUSH_TARGET_INVALID")
                    for check in (["git", "-C", str(root), "remote", "get-url", "origin"],
                                  ["git", "-C", str(root), "remote", "get-url", "--push", "--all", "origin"]):
                        checked = subprocess.run(check, env=env, capture_output=True, text=True, check=False, timeout=20)
                        lines = checked.stdout.splitlines()
                        _require(checked.returncode == 0 and len(lines) == 1 and _origin_matches(lines[0]),
                                 "PUSH_TARGET_INVALID")
                proc = subprocess.run(command, cwd=root, env=env, capture_output=True,
                                      text=True, check=False, timeout=120)
                _require(proc.returncode == 0, "EXECUTION_UNKNOWN")
                result = {"source": "GITHUB_API_RUNTIME", "action": action, "status": "COMMAND_SUCCEEDED",
                          "repository": REPOSITORY, "token_revocation": "PENDING"}
                if action == "pr-create":
                    match = re.fullmatch(rf"https://github.com/{re.escape(REPOSITORY)}/pull/[1-9][0-9]*", proc.stdout.strip())
                    _require(bool(match), "EXECUTION_UNKNOWN")
                    result["pr_url"] = proc.stdout.strip()
            except Exception:
                raise PublicError("EXECUTION_UNKNOWN", details={"side_effects": "POSSIBLE_DO_NOT_RETRY",
                                                               "token_expiry": public["token_grant"]["expires_at"]}) from None
        result["token_revocation"] = public["token_revocation"]
        return result


class _QuietServer(HTTPServer):
    def handle_error(self, request: Any, client_address: Any) -> None:
        # Exceptions can hold callback request paths; never log them.
        return

    def server_close(self) -> None:
        registration = getattr(self, "registration", None)
        if registration is not None:
            registration.close()
        super().server_close()


def make_server(vault: SecretVault, *, port: int = 0, api: Any = None) -> tuple[HTTPServer, Registration]:
    """Loopback only; caller owns its lifetime. This never opens a browser."""
    _require(type(port) is int and 0 <= port <= 65535, "PORT_INVALID")
    _require(not vault.path.exists() and not vault.attempt.exists(), "REGISTRATION_ALREADY_ATTEMPTED")
    registration = Registration(vault, api=api)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args: Any) -> None:
            return

        def send_error(self, code: int, message: str | None = None, explain: str | None = None) -> None:
            # The base class includes malformed request lines in its HTML error.
            self._response(code, b'{"status":"ERROR","error":"REQUEST_INVALID"}')

        def _response(self, status: int, payload: bytes, *, content: str = "application/json", headers: dict | None = None) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'none'; form-action https://github.com; frame-ancestors 'none'; base-uri 'none'")
            for name, value in (headers or {}).items():
                self.send_header(name, value)
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self) -> None:  # noqa: N802
            try:
                _require(self.headers.get("Host") == f"127.0.0.1:{self.server.server_port}", "HOST_FORBIDDEN")
                parsed = urllib.parse.urlsplit(self.path)
                _require(not parsed.scheme and not parsed.netloc and not parsed.fragment,
                         "CALLBACK_INVALID")
                if parsed.path == "/register" and not parsed.query:
                    state, nonce = registration.begin()
                    callback = f"http://127.0.0.1:{self.server.server_port}/manifest/callback"
                    manifest = {"name": APP_SLUG, "url": f"https://github.com/{REPOSITORY}", "redirect_url": callback,
                                "public": False, "hook_attributes": {"active": False, "url": "https://invalid.invalid/mj-agent-unused-webhook"},
                                "default_events": [], "default_permissions": BOOTSTRAP_PERMISSIONS}
                    import html
                    form = (f'<form method="post" action="https://github.com/organizations/{OWNER}/settings/apps/new?state={state}">'
                            f'<input type="hidden" name="manifest" value="{html.escape(json.dumps(manifest), quote=True)}">'
                            '<button>Register permitted App</button></form>').encode()
                    self._response(200, form, content="text/html; charset=utf-8", headers={
                        "Set-Cookie": f"{_COOKIE}={nonce}; HttpOnly; SameSite=Lax; Path=/"})
                elif parsed.path == "/manifest/callback":
                    try:
                        values = urllib.parse.parse_qs(parsed.query, strict_parsing=True, max_num_fields=2)
                        _require(set(values) == {"code", "state"} and all(len(value) == 1 for value in values.values()), "CALLBACK_INVALID")
                        cookie = SimpleCookie(self.headers.get("Cookie", ""))
                        nonce = cookie[_COOKIE].value if _COOKIE in cookie else ""
                        registration.dispatch(values["code"][0], values["state"][0], nonce)
                    except Exception:
                        if registration.result.get("status") not in {"WAITING", "REGISTERED", "UNKNOWN"}:
                            registration.result = {"status": "ERROR", "error": "CALLBACK_INVALID"}
                    self._response(303, b"", headers={"Location": "/result", "Set-Cookie": f"{_COOKIE}=; Max-Age=0; HttpOnly; Path=/"})
                elif parsed.path == "/result" and not parsed.query:
                    self._response(200, json.dumps(registration.public_result()).encode())
                else:
                    raise PublicError("ENDPOINT_FORBIDDEN")
            except Exception:
                self._response(400, b'{"status":"ERROR","error":"CALLBACK_INVALID"}')

        def do_POST(self) -> None:  # noqa: N802
            self._response(405, b'{"status":"ERROR","error":"METHOD_FORBIDDEN"}')

        do_PUT = do_POST  # noqa: N815
        do_DELETE = do_POST  # noqa: N815
        do_PATCH = do_POST  # noqa: N815

    server = _QuietServer(("127.0.0.1", port), Handler)
    server.registration = registration
    return server, registration


def serve(vault: SecretVault, *, port: int = 0, api: Any = None) -> None:
    server, registration = make_server(vault, port=port, api=api)
    print(json.dumps({"status": "READY", "register_url": f"http://127.0.0.1:{server.server_port}/register",
                      "result_url": f"http://127.0.0.1:{server.server_port}/result", "repository": REPOSITORY}), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
        result = registration.public_result()
        if result.get("status") == "UNKNOWN":
            raise PublicError("REGISTRATION_STOPPED_UNKNOWN", details=result) from None
        raise
    finally:
        server.server_close()


class _PublicParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise PublicError("INVALID_REQUEST")


def main(argv: list[str] | None = None) -> int:
    parser = _PublicParser(description=__doc__)
    parser.add_argument("action", choices=("serve", "audit", "public-get", "push", "pr-create", "merge"))
    parser.add_argument("--vault-dir", type=Path, required=True)
    parser.add_argument("--permission-phase", choices=("bootstrap", "daily"), default="daily")
    parser.add_argument("--root", type=Path, default=_ROOT)
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--endpoint")
    parser.add_argument("--branch")
    parser.add_argument("--head")
    parser.add_argument("--head-sha")
    parser.add_argument("--base")
    parser.add_argument("--title")
    parser.add_argument("--body-file")
    parser.add_argument("--pr")
    try:
        args = parser.parse_args(argv)
        vault = SecretVault(args.vault_dir, repo_root=args.root)
        if args.action == "serve":
            serve(vault, port=args.port)
            return 0
        controller = Controller(vault)
        if args.action == "audit":
            result = controller.audit(args.permission_phase)
        elif args.action == "public-get":
            _require(isinstance(args.endpoint, str), "INVALID_REQUEST")
            result = controller.public_get(args.endpoint, args.permission_phase)
        else:
            result = controller.execute(args.action, vars(args), args.root, args.permission_phase)
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result.get("token_revocation") == "CONFIRMED" else 1
    except PublicError as exc:
        print(json.dumps({"status": "UNKNOWN", "error": exc.code, **exc.details}))
        return 2
    except KeyboardInterrupt:
        print('{"status":"STOPPED"}')
        return 0
    except Exception:
        print('{"status":"UNKNOWN","error":"BACKEND_OPERATION_FAILED"}')
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
