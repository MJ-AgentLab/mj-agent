"""BDD step definitions for infrastructure.mcp-server-governance capability.

Binds 2 scenarios from
`capabilities/infrastructure/mcp-server-governance/contracts/behavior.feature`:

- REQ-001 Adding a 14th MCP server triggers A14 PR gate body declaration —
  this is a META gate (PR review process), not a runtime SUT behaviour.
  Binding emits a structural assertion: A14 template section exists in the
  governance STANDARD, and current .mcp.json has the expected 13 entries.

- REQ-002 All 10 pg-* entries reference the same wrapper script — direct
  static check on .mcp.json content (no live MCP server needed).

Both OFFLINE (file-only).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pytest_bdd import given, parsers, scenario, then, when

_FEATURE_FILE = (
    "../../../../capabilities/infrastructure/mcp-server-governance/contracts/behavior.feature"
)

_REPO_ROOT = Path(__file__).resolve().parents[4]
_MCP_JSON = _REPO_ROOT / ".mcp.json"
_GOVERNANCE_STANDARD = (
    _REPO_ROOT / "docs" / "infrastructure" / "mcp"
    / "[STANDARD]_MJ_Agent_MCP_Server_Governance.md"
)


# -------- Background --------

@given(parsers.re(re.escape(
    ".mcp.json declares exactly 13 server entries"
)))
def given_13_servers() -> None:
    data = json.loads(_MCP_JSON.read_text(encoding="utf-8"))
    n = len(data.get("mcpServers", {}))
    assert n == 13, f"expected exactly 13 servers in .mcp.json; found {n}"


@given(parsers.re(re.escape(
    "10 of those 13 entries are pg-* wrapper-based "
    "(5 mj-agent memory + 5 mj-system biz)"
)))
def given_10_pg_entries() -> None:
    data = json.loads(_MCP_JSON.read_text(encoding="utf-8"))
    pg_entries = [k for k in data["mcpServers"] if k.startswith("pg-")]
    assert len(pg_entries) == 10, (
        f"expected exactly 10 pg-* entries; found {len(pg_entries)}: {pg_entries}"
    )


@given(parsers.re(re.escape(
    "the A14 PR gate template lives at "
    "`docs/infrastructure/mcp/[STANDARD]_MJ_Agent_MCP_Server_Governance.md §4`"
)))
def given_a14_template_exists() -> None:
    assert _GOVERNANCE_STANDARD.exists(), (
        f"A14 governance STANDARD not found at {_GOVERNANCE_STANDARD}"
    )
    text = _GOVERNANCE_STANDARD.read_text(encoding="utf-8")
    # Section 4 is the declaration template
    assert re.search(r"^#+\s*§?\s*4", text, re.MULTILINE), (
        "A14 governance STANDARD missing §4 declaration template heading"
    )


# -------- Scenarios --------


@scenario(_FEATURE_FILE, "Adding a 14th MCP server triggers A14 PR gate body declaration")
def test_req_001_a14_gate_template_exists() -> None:
    pass


@scenario(_FEATURE_FILE, "All 10 pg-* entries reference the same wrapper script")
def test_req_002_pg_wrapper_consistency() -> None:
    pass


# -------- REQ-001 step defs --------


@given(parsers.re(re.escape(
    'a PR is submitted that adds a 14th entry to .mcp.json '
    '(e.g. a hypothetical "redis-server" MCP)'
)))
def given_hypothetical_14th_pr() -> None:
    """Descriptive — actual PR review process is human-driven; this BDD
    asserts the governance scaffolding (STANDARD §4 template) is in place
    so a reviewer would have a checklist to follow.
    """


@when("the reviewer parses the PR body", target_fixture="governance_standard_text")
def when_reviewer_parses(governance_standard_text: str | None = None) -> str:
    # Capture the STANDARD text so the @then steps can scan it.
    return _GOVERNANCE_STANDARD.read_text(encoding="utf-8")


@then(parsers.re(re.escape(
    'the body MUST contain a "MCP Server Governance (A14)" block'
)))
def then_a14_block_present(governance_standard_text: str) -> None:
    # The STANDARD defines the A14 block; PR body uses it as a template.
    assert "MCP Server Governance" in governance_standard_text, (
        "STANDARD missing 'MCP Server Governance' section title"
    )
    assert "A14" in governance_standard_text, "STANDARD does not mention A14"


@then(parsers.re(re.escape(
    "the block lists the new entry with trust_posture + credential_mode + rationale"
)))
def then_block_lists_required_fields(governance_standard_text: str) -> None:
    # STANDARD uses space-separated phrases ("trust posture" / "credential mode")
    # and "Justification" for rationale; accept either form.
    aliases = {
        "trust_posture": ("trust_posture", "trust posture"),
        "credential_mode": ("credential_mode", "credential mode"),
        "rationale": ("rationale", "Justification"),
    }
    for field, variants in aliases.items():
        assert any(v in governance_standard_text for v in variants), (
            f"STANDARD §4 template missing required field {field!r}; "
            f"tried variants {variants!r}"
        )


@then(parsers.re(re.escape(
    "a PR that lacks this block fails A14 gate review "
    "(Phase M3+ blocking; warning at M1)"
)))
def then_a14_blocking_schedule_documented(governance_standard_text: str) -> None:
    # STANDARD documents PR-gate enforcement; accepts Chinese (阻塞 = block,
    # 生效 = take effect) or English (blocking) terminology.
    enforcement_markers = ("blocking", "warning", "阻塞", "生效", "enforcement")
    assert any(m in governance_standard_text for m in enforcement_markers), (
        f"STANDARD missing PR-gate enforcement marker; tried {enforcement_markers!r}"
    )
    assert "A14" in governance_standard_text, "STANDARD must mention A14 gate"


# -------- REQ-002 step defs --------


@given(parsers.re(re.escape(".mcp.json is loaded")), target_fixture="mcp_data")
def given_mcp_loaded() -> dict[str, Any]:
    return json.loads(_MCP_JSON.read_text(encoding="utf-8"))


@when(
    "the wrapper-script reference is inspected for each pg-* server entry",
    target_fixture="pg_wrapper_refs",
)
def when_inspect_pg_wrappers(mcp_data: dict[str, Any]) -> dict[str, str]:
    """Extract the wrapper script path from each pg-* entry."""
    pg_refs: dict[str, str] = {}
    for name, cfg in mcp_data["mcpServers"].items():
        if not name.startswith("pg-"):
            continue
        # args has the wrapper path at index 1 (after "/c")
        args = cfg.get("args", [])
        wrapper = next(
            (a for a in args if "pg-server-start" in a or "pg-server" in a),
            "",
        )
        pg_refs[name] = wrapper
    return pg_refs


@then(parsers.re(re.escape(
    r"all 10 pg-* entries reference `.claude\scripts\pg-server-start.cmd`"
)))
def then_all_pg_refer_same_wrapper(pg_wrapper_refs: dict[str, str]) -> None:
    expected = r".claude\scripts\pg-server-start.cmd"
    mismatches = {n: w for n, w in pg_wrapper_refs.items() if w != expected}
    assert not mismatches, (
        f"pg-* entries with non-canonical wrapper: {mismatches}"
    )


@then(parsers.re(re.escape(
    'any entry referencing a different wrapper (e.g. directly invoking npx '
    'for a different pg MCP) triggers the A14 "credential mode changed" '
    "sub-check (PR body MUST justify why per-entry deviation is needed)"
)))
def then_a14_deviation_check_documented() -> None:
    """Descriptive — governance scaffolding present in STANDARD."""
    text = _GOVERNANCE_STANDARD.read_text(encoding="utf-8")
    assert "credential" in text.lower(), (
        "STANDARD missing credential-mode documentation"
    )
