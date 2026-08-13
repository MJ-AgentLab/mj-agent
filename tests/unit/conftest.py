"""Unit-band fixtures (issue #298).

Scoped to ``tests/unit/`` — merges with the root ``tests/conftest.py`` rather
than replacing it.
"""

from __future__ import annotations

import pytest

from mj_agent.config import Settings


@pytest.fixture
def isolated_settings(monkeypatch: pytest.MonkeyPatch) -> Settings:
    """A ``Settings`` isolated from filesystem sources and mapped OS variables.

    The root conftest activates the Settings construction seam, which disables
    dotenv and secrets-directory sources before pydantic builds them. Pydantic
    intentionally still reads OS variables, so this fixture also clears every
    model-mapped name before asserting defaults. ``monkeypatch`` restores the
    process environment at teardown.
    """
    for field_name in Settings.model_fields:
        monkeypatch.delenv(field_name.upper(), raising=False)
    return Settings()
