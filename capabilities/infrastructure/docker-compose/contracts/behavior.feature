# capabilities/infrastructure/docker-compose/contracts/behavior.feature
#
# 3 @risk:high scenarios (REQ-001 / REQ-002 / REQ-003).

@adapter:docker-container
Feature: Docker Compose 4-File Profile + Healthcheck + Secret Safety
  As an mj-agent operator
  I want DEV/TEST/PROD profiles to layer correctly + postgres healthcheck to
  catch half-initialized state + secrets to never bake into the image
  So that compose up reliably produces a healthy stack with isolated credentials

  Background:
    Given mj-agent compose project lives at docker/
    And the mj-system stack is already up (mj-system-backend-network external network exists)
    And .env is populated with MJ_AGENT_MEMORY_USER / MJ_AGENT_MEMORY_PASSWORD / MJ_AGENT_PG_SUPERUSER_PASSWORD

  # ---------- REQ-001 — 4-file profile loading + explicit --env-file ----------

  @REQ-001 @CTR-compose @risk:high @adapter:docker-container @adr:ADR-026
  Scenario: DEV profile loads with explicit -f chain + --env-file
    Given a clean docker daemon
    When `docker compose --env-file .env -f docker/compose.yaml -f docker/compose.override.yml up -d` is invoked
    Then within 90 seconds all 3 services (mj-agent / mj-agent-postgres / mj-agent-redis) reach `Up (healthy)` state
    And mj-agent's `env_file: ../.env` correctly injects MJ_AGENT_MEMORY_* into the container
    And mj-agent can connect to mj-agent-postgres:5432 via mj-agent-storage internal network
    And mj-agent can connect to mj-postgres:5432 via mj-system-backend-network external network

  # ---------- REQ-002 — Healthcheck + startup order ----------

  @REQ-002 @CTR-compose @risk:high @adapter:docker-container
  Scenario: Postgres healthcheck rejects half-initialized DB
    Given mj-agent-postgres container is starting
    And the init script `01-bootstrap-mj-agent-memory.sh` has CREATEd the role but not yet CREATEd the mj_agent_memory database
    When the healthcheck probe runs `psql -U postgres -d $MJ_AGENT_MEMORY_DB -tc 'SELECT 1'`
    Then the probe exits non-zero (target DB doesn't exist yet)
    And mj-agent service's `depends_on: service_healthy` does NOT fire (mj-agent stays in Created state)
    And only after `CREATE DATABASE mj_agent_memory` completes, the next probe succeeds and mj-agent starts

  # ---------- REQ-003 — Secrets not exposed; shell-safe init ----------

  @REQ-003 @CTR-docker @CTR-compose @risk:high @adapter:docker-container @adr:ADR-030
  Scenario: Postgres init handles password with shell metacharacters unmangled
    Given `MJ_AGENT_MEMORY_PASSWORD` contains shell metacharacters (e.g. "p@$$`w\"\"ord" with $, backticks, double quotes)
    And the init script `01-bootstrap-mj-agent-memory.sh` runs on fresh data dir
    When the script's `\getenv MJ_AGENT_MEMORY_PASSWORD` + `format('%I %L', user, password)` + `\gexec` chain executes
    Then `CREATE ROLE mj_agent_app WITH LOGIN PASSWORD '<unmangled password>'` is dispatched correctly
    And subsequent `\password mj_agent_app` login from the mj-agent container succeeds
    And no shell expansion mangling occurs (no $-expansion, no backtick-execution)

# Gherkin tag convention:
#   @REQ-NNN @CTR-<slug> @risk:high @adapter:docker-container @adr:ADR-NNN
# Step definitions: Phase M3 lands tests/bdd/infrastructure/docker_compose/steps/.
# Tests gated on @docker fixture (skip-clean without docker daemon).
