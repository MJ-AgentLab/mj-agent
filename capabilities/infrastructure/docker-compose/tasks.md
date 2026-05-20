---
type: capability-tasks
capability: infrastructure.docker-compose
state: drafting
version: 0.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-05-20
---

# Tasks: Docker Compose 4-File Profile

> Phase M1 baseline. No existing pytest tests for docker layer — all TBD-M3.

## Backlog

### T-001 — Phase M1 capability artifact suite
- **Phase**：M1 / **Priority**：critical (meta) / **Linked REQ**：N/A
- **Status**：in-progress

### T-002 — REQ-001 4-file profile loading + --env-file
- **Phase**：M1 (contract) / M3 (tests)
- **Priority**：high / **Linked REQ**：REQ-001
- **Contract changed?**：no
- **HITL trigger**：prod compose modification → policies/docker-runtime.md §4 HITL
- **Status**：done (M1 contract); TBD-M3 tests
- **TDD test_list**：
  - **TBD-M3** `tests/docker/test_compose_config_dev.py::test_dev_profile_config_valid` — `docker compose --env-file .env -f base -f override config` exits 0; structural assertions
  - **TBD-M3** `tests/docker/test_compose_config_test.py::test_test_profile_config_valid`
  - **TBD-M3** `tests/docker/test_compose_config_prod.py::test_prod_profile_config_valid`
  - **TBD-M3** `tests/docker/test_external_network_required.py::test_compose_up_fails_without_mj_system_network` — assert clear error if external network absent
  - **TBD-M3** `tests/docker/test_env_file_required.py::test_compose_without_env_file_substitutes_sentinel` — assert sentinel password substituted when --env-file omitted

### T-003 — REQ-002 healthcheck + startup order
- **Phase**：M1 (contract) / M3 (tests)
- **Priority**：high / **Linked REQ**：REQ-002
- **Contract changed?**：no
- **HITL trigger**：none (testing layer)
- **Status**：done (M1 contract); TBD-M3 tests
- **TDD test_list**：
  - **TBD-M3** `tests/docker/test_postgres_healthcheck_timing.py::test_psql_healthcheck_rejects_pre_database_state` — spin up postgres with empty data dir; assert healthcheck fails until CREATE DATABASE completes
  - **TBD-M3** `tests/docker/test_postgres_healthcheck_timing.py::test_pg_isready_would_greenlight_too_early` — historical regression test; documents why we use psql not pg_isready
  - **TBD-M3** `tests/docker/test_depends_on_service_healthy.py::test_mj_agent_waits_for_postgres_database_created`
  - **TBD-M3** `tests/docker/test_redis_healthcheck_auth_branch.py::test_redis_healthcheck_with_password_set`
  - **TBD-M3** `tests/docker/test_redis_healthcheck_auth_branch.py::test_redis_healthcheck_without_password`

### T-004 — REQ-003 secrets not in image + shell-safe init
- **Phase**：M1 (contract) / M3 (tests)
- **Priority**：high / **Linked REQ**：REQ-003
- **Contract changed?**：no
- **HITL trigger**：secrets / GRANT / cross-cap to data-boundary policy
- **Status**：done (M1 contract); TBD-M3 tests
- **TDD test_list**：
  - **TBD-M3** `tests/docker/test_dockerfile_lint.py::test_no_secret_paths_in_copy` — scan Dockerfile for `COPY` of `.env` / `secrets.enc` / etc.
  - **TBD-M3** `tests/docker/test_dockerfile_lint.py::test_user_appuser_non_root` — assert USER directive sets non-root
  - **TBD-M3** `tests/docker/test_dockerfile_lint.py::test_no_arg_with_sensitive_default` — no ARG with API_KEY-like default
  - **TBD-M3** `tests/docker/test_password_special_chars.py::test_role_creation_with_dollar_in_password`
  - **TBD-M3** `tests/docker/test_password_special_chars.py::test_role_creation_with_backtick`
  - **TBD-M3** `tests/docker/test_password_special_chars.py::test_role_creation_with_double_quote`
  - **TBD-M3** `tests/docker/test_password_special_chars.py::test_role_creation_with_paren_and_space`

### T-005 — Phase M5 path migration: infra/docker/ → docker/
- **Phase**：M5
- **Priority**：medium
- **Linked REQ**：N/A (path-only refactor)
- **HITL trigger**：大规模目录迁移 (≥ 10 文件 — Dockerfile + 4 compose + entrypoint + postgres-init)
- **Status**：TBD-M5
- **Description**：Per ADR-026 phase 6 plan; relocate `infra/docker/` to `docker/`. Update all path refs (CLAUDE.md / mj-agent-infra-* skills / capabilities/infrastructure/docker-compose/contracts/*). Symlink for 1 week grace.

## In-Progress
(none beyond T-001)

## Anti-Backlog
- **Replace 4-file overlay with single compose + profiles** — rejected per design §4 tradeoff B
- **Add `--env-file` enforcement script** — informational only at M1; M4 evidence/runtime/ might surface drift
- **Move compose to repo root** — rejected per design §4 tradeoff E (mj-agent must be self-contained; ADR-008)

---

> Phase M1 baseline. 17 TBD-M3 test entries across REQ-001/002/003.
