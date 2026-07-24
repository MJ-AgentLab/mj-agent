"""``mj-agent`` CLI — typer-based wrapper around the runtime entrypoints.

Commands (Phase 1 sub 1.A + follow-ups):

  - ``mj-agent serve``  — launch the Chainlit UI on the configured host/port
  - ``mj-agent check``  — health probe. Default: credential presence + a sync
    memory-DB ping + env drift (fast, offline-safe; the Docker ``HEALTHCHECK``).
    ``--live`` additionally exercises the async checkpointer path (issue #283),
    connects to the biz DB, and does a 1-token LLM round-trip.
  - ``mj-agent memory-evict`` — TTL/retention eviction of stale checkpoint threads
    (mechanism C; ADR-038). Opt-in + irreversible; ``--dry-run`` first. Wire into
    external cron (mj-agent has no in-app scheduler).

Each command is intentionally thin; the heavy lifting lives in the
modules it imports lazily (so ``mj-agent --help`` works without a live
DB or ARK key).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import typer

if TYPE_CHECKING:
    from mj_agent.config import Settings

app = typer.Typer(
    name="mj-agent",
    help="mj-agent runtime CLI (Phase 1).",
    add_completion=False,
    no_args_is_help=True,
)


def _ui_path() -> Path:
    return Path(__file__).resolve().parent.parent / "ui.py"


@app.command("serve")
def serve(
    host: str | None = typer.Option(None, help="Override CHAINLIT_HOST."),
    port: int | None = typer.Option(None, help="Override CHAINLIT_PORT."),
    headless: bool = typer.Option(
        False, "--headless", help="Pass `-h` to chainlit (no browser auto-open)."
    ),
) -> None:
    """Launch the Chainlit UI."""
    from mj_agent.config import settings

    bind_host = host or settings.chainlit_host
    bind_port = port or settings.chainlit_port
    cmd = [
        sys.executable,
        "-m",
        "chainlit",
        "run",
        str(_ui_path()),
        "--host",
        bind_host,
        "--port",
        str(bind_port),
    ]
    if headless:
        cmd.append("-h")
    typer.echo(f"[mj-agent serve] {' '.join(cmd)}")
    raise typer.Exit(code=subprocess.call(cmd))


def _memory_sync_ping(settings: Settings) -> str | None:
    """Best-effort *sync* ping of the memory DB. Returns an error string or None.

    Returns None (skip) when creds are absent so ``check`` can report what's
    missing. This is the fast, offline-safe path the Docker healthcheck uses;
    it does NOT exercise the async pool that ``serve`` depends on (see
    ``--live``).
    """
    if not (
        settings.mj_agent_memory_user
        and settings.mj_agent_memory_password.get_secret_value()
    ):
        return None
    try:
        import psycopg

        from mj_agent.memory import memory_conn_string

        with psycopg.connect(memory_conn_string(), connect_timeout=5) as conn:
            conn.execute("SELECT 1")
    except Exception as exc:  # noqa: BLE001
        return f"memory DB unreachable: {exc}"
    return None


async def _probe_memory_async() -> None:
    """Open the async checkpointer (AsyncConnectionPool + ``setup()``) and close it.

    This is the path Chainlit ``serve`` uses and the one ``_memory_sync_ping``
    cannot reach — it catches issue #283-class async event-loop breaks. The
    idempotent ``setup()`` DDL runs here exactly as it does on first ``serve``.
    """
    from mj_agent.memory import open_checkpointer

    async with open_checkpointer():
        pass


def _probe_biz_sync() -> None:
    """Connect to the biz DB as the analyst role and run ``SELECT 1``."""
    from mj_agent.integrations.mj_system_db import readonly_cursor

    with readonly_cursor() as cur:
        cur.execute("SELECT 1")
        cur.fetchone()


def _probe_llm_sync() -> None:
    """Minimal 1-token LLM round-trip — proves the endpoint answers.

    Asserts only that ``invoke`` returns without raising: content can be
    legitimately empty under ark thinking-mode / ``max_tokens=1``. Deep
    tool-calling capability checks live in the
    ``/mj-agent-infra-llm-endpoint-probe`` skill, not here.
    """
    from mj_agent.llm import make_llm

    make_llm().invoke("ping", max_tokens=1)


def _run_live_probes(settings: Settings) -> list[tuple[str, str, str]]:
    """Run the three deep probes, each gated on its own credentials.

    Returns ``(name, status, detail)`` rows where status is ``PASS`` / ``SKIP``
    / ``FAIL``. A probe with absent creds is ``SKIP`` (never ``FAIL``) —
    mirroring the base creds-gates so ``--live`` stays runnable in partial-cred
    environments. Only an attempted-and-failed probe (``FAIL``) should affect
    the caller's exit code.
    """
    import asyncio

    from mj_agent.runtime import run_async

    rows: list[tuple[str, str, str]] = []

    # async memory — the #283 catcher. Its failure mode is a ~30s pool
    # retry-timeout, so bound it well under that.
    if (
        settings.mj_agent_memory_user
        and settings.mj_agent_memory_password.get_secret_value()
    ):
        try:
            run_async(asyncio.wait_for(_probe_memory_async(), timeout=8))
            rows.append(("async memory", "PASS", ""))
        except Exception as exc:  # noqa: BLE001
            rows.append(("async memory", "FAIL", str(exc)))
    else:
        rows.append(("async memory", "SKIP", "MJ_AGENT_MEMORY_USER/PASSWORD absent"))

    # biz DB
    if (
        settings.postgres_analyst_user
        and settings.postgres_analyst_password.get_secret_value()
    ):
        try:
            _probe_biz_sync()
            rows.append(("biz db", "PASS", ""))
        except Exception as exc:  # noqa: BLE001
            rows.append(("biz db", "FAIL", str(exc)))
    else:
        rows.append(("biz db", "SKIP", "POSTGRES_ANALYST_USER/PASSWORD absent"))

    # LLM round-trip (provider-aware gate, mirrors the base creds check)
    llm_creds = (
        settings.effective_llm_api_key
        if settings.llm_provider == "ark"
        else settings.effective_llm_base_url
    )
    if llm_creds:
        try:
            _probe_llm_sync()
            rows.append(("llm round-trip", "PASS", ""))
        except Exception as exc:  # noqa: BLE001
            rows.append(("llm round-trip", "FAIL", str(exc)))
    else:
        rows.append(("llm round-trip", "SKIP", "LLM credentials absent"))

    return rows


def _render_live_rows(rows: list[tuple[str, str, str]], *, err: bool) -> None:
    """Print the live-probe table + a PASS/SKIP/FAIL tally.

    SKIP is rendered distinctly and always counted, so a run where every probe
    silently skipped cannot masquerade as a live-verified success.
    """
    width = max(len(name) for name, _, _ in rows)
    for name, status, detail in rows:
        suffix = f" ({detail})" if detail and status != "PASS" else ""
        typer.echo(f"  [live] {name.ljust(width)} : {status}{suffix}", err=err)
    n_pass = sum(1 for _, s, _ in rows if s == "PASS")
    n_skip = sum(1 for _, s, _ in rows if s == "SKIP")
    n_fail = sum(1 for _, s, _ in rows if s == "FAIL")
    typer.echo(
        f"  [live] summary: {n_pass} PASS / {n_skip} SKIP / {n_fail} FAIL",
        err=err,
    )
    if n_pass == 0 and n_fail == 0:
        typer.echo(
            "  [live] WARNING: all live probes skipped (credentials absent) — "
            "no live verification was performed",
            err=True,
        )


@app.command("check")
def check(
    live: bool = typer.Option(
        False,
        "--live",
        help=(
            "Also run live probes: async memory pool (issue #283), biz DB "
            "SELECT 1, 1-token LLM round-trip. NOT used by the Docker "
            "healthcheck; run before `serve` to catch async/biz/LLM breaks the "
            "default check misses."
        ),
    ),
) -> None:
    """Health probe — verify imports + DB / LLM credentials.

    Default: credential presence + a sync memory-DB ping + env drift — fast and
    offline-safe, suitable for the Docker ``HEALTHCHECK``. Pass ``--live`` to
    additionally exercise the async checkpointer path (issue #283), connect to
    the biz DB, and do a minimal LLM round-trip.

    Exit code 0 on full pass; non-zero on any failure (with reason on stderr).
    SKIP (creds absent) never affects the exit code.
    """
    failures: list[str] = []

    try:
        from mj_agent.config import settings
    except Exception as exc:  # noqa: BLE001
        typer.echo(f"FAIL config: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    if not settings.postgres_analyst_user:
        failures.append("POSTGRES_ANALYST_USER not set")

    # Provider-aware LLM creds check (ADR-025).
    if settings.llm_provider == "ark" and not settings.effective_llm_api_key:
        failures.append("ARK_API_KEY not set")
    elif (
        settings.llm_provider == "local-openai-compat"
        and not settings.effective_llm_base_url
    ):
        failures.append(
            "LLM_BASE_URL not set (required when LLM_PROVIDER=local-openai-compat; "
            "e.g. http://192.168.0.189:8000/v1 for DGX vLLM)"
        )

    if not settings.mj_agent_memory_user:
        failures.append("MJ_AGENT_MEMORY_USER not set")

    # Memory DB ping (best-effort sync; skip if creds absent so users can run
    # `check` to discover what's missing). Does NOT exercise the async pool.
    ping_err = _memory_sync_ping(settings)
    if ping_err:
        failures.append(ping_err)

    # Live probes (opt-in) — exercise the paths the default check cannot reach.
    live_rows: list[tuple[str, str, str]] = []
    if live:
        live_rows = _run_live_probes(settings)
        failures.extend(
            f"[live] {name}: {detail}"
            for name, status, detail in live_rows
            if status == "FAIL"
        )

    # `.env.example` -> `.env` template drift (warn-only; mirrors
    # scripts/setup-env.ps1 detection so users who skip re-running the
    # PowerShell setup still see the warning at every healthcheck).
    from mj_agent.env_drift import find_env_drift

    drift = find_env_drift(Path(".env"), Path(".env.example"))
    if drift:
        typer.echo(
            f"[DRIFT] .env.example declares {len(drift)} key(s) missing from your .env:",
            err=True,
        )
        for key in drift:
            typer.echo(f"  [MISSING] {key}", err=True)

    if failures:
        typer.echo("CHECK FAILED:", err=True)
        for f in failures:
            typer.echo(f"  - {f}", err=True)
        if live_rows:
            _render_live_rows(live_rows, err=True)
        raise typer.Exit(code=1)

    typer.echo("CHECK OK")
    if live_rows:
        _render_live_rows(live_rows, err=False)
    typer.echo(f"  profile = {settings.mj_config_profile}")
    typer.echo(f"  biz host = {settings.biz_pg_host}:{settings.biz_pg_port}")
    typer.echo(f"  memory db = {settings.mj_agent_memory_db}")
    typer.echo(f"  chainlit  = {settings.chainlit_host}:{settings.chainlit_port}")
    typer.echo(f"  langsmith = tracing={settings.langsmith_tracing}")
    typer.echo(
        f"  llm provider = {settings.llm_provider} "
        f"(endpoint={settings.effective_llm_base_url})"
    )


@app.command("memory-evict")
def memory_evict(
    older_than: int | None = typer.Option(
        None,
        "--older-than",
        help=(
            "TTL in days; overrides MJ_AGENT_MEMORY_TTL_DAYS. Threads whose newest checkpoint "
            "is older than this are deleted."
        ),
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Report stale threads without deleting anything."
    ),
) -> None:
    """Evict memory checkpoint threads older than the TTL (mechanism C; ADR-038).

    OPT-IN: does nothing unless a positive TTL is set (``MJ_AGENT_MEMORY_TTL_DAYS`` or
    ``--older-than``). Deletion is IRREVERSIBLE — drops the thread's checkpoints + blobs +
    writes; run ``--dry-run`` first. mj-agent has no in-app scheduler: wire this into external
    cron / Task Scheduler for periodic retention (see the capability runbook).

    Exit 0 on success, on opt-out (TTL <= 0), and on absent memory credentials (SKIP).
    """
    import time

    from mj_agent.config import settings

    ttl_days = older_than if older_than is not None else settings.mj_agent_memory_ttl_days
    if ttl_days <= 0:
        typer.echo(
            "[memory-evict] TTL is not a positive number of days "
            "(MJ_AGENT_MEMORY_TTL_DAYS=0 by default; --older-than overrides) — nothing to do "
            "(opt-in). Pass a positive --older-than or set MJ_AGENT_MEMORY_TTL_DAYS to enable."
        )
        return
    if not (
        settings.mj_agent_memory_user
        and settings.mj_agent_memory_password.get_secret_value()
    ):
        typer.echo("[memory-evict] SKIP: memory DB credentials absent.", err=True)
        return

    from mj_agent.memory import open_checkpointer
    from mj_agent.memory.retention import EvictionResult, evict_stale_threads
    from mj_agent.runtime import run_async

    async def _run() -> EvictionResult:
        async with open_checkpointer() as saver:
            return await evict_stale_threads(
                saver,
                older_than_seconds=ttl_days * 86400,
                now_epoch=time.time(),
                dry_run=dry_run,
            )

    result = run_async(_run())
    if dry_run:
        typer.echo(
            f"[memory-evict] DRY-RUN: scanned {result.scanned_threads} thread(s); "
            f"{len(result.stale_thread_ids)} older than {ttl_days}d would be evicted "
            "(nothing deleted)."
        )
    else:
        typer.echo(
            f"[memory-evict] scanned {result.scanned_threads} thread(s); "
            f"evicted {result.evicted} older than {ttl_days}d."
        )


def main() -> None:
    # Ensure .env propagates to subprocess invocations of `chainlit run` —
    # chainlit re-imports ui.py in a child interpreter and re-evaluates
    # pydantic-settings, so the .env file must be discoverable from the
    # spawn cwd. We rely on user invoking from the project root; warn if
    # MJ_AGENT_DEBUG is on and .env is missing.
    if os.environ.get("MJ_AGENT_DEBUG") and not Path(".env").exists():
        typer.echo("[mj-agent] warning: .env not found in cwd", err=True)
    app()


if __name__ == "__main__":
    main()
