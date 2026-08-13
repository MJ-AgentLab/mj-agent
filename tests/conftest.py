# ruff: noqa: E402, I001
"""Shared pytest fixtures enforcing the repository-wide offline policy.

Human/IDE direct pytest and the hardened Agent/CI runner share this same
boundary.  Pytest never enables a live dependency because credentials happen
to be present.  Biz live legs are permanently unavailable here; non-biz live
legs require a future, separately Owner-approved profile.
"""

from __future__ import annotations

import os

# This assignment precedes imports from project conftests and test modules.
# The hardened runner separately disables third-party plugin autoload.
os.environ["MJ_AGENT_OFFLINE_TEST"] = "1"

import pytest  # noqa: E402

@pytest.fixture(scope="session")
def live_db() -> None:
    """Biz live legs are permanently unavailable to pytest."""
    pytest.skip(
        "SKIP_POLICY_EXTERNAL_DEPENDENCY: biz live legs are permanently unavailable to pytest"
    )


@pytest.fixture(scope="session")
def memory_db() -> None:
    """Skip the non-biz memory service until an approved profile exists."""
    pytest.skip(
        "SKIP_POLICY_EXTERNAL_DEPENDENCY: no Owner-approved non-biz pytest profile exists"
    )


@pytest.fixture(scope="session")
def agent() -> None:
    """Never construct an external-capable graph inside pytest."""
    pytest.skip(
        "SKIP_POLICY_EXTERNAL_DEPENDENCY: agent/LLM pytest legs require a future approved profile"
    )
