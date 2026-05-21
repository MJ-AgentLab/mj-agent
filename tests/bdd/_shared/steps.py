"""tests/bdd/_shared/steps.py — placeholder for cross-capability helper utilities.

Phase M3 Stage B (kickoff). Currently empty — shared Gherkin step
definitions live in `tests/bdd/conftest.py` (pytest-bdd's canonical
discovery path: parent-directory conftest.py auto-applies to all child
tests).

This module is reserved for cross-capability PYTHON helper functions
(e.g., factories for synthetic SQL, common fixtures) that are imported
by capability tests as ordinary utilities — not for @given/@when/@then
step defs, which must live in conftest.py to be discovered.
"""

from __future__ import annotations
