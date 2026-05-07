#!/usr/bin/env bash
# entrypoint.sh — mj-agent container entry
#
# Subcommand router (vs hardcoding `mj-agent serve`):
#   serve   - default: Chainlit UI on $CHAINLIT_HOST:$CHAINLIT_PORT (0.0.0.0:8000)
#   check   - one-shot health probe (DB + Ark + memory DB); exit code = healthcheck result
#   shell   - drop into bash (debugging only)
#   *       - passthrough: `docker run mj-agent uv run pytest tests/unit` works
#
# Secrets: this script does NOT decrypt config/secrets.enc — Docker containers
# get secrets via env-file / Compose env / Portainer Stack vars / Docker secrets
# (handled by orchestrator). For local dev, use `setup-env.ps1` then
# `--env-file .env`.
set -Eeuo pipefail

cmd="${1:-serve}"

case "$cmd" in
  serve)
    shift || true
    # Pass through any extra args (e.g. --host override).
    exec mj-agent serve "$@"
    ;;
  check)
    shift || true
    exec mj-agent check "$@"
    ;;
  shell)
    exec /bin/bash
    ;;
  *)
    # Run arbitrary commands (pytest, ruff, mypy in CI-on-image flow).
    exec "$@"
    ;;
esac
