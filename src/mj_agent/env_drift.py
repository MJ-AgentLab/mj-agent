"""Detect `.env.example` template drift against the developer's `.env`.

Mirrors the PowerShell drift detection in `scripts/setup-env.ps1` (added in
commit 17fcc47) so `uv run mj-agent check` surfaces the same warning even
when developers skip re-running setup-env.ps1 (e.g. they already have a
`.env` from a prior session).

Algorithm: parse keys from each file (skipping blank / `#` lines), return
keys present in `.env.example` but missing from `.env`. Values are not
read or compared.

Scope (post ADR-030): app keys only. MCP infrastructure secrets (5 SSH +
10 PG URL = 15 keys) live in ``config/secrets-mcp.enc`` and are decrypted
directly to OS env via ``.claude/scripts/setup-mcp-secrets.ps1``. They are
intentionally **not** declared in ``.env.example`` and **not** in ``.env``,
so drift detection ignores them by construction. To check MCP keys
separately, run ``setup-mcp-secrets.ps1 -Reload`` which compares OS
User-level env (``HKCU/Environment``) against ``config/secrets-mcp.example``.
"""

from __future__ import annotations

from pathlib import Path


def _parse_keys(path: Path) -> set[str]:
    keys: set[str] = set()
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        eq_idx = line.find("=")
        if eq_idx <= 0:
            continue
        keys.add(line[:eq_idx].strip())
    return keys


def find_env_drift(env_path: Path, example_path: Path) -> list[str]:
    """Return keys declared in `example_path` but missing from `env_path`.

    Returns an empty list if either file is missing (CI runners typically
    have no `.env`; that is not a drift condition). Result is sorted for
    deterministic CLI output.
    """

    if not env_path.is_file() or not example_path.is_file():
        return []
    env_keys = _parse_keys(env_path)
    example_keys = _parse_keys(example_path)
    return sorted(example_keys - env_keys)
