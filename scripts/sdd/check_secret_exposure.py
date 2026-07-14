"""scripts/sdd/check_secret_exposure.py — G7 validator (real implementation).

New in post-M6 completion-audit PR2 (M6-FU-GATES-TRUTH-UP). Pure static —
runs in CI without any secret material.

Semantic correction vs the original gates.md / policies/security.md TBD
wording: what must never enter git or the image is the **decrypted artifacts**
(`.env`, `config/secrets*.conf`, key files). The `config/secrets*.enc`
ciphertext bundles are *intentionally committed* (ADR-030 2-bundle pipeline);
flagging them would be wrong.

Four checks:

(1) tracked-files (FAIL): `git ls-files` must not contain `.env` / `.env.*`
    (except `.env.example`) / `config/secrets*.conf` / `*.pem` / `*.key`.
(2) .gitignore pins (WARN): required ignore entries present
    (`.env` / `config/secrets.conf` / `config/secrets-mcp.conf`).
(3) docker build-context (WARN): `docker/Dockerfile` has `COPY config/` AND
    the DEV compose build context is the repo root → the repo root MUST have
    a `.dockerignore` that covers `config/secrets*.conf` (file missing OR
    coverage absent both WARN — an empty .dockerignore must not satisfy the
    gate). Root `.dockerignore` landed owner-approved 2026-06-11
    (completion-audit follow-up). Note: `docker/.dockerignore` is ineffective
    for `context: ../` builds — dockerignore applies at the context root only.
(4) .codex/config.toml content (FAIL; S2 #330 scan-domain extension): the
    generated Codex MCP projection may reference secrets BY NAME only
    (`env_vars` whitelists). Any `[mcp_servers.*.env]` table (the emitter never
    writes one — its presence means a hand edit / literal injection), any URL
    userinfo password (`://user:pass@`), or any `password/token/secret/api_key=`
    literal inside a string value FAILs. File absent == PASS (pre-S2 / fork
    state); the first line of defense is the V11 blocking drift gate — this
    content scan is defense in depth.

WARNING mode (`continue-on-error: true` in ci.yml); expected baseline
4P/0W/0F (was 3P/0W/0F before the S2 #330 codex-config check; 2P/1W at PR2
landing). Blocking flip is a separate `ci-blocking-gate-toggle` HITL action.
"""

from __future__ import annotations

import re
import subprocess
import sys
import tomllib
from pathlib import Path, PurePosixPath

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.sdd._common.cli import Severity, Summary, build_argparser  # noqa: E402

_SCRIPT_NAME = "check_secret_exposure"

_ALLOWED_ENV_BASENAMES = frozenset({".env.example"})
_REQUIRED_GITIGNORE_PINS = (".env", "config/secrets.conf", "config/secrets-mcp.conf")
_SECRET_CONF_PATTERN = re.compile(r"^config/secrets[^/]*\.conf$")
_COPY_CONFIG_PATTERN = re.compile(r"^\s*COPY\s+(--[\w=]+\s+)*config/", re.MULTILINE)
_CONTEXT_REPO_ROOT_PATTERN = re.compile(r"^\s*context:\s*(\.\./?|\.\.)\s*$", re.MULTILINE)
# Check (4) — .codex/config.toml literal-credential shapes (S2 #330). No leading
# \b on the keyword group: the repo's real env-key names are PREFIXED shapes like
# SSH_SERVER_*_PASSWORD / GITHUB_..._TOKEN and `_` is a word character, so a word
# boundary would never match them (review finding #330-1).
_URL_USERINFO_PATTERN = re.compile(r"://[^/\s:@]+:[^@\s]+@")
_LITERAL_CRED_PATTERN = re.compile(r"(?i)(password|token|secret|api_key)\s*=\s*\S")


def _is_decrypted_artifact(tracked_path: str) -> bool:
    """True if a tracked path matches a decrypted-secret-material pattern."""
    posix = PurePosixPath(tracked_path)
    name = posix.name
    if name == ".env" or (name.startswith(".env.") and name not in _ALLOWED_ENV_BASENAMES):
        return True
    if _SECRET_CONF_PATTERN.match(tracked_path):
        return True
    return name.endswith((".pem", ".key"))


def _check_tracked_files(tracked: list[str]) -> Summary:
    """Check (1): no decrypted artifacts tracked in git (FAIL per hit)."""
    summary = Summary()
    offenders = [p for p in tracked if _is_decrypted_artifact(p)]
    for path in offenders:
        summary.add(
            Severity.FAIL,
            f"tracked file {path!r} matches decrypted-secret pattern "
            "(.env/.env.* except example, config/secrets*.conf, *.pem, *.key)",
        )
    if not offenders:
        summary.add(
            Severity.PASS,
            f"git tracked files clean ({len(tracked)} paths; no decrypted-secret patterns; "
            "secrets*.enc ciphertext intentionally committed per ADR-030)",
        )
    return summary


def _check_gitignore_pins(gitignore_text: str | None) -> Summary:
    """Check (2): .gitignore carries the decrypted-artifact pin entries (WARN)."""
    summary = Summary()
    if gitignore_text is None:
        summary.add(Severity.WARN, ".gitignore missing — decrypted-artifact pins absent")
        return summary
    lines = {line.strip() for line in gitignore_text.splitlines()}
    missing = [pin for pin in _REQUIRED_GITIGNORE_PINS if pin not in lines]
    if missing:
        summary.add(
            Severity.WARN,
            f".gitignore missing pin entries: {', '.join(missing)}",
        )
    else:
        summary.add(
            Severity.PASS,
            f".gitignore pins present ({', '.join(_REQUIRED_GITIGNORE_PINS)})",
        )
    return summary


def _dockerignore_covers_secrets(dockerignore_text: str) -> bool:
    """True if the root .dockerignore excludes the decrypted secrets conf files.

    Accepted coverage forms (non-comment lines): the canonical glob
    ``config/secrets*.conf``, an equivalent broader glob, or both explicit
    file entries. Keeps the predicate simple — coverage of `.env`/key
    material is encouraged but not gated (the Dockerfile never COPYs them).
    """
    lines = {
        line.strip()
        for line in dockerignore_text.splitlines()
        if line.strip() and not line.strip().startswith("#")
    }
    if {"config/secrets*.conf", "config/secrets*", "**/secrets*.conf"} & lines:
        return True
    return {"config/secrets.conf", "config/secrets-mcp.conf"} <= lines


def _check_build_context(
    dockerfile_text: str | None,
    compose_override_text: str | None,
    root_dockerignore_text: str | None,
) -> Summary:
    """Check (3): COPY config/ + repo-root build context needs an EFFECTIVE root .dockerignore.

    WARN when the file is missing OR exists but does not cover
    config/secrets*.conf (an empty/unrelated .dockerignore must not satisfy
    the gate). Root .dockerignore landed owner-approved 2026-06-11
    (completion-audit follow-up) — baseline moved 2P/1W → 3P/0W.
    """
    summary = Summary()
    if dockerfile_text is None:
        summary.add(Severity.WARN, "docker/Dockerfile missing — build-context check skipped")
        return summary

    copies_config = bool(_COPY_CONFIG_PATTERN.search(dockerfile_text))
    context_is_repo_root = bool(
        compose_override_text and _CONTEXT_REPO_ROOT_PATTERN.search(compose_override_text)
    )

    if copies_config and context_is_repo_root:
        if root_dockerignore_text is None:
            summary.add(
                Severity.WARN,
                "docker/Dockerfile `COPY config/` + DEV compose context=repo-root + NO root "
                ".dockerignore: a locally-decrypted config/secrets*.conf would enter the DEV "
                "image (docker/.dockerignore is ineffective for context: ../).",
            )
        elif not _dockerignore_covers_secrets(root_dockerignore_text):
            summary.add(
                Severity.WARN,
                "root .dockerignore exists but does NOT cover config/secrets*.conf — "
                "the exclusion is ineffective for the `COPY config/` + repo-root-context "
                "DEV build; add the canonical glob line.",
            )
        else:
            summary.add(
                Severity.PASS,
                "docker build-context exposure clean (root .dockerignore covers "
                "config/secrets*.conf for the repo-root-context DEV build)",
            )
    else:
        summary.add(
            Severity.PASS,
            "docker build-context exposure clean (no COPY config/ or non-root context)",
        )
    return summary


def _iter_strings(node: object) -> list[str]:
    """All string values inside a parsed TOML structure (depth-first)."""
    out: list[str] = []
    if isinstance(node, str):
        out.append(node)
    elif isinstance(node, dict):
        for value in node.values():
            out.extend(_iter_strings(value))
    elif isinstance(node, list):
        for value in node:
            out.extend(_iter_strings(value))
    return out


def _check_codex_config(config_text: str | None) -> Summary:
    """Check (4): .codex/config.toml carries no literal credentials (FAIL).

    The emitter (agents_sync.py emitter B) references secrets BY NAME via
    `env_vars`; it never writes an `env` table. Defense in depth behind the V11
    blocking drift gate.
    """
    summary = Summary()
    if config_text is None:
        summary.add(
            Severity.PASS,
            ".codex/config.toml absent — nothing to scan (pre-S2 / fork state)",
        )
        return summary
    try:
        parsed = tomllib.loads(config_text.replace("\r\n", "\n"))
    except tomllib.TOMLDecodeError as exc:
        summary.add(
            Severity.WARN,
            f".codex/config.toml is not valid TOML ({exc}) — content scan skipped"
            " (the V11 blocking drift gate rejects any deviation from the generator)",
        )
        return summary

    findings: list[str] = []
    servers = parsed.get("mcp_servers")
    if isinstance(servers, dict):
        for name, node in servers.items():
            if isinstance(node, dict) and "env" in node:
                findings.append(
                    f"mcp_servers.{name} has an `env` table — the emitter never writes"
                    " one; literal credential risk (secrets go BY NAME via env_vars)"
                )
    # NEVER echo flagged value content — the checker must not become the leak
    # (review finding #330-2). Report shape + length only.
    for text in _iter_strings(parsed):
        if _URL_USERINFO_PATTERN.search(text):
            findings.append(
                f"URL userinfo password shape in a string value (length {len(text)};"
                " content not echoed)"
            )
        elif _LITERAL_CRED_PATTERN.search(text):
            findings.append(
                f"literal credential assignment shape in a string value (length"
                f" {len(text)}; content not echoed)"
            )
    for finding in findings:
        summary.add(Severity.FAIL, f".codex/config.toml: {finding}")
    if not findings:
        server_count = len(servers) if isinstance(servers, dict) else 0
        summary.add(
            Severity.PASS,
            f".codex/config.toml clean ({server_count} servers; env-var NAME references"
            " only, no env tables, no literal-credential shapes)",
        )
    return summary


def _git_tracked_files(repo_root: Path) -> list[str] | None:
    """`git ls-files` at repo_root; None on subprocess failure."""
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30,
            check=False,
        )
        if result.returncode != 0:
            return None
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]
    except (OSError, subprocess.SubprocessError):
        return None


def _read_text_or_none(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def main(argv: list[str] | None = None) -> int:
    """G7 validator entry point."""
    parser = build_argparser(
        _SCRIPT_NAME,
        "G7 secret exposure validator (decrypted artifacts not in git; .gitignore pins; "
        "docker build-context exposure; secrets*.enc ciphertext is allowed by design)",
        ".gitignore",
    )
    args = parser.parse_args(argv)
    repo_root = Path(__file__).resolve().parent.parent.parent

    if args.dry_run:
        print(f"{_SCRIPT_NAME}: static checks over git ls-files + .gitignore + docker/ (dry-run)")
        return 0

    aggregate = Summary()

    tracked = _git_tracked_files(repo_root)
    if tracked is None:
        aggregate.add(Severity.WARN, "git ls-files unavailable — tracked-files check skipped")
    else:
        aggregate.merge(sub := _check_tracked_files(tracked))
        sub.print_messages()

    gitignore_summary = _check_gitignore_pins(_read_text_or_none(repo_root / ".gitignore"))
    aggregate.merge(gitignore_summary)
    gitignore_summary.print_messages()

    context_summary = _check_build_context(
        _read_text_or_none(repo_root / "docker" / "Dockerfile"),
        _read_text_or_none(repo_root / "docker" / "compose.override.yml"),
        _read_text_or_none(repo_root / ".dockerignore"),
    )
    aggregate.merge(context_summary)
    context_summary.print_messages()

    codex_summary = _check_codex_config(
        _read_text_or_none(repo_root / ".codex" / "config.toml")
    )
    aggregate.merge(codex_summary)
    codex_summary.print_messages()

    print(
        f"{_SCRIPT_NAME}: "
        f"{aggregate.pass_count}P / {aggregate.warn_count}W / {aggregate.fail_count}F "
        "(decrypted-artifact patterns; ciphertext .enc allowed per ADR-030)"
    )
    return aggregate.exit_code(strict=args.strict)


if __name__ == "__main__":
    sys.exit(main())
