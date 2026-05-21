"""scripts/sdd/_common/enums.py — HITL enum normalization.

Per Stage A C5 augmentation: hyphen is canonical (e.g. `sql-guardrail-relax`);
underscore variants (`sql_guardrail_relax`) emit WARN. M3 cleanup PR will
unify all M1 contract YAML to hyphen form.

Canonical set anchored at `policies/data-boundary.md §3 4 项专属必停`.
"""

from __future__ import annotations

HITL_CANONICAL: frozenset[str] = frozenset({
    "sql-guardrail-relax",
    "runtime-skill-content-change",
    "prompt-version-bump",
    "biz-catalog-sync",
})


def validate_hitl_enum(values: list[str]) -> list[tuple[str, str]]:
    """Validate hitl_required values.

    Returns list of `(severity_value, message)` tuples. severity_value is
    "WARN" string (interop with `Severity` enum in cli.py).
    """
    findings: list[tuple[str, str]] = []
    for item in values:
        if not isinstance(item, str) or item == "none":
            continue
        if "_" in item:
            hyphen_form = item.replace("_", "-")
            if hyphen_form in HITL_CANONICAL:
                findings.append((
                    "WARN",
                    f"hitl_required '{item}' uses underscore; canonical hyphen form is '{hyphen_form}' (M3 cleanup planned per C5)",
                ))
            else:
                findings.append((
                    "WARN",
                    f"hitl_required '{item}' uses underscore but is not in canonical HITL set; verify intent",
                ))
    return findings


__all__ = ["HITL_CANONICAL", "validate_hitl_enum"]
