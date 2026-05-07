"""``mj-agent`` CLI — typer-based wrapper around the runtime entrypoints.

Two commands so far (Phase 1 sub 1.A):

  - ``mj-agent serve``  — launch the Chainlit UI on the configured host/port
  - ``mj-agent check``  — health probe: imports + biz DB + memory DB + LLM key

Each command is intentionally thin; the heavy lifting lives in the
modules it imports lazily (so ``mj-agent --help`` works without a live
DB or ARK key).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import typer

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


@app.command("check")
def check() -> None:
    """Health probe — verify imports + DB / LLM credentials.

    Exit code 0 on full pass; non-zero on any failure (with reason on
    stderr). Suitable for Docker ``HEALTHCHECK`` later (Phase 1 sub 1.H).
    """
    failures: list[str] = []

    try:
        from mj_agent.config import settings
    except Exception as exc:  # noqa: BLE001
        typer.echo(f"FAIL config: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    if not settings.postgres_analyst_user:
        failures.append("POSTGRES_ANALYST_USER not set")
    if not settings.ark_api_key.get_secret_value():
        failures.append("ARK_API_KEY not set")
    if not settings.mj_agent_memory_user:
        failures.append("MJ_AGENT_MEMORY_USER not set")

    # Memory DB ping (best-effort; skip if creds absent so users can run
    # `check` to discover what's missing).
    if settings.mj_agent_memory_user and settings.mj_agent_memory_password.get_secret_value():
        try:
            import psycopg

            from mj_agent.memory import memory_conn_string

            with psycopg.connect(memory_conn_string(), connect_timeout=5) as conn:
                conn.execute("SELECT 1")
        except Exception as exc:  # noqa: BLE001
            failures.append(f"memory DB unreachable: {exc}")

    if failures:
        typer.echo("CHECK FAILED:", err=True)
        for f in failures:
            typer.echo(f"  - {f}", err=True)
        raise typer.Exit(code=1)

    typer.echo("CHECK OK")
    typer.echo(f"  profile = {settings.mj_config_profile}")
    typer.echo(f"  biz host = {settings.biz_pg_host}:{settings.biz_pg_port}")
    typer.echo(f"  memory db = {settings.mj_agent_memory_db}")
    typer.echo(f"  chainlit  = {settings.chainlit_host}:{settings.chainlit_port}")
    typer.echo(f"  langsmith = tracing={settings.langsmith_tracing}")


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
