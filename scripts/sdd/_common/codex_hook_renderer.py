"""codex_hook_renderer.py — the `.codex/hooks.json` output-class renderer.

Epic #499 PR-D1a (plan §5.9). Renders the Codex-side cooperative hook wiring
from the typed source `sdd/adapters/codex-enforcement.yml` and nothing else.
This is the `codex_hook_renderer` module pre-registered by the PR-B lock
fixtures (`tests/unit/test_lock_v2.py`) and enumerated in `policies/ai-agent.md`
§4 (A14 row (b), D-017 extended adjacency).

One output class per module (plan §2.6): the v2 lock records
`renderer_module` / `renderer_module_sha256` / `renderer_version` per entry, so
a rules-only change must never churn the hooks entry's digest — which is why
the shared parsing lives in `_common/enforcement_source.py` rather than here.

WHY PreToolUse ONLY (plan §5.9 "block before side effect"): codex evaluates
PreToolUse hooks BEFORE the tool call executes and reports
"Tool call blocked by PreToolUse hook: " / "Command blocked by PreToolUse
hook: " when the handler returns `decision: block`. A PostToolUse deny would
be a rollback AFTER the side effect and is therefore refused by the loader's
`ALLOWED_EVENTS`.

Wire shape provenance (honest scope): the emitted object graph uses the hook
config vocabulary carried by codex-cli 0.147.0 (`matcher`, `type`, `command`,
`timeout`, `statusMessage`; event names from `HookEventNameWire`). The
END-TO-END harness execution of this file is NOT verified by this repo and is
recorded as SKIP, not PASS — nothing here executes the Codex harness (plan
§1.4: an unexecuted runtime leg is SKIP).

Never inputs (plan §5.9, hard): raw transcript, assistant messages, Secrets,
private harness state. The renderer reads the typed source only.

Deterministic canonical JSON (`canonical-json-v1`): LF, 2-space indent,
`ensure_ascii=false`, object keys sorted, exactly one final newline.
"""

from __future__ import annotations

from typing import Any

from scripts.sdd._common.enforcement_source import EnforcementSource
from scripts.sdd._common.projection_loader import canonical_json_text

RENDERER_MODULE = "scripts.sdd._common.codex_hook_renderer"
RENDERER_VERSION = 1

# Provenance is carried INSIDE the JSON (JSON has no comment syntax), so a
# reader who opens the artifact directly still learns it is generated and how
# to change it.
#
# It MUST go in `description`, which is one of exactly two fields codex's
# `HooksFile` accepts (binary 0xe16bd53: `internally tagged enum
# HookHandlerConfig` ... `HooksFile` `description` `hooks`). That struct is
# deny_unknown_fields, so ANY extra top-level key makes the WHOLE file fail to
# parse and registers ZERO hooks — silently, because an untrusted/unparseable
# hooks file is a warning, not an error. A first draft of this renderer emitted
# the note under `_generated` and shipped an artifact codex could not load at
# all; the Stage 11 review caught it by driving `codex app-server` `hooks/list`
# against the committed bytes. Do not add top-level keys here.
GENERATED_NOTE = (
    "GENERATED -- do not edit. Owned by scripts/sdd/agents_sync.py from"
    " sdd/adapters/codex-enforcement.yml (Epic #499 ADR-039 D-011/D-012)."
    " To change: edit that typed source through its own D-017 gate, run"
    " `python scripts/sdd/agents_sync.py sync`, and commit source + artifact"
    " + .agents.lock.json together. There is no --adopt path for enforcement"
    " outputs. These hooks are COOPERATIVE: they surface AGENTS.md stop points"
    " inside the Codex harness, they never write .claude/**, they bind only"
    " Codex, and they do not replace the self-enforced boundaries in AGENTS.md."
)


class HookRenderError(ValueError):
    """Fail-closed render refusal — the caller must write nothing."""


def render_hooks(source: EnforcementSource) -> str:
    """Render `.codex/hooks.json` canonical text from the typed source."""
    handler = source.handler
    if not handler.command:
        raise HookRenderError("hooks.handler.command is empty")

    # One hook spec object reused by every (event, matcher) pair — the guard
    # script decides per call which guard applies, so the wiring stays flat.
    spec: dict[str, Any] = {
        "type": "command",
        "command": " ".join(handler.command),
        "timeout": handler.timeout_seconds,
    }
    if handler.status_message is not None:
        spec["statusMessage"] = handler.status_message

    by_event: dict[str, list[dict[str, Any]]] = {}
    for event in source.events:
        by_event.setdefault(event.event, []).append(
            {"matcher": event.matcher, "hooks": [dict(spec)]}
        )
    if not by_event:
        raise HookRenderError("no hook events declared")
    # Deterministic order: matchers sorted within each event; events sorted by
    # canonical_json_text's key sort.
    for entries in by_event.values():
        entries.sort(key=lambda e: e["matcher"])

    # Exactly the two keys `HooksFile` accepts — nothing else may be added.
    document = {"description": GENERATED_NOTE, "hooks": by_event}
    return canonical_json_text(document)


__all__ = ["GENERATED_NOTE", "HookRenderError", "RENDERER_MODULE", "RENDERER_VERSION", "render_hooks"]
