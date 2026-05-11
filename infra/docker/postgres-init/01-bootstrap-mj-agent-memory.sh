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
# Idempotent: creates role if missing, otherwise syncs LOGIN + PASSWORD
# from env on each run. Safe to re-run if the bootstrap was previously
# interrupted. Note: postgres image only invokes this script when the
# data dir is empty (first boot); for password rotation on an existing
# volume see `config/README.md "Memory pg password rotation"`.
set -euo pipefail

: "${POSTGRES_USER:?POSTGRES_USER missing — postgres image normally sets this}"
: "${MJ_AGENT_MEMORY_DB:=mj_agent_memory}"
: "${MJ_AGENT_MEMORY_USER:?MJ_AGENT_MEMORY_USER missing — set it in compose env}"
: "${MJ_AGENT_MEMORY_PASSWORD:?MJ_AGENT_MEMORY_PASSWORD missing — set it in compose env}"

echo "[mj-agent-memory init] creating role + database..."

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    -- Create the application role, or sync its LOGIN + password if it exists.
    -- The ALTER branch makes the script idempotent for state (not just for
    -- existence) — needed when `MJ_AGENT_MEMORY_PASSWORD` is rotated and
    -- the volume gets wiped + re-initialized on a later boot.
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '${MJ_AGENT_MEMORY_USER}') THEN
            CREATE ROLE "${MJ_AGENT_MEMORY_USER}" LOGIN PASSWORD '${MJ_AGENT_MEMORY_PASSWORD}';
        ELSE
            ALTER ROLE "${MJ_AGENT_MEMORY_USER}" WITH LOGIN PASSWORD '${MJ_AGENT_MEMORY_PASSWORD}';
        END IF;
    END
    \$\$;

    -- Create the database if it doesn't exist (CREATE DATABASE can't run in DO; check first).
    -- Storage-stack hotfix: drop LC_COLLATE/LC_CTYPE specifiers — they conflicted
    -- with the default postgres:16-alpine template (en_US.utf8). The default locale
    -- is fine for langgraph checkpoint payloads; switch to TEMPLATE template0 + C
    -- collation later if performance tuning warrants.
    SELECT 'CREATE DATABASE "${MJ_AGENT_MEMORY_DB}" OWNER "${MJ_AGENT_MEMORY_USER}"'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${MJ_AGENT_MEMORY_DB}')\\gexec

    -- Grants (idempotent).
    GRANT CONNECT ON DATABASE "${MJ_AGENT_MEMORY_DB}" TO "${MJ_AGENT_MEMORY_USER}";
    GRANT CREATE  ON DATABASE "${MJ_AGENT_MEMORY_DB}" TO "${MJ_AGENT_MEMORY_USER}";
EOSQL

echo "[mj-agent-memory init] done. langgraph AsyncPostgresSaver.setup() will create checkpoint tables on first agent run."
