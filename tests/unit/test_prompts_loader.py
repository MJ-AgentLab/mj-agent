"""Smoke tests for the packaged prompt/skill loaders."""

from __future__ import annotations

import pytest

from mj_agent.prompts import load_prompt
from mj_agent.skills import load_skill


def test_system_prompt_loads() -> None:
    text = load_prompt("system")
    assert "mj-agent" in text
    assert "P1" in text and "P2" in text and "P3" in text


def test_query_writing_skill_loads() -> None:
    text = load_skill("query-writing")
    assert "biz_dws" in text
    assert "execute_sql" in text


def test_missing_prompt_raises() -> None:
    with pytest.raises(FileNotFoundError):
        load_prompt("does-not-exist")


def test_missing_skill_raises() -> None:
    with pytest.raises(FileNotFoundError):
        load_skill("does-not-exist")
