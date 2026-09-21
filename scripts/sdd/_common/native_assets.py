"""Explicit retired CLIENT assets retained pending cleanup; never a broad adapter exclusion.

Approved with the atomic ownership/gate cutover. No source content is read here.
Non-client adapters and all unrelated contract/policy checks remain in scope.
"""
from pathlib import Path

RETIRED_CLIENT_FILES = frozenset(('.agents.lock.json', 'capabilities/infrastructure/mcp-server-governance/contracts/claude-skill.contract.yml', 'policies/claude-code-skill.md', 'scripts/sdd/_common/codex_config_renderer.py', 'scripts/sdd/_common/codex_hook_renderer.py', 'scripts/sdd/_common/codex_readme_renderer.py', 'scripts/sdd/_common/codex_rule_renderer.py', 'scripts/sdd/_common/enforcement_source.py', 'scripts/sdd/_common/projection_loader.py', 'scripts/sdd/_common/skill_renderer.py', 'scripts/sdd/agents_sync.py', 'scripts/sdd/build_fidelity_attestations.py', 'scripts/sdd/check_agents_projection.py', 'scripts/sdd/check_claude_skill_contracts.py', 'scripts/sdd/check_cross_carrier.py', 'scripts/sdd/check_development_agent.py', 'scripts/sdd/check_fidelity_attestations.py', 'scripts/sdd/run_codex_carrier_probe.py', 'scripts/sdd/task0_freeze.py', 'sdd/adapters/claude-code-skill.md', 'sdd/adapters/codex-enforcement.yml', 'sdd/adapters/codex-skill-fidelity.yml', 'sdd/adapters/codex-skill-preface.md', 'sdd/adapters/codex-skill-translation.yml', 'sdd/adapters/codex-skills-readme.md', 'sdd/adapters/development-agent.md', 'sdd/development-agent.yml', 'sdd/templates/contracts/claude-skill.contract.yml.template', 'sdd/workflows/development-agent-workflows.yml'))


def retired_client_asset(relative: Path | str) -> bool:
    value = Path(relative).as_posix()
    return value in RETIRED_CLIENT_FILES or value.startswith('.claude/') or value == 'CLAUDE.md' or value.endswith('/CLAUDE.md')
