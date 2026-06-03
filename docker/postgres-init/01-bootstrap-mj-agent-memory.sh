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
#   MJ_AGENT_MEMORY_PASSWORD - app role password (any chars; see #144)
#
# Idempotent: creates role if missing, otherwise syncs LOGIN + PASSWORD
# on each run (PR #138). Safe to re-run if the bootstrap was previously
# interrupted. Note: postgres image only invokes this script when the
# data dir is empty (first boot); for password rotation on an existing
# volume see `config/README.md "Memory pg password rotation"`.
#
# Password char safety (#144): the heredoc below uses a **single-quoted
# delimiter** (<<-'EOSQL') to disable bash parameter / command / arith
# expansion on the SQL body. Env vars are loaded inside psql via
# `\getenv`, which reads the process env directly — values flow to
# pg literals via psql `:'var'` (and to identifiers via `:"var"`)
# without ever passing through a shell quoting layer. DDL statements
# (CREATE ROLE / ALTER ROLE / CREATE DATABASE) don't accept SQL
# parameters, so they're built with server-side `format('%I %L', ...)`
# and dispatched via `\gexec`. Net effect: passwords containing `$`,
# backticks, parens, single-quotes, spaces, or any other metachar
# round-trip safely.
set -euo pipefail

: "${POSTGRES_USER:?POSTGRES_USER missing — postgres image normally sets this}"
: "${MJ_AGENT_MEMORY_USER:?MJ_AGENT_MEMORY_USER missing — set it in compose env}"
: "${MJ_AGENT_MEMORY_PASSWORD:?MJ_AGENT_MEMORY_PASSWORD missing — set it in compose env}"
: "${MJ_AGENT_MEMORY_DB:=mj_agent_memory}"

# Export so psql `\getenv` (called inside the quoted heredoc below)
# can read them from the child process env. The `:=` above only sets
# bash-local state; without `export`, MJ_AGENT_MEMORY_DB wouldn't
# propagate to psql when the compose default isn't overridden.
export MJ_AGENT_MEMORY_DB MJ_AGENT_MEMORY_USER MJ_AGENT_MEMORY_PASSWORD

echo "[mj-agent-memory init] creating role + database..."

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-'EOSQL'
	-- Load env vars via psql \getenv (PG14+). The single-quoted heredoc
	-- delimiter above disables bash heredoc expansion entirely; psql
	-- reads env directly so the password value's shell metachars
	-- ($, backtick, parens, quotes) cannot be re-interpreted.
	\getenv mem_user MJ_AGENT_MEMORY_USER
	\getenv mem_pwd  MJ_AGENT_MEMORY_PASSWORD
	\getenv mem_db   MJ_AGENT_MEMORY_DB

	-- CREATE/ALTER ROLE accept no SQL parameters, so build the
	-- statement via server-side format() — %I auto-quotes identifier,
	-- %L auto-quotes literal (handles embedded quotes safely).
	SELECT format('CREATE ROLE %I LOGIN PASSWORD %L', :'mem_user', :'mem_pwd')
	WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'mem_user')
	\gexec

	-- ALTER branch keeps PR #138 idempotency: on volume reuse with a
	-- rotated MJ_AGENT_MEMORY_PASSWORD, sync the stored hash.
	SELECT format('ALTER ROLE %I WITH LOGIN PASSWORD %L', :'mem_user', :'mem_pwd')
	WHERE EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'mem_user')
	\gexec

	-- CREATE DATABASE also needs format() + \gexec. Default locale
	-- (en_US.utf8 inherited from postgres:18-alpine template) is fine
	-- for langgraph checkpoint payloads; switch to template0 + C
	-- collation later if performance tuning warrants.
	SELECT format('CREATE DATABASE %I OWNER %I', :'mem_db', :'mem_user')
	WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = :'mem_db')
	\gexec

	-- Grants (idempotent; :"var" quotes as SQL identifier).
	GRANT CONNECT ON DATABASE :"mem_db" TO :"mem_user";
	GRANT CREATE  ON DATABASE :"mem_db" TO :"mem_user";
EOSQL

echo "[mj-agent-memory init] done. langgraph AsyncPostgresSaver.setup() will create checkpoint tables on first agent run."
