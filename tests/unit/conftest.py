"""Unit-band fixtures (issue #298).

Scoped to ``tests/unit/`` — merges with the root ``tests/conftest.py`` rather
than replacing it.
"""

from __future__ import annotations

import pytest

from mj_agent.config import Settings


@pytest.fixture
def isolated_settings(monkeypatch: pytest.MonkeyPatch) -> Settings:
    """A ``Settings`` isolated from BOTH the ``.env`` file and ``os.environ``.

    Why this exists (issue #298): the root ``tests/conftest.py`` loads a
    developer's real ``.env`` into ``os.environ`` (``load_dotenv(..., override=
    False)``) so integration / smoke skip-gates see provisioned credentials.
    ``Settings(_env_file=None)`` opts out of the ``.env`` *file*, but
    pydantic-settings still reads ``os.environ`` — so a bare ``Settings(
    _env_file=None)`` silently inherits those leaked values on any configured
    dev machine. That is exactly what made
    ``test_cli_check_reports_missing_env`` (leaked ``LLM_API_KEY``) and
    ``test_check_live_all_creds_absent_skips_all_probes`` (leaked
    ``LLM_PROVIDER`` / ``LLM_BASE_URL``) false-fail locally while passing in CI
    (which has no ``.env``).

    Deleting the *whole* env surface Settings maps (every model field →
    ``UPPER``) before constructing keeps credential-absence tests hermetic
    regardless of ``.env`` / shell state, and stays correct as new fields are
    added — no per-key whack-a-mole delenv list to keep in sync. ``monkeypatch``
    reverts the deletions at test teardown, so no other test is affected.
    """
    for field_name in Settings.model_fields:
        monkeypatch.delenv(field_name.upper(), raising=False)
    return Settings(_env_file=None)
