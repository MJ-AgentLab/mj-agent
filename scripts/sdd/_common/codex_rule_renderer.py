"""codex_rule_renderer.py — the `.codex/rules/*.rules` output-class renderer.

Epic #499 PR-D1a (plan §5.9). Renders codex execpolicy rule files from the
typed source `sdd/adapters/codex-enforcement.yml` and nothing else. This is the
`codex_rule_renderer` module pre-registered by the PR-B lock fixtures
(`tests/unit/test_lock_v2.py`) and enumerated in `policies/ai-agent.md` §4
(A14 row (b), D-017 extended adjacency).

One output class per module (plan §2.6) — a hooks-only change must not churn a
rule entry's renderer digest, so the shared parsing lives in
`_common/enforcement_source.py`.

FORMAT PROVENANCE (verified, not invented): the `.rules` dialect is Starlark
with a `prefix_rule(pattern=[...], decision="...")` builtin, established
empirically against codex-cli 0.147.0 via `codex execpolicy check --rules`.
The repo carries no `.rules` documentation, so this renderer is pinned to that
build; a future codex may change the dialect (see the PR-P1a caveat that
ready-host discovery does not generalize across versions/machines).

STRICTEST DECISION (plan §5.9): codex itself aggregates the strictest decision
across every matched rule AND across repeated `--rules` files
(`allow` < `prompt` < `forbidden`, verified empirically). This renderer
therefore emits rules verbatim and never re-implements precedence; the fixtures
assert codex's reported top-level `decision`.

Never inputs (plan §5.9, hard): raw transcript, assistant messages, Secrets,
private harness state.

Deterministic UTF-8 (no BOM), LF, exactly one final newline
(`generated-utf8-lf-v1`).
"""

from __future__ import annotations

import json

from scripts.sdd._common.enforcement_source import RuleFile

RENDERER_MODULE = "scripts.sdd._common.codex_rule_renderer"
RENDERER_VERSION = 1

HEADER = """\
# GENERATED -- do not edit. Owned by scripts/sdd/agents_sync.py from
# sdd/adapters/codex-enforcement.yml (Epic #499 ADR-039 D-011/D-012).
# To change: edit that typed source through its own D-017 gate, run
# `python scripts/sdd/agents_sync.py sync`, and commit source + artifact +
# .agents.lock.json together. No --adopt path exists for enforcement outputs.
#
# COOPERATIVE scope: these rules surface AGENTS.md stop points inside the Codex
# harness. They bind only Codex, never write .claude/**, and do NOT replace the
# self-enforced boundaries in AGENTS.md -- a rule that fails to fire is not
# permission to proceed. Owner 拍板 is unchanged.
#
# codex computes the STRICTEST decision across all matched rules
# (allow < prompt < forbidden), so overlapping prefixes are intentional.
"""


class RuleRenderError(ValueError):
    """Fail-closed render refusal — the caller must write nothing."""


def _starlark_str(value: str) -> str:
    """Emit a Starlark string literal. Starlark string syntax is JSON-compatible
    for the escapes we can produce, so json.dumps gives correct quoting without
    hand-rolling an escaper."""
    return json.dumps(value, ensure_ascii=False)


def render_rules(rule_file: RuleFile) -> str:
    """Render one `.codex/rules/<name>.rules` file from its typed declaration."""
    if not rule_file.prefix_rules:
        # codex refuses an empty policy ("rules prefix_rules cannot be empty").
        raise RuleRenderError(f"{rule_file.output_path} declares no prefix_rules")

    blocks: list[str] = [HEADER]
    for rule in rule_file.prefix_rules:
        if not rule.pattern:
            raise RuleRenderError(f"prefix rule {rule.rule_id!r} has an empty pattern")
        pattern = ", ".join(_starlark_str(tok) for tok in rule.pattern)
        blocks.append(
            f"# {rule.rule_id}: {rule.reason}\n"
            f"prefix_rule(\n"
            f"    pattern=[{pattern}],\n"
            f"    decision={_starlark_str(rule.decision)},\n"
            f")\n"
        )
    return "\n".join(blocks).replace("\r\n", "\n").rstrip("\n") + "\n"


__all__ = ["HEADER", "RENDERER_MODULE", "RENDERER_VERSION", "RuleRenderError", "render_rules"]
