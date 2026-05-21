"""tests/bdd/conftest.py — pytest-bdd shared configuration + Background step defs.

Phase M3 Stage B (kickoff).

pytest-bdd 8.x discovers step defs from the same test module or from
conftest.py at any parent directory level. Per-module imports of step
functions do NOT register them (unlike pytest fixtures). To share step
defs across capabilities, they MUST live here in tests/bdd/conftest.py.

Capability-local step defs live in each test file under
tests/bdd/<domain>/<capability>/.
"""

from __future__ import annotations

import re

from pytest_bdd import given, parsers, then

# -------- Background no-op context steps (descriptive only) --------
#
# These steps document precondition state implicit in test setup (Settings
# defaults, upstream GRANTs, catalog YAML). They are no-op step defs so
# pytest-bdd does not raise StepDefinitionNotFoundError.
#
# Gherkin lines with literal `{}` / `[]` / quotes use parsers.re() with
# re.escape() to avoid pytest-bdd 8.x interpreting them as placeholders.

@given(parsers.re(re.escape(
    "the analyst has read-only PostgreSQL grants on biz_dws.* + biz_dwd."
    "{dwd_dim_product_interface, dwd_dim_institution}"
)))
def analyst_grants() -> None:
    """Background — upstream mj-system GRANTs (live in R__analyst_permissions.sql)."""


@given(parsers.re(re.escape(
    'mj-agent is configured with biz_allowed_schemas = ["biz_dws", "biz_dwd"]'
)))
def biz_allowed_schemas_configured() -> None:
    """Background — biz_allowed_schemas is a Settings field default."""


@given(parsers.re(re.escape(
    'mj-agent is configured with biz_allowed_dwd_tables = '
    '["dwd_dim_product_interface", "dwd_dim_institution"]'
)))
def biz_allowed_dwd_tables_configured() -> None:
    """Background — biz_allowed_dwd_tables is a Settings field default."""


@given(parsers.re(re.escape(
    'qcm_catalog.yaml periods.*.time_column includes "data_date" and "month"'
)))
def qcm_catalog_time_columns() -> None:
    """Background — catalog YAML lives at src/mj_agent/biz_catalog/qcm_catalog.yaml."""


# -------- Shared assertion helpers --------

@then(parsers.parse('the message contains the blocked keyword name "{keyword}"'))
def assert_message_contains_blocked_keyword(raised_exception: BaseException, keyword: str) -> None:
    assert keyword in str(raised_exception), f"expected {keyword!r} in {raised_exception!r}"


@then(parsers.parse('the message contains "{substring}"'))
def assert_message_contains(raised_exception: BaseException, substring: str) -> None:
    assert substring in str(raised_exception), f"expected {substring!r} in {raised_exception!r}"
