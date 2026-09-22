"""Native MCP structural BDD: no host, credentials or service calls."""
import tomllib
from pathlib import Path

import yaml
from pytest_bdd import given, scenario, then, when
from scripts.sdd.check_codex_native import MEMORY, check

ROOT = Path(__file__).resolve().parents[4]
FEATURE = '../../../../capabilities/infrastructure/mcp-server-governance/contracts/behavior.feature'
CONTRACT = 'capabilities/infrastructure/mcp-server-governance/contracts/governance.contract.yml'

@scenario(FEATURE, 'Adding a new MCP server triggers A14 PR gate body declaration')
def test_req_001_a14_gate_template_exists():
    pass

@scenario(FEATURE, 'All 5 memory pg entries reference the same native wrapper script')
def test_req_002_pg_wrapper_consistency():
    pass

@given('native config declares only the eight retained project servers', target_fixture='servers')
def servers():
    result = tomllib.loads((ROOT / '.codex/config.toml').read_text('utf-8'))['mcp_servers']
    assert set(result) == {'github', 'playwright', 'serena', *MEMORY}
    return result

@given('the native A14 template defines trust and credential review', target_fixture='governance')
def governance():
    return yaml.safe_load((ROOT / CONTRACT).read_text('utf-8'))

@when('the A14 declaration template is inspected')
def inspect_template(governance):
    assert governance['a14_pr_gate']['pr_body_required_block']

@then('trust posture, credential mode and rationale are required')
def required_fields(governance):
    fields = governance['a14_pr_gate']['pr_body_required_block']['minimum_fields']
    assert {'trust_posture', 'credential_mode', 'rationale'} <= set(fields)

@then('actual Owner review remains required before changing native MCP')
def owner_review(governance):
    assert 'mcp_inventory_change' in governance['hitl_required']
    assert '.codex/config.toml' in governance['a14_pr_gate']['trigger_files']

@when('native wrapper references are inspected')
def inspect_wrappers(servers):
    assert {name for name in servers if name.startswith('pg-')} == set(MEMORY)

@then('all five memory entries have canonical wrappers and env names')
def canonical_wrappers(servers):
    # Exact bootstrap and argument comparison; substring matching is insufficient.
    assert check(ROOT) == []
    for name, variable in MEMORY.items():
        assert servers[name]['env_vars'] == [variable]
