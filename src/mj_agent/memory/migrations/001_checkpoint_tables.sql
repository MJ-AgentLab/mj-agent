-- 001_checkpoint_tables.sql
--
-- Reference DDL for the LangGraph PostgresSaver checkpoint tables.
-- The actual tables are created **at runtime** by
-- ``PostgresSaver.setup()`` (called from ``open_checkpointer()``);
-- this file exists for ops / DBA review and as a quick visualization
-- of the schema langgraph owns.
--
-- Source: langgraph 1.1.x — see
-- ``langgraph.checkpoint.postgres.base.BasePostgresSaver.MIGRATIONS``.
-- If langgraph upgrades the schema, the runtime ``setup()`` will apply
-- the delta; this file should be re-synced manually as a doc artifact.
--
-- DBA pre-flight (Phase 1 sub 1.A; storage-stack PR makes this auto):
--   * Docker co-deploy: the storage-stack PR ships
--     ``infra/docker/postgres-init/01-bootstrap-mj-agent-memory.sh`` which
--     runs on the dedicated ``mj-agent-postgres`` container's first init
--     and performs the CREATE ROLE + CREATE DATABASE + GRANT below
--     automatically. Just set MJ_AGENT_MEMORY_USER / MJ_AGENT_MEMORY_PASSWORD
--     in .env before the first ``docker compose up``.
--   * Non-Docker dev (you point MJ_AGENT_MEMORY_HOST at any postgres you
--     already own): run the SQL block below manually as a super-user.
--
-- Manual bootstrap (non-Docker only):
--   1. Create the database:
--        CREATE DATABASE mj_agent_memory ENCODING 'UTF8' LC_COLLATE 'C' LC_CTYPE 'C';
--   2. Create a read-write role distinct from the biz-domain ``analyst`` role:
--        CREATE ROLE mj_agent_memory LOGIN PASSWORD '<see secrets store>';
--        GRANT CONNECT ON DATABASE mj_agent_memory TO mj_agent_memory;
--        GRANT CREATE ON DATABASE mj_agent_memory TO mj_agent_memory;
--   3. Connect as that role; on first ``open_checkpointer()`` the tables
--      below will be created automatically.
--
-- Tables created by langgraph (read-only reference):

-- checkpoint_migrations: tracks schema migrations applied by langgraph
CREATE TABLE IF NOT EXISTS checkpoint_migrations (
    v INTEGER PRIMARY KEY
);

-- checkpoints: one row per (thread, checkpoint_ns, checkpoint_id)
CREATE TABLE IF NOT EXISTS checkpoints (
    thread_id     TEXT     NOT NULL,
    checkpoint_ns TEXT     NOT NULL DEFAULT '',
    checkpoint_id TEXT     NOT NULL,
    parent_checkpoint_id TEXT,
    type          TEXT,
    checkpoint    JSONB    NOT NULL,
    metadata      JSONB    NOT NULL DEFAULT '{}',
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
);

-- checkpoint_blobs: large object storage for checkpoint payloads
CREATE TABLE IF NOT EXISTS checkpoint_blobs (
    thread_id     TEXT     NOT NULL,
    checkpoint_ns TEXT     NOT NULL DEFAULT '',
    channel       TEXT     NOT NULL,
    version       TEXT     NOT NULL,
    type          TEXT     NOT NULL,
    blob          BYTEA,
    PRIMARY KEY (thread_id, checkpoint_ns, channel, version)
);

-- checkpoint_writes: pending writes between checkpoints
CREATE TABLE IF NOT EXISTS checkpoint_writes (
    thread_id     TEXT     NOT NULL,
    checkpoint_ns TEXT     NOT NULL DEFAULT '',
    checkpoint_id TEXT     NOT NULL,
    task_id       TEXT     NOT NULL,
    idx           INTEGER  NOT NULL,
    channel       TEXT     NOT NULL,
    type          TEXT,
    blob          BYTEA    NOT NULL,
    task_path     TEXT     NOT NULL DEFAULT '',
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, idx)
);
