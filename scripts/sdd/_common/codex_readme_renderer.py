"""codex_readme_renderer.py — the `.agents/README.md` output-class renderer.

Dormant v2 machinery (Epic #499 PR-B, plan §2.6): under the v2 engine the
directory README is rendered from the raw Markdown template
`sdd/adapters/codex-skills-readme.md` plus manifest-derived strategy
statistics, and gets its own lock entry (`entry_kind: skills-readme`,
`surface_members: ["skills"]`). Until the PR-C1 cutover the real tree keeps
the fixed v1 `README_TEMPLATE` inside `agents_sync.py` — this module renders
nothing on the real tree.

The template is a RAW TEMPLATE, not a typed source: it has no schema_version
of its own — its version is owned by the manifest v2 key
`codex_readme_template_version` and the lock records the raw template SHA-256
(plan §2.6). This module is focused on ONE output class so a README change
never churns the 13 skill entries' renderer digests; it joins the A14 row (b)
D-017 loader/renderer enumeration (Gate 1 拍板, PR-B).

Fail-closed: any `{{...}}` token the renderer does not positively understand,
or a known placeholder missing from the template, refuses to render.

Read-only inputs; no secrets; deterministic UTF-8 (no BOM), LF, exactly one
final newline (`generated-utf8-lf-v1`).
"""

from __future__ import annotations

import re
from typing import Any

RENDERER_MODULE = "scripts.sdd._common.codex_readme_renderer"
RENDERER_VERSION = 1

_PLACEHOLDER = re.compile(r"\{\{([a-z0-9_]*)\}\}")
# Closed placeholder vocabulary — the template may use each of these exactly as
# many times as it wants but MUST use every one at least once, and may not use
# anything else.
KNOWN_PLACEHOLDERS = frozenset({"strategy_summary"})


class ReadmeRenderError(ValueError):
    """Fail-closed render refusal — the caller must write nothing."""


def strategy_summary(capabilities: list[dict[str, Any]]) -> str:
    """Derive the carrier strategy statistics line from manifest v2 capability
    rows. Counts are DERIVED, never hardcoded (AC-04): validators and templates
    must not pin the 5/13 split as a constant."""
    counts = {"byte-copy": 0, "translated": 0, "none": 0}
    for entry in capabilities:
        carrier = entry.get("codex_carrier")
        if carrier not in counts:
            raise ReadmeRenderError(
                f"capability {entry.get('id')!r} has codex_carrier {carrier!r}"
                " — README statistics require a valid v2 carrier on every row"
            )
        counts[carrier] += 1
    with_carrier = counts["byte-copy"] + counts["translated"]
    return (
        f"{with_carrier} skills carry a Codex projection"
        f" ({counts['byte-copy']} byte-copy + {counts['translated']} translated);"
        f" {counts['none']} capabilities have no Codex carrier."
    )


def render_skills_readme(
    template_text: str, capabilities: list[dict[str, Any]]
) -> str:
    """Render the README from the raw template + manifest-derived statistics."""
    used: set[str] = set()
    for match in _PLACEHOLDER.finditer(template_text):
        token = match.group(1)
        if token not in KNOWN_PLACEHOLDERS:
            raise ReadmeRenderError(
                f"template placeholder {{{{{token}}}}} is not in the closed"
                f" vocabulary {sorted(KNOWN_PLACEHOLDERS)} (fail-closed)"
            )
        used.add(token)
    missing = KNOWN_PLACEHOLDERS - used
    if missing:
        raise ReadmeRenderError(
            f"template is missing required placeholder(s):"
            f" {sorted('{{' + m + '}}' for m in missing)}"
        )
    rendered = template_text.replace(
        "{{strategy_summary}}", strategy_summary(capabilities)
    )
    rendered = rendered.replace("\r\n", "\n")
    return rendered.rstrip("\n") + "\n"
