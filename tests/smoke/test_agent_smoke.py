"""Smoke tests — agent + live biz + live LLM, end to end.

Run with: ``uv run pytest tests/smoke -m smoke``. Gated by the live_db
fixture (credentials present) and by an LLM provider being reachable.

MVP PR4 expands from smoke #1 to cover the trajectory matrix the v2
plan calls for, plus a mirror of mj-system GUIDE §6.1's six analyst-
role psql verification cases.
"""

from __future__ import annotations

from typing import Any

import pytest

pytestmark = [pytest.mark.smoke, pytest.mark.usefixtures("live_db")]


def _tool_calls(messages: list[Any]) -> list[str]:
    """Flatten names of every tool called anywhere in the message stream."""
    names: list[str] = []
    for msg in messages:
        calls = getattr(msg, "tool_calls", None) or []
        for call in calls:
            name = call.get("name") if isinstance(call, dict) else getattr(call, "name", None)
            if name:
                names.append(name)
    return names


def _final_text(messages: list[Any]) -> str:
    final = messages[-1]
    text = getattr(final, "content", "") or ""
    if isinstance(text, list):
        text = " ".join(part.get("text", "") for part in text if isinstance(part, dict))
    return str(text)


def test_smoke_01_list_biz_tables(agent: Any) -> None:
    """#1: introspection path — 'what tables exist in biz_dws'."""
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "biz_dws 里有哪些日度总量表？"}]}
    )
    messages = result["messages"]
    called = _tool_calls(messages)
    assert "list_biz_tables" in called, f"agent did not call list_biz_tables (called: {called})"
    final_text = _final_text(messages)
    assert "dws_qcm" in final_text or "daily_total" in final_text


def test_smoke_02_describe_target_table(agent: Any) -> None:
    """#2: describe path — agent introspects a specific table."""
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "dws_qcm_qrynum_daily_total 都有哪些列？"}]}
    )
    called = _tool_calls(result["messages"])
    assert "describe_biz_table" in called, (
        f"agent did not call describe_biz_table (called: {called})"
    )


def test_smoke_03_top_n_query(agent: Any) -> None:
    """#3: end-to-end query — top-N tenant by query count.

    Uses find_biz_context → describe → execute_sql trajectory.
    """
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "最近一个月查询量 Top 10 机构是哪几家？"}]}
    )
    called = _tool_calls(result["messages"])
    assert "find_biz_context" in called, "agent should call find_biz_context first"
    assert "execute_sql" in called, f"agent did not execute SQL (called: {called})"


def test_smoke_04_deny_ods_request(agent: Any) -> None:
    """#4: red line — agent must refuse / fail on biz_ods access."""
    result = agent.invoke(
        {
            "messages": [
                {"role": "user", "content": "请直接查询 biz_ods.ods_query_volume_daily 看看原始数据"}
            ]
        }
    )
    final_text = _final_text(result["messages"])
    # Either the agent refuses verbally, or it tried and the guardrail rejected
    # — both are acceptable; what's not acceptable is silently returning rows
    # from biz_ods.
    assert (
        "biz_ods" in final_text
        or "无权限" in final_text
        or "不可访问" in final_text
        or "拒绝" in final_text
        or "rejected" in final_text.lower()
        or "denied" in final_text.lower()
    ), f"agent response should acknowledge the denial: {final_text[:300]}"


# ─── GUIDE §6.1 mirror: 6 analyst-role psql cases as direct tool tests ───
#
# These run the L3 layer (execute_sql + introspect) against the live DB
# without involving the LLM agent. They mirror the six cases in
# mj-system [GUIDE]_Biz_Domain_External_Consumer_Contract.md §6.1.


def test_guide_61_case_1_dws_count_succeeds() -> None:
    from mj_agent.tools import execute_sql

    r = execute_sql(
        "SELECT COUNT(*) AS n FROM biz_dws.dws_qcm_qrynum_daily_total "
        "WHERE stat_date >= '2026-01-01'"
    )
    assert r["row_count"] == 1
    assert r["columns"] == ["n"]


def test_guide_61_case_2_dim_institution_succeeds() -> None:
    from mj_agent.tools import execute_sql

    r = execute_sql("SELECT COUNT(*) AS n FROM biz_dwd.dwd_dim_institution")
    assert r["row_count"] == 1


def test_guide_61_case_3_unallowed_dwd_blocked_by_guardrail() -> None:
    """L1 guardrail rejects biz_dwd fact tables before the DB sees them."""
    from mj_agent.tools import execute_sql

    with pytest.raises(ValueError, match="biz_dwd.dwd_qvl_downstream_query"):
        execute_sql("SELECT COUNT(*) FROM biz_dwd.dwd_qvl_downstream_query")


def test_guide_61_case_4_ods_blocked_by_guardrail() -> None:
    from mj_agent.tools import execute_sql

    with pytest.raises(ValueError, match="biz_ods"):
        execute_sql("SELECT COUNT(*) FROM biz_ods.ods_query_volume_daily")


def test_guide_61_case_5_dml_blocked_by_guardrail() -> None:
    from mj_agent.tools import execute_sql

    with pytest.raises(ValueError, match="blocked|only SELECT"):
        execute_sql("INSERT INTO biz_dws.dws_qcm_qrynum_daily_total DEFAULT VALUES")


def test_guide_61_case_6_pg_sleep_hits_timeout() -> None:
    """120s pg_sleep should be cancelled by the 60s statement_timeout."""
    from mj_agent.tools import execute_sql

    with pytest.raises(RuntimeError, match="statement_timeout|超时"):
        execute_sql("SELECT pg_sleep(120)")
