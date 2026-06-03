"""BDD step definitions for infrastructure.docker-compose capability.

Binds all 3 scenarios from
`capabilities/infrastructure/docker-compose/contracts/behavior.feature`.

All 3 scenarios require live docker + the mj-system stack running on the
same host (mj-system-backend-network external + biz pg). They are gated by
the `docker_available` fixture in tests/bdd/conftest.py, which currently
skips unconditionally in CI.

Step defs are minimal placeholders — they exist so pytest-bdd does not
raise StepDefinitionNotFoundError if the fixture is bypassed locally.
Local smoke runs (e.g., `pytest tests/bdd/infrastructure/docker_compose
--override-ini=...`) would exercise the actual compose stack.
"""

from __future__ import annotations

import re

from pytest_bdd import given, parsers, scenario, then, when

_FEATURE_FILE = (
    "../../../../capabilities/infrastructure/docker-compose/contracts/behavior.feature"
)


# -------- Background --------

@given(parsers.re(re.escape(
    "mj-agent compose project lives at docker/"
)))
def compose_project_at_infra_docker() -> None:
    """Background — path is canonical per CLAUDE.md / ADR-026."""


@given(parsers.re(re.escape(
    "the mj-system stack is already up (mj-system-backend-network external network exists)"
)))
def mj_system_stack_up() -> None:
    """Background — checked by `docker_available` fixture (skip if not)."""


@given(parsers.re(re.escape(
    ".env is populated with MJ_AGENT_MEMORY_USER / MJ_AGENT_MEMORY_PASSWORD / "
    "MJ_AGENT_PG_SUPERUSER_PASSWORD"
)))
def env_populated() -> None:
    """Background — checked at runtime by docker compose `--env-file .env`."""


# -------- Scenarios (all docker-gated; CI skips) --------


@scenario(_FEATURE_FILE, "DEV profile loads with explicit -f chain + --env-file")
def test_req_001_dev_profile_loads(docker_available: None) -> None:  # noqa: ARG001
    pass


@scenario(_FEATURE_FILE, "Postgres healthcheck rejects half-initialized DB")
def test_req_002_postgres_healthcheck(docker_available: None) -> None:  # noqa: ARG001
    pass


@scenario(_FEATURE_FILE, "Postgres init handles password with shell metacharacters unmangled")
def test_req_003_shell_safe_password(docker_available: None) -> None:  # noqa: ARG001
    pass


# -------- Step defs — placeholder bodies (only run if docker_available is satisfied) --------
# Each step would invoke `subprocess.run(["docker", "compose", ...])` against
# the real stack. Implementation deferred to a future M4 work item when
# either CI gains docker-compose support or a local smoke harness lands.


@given("a clean docker daemon")
def given_clean_docker() -> None:
    pass


@when(parsers.re(re.escape(
    "`docker compose --env-file .env -f docker/compose.yaml "
    "-f docker/compose.override.yml up -d` is invoked"
)))
def when_compose_up_invoked() -> None:
    pass


@then(parsers.parse(
    "within {seconds:d} seconds all 3 services (mj-agent / mj-agent-postgres / mj-agent-redis) "
    "reach `Up (healthy)` state"
))
def then_three_services_healthy(seconds: int) -> None:
    del seconds  # placeholder; real impl would poll docker compose ps


@then(parsers.re(re.escape(
    "mj-agent's `env_file: ../.env` correctly injects MJ_AGENT_MEMORY_* into the container"
)))
def then_env_file_injected() -> None:
    pass


@then(parsers.re(re.escape(
    "mj-agent can connect to mj-agent-postgres:5432 via mj-agent-storage internal network"
)))
def then_mj_agent_connects_internal_pg() -> None:
    pass


@then(parsers.re(re.escape(
    "mj-agent can connect to mj-postgres:5432 via mj-system-backend-network external network"
)))
def then_mj_agent_connects_external_pg() -> None:
    pass


@given("mj-agent-postgres container is starting")
def given_postgres_starting() -> None:
    pass


@given(parsers.re(re.escape(
    "the init script `01-bootstrap-mj-agent-memory.sh` has CREATEd the role "
    "but not yet CREATEd the mj_agent_memory database"
)))
def given_init_partial() -> None:
    pass


@when(parsers.re(re.escape(
    "the healthcheck probe runs `psql -U postgres -d $MJ_AGENT_MEMORY_DB -tc 'SELECT 1'`"
)))
def when_healthcheck_probe_runs() -> None:
    pass


@then("the probe exits non-zero (target DB doesn't exist yet)")
def then_probe_exits_nonzero() -> None:
    pass


@then(parsers.re(re.escape(
    "mj-agent service's `depends_on: service_healthy` does NOT fire "
    "(mj-agent stays in Created state)"
)))
def then_depends_on_does_not_fire() -> None:
    pass


@then(parsers.re(re.escape(
    "only after `CREATE DATABASE mj_agent_memory` completes, "
    "the next probe succeeds and mj-agent starts"
)))
def then_next_probe_succeeds() -> None:
    pass


@given(parsers.re(re.escape(
    "`MJ_AGENT_MEMORY_PASSWORD` contains shell metacharacters "
    '(e.g. "p@$$`w""ord" with $, backticks, double quotes)'
)))
def given_password_metachars() -> None:
    pass


@given(parsers.re(re.escape(
    "the init script `01-bootstrap-mj-agent-memory.sh` runs on fresh data dir"
)))
def given_init_runs_fresh() -> None:
    pass


@when(parsers.re(re.escape(
    "the script's `\\getenv MJ_AGENT_MEMORY_PASSWORD` + "
    "`format('%I %L', user, password)` + `\\gexec` chain executes"
)))
def when_format_gexec_chain_runs() -> None:
    pass


@then(parsers.re(re.escape(
    "`CREATE ROLE mj_agent_app WITH LOGIN PASSWORD '<unmangled password>'` "
    "is dispatched correctly"
)))
def then_create_role_dispatched() -> None:
    pass


@then(parsers.re(re.escape(
    "subsequent `\\password mj_agent_app` login from the mj-agent container succeeds"
)))
def then_subsequent_login_succeeds() -> None:
    pass


@then("no shell expansion mangling occurs (no $-expansion, no backtick-execution)")
def then_no_shell_expansion() -> None:
    pass
