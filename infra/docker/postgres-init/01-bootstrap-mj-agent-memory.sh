#!/bin/bash
# postgres-init/01-bootstrap-mj-agent-memory.sh
#
# Auto-run by the official postgres image on **first** initialization
# (when /var/lib/postgresql/data is empty). Once the data dir exists,
# this script is skipped — re-running needs the volume to be wiped.
#
# Bootstraps mj_agent_memory DB + role from env vars supplied by
# docker-compose.mj-agent.yml:
#
#   POSTGRES_USER          - super user (postgres) used by this script
#   POSTGRES_PASSWORD      - super user password
#   MJ_AGENT_MEMORY_DB     - target DB name
#   MJ_AGENT_MEMORY_USER   - app role
#   MJ_AGENT_MEMORY_PASSWORD - app role password
#
# Idempotent: each statement is wrapped in DO blocks that no-op if the
# object already exists. Safe to re-run if the volume is preserved but
# the bootstrap was previously interrupted.
set -euo pipefail

: "${POSTGRES_USER:?POSTGRES_USER missing — postgres image normally sets this}"
: "${MJ_AGENT_MEMORY_DB:=mj_agent_memory}"
: "${MJ_AGENT_MEMORY_USER:?MJ_AGENT_MEMORY_USER missing — set it in compose env}"
: "${MJ_AGENT_MEMORY_PASSWORD:?MJ_AGENT_MEMORY_PASSWORD missing — set it in compose env}"

echo "[mj-agent-memory init] creating role + database..."

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    -- Create the application role if it doesn't exist.
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '${MJ_AGENT_MEMORY_USER}') THEN
            CREATE ROLE "${MJ_AGENT_MEMORY_USER}" LOGIN PASSWORD '${MJ_AGENT_MEMORY_PASSWORD}';
        END IF;
    END
    \$\$;

    -- Create the database if it doesn't exist (CREATE DATABASE can't run in DO; check first).
    SELECT 'CREATE DATABASE "${MJ_AGENT_MEMORY_DB}" ENCODING ''UTF8'' LC_COLLATE ''C'' LC_CTYPE ''C'' OWNER "${MJ_AGENT_MEMORY_USER}"'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${MJ_AGENT_MEMORY_DB}')\\gexec

    -- Grants (idempotent).
    GRANT CONNECT ON DATABASE "${MJ_AGENT_MEMORY_DB}" TO "${MJ_AGENT_MEMORY_USER}";
    GRANT CREATE  ON DATABASE "${MJ_AGENT_MEMORY_DB}" TO "${MJ_AGENT_MEMORY_USER}";
EOSQL

echo "[mj-agent-memory init] done. langgraph PostgresSaver.setup() will create checkpoint tables on first agent run."
